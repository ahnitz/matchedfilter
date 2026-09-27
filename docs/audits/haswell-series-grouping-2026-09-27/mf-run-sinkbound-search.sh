set -e
P=/home/ahnitz/pycbc-wider-cpu-benchmark-20260926
R=$P/hosts/og-node-169
export PYTHONPYCACHEPREFIX=$R/cache/pycache TMPDIR=$R/tmp XDG_CACHE_HOME=$R/cache MPLCONFIGDIR=$R/cache/mpl
export LD_LIBRARY_PATH=$P/lib OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PATH=$P/venv/bin:$P/src/apogee/bin:$PATH
export PYCBC_RATIO_DEVICE=cpu PYCBC_RATIO_UPPER_TIMING=1
unset PYCBC_RATIO_TIMING PYCBC_RATIO_PHASE MF_PBMAX MF_DGROUP MF_HMF_PROF
cd "$P/run"
for variant in sinkbound-1; do
 package=group-baseline
 case "$variant" in sinkbound-1|sinkbound-2) package=sinkbound-candidate;; esac
 export PYTHONPATH=$R/kernel-study/$package:$P/src/apogee
 taskset -c 3 bash run_fir_search.sh --bank-file "$P/run/fir_three_level_spin_mchirp_wider.hdf" --fft-backends fftw --ratio-filter-engine matchedfilter-hierarchical --ratio-filter-false-dismissal 0.001 --snr-threshold 5.5 --gps-end-time 1000002000 --output "$R/results/kernel-full-$variant.hdf" > "$R/results/kernel-full-$variant.log" 2>&1
 "$P/venv/bin/python" -B "$R/summarize.py" "$R/results/kernel-full-$variant.log" > "$R/results/kernel-full-$variant.json"
 echo "$variant completed"
done
