/* Standard normal draws for the gate model's simulations (gatechain: noise block maxima, the
 * signal and direct-refine draws), counter-based so that every value depends only on the seed
 * and its index: out[i] for i in [0, n) is draw offset + i of stream `seed`, whatever the
 * vector width, the ISA or how a caller splits the work.
 *
 * The stream is cut into blocks of 2048 draws. Block b seeds eight xoshiro128++ generators
 * (Blackman and Vigna, "Scrambled linear pseudorandom number generators", 2021) from
 * Threefry-2x32-20 of counters 16 b .. 16 b + 15 under the seed (Salmon et al., "Parallel
 * random numbers: as easy as 1, 2, 3", SC 2011): Threefry is a good hash of the counter, and
 * xoshiro's step is a few integer operations a word where Threefry's twenty rounds were most
 * of a draw's cost (Ivy Bridge, 4-lane SSE4: ~6 of 9 ns). A block's eight generators run as
 * eight lanes -- two 4-lane vectors on SSE4 and NEON, one 8-lane vector on AVX2, and on
 * AVX-512 two blocks share a 16-lane vector, eight lanes each -- so the integers are identical
 * on every ISA. Step q of the block gives words A (one step of every generator) and B (the
 * next): lane j's pair (A_j, B_j) is turned by Box-Muller into the draws at 16 q + 2 j and
 * 16 q + 2 j + 1:
 *   u1 = (A_j >> 8 + 1) 2^-24 in (0, 1],  u2 = (B_j >> 8) 2^-24 in [0, 1),
 *   r = sqrt(-2 ln u1),  cos draw = r cos(2 pi u2),  sin draw = r sin(2 pi u2).
 * Draws reach 5.77 sigma at most (u1 = 2^-24), far past what a simulation of block maxima of
 * transformed noise resolves. Both u1 and u2 come from exact 24-bit integers, so Box-Muller
 * folds u1 directly to m in [sqrt(1/2), sqrt(2)) for a degree-7 minimax -2 ln(1 + f) and
 * reduces B_j >> 8 in integer arithmetic to a quadrant and exact t in [-1/2, 1/2) for degree-7
 * and degree-6 minimax sin/cos. The float part differs between FMA and non-FMA ISAs in the
 * last ulp at most; within each it is lane by lane the same arithmetic across vector widths
 * (including an 8-float AVX1 path paired with 128-bit integer state). A read starting inside a
 * block runs the block's generators through the steps before it without storing them, and one
 * ending inside it generates only the steps it reads. */
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#if AP_HAVE_AVX1
#include <immintrin.h>
#include "backend.h"
#endif

#undef HWY_TARGET_INCLUDE
#define HWY_TARGET_INCLUDE "gauss.cc"
#include "hwy/foreach_target.h"  // must come before highway.h
#include "hwy/highway.h"

#ifndef AP_GAUSS_ONCE
#define AP_GAUSS_ONCE
namespace ap_gauss {
static const uint64_t kBlock = 2048;           // draws a block: 128 steps of 8 pairs

static inline uint32_t rotl32(uint32_t x, int r) { return (x << r) | (x >> (32 - r)); }

/* Threefry-2x32-20 of counter (x0, x1) under key (k0, k1). */
static inline void threefry(uint32_t &x0, uint32_t &x1, uint32_t k0, uint32_t k1) {
  static const int R[8] = {13, 15, 26, 6, 17, 29, 16, 24};
  const uint32_t ks[3] = {k0, k1, k0 ^ k1 ^ 0x1BD11BDAu};
  x0 += k0; x1 += k1;
  for (uint32_t s = 1; s <= 5; s++) {
    for (int i = 0; i < 4; i++) {
      x0 += x1; x1 = rotl32(x1, R[((s - 1) & 1) * 4 + i]); x1 ^= x0;
    }
    x0 += ks[s % 3]; x1 += ks[(s + 1) % 3] + s;
  }
}

/* Block b's eight generators' states, word w of generator j at st[w * ws + j] (ws >= 8). */
static inline void seed_block(uint32_t *st, size_t ws, uint64_t b, uint32_t k0, uint32_t k1) {
  for (uint32_t i = 0; i < 16; i++) {
    const uint64_t c = b * 16 + i;
    uint32_t x0 = (uint32_t)c, x1 = (uint32_t)(c >> 32);
    threefry(x0, x1, k0, k1);
    const uint32_t j = i / 2, w = (i % 2) * 2;     // generator j's words w, w + 1
    st[w * ws + j] = x0; st[(w + 1) * ws + j] = x1;
  }
  for (int j = 0; j < 8; j++) st[j] |= 1u;         // never the all-zero state
}

/* One block's share of a row of a fill: block b's draws [lo, hi) (0 <= lo < hi <= kBlock),
   draw d at row[at + d] -- at is where the block starts relative to the row, negative when
   the row starts inside it -- times sc[(at + d) / 2] when sc (the row's scale, one a pair of
   draws) is given. */
struct Piece {
  float *row;
  const float *sc;
  int64_t at;
  uint64_t b;
  uint32_t lo, hi;
};
}  // namespace ap_gauss
#endif

HWY_BEFORE_NAMESPACE();
namespace ap_gauss {
namespace HWY_NAMESPACE {
namespace hn = hwy::HWY_NAMESPACE;

template <int R, class V>
HWY_INLINE V Rotl(V x) { return hn::Or(hn::ShiftLeft<R>(x), hn::ShiftRight<32 - R>(x)); }

/* Blocks a fill kernel generates together: two where a vector holds sixteen 32-bit lanes,
   else one. */
static constexpr size_t kGroup = HWY_LANES(uint32_t) >= 16 ? 2 : 1;

/* G blocks' generators, block g's in lanes 8 g .. 8 g + 7 of one vector (G = 1: the eight in
   8 / L vectors of L lanes), their word w at st + 8 G w (seed_block's layout). */
template <size_t G>
struct GenLanes {
  using DU = hn::CappedTag<uint32_t, 8 * G>;
  using DF = hn::Rebind<float, DU>;
  using VU = hn::Vec<DU>;
  static constexpr size_t kMax = 8;
  static size_t L() { return hn::Lanes(DU()); }
  static size_t NV() { return G == 1 ? 8 / L() : 1; }   // vectors holding the generators
};

/* One xoshiro128++ step of the generators in s0 .. s3: their output. */
template <class VU>
HWY_INLINE VU Next(VU &s0, VU &s1, VU &s2, VU &s3) {
  const VU r = hn::Add(Rotl<7>(hn::Add(s0, s3)), s0);
  const VU t = hn::ShiftLeft<9>(s1);
  s2 = hn::Xor(s2, s0); s3 = hn::Xor(s3, s1);
  s1 = hn::Xor(s1, s2); s0 = hn::Xor(s0, s3);
  s2 = hn::Xor(s2, t); s3 = Rotl<11>(s3);
  return r;
}

/* n steps of the generators at st, and nothing more: steps before any piece's draws. */
template <size_t G>
static HWY_NOINLINE void Skip(uint32_t *st, uint64_t n) {
  using T = GenLanes<G>;
  const typename T::DU du;
  const size_t L = T::L(), NV = T::NV();
  for (size_t v = 0; v < NV; v++) {
    auto s0 = hn::Load(du, st + 0 * 8 * G + v * L), s1 = hn::Load(du, st + 1 * 8 * G + v * L);
    auto s2 = hn::Load(du, st + 2 * 8 * G + v * L), s3 = hn::Load(du, st + 3 * 8 * G + v * L);
    for (uint64_t i = 0; i < 2 * n; i++) (void)Next(s0, s1, s2, s3);
    hn::Store(s0, du, st + 0 * 8 * G + v * L); hn::Store(s1, du, st + 1 * 8 * G + v * L);
    hn::Store(s2, du, st + 2 * 8 * G + v * L); hn::Store(s3, du, st + 3 * 8 * G + v * L);
  }
}

/* Box-Muller on 24-bit integer inputs A >> 8, B >> 8:
   - u1 = ((A >> 8) + 1) * 2^-24 is folded directly from float((A >> 8) + 1) into exponent
     ne = -e_u1 in {0 .. 24} and mantissa m in [sqrt(1/2), sqrt(2)), where -2 ln(1 + f) is
     evaluated by a degree-7 minimax polynomial (< 0.5 ulp across all 2^24 inputs, exact 0 at
     u1 = 1 because TWO_LN2_HI has 10 trailing zero mantissa bits and ne >= 0).
   - B >> 8 is reduced in exact integer arithmetic into quadrant q in {0 .. 4} and
     t in [-1/2, 1/2), where sin(pi/2 t) and cos(pi/2 t) are degree-7 and degree-6 minimax
     polynomials (< 0.2e-6 across all 2^24 inputs), swapped and sign-flipped from q's bits. */
template <class DF, class DU, class VU, class VF = hn::Vec<DF>>
static HWY_INLINE void BoxMuller(DF df, DU du, VU A, VU B, VF &x, VF &y) {
  const hn::RebindToSigned<DF> di;
  const auto one = hn::Set(du, 1u);
  const auto one_f = hn::Set(df, 1.0f);

  const auto kf = hn::ConvertTo(df, hn::Add(hn::ShiftRight<8>(A), one));
  const auto adj = hn::Add(hn::BitCast(di, kf), hn::Set(di, 0x004afb0d));
  const auto nef = hn::ConvertTo(df, hn::Sub(hn::Set(di, 151), hn::ShiftRight<23>(adj)));
  const auto m = hn::BitCast(df, hn::Add(hn::And(adj, hn::Set(di, 0x007fffff)),
                                         hn::Set(di, 0x3f3504f3)));
  const auto f = hn::Sub(m, one_f);
  const auto f2 = hn::Mul(f, f);
  auto p = hn::Set(df, -0.2397264838218689f);
  p = hn::MulAdd(p, f, hn::Set(df, 0.3752340078353882f));
  p = hn::MulAdd(p, f, hn::Set(df, -0.40985167026519775f));
  p = hn::MulAdd(p, f, hn::Set(df, 0.4979553520679474f));
  p = hn::MulAdd(p, f, hn::Set(df, -0.6663109064102173f));
  p = hn::MulAdd(p, f, hn::Set(df, 1.0000296831130981f));
  const auto lo = hn::MulAdd(p, f2, hn::Mul(nef, hn::Set(df, 2.857213530660374e-6f)));
  const auto hi = hn::Sub(hn::Mul(nef, hn::Set(df, 1.38629150390625f)), hn::Add(f, f));
  const auto r = hn::Sqrt(hn::Add(hi, lo));

  const auto bh = hn::ShiftRight<8>(B);
  const auto q = hn::ShiftRight<22>(hn::Add(bh, hn::Set(du, 1u << 21)));
  const auto ki = hn::Sub(hn::BitCast(di, bh), hn::BitCast(di, hn::ShiftLeft<22>(q)));
  const auto t = hn::Mul(hn::ConvertTo(df, ki), hn::Set(df, 1.0f / 4194304.0f));
  const auto t2 = hn::Mul(t, t);
  auto sp = hn::Set(df, -0.004602177068591118f);
  sp = hn::MulAdd(sp, t2, hn::Set(df, 0.07968022674322128f));
  sp = hn::MulAdd(sp, t2, hn::Set(df, -0.6459634900093079f));
  sp = hn::Mul(t, hn::MulAdd(sp, t2, hn::Set(df, 1.5707963705062866f)));
  auto cp = hn::Set(df, -0.02052159793674946f);
  cp = hn::MulAdd(cp, t2, hn::Set(df, 0.25363752245903015f));
  cp = hn::MulAdd(hn::MulAdd(cp, t2, hn::Set(df, -1.233700156211853f)), t2, one_f);

  const auto swap_v = hn::BitCast(df, hn::ShiftLeft<31>(q));
  auto s = hn::IfNegativeThenElse(swap_v, cp, sp);
  auto c = hn::IfNegativeThenElse(swap_v, sp, cp);
  const auto sign_mask = hn::Set(du, 0x80000000u);
  s = hn::Xor(s, hn::BitCast(df, hn::And(hn::ShiftLeft<30>(q), sign_mask)));
  c = hn::Xor(c, hn::BitCast(df, hn::And(hn::ShiftLeft<30>(hn::Add(q, one)), sign_mask)));
  x = hn::Mul(r, c);
  y = hn::Mul(r, s);
}

/* n steps of the generators at st into draws: step i's sixteen draws of block g at
   dst[g] + 16 i (none: not stored), each pair (the draws at 2 j and 2 j + 1) times
   kp[g][8 i + j] when scaled (a piece not stored reads any 8 n floats). */
template <size_t G, bool kScaled>
static HWY_NOINLINE void Steps(uint32_t *st, uint64_t n, float *const *dst0, const float *const *kp0) {
  using T = GenLanes<G>;
  const typename T::DU du;
  const typename T::DF df;
  using VU = typename T::VU;
  constexpr size_t kMax = T::kMax;
  const size_t L = T::L(), NV = T::NV();
  VU s0[kMax], s1[kMax], s2[kMax], s3[kMax];
  for (size_t v = 0; v < NV; v++) {
    s0[v] = hn::Load(du, st + 0 * 8 * G + v * L); s1[v] = hn::Load(du, st + 1 * 8 * G + v * L);
    s2[v] = hn::Load(du, st + 2 * 8 * G + v * L); s3[v] = hn::Load(du, st + 3 * 8 * G + v * L);
  }
  float *dst[G];                                   // local: the stores cannot move them
  const float *kp[G];
  for (size_t g = 0; g < G; g++) { dst[g] = dst0[g]; kp[g] = kp0[g]; }
  for (uint64_t i = 0; i < n; i++) {
    VU A[kMax], B[kMax];
    for (size_t v = 0; v < NV; v++) A[v] = Next(s0[v], s1[v], s2[v], s3[v]);
    for (size_t v = 0; v < NV; v++) B[v] = Next(s0[v], s1[v], s2[v], s3[v]);
    for (size_t v = 0; v < NV; v++) {
      hn::Vec<decltype(df)> x, y;
      BoxMuller(df, du, A[v], B[v], x, y);
      if constexpr (G == 1) {
        if constexpr (kScaled) {
          const auto k = hn::LoadU(df, kp[0] + 8 * i + v * L);
          x = hn::Mul(x, k); y = hn::Mul(y, k);
        }
        hn::StoreInterleaved2(x, y, df, dst[0] + 16 * i + 2 * v * L);
      } else {
        static_assert(G == 2, "two blocks a vector at most");
        if constexpr (kScaled) {
          const hn::Half<decltype(df)> dh;
          const auto k = hn::Combine(df, hn::LoadU(dh, kp[1] + 8 * i), hn::LoadU(dh, kp[0] + 8 * i));
          x = hn::Mul(x, k); y = hn::Mul(y, k);
        }
        if (dst[0]) hn::StoreU(hn::InterleaveWholeLower(df, x, y), df, dst[0] + 16 * i);
        if (dst[1]) hn::StoreU(hn::InterleaveWholeUpper(df, x, y), df, dst[1] + 16 * i);
      }
    }
  }
  for (size_t v = 0; v < NV; v++) {
    hn::Store(s0[v], du, st + 0 * 8 * G + v * L); hn::Store(s1[v], du, st + 1 * 8 * G + v * L);
    hn::Store(s2[v], du, st + 2 * 8 * G + v * L); hn::Store(s3[v], du, st + 3 * 8 * G + v * L);
  }
}

/* G pieces (Piece), piece g's block's generators in lanes 8 g .. 8 g + 7 (GenLanes), run from
   the block's start. Of a piece's steps [q0, q1), those whose sixteen draws are all its own go
   straight into its row (scaled, when its pairs are the row's: at even), the others through
   buf, only its draws copied out; steps before q0 are not stored. The steps run in spans in
   which no piece changes how it stores them: the long ones, where every piece stores straight
   into its row, in one Steps call, the few a piece stores in part one at a time, and where no
   piece stores, only the generators move (Skip). */
/* SIMD Threefry-2x32-20 of counters (x0, x1) under key (k0, k1): bit-identical to threefry. */
template <class DU, class VU>
static HWY_INLINE void ThreefryVec(DU du, VU &x0, VU &x1, uint32_t k0, uint32_t k1) {
  const uint32_t k2 = k0 ^ k1 ^ 0x1BD11BDAu;
  const VU vk0 = hn::Set(du, k0), vk1 = hn::Set(du, k1), vk2 = hn::Set(du, k2);
  x0 = hn::Add(x0, vk0); x1 = hn::Add(x1, vk1);
  // s = 1
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<13>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<15>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<26>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<6>(x1), x0);
  x0 = hn::Add(x0, vk1); x1 = hn::Add(x1, hn::Set(du, k2 + 1u));
  // s = 2
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<17>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<29>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<16>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<24>(x1), x0);
  x0 = hn::Add(x0, vk2); x1 = hn::Add(x1, hn::Set(du, k0 + 2u));
  // s = 3
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<13>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<15>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<26>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<6>(x1), x0);
  x0 = hn::Add(x0, vk0); x1 = hn::Add(x1, hn::Set(du, k1 + 3u));
  // s = 4
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<17>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<29>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<16>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<24>(x1), x0);
  x0 = hn::Add(x0, vk1); x1 = hn::Add(x1, hn::Set(du, k2 + 4u));
  // s = 5
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<13>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<15>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<26>(x1), x0);
  x0 = hn::Add(x0, x1); x1 = hn::Xor(Rotl<6>(x1), x0);
  x0 = hn::Add(x0, vk2); x1 = hn::Add(x1, hn::Set(du, k0 + 5u));
}

/* Seed all G blocks' eight generators across SIMD lanes in two Threefry passes (even counters
   give words 0, 1; odd counters give words 2, 3), bit-for-bit matching seed_block. */
template <size_t G>
static HWY_INLINE void SeedBlocks(uint32_t *st, const Piece *pc, uint32_t k0, uint32_t k1) {
  using T = GenLanes<G>;
  const typename T::DU du;
  const size_t L = T::L(), NV = T::NV();
  HWY_ALIGN uint32_t x0e[8 * G], x1e[8 * G], x0o[8 * G], x1o[8 * G];
  for (size_t g = 0; g < G; g++) {
    for (uint32_t j = 0; j < 8; j++) {
      const uint64_t ce = pc[g].b * 16 + 2 * j, co = ce + 1;
      x0e[8 * g + j] = (uint32_t)ce; x1e[8 * g + j] = (uint32_t)(ce >> 32);
      x0o[8 * g + j] = (uint32_t)co; x1o[8 * g + j] = (uint32_t)(co >> 32);
    }
  }
  const auto one = hn::Set(du, 1u);
  for (size_t v = 0; v < NV; v++) {
    auto e0 = hn::Load(du, x0e + v * L), e1 = hn::Load(du, x1e + v * L);
    ThreefryVec(du, e0, e1, k0, k1);
    hn::Store(hn::Or(e0, one), du, st + 0 * 8 * G + v * L);
    hn::Store(e1, du, st + 1 * 8 * G + v * L);
    auto o0 = hn::Load(du, x0o + v * L), o1 = hn::Load(du, x1o + v * L);
    ThreefryVec(du, o0, o1, k0, k1);
    hn::Store(o0, du, st + 2 * 8 * G + v * L);
    hn::Store(o1, du, st + 3 * 8 * G + v * L);
  }
}

template <size_t G, bool kScaled>
static void FillPieces(const Piece *pc, uint32_t k0, uint32_t k1) {
  HWY_ALIGN uint32_t st[32 * G];
  HWY_ALIGN float buf[16 * G];                     // a step a piece stores only in part
  static const float ones[8] = {1, 1, 1, 1, 1, 1, 1, 1};   // the scale of a step not scaled in place
  /* piece g's steps [q0, q1) hold its draws, of which [f0, f1) go straight into its row */
  SeedBlocks<G>(st, pc, k0, k1);
  uint64_t q0[G], q1[G], f0[G], f1[G], qmax = 0;
  for (size_t g = 0; g < G; g++) {
    const Piece &p = pc[g];
    q0[g] = p.lo / 16; q1[g] = (p.hi + 15) / 16;
    const bool straight = !kScaled || (p.at & 1) == 0;
    f0[g] = straight ? (p.lo + 15) / 16 : q1[g];
    f1[g] = straight ? p.hi / 16 : q1[g];
    if (f1[g] < f0[g]) f1[g] = f0[g];
    qmax = q1[g] > qmax ? q1[g] : qmax;
  }
  for (uint64_t q = 0; q < qmax;) {
    /* the span [q, qe) and how each piece stores its steps there: 0 not at all, 1 straight
       into its row, 2 through buf */
    uint64_t qe = qmax;
    int mode[G];
    bool any = false, part = false;
    float *dst[G];
    const float *kp[G];
    for (size_t g = 0; g < G; g++) {
      if (q < q0[g]) { mode[g] = 0; qe = q0[g] < qe ? q0[g] : qe; }
      else if (q >= q1[g]) mode[g] = 0;
      else if (q >= f0[g] && q < f1[g]) { mode[g] = 1; qe = f1[g] < qe ? f1[g] : qe; }
      else { mode[g] = 2; const uint64_t e = q < f0[g] ? f0[g] : q1[g]; qe = e < qe ? e : qe; }
      const Piece &p = pc[g];
      dst[g] = mode[g] == 1 ? p.row + (p.at + (int64_t)(16 * q)) : mode[g] == 2 ? buf + 16 * g : nullptr;
      kp[g] = kScaled && mode[g] == 1 ? p.sc + (p.at + (int64_t)(16 * q)) / 2 : ones;
      any = any || mode[g] != 0;
      part = part || mode[g] == 2;
    }
    if (!any) { Skip<G>(st, qe - q); q = qe; continue; }
    if (!part) {
      /* a piece not stored reads the scale of one that is (ones holds a step's) */
      for (size_t g = 0; g < G; g++) if (mode[g] == 0) kp[g] = kp[G - 1 - g];
      Steps<G, kScaled>(st, qe - q, dst, kp);
      q = qe;
      continue;
    }
    for (; q < qe; q++) {
      Steps<G, kScaled>(st, 1, dst, kp);
      for (size_t g = 0; g < G; g++) {
        if (mode[g] == 1) { dst[g] += 16; if (kScaled) kp[g] += 8; }
        if (mode[g] != 2) continue;
        /* the piece's draws [d0, d1) of the step, scaled one at a time */
        const Piece &p = pc[g];
        const uint64_t a = 16 * q, d0 = a > p.lo ? a : p.lo, d1 = a + 16 < p.hi ? a + 16 : p.hi;
        float *o = p.row + (p.at + (int64_t)d0);
        const float *src = buf + 16 * g + (d0 - a);
        if (!kScaled) {
          memcpy(o, src, (d1 - d0) * sizeof(float));
        } else {
          for (uint64_t d = d0; d < d1; d++) o[d - d0] = src[d - d0] * p.sc[(p.at + (int64_t)d) / 2];
        }
      }
    }
  }
}

/* G pieces, all scaled or none (one fill's). */
template <size_t G>
static void Fill(const Piece *pc, uint32_t k0, uint32_t k1) {
  if (pc[0].sc) FillPieces<G, true>(pc, k0, k1);
  else FillPieces<G, false>(pc, k0, k1);
}

/* Rows of draws (ap_gauss_fill_rows): out[r * ostride + i] = draw offset + r * step + i of
   stream seed, times scale[i / 2] when scale is given, for r < rows and i < len; rows do not
   overlap (ostride >= len), and nothing of a row past len is written. With keep, only the
   rows r with keep[r] nonzero are drawn (the others are left as they are). Each block a row
   reads is a piece (Piece), kGroup pieces generated together across blocks and rows. */
void GaussFillRows(float *out, size_t ostride, size_t rows, size_t len, uint64_t seed,
                   uint64_t offset, uint64_t step, const float *scale,
                   const unsigned char *keep) {
  const uint32_t k0 = (uint32_t)seed, k1 = (uint32_t)(seed >> 32);
  Piece pend[kGroup];
  size_t np = 0;
  for (size_t r = 0; r < rows; r++) {
    if (keep && !keep[r]) continue;
    const uint64_t s = offset + r * step, end = s + len;
    float *row = out + r * ostride;
    for (uint64_t pos = s; pos < end;) {
      const uint64_t b = pos / kBlock, b0 = b * kBlock;
      const uint64_t hi = end < b0 + kBlock ? end : b0 + kBlock;
      pend[np++] = Piece{row, scale, (int64_t)(b0 - s), b, (uint32_t)(pos - b0), (uint32_t)(hi - b0)};
      if (np == kGroup) { Fill<kGroup>(pend, k0, k1); np = 0; }
      pos = hi;
    }
  }
  if (np) Fill<1>(pend, k0, k1);                   // a last piece alone
}

void GaussFill(float *out, size_t n, uint64_t seed, uint64_t offset) {
  GaussFillRows(out, n, 1, n, seed, offset, 0, nullptr, nullptr);
}

}  // namespace HWY_NAMESPACE
}  // namespace ap_gauss
HWY_AFTER_NAMESPACE();

#if HWY_ONCE
#if AP_HAVE_AVX1
/* AVX1 (Sandy and Ivy Bridge): two 128-bit integer vectors hold the block's eight generators
   (AVX1 has no 256-bit integer ALU), and one 8-float __m256 vector evaluates Box-Muller,
   scaling and interleaved stores, operation for operation matching SSE4's float arithmetic. */
HWY_PUSH_ATTRIBUTES("avx")
namespace ap_gauss {
namespace avx1 {

template <int R>
static HWY_INLINE __m128i Rotl128(__m128i x) {
  return _mm_or_si128(_mm_slli_epi32(x, R), _mm_srli_epi32(x, 32 - R));
}

static HWY_INLINE __m256 Combine128Ps(__m128 lo, __m128 hi) {
  return _mm256_insertf128_ps(_mm256_castps128_ps256(lo), hi, 1);
}

static HWY_INLINE __m256 CvtCombine128Epi32(__m128i lo, __m128i hi) {
  return _mm256_cvtepi32_ps(_mm256_insertf128_si256(_mm256_castsi128_si256(lo), hi, 1));
}

static HWY_INLINE __m256 FmaddNf(__m256 a, __m256 b, __m256 c) {
  return _mm256_add_ps(_mm256_mul_ps(a, b), c);
}

static HWY_INLINE __m128i Next128(__m128i &s0, __m128i &s1, __m128i &s2, __m128i &s3) {
  const __m128i r = _mm_add_epi32(Rotl128<7>(_mm_add_epi32(s0, s3)), s0);
  const __m128i t = _mm_slli_epi32(s1, 9);
  s2 = _mm_xor_si128(s2, s0); s3 = _mm_xor_si128(s3, s1);
  s1 = _mm_xor_si128(s1, s2); s0 = _mm_xor_si128(s0, s3);
  s2 = _mm_xor_si128(s2, t); s3 = Rotl128<11>(s3);
  return r;
}

static HWY_INLINE void Threefry128(__m128i &x0, __m128i &x1, uint32_t k0, uint32_t k1) {
  const uint32_t k2 = k0 ^ k1 ^ 0x1BD11BDAu;
  const __m128i vk0 = _mm_set1_epi32((int32_t)k0);
  const __m128i vk1 = _mm_set1_epi32((int32_t)k1);
  const __m128i vk2 = _mm_set1_epi32((int32_t)k2);
  x0 = _mm_add_epi32(x0, vk0); x1 = _mm_add_epi32(x1, vk1);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<13>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<15>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<26>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<6>(x1), x0);
  x0 = _mm_add_epi32(x0, vk1); x1 = _mm_add_epi32(x1, _mm_set1_epi32((int32_t)(k2 + 1u)));
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<17>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<29>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<16>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<24>(x1), x0);
  x0 = _mm_add_epi32(x0, vk2); x1 = _mm_add_epi32(x1, _mm_set1_epi32((int32_t)(k0 + 2u)));
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<13>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<15>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<26>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<6>(x1), x0);
  x0 = _mm_add_epi32(x0, vk0); x1 = _mm_add_epi32(x1, _mm_set1_epi32((int32_t)(k1 + 3u)));
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<17>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<29>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<16>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<24>(x1), x0);
  x0 = _mm_add_epi32(x0, vk1); x1 = _mm_add_epi32(x1, _mm_set1_epi32((int32_t)(k2 + 4u)));
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<13>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<15>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<26>(x1), x0);
  x0 = _mm_add_epi32(x0, x1); x1 = _mm_xor_si128(Rotl128<6>(x1), x0);
  x0 = _mm_add_epi32(x0, vk2); x1 = _mm_add_epi32(x1, _mm_set1_epi32((int32_t)(k0 + 5u)));
}

static HWY_INLINE void SeedBlock128(uint32_t *st, uint64_t b, uint32_t k0, uint32_t k1) {
  alignas(16) uint32_t x0e[8], x1e[8], x0o[8], x1o[8];
  for (uint32_t j = 0; j < 8; j++) {
    const uint64_t ce = b * 16 + 2 * j, co = ce + 1;
    x0e[j] = (uint32_t)ce; x1e[j] = (uint32_t)(ce >> 32);
    x0o[j] = (uint32_t)co; x1o[j] = (uint32_t)(co >> 32);
  }
  const __m128i one = _mm_set1_epi32(1);
  for (size_t v = 0; v < 2; v++) {
    __m128i e0 = _mm_load_si128((const __m128i *)(x0e + 4 * v));
    __m128i e1 = _mm_load_si128((const __m128i *)(x1e + 4 * v));
    Threefry128(e0, e1, k0, k1);
    _mm_store_si128((__m128i *)(st + 0 * 8 + 4 * v), _mm_or_si128(e0, one));
    _mm_store_si128((__m128i *)(st + 1 * 8 + 4 * v), e1);
    __m128i o0 = _mm_load_si128((const __m128i *)(x0o + 4 * v));
    __m128i o1 = _mm_load_si128((const __m128i *)(x1o + 4 * v));
    Threefry128(o0, o1, k0, k1);
    _mm_store_si128((__m128i *)(st + 2 * 8 + 4 * v), o0);
    _mm_store_si128((__m128i *)(st + 3 * 8 + 4 * v), o1);
  }
}

static HWY_NOINLINE void Skip128(uint32_t *st, uint64_t n) {
  for (size_t v = 0; v < 2; v++) {
    __m128i s0 = _mm_load_si128((const __m128i *)(st + 0 * 8 + 4 * v));
    __m128i s1 = _mm_load_si128((const __m128i *)(st + 1 * 8 + 4 * v));
    __m128i s2 = _mm_load_si128((const __m128i *)(st + 2 * 8 + 4 * v));
    __m128i s3 = _mm_load_si128((const __m128i *)(st + 3 * 8 + 4 * v));
    for (uint64_t i = 0; i < 2 * n; i++) (void)Next128(s0, s1, s2, s3);
    _mm_store_si128((__m128i *)(st + 0 * 8 + 4 * v), s0);
    _mm_store_si128((__m128i *)(st + 1 * 8 + 4 * v), s1);
    _mm_store_si128((__m128i *)(st + 2 * 8 + 4 * v), s2);
    _mm_store_si128((__m128i *)(st + 3 * 8 + 4 * v), s3);
  }
}

static HWY_INLINE void BoxMuller8(__m128i a0, __m128i a1, __m128i b0, __m128i b1,
                                  __m256 &x, __m256 &y) {
  const __m128i one_i = _mm_set1_epi32(1);
  const __m128i c_fold = _mm_set1_epi32(0x004afb0d);
  const __m128i c_151 = _mm_set1_epi32(151);
  const __m128i c_mant = _mm_set1_epi32(0x007fffff);
  const __m128i c_sqrt05 = _mm_set1_epi32(0x3f3504f3);
  const __m128i c_qhalf = _mm_set1_epi32(1 << 21);
  const __m256 one_f = _mm256_set1_ps(1.0f);
  const __m256 sign_ps = _mm256_set1_ps(-0.0f);

  const __m128 kf0 = _mm_cvtepi32_ps(_mm_add_epi32(_mm_srli_epi32(a0, 8), one_i));
  const __m128 kf1 = _mm_cvtepi32_ps(_mm_add_epi32(_mm_srli_epi32(a1, 8), one_i));
  const __m128i adj0 = _mm_add_epi32(_mm_castps_si128(kf0), c_fold);
  const __m128i adj1 = _mm_add_epi32(_mm_castps_si128(kf1), c_fold);
  const __m256 nef = CvtCombine128Epi32(_mm_sub_epi32(c_151, _mm_srli_epi32(adj0, 23)),
                                        _mm_sub_epi32(c_151, _mm_srli_epi32(adj1, 23)));
  const __m256 m = Combine128Ps(
      _mm_castsi128_ps(_mm_add_epi32(_mm_and_si128(adj0, c_mant), c_sqrt05)),
      _mm_castsi128_ps(_mm_add_epi32(_mm_and_si128(adj1, c_mant), c_sqrt05)));
  const __m256 f = _mm256_sub_ps(m, one_f);
  const __m256 f2 = _mm256_mul_ps(f, f);
  __m256 p = _mm256_set1_ps(-0.2397264838218689f);
  p = FmaddNf(p, f, _mm256_set1_ps(0.3752340078353882f));
  p = FmaddNf(p, f, _mm256_set1_ps(-0.40985167026519775f));
  p = FmaddNf(p, f, _mm256_set1_ps(0.4979553520679474f));
  p = FmaddNf(p, f, _mm256_set1_ps(-0.6663109064102173f));
  p = FmaddNf(p, f, _mm256_set1_ps(1.0000296831130981f));
  const __m256 lo = FmaddNf(p, f2, _mm256_mul_ps(nef, _mm256_set1_ps(2.857213530660374e-6f)));
  const __m256 hi = _mm256_sub_ps(_mm256_mul_ps(nef, _mm256_set1_ps(1.38629150390625f)),
                                  _mm256_add_ps(f, f));
  const __m256 r = _mm256_sqrt_ps(_mm256_add_ps(hi, lo));

  const __m128i bh0 = _mm_srli_epi32(b0, 8), bh1 = _mm_srli_epi32(b1, 8);
  const __m128i q0 = _mm_srli_epi32(_mm_add_epi32(bh0, c_qhalf), 22);
  const __m128i q1 = _mm_srli_epi32(_mm_add_epi32(bh1, c_qhalf), 22);
  const __m256 t = _mm256_mul_ps(
      CvtCombine128Epi32(_mm_sub_epi32(bh0, _mm_slli_epi32(q0, 22)),
                         _mm_sub_epi32(bh1, _mm_slli_epi32(q1, 22))),
      _mm256_set1_ps(1.0f / 4194304.0f));
  const __m256 t2 = _mm256_mul_ps(t, t);
  __m256 sp = _mm256_set1_ps(-0.004602177068591118f);
  sp = FmaddNf(sp, t2, _mm256_set1_ps(0.07968022674322128f));
  sp = FmaddNf(sp, t2, _mm256_set1_ps(-0.6459634900093079f));
  sp = _mm256_mul_ps(t, FmaddNf(sp, t2, _mm256_set1_ps(1.5707963705062866f)));
  __m256 cp = _mm256_set1_ps(-0.02052159793674946f);
  cp = FmaddNf(cp, t2, _mm256_set1_ps(0.25363752245903015f));
  cp = FmaddNf(FmaddNf(cp, t2, _mm256_set1_ps(-1.233700156211853f)), t2, one_f);

  const __m256 swap_v = Combine128Ps(_mm_castsi128_ps(_mm_slli_epi32(q0, 31)),
                                     _mm_castsi128_ps(_mm_slli_epi32(q1, 31)));
  __m256 s = _mm256_blendv_ps(sp, cp, swap_v);
  __m256 c = _mm256_blendv_ps(cp, sp, swap_v);
  const __m256 ss = _mm256_and_ps(Combine128Ps(_mm_castsi128_ps(_mm_slli_epi32(q0, 30)),
                                               _mm_castsi128_ps(_mm_slli_epi32(q1, 30))),
                                  sign_ps);
  const __m256 cs = _mm256_and_ps(
      Combine128Ps(_mm_castsi128_ps(_mm_slli_epi32(_mm_add_epi32(q0, one_i), 30)),
                   _mm_castsi128_ps(_mm_slli_epi32(_mm_add_epi32(q1, one_i), 30))),
      sign_ps);
  s = _mm256_xor_ps(s, ss);
  c = _mm256_xor_ps(c, cs);
  x = _mm256_mul_ps(r, c);
  y = _mm256_mul_ps(r, s);
}

template <bool kScaled>
static HWY_NOINLINE void Steps8(uint32_t *st, uint64_t n, float *dst, const float *kp) {
  __m128i s0[2], s1[2], s2[2], s3[2];
  for (size_t v = 0; v < 2; v++) {
    s0[v] = _mm_load_si128((const __m128i *)(st + 0 * 8 + 4 * v));
    s1[v] = _mm_load_si128((const __m128i *)(st + 1 * 8 + 4 * v));
    s2[v] = _mm_load_si128((const __m128i *)(st + 2 * 8 + 4 * v));
    s3[v] = _mm_load_si128((const __m128i *)(st + 3 * 8 + 4 * v));
  }
  for (uint64_t i = 0; i < n; i++) {
    const __m128i a0 = Next128(s0[0], s1[0], s2[0], s3[0]);
    const __m128i a1 = Next128(s0[1], s1[1], s2[1], s3[1]);
    const __m128i b0 = Next128(s0[0], s1[0], s2[0], s3[0]);
    const __m128i b1 = Next128(s0[1], s1[1], s2[1], s3[1]);
    __m256 x, y;
    BoxMuller8(a0, a1, b0, b1, x, y);
    if constexpr (kScaled) {
      const __m256 k = _mm256_loadu_ps(kp + 8 * i);
      x = _mm256_mul_ps(x, k);
      y = _mm256_mul_ps(y, k);
    }
    const __m256 lo16 = _mm256_unpacklo_ps(x, y), hi16 = _mm256_unpackhi_ps(x, y);
    _mm256_storeu_ps(dst + 16 * i, _mm256_permute2f128_ps(lo16, hi16, 0x20));
    _mm256_storeu_ps(dst + 16 * i + 8, _mm256_permute2f128_ps(lo16, hi16, 0x31));
  }
  for (size_t v = 0; v < 2; v++) {
    _mm_store_si128((__m128i *)(st + 0 * 8 + 4 * v), s0[v]);
    _mm_store_si128((__m128i *)(st + 1 * 8 + 4 * v), s1[v]);
    _mm_store_si128((__m128i *)(st + 2 * 8 + 4 * v), s2[v]);
    _mm_store_si128((__m128i *)(st + 3 * 8 + 4 * v), s3[v]);
  }
}

template <bool kScaled>
static void FillPiece8(const Piece &p, uint32_t k0, uint32_t k1) {
  alignas(32) uint32_t st[32];
  alignas(32) float buf[16];
  static const float ones[8] = {1, 1, 1, 1, 1, 1, 1, 1};
  SeedBlock128(st, p.b, k0, k1);
  const uint64_t q0 = p.lo / 16, q1 = (p.hi + 15) / 16;
  const bool straight = !kScaled || (p.at & 1) == 0;
  const uint64_t f0 = straight ? (p.lo + 15) / 16 : q1;
  uint64_t f1 = straight ? p.hi / 16 : q1;
  if (f1 < f0) f1 = f0;
  if (q0) Skip128(st, q0);
  for (uint64_t q = q0; q < q1;) {
    if (q >= f0 && q < f1) {
      Steps8<kScaled>(st, f1 - q, p.row + (p.at + (int64_t)(16 * q)),
                      kScaled ? p.sc + (p.at + (int64_t)(16 * q)) / 2 : ones);
      q = f1;
      continue;
    }
    const uint64_t qe = q < f0 ? f0 : q1;
    for (; q < qe; q++) {
      Steps8<kScaled>(st, 1, buf, ones);
      const uint64_t a = 16 * q, d0 = a > p.lo ? a : p.lo, d1 = a + 16 < p.hi ? a + 16 : p.hi;
      float *o = p.row + (p.at + (int64_t)d0);
      const float *src = buf + (d0 - a);
      if (!kScaled) {
        memcpy(o, src, (d1 - d0) * sizeof(float));
      } else {
        for (uint64_t d = d0; d < d1; d++) o[d - d0] = src[d - d0] * p.sc[(p.at + (int64_t)d) / 2];
      }
    }
  }
}

static void GaussFillRows(float *out, size_t ostride, size_t rows, size_t len, uint64_t seed,
                          uint64_t offset, uint64_t step, const float *scale,
                          const unsigned char *keep) {
  const uint32_t k0 = (uint32_t)seed, k1 = (uint32_t)(seed >> 32);
  for (size_t r = 0; r < rows; r++) {
    if (keep && !keep[r]) continue;
    const uint64_t s = offset + r * step, end = s + len;
    float *row = out + r * ostride;
    for (uint64_t pos = s; pos < end;) {
      const uint64_t b = pos / kBlock, b0 = b * kBlock;
      const uint64_t hi = end < b0 + kBlock ? end : b0 + kBlock;
      const Piece p{row, scale, (int64_t)(b0 - s), b, (uint32_t)(pos - b0), (uint32_t)(hi - b0)};
      if (scale) FillPiece8<true>(p, k0, k1);
      else FillPiece8<false>(p, k0, k1);
      pos = hi;
    }
  }
}

}  // namespace avx1
}  // namespace ap_gauss
HWY_POP_ATTRIBUTES
#endif

namespace ap_gauss {
HWY_EXPORT(GaussFill);
HWY_EXPORT(GaussFillRows);
#if AP_HAVE_AVX1
static inline bool use_avx1() {
  const ap_backend *b = ap_backend_active();
  return b && !strcmp(b->name, "AVX");
}
#endif
/* Dispatched unqualified from inside the namespace: a single-target build (macOS arm64,
   NEON only) falls back to HWY_STATIC_DISPATCH, which makes ap_gauss::GaussFill into
   N_NEON::ap_gauss::GaussFill, undeclared (see kernel.cc's active()). */
static void Fill(float *out, size_t n, uint64_t seed, uint64_t offset) {
#if AP_HAVE_AVX1
  if (use_avx1()) { avx1::GaussFillRows(out, n, 1, n, seed, offset, 0, nullptr, nullptr); return; }
#endif
  HWY_DYNAMIC_DISPATCH(GaussFill)(out, n, seed, offset);
}
static void FillRows(float *out, size_t ostride, size_t rows, size_t len, uint64_t seed,
                     uint64_t offset, uint64_t step, const float *scale,
                     const unsigned char *keep) {
#if AP_HAVE_AVX1
  if (use_avx1()) {
    avx1::GaussFillRows(out, ostride, rows, len, seed, offset, step, scale, keep);
    return;
  }
#endif
  HWY_DYNAMIC_DISPATCH(GaussFillRows)(out, ostride, rows, len, seed, offset, step, scale, keep);
}
}  // namespace ap_gauss
extern "C" void ap_gauss_fill(float *out, size_t n, uint64_t seed, uint64_t offset) {
  if (n) ap_gauss::Fill(out, n, seed, offset);
}
extern "C" void ap_gauss_fill_rows(float *out, size_t ostride, size_t rows, size_t len,
                                   uint64_t seed, uint64_t offset, uint64_t step,
                                   const float *scale) {
  if (rows && len) ap_gauss::FillRows(out, ostride, rows, len, seed, offset, step, scale, nullptr);
}
/* ap_gauss_fill_rows for the rows r with keep[r] nonzero only: the others are not written. */
extern "C" void ap_gauss_fill_rows_kept(float *out, size_t ostride, size_t rows, size_t len,
                                        uint64_t seed, uint64_t offset, uint64_t step,
                                        const float *scale, const unsigned char *keep) {
  if (rows && len) ap_gauss::FillRows(out, ostride, rows, len, seed, offset, step, scale, keep);
}
#endif
