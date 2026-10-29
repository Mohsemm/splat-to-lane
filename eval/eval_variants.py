"""eval named groups of nets on the real walks (mean +- std)"""
import csv
import os
import sys

import cv2
import numpy as np
import torch

from lane_common import NORM, net, to_tensor

out, specs = sys.argv[1], sys.argv[2:]
real = [r for r in csv.DictReader(open("lane/real_labels.csv"))]
walks = ["w0", "w1", "w2", "w3"]
X = {w: torch.stack([to_tensor(cv2.cvtColor(cv2.imread(f"lane/real/{r['frame']}.jpg"), cv2.COLOR_BGR2RGB)) for r in real if r["walk"] == w]) for w in walks}
Y = {w: np.array([float(r["offset_m"]) for r in real if r["walk"] == w]) for w in walks}
rows = []
for sp in specs:
    g, names = sp.split("="); errs = {w: [] for w in walks}
    for nm in names.split(","):
        if not os.path.exists(f"lane/models/{nm}.pt"):
            print("missing", nm); continue
        m = net(); m.load_state_dict(torch.load(f"lane/models/{nm}.pt", map_location="cpu")); m = m.cuda().eval()
        for w in walks:
            with torch.no_grad():
                p = torch.cat([m(X[w][i:i+64].cuda()).float().cpu() for i in range(0, len(X[w]), 64)]).numpy()[:, 0] * NORM[0]
            errs[w].append(float(np.abs(p - Y[w]).mean() * 100))
    rows.append([g, len(errs["w0"])] + [f"{np.mean(errs[w]):.1f}" + (f"+-{np.std(errs[w], ddof=1):.1f}" if len(errs[w]) > 1 else "") for w in walks])
with open(f"lane/results/{out}.csv", "w", newline="") as fh:
    csv.writer(fh).writerows([("variant", "n_models", "w0_cm", "w1_cm", "w2_cm", "w3_cm"), *rows])
for r in rows: print(*r)
