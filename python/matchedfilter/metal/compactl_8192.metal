#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;

#line 90 "core"
struct EntryPointParams_0
{
    uint pairs_0;
    float thr_0;
    uint nbins_0;
};


#line 1866 "mm_8192_compactListed.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_coarse_0;
    uint device* entryPointParams_survivors_0;
    uint device* entryPointParams_args_0;
    uint device* entryPointParams_list_0;
    uint device* entryPointParams_listArgs_0;
};


#line 1866
[[kernel]] void compactListed(uint3 gid_0 [[thread_position_in_grid]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_coarse_1 [[buffer(1)]], uint device* entryPointParams_survivors_1 [[buffer(2)]], uint device* entryPointParams_args_1 [[buffer(3)]], uint device* entryPointParams_list_1 [[buffer(4)]], uint device* entryPointParams_listArgs_1 [[buffer(5)]])
{

#line 1866
    thread KernelContext_0 kernelContext_0;

#line 1866
    (&kernelContext_0)->entryPointParams_0 = entryPointParams_1;

#line 1866
    (&kernelContext_0)->entryPointParams_coarse_0 = entryPointParams_coarse_1;

#line 1866
    (&kernelContext_0)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1866
    (&kernelContext_0)->entryPointParams_args_0 = entryPointParams_args_1;

#line 1866
    (&kernelContext_0)->entryPointParams_list_0 = entryPointParams_list_1;

#line 1866
    (&kernelContext_0)->entryPointParams_listArgs_0 = entryPointParams_listArgs_1;

#line 1874
    uint k_0 = gid_0.x;

    bool _S1 = k_0 < entryPointParams_listArgs_1[int(0)];

#line 1876
    uint pair_0;

#line 1876
    if(_S1)
    {

#line 1876
        pair_0 = (&kernelContext_0)->entryPointParams_list_0[k_0];

#line 1876
    }
    else
    {

#line 1876
        pair_0 = 0U;

#line 1876
    }

#line 1876
    bool active_0;
    if(_S1)
    {

#line 1877
        active_0 = !((length(float2(*((&kernelContext_0)->entryPointParams_coarse_0+pair_0)) )) < ((&kernelContext_0)->entryPointParams_0->thr_0));

#line 1877
    }
    else
    {

#line 1877
        active_0 = false;

#line 1877
    }

#line 1889
    if(active_0)
    {
        uint slot_0 = atomic_fetch_add_explicit(((atomic_uint device*)((&kernelContext_0)->entryPointParams_args_0+int(0))), 1U, memory_order_relaxed);
        *((&kernelContext_0)->entryPointParams_survivors_0+slot_0) = pair_0;

#line 1889
    }

#line 1895
    return;
}
