# ============================================================
# ANNUAL CORRELATION
# ============================================================
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 600
plt.rcParams['font.size'] = 10

# ------------------------------------------------------------
# 1. DATA LOADING
# ------------------------------------------------------------
df_sn = pd.read_csv(
    "SN_y_tot_V2.0(1).txt",
    sep=r'\s+',
    header=None,
    usecols=[0, 1],
    names=['Year', 'SunspotNumber']
)
df_sn['Year'] = df_sn['Year'].astype(int)

df_cmes = pd.read_csv("datos_procesados_2025_09_30.csv", low_memory=False)
df_cmes['Fecha'] = pd.to_datetime(df_cmes['Fecha'], errors='coerce')

df_cmes[['Central', 'Ancho', 'Rapidez']] = df_cmes[
    ['Central', 'Ancho', 'Rapidez']
].apply(pd.to_numeric, errors='coerce')

df_cmes['Year'] = df_cmes['Fecha'].dt.year

# ===== Analysis periods  =====
#df_cmes = df_cmes[
#    (df_cmes['Fecha'] >= '1996-01-01') &
#    (df_cmes['Fecha'] <= '2025-09-30')
#]

#df_cmes = df_cmes[(df_cmes['Fecha'] >= '1996-01-01') &
#                   (df_cmes['Fecha'] <= '2008-12-31')]

df_cmes = df_cmes[(df_cmes['Fecha'] >= '2009-01-01') &
                   (df_cmes['Fecha'] <= '2019-12-31')]
# ============================================================

df_cmes = df_cmes.dropna(subset=['Rapidez', 'Year'])

# ------------------------------------------------------------
# 2. VELOCITY BINS 
# ------------------------------------------------------------
velocity_bins = [
    (0, 600, "Slow"),
    (600, 1000, 'Moderate'),
    (1000, 1500, 'Fast'),
    (1500, 3000, 'Extreme'),
]

# ------------------------------------------------------------
# 3. ANALYSIS FUNCTIONS
# ------------------------------------------------------------
def annual_cme_rate_by_bin(df_cmes, vmin, vmax):
    subset = df_cmes[
        (df_cmes["Rapidez"] >= vmin) &
        (df_cmes["Rapidez"] < vmax)
    ]
    return subset.groupby("Year").size().reset_index(name="CME_Count")


def align_time_series(df_sn, df_cmes, vmin, vmax):
    annual_counts = annual_cme_rate_by_bin(df_cmes, vmin, vmax)
    merged_df = pd.merge(df_sn, annual_counts, on="Year", how="inner")
    return merged_df.dropna(subset=["SunspotNumber", "CME_Count"])


def bootstrap_ci(x, y, n_bootstrap=1000):
    boot_r = []
    n = len(x)

    for _ in range(n_bootstrap):
        idx = np.random.choice(n, size=n, replace=True)
        r, _ = spearmanr(x.iloc[idx], y.iloc[idx])
        boot_r.append(r)

    return np.percentile(boot_r, [2.5, 97.5])


# ------------------------------------------------------------
# 4. CORRELATION BY VELOCITY BIN
# ------------------------------------------------------------
print("\n" + "="*70)
print("Correlation analysis by velocity bin")
print("="*70)

results = []

for vmin, vmax, label in velocity_bins:
    aligned_df = align_time_series(df_sn, df_cmes, vmin, vmax)

    if len(aligned_df) < 5:
        print(f"{label}: insufficient data")
        continue

    r, p = spearmanr(
        aligned_df["SunspotNumber"],
        aligned_df["CME_Count"]
    )

    ci_low, ci_high = bootstrap_ci(
        aligned_df["SunspotNumber"],
        aligned_df["CME_Count"]
    )

    n_total = len(df_cmes[
        (df_cmes["Rapidez"] >= vmin) &
        (df_cmes["Rapidez"] < vmax)
    ])

    results.append({
        'Bin': label,
        'Vmin': vmin,
        'Vmax': vmax,
        'r': r,
        'CI_low': ci_low,
        'CI_high': ci_high,
        'n_years': len(aligned_df),
        'n_cmes': n_total
    })

    print(f"\n{label} ({vmin}-{vmax} km/s)")
    print(f"r = {r:.3f} [{ci_low:.3f}, {ci_high:.3f}]")
    print(f"p = {p:.4f}")

results_df = pd.DataFrame(results)

# ============================================================
# FIGURE: Correlation vs bin velocity
# ============================================================

v_centers = (results_df['Vmin'] + results_df['Vmax']) / 2

fig, ax = plt.subplots(figsize=(7, 5))

markers = ['o', '^', 's', 'D']

for i, row in results_df.iterrows():
    ax.errorbar(
        v_centers.iloc[i],
        row['r'],
        yerr=[[row['r'] - row['CI_low']],
              [row['CI_high'] - row['r']]],
        fmt=markers[i % len(markers)],
        color='black',
        ecolor='black',
        markerfacecolor='black',
        markersize=6,
        capsize=6,
        linewidth=2,
        label=row['Bin']
    )

ax.axhline(0.7, linestyle='--', color='black', alpha=0.4)

ax.set_xlabel('Bin Central Velocity (km s$^{-1}$)')
ax.set_ylabel('Spearman r')

ax.grid(True, linestyle='--', alpha=0.3)
ax.tick_params(top=True, right=True, direction='in')
ax.minorticks_on()

ax.legend(title="Bin speed", frameon=False)

plt.tight_layout()
plt.savefig('correlation_vs_velocity_annual_full_period.pdf', dpi=600)
plt.close()

print("\nFigure saved: correlation_vs_velocity_annual_full_period.pdf")
