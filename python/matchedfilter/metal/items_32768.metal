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


#line 72 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S2 = ((MF_DATA_STRIDE));

#line 75
    return _S2;
}


#line 169 "mm_32768_refineItems.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 169
    return float2(*(b_0+i_0)) ;
}


#line 300
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 300
    float _S3 = a_0.x;

#line 300
    float _S4 = b_1.x;

#line 300
    float _S5 = a_0.y;

#line 300
    float _S6 = b_1.y;

#line 300
    return float2(_S3 * _S4 + _S5 * _S6, _S5 * _S4 - _S3 * _S6);
}


#line 88 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S7 = ((MF_ACCURATE_TRIG));

#line 91
    return _S7;
}


#line 127
float2 mfTwiddle_0(float angle_0)
{

#line 93
    uint _S8 = mfAccurateTrigFlag_0();

#line 129
    if(_S8 == 0U)
    {

#line 130
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S9 = float(quadrant_0);
    float x_0 = angle_0 - _S9 * 1.57079625129699707f - _S9 * 7.54978941586159635e-08f;
    float z_0 = x_0 * x_0;
    float c_0 = 1.0f + z_0 * (-0.5f + z_0 * (0.0416666679084301f + z_0 * (-0.00138888892251998f + z_0 * (0.00002480158764229f + z_0 * -2.75573199814971304e-07f))));

    float s_0 = x_0 * (1.0f + z_0 * (-0.1666666716337204f + z_0 * (0.00833333376795053f + z_0 * (-0.0001984127011383f + z_0 * (2.75573188446287531e-06f + z_0 * -2.50521079436794025e-08f)))));


    switch(quadrant_0 & int(3))
    {
    case int(1):
        {

#line 143
            return float2(- s_0, c_0);
        }
    case int(2):
        {

#line 144
            return float2(- c_0, - s_0);
        }
    case int(3):
        {

#line 145
            return float2(s_0, - c_0);
        }
    default:
        {

#line 146
            return float2(c_0, s_0);
        }
    }

#line 146
}


#line 299 "mm_32768_refineItems.slang"
float2 cmul_0(float2 a_1, float2 b_2)
{

#line 299
    float _S10 = a_1.x;

#line 299
    float _S11 = b_2.x;

#line 299
    float _S12 = a_1.y;

#line 299
    float _S13 = b_2.y;

#line 299
    return float2(_S10 * _S11 - _S12 * _S13, _S10 * _S13 + _S12 * _S11);
}


#line 505
void r4_0(float2 thread* a_2, float2 thread* b_3, float2 thread* c_1, float2 thread* d_0)
{
    float2 t0_0 = *a_2 + *c_1;

#line 507
    float2 t1_0 = *a_2 - *c_1;

#line 507
    float2 t2_0 = *b_3 + *d_0;

#line 507
    float2 t3_0 = *b_3 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_2 = t0_0 + t2_0;

#line 509
    *b_3 = t1_0 + j3_0;

#line 509
    *c_1 = t0_0 - t2_0;

#line 509
    *d_0 = t1_0 - j3_0;
    return;
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


#line 587
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 589
    thread array<float2, int(16)> v_0;

#line 589
    uint j_0 = 0U;
    for(;;)
    {

#line 590
        if(j_0 < 16U)
        {
        }
        else
        {

#line 590
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        float2 _S15 = (*r_1)[j_0] - (*r_1)[j_0 + 16U];

#line 594
        float2 _S16 = mfTwiddle_0(6.28318548202514648f * float(j_0) / 32.0f);

#line 594
        v_0[j_0] = cmul_0(_S15, _S16);

#line 590
        j_0 = j_0 + 1U;

#line 590
    }

#line 596
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 597
    uint k_0 = 0U;
    for(;;)
    {

#line 598
        if(k_0 < 16U)
        {
        }
        else
        {

#line 598
            break;
        }

#line 598
        uint _S17 = 2U * k_0;

#line 598
        (*r_1)[_S17] = u_0[k_0];

#line 598
        (*r_1)[_S17 + 1U] = v_0[k_0];

#line 598
        k_0 = k_0 + 1U;

#line 598
    }
    return;
}


#line 626
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 301
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S18 = max(TB_0, 1U);

#line 303
    uint j_1 = d_1 / _S18;

#line 303
    uint m_0 = d_1 % _S18;

#line 303
    uint _S19;
    if(TB_0 <= 32U)
    {

#line 304
        _S19 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 304
    }
    else
    {

#line 304
        _S19 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 304
    }

#line 304
    return _S19;
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


#line 288 "mm_32768_refineItems.slang"
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
    uint _tid_0;
    array<uint, int(16384)> threadgroup* stg_0;
};


#line 288
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 288
    uint _S20 = 2U * i_1;

#line 288
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S20] = (as_type<uint>((v_1.x)));

#line 288
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S20 + 1U] = (as_type<uint>((v_1.y)));

#line 288
    return;
}


#line 289
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 289
    uint _S21 = 2U * i_2;

#line 289
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S21]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S21 + 1U]))));
}


#line 730
void exchange_0(array<float2, int(32)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 731
    uint j_2;

#line 742
    thread array<float2, int(32)> out_0;

#line 742
    uint z_1 = 0U;
    for(;;)
    {

#line 743
        if(z_1 < 32U)
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
    uint _S22 = p0_0 & lenMask_0;

#line 749
    uint _S23 = _S22 >> lgSpan_0;

#line 749
    uint _S24 = _S23 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S22 & spanMask_0);

#line 749
    uint c_2 = 0U;

    for(;;)
    {

#line 751
        if(c_2 < 4U)
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
        j_2 = 0U;
        for(;;)
        {

#line 753
            if(j_2 < 8U)
            {
            }
            else
            {

#line 753
                break;
            }

#line 753
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_2 * 8U + j_2], kernelContext_2);

#line 753
            j_2 = j_2 + 1U;

#line 753
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 754
        uint d_2 = 0U;
        for(;;)
        {

#line 755
            if(d_2 < 32U)
            {
            }
            else
            {

#line 755
                break;
            }

#line 756
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S25 = pz_0 & lenMask_0;

#line 757
            uint iz_0 = _S25 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S25 & spanMask_0);
            uint i_3 = _S23 + iz_0;
            uint _S26 = c_2 * 8U;

#line 760
            bool _S27;

#line 760
            if(i_3 >= _S26)
            {

#line 760
                _S27 = i_3 < ((c_2 + 1U) * 8U);

#line 760
            }
            else
            {

#line 760
                _S27 = false;

#line 760
            }

#line 760
            if(_S27)
            {

#line 760
                float2 _S28 = stgGet_0(_S24 + az_0 - _S26 * 1024U, kernelContext_2);
                out_0[d_2] = _S28;

#line 760
            }

#line 755
            d_2 = d_2 + 1U;

#line 755
        }

#line 751
        c_2 = c_2 + 1U;

#line 751
    }

#line 751
    j_2 = 0U;

#line 764
    for(;;)
    {

#line 764
        if(j_2 < 32U)
        {
        }
        else
        {

#line 764
            break;
        }

#line 764
        (*r_3)[j_2] = out_0[j_2];

#line 764
        j_2 = j_2 + 1U;

#line 764
    }
    return;
}


#line 644
void innermost_0(array<float2, int(32)> thread* r_4)
{

    dft32_0(r_4);

#line 656
    return;
}


#line 832
void transform_0(array<float2, int(32)> thread* r_5, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 832
    uint _S29;

#line 832
    uint k2_1;

#line 832
    float cr_0;

#line 832
    float ci_0;

#line 832
    uint _S30;

#line 832
    for(;;)
    {

#line 832
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S29 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(32768U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;

#line 19
                dftR_0(r_5);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 32768.0f);
                float _S31 = tw_0.x;

#line 40
                float _S32 = tw_0.y;

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
                    float nr_0 = cr_0 * _S31 - ci_0 * _S32;
                    float _S33 = cr_0 * _S32 + ci_0 * _S31;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S33;

#line 42
                }

#line 50
                uint per_2 = 32U / max(1024U, 1U);
                uint _S34 = max(32U, 1U);

#line 51
                _S30 = _S34;
                uint blk2_2 = tid_0 / _S34;

#line 52
                uint lane2_2 = tid_0 % _S34;

#line 52
                exchange_0(r_5, lgLn_0, lgTB_0, 1024U, 32768U, blk_2, lane_2, per_2, _S34, 1024U, blk2_2, lane2_2, kernelContext_3);

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
                float _S35 = tw_1.x;

#line 40
                float _S36 = tw_1.y;

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
                    float nr_1 = cr_0 * _S35 - ci_0 * _S36;
                    float _S37 = cr_0 * _S36 + ci_0 * _S35;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S37;

#line 42
                }

#line 50
                uint per_3 = 32U / _S30;
                uint _S38 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S38;

#line 52
                uint lane2_3 = tid_0 % _S38;

#line 52
                exchange_0(r_5, _S29, lgTB_1, 32U, 1024U, blk_3, lane_3, per_3, _S38, 32U, blk2_3, lane2_3, kernelContext_3);

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

#line 835 "mm_32768_refineItems.slang"
    return;
}


#line 789
uint lgOf_0(uint i_4)
{

#line 789
    uint _S39;

#line 789
    if(i_4 < 2U)
    {

#line 789
        _S39 = 5U;

#line 789
    }
    else
    {

#line 789
        if(i_4 == 2U)
        {

#line 789
            _S39 = 5U;

#line 789
        }
        else
        {

#line 789
            _S39 = 1U;

#line 789
        }

#line 789
    }

#line 789
    return _S39;
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
void filterPairOut_0(uint pair_0, uint opair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_0, uint winEnd_0, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{


    uint b_4;

#line 875
    kernelContext_4->_tid_0 = tid_1;
    uint _S40 = pair_0 / ntmpl_1;

#line 876
    uint _S41 = pair_0 % ntmpl_1;

#line 881
    thread array<float2, int(32)> r_6;

#line 881
    uint n2_0 = 0U;

#line 892
    for(;;)
    {

#line 892
        if(n2_0 < 32U)
        {
        }
        else
        {

#line 892
            break;
        }

#line 893
        uint idx_0 = tid_1 + 1024U * n2_0;

#line 77 "twiddle.slang"
        uint _S42 = mfDataStrideFlag_0();

#line 172 "mm_32768_refineItems.slang"
        if(_S42 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S43 = mfDataStrideFlag_0();

#line 77
            b_4 = _S43;

#line 172 "mm_32768_refineItems.slang"
        }
        else
        {

#line 172
            b_4 = 32768U;

#line 172
        }

#line 894
        r_6[n2_0] = cmulConj_0(cload_0(data_0, _S40 * b_4 + idx_0), cload_0(tmpl_0, _S41 * 32768U + idx_0));

#line 892
        n2_0 = n2_0 + 1U;

#line 892
    }

#line 892
    transform_0(&r_6, tid_1, kernelContext_4);

#line 921
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 921
    b_4 = tid_1;

#line 1033
    for(;;)
    {

#line 1033
        if(b_4 < nbins_1)
        {
        }
        else
        {

#line 1033
            break;
        }

#line 1033
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4] = thrBits_1;

#line 1033
        b_4 = b_4 + 1024U;

#line 1033
    }
    bool _S44 = nbins_1 == 1U;

#line 1034
    bool live_0;

#line 1034
    if(_S44)
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
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 1034
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1093
    thread array<uint, int(32)> myMag_0;
    thread array<uint, int(32)> myBin_0;

#line 1094
    uint i_5 = 0U;



    for(;;)
    {

#line 1098
        if(i_5 < 32U)
        {
        }
        else
        {

#line 1098
            break;
        }

#line 1099
        uint idx_1 = slotToIndex_0(tid_1 * 32U + i_5);
        if(idx_1 >= winStart_0)
        {

#line 1100
            live_0 = idx_1 < winEnd_0;

#line 1100
        }
        else
        {

#line 1100
            live_0 = false;

#line 1100
        }



        float _rx_0 = r_6[i_5].x;

#line 1104
        float _ry_0 = r_6[i_5].y;
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
        myMag_0[i_5] = n2_0;

#line 1113
        uint off_0 = idx_1 - winStart_0;

#line 1120
        if(live_0)
        {

#line 1120
            if(binShift_1 >= int(0))
            {

#line 1120
                b_4 = off_0 >> uint(binShift_1);

#line 1120
            }
            else
            {

#line 1120
                uint _S45 = off_0 / binsize_1;

#line 1120
                b_4 = _S45;

#line 1120
            }

#line 1120
        }
        else
        {

#line 1120
            b_4 = 0U;

#line 1120
        }

#line 1120
        myBin_0[i_5] = b_4;

#line 1120
        bool _S46;



        if(nbins_1 > 1U)
        {

#line 1124
            _S46 = (myMag_0[i_5]) > thrBits_1;

#line 1124
        }
        else
        {

#line 1124
            _S46 = false;

#line 1124
        }

#line 1124
        if(_S46)
        {

#line 1125
            uint _S47 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), myMag_0[i_5], memory_order_relaxed);

#line 1124
        }

#line 1098
        i_5 = i_5 + 1U;

#line 1098
    }

#line 1098
    uint winner_0;

#line 1148
    if(_S44)
    {

#line 1148
        winner_0 = thrBits_1;

#line 1148
        i_5 = 0U;


        for(;;)
        {

#line 1151
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1151
                break;
            }

#line 1151
            uint _S48 = max(winner_0, myMag_0[i_5]);

#line 1151
            uint i_6 = i_5 + 1U;

#line 1151
            winner_0 = _S48;

#line 1151
            i_5 = i_6;

#line 1151
        }

        uint wm_0 = simd_max(winner_0);
        bool _S49 = simd_is_first();

#line 1154
        if(_S49)
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
            uint _S50 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1154
        }

#line 1148
    }

#line 1169
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1176
    if(_S44)
    {

#line 1176
        winner_0 = 4294967295U;

#line 1176
        i_5 = 0U;


        for(;;)
        {

#line 1179
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1179
                break;
            }

#line 1180
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1180
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

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
                winner_0 = min(winner_0, tid_1 * 32U + i_5);

#line 1180
            }

#line 1179
            i_5 = i_5 + 1U;

#line 1179
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S51 = simd_is_first();

#line 1184
        if(_S51)
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
            uint _S52 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1184
        }

#line 1189
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1189
        i_5 = 0U;
        for(;;)
        {

#line 1190
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1190
                break;
            }

#line 1191
            uint _S53 = tid_1 * 32U + i_5;

#line 1191
            if(_S53 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 1192
                *(peakIdx_0+opair_0) = int(slotToIndex_0(_S53));

#line 1192
                *(peakVal_0+opair_0) = packed_float2(float2(r_6[i_5].x, r_6[i_5].y)) ;

#line 1191
            }

#line 1190
            i_5 = i_5 + 1U;

#line 1190
        }

#line 1200
        if(tid_1 == 0U)
        {

#line 1200
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

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
        i_5 = 0U;

#line 1209
        for(;;)
        {

#line 1209
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1209
                break;
            }

#line 1210
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1210
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]];

#line 1210
            }
            else
            {

#line 1210
                live_0 = false;

#line 1210
            }

#line 1210
            myMag_0[i_5] = uint(live_0);

#line 1209
            i_5 = i_5 + 1U;

#line 1209
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1212
        b_4 = tid_1;
        for(;;)
        {

#line 1213
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 1213
                break;
            }

#line 1213
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4] = 4294967295U;

#line 1213
            b_4 = b_4 + 1024U;

#line 1213
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1214
        i_5 = 0U;
        for(;;)
        {

#line 1215
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1215
                break;
            }

#line 1216
            if((myMag_0[i_5]) != 0U)
            {

#line 1216
                uint _S54 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), tid_1 * 32U + i_5, memory_order_relaxed);

#line 1216
            }

#line 1215
            i_5 = i_5 + 1U;

#line 1215
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1217
        i_5 = 0U;
        for(;;)
        {

#line 1218
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1218
                break;
            }

#line 1219
            if((myMag_0[i_5]) != 0U)
            {

#line 1219
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]]) == (tid_1 * 32U + i_5);

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
                uint o_0 = opair_0 * nbins_1 + myBin_0[i_5];
                *(peakIdx_0+o_0) = int(slotToIndex_0(tid_1 * 32U + i_5));

#line 1221
                *(peakVal_0+o_0) = packed_float2(float2(r_6[i_5].x, r_6[i_5].y)) ;

#line 1219
            }

#line 1218
            i_5 = i_5 + 1U;

#line 1218
        }

#line 1218
        b_4 = tid_1;

#line 1225
        for(;;)
        {

#line 1225
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 1225
                break;
            }

#line 1226
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4]) == 4294967295U)
            {

#line 1227
                uint _S55 = opair_0 * nbins_1 + b_4;

#line 1227
                *(peakIdx_0+_S55) = int(-1);

#line 1227
                *(peakVal_0+_S55) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1226
            }

#line 1225
            b_4 = b_4 + 1024U;

#line 1225
        }

#line 1176
    }

#line 1235
    return;
}


#line 2170
[[kernel]] void refineItems(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_items_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]])
{

#line 2170
    thread KernelContext_0 kernelContext_5;

#line 2170
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 2170
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2170
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2170
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2170
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2170
    (&kernelContext_5)->entryPointParams_items_0 = entryPointParams_items_1;

#line 2170
    (&kernelContext_5)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2170
    threadgroup array<uint, int(16384)> stg_1;

#line 2170
    (&kernelContext_5)->stg_0 = &stg_1;

#line 2179
    uint _S56 = entryPointParams_count_1[int(0)];

#line 2179
    uint i_7 = gid_0.x;
    for(;;)
    {

#line 2180
        if(i_7 < _S56)
        {
        }
        else
        {

#line 2180
            break;
        }

#line 2181
        (&kernelContext_5)->_stgBase_0 = 0U;
        uint _S57 = 5U * i_7;

#line 2182
        filterPairOut_0((&kernelContext_5)->entryPointParams_items_0[_S57] * (&kernelContext_5)->entryPointParams_0->ntmpl_0 + (&kernelContext_5)->entryPointParams_items_0[_S57 + 1U], (&kernelContext_5)->entryPointParams_items_0[_S57 + 4U], lid_0.x, (&kernelContext_5)->entryPointParams_data_0, (&kernelContext_5)->entryPointParams_tmpl_0, (&kernelContext_5)->entryPointParams_peakIdx_0, (&kernelContext_5)->entryPointParams_peakVal_0, (&kernelContext_5)->entryPointParams_0->ntmpl_0, (&kernelContext_5)->entryPointParams_items_0[_S57 + 2U], (&kernelContext_5)->entryPointParams_items_0[_S57 + 3U], (&kernelContext_5)->entryPointParams_0->binsize_0, (&kernelContext_5)->entryPointParams_0->binShift_0, (&kernelContext_5)->entryPointParams_0->nbins_0, (&kernelContext_5)->entryPointParams_0->thrBits_0, &kernelContext_5);



        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2180
        i_7 = i_7 + (&kernelContext_5)->entryPointParams_0->gridSize_0;

#line 2180
    }

#line 2188
    return;
}
