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

#line 10 "mm_1024_fusedTierB_c16p2t8.slang"
constant array<uint, int(1088)> COARSE_TWT_DATA_0 = { { 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 508050432U, 575159296U, 615922688U, 642268159U, 668613631U, 683031551U, 696204286U, 709377022U, 722549757U, 735656956U, 743521275U, 750074874U, 756694009U, 763247608U, 769801207U, 15360U, 575159296U, 642268159U, 683031551U, 709377022U, 735656956U, 750074874U, 763247608U, 776354806U, 789462004U, 802569201U, 810433517U, 816987114U, 823475174U, 830028770U, 836451293U, 15360U, 615922688U, 683031551U, 722549757U, 750074874U, 769801207U, 789462004U, 807222255U, 816987114U, 826751972U, 836451293U, 846150614U, 855849934U, 865483718U, 873741244U, 878525362U, 15360U, 642268159U, 709377022U, 750074874U, 776354806U, 802569201U, 816987114U, 830028770U, 842939353U, 855849934U, 868629443U, 876886966U, 883243944U, 889535385U, 895761288U, 901921655U, 15360U, 668613631U, 735656956U, 769801207U, 802569201U, 820263912U, 836451293U, 852638673U, 868629443U, 878525362U, 886389664U, 894188428U, 901921655U, 909589343U, 917125958U, 924531499U, 15360U, 683031551U, 750074874U, 789462004U, 816987114U, 836451293U, 855849934U, 873741244U, 883243944U, 892615569U, 901921655U, 911096666U, 920075067U, 928922394U, 937638646U, 942815952U, 15360U, 696204286U, 763247608U, 807222255U, 830028770U, 852638673U, 873741244U, 884816804U, 895761288U, 906509161U, 917125958U, 927480608U, 937638646U, 943536841U, 948386457U, 953039461U, 15360U, 709377022U, 776354806U, 816987114U, 842939353U, 868629443U, 883243944U, 895761288U, 908016484U, 920075067U, 931871502U, 941439709U, 947010215U, 952384109U, 957561391U, 962542061U, 15360U, 722549757U, 789462004U, 826751972U, 855849934U, 878525362U, 892615569U, 906509161U, 920075067U, 933313288U, 942815952U, 949041810U, 955005519U, 960707079U, 966146490U, 971323753U, 15360U, 735656956U, 802569201U, 836451293U, 868629443U, 886389664U, 901921655U, 917125958U, 931871502U, 942815952U, 949697162U, 956316223U, 962542061U, 968505750U, 974076218U, 979253464U, 15360U, 743521275U, 810433517U, 846150614U, 876886966U, 894188428U, 911096666U, 927480608U, 941439709U, 949041810U, 956316223U, 963197413U, 969619844U, 975649053U, 981219504U, 986265661U, 15360U, 750074874U, 816987114U, 855849934U, 883243944U, 901921655U, 920075067U, 937638646U, 947010215U, 955005519U, 962542061U, 969619844U, 976173331U, 982136987U, 987576349U, 992294706U, 15360U, 756694009U, 823475174U, 865483718U, 889535385U, 909589343U, 928922394U, 943536841U, 952384109U, 960707079U, 968505750U, 975649053U, 982136987U, 987969554U, 993015557U, 997340634U, 15360U, 763247608U, 830028770U, 873741244U, 895761288U, 917125958U, 937638646U, 948386457U, 957561391U, 966146490U, 974076218U, 981219504U, 987576349U, 993015557U, 997668290U, 1001337973U, 15360U, 769801207U, 836451293U, 878525362U, 901921655U, 924531499U, 942815952U, 953039461U, 962542061U, 971323753U, 979253464U, 986265661U, 992294706U, 997340634U, 1001337973U, 1004220941U, 15360U, 776354806U, 842939353U, 883243944U, 908016484U, 931871502U, 947010215U, 957561391U, 967326120U, 976173331U, 984037490U, 990787467U, 996423199U, 1000879269U, 1004089918U, 1005989446U, 15360U, 782908405U, 849427412U, 887962525U, 914111312U, 939080432U, 951073404U, 961952246U, 971848031U, 980695226U, 988362759U, 994784915U, 999896325U, 1003565778U, 1005858574U, 1006640712U, 15360U, 789462004U, 855849934U, 892615569U, 920075067U, 942815952U, 955005519U, 966146490U, 976173331U, 984954973U, 992294706U, 998258067U, 1002648518U, 1005400142U, 1006577224U, 1006153086U, 15360U, 796015602U, 862272457U, 897334148U, 926038821U, 946289326U, 958872095U, 970209659U, 980236484U, 988821497U, 995767886U, 1001075853U, 1004679545U, 1006447377U, 1006414809U, 1004581290U, 15360U, 802569201U, 868629443U, 901921655U, 931871502U, 949697162U, 962542061U, 974076218U, 984037490U, 992294706U, 998782308U, 1003369219U, 1005989446U, 1006609992U, 1005236402U, 1001829444U, 15360U, 807222255U, 873741244U, 906509161U, 937638646U, 953039461U, 966146490U, 977746166U, 987576349U, 995440229U, 1001337973U, 1005072612U, 1006577224U, 1005956778U, 1003074405U, 997963179U, 15360U, 810433517U, 876886966U, 911096666U, 941439709U, 956316223U, 969619844U, 981219504U, 990787467U, 998258067U, 1003369219U, 1006120318U, 1006545480U, 1004384731U, 999929093U, 993048325U, 15360U, 813710316U, 880098223U, 915618635U, 944257730U, 959461911U, 972962125U, 984496231U, 993736407U, 1000617149U, 1004941589U, 1006642358U, 1005694934U, 1002026028U, 995800654U, 987150376U, 15360U, 816987114U, 883243944U, 920075067U, 947010215U, 962542061U, 976173331U, 987576349U, 996423199U, 1002648518U, 1005989446U, 1006545480U, 1004122686U, 998815076U, 990820235U, 980269252U, 15360U, 820263912U, 886389664U, 924531499U, 949697162U, 965556675U, 979253464U, 990394273U, 998782308U, 1004220941U, 1006577846U, 1005760370U, 1001829444U, 994817683U, 984987741U, 972470614U, 15360U, 823475174U, 889535385U, 928922394U, 952384109U, 968505750U, 982136987U, 993015557U, 1000879269U, 1005400142U, 1006609992U, 1004384731U, 998815076U, 990033847U, 978303212U, 963819996U, 15360U, 826751972U, 892615569U, 933313288U, 955005519U, 971323753U, 984954973U, 995440229U, 1002648518U, 1006185754U, 1006153086U, 1002484727U, 995145340U, 984528999U, 970766706U, 954382934U, 15360U, 830028770U, 895761288U, 937638646U, 957561391U, 974076218U, 987576349U, 997668290U, 1004089918U, 1006577224U, 1005236402U, 999929093U, 990820235U, 978303212U, 962574829U, 944290498U, 15360U, 833240032U, 898841472U, 940718819U, 960117263U, 976697609U, 990001079U, 999634205U, 1005203634U, 1006610394U, 1003795105U, 996783624U, 985839688U, 971356521U, 953727582U, 927513376U, 15360U, 836451293U, 901921655U, 942815952U, 962542061U, 979253464U, 992294706U, 1001337973U, 1005989446U, 1006153086U, 1001829444U, 993048325U, 980269252U, 963819996U, 944290498U, 905034606U, 15360U, 839728091U, 905001838U, 944913084U, 964966859U, 981678246U, 994457258U, 1002845078U, 1006512712U, 1005367424U, 999404852U, 988854265U, 974108986U, 955693639U, 928955162U, 881703851U, 15360U, 842939353U, 908016484U, 947010215U, 967326120U, 984037490U, 996423199U, 1004089918U, 1006632960U, 1004122686U, 996455967U, 984070258U, 967358888U, 947042983U, 908049252U, 842972121U, 15360U, 846150614U, 911096666U, 949041810U, 969619844U, 986265661U, 998258067U, 1005072612U, 1006545480U, 1002484727U, 993048325U, 978761954U, 960150031U, 936229628U, 886422432U, 782941173U, 15360U, 849427412U, 914111312U, 951073404U, 971848031U, 988362759U, 999896325U, 1005858574U, 1006022214U, 1000387797U, 989247459U, 972994893U, 952416877U, 917158726U, 855882702U, 575192064U, 15360U, 852638673U, 917125958U, 953039461U, 974076218U, 990394273U, 1001337973U, 1006316625U, 1005236402U, 997963179U, 984987741U, 966769073U, 944290498U, 897366916U, 810466285U, 2904210425U, 15360U, 855849934U, 920075067U, 955005519U, 976173331U, 992294706U, 1002648518U, 1006577224U, 1004122686U, 995145340U, 980269252U, 960150031U, 931904270U, 876919734U, 709409790U, 2977545186U, 15360U, 859061195U, 923089712U, 956906039U, 978270444U, 994129601U, 1003762337U, 1006675126U, 1002681286U, 991999816U, 975157543U, 953072229U, 914144080U, 839760859U, 2830547967U, 3022830521U, 15360U, 862272457U, 926038821U, 958872095U, 980236484U, 995767886U, 1004679545U, 1006414809U, 1000912037U, 988395527U, 969652612U, 945666741U, 895794056U, 789494772U, 2950085617U, 3046357888U, 15360U, 865483718U, 928922394U, 960707079U, 982136987U, 997340634U, 1005400142U, 1005956778U, 998815076U, 984528999U, 963819996U, 936229628U, 876919734U, 668646399U, 2996943828U, 3069098806U, 15360U, 868629443U, 931871502U, 962542061U, 984037490U, 998782308U, 1005989446U, 1005236402U, 996455967U, 980269252U, 957594159U, 920107835U, 842972121U, 2856893438U, 3030760360U, 3088956125U, 15360U, 871840704U, 934755074U, 964377044U, 985806920U, 1000158445U, 1006382041U, 1004253709U, 993769175U, 975681821U, 951106172U, 903527282U, 802601969U, 2954738671U, 3052518254U, 3099245172U, 15360U, 873741244U, 937638646U, 966146490U, 987576349U, 1001337973U, 1006577224U, 1003074405U, 990820235U, 970766706U, 944290498U, 886422432U, 709409790U, 2996943828U, 3073555237U, 3108878846U, 15360U, 875314105U, 939997929U, 967915935U, 989214691U, 1002451959U, 1006674504U, 1001567325U, 987609117U, 965589443U, 934787842U, 865516486U, 2789784575U, 3029187499U, 3090332368U, 3117726075U, 15360U, 876886966U, 941439709U, 969619844U, 990787467U, 1003369219U, 1006545480U, 999929093U, 984070258U, 960150031U, 920107835U, 830061538U, 2923871222U, 3049438071U, 3099900525U, 3125786860U, 15360U, 878525362U, 942815952U, 971323753U, 992294706U, 1004220941U, 1006153086U, 997963179U, 980269252U, 954382934U, 905034606U, 782941173U, 2977545186U, 3069098806U, 3108878846U, 3132930130U, 15360U, 880098223U, 944257730U, 972962125U, 993736407U, 1004941589U, 1005694934U, 995800654U, 976206099U, 948419225U, 889568153U, 683064319U, 3016145859U, 3087514345U, 3117136260U, 3139090270U, 15360U, 881671083U, 945633973U, 974600496U, 995112572U, 1005531165U, 1004974357U, 993441518U, 971880799U, 942193366U, 873774012U, 2816130047U, 3037051801U, 3096558226U, 3124738304U, 3144267272U, 15360U, 883243944U, 947010215U, 976173331U, 996423199U, 1005989446U, 1004122686U, 990820235U, 967358888U, 931904270U, 842972121U, 2923871222U, 3055532900U, 3105077807U, 3131553906U, 3148395685U, 15360U, 884816804U, 948386457U, 977746166U, 997668290U, 1006316625U, 1003074405U, 988002322U, 962574829U, 918666049U, 810466285U, 2974268388U, 3073555237U, 3113073091U, 3137517495U, 3151409775U, 15360U, 886389664U, 949697162U, 979253464U, 998782308U, 1006577846U, 1001829444U, 984987741U, 957594159U, 905034606U, 750107642U, 3009788873U, 3088956125U, 3120478541U, 3142628988U, 3153374990U, 15360U, 887962525U, 951073404U, 980695226U, 999896325U, 1006640712U, 1000387797U, 981711014U, 952416877U, 891141013U, 575192064U, 3032333220U, 3097213578U, 3127228622U, 3146888500U, 3154158774U, 15360U, 889535385U, 952384109U, 982136987U, 1000879269U, 1006609992U, 998815076U, 978303212U, 947042983U, 876919734U, 2856893438U, 3049438071U, 3105077807U, 3133323336U, 3150164934U, 3153734837U, 15360U, 891108245U, 953694814U, 983578748U, 1001796676U, 1006480145U, 997111281U, 974633264U, 941472477U, 852671441U, 2936978420U, 3066149697U, 3112483275U, 3138697077U, 3152458005U, 3152294215U, 15360U, 892615569U, 955005519U, 984954973U, 1002648518U, 1006153086U, 995145340U, 970766706U, 931904270U, 823507942U, 2977545186U, 3082271490U, 3119364447U, 3143284302U, 3153767605U, 3149673492U, 15360U, 894188428U, 956316223U, 986265661U, 1003369219U, 1005760370U, 993048325U, 966769073U, 920107835U, 782941173U, 3009788873U, 3092429500U, 3125786860U, 3147150621U, 3154125384U, 3146003836U, 15360U, 895761288U, 957561391U, 987576349U, 1004089918U, 1005236402U, 990820235U, 962574829U, 908049252U, 709409790U, 3030760360U, 3099900525U, 3131553906U, 3150164934U, 3153473094U, 3141220055U, 15360U, 897334148U, 958872095U, 988821497U, 1004679545U, 1004581290U, 988395527U, 958249511U, 895794056U, 2655566848U, 3046357888U, 3106978327U, 3136731107U, 3152326983U, 3151835611U, 3135453202U, 15360U, 898841472U, 960117263U, 990001079U, 1005203634U, 1003795105U, 985839688U, 953727582U, 883276712U, 2883173372U, 3061627728U, 3113662906U, 3141252823U, 3153636734U, 3149280324U, 3128703152U, 15360U, 900414331U, 961362430U, 991180661U, 1005662166U, 1002877846U, 983152775U, 949074578U, 868662211U, 2943532018U, 3076438810U, 3119954262U, 3145184706U, 3154157128U, 3145741715U, 3121035587U, 15360U, 901921655U, 962542061U, 992294706U, 1005989446U, 1001829444U, 980269252U, 944290498U, 842972121U, 2977545186U, 3088956125U, 3125786860U, 3148395685U, 3153734837U, 3141220055U, 3112450507U, 15360U, 903494514U, 963787228U, 993408750U, 1006251189U, 1000649917U, 977254656U, 939113200U, 817019882U, 3006577611U, 3095902873U, 3131095164U, 3150885635U, 3152556260U, 3135846407U, 3103144519U, 15360U, 905001838U, 964966859U, 994457258U, 1006512712U, 999404852U, 974108986U, 928955162U, 776387574U, 3027614639U, 3102521935U, 3135879175U, 3152720050U, 3150525285U, 3129620635U, 3093117621U, 15360U, 906509161U, 966146490U, 995440229U, 1006577224U, 997963179U, 970766706U, 918666049U, 709409790U, 3041704844U, 3108878846U, 3140204315U, 3153767605U, 3147642093U, 3122608423U, 3077913364U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 776354806U, 842939353U, 883243944U, 908016484U, 931871502U, 947010215U, 957561391U, 967326120U, 976173331U, 984037490U, 990787467U, 996423199U, 1000879269U, 1004089918U, 1005989446U, 15360U, 842939353U, 908016484U, 947010215U, 967326120U, 984037490U, 996423199U, 1004089918U, 1006632960U, 1004122686U, 996455967U, 984070258U, 967358888U, 947042983U, 908049252U, 842972121U, 15360U, 883243944U, 947010215U, 976173331U, 996423199U, 1005989446U, 1004122686U, 990820235U, 967358888U, 931904270U, 842972121U, 2923871222U, 3055532900U, 3105077807U, 3131553906U, 3148395685U } };

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
};


#line 308 "mm_1024_fusedTierB_c16p2t8.slang"
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

#line 92 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 232 "mm_1024_fusedTierB_c16p2t8.slang"
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


#line 171 "mm_1024_fusedTierB_c16p2t8.slang"
half2 cload_0(uint device* b_0, uint i_0)
{

#line 172
    uint p_0 = b_0[i_0];

#line 172
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 263
half2 dload_0(uint device* b_1, uint i_1)
{

#line 65 "twiddle.slang"
    uint _S7 = mfDataStrideFlag_0();

#line 265 "mm_1024_fusedTierB_c16p2t8.slang"
    if(_S7 != 0U)
    {

#line 73 "twiddle.slang"
        uint _S8 = mfDataScaleFlag_0();

#line 266 "mm_1024_fusedTierB_c16p2t8.slang"
        float s_0 = (as_type<float>((_S8)));
        uint _S9 = 2U * i_1;

#line 267
        return half2(half((as_type<float>((b_1[_S9]))) * s_0), half((as_type<float>((b_1[_S9 + 1U]))) * s_0));
    }
    return cload_0(b_1, i_1);
}


#line 399
void cmulconjs_0(half2 ar_0, half2 ai_0, half2 br_0, half2 bi_0, half2 thread* pr_0, half2 thread* pi_0)
{
    *pr_0 = ar_0 * br_0 + ai_0 * bi_0;
    *pi_0 = ai_0 * br_0 - ar_0 * bi_0;
    return;
}


#line 411
void r4s_0(array<half2, int(16)> thread* re_0, array<half2, int(16)> thread* im_0, uint a_0, uint b_2, uint c_0, uint d_1)
{
    half2 t0r_0 = (*re_0)[a_0] + (*re_0)[c_0];

#line 413
    half2 t0i_0 = (*im_0)[a_0] + (*im_0)[c_0];
    half2 t1r_0 = (*re_0)[a_0] - (*re_0)[c_0];

#line 414
    half2 t1i_0 = (*im_0)[a_0] - (*im_0)[c_0];
    half2 t2r_0 = (*re_0)[b_2] + (*re_0)[d_1];

#line 415
    half2 t2i_0 = (*im_0)[b_2] + (*im_0)[d_1];
    half2 t3r_0 = (*re_0)[b_2] - (*re_0)[d_1];
    half2 j3r_0 = - ((*im_0)[b_2] - (*im_0)[d_1]);
    (*re_0)[a_0] = t0r_0 + t2r_0;

#line 418
    (*im_0)[a_0] = t0i_0 + t2i_0;
    (*re_0)[b_2] = t1r_0 + j3r_0;

#line 419
    (*im_0)[b_2] = t1i_0 + t3r_0;
    (*re_0)[c_0] = t0r_0 - t2r_0;

#line 420
    (*im_0)[c_0] = t0i_0 - t2i_0;
    (*re_0)[d_1] = t1r_0 - j3r_0;

#line 421
    (*im_0)[d_1] = t1i_0 - t3r_0;
    return;
}


#line 411
void r4s_1(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint a_1, uint b_3, uint c_1, uint d_2)
{
    half2 t0r_1 = (*re_1)[a_1] + (*re_1)[c_1];

#line 413
    half2 t0i_1 = (*im_1)[a_1] + (*im_1)[c_1];
    half2 t1r_1 = (*re_1)[a_1] - (*re_1)[c_1];

#line 414
    half2 t1i_1 = (*im_1)[a_1] - (*im_1)[c_1];
    half2 t2r_1 = (*re_1)[b_3] + (*re_1)[d_2];

#line 415
    half2 t2i_1 = (*im_1)[b_3] + (*im_1)[d_2];
    half2 t3r_1 = (*re_1)[b_3] - (*re_1)[d_2];
    half2 j3r_1 = - ((*im_1)[b_3] - (*im_1)[d_2]);
    (*re_1)[a_1] = t0r_1 + t2r_1;

#line 418
    (*im_1)[a_1] = t0i_1 + t2i_1;
    (*re_1)[b_3] = t1r_1 + j3r_1;

#line 419
    (*im_1)[b_3] = t1i_1 + t3r_1;
    (*re_1)[c_1] = t0r_1 - t2r_1;

#line 420
    (*im_1)[c_1] = t0i_1 - t2i_1;
    (*re_1)[d_2] = t1r_1 - j3r_1;

#line 421
    (*im_1)[d_2] = t1i_1 - t3r_1;
    return;
}


#line 390
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 390
    half2 _S10 = half2(wr_0) ;

#line 390
    half2 _S11 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S11 + *xi_0 * _S10;
    *xr_0 = *xr_0 * _S10 - *xi_0 * _S11;

#line 394
    *xi_0 = ni_0;
    return;
}


#line 424
void swap2_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2, uint p_1, uint q_0)
{

    half2 t_0 = (*re_2)[p_1];

#line 427
    (*re_2)[p_1] = (*re_2)[q_0];

#line 427
    (*re_2)[q_0] = t_0;
    half2 t_1 = (*im_2)[p_1];

#line 428
    (*im_2)[p_1] = (*im_2)[q_0];

#line 428
    (*im_2)[q_0] = t_1;
    return;
}


#line 424
void swap2_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint p_2, uint q_1)
{

    half2 t_2 = (*re_3)[p_2];

#line 427
    (*re_3)[p_2] = (*re_3)[q_1];

#line 427
    (*re_3)[q_1] = t_2;
    half2 t_3 = (*im_3)[p_2];

#line 428
    (*im_3)[p_2] = (*im_3)[q_1];

#line 428
    (*im_3)[q_1] = t_3;
    return;
}


#line 462
void dft16s_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4)
{

#line 462
    uint n1_0 = 0U;

    for(;;)
    {

#line 464
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 464
            break;
        }

#line 464
        r4s_0(re_4, im_4, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 464
        n1_0 = n1_0 + 1U;

#line 464
    }


    cmulw_0(&(*re_4)[int(5)], &(*im_4)[int(5)], 0.923828125h, 0.382568359375h);
    cmulw_0(&(*re_4)[int(9)], &(*im_4)[int(9)], 0.70703125h, 0.70703125h);
    cmulw_0(&(*re_4)[int(13)], &(*im_4)[int(13)], 0.382568359375h, 0.923828125h);
    cmulw_0(&(*re_4)[int(6)], &(*im_4)[int(6)], 0.70703125h, 0.70703125h);
    cmulw_0(&(*re_4)[int(10)], &(*im_4)[int(10)], 0.0h, 1.0h);
    cmulw_0(&(*re_4)[int(14)], &(*im_4)[int(14)], -0.70703125h, 0.70703125h);
    cmulw_0(&(*re_4)[int(7)], &(*im_4)[int(7)], 0.382568359375h, 0.923828125h);
    cmulw_0(&(*re_4)[int(11)], &(*im_4)[int(11)], -0.70703125h, 0.70703125h);
    cmulw_0(&(*re_4)[int(15)], &(*im_4)[int(15)], -0.923828125h, -0.382568359375h);

#line 475
    uint k2_0 = 0U;
    for(;;)
    {

#line 476
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 476
            break;
        }

#line 477
        uint _S12 = 4U * k2_0;

#line 477
        r4s_0(re_4, im_4, _S12, _S12 + 1U, _S12 + 2U, _S12 + 3U);

#line 476
        k2_0 = k2_0 + 1U;

#line 476
    }

    swap2_0(re_4, im_4, 1U, 4U);

#line 478
    swap2_0(re_4, im_4, 2U, 8U);

#line 478
    swap2_0(re_4, im_4, 3U, 12U);
    swap2_0(re_4, im_4, 6U, 9U);

#line 479
    swap2_0(re_4, im_4, 7U, 13U);

#line 479
    swap2_0(re_4, im_4, 11U, 14U);
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
    float c_2 = 1.0f + z_0 * (-0.5f + z_0 * (0.0416666679084301f + z_0 * (-0.00138888892251998f + z_0 * (0.00002480158764229f + z_0 * -2.75573199814971304e-07f))));

    float s_1 = x_0 * (1.0f + z_0 * (-0.1666666716337204f + z_0 * (0.00833333376795053f + z_0 * (-0.0001984127011383f + z_0 * (2.75573188446287531e-06f + z_0 * -2.50521079436794025e-08f)))));


    switch(quadrant_0 & int(3))
    {
    case int(1):
        {

#line 119
            return float2(- s_1, c_2);
        }
    case int(2):
        {

#line 120
            return float2(- c_2, - s_1);
        }
    case int(3):
        {

#line 121
            return float2(s_1, - c_2);
        }
    default:
        {

#line 122
            return float2(c_2, s_1);
        }
    }

#line 122
}


#line 332 "mm_1024_fusedTierB_c16p2t8.slang"
uint computeWant_0(uint d_3, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S17 = max(TB_0, 1U);

#line 334
    uint j_0 = d_3 / _S17;

#line 334
    uint m_0 = d_3 % _S17;

#line 334
    uint _S18;
    if(TB_0 <= 16U)
    {

#line 335
        _S18 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 335
    }
    else
    {

#line 335
        _S18 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_3;

#line 335
    }

#line 335
    return _S18;
}


#line 308
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 308
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 308
    return;
}


#line 309
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_2)
{

#line 309
    return half2(as_type<half>(ushort(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 438
void dft4s_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5, uint o_0)
{
    uint _S19 = o_0 + 1U;

#line 440
    uint _S20 = o_0 + 2U;

#line 440
    r4s_1(re_5, im_5, o_0, _S19, _S20, o_0 + 3U);
    swap2_1(re_5, im_5, _S19, _S20);
    return;
}


#line 606
void innermostS_0(array<half2, int(16)> thread* re_6, array<half2, int(16)> thread* im_6)
{

#line 606
    uint b_4 = 0U;



    for(;;)
    {

#line 610
        if(b_4 < 4U)
        {
        }
        else
        {

#line 610
            break;
        }

#line 610
        dft4s_0(re_6, im_6, b_4 * 4U);

#line 610
        b_4 = b_4 + 1U;

#line 610
    }

    return;
}


#line 882
uint lgOf_0(uint i_4)
{

#line 882
    uint _S21;

#line 882
    if(i_4 < 2U)
    {

#line 882
        _S21 = 4U;

#line 882
    }
    else
    {

#line 882
        _S21 = 1U;

#line 882
    }

#line 882
    return _S21;
}


#line 884
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_1 = slot_0 >> lg_0;

#line 888
    uint lg_1 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_1;

#line 888
    uint lg_2 = lgOf_0(1U);

#line 888
    uint lg_3 = lgOf_0(0U);

#line 893
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | (x_2 & ((1U << lg_2) - 1U))) << lg_3) | ((x_2 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 486
half2 mag2s_0(half2 re_7, half2 im_7)
{

#line 486
    return re_7 * re_7 + im_7 * im_7;
}


#line 1817
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1817
    uint d_4;

#line 1817
    uint j_1;

#line 1817
    uint d_5;

#line 1817
    uint j_2;

#line 1817
    uint mb_0;

#line 1817
    uint mb_1;

#line 1817
    bool live_0;

#line 1817
    half2 bestH_0;

#line 1817
    bool _S22;

#line 1817
    half2 _S23;

#line 1817
    uint winner_0;

#line 1817
    float2 _S24;

#line 1817
    bool _S25;

#line 1817
    thread KernelContext_0 kernelContext_3;

#line 1817
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 1817
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1817
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1817
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1817
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1817
    (&kernelContext_3)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1817
    threadgroup array<uint, int(2048)> stg_1;

#line 1817
    (&kernelContext_3)->stg_0 = &stg_1;

#line 1817
    (&kernelContext_3)->_binPhase_0 = 0U;

#line 1838
    uint _S26 = lid_0.x;

#line 1838
    uint _sub_0 = _S26 / 64U;
    uint _pr_0 = gid_0.x * 2U + _sub_0;

#line 1839
    uint _t_0 = _S26 % 64U;
    (&kernelContext_3)->_stgBase_0 = _sub_0 * 1024U;

#line 1840
    uint _S27 = entryPointParams_1->ntmpl_0;

#line 1840
    uint _S28 = entryPointParams_1->winStart_0;

#line 1840
    uint _S29 = entryPointParams_1->winEnd_0;

#line 1840
    uint _S30 = entryPointParams_1->binsize_0;

#line 1840
    uint _S31 = entryPointParams_1->thrBits_0;

#line 1850
    for(;;)
    {

#line 1850
        thread uint _S32 = _S28;

#line 1850
        thread uint _S33 = _S29;

#line 1850
        (&kernelContext_3)->_tid_0 = _t_0;

#line 1850
        uint tiles_0 = (_S27 + 8U - 1U) / 8U;

#line 1850
        uint slots_0 = _S30 * tiles_0;

#line 1850
        bool slotOk_0 = _pr_0 < slots_0;

#line 1850
        uint q_2;

#line 1850
        if(slotOk_0)
        {

#line 1850
            q_2 = _pr_0;

#line 1850
        }
        else
        {

#line 1850
            q_2 = slots_0 - 1U;

#line 1850
        }

#line 1850
        uint d_6 = q_2 / tiles_0;

#line 1850
        uint t0_0 = (q_2 - d_6 * tiles_0) * 8U;

#line 1850
        uint _S34 = d_6 * _S27 + t0_0;

#line 1850
        rowWindow_0(d_6, &_S32, &_S33, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);

#line 1850
        thread array<half2, int(16)> dreg_0;

#line 1850
        uint n2_0 = 0U;

#line 1850
        for(;;)
        {

#line 1850
            if(n2_0 < 16U)
            {
            }
            else
            {

#line 1850
                break;
            }

#line 1850
            uint _S35 = mfDataStrideFlag_0();

#line 1850
            if(_S35 != 0U)
            {

#line 1850
                uint _S36 = mfDataStrideFlag_0();

#line 1850
                q_2 = _S36;

#line 1850
            }
            else
            {

#line 1850
                q_2 = 1024U;

#line 1850
            }

#line 1850
            half2 _S37 = dload_0((&kernelContext_3)->entryPointParams_data_0, d_6 * q_2 + _t_0 + 64U * n2_0);

#line 1850
            dreg_0[n2_0] = _S37;

#line 1850
            n2_0 = n2_0 + 1U;

#line 1850
        }

#line 1850
        uint k_0 = 0U;

#line 1850
        for(;;)
        {

#line 1850
            if(k_0 < 8U)
            {
            }
            else
            {

#line 1850
                break;
            }

#line 1850
            bool okA_0;

#line 1850
            if(slotOk_0)
            {

#line 1850
                okA_0 = (t0_0 + k_0) < _S27;

#line 1850
            }
            else
            {

#line 1850
                okA_0 = false;

#line 1850
            }

#line 1850
            bool okB_0;

#line 1850
            if(slotOk_0)
            {

#line 1850
                okB_0 = (t0_0 + k_0 + 1U) < _S27;

#line 1850
            }
            else
            {

#line 1850
                okB_0 = false;

#line 1850
            }

#line 1850
            if(okA_0)
            {

#line 1850
                q_2 = _S34 + k_0;

#line 1850
            }
            else
            {

#line 1850
                q_2 = 4294967295U;

#line 1850
            }

#line 1850
            if(okB_0)
            {

#line 1850
                n2_0 = _S34 + k_0 + 1U;

#line 1850
            }
            else
            {

#line 1850
                n2_0 = 4294967295U;

#line 1850
            }

#line 1850
            uint _S38 = t0_0 + k_0;

#line 1850
            uint _S39 = _S27 - 1U;

#line 1850
            uint _S40 = min(_S38, _S39);

#line 1850
            uint _S41 = min(_S38 + 1U, _S39);

#line 1850
            array<half2, int(16)> _S42 = dreg_0;

#line 1850
            uint _S43 = _S32;

#line 1850
            uint _S44 = _S33;

#line 1850
            for(;;)
            {

#line 1850
                thread array<half2, int(16)> re_8;

#line 1850
                thread array<half2, int(16)> im_8;

#line 1850
                uint n2_1 = 0U;

#line 1850
                for(;;)
                {

#line 1850
                    if(n2_1 < 16U)
                    {
                    }
                    else
                    {

#line 1850
                        break;
                    }

#line 1850
                    uint _S45 = 64U * n2_1;

#line 1850
                    half2 ta_0 = cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S40 * 1024U + _t_0 + _S45);

#line 1850
                    half2 tb_0 = cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S41 * 1024U + _t_0 + _S45);

#line 1850
                    half _S46 = _S42[n2_1].x;

#line 1850
                    half _S47 = _S42[n2_1].y;

#line 1850
                    cmulconjs_0(half2(_S46, _S46), half2(_S47, _S47), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_8[n2_1], &im_8[n2_1]);

#line 1850
                    n2_1 = n2_1 + 1U;

#line 1850
                }

#line 1850
                for(;;)
                {

#line 1850
                    uint lgTB_0 = firstbithigh_0(64U);

#line 1850
                    uint lgLn_0 = firstbithigh_0(1024U);

#line 1850
                    uint blk_1 = _t_0 >> lgTB_0;

#line 1850
                    uint lane_1 = _t_0 & 63U;

#line 1850
                    dft16s_0(&re_8, &im_8);

#line 1850
                    uint _S48 = mfCoarseTwtFlag_0();

#line 1850
                    uint z_1;

#line 1850
                    float cr_0;

#line 1850
                    float ci_0;

#line 1850
                    if(_S48 != 0U)
                    {

#line 1850
                        z_1 = 0U;

#line 1850
                        for(;;)
                        {

#line 1850
                            if(z_1 < 16U)
                            {
                            }
                            else
                            {

#line 1850
                                break;
                            }

#line 1850
                            uint _S49 = lane_1 * 16U + z_1;

#line 1850
                            cmulw_0(&re_8[z_1], &im_8[z_1], as_type<half>(ushort((COARSE_TWT_DATA_0[_S49]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S49]) >> 16U) & 65535U)));

#line 1850
                            z_1 = z_1 + 1U;

#line 1850
                        }

#line 1850
                    }
                    else
                    {

#line 1850
                        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 1024.0f);

#line 1850
                        float _S50 = tw_0.x;

#line 1850
                        float _S51 = tw_0.y;

#line 1850
                        z_1 = 0U;

#line 1850
                        cr_0 = 1.0f;

#line 1850
                        ci_0 = 0.0f;

#line 1850
                        for(;;)
                        {

#line 1850
                            if(z_1 < 16U)
                            {
                            }
                            else
                            {

#line 1850
                                break;
                            }

#line 1850
                            cmulw_0(&re_8[z_1], &im_8[z_1], half(cr_0), half(ci_0));

#line 1850
                            float nr_0 = cr_0 * _S50 - ci_0 * _S51;

#line 1850
                            float _S52 = cr_0 * _S51 + ci_0 * _S50;

#line 1850
                            z_1 = z_1 + 1U;

#line 1850
                            cr_0 = nr_0;

#line 1850
                            ci_0 = _S52;

#line 1850
                        }

#line 1850
                    }

#line 1850
                    uint per_1 = 16U / max(64U, 1U);

#line 1850
                    uint _S53 = max(4U, 1U);

#line 1850
                    uint blk2_1 = _t_0 / _S53;

#line 1850
                    uint lane2_1 = _t_0 % _S53;

#line 1850
                    for(;;)
                    {

#line 1850
                        thread array<half2, int(16)> outr_0;

#line 1850
                        thread array<half2, int(16)> outi_0;

#line 1850
                        z_1 = 0U;

#line 1850
                        for(;;)
                        {

#line 1850
                            if(z_1 < 16U)
                            {
                            }
                            else
                            {

#line 1850
                                break;
                            }

#line 1850
                            half2 _S54 = half2(float2(0.0f) );

#line 1850
                            outr_0[z_1] = _S54;

#line 1850
                            outi_0[z_1] = _S54;

#line 1850
                            z_1 = z_1 + 1U;

#line 1850
                        }

#line 1850
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 1850
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1850
                        uint p0_0 = computeWant_0(0U, 64U, 1024U, blk_1, lane_1, per_1, _S53, 64U, blk2_1, lane2_1);

#line 1850
                        uint _S55 = p0_0 & lenMask_0;

#line 1850
                        uint _S56 = (_S55 >> lgTB_0) * 64U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S55 & spanMask_0);

#line 1850
                        uint c_3 = 0U;

#line 1850
                        for(;;)
                        {

#line 1850
                            if(c_3 < 1U)
                            {
                            }
                            else
                            {

#line 1850
                                break;
                            }

#line 1850
                            for(;;)
                            {

#line 1850
                                for(;;)
                                {

#line 1850
                                    for(;;)
                                    {

#line 1850
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1850
                                        j_2 = 0U;

#line 1850
                                        for(;;)
                                        {

#line 1850
                                            if(j_2 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 1850
                                                break;
                                            }

#line 1850
                                            uint _S57 = j_2 * 64U + (&kernelContext_3)->_tid_0;

#line 1850
                                            stgPut_0(_S57, re_8[c_3 * 16U + j_2], &kernelContext_3);

#line 1850
                                            j_2 = j_2 + 1U;

#line 1850
                                        }

#line 1850
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1850
                                        d_4 = 0U;

#line 1850
                                        for(;;)
                                        {

#line 1850
                                            if(d_4 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 1850
                                                break;
                                            }

#line 1850
                                            uint pz_0 = computeWant_0(d_4, 64U, 1024U, 0U, 0U, per_1, _S53, 64U, 0U, 0U);

#line 1850
                                            uint _S58 = pz_0 & lenMask_0;

#line 1850
                                            uint az_0 = (_S58 >> lgTB_0) * 64U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S58 & spanMask_0);

#line 1850
                                            half2 _S59 = stgGet_0(_S56 + az_0 - c_3 * 16U * 64U, &kernelContext_3);

#line 1850
                                            outr_0[d_4] = _S59;

#line 1850
                                            d_4 = d_4 + 1U;

#line 1850
                                        }

#line 1850
                                        break;
                                    }

#line 1850
                                    break;
                                }

#line 1850
                                for(;;)
                                {

#line 1850
                                    for(;;)
                                    {

#line 1850
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1850
                                        j_1 = 0U;

#line 1850
                                        for(;;)
                                        {

#line 1850
                                            if(j_1 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 1850
                                                break;
                                            }

#line 1850
                                            uint _S60 = j_1 * 64U + (&kernelContext_3)->_tid_0;

#line 1850
                                            stgPut_0(_S60, im_8[c_3 * 16U + j_1], &kernelContext_3);

#line 1850
                                            j_1 = j_1 + 1U;

#line 1850
                                        }

#line 1850
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1850
                                        d_5 = 0U;

#line 1850
                                        for(;;)
                                        {

#line 1850
                                            if(d_5 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 1850
                                                break;
                                            }

#line 1850
                                            uint pz_1 = computeWant_0(d_5, 64U, 1024U, 0U, 0U, per_1, _S53, 64U, 0U, 0U);

#line 1850
                                            uint _S61 = pz_1 & lenMask_0;

#line 1850
                                            uint az_1 = (_S61 >> lgTB_0) * 64U + ((pz_1 >> lgLn_0) << lgTB_0) + (_S61 & spanMask_0);

#line 1850
                                            half2 _S62 = stgGet_0(_S56 + az_1 - c_3 * 16U * 64U, &kernelContext_3);

#line 1850
                                            outi_0[d_5] = _S62;

#line 1850
                                            d_5 = d_5 + 1U;

#line 1850
                                        }

#line 1850
                                        break;
                                    }

#line 1850
                                    break;
                                }

#line 1850
                                break;
                            }

#line 1850
                            c_3 = c_3 + 1U;

#line 1850
                        }

#line 1850
                        d_4 = 0U;

#line 1850
                        for(;;)
                        {

#line 1850
                            if(d_4 < 16U)
                            {
                            }
                            else
                            {

#line 1850
                                break;
                            }

#line 1850
                            re_8[d_4] = outr_0[d_4];

#line 1850
                            im_8[d_4] = outi_0[d_4];

#line 1850
                            d_4 = d_4 + 1U;

#line 1850
                        }

#line 1850
                        break;
                    }

#line 1850
                    for(;;)
                    {

#line 1850
                        uint lane_2 = _t_0 & 3U;

#line 1850
                        dft16s_0(&re_8, &im_8);

#line 1850
                        uint _S63 = mfCoarseTwtFlag_0();

#line 1850
                        if(_S63 != 0U)
                        {

#line 1850
                            j_1 = 0U;

#line 1850
                            for(;;)
                            {

#line 1850
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 1850
                                    break;
                                }

#line 1850
                                uint _S64 = 1024U + lane_2 * 16U + j_1;

#line 1850
                                cmulw_0(&re_8[j_1], &im_8[j_1], as_type<half>(ushort((COARSE_TWT_DATA_0[_S64]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S64]) >> 16U) & 65535U)));

#line 1850
                                j_1 = j_1 + 1U;

#line 1850
                            }

#line 1850
                        }
                        else
                        {

#line 1850
                            float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 64.0f);

#line 1850
                            float _S65 = tw_1.x;

#line 1850
                            float _S66 = tw_1.y;

#line 1850
                            j_1 = 0U;

#line 1850
                            cr_0 = 1.0f;

#line 1850
                            ci_0 = 0.0f;

#line 1850
                            for(;;)
                            {

#line 1850
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 1850
                                    break;
                                }

#line 1850
                                cmulw_0(&re_8[j_1], &im_8[j_1], half(cr_0), half(ci_0));

#line 1850
                                float nr_1 = cr_0 * _S65 - ci_0 * _S66;

#line 1850
                                float _S67 = cr_0 * _S66 + ci_0 * _S65;

#line 1850
                                j_1 = j_1 + 1U;

#line 1850
                                cr_0 = nr_1;

#line 1850
                                ci_0 = _S67;

#line 1850
                            }

#line 1850
                        }

#line 1850
                        uint per_2 = 16U / _S53;

#line 1850
                        uint _S68 = max(0U, 1U);

#line 1850
                        uint blk2_2 = _t_0 / _S68;

#line 1850
                        uint lane2_2 = _t_0 % _S68;

#line 1850
                        for(;;)
                        {

#line 1850
                            uint _S69 = (&kernelContext_3)->_tid_0;

#line 1850
                            for(;;)
                            {

#line 1850
                                thread array<uint, int(16)> t_4;

#line 1850
                                j_1 = 0U;

#line 1850
                                for(;;)
                                {

#line 1850
                                    if(j_1 < 4U)
                                    {
                                    }
                                    else
                                    {

#line 1850
                                        break;
                                    }

#line 1850
                                    j_2 = 0U;

#line 1850
                                    for(;;)
                                    {

#line 1850
                                        if(j_2 < 4U)
                                        {
                                        }
                                        else
                                        {

#line 1850
                                            break;
                                        }

#line 1850
                                        t_4[j_2 * 4U + j_1] = (uint(as_type<ushort>(re_8[j_1 * 4U + j_2][0U])) & 65535U) | (uint(as_type<ushort>(re_8[j_1 * 4U + j_2][1U])) << 16U);

#line 1850
                                        j_2 = j_2 + 1U;

#line 1850
                                    }

#line 1850
                                    j_1 = j_1 + 1U;

#line 1850
                                }

#line 1850
                                uint _S70 = _S69 & 3U;

#line 1850
                                bool _S71 = (_S70 & 1U) != 0U;

#line 1850
                                if(_S71)
                                {

#line 1850
                                    d_5 = t_4[0U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    d_5 = t_4[1U];

#line 1850
                                }

#line 1850
                                uint partner_0 = (simd_shuffle_xor((d_5), ushort((1U))));

#line 1850
                                if(_S71)
                                {

#line 1850
                                    t_4[0U] = partner_0;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[1U] = partner_0;

#line 1850
                                }

#line 1850
                                uint _S72;

#line 1850
                                if(_S71)
                                {

#line 1850
                                    _S72 = t_4[2U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S72 = t_4[3U];

#line 1850
                                }

#line 1850
                                uint partner_1 = (simd_shuffle_xor((_S72), ushort((1U))));

#line 1850
                                if(_S71)
                                {

#line 1850
                                    t_4[2U] = partner_1;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[3U] = partner_1;

#line 1850
                                }

#line 1850
                                uint _S73;

#line 1850
                                if(_S71)
                                {

#line 1850
                                    _S73 = t_4[4U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S73 = t_4[5U];

#line 1850
                                }

#line 1850
                                uint partner_2 = (simd_shuffle_xor((_S73), ushort((1U))));

#line 1850
                                if(_S71)
                                {

#line 1850
                                    t_4[4U] = partner_2;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[5U] = partner_2;

#line 1850
                                }

#line 1850
                                uint _S74;

#line 1850
                                if(_S71)
                                {

#line 1850
                                    _S74 = t_4[6U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S74 = t_4[7U];

#line 1850
                                }

#line 1850
                                uint partner_3 = (simd_shuffle_xor((_S74), ushort((1U))));

#line 1850
                                if(_S71)
                                {

#line 1850
                                    t_4[6U] = partner_3;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[7U] = partner_3;

#line 1850
                                }

#line 1850
                                uint _S75;

#line 1850
                                if(_S71)
                                {

#line 1850
                                    _S75 = t_4[8U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S75 = t_4[9U];

#line 1850
                                }

#line 1850
                                uint partner_4 = (simd_shuffle_xor((_S75), ushort((1U))));

#line 1850
                                if(_S71)
                                {

#line 1850
                                    t_4[8U] = partner_4;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[9U] = partner_4;

#line 1850
                                }

#line 1850
                                uint _S76;

#line 1850
                                if(_S71)
                                {

#line 1850
                                    _S76 = t_4[10U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S76 = t_4[11U];

#line 1850
                                }

#line 1850
                                uint partner_5 = (simd_shuffle_xor((_S76), ushort((1U))));

#line 1850
                                if(_S71)
                                {

#line 1850
                                    t_4[10U] = partner_5;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[11U] = partner_5;

#line 1850
                                }

#line 1850
                                uint _S77;

#line 1850
                                if(_S71)
                                {

#line 1850
                                    _S77 = t_4[12U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S77 = t_4[13U];

#line 1850
                                }

#line 1850
                                uint partner_6 = (simd_shuffle_xor((_S77), ushort((1U))));

#line 1850
                                if(_S71)
                                {

#line 1850
                                    t_4[12U] = partner_6;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[13U] = partner_6;

#line 1850
                                }

#line 1850
                                uint _S78;

#line 1850
                                if(_S71)
                                {

#line 1850
                                    _S78 = t_4[14U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S78 = t_4[15U];

#line 1850
                                }

#line 1850
                                uint partner_7 = (simd_shuffle_xor((_S78), ushort((1U))));

#line 1850
                                if(_S71)
                                {

#line 1850
                                    t_4[14U] = partner_7;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[15U] = partner_7;

#line 1850
                                }

#line 1850
                                bool _S79 = (_S70 & 2U) != 0U;

#line 1850
                                uint _S80;

#line 1850
                                if(_S79)
                                {

#line 1850
                                    _S80 = t_4[0U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S80 = t_4[2U];

#line 1850
                                }

#line 1850
                                uint partner_8 = (simd_shuffle_xor((_S80), ushort((2U))));

#line 1850
                                if(_S79)
                                {

#line 1850
                                    t_4[0U] = partner_8;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[2U] = partner_8;

#line 1850
                                }

#line 1850
                                uint _S81;

#line 1850
                                if(_S79)
                                {

#line 1850
                                    _S81 = t_4[1U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S81 = t_4[3U];

#line 1850
                                }

#line 1850
                                uint partner_9 = (simd_shuffle_xor((_S81), ushort((2U))));

#line 1850
                                if(_S79)
                                {

#line 1850
                                    t_4[1U] = partner_9;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[3U] = partner_9;

#line 1850
                                }

#line 1850
                                uint _S82;

#line 1850
                                if(_S79)
                                {

#line 1850
                                    _S82 = t_4[4U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S82 = t_4[6U];

#line 1850
                                }

#line 1850
                                uint partner_10 = (simd_shuffle_xor((_S82), ushort((2U))));

#line 1850
                                if(_S79)
                                {

#line 1850
                                    t_4[4U] = partner_10;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[6U] = partner_10;

#line 1850
                                }

#line 1850
                                uint _S83;

#line 1850
                                if(_S79)
                                {

#line 1850
                                    _S83 = t_4[5U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S83 = t_4[7U];

#line 1850
                                }

#line 1850
                                uint partner_11 = (simd_shuffle_xor((_S83), ushort((2U))));

#line 1850
                                if(_S79)
                                {

#line 1850
                                    t_4[5U] = partner_11;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[7U] = partner_11;

#line 1850
                                }

#line 1850
                                uint _S84;

#line 1850
                                if(_S79)
                                {

#line 1850
                                    _S84 = t_4[8U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S84 = t_4[10U];

#line 1850
                                }

#line 1850
                                uint partner_12 = (simd_shuffle_xor((_S84), ushort((2U))));

#line 1850
                                if(_S79)
                                {

#line 1850
                                    t_4[8U] = partner_12;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[10U] = partner_12;

#line 1850
                                }

#line 1850
                                uint _S85;

#line 1850
                                if(_S79)
                                {

#line 1850
                                    _S85 = t_4[9U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S85 = t_4[11U];

#line 1850
                                }

#line 1850
                                uint partner_13 = (simd_shuffle_xor((_S85), ushort((2U))));

#line 1850
                                if(_S79)
                                {

#line 1850
                                    t_4[9U] = partner_13;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[11U] = partner_13;

#line 1850
                                }

#line 1850
                                uint _S86;

#line 1850
                                if(_S79)
                                {

#line 1850
                                    _S86 = t_4[12U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S86 = t_4[14U];

#line 1850
                                }

#line 1850
                                uint partner_14 = (simd_shuffle_xor((_S86), ushort((2U))));

#line 1850
                                if(_S79)
                                {

#line 1850
                                    t_4[12U] = partner_14;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[14U] = partner_14;

#line 1850
                                }

#line 1850
                                uint _S87;

#line 1850
                                if(_S79)
                                {

#line 1850
                                    _S87 = t_4[13U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S87 = t_4[15U];

#line 1850
                                }

#line 1850
                                uint partner_15 = (simd_shuffle_xor((_S87), ushort((2U))));

#line 1850
                                if(_S79)
                                {

#line 1850
                                    t_4[13U] = partner_15;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_4[15U] = partner_15;

#line 1850
                                }

#line 1850
                                uint i_5 = 0U;

#line 1850
                                for(;;)
                                {

#line 1850
                                    if(i_5 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1850
                                        break;
                                    }

#line 1850
                                    re_8[i_5] = half2(as_type<half>(ushort((t_4[i_5]) & 65535U)), as_type<half>(ushort(((t_4[i_5]) >> 16U) & 65535U)));

#line 1850
                                    i_5 = i_5 + 1U;

#line 1850
                                }

#line 1850
                                break;
                            }

#line 1850
                            uint _S88 = (&kernelContext_3)->_tid_0;

#line 1850
                            for(;;)
                            {

#line 1850
                                thread array<uint, int(16)> t_5;

#line 1850
                                uint r_0 = 0U;

#line 1850
                                for(;;)
                                {

#line 1850
                                    if(r_0 < 4U)
                                    {
                                    }
                                    else
                                    {

#line 1850
                                        break;
                                    }

#line 1850
                                    j_2 = 0U;

#line 1850
                                    for(;;)
                                    {

#line 1850
                                        if(j_2 < 4U)
                                        {
                                        }
                                        else
                                        {

#line 1850
                                            break;
                                        }

#line 1850
                                        t_5[j_2 * 4U + r_0] = (uint(as_type<ushort>(im_8[r_0 * 4U + j_2][0U])) & 65535U) | (uint(as_type<ushort>(im_8[r_0 * 4U + j_2][1U])) << 16U);

#line 1850
                                        j_2 = j_2 + 1U;

#line 1850
                                    }

#line 1850
                                    r_0 = r_0 + 1U;

#line 1850
                                }

#line 1850
                                uint _S89 = _S88 & 3U;

#line 1850
                                bool _S90 = (_S89 & 1U) != 0U;

#line 1850
                                if(_S90)
                                {

#line 1850
                                    j_2 = t_5[0U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    j_2 = t_5[1U];

#line 1850
                                }

#line 1850
                                uint partner_16 = (simd_shuffle_xor((j_2), ushort((1U))));

#line 1850
                                if(_S90)
                                {

#line 1850
                                    t_5[0U] = partner_16;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[1U] = partner_16;

#line 1850
                                }

#line 1850
                                uint _S91;

#line 1850
                                if(_S90)
                                {

#line 1850
                                    _S91 = t_5[2U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S91 = t_5[3U];

#line 1850
                                }

#line 1850
                                uint partner_17 = (simd_shuffle_xor((_S91), ushort((1U))));

#line 1850
                                if(_S90)
                                {

#line 1850
                                    t_5[2U] = partner_17;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[3U] = partner_17;

#line 1850
                                }

#line 1850
                                uint _S92;

#line 1850
                                if(_S90)
                                {

#line 1850
                                    _S92 = t_5[4U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S92 = t_5[5U];

#line 1850
                                }

#line 1850
                                uint partner_18 = (simd_shuffle_xor((_S92), ushort((1U))));

#line 1850
                                if(_S90)
                                {

#line 1850
                                    t_5[4U] = partner_18;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[5U] = partner_18;

#line 1850
                                }

#line 1850
                                uint _S93;

#line 1850
                                if(_S90)
                                {

#line 1850
                                    _S93 = t_5[6U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S93 = t_5[7U];

#line 1850
                                }

#line 1850
                                uint partner_19 = (simd_shuffle_xor((_S93), ushort((1U))));

#line 1850
                                if(_S90)
                                {

#line 1850
                                    t_5[6U] = partner_19;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[7U] = partner_19;

#line 1850
                                }

#line 1850
                                uint _S94;

#line 1850
                                if(_S90)
                                {

#line 1850
                                    _S94 = t_5[8U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S94 = t_5[9U];

#line 1850
                                }

#line 1850
                                uint partner_20 = (simd_shuffle_xor((_S94), ushort((1U))));

#line 1850
                                if(_S90)
                                {

#line 1850
                                    t_5[8U] = partner_20;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[9U] = partner_20;

#line 1850
                                }

#line 1850
                                uint _S95;

#line 1850
                                if(_S90)
                                {

#line 1850
                                    _S95 = t_5[10U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S95 = t_5[11U];

#line 1850
                                }

#line 1850
                                uint partner_21 = (simd_shuffle_xor((_S95), ushort((1U))));

#line 1850
                                if(_S90)
                                {

#line 1850
                                    t_5[10U] = partner_21;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[11U] = partner_21;

#line 1850
                                }

#line 1850
                                uint _S96;

#line 1850
                                if(_S90)
                                {

#line 1850
                                    _S96 = t_5[12U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S96 = t_5[13U];

#line 1850
                                }

#line 1850
                                uint partner_22 = (simd_shuffle_xor((_S96), ushort((1U))));

#line 1850
                                if(_S90)
                                {

#line 1850
                                    t_5[12U] = partner_22;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[13U] = partner_22;

#line 1850
                                }

#line 1850
                                uint _S97;

#line 1850
                                if(_S90)
                                {

#line 1850
                                    _S97 = t_5[14U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S97 = t_5[15U];

#line 1850
                                }

#line 1850
                                uint partner_23 = (simd_shuffle_xor((_S97), ushort((1U))));

#line 1850
                                if(_S90)
                                {

#line 1850
                                    t_5[14U] = partner_23;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[15U] = partner_23;

#line 1850
                                }

#line 1850
                                bool _S98 = (_S89 & 2U) != 0U;

#line 1850
                                uint _S99;

#line 1850
                                if(_S98)
                                {

#line 1850
                                    _S99 = t_5[0U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S99 = t_5[2U];

#line 1850
                                }

#line 1850
                                uint partner_24 = (simd_shuffle_xor((_S99), ushort((2U))));

#line 1850
                                if(_S98)
                                {

#line 1850
                                    t_5[0U] = partner_24;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[2U] = partner_24;

#line 1850
                                }

#line 1850
                                uint _S100;

#line 1850
                                if(_S98)
                                {

#line 1850
                                    _S100 = t_5[1U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S100 = t_5[3U];

#line 1850
                                }

#line 1850
                                uint partner_25 = (simd_shuffle_xor((_S100), ushort((2U))));

#line 1850
                                if(_S98)
                                {

#line 1850
                                    t_5[1U] = partner_25;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[3U] = partner_25;

#line 1850
                                }

#line 1850
                                uint _S101;

#line 1850
                                if(_S98)
                                {

#line 1850
                                    _S101 = t_5[4U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S101 = t_5[6U];

#line 1850
                                }

#line 1850
                                uint partner_26 = (simd_shuffle_xor((_S101), ushort((2U))));

#line 1850
                                if(_S98)
                                {

#line 1850
                                    t_5[4U] = partner_26;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[6U] = partner_26;

#line 1850
                                }

#line 1850
                                uint _S102;

#line 1850
                                if(_S98)
                                {

#line 1850
                                    _S102 = t_5[5U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S102 = t_5[7U];

#line 1850
                                }

#line 1850
                                uint partner_27 = (simd_shuffle_xor((_S102), ushort((2U))));

#line 1850
                                if(_S98)
                                {

#line 1850
                                    t_5[5U] = partner_27;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[7U] = partner_27;

#line 1850
                                }

#line 1850
                                uint _S103;

#line 1850
                                if(_S98)
                                {

#line 1850
                                    _S103 = t_5[8U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S103 = t_5[10U];

#line 1850
                                }

#line 1850
                                uint partner_28 = (simd_shuffle_xor((_S103), ushort((2U))));

#line 1850
                                if(_S98)
                                {

#line 1850
                                    t_5[8U] = partner_28;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[10U] = partner_28;

#line 1850
                                }

#line 1850
                                uint _S104;

#line 1850
                                if(_S98)
                                {

#line 1850
                                    _S104 = t_5[9U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S104 = t_5[11U];

#line 1850
                                }

#line 1850
                                uint partner_29 = (simd_shuffle_xor((_S104), ushort((2U))));

#line 1850
                                if(_S98)
                                {

#line 1850
                                    t_5[9U] = partner_29;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[11U] = partner_29;

#line 1850
                                }

#line 1850
                                uint _S105;

#line 1850
                                if(_S98)
                                {

#line 1850
                                    _S105 = t_5[12U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S105 = t_5[14U];

#line 1850
                                }

#line 1850
                                uint partner_30 = (simd_shuffle_xor((_S105), ushort((2U))));

#line 1850
                                if(_S98)
                                {

#line 1850
                                    t_5[12U] = partner_30;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[14U] = partner_30;

#line 1850
                                }

#line 1850
                                uint _S106;

#line 1850
                                if(_S98)
                                {

#line 1850
                                    _S106 = t_5[13U];

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S106 = t_5[15U];

#line 1850
                                }

#line 1850
                                uint partner_31 = (simd_shuffle_xor((_S106), ushort((2U))));

#line 1850
                                if(_S98)
                                {

#line 1850
                                    t_5[13U] = partner_31;

#line 1850
                                }
                                else
                                {

#line 1850
                                    t_5[15U] = partner_31;

#line 1850
                                }

#line 1850
                                uint i_6 = 0U;

#line 1850
                                for(;;)
                                {

#line 1850
                                    if(i_6 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1850
                                        break;
                                    }

#line 1850
                                    im_8[i_6] = half2(as_type<half>(ushort((t_5[i_6]) & 65535U)), as_type<half>(ushort(((t_5[i_6]) >> 16U) & 65535U)));

#line 1850
                                    i_6 = i_6 + 1U;

#line 1850
                                }

#line 1850
                                break;
                            }

#line 1850
                            break;
                        }

#line 1850
                        break;
                    }

#line 1850
                    break;
                }

#line 1850
                innermostS_0(&re_8, &im_8);

#line 1850
                thread array<half2, int(16)> magv_0;

#line 1850
                uint i_7 = 0U;

#line 1850
                for(;;)
                {

#line 1850
                    if(i_7 < 16U)
                    {
                    }
                    else
                    {

#line 1850
                        break;
                    }

#line 1850
                    uint idx_0 = slotToIndex_0(_t_0 * 16U + i_7);

#line 1850
                    if(idx_0 >= _S43)
                    {

#line 1850
                        live_0 = idx_0 < _S44;

#line 1850
                    }
                    else
                    {

#line 1850
                        live_0 = false;

#line 1850
                    }

#line 1850
                    half2 mg_0 = mag2s_0(re_8[i_7], im_8[i_7]);

#line 1850
                    if(live_0)
                    {

#line 1850
                        bestH_0 = mg_0;

#line 1850
                    }
                    else
                    {

#line 1850
                        bestH_0 = half2(float2(0.0f) );

#line 1850
                    }

#line 1850
                    magv_0[i_7] = bestH_0;

#line 1850
                    if(live_0)
                    {

#line 1850
                        uint ov_0 = ((((uint(as_type<ushort>(re_8[i_7][0U])) & 65535U) | (uint(as_type<ushort>(re_8[i_7][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(im_8[i_7][0U])) & 65535U) | (uint(as_type<ushort>(im_8[i_7][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1850
                        uint _S107 = (uint(as_type<ushort>(magv_0[i_7][0U])) & 65535U) | (uint(as_type<ushort>(magv_0[i_7][1U])) << 16U);

#line 1850
                        if((ov_0 & 32768U) != 0U)
                        {

#line 1850
                            mb_0 = (_S107 & 4294901760U) | 31744U;

#line 1850
                        }
                        else
                        {

#line 1850
                            mb_0 = _S107;

#line 1850
                        }

#line 1850
                        if((ov_0 & 2147483648U) != 0U)
                        {

#line 1850
                            mb_1 = (mb_0 & 65535U) | 2080374784U;

#line 1850
                        }
                        else
                        {

#line 1850
                            mb_1 = mb_0;

#line 1850
                        }

#line 1850
                        magv_0[i_7] = half2(as_type<half>(ushort(mb_1 & 65535U)), as_type<half>(ushort((mb_1 >> 16U) & 65535U)));

#line 1850
                    }

#line 1850
                    i_7 = i_7 + 1U;

#line 1850
                }

#line 1850
                array<half2, int(16)> _S108 = magv_0;

#line 1850
                array<half2, int(16)> _S109 = re_8;

#line 1850
                array<half2, int(16)> _S110 = im_8;

#line 1850
                for(;;)
                {

#line 1850
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1850
                    bool _S111 = _t_0 == 0U;

#line 1850
                    _S22 = _S111;

#line 1850
                    if(_S111)
                    {

#line 1850
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0] = _S31;

#line 1850
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U] = 4294967295U;

#line 1850
                    }

#line 1850
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1850
                    half2 _S112 = half2(float2(0.0f) );

#line 1850
                    _S23 = _S112;

#line 1850
                    mb_0 = 0U;

#line 1850
                    bestH_0 = _S112;

#line 1850
                    half2 poison_0 = _S112;

#line 1850
                    for(;;)
                    {

#line 1850
                        if(mb_0 < 16U)
                        {
                        }
                        else
                        {

#line 1850
                            break;
                        }

#line 1850
                        half2 _S113 = max(bestH_0, _S108[mb_0]);

#line 1850
                        half2 poison_1 = poison_0 + _S108[mb_0] * _S112;

#line 1850
                        mb_0 = mb_0 + 1U;

#line 1850
                        bestH_0 = _S113;

#line 1850
                        poison_0 = poison_1;

#line 1850
                    }

#line 1850
                    if(isnan(float(poison_0.x)))
                    {

#line 1850
                        mb_1 = 2139095040U;

#line 1850
                    }
                    else
                    {

#line 1850
                        mb_1 = (as_type<uint>((float(bestH_0.x))));

#line 1850
                    }

#line 1850
                    uint _S114 = max(_S31, mb_1);

#line 1850
                    if(_S114 > _S31)
                    {

#line 1850
                        uint _S115 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), _S114, memory_order_relaxed);

#line 1850
                    }

#line 1850
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1850
                    uint i_8 = 0U;

#line 1850
                    uint winner_1 = 4294967295U;

#line 1850
                    for(;;)
                    {

#line 1850
                        if(i_8 < 16U)
                        {
                        }
                        else
                        {

#line 1850
                            break;
                        }

#line 1850
                        uint _S116 = min((as_type<uint>((float(_S108[i_8].x)))), 2139095040U);

#line 1850
                        if(_S116 > _S31)
                        {

#line 1850
                            live_0 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0]) == _S116;

#line 1850
                        }
                        else
                        {

#line 1850
                            live_0 = false;

#line 1850
                        }

#line 1850
                        if(live_0)
                        {

#line 1850
                            winner_0 = min(winner_1, _t_0 * 16U + i_8);

#line 1850
                        }
                        else
                        {

#line 1850
                            winner_0 = winner_1;

#line 1850
                        }

#line 1850
                        i_8 = i_8 + 1U;

#line 1850
                        winner_1 = winner_0;

#line 1850
                    }

#line 1850
                    if(winner_1 != 4294967295U)
                    {

#line 1850
                        uint _S117 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), winner_1, memory_order_relaxed);

#line 1850
                    }

#line 1850
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1850
                    uint i_9 = 0U;

#line 1850
                    for(;;)
                    {

#line 1850
                        if(i_9 < 16U)
                        {
                        }
                        else
                        {

#line 1850
                            break;
                        }

#line 1850
                        if(q_2 != 4294967295U)
                        {

#line 1850
                            live_0 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U]) == (_t_0 * 16U + i_9);

#line 1850
                        }
                        else
                        {

#line 1850
                            live_0 = false;

#line 1850
                        }

#line 1850
                        if(live_0)
                        {

#line 1850
                            *((&kernelContext_3)->entryPointParams_peakIdx_0+q_2) = int(slotToIndex_0(_t_0 * 16U + i_9));

#line 1850
                            packed_float2 device* _S118 = (&kernelContext_3)->entryPointParams_peakVal_0+q_2;

#line 1850
                            if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0]) >= 2139095040U)
                            {

#line 1850
                                _S24 = float2(3.40282306073709653e+38f, 0.0f);

#line 1850
                            }
                            else
                            {

#line 1850
                                _S24 = float2(float(_S109[i_9].x), float(_S110[i_9].x));

#line 1850
                            }

#line 1850
                            *_S118 = packed_float2(_S24) ;

#line 1850
                        }

#line 1850
                        i_9 = i_9 + 1U;

#line 1850
                    }

#line 1850
                    if(q_2 != 4294967295U)
                    {

#line 1850
                        live_0 = _S111;

#line 1850
                    }
                    else
                    {

#line 1850
                        live_0 = false;

#line 1850
                    }

#line 1850
                    bool _S119;

#line 1850
                    if(live_0)
                    {

#line 1850
                        _S119 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U]) == 4294967295U;

#line 1850
                    }
                    else
                    {

#line 1850
                        _S119 = false;

#line 1850
                    }

#line 1850
                    if(_S119)
                    {

#line 1850
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+q_2) = int(-1);

#line 1850
                        *((&kernelContext_3)->entryPointParams_peakVal_0+q_2) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1850
                    }

#line 1850
                    break;
                }

#line 1850
                array<half2, int(16)> _S120 = magv_0;

#line 1850
                array<half2, int(16)> _S121 = re_8;

#line 1850
                array<half2, int(16)> _S122 = im_8;

#line 1850
                for(;;)
                {

#line 1850
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1850
                    if(_S22)
                    {

#line 1850
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0] = _S31;

#line 1850
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U] = 4294967295U;

#line 1850
                    }

#line 1850
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1850
                    uint i_10 = 0U;

#line 1850
                    half2 bestH_1 = _S23;

#line 1850
                    half2 poison_2 = _S23;

#line 1850
                    for(;;)
                    {

#line 1850
                        if(i_10 < 16U)
                        {
                        }
                        else
                        {

#line 1850
                            break;
                        }

#line 1850
                        half2 _S123 = max(bestH_1, _S120[i_10]);

#line 1850
                        half2 poison_3 = poison_2 + _S120[i_10] * _S23;

#line 1850
                        i_10 = i_10 + 1U;

#line 1850
                        bestH_1 = _S123;

#line 1850
                        poison_2 = poison_3;

#line 1850
                    }

#line 1850
                    uint _S124;

#line 1850
                    if(isnan(float(poison_2.y)))
                    {

#line 1850
                        _S124 = 2139095040U;

#line 1850
                    }
                    else
                    {

#line 1850
                        _S124 = (as_type<uint>((float(bestH_1.y))));

#line 1850
                    }

#line 1850
                    uint _S125 = max(_S31, _S124);

#line 1850
                    if(_S125 > _S31)
                    {

#line 1850
                        uint _S126 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), _S125, memory_order_relaxed);

#line 1850
                    }

#line 1850
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1850
                    uint i_11 = 0U;

#line 1850
                    winner_0 = 4294967295U;

#line 1850
                    for(;;)
                    {

#line 1850
                        if(i_11 < 16U)
                        {
                        }
                        else
                        {

#line 1850
                            break;
                        }

#line 1850
                        uint _S127 = min((as_type<uint>((float(_S120[i_11].y)))), 2139095040U);

#line 1850
                        if(_S127 > _S31)
                        {

#line 1850
                            _S25 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0]) == _S127;

#line 1850
                        }
                        else
                        {

#line 1850
                            _S25 = false;

#line 1850
                        }

#line 1850
                        if(_S25)
                        {

#line 1850
                            winner_0 = min(winner_0, _t_0 * 16U + i_11);

#line 1850
                        }

#line 1850
                        i_11 = i_11 + 1U;

#line 1850
                    }

#line 1850
                    if(winner_0 != 4294967295U)
                    {

#line 1850
                        uint _S128 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 1850
                    }

#line 1850
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1850
                    uint i_12 = 0U;

#line 1850
                    for(;;)
                    {

#line 1850
                        if(i_12 < 16U)
                        {
                        }
                        else
                        {

#line 1850
                            break;
                        }

#line 1850
                        if(n2_0 != 4294967295U)
                        {

#line 1850
                            _S25 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U]) == (_t_0 * 16U + i_12);

#line 1850
                        }
                        else
                        {

#line 1850
                            _S25 = false;

#line 1850
                        }

#line 1850
                        if(_S25)
                        {

#line 1850
                            *((&kernelContext_3)->entryPointParams_peakIdx_0+n2_0) = int(slotToIndex_0(_t_0 * 16U + i_12));

#line 1850
                            packed_float2 device* _S129 = (&kernelContext_3)->entryPointParams_peakVal_0+n2_0;

#line 1850
                            if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0]) >= 2139095040U)
                            {

#line 1850
                                _S24 = float2(3.40282306073709653e+38f, 0.0f);

#line 1850
                            }
                            else
                            {

#line 1850
                                _S24 = float2(float(_S121[i_12].y), float(_S122[i_12].y));

#line 1850
                            }

#line 1850
                            *_S129 = packed_float2(_S24) ;

#line 1850
                        }

#line 1850
                        i_12 = i_12 + 1U;

#line 1850
                    }

#line 1850
                    if(n2_0 != 4294967295U)
                    {

#line 1850
                        _S25 = _S22;

#line 1850
                    }
                    else
                    {

#line 1850
                        _S25 = false;

#line 1850
                    }

#line 1850
                    bool _S130;

#line 1850
                    if(_S25)
                    {

#line 1850
                        _S130 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U]) == 4294967295U;

#line 1850
                    }
                    else
                    {

#line 1850
                        _S130 = false;

#line 1850
                    }

#line 1850
                    if(_S130)
                    {

#line 1850
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+n2_0) = int(-1);

#line 1850
                        *((&kernelContext_3)->entryPointParams_peakVal_0+n2_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1850
                    }

#line 1850
                    break;
                }

#line 1850
                break;
            }

#line 1850
            k_0 = k_0 + 2U;

#line 1850
        }

#line 1850
        break;
    }

    return;
}
