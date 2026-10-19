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


#line 214 "mm_512_refineListed_onebin_gate.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0, uint device* rowWin_0)
{

#line 104 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 216 "mm_512_refineListed_onebin_gate.slang"
    if(_S3 == 0U)
    {

#line 216
        return;
    }

#line 217
    uint _S4 = 2U * d_0;

#line 217
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


#line 175 "mm_512_refineListed_onebin_gate.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 175
    return float2(*(b_0+i_0)) ;
}


#line 306
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 306
    float _S6 = a_0.x;

#line 306
    float _S7 = b_1.x;

#line 306
    float _S8 = a_0.y;

#line 306
    float _S9 = b_1.y;

#line 306
    return float2(_S6 * _S7 + _S8 * _S9, _S8 * _S7 - _S6 * _S9);
}


#line 511
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 513
    float2 t1_0 = *a_1 - *c_0;

#line 513
    float2 t2_0 = *b_2 + *d_1;

#line 513
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 515
    *b_2 = t1_0 + j3_0;

#line 515
    *c_0 = t0_0 - t2_0;

#line 515
    *d_1 = t1_0 - j3_0;
    return;
}


#line 305
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 305
    float _S10 = a_2.x;

#line 305
    float _S11 = b_3.x;

#line 305
    float _S12 = a_2.y;

#line 305
    float _S13 = b_3.y;

#line 305
    return float2(_S10 * _S11 - _S12 * _S13, _S10 * _S13 + _S12 * _S11);
}


#line 547
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 554
    uint n1_0 = 0U;
    for(;;)
    {

#line 555
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 555
            break;
        }

#line 555
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 555
        n1_0 = n1_0 + 1U;

#line 555
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 556
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 556
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 557
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 557
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 558
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 558
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 558
    uint k2_0 = 0U;
    for(;;)
    {

#line 559
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 559
            break;
        }

#line 559
        uint _S14 = 4U * k2_0;

#line 559
        r4_0(&(*r_0)[_S14], &(*r_0)[_S14 + 1U], &(*r_0)[_S14 + 2U], &(*r_0)[_S14 + 3U]);

#line 559
        k2_0 = k2_0 + 1U;

#line 559
    }

    float2 t_0 = (*r_0)[int(1)];

#line 561
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 561
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 562
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 562
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 563
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 563
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 564
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 564
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 565
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 565
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 566
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 566
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


#line 307 "mm_512_refineListed_onebin_gate.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S18 = max(TB_0, 1U);

#line 309
    uint j_0 = d_2 / _S18;

#line 309
    uint m_0 = d_2 % _S18;

#line 309
    uint _S19;
    if(TB_0 <= 16U)
    {

#line 310
        _S19 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 310
    }
    else
    {

#line 310
        _S19 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 310
    }

#line 310
    return _S19;
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


#line 294 "mm_512_refineListed_onebin_gate.slang"
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
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 294
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 294
    uint _S20 = 2U * i_1;

#line 294
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S20] = (as_type<uint>((v_0.x)));

#line 294
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S20 + 1U] = (as_type<uint>((v_0.y)));

#line 294
    return;
}


#line 295
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 295
    uint _S21 = 2U * i_2;

#line 295
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S21]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S21 + 1U]))));
}


#line 736
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 737
    uint j_1;

#line 748
    thread array<float2, int(16)> out_0;

#line 748
    uint z_1 = 0U;
    for(;;)
    {

#line 749
        if(z_1 < 16U)
        {
        }
        else
        {

#line 749
            break;
        }

#line 749
        out_0[z_1] = float2(0.0f, 0.0f);

#line 749
        z_1 = z_1 + 1U;

#line 749
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S22 = p0_0 & lenMask_0;

#line 755
    uint _S23 = (_S22 >> lgSpan_0) * 32U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S22 & spanMask_0);

#line 755
    uint c_2 = 0U;

    for(;;)
    {

#line 757
        if(c_2 < 1U)
        {
        }
        else
        {

#line 757
            break;
        }

#line 758
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 758
        j_1 = 0U;
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
            stgPut_0(j_1 * 32U + kernelContext_2->_tid_0, (*r_1)[c_2 * 16U + j_1], kernelContext_2);

#line 759
            j_1 = j_1 + 1U;

#line 759
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 760
        uint d_3 = 0U;
        for(;;)
        {

#line 761
            if(d_3 < 16U)
            {
            }
            else
            {

#line 761
                break;
            }

#line 762
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S24 = pz_0 & lenMask_0;
            uint az_0 = (_S24 >> lgSpan_0) * 32U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S24 & spanMask_0);

#line 764
            float2 _S25 = stgGet_0(_S23 + az_0 - c_2 * 16U * 32U, kernelContext_2);


            out_0[d_3] = _S25;

#line 761
            d_3 = d_3 + 1U;

#line 761
        }

#line 757
        c_2 = c_2 + 1U;

#line 757
    }

#line 757
    j_1 = 0U;

#line 770
    for(;;)
    {

#line 770
        if(j_1 < 16U)
        {
        }
        else
        {

#line 770
            break;
        }

#line 770
        (*r_1)[j_1] = out_0[j_1];

#line 770
        j_1 = j_1 + 1U;

#line 770
    }
    return;
}


#line 522
void dft2_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    float2 a_3 = (*r_2)[o_0];

#line 524
    float2 b_4 = (*r_2)[o_0 + 1U];

#line 524
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 524
    (*r_2)[o_0 + 1U] = a_3 - b_4;
    return;
}


#line 650
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 650
    uint b_5 = 0U;

#line 660
    for(;;)
    {

#line 660
        if(b_5 < 8U)
        {
        }
        else
        {

#line 660
            break;
        }

#line 660
        dft2_0(r_3, b_5 * 2U);

#line 660
        b_5 = b_5 + 1U;

#line 660
    }

    return;
}


#line 838
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 838
    uint _S26;

#line 838
    uint k2_1;

#line 838
    float cr_0;

#line 838
    float ci_0;

#line 838
    uint _S27;

#line 838
    for(;;)
    {

#line 838
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
                exchange_0(r_4, lgLn_0, lgTB_0, 32U, 512U, blk_2, lane_2, per_2, _S31, 32U, blk2_2, lane2_2, kernelContext_3);

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
                exchange_0(r_4, _S26, lgTB_1, 2U, 32U, blk_3, lane_3, per_3, _S35, 2U, blk2_3, lane2_3, kernelContext_3);

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

#line 841 "mm_512_refineListed_onebin_gate.slang"
    return;
}


#line 795
uint lgOf_0(uint i_3)
{

#line 795
    uint _S36;

#line 795
    if(i_3 < 2U)
    {

#line 795
        _S36 = 4U;

#line 795
    }
    else
    {

#line 795
        _S36 = 1U;

#line 795
    }

#line 795
    return _S36;
}


#line 797
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 801
    uint lg_1 = lgOf_0(1U);

#line 801
    uint lg_2 = lgOf_0(0U);

#line 806
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 855
void filterPairOut_0(uint pair_0, uint opair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{


    uint m_1;

#line 875
    bool gateOnly_0 = nbins_1 == 0U;

#line 882
    kernelContext_4->_tid_0 = tid_1;
    uint _S37 = pair_0 / ntmpl_1;

#line 883
    uint _S38 = pair_0 % ntmpl_1;

#line 888
    thread array<float2, int(16)> r_5;

#line 888
    uint n2_0 = 0U;

#line 899
    for(;;)
    {

#line 899
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 899
            break;
        }

#line 900
        uint idx_0 = tid_1 + 32U * n2_0;

#line 77 "twiddle.slang"
        uint _S39 = mfDataStrideFlag_0();

#line 178 "mm_512_refineListed_onebin_gate.slang"
        if(_S39 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S40 = mfDataStrideFlag_0();

#line 77
            m_1 = _S40;

#line 178 "mm_512_refineListed_onebin_gate.slang"
        }
        else
        {

#line 178
            m_1 = 512U;

#line 178
        }

#line 901
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S37 * m_1 + idx_0), cload_0(tmpl_0, _S38 * 512U + idx_0));

#line 899
        n2_0 = n2_0 + 1U;

#line 899
    }

#line 899
    transform_0(&r_5, tid_1, kernelContext_4);

#line 928
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 928
    uint i_4;

#line 928
    bool live_0;

#line 937
    if(gateOnly_0)
    {



        if(winStart_2 == 0U)
        {

#line 942
            live_0 = winEnd_2 >= 512U;

#line 942
        }
        else
        {

#line 942
            live_0 = false;

#line 942
        }

#line 942
        if(live_0)
        {

#line 942
            m_1 = 0U;

#line 942
            i_4 = 0U;
            for(;;)
            {

#line 943
                if(i_4 < 16U)
                {
                }
                else
                {

#line 943
                    break;
                }

#line 944
                uint _S41 = max(m_1, (as_type<uint>((r_5[i_4].x * r_5[i_4].x + r_5[i_4].y * r_5[i_4].y))));

#line 943
                uint i_5 = i_4 + 1U;

#line 943
                m_1 = _S41;

#line 943
                i_4 = i_5;

#line 943
            }

#line 942
        }
        else
        {

#line 942
            m_1 = 0U;

#line 942
            i_4 = 0U;



            for(;;)
            {

#line 946
                if(i_4 < 16U)
                {
                }
                else
                {

#line 946
                    break;
                }

#line 947
                uint idx_1 = slotToIndex_0(tid_1 * 16U + i_4);
                if(idx_1 >= winStart_2)
                {

#line 948
                    live_0 = idx_1 < winEnd_2;

#line 948
                }
                else
                {

#line 948
                    live_0 = false;

#line 948
                }
                uint b_6 = (as_type<uint>((r_5[i_4].x * r_5[i_4].x + r_5[i_4].y * r_5[i_4].y)));
                if(live_0)
                {

#line 950
                    n2_0 = max(m_1, b_6);

#line 950
                }
                else
                {

#line 950
                    n2_0 = m_1;

#line 950
                }

#line 946
                uint i_6 = i_4 + 1U;

#line 946
                m_1 = n2_0;

#line 946
                i_4 = i_6;

#line 946
            }

#line 942
        }

#line 953
        uint m_2 = simd_max(m_1);

#line 961
        if(tid_1 == 0U)
        {

#line 962
            int device* _S42 = peakIdx_0+opair_0;

#line 962
            int _S43;

#line 962
            if(m_2 > 0U)
            {

#line 962
                _S43 = int(0);

#line 962
            }
            else
            {

#line 962
                _S43 = int(-1);

#line 962
            }

#line 962
            *_S42 = _S43;

#line 962
            *(peakVal_0+opair_0) = packed_float2(float2(sqrt((as_type<float>((m_2)))), 0.0f)) ;

#line 961
        }



        return;
    }

#line 971
    bool _S44 = tid_1 == 0U;

#line 971
    if(_S44)
    {

#line 971
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 971
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 971
    }



    float2 _S45 = float2(0.0f, 0.0f);

    if(winStart_2 == 0U)
    {

#line 977
        live_0 = winEnd_2 >= 512U;

#line 977
    }
    else
    {

#line 977
        live_0 = false;

#line 977
    }

#line 977
    uint threadBestSlot_0;

#line 977
    float2 threadBestVal_0;

#line 977
    if(live_0)
    {

#line 977
        m_1 = thrBits_1;

#line 977
        threadBestSlot_0 = 4294967295U;

#line 977
        threadBestVal_0 = _S45;

#line 977
        i_4 = 0U;
        for(;;)
        {

#line 978
            if(i_4 < 16U)
            {
            }
            else
            {

#line 978
                break;
            }

#line 979
            float _rx_0 = r_5[i_4].x;

#line 979
            float _ry_0 = r_5[i_4].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > m_1)
            {
                uint _S46 = tid_1 * 16U + i_4;
                float2 _S47 = float2(_rx_0, _ry_0);

#line 984
                m_1 = magBits_0;

#line 984
                threadBestSlot_0 = _S46;

#line 984
                threadBestVal_0 = _S47;

#line 981
            }

#line 978
            i_4 = i_4 + 1U;

#line 978
        }

#line 977
    }
    else
    {

#line 977
        m_1 = thrBits_1;

#line 977
        threadBestSlot_0 = 4294967295U;

#line 977
        threadBestVal_0 = _S45;

#line 977
        i_4 = 0U;

#line 988
        for(;;)
        {

#line 988
            if(i_4 < 16U)
            {
            }
            else
            {

#line 988
                break;
            }

#line 989
            uint _S48 = tid_1 * 16U + i_4;

#line 989
            uint idx_2 = slotToIndex_0(_S48);
            if(idx_2 >= winStart_2)
            {

#line 990
                live_0 = idx_2 < winEnd_2;

#line 990
            }
            else
            {

#line 990
                live_0 = false;

#line 990
            }
            float _rx_1 = r_5[i_4].x;

#line 991
            float _ry_1 = r_5[i_4].y;

#line 991
            uint magBits_1;
            if(live_0)
            {

#line 992
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 992
            }
            else
            {

#line 992
                magBits_1 = 0U;

#line 992
            }
            if(magBits_1 > m_1)
            {

                float2 _S49 = float2(_rx_1, _ry_1);

#line 996
                m_1 = magBits_1;

#line 996
                threadBestSlot_0 = _S48;

#line 996
                threadBestVal_0 = _S49;

#line 993
            }

#line 988
            i_4 = i_4 + 1U;

#line 988
        }

#line 977
    }

#line 1001
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(m_1);
    bool _S50 = simd_is_first();

#line 1005
    if(_S50)
    {

#line 1005
        live_0 = wm_0 > thrBits_1;

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
        uint _S51 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1005
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(m_1 > thrBits_1)
    {

#line 1012
        live_0 = m_1 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 1012
    }
    else
    {

#line 1012
        live_0 = false;

#line 1012
    }

#line 1012
    if(live_0)
    {

#line 1012
        i_4 = threadBestSlot_0;

#line 1012
    }
    else
    {

#line 1012
        i_4 = 4294967295U;

#line 1012
    }



    uint waveWinner_0 = simd_min(i_4);
    bool _S52 = simd_is_first();

#line 1017
    if(_S52)
    {

#line 1017
        live_0 = waveWinner_0 != 4294967295U;

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
        uint _S53 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1017
    }

#line 1022
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(threadBestSlot_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
    {

#line 1024
        live_0 = threadBestSlot_0 != 4294967295U;

#line 1024
    }
    else
    {

#line 1024
        live_0 = false;

#line 1024
    }

#line 1024
    if(live_0)
    {

#line 1025
        *(peakIdx_0+opair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 1025
        *(peakVal_0+opair_0) = packed_float2(threadBestVal_0) ;

#line 1024
    }



    if(_S44)
    {

#line 1028
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1028
    }
    else
    {

#line 1028
        live_0 = false;

#line 1028
    }

#line 1028
    if(live_0)
    {

#line 1029
        *(peakIdx_0+opair_0) = int(-1);

#line 1029
        *(peakVal_0+opair_0) = packed_float2(_S45) ;

#line 1028
    }

#line 1242
    return;
}

void filterPair_0(uint pair_1, uint tid_2, packed_float2 device* data_1, packed_float2 device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_2, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_5)
{


    filterPairOut_0(pair_1, pair_1, tid_2, data_1, tmpl_1, peakIdx_1, peakVal_1, ntmpl_2, winStart_3, winEnd_3, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_5);



    return;
}


#line 2149
[[kernel]] void refineListedBounded(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]], uint device* entryPointParams_rowWin_1 [[buffer(7)]])
{

#line 2149
    thread KernelContext_0 kernelContext_6;

#line 2149
    (&kernelContext_6)->entryPointParams_0 = entryPointParams_1;

#line 2149
    (&kernelContext_6)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2149
    (&kernelContext_6)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2149
    (&kernelContext_6)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2149
    (&kernelContext_6)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2149
    (&kernelContext_6)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2149
    (&kernelContext_6)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2149
    (&kernelContext_6)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 2149
    threadgroup array<uint, int(1024)> stg_1;

#line 2149
    (&kernelContext_6)->stg_0 = &stg_1;

#line 2159
    uint _S54 = entryPointParams_count_1[int(0)];

#line 2159
    uint i_7 = gid_0.x;
    for(;;)
    {

#line 2160
        if(i_7 < _S54)
        {
        }
        else
        {

#line 2160
            break;
        }

#line 2161
        (&kernelContext_6)->_stgBase_0 = 0U;
        uint pair_2 = (&kernelContext_6)->entryPointParams_survivors_0[i_7];

#line 2162
        thread uint ws_0 = (&kernelContext_6)->entryPointParams_0->winStart_1;

#line 2162
        thread uint we_0 = (&kernelContext_6)->entryPointParams_0->winEnd_1;
        uint _S55 = pair_2 / (&kernelContext_6)->entryPointParams_0->ntmpl_0;

#line 2163
        rowWindow_0(_S55, &ws_0, &we_0, (&kernelContext_6)->entryPointParams_rowWin_0);

#line 2163
        filterPair_0(pair_2, lid_0.x, (&kernelContext_6)->entryPointParams_data_0, (&kernelContext_6)->entryPointParams_tmpl_0, (&kernelContext_6)->entryPointParams_peakIdx_0, (&kernelContext_6)->entryPointParams_peakVal_0, (&kernelContext_6)->entryPointParams_0->ntmpl_0, ws_0, we_0, (&kernelContext_6)->entryPointParams_0->binsize_0, (&kernelContext_6)->entryPointParams_0->binShift_0, (&kernelContext_6)->entryPointParams_0->nbins_0, (&kernelContext_6)->entryPointParams_0->thrBits_0, &kernelContext_6);


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2160
        i_7 = i_7 + (&kernelContext_6)->entryPointParams_0->gridSize_0;

#line 2160
    }

#line 2168
    return;
}
