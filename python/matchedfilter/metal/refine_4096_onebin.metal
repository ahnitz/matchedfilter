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


#line 208 "mm_4096_refineListed_onebin.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0, uint device* rowWin_0)
{

#line 104 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 210 "mm_4096_refineListed_onebin.slang"
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


#line 169 "mm_4096_refineListed_onebin.slang"
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


#line 541
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_1 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_1 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_1 = float2(0.0f, 1.0f);
    float2 W6_1 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_1 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 548
    uint n1_1 = 0U;
    for(;;)
    {

#line 549
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 549
            break;
        }

#line 549
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 549
        n1_1 = n1_1 + 1U;

#line 549
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 550
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 550
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 551
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 551
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 552
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 552
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 552
    uint k2_1 = 0U;
    for(;;)
    {

#line 553
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 553
            break;
        }

#line 553
        uint _S15 = 4U * k2_1;

#line 553
        r4_0(&(*r_1)[_S15], &(*r_1)[_S15 + 1U], &(*r_1)[_S15 + 2U], &(*r_1)[_S15 + 3U]);

#line 553
        k2_1 = k2_1 + 1U;

#line 553
    }

    float2 t_6 = (*r_1)[int(1)];

#line 555
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 555
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 556
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 556
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 557
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 557
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 558
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 558
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 559
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 559
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 560
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 560
    (*r_1)[int(14)] = t_11;
    return;
}


#line 88 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S16 = ((MF_ACCURATE_TRIG));

#line 91
    return _S16;
}


#line 127
float2 mfTwiddle_0(float angle_0)
{

#line 93
    uint _S17 = mfAccurateTrigFlag_0();

#line 129
    if(_S17 == 0U)
    {

#line 130
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


#line 301 "mm_4096_refineListed_onebin.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S19 = max(TB_0, 1U);

#line 303
    uint j_0 = d_2 / _S19;

#line 303
    uint m_0 = d_2 % _S19;

#line 303
    uint _S20;
    if(TB_0 <= 16U)
    {

#line 304
        _S20 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 304
    }
    else
    {

#line 304
        _S20 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 304
    }

#line 304
    return _S20;
}


#line 8599 "hlsl.meta.slang"
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


#line 288 "mm_4096_refineListed_onebin.slang"
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


#line 288
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 288
    uint _S21 = 2U * i_1;

#line 288
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S21] = (as_type<uint>((v_0.x)));

#line 288
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S21 + 1U] = (as_type<uint>((v_0.y)));

#line 288
    return;
}


#line 289
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 289
    uint _S22 = 2U * i_2;

#line 289
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S22]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S22 + 1U]))));
}


#line 730
void exchange_0(array<float2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 731
    uint j_1;

#line 742
    thread array<float2, int(16)> out_0;

#line 742
    uint z_1 = 0U;
    for(;;)
    {

#line 743
        if(z_1 < 16U)
        {
        }
        else
        {

#line 743
            break;
        }

#line 743
        out_0[z_1] = float2(0.0f, 0.0f);

#line 743
        z_1 = z_1 + 1U;

#line 743
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S23 = p0_0 & lenMask_0;

#line 749
    uint _S24 = (_S23 >> lgSpan_0) * 256U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S23 & spanMask_0);

#line 749
    uint c_2 = 0U;

    for(;;)
    {

#line 751
        if(c_2 < 1U)
        {
        }
        else
        {

#line 751
            break;
        }

#line 752
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 752
        j_1 = 0U;
        for(;;)
        {

#line 753
            if(j_1 < 16U)
            {
            }
            else
            {

#line 753
                break;
            }

#line 753
            stgPut_0(j_1 * 256U + kernelContext_2->_tid_0, (*r_2)[c_2 * 16U + j_1], kernelContext_2);

#line 753
            j_1 = j_1 + 1U;

#line 753
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 754
        uint d_3 = 0U;
        for(;;)
        {

#line 755
            if(d_3 < 16U)
            {
            }
            else
            {

#line 755
                break;
            }

#line 756
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S25 = pz_0 & lenMask_0;
            uint az_0 = (_S25 >> lgSpan_0) * 256U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S25 & spanMask_0);

#line 758
            float2 _S26 = stgGet_0(_S24 + az_0 - c_2 * 16U * 256U, kernelContext_2);


            out_0[d_3] = _S26;

#line 755
            d_3 = d_3 + 1U;

#line 755
        }

#line 751
        c_2 = c_2 + 1U;

#line 751
    }

#line 751
    j_1 = 0U;

#line 764
    for(;;)
    {

#line 764
        if(j_1 < 16U)
        {
        }
        else
        {

#line 764
            break;
        }

#line 764
        (*r_2)[j_1] = out_0[j_1];

#line 764
        j_1 = j_1 + 1U;

#line 764
    }
    return;
}


#line 644
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 651
    dft16_1(r_3);

#line 656
    return;
}


#line 832
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 832
    uint _S27;

#line 832
    uint k2_2;

#line 832
    float cr_0;

#line 832
    float ci_0;

#line 832
    uint _S28;

#line 832
    for(;;)
    {

#line 832
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(256U);

#line 11
                _S27 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(4096U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 255U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 4096.0f);
                float _S29 = tw_0.x;

#line 40
                float _S30 = tw_0.y;

#line 40
                k2_2 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

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
                    float nr_0 = cr_0 * _S29 - ci_0 * _S30;
                    float _S31 = cr_0 * _S30 + ci_0 * _S29;

#line 42
                    k2_2 = k2_2 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S31;

#line 42
                }

#line 50
                uint per_2 = 16U / max(256U, 1U);
                uint _S32 = max(16U, 1U);

#line 51
                _S28 = _S32;
                uint blk2_2 = tid_0 / _S32;

#line 52
                uint lane2_2 = tid_0 % _S32;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 256U, 4096U, blk_2, lane_2, per_2, _S32, 256U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(16U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 15U;


                dft16_0(r_4);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 256.0f);
                float _S33 = tw_1.x;

#line 40
                float _S34 = tw_1.y;

#line 40
                k2_2 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

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
                    float nr_1 = cr_0 * _S33 - ci_0 * _S34;
                    float _S35 = cr_0 * _S34 + ci_0 * _S33;

#line 42
                    k2_2 = k2_2 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S35;

#line 42
                }

#line 50
                uint per_3 = 16U / _S28;
                uint _S36 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S36;

#line 52
                uint lane2_3 = tid_0 % _S36;

#line 52
                exchange_0(r_4, _S27, lgTB_1, 16U, 256U, blk_3, lane_3, per_3, _S36, 16U, blk2_3, lane2_3, kernelContext_3);

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

#line 835 "mm_4096_refineListed_onebin.slang"
    return;
}


#line 789
uint lgOf_0(uint i_3)
{

#line 789
    uint _S37;

#line 789
    if(i_3 < 2U)
    {

#line 789
        _S37 = 4U;

#line 789
    }
    else
    {

#line 789
        if(i_3 == 2U)
        {

#line 789
            _S37 = 4U;

#line 789
        }
        else
        {

#line 789
            _S37 = 1U;

#line 789
        }

#line 789
    }

#line 789
    return _S37;
}


#line 791
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 795
    uint lg_1 = lgOf_0(1U);

#line 795
    uint lg_2 = lgOf_0(0U);

#line 800
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 849
void filterPairOut_0(uint pair_0, uint opair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{


    uint threadBestBits_0;

#line 875
    kernelContext_4->_tid_0 = tid_1;
    uint _S38 = pair_0 / ntmpl_1;

#line 876
    uint _S39 = pair_0 % ntmpl_1;

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
        uint idx_0 = tid_1 + 256U * n2_0;

#line 77 "twiddle.slang"
        uint _S40 = mfDataStrideFlag_0();

#line 172 "mm_4096_refineListed_onebin.slang"
        if(_S40 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S41 = mfDataStrideFlag_0();

#line 77
            threadBestBits_0 = _S41;

#line 172 "mm_4096_refineListed_onebin.slang"
        }
        else
        {

#line 172
            threadBestBits_0 = 4096U;

#line 172
        }

#line 894
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S38 * threadBestBits_0 + idx_0), cload_0(tmpl_0, _S39 * 4096U + idx_0));

#line 892
        n2_0 = n2_0 + 1U;

#line 892
    }

#line 892
    transform_0(&r_5, tid_1, kernelContext_4);

#line 921
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 964
    bool _S42 = tid_1 == 0U;

#line 964
    if(_S42)
    {

#line 964
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 964
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 964
    }



    float2 _S43 = float2(0.0f, 0.0f);

#line 968
    bool live_0;

    if(winStart_2 == 0U)
    {

#line 970
        live_0 = winEnd_2 >= 4096U;

#line 970
    }
    else
    {

#line 970
        live_0 = false;

#line 970
    }

#line 970
    uint threadBestSlot_0;

#line 970
    uint winner_0;

#line 970
    float2 threadBestVal_0;

#line 970
    if(live_0)
    {

#line 970
        threadBestBits_0 = thrBits_1;

#line 970
        threadBestSlot_0 = 4294967295U;

#line 970
        threadBestVal_0 = _S43;

#line 970
        winner_0 = 0U;
        for(;;)
        {

#line 971
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 971
                break;
            }

#line 972
            float _rx_0 = r_5[winner_0].x;

#line 972
            float _ry_0 = r_5[winner_0].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > threadBestBits_0)
            {
                uint _S44 = tid_1 * 16U + winner_0;
                float2 _S45 = float2(_rx_0, _ry_0);

#line 977
                threadBestBits_0 = magBits_0;

#line 977
                threadBestSlot_0 = _S44;

#line 977
                threadBestVal_0 = _S45;

#line 974
            }

#line 971
            winner_0 = winner_0 + 1U;

#line 971
        }

#line 970
    }
    else
    {

#line 970
        threadBestBits_0 = thrBits_1;

#line 970
        threadBestSlot_0 = 4294967295U;

#line 970
        threadBestVal_0 = _S43;

#line 970
        winner_0 = 0U;

#line 981
        for(;;)
        {

#line 981
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 981
                break;
            }

#line 982
            uint _S46 = tid_1 * 16U + winner_0;

#line 982
            uint idx_1 = slotToIndex_0(_S46);
            if(idx_1 >= winStart_2)
            {

#line 983
                live_0 = idx_1 < winEnd_2;

#line 983
            }
            else
            {

#line 983
                live_0 = false;

#line 983
            }
            float _rx_1 = r_5[winner_0].x;

#line 984
            float _ry_1 = r_5[winner_0].y;

#line 984
            uint magBits_1;
            if(live_0)
            {

#line 985
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 985
            }
            else
            {

#line 985
                magBits_1 = 0U;

#line 985
            }
            if(magBits_1 > threadBestBits_0)
            {

                float2 _S47 = float2(_rx_1, _ry_1);

#line 989
                threadBestBits_0 = magBits_1;

#line 989
                threadBestSlot_0 = _S46;

#line 989
                threadBestVal_0 = _S47;

#line 986
            }

#line 981
            winner_0 = winner_0 + 1U;

#line 981
        }

#line 970
    }

#line 994
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(threadBestBits_0);
    bool _S48 = simd_is_first();

#line 998
    if(_S48)
    {

#line 998
        live_0 = wm_0 > thrBits_1;

#line 998
    }
    else
    {

#line 998
        live_0 = false;

#line 998
    }

#line 998
    if(live_0)
    {

#line 998
        uint _S49 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 998
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(threadBestBits_0 > thrBits_1)
    {

#line 1005
        live_0 = threadBestBits_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 1005
    }
    else
    {

#line 1005
        live_0 = false;

#line 1005
    }

#line 1005
    if(live_0)
    {

#line 1005
        winner_0 = threadBestSlot_0;

#line 1005
    }
    else
    {

#line 1005
        winner_0 = 4294967295U;

#line 1005
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S50 = simd_is_first();

#line 1010
    if(_S50)
    {

#line 1010
        live_0 = waveWinner_0 != 4294967295U;

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
        uint _S51 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1010
    }

#line 1015
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(threadBestSlot_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
    {

#line 1017
        live_0 = threadBestSlot_0 != 4294967295U;

#line 1017
    }
    else
    {

#line 1017
        live_0 = false;

#line 1017
    }

#line 1017
    if(live_0)
    {

#line 1018
        *(peakIdx_0+opair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 1018
        *(peakVal_0+opair_0) = packed_float2(threadBestVal_0) ;

#line 1017
    }



    if(_S42)
    {

#line 1021
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1021
    }
    else
    {

#line 1021
        live_0 = false;

#line 1021
    }

#line 1021
    if(live_0)
    {

#line 1022
        *(peakIdx_0+opair_0) = int(-1);

#line 1022
        *(peakVal_0+opair_0) = packed_float2(_S43) ;

#line 1021
    }

#line 1235
    return;
}

void filterPair_0(uint pair_1, uint tid_2, packed_float2 device* data_1, packed_float2 device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_2, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_5)
{


    filterPairOut_0(pair_1, pair_1, tid_2, data_1, tmpl_1, peakIdx_1, peakVal_1, ntmpl_2, winStart_3, winEnd_3, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_5);



    return;
}


#line 2142
[[kernel]] void refineListedBounded(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]], uint device* entryPointParams_rowWin_1 [[buffer(7)]])
{

#line 2142
    thread KernelContext_0 kernelContext_6;

#line 2142
    (&kernelContext_6)->entryPointParams_0 = entryPointParams_1;

#line 2142
    (&kernelContext_6)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2142
    (&kernelContext_6)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2142
    (&kernelContext_6)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2142
    (&kernelContext_6)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2142
    (&kernelContext_6)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2142
    (&kernelContext_6)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2142
    (&kernelContext_6)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 2142
    threadgroup array<uint, int(8192)> stg_1;

#line 2142
    (&kernelContext_6)->stg_0 = &stg_1;

#line 2152
    uint _S52 = entryPointParams_count_1[int(0)];

#line 2152
    uint i_4 = gid_0.x;
    for(;;)
    {

#line 2153
        if(i_4 < _S52)
        {
        }
        else
        {

#line 2153
            break;
        }

#line 2154
        (&kernelContext_6)->_stgBase_0 = 0U;
        uint pair_2 = (&kernelContext_6)->entryPointParams_survivors_0[i_4];

#line 2155
        thread uint ws_0 = (&kernelContext_6)->entryPointParams_0->winStart_1;

#line 2155
        thread uint we_0 = (&kernelContext_6)->entryPointParams_0->winEnd_1;
        uint _S53 = pair_2 / (&kernelContext_6)->entryPointParams_0->ntmpl_0;

#line 2156
        rowWindow_0(_S53, &ws_0, &we_0, (&kernelContext_6)->entryPointParams_rowWin_0);

#line 2156
        filterPair_0(pair_2, lid_0.x, (&kernelContext_6)->entryPointParams_data_0, (&kernelContext_6)->entryPointParams_tmpl_0, (&kernelContext_6)->entryPointParams_peakIdx_0, (&kernelContext_6)->entryPointParams_peakVal_0, (&kernelContext_6)->entryPointParams_0->ntmpl_0, ws_0, we_0, (&kernelContext_6)->entryPointParams_0->binsize_0, (&kernelContext_6)->entryPointParams_0->binShift_0, (&kernelContext_6)->entryPointParams_0->nbins_0, (&kernelContext_6)->entryPointParams_0->thrBits_0, &kernelContext_6);


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2153
        i_4 = i_4 + (&kernelContext_6)->entryPointParams_0->gridSize_0;

#line 2153
    }

#line 2161
    return;
}
