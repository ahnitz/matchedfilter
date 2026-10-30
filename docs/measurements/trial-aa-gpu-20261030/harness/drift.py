# drift.py: the same GPU call timed 8 times in a row after an idle gap (host wall, as a trial
# times its plays), for gaps 0, 20, 100 ms: does the call speed up along the sequence?
import time, numpy as np
from matchedfilter import HierarchicalFilter, _calibration as C
n = 2048; blocks = 256; nt = 64
spec, ser, starts, ws, we = C._gpu_cal_inputs(n, blocks, nt, 11)
p = HierarchicalFilter(n, 1, nt, chain=(256, 512), device="gpu:0"); p.set_templates(spec)
p.set_coarse_threshold((3.5, 3.0))
res = p.empty_shared(ser.shape); res[:] = ser
for _ in range(20): p.run_series(res, starts, ws, we, threshold=1e6)
for gap in (0.0, 0.02, 0.1):
    seqs = []
    for rep in range(30):
        time.sleep(gap)
        t = []
        for i in range(8):
            t0 = time.perf_counter(); p.run_series(res, starts, ws, we, threshold=1e6); t.append(time.perf_counter() - t0)
        seqs.append(t)
    m = np.median(np.array(seqs), axis=0)
    print("gap %3d ms: median per position (ms)" % (gap * 1e3), " ".join("%.2f" % (x * 1e3) for x in m), " pos1/pos8 %.2f" % (m[0] / m[-1]))
