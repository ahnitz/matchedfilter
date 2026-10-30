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


#line 311 "mm_128_fusedTierB.slang"
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
    array<uint, int(256)> threadgroup* stg_0;
};


#line 227
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 90 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 230 "mm_128_fusedTierB.slang"
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


#line 173 "mm_128_fusedTierB.slang"
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


#line 324 "mm_128_fusedTierB.slang"
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


#line 311
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 311
    uint _S20 = 2U * i_1;

#line 311
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20] = (as_type<uint>((v_0.x)));

#line 311
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20 + 1U] = (as_type<uint>((v_0.y)));

#line 311
    return;
}


#line 312
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_2)
{

#line 312
    uint _S21 = 2U * i_2;

#line 312
    return float2((as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S21]))), (as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S21 + 1U]))));
}


#line 724
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_3)
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
    uint _S22 = p0_0 & lenMask_0;

#line 743
    uint _S23 = (_S22 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S22 & spanMask_0);

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
            stgPut_0(j_1 * 8U + kernelContext_3->_tid_0, (*r_1)[c_2 * 16U + j_1], kernelContext_3);

#line 747
            j_1 = j_1 + 1U;

#line 747
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 748
        uint d_3 = 0U;
        for(;;)
        {

#line 749
            if(d_3 < 16U)
            {
            }
            else
            {

#line 749
                break;
            }

#line 750
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S24 = pz_0 & lenMask_0;
            uint az_0 = (_S24 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S24 & spanMask_0);

#line 752
            float2 _S25 = stgGet_0(_S23 + az_0 - c_2 * 16U * 8U, kernelContext_3);


            out_0[d_3] = _S25;

#line 749
            d_3 = d_3 + 1U;

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
            uint _S26 = o_0 + j_2;

#line 529
            float2 t_6 = cmul_0(w_0, (*r_2)[_S26 + 4U]);
            uint _S27 = base_0 + k_0;

#line 530
            b_4[_S27] = (*r_2)[_S26] + t_6;

#line 530
            b_4[_S27 + s_1] = (*r_2)[_S26] - t_6;

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


#line 826
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_4)
{

#line 826
    for(;;)
    {

#line 826
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
                float _S28 = tw_0.x;

#line 40
                float _S29 = tw_0.y;

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
                    float nr_0 = cr_0 * _S28 - ci_0 * _S29;
                    float _S30 = cr_0 * _S29 + ci_0 * _S28;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S30;

#line 42
                }

#line 50
                uint per_2 = 16U / max(8U, 1U);
                uint _S31 = max(0U, 1U);
                uint blk2_2 = tid_0 / _S31;

#line 52
                uint lane2_2 = tid_0 % _S31;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 8U, 128U, blk_2, lane_2, per_2, _S31, 8U, blk2_2, lane2_2, kernelContext_4);

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

#line 829 "mm_128_fusedTierB.slang"
    return;
}


#line 783
uint lgOf_0(uint i_4)
{

#line 783
    uint _S32;

#line 783
    if(i_4 < 1U)
    {

#line 783
        _S32 = 4U;

#line 783
    }
    else
    {

#line 783
        if(i_4 == 1U)
        {

#line 783
            _S32 = 3U;

#line 783
        }
        else
        {

#line 783
            _S32 = 1U;

#line 783
        }

#line 783
    }

#line 783
    return _S32;
}


#line 785
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 789
    uint lg_1 = lgOf_0(0U);

#line 794
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 849
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{


    uint b_6;

#line 870
    kernelContext_5->_tid_0 = tid_1;
    uint _S33 = pair_0 / ntmpl_1;

#line 871
    uint _S34 = pair_0 % ntmpl_1;

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
        uint idx_0 = tid_1 + 8U * n2_0;

#line 63 "twiddle.slang"
        uint _S35 = mfDataStrideFlag_0();

#line 176 "mm_128_fusedTierB.slang"
        if(_S35 != 0U)
        {

#line 63 "twiddle.slang"
            uint _S36 = mfDataStrideFlag_0();

#line 63
            b_6 = _S36;

#line 176 "mm_128_fusedTierB.slang"
        }
        else
        {

#line 176
            b_6 = 128U;

#line 176
        }

#line 889
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S33 * b_6 + idx_0), cload_0(tmpl_0, _S34 * 128U + idx_0));

#line 887
        n2_0 = n2_0 + 1U;

#line 887
    }

#line 887
    transform_0(&r_5, tid_1, kernelContext_5);

#line 906
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 906
    b_6 = tid_1;

#line 1018
    for(;;)
    {

#line 1018
        if(b_6 < nbins_1)
        {
        }
        else
        {

#line 1018
            break;
        }

#line 1018
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + b_6] = thrBits_1;

#line 1018
        b_6 = b_6 + 8U;

#line 1018
    }
    bool _S37 = nbins_1 == 1U;

#line 1019
    bool live_0;

#line 1019
    if(_S37)
    {

#line 1019
        live_0 = tid_1 == 0U;

#line 1019
    }
    else
    {

#line 1019
        live_0 = false;

#line 1019
    }

#line 1019
    if(live_0)
    {

#line 1019
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 1019
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1078
    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 1079
    uint i_5 = 0U;



    for(;;)
    {

#line 1083
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1083
            break;
        }

#line 1084
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_5);
        if(idx_1 >= winStart_2)
        {

#line 1085
            live_0 = idx_1 < winEnd_2;

#line 1085
        }
        else
        {

#line 1085
            live_0 = false;

#line 1085
        }



        float _rx_0 = r_5[i_5].x;

#line 1089
        float _ry_0 = r_5[i_5].y;
        if(live_0)
        {

#line 1090
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1090
        }
        else
        {

#line 1090
            n2_0 = 0U;

#line 1090
        }

#line 1090
        myMag_0[i_5] = n2_0;

#line 1098
        uint off_0 = idx_1 - winStart_2 + kernelContext_5->_binPhase_0;

#line 1105
        if(live_0)
        {

#line 1105
            if(binShift_1 >= int(0))
            {

#line 1105
                b_6 = off_0 >> uint(binShift_1);

#line 1105
            }
            else
            {

#line 1105
                uint _S38 = off_0 / binsize_1;

#line 1105
                b_6 = _S38;

#line 1105
            }

#line 1105
        }
        else
        {

#line 1105
            b_6 = 0U;

#line 1105
        }

#line 1105
        myBin_0[i_5] = b_6;

#line 1105
        bool _S39;



        if(nbins_1 > 1U)
        {

#line 1109
            _S39 = (myMag_0[i_5]) > thrBits_1;

#line 1109
        }
        else
        {

#line 1109
            _S39 = false;

#line 1109
        }

#line 1109
        if(_S39)
        {

#line 1110
            uint _S40 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + myBin_0[i_5]])), myMag_0[i_5], memory_order_relaxed);

#line 1109
        }

#line 1083
        i_5 = i_5 + 1U;

#line 1083
    }

#line 1083
    uint winner_0;

#line 1133
    if(_S37)
    {

#line 1133
        winner_0 = thrBits_1;

#line 1133
        i_5 = 0U;


        for(;;)
        {

#line 1136
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1136
                break;
            }

#line 1136
            uint _S41 = max(winner_0, myMag_0[i_5]);

#line 1136
            uint i_6 = i_5 + 1U;

#line 1136
            winner_0 = _S41;

#line 1136
            i_5 = i_6;

#line 1136
        }

        uint wm_0 = simd_max(winner_0);
        bool _S42 = simd_is_first();

#line 1139
        if(_S42)
        {

#line 1139
            live_0 = wm_0 > thrBits_1;

#line 1139
        }
        else
        {

#line 1139
            live_0 = false;

#line 1139
        }

#line 1139
        if(live_0)
        {

#line 1139
            uint _S43 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1139
        }

#line 1133
    }

#line 1154
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1161
    if(_S37)
    {

#line 1161
        winner_0 = 4294967295U;

#line 1161
        i_5 = 0U;


        for(;;)
        {

#line 1164
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1164
                break;
            }

#line 1165
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1165
                live_0 = (myMag_0[i_5]) == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1165
            }
            else
            {

#line 1165
                live_0 = false;

#line 1165
            }

#line 1165
            if(live_0)
            {

#line 1165
                winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 1165
            }

#line 1164
            i_5 = i_5 + 1U;

#line 1164
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S44 = simd_is_first();

#line 1169
        if(_S44)
        {

#line 1169
            live_0 = waveWinner_0 != 4294967295U;

#line 1169
        }
        else
        {

#line 1169
            live_0 = false;

#line 1169
        }

#line 1169
        if(live_0)
        {

#line 1170
            uint _S45 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1169
        }

#line 1174
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1174
        i_5 = 0U;
        for(;;)
        {

#line 1175
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1175
                break;
            }

#line 1176
            uint _S46 = tid_1 * 16U + i_5;

#line 1176
            if(_S46 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])
            {

#line 1177
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S46));

#line 1177
                *(peakVal_0+pair_0) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 1176
            }

#line 1175
            i_5 = i_5 + 1U;

#line 1175
        }

#line 1181
        if(tid_1 == 0U)
        {

#line 1181
            live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U]) == 4294967295U;

#line 1181
        }
        else
        {

#line 1181
            live_0 = false;

#line 1181
        }

#line 1181
        if(live_0)
        {

#line 1182
            *(peakIdx_0+pair_0) = int(-1);

#line 1182
            *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1181
        }

#line 1161
    }
    else
    {

#line 1161
        i_5 = 0U;

#line 1190
        for(;;)
        {

#line 1190
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1190
                break;
            }

#line 1191
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1191
                live_0 = (myMag_0[i_5]) == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + myBin_0[i_5]];

#line 1191
            }
            else
            {

#line 1191
                live_0 = false;

#line 1191
            }

#line 1191
            myMag_0[i_5] = uint(live_0);

#line 1190
            i_5 = i_5 + 1U;

#line 1190
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1193
        b_6 = tid_1;
        for(;;)
        {

#line 1194
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 1194
                break;
            }

#line 1194
            (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + b_6] = 4294967295U;

#line 1194
            b_6 = b_6 + 8U;

#line 1194
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1195
        i_5 = 0U;
        for(;;)
        {

#line 1196
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1196
                break;
            }

#line 1197
            if((myMag_0[i_5]) != 0U)
            {

#line 1197
                uint _S47 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + myBin_0[i_5]])), tid_1 * 16U + i_5, memory_order_relaxed);

#line 1197
            }

#line 1196
            i_5 = i_5 + 1U;

#line 1196
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1198
        i_5 = 0U;
        for(;;)
        {

#line 1199
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1199
                break;
            }

#line 1200
            if((myMag_0[i_5]) != 0U)
            {

#line 1200
                live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + myBin_0[i_5]]) == (tid_1 * 16U + i_5);

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
                uint o_1 = pair_0 * nbins_1 + myBin_0[i_5];
                *(peakIdx_0+o_1) = int(slotToIndex_0(tid_1 * 16U + i_5));

#line 1202
                *(peakVal_0+o_1) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 1200
            }

#line 1199
            i_5 = i_5 + 1U;

#line 1199
        }

#line 1199
        b_6 = tid_1;

#line 1206
        for(;;)
        {

#line 1206
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 1206
                break;
            }

#line 1207
            if(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + b_6]) == 4294967295U)
            {

#line 1208
                uint _S48 = pair_0 * nbins_1 + b_6;

#line 1208
                *(peakIdx_0+_S48) = int(-1);

#line 1208
                *(peakVal_0+_S48) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1207
            }

#line 1206
            b_6 = b_6 + 8U;

#line 1206
        }

#line 1161
    }

#line 1216
    return;
}


#line 1672
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1672
    thread KernelContext_0 kernelContext_6;

#line 1672
    (&kernelContext_6)->entryPointParams_0 = entryPointParams_1;

#line 1672
    (&kernelContext_6)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1672
    (&kernelContext_6)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1672
    (&kernelContext_6)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1672
    (&kernelContext_6)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1672
    (&kernelContext_6)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1672
    threadgroup array<uint, int(256)> stg_1;

#line 1672
    (&kernelContext_6)->stg_0 = &stg_1;

#line 1672
    (&kernelContext_6)->_binPhase_0 = 0U;

#line 1689
    uint _pr_0 = gid_0.x;

#line 1689
    uint _t_0 = lid_0.x;
    (&kernelContext_6)->_stgBase_0 = 0U;

#line 1699
    thread uint _ws_0 = entryPointParams_1->winStart_0;

#line 1699
    thread uint _we_0 = entryPointParams_1->winEnd_0;
    uint _S49 = _pr_0 / entryPointParams_1->ntmpl_0;

#line 1700
    rowWindow_0(_S49, &_ws_0, &_we_0, (&kernelContext_6)->entryPointParams_rowWin_0, &kernelContext_6);

#line 1700
    filterPair_0(_pr_0, _t_0, (&kernelContext_6)->entryPointParams_data_0, (&kernelContext_6)->entryPointParams_tmpl_0, (&kernelContext_6)->entryPointParams_peakIdx_0, (&kernelContext_6)->entryPointParams_peakVal_0, entryPointParams_1->ntmpl_0, _ws_0, _we_0, (&kernelContext_6)->entryPointParams_0->binsize_0, (&kernelContext_6)->entryPointParams_0->binShift_0, (&kernelContext_6)->entryPointParams_0->nbins_0, (&kernelContext_6)->entryPointParams_0->thrBits_0, &kernelContext_6);

#line 1707
    return;
}
