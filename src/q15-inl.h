/* Q15 coarse screen: the pair-batched coarse transform in int16 fixed point.
 *
 * What it computes.  For QW (data, template) pairs at once -- lanes are
 * templates, twice as many as the float path's at the same vector width --
 * the conjugated four-step transform conj(Z_k) = sum_j (d_j * t_j) exp(+2*pi*i*j*k/N)
 * (preserving every lag index k and magnitude |Z_k|^2 of the float pair path,
 * while forming d*t directly from (dr, di) without a negated -di data stream),
 * then for every lane the largest |z|^2 over the window, as
 * round(re^2/2^15) + round(im^2/2^15), saturating.  It reports no peak: the caller
 * compares the maximum against the tier threshold LOWERED by an error margin and
 * re-runs the float tier on every pair that clears it, so the screen decides
 * only which pairs need the float answer (matchfilt.c, hmf.c).
 *
 * Range.  Nothing inside the transform rescales.  Every intermediate of an
 * FFT is a partial sum of products with unit-modulus weights, so its
 * magnitude is at most L1 = sum_k |p_k| plus accumulated rounding; the caller
 * quantises the inputs so that sum_k |d_k||t_k| / 2^15 (Cauchy-Schwarz:
 * <= |d|_2 |t|_2 / 2^15) stays at Q15_L1 (q15.h), leaving the rest of the
 * int16 range as headroom for rounding. The codelets multiply each component
 * by its constant before adding (re*c + im*c, never (re + im)*c, whose sum
 * could reach sqrt(2) L1), so no intermediate leaves the int16 range and the
 * transform's adds wrap: on the contract's inputs they equal saturating adds
 * bit for bit (tools/gate_margin.py --gate q15, every family and N, gives the
 * same output either way) and cost ~5% less of the screen on Zen 5. The final
 * re^2 + im^2, which can exceed int16 by itself, still saturates.
 *
 * Error.  Each Q_MUL rounds to nearest; the error at the output is a sum of
 * those roundings over the transform -- the per-N margin in q15.h is set from
 * its measured distribution (docs/cpu-q15-gate.md).
 */
#include "q15.h"
#include "simd-inl.h"

#ifndef AP_Q15_TW32_ONCE_
#define AP_Q15_TW32_ONCE_
namespace ap {
/* Duplicated int16->int32 four-step twiddle table (w | (w << 16)): broadcasting 32-bit
   dwords emits vpbroadcastd (one pure load uop on Haswell/Broadwell, zero Port-5 shuffle
   uops) instead of vpbroadcastw (load + Port-5 shuffle). */
struct q15_twiddles32 { int32_t re[1024], im[1024]; };
static q15_twiddles32 q15_tw32_tab[5];
static pthread_once_t q15_tw32_once = PTHREAD_ONCE_INIT;
static int q15_tw32_ready = 0;

static void q15_tw32_build(void){
  (void)ap_q15_twiddle_table(64);
  for(int i = 0; i < 5; i++){
    for(int j = 0; j < 1024; j++){
      const uint32_t r = (uint16_t)ap_q15_tw_tab[i].re[j];
      const uint32_t m = (uint16_t)ap_q15_tw_tab[i].im[j];
      q15_tw32_tab[i].re[j] = (int32_t)(r | (r << 16));
      q15_tw32_tab[i].im[j] = (int32_t)(m | (m << 16));
    }
  }
}

static HWY_NOINLINE void q15_tw32_init_slow(void){
  pthread_once(&q15_tw32_once, q15_tw32_build);
  __atomic_store_n(&q15_tw32_ready, 1, __ATOMIC_RELEASE);
}
}  // namespace ap
#endif

#if defined(AP_Q15_INL_H_) == defined(HWY_TARGET_TOGGLE)
#ifdef AP_Q15_INL_H_
#undef AP_Q15_INL_H_
#else
#define AP_Q15_INL_H_
#endif

HWY_BEFORE_NAMESPACE();
namespace ap {
namespace HWY_NAMESPACE {

using ap_qtag = hn::CappedTag<int16_t, 2 * AP_W>;
using ap_qditag = hn::Repartition<int32_t, ap_qtag>;
constexpr ap_qtag AP_DQ{};
constexpr ap_qditag AP_QDI{};
constexpr int AP_QW = (int)HWY_MAX_LANES_D(ap_qtag);
typedef hn::Vec<ap_qtag> vq;

#undef Q_ZERO
#undef Q_SET1
#undef Q_DUP32
#undef Q_TWLOAD
#undef Q_LOADU
#undef Q_ADD
#undef Q_SUB
#undef Q_MUL
#define Q_ZERO()       hn::Zero(AP_DQ)
#define Q_SET1(x)      hn::Set(AP_DQ, (int16_t)(x))
#define Q_DUP32(x)     hn::BitCast(AP_DQ, hn::Set(AP_QDI, (int32_t)(x)))
#define Q_LOADU(p)     hn::LoadU(AP_DQ, (const int16_t *)(p))
#define Q_ADD(a, b)    hn::Add((a), (b))
#define Q_SUB(a, b)    hn::Sub((a), (b))
#define Q_MUL(a, b)    hn::MulFixedPoint15((a), (b))
#if HWY_ARCH_X86 && HWY_MAX_BYTES == 32
typedef int32_t qtw_elem;
typedef q15_twiddles32 qtw_table;
#define Q_TWLOAD(x)    Q_DUP32(x)
#else
typedef int16_t qtw_elem;
typedef ap_q15_twiddles qtw_table;
#define Q_TWLOAD(x)    Q_SET1(x)
#endif

/* Listed pairs (q15_screen_perm): each lane's operands are looked up in a vector of one element
   across QW data blocks (dix) and across two groups of QW templates (tix, the second group TW
   further on). On AVX2, precomputed vpshufb byte masks replace Highway's multi-instruction
   cross-lane int16 table lookup inside every codelet load. */
#undef Q_DLOAD
#undef Q_TLOAD
#if HWY_TARGET == HWY_AVX2
struct ap_qidx_avx2 { __m256i s0, s1, s2, s3; };
typedef const ap_qidx_avx2 *qidx;
static HWY_INLINE void q15_make_dix_avx2(ap_qidx_avx2 *out, const int16_t *dsel){
  alignas(32) uint8_t b0[32], b1[32];
  for(int l = 0; l < 16; l++){
    const int h = l >> 3, idx = dsel[l] & 15, sh = idx >> 3;
    const uint8_t lo = (uint8_t)(2 * (idx & 7)), hi = (uint8_t)(lo + 1);
    if(sh == h){ b0[2 * l] = lo; b0[2 * l + 1] = hi; b1[2 * l] = 0x80; b1[2 * l + 1] = 0x80; }
    else       { b0[2 * l] = 0x80; b0[2 * l + 1] = 0x80; b1[2 * l] = lo; b1[2 * l + 1] = hi; }
  }
  out->s0 = _mm256_load_si256((const __m256i *)b0);
  out->s1 = _mm256_load_si256((const __m256i *)b1);
}
static HWY_INLINE void q15_make_tix_avx2(ap_qidx_avx2 *out, const int16_t *tsel, long TW){
  alignas(32) uint8_t b0[32], b1[32], b2[32], b3[32];
  memset(b0, 0x80, 32); memset(b1, 0x80, 32);
  memset(b2, 0x80, 32); memset(b3, 0x80, 32);
  for(int l = 0; l < 16; l++){
    const int h = l >> 3, raw = tsel[l] & 31;
    const int idx = TW ? raw : (raw & 15);
    const int g = idx >> 4, sh = (idx >> 3) & 1;
    const uint8_t lo = (uint8_t)(2 * (idx & 7)), hi = (uint8_t)(lo + 1);
    if(g == 0){
      if(sh == h){ b0[2 * l] = lo; b0[2 * l + 1] = hi; }
      else       { b1[2 * l] = lo; b1[2 * l + 1] = hi; }
    } else {
      if(sh == h){ b2[2 * l] = lo; b2[2 * l + 1] = hi; }
      else       { b3[2 * l] = lo; b3[2 * l + 1] = hi; }
    }
  }
  out->s0 = _mm256_load_si256((const __m256i *)b0);
  out->s1 = _mm256_load_si256((const __m256i *)b1);
  out->s2 = _mm256_load_si256((const __m256i *)b2);
  out->s3 = _mm256_load_si256((const __m256i *)b3);
}
static HWY_INLINE vq q15_dload_avx2(const int16_t *p, const ap_qidx_avx2 *ix){
  const __m256i v = _mm256_loadu_si256((const __m256i *)p);
  const __m256i vs = _mm256_permute4x64_epi64(v, 0x4E);
  return vq{_mm256_or_si256(_mm256_shuffle_epi8(v, ix->s0), _mm256_shuffle_epi8(vs, ix->s1))};
}
static HWY_INLINE vq q15_tload_avx2(const int16_t *p, long TW, const ap_qidx_avx2 *ix){
  const __m256i v0 = _mm256_loadu_si256((const __m256i *)p);
  const __m256i v0s = _mm256_permute4x64_epi64(v0, 0x4E);
  const __m256i v1 = _mm256_loadu_si256((const __m256i *)(p + TW));
  const __m256i v1s = _mm256_permute4x64_epi64(v1, 0x4E);
  const __m256i a = _mm256_or_si256(_mm256_shuffle_epi8(v0, ix->s0), _mm256_shuffle_epi8(v0s, ix->s1));
  const __m256i b = _mm256_or_si256(_mm256_shuffle_epi8(v1, ix->s2), _mm256_shuffle_epi8(v1s, ix->s3));
  return vq{_mm256_or_si256(a, b)};
}
#define Q_DLOAD(p) q15_dload_avx2((p), dix)
#define Q_TLOAD(p) q15_tload_avx2((p), TW, tix)
#else
typedef hn::IndicesFromD<ap_qtag> qidx;
#define Q_DLOAD(p) hn::TableLookupLanes(Q_LOADU(p), dix)
#define Q_TLOAD(p) hn::TwoTablesLookupLanes(AP_DQ, Q_LOADU(p), Q_LOADU((p) + TW), tix)
#endif

/* acc +- round(a*b / 2^15): AArch64 SQRDMLAH/SQRDMLSH (FEAT_RDM, every Apple core) in one
   instruction. acc is an integer, so rounding the sum rounds the product: Q_MLAH equals
   Q_ADD(acc, Q_MUL(a, b)) except where Q_MUL alone saturates (a = b = -32768, outside the
   screen's input range). Q_MLSH rounds -a*b/2^15 to nearest, so an exact tie goes the
   other way from Q_SUB(acc, Q_MUL(a, b)): still within 1/2 LSB, the per-multiply error the
   screen's margin is built on (q15.h). */
#undef AP_Q15_FUSED
#undef Q_MLAH
#undef Q_MLSH
#if HWY_ARCH_ARM_A64 && defined(__ARM_FEATURE_QRDMX) && \
    (HWY_TARGET == HWY_NEON || HWY_TARGET == HWY_NEON_BF16 || HWY_TARGET == HWY_NEON_WITHOUT_AES)
static_assert(HWY_MAX_LANES_D(ap_qtag) == 8, "Q_MLAH assumes a full 128-bit int16 vector");
#define AP_Q15_FUSED 1
#define Q_MLAH(acc, a, b) vq{vqrdmlahq_s16((acc).raw, (a).raw, (b).raw)}
#define Q_MLSH(acc, a, b) vq{vqrdmlshq_s16((acc).raw, (a).raw, (b).raw)}
#else
#define AP_Q15_FUSED 0
#define Q_MLAH(acc, a, b) Q_ADD((acc), Q_MUL((a), (b)))
#define Q_MLSH(acc, a, b) Q_SUB((acc), Q_MUL((a), (b)))
#endif

/* Tail tiles retain each lane's arithmetic and quantised operands. Only the
   product loads change: T templates are repeated for QW/T independent blocks
   (block b's data at + B*b int16s: B = 3*N, even for every supported N). */
#undef AP_Q15_TAIL
#if HWY_ARCH_X86 && HWY_MAX_BYTES == 32 && HWY_TARGET <= HWY_AVX2
/* AVX2, 16 lanes: T = 8 (two blocks) or 4 (four blocks). */
#define AP_Q15_TAIL 1
template<int T> static HWY_INLINE vq q15_tile_template(const int16_t *p){
  if(T == 8) return vq{_mm256_broadcastsi128_si256(_mm_loadu_si128((const __m128i *)p))};
  int64_t v;
  memcpy(&v, p, sizeof v);
  return vq{_mm256_set1_epi64x(v)};
}
template<int T, long B> static HWY_INLINE vq q15_tile_data32(const int32_t *p){
  constexpr long HB = B / 2;
  if(T == 8) return vq{_mm256_set_m128i(_mm_set1_epi32(p[HB]), _mm_set1_epi32(p[0]))};
  return vq{_mm256_setr_epi32(p[0], p[0], p[HB], p[HB],
                              p[2 * HB], p[2 * HB], p[3 * HB], p[3 * HB])};
}
template<int T, long B> static HWY_INLINE vq q15_tile_data16(const int16_t *p){
  if(T == 8) return vq{_mm256_set_m128i(_mm_set1_epi16(p[B]), _mm_set1_epi16(p[0]))};
  const int32_t d0 = (int32_t)((uint32_t)(uint16_t)p[0] * 0x00010001u);
  const int32_t d1 = (int32_t)((uint32_t)(uint16_t)p[B] * 0x00010001u);
  const int32_t d2 = (int32_t)((uint32_t)(uint16_t)p[2 * B] * 0x00010001u);
  const int32_t d3 = (int32_t)((uint32_t)(uint16_t)p[3 * B] * 0x00010001u);
  return vq{_mm256_setr_epi32(d0, d0, d1, d1, d2, d2, d3, d3)};
}
#elif HWY_ARCH_X86 && HWY_MAX_BYTES == 64
#define AP_Q15_TAIL 1
template<int T> static HWY_INLINE vq q15_tile_template(const int16_t *p){
  if(T == 8) return hn::LoadDup128(AP_DQ, p);
  return vq{_mm512_broadcast_i64x4(_mm256_loadu_si256((const __m256i *)p))};
}
template<int T, long B> static HWY_INLINE vq q15_tile_data32(const int32_t *p){
  constexpr long HB = B / 2;
  if(T == 16) return vq{_mm512_inserti64x4(_mm512_castsi256_si512(_mm256_set1_epi32(p[0])),
                                           _mm256_set1_epi32(p[HB]), 1)};
  __m512i v = _mm512_set1_epi32(p[0]);
  v = _mm512_mask_set1_epi32(v, 0x00f0u, p[HB]);
  v = _mm512_mask_set1_epi32(v, 0x0f00u, p[2 * HB]);
  return vq{_mm512_mask_set1_epi32(v, 0xf000u, p[3 * HB])};
}
template<int T, long B> static HWY_INLINE vq q15_tile_data16(const int16_t *p){
  if(T == 16) return vq{_mm512_inserti64x4(_mm512_castsi256_si512(_mm256_set1_epi16(p[0])),
                                           _mm256_set1_epi16(p[B]), 1)};
  __m512i v = _mm512_set1_epi16(p[0]);
  v = _mm512_mask_set1_epi16(v, 0x0000ff00u, p[B]);
  v = _mm512_mask_set1_epi16(v, 0x00ff0000u, p[2 * B]);
  return vq{_mm512_mask_set1_epi16(v, 0xff000000u, p[3 * B])};
}
#else
#define AP_Q15_TAIL 0
#endif

}  // namespace HWY_NAMESPACE
}  // namespace ap
HWY_AFTER_NAMESPACE();

#include "codelets-q15-inl.h"

HWY_BEFORE_NAMESPACE();
namespace ap {
namespace HWY_NAMESPACE {

static HWY_INLINE void qcodelet(int m, vq *restrict ar, vq *restrict ai, long S){
  switch(m){
    case  8: qsr8 (ar,ai,S); return;
    case 16: qsr16(ar,ai,S); return;
    default: qsr32(ar,ai,S); return;
  }
}
static HWY_INLINE void qcodelet_prod(int m, const int32_t *restrict dr, const int16_t *restrict di,
                                     const int16_t *restrict tr, const int16_t *restrict ti,
                                     vq *restrict ar, vq *restrict ai, long S, long DS, long TS){
  switch(m){
    case  8: qsr8_prod (dr,di,tr,ti,ar,ai,S,DS,TS); return;
    case 16: qsr16_prod(dr,di,tr,ti,ar,ai,S,DS,TS); return;
    default: qsr32_prod(dr,di,tr,ti,ar,ai,S,DS,TS); return;
  }
}
static HWY_INLINE void qcodelet_prod_perm(int m, const int16_t *restrict dr,
                                          const int16_t *restrict di, const int16_t *restrict tr,
                                          const int16_t *restrict ti, vq *restrict ar,
                                          vq *restrict ai, long S, long TS, long TW,
                                          const qidx dix, const qidx tix){
  switch(m){
    case  8: qsr8_prod_perm (dr,di,tr,ti,ar,ai,S,TS,TW,dix,tix); return;
    case 16: qsr16_prod_perm(dr,di,tr,ti,ar,ai,S,TS,TW,dix,tix); return;
    default: qsr32_prod_perm(dr,di,tr,ti,ar,ai,S,TS,TW,dix,tix); return;
  }
}
static HWY_INLINE void qcodelet_tw(int m, vq *restrict ar, vq *restrict ai, long S,
                                   const qtw_elem *restrict twr, const qtw_elem *restrict twi){
  switch(m){
    case  8: qsr8_tw (ar,ai,S,twr,twi); return;
    case 16: qsr16_tw(ar,ai,S,twr,twi); return;
    default: qsr32_tw(ar,ai,S,twr,twi); return;
  }
}
static HWY_INLINE void qcodelet_twmax(int m, const vq *restrict ar, const vq *restrict ai, long S,
                                      const qtw_elem *restrict twr, const qtw_elem *restrict twi,
                                      long lo, long hi, vq *restrict mx){
  switch(m){
    case  8: qsr8_twmax (ar,ai,S,twr,twi,lo,hi,mx); return;
    case 16: qsr16_twmax(ar,ai,S,twr,twi,lo,hi,mx); return;
    default: qsr32_twmax(ar,ai,S,twr,twi,lo,hi,mx); return;
  }
}

#if !(HWY_ARCH_X86 && HWY_MAX_BYTES == 32)
static HWY_NOINLINE void q15_tw16_init_slow(int *ready){
  (void)ap_q15_twiddle_table(64);
  __atomic_store_n(ready, 1, __ATOMIC_RELEASE);
}
#endif

template<int IDX>
static HWY_INLINE const qtw_table *q15_tw_fast(void){
#if HWY_ARCH_X86 && HWY_MAX_BYTES == 32
  if(__builtin_expect(!__atomic_load_n(&q15_tw32_ready, __ATOMIC_ACQUIRE), 0))
    q15_tw32_init_slow();
  return &q15_tw32_tab[IDX];
#else
  static int ready = 0;
  if(__builtin_expect(!__atomic_load_n(&ready, __ATOMIC_ACQUIRE), 0))
    q15_tw16_init_slow(&ready);
  return &ap_q15_tw_tab[IDX];
#endif
}

template<int M1, int M2>
static HWY_NOINLINE void q15_twmax_edge_n(const qtw_table *tw, const vq *X, const vq *Xi,
                                          size_t ws, size_t we, vq *mm){
  constexpr size_t st = (size_t)(M1 + 1);
  const size_t wso = ws + (size_t)(M2 - 1), weo = we + (size_t)(M2 - 1);
  for(size_t k2 = 0; k2 < (size_t)M2; k2++){
    const long lo = (long)((wso - k2) / (size_t)M2);
    const long hi = (long)((weo - k2) / (size_t)M2);
    if(lo >= hi) continue;
    qcodelet_twmax(M1, X + k2 * st, Xi + k2 * st, 1,
                   tw->re + k2 * (size_t)M1, tw->im + k2 * (size_t)M1, lo, hi, mm);
  }
}

template<int M1, int M2>
static HWY_NOINLINE int q15_finish_lag_n(const qtw_table *tw, vq *X, vq *Xi,
                                         size_t ws, size_t we, const int16_t *lanethr,
                                         uint64_t *bits, int16_t *lanemax, int16_t *laneidx){
  constexpr size_t st = (size_t)(M1 + 1);
  /* Elect each lane's argmax lag k = k2 + M2*k1 over [ws, we), breaking ties to earliest lag.
     Fusing Pass 2's row transform with the row scan skips empty rows and reads xr/xi L1D-hot. */
  vq m0 = Q_SET1(-1), m1 = Q_SET1(-1), ix0 = Q_SET1(32767), ix1 = Q_SET1(32767);
  const size_t wso = ws + (size_t)(M2 - 1), weo = we + (size_t)(M2 - 1);
  for(size_t k2 = 0; k2 < (size_t)M2; k2++){
    const long lo = (long)((wso - k2) / (size_t)M2);
    const long hi = (long)((weo - k2) / (size_t)M2);
    if(lo >= hi) continue;
    vq *xr = X + k2 * st, *xi = Xi + k2 * st;
    qcodelet_tw(M1, xr, xi, 1, tw->re + k2 * (size_t)M1, tw->im + k2 * (size_t)M1);
    long k1 = lo;
    for(; k1 + 1 < hi; k1 += 2){
      const vq a = xr[k1], b = xi[k1], c = xr[k1 + 1], d = xi[k1 + 1];
      const vq s0 = hn::SaturatedAdd(Q_MUL(a, a), Q_MUL(b, b));
      const vq s1 = hn::SaturatedAdd(Q_MUL(c, c), Q_MUL(d, d));
      const vq j0 = Q_SET1((int)k2 + M2 * (int)k1), j1 = Q_SET1((int)k2 + M2 * (int)(k1 + 1));
      const auto u0 = hn::Or(hn::Gt(s0, m0), hn::And(hn::Eq(s0, m0), hn::Lt(j0, ix0)));
      const auto u1 = hn::Or(hn::Gt(s1, m1), hn::And(hn::Eq(s1, m1), hn::Lt(j1, ix1)));
      m0 = hn::Max(m0, s0);
      m1 = hn::Max(m1, s1);
      ix0 = hn::IfThenElse(u0, j0, ix0);
      ix1 = hn::IfThenElse(u1, j1, ix1);
    }
    if(k1 < hi){
      const vq a = xr[k1], b = xi[k1];
      const vq s0 = hn::SaturatedAdd(Q_MUL(a, a), Q_MUL(b, b));
      const vq j0 = Q_SET1((int)k2 + M2 * (int)k1);
      const auto u0 = hn::Or(hn::Gt(s0, m0), hn::And(hn::Eq(s0, m0), hn::Lt(j0, ix0)));
      m0 = hn::Max(m0, s0);
      ix0 = hn::IfThenElse(u0, j0, ix0);
    }
  }
  const auto u1 = hn::Or(hn::Gt(m1, m0), hn::And(hn::Eq(m1, m0), hn::Lt(ix1, ix0)));
  const vq mx_raw = hn::Max(m0, m1);
  const vq ix = hn::IfThenElse(hn::Ge(mx_raw, Q_ZERO()), hn::IfThenElse(u1, ix1, ix0), Q_SET1(-1));
  hn::StoreU(ix, AP_DQ, laneidx);
  const vq mx = hn::Max(mx_raw, Q_ZERO());
  if(lanemax) hn::StoreU(mx, AP_DQ, lanemax);
  uint64_t b = 0;
  hn::StoreMaskBits(AP_DQ, hn::Ge(mx, hn::LoadU(AP_DQ, lanethr)), (uint8_t *)&b);
  *bits = b;
  return 0;
}

template<int M1, int M2>
static HWY_NOINLINE void q15_twmax_wide_n(const qtw_table *tw, const vq *X, const vq *Xi,
                                          size_t ws, size_t we, vq *mm){
  constexpr size_t st = (size_t)(M1 + 1);
  const size_t wso = ws + (size_t)(M2 - 1), weo = we + (size_t)(M2 - 1);
  for(size_t k2 = 0; k2 < (size_t)M2; k2++){
    const long lo = (long)((wso - k2) / (size_t)M2);
    const long hi = (long)((weo - k2) / (size_t)M2);
    if constexpr (M1 == 16)
      qsr16_twmax_wide(X + k2 * st, Xi + k2 * st, 1,
                       tw->re + k2 * (size_t)M1, tw->im + k2 * (size_t)M1, lo, hi, mm);
    else
      qsr32_twmax_wide(X + k2 * st, Xi + k2 * st, 1,
                       tw->re + k2 * (size_t)M1, tw->im + k2 * (size_t)M1, lo, hi, mm);
  }
}

/* Pass 2 and the fused window maximum are shared across ordinary, permuted, and tiled products.
   Outlining the wide/edge fallbacks keeps q15_screen_n compact (Pass 1 + one middle loop, with
   branchless (ws + M2 - 1 - k2) / M2 row bounds so the compiler never unswitches the k2 loop);
   with the streaming codelet schedule and lazy M0, M1 initialisation, the fused pass stays within
   budget even on 16-register targets (AVX2, SSE4), eliminating the second scratch writeback and
   separate magnitude-squared scan. */
template<int M1, int M2, bool HAS_IDX>
static HWY_INLINE int q15_finish_n(const qtw_table *tw, vq *X, vq *Xi,
                                   size_t ws, size_t we, const int16_t *lanethr,
                                   uint64_t *bits, int16_t *lanemax, int16_t *laneidx){
  constexpr size_t N = (size_t)M1 * (size_t)M2;
  constexpr size_t st = (size_t)(M1 + 1);
  if(we > N) we = N;
  if constexpr (HAS_IDX) {
    if(laneidx) return q15_finish_lag_n<M1, M2>(tw, X, Xi, ws, we, lanethr, bits, lanemax, laneidx);
  }
  vq mm[2] = {Q_ZERO(), Q_ZERO()};
  const size_t wso = ws + (size_t)(M2 - 1), weo = we + (size_t)(M2 - 1);
  if constexpr (M1 == 8) {
    if(ws <= 2 * (size_t)M2 && we >= 6 * (size_t)M2){
      for(size_t k2 = 0; k2 < (size_t)M2; k2++){
        const long lo = (long)((wso - k2) / (size_t)M2);
        const long hi = (long)((weo - k2) / (size_t)M2);
        qsr8_twmax_middle(X + k2 * st, Xi + k2 * st, 1,
                          tw->re + k2 * (size_t)M1, tw->im + k2 * (size_t)M1, lo, hi, mm);
      }
    } else {
      q15_twmax_edge_n<M1, M2>(tw, X, Xi, ws, we, mm);
    }
  } else if constexpr (M1 == 16) {
    if(ws <= 2 * (size_t)M2 && we >= 14 * (size_t)M2){
      for(size_t k2 = 0; k2 < (size_t)M2; k2++){
        const long lo = (long)((wso - k2) / (size_t)M2);
        const long hi = (long)((weo - k2) / (size_t)M2);
        qsr16_twmax_middle(X + k2 * st, Xi + k2 * st, 1,
                           tw->re + k2 * (size_t)M1, tw->im + k2 * (size_t)M1, lo, hi, mm);
      }
    } else if(ws <= 4 * (size_t)M2 && we >= 12 * (size_t)M2){
      q15_twmax_wide_n<M1, M2>(tw, X, Xi, ws, we, mm);
    } else {
      q15_twmax_edge_n<M1, M2>(tw, X, Xi, ws, we, mm);
    }
  } else {
    if(ws <= 4 * (size_t)M2 && we >= 28 * (size_t)M2){
      for(size_t k2 = 0; k2 < (size_t)M2; k2++){
        const long lo = (long)((wso - k2) / (size_t)M2);
        const long hi = (long)((weo - k2) / (size_t)M2);
        qsr32_twmax_middle(X + k2 * st, Xi + k2 * st, 1,
                           tw->re + k2 * (size_t)M1, tw->im + k2 * (size_t)M1, lo, hi, mm);
      }
    } else if(ws <= 8 * (size_t)M2 && we >= 24 * (size_t)M2){
      q15_twmax_wide_n<M1, M2>(tw, X, Xi, ws, we, mm);
    } else {
      q15_twmax_edge_n<M1, M2>(tw, X, Xi, ws, we, mm);
    }
  }
  const vq mx = hn::Max(mm[0], mm[1]);
  if(lanemax) hn::StoreU(mx, AP_DQ, lanemax);
  uint64_t bits_ = 0;
  hn::StoreMaskBits(AP_DQ, hn::Ge(mx, hn::LoadU(AP_DQ, lanethr)), (uint8_t *)&bits_);
  *bits = bits_;
  return 0;
}

/* N x QW pairs: pass 1 forms d*t as it loads (M2-point codelets down the columns),
   pass 2 applies the conjugated four-step twiddle and fused window maximum (M1-point
   codelets along the rows).  dq is [N] int32 duplicated dr followed by [N] int16 di
   (3*N int16 total); tr/ti are [N][QW].  Bit l of *bits is set when lane l's maximum
   reaches lanethr[l]; lanemax, if not NULL, gets the QW maxima. */
template<int M1, int M2>
static HWY_INLINE void q15_prod_n(const int16_t *dq, const int16_t *tr, const int16_t *ti,
                                  vq *X, vq *Xi){
  constexpr size_t N = (size_t)M1 * (size_t)M2;
  const int32_t *dr = (const int32_t *)dq;
  const int16_t *di = dq + 2 * N;
  for(int e1 = 0; e1 < M1; e1++)
    qcodelet_prod(M2, dr + e1, di + e1, tr + (size_t)e1 * AP_QW, ti + (size_t)e1 * AP_QW,
                  X + e1, Xi + e1, M1 + 1, M1, (long)M1 * AP_QW);
}

template<int IDX, int M1, int M2>
static HWY_NOINLINE int q15_screen_n(const int16_t *dq, const int16_t *tr, const int16_t *ti,
                                     size_t ws, size_t we, const int16_t *lanethr, uint64_t *bits,
                                     int16_t *lanemax, void *scratch){
  const qtw_table *tw = q15_tw_fast<IDX>();
  vq *X = (vq *)scratch, *Xi = X + (size_t)(M1 + 1) * M2;
  q15_prod_n<M1, M2>(dq, tr, ti, X, Xi);
  return q15_finish_n<M1, M2, false>(tw, X, Xi, ws, we, lanethr, bits, lanemax, nullptr);
}

static int q15_screen(size_t N, const int16_t *dq, const int16_t *tr, const int16_t *ti,
                      size_t ws, size_t we, const int16_t *lanethr, uint64_t *bits,
                      int16_t *lanemax, void *scratch){
  switch(N){
    case   64: return q15_screen_n<0,  8,  8>(dq, tr, ti, ws, we, lanethr, bits, lanemax, scratch);
    case  128: return q15_screen_n<1, 16,  8>(dq, tr, ti, ws, we, lanethr, bits, lanemax, scratch);
    case  256: return q15_screen_n<2, 16, 16>(dq, tr, ti, ws, we, lanethr, bits, lanemax, scratch);
    case  512: return q15_screen_n<3, 32, 16>(dq, tr, ti, ws, we, lanethr, bits, lanemax, scratch);
    case 1024: return q15_screen_n<4, 32, 32>(dq, tr, ti, ws, we, lanethr, bits, lanemax, scratch);
    default: return -1;
  }
}

/* QW listed pairs: as q15_screen, but lane l's data element is lane dsel[l] of dr/di (QW data
   blocks laid out [N][QW], as the templates are) and its template is lane tsel[l] of the two
   template groups at tr/ti and tr/ti + TW (tsel < 2 QW; TW 0 repeats the first group). Same
   arithmetic per lane as q15_screen: a lane's maximum is bit-identical to the one it gets
   there. */
template<int M1, int M2>
static HWY_INLINE void q15_prod_perm_n(const int16_t *dr, const int16_t *di, const int16_t *tr,
                                       const int16_t *ti, long TW, const qidx dix,
                                       const qidx tix, vq *X, vq *Xi){
  for(int e1 = 0; e1 < M1; e1++)
    qcodelet_prod_perm(M2, dr + (size_t)e1 * AP_QW, di + (size_t)e1 * AP_QW,
                       tr + (size_t)e1 * AP_QW, ti + (size_t)e1 * AP_QW,
                       X + e1, Xi + e1, M1 + 1, (long)M1 * AP_QW, TW, dix, tix);
}

template<int IDX, int M1, int M2>
static HWY_NOINLINE int q15_screen_perm_n(const int16_t *dr, const int16_t *di, const int16_t *tr,
                                          const int16_t *ti, long TW, const int16_t *dsel,
                                          const int16_t *tsel, size_t ws, size_t we,
                                          const int16_t *lanethr, uint64_t *bits,
                                          int16_t *lanemax, int16_t *laneidx, void *scratch){
  const qtw_table *tw = q15_tw_fast<IDX>();
#if HWY_TARGET == HWY_AVX2
  ap_qidx_avx2 dix_s, tix_s;
  q15_make_dix_avx2(&dix_s, dsel);
  q15_make_tix_avx2(&tix_s, tsel, TW);
  const qidx dix = &dix_s, tix = &tix_s;
#else
  const qidx dix = hn::SetTableIndices(AP_DQ, dsel), tix = hn::SetTableIndices(AP_DQ, tsel);
#endif
  vq *X = (vq *)scratch, *Xi = X + (size_t)(M1 + 1) * M2;
  q15_prod_perm_n<M1, M2>(dr, di, tr, ti, TW, dix, tix, X, Xi);
  return q15_finish_n<M1, M2, true>(tw, X, Xi, ws, we, lanethr, bits, lanemax, laneidx);
}

static int q15_screen_perm(size_t N, const int16_t *dr, const int16_t *di, const int16_t *tr,
                           const int16_t *ti, long TW, const int16_t *dsel, const int16_t *tsel,
                           size_t ws, size_t we, const int16_t *lanethr, uint64_t *bits,
                           int16_t *lanemax, int16_t *laneidx, void *scratch){
  switch(N){
    case   64: return q15_screen_perm_n<0,  8,  8>(dr, di, tr, ti, TW, dsel, tsel, ws, we, lanethr, bits, lanemax, laneidx, scratch);
    case  128: return q15_screen_perm_n<1, 16,  8>(dr, di, tr, ti, TW, dsel, tsel, ws, we, lanethr, bits, lanemax, laneidx, scratch);
    case  256: return q15_screen_perm_n<2, 16, 16>(dr, di, tr, ti, TW, dsel, tsel, ws, we, lanethr, bits, lanemax, laneidx, scratch);
    case  512: return q15_screen_perm_n<3, 32, 16>(dr, di, tr, ti, TW, dsel, tsel, ws, we, lanethr, bits, lanemax, laneidx, scratch);
    case 1024: return q15_screen_perm_n<4, 32, 32>(dr, di, tr, ti, TW, dsel, tsel, ws, we, lanethr, bits, lanemax, laneidx, scratch);
    default: return -1;
  }
}

/* Arbitrary-pair Q15 gather screen: up to AP_QW (data, template) pairs at 100% SIMD occupancy
   from contiguous [N] int16 rows without slab or template-group bucketing.  Each pair's complex
   product is streamed sequentially into an L1D-resident padded buffer (reusing dR/dI in vector
   registers across consecutive pairs that share a data block), transposed AP_QW x AP_QW into
   four-step columns X[e1 + (M1 + 1)*e2], and transformed in place with qsr{8,16,32} + Pass 2.
   Every multiply and rounding matches q15_screen bit-for-bit. */
static HWY_INLINE void q15_transpose8_inlane(vq r[8]){
  const hn::Repartition<int32_t, ap_qtag> d32;
  const hn::Repartition<int64_t, ap_qtag> d64;
  vq t[8], u[8];
  for(int j = 0; j < 4; j++){
    t[2 * j]     = hn::InterleaveLower(AP_DQ, r[2 * j], r[2 * j + 1]);
    t[2 * j + 1] = hn::InterleaveUpper(AP_DQ, r[2 * j], r[2 * j + 1]);
  }
  for(int h = 0; h < 2; h++){
    for(int j = 0; j < 2; j++){
      const auto a = hn::BitCast(d32, t[4 * h + j]);
      const auto c = hn::BitCast(d32, t[4 * h + j + 2]);
      u[4 * h + 2 * j]     = hn::BitCast(AP_DQ, hn::InterleaveLower(d32, a, c));
      u[4 * h + 2 * j + 1] = hn::BitCast(AP_DQ, hn::InterleaveUpper(d32, a, c));
    }
  }
  for(int j = 0; j < 4; j++){
    const auto a = hn::BitCast(d64, u[j]);
    const auto c = hn::BitCast(d64, u[4 + j]);
    r[2 * j]     = hn::BitCast(AP_DQ, hn::InterleaveLower(d64, a, c));
    r[2 * j + 1] = hn::BitCast(AP_DQ, hn::InterleaveUpper(d64, a, c));
  }
}

template<int M1>
static HWY_INLINE void q15_store_block_col(const vq *pbuf, int pstride, int dv,
                                           size_t k_base, vq *X){
  constexpr size_t st = (size_t)(M1 + 1);
#if HWY_ARCH_X86 && HWY_MAX_BYTES == 64
  vq u0[8], u1[8];
  for(int j = 0; j < 8; j++){
    u0[j] = pbuf[(size_t)j * (size_t)pstride + (size_t)dv];
    u1[j] = pbuf[(size_t)(8 + j) * (size_t)pstride + (size_t)dv];
  }
  q15_transpose8_inlane(u0);
  q15_transpose8_inlane(u1);
  __m512i ab_01[8], ab_23[8];
  for(int m = 0; m < 8; m++){
    ab_01[m] = _mm512_shuffle_i32x4(u0[m].raw, u1[m].raw, 0x44);
    ab_23[m] = _mm512_shuffle_i32x4(u0[m].raw, u1[m].raw, 0xEE);
  }
  vq u2[8], u3[8];
  for(int j = 0; j < 8; j++){
    u2[j] = pbuf[(size_t)(16 + j) * (size_t)pstride + (size_t)dv];
    u3[j] = pbuf[(size_t)(24 + j) * (size_t)pstride + (size_t)dv];
  }
  q15_transpose8_inlane(u2);
  q15_transpose8_inlane(u3);
  for(int m = 0; m < 8; m++){
    const __m512i cd_01 = _mm512_shuffle_i32x4(u2[m].raw, u3[m].raw, 0x44);
    const __m512i cd_23 = _mm512_shuffle_i32x4(u2[m].raw, u3[m].raw, 0xEE);
    const size_t k0 = k_base + (size_t)m;
    const size_t k1 = k_base + 8 + (size_t)m;
    const size_t k2 = k_base + 16 + (size_t)m;
    const size_t k3 = k_base + 24 + (size_t)m;
    X[(k0 & (size_t)(M1 - 1)) + st * (k0 / (size_t)M1)] = vq{_mm512_shuffle_i32x4(ab_01[m], cd_01, 0x88)};
    X[(k1 & (size_t)(M1 - 1)) + st * (k1 / (size_t)M1)] = vq{_mm512_shuffle_i32x4(ab_01[m], cd_01, 0xDD)};
    X[(k2 & (size_t)(M1 - 1)) + st * (k2 / (size_t)M1)] = vq{_mm512_shuffle_i32x4(ab_23[m], cd_23, 0x88)};
    X[(k3 & (size_t)(M1 - 1)) + st * (k3 / (size_t)M1)] = vq{_mm512_shuffle_i32x4(ab_23[m], cd_23, 0xDD)};
  }
#elif HWY_ARCH_X86 && HWY_MAX_BYTES == 32 && HWY_TARGET <= HWY_AVX2
  vq u0[8], u1[8];
  for(int j = 0; j < 8; j++){
    u0[j] = pbuf[(size_t)j * (size_t)pstride + (size_t)dv];
    u1[j] = pbuf[(size_t)(8 + j) * (size_t)pstride + (size_t)dv];
  }
  q15_transpose8_inlane(u0);
  q15_transpose8_inlane(u1);
  for(int m = 0; m < 8; m++){
    const size_t k0 = k_base + (size_t)m;
    const size_t k1 = k_base + 8 + (size_t)m;
    X[(k0 & (size_t)(M1 - 1)) + st * (k0 / (size_t)M1)] = vq{_mm256_permute2x128_si256(u0[m].raw, u1[m].raw, 0x20)};
    X[(k1 & (size_t)(M1 - 1)) + st * (k1 / (size_t)M1)] = vq{_mm256_permute2x128_si256(u0[m].raw, u1[m].raw, 0x31)};
  }
#elif AP_QW == 8
  vq u[8];
  for(int l = 0; l < 8; l++)
    u[l] = pbuf[(size_t)l * (size_t)pstride + (size_t)dv];
  q15_transpose8_inlane(u);
  for(int m = 0; m < 8; m++){
    const size_t k0 = k_base + (size_t)m;
    X[(k0 & (size_t)(M1 - 1)) + st * (k0 / (size_t)M1)] = u[m];
  }
#else
  alignas(64) int16_t tmp[AP_QW][AP_QW];
  for(int l = 0; l < AP_QW; l++){
    alignas(64) int16_t row[AP_QW];
    hn::Store(pbuf[(size_t)l * (size_t)pstride + (size_t)dv], AP_DQ, row);
    for(int m = 0; m < AP_QW; m++) tmp[m][l] = row[m];
  }
  for(int m = 0; m < AP_QW; m++){
    const size_t k0 = k_base + (size_t)m;
    X[(k0 & (size_t)(M1 - 1)) + st * (k0 / (size_t)M1)] = hn::Load(AP_DQ, tmp[m]);
  }
#endif
}

template<int M1, int M2>
static HWY_INLINE void q15_prod_gather_n(const int16_t *const *drp, const int16_t *const *dip,
                                         const int16_t *const *trp, const int16_t *const *tip,
                                         vq *X, vq *Xi){
  constexpr int NV = (M1 * M2) / AP_QW;
  constexpr int VB = NV < 4 ? NV : 4;
  static_assert(NV % VB == 0, "NV must be divisible by VB");
  constexpr int PSTRIDE = VB + 1;
  alignas(64) vq pbuf_r[AP_QW * PSTRIDE];
  alignas(64) vq pbuf_i[AP_QW * PSTRIDE];
  for(int v0 = 0; v0 < NV; v0 += VB){
    const size_t k_tile = (size_t)v0 * (size_t)AP_QW;
    const int16_t *cur_dr = nullptr;
    vq dR[VB], dI[VB];
    for(int l = 0; l < AP_QW; l++){
      if(drp[l] != cur_dr){
        cur_dr = drp[l];
        const int16_t *drl = cur_dr + k_tile;
        const int16_t *dil = dip[l] + k_tile;
        for(int dv = 0; dv < VB; dv++){
          dR[dv] = Q_LOADU(drl + (size_t)dv * (size_t)AP_QW);
          dI[dv] = Q_LOADU(dil + (size_t)dv * (size_t)AP_QW);
        }
      }
      const int16_t *trl = trp[l] + k_tile;
      const int16_t *til = tip[l] + k_tile;
      vq *pr = pbuf_r + (size_t)l * (size_t)PSTRIDE;
      vq *pi = pbuf_i + (size_t)l * (size_t)PSTRIDE;
      for(int dv = 0; dv < VB; dv++){
        const vq tR = Q_LOADU(trl + (size_t)dv * (size_t)AP_QW);
        const vq tI = Q_LOADU(til + (size_t)dv * (size_t)AP_QW);
        pr[dv] = Q_MLSH(Q_MUL(dR[dv], tR), dI[dv], tI);
        pi[dv] = Q_MLAH(Q_MUL(dR[dv], tI), dI[dv], tR);
      }
    }
    for(int dv = 0; dv < VB; dv++){
      const size_t k_base = k_tile + (size_t)dv * (size_t)AP_QW;
      q15_store_block_col<M1>(pbuf_r, PSTRIDE, dv, k_base, X);
      q15_store_block_col<M1>(pbuf_i, PSTRIDE, dv, k_base, Xi);
    }
  }
  for(int e1 = 0; e1 < M1; e1++)
    qcodelet(M2, X + e1, Xi + e1, M1 + 1);
}

template<int IDX, int M1, int M2>
static HWY_NOINLINE int q15_screen_gather_n(const int16_t *const *drp, const int16_t *const *dip,
                                            const int16_t *const *trp, const int16_t *const *tip,
                                            int cnt, size_t ws, size_t we, const int16_t *lanethr,
                                            uint64_t *bits, int16_t *lanemax, int16_t *laneidx,
                                            void *scratch){
  const qtw_table *tw = q15_tw_fast<IDX>();
  vq *X = (vq *)scratch, *Xi = X + (size_t)(M1 + 1) * M2;
  q15_prod_gather_n<M1, M2>(drp, dip, trp, tip, X, Xi);
  const int r = q15_finish_n<M1, M2, true>(tw, X, Xi, ws, we, lanethr, bits, lanemax, laneidx);
  if(cnt < 64) *bits &= (((uint64_t)1 << cnt) - 1u);
  return r;
}

static int q15_screen_gather(size_t N, const int16_t *const *drp, const int16_t *const *dip,
                             const int16_t *const *trp, const int16_t *const *tip, int cnt,
                             size_t ws, size_t we, const int16_t *lanethr, uint64_t *bits,
                             int16_t *lanemax, int16_t *laneidx, void *scratch){
  if(cnt < 1 || cnt > AP_QW) return -1;
  const int16_t *dr_pad[AP_QW], *di_pad[AP_QW], *tr_pad[AP_QW], *ti_pad[AP_QW];
  if(cnt < AP_QW){
    for(int l = 0; l < cnt; l++){
      dr_pad[l] = drp[l]; di_pad[l] = dip[l];
      tr_pad[l] = trp[l]; ti_pad[l] = tip[l];
    }
    for(int l = cnt; l < AP_QW; l++){
      dr_pad[l] = drp[cnt - 1]; di_pad[l] = dip[cnt - 1];
      tr_pad[l] = trp[cnt - 1]; ti_pad[l] = tip[cnt - 1];
    }
    drp = dr_pad; dip = di_pad; trp = tr_pad; tip = ti_pad;
  }
  switch(N){
    case   64: return q15_screen_gather_n<0,  8,  8>(drp, dip, trp, tip, cnt, ws, we, lanethr, bits, lanemax, laneidx, scratch);
    case  128: return q15_screen_gather_n<1, 16,  8>(drp, dip, trp, tip, cnt, ws, we, lanethr, bits, lanemax, laneidx, scratch);
    case  256: return q15_screen_gather_n<2, 16, 16>(drp, dip, trp, tip, cnt, ws, we, lanethr, bits, lanemax, laneidx, scratch);
    case  512: return q15_screen_gather_n<3, 32, 16>(drp, dip, trp, tip, cnt, ws, we, lanethr, bits, lanemax, laneidx, scratch);
    case 1024: return q15_screen_gather_n<4, 32, 32>(drp, dip, trp, tip, cnt, ws, we, lanethr, bits, lanemax, laneidx, scratch);
    default: return -1;
  }
}

#if AP_Q15_TAIL
template<int T, int IDX, int M1, int M2>
static HWY_NOINLINE int q15_screen_tile_n(const int16_t *dq, const int16_t *tr, const int16_t *ti,
                                          size_t ws, size_t we, const int16_t *lanethr,
                                          uint64_t *bits, int16_t *lanemax, void *scratch){
  constexpr long N = (long)M1 * M2;
  const qtw_table *tw = q15_tw_fast<IDX>();
  vq *X = (vq *)scratch, *Xi = X + (M1 + 1) * M2;
  const int32_t *dr0 = (const int32_t *)dq;
  const int16_t *di0 = dq + 2 * N;
  for(int e1 = 0; e1 < M1; e1++){
    const int32_t *dr = dr0 + e1;
    const int16_t *di = di0 + e1, *r = tr + e1 * AP_QW, *i = ti + e1 * AP_QW;
    if(M2 == 8) qsr8_prod_tile<T, 3 * N>(dr, di, r, i, X + e1, Xi + e1, M1 + 1, M1, (long)M1 * AP_QW);
    else if(M2 == 16) qsr16_prod_tile<T, 3 * N>(dr, di, r, i, X + e1, Xi + e1, M1 + 1, M1, (long)M1 * AP_QW);
    else qsr32_prod_tile<T, 3 * N>(dr, di, r, i, X + e1, Xi + e1, M1 + 1, M1, (long)M1 * AP_QW);
  }
  return q15_finish_n<M1, M2, false>(tw, X, Xi, ws, we, lanethr, bits, lanemax, nullptr);
}
template<int T>
static int q15_screen_tile_t(size_t N, const int16_t *dq, const int16_t *tr, const int16_t *ti,
                             size_t ws, size_t we, const int16_t *lanethr,
                             uint64_t *bits, int16_t *lanemax, void *scratch){
  switch(N){
    case   64: return q15_screen_tile_n<T, 0,  8,  8>(dq,tr,ti,ws,we,lanethr,bits,lanemax,scratch);
    case  128: return q15_screen_tile_n<T, 1, 16,  8>(dq,tr,ti,ws,we,lanethr,bits,lanemax,scratch);
    case  256: return q15_screen_tile_n<T, 2, 16, 16>(dq,tr,ti,ws,we,lanethr,bits,lanemax,scratch);
    case  512: return q15_screen_tile_n<T, 3, 32, 16>(dq,tr,ti,ws,we,lanethr,bits,lanemax,scratch);
    case 1024: return q15_screen_tile_n<T, 4, 32, 32>(dq,tr,ti,ws,we,lanethr,bits,lanemax,scratch);
  }
  return -1;
}
/* An N-point screen of T templates per block: the target's tile widths, QW/4 and QW/2 (8 and 16
   on AVX-512, 4 and 8 on AVX2); any other T or N is refused. */
static int q15_screen_tile(size_t N, int T, const int16_t *dq, const int16_t *tr, const int16_t *ti,
                           size_t ws, size_t we, const int16_t *lanethr,
                           uint64_t *bits, int16_t *lanemax, void *scratch){
  if(T == AP_QW / 4)
    return q15_screen_tile_t<AP_QW / 4>(N,dq,tr,ti,ws,we,lanethr,bits,lanemax,scratch);
  if(T == AP_QW / 2)
    return q15_screen_tile_t<AP_QW / 2>(N,dq,tr,ti,ws,we,lanethr,bits,lanemax,scratch);
  return -1;
}
#endif

/* Eight data blocks' rows quantised into eight consecutive lanes of a slab (q15_screen_perm's
   data layout, [N][QW]): x = nearest(row[k] * sc) for each of re and im, as matchfilt.c's
   q15_data rounds them, then an 8 x 8 int16 transpose in 128-bit registers so each element's
   eight lanes go out in one store. */
static void q15_slab8(size_t N, const float *const *rr, const float *const *ri, const float *sc,
                      int16_t *xr, int16_t *xi){
  const hn::FixedTag<float, 4> df;
  const hn::FixedTag<int32_t, 4> di;
  const hn::FixedTag<int16_t, 8> dh;
  const hn::FixedTag<int64_t, 2> dl;
  using V16 = hn::Vec<decltype(dh)>;
  for(int part = 0; part < 2; part++){
    const float *const *rows = part ? ri : rr;
    int16_t *out = part ? xi : xr;
    for(size_t k = 0; k < N; k += 8){
      V16 r[8];
      for(int b = 0; b < 8; b++){
        const auto s = hn::Set(df, sc[b]);
        const auto a = hn::NearestInt(hn::Mul(hn::LoadU(df, rows[b] + k), s));
        const auto c = hn::NearestInt(hn::Mul(hn::LoadU(df, rows[b] + k + 4), s));
        r[b] = hn::OrderedDemote2To(dh, a, c);
      }
      V16 t[8], u[8];
      for(int j = 0; j < 4; j++){
        t[2 * j] = hn::InterleaveLower(dh, r[2 * j], r[2 * j + 1]);
        t[2 * j + 1] = hn::InterleaveUpper(dh, r[2 * j], r[2 * j + 1]);
      }
      for(int h = 0; h < 2; h++)
        for(int j = 0; j < 2; j++){
          const auto a = hn::BitCast(di, t[4 * h + j]), c = hn::BitCast(di, t[4 * h + j + 2]);
          u[4 * h + 2 * j] = hn::BitCast(dh, hn::InterleaveLower(di, a, c));
          u[4 * h + 2 * j + 1] = hn::BitCast(dh, hn::InterleaveUpper(di, a, c));
        }
      for(int j = 0; j < 4; j++){
        const auto a = hn::BitCast(dl, u[j]), c = hn::BitCast(dl, u[4 + j]);
        hn::StoreU(hn::BitCast(dh, hn::InterleaveLower(dl, a, c)), dh, out + (k + 2 * j) * AP_QW);
        hn::StoreU(hn::BitCast(dh, hn::InterleaveUpper(dl, a, c)), dh, out + (k + 2 * j + 1) * AP_QW);
      }
    }
  }
}

static int q15_lanes(void){ return AP_QW; }

#if defined(__ELF__) && (defined(__GNUC__) || defined(__clang__))
#define MF_Q15PREP_SECTION __attribute__((section(".text.mf_q15prep")))
#else
#define MF_Q15PREP_SECTION
#endif

/* Vectorised sum of squares sum_{k<N} (re[k]^2 + im[k]^2); invariant to group-major layout. */
static HWY_NOINLINE MF_Q15PREP_SECTION double q15_sumsq(size_t N, const float *re, const float *im){
  vf s0 = V_ZERO(), s1 = V_ZERO();
  size_t k = 0;
  for(; k + 2 * (size_t)AP_W <= N; k += 2 * (size_t)AP_W){
    const vf r0 = V_LOADU(re + k), i0 = V_LOADU(im + k);
    const vf r1 = V_LOADU(re + k + AP_W), i1 = V_LOADU(im + k + AP_W);
    s0 = V_FMADD(r0, r0, V_FMADD(i0, i0, s0));
    s1 = V_FMADD(r1, r1, V_FMADD(i1, i1, s1));
  }
  for(; k + (size_t)AP_W <= N; k += (size_t)AP_W){
    const vf r0 = V_LOADU(re + k), i0 = V_LOADU(im + k);
    s0 = V_FMADD(r0, r0, V_FMADD(i0, i0, s0));
  }
  double ss = (double)hn::ReduceSum(AP_D, V_ADD(s0, s1));
  for(; k < N; k++) ss += (double)re[k] * re[k] + (double)im[k] * im[k];
  return ss;
}

/* Quantise one data block's split spectrum into [N] int32 duplicated dr followed by
   [N] int16 di (3*N int16 total, matching p->qd's allocation), handling both natural
   order (n1 <= 0) and group-major order ([n1/w][n2][w]). */
static HWY_NOINLINE MF_Q15PREP_SECTION void q15_data(size_t N, const float *re, const float *im,
                                                     int n1, int n2, int w, int16_t *qd,
                                                     float *scale_out){
  const double ss = q15_sumsq(N, re, im);
  const double D = (AP_Q15_L1 - 1.5 * (double)N) * 32768.0 / AP_Q15_TNORM(N) - sqrt((double)N);
  const double sc = !isfinite(ss) ? -1.0 : ss > 0.0 ? 0.999 * D / sqrt(ss) : 0.0;
  *scale_out = (float)sc;
  if(!(sc > 0.0)){
    memset(qd, 0, N * 3 * sizeof(int16_t));
    return;
  }
  const float scf = (float)sc;
  const vf vs = V_SET1(scf);
  const vi vmin32 = hn::Set(AP_DI, -32767), vmax32 = hn::Set(AP_DI, 32767);
  const vi vmask16 = hn::Set(AP_DI, 0xFFFF);
  int32_t *qd_re = (int32_t *)qd;
  int16_t *qd_im = qd + 2 * N;
  if((n1 <= 0 || (w == AP_W && n1 == AP_W && (size_t)n1 * (size_t)n2 == N)) &&
     N % (size_t)AP_QW == 0){
    for(size_t k = 0; k < N; k += (size_t)AP_QW){
      const vi r0 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(re + k), vs)), vmin32), vmax32);
      const vi r1 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(re + k + AP_W), vs)), vmin32), vmax32);
      const vi i0 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(im + k), vs)), vmin32), vmax32);
      const vi i1 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(im + k + AP_W), vs)), vmin32), vmax32);
      const vi d0 = hn::Or(hn::And(r0, vmask16), hn::ShiftLeft<16>(r0));
      const vi d1 = hn::Or(hn::And(r1, vmask16), hn::ShiftLeft<16>(r1));
      const vq qi = hn::OrderedDemote2To(AP_DQ, i0, i1);
      hn::StoreU(d0, AP_DI, qd_re + k);
      hn::StoreU(d1, AP_DI, qd_re + k + AP_W);
      hn::StoreU(qi, AP_DQ, qd_im + k);
    }
    return;
  }
  if(w == AP_W && n1 > 0 && n1 % AP_QW == 0 && (size_t)n1 * (size_t)n2 == N){
    const int ng = n1 / AP_W;
    for(int b = 0; b < n2; b++){
      for(int g = 0; g < ng; g += 2){
        const size_t j0 = ((size_t)g * (size_t)n2 + (size_t)b) * (size_t)AP_W;
        const size_t j1 = ((size_t)(g + 1) * (size_t)n2 + (size_t)b) * (size_t)AP_W;
        const size_t k = (size_t)b * (size_t)n1 + (size_t)g * (size_t)AP_W;
        const vi r0 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(re + j0), vs)), vmin32), vmax32);
        const vi r1 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(re + j1), vs)), vmin32), vmax32);
        const vi i0 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(im + j0), vs)), vmin32), vmax32);
        const vi i1 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(im + j1), vs)), vmin32), vmax32);
        const vi d0 = hn::Or(hn::And(r0, vmask16), hn::ShiftLeft<16>(r0));
        const vi d1 = hn::Or(hn::And(r1, vmask16), hn::ShiftLeft<16>(r1));
        const vq qi = hn::OrderedDemote2To(AP_DQ, i0, i1);
        hn::StoreU(d0, AP_DI, qd_re + k);
        hn::StoreU(d1, AP_DI, qd_re + k + AP_W);
        hn::StoreU(qi, AP_DQ, qd_im + k);
      }
    }
    return;
  }
  for(size_t k = 0; k < N; k++){
    size_t j = k;
    if(n1 > 0 && w > 0){
      const size_t a = k % (size_t)n1, b = k / (size_t)n1;
      j = (a / (size_t)w) * (size_t)n2 * (size_t)w + b * (size_t)w + a % (size_t)w;
    }
    int r = (int)lrintf(re[j] * scf), i = (int)lrintf(im[j] * scf);
    if(r > 32767) r = 32767; else if(r < -32767) r = -32767;
    if(i > 32767) i = 32767; else if(i < -32767) i = -32767;
    const uint32_t ur = (uint16_t)(int16_t)r;
    qd_re[k] = (int32_t)(ur | (ur << 16));
    qd_im[k] = (int16_t)i;
  }
}

/* Quantise one data block's split spectrum into contiguous natural-order [N] qdr and [N] qdi
   rows for q15_screen_gather, with the identical scale and rounding as q15_data. */
static HWY_NOINLINE MF_Q15PREP_SECTION void q15_data_contig(
    size_t N, const float *re, const float *im, int n1, int n2, int w,
    int16_t *qdr, int16_t *qdi, float *scale_out){
  const double ss = q15_sumsq(N, re, im);
  const double D = (AP_Q15_L1 - 1.5 * (double)N) * 32768.0 / AP_Q15_TNORM(N) - sqrt((double)N);
  const double sc = !isfinite(ss) ? -1.0 : ss > 0.0 ? 0.999 * D / sqrt(ss) : 0.0;
  *scale_out = (float)sc;
  if(!(sc > 0.0)){
    memset(qdr, 0, N * sizeof(int16_t));
    memset(qdi, 0, N * sizeof(int16_t));
    return;
  }
  const float scf = (float)sc;
  const vf vs = V_SET1(scf);
  const vi vmin32 = hn::Set(AP_DI, -32767), vmax32 = hn::Set(AP_DI, 32767);
  if((n1 <= 0 || (w == AP_W && n1 == AP_W && (size_t)n1 * (size_t)n2 == N)) &&
     N % (size_t)AP_QW == 0){
    for(size_t k = 0; k < N; k += (size_t)AP_QW){
      const vi r0 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(re + k), vs)), vmin32), vmax32);
      const vi r1 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(re + k + AP_W), vs)), vmin32), vmax32);
      const vi i0 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(im + k), vs)), vmin32), vmax32);
      const vi i1 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(im + k + AP_W), vs)), vmin32), vmax32);
      hn::StoreU(hn::OrderedDemote2To(AP_DQ, r0, r1), AP_DQ, qdr + k);
      hn::StoreU(hn::OrderedDemote2To(AP_DQ, i0, i1), AP_DQ, qdi + k);
    }
    return;
  }
  if(w == AP_W && n1 > 0 && n1 % AP_QW == 0 && (size_t)n1 * (size_t)n2 == N){
    const int ng = n1 / AP_W;
    for(int b = 0; b < n2; b++){
      for(int g = 0; g < ng; g += 2){
        const size_t j0 = ((size_t)g * (size_t)n2 + (size_t)b) * (size_t)AP_W;
        const size_t j1 = ((size_t)(g + 1) * (size_t)n2 + (size_t)b) * (size_t)AP_W;
        const size_t k = (size_t)b * (size_t)n1 + (size_t)g * (size_t)AP_W;
        const vi r0 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(re + j0), vs)), vmin32), vmax32);
        const vi r1 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(re + j1), vs)), vmin32), vmax32);
        const vi i0 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(im + j0), vs)), vmin32), vmax32);
        const vi i1 = hn::Min(hn::Max(hn::NearestInt(V_MUL(V_LOADU(im + j1), vs)), vmin32), vmax32);
        hn::StoreU(hn::OrderedDemote2To(AP_DQ, r0, r1), AP_DQ, qdr + k);
        hn::StoreU(hn::OrderedDemote2To(AP_DQ, i0, i1), AP_DQ, qdi + k);
      }
    }
    return;
  }
  for(size_t k = 0; k < N; k++){
    size_t j = k;
    if(n1 > 0 && w > 0){
      const size_t a = k % (size_t)n1, b = k / (size_t)n1;
      j = (a / (size_t)w) * (size_t)n2 * (size_t)w + b * (size_t)w + a % (size_t)w;
    }
    int r = (int)lrintf(re[j] * scf), i = (int)lrintf(im[j] * scf);
    if(r > 32767) r = 32767; else if(r < -32767) r = -32767;
    if(i > 32767) i = 32767; else if(i < -32767) i = -32767;
    qdr[k] = (int16_t)r;
    qdi[k] = (int16_t)i;
  }
}

/* Vectorised int16 lane thresholds across AP_QW lanes (qds_stride == 0 broadcasts qds[0]).
   Kept in the hot text section alongside q15_screen because matchfilt.c invokes it per batch. */
static HWY_NOINLINE void q15_lanethr(float threshold, const float *qds,
                                     int qds_stride, const float *qts,
                                     float margin, int nomargin, int16_t *out){
  if(!qds_stride && qds[0] < 0.f){
    hn::StoreU(Q_SET1(-32768), AP_DQ, out);
    return;
  }
  const vf vthr = V_SET1(threshold);
  const vf vinv = V_SET1((float)(1.0 / 32768.0));
  const vf vadj = V_SET1(1.0f - 1e-4f);
  const vf vmarg = V_SET1(margin);
  const vf v2m = V_SET1(2.0f * margin);
  const vf vone = V_SET1(1.0f);
  const vf vz = V_ZERO();
  const vf vmin = V_SET1(-32768.0f);
  const vf vmax = V_SET1(32767.0f);
  const vf vz_out = !(threshold > 0.f) ? vmin : vmax;
  vi parts[2];
  for(int h = 0; h < 2; h++){
    const int u = h * AP_W;
    const vf vd = qds_stride ? V_LOADU(qds + u) : V_SET1(qds[0]);
    const vf vt = V_LOADU(qts + u);
    const vf ds = V_MUL(vd, vinv);
    const vf eq = nomargin ? hn::IfThenElse(hn::Lt(V_MUL(ds, vt), v2m), vmarg, vz) : vmarg;
    const vf q = V_SUB(V_MUL(V_MUL(V_MUL(vthr, ds), vadj), vt), eq);
    const vf T = V_SUB(V_MUL(V_MUL(q, q), vinv), vone);
    vf r = hn::IfThenElse(hn::Ge(T, vmax), vmax, hn::Ceil(T));
    r = hn::IfThenElse(hn::Gt(q, vz), r, vmin);
    r = hn::IfThenElse(hn::Or(hn::Eq(vd, vz), hn::Eq(vt, vz)), vz_out, r);
    r = hn::IfThenElse(hn::Or(hn::Lt(vd, vz), hn::Lt(vt, vz)), vmin, r);
    parts[h] = hn::ConvertTo(AP_DI, r);
  }
  hn::StoreU(hn::OrderedDemote2To(AP_DQ, parts[0], parts[1]), AP_DQ, out);
}

#undef MF_Q15PREP_SECTION

}  // namespace HWY_NAMESPACE
}  // namespace ap
HWY_AFTER_NAMESPACE();

#endif
