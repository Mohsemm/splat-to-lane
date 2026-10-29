"""pick the 2 best variants for extra seeds"""
import csv
import sys

spec = {"G_strict": ("G", "lane/renders_Astrict", 15), "G_big": ("G", "lane/renders_Abig", 15), "G2_big": ("G2", "lane/renders_Bbig", 15)}
for fam in ("G", "G2"):
    for line in open("lane/results/q3_choice.txt"):
        f, best, cfg, _ = line.split()
        if f == fam:
            spec[f"{fam}_20k"] = (fam, f"lane/renders_{fam}20k", 30)
rows = {r["variant"]: r for r in csv.DictReader(open(sys.argv[1]))}
def score(v): return (float(rows[v]["w1_cm"].split("+")[0]) + float(rows[v]["w3_cm"].split("+")[0])) / 2
cands = sorted([v for v in spec if v in rows], key=score)[:2]
for v in cands:
    s, r, e = spec[v]; print(v, s, r, e)
