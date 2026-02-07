# ============================================================
# NORMALITY TESTS ANNUAL
# ============================================================
import pandas as pd
import numpy as np
import pingouin as pg
from scipy.stats import spearmanr, shapiro
from scipy import stats
import matplotlib.pyplot as plt

# ============================================================
# 1. DATA LOADING
# ============================================================

df_sn = pd.read_csv("SN_y_tot_V2.0(1).txt", sep=r'\s+', header=None, 
                    usecols=[0, 1], names=['Year', 'SunspotNumber'])
df_sn['Year'] = df_sn['Year'].astype(int)
print(f"   ✓ SSN cargado: {len(df_sn)} años ({df_sn['Year'].min()}-{df_sn['Year'].max()})")


df_cmes = pd.read_csv("datos_procesados_2025_09_30.csv", low_memory=False)
df_cmes['Fecha'] = pd.to_datetime(df_cmes['Fecha'], errors='coerce')
df_cmes[['Central', 'Ancho', 'Rapidez']] = df_cmes[['Central', 'Ancho', 'Rapidez']].apply(
    pd.to_numeric, errors='coerce'
)
df_cmes['Year'] = df_cmes['Fecha'].dt.year
df_cmes = df_cmes.dropna(subset=['Rapidez', 'Year'])
print(f"   ✓ CMEs cargados: {len(df_cmes)} eventos")
print(f"   ✓ Rango temporal: {df_cmes['Year'].min()}-{df_cmes['Year'].max()}")

# ============================================================
# 2. BUILD ANNUAL SERIES
# ============================================================

annual_cme_total = (
    df_cmes.groupby("Year").size().reset_index(name="CME_Count")
)

data_full = pd.merge(df_sn, annual_cme_total, on="Year", how="inner")
data_full = data_full.dropna()

# Period used in analysis
data_full = data_full[
    (data_full["Year"] >= 1996) & (data_full["Year"] <= 2024)
]

data_for_test = data_full[["SunspotNumber", "CME_Count"]]

print(f"\nObservations used: {len(data_for_test)}")

# ============================================================
# 3. HENZE–ZIRKLER TEST
# ============================================================

print("\n--- Henze–Zirkler multivariate normality test ---")

hz_stat, hz_p, hz_normal = pg.multivariate_normality(
    data_for_test, alpha=0.05
)

print(f"HZ statistic : {hz_stat:.6f}")
print(f"p-value      : {hz_p:.6f}")

if not hz_normal:
    print("Result       : Normality REJECTED")
else:
    print("Result       : Normality NOT rejected")

# ============================================================
# 4. MARDIA TEST (Skewness & Kurtosis)
# ============================================================

def mardia_test(X):
    if isinstance(X, pd.DataFrame):
        X = X.values

    n, p = X.shape
    Xc = X - np.mean(X, axis=0)

    S = np.cov(Xc.T)
    S_inv = np.linalg.pinv(S)

    # --- Skewness ---
    b1p = 0
    for i in range(n):
        for j in range(n):
            diff = Xc[i] - Xc[j]
            m_dist = diff @ S_inv @ diff.T
            b1p += m_dist**3
    b1p /= n**2

    chi2_skew = n * b1p / 6
    df_skew = p * (p + 1) * (p + 2) / 6
    p_skew = 1 - stats.chi2.cdf(chi2_skew, df_skew)

    # --- Kurtosis ---
    b2p = 0
    for i in range(n):
        md = Xc[i] @ S_inv @ Xc[i].T
        b2p += md**2
    b2p /= n

    expected = p * (p + 2)
    var = 8 * p * (p + 2) / n
    z_kurt = (b2p - expected) / np.sqrt(var)
    p_kurt = 2 * (1 - stats.norm.cdf(abs(z_kurt)))

    return p_skew, p_kurt, chi2_skew, z_kurt


p_skew, p_kurt, chi2_skew, z_kurt = mardia_test(data_for_test)

print("\n--- Mardia multivariate normality test ---")

print(f"Skewness χ² : {chi2_skew:.6f}")
print(f"Skewness p  : {p_skew:.6f}")

if p_skew < 0.05:
    print("Skewness    : Normality REJECTED")
else:
    print("Skewness    : Not rejected")

print(f"\nKurtosis z  : {z_kurt:.6f}")
print(f"Kurtosis p  : {p_kurt:.6f}")

if p_kurt < 0.05:
    print("Kurtosis    : Normality REJECTED")
else:
    print("Kurtosis    : Not rejected")

# ============================================================
# 5. FINAL DECISION
# ============================================================

reject_count = sum([
    not hz_normal,
    p_skew < 0.05,
    p_kurt < 0.05
])

print("\n--- Final conclusion ---")
if reject_count > 0:
    print("Multivariate normality REJECTED.")
else:
    print("Multivariate normality NOT rejected.")