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


#line 99 "twiddle.slang"
uint mfRowWindowsFlag_0()
{
    ;
    uint _S2 = ((MF_ROW_WINDOWS));

#line 102
    return _S2;
}


#line 208 "mm_8192_refineListed_lds32.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0, uint device* rowWin_0)
{

#line 104 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 210 "mm_8192_refineListed_lds32.slang"
    if(_S3 == 0U)
    {

#line 210
        return;
    }

#line 211
    uint _S4 = 2U * d_0;

#line 211
    *winStart_0 = rowWin_0[_S4];
    *winEnd_0 = rowWin_0[_S4 + 1U];
    return;
}


#line 72 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S5 = ((MF_DATA_STRIDE));

#line 75
    return _S5;
}


#line 169 "mm_8192_refineListed_lds32.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 169
    return float2(*(b_0+i_0)) ;
}


#line 300
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 300
    float _S6 = a_0.x;

#line 300
    float _S7 = b_1.x;

#line 300
    float _S8 = a_0.y;

#line 300
    float _S9 = b_1.y;

#line 300
    return float2(_S6 * _S7 + _S8 * _S9, _S8 * _S7 - _S6 * _S9);
}


#line 505
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 507
    float2 t1_0 = *a_1 - *c_0;

#line 507
    float2 t2_0 = *b_2 + *d_1;

#line 507
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 509
    *b_2 = t1_0 + j3_0;

#line 509
    *c_0 = t0_0 - t2_0;

#line 509
    *d_1 = t1_0 - j3_0;
    return;
}


#line 299
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 299
    float _S10 = a_2.x;

#line 299
    float _S11 = b_3.x;

#line 299
    float _S12 = a_2.y;

#line 299
    float _S13 = b_3.y;

#line 299
    return float2(_S10 * _S11 - _S12 * _S13, _S10 * _S13 + _S12 * _S11);
}


#line 541
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 548
    uint n1_0 = 0U;
    for(;;)
    {

#line 549
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 549
            break;
        }

#line 549
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 549
        n1_0 = n1_0 + 1U;

#line 549
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 550
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 550
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 551
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 551
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 552
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 552
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 552
    uint k2_0 = 0U;
    for(;;)
    {

#line 553
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 553
            break;
        }

#line 553
        uint _S14 = 4U * k2_0;

#line 553
        r4_0(&(*r_0)[_S14], &(*r_0)[_S14 + 1U], &(*r_0)[_S14 + 2U], &(*r_0)[_S14 + 3U]);

#line 553
        k2_0 = k2_0 + 1U;

#line 553
    }

    float2 t_0 = (*r_0)[int(1)];

#line 555
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 555
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 556
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 556
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 557
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 557
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 558
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 558
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 559
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 559
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 560
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 560
    (*r_0)[int(14)] = t_5;
    return;
}


#line 88 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S15 = ((MF_ACCURATE_TRIG));

#line 91
    return _S15;
}


#line 127
float2 mfTwiddle_0(float angle_0)
{

#line 93
    uint _S16 = mfAccurateTrigFlag_0();

#line 129
    if(_S16 == 0U)
    {

#line 130
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

#line 143
            return float2(- s_0, c_1);
        }
    case int(2):
        {

#line 144
            return float2(- c_1, - s_0);
        }
    case int(3):
        {

#line 145
            return float2(s_0, - c_1);
        }
    default:
        {

#line 146
            return float2(c_1, s_0);
        }
    }

#line 146
}


#line 301 "mm_8192_refineListed_lds32.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S18 = max(TB_0, 1U);

#line 303
    uint j_0 = d_2 / _S18;

#line 303
    uint m_0 = d_2 % _S18;

#line 303
    uint _S19;
    if(TB_0 <= 16U)
    {

#line 304
        _S19 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 304
    }
    else
    {

#line 304
        _S19 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 304
    }

#line 304
    return _S19;
}


#line 8225 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
    uint winStart_1;
    uint winEnd_1;
    uint binsize_0;
    int binShift_0;
    uint nbins_0;
    uint thrBits_0;
    uint gridSize_0;
};


#line 711 "mm_8192_refineListed_lds32.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_survivors_0;
    uint device* entryPointParams_count_0;
    uint device* entryPointParams_rowWin_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 690
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S20 = (1U << lgSpan_0) - 1U;
    uint _S21 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

#line 695
    uint d_3 = 0U;
    for(;;)
    {

#line 696
        if(d_3 < 16U)
        {
        }
        else
        {

#line 696
            break;
        }

#line 697
        uint p_0 = computeWant_0(d_3, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
        uint rem_0 = p_0 & _S21;
        src_0[d_3] = (rem_0 >> lgSpan_0) * 512U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S20);

#line 696
        d_3 = d_3 + 1U;

#line 696
    }

#line 701
    thread array<float, int(16)> xr_0;

#line 708
    bool local_0 = TB_1 <= 32U;

    if((TB_1 << 4U) <= 32U)
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
    uint j_1 = 0U;
    for(;;)
    {

#line 711
        if(j_1 < 16U)
        {
        }
        else
        {

#line 711
            break;
        }

#line 711
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 512U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].x)));

#line 711
        j_1 = j_1 + 1U;

#line 711
    }
    if(local_0)
    {

#line 712
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 712
    }
    else
    {

#line 712
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 712
    }

#line 712
    d_3 = 0U;
    for(;;)
    {

#line 713
        if(d_3 < 16U)
        {
        }
        else
        {

#line 713
            break;
        }

#line 713
        xr_0[d_3] = (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_3]])));

#line 713
        d_3 = d_3 + 1U;

#line 713
    }
    if(local_0)
    {

#line 714
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 714
    }
    else
    {

#line 714
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 714
    }

#line 714
    j_1 = 0U;
    for(;;)
    {

#line 715
        if(j_1 < 16U)
        {
        }
        else
        {

#line 715
            break;
        }

#line 715
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 512U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].y)));

#line 715
        j_1 = j_1 + 1U;

#line 715
    }
    if(local_0)
    {

#line 716
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 716
    }
    else
    {

#line 716
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 716
    }

#line 716
    d_3 = 0U;
    for(;;)
    {

#line 717
        if(d_3 < 16U)
        {
        }
        else
        {

#line 717
            break;
        }

#line 717
        (*r_1)[d_3] = float2(xr_0[d_3], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_3]]))));

#line 717
        d_3 = d_3 + 1U;

#line 717
    }

#line 728
    return;
}


#line 516
void dft2_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    float2 a_3 = (*r_2)[o_0];

#line 518
    float2 b_4 = (*r_2)[o_0 + 1U];

#line 518
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 518
    (*r_2)[o_0 + 1U] = a_3 - b_4;
    return;
}


#line 644
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 644
    uint b_5 = 0U;

#line 654
    for(;;)
    {

#line 654
        if(b_5 < 8U)
        {
        }
        else
        {

#line 654
            break;
        }

#line 654
        dft2_0(r_3, b_5 * 2U);

#line 654
        b_5 = b_5 + 1U;

#line 654
    }

    return;
}


#line 832
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 832
    uint _S22;

#line 832
    uint k2_1;

#line 832
    float cr_0;

#line 832
    float ci_0;

#line 832
    uint _S23;

#line 832
    uint _S24;

#line 832
    uint _S25;

#line 832
    for(;;)
    {

#line 832
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
                exchange_0(r_4, lgLn_0, lgTB_0, 512U, 8192U, blk_2, lane_2, per_2, _S29, 512U, blk2_2, lane2_2, kernelContext_1);

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
                exchange_0(r_4, _S22, lgTB_1, 32U, 512U, blk_3, lane_3, per_3, _S33, 32U, blk2_3, lane2_3, kernelContext_1);

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
                exchange_0(r_4, _S24, lgTB_2, 2U, 32U, blk_4, lane_4, per_4, _S37, 2U, blk2_4, lane2_4, kernelContext_1);

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

#line 835 "mm_8192_refineListed_lds32.slang"
    return;
}


#line 789
uint lgOf_0(uint i_1)
{

#line 789
    uint _S38;

#line 789
    if(i_1 < 3U)
    {

#line 789
        _S38 = 4U;

#line 789
    }
    else
    {

#line 789
        _S38 = 1U;

#line 789
    }

#line 789
    return _S38;
}


#line 791
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_1 = slot_0 >> lg_0;

#line 795
    uint lg_1 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_1;

#line 795
    uint lg_2 = lgOf_0(1U);

#line 795
    uint lg_3 = lgOf_0(0U);

#line 800
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | (x_2 & ((1U << lg_2) - 1U))) << lg_3) | ((x_2 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 849
void filterPairOut_0(uint pair_0, uint opair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_2)
{


    uint b_6;

#line 875
    kernelContext_2->_tid_0 = tid_1;
    uint _S39 = pair_0 / ntmpl_1;

#line 876
    uint _S40 = pair_0 % ntmpl_1;

#line 881
    thread array<float2, int(16)> r_5;

#line 881
    uint n2_0 = 0U;

#line 892
    for(;;)
    {

#line 892
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 892
            break;
        }

#line 893
        uint idx_0 = tid_1 + 512U * n2_0;

#line 77 "twiddle.slang"
        uint _S41 = mfDataStrideFlag_0();

#line 172 "mm_8192_refineListed_lds32.slang"
        if(_S41 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S42 = mfDataStrideFlag_0();

#line 77
            b_6 = _S42;

#line 172 "mm_8192_refineListed_lds32.slang"
        }
        else
        {

#line 172
            b_6 = 8192U;

#line 172
        }

#line 894
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S39 * b_6 + idx_0), cload_0(tmpl_0, _S40 * 8192U + idx_0));

#line 892
        n2_0 = n2_0 + 1U;

#line 892
    }

#line 892
    transform_0(&r_5, tid_1, kernelContext_2);

#line 921
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 921
    b_6 = tid_1;

#line 1033
    for(;;)
    {

#line 1033
        if(b_6 < nbins_1)
        {
        }
        else
        {

#line 1033
            break;
        }

#line 1033
        (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + b_6] = thrBits_1;

#line 1033
        b_6 = b_6 + 512U;

#line 1033
    }
    bool _S43 = nbins_1 == 1U;

#line 1034
    bool live_0;

#line 1034
    if(_S43)
    {

#line 1034
        live_0 = tid_1 == 0U;

#line 1034
    }
    else
    {

#line 1034
        live_0 = false;

#line 1034
    }

#line 1034
    if(live_0)
    {

#line 1034
        (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U] = 4294967295U;

#line 1034
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1093
    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 1094
    uint i_2 = 0U;



    for(;;)
    {

#line 1098
        if(i_2 < 16U)
        {
        }
        else
        {

#line 1098
            break;
        }

#line 1099
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_2);
        if(idx_1 >= winStart_2)
        {

#line 1100
            live_0 = idx_1 < winEnd_2;

#line 1100
        }
        else
        {

#line 1100
            live_0 = false;

#line 1100
        }



        float _rx_0 = r_5[i_2].x;

#line 1104
        float _ry_0 = r_5[i_2].y;
        if(live_0)
        {

#line 1105
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1105
        }
        else
        {

#line 1105
            n2_0 = 0U;

#line 1105
        }

#line 1105
        myMag_0[i_2] = n2_0;

#line 1113
        uint off_0 = idx_1 - winStart_2;

#line 1120
        if(live_0)
        {

#line 1120
            if(binShift_1 >= int(0))
            {

#line 1120
                b_6 = off_0 >> uint(binShift_1);

#line 1120
            }
            else
            {

#line 1120
                uint _S44 = off_0 / binsize_1;

#line 1120
                b_6 = _S44;

#line 1120
            }

#line 1120
        }
        else
        {

#line 1120
            b_6 = 0U;

#line 1120
        }

#line 1120
        myBin_0[i_2] = b_6;

#line 1120
        bool _S45;



        if(nbins_1 > 1U)
        {

#line 1124
            _S45 = (myMag_0[i_2]) > thrBits_1;

#line 1124
        }
        else
        {

#line 1124
            _S45 = false;

#line 1124
        }

#line 1124
        if(_S45)
        {

#line 1125
            uint _S46 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + myBin_0[i_2]])), myMag_0[i_2], memory_order_relaxed);

#line 1124
        }

#line 1098
        i_2 = i_2 + 1U;

#line 1098
    }

#line 1098
    uint winner_0;

#line 1148
    if(_S43)
    {

#line 1148
        winner_0 = thrBits_1;

#line 1148
        i_2 = 0U;


        for(;;)
        {

#line 1151
            if(i_2 < 16U)
            {
            }
            else
            {

#line 1151
                break;
            }

#line 1151
            uint _S47 = max(winner_0, myMag_0[i_2]);

#line 1151
            uint i_3 = i_2 + 1U;

#line 1151
            winner_0 = _S47;

#line 1151
            i_2 = i_3;

#line 1151
        }

        uint wm_0 = simd_max(winner_0);
        bool _S48 = simd_is_first();

#line 1154
        if(_S48)
        {

#line 1154
            live_0 = wm_0 > thrBits_1;

#line 1154
        }
        else
        {

#line 1154
            live_0 = false;

#line 1154
        }

#line 1154
        if(live_0)
        {

#line 1154
            uint _S49 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1154
        }

#line 1148
    }

#line 1169
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1176
    if(_S43)
    {

#line 1176
        winner_0 = 4294967295U;

#line 1176
        i_2 = 0U;


        for(;;)
        {

#line 1179
            if(i_2 < 16U)
            {
            }
            else
            {

#line 1179
                break;
            }

#line 1180
            if((myMag_0[i_2]) > thrBits_1)
            {

#line 1180
                live_0 = (myMag_0[i_2]) == (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0];

#line 1180
            }
            else
            {

#line 1180
                live_0 = false;

#line 1180
            }

#line 1180
            if(live_0)
            {

#line 1180
                winner_0 = min(winner_0, tid_1 * 16U + i_2);

#line 1180
            }

#line 1179
            i_2 = i_2 + 1U;

#line 1179
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S50 = simd_is_first();

#line 1184
        if(_S50)
        {

#line 1184
            live_0 = waveWinner_0 != 4294967295U;

#line 1184
        }
        else
        {

#line 1184
            live_0 = false;

#line 1184
        }

#line 1184
        if(live_0)
        {

#line 1185
            uint _S51 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1184
        }

#line 1189
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1189
        i_2 = 0U;
        for(;;)
        {

#line 1190
            if(i_2 < 16U)
            {
            }
            else
            {

#line 1190
                break;
            }

#line 1191
            uint _S52 = tid_1 * 16U + i_2;

#line 1191
            if(_S52 == (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U])
            {

#line 1192
                *(peakIdx_0+opair_0) = int(slotToIndex_0(_S52));

#line 1192
                *(peakVal_0+opair_0) = packed_float2(float2(r_5[i_2].x, r_5[i_2].y)) ;

#line 1191
            }

#line 1190
            i_2 = i_2 + 1U;

#line 1190
        }

#line 1200
        if(tid_1 == 0U)
        {

#line 1200
            live_0 = ((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U]) == 4294967295U;

#line 1200
        }
        else
        {

#line 1200
            live_0 = false;

#line 1200
        }

#line 1200
        if(live_0)
        {

#line 1201
            *(peakIdx_0+opair_0) = int(-1);

#line 1201
            *(peakVal_0+opair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1200
        }

#line 1176
    }
    else
    {

#line 1176
        i_2 = 0U;

#line 1209
        for(;;)
        {

#line 1209
            if(i_2 < 16U)
            {
            }
            else
            {

#line 1209
                break;
            }

#line 1210
            if((myMag_0[i_2]) > thrBits_1)
            {

#line 1210
                live_0 = (myMag_0[i_2]) == (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + myBin_0[i_2]];

#line 1210
            }
            else
            {

#line 1210
                live_0 = false;

#line 1210
            }

#line 1210
            myMag_0[i_2] = uint(live_0);

#line 1209
            i_2 = i_2 + 1U;

#line 1209
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1212
        b_6 = tid_1;
        for(;;)
        {

#line 1213
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 1213
                break;
            }

#line 1213
            (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + b_6] = 4294967295U;

#line 1213
            b_6 = b_6 + 512U;

#line 1213
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1214
        i_2 = 0U;
        for(;;)
        {

#line 1215
            if(i_2 < 16U)
            {
            }
            else
            {

#line 1215
                break;
            }

#line 1216
            if((myMag_0[i_2]) != 0U)
            {

#line 1216
                uint _S53 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + myBin_0[i_2]])), tid_1 * 16U + i_2, memory_order_relaxed);

#line 1216
            }

#line 1215
            i_2 = i_2 + 1U;

#line 1215
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1217
        i_2 = 0U;
        for(;;)
        {

#line 1218
            if(i_2 < 16U)
            {
            }
            else
            {

#line 1218
                break;
            }

#line 1219
            if((myMag_0[i_2]) != 0U)
            {

#line 1219
                live_0 = ((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + myBin_0[i_2]]) == (tid_1 * 16U + i_2);

#line 1219
            }
            else
            {

#line 1219
                live_0 = false;

#line 1219
            }

#line 1219
            if(live_0)
            {

#line 1220
                uint o_1 = opair_0 * nbins_1 + myBin_0[i_2];
                *(peakIdx_0+o_1) = int(slotToIndex_0(tid_1 * 16U + i_2));

#line 1221
                *(peakVal_0+o_1) = packed_float2(float2(r_5[i_2].x, r_5[i_2].y)) ;

#line 1219
            }

#line 1218
            i_2 = i_2 + 1U;

#line 1218
        }

#line 1218
        b_6 = tid_1;

#line 1225
        for(;;)
        {

#line 1225
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 1225
                break;
            }

#line 1226
            if(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + b_6]) == 4294967295U)
            {

#line 1227
                uint _S54 = opair_0 * nbins_1 + b_6;

#line 1227
                *(peakIdx_0+_S54) = int(-1);

#line 1227
                *(peakVal_0+_S54) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1226
            }

#line 1225
            b_6 = b_6 + 512U;

#line 1225
        }

#line 1176
    }

#line 1235
    return;
}

void filterPair_0(uint pair_1, uint tid_2, packed_float2 device* data_1, packed_float2 device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_2, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_3)
{


    filterPairOut_0(pair_1, pair_1, tid_2, data_1, tmpl_1, peakIdx_1, peakVal_1, ntmpl_2, winStart_3, winEnd_3, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_3);



    return;
}


#line 2142
[[kernel]] void refineListedBounded(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]], uint device* entryPointParams_rowWin_1 [[buffer(7)]])
{

#line 2142
    thread KernelContext_0 kernelContext_4;

#line 2142
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 2142
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2142
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2142
    (&kernelContext_4)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2142
    (&kernelContext_4)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2142
    (&kernelContext_4)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2142
    (&kernelContext_4)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2142
    (&kernelContext_4)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 2142
    threadgroup array<uint, int(8192)> stg_1;

#line 2142
    (&kernelContext_4)->stg_0 = &stg_1;

#line 2152
    uint _S55 = entryPointParams_count_1[int(0)];

#line 2152
    uint i_4 = gid_0.x;
    for(;;)
    {

#line 2153
        if(i_4 < _S55)
        {
        }
        else
        {

#line 2153
            break;
        }

#line 2154
        (&kernelContext_4)->_stgBase_0 = 0U;
        uint pair_2 = (&kernelContext_4)->entryPointParams_survivors_0[i_4];

#line 2155
        thread uint ws_0 = (&kernelContext_4)->entryPointParams_0->winStart_1;

#line 2155
        thread uint we_0 = (&kernelContext_4)->entryPointParams_0->winEnd_1;
        uint _S56 = pair_2 / (&kernelContext_4)->entryPointParams_0->ntmpl_0;

#line 2156
        rowWindow_0(_S56, &ws_0, &we_0, (&kernelContext_4)->entryPointParams_rowWin_0);

#line 2156
        filterPair_0(pair_2, lid_0.x, (&kernelContext_4)->entryPointParams_data_0, (&kernelContext_4)->entryPointParams_tmpl_0, (&kernelContext_4)->entryPointParams_peakIdx_0, (&kernelContext_4)->entryPointParams_peakVal_0, (&kernelContext_4)->entryPointParams_0->ntmpl_0, ws_0, we_0, (&kernelContext_4)->entryPointParams_0->binsize_0, (&kernelContext_4)->entryPointParams_0->binShift_0, (&kernelContext_4)->entryPointParams_0->nbins_0, (&kernelContext_4)->entryPointParams_0->thrBits_0, &kernelContext_4);


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2153
        i_4 = i_4 + (&kernelContext_4)->entryPointParams_0->gridSize_0;

#line 2153
    }

#line 2161
    return;
}
