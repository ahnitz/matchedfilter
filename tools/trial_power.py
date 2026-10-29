#!/usr/bin/env python3
"""The paired rule's null, false-switch rate and power, from A/A rounds (MF_TRIAL_AA_LOG).

    python tools/trial_power.py NAME=LOG[,LOG...][@FIELD=V1|V2[&FIELD=V...]] [NAME=...] [--out TABLE.md]

Each NAME is a group of A/A logs (glob patterns allowed; .gz read as gzip), e.g.
``dev2-replay=runs/*.jsonl``, optionally only the records whose fields have the given values
(``rounds.jsonl.gz@machine=dev2&set=offs|full``: the checked-in evidence of
docs/trial-statistics.md).
A log holds, for every round of every paired trial a process ran, the preference's time and
the A/A arm's: the preference run a second time, settled and timed like a candidate and never
a sample (_choice.Choice.play). The A/A log ratio x = log(t_AA / t_preference) of a round is
then what an equal challenger's log ratio is under the machine's load and the job's own calls.

The report, per group and pooled:

  * the null: quantiles, standard deviation (and its robust estimate), the share of rounds an
    equal challenger wins under the current rule (ratio below 1 - TIE), its dependence on load
    and on the round's size, the order effect (the A/A arm runs last, then first), the
    correlation of successive rounds and the spread of contest means;
  * the current rule (_choice.paired_choice: TIE 5%, a 75% share, MINIMUM 5, CAP 10, exact
    elimination, confirmation): its false-switch rate for one and for m equal challengers,
    from the measured per-round win probabilities (exact, by DP, for independent rounds), and
    on the logged A/A sequences themselves (windows of 10 and 20 rounds of the long contests);
  * candidate rules, each a test of "the challenger is at least delta faster" over paired
    rounds, stopped at the first look that rejects and at the cap: an exact sign test with
    group-sequential boundaries (computed by DP for the cap: one nominal level at every look,
    the largest whose overall error is within alpha), and a paired t and a Wilcoxon
    signed-rank test on the log ratios with one threshold at every look (calibrated by
    simulation under the measured null); Holm across m arms (alpha / m for the first
    rejection, the only one a choice makes). For each: the false-switch rate at gain 0, the
    power at gains of 2, 5 and 10%, and the expected rounds, against the cap.

Rounds are taken as independent draws from the measured null unless a line says otherwise:
a process's first three contest rounds each from its own sample (they are noisier, and the
arm run last gains), later rounds and confirmations from the rounds with the A/A arm after
the preference or before it, as the order alternates (Null). The logged sequences test the
independence: the correlation of successive rounds, the spread of contest means (and the
rates with a contest effect of that size added), and the rules run on the sequences in their
order. A challenger with gain g has log ratio log(1 - g) + x: its noise is the A/A arm's.
Rates far below one over the number of logged rounds rest on the model's tails, not on
observation; the report gives both. The table for D8 (docs/trial-statistics.md) leads.
"""
import argparse
import glob
import gzip
import json
import math
import sys
from collections import defaultdict

import numpy as np

#: The current rule's parameters (_choice: TIE, the share in paired_choice, MINIMUM, CAP).
TIE, SHARE, MINIMUM, CAP = 0.05, 0.75, 5, 10
GAINS = (0.02, 0.05, 0.10)


# ---- the log ---------------------------------------------------------------------------------

def load(patterns, where=None):
    """(rounds, locks): every round and lock record in the files the patterns match (JSON
    lines, gzipped where the name ends in .gz), in file order, keeping the records for which
    where(record) holds. A pattern that matches nothing raises (a typo must not shrink the
    data). A record's own "_file" field, where it has one, names its process's log."""
    rounds, locks = [], []
    for pat in patterns:
        paths = sorted(glob.glob(pat))
        if not paths:
            raise FileNotFoundError("no A/A log matches %r" % pat)
        for p in paths:
            with (gzip.open(p, "rt") if p.endswith(".gz") else open(p)) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    rec.setdefault("_file", p)
                    if where is not None and not where(rec):
                        continue
                    if rec.get("event") == "round":
                        t, base = rec["times"], rec["times"][rec["preference"]]
                        if "ratios" not in rec:
                            rec["ratios"] = {a: v / base for a, v in t.items()}
                        if "aa_ratio" not in rec:
                            rec["aa_ratio"] = rec["A/A"] / base
                        rounds.append(rec)
                    else:
                        locks.append(rec)
    return rounds, locks


def log_ratios(rounds):
    """The A/A log ratio x = log(t_AA / t_preference) of each round."""
    return np.log(np.array([float(r["aa_ratio"]) for r in rounds], float))


def contests(rounds):
    """The rounds as contests: each a list of one process's rounds of one choice and phase
    (a confirmation is a contest of its own), in round order. A process's records are in
    the order it wrote them; a contest restarts where its round number does not grow."""
    by = defaultdict(list)
    for r in rounds:
        by[(r.get("_file"), r.get("host"), r.get("pid"), r.get("key"), r.get("what"))].append(r)
    out = []
    for seq in by.values():
        cur = []
        for r in seq:
            if cur and (r["phase"] != cur[-1]["phase"] or r["round"] <= cur[-1]["round"]):
                out.append(cur)
                cur = []
            cur.append(r)
        if cur:
            out.append(cur)
    return out


# ---- the null --------------------------------------------------------------------------------

def describe(x, tie=TIE):
    """Summary of a sample of log ratios: count, mean, median, sd, robust sd (1.4826 MAD),
    quantiles, P(x < log(1 - tie)) (an equal challenger's round win under the current rule),
    with its 95% Clopper-Pearson interval, and P(x < 0)."""
    x = np.asarray(x, float)
    n = int(x.size)
    if n == 0:
        return dict(n=0)
    k = int(np.count_nonzero(x < math.log(1 - tie)))
    q = np.quantile(x, [0.001, 0.01, 0.05, 0.5, 0.95, 0.99, 0.999]) if n > 1 else [x[0]] * 7
    return dict(n=n, mean=float(x.mean()), median=float(np.median(x)),
                sd=float(x.std(ddof=1)) if n > 1 else 0.0,
                rsd=float(1.4826 * np.median(np.abs(x - np.median(x)))),
                q=dict(zip(("0.1%", "1%", "5%", "50%", "95%", "99%", "99.9%"), map(float, q))),
                p_win=k / n, p_win_ci=clopper_pearson(k, n), wins=k,
                p_neg=float(np.mean(x < 0)))


def _binom_cdf(k, n, p):
    """P(X <= k) for X ~ Binomial(n, p), summed in log space (any n)."""
    if k < 0:
        return 0.0
    if k >= n or p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0
    lp, lq, ln = math.log(p), math.log1p(-p), math.lgamma(n + 1)
    return min(1.0, sum(math.exp(ln - math.lgamma(j + 1) - math.lgamma(n - j + 1) + j * lp + (n - j) * lq)
                        for j in range(k + 1)))


def clopper_pearson(k, n, level=0.95):
    """The exact two-sided binomial confidence interval (Clopper-Pearson) for k successes in
    n trials, by bisection on the binomial tails."""
    a = (1 - level) / 2

    def solve(f, target):       # the p where the decreasing f(p) crosses target
        lo, hi = 0.0, 1.0
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if f(mid) > target else (lo, mid)
        return 0.5 * (lo + hi)
    # lower end: P(X >= k) = a, i.e. P(X <= k - 1) = 1 - a; upper end: P(X <= k) = a
    lo = 0.0 if k == 0 else solve(lambda p: _binom_cdf(k - 1, n, p), 1 - a)
    hi = 1.0 if k == n else solve(lambda p: _binom_cdf(k, n, p), a)
    return (lo, hi)


def order_effect(rounds):
    """(mean x when the A/A arm ran after the preference, mean x when it ran before, counts).
    Where the preference shared another arm's run (they ran alike), that run is its."""
    after, before = [], []
    for r in rounds:
        o = r.get("order", [])
        pref = r.get("shared", {}).get(r.get("preference"), r.get("preference"))
        x = math.log(float(r["aa_ratio"]))
        if "A/A" in o and pref in o:
            (after if o.index("A/A") > o.index(pref) else before).append(x)
    m = lambda v: float(np.mean(v)) if v else float("nan")      # noqa: E731
    return m(after), m(before), len(after), len(before)


def arm_spread(cons):
    """{arm: (pooled within-contest sd of its log ratio, contests)} for the A/A arm and every
    candidate that ran on its own (not sharing another's run): whether real challengers see
    the noise the A/A arm does. Within a contest a candidate's true ratio is fixed, so its
    spread there is noise."""
    var = defaultdict(list)
    for c in cons:
        logs = defaultdict(list)
        for r in c:
            logs["A/A"].append(math.log(float(r["aa_ratio"])))
            for a, v in r["ratios"].items():
                if a != r["preference"] and a not in r.get("shared", {}):
                    logs[a].append(math.log(float(v)))
        for a, v in logs.items():
            if len(v) >= 2 and len(v) == len(c):
                var[a].append(float(np.var(v, ddof=1)))
    return {a: (math.sqrt(float(np.mean(v))), len(v)) for a, v in var.items()}


def serial(cons):
    """Within-contest structure of x: the lag-1 correlation of successive rounds, the variance
    of contest means against what independent rounds give (ratio 1 if none), and the sd of a
    contest effect that would explain the excess (tau: 0 when there is none)."""
    a, b, means, within, sizes = [], [], [], [], []
    for c in cons:
        x = np.log([float(r["aa_ratio"]) for r in c])
        if x.size >= 2:
            a.extend(x[:-1])
            b.extend(x[1:])
            means.append(x.mean())
            within.append(x.var(ddof=1))
            sizes.append(x.size)
    if len(a) < 3 or len(means) < 3:
        return dict(lag1=float("nan"), contests=len(means), mean_var_ratio=float("nan"), tau=0.0)
    lag1 = float(np.corrcoef(a, b)[0, 1])
    expect = float(np.mean(np.asarray(within) / np.asarray(sizes)))
    between = float(np.var(means, ddof=1))
    return dict(lag1=lag1, contests=len(means),
                mean_var_ratio=between / expect if expect > 0 else float("nan"),
                tau=math.sqrt(max(0.0, between - expect)))


def binned(x, z, edges):
    """Rows (lo, hi, n, sd, robust sd, P(win under the current rule)) of x binned by z."""
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (z >= lo) & (z < hi)
        if np.count_nonzero(sel) >= 5:
            d = describe(x[sel])
            rows.append((lo, hi, d["n"], d["sd"], d["rsd"], d["p_win"]))
    return rows


# ---- the current rule, exactly, for independent rounds ----------------------------------------

def _pn(p, n):
    """Round n's (1-based) win probability: p; or (odd rounds', even rounds') for a pair --
    the order reverses every round, so a challenger runs after the preference in odd rounds
    and before it in even ones (the first of a contest or of its confirmation is odd); or
    p(n) for a callable (Null.p: a process's first rounds have their own)."""
    if callable(p):
        return p(n)
    return p[(n - 1) % 2] if isinstance(p, (tuple, list)) else p


def current_dp(p, minimum=MINIMUM, cap=CAP, share=SHARE):
    """(P(switch), expected rounds) of one contest of _choice.paired_choice between the
    preference and one challenger that wins each round (ratio below 1 - tie) with probability
    p (or by round parity, _pn), independently: it switches when its wins reach
    ceil(share * n) at a round n >= minimum, the preference stands when its losses do or at
    the cap, and exact elimination (_choice.can_still_win) ends a contest the challenger can
    no longer win (which changes the rounds, not the switch probability)."""
    need_cap = math.ceil(share * cap)
    dist = {0: 1.0}
    switch = rounds = 0.0
    for n in range(1, cap + 1):
        nd = defaultdict(float)
        pn = _pn(p, n)
        for w, pr in dist.items():
            nd[w + 1] += pr * pn
            nd[w] += pr * (1 - pn)
        dist = {}
        for w, pr in nd.items():
            need = math.ceil(share * n)
            if n >= minimum and w >= need:
                switch += pr
                rounds += pr * n
            elif n >= minimum and (n - w) >= need:
                rounds += pr * n
            elif n == cap or w + (cap - n) < need_cap:
                rounds += pr * n
            else:
                dist[w] = pr
    return switch, rounds


def current_rate(p, m=1, confirm=True, minimum=MINIMUM, cap=CAP, p_confirm=None):
    """The current rule's false-switch rate per contest for m equal challengers, each winning a
    round with probability p (_pn), independently (an upper bound: challengers timed against
    one preference are positively correlated): a first contest that any of them wins, then,
    with confirmation, a fresh contest of that one alone, whose rounds win with p_confirm
    (default p: the confirmation runs later in the process)."""
    q, _ = current_dp(p, minimum, cap)
    first = 1.0 - (1.0 - q) ** m
    if not confirm:
        return first
    return first * current_dp(p if p_confirm is None else p_confirm, minimum, cap)[0]


def current_under(null, m=1, shift=0.0, cap=CAP, below=None):
    """(false switch or power with confirmation, rounds) of the current rule under a Null for
    m challengers whose log ratios are shift + x: the first contest from the process's first
    rounds on, the confirmation from later rounds (Null.later)."""
    below = math.log(1 - TIE) if below is None else below
    q1, rounds = current_dp(null.p(below, shift), MINIMUM, cap)
    q2 = current_dp(null.later().p(below, shift), MINIMUM, cap)[0]
    return (1.0 - (1.0 - q1) ** m) * q2, rounds


def with_contest_effect(rate, tau, nodes=41):
    """E[rate(u)] over a contest-level shift u ~ N(0, tau^2) of every round's log ratio (a
    contest whose rounds all lean one way: a load period, a bank the order favours), by
    Gauss-Hermite quadrature; rate(u) is a contest's rate with its rounds shifted by u. With
    the measured null already holding that spread, this counts it twice: an upper bound."""
    if tau <= 0:
        return rate(0.0)
    z, w = np.polynomial.hermite_e.hermegauss(nodes)
    return float(sum(wi * rate(tau * zi) for zi, wi in zip(z, w)) / math.sqrt(2 * math.pi))


# ---- an exact sign test with group-sequential boundaries ---------------------------------------

_TAILS = {}


def _tails(n):
    """[P(X >= k) for k = 0..n+1], X ~ Binomial(n, 1/2), exactly (cached)."""
    t = _TAILS.get(n)
    if t is None:
        c = [math.comb(n, j) for j in range(n + 1)]
        t = [sum(c[k:]) / 2.0 ** n for k in range(n + 1)] + [0.0]
        _TAILS[n] = t
    return t


def sign_crit(level, minimum, cap):
    """Critical win counts c_n (index n = 0..cap; None before minimum or where no count
    reaches the level): the smallest k with P(Binomial(n, 1/2) >= k) <= level."""
    out = [None] * (cap + 1)
    for n in range(minimum, cap + 1):
        t = _tails(n)
        out[n] = next((k for k in range(n + 1) if t[k] <= level), None)
    return out


def sign_dp(crit, p, cap):
    """(P(reject), expected rounds) of a sequential sign test with boundaries crit (from
    sign_crit) when each round is a win with probability p (or by round parity, _pn)
    independently: it rejects at the
    first n with wins >= crit[n], and stops when no later boundary can be reached (exact
    futility, which changes the rounds only) or at the cap."""
    reach = [None] * (cap + 2)          # reach[n]: least wins at round n from which some
    best = None                         # boundary at a round >= n can still be met
    for n in range(cap, 0, -1):
        cands = [crit[n]] if crit[n] is not None else []
        if best is not None:
            cands.append(best - 1)
        best = min(cands) if cands else None
        reach[n] = best
    dist = {0: 1.0}
    rej = rounds = 0.0
    if reach[1] is None:
        return 0.0, 0.0
    for n in range(1, cap + 1):
        nd = defaultdict(float)
        pn = _pn(p, n)
        for w, pr in dist.items():
            nd[w + 1] += pr * pn
            nd[w] += pr * (1 - pn)
        dist = {}
        for w, pr in nd.items():
            if crit[n] is not None and w >= crit[n]:
                rej += pr
                rounds += pr * n
            elif n == cap or reach[n + 1] is None or w + 1 < reach[n + 1]:
                rounds += pr * n
            else:
                dist[w] = pr
    return rej, rounds


def sign_boundary(alpha, minimum, cap):
    """The group-sequential sign test for the cap: one nominal level at every look from
    minimum to cap, the largest whose overall error under p = 1/2 (a challenger exactly at
    the boundary of the null) is within alpha, by DP. Returns (crit, overall alpha, nominal
    level); crit is all None when no test within alpha exists (too few rounds: a test at
    alpha needs ceil(log2(1/alpha)) straight wins)."""
    levels = sorted({t for n in range(minimum, cap + 1) for t in _tails(n)[1:n + 1]})
    lo, hi = -1, len(levels)            # levels[lo] within alpha (or none), levels[hi] not
    while hi - lo > 1:                  # the overall error grows with the level: bisect
        mid = (lo + hi) // 2
        if sign_dp(sign_crit(levels[mid], minimum, cap), 0.5, cap)[0] <= alpha * (1 + 1e-12):
            lo = mid
        else:
            hi = mid
    if lo < 0:
        return [None] * (cap + 1), 0.0, 0.0
    crit = sign_crit(levels[lo], minimum, cap)
    return crit, sign_dp(crit, 0.5, cap)[0], levels[lo]


def naive_sign_alpha(alpha, minimum, cap):
    """The overall error of the fixed-n exact sign test at alpha applied at every round from
    minimum to cap (the inflation group-sequential boundaries remove)."""
    return sign_dp(sign_crit(alpha, minimum, cap), 0.5, cap)[0]


# ---- statistics on log ratios, by simulation --------------------------------------------------

def _wilcoxon_z(y):
    """Standardised signed-rank statistic of each row's prefixes: z[:, n-1] for the first n
    rounds, positive when the rounds favour the challenger (y > 0). Built round by round: a
    new round's rank is one more than the earlier rounds smaller in size, and each earlier
    positive round larger in size gains one."""
    N, L = y.shape
    a = np.abs(y)
    pos = y > 0
    wplus = np.zeros(N)
    z = np.empty((N, L))
    for n in range(1, L + 1):
        new = a[:, n - 1:n]
        if n > 1:
            smaller = (a[:, :n - 1] < new).sum(axis=1)
            larger_pos = ((a[:, :n - 1] > new) & pos[:, :n - 1]).sum(axis=1)
        else:
            smaller = larger_pos = np.zeros(N)
        wplus += np.where(pos[:, n - 1], smaller + 1, 0) + larger_pos
        mu, var = n * (n + 1) / 4.0, n * (n + 1) * (2 * n + 1) / 24.0
        z[:, n - 1] = (wplus - mu) / math.sqrt(var)
    return z


def _t_stat(y):
    """Paired t statistic of each row's prefixes, positive when y > 0 on average (-inf for
    the first round, which has no spread)."""
    N, L = y.shape
    n = np.arange(1, L + 1, dtype=float)
    mean = np.cumsum(y, axis=1) / n
    ss = np.cumsum(y * y, axis=1) - n * mean ** 2
    var = np.maximum(ss, 0) / np.maximum(n - 1, 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = mean / np.sqrt(var / n)
    t[:, 0] = -np.inf
    return np.nan_to_num(t, nan=-np.inf)


STATS = {"t": _t_stat, "wilcoxon": _wilcoxon_z}


def _marginal_p(stat, ref, minimum):
    """Each look's null p-value of each row's statistic: the share of the null rows (ref,
    each look's sorted null statistics) at or above it."""
    N, L = stat.shape
    p = np.ones((N, L))
    for n in range(minimum - 1, L):
        r = ref[n]
        p[:, n] = (r.size - np.searchsorted(r, stat[:, n], side="left")) / r.size
    return p


def calibrate(stat_name, null, alpha, minimum):
    """A sequential test of one nominal level at every look from minimum: the looks' null
    distributions (sorted, from the simulated null contests `null`) and the largest level at
    which at most alpha of the null contests reject at some look. Returns (ref, level)."""
    s = STATS[stat_name](null)
    ref = [np.sort(s[:, n]) for n in range(s.shape[1])]
    minp = _marginal_p(s, ref, minimum)[:, minimum - 1:].min(axis=1)
    level = float(np.quantile(minp, alpha, method="lower"))
    if np.mean(minp <= level) > alpha:  # discrete statistics: step below the tie
        below = minp[minp < level]
        level = float(below.max()) if below.size else 0.0
    return ref, level


def simulate(stat_name, draws, test, minimum):
    """(P(reject), expected rounds) of a calibrated sequential test (calibrate) on draws: it
    rejects at the first look whose null p-value is at most the level, else runs to the cap."""
    ref, level = test
    p = _marginal_p(STATS[stat_name](draws), ref, minimum)[:, minimum - 1:]
    hit = p <= level
    crossed = hit.any(axis=1)
    first = np.where(crossed, hit.argmax(axis=1) + minimum, draws.shape[1])
    return float(crossed.mean()), float(first.mean())


# ---- the null by position, as a model ----------------------------------------------------------

class Null:
    """A group's measured null of a round's A/A log ratio x. A process's first EARLY rounds of
    a contest are its first timed runs, and each has its own sample (the contest rounds of
    that number, where at least 20 were logged); later rounds and confirmations are split by
    where the A/A arm ran -- after the preference (the order of the candidates: odd rounds)
    or before it (reversed: even rounds) -- since a challenger alternates the same way (the
    pooled later rounds where either side has fewer than 20). p() and draws() give round n
    its sample; later() is the null of a contest that starts later in the process (a
    confirmation)."""

    EARLY = 3

    def __init__(self, rounds, early=True):
        self.x = log_ratios(rounds)
        after, before, first = [], [], defaultdict(list)
        for r in rounds:
            x = math.log(float(r["aa_ratio"]))
            if early and r.get("phase") == "contest" and int(r["round"]) <= self.EARLY:
                first[int(r["round"])].append(x)
                continue
            o = r.get("order", [])
            pref = r.get("shared", {}).get(r.get("preference"), r.get("preference"))
            if "A/A" in o and pref in o:
                (after if o.index("A/A") > o.index(pref) else before).append(x)
        self.after, self.before = np.asarray(after), np.asarray(before)
        if min(self.after.size, self.before.size) < 20:
            late = np.concatenate([self.after, self.before])
            self.after = self.before = late if late.size >= 20 else self.x
        self.first = {n: np.asarray(v) for n, v in first.items() if len(v) >= 20}
        self._rounds = rounds

    def later(self):
        """The null of a contest that starts after the process's first rounds."""
        if getattr(self, "_later", None) is None:
            self._later = self if not self.first else Null(self._rounds, early=False)
        return self._later

    def _sample(self, n):
        return self.first.get(n, self.after if n % 2 else self.before)

    def p(self, below, shift=0.0):
        """Round n -> P(shift + x < below), x from round n's sample (a callable for _pn)."""
        cache = {}

        def pn(n):
            key = n if n in self.first else ("odd" if n % 2 else "even")
            if key not in cache:
                cache[key] = float(np.mean(self._sample(n) + shift < below))
            return cache[key]
        return pn

    def draws(self, rng, nsim, cap, shift=0.0):
        """nsim contests of cap rounds of shift + x, round n from its sample."""
        out = np.empty((nsim, cap))
        for n in range(1, cap + 1):
            out[:, n - 1] = rng.choice(self._sample(n), size=nsim)
        return out + shift


# ---- the report ------------------------------------------------------------------------------

def _f(v, digits=3):
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "-"
    if isinstance(v, float) and (abs(v) < 1e-3 and v != 0):
        return "%.1e" % v
    return ("%%.%dg" % digits) % v


def _rate(v):
    return "<1e-12" if v < 1e-12 else "%.2g" % v


def _challengers(rounds):
    """The most common number of distinct challengers in a round (the runs less the
    preference's and the A/A arm's)."""
    n = [max(1, len(r.get("order", [])) - 2) for r in rounds]
    return int(np.bincount(n).argmax()) if n else 1


def null_section(name, rounds, null, out):
    d = describe(null.x)
    cons = contests(rounds)
    ser = serial(cons)
    after, before, na, nb = order_effect(rounds)
    loads = np.array([float(r["load"][0]) for r in rounds])
    tp = np.array([float(r["times"][r["preference"]]) for r in rounds])
    hosts = sorted({r.get("host", "?").split(".")[0] for r in rounds})
    out.append("### %s: %d rounds, %d contests (%s)" % (name, d["n"], ser["contests"], ", ".join(hosts)))
    out.append("")
    out.append("| sd | robust sd | mean | 0.1% | 1% | 5% | 95% | 99% | 99.9% | P(x < log 0.95) [95% CI] | P(x < 0) |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|")
    q = d["q"]
    out.append("| %.4f | %.4f | %+.4f | %+.3f | %+.3f | %+.3f | %+.3f | %+.3f | %+.3f | %s (%d) [%s, %s] | %.3f |" % (
        d["sd"], d["rsd"], d["mean"], q["0.1%"], q["1%"], q["5%"], q["95%"], q["99%"], q["99.9%"],
        _f(d["p_win"]), d["wins"], _f(d["p_win_ci"][0]), _f(d["p_win_ci"][1]), d["p_neg"]))
    out.append("")
    spread = arm_spread(cons)
    out.append("- Load (1-min) %.1f-%.1f, median %.1f; the preference's time per round %s-%s s, median %s." % (
        loads.min(), loads.max(), float(np.median(loads)), _f(float(tp.min())), _f(float(tp.max())),
        _f(float(np.median(tp)))))
    out.append("- Order: mean x %+.4f with the A/A arm after the preference (%d rounds), %+.4f before it (%d)." % (
        after, na, before, nb))
    out.append("- Successive rounds: lag-1 correlation %.3f; contest means vary %.2fx what independent "
               "rounds give (%d contests): a contest effect of sd %.4f." % (
                   ser["lag1"], ser["mean_var_ratio"], ser["contests"], ser["tau"]))
    out.append("- Within-contest sd of the log ratio, by arm (real challengers against the A/A arm): " + ", ".join(
        "%s %.4f (%d)" % (a, v, k) for a, (v, k) in sorted(spread.items(), key=lambda kv: -kv[1][1])[:5]) + ".")
    out.append("- Distinct challengers per round (most common): %d." % _challengers(rounds))
    out.append("")


def dependence_section(rounds, out):
    x = log_ratios(rounds)
    load = np.array([float(r["load"][0]) for r in rounds])
    tp = np.array([float(r["times"][r["preference"]]) for r in rounds])
    runs = np.array([len(r["order"]) for r in rounds])
    idx = np.array([int(r["round"]) for r in rounds])
    q = lambda z: np.quantile(z, np.linspace(0, 1, 6)) * np.array([1, 1, 1, 1, 1, 1 + 1e-9])   # noqa: E731
    out.append("| by | bin [lo, hi) | rounds | sd | robust sd | P(x < log 0.95) |")
    out.append("|---|---|---|---|---|---|")
    for lab, z, edges in (("load (1-min)", load, q(load)), ("preference's time (s)", tp, q(tp)),
                          ("timed runs in the round", runs, np.array([0, 2.5, 3.5, 4.5, 99])),
                          ("round of the contest", idx, np.array([1, 2, 4, 6, 11, 21, 1000]))):
        for lo, hi, n, sd, rsd, pw in binned(x, z, edges):
            out.append("| %s | %s-%s | %d | %.4f | %.4f | %s |" % (lab, _f(lo), _f(hi), n, sd, rsd, _f(pw)))
    out.append("")


def current_rows(name, null, m, tau=0.0):
    """The current rule's measured false-switch rate in a group: per-round win probability
    (pooled, with its interval; rounds 1-3 and later odd / even rounds), one contest, with
    confirmation for 1 and m equal challengers, at the interval's upper end (every round's
    probability raised by the interval's excess), and with a contest effect of sd tau."""
    d = describe(null.x)
    below = math.log(1 - TIE)
    pp = null.p(below)
    up = d["p_win_ci"][1] - d["p_win"]

    def raised(nl):
        f = nl.p(below)
        return lambda n: min(1.0, f(n) + up)
    q_hi1 = current_dp(raised(null))[0]
    q_hi2 = current_dp(raised(null.later()))[0]
    return dict(name=name, p=d["p_win"], ci=d["p_win_ci"], m=m, tau=tau,
                per_round=[pp(n) for n in (1, 2, 3, 11, 12)],
                contest=current_dp(pp)[0], one=current_under(null, 1)[0], many=current_under(null, m)[0],
                many_hi=(1 - (1 - q_hi1) ** m) * q_hi2,
                many_tau=with_contest_effect(lambda u: current_under(null, m, -u)[0], tau),
                rounds=current_dp(pp)[1])


def windows(cons, cap):
    """Consecutive non-overlapping windows of cap A/A log ratios from every contest at least
    that long, each starting at an odd round (the order's parity kept), in round order."""
    out = []
    for c in cons:
        x = np.log([float(r["aa_ratio"]) for r in c])
        for i in range(0, x.size - cap + 1, cap):
            out.append(x[i:i + cap])
    return out


def run_current(seq, tie=TIE, minimum=MINIMUM, share=SHARE):
    """The current rule on one challenger's log ratios in order (one contest, no
    confirmation): whether it switches."""
    w = 0
    for n, y in enumerate(seq, 1):
        w += y < math.log(1 - tie)
        need = math.ceil(share * n)
        if n >= minimum and w >= need:
            return True
        if n >= minimum and n - w >= need:
            return False
    return False


def run_sign(seq, crit, delta=0.0):
    """The sequential sign test (boundaries crit) on log ratios in order: whether it rejects."""
    w = 0
    for n, y in enumerate(seq, 1):
        w += y < math.log(1 - delta)
        if crit[n] is not None and w >= crit[n]:
            return True
    return False


def empirical_rows(cons, alphas):
    """Rules run on the logged A/A sequences in their order: (rule, windows, switches) for
    windows of 10 and of 20 rounds."""
    rows = []
    for cap in (10, 20):
        ws = windows(cons, cap)
        rules = [("current rule, one contest (no confirmation)", lambda s: run_current(s))]
        for delta in (0.0, 0.02):
            for a in alphas:
                crit = sign_boundary(a, MINIMUM, cap)[0]
                rules.append(("sign test, delta %g, alpha %g" % (delta, a),
                              lambda s, crit=crit, d=delta: run_sign(s, crit, d)))
        for lab, f in rules:
            rows.append((cap, lab, len(ws), sum(bool(f(w)) for w in ws)))
    return rows


def sign_rows(null, alphas, deltas, caps, m):
    """The exact group-sequential sign test under a group's null: per (delta, alpha, cap) the
    test's overall error at its null boundary, its nominal level, the false-switch rate at
    gain 0 for one challenger and for m with Holm (alpha / m per arm), power at GAINS (one
    challenger at alpha / m beside m - 1 equal ones), and expected rounds."""
    rows = []
    for delta in deltas:
        for a in alphas:
            for cap in caps:
                crit, ach, lv = sign_boundary(a, MINIMUM, cap)
                critm, _, _ = sign_boundary(a / m, MINIMUM, cap)
                row = dict(delta=delta, alpha=a, cap=cap, achieved=ach, level=lv,
                           exists=any(c is not None for c in crit),
                           exists_m=any(c is not None for c in critm))
                below = math.log(1 - delta)
                if row["exists"]:
                    row["fs1"], row["rounds0"] = sign_dp(crit, null.p(below), cap)
                if row["exists_m"]:
                    q = sign_dp(critm, null.p(below), cap)[0]
                    row["fsm"] = 1 - (1 - q) ** m
                    row["power"] = [sign_dp(critm, null.p(below, math.log(1 - g)), cap)[0] for g in GAINS]
                    row["rounds5"] = sign_dp(critm, null.p(below, math.log(0.95)), cap)[1]
                rows.append(row)
    return rows


def current_power_rows(null, caps, m):
    """The current rule against the cap: false-switch rate (confirmation) for 1 and m equal
    challengers, power at GAINS (with confirmation), expected rounds."""
    rows = []
    below = math.log(1 - TIE)
    for cap in caps:
        q0, asn0 = current_dp(null.p(below), MINIMUM, cap)
        rows.append(dict(cap=cap, fs1=current_under(null, 1, cap=cap)[0], fsm=current_under(null, m, cap=cap)[0],
                         power=[current_under(null, 1, math.log(1 - g), cap)[0] for g in GAINS], rounds0=asn0,
                         rounds10=current_dp(null.p(below, math.log(0.9)), MINIMUM, cap)[1]))
    return rows


def stat_rows(null, alphas, deltas, caps, m, nsim, rng):
    """The paired t and Wilcoxon tests, by simulation from a group's null: a challenger of gain
    g has log ratio log(1 - g) + x, and a test of "at least delta faster" sees
    y = log(1 - delta) - log ratio, so its null boundary (g = delta) is y = -x. Calibrated at
    alpha / m per arm (Holm); false-switch rate for m equal challengers, power for one."""
    rows = []
    for name in ("t", "wilcoxon"):
        for delta in deltas:
            for a in alphas:
                if a / m * nsim < 50:
                    continue                    # too few null contests past the level
                for cap in caps:
                    def draws(g):
                        return math.log(1 - delta) - null.draws(rng, nsim, cap, math.log(1 - g))
                    test = calibrate(name, draws(delta), a / m, MINIMUM)
                    q, asn0 = simulate(name, draws(0.0), test, MINIMUM)
                    rows.append(dict(test=name, delta=delta, alpha=a, cap=cap, level=test[1],
                                     fsm=1 - (1 - q) ** m, rounds0=asn0,
                                     power=[simulate(name, draws(g), test, MINIMUM)[0] for g in GAINS]))
    return rows


def d8_rows(nulls, cur, deltas, alphas, caps):
    """Exact sign tests (Holm over each group's m) against the current rule under every group's
    null. Per (delta, alpha, cap) and group: the false-switch rate at gain 0 for m equal
    challengers, the current rule's (confirmed), whether the test's is no larger, the same
    with a contest effect of the group's measured sd (tau) added to both, power at GAINS, and
    the expected rounds at gain 0 and at 5%."""
    rows = []
    for delta in deltas:
        for a in alphas:
            for cap in caps:
                row = dict(delta=delta, alpha=a, cap=cap, groups={})
                for name, rounds, null in nulls:
                    m, tau = cur[name]["m"], cur[name]["tau"]
                    crit = sign_boundary(a / m, MINIMUM, cap)[0]
                    if all(c is None for c in crit):
                        row["groups"][name] = None
                        continue
                    below = math.log(1 - delta)

                    def fs(u, crit=crit, null=null, m=m, below=below):
                        return 1 - (1 - sign_dp(crit, null.p(below - u), cap)[0]) ** m

                    def fs_cur(u, null=null, m=m):
                        return current_under(null, m, -u)[0]
                    row["groups"][name] = dict(
                        fs=fs(0.0), cur=cur[name]["many"], rounds_lost=sign_dp(crit, 0.0, cap)[1],
                        fs_tau=with_contest_effect(fs, tau), cur_tau=with_contest_effect(fs_cur, tau),
                        power=[sign_dp(crit, null.p(below, math.log(1 - g)), cap)[0] for g in GAINS],
                        rounds0=sign_dp(crit, null.p(below), cap)[1],
                        rounds5=sign_dp(crit, null.p(below, math.log(0.95)), cap)[1])
                rows.append(row)
    return rows


def round_cost(rounds):
    """The mean overhead of a round in seconds: each configuration that ran is settled and
    timed (twice its time), less the preference's timed run, which is the call's own work;
    the A/A arm is not counted."""
    cost = []
    for r in rounds:
        t = r["times"]
        owner = r.get("shared", {})
        ran = {a: v for a, v in t.items() if a not in owner}
        cost.append(2 * sum(ran.values()) - t[r["preference"]])
    return float(np.mean(cost)) if cost else float("nan")


#: Power within this of the current rule's counts as kept (the table prints three decimals).
KEPT = 0.002


def keeps_power(groups, cp):
    """Whether a rule's power at every gain of 5% or more is at least the current rule's, to
    within KEPT, under every group's null (groups: d8_rows' per-group results; cp: the
    current rule's powers per group)."""
    return all(v["power"][i] >= cp[n][0][i] - KEPT for n, v in groups.items()
               for i, g in enumerate(GAINS) if g >= 0.05)


def d8_section(nulls, cur, out, caps, compare=()):
    """The table D8 asks for: which exact sign tests are no looser than the current rule's
    measured false-switch rate, under every group's null and under the worst group's, whether
    they keep the current rule's power, and their power and rounds; the current rule first,
    for reference. Then, per group, the current rule against the rules in `compare`
    ((delta, alpha, cap) triples)."""
    names = [n for n, _, _ in nulls]
    deltas = (0.0, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05)
    alphas = (0.05, 0.02, 0.01, 5e-3, 3e-3, 2e-3, 1e-3, 1e-4)
    rows = d8_rows(nulls, cur, deltas, alphas, caps)
    worst_cur = max(cur[n]["many"] for n in names)
    out += ["## Candidate rules against D8 (no looser than the current measured false-switch rate)", "",
            "False-switch rates are per contest at gain 0 for each group's m equal challengers (Holm: "
            "alpha / m per arm; the current rule with its confirmation). \"Every group\": the test's rate "
            "is no larger than the current rule's under each group's null; \"worst\": its largest rate "
            "is no larger than the current rule's largest (%s); \"keeps power\": its power at 5%% and 10%% "
            "is at least the current rule's under every group's null (to within %g). Listed: every rule "
            "that meets \"every group\", and those that meet \"worst\" and keep the power (the per-group "
            "rates of all are below). Power for one challenger of the gain, "
            "worst group / best group; rounds: the largest expected count at gain 0 and at 5%%, and the "
            "rounds a challenger that loses every round runs (the usual case: on most banks the CPU's challengers are "
            "1.1-2.2x slower), which with each group's cost of a round (below) is the trial's overhead."
            % (_rate(worst_cur), KEPT), "",
            "| rule | every group | worst | keeps power | %s | rounds at 0 / 5%% | rounds, all lost |"
            % _gains_head().replace("power", "power (worst / best)"),
            "|---|---|---|---|" + "---|" * len(GAINS) + "---|---|"]
    cp = {}
    for name, _, null in nulls:
        below = math.log(1 - TIE)
        cp[name] = ([current_under(null, 1, math.log(1 - g))[0] for g in GAINS],
                    current_dp(null.p(below))[1], current_dp(null.p(below, math.log(0.95)))[1])
    out.append("| current (TIE 5%%, 75%%, 5/10, confirm) | (reference) | (reference) | (reference) | %s | %.1f / %.1f | %.0f |" % (
        " | ".join("%.3f / %.3f" % (min(cp[n][0][i] for n in names), max(cp[n][0][i] for n in names))
                   for i in range(len(GAINS))),
        max(cp[n][1] for n in names), max(cp[n][2] for n in names), current_dp(0.0)[1]))
    for r in rows:
        g = r["groups"]
        if any(v is None for v in g.values()):
            continue
        every = all(v["fs"] <= v["cur"] for v in g.values())
        worst = max(v["fs"] for v in g.values()) <= worst_cur
        kept = keeps_power(g, cp)
        if not (every or (worst and kept)):
            continue
        out.append("| sign, delta %g, alpha %g, cap %d | %s | %s | %s | %s | %.1f / %.1f | %.0f |" % (
            r["delta"], r["alpha"], r["cap"], "yes" if every else "no", "yes" if worst else "no",
            "yes" if kept else "no",
            " | ".join("%.3f / %.3f" % (min(v["power"][i] for v in g.values()), max(v["power"][i] for v in g.values()))
                       for i in range(len(GAINS))),
            max(v["rounds0"] for v in g.values()), max(v["rounds5"] for v in g.values()),
            max(v["rounds_lost"] for v in g.values())))
    out += ["", "The cost of a round, per group: the mean over its rounds of every run but the preference's "
            "timed one (each configuration is settled and timed: twice its time; the A/A arm, a "
            "diagnostic, left out): " + "; ".join("%s %s s" % (n, _f(round_cost(rounds))) for n, rounds, _ in nulls) + "."]
    out += ["", "Per group, for every candidate that exists at alpha / m within its cap (false-switch rate, "
            "the current rule's, and both with the group's contest effect added):", "",
            "| rule | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    for r in rows:
        g = r["groups"]
        if any(v is None for v in g.values()):
            continue
        out.append("| delta %g, alpha %g, cap %d | %s |" % (r["delta"], r["alpha"], r["cap"], " | ".join(
            "%s vs %s (%s vs %s)" % (_rate(g[n]["fs"]), _rate(g[n]["cur"]), _rate(g[n]["fs_tau"]), _rate(g[n]["cur_tau"]))
            for n in names)))
    out.append("")
    if compare:
        have = {(r["delta"], r["alpha"], r["cap"]): r for r in rows}
        chosen = []
        for d, a, c in compare:
            key = (float(d), float(a), int(c))
            r = have.get(key) or d8_rows(nulls, cur, key[:1], key[1:2], key[2:])[0]
            if all(v is not None for v in r["groups"].values()):
                chosen.append(r)
        out += ["Per group, the current rule against %s: the false-switch rate at gain 0 (m equal "
                "challengers), and the power at 5%% and 10%%:" % ", ".join(
                    "delta %g, alpha %g, cap %d" % (r["delta"], r["alpha"], r["cap"]) for r in chosen), "",
                "| group | current: rate | 5% | 10% | " + " | ".join(
                    "d %g a %g c %d: rate | 5%% | 10%%" % (r["delta"], r["alpha"], r["cap"]) for r in chosen) + " |",
                "|---|---|---|---|" + "---|---|---|" * len(chosen)]
        i5, i10 = GAINS.index(0.05), GAINS.index(0.10)
        for n in names:
            out.append("| %s | %s | %.3f | %.3f | %s |" % (
                n, _rate(cur[n]["many"]), cp[n][0][i5], cp[n][0][i10], " | ".join(
                    "%s | %.3f | %.3f" % (_rate(r["groups"][n]["fs"]), r["groups"][n]["power"][i5],
                                          r["groups"][n]["power"][i10]) for r in chosen)))
        out.append("")
    return rows


def _gains_head():
    return " | ".join("power %d%%" % round(100 * g) for g in GAINS)


def report(groups, alphas, caps, nsim, seed, compare=()):
    """The Markdown report of named groups of rounds ([(name, rounds)])."""
    rng = np.random.default_rng(seed)
    out = ["# A/A rounds of paired trials: the null, the current rule, candidate rules", "",
           "x = log(t_AA / t_preference) per round: an equal challenger's log ratio. Rates are per "
           "contest, for independent rounds drawn from the measured null round by round (a process's "
           "first three contest rounds each from its own sample, later rounds and confirmations by "
           "the order's parity: Null), unless a line says otherwise; m equal challengers are taken "
           "as independent (an upper bound). Powers are for one challenger of the stated gain, its "
           "noise the A/A arm's.", ""]
    nulls = [(name, rounds, Null(rounds)) for name, rounds in groups]
    cur = {name: current_rows(name, null, _challengers(rounds), serial(contests(rounds))["tau"])
           for name, rounds, null in nulls}
    d8_section(nulls, cur, out, caps, compare)
    out += ["## The null", ""]
    for name, rounds, null in nulls:
        null_section(name, rounds, null, out)
    out += ["## Dependence on load, work and place in the contest", ""]
    for name, rounds, _ in nulls:
        out += ["### %s" % name, ""]
        dependence_section(rounds, out)
    out += ["## The current rule's false-switch rate (TIE 5%, 75% share, minimum 5, cap 10)", "",
            "| group | P(round win) [95% CI] | rounds 1 / 2 / 3, later odd / even | contest, m=1 | confirmed, m=1 "
            "| confirmed, m | m | confirmed, m, at the CI's upper end | with the contest effect (tau) "
            "| rounds (equal arms) |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for name, rounds, null in nulls:
        r = cur[name]
        out.append("| %s | %s [%s, %s] | %s | %s | %s | %s | %d | %s | %s (%.3f) | %.2f |" % (
            name, _f(r["p"]), _f(r["ci"][0]), _f(r["ci"][1]), " / ".join("%.3f" % v for v in r["per_round"]),
            _rate(r["contest"]), _rate(r["one"]), _rate(r["many"]), r["m"], _rate(r["many_hi"]),
            _rate(r["many_tau"]), r["tau"], r["rounds"]))
    out += ["", "On the logged A/A sequences in their order (contests of at least 10 or 20 rounds, cut "
            "into windows):", "", "| group | window | rule | windows | switches |", "|---|---|---|---|---|"]
    for name, rounds, _ in nulls:
        for cap, lab, nw, ns in empirical_rows(contests(rounds), (1e-2, 1e-3)):
            if nw:
                out.append("| %s | %d | %s | %d | %d |" % (name, cap, lab, nw, ns))
    out.append("")
    for name, rounds, null in nulls:
        m = cur[name]["m"]
        out += ["## Rules under the %s null (%d rounds; m = %d)" % (name, null.x.size, m), "",
                "Current rule against the cap (minimum %d; with its confirmation, a second contest on later "
                "rounds):" % MINIMUM, "",
                "| cap | false switch, m=1 | false switch, m=%d | %s | rounds at gain 0 | rounds at 10%% |" % (m, _gains_head()),
                "|---|---|---|" + "---|" * len(GAINS) + "---|---|"]
        for r in current_power_rows(null, caps, m):
            out.append("| %d | %s | %s | %s | %.1f | %.1f |" % (
                r["cap"], _rate(r["fs1"]), _rate(r["fsm"]), " | ".join("%.3f" % v for v in r["power"]),
                r["rounds0"], r["rounds10"]))
        out += ["", "Exact sign test of \"at least delta faster\", group-sequential (one nominal level at "
                "every look from round %d, the largest within alpha, by DP for the cap); Holm over m arms "
                "(alpha / m per arm); power for one gaining arm at alpha / m:" % MINIMUM, "",
                "| delta | alpha | cap | overall alpha | nominal level | false switch, m=1 | false switch, m=%d "
                "| %s | rounds at gain 0 | rounds at 5%% |" % (m, _gains_head()),
                "|---|---|---|---|---|---|---|" + "---|" * len(GAINS) + "---|---|"]
        for r in sign_rows(null, alphas, (0.0, 0.02, 0.05), caps, m):
            if not r["exists"]:
                out.append("| %g | %g | %d | no test within alpha in %d rounds |%s" % (
                    r["delta"], r["alpha"], r["cap"], r["cap"], " |" * (5 + len(GAINS))))
                continue
            tail = (" | ".join("%.3f" % v for v in r["power"]) + " | %.1f | %.1f" % (r["rounds0"], r["rounds5"])
                    if r["exists_m"] else " | ".join(["-"] * len(GAINS)) + " | %.1f | -" % r["rounds0"])
            out.append("| %g | %g | %d | %s | %s | %s | %s | %s |" % (
                r["delta"], r["alpha"], r["cap"], _rate(r["achieved"]), _f(r["level"]), _rate(r["fs1"]),
                _rate(r["fsm"]) if r["exists_m"] else "no test at alpha/m", tail))
        out += ["", "Paired t and Wilcoxon signed-rank on log ratios (one nominal level at every look from "
                "round %d, calibrated at alpha / m on %d simulated null contests):" % (MINIMUM, nsim), "",
                "| test | delta | alpha | cap | nominal level | false switch, m=%d | %s | rounds at gain 0 |" % (
                    m, _gains_head()),
                "|---|---|---|---|---|---|" + "---|" * len(GAINS) + "---|"]
        for r in stat_rows(null, [a for a in alphas if a >= 1e-3], (0.0, 0.02), caps, m, nsim, rng):
            out.append("| %s | %g | %g | %d | %s | %s | %s | %.1f |" % (
                r["test"], r["delta"], r["alpha"], r["cap"], _f(r["level"]), _rate(r["fsm"]),
                " | ".join("%.3f" % v for v in r["power"]), r["rounds0"]))
        out.append("")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("groups", nargs="+",
                    help="NAME=PATTERN[,PATTERN...][@FIELD=V1|V2[&FIELD=...]] (records whose fields "
                         "have one of the values)")
    ap.add_argument("--out", help="write the Markdown report here (default: stdout)")
    ap.add_argument("--alphas", default="1e-2,1e-3,1e-4", help="error rates for the candidate rules")
    ap.add_argument("--caps", default="10,20,30,40", help="caps of rounds for the candidate rules")
    ap.add_argument("--compare", default="0.02:0.01:20,0.03:0.003:20",
                    help="sign tests (DELTA:ALPHA:CAP, comma-separated) compared with the current rule "
                         "group by group after the D8 table")
    ap.add_argument("--nsim", type=int, default=100000, help="contests per simulated test")
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    groups = []
    for g in a.groups:
        name, _, spec = g.partition("=")
        pats, _, sel = spec.partition("@")
        conds = [(f, set(v.split("|"))) for f, _, v in (c.partition("=") for c in sel.split("&") if c)]
        where = None
        if conds:                       # @f=v1|v2&g=w: records whose fields have those values
            where = (lambda rec, conds=conds: all(str(rec.get(f)) in vs for f, vs in conds))
        groups.append((name, load(pats.split(","), where)[0]))
    compare = [tuple(c.split(":")) for c in a.compare.split(",") if c]
    text = report(groups, [float(v) for v in a.alphas.split(",")], [int(v) for v in a.caps.split(",")],
                  a.nsim, a.seed, compare)
    if a.out:
        with open(a.out, "w") as f:
            f.write(text)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
