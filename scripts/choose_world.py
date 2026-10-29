"""pick the better world per family for the 20k run"""
import csv
import glob
import sys

rows = {r["variant"]: r for r in csv.DictReader(open(sys.argv[1]))}
def score(v): return (float(rows[v]["w1_cm"].split("+")[0]) + float(rows[v]["w3_cm"].split("+")[0])) / 2
cfg = {"G": "outputs/street_walk0/splatfacto/2026-10-28_204550/config.yml",
       "G2": "outputs/street_walk02/splatfacto/2026-10-28_212103/config.yml",
       "G_big": sorted(glob.glob("outputs/street_walk0_big/splatfacto/*/config.yml"))[-1:] or [""],
       "G2_big": sorted(glob.glob("outputs/street_walk02_big/splatfacto/*/config.yml"))[-1:] or [""]}
cfg = {k: (v[0] if isinstance(v, list) else v) for k, v in cfg.items()}
for fam in ("G", "G2"):
    best = min([v for v in (fam, f"{fam}_big") if v in rows and cfg[v]], key=score)
    print(fam, best, cfg[best], round(score(best), 1))
