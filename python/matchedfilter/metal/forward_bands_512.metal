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


#line 2134 "bands.slang"
float2 seriesSample_0(packed_float2 device* series_0, uint i_0, uint layout_0)
{
    if(layout_0 == 0U)
    {

#line 2137
        return float2(*(series_0+i_0)) ;
    }

#line 2138
    uint f_0 = (layout_0 >> 2U) + (layout_0 & 3U) * i_0;

#line 2138
    float2 _S2 = float2(*(series_0+(f_0 >> 1U))) ;

#line 2138
    float _S3;

    if((f_0 & 1U) != 0U)
    {

#line 2140
        _S3 = _S2.y;

#line 2140
    }
    else
    {

#line 2140
        _S3 = _S2.x;

#line 2140
    }

#line 2140
    return float2(_S3, 0.0f);
}


#line 499
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 501
    float2 t1_0 = *a_0 - *c_0;

#line 501
    float2 t2_0 = *b_0 + *d_0;

#line 501
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 503
    *b_0 = t1_0 + j3_0;

#line 503
    *c_0 = t0_0 - t2_0;

#line 503
    *d_0 = t1_0 - j3_0;
    return;
}


#line 293
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 293
    float _S4 = a_1.x;

#line 293
    float _S5 = b_1.x;

#line 293
    float _S6 = a_1.y;

#line 293
    float _S7 = b_1.y;

#line 293
    return float2(_S4 * _S5 - _S6 * _S7, _S4 * _S7 + _S6 * _S5);
}


#line 535
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 542
    uint n1_0 = 0U;
    for(;;)
    {

#line 543
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 543
            break;
        }

#line 543
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 543
        n1_0 = n1_0 + 1U;

#line 543
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 544
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 544
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 545
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 545
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 546
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 546
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 546
    uint k2_0 = 0U;
    for(;;)
    {

#line 547
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 547
            break;
        }

#line 547
        uint _S8 = 4U * k2_0;

#line 547
        r4_0(&(*r_0)[_S8], &(*r_0)[_S8 + 1U], &(*r_0)[_S8 + 2U], &(*r_0)[_S8 + 3U]);

#line 547
        k2_0 = k2_0 + 1U;

#line 547
    }

    float2 t_0 = (*r_0)[int(1)];

#line 549
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 549
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 550
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 550
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 551
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 551
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 552
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 552
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 553
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 553
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 554
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 554
    (*r_0)[int(14)] = t_5;
    return;
}


#line 127 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 295 "bands.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S9 = max(TB_0, 1U);

#line 297
    uint j_0 = d_1 / _S9;

#line 297
    uint m_0 = d_1 % _S9;

#line 297
    uint _S10;
    if(TB_0 <= 16U)
    {

#line 298
        _S10 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 298
    }
    else
    {

#line 298
        _S10 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 298
    }

#line 298
    return _S10;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint seriesLength_0;
    uint B_0;
    uint seriesLayout_0;
};


#line 282 "bands.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_bands_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 282
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 282
    uint _S11 = 2U * i_1;

#line 282
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11] = (as_type<uint>((v_0.x)));

#line 282
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11 + 1U] = (as_type<uint>((v_0.y)));

#line 282
    return;
}


#line 283
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 283
    uint _S12 = 2U * i_2;

#line 283
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12 + 1U]))));
}


#line 724
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 725
    uint j_1;

#line 736
    thread array<float2, int(16)> out_0;

#line 736
    uint z_0 = 0U;
    for(;;)
    {

#line 737
        if(z_0 < 16U)
        {
        }
        else
        {

#line 737
            break;
        }

#line 737
        out_0[z_0] = float2(0.0f, 0.0f);

#line 737
        z_0 = z_0 + 1U;

#line 737
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S13 = p0_0 & lenMask_0;

#line 743
    uint _S14 = (_S13 >> lgSpan_0) * 32U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

#line 743
    uint c_1 = 0U;

    for(;;)
    {

#line 745
        if(c_1 < 1U)
        {
        }
        else
        {

#line 745
            break;
        }

#line 746
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 746
        j_1 = 0U;
        for(;;)
        {

#line 747
            if(j_1 < 16U)
            {
            }
            else
            {

#line 747
                break;
            }

#line 747
            stgPut_0(j_1 * 32U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 747
            j_1 = j_1 + 1U;

#line 747
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 748
        uint d_2 = 0U;
        for(;;)
        {

#line 749
            if(d_2 < 16U)
            {
            }
            else
            {

#line 749
                break;
            }

#line 750
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S15 = pz_0 & lenMask_0;
            uint az_0 = (_S15 >> lgSpan_0) * 32U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 752
            float2 _S16 = stgGet_0(_S14 + az_0 - c_1 * 16U * 32U, kernelContext_2);


            out_0[d_2] = _S16;

#line 749
            d_2 = d_2 + 1U;

#line 749
        }

#line 745
        c_1 = c_1 + 1U;

#line 745
    }

#line 745
    j_1 = 0U;

#line 758
    for(;;)
    {

#line 758
        if(j_1 < 16U)
        {
        }
        else
        {

#line 758
            break;
        }

#line 758
        (*r_1)[j_1] = out_0[j_1];

#line 758
        j_1 = j_1 + 1U;

#line 758
    }
    return;
}


#line 510
void dft2_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    float2 a_2 = (*r_2)[o_0];

#line 512
    float2 b_2 = (*r_2)[o_0 + 1U];

#line 512
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 512
    (*r_2)[o_0 + 1U] = a_2 - b_2;
    return;
}


#line 638
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 638
    uint b_3 = 0U;

#line 648
    for(;;)
    {

#line 648
        if(b_3 < 8U)
        {
        }
        else
        {

#line 648
            break;
        }

#line 648
        dft2_0(r_3, b_3 * 2U);

#line 648
        b_3 = b_3 + 1U;

#line 648
    }

    return;
}


#line 2124
void forwardTransform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 2124
    uint _S17;

#line 2124
    uint k2_1;

#line 2124
    float cr_0;

#line 2124
    float ci_0;

#line 2124
    uint _S18;

#line 2124
    for(;;)
    {

#line 2124
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(32U);

#line 11
                _S17 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(512U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 31U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 512.0f);
                float _S19 = tw_0.x;

#line 40
                float _S20 = tw_0.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S19 - ci_0 * _S20;
                    float _S21 = cr_0 * _S20 + ci_0 * _S19;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S21;

#line 42
                }

#line 50
                uint per_2 = 16U / max(32U, 1U);
                uint _S22 = max(2U, 1U);

#line 51
                _S18 = _S22;
                uint blk2_2 = tid_0 / _S22;

#line 52
                uint lane2_2 = tid_0 % _S22;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 32U, 512U, blk_2, lane_2, per_2, _S22, 32U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(2U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 1U;


                dft16_0(r_4);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 32.0f);
                float _S23 = tw_1.x;

#line 40
                float _S24 = tw_1.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S23 - ci_0 * _S24;
                    float _S25 = cr_0 * _S24 + ci_0 * _S23;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S25;

#line 42
                }

#line 50
                uint per_3 = 16U / _S18;
                uint _S26 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S26;

#line 52
                uint lane2_3 = tid_0 % _S26;

#line 52
                exchange_0(r_4, _S17, lgTB_1, 2U, 32U, blk_3, lane_3, per_3, _S26, 2U, blk2_3, lane2_3, kernelContext_3);

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

#line 2127 "bands.slang"
    return;
}


#line 783
uint lgOf_0(uint i_3)
{

#line 783
    uint _S27;

#line 783
    if(i_3 < 2U)
    {

#line 783
        _S27 = 4U;

#line 783
    }
    else
    {

#line 783
        _S27 = 1U;

#line 783
    }

#line 783
    return _S27;
}


#line 785
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 789
    uint lg_1 = lgOf_0(1U);

#line 789
    uint lg_2 = lgOf_0(0U);

#line 794
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2188
[[kernel]] void seriesForwardBands(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_bands_1 [[buffer(3)]])
{

#line 2188
    thread KernelContext_0 kernelContext_4;

#line 2188
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 2188
    (&kernelContext_4)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2188
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2188
    (&kernelContext_4)->entryPointParams_bands_0 = entryPointParams_bands_1;

#line 2188
    threadgroup array<uint, int(1024)> stg_1;

#line 2188
    (&kernelContext_4)->stg_0 = &stg_1;

#line 2194
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    uint _S28 = gid_0.x;

#line 2197
    uint _S29 = entryPointParams_starts_1[_S28];
    thread array<float2, int(16)> r_5;

#line 2198
    uint k_0 = 0U;
    for(;;)
    {

#line 2199
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2199
            break;
        }

#line 2200
        uint offset_0 = tid_1 + 32U * k_0;
        float2 _S30 = float2(0.0f, 0.0f);

#line 2201
        bool _S31;
        if(_S29 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0))
        {

#line 2202
            _S31 = offset_0 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0 - _S29);

#line 2202
        }
        else
        {

#line 2202
            _S31 = false;

#line 2202
        }

#line 2202
        float2 x_1;

#line 2202
        if(_S31)
        {

#line 2202
            x_1 = seriesSample_0((&kernelContext_4)->entryPointParams_series_0, _S29 + offset_0, (&kernelContext_4)->entryPointParams_0->seriesLayout_0);

#line 2202
        }
        else
        {

#line 2202
            x_1 = _S30;

#line 2202
        }

        r_5[k_0] = float2(x_1.x / 512.0f, - x_1.y / 512.0f);

#line 2199
        k_0 = k_0 + 1U;

#line 2199
    }

#line 2199
    forwardTransform_0(&r_5, tid_1, &kernelContext_4);

#line 2199
    k_0 = 0U;

#line 2207
    for(;;)
    {

#line 2207
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2207
            break;
        }

#line 2208
        uint index_0 = slotToIndex_0(tid_1 * 16U + k_0);
        if(index_0 < ((&kernelContext_4)->entryPointParams_0->B_0))
        {

#line 2209
            *((&kernelContext_4)->entryPointParams_bands_0+(_S28 * (&kernelContext_4)->entryPointParams_0->B_0 + index_0)) = packed_float2(float2(r_5[k_0].x, - r_5[k_0].y)) ;

#line 2209
        }

#line 2207
        k_0 = k_0 + 1U;

#line 2207
    }

#line 2212
    return;
}
