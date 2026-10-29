#!/usr/bin/env bash
# closed loop stats + demo splat export
set -uo pipefail
cd /home/aymane/s3d
LOG=logs/extra-$(date +%Y%m%d-%H%M).log
exec > >(tee -a "$LOG") 2>&1
IMG=ghcr.io/nerfstudio-project/nerfstudio:latest
ns() { echo "== CMD $(date '+%F %T'): $*"; docker run --gpus all --rm -u "$(id -u)" -e HOME=/workspace -e USER=aymane -e LOGNAME=aymane \
  -e TORCHDYNAMO_DISABLE=1 -v /home/aymane/s3d:/workspace -w /workspace --shm-size=12gb "$IMG" "$@"; }
temp() { echo "== GPU $(date '+%T') $1: $(nvidia-smi --query-gpu=temperature.gpu,power.draw,fan.speed,utilization.gpu,memory.used --format=csv,noheader)"; }
cool() { temp "before cooldown"; sleep 300; temp "after cooldown"; }
rm -f lane/ABORT
( while true; do t=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | head -1); t=${t%%.*}
    if [ "${t:-0}" -gt 90 ]; then echo "== ABORT $(date '+%T') GPU core ${t} C > 90" | tee -a "$LOG"; touch lane/ABORT; docker ps -q | xargs -r docker kill; fi
    sleep 20; done ) & GUARD=$!
trap 'kill $GUARD 2>/dev/null' EXIT
step() { [ -e lane/ABORT ] && { echo "== skipped (ABORT): $*"; return 1; }; temp "start $1"; shift; ns "$@" || echo "== FAILED: $*"; }
A=outputs/street_walk0/splatfacto/2026-10-28_204550/config.yml
B=outputs/street_walk02/splatfacto/2026-10-28_212103/config.yml
C=$(ls -t outputs/street_all_1080b/splatfacto/*/config.yml | head -1)
echo "== $(date) START extra"
step cl_A python closed_loop_stats.py A "$A" W G G2; cool
step cl_B python closed_loop_stats.py B "$B" W G G2; cool
step cl_plot python cl_plot.py
step export ns-export gaussian-splat --load-config "$C" --output-dir exports/street_all_1080b
ls -la exports/street_all_1080b 2>&1
temp "end"
echo "== $(date) ALL DONE extra"
