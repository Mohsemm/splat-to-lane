"""world A init points from walk 0 cameras only (leak check)"""
import csv
import json
import os
import shutil

import numpy as np
from nerfstudio.data.utils.colmap_parsing_utils import read_images_binary, read_points3D_binary

walk = {r["frame"]: r["walk"] for r in csv.DictReader(open("proc3/frame_map.csv"))}
ims = read_images_binary("proc3/colmap/sparse/0/images.bin")
w0ids = {i for i, im in ims.items() if walk.get(im.name.rsplit(".", 1)[0]) in ("w0", "w0b")}
pts = read_points3D_binary("proc3/colmap/sparse/0/points3D.bin")
keep = [p for p in pts.values() if sum(1 for i in set(p.image_ids.tolist()) if i in w0ids) >= 2]
tj = json.load(open("split_walk0/transforms.json"))
A = np.array(tj["applied_transform"], float) if "applied_transform" in tj else np.eye(4)[:3]
xyz = np.array([p.xyz for p in keep]) @ A[:3, :3].T + A[:3, 3]
rgb = np.array([p.rgb for p in keep]).astype(np.uint8)
print(f"== strict points: {len(keep)} of {len(pts)} COLMAP points seen by >=2 walk-0 cameras ({len(w0ids)} walk-0 images)")
if os.path.exists("split_walk0_strict"):
    shutil.rmtree("split_walk0_strict")
shutil.copytree("split_walk0", "split_walk0_strict")
with open("split_walk0_strict/sparse_pc_strict.ply", "w") as fh:
    fh.write(f"ply\nformat ascii 1.0\nelement vertex {len(xyz)}\nproperty float x\nproperty float y\nproperty float z\n"
             "property uint8 red\nproperty uint8 green\nproperty uint8 blue\nend_header\n")
    for (x, y, z), (r, g, b) in zip(xyz, rgb):
        fh.write(f"{x:.6f} {y:.6f} {z:.6f} {r} {g} {b}\n")
tj["ply_file_path"] = "sparse_pc_strict.ply"
json.dump(tj, open("split_walk0_strict/transforms.json", "w"), indent=2)
# sanity check vs sparse_pc.ply
allxyz = np.array([p.xyz for p in pts.values()]) @ A[:3, :3].T + A[:3, 3]
print("== strict cloud bounds", np.round(xyz.min(0), 2), np.round(xyz.max(0), 2), "| full", np.round(allxyz.min(0), 2), np.round(allxyz.max(0), 2))
