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


#line 173 "mm_32768_fullCorrelation.slang"
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


#line 74 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S6 = ((MF_ACCURATE_TRIG));

#line 77
    return _S6;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S7 = mfAccurateTrigFlag_0();

#line 103
    if(_S7 == 0U)
    {

#line 104
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S8 = float(quadrant_0);
    float x_0 = angle_0 - _S8 * 1.57079625129699707f - _S8 * 7.54978941586159635e-08f;
    float z_0 = x_0 * x_0;
    float c_0 = 1.0f + z_0 * (-0.5f + z_0 * (0.0416666679084301f + z_0 * (-0.00138888892251998f + z_0 * (0.00002480158764229f + z_0 * -2.75573199814971304e-07f))));

    float s_0 = x_0 * (1.0f + z_0 * (-0.1666666716337204f + z_0 * (0.00833333376795053f + z_0 * (-0.0001984127011383f + z_0 * (2.75573188446287531e-06f + z_0 * -2.50521079436794025e-08f)))));


    switch(quadrant_0 & int(3))
    {
    case int(1):
        {

#line 117
            return float2(- s_0, c_0);
        }
    case int(2):
        {

#line 118
            return float2(- c_0, - s_0);
        }
    case int(3):
        {

#line 119
            return float2(s_0, - c_0);
        }
    default:
        {

#line 120
            return float2(c_0, s_0);
        }
    }

#line 120
}


#line 322 "mm_32768_fullCorrelation.slang"
float2 cmul_0(float2 a_1, float2 b_2)
{

#line 322
    float _S9 = a_1.x;

#line 322
    float _S10 = b_2.x;

#line 322
    float _S11 = a_1.y;

#line 322
    float _S12 = b_2.y;

#line 322
    return float2(_S9 * _S10 - _S11 * _S12, _S9 * _S12 + _S11 * _S10);
}


#line 499
void r4_0(float2 thread* a_2, float2 thread* b_3, float2 thread* c_1, float2 thread* d_0)
{
    float2 t0_0 = *a_2 + *c_1;

#line 501
    float2 t1_0 = *a_2 - *c_1;

#line 501
    float2 t2_0 = *b_3 + *d_0;

#line 501
    float2 t3_0 = *b_3 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_2 = t0_0 + t2_0;

#line 503
    *b_3 = t1_0 + j3_0;

#line 503
    *c_1 = t0_0 - t2_0;

#line 503
    *d_0 = t1_0 - j3_0;
    return;
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
        uint _S13 = 4U * k2_0;

#line 547
        r4_0(&(*r_0)[_S13], &(*r_0)[_S13 + 1U], &(*r_0)[_S13 + 2U], &(*r_0)[_S13 + 3U]);

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


#line 581
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 583
    thread array<float2, int(16)> v_0;

#line 583
    uint j_0 = 0U;
    for(;;)
    {

#line 584
        if(j_0 < 16U)
        {
        }
        else
        {

#line 584
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        float2 _S14 = (*r_1)[j_0] - (*r_1)[j_0 + 16U];

#line 588
        float2 _S15 = mfTwiddle_0(6.28318548202514648f * float(j_0) / 32.0f);

#line 588
        v_0[j_0] = cmul_0(_S14, _S15);

#line 584
        j_0 = j_0 + 1U;

#line 584
    }

#line 590
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 591
    uint k_0 = 0U;
    for(;;)
    {

#line 592
        if(k_0 < 16U)
        {
        }
        else
        {

#line 592
            break;
        }

#line 592
        uint _S16 = 2U * k_0;

#line 592
        (*r_1)[_S16] = u_0[k_0];

#line 592
        (*r_1)[_S16 + 1U] = v_0[k_0];

#line 592
        k_0 = k_0 + 1U;

#line 592
    }
    return;
}


#line 620
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 324
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S17 = max(TB_0, 1U);

#line 326
    uint j_1 = d_1 / _S17;

#line 326
    uint m_0 = d_1 % _S17;

#line 326
    uint _S18;
    if(TB_0 <= 32U)
    {

#line 327
        _S18 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 327
    }
    else
    {

#line 327
        _S18 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 327
    }

#line 327
    return _S18;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
};


#line 311 "mm_32768_fullCorrelation.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(16384)> threadgroup* stg_0;
};


#line 311
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 311
    uint _S19 = 2U * i_1;

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S19] = (as_type<uint>((v_1.x)));

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S19 + 1U] = (as_type<uint>((v_1.y)));

#line 311
    return;
}


#line 312
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 312
    uint _S20 = 2U * i_2;

#line 312
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20 + 1U]))));
}


#line 724
void exchange_0(array<float2, int(32)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 725
    uint j_2;

#line 736
    thread array<float2, int(32)> out_0;

#line 736
    uint z_1 = 0U;
    for(;;)
    {

#line 737
        if(z_1 < 32U)
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
    uint _S21 = p0_0 & lenMask_0;

#line 743
    uint _S22 = _S21 >> lgSpan_0;

#line 743
    uint _S23 = _S22 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S21 & spanMask_0);

#line 743
    uint c_2 = 0U;

    for(;;)
    {

#line 745
        if(c_2 < 4U)
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
        j_2 = 0U;
        for(;;)
        {

#line 747
            if(j_2 < 8U)
            {
            }
            else
            {

#line 747
                break;
            }

#line 747
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_2 * 8U + j_2], kernelContext_2);

#line 747
            j_2 = j_2 + 1U;

#line 747
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 748
        uint d_2 = 0U;
        for(;;)
        {

#line 749
            if(d_2 < 32U)
            {
            }
            else
            {

#line 749
                break;
            }

#line 750
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S24 = pz_0 & lenMask_0;

#line 751
            uint iz_0 = _S24 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S24 & spanMask_0);
            uint i_3 = _S22 + iz_0;
            uint _S25 = c_2 * 8U;

#line 754
            bool _S26;

#line 754
            if(i_3 >= _S25)
            {

#line 754
                _S26 = i_3 < ((c_2 + 1U) * 8U);

#line 754
            }
            else
            {

#line 754
                _S26 = false;

#line 754
            }

#line 754
            if(_S26)
            {

#line 754
                float2 _S27 = stgGet_0(_S23 + az_0 - _S25 * 1024U, kernelContext_2);
                out_0[d_2] = _S27;

#line 754
            }

#line 749
            d_2 = d_2 + 1U;

#line 749
        }

#line 745
        c_2 = c_2 + 1U;

#line 745
    }

#line 745
    j_2 = 0U;

#line 758
    for(;;)
    {

#line 758
        if(j_2 < 32U)
        {
        }
        else
        {

#line 758
            break;
        }

#line 758
        (*r_3)[j_2] = out_0[j_2];

#line 758
        j_2 = j_2 + 1U;

#line 758
    }
    return;
}


#line 638
void innermost_0(array<float2, int(32)> thread* r_4)
{

    dft32_0(r_4);

#line 650
    return;
}


#line 829
void transform_0(array<float2, int(32)> thread* r_5, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 829
    uint _S28;

#line 829
    uint k2_1;

#line 829
    float cr_0;

#line 829
    float ci_0;

#line 829
    uint _S29;

#line 829
    for(;;)
    {

#line 829
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S28 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(32768U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;

#line 19
                dftR_0(r_5);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 32768.0f);
                float _S30 = tw_0.x;

#line 40
                float _S31 = tw_0.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 32U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_5)[k2_1] = cmul_0((*r_5)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S30 - ci_0 * _S31;
                    float _S32 = cr_0 * _S31 + ci_0 * _S30;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S32;

#line 42
                }

#line 50
                uint per_2 = 32U / max(1024U, 1U);
                uint _S33 = max(32U, 1U);

#line 51
                _S29 = _S33;
                uint blk2_2 = tid_0 / _S33;

#line 52
                uint lane2_2 = tid_0 % _S33;

#line 52
                exchange_0(r_5, lgLn_0, lgTB_0, 1024U, 32768U, blk_2, lane_2, per_2, _S33, 1024U, blk2_2, lane2_2, kernelContext_3);

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

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 31U;

#line 19
                dftR_0(r_5);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 1024.0f);
                float _S34 = tw_1.x;

#line 40
                float _S35 = tw_1.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 32U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_5)[k2_1] = cmul_0((*r_5)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S34 - ci_0 * _S35;
                    float _S36 = cr_0 * _S35 + ci_0 * _S34;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S36;

#line 42
                }

#line 50
                uint per_3 = 32U / _S29;
                uint _S37 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S37;

#line 52
                uint lane2_3 = tid_0 % _S37;

#line 52
                exchange_0(r_5, _S28, lgTB_1, 32U, 1024U, blk_3, lane_3, per_3, _S37, 32U, blk2_3, lane2_3, kernelContext_3);

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
    innermost_0(r_5);

#line 832 "mm_32768_fullCorrelation.slang"
    return;
}


#line 783
uint lgOf_0(uint i_4)
{

#line 783
    uint _S38;

#line 783
    if(i_4 < 2U)
    {

#line 783
        _S38 = 5U;

#line 783
    }
    else
    {

#line 783
        if(i_4 == 2U)
        {

#line 783
            _S38 = 5U;

#line 783
        }
        else
        {

#line 783
            _S38 = 1U;

#line 783
        }

#line 783
    }

#line 783
    return _S38;
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


#line 1731
[[kernel]] void fullCorrelation(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], packed_float2 device* entryPointParams_output_1 [[buffer(3)]])
{

#line 1731
    thread KernelContext_0 kernelContext_4;

#line 1731
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1731
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1731
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1731
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1731
    threadgroup array<uint, int(16384)> stg_1;

#line 1731
    (&kernelContext_4)->stg_0 = &stg_1;



    uint pair_0 = gid_0.x;

#line 1735
    uint tid_1 = lid_0.x;
    uint _S39 = pair_0 / entryPointParams_1->ntmpl_0;

#line 1736
    uint _S40 = pair_0 % entryPointParams_1->ntmpl_0;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(32)> r_6;

#line 1739
    uint i_5 = 0U;
    for(;;)
    {

#line 1740
        if(i_5 < 32U)
        {
        }
        else
        {

#line 1740
            break;
        }

#line 1741
        uint idx_0 = tid_1 + 1024U * i_5;
        r_6[i_5] = cmulConj_0(cload_0((&kernelContext_4)->entryPointParams_data_0, _S39 * 32768U + idx_0), cload_0((&kernelContext_4)->entryPointParams_tmpl_0, _S40 * 32768U + idx_0));

#line 1740
        i_5 = i_5 + 1U;

#line 1740
    }

#line 1740
    transform_0(&r_6, tid_1, &kernelContext_4);

#line 1740
    i_5 = 0U;

#line 1745
    for(;;)
    {

#line 1745
        if(i_5 < 32U)
        {
        }
        else
        {

#line 1745
            break;
        }

#line 1745
        *((&kernelContext_4)->entryPointParams_output_0+(pair_0 * 32768U + slotToIndex_0(tid_1 * 32U + i_5))) = packed_float2(float2(r_6[i_5].x, r_6[i_5].y)) ;

#line 1745
        i_5 = i_5 + 1U;

#line 1745
    }

    return;
}
