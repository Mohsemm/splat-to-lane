#!/usr/bin/env bash
# R real frames + G2 renders, 3 seeds
set -uo pipefail; cd /home/aymane/s3d
LOG=logs/mix-$(date +%Y%m%d-%H%M).log; exec > >(tee -a "$LOG") 2>&1
IMG=ghcr.io/nerfstudio-project/nerfstudio:latest
ns() { echo "== CMD $(date '+%F %T'): $*"; docker run --gpus all --rm -u "$(id -u)" -e HOME=/workspace -e USER=aymane -e LOGNAME=aymane \
  -e TORCHDYNAMO_DISABLE=1 -v /home/aymane/s3d:/workspace -w /workspace --shm-size=12gb "$IMG" "$@"; }
temp() { echo "== GPU $(date '+%T') $1: $(nvidia-smi --query-gpu=temperature.gpu,power.draw,fan.speed,utilization.gpu,memory.used --format=csv,noheader)"; }
( while true; do t=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | head -1); t=${t%%.*}
    if [ "${t:-0}" -gt 90 ]; then echo "== ABORT $(date '+%T') GPU core ${t} C > 90"; touch lane/ABORT; docker ps -q | xargs -r docker kill; fi; sleep 20; done ) & GUARD=$!
trap 'kill $GUARD 2>/dev/null' EXIT
late() { [ "$(date +%H%M)" -ge 2215 ]; }
echo "== $(date) START mix (waiting for tmux media)"
while tmux has-session -t =media 2>/dev/null; do sleep 30; done
rm -f lane/ABORT; done_models=""
for s in 0 1 2; do
  { late || [ -e lane/ABORT ]; } && { echo "== skipped seed $s (late/ABORT)"; continue; }
  temp "before cooldown"; sleep 300
  nm=RG2; [ $s -gt 0 ] && nm=RG2_s$s
  temp "start $nm"; t0=$(date +%s)
  SEED=$s NAME=$nm ns env SEED=$s NAME=$nm python train_offset.py RG2 15 && done_models="$done_models,$nm" || echo "== FAILED $nm"
  echo "== DURATION $nm $(( $(date +%s) - t0 )) s"
done
m=${done_models#,}
[ -n "$m" ] && ns python eval_variants.py quality_mix W=W,W_s1,W_s2 G2=G2,G2_s1,G2_s2 R=R,R_s1,R_s2 RG2=$m G2_20k=G2_20k,G2_20k_s1,G2_20k_s2
temp end; echo "== $(date) ALL DONE mix"
