# replay_calls2.py CAPDIR K [NBANKS]: as replay_calls.py (K filter_series_many calls per bank, in
# capture order), for trees with joint trials (_trial) or the old trials; prints total CPU, the
# block sizes banks end on, the chains their plans run, and every trial's lock.
import sys, os, time, pickle, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from setup_replay import load
import matchedfilter.time_domain as td
K = int(sys.argv[2]); NB = int(sys.argv[3]) if len(sys.argv) > 3 else None
refs, calls, banks = load(sys.argv[1])
banks = banks[:NB] if NB else banks
cache = {}; sizes = collections.Counter(); chains = collections.Counter(); q15 = collections.Counter()
c0 = time.thread_time()
for ri, a, k in banks:
    if ri not in cache: cache = {ri: pickle.load(open(calls[ri], "rb"))}
    ser, ca, ck = cache[ri]; k = dict(k); k["device"] = None
    b = td.TimeDomainFilterBank(*a, **k); b.set_reference(*refs[ri][0], **refs[ri][1])
    for _ in range(K):
        td.TimeDomainFilterBank.filter_series_many([(b, ser, dict(ck))])
    for g in b._groups:
        sizes[g.n] += 1
        p = getattr(g, "_plan", None)
        if g.is_hier and p is not None and p._chain is not None:
            chains[tuple(p._chain)] += 1; q15[bool(p._q15)] += 1
try:
    from matchedfilter import _trial
    locks = {k: v.winner for k, v in _trial._TRIALS.items()}
except ImportError:
    locks = {kk: st.winner for kk, st in td._BLOCK_TRIALS.state.items()}
print("K=%d banks %d total CPU %.1f s | n %s | chains %s | q15 %s | locks %s" % (
    K, len(banks), time.thread_time() - c0, dict(sizes), dict(chains.most_common(4)), dict(q15), locks), flush=True)
