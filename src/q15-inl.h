/* Q15 coarse screen: the pair-batched coarse transform in int16 fixed point.
 *
 * What it computes.  For QW (data, template) pairs at once -- lanes are
 * templates, twice as many as the float path's at the same vector width (or 8 / 16
 * VEX-encoded int16 lanes on AVX1, which has no 256-bit integer ALU) --
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
   dwords emits vpbroadcastd on AVX2 or vbroadcastss on AVX1 (one pure load uop on Sandy/Ivy
   Bridge and Haswell/Broadwell, zero Port-5 shuffle uops) instead of multi-uop word shuffles. */
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

[[maybe_unused]] static HWY_NOINLINE void q15_tw32_init_slow(void){
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

#undef Q_ZERO
#undef Q_SET1
#undef Q_DUP32
#undef Q_TWLOAD
#undef Q_LOADU
#undef Q_STOREU
#undef Q_ADD
#undef Q_SUB
#undef Q_ADDS
#undef Q_MUL
#undef Q_MAX
#undef Q_GT
#undef Q_LT
#undef Q_EQ
#undef Q_GE
#undef Q_MASK_OR
#undef Q_MASK_AND
#undef Q_SEL
#undef Q_DLOAD
#undef Q_TLOAD
#undef AP_Q15_USE_TW32
#undef AP_Q15_FUSED
#undef Q_MLAH
#undef Q_MLSH
#undef AP_Q15_TAIL

#if defined(AP_SIMD_AVX1)
/* VEX-encoded 128-bit integer SIMD for Sandy/Ivy Bridge (-mavx): 3-operand VEX instructions
   with zero AVX<->SSE transition penalties and single-uop vbroadcastss 32-bit loads.
   AP_AVX1_QW selects 8 lanes (single __m128i; measured faster across b=512, 1024 and sparse
   gather due to ~3x lower xmm stack spills per pair) or 16 lanes (paired __m128i lo, hi). */
#ifndef AP_AVX1_QW
#define AP_AVX1_QW 8
#endif
static_assert(AP_AVX1_QW == 8 || AP_AVX1_QW == 16, "AP_AVX1_QW must be 8 or 16");
constexpr int AP_QW = AP_AVX1_QW;
#define AP_Q15_USE_TW32 1
typedef int32_t qtw_elem;
typedef q15_twiddles32 qtw_table;

static HWY_INLINE __m128i avx1_bcast32(const int32_t &x){
  return _mm_castps_si128(_mm_broadcast_ss((const float *)&x));
}

#if AP_AVX1_QW == 8
struct vq { __m128i raw; };
typedef vq qmask;
#define Q_ZERO()         vq{_mm_setzero_si128()}
#define Q_SET1(x)        vq{_mm_set1_epi16((int16_t)(x))}
#define Q_DUP32(x)       vq{avx1_bcast32(x)}
#define Q_TWLOAD(x)      Q_DUP32(x)
#define Q_LOADU(p)       vq{_mm_loadu_si128((const __m128i *)(p))}
#define Q_STOREU(p, v)   _mm_storeu_si128((__m128i *)(p), (v).raw)
#define Q_ADD(a, b)      vq{_mm_add_epi16((a).raw, (b).raw)}
#define Q_SUB(a, b)      vq{_mm_sub_epi16((a).raw, (b).raw)}
#define Q_ADDS(a, b)     vq{_mm_adds_epi16((a).raw, (b).raw)}
#define Q_MUL(a, b)      vq{_mm_mulhrs_epi16((a).raw, (b).raw)}
#define Q_MAX(a, b)      vq{_mm_max_epi16((a).raw, (b).raw)}
#define Q_GT(a, b)       qmask{_mm_cmpgt_epi16((a).raw, (b).raw)}
#define Q_LT(a, b)       qmask{_mm_cmpgt_epi16((b).raw, (a).raw)}
#define Q_EQ(a, b)       qmask{_mm_cmpeq_epi16((a).raw, (b).raw)}
static HWY_INLINE qmask q15_ge_avx1(vq a, vq b){
  return qmask{_mm_cmpeq_epi16(_mm_max_epi16(a.raw, b.raw), a.raw)};
}
#define Q_GE(a, b)       q15_ge_avx1((a), (b))
#define Q_MASK_OR(a, b)  qmask{_mm_or_si128((a).raw, (b).raw)}
#define Q_MASK_AND(a, b) qmask{_mm_and_si128((a).raw, (b).raw)}
#define Q_SEL(m, t, f)   vq{_mm_blendv_epi8((f).raw, (t).raw, (m).raw)}
static HWY_INLINE uint64_t q15_mask_bits(qmask m){
  return (uint64_t)(unsigned)_mm_movemask_epi8(_mm_packs_epi16(m.raw, _mm_setzero_si128()));
}

struct ap_qidx_avx1 { __m128i s0, s1; };
typedef const ap_qidx_avx1 *qidx;
static HWY_INLINE void q15_make_dix_avx1(ap_qidx_avx1 *out, const int16_t *dsel){
  alignas(16) uint8_t b0[16];
  for(int l = 0; l < 8; l++){
    const uint8_t lo = (uint8_t)(2 * (dsel[l] & 7));
    b0[2 * l] = lo; b0[2 * l + 1] = (uint8_t)(lo + 1);
  }
  out->s0 = _mm_load_si128((const __m128i *)b0);
  out->s1 = _mm_setzero_si128();
}
static HWY_INLINE void q15_make_tix_avx1(ap_qidx_avx1 *out, const int16_t *tsel, long TW){
  alignas(16) uint8_t b0[16], b1[16];
  memset(b0, 0x80, 16); memset(b1, 0x80, 16);
  for(int l = 0; l < 8; l++){
    const int raw = tsel[l] & 15;
    const int idx = TW ? raw : (raw & 7);
    const uint8_t lo = (uint8_t)(2 * (idx & 7)), hi = (uint8_t)(lo + 1);
    if((idx >> 3) == 0){ b0[2 * l] = lo; b0[2 * l + 1] = hi; }
    else               { b1[2 * l] = lo; b1[2 * l + 1] = hi; }
  }
  out->s0 = _mm_load_si128((const __m128i *)b0);
  out->s1 = _mm_load_si128((const __m128i *)b1);
}
static HWY_INLINE vq q15_dload_avx1(const int16_t *p, const ap_qidx_avx1 *ix){
  return vq{_mm_shuffle_epi8(_mm_loadu_si128((const __m128i *)p), ix->s0)};
}
static HWY_INLINE vq q15_tload_avx1(const int16_t *p, long TW, const ap_qidx_avx1 *ix){
  const __m128i v0 = _mm_loadu_si128((const __m128i *)p);
  const __m128i v1 = _mm_loadu_si128((const __m128i *)(p + TW));
  return vq{_mm_or_si128(_mm_shuffle_epi8(v0, ix->s0), _mm_shuffle_epi8(v1, ix->s1))};
}
#define Q_DLOAD(p) q15_dload_avx1((p), dix)
#define Q_TLOAD(p) q15_tload_avx1((p), TW, tix)

#define AP_Q15_TAIL 1
template<int T> static HWY_INLINE vq q15_tile_template(const int16_t *p){
  if(T == 4) return vq{_mm_castpd_si128(_mm_loaddup_pd((const double *)p))};
  return vq{_mm_castps_si128(_mm_broadcast_ss((const float *)p))};
}
template<int T, long B> static HWY_INLINE vq q15_tile_data32(const int32_t *p){
  constexpr long HB = B / 2;
  if(T == 4) return vq{_mm_unpacklo_epi64(avx1_bcast32(p[0]), avx1_bcast32(p[HB]))};
  return vq{_mm_setr_epi32(p[0], p[HB], p[2 * HB], p[3 * HB])};
}
template<int T, long B> static HWY_INLINE vq q15_tile_data16(const int16_t *p){
  if(T == 4) return vq{_mm_unpacklo_epi64(_mm_set1_epi16(p[0]), _mm_set1_epi16(p[B]))};
  const int32_t d0 = (int32_t)((uint32_t)(uint16_t)p[0] * 0x00010001u);
  const int32_t d1 = (int32_t)((uint32_t)(uint16_t)p[B] * 0x00010001u);
  const int32_t d2 = (int32_t)((uint32_t)(uint16_t)p[2 * B] * 0x00010001u);
  const int32_t d3 = (int32_t)((uint32_t)(uint16_t)p[3 * B] * 0x00010001u);
  return vq{_mm_setr_epi32(d0, d1, d2, d3)};
}

#else /* AP_AVX1_QW == 16 */
struct vq { __m128i lo, hi; };
typedef vq qmask;
static HWY_INLINE vq avx1_dup32_16(const int32_t &x){
  const __m128i b = avx1_bcast32(x);
  return vq{b, b};
}
static HWY_INLINE vq avx1_set1_16(int16_t x){
  const __m128i b = _mm_set1_epi16(x);
  return vq{b, b};
}
static HWY_INLINE vq avx1_loadu_16(const int16_t *p){
  return vq{_mm_loadu_si128((const __m128i *)p), _mm_loadu_si128((const __m128i *)(p + 8))};
}
static HWY_INLINE void avx1_storeu_16(int16_t *p, vq v){
  _mm_storeu_si128((__m128i *)p, v.lo);
  _mm_storeu_si128((__m128i *)(p + 8), v.hi);
}
static HWY_INLINE vq avx1_add_16(vq a, vq b){ return vq{_mm_add_epi16(a.lo, b.lo), _mm_add_epi16(a.hi, b.hi)}; }
static HWY_INLINE vq avx1_sub_16(vq a, vq b){ return vq{_mm_sub_epi16(a.lo, b.lo), _mm_sub_epi16(a.hi, b.hi)}; }
static HWY_INLINE vq avx1_adds_16(vq a, vq b){ return vq{_mm_adds_epi16(a.lo, b.lo), _mm_adds_epi16(a.hi, b.hi)}; }
static HWY_INLINE vq avx1_mul_16(vq a, vq b){ return vq{_mm_mulhrs_epi16(a.lo, b.lo), _mm_mulhrs_epi16(a.hi, b.hi)}; }
static HWY_INLINE vq avx1_max_16(vq a, vq b){ return vq{_mm_max_epi16(a.lo, b.lo), _mm_max_epi16(a.hi, b.hi)}; }
static HWY_INLINE qmask avx1_gt_16(vq a, vq b){ return qmask{_mm_cmpgt_epi16(a.lo, b.lo), _mm_cmpgt_epi16(a.hi, b.hi)}; }
static HWY_INLINE qmask avx1_eq_16(vq a, vq b){ return qmask{_mm_cmpeq_epi16(a.lo, b.lo), _mm_cmpeq_epi16(a.hi, b.hi)}; }
static HWY_INLINE qmask avx1_ge_16(vq a, vq b){
  return qmask{_mm_cmpeq_epi16(_mm_max_epi16(a.lo, b.lo), a.lo),
               _mm_cmpeq_epi16(_mm_max_epi16(a.hi, b.hi), a.hi)};
}
static HWY_INLINE qmask avx1_or_16(qmask a, qmask b){ return qmask{_mm_or_si128(a.lo, b.lo), _mm_or_si128(a.hi, b.hi)}; }
static HWY_INLINE qmask avx1_and_16(qmask a, qmask b){ return qmask{_mm_and_si128(a.lo, b.lo), _mm_and_si128(a.hi, b.hi)}; }
static HWY_INLINE vq avx1_sel_16(qmask m, vq t, vq f){
  return vq{_mm_blendv_epi8(f.lo, t.lo, m.lo), _mm_blendv_epi8(f.hi, t.hi, m.hi)};
}
static HWY_INLINE uint64_t q15_mask_bits(qmask m){
  return (uint64_t)(unsigned)_mm_movemask_epi8(_mm_packs_epi16(m.lo, m.hi));
}
#define Q_ZERO()         vq{_mm_setzero_si128(), _mm_setzero_si128()}
#define Q_SET1(x)        avx1_set1_16((int16_t)(x))
#define Q_DUP32(x)       avx1_dup32_16(x)
#define Q_TWLOAD(x)      Q_DUP32(x)
#define Q_LOADU(p)       avx1_loadu_16((const int16_t *)(p))
#define Q_STOREU(p, v)   avx1_storeu_16((int16_t *)(p), (v))
#define Q_ADD(a, b)      avx1_add_16((a), (b))
#define Q_SUB(a, b)      avx1_sub_16((a), (b))
#define Q_ADDS(a, b)     avx1_adds_16((a), (b))
#define Q_MUL(a, b)      avx1_mul_16((a), (b))
#define Q_MAX(a, b)      avx1_max_16((a), (b))
#define Q_GT(a, b)       avx1_gt_16((a), (b))
#define Q_LT(a, b)       avx1_gt_16((b), (a))
#define Q_EQ(a, b)       avx1_eq_16((a), (b))
#define Q_GE(a, b)       avx1_ge_16((a), (b))
#define Q_MASK_OR(a, b)  avx1_or_16((a), (b))
#define Q_MASK_AND(a, b) avx1_and_16((a), (b))
#define Q_SEL(m, t, f)   avx1_sel_16((m), (t), (f))

struct ap_qidx_avx1 { __m128i lo[4], hi[4]; };
typedef const ap_qidx_avx1 *qidx;
static HWY_INLINE void q15_make_dix_avx1(ap_qidx_avx1 *out, const int16_t *dsel){
  for(int h = 0; h < 2; h++){
    alignas(16) uint8_t b0[16], b1[16];
    memset(b0, 0x80, 16); memset(b1, 0x80, 16);
    for(int l = 0; l < 8; l++){
      const int idx = dsel[8 * h + l] & 15;
      const uint8_t lo = (uint8_t)(2 * (idx & 7)), hi = (uint8_t)(lo + 1);
      if((idx >> 3) == 0){ b0[2 * l] = lo; b0[2 * l + 1] = hi; }
      else               { b1[2 * l] = lo; b1[2 * l + 1] = hi; }
    }
    if(h == 0){ out->lo[0] = _mm_load_si128((const __m128i *)b0); out->lo[1] = _mm_load_si128((const __m128i *)b1); }
    else      { out->hi[0] = _mm_load_si128((const __m128i *)b0); out->hi[1] = _mm_load_si128((const __m128i *)b1); }
  }
}
static HWY_INLINE void q15_make_tix_avx1(ap_qidx_avx1 *out, const int16_t *tsel, long TW){
  for(int h = 0; h < 2; h++){
    alignas(16) uint8_t b[4][16];
    memset(b, 0x80, sizeof b);
    for(int l = 0; l < 8; l++){
      const int raw = tsel[8 * h + l] & 31;
      const int idx = TW ? raw : (raw & 15);
      const uint8_t lo = (uint8_t)(2 * (idx & 7)), hi = (uint8_t)(lo + 1);
      b[idx >> 3][2 * l] = lo; b[idx >> 3][2 * l + 1] = hi;
    }
    for(int c = 0; c < 4; c++){
      const __m128i m = _mm_load_si128((const __m128i *)b[c]);
      if(h == 0) out->lo[c] = m; else out->hi[c] = m;
    }
  }
}
static HWY_INLINE vq q15_dload_avx1(const int16_t *p, const ap_qidx_avx1 *ix){
  const __m128i v0 = _mm_loadu_si128((const __m128i *)p);
  const __m128i v1 = _mm_loadu_si128((const __m128i *)(p + 8));
  return vq{_mm_or_si128(_mm_shuffle_epi8(v0, ix->lo[0]), _mm_shuffle_epi8(v1, ix->lo[1])),
            _mm_or_si128(_mm_shuffle_epi8(v0, ix->hi[0]), _mm_shuffle_epi8(v1, ix->hi[1]))};
}
static HWY_INLINE vq q15_tload_avx1(const int16_t *p, long TW, const ap_qidx_avx1 *ix){
  const __m128i v0 = _mm_loadu_si128((const __m128i *)p);
  const __m128i v1 = _mm_loadu_si128((const __m128i *)(p + 8));
  const __m128i v2 = _mm_loadu_si128((const __m128i *)(p + TW));
  const __m128i v3 = _mm_loadu_si128((const __m128i *)(p + TW + 8));
  const __m128i lo = _mm_or_si128(_mm_or_si128(_mm_shuffle_epi8(v0, ix->lo[0]), _mm_shuffle_epi8(v1, ix->lo[1])),
                                  _mm_or_si128(_mm_shuffle_epi8(v2, ix->lo[2]), _mm_shuffle_epi8(v3, ix->lo[3])));
  const __m128i hi = _mm_or_si128(_mm_or_si128(_mm_shuffle_epi8(v0, ix->hi[0]), _mm_shuffle_epi8(v1, ix->hi[1])),
                                  _mm_or_si128(_mm_shuffle_epi8(v2, ix->hi[2]), _mm_shuffle_epi8(v3, ix->hi[3])));
  return vq{lo, hi};
}
#define Q_DLOAD(p) q15_dload_avx1((p), dix)
#define Q_TLOAD(p) q15_tload_avx1((p), TW, tix)

#define AP_Q15_TAIL 1
template<int T> static HWY_INLINE vq q15_tile_template(const int16_t *p){
  if(T == 8){
    const __m128i v = _mm_loadu_si128((const __m128i *)p);
    return vq{v, v};
  }
  const __m128i v = _mm_castpd_si128(_mm_loaddup_pd((const double *)p));
  return vq{v, v};
}
template<int T, long B> static HWY_INLINE vq q15_tile_data32(const int32_t *p){
  constexpr long HB = B / 2;
  if(T == 8) return vq{avx1_bcast32(p[0]), avx1_bcast32(p[HB])};
  return vq{_mm_unpacklo_epi64(avx1_bcast32(p[0]), avx1_bcast32(p[HB])),
            _mm_unpacklo_epi64(avx1_bcast32(p[2 * HB]), avx1_bcast32(p[3 * HB]))};
}
template<int T, long B> static HWY_INLINE vq q15_tile_data16(const int16_t *p){
  if(T == 8) return vq{_mm_set1_epi16(p[0]), _mm_set1_epi16(p[B])};
  return vq{_mm_unpacklo_epi64(_mm_set1_epi16(p[0]), _mm_set1_epi16(p[B])),
            _mm_unpacklo_epi64(_mm_set1_epi16(p[2 * B]), _mm_set1_epi16(p[3 * B]))};
}
#endif /* AP_AVX1_QW */

#define AP_Q15_FUSED 0
#define Q_MLAH(acc, a, b) Q_ADD((acc), Q_MUL((a), (b)))
#define Q_MLSH(acc, a, b) Q_SUB((acc), Q_MUL((a), (b)))

#else /* Highway targets */

using ap_qtag = hn::CappedTag<int16_t, 2 * AP_W>;
using ap_qditag = hn::Repartition<int32_t, ap_qtag>;
constexpr ap_qtag AP_DQ{};
constexpr ap_qditag AP_QDI{};
constexpr int AP_QW = (int)HWY_MAX_LANES_D(ap_qtag);
typedef hn::Vec<ap_qtag> vq;
typedef hn::Mask<ap_qtag> qmask;

#define Q_ZERO()         hn::Zero(AP_DQ)
#define Q_SET1(x)        hn::Set(AP_DQ, (int16_t)(x))
#define Q_DUP32(x)       hn::BitCast(AP_DQ, hn::Set(AP_QDI, (int32_t)(x)))
#define Q_LOADU(p)       hn::LoadU(AP_DQ, (const int16_t *)(p))
#define Q_STOREU(p, v)   hn::StoreU((v), AP_DQ, (int16_t *)(p))
#define Q_ADD(a, b)      hn::Add((a), (b))
#define Q_SUB(a, b)      hn::Sub((a), (b))
#define Q_ADDS(a, b)     hn::SaturatedAdd((a), (b))
#define Q_MUL(a, b)      hn::MulFixedPoint15((a), (b))
#define Q_MAX(a, b)      hn::Max((a), (b))
#define Q_GT(a, b)       hn::Gt((a), (b))
#define Q_LT(a, b)       hn::Lt((a), (b))
#define Q_EQ(a, b)       hn::Eq((a), (b))
#define Q_GE(a, b)       hn::Ge((a), (b))
#define Q_MASK_OR(a, b)  hn::Or((a), (b))
#define Q_MASK_AND(a, b) hn::And((a), (b))
#define Q_SEL(m, t, f)   hn::IfThenElse((m), (t), (f))
static HWY_INLINE uint64_t q15_mask_bits(qmask m){
  uint64_t b = 0;
  hn::StoreMaskBits(AP_DQ, m, (uint8_t *)&b);
  return b;
}

#if HWY_ARCH_X86 && HWY_MAX_BYTES == 32
#define AP_Q15_USE_TW32 1
typedef int32_t qtw_elem;
typedef q15_twiddles32 qtw_table;
#define Q_TWLOAD(x)      Q_DUP32(x)
#else
#define AP_Q15_USE_TW32 0
typedef int16_t qtw_elem;
typedef ap_q15_twiddles qtw_table;
#define Q_TWLOAD(x)      Q_SET1(x)
#endif

/* Listed pairs (q15_screen_perm): each lane's operands are looked up in a vector of one element
   across QW data blocks (dix) and across two groups of QW templates (tix, the second group TW
   further on). On AVX2, precomputed vpshufb byte masks replace Highway's multi-instruction
   cross-lane int16 table lookup inside every codelet load. */
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

#endif /* AP_SIMD_AVX1 */

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

#if !AP_Q15_USE_TW32
static HWY_NOINLINE void q15_tw16_init_slow(int *ready){
  (void)ap_q15_twiddle_table(64);
  __atomic_store_n(ready, 1, __ATOMIC_RELEASE);
}
#endif

template<int IDX>
static HWY_INLINE const qtw_table *q15_tw_fast(void){
#if AP_Q15_USE_TW32
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
  const vq vneg1 = Q_SET1(-1), vstep = Q_SET1(2 * M2);
  vq m0 = vneg1, m1 = vneg1, ix0 = Q_SET1(32767), ix1 = Q_SET1(32767);
  const size_t wso = ws + (size_t)(M2 - 1), weo = we + (size_t)(M2 - 1);
  for(size_t k2 = 0; k2 < (size_t)M2; k2++){
    const long lo = (long)((wso - k2) / (size_t)M2);
    const long hi = (long)((weo - k2) / (size_t)M2);
    if(lo >= hi) continue;
    vq *xr = X + k2 * st, *xi = Xi + k2 * st;
    qcodelet_tw(M1, xr, xi, 1, tw->re + k2 * (size_t)M1, tw->im + k2 * (size_t)M1);
    long k1 = lo;
    vq j0 = Q_SET1((int)k2 + M2 * (int)lo);
    vq j1 = Q_SET1((int)k2 + M2 * (int)(lo + 1));
    for(; k1 + 1 < hi; k1 += 2){
      const vq a = xr[k1], b = xi[k1], c = xr[k1 + 1], d = xi[k1 + 1];
      const vq s0 = Q_ADDS(Q_MUL(a, a), Q_MUL(b, b));
      const vq s1 = Q_ADDS(Q_MUL(c, c), Q_MUL(d, d));
      const qmask u0 = Q_MASK_OR(Q_GT(s0, m0), Q_MASK_AND(Q_EQ(s0, m0), Q_LT(j0, ix0)));
      const qmask u1 = Q_MASK_OR(Q_GT(s1, m1), Q_MASK_AND(Q_EQ(s1, m1), Q_LT(j1, ix1)));
      m0 = Q_MAX(m0, s0);
      m1 = Q_MAX(m1, s1);
      ix0 = Q_SEL(u0, j0, ix0);
      ix1 = Q_SEL(u1, j1, ix1);
      j0 = Q_ADD(j0, vstep);
      j1 = Q_ADD(j1, vstep);
    }
    if(k1 < hi){
      const vq a = xr[k1], b = xi[k1];
      const vq s0 = Q_ADDS(Q_MUL(a, a), Q_MUL(b, b));
      const qmask u0 = Q_MASK_OR(Q_GT(s0, m0), Q_MASK_AND(Q_EQ(s0, m0), Q_LT(j0, ix0)));
      m0 = Q_MAX(m0, s0);
      ix0 = Q_SEL(u0, j0, ix0);
    }
  }
  const qmask u1 = Q_MASK_OR(Q_GT(m1, m0), Q_MASK_AND(Q_EQ(m1, m0), Q_LT(ix1, ix0)));
  const vq mx_raw = Q_MAX(m0, m1);
  const vq ix = Q_SEL(Q_GT(mx_raw, vneg1), Q_SEL(u1, ix1, ix0), vneg1);
  Q_STOREU(laneidx, ix);
  const vq mx = Q_MAX(mx_raw, Q_ZERO());
  if(lanemax) Q_STOREU(lanemax, mx);
  *bits = q15_mask_bits(Q_GE(mx, Q_LOADU(lanethr)));
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
  const vq mx = Q_MAX(mm[0], mm[1]);
  if(lanemax) Q_STOREU(lanemax, mx);
  *bits = q15_mask_bits(Q_GE(mx, Q_LOADU(lanethr)));
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
  vq *X = (vq *)scratch, *Xi = X + (size_t)(M1 + 1) * M2;
  q15_prod_n<M1, M2>(dq, tr, ti, X, Xi);
  const qtw_table *tw = q15_tw_fast<IDX>();
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
#if defined(AP_SIMD_AVX1)
  ap_qidx_avx1 dix_s, tix_s;
  q15_make_dix_avx1(&dix_s, dsel);
  q15_make_tix_avx1(&tix_s, tsel, TW);
  const qidx dix = &dix_s, tix = &tix_s;
#elif HWY_TARGET == HWY_AVX2
  ap_qidx_avx2 dix_s, tix_s;
  q15_make_dix_avx2(&dix_s, dsel);
  q15_make_tix_avx2(&tix_s, tsel, TW);
  const qidx dix = &dix_s, tix = &tix_s;
#else
  const qidx dix = hn::SetTableIndices(AP_DQ, dsel), tix = hn::SetTableIndices(AP_DQ, tsel);
#endif
  vq *X = (vq *)scratch, *Xi = X + (size_t)(M1 + 1) * M2;
  q15_prod_perm_n<M1, M2>(dr, di, tr, ti, TW, dix, tix, X, Xi);
  const qtw_table *tw = q15_tw_fast<IDX>();
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
#if defined(AP_SIMD_AVX1) || (HWY_ARCH_X86 && HWY_MAX_BYTES >= 32)
static HWY_INLINE void q15_transpose8_128(__m128i r[8]){
  __m128i t[8], u[8];
  for(int j = 0; j < 4; j++){
    t[2 * j]     = _mm_unpacklo_epi16(r[2 * j], r[2 * j + 1]);
    t[2 * j + 1] = _mm_unpackhi_epi16(r[2 * j], r[2 * j + 1]);
  }
  for(int h = 0; h < 2; h++){
    for(int j = 0; j < 2; j++){
      u[4 * h + 2 * j]     = _mm_unpacklo_epi32(t[4 * h + j], t[4 * h + j + 2]);
      u[4 * h + 2 * j + 1] = _mm_unpackhi_epi32(t[4 * h + j], t[4 * h + j + 2]);
    }
  }
  for(int j = 0; j < 4; j++){
    r[2 * j]     = _mm_unpacklo_epi64(u[j], u[4 + j]);
    r[2 * j + 1] = _mm_unpackhi_epi64(u[j], u[4 + j]);
  }
}
#endif

#if !defined(AP_SIMD_AVX1)
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
#endif

template<int M1>
static HWY_INLINE void q15_store_block_col(const vq *pbuf, int pstride, int dv,
                                           size_t k_base, vq *X){
  constexpr size_t st = (size_t)(M1 + 1);
  /* k_base is a multiple of AP_QW (hence of 8), and M1 >= 8 is a power of two, so each
     8-element group lands in one contiguous slice of row (k / M1) without crossing M1. */
#if defined(AP_SIMD_AVX1)
#if AP_AVX1_QW == 8
  __m128i u[8];
  for(int l = 0; l < 8; l++)
    u[l] = pbuf[(size_t)l * (size_t)pstride + (size_t)dv].raw;
  q15_transpose8_128(u);
  vq *dst0 = X + (k_base & (size_t)(M1 - 1)) + st * (k_base / (size_t)M1);
  for(int m = 0; m < 8; m++) dst0[m] = vq{u[m]};
#else
  __m128i q0[8], q1[8];
  for(int l = 0; l < 8; l++) q0[l] = pbuf[(size_t)l * (size_t)pstride + (size_t)dv].lo;
  q15_transpose8_128(q0);
  for(int l = 0; l < 8; l++) q1[l] = pbuf[(size_t)(8 + l) * (size_t)pstride + (size_t)dv].lo;
  q15_transpose8_128(q1);
  vq *dst0 = X + (k_base & (size_t)(M1 - 1)) + st * (k_base / (size_t)M1);
  for(int m = 0; m < 8; m++) dst0[m] = vq{q0[m], q1[m]};

  for(int l = 0; l < 8; l++) q0[l] = pbuf[(size_t)l * (size_t)pstride + (size_t)dv].hi;
  q15_transpose8_128(q0);
  for(int l = 0; l < 8; l++) q1[l] = pbuf[(size_t)(8 + l) * (size_t)pstride + (size_t)dv].hi;
  q15_transpose8_128(q1);
  const size_t k1 = k_base + 8;
  vq *dst1 = X + (k1 & (size_t)(M1 - 1)) + st * (k1 / (size_t)M1);
  for(int m = 0; m < 8; m++) dst1[m] = vq{q0[m], q1[m]};
#endif
#elif HWY_ARCH_X86 && HWY_MAX_BYTES == 64
  vq u0[8], u1[8];
  for(int j = 0; j < 8; j++) u0[j] = pbuf[(size_t)j * (size_t)pstride + (size_t)dv];
  q15_transpose8_inlane(u0);
  for(int j = 0; j < 8; j++) u1[j] = pbuf[(size_t)(8 + j) * (size_t)pstride + (size_t)dv];
  q15_transpose8_inlane(u1);
  __m512i ab_01[8], ab_23[8];
  for(int m = 0; m < 8; m++){
    ab_01[m] = _mm512_shuffle_i32x4(u0[m].raw, u1[m].raw, 0x44);
    ab_23[m] = _mm512_shuffle_i32x4(u0[m].raw, u1[m].raw, 0xEE);
  }
  vq u2[8], u3[8];
  for(int j = 0; j < 8; j++) u2[j] = pbuf[(size_t)(16 + j) * (size_t)pstride + (size_t)dv];
  q15_transpose8_inlane(u2);
  for(int j = 0; j < 8; j++) u3[j] = pbuf[(size_t)(24 + j) * (size_t)pstride + (size_t)dv];
  q15_transpose8_inlane(u3);
  const size_t k1 = k_base + 8, k2 = k_base + 16, k3 = k_base + 24;
  vq *dst0 = X + (k_base & (size_t)(M1 - 1)) + st * (k_base / (size_t)M1);
  vq *dst1 = X + (k1 & (size_t)(M1 - 1)) + st * (k1 / (size_t)M1);
  vq *dst2 = X + (k2 & (size_t)(M1 - 1)) + st * (k2 / (size_t)M1);
  vq *dst3 = X + (k3 & (size_t)(M1 - 1)) + st * (k3 / (size_t)M1);
  for(int m = 0; m < 8; m++){
    const __m512i cd_01 = _mm512_shuffle_i32x4(u2[m].raw, u3[m].raw, 0x44);
    const __m512i cd_23 = _mm512_shuffle_i32x4(u2[m].raw, u3[m].raw, 0xEE);
    dst0[m] = vq{_mm512_shuffle_i32x4(ab_01[m], cd_01, 0x88)};
    dst1[m] = vq{_mm512_shuffle_i32x4(ab_01[m], cd_01, 0xDD)};
    dst2[m] = vq{_mm512_shuffle_i32x4(ab_23[m], cd_23, 0x88)};
    dst3[m] = vq{_mm512_shuffle_i32x4(ab_23[m], cd_23, 0xDD)};
  }
#elif HWY_ARCH_X86 && HWY_MAX_BYTES == 32 && HWY_TARGET <= HWY_AVX2
  /* Transpose u0 before loading u1 so u1[0..7] never occupies 8 of AVX2's 16 ymm registers
     across u0's in-lane transpose. */
  vq u0[8], u1[8];
  for(int j = 0; j < 8; j++) u0[j] = pbuf[(size_t)j * (size_t)pstride + (size_t)dv];
  q15_transpose8_inlane(u0);
  for(int j = 0; j < 8; j++) u1[j] = pbuf[(size_t)(8 + j) * (size_t)pstride + (size_t)dv];
  q15_transpose8_inlane(u1);
  const size_t k1 = k_base + 8;
  vq *dst0 = X + (k_base & (size_t)(M1 - 1)) + st * (k_base / (size_t)M1);
  vq *dst1 = X + (k1 & (size_t)(M1 - 1)) + st * (k1 / (size_t)M1);
  for(int m = 0; m < 8; m++){
    dst0[m] = vq{_mm256_permute2x128_si256(u0[m].raw, u1[m].raw, 0x20)};
    dst1[m] = vq{_mm256_permute2x128_si256(u0[m].raw, u1[m].raw, 0x31)};
  }
#elif AP_QW == 8
  vq u[8];
  for(int l = 0; l < 8; l++)
    u[l] = pbuf[(size_t)l * (size_t)pstride + (size_t)dv];
  q15_transpose8_inlane(u);
  vq *dst0 = X + (k_base & (size_t)(M1 - 1)) + st * (k_base / (size_t)M1);
  for(int m = 0; m < 8; m++) dst0[m] = u[m];
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
    for(int l = 0; l < AP_QW;){
      /* Load a data block's tile once and keep it in registers across the whole run of
         consecutive survivor pairs from that block (such as the members expanded from a
         firing centroid), which the caller's (block, template) order makes contiguous. */
      const int16_t *dr0 = drp[l];
      int run_end = l + 1;
      while(run_end < AP_QW && drp[run_end] == dr0) run_end++;
      const int16_t *drl = dr0 + k_tile;
      const int16_t *dil = dip[l] + k_tile;
      vq dR[VB], dI[VB];
      for(int dv = 0; dv < VB; dv++){
        dR[dv] = Q_LOADU(drl + (size_t)dv * (size_t)AP_QW);
        dI[dv] = Q_LOADU(dil + (size_t)dv * (size_t)AP_QW);
      }
      for(; l < run_end; l++){
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

template<int M1, int M2>
static HWY_INLINE void q15_row_lag_step(const qtw_table *tw, size_t k2,
                                        vq *xr, vq *xi, long lo, long hi,
                                        vq *m0p, vq *m1p, vq *ix0p, vq *ix1p){
  const vq vstep = Q_SET1(2 * M2);
  vq m0 = *m0p, m1 = *m1p, ix0 = *ix0p, ix1 = *ix1p;
  qcodelet_tw(M1, xr, xi, 1, tw->re + k2 * (size_t)M1, tw->im + k2 * (size_t)M1);
  long k1 = lo;
  vq j0 = Q_SET1((int)k2 + M2 * (int)lo);
  vq j1 = Q_SET1((int)k2 + M2 * (int)(lo + 1));
  for(; k1 + 1 < hi; k1 += 2){
    const vq a = xr[k1], b = xi[k1], c = xr[k1 + 1], d = xi[k1 + 1];
    const vq s0 = Q_ADDS(Q_MUL(a, a), Q_MUL(b, b));
    const vq s1 = Q_ADDS(Q_MUL(c, c), Q_MUL(d, d));
    const qmask u0 = Q_MASK_OR(Q_GT(s0, m0), Q_MASK_AND(Q_EQ(s0, m0), Q_LT(j0, ix0)));
    const qmask u1 = Q_MASK_OR(Q_GT(s1, m1), Q_MASK_AND(Q_EQ(s1, m1), Q_LT(j1, ix1)));
    m0 = Q_MAX(m0, s0);
    m1 = Q_MAX(m1, s1);
    ix0 = Q_SEL(u0, j0, ix0);
    ix1 = Q_SEL(u1, j1, ix1);
    j0 = Q_ADD(j0, vstep);
    j1 = Q_ADD(j1, vstep);
  }
  if(k1 < hi){
    const vq a = xr[k1], b = xi[k1];
    const vq s0 = Q_ADDS(Q_MUL(a, a), Q_MUL(b, b));
    const qmask u0 = Q_MASK_OR(Q_GT(s0, m0), Q_MASK_AND(Q_EQ(s0, m0), Q_LT(j0, ix0)));
    m0 = Q_MAX(m0, s0);
    ix0 = Q_SEL(u0, j0, ix0);
  }
  *m0p = m0; *m1p = m1; *ix0p = ix0; *ix1p = ix1;
}

template<int M1, int MODE>
static HWY_INLINE void q15_row_twmax_step(const qtw_table *tw, size_t k2,
                                          const vq *xr, const vq *xi,
                                          long lo, long hi, vq *mm){
  const qtw_elem *twr = tw->re + k2 * (size_t)M1;
  const qtw_elem *twi = tw->im + k2 * (size_t)M1;
  if constexpr (M1 == 8) {
    if constexpr (MODE == 0) qsr8_twmax_middle(xr, xi, 1, twr, twi, lo, hi, mm);
    else                     qsr8_twmax(xr, xi, 1, twr, twi, lo, hi, mm);
  } else if constexpr (M1 == 16) {
    if constexpr (MODE == 0)      qsr16_twmax_middle(xr, xi, 1, twr, twi, lo, hi, mm);
    else if constexpr (MODE == 1) qsr16_twmax_wide(xr, xi, 1, twr, twi, lo, hi, mm);
    else                          qsr16_twmax(xr, xi, 1, twr, twi, lo, hi, mm);
  } else {
    if constexpr (MODE == 0)      qsr32_twmax_middle(xr, xi, 1, twr, twi, lo, hi, mm);
    else if constexpr (MODE == 1) qsr32_twmax_wide(xr, xi, 1, twr, twi, lo, hi, mm);
    else                          qsr32_twmax(xr, xi, 1, twr, twi, lo, hi, mm);
  }
}

template<int M1, int M2>
static HWY_INLINE int q15_win_mode(size_t ws, size_t we){
  if constexpr (M1 == 8) {
    return (ws <= 2 * (size_t)M2 && we >= 6 * (size_t)M2) ? 0 : 2;
  } else if constexpr (M1 == 16) {
    if(ws <= 2 * (size_t)M2 && we >= 14 * (size_t)M2) return 0;
    if(ws <= 4 * (size_t)M2 && we >= 12 * (size_t)M2) return 1;
    return 2;
  } else {
    if(ws <= 4 * (size_t)M2 && we >= 28 * (size_t)M2) return 0;
    if(ws <= 8 * (size_t)M2 && we >= 24 * (size_t)M2) return 1;
    return 2;
  }
}

/* On 32-lane AVX-512 at M1 == 32 (N = 512, 1024), X + Xi would occupy 68-135 KB and
   spill out of L1D three times. Running Pass-1 qcodelet(M2) per lane before corner-turn
   and transposing one active k2 row at a time into a 4 KB stack row buffer keeps Pass 2
   100% L1D-resident with bit-identical Q15 rounding. */
template<int IDX, int M1, int M2>
static HWY_NOINLINE int q15_screen_gather_row_fused_n(
    const int16_t *const *drp, const int16_t *const *dip,
    const int16_t *const *trp, const int16_t *const *tip,
    int cnt, size_t ws, size_t we, const int16_t *lanethr,
    uint64_t *bits, int16_t *lanemax, int16_t *laneidx){
  constexpr size_t N = (size_t)M1 * (size_t)M2;
  if(we > N) we = N;
  constexpr int PSTRIDE = (M2 & 1) ? M2 : (M2 + 1);
  alignas(64) vq pbuf_r[AP_QW * PSTRIDE];
  alignas(64) vq pbuf_i[AP_QW * PSTRIDE];
  for(int l = 0; l < cnt;){
    const int16_t *dr0 = drp[l], *di0 = dip[l];
    /* Share dR/dI in registers across consecutive survivor pairs from the same data block
       (such as members expanded from a firing Tier-0 centroid). */
    if(l + 3 < cnt && drp[l + 1] == dr0 && drp[l + 2] == dr0 && drp[l + 3] == dr0){
      if(l + 5 < cnt){
        __builtin_prefetch(trp[l + 4], 0, 1);
        __builtin_prefetch(tip[l + 4], 0, 1);
      }
      const int16_t *tr0 = trp[l], *ti0 = tip[l];
      const int16_t *tr1 = trp[l + 1], *ti1 = tip[l + 1];
      const int16_t *tr2 = trp[l + 2], *ti2 = tip[l + 2];
      const int16_t *tr3 = trp[l + 3], *ti3 = tip[l + 3];
      vq *pr0 = pbuf_r + (size_t)l * PSTRIDE, *pi0 = pbuf_i + (size_t)l * PSTRIDE;
      vq *pr1 = pr0 + PSTRIDE, *pi1 = pi0 + PSTRIDE;
      vq *pr2 = pr1 + PSTRIDE, *pi2 = pi1 + PSTRIDE;
      vq *pr3 = pr2 + PSTRIDE, *pi3 = pi2 + PSTRIDE;
      for(int e2 = 0; e2 < M2; e2++){
        const size_t off = (size_t)e2 * (size_t)M1;
        const vq dR = Q_LOADU(dr0 + off), dI = Q_LOADU(di0 + off);
        const vq tR0 = Q_LOADU(tr0 + off), tI0 = Q_LOADU(ti0 + off);
        pr0[e2] = Q_MLSH(Q_MUL(dR, tR0), dI, tI0);
        pi0[e2] = Q_MLAH(Q_MUL(dR, tI0), dI, tR0);
        const vq tR1 = Q_LOADU(tr1 + off), tI1 = Q_LOADU(ti1 + off);
        pr1[e2] = Q_MLSH(Q_MUL(dR, tR1), dI, tI1);
        pi1[e2] = Q_MLAH(Q_MUL(dR, tI1), dI, tR1);
        const vq tR2 = Q_LOADU(tr2 + off), tI2 = Q_LOADU(ti2 + off);
        pr2[e2] = Q_MLSH(Q_MUL(dR, tR2), dI, tI2);
        pi2[e2] = Q_MLAH(Q_MUL(dR, tI2), dI, tR2);
        const vq tR3 = Q_LOADU(tr3 + off), tI3 = Q_LOADU(ti3 + off);
        pr3[e2] = Q_MLSH(Q_MUL(dR, tR3), dI, tI3);
        pi3[e2] = Q_MLAH(Q_MUL(dR, tI3), dI, tR3);
      }
      for(int u = 0; u < 4; u++)
        qcodelet(M2, pbuf_r + (size_t)(l + u) * PSTRIDE, pbuf_i + (size_t)(l + u) * PSTRIDE, 1);
      l += 4;
      continue;
    }
    if(l + 1 < cnt && drp[l + 1] == dr0){
      if(l + 3 < cnt){
        __builtin_prefetch(trp[l + 2], 0, 1);
        __builtin_prefetch(tip[l + 2], 0, 1);
      }
      const int16_t *tr0 = trp[l], *ti0 = tip[l];
      const int16_t *tr1 = trp[l + 1], *ti1 = tip[l + 1];
      vq *pr0 = pbuf_r + (size_t)l * PSTRIDE, *pi0 = pbuf_i + (size_t)l * PSTRIDE;
      vq *pr1 = pr0 + PSTRIDE, *pi1 = pi0 + PSTRIDE;
      for(int e2 = 0; e2 < M2; e2++){
        const size_t off = (size_t)e2 * (size_t)M1;
        const vq dR = Q_LOADU(dr0 + off), dI = Q_LOADU(di0 + off);
        const vq tR0 = Q_LOADU(tr0 + off), tI0 = Q_LOADU(ti0 + off);
        pr0[e2] = Q_MLSH(Q_MUL(dR, tR0), dI, tI0);
        pi0[e2] = Q_MLAH(Q_MUL(dR, tI0), dI, tR0);
        const vq tR1 = Q_LOADU(tr1 + off), tI1 = Q_LOADU(ti1 + off);
        pr1[e2] = Q_MLSH(Q_MUL(dR, tR1), dI, tI1);
        pi1[e2] = Q_MLAH(Q_MUL(dR, tI1), dI, tR1);
      }
      qcodelet(M2, pr0, pi0, 1);
      qcodelet(M2, pr1, pi1, 1);
      l += 2;
      continue;
    }
    if(l + 2 < cnt){
      __builtin_prefetch(trp[l + 2], 0, 1);
      __builtin_prefetch(tip[l + 2], 0, 1);
    }
    const int16_t *tr0 = trp[l], *ti0 = tip[l];
    vq *pr = pbuf_r + (size_t)l * PSTRIDE;
    vq *pi = pbuf_i + (size_t)l * PSTRIDE;
    for(int e2 = 0; e2 < M2; e2++){
      const size_t off = (size_t)e2 * (size_t)M1;
      const vq dR = Q_LOADU(dr0 + off), dI = Q_LOADU(di0 + off);
      const vq tR = Q_LOADU(tr0 + off), tI = Q_LOADU(ti0 + off);
      pr[e2] = Q_MLSH(Q_MUL(dR, tR), dI, tI);
      pi[e2] = Q_MLAH(Q_MUL(dR, tI), dI, tR);
    }
    qcodelet(M2, pr, pi, 1);
    l++;
  }
  for(int lp = cnt; lp < AP_QW; lp++){
    memcpy(pbuf_r + (size_t)lp * PSTRIDE, pbuf_r + (size_t)(cnt - 1) * PSTRIDE, M2 * sizeof(vq));
    memcpy(pbuf_i + (size_t)lp * PSTRIDE, pbuf_i + (size_t)(cnt - 1) * PSTRIDE, M2 * sizeof(vq));
  }

  alignas(64) vq Xrow[M1], Xirow[M1];
  const qtw_table *tw = q15_tw_fast<IDX>();
  const size_t wso = ws + (size_t)(M2 - 1), weo = we + (size_t)(M2 - 1);
  if(laneidx){
    const vq vneg1 = Q_SET1(-1);
    vq m0 = vneg1, m1 = vneg1, ix0 = Q_SET1(32767), ix1 = Q_SET1(32767);
    for(size_t k2 = 0; k2 < (size_t)M2; k2++){
      const long lo = (long)((wso - k2) / (size_t)M2);
      const long hi = (long)((weo - k2) / (size_t)M2);
      if(lo >= hi) continue;
      q15_store_block_col<M1>(pbuf_r, PSTRIDE, (int)k2, 0, Xrow);
      q15_store_block_col<M1>(pbuf_i, PSTRIDE, (int)k2, 0, Xirow);
      q15_row_lag_step<M1, M2>(tw, k2, Xrow, Xirow, lo, hi, &m0, &m1, &ix0, &ix1);
    }
    const qmask u1 = Q_MASK_OR(Q_GT(m1, m0), Q_MASK_AND(Q_EQ(m1, m0), Q_LT(ix1, ix0)));
    const vq mx_raw = Q_MAX(m0, m1);
    const vq ix = Q_SEL(Q_GT(mx_raw, vneg1), Q_SEL(u1, ix1, ix0), vneg1);
    Q_STOREU(laneidx, ix);
    const vq mx = Q_MAX(mx_raw, Q_ZERO());
    if(lanemax) Q_STOREU(lanemax, mx);
    *bits = q15_mask_bits(Q_GE(mx, Q_LOADU(lanethr)));
  } else {
    vq mm[2] = {Q_ZERO(), Q_ZERO()};
    const int mode = q15_win_mode<M1, M2>(ws, we);
    if(mode == 0){
      for(size_t k2 = 0; k2 < (size_t)M2; k2++){
        const long lo = (long)((wso - k2) / (size_t)M2);
        const long hi = (long)((weo - k2) / (size_t)M2);
        q15_store_block_col<M1>(pbuf_r, PSTRIDE, (int)k2, 0, Xrow);
        q15_store_block_col<M1>(pbuf_i, PSTRIDE, (int)k2, 0, Xirow);
        q15_row_twmax_step<M1, 0>(tw, k2, Xrow, Xirow, lo, hi, mm);
      }
    } else if(mode == 1){
      for(size_t k2 = 0; k2 < (size_t)M2; k2++){
        const long lo = (long)((wso - k2) / (size_t)M2);
        const long hi = (long)((weo - k2) / (size_t)M2);
        q15_store_block_col<M1>(pbuf_r, PSTRIDE, (int)k2, 0, Xrow);
        q15_store_block_col<M1>(pbuf_i, PSTRIDE, (int)k2, 0, Xirow);
        q15_row_twmax_step<M1, 1>(tw, k2, Xrow, Xirow, lo, hi, mm);
      }
    } else {
      for(size_t k2 = 0; k2 < (size_t)M2; k2++){
        const long lo = (long)((wso - k2) / (size_t)M2);
        const long hi = (long)((weo - k2) / (size_t)M2);
        if(lo >= hi) continue;
        q15_store_block_col<M1>(pbuf_r, PSTRIDE, (int)k2, 0, Xrow);
        q15_store_block_col<M1>(pbuf_i, PSTRIDE, (int)k2, 0, Xirow);
        q15_row_twmax_step<M1, 2>(tw, k2, Xrow, Xirow, lo, hi, mm);
      }
    }
    const vq mx = Q_MAX(mm[0], mm[1]);
    if(lanemax) Q_STOREU(lanemax, mx);
    *bits = q15_mask_bits(Q_GE(mx, Q_LOADU(lanethr)));
  }
  if(cnt < 64) *bits &= (((uint64_t)1 << cnt) - 1u);
  return 0;
}

#if !defined(AP_SIMD_AVX1) && AP_QW == 8
/* On 8-lane targets (ARM64 NEON, SSE4), each 8-element column strip fits one 8-lane
   group directly: run Pass-1 qcodelet(M2) at unit stride in a 4-8 KB L1D buffer, transpose
   active k2 rows into contiguous row-major Tbuf, and run Pass 2 in place without copies. */
template<int IDX, int M1, int M2>
static HWY_NOINLINE int q15_screen_gather_grp8_n(
    const int16_t *const *drp, const int16_t *const *dip,
    const int16_t *const *trp, const int16_t *const *tip,
    int cnt, size_t ws, size_t we, const int16_t *lanethr,
    uint64_t *bits, int16_t *lanemax, int16_t *laneidx, void *scratch){
  constexpr size_t N = (size_t)M1 * (size_t)M2;
  if(we > N) we = N;
  constexpr int CSTRIPS = M1 / 8;
  constexpr int P8_STRIDE = M2 + 1;
  alignas(64) vq pbuf8_r[8 * P8_STRIDE];
  alignas(64) vq pbuf8_i[8 * P8_STRIDE];
  vq *Tbuf_r = (vq *)scratch;
  vq *Tbuf_i = Tbuf_r + (size_t)M1 * (size_t)M2;
  const size_t wso = ws + (size_t)(M2 - 1), weo = we + (size_t)(M2 - 1);

  for(int cs = 0; cs < CSTRIPS; cs++){
    const size_t c0 = (size_t)cs * 8;
    for(int j = 0; j < 8; j++){
      const int16_t *drl = drp[j] + c0, *dil = dip[j] + c0;
      const int16_t *trl = trp[j] + c0, *til = tip[j] + c0;
      vq *pr = pbuf8_r + (size_t)j * P8_STRIDE;
      vq *pi = pbuf8_i + (size_t)j * P8_STRIDE;
      for(int e2 = 0; e2 < M2; e2++){
        const size_t off = (size_t)e2 * (size_t)M1;
        const vq dR = Q_LOADU(drl + off), dI = Q_LOADU(dil + off);
        const vq tR = Q_LOADU(trl + off), tI = Q_LOADU(til + off);
        pr[e2] = Q_MLSH(Q_MUL(dR, tR), dI, tI);
        pi[e2] = Q_MLAH(Q_MUL(dR, tI), dI, tR);
      }
      qcodelet(M2, pr, pi, 1);
    }
    for(size_t k2 = 0; k2 < (size_t)M2; k2++){
      const long lo = (long)((wso - k2) / (size_t)M2);
      const long hi = (long)((weo - k2) / (size_t)M2);
      if(lo >= hi) continue;
      vq *dst_r = Tbuf_r + k2 * (size_t)M1 + c0;
      vq *dst_i = Tbuf_i + k2 * (size_t)M1 + c0;
      vq ur[8], ui[8];
      for(int m = 0; m < 8; m++) ur[m] = pbuf8_r[(size_t)m * P8_STRIDE + k2];
      q15_transpose8_inlane(ur);
      for(int m = 0; m < 8; m++) dst_r[m] = ur[m];
      for(int m = 0; m < 8; m++) ui[m] = pbuf8_i[(size_t)m * P8_STRIDE + k2];
      q15_transpose8_inlane(ui);
      for(int m = 0; m < 8; m++) dst_i[m] = ui[m];
    }
  }

  const qtw_table *tw = q15_tw_fast<IDX>();
  if(laneidx){
    const vq vneg1 = Q_SET1(-1);
    vq m0 = vneg1, m1 = vneg1, ix0 = Q_SET1(32767), ix1 = Q_SET1(32767);
    for(size_t k2 = 0; k2 < (size_t)M2; k2++){
      const long lo = (long)((wso - k2) / (size_t)M2);
      const long hi = (long)((weo - k2) / (size_t)M2);
      if(lo >= hi) continue;
      q15_row_lag_step<M1, M2>(tw, k2, Tbuf_r + k2 * (size_t)M1, Tbuf_i + k2 * (size_t)M1,
                               lo, hi, &m0, &m1, &ix0, &ix1);
    }
    const qmask u1 = Q_MASK_OR(Q_GT(m1, m0), Q_MASK_AND(Q_EQ(m1, m0), Q_LT(ix1, ix0)));
    const vq mx_raw = Q_MAX(m0, m1);
    const vq ix = Q_SEL(Q_GT(mx_raw, vneg1), Q_SEL(u1, ix1, ix0), vneg1);
    Q_STOREU(laneidx, ix);
    const vq mx = Q_MAX(mx_raw, Q_ZERO());
    if(lanemax) Q_STOREU(lanemax, mx);
    *bits = q15_mask_bits(Q_GE(mx, Q_LOADU(lanethr)));
  } else {
    vq mm[2] = {Q_ZERO(), Q_ZERO()};
    const int mode = q15_win_mode<M1, M2>(ws, we);
    if(mode == 0){
      for(size_t k2 = 0; k2 < (size_t)M2; k2++){
        const long lo = (long)((wso - k2) / (size_t)M2);
        const long hi = (long)((weo - k2) / (size_t)M2);
        q15_row_twmax_step<M1, 0>(tw, k2, Tbuf_r + k2 * (size_t)M1, Tbuf_i + k2 * (size_t)M1,
                                  lo, hi, mm);
      }
    } else if(mode == 1){
      for(size_t k2 = 0; k2 < (size_t)M2; k2++){
        const long lo = (long)((wso - k2) / (size_t)M2);
        const long hi = (long)((weo - k2) / (size_t)M2);
        q15_row_twmax_step<M1, 1>(tw, k2, Tbuf_r + k2 * (size_t)M1, Tbuf_i + k2 * (size_t)M1,
                                  lo, hi, mm);
      }
    } else {
      for(size_t k2 = 0; k2 < (size_t)M2; k2++){
        const long lo = (long)((wso - k2) / (size_t)M2);
        const long hi = (long)((weo - k2) / (size_t)M2);
        if(lo >= hi) continue;
        q15_row_twmax_step<M1, 2>(tw, k2, Tbuf_r + k2 * (size_t)M1, Tbuf_i + k2 * (size_t)M1,
                                  lo, hi, mm);
      }
    }
    const vq mx = Q_MAX(mm[0], mm[1]);
    if(lanemax) Q_STOREU(lanemax, mx);
    *bits = q15_mask_bits(Q_GE(mx, Q_LOADU(lanethr)));
  }
  if(cnt < 64) *bits &= (((uint64_t)1 << cnt) - 1u);
  return 0;
}
#endif

template<int IDX, int M1, int M2>
static HWY_NOINLINE int q15_screen_gather_n(const int16_t *const *drp, const int16_t *const *dip,
                                            const int16_t *const *trp, const int16_t *const *tip,
                                            int cnt, size_t ws, size_t we, const int16_t *lanethr,
                                            uint64_t *bits, int16_t *lanemax, int16_t *laneidx,
                                            void *scratch){
  if constexpr (AP_QW == 32 && M1 == 32) {
    return q15_screen_gather_row_fused_n<IDX, M1, M2>(drp, dip, trp, tip, cnt, ws, we, lanethr,
                                                      bits, lanemax, laneidx);
  }
#if !defined(AP_SIMD_AVX1) && AP_QW == 8
  return q15_screen_gather_grp8_n<IDX, M1, M2>(drp, dip, trp, tip, cnt, ws, we, lanethr,
                                               bits, lanemax, laneidx, scratch);
#else
  vq *X = (vq *)scratch, *Xi = X + (size_t)(M1 + 1) * M2;
  q15_prod_gather_n<M1, M2>(drp, dip, trp, tip, X, Xi);
  const qtw_table *tw = q15_tw_fast<IDX>();
  const int r = q15_finish_n<M1, M2, true>(tw, X, Xi, ws, we, lanethr, bits, lanemax, laneidx);
  if(cnt < 64) *bits &= (((uint64_t)1 << cnt) - 1u);
  return r;
#endif
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
  const qtw_table *tw = q15_tw_fast<IDX>();
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
   on AVX-512, 4 and 8 on AVX2, 2 and 4 on 8-lane AVX1); any other T or N is refused. */
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
#if defined(AP_SIMD_AVX1) || (HWY_ARCH_X86 && HWY_MAX_BYTES >= 32)
  __m256 vs[8];
  for(int b = 0; b < 8; b++) vs[b] = _mm256_set1_ps(sc[b]);
  for(int part = 0; part < 2; part++){
    const float *const *rows = part ? ri : rr;
    int16_t *out = part ? xi : xr;
    for(size_t k = 0; k < N; k += 8){
      __m128i r[8];
      for(int b = 0; b < 8; b++){
        const __m256i vi8 = _mm256_cvtps_epi32(_mm256_mul_ps(_mm256_loadu_ps(rows[b] + k), vs[b]));
        r[b] = _mm_packs_epi32(_mm256_castsi256_si128(vi8), _mm256_extractf128_si256(vi8, 1));
      }
      q15_transpose8_128(r);
      for(int m = 0; m < 8; m++)
        _mm_storeu_si128((__m128i *)(out + (k + (size_t)m) * (size_t)AP_QW), r[m]);
    }
  }
#else
  const hn::FixedTag<float, 4> df;
  const hn::FixedTag<int32_t, 4> di;
  const hn::FixedTag<int16_t, 8> dh;
  const hn::FixedTag<int64_t, 2> dl;
  using V16 = hn::Vec<decltype(dh)>;
  using VF4 = hn::Vec<decltype(df)>;
  VF4 vs[8];
  for(int b = 0; b < 8; b++) vs[b] = hn::Set(df, sc[b]);
  for(int part = 0; part < 2; part++){
    const float *const *rows = part ? ri : rr;
    int16_t *out = part ? xi : xr;
    for(size_t k = 0; k < N; k += 8){
      V16 r[8];
      for(int b = 0; b < 8; b++){
        const auto a = hn::NearestInt(hn::Mul(hn::LoadU(df, rows[b] + k), vs[b]));
        const auto c = hn::NearestInt(hn::Mul(hn::LoadU(df, rows[b] + k + 4), vs[b]));
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
#endif
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
#if defined(AP_SIMD_AVX1)
  const vf sv = V_ADD(s0, s1);
  __m128 u = _mm_add_ps(_mm256_castps256_ps128(sv), _mm256_extractf128_ps(sv, 1));
  u = _mm_hadd_ps(u, u);
  u = _mm_hadd_ps(u, u);
  double ss = (double)_mm_cvtss_f32(u);
#else
  double ss = (double)hn::ReduceSum(AP_D, V_ADD(s0, s1));
#endif
  for(; k < N; k++) ss += (double)re[k] * re[k] + (double)im[k] * im[k];
  return ss;
}

#if defined(AP_SIMD_AVX1)
static HWY_INLINE void avx1_quant8_split(vf r_f, vf i_f, vf vs, __m128i vmin32, __m128i vmax32,
                                         __m128i *qr_out, __m128i *qi_out){
  const __m256i r8 = _mm256_cvtps_epi32(_mm256_mul_ps(r_f, vs));
  const __m256i i8 = _mm256_cvtps_epi32(_mm256_mul_ps(i_f, vs));
  const __m128i r0 = _mm_min_epi32(_mm_max_epi32(_mm256_castsi256_si128(r8), vmin32), vmax32);
  const __m128i r1 = _mm_min_epi32(_mm_max_epi32(_mm256_extractf128_si256(r8, 1), vmin32), vmax32);
  const __m128i i0 = _mm_min_epi32(_mm_max_epi32(_mm256_castsi256_si128(i8), vmin32), vmax32);
  const __m128i i1 = _mm_min_epi32(_mm_max_epi32(_mm256_extractf128_si256(i8, 1), vmin32), vmax32);
  *qr_out = _mm_packs_epi32(r0, r1);
  *qi_out = _mm_packs_epi32(i0, i1);
}
#endif

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
  int32_t *qd_re = (int32_t *)qd;
  int16_t *qd_im = qd + 2 * N;
#if defined(AP_SIMD_AVX1)
  const __m128i vmin32 = _mm_set1_epi32(-32767), vmax32 = _mm_set1_epi32(32767);
  if((n1 <= 0 || (w == AP_W && n1 == AP_W && (size_t)n1 * (size_t)n2 == N)) && N % 8 == 0){
    for(size_t k = 0; k < N; k += 8){
      __m128i qr, qi;
      avx1_quant8_split(V_LOADU(re + k), V_LOADU(im + k), vs, vmin32, vmax32, &qr, &qi);
      _mm_storeu_si128((__m128i *)(qd_re + k), _mm_unpacklo_epi16(qr, qr));
      _mm_storeu_si128((__m128i *)(qd_re + k + 4), _mm_unpackhi_epi16(qr, qr));
      _mm_storeu_si128((__m128i *)(qd_im + k), qi);
    }
    return;
  }
  if(w == AP_W && n1 > 0 && n1 % AP_W == 0 && (size_t)n1 * (size_t)n2 == N){
    const int ng = n1 / AP_W;
    for(int b = 0; b < n2; b++){
      for(int g = 0; g < ng; g++){
        const size_t j0 = ((size_t)g * (size_t)n2 + (size_t)b) * (size_t)AP_W;
        const size_t k = (size_t)b * (size_t)n1 + (size_t)g * (size_t)AP_W;
        __m128i qr, qi;
        avx1_quant8_split(V_LOADU(re + j0), V_LOADU(im + j0), vs, vmin32, vmax32, &qr, &qi);
        _mm_storeu_si128((__m128i *)(qd_re + k), _mm_unpacklo_epi16(qr, qr));
        _mm_storeu_si128((__m128i *)(qd_re + k + 4), _mm_unpackhi_epi16(qr, qr));
        _mm_storeu_si128((__m128i *)(qd_im + k), qi);
      }
    }
    return;
  }
#else
  const vi vmin32 = hn::Set(AP_DI, -32767), vmax32 = hn::Set(AP_DI, 32767);
  const vi vmask16 = hn::Set(AP_DI, 0xFFFF);
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
#endif
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
#if defined(AP_SIMD_AVX1)
  const __m128i vmin32 = _mm_set1_epi32(-32767), vmax32 = _mm_set1_epi32(32767);
  if((n1 <= 0 || (w == AP_W && n1 == AP_W && (size_t)n1 * (size_t)n2 == N)) && N % 8 == 0){
    for(size_t k = 0; k < N; k += 8){
      __m128i qr, qi;
      avx1_quant8_split(V_LOADU(re + k), V_LOADU(im + k), vs, vmin32, vmax32, &qr, &qi);
      _mm_storeu_si128((__m128i *)(qdr + k), qr);
      _mm_storeu_si128((__m128i *)(qdi + k), qi);
    }
    return;
  }
  if(w == AP_W && n1 > 0 && n1 % AP_W == 0 && (size_t)n1 * (size_t)n2 == N){
    const int ng = n1 / AP_W;
    for(int b = 0; b < n2; b++){
      for(int g = 0; g < ng; g++){
        const size_t j0 = ((size_t)g * (size_t)n2 + (size_t)b) * (size_t)AP_W;
        const size_t k = (size_t)b * (size_t)n1 + (size_t)g * (size_t)AP_W;
        __m128i qr, qi;
        avx1_quant8_split(V_LOADU(re + j0), V_LOADU(im + j0), vs, vmin32, vmax32, &qr, &qi);
        _mm_storeu_si128((__m128i *)(qdr + k), qr);
        _mm_storeu_si128((__m128i *)(qdi + k), qi);
      }
    }
    return;
  }
#else
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
#endif
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

static HWY_INLINE void q15_deint_slice(const float *HWY_RESTRICT src,
                                       float *HWY_RESTRICT re, float *HWY_RESTRICT im,
                                       size_t len){
  size_t k = 0;
#if defined(AP_SIMD_AVX1) || (HWY_ARCH_X86 && HWY_MAX_BYTES == 32 && HWY_TARGET <= HWY_AVX2)
  for(; k + 8 <= len; k += 8){
    const float *p = src + 2 * k;
    const __m256 e128 = _mm256_insertf128_ps(_mm256_castps128_ps256(_mm_loadu_ps(p)),
                                             _mm_loadu_ps(p + 8), 1);
    const __m256 o128 = _mm256_insertf128_ps(_mm256_castps128_ps256(_mm_loadu_ps(p + 4)),
                                             _mm_loadu_ps(p + 12), 1);
    _mm256_storeu_ps(re + k, _mm256_shuffle_ps(e128, o128, 0x88));
    _mm256_storeu_ps(im + k, _mm256_shuffle_ps(e128, o128, 0xDD));
  }
#else
  for(; k + (size_t)AP_W <= len; k += (size_t)AP_W){
    vf vr, vi;
    v_deint(src + 2 * k, &vr, &vi);
    V_STOREU(re + k, vr);
    V_STOREU(im + k, vi);
  }
#endif
  for(; k < len; k++){
    re[k] = src[2 * k];
    im[k] = src[2 * k + 1];
  }
}

/* Deinterleave data band [k0, khi) directly from interleaved spectrum `spec` into an
   L1D-resident stack buffer (wrapping cyclic slot k & (N - 1) when k0 > 0) and quantise
   into contiguous [N] qdr, qdi rows without staging through split float bank storage. */
static HWY_NOINLINE MF_Q15PREP_SECTION int q15_data_band(
    size_t N, const float *spec, size_t k0, size_t khi,
    int16_t *qdr, int16_t *qdi, float *scale_out){
  if(N == 0 || N > 1024) return -1;
  alignas(64) float re_buf[1024], im_buf[1024];
  if(k0 == 0){
    q15_deint_slice(spec, re_buf, im_buf, N);
  } else {
    const size_t raw_len = khi > k0 ? khi - k0 : 0;
    const size_t len = raw_len < N ? raw_len : N;
    if(len < N){
      memset(re_buf, 0, N * sizeof(float));
      memset(im_buf, 0, N * sizeof(float));
    }
    const size_t u0 = k0 & (N - 1);
    const size_t first = len < N - u0 ? len : N - u0;
    if(first) q15_deint_slice(spec + 2 * k0, re_buf + u0, im_buf + u0, first);
    if(len > first) q15_deint_slice(spec + 2 * (k0 + first), re_buf, im_buf, len - first);
  }
  q15_data_contig(N, re_buf, im_buf, 0, 0, 0, qdr, qdi, scale_out);
  return 0;
}

static HWY_INLINE void q15_lanethr_inline(float threshold, const float *qds,
                                          int qds_stride, const float *qts,
                                          float margin, int nomargin, int16_t *out){
  if(!qds_stride && qds[0] < 0.f){
    Q_STOREU(out, Q_SET1(-32768));
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
#if defined(AP_SIMD_AVX1)
  for(int h = 0; h < AP_QW / 8; h++){
    const int u = h * 8;
    const vf vd = qds_stride ? V_LOADU(qds + u) : V_SET1(qds[0]);
    const vf vt = V_LOADU(qts + u);
    const vf ds = V_MUL(vd, vinv);
    const vf eq = nomargin ? _mm256_blendv_ps(vz, vmarg, _mm256_cmp_ps(V_MUL(ds, vt), v2m, _CMP_LT_OQ)) : vmarg;
    const vf q = V_SUB(V_MUL(V_MUL(V_MUL(vthr, ds), vadj), vt), eq);
    const vf T = V_SUB(V_MUL(V_MUL(q, q), vinv), vone);
    vf r = _mm256_blendv_ps(_mm256_ceil_ps(T), vmax, _mm256_cmp_ps(T, vmax, _CMP_GE_OQ));
    r = _mm256_blendv_ps(vmin, r, _mm256_cmp_ps(q, vz, _CMP_GT_OQ));
    r = _mm256_blendv_ps(r, vz_out, _mm256_or_ps(_mm256_cmp_ps(vd, vz, _CMP_EQ_OQ), _mm256_cmp_ps(vt, vz, _CMP_EQ_OQ)));
    r = _mm256_blendv_ps(r, vmin, _mm256_or_ps(_mm256_cmp_ps(vd, vz, _CMP_LT_OQ), _mm256_cmp_ps(vt, vz, _CMP_LT_OQ)));
    const __m256i ri = _mm256_cvttps_epi32(r);
    _mm_storeu_si128((__m128i *)(out + u),
                     _mm_packs_epi32(_mm256_castsi256_si128(ri), _mm256_extractf128_si256(ri, 1)));
  }
#else
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
#endif
}

/* Vectorised int16 lane thresholds across AP_QW lanes (qds_stride == 0 broadcasts qds[0]).
   Kept in the hot text section alongside q15_screen because matchfilt.c invokes it per batch. */
static HWY_NOINLINE void q15_lanethr(float threshold, const float *qds,
                                     int qds_stride, const float *qts,
                                     float margin, int nomargin, int16_t *out){
  q15_lanethr_inline(threshold, qds, qds_stride, qts, margin, nomargin, out);
}

/* Whole-list Q15 gather batch evaluator: computes SIMD lane thresholds, runs the target's
   gather screen without per-batch indirect dispatch, and compacts survivors directly via
   bitmask ctzll when dst_d/dst_t are provided. */
template<int IDX, int M1, int M2>
static HWY_NOINLINE int q15_pairs_batch_n(
    const int16_t *qdm, const float *qds, const int16_t *qtm, const float *qts,
    int d0, int t0, const int *dsel, const int *tsel, int npairs,
    float threshold, int nomargin, size_t ws, size_t we,
    int *dst_d, int *dst_t, unsigned char *pass_out, int16_t *lag_out, void *scratch){
  constexpr size_t N = (size_t)M1 * (size_t)M2;
  constexpr size_t stride = 2 * N + 32;
  const float margin = (float)ap_q15_margin(N);
  alignas(64) float qds_lane[AP_QW], qts_lane[AP_QW];
  alignas(64) int16_t lanethr[AP_QW], laneidx[AP_QW];
  const int16_t *drp[AP_QW], *dip[AP_QW], *trp[AP_QW], *tip[AP_QW];
  int total = 0;

  for(int i0 = 0; i0 < npairs; i0 += AP_QW){
    const int cnt = npairs - i0 < AP_QW ? npairs - i0 : AP_QW;
    for(int l = 0; l < cnt; l++){
      const int d = d0 + dsel[i0 + l], t = t0 + tsel[i0 + l];
      const int16_t *dq = qdm + (size_t)d * stride;
      const int16_t *tq = qtm + (size_t)t * stride;
      drp[l] = dq; dip[l] = dq + N;
      trp[l] = tq; tip[l] = tq + N;
      qds_lane[l] = qds[d]; qts_lane[l] = qts[t];
    }
    for(int l = cnt; l < AP_QW; l++){
      drp[l] = drp[cnt - 1]; dip[l] = dip[cnt - 1];
      trp[l] = trp[cnt - 1]; tip[l] = tip[cnt - 1];
      qds_lane[l] = 0.f; qts_lane[l] = 0.f;
    }
    q15_lanethr_inline(threshold, qds_lane, 1, qts_lane, margin, nomargin, lanethr);
    uint64_t bits = 0;
    if(q15_screen_gather_n<IDX, M1, M2>(drp, dip, trp, tip, cnt, ws, we, lanethr, &bits,
                                        nullptr, lag_out ? laneidx : nullptr, scratch))
      return -1;
    if(dst_d){
      while(bits){
        const int l = __builtin_ctzll(bits);
        const int idx = i0 + l;
        dst_d[total] = dsel[idx];
        dst_t[total] = tsel[idx];
        if(lag_out)
          lag_out[total] = (qds_lane[l] > 0.f && qts_lane[l] > 0.f) ? laneidx[l] : (int16_t)-1;
        total++;
        bits &= bits - 1;
      }
    } else {
      if(!bits && !lag_out){
        memset(pass_out + i0, 0, (size_t)cnt);
        continue;
      }
      for(int l = 0; l < cnt; l++){
        const int ok = (int)((bits >> l) & 1u);
        pass_out[i0 + l] = (unsigned char)ok;
        total += ok;
        if(lag_out)
          lag_out[i0 + l] = (qds_lane[l] > 0.f && qts_lane[l] > 0.f) ? laneidx[l] : (int16_t)-1;
      }
    }
  }
  return total;
}

static int q15_pairs_batch(
    size_t N, const int16_t *qdm, const float *qds, const int16_t *qtm, const float *qts,
    int d0, int t0, const int *dsel, const int *tsel, int npairs,
    float threshold, int nomargin, size_t ws, size_t we,
    int *dst_d, int *dst_t, unsigned char *pass_out, int16_t *lag_out, void *scratch){
  if(npairs < 1) return 0;
  if(we > N) we = N;
  if(ws >= we){
    if(!dst_d && pass_out) memset(pass_out, 0, (size_t)npairs);
    if(!dst_d && lag_out){
      for(int j = 0; j < npairs; j++) lag_out[j] = -1;
    }
    return 0;
  }
  switch(N){
    case   64: return q15_pairs_batch_n<0,  8,  8>(qdm, qds, qtm, qts, d0, t0, dsel, tsel, npairs, threshold, nomargin, ws, we, dst_d, dst_t, pass_out, lag_out, scratch);
    case  128: return q15_pairs_batch_n<1, 16,  8>(qdm, qds, qtm, qts, d0, t0, dsel, tsel, npairs, threshold, nomargin, ws, we, dst_d, dst_t, pass_out, lag_out, scratch);
    case  256: return q15_pairs_batch_n<2, 16, 16>(qdm, qds, qtm, qts, d0, t0, dsel, tsel, npairs, threshold, nomargin, ws, we, dst_d, dst_t, pass_out, lag_out, scratch);
    case  512: return q15_pairs_batch_n<3, 32, 16>(qdm, qds, qtm, qts, d0, t0, dsel, tsel, npairs, threshold, nomargin, ws, we, dst_d, dst_t, pass_out, lag_out, scratch);
    case 1024: return q15_pairs_batch_n<4, 32, 32>(qdm, qds, qtm, qts, d0, t0, dsel, tsel, npairs, threshold, nomargin, ws, we, dst_d, dst_t, pass_out, lag_out, scratch);
    default: return -1;
  }
}

static HWY_INLINE int q15_write_pass_row(uint64_t bits, int l0, int nlanes, uint64_t act_mask,
                                         unsigned char *row){
  uint64_t mbits = (bits >> l0) & act_mask;
  memset(row, 0, (size_t)nlanes);
  if(!mbits) return 0;
  int cnt = 0;
  while(mbits){
    row[__builtin_ctzll(mbits)] = 1u;
    cnt++;
    mbits &= mbits - 1u;
  }
  return cnt;
}

/* L1D-tiled multi-block Q15 screen: sweeps nd contiguous data blocks against one AP_QW-lane
   template group in B-block tiles (B in {4, 2, 1} chosen from ap_l1d_bytes()), reusing each
   template column and Pass-2 twiddle row across B blocks from L1D without per-block indirect
   dispatch. Bit-for-bit identical to q15_screen_n + q15_lanethr. */
template<int IDX, int M1, int M2>
static HWY_NOINLINE int q15_screen_blocks_n(
    const int16_t *dq, const float *qds, int nd,
    const int16_t *tr, const int16_t *ti, const float *qts,
    int l0, int nlanes, float threshold, float margin, int nomargin,
    size_t ws, size_t we, unsigned char *pass, size_t pass_stride, void *scratch){
  constexpr size_t N = (size_t)M1 * (size_t)M2;
  constexpr size_t st = (size_t)(M1 + 1);
  constexpr size_t scr_vecs = (size_t)2 * (M1 + 1) * M2;
  if(we > N) we = N;
  const uint64_t act_mask = nlanes >= 64 ? ~0ULL : (((uint64_t)1 << nlanes) - 1u);
  const int Bmax = ap_q15_block_tile(N, AP_QW);
  const qtw_table *tw = q15_tw_fast<IDX>();
  const bool mid_mode = (M1 == 8) ? (ws <= 2 * (size_t)M2 && we >= 6 * (size_t)M2)
                      : (M1 == 16) ? (ws <= 2 * (size_t)M2 && we >= 14 * (size_t)M2)
                                   : (ws <= 4 * (size_t)M2 && we >= 28 * (size_t)M2);
  const size_t wso = ws + (size_t)(M2 - 1), weo = we + (size_t)(M2 - 1);
  alignas(64) int16_t lanethr[AP_QW];
  int total = 0;
  int d = 0;

  if constexpr (M1 <= 16) {
    if(Bmax >= 4){
      vq *Xb[4], *Xib[4];
      for(int b = 0; b < 4; b++){
        Xb[b] = (vq *)scratch + (size_t)b * scr_vecs;
        Xib[b] = Xb[b] + st * (size_t)M2;
      }
      for(; d + 4 <= nd; d += 4){
        for(int e1 = 0; e1 < M1; e1++){
          const int16_t *tr_col = tr + (size_t)e1 * AP_QW;
          const int16_t *ti_col = ti + (size_t)e1 * AP_QW;
          for(int b = 0; b < 4; b++){
            const int16_t *dq_b = dq + (size_t)(d + b) * 3 * N;
            qcodelet_prod(M2, (const int32_t *)dq_b + e1, dq_b + 2 * N + e1,
                          tr_col, ti_col, Xb[b] + e1, Xib[b] + e1, M1 + 1, M1, (long)M1 * AP_QW);
          }
        }
        if(mid_mode){
          vq mm[4][2];
          for(int b = 0; b < 4; b++) mm[b][0] = mm[b][1] = Q_ZERO();
          for(size_t k2 = 0; k2 < (size_t)M2; k2++){
            const long lo = (long)((wso - k2) / (size_t)M2);
            const long hi = (long)((weo - k2) / (size_t)M2);
            const qtw_elem *twr = tw->re + k2 * (size_t)M1;
            const qtw_elem *twi = tw->im + k2 * (size_t)M1;
            for(int b = 0; b < 4; b++){
              if constexpr (M1 == 8)
                qsr8_twmax_middle(Xb[b] + k2 * st, Xib[b] + k2 * st, 1, twr, twi, lo, hi, mm[b]);
              else
                qsr16_twmax_middle(Xb[b] + k2 * st, Xib[b] + k2 * st, 1, twr, twi, lo, hi, mm[b]);
            }
          }
          for(int b = 0; b < 4; b++){
            q15_lanethr_inline(threshold, qds + d + b, 0, qts, margin, nomargin, lanethr);
            const vq mx = Q_MAX(mm[b][0], mm[b][1]);
            const uint64_t bits = q15_mask_bits(Q_GE(mx, Q_LOADU(lanethr)));
            total += q15_write_pass_row(bits, l0, nlanes, act_mask, pass + (size_t)(d + b) * pass_stride);
          }
        } else {
          for(int b = 0; b < 4; b++){
            q15_lanethr_inline(threshold, qds + d + b, 0, qts, margin, nomargin, lanethr);
            uint64_t bits = 0;
            q15_finish_n<M1, M2, false>(tw, Xb[b], Xib[b], ws, we, lanethr, &bits, nullptr, nullptr);
            total += q15_write_pass_row(bits, l0, nlanes, act_mask, pass + (size_t)(d + b) * pass_stride);
          }
        }
      }
    }
    if(Bmax >= 2){
      vq *Xb[2] = {(vq *)scratch, (vq *)scratch + scr_vecs};
      vq *Xib[2] = {Xb[0] + st * (size_t)M2, Xb[1] + st * (size_t)M2};
      for(; d + 2 <= nd; d += 2){
        for(int e1 = 0; e1 < M1; e1++){
          const int16_t *tr_col = tr + (size_t)e1 * AP_QW;
          const int16_t *ti_col = ti + (size_t)e1 * AP_QW;
          for(int b = 0; b < 2; b++){
            const int16_t *dq_b = dq + (size_t)(d + b) * 3 * N;
            qcodelet_prod(M2, (const int32_t *)dq_b + e1, dq_b + 2 * N + e1,
                          tr_col, ti_col, Xb[b] + e1, Xib[b] + e1, M1 + 1, M1, (long)M1 * AP_QW);
          }
        }
        if(mid_mode){
          vq mm[2][2] = {{Q_ZERO(), Q_ZERO()}, {Q_ZERO(), Q_ZERO()}};
          for(size_t k2 = 0; k2 < (size_t)M2; k2++){
            const long lo = (long)((wso - k2) / (size_t)M2);
            const long hi = (long)((weo - k2) / (size_t)M2);
            const qtw_elem *twr = tw->re + k2 * (size_t)M1;
            const qtw_elem *twi = tw->im + k2 * (size_t)M1;
            for(int b = 0; b < 2; b++){
              if constexpr (M1 == 8)
                qsr8_twmax_middle(Xb[b] + k2 * st, Xib[b] + k2 * st, 1, twr, twi, lo, hi, mm[b]);
              else
                qsr16_twmax_middle(Xb[b] + k2 * st, Xib[b] + k2 * st, 1, twr, twi, lo, hi, mm[b]);
            }
          }
          for(int b = 0; b < 2; b++){
            q15_lanethr_inline(threshold, qds + d + b, 0, qts, margin, nomargin, lanethr);
            const vq mx = Q_MAX(mm[b][0], mm[b][1]);
            const uint64_t bits = q15_mask_bits(Q_GE(mx, Q_LOADU(lanethr)));
            total += q15_write_pass_row(bits, l0, nlanes, act_mask, pass + (size_t)(d + b) * pass_stride);
          }
        } else {
          for(int b = 0; b < 2; b++){
            q15_lanethr_inline(threshold, qds + d + b, 0, qts, margin, nomargin, lanethr);
            uint64_t bits = 0;
            q15_finish_n<M1, M2, false>(tw, Xb[b], Xib[b], ws, we, lanethr, &bits, nullptr, nullptr);
            total += q15_write_pass_row(bits, l0, nlanes, act_mask, pass + (size_t)(d + b) * pass_stride);
          }
        }
      }
    }
  }

  vq *X = (vq *)scratch, *Xi = X + st * (size_t)M2;
  for(; d < nd; d++){
    q15_prod_n<M1, M2>(dq + (size_t)d * 3 * N, tr, ti, X, Xi);
    q15_lanethr_inline(threshold, qds + d, 0, qts, margin, nomargin, lanethr);
    uint64_t bits = 0;
    q15_finish_n<M1, M2, false>(tw, X, Xi, ws, we, lanethr, &bits, nullptr, nullptr);
    total += q15_write_pass_row(bits, l0, nlanes, act_mask, pass + (size_t)d * pass_stride);
  }
  return total;
}

static int q15_screen_blocks(
    size_t N, const int16_t *dq, const float *qds, int nd,
    const int16_t *tr, const int16_t *ti, const float *qts,
    int l0, int nlanes, float threshold, float margin, int nomargin,
    size_t ws, size_t we, unsigned char *pass, size_t pass_stride, void *scratch){
  if(nd < 1 || nlanes < 1 || l0 < 0 || l0 + nlanes > AP_QW) return -1;
  switch(N){
    case   64: return q15_screen_blocks_n<0,  8,  8>(dq, qds, nd, tr, ti, qts, l0, nlanes, threshold, margin, nomargin, ws, we, pass, pass_stride, scratch);
    case  128: return q15_screen_blocks_n<1, 16,  8>(dq, qds, nd, tr, ti, qts, l0, nlanes, threshold, margin, nomargin, ws, we, pass, pass_stride, scratch);
    case  256: return q15_screen_blocks_n<2, 16, 16>(dq, qds, nd, tr, ti, qts, l0, nlanes, threshold, margin, nomargin, ws, we, pass, pass_stride, scratch);
    case  512: return q15_screen_blocks_n<3, 32, 16>(dq, qds, nd, tr, ti, qts, l0, nlanes, threshold, margin, nomargin, ws, we, pass, pass_stride, scratch);
    case 1024: return q15_screen_blocks_n<4, 32, 32>(dq, qds, nd, tr, ti, qts, l0, nlanes, threshold, margin, nomargin, ws, we, pass, pass_stride, scratch);
    default: return -1;
  }
}

#undef MF_Q15PREP_SECTION

}  // namespace HWY_NAMESPACE
}  // namespace ap
HWY_AFTER_NAMESPACE();

#endif
