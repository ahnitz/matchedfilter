#!/bin/bash
# The dev2 A/A collection, in order: eq, full, offs, long, lad (cores 28-31), from the worktree root.
cd /home/ahnitz/projects/claude/searchdev/work/wk-r7a
export PYTHONPATH=/home/ahnitz/projects/claude/searchdev/work/wk-r7a/python OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VK_ICD_FILENAMES=/nonexistent/icd.json VK_DRIVER_FILES=/nonexistent/icd.json PYTHONDONTWRITEBYTECODE=1
unset MF_TRIAL_AA_LOG MF_AUTOTUNE_LOG MF_COST_FILE MF_TRIAL_ROUNDS
echo "rev $(git rev-parse --short HEAD) dirty $(git status --short | wc -l)"
for set in ${SETS:-eq full offs long lad}; do
  echo "== $set $(date +%T) load $(cut -d' ' -f1-3 /proc/loadavg)"
  /home/ahnitz/projects/claude/searchdev/work/venv-gatechain/bin/python /tmp/claude-1000/-home-ahnitz-projects-claude-searchdev/5386f69e-dcbd-4feb-9d17-703c52804e73/scratchpad/ws-stat/h/jobs.py /tmp/claude-1000/-home-ahnitz-projects-claude-searchdev/5386f69e-dcbd-4feb-9d17-703c52804e73/scratchpad/ws-stat/data/dev2/$set/jobs_$set.json /tmp/claude-1000/-home-ahnitz-projects-claude-searchdev/5386f69e-dcbd-4feb-9d17-703c52804e73/scratchpad/ws-stat/data/dev2/$set/index.jsonl 28,29,30,31 > /tmp/claude-1000/-home-ahnitz-projects-claude-searchdev/5386f69e-dcbd-4feb-9d17-703c52804e73/scratchpad/ws-stat/data/dev2/$set/queue.out 2>&1
  echo "   done $(date +%T) load $(cut -d' ' -f1-3 /proc/loadavg): $(grep -c 'rc=0' /tmp/claude-1000/-home-ahnitz-projects-claude-searchdev/5386f69e-dcbd-4feb-9d17-703c52804e73/scratchpad/ws-stat/data/dev2/$set/queue.out) ok, $(grep 'rc=' /tmp/claude-1000/-home-ahnitz-projects-claude-searchdev/5386f69e-dcbd-4feb-9d17-703c52804e73/scratchpad/ws-stat/data/dev2/$set/queue.out | grep -vc 'rc=0') failed"
done
echo ALLDONE
