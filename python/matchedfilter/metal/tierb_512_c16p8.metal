#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
#ifndef MF_COARSE_TWT
#define MF_COARSE_TWT 0u
#endif
#ifndef MF_C16_RAW
#define MF_C16_RAW 0u
#endif

#line 11 "mm_512_fusedTierB_c16p8.slang"
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


#line 196 "mm_512_fusedTierB_c16p8.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 196
    return;
}


#line 167
half2 cload_0(uint device* b_0, uint i_0)
{

#line 168
    uint p_0 = b_0[i_0];

#line 168
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 202
half2 dload_0(uint device* b_1, uint i_1)
{

#line 208
    return cload_0(b_1, i_1);
}


#line 270
half2 cmulConj_0(half2 a_0, half2 b_2)
{

#line 270
    half _S2 = a_0.x;

#line 270
    half _S3 = b_2.x;

#line 270
    half _S4 = a_0.y;

#line 270
    half _S5 = b_2.y;

#line 270
    return half2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 475
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 477
    half2 t1_0 = *a_1 - *c_0;

#line 477
    half2 t2_0 = *b_3 + *d_1;

#line 477
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 479
    *b_3 = t1_0 + j3_0;

#line 479
    *c_0 = t0_0 - t2_0;

#line 479
    *d_1 = t1_0 - j3_0;
    return;
}


#line 269
half2 cmul_0(half2 a_2, half2 b_4)
{

#line 269
    half _S6 = a_2.x;

#line 269
    half _S7 = b_4.x;

#line 269
    half _S8 = a_2.y;

#line 269
    half _S9 = b_4.y;

#line 269
    return half2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 511
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125h, 0.382568359375h);
    half2 W2_0 = half2(0.70703125h, 0.70703125h);
    half2 W3_0 = half2(0.382568359375h, 0.923828125h);
    half2 W4_0 = half2(0.0h, 1.0h);
    half2 W6_0 = half2(-0.70703125h, 0.70703125h);
    half2 W9_0 = half2(-0.923828125h, -0.382568359375h);

#line 518
    uint n1_0 = 0U;
    for(;;)
    {

#line 519
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 519
            break;
        }

#line 519
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 519
        n1_0 = n1_0 + 1U;

#line 519
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 520
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 520
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 521
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 521
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 522
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 522
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 522
    uint k2_0 = 0U;
    for(;;)
    {

#line 523
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 523
            break;
        }

#line 523
        uint _S10 = 4U * k2_0;

#line 523
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 523
        k2_0 = k2_0 + 1U;

#line 523
    }

    half2 t_0 = (*r_0)[int(1)];

#line 525
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 525
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 526
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 526
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 527
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 527
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 528
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 528
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 529
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 529
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 530
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 530
    (*r_0)[int(14)] = t_5;
    return;
}


#line 52 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S11 = ((MF_COARSE_TWT));

#line 55
    return _S11;
}


#line 84
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 271 "mm_512_fusedTierB_c16p8.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 273
    uint j_0 = d_2 / _S12;

#line 273
    uint m_0 = d_2 % _S12;

#line 273
    uint _S13;
    if(TB_0 <= 16U)
    {

#line 274
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 274
    }
    else
    {

#line 274
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 274
    }

#line 274
    return _S13;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint ntmpl_0;
    uint winStart_1;
    uint winEnd_1;
    uint binsize_0;
    int binShift_0;
    uint nbins_0;
    uint thrBits_0;
};


#line 247 "mm_512_fusedTierB_c16p8.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(4096)> threadgroup* stg_0;
};


#line 247
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 247
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 247
    return;
}


#line 248
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 248
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 700
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 701
    uint j_1;

#line 712
    thread array<half2, int(16)> out_0;

#line 712
    uint z_0 = 0U;
    for(;;)
    {

#line 713
        if(z_0 < 16U)
        {
        }
        else
        {

#line 713
            break;
        }

#line 713
        out_0[z_0] = half2(0.0h, 0.0h);

#line 713
        z_0 = z_0 + 1U;

#line 713
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S14 = p0_0 & lenMask_0;

#line 719
    uint _S15 = (_S14 >> lgSpan_0) * 32U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);

#line 719
    uint c_1 = 0U;

    for(;;)
    {

#line 721
        if(c_1 < 1U)
        {
        }
        else
        {

#line 721
            break;
        }

#line 722
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 722
        j_1 = 0U;
        for(;;)
        {

#line 723
            if(j_1 < 16U)
            {
            }
            else
            {

#line 723
                break;
            }

#line 723
            stgPut_0(j_1 * 32U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 723
            j_1 = j_1 + 1U;

#line 723
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 724
        uint d_3 = 0U;
        for(;;)
        {

#line 725
            if(d_3 < 16U)
            {
            }
            else
            {

#line 725
                break;
            }

#line 726
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S16 = pz_0 & lenMask_0;
            uint az_0 = (_S16 >> lgSpan_0) * 32U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 728
            half2 _S17 = stgGet_0(_S15 + az_0 - c_1 * 16U * 32U, kernelContext_2);


            out_0[d_3] = _S17;

#line 725
            d_3 = d_3 + 1U;

#line 725
        }

#line 721
        c_1 = c_1 + 1U;

#line 721
    }

#line 721
    j_1 = 0U;

#line 734
    for(;;)
    {

#line 734
        if(j_1 < 16U)
        {
        }
        else
        {

#line 734
            break;
        }

#line 734
        (*r_1)[j_1] = out_0[j_1];

#line 734
        j_1 = j_1 + 1U;

#line 734
    }
    return;
}


#line 486
void dft2_0(array<half2, int(16)> thread* r_2, uint o_0)
{
    half2 a_3 = (*r_2)[o_0];

#line 488
    half2 b_5 = (*r_2)[o_0 + 1U];

#line 488
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 488
    (*r_2)[o_0 + 1U] = a_3 - b_5;
    return;
}


#line 614
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 614
    uint b_6 = 0U;

#line 624
    for(;;)
    {

#line 624
        if(b_6 < 8U)
        {
        }
        else
        {

#line 624
            break;
        }

#line 624
        dft2_0(r_3, b_6 * 2U);

#line 624
        b_6 = b_6 + 1U;

#line 624
    }

    return;
}


#line 802
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 11 "fft_transform.slang"
    uint lgTB_0 = firstbithigh_0(32U);
    uint lgLn_0 = firstbithigh_0(512U);
    uint blk_2 = tid_0 >> lgTB_0;
    uint lane_2 = tid_0 & 31U;


    dft16_0(r_4);

#line 57 "twiddle.slang"
    uint _S18 = mfCoarseTwtFlag_0();

#line 57
    uint k2_1;

#line 57
    float cr_0;

#line 57
    float ci_0;

#line 27 "fft_transform.slang"
    if(_S18 != 0U)
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
            uint _S19 = lane_2 * 16U + k2_1;

#line 31
            (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(as_type<half>(ushort((COARSE_TWT_DATA_0[_S19]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S19]) >> 16U) & 65535U))));

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
        float _S20 = tw_0.x;

#line 40
        float _S21 = tw_0.y;

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
            float nr_0 = cr_0 * _S20 - ci_0 * _S21;
            float _S22 = cr_0 * _S21 + ci_0 * _S20;

#line 42
            k2_1 = k2_1 + 1U;

#line 42
            cr_0 = nr_0;

#line 42
            ci_0 = _S22;

#line 42
        }

#line 27
    }

#line 50
    uint per_2 = 16U / max(32U, 1U);
    uint _S23 = max(2U, 1U);
    uint blk2_2 = tid_0 / _S23;

#line 52
    uint lane2_2 = tid_0 % _S23;

#line 52
    exchange_0(r_4, lgLn_0, lgTB_0, 32U, 512U, blk_2, lane_2, per_2, _S23, 32U, blk2_2, lane2_2, kernelContext_3);

#line 11
    uint lgTB_1 = firstbithigh_0(2U);

    uint blk_3 = tid_0 >> lgTB_1;
    uint lane_3 = tid_0 & 1U;


    dft16_0(r_4);

#line 57 "twiddle.slang"
    uint _S24 = mfCoarseTwtFlag_0();

#line 27 "fft_transform.slang"
    if(_S24 != 0U)
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
            uint _S25 = 512U + lane_3 * 16U + k2_1;

#line 31
            (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(as_type<half>(ushort((COARSE_TWT_DATA_0[_S25]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S25]) >> 16U) & 65535U))));

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
        float _S26 = tw_1.x;

#line 40
        float _S27 = tw_1.y;

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
            float nr_1 = cr_0 * _S26 - ci_0 * _S27;
            float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 42
            k2_1 = k2_1 + 1U;

#line 42
            cr_0 = nr_1;

#line 42
            ci_0 = _S28;

#line 42
        }

#line 27
    }

#line 50
    uint per_3 = 16U / _S23;
    uint _S29 = max(0U, 1U);
    uint blk2_3 = tid_0 / _S29;

#line 52
    uint lane2_3 = tid_0 % _S29;

#line 52
    exchange_0(r_4, lgTB_0, lgTB_1, 2U, 32U, blk_3, lane_3, per_3, _S29, 2U, blk2_3, lane2_3, kernelContext_3);



    innermost_0(r_4);

#line 805 "mm_512_fusedTierB_c16p8.slang"
    return;
}


#line 310
float pairSum_0(uint tid_1, float v_1, KernelContext_0 thread* kernelContext_4)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_1] = (as_type<uint>((v_1)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 314
    uint k_0 = 0U;

#line 314
    float t_6 = 0.0f;

    for(;;)
    {

#line 316
        if(k_0 < 32U)
        {
        }
        else
        {

#line 316
            break;
        }

#line 316
        float t_7 = t_6 + (as_type<float>(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_0])));

#line 316
        k_0 = k_0 + 1U;

#line 316
        t_6 = t_7;

#line 316
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_6;
}


#line 759
uint lgOf_0(uint i_4)
{

#line 759
    uint _S30;

#line 759
    if(i_4 < 2U)
    {

#line 759
        _S30 = 4U;

#line 759
    }
    else
    {

#line 759
        _S30 = 1U;

#line 759
    }

#line 759
    return _S30;
}


#line 761
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 765
    uint lg_1 = lgOf_0(1U);

#line 765
    uint lg_2 = lgOf_0(0U);

#line 770
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}



uint c16Mag_0(half2 v_2, uint slot_1, uint ws_0, uint we_0, bool ov_0)
{
    uint idx_0 = slotToIndex_0(slot_1);

#line 777
    bool live_0;
    if(idx_0 >= ws_0)
    {

#line 778
        live_0 = idx_0 < we_0;

#line 778
    }
    else
    {

#line 778
        live_0 = false;

#line 778
    }
    float x_1 = float(v_2.x);

#line 779
    float y_0 = float(v_2.y);

#line 779
    uint m_1;
    if(live_0)
    {

#line 780
        m_1 = (as_type<uint>((x_1 * x_1 + y_0 * y_0)));

#line 780
    }
    else
    {

#line 780
        m_1 = 0U;

#line 780
    }
    if(ov_0)
    {
    }
    else
    {

#line 781
        live_0 = false;

#line 781
    }

#line 781
    if(live_0)
    {

#line 781
        m_1 = 2139095040U;

#line 781
    }

#line 781
    return m_1;
}


#line 66 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S31 = ((MF_C16_RAW));

#line 69
    return _S31;
}


#line 300 "mm_512_fusedTierB_c16p8.slang"
float2 c16Bound_0(float2 v_3, float energy_0)
{

#line 71 "twiddle.slang"
    uint _S32 = mfC16RawFlag_0();

#line 302 "mm_512_fusedTierB_c16p8.slang"
    if((1U - _S32) == 0U)
    {

#line 302
        return v_3;
    }

#line 303
    float m_2 = length(v_3);
    float b_7 = m_2 * 1.00146484375f + 0.00686962902545929f * sqrt(energy_0);

#line 304
    float2 _S33;
    if(m_2 > 0.0f)
    {

#line 305
        _S33 = v_3 * float2((b_7 / m_2)) ;

#line 305
    }
    else
    {

#line 305
        _S33 = float2(b_7, 0.0f);

#line 305
    }

#line 305
    return _S33;
}


#line 811
void filterOne_0(uint pair_0, uint d_4, uint t_8, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{

#line 851
    thread array<half2, int(16)> r_5;

#line 851
    uint n2_0 = 0U;



    for(;;)
    {

#line 855
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 855
            break;
        }

#line 856
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_8 * 512U + tid_2 + 32U * n2_0));

#line 855
        n2_0 = n2_0 + 1U;

#line 855
    }

#line 855
    transform_0(&r_5, tid_2, kernelContext_5);

#line 855
    uint i_5 = 0U;

#line 855
    float energy_1 = 0.0f;

#line 885
    for(;;)
    {

#line 885
        if(i_5 < 16U)
        {
        }
        else
        {

#line 885
            break;
        }

#line 886
        float _ex_0 = float(r_5[i_5].x);

#line 886
        float _ey_0 = float(r_5[i_5].y);
        float energy_2 = energy_1 + (_ex_0 * _ex_0 + _ey_0 * _ey_0);

#line 885
        i_5 = i_5 + 1U;

#line 885
        energy_1 = energy_2;

#line 885
    }

#line 885
    float _S34 = pairSum_0(tid_2, energy_1, kernelContext_5);



    float energy_3 = _S34 / 512.0f;

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1001
    bool _S35 = tid_2 == 0U;

#line 1001
    if(_S35)
    {

#line 1001
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 1001
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 1001
    }

#line 1006
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1006
    i_5 = 0U;

#line 1006
    uint ovAcc_0 = 0U;

#line 1020
    for(;;)
    {

#line 1020
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1020
            break;
        }

#line 1021
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_5][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_5][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1020
        i_5 = i_5 + 1U;

#line 1020
        ovAcc_0 = ovAcc_1;

#line 1020
    }

    bool _S36 = (ovAcc_0 & 2147516416U) != 0U;

#line 1028
    half2 _S37 = half2(0.0h, 0.0h);

#line 1028
    uint bestBits_0 = thrBits_1;

#line 1028
    uint bestSlot_0 = 4294967295U;

#line 1028
    half2 bestV_0 = _S37;

#line 1028
    i_5 = 0U;
    for(;;)
    {

#line 1029
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1029
            break;
        }

#line 1030
        uint _S38 = tid_2 * 16U + i_5;

#line 1030
        uint m_3 = c16Mag_0(r_5[i_5], _S38, winStart_2, winEnd_2, _S36);
        if(m_3 > bestBits_0)
        {

#line 1031
            bestBits_0 = m_3;

#line 1031
            bestSlot_0 = _S38;

#line 1031
            bestV_0 = r_5[i_5];

#line 1031
        }

#line 1029
        i_5 = i_5 + 1U;

#line 1029
    }

#line 1037
    if(bestBits_0 > thrBits_1)
    {

#line 1037
        uint _S39 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), bestBits_0, memory_order_relaxed);

#line 1037
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    uint best_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1041
    bool _S40;
    if(bestSlot_0 != 4294967295U)
    {

#line 1042
        _S40 = bestBits_0 == best_0;

#line 1042
    }
    else
    {

#line 1042
        _S40 = false;

#line 1042
    }

#line 1042
    uint winner_0;

#line 1042
    if(_S40)
    {

#line 1042
        winner_0 = bestSlot_0;

#line 1042
    }
    else
    {

#line 1042
        winner_0 = 4294967295U;

#line 1042
    }

#line 1048
    bool _S41 = winner_0 != 4294967295U;

#line 1048
    if(_S41)
    {

#line 1048
        uint _S42 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 1048
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);
    uint wslot_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U];

    bool _S43 = pair_0 != 4294967295U;

#line 1053
    if(_S43)
    {

#line 1053
        _S40 = _S41;

#line 1053
    }
    else
    {

#line 1053
        _S40 = false;

#line 1053
    }

#line 1053
    if(_S40)
    {

#line 1053
        _S40 = winner_0 == wslot_0;

#line 1053
    }
    else
    {

#line 1053
        _S40 = false;

#line 1053
    }

#line 1053
    if(_S40)
    {

#line 1054
        *(peakIdx_0+pair_0) = int(slotToIndex_0(wslot_0));

#line 1054
        packed_float2 device* _S44 = peakVal_0+pair_0;
        float2 _S45 = c16Bound_0(float2(float(bestV_0.x), float(bestV_0.y)), energy_3);

#line 1055
        *_S44 = packed_float2(_S45) ;

#line 1053
    }



    if(_S43)
    {

#line 1057
        _S40 = _S35;

#line 1057
    }
    else
    {

#line 1057
        _S40 = false;

#line 1057
    }

#line 1057
    if(_S40)
    {

#line 1057
        _S40 = wslot_0 == 4294967295U;

#line 1057
    }
    else
    {

#line 1057
        _S40 = false;

#line 1057
    }

#line 1057
    if(_S40)
    {

#line 1058
        *(peakIdx_0+pair_0) = int(-1);

#line 1058
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1057
    }

#line 1205
    return;
}


#line 1601
void filterPair_0(uint pair_1, uint tid_3, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{

#line 1601
    thread uint _S46 = winStart_3;

#line 1601
    thread uint _S47 = winEnd_3;

#line 1607
    kernelContext_6->_tid_0 = tid_3;

#line 1641
    uint pairs_0 = binsize_2 * ntmpl_1;
    bool slotOk_0 = pair_1 < pairs_0;

#line 1642
    uint q_0;
    if(slotOk_0)
    {

#line 1643
        q_0 = pair_1;

#line 1643
    }
    else
    {

#line 1643
        q_0 = pairs_0 - 1U;

#line 1643
    }

#line 1643
    uint _S48;
    if(slotOk_0)
    {

#line 1644
        _S48 = q_0;

#line 1644
    }
    else
    {

#line 1644
        _S48 = 4294967295U;

#line 1644
    }
    uint d_5 = q_0 / ntmpl_1;

#line 1645
    uint _S49 = q_0 - d_5 * ntmpl_1;
    rowWindow_0(d_5, &_S46, &_S47);

#line 1657
    thread array<half2, int(16)> dreg_1;

#line 1657
    uint n2_1 = 0U;

    for(;;)
    {

#line 1659
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1659
            break;
        }

#line 1660
        dreg_1[n2_1] = dload_0(data_1, d_5 * 512U + tid_3 + 32U * n2_1);

#line 1659
        n2_1 = n2_1 + 1U;

#line 1659
    }

#line 1659
    uint k_1 = 0U;

#line 1679
    for(;;)
    {

#line 1679
        if(k_1 < 1U)
        {
        }
        else
        {

#line 1679
            break;
        }

#line 1680
        uint _S50 = _S48 + k_1;

#line 1680
        uint _S51 = _S49 + k_1;

#line 1680
        thread array<half2, int(16)> _S52 = dreg_1;

#line 1680
        filterOne_0(_S50, d_5, _S51, tid_3, &_S52, data_1, tmpl_1, peakIdx_1, peakVal_1, _S46, _S47, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1679
        k_1 = k_1 + 1U;

#line 1679
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1687
    thread KernelContext_0 kernelContext_7;

#line 1687
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1687
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1687
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1687
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1687
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1687
    threadgroup array<uint, int(4096)> stg_1;

#line 1687
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1707
    uint _S53 = lid_0.x;

#line 1707
    uint _sub_0 = _S53 / 32U;
    uint _pr_0 = gid_0.x * 8U + _sub_0;

#line 1708
    uint _t_0 = _S53 % 32U;
    (&kernelContext_7)->_stgBase_0 = _sub_0 * 512U;

#line 1709
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);



    return;
}
