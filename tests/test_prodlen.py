"""tools/prodlen.py's log parser and summary, on captured logs, and its hook on a CPU script.

tests/data/prodlen_ladder_gpu.log is the log of one ladder process run through the tool's
hook: main a7df139e on dev2's Radeon 8060S, 2 tops x 10 segments, --pipeline --pure, no
MF_COST_FILE (paths shortened to /tree, /data and /runs). tests/data/prodlen_ladder_gpu_prod.log.gz
is one at production length, 27 tops x 28 segments, from the same tree on the same device:
its GPU-BATCH search locked fuse=0 in its first pass and again in the pass around fuse=0.
Both come from the hook of 209224dc, which logged no round timings. Every number asserted
on them here was counted in the logs by hand or with awk, not taken from the parser.

The first version of the parser counted the calls a joint trial's round makes inside a
batch (it replays sub-batches through filter_series_many) as the ladder's own fine
batches: 39 for 2 tops x 10 segments, which put every later lock at the wrong batch. The
second counted a non-default decision once per pass of its search: twice for that fuse=0.
"""
import gzip
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "prodlen.py"
DATA = Path(__file__).resolve().parent / "data"
if not TOOL.exists():
    pytest.skip("tools/ is not shipped here", allow_module_level=True)

spec = importlib.util.spec_from_file_location("prodlen", TOOL)
prodlen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prodlen)

LINES = (DATA / "prodlen_ladder_gpu.log").read_text().splitlines()
with gzip.open(DATA / "prodlen_ladder_gpu_prod.log.gz", "rt") as f:
    PROD = f.read().splitlines()
GPU = "('gpu:0 AMD Radeon 8060S Graphics (RADV GFX1151)',)"
VK = "VK-SUBGROUP AMD Radeon 8060S Graphics (RADV GFX1151)"
BANK = "TRIAL bank|gpu:0|2048,4096,model|6|0.001"


def at(fine, kind, follow):
    return {"fine": fine, "in": kind, "follow": follow}


def rows(lines=LINES):
    parsed = prodlen.parse_log(lines)
    fine = sum(b["kind"] == "fine" for b in parsed["batches"])
    return parsed, {r["what"]: r for r in prodlen.trials(parsed, fine)}


def test_fine_batches_are_the_ladders_own():
    parsed, _ = rows()
    fine = [b for b in parsed["batches"] if b["kind"] == "fine"]
    assert [b["fine"] for b in fine] == list(range(1, 21))          # 2 tops x 10 segments
    assert sum(b["kind"] == "follow" for b in parsed["batches"]) == 20
    # the bank trial's three rounds ran their replays inside the first three fine batches
    assert [b["nested"] for b in fine[:4]] == [7, 6, 6, 0]
    assert sum(b["nested"] for b in parsed["batches"]) == 19
    assert parsed["exit"] and parsed["start"]["matchedfilter"] == "/tree/python/matchedfilter/__init__.py"


def test_every_lock_and_the_batch_it_locked_at():
    _, r = rows()
    assert list(r) == [VK, BANK, "GPU-BATCH " + GPU, "GPU-SINGLE " + GPU, "GPU-KERNELS " + GPU]
    vk = r[VK]
    # measured in subprocesses before the first batch: 32 against the preferred 64
    assert (vk["lock"], vk["nondefault"], vk["lock_at"], vk["open_fine"], vk["rounds"], vk["played"]) == \
        ("32", True, at(0, None, 0), 0, 0, {})
    assert prodlen.where(vk["lock_at"], 10) == "setup"
    bank = r[BANK]
    assert (bank["lock"], bank["nondefault"], bank["lock_at"], bank["open_fine"], bank["played"]) == \
        ("default", False, at(3, "fine", 2), 3, {"fine": 3})
    assert [l for l, _ in bank["drops"]] == ["n=4096", "n=model"]
    batch = r["GPU-BATCH " + GPU]
    # made in the follow-ups after fine batch 1, played fine batches 4-13, locked in 13
    assert (batch["lock"], batch["lock_at"], batch["open_fine"], batch["rounds"], batch["played"],
            batch["ran_nondefault"]) == ("default", at(13, "fine", 12), 12, 10, {"fine": 10}, 10)
    assert batch["confirms"] == [("fuse=0", at(8, "fine", 7))]
    assert [l for l, _ in batch["drops"]] == ["interleave=3", "fuse=0"]
    assert prodlen.where(batch["lock_at"], 10, 2) == "fine 13 (top 2 seg 3, steady)"
    single = r["GPU-SINGLE " + GPU]
    assert (single["lock"], single["lock_at"], single["open_fine"], single["played"]) == \
        ("default", at(3, "follow", 3), 2, {"follow": 3})
    assert prodlen.where(single["lock_at"], 10, 2) == "fine 3 follow-ups (top 1 seg 3, steady)"
    kern = r["GPU-KERNELS " + GPU]
    assert (kern["lock"], kern["lock_at"], kern["open_fine"], kern["played"], len(kern["drops"])) == \
        ("default", at(16, "fine", 15), 12, {"fine": 3}, 10)
    assert all(row["after_fine"] == 20 - row["lock_at"]["fine"] for row in r.values())
    assert all(row["base"] is None and row["search"] == row["what"] for row in r.values())


def test_a_search_is_one_decision_however_many_passes():
    parsed = prodlen.parse_log(PROD)
    assert sum(b["kind"] == "fine" for b in parsed["batches"]) == 756
    passes = prodlen.trials(parsed, 756)
    S = prodlen.searches(passes)
    assert [d["what"] for d in S] == [VK, BANK, "GPU-BATCH " + GPU, "GPU-SINGLE " + GPU, "GPU-KERNELS " + GPU]
    assert [len(d["passes"]) for d in S] == [1, 1, 2, 1, 1]
    batch = S[2]
    first, around = batch["passes"]
    # pass 1: fuse=0 picked for confirmation in fine batch 8, locked in 16 after 13 rounds
    assert (first["lock"], first["nondefault"], first["lock_at"], first["open_fine"], first["rounds"]) == \
        ("fuse=0", True, at(16, "fine", 15), 15, 13)
    assert first["confirms"] == [("fuse=0", at(8, "fine", 7))]
    # the pass around fuse=0, made in fine batch 16: three rounds, fuse=0 again in 19; both of
    # its arms move fuse, so every round ran a non-default configuration
    assert (around["what"], around["base"], around["pref"], around["lock"], around["nondefault"]) == \
        ("GPU-BATCH " + GPU + " around fuse=0", "fuse=0", "fuse=0", "fuse=0", True)
    assert (around["lock_at"], around["open_fine"], around["rounds"], around["ran_nondefault"]) == \
        (at(19, "fine", 18), 4, 3, 3)
    assert (batch["lock"], batch["nondefault"], batch["lock_at"], batch["first_nondefault_at"]) == \
        ("fuse=0", True, at(19, "fine", 18), at(16, "fine", 15))
    # open from fine batch 2 (made in fine 1's follow-ups) to 19; rounds in fine 4-19
    assert (batch["open_fine"], batch["rounds"], batch["played"], batch["after_fine"]) == (18, 16, {"fine": 16}, 737)
    # one non-default decision, though two passes locked it
    assert sum(d["nondefault"] for d in S) == 1 and sum(p["nondefault"] for p in passes) == 2
    assert [d["lock"] for d in S] == ["64", "default", "fuse=0", "default", "default"]
    assert [d["lock_at"]["fine"] for d in S] == [0, 3, 19, 3, 26]
    assert prodlen.lock_check(parsed) == (True, "6 locks by the hook, 6 lock lines")


def test_a_search_cut_short_is_open_at_its_base():
    # the capture up to the pass around fuse=0's lock line: that pass is open, and fuse=0
    # (its base) is what the search runs between its rounds
    cut = next(i for i, l in enumerate(PROD) if l.startswith("[MF_AUTOTUNE] GPU-BATCH") and " around fuse=0 -> " in l)
    parsed = prodlen.parse_log(PROD[:cut])
    S = prodlen.searches(prodlen.trials(parsed, 19))
    batch = S[2]
    assert (batch["lock"], batch["base"], batch["base_nondefault"], batch["nondefault"], batch["lock_at"]) == \
        (None, "fuse=0", True, False, None)
    assert prodlen._decision(batch) == "OPEN at fuse=0"
    assert prodlen._decision(S[4]) == "OPEN"                       # GPU-KERNELS, at default


def test_a_round_ran_a_non_default_arm_only_if_one_was_timed_apart():
    first = dict(what="TRIAL x", pref="default")
    # Choice.play runs arms that run alike once: n=model with default's timing ran default
    assert prodlen.ran_nondefault(first, dict(arms=["default", "n=4096", "n=model"], times=[2.0, 2.1, 2.0]))
    assert not prodlen.ran_nondefault(first, dict(arms=["default", "n=model"], times=[2.0, 2.0]))
    assert prodlen.ran_nondefault(first, dict(arms=["default", "n=model"], times=None))   # an older hook
    vk = dict(what="VK", pref="64")
    assert not prodlen.ran_nondefault(vk, dict(arms=["64", "32"], times=[1.0, 1.0]))
    around = dict(what="TRIAL x around fuse=0", pref="fuse=0")
    assert prodlen.ran_nondefault(around, dict(arms=["fuse=0", "fuse=0,interleave=3"], times=[1.0, 1.0]))


def test_follow_ups_belong_to_their_own_segment():
    assert prodlen.where(at(3, "follow", 3), 10, 2) == "fine 3 follow-ups (top 1 seg 3, steady)"
    # --depth 2: segment 3's follow-ups run after fine batch 4 began
    assert prodlen.where(at(4, "follow", 3), 10, 2) == "fine 4, follow-ups of fine 3 (top 1 seg 3, steady)"
    assert prodlen.where(at(11, "follow", 10), 10, 2) == "fine 11, follow-ups of fine 10 (top 1 seg 10, steady)"
    assert prodlen.where(at(11, None, 11), 10, 2) == "fine 11 +between (top 2 seg 1)"


def test_offline_screens_and_model_picks_are_listed_apart_from_the_trials():
    parsed, r = rows()
    got = [(x["kind"], x["band"], x["label"], x["alt"], x["at"]["fine"]) for x in parsed["screens"]]
    assert [g[:2] for g in got] == [("coarse", 64), ("coarse", 128), ("coarse", 256), ("coarse", 512),
                                    ("coarse", 1024), ("gateway", 256), ("gateway", 512),
                                    ("gateway", 1024), ("coarse", 2048)]
    assert got[4][2:] == ("tierb_1024_c16t2w@64", "tierb_1024_c16t4w@64", 0)   # before any batch
    assert all(g[4] == 0 for g in got) and not any(w.startswith(("coarse", "gateway")) for w in r)
    chains = [p for k, p in parsed["models"] if k == "CHAIN"]
    blocks = [p for k, p in parsed["models"] if k == "BLOCK"]
    assert chains == ["n=2048 model=(256, 512)", "n=4096 model=(512, 1024)"] + ["n=2048 model=(256, 512)"] * 3
    assert len(blocks) == 27 and all(b.endswith("legacy n=2048 -> n=2048") for b in blocks)
    assert "templates=80 longest=295 legacy n=2048 -> n=2048" in blocks
    assert prodlen._picks(blocks) == "n=2048 x27"


def test_a_killed_process_leaves_its_trials_open():
    # the log up to (not including) GPU-BATCH's lock line: fine batches 1-13 begun
    cut = next(i for i, l in enumerate(LINES) if l.startswith("[MF_AUTOTUNE] GPU-BATCH") and " -> " in l)
    parsed, r = rows(LINES[:cut])
    assert sum(b["kind"] == "fine" for b in parsed["batches"]) == 13 and not parsed["exit"]
    batch = r["GPU-BATCH " + GPU]
    assert (batch["lock"], batch["lock_at"], batch["open_fine"], batch["nondefault"]) == (None, None, 12, False)
    assert r["GPU-KERNELS " + GPU]["lock"] is None


def test_every_lock_is_seen_by_the_hook_and_in_the_librarys_log():
    ok, text = prodlen.lock_check(prodlen.parse_log(LINES))
    assert ok and text == "5 locks by the hook, 5 lock lines"
    dropped = [l for l in LINES if not (l.startswith("[MF_AUTOTUNE] GPU-SINGLE") and " -> " in l)]
    ok, text = prodlen.lock_check(prodlen.parse_log(dropped))
    assert not ok and "hook only" in text
    unhooked = [l for l in LINES if not ('"ev": "lock"' in l and '"id": 3,' in l)]
    ok, text = prodlen.lock_check(prodlen.parse_log(unhooked))
    assert not ok and "log only" in text


def _process(d, order, name, lines=LINES, rc=0, tree="/tree", tops=2, segments=10, report=True, **m):
    """Write one recorded process into run directory d: its log, a ladder report (unless
    report is False: a killed ladder writes none) and the runner's record, with the metrics
    in m over the defaults here."""
    v = dict(wall=34.0, user=19.1, sys=10.4, prep=28.7, warm=1.2, steady=1.8, tirt=3.0e7,
             samples=[0.1] * 18, trace=[[10.0, 7.6], [20.0, 7.3], [30.0, 7.9], [40.0, 7.5]])
    v.update(m)
    tag = "%02d_%s" % (order + 1, name)
    (d / (tag + ".log")).write_text("\n".join(lines) + "\n")
    if report:
        (d / (tag + ".json")).write_text(json.dumps(dict(
            meta=dict(args=dict(tops=tops, segments=segments, warmup=2)),
            first_segment_s=dict(prep=v["prep"], wall=v["warm"]), steady_s=dict(wall=v["steady"]),
            steady_samples=dict(wall=v["samples"]), templates_in_real_time=dict(total=v["tirt"]),
            counts=dict(fine_triggers=1413, asym_calls=311))))
    (d / (tag + ".meta.json")).write_text(json.dumps(dict(
        tag=tag, tree_name=name, tree=tree, order=order, wall=v["wall"], user=v["user"], sys=v["sys"],
        rc=rc, tops=tops, segments=segments, start="2026-10-29 14:22:00", load_start=[7.8, 7.0, 6.3],
        load_end=[7.2, 7.0, 6.3], load_trace=v["trace"])))


def test_the_pooled_comparison_is_new_over_base_by_median_and_by_pair(tmp_path):
    # each process's numbers differ, and each top's steady samples differ from the other
    # top's: an inverted ratio, a mismatched pair or a strided per-top split changes them
    spec = [("base", dict(wall=34.0, user=19.0, steady=3.6, tirt=3.0e7, samples=[0.1] * 9 + [0.3] * 9)),
            ("new", dict(wall=30.0, user=18.0, steady=2.7, tirt=4.0e7, samples=[0.2] * 9 + [0.1] * 9)),
            ("new", dict(wall=27.0, user=16.0, steady=6.3, tirt=3.5e7, samples=[0.4] * 9 + [0.3] * 9)),
            ("base", dict(wall=40.0, user=21.0, steady=7.2, tirt=2.0e7, samples=[0.3] * 9 + [0.5] * 9))]
    assert [n for n, _ in spec] == prodlen.abba(2)
    for order, (name, m) in enumerate(spec):
        _process(tmp_path, order, name, **m)
    S = prodlen.summarise(tmp_path)
    assert [p["tag"] for p in S["processes"]] == ["01_base", "02_new", "03_new", "04_base"]
    assert all(ok for _, ok, _ in S["checks"]), S["checks"]
    for p, want in zip(S["processes"], [[0.9, 2.7], [1.8, 0.9], [3.6, 2.7], [2.7, 4.5]]):
        assert p["per_top"] == pytest.approx(want)
        assert p["load_range"] == [7.3, 7.9]
    M = S["pooled"]["metrics"]
    assert M["total"]["median"] == {"base": 37.0, "new": 28.5}
    assert M["total"]["ratio"] == pytest.approx(28.5 / 37.0)
    assert M["total"]["pairs"] == pytest.approx([30.0 / 34.0, 27.0 / 40.0])
    assert M["user"]["ratio"] == pytest.approx(17.0 / 20.0)
    assert M["user"]["pairs"] == pytest.approx([18.0 / 19.0, 16.0 / 21.0])
    assert M["steady"]["ratio"] == pytest.approx(4.5 / 5.4)
    assert M["steady"]["pairs"] == pytest.approx([2.7 / 3.6, 6.3 / 7.2])
    assert M["tirt"]["ratio"] == pytest.approx(3.75e7 / 2.5e7)
    assert M["tirt"]["pairs"] == pytest.approx([4.0 / 3.0, 3.5 / 2.0])
    assert M["sys"]["ratio"] == 1.0 and M["sys"]["pairs"] == [1.0, 1.0]
    per = S["pooled"]["per_top"]
    assert per["median"]["base"] == pytest.approx([1.8, 3.6])
    assert per["median"]["new"] == pytest.approx([2.7, 1.8])
    assert per["ratio"] == pytest.approx([1.5, 0.5])
    assert S["pooled"]["screens"]["coarse 1024"] == {k: {"tierb_1024_c16t2w@64 then tierb_1024_c16t4w@64": 2}
                                                     for k in ("base", "new")}
    assert prodlen.abba(1) == ["base", "new"] and prodlen.abba(3) == ["base", "new", "new", "base", "base", "new"]


def test_the_pooled_comparison_counts_a_search_once(tmp_path):
    _process(tmp_path, 0, "base", lines=PROD, tops=27, segments=28, samples=[0.01] * 729)
    _process(tmp_path, 1, "new")
    S = prodlen.summarise(tmp_path)
    assert all(ok for _, ok, _ in S["checks"]), S["checks"]
    P = S["pooled"]
    # base: GPU-BATCH's fuse=0, which two passes locked; new: VK-SUBGROUP's 32
    assert P["nondefault"] == {k: dict(decisions=1, processes=1, open_at_end=0, open_nondefault=0)
                               for k in ("base", "new")}
    assert not any(" around " in w for w in P["trials"])
    batch = P["trials"]["GPU-BATCH " + GPU]
    assert batch["base"] == dict(locks={"fuse=0": 1}, nondefault=1, processes=1, passes=2, lock_fine=19, open_fine=18)
    assert batch["new"] == dict(locks={"default": 1}, nondefault=0, processes=1, passes=1, lock_fine=13, open_fine=12)
    assert P["trials"][VK]["base"]["locks"] == {"64": 1} and P["trials"][VK]["new"]["locks"] == {"32": 1}
    chain = P["models"]["CHAIN"]
    assert chain["count"] == {"01_base": 59, "02_new": 5}
    assert chain["distinct"] == {"base": 1, "new": 1, "all": 2}
    assert chain["picks"]["base"] == "n=2048 model=(256, 512) x58, n=4096 model=(512, 1024) x1"
    assert P["models"]["BLOCK"]["count"] == {"01_base": 27, "02_new": 27}
    text = "\n".join(prodlen.format_pooled(P))
    assert "base non-default decisions 1 (one per search; in 1 of 1 processes)" in text
    # VK-SUBGROUP times its sizes in subprocesses and locks without a Choice.round
    vk = [l for l in prodlen.format_process(S["processes"][1]) if l.lstrip().startswith("VK-SUBGROUP")]
    assert len(vk) == 1 and "played 0 batches" in vk[0] and "its arms timed outside Choice.round" in vk[0]


def test_killed_processes_leave_their_searches_open(tmp_path):
    # base: the production capture (GPU-BATCH's fuse=0) and the short one (VK-SUBGROUP's 32);
    # new: the production capture killed before the pass around fuse=0 locked (open at
    # fuse=0), and killed before the first pass locked (open at default). Neither new
    # process made a non-default decision; both left GPU-BATCH and GPU-KERNELS open.
    first = next(i for i, l in enumerate(PROD) if l.startswith("[MF_AUTOTUNE] GPU-BATCH")
                 and " -> fuse=0  " in l and " around " not in l)
    around = next(i for i, l in enumerate(PROD) if l.startswith("[MF_AUTOTUNE] GPU-BATCH")
                  and " around fuse=0 -> " in l)
    _process(tmp_path, 0, "base", lines=PROD, tops=27, segments=28, samples=[0.01] * 729)
    _process(tmp_path, 1, "new", lines=PROD[:around], rc=-9, report=False, tops=27, segments=28)
    _process(tmp_path, 2, "new", lines=PROD[:first], rc=-9, report=False, tops=27, segments=28)
    _process(tmp_path, 3, "base")
    S = prodlen.summarise(tmp_path)
    P = S["pooled"]
    assert P["nondefault"]["base"] == dict(decisions=2, processes=2, open_at_end=0, open_nondefault=0)
    assert P["nondefault"]["new"] == dict(decisions=0, processes=0, open_at_end=4, open_nondefault=1)
    assert P["trials"]["GPU-BATCH " + GPU]["new"]["locks"] == {"OPEN at fuse=0": 1, "OPEN": 1}
    assert P["trials"]["GPU-KERNELS " + GPU]["new"]["locks"] == {"OPEN": 2}
    assert P["metrics"]["steady"]["values"]["new"] == [None, None]
    checks = {name: ok for name, ok, _ in S["checks"]}
    assert not checks["02_new exit"] and not checks["03_new exit"] and checks["01_base exit"]
    text = "\n".join(prodlen.format_pooled(P))
    assert "new  non-default decisions 0 (one per search; in 0 of 2 processes); open at the end 4 (1 at" in text


def test_a_process_that_did_not_finish_or_ran_another_tree_fails_its_checks(tmp_path):
    _process(tmp_path, 0, "base")
    _process(tmp_path, 1, "new", lines=LINES[:150], rc=-9, report=False)
    _process(tmp_path, 2, "new", tree="/elsewhere")
    _process(tmp_path, 3, "base", samples=[0.1] * 17)
    _process(tmp_path, 4, "base", rc=-11)               # crashed at exit, after its report
    _process(tmp_path, 5, "new")
    checks = {name: ok for name, ok, _ in prodlen.summarise(tmp_path)["checks"]}
    every = ("exit", "tree", "fine batches", "follow-up batches", "steady series", "locks")
    assert all(checks["01_base " + c] and checks["06_new " + c] for c in every)
    assert not checks["02_new exit"] and not checks["02_new fine batches"] and not checks["02_new follow-up batches"]
    assert checks["03_new exit"] and not checks["03_new tree"]
    assert checks["04_base exit"] and not checks["04_base steady series"]
    assert not checks["05_base exit"] and all(checks["05_base " + c] for c in every[1:])
    assert checks["processes"]
    lone = tmp_path / "lone"
    lone.mkdir()
    _process(lone, 0, "base")
    checks = {name: ok for name, ok, _ in prodlen.summarise(lone)["checks"]}
    assert checks["01_base exit"] and not checks["processes"]


LADDER = '''"""A stand-in for tools/ladder.py: 12 segments, each a fine batch (a small CPU bank's call)
then its follow-ups (one single-template call, or none in every third segment), with the
measured choices still open played once between segments. An arm runs fast (1 ms) or slow
(25 ms): every contest here is decided by that 25x gap or by exact ties."""
import time

import numpy as np

from matchedfilter import TimeDomainFilterBank, _choice

rng = np.random.default_rng(3)
taps = [t / np.linalg.norm(t) for t in (rng.standard_normal(c).astype(np.float32) for c in (200, 260, 310, 380))]
bank = TimeDomainFilterBank(taps, engine="flat", threshold=5.0, device="cpu")
data = rng.standard_normal(1 << 13).astype(np.float32)


def contest(arms, what, fast, **kw):
    """A choice, and its config: which arms run alike (the arms in `fast`, and the rest)."""
    return _choice.Choice(arms, what=what, **kw), (lambda c: "fast" if c in fast else "slow")


# HELD's lock is stored in MF_COST_FILE by the first run and held from the file by the next
choices = [contest(("default", "h=1"), "HELD", {"h=1"}, store_key="prodlen-test|held"),
           contest(("default", "a=1", "b=1"), "APART", {"a=1"}),     # b=1 runs as default does
           contest(("default", "c=1"), "ALIKE", set()),              # c=1 runs as default does
           contest(("default", "d=1"), "TWIN", {"default"})]
for seg in range(12):
    TimeDomainFilterBank.filter_series_many([(bank, data, {})])
    TimeDomainFilterBank.filter_series_many([(bank, data, {"template_index": seg % 4})] if seg % 3 else [])
    for ch, config in list(choices):
        if ch.winner is None:
            ch.play(lambda c, config=config: time.sleep(0.001 if config(c) == "fast" else 0.025),
                    config=config)
    if len(choices) == 4 and choices[3][0].winner is not None:
        choices.append(contest(("default", "d=1"), "TWIN", {"default"}))   # a second of one description
'''


def _hook_run(tree, cost):
    """Run the stand-in ladder in `tree` through the hook, with MF_COST_FILE=cost: returns
    its parsed log."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(("MF_", "LADDER_"))}
    env.update(MF_AUTOTUNE="0", MF_AUTOTUNE_LOG="1", MF_COST_FILE=str(cost), PYTHONPATH=str(tree / "python"),
               PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    p = subprocess.run([sys.executable, str(TOOL), "hook", str(tree / "tools" / "ladder.py")],
                       env=env, capture_output=True, text=True, timeout=300)
    assert p.returncode == 0, p.stderr[-2000:]
    parsed = prodlen.parse_log(p.stderr.splitlines())
    assert parsed["exit"] and parsed["start"]["matchedfilter"] == str(tree / "python" / "matchedfilter" / "__init__.py")
    return parsed


def test_the_hook_reads_a_trees_choices(tmp_path):
    """The hook on a tree's real _choice.Choice and filter_series_many (the stand-in ladder
    above, run twice: the second run holds HELD's stored lock). One round per segment from
    the first: a choice locks in the segment of its last round, between batches; HELD and
    APART lock at the fifth (paired_choice's minimum: 4 of 5 rounds faster), ALIKE and the
    first TWIN at the third (where can_still_win drops their other arm: none of 3 rounds
    faster, with 7 to come, cannot reach 8 of 10), the second TWIN, made after the first
    locked in segment 3, at the third of its own."""
    tree = tmp_path / "tree"
    (tree / "tools").mkdir(parents=True)
    (tree / "tools" / "ladder.py").write_text(LADDER)
    # The package the tests import (an install's in CI, where the checkout's has no built
    # extension), at the tree's path.
    import matchedfilter
    (tree / "python").mkdir()
    (tree / "python" / "matchedfilter").symlink_to(Path(matchedfilter.__file__).resolve().parent)
    cost = tmp_path / "cost.json"
    parsed = _hook_run(tree, cost)
    kinds = [b["kind"] for b in parsed["batches"]]
    assert kinds == sum((["fine", "empty" if s % 3 == 0 else "follow"] for s in range(12)), [])
    assert [b["fine"] for b in parsed["batches"] if b["kind"] == "fine"] == list(range(1, 13))
    assert prodlen.lock_check(parsed) == (True, "5 locks by the hook, 5 lock lines")
    rows = prodlen.trials(parsed, 12)
    assert [r["what"] for r in rows] == ["HELD", "APART", "ALIKE", "TWIN", "TWIN"]
    held, apart, alike, twin1, twin2 = rows

    def between(k):
        return at(k, None, k)
    # APART's b=1 shares default's one timing in every round it is in, a=1 has its own
    for rnd in parsed["choices"][2]["rounds"]:
        t = dict(zip(rnd["arms"], rnd["times"]))
        assert t["a=1"] != t["default"] and t.get("b=1", t["default"]) == t["default"]
    assert (held["lock"], held["nondefault"], held["lock_at"], held["open_fine"], held["rounds"],
            held["played"], held["ran_nondefault"]) == ("h=1", True, between(5), 5, 5, {"between": 5}, 5)
    assert (apart["lock"], apart["nondefault"], apart["lock_at"], apart["rounds"], apart["ran_nondefault"]) == \
        ("a=1", True, between(5), 5, 5)
    assert apart["drops"] == [("b=1", between(3))]
    # every ALIKE round ran one configuration, the preference's; TWIN's d=1 ran its own
    assert (alike["lock"], alike["lock_at"], alike["rounds"], alike["ran_nondefault"]) == ("default", between(3), 3, 0)
    assert alike["drops"] == [("c=1", between(3))]
    assert (twin1["lock"], twin1["lock_at"], twin1["rounds"], twin1["ran_nondefault"]) == ("default", between(3), 3, 3)
    # each TWIN's drop line goes to the one of that description then open
    assert twin1["drops"] == [("d=1", between(3))] and twin2["drops"] == [("d=1", between(6))]
    assert (twin2["lock_at"], twin2["open_fine"], twin2["rounds"]) == (between(6), 3, 3)
    assert prodlen.where(held["lock_at"], 12) == "fine 5 +between (top 1 seg 5)"
    assert [d["what"] for d in prodlen.searches(rows)] == ["HELD", "APART", "ALIKE", "TWIN", "TWIN"]
    assert json.loads(cost.read_text())["choice|prodlen-test|held"]["value"] == "h=1"

    again = _hook_run(tree, cost)
    assert prodlen.lock_check(again) == (True, "4 locks by the hook, 4 lock lines")
    held = prodlen.trials(again, 12)[0]
    # held from the file at creation: no rounds and no lock, open in none of the 12 batches
    assert (held["held"], held["lock"], held["nondefault"], held["lock_at"], held["open_fine"], held["rounds"]) == \
        ("h=1", "h=1", True, None, 0, 0)
    d = prodlen.searches(prodlen.trials(again, 12))[0]
    assert (d["lock"], d["nondefault"]) == ("h=1", True)
    s = dict(segments=12, warmup=2)
    assert "held from file" in prodlen._decision_line("HELD", d, s)
