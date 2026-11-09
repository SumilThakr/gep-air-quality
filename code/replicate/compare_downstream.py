#!/usr/bin/env python3
"""Compare replication_output with the as-run tables in expected/."""
import filecmp, os
import numpy as np, pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
T = f"{ROOT}/replication_output/test_config_output"
E = f"{ROOT}/expected"
for f in ("dep_deaths_avoided.csv", "dust_deaths_avoided.csv", "economic_benefits.csv"):
    print(f"{f}: byte-identical {filecmp.cmp(f'{T}/{f}', f'{E}/{f}', shallow=False)}")
a, b = pd.read_csv(f"{T}/economic_benefits.csv"), pd.read_csv(f"{E}/economic_benefits.csv")
for c in ("Dep_Deaths", "Dust_Deaths", "VSL", "Dep_Benefit_USD", "Dust_Benefit_USD"):
    print(f"  {c}: total {a[c].sum():.8g} vs {b[c].sum():.8g}, max diff {np.abs(a[c] - b[c]).max():.3e}")
print("Countries equal:", (a.Country == b.Country).all(), " FIDs equal:", (a.FID == b.FID).all())
