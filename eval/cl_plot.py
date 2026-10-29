"""closed loop plot for worlds A and B, keeps the best G video and one W video"""
import csv
import os
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

TARGET = float(os.environ.get("TARGET", "0")); PREFIX = os.environ.get("PREFIX", "cl")

col = {"W": "tab:blue", "G": "tab:orange", "G2": "tab:green"}
worlds = [w for w in ("A", "B") if os.path.exists(f"lane/results/{PREFIX}_{w}_runs.csv")]
fig, axs = plt.subplots(1, len(worlds), figsize=(6.5 * len(worlds), 3.8), squeeze=False)
summary = []
for ax, w in zip(axs[0], worlds):
    P = list(csv.DictReader(open(f"lane/results/{PREFIX}_{w}_paths.csv")))
    R = list(csv.DictReader(open(f"lane/results/{PREFIX}_{w}_runs.csv")))
    for st in col:
        rr = [r for r in R if r["set"] == st]
        if not rr: continue
        n = sum(int(r["success"]) for r in rr); mf = np.mean([abs(float(r["final_offset_m"]) - TARGET) for r in rr])
        summary.append((w, st, n, len(rr), round(mf, 2)))
        for r in rr:
            p = [x for x in P if x["set"] == st and x["run"] == r["run"]]
            x0 = float(p[0]["along_m"])
            ax.plot([float(x["along_m"]) - x0 for x in p], [float(x["true_offset_m"]) for x in p], color=col[st], alpha=.55, lw=1,
                    label=f"{st}: {n}/{len(rr)} back in lane" if r is rr[0] else None)
    ax.axhspan(TARGET - .3, TARGET + .3, color="g", alpha=.12); ax.axhline(TARGET, color="k", lw=.9, ls="--", label=f"target {TARGET} m")
    ax.axhline(0, color="grey", lw=.6); ax.text(0, 0.05, "walk-0 line (sidewalk edge)", fontsize=7, color="grey")
    ax.set(xlabel="distance driven (m)", ylabel="offset from the line (m)", title=f"Closed loop, world {w}, target {TARGET} m (10 starts/net)", ylim=(-4, 4) if TARGET == 0 else (-1, 4))
    ax.legend(fontsize=8, loc="lower left")
fig.tight_layout(); fig.savefig(f"lane/results/{PREFIX}_all.png", dpi=130)
with open(f"lane/results/{PREFIX}_summary.csv", "w", newline="") as fh:
    csv.writer(fh).writerows([("world", "set", "successes", "runs", "mean_final_abs_offset_m"), *summary])
for s in summary: print(*s)
# keep best G and one W
R = list(csv.DictReader(open(f"lane/results/{PREFIX}_A_runs.csv")))
bestG = min((r for r in R if r["set"] in ("G", "G2")), key=lambda r: abs(float(r["final_offset_m"]) - TARGET))
oneW = max((r for r in R if r["set"] == "W"), key=lambda r: abs(float(r["final_offset_m"]) - TARGET))
shutil.copy(f"lane/results/{PREFIX}_videos/{PREFIX}_A_{bestG['set']}_r{bestG['run']}.mp4", f"lane/results/{PREFIX}_{bestG['set']}_best.mp4")
shutil.copy(f"lane/results/{PREFIX}_videos/{PREFIX}_A_W_r{oneW['run']}.mp4", f"lane/results/{PREFIX}_W_example.mp4")
shutil.rmtree(f"lane/results/{PREFIX}_videos")
print("== kept", bestG["set"], "run", bestG["run"], "and W run", oneW["run"])
