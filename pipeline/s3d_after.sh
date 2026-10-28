#!/usr/bin/env bash
# big splat at 1080p + ns-eval for A and B
set -uo pipefail

S3D=/home/aymane/s3d
UID_=${SUDO_UID:-$(id -u)}
LOG=$S3D/logs/after-$(date +%Y%m%d-%H%M).log
mkdir -p "$S3D/logs" "$S3D/eval"
chown -R "$UID_:$UID_" "$S3D/eval" "$S3D/outputs" 2>/dev/null
exec > >(tee -a "$LOG") 2>&1

ns() {  # same as s3d_poses.sh
  echo "== CMD $(date '+%F %T'): docker run ... nerfstudio:latest $*"
  docker run --gpus all --rm -u "$UID_" -e HOME=/workspace -e USER=aymane -e LOGNAME=aymane \
    -e TORCHDYNAMO_DISABLE=1 -v "$S3D":/workspace -w /workspace --shm-size=12gb \
    ghcr.io/nerfstudio-project/nerfstudio:latest "$@"
}

echo "== $(date) START (log $LOG)"
docker info >/dev/null 2>&1 || { systemctl start docker 2>/dev/null || service docker start; sleep 5; }

RESUME=()
ck=$(ls -t "$S3D"/outputs/street_all_1080/splatfacto/*/nerfstudio_models/*.ckpt 2>/dev/null | head -1)
[ -n "$ck" ] && RESUME=(--load-dir "$(dirname "${ck#$S3D/}")") && echo "== resuming from ${ck#$S3D/}"
echo "== splatfacto-big on all walks, 30k at 1080p ($(date))"
ns ns-train splatfacto-big "${RESUME[@]}" --data split_all --output-dir outputs --experiment-name street_all_1080 \
   --max-num-iterations 30000 --viewer.quit-on-train-completion True \
   --pipeline.datamanager.cache-images cpu --pipeline.datamanager.camera-res-scale-factor 0.75 \
   nerfstudio-data --downscale-factor 1 --eval-mode filename
echo "== $(date) big DONE -> outputs/street_all_1080/"

for tag in walk0 walk02; do
  cfg=$(ls -t "$S3D"/outputs/street_$tag/splatfacto/*/config.yml | head -1)
  rel=${cfg#$S3D/}
  echo "== eval $tag: $rel ($(date))"
  ns ns-eval --load-config "$rel" --output-path "eval/$tag.json" --render-output-path "eval/renders_$tag"
  echo "== $tag metrics:"; cat "$S3D/eval/$tag.json"
done
echo "== $(date) ALL DONE"
