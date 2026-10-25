/* matchedfilter - single-threaded batched filtering and full correlation.
 *
 * Correlate D data segments against T templates and get back, for each pair, the
 * loudest sample in each bin of a search window, or every correlation lag.
 *
 * Inputs are FREQUENCY DOMAIN: the unnormalised forward transform of each
 * segment, natural order, interleaved complex float32.  CPU peak filtering
 * supports powers of two from 64 to 2^20; full output supports 2^10 to 2^22.
 *
 * Correlation is circular; zero-pad before ingest for linear.  The inverse is
 * unnormalised, matching FFTW and MKL, so a perfect match returns n * energy.
 *
 * There is no plan object to manage beyond the filter itself: ap_mf_plan holds
 * everything, is built once, and is reused for every pair.
 */
#ifndef MATCHEDFILTER_H
#define MATCHEDFILTER_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

/* Transform direction, only needed by the internal transform API. */
#define AP_FORWARD  (-1)
#define AP_BACKWARD (+1)

/* One peak: where it is, and what the transform's value there is. */
typedef struct {
    long  index;      /* bin index k, in [0, N)                      */
    float re, im;     /* X[k]                                        */
    float magnitude;  /* |X[k]| = sqrt(re*re + im*im)                */
} ap_peak;

/* ---- batched matched filter -----------------------------------------------
   D data segments against T template segments, all length n.  For every pair,

       z[k] = IFFT( FFT(data_d)[f] * conj(FFT(tmpl_t)[f]) )[k]

   and the same peak report as ap_binmax: the loudest sample per bin of the
   search window, with a detection floor.

   Segments are supplied ALREADY TRANSFORMED - the caller's pipeline has them in
   the frequency domain anyway, and D+T forward transforms have no business
   inside a D*T loop.  Ingest here only rearranges: templates are conjugated, and
   both sides are stored in the layout stage A walks, which is what lets every
   one of the D*T pair transforms read sequentially.  That rearrangement is paid
   once per segment, so it stays amortised however many pairs run.

   Peaks for pair (d,t) land at peaks[((d-d0)*nt + (t-t0)) * nbins], dense and
   indexed by bin exactly as ap_binmax.  counts, if given, holds one crossing
   count per pair in the same order. */
typedef struct ap_mf_plan ap_mf_plan;

ap_mf_plan *ap_mf_create(size_t n, int ndata, int ntmpl);
ap_mf_plan *ap_mf_create_pairbatch(size_t n, int ndata, int ntmpl);
void        ap_mf_destroy(ap_mf_plan *p);
size_t      ap_mf_nbins(const ap_mf_plan *p, size_t binsize, size_t start, size_t end);

/* Ingest.  spec is the segment's SPECTRUM: n interleaved complex float32, the
   unnormalised forward transform of the segment, in natural frequency order.
   It is copied: the caller's buffer may be reused or freed once this returns.
   Returns 0, or -1 on error. */
int ap_mf_set_data    (ap_mf_plan *p, int d, const float *spec);
int ap_mf_set_template(ap_mf_plan *p, int t, const float *spec);

/* Run the pairs [d0,d0+nd) x [t0,t0+nt).  Any sub-block must give the same
   answer as the corresponding slice of the whole, which is what makes tiling
   safe to tune.  Returns total crossings, or -1. */
int ap_mf_run(ap_mf_plan *p, int d0, int nd, int t0, int nt,
              size_t binsize, float threshold,
              ap_peak *peaks, int *counts, size_t start, size_t end);
/* Full unnormalised circular correlation, interleaved complex float32 in
   natural lag order. out has nd*nt*n complex samples. */
int ap_mf_correlate(ap_mf_plan *p, int d0, int nd, int t0, int nt, float *out);
/* Gather and zero-pad each series block, then correlate it with the selected
   templates. out has nblocks*nt*n complex samples. */
int ap_mf_correlate_series(ap_mf_plan *p,
                           const float *series, size_t nseries,
                           const size_t *starts, int nblocks,
                           int t0, int nt, float *out);
/* Regular overlap-save layout: write only [lo,hi) from each block to the
   template-major continuous output, clipped to nseries. Other samples are
   untouched. The caller supplies disjoint block starts. bounds, if not NULL,
   gives each block its own [bounds[2b], bounds[2b+1]) inside [lo,hi) to write
   (the block is computed the same; only its copy-out is narrower). */
int ap_mf_correlate_series_continuous(ap_mf_plan *p,
                                      const float *series, size_t nseries,
                                      const size_t *starts, int nblocks,
                                      size_t lo, size_t hi, int t0, int nt,
                                      float *out, const size_t *bounds);
/* The same of a REAL float32 series of nseries samples: half-size block transforms split
   into the full spectrum (a real-real-complex hierarchy's middle stage). out is complex. */
int ap_mf_correlate_series_continuous_real(ap_mf_plan *p, const float *series,
                                           size_t nseries, const size_t *starts,
                                           int nblocks, size_t lo, size_t hi,
                                           int t0, int nt, float *out,
                                           const size_t *bounds);

/* Run a pooled list of (data, template) pairs.
   dsel[0..npairs) are data block indices relative to d0.
   tsel[0..npairs) are template indices relative to t0.
   peaks receives the result for each pair, placed at row = (dsel[i]*nt + tsel[i]).
   nt is the row stride in templates. */
int ap_mf_run_pairs_pooled(ap_mf_plan *p, int d0,
                           const int *dsel, const int *tsel, int npairs,
                           int t0, size_t binsize, float threshold,
                           ap_peak *peaks, int *counts, size_t start, size_t end,
                           int nt);

/* Q15 coarse screen.  ap_mf_q15_lanes: pairs per screen call for this plan's
   length on its own back end, 0 when there is no screen.  ap_mf_q15_screen:
   for the pairs [d0,d0+nd) x [t0,t0+nt), pass[(d-d0)*nt + t-t0] = 1 unless the
   pair's maximum over [start,end) certainly stays below `threshold` -- the
   pairs a float run at that threshold could report.  stat, if not NULL,
   receives the screen's estimate of each maximum.  Returns the number passed,
   or -1 when the plan has no screen. */
int ap_mf_q15_lanes(const ap_mf_plan *p);
/* With the margin (1, the default) the screen passes every pair whose float maximum can
   reach the threshold; without it (0) it decides on its own int16 maximum. */
int ap_mf_set_q15_margin(ap_mf_plan *p, int on);
/* The screen over a list of pairs (pair j: data d0+dsel[j], template t0+tsel[j]): pass[j]
   set when it can reach threshold over [start, end); stat[j] (may be NULL) its maximum in the
   float tier's units. Returns the passes, or -1. */
int ap_mf_q15_pairs(ap_mf_plan *p, int d0, const int *dsel, const int *tsel, int npairs,
                    int t0, float threshold, size_t start, size_t end, unsigned char *pass,
                    float *stat);
int ap_mf_q15_screen(ap_mf_plan *p, int d0, int nd, int t0, int nt, float threshold,
                     size_t start, size_t end, unsigned char *pass, float *stat);

/* Filter a time series over a caller-supplied block layout: block b covers
   series[start[b] ...] and reports lags [win_start[b], win_end[b]).  Windows
   are per block, so the ragged ones at a segment's edges need no grouping.

   Block b's bins are numbered from win_start[b] - bin_phase[b] (bin_phase NULL: from
   win_start[b], as ap_mf_run): bin j covers [win_start[b] - bin_phase[b] + j*binsize,
   ... + (j+1)*binsize) clipped to the window, so a bin wholly before win_start[b] is empty
   (a phase of a whole bin or more pads a block to its neighbours' bin count).
   A caller whose windows span several blocks gives each block the phase that puts its
   bins on the window's grid; a bin split between two blocks is then two partial bins,
   one in each, whose larger peak is the window bin's.

   peaks is [block][template][bin], every block with the same bin count (-1 otherwise).  A block whose
   transform would run past nseries is zero-padded.  Blocks sharing a window
   are filtered together, up to the plan's own ndata -- which is the grouping
   knob, there being no second one.  Returns total crossings, or -1. */
int ap_mf_run_series(ap_mf_plan *p,
                     const float *series, size_t nseries,
                     const size_t *start, const size_t *win_start,
                     const size_t *win_end, const unsigned *bin_phase, int nblocks,
                     int t0, int nt, size_t binsize, float threshold,
                     ap_peak *peaks, int *counts);
int ap_mf_run_series_dif(ap_mf_plan *p,
                         const float *series, size_t nseries,
                         const size_t *start, const size_t *win_start,
                         const size_t *win_end, const unsigned *bin_phase, int nblocks,
                         int t0, int nt, size_t binsize, float threshold,
                         int decimated,
                         ap_peak *peaks, int *counts);

/* Interpolated coarse maximum, alongside the peak scan.  hlo/hhi are complex
   taps (2*ntap floats each) for the two half-sample offsets, ncand is how many
   of the largest grid samples to probe, and out receives one value per pair in
   the same [nd][nt] order as ap_mf_run's peaks.  Pass a NULL tap pointer to
   turn it off.  See docs/hierarchical.md for why this brackets the second
   coarse transform rather than replacing it. */
/* ap_mf_set_interp and ap_mf_interp_pause are gone. Interpolation was
   removed with the U / oversample design; the plan state and the innermost
   loop block that used them were unreachable -- interpolation was never
   exposed to Python -- so the whole path went with them. */

/* Is this length supported?  1024, and the powers of two from 4096 to 2^20. */
/* ---------------------------------------------------------------------------
 * Hierarchical matched filter.
 *
 * Most of a template's signal-to-noise sits in the low part of the band.  This
 * filter correlates only that part, on a coarse lag grid, and pays for the full
 * correlation only where the coarse result could plausibly become a detection.
 *
 * Surviving pairs normally receive a full correlation and binned peak search.
 * Equivalent transform paths can differ by floating-point rounding. The gate
 * can omit peaks; its false-dismissal target is supplied by the caller's model.
 * With direct refinement enabled, a single-bin result is the maximum near the
 * last coarse candidate, which can differ from the whole bin's maximum when
 * several excursions occur. Use ap_mf_run for an ungated full-bin search.
 *
 * The caller supplies the chain of bands and one nonnegative threshold per
 * tier. The native engine derives no calibration; Python computes the
 * thresholds from the reference profile and the false-dismissal budget.
 */
typedef struct ap_hmf_plan ap_hmf_plan;

/* Gate chain: coarse tiers at strictly increasing bands, then the full refine.
 * Tier 0 filters every (block, template) pair; tier i only the pairs that
 * passed tier i-1; pairs passing the last tier are refined at full band.
 * A one-band chain is the classic single coarse gate. k = n/2 selects the
 * half-length (DIF) layout, 0 or n the full one. series_group bounds how
 * many blocks are filtered together (execution grouping only). */
#define AP_HMF_MAX_TIERS 8
ap_hmf_plan *ap_hmf_create_chain(size_t n, size_t k, int ndata, int ntmpl,
                                 const size_t *bands, int ntiers, int series_group);
/* One finite threshold per tier, in coarse-output units; a negative value
   marks the plan unconfigured and execution then fails. */
int ap_hmf_set_thresholds(ap_hmf_plan *p, const float *thr, int ntiers);
/* The thresholds in force (thr may be NULL); returns the number of tiers. */
int ap_hmf_thresholds(const ap_hmf_plan *p, float *thr);
/* The chain's bands (bands may be NULL); returns the number of tiers. */
int ap_hmf_chain(const ap_hmf_plan *p, size_t *bands);
/* Pairs that passed tier `tier` and the ticks spent in it; tier == ntiers is
   the refine (refined pairs, refine ticks). Always counted. */
int ap_hmf_tier_stats(const ap_hmf_plan *p, int tier, long *passed, unsigned long long *ticks);
/* Ticks spent in ap_hmf_run_series calls in total: with the tier counters this
   gives the per-block fixed work (forward transform, ingest) in the same units. */
unsigned long long ap_hmf_series_ticks(const ap_hmf_plan *p);
int ap_hmf_series_group(const ap_hmf_plan *p);
/* The series group a plan of size n would run when asked for `requested` (MF_DGROUP,
   then halved until its held spectra fit 4 MB): what ap_hmf_series_group reports. */
int ap_hmf_effective_group(size_t n, int requested);
/* Run the first tier as the Q15 screen (ap_mf_q15_screen, without its margin): a pair
   passes when its int16 maximum reaches the tier's threshold, and no float run of the
   tier follows.  The tier then answers to the chain's false-dismissal budget, as every
   tier does; survivors' peaks are still refined exactly.  Returns 0, or -1 when the
   first tier's band has no screen on this back end (the plan is then unchanged).
   0 turns it off. */
int ap_hmf_set_q15(ap_hmf_plan *p, int on);
/* Cumulative inputs per tier and passes of the first tier. */
int ap_hmf_tier_inputs(const ap_hmf_plan *p, long *checked);
long ap_hmf_first_gate_passed(const ap_hmf_plan *p);
/* The block forward through the platform FFT (macOS: vDSP) instead of the engine's; -1 where
   there is none. Results differ by fp32 rounding only. */
int ap_hmf_set_platform_fft(ap_hmf_plan *p, int on);
/* The continuous correlation (correlate_series_continuous) through the platform FFT. */
int ap_mf_set_platform_fft(ap_mf_plan *p, int on);
int ap_hmf_get_q15(const ap_hmf_plan *p);
/* Pairs the screen passed to the float first tier, and ticks spent screening. */
int ap_hmf_q15_stats(const ap_hmf_plan *p, long *passed, unsigned long long *ticks);
int ap_hmf_set_hermitian(ap_hmf_plan *p, int hermitian);
void         ap_hmf_destroy(ap_hmf_plan *p);

size_t ap_hmf_nbins(const ap_hmf_plan *p, size_t binsize, size_t start, size_t end);
/* Reference SNR distribution: expected power per bin of the filter OUTPUT,
 * length n, real, any scale.  Setting it is usually the right thing to do.
 *
 * By default each template's band fraction is computed
 * from the template itself, which assumes its own power distribution is the
 * distribution of the SNR it produces.  That holds only when the data is white
 * and the template is whitened.  It fails, for instance, when the template is a
 * broadband ratio filter whose output reconstructs a strongly low-frequency
 * signal: the coarse threshold would read the filter and be badly wrong.
 *
 * In practice the output distribution is a property of the SIGNAL, not of the
 * individual template, and is near-identical across a bank -- so supply it once
 * here rather than tuning per template.  Doing so also skips the per-template
 * measurement at ingest entirely.
 *
 * Pass NULL to use each template. Templates already set are scaled for the old
 * reference: they become stale, and a run over a stale template fails until it is
 * set again (no unscaled copy is kept to rescale them from). */
int    ap_hmf_set_reference(ap_hmf_plan *p, const float *power);
/* Ingest, as ap_mf_set_data: spec (n interleaved complex float32) is copied, so the
   caller's buffer may be reused or freed once this returns. */
int    ap_hmf_set_data    (ap_hmf_plan *p, int d, const float *spec);
int    ap_hmf_set_template(ap_hmf_plan *p, int t, const float *spec);

/* Same arguments and same output layout as ap_mf_run. */
int ap_hmf_run(ap_hmf_plan *p, int d0, int nd, int t0, int nt,
               size_t binsize, float threshold,
               ap_peak *peaks, int *counts, size_t start, size_t end);

/* Filter a time series directly, over a caller-supplied block layout.
 *
 * The caller still owns the overlap-save arithmetic: it decides where each
 * block starts and which span of each block's output is valid.  matchedfilter only
 * executes that plan -- forward transform per block, gate, refine where needed
 * -- which removes the per-block round trip through the caller entirely: no
 * separately-planned forward FFT, no spectrum handed back and forth, and one
 * call per segment instead of one per block.
 *
 * series holds `nseries` complex samples, interleaved.  For block b, the
 * transform covers series[start[b] .. start[b]+n), and the peak search covers
 * lags [win_start[b], win_end[b]) within that block.  Windows are per block, so
 * the ragged ones at a segment's edges need no special handling.
 *
 * Block b's bins are numbered from win_start[b] - bin_phase[b], as ap_mf_run_series.
 *
 * peaks is [block][template][bin] with bins as ap_hmf_run.  A block whose
 * transform would run past nseries is zero-padded.
 */
int ap_hmf_run_series(ap_hmf_plan *p,
                      const float *series, size_t nseries,
                      const size_t *start, const size_t *win_start,
                      const size_t *win_end, const unsigned *bin_phase, int nblocks,
                      int t0, int nt, size_t binsize, float threshold,
                      ap_peak *peaks, int *counts);

/* Real series for ap_hmf_run_series (on != 0): series then holds nseries REAL samples (the
   middle output of a real-real-complex hierarchy, filtered with complex quadrature
   templates), each block is transformed at half size into its full Hermitian spectrum, and
   refines are by transform. Fails (-1) where n/2 has no transform. */
int ap_hmf_set_real_series(ap_hmf_plan *p, int on);
/* Floats between a real series' samples: 1, or 2 to read one lane (real or imaginary part)
   of a complex series in place -- a packed pair of real series. nseries counts samples. */
int ap_hmf_set_real_stride(ap_hmf_plan *p, size_t stride);

/* Sparse output for ap_hmf_run / ap_hmf_run_series (on != 0, counts required): a row
   whose pair no tier passes gets counts[row] = 0 and its peaks are NOT written, so the
   caller reads peaks only where counts[row] > 0. At a detection threshold almost every
   pair is such a row; writing an empty peak into each was a pass over the whole table. */
int ap_hmf_set_sparse(ap_hmf_plan *p, int on);

/* Direct refine. ap_hmf_set_taps gives each template's real FIR taps (row t: counts[t]
   taps, stride floats per row, centre tap counts[t]/2 at lag 0 -- the filter whose
   spectrum ap_hmf_set_template holds). With ap_hmf_set_direct on, ap_hmf_run_series
   refines a survivor only at the lags within `halfwidth` last-tier coarse samples of a
   last-tier lag at or above that tier's threshold, by direct correlation, wherever that is
   priced cheaper than its whole-block transform (both timed on this core when turned on);
   the rest, and every ap_hmf_run call, refine by transform as before. */
int ap_hmf_set_taps(ap_hmf_plan *p, const float *taps, size_t stride, const int64_t *counts);
int ap_hmf_set_direct(ap_hmf_plan *p, int on, int halfwidth);
/* Ticks per lag x tap of the direct correlation on this core (< 0 on failure). */
double ap_hmf_price_direct(void);
/* The two prices a survivor's direct-or-transform choice compares, timed on this plan's
   kernels: ticks per lag x tap of the direct correlation and per pair of the whole-block
   refine. ap_hmf_set_direct_prices gives a plan prices measured once (a plan otherwise
   times its own when the direct refine is turned on): plans of one size and kernel then
   decide every pair alike, whatever each would have timed. */
int ap_hmf_price_direct_pair(ap_hmf_plan *p, double *ticks_per_lag_tap, double *ticks_per_fft_pair);
int ap_hmf_set_direct_prices(ap_hmf_plan *p, double ticks_per_lag_tap, double ticks_per_fft_pair);
int ap_hmf_direct_stats(const ap_hmf_plan *p, long *pairs, long *lags, long *fft,
                        double *ticks_per_lag_tap, double *ticks_per_fft_pair);

/* Diagnostics: pairs examined and pairs that went to the full correlation.
   The ratio is the measured refine rate, which is what the speedup rides on. */
void ap_hmf_stats(const ap_hmf_plan *p, long *pairs, long *refined);

int ap_supported(size_t n);

/* The root stage of a hierarchical search (docs/hierarchical-search-design.md): one
   transformed input block D against one root filter T, both one-sided spectra of
   nbins >= n/2 + 1 bins (interleaved complex), to the real n-point series
       out = scale * C2R(P),  P[k] = conj(T[k]) D[k] for k0 <= k < k1, 0 otherwise,
   with C2R the unnormalised complex-to-real transform (imaginary parts of P[0] and P[n/2]
   ignored), i.e. twice the real part of the analytic series. n is a power of two, at least
   128. A plan holds its own workspace: one plan per thread. */
typedef struct ap_root ap_root;
ap_root *ap_root_create(size_t n);
void ap_root_destroy(ap_root *r);
size_t ap_root_length(const ap_root *r);
int ap_root_real(ap_root *r, const float *D, const float *T, size_t nbins,
                 size_t k0, size_t k1, float scale, float *out);

/* Which back end the CPU selected: "avx512", "avx2", or "unsupported". */
const char *ap_isa(void);

#ifdef __cplusplus
}
#endif
#endif
