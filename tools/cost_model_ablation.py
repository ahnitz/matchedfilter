#!/usr/bin/env python3
"""Audit measured-cost versus cost=None chain planning on captured CPU leaves.

Example (set PYTHONPATH to the build being audited):
  python tools/cost_model_ablation.py /path/to/captures/leaves \
      --cost-file /path/to/costs.json --out /path/to/ablation.json

The cost input is read-only: a populated file is copied to temporary storage;
a missing path starts an empty temporary cache. Missing costs are calibrated.
No captured series is filtered. Regret is estimated by the existing cost model,
never measured execution time. This initial audit supports n=2048 and complex
quadrature taps, which do not use the real-tap direct-refinement price adjustment.
"""
import argparse
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

import numpy as np


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git_output(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def capture_cases(args, gc, td, device, select_policy):
    """Reproduce fixed-size grouping and model windows without building plans."""
    cases, profiles = {}, set()
    files = sorted(args.captures.glob(args.pattern))
    if not files:
        raise ValueError("no captures matched %s in %s" % (args.pattern, args.captures))
    for path in files:
        with np.load(path, allow_pickle=False) as record:
            options = ast.literal_eval(str(record["options"].item()))
            if options.get("engine", "hier") not in ("hier", "matchedfilter-hierarchical"):
                raise ValueError("%s is not a hierarchical capture" % path)
            if not np.iscomplexobj(record["taps"]):
                raise ValueError("%s: real-tap direct-refinement pricing is not supported" % path)
            counts = np.asarray(record["counts"], dtype=np.int64)
            rate = float(options.get("data_sample_rate", 2048.0))
            ratio = float(options.get("tap_sample_rate", 2048.0)) / rate
            threshold = float(record["threshold"])
            first_stage = float(options.get("first_stage_snr", 0.0))
            snr = first_stage if first_stage > 0 else threshold
            fd = float(options.get("false_dismissal", 0.001))
            df = float(record["delta_f"])
            profile = gc.rebin_profile(record["profile"], df, rate, args.n)
            if profile is None:
                raise ValueError("%s has no usable rebinned power" % path)
            # TimeDomainFilterBank passes float32 rebinned profiles to its plans.
            power = gc._norm_profile(profile.astype(np.float32), args.n)
            identity = hashlib.sha256(power.tobytes()).hexdigest()
            if identity not in profiles and len(profiles) >= args.limit:
                break
            profiles.add(identity)
            effective = np.ceil(counts / ratio).astype(np.int64)
            groups, order = td._partition_templates(
                effective, max_batch=options.get("max_batch_size"),
                candidate_ns=(args.n,), engine="hier", device="cpu")
            source = dict(path=str(path.resolve()), sha256=sha256(path), options=options,
                          threshold=threshold, delta_f=df,
                          searched_windows=record["windows"].tolist())
            for start, stop, n, _ in groups:
                if n != args.n:
                    raise ValueError("%s contains taps that do not fit n=%d" % (path, args.n))
                indices = order[start:stop]
                margin = int(np.ceil((int(counts[indices].max()) // 2) / ratio))
                window = td.TimeDomainFilterBank._priced_window(margin, n)
                policy = select_policy(device, "hierarchical_series", n, 0, stop - start)
                group = int(policy.get("series_group", gc.default_series_group(n)))
                key = (identity, n, window, snr, fd, group)
                if key not in cases:
                    cases[key] = dict(power=power, profile_sha256=identity, n=n,
                                      window=window, snr=snr, false_dismissal=fd,
                                      series_group=group, execution_policy=policy, sources=[])
                cases[key]["sources"].append(dict(
                    **source, template_indices=indices.tolist(), templates=stop - start,
                    max_tap_count=int(counts[indices].max())))
    return list(cases.values())


def selected(plans, gc, n):
    return gc.pick_stable(
        plans, lambda p: p["cost"],
        lambda p: (gc._flop_cost(p["chain"], p["reach"], n), p["chain"]))


def ranked(plans, best):
    return sorted(plans, key=lambda p: (p["chain"] != best["chain"], p["cost"]))


def plan_record(plan):
    return dict(chain=list(plan["chain"]), thresholds=list(plan["thresholds"]),
                reach=list(plan["reach"]), objective_cost=float(plan["cost"]),
                q15=bool(plan.get("q15", False)))


def audit_case(case, args, gc, mf, cost, signals, noises):
    n, power = case["n"], case["power"]
    snr, fd, window = case["snr"], case["false_dismissal"], tuple(case["window"])
    identity = case["profile_sha256"]
    bands = gc.usable_bands(power, n)
    nsamp = gc._gm._nsamp_for(fd)
    timing = dict(signal_draws_seconds=0.0, noise_block_maxima_seconds=0.0,
                  candidate_enumeration_seconds=0.0, measured_cost_pricing_seconds=0.0,
                  flop_pricing_seconds=0.0)
    skey = (identity, snr, fd, window)
    if skey not in signals:
        # Production allows nearby profiles to share draws. Isolate distinct
        # profiles here so the audit reports sensitivity of each actual input.
        gc._SIGNAL_CACHE.clear()
        gc._SIGNAL_RECORDS.clear()
        gc._NOISE_RECORDS.clear()
        gc._SIMILAR.clear()
        start = time.perf_counter()
        signals[skey] = gc.signal_draws(power, n, bands, snr, nsamp, window=window)
        timing["signal_draws_seconds"] = time.perf_counter() - start
    sig = signals[skey]
    nkey = (identity, window, args.noise_draws)
    if nkey not in noises:
        gc._NOISE_CACHE.clear()
        gc._SIMILAR.clear()
        start = time.perf_counter()
        noises[nkey] = gc.noise_block_maxima(
            power, n, bands, nsim=args.noise_draws, window=window)
        timing["noise_block_maxima_seconds"] = time.perf_counter() - start
    noise = noises[nkey]
    if sig is None:
        raise ValueError("signal draws cannot resolve this profile")
    memo = ("cost-model-ablation", identity, n, snr, fd, window, args.noise_draws, nsamp)
    chains = gc.enumerate_chains(n, args.max_tiers, bands=bands)
    candidate_counts = {}

    def cache_candidates(chain, prune):
        key = memo + (tuple(chain), prune)
        if key not in gc._CAND_CACHE:
            start = time.perf_counter()
            gc._CAND_CACHE[key] = gc._chain_candidates(sig, noise, bands, chain, fd, snr, prune)
            timing["candidate_enumeration_seconds"] += time.perf_counter() - start
        return gc._CAND_CACHE[key]

    for chain in chains:
        candidates = cache_candidates(chain, True)
        candidate_counts[",".join(map(str, chain))] = len(candidates or ())
    feasible = [chain for chain in chains if candidate_counts[",".join(map(str, chain))]]

    plans = {}
    for name, model in (("measured_cost", cost), ("flop", None)):
        start = time.perf_counter()
        rows = [gc.plan_chain(sig, noise, bands, chain, fd, model, n, snr,
                              prune=True, memo=memo) for chain in feasible]
        plans[name] = sorted((p for p in rows if p is not None), key=lambda p: p["cost"])
        timing[name + "_pricing_seconds"] += time.perf_counter() - start
        if not plans[name]:
            raise ValueError("no feasible chain at n=%d snr=%g fd=%g" % (n, snr, fd))
    best = {name: selected(rows, gc, n) for name, rows in plans.items()}
    order = {name: ranked(rows, best[name]) for name, rows in plans.items()}
    # the shortlist the CPU chain trial ran until 2026-10-26: the model's chains within 30% of
    # its best, at most four
    margin, most = 0.30, 4
    shortlist = {
        name: [list(p["chain"]) for p in order[name]
               if p["cost"] <= best[name]["cost"] * (1.0 + margin)][:most]
        for name in plans
    }
    current = best["measured_cost"]
    minimum = min(p["cost"] for p in plans["measured_cost"])
    # A global top-k can spend every slot on one first band. Retain one
    # cost-free FLOP representative per feasible first band as a separate
    # coverage experiment; no execution-time claim follows from its coverage.
    first_bands = sorted({p["chain"][0] for p in plans["flop"]})
    representatives = [
        selected([p for p in plans["flop"] if p["chain"][0] == band], gc, n)
        for band in first_bands]
    # CostModel.chain_cost automatically chooses the cheaper Q15 first tier.
    # Report that controlled comparison separately from literal cost=None,
    # which reports q15=False and would disable the screen.
    no_screen = copy.copy(cost)
    no_screen.screen = {}
    rows = []
    flop_by_chain = {p["chain"]: p for p in plans["flop"]}
    for measured in plans["measured_cost"]:
        flop = flop_by_chain[measured["chain"]]
        rows.append(dict(
            chain=list(measured["chain"]), measured_cost=plan_record(measured),
            flop=plan_record(flop),
            threshold_delta_flop_minus_measured=[
                float(b - a) for a, b in zip(measured["thresholds"], flop["thresholds"])],
            current_model_estimated_cost_at_flop_thresholds=float(
                cost.chain_cost(flop["chain"], list(flop["reach"])))))
    challenger = best["flop"]
    common_screen_cost = cost.chain_cost(challenger["chain"], list(challenger["reach"]))
    literal_cost = no_screen.chain_cost(challenger["chain"], list(challenger["reach"]))

    # Runtime _thresholds() prices prune=False, whereas choose_chain ranks
    # prune=True. Preserve that distinction rather than reporting rank gates as
    # the literal gates the chosen plan would execute.
    execution = []
    for chain in sorted({current["chain"], challenger["chain"]}):
        cache_candidates(chain, False)
        pair = {}
        for name, model in (("measured_cost", cost), ("flop", None)):
            start = time.perf_counter()
            pair[name] = gc.plan_chain(sig, noise, bands, chain, fd, model, n, snr,
                                      prune=False, memo=memo)
            timing[name + "_pricing_seconds"] += time.perf_counter() - start
        execution.append(dict(
            chain=list(chain), **{name: plan_record(p) for name, p in pair.items()},
            threshold_delta_flop_minus_measured=[
                float(b - a) for a, b in zip(pair["measured_cost"]["thresholds"],
                                           pair["flop"]["thresholds"])]))

    return dict(
        **{k: v for k, v in case.items() if k != "power"},
        bands=bands, signal_draws_requested=nsamp, signal_draws_actual=int(sig[0].shape[0]),
        noise_draws=int(noise.shape[0]), timing_seconds=timing,
        candidate_chain_count=len(chains), feasible_chain_count=len(plans["measured_cost"]),
        feasible_threshold_candidate_count=sum(candidate_counts.values()),
        threshold_candidate_counts=candidate_counts,
        selected={name: plan_record(p) for name, p in best.items()},
        cpu_trial_shortlists=shortlist,
        shortlist_overlap=sorted([list(c) for c in
                                  set(map(tuple, shortlist["measured_cost"])) &
                                  set(map(tuple, shortlist["flop"]))]),
        current_model_choice_in_flop_top_k={
            str(k): current["chain"] in {p["chain"] for p in order["flop"][:k]}
            for k in (1, 3, 5)},
        flop_top_five=[plan_record(p) for p in order["flop"][:5]],
        flop_first_band_representatives=[
            dict(**plan_record(p), current_model_estimated_cost_at_flop_thresholds=float(
                cost.chain_cost(p["chain"], list(p["reach"]))))
            for p in representatives],
        first_band_representative_count=len(representatives),
        current_model_choice_in_flop_first_band_representatives=(
            current["chain"] in {p["chain"] for p in representatives}),
        estimated_regret=dict(
            measured_runtime=False, basis="prune=True ranking plans, current calibrated CostModel",
            current_choice_cost=float(current["cost"]), current_model_minimum_cost=float(minimum),
            flop_chain_and_thresholds_with_model_optimal_q15_cost=float(common_screen_cost),
            ratio_to_current_choice=float(common_screen_cost / current["cost"]),
            ratio_to_current_model_minimum=float(common_screen_cost / minimum),
            literal_cost_none_with_q15_off_cost=float(literal_cost),
            literal_cost_none_ratio_to_current_choice=float(literal_cost / current["cost"])),
        per_chain_ranking_comparison=rows, selected_chain_execution_comparison=execution)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", type=Path, help="directory containing captured leaf .npz files")
    parser.add_argument("--cost-file", type=Path, required=True,
                        help="read-only seed; a nonexistent path starts fresh calibration")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pattern", default="*H1.npz")
    parser.add_argument("--limit", type=int, default=3, help="maximum distinct rebinned profiles")
    parser.add_argument("--n", type=int, choices=(2048,), default=2048)
    parser.add_argument("--max-tiers", type=int, default=3)
    parser.add_argument("--noise-draws", type=int, default=20000)
    args = parser.parse_args(argv)
    if args.limit < 1 or not 1 <= args.max_tiers <= 3 or args.noise_draws < 1:
        parser.error("limit/noise-draws must be positive; max-tiers must be in [1, 3]")
    if args.out.resolve() == args.cost_file.resolve():
        parser.error("--out must not overwrite --cost-file")

    import matchedfilter as mf
    from matchedfilter import _calibration, _core, gatechain as gc, time_domain as td
    from matchedfilter.device import parse
    from matchedfilter._execution_policy import select

    root = Path(__file__).resolve().parents[1]
    seed = args.cost_file.read_bytes() if args.cost_file.exists() else b"{}"
    if not isinstance(json.loads(seed), dict):
        parser.error("cost-file must contain a JSON object")
    environment = {k: v for k, v in os.environ.items()
                   if k.startswith("MF_") or k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                                                   "MKL_NUM_THREADS", "BLIS_NUM_THREADS")}
    report = dict(
        schema_version=1, scope="CPU n=2048 chain-planner ablation, not a search benchmark",
        limitations=[
            "No runtime throughput, measured regret, or independent false-dismissal validation.",
            "Uses captured profiles/options and fixed-size group model windows; no series filtering.",
            "Block-size selection, explicit chain pins, and persisted chain/Q15 winners are not applied.",
            "Distinct exact profiles get separate draws; production similarity-cache reuse is disabled.",
            "Complex quadrature taps only; real-tap direct-refinement pricing is unsupported.",
            "FLOP cost=None also disables model-selected Q15; regret reports both Q15 interpretations.",
            "Ranking uses prune=True; selected-chain execution thresholds use prune=False."],
        provenance=dict(
            revision=git_output(root, "rev-parse", "HEAD"),
            worktree_status=git_output(root, "status", "--short"),
            command=sys.argv, python=sys.version, platform=platform.platform(),
            environment=environment, backend=mf.backend(), module=mf.__file__,
            native=_core.__file__, native_sha256=sha256(_core.__file__),
            tool_sha256=sha256(__file__),
            planner_sources={str(Path(m.__file__).resolve()): sha256(m.__file__)
                             for m in (gc, gc._gm, td)},
            cost_file=str(args.cost_file.resolve()), cost_file_existed=args.cost_file.exists(),
            cost_seed_sha256=hashlib.sha256(seed).hexdigest(),
            n=args.n, max_tiers=args.max_tiers, noise_draws=args.noise_draws,
            profile_limit=args.limit, capture_pattern=args.pattern,
            signal_seed=13, noise_seed=29),
        cost_models=[], cases=[])
    start = time.perf_counter()
    cases = capture_cases(args, gc, td, parse("cpu"), select)
    if any(args.out.resolve() == Path(source["path"]).resolve()
           for case in cases for source in case["sources"]):
        parser.error("--out must not overwrite a capture")
    report["capture_preparation_seconds"] = time.perf_counter() - start
    signals, noises, models = {}, {}, {}
    old_cost = os.environ.get("MF_COST_FILE")
    try:
        with tempfile.TemporaryDirectory(prefix="mf-cost-ablation-") as temporary:
            working_cost = Path(temporary) / "costs.json"
            working_cost.write_bytes(seed)
            os.environ["MF_COST_FILE"] = str(working_cost)
            for case in cases:
                group = case["series_group"]
                if group not in models:
                    before = json.loads(working_cost.read_text())
                    start = time.perf_counter()
                    models[group] = _calibration.calibrate_costs(args.n, gc._CAL_TEMPLATES, group=group)
                    elapsed = time.perf_counter() - start
                    after = json.loads(working_cost.read_text())
                    added = {k: v for k, v in after.items() if k not in before or before[k] != v}
                    report["cost_models"].append(dict(
                        n=args.n, series_group=group, calibrate_costs_call_seconds=elapsed,
                        source="fresh_calibration" if added else "seed_or_process_cache",
                        new_or_changed_temporary_records=added, model=models[group].to_dict()))
                result = audit_case(case, args, gc, mf, models[group], signals, noises)
                report["cases"].append(result)
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
                print(json.dumps(dict(
                    profile=case["profile_sha256"], window=case["window"],
                    current=result["selected"]["measured_cost"]["chain"],
                    flop=result["selected"]["flop"]["chain"],
                    estimated_ratio=result["estimated_regret"]["ratio_to_current_choice"],
                    coverage=result["current_model_choice_in_flop_top_k"])), flush=True)
    finally:
        if old_cost is None:
            os.environ.pop("MF_COST_FILE", None)
        else:
            os.environ["MF_COST_FILE"] = old_cost
    report["timing_note"] = (
        "Exclusive top-level phases: calibrate_costs calls include cache loading or synthetic "
        "calibration; signal/noise calls include generation; enumeration builds shared feasible "
        "candidates; pricing only ranks cached candidates. These are setup audit durations, "
        "not calibrated kernel throughput. Zero draw time means exact local reuse.")
    report["total_phase_seconds"] = {
        "calibrate_costs_calls": sum(m["calibrate_costs_call_seconds"] for m in report["cost_models"]),
        **{key: sum(c["timing_seconds"][key] for c in report["cases"])
           for key in report["cases"][0]["timing_seconds"]}}
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
