#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;

#line 90 "core"
struct EntryPointParams_0
{
    uint pairs0_0;
    uint nc_0;
    uint nt_0;
    float thr_0;
    uint packShift_0;
};


#line 2000 "mm_64_compactPairsClustered.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_coarse_0;
    uint device* entryPointParams_clusterOffsets_0;
    uint device* entryPointParams_clusterMembers_0;
    uint device* entryPointParams_survivors_0;
    uint device* entryPointParams_args_0;
};


#line 2000
[[kernel]] void compactPairsClustered(uint3 gid_0 [[thread_position_in_grid]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_coarse_1 [[buffer(1)]], uint device* entryPointParams_clusterOffsets_1 [[buffer(2)]], uint device* entryPointParams_clusterMembers_1 [[buffer(3)]], uint device* entryPointParams_survivors_1 [[buffer(4)]], uint device* entryPointParams_args_1 [[buffer(5)]])
{

#line 2000
    thread KernelContext_0 kernelContext_0;

#line 2000
    (&kernelContext_0)->entryPointParams_0 = entryPointParams_1;

#line 2000
    (&kernelContext_0)->entryPointParams_coarse_0 = entryPointParams_coarse_1;

#line 2000
    (&kernelContext_0)->entryPointParams_clusterOffsets_0 = entryPointParams_clusterOffsets_1;

#line 2000
    (&kernelContext_0)->entryPointParams_clusterMembers_0 = entryPointParams_clusterMembers_1;

#line 2000
    (&kernelContext_0)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2000
    (&kernelContext_0)->entryPointParams_args_0 = entryPointParams_args_1;

#line 2009
    uint pair0_0 = gid_0.x;

#line 2009
    bool active_0;

    if(pair0_0 < (entryPointParams_1->pairs0_0))
    {

#line 2011
        active_0 = !((length(float2(*((&kernelContext_0)->entryPointParams_coarse_0+pair0_0)) )) < ((&kernelContext_0)->entryPointParams_0->thr_0));

#line 2011
    }
    else
    {

#line 2011
        active_0 = false;

#line 2011
    }

#line 2011
    uint cnt_0;

#line 2011
    uint d_0;

#line 2011
    uint m0_0;



    if(active_0)
    {

#line 2016
        uint _S1 = pair0_0 / (&kernelContext_0)->entryPointParams_0->nc_0;
        uint c_0 = pair0_0 % (&kernelContext_0)->entryPointParams_0->nc_0;
        uint m0_1 = (&kernelContext_0)->entryPointParams_clusterOffsets_0[c_0];

#line 2018
        cnt_0 = (&kernelContext_0)->entryPointParams_clusterOffsets_0[c_0 + 1U] - m0_1;

#line 2018
        d_0 = _S1;

#line 2018
        m0_0 = m0_1;

#line 2015
    }
    else
    {

#line 2015
        cnt_0 = 0U;

#line 2015
        d_0 = 0U;

#line 2015
        m0_0 = 0U;

#line 2015
    }

#line 2039
    if(cnt_0 > 0U)
    {
        uint slot_0 = atomic_fetch_add_explicit(((atomic_uint device*)((&kernelContext_0)->entryPointParams_args_0+int(0))), cnt_0, memory_order_relaxed);

#line 2041
        uint j_0 = 0U;
        for(;;)
        {

#line 2042
            if(j_0 < cnt_0)
            {
            }
            else
            {

#line 2042
                break;
            }

#line 2043
            *((&kernelContext_0)->entryPointParams_survivors_0+(slot_0 + j_0)) = d_0 * (&kernelContext_0)->entryPointParams_0->nt_0 + (&kernelContext_0)->entryPointParams_clusterMembers_0[m0_0 + j_0];

#line 2042
            j_0 = j_0 + 1U;

#line 2042
        }


        if(((&kernelContext_0)->entryPointParams_0->packShift_0) > 0U)
        {
            uint _S2 = atomic_fetch_max_explicit(((atomic_uint device*)((&kernelContext_0)->entryPointParams_args_0+int(4))), (slot_0 + cnt_0 + ((1U << ((&kernelContext_0)->entryPointParams_0->packShift_0)) - 1U)) >> ((&kernelContext_0)->entryPointParams_0->packShift_0), memory_order_relaxed);

#line 2045
        }

#line 2039
    }

#line 2051
    return;
}
