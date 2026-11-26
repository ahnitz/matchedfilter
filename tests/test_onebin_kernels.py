"""One-bin specialization must preserve general-kernel output and dispatch."""
import numpy as np
import pytest
import sim_driver
import matchedfilter as mf
from matchedfilter import _gpuhost, _vkcompute as V
from conftest import vulkan_runs


@pytest.mark.parametrize('n', [16384, 32768, 65536])
@pytest.mark.parametrize('shared', [32768, 65536])
def test_onebin_artifacts_and_selection(n, shared):
    from matchedfilter import _kernels
    lim = sim_driver.stated_props(artifact_family='vulkan', max_group_memory=shared,
                                  load_time_constants=True)
    file = lambda role, n: _kernels.resolve(lim, role, n)['file']
    for one_role, general_role in (('peaks1', 'peaks'), ('tier1', 'tier')):
        one, general = file(one_role, n), file(general_role, n)
        assert '_onebin' in one and '_onebin' not in general
        assert one.endswith('_lds32.spv') == (shared == 32768)
        assert (V._SPIRV / one).is_file()
        assert (V._SPIRV / general).is_file()
    assert file('peaks1', 2048) == file('peaks', 2048)
    assert file('peaks1', 4096) == 'tierb_4096_onebin.spv'


def test_compaction_has_one_canonical_artifact():
    from matchedfilter import _kernels
    files = {rec['file'] for rec in _kernels.manifest('vulkan')['kernels'].values()
             if rec['entry'] == 'compactPairs'}
    assert files == {'compact.spv'}
    assert (V._SPIRV / 'compact.spv').is_file()
    assert not list(V._SPIRV.glob('compact_[0-9]*.spv'))     # compact_peaks is another kernel


def _general_only(resolve):
    general = {'peaks1': 'peaks', 'tier1': 'tier', 'refine1': 'refine'}

    def pick(name, size, consts=None):
        if name in general:      # the general kernel, which has no gate-only build
            name, consts = general[name], {k: v for k, v in (consts or {}).items() if k != 'gate'}
        return resolve(name, size, consts)
    return pick


@pytest.mark.parametrize('n', [16384, 32768, 65536])
@pytest.mark.parametrize('hierarchical', [False, True])
@pytest.mark.parametrize('shared', [32768, 65536])
def test_specialized_and_general_peaks_are_identical(n, hierarchical, shared):
    ok, why = vulkan_runs()
    if not ok:
        pytest.skip(why)
    rng = np.random.default_rng(n)
    d = (rng.normal(size=(3,n))+1j*rng.normal(size=(3,n))).astype(np.complex64)
    h = (rng.normal(size=(2,n))+1j*rng.normal(size=(2,n))).astype(np.complex64)
    contexts = []
    filters = []
    try:
        for specialized in (False, True):
            f = (mf.HierarchicalFilter(n, 3, 2, chain=256, device='gpu:0')
                 if hierarchical else mf.MatchedFilter(n,3,2,device='gpu:0'))
            if hierarchical:
                f.set_coarse_threshold(0.)
            f.set_templates(h); f.set_data(d)
            contexts.append(f._gpu)
            f._gpu.props = _gpuhost.DeviceProps(**dict(f._gpu.props.as_dict(), max_group_memory=min(
                shared, f._gpu.props.max_group_memory)))
            if not specialized:
                # the general kernels in place of the one-bin builds
                f._gpu._kernel_record = _general_only(f._gpu._kernel_record)
            filters.append(f)
        for window in [(0,n), (11,n-17)]:
            for threshold in (0., 1e10):
                for binsize in (None, n*2, n//3):
                    a,b = [f.run(window=window,threshold=threshold,binsize=binsize).copy()
                           for f in filters]
                    np.testing.assert_array_equal(a,b)
    finally:
        for context in contexts:
            context.destroy()
