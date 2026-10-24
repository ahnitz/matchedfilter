/* The AVX1 back end: the float kernels at 8 lanes for CPUs with AVX but not AVX2 (Sandy and
 * Ivy Bridge), which Highway would otherwise serve with its 4-lane SSE4 target.
 *
 * Built with -mavx and AP_SIMD_AVX1, which puts simd-avx1.h under the same kernel headers the
 * Highway targets use (balanced-inl.h and everything it includes for the float path). The
 * table starts as the SSE4 back end's and replaces its float entries: the Q15 screen (int16,
 * which AVX1 cannot widen), the direct refine's correlation and the real-series kernels stay
 * SSE4's. Results are the SSE4 path's bit for bit: both multiply then add (no FMA).
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "alloc.h"
#include "env.h"
#include "matchedfilter.h"
#include "backend.h"

#define AP_SIMD_AVX1 1
#include "balanced-inl.h"

/* The AVX1 table on top of base (the SSE4 back end's), built once. */
extern "C" const ap_backend *ap_avx1_backend(const ap_backend *base) {
  static ap_backend be;
  static int ready = 0;
  if (!ready) {
    namespace k = ap::N_AVX;
    be = *base;
    be.name = "AVX";
    be.lanes = k::AP_W;
    be.create = k::create;
    be.destroy = k::destroy;
    be.fft = k::fft;
    be.supported = k::supported;
    be.binmax = k::binmax;
    be.binmax_split = k::binmax_split;
    be.has_prod = k::has_prod;
    be.split = k::split;
    be.binmax_prod = k::binmax_prod;
    be.corr_prod = k::corr_prod;
    be.corr_split = k::corr_split;
    be.pairbatch = k::pairbatch;
    be.binmax_prod_batch = k::binmax_prod_batch;
    be.binmax_prod_batch_lanes = k::binmax_prod_batch_lanes;
    be.corr_prod_batch = k::corr_prod_batch;
    be.create_pairbatch = k::create_small;
    be.broadcast_data = k::broadcast_data;
    be.binmax_prod_threshold = k::binmax_prod_threshold;
    ready = 1;
  }
  return &be;
}
