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

#line 10 "mm_512_refineListed_c16.slang"
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


#line 87 "twiddle.slang"
uint mfRowWindowsFlag_0()
{
    ;
    uint _S2 = ((MF_ROW_WINDOWS));

#line 90
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


#line 323 "mm_512_refineListed_c16.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_survivors_0;
    uint device* entryPointParams_count_0;
    uint device* entryPointParams_rowWin_0;
    uint _stgBase_0;
    uint _binPhase_0;
    uint _tid_0;
};


#line 230
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 92 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 233 "mm_512_refineListed_c16.slang"
    if(_S3 == 0U)
    {

#line 233
        return;
    }

#line 234
    uint _S4 = 3U * d_0;

#line 234
    *winStart_1 = rowWin_0[_S4];
    *winEnd_1 = rowWin_0[_S4 + 1U];
    kernelContext_0->_binPhase_0 = rowWin_0[_S4 + 2U];
    return;
}


#line 60 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S5 = ((MF_DATA_STRIDE));

#line 63
    return _S5;
}



uint mfDataScaleFlag_0()
{
    ;
    uint _S6 = ((MF_DATA_SCALE_BITS));

#line 71
    return _S6;
}


#line 172 "mm_512_refineListed_c16.slang"
half2 cload_0(uint device* b_0, uint i_0)
{

#line 173
    uint p_0 = b_0[i_0];

#line 173
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 264
half2 dload_0(uint device* b_1, uint i_1)
{

#line 65 "twiddle.slang"
    uint _S7 = mfDataStrideFlag_0();

#line 266 "mm_512_refineListed_c16.slang"
    if(_S7 != 0U)
    {

#line 73 "twiddle.slang"
        uint _S8 = mfDataScaleFlag_0();

#line 267 "mm_512_refineListed_c16.slang"
        float s_0 = (as_type<float>((_S8)));
        uint _S9 = 2U * i_1;

#line 268
        return half2(half((as_type<float>((b_1[_S9]))) * s_0), half((as_type<float>((b_1[_S9 + 1U]))) * s_0));
    }
    return cload_0(b_1, i_1);
}


#line 400
void cmulconjs_0(half2 ar_0, half2 ai_0, half2 br_0, half2 bi_0, half2 thread* pr_0, half2 thread* pi_0)
{
    *pr_0 = ar_0 * br_0 + ai_0 * bi_0;
    *pi_0 = ai_0 * br_0 - ar_0 * bi_0;
    return;
}


#line 412
void r4s_0(array<half2, int(16)> thread* re_0, array<half2, int(16)> thread* im_0, uint a_0, uint b_2, uint c_0, uint d_1)
{
    half2 t0r_0 = (*re_0)[a_0] + (*re_0)[c_0];

#line 414
    half2 t0i_0 = (*im_0)[a_0] + (*im_0)[c_0];
    half2 t1r_0 = (*re_0)[a_0] - (*re_0)[c_0];

#line 415
    half2 t1i_0 = (*im_0)[a_0] - (*im_0)[c_0];
    half2 t2r_0 = (*re_0)[b_2] + (*re_0)[d_1];

#line 416
    half2 t2i_0 = (*im_0)[b_2] + (*im_0)[d_1];
    half2 t3r_0 = (*re_0)[b_2] - (*re_0)[d_1];
    half2 j3r_0 = - ((*im_0)[b_2] - (*im_0)[d_1]);
    (*re_0)[a_0] = t0r_0 + t2r_0;

#line 419
    (*im_0)[a_0] = t0i_0 + t2i_0;
    (*re_0)[b_2] = t1r_0 + j3r_0;

#line 420
    (*im_0)[b_2] = t1i_0 + t3r_0;
    (*re_0)[c_0] = t0r_0 - t2r_0;

#line 421
    (*im_0)[c_0] = t0i_0 - t2i_0;
    (*re_0)[d_1] = t1r_0 - j3r_0;

#line 422
    (*im_0)[d_1] = t1i_0 - t3r_0;
    return;
}


#line 391
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 391
    half2 _S10 = half2(wr_0) ;

#line 391
    half2 _S11 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S11 + *xi_0 * _S10;
    *xr_0 = *xr_0 * _S10 - *xi_0 * _S11;

#line 395
    *xi_0 = ni_0;
    return;
}


#line 425
void swap2_0(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint p_1, uint q_0)
{

    half2 t_0 = (*re_1)[p_1];

#line 428
    (*re_1)[p_1] = (*re_1)[q_0];

#line 428
    (*re_1)[q_0] = t_0;
    half2 t_1 = (*im_1)[p_1];

#line 429
    (*im_1)[p_1] = (*im_1)[q_0];

#line 429
    (*im_1)[q_0] = t_1;
    return;
}


#line 463
void dft16s_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2)
{

#line 463
    uint n1_0 = 0U;

    for(;;)
    {

#line 465
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 465
            break;
        }

#line 465
        r4s_0(re_2, im_2, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 465
        n1_0 = n1_0 + 1U;

#line 465
    }


    cmulw_0(&(*re_2)[int(5)], &(*im_2)[int(5)], 0.923828125h, 0.382568359375h);
    cmulw_0(&(*re_2)[int(9)], &(*im_2)[int(9)], 0.70703125h, 0.70703125h);
    cmulw_0(&(*re_2)[int(13)], &(*im_2)[int(13)], 0.382568359375h, 0.923828125h);
    cmulw_0(&(*re_2)[int(6)], &(*im_2)[int(6)], 0.70703125h, 0.70703125h);
    cmulw_0(&(*re_2)[int(10)], &(*im_2)[int(10)], 0.0h, 1.0h);
    cmulw_0(&(*re_2)[int(14)], &(*im_2)[int(14)], -0.70703125h, 0.70703125h);
    cmulw_0(&(*re_2)[int(7)], &(*im_2)[int(7)], 0.382568359375h, 0.923828125h);
    cmulw_0(&(*re_2)[int(11)], &(*im_2)[int(11)], -0.70703125h, 0.70703125h);
    cmulw_0(&(*re_2)[int(15)], &(*im_2)[int(15)], -0.923828125h, -0.382568359375h);

#line 476
    uint k2_0 = 0U;
    for(;;)
    {

#line 477
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 477
            break;
        }

#line 478
        uint _S12 = 4U * k2_0;

#line 478
        r4s_0(re_2, im_2, _S12, _S12 + 1U, _S12 + 2U, _S12 + 3U);

#line 477
        k2_0 = k2_0 + 1U;

#line 477
    }

    swap2_0(re_2, im_2, 1U, 4U);

#line 479
    swap2_0(re_2, im_2, 2U, 8U);

#line 479
    swap2_0(re_2, im_2, 3U, 12U);
    swap2_0(re_2, im_2, 6U, 9U);

#line 480
    swap2_0(re_2, im_2, 7U, 13U);

#line 480
    swap2_0(re_2, im_2, 11U, 14U);
    return;
}


#line 49 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S13 = ((MF_COARSE_TWT));

#line 52
    return _S13;
}


#line 76
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S14 = ((MF_ACCURATE_TRIG));

#line 79
    return _S14;
}


#line 103
float2 mfTwiddle_0(float angle_0)
{

#line 81
    uint _S15 = mfAccurateTrigFlag_0();

#line 105
    if(_S15 == 0U)
    {

#line 106
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S16 = float(quadrant_0);
    float x_0 = angle_0 - _S16 * 1.57079625129699707f - _S16 * 7.54978941586159635e-08f;
    float z_0 = x_0 * x_0;
    float c_1 = 1.0f + z_0 * (-0.5f + z_0 * (0.0416666679084301f + z_0 * (-0.00138888892251998f + z_0 * (0.00002480158764229f + z_0 * -2.75573199814971304e-07f))));

    float s_1 = x_0 * (1.0f + z_0 * (-0.1666666716337204f + z_0 * (0.00833333376795053f + z_0 * (-0.0001984127011383f + z_0 * (2.75573188446287531e-06f + z_0 * -2.50521079436794025e-08f)))));


    switch(quadrant_0 & int(3))
    {
    case int(1):
        {

#line 119
            return float2(- s_1, c_1);
        }
    case int(2):
        {

#line 120
            return float2(- c_1, - s_1);
        }
    case int(3):
        {

#line 121
            return float2(s_1, - c_1);
        }
    default:
        {

#line 122
            return float2(c_1, s_1);
        }
    }

#line 122
}


#line 432 "mm_512_refineListed_c16.slang"
void dft2s_0(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint o_0)
{
    half2 ar_1 = (*re_3)[o_0];

#line 434
    half2 ai_1 = (*im_3)[o_0];

#line 434
    uint _S17 = o_0 + 1U;

#line 434
    half2 br_1 = (*re_3)[_S17];

#line 434
    half2 bi_1 = (*im_3)[_S17];
    (*re_3)[o_0] = (*re_3)[o_0] + (*re_3)[_S17];

#line 435
    (*im_3)[o_0] = ai_1 + bi_1;
    (*re_3)[_S17] = ar_1 - br_1;

#line 436
    (*im_3)[_S17] = ai_1 - bi_1;
    return;
}


#line 607
void innermostS_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4)
{

#line 607
    uint b_3 = 0U;

#line 612
    for(;;)
    {

#line 612
        if(b_3 < 8U)
        {
        }
        else
        {

#line 612
            break;
        }

#line 612
        dft2s_0(re_4, im_4, b_3 * 2U);

#line 612
        b_3 = b_3 + 1U;

#line 612
    }
    return;
}


#line 883
uint lgOf_0(uint i_2)
{

#line 883
    uint _S18;

#line 883
    if(i_2 < 2U)
    {

#line 883
        _S18 = 4U;

#line 883
    }
    else
    {

#line 883
        _S18 = 1U;

#line 883
    }

#line 883
    return _S18;
}


#line 885
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 889
    uint lg_1 = lgOf_0(1U);

#line 889
    uint lg_2 = lgOf_0(0U);

#line 894
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 487
half2 mag2s_0(half2 re_5, half2 im_5)
{

#line 487
    return re_5 * re_5 + im_5 * im_5;
}


#line 2348
[[kernel]] void refineListedBounded(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]], uint device* entryPointParams_rowWin_1 [[buffer(7)]])
{

#line 2348
    half2 db_0;

#line 2348
    uint _S19;

#line 2348
    uint _S20;

#line 2348
    uint _S21;

#line 2348
    uint _S22;

#line 2348
    uint _S23;

#line 2348
    uint j_0;

#line 2348
    thread KernelContext_0 kernelContext_1;

#line 2348
    (&kernelContext_1)->entryPointParams_0 = entryPointParams_1;

#line 2348
    (&kernelContext_1)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2348
    (&kernelContext_1)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2348
    (&kernelContext_1)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2348
    (&kernelContext_1)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2348
    (&kernelContext_1)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2348
    (&kernelContext_1)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2348
    (&kernelContext_1)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 2348
    (&kernelContext_1)->_binPhase_0 = 0U;

#line 2359
    uint total_0 = entryPointParams_count_1[int(0)];

    if(total_0 == 0U)
    {

#line 2361
        return;
    }

#line 2367
    uint _S24 = lid_0.x;

#line 2367
    uint sub_0 = _S24 / 32U;

#line 2367
    uint _S25 = _S24 % 32U;
    (&kernelContext_1)->_stgBase_0 = sub_0 * 512U;

#line 2368
    uint base_0 = gid_0.x * 4U;

    for(;;)
    {

#line 2370
        if(base_0 < total_0)
        {
        }
        else
        {

#line 2370
            break;
        }

#line 2371
        uint idxA_0 = base_0 + 2U * sub_0;
        uint idxB_0 = idxA_0 + 1U;

#line 2372
        uint pairA_0;
        if(idxA_0 < total_0)
        {

#line 2373
            pairA_0 = (&kernelContext_1)->entryPointParams_survivors_0[idxA_0];

#line 2373
        }
        else
        {

#line 2373
            pairA_0 = 4294967295U;

#line 2373
        }

#line 2373
        uint pairB_0;
        if(idxB_0 < total_0)
        {

#line 2374
            pairB_0 = (&kernelContext_1)->entryPointParams_survivors_0[idxB_0];

#line 2374
        }
        else
        {

#line 2374
            pairB_0 = 4294967295U;

#line 2374
        }
        bool _S26 = pairA_0 != 4294967295U;

#line 2375
        uint refPairA_0;

#line 2375
        if(_S26)
        {

#line 2375
            refPairA_0 = pairA_0;

#line 2375
        }
        else
        {

#line 2375
            refPairA_0 = (&kernelContext_1)->entryPointParams_survivors_0[total_0 - 1U];

#line 2375
        }
        bool _S27 = pairB_0 != 4294967295U;

#line 2376
        uint refPairB_0;

#line 2376
        if(_S27)
        {

#line 2376
            refPairB_0 = pairB_0;

#line 2376
        }
        else
        {

#line 2376
            refPairB_0 = refPairA_0;

#line 2376
        }
        uint dA_0 = refPairA_0 / (&kernelContext_1)->entryPointParams_0->ntmpl_0;

#line 2377
        uint tA_0 = refPairA_0 % (&kernelContext_1)->entryPointParams_0->ntmpl_0;
        uint dB_0 = refPairB_0 / (&kernelContext_1)->entryPointParams_0->ntmpl_0;

#line 2378
        uint tB_0 = refPairB_0 % (&kernelContext_1)->entryPointParams_0->ntmpl_0;
        thread uint wsA_0 = (&kernelContext_1)->entryPointParams_0->winStart_0;

#line 2379
        thread uint weA_0 = (&kernelContext_1)->entryPointParams_0->winEnd_0;

#line 2379
        thread uint wsB_0 = (&kernelContext_1)->entryPointParams_0->winStart_0;

#line 2379
        thread uint weB_0 = (&kernelContext_1)->entryPointParams_0->winEnd_0;

#line 2379
        rowWindow_0(dA_0, &wsA_0, &weA_0, (&kernelContext_1)->entryPointParams_rowWin_0, &kernelContext_1);

#line 2379
        rowWindow_0(dB_0, &wsB_0, &weB_0, (&kernelContext_1)->entryPointParams_rowWin_0, &kernelContext_1);


        uint _S28 = wsA_0;

#line 2382
        uint _S29 = weA_0;

#line 2382
        uint _S30 = wsB_0;

#line 2382
        uint _S31 = weB_0;

#line 2382
        uint _S32 = (&kernelContext_1)->entryPointParams_0->nbins_0;

#line 2382
        uint _S33 = (&kernelContext_1)->entryPointParams_0->thrBits_0;

#line 2382
        for(;;)
        {

#line 2382
            thread array<half2, int(16)> re_6;

#line 2382
            thread array<half2, int(16)> im_6;

#line 2382
            uint _S34 = mfDataStrideFlag_0();

#line 2382
            uint _S35;

#line 2382
            if(_S34 != 0U)
            {

#line 2382
                uint _S36 = mfDataStrideFlag_0();

#line 2382
                _S35 = _S36;

#line 2382
            }
            else
            {

#line 2382
                _S35 = 512U;

#line 2382
            }

#line 2382
            bool _S37 = dB_0 == dA_0;

#line 2382
            uint n2_0 = 0U;

#line 2382
            for(;;)
            {

#line 2382
                if(n2_0 < 16U)
                {
                }
                else
                {

#line 2382
                    break;
                }

#line 2382
                uint k_0 = _S25 + 32U * n2_0;

#line 2382
                half2 da_0 = dload_0((&kernelContext_1)->entryPointParams_data_0, dA_0 * _S35 + k_0);

#line 2382
                if(_S37)
                {

#line 2382
                    db_0 = da_0;

#line 2382
                }
                else
                {

#line 2382
                    half2 _S38 = dload_0((&kernelContext_1)->entryPointParams_data_0, dB_0 * _S35 + k_0);

#line 2382
                    db_0 = _S38;

#line 2382
                }

#line 2382
                half2 ta_0 = cload_0((&kernelContext_1)->entryPointParams_tmpl_0, tA_0 * 512U + k_0);

#line 2382
                half2 tb_0 = cload_0((&kernelContext_1)->entryPointParams_tmpl_0, tB_0 * 512U + k_0);

#line 2382
                cmulconjs_0(half2(da_0.x, db_0.x), half2(da_0.y, db_0.y), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_6[n2_0], &im_6[n2_0]);

#line 2382
                n2_0 = n2_0 + 1U;

#line 2382
            }

#line 2382
            array<half2, int(16)> _S39 = re_6;

#line 2382
            array<half2, int(16)> _S40 = im_6;

#line 2382
            for(;;)
            {

#line 2382
                thread array<half2, int(16)> _S41 = _S39;

#line 2382
                thread array<half2, int(16)> _S42 = _S40;

#line 2382
                (&kernelContext_1)->_tid_0 = _S25;

#line 2382
                for(;;)
                {

#line 2382
                    uint lgTB_0 = firstbithigh_0(32U);

#line 2382
                    uint lane_0 = _S25 & 31U;

#line 2382
                    dft16s_0(&_S41, &_S42);

#line 2382
                    uint _S43 = mfCoarseTwtFlag_0();

#line 2382
                    uint i_3;

#line 2382
                    float cr_0;

#line 2382
                    float ci_0;

#line 2382
                    if(_S43 != 0U)
                    {

#line 2382
                        i_3 = 0U;

#line 2382
                        for(;;)
                        {

#line 2382
                            if(i_3 < 16U)
                            {
                            }
                            else
                            {

#line 2382
                                break;
                            }

#line 2382
                            uint _S44 = lane_0 * 16U + i_3;

#line 2382
                            cmulw_0(&_S41[i_3], &_S42[i_3], as_type<half>(ushort((COARSE_TWT_DATA_0[_S44]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S44]) >> 16U) & 65535U)));

#line 2382
                            i_3 = i_3 + 1U;

#line 2382
                        }

#line 2382
                    }
                    else
                    {

#line 2382
                        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_0) / 512.0f);

#line 2382
                        float _S45 = tw_0.x;

#line 2382
                        float _S46 = tw_0.y;

#line 2382
                        i_3 = 0U;

#line 2382
                        cr_0 = 1.0f;

#line 2382
                        ci_0 = 0.0f;

#line 2382
                        for(;;)
                        {

#line 2382
                            if(i_3 < 16U)
                            {
                            }
                            else
                            {

#line 2382
                                break;
                            }

#line 2382
                            cmulw_0(&_S41[i_3], &_S42[i_3], half(cr_0), half(ci_0));

#line 2382
                            float nr_0 = cr_0 * _S45 - ci_0 * _S46;

#line 2382
                            float _S47 = cr_0 * _S46 + ci_0 * _S45;

#line 2382
                            i_3 = i_3 + 1U;

#line 2382
                            cr_0 = nr_0;

#line 2382
                            ci_0 = _S47;

#line 2382
                        }

#line 2382
                    }

#line 2382
                    uint per_0 = 16U / max(32U, 1U);

#line 2382
                    uint _S48 = max(2U, 1U);

#line 2382
                    uint blk2_0 = _S25 / _S48;

#line 2382
                    uint lane2_0 = _S25 % _S48;

#line 2382
                    for(;;)
                    {

#line 2382
                        uint _S49 = (&kernelContext_1)->_tid_0;

#line 2382
                        for(;;)
                        {

#line 2382
                            thread array<uint, int(16)> t_2;

#line 2382
                            i_3 = 0U;

#line 2382
                            for(;;)
                            {

#line 2382
                                if(i_3 < 16U)
                                {
                                }
                                else
                                {

#line 2382
                                    break;
                                }

#line 2382
                                t_2[i_3] = (uint(as_type<ushort>(_S41[i_3][0U])) & 65535U) | (uint(as_type<ushort>(_S41[i_3][1U])) << 16U);

#line 2382
                                i_3 = i_3 + 1U;

#line 2382
                            }

#line 2382
                            uint shift_0 = lgTB_0 - 4U;

#line 2382
                            _S19 = shift_0;

#line 2382
                            uint _S50 = (_S49 >> shift_0) & 15U;

#line 2382
                            bool _S51 = (_S50 & 1U) != 0U;

#line 2382
                            uint _S52;

#line 2382
                            if(_S51)
                            {

#line 2382
                                _S52 = t_2[0U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S52 = t_2[1U];

#line 2382
                            }

#line 2382
                            uint _S53 = 1U << shift_0;

#line 2382
                            _S20 = _S53;

#line 2382
                            uint partner_0 = (simd_shuffle_xor((_S52), ushort((_S53))));

#line 2382
                            if(_S51)
                            {

#line 2382
                                t_2[0U] = partner_0;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[1U] = partner_0;

#line 2382
                            }

#line 2382
                            uint _S54;

#line 2382
                            if(_S51)
                            {

#line 2382
                                _S54 = t_2[2U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S54 = t_2[3U];

#line 2382
                            }

#line 2382
                            uint partner_1 = (simd_shuffle_xor((_S54), ushort((_S53))));

#line 2382
                            if(_S51)
                            {

#line 2382
                                t_2[2U] = partner_1;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[3U] = partner_1;

#line 2382
                            }

#line 2382
                            uint _S55;

#line 2382
                            if(_S51)
                            {

#line 2382
                                _S55 = t_2[4U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S55 = t_2[5U];

#line 2382
                            }

#line 2382
                            uint partner_2 = (simd_shuffle_xor((_S55), ushort((_S53))));

#line 2382
                            if(_S51)
                            {

#line 2382
                                t_2[4U] = partner_2;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[5U] = partner_2;

#line 2382
                            }

#line 2382
                            uint _S56;

#line 2382
                            if(_S51)
                            {

#line 2382
                                _S56 = t_2[6U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S56 = t_2[7U];

#line 2382
                            }

#line 2382
                            uint partner_3 = (simd_shuffle_xor((_S56), ushort((_S53))));

#line 2382
                            if(_S51)
                            {

#line 2382
                                t_2[6U] = partner_3;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[7U] = partner_3;

#line 2382
                            }

#line 2382
                            uint _S57;

#line 2382
                            if(_S51)
                            {

#line 2382
                                _S57 = t_2[8U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S57 = t_2[9U];

#line 2382
                            }

#line 2382
                            uint partner_4 = (simd_shuffle_xor((_S57), ushort((_S53))));

#line 2382
                            if(_S51)
                            {

#line 2382
                                t_2[8U] = partner_4;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[9U] = partner_4;

#line 2382
                            }

#line 2382
                            uint _S58;

#line 2382
                            if(_S51)
                            {

#line 2382
                                _S58 = t_2[10U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S58 = t_2[11U];

#line 2382
                            }

#line 2382
                            uint partner_5 = (simd_shuffle_xor((_S58), ushort((_S53))));

#line 2382
                            if(_S51)
                            {

#line 2382
                                t_2[10U] = partner_5;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[11U] = partner_5;

#line 2382
                            }

#line 2382
                            uint _S59;

#line 2382
                            if(_S51)
                            {

#line 2382
                                _S59 = t_2[12U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S59 = t_2[13U];

#line 2382
                            }

#line 2382
                            uint partner_6 = (simd_shuffle_xor((_S59), ushort((_S53))));

#line 2382
                            if(_S51)
                            {

#line 2382
                                t_2[12U] = partner_6;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[13U] = partner_6;

#line 2382
                            }

#line 2382
                            uint _S60;

#line 2382
                            if(_S51)
                            {

#line 2382
                                _S60 = t_2[14U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S60 = t_2[15U];

#line 2382
                            }

#line 2382
                            uint partner_7 = (simd_shuffle_xor((_S60), ushort((_S53))));

#line 2382
                            if(_S51)
                            {

#line 2382
                                t_2[14U] = partner_7;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[15U] = partner_7;

#line 2382
                            }

#line 2382
                            bool _S61 = (_S50 & 2U) != 0U;

#line 2382
                            uint _S62;

#line 2382
                            if(_S61)
                            {

#line 2382
                                _S62 = t_2[0U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S62 = t_2[2U];

#line 2382
                            }

#line 2382
                            uint _S63 = 2U << shift_0;

#line 2382
                            _S21 = _S63;

#line 2382
                            uint partner_8 = (simd_shuffle_xor((_S62), ushort((_S63))));

#line 2382
                            if(_S61)
                            {

#line 2382
                                t_2[0U] = partner_8;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[2U] = partner_8;

#line 2382
                            }

#line 2382
                            uint _S64;

#line 2382
                            if(_S61)
                            {

#line 2382
                                _S64 = t_2[1U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S64 = t_2[3U];

#line 2382
                            }

#line 2382
                            uint partner_9 = (simd_shuffle_xor((_S64), ushort((_S63))));

#line 2382
                            if(_S61)
                            {

#line 2382
                                t_2[1U] = partner_9;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[3U] = partner_9;

#line 2382
                            }

#line 2382
                            uint _S65;

#line 2382
                            if(_S61)
                            {

#line 2382
                                _S65 = t_2[4U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S65 = t_2[6U];

#line 2382
                            }

#line 2382
                            uint partner_10 = (simd_shuffle_xor((_S65), ushort((_S63))));

#line 2382
                            if(_S61)
                            {

#line 2382
                                t_2[4U] = partner_10;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[6U] = partner_10;

#line 2382
                            }

#line 2382
                            uint _S66;

#line 2382
                            if(_S61)
                            {

#line 2382
                                _S66 = t_2[5U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S66 = t_2[7U];

#line 2382
                            }

#line 2382
                            uint partner_11 = (simd_shuffle_xor((_S66), ushort((_S63))));

#line 2382
                            if(_S61)
                            {

#line 2382
                                t_2[5U] = partner_11;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[7U] = partner_11;

#line 2382
                            }

#line 2382
                            uint _S67;

#line 2382
                            if(_S61)
                            {

#line 2382
                                _S67 = t_2[8U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S67 = t_2[10U];

#line 2382
                            }

#line 2382
                            uint partner_12 = (simd_shuffle_xor((_S67), ushort((_S63))));

#line 2382
                            if(_S61)
                            {

#line 2382
                                t_2[8U] = partner_12;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[10U] = partner_12;

#line 2382
                            }

#line 2382
                            uint _S68;

#line 2382
                            if(_S61)
                            {

#line 2382
                                _S68 = t_2[9U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S68 = t_2[11U];

#line 2382
                            }

#line 2382
                            uint partner_13 = (simd_shuffle_xor((_S68), ushort((_S63))));

#line 2382
                            if(_S61)
                            {

#line 2382
                                t_2[9U] = partner_13;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[11U] = partner_13;

#line 2382
                            }

#line 2382
                            uint _S69;

#line 2382
                            if(_S61)
                            {

#line 2382
                                _S69 = t_2[12U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S69 = t_2[14U];

#line 2382
                            }

#line 2382
                            uint partner_14 = (simd_shuffle_xor((_S69), ushort((_S63))));

#line 2382
                            if(_S61)
                            {

#line 2382
                                t_2[12U] = partner_14;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[14U] = partner_14;

#line 2382
                            }

#line 2382
                            uint _S70;

#line 2382
                            if(_S61)
                            {

#line 2382
                                _S70 = t_2[13U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S70 = t_2[15U];

#line 2382
                            }

#line 2382
                            uint partner_15 = (simd_shuffle_xor((_S70), ushort((_S63))));

#line 2382
                            if(_S61)
                            {

#line 2382
                                t_2[13U] = partner_15;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[15U] = partner_15;

#line 2382
                            }

#line 2382
                            bool _S71 = (_S50 & 4U) != 0U;

#line 2382
                            uint _S72;

#line 2382
                            if(_S71)
                            {

#line 2382
                                _S72 = t_2[0U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S72 = t_2[4U];

#line 2382
                            }

#line 2382
                            uint _S73 = 4U << shift_0;

#line 2382
                            _S22 = _S73;

#line 2382
                            uint partner_16 = (simd_shuffle_xor((_S72), ushort((_S73))));

#line 2382
                            if(_S71)
                            {

#line 2382
                                t_2[0U] = partner_16;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[4U] = partner_16;

#line 2382
                            }

#line 2382
                            uint _S74;

#line 2382
                            if(_S71)
                            {

#line 2382
                                _S74 = t_2[1U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S74 = t_2[5U];

#line 2382
                            }

#line 2382
                            uint partner_17 = (simd_shuffle_xor((_S74), ushort((_S73))));

#line 2382
                            if(_S71)
                            {

#line 2382
                                t_2[1U] = partner_17;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[5U] = partner_17;

#line 2382
                            }

#line 2382
                            uint _S75;

#line 2382
                            if(_S71)
                            {

#line 2382
                                _S75 = t_2[2U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S75 = t_2[6U];

#line 2382
                            }

#line 2382
                            uint partner_18 = (simd_shuffle_xor((_S75), ushort((_S73))));

#line 2382
                            if(_S71)
                            {

#line 2382
                                t_2[2U] = partner_18;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[6U] = partner_18;

#line 2382
                            }

#line 2382
                            uint _S76;

#line 2382
                            if(_S71)
                            {

#line 2382
                                _S76 = t_2[3U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S76 = t_2[7U];

#line 2382
                            }

#line 2382
                            uint partner_19 = (simd_shuffle_xor((_S76), ushort((_S73))));

#line 2382
                            if(_S71)
                            {

#line 2382
                                t_2[3U] = partner_19;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[7U] = partner_19;

#line 2382
                            }

#line 2382
                            uint _S77;

#line 2382
                            if(_S71)
                            {

#line 2382
                                _S77 = t_2[8U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S77 = t_2[12U];

#line 2382
                            }

#line 2382
                            uint partner_20 = (simd_shuffle_xor((_S77), ushort((_S73))));

#line 2382
                            if(_S71)
                            {

#line 2382
                                t_2[8U] = partner_20;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[12U] = partner_20;

#line 2382
                            }

#line 2382
                            uint _S78;

#line 2382
                            if(_S71)
                            {

#line 2382
                                _S78 = t_2[9U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S78 = t_2[13U];

#line 2382
                            }

#line 2382
                            uint partner_21 = (simd_shuffle_xor((_S78), ushort((_S73))));

#line 2382
                            if(_S71)
                            {

#line 2382
                                t_2[9U] = partner_21;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[13U] = partner_21;

#line 2382
                            }

#line 2382
                            uint _S79;

#line 2382
                            if(_S71)
                            {

#line 2382
                                _S79 = t_2[10U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S79 = t_2[14U];

#line 2382
                            }

#line 2382
                            uint partner_22 = (simd_shuffle_xor((_S79), ushort((_S73))));

#line 2382
                            if(_S71)
                            {

#line 2382
                                t_2[10U] = partner_22;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[14U] = partner_22;

#line 2382
                            }

#line 2382
                            uint _S80;

#line 2382
                            if(_S71)
                            {

#line 2382
                                _S80 = t_2[11U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S80 = t_2[15U];

#line 2382
                            }

#line 2382
                            uint partner_23 = (simd_shuffle_xor((_S80), ushort((_S73))));

#line 2382
                            if(_S71)
                            {

#line 2382
                                t_2[11U] = partner_23;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[15U] = partner_23;

#line 2382
                            }

#line 2382
                            bool _S81 = (_S50 & 8U) != 0U;

#line 2382
                            uint _S82;

#line 2382
                            if(_S81)
                            {

#line 2382
                                _S82 = t_2[0U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S82 = t_2[8U];

#line 2382
                            }

#line 2382
                            uint _S83 = 8U << shift_0;

#line 2382
                            _S23 = _S83;

#line 2382
                            uint partner_24 = (simd_shuffle_xor((_S82), ushort((_S83))));

#line 2382
                            if(_S81)
                            {

#line 2382
                                t_2[0U] = partner_24;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[8U] = partner_24;

#line 2382
                            }

#line 2382
                            uint _S84;

#line 2382
                            if(_S81)
                            {

#line 2382
                                _S84 = t_2[1U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S84 = t_2[9U];

#line 2382
                            }

#line 2382
                            uint partner_25 = (simd_shuffle_xor((_S84), ushort((_S83))));

#line 2382
                            if(_S81)
                            {

#line 2382
                                t_2[1U] = partner_25;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[9U] = partner_25;

#line 2382
                            }

#line 2382
                            uint _S85;

#line 2382
                            if(_S81)
                            {

#line 2382
                                _S85 = t_2[2U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S85 = t_2[10U];

#line 2382
                            }

#line 2382
                            uint partner_26 = (simd_shuffle_xor((_S85), ushort((_S83))));

#line 2382
                            if(_S81)
                            {

#line 2382
                                t_2[2U] = partner_26;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[10U] = partner_26;

#line 2382
                            }

#line 2382
                            uint _S86;

#line 2382
                            if(_S81)
                            {

#line 2382
                                _S86 = t_2[3U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S86 = t_2[11U];

#line 2382
                            }

#line 2382
                            uint partner_27 = (simd_shuffle_xor((_S86), ushort((_S83))));

#line 2382
                            if(_S81)
                            {

#line 2382
                                t_2[3U] = partner_27;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[11U] = partner_27;

#line 2382
                            }

#line 2382
                            uint _S87;

#line 2382
                            if(_S81)
                            {

#line 2382
                                _S87 = t_2[4U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S87 = t_2[12U];

#line 2382
                            }

#line 2382
                            uint partner_28 = (simd_shuffle_xor((_S87), ushort((_S83))));

#line 2382
                            if(_S81)
                            {

#line 2382
                                t_2[4U] = partner_28;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[12U] = partner_28;

#line 2382
                            }

#line 2382
                            uint _S88;

#line 2382
                            if(_S81)
                            {

#line 2382
                                _S88 = t_2[5U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S88 = t_2[13U];

#line 2382
                            }

#line 2382
                            uint partner_29 = (simd_shuffle_xor((_S88), ushort((_S83))));

#line 2382
                            if(_S81)
                            {

#line 2382
                                t_2[5U] = partner_29;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[13U] = partner_29;

#line 2382
                            }

#line 2382
                            uint _S89;

#line 2382
                            if(_S81)
                            {

#line 2382
                                _S89 = t_2[6U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S89 = t_2[14U];

#line 2382
                            }

#line 2382
                            uint partner_30 = (simd_shuffle_xor((_S89), ushort((_S83))));

#line 2382
                            if(_S81)
                            {

#line 2382
                                t_2[6U] = partner_30;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[14U] = partner_30;

#line 2382
                            }

#line 2382
                            uint _S90;

#line 2382
                            if(_S81)
                            {

#line 2382
                                _S90 = t_2[7U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S90 = t_2[15U];

#line 2382
                            }

#line 2382
                            uint partner_31 = (simd_shuffle_xor((_S90), ushort((_S83))));

#line 2382
                            if(_S81)
                            {

#line 2382
                                t_2[7U] = partner_31;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_2[15U] = partner_31;

#line 2382
                            }

#line 2382
                            uint i_4 = 0U;

#line 2382
                            for(;;)
                            {

#line 2382
                                if(i_4 < 16U)
                                {
                                }
                                else
                                {

#line 2382
                                    break;
                                }

#line 2382
                                _S41[i_4] = half2(as_type<half>(ushort((t_2[i_4]) & 65535U)), as_type<half>(ushort(((t_2[i_4]) >> 16U) & 65535U)));

#line 2382
                                i_4 = i_4 + 1U;

#line 2382
                            }

#line 2382
                            break;
                        }

#line 2382
                        uint _S91 = (&kernelContext_1)->_tid_0;

#line 2382
                        for(;;)
                        {

#line 2382
                            thread array<uint, int(16)> t_3;

#line 2382
                            uint i_5 = 0U;

#line 2382
                            for(;;)
                            {

#line 2382
                                if(i_5 < 16U)
                                {
                                }
                                else
                                {

#line 2382
                                    break;
                                }

#line 2382
                                t_3[i_5] = (uint(as_type<ushort>(_S42[i_5][0U])) & 65535U) | (uint(as_type<ushort>(_S42[i_5][1U])) << 16U);

#line 2382
                                i_5 = i_5 + 1U;

#line 2382
                            }

#line 2382
                            uint _S92 = (_S91 >> _S19) & 15U;

#line 2382
                            bool _S93 = (_S92 & 1U) != 0U;

#line 2382
                            uint _S94;

#line 2382
                            if(_S93)
                            {

#line 2382
                                _S94 = t_3[0U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S94 = t_3[1U];

#line 2382
                            }

#line 2382
                            uint partner_32 = (simd_shuffle_xor((_S94), ushort((_S20))));

#line 2382
                            if(_S93)
                            {

#line 2382
                                t_3[0U] = partner_32;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[1U] = partner_32;

#line 2382
                            }

#line 2382
                            uint _S95;

#line 2382
                            if(_S93)
                            {

#line 2382
                                _S95 = t_3[2U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S95 = t_3[3U];

#line 2382
                            }

#line 2382
                            uint partner_33 = (simd_shuffle_xor((_S95), ushort((_S20))));

#line 2382
                            if(_S93)
                            {

#line 2382
                                t_3[2U] = partner_33;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[3U] = partner_33;

#line 2382
                            }

#line 2382
                            uint _S96;

#line 2382
                            if(_S93)
                            {

#line 2382
                                _S96 = t_3[4U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S96 = t_3[5U];

#line 2382
                            }

#line 2382
                            uint partner_34 = (simd_shuffle_xor((_S96), ushort((_S20))));

#line 2382
                            if(_S93)
                            {

#line 2382
                                t_3[4U] = partner_34;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[5U] = partner_34;

#line 2382
                            }

#line 2382
                            uint _S97;

#line 2382
                            if(_S93)
                            {

#line 2382
                                _S97 = t_3[6U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S97 = t_3[7U];

#line 2382
                            }

#line 2382
                            uint partner_35 = (simd_shuffle_xor((_S97), ushort((_S20))));

#line 2382
                            if(_S93)
                            {

#line 2382
                                t_3[6U] = partner_35;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[7U] = partner_35;

#line 2382
                            }

#line 2382
                            uint _S98;

#line 2382
                            if(_S93)
                            {

#line 2382
                                _S98 = t_3[8U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S98 = t_3[9U];

#line 2382
                            }

#line 2382
                            uint partner_36 = (simd_shuffle_xor((_S98), ushort((_S20))));

#line 2382
                            if(_S93)
                            {

#line 2382
                                t_3[8U] = partner_36;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[9U] = partner_36;

#line 2382
                            }

#line 2382
                            uint _S99;

#line 2382
                            if(_S93)
                            {

#line 2382
                                _S99 = t_3[10U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S99 = t_3[11U];

#line 2382
                            }

#line 2382
                            uint partner_37 = (simd_shuffle_xor((_S99), ushort((_S20))));

#line 2382
                            if(_S93)
                            {

#line 2382
                                t_3[10U] = partner_37;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[11U] = partner_37;

#line 2382
                            }

#line 2382
                            uint _S100;

#line 2382
                            if(_S93)
                            {

#line 2382
                                _S100 = t_3[12U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S100 = t_3[13U];

#line 2382
                            }

#line 2382
                            uint partner_38 = (simd_shuffle_xor((_S100), ushort((_S20))));

#line 2382
                            if(_S93)
                            {

#line 2382
                                t_3[12U] = partner_38;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[13U] = partner_38;

#line 2382
                            }

#line 2382
                            uint _S101;

#line 2382
                            if(_S93)
                            {

#line 2382
                                _S101 = t_3[14U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S101 = t_3[15U];

#line 2382
                            }

#line 2382
                            uint partner_39 = (simd_shuffle_xor((_S101), ushort((_S20))));

#line 2382
                            if(_S93)
                            {

#line 2382
                                t_3[14U] = partner_39;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[15U] = partner_39;

#line 2382
                            }

#line 2382
                            bool _S102 = (_S92 & 2U) != 0U;

#line 2382
                            uint _S103;

#line 2382
                            if(_S102)
                            {

#line 2382
                                _S103 = t_3[0U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S103 = t_3[2U];

#line 2382
                            }

#line 2382
                            uint partner_40 = (simd_shuffle_xor((_S103), ushort((_S21))));

#line 2382
                            if(_S102)
                            {

#line 2382
                                t_3[0U] = partner_40;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[2U] = partner_40;

#line 2382
                            }

#line 2382
                            uint _S104;

#line 2382
                            if(_S102)
                            {

#line 2382
                                _S104 = t_3[1U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S104 = t_3[3U];

#line 2382
                            }

#line 2382
                            uint partner_41 = (simd_shuffle_xor((_S104), ushort((_S21))));

#line 2382
                            if(_S102)
                            {

#line 2382
                                t_3[1U] = partner_41;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[3U] = partner_41;

#line 2382
                            }

#line 2382
                            uint _S105;

#line 2382
                            if(_S102)
                            {

#line 2382
                                _S105 = t_3[4U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S105 = t_3[6U];

#line 2382
                            }

#line 2382
                            uint partner_42 = (simd_shuffle_xor((_S105), ushort((_S21))));

#line 2382
                            if(_S102)
                            {

#line 2382
                                t_3[4U] = partner_42;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[6U] = partner_42;

#line 2382
                            }

#line 2382
                            uint _S106;

#line 2382
                            if(_S102)
                            {

#line 2382
                                _S106 = t_3[5U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S106 = t_3[7U];

#line 2382
                            }

#line 2382
                            uint partner_43 = (simd_shuffle_xor((_S106), ushort((_S21))));

#line 2382
                            if(_S102)
                            {

#line 2382
                                t_3[5U] = partner_43;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[7U] = partner_43;

#line 2382
                            }

#line 2382
                            uint _S107;

#line 2382
                            if(_S102)
                            {

#line 2382
                                _S107 = t_3[8U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S107 = t_3[10U];

#line 2382
                            }

#line 2382
                            uint partner_44 = (simd_shuffle_xor((_S107), ushort((_S21))));

#line 2382
                            if(_S102)
                            {

#line 2382
                                t_3[8U] = partner_44;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[10U] = partner_44;

#line 2382
                            }

#line 2382
                            uint _S108;

#line 2382
                            if(_S102)
                            {

#line 2382
                                _S108 = t_3[9U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S108 = t_3[11U];

#line 2382
                            }

#line 2382
                            uint partner_45 = (simd_shuffle_xor((_S108), ushort((_S21))));

#line 2382
                            if(_S102)
                            {

#line 2382
                                t_3[9U] = partner_45;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[11U] = partner_45;

#line 2382
                            }

#line 2382
                            uint _S109;

#line 2382
                            if(_S102)
                            {

#line 2382
                                _S109 = t_3[12U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S109 = t_3[14U];

#line 2382
                            }

#line 2382
                            uint partner_46 = (simd_shuffle_xor((_S109), ushort((_S21))));

#line 2382
                            if(_S102)
                            {

#line 2382
                                t_3[12U] = partner_46;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[14U] = partner_46;

#line 2382
                            }

#line 2382
                            uint _S110;

#line 2382
                            if(_S102)
                            {

#line 2382
                                _S110 = t_3[13U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S110 = t_3[15U];

#line 2382
                            }

#line 2382
                            uint partner_47 = (simd_shuffle_xor((_S110), ushort((_S21))));

#line 2382
                            if(_S102)
                            {

#line 2382
                                t_3[13U] = partner_47;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[15U] = partner_47;

#line 2382
                            }

#line 2382
                            bool _S111 = (_S92 & 4U) != 0U;

#line 2382
                            uint _S112;

#line 2382
                            if(_S111)
                            {

#line 2382
                                _S112 = t_3[0U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S112 = t_3[4U];

#line 2382
                            }

#line 2382
                            uint partner_48 = (simd_shuffle_xor((_S112), ushort((_S22))));

#line 2382
                            if(_S111)
                            {

#line 2382
                                t_3[0U] = partner_48;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[4U] = partner_48;

#line 2382
                            }

#line 2382
                            uint _S113;

#line 2382
                            if(_S111)
                            {

#line 2382
                                _S113 = t_3[1U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S113 = t_3[5U];

#line 2382
                            }

#line 2382
                            uint partner_49 = (simd_shuffle_xor((_S113), ushort((_S22))));

#line 2382
                            if(_S111)
                            {

#line 2382
                                t_3[1U] = partner_49;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[5U] = partner_49;

#line 2382
                            }

#line 2382
                            uint _S114;

#line 2382
                            if(_S111)
                            {

#line 2382
                                _S114 = t_3[2U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S114 = t_3[6U];

#line 2382
                            }

#line 2382
                            uint partner_50 = (simd_shuffle_xor((_S114), ushort((_S22))));

#line 2382
                            if(_S111)
                            {

#line 2382
                                t_3[2U] = partner_50;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[6U] = partner_50;

#line 2382
                            }

#line 2382
                            uint _S115;

#line 2382
                            if(_S111)
                            {

#line 2382
                                _S115 = t_3[3U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S115 = t_3[7U];

#line 2382
                            }

#line 2382
                            uint partner_51 = (simd_shuffle_xor((_S115), ushort((_S22))));

#line 2382
                            if(_S111)
                            {

#line 2382
                                t_3[3U] = partner_51;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[7U] = partner_51;

#line 2382
                            }

#line 2382
                            uint _S116;

#line 2382
                            if(_S111)
                            {

#line 2382
                                _S116 = t_3[8U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S116 = t_3[12U];

#line 2382
                            }

#line 2382
                            uint partner_52 = (simd_shuffle_xor((_S116), ushort((_S22))));

#line 2382
                            if(_S111)
                            {

#line 2382
                                t_3[8U] = partner_52;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[12U] = partner_52;

#line 2382
                            }

#line 2382
                            uint _S117;

#line 2382
                            if(_S111)
                            {

#line 2382
                                _S117 = t_3[9U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S117 = t_3[13U];

#line 2382
                            }

#line 2382
                            uint partner_53 = (simd_shuffle_xor((_S117), ushort((_S22))));

#line 2382
                            if(_S111)
                            {

#line 2382
                                t_3[9U] = partner_53;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[13U] = partner_53;

#line 2382
                            }

#line 2382
                            uint _S118;

#line 2382
                            if(_S111)
                            {

#line 2382
                                _S118 = t_3[10U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S118 = t_3[14U];

#line 2382
                            }

#line 2382
                            uint partner_54 = (simd_shuffle_xor((_S118), ushort((_S22))));

#line 2382
                            if(_S111)
                            {

#line 2382
                                t_3[10U] = partner_54;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[14U] = partner_54;

#line 2382
                            }

#line 2382
                            uint _S119;

#line 2382
                            if(_S111)
                            {

#line 2382
                                _S119 = t_3[11U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S119 = t_3[15U];

#line 2382
                            }

#line 2382
                            uint partner_55 = (simd_shuffle_xor((_S119), ushort((_S22))));

#line 2382
                            if(_S111)
                            {

#line 2382
                                t_3[11U] = partner_55;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[15U] = partner_55;

#line 2382
                            }

#line 2382
                            bool _S120 = (_S92 & 8U) != 0U;

#line 2382
                            uint _S121;

#line 2382
                            if(_S120)
                            {

#line 2382
                                _S121 = t_3[0U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S121 = t_3[8U];

#line 2382
                            }

#line 2382
                            uint partner_56 = (simd_shuffle_xor((_S121), ushort((_S23))));

#line 2382
                            if(_S120)
                            {

#line 2382
                                t_3[0U] = partner_56;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[8U] = partner_56;

#line 2382
                            }

#line 2382
                            uint _S122;

#line 2382
                            if(_S120)
                            {

#line 2382
                                _S122 = t_3[1U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S122 = t_3[9U];

#line 2382
                            }

#line 2382
                            uint partner_57 = (simd_shuffle_xor((_S122), ushort((_S23))));

#line 2382
                            if(_S120)
                            {

#line 2382
                                t_3[1U] = partner_57;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[9U] = partner_57;

#line 2382
                            }

#line 2382
                            uint _S123;

#line 2382
                            if(_S120)
                            {

#line 2382
                                _S123 = t_3[2U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S123 = t_3[10U];

#line 2382
                            }

#line 2382
                            uint partner_58 = (simd_shuffle_xor((_S123), ushort((_S23))));

#line 2382
                            if(_S120)
                            {

#line 2382
                                t_3[2U] = partner_58;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[10U] = partner_58;

#line 2382
                            }

#line 2382
                            uint _S124;

#line 2382
                            if(_S120)
                            {

#line 2382
                                _S124 = t_3[3U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S124 = t_3[11U];

#line 2382
                            }

#line 2382
                            uint partner_59 = (simd_shuffle_xor((_S124), ushort((_S23))));

#line 2382
                            if(_S120)
                            {

#line 2382
                                t_3[3U] = partner_59;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[11U] = partner_59;

#line 2382
                            }

#line 2382
                            uint _S125;

#line 2382
                            if(_S120)
                            {

#line 2382
                                _S125 = t_3[4U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S125 = t_3[12U];

#line 2382
                            }

#line 2382
                            uint partner_60 = (simd_shuffle_xor((_S125), ushort((_S23))));

#line 2382
                            if(_S120)
                            {

#line 2382
                                t_3[4U] = partner_60;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[12U] = partner_60;

#line 2382
                            }

#line 2382
                            uint _S126;

#line 2382
                            if(_S120)
                            {

#line 2382
                                _S126 = t_3[5U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S126 = t_3[13U];

#line 2382
                            }

#line 2382
                            uint partner_61 = (simd_shuffle_xor((_S126), ushort((_S23))));

#line 2382
                            if(_S120)
                            {

#line 2382
                                t_3[5U] = partner_61;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[13U] = partner_61;

#line 2382
                            }

#line 2382
                            uint _S127;

#line 2382
                            if(_S120)
                            {

#line 2382
                                _S127 = t_3[6U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S127 = t_3[14U];

#line 2382
                            }

#line 2382
                            uint partner_62 = (simd_shuffle_xor((_S127), ushort((_S23))));

#line 2382
                            if(_S120)
                            {

#line 2382
                                t_3[6U] = partner_62;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[14U] = partner_62;

#line 2382
                            }

#line 2382
                            uint _S128;

#line 2382
                            if(_S120)
                            {

#line 2382
                                _S128 = t_3[7U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S128 = t_3[15U];

#line 2382
                            }

#line 2382
                            uint partner_63 = (simd_shuffle_xor((_S128), ushort((_S23))));

#line 2382
                            if(_S120)
                            {

#line 2382
                                t_3[7U] = partner_63;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[15U] = partner_63;

#line 2382
                            }

#line 2382
                            uint i_6 = 0U;

#line 2382
                            for(;;)
                            {

#line 2382
                                if(i_6 < 16U)
                                {
                                }
                                else
                                {

#line 2382
                                    break;
                                }

#line 2382
                                _S42[i_6] = half2(as_type<half>(ushort((t_3[i_6]) & 65535U)), as_type<half>(ushort(((t_3[i_6]) >> 16U) & 65535U)));

#line 2382
                                i_6 = i_6 + 1U;

#line 2382
                            }

#line 2382
                            break;
                        }

#line 2382
                        break;
                    }

#line 2382
                    for(;;)
                    {

#line 2382
                        uint lane_1 = _S25 & 1U;

#line 2382
                        dft16s_0(&_S41, &_S42);

#line 2382
                        uint _S129 = mfCoarseTwtFlag_0();

#line 2382
                        uint r_0;

#line 2382
                        if(_S129 != 0U)
                        {

#line 2382
                            r_0 = 0U;

#line 2382
                            for(;;)
                            {

#line 2382
                                if(r_0 < 16U)
                                {
                                }
                                else
                                {

#line 2382
                                    break;
                                }

#line 2382
                                uint _S130 = 512U + lane_1 * 16U + r_0;

#line 2382
                                cmulw_0(&_S41[r_0], &_S42[r_0], as_type<half>(ushort((COARSE_TWT_DATA_0[_S130]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S130]) >> 16U) & 65535U)));

#line 2382
                                r_0 = r_0 + 1U;

#line 2382
                            }

#line 2382
                        }
                        else
                        {

#line 2382
                            float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 32.0f);

#line 2382
                            float _S131 = tw_1.x;

#line 2382
                            float _S132 = tw_1.y;

#line 2382
                            r_0 = 0U;

#line 2382
                            cr_0 = 1.0f;

#line 2382
                            ci_0 = 0.0f;

#line 2382
                            for(;;)
                            {

#line 2382
                                if(r_0 < 16U)
                                {
                                }
                                else
                                {

#line 2382
                                    break;
                                }

#line 2382
                                cmulw_0(&_S41[r_0], &_S42[r_0], half(cr_0), half(ci_0));

#line 2382
                                float nr_1 = cr_0 * _S131 - ci_0 * _S132;

#line 2382
                                float _S133 = cr_0 * _S132 + ci_0 * _S131;

#line 2382
                                r_0 = r_0 + 1U;

#line 2382
                                cr_0 = nr_1;

#line 2382
                                ci_0 = _S133;

#line 2382
                            }

#line 2382
                        }

#line 2382
                        uint per_1 = 16U / _S48;

#line 2382
                        uint _S134 = max(0U, 1U);

#line 2382
                        uint blk2_1 = _S25 / _S134;

#line 2382
                        uint lane2_1 = _S25 % _S134;

#line 2382
                        for(;;)
                        {

#line 2382
                            uint _S135 = (&kernelContext_1)->_tid_0;

#line 2382
                            for(;;)
                            {

#line 2382
                                thread array<uint, int(16)> t_4;

#line 2382
                                r_0 = 0U;

#line 2382
                                for(;;)
                                {

#line 2382
                                    if(r_0 < 2U)
                                    {
                                    }
                                    else
                                    {

#line 2382
                                        break;
                                    }

#line 2382
                                    j_0 = 0U;

#line 2382
                                    for(;;)
                                    {

#line 2382
                                        if(j_0 < 8U)
                                        {
                                        }
                                        else
                                        {

#line 2382
                                            break;
                                        }

#line 2382
                                        t_4[j_0 * 2U + r_0] = (uint(as_type<ushort>(_S41[r_0 * 8U + j_0][0U])) & 65535U) | (uint(as_type<ushort>(_S41[r_0 * 8U + j_0][1U])) << 16U);

#line 2382
                                        j_0 = j_0 + 1U;

#line 2382
                                    }

#line 2382
                                    r_0 = r_0 + 1U;

#line 2382
                                }

#line 2382
                                bool _S136 = (_S135 & 1U) != 0U;

#line 2382
                                uint _S137;

#line 2382
                                if(_S136)
                                {

#line 2382
                                    _S137 = t_4[0U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S137 = t_4[1U];

#line 2382
                                }

#line 2382
                                uint partner_64 = (simd_shuffle_xor((_S137), ushort((1U))));

#line 2382
                                if(_S136)
                                {

#line 2382
                                    t_4[0U] = partner_64;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_4[1U] = partner_64;

#line 2382
                                }

#line 2382
                                uint _S138;

#line 2382
                                if(_S136)
                                {

#line 2382
                                    _S138 = t_4[2U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S138 = t_4[3U];

#line 2382
                                }

#line 2382
                                uint partner_65 = (simd_shuffle_xor((_S138), ushort((1U))));

#line 2382
                                if(_S136)
                                {

#line 2382
                                    t_4[2U] = partner_65;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_4[3U] = partner_65;

#line 2382
                                }

#line 2382
                                uint _S139;

#line 2382
                                if(_S136)
                                {

#line 2382
                                    _S139 = t_4[4U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S139 = t_4[5U];

#line 2382
                                }

#line 2382
                                uint partner_66 = (simd_shuffle_xor((_S139), ushort((1U))));

#line 2382
                                if(_S136)
                                {

#line 2382
                                    t_4[4U] = partner_66;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_4[5U] = partner_66;

#line 2382
                                }

#line 2382
                                uint _S140;

#line 2382
                                if(_S136)
                                {

#line 2382
                                    _S140 = t_4[6U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S140 = t_4[7U];

#line 2382
                                }

#line 2382
                                uint partner_67 = (simd_shuffle_xor((_S140), ushort((1U))));

#line 2382
                                if(_S136)
                                {

#line 2382
                                    t_4[6U] = partner_67;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_4[7U] = partner_67;

#line 2382
                                }

#line 2382
                                uint _S141;

#line 2382
                                if(_S136)
                                {

#line 2382
                                    _S141 = t_4[8U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S141 = t_4[9U];

#line 2382
                                }

#line 2382
                                uint partner_68 = (simd_shuffle_xor((_S141), ushort((1U))));

#line 2382
                                if(_S136)
                                {

#line 2382
                                    t_4[8U] = partner_68;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_4[9U] = partner_68;

#line 2382
                                }

#line 2382
                                uint _S142;

#line 2382
                                if(_S136)
                                {

#line 2382
                                    _S142 = t_4[10U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S142 = t_4[11U];

#line 2382
                                }

#line 2382
                                uint partner_69 = (simd_shuffle_xor((_S142), ushort((1U))));

#line 2382
                                if(_S136)
                                {

#line 2382
                                    t_4[10U] = partner_69;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_4[11U] = partner_69;

#line 2382
                                }

#line 2382
                                uint _S143;

#line 2382
                                if(_S136)
                                {

#line 2382
                                    _S143 = t_4[12U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S143 = t_4[13U];

#line 2382
                                }

#line 2382
                                uint partner_70 = (simd_shuffle_xor((_S143), ushort((1U))));

#line 2382
                                if(_S136)
                                {

#line 2382
                                    t_4[12U] = partner_70;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_4[13U] = partner_70;

#line 2382
                                }

#line 2382
                                uint _S144;

#line 2382
                                if(_S136)
                                {

#line 2382
                                    _S144 = t_4[14U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S144 = t_4[15U];

#line 2382
                                }

#line 2382
                                uint partner_71 = (simd_shuffle_xor((_S144), ushort((1U))));

#line 2382
                                if(_S136)
                                {

#line 2382
                                    t_4[14U] = partner_71;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_4[15U] = partner_71;

#line 2382
                                }

#line 2382
                                uint i_7 = 0U;

#line 2382
                                for(;;)
                                {

#line 2382
                                    if(i_7 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2382
                                        break;
                                    }

#line 2382
                                    _S41[i_7] = half2(as_type<half>(ushort((t_4[i_7]) & 65535U)), as_type<half>(ushort(((t_4[i_7]) >> 16U) & 65535U)));

#line 2382
                                    i_7 = i_7 + 1U;

#line 2382
                                }

#line 2382
                                break;
                            }

#line 2382
                            uint _S145 = (&kernelContext_1)->_tid_0;

#line 2382
                            for(;;)
                            {

#line 2382
                                thread array<uint, int(16)> t_5;

#line 2382
                                uint r_1 = 0U;

#line 2382
                                for(;;)
                                {

#line 2382
                                    if(r_1 < 2U)
                                    {
                                    }
                                    else
                                    {

#line 2382
                                        break;
                                    }

#line 2382
                                    j_0 = 0U;

#line 2382
                                    for(;;)
                                    {

#line 2382
                                        if(j_0 < 8U)
                                        {
                                        }
                                        else
                                        {

#line 2382
                                            break;
                                        }

#line 2382
                                        t_5[j_0 * 2U + r_1] = (uint(as_type<ushort>(_S42[r_1 * 8U + j_0][0U])) & 65535U) | (uint(as_type<ushort>(_S42[r_1 * 8U + j_0][1U])) << 16U);

#line 2382
                                        j_0 = j_0 + 1U;

#line 2382
                                    }

#line 2382
                                    r_1 = r_1 + 1U;

#line 2382
                                }

#line 2382
                                bool _S146 = (_S145 & 1U) != 0U;

#line 2382
                                uint _S147;

#line 2382
                                if(_S146)
                                {

#line 2382
                                    _S147 = t_5[0U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S147 = t_5[1U];

#line 2382
                                }

#line 2382
                                uint partner_72 = (simd_shuffle_xor((_S147), ushort((1U))));

#line 2382
                                if(_S146)
                                {

#line 2382
                                    t_5[0U] = partner_72;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_5[1U] = partner_72;

#line 2382
                                }

#line 2382
                                uint _S148;

#line 2382
                                if(_S146)
                                {

#line 2382
                                    _S148 = t_5[2U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S148 = t_5[3U];

#line 2382
                                }

#line 2382
                                uint partner_73 = (simd_shuffle_xor((_S148), ushort((1U))));

#line 2382
                                if(_S146)
                                {

#line 2382
                                    t_5[2U] = partner_73;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_5[3U] = partner_73;

#line 2382
                                }

#line 2382
                                uint _S149;

#line 2382
                                if(_S146)
                                {

#line 2382
                                    _S149 = t_5[4U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S149 = t_5[5U];

#line 2382
                                }

#line 2382
                                uint partner_74 = (simd_shuffle_xor((_S149), ushort((1U))));

#line 2382
                                if(_S146)
                                {

#line 2382
                                    t_5[4U] = partner_74;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_5[5U] = partner_74;

#line 2382
                                }

#line 2382
                                uint _S150;

#line 2382
                                if(_S146)
                                {

#line 2382
                                    _S150 = t_5[6U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S150 = t_5[7U];

#line 2382
                                }

#line 2382
                                uint partner_75 = (simd_shuffle_xor((_S150), ushort((1U))));

#line 2382
                                if(_S146)
                                {

#line 2382
                                    t_5[6U] = partner_75;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_5[7U] = partner_75;

#line 2382
                                }

#line 2382
                                uint _S151;

#line 2382
                                if(_S146)
                                {

#line 2382
                                    _S151 = t_5[8U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S151 = t_5[9U];

#line 2382
                                }

#line 2382
                                uint partner_76 = (simd_shuffle_xor((_S151), ushort((1U))));

#line 2382
                                if(_S146)
                                {

#line 2382
                                    t_5[8U] = partner_76;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_5[9U] = partner_76;

#line 2382
                                }

#line 2382
                                uint _S152;

#line 2382
                                if(_S146)
                                {

#line 2382
                                    _S152 = t_5[10U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S152 = t_5[11U];

#line 2382
                                }

#line 2382
                                uint partner_77 = (simd_shuffle_xor((_S152), ushort((1U))));

#line 2382
                                if(_S146)
                                {

#line 2382
                                    t_5[10U] = partner_77;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_5[11U] = partner_77;

#line 2382
                                }

#line 2382
                                uint _S153;

#line 2382
                                if(_S146)
                                {

#line 2382
                                    _S153 = t_5[12U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S153 = t_5[13U];

#line 2382
                                }

#line 2382
                                uint partner_78 = (simd_shuffle_xor((_S153), ushort((1U))));

#line 2382
                                if(_S146)
                                {

#line 2382
                                    t_5[12U] = partner_78;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_5[13U] = partner_78;

#line 2382
                                }

#line 2382
                                uint _S154;

#line 2382
                                if(_S146)
                                {

#line 2382
                                    _S154 = t_5[14U];

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S154 = t_5[15U];

#line 2382
                                }

#line 2382
                                uint partner_79 = (simd_shuffle_xor((_S154), ushort((1U))));

#line 2382
                                if(_S146)
                                {

#line 2382
                                    t_5[14U] = partner_79;

#line 2382
                                }
                                else
                                {

#line 2382
                                    t_5[15U] = partner_79;

#line 2382
                                }

#line 2382
                                uint i_8 = 0U;

#line 2382
                                for(;;)
                                {

#line 2382
                                    if(i_8 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2382
                                        break;
                                    }

#line 2382
                                    _S42[i_8] = half2(as_type<half>(ushort((t_5[i_8]) & 65535U)), as_type<half>(ushort(((t_5[i_8]) >> 16U) & 65535U)));

#line 2382
                                    i_8 = i_8 + 1U;

#line 2382
                                }

#line 2382
                                break;
                            }

#line 2382
                            break;
                        }

#line 2382
                        break;
                    }

#line 2382
                    break;
                }

#line 2382
                innermostS_0(&_S41, &_S42);

#line 2382
                uint spanA_0;

#line 2382
                uint spanB_0;

#line 2382
                uint i_9;

#line 2382
                uint ovAcc_0;

#line 2382
                uint ovAcc_1;

#line 2382
                uint ovAcc_2;

#line 2382
                uint bb_0;

#line 2382
                uint bb_1;

#line 2382
                bool infLocalA_0;

#line 2382
                bool infLocalB_0;

#line 2382
                bool hitLocalA_0;

#line 2382
                bool hitLocalB_0;

#line 2382
                bool hitA_0;

#line 2382
                bool hitB_0;

#line 2382
                float2 _S155;

#line 2382
                if(_S33 != 0U)
                {

#line 2382
                    float _S156 = (as_type<float>((_S33)));

#line 2382
                    for(;;)
                    {

#line 2382
                        uint _S157 = slotToIndex_0(_S25 * 16U);

#line 2382
                        uint _S158 = _S157 - _S28;

#line 2382
                        if(_S29 > _S28)
                        {

#line 2382
                            spanA_0 = _S29 - _S28;

#line 2382
                        }
                        else
                        {

#line 2382
                            spanA_0 = 0U;

#line 2382
                        }

#line 2382
                        uint _S159 = _S157 - _S30;

#line 2382
                        if(_S31 > _S30)
                        {

#line 2382
                            spanB_0 = _S31 - _S30;

#line 2382
                        }
                        else
                        {

#line 2382
                            spanB_0 = 0U;

#line 2382
                        }

#line 2382
                        half2 _S160 = half2(float2(0.0f) );

#line 2382
                        i_9 = 0U;

#line 2382
                        db_0 = _S160;

#line 2382
                        ovAcc_0 = 0U;

#line 2382
                        for(;;)
                        {

#line 2382
                            if(i_9 < 16U)
                            {
                            }
                            else
                            {

#line 2382
                                break;
                            }

#line 2382
                            uint si_0 = slotToIndex_0(i_9);

#line 2382
                            bool liveB_0 = (_S159 + si_0) < spanB_0;

#line 2382
                            half2 _S161 = _S41[i_9];

#line 2382
                            half2 _S162 = _S42[i_9];

#line 2382
                            half2 _S163 = mag2s_0(_S41[i_9], _S42[i_9]);

#line 2382
                            uint _S164 = (uint(as_type<ushort>(_S163[0U])) & 65535U) | (uint(as_type<ushort>(_S163[1U])) << 16U);

#line 2382
                            if((_S158 + si_0) < spanA_0)
                            {

#line 2382
                                ovAcc_1 = _S164 & 65535U;

#line 2382
                            }
                            else
                            {

#line 2382
                                ovAcc_1 = 0U;

#line 2382
                            }

#line 2382
                            if(liveB_0)
                            {

#line 2382
                                ovAcc_2 = _S164 & 4294901760U;

#line 2382
                            }
                            else
                            {

#line 2382
                                ovAcc_2 = 0U;

#line 2382
                            }

#line 2382
                            uint m_0 = ovAcc_1 | ovAcc_2;

#line 2382
                            half2 _S165 = max(db_0, half2(as_type<half>(ushort(m_0 & 65535U)), as_type<half>(ushort((m_0 >> 16U) & 65535U))));

#line 2382
                            uint ovAcc_3 = ovAcc_0 | (((((uint(as_type<ushort>(_S161[0U])) & 65535U) | (uint(as_type<ushort>(_S161[1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(_S162[0U])) & 65535U) | (uint(as_type<ushort>(_S162[1U])) << 16U)) & 2080406528U) + 67109888U));

#line 2382
                            i_9 = i_9 + 1U;

#line 2382
                            db_0 = _S165;

#line 2382
                            ovAcc_0 = ovAcc_3;

#line 2382
                        }

#line 2382
                        if(spanA_0 == 0U)
                        {

#line 2382
                            ovAcc_1 = ovAcc_0 & 4294934527U;

#line 2382
                        }
                        else
                        {

#line 2382
                            ovAcc_1 = ovAcc_0;

#line 2382
                        }

#line 2382
                        if(spanB_0 == 0U)
                        {

#line 2382
                            ovAcc_2 = ovAcc_1 & 2147483647U;

#line 2382
                        }
                        else
                        {

#line 2382
                            ovAcc_2 = ovAcc_1;

#line 2382
                        }

#line 2382
                        if(_S32 == 0U)
                        {

#line 2382
                            uint _S166 = (uint(as_type<ushort>(db_0[0U])) & 65535U) | (uint(as_type<ushort>(db_0[1U])) << 16U);

#line 2382
                            float thr2_0 = _S156 * _S156;

#line 2382
                            if((ovAcc_2 & 32768U) != 0U)
                            {

#line 2382
                                infLocalA_0 = true;

#line 2382
                            }
                            else
                            {

#line 2382
                                infLocalA_0 = (_S166 & 31744U) == 31744U;

#line 2382
                            }

#line 2382
                            if((ovAcc_2 & 2147483648U) != 0U)
                            {

#line 2382
                                infLocalB_0 = true;

#line 2382
                            }
                            else
                            {

#line 2382
                                infLocalB_0 = (_S166 & 2080374784U) == 2080374784U;

#line 2382
                            }

#line 2382
                            if(infLocalA_0)
                            {

#line 2382
                                hitLocalA_0 = true;

#line 2382
                            }
                            else
                            {

#line 2382
                                if((_S166 & 32767U) != 0U)
                                {

#line 2382
                                    hitLocalA_0 = float(db_0.x) >= thr2_0;

#line 2382
                                }
                                else
                                {

#line 2382
                                    hitLocalA_0 = false;

#line 2382
                                }

#line 2382
                            }

#line 2382
                            if(infLocalB_0)
                            {

#line 2382
                                hitLocalB_0 = true;

#line 2382
                            }
                            else
                            {

#line 2382
                                if((_S166 & 2147418112U) != 0U)
                                {

#line 2382
                                    hitLocalB_0 = float(db_0.y) >= thr2_0;

#line 2382
                                }
                                else
                                {

#line 2382
                                    hitLocalB_0 = false;

#line 2382
                                }

#line 2382
                            }

#line 2382
                            if(hitLocalA_0)
                            {

#line 2382
                                bb_0 = 1U;

#line 2382
                            }
                            else
                            {

#line 2382
                                bb_0 = 0U;

#line 2382
                            }

#line 2382
                            if(hitLocalB_0)
                            {

#line 2382
                                bb_1 = 2U;

#line 2382
                            }
                            else
                            {

#line 2382
                                bb_1 = 0U;

#line 2382
                            }

#line 2382
                            uint _S167 = bb_0 | bb_1;

#line 2382
                            uint _S168 = (simd_shuffle_xor((_S167), ushort((1U))));

#line 2382
                            uint hitBits_0 = _S167 | _S168;

#line 2382
                            uint _S169 = (simd_shuffle_xor((hitBits_0), ushort((2U))));

#line 2382
                            uint hitBits_1 = hitBits_0 | _S169;

#line 2382
                            uint _S170 = (simd_shuffle_xor((hitBits_1), ushort((4U))));

#line 2382
                            uint hitBits_2 = hitBits_1 | _S170;

#line 2382
                            uint _S171 = (simd_shuffle_xor((hitBits_2), ushort((8U))));

#line 2382
                            uint hitBits_3 = hitBits_2 | _S171;

#line 2382
                            uint _S172 = (simd_shuffle_xor((hitBits_3), ushort((16U))));

#line 2382
                            uint hitBits_4 = hitBits_3 | _S172;

#line 2382
                            if(_S25 == 0U)
                            {

#line 2382
                                if(_S26)
                                {

#line 2382
                                    packed_float2 device* _S173 = (&kernelContext_1)->entryPointParams_peakVal_0+pairA_0;

#line 2382
                                    if((hitBits_4 & 1U) != 0U)
                                    {

#line 2382
                                        _S155 = float2(3.40282306073709653e+38f, 0.0f);

#line 2382
                                    }
                                    else
                                    {

#line 2382
                                        _S155 = float2(0.0f, 0.0f);

#line 2382
                                    }

#line 2382
                                    *_S173 = packed_float2(_S155) ;

#line 2382
                                }

#line 2382
                                if(_S27)
                                {

#line 2382
                                    packed_float2 device* _S174 = (&kernelContext_1)->entryPointParams_peakVal_0+pairB_0;

#line 2382
                                    if((hitBits_4 & 2U) != 0U)
                                    {

#line 2382
                                        _S155 = float2(3.40282306073709653e+38f, 0.0f);

#line 2382
                                    }
                                    else
                                    {

#line 2382
                                        _S155 = float2(0.0f, 0.0f);

#line 2382
                                    }

#line 2382
                                    *_S174 = packed_float2(_S155) ;

#line 2382
                                }

#line 2382
                            }

#line 2382
                            break;
                        }

#line 2382
                        uint bb_2 = ((uint(as_type<ushort>(db_0[0U])) & 65535U) | (uint(as_type<ushort>(db_0[1U])) << 16U)) & 2147450879U;

#line 2382
                        if((ovAcc_2 & 32768U) != 0U)
                        {

#line 2382
                            bb_0 = (bb_2 & 4294901760U) | 31744U;

#line 2382
                        }
                        else
                        {

#line 2382
                            bb_0 = bb_2;

#line 2382
                        }

#line 2382
                        if((ovAcc_2 & 2147483648U) != 0U)
                        {

#line 2382
                            bb_1 = (bb_0 & 65535U) | 2080374784U;

#line 2382
                        }
                        else
                        {

#line 2382
                            bb_1 = bb_0;

#line 2382
                        }

#line 2382
                        uint other_0 = (simd_shuffle_xor((bb_1), ushort((1U))));

#line 2382
                        uint _S175 = (max(bb_1 & 65535U, other_0 & 65535U)) | (max(bb_1 & 4294901760U, other_0 & 4294901760U));

#line 2382
                        uint other_1 = (simd_shuffle_xor((_S175), ushort((2U))));

#line 2382
                        uint _S176 = (max(_S175 & 65535U, other_1 & 65535U)) | (max(_S175 & 4294901760U, other_1 & 4294901760U));

#line 2382
                        uint other_2 = (simd_shuffle_xor((_S176), ushort((4U))));

#line 2382
                        uint _S177 = (max(_S176 & 65535U, other_2 & 65535U)) | (max(_S176 & 4294901760U, other_2 & 4294901760U));

#line 2382
                        uint other_3 = (simd_shuffle_xor((_S177), ushort((8U))));

#line 2382
                        uint _S178 = (max(_S177 & 65535U, other_3 & 65535U)) | (max(_S177 & 4294901760U, other_3 & 4294901760U));

#line 2382
                        uint other_4 = (simd_shuffle_xor((_S178), ushort((16U))));

#line 2382
                        uint bb_3 = (max(_S178 & 65535U, other_4 & 65535U)) | (max(_S178 & 4294901760U, other_4 & 4294901760U));

#line 2382
                        if(_S25 == 0U)
                        {

#line 2382
                            bool infA_0 = (bb_3 & 31744U) == 31744U;

#line 2382
                            bool infB_0 = (bb_3 & 2080374784U) == 2080374784U;

#line 2382
                            float bA_0 = sqrt(float(as_type<half>(ushort(bb_3 & 65535U))));

#line 2382
                            float bB_0 = sqrt(float(as_type<half>(ushort((bb_3 >> 16U) & 65535U))));

#line 2382
                            if(infA_0)
                            {

#line 2382
                                hitA_0 = true;

#line 2382
                            }
                            else
                            {

#line 2382
                                if(bA_0 > 0.0f)
                                {

#line 2382
                                    infLocalA_0 = bA_0 >= _S156;

#line 2382
                                }
                                else
                                {

#line 2382
                                    infLocalA_0 = false;

#line 2382
                                }

#line 2382
                                hitA_0 = infLocalA_0;

#line 2382
                            }

#line 2382
                            if(infB_0)
                            {

#line 2382
                                hitB_0 = true;

#line 2382
                            }
                            else
                            {

#line 2382
                                if(bB_0 > 0.0f)
                                {

#line 2382
                                    infLocalA_0 = bB_0 >= _S156;

#line 2382
                                }
                                else
                                {

#line 2382
                                    infLocalA_0 = false;

#line 2382
                                }

#line 2382
                                hitB_0 = infLocalA_0;

#line 2382
                            }

#line 2382
                            if(_S26)
                            {

#line 2382
                                packed_float2 device* _S179 = (&kernelContext_1)->entryPointParams_peakVal_0+pairA_0;

#line 2382
                                if(infA_0)
                                {

#line 2382
                                    _S155 = float2(3.40282306073709653e+38f, 0.0f);

#line 2382
                                }
                                else
                                {

#line 2382
                                    if(hitA_0)
                                    {

#line 2382
                                        _S155 = float2(bA_0, 0.0f);

#line 2382
                                    }
                                    else
                                    {

#line 2382
                                        _S155 = float2(0.0f, 0.0f);

#line 2382
                                    }

#line 2382
                                }

#line 2382
                                *_S179 = packed_float2(_S155) ;

#line 2382
                            }

#line 2382
                            if(_S27)
                            {

#line 2382
                                packed_float2 device* _S180 = (&kernelContext_1)->entryPointParams_peakVal_0+pairB_0;

#line 2382
                                if(infB_0)
                                {

#line 2382
                                    _S155 = float2(3.40282306073709653e+38f, 0.0f);

#line 2382
                                }
                                else
                                {

#line 2382
                                    if(hitB_0)
                                    {

#line 2382
                                        _S155 = float2(bB_0, 0.0f);

#line 2382
                                    }
                                    else
                                    {

#line 2382
                                        _S155 = float2(0.0f, 0.0f);

#line 2382
                                    }

#line 2382
                                }

#line 2382
                                *_S180 = packed_float2(_S155) ;

#line 2382
                            }

#line 2382
                        }

#line 2382
                        break;
                    }

#line 2382
                }
                else
                {

#line 2382
                    array<half2, int(16)> _S181 = _S41;

#line 2382
                    array<half2, int(16)> _S182 = _S42;

#line 2382
                    for(;;)
                    {

#line 2382
                        uint _S183 = slotToIndex_0(_S25 * 16U);

#line 2382
                        uint _S184 = _S183 - _S28;

#line 2382
                        if(_S29 > _S28)
                        {

#line 2382
                            spanA_0 = _S29 - _S28;

#line 2382
                        }
                        else
                        {

#line 2382
                            spanA_0 = 0U;

#line 2382
                        }

#line 2382
                        uint _S185 = _S183 - _S30;

#line 2382
                        if(_S31 > _S30)
                        {

#line 2382
                            spanB_0 = _S31 - _S30;

#line 2382
                        }
                        else
                        {

#line 2382
                            spanB_0 = 0U;

#line 2382
                        }

#line 2382
                        i_9 = 0U;

#line 2382
                        ovAcc_0 = 0U;

#line 2382
                        ovAcc_1 = 0U;

#line 2382
                        ovAcc_2 = 0U;

#line 2382
                        for(;;)
                        {

#line 2382
                            if(i_9 < 16U)
                            {
                            }
                            else
                            {

#line 2382
                                break;
                            }

#line 2382
                            uint si_1 = slotToIndex_0(i_9);

#line 2382
                            bool liveB_1 = (_S185 + si_1) < spanB_0;

#line 2382
                            half2 mg_0 = mag2s_0(_S181[i_9], _S182[i_9]);

#line 2382
                            uint _S186 = (uint(as_type<ushort>(mg_0[0U])) & 65535U) | (uint(as_type<ushort>(mg_0[1U])) << 16U);

#line 2382
                            uint ovAcc_4 = ovAcc_0 | (((((uint(as_type<ushort>(_S181[i_9][0U])) & 65535U) | (uint(as_type<ushort>(_S181[i_9][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(_S182[i_9][0U])) & 65535U) | (uint(as_type<ushort>(_S182[i_9][1U])) << 16U)) & 2080406528U) + 67109888U));

#line 2382
                            if((_S184 + si_1) < spanA_0)
                            {

#line 2382
                                bb_0 = _S186 << 16U;

#line 2382
                            }
                            else
                            {

#line 2382
                                bb_0 = 0U;

#line 2382
                            }

#line 2382
                            uint _S187 = 15U - i_9;

#line 2382
                            uint _S188 = max(ovAcc_1, bb_0 | _S187);

#line 2382
                            if(liveB_1)
                            {

#line 2382
                                bb_1 = _S186 & 4294901760U;

#line 2382
                            }
                            else
                            {

#line 2382
                                bb_1 = 0U;

#line 2382
                            }

#line 2382
                            uint _S189 = max(ovAcc_2, bb_1 | _S187);

#line 2382
                            i_9 = i_9 + 1U;

#line 2382
                            ovAcc_0 = ovAcc_4;

#line 2382
                            ovAcc_1 = _S188;

#line 2382
                            ovAcc_2 = _S189;

#line 2382
                        }

#line 2382
                        bool _S190 = spanA_0 != 0U;

#line 2382
                        if(_S190)
                        {

#line 2382
                            infLocalA_0 = (ovAcc_0 & 32768U) != 0U;

#line 2382
                        }
                        else
                        {

#line 2382
                            infLocalA_0 = false;

#line 2382
                        }

#line 2382
                        if(infLocalA_0)
                        {

#line 2382
                            bb_0 = max(ovAcc_1, 2080374799U);

#line 2382
                        }
                        else
                        {

#line 2382
                            bb_0 = ovAcc_1;

#line 2382
                        }

#line 2382
                        bool _S191 = spanB_0 != 0U;

#line 2382
                        if(_S191)
                        {

#line 2382
                            infLocalB_0 = (ovAcc_0 & 2147483648U) != 0U;

#line 2382
                        }
                        else
                        {

#line 2382
                            infLocalB_0 = false;

#line 2382
                        }

#line 2382
                        if(infLocalB_0)
                        {

#line 2382
                            bb_1 = max(ovAcc_2, 2080374799U);

#line 2382
                        }
                        else
                        {

#line 2382
                            bb_1 = ovAcc_2;

#line 2382
                        }

#line 2382
                        uint _S192 = (4095U - _S25) << 4U;

#line 2382
                        uint kA_0 = bb_0 | _S192;

#line 2382
                        uint kB_0 = bb_1 | _S192;

#line 2382
                        uint _S193 = (simd_shuffle_xor((kA_0), ushort((1U))));

#line 2382
                        uint _S194 = max(kA_0, _S193);

#line 2382
                        uint _S195 = (simd_shuffle_xor((kB_0), ushort((1U))));

#line 2382
                        uint _S196 = max(kB_0, _S195);

#line 2382
                        uint _S197 = (simd_shuffle_xor((_S194), ushort((2U))));

#line 2382
                        uint _S198 = max(_S194, _S197);

#line 2382
                        uint _S199 = (simd_shuffle_xor((_S196), ushort((2U))));

#line 2382
                        uint _S200 = max(_S196, _S199);

#line 2382
                        uint _S201 = (simd_shuffle_xor((_S198), ushort((4U))));

#line 2382
                        uint _S202 = max(_S198, _S201);

#line 2382
                        uint _S203 = (simd_shuffle_xor((_S200), ushort((4U))));

#line 2382
                        uint _S204 = max(_S200, _S203);

#line 2382
                        uint _S205 = (simd_shuffle_xor((_S202), ushort((8U))));

#line 2382
                        uint _S206 = max(_S202, _S205);

#line 2382
                        uint _S207 = (simd_shuffle_xor((_S204), ushort((8U))));

#line 2382
                        uint _S208 = max(_S204, _S207);

#line 2382
                        uint _S209 = (simd_shuffle_xor((_S206), ushort((16U))));

#line 2382
                        uint _S210 = max(_S206, _S209);

#line 2382
                        uint _S211 = (simd_shuffle_xor((_S208), ushort((16U))));

#line 2382
                        uint _S212 = max(_S208, _S211);

#line 2382
                        uint slotA_0 = 65535U - (_S210 & 65535U);

#line 2382
                        uint slotB_0 = 65535U - (_S212 & 65535U);

#line 2382
                        if(_S190)
                        {

#line 2382
                            hitLocalA_0 = (_S210 >> 16U) >= 31744U;

#line 2382
                        }
                        else
                        {

#line 2382
                            hitLocalA_0 = false;

#line 2382
                        }

#line 2382
                        if(_S191)
                        {

#line 2382
                            hitLocalB_0 = (_S212 >> 16U) >= 31744U;

#line 2382
                        }
                        else
                        {

#line 2382
                            hitLocalB_0 = false;

#line 2382
                        }

#line 2382
                        if(hitLocalA_0)
                        {

#line 2382
                            hitA_0 = true;

#line 2382
                        }
                        else
                        {

#line 2382
                            hitA_0 = (as_type<half>((ushort)((_S210 >> 16U)))) > (as_type<float>((_S33)));

#line 2382
                        }

#line 2382
                        if(hitLocalB_0)
                        {

#line 2382
                            hitB_0 = true;

#line 2382
                        }
                        else
                        {

#line 2382
                            hitB_0 = (as_type<half>((ushort)((_S212 >> 16U)))) > (as_type<float>((_S33)));

#line 2382
                        }

#line 2382
                        uint wA_0 = slotA_0 >> 4U;

#line 2382
                        uint _S213 = slotA_0 & 15U;

#line 2382
                        uint wB_0 = slotB_0 >> 4U;

#line 2382
                        uint _S214 = slotB_0 & 15U;

#line 2382
                        half2 _S215 = half2(float2(0.0f) );

#line 2382
                        j_0 = 0U;

#line 2382
                        db_0 = _S215;

#line 2382
                        half2 selB_0 = _S215;

#line 2382
                        for(;;)
                        {

#line 2382
                            if(j_0 < 16U)
                            {
                            }
                            else
                            {

#line 2382
                                break;
                            }

#line 2382
                            if(j_0 == _S213)
                            {

#line 2382
                                db_0 = half2(_S181[j_0].x, _S182[j_0].x);

#line 2382
                            }

#line 2382
                            if(j_0 == _S214)
                            {

#line 2382
                                selB_0 = half2(_S181[j_0].y, _S182[j_0].y);

#line 2382
                            }

#line 2382
                            j_0 = j_0 + 1U;

#line 2382
                        }

#line 2382
                        uint _S216 = (simd_shuffle_xor(((uint(as_type<ushort>(db_0[0U])) & 65535U) | (uint(as_type<ushort>(db_0[1U])) << 16U)), ushort((wA_0))));

#line 2382
                        half _S217 = as_type<half>(ushort(_S216 & 65535U));

#line 2382
                        half _S218 = as_type<half>(ushort((_S216 >> 16U) & 65535U));

#line 2382
                        uint _S219 = (simd_shuffle_xor(((uint(as_type<ushort>(selB_0[0U])) & 65535U) | (uint(as_type<ushort>(selB_0[1U])) << 16U)), ushort((wB_0))));

#line 2382
                        half _S220 = as_type<half>(ushort(_S219 & 65535U));

#line 2382
                        half _S221 = as_type<half>(ushort((_S219 >> 16U) & 65535U));

#line 2382
                        bool _S222 = _S25 == 0U;

#line 2382
                        bool _S223;

#line 2382
                        if(_S222)
                        {

#line 2382
                            _S223 = _S26;

#line 2382
                        }
                        else
                        {

#line 2382
                            _S223 = false;

#line 2382
                        }

#line 2382
                        int _S224;

#line 2382
                        if(_S223)
                        {

#line 2382
                            int device* _S225 = (&kernelContext_1)->entryPointParams_peakIdx_0+pairA_0;

#line 2382
                            if(hitA_0)
                            {

#line 2382
                                _S224 = int(slotToIndex_0(slotA_0));

#line 2382
                            }
                            else
                            {

#line 2382
                                _S224 = int(-1);

#line 2382
                            }

#line 2382
                            *_S225 = _S224;

#line 2382
                            packed_float2 device* _S226 = (&kernelContext_1)->entryPointParams_peakVal_0+pairA_0;

#line 2382
                            if(hitLocalA_0)
                            {

#line 2382
                                _S155 = float2(3.40282306073709653e+38f, 0.0f);

#line 2382
                            }
                            else
                            {

#line 2382
                                if(hitA_0)
                                {

#line 2382
                                    _S155 = float2(float(_S217), float(_S218));

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S155 = float2(0.0f, 0.0f);

#line 2382
                                }

#line 2382
                            }

#line 2382
                            *_S226 = packed_float2(_S155) ;

#line 2382
                        }

#line 2382
                        bool _S227;

#line 2382
                        if(_S222)
                        {

#line 2382
                            _S227 = _S27;

#line 2382
                        }
                        else
                        {

#line 2382
                            _S227 = false;

#line 2382
                        }

#line 2382
                        if(_S227)
                        {

#line 2382
                            int device* _S228 = (&kernelContext_1)->entryPointParams_peakIdx_0+pairB_0;

#line 2382
                            if(hitB_0)
                            {

#line 2382
                                _S224 = int(slotToIndex_0(slotB_0));

#line 2382
                            }
                            else
                            {

#line 2382
                                _S224 = int(-1);

#line 2382
                            }

#line 2382
                            *_S228 = _S224;

#line 2382
                            packed_float2 device* _S229 = (&kernelContext_1)->entryPointParams_peakVal_0+pairB_0;

#line 2382
                            if(hitLocalB_0)
                            {

#line 2382
                                _S155 = float2(3.40282306073709653e+38f, 0.0f);

#line 2382
                            }
                            else
                            {

#line 2382
                                if(hitB_0)
                                {

#line 2382
                                    _S155 = float2(float(_S220), float(_S221));

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S155 = float2(0.0f, 0.0f);

#line 2382
                                }

#line 2382
                            }

#line 2382
                            *_S229 = packed_float2(_S155) ;

#line 2382
                        }

#line 2382
                        break;
                    }

#line 2382
                }

#line 2382
                break;
            }

#line 2382
            break;
        }

#line 2370
        base_0 = base_0 + (&kernelContext_1)->entryPointParams_0->gridSize_0 * 4U;

#line 2370
    }

#line 2399
    return;
}
