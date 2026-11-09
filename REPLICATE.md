# Replicating the air-quality values

## Introduction

This guide explains how to rerun the code in this repository. The scripts in `code/1_emissions`, `code/2_inmap`, `code/3_health`, and `code/4_vsl` are the versions that ran, with machine-specific paths removed. Rerunning the steps after InMAP reproduces the final table, and a sample rerun of the emission steps matched the saved results. InMAP itself has not been rerun.

## Data

| Input | Files | Size | Source |
|---|---|---|---|
| MERRA-2 hourly single-level diagnostics (M2T1NXSLV 5.12.4), 2019 | 365 | 141 GB | NASA GES DISC |
| SMOPS blended soil moisture, 2019 | 365 | 21 GB | NOAA CLASS |
| GHAP monthly PM2.5, 1 km, 2019 (`GHAP_PM2.5_M1K_2019MM_V1.nc`) | 12 | 950 MB | Zenodo record 10800980 |
| USGS land use, GLCC v2, 1 km (`gblulcg20.tif`) | 1 | 662 MB | USGS |
| LAI by Olson class, 2020 (`Yuan_proc_MODIS_XLAI.025x025.2020.nc`) | 1 | 108 MB | GEOS-Chem HEMCO data |
| InMAP grid (`global_inmap_004x003_v1.0.0.gob`, named `global_inmap_004x003-rasterpop.gob` in the configurations) | 1 | 728 MB | https://doi.org/10.5281/zenodo.4641948 |
| Health inputs (`basemorts/`, `ijhats/`, `inputs/`) | 524 | 6 GB | GEP data drive |
| InMAP outputs (`dep.*`, `dust.*`) | 10 | 170 MB | GEP data drive |
| Country boundaries (`ee_r250_correspondence.gpkg`) | 1 | 83 MB | GEP data drive |

Members of the GEP project can find the data-drive files in the air-quality folder of the GEP data drive, along with checksums for the emission inputs.

## Steps after InMAP

This command rebuilds the Go tools, reruns every step from the InMAP outputs to the final table, and compares the results with `expected/`. It takes about 8 minutes, and it needs Go, the NetCDF C library, and the Python environment in `code/1_emissions/environment_luep-analysis.yml`.

```bash
DATADIR=/path/to/health_inputs \
INMAP_OUTPUTS=/path/to/inmap_outputs \
COUNTRIES=/path/to/ee_r250_correspondence.gpkg \
PY=/path/to/python \
code/replicate/run_downstream.sh
```

`export_country_csv.py` replaces a manual QGIS export. `make_vsl_with_fid.py` rebuilds a hand-made table, matching it exactly, including its rounding to 10 significant figures.

## Emissions

The emission scripts use paths relative to the working directory, which needs `grid.tif`, `inputs/`, `intermediate/`, and `outputs/`. A full run needs about 150 GB. The scripts expect the inputs above, plus the files in `inputs_small/`, with `soil_texture.tif` placed in `intermediate/`.

Deposition runs in the order `dep_1`, `dep_2`, `dep_3`, `dep_4`, followed by `utils/convert_deposition_to_inmap.py` and `utils/regrid_deposition_to_dust.py`. The last-used `run_deposition_calculation.py` has its first 3 steps commented out, and `inputdir` should point to `inputs`.

Dust runs `dust_2` and `dust_3` once per scenario, through `run_dust_emissions.py`. `dust_2_flux_calc.py` is set to current land cover. For the barren scenario, uncomment the `global_file` line that names `gblulcg20_10000_devegetated.tif` and comment out the line that follows it. After each run, rename `outputs/dust_sum.tiff` to `2019_dust_vegetation_on.tiff` or `2019_dust_vegetation_off.tiff`, and then pass both to `utils/calculate_dust_difference_inmap.py`. `gep_counterfactual/create_devegetated_scenario.py` builds the barren land cover, and it reads and writes relative to `../inputs`.

## InMAP

`code/2_inmap` holds the 2 Slurm scripts and configurations as they ran. Set the environment variable `INMAP_INPUTS` to the folder holding the grid and emission files, and add your Slurm account to the job scripts. The runs read a saved grid, so they do not need the meteorology or population files named in the configurations. Each case takes about 3 to 4 hours.

## What has been checked

| Step | Result |
|---|---|
| Barren land cover | Identical in all 6.9M cells |
| Dust flux, current land cover | Identical on 4 sample days, including wind and friction velocity |
| Dust totals, both scenarios | Rebuilt for 365 days from the sample-run land-cover factors and saved daily wind and soil moisture, with a 99th percentile cell error of 6e-7 |
| Annual dust, dust difference, deposition regridding | Identical |
| LAI by land class | Matches within 5e-7 |
| Monthly leaf area, July and December, every 100th pixel | Matches within 3e-7 |
| Deposition velocity, December | Identical |
| Annual deposition, all 12 months from saved intermediates, every 100th pixel | Identical |
| Grid and country deaths | Byte-identical |
| Age and VSL tables | Python reimplementation matches, and the R scripts have not been run |
| Final table | Matches within $0.00002 per country |
| InMAP | Not rerun |
