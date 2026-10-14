#!/usr/bin/env python
"""Write tests/data/bank_subset_opt501_v2.npz: the slice of a production FIR bank the
correctness tests use, so they run anywhere (CI included) without the 110 MB bank or h5py.

    python tools/make_bank_subset.py /path/to/fir_three_level_opt501_v2.hdf

Contents (taps cut at the longest tap count in each set; samples beyond a template's count
are zero in the bank, so nothing is lost):
  fine_taps, fine_counts        fir_data/0, the first 128 fine templates of middle group 0
  upper_taps, upper_counts,     fir_data/upper/0, top template 0's middle filters,
  upper_fine_bank_index,        their middle ids,
  upper_sigmas                  and sigmas (columns: reference, -, target)
"""
import sys
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent.parent / "tests" / "data" / "bank_subset_opt501_v2.npz"


def main(bank):
    import h5py
    with h5py.File(bank, "r") as f:
        g, u = f["fir_data/0"], f["fir_data/upper/0"]
        fc = g["actual_tap_count"][:128].astype(np.int64)
        uc = u["actual_tap_count"][:].astype(np.int64)
        data = dict(
            fine_taps=g["taps"][:128, :int(fc.max())].astype(np.float32), fine_counts=fc,
            upper_taps=u["taps"][:, :int(uc.max())].astype(np.float32), upper_counts=uc,
            upper_fine_bank_index=u["fine_bank_index"][:].astype(np.int64),
            upper_sigmas=u["sigmas"][:].astype(np.float64))
    np.savez_compressed(OUT, **data)
    print("wrote %s (%d bytes)" % (OUT, OUT.stat().st_size))


if __name__ == "__main__":
    main(sys.argv[1])
