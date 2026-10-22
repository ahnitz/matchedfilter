#!/usr/bin/env python3
"""Test small real-input CPU probes against independently timed full leaf calls.

This is a feasibility study, NOT a table-free planner. Existing seeded costs and
locks prepare the baseline scientific thresholds, chain and native plan. That
preparation is excluded and reported separately. Only the Q15 enable/order flags
change afterwards; all arms use the same plan, templates, thresholds and input.

Example, from the checkout with its extension built:
  python tools/real_probe_study.py --captures /path/to/captures/leaves \
      --costs /path/to/seeded-costs.json --output /path/to/probe.json --limit 3

Pilots retain whole homogeneous-window 32-block groups, stratified over the
captured layout, and the entire template bank. Three rotated rounds race float,
ordinary Q15 and delayed Q15. Selection uses ONLY pilot timings. A separate full
call race includes those three arms and a duplicate locked-baseline control.
Every switch has an untimed warm call; its cost is INCLUDED in the probe budget.
Sparse outputs and native final row counts must agree exactly. Validation is
outside execution timers but inside the pilot budget.

This measures public plan.run_series, not the entire PyCBC search. Repeated
timings of one input do not add independent survivor observations. Sparse pilots
can choose dense Q15 work well while mispricing rare later tiers/refinement.
"""
import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import traceback


ARMS = ("float", "q15_ordinary", "q15_delayed")
FLAGS = {"float": (False, False), "q15_ordinary": (True, False),
         "q15_delayed": (True, True)}
COMPARISON_VERSION = 2
THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
               "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stratified_rows(low, high, blocks, group, chunk=32):
    """Select full chunks within equal-window runs, without splitting a group."""
    if len(low) != len(high) or not low:
        raise ValueError("nonempty matching window arrays required")
    if group < 1 or chunk % group or blocks < chunk or blocks % chunk:
        raise ValueError("pilot blocks must be multiples of 32; native group must divide 32")
    edges = [0] + [i for i in range(1, len(low))
                   if (low[i], high[i]) != (low[i - 1], high[i - 1])] + [len(low)]
    chunks = [(a, a + chunk) for start, stop in zip(edges[:-1], edges[1:])
              for a in range(start, stop - chunk + 1, chunk)]
    needed = blocks // chunk
    if needed > len(chunks):
        raise ValueError(f"{blocks} pilot blocks requested but only {len(chunks) * chunk} "
                         "fit whole homogeneous-window chunks")
    # Integer midpoints avoid duplicates and float rounding at stratum edges.
    picked = [chunks[(2 * i + 1) * len(chunks) // (2 * needed)] for i in range(needed)]
    rows = [j for start, stop in picked for j in range(start, stop)]
    return rows, dict(original_row_ranges=picked, eligible_chunks=len(chunks),
                      excluded_partial_rows=len(low) - len(chunks) * chunk,
                      chunk_blocks=chunk, native_group=group)


def arm_order(labels, round_index, phase=0, reverse=False):
    offset = (round_index + phase) % len(labels)
    order = list(labels[offset:]) + list(labels[:offset])
    return order[::-1] if reverse and (round_index // len(labels)) % 2 else order


def select_pilot(rounds, baseline, tie_margin):
    """A paired race; small/noisy improvements retain the existing baseline."""
    if any(not math.isfinite(r[arm]) or r[arm] <= 0 for r in rounds for arm in ARMS):
        raise ValueError("all pilot samples must be finite and positive")
    ratios = {arm: [r[arm] / r[baseline] for r in rounds] for arm in ARMS}
    medians = {arm: statistics.median(v) for arm, v in ratios.items()}
    fastest = min(ARMS, key=medians.__getitem__)
    wins = sum(v < 1.0 - tie_margin for v in ratios[fastest])
    enough = wins >= math.ceil(2 * len(rounds) / 3)
    selected = fastest if medians[fastest] < 1.0 - tie_margin and enough else baseline
    return dict(selected=selected, raw_fastest=fastest, paired_median_ratios=medians,
                paired_ratios=ratios, winning_rounds=wins, required_rounds=math.ceil(2 * len(rounds) / 3),
                tie_margin=tie_margin)


def compare_full_call(medians, baseline, picked, probe_elapsed_ns):
    """Compare policies using each unique configuration's canonical measurement.

    The independently timed ``baseline`` alias is only a noise control. Reusing
    the existing policy must have exactly zero estimated execution savings,
    regardless of fluctuations between identical-configuration measurements.
    """
    selected = medians[picked]
    existing = medians[baseline]
    oracle = min(medians[arm] for arm in ARMS)
    saved = existing - selected
    return dict(
        selected_median_ns=selected, oracle_median_ns=oracle, baseline_median_ns=existing,
        saved_ns_per_call=saved, regret=selected / oracle - 1,
        selected_over_baseline=selected / existing,
        oracle_within_2pct=selected <= 1.02 * oracle,
        full_calls_to_amortize_probe=probe_elapsed_ns / saved if saved > 0 else None,
        one_call_including_probe_over_baseline=(probe_elapsed_ns + selected) / existing)


def counter_delta(after, before):
    def sub(a, b):
        if isinstance(a, dict):
            return {k: sub(a[k], b[k]) for k in a}
        if isinstance(a, (list, tuple)):
            return [sub(x, y) for x, y in zip(a, b)]
        return a - b
    return {k: sub(after[k], before[k])
            for k in ("pairs", "passed", "checked", "refined", "q15", "ticks")}


def git_output(root, *args):
    p = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True)
    return p.stdout.strip() if p.returncode == 0 else None


def save(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def unchanged_seed(seed_path, seed):
    if json.loads(seed_path.read_text()) != seed:
        raise RuntimeError("seeded costs/locks changed during preparation; seed is incomplete "
                           "or incompatible. No new calibration is accepted by this study")


def prepare(file, args, mf, td, np, seed_path, seed):
    start = time.perf_counter_ns()
    with np.load(file, allow_pickle=False) as z:
        options = ast.literal_eval(str(z["options"].item()))
        if not isinstance(options, dict) or options.get("engine") != "hier":
            raise ValueError(f"{file}: expected captured hierarchical options dictionary")
        if not np.iscomplexobj(z["taps"]):
            raise ValueError("this initial study requires the captured complex quadrature tap banks")
        captured_options = options.copy()
        options.update(device="cpu", fft_lengths=[2048])
        threshold = float(z["threshold"])
        bank = td.TimeDomainFilterBank(z["taps"], z["counts"], threshold=threshold, **options)
        bank.set_reference(z["profile"], delta_f=float(z["delta_f"]))
        data = np.array(z["series"], copy=True)
        if data.dtype != np.float32 or data.ndim != 1:
            raise ValueError("expected one-dimensional float32 captured input")
        if int(z["strided"]):
            backing = np.zeros(data.size, np.complex64)
            backing.real = data
            series = backing.real
        else:
            series = np.ascontiguousarray(data)
        windows = [tuple(int(v) for v in w) for w in z["windows"]]
        window_arg = slice(*windows[0]) if len(windows) == 1 else windows
        provenance = dict(
            path=str(file.resolve()), sha256=sha256(file), captured_options=captured_options,
            overrides=dict(device="cpu", fft_lengths=[2048]), threshold=threshold,
            delta_f=float(z["delta_f"]), windows=windows,
            array_sha256={k: hashlib.sha256(z[k].tobytes()).hexdigest()
                          for k in ("taps", "counts", "lags", "profile", "series")},
            series_dtype=str(series.dtype), series_shape=list(series.shape),
            series_strides=list(series.strides))
    if int(options.get("binsize", 0)) != 2048:
        raise ValueError("this fixed-block study requires the production binsize=2048")
    for warm in range(args.warmup_max):
        bank.filter_series(series, windows=window_arg)
        unchanged_seed(seed_path, seed)
        if len(bank._groups) != 1:
            raise ValueError("expected one full-bank template group per captured leaf")
        p = bank._groups[0].plan
        if not isinstance(p, mf.HierarchicalFilter) or p.device.kind != "cpu":
            raise ValueError("expected a native CPU hierarchical plan")
        if warm >= 2 and not p.calibrating() and not getattr(p, "_trial_hold", False):
            break
    else:
        raise RuntimeError(f"{file}: seeded adaptive choices did not settle")
    baseline_result = bank.filter_series(series, windows=window_arg)  # adopt settled choice
    unchanged_seed(seed_path, seed)
    if p.n != 2048 or tuple(p.config) != (256, 512, 1024) or p._chain_trial is not None:
        raise RuntimeError("fixed scientific chain/block was not preserved")
    ep = p._execution_plan()                       # resolve thresholds BEFORE flags
    if mf._prices._Q15_TIER0.get(256, False):
        raise RuntimeError("this study expects x86 FP32 tier 0, not the ARM FP16 gate")
    late = bool(getattr(p, "_q15_order_choice", None) and p._q15_order_choice["late"])
    baseline = "q15_delayed" if p._q15 and late else "q15_ordinary" if p._q15 else "float"
    lock = mf._chains._Q15_TRIALS.get(p._q15_trial_key())
    if lock is None or lock.winner is None or bool(lock.winner) != bool(p._q15):
        raise RuntimeError("baseline Q15 choice is not a settled seeded lock")
    thresholds = tuple(ep.thresholds())
    if thresholds != tuple(p._thresholds()):
        # Native thresholds are float32; compare after rounding Python values.
        if thresholds != tuple(float(x) for x in np.asarray(p._thresholds(), np.float32)):
            raise RuntimeError("native and scientific gate thresholds disagree")
    p._trial_hold = True
    p._want_sparse = True
    group = bank._groups[0]
    layout = tuple(group._cached_layout[1:])
    provenance.update(
        baseline_threshold_preparation_excluded_ns=time.perf_counter_ns() - start,
        preparation_calls=warm + 2, n=2048, chain=list(p.config), thresholds=list(thresholds),
        native_plan_id=id(ep), native_group=int(ep.series_group()), ntemplates=p.ntemplates,
        nblocks=len(layout[0]), baseline=baseline, baseline_flags=[bool(p._q15), late],
        baseline_bank_output_sha256=[hashlib.sha256(a.tobytes()).hexdigest()
                                     for a in baseline_result],
        baseline_q15_lock=lock, baseline_order_choice=getattr(p, "_q15_order_choice", None),
        forward_platform=bool(p._pfft), execution_policy=dict(p._execution_policy),
        full_layout_sha256=[hashlib.sha256(a.tobytes()).hexdigest() for a in layout])
    return bank, p, ep, series, layout, provenance


class Race:
    def __init__(self, p, ep, series, layout, threshold, baseline, mf, np):
        self.p, self.ep, self.series, self.layout = p, ep, series, layout
        self.threshold, self.baseline, self.mf, self.np = threshold, baseline, mf, np
        self.thresholds = tuple(ep.thresholds())
        self.reference = None
        self.reference_counts = None
        self.reference_refined = None
        self.validation_ns = 0
        self.switch_warm_ns = 0
        self.samples = []

    def call(self):
        return self.p.run_series(self.series, *self.layout, binsize=2048,
                                 threshold=self.threshold, raw=True)

    def check_result(self, results):
        """Native counts describe the LAST call; all calls use identical input."""
        begin = time.perf_counter_ns()
        np, p = self.np, self.p
        last = results[-1]
        if not all(isinstance(r, self.mf._SparsePeaks) for r in results):
            raise AssertionError("public plan did not return owned sparse results")
        shape = (len(self.layout[0]), p.ntemplates, 1)
        _, layout, _, _, _ = p._grouped_layout(self.series, *self.layout, 2048, None)
        counts = self.mf._scratch_counts(shape[0] * shape[1]).copy().reshape(shape[:2])
        if layout.order is not None:
            restored = np.empty_like(counts)
            restored[layout.order] = counts
            counts = restored
        for result in results:
            payload = (result.shape, result.flat.tobytes(), result.idx.tobytes(), result.val.tobytes())
            if result.shape != shape:
                raise AssertionError(f"unexpected result shape: {result.shape}, expected {shape}")
            if self.reference is None:
                self.reference = payload
            elif payload != self.reference:
                raise AssertionError("exact sparse output mismatch between same-input arms/repeats")
        from_sparse = np.bincount(last.flat // shape[2], minlength=counts.size).reshape(counts.shape)
        if (not np.array_equal(counts, from_sparse) or int(counts.sum()) != p._last_n_triggers
                or p._last_n_triggers != len(last.flat)):
            raise AssertionError("native row counts do not match sparse peaks and returned total")
        if self.reference_counts is None:
            self.reference_counts = counts
        elif not np.array_equal(counts, self.reference_counts):
            raise AssertionError("native final row counts changed across same-input arms")
        if (p._execution_plan() is not self.ep or tuple(self.ep.thresholds()) != self.thresholds
                or not p._trial_hold or p._chain_trial is not None):
            raise AssertionError("native plan, thresholds or adaptive hold changed during race")
        self.validation_ns += time.perf_counter_ns() - begin

    def sample(self, arm, round_index, position, repeats):
        start = time.perf_counter_ns()
        q15, late = FLAGS[self.baseline if arm == "baseline" else arm]
        self.p._q15 = q15
        if not self.ep.set_q15(q15) or not self.ep.set_q15_recheck_late(late):
            raise RuntimeError(f"native plan rejected {arm}")
        warm = self.call()
        warm_ns = time.perf_counter_ns() - start
        self.switch_warm_ns += warm_ns
        self.check_result([warm])
        before = self.p.work_counts()
        start = time.perf_counter_ns()
        results = [self.call() for _ in range(repeats)]
        elapsed = time.perf_counter_ns() - start
        after = self.p.work_counts()
        work = counter_delta(after, before)
        row = dict(arm=arm, round=round_index, position=position, repeats=repeats,
                   elapsed_ns=elapsed, ns_per_call=elapsed / repeats,
                   switch_and_warm_ns=warm_ns, work=work, validated=False)
        self.samples.append(row)
        self.check_result(results)
        expected_pairs = len(self.layout[0]) * self.p.ntemplates * repeats
        if work["pairs"] != expected_pairs or work["refined"] % repeats:
            raise AssertionError("unexpected native work count: an adaptive replay may have run")
        refined = work["refined"] // repeats
        if self.reference_refined is None:
            self.reference_refined = refined
        elif refined != self.reference_refined:
            raise AssertionError("same-input variants produced different final refinement counts")
        ticks = work["ticks"]
        work["ticks"]["tier0_without_q15"] = ticks["tiers"][0] - ticks["q15"]
        work["ticks"]["series_remainder"] = ticks["series"] - sum(ticks["tiers"]) - ticks["refine"]
        row["validated"] = True
        return elapsed / repeats

    def result(self):
        digest = hashlib.sha256()
        for payload in self.reference[1:]:
            digest.update(payload)
        return dict(samples=self.samples, exact_sparse_and_counts_equal=True,
                    output_sha256=digest.hexdigest(),
                    counts_sha256=hashlib.sha256(self.reference_counts.tobytes()).hexdigest(),
                    peaks_per_call=int(self.reference_counts.sum()),
                    refinements_per_distinct_input=self.reference_refined,
                    rare_survivor_warning=self.reference_refined < 10,
                    switch_and_warm_ns=self.switch_warm_ns, validation_ns=self.validation_ns)


def study_capture(file, index, args, mf, td, np, seed_path, seed, row):
    bank, p, ep, series, layout, info = prepare(file, args, mf, td, np, seed_path, seed)
    row.update(info, pilots=[], full={})
    for blocks in args.pilot_blocks:
        begin = time.perf_counter_ns()
        rows, selection = stratified_rows(layout[1].tolist(), layout[2].tolist(), blocks,
                                          int(ep.series_group()))
        pilot_layout = tuple(np.ascontiguousarray(a[rows], dtype=np.uintp) for a in layout)
        race = Race(p, ep, series, pilot_layout, info["threshold"], info["baseline"], mf, np)
        result = dict(blocks=blocks, pairs=blocks * p.ntemplates, layout=selection,
                      samples=race.samples)
        row["pilots"].append(result)
        rounds = []
        for r in range(args.pilot_rounds):
            timings = {}
            for position, arm in enumerate(arm_order(ARMS, r, index)):
                timings[arm] = race.sample(arm, r, position, args.pilot_repeats)
            rounds.append(timings)
        decision = select_pilot(rounds, info["baseline"], args.tie_margin)
        result.update(decision=decision, **race.result())
        result["probe_elapsed_ns"] = time.perf_counter_ns() - begin
        result["execution_timed_ns"] = sum(s["elapsed_ns"] for s in race.samples)
        print(f"{file.name}: pilot {blocks} -> {decision['selected']}, "
              f"{result['refinements_per_distinct_input']} unique refinements, "
              f"{result['probe_elapsed_ns'] / 1e6:.1f} ms including warm/validation", flush=True)

    # Independent measurements: pilot selection never reads these samples.
    race = Race(p, ep, series, layout, info["threshold"], info["baseline"], mf, np)
    row["full"] = dict(samples=race.samples)
    for r in range(args.rounds):
        for position, arm in enumerate(arm_order(ARMS + ("baseline",), r, index, reverse=True)):
            race.sample(arm, r, position, args.repeats)
    full = race.result()
    medians = {arm: statistics.median(s["ns_per_call"] for s in race.samples if s["arm"] == arm)
               for arm in ARMS + ("baseline",)}
    oracle = min(ARMS, key=medians.__getitem__)
    full.update(median_ns=medians, oracle=oracle,
                baseline_alias_ratio=medians[info["baseline"]] / medians["baseline"])
    row["full"] = full
    # Link the direct public-plan replay back to the prepared production bank.
    _, flat_bytes, idx_bytes, val_bytes = race.reference
    flat, idx = np.frombuffer(flat_bytes, np.int64), np.frombuffer(idx_bytes, np.int64)
    bi, ti = np.divmod(flat, p.ntemplates)  # binsize=2048 gives exactly one bin
    starts = np.asarray(layout[0], np.int64)[bi]
    bank_arrays = (bank._groups[0].template_indices[ti], starts + idx,
                   np.frombuffer(val_bytes, np.complex64), starts,
                   np.full(flat.size, 2048, np.int64))
    if [hashlib.sha256(a.tobytes()).hexdigest() for a in bank_arrays] != info["baseline_bank_output_sha256"]:
        raise AssertionError("public plan replay does not reproduce prepared bank outputs")
    full["matches_prepared_bank"] = True
    for pilot in row["pilots"]:
        picked = pilot["decision"]["selected"]
        pilot["full_comparison"] = compare_full_call(
            medians, info["baseline"], picked, pilot["probe_elapsed_ns"])
    unchanged_seed(seed_path, seed)
    row["complete"] = True
    print(f"{file.name}: full winner {oracle}, baseline alias ratio "
          f"{full['baseline_alias_ratio']:.4f}, {full['peaks_per_call']} peaks", flush=True)
    # bank keeps templates/native owners alive through the last validation.
    del bank


def aggregate(rows, pilot_blocks):
    completed = [row for row in rows if row.get("complete")]
    if not completed:
        return {}
    out = dict(captures=len(completed), pairs=sum(r["nblocks"] * r["ntemplates"] for r in completed),
               peaks=sum(r["full"]["peaks_per_call"] for r in completed),
               baseline_threshold_preparation_excluded_ns=
               sum(r["baseline_threshold_preparation_excluded_ns"] for r in completed), pilots={})
    for blocks in pilot_blocks:
        pilots = [next(p for p in r["pilots"] if p["blocks"] == blocks) for r in completed]
        comparisons = [p["full_comparison"] for p in pilots]
        chosen = sum(c["selected_median_ns"] for c in comparisons)
        oracle = sum(c["oracle_median_ns"] for c in comparisons)
        baseline = sum(c["baseline_median_ns"] for c in comparisons)
        overhead = sum(p["probe_elapsed_ns"] for p in pilots)
        out["pilots"][str(blocks)] = dict(
            selected_full_ns_sum=chosen, oracle_full_ns_sum=oracle, baseline_full_ns_sum=baseline,
            saved_ns_per_pass=baseline - chosen,
            aggregate_regret=chosen / oracle - 1, selected_over_baseline=chosen / baseline,
            median_capture_regret=statistics.median(c["regret"] for c in comparisons),
            worst_capture_regret=max(c["regret"] for c in comparisons),
            outside_2pct_oracle=sum(not c["oracle_within_2pct"] for c in comparisons),
            rare_survivor_pilots=sum(p["rare_survivor_warning"] for p in pilots),
            probe_elapsed_ns_sum=overhead,
            full_calls_to_amortize_probe=overhead / (baseline - chosen) if baseline > chosen else None,
            one_pass_including_probes_over_baseline=(overhead + chosen) / baseline)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--captures", type=Path, required=True)
    parser.add_argument("--costs", type=Path, required=True, help="complete read-only baseline seed")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pattern", default="*.npz")
    parser.add_argument("--limit", type=int, default=0, help="0: all matched captures")
    parser.add_argument("--pilot-blocks", type=int, nargs="+", default=[32, 64, 128])
    parser.add_argument("--pilot-rounds", type=int, default=3)
    parser.add_argument("--pilot-repeats", type=int, default=1)
    parser.add_argument("--rounds", type=int, default=9, help="independent full-call rounds, >=7")
    parser.add_argument("--repeats", type=int, default=5, help="full calls per timed batch, >=2")
    parser.add_argument("--tie-margin", type=float, default=.02)
    parser.add_argument("--warmup-max", type=int, default=32)
    parser.add_argument("--core", type=int, default=6)
    args = parser.parse_args()
    if (args.rounds < 7 or args.repeats < 2 or args.pilot_rounds < 3 or args.pilot_rounds % 3
            or args.pilot_repeats < 1 or args.warmup_max < 3 or args.limit < 0
            or not 0 <= args.tie_margin < 1 or len(set(args.pilot_blocks)) != len(args.pilot_blocks)
            or any(b < 32 or b % 32 for b in args.pilot_blocks)):
        parser.error("need full rounds>=7, repeats>=2; pilot rounds multiple of 3, repeats>=1; "
                     "distinct pilot blocks positive multiples of 32; warmup>=3, limit>=0, 0<=tie<1")
    files = sorted(args.captures.glob(args.pattern))
    if args.limit:
        files = files[:args.limit]
    if not files:
        parser.error("no matching captures")
    if not args.costs.is_file():
        parser.error("an existing complete baseline cost seed is required")
    os.sched_setaffinity(0, {args.core})
    for name in THREAD_VARS:
        os.environ[name] = "1"
    os.environ.update(MF_CHAIN_FORCE="2048:256,512,1024", MF_AUTOTUNE="1",
                      VK_ICD_FILENAMES="/dev/null")
    for name in ("MF_HMF_PROF", "MF_HMF_TRACE", "MF_HMF_DUMP"):
        os.environ.pop(name, None)
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "python"))
    with tempfile.TemporaryDirectory(prefix="mf-real-probe-") as scratch:
        seed_path = Path(scratch) / "costs.json"
        shutil.copyfile(args.costs, seed_path)
        seed = json.loads(seed_path.read_text())
        os.environ["MF_COST_FILE"] = str(seed_path)
        import numpy as np
        import matchedfilter as mf
        from matchedfilter import _core, time_domain as td
        sources = ["tools/real_probe_study.py", "python/matchedfilter/__init__.py",
                   "python/matchedfilter/time_domain.py", "python/matchedfilter/gatechain.py",
                   "python/matchedfilter/_core.c", "src/hmf.c", "src/q15-inl.h"]
        report = dict(
            study="fixed-science CPU real-input execution probe", status="running",
            comparison_version=COMPARISON_VERSION,
            interpretation=[
                "Baseline threshold preparation excluded; existing costs still determine science.",
                "Same native plan and full template bank; only Q15 enable/recheck order varies.",
                "Pilot budget includes switches, warm calls, validation and selection overhead.",
                "Warm prepared-plan study: initial native creation is not charged to the probe.",
                "Pilot sizes are separate races; later races reuse the already warmed plan.",
                "Whole homogeneous-window groups omit incomplete edge/tail chunks from pilots.",
                "Repeated timings do not add independent rare-survivor observations.",
                "Full-call oracle uses three unique arms; baseline is an identical-config control.",
                "Policy savings use the canonical baseline configuration's median; alias is noise only.",
                "Series remainder counters include forward transform, ingestion and bookkeeping.",
                "Exact agreement on these captures is not a general false-dismissal proof."],
            parameters={k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
            provenance=dict(
                root=str(root), git_head=git_output(root, "rev-parse", "HEAD"),
                git_branch=git_output(root, "branch", "--show-current"),
                git_status=git_output(root, "status", "--short"),
                git_diff_sha256=hashlib.sha256((git_output(root, "diff", "HEAD") or "").encode()).hexdigest(),
                source_sha256={p: sha256(root / p) for p in sources},
                core_path=str(_core.__file__), core_sha256=sha256(_core.__file__),
                package=str(mf.__file__), backend=mf.backend(),
                python=sys.version, numpy=np.__version__, platform=platform.platform(),
                affinity=sorted(os.sched_getaffinity(0)),
                environment={k: v for k, v in os.environ.items()
                             if k.startswith("MF_") or k in THREAD_VARS or k == "VK_ICD_FILENAMES"},
                cost_seed_path=str(args.costs.resolve()), cost_seed_sha256=sha256(args.costs)),
            captures=[])
        save(args.output, report)
        try:
            for index, file in enumerate(files):
                row = dict(path=str(file.resolve()), complete=False)
                report["captures"].append(row)
                study_capture(file, index, args, mf, td, np, seed_path, seed, row)
                report["aggregate"] = aggregate(report["captures"], args.pilot_blocks)
                save(args.output, report)
            if sha256(args.costs) != report["provenance"]["cost_seed_sha256"]:
                raise RuntimeError("original read-only cost seed changed externally during study")
            report["status"] = "complete"
        except Exception:
            report["status"] = "failed"
            report["error"] = traceback.format_exc()
            raise
        finally:
            report["aggregate"] = aggregate(report["captures"], args.pilot_blocks)
            report["seed_unchanged"] = json.loads(seed_path.read_text()) == seed
            save(args.output, report)


if __name__ == "__main__":
    main()
