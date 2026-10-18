#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;

#line 9 "src/gpu/compact_peaks.slang"
struct EntryPointParams_0
{
    uint total_0;
    uint cap_0;
};


#line 9
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_count_0;
    packed_uint4 device* entryPointParams_list_0;
};


#line 9
[[kernel]] void compactPeaks(uint3 tid_0 [[thread_position_in_grid]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], int device* entryPointParams_peakIdx_1 [[buffer(1)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(2)]], uint device* entryPointParams_count_1 [[buffer(3)]], packed_uint4 device* entryPointParams_list_1 [[buffer(4)]])
{

#line 9
    thread KernelContext_0 kernelContext_0;

#line 9
    (&kernelContext_0)->entryPointParams_0 = entryPointParams_1;

#line 9
    (&kernelContext_0)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 9
    (&kernelContext_0)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 9
    (&kernelContext_0)->entryPointParams_count_0 = entryPointParams_count_1;

#line 9
    (&kernelContext_0)->entryPointParams_list_0 = entryPointParams_list_1;

#line 16
    uint i_0 = tid_0.x;
    if(i_0 >= (entryPointParams_1->total_0))
    {

#line 17
        return;
    }

#line 18
    int k_0 = (&kernelContext_0)->entryPointParams_peakIdx_0[i_0];
    if(k_0 < int(0))
    {

#line 19
        return;
    }
    uint slot_0 = atomic_fetch_add_explicit(((atomic_uint device*)((&kernelContext_0)->entryPointParams_count_0+int(0))), 1U, memory_order_relaxed);
    if(slot_0 < ((&kernelContext_0)->entryPointParams_0->cap_0))
    {

#line 22
        float2 _S1 = float2(*((&kernelContext_0)->entryPointParams_peakVal_0+i_0)) ;

#line 22
        *((&kernelContext_0)->entryPointParams_list_0+slot_0) = packed_uint4(uint4(i_0, uint(k_0), (as_type<uint>((_S1.x))), (as_type<uint>((_S1.y))))) ;

#line 22
    }



    return;
}
