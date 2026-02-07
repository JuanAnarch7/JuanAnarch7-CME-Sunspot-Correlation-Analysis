# ============================================================
# NORMALITY TESTS (MONTHLY) — SIMPLIFIED VERSION
# Keeps only Henze–Zirkler and Mardia tests
# Prints results and whether normality is rejected
# ============================================================

import pandas as pd
import numpy as np
import pingouin as pg
from scipy import stats

# ============================================================
# 1. LOAD DATA
# ============================================================

# Monthly Sunspot Number
df_sn = pd.read_csv(
    "SN_m_tot_V2.0.txt",
    sep=r"\s+",
    header=None,
    usecols=[0, 1, 3],
    names=["Year", "Month", "SSN"],
)

df_sn["Year"] = df_sn["Year"].astype(int)
df_sn["Month"] = df_sn["Month"].astype(int)
df_sn["Date"] = pd.to_datetime(
    df_sn[["Year", "Month"]].assign(Day=1)
)

# CME catalog
df_cmes = pd.read_csv("datos_procesados_2025_09_30.csv", low_memory=False)
df_cmes["Fecha"] = pd.to_datetime(df_cmes["Fecha"], errors="coerce")

df_cmes[["Central", "Ancho", "Rapidez"]] = df_cmes[
    ["Central", "Ancho", "Rapidez"]
].apply(pd.to_numeric, errors="coerce")

df_cmes = df_cmes.dropna(subset=["Fecha", "Rapidez"])
df_cmes["YearMonth"] = df_cmes["Fecha"].dt.to_period("M")

# ============================================================
# 2. BUILD MONTHLY SERIES
# ============================================================

monthly_cme = (
    df_cmes.groupby("YearMonth")
    .size()
    .reset_index(name="CME_Count")
)

monthly_cme["Date"] = monthly_cme["YearMonth"].dt.to_timestamp()

df_sn_filtered = df_sn[
    (df_sn["Year"] >= 1996) & (df_sn["Year"] <= 2024)
]

data_full = pd.merge(
    df_sn_filtered[["Date", "SSN"]],
    monthly_cme[["Date", "CME_Count"]],
    on="Date",
    how="inner",
).dropna()

data_for_test = data_full[["SSN", "CME_Count"]]

print(f"\nMonthly observations used: {len(data_for_test)}")

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
# 4. MARDIA TEST
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
            md = diff @ S_inv @ diff.T
            b1p += md**3
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
