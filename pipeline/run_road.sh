#!/usr/bin/env bash
# closed loop with the target in the road (1.5 m)
set -uo pipefail
cd /home/aymane/s3d
LOG=logs/road-$(date +%Y%m%d-%H%M).log
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
step() { { [ -e lane/ABORT ] || late; } && { echo "== skipped (ABORT/late): $*"; return 1; }; temp "start $1"; shift; ns "$@" || echo "== FAILED: $*"; }
A=outputs/street_walk0/splatfacto/2026-10-28_204550/config.yml
B=outputs/street_walk02/splatfacto/2026-10-28_212103/config.yml
E_="TARGET=1.5 PREFIX=cl_road STARTS=0.3:5,2.8:-5"
echo "== $(date) START road (waiting for tmux robust)"
while tmux has-session -t =robust 2>/dev/null; do sleep 60; done
cool
step road_A env $E_ python closed_loop_stats.py A "$A" W G G2; cool
step road_B env $E_ python closed_loop_stats.py B "$B" W G G2; cool
step road_plot env TARGET=1.5 PREFIX=cl_road python cl_plot.py
temp "end"
echo "== $(date) ALL DONE road"
