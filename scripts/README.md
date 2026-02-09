# Scripts Directory

This folder contains the analysis scripts used to study correlations
between CME occurrence rates and sunspot activity.

All scripts can be executed independently, provided the required
input datasets are available.

## Analysis Organization

Scripts are provided for analyses performed in both:

- Annual temporal resolution
- Monthly temporal resolution

Each script performs a specific step of the statistical analysis,
including stationarity diagnostics, correlation estimation, bootstrap
confidence intervals, and sensitivity tests.

## Inputs

Scripts expect processed CME and sunspot datasets as described in
`data/README.md`.
## Script Types and Outputs

Scripts are grouped according to their purpose:

### Correlation analysis scripts
(e.g., `Annual_correlation.py`, `Monthly_correlation.py`)

These scripts:

- Compute correlations between CME occurrence rates and sunspot numbers.
- Generate a figure saved in **PDF format**.
- Produce a **CSV file** containing a statistical summary of the analysis.
- Allow modification of the analysis period through commented
  sections in the script.

Note: the output PDF filename must currently be specified manually
inside the script before execution.

---

### Sensitivity analysis scripts
(e.g., `annual_sensitivity.py`, `Monthly_sensitivity.py`)

These scripts generate figures used to evaluate the robustness of
correlations under different parameter selections. No CSV files are produced.

---

### Test scripts
(e.g., `Annual_test.py`, `Monthly_test.py`)

These scripts perform statistical diagnostics and display results
directly in the execution terminal without generating files.


## Configuration Notes

Some analysis parameters, such as the temporal period studied,
can be modified directly in each script via commented configuration
sections.


## Outputs

Scripts generate statistical summaries and figures used in the analysis
and publications derived from this project.

## Execution Notes
