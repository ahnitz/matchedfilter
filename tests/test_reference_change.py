"""A reference changed after the templates are loaded.

The hierarchical plan keeps no unscaled copy of its tier templates: a new reference
leaves the loaded ones stale, and the Python plan loads them again (from its template
source, or the copy it holds). The result must be exactly that of loading the templates
after the final reference."""
import numpy as np
import pytest

import matchedfilter as mf

from test_api import inspiral_power, template_with_power, noise

N, ND, NT = 4096, 4, 6
CHAIN = (256, 1024)


def _inputs():
    rng = np.random.default_rng(21)
    exps = np.linspace(-7 / 3.0, -4 / 3.0, NT)
    H = np.stack([template_with_power(N, inspiral_power(N, exponent=e)) for e in exps])
    D = noise((ND, N), rng)
    for d in range(ND):
        D[d] += (9.0 * H[d % NT] * np.exp(2j * np.pi * np.arange(N) * (300 + 41 * d) / N)
                 ).astype(np.complex64)
    return H, D


def _filter():
    return mf.HierarchicalFilter(N, ndata=ND, ntemplates=NT, snr=5.5, fd=1e-2, chain=CHAIN)


def _run(hf, D):
    hf.set_data(D)
    return hf.run(binsize=512, threshold=5.0)


@pytest.mark.parametrize("source", [False, True])
def test_reference_changed_after_loading_equals_loading_after_it(source):
    H, D = _inputs()
    first, final = inspiral_power(N, exponent=-4 / 3.0), inspiral_power(N)
    expect = _filter()
    expect.set_reference(final)
    expect.set_templates(H)
    a = _run(expect, D)

    hf = _filter()
    if source:
        hf.set_template_source(lambda: H)
    hf.set_reference(first)
    hf.set_templates(H)
    assert (hf._held_templates is None) == source
    hf.set_reference(final)
    b = _run(hf, D)
    assert (a["index"] >= 0).any()
    np.testing.assert_array_equal(a["index"], b["index"])
    np.testing.assert_array_equal(a["value"], b["value"])


def test_a_run_over_stale_templates_fails():
    """The C plan, given a new reference behind the Python plan's back, refuses to run the
    templates it scaled for the old one."""
    H, D = _inputs()
    hf = _filter()
    hf.set_reference(inspiral_power(N, exponent=-4 / 3.0))
    hf.set_templates(H)
    _run(hf, D)
    hf._mf.set_reference(np.ascontiguousarray(inspiral_power(N), dtype=np.float32))
    with pytest.raises(Exception):
        _run(hf, D)
