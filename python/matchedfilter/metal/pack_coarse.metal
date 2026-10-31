#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;

#line 11218 "hlsl.meta.slang"
uint firstbithigh_0(uint value_0)
{

#line 11231
    if(value_0 == 0U)
    {

#line 11232
        return 4294967295U;
    }

#line 11233
    uint _S1 = clz(value_0);

#line 11233
    return 31U - _S1;
}


#line 7 "pack_coarse.slang"
struct EntryPointParams_0
{
    uint n_0;
    uint band_0;
    uint count_0;
    uint packed_0;
    uint scaleBits_0;
    uint k0_0;
};


#line 7
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    uint device* entryPointParams_coarse_0;
};


#line 7
[[kernel]] void packCoarse(uint3 tid_0 [[thread_position_in_grid]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_coarse_1 [[buffer(2)]])
{

#line 7
    thread KernelContext_0 kernelContext_0;

#line 7
    (&kernelContext_0)->entryPointParams_0 = entryPointParams_1;

#line 7
    (&kernelContext_0)->entryPointParams_data_0 = entryPointParams_data_1;

#line 7
    (&kernelContext_0)->entryPointParams_coarse_0 = entryPointParams_coarse_1;

#line 14
    uint i_0 = tid_0.x;
    if(i_0 >= (entryPointParams_1->count_0))
    {

#line 15
        return;
    }

    uint slot_0 = i_0 & ((&kernelContext_0)->entryPointParams_0->band_0 - 1U);
    uint row_0 = i_0 >> (firstbithigh_0((&kernelContext_0)->entryPointParams_0->band_0));
    float2 _S2 = float2(0.0f, 0.0f);

#line 20
    float2 x_0;
    if(((&kernelContext_0)->entryPointParams_0->k0_0) == 0U)
    {

#line 21
        x_0 = float2(*((&kernelContext_0)->entryPointParams_data_0+(row_0 * (&kernelContext_0)->entryPointParams_0->n_0 + slot_0))) ;

#line 21
    }
    else
    {

        uint k_0 = (&kernelContext_0)->entryPointParams_0->k0_0 + ((slot_0 - (((&kernelContext_0)->entryPointParams_0->k0_0) & ((&kernelContext_0)->entryPointParams_0->band_0 - 1U))) & ((&kernelContext_0)->entryPointParams_0->band_0 - 1U));
        if(k_0 < (((&kernelContext_0)->entryPointParams_0->n_0) >> 1U))
        {

#line 26
            x_0 = float2(*((&kernelContext_0)->entryPointParams_data_0+(row_0 * (&kernelContext_0)->entryPointParams_0->n_0 + k_0))) ;

#line 26
        }
        else
        {

#line 26
            x_0 = _S2;

#line 26
        }

#line 21
    }

#line 29
    if(((&kernelContext_0)->entryPointParams_0->packed_0) != 0U)
    {

#line 30
        float s_0 = (as_type<float>(((&kernelContext_0)->entryPointParams_0->scaleBits_0)));
        *((&kernelContext_0)->entryPointParams_coarse_0+i_0) = (as_type<ushort>((half)((x_0.x * s_0)))) | ((as_type<ushort>((half)((x_0.y * s_0)))) << 16U);

#line 29
    }
    else
    {

        uint _S3 = 2U * i_0;

#line 33
        *((&kernelContext_0)->entryPointParams_coarse_0+_S3) = (as_type<uint>((x_0.x)));
        *((&kernelContext_0)->entryPointParams_coarse_0+(_S3 + 1U)) = (as_type<uint>((x_0.y)));

#line 29
    }

#line 36
    return;
}
