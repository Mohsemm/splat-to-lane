#!/usr/bin/env bash
# splat quality on all non training frames
set -uo pipefail; cd /home/aymane/s3d
LOG=logs/allfr-$(date +%Y%m%d-%H%M).log; exec > >(tee -a "$LOG") 2>&1
IMG=ghcr.io/nerfstudio-project/nerfstudio:latest
ns() { echo "== CMD $(date '+%F %T'): $*"; docker run --gpus all --rm -u "$(id -u)" -e HOME=/workspace -e USER=aymane -e LOGNAME=aymane \
  -e TORCHDYNAMO_DISABLE=1 -v /home/aymane/s3d:/workspace -w /workspace --shm-size=12gb "$IMG" "$@"; }
temp() { echo "== GPU $(date '+%T') $1: $(nvidia-smi --query-gpu=temperature.gpu,power.draw,fan.speed,utilization.gpu,memory.used --format=csv,noheader)"; }
echo "== $(date) START allfr (waiting for tmux resume)"
# stop at 14:00
ABORT_AT=$(date -d 'today 14:00' +%s); [ "$(date +%s)" -ge "$ABORT_AT" ] && ABORT_AT=$(date -d 'tomorrow 14:00' +%s)
echo "== resume abort at $(date -d @$ABORT_AT '+%F %T')"
while tmux has-session -t =resume 2>/dev/null; do
  [ "$(date +%s)" -ge "$ABORT_AT" ] && [ ! -e lane/ABORT ] && { echo "== $(date '+%T') 14:00 PC reached: ABORT resume remaining steps"; touch lane/ABORT; }
  sleep 60; done
rm -f lane/ABORT; temp "before cooldown"; sleep 300
for e in walk0allfr:street_walk0 walk02allfr:street_walk02 walk0bigallfr:street_walk0_big walk02bigallfr:street_walk02_big; do
  [ "$(date +%H%M)" -ge 1540 ] && [ "$(date +%H%M)" -lt 1800 ] && { echo "== late, skip ${e%%:*}"; continue; }
  tag=${e%%:*}; x=${e#*:}; c=$(ls -t outputs/$x/*/*/config_allfr.yml | head -1); t0=$(date +%s); temp "start $tag"
  ns ns-eval --load-config "$c" --output-path eval/$tag.json --render-output-path eval/renders_$tag || echo "== FAILED $tag"
  echo "== DURATION $tag $(( $(date +%s) - t0 )) s"
done
ns python metrics_by_offset.py walk0allfr:walk0_allfr walk02allfr:walk02_allfr walk0bigallfr:walk0_allfr walk02bigallfr:walk02_allfr
temp end; echo "== $(date) ALL DONE allfr"
