# The joint trial's settle, before and after, 2026-10-30

`rounds.jsonl.gz` holds the A/A rounds of 24 short test27 ladders per GPU (dev2, dev3, dev4;
`--tops 1 --segments 4`, one at a time, as the collection's `gshort` set) with the joint
round's settle to a steady time (`time_domain._settle`), on b706836f plus that change. The
rounds before are the collection's `gshort` set (`../rounds.jsonl.gz`). `report.md` is:

```bash
M=docs/measurements/trial-aa-gpu-20261030
G=(); for m in dev2 dev3 dev4; do
  G+=("$m-before=$M/rounds.jsonl.gz@machine=$m&kind=joint&set=gshort" "$m-after=$M/settle/rounds.jsonl.gz@machine=$m&kind=joint"); done
python tools/trial_power.py "${G[@]}" --nsim 20000 --seed 1 --out $M/settle/report.md
```

The order tables come from `../harness/bykind.py` and `../harness/realorder.py`. The runs
were the collection's harness scripts (`../harness/remote_gpu_aa.sh`, `local_gpu_aa.sh`);
all 72 jobs exited with status 0. The run-by-run logs that located the cause (a round's
first use of a configuration against its second) came from a scratch build that also
logged every play's runs; they are summarised on the page, not kept.
