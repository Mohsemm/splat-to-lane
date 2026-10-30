"""main plot: error vs offset, mean +- std over seeds"""
import csv
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

X = [0.03, 0.93, 1.93, 3.07]  # colmap offsets
rows = {r["variant"]: r for r in csv.DictReader(open(sys.argv[1]))}


def mv(s):
    p = s.split("+-"); return float(p[0]), float(p[1]) if len(p) > 1 else 0.0


style = {"W": ("2D warps, 6k (W)", "#d1495b", "o"), "R": ("real frames, walks 0+2 (R)", "#8d8d8d", "s"),
         "G": ("3D renders, 6k (G)", "#66a3d2", "^"), "G2": ("3D renders 2-walk world, 6k (G2)", "#2e6f9e", "v"),
         "G_20k": ("3D renders, 20k x 30 ep (G_20k; matched W-20k pending)", "#30a46c", "D"), "G2_20k": ("3D renders 2-walk, 20k x 30 ep (G2_20k)", "#1b6b45", "P")}
fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
for k, (lab, c, m) in style.items():
    v = [mv(rows[k][f"w{i}_cm"]) for i in range(4)]
    ax.errorbar(X, [a for a, _ in v], yerr=[b for _, b in v], label=lab, color=c, marker=m, capsize=3, lw=2)
ax.set_xlabel("true lateral offset of the real test walk from the filmed path (m)")
ax.set_ylabel("offset error on real frames, MAE (cm)")
ax.set_title("Lane-offset error on real iPhone frames (mean ± std over 3 seeds)")
ax.grid(alpha=.3); ax.legend(fontsize=8, frameon=False); ax.set_ylim(0, 190)
ax.annotate("R trained on walk 2", xy=(1.93, 0.7), xytext=(1.5, 30), fontsize=8, arrowprops=dict(arrowstyle="->", color="#8d8d8d"))
fig.tight_layout(); fig.savefig(sys.argv[2])
