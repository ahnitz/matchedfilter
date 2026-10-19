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

#line 11 "mm_1024_fusedTierB_c16.slang"
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


#line 210 "mm_1024_fusedTierB_c16.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0, uint device* rowWin_0)
{

#line 104 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 212 "mm_1024_fusedTierB_c16.slang"
    if(_S3 == 0U)
    {

#line 212
        return;
    }

#line 213
    uint _S4 = 2U * d_0;

#line 213
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



uint mfDataScaleFlag_0()
{
    ;
    uint _S6 = ((MF_DATA_SCALE_BITS));

#line 83
    return _S6;
}


#line 167 "mm_1024_fusedTierB_c16.slang"
half2 cload_0(uint device* b_0, uint i_0)
{

#line 168
    uint p_0 = b_0[i_0];

#line 168
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 234
half2 dload_0(uint device* b_1, uint i_1)
{

#line 77 "twiddle.slang"
    uint _S7 = mfDataStrideFlag_0();

#line 236 "mm_1024_fusedTierB_c16.slang"
    if(_S7 != 0U)
    {

#line 85 "twiddle.slang"
        uint _S8 = mfDataScaleFlag_0();

#line 237 "mm_1024_fusedTierB_c16.slang"
        float s_0 = (as_type<float>((_S8)));
        uint _S9 = 2U * i_1;

#line 238
        return half2(half((as_type<float>((b_1[_S9]))) * s_0), half((as_type<float>((b_1[_S9 + 1U]))) * s_0));
    }
    return cload_0(b_1, i_1);
}


#line 302
half2 cmulConj_0(half2 a_0, half2 b_2)
{

#line 302
    half _S10 = a_0.x;

#line 302
    half _S11 = b_2.x;

#line 302
    half _S12 = a_0.y;

#line 302
    half _S13 = b_2.y;

#line 302
    return half2(_S10 * _S11 + _S12 * _S13, _S12 * _S11 - _S10 * _S13);
}


#line 507
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 509
    half2 t1_0 = *a_1 - *c_0;

#line 509
    half2 t2_0 = *b_3 + *d_1;

#line 509
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 511
    *b_3 = t1_0 + j3_0;

#line 511
    *c_0 = t0_0 - t2_0;

#line 511
    *d_1 = t1_0 - j3_0;
    return;
}


#line 301
half2 cmul_0(half2 a_2, half2 b_4)
{

#line 301
    half _S14 = a_2.x;

#line 301
    half _S15 = b_4.x;

#line 301
    half _S16 = a_2.y;

#line 301
    half _S17 = b_4.y;

#line 301
    return half2(_S14 * _S15 - _S16 * _S17, _S14 * _S17 + _S16 * _S15);
}


#line 543
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125h, 0.382568359375h);
    half2 W2_0 = half2(0.70703125h, 0.70703125h);
    half2 W3_0 = half2(0.382568359375h, 0.923828125h);
    half2 W4_0 = half2(0.0h, 1.0h);
    half2 W6_0 = half2(-0.70703125h, 0.70703125h);
    half2 W9_0 = half2(-0.923828125h, -0.382568359375h);

#line 550
    uint n1_0 = 0U;
    for(;;)
    {

#line 551
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 551
            break;
        }

#line 551
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 551
        n1_0 = n1_0 + 1U;

#line 551
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 552
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 552
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 553
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 553
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 554
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 554
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 554
    uint k2_0 = 0U;
    for(;;)
    {

#line 555
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 555
            break;
        }

#line 555
        uint _S18 = 4U * k2_0;

#line 555
        r4_0(&(*r_0)[_S18], &(*r_0)[_S18 + 1U], &(*r_0)[_S18 + 2U], &(*r_0)[_S18 + 3U]);

#line 555
        k2_0 = k2_0 + 1U;

#line 555
    }

    half2 t_0 = (*r_0)[int(1)];

#line 557
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 557
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 558
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 558
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 559
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 559
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 560
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 560
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 561
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 561
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 562
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 562
    (*r_0)[int(14)] = t_5;
    return;
}


#line 61 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S19 = ((MF_COARSE_TWT));

#line 64
    return _S19;
}


#line 88
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S20 = ((MF_ACCURATE_TRIG));

#line 91
    return _S20;
}


#line 127
float2 mfTwiddle_0(float angle_0)
{

#line 93
    uint _S21 = mfAccurateTrigFlag_0();

#line 129
    if(_S21 == 0U)
    {

#line 130
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

#line 143
            return float2(- s_1, c_1);
        }
    case int(2):
        {

#line 144
            return float2(- c_1, - s_1);
        }
    case int(3):
        {

#line 145
            return float2(s_1, - c_1);
        }
    default:
        {

#line 146
            return float2(c_1, s_1);
        }
    }

#line 146
}


#line 303 "mm_1024_fusedTierB_c16.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S23 = max(TB_0, 1U);

#line 305
    uint j_0 = d_2 / _S23;

#line 305
    uint m_0 = d_2 % _S23;

#line 305
    uint _S24;
    if(TB_0 <= 16U)
    {

#line 306
        _S24 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 306
    }
    else
    {

#line 306
        _S24 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 306
    }

#line 306
    return _S24;
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


#line 279 "mm_1024_fusedTierB_c16.slang"
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
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 279
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 279
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 279
    return;
}


#line 280
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 280
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 732
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 733
    uint j_1;

#line 744
    thread array<half2, int(16)> out_0;

#line 744
    uint z_1 = 0U;
    for(;;)
    {

#line 745
        if(z_1 < 16U)
        {
        }
        else
        {

#line 745
            break;
        }

#line 745
        out_0[z_1] = half2(0.0h, 0.0h);

#line 745
        z_1 = z_1 + 1U;

#line 745
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S25 = p0_0 & lenMask_0;

#line 751
    uint _S26 = (_S25 >> lgSpan_0) * 64U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S25 & spanMask_0);

#line 751
    uint c_2 = 0U;

    for(;;)
    {

#line 753
        if(c_2 < 1U)
        {
        }
        else
        {

#line 753
            break;
        }

#line 754
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 754
        j_1 = 0U;
        for(;;)
        {

#line 755
            if(j_1 < 16U)
            {
            }
            else
            {

#line 755
                break;
            }

#line 755
            stgPut_0(j_1 * 64U + kernelContext_2->_tid_0, (*r_1)[c_2 * 16U + j_1], kernelContext_2);

#line 755
            j_1 = j_1 + 1U;

#line 755
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 756
        uint d_3 = 0U;
        for(;;)
        {

#line 757
            if(d_3 < 16U)
            {
            }
            else
            {

#line 757
                break;
            }

#line 758
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S27 = pz_0 & lenMask_0;
            uint az_0 = (_S27 >> lgSpan_0) * 64U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S27 & spanMask_0);

#line 760
            half2 _S28 = stgGet_0(_S26 + az_0 - c_2 * 16U * 64U, kernelContext_2);


            out_0[d_3] = _S28;

#line 757
            d_3 = d_3 + 1U;

#line 757
        }

#line 753
        c_2 = c_2 + 1U;

#line 753
    }

#line 753
    j_1 = 0U;

#line 766
    for(;;)
    {

#line 766
        if(j_1 < 16U)
        {
        }
        else
        {

#line 766
            break;
        }

#line 766
        (*r_1)[j_1] = out_0[j_1];

#line 766
        j_1 = j_1 + 1U;

#line 766
    }
    return;
}


#line 522
void dft4_0(array<half2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    half2 t_6 = (*r_2)[o_0 + 1U];

#line 525
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 525
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 646
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 646
    uint b_5 = 0U;

#line 655
    for(;;)
    {

#line 655
        if(b_5 < 4U)
        {
        }
        else
        {

#line 655
            break;
        }

#line 655
        dft4_0(r_3, b_5 * 4U);

#line 655
        b_5 = b_5 + 1U;

#line 655
    }


    return;
}


#line 834
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 11 "fft_transform.slang"
    uint lgTB_0 = firstbithigh_0(64U);
    uint lgLn_0 = firstbithigh_0(1024U);
    uint blk_2 = tid_0 >> lgTB_0;
    uint lane_2 = tid_0 & 63U;


    dft16_0(r_4);

#line 66 "twiddle.slang"
    uint _S29 = mfCoarseTwtFlag_0();

#line 66
    uint k2_1;

#line 66
    float cr_0;

#line 66
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
        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);
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
    uint per_2 = 16U / max(64U, 1U);
    uint _S34 = max(4U, 1U);
    uint blk2_2 = tid_0 / _S34;

#line 52
    uint lane2_2 = tid_0 % _S34;

#line 52
    exchange_0(r_4, lgLn_0, lgTB_0, 64U, 1024U, blk_2, lane_2, per_2, _S34, 64U, blk2_2, lane2_2, kernelContext_3);

#line 11
    uint lgTB_1 = firstbithigh_0(4U);

    uint blk_3 = tid_0 >> lgTB_1;
    uint lane_3 = tid_0 & 3U;


    dft16_0(r_4);

#line 66 "twiddle.slang"
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
            uint _S36 = 1024U + lane_3 * 16U + k2_1;

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
        float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 64.0f);
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
    exchange_0(r_4, lgTB_0, lgTB_1, 4U, 64U, blk_3, lane_3, per_3, _S40, 4U, blk2_3, lane2_3, kernelContext_3);



    innermost_0(r_4);

#line 837 "mm_1024_fusedTierB_c16.slang"
    return;
}


#line 342
float pairSum_0(uint tid_1, float v_1, KernelContext_0 thread* kernelContext_4)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_1] = (as_type<uint>((v_1)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 346
    uint k_0 = 0U;

#line 346
    float t_7 = 0.0f;

    for(;;)
    {

#line 348
        if(k_0 < 64U)
        {
        }
        else
        {

#line 348
            break;
        }

#line 348
        float t_8 = t_7 + (as_type<float>(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_0])));

#line 348
        k_0 = k_0 + 1U;

#line 348
        t_7 = t_8;

#line 348
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_7;
}


#line 791
uint lgOf_0(uint i_4)
{

#line 791
    uint _S41;

#line 791
    if(i_4 < 2U)
    {

#line 791
        _S41 = 4U;

#line 791
    }
    else
    {

#line 791
        _S41 = 1U;

#line 791
    }

#line 791
    return _S41;
}


#line 793
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_1 = slot_0 >> lg_0;

#line 797
    uint lg_1 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_1;

#line 797
    uint lg_2 = lgOf_0(1U);

#line 797
    uint lg_3 = lgOf_0(0U);

#line 802
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | (x_2 & ((1U << lg_2) - 1U))) << lg_3) | ((x_2 >> lg_2) & ((1U << lg_3) - 1U));
}



uint c16Mag_0(half2 v_2, uint slot_1, uint ws_0, uint we_0, bool ov_0)
{
    uint idx_0 = slotToIndex_0(slot_1);

#line 809
    bool live_0;
    if(idx_0 >= ws_0)
    {

#line 810
        live_0 = idx_0 < we_0;

#line 810
    }
    else
    {

#line 810
        live_0 = false;

#line 810
    }
    float x_3 = float(v_2.x);

#line 811
    float y_0 = float(v_2.y);

#line 811
    uint m_1;
    if(live_0)
    {

#line 812
        m_1 = (as_type<uint>((x_3 * x_3 + y_0 * y_0)));

#line 812
    }
    else
    {

#line 812
        m_1 = 0U;

#line 812
    }
    if(ov_0)
    {
    }
    else
    {

#line 813
        live_0 = false;

#line 813
    }

#line 813
    if(live_0)
    {

#line 813
        m_1 = 2139095040U;

#line 813
    }

#line 813
    return m_1;
}


#line 110 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S42 = ((MF_C16_RAW));

#line 113
    return _S42;
}


#line 332 "mm_1024_fusedTierB_c16.slang"
float2 c16Bound_0(float2 v_3, float energy_0)
{

#line 115 "twiddle.slang"
    uint _S43 = mfC16RawFlag_0();

#line 334 "mm_1024_fusedTierB_c16.slang"
    if((1U - _S43) == 0U)
    {

#line 334
        return v_3;
    }

#line 335
    float m_2 = length(v_3);
    float b_6 = m_2 * 1.00146484375f + 0.00755659164860845f * sqrt(energy_0);

#line 336
    float2 _S44;
    if(m_2 > 0.0f)
    {

#line 337
        _S44 = v_3 * float2((b_6 / m_2)) ;

#line 337
    }
    else
    {

#line 337
        _S44 = float2(b_6, 0.0f);

#line 337
    }

#line 337
    return _S44;
}


#line 843
void filterOne_0(uint pair_0, uint d_4, uint t_9, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{

#line 883
    thread array<half2, int(16)> r_5;

#line 883
    uint n2_0 = 0U;



    for(;;)
    {

#line 887
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 887
            break;
        }

#line 888
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_9 * 1024U + tid_2 + 64U * n2_0));

#line 887
        n2_0 = n2_0 + 1U;

#line 887
    }

#line 887
    transform_0(&r_5, tid_2, kernelContext_5);

#line 887
    uint i_5 = 0U;

#line 887
    float energy_1 = 0.0f;

#line 917
    for(;;)
    {

#line 917
        if(i_5 < 16U)
        {
        }
        else
        {

#line 917
            break;
        }

#line 918
        float _ex_0 = float(r_5[i_5].x);

#line 918
        float _ey_0 = float(r_5[i_5].y);
        float energy_2 = energy_1 + (_ex_0 * _ex_0 + _ey_0 * _ey_0);

#line 917
        i_5 = i_5 + 1U;

#line 917
        energy_1 = energy_2;

#line 917
    }

#line 917
    float _S45 = pairSum_0(tid_2, energy_1, kernelContext_5);



    float energy_3 = _S45 / 1024.0f;

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1033
    bool _S46 = tid_2 == 0U;

#line 1033
    if(_S46)
    {

#line 1033
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 1033
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 1033
    }

#line 1038
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1038
    i_5 = 0U;

#line 1038
    uint ovAcc_0 = 0U;

#line 1052
    for(;;)
    {

#line 1052
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1052
            break;
        }

#line 1053
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_5][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_5][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1052
        i_5 = i_5 + 1U;

#line 1052
        ovAcc_0 = ovAcc_1;

#line 1052
    }

    bool _S47 = (ovAcc_0 & 2147516416U) != 0U;

#line 1060
    half2 _S48 = half2(0.0h, 0.0h);

#line 1060
    uint bestBits_0 = thrBits_1;

#line 1060
    uint bestSlot_0 = 4294967295U;

#line 1060
    half2 bestV_0 = _S48;

#line 1060
    i_5 = 0U;
    for(;;)
    {

#line 1061
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1061
            break;
        }

#line 1062
        uint _S49 = tid_2 * 16U + i_5;

#line 1062
        uint m_3 = c16Mag_0(r_5[i_5], _S49, winStart_2, winEnd_2, _S47);
        if(m_3 > bestBits_0)
        {

#line 1063
            bestBits_0 = m_3;

#line 1063
            bestSlot_0 = _S49;

#line 1063
            bestV_0 = r_5[i_5];

#line 1063
        }

#line 1061
        i_5 = i_5 + 1U;

#line 1061
    }

#line 1066
    uint wm_0 = simd_max(bestBits_0);
    bool _S50 = simd_is_first();

#line 1067
    bool _S51;

#line 1067
    if(_S50)
    {

#line 1067
        _S51 = wm_0 > thrBits_1;

#line 1067
    }
    else
    {

#line 1067
        _S51 = false;

#line 1067
    }

#line 1067
    if(_S51)
    {

#line 1067
        uint _S52 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1067
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);

    uint best_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];
    if(bestSlot_0 != 4294967295U)
    {

#line 1074
        _S51 = bestBits_0 == best_0;

#line 1074
    }
    else
    {

#line 1074
        _S51 = false;

#line 1074
    }

#line 1074
    uint winner_0;

#line 1074
    if(_S51)
    {

#line 1074
        winner_0 = bestSlot_0;

#line 1074
    }
    else
    {

#line 1074
        winner_0 = 4294967295U;

#line 1074
    }

    uint waveWinner_0 = simd_min(winner_0);
    bool _S53 = simd_is_first();

#line 1077
    if(_S53)
    {

#line 1077
        _S51 = waveWinner_0 != 4294967295U;

#line 1077
    }
    else
    {

#line 1077
        _S51 = false;

#line 1077
    }

#line 1077
    if(_S51)
    {

#line 1078
        uint _S54 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1077
    }

#line 1082
    threadgroup_barrier(mem_flags::mem_threadgroup);
    uint wslot_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U];

    bool _S55 = pair_0 != 4294967295U;

#line 1085
    if(_S55)
    {

#line 1085
        _S51 = winner_0 != 4294967295U;

#line 1085
    }
    else
    {

#line 1085
        _S51 = false;

#line 1085
    }

#line 1085
    if(_S51)
    {

#line 1085
        _S51 = winner_0 == wslot_0;

#line 1085
    }
    else
    {

#line 1085
        _S51 = false;

#line 1085
    }

#line 1085
    if(_S51)
    {

#line 1086
        *(peakIdx_0+pair_0) = int(slotToIndex_0(wslot_0));

#line 1086
        packed_float2 device* _S56 = peakVal_0+pair_0;
        float2 _S57 = c16Bound_0(float2(float(bestV_0.x), float(bestV_0.y)), energy_3);

#line 1087
        *_S56 = packed_float2(_S57) ;

#line 1085
    }



    if(_S55)
    {

#line 1089
        _S51 = _S46;

#line 1089
    }
    else
    {

#line 1089
        _S51 = false;

#line 1089
    }

#line 1089
    if(_S51)
    {

#line 1089
        _S51 = wslot_0 == 4294967295U;

#line 1089
    }
    else
    {

#line 1089
        _S51 = false;

#line 1089
    }

#line 1089
    if(_S51)
    {

#line 1090
        *(peakIdx_0+pair_0) = int(-1);

#line 1090
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1089
    }

#line 1237
    return;
}


#line 1633
void filterPair_0(uint pair_1, uint tid_3, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, uint device* rowWin_1, KernelContext_0 thread* kernelContext_6)
{

#line 208
    uint k_1;

#line 1633
    thread uint _S58 = winStart_3;

#line 1633
    thread uint _S59 = winEnd_3;

#line 1639
    kernelContext_6->_tid_0 = tid_3;

#line 1681
    uint d_5 = pair_1 / ntmpl_1;

#line 1681
    uint _S60 = pair_1 % ntmpl_1;

#line 1686
    rowWindow_0(d_5, &_S58, &_S59, rowWin_1);


    thread array<half2, int(16)> dreg_1;

#line 1689
    uint n2_1 = 0U;

    for(;;)
    {

#line 1691
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1691
            break;
        }

#line 77 "twiddle.slang"
        uint _S61 = mfDataStrideFlag_0();

#line 174 "mm_1024_fusedTierB_c16.slang"
        if(_S61 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S62 = mfDataStrideFlag_0();

#line 77
            k_1 = _S62;

#line 174 "mm_1024_fusedTierB_c16.slang"
        }
        else
        {

#line 174
            k_1 = 1024U;

#line 174
        }

#line 1692
        half2 _S63 = dload_0(data_1, d_5 * k_1 + tid_3 + 64U * n2_1);

#line 1692
        dreg_1[n2_1] = _S63;

#line 1691
        n2_1 = n2_1 + 1U;

#line 1691
    }

#line 1691
    k_1 = 0U;

#line 1711
    for(;;)
    {

#line 1711
        if(k_1 < 1U)
        {
        }
        else
        {

#line 1711
            break;
        }

#line 1712
        uint _S64 = pair_1 + k_1;

#line 1712
        uint _S65 = _S60 + k_1;

#line 1712
        thread array<half2, int(16)> _S66 = dreg_1;

#line 1712
        filterOne_0(_S64, d_5, _S65, tid_3, &_S66, data_1, tmpl_1, peakIdx_1, peakVal_1, _S58, _S59, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1711
        k_1 = k_1 + 1U;

#line 1711
    }



    return;
}


#line 1728
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1728
    thread KernelContext_0 kernelContext_7;

#line 1728
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1728
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1728
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1728
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1728
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1728
    (&kernelContext_7)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1728
    threadgroup array<uint, int(1024)> stg_1;

#line 1728
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1745
    uint _pr_0 = gid_0.x;

#line 1745
    uint _t_0 = lid_0.x;
    (&kernelContext_7)->_stgBase_0 = 0U;

#line 1746
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, entryPointParams_rowWin_1, &kernelContext_7);

#line 1761
    return;
}
