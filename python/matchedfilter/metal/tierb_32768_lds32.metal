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


#line 311 "mm_32768_fusedTierB_lds32.slang"
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
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 227
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 104 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 230 "mm_32768_fusedTierB_lds32.slang"
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


#line 173 "mm_32768_fusedTierB_lds32.slang"
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


#line 88 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S10 = ((MF_ACCURATE_TRIG));

#line 91
    return _S10;
}


#line 127
float2 mfTwiddle_0(float angle_0)
{

#line 93
    uint _S11 = mfAccurateTrigFlag_0();

#line 129
    if(_S11 == 0U)
    {

#line 130
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S12 = float(quadrant_0);
    float x_0 = angle_0 - _S12 * 1.57079625129699707f - _S12 * 7.54978941586159635e-08f;
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


#line 322 "mm_32768_fusedTierB_lds32.slang"
float2 cmul_0(float2 a_1, float2 b_2)
{

#line 322
    float _S13 = a_1.x;

#line 322
    float _S14 = b_2.x;

#line 322
    float _S15 = a_1.y;

#line 322
    float _S16 = b_2.y;

#line 322
    return float2(_S13 * _S14 - _S15 * _S16, _S13 * _S16 + _S15 * _S14);
}


#line 528
void r4_0(float2 thread* a_2, float2 thread* b_3, float2 thread* c_1, float2 thread* d_1)
{
    float2 t0_0 = *a_2 + *c_1;

#line 530
    float2 t1_0 = *a_2 - *c_1;

#line 530
    float2 t2_0 = *b_3 + *d_1;

#line 530
    float2 t3_0 = *b_3 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_2 = t0_0 + t2_0;

#line 532
    *b_3 = t1_0 + j3_0;

#line 532
    *c_1 = t0_0 - t2_0;

#line 532
    *d_1 = t1_0 - j3_0;
    return;
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
        uint _S17 = 4U * k2_0;

#line 576
        r4_0(&(*r_0)[_S17], &(*r_0)[_S17 + 1U], &(*r_0)[_S17 + 2U], &(*r_0)[_S17 + 3U]);

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


#line 610
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 612
    thread array<float2, int(16)> v_0;

#line 612
    uint j_0 = 0U;
    for(;;)
    {

#line 613
        if(j_0 < 16U)
        {
        }
        else
        {

#line 613
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        float2 _S18 = (*r_1)[j_0] - (*r_1)[j_0 + 16U];

#line 617
        float2 _S19 = mfTwiddle_0(6.28318548202514648f * float(j_0) / 32.0f);

#line 617
        v_0[j_0] = cmul_0(_S18, _S19);

#line 613
        j_0 = j_0 + 1U;

#line 613
    }

#line 619
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 620
    uint k_0 = 0U;
    for(;;)
    {

#line 621
        if(k_0 < 16U)
        {
        }
        else
        {

#line 621
            break;
        }

#line 621
        uint _S20 = 2U * k_0;

#line 621
        (*r_1)[_S20] = u_0[k_0];

#line 621
        (*r_1)[_S20 + 1U] = v_0[k_0];

#line 621
        k_0 = k_0 + 1U;

#line 621
    }
    return;
}


#line 649
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 324
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S21 = max(TB_0, 1U);

#line 326
    uint j_1 = d_2 / _S21;

#line 326
    uint m_0 = d_2 % _S21;

#line 326
    uint _S22;
    if(TB_0 <= 32U)
    {

#line 327
        _S22 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 327
    }
    else
    {

#line 327
        _S22 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 327
    }

#line 327
    return _S22;
}


#line 311
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_1)
{

#line 311
    uint _S23 = 2U * i_1;

#line 311
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S23] = (as_type<uint>((v_1.x)));

#line 311
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S23 + 1U] = (as_type<uint>((v_1.y)));

#line 311
    return;
}


#line 312
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_2)
{

#line 312
    uint _S24 = 2U * i_2;

#line 312
    return float2((as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S24]))), (as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S24 + 1U]))));
}


#line 753
void exchange_0(array<float2, int(32)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_3)
{

#line 754
    uint j_2;

#line 765
    thread array<float2, int(32)> out_0;

#line 765
    uint z_1 = 0U;
    for(;;)
    {

#line 766
        if(z_1 < 32U)
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
    uint _S25 = p0_0 & lenMask_0;

#line 772
    uint _S26 = _S25 >> lgSpan_0;

#line 772
    uint _S27 = _S26 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S25 & spanMask_0);

#line 772
    uint c_2 = 0U;

    for(;;)
    {

#line 774
        if(c_2 < 8U)
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
        j_2 = 0U;
        for(;;)
        {

#line 776
            if(j_2 < 4U)
            {
            }
            else
            {

#line 776
                break;
            }

#line 776
            stgPut_0(j_2 * 1024U + kernelContext_3->_tid_0, (*r_3)[c_2 * 4U + j_2], kernelContext_3);

#line 776
            j_2 = j_2 + 1U;

#line 776
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 777
        uint d_3 = 0U;
        for(;;)
        {

#line 778
            if(d_3 < 32U)
            {
            }
            else
            {

#line 778
                break;
            }

#line 779
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S28 = pz_0 & lenMask_0;

#line 780
            uint iz_0 = _S28 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S28 & spanMask_0);
            uint i_3 = _S26 + iz_0;
            uint _S29 = c_2 * 4U;

#line 783
            bool _S30;

#line 783
            if(i_3 >= _S29)
            {

#line 783
                _S30 = i_3 < ((c_2 + 1U) * 4U);

#line 783
            }
            else
            {

#line 783
                _S30 = false;

#line 783
            }

#line 783
            if(_S30)
            {

#line 783
                float2 _S31 = stgGet_0(_S27 + az_0 - _S29 * 1024U, kernelContext_3);
                out_0[d_3] = _S31;

#line 783
            }

#line 778
            d_3 = d_3 + 1U;

#line 778
        }

#line 774
        c_2 = c_2 + 1U;

#line 774
    }

#line 774
    j_2 = 0U;

#line 787
    for(;;)
    {

#line 787
        if(j_2 < 32U)
        {
        }
        else
        {

#line 787
            break;
        }

#line 787
        (*r_3)[j_2] = out_0[j_2];

#line 787
        j_2 = j_2 + 1U;

#line 787
    }
    return;
}


#line 667
void innermost_0(array<float2, int(32)> thread* r_4)
{

    dft32_0(r_4);

#line 679
    return;
}


#line 855
void transform_0(array<float2, int(32)> thread* r_5, uint tid_0, KernelContext_0 thread* kernelContext_4)
{

#line 855
    uint _S32;

#line 855
    uint k2_1;

#line 855
    float cr_0;

#line 855
    float ci_0;

#line 855
    uint _S33;

#line 855
    for(;;)
    {

#line 855
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S32 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(32768U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;

#line 19
                dftR_0(r_5);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 32768.0f);
                float _S34 = tw_0.x;

#line 40
                float _S35 = tw_0.y;

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
                    float nr_0 = cr_0 * _S34 - ci_0 * _S35;
                    float _S36 = cr_0 * _S35 + ci_0 * _S34;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S36;

#line 42
                }

#line 50
                uint per_2 = 32U / max(1024U, 1U);
                uint _S37 = max(32U, 1U);

#line 51
                _S33 = _S37;
                uint blk2_2 = tid_0 / _S37;

#line 52
                uint lane2_2 = tid_0 % _S37;

#line 52
                exchange_0(r_5, lgLn_0, lgTB_0, 1024U, 32768U, blk_2, lane_2, per_2, _S37, 1024U, blk2_2, lane2_2, kernelContext_4);

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
                float _S38 = tw_1.x;

#line 40
                float _S39 = tw_1.y;

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
                    float nr_1 = cr_0 * _S38 - ci_0 * _S39;
                    float _S40 = cr_0 * _S39 + ci_0 * _S38;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S40;

#line 42
                }

#line 50
                uint per_3 = 32U / _S33;
                uint _S41 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S41;

#line 52
                uint lane2_3 = tid_0 % _S41;

#line 52
                exchange_0(r_5, _S32, lgTB_1, 32U, 1024U, blk_3, lane_3, per_3, _S41, 32U, blk2_3, lane2_3, kernelContext_4);

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

#line 858 "mm_32768_fusedTierB_lds32.slang"
    return;
}


#line 812
uint lgOf_0(uint i_4)
{

#line 812
    uint _S42;

#line 812
    if(i_4 < 2U)
    {

#line 812
        _S42 = 5U;

#line 812
    }
    else
    {

#line 812
        if(i_4 == 2U)
        {

#line 812
            _S42 = 5U;

#line 812
        }
        else
        {

#line 812
            _S42 = 1U;

#line 812
        }

#line 812
    }

#line 812
    return _S42;
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


    uint b_4;

#line 899
    kernelContext_5->_tid_0 = tid_1;
    uint _S43 = pair_0 / ntmpl_1;

#line 900
    uint _S44 = pair_0 % ntmpl_1;

#line 905
    thread array<float2, int(32)> r_6;

#line 905
    uint n2_0 = 0U;

#line 916
    for(;;)
    {

#line 916
        if(n2_0 < 32U)
        {
        }
        else
        {

#line 916
            break;
        }

#line 917
        uint idx_0 = tid_1 + 1024U * n2_0;

#line 77 "twiddle.slang"
        uint _S45 = mfDataStrideFlag_0();

#line 176 "mm_32768_fusedTierB_lds32.slang"
        if(_S45 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S46 = mfDataStrideFlag_0();

#line 77
            b_4 = _S46;

#line 176 "mm_32768_fusedTierB_lds32.slang"
        }
        else
        {

#line 176
            b_4 = 32768U;

#line 176
        }

#line 918
        r_6[n2_0] = cmulConj_0(cload_0(data_0, _S43 * b_4 + idx_0), cload_0(tmpl_0, _S44 * 32768U + idx_0));

#line 916
        n2_0 = n2_0 + 1U;

#line 916
    }

#line 916
    transform_0(&r_6, tid_1, kernelContext_5);

#line 945
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 945
    b_4 = tid_1;

#line 1057
    for(;;)
    {

#line 1057
        if(b_4 < nbins_1)
        {
        }
        else
        {

#line 1057
            break;
        }

#line 1057
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + b_4] = thrBits_1;

#line 1057
        b_4 = b_4 + 1024U;

#line 1057
    }
    bool _S47 = nbins_1 == 1U;

#line 1058
    bool live_0;

#line 1058
    if(_S47)
    {

#line 1058
        live_0 = tid_1 == 0U;

#line 1058
    }
    else
    {

#line 1058
        live_0 = false;

#line 1058
    }

#line 1058
    if(live_0)
    {

#line 1058
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 1058
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1117
    thread array<uint, int(32)> myMag_0;
    thread array<uint, int(32)> myBin_0;

#line 1118
    uint i_5 = 0U;



    for(;;)
    {

#line 1122
        if(i_5 < 32U)
        {
        }
        else
        {

#line 1122
            break;
        }

#line 1123
        uint idx_1 = slotToIndex_0(tid_1 * 32U + i_5);
        if(idx_1 >= winStart_2)
        {

#line 1124
            live_0 = idx_1 < winEnd_2;

#line 1124
        }
        else
        {

#line 1124
            live_0 = false;

#line 1124
        }



        float _rx_0 = r_6[i_5].x;

#line 1128
        float _ry_0 = r_6[i_5].y;
        if(live_0)
        {

#line 1129
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1129
        }
        else
        {

#line 1129
            n2_0 = 0U;

#line 1129
        }

#line 1129
        myMag_0[i_5] = n2_0;

#line 1137
        uint off_0 = idx_1 - winStart_2 + kernelContext_5->_binPhase_0;

#line 1144
        if(live_0)
        {

#line 1144
            if(binShift_1 >= int(0))
            {

#line 1144
                b_4 = off_0 >> uint(binShift_1);

#line 1144
            }
            else
            {

#line 1144
                uint _S48 = off_0 / binsize_1;

#line 1144
                b_4 = _S48;

#line 1144
            }

#line 1144
        }
        else
        {

#line 1144
            b_4 = 0U;

#line 1144
        }

#line 1144
        myBin_0[i_5] = b_4;

#line 1144
        bool _S49;



        if(nbins_1 > 1U)
        {

#line 1148
            _S49 = (myMag_0[i_5]) > thrBits_1;

#line 1148
        }
        else
        {

#line 1148
            _S49 = false;

#line 1148
        }

#line 1148
        if(_S49)
        {

#line 1149
            uint _S50 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + myBin_0[i_5]])), myMag_0[i_5], memory_order_relaxed);

#line 1148
        }

#line 1122
        i_5 = i_5 + 1U;

#line 1122
    }

#line 1122
    uint winner_0;

#line 1172
    if(_S47)
    {

#line 1172
        winner_0 = thrBits_1;

#line 1172
        i_5 = 0U;


        for(;;)
        {

#line 1175
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1175
                break;
            }

#line 1175
            uint _S51 = max(winner_0, myMag_0[i_5]);

#line 1175
            uint i_6 = i_5 + 1U;

#line 1175
            winner_0 = _S51;

#line 1175
            i_5 = i_6;

#line 1175
        }

        uint wm_0 = simd_max(winner_0);
        bool _S52 = simd_is_first();

#line 1178
        if(_S52)
        {

#line 1178
            live_0 = wm_0 > thrBits_1;

#line 1178
        }
        else
        {

#line 1178
            live_0 = false;

#line 1178
        }

#line 1178
        if(live_0)
        {

#line 1178
            uint _S53 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1178
        }

#line 1172
    }

#line 1193
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1200
    if(_S47)
    {

#line 1200
        winner_0 = 4294967295U;

#line 1200
        i_5 = 0U;


        for(;;)
        {

#line 1203
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1203
                break;
            }

#line 1204
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1204
                live_0 = (myMag_0[i_5]) == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1204
            }
            else
            {

#line 1204
                live_0 = false;

#line 1204
            }

#line 1204
            if(live_0)
            {

#line 1204
                winner_0 = min(winner_0, tid_1 * 32U + i_5);

#line 1204
            }

#line 1203
            i_5 = i_5 + 1U;

#line 1203
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S54 = simd_is_first();

#line 1208
        if(_S54)
        {

#line 1208
            live_0 = waveWinner_0 != 4294967295U;

#line 1208
        }
        else
        {

#line 1208
            live_0 = false;

#line 1208
        }

#line 1208
        if(live_0)
        {

#line 1209
            uint _S55 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1208
        }

#line 1213
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1213
        i_5 = 0U;
        for(;;)
        {

#line 1214
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1214
                break;
            }

#line 1215
            uint _S56 = tid_1 * 32U + i_5;

#line 1215
            if(_S56 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])
            {

#line 1216
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S56));

#line 1216
                *(peakVal_0+pair_0) = packed_float2(float2(r_6[i_5].x, r_6[i_5].y)) ;

#line 1215
            }

#line 1214
            i_5 = i_5 + 1U;

#line 1214
        }

#line 1224
        if(tid_1 == 0U)
        {

#line 1224
            live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U]) == 4294967295U;

#line 1224
        }
        else
        {

#line 1224
            live_0 = false;

#line 1224
        }

#line 1224
        if(live_0)
        {

#line 1225
            *(peakIdx_0+pair_0) = int(-1);

#line 1225
            *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1224
        }

#line 1200
    }
    else
    {

#line 1200
        i_5 = 0U;

#line 1233
        for(;;)
        {

#line 1233
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1233
                break;
            }

#line 1234
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1234
                live_0 = (myMag_0[i_5]) == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + myBin_0[i_5]];

#line 1234
            }
            else
            {

#line 1234
                live_0 = false;

#line 1234
            }

#line 1234
            myMag_0[i_5] = uint(live_0);

#line 1233
            i_5 = i_5 + 1U;

#line 1233
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1236
        b_4 = tid_1;
        for(;;)
        {

#line 1237
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 1237
                break;
            }

#line 1237
            (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + b_4] = 4294967295U;

#line 1237
            b_4 = b_4 + 1024U;

#line 1237
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1238
        i_5 = 0U;
        for(;;)
        {

#line 1239
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1239
                break;
            }

#line 1240
            if((myMag_0[i_5]) != 0U)
            {

#line 1240
                uint _S57 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + myBin_0[i_5]])), tid_1 * 32U + i_5, memory_order_relaxed);

#line 1240
            }

#line 1239
            i_5 = i_5 + 1U;

#line 1239
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1241
        i_5 = 0U;
        for(;;)
        {

#line 1242
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1242
                break;
            }

#line 1243
            if((myMag_0[i_5]) != 0U)
            {

#line 1243
                live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + myBin_0[i_5]]) == (tid_1 * 32U + i_5);

#line 1243
            }
            else
            {

#line 1243
                live_0 = false;

#line 1243
            }

#line 1243
            if(live_0)
            {

#line 1244
                uint o_0 = pair_0 * nbins_1 + myBin_0[i_5];
                *(peakIdx_0+o_0) = int(slotToIndex_0(tid_1 * 32U + i_5));

#line 1245
                *(peakVal_0+o_0) = packed_float2(float2(r_6[i_5].x, r_6[i_5].y)) ;

#line 1243
            }

#line 1242
            i_5 = i_5 + 1U;

#line 1242
        }

#line 1242
        b_4 = tid_1;

#line 1249
        for(;;)
        {

#line 1249
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 1249
                break;
            }

#line 1250
            if(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + b_4]) == 4294967295U)
            {

#line 1251
                uint _S58 = pair_0 * nbins_1 + b_4;

#line 1251
                *(peakIdx_0+_S58) = int(-1);

#line 1251
                *(peakVal_0+_S58) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1250
            }

#line 1249
            b_4 = b_4 + 1024U;

#line 1249
        }

#line 1200
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
    threadgroup array<uint, int(8192)> stg_1;

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
    uint _S59 = _pr_0 / entryPointParams_1->ntmpl_0;

#line 1778
    rowWindow_0(_S59, &_ws_0, &_we_0, (&kernelContext_6)->entryPointParams_rowWin_0, &kernelContext_6);

#line 1778
    filterPair_0(_pr_0, _t_0, (&kernelContext_6)->entryPointParams_data_0, (&kernelContext_6)->entryPointParams_tmpl_0, (&kernelContext_6)->entryPointParams_peakIdx_0, (&kernelContext_6)->entryPointParams_peakVal_0, entryPointParams_1->ntmpl_0, _ws_0, _we_0, (&kernelContext_6)->entryPointParams_0->binsize_0, (&kernelContext_6)->entryPointParams_0->binShift_0, (&kernelContext_6)->entryPointParams_0->nbins_0, (&kernelContext_6)->entryPointParams_0->thrBits_0, &kernelContext_6);

#line 1785
    return;
}
