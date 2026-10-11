// Device-side follow-up items (CUDA): the fine stage's peaks -> follow-up windows, with no
// host round trip, so the follow-ups join the segment graph (time_domain.SegmentPlan,
// FollowUp). The rule is FollowUp's (time_domain.py), applied per source job:
//
//   candidates  the job's fine peaks with |snr| >= thr,
//   order       by |snr| descending, ties in the job's own result order (stable),
//   keep        the first peak in each dedupe interval (sample / dedupe),
//   item        for each kept peak: the PARTNER job's series, the window
//               [max(0, c - half), min(S, c + half)), the peak's template, threshold 0.
//
// fuSelect (one block per source job) builds the items; fuBlocks (one thread per item block)
// lays each window onto its group's block grid exactly as TimeDomainFilterBank._window_layout
// does, writes the block's series offset for the forward and a refineItems entry
// (src/gpu/refine_bounded.slang). Every capacity is fixed; exceeding one sets a flag and the
// host redoes that segment's follow-ups on the host path.

// Dispatch table, one row of DT words per fine dispatch (uint32):
#define DT 16
//  0 job          1 entry (order of this call in the job's results)
//  2 nt           3 nb           4 b0 (first layout row)   5 rows (b1 - b0)
//  6..7  records  (u64: compactPeaks records: flat, idx, re, im)
//  8..9  count    (u64: record count)
// 10..11 rowSample (u64: int64 per layout row: the block's absolute start sample)
// 12..13 rowCaller (u64: uint32 per layout row: its block index in caller order)
// 14..15 tmplGlobal (u64: int64 per local template: its bank index)
// Job table, JT words per job: 0 first dispatch, 1 dispatch count, 2 partner job,
// 4 S (this job's series length), 5..6 this job's series offset (samples) in its allocation.
#define JT 8
// Follow-up group table (one per bank template group x partner allocation; dgroup maps each
// dispatch to it), GT words: 0 n, 1 step (n_valid), 2 c_bad, 3 region (forward workspace:
// one per block length x allocation), 4 list (refineItems list: one per follow-up group).
#define GT 8
// Item record IT words: 0 job, 1 rank, 2 c0 lo, 3 c0 hi, 4 ti lo, 5 ti hi, 6 t local,
// 7 group, 8 region slot, 9 nblocks
#define IT 10
#define CAND_MAX 1024

extern "C" {

__device__ inline unsigned long long ld64(const unsigned* p)
{
    return (unsigned long long)p[0] | ((unsigned long long)p[1] << 32);
}

// One block per source job. flags[0] overflow, counts[0] items, counts[1 + r] region slots.
__global__ void fuSelect(const unsigned* __restrict__ dtab, const unsigned* __restrict__ jtab,
                         const unsigned* __restrict__ dgroup, const unsigned* __restrict__ gtab,
                         unsigned* __restrict__ items, unsigned* __restrict__ counts,
                         unsigned* __restrict__ flags, unsigned maxItems,
                         const unsigned* __restrict__ rcap,
                         float thr, unsigned dedupe, unsigned njobs)
{
    __shared__ float cabs[CAND_MAX];
    __shared__ unsigned long long ckey[CAND_MAX];
    __shared__ long long csample[CAND_MAX];
    __shared__ long long cti[CAND_MAX];
    __shared__ unsigned ct[CAND_MAX], cg[CAND_MAX], crank[CAND_MAX];
    __shared__ unsigned ncand;
    const unsigned j = blockIdx.x;
    if (j >= njobs) return;
    const unsigned* jr = jtab + j * JT;
    if (threadIdx.x == 0) ncand = 0;
    __syncthreads();
    for (unsigned k = 0; k < jr[1]; ++k) {
        const unsigned dk = jr[0] + k;
        const unsigned* d = dtab + dk * DT;
        const unsigned* rec = (const unsigned*)ld64(d + 6);
        const unsigned cnt = *(const unsigned*)ld64(d + 8);
        const long long* rowSample = (const long long*)ld64(d + 10);
        const unsigned* rowCaller = (const unsigned*)ld64(d + 12);
        const long long* tmplGlobal = (const long long*)ld64(d + 14);
        const unsigned nt = d[2], nb = d[3], b0 = d[4], rows = d[5];
        for (unsigned i = threadIdx.x; i < cnt; i += blockDim.x) {
            const unsigned flat = rec[4 * i];
            const unsigned per = nt * nb;
            const unsigned bi = flat / per, rest = flat - bi * per;
            if (bi >= rows) continue;                      // padded rows
            const unsigned t = rest / nb, bin = rest - t * nb;
            const float re = __int_as_float(rec[4 * i + 2]), im = __int_as_float(rec[4 * i + 3]);
            const float a = hypotf(re, im);
            if (!(a >= thr)) continue;
            const unsigned slot = atomicAdd(&ncand, 1u);
            if (slot >= CAND_MAX) { flags[0] = 1u; continue; }
            const unsigned lr = b0 + bi;
            const unsigned row = rowCaller[lr];
            cabs[slot] = a;
            // The job's result order: call entry, caller block, template, bin.
            ckey[slot] = ((unsigned long long)d[1] << 56) | ((unsigned long long)row << 32)
                         | ((unsigned long long)t << 16) | (unsigned long long)bin;
            csample[slot] = rowSample[lr] + (long long)(int)rec[4 * i + 1];
            cti[slot] = tmplGlobal[t];
            ct[slot] = t;
            cg[slot] = dgroup[dk];
        }
        __syncthreads();
    }
    const unsigned n = min(ncand, (unsigned)CAND_MAX);
    // Rank: |snr| descending, then key ascending (np.argsort(-|snr|, kind="stable")).
    for (unsigned a = threadIdx.x; a < n; a += blockDim.x) {
        unsigned r = 0;
        for (unsigned b = 0; b < n; ++b)
            r += (cabs[b] > cabs[a]) || (cabs[b] == cabs[a] && ckey[b] < ckey[a]);
        crank[r] = a;
    }
    __syncthreads();
    if (threadIdx.x != 0) return;
    // One per dedupe interval, in rank order. A small linear set: kept peaks are few.
    long long used[256];
    unsigned nused = 0;
    for (unsigned r = 0; r < n; ++r) {
        const unsigned a = crank[r];
        const long long sec = csample[a] / (long long)dedupe;
        bool seen = false;
        for (unsigned u = 0; u < nused; ++u) seen |= used[u] == sec;
        if (seen) continue;
        if (nused == 256) { flags[0] = 1u; break; }
        used[nused++] = sec;
        const unsigned g = cg[a];
        const unsigned region = gtab[g * GT + 3];
        const unsigned rs = atomicAdd(&counts[1 + region], 1u);
        if (rs >= rcap[region]) { flags[0] = 1u; continue; }
        const unsigned it = atomicAdd(&counts[0], 1u);
        if (it >= maxItems) { flags[0] = 1u; continue; }
        unsigned* o = items + it * IT;
        o[0] = j; o[1] = r;
        o[2] = (unsigned)(csample[a] & 0xffffffffu); o[3] = (unsigned)(csample[a] >> 32);
        o[4] = (unsigned)(cti[a] & 0xffffffffu); o[5] = (unsigned)(cti[a] >> 32);
        o[6] = ct[a]; o[7] = g; o[8] = rs; o[9] = 0;
    }
}

// One thread per (item, block slot). bpi block slots per item.
// rbase[region]: the region's first entry in `starts` (its rows are region-local);
// lbase[list]: the list's first entry in `lists`.
__global__ void fuBlocks(unsigned* __restrict__ items, const unsigned* __restrict__ counts,
                         const unsigned* __restrict__ jtab, const unsigned* __restrict__ gtab,
                         unsigned* __restrict__ starts, unsigned* __restrict__ lists,
                         unsigned* __restrict__ lcounts, const unsigned* __restrict__ lcap,
                         unsigned* __restrict__ flags, unsigned maxItems, unsigned bpi,
                         unsigned half, const unsigned* __restrict__ rbase,
                         const unsigned* __restrict__ lbase)
{
    const unsigned id = blockIdx.x * blockDim.x + threadIdx.x;
    const unsigned it = id / bpi, k = id - it * bpi;
    if (it >= min(counts[0], maxItems)) return;
    unsigned* o = items + it * IT;
    const unsigned j = o[0];
    const unsigned* jr = jtab + j * JT;
    const unsigned p = jr[2];                                   // partner job
    const unsigned* pr = jtab + p * JT;
    const long long S = (long long)pr[4];
    const long long poff = (long long)ld64(pr + 5);              // partner series offset
    const long long c0 = (long long)ld64(o + 2);
    const unsigned g = o[7];
    const unsigned* gr = gtab + g * GT;
    const long long n = gr[0], step = gr[1], cbad = gr[2];
    const unsigned region = gr[3], list = gr[4];
    long long v0 = c0 - (long long)half; if (v0 < 0) v0 = 0;
    long long v1 = c0 + (long long)half; if (v1 > S) v1 = S;
    long long first = (v0 - cbad) / step;                        // v0 >= 0 >= -cbad: floor ok
    if (v0 - cbad < 0) first = -1;                               // python floor of a negative
    if (first < 0) first = 0;
    const long long ts = (first + k) * step;
    if (ts >= S) return;
    const long long bvt0 = ts + cbad;
    if (!(bvt0 < v1 && bvt0 + step > v0)) return;
    const long long rs = bvt0 > v0 ? bvt0 : v0;
    const long long re = (bvt0 + step) < v1 ? (bvt0 + step) : v1;
    if (re <= rs) return;
    if (k + 1 == bpi && (first + k + 1) * step + cbad < v1) flags[0] = 1u;   // window too long
    if (ts + n > S) { flags[0] = 1u; return; }                   // needs the host's zero padding
    const unsigned row = o[8] * bpi + k;                         // region-local row
    starts[rbase[region] + row] = (unsigned)(poff + ts);
    const unsigned e = atomicAdd(&lcounts[list], 1u);
    if (e >= lcap[list]) { flags[0] = 1u; return; }
    unsigned* L = lists + (size_t)(lbase[list] + e) * 5u;
    L[0] = row; L[1] = o[6]; L[2] = (unsigned)(rs - ts); L[3] = (unsigned)(re - ts);
    L[4] = it * bpi + k;
    atomicMax(&o[9], k + 1);
}

}
