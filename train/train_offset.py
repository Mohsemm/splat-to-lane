"""resnet18 -> (offset, heading)
usage: python train_offset.py <W|G|G2|R|RG2> [epochs]"""
import csv
import os
import sys
import time

import cv2
import numpy as np
import torch

from lane_common import NORM, net, to_tensor

SET = sys.argv[1]; EPOCHS = int(sys.argv[2]) if len(sys.argv) > 2 else 15
SEED = int(os.environ.get("SEED", "0"))                  # seed
NAME = os.environ.get("NAME", SET)
WARPS = os.environ.get("WARPS", "lane/warps_W")
RENDERS = os.environ.get("RENDERS")
torch.manual_seed(SEED); np.random.seed(SEED)
real = [r for r in csv.DictReader(open("lane/real_labels.csv"))]
items = []
def add_real(walks):
    items.extend((f"lane/real/{r['frame']}.jpg", float(r["offset_m"]), float(r["heading_deg"])) for r in real if r["walk"] in walks)
def add_dir(d):
    items.extend((f"{d}/{r['file']}", float(r["offset_m"]), float(r["heading_deg"])) for r in csv.DictReader(open(f"{d}/labels.csv")))
if SET == "W": add_dir(WARPS); add_real(("w0", "w0b"))
elif SET == "G": add_dir(RENDERS or "lane/renders_A"); add_real(("w0", "w0b"))
elif SET == "G2": add_dir(RENDERS or "lane/renders_B"); add_real(("w0", "w0b"))
elif SET == "R": add_real(("w0", "w0b", "w2"))
elif SET == "RG2": add_dir(RENDERS or "lane/renders_B"); add_real(("w0", "w0b", "w2"))
rng = np.random.default_rng(0); idx = rng.permutation(len(items)); nv = len(items) // 10
val, tr = [items[i] for i in idx[:nv]], [items[i] for i in idx[nv:]]
if SET == "R":   # only ~500 real frames so repeat them
    tr = tr * 10
elif SET == "RG2":  # repeat real 4x
    tr = tr + [t for t in tr if t[0].startswith("lane/real/")] * 3


class DS(torch.utils.data.Dataset):
    def __init__(self, it, aug): self.it, self.aug = it, aug
    def __len__(self): return len(self.it)
    def __getitem__(self, i):
        p, o, h = self.it[i]
        im = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB)
        if self.aug:   # no flips, they flip the offset
            a = np.random.uniform(0.8, 1.2); b = np.random.uniform(-20, 20)
            im = np.clip(im.astype(np.float32) * a + b, 0, 255).astype(np.uint8)
        return to_tensor(im), torch.tensor(np.array([o, h], np.float32) / NORM)


dev = "cuda"
dl = torch.utils.data.DataLoader(DS(tr, True), batch_size=64, shuffle=True, num_workers=6, drop_last=True,
                                 generator=torch.Generator().manual_seed(SEED), worker_init_fn=lambda w: np.random.seed(SEED * 100 + w))
dv = torch.utils.data.DataLoader(DS(val, False), batch_size=64, num_workers=6)
m = net().to(dev); opt = torch.optim.AdamW(m.parameters(), lr=3e-4, weight_decay=1e-4)
sched = torch.optim.lr_scheduler.OneCycleLR(opt, 3e-4, total_steps=EPOCHS * len(dl))
os.makedirs("lane/models", exist_ok=True); log = []
print(f"== {NAME} (seed {SEED}): train {len(tr)} val {len(val)} epochs {EPOCHS}", flush=True)
for ep in range(EPOCHS):
    t0 = time.time(); m.train(); tl = []
    for x, y in dl:
        x, y = x.to(dev, non_blocking=True), y.to(dev)
        with torch.autocast("cuda", dtype=torch.float16):
            loss = torch.nn.functional.l1_loss(m(x).float(), y)
        opt.zero_grad(); loss.backward(); opt.step(); sched.step(); tl.append(loss.item())
    m.eval(); err = []
    with torch.no_grad():
        for x, y in dv:
            err.append((m(x.to(dev)).float().cpu() - y).abs().numpy() * NORM)
    err = np.concatenate(err).mean(0)
    log.append((ep + 1, np.mean(tl), err[0] * 100, err[1]))
    print(f"   ep {ep+1:2d} train L1 {np.mean(tl):.4f} | val offset err {err[0]*100:.1f} cm heading err {err[1]:.2f} deg | {time.time()-t0:.0f}s", flush=True)
torch.save(m.state_dict(), f"lane/models/{NAME}.pt")
with open(f"lane/models/{NAME}_loss.csv", "w", newline="") as fh:
    csv.writer(fh).writerows([("epoch", "train_l1", "val_offset_cm", "val_heading_deg"), *log])
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
a = np.array(log); fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
ax[0].plot(a[:, 0], a[:, 1]); ax[0].set(title=f"{NAME}: train L1 (normalised)", xlabel="epoch")
ax[1].plot(a[:, 0], a[:, 2]); ax[1].set(title=f"{NAME}: val offset error (cm)", xlabel="epoch")
fig.tight_layout(); fig.savefig(f"lane/models/{NAME}_loss.png", dpi=110)
print(f"== {NAME} done")
