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

#line 10 "mm_64_refineListed_c16.slang"
constant array<uint, int(64)> COARSE_TWT_DATA_0 = { { 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 776354806U, 842939353U, 883243944U, 908016484U, 931871502U, 947010215U, 957561391U, 967326120U, 976173331U, 984037490U, 990787467U, 996423199U, 1000879269U, 1004089918U, 1005989446U, 15360U, 842939353U, 908016484U, 947010215U, 967326120U, 984037490U, 996423199U, 1004089918U, 1006632960U, 1004122686U, 996455967U, 984070258U, 967358888U, 947042983U, 908049252U, 842972121U, 15360U, 883243944U, 947010215U, 976173331U, 996423199U, 1005989446U, 1004122686U, 990820235U, 967358888U, 931904270U, 842972121U, 2923871222U, 3055532900U, 3105077807U, 3131553906U, 3148395685U } };

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


#line 323 "mm_64_refineListed_c16.slang"
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

#line 233 "mm_64_refineListed_c16.slang"
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


#line 172 "mm_64_refineListed_c16.slang"
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

#line 266 "mm_64_refineListed_c16.slang"
    if(_S6 != 0U)
    {

#line 73 "twiddle.slang"
        uint _S7 = mfDataScaleFlag_0();

#line 267 "mm_64_refineListed_c16.slang"
        float s_0 = (as_type<float>((_S7)));
        uint _S8 = 2U * i_1;

#line 268
        return half2(half((as_type<float>((b_1[_S8]))) * s_0), half((as_type<float>((b_1[_S8 + 1U]))) * s_0));
    }
    return cload_0(b_1, i_1);
}


#line 402
void cmulconjs_0(half2 ar_0, half2 ai_0, half2 br_0, half2 bi_0, half2 thread* pr_0, half2 thread* pi_0)
{
    *pr_0 = ar_0 * br_0 + ai_0 * bi_0;
    *pi_0 = ai_0 * br_0 - ar_0 * bi_0;
    return;
}


#line 414
void r4s_0(array<half2, int(16)> thread* re_0, array<half2, int(16)> thread* im_0, uint a_0, uint b_2, uint c_0, uint d_1)
{
    half2 t0r_0 = (*re_0)[a_0] + (*re_0)[c_0];

#line 416
    half2 t0i_0 = (*im_0)[a_0] + (*im_0)[c_0];
    half2 t1r_0 = (*re_0)[a_0] - (*re_0)[c_0];

#line 417
    half2 t1i_0 = (*im_0)[a_0] - (*im_0)[c_0];
    half2 t2r_0 = (*re_0)[b_2] + (*re_0)[d_1];

#line 418
    half2 t2i_0 = (*im_0)[b_2] + (*im_0)[d_1];
    half2 t3r_0 = (*re_0)[b_2] - (*re_0)[d_1];
    half2 j3r_0 = - ((*im_0)[b_2] - (*im_0)[d_1]);
    (*re_0)[a_0] = t0r_0 + t2r_0;

#line 421
    (*im_0)[a_0] = t0i_0 + t2i_0;
    (*re_0)[b_2] = t1r_0 + j3r_0;

#line 422
    (*im_0)[b_2] = t1i_0 + t3r_0;
    (*re_0)[c_0] = t0r_0 - t2r_0;

#line 423
    (*im_0)[c_0] = t0i_0 - t2i_0;
    (*re_0)[d_1] = t1r_0 - j3r_0;

#line 424
    (*im_0)[d_1] = t1i_0 - t3r_0;
    return;
}


#line 414
void r4s_1(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint a_1, uint b_3, uint c_1, uint d_2)
{
    half2 t0r_1 = (*re_1)[a_1] + (*re_1)[c_1];

#line 416
    half2 t0i_1 = (*im_1)[a_1] + (*im_1)[c_1];
    half2 t1r_1 = (*re_1)[a_1] - (*re_1)[c_1];

#line 417
    half2 t1i_1 = (*im_1)[a_1] - (*im_1)[c_1];
    half2 t2r_1 = (*re_1)[b_3] + (*re_1)[d_2];

#line 418
    half2 t2i_1 = (*im_1)[b_3] + (*im_1)[d_2];
    half2 t3r_1 = (*re_1)[b_3] - (*re_1)[d_2];
    half2 j3r_1 = - ((*im_1)[b_3] - (*im_1)[d_2]);
    (*re_1)[a_1] = t0r_1 + t2r_1;

#line 421
    (*im_1)[a_1] = t0i_1 + t2i_1;
    (*re_1)[b_3] = t1r_1 + j3r_1;

#line 422
    (*im_1)[b_3] = t1i_1 + t3r_1;
    (*re_1)[c_1] = t0r_1 - t2r_1;

#line 423
    (*im_1)[c_1] = t0i_1 - t2i_1;
    (*re_1)[d_2] = t1r_1 - j3r_1;

#line 424
    (*im_1)[d_2] = t1i_1 - t3r_1;
    return;
}


#line 393
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 393
    half2 _S9 = half2(wr_0) ;

#line 393
    half2 _S10 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S10 + *xi_0 * _S9;
    *xr_0 = *xr_0 * _S9 - *xi_0 * _S10;

#line 397
    *xi_0 = ni_0;
    return;
}


#line 427
void swap2_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2, uint p_1, uint q_0)
{

    half2 t_0 = (*re_2)[p_1];

#line 430
    (*re_2)[p_1] = (*re_2)[q_0];

#line 430
    (*re_2)[q_0] = t_0;
    half2 t_1 = (*im_2)[p_1];

#line 431
    (*im_2)[p_1] = (*im_2)[q_0];

#line 431
    (*im_2)[q_0] = t_1;
    return;
}


#line 427
void swap2_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint p_2, uint q_1)
{

    half2 t_2 = (*re_3)[p_2];

#line 430
    (*re_3)[p_2] = (*re_3)[q_1];

#line 430
    (*re_3)[q_1] = t_2;
    half2 t_3 = (*im_3)[p_2];

#line 431
    (*im_3)[p_2] = (*im_3)[q_1];

#line 431
    (*im_3)[q_1] = t_3;
    return;
}


#line 465
void dft16s_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4)
{

#line 465
    uint n1_0 = 0U;

    for(;;)
    {

#line 467
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 467
            break;
        }

#line 467
        r4s_0(re_4, im_4, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 467
        n1_0 = n1_0 + 1U;

#line 467
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

#line 478
    uint k2_0 = 0U;
    for(;;)
    {

#line 479
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 479
            break;
        }

#line 480
        uint _S11 = 4U * k2_0;

#line 480
        r4s_0(re_4, im_4, _S11, _S11 + 1U, _S11 + 2U, _S11 + 3U);

#line 479
        k2_0 = k2_0 + 1U;

#line 479
    }

    swap2_0(re_4, im_4, 1U, 4U);

#line 481
    swap2_0(re_4, im_4, 2U, 8U);

#line 481
    swap2_0(re_4, im_4, 3U, 12U);
    swap2_0(re_4, im_4, 6U, 9U);

#line 482
    swap2_0(re_4, im_4, 7U, 13U);

#line 482
    swap2_0(re_4, im_4, 11U, 14U);
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


#line 441 "mm_64_refineListed_c16.slang"
void dft4s_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5, uint o_0)
{
    uint _S16 = o_0 + 1U;

#line 443
    uint _S17 = o_0 + 2U;

#line 443
    r4s_1(re_5, im_5, o_0, _S16, _S17, o_0 + 3U);
    swap2_1(re_5, im_5, _S16, _S17);
    return;
}


#line 609
void innermostS_0(array<half2, int(16)> thread* re_6, array<half2, int(16)> thread* im_6)
{

#line 609
    uint b_4 = 0U;



    for(;;)
    {

#line 613
        if(b_4 < 4U)
        {
        }
        else
        {

#line 613
            break;
        }

#line 613
        dft4s_0(re_6, im_6, b_4 * 4U);

#line 613
        b_4 = b_4 + 1U;

#line 613
    }

    return;
}


#line 885
uint lgOf_0(uint i_2)
{

#line 885
    uint _S18;

#line 885
    if(i_2 < 1U)
    {

#line 885
        _S18 = 4U;

#line 885
    }
    else
    {

#line 885
        _S18 = 1U;

#line 885
    }

#line 885
    return _S18;
}


#line 887
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 891
    uint lg_1 = lgOf_0(1U);

#line 891
    uint lg_2 = lgOf_0(0U);

#line 896
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 489
half2 mag2s_0(half2 re_7, half2 im_7)
{

#line 489
    return re_7 * re_7 + im_7 * im_7;
}


#line 2350
[[kernel]] void refineListedBounded(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]], uint device* entryPointParams_rowWin_1 [[buffer(7)]])
{

#line 2350
    half2 db_0;

#line 2350
    uint j_0;

#line 2350
    thread KernelContext_0 kernelContext_1;

#line 2350
    (&kernelContext_1)->entryPointParams_0 = entryPointParams_1;

#line 2350
    (&kernelContext_1)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2350
    (&kernelContext_1)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2350
    (&kernelContext_1)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2350
    (&kernelContext_1)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2350
    (&kernelContext_1)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2350
    (&kernelContext_1)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2350
    (&kernelContext_1)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 2350
    (&kernelContext_1)->_binPhase_0 = 0U;

#line 2361
    uint total_0 = entryPointParams_count_1[int(0)];

    if(total_0 == 0U)
    {

#line 2363
        return;
    }

#line 2369
    uint _S19 = lid_0.x;

#line 2369
    uint sub_0 = _S19 / 4U;

#line 2369
    uint _S20 = _S19 % 4U;
    (&kernelContext_1)->_stgBase_0 = sub_0 * 64U;

#line 2370
    uint base_0 = gid_0.x * 32U;

    for(;;)
    {

#line 2372
        if(base_0 < total_0)
        {
        }
        else
        {

#line 2372
            break;
        }

#line 2373
        uint idxA_0 = base_0 + 2U * sub_0;
        uint idxB_0 = idxA_0 + 1U;

#line 2374
        uint pairA_0;
        if(idxA_0 < total_0)
        {

#line 2375
            pairA_0 = (&kernelContext_1)->entryPointParams_survivors_0[idxA_0];

#line 2375
        }
        else
        {

#line 2375
            pairA_0 = 4294967295U;

#line 2375
        }

#line 2375
        uint pairB_0;
        if(idxB_0 < total_0)
        {

#line 2376
            pairB_0 = (&kernelContext_1)->entryPointParams_survivors_0[idxB_0];

#line 2376
        }
        else
        {

#line 2376
            pairB_0 = 4294967295U;

#line 2376
        }
        bool _S21 = pairA_0 != 4294967295U;

#line 2377
        uint refPairA_0;

#line 2377
        if(_S21)
        {

#line 2377
            refPairA_0 = pairA_0;

#line 2377
        }
        else
        {

#line 2377
            refPairA_0 = (&kernelContext_1)->entryPointParams_survivors_0[total_0 - 1U];

#line 2377
        }
        bool _S22 = pairB_0 != 4294967295U;

#line 2378
        uint refPairB_0;

#line 2378
        if(_S22)
        {

#line 2378
            refPairB_0 = pairB_0;

#line 2378
        }
        else
        {

#line 2378
            refPairB_0 = refPairA_0;

#line 2378
        }
        uint dA_0 = refPairA_0 / (&kernelContext_1)->entryPointParams_0->ntmpl_0;

#line 2379
        uint tA_0 = refPairA_0 % (&kernelContext_1)->entryPointParams_0->ntmpl_0;
        uint dB_0 = refPairB_0 / (&kernelContext_1)->entryPointParams_0->ntmpl_0;

#line 2380
        uint tB_0 = refPairB_0 % (&kernelContext_1)->entryPointParams_0->ntmpl_0;
        thread uint wsA_0 = (&kernelContext_1)->entryPointParams_0->winStart_0;

#line 2381
        thread uint weA_0 = (&kernelContext_1)->entryPointParams_0->winEnd_0;

#line 2381
        thread uint wsB_0 = (&kernelContext_1)->entryPointParams_0->winStart_0;

#line 2381
        thread uint weB_0 = (&kernelContext_1)->entryPointParams_0->winEnd_0;

#line 2381
        rowWindow_0(dA_0, &wsA_0, &weA_0, (&kernelContext_1)->entryPointParams_rowWin_0, &kernelContext_1);

#line 2381
        rowWindow_0(dB_0, &wsB_0, &weB_0, (&kernelContext_1)->entryPointParams_rowWin_0, &kernelContext_1);


        uint _S23 = wsA_0;

#line 2384
        uint _S24 = weA_0;

#line 2384
        uint _S25 = wsB_0;

#line 2384
        uint _S26 = weB_0;

#line 2384
        uint _S27 = (&kernelContext_1)->entryPointParams_0->nbins_0;

#line 2384
        uint _S28 = (&kernelContext_1)->entryPointParams_0->thrBits_0;

#line 2384
        for(;;)
        {

#line 2384
            thread array<half2, int(16)> re_8;

#line 2384
            thread array<half2, int(16)> im_8;

#line 2384
            uint _S29 = mfDataStrideFlag_0();

#line 2384
            uint _S30;

#line 2384
            if(_S29 != 0U)
            {

#line 2384
                uint _S31 = mfDataStrideFlag_0();

#line 2384
                _S30 = _S31;

#line 2384
            }
            else
            {

#line 2384
                _S30 = 64U;

#line 2384
            }

#line 2384
            bool _S32 = dB_0 == dA_0;

#line 2384
            uint n2_0 = 0U;

#line 2384
            for(;;)
            {

#line 2384
                if(n2_0 < 16U)
                {
                }
                else
                {

#line 2384
                    break;
                }

#line 2384
                uint k_0 = _S20 + 4U * n2_0;

#line 2384
                half2 da_0 = dload_0((&kernelContext_1)->entryPointParams_data_0, dA_0 * _S30 + k_0);

#line 2384
                if(_S32)
                {

#line 2384
                    db_0 = da_0;

#line 2384
                }
                else
                {

#line 2384
                    half2 _S33 = dload_0((&kernelContext_1)->entryPointParams_data_0, dB_0 * _S30 + k_0);

#line 2384
                    db_0 = _S33;

#line 2384
                }

#line 2384
                half2 ta_0 = cload_0((&kernelContext_1)->entryPointParams_tmpl_0, tA_0 * 64U + k_0);

#line 2384
                half2 tb_0 = cload_0((&kernelContext_1)->entryPointParams_tmpl_0, tB_0 * 64U + k_0);

#line 2384
                cmulconjs_0(half2(da_0.x, db_0.x), half2(da_0.y, db_0.y), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_8[n2_0], &im_8[n2_0]);

#line 2384
                n2_0 = n2_0 + 1U;

#line 2384
            }

#line 2384
            array<half2, int(16)> _S34 = re_8;

#line 2384
            array<half2, int(16)> _S35 = im_8;

#line 2384
            for(;;)
            {

#line 2384
                thread array<half2, int(16)> _S36 = _S34;

#line 2384
                thread array<half2, int(16)> _S37 = _S35;

#line 2384
                (&kernelContext_1)->_tid_0 = _S20;

#line 2384
                for(;;)
                {

#line 2384
                    uint lane_0 = _S20 & 3U;

#line 2384
                    dft16s_0(&_S36, &_S37);

#line 2384
                    uint _S38 = mfCoarseTwtFlag_0();

#line 2384
                    uint r_0;

#line 2384
                    if(_S38 != 0U)
                    {

#line 2384
                        r_0 = 0U;

#line 2384
                        for(;;)
                        {

#line 2384
                            if(r_0 < 16U)
                            {
                            }
                            else
                            {

#line 2384
                                break;
                            }

#line 2384
                            uint _S39 = lane_0 * 16U + r_0;

#line 2384
                            cmulw_0(&_S36[r_0], &_S37[r_0], as_type<half>(ushort((COARSE_TWT_DATA_0[_S39]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S39]) >> 16U) & 65535U)));

#line 2384
                            r_0 = r_0 + 1U;

#line 2384
                        }

#line 2384
                    }
                    else
                    {

#line 2384
                        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_0) / 64.0f);

#line 2384
                        float _S40 = tw_0.x;

#line 2384
                        float _S41 = tw_0.y;

#line 2384
                        r_0 = 0U;

#line 2384
                        float cr_0 = 1.0f;

#line 2384
                        float ci_0 = 0.0f;

#line 2384
                        for(;;)
                        {

#line 2384
                            if(r_0 < 16U)
                            {
                            }
                            else
                            {

#line 2384
                                break;
                            }

#line 2384
                            cmulw_0(&_S36[r_0], &_S37[r_0], half(cr_0), half(ci_0));

#line 2384
                            float nr_0 = cr_0 * _S40 - ci_0 * _S41;

#line 2384
                            float _S42 = cr_0 * _S41 + ci_0 * _S40;

#line 2384
                            r_0 = r_0 + 1U;

#line 2384
                            cr_0 = nr_0;

#line 2384
                            ci_0 = _S42;

#line 2384
                        }

#line 2384
                    }

#line 2384
                    uint per_0 = 16U / max(4U, 1U);

#line 2384
                    uint _S43 = max(0U, 1U);

#line 2384
                    uint blk2_0 = _S20 / _S43;

#line 2384
                    uint lane2_0 = _S20 % _S43;

#line 2384
                    for(;;)
                    {

#line 2384
                        uint _S44 = (&kernelContext_1)->_tid_0;

#line 2384
                        for(;;)
                        {

#line 2384
                            thread array<uint, int(16)> t_4;

#line 2384
                            r_0 = 0U;

#line 2384
                            for(;;)
                            {

#line 2384
                                if(r_0 < 4U)
                                {
                                }
                                else
                                {

#line 2384
                                    break;
                                }

#line 2384
                                j_0 = 0U;

#line 2384
                                for(;;)
                                {

#line 2384
                                    if(j_0 < 4U)
                                    {
                                    }
                                    else
                                    {

#line 2384
                                        break;
                                    }

#line 2384
                                    t_4[j_0 * 4U + r_0] = (uint(as_type<ushort>(_S36[r_0 * 4U + j_0][0U])) & 65535U) | (uint(as_type<ushort>(_S36[r_0 * 4U + j_0][1U])) << 16U);

#line 2384
                                    j_0 = j_0 + 1U;

#line 2384
                                }

#line 2384
                                r_0 = r_0 + 1U;

#line 2384
                            }

#line 2384
                            uint _S45 = _S44 & 3U;

#line 2384
                            bool _S46 = (_S45 & 1U) != 0U;

#line 2384
                            uint _S47;

#line 2384
                            if(_S46)
                            {

#line 2384
                                _S47 = t_4[0U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S47 = t_4[1U];

#line 2384
                            }

#line 2384
                            uint partner_0 = (simd_shuffle_xor((_S47), ushort((1U))));

#line 2384
                            if(_S46)
                            {

#line 2384
                                t_4[0U] = partner_0;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[1U] = partner_0;

#line 2384
                            }

#line 2384
                            uint _S48;

#line 2384
                            if(_S46)
                            {

#line 2384
                                _S48 = t_4[2U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S48 = t_4[3U];

#line 2384
                            }

#line 2384
                            uint partner_1 = (simd_shuffle_xor((_S48), ushort((1U))));

#line 2384
                            if(_S46)
                            {

#line 2384
                                t_4[2U] = partner_1;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[3U] = partner_1;

#line 2384
                            }

#line 2384
                            uint _S49;

#line 2384
                            if(_S46)
                            {

#line 2384
                                _S49 = t_4[4U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S49 = t_4[5U];

#line 2384
                            }

#line 2384
                            uint partner_2 = (simd_shuffle_xor((_S49), ushort((1U))));

#line 2384
                            if(_S46)
                            {

#line 2384
                                t_4[4U] = partner_2;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[5U] = partner_2;

#line 2384
                            }

#line 2384
                            uint _S50;

#line 2384
                            if(_S46)
                            {

#line 2384
                                _S50 = t_4[6U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S50 = t_4[7U];

#line 2384
                            }

#line 2384
                            uint partner_3 = (simd_shuffle_xor((_S50), ushort((1U))));

#line 2384
                            if(_S46)
                            {

#line 2384
                                t_4[6U] = partner_3;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[7U] = partner_3;

#line 2384
                            }

#line 2384
                            uint _S51;

#line 2384
                            if(_S46)
                            {

#line 2384
                                _S51 = t_4[8U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S51 = t_4[9U];

#line 2384
                            }

#line 2384
                            uint partner_4 = (simd_shuffle_xor((_S51), ushort((1U))));

#line 2384
                            if(_S46)
                            {

#line 2384
                                t_4[8U] = partner_4;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[9U] = partner_4;

#line 2384
                            }

#line 2384
                            uint _S52;

#line 2384
                            if(_S46)
                            {

#line 2384
                                _S52 = t_4[10U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S52 = t_4[11U];

#line 2384
                            }

#line 2384
                            uint partner_5 = (simd_shuffle_xor((_S52), ushort((1U))));

#line 2384
                            if(_S46)
                            {

#line 2384
                                t_4[10U] = partner_5;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[11U] = partner_5;

#line 2384
                            }

#line 2384
                            uint _S53;

#line 2384
                            if(_S46)
                            {

#line 2384
                                _S53 = t_4[12U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S53 = t_4[13U];

#line 2384
                            }

#line 2384
                            uint partner_6 = (simd_shuffle_xor((_S53), ushort((1U))));

#line 2384
                            if(_S46)
                            {

#line 2384
                                t_4[12U] = partner_6;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[13U] = partner_6;

#line 2384
                            }

#line 2384
                            uint _S54;

#line 2384
                            if(_S46)
                            {

#line 2384
                                _S54 = t_4[14U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S54 = t_4[15U];

#line 2384
                            }

#line 2384
                            uint partner_7 = (simd_shuffle_xor((_S54), ushort((1U))));

#line 2384
                            if(_S46)
                            {

#line 2384
                                t_4[14U] = partner_7;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[15U] = partner_7;

#line 2384
                            }

#line 2384
                            bool _S55 = (_S45 & 2U) != 0U;

#line 2384
                            uint _S56;

#line 2384
                            if(_S55)
                            {

#line 2384
                                _S56 = t_4[0U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S56 = t_4[2U];

#line 2384
                            }

#line 2384
                            uint partner_8 = (simd_shuffle_xor((_S56), ushort((2U))));

#line 2384
                            if(_S55)
                            {

#line 2384
                                t_4[0U] = partner_8;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[2U] = partner_8;

#line 2384
                            }

#line 2384
                            uint _S57;

#line 2384
                            if(_S55)
                            {

#line 2384
                                _S57 = t_4[1U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S57 = t_4[3U];

#line 2384
                            }

#line 2384
                            uint partner_9 = (simd_shuffle_xor((_S57), ushort((2U))));

#line 2384
                            if(_S55)
                            {

#line 2384
                                t_4[1U] = partner_9;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[3U] = partner_9;

#line 2384
                            }

#line 2384
                            uint _S58;

#line 2384
                            if(_S55)
                            {

#line 2384
                                _S58 = t_4[4U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S58 = t_4[6U];

#line 2384
                            }

#line 2384
                            uint partner_10 = (simd_shuffle_xor((_S58), ushort((2U))));

#line 2384
                            if(_S55)
                            {

#line 2384
                                t_4[4U] = partner_10;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[6U] = partner_10;

#line 2384
                            }

#line 2384
                            uint _S59;

#line 2384
                            if(_S55)
                            {

#line 2384
                                _S59 = t_4[5U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S59 = t_4[7U];

#line 2384
                            }

#line 2384
                            uint partner_11 = (simd_shuffle_xor((_S59), ushort((2U))));

#line 2384
                            if(_S55)
                            {

#line 2384
                                t_4[5U] = partner_11;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[7U] = partner_11;

#line 2384
                            }

#line 2384
                            uint _S60;

#line 2384
                            if(_S55)
                            {

#line 2384
                                _S60 = t_4[8U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S60 = t_4[10U];

#line 2384
                            }

#line 2384
                            uint partner_12 = (simd_shuffle_xor((_S60), ushort((2U))));

#line 2384
                            if(_S55)
                            {

#line 2384
                                t_4[8U] = partner_12;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[10U] = partner_12;

#line 2384
                            }

#line 2384
                            uint _S61;

#line 2384
                            if(_S55)
                            {

#line 2384
                                _S61 = t_4[9U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S61 = t_4[11U];

#line 2384
                            }

#line 2384
                            uint partner_13 = (simd_shuffle_xor((_S61), ushort((2U))));

#line 2384
                            if(_S55)
                            {

#line 2384
                                t_4[9U] = partner_13;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[11U] = partner_13;

#line 2384
                            }

#line 2384
                            uint _S62;

#line 2384
                            if(_S55)
                            {

#line 2384
                                _S62 = t_4[12U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S62 = t_4[14U];

#line 2384
                            }

#line 2384
                            uint partner_14 = (simd_shuffle_xor((_S62), ushort((2U))));

#line 2384
                            if(_S55)
                            {

#line 2384
                                t_4[12U] = partner_14;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[14U] = partner_14;

#line 2384
                            }

#line 2384
                            uint _S63;

#line 2384
                            if(_S55)
                            {

#line 2384
                                _S63 = t_4[13U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S63 = t_4[15U];

#line 2384
                            }

#line 2384
                            uint partner_15 = (simd_shuffle_xor((_S63), ushort((2U))));

#line 2384
                            if(_S55)
                            {

#line 2384
                                t_4[13U] = partner_15;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_4[15U] = partner_15;

#line 2384
                            }

#line 2384
                            uint i_3 = 0U;

#line 2384
                            for(;;)
                            {

#line 2384
                                if(i_3 < 16U)
                                {
                                }
                                else
                                {

#line 2384
                                    break;
                                }

#line 2384
                                _S36[i_3] = half2(as_type<half>(ushort((t_4[i_3]) & 65535U)), as_type<half>(ushort(((t_4[i_3]) >> 16U) & 65535U)));

#line 2384
                                i_3 = i_3 + 1U;

#line 2384
                            }

#line 2384
                            break;
                        }

#line 2384
                        uint _S64 = (&kernelContext_1)->_tid_0;

#line 2384
                        for(;;)
                        {

#line 2384
                            thread array<uint, int(16)> t_5;

#line 2384
                            uint r_1 = 0U;

#line 2384
                            for(;;)
                            {

#line 2384
                                if(r_1 < 4U)
                                {
                                }
                                else
                                {

#line 2384
                                    break;
                                }

#line 2384
                                j_0 = 0U;

#line 2384
                                for(;;)
                                {

#line 2384
                                    if(j_0 < 4U)
                                    {
                                    }
                                    else
                                    {

#line 2384
                                        break;
                                    }

#line 2384
                                    t_5[j_0 * 4U + r_1] = (uint(as_type<ushort>(_S37[r_1 * 4U + j_0][0U])) & 65535U) | (uint(as_type<ushort>(_S37[r_1 * 4U + j_0][1U])) << 16U);

#line 2384
                                    j_0 = j_0 + 1U;

#line 2384
                                }

#line 2384
                                r_1 = r_1 + 1U;

#line 2384
                            }

#line 2384
                            uint _S65 = _S64 & 3U;

#line 2384
                            bool _S66 = (_S65 & 1U) != 0U;

#line 2384
                            uint _S67;

#line 2384
                            if(_S66)
                            {

#line 2384
                                _S67 = t_5[0U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S67 = t_5[1U];

#line 2384
                            }

#line 2384
                            uint partner_16 = (simd_shuffle_xor((_S67), ushort((1U))));

#line 2384
                            if(_S66)
                            {

#line 2384
                                t_5[0U] = partner_16;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[1U] = partner_16;

#line 2384
                            }

#line 2384
                            uint _S68;

#line 2384
                            if(_S66)
                            {

#line 2384
                                _S68 = t_5[2U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S68 = t_5[3U];

#line 2384
                            }

#line 2384
                            uint partner_17 = (simd_shuffle_xor((_S68), ushort((1U))));

#line 2384
                            if(_S66)
                            {

#line 2384
                                t_5[2U] = partner_17;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[3U] = partner_17;

#line 2384
                            }

#line 2384
                            uint _S69;

#line 2384
                            if(_S66)
                            {

#line 2384
                                _S69 = t_5[4U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S69 = t_5[5U];

#line 2384
                            }

#line 2384
                            uint partner_18 = (simd_shuffle_xor((_S69), ushort((1U))));

#line 2384
                            if(_S66)
                            {

#line 2384
                                t_5[4U] = partner_18;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[5U] = partner_18;

#line 2384
                            }

#line 2384
                            uint _S70;

#line 2384
                            if(_S66)
                            {

#line 2384
                                _S70 = t_5[6U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S70 = t_5[7U];

#line 2384
                            }

#line 2384
                            uint partner_19 = (simd_shuffle_xor((_S70), ushort((1U))));

#line 2384
                            if(_S66)
                            {

#line 2384
                                t_5[6U] = partner_19;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[7U] = partner_19;

#line 2384
                            }

#line 2384
                            uint _S71;

#line 2384
                            if(_S66)
                            {

#line 2384
                                _S71 = t_5[8U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S71 = t_5[9U];

#line 2384
                            }

#line 2384
                            uint partner_20 = (simd_shuffle_xor((_S71), ushort((1U))));

#line 2384
                            if(_S66)
                            {

#line 2384
                                t_5[8U] = partner_20;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[9U] = partner_20;

#line 2384
                            }

#line 2384
                            uint _S72;

#line 2384
                            if(_S66)
                            {

#line 2384
                                _S72 = t_5[10U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S72 = t_5[11U];

#line 2384
                            }

#line 2384
                            uint partner_21 = (simd_shuffle_xor((_S72), ushort((1U))));

#line 2384
                            if(_S66)
                            {

#line 2384
                                t_5[10U] = partner_21;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[11U] = partner_21;

#line 2384
                            }

#line 2384
                            uint _S73;

#line 2384
                            if(_S66)
                            {

#line 2384
                                _S73 = t_5[12U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S73 = t_5[13U];

#line 2384
                            }

#line 2384
                            uint partner_22 = (simd_shuffle_xor((_S73), ushort((1U))));

#line 2384
                            if(_S66)
                            {

#line 2384
                                t_5[12U] = partner_22;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[13U] = partner_22;

#line 2384
                            }

#line 2384
                            uint _S74;

#line 2384
                            if(_S66)
                            {

#line 2384
                                _S74 = t_5[14U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S74 = t_5[15U];

#line 2384
                            }

#line 2384
                            uint partner_23 = (simd_shuffle_xor((_S74), ushort((1U))));

#line 2384
                            if(_S66)
                            {

#line 2384
                                t_5[14U] = partner_23;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[15U] = partner_23;

#line 2384
                            }

#line 2384
                            bool _S75 = (_S65 & 2U) != 0U;

#line 2384
                            uint _S76;

#line 2384
                            if(_S75)
                            {

#line 2384
                                _S76 = t_5[0U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S76 = t_5[2U];

#line 2384
                            }

#line 2384
                            uint partner_24 = (simd_shuffle_xor((_S76), ushort((2U))));

#line 2384
                            if(_S75)
                            {

#line 2384
                                t_5[0U] = partner_24;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[2U] = partner_24;

#line 2384
                            }

#line 2384
                            uint _S77;

#line 2384
                            if(_S75)
                            {

#line 2384
                                _S77 = t_5[1U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S77 = t_5[3U];

#line 2384
                            }

#line 2384
                            uint partner_25 = (simd_shuffle_xor((_S77), ushort((2U))));

#line 2384
                            if(_S75)
                            {

#line 2384
                                t_5[1U] = partner_25;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[3U] = partner_25;

#line 2384
                            }

#line 2384
                            uint _S78;

#line 2384
                            if(_S75)
                            {

#line 2384
                                _S78 = t_5[4U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S78 = t_5[6U];

#line 2384
                            }

#line 2384
                            uint partner_26 = (simd_shuffle_xor((_S78), ushort((2U))));

#line 2384
                            if(_S75)
                            {

#line 2384
                                t_5[4U] = partner_26;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[6U] = partner_26;

#line 2384
                            }

#line 2384
                            uint _S79;

#line 2384
                            if(_S75)
                            {

#line 2384
                                _S79 = t_5[5U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S79 = t_5[7U];

#line 2384
                            }

#line 2384
                            uint partner_27 = (simd_shuffle_xor((_S79), ushort((2U))));

#line 2384
                            if(_S75)
                            {

#line 2384
                                t_5[5U] = partner_27;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[7U] = partner_27;

#line 2384
                            }

#line 2384
                            uint _S80;

#line 2384
                            if(_S75)
                            {

#line 2384
                                _S80 = t_5[8U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S80 = t_5[10U];

#line 2384
                            }

#line 2384
                            uint partner_28 = (simd_shuffle_xor((_S80), ushort((2U))));

#line 2384
                            if(_S75)
                            {

#line 2384
                                t_5[8U] = partner_28;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[10U] = partner_28;

#line 2384
                            }

#line 2384
                            uint _S81;

#line 2384
                            if(_S75)
                            {

#line 2384
                                _S81 = t_5[9U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S81 = t_5[11U];

#line 2384
                            }

#line 2384
                            uint partner_29 = (simd_shuffle_xor((_S81), ushort((2U))));

#line 2384
                            if(_S75)
                            {

#line 2384
                                t_5[9U] = partner_29;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[11U] = partner_29;

#line 2384
                            }

#line 2384
                            uint _S82;

#line 2384
                            if(_S75)
                            {

#line 2384
                                _S82 = t_5[12U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S82 = t_5[14U];

#line 2384
                            }

#line 2384
                            uint partner_30 = (simd_shuffle_xor((_S82), ushort((2U))));

#line 2384
                            if(_S75)
                            {

#line 2384
                                t_5[12U] = partner_30;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[14U] = partner_30;

#line 2384
                            }

#line 2384
                            uint _S83;

#line 2384
                            if(_S75)
                            {

#line 2384
                                _S83 = t_5[13U];

#line 2384
                            }
                            else
                            {

#line 2384
                                _S83 = t_5[15U];

#line 2384
                            }

#line 2384
                            uint partner_31 = (simd_shuffle_xor((_S83), ushort((2U))));

#line 2384
                            if(_S75)
                            {

#line 2384
                                t_5[13U] = partner_31;

#line 2384
                            }
                            else
                            {

#line 2384
                                t_5[15U] = partner_31;

#line 2384
                            }

#line 2384
                            uint i_4 = 0U;

#line 2384
                            for(;;)
                            {

#line 2384
                                if(i_4 < 16U)
                                {
                                }
                                else
                                {

#line 2384
                                    break;
                                }

#line 2384
                                _S37[i_4] = half2(as_type<half>(ushort((t_5[i_4]) & 65535U)), as_type<half>(ushort(((t_5[i_4]) >> 16U) & 65535U)));

#line 2384
                                i_4 = i_4 + 1U;

#line 2384
                            }

#line 2384
                            break;
                        }

#line 2384
                        break;
                    }

#line 2384
                    break;
                }

#line 2384
                innermostS_0(&_S36, &_S37);

#line 2384
                uint spanA_0;

#line 2384
                uint spanB_0;

#line 2384
                uint i_5;

#line 2384
                uint ovAcc_0;

#line 2384
                uint ovAcc_1;

#line 2384
                uint ovAcc_2;

#line 2384
                uint bb_0;

#line 2384
                uint bb_1;

#line 2384
                bool infLocalA_0;

#line 2384
                bool infLocalB_0;

#line 2384
                bool hitLocalA_0;

#line 2384
                bool hitLocalB_0;

#line 2384
                bool hitA_0;

#line 2384
                bool hitB_0;

#line 2384
                float2 _S84;

#line 2384
                if(_S28 != 0U)
                {

#line 2384
                    float _S85 = (as_type<float>((_S28)));

#line 2384
                    for(;;)
                    {

#line 2384
                        uint _S86 = slotToIndex_0(_S20 * 16U);

#line 2384
                        uint _S87 = _S86 - _S23;

#line 2384
                        if(_S24 > _S23)
                        {

#line 2384
                            spanA_0 = _S24 - _S23;

#line 2384
                        }
                        else
                        {

#line 2384
                            spanA_0 = 0U;

#line 2384
                        }

#line 2384
                        uint _S88 = _S86 - _S25;

#line 2384
                        if(_S26 > _S25)
                        {

#line 2384
                            spanB_0 = _S26 - _S25;

#line 2384
                        }
                        else
                        {

#line 2384
                            spanB_0 = 0U;

#line 2384
                        }

#line 2384
                        half2 _S89 = half2(float2(0.0f) );

#line 2384
                        i_5 = 0U;

#line 2384
                        db_0 = _S89;

#line 2384
                        ovAcc_0 = 0U;

#line 2384
                        for(;;)
                        {

#line 2384
                            if(i_5 < 16U)
                            {
                            }
                            else
                            {

#line 2384
                                break;
                            }

#line 2384
                            uint si_0 = slotToIndex_0(i_5);

#line 2384
                            bool liveB_0 = (_S88 + si_0) < spanB_0;

#line 2384
                            half2 _S90 = _S36[i_5];

#line 2384
                            half2 _S91 = _S37[i_5];

#line 2384
                            half2 _S92 = mag2s_0(_S36[i_5], _S37[i_5]);

#line 2384
                            uint _S93 = (uint(as_type<ushort>(_S92[0U])) & 65535U) | (uint(as_type<ushort>(_S92[1U])) << 16U);

#line 2384
                            if((_S87 + si_0) < spanA_0)
                            {

#line 2384
                                ovAcc_1 = _S93 & 65535U;

#line 2384
                            }
                            else
                            {

#line 2384
                                ovAcc_1 = 0U;

#line 2384
                            }

#line 2384
                            if(liveB_0)
                            {

#line 2384
                                ovAcc_2 = _S93 & 4294901760U;

#line 2384
                            }
                            else
                            {

#line 2384
                                ovAcc_2 = 0U;

#line 2384
                            }

#line 2384
                            uint m_0 = ovAcc_1 | ovAcc_2;

#line 2384
                            half2 _S94 = max(db_0, half2(as_type<half>(ushort(m_0 & 65535U)), as_type<half>(ushort((m_0 >> 16U) & 65535U))));

#line 2384
                            uint ovAcc_3 = ovAcc_0 | (((((uint(as_type<ushort>(_S90[0U])) & 65535U) | (uint(as_type<ushort>(_S90[1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(_S91[0U])) & 65535U) | (uint(as_type<ushort>(_S91[1U])) << 16U)) & 2080406528U) + 67109888U));

#line 2384
                            i_5 = i_5 + 1U;

#line 2384
                            db_0 = _S94;

#line 2384
                            ovAcc_0 = ovAcc_3;

#line 2384
                        }

#line 2384
                        if(spanA_0 == 0U)
                        {

#line 2384
                            ovAcc_1 = ovAcc_0 & 4294934527U;

#line 2384
                        }
                        else
                        {

#line 2384
                            ovAcc_1 = ovAcc_0;

#line 2384
                        }

#line 2384
                        if(spanB_0 == 0U)
                        {

#line 2384
                            ovAcc_2 = ovAcc_1 & 2147483647U;

#line 2384
                        }
                        else
                        {

#line 2384
                            ovAcc_2 = ovAcc_1;

#line 2384
                        }

#line 2384
                        if(_S27 == 0U)
                        {

#line 2384
                            uint _S95 = (uint(as_type<ushort>(db_0[0U])) & 65535U) | (uint(as_type<ushort>(db_0[1U])) << 16U);

#line 2384
                            float thr2_0 = _S85 * _S85;

#line 2384
                            if((ovAcc_2 & 32768U) != 0U)
                            {

#line 2384
                                infLocalA_0 = true;

#line 2384
                            }
                            else
                            {

#line 2384
                                infLocalA_0 = (_S95 & 31744U) == 31744U;

#line 2384
                            }

#line 2384
                            if((ovAcc_2 & 2147483648U) != 0U)
                            {

#line 2384
                                infLocalB_0 = true;

#line 2384
                            }
                            else
                            {

#line 2384
                                infLocalB_0 = (_S95 & 2080374784U) == 2080374784U;

#line 2384
                            }

#line 2384
                            if(infLocalA_0)
                            {

#line 2384
                                hitLocalA_0 = true;

#line 2384
                            }
                            else
                            {

#line 2384
                                if((_S95 & 32767U) != 0U)
                                {

#line 2384
                                    hitLocalA_0 = float(db_0.x) >= thr2_0;

#line 2384
                                }
                                else
                                {

#line 2384
                                    hitLocalA_0 = false;

#line 2384
                                }

#line 2384
                            }

#line 2384
                            if(infLocalB_0)
                            {

#line 2384
                                hitLocalB_0 = true;

#line 2384
                            }
                            else
                            {

#line 2384
                                if((_S95 & 2147418112U) != 0U)
                                {

#line 2384
                                    hitLocalB_0 = float(db_0.y) >= thr2_0;

#line 2384
                                }
                                else
                                {

#line 2384
                                    hitLocalB_0 = false;

#line 2384
                                }

#line 2384
                            }

#line 2384
                            if(hitLocalA_0)
                            {

#line 2384
                                bb_0 = 1U;

#line 2384
                            }
                            else
                            {

#line 2384
                                bb_0 = 0U;

#line 2384
                            }

#line 2384
                            if(hitLocalB_0)
                            {

#line 2384
                                bb_1 = 2U;

#line 2384
                            }
                            else
                            {

#line 2384
                                bb_1 = 0U;

#line 2384
                            }

#line 2384
                            uint _S96 = bb_0 | bb_1;

#line 2384
                            uint _S97 = (simd_shuffle_xor((_S96), ushort((1U))));

#line 2384
                            uint hitBits_0 = _S96 | _S97;

#line 2384
                            uint _S98 = (simd_shuffle_xor((hitBits_0), ushort((2U))));

#line 2384
                            uint hitBits_1 = hitBits_0 | _S98;

#line 2384
                            if(_S20 == 0U)
                            {

#line 2384
                                if(_S21)
                                {

#line 2384
                                    packed_float2 device* _S99 = (&kernelContext_1)->entryPointParams_peakVal_0+pairA_0;

#line 2384
                                    if((hitBits_1 & 1U) != 0U)
                                    {

#line 2384
                                        _S84 = float2(3.40282306073709653e+38f, 0.0f);

#line 2384
                                    }
                                    else
                                    {

#line 2384
                                        _S84 = float2(0.0f, 0.0f);

#line 2384
                                    }

#line 2384
                                    *_S99 = packed_float2(_S84) ;

#line 2384
                                }

#line 2384
                                if(_S22)
                                {

#line 2384
                                    packed_float2 device* _S100 = (&kernelContext_1)->entryPointParams_peakVal_0+pairB_0;

#line 2384
                                    if((hitBits_1 & 2U) != 0U)
                                    {

#line 2384
                                        _S84 = float2(3.40282306073709653e+38f, 0.0f);

#line 2384
                                    }
                                    else
                                    {

#line 2384
                                        _S84 = float2(0.0f, 0.0f);

#line 2384
                                    }

#line 2384
                                    *_S100 = packed_float2(_S84) ;

#line 2384
                                }

#line 2384
                            }

#line 2384
                            break;
                        }

#line 2384
                        uint bb_2 = ((uint(as_type<ushort>(db_0[0U])) & 65535U) | (uint(as_type<ushort>(db_0[1U])) << 16U)) & 2147450879U;

#line 2384
                        if((ovAcc_2 & 32768U) != 0U)
                        {

#line 2384
                            bb_0 = (bb_2 & 4294901760U) | 31744U;

#line 2384
                        }
                        else
                        {

#line 2384
                            bb_0 = bb_2;

#line 2384
                        }

#line 2384
                        if((ovAcc_2 & 2147483648U) != 0U)
                        {

#line 2384
                            bb_1 = (bb_0 & 65535U) | 2080374784U;

#line 2384
                        }
                        else
                        {

#line 2384
                            bb_1 = bb_0;

#line 2384
                        }

#line 2384
                        uint other_0 = (simd_shuffle_xor((bb_1), ushort((1U))));

#line 2384
                        uint _S101 = (max(bb_1 & 65535U, other_0 & 65535U)) | (max(bb_1 & 4294901760U, other_0 & 4294901760U));

#line 2384
                        uint other_1 = (simd_shuffle_xor((_S101), ushort((2U))));

#line 2384
                        uint bb_3 = (max(_S101 & 65535U, other_1 & 65535U)) | (max(_S101 & 4294901760U, other_1 & 4294901760U));

#line 2384
                        if(_S20 == 0U)
                        {

#line 2384
                            bool infA_0 = (bb_3 & 31744U) == 31744U;

#line 2384
                            bool infB_0 = (bb_3 & 2080374784U) == 2080374784U;

#line 2384
                            float bA_0 = sqrt(float(as_type<half>(ushort(bb_3 & 65535U))));

#line 2384
                            float bB_0 = sqrt(float(as_type<half>(ushort((bb_3 >> 16U) & 65535U))));

#line 2384
                            if(infA_0)
                            {

#line 2384
                                hitA_0 = true;

#line 2384
                            }
                            else
                            {

#line 2384
                                if(bA_0 > 0.0f)
                                {

#line 2384
                                    infLocalA_0 = bA_0 >= _S85;

#line 2384
                                }
                                else
                                {

#line 2384
                                    infLocalA_0 = false;

#line 2384
                                }

#line 2384
                                hitA_0 = infLocalA_0;

#line 2384
                            }

#line 2384
                            if(infB_0)
                            {

#line 2384
                                hitB_0 = true;

#line 2384
                            }
                            else
                            {

#line 2384
                                if(bB_0 > 0.0f)
                                {

#line 2384
                                    infLocalA_0 = bB_0 >= _S85;

#line 2384
                                }
                                else
                                {

#line 2384
                                    infLocalA_0 = false;

#line 2384
                                }

#line 2384
                                hitB_0 = infLocalA_0;

#line 2384
                            }

#line 2384
                            if(_S21)
                            {

#line 2384
                                packed_float2 device* _S102 = (&kernelContext_1)->entryPointParams_peakVal_0+pairA_0;

#line 2384
                                if(infA_0)
                                {

#line 2384
                                    _S84 = float2(3.40282306073709653e+38f, 0.0f);

#line 2384
                                }
                                else
                                {

#line 2384
                                    if(hitA_0)
                                    {

#line 2384
                                        _S84 = float2(bA_0, 0.0f);

#line 2384
                                    }
                                    else
                                    {

#line 2384
                                        _S84 = float2(0.0f, 0.0f);

#line 2384
                                    }

#line 2384
                                }

#line 2384
                                *_S102 = packed_float2(_S84) ;

#line 2384
                            }

#line 2384
                            if(_S22)
                            {

#line 2384
                                packed_float2 device* _S103 = (&kernelContext_1)->entryPointParams_peakVal_0+pairB_0;

#line 2384
                                if(infB_0)
                                {

#line 2384
                                    _S84 = float2(3.40282306073709653e+38f, 0.0f);

#line 2384
                                }
                                else
                                {

#line 2384
                                    if(hitB_0)
                                    {

#line 2384
                                        _S84 = float2(bB_0, 0.0f);

#line 2384
                                    }
                                    else
                                    {

#line 2384
                                        _S84 = float2(0.0f, 0.0f);

#line 2384
                                    }

#line 2384
                                }

#line 2384
                                *_S103 = packed_float2(_S84) ;

#line 2384
                            }

#line 2384
                        }

#line 2384
                        break;
                    }

#line 2384
                }
                else
                {

#line 2384
                    array<half2, int(16)> _S104 = _S36;

#line 2384
                    array<half2, int(16)> _S105 = _S37;

#line 2384
                    for(;;)
                    {

#line 2384
                        uint _S106 = slotToIndex_0(_S20 * 16U);

#line 2384
                        uint _S107 = _S106 - _S23;

#line 2384
                        if(_S24 > _S23)
                        {

#line 2384
                            spanA_0 = _S24 - _S23;

#line 2384
                        }
                        else
                        {

#line 2384
                            spanA_0 = 0U;

#line 2384
                        }

#line 2384
                        uint _S108 = _S106 - _S25;

#line 2384
                        if(_S26 > _S25)
                        {

#line 2384
                            spanB_0 = _S26 - _S25;

#line 2384
                        }
                        else
                        {

#line 2384
                            spanB_0 = 0U;

#line 2384
                        }

#line 2384
                        i_5 = 0U;

#line 2384
                        ovAcc_0 = 0U;

#line 2384
                        ovAcc_1 = 0U;

#line 2384
                        ovAcc_2 = 0U;

#line 2384
                        for(;;)
                        {

#line 2384
                            if(i_5 < 16U)
                            {
                            }
                            else
                            {

#line 2384
                                break;
                            }

#line 2384
                            uint si_1 = slotToIndex_0(i_5);

#line 2384
                            bool liveB_1 = (_S108 + si_1) < spanB_0;

#line 2384
                            half2 mg_0 = mag2s_0(_S104[i_5], _S105[i_5]);

#line 2384
                            uint _S109 = (uint(as_type<ushort>(mg_0[0U])) & 65535U) | (uint(as_type<ushort>(mg_0[1U])) << 16U);

#line 2384
                            uint ovAcc_4 = ovAcc_0 | (((((uint(as_type<ushort>(_S104[i_5][0U])) & 65535U) | (uint(as_type<ushort>(_S104[i_5][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(_S105[i_5][0U])) & 65535U) | (uint(as_type<ushort>(_S105[i_5][1U])) << 16U)) & 2080406528U) + 67109888U));

#line 2384
                            if((_S107 + si_1) < spanA_0)
                            {

#line 2384
                                bb_0 = _S109 << 16U;

#line 2384
                            }
                            else
                            {

#line 2384
                                bb_0 = 0U;

#line 2384
                            }

#line 2384
                            uint _S110 = 15U - i_5;

#line 2384
                            uint _S111 = max(ovAcc_1, bb_0 | _S110);

#line 2384
                            if(liveB_1)
                            {

#line 2384
                                bb_1 = _S109 & 4294901760U;

#line 2384
                            }
                            else
                            {

#line 2384
                                bb_1 = 0U;

#line 2384
                            }

#line 2384
                            uint _S112 = max(ovAcc_2, bb_1 | _S110);

#line 2384
                            i_5 = i_5 + 1U;

#line 2384
                            ovAcc_0 = ovAcc_4;

#line 2384
                            ovAcc_1 = _S111;

#line 2384
                            ovAcc_2 = _S112;

#line 2384
                        }

#line 2384
                        bool _S113 = spanA_0 != 0U;

#line 2384
                        if(_S113)
                        {

#line 2384
                            infLocalA_0 = (ovAcc_0 & 32768U) != 0U;

#line 2384
                        }
                        else
                        {

#line 2384
                            infLocalA_0 = false;

#line 2384
                        }

#line 2384
                        if(infLocalA_0)
                        {

#line 2384
                            bb_0 = max(ovAcc_1, 2080374799U);

#line 2384
                        }
                        else
                        {

#line 2384
                            bb_0 = ovAcc_1;

#line 2384
                        }

#line 2384
                        bool _S114 = spanB_0 != 0U;

#line 2384
                        if(_S114)
                        {

#line 2384
                            infLocalB_0 = (ovAcc_0 & 2147483648U) != 0U;

#line 2384
                        }
                        else
                        {

#line 2384
                            infLocalB_0 = false;

#line 2384
                        }

#line 2384
                        if(infLocalB_0)
                        {

#line 2384
                            bb_1 = max(ovAcc_2, 2080374799U);

#line 2384
                        }
                        else
                        {

#line 2384
                            bb_1 = ovAcc_2;

#line 2384
                        }

#line 2384
                        uint _S115 = (4095U - _S20) << 4U;

#line 2384
                        uint kA_0 = bb_0 | _S115;

#line 2384
                        uint kB_0 = bb_1 | _S115;

#line 2384
                        uint _S116 = (simd_shuffle_xor((kA_0), ushort((1U))));

#line 2384
                        uint _S117 = max(kA_0, _S116);

#line 2384
                        uint _S118 = (simd_shuffle_xor((kB_0), ushort((1U))));

#line 2384
                        uint _S119 = max(kB_0, _S118);

#line 2384
                        uint _S120 = (simd_shuffle_xor((_S117), ushort((2U))));

#line 2384
                        uint _S121 = max(_S117, _S120);

#line 2384
                        uint _S122 = (simd_shuffle_xor((_S119), ushort((2U))));

#line 2384
                        uint _S123 = max(_S119, _S122);

#line 2384
                        uint slotA_0 = 65535U - (_S121 & 65535U);

#line 2384
                        uint slotB_0 = 65535U - (_S123 & 65535U);

#line 2384
                        if(_S113)
                        {

#line 2384
                            hitLocalA_0 = (_S121 >> 16U) >= 31744U;

#line 2384
                        }
                        else
                        {

#line 2384
                            hitLocalA_0 = false;

#line 2384
                        }

#line 2384
                        if(_S114)
                        {

#line 2384
                            hitLocalB_0 = (_S123 >> 16U) >= 31744U;

#line 2384
                        }
                        else
                        {

#line 2384
                            hitLocalB_0 = false;

#line 2384
                        }

#line 2384
                        if(hitLocalA_0)
                        {

#line 2384
                            hitA_0 = true;

#line 2384
                        }
                        else
                        {

#line 2384
                            hitA_0 = (as_type<half>((ushort)((_S121 >> 16U)))) > (as_type<float>((_S28)));

#line 2384
                        }

#line 2384
                        if(hitLocalB_0)
                        {

#line 2384
                            hitB_0 = true;

#line 2384
                        }
                        else
                        {

#line 2384
                            hitB_0 = (as_type<half>((ushort)((_S123 >> 16U)))) > (as_type<float>((_S28)));

#line 2384
                        }

#line 2384
                        uint wA_0 = slotA_0 >> 4U;

#line 2384
                        uint _S124 = slotA_0 & 15U;

#line 2384
                        uint wB_0 = slotB_0 >> 4U;

#line 2384
                        uint _S125 = slotB_0 & 15U;

#line 2384
                        half2 _S126 = half2(float2(0.0f) );

#line 2384
                        j_0 = 0U;

#line 2384
                        db_0 = _S126;

#line 2384
                        half2 selB_0 = _S126;

#line 2384
                        for(;;)
                        {

#line 2384
                            if(j_0 < 16U)
                            {
                            }
                            else
                            {

#line 2384
                                break;
                            }

#line 2384
                            if(j_0 == _S124)
                            {

#line 2384
                                db_0 = half2(_S104[j_0].x, _S105[j_0].x);

#line 2384
                            }

#line 2384
                            if(j_0 == _S125)
                            {

#line 2384
                                selB_0 = half2(_S104[j_0].y, _S105[j_0].y);

#line 2384
                            }

#line 2384
                            j_0 = j_0 + 1U;

#line 2384
                        }

#line 2384
                        uint _S127 = (simd_shuffle_xor(((uint(as_type<ushort>(db_0[0U])) & 65535U) | (uint(as_type<ushort>(db_0[1U])) << 16U)), ushort((wA_0))));

#line 2384
                        half _S128 = as_type<half>(ushort(_S127 & 65535U));

#line 2384
                        half _S129 = as_type<half>(ushort((_S127 >> 16U) & 65535U));

#line 2384
                        uint _S130 = (simd_shuffle_xor(((uint(as_type<ushort>(selB_0[0U])) & 65535U) | (uint(as_type<ushort>(selB_0[1U])) << 16U)), ushort((wB_0))));

#line 2384
                        half _S131 = as_type<half>(ushort(_S130 & 65535U));

#line 2384
                        half _S132 = as_type<half>(ushort((_S130 >> 16U) & 65535U));

#line 2384
                        bool _S133 = _S20 == 0U;

#line 2384
                        bool _S134;

#line 2384
                        if(_S133)
                        {

#line 2384
                            _S134 = _S21;

#line 2384
                        }
                        else
                        {

#line 2384
                            _S134 = false;

#line 2384
                        }

#line 2384
                        int _S135;

#line 2384
                        if(_S134)
                        {

#line 2384
                            int device* _S136 = (&kernelContext_1)->entryPointParams_peakIdx_0+pairA_0;

#line 2384
                            if(hitA_0)
                            {

#line 2384
                                _S135 = int(slotToIndex_0(slotA_0));

#line 2384
                            }
                            else
                            {

#line 2384
                                _S135 = int(-1);

#line 2384
                            }

#line 2384
                            *_S136 = _S135;

#line 2384
                            packed_float2 device* _S137 = (&kernelContext_1)->entryPointParams_peakVal_0+pairA_0;

#line 2384
                            if(hitLocalA_0)
                            {

#line 2384
                                _S84 = float2(3.40282306073709653e+38f, 0.0f);

#line 2384
                            }
                            else
                            {

#line 2384
                                if(hitA_0)
                                {

#line 2384
                                    _S84 = float2(float(_S128), float(_S129));

#line 2384
                                }
                                else
                                {

#line 2384
                                    _S84 = float2(0.0f, 0.0f);

#line 2384
                                }

#line 2384
                            }

#line 2384
                            *_S137 = packed_float2(_S84) ;

#line 2384
                        }

#line 2384
                        bool _S138;

#line 2384
                        if(_S133)
                        {

#line 2384
                            _S138 = _S22;

#line 2384
                        }
                        else
                        {

#line 2384
                            _S138 = false;

#line 2384
                        }

#line 2384
                        if(_S138)
                        {

#line 2384
                            int device* _S139 = (&kernelContext_1)->entryPointParams_peakIdx_0+pairB_0;

#line 2384
                            if(hitB_0)
                            {

#line 2384
                                _S135 = int(slotToIndex_0(slotB_0));

#line 2384
                            }
                            else
                            {

#line 2384
                                _S135 = int(-1);

#line 2384
                            }

#line 2384
                            *_S139 = _S135;

#line 2384
                            packed_float2 device* _S140 = (&kernelContext_1)->entryPointParams_peakVal_0+pairB_0;

#line 2384
                            if(hitLocalB_0)
                            {

#line 2384
                                _S84 = float2(3.40282306073709653e+38f, 0.0f);

#line 2384
                            }
                            else
                            {

#line 2384
                                if(hitB_0)
                                {

#line 2384
                                    _S84 = float2(float(_S131), float(_S132));

#line 2384
                                }
                                else
                                {

#line 2384
                                    _S84 = float2(0.0f, 0.0f);

#line 2384
                                }

#line 2384
                            }

#line 2384
                            *_S140 = packed_float2(_S84) ;

#line 2384
                        }

#line 2384
                        break;
                    }

#line 2384
                }

#line 2384
                break;
            }

#line 2384
            break;
        }

#line 2372
        base_0 = base_0 + (&kernelContext_1)->entryPointParams_0->gridSize_0 * 32U;

#line 2372
    }

#line 2401
    return;
}
