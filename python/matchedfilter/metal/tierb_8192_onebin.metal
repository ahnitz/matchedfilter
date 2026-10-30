#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
#ifndef MF_ROW_WINDOWS
#define MF_ROW_WINDOWS 0u
#endif
#ifndef MF_DATA_STRIDE
#define MF_DATA_STRIDE 0u
#endif
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


#line 85 "twiddle.slang"
uint mfRowWindowsFlag_0()
{
    ;
    uint _S2 = ((MF_ROW_WINDOWS));

#line 88
    return _S2;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint ntmpl_0;
    uint winStart_0;
    uint winEnd_0;
    uint binsize_0;
    int binShift_0;
    uint nbins_0;
    uint thrBits_0;
};


#line 705 "mm_8192_fusedTierB_onebin.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_rowWin_0;
    uint _stgBase_0;
    uint _binPhase_0;
    uint _tid_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 227
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 90 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 230 "mm_8192_fusedTierB_onebin.slang"
    if(_S3 == 0U)
    {

#line 230
        return;
    }

#line 231
    uint _S4 = 3U * d_0;

#line 231
    *winStart_1 = rowWin_0[_S4];
    *winEnd_1 = rowWin_0[_S4 + 1U];
    kernelContext_0->_binPhase_0 = rowWin_0[_S4 + 2U];
    return;
}


#line 58 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S5 = ((MF_DATA_STRIDE));

#line 61
    return _S5;
}


#line 173 "mm_8192_fusedTierB_onebin.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 173
    return float2(*(b_0+i_0)) ;
}


#line 323
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 323
    float _S6 = a_0.x;

#line 323
    float _S7 = b_1.x;

#line 323
    float _S8 = a_0.y;

#line 323
    float _S9 = b_1.y;

#line 323
    return float2(_S6 * _S7 + _S8 * _S9, _S8 * _S7 - _S6 * _S9);
}


#line 499
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 501
    float2 t1_0 = *a_1 - *c_0;

#line 501
    float2 t2_0 = *b_2 + *d_1;

#line 501
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 503
    *b_2 = t1_0 + j3_0;

#line 503
    *c_0 = t0_0 - t2_0;

#line 503
    *d_1 = t1_0 - j3_0;
    return;
}


#line 322
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 322
    float _S10 = a_2.x;

#line 322
    float _S11 = b_3.x;

#line 322
    float _S12 = a_2.y;

#line 322
    float _S13 = b_3.y;

#line 322
    return float2(_S10 * _S11 - _S12 * _S13, _S10 * _S13 + _S12 * _S11);
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
        uint _S14 = 4U * k2_0;

#line 547
        r4_0(&(*r_0)[_S14], &(*r_0)[_S14 + 1U], &(*r_0)[_S14 + 2U], &(*r_0)[_S14 + 3U]);

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
    uint _S15 = ((MF_ACCURATE_TRIG));

#line 77
    return _S15;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S16 = mfAccurateTrigFlag_0();

#line 103
    if(_S16 == 0U)
    {

#line 104
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S17 = float(quadrant_0);
    float x_0 = angle_0 - _S17 * 1.57079625129699707f - _S17 * 7.54978941586159635e-08f;
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


#line 324 "mm_8192_fusedTierB_onebin.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S18 = max(TB_0, 1U);

#line 326
    uint j_0 = d_2 / _S18;

#line 326
    uint m_0 = d_2 % _S18;

#line 326
    uint _S19;
    if(TB_0 <= 16U)
    {

#line 327
        _S19 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 327
    }
    else
    {

#line 327
        _S19 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 327
    }

#line 327
    return _S19;
}


#line 684
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_1)
{

    uint _S20 = (1U << lgSpan_0) - 1U;
    uint _S21 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

#line 689
    uint d_3 = 0U;
    for(;;)
    {

#line 690
        if(d_3 < 16U)
        {
        }
        else
        {

#line 690
            break;
        }

#line 691
        uint p_0 = computeWant_0(d_3, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
        uint rem_0 = p_0 & _S21;
        src_0[d_3] = (rem_0 >> lgSpan_0) * 512U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S20);

#line 690
        d_3 = d_3 + 1U;

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
        (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + j_1 * 512U + kernelContext_1->_tid_0] = (as_type<uint>(((*r_1)[j_1].x)));

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
    d_3 = 0U;
    for(;;)
    {

#line 707
        if(d_3 < 16U)
        {
        }
        else
        {

#line 707
            break;
        }

#line 707
        xr_0[d_3] = (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + src_0[d_3]])));

#line 707
        d_3 = d_3 + 1U;

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
        (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + j_1 * 512U + kernelContext_1->_tid_0] = (as_type<uint>(((*r_1)[j_1].y)));

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
    d_3 = 0U;
    for(;;)
    {

#line 711
        if(d_3 < 16U)
        {
        }
        else
        {

#line 711
            break;
        }

#line 711
        (*r_1)[d_3] = float2(xr_0[d_3], (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + src_0[d_3]]))));

#line 711
        d_3 = d_3 + 1U;

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


#line 826
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_2)
{

#line 826
    uint _S22;

#line 826
    uint k2_1;

#line 826
    float cr_0;

#line 826
    float ci_0;

#line 826
    uint _S23;

#line 826
    uint _S24;

#line 826
    uint _S25;

#line 826
    for(;;)
    {

#line 826
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(512U);

#line 11
                _S22 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(8192U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 511U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 8192.0f);
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
                uint per_2 = 16U / max(512U, 1U);
                uint _S29 = max(32U, 1U);

#line 51
                _S23 = _S29;
                uint blk2_2 = tid_0 / _S29;

#line 52
                uint lane2_2 = tid_0 % _S29;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 512U, 8192U, blk_2, lane_2, per_2, _S29, 512U, blk2_2, lane2_2, kernelContext_2);

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
                _S24 = lgTB_1;

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 31U;


                dft16_0(r_4);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 512.0f);
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
                uint per_3 = 16U / _S23;
                uint _S33 = max(2U, 1U);

#line 51
                _S25 = _S33;
                uint blk2_3 = tid_0 / _S33;

#line 52
                uint lane2_3 = tid_0 % _S33;

#line 52
                exchange_0(r_4, _S22, lgTB_1, 32U, 512U, blk_3, lane_3, per_3, _S33, 32U, blk2_3, lane2_3, kernelContext_2);

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
                float _S34 = tw_2.x;

#line 40
                float _S35 = tw_2.y;

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
                    float nr_2 = cr_0 * _S34 - ci_0 * _S35;
                    float _S36 = cr_0 * _S35 + ci_0 * _S34;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_2;

#line 42
                    ci_0 = _S36;

#line 42
                }

#line 50
                uint per_4 = 16U / _S25;
                uint _S37 = max(0U, 1U);
                uint blk2_4 = tid_0 / _S37;

#line 52
                uint lane2_4 = tid_0 % _S37;

#line 52
                exchange_0(r_4, _S24, lgTB_2, 2U, 32U, blk_4, lane_4, per_4, _S37, 2U, blk2_4, lane2_4, kernelContext_2);

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

#line 829 "mm_8192_fusedTierB_onebin.slang"
    return;
}


#line 783
uint lgOf_0(uint i_1)
{

#line 783
    uint _S38;

#line 783
    if(i_1 < 3U)
    {

#line 783
        _S38 = 4U;

#line 783
    }
    else
    {

#line 783
        _S38 = 1U;

#line 783
    }

#line 783
    return _S38;
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


#line 849
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_3)
{


    uint threadBestBits_0;

#line 870
    kernelContext_3->_tid_0 = tid_1;
    uint _S39 = pair_0 / ntmpl_1;

#line 871
    uint _S40 = pair_0 % ntmpl_1;

#line 876
    thread array<float2, int(16)> r_5;

#line 876
    uint n2_0 = 0U;

#line 887
    for(;;)
    {

#line 887
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 887
            break;
        }

#line 888
        uint idx_0 = tid_1 + 512U * n2_0;

#line 63 "twiddle.slang"
        uint _S41 = mfDataStrideFlag_0();

#line 176 "mm_8192_fusedTierB_onebin.slang"
        if(_S41 != 0U)
        {

#line 63 "twiddle.slang"
            uint _S42 = mfDataStrideFlag_0();

#line 63
            threadBestBits_0 = _S42;

#line 176 "mm_8192_fusedTierB_onebin.slang"
        }
        else
        {

#line 176
            threadBestBits_0 = 8192U;

#line 176
        }

#line 889
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S39 * threadBestBits_0 + idx_0), cload_0(tmpl_0, _S40 * 8192U + idx_0));

#line 887
        n2_0 = n2_0 + 1U;

#line 887
    }

#line 887
    transform_0(&r_5, tid_1, kernelContext_3);

#line 906
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 949
    bool _S43 = tid_1 == 0U;

#line 949
    if(_S43)
    {

#line 949
        (*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0] = thrBits_1;

#line 949
        (*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0 + 1U] = 4294967295U;

#line 949
    }



    float2 _S44 = float2(0.0f, 0.0f);

#line 953
    bool live_0;

    if(winStart_2 == 0U)
    {

#line 955
        live_0 = winEnd_2 >= 8192U;

#line 955
    }
    else
    {

#line 955
        live_0 = false;

#line 955
    }

#line 955
    uint threadBestSlot_0;

#line 955
    uint winner_0;

#line 955
    float2 threadBestVal_0;

#line 955
    if(live_0)
    {

#line 955
        threadBestBits_0 = thrBits_1;

#line 955
        threadBestSlot_0 = 4294967295U;

#line 955
        threadBestVal_0 = _S44;

#line 955
        winner_0 = 0U;
        for(;;)
        {

#line 956
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 956
                break;
            }

#line 957
            float _rx_0 = r_5[winner_0].x;

#line 957
            float _ry_0 = r_5[winner_0].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > threadBestBits_0)
            {
                uint _S45 = tid_1 * 16U + winner_0;
                float2 _S46 = float2(_rx_0, _ry_0);

#line 962
                threadBestBits_0 = magBits_0;

#line 962
                threadBestSlot_0 = _S45;

#line 962
                threadBestVal_0 = _S46;

#line 959
            }

#line 956
            winner_0 = winner_0 + 1U;

#line 956
        }

#line 955
    }
    else
    {

#line 955
        threadBestBits_0 = thrBits_1;

#line 955
        threadBestSlot_0 = 4294967295U;

#line 955
        threadBestVal_0 = _S44;

#line 955
        winner_0 = 0U;

#line 966
        for(;;)
        {

#line 966
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 966
                break;
            }

#line 967
            uint _S47 = tid_1 * 16U + winner_0;

#line 967
            uint idx_1 = slotToIndex_0(_S47);
            if(idx_1 >= winStart_2)
            {

#line 968
                live_0 = idx_1 < winEnd_2;

#line 968
            }
            else
            {

#line 968
                live_0 = false;

#line 968
            }
            float _rx_1 = r_5[winner_0].x;

#line 969
            float _ry_1 = r_5[winner_0].y;

#line 969
            uint magBits_1;
            if(live_0)
            {

#line 970
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 970
            }
            else
            {

#line 970
                magBits_1 = 0U;

#line 970
            }
            if(magBits_1 > threadBestBits_0)
            {

                float2 _S48 = float2(_rx_1, _ry_1);

#line 974
                threadBestBits_0 = magBits_1;

#line 974
                threadBestSlot_0 = _S47;

#line 974
                threadBestVal_0 = _S48;

#line 971
            }

#line 966
            winner_0 = winner_0 + 1U;

#line 966
        }

#line 955
    }

#line 979
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(threadBestBits_0);
    bool _S49 = simd_is_first();

#line 983
    if(_S49)
    {

#line 983
        live_0 = wm_0 > thrBits_1;

#line 983
    }
    else
    {

#line 983
        live_0 = false;

#line 983
    }

#line 983
    if(live_0)
    {

#line 983
        uint _S50 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0])), wm_0, memory_order_relaxed);

#line 983
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(threadBestBits_0 > thrBits_1)
    {

#line 990
        live_0 = threadBestBits_0 == (*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0];

#line 990
    }
    else
    {

#line 990
        live_0 = false;

#line 990
    }

#line 990
    if(live_0)
    {

#line 990
        winner_0 = threadBestSlot_0;

#line 990
    }
    else
    {

#line 990
        winner_0 = 4294967295U;

#line 990
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S51 = simd_is_first();

#line 995
    if(_S51)
    {

#line 995
        live_0 = waveWinner_0 != 4294967295U;

#line 995
    }
    else
    {

#line 995
        live_0 = false;

#line 995
    }

#line 995
    if(live_0)
    {

#line 996
        uint _S52 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 995
    }

#line 1000
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(threadBestSlot_0 == (*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0 + 1U])
    {

#line 1002
        live_0 = threadBestSlot_0 != 4294967295U;

#line 1002
    }
    else
    {

#line 1002
        live_0 = false;

#line 1002
    }

#line 1002
    if(live_0)
    {

#line 1003
        *(peakIdx_0+pair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 1003
        *(peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 1002
    }



    if(_S43)
    {

#line 1006
        live_0 = ((*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0 + 1U]) == 4294967295U;

#line 1006
    }
    else
    {

#line 1006
        live_0 = false;

#line 1006
    }

#line 1006
    if(live_0)
    {

#line 1007
        *(peakIdx_0+pair_0) = int(-1);

#line 1007
        *(peakVal_0+pair_0) = packed_float2(_S44) ;

#line 1006
    }

#line 1216
    return;
}


#line 1672
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1672
    thread KernelContext_0 kernelContext_4;

#line 1672
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1672
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1672
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1672
    (&kernelContext_4)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1672
    (&kernelContext_4)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1672
    (&kernelContext_4)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1672
    threadgroup array<uint, int(8192)> stg_1;

#line 1672
    (&kernelContext_4)->stg_0 = &stg_1;

#line 1672
    (&kernelContext_4)->_binPhase_0 = 0U;

#line 1689
    uint _pr_0 = gid_0.x;

#line 1689
    uint _t_0 = lid_0.x;
    (&kernelContext_4)->_stgBase_0 = 0U;

#line 1699
    thread uint _ws_0 = entryPointParams_1->winStart_0;

#line 1699
    thread uint _we_0 = entryPointParams_1->winEnd_0;
    uint _S53 = _pr_0 / entryPointParams_1->ntmpl_0;

#line 1700
    rowWindow_0(_S53, &_ws_0, &_we_0, (&kernelContext_4)->entryPointParams_rowWin_0, &kernelContext_4);

#line 1700
    filterPair_0(_pr_0, _t_0, (&kernelContext_4)->entryPointParams_data_0, (&kernelContext_4)->entryPointParams_tmpl_0, (&kernelContext_4)->entryPointParams_peakIdx_0, (&kernelContext_4)->entryPointParams_peakVal_0, entryPointParams_1->ntmpl_0, _ws_0, _we_0, (&kernelContext_4)->entryPointParams_0->binsize_0, (&kernelContext_4)->entryPointParams_0->binShift_0, (&kernelContext_4)->entryPointParams_0->nbins_0, (&kernelContext_4)->entryPointParams_0->thrBits_0, &kernelContext_4);

#line 1707
    return;
}
