# ============================================================
# MONTHLY SENSIVILITY ANALYSIS
# ============================================================

import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import matplotlib.pyplot as plt

print("="*60)
print("SENSIBILIDAD MENSUAL")
print("="*60)

# ------------------------------------------------------------
# 1. SUNSPOT DATA LOADING
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# 2. LOAD CMEs
# ------------------------------------------------------------
df_cmes = pd.read_csv("datos_procesados_2025_09_30.csv", low_memory=False)

df_cmes['Fecha'] = pd.to_datetime(df_cmes['Fecha'], errors='coerce')
df_cmes['Rapidez'] = pd.to_numeric(df_cmes['Rapidez'], errors='coerce')
df_cmes['Date'] = df_cmes['Fecha'].dt.to_period('M').dt.to_timestamp()

df_cmes = df_cmes.dropna(subset=['Rapidez','Date'])

print("CMEs:", len(df_cmes))

# ------------------------------------------------------------
# 3. BIN SCHEMES
# ------------------------------------------------------------
binning_schemes = {
    'Baseline': [
        (0, 600, 'Slow'),
        (600, 1000, 'Moderate'),
        (1000, 1500, 'Fast'),
        (1500, 3000, 'Super Fast')
    ],
    
    'Moderate (-50 km/s)': [
        (0, 550, 'Slow'),
        (550, 950, 'Moderate'),
        (950, 1450, 'Fast'),
        (1450, 3000, 'Super Fast')
    ],

    'Moderate (+50 km/s)': [
        (0, 650, 'Slow'),
        (650, 1050, 'Moderate'),
        (1050, 1550, 'Fast'),
        (1550, 3000, 'Super Fast')
    ],
    
    'Slight (-25 km/s)': [
        (50, 575, 'Slow'),
        (575, 975, 'Moderate'),
        (975, 1475, 'Fast'),
        (1475, 3000, 'Super Fast')
    ],
    
    'Slight (+50 km/s)': [
        (0, 625, 'Slow'),
        (625, 1025, 'Moderate'),
        (1025, 1525, 'Fast'),
        (1525, 3000, 'Super Fast')
    ]
}


# ------------------------------------------------------------
# 4. MONTHLY CORRELATION CALCULATION
# ------------------------------------------------------------
def calc_corr_monthly(df_sn, df_cmes, bins):

    results = {}

    for vmin, vmax, label in bins:

        subset = df_cmes[
            (df_cmes['Rapidez'] >= vmin) &
            (df_cmes['Rapidez'] < vmax)
        ]

        monthly_counts = (
            subset.groupby('Date')
                  .size()
                  .reset_index(name='CME_Count')
        )

        merged = pd.merge(df_sn, monthly_counts,
                          on='Date', how='inner')

        if len(merged) < 10:
            continue

        rho, p = spearmanr(
            merged['SSN'],
            merged['CME_Count']
        )

        results[label] = rho

    return results

# ------------------------------------------------------------
# 5. ANALYSIS PER BIN
# ------------------------------------------------------------
all_results = {}

for name, bins in binning_schemes.items():
    print(f"\n[{name}]")
    res = calc_corr_monthly(df_sn, df_cmes, bins)
    all_results[name] = res

    for k, v in res.items():
        print(f"{k:12s}  ρ = {v:.3f}")

# ------------------------------------------------------------
# 6. PERCENTAGE VARIATION CALCULATION
# ------------------------------------------------------------
print("\n" + "="*60)
print("ROBUSTEZ POR VARIACIÓN %")
print("="*60)

baseline_bins = ['Slow','Moderate','Fast','Super Fast']
summary = []

for b in baseline_bins:

    values = [
        all_results[s][b]
        for s in all_results
        if b in all_results[s]
    ]

    if len(values) < 2:
        continue

    mean_rho = np.mean(values)
    perc_var = (
        (max(values) - min(values))
        / abs(mean_rho) * 100
    )

    summary.append({
        'Bin': b,
        'Mean % Variation': perc_var
    })

    print(f"{b:12s}: Δ% = {perc_var:.2f}%")

summary_df = pd.DataFrame(summary)

# ------------------------------------------------------------
# 7. VISUALIZATION
# ------------------------------------------------------------

fig, ax = plt.subplots(figsize=(9, 5.5))

summary_df_sorted = summary_df.sort_values("Mean % Variation")

bins = summary_df_sorted['Bin']
variations = summary_df_sorted['Mean % Variation']

colors = []
for v in variations:
    if v < 5:
        colors.append('#1a1a1a')
    elif v < 10:
        colors.append('#555555')
    else:
        colors.append('#9c9c9c')

bars = ax.barh(
    bins,
    variations,
    color=colors,
    edgecolor='black',
    linewidth=1.2,
    height=0.65,
    zorder=3
)

for bar in bars:
    width = bar.get_width()
    ax.text(
        width + 0.3,
        bar.get_y() + bar.get_height()/2,
        f"{width:.2f}%",
        va='center',
        fontsize=10
    )

ax.axvline(5, color='black', linestyle='--',
           linewidth=1.3, alpha=0.7,
           label='Highly robust (5%)')

ax.axvline(10, color='black', linestyle=':',
           linewidth=1.3, alpha=0.7,
           label='Moderate (10%)')
ax.axvline(15, color='black', linestyle='-.',
           linewidth=1.3, alpha=0.7,
           label='Moderate sensibility (15%)')

ax.axvspan(0, 5, alpha=0.08, color='black', zorder=0)
ax.axvspan(5, 10, alpha=0.04, color='black', zorder=0)

ax.set_xlabel(
    'Mean Percentage Variation of Correlation',
    fontsize=12,
    fontweight='bold'
)

ax.set_ylabel(
    'Velocity Bin',
    fontsize=12,
    fontweight='bold'
)

ax.set_xlim(0, max(variations) * 1.15)

ax.grid(
    axis='x',
    linestyle='--',
    linewidth=0.6,
    alpha=0.35,
    zorder=0
)

ax.tick_params(
    axis='both',
    which='major',
    labelsize=11,
    direction='in',
    length=6,
    width=1,
    top=True,
    right=True
)

for spine in ax.spines.values():
    spine.set_linewidth(1.2)

ax.legend(
    loc='lower right',
    fontsize=10,
    frameon=True
)

plt.tight_layout()

# ------------------------------------------------------------
# SAVE FIGURE
# ------------------------------------------------------------
plt.savefig(
    'robustness_monthly.pdf',
    dpi=800,
    bbox_inches='tight',
    facecolor='white'
)

print("\n✓ Saved figure: robustness_monthly.pdf")
plt.show()
