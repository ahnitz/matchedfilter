#!/bin/bash
# Stage U baselines for one device: unify_baseline.sh PYTHON CAPTURE_DIR OUT_DIR TAG [DEVICE]
# Three plain rounds (throughput, stages, host CPU time), one round with device timing and the
# roofline (per-label counts and device seconds), and the feature dump; one JSON file each.
# The chain is pinned so that runs of different trees compare like with like.
set -u
PY=$1; CAP=$2; OUT=$3; TAG=$4; DEV=${5:-gpu:0}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT"
export MF_CHAIN_FORCE="2048:256,512" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
       VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
for r in 1 2 3; do
  "$PY" "$HERE/search_bench.py" "$CAP" --device "$DEV" --repeats 3 --json "$OUT/${TAG}_r$r.json" \
    | grep -E "^device"
done
MF_GPU_TIMING=1 "$PY" "$HERE/search_bench.py" "$CAP" --device "$DEV" --repeats 2 --roofline \
  --json "$OUT/${TAG}_timing.json" | grep -E "^device|roofline [0-9]"
"$PY" "$HERE/gpu_features.py" --device "$DEV" --json "$OUT/${TAG}_features.json" > /dev/null
echo "baseline $TAG done"
