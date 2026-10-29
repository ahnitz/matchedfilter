#!/bin/bash
# After run_dev1.sh: the short ladders (cores 8-15), then the solo control (core 8 alone).
B=$HOME/fleet/wk-r7a-data; H=$B/h; O=$B/out
until grep -q ALLDONE $O/lad/queue.out 2>/dev/null; do sleep 20; done
cd $HOME/fleet/wk-r7a && source ~/matchedfilter-benchmark-20260926/venv/bin/activate
export PYTHONPATH=$HOME/fleet/wk-r7a/python OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VK_ICD_FILENAMES=/nonexistent/icd.json VK_DRIVER_FILES=/nonexistent/icd.json PYTHONDONTWRITEBYTECODE=1
unset MF_TRIAL_AA_LOG MF_AUTOTUNE_LOG MF_COST_FILE MF_TRIAL_ROUNDS
PY=$(which python)
for spec in ladshort:8,9,10,11,12,13,14,15 solo:8; do
  s=${spec%%:*}; cores=${spec#*:}
  echo "== $s $(date +%T) load $(cut -d' ' -f1-3 /proc/loadavg)"
  nice -n 5 $PY $H/jobs.py $O/$s/jobs_$s.json $O/$s/index.jsonl $cores > $O/$s/queue.out 2>&1
  echo "   done $(date +%T) load $(cut -d' ' -f1-3 /proc/loadavg): $(grep -c 'rc=0' $O/$s/queue.out) ok, $(grep 'rc=' $O/$s/queue.out | grep -vc 'rc=0') failed"
done
echo ALLDONE
