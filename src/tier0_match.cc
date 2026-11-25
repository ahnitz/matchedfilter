/* The matching of a level's vectors into pairs (_screeners.cluster_tier0_candidates).
 *
 * The vectors U (nodes, K) complex64 are taken a chunk at a time in the given order (alike
 * ones are neighbours in it), and in a chunk:
 *
 *   1. Every pair is scored (ap_tier0_pair_scores: its coherence at the best coarse shift,
 *      exact where it reaches the floor, only known to be below it elsewhere).
 *      With sizes, a pair whose two sizes sum to more than size_cap gets -1.
 *   2. Greedy: the candidates are, in a chunk of more than 9, each row's 8 largest scores
 *      that reach the floor, and in a smaller one every score that does; they are taken
 *      from the largest down (equal scores by row, then by column), a pair being kept when
 *      neither of its two is in a pair yet.
 *   3. Without sizes, when two or more are left over: a left-over u and a later left-over
 *      v are placed by breaking one kept pair (w, z) into (u, w), (v, z) or (u, z), (v, w)
 *      when both new pairs reach the floor; of the swaps open to u the one whose two scores
 *      sum highest (of equal sums the first v, u on w's side before z's, the first pair).
 *
 * What the chunks leave unpaired is matched once more, chunk by chunk, in the same way. A
 * pair is reported smaller index first, with the lag of the second against the first.
 *
 * This is the numpy code it replaced, with one difference: where a row held two equal
 * candidate scores, or more than eight no smaller than its eighth, numpy's order was that
 * of its partial sort; here it is the column's. */
#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include <algorithm>
#include <functional>
#include <vector>

extern "C" int ap_tier0_pair_scores(const float *ur, const float *ui, const float *sr,
                                    const float *si, const double *v, long long mc,
                                    long long len, long long nsh, float floor, float *r2,
                                    int32_t *bs);

namespace {

struct Cand { float r; int32_t a, b; };
struct Pair { int32_t a, b; };

struct Matcher {
  const float *U;            // (nodes, K) complex64
  const double *v;
  const float *sr, *si;      // (nsh, K) the coarse shifts
  const int64_t *shift_lags;
  const int32_t *sizes;      // or null
  long long K, nsh, size_cap;
  float floor;
  std::vector<float> ur, ui, r2, sym, row;
  std::vector<double> vc;
  std::vector<int32_t> bs;
  std::vector<Cand> cand;
  std::vector<Pair> pairs;
  std::vector<uint8_t> used, open;
  std::vector<int32_t> left;

  // 2. the greedy matching of the chunk's scored pairs
  void Greedy(long long mc) {
    cand.clear();
    for (long long a = 0; a < mc; a++) {
      const float *ra = r2.data() + a * mc;
      float least = floor;
      long long room = mc;
      if (mc > 9) {
        // the row's eighth largest score: a candidate is no smaller than it
        memcpy(row.data(), ra, (size_t)mc * sizeof(float));
        std::nth_element(row.begin(), row.begin() + 7, row.begin() + mc, std::greater<float>());
        if (row[7] >= floor) least = row[7];
        room = 8;
      }
      for (long long b = 0; b < mc && room > 0; b++)
        if (ra[b] >= least) {
          cand.push_back(Cand{ra[b], (int32_t)a, (int32_t)b});
          room--;
        }
    }
    std::stable_sort(cand.begin(), cand.end(),
                     [](const Cand &x, const Cand &y) { return x.r > y.r; });
    for (const Cand &c : cand) {
      if (used[c.a] || used[c.b]) continue;
      used[c.a] = used[c.b] = 1;
      pairs.push_back(c.a < c.b ? Pair{c.a, c.b} : Pair{c.b, c.a});
    }
  }

  // 3. left-over nodes placed by breaking a kept pair
  void Swaps(long long mc) {
    sym.resize((size_t)(mc * mc));
    for (long long a = 0; a < mc; a++)
      for (long long b = 0; b < mc; b++) sym[a * mc + b] = r2[a * mc + b] + r2[b * mc + a];
    left.clear();
    for (long long a = 0; a < mc; a++)
      if (!used[a]) left.push_back((int32_t)a);
    const long long nl = (long long)left.size(), np0 = (long long)pairs.size();
    // a left-over is tried if, with a later one, some kept pair could take the two
    open.assign((size_t)nl, 0);
    for (long long i = 0; i < nl; i++) {
      const float *si_ = sym.data() + (long long)left[i] * mc;
      for (long long j = i + 1; j < nl && !open[i]; j++) {
        const float *sj = sym.data() + (long long)left[j] * mc;
        for (long long e = 0; e < np0; e++) {
          const int32_t w = pairs[e].a, z = pairs[e].b;
          if ((si_[w] >= floor && sj[z] >= floor) || (si_[z] >= floor && sj[w] >= floor)) {
            open[i] = 1;
            break;
          }
        }
      }
    }
    for (long long i = 0; i < nl; i++) {
      const int32_t u = left[i];
      if (!open[i] || used[u]) continue;
      const float *su = sym.data() + (long long)u * mc;
      const long long np = (long long)pairs.size();
      bool any = false;
      for (long long e = 0; e < np && !any; e++)
        any = su[pairs[e].a] >= floor || su[pairs[e].b] >= floor;
      if (!any) continue;
      // per later left-over v: its best pair with u on w's side, then on z's; the first of
      // the largest over all
      float best = -HUGE_VALF;
      long long best_e = -1;
      int32_t best_v = -1;
      bool on_w = true;
      for (long long j = i + 1; j < nl; j++) {
        const int32_t vn = left[j];
        if (used[vn]) continue;
        const float *sv = sym.data() + (long long)vn * mc;
        float gw = -HUGE_VALF, gz = -HUGE_VALF;
        long long ew = 0, ez = 0;
        for (long long e = 0; e < np; e++) {
          const int32_t w = pairs[e].a, z = pairs[e].b;
          if (su[w] >= floor && sv[z] >= floor && su[w] + sv[z] > gw) { gw = su[w] + sv[z]; ew = e; }
          if (su[z] >= floor && sv[w] >= floor && su[z] + sv[w] > gz) { gz = su[z] + sv[w]; ez = e; }
        }
        if (gw > best) { best = gw; best_e = ew; best_v = vn; on_w = true; }
        if (gz > best) { best = gz; best_e = ez; best_v = vn; on_w = false; }
      }
      if (!(best > -1.0f)) continue;
      const int32_t mine = on_w ? pairs[best_e].a : pairs[best_e].b;
      const int32_t theirs = on_w ? pairs[best_e].b : pairs[best_e].a;
      used[u] = used[best_v] = 1;
      pairs[best_e] = u < mine ? Pair{u, mine} : Pair{mine, u};
      pairs.push_back(best_v < theirs ? Pair{best_v, theirs} : Pair{theirs, best_v});
    }
  }

  // one chunk: the pairs of nodes idx[0 .. mc) appended to (a, b, dl) at n; returns the new n
  long long Chunk(const int64_t *idx, long long mc, int32_t *a, int32_t *b, int64_t *dl,
                  long long n) {
    if (mc < 2) return n;
    ur.resize((size_t)(mc * K));
    ui.resize((size_t)(mc * K));
    vc.resize((size_t)mc);
    r2.resize((size_t)(mc * mc));
    bs.resize((size_t)(mc * mc));
    row.resize((size_t)mc);
    for (long long i = 0; i < mc; i++) {
      const float *u = U + 2 * idx[i] * K;
      for (long long k = 0; k < K; k++) {
        ur[i * K + k] = u[2 * k];
        ui[i * K + k] = u[2 * k + 1];
      }
      vc[i] = v[idx[i]];
    }
    if (ap_tier0_pair_scores(ur.data(), ui.data(), sr, si, vc.data(), mc, K, nsh, floor,
                             r2.data(), bs.data()) != 0)
      throw std::bad_alloc();
    if (sizes)
      for (long long i = 0; i < mc; i++)
        for (long long j = 0; j < mc; j++)
          if ((long long)sizes[idx[i]] + sizes[idx[j]] > size_cap) r2[i * mc + j] = -1.0f;
    used.assign((size_t)mc, 0);
    pairs.clear();
    Greedy(mc);
    if (pairs.empty()) return n;
    if (!sizes && mc - 2 * (long long)pairs.size() >= 2) Swaps(mc);
    for (const Pair &p : pairs) {
      const int64_t ta = idx[p.a], tb = idx[p.b], d = shift_lags[bs[(long long)p.a * mc + p.b]];
      a[n] = (int32_t)(ta < tb ? ta : tb);
      b[n] = (int32_t)(ta < tb ? tb : ta);
      dl[n] = ta < tb ? d : -d;
      n++;
    }
    return n;
  }
};

}  // namespace

/* order (count) the nodes to match, in the order they are chunked; U (nodes, K) complex64
   and v (nodes) their vectors and variances; sr, si (nsh, K) the coarse shifts in the order
   they are tried and shift_lags their lags; sizes (nodes) with size_cap, or null. a, b, dl
   (count / 2) get the pairs. Returns their number, or -1 when out of memory. */
extern "C" long long ap_tier0_match(
    const int64_t *order, long long count, long long nodes, const float *U, const double *v,
    const float *sr, const float *si, const int64_t *shift_lags, long long K, long long nsh,
    double floor, const int32_t *sizes, long long size_cap, long long chunk, int32_t *a,
    int32_t *b, int64_t *dl) try {
  Matcher m{U, v, sr, si, shift_lags, sizes, K, nsh, size_cap, (float)floor};
  std::vector<uint8_t> paired((size_t)nodes, 0);
  long long n = 0;
  for (long long c = 0; c < count; c += chunk)
    n = m.Chunk(order + c, std::min(chunk, count - c), a, b, dl, n);
  for (long long i = 0; i < n; i++) paired[a[i]] = paired[b[i]] = 1;
  // what the chunks left unpaired, matched once more
  std::vector<int64_t> rest;
  for (long long i = 0; i < count; i++)
    if (!paired[order[i]]) rest.push_back(order[i]);
  const long long nr = (long long)rest.size();
  if (nr >= 2)
    for (long long c = 0; c < nr; c += chunk)
      n = m.Chunk(rest.data() + c, std::min(chunk, nr - c), a, b, dl, n);
  return n;
} catch (const std::bad_alloc &) {
  return -1;
}

/* The pairs inside each cluster of a partition (_screeners.cluster_tier1_from_tier0): the
   valid members of cluster c, members[offsets[c] : offsets[c + 1]] where valid, are scored
   against each other (ap_tier0_pair_scores over U's rows, complex64 (nodes, K), variances
   v) and the pairs whose score reaches floor are taken from the largest down (equal scores
   in the order of their first member, then their second, as listed in the cluster), each
   member at most once. a, b, dl (room for the members' number / 2) get each pair's
   smaller template, its larger and the lag of the larger against the smaller. This is the
   numpy loop it replaced, its sort stable. Returns the number of pairs, or -1 when out of
   memory. */
extern "C" long long ap_tier0_pairs_within(
    const int32_t *offsets, long long nclusters, const int32_t *members, const uint8_t *valid,
    const float *U, const double *v, const float *sr, const float *si,
    const int64_t *shift_lags, long long K, long long nsh, double floor, int32_t *a,
    int32_t *b, int64_t *dl) try {
  // the float floor at or below floor: every score that reaches floor is exact
  float floor32 = (float)floor;
  if ((double)floor32 > floor) floor32 = nextafterf(floor32, -HUGE_VALF);
  std::vector<int32_t> grp, bs;
  std::vector<float> ur, ui, r2;
  std::vector<double> vg;
  std::vector<Cand> cand;
  std::vector<uint8_t> used;
  long long n = 0;
  for (long long c = 0; c < nclusters; c++) {
    grp.clear();
    for (int32_t p = offsets[c]; p < offsets[c + 1]; p++)
      if (valid[members[p]]) grp.push_back(members[p]);
    const long long m = (long long)grp.size();
    if (m < 2) continue;
    ur.resize((size_t)(m * K));
    ui.resize((size_t)(m * K));
    vg.resize((size_t)m);
    r2.resize((size_t)(m * m));
    bs.resize((size_t)(m * m));
    for (long long i = 0; i < m; i++) {
      const float *u = U + 2 * (long long)grp[i] * K;
      for (long long k = 0; k < K; k++) {
        ur[i * K + k] = u[2 * k];
        ui[i * K + k] = u[2 * k + 1];
      }
      vg[i] = v[grp[i]];
    }
    if (ap_tier0_pair_scores(ur.data(), ui.data(), sr, si, vg.data(), m, K, nsh, floor32,
                             r2.data(), bs.data()) != 0)
      throw std::bad_alloc();
    cand.clear();
    for (long long i = 0; i < m; i++)
      for (long long j = 0; j < m; j++)
        if ((double)r2[i * m + j] >= floor) cand.push_back(Cand{r2[i * m + j], (int32_t)i, (int32_t)j});
    std::stable_sort(cand.begin(), cand.end(),
                     [](const Cand &x, const Cand &y) { return x.r > y.r; });
    used.assign((size_t)m, 0);
    for (const Cand &e : cand) {
      if (used[e.a] || used[e.b]) continue;
      used[e.a] = used[e.b] = 1;
      const int32_t ta = grp[e.a], tb = grp[e.b];
      const int64_t d = shift_lags[bs[(long long)e.a * m + e.b]];
      a[n] = ta < tb ? ta : tb;
      b[n] = ta < tb ? tb : ta;
      dl[n] = ta < tb ? d : -d;
      n++;
    }
  }
  return n;
} catch (const std::bad_alloc &) {
  return -1;
}
