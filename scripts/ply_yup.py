"""rotate the splat ply to y-up for supersplat"""
import sys

import numpy as np

src, dst = sys.argv[1], sys.argv[2]
with open(src, "rb") as fh:
    header = b""
    while not header.endswith(b"end_header\n"):
        header += fh.readline()
    props, n = [], 0
    for line in header.decode().splitlines():
        p = line.split()
        if p[:2] == ["element", "vertex"]:
            n = int(p[2])
        elif p[0] == "property":
            assert p[1] == "float", f"unexpected type {p[1]}"
            props.append(p[2])
    data = np.fromfile(fh, dtype=np.dtype([(q, "<f4") for q in props]), count=n)
R = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], np.float32)          # -90 about x
for a, b, c in (("x", "y", "z"), ("nx", "ny", "nz")):
    if a in props:
        v = np.stack([data[a], data[b], data[c]], 1) @ R.T
        data[a], data[b], data[c] = v[:, 0], v[:, 1], v[:, 2]
if "rot_0" in props:
    w2, x2, y2, z2 = np.float32(np.cos(np.radians(-45))), np.float32(np.sin(np.radians(-45))), np.float32(0), np.float32(0)
    w1, x1, y1, z1 = (data[f"rot_{i}"].copy() for i in range(4))
    data["rot_0"] = w2 * w1 - x2 * x1 - y2 * y1 - z2 * z1
    data["rot_1"] = w2 * x1 + x2 * w1 + y2 * z1 - z2 * y1
    data["rot_2"] = w2 * y1 - x2 * z1 + y2 * w1 + z2 * x1
    data["rot_3"] = w2 * z1 + x2 * y1 - y2 * x1 + z2 * w1
with open(dst, "wb") as fh:
    fh.write(header); data.tofile(fh)
print(f"== wrote {dst}: {n} gaussians, props {len(props)}, normals {'nx' in props}, rotated quats {'rot_0' in props}")
