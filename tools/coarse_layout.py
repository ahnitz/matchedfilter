"""Build-time layout for the packed fp16 coarse kernel (tierb.slang, COARSE16).

Two things the shader takes as compile-time input rather than computing:

exchange_layout(n, ppg) -> (XSTRIDE, XSLOT)
    The stage row stride and the per-pair region of the SoA exchange, chosen by
    an LDS bank model. A wave64 LDS b32 access runs as two 32-lane halves over
    32 four-byte banks; the cost of an access is the most lanes that land on one
    bank in a half. The default layout (stride WG) put all 16 registers a band-256
    thread reads into one row, 16 words apart across the pair's lanes: 8-way
    conflicts on every read. The model scores every write and read the exchange
    issues and picks the padding with the fewest conflicts, then the least LDS.
    It also checks the affine separation exchangeS relies on (see there).

twiddle_table_source(n) -> Slang source
    W_len^(lane*k2) for every exchange level, correctly rounded to fp16 and
    packed (real in the low half), in the order filterTwo reads it: level by
    level, one row of R entries per lane.

Run directly to print the model's choices against the default layout.
"""
import numpy as np

R = 16
WAVE, BANKS, HALF = 64, 32, 32
#: Bank models, (subgroup lanes, banks of 4 B, lanes served per bank cycle). RDNA wave64 runs
#: an LDS access as two 32-lane halves. Apple (M2) measured with tools/metal_bank_probe.py:
#: the k-way conflict cost is linear in k-1 with period 32 in the word stride, so 32 banks of
#: 4 B serving the whole 32-lane SIMD group at once.
MODELS = {"rdna_wave64": (64, 32, 32), "apple_simd32": (32, 32, 32)}


def _lg(x):
    return x.bit_length() - 1


def _geometry(n, lds_cap):
    wg = n // R
    lgr = _lg(R)
    nlevels = 1 if wg <= R else (2 if wg <= R * R else 3)
    cap = min(R * wg, lds_cap)
    ch = min(max(cap // wg, 1), R)
    levels = []
    for lvl in range(nlevels):
        tb = wg >> (lgr * lvl)
        ln = n >> (lgr * lvl)
        levels.append((tb, ln))
    return wg, ch, levels


def _source(tb, ln, tid, d):
    """(row, column) of the stage that register d of thread tid reads: computeWant + exchangeS."""
    lgtb, lgln = _lg(tb), _lg(ln)
    per, tb2, len2 = R // max(tb, 1), max(tb >> _lg(R), 1), tb
    blk, lane = tid >> lgtb, tid & (tb - 1)
    blk2, lane2 = tid // tb2, tid % tb2
    j, m = d // tb, d % tb
    p = (blk * ln + (lane * per + j) * tb + m) if tb <= R else (blk2 * len2 + lane2 + tb2 * d)
    b, rem = p >> lgln, p & ((1 << lgln) - 1)
    return rem >> lgtb, (b << lgtb) + (rem & ((1 << lgtb) - 1))


def affine_separable(n, lds_cap):
    """exchangeS reads register d at base(tid) + offset(d): true for this geometry?"""
    wg, ch, levels = _geometry(n, lds_cap)
    for tb, ln in levels:
        for tid in range(wg):
            i0, c0 = _source(tb, ln, tid, 0)
            for d in range(R):
                i, c = _source(tb, ln, tid, d)
                iz, cz = _source(tb, ln, 0, d)
                if (i, c) != (i0 + iz, c0 + cz):
                    return False
    return True


def _conflict(lane_addrs):
    total = 0
    for h0 in range(0, WAVE, HALF):
        count = {}
        for lane, a in lane_addrs:
            if h0 <= lane < h0 + HALF and a is not None:
                count[a % BANKS] = count.get(a % BANKS, 0) + 1
        if count:
            total += max(count.values())
    return total


def exchange_cost(n, ppg, xs, slot, lds_cap):
    """Summed per-half worst bank multiplicity over every exchange access of one wave."""
    wg, ch, levels = _geometry(n, lds_cap)
    lanes = min(WAVE, wg * ppg)
    total = 0
    for tb, ln in levels:
        for c in range(R // ch):
            for j in range(ch):
                total += _conflict([(L, (L // wg) * slot + j * xs + L % wg) for L in range(lanes)])
            for d in range(R):
                acc = []
                for L in range(lanes):
                    i, col = _source(tb, ln, L % wg, d)
                    inside = c * ch <= i < (c + 1) * ch
                    acc.append((L, (L // wg) * slot + (i - c * ch) * xs + col if inside else None))
                total += _conflict(acc)
    return total


def exchange_layout(n, ppg, lds_cap, model="rdna_wave64"):
    """(XSTRIDE, XSLOT) for the coarse SoA exchange at band n and ppg pairs per group,
    under a bank model of MODELS."""
    global WAVE, BANKS, HALF
    saved = WAVE, BANKS, HALF
    WAVE, BANKS, HALF = MODELS[model]
    try:
        return _exchange_layout(n, ppg, lds_cap)
    finally:
        WAVE, BANKS, HALF = saved


def _exchange_layout(n, ppg, lds_cap):
    wg, ch, _ = _geometry(n, lds_cap)
    if not affine_separable(n, lds_cap):
        raise ValueError("exchangeS needs affine-separable sources; n=%d is not" % n)
    best = None
    for xs in range(wg, wg + 9):
        for pad in range(0, BANKS + 1):
            slot = ch * xs + pad
            key = (exchange_cost(n, ppg, xs, slot, lds_cap), (ppg - 1) * slot + ch * xs)
            if best is None or key < best[0]:
                best = (key, xs, slot)
    return best[1], best[2]


def twiddle_table_source(n):
    """Slang source defining COARSE_TWT for band n (see filterTwo)."""
    wg, _, levels = _geometry(n, 1 << 30)
    words = []
    for tb, ln in levels:
        lane = np.arange(tb)[:, None]
        k2 = np.arange(R)[None, :]
        ang = 2.0 * np.pi * ((lane * k2) % ln) / ln
        wr = np.cos(ang).astype(np.float16).view(np.uint16).astype(np.uint32)
        wi = np.sin(ang).astype(np.float16).view(np.uint16).astype(np.uint32)
        words.extend((wr | (wi << 16)).ravel().tolist())
    body = ",".join("0x%08x" % w for w in words)
    return ("static const uint COARSE_TWT_DATA[%d] = {%s};\n#define COARSE_TWT COARSE_TWT_DATA\n"
            % (len(words), body))


if __name__ == "__main__":
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import build_spirv as B
    for n in (64, 128, 256, 512, 1024):
        wg, ch, _ = _geometry(n, B.LDS_CAP[n])
        for ppg in (1, 2, 4, 8, 16):
            if wg * ppg > 1024:
                continue
            xs, slot = exchange_layout(n, ppg, B.LDS_CAP[n])
            print("band %4d ppg %2d: default cost %4d -> XSTRIDE %2d XSLOT %4d cost %4d"
                  % (n, ppg, exchange_cost(n, ppg, wg, ch * wg, B.LDS_CAP[n]), xs, slot,
                     exchange_cost(n, ppg, xs, slot, B.LDS_CAP[n])))


#: The fp16 coarse transform's rounding error at the elected lag, in units of
#: u rms(y) (u = 2^-11, rms(y)^2 = sum_j |x_j|^2): its standard deviation per band,
#: the largest over the gate_margin families (noise, profile-shaped, injection, loud
#: transient), 1024 pairs each, rounded up to 0.1. Measured on the Radeon 8060S with
#: the bound disabled (spec constant mfC16Bound = 0; see docs/vulkan-8060s-roofline.md
#: section 10). This is the arithmetic's own error, characterised once -- it is NOT the
#: margin, which follows from it:
C16_SIGMA = {64: 1.6, 128: 1.7, 256: 1.8, 512: 2.2, 1024: 2.5, 2048: 3.3}

#: The same, measured on the Apple M2 through the Metal builds (tiled and untiled, the
#: larger), by tools/metal_c16_sigma.py with the bound switched off (MF_VK_C16_BOUND=0):
#: 8192 pairs per band. The worst residual after the proven (1+3u) factor was 4.9 u rms
#: (band 2048, loud transient), against kappa 18.3 there.
C16_SIGMA_APPLE = {64: 1.5, 128: 1.7, 256: 1.8, 512: 2.0, 1024: 2.2, 2048: 2.6}

#: Per-pair probability that the rms part of the bound fails, and the one-sided
#: normal quantile it implies: kappa_B = z * sigma_B. 1e-12 per pair is ~1e-3 per
#: year of pairs at this search's rate; the dismissal budget the gates are
#: calibrated to (fd ~ 1e-3 per signal) is many orders of magnitude larger.
C16_FAIL = 1e-12


def c16_kappa(n, sigmas=None):
    """kappa for band n: z(C16_FAIL) * sigma_n (the bound's rms coefficient); sigmas is the
    measured table of the target (C16_SIGMA: Radeon/Vulkan, C16_SIGMA_APPLE: Metal)."""
    from statistics import NormalDist
    sigmas = C16_SIGMA if sigmas is None else sigmas
    z = NormalDist().inv_cdf(1.0 - C16_FAIL)
    sigma = sigmas.get(n, max(sigmas.values()))
    return z * sigma
