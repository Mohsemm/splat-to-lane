#!/usr/bin/env bash
# hd demo + y-up ply
set -uo pipefail
cd /home/aymane/s3d
LOG=logs/final-$(date +%Y%m%d-%H%M).log
exec > >(tee -a "$LOG") 2>&1
IMG=ghcr.io/nerfstudio-project/nerfstudio:latest
ns() { echo "== CMD $(date '+%F %T'): $*"; docker run --gpus all --rm -u "$(id -u)" -e HOME=/workspace -e USER=aymane -e LOGNAME=aymane \
  -e TORCHDYNAMO_DISABLE=1 -v /home/aymane/s3d:/workspace -w /workspace --shm-size=12gb "$IMG" "$@"; }
temp() { echo "== GPU $(date '+%T') $1: $(nvidia-smi --query-gpu=temperature.gpu,power.draw,fan.speed,utilization.gpu,memory.used --format=csv,noheader)"; }
cool() { temp "before cooldown"; sleep 300; temp "after cooldown"; }
late() { [ "$(date +%H%M)" -ge 1445 ] && [ "$(date +%H%M)" -lt 1600 ]; }
rm -f lane/ABORT
( while true; do t=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | head -1); t=${t%%.*}
    if [ "${t:-0}" -gt 90 ]; then echo "== ABORT $(date '+%T') GPU core ${t} C > 90" | tee -a "$LOG"; touch lane/ABORT; docker ps -q | xargs -r docker kill; fi
    sleep 20; done ) & GUARD=$!
trap 'kill $GUARD 2>/dev/null' EXIT
step() { { [ -e lane/ABORT ] || late; } && { echo "== skipped (ABORT/late): $*"; return 1; }; temp "start $1"; shift; t0=$(date +%s); ns "$@" || echo "== FAILED: $*"; echo "== DURATION $(( $(date +%s) - t0 )) s"; }
echo "== $(date) START final (waiting for tmux road)"
while tmux has-session -t =road 2>/dev/null; do sleep 60; done
cool
step demo_hd python demo_hd.py; cool
step ply_yup python ply_yup.py exports/street_all_1080b/splat.ply exports/street_all_1080b/splat_yup.ply
ls -la exports/street_all_1080b lane/results/demo_hd.mp4
temp "end"
echo "== $(date) ALL DONE final"
