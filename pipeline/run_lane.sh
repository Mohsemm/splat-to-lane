#!/usr/bin/env bash
# renders, warps, train W G G2 R, eval, closed loop
# 5 min cooldown between gpu jobs, stops if gpu > 90C
set -uo pipefail
cd /home/aymane/s3d
LOG=logs/lane-$(date +%Y%m%d-%H%M).log
exec > >(tee -a "$LOG") 2>&1
IMG=ghcr.io/nerfstudio-project/nerfstudio:latest
ns() { echo "== CMD $(date '+%F %T'): $*"; docker run --gpus all --rm -u "$(id -u)" -e HOME=/workspace -e USER=aymane -e LOGNAME=aymane \
  -e TORCHDYNAMO_DISABLE=1 -v /home/aymane/s3d:/workspace -w /workspace --shm-size=12gb "$IMG" "$@"; }
temp() { echo "== GPU $(date '+%T') $1: $(nvidia-smi --query-gpu=temperature.gpu,power.draw,fan.speed,utilization.gpu,memory.used --format=csv,noheader)"; }
cool() { temp "before cooldown"; sleep 300; temp "after cooldown"; }
aborted() { [ -e lane/ABORT ]; }
# gpu > 90C -> stop everything
rm -f lane/ABORT
( while true; do t=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | head -1)
    t=${t%%.*}; if [ "${t:-0}" -gt 90 ]; then echo "== ABORT $(date '+%T') GPU core ${t} C > 90" | tee -a "$LOG"; touch lane/ABORT; docker ps -q | xargs -r docker kill; fi
    sleep 20; done ) & GUARD=$!
trap 'kill $GUARD 2>/dev/null' EXIT

echo "== $(date) START lane pipeline"
while tmux has-session -t =big 2>/dev/null; do sleep 60; done
echo "== big splat finished $(date)"; cool
A=outputs/street_walk0/splatfacto/2026-10-28_204550/config.yml
B=outputs/street_walk02/splatfacto/2026-10-28_212103/config.yml
step() { aborted && { echo "== skipped (ABORT): $*"; return 1; }; temp "start $1"; shift; ns "$@" || echo "== FAILED: $*"; }
step renders_A python render_offsets.py A "$A" 6000; cool
step renders_B python render_offsets.py B "$B" 6000; cool
step warps_W python warp2d.py 6000
for s in W G G2 R; do step "train_$s" python train_offset.py "$s" 15; cool; done
step eval python eval_real.py
step closed_A python closed_loop.py A "$A" W G G2
temp "end"
echo "== $(date) ALL DONE lane pipeline"
