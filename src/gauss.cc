/* Standard normal draws for the gate model's simulations (gatechain: noise block maxima, the
 * signal and direct-refine draws), counter-based so that every value depends only on the seed
 * and its index: out[i] for i in [0, n) is draw offset + i of stream `seed`, whatever the
 * vector width, the ISA or how a caller splits the work.
 *
 * Counter c gives two 32-bit words from Threefry-2x32 with 20 rounds (Salmon et al., "Parallel
 * random numbers: as easy as 1, 2, 3", SC 2011; only adds, rotates and xors, so it vectorises
 * alike from SSE4 to AVX-512), turned by Box-Muller into the draws at 2c and 2c + 1:
 *   u1 = (w0 >> 8 + 1) 2^-24 in (0, 1],  u2 = (w1 >> 8) 2^-24 in [0, 1),
 *   r = sqrt(-2 ln u1),  out[2c] = r cos(2 pi u2),  out[2c + 1] = r sin(2 pi u2).
 * Draws reach 5.77 sigma at most (u1 = 2^-24), far past what a simulation of block maxima of
 * transformed noise resolves. NumPy's generator took ~8 ns a draw, and the draws were most of
 * a Haswell job's setup simulation. */
#include <stddef.h>
#include <stdint.h>
#include <string.h>

#undef HWY_TARGET_INCLUDE
#define HWY_TARGET_INCLUDE "gauss.cc"
#include "hwy/foreach_target.h"  // must come before highway.h
#include "hwy/highway.h"
#include "hwy/contrib/math/math-inl.h"

HWY_BEFORE_NAMESPACE();
namespace ap_gauss {
namespace HWY_NAMESPACE {
namespace hn = hwy::HWY_NAMESPACE;

template <int R, class V>
HWY_INLINE V Rotl(V x) { return hn::Or(hn::ShiftLeft<R>(x), hn::ShiftRight<32 - R>(x)); }

/* Threefry-2x32-20 of counters (x0, x1) under key (k0, k1). */
template <class D, class V>
HWY_INLINE void Threefry(D du, V& x0, V& x1, uint32_t k0, uint32_t k1) {
  const uint32_t k2 = k0 ^ k1 ^ 0x1BD11BDAu;
  const uint32_t ks[3] = {k0, k1, k2};
  x0 = hn::Add(x0, hn::Set(du, k0));
  x1 = hn::Add(x1, hn::Set(du, k1));
#define AP_TF_ROUND(R) do { x0 = hn::Add(x0, x1); x1 = Rotl<R>(x1); x1 = hn::Xor(x1, x0); } while (0)
  for (uint32_t s = 1; s <= 5; s++) {
    if (s & 1) { AP_TF_ROUND(13); AP_TF_ROUND(15); AP_TF_ROUND(26); AP_TF_ROUND(6); }
    else       { AP_TF_ROUND(17); AP_TF_ROUND(29); AP_TF_ROUND(16); AP_TF_ROUND(24); }
    x0 = hn::Add(x0, hn::Set(du, ks[s % 3]));
    x1 = hn::Add(x1, hn::Set(du, ks[(s + 1) % 3] + s));
  }
#undef AP_TF_ROUND
}

/* Draws [first, first + 2 * pairs) of the stream into out, first even. */
static void FillPairs(float *HWY_RESTRICT out, uint64_t pairs, uint64_t first_pair, uint32_t k0,
                      uint32_t k1) {
  const hn::ScalableTag<uint32_t> du;
  const hn::Rebind<float, decltype(du)> df;
  const size_t L = hn::Lanes(du);
  const auto lane = hn::Iota(du, 0);
  const auto tiny = hn::Set(df, 1.0f / 16777216.0f);
  const auto one = hn::Set(du, 1u);
  const auto m2 = hn::Set(df, -2.0f);
  const auto twopi = hn::Set(df, 6.283185307179586f);
  uint64_t c = 0;
  HWY_ALIGN float bufc[64], bufs[64];
  for (; c < pairs; c += L) {
    const uint64_t ctr = first_pair + c;
    auto x0 = hn::Add(hn::Set(du, (uint32_t)ctr), lane);
    // the high word carries into it where the low word of a lane wrapped
    auto x1 = hn::Add(hn::Set(du, (uint32_t)(ctr >> 32)),
                      hn::IfThenElseZero(hn::Lt(x0, hn::Set(du, (uint32_t)ctr)), one));
    Threefry(du, x0, x1, k0, k1);
    auto u1 = hn::Mul(hn::ConvertTo(df, hn::Add(hn::ShiftRight<8>(x0), one)), tiny);
    auto u2 = hn::Mul(hn::ConvertTo(df, hn::ShiftRight<8>(x1)), tiny);
    auto r = hn::Sqrt(hn::Mul(m2, hn::Log(df, u1)));
    decltype(u2) s, co;
    hn::SinCos(df, hn::Mul(twopi, u2), s, co);
    s = hn::Mul(r, s); co = hn::Mul(r, co);
    const size_t take = (size_t)((pairs - c) < L ? (pairs - c) : L);
    if (take == L) {
      hn::StoreInterleaved2(co, s, df, out + 2 * c);
    } else {
      hn::Store(co, df, bufc); hn::Store(s, df, bufs);
      for (size_t i = 0; i < take; i++) { out[2 * (c + i)] = bufc[i]; out[2 * (c + i) + 1] = bufs[i]; }
    }
  }
}

void GaussFill(float *out, size_t n, uint64_t seed, uint64_t offset) {
  const uint32_t k0 = (uint32_t)seed, k1 = (uint32_t)(seed >> 32);
  size_t done = 0;
  if (offset & 1) {                 // a stream position mid-pair: its second draw first
    float two[2];
    FillPairs(two, 1, offset >> 1, k0, k1);
    out[0] = two[1]; done = 1; offset++;
  }
  const uint64_t pairs = (n - done) / 2;
  if (pairs) FillPairs(out + done, pairs, offset >> 1, k0, k1);
  done += 2 * pairs;
  if (done < n) {                   // an odd tail: the first draw of the next pair
    float two[2];
    FillPairs(two, 1, (offset + 2 * pairs) >> 1, k0, k1);
    out[done] = two[0];
  }
}

}  // namespace HWY_NAMESPACE
}  // namespace ap_gauss
HWY_AFTER_NAMESPACE();

#if HWY_ONCE
namespace ap_gauss {
HWY_EXPORT(GaussFill);
}
extern "C" void ap_gauss_fill(float *out, size_t n, uint64_t seed, uint64_t offset) {
  if (n) HWY_DYNAMIC_DISPATCH(ap_gauss::GaussFill)(out, n, seed, offset);
}
#endif
