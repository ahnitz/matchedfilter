# mc_choice.py: the current rule's false-switch rate from the library's own Choice (minimum 5,
# cap 10, TIE 5%, confirmation) with m equal challengers whose per-round log ratios are iid
# draws from a measured A/A null, against tools/trial_power.py's DP (current_rate) with the
# same iid model (the pooled win probability). An independent check of the DP's composition
# of elimination, the share rule, m arms and confirmation.
import importlib.util, math
import numpy as np
from matchedfilter import _choice
spec = importlib.util.spec_from_file_location("tp", "tools/trial_power.py")
tp = importlib.util.module_from_spec(spec); spec.loader.exec_module(tp)
E = "docs/measurements/trial-aa-20261029/rounds.jsonl.gz"
_choice._log_autotune = lambda *a, **k: None
for name, where, m, n in (("dev2-ladder", dict(machine="dev2", sets={"lad", "ladshort"}), 2, 200000),
                          ("dev2-replay-solo", dict(machine="dev2", sets={"solo"}), 2, 200000)):
    rounds, _ = tp.load([E], where=lambda r: r.get("machine") == where["machine"] and r.get("set") in where["sets"])
    x = tp.log_ratios(rounds)
    p = float(np.mean(x < math.log(0.95)))
    rng = np.random.default_rng(7)
    sw = 0; rr = 0
    for i in range(n):
        ch = _choice.Choice(["pref"] + ["c%d" % j for j in range(m)], minimum=5, cap=10, confirm=True)
        while ch.winner is None:
            t = {c: (1.0 if c == "pref" else float(math.exp(rng.choice(x)))) for c in ch.live()}
            ch.round(t); rr += 1
        sw += ch.winner != "pref"
    se = math.sqrt(max(sw, 1)) / n
    print("%s: rounds %d p_win %.4f | Choice MC m=%d: %d/%d = %.2e (+-%.1e) | DP iid: %.2e | DP m=1 no confirm %.4f"
          % (name, x.size, p, m, sw, n, sw / n, se, tp.current_rate(p, m), tp.current_rate(p, 1, confirm=False)))
