# Plan for the matchedfilter developer: a reduced-rate analytic engine

**Audience:** the matchedfilter (MF) library developer. Implement and test this on the
library side first. Once it's validated there, the PyCBC developer adopts it (§6); their
changes are small and come later.

**Relation to other plans:** follows `docs/cpu-levers-consumer.md`, which tunes how each
stage runs. This changes *what* is computed, so the two compound. Measurements are against
the real consumer (`pycbc_inspiral_fir` with `ntest3.sh` settings). Gains reuse the measured
stage shares in `cpu-levers-consumer.md` §2.

**Revised 2026-10-04 — read before implementing further.** §3.2.1 was wrong as first
written. Cutting the input-rate tap spectrum to `[0, N_e)` puts SNR errors of up to 3.6 into
the output (measured on a captured consumer call). Its replacement, folding the taps,
measures ≤ 3e-5. The first implementation also departs from §3.2.5 in two ways:
- It takes odd samples from a phase ramp on the block: errors up to 1.5. The kernel on exact
  values gives ≤ 5e-5.
- It has no scalloping guard.

§3.2.5 now says why each matters. Also new: §3.0 (no physical units), and §5 checks that
catch all three.

**Headline.** The analytic SNR series the library filters occupies only part of its
one-sided band. For the consumer that's [20, 800) Hz of a 2048 Hz series, so running the
engine decimated by 2 is lossless.

- **Step 1** — library only, **no API change, no PyCBC change**: ≈1.10× on the whole
  Haswell run (1.14× on library time).
- **Step 2** — once PyCBC opts into a reduced-rate upper stage: ≈1.17× (1.24× on library).
- **With the consumer report's levers** (tier-1 staging, Q15, refine pooling): ≈1.43×.

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

### 3.0 No physical units
Nothing here needs to know units. Decimating the input and folding the taps (§3.2.1) only
need to know which bins of the input-rate grid are occupied. The reference profile already
says so, in bins. So the engine should work in samples, bins and cycles per sample. The Hz
values in this plan (2048 → 1024 Hz, [20, 800) Hz, f_c ≈ 410 Hz) are the consumer's
instance, quoted because that's what was measured; none should be a constant in the code.
With `n` the input-rate block and `[k_lo, k_hi)` the profile's occupied bins:

| Quantity | Rule | Consumer value |
|---|---|---|
| Decimation `D` | Largest power of 2 with `[k_lo, k_hi)` inside `[0, n/D)` and room for the kernel's transition band | 2 |
| Kernel centre `ν_c` (cycles per engine sample) | `D·(k_lo + k_hi)/(2n)` | 0.40 |
| Kernel length `K` | From the empty fraction `e = 1 − D·(k_hi − k_lo)/n` and the error budget. Kaiser: `K ≈ (A − 8)/(2.285·2π·e)`, `A` in dB | 32, for 4e-6 |
| Fractional delays | `D − 1`, one kernel each | 1 (half a sample) |
| Engine `c_bad` | `ceil((taps//2)/D) + K/2` | 191 for 701 taps |
| Scalloping guard `L` | `1 − abs(R(D/2))`, with `R(τ)` the profile's normalised autocorrelation at `τ` input samples | 4.3% |

The first implementation hard-codes the consumer's values in several places:
- `'auto'` returns 1024.0 for any input rate ≥ 2048 without reading the profile, so a band
  above 1024 Hz would alias silently.
- `eff_band = (20.0, 800.0)` in `filter_series` and `correlate_series_analytic`.
- The 1024.0 switches for candidate block sizes and the output rate.
- The even/odd split assumes `D = 2`.

`AnalyticSeries` already derives its kernel centre from its band, which is the right pattern.

### 3.1 Opt-in, then default
Add a keyword-only constructor argument, a decimation factor rather than a rate:

- `None` (initial default): today's behaviour.
- `'auto'`: the `D` of §3.0, read from the reference profile; `D = 1` if nothing fits.
- An explicit `D`. If a rate is accepted for convenience, convert it to `D` at once.

Flip the default to `'auto'` only after §5 passes. Keep the existing two-sided multi-rate
path (`tap_sample_rate ≠ data_sample_rate`) unchanged for current callers; it's a different
feature.

### 3.2 What changes inside, for `engine='hier'`
1. **Engine tap spectra: fold the taps; don't cut the spectrum.** Build the engine filter
   in the time domain from the input-rate taps `h[s]` (centre-rolled, as today), with the
   half-sample kernel `g` of item 5:
   `h_e[q] = h[2q] + Σ_j conj(g[j])·h[2(q − j) + 1]`, then `H_e = FFT_{N_e}(h_e)`.
   (For general `D`: `h_e[q] = Σ_{r<D} Σ_j conj(g_r[j])·h[D(q − j) + r]`, with `g_0 = δ`.)
   Even taps carry over. Odd taps reach the engine grid through the same interpolator used
   for peaks. In the occupied band `H_e = H` to the kernel's accuracy. Outside it they differ,
   which is harmless because the series has nothing there. `h_e` is compact, within
   `ceil((taps//2)/2) + K/2` (±190 for 701 taps), so the engine `c_bad` grows by `K/2` = 16. It's a
   one-off per template, ~`taps/2 × K` MACs; a C fast path is optional. `filters_f` stays
   today's input-rate spectrum (§2 item 2), not `H_e` zero-padded. (The old two-sided
   truncation, `time_domain.py:292–295` at the time, would have discarded [512, 800) Hz.)

   **Not bins `[0, N_e)` of the input-rate spectrum**, as this item first said (implemented in
   the `self.analytic and N_taps > chosen_N` branch). The cut has the right in-band response.
   But it's a step at 0 Hz, where the consumer's FIRs have 6–133× their in-band gain. The
   engine filter then has a slowly decaying tail that no `c_bad` contains, and overlap-save
   wraps it into the output. Measured on a captured consumer call (701-tap group: 171
   templates × 366k engine samples, inside the analysis window), against the exact
   input-rate output:

   | Engine filter | `c_bad` | Max SNR error, median / worst template | Worst where SNR ≥ 5 |
   |---|---|---|---|
   | Cut `[0, N_e)` (implemented) | 175 | 0.35 / 3.6 | 0.40 |
   | Cut, 1.5× guard | 263 | 0.17 / 1.2 | 0.45 |
   | Cut, 2× guard | 350 | 0.14 / 0.99 | 0.38 |
   | **Fold, 32-tap kernel** | **191** | **1.9e-5 / 3.0e-5** | **1.3e-5** |

   No guard rescues the cut. A smooth taper through the empty bands (2–20 Hz, 800–1000 Hz)
   still leaves 0.01–0.13 with 32 extra guard samples. A least-squares fit of `H` in band on
   support `ceil((taps//2)/2) + m`, with `m < K/2`, might win back part of the extra guard. That's
   untested.
2. **Free decimation.** In `ap_hmf_run_series`, the block load already copies and scales
   (`hmf.c:272–275`, `dst[k]=src[k]*inv`). Read with stride `D` instead; the forward FFT
   becomes `n/D` points.
3. **Block length.** `pick_n`'s candidates are sample counts starting at 2048
   (`time_domain.py:27`, `:53` at the time). Applied to the engine at `D = 2`, they give
   blocks twice as long and double the coarse band in bins. Divide the input-rate candidates by `D`, rather than
   switching lists on a rate (the first implementation adds 1024 below a 1024 Hz engine).
4. **Coarse stage unchanged.** At the same bin spacing, the coarse band covers the same
   frequencies with the same `b` and the same lag spacing in time. Gate thresholds and
   calibration carry over. The gate model keys on the engine `n` but should reproduce the
   same thresholds. One check: `gatemodel._samples` draws peaks only at integer engine-grid
   offsets, so at `D = 2` it never draws a peak on an odd input sample. Confirm the
   false-dismissal rate with half-engine-sample offsets added (§5).
5. **Refine at `N_e`, then recover input-rate peaks.**
   - **The kernel.** Even input samples are the engine samples. Odd ones are a fixed
     half-sample delay of the engine grid (`D − 1` fixed delays in general). That's one
     precomputed filter, not a fractional LUT. Demodulate by the band centre, folded into the
     coefficients: `z(2m+1) = Σ_j g[j]·z_e[m+j]` with
     `g[j] = sinc(½ − j)·kaiser[j]·exp(2πi·ν_c·(½ − j))`, `j = −K/2+1 … K/2` and `ν_c` from
     §3.0. Centring makes the transition band symmetric, which is what keeps the kernel
     short. Measured on the real captured series, against its true odd samples (error
     relative to rms `|z|`):

     | Taps | Centred (ν_c = 0.40) rms / at peaks | Demodulated at fs/2 (ν = 0.5) rms |
     |---|---|---|
     | 16 | 1.4e-3 / 1.2e-3 | 2.6e-1 |
     | 24 | 9.7e-5 / 8.7e-5 | 1.4e-1 |
     | **32** | **4.0e-6 / 4.3e-6** (the data's own floor) | 7.5e-2 |
     | 64 | 2.5e-6 / 2.9e-6 | 3.9e-3 |

     Use **32 taps**, centred. Demodulating at fs/2, as the `multiband` branch's
     `KAISER_128_LUT` does for its arbitrary offsets, is ~1000× worse here even at 64 taps.
   - **Odd values only from exact values.** Apply the kernel to even outputs that are
     themselves exact. Or take a direct dot product of the input-rate taps with the caller's
     input-rate series: `z(2m+1) = Σ_s x[2m+1+s]·conj(h[s])`, ~`taps` complex MACs per point,
     exact, no edge handling. **Not** a phase ramp `exp(iπk/N_e)` on the block's spectrum, as
     implemented (the `rot_cache` / `z_odd` step at the end of `filter_series`). The ramp
     shifts the block as if it were periodic. Its wrap error lands at 0 ≡ `N_e`, where the
     FIR gain is large. Measured with the folded spectrum, so the even outputs are exact: the
     ramp is off by 0.08–0.38 mid-block and by up to 1.5 near the valid edges. The kernel on
     exact even outputs stays ≤ 4.8e-5 everywhere.
   - **Scalloping guard.** A peak on an odd input sample sits one input sample from the engine
     grid. There `|z|` is up to **4.3%** lower on the consumer's profile; today's worst case at
     full rate, half an input sample, is 1.17%. So the refine must report every bin whose
     engine max is ≥ `thr·(1 − L)` (§3.0, plus margin).
     - Lower only this reporting threshold. Keep the gate at `thr`, and don't route through
       the flat plan, which a lowered `threshold` argument does today.
     - For each reported bin, take the even samples within `L` of the bin's even max,
       evaluate their odd neighbours, report the largest, then apply `thr`.

     The first implementation thresholds the engine grid at `thr` and checks only the
     neighbours of the even max, so near-threshold peaks on odd samples are dismissed.
     Recomputing reported bins stays cheap. At `thr·(1 − L)` a noise block crosses on the
     order of 10⁻³ as often as it is refined (estimated, not measured).
   - **Edges.** The fold's `c_bad` (item 1) covers the even outputs, and the dot product needs
     nothing more. The kernel reads `K/2` beyond the reported window, so it needs another
     `K/2` of `c_bad`, or reads from the neighbouring block.
6. **Block geometry reported at input rate:** `block_starts = D × engine starts`,
   `block_lengths = D × N_e`, and the groups' `c_bad` = `D ×` the engine's.

### 3.3 Step 1 gain
Measured stage shares; forward FFT and scaling ÷2.2 (assumed to be 75% of "outside
kernels"), refine ÷2.1. The fold's larger `c_bad` (§3.2 item 1) then adds 3.3% (151 taps)
to 4.7% (701 taps) more blocks to every hierarchical stage. These are flop ratios, not a
measured build.

| Host | Whole run | Library time | Before the fold's guard (whole / library) |
|---|---|---|---|
| Haswell | **≈1.10×** | 1.14× | 1.13× / 1.18× |
| dev1 | ≈1.12× | 1.16× | 1.15× / 1.20× |
| dev2 | ≈1.07× | 1.10× | 1.09× / 1.14× |

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
  Its filters are folded as in §3.2.1. Keeping only the positive bins of the product is the
  same cut and fails the same way; the first `correlate_series_analytic` uses the cut
  spectra. It inverse-transforms at the engine size. Transform sizes halve (taps 3001–6001
  → ~1500–3000; n = 8192/16384 → 4096/8192), and so does the dense output.
- **`filter_series`** also accepts an `AnalyticSeries`, skipping the internal decimation.

Step 2 gain, combined with step 1: **≈1.17× whole run on Haswell** (1.24× library), dev1
≈1.18×, dev2 ≈1.11×. These include the fold's guard; without it they were 1.20× (1.29×),
1.21× and 1.14×.

**Optional — peak resolution as a parameter.** Since peaks come from interpolation, the
resolution is independent of every stage before it. A `peak_upsample` keyword (default 1, so
units unchanged) can report finer, documented sub-sample indices and their SNRs, at
negligible per-trigger cost.

## 5. Library-side validation (before PyCBC sees it)

1. **Equivalence.** On band-limited analytic test series and on the captured consumer series:
   full rate vs decimated. Identical trigger sets (same input-rate indices); SNR within 1e-4
   relative. Use the consumer's FIR taps, or taps like them: large gain below the band,
   truncated edges. Synthetic in-band chirps (e.g. 30–750 Hz) have little gain where the cut
   and the ramp go wrong. The first tests also compare trigger positions and in-band spectra,
   not output SNRs against the full-rate path. So they pass with both errors present.
2. **Engine filter, every sample.** Every even and odd output in the valid window, against
   the exact input-rate output: ≤ 1e-4. The cut (§3.2.1) fails this at 0.35 typical; the ramp
   (§3.2.5) at 0.08 mid-block.
3. **Scalloping guard.** Inject peaks on odd input samples, just above threshold. None may be
   dismissed relative to the full-rate path.
4. **Fallback.** A profile with support beyond the reduced band must run at full rate
   (`D = 1`). Include a band that a hard-coded 1024 Hz would alias.
5. **Compatibility.** `FilterResults` shape and units, `filters_f` values and lengths,
   `get_block_length`, and existing `groups` keys are unchanged by the mode. Reuse the
   consumer's chisq geometry: block start + `len(filters_f)` must still index the full-rate
   series correctly.
6. **Calibration.** Gate-model thresholds unchanged; re-run `tests/test_gate_model.py`, with
   peaks drawn on odd input samples as well (§3.2 item 4).
7. **Performance.** Replay real captured consumer inputs (the capture/replay method of
   `cpu-levers-consumer.md` §6) on dev1 (clean AVX2) and Haswell (production-like): the
   stage split at full rate vs reduced rate, interleaved.
8. **Interpolation accuracy.** Peak SNR vs the full-rate reference across the band, including
   near its edges.

## 6. Handoff to the PyCBC developer (after §5)

- **P1 — fine stage:** set the decimation option to `'auto'`, or nothing once it's the
  default. No other change: indices, block geometry, `filters_f` and the full-rate `ref_snr`
  used by chisq are untouched. ≈1.10× on Haswell.
- **P2 — upper stage:** switch `UpperReferenceBatch` to `correlate_series_analytic`, pass the
  resulting `AnalyticSeries` to `filter_series`, and have chisq read its block through
  `window(...)`. ≈1.17× on Haswell.
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
| Engine filter as bins `[0, N_e)` of the input-rate spectrum (first §3.2.1) | Max SNR error 0.35 median / 3.6 worst per template at `c_bad` 175; 0.14 / 0.99 at 2× guard | Replaced by the fold (§3.2.1) |
| Odd samples by a phase ramp on the block spectrum | Off by 0.08–0.38 mid-block, up to 1.5 near the valid edges | Kernel on exact values, or a direct dot product (§3.2.5) |
| Sub-grid (half-lag) coarse maximum, a cheap revival of the removed odd pass | Exact half-lag values would cut tier-0 survivors 3.5–4.1× and refines 12–18×. Guarded interpolation still misses crossings: with tapered spectra, 29–114 at band 128 and 1–3 at band 256. It also needs 0.7–8.9 interpolated points per pair | Killed by its pre-registered zero-miss criterion |

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
