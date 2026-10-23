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


#line 311 "mm_512_fusedTierB_onebin.slang"
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
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 227
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 104 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 230 "mm_512_fusedTierB_onebin.slang"
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


#line 72 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S5 = ((MF_DATA_STRIDE));

#line 75
    return _S5;
}


#line 173 "mm_512_fusedTierB_onebin.slang"
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


#line 528
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 530
    float2 t1_0 = *a_1 - *c_0;

#line 530
    float2 t2_0 = *b_2 + *d_1;

#line 530
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 532
    *b_2 = t1_0 + j3_0;

#line 532
    *c_0 = t0_0 - t2_0;

#line 532
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


#line 564
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 571
    uint n1_0 = 0U;
    for(;;)
    {

#line 572
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 572
            break;
        }

#line 572
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 572
        n1_0 = n1_0 + 1U;

#line 572
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 573
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 573
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 574
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 574
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 575
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 575
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 575
    uint k2_0 = 0U;
    for(;;)
    {

#line 576
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 576
            break;
        }

#line 576
        uint _S14 = 4U * k2_0;

#line 576
        r4_0(&(*r_0)[_S14], &(*r_0)[_S14 + 1U], &(*r_0)[_S14 + 2U], &(*r_0)[_S14 + 3U]);

#line 576
        k2_0 = k2_0 + 1U;

#line 576
    }

    float2 t_0 = (*r_0)[int(1)];

#line 578
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 578
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 579
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 579
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 580
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 580
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 581
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 581
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 582
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 582
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 583
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 583
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


#line 324 "mm_512_fusedTierB_onebin.slang"
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


#line 753
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_3)
{

#line 754
    uint j_1;

#line 765
    thread array<float2, int(16)> out_0;

#line 765
    uint z_1 = 0U;
    for(;;)
    {

#line 766
        if(z_1 < 16U)
        {
        }
        else
        {

#line 766
            break;
        }

#line 766
        out_0[z_1] = float2(0.0f, 0.0f);

#line 766
        z_1 = z_1 + 1U;

#line 766
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S22 = p0_0 & lenMask_0;

#line 772
    uint _S23 = (_S22 >> lgSpan_0) * 32U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S22 & spanMask_0);

#line 772
    uint c_2 = 0U;

    for(;;)
    {

#line 774
        if(c_2 < 1U)
        {
        }
        else
        {

#line 774
            break;
        }

#line 775
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 775
        j_1 = 0U;
        for(;;)
        {

#line 776
            if(j_1 < 16U)
            {
            }
            else
            {

#line 776
                break;
            }

#line 776
            stgPut_0(j_1 * 32U + kernelContext_3->_tid_0, (*r_1)[c_2 * 16U + j_1], kernelContext_3);

#line 776
            j_1 = j_1 + 1U;

#line 776
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 777
        uint d_3 = 0U;
        for(;;)
        {

#line 778
            if(d_3 < 16U)
            {
            }
            else
            {

#line 778
                break;
            }

#line 779
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S24 = pz_0 & lenMask_0;
            uint az_0 = (_S24 >> lgSpan_0) * 32U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S24 & spanMask_0);

#line 781
            float2 _S25 = stgGet_0(_S23 + az_0 - c_2 * 16U * 32U, kernelContext_3);


            out_0[d_3] = _S25;

#line 778
            d_3 = d_3 + 1U;

#line 778
        }

#line 774
        c_2 = c_2 + 1U;

#line 774
    }

#line 774
    j_1 = 0U;

#line 787
    for(;;)
    {

#line 787
        if(j_1 < 16U)
        {
        }
        else
        {

#line 787
            break;
        }

#line 787
        (*r_1)[j_1] = out_0[j_1];

#line 787
        j_1 = j_1 + 1U;

#line 787
    }
    return;
}


#line 539
void dft2_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    float2 a_3 = (*r_2)[o_0];

#line 541
    float2 b_4 = (*r_2)[o_0 + 1U];

#line 541
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 541
    (*r_2)[o_0 + 1U] = a_3 - b_4;
    return;
}


#line 667
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 667
    uint b_5 = 0U;

#line 677
    for(;;)
    {

#line 677
        if(b_5 < 8U)
        {
        }
        else
        {

#line 677
            break;
        }

#line 677
        dft2_0(r_3, b_5 * 2U);

#line 677
        b_5 = b_5 + 1U;

#line 677
    }

    return;
}


#line 855
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_4)
{

#line 855
    uint _S26;

#line 855
    uint k2_1;

#line 855
    float cr_0;

#line 855
    float ci_0;

#line 855
    uint _S27;

#line 855
    for(;;)
    {

#line 855
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

#line 858 "mm_512_fusedTierB_onebin.slang"
    return;
}


#line 812
uint lgOf_0(uint i_3)
{

#line 812
    uint _S36;

#line 812
    if(i_3 < 2U)
    {

#line 812
        _S36 = 4U;

#line 812
    }
    else
    {

#line 812
        _S36 = 1U;

#line 812
    }

#line 812
    return _S36;
}


#line 814
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 818
    uint lg_1 = lgOf_0(1U);

#line 818
    uint lg_2 = lgOf_0(0U);

#line 823
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 878
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{


    uint threadBestBits_0;

#line 899
    kernelContext_5->_tid_0 = tid_1;
    uint _S37 = pair_0 / ntmpl_1;

#line 900
    uint _S38 = pair_0 % ntmpl_1;

#line 905
    thread array<float2, int(16)> r_5;

#line 905
    uint n2_0 = 0U;

#line 916
    for(;;)
    {

#line 916
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 916
            break;
        }

#line 917
        uint idx_0 = tid_1 + 32U * n2_0;

#line 77 "twiddle.slang"
        uint _S39 = mfDataStrideFlag_0();

#line 176 "mm_512_fusedTierB_onebin.slang"
        if(_S39 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S40 = mfDataStrideFlag_0();

#line 77
            threadBestBits_0 = _S40;

#line 176 "mm_512_fusedTierB_onebin.slang"
        }
        else
        {

#line 176
            threadBestBits_0 = 512U;

#line 176
        }

#line 918
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S37 * threadBestBits_0 + idx_0), cload_0(tmpl_0, _S38 * 512U + idx_0));

#line 916
        n2_0 = n2_0 + 1U;

#line 916
    }

#line 916
    transform_0(&r_5, tid_1, kernelContext_5);

#line 945
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 988
    bool _S41 = tid_1 == 0U;

#line 988
    if(_S41)
    {

#line 988
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 988
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 988
    }



    float2 _S42 = float2(0.0f, 0.0f);

#line 992
    bool live_0;

    if(winStart_2 == 0U)
    {

#line 994
        live_0 = winEnd_2 >= 512U;

#line 994
    }
    else
    {

#line 994
        live_0 = false;

#line 994
    }

#line 994
    uint threadBestSlot_0;

#line 994
    uint winner_0;

#line 994
    float2 threadBestVal_0;

#line 994
    if(live_0)
    {

#line 994
        threadBestBits_0 = thrBits_1;

#line 994
        threadBestSlot_0 = 4294967295U;

#line 994
        threadBestVal_0 = _S42;

#line 994
        winner_0 = 0U;
        for(;;)
        {

#line 995
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 995
                break;
            }

#line 996
            float _rx_0 = r_5[winner_0].x;

#line 996
            float _ry_0 = r_5[winner_0].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > threadBestBits_0)
            {
                uint _S43 = tid_1 * 16U + winner_0;
                float2 _S44 = float2(_rx_0, _ry_0);

#line 1001
                threadBestBits_0 = magBits_0;

#line 1001
                threadBestSlot_0 = _S43;

#line 1001
                threadBestVal_0 = _S44;

#line 998
            }

#line 995
            winner_0 = winner_0 + 1U;

#line 995
        }

#line 994
    }
    else
    {

#line 994
        threadBestBits_0 = thrBits_1;

#line 994
        threadBestSlot_0 = 4294967295U;

#line 994
        threadBestVal_0 = _S42;

#line 994
        winner_0 = 0U;

#line 1005
        for(;;)
        {

#line 1005
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 1005
                break;
            }

#line 1006
            uint _S45 = tid_1 * 16U + winner_0;

#line 1006
            uint idx_1 = slotToIndex_0(_S45);
            if(idx_1 >= winStart_2)
            {

#line 1007
                live_0 = idx_1 < winEnd_2;

#line 1007
            }
            else
            {

#line 1007
                live_0 = false;

#line 1007
            }
            float _rx_1 = r_5[winner_0].x;

#line 1008
            float _ry_1 = r_5[winner_0].y;

#line 1008
            uint magBits_1;
            if(live_0)
            {

#line 1009
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 1009
            }
            else
            {

#line 1009
                magBits_1 = 0U;

#line 1009
            }
            if(magBits_1 > threadBestBits_0)
            {

                float2 _S46 = float2(_rx_1, _ry_1);

#line 1013
                threadBestBits_0 = magBits_1;

#line 1013
                threadBestSlot_0 = _S45;

#line 1013
                threadBestVal_0 = _S46;

#line 1010
            }

#line 1005
            winner_0 = winner_0 + 1U;

#line 1005
        }

#line 994
    }

#line 1018
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(threadBestBits_0);
    bool _S47 = simd_is_first();

#line 1022
    if(_S47)
    {

#line 1022
        live_0 = wm_0 > thrBits_1;

#line 1022
    }
    else
    {

#line 1022
        live_0 = false;

#line 1022
    }

#line 1022
    if(live_0)
    {

#line 1022
        uint _S48 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1022
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(threadBestBits_0 > thrBits_1)
    {

#line 1029
        live_0 = threadBestBits_0 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1029
    }
    else
    {

#line 1029
        live_0 = false;

#line 1029
    }

#line 1029
    if(live_0)
    {

#line 1029
        winner_0 = threadBestSlot_0;

#line 1029
    }
    else
    {

#line 1029
        winner_0 = 4294967295U;

#line 1029
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S49 = simd_is_first();

#line 1034
    if(_S49)
    {

#line 1034
        live_0 = waveWinner_0 != 4294967295U;

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

#line 1035
        uint _S50 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1034
    }

#line 1039
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(threadBestSlot_0 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])
    {

#line 1041
        live_0 = threadBestSlot_0 != 4294967295U;

#line 1041
    }
    else
    {

#line 1041
        live_0 = false;

#line 1041
    }

#line 1041
    if(live_0)
    {

#line 1042
        *(peakIdx_0+pair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 1042
        *(peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 1041
    }



    if(_S41)
    {

#line 1045
        live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U]) == 4294967295U;

#line 1045
    }
    else
    {

#line 1045
        live_0 = false;

#line 1045
    }

#line 1045
    if(live_0)
    {

#line 1046
        *(peakIdx_0+pair_0) = int(-1);

#line 1046
        *(peakVal_0+pair_0) = packed_float2(_S42) ;

#line 1045
    }

#line 1259
    return;
}


#line 1750
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1750
    thread KernelContext_0 kernelContext_6;

#line 1750
    (&kernelContext_6)->entryPointParams_0 = entryPointParams_1;

#line 1750
    (&kernelContext_6)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1750
    (&kernelContext_6)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1750
    (&kernelContext_6)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1750
    (&kernelContext_6)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1750
    (&kernelContext_6)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1750
    threadgroup array<uint, int(1024)> stg_1;

#line 1750
    (&kernelContext_6)->stg_0 = &stg_1;

#line 1750
    (&kernelContext_6)->_binPhase_0 = 0U;

#line 1767
    uint _pr_0 = gid_0.x;

#line 1767
    uint _t_0 = lid_0.x;
    (&kernelContext_6)->_stgBase_0 = 0U;

#line 1777
    thread uint _ws_0 = entryPointParams_1->winStart_0;

#line 1777
    thread uint _we_0 = entryPointParams_1->winEnd_0;
    uint _S51 = _pr_0 / entryPointParams_1->ntmpl_0;

#line 1778
    rowWindow_0(_S51, &_ws_0, &_we_0, (&kernelContext_6)->entryPointParams_rowWin_0, &kernelContext_6);

#line 1778
    filterPair_0(_pr_0, _t_0, (&kernelContext_6)->entryPointParams_data_0, (&kernelContext_6)->entryPointParams_tmpl_0, (&kernelContext_6)->entryPointParams_peakIdx_0, (&kernelContext_6)->entryPointParams_peakVal_0, entryPointParams_1->ntmpl_0, _ws_0, _we_0, (&kernelContext_6)->entryPointParams_0->binsize_0, (&kernelContext_6)->entryPointParams_0->binShift_0, (&kernelContext_6)->entryPointParams_0->nbins_0, (&kernelContext_6)->entryPointParams_0->thrBits_0, &kernelContext_6);

#line 1785
    return;
}
