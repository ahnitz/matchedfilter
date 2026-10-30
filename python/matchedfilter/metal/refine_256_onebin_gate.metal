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
    uint gridSize_0;
};


#line 313 "mm_256_refineListed_onebin_gate.slang"
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
    uint _binPhase_0;
    uint _tid_0;
    array<uint, int(512)> threadgroup* stg_0;
};


#line 229
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 90 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 232 "mm_256_refineListed_onebin_gate.slang"
    if(_S3 == 0U)
    {

#line 232
        return;
    }

#line 233
    uint _S4 = 3U * d_0;

#line 233
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


#line 175 "mm_256_refineListed_onebin_gate.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 175
    return float2(*(b_0+i_0)) ;
}


#line 325
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 325
    float _S6 = a_0.x;

#line 325
    float _S7 = b_1.x;

#line 325
    float _S8 = a_0.y;

#line 325
    float _S9 = b_1.y;

#line 325
    return float2(_S6 * _S7 + _S8 * _S9, _S8 * _S7 - _S6 * _S9);
}


#line 501
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 503
    float2 t1_0 = *a_1 - *c_0;

#line 503
    float2 t2_0 = *b_2 + *d_1;

#line 503
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 505
    *b_2 = t1_0 + j3_0;

#line 505
    *c_0 = t0_0 - t2_0;

#line 505
    *d_1 = t1_0 - j3_0;
    return;
}


#line 324
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 324
    float _S10 = a_2.x;

#line 324
    float _S11 = b_3.x;

#line 324
    float _S12 = a_2.y;

#line 324
    float _S13 = b_3.y;

#line 324
    return float2(_S10 * _S11 - _S12 * _S13, _S10 * _S13 + _S12 * _S11);
}


#line 537
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 544
    uint n1_0 = 0U;
    for(;;)
    {

#line 545
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 545
            break;
        }

#line 545
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 545
        n1_0 = n1_0 + 1U;

#line 545
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 546
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 546
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 547
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 547
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 548
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 548
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 548
    uint k2_0 = 0U;
    for(;;)
    {

#line 549
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 549
            break;
        }

#line 549
        uint _S14 = 4U * k2_0;

#line 549
        r4_0(&(*r_0)[_S14], &(*r_0)[_S14 + 1U], &(*r_0)[_S14 + 2U], &(*r_0)[_S14 + 3U]);

#line 549
        k2_0 = k2_0 + 1U;

#line 549
    }

    float2 t_0 = (*r_0)[int(1)];

#line 551
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 551
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 552
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 552
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 553
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 553
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 554
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 554
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 555
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 555
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 556
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 556
    (*r_0)[int(14)] = t_5;
    return;
}


#line 537
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_1 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_1 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_1 = float2(0.0f, 1.0f);
    float2 W6_1 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_1 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 544
    uint n1_1 = 0U;
    for(;;)
    {

#line 545
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 545
            break;
        }

#line 545
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 545
        n1_1 = n1_1 + 1U;

#line 545
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 546
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 546
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 547
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 547
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 548
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 548
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 548
    uint k2_1 = 0U;
    for(;;)
    {

#line 549
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 549
            break;
        }

#line 549
        uint _S15 = 4U * k2_1;

#line 549
        r4_0(&(*r_1)[_S15], &(*r_1)[_S15 + 1U], &(*r_1)[_S15 + 2U], &(*r_1)[_S15 + 3U]);

#line 549
        k2_1 = k2_1 + 1U;

#line 549
    }

    float2 t_6 = (*r_1)[int(1)];

#line 551
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 551
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 552
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 552
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 553
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 553
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 554
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 554
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 555
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 555
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 556
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 556
    (*r_1)[int(14)] = t_11;
    return;
}


#line 74 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S16 = ((MF_ACCURATE_TRIG));

#line 77
    return _S16;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S17 = mfAccurateTrigFlag_0();

#line 103
    if(_S17 == 0U)
    {

#line 104
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S18 = float(quadrant_0);
    float x_0 = angle_0 - _S18 * 1.57079625129699707f - _S18 * 7.54978941586159635e-08f;
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


#line 326 "mm_256_refineListed_onebin_gate.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S19 = max(TB_0, 1U);

#line 328
    uint j_0 = d_2 / _S19;

#line 328
    uint m_0 = d_2 % _S19;

#line 328
    uint _S20;
    if(TB_0 <= 16U)
    {

#line 329
        _S20 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 329
    }
    else
    {

#line 329
        _S20 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 329
    }

#line 329
    return _S20;
}


#line 313
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 313
    uint _S21 = 2U * i_1;

#line 313
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S21] = (as_type<uint>((v_0.x)));

#line 313
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S21 + 1U] = (as_type<uint>((v_0.y)));

#line 313
    return;
}


#line 314
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_2)
{

#line 314
    uint _S22 = 2U * i_2;

#line 314
    return float2((as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S22]))), (as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S22 + 1U]))));
}


#line 726
void exchange_0(array<float2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_3)
{

#line 727
    uint j_1;

#line 738
    thread array<float2, int(16)> out_0;

#line 738
    uint z_1 = 0U;
    for(;;)
    {

#line 739
        if(z_1 < 16U)
        {
        }
        else
        {

#line 739
            break;
        }

#line 739
        out_0[z_1] = float2(0.0f, 0.0f);

#line 739
        z_1 = z_1 + 1U;

#line 739
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S23 = p0_0 & lenMask_0;

#line 745
    uint _S24 = (_S23 >> lgSpan_0) * 16U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S23 & spanMask_0);

#line 745
    uint c_2 = 0U;

    for(;;)
    {

#line 747
        if(c_2 < 1U)
        {
        }
        else
        {

#line 747
            break;
        }

#line 748
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 748
        j_1 = 0U;
        for(;;)
        {

#line 749
            if(j_1 < 16U)
            {
            }
            else
            {

#line 749
                break;
            }

#line 749
            stgPut_0(j_1 * 16U + kernelContext_3->_tid_0, (*r_2)[c_2 * 16U + j_1], kernelContext_3);

#line 749
            j_1 = j_1 + 1U;

#line 749
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 750
        uint d_3 = 0U;
        for(;;)
        {

#line 751
            if(d_3 < 16U)
            {
            }
            else
            {

#line 751
                break;
            }

#line 752
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S25 = pz_0 & lenMask_0;
            uint az_0 = (_S25 >> lgSpan_0) * 16U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S25 & spanMask_0);

#line 754
            float2 _S26 = stgGet_0(_S24 + az_0 - c_2 * 16U * 16U, kernelContext_3);


            out_0[d_3] = _S26;

#line 751
            d_3 = d_3 + 1U;

#line 751
        }

#line 747
        c_2 = c_2 + 1U;

#line 747
    }

#line 747
    j_1 = 0U;

#line 760
    for(;;)
    {

#line 760
        if(j_1 < 16U)
        {
        }
        else
        {

#line 760
            break;
        }

#line 760
        (*r_2)[j_1] = out_0[j_1];

#line 760
        j_1 = j_1 + 1U;

#line 760
    }
    return;
}


#line 640
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 647
    dft16_1(r_3);

#line 652
    return;
}


#line 828
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_4)
{

#line 828
    for(;;)
    {

#line 828
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(16U);
                uint lgLn_0 = firstbithigh_0(256U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 15U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 256.0f);
                float _S27 = tw_0.x;

#line 40
                float _S28 = tw_0.y;

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
                    float nr_0 = cr_0 * _S27 - ci_0 * _S28;
                    float _S29 = cr_0 * _S28 + ci_0 * _S27;

#line 42
                    k2_2 = k2_2 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S29;

#line 42
                }

#line 50
                uint per_2 = 16U / max(16U, 1U);
                uint _S30 = max(1U, 1U);
                uint blk2_2 = tid_0 / _S30;

#line 52
                uint lane2_2 = tid_0 % _S30;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 16U, 256U, blk_2, lane_2, per_2, _S30, 16U, blk2_2, lane2_2, kernelContext_4);

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

#line 831 "mm_256_refineListed_onebin_gate.slang"
    return;
}


#line 785
uint lgOf_0(uint i_3)
{

#line 785
    uint _S31;

#line 785
    if(i_3 < 1U)
    {

#line 785
        _S31 = 4U;

#line 785
    }
    else
    {

#line 785
        if(i_3 == 1U)
        {

#line 785
            _S31 = 4U;

#line 785
        }
        else
        {

#line 785
            _S31 = 1U;

#line 785
        }

#line 785
    }

#line 785
    return _S31;
}


#line 787
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 791
    uint lg_1 = lgOf_0(0U);

#line 796
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 845
void filterPairOut_0(uint pair_0, uint opair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{


    uint m_1;

#line 865
    bool gateOnly_0 = nbins_1 == 0U;

#line 872
    kernelContext_5->_tid_0 = tid_1;
    uint _S32 = pair_0 / ntmpl_1;

#line 873
    uint _S33 = pair_0 % ntmpl_1;

#line 878
    thread array<float2, int(16)> r_5;

#line 878
    uint n2_0 = 0U;

#line 889
    for(;;)
    {

#line 889
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 889
            break;
        }

#line 890
        uint idx_0 = tid_1 + 16U * n2_0;

#line 63 "twiddle.slang"
        uint _S34 = mfDataStrideFlag_0();

#line 178 "mm_256_refineListed_onebin_gate.slang"
        if(_S34 != 0U)
        {

#line 63 "twiddle.slang"
            uint _S35 = mfDataStrideFlag_0();

#line 63
            m_1 = _S35;

#line 178 "mm_256_refineListed_onebin_gate.slang"
        }
        else
        {

#line 178
            m_1 = 256U;

#line 178
        }

#line 891
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S32 * m_1 + idx_0), cload_0(tmpl_0, _S33 * 256U + idx_0));

#line 889
        n2_0 = n2_0 + 1U;

#line 889
    }

#line 889
    transform_0(&r_5, tid_1, kernelContext_5);

#line 908
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 908
    uint i_4;

#line 908
    bool live_0;

#line 917
    if(gateOnly_0)
    {



        if(winStart_2 == 0U)
        {

#line 922
            live_0 = winEnd_2 >= 256U;

#line 922
        }
        else
        {

#line 922
            live_0 = false;

#line 922
        }

#line 922
        if(live_0)
        {

#line 922
            m_1 = 0U;

#line 922
            i_4 = 0U;
            for(;;)
            {

#line 923
                if(i_4 < 16U)
                {
                }
                else
                {

#line 923
                    break;
                }

#line 924
                uint _S36 = max(m_1, (as_type<uint>((r_5[i_4].x * r_5[i_4].x + r_5[i_4].y * r_5[i_4].y))));

#line 923
                uint i_5 = i_4 + 1U;

#line 923
                m_1 = _S36;

#line 923
                i_4 = i_5;

#line 923
            }

#line 922
        }
        else
        {

#line 922
            m_1 = 0U;

#line 922
            i_4 = 0U;



            for(;;)
            {

#line 926
                if(i_4 < 16U)
                {
                }
                else
                {

#line 926
                    break;
                }

#line 927
                uint idx_1 = slotToIndex_0(tid_1 * 16U + i_4);
                if(idx_1 >= winStart_2)
                {

#line 928
                    live_0 = idx_1 < winEnd_2;

#line 928
                }
                else
                {

#line 928
                    live_0 = false;

#line 928
                }
                uint b_4 = (as_type<uint>((r_5[i_4].x * r_5[i_4].x + r_5[i_4].y * r_5[i_4].y)));
                if(live_0)
                {

#line 930
                    n2_0 = max(m_1, b_4);

#line 930
                }
                else
                {

#line 930
                    n2_0 = m_1;

#line 930
                }

#line 926
                uint i_6 = i_4 + 1U;

#line 926
                m_1 = n2_0;

#line 926
                i_4 = i_6;

#line 926
            }

#line 922
        }

#line 933
        uint m_2 = simd_max(m_1);

#line 941
        if(tid_1 == 0U)
        {

#line 942
            int device* _S37 = peakIdx_0+opair_0;

#line 942
            int _S38;

#line 942
            if(m_2 > 0U)
            {

#line 942
                _S38 = int(0);

#line 942
            }
            else
            {

#line 942
                _S38 = int(-1);

#line 942
            }

#line 942
            *_S37 = _S38;

#line 942
            *(peakVal_0+opair_0) = packed_float2(float2(sqrt((as_type<float>((m_2)))), 0.0f)) ;

#line 941
        }



        return;
    }

#line 951
    bool _S39 = tid_1 == 0U;

#line 951
    if(_S39)
    {

#line 951
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 951
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 951
    }



    float2 _S40 = float2(0.0f, 0.0f);

    if(winStart_2 == 0U)
    {

#line 957
        live_0 = winEnd_2 >= 256U;

#line 957
    }
    else
    {

#line 957
        live_0 = false;

#line 957
    }

#line 957
    uint threadBestSlot_0;

#line 957
    float2 threadBestVal_0;

#line 957
    if(live_0)
    {

#line 957
        m_1 = thrBits_1;

#line 957
        threadBestSlot_0 = 4294967295U;

#line 957
        threadBestVal_0 = _S40;

#line 957
        i_4 = 0U;
        for(;;)
        {

#line 958
            if(i_4 < 16U)
            {
            }
            else
            {

#line 958
                break;
            }

#line 959
            float _rx_0 = r_5[i_4].x;

#line 959
            float _ry_0 = r_5[i_4].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > m_1)
            {
                uint _S41 = tid_1 * 16U + i_4;
                float2 _S42 = float2(_rx_0, _ry_0);

#line 964
                m_1 = magBits_0;

#line 964
                threadBestSlot_0 = _S41;

#line 964
                threadBestVal_0 = _S42;

#line 961
            }

#line 958
            i_4 = i_4 + 1U;

#line 958
        }

#line 957
    }
    else
    {

#line 957
        m_1 = thrBits_1;

#line 957
        threadBestSlot_0 = 4294967295U;

#line 957
        threadBestVal_0 = _S40;

#line 957
        i_4 = 0U;

#line 968
        for(;;)
        {

#line 968
            if(i_4 < 16U)
            {
            }
            else
            {

#line 968
                break;
            }

#line 969
            uint _S43 = tid_1 * 16U + i_4;

#line 969
            uint idx_2 = slotToIndex_0(_S43);
            if(idx_2 >= winStart_2)
            {

#line 970
                live_0 = idx_2 < winEnd_2;

#line 970
            }
            else
            {

#line 970
                live_0 = false;

#line 970
            }
            float _rx_1 = r_5[i_4].x;

#line 971
            float _ry_1 = r_5[i_4].y;

#line 971
            uint magBits_1;
            if(live_0)
            {

#line 972
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 972
            }
            else
            {

#line 972
                magBits_1 = 0U;

#line 972
            }
            if(magBits_1 > m_1)
            {

                float2 _S44 = float2(_rx_1, _ry_1);

#line 976
                m_1 = magBits_1;

#line 976
                threadBestSlot_0 = _S43;

#line 976
                threadBestVal_0 = _S44;

#line 973
            }

#line 968
            i_4 = i_4 + 1U;

#line 968
        }

#line 957
    }

#line 981
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(m_1);
    bool _S45 = simd_is_first();

#line 985
    if(_S45)
    {

#line 985
        live_0 = wm_0 > thrBits_1;

#line 985
    }
    else
    {

#line 985
        live_0 = false;

#line 985
    }

#line 985
    if(live_0)
    {

#line 985
        uint _S46 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), wm_0, memory_order_relaxed);

#line 985
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(m_1 > thrBits_1)
    {

#line 992
        live_0 = m_1 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 992
    }
    else
    {

#line 992
        live_0 = false;

#line 992
    }

#line 992
    if(live_0)
    {

#line 992
        i_4 = threadBestSlot_0;

#line 992
    }
    else
    {

#line 992
        i_4 = 4294967295U;

#line 992
    }



    uint waveWinner_0 = simd_min(i_4);
    bool _S47 = simd_is_first();

#line 997
    if(_S47)
    {

#line 997
        live_0 = waveWinner_0 != 4294967295U;

#line 997
    }
    else
    {

#line 997
        live_0 = false;

#line 997
    }

#line 997
    if(live_0)
    {

#line 998
        uint _S48 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 997
    }

#line 1002
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(threadBestSlot_0 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])
    {

#line 1004
        live_0 = threadBestSlot_0 != 4294967295U;

#line 1004
    }
    else
    {

#line 1004
        live_0 = false;

#line 1004
    }

#line 1004
    if(live_0)
    {

#line 1005
        *(peakIdx_0+opair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 1005
        *(peakVal_0+opair_0) = packed_float2(threadBestVal_0) ;

#line 1004
    }



    if(_S39)
    {

#line 1008
        live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U]) == 4294967295U;

#line 1008
    }
    else
    {

#line 1008
        live_0 = false;

#line 1008
    }

#line 1008
    if(live_0)
    {

#line 1009
        *(peakIdx_0+opair_0) = int(-1);

#line 1009
        *(peakVal_0+opair_0) = packed_float2(_S40) ;

#line 1008
    }

#line 1218
    return;
}

void filterPair_0(uint pair_1, uint tid_2, packed_float2 device* data_1, packed_float2 device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_2, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{


    filterPairOut_0(pair_1, pair_1, tid_2, data_1, tmpl_1, peakIdx_1, peakVal_1, ntmpl_2, winStart_3, winEnd_3, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);



    return;
}


#line 2092
[[kernel]] void refineListedBounded(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]], uint device* entryPointParams_rowWin_1 [[buffer(7)]])
{

#line 2092
    thread KernelContext_0 kernelContext_7;

#line 2092
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 2092
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2092
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2092
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2092
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2092
    (&kernelContext_7)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2092
    (&kernelContext_7)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2092
    (&kernelContext_7)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 2092
    threadgroup array<uint, int(512)> stg_1;

#line 2092
    (&kernelContext_7)->stg_0 = &stg_1;

#line 2092
    (&kernelContext_7)->_binPhase_0 = 0U;

#line 2102
    uint _S49 = entryPointParams_count_1[int(0)];

#line 2102
    uint i_7 = gid_0.x;
    for(;;)
    {

#line 2103
        if(i_7 < _S49)
        {
        }
        else
        {

#line 2103
            break;
        }

#line 2104
        (&kernelContext_7)->_stgBase_0 = 0U;
        uint pair_2 = (&kernelContext_7)->entryPointParams_survivors_0[i_7];

#line 2105
        thread uint ws_0 = (&kernelContext_7)->entryPointParams_0->winStart_0;

#line 2105
        thread uint we_0 = (&kernelContext_7)->entryPointParams_0->winEnd_0;
        uint _S50 = pair_2 / (&kernelContext_7)->entryPointParams_0->ntmpl_0;

#line 2106
        rowWindow_0(_S50, &ws_0, &we_0, (&kernelContext_7)->entryPointParams_rowWin_0, &kernelContext_7);

#line 2106
        filterPair_0(pair_2, lid_0.x, (&kernelContext_7)->entryPointParams_data_0, (&kernelContext_7)->entryPointParams_tmpl_0, (&kernelContext_7)->entryPointParams_peakIdx_0, (&kernelContext_7)->entryPointParams_peakVal_0, (&kernelContext_7)->entryPointParams_0->ntmpl_0, ws_0, we_0, (&kernelContext_7)->entryPointParams_0->binsize_0, (&kernelContext_7)->entryPointParams_0->binShift_0, (&kernelContext_7)->entryPointParams_0->nbins_0, (&kernelContext_7)->entryPointParams_0->thrBits_0, &kernelContext_7);


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2103
        i_7 = i_7 + (&kernelContext_7)->entryPointParams_0->gridSize_0;

#line 2103
    }

#line 2111
    return;
}
