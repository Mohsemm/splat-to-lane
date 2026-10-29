"""W set: pilotnet style 2d warps of the real walk 0 frames"""
import csv
import os
import sys

import cv2
import numpy as np

from lane_common import H, W, fit_geometry, intrinsics, load_frames, pose_at, real_image

CAM_H = float(os.environ.get("CAM_H", "1.4"))   # phone height, guessed
OUT = os.environ.get("OUT", "lane/warps_W")
F = np.diag([1.0, -1.0, -1.0])   # opengl -> opencv axes
HEAD_RANGE = (-10.0, 15.0)

tj, fr = load_frames(); g = fit_geometry(fr); K, dist, Ks = intrinsics(tj); Kinv = np.linalg.inv(Ks)
os.makedirs("lane/real", exist_ok=True); os.makedirs(OUT, exist_ok=True)
real = {}
for f in fr:
    p = f"lane/real/{f['key']}.jpg"
    if not os.path.exists(p):
        cv2.imwrite(p, cv2.cvtColor(real_image(tj, f, K, dist), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
    if f["walk"] in ("w0", "w0b"):
        real[f["key"]] = f
print(f"== real frames ready ({len(fr)})", flush=True)

n = int(sys.argv[1]); rng = np.random.default_rng(2); keys = sorted(real); rows = []
ys, xs = np.mgrid[0:H, 0:W]; pix = np.stack([xs.ravel(), ys.ravel(), np.ones(xs.size)])
for i in range(n):
    f = real[keys[rng.integers(len(keys))]]
    o, h = rng.uniform(0, 3), rng.uniform(*HEAD_RANGE)
    old, new = f["c2w"], pose_at(g, f["c2w"], o, h)
    Ro, Rn = old[:3, :3], new[:3, :3]
    Rrel = F @ Ro.T @ Rn @ F
    c = F @ Ro.T @ (new[:3, 3] - old[:3, 3]) * g["k"]
    nrm = F @ Ro.T @ (-g["up"])
    Hg = Ks @ Rrel.T @ (np.eye(3) - np.outer(c, nrm) / CAM_H) @ Kinv   # ground homography
    Hi = Ks @ Rrel.T @ Kinv                                  # sky homography
    rays_old = Rrel @ (Kinv @ pix)
    ground = ((nrm @ rays_old) > 1e-3).reshape(H, W)
    src = cv2.imread(f"lane/real/{f['key']}.jpg")
    wg = cv2.warpPerspective(src, Hg, (W, H), borderMode=cv2.BORDER_REPLICATE)
    wi = cv2.warpPerspective(src, Hi, (W, H), borderMode=cv2.BORDER_REPLICATE)
    out = np.where(ground[..., None], wg, wi)
    cv2.imwrite(f"{OUT}/{i:05d}.jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 92])
    rows.append((f"{i:05d}.jpg", round(o, 4), round(h, 3), f["key"]))
with open(f"{OUT}/labels.csv", "w", newline="") as fh:
    csv.writer(fh).writerows([("file", "offset_m", "heading_deg", "anchor"), *rows])
print(f"== warps done {n} (camera height {CAM_H} m) -> {OUT}")
