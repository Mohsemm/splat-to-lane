#!/usr/bin/env bash
# strict world, big worlds, 20k renders, extra seeds
set -uo pipefail
cd /home/aymane/s3d
LOG=logs/quality-$(date +%Y%m%d-%H%M).log
exec > >(tee -a "$LOG") 2>&1
IMG=ghcr.io/nerfstudio-project/nerfstudio:latest
ns() { echo "== CMD $(date '+%F %T'): $*"; docker run --gpus all --rm -u "$(id -u)" -e HOME=/workspace -e USER=aymane -e LOGNAME=aymane \
  -e TORCHDYNAMO_DISABLE=1 -v /home/aymane/s3d:/workspace -w /workspace --shm-size=12gb "$IMG" "$@"; }
temp() { echo "== GPU $(date '+%T') $1: $(nvidia-smi --query-gpu=temperature.gpu,power.draw,fan.speed,utilization.gpu,memory.used --format=csv,noheader)"; }
cool() { temp "before cooldown"; sleep 300; temp "after cooldown"; }
late() { [ "$(date +%H%M)" -ge 1630 ] && [ "$(date +%H%M)" -lt 1800 ]; }
rm -f lane/ABORT
( while true; do t=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits | head -1); t=${t%%.*}
    if [ "${t:-0}" -gt 90 ]; then echo "== ABORT $(date '+%T') GPU core ${t} C > 90" | tee -a "$LOG"; touch lane/ABORT; docker ps -q | xargs -r docker kill; fi
    sleep 20; done ) & GUARD=$!
trap 'kill $GUARD 2>/dev/null' EXIT
step() { { [ -e lane/ABORT ] || late; } && { echo "== skipped (ABORT/late): $1"; return 1; }; local n=$1; shift; temp "start $n"; t0=$(date +%s)
         ns "$@" || echo "== FAILED: $n"; echo "== DURATION $n $(( $(date +%s) - t0 )) s"; }
world() { # $1 name, $2 method, $3 data
  step "world_$1" ns-train "$2" --data "$3" --output-dir outputs --experiment-name "$1" --max-num-iterations 30000 \
    --viewer.quit-on-train-completion True --pipeline.datamanager.cache-images cpu nerfstudio-data --downscale-factor 1 --eval-mode filename; }
cfg() { ls -t outputs/$1/*/*/config.yml 2>/dev/null | head -1; }
SEEDS="G=G,G_s1,G_s2 G2=G2,G2_s1,G2_s2"
echo "== $(date) START quality (waiting for tmux final)"
while tmux has-session -t =final 2>/dev/null; do sleep 60; done
cool
# q1 strict
step strict_points python strict_points.py
world street_walk0_strict splatfacto split_walk0_strict; cool
step render_Astrict python render_offsets.py Astrict "$(cfg street_walk0_strict)" 6000; cool
step train_G_strict env NAME=G_strict RENDERS=lane/renders_Astrict python train_offset.py G 15; cool
step eval_q1 python eval_variants.py quality_q1 $SEEDS G_strict=G_strict
# q2 big worlds
world street_walk0_big splatfacto-big split_walk0; cool
world street_walk02_big splatfacto-big split_walk02; cool
step evalA_big ns-eval --load-config "$(cfg street_walk0_big)" --output-path eval/walk0big.json --render-output-path eval/renders_walk0big
step evalB_big ns-eval --load-config "$(cfg street_walk02_big)" --output-path eval/walk02big.json --render-output-path eval/renders_walk02big
step curve_big python metrics_by_offset.py walk0big:walk0 walk02big:walk02; cool
step render_Abig python render_offsets.py Abig "$(cfg street_walk0_big)" 6000; cool
step render_Bbig python render_offsets.py Bbig "$(cfg street_walk02_big)" 6000; cool
step train_G_big env NAME=G_big RENDERS=lane/renders_Abig python train_offset.py G 15; cool
step train_G2_big env NAME=G2_big RENDERS=lane/renders_Bbig python train_offset.py G2 15; cool
step eval_q2 python eval_variants.py quality_q2 $SEEDS G_big=G_big G2_big=G2_big
# q3 20k renders
step choose python choose_world.py lane/results/quality_q2.csv
docker run --rm -u "$(id -u)" -v /home/aymane/s3d:/workspace -w /workspace "$IMG" python choose_world.py lane/results/quality_q2.csv 2>/dev/null | grep -E "^(G|G2) " > lane/results/q3_choice.txt
cat lane/results/q3_choice.txt
while read -r fam best c _; do
  step "render_${fam}20k" python render_offsets.py "${fam}20k" "$c" 20000; cool
  step "train_${fam}_20k" env NAME=${fam}_20k RENDERS=lane/renders_${fam}20k python train_offset.py "$fam" 30; cool
done < lane/results/q3_choice.txt
step eval_q3 python eval_variants.py quality_q3 $SEEDS G_strict=G_strict G_big=G_big G2_big=G2_big G_20k=G_20k G2_20k=G2_20k
# q4 extra seeds
docker run --rm -u "$(id -u)" -v /home/aymane/s3d:/workspace -w /workspace "$IMG" python pick_q4.py lane/results/quality_q3.csv 2>/dev/null | grep -E "^G" > lane/results/q4_pick.txt
cat lane/results/q4_pick.txt
Q4=""
while read -r name set rd ep; do
  for seed in 1 2; do step "train_${name}_s${seed}" env SEED=$seed NAME=${name}_s${seed} RENDERS=$rd python train_offset.py "$set" "$ep"; cool; done
  Q4="$Q4 $name=$name,${name}_s1,${name}_s2"
done < lane/results/q4_pick.txt
ALLV="W=W,W_s1,W_s2 $SEEDS R=R,R_s1,R_s2 G_strict=G_strict G_big=G_big G2_big=G2_big G_20k=G_20k G2_20k=G2_20k"
for v in $Q4; do ALLV="${ALLV/ ${v%%=*}=${v%%=*}/ $v}"; done
late && echo "== (late) running final eval anyway (~1 min)"
temp "start eval_all"; ns python eval_variants.py quality_all $ALLV
temp "end"
ns python summarize.py
echo "== $(date) ALL DONE quality"
