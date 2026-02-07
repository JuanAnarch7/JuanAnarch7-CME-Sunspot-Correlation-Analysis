# JuanAnarch7-CME-Sunspot-Correlation-Analysis
Statistical analysis of correlations between coronal mass ejections and sunspot activity across solar cycles.

# CME–Sunspot Correlations

Statistical analysis of the relationship between Coronal Mass Ejection (CME) occurrence rates and sunspot activity across solar cycles. This project evaluates the robustness of CME–sunspot coupling using correlation analysis, bootstrap confidence intervals, and sensitivity tests across CME velocity regimes.

The repository is designed to ensure reproducibility of results used in scientific publications and related studies.

---

## Project Objectives

- Quantify correlations between CME occurrence rates and sunspot numbers.
- Evaluate robustness across CME velocity subsets.
- Estimate confidence intervals via bootstrap resampling.
- Test sensitivity of correlations to data selection and filtering.
- Support reproducible solar-cycle variability studies.

---

## Repository Structure

CME-Sunspot-Correlation-Analysis/
├── README.md
├── LICENSE
├── requirements.txt
├── scripts/
│ ├── 02_normality_tests.py
│ ├── 03_correlation_analysis.py
│ └── 04_sensitivity_analysis.py
└── data/
└── README.md

## Data Description

The analysis combines CME and sunspot datasets:

- **Sunspot numbers:** International Sunspot Number provided by SILSO (Royal Observatory of Belgium).
- **CME data:** Processed CME catalog derived from SOHO/LASCO observations.

Processed datasets are used to ensure consistent event filtering and temporal aggregation. Raw datasets are not distributed in this repository; instructions and sources are described in `data/README.md`.

---

## Scripts Description

The scripts directory contains analysis pipelines used to generate results:

- `02_normality_tests.py`  
  Evaluates statistical properties and stationarity of time series.

- `03_correlation_analysis.py`  
  Computes correlations between CME occurrence rates and sunspot numbers for velocity-defined subsets.

- `04_sensitivity_analysis.py`  
  Evaluates robustness of correlations under different binning and filtering choices.



