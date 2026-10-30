#!/bin/bash
# remote_gpu_aa.sh SET N TOPS SEG: run from a fleet tree's root on dev3/dev4 (h5shim bank); GPU
# ladders one at a time with the A/A diagnostic, fresh cost files, logs in ~/fleet/gaa/SET.
SET=$1 N=$2 TOPS=$3 SEG=$4; D=/home/ahnitz/projects/claude/searchdev/tests/search_test/prod_job_test27; d=/tmp/claude-1000/-home-ahnitz-projects-claude-searchdev/5386f69e-dcbd-4feb-9d17-703c52804e73/scratchpad/ws-g/data/dev2/$SET; mkdir -p $d
export PYTHONPATH=$PWD/python OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
for i in $(seq 1 $N); do
  tag=${SET}_$i; cost=$d/$tag.cost.json; rm -f $cost $cost.lock
  l0=$(cut -d' ' -f1 /proc/loadavg); t0=$(date +%s)
  MF_TRIAL_AA_LOG=$d/$tag.jsonl MF_COST_FILE=$cost timeout 3600 taskset -c 12 ../venv-gatechain/bin/python tools/ladder.py --bank $D/fir_three_level_modern_v1_bottomup_cap401.hdf --profiles $D/ladder_profiles_H1.npz --device gpu:0 --tops $TOPS --segments $SEG --pipeline --pure --out $d/$tag.json > $d/$tag.log 2>&1
  rc=$?; t1=$(date +%s); l1=$(cut -d' ' -f1 /proc/loadavg)
  echo "{\"tag\": \"$tag\", \"host\": \"$(hostname -s)\", \"core\": \"12\", \"wall\": $((t1-t0)), \"load_start\": $l0, \"load_end\": $l1, \"rc\": $rc}" >> $d/index.jsonl
  rm -f $cost $cost.lock
done
echo ALLDONE >> $d/index.done
