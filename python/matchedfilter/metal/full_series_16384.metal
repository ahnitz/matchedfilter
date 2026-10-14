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


#line 168 "mm_16384_fullCorrelationSeries.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 168
    return float2(*(b_0+i_0)) ;
}


#line 270
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 270
    float _S2 = a_0.x;

#line 270
    float _S3 = b_1.x;

#line 270
    float _S4 = a_0.y;

#line 270
    float _S5 = b_1.y;

#line 270
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 475
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 477
    float2 t1_0 = *a_1 - *c_0;

#line 477
    float2 t2_0 = *b_2 + *d_0;

#line 477
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 479
    *b_2 = t1_0 + j3_0;

#line 479
    *c_0 = t0_0 - t2_0;

#line 479
    *d_0 = t1_0 - j3_0;
    return;
}


#line 269
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 269
    float _S6 = a_2.x;

#line 269
    float _S7 = b_3.x;

#line 269
    float _S8 = a_2.y;

#line 269
    float _S9 = b_3.y;

#line 269
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 511
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 518
    uint n1_0 = 0U;
    for(;;)
    {

#line 519
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 519
            break;
        }

#line 519
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 519
        n1_0 = n1_0 + 1U;

#line 519
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 520
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 520
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 521
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 521
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 522
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 522
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 522
    uint k2_0 = 0U;
    for(;;)
    {

#line 523
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 523
            break;
        }

#line 523
        uint _S10 = 4U * k2_0;

#line 523
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 523
        k2_0 = k2_0 + 1U;

#line 523
    }

    float2 t_0 = (*r_0)[int(1)];

#line 525
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 525
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 526
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 526
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 527
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 527
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 528
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 528
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 529
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 529
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 530
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 530
    (*r_0)[int(14)] = t_5;
    return;
}


#line 72 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 271 "mm_16384_fullCorrelationSeries.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 273
    uint j_0 = d_1 / _S11;

#line 273
    uint m_0 = d_1 % _S11;

#line 273
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 274
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 274
    }
    else
    {

#line 274
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 274
    }

#line 274
    return _S12;
}


#line 1660
struct EntryPointParams_0
{
    uint4 params_0;
};


#line 681
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(16384)> threadgroup* stg_0;
};


#line 660
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S13 = (1U << lgSpan_0) - 1U;
    uint _S14 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

#line 665
    uint d_2 = 0U;
    for(;;)
    {

#line 666
        if(d_2 < 16U)
        {
        }
        else
        {

#line 666
            break;
        }

#line 667
        uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
        uint rem_0 = p_0 & _S14;
        src_0[d_2] = (rem_0 >> lgSpan_0) * 1024U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S13);

#line 666
        d_2 = d_2 + 1U;

#line 666
    }

#line 671
    thread array<float, int(16)> xr_0;

#line 678
    bool local_0 = TB_1 <= 32U;

    if((TB_1 << 4U) <= 32U)
    {

#line 680
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 680
    }
    else
    {

#line 680
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 680
    }

#line 680
    uint j_1 = 0U;
    for(;;)
    {

#line 681
        if(j_1 < 16U)
        {
        }
        else
        {

#line 681
            break;
        }

#line 681
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 1024U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].x)));

#line 681
        j_1 = j_1 + 1U;

#line 681
    }
    if(local_0)
    {

#line 682
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 682
    }
    else
    {

#line 682
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 682
    }

#line 682
    d_2 = 0U;
    for(;;)
    {

#line 683
        if(d_2 < 16U)
        {
        }
        else
        {

#line 683
            break;
        }

#line 683
        xr_0[d_2] = (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]])));

#line 683
        d_2 = d_2 + 1U;

#line 683
    }
    if(local_0)
    {

#line 684
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 684
    }
    else
    {

#line 684
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 684
    }

#line 684
    j_1 = 0U;
    for(;;)
    {

#line 685
        if(j_1 < 16U)
        {
        }
        else
        {

#line 685
            break;
        }

#line 685
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 1024U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].y)));

#line 685
        j_1 = j_1 + 1U;

#line 685
    }
    if(local_0)
    {

#line 686
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 686
    }
    else
    {

#line 686
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 686
    }

#line 686
    d_2 = 0U;
    for(;;)
    {

#line 687
        if(d_2 < 16U)
        {
        }
        else
        {

#line 687
            break;
        }

#line 687
        (*r_1)[d_2] = float2(xr_0[d_2], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]]))));

#line 687
        d_2 = d_2 + 1U;

#line 687
    }

#line 698
    return;
}


#line 490
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 493
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 493
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 614
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 614
    uint b_4 = 0U;

#line 623
    for(;;)
    {

#line 623
        if(b_4 < 4U)
        {
        }
        else
        {

#line 623
            break;
        }

#line 623
        dft4_0(r_3, b_4 * 4U);

#line 623
        b_4 = b_4 + 1U;

#line 623
    }


    return;
}


#line 790
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 790
    uint _S15;

#line 790
    uint k2_1;

#line 790
    float cr_0;

#line 790
    float ci_0;

#line 790
    uint _S16;

#line 790
    uint _S17;

#line 790
    uint _S18;

#line 790
    for(;;)
    {

#line 790
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S15 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(16384U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 16384.0f);
                float _S19 = tw_0.x;

#line 27
                float _S20 = tw_0.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0f;

#line 27
                ci_0 = 0.0f;

                for(;;)
                {

#line 29
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S19 - ci_0 * _S20;
                    float _S21 = cr_0 * _S20 + ci_0 * _S19;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S21;

#line 29
                }

#line 37
                uint per_2 = 16U / max(1024U, 1U);
                uint _S22 = max(64U, 1U);

#line 38
                _S16 = _S22;
                uint blk2_2 = tid_0 / _S22;

#line 39
                uint lane2_2 = tid_0 % _S22;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 1024U, 16384U, blk_2, lane_2, per_2, _S22, 1024U, blk2_2, lane2_2, kernelContext_1);

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


                uint lgTB_1 = firstbithigh_0(64U);

#line 11
                _S17 = lgTB_1;

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 63U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 1024.0f);
                float _S23 = tw_1.x;

#line 27
                float _S24 = tw_1.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0f;

#line 27
                ci_0 = 0.0f;

                for(;;)
                {

#line 29
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S23 - ci_0 * _S24;
                    float _S25 = cr_0 * _S24 + ci_0 * _S23;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S25;

#line 29
                }

#line 37
                uint per_3 = 16U / _S16;
                uint _S26 = max(4U, 1U);

#line 38
                _S18 = _S26;
                uint blk2_3 = tid_0 / _S26;

#line 39
                uint lane2_3 = tid_0 % _S26;

#line 39
                exchange_0(r_4, _S15, lgTB_1, 64U, 1024U, blk_3, lane_3, per_3, _S26, 64U, blk2_3, lane2_3, kernelContext_1);

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


                uint lgTB_2 = firstbithigh_0(4U);

                uint blk_4 = tid_0 >> lgTB_2;
                uint lane_4 = tid_0 & 3U;


                dft16_0(r_4);

#line 26
                float2 tw_2 = mfTwiddle_0(6.28318548202514648f * float(lane_4) / 64.0f);
                float _S27 = tw_2.x;

#line 27
                float _S28 = tw_2.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0f;

#line 27
                ci_0 = 0.0f;

                for(;;)
                {

#line 29
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_2 = cr_0 * _S27 - ci_0 * _S28;
                    float _S29 = cr_0 * _S28 + ci_0 * _S27;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_2;

#line 29
                    ci_0 = _S29;

#line 29
                }

#line 37
                uint per_4 = 16U / _S18;
                uint _S30 = max(0U, 1U);
                uint blk2_4 = tid_0 / _S30;

#line 39
                uint lane2_4 = tid_0 % _S30;

#line 39
                exchange_0(r_4, _S17, lgTB_2, 4U, 64U, blk_4, lane_4, per_4, _S30, 4U, blk2_4, lane2_4, kernelContext_1);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        break;
    }

#line 43
    innermost_0(r_4);

#line 793 "mm_16384_fullCorrelationSeries.slang"
    return;
}


#line 759
uint lgOf_0(uint i_1)
{

#line 759
    uint _S31;

#line 759
    if(i_1 < 3U)
    {

#line 759
        _S31 = 4U;

#line 759
    }
    else
    {

#line 759
        _S31 = 1U;

#line 759
    }

#line 759
    return _S31;
}


#line 761
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(4U);

    uint x_0 = slot_0 >> lg_0;

#line 765
    uint lg_1 = lgOf_0(3U);

    uint x_1 = x_0 >> lg_1;

#line 765
    uint lg_2 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_2;

#line 765
    uint lg_3 = lgOf_0(1U);

#line 765
    uint lg_4 = lgOf_0(0U);

#line 770
    return (((((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | (x_2 & ((1U << lg_3) - 1U))) << lg_4) | ((x_2 >> lg_3) & ((1U << lg_4) - 1U));
}


#line 1660
[[kernel]] void fullCorrelationSeries(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], uint device* entryPointParams_starts_1 [[buffer(3)]], packed_float2 device* entryPointParams_output_1 [[buffer(4)]])
{

#line 1660
    thread KernelContext_0 kernelContext_2;

#line 1660
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 1660
    (&kernelContext_2)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1660
    (&kernelContext_2)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1660
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1660
    (&kernelContext_2)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1660
    threadgroup array<uint, int(16384)> stg_1;

#line 1660
    (&kernelContext_2)->stg_0 = &stg_1;

#line 1665
    uint pair_0 = gid_0.x;

#line 1665
    uint tid_1 = lid_0.x;
    uint d_3 = pair_0 / entryPointParams_1->params_0.x;

#line 1666
    uint _S32 = pair_0 % entryPointParams_1->params_0.x;
    uint _S33 = (&kernelContext_2)->entryPointParams_starts_0[d_3];
    (&kernelContext_2)->_tid_0 = tid_1;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 1670
    uint i_2 = 0U;
    for(;;)
    {

#line 1671
        if(i_2 < 16U)
        {
        }
        else
        {

#line 1671
            break;
        }

#line 1672
        uint idx_0 = tid_1 + 1024U * i_2;
        r_5[i_2] = cmulConj_0(cload_0((&kernelContext_2)->entryPointParams_data_0, d_3 * 16384U + idx_0), cload_0((&kernelContext_2)->entryPointParams_tmpl_0, _S32 * 16384U + idx_0));

#line 1671
        i_2 = i_2 + 1U;

#line 1671
    }

#line 1671
    transform_0(&r_5, tid_1, &kernelContext_2);

#line 1671
    i_2 = 0U;

#line 1676
    for(;;)
    {

#line 1676
        if(i_2 < 16U)
        {
        }
        else
        {

#line 1676
            break;
        }

#line 1677
        uint lag_0 = slotToIndex_0(tid_1 * 16U + i_2);

#line 1677
        bool _S34;
        if(lag_0 >= (entryPointParams_1->params_0.z))
        {

#line 1678
            _S34 = lag_0 < (entryPointParams_1->params_0.w);

#line 1678
        }
        else
        {

#line 1678
            _S34 = false;

#line 1678
        }

#line 1678
        bool _S35;

#line 1678
        if(_S34)
        {

#line 1678
            _S35 = lag_0 < (entryPointParams_1->params_0.y - _S33);

#line 1678
        }
        else
        {

#line 1678
            _S35 = false;

#line 1678
        }

#line 1678
        if(_S35)
        {

#line 1678
            *((&kernelContext_2)->entryPointParams_output_0+(_S32 * entryPointParams_1->params_0.y + _S33 + lag_0)) = packed_float2(float2(r_5[i_2].x, r_5[i_2].y)) ;

#line 1678
        }

#line 1676
        i_2 = i_2 + 1U;

#line 1676
    }

#line 1681
    return;
}
