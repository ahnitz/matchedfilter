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

#line 10 "mm_512_fusedTierB_c16p2.slang"
constant array<uint, int(544)> COARSE_TWT_DATA_0 = { { 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 575159296U, 642268159U, 683031551U, 709377022U, 735656956U, 750074874U, 763247608U, 776354806U, 789462004U, 802569201U, 810433517U, 816987114U, 823475174U, 830028770U, 836451293U, 15360U, 642268159U, 709377022U, 750074874U, 776354806U, 802569201U, 816987114U, 830028770U, 842939353U, 855849934U, 868629443U, 876886966U, 883243944U, 889535385U, 895761288U, 901921655U, 15360U, 683031551U, 750074874U, 789462004U, 816987114U, 836451293U, 855849934U, 873741244U, 883243944U, 892615569U, 901921655U, 911096666U, 920075067U, 928922394U, 937638646U, 942815952U, 15360U, 709377022U, 776354806U, 816987114U, 842939353U, 868629443U, 883243944U, 895761288U, 908016484U, 920075067U, 931871502U, 941439709U, 947010215U, 952384109U, 957561391U, 962542061U, 15360U, 735656956U, 802569201U, 836451293U, 868629443U, 886389664U, 901921655U, 917125958U, 931871502U, 942815952U, 949697162U, 956316223U, 962542061U, 968505750U, 974076218U, 979253464U, 15360U, 750074874U, 816987114U, 855849934U, 883243944U, 901921655U, 920075067U, 937638646U, 947010215U, 955005519U, 962542061U, 969619844U, 976173331U, 982136987U, 987576349U, 992294706U, 15360U, 763247608U, 830028770U, 873741244U, 895761288U, 917125958U, 937638646U, 948386457U, 957561391U, 966146490U, 974076218U, 981219504U, 987576349U, 993015557U, 997668290U, 1001337973U, 15360U, 776354806U, 842939353U, 883243944U, 908016484U, 931871502U, 947010215U, 957561391U, 967326120U, 976173331U, 984037490U, 990787467U, 996423199U, 1000879269U, 1004089918U, 1005989446U, 15360U, 789462004U, 855849934U, 892615569U, 920075067U, 942815952U, 955005519U, 966146490U, 976173331U, 984954973U, 992294706U, 998258067U, 1002648518U, 1005400142U, 1006577224U, 1006153086U, 15360U, 802569201U, 868629443U, 901921655U, 931871502U, 949697162U, 962542061U, 974076218U, 984037490U, 992294706U, 998782308U, 1003369219U, 1005989446U, 1006609992U, 1005236402U, 1001829444U, 15360U, 810433517U, 876886966U, 911096666U, 941439709U, 956316223U, 969619844U, 981219504U, 990787467U, 998258067U, 1003369219U, 1006120318U, 1006545480U, 1004384731U, 999929093U, 993048325U, 15360U, 816987114U, 883243944U, 920075067U, 947010215U, 962542061U, 976173331U, 987576349U, 996423199U, 1002648518U, 1005989446U, 1006545480U, 1004122686U, 998815076U, 990820235U, 980269252U, 15360U, 823475174U, 889535385U, 928922394U, 952384109U, 968505750U, 982136987U, 993015557U, 1000879269U, 1005400142U, 1006609992U, 1004384731U, 998815076U, 990033847U, 978303212U, 963819996U, 15360U, 830028770U, 895761288U, 937638646U, 957561391U, 974076218U, 987576349U, 997668290U, 1004089918U, 1006577224U, 1005236402U, 999929093U, 990820235U, 978303212U, 962574829U, 944290498U, 15360U, 836451293U, 901921655U, 942815952U, 962542061U, 979253464U, 992294706U, 1001337973U, 1005989446U, 1006153086U, 1001829444U, 993048325U, 980269252U, 963819996U, 944290498U, 905034606U, 15360U, 842939353U, 908016484U, 947010215U, 967326120U, 984037490U, 996423199U, 1004089918U, 1006632960U, 1004122686U, 996455967U, 984070258U, 967358888U, 947042983U, 908049252U, 842972121U, 15360U, 849427412U, 914111312U, 951073404U, 971848031U, 988362759U, 999896325U, 1005858574U, 1006022214U, 1000387797U, 989247459U, 972994893U, 952416877U, 917158726U, 855882702U, 575192064U, 15360U, 855849934U, 920075067U, 955005519U, 976173331U, 992294706U, 1002648518U, 1006577224U, 1004122686U, 995145340U, 980269252U, 960150031U, 931904270U, 876919734U, 709409790U, 2977545186U, 15360U, 862272457U, 926038821U, 958872095U, 980236484U, 995767886U, 1004679545U, 1006414809U, 1000912037U, 988395527U, 969652612U, 945666741U, 895794056U, 789494772U, 2950085617U, 3046357888U, 15360U, 868629443U, 931871502U, 962542061U, 984037490U, 998782308U, 1005989446U, 1005236402U, 996455967U, 980269252U, 957594159U, 920107835U, 842972121U, 2856893438U, 3030760360U, 3088956125U, 15360U, 873741244U, 937638646U, 966146490U, 987576349U, 1001337973U, 1006577224U, 1003074405U, 990820235U, 970766706U, 944290498U, 886422432U, 709409790U, 2996943828U, 3073555237U, 3108878846U, 15360U, 876886966U, 941439709U, 969619844U, 990787467U, 1003369219U, 1006545480U, 999929093U, 984070258U, 960150031U, 920107835U, 830061538U, 2923871222U, 3049438071U, 3099900525U, 3125786860U, 15360U, 880098223U, 944257730U, 972962125U, 993736407U, 1004941589U, 1005694934U, 995800654U, 976206099U, 948419225U, 889568153U, 683064319U, 3016145859U, 3087514345U, 3117136260U, 3139090270U, 15360U, 883243944U, 947010215U, 976173331U, 996423199U, 1005989446U, 1004122686U, 990820235U, 967358888U, 931904270U, 842972121U, 2923871222U, 3055532900U, 3105077807U, 3131553906U, 3148395685U, 15360U, 886389664U, 949697162U, 979253464U, 998782308U, 1006577846U, 1001829444U, 984987741U, 957594159U, 905034606U, 750107642U, 3009788873U, 3088956125U, 3120478541U, 3142628988U, 3153374990U, 15360U, 889535385U, 952384109U, 982136987U, 1000879269U, 1006609992U, 998815076U, 978303212U, 947042983U, 876919734U, 2856893438U, 3049438071U, 3105077807U, 3133323336U, 3150164934U, 3153734837U, 15360U, 892615569U, 955005519U, 984954973U, 1002648518U, 1006153086U, 995145340U, 970766706U, 931904270U, 823507942U, 2977545186U, 3082271490U, 3119364447U, 3143284302U, 3153767605U, 3149673492U, 15360U, 895761288U, 957561391U, 987576349U, 1004089918U, 1005236402U, 990820235U, 962574829U, 908049252U, 709409790U, 3030760360U, 3099900525U, 3131553906U, 3150164934U, 3153473094U, 3141220055U, 15360U, 898841472U, 960117263U, 990001079U, 1005203634U, 1003795105U, 985839688U, 953727582U, 883276712U, 2883173372U, 3061627728U, 3113662906U, 3141252823U, 3153636734U, 3149280324U, 3128703152U, 15360U, 901921655U, 962542061U, 992294706U, 1005989446U, 1001829444U, 980269252U, 944290498U, 842972121U, 2977545186U, 3088956125U, 3125786860U, 3148395685U, 3153734837U, 3141220055U, 3112450507U, 15360U, 905001838U, 964966859U, 994457258U, 1006512712U, 999404852U, 974108986U, 928955162U, 776387574U, 3027614639U, 3102521935U, 3135879175U, 3152720050U, 3150525285U, 3129620635U, 3093117621U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 842939353U, 908016484U, 947010215U, 967326120U, 984037490U, 996423199U, 1004089918U, 1006632960U, 1004122686U, 996455967U, 984070258U, 967358888U, 947042983U, 908049252U, 842972121U } };

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


#line 302 "mm_512_fusedTierB_c16p2.slang"
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

#line 232 "mm_512_fusedTierB_c16p2.slang"
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


#line 171 "mm_512_fusedTierB_c16p2.slang"
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

#line 259 "mm_512_fusedTierB_c16p2.slang"
    if(_S7 != 0U)
    {

#line 71 "twiddle.slang"
        uint _S8 = mfDataScaleFlag_0();

#line 260 "mm_512_fusedTierB_c16p2.slang"
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


#line 47 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S19 = ((MF_COARSE_TWT));

#line 50
    return _S19;
}


#line 74
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S20 = ((MF_ACCURATE_TRIG));

#line 77
    return _S20;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S21 = mfAccurateTrigFlag_0();

#line 103
    if(_S21 == 0U)
    {

#line 104
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S22 = float(quadrant_0);
    float x_0 = angle_0 - _S22 * 1.57079625129699707f - _S22 * 7.54978941586159635e-08f;
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


#line 326 "mm_512_fusedTierB_c16p2.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S23 = max(TB_0, 1U);

#line 328
    uint j_0 = d_2 / _S23;

#line 328
    uint m_0 = d_2 % _S23;

#line 328
    uint _S24;
    if(TB_0 <= 16U)
    {

#line 329
        _S24 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 329
    }
    else
    {

#line 329
        _S24 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 329
    }

#line 329
    return _S24;
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
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_3)
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
    uint _S25 = p0_0 & lenMask_0;

#line 745
    uint _S26 = (_S25 >> lgSpan_0) * 32U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S25 & spanMask_0);

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
            stgPut_0(j_1 * 32U + kernelContext_3->_tid_0, (*r_1)[c_2 * 16U + j_1], kernelContext_3);

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
            uint _S27 = pz_0 & lenMask_0;
            uint az_0 = (_S27 >> lgSpan_0) * 32U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S27 & spanMask_0);

#line 754
            half2 _S28 = stgGet_0(_S26 + az_0 - c_2 * 16U * 32U, kernelContext_3);


            out_0[d_3] = _S28;

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
        (*r_1)[j_1] = out_0[j_1];

#line 760
        j_1 = j_1 + 1U;

#line 760
    }
    return;
}


#line 512
void dft2_0(array<half2, int(16)> thread* r_2, uint o_0)
{
    half2 a_3 = (*r_2)[o_0];

#line 514
    half2 b_5 = (*r_2)[o_0 + 1U];

#line 514
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 514
    (*r_2)[o_0 + 1U] = a_3 - b_5;
    return;
}


#line 640
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 640
    uint b_6 = 0U;

#line 650
    for(;;)
    {

#line 650
        if(b_6 < 8U)
        {
        }
        else
        {

#line 650
            break;
        }

#line 650
        dft2_0(r_3, b_6 * 2U);

#line 650
        b_6 = b_6 + 1U;

#line 650
    }

    return;
}


#line 828
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_4)
{

#line 11 "fft_transform.slang"
    uint lgTB_0 = firstbithigh_0(32U);
    uint lgLn_0 = firstbithigh_0(512U);
    uint blk_2 = tid_0 >> lgTB_0;
    uint lane_2 = tid_0 & 31U;


    dft16_0(r_4);

#line 52 "twiddle.slang"
    uint _S29 = mfCoarseTwtFlag_0();

#line 52
    uint k2_1;

#line 52
    float cr_0;

#line 52
    float ci_0;

#line 27 "fft_transform.slang"
    if(_S29 != 0U)
    {

#line 27
        k2_1 = 0U;


        for(;;)
        {

#line 30
            if(k2_1 < 16U)
            {
            }
            else
            {

#line 30
                break;
            }

#line 31
            uint _S30 = lane_2 * 16U + k2_1;

#line 31
            (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(as_type<half>(ushort((COARSE_TWT_DATA_0[_S30]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S30]) >> 16U) & 65535U))));

#line 30
            k2_1 = k2_1 + 1U;

#line 30
        }

#line 27
    }
    else
    {

#line 39
        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 512.0f);
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
            if(k2_1 < 16U)
            {
            }
            else
            {

#line 42
                break;
            }

#line 43
            (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(half(cr_0), half(ci_0)));
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

#line 27
    }

#line 50
    uint per_2 = 16U / max(32U, 1U);
    uint _S34 = max(2U, 1U);
    uint blk2_2 = tid_0 / _S34;

#line 52
    uint lane2_2 = tid_0 % _S34;

#line 52
    exchange_0(r_4, lgLn_0, lgTB_0, 32U, 512U, blk_2, lane_2, per_2, _S34, 32U, blk2_2, lane2_2, kernelContext_4);

#line 11
    uint lgTB_1 = firstbithigh_0(2U);

    uint blk_3 = tid_0 >> lgTB_1;
    uint lane_3 = tid_0 & 1U;


    dft16_0(r_4);

#line 52 "twiddle.slang"
    uint _S35 = mfCoarseTwtFlag_0();

#line 27 "fft_transform.slang"
    if(_S35 != 0U)
    {

#line 27
        k2_1 = 0U;


        for(;;)
        {

#line 30
            if(k2_1 < 16U)
            {
            }
            else
            {

#line 30
                break;
            }

#line 31
            uint _S36 = 512U + lane_3 * 16U + k2_1;

#line 31
            (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(as_type<half>(ushort((COARSE_TWT_DATA_0[_S36]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S36]) >> 16U) & 65535U))));

#line 30
            k2_1 = k2_1 + 1U;

#line 30
        }

#line 27
    }
    else
    {

#line 39
        float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 32.0f);
        float _S37 = tw_1.x;

#line 40
        float _S38 = tw_1.y;

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
            (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(half(cr_0), half(ci_0)));
            float nr_1 = cr_0 * _S37 - ci_0 * _S38;
            float _S39 = cr_0 * _S38 + ci_0 * _S37;

#line 42
            k2_1 = k2_1 + 1U;

#line 42
            cr_0 = nr_1;

#line 42
            ci_0 = _S39;

#line 42
        }

#line 27
    }

#line 50
    uint per_3 = 16U / _S34;
    uint _S40 = max(0U, 1U);
    uint blk2_3 = tid_0 / _S40;

#line 52
    uint lane2_3 = tid_0 % _S40;

#line 52
    exchange_0(r_4, lgTB_0, lgTB_1, 2U, 32U, blk_3, lane_3, per_3, _S40, 2U, blk2_3, lane2_3, kernelContext_4);



    innermost_0(r_4);

#line 831 "mm_512_fusedTierB_c16p2.slang"
    return;
}


#line 785
uint lgOf_0(uint i_4)
{

#line 785
    uint _S41;

#line 785
    if(i_4 < 2U)
    {

#line 785
        _S41 = 4U;

#line 785
    }
    else
    {

#line 785
        _S41 = 1U;

#line 785
    }

#line 785
    return _S41;
}


#line 787
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 791
    uint lg_1 = lgOf_0(1U);

#line 791
    uint lg_2 = lgOf_0(0U);

#line 796
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}



uint c16Mag_0(half2 v_1, uint slot_1, uint ws_0, uint we_0, bool ov_0)
{
    uint idx_0 = slotToIndex_0(slot_1);

#line 803
    bool live_0;
    if(idx_0 >= ws_0)
    {

#line 804
        live_0 = idx_0 < we_0;

#line 804
    }
    else
    {

#line 804
        live_0 = false;

#line 804
    }
    float x_2 = float(v_1.x);

#line 805
    float y_0 = float(v_1.y);

#line 805
    uint m_1;
    if(live_0)
    {

#line 806
        m_1 = (as_type<uint>((x_2 * x_2 + y_0 * y_0)));

#line 806
    }
    else
    {

#line 806
        m_1 = 0U;

#line 806
    }
    if(ov_0)
    {
    }
    else
    {

#line 807
        live_0 = false;

#line 807
    }

#line 807
    if(live_0)
    {

#line 807
        m_1 = 2139095040U;

#line 807
    }

#line 807
    return m_1;
}


#line 837
void filterOne_0(uint pair_0, uint d_4, uint t_6, uint tid_1, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{

#line 878
    thread array<half2, int(16)> r_5;

#line 878
    uint n2_0 = 0U;



    for(;;)
    {

#line 882
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 882
            break;
        }

#line 883
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_6 * 512U + tid_1 + 32U * n2_0));

#line 882
        n2_0 = n2_0 + 1U;

#line 882
    }

#line 882
    transform_0(&r_5, tid_1, kernelContext_5);

#line 908
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1018
    bool _S42 = tid_1 == 0U;

#line 1018
    if(_S42)
    {

#line 1018
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 1018
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 1018
    }

#line 1023
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1023
    uint i_5 = 0U;

#line 1023
    uint ovAcc_0 = 0U;

#line 1037
    for(;;)
    {

#line 1037
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1037
            break;
        }

#line 1038
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_5][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_5][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1037
        i_5 = i_5 + 1U;

#line 1037
        ovAcc_0 = ovAcc_1;

#line 1037
    }

    bool _S43 = (ovAcc_0 & 2147516416U) != 0U;

#line 1045
    half2 _S44 = half2(0.0h, 0.0h);

#line 1045
    uint bestBits_0 = thrBits_1;

#line 1045
    uint bestSlot_0 = 4294967295U;

#line 1045
    half2 bestV_0 = _S44;

#line 1045
    i_5 = 0U;
    for(;;)
    {

#line 1046
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1046
            break;
        }

#line 1047
        uint _S45 = tid_1 * 16U + i_5;

#line 1047
        uint m_2 = c16Mag_0(r_5[i_5], _S45, winStart_2, winEnd_2, _S43);
        if(m_2 > bestBits_0)
        {

#line 1048
            bestBits_0 = m_2;

#line 1048
            bestSlot_0 = _S45;

#line 1048
            bestV_0 = r_5[i_5];

#line 1048
        }

#line 1046
        i_5 = i_5 + 1U;

#line 1046
    }

#line 1054
    if(bestBits_0 > thrBits_1)
    {

#line 1054
        uint _S46 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), bestBits_0, memory_order_relaxed);

#line 1054
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    uint best_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1058
    bool _S47;
    if(bestSlot_0 != 4294967295U)
    {

#line 1059
        _S47 = bestBits_0 == best_0;

#line 1059
    }
    else
    {

#line 1059
        _S47 = false;

#line 1059
    }

#line 1059
    uint winner_0;

#line 1059
    if(_S47)
    {

#line 1059
        winner_0 = bestSlot_0;

#line 1059
    }
    else
    {

#line 1059
        winner_0 = 4294967295U;

#line 1059
    }

#line 1065
    bool _S48 = winner_0 != 4294967295U;

#line 1065
    if(_S48)
    {

#line 1065
        uint _S49 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 1065
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);
    uint wslot_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U];

    bool _S50 = pair_0 != 4294967295U;

#line 1070
    if(_S50)
    {

#line 1070
        _S47 = _S48;

#line 1070
    }
    else
    {

#line 1070
        _S47 = false;

#line 1070
    }

#line 1070
    if(_S47)
    {

#line 1070
        _S47 = winner_0 == wslot_0;

#line 1070
    }
    else
    {

#line 1070
        _S47 = false;

#line 1070
    }

#line 1070
    if(_S47)
    {

#line 1071
        *(peakIdx_0+pair_0) = int(slotToIndex_0(wslot_0));

#line 1071
        *(peakVal_0+pair_0) = packed_float2(float2(float(bestV_0.x), float(bestV_0.y))) ;

#line 1070
    }



    if(_S50)
    {

#line 1074
        _S47 = _S42;

#line 1074
    }
    else
    {

#line 1074
        _S47 = false;

#line 1074
    }

#line 1074
    if(_S47)
    {

#line 1074
        _S47 = wslot_0 == 4294967295U;

#line 1074
    }
    else
    {

#line 1074
        _S47 = false;

#line 1074
    }

#line 1074
    if(_S47)
    {

#line 1075
        *(peakIdx_0+pair_0) = int(-1);

#line 1075
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1074
    }

#line 1218
    return;
}


#line 1579
void filterPair_0(uint pair_1, uint tid_2, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, uint device* rowWin_1, KernelContext_0 thread* kernelContext_6)
{

#line 1579
    thread uint _S51 = winStart_3;

#line 1579
    thread uint _S52 = winEnd_3;

#line 1585
    kernelContext_6->_tid_0 = tid_2;

#line 1619
    uint pairs_0 = binsize_2 * ntmpl_1;
    bool slotOk_0 = pair_1 < pairs_0;

#line 1620
    uint q_0;
    if(slotOk_0)
    {

#line 1621
        q_0 = pair_1;

#line 1621
    }
    else
    {

#line 1621
        q_0 = pairs_0 - 1U;

#line 1621
    }

#line 1621
    uint _S53;
    if(slotOk_0)
    {

#line 1622
        _S53 = q_0;

#line 1622
    }
    else
    {

#line 1622
        _S53 = 4294967295U;

#line 1622
    }
    uint d_5 = q_0 / ntmpl_1;

#line 1623
    uint _S54 = q_0 - d_5 * ntmpl_1;

#line 1623
    rowWindow_0(d_5, &_S51, &_S52, rowWin_1, kernelContext_6);

#line 1635
    thread array<half2, int(16)> dreg_1;

#line 1635
    uint n2_1 = 0U;

    for(;;)
    {

#line 1637
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1637
            break;
        }

#line 63 "twiddle.slang"
        uint _S55 = mfDataStrideFlag_0();

#line 178 "mm_512_fusedTierB_c16p2.slang"
        if(_S55 != 0U)
        {

#line 63 "twiddle.slang"
            uint _S56 = mfDataStrideFlag_0();

#line 63
            q_0 = _S56;

#line 178 "mm_512_fusedTierB_c16p2.slang"
        }
        else
        {

#line 178
            q_0 = 512U;

#line 178
        }

#line 1638
        half2 _S57 = dload_0(data_1, d_5 * q_0 + tid_2 + 32U * n2_1);

#line 1638
        dreg_1[n2_1] = _S57;

#line 1637
        n2_1 = n2_1 + 1U;

#line 1637
    }

#line 1637
    uint k_0 = 0U;

#line 1657
    for(;;)
    {

#line 1657
        if(k_0 < 1U)
        {
        }
        else
        {

#line 1657
            break;
        }

#line 1658
        uint _S58 = _S53 + k_0;

#line 1658
        uint _S59 = _S54 + k_0;

#line 1658
        thread array<half2, int(16)> _S60 = dreg_1;

#line 1658
        filterOne_0(_S58, d_5, _S59, tid_2, &_S60, data_1, tmpl_1, peakIdx_1, peakVal_1, _S51, _S52, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1657
        k_0 = k_0 + 1U;

#line 1657
    }



    return;
}


#line 1674
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1674
    thread KernelContext_0 kernelContext_7;

#line 1674
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1674
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1674
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1674
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1674
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1674
    (&kernelContext_7)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1674
    threadgroup array<uint, int(1024)> stg_1;

#line 1674
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1674
    (&kernelContext_7)->_binPhase_0 = 0U;

#line 1694
    uint _S61 = lid_0.x;

#line 1694
    uint _sub_0 = _S61 / 32U;
    uint _pr_0 = gid_0.x * 2U + _sub_0;

#line 1695
    uint _t_0 = _S61 % 32U;
    (&kernelContext_7)->_stgBase_0 = _sub_0 * 512U;

#line 1696
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, entryPointParams_rowWin_1, &kernelContext_7);

#line 1709
    return;
}
