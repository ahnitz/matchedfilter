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

#line 10 "mm_256_fusedTierB_c16p4.slang"
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


#line 302 "mm_256_fusedTierB_c16p4.slang"
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
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 229
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 90 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 232 "mm_256_fusedTierB_c16p4.slang"
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


#line 171 "mm_256_fusedTierB_c16p4.slang"
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

#line 259 "mm_256_fusedTierB_c16p4.slang"
    if(_S7 != 0U)
    {

#line 71 "twiddle.slang"
        uint _S8 = mfDataScaleFlag_0();

#line 260 "mm_256_fusedTierB_c16p4.slang"
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


#line 584
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 586
    half2 t1_0 = *a_1 - *c_0;

#line 586
    half2 t2_0 = *b_3 + *d_1;

#line 586
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 588
    *b_3 = t1_0 + j3_0;

#line 588
    *c_0 = t0_0 - t2_0;

#line 588
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


#line 620
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125h, 0.382568359375h);
    half2 W2_0 = half2(0.70703125h, 0.70703125h);
    half2 W3_0 = half2(0.382568359375h, 0.923828125h);
    half2 W4_0 = half2(0.0h, 1.0h);
    half2 W6_0 = half2(-0.70703125h, 0.70703125h);
    half2 W9_0 = half2(-0.923828125h, -0.382568359375h);

#line 627
    uint n1_0 = 0U;
    for(;;)
    {

#line 628
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 628
            break;
        }

#line 628
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 628
        n1_0 = n1_0 + 1U;

#line 628
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 629
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 629
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 630
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 630
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 631
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 631
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 631
    uint k2_0 = 0U;
    for(;;)
    {

#line 632
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 632
            break;
        }

#line 632
        uint _S18 = 4U * k2_0;

#line 632
        r4_0(&(*r_0)[_S18], &(*r_0)[_S18 + 1U], &(*r_0)[_S18 + 2U], &(*r_0)[_S18 + 3U]);

#line 632
        k2_0 = k2_0 + 1U;

#line 632
    }

    half2 t_0 = (*r_0)[int(1)];

#line 634
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 634
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 635
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 635
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 636
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 636
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 637
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 637
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 638
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 638
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 639
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 639
    (*r_0)[int(14)] = t_5;
    return;
}


#line 620
void dft16_1(array<half2, int(16)> thread* r_1)
{
    half2 W1_1 = half2(0.923828125h, 0.382568359375h);
    half2 W2_1 = half2(0.70703125h, 0.70703125h);
    half2 W3_1 = half2(0.382568359375h, 0.923828125h);
    half2 W4_1 = half2(0.0h, 1.0h);
    half2 W6_1 = half2(-0.70703125h, 0.70703125h);
    half2 W9_1 = half2(-0.923828125h, -0.382568359375h);

#line 627
    uint n1_1 = 0U;
    for(;;)
    {

#line 628
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 628
            break;
        }

#line 628
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 628
        n1_1 = n1_1 + 1U;

#line 628
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 629
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 629
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 630
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 630
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 631
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 631
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 631
    uint k2_1 = 0U;
    for(;;)
    {

#line 632
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 632
            break;
        }

#line 632
        uint _S19 = 4U * k2_1;

#line 632
        r4_0(&(*r_1)[_S19], &(*r_1)[_S19 + 1U], &(*r_1)[_S19 + 2U], &(*r_1)[_S19 + 3U]);

#line 632
        k2_1 = k2_1 + 1U;

#line 632
    }

    half2 t_6 = (*r_1)[int(1)];

#line 634
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 634
    (*r_1)[int(4)] = t_6;
    half2 t_7 = (*r_1)[int(2)];

#line 635
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 635
    (*r_1)[int(8)] = t_7;
    half2 t_8 = (*r_1)[int(3)];

#line 636
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 636
    (*r_1)[int(12)] = t_8;
    half2 t_9 = (*r_1)[int(6)];

#line 637
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 637
    (*r_1)[int(9)] = t_9;
    half2 t_10 = (*r_1)[int(7)];

#line 638
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 638
    (*r_1)[int(13)] = t_10;
    half2 t_11 = (*r_1)[int(11)];

#line 639
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 639
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


#line 326 "mm_256_fusedTierB_c16p4.slang"
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


#line 723
void innermost_0(array<half2, int(16)> thread* r_2)
{

#line 730
    dft16_1(r_2);

#line 735
    return;
}


#line 870
uint lgOf_0(uint i_4)
{

#line 870
    uint _S26;

#line 870
    if(i_4 < 1U)
    {

#line 870
        _S26 = 4U;

#line 870
    }
    else
    {

#line 870
        if(i_4 == 1U)
        {

#line 870
            _S26 = 4U;

#line 870
        }
        else
        {

#line 870
            _S26 = 1U;

#line 870
        }

#line 870
    }

#line 870
    return _S26;
}


#line 872
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 876
    uint lg_1 = lgOf_0(0U);

#line 881
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}




uint c16Mag_0(half2 v_1, uint slot_1, uint ws_0, uint we_0, bool ov_0)
{
    uint idx_0 = slotToIndex_0(slot_1);

#line 889
    bool live_0;
    if(idx_0 >= ws_0)
    {

#line 890
        live_0 = idx_0 < we_0;

#line 890
    }
    else
    {

#line 890
        live_0 = false;

#line 890
    }
    uint nonfin_0 = ((((uint(as_type<ushort>(v_1[0U])) & 65535U) | (uint(as_type<ushort>(v_1[1U])) << 16U)) & 2080406528U) + 67109888U) & 2147516416U;
    float x_1 = float(v_1.x);

#line 892
    float y_0 = float(v_1.y);

#line 892
    uint m_1;
    if(live_0)
    {

#line 893
        m_1 = min((as_type<uint>((x_1 * x_1 + y_0 * y_0))), 2139095040U);

#line 893
    }
    else
    {

#line 893
        m_1 = 0U;

#line 893
    }

#line 893
    bool _S27;
    if(ov_0)
    {

#line 894
        _S27 = true;

#line 894
    }
    else
    {

#line 894
        _S27 = nonfin_0 != 0U;

#line 894
    }

#line 894
    if(_S27)
    {
    }
    else
    {

#line 894
        live_0 = false;

#line 894
    }

#line 894
    if(live_0)
    {

#line 894
        m_1 = 2139095040U;

#line 894
    }

#line 894
    return m_1;
}


#line 1767
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1767
    uint j_1;

#line 1767
    uint d_3;

#line 1767
    thread KernelContext_0 kernelContext_3;

#line 1767
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 1767
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1767
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1767
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1767
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1767
    (&kernelContext_3)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1767
    threadgroup array<uint, int(1024)> stg_1;

#line 1767
    (&kernelContext_3)->stg_0 = &stg_1;

#line 1767
    (&kernelContext_3)->_binPhase_0 = 0U;

#line 1787
    uint _S28 = lid_0.x;

#line 1787
    uint _sub_0 = _S28 / 16U;
    uint _pr_0 = gid_0.x * 4U + _sub_0;

#line 1788
    uint _t_0 = _S28 % 16U;
    (&kernelContext_3)->_stgBase_0 = _sub_0 * 256U;

#line 1789
    uint _S29 = entryPointParams_1->ntmpl_0;

#line 1789
    uint _S30 = entryPointParams_1->winStart_0;

#line 1789
    uint _S31 = entryPointParams_1->winEnd_0;

#line 1789
    uint _S32 = entryPointParams_1->binsize_0;

#line 1789
    uint _S33 = entryPointParams_1->thrBits_0;

#line 1799
    for(;;)
    {

#line 1799
        thread uint _S34 = _S30;

#line 1799
        thread uint _S35 = _S31;

#line 1799
        (&kernelContext_3)->_tid_0 = _t_0;

#line 1799
        uint pairs_0 = _S32 * _S29;

#line 1799
        bool slotOk_0 = _pr_0 < pairs_0;

#line 1799
        uint q_0;

#line 1799
        if(slotOk_0)
        {

#line 1799
            q_0 = _pr_0;

#line 1799
        }
        else
        {

#line 1799
            q_0 = pairs_0 - 1U;

#line 1799
        }

#line 1799
        uint _S36;

#line 1799
        if(slotOk_0)
        {

#line 1799
            _S36 = q_0;

#line 1799
        }
        else
        {

#line 1799
            _S36 = 4294967295U;

#line 1799
        }

#line 1799
        uint d_4 = q_0 / _S29;

#line 1799
        uint _S37 = q_0 - d_4 * _S29;

#line 1799
        rowWindow_0(d_4, &_S34, &_S35, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);

#line 1799
        thread array<half2, int(16)> dreg_0;

#line 1799
        uint n2_0 = 0U;

#line 1799
        for(;;)
        {

#line 1799
            if(n2_0 < 16U)
            {
            }
            else
            {

#line 1799
                break;
            }

#line 1799
            uint _S38 = mfDataStrideFlag_0();

#line 1799
            if(_S38 != 0U)
            {

#line 1799
                uint _S39 = mfDataStrideFlag_0();

#line 1799
                q_0 = _S39;

#line 1799
            }
            else
            {

#line 1799
                q_0 = 256U;

#line 1799
            }

#line 1799
            half2 _S40 = dload_0((&kernelContext_3)->entryPointParams_data_0, d_4 * q_0 + _t_0 + 16U * n2_0);

#line 1799
            dreg_0[n2_0] = _S40;

#line 1799
            n2_0 = n2_0 + 1U;

#line 1799
        }

#line 1799
        uint k_0 = 0U;

#line 1799
        for(;;)
        {

#line 1799
            if(k_0 < 1U)
            {
            }
            else
            {

#line 1799
                break;
            }

#line 1799
            uint _S41 = _S36 + k_0;

#line 1799
            uint _S42 = _S37 + k_0;

#line 1799
            uint _S43 = _S34;

#line 1799
            uint _S44 = _S35;

#line 1799
            for(;;)
            {

#line 1799
                thread array<half2, int(16)> r_3;

#line 1799
                n2_0 = 0U;

#line 1799
                for(;;)
                {

#line 1799
                    if(n2_0 < 16U)
                    {
                    }
                    else
                    {

#line 1799
                        break;
                    }

#line 1799
                    r_3[n2_0] = cmulConj_0(dreg_0[n2_0], cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S42 * 256U + _t_0 + 16U * n2_0));

#line 1799
                    n2_0 = n2_0 + 1U;

#line 1799
                }

#line 1799
                for(;;)
                {

#line 1799
                    for(;;)
                    {

#line 1799
                        uint lgTB_0 = firstbithigh_0(16U);

#line 1799
                        uint lgLn_0 = firstbithigh_0(256U);

#line 1799
                        uint blk_1 = _t_0 >> lgTB_0;

#line 1799
                        uint lane_1 = _t_0 & 15U;

#line 1799
                        dft16_0(&r_3);

#line 1799
                        uint _S45 = mfCoarseTwtFlag_0();

#line 1799
                        uint z_1;

#line 1799
                        if(_S45 != 0U)
                        {

#line 1799
                            z_1 = 0U;

#line 1799
                            for(;;)
                            {

#line 1799
                                if(z_1 < 16U)
                                {
                                }
                                else
                                {

#line 1799
                                    break;
                                }

#line 1799
                                uint _S46 = lane_1 * 16U + z_1;

#line 1799
                                r_3[z_1] = cmul_0(r_3[z_1], half2(as_type<half>(ushort((COARSE_TWT_DATA_0[_S46]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S46]) >> 16U) & 65535U))));

#line 1799
                                z_1 = z_1 + 1U;

#line 1799
                            }

#line 1799
                        }
                        else
                        {

#line 1799
                            float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 256.0f);

#line 1799
                            float _S47 = tw_0.x;

#line 1799
                            float _S48 = tw_0.y;

#line 1799
                            z_1 = 0U;

#line 1799
                            float cr_0 = 1.0f;

#line 1799
                            float ci_0 = 0.0f;

#line 1799
                            for(;;)
                            {

#line 1799
                                if(z_1 < 16U)
                                {
                                }
                                else
                                {

#line 1799
                                    break;
                                }

#line 1799
                                r_3[z_1] = cmul_0(r_3[z_1], half2(half(cr_0), half(ci_0)));

#line 1799
                                float nr_0 = cr_0 * _S47 - ci_0 * _S48;

#line 1799
                                float _S49 = cr_0 * _S48 + ci_0 * _S47;

#line 1799
                                z_1 = z_1 + 1U;

#line 1799
                                cr_0 = nr_0;

#line 1799
                                ci_0 = _S49;

#line 1799
                            }

#line 1799
                        }

#line 1799
                        uint per_1 = 16U / max(16U, 1U);

#line 1799
                        uint _S50 = max(1U, 1U);

#line 1799
                        uint blk2_1 = _t_0 / _S50;

#line 1799
                        uint lane2_1 = _t_0 % _S50;

#line 1799
                        for(;;)
                        {

#line 1799
                            thread array<half2, int(16)> out_0;

#line 1799
                            z_1 = 0U;

#line 1799
                            for(;;)
                            {

#line 1799
                                if(z_1 < 16U)
                                {
                                }
                                else
                                {

#line 1799
                                    break;
                                }

#line 1799
                                out_0[z_1] = half2(0.0h, 0.0h);

#line 1799
                                z_1 = z_1 + 1U;

#line 1799
                            }

#line 1799
                            uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 1799
                            uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1799
                            uint p0_0 = computeWant_0(0U, 16U, 256U, blk_1, lane_1, per_1, _S50, 16U, blk2_1, lane2_1);

#line 1799
                            uint _S51 = p0_0 & lenMask_0;

#line 1799
                            uint _S52 = (_S51 >> lgTB_0) * 16U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S51 & spanMask_0);

#line 1799
                            uint c_2 = 0U;

#line 1799
                            for(;;)
                            {

#line 1799
                                if(c_2 < 1U)
                                {
                                }
                                else
                                {

#line 1799
                                    break;
                                }

#line 1799
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1799
                                j_1 = 0U;

#line 1799
                                for(;;)
                                {

#line 1799
                                    if(j_1 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1799
                                        break;
                                    }

#line 1799
                                    stgPut_0(j_1 * 16U + (&kernelContext_3)->_tid_0, r_3[c_2 * 16U + j_1], &kernelContext_3);

#line 1799
                                    j_1 = j_1 + 1U;

#line 1799
                                }

#line 1799
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1799
                                d_3 = 0U;

#line 1799
                                for(;;)
                                {

#line 1799
                                    if(d_3 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1799
                                        break;
                                    }

#line 1799
                                    uint pz_0 = computeWant_0(d_3, 16U, 256U, 0U, 0U, per_1, _S50, 16U, 0U, 0U);

#line 1799
                                    uint _S53 = pz_0 & lenMask_0;

#line 1799
                                    uint az_0 = (_S53 >> lgTB_0) * 16U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S53 & spanMask_0);

#line 1799
                                    half2 _S54 = stgGet_0(_S52 + az_0 - c_2 * 16U * 16U, &kernelContext_3);

#line 1799
                                    out_0[d_3] = _S54;

#line 1799
                                    d_3 = d_3 + 1U;

#line 1799
                                }

#line 1799
                                c_2 = c_2 + 1U;

#line 1799
                            }

#line 1799
                            j_1 = 0U;

#line 1799
                            for(;;)
                            {

#line 1799
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 1799
                                    break;
                                }

#line 1799
                                r_3[j_1] = out_0[j_1];

#line 1799
                                j_1 = j_1 + 1U;

#line 1799
                            }

#line 1799
                            break;
                        }

#line 1799
                        break;
                    }

#line 1799
                    innermost_0(&r_3);

#line 1799
                    break;
                }

#line 1799
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1799
                bool _S55 = _t_0 == 0U;

#line 1799
                if(_S55)
                {

#line 1799
                    (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0] = _S33;

#line 1799
                    (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U] = 4294967295U;

#line 1799
                }

#line 1799
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1799
                d_3 = 0U;

#line 1799
                uint ovAcc_0 = 0U;

#line 1799
                for(;;)
                {

#line 1799
                    if(d_3 < 16U)
                    {
                    }
                    else
                    {

#line 1799
                        break;
                    }

#line 1799
                    uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_3[d_3][0U])) & 65535U) | (uint(as_type<ushort>(r_3[d_3][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1799
                    d_3 = d_3 + 1U;

#line 1799
                    ovAcc_0 = ovAcc_1;

#line 1799
                }

#line 1799
                bool _S56 = (ovAcc_0 & 2147516416U) != 0U;

#line 1799
                half2 _S57 = half2(0.0h, 0.0h);

#line 1799
                uint i_5 = 0U;

#line 1799
                uint bestBits_0 = _S33;

#line 1799
                uint bestSlot_0 = 4294967295U;

#line 1799
                half2 bestV_0 = _S57;

#line 1799
                for(;;)
                {

#line 1799
                    if(i_5 < 16U)
                    {
                    }
                    else
                    {

#line 1799
                        break;
                    }

#line 1799
                    uint _S58 = _t_0 * 16U + i_5;

#line 1799
                    uint m_2 = c16Mag_0(r_3[i_5], _S58, _S43, _S44, _S56);

#line 1799
                    if(m_2 > bestBits_0)
                    {

#line 1799
                        bestBits_0 = m_2;

#line 1799
                        bestSlot_0 = _S58;

#line 1799
                        bestV_0 = r_3[i_5];

#line 1799
                    }

#line 1799
                    i_5 = i_5 + 1U;

#line 1799
                }

#line 1799
                if(bestBits_0 > _S33)
                {

#line 1799
                    uint _S59 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), bestBits_0, memory_order_relaxed);

#line 1799
                }

#line 1799
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1799
                uint best_0 = (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0];

#line 1799
                bool _S60;

#line 1799
                if(bestSlot_0 != 4294967295U)
                {

#line 1799
                    _S60 = bestBits_0 == best_0;

#line 1799
                }
                else
                {

#line 1799
                    _S60 = false;

#line 1799
                }

#line 1799
                uint winner_0;

#line 1799
                if(_S60)
                {

#line 1799
                    winner_0 = bestSlot_0;

#line 1799
                }
                else
                {

#line 1799
                    winner_0 = 4294967295U;

#line 1799
                }

#line 1799
                bool _S61 = winner_0 != 4294967295U;

#line 1799
                if(_S61)
                {

#line 1799
                    uint _S62 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 1799
                }

#line 1799
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1799
                uint wslot_0 = (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U];

#line 1799
                bool _S63 = _S41 != 4294967295U;

#line 1799
                bool _S64;

#line 1799
                if(_S63)
                {

#line 1799
                    _S64 = _S61;

#line 1799
                }
                else
                {

#line 1799
                    _S64 = false;

#line 1799
                }

#line 1799
                bool _S65;

#line 1799
                if(_S64)
                {

#line 1799
                    _S65 = winner_0 == wslot_0;

#line 1799
                }
                else
                {

#line 1799
                    _S65 = false;

#line 1799
                }

#line 1799
                if(_S65)
                {

#line 1799
                    *((&kernelContext_3)->entryPointParams_peakIdx_0+_S41) = int(slotToIndex_0(wslot_0));

#line 1799
                    packed_float2 device* _S66 = (&kernelContext_3)->entryPointParams_peakVal_0+_S41;

#line 1799
                    float2 _S67;

#line 1799
                    if(best_0 >= 2139095040U)
                    {

#line 1799
                        _S67 = float2(3.40282306073709653e+38f, 0.0f);

#line 1799
                    }
                    else
                    {

#line 1799
                        _S67 = float2(float(bestV_0.x), float(bestV_0.y));

#line 1799
                    }

#line 1799
                    *_S66 = packed_float2(_S67) ;

#line 1799
                }

#line 1799
                bool _S68;

#line 1799
                if(_S63)
                {

#line 1799
                    _S68 = _S55;

#line 1799
                }
                else
                {

#line 1799
                    _S68 = false;

#line 1799
                }

#line 1799
                bool _S69;

#line 1799
                if(_S68)
                {

#line 1799
                    _S69 = wslot_0 == 4294967295U;

#line 1799
                }
                else
                {

#line 1799
                    _S69 = false;

#line 1799
                }

#line 1799
                if(_S69)
                {

#line 1799
                    *((&kernelContext_3)->entryPointParams_peakIdx_0+_S41) = int(-1);

#line 1799
                    *((&kernelContext_3)->entryPointParams_peakVal_0+_S41) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1799
                }

#line 1799
                break;
            }

#line 1799
            k_0 = k_0 + 1U;

#line 1799
        }

#line 1799
        break;
    }

    return;
}
