"""A successful builder must not silently omit a requested Python version."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    'check_wheels', Path(__file__).resolve().parents[1]/'tools/check_wheels.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


@pytest.mark.parametrize('platform,tags,arch', [
    ('linux-x86_64', ('manylinux_2_28', 'musllinux_1_2'), 'x86_64'),
    ('macos-arm64', ('macosx_11_0',), 'arm64'),
])
def test_release_requires_all_supported_interpreters(tmp_path, platform, tags, arch):
    for minor in range(10, 15):
        for tag in tags:
            wheel = tmp_path/f'matchedfilter-0.1.0a2-cp3{minor}-cp3{minor}-{tag}_{arch}.whl'
            wheel.touch()
    assert len(checker.check(tmp_path, platform)) == 5*len(tags)
    wheel.unlink()
    with pytest.raises(ValueError, match='cp314'):
        checker.check(tmp_path, platform)
    # A free-threaded wheel cannot replace the standard CPython wheel.
    wheel.with_name(wheel.name.replace('-cp314-', '-cp314t-')).touch()
    with pytest.raises(ValueError, match='cp314'):
        checker.check(tmp_path, platform)
