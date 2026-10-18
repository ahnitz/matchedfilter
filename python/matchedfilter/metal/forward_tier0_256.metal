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


#line 2112 "/tmp/tmpw29plkyi/tier0.slang"
float2 seriesSample_0(packed_float2 device* series_0, uint i_0, uint layout_0)
{
    if(layout_0 == 0U)
    {

#line 2115
        return float2(*(series_0+i_0)) ;
    }

#line 2116
    uint f_0 = (layout_0 >> 2U) + (layout_0 & 3U) * i_0;

#line 2116
    float2 _S2 = float2(*(series_0+(f_0 >> 1U))) ;

#line 2116
    float _S3;

    if((f_0 & 1U) != 0U)
    {

#line 2118
        _S3 = _S2.y;

#line 2118
    }
    else
    {

#line 2118
        _S3 = _S2.x;

#line 2118
    }

#line 2118
    return float2(_S3, 0.0f);
}


#line 486
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 488
    float2 t1_0 = *a_0 - *c_0;

#line 488
    float2 t2_0 = *b_0 + *d_0;

#line 488
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 490
    *b_0 = t1_0 + j3_0;

#line 490
    *c_0 = t0_0 - t2_0;

#line 490
    *d_0 = t1_0 - j3_0;
    return;
}


#line 280
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 280
    float _S4 = a_1.x;

#line 280
    float _S5 = b_1.x;

#line 280
    float _S6 = a_1.y;

#line 280
    float _S7 = b_1.y;

#line 280
    return float2(_S4 * _S5 - _S6 * _S7, _S4 * _S7 + _S6 * _S5);
}


#line 522
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 529
    uint n1_0 = 0U;
    for(;;)
    {

#line 530
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 530
            break;
        }

#line 530
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 530
        n1_0 = n1_0 + 1U;

#line 530
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 531
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 531
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 532
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 532
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 533
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 533
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 533
    uint k2_0 = 0U;
    for(;;)
    {

#line 534
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 534
            break;
        }

#line 534
        uint _S8 = 4U * k2_0;

#line 534
        r4_0(&(*r_0)[_S8], &(*r_0)[_S8 + 1U], &(*r_0)[_S8 + 2U], &(*r_0)[_S8 + 3U]);

#line 534
        k2_0 = k2_0 + 1U;

#line 534
    }

    float2 t_0 = (*r_0)[int(1)];

#line 536
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 536
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 537
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 537
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 538
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 538
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 539
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 539
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 540
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 540
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 541
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 541
    (*r_0)[int(14)] = t_5;
    return;
}


#line 522
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_1 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_1 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_1 = float2(0.0f, 1.0f);
    float2 W6_1 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_1 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 529
    uint n1_1 = 0U;
    for(;;)
    {

#line 530
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 530
            break;
        }

#line 530
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 530
        n1_1 = n1_1 + 1U;

#line 530
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 531
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 531
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 532
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 532
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 533
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 533
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 533
    uint k2_1 = 0U;
    for(;;)
    {

#line 534
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 534
            break;
        }

#line 534
        uint _S9 = 4U * k2_1;

#line 534
        r4_0(&(*r_1)[_S9], &(*r_1)[_S9 + 1U], &(*r_1)[_S9 + 2U], &(*r_1)[_S9 + 3U]);

#line 534
        k2_1 = k2_1 + 1U;

#line 534
    }

    float2 t_6 = (*r_1)[int(1)];

#line 536
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 536
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 537
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 537
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 538
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 538
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 539
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 539
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 540
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 540
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 541
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 541
    (*r_1)[int(14)] = t_11;
    return;
}


#line 84 "/home/ahnitz/projects/claude/searchdev/work/mf-backends/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 282 "/tmp/tmpw29plkyi/tier0.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S10 = max(TB_0, 1U);

#line 284
    uint j_0 = d_1 / _S10;

#line 284
    uint m_0 = d_1 % _S10;

#line 284
    uint _S11;
    if(TB_0 <= 16U)
    {

#line 285
        _S11 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 285
    }
    else
    {

#line 285
        _S11 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 285
    }

#line 285
    return _S11;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint seriesLength_0;
    uint B0_0;
    uint B1_0;
    uint seriesLayout_0;
};


#line 269 "/tmp/tmpw29plkyi/tier0.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    uint device* entryPointParams_band0_0;
    packed_float2 device* entryPointParams_band1_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(512)> threadgroup* stg_0;
};


#line 269
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 269
    uint _S12 = 2U * i_1;

#line 269
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S12] = (as_type<uint>((v_0.x)));

#line 269
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S12 + 1U] = (as_type<uint>((v_0.y)));

#line 269
    return;
}


#line 270
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 270
    uint _S13 = 2U * i_2;

#line 270
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S13]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S13 + 1U]))));
}


#line 711
void exchange_0(array<float2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 712
    uint j_1;

#line 723
    thread array<float2, int(16)> out_0;

#line 723
    uint z_0 = 0U;
    for(;;)
    {

#line 724
        if(z_0 < 16U)
        {
        }
        else
        {

#line 724
            break;
        }

#line 724
        out_0[z_0] = float2(0.0f, 0.0f);

#line 724
        z_0 = z_0 + 1U;

#line 724
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S14 = p0_0 & lenMask_0;

#line 730
    uint _S15 = (_S14 >> lgSpan_0) * 16U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);

#line 730
    uint c_1 = 0U;

    for(;;)
    {

#line 732
        if(c_1 < 1U)
        {
        }
        else
        {

#line 732
            break;
        }

#line 733
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 733
        j_1 = 0U;
        for(;;)
        {

#line 734
            if(j_1 < 16U)
            {
            }
            else
            {

#line 734
                break;
            }

#line 734
            stgPut_0(j_1 * 16U + kernelContext_2->_tid_0, (*r_2)[c_1 * 16U + j_1], kernelContext_2);

#line 734
            j_1 = j_1 + 1U;

#line 734
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 735
        uint d_2 = 0U;
        for(;;)
        {

#line 736
            if(d_2 < 16U)
            {
            }
            else
            {

#line 736
                break;
            }

#line 737
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S16 = pz_0 & lenMask_0;
            uint az_0 = (_S16 >> lgSpan_0) * 16U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 739
            float2 _S17 = stgGet_0(_S15 + az_0 - c_1 * 16U * 16U, kernelContext_2);


            out_0[d_2] = _S17;

#line 736
            d_2 = d_2 + 1U;

#line 736
        }

#line 732
        c_1 = c_1 + 1U;

#line 732
    }

#line 732
    j_1 = 0U;

#line 745
    for(;;)
    {

#line 745
        if(j_1 < 16U)
        {
        }
        else
        {

#line 745
            break;
        }

#line 745
        (*r_2)[j_1] = out_0[j_1];

#line 745
        j_1 = j_1 + 1U;

#line 745
    }
    return;
}


#line 625
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 632
    dft16_1(r_3);

#line 637
    return;
}


#line 2102
void forwardTransform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 2102
    for(;;)
    {

#line 2102
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/mf-backends/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(16U);
                uint lgLn_0 = firstbithigh_0(256U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 15U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 256.0f);
                float _S18 = tw_0.x;

#line 40
                float _S19 = tw_0.y;

#line 40
                uint k2_2 = 0U;

#line 40
                float cr_0 = 1.0f;

#line 40
                float ci_0 = 0.0f;

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
                    float nr_0 = cr_0 * _S18 - ci_0 * _S19;
                    float _S20 = cr_0 * _S19 + ci_0 * _S18;

#line 42
                    k2_2 = k2_2 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S20;

#line 42
                }

#line 50
                uint per_2 = 16U / max(16U, 1U);
                uint _S21 = max(1U, 1U);
                uint blk2_2 = tid_0 / _S21;

#line 52
                uint lane2_2 = tid_0 % _S21;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 16U, 256U, blk_2, lane_2, per_2, _S21, 16U, blk2_2, lane2_2, kernelContext_3);

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

#line 2105 "/tmp/tmpw29plkyi/tier0.slang"
    return;
}


#line 770
uint lgOf_0(uint i_3)
{

#line 770
    uint _S22;

#line 770
    if(i_3 < 1U)
    {

#line 770
        _S22 = 4U;

#line 770
    }
    else
    {

#line 770
        if(i_3 == 1U)
        {

#line 770
            _S22 = 4U;

#line 770
        }
        else
        {

#line 770
            _S22 = 1U;

#line 770
        }

#line 770
    }

#line 770
    return _S22;
}


#line 772
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 776
    uint lg_1 = lgOf_0(0U);

#line 781
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 2264
[[kernel]] void forwardTier0(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], uint device* entryPointParams_band0_1 [[buffer(3)]], packed_float2 device* entryPointParams_band1_1 [[buffer(4)]])
{

#line 2264
    thread KernelContext_0 kernelContext_4;

#line 2264
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 2264
    (&kernelContext_4)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2264
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2264
    (&kernelContext_4)->entryPointParams_band0_0 = entryPointParams_band0_1;

#line 2264
    (&kernelContext_4)->entryPointParams_band1_0 = entryPointParams_band1_1;

#line 2264
    threadgroup array<uint, int(512)> stg_1;

#line 2264
    (&kernelContext_4)->stg_0 = &stg_1;

#line 2271
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    uint _S23 = gid_0.x;

#line 2274
    uint _S24 = entryPointParams_starts_1[_S23];
    thread array<float2, int(16)> r_5;

#line 2275
    uint k_0 = 0U;
    for(;;)
    {

#line 2276
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2276
            break;
        }

#line 2277
        uint offset_0 = tid_1 + 16U * k_0;
        float2 _S25 = float2(0.0f, 0.0f);

#line 2278
        bool _S26;
        if(_S24 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0))
        {

#line 2279
            _S26 = offset_0 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0 - _S24);

#line 2279
        }
        else
        {

#line 2279
            _S26 = false;

#line 2279
        }

#line 2279
        float2 x_0;

#line 2279
        if(_S26)
        {

#line 2279
            x_0 = seriesSample_0((&kernelContext_4)->entryPointParams_series_0, _S24 + offset_0, (&kernelContext_4)->entryPointParams_0->seriesLayout_0);

#line 2279
        }
        else
        {

#line 2279
            x_0 = _S25;

#line 2279
        }

        r_5[k_0] = float2(x_0.x / 256.0f, - x_0.y / 256.0f);

#line 2276
        k_0 = k_0 + 1U;

#line 2276
    }

#line 2276
    forwardTransform_0(&r_5, tid_1, &kernelContext_4);

#line 2276
    k_0 = 0U;

#line 2284
    for(;;)
    {

#line 2284
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2284
            break;
        }

#line 2285
        uint index_0 = slotToIndex_0(tid_1 * 16U + k_0);
        float _S27 = r_5[k_0].x;

#line 2286
        float _S28 = - r_5[k_0].y;

#line 2286
        float2 v_1 = float2(_S27, _S28);
        if(index_0 < ((&kernelContext_4)->entryPointParams_0->B0_0))
        {

#line 2288
            *((&kernelContext_4)->entryPointParams_band0_0+(_S23 * (&kernelContext_4)->entryPointParams_0->B0_0 + index_0)) = (as_type<ushort>((half)((_S27)))) | ((as_type<ushort>((half)((_S28)))) << 16U);

#line 2287
        }

        if(index_0 < ((&kernelContext_4)->entryPointParams_0->B1_0))
        {

#line 2289
            *((&kernelContext_4)->entryPointParams_band1_0+(_S23 * (&kernelContext_4)->entryPointParams_0->B1_0 + index_0)) = packed_float2(v_1) ;

#line 2289
        }

#line 2284
        k_0 = k_0 + 1U;

#line 2284
    }

#line 2292
    return;
}
