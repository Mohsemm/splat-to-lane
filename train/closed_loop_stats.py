"""closed loop over 10 starts per world"""
import csv
import math
import os
import sys

import cv2
import numpy as np
import torch

from lane_common import NORM, along, fit_geometry, intrinsics, load_frames, net, pose_at, to_tensor
from render_offsets import render, world_loader

STEP, CAP, LOOKAHEAD, NSTEPS = 0.5, 5.0, 5.0, 40
TARGET = float(os.environ.get("TARGET", "0"))    # target offset, 0 = sidewalk, 1.5 = road
PREFIX = os.environ.get("PREFIX", "cl")
STARTS = [tuple(map(float, x.split(":"))) for x in os.environ.get("STARTS", "2.5:5,1.5:-5").split(",")]
tag, cfg, sets = sys.argv[1], sys.argv[2], sys.argv[3:]
tj, fr = load_frames(); g = fit_geometry(fr); _, _, Ks = intrinsics(tj)
track = sorted([f for f in fr if f["walk"] == "w0b"], key=lambda f: along(g, f["c2w"]))
S = np.array([along(g, f["c2w"]) for f in track])
pipe, tomodel = world_loader(cfg)
anchors = np.linspace(S[0] + 1.0, S[-1] - 1.0 - NSTEPS * STEP, 5)
starts = [(a, o, h) for o, h in STARTS for a in anchors]
print(f"== {tag} target {TARGET} m starts {STARTS}: walk-0b track {S[0]:.1f}..{S[-1]:.1f} m; anchors {np.round(anchors, 1).tolist()}", flush=True)


def pose(s, y, th):
    a = track[int(np.argmin(np.abs(S - s)))]
    p = pose_at(g, a["c2w"], y, th)
    p[:3, 3] += (s - along(g, a["c2w"])) / g["k"] * g["d"]
    return p


runs, paths = [], []
os.makedirs(f"lane/results/{PREFIX}_videos", exist_ok=True)
for st in sets:
    m = net(); m.load_state_dict(torch.load(f"lane/models/{st}.pt", map_location="cpu")); m = m.cuda().eval()
    for k, (s, y, th) in enumerate(starts):
        s0, y0, th0 = s, y, th
        vw = cv2.VideoWriter(f"lane/results/{PREFIX}_videos/{PREFIX}_{tag}_{st}_r{k}.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 8, (480, 270))
        for i in range(NSTEPS):
            img = render(pipe, tomodel, Ks, pose(s, y, th))
            with torch.no_grad():
                po, ph = m(to_tensor(img)[None].cuda()).float().cpu().numpy()[0] * NORM
            paths.append((st, k, i, round(s, 3), round(y, 4), round(th, 3), round(float(po), 4), round(float(ph), 3)))
            f_ = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            cv2.putText(f_, f"{st} run {k}  true {y:+.2f} m  pred {po:+.2f} m", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, .5, (255, 255, 255), 1)
            vw.write(f_)
            th += float(np.clip(-math.degrees(math.atan2(po - TARGET, LOOKAHEAD)) - ph, -CAP, CAP))
            s += STEP * math.cos(math.radians(th)); y += STEP * math.sin(math.radians(th))
        vw.release()
        runs.append((st, k, round(s0, 2), y0, th0, round(y, 4), int(abs(y - TARGET) < 0.3)))
    r = [x for x in runs if x[0] == st]
    print(f"== {tag} {st}: success {sum(x[6] for x in r)}/{len(r)}, mean final |offset - target| {np.mean([abs(x[5] - TARGET) for x in r]):.2f} m", flush=True)
with open(f"lane/results/{PREFIX}_{tag}_runs.csv", "w", newline="") as fh:
    csv.writer(fh).writerows([("set", "run", "start_along_m", "start_offset_m", "start_heading_deg", "final_offset_m", "success"), *runs])
with open(f"lane/results/{PREFIX}_{tag}_paths.csv", "w", newline="") as fh:
    csv.writer(fh).writerows([("set", "run", "step", "along_m", "true_offset_m", "heading_deg", "pred_offset_m", "pred_heading_deg"), *paths])
