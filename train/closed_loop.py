"""closed loop in a splat world: render, predict, steer, move 0.5 m, repeat"""
import csv
import math
import os
import sys

import cv2
import numpy as np
import torch

from lane_common import NORM, fit_geometry, intrinsics, load_frames, net, pose_at, to_tensor, along
from render_offsets import render, world_loader

START_OFF, STEP, CAP, LOOKAHEAD = 2.5, 0.5, 5.0, 5.0
tag, cfg, sets = sys.argv[1], sys.argv[2], sys.argv[3:]
tj, fr = load_frames(); g = fit_geometry(fr); _, _, Ks = intrinsics(tj)
track = sorted([f for f in fr if f["walk"] == "w0b"], key=lambda f: along(g, f["c2w"]))   # w0b is denser
S = np.array([along(g, f["c2w"]) for f in track])
pipe, tomodel = world_loader(cfg)
os.makedirs("lane/results", exist_ok=True)


def pose(s, y, th):
    a = track[int(np.argmin(np.abs(S - s)))]
    p = pose_at(g, a["c2w"], y, th)
    p[:3, 3] += (s - along(g, a["c2w"])) / g["k"] * g["d"]
    return p


for st in sets:
    m = net(); m.load_state_dict(torch.load(f"lane/models/{st}.pt", map_location="cpu")); m = m.cuda().eval()
    s, y, th = S[0] + 1.0, START_OFF, 0.0
    steps = int((S[-1] - 1.0 - s) / STEP)
    vw = cv2.VideoWriter(f"lane/results/closed_{tag}_{st}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 8, (480, 270))
    rows = []
    for i in range(steps):
        img = render(pipe, tomodel, Ks, pose(s, y, th))
        with torch.no_grad():
            po, ph = (m(to_tensor(img)[None].cuda()).float().cpu().numpy()[0] * NORM)
        want = -math.degrees(math.atan2(po, LOOKAHEAD))        # aim 5 m ahead
        dth = float(np.clip(want - ph, -CAP, CAP))
        rows.append((i, round(s, 3), round(y, 4), round(th, 3), round(float(po), 4), round(float(ph), 3)))
        fr_ = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.putText(fr_, f"{st}  true {y:+.2f} m  pred {po:+.2f} m  head {th:+.1f}", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 255), 1)
        vw.write(fr_)
        th += dth
        s += STEP * math.cos(math.radians(th)); y += STEP * math.sin(math.radians(th))
    vw.release()
    with open(f"lane/results/closed_{tag}_{st}.csv", "w", newline="") as fh:
        csv.writer(fh).writerows([("step", "along_m", "true_offset_m", "heading_deg", "pred_offset_m", "pred_heading_deg"), *rows])
    print(f"== closed {tag} {st}: {steps} steps, final offset {y:+.2f} m -> {'SUCCESS' if abs(y) < 0.3 else 'FAIL'}", flush=True)

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(7, 3.4))
for st in sets:
    a = np.array([[float(r["along_m"]), float(r["true_offset_m"])] for r in csv.DictReader(open(f"lane/results/closed_{tag}_{st}.csv"))])
    ax.plot(a[:, 0], a[:, 1], label=st)
ax.axhline(0, color="k", lw=.8); ax.axhspan(-.3, .3, color="g", alpha=.12, label="success band (±30 cm)")
ax.set(xlabel="distance along the street (m)", ylabel="offset from the line (m)", title=f"Closed loop in world {tag}")
ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(f"lane/results/closed_{tag}.png", dpi=130)
