"""shared stuff: geometry, image loading, model"""
import csv
import json
import math

import cv2
import numpy as np

W, H = 480, 270                 # net input size
TJ = "proc3/transforms.json"
NOMINAL = {"w1": 1.0, "w2": 2.0, "w3": 3.0}


def load_frames():
    tj = json.load(open(TJ))
    walk = {r["frame"]: r["walk"] for r in csv.DictReader(open("proc3/frame_map.csv"))}
    orig = {r["frame"]: r["original"] for r in csv.DictReader(open("proc3/frame_map.csv"))}
    fr = []
    for f in tj["frames"]:
        key = f["file_path"].split("/")[-1].rsplit(".", 1)[0]
        fr.append(dict(key=key, walk=walk[key], orig=orig[key], c2w=np.array(f["transform_matrix"], float)))
    return tj, fr


def fit_geometry(fr):
    w0 = [f for f in fr if f["walk"] in ("w0", "w0b")]
    P = np.array([f["c2w"][:3, 3] for f in w0])
    c = P.mean(0)
    up = np.mean([f["c2w"][:3, 1] for f in w0], 0); up /= np.linalg.norm(up)
    _, _, vt = np.linalg.svd(P - c)
    d = vt[0] - (vt[0] @ up) * up; d /= np.linalg.norm(d)
    fwd = -np.mean([f["c2w"][:3, 2] for f in w0], 0)
    if d @ fwd < 0:
        d = -d
    l = np.cross(d, up); l /= np.linalg.norm(l)
    lat = {wk: np.mean([(f["c2w"][:3, 3] - c) @ l for f in fr if f["walk"] == wk]) for wk in NOMINAL}
    if lat["w3"] < 0:                       # road side = positive
        l = -l; lat = {k: -v for k, v in lat.items()}
    nom = np.array([NOMINAL[k] for k in NOMINAL]); meas = np.array([lat[k] for k in NOMINAL])
    k = float(nom @ meas / (meas @ meas))
    implied = {wk: lat[wk] * k for wk in NOMINAL}
    if max(abs(implied[w] - NOMINAL[w]) / NOMINAL[w] for w in NOMINAL) > 0.2:
        k = NOMINAL["w3"] / lat["w3"]; implied = {wk: lat[wk] * k for wk in NOMINAL}; flag = "INCONSISTENT -> w3-only scale"
    else:
        flag = "ok"
    return dict(c=c, d=d, up=up, l=l, k=k, implied=implied, flag=flag)


def label(g, c2w):
    off = float((c2w[:3, 3] - g["c"]) @ g["l"] * g["k"])
    f = -c2w[:3, 2]
    head = math.degrees(math.atan2(f @ g["l"], f @ g["d"]))
    return off, head


def along(g, c2w):
    return float((c2w[:3, 3] - g["c"]) @ g["d"] * g["k"])


def rot_about(axis, deg):
    return cv2.Rodrigues(np.asarray(axis, float) * math.radians(deg))[0]


def pose_at(g, anchor_c2w, offset_m, heading_deg):
    """Anchor pose moved sideways to absolute offset and yawed to absolute heading (keeps anchor pitch/roll)."""
    o0, h0 = label(g, anchor_c2w)
    out = anchor_c2w.copy()
    # yaw, positive = toward the road
    out[:3, :3] = rot_about(g["up"], -(heading_deg - h0)) @ anchor_c2w[:3, :3]
    out[:3, 3] = anchor_c2w[:3, 3] + (offset_m - o0) / g["k"] * g["l"]
    return out


def intrinsics(tj):
    s = W / tj["w"]
    K = np.array([[tj["fl_x"], 0, tj["cx"]], [0, tj["fl_y"], tj["cy"]], [0, 0, 1]])
    dist = np.array([tj.get(x, 0.0) for x in ("k1", "k2", "p1", "p2")])
    Ks = K.copy(); Ks[:2] *= s
    return K, dist, Ks


def real_image(tj, f, K, dist):
    """Real frame, undistorted to pinhole (same model as the renders), resized to W x H, RGB uint8."""
    im = cv2.imread(f"frames3/{f['orig']}")
    im = cv2.undistort(im, K, dist, None, K)
    return cv2.cvtColor(cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)


def net():
    import torch
    import torchvision
    m = torchvision.models.resnet18(weights=torchvision.models.ResNet18_Weights.IMAGENET1K_V1)
    m.fc = torch.nn.Linear(m.fc.in_features, 2)
    return m


MEAN = np.array([0.485, 0.456, 0.406], np.float32); STD = np.array([0.229, 0.224, 0.225], np.float32)
NORM = np.array([3.0, 10.0], np.float32)       # scale to ~[-1, 1]


def to_tensor(rgb_u8):
    import torch
    x = (rgb_u8.astype(np.float32) / 255 - MEAN) / STD
    return torch.from_numpy(x.transpose(2, 0, 1).copy())
