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


#line 2186 "bands.slang"
float2 seriesSample_0(packed_float2 device* series_0, uint i_0, uint layout_0)
{
    if(layout_0 == 0U)
    {

#line 2189
        return float2(*(series_0+i_0)) ;
    }

#line 2190
    uint f_0 = (layout_0 >> 2U) + (layout_0 & 3U) * i_0;

#line 2190
    float2 _S2 = float2(*(series_0+(f_0 >> 1U))) ;

#line 2190
    float _S3;

    if((f_0 & 1U) != 0U)
    {

#line 2192
        _S3 = _S2.y;

#line 2192
    }
    else
    {

#line 2192
        _S3 = _S2.x;

#line 2192
    }

#line 2192
    return float2(_S3, 0.0f);
}


#line 577
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 579
    float2 t1_0 = *a_0 - *c_0;

#line 579
    float2 t2_0 = *b_0 + *d_0;

#line 579
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 581
    *b_0 = t1_0 + j3_0;

#line 581
    *c_0 = t0_0 - t2_0;

#line 581
    *d_0 = t1_0 - j3_0;
    return;
}


#line 317
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 317
    float _S4 = a_1.x;

#line 317
    float _S5 = b_1.x;

#line 317
    float _S6 = a_1.y;

#line 317
    float _S7 = b_1.y;

#line 317
    return float2(_S4 * _S5 - _S6 * _S7, _S4 * _S7 + _S6 * _S5);
}


#line 613
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 620
    uint n1_0 = 0U;
    for(;;)
    {

#line 621
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 621
            break;
        }

#line 621
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 621
        n1_0 = n1_0 + 1U;

#line 621
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 622
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 622
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 623
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 623
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 624
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 624
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 624
    uint k2_0 = 0U;
    for(;;)
    {

#line 625
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 625
            break;
        }

#line 625
        uint _S8 = 4U * k2_0;

#line 625
        r4_0(&(*r_0)[_S8], &(*r_0)[_S8 + 1U], &(*r_0)[_S8 + 2U], &(*r_0)[_S8 + 3U]);

#line 625
        k2_0 = k2_0 + 1U;

#line 625
    }

    float2 t_0 = (*r_0)[int(1)];

#line 627
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 627
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 628
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 628
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 629
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 629
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 630
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 630
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 631
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 631
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 632
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 632
    (*r_0)[int(14)] = t_5;
    return;
}


#line 101 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 319 "bands.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S9 = max(TB_0, 1U);

#line 321
    uint j_0 = d_1 / _S9;

#line 321
    uint m_0 = d_1 % _S9;

#line 321
    uint _S10;
    if(TB_0 <= 16U)
    {

#line 322
        _S10 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 322
    }
    else
    {

#line 322
        _S10 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 322
    }

#line 322
    return _S10;
}


#line 588
void dft2_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    float2 a_2 = (*r_1)[o_0];

#line 590
    float2 b_2 = (*r_1)[o_0 + 1U];

#line 590
    (*r_1)[o_0] = (*r_1)[o_0] + (*r_1)[o_0 + 1U];

#line 590
    (*r_1)[o_0 + 1U] = a_2 - b_2;
    return;
}


#line 716
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 716
    uint b_3 = 0U;

#line 726
    for(;;)
    {

#line 726
        if(b_3 < 8U)
        {
        }
        else
        {

#line 726
            break;
        }

#line 726
        dft2_0(r_2, b_3 * 2U);

#line 726
        b_3 = b_3 + 1U;

#line 726
    }

    return;
}


#line 863
uint lgOf_0(uint i_1)
{

#line 863
    uint _S11;

#line 863
    if(i_1 < 3U)
    {

#line 863
        _S11 = 4U;

#line 863
    }
    else
    {

#line 863
        _S11 = 1U;

#line 863
    }

#line 863
    return _S11;
}


#line 865
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 869
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 869
    uint lg_2 = lgOf_0(1U);

#line 869
    uint lg_3 = lgOf_0(0U);

#line 874
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 2354
struct EntryPointParams_0
{
    uint seriesLength_0;
    uint B0_0;
    uint B1_0;
    uint scaleBits_0;
    uint k0_0_0;
    uint k0_1_0;
    uint seriesLayout_0;
};


#line 793
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    uint device* entryPointParams_band0_0;
    packed_float2 device* entryPointParams_band1_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 2354
[[kernel]] void forwardTier0(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], uint device* entryPointParams_band0_1 [[buffer(3)]], packed_float2 device* entryPointParams_band1_1 [[buffer(4)]])
{

#line 2354
    bool _S12;

#line 2354
    float2 x_2;

#line 2354
    uint _S13;

#line 2354
    uint k2_1;

#line 2354
    float cr_0;

#line 2354
    float ci_0;

#line 2354
    uint _S14;

#line 2354
    uint _S15;

#line 2354
    uint d_2;

#line 2354
    uint j_1;

#line 2354
    uint _S16;

#line 2354
    uint _S17;

#line 2354
    uint _S18;

#line 2354
    thread KernelContext_0 kernelContext_0;

#line 2354
    (&kernelContext_0)->entryPointParams_0 = entryPointParams_1;

#line 2354
    (&kernelContext_0)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2354
    (&kernelContext_0)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2354
    (&kernelContext_0)->entryPointParams_band0_0 = entryPointParams_band0_1;

#line 2354
    (&kernelContext_0)->entryPointParams_band1_0 = entryPointParams_band1_1;

#line 2354
    threadgroup array<uint, int(8192)> stg_1;

#line 2354
    (&kernelContext_0)->stg_0 = &stg_1;

#line 2362
    uint tid_0 = lid_0.x;
    (&kernelContext_0)->_tid_0 = tid_0;
    (&kernelContext_0)->_stgBase_0 = 0U;
    uint _S19 = gid_0.x;

#line 2365
    uint _S20 = entryPointParams_starts_1[_S19];
    thread array<float2, int(16)> r_3;

#line 2366
    uint k_0 = 0U;
    for(;;)
    {

#line 2367
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2367
            break;
        }

#line 2368
        uint offset_0 = tid_0 + 512U * k_0;
        float2 _S21 = float2(0.0f, 0.0f);
        if(_S20 < ((&kernelContext_0)->entryPointParams_0->seriesLength_0))
        {

#line 2370
            _S12 = offset_0 < ((&kernelContext_0)->entryPointParams_0->seriesLength_0 - _S20);

#line 2370
        }
        else
        {

#line 2370
            _S12 = false;

#line 2370
        }

#line 2370
        if(_S12)
        {

#line 2370
            x_2 = seriesSample_0((&kernelContext_0)->entryPointParams_series_0, _S20 + offset_0, (&kernelContext_0)->entryPointParams_0->seriesLayout_0);

#line 2370
        }
        else
        {

#line 2370
            x_2 = _S21;

#line 2370
        }

        r_3[k_0] = float2(x_2.x / 8192.0f, - x_2.y / 8192.0f);

#line 2367
        k_0 = k_0 + 1U;

#line 2367
    }

#line 2374
    for(;;)
    {

#line 2374
        for(;;)
        {

#line 2374
            for(;;)
            {

#line 2374
                for(;;)
                {

#line 2374
                    uint lgTB_0 = firstbithigh_0(512U);

#line 2374
                    _S13 = lgTB_0;

#line 2374
                    uint lgLn_0 = firstbithigh_0(8192U);

#line 2374
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2374
                    uint lane_1 = tid_0 & 511U;

#line 2374
                    dft16_0(&r_3);

#line 2374
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 8192.0f);

#line 2374
                    float _S22 = tw_0.x;

#line 2374
                    float _S23 = tw_0.y;

#line 2374
                    k2_1 = 0U;

#line 2374
                    cr_0 = 1.0f;

#line 2374
                    ci_0 = 0.0f;

#line 2374
                    for(;;)
                    {

#line 2374
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2374
                            break;
                        }

#line 2374
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2374
                        float nr_0 = cr_0 * _S22 - ci_0 * _S23;

#line 2374
                        float _S24 = cr_0 * _S23 + ci_0 * _S22;

#line 2374
                        k2_1 = k2_1 + 1U;

#line 2374
                        cr_0 = nr_0;

#line 2374
                        ci_0 = _S24;

#line 2374
                    }

#line 2374
                    uint per_1 = 16U / max(512U, 1U);

#line 2374
                    uint _S25 = max(32U, 1U);

#line 2374
                    _S14 = _S25;

#line 2374
                    uint blk2_1 = tid_0 / _S25;

#line 2374
                    uint lane2_1 = tid_0 % _S25;

#line 2374
                    for(;;)
                    {

#line 2374
                        uint _S26 = (1U << lgTB_0) - 1U;

#line 2374
                        _S15 = _S26;

#line 2374
                        uint _S27 = (1U << lgLn_0) - 1U;

#line 2374
                        thread array<uint, int(16)> src_0;

#line 2374
                        d_2 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            uint p_0 = computeWant_0(d_2, 512U, 8192U, blk_1, lane_1, per_1, _S25, 512U, blk2_1, lane2_1);

#line 2374
                            uint rem_0 = p_0 & _S27;

#line 2374
                            src_0[d_2] = (rem_0 >> lgTB_0) * 512U + ((p_0 >> lgLn_0) << lgTB_0) + (rem_0 & _S26);

#line 2374
                            d_2 = d_2 + 1U;

#line 2374
                        }

#line 2374
                        thread array<float, int(16)> xr_0;

#line 2374
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2374
                        j_1 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            (*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + j_1 * 512U + (&kernelContext_0)->_tid_0] = (as_type<uint>((r_3[j_1].x)));

#line 2374
                            j_1 = j_1 + 1U;

#line 2374
                        }

#line 2374
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2374
                        d_2 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            xr_0[d_2] = (as_type<float>(((*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + src_0[d_2]])));

#line 2374
                            d_2 = d_2 + 1U;

#line 2374
                        }

#line 2374
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2374
                        j_1 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            (*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + j_1 * 512U + (&kernelContext_0)->_tid_0] = (as_type<uint>((r_3[j_1].y)));

#line 2374
                            j_1 = j_1 + 1U;

#line 2374
                        }

#line 2374
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2374
                        d_2 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            r_3[d_2] = float2(xr_0[d_2], (as_type<float>(((*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + src_0[d_2]]))));

#line 2374
                            d_2 = d_2 + 1U;

#line 2374
                        }

#line 2374
                        break;
                    }

#line 2374
                    break;
                }

#line 2374
                break;
            }

#line 2374
            for(;;)
            {

#line 2374
                for(;;)
                {

#line 2374
                    uint lgTB_1 = firstbithigh_0(32U);

#line 2374
                    _S16 = lgTB_1;

#line 2374
                    uint blk_2 = tid_0 >> lgTB_1;

#line 2374
                    uint lane_2 = tid_0 & 31U;

#line 2374
                    dft16_0(&r_3);

#line 2374
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 512.0f);

#line 2374
                    float _S28 = tw_1.x;

#line 2374
                    float _S29 = tw_1.y;

#line 2374
                    k2_1 = 0U;

#line 2374
                    cr_0 = 1.0f;

#line 2374
                    ci_0 = 0.0f;

#line 2374
                    for(;;)
                    {

#line 2374
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2374
                            break;
                        }

#line 2374
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2374
                        float nr_1 = cr_0 * _S28 - ci_0 * _S29;

#line 2374
                        float _S30 = cr_0 * _S29 + ci_0 * _S28;

#line 2374
                        k2_1 = k2_1 + 1U;

#line 2374
                        cr_0 = nr_1;

#line 2374
                        ci_0 = _S30;

#line 2374
                    }

#line 2374
                    uint per_2 = 16U / _S14;

#line 2374
                    uint _S31 = max(2U, 1U);

#line 2374
                    _S17 = _S31;

#line 2374
                    uint blk2_2 = tid_0 / _S31;

#line 2374
                    uint lane2_2 = tid_0 % _S31;

#line 2374
                    for(;;)
                    {

#line 2374
                        uint _S32 = (1U << lgTB_1) - 1U;

#line 2374
                        _S18 = _S32;

#line 2374
                        thread array<uint, int(16)> src_1;

#line 2374
                        d_2 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            uint p_1 = computeWant_0(d_2, 32U, 512U, blk_2, lane_2, per_2, _S31, 32U, blk2_2, lane2_2);

#line 2374
                            uint rem_1 = p_1 & _S15;

#line 2374
                            src_1[d_2] = (rem_1 >> lgTB_1) * 512U + ((p_1 >> _S13) << lgTB_1) + (rem_1 & _S32);

#line 2374
                            d_2 = d_2 + 1U;

#line 2374
                        }

#line 2374
                        thread array<float, int(16)> xr_1;

#line 2374
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2374
                        j_1 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            (*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + j_1 * 512U + (&kernelContext_0)->_tid_0] = (as_type<uint>((r_3[j_1].x)));

#line 2374
                            j_1 = j_1 + 1U;

#line 2374
                        }

#line 2374
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2374
                        d_2 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            xr_1[d_2] = (as_type<float>(((*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + src_1[d_2]])));

#line 2374
                            d_2 = d_2 + 1U;

#line 2374
                        }

#line 2374
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2374
                        j_1 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            (*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + j_1 * 512U + (&kernelContext_0)->_tid_0] = (as_type<uint>((r_3[j_1].y)));

#line 2374
                            j_1 = j_1 + 1U;

#line 2374
                        }

#line 2374
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2374
                        d_2 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            r_3[d_2] = float2(xr_1[d_2], (as_type<float>(((*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + src_1[d_2]]))));

#line 2374
                            d_2 = d_2 + 1U;

#line 2374
                        }

#line 2374
                        break;
                    }

#line 2374
                    break;
                }

#line 2374
                break;
            }

#line 2374
            for(;;)
            {

#line 2374
                for(;;)
                {

#line 2374
                    uint lgTB_2 = firstbithigh_0(2U);

#line 2374
                    uint blk_3 = tid_0 >> lgTB_2;

#line 2374
                    uint lane_3 = tid_0 & 1U;

#line 2374
                    dft16_0(&r_3);

#line 2374
                    float2 tw_2 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 32.0f);

#line 2374
                    float _S33 = tw_2.x;

#line 2374
                    float _S34 = tw_2.y;

#line 2374
                    k2_1 = 0U;

#line 2374
                    cr_0 = 1.0f;

#line 2374
                    ci_0 = 0.0f;

#line 2374
                    for(;;)
                    {

#line 2374
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2374
                            break;
                        }

#line 2374
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2374
                        float nr_2 = cr_0 * _S33 - ci_0 * _S34;

#line 2374
                        float _S35 = cr_0 * _S34 + ci_0 * _S33;

#line 2374
                        k2_1 = k2_1 + 1U;

#line 2374
                        cr_0 = nr_2;

#line 2374
                        ci_0 = _S35;

#line 2374
                    }

#line 2374
                    uint per_3 = 16U / _S17;

#line 2374
                    uint _S36 = max(0U, 1U);

#line 2374
                    uint blk2_3 = tid_0 / _S36;

#line 2374
                    uint lane2_3 = tid_0 % _S36;

#line 2374
                    for(;;)
                    {

#line 2374
                        uint _S37 = (1U << lgTB_2) - 1U;

#line 2374
                        thread array<uint, int(16)> src_2;

#line 2374
                        d_2 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            uint p_2 = computeWant_0(d_2, 2U, 32U, blk_3, lane_3, per_3, _S36, 2U, blk2_3, lane2_3);

#line 2374
                            uint rem_2 = p_2 & _S18;

#line 2374
                            src_2[d_2] = (rem_2 >> lgTB_2) * 512U + ((p_2 >> _S16) << lgTB_2) + (rem_2 & _S37);

#line 2374
                            d_2 = d_2 + 1U;

#line 2374
                        }

#line 2374
                        thread array<float, int(16)> xr_2;

#line 2374
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2374
                        j_1 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            (*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + j_1 * 512U + (&kernelContext_0)->_tid_0] = (as_type<uint>((r_3[j_1].x)));

#line 2374
                            j_1 = j_1 + 1U;

#line 2374
                        }

#line 2374
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2374
                        d_2 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            xr_2[d_2] = (as_type<float>(((*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + src_2[d_2]])));

#line 2374
                            d_2 = d_2 + 1U;

#line 2374
                        }

#line 2374
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2374
                        j_1 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            (*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + j_1 * 512U + (&kernelContext_0)->_tid_0] = (as_type<uint>((r_3[j_1].y)));

#line 2374
                            j_1 = j_1 + 1U;

#line 2374
                        }

#line 2374
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2374
                        d_2 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            r_3[d_2] = float2(xr_2[d_2], (as_type<float>(((*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + src_2[d_2]]))));

#line 2374
                            d_2 = d_2 + 1U;

#line 2374
                        }

#line 2374
                        break;
                    }

#line 2374
                    break;
                }

#line 2374
                break;
            }

#line 2374
            break;
        }

#line 2374
        innermost_0(&r_3);

#line 2374
        break;
    }

#line 2374
    k_0 = 0U;
    for(;;)
    {

#line 2375
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2375
            break;
        }

#line 2376
        uint index_0 = slotToIndex_0(tid_0 * 16U + k_0);
        float _S38 = r_3[k_0].x;

#line 2377
        float _S39 = - r_3[k_0].y;

#line 2377
        float2 v_0 = float2(_S38, _S39);
        if(((&kernelContext_0)->entryPointParams_0->k0_0_0) == 0U)
        {

#line 2379
            if(index_0 < ((&kernelContext_0)->entryPointParams_0->B0_0))
            {

#line 2380
                float s_0 = (as_type<float>(((&kernelContext_0)->entryPointParams_0->scaleBits_0)));
                *((&kernelContext_0)->entryPointParams_band0_0+(_S19 * (&kernelContext_0)->entryPointParams_0->B0_0 + index_0)) = (as_type<ushort>((half)((_S38 * s_0)))) | ((as_type<ushort>((half)((_S39 * s_0)))) << 16U);

#line 2379
            }

#line 2378
        }
        else
        {


            if(index_0 >= ((&kernelContext_0)->entryPointParams_0->k0_0_0))
            {

#line 2383
                _S12 = index_0 < ((&kernelContext_0)->entryPointParams_0->k0_0_0 + (&kernelContext_0)->entryPointParams_0->B0_0);

#line 2383
            }
            else
            {

#line 2383
                _S12 = false;

#line 2383
            }

#line 2383
            if(_S12)
            {

#line 2383
                uint out0_0;

                if(index_0 < 4096U)
                {

#line 2386
                    float s_1 = (as_type<float>(((&kernelContext_0)->entryPointParams_0->scaleBits_0)));

#line 2386
                    out0_0 = (as_type<ushort>((half)((_S38 * s_1)))) | ((as_type<ushort>((half)((_S39 * s_1)))) << 16U);

#line 2385
                }
                else
                {

#line 2385
                    out0_0 = 0U;

#line 2385
                }



                *((&kernelContext_0)->entryPointParams_band0_0+(_S19 * (&kernelContext_0)->entryPointParams_0->B0_0 + (index_0 & ((&kernelContext_0)->entryPointParams_0->B0_0 - 1U)))) = out0_0;

#line 2383
            }

#line 2378
        }

#line 2391
        if(((&kernelContext_0)->entryPointParams_0->k0_1_0) == 0U)
        {

#line 2392
            if(index_0 < ((&kernelContext_0)->entryPointParams_0->B1_0))
            {

#line 2392
                *((&kernelContext_0)->entryPointParams_band1_0+(_S19 * (&kernelContext_0)->entryPointParams_0->B1_0 + index_0)) = packed_float2(v_0) ;

#line 2392
            }

#line 2391
        }
        else
        {
            if(((&kernelContext_0)->entryPointParams_0->B1_0) > 0U)
            {

#line 2394
                _S12 = index_0 >= ((&kernelContext_0)->entryPointParams_0->k0_1_0);

#line 2394
            }
            else
            {

#line 2394
                _S12 = false;

#line 2394
            }

#line 2394
            bool _S40;

#line 2394
            if(_S12)
            {

#line 2394
                _S40 = index_0 < ((&kernelContext_0)->entryPointParams_0->k0_1_0 + (&kernelContext_0)->entryPointParams_0->B1_0);

#line 2394
            }
            else
            {

#line 2394
                _S40 = false;

#line 2394
            }

#line 2394
            if(_S40)
            {

#line 2394
                packed_float2 device* _S41 = (&kernelContext_0)->entryPointParams_band1_0+(_S19 * (&kernelContext_0)->entryPointParams_0->B1_0 + (index_0 & ((&kernelContext_0)->entryPointParams_0->B1_0 - 1U)));

                if(index_0 < 4096U)
                {

#line 2396
                    x_2 = v_0;

#line 2396
                }
                else
                {

#line 2396
                    x_2 = float2(0.0f, 0.0f);

#line 2396
                }

#line 2396
                *_S41 = packed_float2(x_2) ;

#line 2394
            }

#line 2391
        }

#line 2375
        k_0 = k_0 + 1U;

#line 2375
    }

#line 2399
    return;
}
