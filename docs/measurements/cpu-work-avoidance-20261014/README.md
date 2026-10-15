# Shared-subspace screening feasibility

This probe tests a reject-only use of a shared basis. It does **not** reconstruct every
filter output as a replacement for the existing filter bank. The inexpensive bound tested
here rejects too few pairs to justify native implementation on the measured workload.
This is a negative result for these bounds and clusters, not for every possible proxy gate.

Run [proxy_bounds.py](proxy_bounds.py) with the cap401 bank and matching H1 profiles:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 taskset -c 12 python \
  docs/measurements/cpu-work-avoidance-20261014/proxy_bounds.py \
  --bank /path/to/fir_three_level_modern_v1_bottomup_cap401.hdf \
  --profiles /path/to/ladder_profiles_H1.npz --output proxy_bounds.json
```

The recorded [results](proxy_bounds.json) use source `c5994d1e`, top 4, all 4,698 fine
filters in its 27 middle banks, `N=2048`, coarse band 256, 32 Gaussian spectral blocks,
and seed 71. File hashes identify the external inputs. The model uses SNR 6, dismissal
budget 0.001, and chain `(256,512,1024)`. Its first threshold is 4.101588; the reference
power fraction in the coarse band is 0.888643. This is a bound-feasibility study, not a
timing measurement or production-input replay.

## Method

Each centered fine filter spectrum is weighted by the square root of the input power:
the H1 top profile times the squared magnitude of its assigned middle filter. Normalize
by the filter's full positive-frequency output power and the reference coarse-band
fraction, matching the coarse SNR convention. Draw independent complex Gaussian bins
with unit variance in each quadrature; profile-zero bins are zero. The same 32 draws
are reused across banks. A bank-wide basis or phase-invariant, farthest-first medoid
clusters supplies an SVD basis of rank 1, 2, 4, 8, or 16. Clusters do not align time lags.
Requested cluster sizes 8, 16, and 32 determine the number of centers, not a hard size cap.

For coarse filter `c_t = a_t V + r_t`, let `Y_j(lag)` be the unnormalized inverse
transform of the Gaussian data times basis vector `V_j`. Two upper bounds are evaluated:

- **Oracle:** `max_lag |sum_j a_tj Y_j(lag)| + ||X||₂ ||r_t||₂`.
  Computing the projected filter's exact maximum is treated as free. This is optimistic;
  its per-template reconstruction would cost work that the screen aims to avoid.
- **Cheap:** `||a_t||₂ max_lag ||Y(lag)||₂ + ||X||₂ ||r_t||₂`.
  The shared basis-energy maximum is computed once per cluster; each template needs
  only its coefficient and residual norms.

A second residual bound splits frequencies into 16 contiguous regions and uses
`sum_s ||X_s||₂ ||r_ts||₂`. It is still a Cauchy–Schwarz certificate, with extra per-template
work. Reject a pair only when its upper bound is below the existing first-stage gate.

All bounds use the full 256-lag circular window. The reference gate is calibrated for
full-rate window `[192,1856)`; production searches a clipped valid window that varies
by group/block. A future clipped-region or lag-aligned proxy could be tighter. These
Gaussian blocks omit time-window spectral leakage and do not constitute a signal or
false-dismissal test. The mathematical bounds apply to the modeled vectors; a runtime
implementation would also need conservative floating-point margins and handling of
power-zero bins and leakage. No runtime implementation was attempted.

## Results and break-even condition

For a whole-bank rank 1/2/4/8 basis, median residual radii are respectively
17.584 / 15.331 / 12.245 / 7.789 SNR, against a 4.102 threshold. The unsplit oracle
rejects zero pairs for all four ranks. Splitting the residual frequency regions lets
rank 8 reject only 0.002%.

The following rates include **all 4,698 templates**. Groups with size no greater than
the candidate rank retain their original filters: their rejection and added basis work
are both zero. The JSON also retains conditional rates and the number of covered templates.

| Basis | Covered templates | Basis transforms / original transforms | Oracle rejection | Oracle, split residual | Cheap rejection | Cheap, split residual |
|---|---:|---:|---:|---:|---:|---:|
| Whole bank, rank 8 | 4,698 | 4.60% | 0% | 0.002% | 0% | 0% |
| Whole bank, rank 16 | 4,698 | 9.20% | 25.09% | 30.55% | 0% | 0% |
| Cluster target 32, rank 8 | 4,551 | 22.65% | 54.12% | 57.81% | 0% | 0% |
| Cluster target 8, rank 2 | 4,653 | 24.44% | 1.47% | 2.01% | 0.144% | 0.193% |

Even under equal transform costs, rejection must exceed the extra basis-transform
fraction **before** paying for bounds, clustering metadata, and survivor handling.
The usable cheap bound fails this necessary condition by a wide margin. The oracle's
higher rejection at rank 16 or clustered rank 8 does not establish a speedup because
it hides the reconstruction cost. The existing Q15 filter also makes an equal-cost
basis-transform assumption favorable to this proposed screen.

Separately, the recorded ladder run has exactly 27 initial hierarchical plans totaling
4,698 templates, one per distinct middle input. There are no duplicate fine-group
forwards to eliminate in that workload; each bank already shares a forward among its
80–254 fine filters. Larger banks or different layouts may have different reuse.
