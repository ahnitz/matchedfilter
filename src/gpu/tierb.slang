#include "twiddle.slang"
// Tier B: every transform length one workgroup can carry.
//
// L = TB*16 with TB threads holding 16 points each: a 16-point DFT per
// thread over its stride-TB column, a twiddle, a transpose among those TB
// threads, then TB-point transforms per block carried by TB/16 threads --
// recursing until TB <= 16, where a thread's 16 registers hold 16/TB whole
// blocks and it finishes them with no exchange at all.
//
// Verified in tools/gpu_decomposition.py before any of this was written,
// and checked register by register in tools/gpu_regmodel.py, which runs
// the real want[] scatter and the real slotToIndex against a float64
// reference. R is a parameter: 1024 threads is the cap, so 16 points per
// thread stops at 16384 and the last two lengths widen R instead.
//
//   n      R   threads  recursion     innermost
//   1024   16     64    64->4         4 blocks of 4 per thread
//   2048   16    128    128->8        2 blocks of 8
//   4096   16    256    256->16       1 block of 16
//   8192   16    512    512->32->2    8 blocks of 2
//  16384   16   1024    1024->64->4   4 blocks of 4
//  32768   32   1024    1024->32      1 block of 32
//  65536   64   1024    1024->16      4 blocks of 16
//
// 131072 would want R=128 -- 256 VGPRs of transform state per thread
// before any working set -- so it is Tier C: the four-step split across
// dispatches with global memory between.

#ifndef NLEN
#define NLEN 1024
#endif
//: Every unroll in this file. CUDA forces it: with a plain [unroll] Slang emitted the
//: multi-bin path's per-register loops as loops in CUDA source and NVVM kept myMag/myBin in
//: local memory (288 B per thread). SPIR-V and Metal keep [unroll] (their output unchanged).
#if defined(MF_CUDA)
#define MF_UNROLL [ForceUnroll]
#else
#define MF_UNROLL [unroll]
#endif
//: Points per thread.  16 wherever a workgroup can carry the transform at
//: 16; 32 and 64 are what take a length past 16384, where WG = NLEN/R would
//: otherwise need more than the 1024 threads a workgroup is allowed.
//:
//: R is the DECOMPOSITION RADIX as well as the register count -- every
//: level does an R-point DFT in registers, so widening it changes the
//: recursion, the twiddles and the digit-reversed output order together.
//: tools/gpu_regmodel.py checks all three against a float64 reference and
//: reproduces every shipped length, which is the only reason this is a
//: parameter and not a rewrite.
#ifndef RADIX
#define RADIX 16
#endif
static const uint N   = NLEN;
static const uint R   = RADIX;
static const uint LGR = (RADIX == 16) ? 4u : ((RADIX == 32) ? 5u : 6u);
static const uint WG  = NLEN / RADIX;       // threads per transform
static const float PI = 3.14159265358979f;

//: The exchange is staged in chunks so the threadgroup array is a fixed
//: 8 KB at every length, rather than sized to the transform -- which was
//: 128 KB at n=16384, over every device's limit, and already past Apple's
//: 32 KB at n=4096. CH registers of every thread are in flight at once.
//: Staging capacity in complex values. The exchange runs R/CH chunks with
//: CH = CAP/WG, and each chunk costs two barriers -- so a small CAP at a
//: large workgroup is barrier-bound, not bandwidth-bound. Measured at
//: threshold 5.5, 8192 pairs:
//:
//:     n=8192   8 KB 9.6x   16 KB 19.8x   32 KB 23.5x   64 KB 23.8x
//:     n=16384  8 KB 6.6x   16 KB  8.3x   32 KB 14.1x   64 KB 16.2x
//:
//: So it follows the workgroup rather than being fixed. The ceiling is a
//: PORTABILITY limit, not a performance one: 32 KB is what Apple allows a
//: threadgroup, and this device would take 64. MF_LDS_KB overrides it at
//: build time, which is how a per-device variant will be emitted.
#ifndef LDS_CAP
#define LDS_CAP 4096                           // complex, = 32 KB
#endif
static const uint CAP = (R * WG < LDS_CAP) ? (R * WG) : LDS_CAP;
//: Clamped to R. The exchange runs R/CH chunks, so CH > R makes that zero
//: and the exchange never happens -- the kernel then returns a transform of
//: the wrong axis, silently, with plausible magnitudes. That is what it did
//: at every length below 1024, where CAP/WG exceeds 16.
static const uint CH  = ((CAP / WG) > R) ? R : ((CAP / WG > 0) ? (CAP / WG) : 1);
//: Staged as uint so the per-bin peak table can alias this same memory once
//: the transform is finished. A second array would have doubled LDS to 16 KB,
//: and LDS is what caps how many workgroups a CU holds -- the 8 KB here was
//: chosen for occupancy. Measured free: +0.1% against float2 staging.
//: COARSE16: the coarse spectra are the dominant global traffic -- every
//: pair reads a band of data AND of template, so at 512x512 pairs the
//: coarse stage moves 2.15 GB at 978 GB/s: bandwidth bound at an
//: arithmetic intensity of 3.19 FLOP/byte, ~21% of this part's fp32 peak.
//: Halving the element halves that traffic.
//:
//: Packed as ONE uint holding two halves rather than a half2 buffer, so no
//: 16-bit storage extension is needed. The host packs once on upload and
//: every pair reuses the row, so the conversion amortises to nothing across
//: the N x M pair grid.
//:
//: This is a ROLE, not an entry point. fusedTierB is both the flat filter
//: (full precision data/tmpl) and the untiled coarse stage (cdata/ct0), so
//: the format cannot be keyed on the entry name -- doing that changed both
//: and made every coarse peak read as -1, a kernel reading 4-byte elements
//: as 8-byte ones. Hence a separate suffixed build.
#ifndef COARSE16
#define COARSE16 0
#endif
//: The SoA/fp16 half is written at 16 registers throughout. It only ever
//: builds at a coarse band, and every band is <= 1024 and so carries R=16 --
//: but that is an assumption a future band could break silently, so it is
//: stated here where the compiler can hold it.
#if COARSE16 && (RADIX != 16)
#error "COARSE16 is written for R=16; a wider band needs the SoA half widened too"
#endif
//: PPG: pairs per workgroup. One pair per workgroup makes a workgroup a
//: SINGLE wave32 at band 512, and the 16-workgroups-per-CU cap then pins
//: occupancy at 16 waves against a 32-wave capacity -- 50%, in every
//: configuration measured (at small bands the workgroup cap binds, at
//: large bands LDS does, and the product is the same 16 either way).
//:
//: That one number explains why halving traffic, halving LDS and halving
//: ALU work each bought nothing: at 16 waves/CU there is not enough
//: parallelism to hide a global load, and none of those touch parallelism.
//: Packing K pairs per workgroup raises waves/workgroup WITHOUT raising
//: LDS per wave, which is the only lever that moves it.
//:
//: Each pair gets its own staging region; every stg access is offset by
//: _stgBase. At band 512 one pair is exactly one wave, so WaveActiveMax
//: still reduces per pair.
#ifndef PPG
#define PPG 1
#endif
#ifndef SINGLE_BIN
#define SINGLE_BIN 0
#endif
//: The transform's own type. half2 halves register occupancy per point --
//: R=16 complex drops from 32 VGPRs to 16 -- which is what lets independent
//: transforms sit in registers together and cover each other's exchange
//: latency. That latency, not bandwidth, is the coarse stage's 5.7x.
#if COARSE16
typedef half2 C;
typedef half  CS;
#else
typedef float2 C;
typedef float CS;
#endif

#if COARSE16
typedef uint CVal;
C cload(StructuredBuffer<CVal> b, uint i)
{ uint p = b[i]; return C(CS(f16tof32(p & 0xFFFFu)), CS(f16tof32(p >> 16))); }
#else
typedef float2 CVal;
C cload(StructuredBuffer<CVal> b, uint i) { return b[i]; }
#endif
//: The data row stride (see mfDataStride in twiddle.slang).
#define DSTRIDE ((mfDataStride != 0u) ? mfDataStride : N)

#if defined(MF_VULKAN)
//: Per-row windows, (lo, hi) per data row, read when mfRowWindows != 0. A
//: separate binding after the entry's own (4 for the coarse role, 5 for the
//: listed refine), so no existing binding moves; Vulkan only.
#if COARSE16
[[vk::binding(4, 0)]] StructuredBuffer<uint> gRowWin;
#else
[[vk::binding(5, 0)]] StructuredBuffer<uint> gRowWin;
#endif
//: The window of data row d for this kernel: raw, or mapped onto the band
//: exactly as the host maps one window (cstart/cend in _vkcompute).
void rowWindow(uint d, inout uint winStart, inout uint winEnd)
{
    if (mfRowWindows == 0u) return;
    uint lo = gRowWin[2u * d], hi = gRowWin[2u * d + 1u];
    if (mfRowWindows == 1u) { winStart = lo; winEnd = hi; return; }
    uint rr = mfDataStride / N;
    uint cs = lo / rr, ce = min(N, (hi + rr - 1u) / rr);
    if (cs > 0u) cs -= 1u;
    ce = max(cs + 1u, ce);
    winStart = cs; winEnd = ce;
}
#else
void rowWindow(uint d, inout uint winStart, inout uint winEnd) {}
#endif
//: A data element for the coarse role. With a stride set, the data buffer is
//: the full fp32 spectra (two words per element) and is rounded to half here,
//: exactly as packCoarse rounded it (f32tof16, round to nearest even).
#if COARSE16
C dload(StructuredBuffer<CVal> b, uint i)
{
    if (mfDataStride != 0u)
        return C(CS(asfloat(b[2u * i])), CS(asfloat(b[2u * i + 1u])));
    return cload(b, i);
}
#endif
//: Half-width staging is what makes PPG pay. Each pair needs its own
//: region, so LDS scales with PPG -- at CH*WG*2 uints per pair, PPG=4 costs
//: 16 KB and a CU fits 4 workgroups x 4 waves: still 16 waves, exactly what
//: one pair per workgroup gave. Packing the stage to half halves the region,
//: so PPG=4 costs 8 KB, a CU fits 8 workgroups x 4 waves = 32 waves, and
//: occupancy finally doubles to the hardware's capacity.
//:
//: This is why halving LDS measured neutral on its own: it relieved a limit
//: that was not binding until PPG made waves available to use it. The two
//: changes are only worth anything together.
#if COARSE16
//: XS: the stage's row stride in the SoA exchange (exchangeS), one row per
//: register, one column per thread. XSLOT: the words between two pairs'
//: regions. At the defaults (WG, CH*WG) the band-256 exchange read 16
//: registers of one thread from one row -- stride WG = 16 words across the
//: 16 lanes of a pair -- which lands a wave64 read on 4 of the 32 banks a
//: half-wave sees: 8-way conflicts on every read, 9x the conflict-free LDS
//: cost by the bank model in tools/lds_layout.py, which picks both values per
//: (band, PPG) for the build. Padding only; the transform is unchanged.
#ifndef XSTRIDE
#define XSTRIDE (NLEN / RADIX)
#endif
static const uint XS = XSTRIDE;
static const uint XSF = NLEN / RADIX;     // the AoS exchange(), unused by the SoA path
#ifndef XSLOT
#define XSLOT (CH * XS)
#endif
static const uint STGW = (XSLOT > CH * XS) ? XSLOT : CH * XS;
groupshared uint stg[STGW * PPG];
static uint _stgBase;
//: Pure bitcast, no conversion. C is already half2 and the slot is 32
//: bits, so packing is a reinterpret. The previous form went
//: half -> float -> half-bits via f32tof16/f16tof32 on every stage access,
//: and the exchange touches every register twice per level: that round
//: trip was 196 v_cvt_f32_f16 in the disassembly, converting data that
//: was already in the right format.
void stgPut(uint i, C v) { stg[_stgBase+i] = bit_cast<uint>(v); }
C stgGet(uint i) { return bit_cast<C>(stg[_stgBase+i]); }
#else
//: Row stride of the fp32 exchange stage, in complex elements (see XSTRIDE).
#ifndef XSTRIDE_F
#define XSTRIDE_F (NLEN / RADIX)
#endif
static const uint XSF = XSTRIDE_F;
static const uint STGW = CH * XSF * 2;
groupshared uint stg[STGW * PPG];
static uint _stgBase;
void stgPut(uint i, float2 v) { stg[_stgBase+2*i] = asuint(v.x); stg[_stgBase+2*i+1] = asuint(v.y); }
float2 stgGet(uint i) { return float2(asfloat(stg[_stgBase+2*i]), asfloat(stg[_stgBase+2*i+1])); }
#endif
static uint _tid;

//: Levels until a block fits in one thread's registers. Known from NLEN,
//: so the level loop unrolls and every len/TB/shift below folds to a
//: constant -- which is the whole difference between this and the
//: hand-specialised kernel.
static const uint NLEVELS = (WG <= R) ? 1 : ((WG <= R * R) ? 2 : 3);

C cmul(C a, C b) { return C(a.x*b.x - a.y*b.y, a.x*b.y + a.y*b.x); }
C cmulConj(C a, C b) { return C(a.x*b.x + a.y*b.y, a.y*b.x - a.x*b.y); }
inline uint computeWant(uint d, uint TB, uint len, uint blk, uint lane, uint per, uint TB2, uint len2, uint blk2, uint lane2)
{
    uint j = d / max(TB, 1u), m = d % max(TB, 1u);
    return (TB <= RADIX) ? (blk * len + (lane * per + j) * TB + m)
                         : (blk2 * len2 + lane2 + TB2 * d);
}

#if COARSE16
typedef half2 H;
//: A pair index that writes nothing: the clamped tail of a ragged tile.
static const uint NOPAIR = 0xFFFFFFFFu;

//: The coarse tier's ERROR BOUND (docs/vulkan-8060s-roofline.md section 10). The
//: value a pair reports is an upper bound on its exact coarse maximum, not the fp16
//: maximum itself:
//:
//:     B = |c16| (1 + 3u) + C16_KAPPA u rms(y),   u = 2^-11,  rms(y)^2 = sum_j |x_j|^2
//:
//: (1 + 3u) is proven: the lag is chosen on fp16 |v|^2 (two roundings, within
//: (1 +- u)^2 of the fp16 transform's power), so the fp16 maximum is at most
//: |c16| (1+u)/(1-u). C16_KAPPA u rms covers the transform's own rounding error at
//: that lag: z sigma_B with sigma_B the band's measured error rms (in u rms units)
//: and z the one-sided normal quantile of the per-pair failure target, both set at
//: build time (tools/coarse_layout.py). rms is over all lags (Parseval: the inputs'
//: energy), so a loud out-of-window glitch raises the bound with it.
#ifndef C16_KAPPA
#define C16_KAPPA 0.0
#endif
static const float C16_U = 4.8828125e-4f;          // 2^-11
float2 c16Bound(float2 v, float energy)
{
    if (mfC16Bound == 0u) return v;
    float m = length(v);
    float b = m * (1.0f + 3.0f * C16_U) + float(C16_KAPPA) * C16_U * sqrt(energy);
    return (m > 0.0f) ? v * (b / m) : float2(b, 0.0f);
}

//: Sum of one float per thread over a pair's WG threads through the stage, the
//: result on every thread. Uniform control flow; leaves the stage free again.
float pairSum(uint tid, float v)
{
    GroupMemoryBarrierWithGroupSync();
    stg[_stgBase + tid] = asuint(v);
    GroupMemoryBarrierWithGroupSync();
    float t = 0.0f;
    for (uint k = 0; k < WG; ++k) t += asfloat(stg[_stgBase + k]);
    GroupMemoryBarrierWithGroupSync();
    return t;
}

//: Complex multiply by a twiddle that is the SAME for both transforms, so
//: wr/wi broadcast to both lanes. Four v_pk_* and nothing else.
void cmulw(inout H xr, inout H xi, CS wr, CS wi)
{
    H nr = xr * wr - xi * wi;
    H ni = xr * wi + xi * wr;
    xr = nr; xi = ni;
}

//: Correlate against a conjugated template: (ar,ai) * conj(br,bi).
//: Both lanes are distinct transforms, so this is fully packed too.
void cmulconjs(H ar, H ai, H br, H bi, out H pr, out H pi)
{
    pr = ar * br + ai * bi;
    pi = ai * br - ar * bi;
}

//: Radix-4 butterfly.
//:
//: The ×i rotation is the quiet win. AoS needed C(-t3.y, t3.x) -- a
//: cross-component swizzle, one of the v_mov_b16 the ISA dump is full of.
//: In SoA it is a register RENAME plus a negate, and radix-4 is built from
//: these: every ±i in the kernel becomes free.
void r4s(inout H re[16], inout H im[16], uint a, uint b, uint c, uint d)
{
    H t0r = re[a] + re[c], t0i = im[a] + im[c];
    H t1r = re[a] - re[c], t1i = im[a] - im[c];
    H t2r = re[b] + re[d], t2i = im[b] + im[d];
    H t3r = re[b] - re[d], t3i = im[b] - im[d];
    H j3r = -t3i, j3i = t3r;                 // i * t3, free
    re[a] = t0r + t2r; im[a] = t0i + t2i;
    re[b] = t1r + j3r; im[b] = t1i + j3i;
    re[c] = t0r - t2r; im[c] = t0i - t2i;
    re[d] = t1r - j3r; im[d] = t1i - j3i;
}

void swap2(inout H re[16], inout H im[16], uint p, uint q)
{
    H t;
    t = re[p]; re[p] = re[q]; re[q] = t;
    t = im[p]; im[p] = im[q]; im[q] = t;
}

void dft2s(inout H re[16], inout H im[16], uint o)
{
    H ar = re[o], ai = im[o], br = re[o+1], bi = im[o+1];
    re[o]   = ar + br; im[o]   = ai + bi;
    re[o+1] = ar - br; im[o+1] = ai - bi;
}

void dft4s(inout H re[16], inout H im[16], uint o)
{
    r4s(re, im, o, o+1, o+2, o+3);
    swap2(re, im, o+1, o+2);
}

void dft8s(inout H re[16], inout H im[16], uint o)
{
    H br[8], bi[8];
    MF_UNROLL for (uint s = 1; s < 8; s <<= 1) {
        MF_UNROLL for (uint j = 0; j < 4; ++j) {
            uint k = j & (s-1), base = (j-k) << 1;
            float ang = PI * float(k) / float(s);
            H vr = re[o+j+4], vi = im[o+j+4];
            float2 tw = mfTwiddle(ang);
            cmulw(vr, vi, CS(tw.x), CS(tw.y));
            H ur = re[o+j], ui = im[o+j];
            br[base+k]   = ur + vr; bi[base+k]   = ui + vi;
            br[base+k+s] = ur - vr; bi[base+k+s] = ui - vi;
        }
        MF_UNROLL for (uint i = 0; i < 8; ++i) { re[o+i] = br[i]; im[o+i] = bi[i]; }
    }
}

void dft16s(inout H re[16], inout H im[16])
{
    MF_UNROLL for (uint n1 = 0; n1 < 4; ++n1) r4s(re, im, n1, n1+4, n1+8, n1+12);
    // Same twiddles as the AoS form, now broadcast scalars rather than
    // packed constants -- the multiply is elementwise in SoA.
    cmulw(re[5],  im[5],  CS( 0.92387953f), CS( 0.38268343f));  // W1
    cmulw(re[9],  im[9],  CS( 0.70710678f), CS( 0.70710678f));  // W2
    cmulw(re[13], im[13], CS( 0.38268343f), CS( 0.92387953f));  // W3
    cmulw(re[6],  im[6],  CS( 0.70710678f), CS( 0.70710678f));  // W2
    cmulw(re[10], im[10], CS( 0.0f),        CS( 1.0f));         // W4 = i
    cmulw(re[14], im[14], CS(-0.70710678f), CS( 0.70710678f));  // W6
    cmulw(re[7],  im[7],  CS( 0.38268343f), CS( 0.92387953f));  // W3
    cmulw(re[11], im[11], CS(-0.70710678f), CS( 0.70710678f));  // W6
    cmulw(re[15], im[15], CS(-0.92387953f), CS(-0.38268343f));  // W9
    MF_UNROLL for (uint k2 = 0; k2 < 4; ++k2)
        r4s(re, im, 4*k2, 4*k2+1, 4*k2+2, 4*k2+3);
    swap2(re, im, 1, 4);   swap2(re, im, 2, 8);   swap2(re, im, 3, 12);
    swap2(re, im, 6, 9);   swap2(re, im, 7, 13);  swap2(re, im, 11, 14);
}

//: |v|^2 for BOTH transforms in one packed multiply-add. The shipped
//: kernel promotes to fp32 here (float(r[i].x) etc), which is 598 of the
//: fp32 ops in the ISA dump; this keeps it in half and hands back one
//: magnitude per lane.
H mag2s(H re, H im) { return re * re + im * im; }


//: Dual exchange. Two passes over the same stage -- re then im -- so the
//: LDS sizing is untouched. Each stgPut stores one half2, which is the
//: same element of BOTH transforms, so one pass moves both.
//:
//: The source of register d is (row i, column col) of the stage, and both
//: are AFFINE-SEPARABLE in (tid, d): i(tid,d) = i(tid,0) + i(0,d), and the
//: same for col. So each thread works its base out once and every register
//: reads at a compile-time offset from it -- an LDS immediate, no address
//: arithmetic. Recomputing computeWant per register cost ~4 VALU each, 128
//: per exchange at band 256. tools/lds_layout.py checks the separation for
//: every band and level the build emits.
void exchangeS(inout H re[16], inout H im[16],
               uint lgLen, uint lgSpan,
               uint TB, uint len, uint blk, uint lane, uint per, uint TB2, uint len2, uint blk2, uint lane2)
{
    H outr[16], outi[16];
    MF_UNROLL for (uint z = 0; z < R; ++z) { outr[z] = H(0.0f); outi[z] = H(0.0f); }
    uint spanMask = (1u << lgSpan) - 1u;
    uint lenMask  = (1u << lgLen) - 1u;
    uint p0 = computeWant(0, TB, len, blk, lane, per, TB2, len2, blk2, lane2);
    uint i0 = (p0 & lenMask) >> lgSpan;
    uint a0 = i0 * XS + ((p0 >> lgLen) << lgSpan) + (p0 & lenMask & spanMask);
    MF_UNROLL for (uint c = 0; c < R / CH; ++c) {
        [ForceUnroll] for (uint comp = 0; comp < 2; ++comp) {
            GroupMemoryBarrierWithGroupSync();
            MF_UNROLL for (uint j = 0; j < CH; ++j)
                stgPut(j * XS + _tid, comp == 0 ? re[c * CH + j] : im[c * CH + j]);
            GroupMemoryBarrierWithGroupSync();
            MF_UNROLL for (uint d = 0; d < R; ++d) {
                // tid = 0 terms: blk = lane = blk2 = lane2 = 0, all constants
                uint pz = computeWant(d, TB, len, 0u, 0u, per, TB2, len2, 0u, 0u);
                uint iz = (pz & lenMask) >> lgSpan;
                uint az = iz * XS + ((pz >> lgLen) << lgSpan) + (pz & lenMask & spanMask);
                uint i = i0 + iz;
                if (CH == R || (i >= c * CH && i < (c + 1) * CH)) {
                    H v = stgGet(a0 + az - c * CH * XS);
                    if (comp == 0) outr[d] = v; else outi[d] = v;
                }
            }
        }
    }
    MF_UNROLL for (uint d = 0; d < R; ++d) { re[d] = outr[d]; im[d] = outi[d]; }
}

void innermostS(inout H re[16], inout H im[16])
{
    if (INNER == 16)     { dft16s(re, im); }
    else if (INNER == 8) { MF_UNROLL for (uint b = 0; b < 2; ++b) dft8s(re, im, b*8); }
    else if (INNER == 4) { MF_UNROLL for (uint b = 0; b < 4; ++b) dft4s(re, im, b*4); }
    else                 { MF_UNROLL for (uint b = 0; b < 8; ++b) dft2s(re, im, b*2); }
}
#endif

void r4(inout C a, inout C b, inout C c, inout C d)
{
    C t0=a+c, t1=a-c, t2=b+d, t3=b-d;
    C j3 = C(-t3.y, t3.x);
    a=t0+t2; b=t1+j3; c=t0-t2; d=t1-j3;
}

// In-register DFTs at COMPILE-TIME sizes and offsets. A runtime offset
// or length here indexes the register array dynamically, which forces a
// spill to scratch -- the first version did that and the driver crashed.
// The innermost block size follows from NLEN, so it folds.
void dft2(inout C r[RADIX], uint o)
{
    C a=r[o], b=r[o+1]; r[o]=a+b; r[o+1]=a-b;
}
void dft4(inout C r[RADIX], uint o)
{
    r4(r[o], r[o+1], r[o+2], r[o+3]);
    C t=r[o+1]; r[o+1]=r[o+2]; r[o+2]=t;
}
void dft8(inout C r[RADIX], uint o)
{
    // radix-2, three stages, fully unrolled with static indices
    const float S = 0.70710678f;
    C b[8];
    MF_UNROLL for (uint s = 1; s < 8; s <<= 1) {
        MF_UNROLL for (uint j = 0; j < 4; ++j) {
            uint k = j & (s-1), base = (j-k) << 1;
            float ang = PI * float(k) / float(s);
            C w = C(mfTwiddle(ang));
            C u = r[o+j], v = r[o+j+4], t = cmul(w, v);
            b[base+k] = u+t; b[base+k+s] = u-t;
        }
        MF_UNROLL for (uint i = 0; i < 8; ++i) r[o+i] = b[i];
    }
}
void dft16(inout C r[16])
{
    const C W1 = C( 0.92387953f,  0.38268343f);
    const C W2 = C( 0.70710678f,  0.70710678f);
    const C W3 = C( 0.38268343f,  0.92387953f);
    const C W4 = C( 0.0f,         1.0f       );
    const C W6 = C(-0.70710678f,  0.70710678f);
    const C W9 = C(-0.92387953f, -0.38268343f);
    MF_UNROLL for (uint n1 = 0; n1 < 4; ++n1) r4(r[n1], r[n1+4], r[n1+8], r[n1+12]);
    r[5]=cmul(r[5],W1);  r[9]=cmul(r[9],W2);   r[13]=cmul(r[13],W3);
    r[6]=cmul(r[6],W2);  r[10]=cmul(r[10],W4); r[14]=cmul(r[14],W6);
    r[7]=cmul(r[7],W3);  r[11]=cmul(r[11],W6); r[15]=cmul(r[15],W9);
    MF_UNROLL for (uint k2 = 0; k2 < 4; ++k2) r4(r[4*k2], r[4*k2+1], r[4*k2+2], r[4*k2+3]);
    C t;
    t=r[1];  r[1]=r[4];   r[4]=t;
    t=r[2];  r[2]=r[8];   r[8]=t;
    t=r[3];  r[3]=r[12];  r[12]=t;
    t=r[6];  r[6]=r[9];   r[9]=t;
    t=r[7];  r[7]=r[13];  r[13]=t;
    t=r[11]; r[11]=r[14]; r[14]=t;
}

//: dft16 at a static offset inside a wider register file. At R=16 this is
//: dft16 itself; above it the slice is copied out and back, which unrolls
//: to register renames because every offset is a compile-time constant.
void dft16at(inout C r[RADIX], uint o)
{
#if RADIX == 16
    dft16(r);
#else
    C b[16];
    MF_UNROLL for (uint i = 0; i < 16; ++i) b[i] = r[o + i];
    dft16(b);
    MF_UNROLL for (uint i = 0; i < 16; ++i) r[o + i] = b[i];
#endif
}

#if RADIX == 32
//: R=32 as two dft16 under a decimation-in-frequency split:
//:
//:     u[j] = x[j] + x[j+16]              -> X[2k]
//:     v[j] = (x[j] - x[j+16]) * W32^j    -> X[2k+1]
//:
//: The interleave at the end is NOT optional. want[] below indexes
//: registers by frequency k2, so a radix that left its output permuted
//: would mis-route the entire level -- silently, at plausible magnitudes.
void dft32(inout C r[RADIX])
{
    C u[16], v[16];
    MF_UNROLL for (uint j = 0; j < 16; ++j) {
        C a = r[j], b = r[j + 16];
        u[j] = a + b;
        float ang = 2.0f * PI * float(j) / 32.0f;
        v[j] = cmul(a - b, C(mfTwiddle(ang)));
    }
    dft16(u);
    dft16(v);
    MF_UNROLL for (uint k = 0; k < 16; ++k) { r[2 * k] = u[k]; r[2 * k + 1] = v[k]; }
}
#endif

#if RADIX == 64
//: R=64 as four dft16 under a radix-4 decimation in frequency. r4 already
//: computes the four sums sum_q x[j+16q] * i^(pq) in place and in natural p
//: order -- the same butterfly dft16 is built from -- so the split costs one
//: r4 per j and no twiddle of its own.
void dft64(inout C r[RADIX])
{
    MF_UNROLL for (uint j = 0; j < 16; ++j)
        r4(r[j], r[j + 16], r[j + 32], r[j + 48]);
    C o[64];
    MF_UNROLL for (uint pp = 0; pp < 4; ++pp) {
        C b[16];
        MF_UNROLL for (uint j = 0; j < 16; ++j) {
            float ang = 2.0f * PI * float(pp * j) / 64.0f;
            b[j] = cmul(r[pp * 16 + j], C(mfTwiddle(ang)));
        }
        dft16(b);
        MF_UNROLL for (uint k = 0; k < 16; ++k) o[4 * k + pp] = b[k];
    }
    MF_UNROLL for (uint i = 0; i < 64; ++i) r[i] = o[i];
}
#endif

//: The per-level radix.
void dftR(inout C r[RADIX])
{
#if RADIX == 16
    dft16(r);
#elif RADIX == 32
    dft32(r);
#else
    dft64(r);
#endif
}

//: Innermost block size: recurse TB /= R until it fits in a thread.
static const uint INNER = (WG <= R) ? WG
                        : ((WG / R <= R) ? WG / R : WG / (R * R));

//: Only the combinations that are actually built appear here. R>16 occurs
//: at one geometry each -- WG=1024 gives INNER=32 at R=32 and INNER=16 at
//: R=64 -- so the other branches would be dead code carrying live risk.
void innermost(inout C r[RADIX])
{
#if RADIX == 32
    dft32(r);                                    // INNER == 32
#elif RADIX == 64
    MF_UNROLL for (uint b = 0; b < 4; ++b) dft16at(r, b*16);   // INNER == 16
#else
    if (INNER == 16)     { dft16(r); }
    else if (INNER == 8) { MF_UNROLL for (uint b = 0; b < 2; ++b) dft8(r, b*8); }
    else if (INNER == 4) { MF_UNROLL for (uint b = 0; b < 4; ++b) dft4(r, b*4); }
    else                 { MF_UNROLL for (uint b = 0; b < 8; ++b) dft2(r, b*2); }
#endif
}

// Exchange in chunks. Staging CH registers of every thread at a time,
// a reader works out for each value it wants which register of which
// thread wrote it -- the scatter formula inverts -- and takes it when
// that register falls in the current chunk.
//
//   scatter wrote   p = blk*len + i*span + lane
//   so from p:      blk = p/len, i = (p%len)/span, lane = (p%len)%span
//                   writer thread = blk*span + lane
//: SPLIT_STAGE: the same staging bytes as two float2 chunks hold every register of every
//: thread as ONE float each, so the exchange runs once per component instead of once per
//: chunk. Same four barriers; but every staged read lands (a chunk's reader loop walks all
//: R registers and keeps only CH of them) and the source index of each register is worked
//: out once rather than per chunk. Only where two chunks would be needed and the staging
//: holds R*WG floats: the Metal build at n=8192, whose 64 KB variant Apple cannot create.
#ifndef SPLIT_STAGE
#define SPLIT_STAGE 0
#endif
#if SPLIT_STAGE && !COARSE16
#if (2 * LDS_CAP) < (NLEN)
#error "SPLIT_STAGE needs staging for R*WG floats"
#endif
void exchange(inout C r[RADIX], uint lgLen, uint lgSpan,
              uint TB, uint len, uint blk, uint lane, uint per, uint TB2, uint len2, uint blk2, uint lane2)
{
    uint spanMask = (1u << lgSpan) - 1u;
    uint lenMask  = (1u << lgLen) - 1u;
    uint src[RADIX];
    MF_UNROLL for (uint d = 0; d < R; ++d) {
        uint p = computeWant(d, TB, len, blk, lane, per, TB2, len2, blk2, lane2);
        uint b = p >> lgLen, rem = p & lenMask;
        src[d] = (rem >> lgSpan) * WG + (b << lgSpan) + (rem & spanMask);
    }
    float xr[RADIX];
    GroupMemoryBarrierWithGroupSync();
    MF_UNROLL for (uint j = 0; j < R; ++j) stg[_stgBase + j * WG + _tid] = asuint(r[j].x);
    GroupMemoryBarrierWithGroupSync();
    MF_UNROLL for (uint d = 0; d < R; ++d) xr[d] = asfloat(stg[_stgBase + src[d]]);
    GroupMemoryBarrierWithGroupSync();
    MF_UNROLL for (uint j = 0; j < R; ++j) stg[_stgBase + j * WG + _tid] = asuint(r[j].y);
    GroupMemoryBarrierWithGroupSync();
    MF_UNROLL for (uint d = 0; d < R; ++d) r[d] = C(xr[d], asfloat(stg[_stgBase + src[d]]));
}
#else
void exchange(inout C r[RADIX], uint lgLen, uint lgSpan,
              uint TB, uint len, uint blk, uint lane, uint per, uint TB2, uint len2, uint blk2, uint lane2)
{
    // Every divisor here is a power of two, so these are shifts and masks.
    // Written as / and % they were integer divisions -- 16 of them per
    // thread per chunk -- and cost n=4096 a third of its throughput
    // against the hand-specialised kernel.
    // Explicitly initialised. Every register index falls in exactly one
    // chunk, so these are always written -- but the compiler cannot prove
    // it and warns, and a backend that leaves an unwritten register as
    // garbage rather than zero would turn that warning into a wrong
    // answer. Cheap insurance against a compiler we have not met.
    C out[RADIX];
    MF_UNROLL for (uint z = 0; z < R; ++z) out[z] = C(0.0f, 0.0f);
    uint spanMask = (1u << lgSpan) - 1u;
    uint lenMask  = (1u << lgLen) - 1u;
    // Affine-separable source (see exchangeS): one base per thread, every
    // register at a compile-time offset; rows XSF apart (bank padding).
    uint p0 = computeWant(0, TB, len, blk, lane, per, TB2, len2, blk2, lane2);
    uint a0 = ((p0 & lenMask) >> lgSpan) * XSF + ((p0 >> lgLen) << lgSpan) + (p0 & lenMask & spanMask);
    uint i0 = (p0 & lenMask) >> lgSpan;
    MF_UNROLL for (uint c = 0; c < R / CH; ++c) {
        GroupMemoryBarrierWithGroupSync();
        MF_UNROLL for (uint j = 0; j < CH; ++j) stgPut(j * XSF + _tid, r[c * CH + j]);
        GroupMemoryBarrierWithGroupSync();
        MF_UNROLL for (uint d = 0; d < R; ++d) {
            uint pz = computeWant(d, TB, len, 0u, 0u, per, TB2, len2, 0u, 0u);
            uint iz = (pz & lenMask) >> lgSpan;
            uint az = iz * XSF + ((pz >> lgLen) << lgSpan) + (pz & lenMask & spanMask);
            uint i = i0 + iz;
            if (CH == R || (i >= c * CH && i < (c + 1) * CH))
                out[d] = stgGet(a0 + az - c * CH * XSF);
        }
    }
    MF_UNROLL for (uint d = 0; d < R; ++d) r[d] = out[d];
}
#endif

//: The four-step skips its final transposes, so the transform leaves results
//: in mixed-radix digit-reversed order: register q of thread tid holds output
//: index reverse(tid*16 + q) under radices [16]*NLEVELS + INNER. Established
//: by dumping every register against a float64 reference for all five
//: lengths -- see tools/gpu_output_order.py. INNER=4 contributes [2,2] and not
//: [4]: dft4 leaves its pair bit-reversed, which was measured, not reasoned.
//:
//: A peak MAGNITUDE is order-independent, which is why nothing needed this
//: until the kernel had to report an index and place samples into bins -- and
//: why getting it wrong would be silent rather than loud.
//:
//: Every radix is a power of two, so this is a bit shuffle. The digits come
//: out least-significant first and are consumed in that same order, so
//: extraction and rebuild fuse into one loop with NO array: dynamic indexing
//: of a register array spills to scratch and crashed a driver here once.
static const uint NIDIG = (INNER == 4) ? 2u : 1u;
static const uint NDIG  = NLEVELS + NIDIG;
static const uint LGI0  = (INNER == 2) ? 1u : ((INNER == 4) ? 1u
                        : ((INNER == 8) ? 3u : ((INNER == 16) ? 4u
                        : ((INNER == 32) ? 5u : 6u))));

uint lgOf(uint i) { return (i < NLEVELS) ? LGR : ((i == NLEVELS) ? LGI0 : 1u); }

uint slotToIndex(uint slot)
{
    uint idx = 0u, x = slot;
    [ForceUnroll] for (int i = int(NDIG) - 1; i >= 0; --i) {
        uint lg = lgOf(uint(i));
        uint d  = x & ((1u << lg) - 1u);
        x >>= lg;
        idx = (idx << lg) | d;
    }
    return idx;
}

//: The filter itself, as a plain function so more than one entry point can
//: use it. Slang does not allow one entry point to call another, and the
//: compacted refinement uses this same body.
#ifndef TILE_T
#define TILE_T 1
#endif

//: The transform itself, with no filtering and no peak search around it.
//:
//: Split out of filterOne because Tier C calls it too: a length past 65536
//: is two of these, with a twiddle and a transpose between. Everything in
//: here is a function of `tid` and the compile-time geometry, so lifting it
//: is a pure move of the source. It is NOT byte-identical in the SPIR-V --
//: n=16384 goes 29932 -> 29972 -- so it rests on the cross-device index and
//: value checks, not on the artefact being unchanged. What it buys is that
//: the Tier C stages cannot drift from the transform eleven lengths are
//: already verified against.
void transform(inout C r[RADIX], uint tid)
{
#include "fft_transform.slang"
}

// Keep the full-precision path in one function. Passing a dummy data
// register array through the coarse tiling wrapper doubled flat/refine
// execution time on the Radeon 8060S, even when its loads were disabled.
#if COARSE16
void filterOne(uint pair, uint d, uint t, uint tid, C dreg[RADIX],
               StructuredBuffer<CVal> data, StructuredBuffer<CVal> tmpl,
               RWStructuredBuffer<int> peakIdx, RWStructuredBuffer<float2> peakVal,
               uint winStart, uint winEnd,
               uint binsize, int binShift, uint nbins, uint thrBits)
#else
void filterPair(uint pair, uint tid,
                StructuredBuffer<CVal> data, StructuredBuffer<CVal> tmpl,
                RWStructuredBuffer<int> peakIdx, RWStructuredBuffer<float2> peakVal,
                uint ntmpl, uint winStart, uint winEnd,
                uint binsize, int binShift, uint nbins, uint thrBits)
#endif
{
#if !COARSE16
#if SINGLE_BIN
    // The host selects this build only when the searched window has one
    // output bin. Constant propagation removes the general bin tables and
    // their live ranges without changing the FFT or tied-winner election.
    nbins = 1u;
#endif
    _tid = tid;
    uint d = pair / ntmpl, t = pair % ntmpl;
#endif
    C r[RADIX];

    // level 0: gather this thread's stride-WG column straight from global
#if COARSE16
    MF_UNROLL for (uint n2 = 0; n2 < R; ++n2)
        r[n2] = cmulConj(dreg[n2], cload(tmpl, t*N + tid + WG * n2));
#else
    // No tile on this path, so nothing amortises a hoisted data slice --
    // it is 16 live registers of pure cost. The FLAT filter and the refine
    // stage both come through here, and holding dreg for them cost the
    // flat filter 1.29 -> 2.93 ms at n=4096 before this guard.
    MF_UNROLL for (uint n2 = 0; n2 < R; ++n2) {
        uint idx = tid + WG * n2;
        r[n2] = cmulConj(cload(data, d*DSTRIDE + idx), cload(tmpl, t*N + idx));
    }
#endif

    transform(r, tid);

    // --- peak per bin ---------------------------------------------------
    // Bins are contiguous in OUTPUT index, and the output index is not
    // contiguous in register or thread space, so every register has to be
    // placed by its true index. A host-side lookup cannot do this.

    // Seeded with the SQUARED THRESHOLD, exactly as the CPU does (bmax[j] =
    // t2). Anything at or below it can never win, so it takes no atomic and
    // no comparison -- and at a real detection threshold almost nothing
    // clears it, often nothing at all in a given bin. Seeding at zero rather
    // than -1 also means a bin whose every |v|^2 underflowed reports index
    // -1 instead of naming the first sample, matching the CPU.
#if COARSE16
    // The pair's energy over all lags, for the coarse error bound (c16Bound),
    // before the peak tables take the stage over.
    float energy = 0.0f;
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        float _ex = float(r[i].x), _ey = float(r[i].y);
        energy += _ex * _ex + _ey * _ey;
    }
    energy = pairSum(tid, energy) / float(N);
#endif
    GroupMemoryBarrierWithGroupSync();          // transform is done with stg
#if SINGLE_BIN
    // ONE BIN by construction:
    // Eliminate myMag[RADIX] and myBin[RADIX] arrays entirely and free r[RADIX]
    // immediately after the unrolled reduction loop to eliminate register spilling.
    if (tid == 0) { stg[_stgBase] = thrBits; stg[_stgBase+1] = 0xffffffffu; }

    uint threadBestBits = thrBits;
    uint threadBestSlot = 0xffffffffu;
    float2 threadBestVal = float2(0.0f, 0.0f);

    if (winStart == 0u && winEnd >= N) {
        MF_UNROLL for (uint i = 0; i < R; ++i) {
            float _rx = float(r[i].x), _ry = float(r[i].y);
            uint magBits = asuint(_rx*_rx + _ry*_ry);
            if (magBits > threadBestBits) {
                threadBestBits = magBits;
                threadBestSlot = tid * R + i;
                threadBestVal = float2(_rx, _ry);
            }
        }
    } else {
        MF_UNROLL for (uint i = 0; i < R; ++i) {
            uint idx = slotToIndex(tid * R + i);
            bool live = (idx >= winStart && idx < winEnd);
            float _rx = float(r[i].x), _ry = float(r[i].y);
            uint magBits = live ? asuint(_rx*_rx + _ry*_ry) : 0u;
            if (magBits > threadBestBits) {
                threadBestBits = magBits;
                threadBestSlot = tid * R + i;
                threadBestVal = float2(_rx, _ry);
            }
        }
    }

    GroupMemoryBarrierWithGroupSync();          // ensure tid 0 stg initialized before atomics

#if PPG == 1 && !TARGET_CUDA
    uint wm = WaveActiveMax(threadBestBits);
    if (WaveIsFirstLane() && wm > thrBits) InterlockedMax(stg[_stgBase], wm);
#else
    if (threadBestBits > thrBits) InterlockedMax(stg[_stgBase], threadBestBits);
#endif
    GroupMemoryBarrierWithGroupSync();

    uint winner = 0xffffffffu;
    if (threadBestBits > thrBits && threadBestBits == stg[_stgBase])
        winner = threadBestSlot;

#if PPG == 1 && !TARGET_CUDA
    uint waveWinner = WaveActiveMin(winner);
    if (WaveIsFirstLane() && waveWinner != 0xffffffffu)
        InterlockedMin(stg[_stgBase+1], waveWinner);
#else
    if (winner != 0xffffffffu) InterlockedMin(stg[_stgBase+1], winner);
#endif
    GroupMemoryBarrierWithGroupSync();

    if (threadBestSlot == stg[_stgBase+1] && threadBestSlot != 0xffffffffu) {
        peakIdx[pair] = int(slotToIndex(threadBestSlot));
        peakVal[pair] = threadBestVal;
    }
    if (tid == 0 && stg[_stgBase+1] == 0xffffffffu) {
        peakIdx[pair] = -1;
        peakVal[pair] = float2(0, 0);
    }
#else
#if COARSE16
    // ONE BIN by construction on the coarse gate: cidx/cval are sized
    // `pairs`, so the coarse stage reports one value per pair and never a
    // per-bin table. Binning is the FINE stage's job and is unaffected.
    // The window is KEPT -- winStart/winEnd still bound the search.
    if (tid == 0) { stg[_stgBase] = thrBits; stg[_stgBase+1] = 0xffffffffu; }
#else
    for (uint b = tid; b < nbins; b += WG) stg[_stgBase+b] = thrBits;
    if (nbins == 1 && tid == 0) stg[_stgBase+1] = 0xffffffffu;
#endif
    GroupMemoryBarrierWithGroupSync();

    uint myMag[RADIX];
    uint myBin[RADIX];
#if defined(MF_METAL) && COARSE16
    uint ovAcc = 0u;
#endif
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        uint idx = slotToIndex(tid * R + i);
        bool live = (idx >= winStart && idx < winEnd);
        // Out-of-window samples are set to zero rather than branched around:
        // zero can never beat a seed of >= 0, so the window costs a select
        // and no divergence.
        float _rx = float(r[i].x), _ry = float(r[i].y);
        myMag[i] = live ? asuint(_rx*_rx + _ry*_ry) : 0u;
#if defined(MF_METAL) && COARSE16
        // FAIL OPEN on fp16 overflow. Metal compiles with fast math, under which an inf
        // or NaN magnitude compares unpredictably. An fp16 exponent field of all ones
        // (inf or NaN) carries into its sign bit when 0x0400 is added to the masked
        // field: two integer ops per register, exact under any math mode.
        ovAcc |= (bit_cast<uint>(r[i]) & 0x7C007C00u) + 0x04000400u;
#endif
        uint off = idx - winStart;
        // Shift when the binsize is a power of two, divide when it is not --
        // the same split the CPU makes, and the reason no restriction on
        // binsize is needed. A real division here is ~20 cycles.
#if COARSE16
        myBin[i] = 0u;            // one bin; `off` is unused here
#else
        myBin[i] = live ? (binShift >= 0 ? (off >> uint(binShift)) : (off / binsize))
                        : 0u;
#endif
#if !COARSE16
        if (nbins > 1 && myMag[i] > thrBits)
            InterlockedMax(stg[_stgBase+myBin[i]], myMag[i]);
#endif
    }
#if defined(MF_METAL) && COARSE16
    // An overflow anywhere in this thread's registers (the transform has blown up; a NaN
    // spreads): every in-window register reports +inf, which passes every gate, and the
    // exact refine decides. Rare, so the branch costs nothing on quiet data.
    if ((ovAcc & 0x80008000u) != 0u) {
        MF_UNROLL for (uint i = 0; i < R; ++i)
            if (myMag[i] != 0u || (slotToIndex(tid * R + i) >= winStart
                                   && slotToIndex(tid * R + i) < winEnd))
                myMag[i] = 0x7F800000u;
    }
#endif

    // One bin over the whole window is the common case at the small sizes --
    // the CPU has a dedicated binmax_one for it. Every register shares the
    // bin, so they combine in REGISTERS first and the wave reduces once.
    // Reducing per register spends 16 wave operations where 1 will do, and
    // that single change was worth 2.48 -> 2.28 ms at n=4096.
#if COARSE16
    {                              // one bin: always this path
#else
    if (nbins == 1) {
#endif
        uint bestBits = thrBits;
        MF_UNROLL for (uint i = 0; i < R; ++i) bestBits = max(bestBits, myMag[i]);
#if PPG == 1
        uint wm = WaveActiveMax(bestBits);
        if (WaveIsFirstLane() && wm > thrBits) InterlockedMax(stg[_stgBase], wm);
#else
        // Several pairs share this wave, so a wave-wide reduction mixes
        // them: each pair receives the loudest of the group, only that one
        // matches its own value in the writeback, and the rest report -1.
        // Measured 16 of 64 survivors at band 128, PPG 4.
        //
        // No mask needed. Each lane maxes into ITS OWN pair's slot, which
        // _stgBase already scopes, so a tile cannot leak into its neighbour
        // by construction rather than by getting a lane mask right. Nearly
        // free: bestBits starts at the threshold and clears it only on a
        // real peak, so on noise the atomic almost never fires.
        if (bestBits > thrBits) InterlockedMax(stg[_stgBase], bestBits);
#endif
    }
    GroupMemoryBarrierWithGroupSync();

    // Elect ONE register slot before writing either output. Tied samples
    // can have different phases; independent index/value stores race.
#if COARSE16
    {
#else
    if (nbins == 1) {
#endif
        uint winner = 0xffffffffu;
        MF_UNROLL for (uint i = 0; i < R; ++i)
            if (myMag[i] > thrBits && myMag[i] == stg[_stgBase])
                winner = min(winner, tid * R + i);
#if PPG == 1
        uint waveWinner = WaveActiveMin(winner);
        if (WaveIsFirstLane() && waveWinner != 0xffffffffu)
            InterlockedMin(stg[_stgBase+1], waveWinner);
#else
        if (winner != 0xffffffffu) InterlockedMin(stg[_stgBase+1], winner);
#endif
        GroupMemoryBarrierWithGroupSync();
        MF_UNROLL for (uint i = 0; i < R; ++i) {
            if (tid * R + i == stg[_stgBase+1]) {
                peakIdx[pair] = int(slotToIndex(tid * R + i));
#if COARSE16
                peakVal[pair] = c16Bound(float2(float(r[i].x), float(r[i].y)), energy);
#else
                peakVal[pair] = float2(float(r[i].x), float(r[i].y));
#endif
            }
        }
        if (tid == 0 && stg[_stgBase+1] == 0xffffffffu) {
            peakIdx[pair] = -1;
            peakVal[pair] = float2(0, 0);
        }
    }
#if !COARSE16
    else {
        // Reuse the magnitude table for winner slots, retaining candidates
        // in registers. A separate bin array would increase LDS occupancy.
        MF_UNROLL for (uint i = 0; i < R; ++i)
            myMag[i] = uint(myMag[i] > thrBits &&
                           myMag[i] == stg[_stgBase+myBin[i]]);
        GroupMemoryBarrierWithGroupSync();
        for (uint b = tid; b < nbins; b += WG) stg[_stgBase+b] = 0xffffffffu;
        GroupMemoryBarrierWithGroupSync();
        MF_UNROLL for (uint i = 0; i < R; ++i)
            if (myMag[i] != 0u) InterlockedMin(stg[_stgBase+myBin[i]], tid*R+i);
        GroupMemoryBarrierWithGroupSync();
        MF_UNROLL for (uint i = 0; i < R; ++i) {
            if (myMag[i] != 0u && stg[_stgBase+myBin[i]] == tid*R+i) {
                uint o = pair * nbins + myBin[i];
                peakIdx[o] = int(slotToIndex(tid*R+i));
                peakVal[o] = float2(float(r[i].x), float(r[i].y));
            }
        }
        for (uint b = tid; b < nbins; b += WG) {
            if (stg[_stgBase+b] == 0xffffffffu) {
                peakIdx[pair*nbins+b] = -1;
                peakVal[pair*nbins+b] = float2(0, 0);
            }
        }
    }
#endif
#endif
}




#if COARSE16
//: Peak for ONE lane of the dual-transform registers. Each lane is a
//: different pair, so the reduction must stay per lane -- a wave-wide max
//: across lanes is the PPG bug again, and the flat-vs-hierarchical guard
//: is what catches it.
void peakLane(uint pair, uint tid, uint lane, H magv[16], H re[16], H im[16],
              RWStructuredBuffer<int> peakIdx, RWStructuredBuffer<float2> peakVal,
              uint winStart, uint winEnd, uint thrBits, float energy)
{
    GroupMemoryBarrierWithGroupSync();
    if (tid == 0) { stg[_stgBase] = thrBits; stg[_stgBase+1] = 0xffffffffu; }
    GroupMemoryBarrierWithGroupSync();

    // Reduce PACKED: one v_pk_max_f16 per register gives both lanes'
    // running maximum. The previous form extracted a lane per element --
    // 16 v_mov_b16 per pair -- to do the same work at half rate.
    // FAIL OPEN on overflow. A loud pair overflows fp16 (|v|^2 past 65504, and
    // inf - inf = NaN inside the transform); v_pk_max_f16 drops NaN, which made a
    // pair whose every sample overflowed report nothing and be gated out. NaN is
    // elected as +inf instead: any non-finite element wins and passes the gate.
    H bestH = H(0.0f), poison = H(0.0f);
    MF_UNROLL for (uint i = 0; i < R; ++i) { bestH = max(bestH, magv[i]); poison += magv[i] * H(0.0f); }
    float pl = float(lane == 0u ? poison.x : poison.y);
    uint bestBits = max(thrBits, isnan(pl) ? 0x7F800000u : asuint(float(lane == 0u ? bestH.x : bestH.y)));
#if PPG == 1
    uint wm = WaveActiveMax(bestBits);
    if (WaveIsFirstLane() && wm > thrBits) InterlockedMax(stg[_stgBase], wm);
#else
    if (bestBits > thrBits) InterlockedMax(stg[_stgBase], bestBits);
#endif
    GroupMemoryBarrierWithGroupSync();

    uint winner = 0xffffffffu;
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        uint mi = min(asuint(float(lane == 0u ? magv[i].x : magv[i].y)), 0x7F800000u);
        if (mi > thrBits && stg[_stgBase] == mi)
            winner = min(winner, tid*R+i);
    }
#if PPG == 1
    uint waveWinner = WaveActiveMin(winner);
    if (WaveIsFirstLane() && waveWinner != 0xffffffffu)
        InterlockedMin(stg[_stgBase+1], waveWinner);
#else
    if (winner != 0xffffffffu) InterlockedMin(stg[_stgBase+1], winner);
#endif
    GroupMemoryBarrierWithGroupSync();
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        if (pair != NOPAIR && stg[_stgBase+1] == tid*R+i) {
            peakIdx[pair] = int(slotToIndex(tid*R+i));
            peakVal[pair] = c16Bound(float2(float(lane == 0u ? re[i].x : re[i].y),
                                            float(lane == 0u ? im[i].x : im[i].y)), energy);
        }
    }
    if (pair != NOPAIR && tid == 0 && stg[_stgBase+1] == 0xffffffffu) {
        peakIdx[pair] = -1;
        peakVal[pair] = float2(0.0f, 0.0f);
    }
}

//: The same election as two peakLane calls -- the largest fp16 |v|^2 in the
//: window, ties to the LOWEST slot, its (re, im) reported -- for a pair whose
//: WG threads sit inside one subgroup, without LDS atomics or a dependent LDS
//: round trip per register.
//:
//: peakLane re-read the elected maximum from LDS inside every register's
//: comparison, so each of its 32 iterations (16 registers x 2 lanes) waited
//: out an LDS latency behind a branch: 30% of the band-256 coarse kernel,
//: measured by deleting it. Here the election is a max over 32-bit KEYS,
//:
//:     key = (fp16 |v|^2 bits << 16) | (0xFFFF - slot),
//:
//: so the larger magnitude wins and, among equal magnitudes, the lower slot.
//: Non-negative fp16 values order like their bit patterns, and like the
//: float32 bits peakLane compared, so the elected element is the same one.
//: The cross-thread max is a shuffle-xor butterfly over the pair's WG lanes,
//: which ACO emits as DPP max instructions (no LDS). The elected register is
//: then fetched through the stage by one lane.
//:
//: The window test uses that slotToIndex is a bit permutation: the register
//: index and tid*R occupy disjoint bits, so idx = slotToIndex(tid*R) |
//: slotToIndex(i), the second term a compile-time constant.
// The butterfly's lane exchange. The partner lane (lane ^ s, s < WG) is always in the
// same pair and so the same workgroup, and every lane of the group reaches this call.
// CUDA: a FULL-warp shuffle. Slang lowers WaveReadLaneAt to shfl.sync with a
// ballot-derived member mask, which under independent thread scheduling can name a
// partial warp after the barriers above (wrong peaks, measured on the L40S by the CUDA
// fold). Vulkan/Metal: subgroup read, which RADV emits as DPP with every lane active.
#if defined(MF_CUDA)
__target_intrinsic(cuda, "__shfl_xor_sync(0xffffffffu, $0, $1)")
uint mfShflXor(uint v, uint s);
#else
uint mfShflXor(uint v, uint s) { return WaveReadLaneAt(v, WaveGetLaneIndex() ^ s); }
#endif

void peakTwoWave(uint pairA, uint pairB, uint tid, H re[16], H im[16],
                 RWStructuredBuffer<int> peakIdx, RWStructuredBuffer<float2> peakVal,
                 uint winStart, uint winEnd, uint thrBits)
{
    uint u0 = slotToIndex(tid * R) - winStart;      // idx - winStart, wrapping
    uint span = winEnd - winStart;
    uint kA = 0u, kB = 0u;
    // Energy, both pairs, all lags, from values scaled by 2^-6 (exact): |v|^2
    // overflows fp16 past |v| = 256, which out-of-window lags of an ordinary
    // pair reach, and an inf energy would pass every pair. Scaled, a lag reaches
    // 16384 and the band's sum (x 2^-12) fits; only a value that overflowed
    // the transform itself makes it inf, and then the pair passes, as it must.
    H en = H(0.0f);
    const H esc = H(0.015625f);
#if defined(MF_METAL)
    uint ovAcc = 0u;
#endif
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        bool live = (u0 + slotToIndex(i)) < span;  // winStart <= idx < winEnd
        H mg = mag2s(re[i], im[i]);
        H sr = re[i] * esc, si = im[i] * esc;
        en += sr * sr + si * si;
        uint m = live ? bit_cast<uint>(mg) : 0u;
#if defined(MF_METAL)
        // FAIL OPEN on fp16 overflow, per lane (A low half, B high half): an exponent
        // field of all ones carries into the sign bit (see filterOne). Exact under fast math.
        // Each operand tested on its own: OR-ing the two first can assemble an all-ones
        // field from two finite exponents (0x7800 | 0x4400).
        ovAcc |= ((bit_cast<uint>(re[i]) & 0x7C007C00u) + 0x04000400u)
               | ((bit_cast<uint>(im[i]) & 0x7C007C00u) + 0x04000400u);
#endif
        kA = max(kA, (m << 16) | (15u - i));
        kB = max(kB, (m & 0xFFFF0000u) | (15u - i));
    }
#if defined(MF_METAL)
    // An overflowed lane takes the +inf key (slot of register 0), which wins and passes.
    if ((ovAcc & 0x00008000u) != 0u) kA = max(kA, 0x7C00000Fu);
    if ((ovAcc & 0x80000000u) != 0u) kB = max(kB, 0x7C00000Fu);
#endif
    // 0xFFFF - (tid*R + i) == ((0xFFF - tid) << 4) | (15 - i), R == 16
    kA |= (0xFFFu - tid) << 4;
    kB |= (0xFFFu - tid) << 4;
    [ForceUnroll] for (uint s = 1; s < WG; s <<= 1) {
        kA = max(kA, mfShflXor(kA, s));
        kB = max(kB, mfShflXor(kB, s));
        en += bit_cast<H>(mfShflXor(bit_cast<uint>(en), s));
    }
    // The transform's energy over all lags is N times the inputs' (Parseval), so
    // the per-lag rms the bound needs is energy / N.
    float enA = float(en.x) * (4096.0f / float(N)), enB = float(en.y) * (4096.0f / float(N));
    uint slotA = 0xFFFFu - (kA & 0xFFFFu), slotB = 0xFFFFu - (kB & 0xFFFFu);
    // FAIL OPEN on overflow. Keys compare as unsigned, so a NaN or inf |v|^2
    // (bits >= 0x7C00: a loud pair overflowing fp16) outranks every finite one and
    // is elected; it must then PASS. Its reported value is replaced by the largest
    // float, since the element itself may be NaN, which compares false against any
    // threshold and gated the whole loud batch out (0 peaks at SNR >= 2500).
    bool infA = (kA >> 16) >= 0x7C00u, infB = (kB >> 16) >= 0x7C00u;
#if defined(MF_METAL)
    // Slang's Metal target types f16tof32 as half, and as_type<uint>(half) is rejected;
    // both sides are non-negative and finite here, so values order as the bits do.
    bool hitA = infA || f16tof32(kA >> 16) > asfloat(thrBits);
    bool hitB = infB || f16tof32(kB >> 16) > asfloat(thrBits);
#else
    bool hitA = infA || asuint(f16tof32(kA >> 16)) > thrBits;
    bool hitB = infB || asuint(f16tof32(kB >> 16)) > thrBits;
#endif

    // Fetch the elected registers through the stage, one component at a
    // time and CH registers per chunk -- the stage holds CH*WG values.
    uint wA = slotA >> 4, iA = slotA & 15u, wB = slotB >> 4, iB = slotB & 15u;
    float vA[2], vB[2];
    vA[0] = vA[1] = vB[0] = vB[1] = 0.0f;
    [ForceUnroll] for (uint comp = 0; comp < 2; ++comp) {
        [ForceUnroll] for (uint c = 0; c < R / CH; ++c) {
            GroupMemoryBarrierWithGroupSync();
            MF_UNROLL for (uint j = 0; j < CH; ++j)
                stg[_stgBase + j * XS + tid] = bit_cast<uint>(comp == 0 ? re[c * CH + j] : im[c * CH + j]);
            GroupMemoryBarrierWithGroupSync();
            if (tid == 0) {
                if (iA >= c * CH && iA < (c + 1) * CH)
                    vA[comp] = f16tof32(stg[_stgBase + (iA - c * CH) * XS + wA]);
                if (iB >= c * CH && iB < (c + 1) * CH)
                    vB[comp] = f16tof32(stg[_stgBase + (iB - c * CH) * XS + wB] >> 16);
            }
        }
    }
    if (tid == 0 && pairA != NOPAIR) {
        peakIdx[pairA] = hitA ? int(slotToIndex(slotA)) : -1;
        peakVal[pairA] = infA ? float2(3.402823e38f, 0.0f)
                       : (hitA ? c16Bound(float2(vA[0], vA[1]), enA) : float2(0.0f, 0.0f));
    }
    if (tid == 0 && pairB != NOPAIR) {
        peakIdx[pairB] = hitB ? int(slotToIndex(slotB)) : -1;
        peakVal[pairB] = infB ? float2(3.402823e38f, 0.0f)
                       : (hitB ? c16Bound(float2(vB[0], vB[1]), enB) : float2(0.0f, 0.0f));
    }
}

//: TWO pairs at once in split/SoA form. Both share the data row and differ
//: only in template, so the data broadcasts to both lanes and the templates
//: fill one lane each. Every operation from here to the magnitude is
//: elementwise and packs.
void filterTwo(uint pairA, uint pairB, uint tA, uint tB, uint tid,
               C dreg[RADIX], StructuredBuffer<CVal> tmpl,
               RWStructuredBuffer<int> peakIdx, RWStructuredBuffer<float2> peakVal,
               uint winStart, uint winEnd, uint thrBits)
{
    H re[16], im[16];
    MF_UNROLL for (uint n2 = 0; n2 < R; ++n2) {
        C ta = cload(tmpl, tA*N + tid + WG * n2);
        C tb = cload(tmpl, tB*N + tid + WG * n2);
        H dr = H(dreg[n2].x, dreg[n2].x);     // data broadcast: .xx swizzle
        H di = H(dreg[n2].y, dreg[n2].y);
        H tr = H(ta.x, tb.x);                 // one template per lane
        H ti = H(ta.y, tb.y);
        cmulconjs(dr, di, tr, ti, re[n2], im[n2]);
    }

    [ForceUnroll] for (uint lvl = 0; lvl < NLEVELS; ++lvl) {
        const uint TB   = WG >> (LGR * lvl);
        const uint len  = N  >> (LGR * lvl);
        const uint lgTB = firstbithigh(TB);
        const uint lgLn = firstbithigh(len);
        uint blk  = tid >> lgTB;
        uint lane = tid & (TB - 1);

        dft16s(re, im);
#if defined(COARSE_TWT)
        {
            // W_len^(lane*k2) from the build's table, correctly rounded to
            // half: one 64-byte row per lane, so four 128-bit loads at
            // immediate offsets replace a cos/sin and an fp32 recurrence
            // with two conversions per register (~6 VALU each, ~96 a level).
            const uint toff = (lvl == 0) ? 0u : ((lvl == 1) ? WG * R : WG * R + (WG >> LGR) * R);
            MF_UNROLL for (uint k2 = 0; k2 < R; ++k2) {
                H w = bit_cast<H>(COARSE_TWT[toff + lane * R + k2]);
                cmulw(re[k2], im[k2], w.x, w.y);
            }
        }
#else
        {
            float a1 = 2.0f * PI * float(lane) / float(len);
            float2 tw = mfTwiddle(a1);
            float wr = tw.x, wi = tw.y;
            float cr = 1.0f, ci = 0.0f;
            MF_UNROLL for (uint k2 = 0; k2 < R; ++k2) {
                cmulw(re[k2], im[k2], CS(cr), CS(ci));
                float nr = cr * wr - ci * wi;
                ci = cr * wi + ci * wr;
                cr = nr;
            }
        }
#endif
        const uint per  = R / max(TB, 1u);
        const uint TB2  = max(TB >> LGR, 1u), len2 = TB;
        uint blk2 = tid / TB2, lane2 = tid % TB2;
        exchangeS(re, im, lgLn, lgTB, TB, len, blk, lane, per, TB2, len2, blk2, lane2);
    }
    innermostS(re, im);

    // |v|^2 for BOTH pairs in one packed multiply-add; the AoS path
    // promoted to fp32 here (128 v_cvt_f32_f16 in the dump).
    // |v|^2 masked by the window, both lanes at once. `live` depends on the
    // element index, which is shared by the two transforms, so the select
    // is packed and no lane is extracted here.
#if defined(MF_VULKAN) || defined(MF_CUDA) || defined(MF_METAL)
    // mfSubgroupSize is a specialization constant on Vulkan (one branch survives); 32 on
    // CUDA (the warp) and on Metal (Apple's SIMD-group width; the host checks the
    // pipeline's threadExecutionWidth). The election is subgroup shuffles and no barrier:
    // the earlier falsified Metal attempt relied on a simdgroup_barrier.
    const bool wavePeak = WG <= mfSubgroupSize;
#else
    const bool wavePeak = false;
#endif
    if (wavePeak) {
        peakTwoWave(pairA, pairB, tid, re, im, peakIdx, peakVal, winStart, winEnd, thrBits);
    } else {
        H magv[16];
        float eA = 0.0f, eB = 0.0f;
        MF_UNROLL for (uint i = 0; i < R; ++i) {
            uint idx = slotToIndex(tid * R + i);
            bool live = (idx >= winStart && idx < winEnd);
            H mg = mag2s(re[i], im[i]);
            eA += float(mg.x); eB += float(mg.y);
            magv[i] = live ? mg : H(0.0f);
#if defined(MF_METAL)
            // FAIL OPEN on fp16 overflow, per lane (see filterOne): an exponent field of
            // all ones in re or im makes that lane's magnitude +inf (a NaN would compare
            // unpredictably under fast math), which peakLane elects and passes.
            if (live) {
                uint ov = ((bit_cast<uint>(re[i]) & 0x7C007C00u) + 0x04000400u)
                        | ((bit_cast<uint>(im[i]) & 0x7C007C00u) + 0x04000400u);
                uint mb = bit_cast<uint>(magv[i]);
                if ((ov & 0x00008000u) != 0u) mb = (mb & 0xFFFF0000u) | 0x7C00u;
                if ((ov & 0x80000000u) != 0u) mb = (mb & 0x0000FFFFu) | 0x7C000000u;
                magv[i] = bit_cast<H>(mb);
            }
#endif
        }
        eA = pairSum(tid, eA) / float(N);
        eB = pairSum(tid, eB) / float(N);
        peakLane(pairA, tid, 0u, magv, re, im, peakIdx, peakVal, winStart, winEnd, thrBits, eA);
        peakLane(pairB, tid, 1u, magv, re, im, peakIdx, peakVal, winStart, winEnd, thrBits, eB);
    }
}
#endif

#if COARSE16
void filterPair(uint pair, uint tid,
                StructuredBuffer<CVal> data, StructuredBuffer<CVal> tmpl,
                RWStructuredBuffer<int> peakIdx, RWStructuredBuffer<float2> peakVal,
                uint ntmpl, uint winStart, uint winEnd,
                uint binsize, int binShift, uint nbins, uint thrBits)
{
    _tid = tid;
    // The host dispatches pairs/TILE_T groups, so this group owns TILE_T
    // CONSECUTIVE pairs starting here. Without the scale the kernel walked
    // pairs 0..pairs/TILE_T and simply never visited the rest -- which the
    // flat-vs-hierarchical guard caught as dismissed signals.
    //
    // Consecutive pairs share a data row because d = pair/ntmpl, provided
    // the run does not straddle a row end; the host drops to TILE_T=1 when
    // the pair count is not a multiple of it.
#if (defined(MF_VULKAN) || defined(MF_CUDA) || defined(MF_METAL)) && COARSE16 && (TILE_T % 2) == 0
    // RAGGED TILES. Each group slot takes TILE_T consecutive templates of ONE
    // data row, the row's last tile clamped to its last template; the host
    // passes the row count in `binsize` (unused by the one-bin coarse role)
    // and dispatches ceil(rows * ceil(ntmpl/TILE_T) / PPG) groups. A slot or
    // template past the end recomputes a valid one and writes nothing.
    //
    // This is what lets an ODD template count keep the two-pairs-per-lane
    // kernel. The exact-tile rule (ntmpl % TILE_T == 0) sent 52% of a
    // realistic fine segment's coarse pairs to the TILE_T=1 build, which
    // packs nothing into the second half of each register.
    uint tiles = (ntmpl + TILE_T - 1) / TILE_T;
    uint slots = binsize * tiles;
    bool slotOk = pair < slots;
    uint q = slotOk ? pair : slots - 1u;
    uint d = q / tiles, t0 = (q - d * tiles) * TILE_T;
    uint p0 = d * ntmpl + t0;
    rowWindow(d, winStart, winEnd);
#else
    uint p0 = pair * TILE_T;
    uint d = p0 / ntmpl, t0 = p0 % ntmpl;
#if COARSE16
    // Every coarse build honours per-row windows. The untiled builds once skipped
    // this: their module then declared no gRowWin, the host bound one past the
    // layout, and a grouped call gated every pair out (tests/test_vk_hier_grouped.py).
    rowWindow(d, winStart, winEnd);
#endif
#endif
    C dreg[RADIX];
#if COARSE16
    MF_UNROLL for (uint n2 = 0; n2 < R; ++n2)
        dreg[n2] = dload(data, d*DSTRIDE + tid + WG * n2);
#else
    MF_UNROLL for (uint n2 = 0; n2 < R; ++n2) dreg[n2] = C(0.0f);
#endif
#if COARSE16 && (TILE_T % 2) == 0
    // Two at a time, in split/SoA form.
#if defined(MF_VULKAN) || defined(MF_CUDA) || defined(MF_METAL)
    MF_UNROLL for (uint k = 0; k < TILE_T; k += 2) {
        bool okA = slotOk && t0 + k < ntmpl, okB = slotOk && t0 + k + 1 < ntmpl;
        filterTwo(okA ? p0 + k : NOPAIR, okB ? p0 + k + 1 : NOPAIR,
                  min(t0 + k, ntmpl - 1u), min(t0 + k + 1, ntmpl - 1u), tid, dreg, tmpl,
                  peakIdx, peakVal, winStart, winEnd, thrBits);
    }
#else
    MF_UNROLL for (uint k = 0; k < TILE_T; k += 2)
        filterTwo(p0 + k, p0 + k + 1, t0 + k, t0 + k + 1, tid, dreg, tmpl,
                  peakIdx, peakVal, winStart, winEnd, thrBits);
#endif
#else
    MF_UNROLL for (uint k = 0; k < TILE_T; ++k)
        filterOne(p0 + k, d, t0 + k, tid, dreg, data, tmpl, peakIdx, peakVal,
                  winStart, winEnd, binsize, binShift, nbins, thrBits);
#endif
}
#endif

[shader("compute")][numthreads(WG*PPG,1,1)]
void fusedTierB(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                StructuredBuffer<CVal> data, StructuredBuffer<CVal> tmpl,
                RWStructuredBuffer<int> peakIdx,
                RWStructuredBuffer<float2> peakVal,
                uniform uint ntmpl, uniform uint winStart, uniform uint winEnd,
                uniform uint binsize, uniform int binShift, uniform uint nbins,
                uniform uint thrBits)
{
    // lid spans PPG pairs of WG threads. Each slice is one pair, and at
    // band 512 one pair is exactly one wave, so WaveActiveMax below still
    // reduces per pair rather than across the group.
    // One pair per group: the split is identity and _stgBase is always 0.
    // Leaving the divide and the multiply in cost ~20% at band 512, where
    // this path is the default -- the compiler cannot prove _sub == 0.
    // Computed into locals rather than splitting the CALL across #if/#else,
    // which the preprocessor rejects outright at some sizes.
#if PPG == 1
    uint _pr = gid.x, _t = lid.x;
    _stgBase = 0;
#else
    uint _sub = lid.x / WG;
    uint _pr = gid.x * PPG + _sub, _t = lid.x % WG;
    _stgBase = _sub * STGW;
#endif
    filterPair(_pr, _t, data, tmpl, peakIdx, peakVal, ntmpl,
               winStart, winEnd, binsize, binShift, nbins, thrBits);
}

// Full circular correlation in natural lag order. The same fused spectral
// product and transform as the peak path, with one ordered output write per
// transformed sample and no peak table or reduction.
[shader("compute")][numthreads(WG,1,1)]
void fullCorrelation(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                     StructuredBuffer<CVal> data, StructuredBuffer<CVal> tmpl,
                     RWStructuredBuffer<float2> output, uniform uint ntmpl)
{
    uint pair = gid.x, tid = lid.x;
    uint d = pair / ntmpl, t = pair % ntmpl;
    _tid = tid;
    _stgBase = 0;
    C r[RADIX];
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        uint idx = tid + WG * i;
        r[i] = cmulConj(cload(data, d*N + idx), cload(tmpl, t*N + idx));
    }
    transform(r, tid);
    MF_UNROLL for (uint i = 0; i < R; ++i)
        output[pair*N + slotToIndex(tid*R + i)] = float2(float(r[i].x), float(r[i].y));
}

// The same transform, with its valid lags written at absolute series offsets.
// params = (template count, output length, valid start, valid end).
[shader("compute")][numthreads(WG,1,1)]
void fullCorrelationSeries(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                           StructuredBuffer<CVal> data, StructuredBuffer<CVal> tmpl,
                           StructuredBuffer<uint> starts,
                           RWStructuredBuffer<float2> output, uniform uint4 params)
{
    uint pair = gid.x, tid = lid.x;
    uint d = pair / params.x, t = pair % params.x;
    uint start = starts[d];
    _tid = tid;
    _stgBase = 0;
    C r[RADIX];
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        uint idx = tid + WG * i;
        r[i] = cmulConj(cload(data, d*N + idx), cload(tmpl, t*N + idx));
    }
    transform(r, tid);
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        uint lag = slotToIndex(tid*R + i);
        if (lag >= params.z && lag < params.w && lag < params.y - start)
            output[t*params.y + start + lag] = float2(float(r[i].x), float(r[i].y));
    }
}

//: Compaction. One THREAD per pair, not one workgroup.
//:
//: The refine used to launch a workgroup for every pair so that each could
//: read the coarse value, find itself below threshold, and exit. Measured at
//: 512x512 pairs and n=4096 that cost 1.394 ms of a 2.4 ms call -- 57% of the
//: work spent launching groups that do nothing, and it does not shrink with
//: the band because it is not arithmetic.
//:
//: So the survivors are gathered first and the refine is dispatched over the
//: list. The count lands in args[0], which is the X group count an indirect
//: dispatch reads, so it never has to reach the host: one recorded command
//: buffer still, exactly as before.
//:
//: The output has to be pre-cleared, because pairs that do not survive are
//: now never visited and something must still write their -1.
[shader("compute")][numthreads(256,1,1)]
void compactPairs(uint3 gid: SV_DispatchThreadID,
                  StructuredBuffer<float2> coarse,
                  RWStructuredBuffer<uint> survivors,
                  RWStructuredBuffer<uint> args,
                  uniform uint pairs, uniform float thr, uniform uint nbins)
{
    uint pair = gid.x;
#if defined(MF_VULKAN) || defined(MF_CUDA)
    // !(x < thr), not x >= thr: a NaN coarse value (an overflowed narrow tier)
    // passes. The gate may only ever fail open.
    bool active = (pair < pairs) && !(length(coarse[pair]) < thr);
    uint waveCount = WaveActiveCountBits(active);
    uint waveOffset = WavePrefixCountBits(active);
    uint baseSlot = 0;
    if (WaveIsFirstLane()) {
        if (waveCount > 0) {
            InterlockedAdd(args[0], waveCount, baseSlot);
        }
    }
    baseSlot = WaveReadLaneFirst(baseSlot);
    if (active) {
        survivors[baseSlot + waveOffset] = pair;
    }
#else
    if (pair >= pairs) return;
    // !(x < thr): a NaN coarse value is listed for the exact refine (fails open).
    if (!(length(coarse[pair]) < thr)) {
        uint slot;
        InterlockedAdd(args[0], 1u, slot);
        survivors[slot] = pair;
    }
#endif
}

//: Compaction over a LIST: the second tier's gate. Tier 1 ran only on the
//: pairs in `list` (the tier-0 survivors, count in listArgs[0]), so only those
//: pairs have a tier-1 value. Walking every pair, as compactPairs does, read
//: the whole cval1 array and needed it pre-cleared (pairs x 8 B of fill per
//: dispatch) so unvisited pairs read as zero. This visits the list alone.
//: The host dispatches ceil(pairs/256) groups -- an upper bound on the list
//: -- and lanes past the count exit; that costs launches, not bandwidth.
[shader("compute")][numthreads(256,1,1)]
void compactListed(uint3 gid: SV_DispatchThreadID,
                   StructuredBuffer<float2> coarse,
                   RWStructuredBuffer<uint> survivors,
                   RWStructuredBuffer<uint> args,
                   StructuredBuffer<uint> list,
                   StructuredBuffer<uint> listArgs,
                   uniform uint pairs, uniform float thr, uniform uint nbins)
{
    uint k = gid.x;
    uint count = listArgs[0];
    uint pair = (k < count) ? list[k] : 0u;
    bool active = (k < count) && !(length(coarse[pair]) < thr);
    uint waveCount = WaveActiveCountBits(active);
    uint waveOffset = WavePrefixCountBits(active);
    uint baseSlot = 0;
    if (WaveIsFirstLane() && waveCount > 0)
        InterlockedAdd(args[0], waveCount, baseSlot);
    baseSlot = WaveReadLaneFirst(baseSlot);
    if (active)
        survivors[baseSlot + waveOffset] = pair;
}

//: The refine, over a compacted list. Uses the same filtering body, except that
//: the pair comes from the list rather than from the group id, and there is
//: no gate left to apply -- being in the list IS having passed it.
[shader("compute")][numthreads(WG*PPG,1,1)]
void refineListed(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                  StructuredBuffer<CVal> data, StructuredBuffer<CVal> tmpl,
                  RWStructuredBuffer<int> peakIdx,
                  RWStructuredBuffer<float2> peakVal,
                  StructuredBuffer<uint> survivors,
                  uniform uint ntmpl, uniform uint winStart, uniform uint winEnd,
                  uniform uint binsize, uniform int binShift, uniform uint nbins,
                  uniform uint thrBits)
{
    uint pair = survivors[gid.x];
    // MUST be set on every path that reaches filterPair. Leaving it unset
    // here read as 0 under SPIR-V and as garbage under MSL, which offset
    // the whole staging window: the transform then read values never
    // written, every coarse peak came back -1, and macOS CI dismissed a
    // 12-sigma injection while Linux passed.
    _stgBase = 0;
    uint ws = winStart, we = winEnd;
    rowWindow(pair / ntmpl, ws, we);
    filterPair(pair, lid.x, data, tmpl, peakIdx, peakVal, ntmpl,
               ws, we, binsize, binShift, nbins, thrBits);
}

// ---------------------------------------------------------------------
// Tier C: the lengths one workgroup cannot carry.
//
// n = N1 * N2 with j = n1 + N1*n2 and k = k1*N2 + k2:
//
//   stage 1   one workgroup per (pair, n1): an N2-point transform over n2,
//             times W_n^(n1*k2), scattered to scratch[k2*N1 + n1]
//   stage 3   one workgroup per (pair, k2): an N1-point transform over n1,
//             output index k1*N2 + k2
//
// Both stages are THIS file compiled at their own NLEN -- stage 1 at N2,
// stage 3 at N1 -- so each reuses transform() and slotToIndex() rather than
// carrying a second copy of the decomposition. The other factor is then
// just TC_N/NLEN in both, which is why one define is enough.
//
// Verified against a float64 reference in tools/gpu_tierc_model.py, INCLUDING
// the register-to-index mapping: each stage leaves its output digit-reversed,
// so slotToIndex applies twice, and getting either wrong reports a real peak
// at the wrong sample.
#ifndef TC_N
#define TC_N 0
#endif
#if TC_N

//: N1 in stage 1, N2 in stage 3 -- the factor this compilation is NOT.
static const uint TC_OTHER = TC_N / NLEN;

[shader("compute")][numthreads(WG, 1, 1)]
void tcStage1(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
              StructuredBuffer<float2> data, StructuredBuffer<float2> tmpl,
              RWStructuredBuffer<float2> scratch, uniform uint ntmpl)
{
    uint pair = gid.x / TC_OTHER, n1 = gid.x % TC_OTHER;
    uint d = pair / ntmpl, t = pair % ntmpl;
    uint tid = lid.x;
    _tid = tid;
    _stgBase = 0;

    C r[RADIX];
    MF_UNROLL for (uint m = 0; m < R; ++m) {
        uint j = n1 + TC_OTHER * (tid + WG * m);
        r[m] = cmulConj(data[d * TC_N + j], tmpl[t * TC_N + j]);
    }
    transform(r, tid);

    //: n1*k2 < N1*N2 = n <= 2^22, so the product is exact in float32 and the
    //: angle stays inside one turn. Folding it any other way costs accuracy
    //: for nothing.
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        uint k2 = slotToIndex(tid * R + i);
        float a = 2.0f * PI * float(n1 * k2) / float(TC_N);
        scratch[pair * TC_N + k2 * TC_OTHER + n1] = cmul(r[i], C(mfTwiddle(a)));
    }
}

//: One candidate per (pair, k2): stage 3's workgroup owns a strided N1-sample
//: slice of the output, so the whole-transform maximum is a reduction ACROSS
//: workgroups. Each writes its own best and a third pass combines them --
//: N2 candidates a pair rather than n, which is why this needs no global
//: atomic and no second evaluation of the transform.
[shader("compute")][numthreads(WG, 1, 1)]
void tcStage3(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
              StructuredBuffer<float2> scratch,
              RWStructuredBuffer<uint> candMag, RWStructuredBuffer<int> candIdx,
              RWStructuredBuffer<float2> candVal,
              uniform uint winStart, uniform uint winEnd, uniform uint thrBits)
{
    uint pair = gid.x / TC_OTHER, k2 = gid.x % TC_OTHER;
    uint tid = lid.x;
    _tid = tid;
    _stgBase = 0;

    C r[RADIX];
    MF_UNROLL for (uint m = 0; m < R; ++m)
        r[m] = scratch[pair * TC_N + k2 * NLEN + (tid + WG * m)];
    transform(r, tid);

    uint best = thrBits;
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        uint k1 = slotToIndex(tid * R + i);
        uint idx = k1 * TC_OTHER + k2;
        bool live = (idx >= winStart && idx < winEnd);
        uint mg = live ? asuint(r[i].x * r[i].x + r[i].y * r[i].y) : 0u;
        best = max(best, mg);
    }

    GroupMemoryBarrierWithGroupSync();
    if (tid == 0) stg[0] = thrBits;
    GroupMemoryBarrierWithGroupSync();
    if (best > thrBits) InterlockedMax(stg[0], best);
    GroupMemoryBarrierWithGroupSync();

    uint slot = pair * TC_OTHER + k2;
    if (tid == 0 && stg[0] == thrBits) {
        candMag[slot] = thrBits;
        candIdx[slot] = -1;
        candVal[slot] = float2(0.0f, 0.0f);
    }
    GroupMemoryBarrierWithGroupSync();
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        uint k1 = slotToIndex(tid * R + i);
        uint idx = k1 * TC_OTHER + k2;
        bool live = (idx >= winStart && idx < winEnd);
        uint mg = live ? asuint(r[i].x * r[i].x + r[i].y * r[i].y) : 0u;
        if (mg > thrBits && stg[0] == mg) {
            candMag[slot] = mg;
            candIdx[slot] = int(idx);
            candVal[slot] = float2(float(r[i].x), float(r[i].y));
        }
    }
}

// Full-output Stage 3 has no inter-workgroup peak reduction. It writes one
// complete natural-order lag per register to the caller's output allocation.
[shader("compute")][numthreads(WG, 1, 1)]
void tcFullStage3(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                  StructuredBuffer<float2> scratch,
                  RWStructuredBuffer<float2> output)
{
    uint pair = gid.x / TC_OTHER, k2 = gid.x % TC_OTHER;
    uint tid = lid.x;
    _tid = tid;
    _stgBase = 0;
    C r[RADIX];
    MF_UNROLL for (uint m = 0; m < R; ++m)
        r[m] = scratch[pair * TC_N + k2 * NLEN + tid + WG*m];
    transform(r, tid);
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        uint k1 = slotToIndex(tid * R + i);
        output[pair * TC_N + k1 * TC_OTHER + k2] = float2(r[i].x, r[i].y);
    }
}

[shader("compute")][numthreads(WG, 1, 1)]
void tcFullSeriesStage3(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                        StructuredBuffer<float2> scratch,
                        StructuredBuffer<uint> starts,
                        RWStructuredBuffer<float2> output, uniform uint4 params)
{
    uint pair = gid.x / TC_OTHER, k2 = gid.x % TC_OTHER;
    uint d = pair / params.x, t = pair % params.x;
    uint start = starts[d];
    uint tid = lid.x;
    _tid = tid;
    _stgBase = 0;
    C r[RADIX];
    MF_UNROLL for (uint m = 0; m < R; ++m)
        r[m] = scratch[pair * TC_N + k2 * NLEN + tid + WG*m];
    transform(r, tid);
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        uint lag = slotToIndex(tid * R + i) * TC_OTHER + k2;
        if (lag >= params.z && lag < params.w && lag < params.y - start)
            output[t * params.y + start + lag] = float2(r[i].x, r[i].y);
    }
}

// FFT(series)/n = conj(IFFT(conj(series)/n)). The same inverse butterflies,
// twiddle and scratch layout therefore serve the time-series forward pass.
[shader("compute")][numthreads(WG, 1, 1)]
void tcForwardStage1(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                      StructuredBuffer<float2> series,
                      StructuredBuffer<uint> starts,
                      RWStructuredBuffer<float2> scratch,
                      uniform uint seriesLength)
{
    uint block = gid.x / TC_OTHER, n1 = gid.x % TC_OTHER;
    uint tid = lid.x;
    uint start = starts[block];
    _tid = tid;
    _stgBase = 0;
    C r[RADIX];
    MF_UNROLL for (uint m = 0; m < R; ++m) {
        uint j = n1 + TC_OTHER * (tid + WG*m);
        float2 x = float2(0, 0);
        if (start < seriesLength && j < seriesLength - start)
            x = series[start+j];
        r[m] = C(x.x/float(TC_N), -x.y/float(TC_N));
    }
    transform(r, tid);
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        uint k2 = slotToIndex(tid * R + i);
        float a = 2.0f * PI * float(n1 * k2) / float(TC_N);
        scratch[block * TC_N + k2 * TC_OTHER + n1] = cmul(r[i], C(mfTwiddle(a)));
    }
}

[shader("compute")][numthreads(WG, 1, 1)]
void tcForwardStage3(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                      StructuredBuffer<float2> scratch,
                      RWStructuredBuffer<float2> spectra)
{
    uint block = gid.x / TC_OTHER, k2 = gid.x % TC_OTHER;
    uint tid = lid.x;
    _tid = tid;
    _stgBase = 0;
    C r[RADIX];
    MF_UNROLL for (uint m = 0; m < R; ++m)
        r[m] = scratch[block * TC_N + k2 * NLEN + tid + WG*m];
    transform(r, tid);
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        uint k1 = slotToIndex(tid * R + i);
        spectra[block * TC_N + k1 * TC_OTHER + k2] = float2(r[i].x, -r[i].y);
    }
}
#endif
