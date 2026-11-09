# gep-air-quality

This repository holds the code that produced the air-quality values in Gross Ecosystem Product (GEP). It covers 2 services, air filtration by vegetation and sandstorm prevention. The code is the version that ran in November 2025, and it reproduces $17.81B for air filtration (5,522 avoided deaths) and $595.4B for sandstorm prevention (250,778 avoided deaths), in the units used by the GEP workbook of 2025-11-11.

The code is kept as it ran, apart from machine-specific paths, so that the published values can be reproduced exactly.

## The pipeline

| Step | Code | Output |
|---|---|---|
| Deposition of PM2.5 to vegetation | `code/1_emissions/dep_scripts` | 1.815 Tg |
| Windblown dust, current and barren land cover | `code/1_emissions/dust_scripts`, `gep_counterfactual` | 417.3 and 567.7 Tg, a difference of 150.3 Tg |
| Format for InMAP | `code/1_emissions/utils` | 2 NetCDF emission files |
| PM2.5 concentrations | Global InMAP, configured by `code/2_inmap` | `dep.shp`, `dust.shp` |
| Deaths on the InMAP grid (GEMM, 5 causes, proportional attribution) | `code/3_health/main.go` | Grid deaths |
| Deaths by GEP country | `code/3_health/deathsbycountry_dust.go` | Country deaths |
| Value of a statistical life | `code/4_vsl` (Raahil Madhok) | VSL by country |
| Dollars | `code/3_health/utils/calculate_benefits.py` | `economic_benefits.csv` |

`REPLICATE.md` explains how to rerun each step and records which steps have been checked.

## Contents

| Path | What it is |
|---|---|
| `code/` | The as-run scripts. `code/replicate/` holds the runner, 2 scripts that replace manual steps, and the comparison. |
| `inputs_small/` | Small input tables and rasters |
| `expected/` | As-run country deaths and final values to compare against |
| `REPLICATE.md` | Replication instructions and status |
