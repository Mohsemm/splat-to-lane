"""render N labelled views off the walk 0 path
usage: python render_offsets.py <tag> <config.yml> <N>"""
import csv
import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from nerfstudio.cameras.cameras import Cameras, CameraType
from nerfstudio.utils.eval_utils import eval_setup

from lane_common import H, W, fit_geometry, intrinsics, load_frames, pose_at

HEAD_RANGE = (-10.0, 15.0)   # real headings are ~0-15 deg


def world_loader(cfg):
    """Load a splat world and the map transforms.json pose -> model pose.
    dataparser_transforms.json alone is off by an axis swap (applied_transform), so fit the map from the
    dataset's own cameras: model = A @ (T @ c2w, translation * s), A checked on every train camera."""
    _, pipe, _, _ = eval_setup(Path(cfg), test_mode="inference")
    dt = json.load(open(Path(cfg).parent / "dataparser_transforms.json"))
    T = np.vstack([np.array(dt["transform"]), [0, 0, 0, 1]]); s = dt["scale"]
    ds = pipe.datamanager.train_dataset
    tj = json.load(open("proc3/transforms.json"))
    byk = {f["file_path"].split("/")[-1].rsplit(".", 1)[0]: np.array(f["transform_matrix"], float) for f in tj["frames"]}
    def base(c2w):
        m = T @ c2w; m[:3, 3] *= s; return m
    As = []
    for i, p in enumerate(ds.image_filenames):
        c = np.vstack([ds.cameras.camera_to_worlds[i].numpy(), [0, 0, 0, 1]])
        As.append(c @ np.linalg.inv(base(byk[Path(p).stem])))
    As = np.array(As); A = np.median(As, 0)
    u, _, vt = np.linalg.svd(A[:3, :3]); A[:3, :3] = u @ vt
    err = np.abs(As - A).max()
    print(f"== pose map fitted on {len(As)} cams, max deviation {err:.4f}", flush=True)
    assert err < 0.05, "pose map inconsistent"
    return pipe, (lambda c2w: A @ base(c2w))


def render(pipe, tomodel, Ks, c2w):
    m = tomodel(c2w)
    cam = Cameras(camera_to_worlds=torch.tensor(m[None, :3, :], dtype=torch.float32),
                  fx=float(Ks[0, 0]), fy=float(Ks[1, 1]), cx=float(Ks[0, 2]), cy=float(Ks[1, 2]),
                  width=W, height=H, camera_type=CameraType.PERSPECTIVE).to(pipe.device)
    with torch.no_grad():
        rgb = pipe.model.get_outputs_for_camera(cam)["rgb"]
    return (rgb.clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)


if __name__ == "__main__":
    tag, cfg, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
    tj, fr = load_frames(); g = fit_geometry(fr); _, _, Ks = intrinsics(tj)
    anchors = [f for f in fr if f["walk"] in ("w0", "w0b")]
    pipe, tomodel = world_loader(cfg)
    out = f"lane/renders_{tag}"; os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(0 if tag == "A" else 1)
    rows = []
    for i in range(n):
        a = anchors[rng.integers(len(anchors))]
        o, h = rng.uniform(0, 3), rng.uniform(*HEAD_RANGE)
        img = render(pipe, tomodel, Ks, pose_at(g, a["c2w"], o, h))
        cv2.imwrite(f"{out}/{i:05d}.jpg", cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
        rows.append((f"{i:05d}.jpg", round(o, 4), round(h, 3), a["key"]))
        if i % 500 == 0:
            print(f"== {tag} {i}/{n}", flush=True)
    with open(f"{out}/labels.csv", "w", newline="") as fh:
        csv.writer(fh).writerows([("file", "offset_m", "heading_deg", "anchor"), *rows])
    print(f"== {tag} done {n}")
