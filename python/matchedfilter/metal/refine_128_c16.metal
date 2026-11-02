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

#line 10 "mm_128_refineListed_c16.slang"
constant array<uint, int(128)> COARSE_TWT_DATA_0 = { { 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 709377022U, 776354806U, 816987114U, 842939353U, 868629443U, 883243944U, 895761288U, 908016484U, 920075067U, 931871502U, 941439709U, 947010215U, 952384109U, 957561391U, 962542061U, 15360U, 776354806U, 842939353U, 883243944U, 908016484U, 931871502U, 947010215U, 957561391U, 967326120U, 976173331U, 984037490U, 990787467U, 996423199U, 1000879269U, 1004089918U, 1005989446U, 15360U, 816987114U, 883243944U, 920075067U, 947010215U, 962542061U, 976173331U, 987576349U, 996423199U, 1002648518U, 1005989446U, 1006545480U, 1004122686U, 998815076U, 990820235U, 980269252U, 15360U, 842939353U, 908016484U, 947010215U, 967326120U, 984037490U, 996423199U, 1004089918U, 1006632960U, 1004122686U, 996455967U, 984070258U, 967358888U, 947042983U, 908049252U, 842972121U, 15360U, 868629443U, 931871502U, 962542061U, 984037490U, 998782308U, 1005989446U, 1005236402U, 996455967U, 980269252U, 957594159U, 920107835U, 842972121U, 2856893438U, 3030760360U, 3088956125U, 15360U, 883243944U, 947010215U, 976173331U, 996423199U, 1005989446U, 1004122686U, 990820235U, 967358888U, 931904270U, 842972121U, 2923871222U, 3055532900U, 3105077807U, 3131553906U, 3148395685U, 15360U, 895761288U, 957561391U, 987576349U, 1004089918U, 1005236402U, 990820235U, 962574829U, 908049252U, 709409790U, 3030760360U, 3099900525U, 3131553906U, 3150164934U, 3153473094U, 3141220055U } };

#line 87 "twiddle.slang"
uint mfRowWindowsFlag_0()
{
    ;
    uint _S1 = ((MF_ROW_WINDOWS));

#line 90
    return _S1;
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


#line 323 "mm_128_refineListed_c16.slang"
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
    uint _S2 = mfRowWindowsFlag_0();

#line 233 "mm_128_refineListed_c16.slang"
    if(_S2 == 0U)
    {

#line 233
        return;
    }

#line 234
    uint _S3 = 3U * d_0;

#line 234
    *winStart_1 = rowWin_0[_S3];
    *winEnd_1 = rowWin_0[_S3 + 1U];
    kernelContext_0->_binPhase_0 = rowWin_0[_S3 + 2U];
    return;
}


#line 60 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S4 = ((MF_DATA_STRIDE));

#line 63
    return _S4;
}



uint mfDataScaleFlag_0()
{
    ;
    uint _S5 = ((MF_DATA_SCALE_BITS));

#line 71
    return _S5;
}


#line 172 "mm_128_refineListed_c16.slang"
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
    uint _S6 = mfDataStrideFlag_0();

#line 266 "mm_128_refineListed_c16.slang"
    if(_S6 != 0U)
    {

#line 73 "twiddle.slang"
        uint _S7 = mfDataScaleFlag_0();

#line 267 "mm_128_refineListed_c16.slang"
        float s_0 = (as_type<float>((_S7)));
        uint _S8 = 2U * i_1;

#line 268
        return half2(half((as_type<float>((b_1[_S8]))) * s_0), half((as_type<float>((b_1[_S8 + 1U]))) * s_0));
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
    half2 _S9 = half2(wr_0) ;

#line 391
    half2 _S10 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S10 + *xi_0 * _S9;
    *xr_0 = *xr_0 * _S9 - *xi_0 * _S10;

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
        uint _S11 = 4U * k2_0;

#line 478
        r4s_0(re_2, im_2, _S11, _S11 + 1U, _S11 + 2U, _S11 + 3U);

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
    uint _S12 = ((MF_COARSE_TWT));

#line 52
    return _S12;
}


#line 76
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S13 = ((MF_ACCURATE_TRIG));

#line 79
    return _S13;
}


#line 103
float2 mfTwiddle_0(float angle_0)
{

#line 81
    uint _S14 = mfAccurateTrigFlag_0();

#line 105
    if(_S14 == 0U)
    {

#line 106
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S15 = float(quadrant_0);
    float x_0 = angle_0 - _S15 * 1.57079625129699707f - _S15 * 7.54978941586159635e-08f;
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


#line 445 "mm_128_refineListed_c16.slang"
void dft8s_0(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint o_0)
{
    thread array<half2, int(8)> br_1;

#line 447
    thread array<half2, int(8)> bi_1;

#line 447
    uint s_2 = 1U;
    for(;;)
    {

#line 448
        if(s_2 < 8U)
        {
        }
        else
        {

#line 448
            break;
        }

#line 448
        uint j_0 = 0U;
        for(;;)
        {

#line 449
            if(j_0 < 4U)
            {
            }
            else
            {

#line 449
                break;
            }

#line 450
            uint k_0 = j_0 & (s_2 - 1U);

#line 450
            uint base_0 = (j_0 - k_0) << 1U;
            float ang_0 = 3.14159274101257324f * float(k_0) / float(s_2);
            uint _S16 = o_0 + j_0;

#line 452
            uint _S17 = _S16 + 4U;

#line 452
            thread half2 vr_0 = (*re_3)[_S17];

#line 452
            thread half2 vi_0 = (*im_3)[_S17];
            float2 tw_0 = mfTwiddle_0(ang_0);
            cmulw_0(&vr_0, &vi_0, half(tw_0.x), half(tw_0.y));

            uint _S18 = base_0 + k_0;

#line 456
            br_1[_S18] = (*re_3)[_S16] + vr_0;

#line 456
            bi_1[_S18] = (*im_3)[_S16] + vi_0;
            uint _S19 = _S18 + s_2;

#line 457
            br_1[_S19] = (*re_3)[_S16] - vr_0;

#line 457
            bi_1[_S19] = (*im_3)[_S16] - vi_0;

#line 449
            j_0 = j_0 + 1U;

#line 449
        }

#line 449
        uint i_2 = 0U;

#line 459
        for(;;)
        {

#line 459
            if(i_2 < 8U)
            {
            }
            else
            {

#line 459
                break;
            }

#line 459
            uint _S20 = o_0 + i_2;

#line 459
            (*re_3)[_S20] = br_1[i_2];

#line 459
            (*im_3)[_S20] = bi_1[i_2];

#line 459
            i_2 = i_2 + 1U;

#line 459
        }

#line 448
        s_2 = s_2 << 1U;

#line 448
    }

#line 461
    return;
}


#line 607
void innermostS_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4)
{

#line 607
    uint b_3 = 0U;


    for(;;)
    {

#line 610
        if(b_3 < 2U)
        {
        }
        else
        {

#line 610
            break;
        }

#line 610
        dft8s_0(re_4, im_4, b_3 * 8U);

#line 610
        b_3 = b_3 + 1U;

#line 610
    }


    return;
}


#line 883
uint lgOf_0(uint i_3)
{

#line 883
    uint _S21;

#line 883
    if(i_3 < 1U)
    {

#line 883
        _S21 = 4U;

#line 883
    }
    else
    {

#line 883
        if(i_3 == 1U)
        {

#line 883
            _S21 = 3U;

#line 883
        }
        else
        {

#line 883
            _S21 = 1U;

#line 883
        }

#line 883
    }

#line 883
    return _S21;
}


#line 885
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 889
    uint lg_1 = lgOf_0(0U);

#line 894
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
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
    uint j_1;

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
    uint _S22 = lid_0.x;

#line 2367
    uint sub_0 = _S22 / 8U;

#line 2367
    uint _S23 = _S22 % 8U;
    (&kernelContext_1)->_stgBase_0 = sub_0 * 128U;

#line 2368
    uint base_1 = gid_0.x * 16U;

    for(;;)
    {

#line 2370
        if(base_1 < total_0)
        {
        }
        else
        {

#line 2370
            break;
        }

#line 2371
        uint idxA_0 = base_1 + 2U * sub_0;
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
        bool _S24 = pairA_0 != 4294967295U;

#line 2375
        uint refPairA_0;

#line 2375
        if(_S24)
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
        bool _S25 = pairB_0 != 4294967295U;

#line 2376
        uint refPairB_0;

#line 2376
        if(_S25)
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


        uint _S26 = wsA_0;

#line 2382
        uint _S27 = weA_0;

#line 2382
        uint _S28 = wsB_0;

#line 2382
        uint _S29 = weB_0;

#line 2382
        uint _S30 = (&kernelContext_1)->entryPointParams_0->nbins_0;

#line 2382
        uint _S31 = (&kernelContext_1)->entryPointParams_0->thrBits_0;

#line 2382
        for(;;)
        {

#line 2382
            thread array<half2, int(16)> re_6;

#line 2382
            thread array<half2, int(16)> im_6;

#line 2382
            uint _S32 = mfDataStrideFlag_0();

#line 2382
            uint _S33;

#line 2382
            if(_S32 != 0U)
            {

#line 2382
                uint _S34 = mfDataStrideFlag_0();

#line 2382
                _S33 = _S34;

#line 2382
            }
            else
            {

#line 2382
                _S33 = 128U;

#line 2382
            }

#line 2382
            bool _S35 = dB_0 == dA_0;

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
                uint k_1 = _S23 + 8U * n2_0;

#line 2382
                half2 da_0 = dload_0((&kernelContext_1)->entryPointParams_data_0, dA_0 * _S33 + k_1);

#line 2382
                if(_S35)
                {

#line 2382
                    db_0 = da_0;

#line 2382
                }
                else
                {

#line 2382
                    half2 _S36 = dload_0((&kernelContext_1)->entryPointParams_data_0, dB_0 * _S33 + k_1);

#line 2382
                    db_0 = _S36;

#line 2382
                }

#line 2382
                half2 ta_0 = cload_0((&kernelContext_1)->entryPointParams_tmpl_0, tA_0 * 128U + k_1);

#line 2382
                half2 tb_0 = cload_0((&kernelContext_1)->entryPointParams_tmpl_0, tB_0 * 128U + k_1);

#line 2382
                cmulconjs_0(half2(da_0.x, db_0.x), half2(da_0.y, db_0.y), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_6[n2_0], &im_6[n2_0]);

#line 2382
                n2_0 = n2_0 + 1U;

#line 2382
            }

#line 2382
            array<half2, int(16)> _S37 = re_6;

#line 2382
            array<half2, int(16)> _S38 = im_6;

#line 2382
            for(;;)
            {

#line 2382
                thread array<half2, int(16)> _S39 = _S37;

#line 2382
                thread array<half2, int(16)> _S40 = _S38;

#line 2382
                (&kernelContext_1)->_tid_0 = _S23;

#line 2382
                for(;;)
                {

#line 2382
                    uint lane_0 = _S23 & 7U;

#line 2382
                    dft16s_0(&_S39, &_S40);

#line 2382
                    uint _S41 = mfCoarseTwtFlag_0();

#line 2382
                    uint r_0;

#line 2382
                    if(_S41 != 0U)
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
                            uint _S42 = lane_0 * 16U + r_0;

#line 2382
                            cmulw_0(&_S39[r_0], &_S40[r_0], as_type<half>(ushort((COARSE_TWT_DATA_0[_S42]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S42]) >> 16U) & 65535U)));

#line 2382
                            r_0 = r_0 + 1U;

#line 2382
                        }

#line 2382
                    }
                    else
                    {

#line 2382
                        float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_0) / 128.0f);

#line 2382
                        float _S43 = tw_1.x;

#line 2382
                        float _S44 = tw_1.y;

#line 2382
                        r_0 = 0U;

#line 2382
                        float cr_0 = 1.0f;

#line 2382
                        float ci_0 = 0.0f;

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
                            cmulw_0(&_S39[r_0], &_S40[r_0], half(cr_0), half(ci_0));

#line 2382
                            float nr_0 = cr_0 * _S43 - ci_0 * _S44;

#line 2382
                            float _S45 = cr_0 * _S44 + ci_0 * _S43;

#line 2382
                            r_0 = r_0 + 1U;

#line 2382
                            cr_0 = nr_0;

#line 2382
                            ci_0 = _S45;

#line 2382
                        }

#line 2382
                    }

#line 2382
                    uint per_0 = 16U / max(8U, 1U);

#line 2382
                    uint _S46 = max(0U, 1U);

#line 2382
                    uint blk2_0 = _S23 / _S46;

#line 2382
                    uint lane2_0 = _S23 % _S46;

#line 2382
                    for(;;)
                    {

#line 2382
                        uint _S47 = (&kernelContext_1)->_tid_0;

#line 2382
                        for(;;)
                        {

#line 2382
                            thread array<uint, int(16)> t_2;

#line 2382
                            r_0 = 0U;

#line 2382
                            for(;;)
                            {

#line 2382
                                if(r_0 < 8U)
                                {
                                }
                                else
                                {

#line 2382
                                    break;
                                }

#line 2382
                                j_1 = 0U;

#line 2382
                                for(;;)
                                {

#line 2382
                                    if(j_1 < 2U)
                                    {
                                    }
                                    else
                                    {

#line 2382
                                        break;
                                    }

#line 2382
                                    t_2[j_1 * 8U + r_0] = (uint(as_type<ushort>(_S39[r_0 * 2U + j_1][0U])) & 65535U) | (uint(as_type<ushort>(_S39[r_0 * 2U + j_1][1U])) << 16U);

#line 2382
                                    j_1 = j_1 + 1U;

#line 2382
                                }

#line 2382
                                r_0 = r_0 + 1U;

#line 2382
                            }

#line 2382
                            uint _S48 = _S47 & 7U;

#line 2382
                            bool _S49 = (_S48 & 1U) != 0U;

#line 2382
                            uint _S50;

#line 2382
                            if(_S49)
                            {

#line 2382
                                _S50 = t_2[0U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S50 = t_2[1U];

#line 2382
                            }

#line 2382
                            uint partner_0 = (simd_shuffle_xor((_S50), ushort((1U))));

#line 2382
                            if(_S49)
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
                            uint _S51;

#line 2382
                            if(_S49)
                            {

#line 2382
                                _S51 = t_2[2U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S51 = t_2[3U];

#line 2382
                            }

#line 2382
                            uint partner_1 = (simd_shuffle_xor((_S51), ushort((1U))));

#line 2382
                            if(_S49)
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
                            uint _S52;

#line 2382
                            if(_S49)
                            {

#line 2382
                                _S52 = t_2[4U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S52 = t_2[5U];

#line 2382
                            }

#line 2382
                            uint partner_2 = (simd_shuffle_xor((_S52), ushort((1U))));

#line 2382
                            if(_S49)
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
                            uint _S53;

#line 2382
                            if(_S49)
                            {

#line 2382
                                _S53 = t_2[6U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S53 = t_2[7U];

#line 2382
                            }

#line 2382
                            uint partner_3 = (simd_shuffle_xor((_S53), ushort((1U))));

#line 2382
                            if(_S49)
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
                            uint _S54;

#line 2382
                            if(_S49)
                            {

#line 2382
                                _S54 = t_2[8U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S54 = t_2[9U];

#line 2382
                            }

#line 2382
                            uint partner_4 = (simd_shuffle_xor((_S54), ushort((1U))));

#line 2382
                            if(_S49)
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
                            uint _S55;

#line 2382
                            if(_S49)
                            {

#line 2382
                                _S55 = t_2[10U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S55 = t_2[11U];

#line 2382
                            }

#line 2382
                            uint partner_5 = (simd_shuffle_xor((_S55), ushort((1U))));

#line 2382
                            if(_S49)
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
                            uint _S56;

#line 2382
                            if(_S49)
                            {

#line 2382
                                _S56 = t_2[12U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S56 = t_2[13U];

#line 2382
                            }

#line 2382
                            uint partner_6 = (simd_shuffle_xor((_S56), ushort((1U))));

#line 2382
                            if(_S49)
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
                            uint _S57;

#line 2382
                            if(_S49)
                            {

#line 2382
                                _S57 = t_2[14U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S57 = t_2[15U];

#line 2382
                            }

#line 2382
                            uint partner_7 = (simd_shuffle_xor((_S57), ushort((1U))));

#line 2382
                            if(_S49)
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
                            bool _S58 = (_S48 & 2U) != 0U;

#line 2382
                            uint _S59;

#line 2382
                            if(_S58)
                            {

#line 2382
                                _S59 = t_2[0U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S59 = t_2[2U];

#line 2382
                            }

#line 2382
                            uint partner_8 = (simd_shuffle_xor((_S59), ushort((2U))));

#line 2382
                            if(_S58)
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
                            uint _S60;

#line 2382
                            if(_S58)
                            {

#line 2382
                                _S60 = t_2[1U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S60 = t_2[3U];

#line 2382
                            }

#line 2382
                            uint partner_9 = (simd_shuffle_xor((_S60), ushort((2U))));

#line 2382
                            if(_S58)
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
                            uint _S61;

#line 2382
                            if(_S58)
                            {

#line 2382
                                _S61 = t_2[4U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S61 = t_2[6U];

#line 2382
                            }

#line 2382
                            uint partner_10 = (simd_shuffle_xor((_S61), ushort((2U))));

#line 2382
                            if(_S58)
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
                            uint _S62;

#line 2382
                            if(_S58)
                            {

#line 2382
                                _S62 = t_2[5U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S62 = t_2[7U];

#line 2382
                            }

#line 2382
                            uint partner_11 = (simd_shuffle_xor((_S62), ushort((2U))));

#line 2382
                            if(_S58)
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
                            uint _S63;

#line 2382
                            if(_S58)
                            {

#line 2382
                                _S63 = t_2[8U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S63 = t_2[10U];

#line 2382
                            }

#line 2382
                            uint partner_12 = (simd_shuffle_xor((_S63), ushort((2U))));

#line 2382
                            if(_S58)
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
                            uint _S64;

#line 2382
                            if(_S58)
                            {

#line 2382
                                _S64 = t_2[9U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S64 = t_2[11U];

#line 2382
                            }

#line 2382
                            uint partner_13 = (simd_shuffle_xor((_S64), ushort((2U))));

#line 2382
                            if(_S58)
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
                            uint _S65;

#line 2382
                            if(_S58)
                            {

#line 2382
                                _S65 = t_2[12U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S65 = t_2[14U];

#line 2382
                            }

#line 2382
                            uint partner_14 = (simd_shuffle_xor((_S65), ushort((2U))));

#line 2382
                            if(_S58)
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
                            uint _S66;

#line 2382
                            if(_S58)
                            {

#line 2382
                                _S66 = t_2[13U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S66 = t_2[15U];

#line 2382
                            }

#line 2382
                            uint partner_15 = (simd_shuffle_xor((_S66), ushort((2U))));

#line 2382
                            if(_S58)
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
                            bool _S67 = (_S48 & 4U) != 0U;

#line 2382
                            uint _S68;

#line 2382
                            if(_S67)
                            {

#line 2382
                                _S68 = t_2[0U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S68 = t_2[4U];

#line 2382
                            }

#line 2382
                            uint partner_16 = (simd_shuffle_xor((_S68), ushort((4U))));

#line 2382
                            if(_S67)
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
                            uint _S69;

#line 2382
                            if(_S67)
                            {

#line 2382
                                _S69 = t_2[1U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S69 = t_2[5U];

#line 2382
                            }

#line 2382
                            uint partner_17 = (simd_shuffle_xor((_S69), ushort((4U))));

#line 2382
                            if(_S67)
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
                            uint _S70;

#line 2382
                            if(_S67)
                            {

#line 2382
                                _S70 = t_2[2U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S70 = t_2[6U];

#line 2382
                            }

#line 2382
                            uint partner_18 = (simd_shuffle_xor((_S70), ushort((4U))));

#line 2382
                            if(_S67)
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
                            uint _S71;

#line 2382
                            if(_S67)
                            {

#line 2382
                                _S71 = t_2[3U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S71 = t_2[7U];

#line 2382
                            }

#line 2382
                            uint partner_19 = (simd_shuffle_xor((_S71), ushort((4U))));

#line 2382
                            if(_S67)
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
                            uint _S72;

#line 2382
                            if(_S67)
                            {

#line 2382
                                _S72 = t_2[8U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S72 = t_2[12U];

#line 2382
                            }

#line 2382
                            uint partner_20 = (simd_shuffle_xor((_S72), ushort((4U))));

#line 2382
                            if(_S67)
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
                            uint _S73;

#line 2382
                            if(_S67)
                            {

#line 2382
                                _S73 = t_2[9U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S73 = t_2[13U];

#line 2382
                            }

#line 2382
                            uint partner_21 = (simd_shuffle_xor((_S73), ushort((4U))));

#line 2382
                            if(_S67)
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
                            uint _S74;

#line 2382
                            if(_S67)
                            {

#line 2382
                                _S74 = t_2[10U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S74 = t_2[14U];

#line 2382
                            }

#line 2382
                            uint partner_22 = (simd_shuffle_xor((_S74), ushort((4U))));

#line 2382
                            if(_S67)
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
                            uint _S75;

#line 2382
                            if(_S67)
                            {

#line 2382
                                _S75 = t_2[11U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S75 = t_2[15U];

#line 2382
                            }

#line 2382
                            uint partner_23 = (simd_shuffle_xor((_S75), ushort((4U))));

#line 2382
                            if(_S67)
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
                                _S39[i_4] = half2(as_type<half>(ushort((t_2[i_4]) & 65535U)), as_type<half>(ushort(((t_2[i_4]) >> 16U) & 65535U)));

#line 2382
                                i_4 = i_4 + 1U;

#line 2382
                            }

#line 2382
                            break;
                        }

#line 2382
                        uint _S76 = (&kernelContext_1)->_tid_0;

#line 2382
                        for(;;)
                        {

#line 2382
                            thread array<uint, int(16)> t_3;

#line 2382
                            uint r_1 = 0U;

#line 2382
                            for(;;)
                            {

#line 2382
                                if(r_1 < 8U)
                                {
                                }
                                else
                                {

#line 2382
                                    break;
                                }

#line 2382
                                j_1 = 0U;

#line 2382
                                for(;;)
                                {

#line 2382
                                    if(j_1 < 2U)
                                    {
                                    }
                                    else
                                    {

#line 2382
                                        break;
                                    }

#line 2382
                                    t_3[j_1 * 8U + r_1] = (uint(as_type<ushort>(_S40[r_1 * 2U + j_1][0U])) & 65535U) | (uint(as_type<ushort>(_S40[r_1 * 2U + j_1][1U])) << 16U);

#line 2382
                                    j_1 = j_1 + 1U;

#line 2382
                                }

#line 2382
                                r_1 = r_1 + 1U;

#line 2382
                            }

#line 2382
                            uint _S77 = _S76 & 7U;

#line 2382
                            bool _S78 = (_S77 & 1U) != 0U;

#line 2382
                            uint _S79;

#line 2382
                            if(_S78)
                            {

#line 2382
                                _S79 = t_3[0U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S79 = t_3[1U];

#line 2382
                            }

#line 2382
                            uint partner_24 = (simd_shuffle_xor((_S79), ushort((1U))));

#line 2382
                            if(_S78)
                            {

#line 2382
                                t_3[0U] = partner_24;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[1U] = partner_24;

#line 2382
                            }

#line 2382
                            uint _S80;

#line 2382
                            if(_S78)
                            {

#line 2382
                                _S80 = t_3[2U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S80 = t_3[3U];

#line 2382
                            }

#line 2382
                            uint partner_25 = (simd_shuffle_xor((_S80), ushort((1U))));

#line 2382
                            if(_S78)
                            {

#line 2382
                                t_3[2U] = partner_25;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[3U] = partner_25;

#line 2382
                            }

#line 2382
                            uint _S81;

#line 2382
                            if(_S78)
                            {

#line 2382
                                _S81 = t_3[4U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S81 = t_3[5U];

#line 2382
                            }

#line 2382
                            uint partner_26 = (simd_shuffle_xor((_S81), ushort((1U))));

#line 2382
                            if(_S78)
                            {

#line 2382
                                t_3[4U] = partner_26;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[5U] = partner_26;

#line 2382
                            }

#line 2382
                            uint _S82;

#line 2382
                            if(_S78)
                            {

#line 2382
                                _S82 = t_3[6U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S82 = t_3[7U];

#line 2382
                            }

#line 2382
                            uint partner_27 = (simd_shuffle_xor((_S82), ushort((1U))));

#line 2382
                            if(_S78)
                            {

#line 2382
                                t_3[6U] = partner_27;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[7U] = partner_27;

#line 2382
                            }

#line 2382
                            uint _S83;

#line 2382
                            if(_S78)
                            {

#line 2382
                                _S83 = t_3[8U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S83 = t_3[9U];

#line 2382
                            }

#line 2382
                            uint partner_28 = (simd_shuffle_xor((_S83), ushort((1U))));

#line 2382
                            if(_S78)
                            {

#line 2382
                                t_3[8U] = partner_28;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[9U] = partner_28;

#line 2382
                            }

#line 2382
                            uint _S84;

#line 2382
                            if(_S78)
                            {

#line 2382
                                _S84 = t_3[10U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S84 = t_3[11U];

#line 2382
                            }

#line 2382
                            uint partner_29 = (simd_shuffle_xor((_S84), ushort((1U))));

#line 2382
                            if(_S78)
                            {

#line 2382
                                t_3[10U] = partner_29;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[11U] = partner_29;

#line 2382
                            }

#line 2382
                            uint _S85;

#line 2382
                            if(_S78)
                            {

#line 2382
                                _S85 = t_3[12U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S85 = t_3[13U];

#line 2382
                            }

#line 2382
                            uint partner_30 = (simd_shuffle_xor((_S85), ushort((1U))));

#line 2382
                            if(_S78)
                            {

#line 2382
                                t_3[12U] = partner_30;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[13U] = partner_30;

#line 2382
                            }

#line 2382
                            uint _S86;

#line 2382
                            if(_S78)
                            {

#line 2382
                                _S86 = t_3[14U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S86 = t_3[15U];

#line 2382
                            }

#line 2382
                            uint partner_31 = (simd_shuffle_xor((_S86), ushort((1U))));

#line 2382
                            if(_S78)
                            {

#line 2382
                                t_3[14U] = partner_31;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[15U] = partner_31;

#line 2382
                            }

#line 2382
                            bool _S87 = (_S77 & 2U) != 0U;

#line 2382
                            uint _S88;

#line 2382
                            if(_S87)
                            {

#line 2382
                                _S88 = t_3[0U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S88 = t_3[2U];

#line 2382
                            }

#line 2382
                            uint partner_32 = (simd_shuffle_xor((_S88), ushort((2U))));

#line 2382
                            if(_S87)
                            {

#line 2382
                                t_3[0U] = partner_32;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[2U] = partner_32;

#line 2382
                            }

#line 2382
                            uint _S89;

#line 2382
                            if(_S87)
                            {

#line 2382
                                _S89 = t_3[1U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S89 = t_3[3U];

#line 2382
                            }

#line 2382
                            uint partner_33 = (simd_shuffle_xor((_S89), ushort((2U))));

#line 2382
                            if(_S87)
                            {

#line 2382
                                t_3[1U] = partner_33;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[3U] = partner_33;

#line 2382
                            }

#line 2382
                            uint _S90;

#line 2382
                            if(_S87)
                            {

#line 2382
                                _S90 = t_3[4U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S90 = t_3[6U];

#line 2382
                            }

#line 2382
                            uint partner_34 = (simd_shuffle_xor((_S90), ushort((2U))));

#line 2382
                            if(_S87)
                            {

#line 2382
                                t_3[4U] = partner_34;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[6U] = partner_34;

#line 2382
                            }

#line 2382
                            uint _S91;

#line 2382
                            if(_S87)
                            {

#line 2382
                                _S91 = t_3[5U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S91 = t_3[7U];

#line 2382
                            }

#line 2382
                            uint partner_35 = (simd_shuffle_xor((_S91), ushort((2U))));

#line 2382
                            if(_S87)
                            {

#line 2382
                                t_3[5U] = partner_35;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[7U] = partner_35;

#line 2382
                            }

#line 2382
                            uint _S92;

#line 2382
                            if(_S87)
                            {

#line 2382
                                _S92 = t_3[8U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S92 = t_3[10U];

#line 2382
                            }

#line 2382
                            uint partner_36 = (simd_shuffle_xor((_S92), ushort((2U))));

#line 2382
                            if(_S87)
                            {

#line 2382
                                t_3[8U] = partner_36;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[10U] = partner_36;

#line 2382
                            }

#line 2382
                            uint _S93;

#line 2382
                            if(_S87)
                            {

#line 2382
                                _S93 = t_3[9U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S93 = t_3[11U];

#line 2382
                            }

#line 2382
                            uint partner_37 = (simd_shuffle_xor((_S93), ushort((2U))));

#line 2382
                            if(_S87)
                            {

#line 2382
                                t_3[9U] = partner_37;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[11U] = partner_37;

#line 2382
                            }

#line 2382
                            uint _S94;

#line 2382
                            if(_S87)
                            {

#line 2382
                                _S94 = t_3[12U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S94 = t_3[14U];

#line 2382
                            }

#line 2382
                            uint partner_38 = (simd_shuffle_xor((_S94), ushort((2U))));

#line 2382
                            if(_S87)
                            {

#line 2382
                                t_3[12U] = partner_38;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[14U] = partner_38;

#line 2382
                            }

#line 2382
                            uint _S95;

#line 2382
                            if(_S87)
                            {

#line 2382
                                _S95 = t_3[13U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S95 = t_3[15U];

#line 2382
                            }

#line 2382
                            uint partner_39 = (simd_shuffle_xor((_S95), ushort((2U))));

#line 2382
                            if(_S87)
                            {

#line 2382
                                t_3[13U] = partner_39;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[15U] = partner_39;

#line 2382
                            }

#line 2382
                            bool _S96 = (_S77 & 4U) != 0U;

#line 2382
                            uint _S97;

#line 2382
                            if(_S96)
                            {

#line 2382
                                _S97 = t_3[0U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S97 = t_3[4U];

#line 2382
                            }

#line 2382
                            uint partner_40 = (simd_shuffle_xor((_S97), ushort((4U))));

#line 2382
                            if(_S96)
                            {

#line 2382
                                t_3[0U] = partner_40;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[4U] = partner_40;

#line 2382
                            }

#line 2382
                            uint _S98;

#line 2382
                            if(_S96)
                            {

#line 2382
                                _S98 = t_3[1U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S98 = t_3[5U];

#line 2382
                            }

#line 2382
                            uint partner_41 = (simd_shuffle_xor((_S98), ushort((4U))));

#line 2382
                            if(_S96)
                            {

#line 2382
                                t_3[1U] = partner_41;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[5U] = partner_41;

#line 2382
                            }

#line 2382
                            uint _S99;

#line 2382
                            if(_S96)
                            {

#line 2382
                                _S99 = t_3[2U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S99 = t_3[6U];

#line 2382
                            }

#line 2382
                            uint partner_42 = (simd_shuffle_xor((_S99), ushort((4U))));

#line 2382
                            if(_S96)
                            {

#line 2382
                                t_3[2U] = partner_42;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[6U] = partner_42;

#line 2382
                            }

#line 2382
                            uint _S100;

#line 2382
                            if(_S96)
                            {

#line 2382
                                _S100 = t_3[3U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S100 = t_3[7U];

#line 2382
                            }

#line 2382
                            uint partner_43 = (simd_shuffle_xor((_S100), ushort((4U))));

#line 2382
                            if(_S96)
                            {

#line 2382
                                t_3[3U] = partner_43;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[7U] = partner_43;

#line 2382
                            }

#line 2382
                            uint _S101;

#line 2382
                            if(_S96)
                            {

#line 2382
                                _S101 = t_3[8U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S101 = t_3[12U];

#line 2382
                            }

#line 2382
                            uint partner_44 = (simd_shuffle_xor((_S101), ushort((4U))));

#line 2382
                            if(_S96)
                            {

#line 2382
                                t_3[8U] = partner_44;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[12U] = partner_44;

#line 2382
                            }

#line 2382
                            uint _S102;

#line 2382
                            if(_S96)
                            {

#line 2382
                                _S102 = t_3[9U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S102 = t_3[13U];

#line 2382
                            }

#line 2382
                            uint partner_45 = (simd_shuffle_xor((_S102), ushort((4U))));

#line 2382
                            if(_S96)
                            {

#line 2382
                                t_3[9U] = partner_45;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[13U] = partner_45;

#line 2382
                            }

#line 2382
                            uint _S103;

#line 2382
                            if(_S96)
                            {

#line 2382
                                _S103 = t_3[10U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S103 = t_3[14U];

#line 2382
                            }

#line 2382
                            uint partner_46 = (simd_shuffle_xor((_S103), ushort((4U))));

#line 2382
                            if(_S96)
                            {

#line 2382
                                t_3[10U] = partner_46;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[14U] = partner_46;

#line 2382
                            }

#line 2382
                            uint _S104;

#line 2382
                            if(_S96)
                            {

#line 2382
                                _S104 = t_3[11U];

#line 2382
                            }
                            else
                            {

#line 2382
                                _S104 = t_3[15U];

#line 2382
                            }

#line 2382
                            uint partner_47 = (simd_shuffle_xor((_S104), ushort((4U))));

#line 2382
                            if(_S96)
                            {

#line 2382
                                t_3[11U] = partner_47;

#line 2382
                            }
                            else
                            {

#line 2382
                                t_3[15U] = partner_47;

#line 2382
                            }

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
                                _S40[i_5] = half2(as_type<half>(ushort((t_3[i_5]) & 65535U)), as_type<half>(ushort(((t_3[i_5]) >> 16U) & 65535U)));

#line 2382
                                i_5 = i_5 + 1U;

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
                innermostS_0(&_S39, &_S40);

#line 2382
                uint spanA_0;

#line 2382
                uint spanB_0;

#line 2382
                uint i_6;

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
                float2 _S105;

#line 2382
                if(_S31 != 0U)
                {

#line 2382
                    float _S106 = (as_type<float>((_S31)));

#line 2382
                    for(;;)
                    {

#line 2382
                        uint _S107 = slotToIndex_0(_S23 * 16U);

#line 2382
                        uint _S108 = _S107 - _S26;

#line 2382
                        if(_S27 > _S26)
                        {

#line 2382
                            spanA_0 = _S27 - _S26;

#line 2382
                        }
                        else
                        {

#line 2382
                            spanA_0 = 0U;

#line 2382
                        }

#line 2382
                        uint _S109 = _S107 - _S28;

#line 2382
                        if(_S29 > _S28)
                        {

#line 2382
                            spanB_0 = _S29 - _S28;

#line 2382
                        }
                        else
                        {

#line 2382
                            spanB_0 = 0U;

#line 2382
                        }

#line 2382
                        half2 _S110 = half2(float2(0.0f) );

#line 2382
                        i_6 = 0U;

#line 2382
                        db_0 = _S110;

#line 2382
                        ovAcc_0 = 0U;

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
                            uint si_0 = slotToIndex_0(i_6);

#line 2382
                            bool liveB_0 = (_S109 + si_0) < spanB_0;

#line 2382
                            half2 _S111 = _S39[i_6];

#line 2382
                            half2 _S112 = _S40[i_6];

#line 2382
                            half2 _S113 = mag2s_0(_S39[i_6], _S40[i_6]);

#line 2382
                            uint _S114 = (uint(as_type<ushort>(_S113[0U])) & 65535U) | (uint(as_type<ushort>(_S113[1U])) << 16U);

#line 2382
                            if((_S108 + si_0) < spanA_0)
                            {

#line 2382
                                ovAcc_1 = _S114 & 65535U;

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
                                ovAcc_2 = _S114 & 4294901760U;

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
                            half2 _S115 = max(db_0, half2(as_type<half>(ushort(m_0 & 65535U)), as_type<half>(ushort((m_0 >> 16U) & 65535U))));

#line 2382
                            uint ovAcc_3 = ovAcc_0 | (((((uint(as_type<ushort>(_S111[0U])) & 65535U) | (uint(as_type<ushort>(_S111[1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(_S112[0U])) & 65535U) | (uint(as_type<ushort>(_S112[1U])) << 16U)) & 2080406528U) + 67109888U));

#line 2382
                            i_6 = i_6 + 1U;

#line 2382
                            db_0 = _S115;

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
                        if(_S30 == 0U)
                        {

#line 2382
                            uint _S116 = (uint(as_type<ushort>(db_0[0U])) & 65535U) | (uint(as_type<ushort>(db_0[1U])) << 16U);

#line 2382
                            float thr2_0 = _S106 * _S106;

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
                                infLocalA_0 = (_S116 & 31744U) == 31744U;

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
                                infLocalB_0 = (_S116 & 2080374784U) == 2080374784U;

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
                                if((_S116 & 32767U) != 0U)
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
                                if((_S116 & 2147418112U) != 0U)
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
                            uint _S117 = bb_0 | bb_1;

#line 2382
                            uint _S118 = (simd_shuffle_xor((_S117), ushort((1U))));

#line 2382
                            uint hitBits_0 = _S117 | _S118;

#line 2382
                            uint _S119 = (simd_shuffle_xor((hitBits_0), ushort((2U))));

#line 2382
                            uint hitBits_1 = hitBits_0 | _S119;

#line 2382
                            uint _S120 = (simd_shuffle_xor((hitBits_1), ushort((4U))));

#line 2382
                            uint hitBits_2 = hitBits_1 | _S120;

#line 2382
                            if(_S23 == 0U)
                            {

#line 2382
                                if(_S24)
                                {

#line 2382
                                    packed_float2 device* _S121 = (&kernelContext_1)->entryPointParams_peakVal_0+pairA_0;

#line 2382
                                    if((hitBits_2 & 1U) != 0U)
                                    {

#line 2382
                                        _S105 = float2(3.40282306073709653e+38f, 0.0f);

#line 2382
                                    }
                                    else
                                    {

#line 2382
                                        _S105 = float2(0.0f, 0.0f);

#line 2382
                                    }

#line 2382
                                    *_S121 = packed_float2(_S105) ;

#line 2382
                                }

#line 2382
                                if(_S25)
                                {

#line 2382
                                    packed_float2 device* _S122 = (&kernelContext_1)->entryPointParams_peakVal_0+pairB_0;

#line 2382
                                    if((hitBits_2 & 2U) != 0U)
                                    {

#line 2382
                                        _S105 = float2(3.40282306073709653e+38f, 0.0f);

#line 2382
                                    }
                                    else
                                    {

#line 2382
                                        _S105 = float2(0.0f, 0.0f);

#line 2382
                                    }

#line 2382
                                    *_S122 = packed_float2(_S105) ;

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
                        uint _S123 = (max(bb_1 & 65535U, other_0 & 65535U)) | (max(bb_1 & 4294901760U, other_0 & 4294901760U));

#line 2382
                        uint other_1 = (simd_shuffle_xor((_S123), ushort((2U))));

#line 2382
                        uint _S124 = (max(_S123 & 65535U, other_1 & 65535U)) | (max(_S123 & 4294901760U, other_1 & 4294901760U));

#line 2382
                        uint other_2 = (simd_shuffle_xor((_S124), ushort((4U))));

#line 2382
                        uint bb_3 = (max(_S124 & 65535U, other_2 & 65535U)) | (max(_S124 & 4294901760U, other_2 & 4294901760U));

#line 2382
                        if(_S23 == 0U)
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
                                    infLocalA_0 = bA_0 >= _S106;

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
                                    infLocalA_0 = bB_0 >= _S106;

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
                            if(_S24)
                            {

#line 2382
                                packed_float2 device* _S125 = (&kernelContext_1)->entryPointParams_peakVal_0+pairA_0;

#line 2382
                                if(infA_0)
                                {

#line 2382
                                    _S105 = float2(3.40282306073709653e+38f, 0.0f);

#line 2382
                                }
                                else
                                {

#line 2382
                                    if(hitA_0)
                                    {

#line 2382
                                        _S105 = float2(bA_0, 0.0f);

#line 2382
                                    }
                                    else
                                    {

#line 2382
                                        _S105 = float2(0.0f, 0.0f);

#line 2382
                                    }

#line 2382
                                }

#line 2382
                                *_S125 = packed_float2(_S105) ;

#line 2382
                            }

#line 2382
                            if(_S25)
                            {

#line 2382
                                packed_float2 device* _S126 = (&kernelContext_1)->entryPointParams_peakVal_0+pairB_0;

#line 2382
                                if(infB_0)
                                {

#line 2382
                                    _S105 = float2(3.40282306073709653e+38f, 0.0f);

#line 2382
                                }
                                else
                                {

#line 2382
                                    if(hitB_0)
                                    {

#line 2382
                                        _S105 = float2(bB_0, 0.0f);

#line 2382
                                    }
                                    else
                                    {

#line 2382
                                        _S105 = float2(0.0f, 0.0f);

#line 2382
                                    }

#line 2382
                                }

#line 2382
                                *_S126 = packed_float2(_S105) ;

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
                    array<half2, int(16)> _S127 = _S39;

#line 2382
                    array<half2, int(16)> _S128 = _S40;

#line 2382
                    for(;;)
                    {

#line 2382
                        uint _S129 = slotToIndex_0(_S23 * 16U);

#line 2382
                        uint _S130 = _S129 - _S26;

#line 2382
                        if(_S27 > _S26)
                        {

#line 2382
                            spanA_0 = _S27 - _S26;

#line 2382
                        }
                        else
                        {

#line 2382
                            spanA_0 = 0U;

#line 2382
                        }

#line 2382
                        uint _S131 = _S129 - _S28;

#line 2382
                        if(_S29 > _S28)
                        {

#line 2382
                            spanB_0 = _S29 - _S28;

#line 2382
                        }
                        else
                        {

#line 2382
                            spanB_0 = 0U;

#line 2382
                        }

#line 2382
                        i_6 = 0U;

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
                            if(i_6 < 16U)
                            {
                            }
                            else
                            {

#line 2382
                                break;
                            }

#line 2382
                            uint si_1 = slotToIndex_0(i_6);

#line 2382
                            bool liveB_1 = (_S131 + si_1) < spanB_0;

#line 2382
                            half2 mg_0 = mag2s_0(_S127[i_6], _S128[i_6]);

#line 2382
                            uint _S132 = (uint(as_type<ushort>(mg_0[0U])) & 65535U) | (uint(as_type<ushort>(mg_0[1U])) << 16U);

#line 2382
                            uint ovAcc_4 = ovAcc_0 | (((((uint(as_type<ushort>(_S127[i_6][0U])) & 65535U) | (uint(as_type<ushort>(_S127[i_6][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(_S128[i_6][0U])) & 65535U) | (uint(as_type<ushort>(_S128[i_6][1U])) << 16U)) & 2080406528U) + 67109888U));

#line 2382
                            if((_S130 + si_1) < spanA_0)
                            {

#line 2382
                                bb_0 = _S132 << 16U;

#line 2382
                            }
                            else
                            {

#line 2382
                                bb_0 = 0U;

#line 2382
                            }

#line 2382
                            uint _S133 = 15U - i_6;

#line 2382
                            uint _S134 = max(ovAcc_1, bb_0 | _S133);

#line 2382
                            if(liveB_1)
                            {

#line 2382
                                bb_1 = _S132 & 4294901760U;

#line 2382
                            }
                            else
                            {

#line 2382
                                bb_1 = 0U;

#line 2382
                            }

#line 2382
                            uint _S135 = max(ovAcc_2, bb_1 | _S133);

#line 2382
                            i_6 = i_6 + 1U;

#line 2382
                            ovAcc_0 = ovAcc_4;

#line 2382
                            ovAcc_1 = _S134;

#line 2382
                            ovAcc_2 = _S135;

#line 2382
                        }

#line 2382
                        bool _S136 = spanA_0 != 0U;

#line 2382
                        if(_S136)
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
                        bool _S137 = spanB_0 != 0U;

#line 2382
                        if(_S137)
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
                        uint _S138 = (4095U - _S23) << 4U;

#line 2382
                        uint kA_0 = bb_0 | _S138;

#line 2382
                        uint kB_0 = bb_1 | _S138;

#line 2382
                        uint _S139 = (simd_shuffle_xor((kA_0), ushort((1U))));

#line 2382
                        uint _S140 = max(kA_0, _S139);

#line 2382
                        uint _S141 = (simd_shuffle_xor((kB_0), ushort((1U))));

#line 2382
                        uint _S142 = max(kB_0, _S141);

#line 2382
                        uint _S143 = (simd_shuffle_xor((_S140), ushort((2U))));

#line 2382
                        uint _S144 = max(_S140, _S143);

#line 2382
                        uint _S145 = (simd_shuffle_xor((_S142), ushort((2U))));

#line 2382
                        uint _S146 = max(_S142, _S145);

#line 2382
                        uint _S147 = (simd_shuffle_xor((_S144), ushort((4U))));

#line 2382
                        uint _S148 = max(_S144, _S147);

#line 2382
                        uint _S149 = (simd_shuffle_xor((_S146), ushort((4U))));

#line 2382
                        uint _S150 = max(_S146, _S149);

#line 2382
                        uint slotA_0 = 65535U - (_S148 & 65535U);

#line 2382
                        uint slotB_0 = 65535U - (_S150 & 65535U);

#line 2382
                        if(_S136)
                        {

#line 2382
                            hitLocalA_0 = (_S148 >> 16U) >= 31744U;

#line 2382
                        }
                        else
                        {

#line 2382
                            hitLocalA_0 = false;

#line 2382
                        }

#line 2382
                        if(_S137)
                        {

#line 2382
                            hitLocalB_0 = (_S150 >> 16U) >= 31744U;

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
                            hitA_0 = (as_type<half>((ushort)((_S148 >> 16U)))) > (as_type<float>((_S31)));

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
                            hitB_0 = (as_type<half>((ushort)((_S150 >> 16U)))) > (as_type<float>((_S31)));

#line 2382
                        }

#line 2382
                        uint wA_0 = slotA_0 >> 4U;

#line 2382
                        uint _S151 = slotA_0 & 15U;

#line 2382
                        uint wB_0 = slotB_0 >> 4U;

#line 2382
                        uint _S152 = slotB_0 & 15U;

#line 2382
                        half2 _S153 = half2(float2(0.0f) );

#line 2382
                        j_1 = 0U;

#line 2382
                        db_0 = _S153;

#line 2382
                        half2 selB_0 = _S153;

#line 2382
                        for(;;)
                        {

#line 2382
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2382
                                break;
                            }

#line 2382
                            if(j_1 == _S151)
                            {

#line 2382
                                db_0 = half2(_S127[j_1].x, _S128[j_1].x);

#line 2382
                            }

#line 2382
                            if(j_1 == _S152)
                            {

#line 2382
                                selB_0 = half2(_S127[j_1].y, _S128[j_1].y);

#line 2382
                            }

#line 2382
                            j_1 = j_1 + 1U;

#line 2382
                        }

#line 2382
                        uint _S154 = (simd_shuffle_xor(((uint(as_type<ushort>(db_0[0U])) & 65535U) | (uint(as_type<ushort>(db_0[1U])) << 16U)), ushort((wA_0))));

#line 2382
                        half _S155 = as_type<half>(ushort(_S154 & 65535U));

#line 2382
                        half _S156 = as_type<half>(ushort((_S154 >> 16U) & 65535U));

#line 2382
                        uint _S157 = (simd_shuffle_xor(((uint(as_type<ushort>(selB_0[0U])) & 65535U) | (uint(as_type<ushort>(selB_0[1U])) << 16U)), ushort((wB_0))));

#line 2382
                        half _S158 = as_type<half>(ushort(_S157 & 65535U));

#line 2382
                        half _S159 = as_type<half>(ushort((_S157 >> 16U) & 65535U));

#line 2382
                        bool _S160 = _S23 == 0U;

#line 2382
                        bool _S161;

#line 2382
                        if(_S160)
                        {

#line 2382
                            _S161 = _S24;

#line 2382
                        }
                        else
                        {

#line 2382
                            _S161 = false;

#line 2382
                        }

#line 2382
                        int _S162;

#line 2382
                        if(_S161)
                        {

#line 2382
                            int device* _S163 = (&kernelContext_1)->entryPointParams_peakIdx_0+pairA_0;

#line 2382
                            if(hitA_0)
                            {

#line 2382
                                _S162 = int(slotToIndex_0(slotA_0));

#line 2382
                            }
                            else
                            {

#line 2382
                                _S162 = int(-1);

#line 2382
                            }

#line 2382
                            *_S163 = _S162;

#line 2382
                            packed_float2 device* _S164 = (&kernelContext_1)->entryPointParams_peakVal_0+pairA_0;

#line 2382
                            if(hitLocalA_0)
                            {

#line 2382
                                _S105 = float2(3.40282306073709653e+38f, 0.0f);

#line 2382
                            }
                            else
                            {

#line 2382
                                if(hitA_0)
                                {

#line 2382
                                    _S105 = float2(float(_S155), float(_S156));

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S105 = float2(0.0f, 0.0f);

#line 2382
                                }

#line 2382
                            }

#line 2382
                            *_S164 = packed_float2(_S105) ;

#line 2382
                        }

#line 2382
                        bool _S165;

#line 2382
                        if(_S160)
                        {

#line 2382
                            _S165 = _S25;

#line 2382
                        }
                        else
                        {

#line 2382
                            _S165 = false;

#line 2382
                        }

#line 2382
                        if(_S165)
                        {

#line 2382
                            int device* _S166 = (&kernelContext_1)->entryPointParams_peakIdx_0+pairB_0;

#line 2382
                            if(hitB_0)
                            {

#line 2382
                                _S162 = int(slotToIndex_0(slotB_0));

#line 2382
                            }
                            else
                            {

#line 2382
                                _S162 = int(-1);

#line 2382
                            }

#line 2382
                            *_S166 = _S162;

#line 2382
                            packed_float2 device* _S167 = (&kernelContext_1)->entryPointParams_peakVal_0+pairB_0;

#line 2382
                            if(hitLocalB_0)
                            {

#line 2382
                                _S105 = float2(3.40282306073709653e+38f, 0.0f);

#line 2382
                            }
                            else
                            {

#line 2382
                                if(hitB_0)
                                {

#line 2382
                                    _S105 = float2(float(_S158), float(_S159));

#line 2382
                                }
                                else
                                {

#line 2382
                                    _S105 = float2(0.0f, 0.0f);

#line 2382
                                }

#line 2382
                            }

#line 2382
                            *_S167 = packed_float2(_S105) ;

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
        base_1 = base_1 + (&kernelContext_1)->entryPointParams_0->gridSize_0 * 16U;

#line 2370
    }

#line 2399
    return;
}
