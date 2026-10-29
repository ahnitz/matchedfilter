# aa_replay.py CAPDIR K [OFFSET [NBANKS]]: replay_calls2.py's replay of a capture -- K
# filter_series_many calls per bank, banks in capture order -- started at bank OFFSET (the order
# rotated, so each process's joint trial plays on other banks) and limited to NBANKS banks (all
# by default). Prints total CPU, the block sizes banks end on, the chains their plans run, the Q15
# settings and every trial's lock, as replay_calls2.py does.
import sys, os, time, pickle, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from setup_replay import load
import matchedfilter.time_domain as td
from matchedfilter import _trial
K = int(sys.argv[2]); OFF = int(sys.argv[3]) if len(sys.argv) > 3 else 0
NB = int(sys.argv[4]) if len(sys.argv) > 4 else None
refs, calls, banks = load(sys.argv[1])
OFF %= len(banks)
banks = banks[OFF:] + banks[:OFF]
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
locks = {k: v.winner for k, v in _trial._TRIALS.items()}
print("K=%d offset %d banks %d total CPU %.1f s | n %s | chains %s | q15 %s | locks %s" % (
    K, OFF, len(banks), time.thread_time() - c0, dict(sizes), dict(chains.most_common(4)), dict(q15), locks), flush=True)
