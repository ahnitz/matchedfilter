// Ceilings for the CUDA roofline (tools/cuda_roofline.py): what this device's
// fp32 pipes and DRAM actually deliver, measured rather than taken from a data sheet.
// Compiled to PTX with NVRTC (python tools/cuda_roofline.py --build-ceilings).
extern "C" __global__ void fmaPeak(float *out, int iters, float a, float b)
{
    // 8 independent chains per thread hide the FMA latency; 2 flops per FMA.
    float x0 = threadIdx.x, x1 = x0 + 1, x2 = x0 + 2, x3 = x0 + 3;
    float x4 = x0 + 4, x5 = x0 + 5, x6 = x0 + 6, x7 = x0 + 7;
    for (int i = 0; i < iters; ++i) {
        x0 = fmaf(x0, a, b); x1 = fmaf(x1, a, b); x2 = fmaf(x2, a, b); x3 = fmaf(x3, a, b);
        x4 = fmaf(x4, a, b); x5 = fmaf(x5, a, b); x6 = fmaf(x6, a, b); x7 = fmaf(x7, a, b);
    }
    float s = x0 + x1 + x2 + x3 + x4 + x5 + x6 + x7;
    if (s == 1234.5f) out[blockIdx.x * blockDim.x + threadIdx.x] = s;   // never true: keeps the work
}

extern "C" __global__ void copyStream(const float4 *__restrict__ src, float4 *__restrict__ dst, size_t n)
{
    size_t stride = (size_t)gridDim.x * blockDim.x;
    for (size_t i = (size_t)blockIdx.x * blockDim.x + threadIdx.x; i < n; i += stride)
        dst[i] = src[i];
}
