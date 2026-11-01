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
};


#line 1955 "mm_64_compactPairsClustered.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_coarse_0;
    uint device* entryPointParams_clusterOffsets_0;
    uint device* entryPointParams_clusterMembers_0;
    uint device* entryPointParams_survivors_0;
    uint device* entryPointParams_args_0;
};


#line 1955
[[kernel]] void compactPairsClustered(uint3 gid_0 [[thread_position_in_grid]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_coarse_1 [[buffer(1)]], uint device* entryPointParams_clusterOffsets_1 [[buffer(2)]], uint device* entryPointParams_clusterMembers_1 [[buffer(3)]], uint device* entryPointParams_survivors_1 [[buffer(4)]], uint device* entryPointParams_args_1 [[buffer(5)]])
{

#line 1955
    thread KernelContext_0 kernelContext_0;

#line 1955
    (&kernelContext_0)->entryPointParams_0 = entryPointParams_1;

#line 1955
    (&kernelContext_0)->entryPointParams_coarse_0 = entryPointParams_coarse_1;

#line 1955
    (&kernelContext_0)->entryPointParams_clusterOffsets_0 = entryPointParams_clusterOffsets_1;

#line 1955
    (&kernelContext_0)->entryPointParams_clusterMembers_0 = entryPointParams_clusterMembers_1;

#line 1955
    (&kernelContext_0)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1955
    (&kernelContext_0)->entryPointParams_args_0 = entryPointParams_args_1;

#line 1963
    uint pair0_0 = gid_0.x;

#line 1963
    bool active_0;

    if(pair0_0 < (entryPointParams_1->pairs0_0))
    {

#line 1965
        active_0 = !((length(float2(*((&kernelContext_0)->entryPointParams_coarse_0+pair0_0)) )) < ((&kernelContext_0)->entryPointParams_0->thr_0));

#line 1965
    }
    else
    {

#line 1965
        active_0 = false;

#line 1965
    }

#line 1965
    uint cnt_0;

#line 1965
    uint d_0;

#line 1965
    uint m0_0;



    if(active_0)
    {

#line 1970
        uint _S1 = pair0_0 / (&kernelContext_0)->entryPointParams_0->nc_0;
        uint c_0 = pair0_0 % (&kernelContext_0)->entryPointParams_0->nc_0;
        uint m0_1 = (&kernelContext_0)->entryPointParams_clusterOffsets_0[c_0];

#line 1972
        cnt_0 = (&kernelContext_0)->entryPointParams_clusterOffsets_0[c_0 + 1U] - m0_1;

#line 1972
        d_0 = _S1;

#line 1972
        m0_0 = m0_1;

#line 1969
    }
    else
    {

#line 1969
        cnt_0 = 0U;

#line 1969
        d_0 = 0U;

#line 1969
        m0_0 = 0U;

#line 1969
    }

#line 1989
    if(cnt_0 > 0U)
    {
        uint _S2 = atomic_fetch_add_explicit(((atomic_uint device*)((&kernelContext_0)->entryPointParams_args_0+int(0))), cnt_0, memory_order_relaxed);

#line 1991
        uint j_0 = 0U;
        for(;;)
        {

#line 1992
            if(j_0 < cnt_0)
            {
            }
            else
            {

#line 1992
                break;
            }

#line 1993
            *((&kernelContext_0)->entryPointParams_survivors_0+(_S2 + j_0)) = d_0 * (&kernelContext_0)->entryPointParams_0->nt_0 + (&kernelContext_0)->entryPointParams_clusterMembers_0[m0_0 + j_0];

#line 1992
            j_0 = j_0 + 1U;

#line 1992
        }

#line 1989
    }

#line 1997
    return;
}
