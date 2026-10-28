#!/usr/bin/env bash
# frames -> colmap poses -> split -> splats A, B, C
# run in tmux: bash s3d_poses.sh
set -uo pipefail

S3D=/home/aymane/s3d
UID_=${SUDO_UID:-$(id -u)}
LOG=$S3D/logs/poses-$(date +%Y%m%d-%H%M).log
mkdir -p "$S3D/logs" "$S3D/frames3"
chown -R "$UID_:$UID_" "$S3D"   # fix root owned dirs
exec > >(tee -a "$LOG") 2>&1

ns() {  # run in the nerfstudio container
  echo "== CMD $(date '+%F %T'): docker run ... nerfstudio:latest $*"
  docker run --gpus all --rm -u "$UID_" -e HOME=/workspace -e USER=aymane -e LOGNAME=aymane \
    -e TORCHDYNAMO_DISABLE=1 -v "$S3D":/workspace -w /workspace --shm-size=12gb \
    ghcr.io/nerfstudio-project/nerfstudio:latest "$@"
}

RELAX0="--Mapper.init_min_tri_angle 2 --Mapper.init_min_num_inliers 50 --Mapper.abs_pose_min_num_inliers 15"
RELAX="$RELAX0 --Mapper.ba_global_function_tolerance=1e-6"
# colmap wrapper, relaxed init for the mapper only
printf '#!/bin/bash\nif [ "$1" = mapper ]; then exec colmap "$@" %s; else exec colmap "$@"; fi\n' "$RELAX0" > "$S3D/colmap_relaxed.sh"
chown "$UID_:$UID_" "$S3D/colmap_relaxed.sh"

posed() {  # count posed images
  python3 -c "import json,sys;print(len(json.load(open(sys.argv[1]))['frames']))" "$1" 2>/dev/null || echo 0
}

echo "== $(date) START (log $LOG)"
docker info >/dev/null 2>&1 || { systemctl start docker 2>/dev/null || service docker start; sleep 5; }
echo "== CPUs $(nproc), RAM $(free -g | awk '/Mem/{print $2}') GB, disk free $(df -h "$S3D" | awk 'NR==2{print $4}')"

# stage 1: test the relaxed mapper on the short clip
if [ -e "$S3D/street_clip/colmap/database.db" ]; then
  echo "== Stage 1: relaxed mapper test on street_clip ($(date))"
  rm -rf "$S3D/street_clip/colmap/sparse"; mkdir -p "$S3D/street_clip/colmap/sparse"; chown -R "$UID_:$UID_" "$S3D/street_clip"
  ns colmap mapper --database_path street_clip/colmap/database.db --image_path street_clip/images \
     --output_path street_clip/colmap/sparse $RELAX 2>&1 | grep -E "Registering image|Elapsed|No good|failed" | tail -5
  ns colmap model_analyzer --path street_clip/colmap/sparse/0 2>&1 | grep -E "Registered images|Points|Mean reprojection"
  echo "== Stage 1 done ($(date)); 61 images in the clip"
fi

FPS=3
echo "== frames at $FPS fps ($(date))"
mkdir -p "$S3D/frames3"
for f in "$S3D"/raw/w*.mov "$S3D"/raw/sweep.mov; do
  [ -e "$f" ] || continue
  b=$(basename "$f" .mov)
  ns ffmpeg -loglevel error -i "raw/$b.mov" -vf "fps=$FPS,scale=2560:-2" "frames3/${b}_%04d.jpg"
  echo "   $b: $(ls "$S3D"/frames3/${b}_*.jpg | wc -l) frames"
done
N=$(ls "$S3D/frames3" | wc -l); echo "== total frames: $N"

echo "== camera positions, all walks in one map ($(date))"
ns ns-process-data images --data frames3 --output-dir proc3 --matching-method vocab_tree \
   --colmap-cmd "bash /workspace/colmap_relaxed.sh"
if [ ! -e "$S3D/proc3/colmap/database.db" ]; then   # no --colmap-cmd, plain run
  echo "== --colmap-cmd rejected, plain run"
  ns ns-process-data images --data frames3 --output-dir proc3 --matching-method vocab_tree
fi
P=$(posed "$S3D/proc3/transforms.json")
if [ -e "$S3D/proc3/colmap/database.db" ] && [ $((N ? P * 100 / N : 0)) -lt 50 ]; then
  echo "== default mapper posed $P / $N -> relaxed mapper on the same matches ($(date))"
  rm -rf "$S3D/proc3/colmap/sparse"; mkdir -p "$S3D/proc3/colmap/sparse"; chown -R "$UID_:$UID_" "$S3D/proc3"
  ns colmap mapper --database_path proc3/colmap/database.db --image_path proc3/images --output_path proc3/colmap/sparse $RELAX
  ns ns-process-data images --data frames3 --output-dir proc3 --skip-colmap --colmap-model-path colmap/sparse/0
  P=$(posed "$S3D/proc3/transforms.json")
fi
echo "== $(date) POSES DONE: posed $P / $N ($((N ? P * 100 / N : 0))%; 80%+ = good). Keep proc3/; never re-run for a training change."
[ "$P" -gt 0 ] || { echo "== no poses, stopping"; exit 1; }

# split by walk (frames are renamed in sorted order)
python3 - "$S3D" <<'PY'
import json, os, sys
root = sys.argv[1]
orig = sorted(os.listdir(f"{root}/frames3"))
walk = {f"frame_{i+1:05d}": o.rsplit("_", 1)[0] for i, o in enumerate(orig)}
with open(f"{root}/proc3/frame_map.csv", "w") as fh:
    fh.write("frame,original,walk\n")
    for i, o in enumerate(orig):
        fh.write(f"frame_{i+1:05d},{o},{o.rsplit('_', 1)[0]}\n")
tj = json.load(open(f"{root}/proc3/transforms.json"))
names = [fr["file_path"] for fr in tj["frames"]]
def w(n): return walk.get(os.path.splitext(os.path.basename(n))[0], "?")
def split(train_walks):
    tr, te, k = [], [], {}
    for n in sorted(names):
        x = w(n); k[x] = k.get(x, 0) + 1
        if x in ("w0", "w0b"):
            (te if k[x] % 8 == 0 else tr).append(n)
        elif x in train_walks:
            tr.append(n)
        elif x in ("w1", "w2", "w3") and k[x] % 2 == 0:
            te.append(n)
    return tr, te
for tag, extra in (("walk0", ()), ("walk02", ("w2",)), ("all", ("w1", "w2", "w3", "sweep"))):
    tr, te = split(extra)
    if tag == "all":
        tr, te = sorted(names), sorted(names)[::8]
    d = dict(tj, train_filenames=tr, val_filenames=te, test_filenames=te)
    json.dump(d, open(f"{root}/proc3/transforms_{tag}.json", "w"), indent=2)
    print(f"== split {tag}: train {len(tr)}, test {len(te)}; walks seen: {sorted(set(map(w, names)))}")
PY

train() {  # $1 split, $2 method
  echo "== $2 on $1, 30k at 1440p ($(date))"
  rm -rf "$S3D/split_$1" && cp -r "$S3D/proc3" "$S3D/split_$1"   # nerfstudio wants transforms.json
  chown -R "$UID_:$UID_" "$S3D/split_$1" "$S3D/proc3"
  cp "$S3D/proc3/transforms_$1.json" "$S3D/split_$1/transforms.json"
  ns ns-train "$2" --data "split_$1" --output-dir outputs --experiment-name "street_$1" \
     --max-num-iterations 30000 --viewer.quit-on-train-completion True \
     --pipeline.datamanager.cache-images cpu nerfstudio-data --downscale-factor 1 --eval-mode filename
  echo "== $(date) $2 on $1 DONE -> outputs/street_$1/"
}

train walk0 splatfacto       # A: walk 0 only
train walk02 splatfacto      # B: walks 0 + 2
train all splatfacto-big     # C: all walks, for the demo
echo "== $(date) ALL DONE"
