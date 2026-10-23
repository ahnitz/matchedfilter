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
#ifndef MF_C16_RAW
#define MF_C16_RAW 0u
#endif

#line 11 "mm_1024_fusedTierB_c16p2t8.slang"
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


#line 303 "mm_1024_fusedTierB_c16p2t8.slang"
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


#line 230
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 104 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 233 "mm_1024_fusedTierB_c16p2t8.slang"
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


#line 72 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S5 = ((MF_DATA_STRIDE));

#line 75
    return _S5;
}



uint mfDataScaleFlag_0()
{
    ;
    uint _S6 = ((MF_DATA_SCALE_BITS));

#line 83
    return _S6;
}


#line 172 "mm_1024_fusedTierB_c16p2t8.slang"
half2 cload_0(uint device* b_0, uint i_0)
{

#line 173
    uint p_0 = b_0[i_0];

#line 173
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 258
half2 dload_0(uint device* b_1, uint i_1)
{

#line 77 "twiddle.slang"
    uint _S7 = mfDataStrideFlag_0();

#line 260 "mm_1024_fusedTierB_c16p2t8.slang"
    if(_S7 != 0U)
    {

#line 85 "twiddle.slang"
        uint _S8 = mfDataScaleFlag_0();

#line 261 "mm_1024_fusedTierB_c16p2t8.slang"
        float s_0 = (as_type<float>((_S8)));
        uint _S9 = 2U * i_1;

#line 262
        return half2(half((as_type<float>((b_1[_S9]))) * s_0), half((as_type<float>((b_1[_S9 + 1U]))) * s_0));
    }
    return cload_0(b_1, i_1);
}


#line 388
void cmulconjs_0(half2 ar_0, half2 ai_0, half2 br_0, half2 bi_0, half2 thread* pr_0, half2 thread* pi_0)
{
    *pr_0 = ar_0 * br_0 + ai_0 * bi_0;
    *pi_0 = ai_0 * br_0 - ar_0 * bi_0;
    return;
}


#line 400
void r4s_0(array<half2, int(16)> thread* re_0, array<half2, int(16)> thread* im_0, uint a_0, uint b_2, uint c_0, uint d_1)
{
    half2 t0r_0 = (*re_0)[a_0] + (*re_0)[c_0];

#line 402
    half2 t0i_0 = (*im_0)[a_0] + (*im_0)[c_0];
    half2 t1r_0 = (*re_0)[a_0] - (*re_0)[c_0];

#line 403
    half2 t1i_0 = (*im_0)[a_0] - (*im_0)[c_0];
    half2 t2r_0 = (*re_0)[b_2] + (*re_0)[d_1];

#line 404
    half2 t2i_0 = (*im_0)[b_2] + (*im_0)[d_1];
    half2 t3r_0 = (*re_0)[b_2] - (*re_0)[d_1];
    half2 j3r_0 = - ((*im_0)[b_2] - (*im_0)[d_1]);
    (*re_0)[a_0] = t0r_0 + t2r_0;

#line 407
    (*im_0)[a_0] = t0i_0 + t2i_0;
    (*re_0)[b_2] = t1r_0 + j3r_0;

#line 408
    (*im_0)[b_2] = t1i_0 + t3r_0;
    (*re_0)[c_0] = t0r_0 - t2r_0;

#line 409
    (*im_0)[c_0] = t0i_0 - t2i_0;
    (*re_0)[d_1] = t1r_0 - j3r_0;

#line 410
    (*im_0)[d_1] = t1i_0 - t3r_0;
    return;
}


#line 400
void r4s_1(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint a_1, uint b_3, uint c_1, uint d_2)
{
    half2 t0r_1 = (*re_1)[a_1] + (*re_1)[c_1];

#line 402
    half2 t0i_1 = (*im_1)[a_1] + (*im_1)[c_1];
    half2 t1r_1 = (*re_1)[a_1] - (*re_1)[c_1];

#line 403
    half2 t1i_1 = (*im_1)[a_1] - (*im_1)[c_1];
    half2 t2r_1 = (*re_1)[b_3] + (*re_1)[d_2];

#line 404
    half2 t2i_1 = (*im_1)[b_3] + (*im_1)[d_2];
    half2 t3r_1 = (*re_1)[b_3] - (*re_1)[d_2];
    half2 j3r_1 = - ((*im_1)[b_3] - (*im_1)[d_2]);
    (*re_1)[a_1] = t0r_1 + t2r_1;

#line 407
    (*im_1)[a_1] = t0i_1 + t2i_1;
    (*re_1)[b_3] = t1r_1 + j3r_1;

#line 408
    (*im_1)[b_3] = t1i_1 + t3r_1;
    (*re_1)[c_1] = t0r_1 - t2r_1;

#line 409
    (*im_1)[c_1] = t0i_1 - t2i_1;
    (*re_1)[d_2] = t1r_1 - j3r_1;

#line 410
    (*im_1)[d_2] = t1i_1 - t3r_1;
    return;
}


#line 379
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 379
    half2 _S10 = half2(wr_0) ;

#line 379
    half2 _S11 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S11 + *xi_0 * _S10;
    *xr_0 = *xr_0 * _S10 - *xi_0 * _S11;

#line 383
    *xi_0 = ni_0;
    return;
}


#line 413
void swap2_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2, uint p_1, uint q_0)
{

    half2 t_0 = (*re_2)[p_1];

#line 416
    (*re_2)[p_1] = (*re_2)[q_0];

#line 416
    (*re_2)[q_0] = t_0;
    half2 t_1 = (*im_2)[p_1];

#line 417
    (*im_2)[p_1] = (*im_2)[q_0];

#line 417
    (*im_2)[q_0] = t_1;
    return;
}


#line 413
void swap2_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint p_2, uint q_1)
{

    half2 t_2 = (*re_3)[p_2];

#line 416
    (*re_3)[p_2] = (*re_3)[q_1];

#line 416
    (*re_3)[q_1] = t_2;
    half2 t_3 = (*im_3)[p_2];

#line 417
    (*im_3)[p_2] = (*im_3)[q_1];

#line 417
    (*im_3)[q_1] = t_3;
    return;
}


#line 451
void dft16s_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4)
{

#line 451
    uint n1_0 = 0U;

    for(;;)
    {

#line 453
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 453
            break;
        }

#line 453
        r4s_0(re_4, im_4, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 453
        n1_0 = n1_0 + 1U;

#line 453
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

#line 464
    uint k2_0 = 0U;
    for(;;)
    {

#line 465
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 465
            break;
        }

#line 466
        uint _S12 = 4U * k2_0;

#line 466
        r4s_0(re_4, im_4, _S12, _S12 + 1U, _S12 + 2U, _S12 + 3U);

#line 465
        k2_0 = k2_0 + 1U;

#line 465
    }

    swap2_0(re_4, im_4, 1U, 4U);

#line 467
    swap2_0(re_4, im_4, 2U, 8U);

#line 467
    swap2_0(re_4, im_4, 3U, 12U);
    swap2_0(re_4, im_4, 6U, 9U);

#line 468
    swap2_0(re_4, im_4, 7U, 13U);

#line 468
    swap2_0(re_4, im_4, 11U, 14U);
    return;
}


#line 61 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S13 = ((MF_COARSE_TWT));

#line 64
    return _S13;
}


#line 88
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S14 = ((MF_ACCURATE_TRIG));

#line 91
    return _S14;
}


#line 127
float2 mfTwiddle_0(float angle_0)
{

#line 93
    uint _S15 = mfAccurateTrigFlag_0();

#line 129
    if(_S15 == 0U)
    {

#line 130
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

#line 143
            return float2(- s_1, c_2);
        }
    case int(2):
        {

#line 144
            return float2(- c_2, - s_1);
        }
    case int(3):
        {

#line 145
            return float2(s_1, - c_2);
        }
    default:
        {

#line 146
            return float2(c_2, s_1);
        }
    }

#line 146
}


#line 327 "mm_1024_fusedTierB_c16p2t8.slang"
uint computeWant_0(uint d_3, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S17 = max(TB_0, 1U);

#line 329
    uint j_0 = d_3 / _S17;

#line 329
    uint m_0 = d_3 % _S17;

#line 329
    uint _S18;
    if(TB_0 <= 16U)
    {

#line 330
        _S18 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 330
    }
    else
    {

#line 330
        _S18 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_3;

#line 330
    }

#line 330
    return _S18;
}


#line 303
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 303
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 303
    return;
}


#line 304
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_2)
{

#line 304
    return half2(as_type<half>(ushort(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 489
void exchangeS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_3)
{
    uint j_1;

    thread array<half2, int(16)> outr_0;

#line 493
    thread array<half2, int(16)> outi_0;

#line 493
    uint z_1 = 0U;
    for(;;)
    {

#line 494
        if(z_1 < 16U)
        {
        }
        else
        {

#line 494
            break;
        }

#line 494
        half2 _S19 = half2(float2(0.0f) );

#line 494
        outr_0[z_1] = _S19;

#line 494
        outi_0[z_1] = _S19;

#line 494
        z_1 = z_1 + 1U;

#line 494
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S20 = p0_0 & lenMask_0;
    uint _S21 = (_S20 >> lgSpan_0) * 64U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S20 & spanMask_0);

#line 499
    uint c_3 = 0U;
    for(;;)
    {

#line 500
        if(c_3 < 1U)
        {
        }
        else
        {

#line 500
            break;
        }

#line 500
        for(;;)
        {

#line 500
            for(;;)
            {

#line 501
                for(;;)
                {

#line 502
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 502
                    j_1 = 0U;
                    for(;;)
                    {

#line 503
                        if(j_1 < 16U)
                        {
                        }
                        else
                        {

#line 503
                            break;
                        }

#line 504
                        uint _S22 = j_1 * 64U + kernelContext_3->_tid_0;

#line 504
                        stgPut_0(_S22, (*re_5)[c_3 * 16U + j_1], kernelContext_3);

#line 503
                        j_1 = j_1 + 1U;

#line 503
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 505
                    uint d_4 = 0U;
                    for(;;)
                    {

#line 506
                        if(d_4 < 16U)
                        {
                        }
                        else
                        {

#line 506
                            break;
                        }
                        uint pz_0 = computeWant_0(d_4, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S23 = pz_0 & lenMask_0;
                        uint az_0 = (_S23 >> lgSpan_0) * 64U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S23 & spanMask_0);

#line 510
                        half2 _S24 = stgGet_0(_S21 + az_0 - c_3 * 16U * 64U, kernelContext_3);



                        outr_0[d_4] = _S24;

#line 506
                        d_4 = d_4 + 1U;

#line 506
                    }

#line 501
                    break;
                }

#line 501
                break;
            }

#line 501
            for(;;)
            {

#line 501
                for(;;)
                {

#line 502
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 502
                    uint j_2 = 0U;
                    for(;;)
                    {

#line 503
                        if(j_2 < 16U)
                        {
                        }
                        else
                        {

#line 503
                            break;
                        }

#line 504
                        uint _S25 = j_2 * 64U + kernelContext_3->_tid_0;

#line 504
                        stgPut_0(_S25, (*im_5)[c_3 * 16U + j_2], kernelContext_3);

#line 503
                        j_2 = j_2 + 1U;

#line 503
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 505
                    uint d_5 = 0U;
                    for(;;)
                    {

#line 506
                        if(d_5 < 16U)
                        {
                        }
                        else
                        {

#line 506
                            break;
                        }
                        uint pz_1 = computeWant_0(d_5, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S26 = pz_1 & lenMask_0;
                        uint az_1 = (_S26 >> lgSpan_0) * 64U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S26 & spanMask_0);

#line 510
                        half2 _S27 = stgGet_0(_S21 + az_1 - c_3 * 16U * 64U, kernelContext_3);



                        outi_0[d_5] = _S27;

#line 506
                        d_5 = d_5 + 1U;

#line 506
                    }

#line 501
                    break;
                }

#line 501
                break;
            }

#line 501
            break;
        }

#line 500
        c_3 = c_3 + 1U;

#line 500
    }

#line 500
    j_1 = 0U;

#line 519
    for(;;)
    {

#line 519
        if(j_1 < 16U)
        {
        }
        else
        {

#line 519
            break;
        }

#line 519
        (*re_5)[j_1] = outr_0[j_1];

#line 519
        (*im_5)[j_1] = outi_0[j_1];

#line 519
        j_1 = j_1 + 1U;

#line 519
    }
    return;
}


#line 427
void dft4s_0(array<half2, int(16)> thread* re_6, array<half2, int(16)> thread* im_6, uint o_0)
{
    uint _S28 = o_0 + 1U;

#line 429
    uint _S29 = o_0 + 2U;

#line 429
    r4s_1(re_6, im_6, o_0, _S28, _S29, o_0 + 3U);
    swap2_1(re_6, im_6, _S28, _S29);
    return;
}


#line 522
void innermostS_0(array<half2, int(16)> thread* re_7, array<half2, int(16)> thread* im_7)
{

#line 522
    uint b_4 = 0U;



    for(;;)
    {

#line 526
        if(b_4 < 4U)
        {
        }
        else
        {

#line 526
            break;
        }

#line 526
        dft4s_0(re_7, im_7, b_4 * 4U);

#line 526
        b_4 = b_4 + 1U;

#line 526
    }

    return;
}


#line 815
uint lgOf_0(uint i_4)
{

#line 815
    uint _S30;

#line 815
    if(i_4 < 2U)
    {

#line 815
        _S30 = 4U;

#line 815
    }
    else
    {

#line 815
        _S30 = 1U;

#line 815
    }

#line 815
    return _S30;
}


#line 817
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_1 = slot_0 >> lg_0;

#line 821
    uint lg_1 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_1;

#line 821
    uint lg_2 = lgOf_0(1U);

#line 821
    uint lg_3 = lgOf_0(0U);

#line 826
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | (x_2 & ((1U << lg_2) - 1U))) << lg_3) | ((x_2 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 475
half2 mag2s_0(half2 re_8, half2 im_8)
{

#line 475
    return re_8 * re_8 + im_8 * im_8;
}


#line 110 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S31 = ((MF_C16_RAW));

#line 113
    return _S31;
}


#line 356 "mm_1024_fusedTierB_c16p2t8.slang"
float2 c16Bound_0(float2 v_1, float energy_0)
{

#line 115 "twiddle.slang"
    uint _S32 = mfC16RawFlag_0();

#line 358 "mm_1024_fusedTierB_c16p2t8.slang"
    if((1U - _S32) == 0U)
    {

#line 358
        return v_1;
    }

#line 359
    float m_1 = length(v_1);
    float b_5 = m_1 * 1.00146484375f + 0.00755659164860845f * sqrt(energy_0);

#line 360
    float2 _S33;
    if(m_1 > 0.0f)
    {

#line 361
        _S33 = v_1 * float2((b_5 / m_1)) ;

#line 361
    }
    else
    {

#line 361
        _S33 = float2(b_5, 0.0f);

#line 361
    }

#line 361
    return _S33;
}



float pairSum_0(uint tid_0, float v_2, KernelContext_0 thread* kernelContext_4)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_0] = (as_type<uint>((v_2)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 370
    uint k_0 = 0U;

#line 370
    float t_4 = 0.0f;

    for(;;)
    {

#line 372
        if(k_0 < 64U)
        {
        }
        else
        {

#line 372
            break;
        }

#line 372
        float t_5 = t_4 + (as_type<float>(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_0])));

#line 372
        k_0 = k_0 + 1U;

#line 372
        t_4 = t_5;

#line 372
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_4;
}


#line 1284
void peakLane_0(uint pair_0, uint tid_1, uint lane_2, const array<half2, int(16)> thread* magv_0, const array<half2, int(16)> thread* re_9, const array<half2, int(16)> thread* im_9, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint thrBits_1, float energy_1, KernelContext_0 thread* kernelContext_5)
{
    bool _S34;

    threadgroup_barrier(mem_flags::mem_threadgroup);
    bool _S35 = tid_1 == 0U;

#line 1289
    if(_S35)
    {

#line 1289
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 1289
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 1289
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1299
    half2 _S36 = half2(float2(0.0f) );

#line 1299
    half2 bestH_0 = _S36;

#line 1299
    uint i_5 = 0U;

#line 1299
    half2 poison_0 = _S36;
    for(;;)
    {

#line 1300
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1300
            break;
        }

#line 1300
        half2 _S37 = max(bestH_0, (*magv_0)[i_5]);

#line 1300
        half2 poison_1 = poison_0 + (*magv_0)[i_5] * _S36;

#line 1300
        uint i_6 = i_5 + 1U;

#line 1300
        bestH_0 = _S37;

#line 1300
        i_5 = i_6;

#line 1300
        poison_0 = poison_1;

#line 1300
    }
    bool _S38 = lane_2 == 0U;

#line 1301
    half _S39;

#line 1301
    if(_S38)
    {

#line 1301
        _S39 = poison_0.x;

#line 1301
    }
    else
    {

#line 1301
        _S39 = poison_0.y;

#line 1301
    }
    if(isnan(float(_S39)))
    {

#line 1302
        i_5 = 2139095040U;

#line 1302
    }
    else
    {

#line 1302
        if(_S38)
        {

#line 1302
            _S39 = bestH_0.x;

#line 1302
        }
        else
        {

#line 1302
            _S39 = bestH_0.y;

#line 1302
        }

#line 1302
        i_5 = (as_type<uint>((float(_S39))));

#line 1302
    }

#line 1302
    uint _S40 = max(thrBits_1, i_5);

#line 1307
    if(_S40 > thrBits_1)
    {

#line 1307
        uint _S41 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), _S40, memory_order_relaxed);

#line 1307
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1309
    uint winner_0 = 4294967295U;

#line 1309
    i_5 = 0U;


    for(;;)
    {

#line 1312
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1312
            break;
        }

#line 1313
        if(_S38)
        {

#line 1313
            _S39 = (*magv_0)[i_5].x;

#line 1313
        }
        else
        {

#line 1313
            _S39 = (*magv_0)[i_5].y;

#line 1313
        }

#line 1313
        uint _S42 = min((as_type<uint>((float(_S39)))), 2139095040U);
        if(_S42 > thrBits_1)
        {

#line 1314
            _S34 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0]) == _S42;

#line 1314
        }
        else
        {

#line 1314
            _S34 = false;

#line 1314
        }

#line 1314
        if(_S34)
        {

#line 1314
            winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 1314
        }

#line 1312
        i_5 = i_5 + 1U;

#line 1312
    }

#line 1322
    if(winner_0 != 4294967295U)
    {

#line 1322
        uint _S43 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 1322
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1324
    i_5 = 0U;
    for(;;)
    {

#line 1325
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1325
            break;
        }

#line 1326
        if(pair_0 != 4294967295U)
        {

#line 1326
            _S34 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U]) == (tid_1 * 16U + i_5);

#line 1326
        }
        else
        {

#line 1326
            _S34 = false;

#line 1326
        }

#line 1326
        if(_S34)
        {

#line 1327
            *(peakIdx_0+pair_0) = int(slotToIndex_0(tid_1 * 16U + i_5));

#line 1327
            packed_float2 device* _S44 = peakVal_0+pair_0;
            if(_S38)
            {

#line 1328
                _S39 = (*re_9)[i_5].x;

#line 1328
            }
            else
            {

#line 1328
                _S39 = (*re_9)[i_5].y;

#line 1328
            }

#line 1328
            float _S45 = float(_S39);

#line 1328
            half _S46;
            if(_S38)
            {

#line 1329
                _S46 = (*im_9)[i_5].x;

#line 1329
            }
            else
            {

#line 1329
                _S46 = (*im_9)[i_5].y;

#line 1329
            }

#line 1328
            float2 _S47 = c16Bound_0(float2(_S45, float(_S46)), energy_1);

#line 1328
            *_S44 = packed_float2(_S47) ;

#line 1326
        }

#line 1325
        i_5 = i_5 + 1U;

#line 1325
    }

#line 1332
    if(pair_0 != 4294967295U)
    {

#line 1332
        _S34 = _S35;

#line 1332
    }
    else
    {

#line 1332
        _S34 = false;

#line 1332
    }

#line 1332
    if(_S34)
    {

#line 1332
        _S34 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U]) == 4294967295U;

#line 1332
    }
    else
    {

#line 1332
        _S34 = false;

#line 1332
    }

#line 1332
    if(_S34)
    {

#line 1333
        *(peakIdx_0+pair_0) = int(-1);

#line 1333
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1332
    }



    return;
}


#line 1540
void filterTwo_0(uint pairA_0, uint pairB_0, uint tA_0, uint tB_0, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* tmpl_0, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{



    thread array<half2, int(16)> re_10;

#line 1545
    thread array<half2, int(16)> im_10;

#line 1545
    uint n2_0 = 0U;
    for(;;)
    {

#line 1546
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 1546
            break;
        }

#line 1547
        uint _S48 = 64U * n2_0;

#line 1547
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 1024U + tid_2 + _S48);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 1024U + tid_2 + _S48);
        half _S49 = (*dreg_0)[n2_0].x;
        half _S50 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S49, _S49), half2(_S50, _S50), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_10[n2_0], &im_10[n2_0]);

#line 1546
        n2_0 = n2_0 + 1U;

#line 1546
    }

#line 1559
    uint lgTB_0 = firstbithigh_0(64U);
    uint lgLn_0 = firstbithigh_0(1024U);
    uint blk_2 = tid_2 >> lgTB_0;
    uint lane_3 = tid_2 & 63U;

    dft16s_0(&re_10, &im_10);

#line 66 "twiddle.slang"
    uint _S51 = mfCoarseTwtFlag_0();

#line 66
    uint i_7;

#line 66
    float cr_0;

#line 66
    float ci_0;

#line 1566 "mm_1024_fusedTierB_c16p2t8.slang"
    if(_S51 != 0U)
    {

#line 1566
        i_7 = 0U;

#line 1573
        for(;;)
        {

#line 1573
            if(i_7 < 16U)
            {
            }
            else
            {

#line 1573
                break;
            }

#line 1574
            uint _S52 = lane_3 * 16U + i_7;
            cmulw_0(&re_10[i_7], &im_10[i_7], as_type<half>(ushort((COARSE_TWT_DATA_0[_S52]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S52]) >> 16U) & 65535U)));

#line 1573
            i_7 = i_7 + 1U;

#line 1573
        }

#line 1566
    }
    else
    {

#line 1582
        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 1024.0f);
        float _S53 = tw_0.x;

#line 1583
        float _S54 = tw_0.y;

#line 1583
        i_7 = 0U;

#line 1583
        cr_0 = 1.0f;

#line 1583
        ci_0 = 0.0f;

        for(;;)
        {

#line 1585
            if(i_7 < 16U)
            {
            }
            else
            {

#line 1585
                break;
            }

#line 1586
            cmulw_0(&re_10[i_7], &im_10[i_7], half(cr_0), half(ci_0));
            float nr_0 = cr_0 * _S53 - ci_0 * _S54;
            float _S55 = cr_0 * _S54 + ci_0 * _S53;

#line 1585
            i_7 = i_7 + 1U;

#line 1585
            cr_0 = nr_0;

#line 1585
            ci_0 = _S55;

#line 1585
        }

#line 1566
    }

#line 1592
    uint per_2 = 16U / max(64U, 1U);
    uint _S56 = max(4U, 1U);
    uint blk2_2 = tid_2 / _S56;

#line 1594
    uint lane2_2 = tid_2 % _S56;

#line 1594
    exchangeS_0(&re_10, &im_10, lgLn_0, lgTB_0, 64U, 1024U, blk_2, lane_3, per_2, _S56, 64U, blk2_2, lane2_2, kernelContext_6);

#line 1559
    uint lgTB_1 = firstbithigh_0(4U);

    uint blk_3 = tid_2 >> lgTB_1;
    uint lane_4 = tid_2 & 3U;

    dft16s_0(&re_10, &im_10);

#line 66 "twiddle.slang"
    uint _S57 = mfCoarseTwtFlag_0();

#line 1566 "mm_1024_fusedTierB_c16p2t8.slang"
    if(_S57 != 0U)
    {

#line 1566
        i_7 = 0U;

#line 1573
        for(;;)
        {

#line 1573
            if(i_7 < 16U)
            {
            }
            else
            {

#line 1573
                break;
            }

#line 1574
            uint _S58 = 1024U + lane_4 * 16U + i_7;
            cmulw_0(&re_10[i_7], &im_10[i_7], as_type<half>(ushort((COARSE_TWT_DATA_0[_S58]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S58]) >> 16U) & 65535U)));

#line 1573
            i_7 = i_7 + 1U;

#line 1573
        }

#line 1566
    }
    else
    {

#line 1582
        float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_4) / 64.0f);
        float _S59 = tw_1.x;

#line 1583
        float _S60 = tw_1.y;

#line 1583
        i_7 = 0U;

#line 1583
        cr_0 = 1.0f;

#line 1583
        ci_0 = 0.0f;

        for(;;)
        {

#line 1585
            if(i_7 < 16U)
            {
            }
            else
            {

#line 1585
                break;
            }

#line 1586
            cmulw_0(&re_10[i_7], &im_10[i_7], half(cr_0), half(ci_0));
            float nr_1 = cr_0 * _S59 - ci_0 * _S60;
            float _S61 = cr_0 * _S60 + ci_0 * _S59;

#line 1585
            i_7 = i_7 + 1U;

#line 1585
            cr_0 = nr_1;

#line 1585
            ci_0 = _S61;

#line 1585
        }

#line 1566
    }

#line 1592
    uint per_3 = 16U / _S56;
    uint _S62 = max(0U, 1U);
    uint blk2_3 = tid_2 / _S62;

#line 1594
    uint lane2_3 = tid_2 % _S62;

#line 1594
    exchangeS_0(&re_10, &im_10, lgTB_0, lgTB_1, 4U, 64U, blk_3, lane_4, per_3, _S62, 4U, blk2_3, lane2_3, kernelContext_6);


    innermostS_0(&re_10, &im_10);

#line 1621
    thread array<half2, int(16)> magv_1;



    half2 _S63 = half2(float2(0.0f) );
    half2 _S64 = half2(float2(0.015625f) );

#line 1626
    i_7 = 0U;

#line 1626
    half2 en_0 = _S63;
    for(;;)
    {

#line 1627
        if(i_7 < 16U)
        {
        }
        else
        {

#line 1627
            break;
        }

#line 1628
        uint idx_0 = slotToIndex_0(tid_2 * 16U + i_7);

#line 1628
        bool live_0;
        if(idx_0 >= winStart_3)
        {

#line 1629
            live_0 = idx_0 < winEnd_3;

#line 1629
        }
        else
        {

#line 1629
            live_0 = false;

#line 1629
        }
        half2 mg_0 = mag2s_0(re_10[i_7], im_10[i_7]);
        half2 sr_0 = re_10[i_7] * _S64;

#line 1631
        half2 si_0 = im_10[i_7] * _S64;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1632
        half2 _S65;
        if(live_0)
        {

#line 1633
            _S65 = mg_0;

#line 1633
        }
        else
        {

#line 1633
            _S65 = _S63;

#line 1633
        }

#line 1633
        magv_1[i_7] = _S65;

#line 1639
        if(live_0)
        {
            uint ov_0 = ((((uint(as_type<ushort>(re_10[i_7][0U])) & 65535U) | (uint(as_type<ushort>(re_10[i_7][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(im_10[i_7][0U])) & 65535U) | (uint(as_type<ushort>(im_10[i_7][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1641
            uint _S66 = (uint(as_type<ushort>(magv_1[i_7][0U])) & 65535U) | (uint(as_type<ushort>(magv_1[i_7][1U])) << 16U);

#line 1641
            uint mb_0;

            if((ov_0 & 32768U) != 0U)
            {

#line 1643
                mb_0 = (_S66 & 4294901760U) | 31744U;

#line 1643
            }
            else
            {

#line 1643
                mb_0 = _S66;

#line 1643
            }

#line 1643
            uint mb_1;
            if((ov_0 & 2147483648U) != 0U)
            {

#line 1644
                mb_1 = (mb_0 & 65535U) | 2080374784U;

#line 1644
            }
            else
            {

#line 1644
                mb_1 = mb_0;

#line 1644
            }
            magv_1[i_7] = half2(as_type<half>(ushort(mb_1 & 65535U)), as_type<half>(ushort((mb_1 >> 16U) & 65535U)));

#line 1639
        }

#line 1627
        i_7 = i_7 + 1U;

#line 1627
        en_0 = en_1;

#line 1627
    }

#line 1648
    float eB_0 = float(en_0.y) * 4096.0f;

#line 1648
    float _S67 = pairSum_0(tid_2, float(en_0.x) * 4096.0f, kernelContext_6);
    float eA_0 = _S67 / 1024.0f;

#line 1649
    float _S68 = pairSum_0(tid_2, eB_0, kernelContext_6);
    float eB_1 = _S68 / 1024.0f;

#line 1650
    thread array<half2, int(16)> _S69 = magv_1;

#line 1650
    thread array<half2, int(16)> _S70 = re_10;

#line 1650
    thread array<half2, int(16)> _S71 = im_10;

#line 1650
    peakLane_0(pairA_0, tid_2, 0U, &_S69, &_S70, &_S71, peakIdx_1, peakVal_1, winStart_3, winEnd_3, thrBits_2, eA_0, kernelContext_6);

#line 1650
    thread array<half2, int(16)> _S72 = magv_1;

#line 1650
    thread array<half2, int(16)> _S73 = re_10;

#line 1650
    thread array<half2, int(16)> _S74 = im_10;

#line 1650
    peakLane_0(pairB_0, tid_2, 1U, &_S72, &_S73, &_S74, peakIdx_1, peakVal_1, winStart_3, winEnd_3, thrBits_2, eB_1, kernelContext_6);



    return;
}


void filterPair_0(uint pair_1, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_2, packed_float2 device* peakVal_2, uint ntmpl_1, uint winStart_4, uint winEnd_4, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, uint device* rowWin_1, KernelContext_0 thread* kernelContext_7)
{

#line 1658
    thread uint _S75 = winStart_4;

#line 1658
    thread uint _S76 = winEnd_4;

#line 1664
    kernelContext_7->_tid_0 = tid_3;

#line 1684
    uint tiles_0 = (ntmpl_1 + 8U - 1U) / 8U;
    uint slots_0 = binsize_1 * tiles_0;
    bool slotOk_0 = pair_1 < slots_0;

#line 1686
    uint q_2;
    if(slotOk_0)
    {

#line 1687
        q_2 = pair_1;

#line 1687
    }
    else
    {

#line 1687
        q_2 = slots_0 - 1U;

#line 1687
    }
    uint d_6 = q_2 / tiles_0;

#line 1688
    uint t0_0 = (q_2 - d_6 * tiles_0) * 8U;
    uint _S77 = d_6 * ntmpl_1 + t0_0;

#line 1689
    rowWindow_0(d_6, &_S75, &_S76, rowWin_1, kernelContext_7);

#line 1714
    thread array<half2, int(16)> dreg_1;

#line 1714
    uint n2_1 = 0U;

    for(;;)
    {

#line 1716
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1716
            break;
        }

#line 77 "twiddle.slang"
        uint _S78 = mfDataStrideFlag_0();

#line 179 "mm_1024_fusedTierB_c16p2t8.slang"
        if(_S78 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S79 = mfDataStrideFlag_0();

#line 77
            q_2 = _S79;

#line 179 "mm_1024_fusedTierB_c16p2t8.slang"
        }
        else
        {

#line 179
            q_2 = 1024U;

#line 179
        }

#line 1717
        half2 _S80 = dload_0(data_0, d_6 * q_2 + tid_3 + 64U * n2_1);

#line 1717
        dreg_1[n2_1] = _S80;

#line 1716
        n2_1 = n2_1 + 1U;

#line 1716
    }

#line 1716
    uint k_1 = 0U;

#line 1724
    for(;;)
    {

#line 1724
        if(k_1 < 8U)
        {
        }
        else
        {

#line 1724
            break;
        }

#line 1724
        bool okA_0;
        if(slotOk_0)
        {

#line 1725
            okA_0 = (t0_0 + k_1) < ntmpl_1;

#line 1725
        }
        else
        {

#line 1725
            okA_0 = false;

#line 1725
        }

#line 1725
        bool okB_0;

#line 1725
        if(slotOk_0)
        {

#line 1725
            okB_0 = (t0_0 + k_1 + 1U) < ntmpl_1;

#line 1725
        }
        else
        {

#line 1725
            okB_0 = false;

#line 1725
        }
        if(okA_0)
        {

#line 1726
            q_2 = _S77 + k_1;

#line 1726
        }
        else
        {

#line 1726
            q_2 = 4294967295U;

#line 1726
        }

#line 1726
        if(okB_0)
        {

#line 1726
            n2_1 = _S77 + k_1 + 1U;

#line 1726
        }
        else
        {

#line 1726
            n2_1 = 4294967295U;

#line 1726
        }
        uint _S81 = t0_0 + k_1;

#line 1727
        uint _S82 = ntmpl_1 - 1U;

#line 1727
        uint _S83 = min(_S81, _S82);

#line 1727
        uint _S84 = min(_S81 + 1U, _S82);

#line 1727
        thread array<half2, int(16)> _S85 = dreg_1;

#line 1727
        filterTwo_0(q_2, n2_1, _S83, _S84, tid_3, &_S85, tmpl_1, peakIdx_2, peakVal_2, _S75, _S76, thrBits_3, kernelContext_7);

#line 1724
        k_1 = k_1 + 2U;

#line 1724
    }

#line 1740
    return;
}


#line 1753
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1753
    thread KernelContext_0 kernelContext_8;

#line 1753
    (&kernelContext_8)->entryPointParams_0 = entryPointParams_1;

#line 1753
    (&kernelContext_8)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1753
    (&kernelContext_8)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1753
    (&kernelContext_8)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1753
    (&kernelContext_8)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1753
    (&kernelContext_8)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1753
    threadgroup array<uint, int(2048)> stg_1;

#line 1753
    (&kernelContext_8)->stg_0 = &stg_1;

#line 1753
    (&kernelContext_8)->_binPhase_0 = 0U;

#line 1773
    uint _S86 = lid_0.x;

#line 1773
    uint _sub_0 = _S86 / 64U;
    uint _pr_0 = gid_0.x * 2U + _sub_0;

#line 1774
    uint _t_0 = _S86 % 64U;
    (&kernelContext_8)->_stgBase_0 = _sub_0 * 1024U;

#line 1775
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, entryPointParams_rowWin_1, &kernelContext_8);

#line 1788
    return;
}
