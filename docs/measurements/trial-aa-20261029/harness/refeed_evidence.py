# refeed_evidence.py EVIDENCE.jsonl.gz [--break]: every logged trial's rounds (the candidates' own
# times; the A/A time left out) fed to a fresh _choice.Choice with the logged schedule; after every
# round its winner, dropped arms and confirmation must equal the logged ones, and each process's
# lock must be the refed winner. Prints the counts and every mismatch. With --break, the A/A time
# replaces the preference's (what a leak of the A/A arm into the samples would do): the check
# must then report mismatches, which shows it discriminates.
import gzip, json, sys
from collections import defaultdict, Counter
from matchedfilter import _choice
BREAK = "--break" in sys.argv[2:]
by, locks = defaultdict(list), defaultdict(list)
for line in gzip.open(sys.argv[1], "rt"):
    r = json.loads(line)
    if r["event"] == "round":
        by[(r["_file"], r["pid"], r["key"])].append(r)
    elif r["event"] == "lock":
        locks[(r["_file"], r["pid"], r["key"])].append(r)
trials = rounds = bad = lockbad = 0
phases = Counter()
for k, seq in by.items():
    first = seq[0]
    ch = _choice.Choice(list(first["times"]), minimum=first["minimum"], cap=first["cap"],
                        tie=first["tie"], confirm=True)
    trials += 1
    for r in seq:
        rounds += 1
        phases[r["phase"]] += 1
        assert "A/A" not in r["times"]
        try:
            ch.round({c: r["A/A"] if BREAK and c == r["preference"] else r["times"][c]
                      for c in ch.live()})
        except KeyError:            # the refed contest diverged: it asks for a dropped arm
            bad += 1
            print("DIVERGED", k, r["phase"], r["round"])
            break
        got = (ch.winner, sorted(ch.dropped), ch.confirming)
        want = (r["winner"], r["dropped"], r["confirming"])
        if got != want:
            bad += 1
            print("MISMATCH", k, r["phase"], r["round"], got, want)
    for lk in locks.get(k, ()):
        if ch.winner is not None and lk["value"] != ch.winner:
            lockbad += 1
            print("LOCK MISMATCH", k, lk["value"], ch.winner)
print("trials %d rounds %d (%s) mismatches %d lock mismatches %d; locks %d" % (
    trials, rounds, dict(phases), bad, lockbad, sum(map(len, locks.values()))))
