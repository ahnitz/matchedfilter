"""The gate chain's measured choices: the chain trial a hierarchical plan joins (on the CPU
per call, on a GPU per whole batch) and the Q15 screen's paired trial, with the tables
that hold them for the process and the keys their locks are filed under in MF_COST_FILE."""
from . import _choice, _config, _costfile
from ._choice import _AUTOTUNE_LOCK, _log_autotune


#: Batches a GPU chain trial runs a candidate before it takes samples of it: after a switch
#: the ladder's fine stage took 150, 55, then 17 ms for a 17 ms segment, so the third batch
#: is the first sample.
_CHAIN_WARM_BATCHES = 2


def _chain_lock_key(tkey):
    """The chain trial's key in MF_COST_FILE (its record is "choice|" + this)."""
    n, snr, fd, tiers, device = tkey[:5]
    # tkey[5]: present (1) when the direct refine is priced in, which changes what refining
    # costs and so which chain wins (HierarchicalFilter._chain_trial_key).
    direct = tkey[5] if len(tkey) > 5 else None
    return "chain-trial|%d|%g|%g|%d|%s" % (n, snr, fd, tiers, device) + (
        "|direct" if direct is not None else "")


def _chain_str(c):
    return ",".join(str(int(b)) for b in c)


def _parse_chain(s):
    c = tuple(int(b) for b in str(s).split(",") if b)
    return c or None


def _chain_trial(tkey):
    """The chain trial of tkey (caller holds _AUTOTUNE_LOCK): one measured choice
    (_choice.Choice) per key, its candidates the union of the shortlists of the plans that
    join it, the first (the first plan's model chain) the preference. Its samples persist in
    MF_COST_FILE, so a trial longer than a process continues in the next, and it ends at its
    budget whatever runs. On the CPU a sample is one call (s/pair); on a GPU, one whole batch
    (s/unit: every job of a segment, submission to last result), after _CHAIN_WARM_BATCHES
    on the candidate -- judged on what a search pays, host and device, not one call's time."""
    tr = _CHAIN_TRIALS.get(tkey)
    if tr is None:
        if str(tkey[4]).split(":")[0] == "cpu":
            base = _config.get("MF_CHAIN_TRIALS", _CHAIN_TRIALS_PER_CAND)
            budget = (_TRIAL_BUDGET * base, 0)
        else:
            warm = _CHAIN_WARM_BATCHES
            base = _config.get("MF_CHAIN_TRIALS", _CHAIN_BATCH_TRIALS)
            budget = (warm + base, 6)
        tr = _CHAIN_TRIALS[tkey] = _choice.Choice(
            store_key=_chain_lock_key(tkey), what="CHAIN-TRIAL %s" % (tkey,), warmup=0,
            minimum=base, cap=2 * base, budget=budget, persist=True,
            label=_chain_str, parse=_parse_chain)
    return tr


def _stored_chain_lock(tkey, feasible):
    """A chain-trial winner kept in MF_COST_FILE by an earlier process, if this plan can run it
    (`feasible`: every chain the gate model covers for it). Deliberately NOT only when it is
    on this process's shortlist: the lock key is the trial's identity, and in-process every
    plan with the key adopts the winner whatever its own shortlist -- the shortlist is a
    per-process pruning of what to measure (the model's best few for this group's shape),
    not of what is valid. Filtered by it, a group whose shortlist missed the winner ignored
    the lock and the chain varied between processes. Chain trials, like block-size trials
    (time_domain._BlockTrials) and the cost models themselves, are per machine: re-run in
    every process they lock differently on noise, and that was the remaining
    process-to-process variation of a pinned layout (docs/gate-model.md, "Block-size
    trials, round 3")."""
    chain = _choice.stored_lock(_chain_lock_key(tkey), _parse_chain)
    if chain is None or feasible is None:
        return chain                 # the key's lock, whichever plan asks (see _choose_chain)
    return chain if chain in tuple(tuple(c) for c in feasible) else None


def _store_chain_lock(tkey, chain, median=None):
    """Store a chain lock for tkey, as its trial would."""
    path = _costfile._cost_file()
    if path is not None and tkey is not None:
        rec = {"value": _chain_str(chain)}
        if median:
            rec["median"] = {_chain_str(c): float(v) for c, v in median.items()}
        _costfile._store_cost(path, "choice|" + _chain_lock_key(tkey), rec)


def _chain_trial_next(tkey):
    """The candidate a GPU chain trial's next batch runs on every plan of the trial: the
    current one until it has its samples (a switch rebuilds thresholds and uploads, and the
    batches after it are not samples: alternating every batch measured mostly the switching,
    cheapest for the chain with fewest tiers), then the one with the fewest. None once the
    trial has a winner -- by its samples, or by its budget of batches (Choice.tick), which
    every batch counts, sampled or not."""
    with _AUTOTUNE_LOCK:
        tr = _CHAIN_TRIALS.get(tkey)
        if tr is None or tr.winner is not None:
            return None
        warm = _CHAIN_WARM_BATCHES
        cur, run, got0 = _CHAIN_BATCH_RUN.get(tkey, (None, 0, 0))
        # A candidate current for longer than its warm-up and samples (+2) without yielding
        # one cannot or will not run here (a plan that does not switch to it, batches never
        # recorded): it leaves the contest instead of being waited for.
        if cur in tr.live() and len(tr.samples[cur]) == got0 and run > warm + tr.needs(cur) + 2:
            _log_autotune("CHAIN-TRIAL %s: %s yielded no sample in %d batches: dropped",
                          tkey, cur, run)
            tr.drop(cur)
            cur = None
        if tr.tick() is not None:
            return None
        c = tr.pick(stay=cur)
        if c is None:
            tr.expire()                     # every candidate dropped: the preference stands
            return None
        _CHAIN_BATCH_RUN[tkey] = (c, run + 1, got0) if c == cur else (c, 1, len(tr.samples[c]))
        return c


def _chain_trial_pending(tkey, chain, delta):
    """A settled batch of a GPU chain trial started (+1) or finished (-1) on chain."""
    with _AUTOTUNE_LOCK:
        tr = _CHAIN_TRIALS.get(tkey)
        if tr is not None:
            c = tuple(chain)
            tr.pending[c] = tr.pending.get(c, 0) + delta


def _chain_trial_batch(tkey, chain, value):
    """One sample of a GPU chain trial (s/unit of a whole batch with every plan of the
    trial on `chain`). Returns the winner once the trial has one."""
    with _AUTOTUNE_LOCK:
        tr = _CHAIN_TRIALS.get(tkey)
        if tr is None:
            return None
        _log_autotune("CHAIN-TRIAL batch sample %s %.3g", tuple(chain), value)
        return tr.record(tuple(chain), value)


#: A CPU chain trial ends after this many times its per-candidate samples in calls: candidates
#: some live plan never runs -- another process's shortlist, a group that stopped calling --
#: must not keep a trial open for good.
_TRIAL_BUDGET = 3


#: (n, snr, fd, chain, device) -> the Q15 screen's paired trial (_choice.Choice: False, True)
_Q15_TRIALS = {}


#: A Q15 trial ends after this many times its rounds in calls (each call of a plan in the
#: trial counts, paired or not).
_Q15_TRIAL_BUDGET = 8


#: (chain-choice key, chain) -> whether the cost model prices the Q15 screen cheaper
_Q15_MODEL = {}


#: (n, snr, fd, tiers, window, profile signature) -> (model's chain, shortlist)
_CHAIN_CHOICE = {}


#: chain-trial key (HierarchicalFilter._chain_trial_key) -> its _choice.Choice, shared by
#: every plan with the key (_chain_trial)
_CHAIN_TRIALS = {}


#: chain-trial key -> {chain: plans placed on it}, for spreading a CPU trial's plans
_CHAIN_PLACED = {}


#: chain-trial key -> (current candidate, batches run on it, its samples when it became
#: current): a GPU trial's run of batches (_chain_trial_next)
_CHAIN_BATCH_RUN = {}


#: Relative cost margin inside which modelled chains are measured rather than decided by the
#: model. It is the model's demonstrated error: tier costs agreed with the engine counters to
#: ~25% in the consumer.
_CHAIN_MARGIN = 0.30


_CHAIN_SHORTLIST_MAX = 4


#: GPU chain trials measure the model's best three, each over whole batches (see _choose).
_CHAIN_SHORTLIST_GPU = 3


_CHAIN_TRIALS_PER_CAND = 6


#: Batch samples per candidate of a GPU chain trial (a batch is a whole segment's jobs; its
#: first batch on a candidate builds recordings and is not counted).
_CHAIN_BATCH_TRIALS = 4
