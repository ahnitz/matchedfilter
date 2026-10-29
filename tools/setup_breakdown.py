#!/usr/bin/env python
"""Where a job's matchedfilter setup time goes, by part, replayed from a capture.

    python tools/setup_breakdown.py CAPDIR [NREFS]

Replays a capture as tools/setup_replay.py does, with the library's entry points wrapped:
each wrapped call's time, less the wrapped calls inside it, is charged to its part (cost
calibration, the noise and signal simulations, the plan search, template loading, ...), so
the parts add up to the replay. The second call of each bank is the steady filtering; the
first call's time beyond it is setup done inside the call. Prints CPU and wall seconds per
part and per reference. CSEARCH=0 runs the plan search's Python reference.
"""
import sys, os, glob, pickle, time, json, collections
import matchedfilter.time_domain as td
from matchedfilter import gatechain as gc, gatemodel as gm, _calibration as cal, _hierarchical as hi
from matchedfilter import _layout as lay, _prices as pr

T = collections.defaultdict(lambda: [0.0, 0.0, 0])      # part -> [cpu, wall, calls]
stack = []                                              # [part, cpu0, wall0, child cpu, child wall]


def clocks():
    return time.thread_time(), time.perf_counter()


def wrap(owner, name, part):
    f = getattr(owner, name, None)
    if f is None:                   # an older tree without this entry point
        print("  (no %s.%s)" % (getattr(owner, "__name__", owner), name)); return
    if isinstance(f, (staticmethod, classmethod)):
        raise TypeError(name)

    def w(*a, **k):
        c0, w0 = clocks()
        stack.append([part, c0, w0, 0.0, 0.0])
        try:
            return f(*a, **k)
        finally:
            c1, w1 = clocks()
            p, _, _, cc, cw = stack.pop()
            dc, dw = c1 - c0, w1 - w0
            t = T[p]; t[0] += dc - cc; t[1] += dw - cw; t[2] += 1
            if stack:
                stack[-1][3] += dc; stack[-1][4] += dw
    w.__wrapped__ = f
    setattr(owner, name, w)


def main():
    if os.environ.get("CSEARCH") == "0" and hasattr(gc, "_C_SEARCH"):
        gc._C_SEARCH = False                    # the plan search's Python reference
    H, TD = hi.HierarchicalFilter, td.TimeDomainFilterBank
    for owner, name, part in [
            (cal, "calibrate_costs", "cost calibration"),
            (gc, "noise_block_maxima", "MC noise maxima"),
            (gc, "signal_draws", "MC signal draws"),
            (gc, "_simulate", "MC simulation"),
            (gc, "kept_draws", "plan search"), (gc, "_chain_candidates", "plan search"),
            (gc, "plan_chain", "plan search"), (gc, "_choose_chain", "plan search"),
            (gc, "choose_chain", "plan search"), (gc, "chain_thresholds", "plan search"),
            (gc, "_gate_features", "profile/features"), (gm, "_profile_sig", "profile/features"),
            (gc, "rebin_profile", "profile/features"),
            (H, "_choose_chain", "chain choice (rest)"), (H, "_direct_price", "chain choice (rest)"),
            (H, "_cost_model", "chain choice (rest)"),
            (H, "_new_cpu_plan", "plan construction"), (H, "_restore_into", "template load"),
            (H, "_load_held_templates", "template load"), (H, "set_templates", "template load"),
            (td._TemplateGroup, "load_templates", "template load"),
            (H, "set_reference", "HF set_reference (rest)"),
            (TD, "_choose_layout", "block layout"), (TD, "_build", "bank build"),
            (lay, "_corr_block_costs", "correlation pricing"),
            (pr, "_cpu_forward_platform", "forward/direct pricing"), (pr, "_direct_lagtap", "forward/direct pricing"),
            (TD, "__init__", "bank init (rest)"), (TD, "set_reference", "bank set_reference (rest)"),
            ]:
        wrap(owner, name, part)

    d = sys.argv[1]; nref = int(sys.argv[2]) if len(sys.argv) > 2 else 10**6
    refs = {int(f[-7:-4]): pickle.load(open(f, "rb")) for f in sorted(glob.glob(d + "/ref*.pkl"))}
    calls = {int(f[-7:-4]): f for f in sorted(glob.glob(d + "/call_ref*.pkl"))}
    banks = [pickle.load(open(f, "rb")) for f in sorted(glob.glob(d + "/bank*.pkl"))]
    banks = [b for b in banks if b[0] < nref and b[0] in calls]
    fs = TD.filter_series

    def timed(part, fn):
        c0, w0 = clocks()
        stack.append([part, c0, w0, 0.0, 0.0])
        try:
            return fn()
        finally:
            c1, w1 = clocks(); p, _, _, xc, xw = stack.pop()
            t = T[p]; t[0] += c1 - c0 - xc; t[1] += w1 - w0 - xw; t[2] += 1


    per = collections.defaultdict(float); cache = {}
    cpu0, wall0 = clocks()
    for ri, a, k in banks:
        if ri not in cache:
            cache = {ri: pickle.load(open(calls[ri], "rb"))}
        ser, ca, ck = cache[ri]
        k = dict(k); k["device"] = None
        c0, _ = clocks()

        def build():
            b = TD(*a, **k); b.set_reference(*refs[ri][0], **refs[ri][1]); return b
        b = timed("bank init (rest)", build)
        timed("first call (rest)", lambda: fs(b, ser, *ca, **ck))
        timed("steady call", lambda: fs(b, ser, *ca, **ck))
        per[ri] += clocks()[0] - c0
    cpu, wall = clocks()[0] - cpu0, clocks()[1] - wall0
    steady = T["steady call"][0]
    # the first call's own time, beyond a steady call, is setup done inside it
    T["first call beyond steady"] = [T["first call (rest)"][0] - steady, T["first call (rest)"][1] - T["steady call"][1], len(banks)]
    del T["first call (rest)"]
    acc = sum(v[0] for v in T.values()) + steady    # the first call's part had a steady call taken off
    print("refs %d banks %d: replay %.2f s CPU (%.2f wall); parts add to %.2f s CPU" % (len(per), len(banks), cpu, wall, acc))
    setup = cpu - steady
    print("  setup (all but the steady calls) %.2f s CPU; steady calls %.2f s CPU" % (setup, steady))
    for p, (c, w, n) in sorted(T.items(), key=lambda kv: -kv[1][0]):
        print("  %-28s %8.3f s CPU %8.3f s wall %6d calls  %5.1f%% of setup" % (p, c, w, n, 100 * c / setup if p != "steady call" else float("nan")))
    print("  per ref CPU: " + " ".join("%.2f" % per[r] for r in sorted(per)))
    if os.environ.get("OUTJSON"):
        json.dump({"cpu": cpu, "wall": wall, "parts": dict(T), "per_ref": per}, open(os.environ["OUTJSON"], "w"))


if __name__ == "__main__":
    main()
