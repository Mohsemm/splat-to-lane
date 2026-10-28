"""test W, G, G2, R on the real frames of walks 0-3"""
import csv
import os

import cv2
import numpy as np
import torch

from lane_common import NORM, net, to_tensor

real = [r for r in csv.DictReader(open("lane/real_labels.csv"))]
walks = ["w0", "w1", "w2", "w3"]
os.makedirs("lane/results", exist_ok=True); rows = []
for s in ("W", "G", "G2", "R"):
    if not os.path.exists(f"lane/models/{s}.pt"):
        print("missing", s); continue
    m = net(); m.load_state_dict(torch.load(f"lane/models/{s}.pt", map_location="cpu")); m = m.cuda().eval()
    for w in walks:
        rs = [r for r in real if r["walk"] == w]
        x = torch.stack([to_tensor(cv2.cvtColor(cv2.imread(f"lane/real/{r['frame']}.jpg"), cv2.COLOR_BGR2RGB)) for r in rs])
        with torch.no_grad():
            p = torch.cat([m(x[i:i+64].cuda()).float().cpu() for i in range(0, len(x), 64)]).numpy() * NORM
        y = np.array([[float(r["offset_m"]), float(r["heading_deg"])] for r in rs])
        e = np.abs(p - y)
        rows.append((s, w, round(float(y[:, 0].mean()), 2), len(rs), round(float(e[:, 0].mean() * 100), 1),
                     round(float(np.median(e[:, 0]) * 100), 1), round(float(e[:, 1].mean()), 2), round(float(p[:, 0].mean()), 2)))
with open("lane/results/real_errors.csv", "w", newline="") as fh:
    csv.writer(fh).writerows([("set", "walk", "true_offset_m", "n", "offset_mae_cm", "offset_median_cm", "heading_mae_deg", "mean_pred_offset_m"), *rows])
print("set walk true_m n offset_MAE_cm median_cm heading_MAE_deg mean_pred_m")
for r in rows: print(*r)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6.4, 4))
names = {"W": "W: 2D warps", "G": "G: 3D renders (1-walk world)", "G2": "G2: 3D renders (2-walk world)", "R": "R: real walks 0+2"}
for s in names:
    pts = [(r[2], r[4]) for r in rows if r[0] == s]
    if pts: ax.plot(*zip(*pts), marker="o", label=names[s])
ax.set(xlabel="true sideways offset of the real walk (m)", ylabel="lane-position error on real frames (cm)",
       title="Street-in-3D: error vs offset (real test frames)"); ax.grid(alpha=.3); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig("lane/results/error_vs_offset.png", dpi=130)
print("== eval done")
