#!/usr/bin/env bash
# extra seeds + W warp height check
set -uo pipefail
cd /home/aymane/s3d
LOG=logs/robust-$(date +%Y%m%d-%H%M).log
exec > >(tee -a "$LOG") 2>&1
IMG=ghcr.io/nerfstudio-project/nerfstudio:latest
ns() { echo "== CMD $(date '+%F %T'): $*"; docker run --gpus all --rm -u "$(id -u)" -e HOME=/workspace -e USER=aymane -e LOGNAME=aymane \
  -e TORCHDYNAMO_DISABLE=1 -v /home/aymane/s3d:/workspace -w /workspace --shm-size=12gb "$IMG" "$@"; }
temp() { echo "== GPU $(date '+%T') $1: $(nvidia-smi --query-gpu=temperature.gpu,power.draw,fan.speed,utilization.gpu,memory.used --format=csv,noheader)"; }
cool() { temp "before cooldown"; sleep 300; temp "after cooldown"; }
late() { [ "$(date +%H%M)" -ge 1445 ] && [ "$(date +%H%M)" -lt 1600 ]; }   # pc clock is +4
rm -f lane/ABORT
( while true; do t=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | head -1); t=${t%%.*}
    if [ "${t:-0}" -gt 90 ]; then echo "== ABORT $(date '+%T') GPU core ${t} C > 90" | tee -a "$LOG"; touch lane/ABORT; docker ps -q | xargs -r docker kill; fi
    sleep 20; done ) & GUARD=$!
trap 'kill $GUARD 2>/dev/null' EXIT
step() { { [ -e lane/ABORT ] || late; } && { echo "== skipped (ABORT/late): $*"; return 1; }; temp "start $1"; shift; ns "$@" || echo "== FAILED: $*"; }
echo "== $(date) START robust (waiting for tmux extra)"
while tmux has-session -t =extra 2>/dev/null; do sleep 60; done
cool
for s in W G G2 R; do for seed in 1 2; do step "train_${s}_s${seed}" env SEED=$seed NAME=${s}_s${seed} python train_offset.py $s 15; cool; done; done
step warps_h12 env CAM_H=1.2 OUT=lane/warps_W_h12 python warp2d.py 6000
step warps_h16 env CAM_H=1.6 OUT=lane/warps_W_h16 python warp2d.py 6000
step train_W_h12 env NAME=W_h12 WARPS=lane/warps_W_h12 python train_offset.py W 15; cool
step train_W_h16 env NAME=W_h16 WARPS=lane/warps_W_h16 python train_offset.py W 15; cool
step eval python eval_multi.py
temp "end"
echo "== $(date) ALL DONE robust"
