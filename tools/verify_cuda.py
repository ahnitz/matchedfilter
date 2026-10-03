"""Verify and benchmark the native CUDA Driver backend on NVIDIA hardware."""
import sys
import time
import numpy as np

import matchedfilter
from matchedfilter import _cuda

print("=== MatchedFilter NVIDIA CUDA Driver Verification ===")
all_devices = matchedfilter.devices()
print("All detected devices:")
for d in all_devices:
    print(f"  {d} - {d.name} (backend={d.backend})")

cuda_devices = [d for d in all_devices if d.backend == "cuda"]
if not cuda_devices:
    print("ERROR: No CUDA devices found!")
    sys.exit(1)

dev = cuda_devices[0]
print(f"\nTarget CUDA device: {dev.name} ({dev})")

# 1. Verification: Flat Filter
print("\n--- Running Flat Filter Verification (n=1024, nd=4, nt=8) ---")
n = 1024
nd, nt = 4, 8
np.random.seed(42)
data = (np.random.randn(nd, n) + 1j * np.random.randn(nd, n)).astype(np.complex64)
tmpl = (np.random.randn(nt, n) + 1j * np.random.randn(nt, n)).astype(np.complex64)

mf_cpu = matchedfilter.MatchedFilter(n, nd, nt, device="cpu")
mf_cpu.set_data(data)
mf_cpu.set_templates(tmpl)
idx_cpu, val_cpu = mf_cpu.run(raw=True)

mf_gpu = matchedfilter.MatchedFilter(n, nd, nt, device=dev)
mf_gpu.set_data(data)
mf_gpu.set_templates(tmpl)
idx_gpu, val_gpu = mf_gpu.run(raw=True)

np.testing.assert_array_equal(idx_gpu, idx_cpu)
np.testing.assert_allclose(val_gpu, val_cpu, rtol=1e-4, atol=1e-4)
print(f"SUCCESS: Flat filter matches CPU! Sample peak: idx={idx_gpu[0, 0, 0]}, val={val_gpu[0, 0, 0]}")

# 2. Verification: Hierarchical Filter
print("\n--- Running Hierarchical Filter Verification (n=4096, nd=4, nt=8) ---")
n = 4096
nd, nt = 4, 8
np.random.seed(123)
data = (np.random.randn(nd, n) + 1j * np.random.randn(nd, n)).astype(np.complex64)
tmpl = (np.random.randn(nt, n) + 1j * np.random.randn(nt, n)).astype(np.complex64)

# Inject signal on pair (0, 0)
data[0, :] += 20.0 * tmpl[0, :]

hf_cpu = matchedfilter.HierarchicalFilter(n, nd, nt, band=512, device="cpu")
hf_cpu.set_coarse_threshold(4.0)
hf_cpu.set_data(data)
hf_cpu.set_templates(tmpl)
idx_cpu, val_cpu = hf_cpu.run(threshold=5.5, raw=True)

hf_gpu = matchedfilter.HierarchicalFilter(n, nd, nt, band=512, device=dev)
hf_gpu.set_coarse_threshold(4.0)
hf_gpu.set_data(data)
hf_gpu.set_templates(tmpl)
idx_gpu, val_gpu = hf_gpu.run(threshold=5.5, raw=True)

np.testing.assert_array_equal(idx_gpu, idx_cpu)
np.testing.assert_allclose(val_gpu, val_cpu, rtol=1e-3, atol=1e-3)
print(f"SUCCESS: Hierarchical filter matches CPU! Injected peak: idx={idx_gpu[0, 0, 0]}, val={val_gpu[0, 0, 0]}")

# 3. Benchmark: Scale to 512 x 512 pairs (Production Workload)
print("\n--- Running Production Workload Benchmark (n=4096, nd=512, nt=512, 262,144 pairs) ---")
nd, nt = 512, 512
data = (np.random.randn(nd, n) + 1j * np.random.randn(nd, n)).astype(np.complex64)
tmpl = (np.random.randn(nt, n) + 1j * np.random.randn(nt, n)).astype(np.complex64)

# Warmup
hf_gpu = matchedfilter.HierarchicalFilter(n, nd, nt, band=512, device=dev)
hf_gpu.set_coarse_threshold(4.0)
hf_gpu.set_data(data)
hf_gpu.set_templates(tmpl)
hf_gpu.run(threshold=5.5)

# Timed runs
timings = []
for _ in range(5):
    t0 = time.perf_counter()
    hf_gpu.run(threshold=5.5)
    t1 = time.perf_counter()
    timings.append(t1 - t0)

best_ms = min(timings) * 1000.0
gpu_compute_ms = hf_gpu._gpu.last_gpu_time * 1000.0
print(f"HierarchicalFilter 512x512 pairs (n=4096, threshold=5.5):")
print(f"  Wall time:   {best_ms:.3f} ms")
print(f"  GPU compute: {gpu_compute_ms:.3f} ms")
print(f"  Pairs/sec:   {nd * nt / (best_ms * 1e-3):,.0f} pairs/s")

# Flat filter benchmark at 512x512
mf_gpu = matchedfilter.MatchedFilter(n, nd, nt, device=dev)
mf_gpu.set_data(data)
mf_gpu.set_templates(tmpl)
mf_gpu.run()
flat_timings = []
for _ in range(5):
    t0 = time.perf_counter()
    mf_gpu.run()
    t1 = time.perf_counter()
    flat_timings.append(t1 - t0)
best_flat_ms = min(flat_timings) * 1000.0
gpu_flat_ms = mf_gpu._gpu.last_gpu_time * 1000.0
print(f"\nFlat MatchedFilter 512x512 pairs (n=4096):")
print(f"  Wall time:   {best_flat_ms:.3f} ms")
print(f"  GPU compute: {gpu_flat_ms:.3f} ms")
print(f"  Pairs/sec:   {nd * nt / (best_flat_ms * 1e-3):,.0f} pairs/s")

print("\n=== ALL TESTS AND BENCHMARKS PASSED SUCCESSFULLY ===")
