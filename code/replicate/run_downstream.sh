#!/bin/bash
# Reruns everything after InMAP, from dep.shp and dust.shp to the final dollar values, and compares
# the results with expected/. Writes only to replication_output/.
#
# Required environment variables:
#   DATADIR        folder holding the health inputs (basemorts/, ijhats/, inputs/)
#   INMAP_OUTPUTS  folder holding dep.shp and dust.shp with their sidecar files
#   COUNTRIES      path to ee_r250_correspondence.gpkg
# Optional: PY (default python3), and REUSE_DEATHS=1 to keep existing deaths in replication_output.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
: "${DATADIR:?set DATADIR}" "${INMAP_OUTPUTS:?set INMAP_OUTPUTS}" "${COUNTRIES:?set COUNTRIES}"
DATADIR="${DATADIR%/}"
PY="${PY:-python3}"
OUT="$ROOT/replication_output"
BUILD="$OUT/build"
T="$OUT/test_config_output"
mkdir -p "$BUILD" "$T" "$OUT/utils"
cp "$ROOT"/code/3_health/{main.go,deathsbycountry_dust.go,go.mod,go.sum} "$BUILD/"
cd "$BUILD"
go build -o aqhealth main.go
go build -o deathsbycountry_dust deathsbycountry_dust.go

if [ -z "${REUSE_DEATHS:-}" ]; then
  for pair in "dep:deposition_deaths_avoided:deposition" "dust:dust_deaths_avoided:dust"; do
    IFS=: read -r run grid country <<< "$pair"
    cat > "$OUT/config_$run.json" <<JSON
{
  "dataDir": "$DATADIR/",
  "popFile": "inputs/pop.shp",
  "totalPMFile": "inputs/totalpm.shp",
  "gemmFile": "inputs/gemm_params.csv",
  "resultFile": "$INMAP_OUTPUTS/$run.shp",
  "outputDir": "$T/",
  "outputFile": "$grid.shp",
  "ncVarName": "PM25",
  "ncLayer": 0,
  "outputSpec": {"mode": "5cod", "causes": [], "ages": []}
}
JSON
    ./aqhealth --config "$OUT/config_$run.json"
    ./deathsbycountry_dust -mode apply-mapping \
      -input "$T/$grid.shp" \
      -output "$T/deaths_by_country_$country.shp" \
      -countries "$COUNTRIES" \
      -mapping "$ROOT/code/3_health/map.csv" -field TotalPopD
  done
fi

"$PY" "$ROOT/code/replicate/export_country_csv.py" "$T/deaths_by_country_deposition.dbf" "$T/dep_deaths_avoided.csv"
"$PY" "$ROOT/code/replicate/export_country_csv.py" "$T/deaths_by_country_dust.dbf" "$T/dust_deaths_avoided.csv"
"$PY" "$ROOT/code/replicate/make_vsl_with_fid.py" "$ROOT/code/4_vsl/data/clean/vsl.csv" "$ROOT/inputs_small/country_fid_mapping_final.csv" "$T/vsl_with_fid_final.csv"
cp "$ROOT/code/3_health/utils/calculate_benefits.py" "$OUT/utils/"
"$PY" "$OUT/utils/calculate_benefits.py"
"$PY" "$ROOT/code/replicate/compare_downstream.py"
