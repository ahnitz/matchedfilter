#!/bin/bash
set -euo pipefail
base="$1"
out="$2"
alpha="$3"
new="$4"
cpu="$5"
pycbc="$6"
venv="$7"
source_first="$8"
rounds="$9"
mkdir -p "$out/cache"
cd "$base"
if [[ "$source_first" == yes ]]; then
  export PATH="$pycbc/bin:$venv/bin:$PATH"
else
  export PATH="$venv/bin:$pycbc/bin:$PATH"
fi
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYCBC_RATIO_DEVICE=cpu PYCBC_RATIO_UPPER_TIMING=1
export XDG_CACHE_HOME="$out/cache"
run_one() {
  local variant="$1" number="$2" target
  if [[ "$variant" == A ]]; then target="$alpha"; else target="$new"; fi
  export PYTHONPATH="$target:$pycbc"
  local path="$out/paired-$variant$number"
  taskset -c "$cpu" ./run_fir_search.sh \
    --bank-file fir_three_level_spin_mchirp_wider.hdf \
    --fft-backends fftw \
    --ratio-filter-engine matchedfilter-hierarchical \
    --ratio-filter-false-dismissal 0.001 \
    --snr-threshold 5.5 \
    --gps-end-time 1000002000 \
    --output "$path.hdf" >"$path.log" 2>&1
  grep 'We currently have' "$path.log" | tail -1
}
run_one B 3
run_one A 3
run_one A 4
run_one B 4
