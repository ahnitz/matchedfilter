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

#line 10 "mm_64_fusedTierB_c16p16t2.slang"
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
};


#line 202 "mm_64_fusedTierB_c16p16t2.slang"
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

#line 232 "mm_64_fusedTierB_c16p16t2.slang"
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


#line 171 "mm_64_fusedTierB_c16p16t2.slang"
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

#line 265 "mm_64_fusedTierB_c16p16t2.slang"
    if(_S6 != 0U)
    {

#line 73 "twiddle.slang"
        uint _S7 = mfDataScaleFlag_0();

#line 266 "mm_64_fusedTierB_c16p16t2.slang"
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
        uint _S11 = 4U * k2_0;

#line 477
        r4s_0(re_4, im_4, _S11, _S11 + 1U, _S11 + 2U, _S11 + 3U);

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


#line 438 "mm_64_fusedTierB_c16p16t2.slang"
void dft4s_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5, uint o_0)
{
    uint _S16 = o_0 + 1U;

#line 440
    uint _S17 = o_0 + 2U;

#line 440
    r4s_1(re_5, im_5, o_0, _S16, _S17, o_0 + 3U);
    swap2_1(re_5, im_5, _S16, _S17);
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
uint lgOf_0(uint i_2)
{

#line 882
    uint _S18;

#line 882
    if(i_2 < 1U)
    {

#line 882
        _S18 = 4U;

#line 882
    }
    else
    {

#line 882
        _S18 = 1U;

#line 882
    }

#line 882
    return _S18;
}


#line 884
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 888
    uint lg_1 = lgOf_0(1U);

#line 888
    uint lg_2 = lgOf_0(0U);

#line 893
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 486
half2 mag2s_0(half2 re_7, half2 im_7)
{

#line 486
    return re_7 * re_7 + im_7 * im_7;
}


#line 1854
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1854
    uint j_0;

#line 1854
    thread KernelContext_0 kernelContext_1;

#line 1854
    (&kernelContext_1)->entryPointParams_0 = entryPointParams_1;

#line 1854
    (&kernelContext_1)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1854
    (&kernelContext_1)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1854
    (&kernelContext_1)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1854
    (&kernelContext_1)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1854
    (&kernelContext_1)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1854
    (&kernelContext_1)->_binPhase_0 = 0U;

#line 1875
    uint _S19 = lid_0.x;

#line 1875
    uint _sub_0 = _S19 / 4U;
    uint _pr_0 = gid_0.x * 16U + _sub_0;

#line 1876
    uint _t_0 = _S19 % 4U;
    (&kernelContext_1)->_stgBase_0 = _sub_0 * 64U;

#line 1877
    uint _S20 = entryPointParams_1->ntmpl_0;

#line 1877
    uint _S21 = entryPointParams_1->winStart_0;

#line 1877
    uint _S22 = entryPointParams_1->winEnd_0;

#line 1877
    uint _S23 = entryPointParams_1->binsize_0;

#line 1877
    uint _S24 = entryPointParams_1->nbins_0;

#line 1877
    uint _S25 = entryPointParams_1->thrBits_0;

#line 1887
    for(;;)
    {

#line 1887
        thread uint _S26 = _S21;

#line 1887
        thread uint _S27 = _S22;

#line 1887
        (&kernelContext_1)->_tid_0 = _t_0;

#line 1887
        uint tiles_0 = (_S20 + 2U - 1U) / 2U;

#line 1887
        uint slots_0 = _S23 * tiles_0;

#line 1887
        bool slotOk_0 = _pr_0 < slots_0;

#line 1887
        uint q_2;

#line 1887
        if(slotOk_0)
        {

#line 1887
            q_2 = _pr_0;

#line 1887
        }
        else
        {

#line 1887
            q_2 = slots_0 - 1U;

#line 1887
        }

#line 1887
        uint d_3 = q_2 / tiles_0;

#line 1887
        uint t0_0 = (q_2 - d_3 * tiles_0) * 2U;

#line 1887
        uint _S28 = d_3 * _S20 + t0_0;

#line 1887
        rowWindow_0(d_3, &_S26, &_S27, (&kernelContext_1)->entryPointParams_rowWin_0, &kernelContext_1);

#line 1887
        thread array<half2, int(16)> dreg_0;

#line 1887
        uint n2_0 = 0U;

#line 1887
        for(;;)
        {

#line 1887
            if(n2_0 < 16U)
            {
            }
            else
            {

#line 1887
                break;
            }

#line 1887
            uint _S29 = mfDataStrideFlag_0();

#line 1887
            if(_S29 != 0U)
            {

#line 1887
                uint _S30 = mfDataStrideFlag_0();

#line 1887
                q_2 = _S30;

#line 1887
            }
            else
            {

#line 1887
                q_2 = 64U;

#line 1887
            }

#line 1887
            half2 _S31 = dload_0((&kernelContext_1)->entryPointParams_data_0, d_3 * q_2 + _t_0 + 4U * n2_0);

#line 1887
            dreg_0[n2_0] = _S31;

#line 1887
            n2_0 = n2_0 + 1U;

#line 1887
        }

#line 1887
        uint k_0 = 0U;

#line 1887
        for(;;)
        {

#line 1887
            if(k_0 < 2U)
            {
            }
            else
            {

#line 1887
                break;
            }

#line 1887
            bool okA_0;

#line 1887
            if(slotOk_0)
            {

#line 1887
                okA_0 = (t0_0 + k_0) < _S20;

#line 1887
            }
            else
            {

#line 1887
                okA_0 = false;

#line 1887
            }

#line 1887
            bool okB_0;

#line 1887
            if(slotOk_0)
            {

#line 1887
                okB_0 = (t0_0 + k_0 + 1U) < _S20;

#line 1887
            }
            else
            {

#line 1887
                okB_0 = false;

#line 1887
            }

#line 1887
            if(okA_0)
            {

#line 1887
                q_2 = _S28 + k_0;

#line 1887
            }
            else
            {

#line 1887
                q_2 = 4294967295U;

#line 1887
            }

#line 1887
            if(okB_0)
            {

#line 1887
                n2_0 = _S28 + k_0 + 1U;

#line 1887
            }
            else
            {

#line 1887
                n2_0 = 4294967295U;

#line 1887
            }

#line 1887
            uint _S32 = t0_0 + k_0;

#line 1887
            uint _S33 = _S20 - 1U;

#line 1887
            uint _S34 = min(_S32, _S33);

#line 1887
            uint _S35 = min(_S32 + 1U, _S33);

#line 1887
            array<half2, int(16)> _S36 = dreg_0;

#line 1887
            uint _S37 = _S26;

#line 1887
            uint _S38 = _S27;

#line 1887
            for(;;)
            {

#line 1887
                thread array<half2, int(16)> re_8;

#line 1887
                thread array<half2, int(16)> im_8;

#line 1887
                uint n2_1 = 0U;

#line 1887
                for(;;)
                {

#line 1887
                    if(n2_1 < 16U)
                    {
                    }
                    else
                    {

#line 1887
                        break;
                    }

#line 1887
                    uint _S39 = 4U * n2_1;

#line 1887
                    half2 ta_0 = cload_0((&kernelContext_1)->entryPointParams_tmpl_0, _S34 * 64U + _t_0 + _S39);

#line 1887
                    half2 tb_0 = cload_0((&kernelContext_1)->entryPointParams_tmpl_0, _S35 * 64U + _t_0 + _S39);

#line 1887
                    half _S40 = _S36[n2_1].x;

#line 1887
                    half _S41 = _S36[n2_1].y;

#line 1887
                    cmulconjs_0(half2(_S40, _S40), half2(_S41, _S41), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_8[n2_1], &im_8[n2_1]);

#line 1887
                    n2_1 = n2_1 + 1U;

#line 1887
                }

#line 1887
                array<half2, int(16)> _S42 = re_8;

#line 1887
                array<half2, int(16)> _S43 = im_8;

#line 1887
                for(;;)
                {

#line 1887
                    thread array<half2, int(16)> _S44 = _S42;

#line 1887
                    thread array<half2, int(16)> _S45 = _S43;

#line 1887
                    (&kernelContext_1)->_tid_0 = _t_0;

#line 1887
                    for(;;)
                    {

#line 1887
                        uint lane_0 = _t_0 & 3U;

#line 1887
                        dft16s_0(&_S44, &_S45);

#line 1887
                        uint _S46 = mfCoarseTwtFlag_0();

#line 1887
                        uint r_0;

#line 1887
                        if(_S46 != 0U)
                        {

#line 1887
                            r_0 = 0U;

#line 1887
                            for(;;)
                            {

#line 1887
                                if(r_0 < 16U)
                                {
                                }
                                else
                                {

#line 1887
                                    break;
                                }

#line 1887
                                uint _S47 = lane_0 * 16U + r_0;

#line 1887
                                cmulw_0(&_S44[r_0], &_S45[r_0], as_type<half>(ushort((COARSE_TWT_DATA_0[_S47]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S47]) >> 16U) & 65535U)));

#line 1887
                                r_0 = r_0 + 1U;

#line 1887
                            }

#line 1887
                        }
                        else
                        {

#line 1887
                            float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_0) / 64.0f);

#line 1887
                            float _S48 = tw_0.x;

#line 1887
                            float _S49 = tw_0.y;

#line 1887
                            r_0 = 0U;

#line 1887
                            float cr_0 = 1.0f;

#line 1887
                            float ci_0 = 0.0f;

#line 1887
                            for(;;)
                            {

#line 1887
                                if(r_0 < 16U)
                                {
                                }
                                else
                                {

#line 1887
                                    break;
                                }

#line 1887
                                cmulw_0(&_S44[r_0], &_S45[r_0], half(cr_0), half(ci_0));

#line 1887
                                float nr_0 = cr_0 * _S48 - ci_0 * _S49;

#line 1887
                                float _S50 = cr_0 * _S49 + ci_0 * _S48;

#line 1887
                                r_0 = r_0 + 1U;

#line 1887
                                cr_0 = nr_0;

#line 1887
                                ci_0 = _S50;

#line 1887
                            }

#line 1887
                        }

#line 1887
                        uint per_0 = 16U / max(4U, 1U);

#line 1887
                        uint _S51 = max(0U, 1U);

#line 1887
                        uint blk2_0 = _t_0 / _S51;

#line 1887
                        uint lane2_0 = _t_0 % _S51;

#line 1887
                        for(;;)
                        {

#line 1887
                            uint _S52 = (&kernelContext_1)->_tid_0;

#line 1887
                            for(;;)
                            {

#line 1887
                                thread array<uint, int(16)> t_4;

#line 1887
                                r_0 = 0U;

#line 1887
                                for(;;)
                                {

#line 1887
                                    if(r_0 < 4U)
                                    {
                                    }
                                    else
                                    {

#line 1887
                                        break;
                                    }

#line 1887
                                    j_0 = 0U;

#line 1887
                                    for(;;)
                                    {

#line 1887
                                        if(j_0 < 4U)
                                        {
                                        }
                                        else
                                        {

#line 1887
                                            break;
                                        }

#line 1887
                                        t_4[j_0 * 4U + r_0] = (uint(as_type<ushort>(_S44[r_0 * 4U + j_0][0U])) & 65535U) | (uint(as_type<ushort>(_S44[r_0 * 4U + j_0][1U])) << 16U);

#line 1887
                                        j_0 = j_0 + 1U;

#line 1887
                                    }

#line 1887
                                    r_0 = r_0 + 1U;

#line 1887
                                }

#line 1887
                                uint _S53 = _S52 & 3U;

#line 1887
                                bool _S54 = (_S53 & 1U) != 0U;

#line 1887
                                uint _S55;

#line 1887
                                if(_S54)
                                {

#line 1887
                                    _S55 = t_4[0U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S55 = t_4[1U];

#line 1887
                                }

#line 1887
                                uint partner_0 = (simd_shuffle_xor((_S55), ushort((1U))));

#line 1887
                                if(_S54)
                                {

#line 1887
                                    t_4[0U] = partner_0;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[1U] = partner_0;

#line 1887
                                }

#line 1887
                                uint _S56;

#line 1887
                                if(_S54)
                                {

#line 1887
                                    _S56 = t_4[2U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S56 = t_4[3U];

#line 1887
                                }

#line 1887
                                uint partner_1 = (simd_shuffle_xor((_S56), ushort((1U))));

#line 1887
                                if(_S54)
                                {

#line 1887
                                    t_4[2U] = partner_1;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[3U] = partner_1;

#line 1887
                                }

#line 1887
                                uint _S57;

#line 1887
                                if(_S54)
                                {

#line 1887
                                    _S57 = t_4[4U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S57 = t_4[5U];

#line 1887
                                }

#line 1887
                                uint partner_2 = (simd_shuffle_xor((_S57), ushort((1U))));

#line 1887
                                if(_S54)
                                {

#line 1887
                                    t_4[4U] = partner_2;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[5U] = partner_2;

#line 1887
                                }

#line 1887
                                uint _S58;

#line 1887
                                if(_S54)
                                {

#line 1887
                                    _S58 = t_4[6U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S58 = t_4[7U];

#line 1887
                                }

#line 1887
                                uint partner_3 = (simd_shuffle_xor((_S58), ushort((1U))));

#line 1887
                                if(_S54)
                                {

#line 1887
                                    t_4[6U] = partner_3;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[7U] = partner_3;

#line 1887
                                }

#line 1887
                                uint _S59;

#line 1887
                                if(_S54)
                                {

#line 1887
                                    _S59 = t_4[8U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S59 = t_4[9U];

#line 1887
                                }

#line 1887
                                uint partner_4 = (simd_shuffle_xor((_S59), ushort((1U))));

#line 1887
                                if(_S54)
                                {

#line 1887
                                    t_4[8U] = partner_4;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[9U] = partner_4;

#line 1887
                                }

#line 1887
                                uint _S60;

#line 1887
                                if(_S54)
                                {

#line 1887
                                    _S60 = t_4[10U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S60 = t_4[11U];

#line 1887
                                }

#line 1887
                                uint partner_5 = (simd_shuffle_xor((_S60), ushort((1U))));

#line 1887
                                if(_S54)
                                {

#line 1887
                                    t_4[10U] = partner_5;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[11U] = partner_5;

#line 1887
                                }

#line 1887
                                uint _S61;

#line 1887
                                if(_S54)
                                {

#line 1887
                                    _S61 = t_4[12U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S61 = t_4[13U];

#line 1887
                                }

#line 1887
                                uint partner_6 = (simd_shuffle_xor((_S61), ushort((1U))));

#line 1887
                                if(_S54)
                                {

#line 1887
                                    t_4[12U] = partner_6;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[13U] = partner_6;

#line 1887
                                }

#line 1887
                                uint _S62;

#line 1887
                                if(_S54)
                                {

#line 1887
                                    _S62 = t_4[14U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S62 = t_4[15U];

#line 1887
                                }

#line 1887
                                uint partner_7 = (simd_shuffle_xor((_S62), ushort((1U))));

#line 1887
                                if(_S54)
                                {

#line 1887
                                    t_4[14U] = partner_7;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[15U] = partner_7;

#line 1887
                                }

#line 1887
                                bool _S63 = (_S53 & 2U) != 0U;

#line 1887
                                uint _S64;

#line 1887
                                if(_S63)
                                {

#line 1887
                                    _S64 = t_4[0U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S64 = t_4[2U];

#line 1887
                                }

#line 1887
                                uint partner_8 = (simd_shuffle_xor((_S64), ushort((2U))));

#line 1887
                                if(_S63)
                                {

#line 1887
                                    t_4[0U] = partner_8;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[2U] = partner_8;

#line 1887
                                }

#line 1887
                                uint _S65;

#line 1887
                                if(_S63)
                                {

#line 1887
                                    _S65 = t_4[1U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S65 = t_4[3U];

#line 1887
                                }

#line 1887
                                uint partner_9 = (simd_shuffle_xor((_S65), ushort((2U))));

#line 1887
                                if(_S63)
                                {

#line 1887
                                    t_4[1U] = partner_9;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[3U] = partner_9;

#line 1887
                                }

#line 1887
                                uint _S66;

#line 1887
                                if(_S63)
                                {

#line 1887
                                    _S66 = t_4[4U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S66 = t_4[6U];

#line 1887
                                }

#line 1887
                                uint partner_10 = (simd_shuffle_xor((_S66), ushort((2U))));

#line 1887
                                if(_S63)
                                {

#line 1887
                                    t_4[4U] = partner_10;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[6U] = partner_10;

#line 1887
                                }

#line 1887
                                uint _S67;

#line 1887
                                if(_S63)
                                {

#line 1887
                                    _S67 = t_4[5U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S67 = t_4[7U];

#line 1887
                                }

#line 1887
                                uint partner_11 = (simd_shuffle_xor((_S67), ushort((2U))));

#line 1887
                                if(_S63)
                                {

#line 1887
                                    t_4[5U] = partner_11;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[7U] = partner_11;

#line 1887
                                }

#line 1887
                                uint _S68;

#line 1887
                                if(_S63)
                                {

#line 1887
                                    _S68 = t_4[8U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S68 = t_4[10U];

#line 1887
                                }

#line 1887
                                uint partner_12 = (simd_shuffle_xor((_S68), ushort((2U))));

#line 1887
                                if(_S63)
                                {

#line 1887
                                    t_4[8U] = partner_12;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[10U] = partner_12;

#line 1887
                                }

#line 1887
                                uint _S69;

#line 1887
                                if(_S63)
                                {

#line 1887
                                    _S69 = t_4[9U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S69 = t_4[11U];

#line 1887
                                }

#line 1887
                                uint partner_13 = (simd_shuffle_xor((_S69), ushort((2U))));

#line 1887
                                if(_S63)
                                {

#line 1887
                                    t_4[9U] = partner_13;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[11U] = partner_13;

#line 1887
                                }

#line 1887
                                uint _S70;

#line 1887
                                if(_S63)
                                {

#line 1887
                                    _S70 = t_4[12U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S70 = t_4[14U];

#line 1887
                                }

#line 1887
                                uint partner_14 = (simd_shuffle_xor((_S70), ushort((2U))));

#line 1887
                                if(_S63)
                                {

#line 1887
                                    t_4[12U] = partner_14;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[14U] = partner_14;

#line 1887
                                }

#line 1887
                                uint _S71;

#line 1887
                                if(_S63)
                                {

#line 1887
                                    _S71 = t_4[13U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S71 = t_4[15U];

#line 1887
                                }

#line 1887
                                uint partner_15 = (simd_shuffle_xor((_S71), ushort((2U))));

#line 1887
                                if(_S63)
                                {

#line 1887
                                    t_4[13U] = partner_15;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_4[15U] = partner_15;

#line 1887
                                }

#line 1887
                                uint i_3 = 0U;

#line 1887
                                for(;;)
                                {

#line 1887
                                    if(i_3 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1887
                                        break;
                                    }

#line 1887
                                    _S44[i_3] = half2(as_type<half>(ushort((t_4[i_3]) & 65535U)), as_type<half>(ushort(((t_4[i_3]) >> 16U) & 65535U)));

#line 1887
                                    i_3 = i_3 + 1U;

#line 1887
                                }

#line 1887
                                break;
                            }

#line 1887
                            uint _S72 = (&kernelContext_1)->_tid_0;

#line 1887
                            for(;;)
                            {

#line 1887
                                thread array<uint, int(16)> t_5;

#line 1887
                                uint r_1 = 0U;

#line 1887
                                for(;;)
                                {

#line 1887
                                    if(r_1 < 4U)
                                    {
                                    }
                                    else
                                    {

#line 1887
                                        break;
                                    }

#line 1887
                                    j_0 = 0U;

#line 1887
                                    for(;;)
                                    {

#line 1887
                                        if(j_0 < 4U)
                                        {
                                        }
                                        else
                                        {

#line 1887
                                            break;
                                        }

#line 1887
                                        t_5[j_0 * 4U + r_1] = (uint(as_type<ushort>(_S45[r_1 * 4U + j_0][0U])) & 65535U) | (uint(as_type<ushort>(_S45[r_1 * 4U + j_0][1U])) << 16U);

#line 1887
                                        j_0 = j_0 + 1U;

#line 1887
                                    }

#line 1887
                                    r_1 = r_1 + 1U;

#line 1887
                                }

#line 1887
                                uint _S73 = _S72 & 3U;

#line 1887
                                bool _S74 = (_S73 & 1U) != 0U;

#line 1887
                                uint _S75;

#line 1887
                                if(_S74)
                                {

#line 1887
                                    _S75 = t_5[0U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S75 = t_5[1U];

#line 1887
                                }

#line 1887
                                uint partner_16 = (simd_shuffle_xor((_S75), ushort((1U))));

#line 1887
                                if(_S74)
                                {

#line 1887
                                    t_5[0U] = partner_16;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[1U] = partner_16;

#line 1887
                                }

#line 1887
                                uint _S76;

#line 1887
                                if(_S74)
                                {

#line 1887
                                    _S76 = t_5[2U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S76 = t_5[3U];

#line 1887
                                }

#line 1887
                                uint partner_17 = (simd_shuffle_xor((_S76), ushort((1U))));

#line 1887
                                if(_S74)
                                {

#line 1887
                                    t_5[2U] = partner_17;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[3U] = partner_17;

#line 1887
                                }

#line 1887
                                uint _S77;

#line 1887
                                if(_S74)
                                {

#line 1887
                                    _S77 = t_5[4U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S77 = t_5[5U];

#line 1887
                                }

#line 1887
                                uint partner_18 = (simd_shuffle_xor((_S77), ushort((1U))));

#line 1887
                                if(_S74)
                                {

#line 1887
                                    t_5[4U] = partner_18;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[5U] = partner_18;

#line 1887
                                }

#line 1887
                                uint _S78;

#line 1887
                                if(_S74)
                                {

#line 1887
                                    _S78 = t_5[6U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S78 = t_5[7U];

#line 1887
                                }

#line 1887
                                uint partner_19 = (simd_shuffle_xor((_S78), ushort((1U))));

#line 1887
                                if(_S74)
                                {

#line 1887
                                    t_5[6U] = partner_19;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[7U] = partner_19;

#line 1887
                                }

#line 1887
                                uint _S79;

#line 1887
                                if(_S74)
                                {

#line 1887
                                    _S79 = t_5[8U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S79 = t_5[9U];

#line 1887
                                }

#line 1887
                                uint partner_20 = (simd_shuffle_xor((_S79), ushort((1U))));

#line 1887
                                if(_S74)
                                {

#line 1887
                                    t_5[8U] = partner_20;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[9U] = partner_20;

#line 1887
                                }

#line 1887
                                uint _S80;

#line 1887
                                if(_S74)
                                {

#line 1887
                                    _S80 = t_5[10U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S80 = t_5[11U];

#line 1887
                                }

#line 1887
                                uint partner_21 = (simd_shuffle_xor((_S80), ushort((1U))));

#line 1887
                                if(_S74)
                                {

#line 1887
                                    t_5[10U] = partner_21;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[11U] = partner_21;

#line 1887
                                }

#line 1887
                                uint _S81;

#line 1887
                                if(_S74)
                                {

#line 1887
                                    _S81 = t_5[12U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S81 = t_5[13U];

#line 1887
                                }

#line 1887
                                uint partner_22 = (simd_shuffle_xor((_S81), ushort((1U))));

#line 1887
                                if(_S74)
                                {

#line 1887
                                    t_5[12U] = partner_22;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[13U] = partner_22;

#line 1887
                                }

#line 1887
                                uint _S82;

#line 1887
                                if(_S74)
                                {

#line 1887
                                    _S82 = t_5[14U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S82 = t_5[15U];

#line 1887
                                }

#line 1887
                                uint partner_23 = (simd_shuffle_xor((_S82), ushort((1U))));

#line 1887
                                if(_S74)
                                {

#line 1887
                                    t_5[14U] = partner_23;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[15U] = partner_23;

#line 1887
                                }

#line 1887
                                bool _S83 = (_S73 & 2U) != 0U;

#line 1887
                                uint _S84;

#line 1887
                                if(_S83)
                                {

#line 1887
                                    _S84 = t_5[0U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S84 = t_5[2U];

#line 1887
                                }

#line 1887
                                uint partner_24 = (simd_shuffle_xor((_S84), ushort((2U))));

#line 1887
                                if(_S83)
                                {

#line 1887
                                    t_5[0U] = partner_24;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[2U] = partner_24;

#line 1887
                                }

#line 1887
                                uint _S85;

#line 1887
                                if(_S83)
                                {

#line 1887
                                    _S85 = t_5[1U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S85 = t_5[3U];

#line 1887
                                }

#line 1887
                                uint partner_25 = (simd_shuffle_xor((_S85), ushort((2U))));

#line 1887
                                if(_S83)
                                {

#line 1887
                                    t_5[1U] = partner_25;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[3U] = partner_25;

#line 1887
                                }

#line 1887
                                uint _S86;

#line 1887
                                if(_S83)
                                {

#line 1887
                                    _S86 = t_5[4U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S86 = t_5[6U];

#line 1887
                                }

#line 1887
                                uint partner_26 = (simd_shuffle_xor((_S86), ushort((2U))));

#line 1887
                                if(_S83)
                                {

#line 1887
                                    t_5[4U] = partner_26;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[6U] = partner_26;

#line 1887
                                }

#line 1887
                                uint _S87;

#line 1887
                                if(_S83)
                                {

#line 1887
                                    _S87 = t_5[5U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S87 = t_5[7U];

#line 1887
                                }

#line 1887
                                uint partner_27 = (simd_shuffle_xor((_S87), ushort((2U))));

#line 1887
                                if(_S83)
                                {

#line 1887
                                    t_5[5U] = partner_27;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[7U] = partner_27;

#line 1887
                                }

#line 1887
                                uint _S88;

#line 1887
                                if(_S83)
                                {

#line 1887
                                    _S88 = t_5[8U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S88 = t_5[10U];

#line 1887
                                }

#line 1887
                                uint partner_28 = (simd_shuffle_xor((_S88), ushort((2U))));

#line 1887
                                if(_S83)
                                {

#line 1887
                                    t_5[8U] = partner_28;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[10U] = partner_28;

#line 1887
                                }

#line 1887
                                uint _S89;

#line 1887
                                if(_S83)
                                {

#line 1887
                                    _S89 = t_5[9U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S89 = t_5[11U];

#line 1887
                                }

#line 1887
                                uint partner_29 = (simd_shuffle_xor((_S89), ushort((2U))));

#line 1887
                                if(_S83)
                                {

#line 1887
                                    t_5[9U] = partner_29;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[11U] = partner_29;

#line 1887
                                }

#line 1887
                                uint _S90;

#line 1887
                                if(_S83)
                                {

#line 1887
                                    _S90 = t_5[12U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S90 = t_5[14U];

#line 1887
                                }

#line 1887
                                uint partner_30 = (simd_shuffle_xor((_S90), ushort((2U))));

#line 1887
                                if(_S83)
                                {

#line 1887
                                    t_5[12U] = partner_30;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[14U] = partner_30;

#line 1887
                                }

#line 1887
                                uint _S91;

#line 1887
                                if(_S83)
                                {

#line 1887
                                    _S91 = t_5[13U];

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S91 = t_5[15U];

#line 1887
                                }

#line 1887
                                uint partner_31 = (simd_shuffle_xor((_S91), ushort((2U))));

#line 1887
                                if(_S83)
                                {

#line 1887
                                    t_5[13U] = partner_31;

#line 1887
                                }
                                else
                                {

#line 1887
                                    t_5[15U] = partner_31;

#line 1887
                                }

#line 1887
                                uint i_4 = 0U;

#line 1887
                                for(;;)
                                {

#line 1887
                                    if(i_4 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1887
                                        break;
                                    }

#line 1887
                                    _S45[i_4] = half2(as_type<half>(ushort((t_5[i_4]) & 65535U)), as_type<half>(ushort(((t_5[i_4]) >> 16U) & 65535U)));

#line 1887
                                    i_4 = i_4 + 1U;

#line 1887
                                }

#line 1887
                                break;
                            }

#line 1887
                            break;
                        }

#line 1887
                        break;
                    }

#line 1887
                    innermostS_0(&_S44, &_S45);

#line 1887
                    uint spanA_0;

#line 1887
                    uint spanB_0;

#line 1887
                    uint i_5;

#line 1887
                    uint ovAcc_0;

#line 1887
                    uint ovAcc_1;

#line 1887
                    uint ovAcc_2;

#line 1887
                    uint bb_0;

#line 1887
                    uint bb_1;

#line 1887
                    bool infLocalA_0;

#line 1887
                    bool infLocalB_0;

#line 1887
                    bool hitLocalA_0;

#line 1887
                    bool hitLocalB_0;

#line 1887
                    bool hitA_0;

#line 1887
                    bool hitB_0;

#line 1887
                    half2 best_0;

#line 1887
                    float2 _S92;

#line 1887
                    if(_S25 != 0U)
                    {

#line 1887
                        float _S93 = (as_type<float>((_S25)));

#line 1887
                        for(;;)
                        {

#line 1887
                            uint _S94 = slotToIndex_0(_t_0 * 16U) - _S37;

#line 1887
                            bool _S95 = _S38 > _S37;

#line 1887
                            if(_S95)
                            {

#line 1887
                                spanA_0 = _S38 - _S37;

#line 1887
                            }
                            else
                            {

#line 1887
                                spanA_0 = 0U;

#line 1887
                            }

#line 1887
                            if(_S95)
                            {

#line 1887
                                spanB_0 = _S38 - _S37;

#line 1887
                            }
                            else
                            {

#line 1887
                                spanB_0 = 0U;

#line 1887
                            }

#line 1887
                            half2 _S96 = half2(float2(0.0f) );

#line 1887
                            i_5 = 0U;

#line 1887
                            best_0 = _S96;

#line 1887
                            ovAcc_0 = 0U;

#line 1887
                            for(;;)
                            {

#line 1887
                                if(i_5 < 16U)
                                {
                                }
                                else
                                {

#line 1887
                                    break;
                                }

#line 1887
                                uint _S97 = _S94 + slotToIndex_0(i_5);

#line 1887
                                bool liveB_0 = _S97 < spanB_0;

#line 1887
                                half2 _S98 = _S44[i_5];

#line 1887
                                half2 _S99 = _S45[i_5];

#line 1887
                                half2 _S100 = mag2s_0(_S44[i_5], _S45[i_5]);

#line 1887
                                uint _S101 = (uint(as_type<ushort>(_S100[0U])) & 65535U) | (uint(as_type<ushort>(_S100[1U])) << 16U);

#line 1887
                                if(_S97 < spanA_0)
                                {

#line 1887
                                    ovAcc_1 = _S101 & 65535U;

#line 1887
                                }
                                else
                                {

#line 1887
                                    ovAcc_1 = 0U;

#line 1887
                                }

#line 1887
                                if(liveB_0)
                                {

#line 1887
                                    ovAcc_2 = _S101 & 4294901760U;

#line 1887
                                }
                                else
                                {

#line 1887
                                    ovAcc_2 = 0U;

#line 1887
                                }

#line 1887
                                uint m_0 = ovAcc_1 | ovAcc_2;

#line 1887
                                half2 _S102 = max(best_0, half2(as_type<half>(ushort(m_0 & 65535U)), as_type<half>(ushort((m_0 >> 16U) & 65535U))));

#line 1887
                                uint ovAcc_3 = ovAcc_0 | (((((uint(as_type<ushort>(_S98[0U])) & 65535U) | (uint(as_type<ushort>(_S98[1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(_S99[0U])) & 65535U) | (uint(as_type<ushort>(_S99[1U])) << 16U)) & 2080406528U) + 67109888U));

#line 1887
                                i_5 = i_5 + 1U;

#line 1887
                                best_0 = _S102;

#line 1887
                                ovAcc_0 = ovAcc_3;

#line 1887
                            }

#line 1887
                            if(spanA_0 == 0U)
                            {

#line 1887
                                ovAcc_1 = ovAcc_0 & 4294934527U;

#line 1887
                            }
                            else
                            {

#line 1887
                                ovAcc_1 = ovAcc_0;

#line 1887
                            }

#line 1887
                            if(spanB_0 == 0U)
                            {

#line 1887
                                ovAcc_2 = ovAcc_1 & 2147483647U;

#line 1887
                            }
                            else
                            {

#line 1887
                                ovAcc_2 = ovAcc_1;

#line 1887
                            }

#line 1887
                            if(_S24 == 0U)
                            {

#line 1887
                                uint _S103 = (uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U);

#line 1887
                                float thr2_0 = _S93 * _S93;

#line 1887
                                if((ovAcc_2 & 32768U) != 0U)
                                {

#line 1887
                                    infLocalA_0 = true;

#line 1887
                                }
                                else
                                {

#line 1887
                                    infLocalA_0 = (_S103 & 31744U) == 31744U;

#line 1887
                                }

#line 1887
                                if((ovAcc_2 & 2147483648U) != 0U)
                                {

#line 1887
                                    infLocalB_0 = true;

#line 1887
                                }
                                else
                                {

#line 1887
                                    infLocalB_0 = (_S103 & 2080374784U) == 2080374784U;

#line 1887
                                }

#line 1887
                                if(infLocalA_0)
                                {

#line 1887
                                    hitLocalA_0 = true;

#line 1887
                                }
                                else
                                {

#line 1887
                                    if((_S103 & 32767U) != 0U)
                                    {

#line 1887
                                        hitLocalA_0 = float(best_0.x) >= thr2_0;

#line 1887
                                    }
                                    else
                                    {

#line 1887
                                        hitLocalA_0 = false;

#line 1887
                                    }

#line 1887
                                }

#line 1887
                                if(infLocalB_0)
                                {

#line 1887
                                    hitLocalB_0 = true;

#line 1887
                                }
                                else
                                {

#line 1887
                                    if((_S103 & 2147418112U) != 0U)
                                    {

#line 1887
                                        hitLocalB_0 = float(best_0.y) >= thr2_0;

#line 1887
                                    }
                                    else
                                    {

#line 1887
                                        hitLocalB_0 = false;

#line 1887
                                    }

#line 1887
                                }

#line 1887
                                if(hitLocalA_0)
                                {

#line 1887
                                    bb_0 = 1U;

#line 1887
                                }
                                else
                                {

#line 1887
                                    bb_0 = 0U;

#line 1887
                                }

#line 1887
                                if(hitLocalB_0)
                                {

#line 1887
                                    bb_1 = 2U;

#line 1887
                                }
                                else
                                {

#line 1887
                                    bb_1 = 0U;

#line 1887
                                }

#line 1887
                                uint _S104 = bb_0 | bb_1;

#line 1887
                                uint _S105 = (simd_shuffle_xor((_S104), ushort((1U))));

#line 1887
                                uint hitBits_0 = _S104 | _S105;

#line 1887
                                uint _S106 = (simd_shuffle_xor((hitBits_0), ushort((2U))));

#line 1887
                                uint hitBits_1 = hitBits_0 | _S106;

#line 1887
                                if(_t_0 == 0U)
                                {

#line 1887
                                    if(q_2 != 4294967295U)
                                    {

#line 1887
                                        packed_float2 device* _S107 = (&kernelContext_1)->entryPointParams_peakVal_0+q_2;

#line 1887
                                        if((hitBits_1 & 1U) != 0U)
                                        {

#line 1887
                                            _S92 = float2(3.40282306073709653e+38f, 0.0f);

#line 1887
                                        }
                                        else
                                        {

#line 1887
                                            _S92 = float2(0.0f, 0.0f);

#line 1887
                                        }

#line 1887
                                        *_S107 = packed_float2(_S92) ;

#line 1887
                                    }

#line 1887
                                    if(n2_0 != 4294967295U)
                                    {

#line 1887
                                        packed_float2 device* _S108 = (&kernelContext_1)->entryPointParams_peakVal_0+n2_0;

#line 1887
                                        if((hitBits_1 & 2U) != 0U)
                                        {

#line 1887
                                            _S92 = float2(3.40282306073709653e+38f, 0.0f);

#line 1887
                                        }
                                        else
                                        {

#line 1887
                                            _S92 = float2(0.0f, 0.0f);

#line 1887
                                        }

#line 1887
                                        *_S108 = packed_float2(_S92) ;

#line 1887
                                    }

#line 1887
                                }

#line 1887
                                break;
                            }

#line 1887
                            uint bb_2 = ((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U)) & 2147450879U;

#line 1887
                            if((ovAcc_2 & 32768U) != 0U)
                            {

#line 1887
                                bb_0 = (bb_2 & 4294901760U) | 31744U;

#line 1887
                            }
                            else
                            {

#line 1887
                                bb_0 = bb_2;

#line 1887
                            }

#line 1887
                            if((ovAcc_2 & 2147483648U) != 0U)
                            {

#line 1887
                                bb_1 = (bb_0 & 65535U) | 2080374784U;

#line 1887
                            }
                            else
                            {

#line 1887
                                bb_1 = bb_0;

#line 1887
                            }

#line 1887
                            uint other_0 = (simd_shuffle_xor((bb_1), ushort((1U))));

#line 1887
                            uint _S109 = (max(bb_1 & 65535U, other_0 & 65535U)) | (max(bb_1 & 4294901760U, other_0 & 4294901760U));

#line 1887
                            uint other_1 = (simd_shuffle_xor((_S109), ushort((2U))));

#line 1887
                            uint bb_3 = (max(_S109 & 65535U, other_1 & 65535U)) | (max(_S109 & 4294901760U, other_1 & 4294901760U));

#line 1887
                            if(_t_0 == 0U)
                            {

#line 1887
                                bool infA_0 = (bb_3 & 31744U) == 31744U;

#line 1887
                                bool infB_0 = (bb_3 & 2080374784U) == 2080374784U;

#line 1887
                                float bA_0 = sqrt(float(as_type<half>(ushort(bb_3 & 65535U))));

#line 1887
                                float bB_0 = sqrt(float(as_type<half>(ushort((bb_3 >> 16U) & 65535U))));

#line 1887
                                if(infA_0)
                                {

#line 1887
                                    hitA_0 = true;

#line 1887
                                }
                                else
                                {

#line 1887
                                    if(bA_0 > 0.0f)
                                    {

#line 1887
                                        infLocalA_0 = bA_0 >= _S93;

#line 1887
                                    }
                                    else
                                    {

#line 1887
                                        infLocalA_0 = false;

#line 1887
                                    }

#line 1887
                                    hitA_0 = infLocalA_0;

#line 1887
                                }

#line 1887
                                if(infB_0)
                                {

#line 1887
                                    hitB_0 = true;

#line 1887
                                }
                                else
                                {

#line 1887
                                    if(bB_0 > 0.0f)
                                    {

#line 1887
                                        infLocalA_0 = bB_0 >= _S93;

#line 1887
                                    }
                                    else
                                    {

#line 1887
                                        infLocalA_0 = false;

#line 1887
                                    }

#line 1887
                                    hitB_0 = infLocalA_0;

#line 1887
                                }

#line 1887
                                if(q_2 != 4294967295U)
                                {

#line 1887
                                    packed_float2 device* _S110 = (&kernelContext_1)->entryPointParams_peakVal_0+q_2;

#line 1887
                                    if(infA_0)
                                    {

#line 1887
                                        _S92 = float2(3.40282306073709653e+38f, 0.0f);

#line 1887
                                    }
                                    else
                                    {

#line 1887
                                        if(hitA_0)
                                        {

#line 1887
                                            _S92 = float2(bA_0, 0.0f);

#line 1887
                                        }
                                        else
                                        {

#line 1887
                                            _S92 = float2(0.0f, 0.0f);

#line 1887
                                        }

#line 1887
                                    }

#line 1887
                                    *_S110 = packed_float2(_S92) ;

#line 1887
                                }

#line 1887
                                if(n2_0 != 4294967295U)
                                {

#line 1887
                                    packed_float2 device* _S111 = (&kernelContext_1)->entryPointParams_peakVal_0+n2_0;

#line 1887
                                    if(infB_0)
                                    {

#line 1887
                                        _S92 = float2(3.40282306073709653e+38f, 0.0f);

#line 1887
                                    }
                                    else
                                    {

#line 1887
                                        if(hitB_0)
                                        {

#line 1887
                                            _S92 = float2(bB_0, 0.0f);

#line 1887
                                        }
                                        else
                                        {

#line 1887
                                            _S92 = float2(0.0f, 0.0f);

#line 1887
                                        }

#line 1887
                                    }

#line 1887
                                    *_S111 = packed_float2(_S92) ;

#line 1887
                                }

#line 1887
                            }

#line 1887
                            break;
                        }

#line 1887
                    }
                    else
                    {

#line 1887
                        array<half2, int(16)> _S112 = _S44;

#line 1887
                        array<half2, int(16)> _S113 = _S45;

#line 1887
                        for(;;)
                        {

#line 1887
                            uint _S114 = slotToIndex_0(_t_0 * 16U) - _S37;

#line 1887
                            bool _S115 = _S38 > _S37;

#line 1887
                            if(_S115)
                            {

#line 1887
                                spanA_0 = _S38 - _S37;

#line 1887
                            }
                            else
                            {

#line 1887
                                spanA_0 = 0U;

#line 1887
                            }

#line 1887
                            if(_S115)
                            {

#line 1887
                                spanB_0 = _S38 - _S37;

#line 1887
                            }
                            else
                            {

#line 1887
                                spanB_0 = 0U;

#line 1887
                            }

#line 1887
                            i_5 = 0U;

#line 1887
                            ovAcc_0 = 0U;

#line 1887
                            ovAcc_1 = 0U;

#line 1887
                            ovAcc_2 = 0U;

#line 1887
                            for(;;)
                            {

#line 1887
                                if(i_5 < 16U)
                                {
                                }
                                else
                                {

#line 1887
                                    break;
                                }

#line 1887
                                uint _S116 = _S114 + slotToIndex_0(i_5);

#line 1887
                                bool liveB_1 = _S116 < spanB_0;

#line 1887
                                half2 mg_0 = mag2s_0(_S112[i_5], _S113[i_5]);

#line 1887
                                uint _S117 = (uint(as_type<ushort>(mg_0[0U])) & 65535U) | (uint(as_type<ushort>(mg_0[1U])) << 16U);

#line 1887
                                uint ovAcc_4 = ovAcc_0 | (((((uint(as_type<ushort>(_S112[i_5][0U])) & 65535U) | (uint(as_type<ushort>(_S112[i_5][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(_S113[i_5][0U])) & 65535U) | (uint(as_type<ushort>(_S113[i_5][1U])) << 16U)) & 2080406528U) + 67109888U));

#line 1887
                                if(_S116 < spanA_0)
                                {

#line 1887
                                    bb_0 = _S117 << 16U;

#line 1887
                                }
                                else
                                {

#line 1887
                                    bb_0 = 0U;

#line 1887
                                }

#line 1887
                                uint _S118 = 15U - i_5;

#line 1887
                                uint _S119 = max(ovAcc_1, bb_0 | _S118);

#line 1887
                                if(liveB_1)
                                {

#line 1887
                                    bb_1 = _S117 & 4294901760U;

#line 1887
                                }
                                else
                                {

#line 1887
                                    bb_1 = 0U;

#line 1887
                                }

#line 1887
                                uint _S120 = max(ovAcc_2, bb_1 | _S118);

#line 1887
                                i_5 = i_5 + 1U;

#line 1887
                                ovAcc_0 = ovAcc_4;

#line 1887
                                ovAcc_1 = _S119;

#line 1887
                                ovAcc_2 = _S120;

#line 1887
                            }

#line 1887
                            bool _S121 = spanA_0 != 0U;

#line 1887
                            if(_S121)
                            {

#line 1887
                                infLocalA_0 = (ovAcc_0 & 32768U) != 0U;

#line 1887
                            }
                            else
                            {

#line 1887
                                infLocalA_0 = false;

#line 1887
                            }

#line 1887
                            if(infLocalA_0)
                            {

#line 1887
                                bb_0 = max(ovAcc_1, 2080374799U);

#line 1887
                            }
                            else
                            {

#line 1887
                                bb_0 = ovAcc_1;

#line 1887
                            }

#line 1887
                            bool _S122 = spanB_0 != 0U;

#line 1887
                            if(_S122)
                            {

#line 1887
                                infLocalB_0 = (ovAcc_0 & 2147483648U) != 0U;

#line 1887
                            }
                            else
                            {

#line 1887
                                infLocalB_0 = false;

#line 1887
                            }

#line 1887
                            if(infLocalB_0)
                            {

#line 1887
                                bb_1 = max(ovAcc_2, 2080374799U);

#line 1887
                            }
                            else
                            {

#line 1887
                                bb_1 = ovAcc_2;

#line 1887
                            }

#line 1887
                            uint _S123 = (4095U - _t_0) << 4U;

#line 1887
                            uint kA_0 = bb_0 | _S123;

#line 1887
                            uint kB_0 = bb_1 | _S123;

#line 1887
                            uint _S124 = (simd_shuffle_xor((kA_0), ushort((1U))));

#line 1887
                            uint _S125 = max(kA_0, _S124);

#line 1887
                            uint _S126 = (simd_shuffle_xor((kB_0), ushort((1U))));

#line 1887
                            uint _S127 = max(kB_0, _S126);

#line 1887
                            uint _S128 = (simd_shuffle_xor((_S125), ushort((2U))));

#line 1887
                            uint _S129 = max(_S125, _S128);

#line 1887
                            uint _S130 = (simd_shuffle_xor((_S127), ushort((2U))));

#line 1887
                            uint _S131 = max(_S127, _S130);

#line 1887
                            uint slotA_0 = 65535U - (_S129 & 65535U);

#line 1887
                            uint slotB_0 = 65535U - (_S131 & 65535U);

#line 1887
                            if(_S121)
                            {

#line 1887
                                hitLocalA_0 = (_S129 >> 16U) >= 31744U;

#line 1887
                            }
                            else
                            {

#line 1887
                                hitLocalA_0 = false;

#line 1887
                            }

#line 1887
                            if(_S122)
                            {

#line 1887
                                hitLocalB_0 = (_S131 >> 16U) >= 31744U;

#line 1887
                            }
                            else
                            {

#line 1887
                                hitLocalB_0 = false;

#line 1887
                            }

#line 1887
                            if(hitLocalA_0)
                            {

#line 1887
                                hitA_0 = true;

#line 1887
                            }
                            else
                            {

#line 1887
                                hitA_0 = (as_type<half>((ushort)((_S129 >> 16U)))) > (as_type<float>((_S25)));

#line 1887
                            }

#line 1887
                            if(hitLocalB_0)
                            {

#line 1887
                                hitB_0 = true;

#line 1887
                            }
                            else
                            {

#line 1887
                                hitB_0 = (as_type<half>((ushort)((_S131 >> 16U)))) > (as_type<float>((_S25)));

#line 1887
                            }

#line 1887
                            uint wA_0 = slotA_0 >> 4U;

#line 1887
                            uint _S132 = slotA_0 & 15U;

#line 1887
                            uint wB_0 = slotB_0 >> 4U;

#line 1887
                            uint _S133 = slotB_0 & 15U;

#line 1887
                            half2 _S134 = half2(float2(0.0f) );

#line 1887
                            j_0 = 0U;

#line 1887
                            best_0 = _S134;

#line 1887
                            half2 selB_0 = _S134;

#line 1887
                            for(;;)
                            {

#line 1887
                                if(j_0 < 16U)
                                {
                                }
                                else
                                {

#line 1887
                                    break;
                                }

#line 1887
                                if(j_0 == _S132)
                                {

#line 1887
                                    best_0 = half2(_S112[j_0].x, _S113[j_0].x);

#line 1887
                                }

#line 1887
                                if(j_0 == _S133)
                                {

#line 1887
                                    selB_0 = half2(_S112[j_0].y, _S113[j_0].y);

#line 1887
                                }

#line 1887
                                j_0 = j_0 + 1U;

#line 1887
                            }

#line 1887
                            uint _S135 = (simd_shuffle_xor(((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U)), ushort((wA_0))));

#line 1887
                            half _S136 = as_type<half>(ushort(_S135 & 65535U));

#line 1887
                            half _S137 = as_type<half>(ushort((_S135 >> 16U) & 65535U));

#line 1887
                            uint _S138 = (simd_shuffle_xor(((uint(as_type<ushort>(selB_0[0U])) & 65535U) | (uint(as_type<ushort>(selB_0[1U])) << 16U)), ushort((wB_0))));

#line 1887
                            half _S139 = as_type<half>(ushort(_S138 & 65535U));

#line 1887
                            half _S140 = as_type<half>(ushort((_S138 >> 16U) & 65535U));

#line 1887
                            bool _S141 = _t_0 == 0U;

#line 1887
                            bool _S142;

#line 1887
                            if(_S141)
                            {

#line 1887
                                _S142 = q_2 != 4294967295U;

#line 1887
                            }
                            else
                            {

#line 1887
                                _S142 = false;

#line 1887
                            }

#line 1887
                            int _S143;

#line 1887
                            if(_S142)
                            {

#line 1887
                                int device* _S144 = (&kernelContext_1)->entryPointParams_peakIdx_0+q_2;

#line 1887
                                if(hitA_0)
                                {

#line 1887
                                    _S143 = int(slotToIndex_0(slotA_0));

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S143 = int(-1);

#line 1887
                                }

#line 1887
                                *_S144 = _S143;

#line 1887
                                packed_float2 device* _S145 = (&kernelContext_1)->entryPointParams_peakVal_0+q_2;

#line 1887
                                if(hitLocalA_0)
                                {

#line 1887
                                    _S92 = float2(3.40282306073709653e+38f, 0.0f);

#line 1887
                                }
                                else
                                {

#line 1887
                                    if(hitA_0)
                                    {

#line 1887
                                        _S92 = float2(float(_S136), float(_S137));

#line 1887
                                    }
                                    else
                                    {

#line 1887
                                        _S92 = float2(0.0f, 0.0f);

#line 1887
                                    }

#line 1887
                                }

#line 1887
                                *_S145 = packed_float2(_S92) ;

#line 1887
                            }

#line 1887
                            bool _S146;

#line 1887
                            if(_S141)
                            {

#line 1887
                                _S146 = n2_0 != 4294967295U;

#line 1887
                            }
                            else
                            {

#line 1887
                                _S146 = false;

#line 1887
                            }

#line 1887
                            if(_S146)
                            {

#line 1887
                                int device* _S147 = (&kernelContext_1)->entryPointParams_peakIdx_0+n2_0;

#line 1887
                                if(hitB_0)
                                {

#line 1887
                                    _S143 = int(slotToIndex_0(slotB_0));

#line 1887
                                }
                                else
                                {

#line 1887
                                    _S143 = int(-1);

#line 1887
                                }

#line 1887
                                *_S147 = _S143;

#line 1887
                                packed_float2 device* _S148 = (&kernelContext_1)->entryPointParams_peakVal_0+n2_0;

#line 1887
                                if(hitLocalB_0)
                                {

#line 1887
                                    _S92 = float2(3.40282306073709653e+38f, 0.0f);

#line 1887
                                }
                                else
                                {

#line 1887
                                    if(hitB_0)
                                    {

#line 1887
                                        _S92 = float2(float(_S139), float(_S140));

#line 1887
                                    }
                                    else
                                    {

#line 1887
                                        _S92 = float2(0.0f, 0.0f);

#line 1887
                                    }

#line 1887
                                }

#line 1887
                                *_S148 = packed_float2(_S92) ;

#line 1887
                            }

#line 1887
                            break;
                        }

#line 1887
                    }

#line 1887
                    break;
                }

#line 1887
                break;
            }

#line 1887
            k_0 = k_0 + 2U;

#line 1887
        }

#line 1887
        break;
    }

    return;
}
