#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
#ifndef MF_ACCURATE_TRIG
#define MF_ACCURATE_TRIG 0u
#endif

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


#line 173 "mm_8192_fullCorrelationSeries_lds32.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 173
    return float2(*(b_0+i_0)) ;
}


#line 323
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 323
    float _S2 = a_0.x;

#line 323
    float _S3 = b_1.x;

#line 323
    float _S4 = a_0.y;

#line 323
    float _S5 = b_1.y;

#line 323
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 499
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 501
    float2 t1_0 = *a_1 - *c_0;

#line 501
    float2 t2_0 = *b_2 + *d_0;

#line 501
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 503
    *b_2 = t1_0 + j3_0;

#line 503
    *c_0 = t0_0 - t2_0;

#line 503
    *d_0 = t1_0 - j3_0;
    return;
}


#line 322
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 322
    float _S6 = a_2.x;

#line 322
    float _S7 = b_3.x;

#line 322
    float _S8 = a_2.y;

#line 322
    float _S9 = b_3.y;

#line 322
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
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
        uint _S10 = 4U * k2_0;

#line 547
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

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


#line 74 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S11 = ((MF_ACCURATE_TRIG));

#line 77
    return _S11;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S12 = mfAccurateTrigFlag_0();

#line 103
    if(_S12 == 0U)
    {

#line 104
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S13 = float(quadrant_0);
    float x_0 = angle_0 - _S13 * 1.57079625129699707f - _S13 * 7.54978941586159635e-08f;
    float z_0 = x_0 * x_0;
    float c_1 = 1.0f + z_0 * (-0.5f + z_0 * (0.0416666679084301f + z_0 * (-0.00138888892251998f + z_0 * (0.00002480158764229f + z_0 * -2.75573199814971304e-07f))));

    float s_0 = x_0 * (1.0f + z_0 * (-0.1666666716337204f + z_0 * (0.00833333376795053f + z_0 * (-0.0001984127011383f + z_0 * (2.75573188446287531e-06f + z_0 * -2.50521079436794025e-08f)))));


    switch(quadrant_0 & int(3))
    {
    case int(1):
        {

#line 117
            return float2(- s_0, c_1);
        }
    case int(2):
        {

#line 118
            return float2(- c_1, - s_0);
        }
    case int(3):
        {

#line 119
            return float2(s_0, - c_1);
        }
    default:
        {

#line 120
            return float2(c_1, s_0);
        }
    }

#line 120
}


#line 324 "mm_8192_fullCorrelationSeries_lds32.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S14 = max(TB_0, 1U);

#line 326
    uint j_0 = d_1 / _S14;

#line 326
    uint m_0 = d_1 % _S14;

#line 326
    uint _S15;
    if(TB_0 <= 16U)
    {

#line 327
        _S15 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 327
    }
    else
    {

#line 327
        _S15 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 327
    }

#line 327
    return _S15;
}


#line 1752
struct EntryPointParams_0
{
    uint4 params_0;
};


#line 705
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 684
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S16 = (1U << lgSpan_0) - 1U;
    uint _S17 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

#line 689
    uint d_2 = 0U;
    for(;;)
    {

#line 690
        if(d_2 < 16U)
        {
        }
        else
        {

#line 690
            break;
        }

#line 691
        uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
        uint rem_0 = p_0 & _S17;
        src_0[d_2] = (rem_0 >> lgSpan_0) * 512U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S16);

#line 690
        d_2 = d_2 + 1U;

#line 690
    }

#line 695
    thread array<float, int(16)> xr_0;

#line 702
    bool local_0 = TB_1 <= 32U;

    if((TB_1 << 4U) <= 32U)
    {

#line 704
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 704
    }
    else
    {

#line 704
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 704
    }

#line 704
    uint j_1 = 0U;
    for(;;)
    {

#line 705
        if(j_1 < 16U)
        {
        }
        else
        {

#line 705
            break;
        }

#line 705
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 512U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].x)));

#line 705
        j_1 = j_1 + 1U;

#line 705
    }
    if(local_0)
    {

#line 706
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 706
    }
    else
    {

#line 706
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 706
    }

#line 706
    d_2 = 0U;
    for(;;)
    {

#line 707
        if(d_2 < 16U)
        {
        }
        else
        {

#line 707
            break;
        }

#line 707
        xr_0[d_2] = (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]])));

#line 707
        d_2 = d_2 + 1U;

#line 707
    }
    if(local_0)
    {

#line 708
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 708
    }
    else
    {

#line 708
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 708
    }

#line 708
    j_1 = 0U;
    for(;;)
    {

#line 709
        if(j_1 < 16U)
        {
        }
        else
        {

#line 709
            break;
        }

#line 709
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 512U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].y)));

#line 709
        j_1 = j_1 + 1U;

#line 709
    }
    if(local_0)
    {

#line 710
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 710
    }
    else
    {

#line 710
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 710
    }

#line 710
    d_2 = 0U;
    for(;;)
    {

#line 711
        if(d_2 < 16U)
        {
        }
        else
        {

#line 711
            break;
        }

#line 711
        (*r_1)[d_2] = float2(xr_0[d_2], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]]))));

#line 711
        d_2 = d_2 + 1U;

#line 711
    }

#line 722
    return;
}


#line 510
void dft2_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    float2 a_3 = (*r_2)[o_0];

#line 512
    float2 b_4 = (*r_2)[o_0 + 1U];

#line 512
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 512
    (*r_2)[o_0 + 1U] = a_3 - b_4;
    return;
}


#line 638
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 638
    uint b_5 = 0U;

#line 648
    for(;;)
    {

#line 648
        if(b_5 < 8U)
        {
        }
        else
        {

#line 648
            break;
        }

#line 648
        dft2_0(r_3, b_5 * 2U);

#line 648
        b_5 = b_5 + 1U;

#line 648
    }

    return;
}


#line 829
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 829
    uint _S18;

#line 829
    uint k2_1;

#line 829
    float cr_0;

#line 829
    float ci_0;

#line 829
    uint _S19;

#line 829
    uint _S20;

#line 829
    uint _S21;

#line 829
    for(;;)
    {

#line 829
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(512U);

#line 11
                _S18 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(8192U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 511U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 8192.0f);
                float _S22 = tw_0.x;

#line 40
                float _S23 = tw_0.y;

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
                    float nr_0 = cr_0 * _S22 - ci_0 * _S23;
                    float _S24 = cr_0 * _S23 + ci_0 * _S22;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S24;

#line 42
                }

#line 50
                uint per_2 = 16U / max(512U, 1U);
                uint _S25 = max(32U, 1U);

#line 51
                _S19 = _S25;
                uint blk2_2 = tid_0 / _S25;

#line 52
                uint lane2_2 = tid_0 % _S25;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 512U, 8192U, blk_2, lane_2, per_2, _S25, 512U, blk2_2, lane2_2, kernelContext_1);

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


                uint lgTB_1 = firstbithigh_0(32U);

#line 11
                _S20 = lgTB_1;

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 31U;


                dft16_0(r_4);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 512.0f);
                float _S26 = tw_1.x;

#line 40
                float _S27 = tw_1.y;

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
                    float nr_1 = cr_0 * _S26 - ci_0 * _S27;
                    float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S28;

#line 42
                }

#line 50
                uint per_3 = 16U / _S19;
                uint _S29 = max(2U, 1U);

#line 51
                _S21 = _S29;
                uint blk2_3 = tid_0 / _S29;

#line 52
                uint lane2_3 = tid_0 % _S29;

#line 52
                exchange_0(r_4, _S18, lgTB_1, 32U, 512U, blk_3, lane_3, per_3, _S29, 32U, blk2_3, lane2_3, kernelContext_1);

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


                uint lgTB_2 = firstbithigh_0(2U);

                uint blk_4 = tid_0 >> lgTB_2;
                uint lane_4 = tid_0 & 1U;


                dft16_0(r_4);

#line 39
                float2 tw_2 = mfTwiddle_0(6.28318548202514648f * float(lane_4) / 32.0f);
                float _S30 = tw_2.x;

#line 40
                float _S31 = tw_2.y;

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
                    float nr_2 = cr_0 * _S30 - ci_0 * _S31;
                    float _S32 = cr_0 * _S31 + ci_0 * _S30;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_2;

#line 42
                    ci_0 = _S32;

#line 42
                }

#line 50
                uint per_4 = 16U / _S21;
                uint _S33 = max(0U, 1U);
                uint blk2_4 = tid_0 / _S33;

#line 52
                uint lane2_4 = tid_0 % _S33;

#line 52
                exchange_0(r_4, _S20, lgTB_2, 2U, 32U, blk_4, lane_4, per_4, _S33, 2U, blk2_4, lane2_4, kernelContext_1);

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

#line 832 "mm_8192_fullCorrelationSeries_lds32.slang"
    return;
}


#line 783
uint lgOf_0(uint i_1)
{

#line 783
    uint _S34;

#line 783
    if(i_1 < 3U)
    {

#line 783
        _S34 = 4U;

#line 783
    }
    else
    {

#line 783
        _S34 = 1U;

#line 783
    }

#line 783
    return _S34;
}


#line 785
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_1 = slot_0 >> lg_0;

#line 789
    uint lg_1 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_1;

#line 789
    uint lg_2 = lgOf_0(1U);

#line 789
    uint lg_3 = lgOf_0(0U);

#line 794
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | (x_2 & ((1U << lg_2) - 1U))) << lg_3) | ((x_2 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 1752
[[kernel]] void fullCorrelationSeries(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], uint device* entryPointParams_starts_1 [[buffer(3)]], packed_float2 device* entryPointParams_output_1 [[buffer(4)]])
{

#line 1752
    thread KernelContext_0 kernelContext_2;

#line 1752
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 1752
    (&kernelContext_2)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1752
    (&kernelContext_2)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1752
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1752
    (&kernelContext_2)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1752
    threadgroup array<uint, int(8192)> stg_1;

#line 1752
    (&kernelContext_2)->stg_0 = &stg_1;

#line 1757
    uint pair_0 = gid_0.x;

#line 1757
    uint tid_1 = lid_0.x;
    uint d_3 = pair_0 / entryPointParams_1->params_0.x;

#line 1758
    uint _S35 = pair_0 % entryPointParams_1->params_0.x;
    uint _S36 = (&kernelContext_2)->entryPointParams_starts_0[d_3];
    (&kernelContext_2)->_tid_0 = tid_1;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 1762
    uint i_2 = 0U;
    for(;;)
    {

#line 1763
        if(i_2 < 16U)
        {
        }
        else
        {

#line 1763
            break;
        }

#line 1764
        uint idx_0 = tid_1 + 512U * i_2;
        r_5[i_2] = cmulConj_0(cload_0((&kernelContext_2)->entryPointParams_data_0, d_3 * 8192U + idx_0), cload_0((&kernelContext_2)->entryPointParams_tmpl_0, _S35 * 8192U + idx_0));

#line 1763
        i_2 = i_2 + 1U;

#line 1763
    }

#line 1763
    transform_0(&r_5, tid_1, &kernelContext_2);

#line 1763
    i_2 = 0U;

#line 1768
    for(;;)
    {

#line 1768
        if(i_2 < 16U)
        {
        }
        else
        {

#line 1768
            break;
        }

#line 1769
        uint lag_0 = slotToIndex_0(tid_1 * 16U + i_2);

#line 1769
        bool _S37;
        if(lag_0 >= (entryPointParams_1->params_0.z))
        {

#line 1770
            _S37 = lag_0 < (entryPointParams_1->params_0.w);

#line 1770
        }
        else
        {

#line 1770
            _S37 = false;

#line 1770
        }

#line 1770
        bool _S38;

#line 1770
        if(_S37)
        {

#line 1770
            _S38 = lag_0 < (entryPointParams_1->params_0.y - _S36);

#line 1770
        }
        else
        {

#line 1770
            _S38 = false;

#line 1770
        }

#line 1770
        if(_S38)
        {

#line 1770
            *((&kernelContext_2)->entryPointParams_output_0+(_S35 * entryPointParams_1->params_0.y + _S36 + lag_0)) = packed_float2(float2(r_5[i_2].x, r_5[i_2].y)) ;

#line 1770
        }

#line 1768
        i_2 = i_2 + 1U;

#line 1768
    }

#line 1773
    return;
}
