#!/usr/bin/env python3
"""Attach country FIDs to vsl.csv using the saved name mapping. Replaces a manual step.

Usage: python make_vsl_with_fid.py vsl.csv country_fid_mapping_final.csv OUTPUT.csv
West Bank maps to the same FID as the Gaza Strip, so the as-run table leaves its FID empty.
The as-run table holds VSL to 10 significant figures, and the final dollars inherit that rounding.
"""
import sys
import pandas as pd

v = pd.read_csv(sys.argv[1])
# The as-run table lists these 2 names in the opposite order, and this matches it exactly.
v["country"] = v.country.replace({"serbia": "kosovo", "kosovo": "serbia"})
m = pd.read_csv(sys.argv[2])
m = m[m.match_type != "DUPLICATE"]
out = v.merge(m[["vsl_country", "FID"]], left_on="country", right_on="vsl_country", how="left")
out["FID"] = out.FID.astype("Int64")
out["vsl"] = out.vsl.map(lambda x: float(f"{x:.10g}"))
out[["FID", "country", "vsl"]].to_csv(sys.argv[3], index=False)
