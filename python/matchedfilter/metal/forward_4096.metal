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


#line 2161 "forward.slang"
float2 seriesSample_0(packed_float2 device* series_0, uint i_0, uint layout_0)
{
    if(layout_0 == 0U)
    {

#line 2164
        return float2(*(series_0+i_0)) ;
    }

#line 2165
    uint f_0 = (layout_0 >> 2U) + (layout_0 & 3U) * i_0;

#line 2165
    float2 _S2 = float2(*(series_0+(f_0 >> 1U))) ;

#line 2165
    float _S3;

    if((f_0 & 1U) != 0U)
    {

#line 2167
        _S3 = _S2.y;

#line 2167
    }
    else
    {

#line 2167
        _S3 = _S2.x;

#line 2167
    }

#line 2167
    return float2(_S3, 0.0f);
}


#line 523
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 525
    float2 t1_0 = *a_0 - *c_0;

#line 525
    float2 t2_0 = *b_0 + *d_0;

#line 525
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 527
    *b_0 = t1_0 + j3_0;

#line 527
    *c_0 = t0_0 - t2_0;

#line 527
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


#line 559
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 566
    uint n1_0 = 0U;
    for(;;)
    {

#line 567
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 567
            break;
        }

#line 567
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 567
        n1_0 = n1_0 + 1U;

#line 567
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 568
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 568
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 569
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 569
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 570
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 570
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 570
    uint k2_0 = 0U;
    for(;;)
    {

#line 571
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 571
            break;
        }

#line 571
        uint _S8 = 4U * k2_0;

#line 571
        r4_0(&(*r_0)[_S8], &(*r_0)[_S8 + 1U], &(*r_0)[_S8 + 2U], &(*r_0)[_S8 + 3U]);

#line 571
        k2_0 = k2_0 + 1U;

#line 571
    }

    float2 t_0 = (*r_0)[int(1)];

#line 573
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 573
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 574
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 574
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 575
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 575
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 576
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 576
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 577
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 577
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 578
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 578
    (*r_0)[int(14)] = t_5;
    return;
}


#line 559
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_1 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_1 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_1 = float2(0.0f, 1.0f);
    float2 W6_1 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_1 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 566
    uint n1_1 = 0U;
    for(;;)
    {

#line 567
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 567
            break;
        }

#line 567
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 567
        n1_1 = n1_1 + 1U;

#line 567
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 568
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 568
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 569
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 569
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 570
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 570
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 570
    uint k2_1 = 0U;
    for(;;)
    {

#line 571
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 571
            break;
        }

#line 571
        uint _S9 = 4U * k2_1;

#line 571
        r4_0(&(*r_1)[_S9], &(*r_1)[_S9 + 1U], &(*r_1)[_S9 + 2U], &(*r_1)[_S9 + 3U]);

#line 571
        k2_1 = k2_1 + 1U;

#line 571
    }

    float2 t_6 = (*r_1)[int(1)];

#line 573
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 573
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 574
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 574
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 575
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 575
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 576
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 576
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 577
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 577
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 578
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 578
    (*r_1)[int(14)] = t_11;
    return;
}


#line 127 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 319 "forward.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S10 = max(TB_0, 1U);

#line 321
    uint j_0 = d_1 / _S10;

#line 321
    uint m_0 = d_1 % _S10;

#line 321
    uint _S11;
    if(TB_0 <= 16U)
    {

#line 322
        _S11 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 322
    }
    else
    {

#line 322
        _S11 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 322
    }

#line 322
    return _S11;
}


#line 8225 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint seriesLength_0;
    uint seriesLayout_0;
};


#line 738 "forward.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_spectra_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(4096)> threadgroup* stg_0;
};


#line 708
void exchange_0(array<float2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S12 = (1U << lgSpan_0) - 1U;
    uint _S13 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

#line 713
    uint d_2 = 0U;
    for(;;)
    {

#line 714
        if(d_2 < 16U)
        {
        }
        else
        {

#line 714
            break;
        }

#line 715
        uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
        uint rem_0 = p_0 & _S13;
        src_0[d_2] = (rem_0 >> lgSpan_0) * 256U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S12);

#line 714
        d_2 = d_2 + 1U;

#line 714
    }

#line 719
    thread array<float, int(16)> xr_0;

#line 737
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 737
    uint j_1 = 0U;
    for(;;)
    {

#line 738
        if(j_1 < 16U)
        {
        }
        else
        {

#line 738
            break;
        }

#line 738
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 256U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_2)[j_1].x)));

#line 738
        j_1 = j_1 + 1U;

#line 738
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 739
    d_2 = 0U;
    for(;;)
    {

#line 740
        if(d_2 < 16U)
        {
        }
        else
        {

#line 740
            break;
        }

#line 740
        xr_0[d_2] = (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]])));

#line 740
        d_2 = d_2 + 1U;

#line 740
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 741
    j_1 = 0U;
    for(;;)
    {

#line 742
        if(j_1 < 16U)
        {
        }
        else
        {

#line 742
            break;
        }

#line 742
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 256U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_2)[j_1].y)));

#line 742
        j_1 = j_1 + 1U;

#line 742
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 743
    d_2 = 0U;
    for(;;)
    {

#line 744
        if(d_2 < 16U)
        {
        }
        else
        {

#line 744
            break;
        }

#line 744
        (*r_2)[d_2] = float2(xr_0[d_2], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]]))));

#line 744
        d_2 = d_2 + 1U;

#line 744
    }

    return;
}


#line 662
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 669
    dft16_1(r_3);

#line 674
    return;
}


#line 2151
void forwardTransform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 2151
    uint _S14;

#line 2151
    uint k2_2;

#line 2151
    float cr_0;

#line 2151
    float ci_0;

#line 2151
    uint _S15;

#line 2151
    for(;;)
    {

#line 2151
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(256U);

#line 11
                _S14 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(4096U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 255U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 4096.0f);
                float _S16 = tw_0.x;

#line 40
                float _S17 = tw_0.y;

#line 40
                k2_2 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S16 - ci_0 * _S17;
                    float _S18 = cr_0 * _S17 + ci_0 * _S16;

#line 42
                    k2_2 = k2_2 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S18;

#line 42
                }

#line 50
                uint per_2 = 16U / max(256U, 1U);
                uint _S19 = max(16U, 1U);

#line 51
                _S15 = _S19;
                uint blk2_2 = tid_0 / _S19;

#line 52
                uint lane2_2 = tid_0 % _S19;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 256U, 4096U, blk_2, lane_2, per_2, _S19, 256U, blk2_2, lane2_2, kernelContext_1);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        for(;;)
        {

#line 7
            for(;;)
            {


                uint lgTB_1 = firstbithigh_0(16U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 15U;


                dft16_0(r_4);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 256.0f);
                float _S20 = tw_1.x;

#line 40
                float _S21 = tw_1.y;

#line 40
                k2_2 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S20 - ci_0 * _S21;
                    float _S22 = cr_0 * _S21 + ci_0 * _S20;

#line 42
                    k2_2 = k2_2 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S22;

#line 42
                }

#line 50
                uint per_3 = 16U / _S15;
                uint _S23 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S23;

#line 52
                uint lane2_3 = tid_0 % _S23;

#line 52
                exchange_0(r_4, _S14, lgTB_1, 16U, 256U, blk_3, lane_3, per_3, _S23, 16U, blk2_3, lane2_3, kernelContext_1);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        break;
    }

#line 56
    innermost_0(r_4);

#line 2154 "forward.slang"
    return;
}


#line 807
uint lgOf_0(uint i_1)
{

#line 807
    uint _S24;

#line 807
    if(i_1 < 2U)
    {

#line 807
        _S24 = 4U;

#line 807
    }
    else
    {

#line 807
        if(i_1 == 2U)
        {

#line 807
            _S24 = 4U;

#line 807
        }
        else
        {

#line 807
            _S24 = 1U;

#line 807
        }

#line 807
    }

#line 807
    return _S24;
}


#line 809
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 813
    uint lg_1 = lgOf_0(1U);

#line 813
    uint lg_2 = lgOf_0(0U);

#line 818
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2175
[[kernel]] void seriesForward(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]])
{

#line 2175
    thread KernelContext_0 kernelContext_2;

#line 2175
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2175
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2175
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2175
    (&kernelContext_2)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 2175
    threadgroup array<uint, int(4096)> stg_1;

#line 2175
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2181
    uint tid_1 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_1;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S25 = gid_0.x;

#line 2184
    uint _S26 = entryPointParams_starts_1[_S25];
    thread array<float2, int(16)> r_5;

#line 2185
    uint k_0 = 0U;
    for(;;)
    {

#line 2186
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2186
            break;
        }

#line 2187
        uint offset_0 = tid_1 + 256U * k_0;
        float2 _S27 = float2(0.0f, 0.0f);

#line 2188
        bool _S28;

        if(_S26 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2190
            _S28 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S26);

#line 2190
        }
        else
        {

#line 2190
            _S28 = false;

#line 2190
        }

#line 2190
        float2 x_1;

#line 2190
        if(_S28)
        {

#line 2190
            x_1 = seriesSample_0((&kernelContext_2)->entryPointParams_series_0, _S26 + offset_0, (&kernelContext_2)->entryPointParams_0->seriesLayout_0);

#line 2190
        }
        else
        {

#line 2190
            x_1 = _S27;

#line 2190
        }

        r_5[k_0] = float2(x_1.x / 4096.0f, - x_1.y / 4096.0f);

#line 2186
        k_0 = k_0 + 1U;

#line 2186
    }

#line 2186
    forwardTransform_0(&r_5, tid_1, &kernelContext_2);

#line 2186
    k_0 = 0U;

#line 2195
    for(;;)
    {

#line 2195
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2195
            break;
        }

#line 2195
        *((&kernelContext_2)->entryPointParams_spectra_0+(_S25 * 4096U + slotToIndex_0(tid_1 * 16U + k_0))) = packed_float2(float2(r_5[k_0].x, - r_5[k_0].y)) ;

#line 2195
        k_0 = k_0 + 1U;

#line 2195
    }



    return;
}
