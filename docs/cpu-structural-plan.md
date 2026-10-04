# Plan for the matchedfilter developer: a reduced-rate analytic engine

**Audience:** the matchedfilter (MF) library developer. Implement and test this on the
library side first. Once it's validated there, the PyCBC developer adopts it (§6); their
changes are small and come later.

**Relation to other plans:** follows `docs/cpu-levers-consumer.md`, which tunes how each
stage runs. This changes *what* is computed, so the two compound. Measurements are against
the real consumer (`pycbc_inspiral_fir` with `ntest3.sh` settings). Gains reuse the measured
stage shares in `cpu-levers-consumer.md` §2.

**Headline.** The analytic SNR series the library filters carries content only in
**[20, 800) Hz**, but it's processed at 2048 Hz. Running at **1024 Hz internally** is
lossless.

- **Step 1** — library only, **no API change, no PyCBC change**: ≈1.13× on the whole
  Haswell run (1.18× on library time).
- **Step 2** — once PyCBC opts into a reduced-rate upper stage: ≈1.20× (1.29× on library).
- **With the consumer report's levers** (tier-1 staging, Q15, refine pooling): ≈1.47×
  (1.40–1.53×).

---

## 1. Why it's lossless

The library filters the analytic series: real part is the 0-phase matched-filter output,
imaginary part the π/2 output, `|z|` the phase-maximised SNR. Its spectrum is one-sided by
construction. A *real* series with content to 800 Hz needs fs > 1600 Hz. The analytic one
needs complex sampling at only fs ≥ 800 Hz, since there's no negative-frequency mirror to
alias into.

Measured on two real middle-reference series captured mid-run from the consumer:

| Quantity | Capture A | Capture B |
|---|---|---|
| Power in [20, 800) Hz | 0.999991 | 0.999984 |
| Negative-band power (Blackman-Harris window) | **3.6e-14** | **6.3e-11** |
| Full-rate series rebuilt from `x[::2]` alone, rms rel. error | 3.3e-6 | 1.5e-5 |
| ... max rel. error | 9.2e-6 | 7.4e-5 |

Every template in `fir_three_level_701taps.hdf` has `f_final = 800`. So decimating by 2 is
literally `x[::2]`: no anti-alias filter, no leak.

## 2. Compatibility contract — what must not change

The consumer depends on more than the trigger list:

- **Result geometry.** `RatioPowerChisq.compute` (`pycbc_inspiral_fir:195–300`) takes each
  trigger's `block_starts` plus `len(filters_f[id])` as the block geometry, and slices the
  caller's **full-rate** `ref_snr[tstart:tstart+block_len]` to recompute power chisq.
- **Private internals.** The consumer reaches into `bank._groups`,
  `g.get_correlation_plan()`, `cplan.valid`, `_automatic_series_layout`,
  `cplan._execution_plan().correlate_series_continuous(...)` and `cplan._continuous_gpu`
  (`pycbc_inspiral_fir:73–160`).

So, by default:

1. **`FilterResults`** (`time_domain.py:16`) keeps exactly its five fields, in input-rate
   units. Don't add a field: positional unpacking would break. `sample_indices` and
   `block_starts` stay in input-rate samples. `block_lengths` stays the block span in
   input-rate samples (2048), even when the internal transform is 1024 points.
2. **`filters_f` / `get_filter_f` / `get_block_length`** (`:368`, `:397`) keep returning
   input-rate (2048-point) spectra and lengths. Chisq uses them.
3. **`groups`** (`:378`) keeps its existing keys and values. *Adding* keys (`engine_n`,
   `engine_rate`) is fine.
4. **The upper stage's** `correlate_series_continuous` keeps writing full-rate output into
   the caller's buffer. The reduced-rate upper stage is a *new* entry point (§4), not a
   behaviour change.
5. **SNR values** stay within the library's existing comparison contract ("within float32
   roundoff, not bitwise"). Budget: ≤ 1e-4 relative at reported peaks; the measured
   rebuild error is 1e-5.
6. **GPU backends** keep today's behaviour until they implement the mode. The new path is
   CPU-only at first, with an automatic fallback.

## 3. Step 1 — internal reduced rate for the hierarchical engine (no API change)

### 3.1 Opt-in, then default
Add a keyword-only constructor argument, `execution_rate`:

- `None` (initial default): today's behaviour.
- `'auto'`: use the lowest `data_sample_rate / 2^k` whose one-sided band `[0, rate)` contains
  the reference profile's support, with margin (e.g. profile power above 0.98·rate below
  1e-9). Otherwise fall back to full rate.
- An explicit rate.

Flip the default to `'auto'` only after §5 passes. Keep the existing two-sided multi-rate
path (`tap_sample_rate ≠ data_sample_rate`) unchanged for current callers; it's a different
feature.

### 3.2 What changes inside, for `engine='hier'`
1. **One-sided tap spectra.** Keep bins `[0, N_e)` of the input-rate tap spectrum. The
   existing two-sided truncation (`time_domain.py:292–295`) would discard [512, 800) Hz
   (~1.3% of SNR power) and keep the empty negative band. Extend the C `taps_to_spectra`
   fast path (gated on `rate_ratio == 1.0` at `:258`) to this case.
2. **Free decimation.** In `ap_hmf_run_series`, the block load already copies and scales
   (`hmf.c:272–275`, `dst[k]=src[k]*inv`). Read with stride 2 instead; the forward FFT
   becomes 1024 points.
3. **Block length in time.** `pick_n`'s candidates are in samples starting at 2048
   (`time_domain.py:27`, `:53`), so at 1024 Hz it would choose 2 s blocks and double the
   coarse band in bins. Express candidates as durations, or include 1024.
4. **Coarse stage unchanged.** At 1 Hz bins the coarse band covers the same frequencies with
   the same `b` and the same lag spacing in time. Gate thresholds and calibration carry
   over; the gate model keys on the engine `n` but should reproduce the same thresholds.
5. **Refine at n = 1024**, then **interpolate back to input-rate indices and SNRs**:
   - **Only one fractional phase is needed.** The rate ratio is exactly 2, so even input-rate
     samples are the engine samples themselves; with content inside [0, 1024) Hz the
     2048-point inverse at even indices equals the 1024-point inverse, up to roundoff. Odd
     samples are a fixed half-sample delay. That's one precomputed filter, not a fractional
     LUT.
   - **The filter.** Demodulate by the band centre `f_c ≈ 410 Hz`, folded into the
     coefficients: `z(2m+1) = Σ_j g[j]·z_e[m+j]` with
     `g[j] = sinc(½ − j)·kaiser[j]·exp(2πi·f_c·(½ − j)/1024)` and `j = −K/2+1 … K/2`.
     Centring makes the transition band symmetric (390 → 634 Hz), which is what keeps the
     kernel short. Measured on the real captured series, against its true odd samples
     (error relative to rms `|z|`):

     | Taps | Centred (f_c = 410 Hz) rms / at peaks | fs/2 (f_c = 512 Hz) rms |
     |---|---|---|
     | 16 | 1.4e-3 / 1.2e-3 | 2.6e-1 |
     | 24 | 9.7e-5 / 8.7e-5 | 1.4e-1 |
     | **32** | **4.0e-6 / 4.3e-6** (the data's own floor) | 7.5e-2 |
     | 64 | 2.5e-6 / 2.9e-6 | 3.9e-3 |

     Use **32 taps**, centred. Demodulating at fs/2, as the `multiband` branch's
     `KAISER_128_LUT` does for its arbitrary offsets, is ~1000× worse here even at 64 taps.
     Cost: ~256 flops per interpolated point, ~1–6% of the 1024-point refine transform per
     refined pair.
   - **Evaluate locally, behind a scalloping guard.** For each refined pair, evaluate the
     half-sample points on either side of every engine sample with `|z| ≥ thr·(1 − L)`.
     Take `L` from the reference profile: `1 − |A(1)|/|A(0)|` at input-rate lag 1, where
     `A` is the profile autocorrelation the gate model already computes. Add margin, since
     noise changes local curvature (a guard as loose as `0.8·thr` still costs only a
     handful of evaluations). Report the input-rate sample with the largest `|z|` and its
     complex value, with today's per-bin semantics.
   - **Edges.** Widen the engine-rate `c_bad` by `K/2` (16 samples), so the kernel never
     reads corrupted overlap-save samples near the valid-window edges. ~2% more blocks.
6. **Block geometry reported at input rate:** `block_starts = 2 × engine starts`,
   `block_lengths = 2 × N_e`. The internal block step and `c_bad` halve consistently.

### 3.3 Step 1 gain
Measured stage shares; forward FFT and scaling ÷2.2 (assumed to be 75% of "outside
kernels"), refine ÷2.1. These are flop ratios, not a measured build.

| Host | Whole run | Library time |
|---|---|---|
| Haswell | **1.13×** | 1.18× |
| dev1 | 1.15× | 1.20× |
| dev2 | 1.09× | 1.14× |

### 3.4 Synergy with the consumer report
At n = 1024 the refine and per-block forward transforms fall **inside** the existing pair-path
caps (`ap_create_pairbatch` / `pairbatch_size`: `N ≤ 1024`). The refine-pooling lever from
`cpu-levers-consumer.md` §4.3 then needs no cap change. It can reuse the template-major copy
and stride-1 `gather_template_batch` that `f371d01` added for tier-1; pooling survivors
across the `g` blocks of a call isn't implemented yet and is still needed to fill lanes.

## 4. Step 2 — new opt-in API for a reduced-rate upper stage

The upper stage (`engine='corr'`, 8–10% of the run) writes dense full-rate middle series.
Halving it needs a new entry point, because the existing one's output buffer is part of the
contract:

- **`AnalyticSeries`:** a small container holding samples at the reduced rate, the rate, the
  one-sided band, and the input-rate sample offset. It has a `window(start, stop)` method
  that returns **input-rate samples on demand** by band-limited interpolation. Chisq only
  needs full-rate windows around triggers, which are rare.
- **The corr engine** gets a method such as `correlate_series_analytic(...) -> AnalyticSeries`.
  It keeps only the positive bins in its frequency-domain product and inverse-transforms at
  the engine size. Transform sizes halve (taps 3001–6001 → ~1500–3000; n = 8192/16384 →
  4096/8192), and so does the dense output.
- **`filter_series`** also accepts an `AnalyticSeries`, skipping the internal decimation.

Step 2 gain, combined with step 1: **1.20× whole run on Haswell** (1.29× library), dev1 1.21×,
dev2 1.14×.

**Optional — peak resolution as a parameter.** Since peaks come from interpolation, the
resolution is independent of every stage before it. A `peak_upsample` keyword (default 1, so
units unchanged) can report finer, documented sub-sample indices and their SNRs, at
negligible per-trigger cost.

## 5. Library-side validation (before PyCBC sees it)

1. **Equivalence.** On band-limited analytic test series and on the captured consumer series:
   full rate vs `execution_rate='auto'`. Identical trigger sets (same input-rate indices);
   SNR within 1e-4 relative.
2. **Scalloping guard.** Inject peaks at half-sample offsets just above threshold. None may be
   dismissed relative to the full-rate path.
3. **Fallback.** A profile with support beyond the reduced rate must run at full rate.
4. **Compatibility.** `FilterResults` shape and units, `filters_f` lengths,
   `get_block_length`, and existing `groups` keys are unchanged by the mode. Reuse the
   consumer's chisq geometry: block start + `len(filters_f)` must still index the full-rate
   series correctly.
5. **Calibration.** Gate-model thresholds unchanged; re-run `tests/test_gate_model.py`.
6. **Performance.** Replay real captured consumer inputs (the capture/replay method of
   `cpu-levers-consumer.md` §6) on dev1 (clean AVX2) and Haswell (production-like): the
   stage split at full rate vs reduced rate, interleaved.
7. **Interpolation accuracy.** Peak SNR vs the full-rate reference across the band, including
   near 800 Hz.

## 6. Handoff to the PyCBC developer (after §5)

- **P1 — fine stage:** set `execution_rate='auto'`, or nothing once it's the default. No other
  change: indices, block geometry, `filters_f` and the full-rate `ref_snr` used by chisq are
  untouched. ≈1.13× on Haswell.
- **P2 — upper stage:** switch `UpperReferenceBatch` to `correlate_series_analytic`, pass the
  resulting `AnalyticSeries` to `filter_series`, and have chisq read its block through
  `window(...)`. ≈1.20× on Haswell.
- **P3 — optional, PyCBC-side:** produce the top reference series at the reduced rate too.
  "Upper Ref SNR Generation" is 8.5% of the Haswell run.

## 7. Tested and ruled out

| Idea | Evidence | Verdict |
|---|---|---|
| Gate children on their FIR parent's SNR (two-step hierarchy [3,4]) | Fine-vs-assigned-middle match 0.28–1.0, median 0.54; the hierarchy is computational (filter match ≥ 0.9999), not detection-based | A parent threshold would sit inside the noise |
| SVD / low-rank sharing (LLOID [2]) | Rank for 0.1% residual: 10–21 at band 256; reconstruction costs `8·r·b` vs ~`4·b·log₂b`, break-even near r ≈ 8 | ~1.3× slower at r ≈ 17 |
| Template-space interpolation [5] | A fixed linear basis, bounded by the SVD result | Same verdict |
| Shift the coarse band off empty bins 0–19 | Measured: (256) +3%, (128, 256) **+17%** slower; the empty bins are a guard band against coarse-grid scalloping, and the gate model lowers thresholds without them | Withdrawn |
| 64-bin first pass | Tier-0 pass rate 86–99% | Not a gate |

## 8. Open questions

- **Proxy gate from a better-matched coarse template** (Soni et al. [3]). The bank's
  per-template `max_matches` (median 0.957, p10 0.85) is uncorrelated with the
  assigned-parent match. *Needs confirming what it measures* before modelling: best match to
  another coarse-level template, or nearest-neighbour match within the fine bank.
- **fp16 beyond Q15.** The PyTorch port of GstLAL's filtering reports search performance
  comparable to full precision in float16 [6]. AVX512-FP16 (Intel Sapphire Rapids and later)
  would give 32 lanes per register.
- **Time-slice multi-rate FIRs** (LLOID-style [2]). If a ratio FIR's long-delay taps carry
  mostly low-frequency content, split it into a short full-rate core and a low-rate tail, to
  shorten blocks and raise the 0.70 valid fraction. Untested.

## References

1. Adams et al. (MBTA), CQG 33 175012 (2016), [arXiv:1512.02864](https://arxiv.org/abs/1512.02864).
   Two bands, the low band downsampled in the frequency domain, quadratic upsampling,
   combination only above a per-band threshold.
2. Cannon et al. (LLOID), ApJ 748 136 (2012); recent description:
   [arXiv:2305.05625](https://arxiv.org/html/2305.05625).
3. Soni, Gadre, Mitra, Dhurandhar, PRD 105 064005 (2022), [arXiv:2106.08925](https://arxiv.org/abs/2106.08925).
4. Gadre, Mitra, Dhurandhar, PRD 99 124035 (2019), [arXiv:1807.06803](https://arxiv.org/abs/1807.06803).
5. Croce et al., cardinal interpolation of PN filter banks, [arXiv:gr-qc/0008059](https://arxiv.org/abs/gr-qc/0008059).
6. Scalable matched-filtering pipeline (PyTorch GstLAL), [arXiv:2410.16416](https://arxiv.org/abs/2410.16416).
