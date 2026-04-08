# Data Directory

This folder documents the datasets used in the CME–sunspot
correlation analysis.

## Included Datasets

### 1. Processed CME Catalog

File: "datos_procesados_2025_09_30.csv"

This file contains CME events derived from the SOHO/LASCO CME
catalog after preprocessing.

The dataset is lightweight (~3 MB) and is included to allow direct
reproducibility of the analysis.

### 2. Annual Paired Time Series

File: `master_annual_paired_series.csv`

This file contains the **aligned annual time series** used in the correlation analysis.  
It includes:

- Annual sunspot numbers  
- Annual CME counts for each velocity bin:
  - Slow (0–600 km/s)
  - Moderate (600–1000 km/s)
  - Fast (1000–1500 km/s)
  - Extreme (>1500 km/s)

Each row corresponds to a calendar year, and all series are **synchronized**, ensuring that
correlation calculations are performed on consistent paired observations.

---

### 3. Monthly Paired Time Series

File: `master_monthly_paired_series_corrected.csv`

This file contains the **aligned monthly time series** used in the high-resolution analysis.  
It includes:

- Monthly sunspot numbers  
- Monthly CME counts for each velocity bin

Key features:

- Time series are aligned at monthly resolution
- Data gaps due to SOHO/LASCO interruptions (e.g., 1998–1999) have been removed
- The dataset is prepared for **block bootstrap resampling**


### Column Language

Column names are kept in Spanish to match the original processing
pipeline:

- `Fecha` — CME occurrence date
- `Rapidez` — CME linear speed (km/s)
- `Ancho` — angular width (degrees)
- `Central` — central position angle (degrees)

## CME Data Source

Raw CME observations come from:

SOHO/LASCO CME Catalog  
https://cdaw.gsfc.nasa.gov/CME_list/

## CME Preprocessing Steps

The raw catalog was processed before analysis:

1. Conversion of event dates to standard datetime format.
2. Removal of events with missing speed or invalid entries.
3. Conversion of numerical columns to numeric format.
4. Extraction of event year and month for time-series aggregation.
5. Standardization of column names.
6. Aggregation into annual or monthly occurrence rates.

These steps allow direct use in statistical analyses without further cleaning.

## Sunspot Data

Sunspot numbers are **not included** in this repository and should
be downloaded from:

SILSO – Royal Observatory of Belgium  
https://www.sidc.be/silso/

The scripts automatically read the downloaded dataset once placed in
the project directory.

## Reproducibility

All analyses can be reproduced using:

- The processed CME catalog
- The aligned annual and monthly paired datasets
- Publicly available sunspot data

The repository includes:

- Fully prepared time series for correlation analysis
- Scripts for statistical analysis and figure generation
- A complete computational environment specification (`requirements.txt`)

The inclusion of pre-aligned datasets allows users to:

- Directly reproduce correlation results
- Validate intermediate data products
- Avoid reprocessing steps if desired

---

## Notes on Statistical Analysis

- Annual analyses use **paired bootstrap resampling**
- Monthly analyses use **block bootstrap resampling** (block size = 12 months)

This distinction reflects the different levels of temporal autocorrelation
present in the data and ensures robust estimation of confidence intervals
