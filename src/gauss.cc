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
 * transformed noise resolves. The float part (log, sincos) differs between ISAs in the last
 * ulp; within one it is lane by lane the same arithmetic at 8 lanes and at 16. A read
 * starting inside a block runs the block's generators through the steps before it without
 * storing them, and one ending inside it generates only the steps it reads. */
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#undef HWY_TARGET_INCLUDE
#define HWY_TARGET_INCLUDE "gauss.cc"
#include "hwy/foreach_target.h"  // must come before highway.h
#include "hwy/highway.h"
#include "hwy/contrib/math/math-inl.h"

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
  const auto tiny = hn::Set(df, 1.0f / 16777216.0f);
  const auto one = hn::Set(du, 1u);
  const auto m2 = hn::Set(df, -2.0f);
  const auto twopi = hn::Set(df, 6.283185307179586f);
  for (uint64_t i = 0; i < n; i++) {
    VU A[kMax], B[kMax];
    for (size_t v = 0; v < NV; v++) A[v] = Next(s0[v], s1[v], s2[v], s3[v]);
    for (size_t v = 0; v < NV; v++) B[v] = Next(s0[v], s1[v], s2[v], s3[v]);
    for (size_t v = 0; v < NV; v++) {
      const auto u1 = hn::Mul(hn::ConvertTo(df, hn::Add(hn::ShiftRight<8>(A[v]), one)), tiny);
      const auto u2 = hn::Mul(hn::ConvertTo(df, hn::ShiftRight<8>(B[v])), tiny);
      const auto r = hn::Sqrt(hn::Mul(m2, hn::Log(df, u1)));
      hn::Vec<decltype(df)> s, c;
      hn::SinCos(df, hn::Mul(twopi, u2), s, c);
      auto x = hn::Mul(r, c), y = hn::Mul(r, s);
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
template <size_t G, bool kScaled>
static void FillPieces(const Piece *pc, uint32_t k0, uint32_t k1) {
  HWY_ALIGN uint32_t st[32 * G];
  HWY_ALIGN float buf[16 * G];                     // a step a piece stores only in part
  static const float ones[8] = {1, 1, 1, 1, 1, 1, 1, 1};   // the scale of a step not scaled in place
  /* piece g's steps [q0, q1) hold its draws, of which [f0, f1) go straight into its row */
  uint64_t q0[G], q1[G], f0[G], f1[G], qmax = 0;
  for (size_t g = 0; g < G; g++) {
    const Piece &p = pc[g];
    seed_block(st + 8 * g, 8 * G, p.b, k0, k1);
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
   overlap (ostride >= len), and nothing of a row past len is written. Each block a row reads
   is a piece (Piece), kGroup pieces generated together across blocks and rows. */
void GaussFillRows(float *out, size_t ostride, size_t rows, size_t len, uint64_t seed,
                   uint64_t offset, uint64_t step, const float *scale) {
  const uint32_t k0 = (uint32_t)seed, k1 = (uint32_t)(seed >> 32);
  Piece pend[kGroup];
  size_t np = 0;
  for (size_t r = 0; r < rows; r++) {
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
  GaussFillRows(out, n, 1, n, seed, offset, 0, nullptr);
}

}  // namespace HWY_NAMESPACE
}  // namespace ap_gauss
HWY_AFTER_NAMESPACE();

#if HWY_ONCE
namespace ap_gauss {
HWY_EXPORT(GaussFill);
HWY_EXPORT(GaussFillRows);
/* Dispatched unqualified from inside the namespace: a single-target build (macOS arm64,
   NEON only) falls back to HWY_STATIC_DISPATCH, which makes ap_gauss::GaussFill into
   N_NEON::ap_gauss::GaussFill, undeclared (see kernel.cc's active()). */
static void Fill(float *out, size_t n, uint64_t seed, uint64_t offset) {
  HWY_DYNAMIC_DISPATCH(GaussFill)(out, n, seed, offset);
}
static void FillRows(float *out, size_t ostride, size_t rows, size_t len, uint64_t seed,
                     uint64_t offset, uint64_t step, const float *scale) {
  HWY_DYNAMIC_DISPATCH(GaussFillRows)(out, ostride, rows, len, seed, offset, step, scale);
}
}  // namespace ap_gauss
extern "C" void ap_gauss_fill(float *out, size_t n, uint64_t seed, uint64_t offset) {
  if (n) ap_gauss::Fill(out, n, seed, offset);
}
extern "C" void ap_gauss_fill_rows(float *out, size_t ostride, size_t rows, size_t len,
                                   uint64_t seed, uint64_t offset, uint64_t step,
                                   const float *scale) {
  if (rows && len) ap_gauss::FillRows(out, ostride, rows, len, seed, offset, step, scale);
}
#endif
