/* One pass of the shared-screener merging (gatechain.cluster_tier0_candidates): every
 * candidate merge of two clusters turned into a group of templates with one screener, or
 * turned down.
 *
 * The templates are C (nt, K) complex128 over a band of K bins, with weights w of the inner
 * product <a, b> = sum_k w[k] conj(a[k]) b[k], variances v and 1 / sqrt(v); a lag d turns a
 * vector by exp_all[d + R] (K unit phases), |d| <= R. The clusters of the level being merged
 * are cur (nc, K), their members cur_members[cur_offsets[c] : cur_offsets[c + 1]]. Candidate
 * g merges clusters ca[g] and cb[g], the second lagged cdl[g] against the first. For each:
 *
 *   1. Its members are the two clusters', sorted. It is turned down if the smallest member
 *      variance is under 0.80 of the largest.
 *   2. The frame the members are aligned in is the two clusters' unit vectors added in
 *      phase (the second at its lag), normalised.
 *   3. Each member's lag against that frame: the best of the coarse shifts (float32), then
 *      the best lag within half_span of it (ap_tier0_refine_lags, complex128).
 *   4. The screener of the members at those lags (ap_tier0_mwu), scaled to the members' mean
 *      variance; a member's retention is its overlap with it times sqrt(mean variance / its
 *      own), at most 1. The group is accepted if every retention reaches alpha_floor.
 *
 * This is the numpy code it replaced, operation for operation in double precision: sums
 * over the band run as numpy's do (its pairwise sum, or one after another where it used
 * einsum), a complex number over a real one is multiplied by the real's reciprocal, and a
 * modulus is hi sqrt(1 + (lo / hi)^2) with a fused 1 + q^2, numpy's own on AVX-512 (it is
 * hypot() elsewhere, so numpy's results differed between machines in the last place; these
 * do not). The float32 coarse shift sums run bin after bin where numpy called BLAS: two
 * shifts equal to rounding can order the other way, and the refinement that follows usually
 * lands on the same lag. Built with floating-point contraction off (setup.py). */
#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <algorithm>
#include <vector>

extern "C" void ap_tier0_refine_lags(const double *prod_ab, const double *exp_all,
                                     const int64_t *pdl, long long npairs, long long len,
                                     long long R, long long half_span, int64_t *out_dl,
                                     double *out_g);
extern "C" int ap_tier0_mwu(const double *u, const double *ref, const double *w, long long nb,
                            long long m, long long K, int steps, double *c_out,
                            double *ov_out);

namespace {

struct Cx { double r, i; };
// numpy's complex product, and a real factor as the complex number it is promoted to
inline Cx mul(Cx a, Cx b) { return Cx{a.r * b.r - a.i * b.i, a.r * b.i + a.i * b.r}; }
inline Cx real(double x) { return Cx{x, 0.0}; }
// numpy's complex over real: by the real's reciprocal
inline Cx over(Cx a, double x) {
  const double rat = 0.0 / x, scl = 1.0 / (x + 0.0 * rat);
  return Cx{(a.r + a.i * rat) * scl, (a.i - a.r * rat) * scl};
}
// numpy's modulus (AVX-512 loop)
inline double modulus(Cx a) {
  const double x = fabs(a.r), y = fabs(a.i), hi = x > y ? x : y, lo = x > y ? y : x;
  if (hi == 0.0) return 0.0;
  const double q = lo / hi;
  return hi * sqrt(fma(q, q, 1.0));
}
inline float modulusf(float re, float im) {
  const float x = fabsf(re), y = fabsf(im), hi = x > y ? x : y, lo = x > y ? y : x;
  if (hi == 0.0f) return 0.0f;
  const float q = lo / hi;
  return hi * sqrtf(fmaf(q, q, 1.0f));
}
// numpy's sum of n doubles (pairwise_sum in loops_utils.h)
double pairwise(const double *a, long long n) {
  if (n < 8) {
    double res = 0.0;
    for (long long i = 0; i < n; i++) res += a[i];
    return res;
  }
  if (n <= 128) {
    double r[8];
    for (int j = 0; j < 8; j++) r[j] = a[j];
    long long i = 8;
    for (; i < n - (n % 8); i += 8)
      for (int j = 0; j < 8; j++) r[j] += a[i + j];
    double res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
    for (; i < n; i++) res += a[i];
    return res;
  }
  long long n2 = n / 2;
  n2 -= n2 % 8;
  return pairwise(a, n2) + pairwise(a + n2, n - n2);
}

}  // namespace

/* accepted (ncand): 1 for a group that is accepted. members, alpha (the candidates' member
   counts summed) and offsets (ncand + 1): every candidate's sorted members and, for an
   accepted one, their retentions. screener (ncand, K) complex128, v_bar and reach (ncand),
   written for the accepted: the group's screener, its mean variance and its largest member
   lag in absolute value. shifts (nsh, K) complex64 are the coarse shifts and shift_lags
   their lags. Returns the number accepted, or -1 when out of memory. */
extern "C" long long ap_tier0_pass(
    const double *C, const double *inv_sqrt_v, const double *v, const double *w,
    const double *exp_all, const float *shifts, const int64_t *shift_lags, long long K,
    long long R, long long nsh, long long half_span, const double *cur,
    const double *inv_sqrt_vc, const int32_t *cur_offsets, const int32_t *cur_members,
    const int64_t *ca, const int64_t *cb, const int64_t *cdl, long long ncand, int steps,
    double alpha_floor, uint8_t *accepted, double *screener, double *v_bar, int64_t *reach,
    int32_t *members, int32_t *offsets, double *alpha) try {
  const Cx *Cz = (const Cx *)C, *ex = (const Cx *)exp_all, *cz = (const Cx *)cur;
  // 1. every candidate's members, sorted; those whose variances are compatible go on
  std::vector<long long> kept;
  long long total = 0, kept_members = 0;
  offsets[0] = 0;
  for (long long g = 0; g < ncand; g++) {
    int32_t *mem = members + total;
    long long m = 0;
    for (const int64_t c : {ca[g], cb[g]})
      for (int32_t p = cur_offsets[c]; p < cur_offsets[c + 1]; p++) mem[m++] = cur_members[p];
    std::sort(mem, mem + m);
    total += m;
    offsets[g + 1] = (int32_t)total;
    accepted[g] = 0;
    double lo = v[mem[0]], hi = lo;
    for (long long j = 1; j < m; j++) {
      lo = v[mem[j]] < lo ? v[mem[j]] : lo;
      hi = v[mem[j]] > hi ? v[mem[j]] : hi;
    }
    if (lo < 0.80 * hi) continue;
    kept.push_back(g);
    kept_members += m;
  }
  if (kept.empty()) return 0;
  const long long nk = (long long)kept.size();
  std::vector<Cx> frame((size_t)(nk * K));          // each kept group's frame
  std::vector<Cx> unit((size_t)(kept_members * K)); // each member over sqrt(its variance)
  std::vector<Cx> prod((size_t)(kept_members * K)); // w conj(frame) member
  std::vector<int64_t> lag((size_t)kept_members), fine((size_t)kept_members);
  std::vector<Cx> ua((size_t)K), ub((size_t)K);
  std::vector<double> power((size_t)K);
  long long row = 0;
  for (long long q = 0; q < nk; q++) {
    const long long g = kept[q];
    // 2. the frame: the two clusters' unit vectors added in phase, normalised
    const Cx *a = cz + ca[g] * K, *b = cz + cb[g] * K;
    const double sa = inv_sqrt_vc[ca[g]], sb = inv_sqrt_vc[cb[g]];
    const int64_t d = cdl[g] < -R ? -R : (cdl[g] > R ? R : cdl[g]);
    const Cx *turn = ex + (d + R) * K;
    Cx ip{0.0, 0.0};
    for (long long k = 0; k < K; k++) {
      ua[k] = mul(a[k], real(sa));
      ub[k] = mul(mul(b[k], real(sb)), turn[k]);
      const Cx t = mul(mul(real(w[k]), Cx{ua[k].r, -ua[k].i}), ub[k]);
      ip.r += t.r;
      ip.i += t.i;
    }
    const double size = modulus(ip);
    const Cx phase = size > 1e-12 ? over(Cx{ip.r, -ip.i}, size > 1e-12 ? size : 1e-12)
                                  : Cx{1.0, 0.0};
    Cx *f = frame.data() + q * K;
    for (long long k = 0; k < K; k++) {
      const Cx t = mul(phase, ub[k]);
      f[k] = Cx{ua[k].r + t.r, ua[k].i + t.i};
      power[k] = (f[k].r * f[k].r + f[k].i * f[k].i) * w[k];
    }
    const double sum = 0.0 + pairwise(power.data(), K);
    const double norm = sqrt(sum > 1e-30 ? sum : 1e-30);
    for (long long k = 0; k < K; k++) f[k] = over(f[k], norm);
    // 3. each member against the frame, and the best coarse shift
    for (int32_t p = offsets[g]; p < offsets[g + 1]; p++, row++) {
      const int32_t t = members[p];
      const Cx *ct = Cz + (long long)t * K;
      Cx *un = unit.data() + row * K, *pr = prod.data() + row * K;
      for (long long k = 0; k < K; k++) {
        un[k] = mul(ct[k], real(inv_sqrt_v[t]));
        pr[k] = mul(mul(real(w[k]), Cx{f[k].r, -f[k].i}), un[k]);
      }
      float best = -1.0f;
      long long at = 0;
      for (long long s = 0; s < nsh; s++) {
        const float *sh = shifts + 2 * s * K;
        float re = 0.0f, im = 0.0f;
        for (long long k = 0; k < K; k++) {
          const float xr = (float)pr[k].r, xi = (float)pr[k].i;
          re += xr * sh[2 * k] - xi * sh[2 * k + 1];
          im += xr * sh[2 * k + 1] + xi * sh[2 * k];
        }
        const float mag = modulusf(re, im);
        if (mag > best) { best = mag; at = s; }
      }
      lag[row] = shift_lags[at];
    }
  }
  // the best lag within half_span of each coarse one
  if (half_span > 0) {
    ap_tier0_refine_lags((const double *)prod.data(), exp_all, lag.data(), kept_members, K, R,
                         half_span, fine.data(), nullptr);
    lag.swap(fine);
  }
  // 4. the groups of one size are synthesised together
  long long largest = 0;
  for (const long long g : kept) largest = std::max<long long>(largest, offsets[g + 1] - offsets[g]);
  std::vector<long long> first((size_t)nk);            // a kept group's first row
  for (long long q = 0, at = 0; q < nk; q++) {
    first[q] = at;
    at += offsets[kept[q] + 1] - offsets[kept[q]];
  }
  std::vector<Cx> turned, refs, made;
  std::vector<double> overlap, vm;
  std::vector<long long> bucket;
  long long count = 0;
  for (long long m = 2; m <= largest; m++) {
    bucket.clear();
    for (long long q = 0; q < nk; q++)
      if (offsets[kept[q] + 1] - offsets[kept[q]] == m) bucket.push_back(q);
    if (bucket.empty()) continue;
    const long long nb = (long long)bucket.size();
    turned.resize((size_t)(nb * m * K));
    refs.resize((size_t)(nb * K));
    made.resize((size_t)(nb * K));
    overlap.resize((size_t)(nb * m));
    vm.resize((size_t)m);
    for (long long x = 0; x < nb; x++) {
      const long long q = bucket[x];
      memcpy(refs.data() + x * K, frame.data() + q * K, (size_t)K * sizeof(Cx));
      for (long long j = 0; j < m; j++) {
        const Cx *un = unit.data() + (first[q] + j) * K;
        const Cx *turn = ex + (lag[first[q] + j] + R) * K;
        Cx *out = turned.data() + (x * m + j) * K;
        for (long long k = 0; k < K; k++) out[k] = mul(un[k], turn[k]);
      }
    }
    if (ap_tier0_mwu((const double *)turned.data(), (const double *)refs.data(), w, nb, m, K,
                     steps, (double *)made.data(), overlap.data()) != 0)
      return -1;
    for (long long x = 0; x < nb; x++) {
      const long long q = bucket[x], g = kept[q];
      const int32_t *mem = members + offsets[g];
      for (long long j = 0; j < m; j++) vm[j] = v[mem[j]];
      const double mean = (0.0 + pairwise(vm.data(), m)) / (double)m;
      double least = HUGE_VAL;
      int64_t far = 0;
      for (long long j = 0; j < m; j++) {
        const double keep = sqrt(mean / vm[j]) * overlap[x * m + j];
        const double al = keep < 1.0 ? keep : 1.0;
        alpha[offsets[g] + j] = al;
        least = al < least ? al : least;
        const int64_t dj = lag[first[q] + j] < 0 ? -lag[first[q] + j] : lag[first[q] + j];
        far = dj > far ? dj : far;
      }
      if (!(least >= alpha_floor)) continue;
      accepted[g] = 1;
      count++;
      v_bar[g] = mean;
      reach[g] = far;
      const double scale = sqrt(mean);
      const Cx *c = made.data() + x * K;
      Cx *out = (Cx *)screener + g * K;
      for (long long k = 0; k < K; k++) out[k] = mul(real(scale), c[k]);
    }
  }
  return count;
} catch (const std::bad_alloc &) {
  return -1;
}
