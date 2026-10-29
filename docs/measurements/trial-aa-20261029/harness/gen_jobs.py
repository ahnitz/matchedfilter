#!/usr/bin/env python3
"""gen_jobs.py SET OUTDIR PY HDIR CAP [BANK PROFILES]: the job list (jobs.py) of one A/A collection set.

Sets:
  eq      the seeded on/off equivalence: 12 pairs of full cap67 replays (replay_calls2.py, K=12)
          from copies of OUTDIR/seed.json, A/A on and off alternating first
  full    24 full cap67 replays (replay_calls2.py K=12), no cost file, A/A on
  offs    one replay per bank offset (aa_replay.py K=12, 2 banks), no cost file, A/A on
  long    one replay per third bank offset (aa_replay.py K=12, 4 banks), MF_TRIAL_ROUNDS=40
  solo    one replay per fourth bank offset (aa_replay.py K=12, 2 banks), run on one core alone
          (the control for this collection's own concurrency)
  ladshort LADN x 6 test27 CPU ladders cut to the trial's segments (--tops 1 --segments 4: the
          same first fine batches, so the same rounds), default schedule
  lad     LADN (env, default 4) test27 CPU ladders at production length, default schedule, then
          LADN at MF_TRIAL_ROUNDS=100
"""
import json, os, sys
SET, OUT, PY, H, CAP = sys.argv[1:6]
BANK, PROF = (sys.argv[6], sys.argv[7]) if len(sys.argv) > 7 else (None, None)
jobs = []
def job(tag, cmd, env=None, aa=True):
    env = dict(env or {})
    if aa:
        env["MF_TRIAL_AA_LOG"] = "%s/%s.jsonl" % (OUT, tag)
    jobs.append(dict(tag=tag, cmd=cmd, env=env, log="%s/%s.log" % (OUT, tag)))
if SET == "eq":
    for i in range(12):
        for aa in ((True, False) if i % 2 == 0 else (False, True)):
            tag = "eq_%s_%02d" % ("aa" if aa else "off", i)
            cf = "%s/%s.cost.json" % (OUT, tag)
            job(tag, ["bash", "-c", "rm -f %s %s.lock; cp %s/seed.json %s; exec %s %s/replay_calls2.py %s 12"
                      % (cf, cf, OUT, cf, PY, H, CAP)], {"MF_COST_FILE": cf}, aa=aa)
elif SET == "full":
    for i in range(24):
        job("full_%02d" % i, [PY, "%s/replay_calls2.py" % H, CAP, "12"])
elif SET == "offs":
    for o in range(323):
        job("offs_%03d" % o, [PY, "%s/aa_replay.py" % H, CAP, "12", str(o), "2"])
elif SET == "solo":
    for o in range(0, 323, 4):
        job("solo_%03d" % o, [PY, "%s/aa_replay.py" % H, CAP, "12", str(o), "2"])
elif SET == "long":
    for o in range(0, 323, 3):
        job("long_%03d" % o, [PY, "%s/aa_replay.py" % H, CAP, "12", str(o), "4"], {"MF_TRIAL_ROUNDS": "40"})
elif SET == "ladshort":
    for i in range(6 * int(os.environ.get("LADN", 4))):
        job("ladshort_%02d" % i, [PY, "tools/ladder.py", "--bank", BANK, "--profiles", PROF, "--device", "cpu",
                                  "--tops", "1", "--segments", "4", "--pipeline", "--pure"],
            {"MF_AUTOTUNE_LOG": "1"})
elif SET == "lad":
    n = int(os.environ.get("LADN", 4))
    for i, rounds in enumerate([None] * n + ["100"] * n):
        tag = "lad_%s_%d" % ("r100" if rounds else "def", i % n)
        env = {"MF_AUTOTUNE_LOG": "1"}
        if rounds:
            env["MF_TRIAL_ROUNDS"] = rounds
        job(tag, [PY, "tools/ladder.py", "--bank", BANK, "--profiles", PROF, "--device", "cpu",
                  "--tops", "27", "--segments", "28", "--pipeline", "--pure",
                  "--out", "%s/%s.json" % (OUT, tag)], env)
json.dump(jobs, open("%s/jobs_%s.json" % (OUT, SET), "w"), indent=0)
print(SET, len(jobs))
