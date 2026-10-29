#!/usr/bin/env python3
"""jobs.py JOBS.json INDEX.jsonl CORES: run a list of jobs, one per core at a time.

JOBS.json is a list of {"tag", "cmd": [...], "env": {...}, "log": path}; each job runs as
`taskset -c <core> cmd` with the environment updated by env, its output in log. CORES is a
comma list (e.g. 28,29,30,31). Every job's core, start and end times, load averages at start
and end, wall time and exit status are appended to INDEX.jsonl. Jobs start in list order.
"""
import json, os, subprocess, sys, time
jobs = json.load(open(sys.argv[1])); index = sys.argv[2]
cores = [int(c) for c in sys.argv[3].split(",")]
free, running = list(cores), {}
def finish(p):
    core, job, t0, l0, f = running.pop(p)
    f.close()
    rec = dict(tag=job["tag"], core=core, start=t0, end=time.time(), wall=time.time() - t0,
               load_start=l0, load_end=list(os.getloadavg()), rc=p.returncode, host=os.uname().nodename)
    with open(index, "a") as out:
        out.write(json.dumps(rec) + "\n")
    print("%s core %d rc=%d wall %.1f load %.1f->%.1f" % (job["tag"], core, p.returncode, rec["wall"],
                                                           l0[0], rec["load_end"][0]), flush=True)
    free.append(core)
for job in jobs:
    while not free:
        for p in list(running):
            if p.poll() is not None:
                finish(p)
        time.sleep(0.2)
    core = free.pop(0)
    env = dict(os.environ); env.update(job.get("env", {}))
    f = open(job["log"], "w")
    p = subprocess.Popen(["taskset", "-c", str(core)] + job["cmd"], env=env, stdout=f, stderr=subprocess.STDOUT)
    running[p] = (core, job, time.time(), list(os.getloadavg()), f)
while running:
    for p in list(running):
        if p.poll() is not None:
            finish(p)
    time.sleep(0.2)
print("ALLDONE", flush=True)
