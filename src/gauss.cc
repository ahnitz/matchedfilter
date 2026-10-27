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
 * starting inside a block generates the block and skips its first draws; one ending inside
 * it generates only the steps it reads. */
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

/* One block's share of a fill: steps [0, q1) of block b, the draws 16 q .. 16 q + 15 of step
   q at out + 16 q, each pair (the draws at 16 q + 2 j and 16 q + 2 j + 1) times sc[8 q + j]
   when sc is given. */
struct Piece {
  float *out;
  const float *sc;
  uint64_t b, q1;
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

/* G pieces (Piece) of distinct blocks, block g's generators in lanes 8 g .. 8 g + 7 of one
   vector (G = 1: the eight in 8 / L vectors of L lanes); each piece's steps past its q1 are
   left out of its output. */
template <size_t G, bool kScaled>
static void FillPieces(const Piece *pc, uint32_t k0, uint32_t k1) {
  const hn::CappedTag<uint32_t, 8 * G> du;
  const hn::Rebind<float, decltype(du)> df;
  constexpr size_t kMax = 8;
  const size_t L = hn::Lanes(du);
  const size_t NV = G == 1 ? 8 / L : 1;            // vectors holding the generators
  using VU = decltype(hn::Zero(du));
  HWY_ALIGN uint32_t st[32 * G];
  uint64_t qmax = 0;
  for (size_t g = 0; g < G; g++) {
    seed_block(st + 8 * g, 8 * G, pc[g].b, k0, k1);
    qmax = pc[g].q1 > qmax ? pc[g].q1 : qmax;
  }
  VU s0[kMax], s1[kMax], s2[kMax], s3[kMax];
  for (size_t v = 0; v < NV; v++) {
    s0[v] = hn::Load(du, st + 0 * 8 * G + v * L); s1[v] = hn::Load(du, st + 1 * 8 * G + v * L);
    s2[v] = hn::Load(du, st + 2 * 8 * G + v * L); s3[v] = hn::Load(du, st + 3 * 8 * G + v * L);
  }
  const auto tiny = hn::Set(df, 1.0f / 16777216.0f);
  const auto one = hn::Set(du, 1u);
  const auto m2 = hn::Set(df, -2.0f);
  const auto twopi = hn::Set(df, 6.283185307179586f);
  for (uint64_t q = 0; q < qmax; q++) {
    VU A[kMax], B[kMax];
    for (int half = 0; half < 2; half++) {
      for (size_t v = 0; v < NV; v++) {          // xoshiro128++ step
        const VU r = hn::Add(Rotl<7>(hn::Add(s0[v], s3[v])), s0[v]);
        const VU t = hn::ShiftLeft<9>(s1[v]);
        s2[v] = hn::Xor(s2[v], s0[v]); s3[v] = hn::Xor(s3[v], s1[v]);
        s1[v] = hn::Xor(s1[v], s2[v]); s0[v] = hn::Xor(s0[v], s3[v]);
        s2[v] = hn::Xor(s2[v], t); s3[v] = Rotl<11>(s3[v]);
        (half ? B : A)[v] = r;
      }
    }
    for (size_t v = 0; v < NV; v++) {
      const auto u1 = hn::Mul(hn::ConvertTo(df, hn::Add(hn::ShiftRight<8>(A[v]), one)), tiny);
      const auto u2 = hn::Mul(hn::ConvertTo(df, hn::ShiftRight<8>(B[v])), tiny);
      const auto r = hn::Sqrt(hn::Mul(m2, hn::Log(df, u1)));
      hn::Vec<decltype(df)> s, c;
      hn::SinCos(df, hn::Mul(twopi, u2), s, c);
      auto x = hn::Mul(r, c), y = hn::Mul(r, s);
      if constexpr (G == 1) {
        if constexpr (kScaled) {
          const auto k = hn::LoadU(df, pc[0].sc + 8 * q + v * L);
          x = hn::Mul(x, k); y = hn::Mul(y, k);
        }
        hn::StoreInterleaved2(x, y, df, pc[0].out + 16 * q + 2 * v * L);
      } else {
        static_assert(G == 2, "two blocks a vector at most");
        if constexpr (kScaled) {
          /* a piece past its last step reads ones (its output is not stored) */
          static const float ones[8] = {1, 1, 1, 1, 1, 1, 1, 1};
          const hn::Half<decltype(df)> dh;
          const float *k0p = q < pc[0].q1 ? pc[0].sc + 8 * q : ones;
          const float *k1p = q < pc[1].q1 ? pc[1].sc + 8 * q : ones;
          const auto k = hn::Combine(df, hn::LoadU(dh, k1p), hn::LoadU(dh, k0p));
          x = hn::Mul(x, k); y = hn::Mul(y, k);
        }
        if (q < pc[0].q1) hn::StoreU(hn::InterleaveWholeLower(df, x, y), df, pc[0].out + 16 * q);
        if (q < pc[1].q1) hn::StoreU(hn::InterleaveWholeUpper(df, x, y), df, pc[1].out + 16 * q);
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
   overlap (ostride >= len). A row's whole blocks, and the starts of blocks it ends inside
   (a multiple of 16 draws), go straight into out, kGroup blocks at a time across rows; the
   rest is copied out of a block generated alone. */
void GaussFillRows(float *out, size_t ostride, size_t rows, size_t len, uint64_t seed,
                   uint64_t offset, uint64_t step, const float *scale) {
  const uint32_t k0 = (uint32_t)seed, k1 = (uint32_t)(seed >> 32);
  HWY_ALIGN float tmp[kBlock];
  uint64_t tmp_b = ~(uint64_t)0, tmp_q1 = 0;      // the block tmp holds, and its steps
  Piece pend[kGroup];
  size_t np = 0;
  for (size_t r = 0; r < rows; r++) {
    const uint64_t s = offset + r * step, end = s + len;
    float *row = out + r * ostride;
    for (uint64_t pos = s; pos < end;) {
      const uint64_t b = pos / kBlock, b0 = b * kBlock;
      const uint64_t hi = end < b0 + kBlock ? end : b0 + kBlock;
      if (pos == b0 && (hi - b0) % 16 == 0 && (!scale || (b0 - s) % 2 == 0)) {
        /* the block's first steps straight into out, scaled there */
        pend[np++] = Piece{row + (b0 - s), scale ? scale + (b0 - s) / 2 : nullptr, b,
                           (hi - b0) / 16};
        if (np == kGroup) { Fill<kGroup>(pend, k0, k1); np = 0; }
      } else {
        const uint64_t q1 = (hi - b0 + 15) / 16;
        if (tmp_b != b || tmp_q1 < q1) {
          const Piece p{tmp, nullptr, b, q1};
          FillPieces<1, false>(&p, k0, k1);
          tmp_b = b; tmp_q1 = q1;
        }
        float *dst = row + (pos - s);
        const float *src = tmp + (pos - b0);
        const uint64_t take = hi - pos;
        if (!scale) {
          memcpy(dst, src, take * sizeof(float));
        } else {
          const uint64_t i0 = pos - s;
          for (uint64_t i = 0; i < take; i++) dst[i] = src[i] * scale[(i0 + i) / 2];
        }
      }
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
