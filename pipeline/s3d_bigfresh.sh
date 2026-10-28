#!/usr/bin/env bash
# big splat, fresh run
set -uo pipefail
S3D=/home/aymane/s3d
LOG=$S3D/logs/bigfresh-$(date +%Y%m%d-%H%M).log
exec > >(tee -a "$LOG") 2>&1
echo "== $(date) START splatfacto-big fresh, all walks, 30k at 1080p"
docker run --gpus all --rm -u "$(id -u)" -e HOME=/workspace -e USER=aymane -e LOGNAME=aymane \
  -e TORCHDYNAMO_DISABLE=1 -v "$S3D":/workspace -w /workspace --shm-size=12gb \
  ghcr.io/nerfstudio-project/nerfstudio:latest \
  ns-train splatfacto-big --data split_all --output-dir outputs --experiment-name street_all_1080b \
  --max-num-iterations 30000 --viewer.quit-on-train-completion True \
  --pipeline.datamanager.cache-images cpu --pipeline.datamanager.camera-res-scale-factor 0.75 \
  nerfstudio-data --downscale-factor 1 --eval-mode filename
echo "== $(date) ALL DONE big fresh -> outputs/street_all_1080b/"
