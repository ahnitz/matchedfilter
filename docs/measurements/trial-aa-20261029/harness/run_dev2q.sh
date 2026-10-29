#!/bin/bash
# The quiet-dev2 supplement (2026-10-29 ~16:50, load ~1-2): the solo replay control and 12 short
# ladders, one job at a time on core 28, from the worktree root, library at the A/A commit.
S=/tmp/claude-1000/-home-ahnitz-projects-claude-searchdev/5386f69e-dcbd-4feb-9d17-703c52804e73/scratchpad/ws-stat
cd /home/ahnitz/projects/claude/searchdev/work/wk-r7a
export PYTHONPATH=/home/ahnitz/projects/claude/searchdev/work/wk-r7a/python OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VK_ICD_FILENAMES=/nonexistent/icd.json VK_DRIVER_FILES=/nonexistent/icd.json PYTHONDONTWRITEBYTECODE=1 TMPDIR=/home/ahnitz/projects/claude/searchdev/work/wk-r7a/build/tmp
unset MF_TRIAL_AA_LOG MF_AUTOTUNE_LOG MF_COST_FILE MF_TRIAL_ROUNDS
echo "rev $(git rev-parse --short HEAD) lib-diff-vs-f634aeae $(git diff f634aeae -- python | wc -l)"
for set in qsolo qladshort; do
  echo "== $set $(date +%T) load $(cut -d' ' -f1-3 /proc/loadavg)"
  /home/ahnitz/projects/claude/searchdev/work/venv-gatechain/bin/python $S/h/jobs.py $S/data/dev2/$set/jobs_$set.json $S/data/dev2/$set/index.jsonl 28 > $S/data/dev2/$set/queue.out 2>&1
  echo "   done $(date +%T) load $(cut -d' ' -f1-3 /proc/loadavg): $(grep -c 'rc=0' $S/data/dev2/$set/queue.out) ok, $(grep 'rc=' $S/data/dev2/$set/queue.out | grep -vc 'rc=0') failed"
done
echo ALLDONE
