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
#ifndef MF_DATA_SCALE_BITS
#define MF_DATA_SCALE_BITS 0x3f800000u
#endif
#ifndef MF_COARSE_TWT
#define MF_COARSE_TWT 0u
#endif
#ifndef MF_ACCURATE_TRIG
#define MF_ACCURATE_TRIG 0u
#endif

#line 10 "mm_256_fusedTierB_c16p8.slang"
constant array<uint, int(256)> COARSE_TWT_DATA_0 = { { 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 642268159U, 709377022U, 750074874U, 776354806U, 802569201U, 816987114U, 830028770U, 842939353U, 855849934U, 868629443U, 876886966U, 883243944U, 889535385U, 895761288U, 901921655U, 15360U, 709377022U, 776354806U, 816987114U, 842939353U, 868629443U, 883243944U, 895761288U, 908016484U, 920075067U, 931871502U, 941439709U, 947010215U, 952384109U, 957561391U, 962542061U, 15360U, 750074874U, 816987114U, 855849934U, 883243944U, 901921655U, 920075067U, 937638646U, 947010215U, 955005519U, 962542061U, 969619844U, 976173331U, 982136987U, 987576349U, 992294706U, 15360U, 776354806U, 842939353U, 883243944U, 908016484U, 931871502U, 947010215U, 957561391U, 967326120U, 976173331U, 984037490U, 990787467U, 996423199U, 1000879269U, 1004089918U, 1005989446U, 15360U, 802569201U, 868629443U, 901921655U, 931871502U, 949697162U, 962542061U, 974076218U, 984037490U, 992294706U, 998782308U, 1003369219U, 1005989446U, 1006609992U, 1005236402U, 1001829444U, 15360U, 816987114U, 883243944U, 920075067U, 947010215U, 962542061U, 976173331U, 987576349U, 996423199U, 1002648518U, 1005989446U, 1006545480U, 1004122686U, 998815076U, 990820235U, 980269252U, 15360U, 830028770U, 895761288U, 937638646U, 957561391U, 974076218U, 987576349U, 997668290U, 1004089918U, 1006577224U, 1005236402U, 999929093U, 990820235U, 978303212U, 962574829U, 944290498U, 15360U, 842939353U, 908016484U, 947010215U, 967326120U, 984037490U, 996423199U, 1004089918U, 1006632960U, 1004122686U, 996455967U, 984070258U, 967358888U, 947042983U, 908049252U, 842972121U, 15360U, 855849934U, 920075067U, 955005519U, 976173331U, 992294706U, 1002648518U, 1006577224U, 1004122686U, 995145340U, 980269252U, 960150031U, 931904270U, 876919734U, 709409790U, 2977545186U, 15360U, 868629443U, 931871502U, 962542061U, 984037490U, 998782308U, 1005989446U, 1005236402U, 996455967U, 980269252U, 957594159U, 920107835U, 842972121U, 2856893438U, 3030760360U, 3088956125U, 15360U, 876886966U, 941439709U, 969619844U, 990787467U, 1003369219U, 1006545480U, 999929093U, 984070258U, 960150031U, 920107835U, 830061538U, 2923871222U, 3049438071U, 3099900525U, 3125786860U, 15360U, 883243944U, 947010215U, 976173331U, 996423199U, 1005989446U, 1004122686U, 990820235U, 967358888U, 931904270U, 842972121U, 2923871222U, 3055532900U, 3105077807U, 3131553906U, 3148395685U, 15360U, 889535385U, 952384109U, 982136987U, 1000879269U, 1006609992U, 998815076U, 978303212U, 947042983U, 876919734U, 2856893438U, 3049438071U, 3105077807U, 3133323336U, 3150164934U, 3153734837U, 15360U, 895761288U, 957561391U, 987576349U, 1004089918U, 1005236402U, 990820235U, 962574829U, 908049252U, 709409790U, 3030760360U, 3099900525U, 3131553906U, 3150164934U, 3153473094U, 3141220055U, 15360U, 901921655U, 962542061U, 992294706U, 1005989446U, 1001829444U, 980269252U, 944290498U, 842972121U, 2977545186U, 3088956125U, 3125786860U, 3148395685U, 3153734837U, 3141220055U, 3112450507U } };

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


#line 302 "mm_256_fusedTierB_c16p8.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_rowWin_0;
    uint _stgBase_0;
    uint _tid_0;
    uint _binPhase_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 229
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 90 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 232 "mm_256_fusedTierB_c16p8.slang"
    if(_S3 == 0U)
    {

#line 232
        return;
    }

#line 233
    uint _S4 = 3U * d_0;

#line 233
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



uint mfDataScaleFlag_0()
{
    ;
    uint _S6 = ((MF_DATA_SCALE_BITS));

#line 69
    return _S6;
}


#line 171 "mm_256_fusedTierB_c16p8.slang"
half2 cload_0(uint device* b_0, uint i_0)
{

#line 172
    uint p_0 = b_0[i_0];

#line 172
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 257
half2 dload_0(uint device* b_1, uint i_1)
{

#line 63 "twiddle.slang"
    uint _S7 = mfDataStrideFlag_0();

#line 259 "mm_256_fusedTierB_c16p8.slang"
    if(_S7 != 0U)
    {

#line 71 "twiddle.slang"
        uint _S8 = mfDataScaleFlag_0();

#line 260 "mm_256_fusedTierB_c16p8.slang"
        float s_0 = (as_type<float>((_S8)));
        uint _S9 = 2U * i_1;

#line 261
        return half2(half((as_type<float>((b_1[_S9]))) * s_0), half((as_type<float>((b_1[_S9 + 1U]))) * s_0));
    }
    return cload_0(b_1, i_1);
}


#line 325
half2 cmulConj_0(half2 a_0, half2 b_2)
{

#line 325
    half _S10 = a_0.x;

#line 325
    half _S11 = b_2.x;

#line 325
    half _S12 = a_0.y;

#line 325
    half _S13 = b_2.y;

#line 325
    return half2(_S10 * _S11 + _S12 * _S13, _S12 * _S11 - _S10 * _S13);
}


#line 501
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 503
    half2 t1_0 = *a_1 - *c_0;

#line 503
    half2 t2_0 = *b_3 + *d_1;

#line 503
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 505
    *b_3 = t1_0 + j3_0;

#line 505
    *c_0 = t0_0 - t2_0;

#line 505
    *d_1 = t1_0 - j3_0;
    return;
}


#line 324
half2 cmul_0(half2 a_2, half2 b_4)
{

#line 324
    half _S14 = a_2.x;

#line 324
    half _S15 = b_4.x;

#line 324
    half _S16 = a_2.y;

#line 324
    half _S17 = b_4.y;

#line 324
    return half2(_S14 * _S15 - _S16 * _S17, _S14 * _S17 + _S16 * _S15);
}


#line 537
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125h, 0.382568359375h);
    half2 W2_0 = half2(0.70703125h, 0.70703125h);
    half2 W3_0 = half2(0.382568359375h, 0.923828125h);
    half2 W4_0 = half2(0.0h, 1.0h);
    half2 W6_0 = half2(-0.70703125h, 0.70703125h);
    half2 W9_0 = half2(-0.923828125h, -0.382568359375h);

#line 544
    uint n1_0 = 0U;
    for(;;)
    {

#line 545
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 545
            break;
        }

#line 545
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 545
        n1_0 = n1_0 + 1U;

#line 545
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 546
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 546
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 547
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 547
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 548
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 548
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 548
    uint k2_0 = 0U;
    for(;;)
    {

#line 549
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 549
            break;
        }

#line 549
        uint _S18 = 4U * k2_0;

#line 549
        r4_0(&(*r_0)[_S18], &(*r_0)[_S18 + 1U], &(*r_0)[_S18 + 2U], &(*r_0)[_S18 + 3U]);

#line 549
        k2_0 = k2_0 + 1U;

#line 549
    }

    half2 t_0 = (*r_0)[int(1)];

#line 551
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 551
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 552
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 552
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 553
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 553
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 554
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 554
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 555
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 555
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 556
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 556
    (*r_0)[int(14)] = t_5;
    return;
}


#line 537
void dft16_1(array<half2, int(16)> thread* r_1)
{
    half2 W1_1 = half2(0.923828125h, 0.382568359375h);
    half2 W2_1 = half2(0.70703125h, 0.70703125h);
    half2 W3_1 = half2(0.382568359375h, 0.923828125h);
    half2 W4_1 = half2(0.0h, 1.0h);
    half2 W6_1 = half2(-0.70703125h, 0.70703125h);
    half2 W9_1 = half2(-0.923828125h, -0.382568359375h);

#line 544
    uint n1_1 = 0U;
    for(;;)
    {

#line 545
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 545
            break;
        }

#line 545
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 545
        n1_1 = n1_1 + 1U;

#line 545
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 546
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 546
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 547
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 547
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 548
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 548
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 548
    uint k2_1 = 0U;
    for(;;)
    {

#line 549
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 549
            break;
        }

#line 549
        uint _S19 = 4U * k2_1;

#line 549
        r4_0(&(*r_1)[_S19], &(*r_1)[_S19 + 1U], &(*r_1)[_S19 + 2U], &(*r_1)[_S19 + 3U]);

#line 549
        k2_1 = k2_1 + 1U;

#line 549
    }

    half2 t_6 = (*r_1)[int(1)];

#line 551
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 551
    (*r_1)[int(4)] = t_6;
    half2 t_7 = (*r_1)[int(2)];

#line 552
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 552
    (*r_1)[int(8)] = t_7;
    half2 t_8 = (*r_1)[int(3)];

#line 553
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 553
    (*r_1)[int(12)] = t_8;
    half2 t_9 = (*r_1)[int(6)];

#line 554
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 554
    (*r_1)[int(9)] = t_9;
    half2 t_10 = (*r_1)[int(7)];

#line 555
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 555
    (*r_1)[int(13)] = t_10;
    half2 t_11 = (*r_1)[int(11)];

#line 556
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 556
    (*r_1)[int(14)] = t_11;
    return;
}


#line 47 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S20 = ((MF_COARSE_TWT));

#line 50
    return _S20;
}


#line 74
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S21 = ((MF_ACCURATE_TRIG));

#line 77
    return _S21;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S22 = mfAccurateTrigFlag_0();

#line 103
    if(_S22 == 0U)
    {

#line 104
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S23 = float(quadrant_0);
    float x_0 = angle_0 - _S23 * 1.57079625129699707f - _S23 * 7.54978941586159635e-08f;
    float z_0 = x_0 * x_0;
    float c_1 = 1.0f + z_0 * (-0.5f + z_0 * (0.0416666679084301f + z_0 * (-0.00138888892251998f + z_0 * (0.00002480158764229f + z_0 * -2.75573199814971304e-07f))));

    float s_1 = x_0 * (1.0f + z_0 * (-0.1666666716337204f + z_0 * (0.00833333376795053f + z_0 * (-0.0001984127011383f + z_0 * (2.75573188446287531e-06f + z_0 * -2.50521079436794025e-08f)))));


    switch(quadrant_0 & int(3))
    {
    case int(1):
        {

#line 117
            return float2(- s_1, c_1);
        }
    case int(2):
        {

#line 118
            return float2(- c_1, - s_1);
        }
    case int(3):
        {

#line 119
            return float2(s_1, - c_1);
        }
    default:
        {

#line 120
            return float2(c_1, s_1);
        }
    }

#line 120
}


#line 326 "mm_256_fusedTierB_c16p8.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S24 = max(TB_0, 1U);

#line 328
    uint j_0 = d_2 / _S24;

#line 328
    uint m_0 = d_2 % _S24;

#line 328
    uint _S25;
    if(TB_0 <= 16U)
    {

#line 329
        _S25 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 329
    }
    else
    {

#line 329
        _S25 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 329
    }

#line 329
    return _S25;
}


#line 302
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 302
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 302
    return;
}


#line 303
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_2)
{

#line 303
    return half2(as_type<half>(ushort(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 726
void exchange_0(array<half2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_3)
{

#line 727
    uint j_1;

#line 738
    thread array<half2, int(16)> out_0;

#line 738
    uint z_1 = 0U;
    for(;;)
    {

#line 739
        if(z_1 < 16U)
        {
        }
        else
        {

#line 739
            break;
        }

#line 739
        out_0[z_1] = half2(0.0h, 0.0h);

#line 739
        z_1 = z_1 + 1U;

#line 739
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S26 = p0_0 & lenMask_0;

#line 745
    uint _S27 = (_S26 >> lgSpan_0) * 16U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S26 & spanMask_0);

#line 745
    uint c_2 = 0U;

    for(;;)
    {

#line 747
        if(c_2 < 1U)
        {
        }
        else
        {

#line 747
            break;
        }

#line 748
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 748
        j_1 = 0U;
        for(;;)
        {

#line 749
            if(j_1 < 16U)
            {
            }
            else
            {

#line 749
                break;
            }

#line 749
            stgPut_0(j_1 * 16U + kernelContext_3->_tid_0, (*r_2)[c_2 * 16U + j_1], kernelContext_3);

#line 749
            j_1 = j_1 + 1U;

#line 749
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 750
        uint d_3 = 0U;
        for(;;)
        {

#line 751
            if(d_3 < 16U)
            {
            }
            else
            {

#line 751
                break;
            }

#line 752
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S28 = pz_0 & lenMask_0;
            uint az_0 = (_S28 >> lgSpan_0) * 16U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S28 & spanMask_0);

#line 754
            half2 _S29 = stgGet_0(_S27 + az_0 - c_2 * 16U * 16U, kernelContext_3);


            out_0[d_3] = _S29;

#line 751
            d_3 = d_3 + 1U;

#line 751
        }

#line 747
        c_2 = c_2 + 1U;

#line 747
    }

#line 747
    j_1 = 0U;

#line 760
    for(;;)
    {

#line 760
        if(j_1 < 16U)
        {
        }
        else
        {

#line 760
            break;
        }

#line 760
        (*r_2)[j_1] = out_0[j_1];

#line 760
        j_1 = j_1 + 1U;

#line 760
    }
    return;
}


#line 640
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 647
    dft16_1(r_3);

#line 652
    return;
}


#line 831
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_4)
{

#line 11 "fft_transform.slang"
    uint lgTB_0 = firstbithigh_0(16U);
    uint lgLn_0 = firstbithigh_0(256U);
    uint blk_2 = tid_0 >> lgTB_0;
    uint lane_2 = tid_0 & 15U;


    dft16_0(r_4);

#line 52 "twiddle.slang"
    uint _S30 = mfCoarseTwtFlag_0();

#line 52
    uint k2_2;

#line 27 "fft_transform.slang"
    if(_S30 != 0U)
    {

#line 27
        k2_2 = 0U;


        for(;;)
        {

#line 30
            if(k2_2 < 16U)
            {
            }
            else
            {

#line 30
                break;
            }

#line 31
            uint _S31 = lane_2 * 16U + k2_2;

#line 31
            (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], half2(as_type<half>(ushort((COARSE_TWT_DATA_0[_S31]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S31]) >> 16U) & 65535U))));

#line 30
            k2_2 = k2_2 + 1U;

#line 30
        }

#line 27
    }
    else
    {

#line 39
        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 256.0f);
        float _S32 = tw_0.x;

#line 40
        float _S33 = tw_0.y;

#line 40
        k2_2 = 0U;

#line 40
        float cr_0 = 1.0f;

#line 40
        float ci_0 = 0.0f;

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
            (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], half2(half(cr_0), half(ci_0)));
            float nr_0 = cr_0 * _S32 - ci_0 * _S33;
            float _S34 = cr_0 * _S33 + ci_0 * _S32;

#line 42
            k2_2 = k2_2 + 1U;

#line 42
            cr_0 = nr_0;

#line 42
            ci_0 = _S34;

#line 42
        }

#line 27
    }

#line 50
    uint per_2 = 16U / max(16U, 1U);
    uint _S35 = max(1U, 1U);
    uint blk2_2 = tid_0 / _S35;

#line 52
    uint lane2_2 = tid_0 % _S35;

#line 52
    exchange_0(r_4, lgLn_0, lgTB_0, 16U, 256U, blk_2, lane_2, per_2, _S35, 16U, blk2_2, lane2_2, kernelContext_4);



    innermost_0(r_4);

#line 834 "mm_256_fusedTierB_c16p8.slang"
    return;
}


#line 785
uint lgOf_0(uint i_4)
{

#line 785
    uint _S36;

#line 785
    if(i_4 < 1U)
    {

#line 785
        _S36 = 4U;

#line 785
    }
    else
    {

#line 785
        if(i_4 == 1U)
        {

#line 785
            _S36 = 4U;

#line 785
        }
        else
        {

#line 785
            _S36 = 1U;

#line 785
        }

#line 785
    }

#line 785
    return _S36;
}


#line 787
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 791
    uint lg_1 = lgOf_0(0U);

#line 796
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}




uint c16Mag_0(half2 v_1, uint slot_1, uint ws_0, uint we_0, bool ov_0)
{
    uint idx_0 = slotToIndex_0(slot_1);

#line 804
    bool live_0;
    if(idx_0 >= ws_0)
    {

#line 805
        live_0 = idx_0 < we_0;

#line 805
    }
    else
    {

#line 805
        live_0 = false;

#line 805
    }
    uint nonfin_0 = ((((uint(as_type<ushort>(v_1[0U])) & 65535U) | (uint(as_type<ushort>(v_1[1U])) << 16U)) & 2080406528U) + 67109888U) & 2147516416U;
    float x_1 = float(v_1.x);

#line 807
    float y_0 = float(v_1.y);

#line 807
    uint m_1;
    if(live_0)
    {

#line 808
        m_1 = min((as_type<uint>((x_1 * x_1 + y_0 * y_0))), 2139095040U);

#line 808
    }
    else
    {

#line 808
        m_1 = 0U;

#line 808
    }

#line 808
    bool _S37;
    if(ov_0)
    {

#line 809
        _S37 = true;

#line 809
    }
    else
    {

#line 809
        _S37 = nonfin_0 != 0U;

#line 809
    }

#line 809
    if(_S37)
    {
    }
    else
    {

#line 809
        live_0 = false;

#line 809
    }

#line 809
    if(live_0)
    {

#line 809
        m_1 = 2139095040U;

#line 809
    }

#line 809
    return m_1;
}


#line 840
void filterOne_0(uint pair_0, uint d_4, uint t_12, uint tid_1, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{

#line 881
    thread array<half2, int(16)> r_5;

#line 881
    uint n2_0 = 0U;



    for(;;)
    {

#line 885
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 885
            break;
        }

#line 886
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_12 * 256U + tid_1 + 16U * n2_0));

#line 885
        n2_0 = n2_0 + 1U;

#line 885
    }

#line 885
    transform_0(&r_5, tid_1, kernelContext_5);

#line 911
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1021
    bool _S38 = tid_1 == 0U;

#line 1021
    if(_S38)
    {

#line 1021
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 1021
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 1021
    }

#line 1026
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1026
    uint i_5 = 0U;

#line 1026
    uint ovAcc_0 = 0U;

#line 1040
    for(;;)
    {

#line 1040
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1040
            break;
        }

#line 1041
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_5][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_5][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1040
        i_5 = i_5 + 1U;

#line 1040
        ovAcc_0 = ovAcc_1;

#line 1040
    }

    bool _S39 = (ovAcc_0 & 2147516416U) != 0U;

#line 1048
    half2 _S40 = half2(0.0h, 0.0h);

#line 1048
    uint bestBits_0 = thrBits_1;

#line 1048
    uint bestSlot_0 = 4294967295U;

#line 1048
    half2 bestV_0 = _S40;

#line 1048
    i_5 = 0U;
    for(;;)
    {

#line 1049
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1049
            break;
        }

#line 1050
        uint _S41 = tid_1 * 16U + i_5;

#line 1050
        uint m_2 = c16Mag_0(r_5[i_5], _S41, winStart_2, winEnd_2, _S39);
        if(m_2 > bestBits_0)
        {

#line 1051
            bestBits_0 = m_2;

#line 1051
            bestSlot_0 = _S41;

#line 1051
            bestV_0 = r_5[i_5];

#line 1051
        }

#line 1049
        i_5 = i_5 + 1U;

#line 1049
    }

#line 1057
    if(bestBits_0 > thrBits_1)
    {

#line 1057
        uint _S42 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), bestBits_0, memory_order_relaxed);

#line 1057
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    uint best_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1061
    bool _S43;
    if(bestSlot_0 != 4294967295U)
    {

#line 1062
        _S43 = bestBits_0 == best_0;

#line 1062
    }
    else
    {

#line 1062
        _S43 = false;

#line 1062
    }

#line 1062
    uint winner_0;

#line 1062
    if(_S43)
    {

#line 1062
        winner_0 = bestSlot_0;

#line 1062
    }
    else
    {

#line 1062
        winner_0 = 4294967295U;

#line 1062
    }

#line 1068
    bool _S44 = winner_0 != 4294967295U;

#line 1068
    if(_S44)
    {

#line 1068
        uint _S45 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 1068
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);
    uint wslot_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U];

    bool _S46 = pair_0 != 4294967295U;

#line 1073
    if(_S46)
    {

#line 1073
        _S43 = _S44;

#line 1073
    }
    else
    {

#line 1073
        _S43 = false;

#line 1073
    }

#line 1073
    if(_S43)
    {

#line 1073
        _S43 = winner_0 == wslot_0;

#line 1073
    }
    else
    {

#line 1073
        _S43 = false;

#line 1073
    }

#line 1073
    if(_S43)
    {

#line 1074
        *(peakIdx_0+pair_0) = int(slotToIndex_0(wslot_0));

#line 1074
        packed_float2 device* _S47 = peakVal_0+pair_0;

#line 1074
        float2 _S48;

        if(best_0 >= 2139095040U)
        {

#line 1076
            _S48 = float2(3.40282306073709653e+38f, 0.0f);

#line 1076
        }
        else
        {

#line 1076
            _S48 = float2(float(bestV_0.x), float(bestV_0.y));

#line 1076
        }

#line 1076
        *_S47 = packed_float2(_S48) ;

#line 1073
    }

#line 1079
    if(_S46)
    {

#line 1079
        _S43 = _S38;

#line 1079
    }
    else
    {

#line 1079
        _S43 = false;

#line 1079
    }

#line 1079
    if(_S43)
    {

#line 1079
        _S43 = wslot_0 == 4294967295U;

#line 1079
    }
    else
    {

#line 1079
        _S43 = false;

#line 1079
    }

#line 1079
    if(_S43)
    {

#line 1080
        *(peakIdx_0+pair_0) = int(-1);

#line 1080
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1079
    }

#line 1234
    return;
}


#line 1597
void filterPair_0(uint pair_1, uint tid_2, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, uint device* rowWin_1, KernelContext_0 thread* kernelContext_6)
{

#line 1597
    thread uint _S49 = winStart_3;

#line 1597
    thread uint _S50 = winEnd_3;

#line 1603
    kernelContext_6->_tid_0 = tid_2;

#line 1637
    uint pairs_0 = binsize_2 * ntmpl_1;
    bool slotOk_0 = pair_1 < pairs_0;

#line 1638
    uint q_0;
    if(slotOk_0)
    {

#line 1639
        q_0 = pair_1;

#line 1639
    }
    else
    {

#line 1639
        q_0 = pairs_0 - 1U;

#line 1639
    }

#line 1639
    uint _S51;
    if(slotOk_0)
    {

#line 1640
        _S51 = q_0;

#line 1640
    }
    else
    {

#line 1640
        _S51 = 4294967295U;

#line 1640
    }
    uint d_5 = q_0 / ntmpl_1;

#line 1641
    uint _S52 = q_0 - d_5 * ntmpl_1;

#line 1641
    rowWindow_0(d_5, &_S49, &_S50, rowWin_1, kernelContext_6);

#line 1653
    thread array<half2, int(16)> dreg_1;

#line 1653
    uint n2_1 = 0U;

    for(;;)
    {

#line 1655
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1655
            break;
        }

#line 63 "twiddle.slang"
        uint _S53 = mfDataStrideFlag_0();

#line 178 "mm_256_fusedTierB_c16p8.slang"
        if(_S53 != 0U)
        {

#line 63 "twiddle.slang"
            uint _S54 = mfDataStrideFlag_0();

#line 63
            q_0 = _S54;

#line 178 "mm_256_fusedTierB_c16p8.slang"
        }
        else
        {

#line 178
            q_0 = 256U;

#line 178
        }

#line 1656
        half2 _S55 = dload_0(data_1, d_5 * q_0 + tid_2 + 16U * n2_1);

#line 1656
        dreg_1[n2_1] = _S55;

#line 1655
        n2_1 = n2_1 + 1U;

#line 1655
    }

#line 1655
    uint k_0 = 0U;

#line 1675
    for(;;)
    {

#line 1675
        if(k_0 < 1U)
        {
        }
        else
        {

#line 1675
            break;
        }

#line 1676
        uint _S56 = _S51 + k_0;

#line 1676
        uint _S57 = _S52 + k_0;

#line 1676
        thread array<half2, int(16)> _S58 = dreg_1;

#line 1676
        filterOne_0(_S56, d_5, _S57, tid_2, &_S58, data_1, tmpl_1, peakIdx_1, peakVal_1, _S49, _S50, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1675
        k_0 = k_0 + 1U;

#line 1675
    }



    return;
}


#line 1692
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1692
    thread KernelContext_0 kernelContext_7;

#line 1692
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1692
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1692
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1692
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1692
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1692
    (&kernelContext_7)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1692
    threadgroup array<uint, int(2048)> stg_1;

#line 1692
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1692
    (&kernelContext_7)->_binPhase_0 = 0U;

#line 1712
    uint _S59 = lid_0.x;

#line 1712
    uint _sub_0 = _S59 / 16U;
    uint _pr_0 = gid_0.x * 8U + _sub_0;

#line 1713
    uint _t_0 = _S59 % 16U;
    (&kernelContext_7)->_stgBase_0 = _sub_0 * 256U;

#line 1714
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, entryPointParams_rowWin_1, &kernelContext_7);

#line 1727
    return;
}
