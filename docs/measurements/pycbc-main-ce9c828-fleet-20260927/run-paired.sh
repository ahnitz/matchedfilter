#!/bin/bash
# Redo driver: interleaved paired A/B, two comparisons + reverse-order check.
set -euo pipefail
base="$1"; out="$2"; alpha="$3"; old="$4"; new="$5"; cpu="$6"
pycbc="$7"; venv="$8"; source_first="$9"; rounds="${10}"; extra_ld="${11:-}"
mkdir -p "$out/cache" "$out/old-v-new"
cd "$base"
if [[ "$source_first" == yes ]]; then export PATH="$pycbc/bin:$venv/bin:$PATH"
else export PATH="$venv/bin:$pycbc/bin:$PATH"; fi
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYCBC_RATIO_DEVICE=cpu PYCBC_RATIO_UPPER_TIMING=1
export XDG_CACHE_HOME="$out/cache"
[[ -n "$extra_ld" ]] && export LD_LIBRARY_PATH="$extra_ld:${LD_LIBRARY_PATH:-}"

run_one() { # target label dir
  export PYTHONPATH="$1:$pycbc"
  taskset -c "$cpu" ./run_fir_search.sh \
    --bank-file fir_three_level_spin_mchirp_wider.hdf \
    --fft-backends fftw --ratio-filter-engine matchedfilter-hierarchical \
    --ratio-filter-false-dismissal 0.001 --snr-threshold 5.5 \
    --gps-end-time 1000002000 --output "$3/$2.hdf" >"$3/$2.log" 2>&1
}
# Comparison 1: alpha6 (A) vs new (B), interleaved A1 B1 A2 B2 ...
for ((i=1;i<=rounds;i++)); do run_one "$alpha" "paired-A$i" "$out"; run_one "$new" "paired-B$i" "$out"; done
# Comparison 2: prior hdev (A) vs new (B)
for ((i=1;i<=rounds;i++)); do run_one "$old" "paired-A$i" "$out/old-v-new"; run_one "$new" "paired-B$i" "$out/old-v-new"; done
# Reverse order guard: B first, then A, appended as rounds+1
j=$((rounds+1))
run_one "$new" "paired-B$j" "$out/old-v-new"; run_one "$old" "paired-A$j" "$out/old-v-new"
echo "DONE $(hostname)"
