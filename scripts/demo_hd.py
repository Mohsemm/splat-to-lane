"""hd demo video, G vs W side by side in the big world"""
import csv
import glob
import math

import cv2
import numpy as np
import torch
from nerfstudio.cameras.cameras import Cameras, CameraType

from lane_common import along, fit_geometry, intrinsics, load_frames, pose_at
from render_offsets import world_loader

TARGET, SUB, OW, OH = 1.5, 6, 1920, 1080
tj, fr = load_frames(); g = fit_geometry(fr); _, _, Ks480 = intrinsics(tj)
Kh = Ks480.copy(); Kh[:2] *= OW / 480
track = sorted([f for f in fr if f["walk"] == "w0b"], key=lambda f: along(g, f["c2w"]))
S = np.array([along(g, f["c2w"]) for f in track])


def pose(s, y, th):
    a = track[int(np.argmin(np.abs(S - s)))]
    p = pose_at(g, a["c2w"], y, th)
    p[:3, 3] += (s - along(g, a["c2w"])) / g["k"] * g["d"]
    return p


def rend(pipe, tomodel, c2w, K, w, h):
    m = tomodel(c2w)
    cam = Cameras(camera_to_worlds=torch.tensor(m[None, :3, :], dtype=torch.float32), fx=float(K[0, 0]), fy=float(K[1, 1]),
                  cx=float(K[0, 2]), cy=float(K[1, 2]), width=w, height=h, camera_type=CameraType.PERSPECTIVE).to(pipe.device)
    with torch.no_grad():
        return (pipe.model.get_outputs_for_camera(cam)["rgb"].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)


# check on a real camera
probe = next(f for f in fr if f["walk"] == "w0b")["c2w"]
pa, ta = world_loader("outputs/street_walk0/splatfacto/2026-10-28_204550/config.yml")
ra = rend(pa, ta, probe, Ks480, 480, 270)
del pa; torch.cuda.empty_cache()
pc, tc = world_loader(sorted(glob.glob("outputs/street_all_1080b/splatfacto/*/config.yml"))[-1])
rc = rend(pc, tc, probe, Ks480, 480, 270)
diff = float(np.abs(ra.astype(float) - rc.astype(float)).mean())
print(f"== cross-world check: mean abs pixel diff A vs big = {diff:.1f} / 255 (same view if small; ~60+ means misaligned)", flush=True)
cv2.imwrite("lane/results/demo_check_A_vs_big.jpg", cv2.cvtColor(np.hstack([ra, rc]), cv2.COLOR_RGB2BGR))
assert diff < 40, "worlds misaligned"

# pick runs
R = list(csv.DictReader(open("lane/results/cl_road_A_runs.csv")))
P = list(csv.DictReader(open("lane/results/cl_road_A_paths.csv")))
best = min((r for r in R if r["set"] in ("G", "G2")), key=lambda r: abs(float(r["final_offset_m"]) - TARGET))
wrun = next(r for r in R if r["set"] == "W" and r["run"] == best["run"])
def path(r): return [(float(x["along_m"]), float(x["true_offset_m"]), float(x["heading_deg"])) for x in P if x["set"] == r["set"] and x["run"] == r["run"]]
pg, pw = path(best), path(wrun)
print(f"== replaying {best['set']} run {best['run']} (final {float(best['final_offset_m']):+.2f} m) vs W run {wrun['run']} (final {float(wrun['final_offset_m']):+.2f} m)", flush=True)


def frames(p):
    for i in range(len(p) - 1):
        for j in range(SUB):
            t = j / SUB
            yield tuple(a + (b - a) * t for a, b in zip(p[i], p[i + 1]))
    yield p[-1]


vw = cv2.VideoWriter("lane/results/demo_hd.mp4", cv2.VideoWriter_fourcc(*"mp4v"), 30, (2 * OW, OH))
n = 0
for (sg, yg, hg), (sw, yw, hw) in zip(frames(pg), frames(pw)):
    pan = []
    for nm, s, y, th in ((best["set"], sg, yg, hg), ("W", sw, yw, hw)):
        im = cv2.cvtColor(rend(pc, tc, pose(s, y, th), Kh, OW, OH), cv2.COLOR_RGB2BGR)
        col = (80, 220, 80) if abs(y - TARGET) < 0.3 else (60, 60, 255)
        cv2.rectangle(im, (0, 0), (OW, 110), (0, 0, 0), -1)
        name = {"G": "G: trained on 3D renders", "G2": "G2: trained on 3D renders (2-walk world)", "W": "W: trained on 2D warps"}[nm]
        cv2.putText(im, name, (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
        cv2.putText(im, f"offset {y:+.2f} m   lane target {TARGET:.1f} m   heading {th:+.1f} deg", (30, 95), cv2.FONT_HERSHEY_SIMPLEX, 1.1, col, 3)
        pan.append(im)
    vw.write(np.hstack(pan)); n += 1
vw.release()
print(f"== demo_hd.mp4 written: {n} frames ({n/30:.1f} s), {2*OW}x{OH}")
