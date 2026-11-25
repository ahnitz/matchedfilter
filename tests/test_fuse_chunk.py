"""The submissions per fused command buffer: a kernel slot of the device trial on every
backend that fuses (_settings.fuse_chunk), not a per-backend constant."""
import pytest

from matchedfilter import _settings


class _Dev:
    """What a fused batch reads of its device: the name its choices are keyed on."""
    name = device_name = "Test GPU (fuse chunk)"
    collector = None


@pytest.fixture(autouse=True)
def _fresh_settings():
    _settings.clear()
    yield
    _settings.clear()


@pytest.mark.parametrize("module, default", [("_vkcompute", 16), ("_mtlcompute", 2)])
def test_a_fused_batch_takes_its_chunk_from_the_device_trial(module, default):
    """A batch made with no trial running or lock held commits after the backend's tuned
    default; it registers the slot with the other value as the alternative, so the device
    trial can play it; with that arm in force (a play, or a lock) a new batch takes it."""
    import importlib
    mod = importlib.import_module("matchedfilter." + module)
    assert mod._FusedBatch(_Dev()).chunk == default
    other = next(c for c in _settings.FUSE_CHUNKS if c != default)
    assert _settings.slots({_Dev.name}) == {"kern:fuse:chunk": (str(default), str(other))}
    with _settings.running({"kern:fuse:chunk": str(other)}):
        assert mod._FusedBatch(_Dev()).chunk == other
    _settings.locks(("gpu:0 " + _Dev.name,))["kern:fuse:chunk"] = str(other)
    assert mod._FusedBatch(_Dev()).chunk == other
