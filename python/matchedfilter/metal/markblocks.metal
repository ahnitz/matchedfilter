#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;

#line 2147 "/tmp/tmpd1hqnsls/tier0.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
};


#line 2147
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_survivors_0;
    uint device* entryPointParams_countArgs_0;
    uint device* entryPointParams_flags_0;
    uint device* entryPointParams_blockList_0;
    uint device* entryPointParams_blockArgs_0;
};


#line 2147
[[kernel]] void markBlocks(uint3 gid_0 [[thread_position_in_grid]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_survivors_1 [[buffer(1)]], uint device* entryPointParams_countArgs_1 [[buffer(2)]], uint device* entryPointParams_flags_1 [[buffer(3)]], uint device* entryPointParams_blockList_1 [[buffer(4)]], uint device* entryPointParams_blockArgs_1 [[buffer(5)]])
{

#line 2147
    thread KernelContext_0 kernelContext_0;

#line 2147
    (&kernelContext_0)->entryPointParams_0 = entryPointParams_1;

#line 2147
    (&kernelContext_0)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2147
    (&kernelContext_0)->entryPointParams_countArgs_0 = entryPointParams_countArgs_1;

#line 2147
    (&kernelContext_0)->entryPointParams_flags_0 = entryPointParams_flags_1;

#line 2147
    (&kernelContext_0)->entryPointParams_blockList_0 = entryPointParams_blockList_1;

#line 2147
    (&kernelContext_0)->entryPointParams_blockArgs_0 = entryPointParams_blockArgs_1;

#line 2155
    uint k_0 = gid_0.x;
    if(k_0 >= entryPointParams_countArgs_1[int(0)])
    {

#line 2157
        return;
    }

#line 2158
    uint d_0 = (&kernelContext_0)->entryPointParams_survivors_0[k_0] / (&kernelContext_0)->entryPointParams_0->ntmpl_0;

    uint was_0 = atomic_exchange_explicit(((atomic_uint device*)((&kernelContext_0)->entryPointParams_flags_0+d_0)), 1U, memory_order_relaxed);
    if(was_0 == 0U)
    {
        uint slot_0 = atomic_fetch_add_explicit(((atomic_uint device*)((&kernelContext_0)->entryPointParams_blockArgs_0+int(0))), 1U, memory_order_relaxed);
        *((&kernelContext_0)->entryPointParams_blockList_0+slot_0) = d_0;

#line 2161
    }

#line 2166
    return;
}
