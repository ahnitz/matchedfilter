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


#line 2285 "bands.slang"
float2 seriesSample_0(packed_float2 device* series_0, uint i_0, uint layout_0)
{
    if(layout_0 == 0U)
    {

#line 2288
        return float2(*(series_0+i_0)) ;
    }

#line 2289
    uint f_0 = (layout_0 >> 2U) + (layout_0 & 3U) * i_0;

#line 2289
    float2 _S2 = float2(*(series_0+(f_0 >> 1U))) ;

#line 2289
    float _S3;

    if((f_0 & 1U) != 0U)
    {

#line 2291
        _S3 = _S2.y;

#line 2291
    }
    else
    {

#line 2291
        _S3 = _S2.x;

#line 2291
    }

#line 2291
    return float2(_S3, 0.0f);
}


#line 608
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 610
    float2 t1_0 = *a_0 - *c_0;

#line 610
    float2 t2_0 = *b_0 + *d_0;

#line 610
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 612
    *b_0 = t1_0 + j3_0;

#line 612
    *c_0 = t0_0 - t2_0;

#line 612
    *d_0 = t1_0 - j3_0;
    return;
}


#line 323
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 323
    float _S4 = a_1.x;

#line 323
    float _S5 = b_1.x;

#line 323
    float _S6 = a_1.y;

#line 323
    float _S7 = b_1.y;

#line 323
    return float2(_S4 * _S5 - _S6 * _S7, _S4 * _S7 + _S6 * _S5);
}


#line 644
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 651
    uint n1_0 = 0U;
    for(;;)
    {

#line 652
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 652
            break;
        }

#line 652
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 652
        n1_0 = n1_0 + 1U;

#line 652
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 653
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 653
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 654
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 654
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 655
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 655
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 655
    uint k2_0 = 0U;
    for(;;)
    {

#line 656
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 656
            break;
        }

#line 656
        uint _S8 = 4U * k2_0;

#line 656
        r4_0(&(*r_0)[_S8], &(*r_0)[_S8 + 1U], &(*r_0)[_S8 + 2U], &(*r_0)[_S8 + 3U]);

#line 656
        k2_0 = k2_0 + 1U;

#line 656
    }

    float2 t_0 = (*r_0)[int(1)];

#line 658
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 658
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 659
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 659
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 660
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 660
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 661
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 661
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 662
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 662
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 663
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 663
    (*r_0)[int(14)] = t_5;
    return;
}


#line 103 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 325 "bands.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S9 = max(TB_0, 1U);

#line 327
    uint j_0 = d_1 / _S9;

#line 327
    uint m_0 = d_1 % _S9;

#line 327
    uint _S10;
    if(TB_0 <= 16U)
    {

#line 328
        _S10 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 328
    }
    else
    {

#line 328
        _S10 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 328
    }

#line 328
    return _S10;
}


#line 623
void dft4_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    r4_0(&(*r_1)[o_0], &(*r_1)[o_0 + 1U], &(*r_1)[o_0 + 2U], &(*r_1)[o_0 + 3U]);
    float2 t_6 = (*r_1)[o_0 + 1U];

#line 626
    (*r_1)[o_0 + 1U] = (*r_1)[o_0 + 2U];

#line 626
    (*r_1)[o_0 + 2U] = t_6;
    return;
}


#line 747
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 747
    uint b_2 = 0U;

#line 756
    for(;;)
    {

#line 756
        if(b_2 < 4U)
        {
        }
        else
        {

#line 756
            break;
        }

#line 756
        dft4_0(r_2, b_2 * 4U);

#line 756
        b_2 = b_2 + 1U;

#line 756
    }


    return;
}


#line 875
uint lgOf_0(uint i_1)
{

#line 875
    uint _S11;

#line 875
    if(i_1 < 2U)
    {

#line 875
        _S11 = 4U;

#line 875
    }
    else
    {

#line 875
        _S11 = 1U;

#line 875
    }

#line 875
    return _S11;
}


#line 877
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 881
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 881
    uint lg_2 = lgOf_0(1U);

#line 881
    uint lg_3 = lgOf_0(0U);

#line 886
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 2453
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


#line 802
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    uint device* entryPointParams_band0_0;
    packed_float2 device* entryPointParams_band1_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 2453
[[kernel]] void forwardTier0(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], uint device* entryPointParams_band0_1 [[buffer(3)]], packed_float2 device* entryPointParams_band1_1 [[buffer(4)]])
{

#line 2453
    bool _S12;

#line 2453
    float2 x_2;

#line 2453
    uint _S13;

#line 2453
    uint k2_1;

#line 2453
    float cr_0;

#line 2453
    float ci_0;

#line 2453
    uint _S14;

#line 2453
    uint _S15;

#line 2453
    uint d_2;

#line 2453
    uint j_1;

#line 2453
    thread KernelContext_0 kernelContext_0;

#line 2453
    (&kernelContext_0)->entryPointParams_0 = entryPointParams_1;

#line 2453
    (&kernelContext_0)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2453
    (&kernelContext_0)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2453
    (&kernelContext_0)->entryPointParams_band0_0 = entryPointParams_band0_1;

#line 2453
    (&kernelContext_0)->entryPointParams_band1_0 = entryPointParams_band1_1;

#line 2453
    threadgroup array<uint, int(1024)> stg_1;

#line 2453
    (&kernelContext_0)->stg_0 = &stg_1;

#line 2461
    uint tid_0 = lid_0.x;
    (&kernelContext_0)->_tid_0 = tid_0;
    (&kernelContext_0)->_stgBase_0 = 0U;
    uint _S16 = gid_0.x;

#line 2464
    uint _S17 = entryPointParams_starts_1[_S16];
    thread array<float2, int(16)> r_3;

#line 2465
    uint k_0 = 0U;
    for(;;)
    {

#line 2466
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2466
            break;
        }

#line 2467
        uint offset_0 = tid_0 + 64U * k_0;
        float2 _S18 = float2(0.0f, 0.0f);
        if(_S17 < ((&kernelContext_0)->entryPointParams_0->seriesLength_0))
        {

#line 2469
            _S12 = offset_0 < ((&kernelContext_0)->entryPointParams_0->seriesLength_0 - _S17);

#line 2469
        }
        else
        {

#line 2469
            _S12 = false;

#line 2469
        }

#line 2469
        if(_S12)
        {

#line 2469
            x_2 = seriesSample_0((&kernelContext_0)->entryPointParams_series_0, _S17 + offset_0, (&kernelContext_0)->entryPointParams_0->seriesLayout_0);

#line 2469
        }
        else
        {

#line 2469
            x_2 = _S18;

#line 2469
        }

        r_3[k_0] = float2(x_2.x / 1024.0f, - x_2.y / 1024.0f);

#line 2466
        k_0 = k_0 + 1U;

#line 2466
    }

#line 2473
    for(;;)
    {

#line 2473
        for(;;)
        {

#line 2473
            for(;;)
            {

#line 2473
                for(;;)
                {

#line 2473
                    uint lgTB_0 = firstbithigh_0(64U);

#line 2473
                    _S13 = lgTB_0;

#line 2473
                    uint lgLn_0 = firstbithigh_0(1024U);

#line 2473
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2473
                    uint lane_1 = tid_0 & 63U;

#line 2473
                    dft16_0(&r_3);

#line 2473
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 1024.0f);

#line 2473
                    float _S19 = tw_0.x;

#line 2473
                    float _S20 = tw_0.y;

#line 2473
                    k2_1 = 0U;

#line 2473
                    cr_0 = 1.0f;

#line 2473
                    ci_0 = 0.0f;

#line 2473
                    for(;;)
                    {

#line 2473
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2473
                            break;
                        }

#line 2473
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2473
                        float nr_0 = cr_0 * _S19 - ci_0 * _S20;

#line 2473
                        float _S21 = cr_0 * _S20 + ci_0 * _S19;

#line 2473
                        k2_1 = k2_1 + 1U;

#line 2473
                        cr_0 = nr_0;

#line 2473
                        ci_0 = _S21;

#line 2473
                    }

#line 2473
                    uint per_1 = 16U / max(64U, 1U);

#line 2473
                    uint _S22 = max(4U, 1U);

#line 2473
                    _S14 = _S22;

#line 2473
                    uint blk2_1 = tid_0 / _S22;

#line 2473
                    uint lane2_1 = tid_0 % _S22;

#line 2473
                    for(;;)
                    {

#line 2473
                        uint _S23 = (1U << lgTB_0) - 1U;

#line 2473
                        _S15 = _S23;

#line 2473
                        uint _S24 = (1U << lgLn_0) - 1U;

#line 2473
                        thread array<uint, int(16)> src_0;

#line 2473
                        d_2 = 0U;

#line 2473
                        for(;;)
                        {

#line 2473
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2473
                                break;
                            }

#line 2473
                            uint p_0 = computeWant_0(d_2, 64U, 1024U, blk_1, lane_1, per_1, _S22, 64U, blk2_1, lane2_1);

#line 2473
                            uint rem_0 = p_0 & _S24;

#line 2473
                            src_0[d_2] = (rem_0 >> lgTB_0) * 64U + ((p_0 >> lgLn_0) << lgTB_0) + (rem_0 & _S23);

#line 2473
                            d_2 = d_2 + 1U;

#line 2473
                        }

#line 2473
                        thread array<float, int(16)> xr_0;

#line 2473
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2473
                        j_1 = 0U;

#line 2473
                        for(;;)
                        {

#line 2473
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2473
                                break;
                            }

#line 2473
                            (*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + j_1 * 64U + (&kernelContext_0)->_tid_0] = (as_type<uint>((r_3[j_1].x)));

#line 2473
                            j_1 = j_1 + 1U;

#line 2473
                        }

#line 2473
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2473
                        d_2 = 0U;

#line 2473
                        for(;;)
                        {

#line 2473
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2473
                                break;
                            }

#line 2473
                            xr_0[d_2] = (as_type<float>(((*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + src_0[d_2]])));

#line 2473
                            d_2 = d_2 + 1U;

#line 2473
                        }

#line 2473
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2473
                        j_1 = 0U;

#line 2473
                        for(;;)
                        {

#line 2473
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2473
                                break;
                            }

#line 2473
                            (*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + j_1 * 64U + (&kernelContext_0)->_tid_0] = (as_type<uint>((r_3[j_1].y)));

#line 2473
                            j_1 = j_1 + 1U;

#line 2473
                        }

#line 2473
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2473
                        d_2 = 0U;

#line 2473
                        for(;;)
                        {

#line 2473
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2473
                                break;
                            }

#line 2473
                            r_3[d_2] = float2(xr_0[d_2], (as_type<float>(((*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + src_0[d_2]]))));

#line 2473
                            d_2 = d_2 + 1U;

#line 2473
                        }

#line 2473
                        break;
                    }

#line 2473
                    break;
                }

#line 2473
                break;
            }

#line 2473
            for(;;)
            {

#line 2473
                for(;;)
                {

#line 2473
                    uint lgTB_1 = firstbithigh_0(4U);

#line 2473
                    uint blk_2 = tid_0 >> lgTB_1;

#line 2473
                    uint lane_2 = tid_0 & 3U;

#line 2473
                    dft16_0(&r_3);

#line 2473
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 64.0f);

#line 2473
                    float _S25 = tw_1.x;

#line 2473
                    float _S26 = tw_1.y;

#line 2473
                    k2_1 = 0U;

#line 2473
                    cr_0 = 1.0f;

#line 2473
                    ci_0 = 0.0f;

#line 2473
                    for(;;)
                    {

#line 2473
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2473
                            break;
                        }

#line 2473
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2473
                        float nr_1 = cr_0 * _S25 - ci_0 * _S26;

#line 2473
                        float _S27 = cr_0 * _S26 + ci_0 * _S25;

#line 2473
                        k2_1 = k2_1 + 1U;

#line 2473
                        cr_0 = nr_1;

#line 2473
                        ci_0 = _S27;

#line 2473
                    }

#line 2473
                    uint per_2 = 16U / _S14;

#line 2473
                    uint _S28 = max(0U, 1U);

#line 2473
                    uint blk2_2 = tid_0 / _S28;

#line 2473
                    uint lane2_2 = tid_0 % _S28;

#line 2473
                    for(;;)
                    {

#line 2473
                        uint _S29 = (1U << lgTB_1) - 1U;

#line 2473
                        thread array<uint, int(16)> src_1;

#line 2473
                        d_2 = 0U;

#line 2473
                        for(;;)
                        {

#line 2473
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2473
                                break;
                            }

#line 2473
                            uint p_1 = computeWant_0(d_2, 4U, 64U, blk_2, lane_2, per_2, _S28, 4U, blk2_2, lane2_2);

#line 2473
                            uint rem_1 = p_1 & _S15;

#line 2473
                            src_1[d_2] = (rem_1 >> lgTB_1) * 64U + ((p_1 >> _S13) << lgTB_1) + (rem_1 & _S29);

#line 2473
                            d_2 = d_2 + 1U;

#line 2473
                        }

#line 2473
                        thread array<float, int(16)> xr_1;

#line 2473
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2473
                        j_1 = 0U;

#line 2473
                        for(;;)
                        {

#line 2473
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2473
                                break;
                            }

#line 2473
                            (*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + j_1 * 64U + (&kernelContext_0)->_tid_0] = (as_type<uint>((r_3[j_1].x)));

#line 2473
                            j_1 = j_1 + 1U;

#line 2473
                        }

#line 2473
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2473
                        d_2 = 0U;

#line 2473
                        for(;;)
                        {

#line 2473
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2473
                                break;
                            }

#line 2473
                            xr_1[d_2] = (as_type<float>(((*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + src_1[d_2]])));

#line 2473
                            d_2 = d_2 + 1U;

#line 2473
                        }

#line 2473
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2473
                        j_1 = 0U;

#line 2473
                        for(;;)
                        {

#line 2473
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2473
                                break;
                            }

#line 2473
                            (*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + j_1 * 64U + (&kernelContext_0)->_tid_0] = (as_type<uint>((r_3[j_1].y)));

#line 2473
                            j_1 = j_1 + 1U;

#line 2473
                        }

#line 2473
                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2473
                        d_2 = 0U;

#line 2473
                        for(;;)
                        {

#line 2473
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2473
                                break;
                            }

#line 2473
                            r_3[d_2] = float2(xr_1[d_2], (as_type<float>(((*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + src_1[d_2]]))));

#line 2473
                            d_2 = d_2 + 1U;

#line 2473
                        }

#line 2473
                        break;
                    }

#line 2473
                    break;
                }

#line 2473
                break;
            }

#line 2473
            break;
        }

#line 2473
        innermost_0(&r_3);

#line 2473
        break;
    }

#line 2473
    k_0 = 0U;
    for(;;)
    {

#line 2474
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2474
            break;
        }

#line 2475
        uint index_0 = slotToIndex_0(tid_0 * 16U + k_0);
        float _S30 = r_3[k_0].x;

#line 2476
        float _S31 = - r_3[k_0].y;

#line 2476
        float2 v_0 = float2(_S30, _S31);
        if(((&kernelContext_0)->entryPointParams_0->k0_0_0) == 0U)
        {

#line 2478
            if(index_0 < ((&kernelContext_0)->entryPointParams_0->B0_0))
            {

#line 2479
                float s_0 = (as_type<float>(((&kernelContext_0)->entryPointParams_0->scaleBits_0)));
                *((&kernelContext_0)->entryPointParams_band0_0+(_S16 * (&kernelContext_0)->entryPointParams_0->B0_0 + index_0)) = (as_type<ushort>((half)((_S30 * s_0)))) | ((as_type<ushort>((half)((_S31 * s_0)))) << 16U);

#line 2478
            }

#line 2477
        }
        else
        {


            if(index_0 >= ((&kernelContext_0)->entryPointParams_0->k0_0_0))
            {

#line 2482
                _S12 = index_0 < ((&kernelContext_0)->entryPointParams_0->k0_0_0 + (&kernelContext_0)->entryPointParams_0->B0_0);

#line 2482
            }
            else
            {

#line 2482
                _S12 = false;

#line 2482
            }

#line 2482
            if(_S12)
            {

#line 2482
                uint out0_0;

                if(index_0 < 512U)
                {

#line 2485
                    float s_1 = (as_type<float>(((&kernelContext_0)->entryPointParams_0->scaleBits_0)));

#line 2485
                    out0_0 = (as_type<ushort>((half)((_S30 * s_1)))) | ((as_type<ushort>((half)((_S31 * s_1)))) << 16U);

#line 2484
                }
                else
                {

#line 2484
                    out0_0 = 0U;

#line 2484
                }



                *((&kernelContext_0)->entryPointParams_band0_0+(_S16 * (&kernelContext_0)->entryPointParams_0->B0_0 + (index_0 & ((&kernelContext_0)->entryPointParams_0->B0_0 - 1U)))) = out0_0;

#line 2482
            }

#line 2477
        }

#line 2490
        if(((&kernelContext_0)->entryPointParams_0->k0_1_0) == 0U)
        {

#line 2491
            if(index_0 < ((&kernelContext_0)->entryPointParams_0->B1_0))
            {

#line 2491
                *((&kernelContext_0)->entryPointParams_band1_0+(_S16 * (&kernelContext_0)->entryPointParams_0->B1_0 + index_0)) = packed_float2(v_0) ;

#line 2491
            }

#line 2490
        }
        else
        {
            if(((&kernelContext_0)->entryPointParams_0->B1_0) > 0U)
            {

#line 2493
                _S12 = index_0 >= ((&kernelContext_0)->entryPointParams_0->k0_1_0);

#line 2493
            }
            else
            {

#line 2493
                _S12 = false;

#line 2493
            }

#line 2493
            bool _S32;

#line 2493
            if(_S12)
            {

#line 2493
                _S32 = index_0 < ((&kernelContext_0)->entryPointParams_0->k0_1_0 + (&kernelContext_0)->entryPointParams_0->B1_0);

#line 2493
            }
            else
            {

#line 2493
                _S32 = false;

#line 2493
            }

#line 2493
            if(_S32)
            {

#line 2493
                packed_float2 device* _S33 = (&kernelContext_0)->entryPointParams_band1_0+(_S16 * (&kernelContext_0)->entryPointParams_0->B1_0 + (index_0 & ((&kernelContext_0)->entryPointParams_0->B1_0 - 1U)));

                if(index_0 < 512U)
                {

#line 2495
                    x_2 = v_0;

#line 2495
                }
                else
                {

#line 2495
                    x_2 = float2(0.0f, 0.0f);

#line 2495
                }

#line 2495
                *_S33 = packed_float2(x_2) ;

#line 2493
            }

#line 2490
        }

#line 2474
        k_0 = k_0 + 1U;

#line 2474
    }

#line 2498
    return;
}
