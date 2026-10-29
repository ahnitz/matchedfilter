"""tools/prodlen.py's log parser and summary, on a captured log.

tests/data/prodlen_ladder_gpu.log is the log of one ladder process run through the tool's
hook: main a7df139e on dev2's Radeon 8060S, 2 tops x 10 segments, --pipeline --pure, no
MF_COST_FILE (paths shortened to /tree, /data and /runs). Every number asserted here was
counted in that log by hand, not taken from the parser.

The first version of the parser counted the calls a joint trial's round makes inside a
batch (it replays sub-batches through filter_series_many) as the ladder's own fine
batches: 39 for 2 tops x 10 segments, which put every later lock at the wrong batch.
"""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "prodlen.py"
LOG = Path(__file__).resolve().parent / "data" / "prodlen_ladder_gpu.log"
if not TOOL.exists():
    pytest.skip("tools/ is not shipped here", allow_module_level=True)

spec = importlib.util.spec_from_file_location("prodlen", TOOL)
prodlen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prodlen)

LINES = LOG.read_text().splitlines()
GPU = "('gpu:0 AMD Radeon 8060S Graphics (RADV GFX1151)',)"


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
    assert list(r) == ["VK-SUBGROUP AMD Radeon 8060S Graphics (RADV GFX1151)",
                       "TRIAL bank|gpu:0|2048,4096,model|6|0.001",
                       "GPU-BATCH " + GPU, "GPU-SINGLE " + GPU, "GPU-KERNELS " + GPU]
    vk = r["VK-SUBGROUP AMD Radeon 8060S Graphics (RADV GFX1151)"]
    # measured in subprocesses before the first batch: 32 against the preferred 64
    assert (vk["lock"], vk["nondefault"], vk["lock_at"], vk["open_fine"], vk["played"]) == \
        ("32", True, {"fine": 0, "in": None}, 0, {})
    assert prodlen.where(vk["lock_at"], 10) == "setup"
    bank = r["TRIAL bank|gpu:0|2048,4096,model|6|0.001"]
    assert (bank["lock"], bank["nondefault"], bank["lock_at"], bank["open_fine"], bank["played"]) == \
        ("default", False, {"fine": 3, "in": "fine"}, 3, {"fine": 3})
    assert [l for l, _ in bank["drops"]] == ["n=4096", "n=model"]
    batch = r["GPU-BATCH " + GPU]
    # made in the follow-ups after fine batch 1, played fine batches 4-13, locked in 13
    assert (batch["lock"], batch["lock_at"], batch["open_fine"], batch["played"], batch["played_nondefault"]) == \
        ("default", {"fine": 13, "in": "fine"}, 12, {"fine": 10}, 10)
    assert batch["confirms"] == [("fuse=0", {"fine": 8, "in": "fine"})]
    assert [l for l, _ in batch["drops"]] == ["interleave=3", "fuse=0"]
    assert prodlen.where(batch["lock_at"], 10, 2) == "fine 13 (top 2 seg 3, steady)"
    single = r["GPU-SINGLE " + GPU]
    assert (single["lock"], single["lock_at"], single["open_fine"], single["played"]) == \
        ("default", {"fine": 3, "in": "follow"}, 2, {"follow": 3})
    assert prodlen.where(single["lock_at"], 10, 2) == "fine 3 follow-ups (top 1 seg 3, steady)"
    kern = r["GPU-KERNELS " + GPU]
    assert (kern["lock"], kern["lock_at"], kern["open_fine"], kern["played"], len(kern["drops"])) == \
        ("default", {"fine": 16, "in": "fine"}, 12, {"fine": 3}, 10)
    assert all(row["after_fine"] == 20 - row["lock_at"]["fine"] for row in r.values())


def test_offline_screens_are_listed_apart_from_the_trials():
    parsed, r = rows()
    got = [(x["kind"], x["band"], x["label"], x["alt"], x["at"]["fine"]) for x in parsed["screens"]]
    assert [g[:2] for g in got] == [("coarse", 64), ("coarse", 128), ("coarse", 256), ("coarse", 512),
                                    ("coarse", 1024), ("gateway", 256), ("gateway", 512),
                                    ("gateway", 1024), ("coarse", 2048)]
    assert got[4][2:] == ("tierb_1024_c16t2w@64", "tierb_1024_c16t4w@64", 0)   # before any batch
    assert all(g[4] == 0 for g in got) and not any(w.startswith(("coarse", "gateway")) for w in r)


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


def _process(d, order, name, lines=LINES, rc=0):
    tag = "%02d_%s" % (order + 1, name)
    (d / (tag + ".log")).write_text("\n".join(lines) + "\n")
    (d / (tag + ".json")).write_text(json.dumps(dict(
        meta=dict(args=dict(tops=2, segments=10, warmup=2)),
        first_segment_s=dict(prep=28.7, wall=1.2), steady_s=dict(wall=1.8),
        steady_samples=dict(wall=[0.1] * 18), templates_in_real_time=dict(total=3.0e7),
        counts=dict(fine_triggers=1413, asym_calls=311))))
    (d / (tag + ".meta.json")).write_text(json.dumps(dict(
        tag=tag, tree_name=name, tree="/tree", order=order, wall=34.0, user=19.1, sys=10.4, rc=rc,
        tops=2, segments=10, start="2026-10-29 14:22:00", load_start=[7.8, 7.0, 6.3],
        load_end=[7.2, 7.0, 6.3], load_trace=[[10.0, 7.3], [20.0, 7.9]])))


def test_a_run_directory_is_summarised_and_checked(tmp_path):
    for order, name in enumerate(prodlen.abba(1)):
        _process(tmp_path, order, name)
    S = prodlen.summarise(tmp_path)
    assert [p["tag"] for p in S["processes"]] == ["01_base", "02_new"]
    assert all(ok for _, ok, _ in S["checks"]), S["checks"]
    P = S["pooled"]
    assert all(e["ratio"] == 1.0 and e["pairs"] == [1.0] for e in P["metrics"].values())
    assert P["per_top"]["median"]["base"] == pytest.approx([0.9, 0.9])
    assert P["nondefault"] == {k: dict(locks=1, processes=1, open_at_end=0) for k in ("base", "new")}
    assert P["trials"]["GPU-BATCH " + GPU]["new"]["lock_fine"] == 13
    assert P["screens"]["coarse 1024"] == {k: {"tierb_1024_c16t2w@64 then tierb_1024_c16t4w@64": 1}
                                           for k in ("base", "new")}
    assert prodlen.abba(2) == ["base", "new", "new", "base"]


def test_a_process_that_did_not_finish_fails_its_checks(tmp_path):
    _process(tmp_path, 0, "base")
    _process(tmp_path, 1, "new", lines=LINES[:150], rc=-9)
    checks = {name: ok for name, ok, _ in prodlen.summarise(tmp_path)["checks"]}
    assert checks["01_base exit"] and checks["01_base fine batches"]
    assert not checks["02_new exit"] and not checks["02_new fine batches"]
