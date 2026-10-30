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


#line 2083 "bands.slang"
float2 seriesSample_0(packed_float2 device* series_0, uint i_0, uint layout_0)
{
    if(layout_0 == 0U)
    {

#line 2086
        return float2(*(series_0+i_0)) ;
    }

#line 2087
    uint f_0 = (layout_0 >> 2U) + (layout_0 & 3U) * i_0;

#line 2087
    float2 _S2 = float2(*(series_0+(f_0 >> 1U))) ;

#line 2087
    float _S3;

    if((f_0 & 1U) != 0U)
    {

#line 2089
        _S3 = _S2.y;

#line 2089
    }
    else
    {

#line 2089
        _S3 = _S2.x;

#line 2089
    }

#line 2089
    return float2(_S3, 0.0f);
}


#line 494
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 496
    float2 t1_0 = *a_0 - *c_0;

#line 496
    float2 t2_0 = *b_0 + *d_0;

#line 496
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 498
    *b_0 = t1_0 + j3_0;

#line 498
    *c_0 = t0_0 - t2_0;

#line 498
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


#line 530
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 537
    uint n1_0 = 0U;
    for(;;)
    {

#line 538
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 538
            break;
        }

#line 538
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 538
        n1_0 = n1_0 + 1U;

#line 538
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 539
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 539
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 540
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 540
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 541
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 541
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 541
    uint k2_0 = 0U;
    for(;;)
    {

#line 542
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 542
            break;
        }

#line 542
        uint _S8 = 4U * k2_0;

#line 542
        r4_0(&(*r_0)[_S8], &(*r_0)[_S8 + 1U], &(*r_0)[_S8 + 2U], &(*r_0)[_S8 + 3U]);

#line 542
        k2_0 = k2_0 + 1U;

#line 542
    }

    float2 t_0 = (*r_0)[int(1)];

#line 544
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 544
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 545
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 545
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 546
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 546
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 547
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 547
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 548
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 548
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 549
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 549
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


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint seriesLength_0;
    uint B0_0;
    uint B1_0;
    uint scaleBits_0;
    uint seriesLayout_0;
};


#line 306 "bands.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    uint device* entryPointParams_band0_0;
    packed_float2 device* entryPointParams_band1_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(256)> threadgroup* stg_0;
};


#line 306
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 306
    uint _S11 = 2U * i_1;

#line 306
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11] = (as_type<uint>((v_0.x)));

#line 306
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11 + 1U] = (as_type<uint>((v_0.y)));

#line 306
    return;
}


#line 307
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 307
    uint _S12 = 2U * i_2;

#line 307
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12 + 1U]))));
}


#line 719
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 720
    uint j_1;

#line 731
    thread array<float2, int(16)> out_0;

#line 731
    uint z_0 = 0U;
    for(;;)
    {

#line 732
        if(z_0 < 16U)
        {
        }
        else
        {

#line 732
            break;
        }

#line 732
        out_0[z_0] = float2(0.0f, 0.0f);

#line 732
        z_0 = z_0 + 1U;

#line 732
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S13 = p0_0 & lenMask_0;

#line 738
    uint _S14 = (_S13 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

#line 738
    uint c_1 = 0U;

    for(;;)
    {

#line 740
        if(c_1 < 1U)
        {
        }
        else
        {

#line 740
            break;
        }

#line 741
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
            stgPut_0(j_1 * 8U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 742
            j_1 = j_1 + 1U;

#line 742
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 743
        uint d_2 = 0U;
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

#line 745
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S15 = pz_0 & lenMask_0;
            uint az_0 = (_S15 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 747
            float2 _S16 = stgGet_0(_S14 + az_0 - c_1 * 16U * 8U, kernelContext_2);


            out_0[d_2] = _S16;

#line 744
            d_2 = d_2 + 1U;

#line 744
        }

#line 740
        c_1 = c_1 + 1U;

#line 740
    }

#line 740
    j_1 = 0U;

#line 753
    for(;;)
    {

#line 753
        if(j_1 < 16U)
        {
        }
        else
        {

#line 753
            break;
        }

#line 753
        (*r_1)[j_1] = out_0[j_1];

#line 753
        j_1 = j_1 + 1U;

#line 753
    }
    return;
}


#line 514
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_2;

#line 518
    uint s_0 = 1U;
    for(;;)
    {

#line 519
        if(s_0 < 8U)
        {
        }
        else
        {

#line 519
            break;
        }

#line 519
        uint j_2 = 0U;
        for(;;)
        {

#line 520
            if(j_2 < 4U)
            {
            }
            else
            {

#line 520
                break;
            }

#line 521
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S17 = o_0 + j_2;

#line 524
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_0)), (*r_2)[_S17 + 4U]);
            uint _S18 = ((j_2 - k_0) << 1U) + k_0;

#line 525
            b_2[_S18] = (*r_2)[_S17] + t_6;

#line 525
            b_2[_S18 + s_0] = (*r_2)[_S17] - t_6;

#line 520
            j_2 = j_2 + 1U;

#line 520
        }

#line 520
        uint i_3 = 0U;

#line 527
        for(;;)
        {

#line 527
            if(i_3 < 8U)
            {
            }
            else
            {

#line 527
                break;
            }

#line 527
            (*r_2)[o_0 + i_3] = b_2[i_3];

#line 527
            i_3 = i_3 + 1U;

#line 527
        }

#line 519
        s_0 = s_0 << 1U;

#line 519
    }

#line 529
    return;
}


#line 633
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 633
    uint b_3 = 0U;

#line 641
    for(;;)
    {

#line 641
        if(b_3 < 2U)
        {
        }
        else
        {

#line 641
            break;
        }

#line 641
        dft8_0(r_3, b_3 * 8U);

#line 641
        b_3 = b_3 + 1U;

#line 641
    }



    return;
}


#line 2073
void forwardTransform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 2073
    for(;;)
    {

#line 2073
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(8U);
                uint lgLn_0 = firstbithigh_0(128U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 7U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 128.0f);
                float _S19 = tw_0.x;

#line 40
                float _S20 = tw_0.y;

#line 40
                uint k2_1 = 0U;

#line 40
                float cr_0 = 1.0f;

#line 40
                float ci_0 = 0.0f;

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
                uint per_2 = 16U / max(8U, 1U);
                uint _S22 = max(0U, 1U);
                uint blk2_2 = tid_0 / _S22;

#line 52
                uint lane2_2 = tid_0 % _S22;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 8U, 128U, blk_2, lane_2, per_2, _S22, 8U, blk2_2, lane2_2, kernelContext_3);

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

#line 2076 "bands.slang"
    return;
}


#line 778
uint lgOf_0(uint i_4)
{

#line 778
    uint _S23;

#line 778
    if(i_4 < 1U)
    {

#line 778
        _S23 = 4U;

#line 778
    }
    else
    {

#line 778
        if(i_4 == 1U)
        {

#line 778
            _S23 = 3U;

#line 778
        }
        else
        {

#line 778
            _S23 = 1U;

#line 778
        }

#line 778
    }

#line 778
    return _S23;
}


#line 780
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 784
    uint lg_1 = lgOf_0(0U);

#line 789
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 2246
[[kernel]] void forwardTier0(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], uint device* entryPointParams_band0_1 [[buffer(3)]], packed_float2 device* entryPointParams_band1_1 [[buffer(4)]])
{

#line 2246
    thread KernelContext_0 kernelContext_4;

#line 2246
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 2246
    (&kernelContext_4)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2246
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2246
    (&kernelContext_4)->entryPointParams_band0_0 = entryPointParams_band0_1;

#line 2246
    (&kernelContext_4)->entryPointParams_band1_0 = entryPointParams_band1_1;

#line 2246
    threadgroup array<uint, int(256)> stg_1;

#line 2246
    (&kernelContext_4)->stg_0 = &stg_1;

#line 2254
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    uint _S24 = gid_0.x;

#line 2257
    uint _S25 = entryPointParams_starts_1[_S24];
    thread array<float2, int(16)> r_5;

#line 2258
    uint k_1 = 0U;
    for(;;)
    {

#line 2259
        if(k_1 < 16U)
        {
        }
        else
        {

#line 2259
            break;
        }

#line 2260
        uint offset_0 = tid_1 + 8U * k_1;
        float2 _S26 = float2(0.0f, 0.0f);

#line 2261
        bool _S27;
        if(_S25 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0))
        {

#line 2262
            _S27 = offset_0 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0 - _S25);

#line 2262
        }
        else
        {

#line 2262
            _S27 = false;

#line 2262
        }

#line 2262
        float2 x_0;

#line 2262
        if(_S27)
        {

#line 2262
            x_0 = seriesSample_0((&kernelContext_4)->entryPointParams_series_0, _S25 + offset_0, (&kernelContext_4)->entryPointParams_0->seriesLayout_0);

#line 2262
        }
        else
        {

#line 2262
            x_0 = _S26;

#line 2262
        }

        r_5[k_1] = float2(x_0.x / 128.0f, - x_0.y / 128.0f);

#line 2259
        k_1 = k_1 + 1U;

#line 2259
    }

#line 2259
    forwardTransform_0(&r_5, tid_1, &kernelContext_4);

#line 2259
    k_1 = 0U;

#line 2267
    for(;;)
    {

#line 2267
        if(k_1 < 16U)
        {
        }
        else
        {

#line 2267
            break;
        }

#line 2268
        uint index_0 = slotToIndex_0(tid_1 * 16U + k_1);
        float _S28 = r_5[k_1].x;

#line 2269
        float _S29 = - r_5[k_1].y;

#line 2269
        float2 v_1 = float2(_S28, _S29);
        if(index_0 < ((&kernelContext_4)->entryPointParams_0->B0_0))
        {

#line 2271
            float s_1 = (as_type<float>(((&kernelContext_4)->entryPointParams_0->scaleBits_0)));
            *((&kernelContext_4)->entryPointParams_band0_0+(_S24 * (&kernelContext_4)->entryPointParams_0->B0_0 + index_0)) = (as_type<ushort>((half)((_S28 * s_1)))) | ((as_type<ushort>((half)((_S29 * s_1)))) << 16U);

#line 2270
        }



        if(index_0 < ((&kernelContext_4)->entryPointParams_0->B1_0))
        {

#line 2274
            *((&kernelContext_4)->entryPointParams_band1_0+(_S24 * (&kernelContext_4)->entryPointParams_0->B1_0 + index_0)) = packed_float2(v_1) ;

#line 2274
        }

#line 2267
        k_1 = k_1 + 1U;

#line 2267
    }

#line 2277
    return;
}
