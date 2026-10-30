# drift2.py: a "play" of 4 GPU submissions with HOSTMS of host work between them, timed 8
# times in a row after an idle gap: does a play speed up along the sequence?
import sys, time, numpy as np
from matchedfilter import HierarchicalFilter, _calibration as C
hostms = float(sys.argv[1])
n = 2048; blocks = 128; nt = 64
spec, ser, starts, ws, we = C._gpu_cal_inputs(n, blocks, nt, 11)
p = HierarchicalFilter(n, 1, nt, chain=(256, 512), device="gpu:0"); p.set_templates(spec)
p.set_coarse_threshold((3.5, 3.0))
res = p.empty_shared(ser.shape); res[:] = ser
def busy(ms):
    t = time.perf_counter() + ms / 1e3
    x = 0
    while time.perf_counter() < t: x += 1
def play():
    for _ in range(4):
        p.run_series(res, starts, ws, we, threshold=1e6); busy(hostms)
for _ in range(20): play()
for gap in (0.0, 0.1, 0.5):
    seqs = []
    for rep in range(20):
        time.sleep(gap)
        t = []
        for i in range(8):
            t0 = time.perf_counter(); play(); t.append(time.perf_counter() - t0)
        seqs.append(t)
    m = np.median(np.array(seqs), axis=0)
    print("host %.0f ms gap %3d ms: per position (ms)" % (hostms, gap * 1e3), " ".join("%.2f" % (x * 1e3) for x in m), " pos2/pos8 %.2f" % (m[1] / m[-1]))
