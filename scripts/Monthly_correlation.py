# ============================================================
# MONTHLY CORRELATION 
# ============================================================
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# REPRODUCIBILITY & METHODOLOGY
# ------------------------------------------------------------
RANDOM_SEED = 42
BLOCK_SIZE = 12  
rng = np.random.default_rng(RANDOM_SEED)

print("="*70)
print(f"REPRODUCIBILITY ENABLED | Seed: {RANDOM_SEED} | Block Size: {BLOCK_SIZE}")
print("="*70)

# ------------------------------------------------------------
# 1. DATA LOADING
# ------------------------------------------------------------
print("\n[1/6] Loading monthly sunspot data")
df_sn = pd.read_csv(
    "SN_m_tot_V2.0.txt",
    sep=r'\s+',
    header=None,
    usecols=[0, 1, 3],
    names=['Year', 'Month', 'SSN']
)
df_sn['Year'] = df_sn['Year'].astype(int)
df_sn['Month'] = df_sn['Month'].astype(int)
df_sn['Date'] = pd.to_datetime(df_sn[['Year', 'Month']].assign(Day=1))

print("\n[2/6] Loading CME data")
df_cmes = pd.read_csv("datos_procesados_2025_09_30.csv", low_memory=False)
df_cmes['Fecha'] = pd.to_datetime(df_cmes['Fecha'], errors='coerce')
df_cmes[['Central', 'Ancho', 'Rapidez']] = df_cmes[['Central', 'Ancho', 'Rapidez']].apply(pd.to_numeric, errors='coerce')
df_cmes['Year'] = df_cmes['Fecha'].dt.year
df_cmes['Month'] = df_cmes['Fecha'].dt.month

# ------------------------------------------------------------
# 2. MONTHLY GAP FILTERING (SOHO/LASCO)
# ------------------------------------------------------------
print("\n[3/6] Applying SOHO/LASCO data gap filtering")
gaps = [
    (1998, 7), (1998, 8), (1998, 9), 
    (1999, 1)                         
]

for year, month in gaps:
    df_cmes = df_cmes[~((df_cmes['Year'] == year) & (df_cmes['Month'] == month))]
    df_sn = df_sn[~((df_sn['Year'] == year) & (df_sn['Month'] == month))]

# Definition of analysis periods ==================rates, using the same velocity-based CME
# Full period
df_cmes = df_cmes[(df_cmes['Fecha'] >= '1996-01-01') & (df_cmes['Fecha'] <= '2025-09-30')]
# Cycle 23
#df_cmes = df_cmes[(df_cmes['Fecha'] >= '1996-01-01') & (df_cmes['Fecha'] <= '2008-12-31')]
# Cycle 24
#df_cmes = df_cmes[(df_cmes['Fecha'] >= '2009-01-01') & (df_cmes['Fecha'] <= '2019-12-31')]
# Cycle 25 (June 2025)
#df_cmes = df_cmes[(df_cmes['Fecha'] >= '2020-01-01') & (df_cmes['Fecha'] <= '2025-09-30')]

# ------------------------------------------------------------
# 3. ANALYSIS FUNCTIONS 
# ------------------------------------------------------------
def block_bootstrap_ci(x, y, n_bootstrap=1000, block_size=12, rng=None):
    if rng is None: rng = np.random.default_rng()
    n = len(x)
    boot_r = []
    num_blocks = int(np.ceil(n / block_size))
    
    for _ in range(n_bootstrap):
        boot_x, boot_y = [], []
        for _ in range(num_blocks):
            start_idx = rng.integers(0, n - block_size + 1)
            boot_x.extend(x.iloc[start_idx : start_idx + block_size].values)
            boot_y.extend(y.iloc[start_idx : start_idx + block_size].values)
        
        r, _ = spearmanr(boot_x[:n], boot_y[:n])
        boot_r.append(r)
    return np.percentile(boot_r, [2.5, 97.5])

def align_time_series_monthly(df_sn, df_cmes, vmin, vmax):
    subset = df_cmes[(df_cmes['Rapidez'] >= vmin) & (df_cmes['Rapidez'] < vmax)]
    df_cmes['YearMonth'] = df_cmes['Fecha'].dt.to_period('M') # 
    counts = subset.groupby(df_cmes['Fecha'].dt.to_period('M')).size().reset_index(name='CME_Count')
    counts['Date'] = counts['Fecha'].dt.to_timestamp()
    
    merged = pd.merge(df_sn[['Date', 'SSN']], counts[['Date', 'CME_Count']], on='Date', how='inner')
    return merged.dropna()

# ------------------------------------------------------------
# 4. ANALYSIS & MASTER CSV
# ------------------------------------------------------------
velocity_bins = [(0, 600, "Slow"), (600, 1000, 'Moderate'), (1000, 1500, 'Fast'), (1500, 3000, 'Extreme')] # 

results, master_frames = [], []

for vmin, vmax, label in velocity_bins:
    aligned = align_time_series_monthly(df_sn, df_cmes, vmin, vmax)
    
    if len(aligned) < (BLOCK_SIZE + 5): continue

    r, p = spearmanr(aligned['SSN'], aligned['CME_Count'])
    ci_low, ci_high = block_bootstrap_ci(aligned['SSN'], aligned['CME_Count'], block_size=BLOCK_SIZE, rng=rng)

    sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
    results.append({'Bin': label, 'Vmin': vmin, 'Vmax': vmax, 'r': r, 'CI_low': ci_low, 'CI_high': ci_high, 'sig': sig})

    print(f"{label:15s}: r={r:+.3f} [{ci_low:+.3f},{ci_high:+.3f}] {sig}")

    bin_frame = aligned[["Date", "SSN", "CME_Count"]].copy()
    bin_frame.rename(columns={"CME_Count": f"CME_Count_{label}"}, inplace=True)
    master_frames.append(bin_frame.set_index("Date"))

# Exportar Master CSV
master_df = pd.concat(master_frames, axis=1).loc[:, ~pd.concat(master_frames, axis=1).columns.duplicated()].reset_index()
master_df.to_csv("master_monthly_paired_series_corrected.csv", index=False)

# ------------------------------------------------------------
# 5. VISUALIZATION 
# ------------------------------------------------------------
results_df = pd.DataFrame(results)
v_centers = (results_df['Vmin'] + results_df['Vmax']) / 2
fig, ax = plt.subplots(figsize=(8, 5)) # 
markers = ['o', '^', 's', 'D']

for i, row in results_df.iterrows():
    ax.errorbar(
        v_centers.iloc[i], row['r'],
        yerr=[[row['r'] - row['CI_low']], [row['CI_high'] - row['r']]],
        fmt=markers[i % len(markers)], color='black', ecolor='black', markerfacecolor='black',
        markersize=8, capsize=6, linewidth=2, label=row['Bin']
    )

ax.axhline(0.7, ls='--', color='black', alpha=0.4) # 
ax.set_xlabel('Bin central speed (km s$^{-1}$)', fontweight='bold')
ax.set_ylabel('Spearman r', fontweight='bold')
ax.grid(True, linestyle='--', alpha=0.3)
ticks_x = ax.get_xticks()
ax.set_xticks(ticks_x[1:-1])
ticks_y = ax.get_yticks()
ax.set_yticks(ticks_y[1:-1])
ax.tick_params(top=True, right=True, direction='in', which='both')
ax.minorticks_on()
ax.tick_params(axis='both', which='minor', length=4, direction='in',
               top=True, right=True)
ax.tick_params(axis='both', which='major', length=7, width=1.2,
               direction='in', top=True, right=True)
ax.legend(
    title='CME Subsets',
    fontsize=9,
    title_fontsize=8,
    frameon=True,
    loc='best'
)
plt.tight_layout()
plt.savefig("Correlation_monthly_corrected_full period.pdf", dpi=600)
plt.show()

print("\nProceso mensual finalizado. CSV exportado: master_monthly_paired_series_corrected.csv")
