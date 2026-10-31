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


#line 173 "mm_2048_fullCorrelationSeries.slang"
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


#line 324 "mm_2048_fullCorrelationSeries.slang"
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


#line 311
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(4096)> threadgroup* stg_0;
};


#line 311
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 311
    uint _S16 = 2U * i_1;

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S16] = (as_type<uint>((v_0.x)));

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S16 + 1U] = (as_type<uint>((v_0.y)));

#line 311
    return;
}


#line 312
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 312
    uint _S17 = 2U * i_2;

#line 312
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S17]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S17 + 1U]))));
}


#line 724
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 725
    uint j_1;

#line 736
    thread array<float2, int(16)> out_0;

#line 736
    uint z_1 = 0U;
    for(;;)
    {

#line 737
        if(z_1 < 16U)
        {
        }
        else
        {

#line 737
            break;
        }

#line 737
        out_0[z_1] = float2(0.0f, 0.0f);

#line 737
        z_1 = z_1 + 1U;

#line 737
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S18 = p0_0 & lenMask_0;

#line 743
    uint _S19 = (_S18 >> lgSpan_0) * 128U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S18 & spanMask_0);

#line 743
    uint c_2 = 0U;

    for(;;)
    {

#line 745
        if(c_2 < 1U)
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
            stgPut_0(j_1 * 128U + kernelContext_2->_tid_0, (*r_1)[c_2 * 16U + j_1], kernelContext_2);

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
            uint _S20 = pz_0 & lenMask_0;
            uint az_0 = (_S20 >> lgSpan_0) * 128U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S20 & spanMask_0);

#line 752
            float2 _S21 = stgGet_0(_S19 + az_0 - c_2 * 16U * 128U, kernelContext_2);


            out_0[d_2] = _S21;

#line 749
            d_2 = d_2 + 1U;

#line 749
        }

#line 745
        c_2 = c_2 + 1U;

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


#line 519
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_4;

#line 523
    uint s_1 = 1U;
    for(;;)
    {

#line 524
        if(s_1 < 8U)
        {
        }
        else
        {

#line 524
            break;
        }

#line 524
        uint j_2 = 0U;
        for(;;)
        {

#line 525
            if(j_2 < 4U)
            {
            }
            else
            {

#line 525
                break;
            }

#line 526
            uint k_0 = j_2 & (s_1 - 1U);

#line 526
            uint base_0 = (j_2 - k_0) << 1U;

            float2 w_0 = mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_1));
            uint _S22 = o_0 + j_2;

#line 529
            float2 t_6 = cmul_0(w_0, (*r_2)[_S22 + 4U]);
            uint _S23 = base_0 + k_0;

#line 530
            b_4[_S23] = (*r_2)[_S22] + t_6;

#line 530
            b_4[_S23 + s_1] = (*r_2)[_S22] - t_6;

#line 525
            j_2 = j_2 + 1U;

#line 525
        }

#line 525
        uint i_3 = 0U;

#line 532
        for(;;)
        {

#line 532
            if(i_3 < 8U)
            {
            }
            else
            {

#line 532
                break;
            }

#line 532
            (*r_2)[o_0 + i_3] = b_4[i_3];

#line 532
            i_3 = i_3 + 1U;

#line 532
        }

#line 524
        s_1 = s_1 << 1U;

#line 524
    }

#line 534
    return;
}


#line 638
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 638
    uint b_5 = 0U;

#line 646
    for(;;)
    {

#line 646
        if(b_5 < 2U)
        {
        }
        else
        {

#line 646
            break;
        }

#line 646
        dft8_0(r_3, b_5 * 8U);

#line 646
        b_5 = b_5 + 1U;

#line 646
    }



    return;
}


#line 829
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 829
    uint _S24;

#line 829
    uint k2_1;

#line 829
    float cr_0;

#line 829
    float ci_0;

#line 829
    uint _S25;

#line 829
    for(;;)
    {

#line 829
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(128U);

#line 11
                _S24 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(2048U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 127U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 2048.0f);
                float _S26 = tw_0.x;

#line 40
                float _S27 = tw_0.y;

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
                    float nr_0 = cr_0 * _S26 - ci_0 * _S27;
                    float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S28;

#line 42
                }

#line 50
                uint per_2 = 16U / max(128U, 1U);
                uint _S29 = max(8U, 1U);

#line 51
                _S25 = _S29;
                uint blk2_2 = tid_0 / _S29;

#line 52
                uint lane2_2 = tid_0 % _S29;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 128U, 2048U, blk_2, lane_2, per_2, _S29, 128U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(8U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 7U;


                dft16_0(r_4);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 128.0f);
                float _S30 = tw_1.x;

#line 40
                float _S31 = tw_1.y;

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
                    float nr_1 = cr_0 * _S30 - ci_0 * _S31;
                    float _S32 = cr_0 * _S31 + ci_0 * _S30;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S32;

#line 42
                }

#line 50
                uint per_3 = 16U / _S25;
                uint _S33 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S33;

#line 52
                uint lane2_3 = tid_0 % _S33;

#line 52
                exchange_0(r_4, _S24, lgTB_1, 8U, 128U, blk_3, lane_3, per_3, _S33, 8U, blk2_3, lane2_3, kernelContext_3);

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

#line 832 "mm_2048_fullCorrelationSeries.slang"
    return;
}


#line 783
uint lgOf_0(uint i_4)
{

#line 783
    uint _S34;

#line 783
    if(i_4 < 2U)
    {

#line 783
        _S34 = 4U;

#line 783
    }
    else
    {

#line 783
        if(i_4 == 2U)
        {

#line 783
            _S34 = 3U;

#line 783
        }
        else
        {

#line 783
            _S34 = 1U;

#line 783
        }

#line 783
    }

#line 783
    return _S34;
}


#line 785
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 789
    uint lg_1 = lgOf_0(1U);

#line 789
    uint lg_2 = lgOf_0(0U);

#line 794
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1752
[[kernel]] void fullCorrelationSeries(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], uint device* entryPointParams_starts_1 [[buffer(3)]], packed_float2 device* entryPointParams_output_1 [[buffer(4)]])
{

#line 1752
    thread KernelContext_0 kernelContext_4;

#line 1752
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1752
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1752
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1752
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1752
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1752
    threadgroup array<uint, int(4096)> stg_1;

#line 1752
    (&kernelContext_4)->stg_0 = &stg_1;

#line 1757
    uint pair_0 = gid_0.x;

#line 1757
    uint tid_1 = lid_0.x;
    uint d_3 = pair_0 / entryPointParams_1->params_0.x;

#line 1758
    uint _S35 = pair_0 % entryPointParams_1->params_0.x;
    uint _S36 = (&kernelContext_4)->entryPointParams_starts_0[d_3];
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 1762
    uint i_5 = 0U;
    for(;;)
    {

#line 1763
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1763
            break;
        }

#line 1764
        uint idx_0 = tid_1 + 128U * i_5;
        r_5[i_5] = cmulConj_0(cload_0((&kernelContext_4)->entryPointParams_data_0, d_3 * 2048U + idx_0), cload_0((&kernelContext_4)->entryPointParams_tmpl_0, _S35 * 2048U + idx_0));

#line 1763
        i_5 = i_5 + 1U;

#line 1763
    }

#line 1763
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 1763
    i_5 = 0U;

#line 1768
    for(;;)
    {

#line 1768
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1768
            break;
        }

#line 1769
        uint lag_0 = slotToIndex_0(tid_1 * 16U + i_5);

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
            *((&kernelContext_4)->entryPointParams_output_0+(_S35 * entryPointParams_1->params_0.y + _S36 + lag_0)) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 1770
        }

#line 1768
        i_5 = i_5 + 1U;

#line 1768
    }

#line 1773
    return;
}
