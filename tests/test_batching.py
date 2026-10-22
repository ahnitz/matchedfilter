"""Batch shapes, including the ones nothing exercised until a cost sweep did.

Helpers come from test_api, which holds the signal and layout builders the
whole suite shares.
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(__file__))
import matchedfilter as mf                                    # noqa: E402
from test_api import (inspiral_power, template_with_power, noise)  # noqa: E402


def test_many_data_segments_and_templates():
    """Batch shapes beyond the ones the captures happen to use.

    The library was exercised at one or a few data segments for most of its
    life, and the shapes a cost sweep wants -- tens of segments against tens
    of templates -- went through paths nothing had run. Walk a spread of them
    and check the output stays the shape it claims.
    """
    n = 4096
    power = np.ascontiguousarray(inspiral_power(n), dtype=np.float32)
    rng = np.random.default_rng(4)
    for nt, nd in ((1, 1), (1, 16), (16, 1), (8, 8), (32, 8), (16, 16)):
        hf = mf.HierarchicalFilter(n, ndata=nd, ntemplates=nt, snr=5.0, fd=1e-3, chain=1024)
        hf.set_reference(power)
        hf.set_templates(np.stack([template_with_power(n, power)
                                   for _ in range(nt)]))
        for _ in range(3):
            hf.set_data(noise((nd, n), rng))
            idx, val = hf.run(binsize=n, threshold=5.0, raw=True)
            assert idx.shape == (nd, nt, 1), (nt, nd, idx.shape)
