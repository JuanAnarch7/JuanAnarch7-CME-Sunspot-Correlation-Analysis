# ============================================================
# Monthly Correlation
# ============================================================

import pandas as pd
import numpy as np
from scipy.stats import spearmanr, kendalltau
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# 1. DATA LOADING
# ------------------------------------------------------------
print("="*70)
print("MONTHLY DIAGNOSIS")
print("="*70)

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

# Filtra período de interés
df_sn = df_sn[(df_sn['Year'] >= 1996) & (df_sn['Year'] <= 2025)].copy()

print(f"    Loaded Months: {len(df_sn)}")
print(f"    Range: {df_sn['Date'].min()} – {df_sn['Date'].max()}")

print("\n[2/6] Loading CME data")

df_cmes = pd.read_csv("datos_procesados_2025_09_30.csv", low_memory=False)
df_cmes['Fecha'] = pd.to_datetime(df_cmes['Fecha'], errors='coerce')


# Definition of analysis periods ==================rates, using the same velocity-based CME
# Full period
df_cmes = df_cmes[(df_cmes['Fecha'] >= '1996-01-01') & (df_cmes['Fecha'] <= '2025-09-30')]
# Cycle 23
#df_cmes = df_cmes[(df_cmes['Fecha'] >= '1996-01-01') & (df_cmes['Fecha'] <= '2008-12-31')]
# Cycle 24
#df_cmes = df_cmes[(df_cmes['Fecha'] >= '2009-01-01') & (df_cmes['Fecha'] <= '2019-12-31')]
# Cycle 25 (June 2025)
#df_cmes = df_cmes[(df_cmes['Fecha'] >= '2020-01-01') & (df_cmes['Fecha'] <= '2025-09-30')]
#==============================================================


df_cmes[['Central', 'Ancho', 'Rapidez']] = df_cmes[
    ['Central', 'Ancho', 'Rapidez']
].apply(pd.to_numeric, errors='coerce')

df_cmes = df_cmes.dropna(subset=['Fecha', 'Rapidez'])
df_cmes['YearMonth'] = df_cmes['Fecha'].dt.to_period('M')

print(f"    Total CMEs: {len(df_cmes)}")
print(f"    Range: {df_cmes['Fecha'].min()} – {df_cmes['Fecha'].max()}")
print(f"    Speed: {df_cmes['Rapidez'].min():.0f} – {df_cmes['Rapidez'].max():.0f} km/s")

# ------------------------------------------------------------
# 2. DEFINITION OF SPEED BINS
# ------------------------------------------------------------
#velocity_bins = [
#    (0, 600, "Slow"),
#    (600, 800, 'Moderate Slow'),
#    (800, 1000, 'Moderate Fast'),
#    (1000, 1300, 'Fast'),
#    (1300, 1600, 'Extreme'),
#    (1600, 3000, 'Super Extreme'),
#]
#velocity_bins = [
#    (0, 600, "Slow"),
#    (600, 1000, 'Moderate'),
#    (1000, 1300, 'Fast'),
#    (1300, 1600, 'Super Fast'),
#    (1600, 3000, 'Extreme'),
#]
velocity_bins = [
    (0, 600, "Slow"),
    (600, 1000, 'Moderate'),
    (1000, 1500, 'Fast'),
    (1500, 3000, 'Extreme'),
]
# ------------------------------------------------------------
# 3. FUNCTIONS
# ------------------------------------------------------------
def monthly_cme_rate_by_bin(df, vmin, vmax):
    subset = df[(df['Rapidez'] >= vmin) & (df['Rapidez'] < vmax)]
    counts = subset.groupby('YearMonth').size().reset_index(name='CME_Count')
    counts['Date'] = counts['YearMonth'].dt.to_timestamp()
    return counts

def align_time_series_monthly(df_sn, df_cmes, vmin, vmax):
    cme_monthly = monthly_cme_rate_by_bin(df_cmes, vmin, vmax)
    merged = pd.merge(
        df_sn[['Date', 'SSN']],
        cme_monthly[['Date', 'CME_Count']],
        on='Date',
        how='inner'
    )
    return merged.dropna()

def bootstrap_ci(x, y, n_bootstrap=1000):
    boot_r = []
    n = len(x)
    for _ in range(n_bootstrap):
        idx = np.random.choice(n, n, replace=True)
        r, _ = spearmanr(x.iloc[idx], y.iloc[idx])
        boot_r.append(r)
    return np.percentile(boot_r, [2.5, 97.5])

# ------------------------------------------------------------
# 4. TEST : CORRELATIONS PER BIN
# ------------------------------------------------------------
print("\n" + "="*70)
print("TEST : Monthly Correlation per bin")
print("="*70)

results = []

for vmin, vmax, label in velocity_bins:
    aligned = align_time_series_monthly(df_sn, df_cmes, vmin, vmax)

    if len(aligned) < 12:
        print(f"{label}: insufficient data (n={len(aligned)})")
        continue

    r, p = spearmanr(aligned['SSN'], aligned['CME_Count'])
    ci_low, ci_high = bootstrap_ci(aligned['SSN'], aligned['CME_Count'])

    sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
    n_cmes = len(df_cmes[(df_cmes['Rapidez'] >= vmin) & (df_cmes['Rapidez'] < vmax)])

    results.append({
        'Bin': label,
        'Vmin': vmin,
        'Vmax': vmax,
        'r': r,
        'p': p,
        'CI_low': ci_low,
        'CI_high': ci_high,
        'n_months': len(aligned),
        'n_cmes': n_cmes,
        'sig': sig
    })

    print(f"{label:15s}: r={r:+.3f} [{ci_low:+.3f},{ci_high:+.3f}] {sig}")

results_df = pd.DataFrame(results)


# ------------------------------------------------------------
# 5. VISUALIZATION
# ------------------------------------------------------------
print("\n[5/6] Generating diagnostic figure")

fig, ax = plt.subplots(figsize=(8, 5))
v_centers = (results_df['Vmin'] + results_df['Vmax']) / 2
markers = ['o', '^', 's', 'D', 'v', 'P', 'X']

for i, row in results_df.iterrows():
    ax.errorbar(
        v_centers.iloc[i],
        row['r'],
        yerr=[[row['r'] - row['CI_low']],
              [row['CI_high'] - row['r']]],
        fmt=markers[i % len(markers)],
        color='black',
        ecolor='black',
        markeredgecolor='black',
        markerfacecolor='black',
        markersize=8,
        capsize=6,
        capthick=1.8,
        linewidth=2,
        label=row['Bin']
    )

ax.axhline(0.7, ls='--', color='black', alpha=0.4)

ax.set_xlabel(' Bin central speed (km/s)', fontweight='bold')
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

# Save figure
plt.tight_layout()
plt.savefig("Correlation_monthly_Sc_25.pdf", dpi=600)
plt.close()

print("    Figure Saved: Correlation_monthly_Sc_25.pdf")
# ------------------------------------------------------------
# 6. SAVE RESULTS
# ------------------------------------------------------------
print("\n[6/6] Saving results")

results_df.to_csv("Correlation_results_monthly_Sc_25.csv", index=False)
print("    Table saved: Correlation_results_monthly_Sc_25.csv")


