#!/usr/bin/env python
"""Capture what a job's matchedfilter setup sees, for replaying the setup without the job.

    CAPDIR=cap python tools/setup_capture.py SCRIPT [ARGS...]

Runs SCRIPT (a pycbc_inspiral_fir, say) with TimeDomainFilterBank hooked and writes into
CAPDIR, for every bank in the order the job makes them:

  * ref%03d.pkl  -- (set_reference args, kwargs), one file per distinct reference;
  * bank%04d.pkl -- (reference index, constructor args, kwargs);
  * call_ref%03d.pkl -- (series, args, kwargs) of the first filter_series call of a bank on
    that reference.

tools/setup_replay.py and tools/setup_breakdown.py replay a capture: every bank built, given
its reference and run on its reference's captured series, in one process.
"""
import hashlib
import itertools
import os
import pickle
import runpy
import sys

import numpy as np

import matchedfilter.time_domain as td


def main():
    out = os.environ["CAPDIR"]
    os.makedirs(out, exist_ok=True)
    refs, info, called, nb = {}, {}, set(), itertools.count()
    init, setref, fs = (td.TimeDomainFilterBank.__init__, td.TimeDomainFilterBank.set_reference,
                        td.TimeDomainFilterBank.filter_series)

    def hooked_init(self, *a, **k):
        info[id(self)] = (a, dict(k))
        return init(self, *a, **k)

    def hooked_set_reference(self, *a, **k):
        r = setref(self, *a, **k)
        if id(self) in info:
            h = hashlib.sha1(np.ascontiguousarray(np.asarray(a[0])).tobytes()).hexdigest()
            if h not in refs:
                refs[h] = len(refs)
                pickle.dump((a, dict(k)), open("%s/ref%03d.pkl" % (out, refs[h]), "wb"))
            ba, bk = info.pop(id(self))
            pickle.dump((refs[h], ba, bk), open("%s/bank%04d.pkl" % (out, next(nb)), "wb"))
            self._cap_ref = refs[h]
        return r

    def hooked_filter_series(self, ser, *a, **k):
        ri = getattr(self, "_cap_ref", None)
        if ri is not None and ri not in called:
            called.add(ri)
            pickle.dump((ser, a, k), open("%s/call_ref%03d.pkl" % (out, ri), "wb"))
        return fs(self, ser, *a, **k)

    td.TimeDomainFilterBank.__init__ = hooked_init
    td.TimeDomainFilterBank.set_reference = hooked_set_reference
    td.TimeDomainFilterBank.filter_series = hooked_filter_series
    sys.argv = sys.argv[1:]
    runpy.run_path(sys.argv[0], run_name="__main__")


if __name__ == "__main__":
    main()
