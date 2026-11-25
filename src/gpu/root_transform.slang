// The root stage of a hierarchical search on the device: appended to tierb.slang, compiled
// as the two stages of a two-stage (Tier C) inverse transform at TC_N = h (tools/
// kernel_variants.py, roles root1 at NLEN = N2 and root2 at NLEN = N1), PPG columns of the
// decomposition per workgroup.
//
// The root's output for one block is the real n-point series scale * C2R(P), n = 2h, of the
// product P[k] = conj(T[k]) D[k] over bins [k0, k1) of two one-sided spectra (h + 1 bins).
// As on the host (src/rsplit-inl.h, root_merge), it is the h-point inverse transform of the
// merged spectrum
//
//   Z[k] = (P[k] + conj(P[h-k])) + i e^{2 pi i k / n} (P[k] - conj(P[h-k]))
//
// read as h complex samples = n real ones, with P[0] and P[h] taken real.
//
// With h = N1 N2, point j = n1 + N1 n2 and output k = k1 N2 + k2:
//   stage 1 (tcRootStage1): per column n1, Z over n2 (formed here from the four inputs it
//            needs: D and T at j and h - j), an N2-point inverse, times W_h^(n1 k2), to
//            scratch[k2 N1 + n1];
//   stage 2 (tcRootStage2): per k2, the N1-point inverse over n1, to out[k1 N2 + k2].
// A column's points lie N1 apart, and so do a stage-2 column's outputs N2 apart. One column
// per workgroup (tcStage1 and tcFullStage3) moves each 8-byte value in a cache line of its
// own; here a workgroup takes PPG columns, each transformed by its own WG threads (as
// tierb.slang's pairs per group), and its global reads and writes go through workgroup
// memory as rows of adjacent values. Stage 1's columns come in mirror pairs (rootColumn),
// so the products its merge needs are all its own.
#if TC_N

//: Columns of one workgroup, and the row pitch (in words) of the row tiles staged through
//: stg: one more than PPG, so a column read across a wave's lanes hits distinct banks.
static const uint RC = PPG;
static const uint RPITCH = PPG + 1u;
static const uint STG_WORDS = STGW * PPG;
//: Registers loaded per staged chunk in stage 1 (own and mirror products, two planes each):
//: the largest power of two that fits, at most R.
static const uint RFIT = STG_WORDS / (4u * RPITCH * WG);
static const uint RREG = (RFIT >= 16u) ? 16u : ((RFIT >= 8u) ? 8u : ((RFIT >= 4u) ? 4u
                        : ((RFIT >= 2u) ? 2u : 1u)));
static const uint RROWS = RREG * WG;
static const uint RPLANE = RROWS * RPITCH;
//: Output rows staged per pass (two planes): the largest power of two that fits, at most NLEN.
static const uint OFIT = STG_WORDS / (2u * RPITCH);
static const uint OROWS0 = (OFIT >= 2048u) ? 2048u : ((OFIT >= 1024u) ? 1024u
                         : ((OFIT >= 512u) ? 512u : ((OFIT >= 256u) ? 256u
                         : ((OFIT >= 128u) ? 128u : 64u))));
static const uint OROWS = (OROWS0 < NLEN) ? OROWS0 : NLEN;
static const uint OPLANE = OROWS * RPITCH;

//: P[k] = scale conj(T[k]) D[k] inside [k0, k1), else zero; real at k = 0 and k = h
//: (root_merge's prod and its k = 0 term).
C rootProduct(StructuredBuffer<float2> data, StructuredBuffer<float2> tmpl, uint k,
              uint k0, uint k1, float scale)
{
    if (k < k0 || k >= k1)
        return C(0.0f, 0.0f);
    float2 d = data[k], t = tmpl[k];
    float im = (k == 0u || k == TC_N) ? 0.0f : scale * (t.x * d.y - t.y * d.x);
    return C(scale * (t.x * d.x + t.y * d.y), im);
}

//: Stage 1's column at position p (< RC) of workgroup g: pairs of mirror columns (n1,
//: N1 - n1), RC/2 of them per workgroup, so that every product a workgroup needs is one it
//: reads -- the mirror of a point lies in its mirror column -- and none is read twice.
//: Workgroup 0 holds the two columns that are their own mirrors, 0 and N1/2, and pairs
//: 1..RC/2-1; workgroup g > 0 pairs g RC/2 .. (g + 1) RC/2 - 1.
uint rootColumn(uint g, uint p)
{
    uint i = p >> 1;
    if (g == 0u) {
        if (p == 0u) return 0u;
        if (p == 1u) return TC_OTHER / 2u;
        i = (p >> 1);                         // pairs 1 .. RC/2 - 1 at positions 2..RC-1
        return ((p & 1u) == 0u) ? i : TC_OTHER - i;
    }
    uint c = g * (RC / 2u) + i;
    return ((p & 1u) == 0u) ? c : TC_OTHER - c;
}

//: The position of p's mirror column in its workgroup.
uint rootMirror(uint g, uint p)
{
    return (g == 0u && p < 2u) ? p : (p ^ 1u);
}

//: Write this thread's registers whose output row (slotToIndex) falls in pass p to the
//: staged tile rows [p OROWS, (p + 1) OROWS) of column col.
void rootStageOut(C r[RADIX], uint tid, uint col, uint p)
{
    MF_UNROLL for (uint i = 0; i < R; ++i) {
        uint row = slotToIndex(tid * R + i);
        if (row / OROWS == p) {
            uint a = (row % OROWS) * RPITCH + col;
            stg[a] = asuint(r[i].x);
            stg[a + OPLANE] = asuint(r[i].y);
        }
    }
}

//: params[4 slot ..]: k0, k1, the scale's bits (and one spare word), written by the host
//: before each run, so one recording serves every block, band and scale.
[shader("compute")][numthreads(WG * PPG, 1, 1)]
void tcRootStage1(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                  StructuredBuffer<float2> data, StructuredBuffer<float2> tmpl,
                  StructuredBuffer<uint> params, RWStructuredBuffer<float2> scratch,
                  uniform uint slot)
{
    uint g = gid.x;
    uint l = lid.x, col = l / WG, tid = l % WG;
    uint n1 = rootColumn(g, col), mcol = rootMirror(g, col);
    uint k0 = params[4u * slot], k1 = params[4u * slot + 1u];
    float scale = asfloat(params[4u * slot + 2u]);

    // Z at this thread's points j = n1 + N1 (tid + WG m). A point's mirror h - j is row
    // N2 - 1 - r of the mirror column (column 0's: row N2 - r, h itself at r = 0), so rows
    // are staged two chunks at a time, q and its mirror Q - 1 - q, all RC columns: then every
    // register of both chunks finds its pair, and each product is read once.
    C r[RADIX];
    const uint Q = NLEN / RROWS;
    MF_UNROLL for (uint q = 0; q < Q / 2u; ++q) {
        GroupMemoryBarrierWithGroupSync();
        MF_UNROLL for (uint s = 0; s < 2u * RROWS / WG; ++s) {
            uint e = l + WG * PPG * s;
            uint half = e / (RROWS * RC), w = e % (RROWS * RC);
            uint rr = w / RC, p = w % RC;
            uint row = ((half == 0u) ? q : (Q - 1u - q)) * RROWS + rr;
            C v = rootProduct(data, tmpl, rootColumn(g, p) + TC_OTHER * row, k0, k1, scale);
            uint a = half * 2u * RPLANE + rr * RPITCH + p;
            stg[a] = asuint(v.x);
            stg[a + RPLANE] = asuint(v.y);
        }
        GroupMemoryBarrierWithGroupSync();
        MF_UNROLL for (uint half = 0; half < 2u; ++half) {
            uint qq = (half == 0u) ? q : (Q - 1u - q);
            MF_UNROLL for (uint mm = 0; mm < RREG; ++mm) {
                uint m = qq * RREG + mm;
                uint rr = tid + WG * mm;
                uint a = half * 2u * RPLANE + rr * RPITCH + col;
                C pa = C(asfloat(stg[a]), asfloat(stg[a + RPLANE]));
                uint j = n1 + TC_OTHER * (tid + WG * m);
                C pb;
                if (n1 == 0u) {
                    // column 0 pairs row r with row N2 - r: read from memory (one column)
                    pb = rootProduct(data, tmpl, TC_N - j, k0, k1, scale);
                } else {
                    uint b = (1u - half) * 2u * RPLANE + (RROWS - 1u - rr) * RPITCH + mcol;
                    pb = C(asfloat(stg[b]), asfloat(stg[b + RPLANE]));
                }
                float sr = pa.x + pb.x, si = pa.y - pb.y, er = pa.x - pb.x, ei = pa.y + pb.y;
                float2 w = mfTwiddle(PI * float(j) / float(TC_N));
                float u = w.x * ei + w.y * er, v = w.x * er - w.y * ei;
                r[m] = C(sr - u, si + v);
            }
        }
    }
    GroupMemoryBarrierWithGroupSync();
    _tid = tid;
    _stgBase = col * STGW;
    transform(r, tid);

    MF_UNROLL for (uint i = 0; i < R; ++i) {
        uint k2 = slotToIndex(tid * R + i);
        r[i] = cmul(r[i], C(mfTwiddle(2.0f * PI * float(n1 * k2) / float(TC_N))));
    }
    // scratch[k2 N1 + n1]: rows of the workgroup's RC columns (two runs of RC/2)
    MF_UNROLL for (uint p = 0; p < NLEN / OROWS; ++p) {
        GroupMemoryBarrierWithGroupSync();
        rootStageOut(r, tid, col, p);
        GroupMemoryBarrierWithGroupSync();
        MF_UNROLL for (uint s = 0; s < OROWS / WG; ++s) {
            uint e = l + WG * PPG * s;
            uint rr = e / RC, c = e % RC;
            uint a = rr * RPITCH + c;
            scratch[(p * OROWS + rr) * TC_OTHER + rootColumn(g, c)] =
                float2(asfloat(stg[a]), asfloat(stg[a + OPLANE]));
        }
    }
}

//: Stage 2: per k2 (RC adjacent ones per workgroup) the NLEN = N1 point inverse of
//: scratch[k2 N1 ..], written to out[k1 N2 + k2] as rows of RC adjacent outputs.
[shader("compute")][numthreads(WG * PPG, 1, 1)]
void tcRootStage2(uint3 gid: SV_GroupID, uint3 lid: SV_GroupThreadID,
                  StructuredBuffer<float2> scratch, RWStructuredBuffer<float2> output)
{
    uint b0 = RC * gid.x;
    uint l = lid.x, col = l / WG, tid = l % WG;
    _tid = tid;
    _stgBase = col * STGW;
    C r[RADIX];
    MF_UNROLL for (uint m = 0; m < R; ++m)
        r[m] = scratch[(b0 + col) * NLEN + tid + WG * m];
    transform(r, tid);
    MF_UNROLL for (uint p = 0; p < NLEN / OROWS; ++p) {
        GroupMemoryBarrierWithGroupSync();
        rootStageOut(r, tid, col, p);
        GroupMemoryBarrierWithGroupSync();
        MF_UNROLL for (uint s = 0; s < OROWS / WG; ++s) {
            uint e = l + WG * PPG * s;
            uint rr = e / RC, c = e % RC;
            uint a = rr * RPITCH + c;
            output[(p * OROWS + rr) * TC_OTHER + b0 + c] =
                float2(asfloat(stg[a]), asfloat(stg[a + OPLANE]));
        }
    }
}
#endif
