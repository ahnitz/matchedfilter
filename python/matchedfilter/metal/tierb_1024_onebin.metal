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


#line 168 "mm_1024_fusedTierB_onebin.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 168
    return float2(*(b_0+i_0)) ;
}


#line 299
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 299
    float _S3 = a_0.x;

#line 299
    float _S4 = b_1.x;

#line 299
    float _S5 = a_0.y;

#line 299
    float _S6 = b_1.y;

#line 299
    return float2(_S3 * _S4 + _S5 * _S6, _S5 * _S4 - _S3 * _S6);
}


#line 504
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 506
    float2 t1_0 = *a_1 - *c_0;

#line 506
    float2 t2_0 = *b_2 + *d_0;

#line 506
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 508
    *b_2 = t1_0 + j3_0;

#line 508
    *c_0 = t0_0 - t2_0;

#line 508
    *d_0 = t1_0 - j3_0;
    return;
}


#line 298
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 298
    float _S7 = a_2.x;

#line 298
    float _S8 = b_3.x;

#line 298
    float _S9 = a_2.y;

#line 298
    float _S10 = b_3.y;

#line 298
    return float2(_S7 * _S8 - _S9 * _S10, _S7 * _S10 + _S9 * _S8);
}


#line 540
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 547
    uint n1_0 = 0U;
    for(;;)
    {

#line 548
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 548
            break;
        }

#line 548
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 548
        n1_0 = n1_0 + 1U;

#line 548
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 549
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 549
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 550
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 550
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 551
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 551
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 551
    uint k2_0 = 0U;
    for(;;)
    {

#line 552
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 552
            break;
        }

#line 552
        uint _S11 = 4U * k2_0;

#line 552
        r4_0(&(*r_0)[_S11], &(*r_0)[_S11 + 1U], &(*r_0)[_S11 + 2U], &(*r_0)[_S11 + 3U]);

#line 552
        k2_0 = k2_0 + 1U;

#line 552
    }

    float2 t_0 = (*r_0)[int(1)];

#line 554
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 554
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 555
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 555
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 556
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 556
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 557
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 557
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 558
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 558
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 559
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 559
    (*r_0)[int(14)] = t_5;
    return;
}


#line 88 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S12 = ((MF_ACCURATE_TRIG));

#line 91
    return _S12;
}


#line 127
float2 mfTwiddle_0(float angle_0)
{

#line 93
    uint _S13 = mfAccurateTrigFlag_0();

#line 129
    if(_S13 == 0U)
    {

#line 130
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S14 = float(quadrant_0);
    float x_0 = angle_0 - _S14 * 1.57079625129699707f - _S14 * 7.54978941586159635e-08f;
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


#line 300 "mm_1024_fusedTierB_onebin.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S15 = max(TB_0, 1U);

#line 302
    uint j_0 = d_1 / _S15;

#line 302
    uint m_0 = d_1 % _S15;

#line 302
    uint _S16;
    if(TB_0 <= 16U)
    {

#line 303
        _S16 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 303
    }
    else
    {

#line 303
        _S16 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 303
    }

#line 303
    return _S16;
}


#line 8599 "hlsl.meta.slang"
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


#line 287 "mm_1024_fusedTierB_onebin.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 287
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 287
    uint _S17 = 2U * i_1;

#line 287
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S17] = (as_type<uint>((v_0.x)));

#line 287
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S17 + 1U] = (as_type<uint>((v_0.y)));

#line 287
    return;
}


#line 288
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 288
    uint _S18 = 2U * i_2;

#line 288
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S18]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S18 + 1U]))));
}


#line 729
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 730
    uint j_1;

#line 741
    thread array<float2, int(16)> out_0;

#line 741
    uint z_1 = 0U;
    for(;;)
    {

#line 742
        if(z_1 < 16U)
        {
        }
        else
        {

#line 742
            break;
        }

#line 742
        out_0[z_1] = float2(0.0f, 0.0f);

#line 742
        z_1 = z_1 + 1U;

#line 742
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S19 = p0_0 & lenMask_0;

#line 748
    uint _S20 = (_S19 >> lgSpan_0) * 64U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S19 & spanMask_0);

#line 748
    uint c_2 = 0U;

    for(;;)
    {

#line 750
        if(c_2 < 1U)
        {
        }
        else
        {

#line 750
            break;
        }

#line 751
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 751
        j_1 = 0U;
        for(;;)
        {

#line 752
            if(j_1 < 16U)
            {
            }
            else
            {

#line 752
                break;
            }

#line 752
            stgPut_0(j_1 * 64U + kernelContext_2->_tid_0, (*r_1)[c_2 * 16U + j_1], kernelContext_2);

#line 752
            j_1 = j_1 + 1U;

#line 752
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 753
        uint d_2 = 0U;
        for(;;)
        {

#line 754
            if(d_2 < 16U)
            {
            }
            else
            {

#line 754
                break;
            }

#line 755
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S21 = pz_0 & lenMask_0;
            uint az_0 = (_S21 >> lgSpan_0) * 64U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S21 & spanMask_0);

#line 757
            float2 _S22 = stgGet_0(_S20 + az_0 - c_2 * 16U * 64U, kernelContext_2);


            out_0[d_2] = _S22;

#line 754
            d_2 = d_2 + 1U;

#line 754
        }

#line 750
        c_2 = c_2 + 1U;

#line 750
    }

#line 750
    j_1 = 0U;

#line 763
    for(;;)
    {

#line 763
        if(j_1 < 16U)
        {
        }
        else
        {

#line 763
            break;
        }

#line 763
        (*r_1)[j_1] = out_0[j_1];

#line 763
        j_1 = j_1 + 1U;

#line 763
    }
    return;
}


#line 519
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 522
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 522
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 643
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 643
    uint b_4 = 0U;

#line 652
    for(;;)
    {

#line 652
        if(b_4 < 4U)
        {
        }
        else
        {

#line 652
            break;
        }

#line 652
        dft4_0(r_3, b_4 * 4U);

#line 652
        b_4 = b_4 + 1U;

#line 652
    }


    return;
}


#line 831
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 831
    uint _S23;

#line 831
    uint k2_1;

#line 831
    float cr_0;

#line 831
    float ci_0;

#line 831
    uint _S24;

#line 831
    for(;;)
    {

#line 831
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(64U);

#line 11
                _S23 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(1024U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 63U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);
                float _S25 = tw_0.x;

#line 40
                float _S26 = tw_0.y;

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
                    float nr_0 = cr_0 * _S25 - ci_0 * _S26;
                    float _S27 = cr_0 * _S26 + ci_0 * _S25;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S27;

#line 42
                }

#line 50
                uint per_2 = 16U / max(64U, 1U);
                uint _S28 = max(4U, 1U);

#line 51
                _S24 = _S28;
                uint blk2_2 = tid_0 / _S28;

#line 52
                uint lane2_2 = tid_0 % _S28;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 64U, 1024U, blk_2, lane_2, per_2, _S28, 64U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(4U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 3U;


                dft16_0(r_4);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 64.0f);
                float _S29 = tw_1.x;

#line 40
                float _S30 = tw_1.y;

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
                    float nr_1 = cr_0 * _S29 - ci_0 * _S30;
                    float _S31 = cr_0 * _S30 + ci_0 * _S29;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S31;

#line 42
                }

#line 50
                uint per_3 = 16U / _S24;
                uint _S32 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S32;

#line 52
                uint lane2_3 = tid_0 % _S32;

#line 52
                exchange_0(r_4, _S23, lgTB_1, 4U, 64U, blk_3, lane_3, per_3, _S32, 4U, blk2_3, lane2_3, kernelContext_3);

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

#line 834 "mm_1024_fusedTierB_onebin.slang"
    return;
}


#line 788
uint lgOf_0(uint i_3)
{

#line 788
    uint _S33;

#line 788
    if(i_3 < 2U)
    {

#line 788
        _S33 = 4U;

#line 788
    }
    else
    {

#line 788
        _S33 = 1U;

#line 788
    }

#line 788
    return _S33;
}


#line 790
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_1 = slot_0 >> lg_0;

#line 794
    uint lg_1 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_1;

#line 794
    uint lg_2 = lgOf_0(1U);

#line 794
    uint lg_3 = lgOf_0(0U);

#line 799
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | (x_2 & ((1U << lg_2) - 1U))) << lg_3) | ((x_2 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 854
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{


    uint m_1;

#line 867
    bool gateOnly_0 = nbins_1 == 0U;

#line 874
    kernelContext_4->_tid_0 = tid_1;
    uint _S34 = pair_0 / ntmpl_1;

#line 875
    uint _S35 = pair_0 % ntmpl_1;

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
        uint idx_0 = tid_1 + 64U * n2_0;

#line 77 "twiddle.slang"
        uint _S36 = mfDataStrideFlag_0();

#line 171 "mm_1024_fusedTierB_onebin.slang"
        if(_S36 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S37 = mfDataStrideFlag_0();

#line 77
            m_1 = _S37;

#line 171 "mm_1024_fusedTierB_onebin.slang"
        }
        else
        {

#line 171
            m_1 = 1024U;

#line 171
        }

#line 893
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S34 * m_1 + idx_0), cload_0(tmpl_0, _S35 * 1024U + idx_0));

#line 891
        n2_0 = n2_0 + 1U;

#line 891
    }

#line 891
    transform_0(&r_5, tid_1, kernelContext_4);

#line 920
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 920
    uint k_0;

#line 920
    uint i_4;

#line 920
    bool live_0;

#line 929
    if(gateOnly_0)
    {



        if(winStart_1 == 0U)
        {

#line 934
            live_0 = winEnd_1 >= 1024U;

#line 934
        }
        else
        {

#line 934
            live_0 = false;

#line 934
        }

#line 934
        if(live_0)
        {

#line 934
            m_1 = 0U;

#line 934
            i_4 = 0U;
            for(;;)
            {

#line 935
                if(i_4 < 16U)
                {
                }
                else
                {

#line 935
                    break;
                }

#line 936
                uint _S38 = max(m_1, (as_type<uint>((r_5[i_4].x * r_5[i_4].x + r_5[i_4].y * r_5[i_4].y))));

#line 935
                uint i_5 = i_4 + 1U;

#line 935
                m_1 = _S38;

#line 935
                i_4 = i_5;

#line 935
            }

#line 934
        }
        else
        {

#line 934
            m_1 = 0U;

#line 934
            i_4 = 0U;



            for(;;)
            {

#line 938
                if(i_4 < 16U)
                {
                }
                else
                {

#line 938
                    break;
                }

#line 939
                uint idx_1 = slotToIndex_0(tid_1 * 16U + i_4);
                if(idx_1 >= winStart_1)
                {

#line 940
                    live_0 = idx_1 < winEnd_1;

#line 940
                }
                else
                {

#line 940
                    live_0 = false;

#line 940
                }
                uint b_5 = (as_type<uint>((r_5[i_4].x * r_5[i_4].x + r_5[i_4].y * r_5[i_4].y)));
                if(live_0)
                {

#line 942
                    n2_0 = max(m_1, b_5);

#line 942
                }
                else
                {

#line 942
                    n2_0 = m_1;

#line 942
                }

#line 938
                uint i_6 = i_4 + 1U;

#line 938
                m_1 = n2_0;

#line 938
                i_4 = i_6;

#line 938
            }

#line 934
        }

#line 945
        uint m_2 = simd_max(m_1);


        bool _S39 = simd_is_first();

#line 948
        if(_S39)
        {

#line 948
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_1 / 32U] = m_2;

#line 948
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 949
        m_1 = 0U;

#line 949
        k_0 = 0U;

        for(;;)
        {

#line 951
            if(k_0 < 2U)
            {
            }
            else
            {

#line 951
                break;
            }

#line 951
            uint _S40 = max(m_1, (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_0]);

#line 951
            uint k_1 = k_0 + 1U;

#line 951
            m_1 = _S40;

#line 951
            k_0 = k_1;

#line 951
        }

        if(tid_1 == 0U)
        {

#line 954
            int device* _S41 = peakIdx_0+pair_0;

#line 954
            int _S42;

#line 954
            if(m_1 > 0U)
            {

#line 954
                _S42 = int(0);

#line 954
            }
            else
            {

#line 954
                _S42 = int(-1);

#line 954
            }

#line 954
            *_S41 = _S42;

#line 954
            *(peakVal_0+pair_0) = packed_float2(float2(sqrt((as_type<float>((m_1)))), 0.0f)) ;

#line 953
        }



        return;
    }

#line 963
    bool _S43 = tid_1 == 0U;

#line 963
    if(_S43)
    {

#line 963
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 963
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 963
    }



    float2 _S44 = float2(0.0f, 0.0f);

    if(winStart_1 == 0U)
    {

#line 969
        live_0 = winEnd_1 >= 1024U;

#line 969
    }
    else
    {

#line 969
        live_0 = false;

#line 969
    }

#line 969
    float2 threadBestVal_0;

#line 969
    if(live_0)
    {

#line 969
        m_1 = thrBits_1;

#line 969
        k_0 = 4294967295U;

#line 969
        threadBestVal_0 = _S44;

#line 969
        i_4 = 0U;
        for(;;)
        {

#line 970
            if(i_4 < 16U)
            {
            }
            else
            {

#line 970
                break;
            }

#line 971
            float _rx_0 = r_5[i_4].x;

#line 971
            float _ry_0 = r_5[i_4].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > m_1)
            {
                uint _S45 = tid_1 * 16U + i_4;
                float2 _S46 = float2(_rx_0, _ry_0);

#line 976
                m_1 = magBits_0;

#line 976
                k_0 = _S45;

#line 976
                threadBestVal_0 = _S46;

#line 973
            }

#line 970
            i_4 = i_4 + 1U;

#line 970
        }

#line 969
    }
    else
    {

#line 969
        m_1 = thrBits_1;

#line 969
        k_0 = 4294967295U;

#line 969
        threadBestVal_0 = _S44;

#line 969
        i_4 = 0U;

#line 980
        for(;;)
        {

#line 980
            if(i_4 < 16U)
            {
            }
            else
            {

#line 980
                break;
            }

#line 981
            uint _S47 = tid_1 * 16U + i_4;

#line 981
            uint idx_2 = slotToIndex_0(_S47);
            if(idx_2 >= winStart_1)
            {

#line 982
                live_0 = idx_2 < winEnd_1;

#line 982
            }
            else
            {

#line 982
                live_0 = false;

#line 982
            }
            float _rx_1 = r_5[i_4].x;

#line 983
            float _ry_1 = r_5[i_4].y;

#line 983
            uint magBits_1;
            if(live_0)
            {

#line 984
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 984
            }
            else
            {

#line 984
                magBits_1 = 0U;

#line 984
            }
            if(magBits_1 > m_1)
            {

                float2 _S48 = float2(_rx_1, _ry_1);

#line 988
                m_1 = magBits_1;

#line 988
                k_0 = _S47;

#line 988
                threadBestVal_0 = _S48;

#line 985
            }

#line 980
            i_4 = i_4 + 1U;

#line 980
        }

#line 969
    }

#line 993
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(m_1);
    bool _S49 = simd_is_first();

#line 997
    if(_S49)
    {

#line 997
        live_0 = wm_0 > thrBits_1;

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

#line 997
        uint _S50 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 997
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(m_1 > thrBits_1)
    {

#line 1004
        live_0 = m_1 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

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

#line 1004
        i_4 = k_0;

#line 1004
    }
    else
    {

#line 1004
        i_4 = 4294967295U;

#line 1004
    }



    uint waveWinner_0 = simd_min(i_4);
    bool _S51 = simd_is_first();

#line 1009
    if(_S51)
    {

#line 1009
        live_0 = waveWinner_0 != 4294967295U;

#line 1009
    }
    else
    {

#line 1009
        live_0 = false;

#line 1009
    }

#line 1009
    if(live_0)
    {

#line 1010
        uint _S52 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1009
    }

#line 1014
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(k_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
    {

#line 1016
        live_0 = k_0 != 4294967295U;

#line 1016
    }
    else
    {

#line 1016
        live_0 = false;

#line 1016
    }

#line 1016
    if(live_0)
    {

#line 1017
        *(peakIdx_0+pair_0) = int(slotToIndex_0(k_0));

#line 1017
        *(peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 1016
    }



    if(_S43)
    {

#line 1020
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

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

#line 1021
        *(peakIdx_0+pair_0) = int(-1);

#line 1021
        *(peakVal_0+pair_0) = packed_float2(_S44) ;

#line 1020
    }

#line 1234
    return;
}


#line 1725
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1725
    thread KernelContext_0 kernelContext_5;

#line 1725
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1725
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1725
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1725
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1725
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1725
    threadgroup array<uint, int(2048)> stg_1;

#line 1725
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1742
    uint _pr_0 = gid_0.x;

#line 1742
    uint _t_0 = lid_0.x;
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 1743
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);

#line 1758
    return;
}
