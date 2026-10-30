# A/A rounds of the GPU trials, 2026-10-30

`rounds.jsonl.gz` holds every round and lock that `MF_TRIAL_AA_LOG` logged in the collection
that [the GPU trial statistics page](../../trial-statistics-gpu.md) analyses: 3179 records,
from 96 job records. `report.md` was generated from it with:

```bash
E=docs/measurements/trial-aa-gpu-20261030/rounds.jsonl.gz
G=(); for m in dev2 dev3 dev4; do for k in joint gpu-single gpu-kernels; do
  G+=("$m-$k=$E@machine=$m&kind=$k"); done; done
python tools/trial_power.py "${G[@]}" --nsim 100000 --seed 1 --out docs/measurements/trial-aa-gpu-20261030/report.md
```

The tables of the A/A arm's and the real challengers' log ratios by order come from
`harness/bykind.py` and `harness/realorder.py`, each run on `rounds.jsonl.gz`.

## Provenance

The library was at 2b595add (main) on every host. dev3 and dev4 ran the tree shipped by the
fleet helper with the extension built on dev2 (Python 3.13), and read the bank through an
h5py shim. Every process was single-threaded (`OMP_NUM_THREADS=1`), pinned to one core
(dev2 core 12, dev3 and dev4 core 0), and started with a fresh cost file. One ran at a time
per host.

- **dev2**: Ryzen AI MAX+ 395 with a Radeon 8060S (RADV). Another workstream's processes
  ran on other cores; the 1-minute load was 1.4-3.5 at job starts and ends.
- **dev3**: Radeon Graphics (Renoir, RADV). Load 0.1-4.6.
- **dev4**: Iris Xe Graphics (ANV). Load 0.0-0.9.

Each host ran three sets of `tools/ladder.py --device gpu:0 --pipeline --pure` on the test27
production bank with the H1 profiles:

| set | what ran | per host |
|---|---|---|
| `gshort` | `--tops 1 --segments 4` | 24 |
| `glad` | `--tops 9 --segments 28` | 4 |
| `gladlong` | `--tops 9 --segments 28` at `MF_TRIAL_ROUNDS=100` | 4 |

## Harness

`harness/` holds the scripts as they ran. Their paths point at the session's scratch
directory and at the fleet hosts' `~/fleet/data`.

- `remote_gpu_aa.sh` (dev3, dev4) and `local_gpu_aa.sh` (dev2) run one set and write each
  process's log and the job index that the CPU collection's
  [`extract.py`](../trial-aa-20261029/harness/extract.py) reads. That script built
  `rounds.jsonl.gz`.
- `drift.py` and `drift2.py` are the dev3 checks for a clock ramp after an idle gap: a
  single call, and a play of four submissions with host work between them.

## Fields

As in [the CPU collection](../trial-aa-20261029/README.md#fields): `ratios`, `aa_ratio` and
`what` are dropped; `machine`, `set` and `_file` are added; job records carry each process's
core, wall time, load and exit status. All 96 jobs exited with status 0.
