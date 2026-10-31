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

#line 10 "mm_256_fusedTierB_c16p8t2.slang"
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


#line 202 "mm_256_fusedTierB_c16p8t2.slang"
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

#line 90 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 232 "mm_256_fusedTierB_c16p8t2.slang"
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


#line 171 "mm_256_fusedTierB_c16p8t2.slang"
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

#line 259 "mm_256_fusedTierB_c16p8t2.slang"
    if(_S7 != 0U)
    {

#line 71 "twiddle.slang"
        uint _S8 = mfDataScaleFlag_0();

#line 260 "mm_256_fusedTierB_c16p8t2.slang"
        float s_0 = (as_type<float>((_S8)));
        uint _S9 = 2U * i_1;

#line 261
        return half2(half((as_type<float>((b_1[_S9]))) * s_0), half((as_type<float>((b_1[_S9 + 1U]))) * s_0));
    }
    return cload_0(b_1, i_1);
}


#line 372
void cmulconjs_0(half2 ar_0, half2 ai_0, half2 br_0, half2 bi_0, half2 thread* pr_0, half2 thread* pi_0)
{
    *pr_0 = ar_0 * br_0 + ai_0 * bi_0;
    *pi_0 = ai_0 * br_0 - ar_0 * bi_0;
    return;
}


#line 384
void r4s_0(array<half2, int(16)> thread* re_0, array<half2, int(16)> thread* im_0, uint a_0, uint b_2, uint c_0, uint d_1)
{
    half2 t0r_0 = (*re_0)[a_0] + (*re_0)[c_0];

#line 386
    half2 t0i_0 = (*im_0)[a_0] + (*im_0)[c_0];
    half2 t1r_0 = (*re_0)[a_0] - (*re_0)[c_0];

#line 387
    half2 t1i_0 = (*im_0)[a_0] - (*im_0)[c_0];
    half2 t2r_0 = (*re_0)[b_2] + (*re_0)[d_1];

#line 388
    half2 t2i_0 = (*im_0)[b_2] + (*im_0)[d_1];
    half2 t3r_0 = (*re_0)[b_2] - (*re_0)[d_1];
    half2 j3r_0 = - ((*im_0)[b_2] - (*im_0)[d_1]);
    (*re_0)[a_0] = t0r_0 + t2r_0;

#line 391
    (*im_0)[a_0] = t0i_0 + t2i_0;
    (*re_0)[b_2] = t1r_0 + j3r_0;

#line 392
    (*im_0)[b_2] = t1i_0 + t3r_0;
    (*re_0)[c_0] = t0r_0 - t2r_0;

#line 393
    (*im_0)[c_0] = t0i_0 - t2i_0;
    (*re_0)[d_1] = t1r_0 - j3r_0;

#line 394
    (*im_0)[d_1] = t1i_0 - t3r_0;
    return;
}


#line 363
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 363
    half2 _S10 = half2(wr_0) ;

#line 363
    half2 _S11 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S11 + *xi_0 * _S10;
    *xr_0 = *xr_0 * _S10 - *xi_0 * _S11;

#line 367
    *xi_0 = ni_0;
    return;
}


#line 397
void swap2_0(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint p_1, uint q_0)
{

    half2 t_0 = (*re_1)[p_1];

#line 400
    (*re_1)[p_1] = (*re_1)[q_0];

#line 400
    (*re_1)[q_0] = t_0;
    half2 t_1 = (*im_1)[p_1];

#line 401
    (*im_1)[p_1] = (*im_1)[q_0];

#line 401
    (*im_1)[q_0] = t_1;
    return;
}


#line 435
void dft16s_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2)
{

#line 435
    uint n1_0 = 0U;

    for(;;)
    {

#line 437
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 437
            break;
        }

#line 437
        r4s_0(re_2, im_2, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 437
        n1_0 = n1_0 + 1U;

#line 437
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

#line 448
    uint k2_0 = 0U;
    for(;;)
    {

#line 449
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 449
            break;
        }

#line 450
        uint _S12 = 4U * k2_0;

#line 450
        r4s_0(re_2, im_2, _S12, _S12 + 1U, _S12 + 2U, _S12 + 3U);

#line 449
        k2_0 = k2_0 + 1U;

#line 449
    }

    swap2_0(re_2, im_2, 1U, 4U);

#line 451
    swap2_0(re_2, im_2, 2U, 8U);

#line 451
    swap2_0(re_2, im_2, 3U, 12U);
    swap2_0(re_2, im_2, 6U, 9U);

#line 452
    swap2_0(re_2, im_2, 7U, 13U);

#line 452
    swap2_0(re_2, im_2, 11U, 14U);
    return;
}


#line 435
void dft16s_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3)
{

#line 435
    uint n1_1 = 0U;

    for(;;)
    {

#line 437
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 437
            break;
        }

#line 437
        r4s_0(re_3, im_3, n1_1, n1_1 + 4U, n1_1 + 8U, n1_1 + 12U);

#line 437
        n1_1 = n1_1 + 1U;

#line 437
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

#line 448
    uint k2_1 = 0U;
    for(;;)
    {

#line 449
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 449
            break;
        }

#line 450
        uint _S13 = 4U * k2_1;

#line 450
        r4s_0(re_3, im_3, _S13, _S13 + 1U, _S13 + 2U, _S13 + 3U);

#line 449
        k2_1 = k2_1 + 1U;

#line 449
    }

    swap2_0(re_3, im_3, 1U, 4U);

#line 451
    swap2_0(re_3, im_3, 2U, 8U);

#line 451
    swap2_0(re_3, im_3, 3U, 12U);
    swap2_0(re_3, im_3, 6U, 9U);

#line 452
    swap2_0(re_3, im_3, 7U, 13U);

#line 452
    swap2_0(re_3, im_3, 11U, 14U);
    return;
}


#line 47 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S14 = ((MF_COARSE_TWT));

#line 50
    return _S14;
}


#line 74
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S15 = ((MF_ACCURATE_TRIG));

#line 77
    return _S15;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S16 = mfAccurateTrigFlag_0();

#line 103
    if(_S16 == 0U)
    {

#line 104
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


#line 575 "mm_256_fusedTierB_c16p8t2.slang"
void innermostS_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4)
{
    dft16s_1(re_4, im_4);



    return;
}


#line 870
uint lgOf_0(uint i_2)
{

#line 870
    uint _S18;

#line 870
    if(i_2 < 1U)
    {

#line 870
        _S18 = 4U;

#line 870
    }
    else
    {

#line 870
        if(i_2 == 1U)
        {

#line 870
            _S18 = 4U;

#line 870
        }
        else
        {

#line 870
            _S18 = 1U;

#line 870
        }

#line 870
    }

#line 870
    return _S18;
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


#line 459
half2 mag2s_0(half2 re_5, half2 im_5)
{

#line 459
    return re_5 * re_5 + im_5 * im_5;
}


#line 1767
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1767
    uint _S19;

#line 1767
    uint _S20;

#line 1767
    uint _S21;

#line 1767
    uint _S22;

#line 1767
    uint _S23;

#line 1767
    uint m_0;

#line 1767
    thread KernelContext_0 kernelContext_1;

#line 1767
    (&kernelContext_1)->entryPointParams_0 = entryPointParams_1;

#line 1767
    (&kernelContext_1)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1767
    (&kernelContext_1)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1767
    (&kernelContext_1)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1767
    (&kernelContext_1)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1767
    (&kernelContext_1)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1767
    (&kernelContext_1)->_binPhase_0 = 0U;

#line 1787
    uint _S24 = lid_0.x;

#line 1787
    uint _sub_0 = _S24 / 16U;
    uint _pr_0 = gid_0.x * 8U + _sub_0;

#line 1788
    uint _t_0 = _S24 % 16U;
    (&kernelContext_1)->_stgBase_0 = _sub_0 * 256U;

#line 1789
    uint _S25 = entryPointParams_1->ntmpl_0;

#line 1789
    uint _S26 = entryPointParams_1->winStart_0;

#line 1789
    uint _S27 = entryPointParams_1->winEnd_0;

#line 1789
    uint _S28 = entryPointParams_1->binsize_0;

#line 1789
    uint _S29 = entryPointParams_1->thrBits_0;

#line 1799
    for(;;)
    {

#line 1799
        thread uint _S30 = _S26;

#line 1799
        thread uint _S31 = _S27;

#line 1799
        (&kernelContext_1)->_tid_0 = _t_0;

#line 1799
        uint tiles_0 = (_S25 + 2U - 1U) / 2U;

#line 1799
        uint slots_0 = _S28 * tiles_0;

#line 1799
        bool slotOk_0 = _pr_0 < slots_0;

#line 1799
        uint q_1;

#line 1799
        if(slotOk_0)
        {

#line 1799
            q_1 = _pr_0;

#line 1799
        }
        else
        {

#line 1799
            q_1 = slots_0 - 1U;

#line 1799
        }

#line 1799
        uint d_2 = q_1 / tiles_0;

#line 1799
        uint t0_0 = (q_1 - d_2 * tiles_0) * 2U;

#line 1799
        uint _S32 = d_2 * _S25 + t0_0;

#line 1799
        rowWindow_0(d_2, &_S30, &_S31, (&kernelContext_1)->entryPointParams_rowWin_0, &kernelContext_1);

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
            uint _S33 = mfDataStrideFlag_0();

#line 1799
            if(_S33 != 0U)
            {

#line 1799
                uint _S34 = mfDataStrideFlag_0();

#line 1799
                q_1 = _S34;

#line 1799
            }
            else
            {

#line 1799
                q_1 = 256U;

#line 1799
            }

#line 1799
            half2 _S35 = dload_0((&kernelContext_1)->entryPointParams_data_0, d_2 * q_1 + _t_0 + 16U * n2_0);

#line 1799
            dreg_0[n2_0] = _S35;

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
            if(k_0 < 2U)
            {
            }
            else
            {

#line 1799
                break;
            }

#line 1799
            bool okA_0;

#line 1799
            if(slotOk_0)
            {

#line 1799
                okA_0 = (t0_0 + k_0) < _S25;

#line 1799
            }
            else
            {

#line 1799
                okA_0 = false;

#line 1799
            }

#line 1799
            bool okB_0;

#line 1799
            if(slotOk_0)
            {

#line 1799
                okB_0 = (t0_0 + k_0 + 1U) < _S25;

#line 1799
            }
            else
            {

#line 1799
                okB_0 = false;

#line 1799
            }

#line 1799
            if(okA_0)
            {

#line 1799
                q_1 = _S32 + k_0;

#line 1799
            }
            else
            {

#line 1799
                q_1 = 4294967295U;

#line 1799
            }

#line 1799
            if(okB_0)
            {

#line 1799
                n2_0 = _S32 + k_0 + 1U;

#line 1799
            }
            else
            {

#line 1799
                n2_0 = 4294967295U;

#line 1799
            }

#line 1799
            uint _S36 = t0_0 + k_0;

#line 1799
            uint _S37 = _S25 - 1U;

#line 1799
            uint _S38 = min(_S36, _S37);

#line 1799
            uint _S39 = min(_S36 + 1U, _S37);

#line 1799
            array<half2, int(16)> _S40 = dreg_0;

#line 1799
            uint _S41 = _S30;

#line 1799
            uint _S42 = _S31;

#line 1799
            for(;;)
            {

#line 1799
                thread array<half2, int(16)> re_6;

#line 1799
                thread array<half2, int(16)> im_6;

#line 1799
                uint n2_1 = 0U;

#line 1799
                for(;;)
                {

#line 1799
                    if(n2_1 < 16U)
                    {
                    }
                    else
                    {

#line 1799
                        break;
                    }

#line 1799
                    uint _S43 = 16U * n2_1;

#line 1799
                    half2 ta_0 = cload_0((&kernelContext_1)->entryPointParams_tmpl_0, _S38 * 256U + _t_0 + _S43);

#line 1799
                    half2 tb_0 = cload_0((&kernelContext_1)->entryPointParams_tmpl_0, _S39 * 256U + _t_0 + _S43);

#line 1799
                    half _S44 = _S40[n2_1].x;

#line 1799
                    half _S45 = _S40[n2_1].y;

#line 1799
                    cmulconjs_0(half2(_S44, _S44), half2(_S45, _S45), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_6[n2_1], &im_6[n2_1]);

#line 1799
                    n2_1 = n2_1 + 1U;

#line 1799
                }

#line 1799
                for(;;)
                {

#line 1799
                    uint lgTB_0 = firstbithigh_0(16U);

#line 1799
                    uint lane_0 = _t_0 & 15U;

#line 1799
                    dft16s_0(&re_6, &im_6);

#line 1799
                    uint _S46 = mfCoarseTwtFlag_0();

#line 1799
                    uint i_3;

#line 1799
                    if(_S46 != 0U)
                    {

#line 1799
                        i_3 = 0U;

#line 1799
                        for(;;)
                        {

#line 1799
                            if(i_3 < 16U)
                            {
                            }
                            else
                            {

#line 1799
                                break;
                            }

#line 1799
                            uint _S47 = lane_0 * 16U + i_3;

#line 1799
                            cmulw_0(&re_6[i_3], &im_6[i_3], as_type<half>(ushort((COARSE_TWT_DATA_0[_S47]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S47]) >> 16U) & 65535U)));

#line 1799
                            i_3 = i_3 + 1U;

#line 1799
                        }

#line 1799
                    }
                    else
                    {

#line 1799
                        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_0) / 256.0f);

#line 1799
                        float _S48 = tw_0.x;

#line 1799
                        float _S49 = tw_0.y;

#line 1799
                        i_3 = 0U;

#line 1799
                        float cr_0 = 1.0f;

#line 1799
                        float ci_0 = 0.0f;

#line 1799
                        for(;;)
                        {

#line 1799
                            if(i_3 < 16U)
                            {
                            }
                            else
                            {

#line 1799
                                break;
                            }

#line 1799
                            cmulw_0(&re_6[i_3], &im_6[i_3], half(cr_0), half(ci_0));

#line 1799
                            float nr_0 = cr_0 * _S48 - ci_0 * _S49;

#line 1799
                            float _S50 = cr_0 * _S49 + ci_0 * _S48;

#line 1799
                            i_3 = i_3 + 1U;

#line 1799
                            cr_0 = nr_0;

#line 1799
                            ci_0 = _S50;

#line 1799
                        }

#line 1799
                    }

#line 1799
                    uint per_0 = 16U / max(16U, 1U);

#line 1799
                    uint _S51 = max(1U, 1U);

#line 1799
                    uint blk2_0 = _t_0 / _S51;

#line 1799
                    uint lane2_0 = _t_0 % _S51;

#line 1799
                    for(;;)
                    {

#line 1799
                        uint _S52 = (&kernelContext_1)->_tid_0;

#line 1799
                        for(;;)
                        {

#line 1799
                            thread array<uint, int(16)> t_2;

#line 1799
                            i_3 = 0U;

#line 1799
                            for(;;)
                            {

#line 1799
                                if(i_3 < 16U)
                                {
                                }
                                else
                                {

#line 1799
                                    break;
                                }

#line 1799
                                t_2[i_3] = (uint(as_type<ushort>(re_6[i_3][0U])) & 65535U) | (uint(as_type<ushort>(re_6[i_3][1U])) << 16U);

#line 1799
                                i_3 = i_3 + 1U;

#line 1799
                            }

#line 1799
                            uint shift_0 = lgTB_0 - 4U;

#line 1799
                            _S19 = shift_0;

#line 1799
                            uint _S53 = (_S52 >> shift_0) & 15U;

#line 1799
                            bool _S54 = (_S53 & 1U) != 0U;

#line 1799
                            uint _S55;

#line 1799
                            if(_S54)
                            {

#line 1799
                                _S55 = t_2[0U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S55 = t_2[1U];

#line 1799
                            }

#line 1799
                            uint _S56 = 1U << shift_0;

#line 1799
                            _S20 = _S56;

#line 1799
                            uint partner_0 = (simd_shuffle_xor((_S55), ushort((_S56))));

#line 1799
                            if(_S54)
                            {

#line 1799
                                t_2[0U] = partner_0;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[1U] = partner_0;

#line 1799
                            }

#line 1799
                            uint _S57;

#line 1799
                            if(_S54)
                            {

#line 1799
                                _S57 = t_2[2U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S57 = t_2[3U];

#line 1799
                            }

#line 1799
                            uint partner_1 = (simd_shuffle_xor((_S57), ushort((_S56))));

#line 1799
                            if(_S54)
                            {

#line 1799
                                t_2[2U] = partner_1;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[3U] = partner_1;

#line 1799
                            }

#line 1799
                            uint _S58;

#line 1799
                            if(_S54)
                            {

#line 1799
                                _S58 = t_2[4U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S58 = t_2[5U];

#line 1799
                            }

#line 1799
                            uint partner_2 = (simd_shuffle_xor((_S58), ushort((_S56))));

#line 1799
                            if(_S54)
                            {

#line 1799
                                t_2[4U] = partner_2;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[5U] = partner_2;

#line 1799
                            }

#line 1799
                            uint _S59;

#line 1799
                            if(_S54)
                            {

#line 1799
                                _S59 = t_2[6U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S59 = t_2[7U];

#line 1799
                            }

#line 1799
                            uint partner_3 = (simd_shuffle_xor((_S59), ushort((_S56))));

#line 1799
                            if(_S54)
                            {

#line 1799
                                t_2[6U] = partner_3;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[7U] = partner_3;

#line 1799
                            }

#line 1799
                            uint _S60;

#line 1799
                            if(_S54)
                            {

#line 1799
                                _S60 = t_2[8U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S60 = t_2[9U];

#line 1799
                            }

#line 1799
                            uint partner_4 = (simd_shuffle_xor((_S60), ushort((_S56))));

#line 1799
                            if(_S54)
                            {

#line 1799
                                t_2[8U] = partner_4;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[9U] = partner_4;

#line 1799
                            }

#line 1799
                            uint _S61;

#line 1799
                            if(_S54)
                            {

#line 1799
                                _S61 = t_2[10U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S61 = t_2[11U];

#line 1799
                            }

#line 1799
                            uint partner_5 = (simd_shuffle_xor((_S61), ushort((_S56))));

#line 1799
                            if(_S54)
                            {

#line 1799
                                t_2[10U] = partner_5;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[11U] = partner_5;

#line 1799
                            }

#line 1799
                            uint _S62;

#line 1799
                            if(_S54)
                            {

#line 1799
                                _S62 = t_2[12U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S62 = t_2[13U];

#line 1799
                            }

#line 1799
                            uint partner_6 = (simd_shuffle_xor((_S62), ushort((_S56))));

#line 1799
                            if(_S54)
                            {

#line 1799
                                t_2[12U] = partner_6;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[13U] = partner_6;

#line 1799
                            }

#line 1799
                            uint _S63;

#line 1799
                            if(_S54)
                            {

#line 1799
                                _S63 = t_2[14U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S63 = t_2[15U];

#line 1799
                            }

#line 1799
                            uint partner_7 = (simd_shuffle_xor((_S63), ushort((_S56))));

#line 1799
                            if(_S54)
                            {

#line 1799
                                t_2[14U] = partner_7;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[15U] = partner_7;

#line 1799
                            }

#line 1799
                            bool _S64 = (_S53 & 2U) != 0U;

#line 1799
                            uint _S65;

#line 1799
                            if(_S64)
                            {

#line 1799
                                _S65 = t_2[0U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S65 = t_2[2U];

#line 1799
                            }

#line 1799
                            uint _S66 = 2U << shift_0;

#line 1799
                            _S21 = _S66;

#line 1799
                            uint partner_8 = (simd_shuffle_xor((_S65), ushort((_S66))));

#line 1799
                            if(_S64)
                            {

#line 1799
                                t_2[0U] = partner_8;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[2U] = partner_8;

#line 1799
                            }

#line 1799
                            uint _S67;

#line 1799
                            if(_S64)
                            {

#line 1799
                                _S67 = t_2[1U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S67 = t_2[3U];

#line 1799
                            }

#line 1799
                            uint partner_9 = (simd_shuffle_xor((_S67), ushort((_S66))));

#line 1799
                            if(_S64)
                            {

#line 1799
                                t_2[1U] = partner_9;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[3U] = partner_9;

#line 1799
                            }

#line 1799
                            uint _S68;

#line 1799
                            if(_S64)
                            {

#line 1799
                                _S68 = t_2[4U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S68 = t_2[6U];

#line 1799
                            }

#line 1799
                            uint partner_10 = (simd_shuffle_xor((_S68), ushort((_S66))));

#line 1799
                            if(_S64)
                            {

#line 1799
                                t_2[4U] = partner_10;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[6U] = partner_10;

#line 1799
                            }

#line 1799
                            uint _S69;

#line 1799
                            if(_S64)
                            {

#line 1799
                                _S69 = t_2[5U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S69 = t_2[7U];

#line 1799
                            }

#line 1799
                            uint partner_11 = (simd_shuffle_xor((_S69), ushort((_S66))));

#line 1799
                            if(_S64)
                            {

#line 1799
                                t_2[5U] = partner_11;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[7U] = partner_11;

#line 1799
                            }

#line 1799
                            uint _S70;

#line 1799
                            if(_S64)
                            {

#line 1799
                                _S70 = t_2[8U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S70 = t_2[10U];

#line 1799
                            }

#line 1799
                            uint partner_12 = (simd_shuffle_xor((_S70), ushort((_S66))));

#line 1799
                            if(_S64)
                            {

#line 1799
                                t_2[8U] = partner_12;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[10U] = partner_12;

#line 1799
                            }

#line 1799
                            uint _S71;

#line 1799
                            if(_S64)
                            {

#line 1799
                                _S71 = t_2[9U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S71 = t_2[11U];

#line 1799
                            }

#line 1799
                            uint partner_13 = (simd_shuffle_xor((_S71), ushort((_S66))));

#line 1799
                            if(_S64)
                            {

#line 1799
                                t_2[9U] = partner_13;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[11U] = partner_13;

#line 1799
                            }

#line 1799
                            uint _S72;

#line 1799
                            if(_S64)
                            {

#line 1799
                                _S72 = t_2[12U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S72 = t_2[14U];

#line 1799
                            }

#line 1799
                            uint partner_14 = (simd_shuffle_xor((_S72), ushort((_S66))));

#line 1799
                            if(_S64)
                            {

#line 1799
                                t_2[12U] = partner_14;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[14U] = partner_14;

#line 1799
                            }

#line 1799
                            uint _S73;

#line 1799
                            if(_S64)
                            {

#line 1799
                                _S73 = t_2[13U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S73 = t_2[15U];

#line 1799
                            }

#line 1799
                            uint partner_15 = (simd_shuffle_xor((_S73), ushort((_S66))));

#line 1799
                            if(_S64)
                            {

#line 1799
                                t_2[13U] = partner_15;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[15U] = partner_15;

#line 1799
                            }

#line 1799
                            bool _S74 = (_S53 & 4U) != 0U;

#line 1799
                            uint _S75;

#line 1799
                            if(_S74)
                            {

#line 1799
                                _S75 = t_2[0U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S75 = t_2[4U];

#line 1799
                            }

#line 1799
                            uint _S76 = 4U << shift_0;

#line 1799
                            _S22 = _S76;

#line 1799
                            uint partner_16 = (simd_shuffle_xor((_S75), ushort((_S76))));

#line 1799
                            if(_S74)
                            {

#line 1799
                                t_2[0U] = partner_16;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[4U] = partner_16;

#line 1799
                            }

#line 1799
                            uint _S77;

#line 1799
                            if(_S74)
                            {

#line 1799
                                _S77 = t_2[1U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S77 = t_2[5U];

#line 1799
                            }

#line 1799
                            uint partner_17 = (simd_shuffle_xor((_S77), ushort((_S76))));

#line 1799
                            if(_S74)
                            {

#line 1799
                                t_2[1U] = partner_17;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[5U] = partner_17;

#line 1799
                            }

#line 1799
                            uint _S78;

#line 1799
                            if(_S74)
                            {

#line 1799
                                _S78 = t_2[2U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S78 = t_2[6U];

#line 1799
                            }

#line 1799
                            uint partner_18 = (simd_shuffle_xor((_S78), ushort((_S76))));

#line 1799
                            if(_S74)
                            {

#line 1799
                                t_2[2U] = partner_18;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[6U] = partner_18;

#line 1799
                            }

#line 1799
                            uint _S79;

#line 1799
                            if(_S74)
                            {

#line 1799
                                _S79 = t_2[3U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S79 = t_2[7U];

#line 1799
                            }

#line 1799
                            uint partner_19 = (simd_shuffle_xor((_S79), ushort((_S76))));

#line 1799
                            if(_S74)
                            {

#line 1799
                                t_2[3U] = partner_19;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[7U] = partner_19;

#line 1799
                            }

#line 1799
                            uint _S80;

#line 1799
                            if(_S74)
                            {

#line 1799
                                _S80 = t_2[8U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S80 = t_2[12U];

#line 1799
                            }

#line 1799
                            uint partner_20 = (simd_shuffle_xor((_S80), ushort((_S76))));

#line 1799
                            if(_S74)
                            {

#line 1799
                                t_2[8U] = partner_20;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[12U] = partner_20;

#line 1799
                            }

#line 1799
                            uint _S81;

#line 1799
                            if(_S74)
                            {

#line 1799
                                _S81 = t_2[9U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S81 = t_2[13U];

#line 1799
                            }

#line 1799
                            uint partner_21 = (simd_shuffle_xor((_S81), ushort((_S76))));

#line 1799
                            if(_S74)
                            {

#line 1799
                                t_2[9U] = partner_21;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[13U] = partner_21;

#line 1799
                            }

#line 1799
                            uint _S82;

#line 1799
                            if(_S74)
                            {

#line 1799
                                _S82 = t_2[10U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S82 = t_2[14U];

#line 1799
                            }

#line 1799
                            uint partner_22 = (simd_shuffle_xor((_S82), ushort((_S76))));

#line 1799
                            if(_S74)
                            {

#line 1799
                                t_2[10U] = partner_22;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[14U] = partner_22;

#line 1799
                            }

#line 1799
                            uint _S83;

#line 1799
                            if(_S74)
                            {

#line 1799
                                _S83 = t_2[11U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S83 = t_2[15U];

#line 1799
                            }

#line 1799
                            uint partner_23 = (simd_shuffle_xor((_S83), ushort((_S76))));

#line 1799
                            if(_S74)
                            {

#line 1799
                                t_2[11U] = partner_23;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[15U] = partner_23;

#line 1799
                            }

#line 1799
                            bool _S84 = (_S53 & 8U) != 0U;

#line 1799
                            uint _S85;

#line 1799
                            if(_S84)
                            {

#line 1799
                                _S85 = t_2[0U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S85 = t_2[8U];

#line 1799
                            }

#line 1799
                            uint _S86 = 8U << shift_0;

#line 1799
                            _S23 = _S86;

#line 1799
                            uint partner_24 = (simd_shuffle_xor((_S85), ushort((_S86))));

#line 1799
                            if(_S84)
                            {

#line 1799
                                t_2[0U] = partner_24;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[8U] = partner_24;

#line 1799
                            }

#line 1799
                            uint _S87;

#line 1799
                            if(_S84)
                            {

#line 1799
                                _S87 = t_2[1U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S87 = t_2[9U];

#line 1799
                            }

#line 1799
                            uint partner_25 = (simd_shuffle_xor((_S87), ushort((_S86))));

#line 1799
                            if(_S84)
                            {

#line 1799
                                t_2[1U] = partner_25;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[9U] = partner_25;

#line 1799
                            }

#line 1799
                            uint _S88;

#line 1799
                            if(_S84)
                            {

#line 1799
                                _S88 = t_2[2U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S88 = t_2[10U];

#line 1799
                            }

#line 1799
                            uint partner_26 = (simd_shuffle_xor((_S88), ushort((_S86))));

#line 1799
                            if(_S84)
                            {

#line 1799
                                t_2[2U] = partner_26;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[10U] = partner_26;

#line 1799
                            }

#line 1799
                            uint _S89;

#line 1799
                            if(_S84)
                            {

#line 1799
                                _S89 = t_2[3U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S89 = t_2[11U];

#line 1799
                            }

#line 1799
                            uint partner_27 = (simd_shuffle_xor((_S89), ushort((_S86))));

#line 1799
                            if(_S84)
                            {

#line 1799
                                t_2[3U] = partner_27;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[11U] = partner_27;

#line 1799
                            }

#line 1799
                            uint _S90;

#line 1799
                            if(_S84)
                            {

#line 1799
                                _S90 = t_2[4U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S90 = t_2[12U];

#line 1799
                            }

#line 1799
                            uint partner_28 = (simd_shuffle_xor((_S90), ushort((_S86))));

#line 1799
                            if(_S84)
                            {

#line 1799
                                t_2[4U] = partner_28;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[12U] = partner_28;

#line 1799
                            }

#line 1799
                            uint _S91;

#line 1799
                            if(_S84)
                            {

#line 1799
                                _S91 = t_2[5U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S91 = t_2[13U];

#line 1799
                            }

#line 1799
                            uint partner_29 = (simd_shuffle_xor((_S91), ushort((_S86))));

#line 1799
                            if(_S84)
                            {

#line 1799
                                t_2[5U] = partner_29;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[13U] = partner_29;

#line 1799
                            }

#line 1799
                            uint _S92;

#line 1799
                            if(_S84)
                            {

#line 1799
                                _S92 = t_2[6U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S92 = t_2[14U];

#line 1799
                            }

#line 1799
                            uint partner_30 = (simd_shuffle_xor((_S92), ushort((_S86))));

#line 1799
                            if(_S84)
                            {

#line 1799
                                t_2[6U] = partner_30;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[14U] = partner_30;

#line 1799
                            }

#line 1799
                            uint _S93;

#line 1799
                            if(_S84)
                            {

#line 1799
                                _S93 = t_2[7U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S93 = t_2[15U];

#line 1799
                            }

#line 1799
                            uint partner_31 = (simd_shuffle_xor((_S93), ushort((_S86))));

#line 1799
                            if(_S84)
                            {

#line 1799
                                t_2[7U] = partner_31;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_2[15U] = partner_31;

#line 1799
                            }

#line 1799
                            uint i_4 = 0U;

#line 1799
                            for(;;)
                            {

#line 1799
                                if(i_4 < 16U)
                                {
                                }
                                else
                                {

#line 1799
                                    break;
                                }

#line 1799
                                re_6[i_4] = half2(as_type<half>(ushort((t_2[i_4]) & 65535U)), as_type<half>(ushort(((t_2[i_4]) >> 16U) & 65535U)));

#line 1799
                                i_4 = i_4 + 1U;

#line 1799
                            }

#line 1799
                            break;
                        }

#line 1799
                        uint _S94 = (&kernelContext_1)->_tid_0;

#line 1799
                        for(;;)
                        {

#line 1799
                            thread array<uint, int(16)> t_3;

#line 1799
                            uint i_5 = 0U;

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
                                t_3[i_5] = (uint(as_type<ushort>(im_6[i_5][0U])) & 65535U) | (uint(as_type<ushort>(im_6[i_5][1U])) << 16U);

#line 1799
                                i_5 = i_5 + 1U;

#line 1799
                            }

#line 1799
                            uint _S95 = (_S94 >> _S19) & 15U;

#line 1799
                            bool _S96 = (_S95 & 1U) != 0U;

#line 1799
                            uint _S97;

#line 1799
                            if(_S96)
                            {

#line 1799
                                _S97 = t_3[0U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S97 = t_3[1U];

#line 1799
                            }

#line 1799
                            uint partner_32 = (simd_shuffle_xor((_S97), ushort((_S20))));

#line 1799
                            if(_S96)
                            {

#line 1799
                                t_3[0U] = partner_32;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[1U] = partner_32;

#line 1799
                            }

#line 1799
                            uint _S98;

#line 1799
                            if(_S96)
                            {

#line 1799
                                _S98 = t_3[2U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S98 = t_3[3U];

#line 1799
                            }

#line 1799
                            uint partner_33 = (simd_shuffle_xor((_S98), ushort((_S20))));

#line 1799
                            if(_S96)
                            {

#line 1799
                                t_3[2U] = partner_33;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[3U] = partner_33;

#line 1799
                            }

#line 1799
                            uint _S99;

#line 1799
                            if(_S96)
                            {

#line 1799
                                _S99 = t_3[4U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S99 = t_3[5U];

#line 1799
                            }

#line 1799
                            uint partner_34 = (simd_shuffle_xor((_S99), ushort((_S20))));

#line 1799
                            if(_S96)
                            {

#line 1799
                                t_3[4U] = partner_34;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[5U] = partner_34;

#line 1799
                            }

#line 1799
                            uint _S100;

#line 1799
                            if(_S96)
                            {

#line 1799
                                _S100 = t_3[6U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S100 = t_3[7U];

#line 1799
                            }

#line 1799
                            uint partner_35 = (simd_shuffle_xor((_S100), ushort((_S20))));

#line 1799
                            if(_S96)
                            {

#line 1799
                                t_3[6U] = partner_35;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[7U] = partner_35;

#line 1799
                            }

#line 1799
                            uint _S101;

#line 1799
                            if(_S96)
                            {

#line 1799
                                _S101 = t_3[8U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S101 = t_3[9U];

#line 1799
                            }

#line 1799
                            uint partner_36 = (simd_shuffle_xor((_S101), ushort((_S20))));

#line 1799
                            if(_S96)
                            {

#line 1799
                                t_3[8U] = partner_36;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[9U] = partner_36;

#line 1799
                            }

#line 1799
                            uint _S102;

#line 1799
                            if(_S96)
                            {

#line 1799
                                _S102 = t_3[10U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S102 = t_3[11U];

#line 1799
                            }

#line 1799
                            uint partner_37 = (simd_shuffle_xor((_S102), ushort((_S20))));

#line 1799
                            if(_S96)
                            {

#line 1799
                                t_3[10U] = partner_37;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[11U] = partner_37;

#line 1799
                            }

#line 1799
                            uint _S103;

#line 1799
                            if(_S96)
                            {

#line 1799
                                _S103 = t_3[12U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S103 = t_3[13U];

#line 1799
                            }

#line 1799
                            uint partner_38 = (simd_shuffle_xor((_S103), ushort((_S20))));

#line 1799
                            if(_S96)
                            {

#line 1799
                                t_3[12U] = partner_38;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[13U] = partner_38;

#line 1799
                            }

#line 1799
                            uint _S104;

#line 1799
                            if(_S96)
                            {

#line 1799
                                _S104 = t_3[14U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S104 = t_3[15U];

#line 1799
                            }

#line 1799
                            uint partner_39 = (simd_shuffle_xor((_S104), ushort((_S20))));

#line 1799
                            if(_S96)
                            {

#line 1799
                                t_3[14U] = partner_39;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[15U] = partner_39;

#line 1799
                            }

#line 1799
                            bool _S105 = (_S95 & 2U) != 0U;

#line 1799
                            uint _S106;

#line 1799
                            if(_S105)
                            {

#line 1799
                                _S106 = t_3[0U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S106 = t_3[2U];

#line 1799
                            }

#line 1799
                            uint partner_40 = (simd_shuffle_xor((_S106), ushort((_S21))));

#line 1799
                            if(_S105)
                            {

#line 1799
                                t_3[0U] = partner_40;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[2U] = partner_40;

#line 1799
                            }

#line 1799
                            uint _S107;

#line 1799
                            if(_S105)
                            {

#line 1799
                                _S107 = t_3[1U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S107 = t_3[3U];

#line 1799
                            }

#line 1799
                            uint partner_41 = (simd_shuffle_xor((_S107), ushort((_S21))));

#line 1799
                            if(_S105)
                            {

#line 1799
                                t_3[1U] = partner_41;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[3U] = partner_41;

#line 1799
                            }

#line 1799
                            uint _S108;

#line 1799
                            if(_S105)
                            {

#line 1799
                                _S108 = t_3[4U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S108 = t_3[6U];

#line 1799
                            }

#line 1799
                            uint partner_42 = (simd_shuffle_xor((_S108), ushort((_S21))));

#line 1799
                            if(_S105)
                            {

#line 1799
                                t_3[4U] = partner_42;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[6U] = partner_42;

#line 1799
                            }

#line 1799
                            uint _S109;

#line 1799
                            if(_S105)
                            {

#line 1799
                                _S109 = t_3[5U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S109 = t_3[7U];

#line 1799
                            }

#line 1799
                            uint partner_43 = (simd_shuffle_xor((_S109), ushort((_S21))));

#line 1799
                            if(_S105)
                            {

#line 1799
                                t_3[5U] = partner_43;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[7U] = partner_43;

#line 1799
                            }

#line 1799
                            uint _S110;

#line 1799
                            if(_S105)
                            {

#line 1799
                                _S110 = t_3[8U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S110 = t_3[10U];

#line 1799
                            }

#line 1799
                            uint partner_44 = (simd_shuffle_xor((_S110), ushort((_S21))));

#line 1799
                            if(_S105)
                            {

#line 1799
                                t_3[8U] = partner_44;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[10U] = partner_44;

#line 1799
                            }

#line 1799
                            uint _S111;

#line 1799
                            if(_S105)
                            {

#line 1799
                                _S111 = t_3[9U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S111 = t_3[11U];

#line 1799
                            }

#line 1799
                            uint partner_45 = (simd_shuffle_xor((_S111), ushort((_S21))));

#line 1799
                            if(_S105)
                            {

#line 1799
                                t_3[9U] = partner_45;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[11U] = partner_45;

#line 1799
                            }

#line 1799
                            uint _S112;

#line 1799
                            if(_S105)
                            {

#line 1799
                                _S112 = t_3[12U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S112 = t_3[14U];

#line 1799
                            }

#line 1799
                            uint partner_46 = (simd_shuffle_xor((_S112), ushort((_S21))));

#line 1799
                            if(_S105)
                            {

#line 1799
                                t_3[12U] = partner_46;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[14U] = partner_46;

#line 1799
                            }

#line 1799
                            uint _S113;

#line 1799
                            if(_S105)
                            {

#line 1799
                                _S113 = t_3[13U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S113 = t_3[15U];

#line 1799
                            }

#line 1799
                            uint partner_47 = (simd_shuffle_xor((_S113), ushort((_S21))));

#line 1799
                            if(_S105)
                            {

#line 1799
                                t_3[13U] = partner_47;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[15U] = partner_47;

#line 1799
                            }

#line 1799
                            bool _S114 = (_S95 & 4U) != 0U;

#line 1799
                            uint _S115;

#line 1799
                            if(_S114)
                            {

#line 1799
                                _S115 = t_3[0U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S115 = t_3[4U];

#line 1799
                            }

#line 1799
                            uint partner_48 = (simd_shuffle_xor((_S115), ushort((_S22))));

#line 1799
                            if(_S114)
                            {

#line 1799
                                t_3[0U] = partner_48;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[4U] = partner_48;

#line 1799
                            }

#line 1799
                            uint _S116;

#line 1799
                            if(_S114)
                            {

#line 1799
                                _S116 = t_3[1U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S116 = t_3[5U];

#line 1799
                            }

#line 1799
                            uint partner_49 = (simd_shuffle_xor((_S116), ushort((_S22))));

#line 1799
                            if(_S114)
                            {

#line 1799
                                t_3[1U] = partner_49;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[5U] = partner_49;

#line 1799
                            }

#line 1799
                            uint _S117;

#line 1799
                            if(_S114)
                            {

#line 1799
                                _S117 = t_3[2U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S117 = t_3[6U];

#line 1799
                            }

#line 1799
                            uint partner_50 = (simd_shuffle_xor((_S117), ushort((_S22))));

#line 1799
                            if(_S114)
                            {

#line 1799
                                t_3[2U] = partner_50;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[6U] = partner_50;

#line 1799
                            }

#line 1799
                            uint _S118;

#line 1799
                            if(_S114)
                            {

#line 1799
                                _S118 = t_3[3U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S118 = t_3[7U];

#line 1799
                            }

#line 1799
                            uint partner_51 = (simd_shuffle_xor((_S118), ushort((_S22))));

#line 1799
                            if(_S114)
                            {

#line 1799
                                t_3[3U] = partner_51;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[7U] = partner_51;

#line 1799
                            }

#line 1799
                            uint _S119;

#line 1799
                            if(_S114)
                            {

#line 1799
                                _S119 = t_3[8U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S119 = t_3[12U];

#line 1799
                            }

#line 1799
                            uint partner_52 = (simd_shuffle_xor((_S119), ushort((_S22))));

#line 1799
                            if(_S114)
                            {

#line 1799
                                t_3[8U] = partner_52;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[12U] = partner_52;

#line 1799
                            }

#line 1799
                            uint _S120;

#line 1799
                            if(_S114)
                            {

#line 1799
                                _S120 = t_3[9U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S120 = t_3[13U];

#line 1799
                            }

#line 1799
                            uint partner_53 = (simd_shuffle_xor((_S120), ushort((_S22))));

#line 1799
                            if(_S114)
                            {

#line 1799
                                t_3[9U] = partner_53;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[13U] = partner_53;

#line 1799
                            }

#line 1799
                            uint _S121;

#line 1799
                            if(_S114)
                            {

#line 1799
                                _S121 = t_3[10U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S121 = t_3[14U];

#line 1799
                            }

#line 1799
                            uint partner_54 = (simd_shuffle_xor((_S121), ushort((_S22))));

#line 1799
                            if(_S114)
                            {

#line 1799
                                t_3[10U] = partner_54;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[14U] = partner_54;

#line 1799
                            }

#line 1799
                            uint _S122;

#line 1799
                            if(_S114)
                            {

#line 1799
                                _S122 = t_3[11U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S122 = t_3[15U];

#line 1799
                            }

#line 1799
                            uint partner_55 = (simd_shuffle_xor((_S122), ushort((_S22))));

#line 1799
                            if(_S114)
                            {

#line 1799
                                t_3[11U] = partner_55;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[15U] = partner_55;

#line 1799
                            }

#line 1799
                            bool _S123 = (_S95 & 8U) != 0U;

#line 1799
                            uint _S124;

#line 1799
                            if(_S123)
                            {

#line 1799
                                _S124 = t_3[0U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S124 = t_3[8U];

#line 1799
                            }

#line 1799
                            uint partner_56 = (simd_shuffle_xor((_S124), ushort((_S23))));

#line 1799
                            if(_S123)
                            {

#line 1799
                                t_3[0U] = partner_56;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[8U] = partner_56;

#line 1799
                            }

#line 1799
                            uint _S125;

#line 1799
                            if(_S123)
                            {

#line 1799
                                _S125 = t_3[1U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S125 = t_3[9U];

#line 1799
                            }

#line 1799
                            uint partner_57 = (simd_shuffle_xor((_S125), ushort((_S23))));

#line 1799
                            if(_S123)
                            {

#line 1799
                                t_3[1U] = partner_57;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[9U] = partner_57;

#line 1799
                            }

#line 1799
                            uint _S126;

#line 1799
                            if(_S123)
                            {

#line 1799
                                _S126 = t_3[2U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S126 = t_3[10U];

#line 1799
                            }

#line 1799
                            uint partner_58 = (simd_shuffle_xor((_S126), ushort((_S23))));

#line 1799
                            if(_S123)
                            {

#line 1799
                                t_3[2U] = partner_58;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[10U] = partner_58;

#line 1799
                            }

#line 1799
                            uint _S127;

#line 1799
                            if(_S123)
                            {

#line 1799
                                _S127 = t_3[3U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S127 = t_3[11U];

#line 1799
                            }

#line 1799
                            uint partner_59 = (simd_shuffle_xor((_S127), ushort((_S23))));

#line 1799
                            if(_S123)
                            {

#line 1799
                                t_3[3U] = partner_59;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[11U] = partner_59;

#line 1799
                            }

#line 1799
                            uint _S128;

#line 1799
                            if(_S123)
                            {

#line 1799
                                _S128 = t_3[4U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S128 = t_3[12U];

#line 1799
                            }

#line 1799
                            uint partner_60 = (simd_shuffle_xor((_S128), ushort((_S23))));

#line 1799
                            if(_S123)
                            {

#line 1799
                                t_3[4U] = partner_60;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[12U] = partner_60;

#line 1799
                            }

#line 1799
                            uint _S129;

#line 1799
                            if(_S123)
                            {

#line 1799
                                _S129 = t_3[5U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S129 = t_3[13U];

#line 1799
                            }

#line 1799
                            uint partner_61 = (simd_shuffle_xor((_S129), ushort((_S23))));

#line 1799
                            if(_S123)
                            {

#line 1799
                                t_3[5U] = partner_61;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[13U] = partner_61;

#line 1799
                            }

#line 1799
                            uint _S130;

#line 1799
                            if(_S123)
                            {

#line 1799
                                _S130 = t_3[6U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S130 = t_3[14U];

#line 1799
                            }

#line 1799
                            uint partner_62 = (simd_shuffle_xor((_S130), ushort((_S23))));

#line 1799
                            if(_S123)
                            {

#line 1799
                                t_3[6U] = partner_62;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[14U] = partner_62;

#line 1799
                            }

#line 1799
                            uint _S131;

#line 1799
                            if(_S123)
                            {

#line 1799
                                _S131 = t_3[7U];

#line 1799
                            }
                            else
                            {

#line 1799
                                _S131 = t_3[15U];

#line 1799
                            }

#line 1799
                            uint partner_63 = (simd_shuffle_xor((_S131), ushort((_S23))));

#line 1799
                            if(_S123)
                            {

#line 1799
                                t_3[7U] = partner_63;

#line 1799
                            }
                            else
                            {

#line 1799
                                t_3[15U] = partner_63;

#line 1799
                            }

#line 1799
                            uint i_6 = 0U;

#line 1799
                            for(;;)
                            {

#line 1799
                                if(i_6 < 16U)
                                {
                                }
                                else
                                {

#line 1799
                                    break;
                                }

#line 1799
                                im_6[i_6] = half2(as_type<half>(ushort((t_3[i_6]) & 65535U)), as_type<half>(ushort(((t_3[i_6]) >> 16U) & 65535U)));

#line 1799
                                i_6 = i_6 + 1U;

#line 1799
                            }

#line 1799
                            break;
                        }

#line 1799
                        break;
                    }

#line 1799
                    break;
                }

#line 1799
                innermostS_0(&re_6, &im_6);

#line 1799
                uint i_7;

#line 1799
                bool infA_0;

#line 1799
                bool infB_0;

#line 1799
                bool hitA_0;

#line 1799
                bool hitB_0;

#line 1799
                half2 best_0;

#line 1799
                half2 en_0;

#line 1799
                int _S132;

#line 1799
                float2 _S133;

#line 1799
                if(_S29 != 0U)
                {

#line 1799
                    float _S134 = (as_type<float>((_S29)));

#line 1799
                    for(;;)
                    {

#line 1799
                        uint _S135 = slotToIndex_0(_t_0 * 16U) - _S41;

#line 1799
                        uint _S136 = _S42 - _S41;

#line 1799
                        half2 _S137 = half2(float2(0.0f) );

#line 1799
                        half2 _S138 = half2(float2(0.015625f) );

#line 1799
                        i_7 = 0U;

#line 1799
                        best_0 = _S137;

#line 1799
                        en_0 = _S137;

#line 1799
                        for(;;)
                        {

#line 1799
                            if(i_7 < 16U)
                            {
                            }
                            else
                            {

#line 1799
                                break;
                            }

#line 1799
                            half2 _S139;

#line 1799
                            if((_S135 + slotToIndex_0(i_7)) < _S136)
                            {

#line 1799
                                _S139 = mag2s_0(re_6[i_7], im_6[i_7]);

#line 1799
                            }
                            else
                            {

#line 1799
                                _S139 = _S137;

#line 1799
                            }

#line 1799
                            half2 _S140 = max(best_0, _S139);

#line 1799
                            half2 sr_0 = re_6[i_7] * _S138;

#line 1799
                            half2 si_0 = im_6[i_7] * _S138;

#line 1799
                            half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1799
                            i_7 = i_7 + 1U;

#line 1799
                            best_0 = _S140;

#line 1799
                            en_0 = en_1;

#line 1799
                        }

#line 1799
                        uint _S141 = (simd_shuffle_xor(((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U)), ushort((1U))));

#line 1799
                        half2 _S142 = max(best_0, half2(as_type<half>(ushort(_S141 & 65535U)), as_type<half>(ushort((_S141 >> 16U) & 65535U))));

#line 1799
                        uint _S143 = (simd_shuffle_xor(((uint(as_type<ushort>(en_0[0U])) & 65535U) | (uint(as_type<ushort>(en_0[1U])) << 16U)), ushort((1U))));

#line 1799
                        half2 en_2 = en_0 + half2(as_type<half>(ushort(_S143 & 65535U)), as_type<half>(ushort((_S143 >> 16U) & 65535U)));

#line 1799
                        uint _S144 = (simd_shuffle_xor(((uint(as_type<ushort>(_S142[0U])) & 65535U) | (uint(as_type<ushort>(_S142[1U])) << 16U)), ushort((2U))));

#line 1799
                        half2 _S145 = max(_S142, half2(as_type<half>(ushort(_S144 & 65535U)), as_type<half>(ushort((_S144 >> 16U) & 65535U))));

#line 1799
                        uint _S146 = (simd_shuffle_xor(((uint(as_type<ushort>(en_2[0U])) & 65535U) | (uint(as_type<ushort>(en_2[1U])) << 16U)), ushort((2U))));

#line 1799
                        half2 en_3 = en_2 + half2(as_type<half>(ushort(_S146 & 65535U)), as_type<half>(ushort((_S146 >> 16U) & 65535U)));

#line 1799
                        uint _S147 = (simd_shuffle_xor(((uint(as_type<ushort>(_S145[0U])) & 65535U) | (uint(as_type<ushort>(_S145[1U])) << 16U)), ushort((4U))));

#line 1799
                        half2 _S148 = max(_S145, half2(as_type<half>(ushort(_S147 & 65535U)), as_type<half>(ushort((_S147 >> 16U) & 65535U))));

#line 1799
                        uint _S149 = (simd_shuffle_xor(((uint(as_type<ushort>(en_3[0U])) & 65535U) | (uint(as_type<ushort>(en_3[1U])) << 16U)), ushort((4U))));

#line 1799
                        half2 en_4 = en_3 + half2(as_type<half>(ushort(_S149 & 65535U)), as_type<half>(ushort((_S149 >> 16U) & 65535U)));

#line 1799
                        uint _S150 = (simd_shuffle_xor(((uint(as_type<ushort>(_S148[0U])) & 65535U) | (uint(as_type<ushort>(_S148[1U])) << 16U)), ushort((8U))));

#line 1799
                        half2 best_1 = max(_S148, half2(as_type<half>(ushort(_S150 & 65535U)), as_type<half>(ushort((_S150 >> 16U) & 65535U))));

#line 1799
                        uint _S151 = (simd_shuffle_xor(((uint(as_type<ushort>(en_4[0U])) & 65535U) | (uint(as_type<ushort>(en_4[1U])) << 16U)), ushort((8U))));

#line 1799
                        half2 en_5 = en_4 + half2(as_type<half>(ushort(_S151 & 65535U)), as_type<half>(ushort((_S151 >> 16U) & 65535U)));

#line 1799
                        uint _S152 = (uint(as_type<ushort>(en_5[0U])) & 65535U) | (uint(as_type<ushort>(en_5[1U])) << 16U);

#line 1799
                        uint _S153 = (uint(as_type<ushort>(best_1[0U])) & 65535U) | (uint(as_type<ushort>(best_1[1U])) << 16U);

#line 1799
                        if((_S152 & 31744U) == 31744U)
                        {

#line 1799
                            infA_0 = true;

#line 1799
                        }
                        else
                        {

#line 1799
                            infA_0 = (_S153 & 31744U) == 31744U;

#line 1799
                        }

#line 1799
                        if((_S152 & 2080374784U) == 2080374784U)
                        {

#line 1799
                            infB_0 = true;

#line 1799
                        }
                        else
                        {

#line 1799
                            infB_0 = (_S153 & 2080374784U) == 2080374784U;

#line 1799
                        }

#line 1799
                        float bA_0 = sqrt(float(best_1.x));

#line 1799
                        float bB_0 = sqrt(float(best_1.y));

#line 1799
                        if(infA_0)
                        {

#line 1799
                            hitA_0 = true;

#line 1799
                        }
                        else
                        {

#line 1799
                            if(bA_0 > 0.0f)
                            {

#line 1799
                                hitA_0 = bA_0 >= _S134;

#line 1799
                            }
                            else
                            {

#line 1799
                                hitA_0 = false;

#line 1799
                            }

#line 1799
                        }

#line 1799
                        if(infB_0)
                        {

#line 1799
                            hitB_0 = true;

#line 1799
                        }
                        else
                        {

#line 1799
                            if(bB_0 > 0.0f)
                            {

#line 1799
                                hitB_0 = bB_0 >= _S134;

#line 1799
                            }
                            else
                            {

#line 1799
                                hitB_0 = false;

#line 1799
                            }

#line 1799
                        }

#line 1799
                        bool _S154 = _t_0 == 0U;

#line 1799
                        bool _S155;

#line 1799
                        if(_S154)
                        {

#line 1799
                            _S155 = q_1 != 4294967295U;

#line 1799
                        }
                        else
                        {

#line 1799
                            _S155 = false;

#line 1799
                        }

#line 1799
                        if(_S155)
                        {

#line 1799
                            int device* _S156 = (&kernelContext_1)->entryPointParams_peakIdx_0+q_1;

#line 1799
                            if(hitA_0)
                            {

#line 1799
                                _S132 = int(0);

#line 1799
                            }
                            else
                            {

#line 1799
                                _S132 = int(-1);

#line 1799
                            }

#line 1799
                            *_S156 = _S132;

#line 1799
                            packed_float2 device* _S157 = (&kernelContext_1)->entryPointParams_peakVal_0+q_1;

#line 1799
                            if(infA_0)
                            {

#line 1799
                                _S133 = float2(3.40282306073709653e+38f, 0.0f);

#line 1799
                            }
                            else
                            {

#line 1799
                                if(hitA_0)
                                {

#line 1799
                                    _S133 = float2(bA_0, 0.0f);

#line 1799
                                }
                                else
                                {

#line 1799
                                    _S133 = float2(0.0f, 0.0f);

#line 1799
                                }

#line 1799
                            }

#line 1799
                            *_S157 = packed_float2(_S133) ;

#line 1799
                        }

#line 1799
                        bool _S158;

#line 1799
                        if(_S154)
                        {

#line 1799
                            _S158 = n2_0 != 4294967295U;

#line 1799
                        }
                        else
                        {

#line 1799
                            _S158 = false;

#line 1799
                        }

#line 1799
                        if(_S158)
                        {

#line 1799
                            int device* _S159 = (&kernelContext_1)->entryPointParams_peakIdx_0+n2_0;

#line 1799
                            if(hitB_0)
                            {

#line 1799
                                _S132 = int(0);

#line 1799
                            }
                            else
                            {

#line 1799
                                _S132 = int(-1);

#line 1799
                            }

#line 1799
                            *_S159 = _S132;

#line 1799
                            packed_float2 device* _S160 = (&kernelContext_1)->entryPointParams_peakVal_0+n2_0;

#line 1799
                            if(infB_0)
                            {

#line 1799
                                _S133 = float2(3.40282306073709653e+38f, 0.0f);

#line 1799
                            }
                            else
                            {

#line 1799
                                if(hitB_0)
                                {

#line 1799
                                    _S133 = float2(bB_0, 0.0f);

#line 1799
                                }
                                else
                                {

#line 1799
                                    _S133 = float2(0.0f, 0.0f);

#line 1799
                                }

#line 1799
                            }

#line 1799
                            *_S160 = packed_float2(_S133) ;

#line 1799
                        }

#line 1799
                        break;
                    }

#line 1799
                }
                else
                {

#line 1799
                    array<half2, int(16)> _S161 = re_6;

#line 1799
                    array<half2, int(16)> _S162 = im_6;

#line 1799
                    for(;;)
                    {

#line 1799
                        uint _S163 = slotToIndex_0(_t_0 * 16U) - _S41;

#line 1799
                        uint _S164 = _S42 - _S41;

#line 1799
                        i_7 = 0U;

#line 1799
                        uint ovAcc_0 = 0U;

#line 1799
                        uint kA_0 = 0U;

#line 1799
                        uint kB_0 = 0U;

#line 1799
                        for(;;)
                        {

#line 1799
                            if(i_7 < 16U)
                            {
                            }
                            else
                            {

#line 1799
                                break;
                            }

#line 1799
                            uint _S165 = i_7;

#line 1799
                            uint _S166 = i_7;

#line 1799
                            half2 mg_0 = mag2s_0(_S161[i_7], _S162[i_7]);

#line 1799
                            if((_S163 + slotToIndex_0(i_7)) < _S164)
                            {

#line 1799
                                m_0 = (uint(as_type<ushort>(mg_0[0U])) & 65535U) | (uint(as_type<ushort>(mg_0[1U])) << 16U);

#line 1799
                            }
                            else
                            {

#line 1799
                                m_0 = 0U;

#line 1799
                            }

#line 1799
                            uint ovAcc_1 = ovAcc_0 | (((((uint(as_type<ushort>(_S161[_S165][0U])) & 65535U) | (uint(as_type<ushort>(_S161[_S165][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(_S162[_S166][0U])) & 65535U) | (uint(as_type<ushort>(_S162[_S166][1U])) << 16U)) & 2080406528U) + 67109888U));

#line 1799
                            uint _S167 = 15U - i_7;

#line 1799
                            uint _S168 = max(kA_0, (m_0 << 16U) | _S167);

#line 1799
                            uint _S169 = max(kB_0, (m_0 & 4294901760U) | _S167);

#line 1799
                            i_7 = i_7 + 1U;

#line 1799
                            ovAcc_0 = ovAcc_1;

#line 1799
                            kA_0 = _S168;

#line 1799
                            kB_0 = _S169;

#line 1799
                        }

#line 1799
                        if((ovAcc_0 & 32768U) != 0U)
                        {

#line 1799
                            m_0 = max(kA_0, 2080374799U);

#line 1799
                        }
                        else
                        {

#line 1799
                            m_0 = kA_0;

#line 1799
                        }

#line 1799
                        uint kB_1;

#line 1799
                        if((ovAcc_0 & 2147483648U) != 0U)
                        {

#line 1799
                            kB_1 = max(kB_0, 2080374799U);

#line 1799
                        }
                        else
                        {

#line 1799
                            kB_1 = kB_0;

#line 1799
                        }

#line 1799
                        uint _S170 = (4095U - _t_0) << 4U;

#line 1799
                        uint kA_1 = m_0 | _S170;

#line 1799
                        uint kB_2 = kB_1 | _S170;

#line 1799
                        uint _S171 = (simd_shuffle_xor((kA_1), ushort((1U))));

#line 1799
                        uint _S172 = max(kA_1, _S171);

#line 1799
                        uint _S173 = (simd_shuffle_xor((kB_2), ushort((1U))));

#line 1799
                        uint _S174 = max(kB_2, _S173);

#line 1799
                        uint _S175 = (simd_shuffle_xor((_S172), ushort((2U))));

#line 1799
                        uint _S176 = max(_S172, _S175);

#line 1799
                        uint _S177 = (simd_shuffle_xor((_S174), ushort((2U))));

#line 1799
                        uint _S178 = max(_S174, _S177);

#line 1799
                        uint _S179 = (simd_shuffle_xor((_S176), ushort((4U))));

#line 1799
                        uint _S180 = max(_S176, _S179);

#line 1799
                        uint _S181 = (simd_shuffle_xor((_S178), ushort((4U))));

#line 1799
                        uint _S182 = max(_S178, _S181);

#line 1799
                        uint _S183 = (simd_shuffle_xor((_S180), ushort((8U))));

#line 1799
                        uint _S184 = max(_S180, _S183);

#line 1799
                        uint _S185 = (simd_shuffle_xor((_S182), ushort((8U))));

#line 1799
                        uint _S186 = max(_S182, _S185);

#line 1799
                        uint slotA_0 = 65535U - (_S184 & 65535U);

#line 1799
                        uint slotB_0 = 65535U - (_S186 & 65535U);

#line 1799
                        uint _S187 = _S184 >> 16U;

#line 1799
                        bool infA_1 = _S187 >= 31744U;

#line 1799
                        uint _S188 = _S186 >> 16U;

#line 1799
                        bool infB_1 = _S188 >= 31744U;

#line 1799
                        if(infA_1)
                        {

#line 1799
                            infA_0 = true;

#line 1799
                        }
                        else
                        {

#line 1799
                            infA_0 = (as_type<half>((ushort)((_S187)))) > (as_type<float>((_S29)));

#line 1799
                        }

#line 1799
                        if(infB_1)
                        {

#line 1799
                            infB_0 = true;

#line 1799
                        }
                        else
                        {

#line 1799
                            infB_0 = (as_type<half>((ushort)((_S188)))) > (as_type<float>((_S29)));

#line 1799
                        }

#line 1799
                        uint wA_0 = slotA_0 >> 4U;

#line 1799
                        uint _S189 = slotA_0 & 15U;

#line 1799
                        uint wB_0 = slotB_0 >> 4U;

#line 1799
                        uint _S190 = slotB_0 & 15U;

#line 1799
                        half2 _S191 = half2(float2(0.0f) );

#line 1799
                        uint j_0 = 0U;

#line 1799
                        best_0 = _S191;

#line 1799
                        en_0 = _S191;

#line 1799
                        for(;;)
                        {

#line 1799
                            if(j_0 < 16U)
                            {
                            }
                            else
                            {

#line 1799
                                break;
                            }

#line 1799
                            if(j_0 == _S189)
                            {

#line 1799
                                best_0 = half2(_S161[j_0].x, _S162[j_0].x);

#line 1799
                            }

#line 1799
                            if(j_0 == _S190)
                            {

#line 1799
                                en_0 = half2(_S161[j_0].y, _S162[j_0].y);

#line 1799
                            }

#line 1799
                            j_0 = j_0 + 1U;

#line 1799
                        }

#line 1799
                        uint _S192 = (simd_shuffle_xor(((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U)), ushort((wA_0))));

#line 1799
                        half _S193 = as_type<half>(ushort(_S192 & 65535U));

#line 1799
                        half _S194 = as_type<half>(ushort((_S192 >> 16U) & 65535U));

#line 1799
                        uint _S195 = (simd_shuffle_xor(((uint(as_type<ushort>(en_0[0U])) & 65535U) | (uint(as_type<ushort>(en_0[1U])) << 16U)), ushort((wB_0))));

#line 1799
                        half _S196 = as_type<half>(ushort(_S195 & 65535U));

#line 1799
                        half _S197 = as_type<half>(ushort((_S195 >> 16U) & 65535U));

#line 1799
                        bool _S198 = _t_0 == 0U;

#line 1799
                        if(_S198)
                        {

#line 1799
                            hitA_0 = q_1 != 4294967295U;

#line 1799
                        }
                        else
                        {

#line 1799
                            hitA_0 = false;

#line 1799
                        }

#line 1799
                        if(hitA_0)
                        {

#line 1799
                            int device* _S199 = (&kernelContext_1)->entryPointParams_peakIdx_0+q_1;

#line 1799
                            if(infA_0)
                            {

#line 1799
                                _S132 = int(slotToIndex_0(slotA_0));

#line 1799
                            }
                            else
                            {

#line 1799
                                _S132 = int(-1);

#line 1799
                            }

#line 1799
                            *_S199 = _S132;

#line 1799
                            packed_float2 device* _S200 = (&kernelContext_1)->entryPointParams_peakVal_0+q_1;

#line 1799
                            if(infA_1)
                            {

#line 1799
                                _S133 = float2(3.40282306073709653e+38f, 0.0f);

#line 1799
                            }
                            else
                            {

#line 1799
                                if(infA_0)
                                {

#line 1799
                                    _S133 = float2(float(_S193), float(_S194));

#line 1799
                                }
                                else
                                {

#line 1799
                                    _S133 = float2(0.0f, 0.0f);

#line 1799
                                }

#line 1799
                            }

#line 1799
                            *_S200 = packed_float2(_S133) ;

#line 1799
                        }

#line 1799
                        if(_S198)
                        {

#line 1799
                            hitB_0 = n2_0 != 4294967295U;

#line 1799
                        }
                        else
                        {

#line 1799
                            hitB_0 = false;

#line 1799
                        }

#line 1799
                        if(hitB_0)
                        {

#line 1799
                            int device* _S201 = (&kernelContext_1)->entryPointParams_peakIdx_0+n2_0;

#line 1799
                            if(infB_0)
                            {

#line 1799
                                _S132 = int(slotToIndex_0(slotB_0));

#line 1799
                            }
                            else
                            {

#line 1799
                                _S132 = int(-1);

#line 1799
                            }

#line 1799
                            *_S201 = _S132;

#line 1799
                            packed_float2 device* _S202 = (&kernelContext_1)->entryPointParams_peakVal_0+n2_0;

#line 1799
                            if(infB_1)
                            {

#line 1799
                                _S133 = float2(3.40282306073709653e+38f, 0.0f);

#line 1799
                            }
                            else
                            {

#line 1799
                                if(infB_0)
                                {

#line 1799
                                    _S133 = float2(float(_S196), float(_S197));

#line 1799
                                }
                                else
                                {

#line 1799
                                    _S133 = float2(0.0f, 0.0f);

#line 1799
                                }

#line 1799
                            }

#line 1799
                            *_S202 = packed_float2(_S133) ;

#line 1799
                        }

#line 1799
                        break;
                    }

#line 1799
                }

#line 1799
                break;
            }

#line 1799
            k_0 = k_0 + 2U;

#line 1799
        }

#line 1799
        break;
    }

    return;
}
