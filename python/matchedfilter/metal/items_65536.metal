#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
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


#line 58 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S2 = ((MF_DATA_STRIDE));

#line 61
    return _S2;
}


#line 174 "mm_65536_refineItems.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 174
    return float2(*(b_0+i_0)) ;
}


#line 324
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 324
    float _S3 = a_0.x;

#line 324
    float _S4 = b_1.x;

#line 324
    float _S5 = a_0.y;

#line 324
    float _S6 = b_1.y;

#line 324
    return float2(_S3 * _S4 + _S5 * _S6, _S5 * _S4 - _S3 * _S6);
}


#line 500
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 502
    float2 t1_0 = *a_1 - *c_0;

#line 502
    float2 t2_0 = *b_2 + *d_0;

#line 502
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 504
    *b_2 = t1_0 + j3_0;

#line 504
    *c_0 = t0_0 - t2_0;

#line 504
    *d_0 = t1_0 - j3_0;
    return;
}


#line 74 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S7 = ((MF_ACCURATE_TRIG));

#line 77
    return _S7;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S8 = mfAccurateTrigFlag_0();

#line 103
    if(_S8 == 0U)
    {

#line 104
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S9 = float(quadrant_0);
    float x_0 = angle_0 - _S9 * 1.57079625129699707f - _S9 * 7.54978941586159635e-08f;
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


#line 323 "mm_65536_refineItems.slang"
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
            float2 _S15 = mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f);

#line 611
            b_4[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], _S15);

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
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S16 = max(TB_0, 1U);

#line 327
    uint j_1 = d_1 / _S16;

#line 327
    uint m_0 = d_1 % _S16;

#line 327
    uint _S17;
    if(TB_0 <= 64U)
    {

#line 328
        _S17 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 328
    }
    else
    {

#line 328
        _S17 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 328
    }

#line 328
    return _S17;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
    uint binsize_0;
    int binShift_0;
    uint nbins_0;
    uint thrBits_0;
    uint gridSize_0;
};


#line 312 "mm_65536_refineItems.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_items_0;
    uint device* entryPointParams_count_0;
    uint _stgBase_0;
    uint _binPhase_0;
    uint _tid_0;
    array<uint, int(16384)> threadgroup* stg_0;
};


#line 312
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 312
    uint _S18 = 2U * i_1;

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S18] = (as_type<uint>((v_0.x)));

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S18 + 1U] = (as_type<uint>((v_0.y)));

#line 312
    return;
}


#line 313
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 313
    uint _S19 = 2U * i_2;

#line 313
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S19]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S19 + 1U]))));
}


#line 725
void exchange_0(array<float2, int(64)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
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
    uint _S20 = p0_0 & lenMask_0;

#line 744
    uint _S21 = _S20 >> lgSpan_0;

#line 744
    uint _S22 = _S21 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S20 & spanMask_0);

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
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_2 * 8U + j_2], kernelContext_2);

#line 748
            j_2 = j_2 + 1U;

#line 748
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 749
        uint d_2 = 0U;
        for(;;)
        {

#line 750
            if(d_2 < 64U)
            {
            }
            else
            {

#line 750
                break;
            }

#line 751
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S23 = pz_0 & lenMask_0;

#line 752
            uint iz_0 = _S23 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S23 & spanMask_0);
            uint i_3 = _S21 + iz_0;
            uint _S24 = c_2 * 8U;

#line 755
            bool _S25;

#line 755
            if(i_3 >= _S24)
            {

#line 755
                _S25 = i_3 < ((c_2 + 1U) * 8U);

#line 755
            }
            else
            {

#line 755
                _S25 = false;

#line 755
            }

#line 755
            if(_S25)
            {

#line 755
                float2 _S26 = stgGet_0(_S22 + az_0 - _S24 * 1024U, kernelContext_2);
                out_0[d_2] = _S26;

#line 755
            }

#line 750
            d_2 = d_2 + 1U;

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


#line 830
void transform_0(array<float2, int(64)> thread* r_6, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 830
    uint _S27;

#line 830
    uint k2_1;

#line 830
    float cr_0;

#line 830
    float ci_0;

#line 830
    uint _S28;

#line 830
    for(;;)
    {

#line 830
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S27 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(65536U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;

#line 19
                dftR_0(r_6);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 6.5536e+04f);
                float _S29 = tw_0.x;

#line 40
                float _S30 = tw_0.y;

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
                    float nr_0 = cr_0 * _S29 - ci_0 * _S30;
                    float _S31 = cr_0 * _S30 + ci_0 * _S29;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S31;

#line 42
                }

#line 50
                uint per_2 = 64U / max(1024U, 1U);
                uint _S32 = max(16U, 1U);

#line 51
                _S28 = _S32;
                uint blk2_2 = tid_0 / _S32;

#line 52
                uint lane2_2 = tid_0 % _S32;

#line 52
                exchange_0(r_6, lgLn_0, lgTB_0, 1024U, 65536U, blk_2, lane_2, per_2, _S32, 1024U, blk2_2, lane2_2, kernelContext_3);

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
                float _S33 = tw_1.x;

#line 40
                float _S34 = tw_1.y;

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
                    float nr_1 = cr_0 * _S33 - ci_0 * _S34;
                    float _S35 = cr_0 * _S34 + ci_0 * _S33;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S35;

#line 42
                }

#line 50
                uint per_3 = 64U / _S28;
                uint _S36 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S36;

#line 52
                uint lane2_3 = tid_0 % _S36;

#line 52
                exchange_0(r_6, _S27, lgTB_1, 16U, 1024U, blk_3, lane_3, per_3, _S36, 16U, blk2_3, lane2_3, kernelContext_3);

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

#line 833 "mm_65536_refineItems.slang"
    return;
}


#line 784
uint lgOf_0(uint i_5)
{

#line 784
    uint _S37;

#line 784
    if(i_5 < 2U)
    {

#line 784
        _S37 = 6U;

#line 784
    }
    else
    {

#line 784
        if(i_5 == 2U)
        {

#line 784
            _S37 = 4U;

#line 784
        }
        else
        {

#line 784
            _S37 = 1U;

#line 784
        }

#line 784
    }

#line 784
    return _S37;
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
void filterPairOut_0(uint pair_0, uint opair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_0, uint winEnd_0, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{


    uint b_7;

#line 874
    kernelContext_4->_tid_0 = tid_1;
    uint _S38 = pair_0 / ntmpl_1;

#line 875
    uint _S39 = pair_0 % ntmpl_1;

#line 880
    thread array<float2, int(64)> r_7;

#line 880
    uint n2_0 = 0U;

#line 891
    for(;;)
    {

#line 891
        if(n2_0 < 64U)
        {
        }
        else
        {

#line 891
            break;
        }

#line 892
        uint idx_0 = tid_1 + 1024U * n2_0;

#line 63 "twiddle.slang"
        uint _S40 = mfDataStrideFlag_0();

#line 177 "mm_65536_refineItems.slang"
        if(_S40 != 0U)
        {

#line 63 "twiddle.slang"
            uint _S41 = mfDataStrideFlag_0();

#line 63
            b_7 = _S41;

#line 177 "mm_65536_refineItems.slang"
        }
        else
        {

#line 177
            b_7 = 65536U;

#line 177
        }

#line 893
        r_7[n2_0] = cmulConj_0(cload_0(data_0, _S38 * b_7 + idx_0), cload_0(tmpl_0, _S39 * 65536U + idx_0));

#line 891
        n2_0 = n2_0 + 1U;

#line 891
    }

#line 891
    transform_0(&r_7, tid_1, kernelContext_4);

#line 910
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 910
    b_7 = tid_1;

#line 1022
    for(;;)
    {

#line 1022
        if(b_7 < nbins_1)
        {
        }
        else
        {

#line 1022
            break;
        }

#line 1022
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_7] = thrBits_1;

#line 1022
        b_7 = b_7 + 1024U;

#line 1022
    }
    bool _S42 = nbins_1 == 1U;

#line 1023
    bool live_0;

#line 1023
    if(_S42)
    {

#line 1023
        live_0 = tid_1 == 0U;

#line 1023
    }
    else
    {

#line 1023
        live_0 = false;

#line 1023
    }

#line 1023
    if(live_0)
    {

#line 1023
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 1023
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1084
    thread array<uint, int(64)> myMag_0;
    thread array<uint, int(64)> myBin_0;

#line 1085
    uint i_6 = 0U;



    for(;;)
    {

#line 1089
        if(i_6 < 64U)
        {
        }
        else
        {

#line 1089
            break;
        }

#line 1090
        uint idx_1 = slotToIndex_0(tid_1 * 64U + i_6);
        if(idx_1 >= winStart_0)
        {

#line 1091
            live_0 = idx_1 < winEnd_0;

#line 1091
        }
        else
        {

#line 1091
            live_0 = false;

#line 1091
        }



        float _rx_0 = r_7[i_6].x;

#line 1095
        float _ry_0 = r_7[i_6].y;

#line 1100
        if(live_0)
        {

#line 1100
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1100
        }
        else
        {

#line 1100
            n2_0 = 0U;

#line 1100
        }

#line 1100
        myMag_0[i_6] = n2_0;

#line 1109
        uint off_0 = idx_1 - winStart_0 + kernelContext_4->_binPhase_0;

#line 1116
        if(live_0)
        {

#line 1116
            if(binShift_1 >= int(0))
            {

#line 1116
                b_7 = off_0 >> uint(binShift_1);

#line 1116
            }
            else
            {

#line 1116
                uint _S43 = off_0 / binsize_1;

#line 1116
                b_7 = _S43;

#line 1116
            }

#line 1116
        }
        else
        {

#line 1116
            b_7 = 0U;

#line 1116
        }

#line 1116
        myBin_0[i_6] = b_7;

#line 1116
        bool _S44;



        if(nbins_1 > 1U)
        {

#line 1120
            _S44 = (myMag_0[i_6]) > thrBits_1;

#line 1120
        }
        else
        {

#line 1120
            _S44 = false;

#line 1120
        }

#line 1120
        if(_S44)
        {

#line 1121
            uint _S45 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_6]])), myMag_0[i_6], memory_order_relaxed);

#line 1120
        }

#line 1089
        i_6 = i_6 + 1U;

#line 1089
    }

#line 1089
    uint winner_0;

#line 1144
    if(_S42)
    {

#line 1144
        winner_0 = thrBits_1;

#line 1144
        i_6 = 0U;


        for(;;)
        {

#line 1147
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1147
                break;
            }

#line 1147
            uint _S46 = max(winner_0, myMag_0[i_6]);

#line 1147
            uint i_7 = i_6 + 1U;

#line 1147
            winner_0 = _S46;

#line 1147
            i_6 = i_7;

#line 1147
        }

        uint wm_0 = simd_max(winner_0);
        bool _S47 = simd_is_first();

#line 1150
        if(_S47)
        {

#line 1150
            live_0 = wm_0 > thrBits_1;

#line 1150
        }
        else
        {

#line 1150
            live_0 = false;

#line 1150
        }

#line 1150
        if(live_0)
        {

#line 1150
            uint _S48 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1150
        }

#line 1144
    }

#line 1165
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1172
    if(_S42)
    {

#line 1172
        winner_0 = 4294967295U;

#line 1172
        i_6 = 0U;


        for(;;)
        {

#line 1175
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1175
                break;
            }

#line 1176
            if((myMag_0[i_6]) > thrBits_1)
            {

#line 1176
                live_0 = (myMag_0[i_6]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 1176
            }
            else
            {

#line 1176
                live_0 = false;

#line 1176
            }

#line 1176
            if(live_0)
            {

#line 1176
                winner_0 = min(winner_0, tid_1 * 64U + i_6);

#line 1176
            }

#line 1175
            i_6 = i_6 + 1U;

#line 1175
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S49 = simd_is_first();

#line 1180
        if(_S49)
        {

#line 1180
            live_0 = waveWinner_0 != 4294967295U;

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

#line 1181
            uint _S50 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1180
        }

#line 1185
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1185
        i_6 = 0U;
        for(;;)
        {

#line 1186
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1186
                break;
            }

#line 1187
            uint _S51 = tid_1 * 64U + i_6;

#line 1187
            if(_S51 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 1188
                *(peakIdx_0+opair_0) = int(slotToIndex_0(_S51));

#line 1188
                *(peakVal_0+opair_0) = packed_float2(float2(r_7[i_6].x, r_7[i_6].y)) ;

#line 1187
            }

#line 1186
            i_6 = i_6 + 1U;

#line 1186
        }

#line 1198
        if(tid_1 == 0U)
        {

#line 1198
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1198
        }
        else
        {

#line 1198
            live_0 = false;

#line 1198
        }

#line 1198
        if(live_0)
        {

#line 1199
            *(peakIdx_0+opair_0) = int(-1);

#line 1199
            *(peakVal_0+opair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1198
        }

#line 1172
    }
    else
    {

#line 1172
        i_6 = 0U;

#line 1207
        for(;;)
        {

#line 1207
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1207
                break;
            }

#line 1208
            if((myMag_0[i_6]) > thrBits_1)
            {

#line 1208
                live_0 = (myMag_0[i_6]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_6]];

#line 1208
            }
            else
            {

#line 1208
                live_0 = false;

#line 1208
            }

#line 1208
            myMag_0[i_6] = uint(live_0);

#line 1207
            i_6 = i_6 + 1U;

#line 1207
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1210
        b_7 = tid_1;
        for(;;)
        {

#line 1211
            if(b_7 < nbins_1)
            {
            }
            else
            {

#line 1211
                break;
            }

#line 1211
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_7] = 4294967295U;

#line 1211
            b_7 = b_7 + 1024U;

#line 1211
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1212
        i_6 = 0U;
        for(;;)
        {

#line 1213
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1213
                break;
            }

#line 1214
            if((myMag_0[i_6]) != 0U)
            {

#line 1214
                uint _S52 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_6]])), tid_1 * 64U + i_6, memory_order_relaxed);

#line 1214
            }

#line 1213
            i_6 = i_6 + 1U;

#line 1213
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1215
        i_6 = 0U;
        for(;;)
        {

#line 1216
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1216
                break;
            }

#line 1217
            if((myMag_0[i_6]) != 0U)
            {

#line 1217
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_6]]) == (tid_1 * 64U + i_6);

#line 1217
            }
            else
            {

#line 1217
                live_0 = false;

#line 1217
            }

#line 1217
            if(live_0)
            {

#line 1218
                uint o_2 = opair_0 * nbins_1 + myBin_0[i_6];
                *(peakIdx_0+o_2) = int(slotToIndex_0(tid_1 * 64U + i_6));

#line 1219
                *(peakVal_0+o_2) = packed_float2(float2(r_7[i_6].x, r_7[i_6].y)) ;

#line 1217
            }

#line 1216
            i_6 = i_6 + 1U;

#line 1216
        }

#line 1216
        b_7 = tid_1;

#line 1223
        for(;;)
        {

#line 1223
            if(b_7 < nbins_1)
            {
            }
            else
            {

#line 1223
                break;
            }

#line 1224
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_7]) == 4294967295U)
            {

#line 1225
                uint _S53 = opair_0 * nbins_1 + b_7;

#line 1225
                *(peakIdx_0+_S53) = int(-1);

#line 1225
                *(peakVal_0+_S53) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1224
            }

#line 1223
            b_7 = b_7 + 1024U;

#line 1223
        }

#line 1172
    }

#line 1233
    return;
}


#line 2146
[[kernel]] void refineItems(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_items_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]])
{

#line 2146
    thread KernelContext_0 kernelContext_5;

#line 2146
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 2146
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2146
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2146
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2146
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2146
    (&kernelContext_5)->entryPointParams_items_0 = entryPointParams_items_1;

#line 2146
    (&kernelContext_5)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2146
    threadgroup array<uint, int(16384)> stg_1;

#line 2146
    (&kernelContext_5)->stg_0 = &stg_1;

#line 2146
    (&kernelContext_5)->_binPhase_0 = 0U;

#line 2155
    uint _S54 = entryPointParams_count_1[int(0)];

#line 2155
    uint i_8 = gid_0.x;
    for(;;)
    {

#line 2156
        if(i_8 < _S54)
        {
        }
        else
        {

#line 2156
            break;
        }

#line 2157
        (&kernelContext_5)->_stgBase_0 = 0U;
        uint _S55 = 6U * i_8;

#line 2158
        uint d_3 = (&kernelContext_5)->entryPointParams_items_0[_S55];

#line 2158
        uint t_6 = (&kernelContext_5)->entryPointParams_items_0[_S55 + 1U];
        (&kernelContext_5)->_binPhase_0 = (&kernelContext_5)->entryPointParams_items_0[_S55 + 5U];

#line 2159
        filterPairOut_0(d_3 * (&kernelContext_5)->entryPointParams_0->ntmpl_0 + t_6, (&kernelContext_5)->entryPointParams_items_0[_S55 + 4U], lid_0.x, (&kernelContext_5)->entryPointParams_data_0, (&kernelContext_5)->entryPointParams_tmpl_0, (&kernelContext_5)->entryPointParams_peakIdx_0, (&kernelContext_5)->entryPointParams_peakVal_0, (&kernelContext_5)->entryPointParams_0->ntmpl_0, (&kernelContext_5)->entryPointParams_items_0[_S55 + 2U], (&kernelContext_5)->entryPointParams_items_0[_S55 + 3U], (&kernelContext_5)->entryPointParams_0->binsize_0, (&kernelContext_5)->entryPointParams_0->binShift_0, (&kernelContext_5)->entryPointParams_0->nbins_0, (&kernelContext_5)->entryPointParams_0->thrBits_0, &kernelContext_5);



        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2156
        i_8 = i_8 + (&kernelContext_5)->entryPointParams_0->gridSize_0;

#line 2156
    }

#line 2165
    return;
}
