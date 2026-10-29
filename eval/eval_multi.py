"""eval every seed / warp height variant on the real walks"""
import csv
import os

import cv2
import numpy as np
import torch

from lane_common import NORM, net, to_tensor

real = [r for r in csv.DictReader(open("lane/real_labels.csv"))]
walks = ["w0", "w1", "w2", "w3"]
X, Y = {}, {}
for w in walks:
    rs = [r for r in real if r["walk"] == w]
    X[w] = torch.stack([to_tensor(cv2.cvtColor(cv2.imread(f"lane/real/{r['frame']}.jpg"), cv2.COLOR_BGR2RGB)) for r in rs])
    Y[w] = np.array([[float(r["offset_m"]), float(r["heading_deg"])] for r in rs])
groups = {s: [s, f"{s}_s1", f"{s}_s2"] for s in ("W", "G", "G2", "R")}
groups.update({"W_h1.2": ["W_h12"], "W_h1.6": ["W_h16"]})
per, summ = [], []
for gname, names in groups.items():
    errs = {w: [] for w in walks}
    for nm in names:
        if not os.path.exists(f"lane/models/{nm}.pt"):
            print("missing", nm); continue
        m = net(); m.load_state_dict(torch.load(f"lane/models/{nm}.pt", map_location="cpu")); m = m.cuda().eval()
        for w in walks:
            with torch.no_grad():
                p = torch.cat([m(X[w][i:i+64].cuda()).float().cpu() for i in range(0, len(X[w]), 64)]).numpy() * NORM
            e = float(np.abs(p[:, 0] - Y[w][:, 0]).mean() * 100)
            errs[w].append(e)
            per.append((gname, nm, w, round(float(Y[w][:, 0].mean()), 2), round(e, 1), round(float(np.abs(p[:, 1] - Y[w][:, 1]).mean()), 2),
                        round(float(p[:, 0].mean()), 2), round(float(p[:, 0].min()), 2), round(float(p[:, 0].max()), 2)))
    for w in walks:
        if errs[w]:
            summ.append((gname, w, len(errs[w]), round(float(np.mean(errs[w])), 1), round(float(np.std(errs[w], ddof=1)) if len(errs[w]) > 1 else 0.0, 1)))
os.makedirs("lane/results", exist_ok=True)
with open("lane/results/robust_per_model.csv", "w", newline="") as fh:
    csv.writer(fh).writerows([("group", "model", "walk", "true_offset_m", "offset_mae_cm", "heading_mae_deg", "pred_mean_m", "pred_min_m", "pred_max_m"), *per])
with open("lane/results/robust_summary.csv", "w", newline="") as fh:
    csv.writer(fh).writerows([("group", "walk", "n_models", "offset_mae_mean_cm", "offset_mae_std_cm"), *summ])
for s in summ: print(*s)
print("R on walk 3 (true ~3.07 m):", [(r[1], r[6], r[7], r[8]) for r in per if r[0] == "R" and r[2] == "w3"])
print("== robust eval done")
