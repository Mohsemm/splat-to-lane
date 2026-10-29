"""psnr / ssim / lpips per walk from ns-eval renders"""
import csv
import json
import sys
from collections import defaultdict

import numpy as np
import torch
from PIL import Image
from torchmetrics.image import PeakSignalNoiseRatio, StructuralSimilarityIndexMeasure
from torchmetrics.image.lpip import LearnedPerceptualImagePatchSimilarity

OFFSET_M = {"w0": 0, "w0b": 0, "w1": 1, "w2": 2, "w3": 3, "sweep": None}  # metres from walk 0
dev = "cuda" if torch.cuda.is_available() else "cpu"
psnr = PeakSignalNoiseRatio(data_range=1.0).to(dev)
ssim = StructuralSimilarityIndexMeasure(data_range=1.0).to(dev)
lpips = LearnedPerceptualImagePatchSimilarity(net_type="alex", normalize=True).to(dev)

walk_of = {r["frame"]: r["walk"] for r in csv.DictReader(open("proc3/frame_map.csv"))}

for arg in sys.argv[1:]:
    tag, split = (arg.split(":") + [arg])[:2]
    test = sorted(json.load(open(f"split_{split}/transforms.json"))["test_filenames"])
    rows, acc = [], defaultdict(list)
    for i, name in enumerate(test):
        img = np.asarray(Image.open(f"eval/renders_{tag}/eval_img_{i:04d}.png").convert("RGB"), dtype=np.float32) / 255
        w = img.shape[1] // 2
        gt, rgb = (torch.from_numpy(x).permute(2, 0, 1)[None].to(dev) for x in (img[:, :w], img[:, w:]))
        with torch.no_grad():
            m = (psnr(rgb, gt).item(), ssim(rgb, gt).item(), lpips(rgb.clamp(0, 1), gt).item())
        walk = walk_of[name.split("/")[-1].rsplit(".", 1)[0]]
        rows.append((name, walk, *m))
        acc[walk].append(m)
    with open(f"eval/by_offset_{tag}.csv", "w", newline="") as fh:
        csv.writer(fh).writerows([("frame", "walk", "psnr", "ssim", "lpips"), *rows])
    print(f"== {tag}: walk, offset_m, n, psnr, ssim, lpips")
    for walk in sorted(acc, key=lambda k: (OFFSET_M[k] is None, OFFSET_M[k] or 0, k)):
        a = np.array(acc[walk])
        print(f"   {walk:5s} {str(OFFSET_M[walk]):>4s} {len(a):4d}  {a[:, 0].mean():6.2f}  {a[:, 1].mean():.3f}  {a[:, 2].mean():.3f}")
