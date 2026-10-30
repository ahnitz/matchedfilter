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


#line 312 "mm_65536_refineListed.slang"
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
    array<uint, int(16384)> threadgroup* stg_0;
};


#line 228
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 90 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 231 "mm_65536_refineListed.slang"
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


#line 174 "mm_65536_refineListed.slang"
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


#line 74 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S10 = ((MF_ACCURATE_TRIG));

#line 77
    return _S10;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S11 = mfAccurateTrigFlag_0();

#line 103
    if(_S11 == 0U)
    {

#line 104
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S12 = float(quadrant_0);
    float x_0 = angle_0 - _S12 * 1.57079625129699707f - _S12 * 7.54978941586159635e-08f;
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


#line 323 "mm_65536_refineListed.slang"
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 323
    float _S13 = a_2.x;

#line 323
    float _S14 = b_3.x;

#line 323
    float _S15 = a_2.y;

#line 323
    float _S16 = b_3.y;

#line 323
    return float2(_S13 * _S14 - _S15 * _S16, _S13 * _S16 + _S15 * _S14);
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
        uint _S17 = 4U * k2_0;

#line 548
        r4_0(&(*r_0)[_S17], &(*r_0)[_S17 + 1U], &(*r_0)[_S17 + 2U], &(*r_0)[_S17 + 3U]);

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


#line 602
void dft64_0(array<float2, int(64)> thread* r_1)
{

#line 602
    uint k_0;

#line 602
    uint j_0 = 0U;

    for(;;)
    {

#line 604
        if(j_0 < 16U)
        {
        }
        else
        {

#line 604
            break;
        }

#line 605
        r4_0(&(*r_1)[j_0], &(*r_1)[j_0 + 16U], &(*r_1)[j_0 + 32U], &(*r_1)[j_0 + 48U]);

#line 604
        j_0 = j_0 + 1U;

#line 604
    }

    thread array<float2, int(64)> o_0;

#line 606
    uint pp_0 = 0U;
    for(;;)
    {

#line 607
        if(pp_0 < 4U)
        {
        }
        else
        {

#line 607
            break;
        }

#line 608
        thread array<float2, int(16)> b_4;

#line 608
        j_0 = 0U;
        for(;;)
        {

#line 609
            if(j_0 < 16U)
            {
            }
            else
            {

#line 609
                break;
            }
            float2 _S18 = mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f);

#line 611
            b_4[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], _S18);

#line 609
            j_0 = j_0 + 1U;

#line 609
        }



        dft16_0(&b_4);

#line 613
        k_0 = 0U;
        for(;;)
        {

#line 614
            if(k_0 < 16U)
            {
            }
            else
            {

#line 614
                break;
            }

#line 614
            o_0[4U * k_0 + pp_0] = b_4[k_0];

#line 614
            k_0 = k_0 + 1U;

#line 614
        }

#line 607
        pp_0 = pp_0 + 1U;

#line 607
    }

#line 607
    k_0 = 0U;

#line 616
    for(;;)
    {

#line 616
        if(k_0 < 64U)
        {
        }
        else
        {

#line 616
            break;
        }

#line 616
        (*r_1)[k_0] = o_0[k_0];

#line 616
        k_0 = k_0 + 1U;

#line 616
    }
    return;
}


void dftR_0(array<float2, int(64)> thread* r_2)
{

#line 628
    dft64_0(r_2);

    return;
}


#line 325
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S19 = max(TB_0, 1U);

#line 327
    uint j_1 = d_2 / _S19;

#line 327
    uint m_0 = d_2 % _S19;

#line 327
    uint _S20;
    if(TB_0 <= 64U)
    {

#line 328
        _S20 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 328
    }
    else
    {

#line 328
        _S20 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 328
    }

#line 328
    return _S20;
}


#line 312
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 312
    uint _S21 = 2U * i_1;

#line 312
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S21] = (as_type<uint>((v_0.x)));

#line 312
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S21 + 1U] = (as_type<uint>((v_0.y)));

#line 312
    return;
}


#line 313
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_2)
{

#line 313
    uint _S22 = 2U * i_2;

#line 313
    return float2((as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S22]))), (as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S22 + 1U]))));
}


#line 725
void exchange_0(array<float2, int(64)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_3)
{

#line 726
    uint j_2;

#line 737
    thread array<float2, int(64)> out_0;

#line 737
    uint z_1 = 0U;
    for(;;)
    {

#line 738
        if(z_1 < 64U)
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
    uint _S23 = p0_0 & lenMask_0;

#line 744
    uint _S24 = _S23 >> lgSpan_0;

#line 744
    uint _S25 = _S24 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S23 & spanMask_0);

#line 744
    uint c_2 = 0U;

    for(;;)
    {

#line 746
        if(c_2 < 8U)
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
        j_2 = 0U;
        for(;;)
        {

#line 748
            if(j_2 < 8U)
            {
            }
            else
            {

#line 748
                break;
            }

#line 748
            stgPut_0(j_2 * 1024U + kernelContext_3->_tid_0, (*r_3)[c_2 * 8U + j_2], kernelContext_3);

#line 748
            j_2 = j_2 + 1U;

#line 748
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 749
        uint d_3 = 0U;
        for(;;)
        {

#line 750
            if(d_3 < 64U)
            {
            }
            else
            {

#line 750
                break;
            }

#line 751
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S26 = pz_0 & lenMask_0;

#line 752
            uint iz_0 = _S26 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S26 & spanMask_0);
            uint i_3 = _S24 + iz_0;
            uint _S27 = c_2 * 8U;

#line 755
            bool _S28;

#line 755
            if(i_3 >= _S27)
            {

#line 755
                _S28 = i_3 < ((c_2 + 1U) * 8U);

#line 755
            }
            else
            {

#line 755
                _S28 = false;

#line 755
            }

#line 755
            if(_S28)
            {

#line 755
                float2 _S29 = stgGet_0(_S25 + az_0 - _S27 * 1024U, kernelContext_3);
                out_0[d_3] = _S29;

#line 755
            }

#line 750
            d_3 = d_3 + 1U;

#line 750
        }

#line 746
        c_2 = c_2 + 1U;

#line 746
    }

#line 746
    j_2 = 0U;

#line 759
    for(;;)
    {

#line 759
        if(j_2 < 64U)
        {
        }
        else
        {

#line 759
            break;
        }

#line 759
        (*r_3)[j_2] = out_0[j_2];

#line 759
        j_2 = j_2 + 1U;

#line 759
    }
    return;
}


#line 561
void dft16at_0(array<float2, int(64)> thread* r_4, uint o_1)
{



    thread array<float2, int(16)> b_5;

#line 566
    uint i_4 = 0U;
    for(;;)
    {

#line 567
        if(i_4 < 16U)
        {
        }
        else
        {

#line 567
            break;
        }

#line 567
        b_5[i_4] = (*r_4)[o_1 + i_4];

#line 567
        i_4 = i_4 + 1U;

#line 567
    }
    dft16_0(&b_5);

#line 568
    i_4 = 0U;
    for(;;)
    {

#line 569
        if(i_4 < 16U)
        {
        }
        else
        {

#line 569
            break;
        }

#line 569
        (*r_4)[o_1 + i_4] = b_5[i_4];

#line 569
        i_4 = i_4 + 1U;

#line 569
    }

    return;
}


#line 639
void innermost_0(array<float2, int(64)> thread* r_5)
{

#line 639
    uint b_6 = 0U;

#line 644
    for(;;)
    {

#line 644
        if(b_6 < 4U)
        {
        }
        else
        {

#line 644
            break;
        }

#line 644
        dft16at_0(r_5, b_6 * 16U);

#line 644
        b_6 = b_6 + 1U;

#line 644
    }

#line 651
    return;
}


#line 827
void transform_0(array<float2, int(64)> thread* r_6, uint tid_0, KernelContext_0 thread* kernelContext_4)
{

#line 827
    uint _S30;

#line 827
    uint k2_1;

#line 827
    float cr_0;

#line 827
    float ci_0;

#line 827
    uint _S31;

#line 827
    for(;;)
    {

#line 827
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S30 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(65536U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;

#line 19
                dftR_0(r_6);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 6.5536e+04f);
                float _S32 = tw_0.x;

#line 40
                float _S33 = tw_0.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 64U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_6)[k2_1] = cmul_0((*r_6)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S32 - ci_0 * _S33;
                    float _S34 = cr_0 * _S33 + ci_0 * _S32;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S34;

#line 42
                }

#line 50
                uint per_2 = 64U / max(1024U, 1U);
                uint _S35 = max(16U, 1U);

#line 51
                _S31 = _S35;
                uint blk2_2 = tid_0 / _S35;

#line 52
                uint lane2_2 = tid_0 % _S35;

#line 52
                exchange_0(r_6, lgLn_0, lgTB_0, 1024U, 65536U, blk_2, lane_2, per_2, _S35, 1024U, blk2_2, lane2_2, kernelContext_4);

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

#line 19
                dftR_0(r_6);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 1024.0f);
                float _S36 = tw_1.x;

#line 40
                float _S37 = tw_1.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 64U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_6)[k2_1] = cmul_0((*r_6)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S36 - ci_0 * _S37;
                    float _S38 = cr_0 * _S37 + ci_0 * _S36;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S38;

#line 42
                }

#line 50
                uint per_3 = 64U / _S31;
                uint _S39 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S39;

#line 52
                uint lane2_3 = tid_0 % _S39;

#line 52
                exchange_0(r_6, _S30, lgTB_1, 16U, 1024U, blk_3, lane_3, per_3, _S39, 16U, blk2_3, lane2_3, kernelContext_4);

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
    innermost_0(r_6);

#line 830 "mm_65536_refineListed.slang"
    return;
}


#line 784
uint lgOf_0(uint i_5)
{

#line 784
    uint _S40;

#line 784
    if(i_5 < 2U)
    {

#line 784
        _S40 = 6U;

#line 784
    }
    else
    {

#line 784
        if(i_5 == 2U)
        {

#line 784
            _S40 = 4U;

#line 784
        }
        else
        {

#line 784
            _S40 = 1U;

#line 784
        }

#line 784
    }

#line 784
    return _S40;
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


#line 844
void filterPairOut_0(uint pair_0, uint opair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{


    uint b_7;

#line 871
    kernelContext_5->_tid_0 = tid_1;
    uint _S41 = pair_0 / ntmpl_1;

#line 872
    uint _S42 = pair_0 % ntmpl_1;

#line 877
    thread array<float2, int(64)> r_7;

#line 877
    uint n2_0 = 0U;

#line 888
    for(;;)
    {

#line 888
        if(n2_0 < 64U)
        {
        }
        else
        {

#line 888
            break;
        }

#line 889
        uint idx_0 = tid_1 + 1024U * n2_0;

#line 63 "twiddle.slang"
        uint _S43 = mfDataStrideFlag_0();

#line 177 "mm_65536_refineListed.slang"
        if(_S43 != 0U)
        {

#line 63 "twiddle.slang"
            uint _S44 = mfDataStrideFlag_0();

#line 63
            b_7 = _S44;

#line 177 "mm_65536_refineListed.slang"
        }
        else
        {

#line 177
            b_7 = 65536U;

#line 177
        }

#line 890
        r_7[n2_0] = cmulConj_0(cload_0(data_0, _S41 * b_7 + idx_0), cload_0(tmpl_0, _S42 * 65536U + idx_0));

#line 888
        n2_0 = n2_0 + 1U;

#line 888
    }

#line 888
    transform_0(&r_7, tid_1, kernelContext_5);

#line 907
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 907
    b_7 = tid_1;

#line 1019
    for(;;)
    {

#line 1019
        if(b_7 < nbins_1)
        {
        }
        else
        {

#line 1019
            break;
        }

#line 1019
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + b_7] = thrBits_1;

#line 1019
        b_7 = b_7 + 1024U;

#line 1019
    }
    bool _S45 = nbins_1 == 1U;

#line 1020
    bool live_0;

#line 1020
    if(_S45)
    {

#line 1020
        live_0 = tid_1 == 0U;

#line 1020
    }
    else
    {

#line 1020
        live_0 = false;

#line 1020
    }

#line 1020
    if(live_0)
    {

#line 1020
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 1020
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1079
    thread array<uint, int(64)> myMag_0;
    thread array<uint, int(64)> myBin_0;

#line 1080
    uint i_6 = 0U;



    for(;;)
    {

#line 1084
        if(i_6 < 64U)
        {
        }
        else
        {

#line 1084
            break;
        }

#line 1085
        uint idx_1 = slotToIndex_0(tid_1 * 64U + i_6);
        if(idx_1 >= winStart_2)
        {

#line 1086
            live_0 = idx_1 < winEnd_2;

#line 1086
        }
        else
        {

#line 1086
            live_0 = false;

#line 1086
        }



        float _rx_0 = r_7[i_6].x;

#line 1090
        float _ry_0 = r_7[i_6].y;
        if(live_0)
        {

#line 1091
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1091
        }
        else
        {

#line 1091
            n2_0 = 0U;

#line 1091
        }

#line 1091
        myMag_0[i_6] = n2_0;

#line 1099
        uint off_0 = idx_1 - winStart_2 + kernelContext_5->_binPhase_0;

#line 1106
        if(live_0)
        {

#line 1106
            if(binShift_1 >= int(0))
            {

#line 1106
                b_7 = off_0 >> uint(binShift_1);

#line 1106
            }
            else
            {

#line 1106
                uint _S46 = off_0 / binsize_1;

#line 1106
                b_7 = _S46;

#line 1106
            }

#line 1106
        }
        else
        {

#line 1106
            b_7 = 0U;

#line 1106
        }

#line 1106
        myBin_0[i_6] = b_7;

#line 1106
        bool _S47;



        if(nbins_1 > 1U)
        {

#line 1110
            _S47 = (myMag_0[i_6]) > thrBits_1;

#line 1110
        }
        else
        {

#line 1110
            _S47 = false;

#line 1110
        }

#line 1110
        if(_S47)
        {

#line 1111
            uint _S48 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + myBin_0[i_6]])), myMag_0[i_6], memory_order_relaxed);

#line 1110
        }

#line 1084
        i_6 = i_6 + 1U;

#line 1084
    }

#line 1084
    uint winner_0;

#line 1134
    if(_S45)
    {

#line 1134
        winner_0 = thrBits_1;

#line 1134
        i_6 = 0U;


        for(;;)
        {

#line 1137
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1137
                break;
            }

#line 1137
            uint _S49 = max(winner_0, myMag_0[i_6]);

#line 1137
            uint i_7 = i_6 + 1U;

#line 1137
            winner_0 = _S49;

#line 1137
            i_6 = i_7;

#line 1137
        }

        uint wm_0 = simd_max(winner_0);
        bool _S50 = simd_is_first();

#line 1140
        if(_S50)
        {

#line 1140
            live_0 = wm_0 > thrBits_1;

#line 1140
        }
        else
        {

#line 1140
            live_0 = false;

#line 1140
        }

#line 1140
        if(live_0)
        {

#line 1140
            uint _S51 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1140
        }

#line 1134
    }

#line 1155
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1162
    if(_S45)
    {

#line 1162
        winner_0 = 4294967295U;

#line 1162
        i_6 = 0U;


        for(;;)
        {

#line 1165
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1165
                break;
            }

#line 1166
            if((myMag_0[i_6]) > thrBits_1)
            {

#line 1166
                live_0 = (myMag_0[i_6]) == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1166
            }
            else
            {

#line 1166
                live_0 = false;

#line 1166
            }

#line 1166
            if(live_0)
            {

#line 1166
                winner_0 = min(winner_0, tid_1 * 64U + i_6);

#line 1166
            }

#line 1165
            i_6 = i_6 + 1U;

#line 1165
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S52 = simd_is_first();

#line 1170
        if(_S52)
        {

#line 1170
            live_0 = waveWinner_0 != 4294967295U;

#line 1170
        }
        else
        {

#line 1170
            live_0 = false;

#line 1170
        }

#line 1170
        if(live_0)
        {

#line 1171
            uint _S53 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1170
        }

#line 1175
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1175
        i_6 = 0U;
        for(;;)
        {

#line 1176
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1176
                break;
            }

#line 1177
            uint _S54 = tid_1 * 64U + i_6;

#line 1177
            if(_S54 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])
            {

#line 1178
                *(peakIdx_0+opair_0) = int(slotToIndex_0(_S54));

#line 1178
                *(peakVal_0+opair_0) = packed_float2(float2(r_7[i_6].x, r_7[i_6].y)) ;

#line 1177
            }

#line 1176
            i_6 = i_6 + 1U;

#line 1176
        }

#line 1182
        if(tid_1 == 0U)
        {

#line 1182
            live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U]) == 4294967295U;

#line 1182
        }
        else
        {

#line 1182
            live_0 = false;

#line 1182
        }

#line 1182
        if(live_0)
        {

#line 1183
            *(peakIdx_0+opair_0) = int(-1);

#line 1183
            *(peakVal_0+opair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1182
        }

#line 1162
    }
    else
    {

#line 1162
        i_6 = 0U;

#line 1191
        for(;;)
        {

#line 1191
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1191
                break;
            }

#line 1192
            if((myMag_0[i_6]) > thrBits_1)
            {

#line 1192
                live_0 = (myMag_0[i_6]) == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + myBin_0[i_6]];

#line 1192
            }
            else
            {

#line 1192
                live_0 = false;

#line 1192
            }

#line 1192
            myMag_0[i_6] = uint(live_0);

#line 1191
            i_6 = i_6 + 1U;

#line 1191
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1194
        b_7 = tid_1;
        for(;;)
        {

#line 1195
            if(b_7 < nbins_1)
            {
            }
            else
            {

#line 1195
                break;
            }

#line 1195
            (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + b_7] = 4294967295U;

#line 1195
            b_7 = b_7 + 1024U;

#line 1195
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1196
        i_6 = 0U;
        for(;;)
        {

#line 1197
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1197
                break;
            }

#line 1198
            if((myMag_0[i_6]) != 0U)
            {

#line 1198
                uint _S55 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + myBin_0[i_6]])), tid_1 * 64U + i_6, memory_order_relaxed);

#line 1198
            }

#line 1197
            i_6 = i_6 + 1U;

#line 1197
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1199
        i_6 = 0U;
        for(;;)
        {

#line 1200
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1200
                break;
            }

#line 1201
            if((myMag_0[i_6]) != 0U)
            {

#line 1201
                live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + myBin_0[i_6]]) == (tid_1 * 64U + i_6);

#line 1201
            }
            else
            {

#line 1201
                live_0 = false;

#line 1201
            }

#line 1201
            if(live_0)
            {

#line 1202
                uint o_2 = opair_0 * nbins_1 + myBin_0[i_6];
                *(peakIdx_0+o_2) = int(slotToIndex_0(tid_1 * 64U + i_6));

#line 1203
                *(peakVal_0+o_2) = packed_float2(float2(r_7[i_6].x, r_7[i_6].y)) ;

#line 1201
            }

#line 1200
            i_6 = i_6 + 1U;

#line 1200
        }

#line 1200
        b_7 = tid_1;

#line 1207
        for(;;)
        {

#line 1207
            if(b_7 < nbins_1)
            {
            }
            else
            {

#line 1207
                break;
            }

#line 1208
            if(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + b_7]) == 4294967295U)
            {

#line 1209
                uint _S56 = opair_0 * nbins_1 + b_7;

#line 1209
                *(peakIdx_0+_S56) = int(-1);

#line 1209
                *(peakVal_0+_S56) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1208
            }

#line 1207
            b_7 = b_7 + 1024U;

#line 1207
        }

#line 1162
    }

#line 1217
    return;
}

void filterPair_0(uint pair_1, uint tid_2, packed_float2 device* data_1, packed_float2 device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_2, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{


    filterPairOut_0(pair_1, pair_1, tid_2, data_1, tmpl_1, peakIdx_1, peakVal_1, ntmpl_2, winStart_3, winEnd_3, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);



    return;
}


#line 2091
[[kernel]] void refineListedBounded(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]], uint device* entryPointParams_rowWin_1 [[buffer(7)]])
{

#line 2091
    thread KernelContext_0 kernelContext_7;

#line 2091
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 2091
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2091
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2091
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2091
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2091
    (&kernelContext_7)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2091
    (&kernelContext_7)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2091
    (&kernelContext_7)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 2091
    threadgroup array<uint, int(16384)> stg_1;

#line 2091
    (&kernelContext_7)->stg_0 = &stg_1;

#line 2091
    (&kernelContext_7)->_binPhase_0 = 0U;

#line 2101
    uint _S57 = entryPointParams_count_1[int(0)];

#line 2101
    uint i_8 = gid_0.x;
    for(;;)
    {

#line 2102
        if(i_8 < _S57)
        {
        }
        else
        {

#line 2102
            break;
        }

#line 2103
        (&kernelContext_7)->_stgBase_0 = 0U;
        uint pair_2 = (&kernelContext_7)->entryPointParams_survivors_0[i_8];

#line 2104
        thread uint ws_0 = (&kernelContext_7)->entryPointParams_0->winStart_0;

#line 2104
        thread uint we_0 = (&kernelContext_7)->entryPointParams_0->winEnd_0;
        uint _S58 = pair_2 / (&kernelContext_7)->entryPointParams_0->ntmpl_0;

#line 2105
        rowWindow_0(_S58, &ws_0, &we_0, (&kernelContext_7)->entryPointParams_rowWin_0, &kernelContext_7);

#line 2105
        filterPair_0(pair_2, lid_0.x, (&kernelContext_7)->entryPointParams_data_0, (&kernelContext_7)->entryPointParams_tmpl_0, (&kernelContext_7)->entryPointParams_peakIdx_0, (&kernelContext_7)->entryPointParams_peakVal_0, (&kernelContext_7)->entryPointParams_0->ntmpl_0, ws_0, we_0, (&kernelContext_7)->entryPointParams_0->binsize_0, (&kernelContext_7)->entryPointParams_0->binShift_0, (&kernelContext_7)->entryPointParams_0->nbins_0, (&kernelContext_7)->entryPointParams_0->thrBits_0, &kernelContext_7);


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2102
        i_8 = i_8 + (&kernelContext_7)->entryPointParams_0->gridSize_0;

#line 2102
    }

#line 2110
    return;
}
