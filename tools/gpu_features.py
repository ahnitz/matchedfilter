#!/usr/bin/env python3
"""What the library knows about a GPU, and what its backend declares it can do (stage U0).

Prints (and with --json writes) for one device:
  * device: the matchedfilter device entry (name, backend, arch);
  * properties: the hardware facts the backend's Context records (limits, subgroup sizes,
    queues, ...) -- the inputs a feature-keyed decision can use today;
  * capabilities: the class-level flags the shared layers test (real_series, forward_rows,
    supports_replay, ...). Under stage U these become universal (deleted) or hardware
    features; this file is the "before" picture.

    python tools/gpu_features.py --device gpu:0 --json features.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "python"))


def _plain(v):
    if isinstance(v, (bool, int, float, str)) or v is None:
        return v
    if isinstance(v, (tuple, list)) and all(isinstance(x, (bool, int, float, str)) for x in v):
        return list(v)
    if hasattr(v, "value") and isinstance(getattr(v, "value"), (int, float)):
        return v.value
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--device", default="gpu:0")
    ap.add_argument("--json")
    a = ap.parse_args()
    import matchedfilter as mf
    from matchedfilter.device import parse
    d = parse(a.device)
    plan = mf.MatchedFilter(1024, ndata=1, ntemplates=1, device=a.device)
    ctx = plan._gpu
    if ctx is None:
        raise SystemExit("%s is not a GPU" % a.device)
    cls = type(ctx)
    caps = {}
    for klass in reversed(cls.__mro__):
        for k, v in vars(klass).items():
            if k.startswith("_") or callable(v) or isinstance(v, (property, staticmethod,
                                                                   classmethod)):
                continue
            pv = _plain(v)
            if pv is not None:
                caps[k] = pv
    handles = {"command_pool", "device", "instance", "physical", "queue", "queue_family",
               "timing_log", "ctx", "cuda", "o", "stream"}
    props = {}
    for k, v in vars(ctx).items():
        if k.startswith("_") or k in caps or k in handles:
            continue
        pv = _plain(v)
        if pv is not None and not isinstance(pv, str) or k in ("name", "device_name"):
            props[k] = pv
    out = dict(device=dict(name=d.name, backend=d.backend, arch=list(getattr(d, "arch", ()) or ()),
                           is_software=d.is_software),
               context_class="%s.%s" % (cls.__module__, cls.__name__),
               properties=dict(sorted(props.items())), capabilities=dict(sorted(caps.items())))
    print(json.dumps(out, indent=1))
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
