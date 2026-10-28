"""label every real frame with offset + heading from colmap"""
import csv
import json
import os

import numpy as np

from lane_common import fit_geometry, label, along, load_frames

os.makedirs("lane", exist_ok=True)
tj, fr = load_frames()
g = fit_geometry(fr)
print("metres per unit k =", round(g["k"], 4), "| implied walk offsets (m):", {w: round(v, 2) for w, v in g["implied"].items()}, "|", g["flag"])
rows = []
for f in fr:
    o, h = label(g, f["c2w"])
    rows.append((f["key"], f["walk"], f["orig"], round(o, 4), round(h, 3), round(along(g, f["c2w"]), 3)))
with open("lane/real_labels.csv", "w", newline="") as fh:
    csv.writer(fh).writerows([("frame", "walk", "original", "offset_m", "heading_deg", "along_m"), *rows])
json.dump({k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in g.items()}, open("lane/geometry.json", "w"), indent=1)
for w in ("w0", "w0b", "w1", "w2", "w3", "sweep"):
    a = np.array([(r[3], r[4], r[5]) for r in rows if r[1] == w])
    print(f"{w:5s} n={len(a):3d} offset mean {a[:,0].mean():5.2f} sd {a[:,0].std():.2f} | heading mean {a[:,1].mean():6.2f} sd {a[:,1].std():.2f} | along {a[:,2].min():6.1f}..{a[:,2].max():5.1f} m")
