#!/bin/bash
# The dev1 A/A collection (run from the shipped tree's root by fleet.sh): a seed cost file, then
# the sets eq, full, offs, long, lad on cores 8-15. Outputs in ~/fleet/wk-r7a-data/out/<set>.
set -u
B=$HOME/fleet/wk-r7a-data; H=$B/h; O=$B/out; CAP=$B/cap67; PY=$(which python)
export VK_ICD_FILENAMES=/nonexistent/icd.json VK_DRIVER_FILES=/nonexistent/icd.json PYTHONDONTWRITEBYTECODE=1
unset MF_TRIAL_AA_LOG MF_AUTOTUNE_LOG MF_COST_FILE MF_TRIAL_ROUNDS
echo "tree $PWD python $PY host $(hostname) load $(cut -d' ' -f1-3 /proc/loadavg)"
python -c "import matchedfilter as mf; print(mf.devices(), mf.targets() if hasattr(mf, 'targets') else '')"
for s in eq full offs long lad; do mkdir -p $O/$s; done
if [ ! -f $O/eq/seed.json ]; then
  MF_COST_FILE=$O/eq/seed_full.json taskset -c 8 $PY $H/replay_calls2.py $CAP 12 > $O/eq/seed.log 2>&1
  $PY -c "
import json; d=json.load(open('$O/eq/seed_full.json'))
for k in [k for k in d if k.startswith('choice|')]: del d[k]
json.dump(d, open('$O/eq/seed.json','w'))"
fi
cat $O/eq/seed.log
for s in eq full offs long; do $PY $H/gen_jobs.py $s $O/$s $PY $H $CAP; done
LADN=8 $PY $H/gen_jobs.py lad $O/lad $PY $H $CAP $HOME/mf-data/fir_three_level_modern_v1_bottomup_cap401.hdf $HOME/mf-data/ladder_profiles_H1.npz
for s in ${SETS:-eq full offs long lad}; do
  echo "== $s $(date +%T) load $(cut -d' ' -f1-3 /proc/loadavg)"
  $PY $H/jobs.py $O/$s/jobs_$s.json $O/$s/index.jsonl 8,9,10,11,12,13,14,15 > $O/$s/queue.out 2>&1
  echo "   done $(date +%T) load $(cut -d' ' -f1-3 /proc/loadavg): $(grep -c 'rc=0' $O/$s/queue.out) ok, $(grep 'rc=' $O/$s/queue.out | grep -vc 'rc=0') failed"
done
echo ALLDONE
