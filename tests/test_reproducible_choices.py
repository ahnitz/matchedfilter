"""Two processes sharing MF_COST_FILE make the same measured choices and the same results.

Measured choices (cost models, chain and block-size trials, coarse kernel variants, fused
interleave depths) are each valid, but made afresh per process they differ on noise and
borderline pairs then gate differently. With a cost file a machine makes each once."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent

SCRIPT = r'''
import json, sys
import numpy as np
sys.path.insert(0, sys.argv[1])
import matchedfilter as mf
from matchedfilter import TimeDomainFilterBank
device = sys.argv[2]
rng = np.random.default_rng(5)
counts = list(rng.integers(300, 900, 48))
rate, df = 2048.0, 1.0 / 16
f = np.arange(int(rate / 2 / df) + 1) * df
w = np.where((f > 20) & (f < 900), np.maximum(f, 1.0) ** (-7.0 / 3), 0.0)
taps = []
for c in counts:
    ff = np.fft.rfftfreq(c, 1 / rate)
    amp = np.sqrt(np.interp(ff, f, w))
    h = np.fft.irfft(amp * np.exp(2j * np.pi * rng.random(ff.size)), c)
    taps.append((h / np.linalg.norm(h)).astype(np.float32))
bank = TimeDomainFilterBank(taps, tap_counts=counts, engine='hier', threshold=5.0,
                            false_dismissal=0.001, binsize=256, device=device)
bank.set_reference(w, delta_f=df)
L = 1 << 16
out = []
# Trials persist their samples in MF_COST_FILE and may span processes: a block-size trial
# samples only once its plans' chain and Q15 trials have locked, and on a GPU the chain trial
# takes candidates x (2 settle + samples) whole batches. The test runs processes until no
# trial is left open on file.
for seg in range(20):
    r = np.random.default_rng(100 + seg)
    x = ((r.standard_normal(L) + 1j * r.standard_normal(L)) / np.sqrt(2)).astype(np.complex64)
    x[20000:20400] += 8 * np.exp(1j * np.linspace(0, 30, 400))
    res = TimeDomainFilterBank.filter_series_many([(bank, x, {})])[0]
    out.append([res.template_indices.tolist(), res.sample_indices.tolist(),
                np.round(np.abs(res.snr), 4).tolist()])
print(json.dumps({"last": out[-4:], "layout": bank.chosen_layout,
                  "chains": sorted({str(g.plan._chain) for g in bank._groups if g.is_hier})}))
'''


def _run(device, cost):
    env = dict(os.environ, MF_COST_FILE=str(cost), MF_AUTOTUNE="1", MF_CHAIN_TRIALS="1",
               MF_BLOCK_TRIALS="1", OMP_NUM_THREADS="1")
    p = subprocess.run([sys.executable, "-c", SCRIPT, str(ROOT / "python"), device], env=env,
                       capture_output=True, text=True, timeout=900)
    assert p.returncode == 0, p.stderr[-3000:]
    return json.loads(p.stdout.strip().splitlines()[-1])


def _trial_records(rec):
    """The trial locks on file (what a process reads back), without timings."""
    out = {}
    for k, v in rec.items():
        if k.startswith(("block-trial|", "chain-trial|", "q15-trial|")) and not k.endswith("|batches"):
            out[k] = (v.get("winner"), tuple(v.get("chain", ())), v.get("q15"), v.get("rechecked"))
    return out


def _open_trials(rec):
    """Trials on file that have samples but no lock: a block-size trial without a winner, or a
    chain trial's batch samples without the chain's lock."""
    open_ = [k for k, v in rec.items() if k.startswith("block-trial|") and "winner" not in v
             and any(v.get("samples", {}).values())]
    open_ += [k for k, v in rec.items() if k.endswith("|batches") and any(v.get("samples", {}).values())
              and "chain" not in rec.get(k[:-len("|batches")], {})]
    return open_


@pytest.mark.parametrize("device", ["cpu", "gpu:0"])
def test_two_processes_sharing_a_cost_file_agree(device, tmp_path):
    if device != "cpu":
        import matchedfilter as mf
        if not any(str(d) == device for d in mf.devices()):
            pytest.skip("no %s here" % device)
    cost = tmp_path / "costs.json"
    # A block-size trial samples only once the chain and Q15 trials have locked, so it may
    # span processes (its samples persist): run until its lock is on file. From then on
    # every process reads the same choices back.
    # Run until the trial records reach a fixed point: no trial open, and a process changes
    # none of them (a steady-state re-check may reopen a lock once; then it is final).
    prev = None
    for _ in range(10):
        first = _run(device, cost)
        rec = json.loads(cost.read_text())
        now = _trial_records(rec)
        if not _open_trials(rec) and now == prev:
            break
        prev = now
    assert not _open_trials(rec) and now == prev
    second = _run(device, cost)                 # reads them back
    third = _run(device, cost)
    assert second == third                      # reproducible from the file on
    assert second["layout"] == first["layout"] and second["chains"] == first["chains"]
