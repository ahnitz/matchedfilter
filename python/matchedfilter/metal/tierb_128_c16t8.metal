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

#line 10 "mm_128_fusedTierB_c16t8.slang"
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
};


#line 202 "mm_128_fusedTierB_c16t8.slang"
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
    uint _S2 = mfRowWindowsFlag_0();

#line 232 "mm_128_fusedTierB_c16t8.slang"
    if(_S2 == 0U)
    {

#line 232
        return;
    }

#line 233
    uint _S3 = 3U * d_0;

#line 233
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


#line 171 "mm_128_fusedTierB_c16t8.slang"
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
    uint _S6 = mfDataStrideFlag_0();

#line 265 "mm_128_fusedTierB_c16t8.slang"
    if(_S6 != 0U)
    {

#line 73 "twiddle.slang"
        uint _S7 = mfDataScaleFlag_0();

#line 266 "mm_128_fusedTierB_c16t8.slang"
        float s_0 = (as_type<float>((_S7)));
        uint _S8 = 2U * i_1;

#line 267
        return half2(half((as_type<float>((b_1[_S8]))) * s_0), half((as_type<float>((b_1[_S8 + 1U]))) * s_0));
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


#line 390
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 390
    half2 _S9 = half2(wr_0) ;

#line 390
    half2 _S10 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S10 + *xi_0 * _S9;
    *xr_0 = *xr_0 * _S9 - *xi_0 * _S10;

#line 394
    *xi_0 = ni_0;
    return;
}


#line 424
void swap2_0(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint p_1, uint q_0)
{

    half2 t_0 = (*re_1)[p_1];

#line 427
    (*re_1)[p_1] = (*re_1)[q_0];

#line 427
    (*re_1)[q_0] = t_0;
    half2 t_1 = (*im_1)[p_1];

#line 428
    (*im_1)[p_1] = (*im_1)[q_0];

#line 428
    (*im_1)[q_0] = t_1;
    return;
}


#line 462
void dft16s_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2)
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
        r4s_0(re_2, im_2, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 464
        n1_0 = n1_0 + 1U;

#line 464
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
        uint _S11 = 4U * k2_0;

#line 477
        r4s_0(re_2, im_2, _S11, _S11 + 1U, _S11 + 2U, _S11 + 3U);

#line 476
        k2_0 = k2_0 + 1U;

#line 476
    }

    swap2_0(re_2, im_2, 1U, 4U);

#line 478
    swap2_0(re_2, im_2, 2U, 8U);

#line 478
    swap2_0(re_2, im_2, 3U, 12U);
    swap2_0(re_2, im_2, 6U, 9U);

#line 479
    swap2_0(re_2, im_2, 7U, 13U);

#line 479
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


#line 444 "mm_128_fusedTierB_c16t8.slang"
void dft8s_0(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint o_0)
{
    thread array<half2, int(8)> br_1;

#line 446
    thread array<half2, int(8)> bi_1;

#line 446
    uint s_2 = 1U;
    for(;;)
    {

#line 447
        if(s_2 < 8U)
        {
        }
        else
        {

#line 447
            break;
        }

#line 447
        uint j_0 = 0U;
        for(;;)
        {

#line 448
            if(j_0 < 4U)
            {
            }
            else
            {

#line 448
                break;
            }

#line 449
            uint k_0 = j_0 & (s_2 - 1U);

#line 449
            uint base_0 = (j_0 - k_0) << 1U;
            float ang_0 = 3.14159274101257324f * float(k_0) / float(s_2);
            uint _S16 = o_0 + j_0;

#line 451
            uint _S17 = _S16 + 4U;

#line 451
            thread half2 vr_0 = (*re_3)[_S17];

#line 451
            thread half2 vi_0 = (*im_3)[_S17];
            float2 tw_0 = mfTwiddle_0(ang_0);
            cmulw_0(&vr_0, &vi_0, half(tw_0.x), half(tw_0.y));

            uint _S18 = base_0 + k_0;

#line 455
            br_1[_S18] = (*re_3)[_S16] + vr_0;

#line 455
            bi_1[_S18] = (*im_3)[_S16] + vi_0;
            uint _S19 = _S18 + s_2;

#line 456
            br_1[_S19] = (*re_3)[_S16] - vr_0;

#line 456
            bi_1[_S19] = (*im_3)[_S16] - vi_0;

#line 448
            j_0 = j_0 + 1U;

#line 448
        }

#line 448
        uint i_2 = 0U;

#line 458
        for(;;)
        {

#line 458
            if(i_2 < 8U)
            {
            }
            else
            {

#line 458
                break;
            }

#line 458
            uint _S20 = o_0 + i_2;

#line 458
            (*re_3)[_S20] = br_1[i_2];

#line 458
            (*im_3)[_S20] = bi_1[i_2];

#line 458
            i_2 = i_2 + 1U;

#line 458
        }

#line 447
        s_2 = s_2 << 1U;

#line 447
    }

#line 460
    return;
}


#line 606
void innermostS_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4)
{

#line 606
    uint b_3 = 0U;


    for(;;)
    {

#line 609
        if(b_3 < 2U)
        {
        }
        else
        {

#line 609
            break;
        }

#line 609
        dft8s_0(re_4, im_4, b_3 * 8U);

#line 609
        b_3 = b_3 + 1U;

#line 609
    }


    return;
}


#line 882
uint lgOf_0(uint i_3)
{

#line 882
    uint _S21;

#line 882
    if(i_3 < 1U)
    {

#line 882
        _S21 = 4U;

#line 882
    }
    else
    {

#line 882
        if(i_3 == 1U)
        {

#line 882
            _S21 = 3U;

#line 882
        }
        else
        {

#line 882
            _S21 = 1U;

#line 882
        }

#line 882
    }

#line 882
    return _S21;
}


#line 884
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 888
    uint lg_1 = lgOf_0(0U);

#line 893
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 486
half2 mag2s_0(half2 re_5, half2 im_5)
{

#line 486
    return re_5 * re_5 + im_5 * im_5;
}


#line 1817
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1817
    uint j_1;

#line 1817
    uint m_0;

#line 1817
    thread KernelContext_0 kernelContext_1;

#line 1817
    (&kernelContext_1)->entryPointParams_0 = entryPointParams_1;

#line 1817
    (&kernelContext_1)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1817
    (&kernelContext_1)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1817
    (&kernelContext_1)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1817
    (&kernelContext_1)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1817
    (&kernelContext_1)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1817
    (&kernelContext_1)->_binPhase_0 = 0U;

#line 1835
    uint _pr_0 = gid_0.x;

#line 1835
    uint _t_0 = lid_0.x;
    (&kernelContext_1)->_stgBase_0 = 0U;

#line 1836
    uint _S22 = entryPointParams_1->ntmpl_0;

#line 1836
    uint _S23 = entryPointParams_1->winStart_0;

#line 1836
    uint _S24 = entryPointParams_1->winEnd_0;

#line 1836
    uint _S25 = entryPointParams_1->binsize_0;

#line 1836
    uint _S26 = entryPointParams_1->nbins_0;

#line 1836
    uint _S27 = entryPointParams_1->thrBits_0;

#line 1850
    for(;;)
    {

#line 1850
        thread uint _S28 = _S23;

#line 1850
        thread uint _S29 = _S24;

#line 1850
        (&kernelContext_1)->_tid_0 = _t_0;

#line 1850
        uint tiles_0 = (_S22 + 8U - 1U) / 8U;

#line 1850
        uint slots_0 = _S25 * tiles_0;

#line 1850
        bool slotOk_0 = _pr_0 < slots_0;

#line 1850
        uint q_1;

#line 1850
        if(slotOk_0)
        {

#line 1850
            q_1 = _pr_0;

#line 1850
        }
        else
        {

#line 1850
            q_1 = slots_0 - 1U;

#line 1850
        }

#line 1850
        uint d_2 = q_1 / tiles_0;

#line 1850
        uint t0_0 = (q_1 - d_2 * tiles_0) * 8U;

#line 1850
        uint _S30 = d_2 * _S22 + t0_0;

#line 1850
        rowWindow_0(d_2, &_S28, &_S29, (&kernelContext_1)->entryPointParams_rowWin_0, &kernelContext_1);

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
            uint _S31 = mfDataStrideFlag_0();

#line 1850
            if(_S31 != 0U)
            {

#line 1850
                uint _S32 = mfDataStrideFlag_0();

#line 1850
                q_1 = _S32;

#line 1850
            }
            else
            {

#line 1850
                q_1 = 128U;

#line 1850
            }

#line 1850
            half2 _S33 = dload_0((&kernelContext_1)->entryPointParams_data_0, d_2 * q_1 + _t_0 + 8U * n2_0);

#line 1850
            dreg_0[n2_0] = _S33;

#line 1850
            n2_0 = n2_0 + 1U;

#line 1850
        }

#line 1850
        uint k_1 = 0U;

#line 1850
        for(;;)
        {

#line 1850
            if(k_1 < 8U)
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
                okA_0 = (t0_0 + k_1) < _S22;

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
                okB_0 = (t0_0 + k_1 + 1U) < _S22;

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
                q_1 = _S30 + k_1;

#line 1850
            }
            else
            {

#line 1850
                q_1 = 4294967295U;

#line 1850
            }

#line 1850
            if(okB_0)
            {

#line 1850
                n2_0 = _S30 + k_1 + 1U;

#line 1850
            }
            else
            {

#line 1850
                n2_0 = 4294967295U;

#line 1850
            }

#line 1850
            uint _S34 = t0_0 + k_1;

#line 1850
            uint _S35 = _S22 - 1U;

#line 1850
            uint _S36 = min(_S34, _S35);

#line 1850
            uint _S37 = min(_S34 + 1U, _S35);

#line 1850
            array<half2, int(16)> _S38 = dreg_0;

#line 1850
            uint _S39 = _S28;

#line 1850
            uint _S40 = _S29;

#line 1850
            for(;;)
            {

#line 1850
                thread array<half2, int(16)> re_6;

#line 1850
                thread array<half2, int(16)> im_6;

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
                    uint _S41 = 8U * n2_1;

#line 1850
                    half2 ta_0 = cload_0((&kernelContext_1)->entryPointParams_tmpl_0, _S36 * 128U + _t_0 + _S41);

#line 1850
                    half2 tb_0 = cload_0((&kernelContext_1)->entryPointParams_tmpl_0, _S37 * 128U + _t_0 + _S41);

#line 1850
                    half _S42 = _S38[n2_1].x;

#line 1850
                    half _S43 = _S38[n2_1].y;

#line 1850
                    cmulconjs_0(half2(_S42, _S42), half2(_S43, _S43), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_6[n2_1], &im_6[n2_1]);

#line 1850
                    n2_1 = n2_1 + 1U;

#line 1850
                }

#line 1850
                for(;;)
                {

#line 1850
                    uint lane_0 = _t_0 & 7U;

#line 1850
                    dft16s_0(&re_6, &im_6);

#line 1850
                    uint _S44 = mfCoarseTwtFlag_0();

#line 1850
                    uint r_0;

#line 1850
                    if(_S44 != 0U)
                    {

#line 1850
                        r_0 = 0U;

#line 1850
                        for(;;)
                        {

#line 1850
                            if(r_0 < 16U)
                            {
                            }
                            else
                            {

#line 1850
                                break;
                            }

#line 1850
                            uint _S45 = lane_0 * 16U + r_0;

#line 1850
                            cmulw_0(&re_6[r_0], &im_6[r_0], as_type<half>(ushort((COARSE_TWT_DATA_0[_S45]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S45]) >> 16U) & 65535U)));

#line 1850
                            r_0 = r_0 + 1U;

#line 1850
                        }

#line 1850
                    }
                    else
                    {

#line 1850
                        float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_0) / 128.0f);

#line 1850
                        float _S46 = tw_1.x;

#line 1850
                        float _S47 = tw_1.y;

#line 1850
                        r_0 = 0U;

#line 1850
                        float cr_0 = 1.0f;

#line 1850
                        float ci_0 = 0.0f;

#line 1850
                        for(;;)
                        {

#line 1850
                            if(r_0 < 16U)
                            {
                            }
                            else
                            {

#line 1850
                                break;
                            }

#line 1850
                            cmulw_0(&re_6[r_0], &im_6[r_0], half(cr_0), half(ci_0));

#line 1850
                            float nr_0 = cr_0 * _S46 - ci_0 * _S47;

#line 1850
                            float _S48 = cr_0 * _S47 + ci_0 * _S46;

#line 1850
                            r_0 = r_0 + 1U;

#line 1850
                            cr_0 = nr_0;

#line 1850
                            ci_0 = _S48;

#line 1850
                        }

#line 1850
                    }

#line 1850
                    uint per_0 = 16U / max(8U, 1U);

#line 1850
                    uint _S49 = max(0U, 1U);

#line 1850
                    uint blk2_0 = _t_0 / _S49;

#line 1850
                    uint lane2_0 = _t_0 % _S49;

#line 1850
                    for(;;)
                    {

#line 1850
                        uint _S50 = (&kernelContext_1)->_tid_0;

#line 1850
                        for(;;)
                        {

#line 1850
                            thread array<uint, int(16)> t_2;

#line 1850
                            r_0 = 0U;

#line 1850
                            for(;;)
                            {

#line 1850
                                if(r_0 < 8U)
                                {
                                }
                                else
                                {

#line 1850
                                    break;
                                }

#line 1850
                                j_1 = 0U;

#line 1850
                                for(;;)
                                {

#line 1850
                                    if(j_1 < 2U)
                                    {
                                    }
                                    else
                                    {

#line 1850
                                        break;
                                    }

#line 1850
                                    t_2[j_1 * 8U + r_0] = (uint(as_type<ushort>(re_6[r_0 * 2U + j_1][0U])) & 65535U) | (uint(as_type<ushort>(re_6[r_0 * 2U + j_1][1U])) << 16U);

#line 1850
                                    j_1 = j_1 + 1U;

#line 1850
                                }

#line 1850
                                r_0 = r_0 + 1U;

#line 1850
                            }

#line 1850
                            uint _S51 = _S50 & 7U;

#line 1850
                            bool _S52 = (_S51 & 1U) != 0U;

#line 1850
                            uint _S53;

#line 1850
                            if(_S52)
                            {

#line 1850
                                _S53 = t_2[0U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S53 = t_2[1U];

#line 1850
                            }

#line 1850
                            uint partner_0 = (simd_shuffle_xor((_S53), ushort((1U))));

#line 1850
                            if(_S52)
                            {

#line 1850
                                t_2[0U] = partner_0;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[1U] = partner_0;

#line 1850
                            }

#line 1850
                            uint _S54;

#line 1850
                            if(_S52)
                            {

#line 1850
                                _S54 = t_2[2U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S54 = t_2[3U];

#line 1850
                            }

#line 1850
                            uint partner_1 = (simd_shuffle_xor((_S54), ushort((1U))));

#line 1850
                            if(_S52)
                            {

#line 1850
                                t_2[2U] = partner_1;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[3U] = partner_1;

#line 1850
                            }

#line 1850
                            uint _S55;

#line 1850
                            if(_S52)
                            {

#line 1850
                                _S55 = t_2[4U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S55 = t_2[5U];

#line 1850
                            }

#line 1850
                            uint partner_2 = (simd_shuffle_xor((_S55), ushort((1U))));

#line 1850
                            if(_S52)
                            {

#line 1850
                                t_2[4U] = partner_2;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[5U] = partner_2;

#line 1850
                            }

#line 1850
                            uint _S56;

#line 1850
                            if(_S52)
                            {

#line 1850
                                _S56 = t_2[6U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S56 = t_2[7U];

#line 1850
                            }

#line 1850
                            uint partner_3 = (simd_shuffle_xor((_S56), ushort((1U))));

#line 1850
                            if(_S52)
                            {

#line 1850
                                t_2[6U] = partner_3;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[7U] = partner_3;

#line 1850
                            }

#line 1850
                            uint _S57;

#line 1850
                            if(_S52)
                            {

#line 1850
                                _S57 = t_2[8U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S57 = t_2[9U];

#line 1850
                            }

#line 1850
                            uint partner_4 = (simd_shuffle_xor((_S57), ushort((1U))));

#line 1850
                            if(_S52)
                            {

#line 1850
                                t_2[8U] = partner_4;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[9U] = partner_4;

#line 1850
                            }

#line 1850
                            uint _S58;

#line 1850
                            if(_S52)
                            {

#line 1850
                                _S58 = t_2[10U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S58 = t_2[11U];

#line 1850
                            }

#line 1850
                            uint partner_5 = (simd_shuffle_xor((_S58), ushort((1U))));

#line 1850
                            if(_S52)
                            {

#line 1850
                                t_2[10U] = partner_5;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[11U] = partner_5;

#line 1850
                            }

#line 1850
                            uint _S59;

#line 1850
                            if(_S52)
                            {

#line 1850
                                _S59 = t_2[12U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S59 = t_2[13U];

#line 1850
                            }

#line 1850
                            uint partner_6 = (simd_shuffle_xor((_S59), ushort((1U))));

#line 1850
                            if(_S52)
                            {

#line 1850
                                t_2[12U] = partner_6;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[13U] = partner_6;

#line 1850
                            }

#line 1850
                            uint _S60;

#line 1850
                            if(_S52)
                            {

#line 1850
                                _S60 = t_2[14U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S60 = t_2[15U];

#line 1850
                            }

#line 1850
                            uint partner_7 = (simd_shuffle_xor((_S60), ushort((1U))));

#line 1850
                            if(_S52)
                            {

#line 1850
                                t_2[14U] = partner_7;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[15U] = partner_7;

#line 1850
                            }

#line 1850
                            bool _S61 = (_S51 & 2U) != 0U;

#line 1850
                            uint _S62;

#line 1850
                            if(_S61)
                            {

#line 1850
                                _S62 = t_2[0U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S62 = t_2[2U];

#line 1850
                            }

#line 1850
                            uint partner_8 = (simd_shuffle_xor((_S62), ushort((2U))));

#line 1850
                            if(_S61)
                            {

#line 1850
                                t_2[0U] = partner_8;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[2U] = partner_8;

#line 1850
                            }

#line 1850
                            uint _S63;

#line 1850
                            if(_S61)
                            {

#line 1850
                                _S63 = t_2[1U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S63 = t_2[3U];

#line 1850
                            }

#line 1850
                            uint partner_9 = (simd_shuffle_xor((_S63), ushort((2U))));

#line 1850
                            if(_S61)
                            {

#line 1850
                                t_2[1U] = partner_9;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[3U] = partner_9;

#line 1850
                            }

#line 1850
                            uint _S64;

#line 1850
                            if(_S61)
                            {

#line 1850
                                _S64 = t_2[4U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S64 = t_2[6U];

#line 1850
                            }

#line 1850
                            uint partner_10 = (simd_shuffle_xor((_S64), ushort((2U))));

#line 1850
                            if(_S61)
                            {

#line 1850
                                t_2[4U] = partner_10;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[6U] = partner_10;

#line 1850
                            }

#line 1850
                            uint _S65;

#line 1850
                            if(_S61)
                            {

#line 1850
                                _S65 = t_2[5U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S65 = t_2[7U];

#line 1850
                            }

#line 1850
                            uint partner_11 = (simd_shuffle_xor((_S65), ushort((2U))));

#line 1850
                            if(_S61)
                            {

#line 1850
                                t_2[5U] = partner_11;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[7U] = partner_11;

#line 1850
                            }

#line 1850
                            uint _S66;

#line 1850
                            if(_S61)
                            {

#line 1850
                                _S66 = t_2[8U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S66 = t_2[10U];

#line 1850
                            }

#line 1850
                            uint partner_12 = (simd_shuffle_xor((_S66), ushort((2U))));

#line 1850
                            if(_S61)
                            {

#line 1850
                                t_2[8U] = partner_12;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[10U] = partner_12;

#line 1850
                            }

#line 1850
                            uint _S67;

#line 1850
                            if(_S61)
                            {

#line 1850
                                _S67 = t_2[9U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S67 = t_2[11U];

#line 1850
                            }

#line 1850
                            uint partner_13 = (simd_shuffle_xor((_S67), ushort((2U))));

#line 1850
                            if(_S61)
                            {

#line 1850
                                t_2[9U] = partner_13;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[11U] = partner_13;

#line 1850
                            }

#line 1850
                            uint _S68;

#line 1850
                            if(_S61)
                            {

#line 1850
                                _S68 = t_2[12U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S68 = t_2[14U];

#line 1850
                            }

#line 1850
                            uint partner_14 = (simd_shuffle_xor((_S68), ushort((2U))));

#line 1850
                            if(_S61)
                            {

#line 1850
                                t_2[12U] = partner_14;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[14U] = partner_14;

#line 1850
                            }

#line 1850
                            uint _S69;

#line 1850
                            if(_S61)
                            {

#line 1850
                                _S69 = t_2[13U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S69 = t_2[15U];

#line 1850
                            }

#line 1850
                            uint partner_15 = (simd_shuffle_xor((_S69), ushort((2U))));

#line 1850
                            if(_S61)
                            {

#line 1850
                                t_2[13U] = partner_15;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[15U] = partner_15;

#line 1850
                            }

#line 1850
                            bool _S70 = (_S51 & 4U) != 0U;

#line 1850
                            uint _S71;

#line 1850
                            if(_S70)
                            {

#line 1850
                                _S71 = t_2[0U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S71 = t_2[4U];

#line 1850
                            }

#line 1850
                            uint partner_16 = (simd_shuffle_xor((_S71), ushort((4U))));

#line 1850
                            if(_S70)
                            {

#line 1850
                                t_2[0U] = partner_16;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[4U] = partner_16;

#line 1850
                            }

#line 1850
                            uint _S72;

#line 1850
                            if(_S70)
                            {

#line 1850
                                _S72 = t_2[1U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S72 = t_2[5U];

#line 1850
                            }

#line 1850
                            uint partner_17 = (simd_shuffle_xor((_S72), ushort((4U))));

#line 1850
                            if(_S70)
                            {

#line 1850
                                t_2[1U] = partner_17;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[5U] = partner_17;

#line 1850
                            }

#line 1850
                            uint _S73;

#line 1850
                            if(_S70)
                            {

#line 1850
                                _S73 = t_2[2U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S73 = t_2[6U];

#line 1850
                            }

#line 1850
                            uint partner_18 = (simd_shuffle_xor((_S73), ushort((4U))));

#line 1850
                            if(_S70)
                            {

#line 1850
                                t_2[2U] = partner_18;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[6U] = partner_18;

#line 1850
                            }

#line 1850
                            uint _S74;

#line 1850
                            if(_S70)
                            {

#line 1850
                                _S74 = t_2[3U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S74 = t_2[7U];

#line 1850
                            }

#line 1850
                            uint partner_19 = (simd_shuffle_xor((_S74), ushort((4U))));

#line 1850
                            if(_S70)
                            {

#line 1850
                                t_2[3U] = partner_19;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[7U] = partner_19;

#line 1850
                            }

#line 1850
                            uint _S75;

#line 1850
                            if(_S70)
                            {

#line 1850
                                _S75 = t_2[8U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S75 = t_2[12U];

#line 1850
                            }

#line 1850
                            uint partner_20 = (simd_shuffle_xor((_S75), ushort((4U))));

#line 1850
                            if(_S70)
                            {

#line 1850
                                t_2[8U] = partner_20;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[12U] = partner_20;

#line 1850
                            }

#line 1850
                            uint _S76;

#line 1850
                            if(_S70)
                            {

#line 1850
                                _S76 = t_2[9U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S76 = t_2[13U];

#line 1850
                            }

#line 1850
                            uint partner_21 = (simd_shuffle_xor((_S76), ushort((4U))));

#line 1850
                            if(_S70)
                            {

#line 1850
                                t_2[9U] = partner_21;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[13U] = partner_21;

#line 1850
                            }

#line 1850
                            uint _S77;

#line 1850
                            if(_S70)
                            {

#line 1850
                                _S77 = t_2[10U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S77 = t_2[14U];

#line 1850
                            }

#line 1850
                            uint partner_22 = (simd_shuffle_xor((_S77), ushort((4U))));

#line 1850
                            if(_S70)
                            {

#line 1850
                                t_2[10U] = partner_22;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[14U] = partner_22;

#line 1850
                            }

#line 1850
                            uint _S78;

#line 1850
                            if(_S70)
                            {

#line 1850
                                _S78 = t_2[11U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S78 = t_2[15U];

#line 1850
                            }

#line 1850
                            uint partner_23 = (simd_shuffle_xor((_S78), ushort((4U))));

#line 1850
                            if(_S70)
                            {

#line 1850
                                t_2[11U] = partner_23;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_2[15U] = partner_23;

#line 1850
                            }

#line 1850
                            uint i_4 = 0U;

#line 1850
                            for(;;)
                            {

#line 1850
                                if(i_4 < 16U)
                                {
                                }
                                else
                                {

#line 1850
                                    break;
                                }

#line 1850
                                re_6[i_4] = half2(as_type<half>(ushort((t_2[i_4]) & 65535U)), as_type<half>(ushort(((t_2[i_4]) >> 16U) & 65535U)));

#line 1850
                                i_4 = i_4 + 1U;

#line 1850
                            }

#line 1850
                            break;
                        }

#line 1850
                        uint _S79 = (&kernelContext_1)->_tid_0;

#line 1850
                        for(;;)
                        {

#line 1850
                            thread array<uint, int(16)> t_3;

#line 1850
                            uint r_1 = 0U;

#line 1850
                            for(;;)
                            {

#line 1850
                                if(r_1 < 8U)
                                {
                                }
                                else
                                {

#line 1850
                                    break;
                                }

#line 1850
                                j_1 = 0U;

#line 1850
                                for(;;)
                                {

#line 1850
                                    if(j_1 < 2U)
                                    {
                                    }
                                    else
                                    {

#line 1850
                                        break;
                                    }

#line 1850
                                    t_3[j_1 * 8U + r_1] = (uint(as_type<ushort>(im_6[r_1 * 2U + j_1][0U])) & 65535U) | (uint(as_type<ushort>(im_6[r_1 * 2U + j_1][1U])) << 16U);

#line 1850
                                    j_1 = j_1 + 1U;

#line 1850
                                }

#line 1850
                                r_1 = r_1 + 1U;

#line 1850
                            }

#line 1850
                            uint _S80 = _S79 & 7U;

#line 1850
                            bool _S81 = (_S80 & 1U) != 0U;

#line 1850
                            uint _S82;

#line 1850
                            if(_S81)
                            {

#line 1850
                                _S82 = t_3[0U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S82 = t_3[1U];

#line 1850
                            }

#line 1850
                            uint partner_24 = (simd_shuffle_xor((_S82), ushort((1U))));

#line 1850
                            if(_S81)
                            {

#line 1850
                                t_3[0U] = partner_24;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[1U] = partner_24;

#line 1850
                            }

#line 1850
                            uint _S83;

#line 1850
                            if(_S81)
                            {

#line 1850
                                _S83 = t_3[2U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S83 = t_3[3U];

#line 1850
                            }

#line 1850
                            uint partner_25 = (simd_shuffle_xor((_S83), ushort((1U))));

#line 1850
                            if(_S81)
                            {

#line 1850
                                t_3[2U] = partner_25;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[3U] = partner_25;

#line 1850
                            }

#line 1850
                            uint _S84;

#line 1850
                            if(_S81)
                            {

#line 1850
                                _S84 = t_3[4U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S84 = t_3[5U];

#line 1850
                            }

#line 1850
                            uint partner_26 = (simd_shuffle_xor((_S84), ushort((1U))));

#line 1850
                            if(_S81)
                            {

#line 1850
                                t_3[4U] = partner_26;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[5U] = partner_26;

#line 1850
                            }

#line 1850
                            uint _S85;

#line 1850
                            if(_S81)
                            {

#line 1850
                                _S85 = t_3[6U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S85 = t_3[7U];

#line 1850
                            }

#line 1850
                            uint partner_27 = (simd_shuffle_xor((_S85), ushort((1U))));

#line 1850
                            if(_S81)
                            {

#line 1850
                                t_3[6U] = partner_27;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[7U] = partner_27;

#line 1850
                            }

#line 1850
                            uint _S86;

#line 1850
                            if(_S81)
                            {

#line 1850
                                _S86 = t_3[8U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S86 = t_3[9U];

#line 1850
                            }

#line 1850
                            uint partner_28 = (simd_shuffle_xor((_S86), ushort((1U))));

#line 1850
                            if(_S81)
                            {

#line 1850
                                t_3[8U] = partner_28;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[9U] = partner_28;

#line 1850
                            }

#line 1850
                            uint _S87;

#line 1850
                            if(_S81)
                            {

#line 1850
                                _S87 = t_3[10U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S87 = t_3[11U];

#line 1850
                            }

#line 1850
                            uint partner_29 = (simd_shuffle_xor((_S87), ushort((1U))));

#line 1850
                            if(_S81)
                            {

#line 1850
                                t_3[10U] = partner_29;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[11U] = partner_29;

#line 1850
                            }

#line 1850
                            uint _S88;

#line 1850
                            if(_S81)
                            {

#line 1850
                                _S88 = t_3[12U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S88 = t_3[13U];

#line 1850
                            }

#line 1850
                            uint partner_30 = (simd_shuffle_xor((_S88), ushort((1U))));

#line 1850
                            if(_S81)
                            {

#line 1850
                                t_3[12U] = partner_30;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[13U] = partner_30;

#line 1850
                            }

#line 1850
                            uint _S89;

#line 1850
                            if(_S81)
                            {

#line 1850
                                _S89 = t_3[14U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S89 = t_3[15U];

#line 1850
                            }

#line 1850
                            uint partner_31 = (simd_shuffle_xor((_S89), ushort((1U))));

#line 1850
                            if(_S81)
                            {

#line 1850
                                t_3[14U] = partner_31;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[15U] = partner_31;

#line 1850
                            }

#line 1850
                            bool _S90 = (_S80 & 2U) != 0U;

#line 1850
                            uint _S91;

#line 1850
                            if(_S90)
                            {

#line 1850
                                _S91 = t_3[0U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S91 = t_3[2U];

#line 1850
                            }

#line 1850
                            uint partner_32 = (simd_shuffle_xor((_S91), ushort((2U))));

#line 1850
                            if(_S90)
                            {

#line 1850
                                t_3[0U] = partner_32;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[2U] = partner_32;

#line 1850
                            }

#line 1850
                            uint _S92;

#line 1850
                            if(_S90)
                            {

#line 1850
                                _S92 = t_3[1U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S92 = t_3[3U];

#line 1850
                            }

#line 1850
                            uint partner_33 = (simd_shuffle_xor((_S92), ushort((2U))));

#line 1850
                            if(_S90)
                            {

#line 1850
                                t_3[1U] = partner_33;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[3U] = partner_33;

#line 1850
                            }

#line 1850
                            uint _S93;

#line 1850
                            if(_S90)
                            {

#line 1850
                                _S93 = t_3[4U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S93 = t_3[6U];

#line 1850
                            }

#line 1850
                            uint partner_34 = (simd_shuffle_xor((_S93), ushort((2U))));

#line 1850
                            if(_S90)
                            {

#line 1850
                                t_3[4U] = partner_34;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[6U] = partner_34;

#line 1850
                            }

#line 1850
                            uint _S94;

#line 1850
                            if(_S90)
                            {

#line 1850
                                _S94 = t_3[5U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S94 = t_3[7U];

#line 1850
                            }

#line 1850
                            uint partner_35 = (simd_shuffle_xor((_S94), ushort((2U))));

#line 1850
                            if(_S90)
                            {

#line 1850
                                t_3[5U] = partner_35;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[7U] = partner_35;

#line 1850
                            }

#line 1850
                            uint _S95;

#line 1850
                            if(_S90)
                            {

#line 1850
                                _S95 = t_3[8U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S95 = t_3[10U];

#line 1850
                            }

#line 1850
                            uint partner_36 = (simd_shuffle_xor((_S95), ushort((2U))));

#line 1850
                            if(_S90)
                            {

#line 1850
                                t_3[8U] = partner_36;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[10U] = partner_36;

#line 1850
                            }

#line 1850
                            uint _S96;

#line 1850
                            if(_S90)
                            {

#line 1850
                                _S96 = t_3[9U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S96 = t_3[11U];

#line 1850
                            }

#line 1850
                            uint partner_37 = (simd_shuffle_xor((_S96), ushort((2U))));

#line 1850
                            if(_S90)
                            {

#line 1850
                                t_3[9U] = partner_37;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[11U] = partner_37;

#line 1850
                            }

#line 1850
                            uint _S97;

#line 1850
                            if(_S90)
                            {

#line 1850
                                _S97 = t_3[12U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S97 = t_3[14U];

#line 1850
                            }

#line 1850
                            uint partner_38 = (simd_shuffle_xor((_S97), ushort((2U))));

#line 1850
                            if(_S90)
                            {

#line 1850
                                t_3[12U] = partner_38;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[14U] = partner_38;

#line 1850
                            }

#line 1850
                            uint _S98;

#line 1850
                            if(_S90)
                            {

#line 1850
                                _S98 = t_3[13U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S98 = t_3[15U];

#line 1850
                            }

#line 1850
                            uint partner_39 = (simd_shuffle_xor((_S98), ushort((2U))));

#line 1850
                            if(_S90)
                            {

#line 1850
                                t_3[13U] = partner_39;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[15U] = partner_39;

#line 1850
                            }

#line 1850
                            bool _S99 = (_S80 & 4U) != 0U;

#line 1850
                            uint _S100;

#line 1850
                            if(_S99)
                            {

#line 1850
                                _S100 = t_3[0U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S100 = t_3[4U];

#line 1850
                            }

#line 1850
                            uint partner_40 = (simd_shuffle_xor((_S100), ushort((4U))));

#line 1850
                            if(_S99)
                            {

#line 1850
                                t_3[0U] = partner_40;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[4U] = partner_40;

#line 1850
                            }

#line 1850
                            uint _S101;

#line 1850
                            if(_S99)
                            {

#line 1850
                                _S101 = t_3[1U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S101 = t_3[5U];

#line 1850
                            }

#line 1850
                            uint partner_41 = (simd_shuffle_xor((_S101), ushort((4U))));

#line 1850
                            if(_S99)
                            {

#line 1850
                                t_3[1U] = partner_41;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[5U] = partner_41;

#line 1850
                            }

#line 1850
                            uint _S102;

#line 1850
                            if(_S99)
                            {

#line 1850
                                _S102 = t_3[2U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S102 = t_3[6U];

#line 1850
                            }

#line 1850
                            uint partner_42 = (simd_shuffle_xor((_S102), ushort((4U))));

#line 1850
                            if(_S99)
                            {

#line 1850
                                t_3[2U] = partner_42;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[6U] = partner_42;

#line 1850
                            }

#line 1850
                            uint _S103;

#line 1850
                            if(_S99)
                            {

#line 1850
                                _S103 = t_3[3U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S103 = t_3[7U];

#line 1850
                            }

#line 1850
                            uint partner_43 = (simd_shuffle_xor((_S103), ushort((4U))));

#line 1850
                            if(_S99)
                            {

#line 1850
                                t_3[3U] = partner_43;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[7U] = partner_43;

#line 1850
                            }

#line 1850
                            uint _S104;

#line 1850
                            if(_S99)
                            {

#line 1850
                                _S104 = t_3[8U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S104 = t_3[12U];

#line 1850
                            }

#line 1850
                            uint partner_44 = (simd_shuffle_xor((_S104), ushort((4U))));

#line 1850
                            if(_S99)
                            {

#line 1850
                                t_3[8U] = partner_44;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[12U] = partner_44;

#line 1850
                            }

#line 1850
                            uint _S105;

#line 1850
                            if(_S99)
                            {

#line 1850
                                _S105 = t_3[9U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S105 = t_3[13U];

#line 1850
                            }

#line 1850
                            uint partner_45 = (simd_shuffle_xor((_S105), ushort((4U))));

#line 1850
                            if(_S99)
                            {

#line 1850
                                t_3[9U] = partner_45;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[13U] = partner_45;

#line 1850
                            }

#line 1850
                            uint _S106;

#line 1850
                            if(_S99)
                            {

#line 1850
                                _S106 = t_3[10U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S106 = t_3[14U];

#line 1850
                            }

#line 1850
                            uint partner_46 = (simd_shuffle_xor((_S106), ushort((4U))));

#line 1850
                            if(_S99)
                            {

#line 1850
                                t_3[10U] = partner_46;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[14U] = partner_46;

#line 1850
                            }

#line 1850
                            uint _S107;

#line 1850
                            if(_S99)
                            {

#line 1850
                                _S107 = t_3[11U];

#line 1850
                            }
                            else
                            {

#line 1850
                                _S107 = t_3[15U];

#line 1850
                            }

#line 1850
                            uint partner_47 = (simd_shuffle_xor((_S107), ushort((4U))));

#line 1850
                            if(_S99)
                            {

#line 1850
                                t_3[11U] = partner_47;

#line 1850
                            }
                            else
                            {

#line 1850
                                t_3[15U] = partner_47;

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
                                im_6[i_5] = half2(as_type<half>(ushort((t_3[i_5]) & 65535U)), as_type<half>(ushort(((t_3[i_5]) >> 16U) & 65535U)));

#line 1850
                                i_5 = i_5 + 1U;

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
                innermostS_0(&re_6, &im_6);

#line 1850
                uint i_6;

#line 1850
                uint ovAcc_0;

#line 1850
                uint bb_0;

#line 1850
                uint bb_1;

#line 1850
                bool infLocalA_0;

#line 1850
                bool infLocalB_0;

#line 1850
                bool hitLocalA_0;

#line 1850
                bool hitLocalB_0;

#line 1850
                half2 best_0;

#line 1850
                half2 selB_0;

#line 1850
                float2 _S108;

#line 1850
                if(_S27 != 0U)
                {

#line 1850
                    float _S109 = (as_type<float>((_S27)));

#line 1850
                    for(;;)
                    {

#line 1850
                        uint _S110 = slotToIndex_0(_t_0 * 16U) - _S39;

#line 1850
                        uint _S111 = _S40 - _S39;

#line 1850
                        half2 _S112 = half2(float2(0.0f) );

#line 1850
                        i_6 = 0U;

#line 1850
                        best_0 = _S112;

#line 1850
                        ovAcc_0 = 0U;

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
                            if((_S110 + slotToIndex_0(i_6)) < _S111)
                            {

#line 1850
                                selB_0 = mag2s_0(re_6[i_6], im_6[i_6]);

#line 1850
                            }
                            else
                            {

#line 1850
                                selB_0 = _S112;

#line 1850
                            }

#line 1850
                            half2 _S113 = max(best_0, selB_0);

#line 1850
                            uint ovAcc_1 = ovAcc_0 | (((((uint(as_type<ushort>(re_6[i_6][0U])) & 65535U) | (uint(as_type<ushort>(re_6[i_6][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(im_6[i_6][0U])) & 65535U) | (uint(as_type<ushort>(im_6[i_6][1U])) << 16U)) & 2080406528U) + 67109888U));

#line 1850
                            i_6 = i_6 + 1U;

#line 1850
                            best_0 = _S113;

#line 1850
                            ovAcc_0 = ovAcc_1;

#line 1850
                        }

#line 1850
                        if(_S26 == 0U)
                        {

#line 1850
                            uint _S114 = (uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U);

#line 1850
                            float thr2_0 = _S109 * _S109;

#line 1850
                            if((ovAcc_0 & 32768U) != 0U)
                            {

#line 1850
                                infLocalA_0 = true;

#line 1850
                            }
                            else
                            {

#line 1850
                                infLocalA_0 = (_S114 & 31744U) == 31744U;

#line 1850
                            }

#line 1850
                            if((ovAcc_0 & 2147483648U) != 0U)
                            {

#line 1850
                                infLocalB_0 = true;

#line 1850
                            }
                            else
                            {

#line 1850
                                infLocalB_0 = (_S114 & 2080374784U) == 2080374784U;

#line 1850
                            }

#line 1850
                            if(infLocalA_0)
                            {

#line 1850
                                hitLocalA_0 = true;

#line 1850
                            }
                            else
                            {

#line 1850
                                if((_S114 & 32767U) != 0U)
                                {

#line 1850
                                    hitLocalA_0 = float(best_0.x) >= thr2_0;

#line 1850
                                }
                                else
                                {

#line 1850
                                    hitLocalA_0 = false;

#line 1850
                                }

#line 1850
                            }

#line 1850
                            if(infLocalB_0)
                            {

#line 1850
                                hitLocalB_0 = true;

#line 1850
                            }
                            else
                            {

#line 1850
                                if((_S114 & 2147418112U) != 0U)
                                {

#line 1850
                                    hitLocalB_0 = float(best_0.y) >= thr2_0;

#line 1850
                                }
                                else
                                {

#line 1850
                                    hitLocalB_0 = false;

#line 1850
                                }

#line 1850
                            }

#line 1850
                            if(hitLocalA_0)
                            {

#line 1850
                                bb_0 = 1U;

#line 1850
                            }
                            else
                            {

#line 1850
                                bb_0 = 0U;

#line 1850
                            }

#line 1850
                            if(hitLocalB_0)
                            {

#line 1850
                                bb_1 = 2U;

#line 1850
                            }
                            else
                            {

#line 1850
                                bb_1 = 0U;

#line 1850
                            }

#line 1850
                            uint _S115 = bb_0 | bb_1;

#line 1850
                            uint _S116 = (simd_shuffle_xor((_S115), ushort((1U))));

#line 1850
                            uint hitBits_0 = _S115 | _S116;

#line 1850
                            uint _S117 = (simd_shuffle_xor((hitBits_0), ushort((2U))));

#line 1850
                            uint hitBits_1 = hitBits_0 | _S117;

#line 1850
                            uint _S118 = (simd_shuffle_xor((hitBits_1), ushort((4U))));

#line 1850
                            uint hitBits_2 = hitBits_1 | _S118;

#line 1850
                            if(_t_0 == 0U)
                            {

#line 1850
                                if(q_1 != 4294967295U)
                                {

#line 1850
                                    packed_float2 device* _S119 = (&kernelContext_1)->entryPointParams_peakVal_0+q_1;

#line 1850
                                    if((hitBits_2 & 1U) != 0U)
                                    {

#line 1850
                                        _S108 = float2(3.40282306073709653e+38f, 0.0f);

#line 1850
                                    }
                                    else
                                    {

#line 1850
                                        _S108 = float2(0.0f, 0.0f);

#line 1850
                                    }

#line 1850
                                    *_S119 = packed_float2(_S108) ;

#line 1850
                                }

#line 1850
                                if(n2_0 != 4294967295U)
                                {

#line 1850
                                    packed_float2 device* _S120 = (&kernelContext_1)->entryPointParams_peakVal_0+n2_0;

#line 1850
                                    if((hitBits_2 & 2U) != 0U)
                                    {

#line 1850
                                        _S108 = float2(3.40282306073709653e+38f, 0.0f);

#line 1850
                                    }
                                    else
                                    {

#line 1850
                                        _S108 = float2(0.0f, 0.0f);

#line 1850
                                    }

#line 1850
                                    *_S120 = packed_float2(_S108) ;

#line 1850
                                }

#line 1850
                            }

#line 1850
                            break;
                        }

#line 1850
                        uint bb_2 = ((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U)) & 2147450879U;

#line 1850
                        if((ovAcc_0 & 32768U) != 0U)
                        {

#line 1850
                            bb_0 = (bb_2 & 4294901760U) | 31744U;

#line 1850
                        }
                        else
                        {

#line 1850
                            bb_0 = bb_2;

#line 1850
                        }

#line 1850
                        if((ovAcc_0 & 2147483648U) != 0U)
                        {

#line 1850
                            bb_1 = (bb_0 & 65535U) | 2080374784U;

#line 1850
                        }
                        else
                        {

#line 1850
                            bb_1 = bb_0;

#line 1850
                        }

#line 1850
                        uint other_0 = (simd_shuffle_xor((bb_1), ushort((1U))));

#line 1850
                        uint _S121 = (max(bb_1 & 65535U, other_0 & 65535U)) | (max(bb_1 & 4294901760U, other_0 & 4294901760U));

#line 1850
                        uint other_1 = (simd_shuffle_xor((_S121), ushort((2U))));

#line 1850
                        uint _S122 = (max(_S121 & 65535U, other_1 & 65535U)) | (max(_S121 & 4294901760U, other_1 & 4294901760U));

#line 1850
                        uint other_2 = (simd_shuffle_xor((_S122), ushort((4U))));

#line 1850
                        uint bb_3 = (max(_S122 & 65535U, other_2 & 65535U)) | (max(_S122 & 4294901760U, other_2 & 4294901760U));

#line 1850
                        if(_t_0 == 0U)
                        {

#line 1850
                            bool infA_0 = (bb_3 & 31744U) == 31744U;

#line 1850
                            bool infB_0 = (bb_3 & 2080374784U) == 2080374784U;

#line 1850
                            float bA_0 = sqrt(float(as_type<half>(ushort(bb_3 & 65535U))));

#line 1850
                            float bB_0 = sqrt(float(as_type<half>(ushort((bb_3 >> 16U) & 65535U))));

#line 1850
                            if(infA_0)
                            {

#line 1850
                                infLocalA_0 = true;

#line 1850
                            }
                            else
                            {

#line 1850
                                if(bA_0 > 0.0f)
                                {

#line 1850
                                    infLocalA_0 = bA_0 >= _S109;

#line 1850
                                }
                                else
                                {

#line 1850
                                    infLocalA_0 = false;

#line 1850
                                }

#line 1850
                            }

#line 1850
                            if(infB_0)
                            {

#line 1850
                                infLocalB_0 = true;

#line 1850
                            }
                            else
                            {

#line 1850
                                if(bB_0 > 0.0f)
                                {

#line 1850
                                    infLocalB_0 = bB_0 >= _S109;

#line 1850
                                }
                                else
                                {

#line 1850
                                    infLocalB_0 = false;

#line 1850
                                }

#line 1850
                            }

#line 1850
                            if(q_1 != 4294967295U)
                            {

#line 1850
                                packed_float2 device* _S123 = (&kernelContext_1)->entryPointParams_peakVal_0+q_1;

#line 1850
                                if(infA_0)
                                {

#line 1850
                                    _S108 = float2(3.40282306073709653e+38f, 0.0f);

#line 1850
                                }
                                else
                                {

#line 1850
                                    if(infLocalA_0)
                                    {

#line 1850
                                        _S108 = float2(bA_0, 0.0f);

#line 1850
                                    }
                                    else
                                    {

#line 1850
                                        _S108 = float2(0.0f, 0.0f);

#line 1850
                                    }

#line 1850
                                }

#line 1850
                                *_S123 = packed_float2(_S108) ;

#line 1850
                            }

#line 1850
                            if(n2_0 != 4294967295U)
                            {

#line 1850
                                packed_float2 device* _S124 = (&kernelContext_1)->entryPointParams_peakVal_0+n2_0;

#line 1850
                                if(infB_0)
                                {

#line 1850
                                    _S108 = float2(3.40282306073709653e+38f, 0.0f);

#line 1850
                                }
                                else
                                {

#line 1850
                                    if(infLocalB_0)
                                    {

#line 1850
                                        _S108 = float2(bB_0, 0.0f);

#line 1850
                                    }
                                    else
                                    {

#line 1850
                                        _S108 = float2(0.0f, 0.0f);

#line 1850
                                    }

#line 1850
                                }

#line 1850
                                *_S124 = packed_float2(_S108) ;

#line 1850
                            }

#line 1850
                        }

#line 1850
                        break;
                    }

#line 1850
                }
                else
                {

#line 1850
                    array<half2, int(16)> _S125 = re_6;

#line 1850
                    array<half2, int(16)> _S126 = im_6;

#line 1850
                    for(;;)
                    {

#line 1850
                        uint _S127 = slotToIndex_0(_t_0 * 16U) - _S39;

#line 1850
                        uint _S128 = _S40 - _S39;

#line 1850
                        i_6 = 0U;

#line 1850
                        ovAcc_0 = 0U;

#line 1850
                        bb_0 = 0U;

#line 1850
                        bb_1 = 0U;

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
                            uint _S129 = i_6;

#line 1850
                            uint _S130 = i_6;

#line 1850
                            half2 mg_0 = mag2s_0(_S125[i_6], _S126[i_6]);

#line 1850
                            if((_S127 + slotToIndex_0(i_6)) < _S128)
                            {

#line 1850
                                m_0 = (uint(as_type<ushort>(mg_0[0U])) & 65535U) | (uint(as_type<ushort>(mg_0[1U])) << 16U);

#line 1850
                            }
                            else
                            {

#line 1850
                                m_0 = 0U;

#line 1850
                            }

#line 1850
                            uint ovAcc_2 = ovAcc_0 | (((((uint(as_type<ushort>(_S125[_S129][0U])) & 65535U) | (uint(as_type<ushort>(_S125[_S129][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(_S126[_S130][0U])) & 65535U) | (uint(as_type<ushort>(_S126[_S130][1U])) << 16U)) & 2080406528U) + 67109888U));

#line 1850
                            uint _S131 = 15U - i_6;

#line 1850
                            uint _S132 = max(bb_0, (m_0 << 16U) | _S131);

#line 1850
                            uint _S133 = max(bb_1, (m_0 & 4294901760U) | _S131);

#line 1850
                            i_6 = i_6 + 1U;

#line 1850
                            ovAcc_0 = ovAcc_2;

#line 1850
                            bb_0 = _S132;

#line 1850
                            bb_1 = _S133;

#line 1850
                        }

#line 1850
                        if((ovAcc_0 & 32768U) != 0U)
                        {

#line 1850
                            m_0 = max(bb_0, 2080374799U);

#line 1850
                        }
                        else
                        {

#line 1850
                            m_0 = bb_0;

#line 1850
                        }

#line 1850
                        uint kB_0;

#line 1850
                        if((ovAcc_0 & 2147483648U) != 0U)
                        {

#line 1850
                            kB_0 = max(bb_1, 2080374799U);

#line 1850
                        }
                        else
                        {

#line 1850
                            kB_0 = bb_1;

#line 1850
                        }

#line 1850
                        uint _S134 = (4095U - _t_0) << 4U;

#line 1850
                        uint kA_0 = m_0 | _S134;

#line 1850
                        uint kB_1 = kB_0 | _S134;

#line 1850
                        uint _S135 = (simd_shuffle_xor((kA_0), ushort((1U))));

#line 1850
                        uint _S136 = max(kA_0, _S135);

#line 1850
                        uint _S137 = (simd_shuffle_xor((kB_1), ushort((1U))));

#line 1850
                        uint _S138 = max(kB_1, _S137);

#line 1850
                        uint _S139 = (simd_shuffle_xor((_S136), ushort((2U))));

#line 1850
                        uint _S140 = max(_S136, _S139);

#line 1850
                        uint _S141 = (simd_shuffle_xor((_S138), ushort((2U))));

#line 1850
                        uint _S142 = max(_S138, _S141);

#line 1850
                        uint _S143 = (simd_shuffle_xor((_S140), ushort((4U))));

#line 1850
                        uint _S144 = max(_S140, _S143);

#line 1850
                        uint _S145 = (simd_shuffle_xor((_S142), ushort((4U))));

#line 1850
                        uint _S146 = max(_S142, _S145);

#line 1850
                        uint slotA_0 = 65535U - (_S144 & 65535U);

#line 1850
                        uint slotB_0 = 65535U - (_S146 & 65535U);

#line 1850
                        uint _S147 = _S144 >> 16U;

#line 1850
                        bool infA_1 = _S147 >= 31744U;

#line 1850
                        uint _S148 = _S146 >> 16U;

#line 1850
                        bool infB_1 = _S148 >= 31744U;

#line 1850
                        if(infA_1)
                        {

#line 1850
                            infLocalA_0 = true;

#line 1850
                        }
                        else
                        {

#line 1850
                            infLocalA_0 = (as_type<half>((ushort)((_S147)))) > (as_type<float>((_S27)));

#line 1850
                        }

#line 1850
                        if(infB_1)
                        {

#line 1850
                            infLocalB_0 = true;

#line 1850
                        }
                        else
                        {

#line 1850
                            infLocalB_0 = (as_type<half>((ushort)((_S148)))) > (as_type<float>((_S27)));

#line 1850
                        }

#line 1850
                        uint wA_0 = slotA_0 >> 4U;

#line 1850
                        uint _S149 = slotA_0 & 15U;

#line 1850
                        uint wB_0 = slotB_0 >> 4U;

#line 1850
                        uint _S150 = slotB_0 & 15U;

#line 1850
                        half2 _S151 = half2(float2(0.0f) );

#line 1850
                        j_1 = 0U;

#line 1850
                        best_0 = _S151;

#line 1850
                        selB_0 = _S151;

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
                            if(j_1 == _S149)
                            {

#line 1850
                                best_0 = half2(_S125[j_1].x, _S126[j_1].x);

#line 1850
                            }

#line 1850
                            if(j_1 == _S150)
                            {

#line 1850
                                selB_0 = half2(_S125[j_1].y, _S126[j_1].y);

#line 1850
                            }

#line 1850
                            j_1 = j_1 + 1U;

#line 1850
                        }

#line 1850
                        uint _S152 = (simd_shuffle_xor(((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U)), ushort((wA_0))));

#line 1850
                        half _S153 = as_type<half>(ushort(_S152 & 65535U));

#line 1850
                        half _S154 = as_type<half>(ushort((_S152 >> 16U) & 65535U));

#line 1850
                        uint _S155 = (simd_shuffle_xor(((uint(as_type<ushort>(selB_0[0U])) & 65535U) | (uint(as_type<ushort>(selB_0[1U])) << 16U)), ushort((wB_0))));

#line 1850
                        half _S156 = as_type<half>(ushort(_S155 & 65535U));

#line 1850
                        half _S157 = as_type<half>(ushort((_S155 >> 16U) & 65535U));

#line 1850
                        bool _S158 = _t_0 == 0U;

#line 1850
                        if(_S158)
                        {

#line 1850
                            hitLocalA_0 = q_1 != 4294967295U;

#line 1850
                        }
                        else
                        {

#line 1850
                            hitLocalA_0 = false;

#line 1850
                        }

#line 1850
                        int _S159;

#line 1850
                        if(hitLocalA_0)
                        {

#line 1850
                            int device* _S160 = (&kernelContext_1)->entryPointParams_peakIdx_0+q_1;

#line 1850
                            if(infLocalA_0)
                            {

#line 1850
                                _S159 = int(slotToIndex_0(slotA_0));

#line 1850
                            }
                            else
                            {

#line 1850
                                _S159 = int(-1);

#line 1850
                            }

#line 1850
                            *_S160 = _S159;

#line 1850
                            packed_float2 device* _S161 = (&kernelContext_1)->entryPointParams_peakVal_0+q_1;

#line 1850
                            if(infA_1)
                            {

#line 1850
                                _S108 = float2(3.40282306073709653e+38f, 0.0f);

#line 1850
                            }
                            else
                            {

#line 1850
                                if(infLocalA_0)
                                {

#line 1850
                                    _S108 = float2(float(_S153), float(_S154));

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S108 = float2(0.0f, 0.0f);

#line 1850
                                }

#line 1850
                            }

#line 1850
                            *_S161 = packed_float2(_S108) ;

#line 1850
                        }

#line 1850
                        if(_S158)
                        {

#line 1850
                            hitLocalB_0 = n2_0 != 4294967295U;

#line 1850
                        }
                        else
                        {

#line 1850
                            hitLocalB_0 = false;

#line 1850
                        }

#line 1850
                        if(hitLocalB_0)
                        {

#line 1850
                            int device* _S162 = (&kernelContext_1)->entryPointParams_peakIdx_0+n2_0;

#line 1850
                            if(infLocalB_0)
                            {

#line 1850
                                _S159 = int(slotToIndex_0(slotB_0));

#line 1850
                            }
                            else
                            {

#line 1850
                                _S159 = int(-1);

#line 1850
                            }

#line 1850
                            *_S162 = _S159;

#line 1850
                            packed_float2 device* _S163 = (&kernelContext_1)->entryPointParams_peakVal_0+n2_0;

#line 1850
                            if(infB_1)
                            {

#line 1850
                                _S108 = float2(3.40282306073709653e+38f, 0.0f);

#line 1850
                            }
                            else
                            {

#line 1850
                                if(infLocalB_0)
                                {

#line 1850
                                    _S108 = float2(float(_S156), float(_S157));

#line 1850
                                }
                                else
                                {

#line 1850
                                    _S108 = float2(0.0f, 0.0f);

#line 1850
                                }

#line 1850
                            }

#line 1850
                            *_S163 = packed_float2(_S108) ;

#line 1850
                        }

#line 1850
                        break;
                    }

#line 1850
                }

#line 1850
                break;
            }

#line 1850
            k_1 = k_1 + 2U;

#line 1850
        }

#line 1850
        break;
    }

    return;
}
