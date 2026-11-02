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

#line 10 "mm_256_fusedTierB_c16t8.slang"
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


#line 202 "mm_256_fusedTierB_c16t8.slang"
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
};


#line 229
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 92 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 232 "mm_256_fusedTierB_c16t8.slang"
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


#line 171 "mm_256_fusedTierB_c16t8.slang"
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

#line 265 "mm_256_fusedTierB_c16t8.slang"
    if(_S7 != 0U)
    {

#line 73 "twiddle.slang"
        uint _S8 = mfDataScaleFlag_0();

#line 266 "mm_256_fusedTierB_c16t8.slang"
        float s_0 = (as_type<float>((_S8)));
        uint _S9 = 2U * i_1;

#line 267
        return half2(half((as_type<float>((b_1[_S9]))) * s_0), half((as_type<float>((b_1[_S9 + 1U]))) * s_0));
    }
    return cload_0(b_1, i_1);
}


#line 401
void cmulconjs_0(half2 ar_0, half2 ai_0, half2 br_0, half2 bi_0, half2 thread* pr_0, half2 thread* pi_0)
{
    *pr_0 = ar_0 * br_0 + ai_0 * bi_0;
    *pi_0 = ai_0 * br_0 - ar_0 * bi_0;
    return;
}


#line 413
void r4s_0(array<half2, int(16)> thread* re_0, array<half2, int(16)> thread* im_0, uint a_0, uint b_2, uint c_0, uint d_1)
{
    half2 t0r_0 = (*re_0)[a_0] + (*re_0)[c_0];

#line 415
    half2 t0i_0 = (*im_0)[a_0] + (*im_0)[c_0];
    half2 t1r_0 = (*re_0)[a_0] - (*re_0)[c_0];

#line 416
    half2 t1i_0 = (*im_0)[a_0] - (*im_0)[c_0];
    half2 t2r_0 = (*re_0)[b_2] + (*re_0)[d_1];

#line 417
    half2 t2i_0 = (*im_0)[b_2] + (*im_0)[d_1];
    half2 t3r_0 = (*re_0)[b_2] - (*re_0)[d_1];
    half2 j3r_0 = - ((*im_0)[b_2] - (*im_0)[d_1]);
    (*re_0)[a_0] = t0r_0 + t2r_0;

#line 420
    (*im_0)[a_0] = t0i_0 + t2i_0;
    (*re_0)[b_2] = t1r_0 + j3r_0;

#line 421
    (*im_0)[b_2] = t1i_0 + t3r_0;
    (*re_0)[c_0] = t0r_0 - t2r_0;

#line 422
    (*im_0)[c_0] = t0i_0 - t2i_0;
    (*re_0)[d_1] = t1r_0 - j3r_0;

#line 423
    (*im_0)[d_1] = t1i_0 - t3r_0;
    return;
}


#line 392
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 392
    half2 _S10 = half2(wr_0) ;

#line 392
    half2 _S11 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S11 + *xi_0 * _S10;
    *xr_0 = *xr_0 * _S10 - *xi_0 * _S11;

#line 396
    *xi_0 = ni_0;
    return;
}


#line 426
void swap2_0(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint p_1, uint q_0)
{

    half2 t_0 = (*re_1)[p_1];

#line 429
    (*re_1)[p_1] = (*re_1)[q_0];

#line 429
    (*re_1)[q_0] = t_0;
    half2 t_1 = (*im_1)[p_1];

#line 430
    (*im_1)[p_1] = (*im_1)[q_0];

#line 430
    (*im_1)[q_0] = t_1;
    return;
}


#line 464
void dft16s_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2)
{

#line 464
    uint n1_0 = 0U;

    for(;;)
    {

#line 466
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 466
            break;
        }

#line 466
        r4s_0(re_2, im_2, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 466
        n1_0 = n1_0 + 1U;

#line 466
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

#line 477
    uint k2_0 = 0U;
    for(;;)
    {

#line 478
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 478
            break;
        }

#line 479
        uint _S12 = 4U * k2_0;

#line 479
        r4s_0(re_2, im_2, _S12, _S12 + 1U, _S12 + 2U, _S12 + 3U);

#line 478
        k2_0 = k2_0 + 1U;

#line 478
    }

    swap2_0(re_2, im_2, 1U, 4U);

#line 480
    swap2_0(re_2, im_2, 2U, 8U);

#line 480
    swap2_0(re_2, im_2, 3U, 12U);
    swap2_0(re_2, im_2, 6U, 9U);

#line 481
    swap2_0(re_2, im_2, 7U, 13U);

#line 481
    swap2_0(re_2, im_2, 11U, 14U);
    return;
}


#line 464
void dft16s_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3)
{

#line 464
    uint n1_1 = 0U;

    for(;;)
    {

#line 466
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 466
            break;
        }

#line 466
        r4s_0(re_3, im_3, n1_1, n1_1 + 4U, n1_1 + 8U, n1_1 + 12U);

#line 466
        n1_1 = n1_1 + 1U;

#line 466
    }


    cmulw_0(&(*re_3)[int(5)], &(*im_3)[int(5)], 0.923828125h, 0.382568359375h);
    cmulw_0(&(*re_3)[int(9)], &(*im_3)[int(9)], 0.70703125h, 0.70703125h);
    cmulw_0(&(*re_3)[int(13)], &(*im_3)[int(13)], 0.382568359375h, 0.923828125h);
    cmulw_0(&(*re_3)[int(6)], &(*im_3)[int(6)], 0.70703125h, 0.70703125h);
    cmulw_0(&(*re_3)[int(10)], &(*im_3)[int(10)], 0.0h, 1.0h);
    cmulw_0(&(*re_3)[int(14)], &(*im_3)[int(14)], -0.70703125h, 0.70703125h);
    cmulw_0(&(*re_3)[int(7)], &(*im_3)[int(7)], 0.382568359375h, 0.923828125h);
    cmulw_0(&(*re_3)[int(11)], &(*im_3)[int(11)], -0.70703125h, 0.70703125h);
    cmulw_0(&(*re_3)[int(15)], &(*im_3)[int(15)], -0.923828125h, -0.382568359375h);

#line 477
    uint k2_1 = 0U;
    for(;;)
    {

#line 478
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 478
            break;
        }

#line 479
        uint _S13 = 4U * k2_1;

#line 479
        r4s_0(re_3, im_3, _S13, _S13 + 1U, _S13 + 2U, _S13 + 3U);

#line 478
        k2_1 = k2_1 + 1U;

#line 478
    }

    swap2_0(re_3, im_3, 1U, 4U);

#line 480
    swap2_0(re_3, im_3, 2U, 8U);

#line 480
    swap2_0(re_3, im_3, 3U, 12U);
    swap2_0(re_3, im_3, 6U, 9U);

#line 481
    swap2_0(re_3, im_3, 7U, 13U);

#line 481
    swap2_0(re_3, im_3, 11U, 14U);
    return;
}


#line 49 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S14 = ((MF_COARSE_TWT));

#line 52
    return _S14;
}


#line 76
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S15 = ((MF_ACCURATE_TRIG));

#line 79
    return _S15;
}


#line 103
float2 mfTwiddle_0(float angle_0)
{

#line 81
    uint _S16 = mfAccurateTrigFlag_0();

#line 105
    if(_S16 == 0U)
    {

#line 106
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S17 = float(quadrant_0);
    float x_0 = angle_0 - _S17 * 1.57079625129699707f - _S17 * 7.54978941586159635e-08f;
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


#line 608 "mm_256_fusedTierB_c16t8.slang"
void innermostS_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4)
{
    dft16s_1(re_4, im_4);



    return;
}


#line 884
uint lgOf_0(uint i_2)
{

#line 884
    uint _S18;

#line 884
    if(i_2 < 1U)
    {

#line 884
        _S18 = 4U;

#line 884
    }
    else
    {

#line 884
        if(i_2 == 1U)
        {

#line 884
            _S18 = 4U;

#line 884
        }
        else
        {

#line 884
            _S18 = 1U;

#line 884
        }

#line 884
    }

#line 884
    return _S18;
}


#line 886
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 890
    uint lg_1 = lgOf_0(0U);

#line 895
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 488
half2 mag2s_0(half2 re_5, half2 im_5)
{

#line 488
    return re_5 * re_5 + im_5 * im_5;
}


#line 1856
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1856
    uint _S19;

#line 1856
    uint _S20;

#line 1856
    uint _S21;

#line 1856
    uint _S22;

#line 1856
    uint _S23;

#line 1856
    thread KernelContext_0 kernelContext_1;

#line 1856
    (&kernelContext_1)->entryPointParams_0 = entryPointParams_1;

#line 1856
    (&kernelContext_1)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1856
    (&kernelContext_1)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1856
    (&kernelContext_1)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1856
    (&kernelContext_1)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1856
    (&kernelContext_1)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1856
    (&kernelContext_1)->_binPhase_0 = 0U;

#line 1874
    uint _pr_0 = gid_0.x;

#line 1874
    uint _t_0 = lid_0.x;
    (&kernelContext_1)->_stgBase_0 = 0U;

#line 1875
    uint _S24 = entryPointParams_1->ntmpl_0;

#line 1875
    uint _S25 = entryPointParams_1->winStart_0;

#line 1875
    uint _S26 = entryPointParams_1->winEnd_0;

#line 1875
    uint _S27 = entryPointParams_1->binsize_0;

#line 1875
    uint _S28 = entryPointParams_1->nbins_0;

#line 1875
    uint _S29 = entryPointParams_1->thrBits_0;

#line 1889
    for(;;)
    {

#line 1889
        thread uint _S30 = _S25;

#line 1889
        thread uint _S31 = _S26;

#line 1889
        (&kernelContext_1)->_tid_0 = _t_0;

#line 1889
        uint tiles_0 = (_S24 + 8U - 1U) / 8U;

#line 1889
        uint slots_0 = _S27 * tiles_0;

#line 1889
        bool slotOk_0 = _pr_0 < slots_0;

#line 1889
        uint q_1;

#line 1889
        if(slotOk_0)
        {

#line 1889
            q_1 = _pr_0;

#line 1889
        }
        else
        {

#line 1889
            q_1 = slots_0 - 1U;

#line 1889
        }

#line 1889
        uint d_2 = q_1 / tiles_0;

#line 1889
        uint t0_0 = (q_1 - d_2 * tiles_0) * 8U;

#line 1889
        uint _S32 = d_2 * _S24 + t0_0;

#line 1889
        rowWindow_0(d_2, &_S30, &_S31, (&kernelContext_1)->entryPointParams_rowWin_0, &kernelContext_1);

#line 1889
        thread array<half2, int(16)> dreg_0;

#line 1889
        uint n2_0 = 0U;

#line 1889
        for(;;)
        {

#line 1889
            if(n2_0 < 16U)
            {
            }
            else
            {

#line 1889
                break;
            }

#line 1889
            uint _S33 = mfDataStrideFlag_0();

#line 1889
            if(_S33 != 0U)
            {

#line 1889
                uint _S34 = mfDataStrideFlag_0();

#line 1889
                q_1 = _S34;

#line 1889
            }
            else
            {

#line 1889
                q_1 = 256U;

#line 1889
            }

#line 1889
            half2 _S35 = dload_0((&kernelContext_1)->entryPointParams_data_0, d_2 * q_1 + _t_0 + 16U * n2_0);

#line 1889
            dreg_0[n2_0] = _S35;

#line 1889
            n2_0 = n2_0 + 1U;

#line 1889
        }

#line 1889
        uint k_0 = 0U;

#line 1889
        for(;;)
        {

#line 1889
            if(k_0 < 8U)
            {
            }
            else
            {

#line 1889
                break;
            }

#line 1889
            bool okA_0;

#line 1889
            if(slotOk_0)
            {

#line 1889
                okA_0 = (t0_0 + k_0) < _S24;

#line 1889
            }
            else
            {

#line 1889
                okA_0 = false;

#line 1889
            }

#line 1889
            bool okB_0;

#line 1889
            if(slotOk_0)
            {

#line 1889
                okB_0 = (t0_0 + k_0 + 1U) < _S24;

#line 1889
            }
            else
            {

#line 1889
                okB_0 = false;

#line 1889
            }

#line 1889
            if(okA_0)
            {

#line 1889
                q_1 = _S32 + k_0;

#line 1889
            }
            else
            {

#line 1889
                q_1 = 4294967295U;

#line 1889
            }

#line 1889
            if(okB_0)
            {

#line 1889
                n2_0 = _S32 + k_0 + 1U;

#line 1889
            }
            else
            {

#line 1889
                n2_0 = 4294967295U;

#line 1889
            }

#line 1889
            uint _S36 = t0_0 + k_0;

#line 1889
            uint _S37 = _S24 - 1U;

#line 1889
            uint _S38 = min(_S36, _S37);

#line 1889
            uint _S39 = min(_S36 + 1U, _S37);

#line 1889
            array<half2, int(16)> _S40 = dreg_0;

#line 1889
            uint _S41 = _S30;

#line 1889
            uint _S42 = _S31;

#line 1889
            for(;;)
            {

#line 1889
                thread array<half2, int(16)> re_6;

#line 1889
                thread array<half2, int(16)> im_6;

#line 1889
                uint n2_1 = 0U;

#line 1889
                for(;;)
                {

#line 1889
                    if(n2_1 < 16U)
                    {
                    }
                    else
                    {

#line 1889
                        break;
                    }

#line 1889
                    uint _S43 = 16U * n2_1;

#line 1889
                    half2 ta_0 = cload_0((&kernelContext_1)->entryPointParams_tmpl_0, _S38 * 256U + _t_0 + _S43);

#line 1889
                    half2 tb_0 = cload_0((&kernelContext_1)->entryPointParams_tmpl_0, _S39 * 256U + _t_0 + _S43);

#line 1889
                    half _S44 = _S40[n2_1].x;

#line 1889
                    half _S45 = _S40[n2_1].y;

#line 1889
                    cmulconjs_0(half2(_S44, _S44), half2(_S45, _S45), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_6[n2_1], &im_6[n2_1]);

#line 1889
                    n2_1 = n2_1 + 1U;

#line 1889
                }

#line 1889
                array<half2, int(16)> _S46 = re_6;

#line 1889
                array<half2, int(16)> _S47 = im_6;

#line 1889
                for(;;)
                {

#line 1889
                    thread array<half2, int(16)> _S48 = _S46;

#line 1889
                    thread array<half2, int(16)> _S49 = _S47;

#line 1889
                    (&kernelContext_1)->_tid_0 = _t_0;

#line 1889
                    for(;;)
                    {

#line 1889
                        uint lgTB_0 = firstbithigh_0(16U);

#line 1889
                        uint lane_0 = _t_0 & 15U;

#line 1889
                        dft16s_0(&_S48, &_S49);

#line 1889
                        uint _S50 = mfCoarseTwtFlag_0();

#line 1889
                        uint i_3;

#line 1889
                        if(_S50 != 0U)
                        {

#line 1889
                            i_3 = 0U;

#line 1889
                            for(;;)
                            {

#line 1889
                                if(i_3 < 16U)
                                {
                                }
                                else
                                {

#line 1889
                                    break;
                                }

#line 1889
                                uint _S51 = lane_0 * 16U + i_3;

#line 1889
                                cmulw_0(&_S48[i_3], &_S49[i_3], as_type<half>(ushort((COARSE_TWT_DATA_0[_S51]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S51]) >> 16U) & 65535U)));

#line 1889
                                i_3 = i_3 + 1U;

#line 1889
                            }

#line 1889
                        }
                        else
                        {

#line 1889
                            float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_0) / 256.0f);

#line 1889
                            float _S52 = tw_0.x;

#line 1889
                            float _S53 = tw_0.y;

#line 1889
                            i_3 = 0U;

#line 1889
                            float cr_0 = 1.0f;

#line 1889
                            float ci_0 = 0.0f;

#line 1889
                            for(;;)
                            {

#line 1889
                                if(i_3 < 16U)
                                {
                                }
                                else
                                {

#line 1889
                                    break;
                                }

#line 1889
                                cmulw_0(&_S48[i_3], &_S49[i_3], half(cr_0), half(ci_0));

#line 1889
                                float nr_0 = cr_0 * _S52 - ci_0 * _S53;

#line 1889
                                float _S54 = cr_0 * _S53 + ci_0 * _S52;

#line 1889
                                i_3 = i_3 + 1U;

#line 1889
                                cr_0 = nr_0;

#line 1889
                                ci_0 = _S54;

#line 1889
                            }

#line 1889
                        }

#line 1889
                        uint per_0 = 16U / max(16U, 1U);

#line 1889
                        uint _S55 = max(1U, 1U);

#line 1889
                        uint blk2_0 = _t_0 / _S55;

#line 1889
                        uint lane2_0 = _t_0 % _S55;

#line 1889
                        for(;;)
                        {

#line 1889
                            uint _S56 = (&kernelContext_1)->_tid_0;

#line 1889
                            for(;;)
                            {

#line 1889
                                thread array<uint, int(16)> t_2;

#line 1889
                                i_3 = 0U;

#line 1889
                                for(;;)
                                {

#line 1889
                                    if(i_3 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1889
                                        break;
                                    }

#line 1889
                                    t_2[i_3] = (uint(as_type<ushort>(_S48[i_3][0U])) & 65535U) | (uint(as_type<ushort>(_S48[i_3][1U])) << 16U);

#line 1889
                                    i_3 = i_3 + 1U;

#line 1889
                                }

#line 1889
                                uint shift_0 = lgTB_0 - 4U;

#line 1889
                                _S19 = shift_0;

#line 1889
                                uint _S57 = (_S56 >> shift_0) & 15U;

#line 1889
                                bool _S58 = (_S57 & 1U) != 0U;

#line 1889
                                uint _S59;

#line 1889
                                if(_S58)
                                {

#line 1889
                                    _S59 = t_2[0U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S59 = t_2[1U];

#line 1889
                                }

#line 1889
                                uint _S60 = 1U << shift_0;

#line 1889
                                _S20 = _S60;

#line 1889
                                uint partner_0 = (simd_shuffle_xor((_S59), ushort((_S60))));

#line 1889
                                if(_S58)
                                {

#line 1889
                                    t_2[0U] = partner_0;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[1U] = partner_0;

#line 1889
                                }

#line 1889
                                uint _S61;

#line 1889
                                if(_S58)
                                {

#line 1889
                                    _S61 = t_2[2U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S61 = t_2[3U];

#line 1889
                                }

#line 1889
                                uint partner_1 = (simd_shuffle_xor((_S61), ushort((_S60))));

#line 1889
                                if(_S58)
                                {

#line 1889
                                    t_2[2U] = partner_1;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[3U] = partner_1;

#line 1889
                                }

#line 1889
                                uint _S62;

#line 1889
                                if(_S58)
                                {

#line 1889
                                    _S62 = t_2[4U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S62 = t_2[5U];

#line 1889
                                }

#line 1889
                                uint partner_2 = (simd_shuffle_xor((_S62), ushort((_S60))));

#line 1889
                                if(_S58)
                                {

#line 1889
                                    t_2[4U] = partner_2;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[5U] = partner_2;

#line 1889
                                }

#line 1889
                                uint _S63;

#line 1889
                                if(_S58)
                                {

#line 1889
                                    _S63 = t_2[6U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S63 = t_2[7U];

#line 1889
                                }

#line 1889
                                uint partner_3 = (simd_shuffle_xor((_S63), ushort((_S60))));

#line 1889
                                if(_S58)
                                {

#line 1889
                                    t_2[6U] = partner_3;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[7U] = partner_3;

#line 1889
                                }

#line 1889
                                uint _S64;

#line 1889
                                if(_S58)
                                {

#line 1889
                                    _S64 = t_2[8U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S64 = t_2[9U];

#line 1889
                                }

#line 1889
                                uint partner_4 = (simd_shuffle_xor((_S64), ushort((_S60))));

#line 1889
                                if(_S58)
                                {

#line 1889
                                    t_2[8U] = partner_4;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[9U] = partner_4;

#line 1889
                                }

#line 1889
                                uint _S65;

#line 1889
                                if(_S58)
                                {

#line 1889
                                    _S65 = t_2[10U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S65 = t_2[11U];

#line 1889
                                }

#line 1889
                                uint partner_5 = (simd_shuffle_xor((_S65), ushort((_S60))));

#line 1889
                                if(_S58)
                                {

#line 1889
                                    t_2[10U] = partner_5;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[11U] = partner_5;

#line 1889
                                }

#line 1889
                                uint _S66;

#line 1889
                                if(_S58)
                                {

#line 1889
                                    _S66 = t_2[12U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S66 = t_2[13U];

#line 1889
                                }

#line 1889
                                uint partner_6 = (simd_shuffle_xor((_S66), ushort((_S60))));

#line 1889
                                if(_S58)
                                {

#line 1889
                                    t_2[12U] = partner_6;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[13U] = partner_6;

#line 1889
                                }

#line 1889
                                uint _S67;

#line 1889
                                if(_S58)
                                {

#line 1889
                                    _S67 = t_2[14U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S67 = t_2[15U];

#line 1889
                                }

#line 1889
                                uint partner_7 = (simd_shuffle_xor((_S67), ushort((_S60))));

#line 1889
                                if(_S58)
                                {

#line 1889
                                    t_2[14U] = partner_7;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[15U] = partner_7;

#line 1889
                                }

#line 1889
                                bool _S68 = (_S57 & 2U) != 0U;

#line 1889
                                uint _S69;

#line 1889
                                if(_S68)
                                {

#line 1889
                                    _S69 = t_2[0U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S69 = t_2[2U];

#line 1889
                                }

#line 1889
                                uint _S70 = 2U << shift_0;

#line 1889
                                _S21 = _S70;

#line 1889
                                uint partner_8 = (simd_shuffle_xor((_S69), ushort((_S70))));

#line 1889
                                if(_S68)
                                {

#line 1889
                                    t_2[0U] = partner_8;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[2U] = partner_8;

#line 1889
                                }

#line 1889
                                uint _S71;

#line 1889
                                if(_S68)
                                {

#line 1889
                                    _S71 = t_2[1U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S71 = t_2[3U];

#line 1889
                                }

#line 1889
                                uint partner_9 = (simd_shuffle_xor((_S71), ushort((_S70))));

#line 1889
                                if(_S68)
                                {

#line 1889
                                    t_2[1U] = partner_9;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[3U] = partner_9;

#line 1889
                                }

#line 1889
                                uint _S72;

#line 1889
                                if(_S68)
                                {

#line 1889
                                    _S72 = t_2[4U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S72 = t_2[6U];

#line 1889
                                }

#line 1889
                                uint partner_10 = (simd_shuffle_xor((_S72), ushort((_S70))));

#line 1889
                                if(_S68)
                                {

#line 1889
                                    t_2[4U] = partner_10;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[6U] = partner_10;

#line 1889
                                }

#line 1889
                                uint _S73;

#line 1889
                                if(_S68)
                                {

#line 1889
                                    _S73 = t_2[5U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S73 = t_2[7U];

#line 1889
                                }

#line 1889
                                uint partner_11 = (simd_shuffle_xor((_S73), ushort((_S70))));

#line 1889
                                if(_S68)
                                {

#line 1889
                                    t_2[5U] = partner_11;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[7U] = partner_11;

#line 1889
                                }

#line 1889
                                uint _S74;

#line 1889
                                if(_S68)
                                {

#line 1889
                                    _S74 = t_2[8U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S74 = t_2[10U];

#line 1889
                                }

#line 1889
                                uint partner_12 = (simd_shuffle_xor((_S74), ushort((_S70))));

#line 1889
                                if(_S68)
                                {

#line 1889
                                    t_2[8U] = partner_12;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[10U] = partner_12;

#line 1889
                                }

#line 1889
                                uint _S75;

#line 1889
                                if(_S68)
                                {

#line 1889
                                    _S75 = t_2[9U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S75 = t_2[11U];

#line 1889
                                }

#line 1889
                                uint partner_13 = (simd_shuffle_xor((_S75), ushort((_S70))));

#line 1889
                                if(_S68)
                                {

#line 1889
                                    t_2[9U] = partner_13;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[11U] = partner_13;

#line 1889
                                }

#line 1889
                                uint _S76;

#line 1889
                                if(_S68)
                                {

#line 1889
                                    _S76 = t_2[12U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S76 = t_2[14U];

#line 1889
                                }

#line 1889
                                uint partner_14 = (simd_shuffle_xor((_S76), ushort((_S70))));

#line 1889
                                if(_S68)
                                {

#line 1889
                                    t_2[12U] = partner_14;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[14U] = partner_14;

#line 1889
                                }

#line 1889
                                uint _S77;

#line 1889
                                if(_S68)
                                {

#line 1889
                                    _S77 = t_2[13U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S77 = t_2[15U];

#line 1889
                                }

#line 1889
                                uint partner_15 = (simd_shuffle_xor((_S77), ushort((_S70))));

#line 1889
                                if(_S68)
                                {

#line 1889
                                    t_2[13U] = partner_15;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[15U] = partner_15;

#line 1889
                                }

#line 1889
                                bool _S78 = (_S57 & 4U) != 0U;

#line 1889
                                uint _S79;

#line 1889
                                if(_S78)
                                {

#line 1889
                                    _S79 = t_2[0U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S79 = t_2[4U];

#line 1889
                                }

#line 1889
                                uint _S80 = 4U << shift_0;

#line 1889
                                _S22 = _S80;

#line 1889
                                uint partner_16 = (simd_shuffle_xor((_S79), ushort((_S80))));

#line 1889
                                if(_S78)
                                {

#line 1889
                                    t_2[0U] = partner_16;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[4U] = partner_16;

#line 1889
                                }

#line 1889
                                uint _S81;

#line 1889
                                if(_S78)
                                {

#line 1889
                                    _S81 = t_2[1U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S81 = t_2[5U];

#line 1889
                                }

#line 1889
                                uint partner_17 = (simd_shuffle_xor((_S81), ushort((_S80))));

#line 1889
                                if(_S78)
                                {

#line 1889
                                    t_2[1U] = partner_17;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[5U] = partner_17;

#line 1889
                                }

#line 1889
                                uint _S82;

#line 1889
                                if(_S78)
                                {

#line 1889
                                    _S82 = t_2[2U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S82 = t_2[6U];

#line 1889
                                }

#line 1889
                                uint partner_18 = (simd_shuffle_xor((_S82), ushort((_S80))));

#line 1889
                                if(_S78)
                                {

#line 1889
                                    t_2[2U] = partner_18;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[6U] = partner_18;

#line 1889
                                }

#line 1889
                                uint _S83;

#line 1889
                                if(_S78)
                                {

#line 1889
                                    _S83 = t_2[3U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S83 = t_2[7U];

#line 1889
                                }

#line 1889
                                uint partner_19 = (simd_shuffle_xor((_S83), ushort((_S80))));

#line 1889
                                if(_S78)
                                {

#line 1889
                                    t_2[3U] = partner_19;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[7U] = partner_19;

#line 1889
                                }

#line 1889
                                uint _S84;

#line 1889
                                if(_S78)
                                {

#line 1889
                                    _S84 = t_2[8U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S84 = t_2[12U];

#line 1889
                                }

#line 1889
                                uint partner_20 = (simd_shuffle_xor((_S84), ushort((_S80))));

#line 1889
                                if(_S78)
                                {

#line 1889
                                    t_2[8U] = partner_20;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[12U] = partner_20;

#line 1889
                                }

#line 1889
                                uint _S85;

#line 1889
                                if(_S78)
                                {

#line 1889
                                    _S85 = t_2[9U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S85 = t_2[13U];

#line 1889
                                }

#line 1889
                                uint partner_21 = (simd_shuffle_xor((_S85), ushort((_S80))));

#line 1889
                                if(_S78)
                                {

#line 1889
                                    t_2[9U] = partner_21;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[13U] = partner_21;

#line 1889
                                }

#line 1889
                                uint _S86;

#line 1889
                                if(_S78)
                                {

#line 1889
                                    _S86 = t_2[10U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S86 = t_2[14U];

#line 1889
                                }

#line 1889
                                uint partner_22 = (simd_shuffle_xor((_S86), ushort((_S80))));

#line 1889
                                if(_S78)
                                {

#line 1889
                                    t_2[10U] = partner_22;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[14U] = partner_22;

#line 1889
                                }

#line 1889
                                uint _S87;

#line 1889
                                if(_S78)
                                {

#line 1889
                                    _S87 = t_2[11U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S87 = t_2[15U];

#line 1889
                                }

#line 1889
                                uint partner_23 = (simd_shuffle_xor((_S87), ushort((_S80))));

#line 1889
                                if(_S78)
                                {

#line 1889
                                    t_2[11U] = partner_23;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[15U] = partner_23;

#line 1889
                                }

#line 1889
                                bool _S88 = (_S57 & 8U) != 0U;

#line 1889
                                uint _S89;

#line 1889
                                if(_S88)
                                {

#line 1889
                                    _S89 = t_2[0U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S89 = t_2[8U];

#line 1889
                                }

#line 1889
                                uint _S90 = 8U << shift_0;

#line 1889
                                _S23 = _S90;

#line 1889
                                uint partner_24 = (simd_shuffle_xor((_S89), ushort((_S90))));

#line 1889
                                if(_S88)
                                {

#line 1889
                                    t_2[0U] = partner_24;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[8U] = partner_24;

#line 1889
                                }

#line 1889
                                uint _S91;

#line 1889
                                if(_S88)
                                {

#line 1889
                                    _S91 = t_2[1U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S91 = t_2[9U];

#line 1889
                                }

#line 1889
                                uint partner_25 = (simd_shuffle_xor((_S91), ushort((_S90))));

#line 1889
                                if(_S88)
                                {

#line 1889
                                    t_2[1U] = partner_25;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[9U] = partner_25;

#line 1889
                                }

#line 1889
                                uint _S92;

#line 1889
                                if(_S88)
                                {

#line 1889
                                    _S92 = t_2[2U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S92 = t_2[10U];

#line 1889
                                }

#line 1889
                                uint partner_26 = (simd_shuffle_xor((_S92), ushort((_S90))));

#line 1889
                                if(_S88)
                                {

#line 1889
                                    t_2[2U] = partner_26;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[10U] = partner_26;

#line 1889
                                }

#line 1889
                                uint _S93;

#line 1889
                                if(_S88)
                                {

#line 1889
                                    _S93 = t_2[3U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S93 = t_2[11U];

#line 1889
                                }

#line 1889
                                uint partner_27 = (simd_shuffle_xor((_S93), ushort((_S90))));

#line 1889
                                if(_S88)
                                {

#line 1889
                                    t_2[3U] = partner_27;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[11U] = partner_27;

#line 1889
                                }

#line 1889
                                uint _S94;

#line 1889
                                if(_S88)
                                {

#line 1889
                                    _S94 = t_2[4U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S94 = t_2[12U];

#line 1889
                                }

#line 1889
                                uint partner_28 = (simd_shuffle_xor((_S94), ushort((_S90))));

#line 1889
                                if(_S88)
                                {

#line 1889
                                    t_2[4U] = partner_28;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[12U] = partner_28;

#line 1889
                                }

#line 1889
                                uint _S95;

#line 1889
                                if(_S88)
                                {

#line 1889
                                    _S95 = t_2[5U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S95 = t_2[13U];

#line 1889
                                }

#line 1889
                                uint partner_29 = (simd_shuffle_xor((_S95), ushort((_S90))));

#line 1889
                                if(_S88)
                                {

#line 1889
                                    t_2[5U] = partner_29;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[13U] = partner_29;

#line 1889
                                }

#line 1889
                                uint _S96;

#line 1889
                                if(_S88)
                                {

#line 1889
                                    _S96 = t_2[6U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S96 = t_2[14U];

#line 1889
                                }

#line 1889
                                uint partner_30 = (simd_shuffle_xor((_S96), ushort((_S90))));

#line 1889
                                if(_S88)
                                {

#line 1889
                                    t_2[6U] = partner_30;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[14U] = partner_30;

#line 1889
                                }

#line 1889
                                uint _S97;

#line 1889
                                if(_S88)
                                {

#line 1889
                                    _S97 = t_2[7U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S97 = t_2[15U];

#line 1889
                                }

#line 1889
                                uint partner_31 = (simd_shuffle_xor((_S97), ushort((_S90))));

#line 1889
                                if(_S88)
                                {

#line 1889
                                    t_2[7U] = partner_31;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_2[15U] = partner_31;

#line 1889
                                }

#line 1889
                                uint i_4 = 0U;

#line 1889
                                for(;;)
                                {

#line 1889
                                    if(i_4 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1889
                                        break;
                                    }

#line 1889
                                    _S48[i_4] = half2(as_type<half>(ushort((t_2[i_4]) & 65535U)), as_type<half>(ushort(((t_2[i_4]) >> 16U) & 65535U)));

#line 1889
                                    i_4 = i_4 + 1U;

#line 1889
                                }

#line 1889
                                break;
                            }

#line 1889
                            uint _S98 = (&kernelContext_1)->_tid_0;

#line 1889
                            for(;;)
                            {

#line 1889
                                thread array<uint, int(16)> t_3;

#line 1889
                                uint i_5 = 0U;

#line 1889
                                for(;;)
                                {

#line 1889
                                    if(i_5 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1889
                                        break;
                                    }

#line 1889
                                    t_3[i_5] = (uint(as_type<ushort>(_S49[i_5][0U])) & 65535U) | (uint(as_type<ushort>(_S49[i_5][1U])) << 16U);

#line 1889
                                    i_5 = i_5 + 1U;

#line 1889
                                }

#line 1889
                                uint _S99 = (_S98 >> _S19) & 15U;

#line 1889
                                bool _S100 = (_S99 & 1U) != 0U;

#line 1889
                                uint _S101;

#line 1889
                                if(_S100)
                                {

#line 1889
                                    _S101 = t_3[0U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S101 = t_3[1U];

#line 1889
                                }

#line 1889
                                uint partner_32 = (simd_shuffle_xor((_S101), ushort((_S20))));

#line 1889
                                if(_S100)
                                {

#line 1889
                                    t_3[0U] = partner_32;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[1U] = partner_32;

#line 1889
                                }

#line 1889
                                uint _S102;

#line 1889
                                if(_S100)
                                {

#line 1889
                                    _S102 = t_3[2U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S102 = t_3[3U];

#line 1889
                                }

#line 1889
                                uint partner_33 = (simd_shuffle_xor((_S102), ushort((_S20))));

#line 1889
                                if(_S100)
                                {

#line 1889
                                    t_3[2U] = partner_33;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[3U] = partner_33;

#line 1889
                                }

#line 1889
                                uint _S103;

#line 1889
                                if(_S100)
                                {

#line 1889
                                    _S103 = t_3[4U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S103 = t_3[5U];

#line 1889
                                }

#line 1889
                                uint partner_34 = (simd_shuffle_xor((_S103), ushort((_S20))));

#line 1889
                                if(_S100)
                                {

#line 1889
                                    t_3[4U] = partner_34;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[5U] = partner_34;

#line 1889
                                }

#line 1889
                                uint _S104;

#line 1889
                                if(_S100)
                                {

#line 1889
                                    _S104 = t_3[6U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S104 = t_3[7U];

#line 1889
                                }

#line 1889
                                uint partner_35 = (simd_shuffle_xor((_S104), ushort((_S20))));

#line 1889
                                if(_S100)
                                {

#line 1889
                                    t_3[6U] = partner_35;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[7U] = partner_35;

#line 1889
                                }

#line 1889
                                uint _S105;

#line 1889
                                if(_S100)
                                {

#line 1889
                                    _S105 = t_3[8U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S105 = t_3[9U];

#line 1889
                                }

#line 1889
                                uint partner_36 = (simd_shuffle_xor((_S105), ushort((_S20))));

#line 1889
                                if(_S100)
                                {

#line 1889
                                    t_3[8U] = partner_36;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[9U] = partner_36;

#line 1889
                                }

#line 1889
                                uint _S106;

#line 1889
                                if(_S100)
                                {

#line 1889
                                    _S106 = t_3[10U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S106 = t_3[11U];

#line 1889
                                }

#line 1889
                                uint partner_37 = (simd_shuffle_xor((_S106), ushort((_S20))));

#line 1889
                                if(_S100)
                                {

#line 1889
                                    t_3[10U] = partner_37;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[11U] = partner_37;

#line 1889
                                }

#line 1889
                                uint _S107;

#line 1889
                                if(_S100)
                                {

#line 1889
                                    _S107 = t_3[12U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S107 = t_3[13U];

#line 1889
                                }

#line 1889
                                uint partner_38 = (simd_shuffle_xor((_S107), ushort((_S20))));

#line 1889
                                if(_S100)
                                {

#line 1889
                                    t_3[12U] = partner_38;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[13U] = partner_38;

#line 1889
                                }

#line 1889
                                uint _S108;

#line 1889
                                if(_S100)
                                {

#line 1889
                                    _S108 = t_3[14U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S108 = t_3[15U];

#line 1889
                                }

#line 1889
                                uint partner_39 = (simd_shuffle_xor((_S108), ushort((_S20))));

#line 1889
                                if(_S100)
                                {

#line 1889
                                    t_3[14U] = partner_39;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[15U] = partner_39;

#line 1889
                                }

#line 1889
                                bool _S109 = (_S99 & 2U) != 0U;

#line 1889
                                uint _S110;

#line 1889
                                if(_S109)
                                {

#line 1889
                                    _S110 = t_3[0U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S110 = t_3[2U];

#line 1889
                                }

#line 1889
                                uint partner_40 = (simd_shuffle_xor((_S110), ushort((_S21))));

#line 1889
                                if(_S109)
                                {

#line 1889
                                    t_3[0U] = partner_40;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[2U] = partner_40;

#line 1889
                                }

#line 1889
                                uint _S111;

#line 1889
                                if(_S109)
                                {

#line 1889
                                    _S111 = t_3[1U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S111 = t_3[3U];

#line 1889
                                }

#line 1889
                                uint partner_41 = (simd_shuffle_xor((_S111), ushort((_S21))));

#line 1889
                                if(_S109)
                                {

#line 1889
                                    t_3[1U] = partner_41;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[3U] = partner_41;

#line 1889
                                }

#line 1889
                                uint _S112;

#line 1889
                                if(_S109)
                                {

#line 1889
                                    _S112 = t_3[4U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S112 = t_3[6U];

#line 1889
                                }

#line 1889
                                uint partner_42 = (simd_shuffle_xor((_S112), ushort((_S21))));

#line 1889
                                if(_S109)
                                {

#line 1889
                                    t_3[4U] = partner_42;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[6U] = partner_42;

#line 1889
                                }

#line 1889
                                uint _S113;

#line 1889
                                if(_S109)
                                {

#line 1889
                                    _S113 = t_3[5U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S113 = t_3[7U];

#line 1889
                                }

#line 1889
                                uint partner_43 = (simd_shuffle_xor((_S113), ushort((_S21))));

#line 1889
                                if(_S109)
                                {

#line 1889
                                    t_3[5U] = partner_43;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[7U] = partner_43;

#line 1889
                                }

#line 1889
                                uint _S114;

#line 1889
                                if(_S109)
                                {

#line 1889
                                    _S114 = t_3[8U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S114 = t_3[10U];

#line 1889
                                }

#line 1889
                                uint partner_44 = (simd_shuffle_xor((_S114), ushort((_S21))));

#line 1889
                                if(_S109)
                                {

#line 1889
                                    t_3[8U] = partner_44;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[10U] = partner_44;

#line 1889
                                }

#line 1889
                                uint _S115;

#line 1889
                                if(_S109)
                                {

#line 1889
                                    _S115 = t_3[9U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S115 = t_3[11U];

#line 1889
                                }

#line 1889
                                uint partner_45 = (simd_shuffle_xor((_S115), ushort((_S21))));

#line 1889
                                if(_S109)
                                {

#line 1889
                                    t_3[9U] = partner_45;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[11U] = partner_45;

#line 1889
                                }

#line 1889
                                uint _S116;

#line 1889
                                if(_S109)
                                {

#line 1889
                                    _S116 = t_3[12U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S116 = t_3[14U];

#line 1889
                                }

#line 1889
                                uint partner_46 = (simd_shuffle_xor((_S116), ushort((_S21))));

#line 1889
                                if(_S109)
                                {

#line 1889
                                    t_3[12U] = partner_46;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[14U] = partner_46;

#line 1889
                                }

#line 1889
                                uint _S117;

#line 1889
                                if(_S109)
                                {

#line 1889
                                    _S117 = t_3[13U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S117 = t_3[15U];

#line 1889
                                }

#line 1889
                                uint partner_47 = (simd_shuffle_xor((_S117), ushort((_S21))));

#line 1889
                                if(_S109)
                                {

#line 1889
                                    t_3[13U] = partner_47;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[15U] = partner_47;

#line 1889
                                }

#line 1889
                                bool _S118 = (_S99 & 4U) != 0U;

#line 1889
                                uint _S119;

#line 1889
                                if(_S118)
                                {

#line 1889
                                    _S119 = t_3[0U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S119 = t_3[4U];

#line 1889
                                }

#line 1889
                                uint partner_48 = (simd_shuffle_xor((_S119), ushort((_S22))));

#line 1889
                                if(_S118)
                                {

#line 1889
                                    t_3[0U] = partner_48;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[4U] = partner_48;

#line 1889
                                }

#line 1889
                                uint _S120;

#line 1889
                                if(_S118)
                                {

#line 1889
                                    _S120 = t_3[1U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S120 = t_3[5U];

#line 1889
                                }

#line 1889
                                uint partner_49 = (simd_shuffle_xor((_S120), ushort((_S22))));

#line 1889
                                if(_S118)
                                {

#line 1889
                                    t_3[1U] = partner_49;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[5U] = partner_49;

#line 1889
                                }

#line 1889
                                uint _S121;

#line 1889
                                if(_S118)
                                {

#line 1889
                                    _S121 = t_3[2U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S121 = t_3[6U];

#line 1889
                                }

#line 1889
                                uint partner_50 = (simd_shuffle_xor((_S121), ushort((_S22))));

#line 1889
                                if(_S118)
                                {

#line 1889
                                    t_3[2U] = partner_50;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[6U] = partner_50;

#line 1889
                                }

#line 1889
                                uint _S122;

#line 1889
                                if(_S118)
                                {

#line 1889
                                    _S122 = t_3[3U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S122 = t_3[7U];

#line 1889
                                }

#line 1889
                                uint partner_51 = (simd_shuffle_xor((_S122), ushort((_S22))));

#line 1889
                                if(_S118)
                                {

#line 1889
                                    t_3[3U] = partner_51;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[7U] = partner_51;

#line 1889
                                }

#line 1889
                                uint _S123;

#line 1889
                                if(_S118)
                                {

#line 1889
                                    _S123 = t_3[8U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S123 = t_3[12U];

#line 1889
                                }

#line 1889
                                uint partner_52 = (simd_shuffle_xor((_S123), ushort((_S22))));

#line 1889
                                if(_S118)
                                {

#line 1889
                                    t_3[8U] = partner_52;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[12U] = partner_52;

#line 1889
                                }

#line 1889
                                uint _S124;

#line 1889
                                if(_S118)
                                {

#line 1889
                                    _S124 = t_3[9U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S124 = t_3[13U];

#line 1889
                                }

#line 1889
                                uint partner_53 = (simd_shuffle_xor((_S124), ushort((_S22))));

#line 1889
                                if(_S118)
                                {

#line 1889
                                    t_3[9U] = partner_53;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[13U] = partner_53;

#line 1889
                                }

#line 1889
                                uint _S125;

#line 1889
                                if(_S118)
                                {

#line 1889
                                    _S125 = t_3[10U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S125 = t_3[14U];

#line 1889
                                }

#line 1889
                                uint partner_54 = (simd_shuffle_xor((_S125), ushort((_S22))));

#line 1889
                                if(_S118)
                                {

#line 1889
                                    t_3[10U] = partner_54;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[14U] = partner_54;

#line 1889
                                }

#line 1889
                                uint _S126;

#line 1889
                                if(_S118)
                                {

#line 1889
                                    _S126 = t_3[11U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S126 = t_3[15U];

#line 1889
                                }

#line 1889
                                uint partner_55 = (simd_shuffle_xor((_S126), ushort((_S22))));

#line 1889
                                if(_S118)
                                {

#line 1889
                                    t_3[11U] = partner_55;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[15U] = partner_55;

#line 1889
                                }

#line 1889
                                bool _S127 = (_S99 & 8U) != 0U;

#line 1889
                                uint _S128;

#line 1889
                                if(_S127)
                                {

#line 1889
                                    _S128 = t_3[0U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S128 = t_3[8U];

#line 1889
                                }

#line 1889
                                uint partner_56 = (simd_shuffle_xor((_S128), ushort((_S23))));

#line 1889
                                if(_S127)
                                {

#line 1889
                                    t_3[0U] = partner_56;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[8U] = partner_56;

#line 1889
                                }

#line 1889
                                uint _S129;

#line 1889
                                if(_S127)
                                {

#line 1889
                                    _S129 = t_3[1U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S129 = t_3[9U];

#line 1889
                                }

#line 1889
                                uint partner_57 = (simd_shuffle_xor((_S129), ushort((_S23))));

#line 1889
                                if(_S127)
                                {

#line 1889
                                    t_3[1U] = partner_57;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[9U] = partner_57;

#line 1889
                                }

#line 1889
                                uint _S130;

#line 1889
                                if(_S127)
                                {

#line 1889
                                    _S130 = t_3[2U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S130 = t_3[10U];

#line 1889
                                }

#line 1889
                                uint partner_58 = (simd_shuffle_xor((_S130), ushort((_S23))));

#line 1889
                                if(_S127)
                                {

#line 1889
                                    t_3[2U] = partner_58;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[10U] = partner_58;

#line 1889
                                }

#line 1889
                                uint _S131;

#line 1889
                                if(_S127)
                                {

#line 1889
                                    _S131 = t_3[3U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S131 = t_3[11U];

#line 1889
                                }

#line 1889
                                uint partner_59 = (simd_shuffle_xor((_S131), ushort((_S23))));

#line 1889
                                if(_S127)
                                {

#line 1889
                                    t_3[3U] = partner_59;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[11U] = partner_59;

#line 1889
                                }

#line 1889
                                uint _S132;

#line 1889
                                if(_S127)
                                {

#line 1889
                                    _S132 = t_3[4U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S132 = t_3[12U];

#line 1889
                                }

#line 1889
                                uint partner_60 = (simd_shuffle_xor((_S132), ushort((_S23))));

#line 1889
                                if(_S127)
                                {

#line 1889
                                    t_3[4U] = partner_60;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[12U] = partner_60;

#line 1889
                                }

#line 1889
                                uint _S133;

#line 1889
                                if(_S127)
                                {

#line 1889
                                    _S133 = t_3[5U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S133 = t_3[13U];

#line 1889
                                }

#line 1889
                                uint partner_61 = (simd_shuffle_xor((_S133), ushort((_S23))));

#line 1889
                                if(_S127)
                                {

#line 1889
                                    t_3[5U] = partner_61;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[13U] = partner_61;

#line 1889
                                }

#line 1889
                                uint _S134;

#line 1889
                                if(_S127)
                                {

#line 1889
                                    _S134 = t_3[6U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S134 = t_3[14U];

#line 1889
                                }

#line 1889
                                uint partner_62 = (simd_shuffle_xor((_S134), ushort((_S23))));

#line 1889
                                if(_S127)
                                {

#line 1889
                                    t_3[6U] = partner_62;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[14U] = partner_62;

#line 1889
                                }

#line 1889
                                uint _S135;

#line 1889
                                if(_S127)
                                {

#line 1889
                                    _S135 = t_3[7U];

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S135 = t_3[15U];

#line 1889
                                }

#line 1889
                                uint partner_63 = (simd_shuffle_xor((_S135), ushort((_S23))));

#line 1889
                                if(_S127)
                                {

#line 1889
                                    t_3[7U] = partner_63;

#line 1889
                                }
                                else
                                {

#line 1889
                                    t_3[15U] = partner_63;

#line 1889
                                }

#line 1889
                                uint i_6 = 0U;

#line 1889
                                for(;;)
                                {

#line 1889
                                    if(i_6 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1889
                                        break;
                                    }

#line 1889
                                    _S49[i_6] = half2(as_type<half>(ushort((t_3[i_6]) & 65535U)), as_type<half>(ushort(((t_3[i_6]) >> 16U) & 65535U)));

#line 1889
                                    i_6 = i_6 + 1U;

#line 1889
                                }

#line 1889
                                break;
                            }

#line 1889
                            break;
                        }

#line 1889
                        break;
                    }

#line 1889
                    innermostS_0(&_S48, &_S49);

#line 1889
                    uint spanA_0;

#line 1889
                    uint spanB_0;

#line 1889
                    uint i_7;

#line 1889
                    uint ovAcc_0;

#line 1889
                    uint ovAcc_1;

#line 1889
                    uint ovAcc_2;

#line 1889
                    uint bb_0;

#line 1889
                    uint bb_1;

#line 1889
                    bool infLocalA_0;

#line 1889
                    bool infLocalB_0;

#line 1889
                    bool hitLocalA_0;

#line 1889
                    bool hitLocalB_0;

#line 1889
                    bool hitA_0;

#line 1889
                    bool hitB_0;

#line 1889
                    half2 best_0;

#line 1889
                    float2 _S136;

#line 1889
                    if(_S29 != 0U)
                    {

#line 1889
                        float _S137 = (as_type<float>((_S29)));

#line 1889
                        for(;;)
                        {

#line 1889
                            uint _S138 = slotToIndex_0(_t_0 * 16U) - _S41;

#line 1889
                            bool _S139 = _S42 > _S41;

#line 1889
                            if(_S139)
                            {

#line 1889
                                spanA_0 = _S42 - _S41;

#line 1889
                            }
                            else
                            {

#line 1889
                                spanA_0 = 0U;

#line 1889
                            }

#line 1889
                            if(_S139)
                            {

#line 1889
                                spanB_0 = _S42 - _S41;

#line 1889
                            }
                            else
                            {

#line 1889
                                spanB_0 = 0U;

#line 1889
                            }

#line 1889
                            half2 _S140 = half2(float2(0.0f) );

#line 1889
                            i_7 = 0U;

#line 1889
                            best_0 = _S140;

#line 1889
                            ovAcc_0 = 0U;

#line 1889
                            for(;;)
                            {

#line 1889
                                if(i_7 < 16U)
                                {
                                }
                                else
                                {

#line 1889
                                    break;
                                }

#line 1889
                                uint _S141 = _S138 + slotToIndex_0(i_7);

#line 1889
                                bool liveB_0 = _S141 < spanB_0;

#line 1889
                                half2 _S142 = _S48[i_7];

#line 1889
                                half2 _S143 = _S49[i_7];

#line 1889
                                half2 _S144 = mag2s_0(_S48[i_7], _S49[i_7]);

#line 1889
                                uint _S145 = (uint(as_type<ushort>(_S144[0U])) & 65535U) | (uint(as_type<ushort>(_S144[1U])) << 16U);

#line 1889
                                if(_S141 < spanA_0)
                                {

#line 1889
                                    ovAcc_1 = _S145 & 65535U;

#line 1889
                                }
                                else
                                {

#line 1889
                                    ovAcc_1 = 0U;

#line 1889
                                }

#line 1889
                                if(liveB_0)
                                {

#line 1889
                                    ovAcc_2 = _S145 & 4294901760U;

#line 1889
                                }
                                else
                                {

#line 1889
                                    ovAcc_2 = 0U;

#line 1889
                                }

#line 1889
                                uint m_0 = ovAcc_1 | ovAcc_2;

#line 1889
                                half2 _S146 = max(best_0, half2(as_type<half>(ushort(m_0 & 65535U)), as_type<half>(ushort((m_0 >> 16U) & 65535U))));

#line 1889
                                uint ovAcc_3 = ovAcc_0 | (((((uint(as_type<ushort>(_S142[0U])) & 65535U) | (uint(as_type<ushort>(_S142[1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(_S143[0U])) & 65535U) | (uint(as_type<ushort>(_S143[1U])) << 16U)) & 2080406528U) + 67109888U));

#line 1889
                                i_7 = i_7 + 1U;

#line 1889
                                best_0 = _S146;

#line 1889
                                ovAcc_0 = ovAcc_3;

#line 1889
                            }

#line 1889
                            if(spanA_0 == 0U)
                            {

#line 1889
                                ovAcc_1 = ovAcc_0 & 4294934527U;

#line 1889
                            }
                            else
                            {

#line 1889
                                ovAcc_1 = ovAcc_0;

#line 1889
                            }

#line 1889
                            if(spanB_0 == 0U)
                            {

#line 1889
                                ovAcc_2 = ovAcc_1 & 2147483647U;

#line 1889
                            }
                            else
                            {

#line 1889
                                ovAcc_2 = ovAcc_1;

#line 1889
                            }

#line 1889
                            if(_S28 == 0U)
                            {

#line 1889
                                uint _S147 = (uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U);

#line 1889
                                float thr2_0 = _S137 * _S137;

#line 1889
                                if((ovAcc_2 & 32768U) != 0U)
                                {

#line 1889
                                    infLocalA_0 = true;

#line 1889
                                }
                                else
                                {

#line 1889
                                    infLocalA_0 = (_S147 & 31744U) == 31744U;

#line 1889
                                }

#line 1889
                                if((ovAcc_2 & 2147483648U) != 0U)
                                {

#line 1889
                                    infLocalB_0 = true;

#line 1889
                                }
                                else
                                {

#line 1889
                                    infLocalB_0 = (_S147 & 2080374784U) == 2080374784U;

#line 1889
                                }

#line 1889
                                if(infLocalA_0)
                                {

#line 1889
                                    hitLocalA_0 = true;

#line 1889
                                }
                                else
                                {

#line 1889
                                    if((_S147 & 32767U) != 0U)
                                    {

#line 1889
                                        hitLocalA_0 = float(best_0.x) >= thr2_0;

#line 1889
                                    }
                                    else
                                    {

#line 1889
                                        hitLocalA_0 = false;

#line 1889
                                    }

#line 1889
                                }

#line 1889
                                if(infLocalB_0)
                                {

#line 1889
                                    hitLocalB_0 = true;

#line 1889
                                }
                                else
                                {

#line 1889
                                    if((_S147 & 2147418112U) != 0U)
                                    {

#line 1889
                                        hitLocalB_0 = float(best_0.y) >= thr2_0;

#line 1889
                                    }
                                    else
                                    {

#line 1889
                                        hitLocalB_0 = false;

#line 1889
                                    }

#line 1889
                                }

#line 1889
                                if(hitLocalA_0)
                                {

#line 1889
                                    bb_0 = 1U;

#line 1889
                                }
                                else
                                {

#line 1889
                                    bb_0 = 0U;

#line 1889
                                }

#line 1889
                                if(hitLocalB_0)
                                {

#line 1889
                                    bb_1 = 2U;

#line 1889
                                }
                                else
                                {

#line 1889
                                    bb_1 = 0U;

#line 1889
                                }

#line 1889
                                uint _S148 = bb_0 | bb_1;

#line 1889
                                uint _S149 = (simd_shuffle_xor((_S148), ushort((1U))));

#line 1889
                                uint hitBits_0 = _S148 | _S149;

#line 1889
                                uint _S150 = (simd_shuffle_xor((hitBits_0), ushort((2U))));

#line 1889
                                uint hitBits_1 = hitBits_0 | _S150;

#line 1889
                                uint _S151 = (simd_shuffle_xor((hitBits_1), ushort((4U))));

#line 1889
                                uint hitBits_2 = hitBits_1 | _S151;

#line 1889
                                uint _S152 = (simd_shuffle_xor((hitBits_2), ushort((8U))));

#line 1889
                                uint hitBits_3 = hitBits_2 | _S152;

#line 1889
                                if(_t_0 == 0U)
                                {

#line 1889
                                    if(q_1 != 4294967295U)
                                    {

#line 1889
                                        packed_float2 device* _S153 = (&kernelContext_1)->entryPointParams_peakVal_0+q_1;

#line 1889
                                        if((hitBits_3 & 1U) != 0U)
                                        {

#line 1889
                                            _S136 = float2(3.40282306073709653e+38f, 0.0f);

#line 1889
                                        }
                                        else
                                        {

#line 1889
                                            _S136 = float2(0.0f, 0.0f);

#line 1889
                                        }

#line 1889
                                        *_S153 = packed_float2(_S136) ;

#line 1889
                                    }

#line 1889
                                    if(n2_0 != 4294967295U)
                                    {

#line 1889
                                        packed_float2 device* _S154 = (&kernelContext_1)->entryPointParams_peakVal_0+n2_0;

#line 1889
                                        if((hitBits_3 & 2U) != 0U)
                                        {

#line 1889
                                            _S136 = float2(3.40282306073709653e+38f, 0.0f);

#line 1889
                                        }
                                        else
                                        {

#line 1889
                                            _S136 = float2(0.0f, 0.0f);

#line 1889
                                        }

#line 1889
                                        *_S154 = packed_float2(_S136) ;

#line 1889
                                    }

#line 1889
                                }

#line 1889
                                break;
                            }

#line 1889
                            uint bb_2 = ((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U)) & 2147450879U;

#line 1889
                            if((ovAcc_2 & 32768U) != 0U)
                            {

#line 1889
                                bb_0 = (bb_2 & 4294901760U) | 31744U;

#line 1889
                            }
                            else
                            {

#line 1889
                                bb_0 = bb_2;

#line 1889
                            }

#line 1889
                            if((ovAcc_2 & 2147483648U) != 0U)
                            {

#line 1889
                                bb_1 = (bb_0 & 65535U) | 2080374784U;

#line 1889
                            }
                            else
                            {

#line 1889
                                bb_1 = bb_0;

#line 1889
                            }

#line 1889
                            uint other_0 = (simd_shuffle_xor((bb_1), ushort((1U))));

#line 1889
                            uint _S155 = (max(bb_1 & 65535U, other_0 & 65535U)) | (max(bb_1 & 4294901760U, other_0 & 4294901760U));

#line 1889
                            uint other_1 = (simd_shuffle_xor((_S155), ushort((2U))));

#line 1889
                            uint _S156 = (max(_S155 & 65535U, other_1 & 65535U)) | (max(_S155 & 4294901760U, other_1 & 4294901760U));

#line 1889
                            uint other_2 = (simd_shuffle_xor((_S156), ushort((4U))));

#line 1889
                            uint _S157 = (max(_S156 & 65535U, other_2 & 65535U)) | (max(_S156 & 4294901760U, other_2 & 4294901760U));

#line 1889
                            uint other_3 = (simd_shuffle_xor((_S157), ushort((8U))));

#line 1889
                            uint bb_3 = (max(_S157 & 65535U, other_3 & 65535U)) | (max(_S157 & 4294901760U, other_3 & 4294901760U));

#line 1889
                            if(_t_0 == 0U)
                            {

#line 1889
                                bool infA_0 = (bb_3 & 31744U) == 31744U;

#line 1889
                                bool infB_0 = (bb_3 & 2080374784U) == 2080374784U;

#line 1889
                                float bA_0 = sqrt(float(as_type<half>(ushort(bb_3 & 65535U))));

#line 1889
                                float bB_0 = sqrt(float(as_type<half>(ushort((bb_3 >> 16U) & 65535U))));

#line 1889
                                if(infA_0)
                                {

#line 1889
                                    hitA_0 = true;

#line 1889
                                }
                                else
                                {

#line 1889
                                    if(bA_0 > 0.0f)
                                    {

#line 1889
                                        infLocalA_0 = bA_0 >= _S137;

#line 1889
                                    }
                                    else
                                    {

#line 1889
                                        infLocalA_0 = false;

#line 1889
                                    }

#line 1889
                                    hitA_0 = infLocalA_0;

#line 1889
                                }

#line 1889
                                if(infB_0)
                                {

#line 1889
                                    hitB_0 = true;

#line 1889
                                }
                                else
                                {

#line 1889
                                    if(bB_0 > 0.0f)
                                    {

#line 1889
                                        infLocalA_0 = bB_0 >= _S137;

#line 1889
                                    }
                                    else
                                    {

#line 1889
                                        infLocalA_0 = false;

#line 1889
                                    }

#line 1889
                                    hitB_0 = infLocalA_0;

#line 1889
                                }

#line 1889
                                if(q_1 != 4294967295U)
                                {

#line 1889
                                    packed_float2 device* _S158 = (&kernelContext_1)->entryPointParams_peakVal_0+q_1;

#line 1889
                                    if(infA_0)
                                    {

#line 1889
                                        _S136 = float2(3.40282306073709653e+38f, 0.0f);

#line 1889
                                    }
                                    else
                                    {

#line 1889
                                        if(hitA_0)
                                        {

#line 1889
                                            _S136 = float2(bA_0, 0.0f);

#line 1889
                                        }
                                        else
                                        {

#line 1889
                                            _S136 = float2(0.0f, 0.0f);

#line 1889
                                        }

#line 1889
                                    }

#line 1889
                                    *_S158 = packed_float2(_S136) ;

#line 1889
                                }

#line 1889
                                if(n2_0 != 4294967295U)
                                {

#line 1889
                                    packed_float2 device* _S159 = (&kernelContext_1)->entryPointParams_peakVal_0+n2_0;

#line 1889
                                    if(infB_0)
                                    {

#line 1889
                                        _S136 = float2(3.40282306073709653e+38f, 0.0f);

#line 1889
                                    }
                                    else
                                    {

#line 1889
                                        if(hitB_0)
                                        {

#line 1889
                                            _S136 = float2(bB_0, 0.0f);

#line 1889
                                        }
                                        else
                                        {

#line 1889
                                            _S136 = float2(0.0f, 0.0f);

#line 1889
                                        }

#line 1889
                                    }

#line 1889
                                    *_S159 = packed_float2(_S136) ;

#line 1889
                                }

#line 1889
                            }

#line 1889
                            break;
                        }

#line 1889
                    }
                    else
                    {

#line 1889
                        array<half2, int(16)> _S160 = _S48;

#line 1889
                        array<half2, int(16)> _S161 = _S49;

#line 1889
                        for(;;)
                        {

#line 1889
                            uint _S162 = slotToIndex_0(_t_0 * 16U) - _S41;

#line 1889
                            bool _S163 = _S42 > _S41;

#line 1889
                            if(_S163)
                            {

#line 1889
                                spanA_0 = _S42 - _S41;

#line 1889
                            }
                            else
                            {

#line 1889
                                spanA_0 = 0U;

#line 1889
                            }

#line 1889
                            if(_S163)
                            {

#line 1889
                                spanB_0 = _S42 - _S41;

#line 1889
                            }
                            else
                            {

#line 1889
                                spanB_0 = 0U;

#line 1889
                            }

#line 1889
                            i_7 = 0U;

#line 1889
                            ovAcc_0 = 0U;

#line 1889
                            ovAcc_1 = 0U;

#line 1889
                            ovAcc_2 = 0U;

#line 1889
                            for(;;)
                            {

#line 1889
                                if(i_7 < 16U)
                                {
                                }
                                else
                                {

#line 1889
                                    break;
                                }

#line 1889
                                uint _S164 = _S162 + slotToIndex_0(i_7);

#line 1889
                                bool liveB_1 = _S164 < spanB_0;

#line 1889
                                half2 mg_0 = mag2s_0(_S160[i_7], _S161[i_7]);

#line 1889
                                uint _S165 = (uint(as_type<ushort>(mg_0[0U])) & 65535U) | (uint(as_type<ushort>(mg_0[1U])) << 16U);

#line 1889
                                uint ovAcc_4 = ovAcc_0 | (((((uint(as_type<ushort>(_S160[i_7][0U])) & 65535U) | (uint(as_type<ushort>(_S160[i_7][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(_S161[i_7][0U])) & 65535U) | (uint(as_type<ushort>(_S161[i_7][1U])) << 16U)) & 2080406528U) + 67109888U));

#line 1889
                                if(_S164 < spanA_0)
                                {

#line 1889
                                    bb_0 = _S165 << 16U;

#line 1889
                                }
                                else
                                {

#line 1889
                                    bb_0 = 0U;

#line 1889
                                }

#line 1889
                                uint _S166 = 15U - i_7;

#line 1889
                                uint _S167 = max(ovAcc_1, bb_0 | _S166);

#line 1889
                                if(liveB_1)
                                {

#line 1889
                                    bb_1 = _S165 & 4294901760U;

#line 1889
                                }
                                else
                                {

#line 1889
                                    bb_1 = 0U;

#line 1889
                                }

#line 1889
                                uint _S168 = max(ovAcc_2, bb_1 | _S166);

#line 1889
                                i_7 = i_7 + 1U;

#line 1889
                                ovAcc_0 = ovAcc_4;

#line 1889
                                ovAcc_1 = _S167;

#line 1889
                                ovAcc_2 = _S168;

#line 1889
                            }

#line 1889
                            bool _S169 = spanA_0 != 0U;

#line 1889
                            if(_S169)
                            {

#line 1889
                                infLocalA_0 = (ovAcc_0 & 32768U) != 0U;

#line 1889
                            }
                            else
                            {

#line 1889
                                infLocalA_0 = false;

#line 1889
                            }

#line 1889
                            if(infLocalA_0)
                            {

#line 1889
                                bb_0 = max(ovAcc_1, 2080374799U);

#line 1889
                            }
                            else
                            {

#line 1889
                                bb_0 = ovAcc_1;

#line 1889
                            }

#line 1889
                            bool _S170 = spanB_0 != 0U;

#line 1889
                            if(_S170)
                            {

#line 1889
                                infLocalB_0 = (ovAcc_0 & 2147483648U) != 0U;

#line 1889
                            }
                            else
                            {

#line 1889
                                infLocalB_0 = false;

#line 1889
                            }

#line 1889
                            if(infLocalB_0)
                            {

#line 1889
                                bb_1 = max(ovAcc_2, 2080374799U);

#line 1889
                            }
                            else
                            {

#line 1889
                                bb_1 = ovAcc_2;

#line 1889
                            }

#line 1889
                            uint _S171 = (4095U - _t_0) << 4U;

#line 1889
                            uint kA_0 = bb_0 | _S171;

#line 1889
                            uint kB_0 = bb_1 | _S171;

#line 1889
                            uint _S172 = (simd_shuffle_xor((kA_0), ushort((1U))));

#line 1889
                            uint _S173 = max(kA_0, _S172);

#line 1889
                            uint _S174 = (simd_shuffle_xor((kB_0), ushort((1U))));

#line 1889
                            uint _S175 = max(kB_0, _S174);

#line 1889
                            uint _S176 = (simd_shuffle_xor((_S173), ushort((2U))));

#line 1889
                            uint _S177 = max(_S173, _S176);

#line 1889
                            uint _S178 = (simd_shuffle_xor((_S175), ushort((2U))));

#line 1889
                            uint _S179 = max(_S175, _S178);

#line 1889
                            uint _S180 = (simd_shuffle_xor((_S177), ushort((4U))));

#line 1889
                            uint _S181 = max(_S177, _S180);

#line 1889
                            uint _S182 = (simd_shuffle_xor((_S179), ushort((4U))));

#line 1889
                            uint _S183 = max(_S179, _S182);

#line 1889
                            uint _S184 = (simd_shuffle_xor((_S181), ushort((8U))));

#line 1889
                            uint _S185 = max(_S181, _S184);

#line 1889
                            uint _S186 = (simd_shuffle_xor((_S183), ushort((8U))));

#line 1889
                            uint _S187 = max(_S183, _S186);

#line 1889
                            uint slotA_0 = 65535U - (_S185 & 65535U);

#line 1889
                            uint slotB_0 = 65535U - (_S187 & 65535U);

#line 1889
                            if(_S169)
                            {

#line 1889
                                hitLocalA_0 = (_S185 >> 16U) >= 31744U;

#line 1889
                            }
                            else
                            {

#line 1889
                                hitLocalA_0 = false;

#line 1889
                            }

#line 1889
                            if(_S170)
                            {

#line 1889
                                hitLocalB_0 = (_S187 >> 16U) >= 31744U;

#line 1889
                            }
                            else
                            {

#line 1889
                                hitLocalB_0 = false;

#line 1889
                            }

#line 1889
                            if(hitLocalA_0)
                            {

#line 1889
                                hitA_0 = true;

#line 1889
                            }
                            else
                            {

#line 1889
                                hitA_0 = (as_type<half>((ushort)((_S185 >> 16U)))) > (as_type<float>((_S29)));

#line 1889
                            }

#line 1889
                            if(hitLocalB_0)
                            {

#line 1889
                                hitB_0 = true;

#line 1889
                            }
                            else
                            {

#line 1889
                                hitB_0 = (as_type<half>((ushort)((_S187 >> 16U)))) > (as_type<float>((_S29)));

#line 1889
                            }

#line 1889
                            uint wA_0 = slotA_0 >> 4U;

#line 1889
                            uint _S188 = slotA_0 & 15U;

#line 1889
                            uint wB_0 = slotB_0 >> 4U;

#line 1889
                            uint _S189 = slotB_0 & 15U;

#line 1889
                            half2 _S190 = half2(float2(0.0f) );

#line 1889
                            uint j_0 = 0U;

#line 1889
                            best_0 = _S190;

#line 1889
                            half2 selB_0 = _S190;

#line 1889
                            for(;;)
                            {

#line 1889
                                if(j_0 < 16U)
                                {
                                }
                                else
                                {

#line 1889
                                    break;
                                }

#line 1889
                                if(j_0 == _S188)
                                {

#line 1889
                                    best_0 = half2(_S160[j_0].x, _S161[j_0].x);

#line 1889
                                }

#line 1889
                                if(j_0 == _S189)
                                {

#line 1889
                                    selB_0 = half2(_S160[j_0].y, _S161[j_0].y);

#line 1889
                                }

#line 1889
                                j_0 = j_0 + 1U;

#line 1889
                            }

#line 1889
                            uint _S191 = (simd_shuffle_xor(((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U)), ushort((wA_0))));

#line 1889
                            half _S192 = as_type<half>(ushort(_S191 & 65535U));

#line 1889
                            half _S193 = as_type<half>(ushort((_S191 >> 16U) & 65535U));

#line 1889
                            uint _S194 = (simd_shuffle_xor(((uint(as_type<ushort>(selB_0[0U])) & 65535U) | (uint(as_type<ushort>(selB_0[1U])) << 16U)), ushort((wB_0))));

#line 1889
                            half _S195 = as_type<half>(ushort(_S194 & 65535U));

#line 1889
                            half _S196 = as_type<half>(ushort((_S194 >> 16U) & 65535U));

#line 1889
                            bool _S197 = _t_0 == 0U;

#line 1889
                            bool _S198;

#line 1889
                            if(_S197)
                            {

#line 1889
                                _S198 = q_1 != 4294967295U;

#line 1889
                            }
                            else
                            {

#line 1889
                                _S198 = false;

#line 1889
                            }

#line 1889
                            int _S199;

#line 1889
                            if(_S198)
                            {

#line 1889
                                int device* _S200 = (&kernelContext_1)->entryPointParams_peakIdx_0+q_1;

#line 1889
                                if(hitA_0)
                                {

#line 1889
                                    _S199 = int(slotToIndex_0(slotA_0));

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S199 = int(-1);

#line 1889
                                }

#line 1889
                                *_S200 = _S199;

#line 1889
                                packed_float2 device* _S201 = (&kernelContext_1)->entryPointParams_peakVal_0+q_1;

#line 1889
                                if(hitLocalA_0)
                                {

#line 1889
                                    _S136 = float2(3.40282306073709653e+38f, 0.0f);

#line 1889
                                }
                                else
                                {

#line 1889
                                    if(hitA_0)
                                    {

#line 1889
                                        _S136 = float2(float(_S192), float(_S193));

#line 1889
                                    }
                                    else
                                    {

#line 1889
                                        _S136 = float2(0.0f, 0.0f);

#line 1889
                                    }

#line 1889
                                }

#line 1889
                                *_S201 = packed_float2(_S136) ;

#line 1889
                            }

#line 1889
                            bool _S202;

#line 1889
                            if(_S197)
                            {

#line 1889
                                _S202 = n2_0 != 4294967295U;

#line 1889
                            }
                            else
                            {

#line 1889
                                _S202 = false;

#line 1889
                            }

#line 1889
                            if(_S202)
                            {

#line 1889
                                int device* _S203 = (&kernelContext_1)->entryPointParams_peakIdx_0+n2_0;

#line 1889
                                if(hitB_0)
                                {

#line 1889
                                    _S199 = int(slotToIndex_0(slotB_0));

#line 1889
                                }
                                else
                                {

#line 1889
                                    _S199 = int(-1);

#line 1889
                                }

#line 1889
                                *_S203 = _S199;

#line 1889
                                packed_float2 device* _S204 = (&kernelContext_1)->entryPointParams_peakVal_0+n2_0;

#line 1889
                                if(hitLocalB_0)
                                {

#line 1889
                                    _S136 = float2(3.40282306073709653e+38f, 0.0f);

#line 1889
                                }
                                else
                                {

#line 1889
                                    if(hitB_0)
                                    {

#line 1889
                                        _S136 = float2(float(_S195), float(_S196));

#line 1889
                                    }
                                    else
                                    {

#line 1889
                                        _S136 = float2(0.0f, 0.0f);

#line 1889
                                    }

#line 1889
                                }

#line 1889
                                *_S204 = packed_float2(_S136) ;

#line 1889
                            }

#line 1889
                            break;
                        }

#line 1889
                    }

#line 1889
                    break;
                }

#line 1889
                break;
            }

#line 1889
            k_0 = k_0 + 2U;

#line 1889
        }

#line 1889
        break;
    }

    return;
}
