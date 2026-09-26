# Testing Metal on physical Apple hardware

macOS CI can use an Apple Paravirtual GPU. It checks compilation, dispatch,
and numerical agreement, but its pipeline limits and timings do not describe
a physical Apple GPU. Test supported sizes on physical hardware as well.

For example, an earlier 8,192-point kernel required 512 threads per
threadgroup. CI allowed 512, while an Apple M2 allowed only 448 for that
pipeline. This exposed a support gap that CI alone did not detect. These
are historical measurements of that kernel, not current size limits.

## Run the tests

Use a checkout with submodules and Python 3.10 or newer. From its root:

```bash
python3 -m venv .local/metal-venv
source .local/metal-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install '.[test]'
python -m pytest tests -q -rs
```

Inspect skip reasons (`-rs`) as well as failures. Record the commit, macOS
version, chip, reported GPU device, and any unsupported pipeline sizes.
The [tooling map](../tools/README.md) describes the Metal kernel probe and
benchmark entry points. Exclude compilation and plan setup from warm timings.

Test runtime source compilation on a system without the Metal compiler as
well as precompiled libraries where available. A machine with Command Line
Tools but no full Xcode can exercise that fallback.

Keep remote hostnames, SSH configuration, credentials, local paths, and
machine provisioning instructions outside tracked documentation. Only the
hardware characteristics and reproducible test procedure belong here.
