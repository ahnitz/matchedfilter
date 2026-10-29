# A/A rounds of the CPU joint trial, 2026-10-29

`rounds.jsonl.gz` holds every round and lock that `MF_TRIAL_AA_LOG` logged in the collection
that [the trial statistics log](../../trial-statistics.md) analyses. It has 9494 rounds, 1361
locks and 1323 job records. The page's tables are regenerated from it with:

```bash
E=docs/measurements/trial-aa-20261029/rounds.jsonl.gz
G=(); for m in dev2 dev1; do
  G+=("$m-replay=$E@machine=$m&set=eq|full|offs|long" "$m-ladder=$E@machine=$m&set=lad|ladshort"
      "$m-replay-solo=$E@machine=$m&set=solo")
  [ $m = dev2 ] && G+=("dev2-ladder-lowload=$E@machine=dev2&set=qlad|qladshort"
                       "dev2-replay-solo-lowload=$E@machine=dev2&set=qsolo")
done
python tools/trial_power.py "${G[@]}" --nsim 100000 --seed 1 --out docs/measurements/trial-aa-20261029/report.md
```

The exact computations (the current rule and the sign tests, by DP) are deterministic. The
paired t and Wilcoxon rows are simulated with `--seed 1`.

## Provenance

The library was at f634aeae, the A/A diagnostic's commit on a7df139e, for every set (the
low-load sets ran from a later commit of the branch whose `python/` is identical to
f634aeae's). dev1 runs used the tree shipped by the fleet helper and built there. GPUs were
hidden (`VK_ICD_FILENAMES=/nonexistent/icd.json`). Every process was single-threaded
(`OMP_NUM_THREADS=1`), ran without `MF_COST_FILE` unless the set says otherwise, and was
pinned to one core.

- **dev2** is the Ryzen AI MAX+ 395 (Zen 5, AVX-512), cores 28-31, with 4 jobs at a time.
  Those cores are the SMT siblings of cores 12-15. Another workstream was assigned those
  cores, and other processes ran on them during the main collection (14:45-15:53). The
  1-minute load was 11-38 in its rounds (10.5-36 at job starts and ends). The low-load sets
  (16:49-17:10) ran one job at a time on core 28 (the two `qlad` ladders together on cores
  28-29) at load 3-8, most of it another workstream's four processes on cores 24-27.
- **dev1** is the Ryzen 9 5950X (Zen 3, AVX2), cores 8-15, with 8 jobs at a time. Its load
  was 1-8 in the rounds (0.8-9 at job starts and ends), and nearly all of it was these jobs.

| set | what ran | per host |
|---|---|---|
| `eq` | the full cap67 replay (`replay_calls2.py`, 12 calls per bank) from copies of one seeded cost file without locks, A/A on; the A/A-off twins logged nothing | 12 |
| `full` | the full cap67 replay, no cost file | 24 |
| `offs` | the replay started at bank offset 0..322 (the order rotated), 2 banks | 323 |
| `long` | as `offs` at every third offset, 4 banks, `MF_TRIAL_ROUNDS=40` (contests of about 21 rounds) | 108 |
| `solo` | as `offs` at every fourth offset, one job at a time on one core (the control for the collection's own load) | 81 |
| `lad` | the test27 CPU ladder at production length (`tools/ladder.py --device cpu --tops 27 --segments 28 --pipeline --pure`, the production bank and H1 profiles): 4 (dev2) or 8 (dev1) at the default schedule, then as many at `MF_TRIAL_ROUNDS=100` (51-round contests) | 8 / 16 |
| `ladshort` | the same ladder cut to `--tops 1 --segments 4`: the same first fine batches, so the same trial rounds | 24 / 48 |
| `qsolo` | `solo` again at low load (dev2 only) | 81 |
| `qladshort` | `ladshort` at low load, one job at a time (dev2 only) | 24 |
| `qlad` | two `lad` runs at `MF_TRIAL_ROUNDS=100` at low load (dev2 only) | 2 |

The capture is the test67 job's banks, references and series (`tools/setup_capture.py`).

## Harness

`harness/` holds the scripts that ran the collection, as they ran (their paths point at the
session's scratch directory and the fleet host's `~/fleet/wk-r7a-data`):

- `replay_calls2.py` replays a capture (12 calls per bank, in capture order); `aa_replay.py`
  is the same started at a bank offset and limited to some banks. Both import
  `setup_replay.py`, which is `tools/setup_replay.py`.
- `gen_jobs.py` writes each set's job list; `jobs.py` runs a list one job per core at a time
  and records each job's core, wall time, load and exit status; `run_dev2*.sh` and
  `run_dev1*.sh` ran the sets in order.
- `extract.py` built `rounds.jsonl.gz` from the per-process logs (re-run with the low-load
  sets, it reproduces the earlier extract's records exactly).
- `refeed_evidence.py` feeds every logged trial's rounds, the A/A time left out, to a fresh
  `_choice.Choice`. All 9494 rounds (1361 trials) give the logged winner, dropped arms,
  confirmation and lock. With `--break` it uses the A/A time as the preference's, and 640
  rounds then disagree: the check discriminates.
- `mc_choice.py` checks `tools/trial_power.py`'s DP for the current rule (m = 2, with
  confirmation) against 200,000 contests played by the library's own `Choice` on iid draws
  from two groups' nulls: 7.6e-4 ± 0.6e-4 against the DP's 8.0e-4 (an upper bound), and
  8.3e-3 ± 0.2e-3 against 8.4e-3.

## Fields

Round and lock records are as `_choice` writes them (see `docs/environment.md`,
`MF_TRIAL_AA_LOG`), with three changes:

- `ratios`, `aa_ratio` and `what` are dropped, because they can be derived;
  `tools/trial_power.py` derives the ratios from `times` and `A/A`.
- `machine` and `set` are added.
- `_file` (`<machine>/<set>/<job>`) is added, naming the process's own log.

Job records (`event: job`) carry each process's core, wall time, load at its start and end,
and exit status. All 1323 jobs exited with status 0.
