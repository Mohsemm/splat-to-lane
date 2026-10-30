"""check the y-up ply is actually y-up"""
import sys

import numpy as np


def xyz(path):
    with open(path, "rb") as f:
        hdr = []
        while True:
            line = f.readline().decode("ascii", "ignore").strip(); hdr.append(line)
            if line == "end_header":
                break
        off = f.tell()
    n = int(next(l for l in hdr if l.startswith("element vertex")).split()[-1])
    props = [l.split()[-1] for l in hdr if l.startswith("property")]
    assert all(l.split()[1] == "float" for l in hdr if l.startswith("property")), "non-float props"
    a = np.memmap(path, np.float32, "r", off, (n, len(props)))
    return a[:, [props.index(k) for k in ("x", "y", "z")]].astype(np.float64), a, props


for p in sys.argv[1:]:
    P, _, _ = xyz(p)
    c = P - np.median(P, 0); keep = np.all(np.abs(c) < np.percentile(np.abs(c), 95, 0), 1); c = c[keep]
    w, v = np.linalg.eigh(np.cov(c.T))
    up = v[:, 0]; ax = int(np.argmax(np.abs(up))); h = c[:, ax]
    sk = float(((h - h.mean()) ** 3).mean() / h.std() ** 3)  # road is low, trees go up
    print(f"   axis {'XYZ'[ax]}: skew {sk:+.2f} (positive = long tail toward +{'XYZ'[ax]} = that direction is up)")
    print(f"{p}: n={len(P)}, spread (5-95%) xyz={np.percentile(c, 95, 0) - np.percentile(c, 5, 0)}, thinnest axis={np.round(up, 3)} -> {'XYZ'[int(np.argmax(np.abs(up)))]}")
a, _, _ = xyz(sys.argv[1]); b, _, _ = xyz(sys.argv[2])
R = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])  # -90 about x
print("max |R a - b| =", float(np.abs(a[:200000] @ R.T - b[:200000]).max()))
