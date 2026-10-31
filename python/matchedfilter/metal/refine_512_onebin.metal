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


#line 312 "mm_512_refineListed_onebin.slang"
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
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 228
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 90 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 231 "mm_512_refineListed_onebin.slang"
    if(_S3 == 0U)
    {

#line 231
        return;
    }

#line 232
    uint _S4 = 3U * d_0;

#line 232
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


#line 174 "mm_512_refineListed_onebin.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 174
    return float2(*(b_0+i_0)) ;
}


#line 324
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 324
    float _S6 = a_0.x;

#line 324
    float _S7 = b_1.x;

#line 324
    float _S8 = a_0.y;

#line 324
    float _S9 = b_1.y;

#line 324
    return float2(_S6 * _S7 + _S8 * _S9, _S8 * _S7 - _S6 * _S9);
}


#line 500
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 502
    float2 t1_0 = *a_1 - *c_0;

#line 502
    float2 t2_0 = *b_2 + *d_1;

#line 502
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 504
    *b_2 = t1_0 + j3_0;

#line 504
    *c_0 = t0_0 - t2_0;

#line 504
    *d_1 = t1_0 - j3_0;
    return;
}


#line 323
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 323
    float _S10 = a_2.x;

#line 323
    float _S11 = b_3.x;

#line 323
    float _S12 = a_2.y;

#line 323
    float _S13 = b_3.y;

#line 323
    return float2(_S10 * _S11 - _S12 * _S13, _S10 * _S13 + _S12 * _S11);
}


#line 536
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 543
    uint n1_0 = 0U;
    for(;;)
    {

#line 544
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 544
            break;
        }

#line 544
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 544
        n1_0 = n1_0 + 1U;

#line 544
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 545
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 545
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 546
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 546
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 547
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 547
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 547
    uint k2_0 = 0U;
    for(;;)
    {

#line 548
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 548
            break;
        }

#line 548
        uint _S14 = 4U * k2_0;

#line 548
        r4_0(&(*r_0)[_S14], &(*r_0)[_S14 + 1U], &(*r_0)[_S14 + 2U], &(*r_0)[_S14 + 3U]);

#line 548
        k2_0 = k2_0 + 1U;

#line 548
    }

    float2 t_0 = (*r_0)[int(1)];

#line 550
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 550
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 551
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 551
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 552
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 552
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 553
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 553
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 554
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 554
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 555
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 555
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


#line 325 "mm_512_refineListed_onebin.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S18 = max(TB_0, 1U);

#line 327
    uint j_0 = d_2 / _S18;

#line 327
    uint m_0 = d_2 % _S18;

#line 327
    uint _S19;
    if(TB_0 <= 16U)
    {

#line 328
        _S19 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 328
    }
    else
    {

#line 328
        _S19 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 328
    }

#line 328
    return _S19;
}


#line 312
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 312
    uint _S20 = 2U * i_1;

#line 312
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20] = (as_type<uint>((v_0.x)));

#line 312
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20 + 1U] = (as_type<uint>((v_0.y)));

#line 312
    return;
}


#line 313
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_2)
{

#line 313
    uint _S21 = 2U * i_2;

#line 313
    return float2((as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S21]))), (as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S21 + 1U]))));
}


#line 725
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_3)
{

#line 726
    uint j_1;

#line 737
    thread array<float2, int(16)> out_0;

#line 737
    uint z_1 = 0U;
    for(;;)
    {

#line 738
        if(z_1 < 16U)
        {
        }
        else
        {

#line 738
            break;
        }

#line 738
        out_0[z_1] = float2(0.0f, 0.0f);

#line 738
        z_1 = z_1 + 1U;

#line 738
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S22 = p0_0 & lenMask_0;

#line 744
    uint _S23 = (_S22 >> lgSpan_0) * 32U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S22 & spanMask_0);

#line 744
    uint c_2 = 0U;

    for(;;)
    {

#line 746
        if(c_2 < 1U)
        {
        }
        else
        {

#line 746
            break;
        }

#line 747
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 747
        j_1 = 0U;
        for(;;)
        {

#line 748
            if(j_1 < 16U)
            {
            }
            else
            {

#line 748
                break;
            }

#line 748
            stgPut_0(j_1 * 32U + kernelContext_3->_tid_0, (*r_1)[c_2 * 16U + j_1], kernelContext_3);

#line 748
            j_1 = j_1 + 1U;

#line 748
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 749
        uint d_3 = 0U;
        for(;;)
        {

#line 750
            if(d_3 < 16U)
            {
            }
            else
            {

#line 750
                break;
            }

#line 751
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S24 = pz_0 & lenMask_0;
            uint az_0 = (_S24 >> lgSpan_0) * 32U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S24 & spanMask_0);

#line 753
            float2 _S25 = stgGet_0(_S23 + az_0 - c_2 * 16U * 32U, kernelContext_3);


            out_0[d_3] = _S25;

#line 750
            d_3 = d_3 + 1U;

#line 750
        }

#line 746
        c_2 = c_2 + 1U;

#line 746
    }

#line 746
    j_1 = 0U;

#line 759
    for(;;)
    {

#line 759
        if(j_1 < 16U)
        {
        }
        else
        {

#line 759
            break;
        }

#line 759
        (*r_1)[j_1] = out_0[j_1];

#line 759
        j_1 = j_1 + 1U;

#line 759
    }
    return;
}


#line 511
void dft2_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    float2 a_3 = (*r_2)[o_0];

#line 513
    float2 b_4 = (*r_2)[o_0 + 1U];

#line 513
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 513
    (*r_2)[o_0 + 1U] = a_3 - b_4;
    return;
}


#line 639
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 639
    uint b_5 = 0U;

#line 649
    for(;;)
    {

#line 649
        if(b_5 < 8U)
        {
        }
        else
        {

#line 649
            break;
        }

#line 649
        dft2_0(r_3, b_5 * 2U);

#line 649
        b_5 = b_5 + 1U;

#line 649
    }

    return;
}


#line 830
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_4)
{

#line 830
    uint _S26;

#line 830
    uint k2_1;

#line 830
    float cr_0;

#line 830
    float ci_0;

#line 830
    uint _S27;

#line 830
    for(;;)
    {

#line 830
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(32U);

#line 11
                _S26 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(512U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 31U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 512.0f);
                float _S28 = tw_0.x;

#line 40
                float _S29 = tw_0.y;

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
                uint per_2 = 16U / max(32U, 1U);
                uint _S31 = max(2U, 1U);

#line 51
                _S27 = _S31;
                uint blk2_2 = tid_0 / _S31;

#line 52
                uint lane2_2 = tid_0 % _S31;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 32U, 512U, blk_2, lane_2, per_2, _S31, 32U, blk2_2, lane2_2, kernelContext_4);

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


                uint lgTB_1 = firstbithigh_0(2U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 1U;


                dft16_0(r_4);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 32.0f);
                float _S32 = tw_1.x;

#line 40
                float _S33 = tw_1.y;

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
                    float nr_1 = cr_0 * _S32 - ci_0 * _S33;
                    float _S34 = cr_0 * _S33 + ci_0 * _S32;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S34;

#line 42
                }

#line 50
                uint per_3 = 16U / _S27;
                uint _S35 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S35;

#line 52
                uint lane2_3 = tid_0 % _S35;

#line 52
                exchange_0(r_4, _S26, lgTB_1, 2U, 32U, blk_3, lane_3, per_3, _S35, 2U, blk2_3, lane2_3, kernelContext_4);

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

#line 833 "mm_512_refineListed_onebin.slang"
    return;
}


#line 784
uint lgOf_0(uint i_3)
{

#line 784
    uint _S36;

#line 784
    if(i_3 < 2U)
    {

#line 784
        _S36 = 4U;

#line 784
    }
    else
    {

#line 784
        _S36 = 1U;

#line 784
    }

#line 784
    return _S36;
}


#line 786
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 790
    uint lg_1 = lgOf_0(1U);

#line 790
    uint lg_2 = lgOf_0(0U);

#line 795
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 847
void filterPairOut_0(uint pair_0, uint opair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{


    uint threadBestBits_0;

#line 874
    kernelContext_5->_tid_0 = tid_1;
    uint _S37 = pair_0 / ntmpl_1;

#line 875
    uint _S38 = pair_0 % ntmpl_1;

#line 880
    thread array<float2, int(16)> r_5;

#line 880
    uint n2_0 = 0U;

#line 891
    for(;;)
    {

#line 891
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 891
            break;
        }

#line 892
        uint idx_0 = tid_1 + 32U * n2_0;

#line 63 "twiddle.slang"
        uint _S39 = mfDataStrideFlag_0();

#line 177 "mm_512_refineListed_onebin.slang"
        if(_S39 != 0U)
        {

#line 63 "twiddle.slang"
            uint _S40 = mfDataStrideFlag_0();

#line 63
            threadBestBits_0 = _S40;

#line 177 "mm_512_refineListed_onebin.slang"
        }
        else
        {

#line 177
            threadBestBits_0 = 512U;

#line 177
        }

#line 893
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S37 * threadBestBits_0 + idx_0), cload_0(tmpl_0, _S38 * 512U + idx_0));

#line 891
        n2_0 = n2_0 + 1U;

#line 891
    }

#line 891
    transform_0(&r_5, tid_1, kernelContext_5);

#line 910
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 953
    bool _S41 = tid_1 == 0U;

#line 953
    if(_S41)
    {

#line 953
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 953
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 953
    }



    float2 _S42 = float2(0.0f, 0.0f);

#line 957
    bool live_0;

    if(winStart_2 == 0U)
    {

#line 959
        live_0 = winEnd_2 >= 512U;

#line 959
    }
    else
    {

#line 959
        live_0 = false;

#line 959
    }

#line 959
    uint threadBestSlot_0;

#line 959
    uint winner_0;

#line 959
    float2 threadBestVal_0;

#line 959
    if(live_0)
    {

#line 959
        threadBestBits_0 = thrBits_1;

#line 959
        threadBestSlot_0 = 4294967295U;

#line 959
        threadBestVal_0 = _S42;

#line 959
        winner_0 = 0U;
        for(;;)
        {

#line 960
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 960
                break;
            }

#line 961
            float _rx_0 = r_5[winner_0].x;

#line 961
            float _ry_0 = r_5[winner_0].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > threadBestBits_0)
            {
                uint _S43 = tid_1 * 16U + winner_0;
                float2 _S44 = float2(_rx_0, _ry_0);

#line 966
                threadBestBits_0 = magBits_0;

#line 966
                threadBestSlot_0 = _S43;

#line 966
                threadBestVal_0 = _S44;

#line 963
            }

#line 960
            winner_0 = winner_0 + 1U;

#line 960
        }

#line 959
    }
    else
    {

#line 959
        threadBestBits_0 = thrBits_1;

#line 959
        threadBestSlot_0 = 4294967295U;

#line 959
        threadBestVal_0 = _S42;

#line 959
        winner_0 = 0U;

#line 970
        for(;;)
        {

#line 970
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 970
                break;
            }

#line 971
            uint _S45 = tid_1 * 16U + winner_0;

#line 971
            uint idx_1 = slotToIndex_0(_S45);
            if(idx_1 >= winStart_2)
            {

#line 972
                live_0 = idx_1 < winEnd_2;

#line 972
            }
            else
            {

#line 972
                live_0 = false;

#line 972
            }
            float _rx_1 = r_5[winner_0].x;

#line 973
            float _ry_1 = r_5[winner_0].y;

#line 973
            uint magBits_1;
            if(live_0)
            {

#line 974
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 974
            }
            else
            {

#line 974
                magBits_1 = 0U;

#line 974
            }
            if(magBits_1 > threadBestBits_0)
            {

                float2 _S46 = float2(_rx_1, _ry_1);

#line 978
                threadBestBits_0 = magBits_1;

#line 978
                threadBestSlot_0 = _S45;

#line 978
                threadBestVal_0 = _S46;

#line 975
            }

#line 970
            winner_0 = winner_0 + 1U;

#line 970
        }

#line 959
    }

#line 983
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(threadBestBits_0);
    bool _S47 = simd_is_first();

#line 987
    if(_S47)
    {

#line 987
        live_0 = wm_0 > thrBits_1;

#line 987
    }
    else
    {

#line 987
        live_0 = false;

#line 987
    }

#line 987
    if(live_0)
    {

#line 987
        uint _S48 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), wm_0, memory_order_relaxed);

#line 987
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(threadBestBits_0 > thrBits_1)
    {

#line 994
        live_0 = threadBestBits_0 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 994
    }
    else
    {

#line 994
        live_0 = false;

#line 994
    }

#line 994
    if(live_0)
    {

#line 994
        winner_0 = threadBestSlot_0;

#line 994
    }
    else
    {

#line 994
        winner_0 = 4294967295U;

#line 994
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S49 = simd_is_first();

#line 999
    if(_S49)
    {

#line 999
        live_0 = waveWinner_0 != 4294967295U;

#line 999
    }
    else
    {

#line 999
        live_0 = false;

#line 999
    }

#line 999
    if(live_0)
    {

#line 1000
        uint _S50 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 999
    }

#line 1004
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(threadBestSlot_0 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])
    {

#line 1006
        live_0 = threadBestSlot_0 != 4294967295U;

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
        *(peakIdx_0+opair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 1007
        *(peakVal_0+opair_0) = packed_float2(threadBestVal_0) ;

#line 1006
    }



    if(_S41)
    {

#line 1010
        live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U]) == 4294967295U;

#line 1010
    }
    else
    {

#line 1010
        live_0 = false;

#line 1010
    }

#line 1010
    if(live_0)
    {

#line 1011
        *(peakIdx_0+opair_0) = int(-1);

#line 1011
        *(peakVal_0+opair_0) = packed_float2(_S42) ;

#line 1010
    }

#line 1233
    return;
}

void filterPair_0(uint pair_1, uint tid_2, packed_float2 device* data_1, packed_float2 device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_2, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{


    filterPairOut_0(pair_1, pair_1, tid_2, data_1, tmpl_1, peakIdx_1, peakVal_1, ntmpl_2, winStart_3, winEnd_3, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);



    return;
}


#line 2118
[[kernel]] void refineListedBounded(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]], uint device* entryPointParams_rowWin_1 [[buffer(7)]])
{

#line 2118
    thread KernelContext_0 kernelContext_7;

#line 2118
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 2118
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2118
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2118
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2118
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2118
    (&kernelContext_7)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2118
    (&kernelContext_7)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2118
    (&kernelContext_7)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 2118
    threadgroup array<uint, int(1024)> stg_1;

#line 2118
    (&kernelContext_7)->stg_0 = &stg_1;

#line 2118
    (&kernelContext_7)->_binPhase_0 = 0U;

#line 2128
    uint _S51 = entryPointParams_count_1[int(0)];

#line 2128
    uint i_4 = gid_0.x;
    for(;;)
    {

#line 2129
        if(i_4 < _S51)
        {
        }
        else
        {

#line 2129
            break;
        }

#line 2130
        (&kernelContext_7)->_stgBase_0 = 0U;
        uint pair_2 = (&kernelContext_7)->entryPointParams_survivors_0[i_4];

#line 2131
        thread uint ws_0 = (&kernelContext_7)->entryPointParams_0->winStart_0;

#line 2131
        thread uint we_0 = (&kernelContext_7)->entryPointParams_0->winEnd_0;
        uint _S52 = pair_2 / (&kernelContext_7)->entryPointParams_0->ntmpl_0;

#line 2132
        rowWindow_0(_S52, &ws_0, &we_0, (&kernelContext_7)->entryPointParams_rowWin_0, &kernelContext_7);

#line 2132
        filterPair_0(pair_2, lid_0.x, (&kernelContext_7)->entryPointParams_data_0, (&kernelContext_7)->entryPointParams_tmpl_0, (&kernelContext_7)->entryPointParams_peakIdx_0, (&kernelContext_7)->entryPointParams_peakVal_0, (&kernelContext_7)->entryPointParams_0->ntmpl_0, ws_0, we_0, (&kernelContext_7)->entryPointParams_0->binsize_0, (&kernelContext_7)->entryPointParams_0->binShift_0, (&kernelContext_7)->entryPointParams_0->nbins_0, (&kernelContext_7)->entryPointParams_0->thrBits_0, &kernelContext_7);


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2129
        i_4 = i_4 + (&kernelContext_7)->entryPointParams_0->gridSize_0;

#line 2129
    }

#line 2137
    return;
}
