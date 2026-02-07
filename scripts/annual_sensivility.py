# ============================================================
# SENSITIVITY ANALYSIS
# ============================================================
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import matplotlib.pyplot as plt

print("="*60)
print("SENSITIVITY ANALYSIS (PERCENTAGE VARIATION)")
print("="*60)

# ============================================================
# 1. DATA LOADING
# ============================================================
df_sn = pd.read_csv("SN_y_tot_V2.0(1).txt", sep=r'\s+', header=None,
                    usecols=[0, 1], names=['Year', 'SunspotNumber'])
df_sn['Year'] = df_sn['Year'].astype(int)

df_cmes = pd.read_csv("datos_procesados_2025_09_30.csv", low_memory=False)
df_cmes['Fecha'] = pd.to_datetime(df_cmes['Fecha'], errors='coerce')
df_cmes['Rapidez'] = pd.to_numeric(df_cmes['Rapidez'], errors='coerce')
df_cmes['Year'] = df_cmes['Fecha'].dt.year
df_cmes = df_cmes.dropna(subset=['Rapidez', 'Year'])

print(f"✓ {len(df_cmes)} CMEs loaded")

# ============================================================
# 2. BINNING SCHEMES
# ============================================================
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
    
    'Slight (+25 km/s)': [
        (0, 625, 'Slow'),
        (625, 1025, 'Moderate'),
        (1025, 1525, 'Fast'),
        (1525, 3000, 'Super Fast')
    ]
}


# ============================================================
# 3. CORRELATION CALCULATION FUNCTION
# ============================================================
def calculate_correlations(df_sn, df_cmes, bins):
    results = {}

    for vmin, vmax, label in bins:
        subset = df_cmes[(df_cmes['Rapidez'] >= vmin) &
                         (df_cmes['Rapidez'] < vmax)]

        annual_counts = subset.groupby('Year').size().reset_index(name='CME_Count')
        merged = pd.merge(df_sn, annual_counts, on='Year', how='inner')
        merged = merged[(merged['Year'] >= 1996) &
                        (merged['Year'] <= 2024)]

        if len(merged) < 3:
            continue

        rho, _ = spearmanr(merged['SunspotNumber'], merged['CME_Count'])
        results[label] = rho

    return results

# ============================================================
# 4. CALCULATE RESULTS AND PRINT CORRELATIONS
# ============================================================
all_results = {}

print("\n" + "="*60)
print("CORRELATIONS BY SCHEME")
print("="*60)

for name, bins in binning_schemes.items():

    results = calculate_correlations(df_sn, df_cmes, bins)
    all_results[name] = results

    print(f"\n[{name}]")

    for label, rho in results.items():
        print(f"  {label:12s}: ρ = {rho:.3f}")

baseline = all_results["Baseline"]

# ============================================================
# 5. VARIACIÓN PORCENTUAL
# ============================================================
summary = []

print("\nPercentage change from baseline:\n")

for bin_name, rho_base in baseline.items():

    variations = []

    for scheme, results in all_results.items():
        if scheme == 'Baseline':
            continue
        if bin_name not in results:
            continue

        rho_alt = results[bin_name]
        percent_change = abs(rho_alt - rho_base) / abs(rho_base) * 100
        variations.append(percent_change)

    mean_variation = np.mean(variations)

    summary.append({
        'Bin': bin_name,
        'Baseline ρ': rho_base,
        'Mean % Variation': mean_variation
    })

    print(f"{bin_name:12s} → Δρ ≈ {mean_variation:.2f}%")

summary_df = pd.DataFrame(summary)
summary_df.to_csv("sensitivity_percent_variation.csv", index=False)

print("\n✓ Results saved to sensitivity_percent_variation.csv")
print("="*60)

# ============================================================
# 6. VISUALIZATION
# ============================================================
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(9, 5.5))

summary_df_sorted = summary_df.sort_values("Mean % Variation")

bins = summary_df_sorted['Bin']
variations = summary_df_sorted['Mean % Variation']

colors = []
for v in variations:
    if v < 5:
        colors.append('#1a1a1a')   # Robust
    elif v < 10:
        colors.append('#555555')   # Moderate
    else:
        colors.append('#9c9c9c')   # Moderate Sensibility

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
           linewidth=1.3, alpha=0.7)

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
# Save figure
# ------------------------------------------------------------
plt.savefig(
    'robustness_annual.pdf',
    dpi=800,               
    bbox_inches='tight',
    facecolor='white'
)

print("\n✓ Figure Saved: robustness_annual.pdf")
plt.show()