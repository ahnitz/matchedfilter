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

#line 10 "mm_64_fusedTierB_c16t4.slang"
constant array<uint, int(64)> COARSE_TWT_DATA_0 = { { 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 776354806U, 842939353U, 883243944U, 908016484U, 931871502U, 947010215U, 957561391U, 967326120U, 976173331U, 984037490U, 990787467U, 996423199U, 1000879269U, 1004089918U, 1005989446U, 15360U, 842939353U, 908016484U, 947010215U, 967326120U, 984037490U, 996423199U, 1004089918U, 1006632960U, 1004122686U, 996455967U, 984070258U, 967358888U, 947042983U, 908049252U, 842972121U, 15360U, 883243944U, 947010215U, 976173331U, 996423199U, 1005989446U, 1004122686U, 990820235U, 967358888U, 931904270U, 842972121U, 2923871222U, 3055532900U, 3105077807U, 3131553906U, 3148395685U } };

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


#line 5534 "core.meta.slang"
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
    array<uint, int(64)> threadgroup* stg_0;
    uint _S3;
};


#line 229 "mm_64_fusedTierB_c16t4.slang"
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 90 "twiddle.slang"
    uint _S4 = mfRowWindowsFlag_0();

#line 232 "mm_64_fusedTierB_c16t4.slang"
    if(_S4 == 0U)
    {

#line 232
        return;
    }

#line 233
    uint _S5 = 3U * d_0;

#line 233
    *winStart_1 = rowWin_0[_S5];
    *winEnd_1 = rowWin_0[_S5 + 1U];
    kernelContext_0->_binPhase_0 = rowWin_0[_S5 + 2U];
    return;
}


#line 58 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S6 = ((MF_DATA_STRIDE));

#line 61
    return _S6;
}



uint mfDataScaleFlag_0()
{
    ;
    uint _S7 = ((MF_DATA_SCALE_BITS));

#line 69
    return _S7;
}


#line 171 "mm_64_fusedTierB_c16t4.slang"
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
    uint _S8 = mfDataStrideFlag_0();

#line 259 "mm_64_fusedTierB_c16t4.slang"
    if(_S8 != 0U)
    {

#line 71 "twiddle.slang"
        uint _S9 = mfDataScaleFlag_0();

#line 260 "mm_64_fusedTierB_c16t4.slang"
        float s_0 = (as_type<float>((_S9)));
        uint _S10 = 2U * i_1;

#line 261
        return half2(half((as_type<float>((b_1[_S10]))) * s_0), half((as_type<float>((b_1[_S10 + 1U]))) * s_0));
    }
    return cload_0(b_1, i_1);
}


#line 358
void cmulconjs_0(half2 ar_0, half2 ai_0, half2 br_0, half2 bi_0, half2 thread* pr_0, half2 thread* pi_0)
{
    *pr_0 = ar_0 * br_0 + ai_0 * bi_0;
    *pi_0 = ai_0 * br_0 - ar_0 * bi_0;
    return;
}


#line 370
void r4s_0(array<half2, int(16)> thread* re_0, array<half2, int(16)> thread* im_0, uint a_0, uint b_2, uint c_0, uint d_1)
{
    half2 t0r_0 = (*re_0)[a_0] + (*re_0)[c_0];

#line 372
    half2 t0i_0 = (*im_0)[a_0] + (*im_0)[c_0];
    half2 t1r_0 = (*re_0)[a_0] - (*re_0)[c_0];

#line 373
    half2 t1i_0 = (*im_0)[a_0] - (*im_0)[c_0];
    half2 t2r_0 = (*re_0)[b_2] + (*re_0)[d_1];

#line 374
    half2 t2i_0 = (*im_0)[b_2] + (*im_0)[d_1];
    half2 t3r_0 = (*re_0)[b_2] - (*re_0)[d_1];
    half2 j3r_0 = - ((*im_0)[b_2] - (*im_0)[d_1]);
    (*re_0)[a_0] = t0r_0 + t2r_0;

#line 377
    (*im_0)[a_0] = t0i_0 + t2i_0;
    (*re_0)[b_2] = t1r_0 + j3r_0;

#line 378
    (*im_0)[b_2] = t1i_0 + t3r_0;
    (*re_0)[c_0] = t0r_0 - t2r_0;

#line 379
    (*im_0)[c_0] = t0i_0 - t2i_0;
    (*re_0)[d_1] = t1r_0 - j3r_0;

#line 380
    (*im_0)[d_1] = t1i_0 - t3r_0;
    return;
}


#line 370
void r4s_1(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint a_1, uint b_3, uint c_1, uint d_2)
{
    half2 t0r_1 = (*re_1)[a_1] + (*re_1)[c_1];

#line 372
    half2 t0i_1 = (*im_1)[a_1] + (*im_1)[c_1];
    half2 t1r_1 = (*re_1)[a_1] - (*re_1)[c_1];

#line 373
    half2 t1i_1 = (*im_1)[a_1] - (*im_1)[c_1];
    half2 t2r_1 = (*re_1)[b_3] + (*re_1)[d_2];

#line 374
    half2 t2i_1 = (*im_1)[b_3] + (*im_1)[d_2];
    half2 t3r_1 = (*re_1)[b_3] - (*re_1)[d_2];
    half2 j3r_1 = - ((*im_1)[b_3] - (*im_1)[d_2]);
    (*re_1)[a_1] = t0r_1 + t2r_1;

#line 377
    (*im_1)[a_1] = t0i_1 + t2i_1;
    (*re_1)[b_3] = t1r_1 + j3r_1;

#line 378
    (*im_1)[b_3] = t1i_1 + t3r_1;
    (*re_1)[c_1] = t0r_1 - t2r_1;

#line 379
    (*im_1)[c_1] = t0i_1 - t2i_1;
    (*re_1)[d_2] = t1r_1 - j3r_1;

#line 380
    (*im_1)[d_2] = t1i_1 - t3r_1;
    return;
}


#line 349
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 349
    half2 _S11 = half2(wr_0) ;

#line 349
    half2 _S12 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S12 + *xi_0 * _S11;
    *xr_0 = *xr_0 * _S11 - *xi_0 * _S12;

#line 353
    *xi_0 = ni_0;
    return;
}


#line 383
void swap2_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2, uint p_1, uint q_0)
{

    half2 t_0 = (*re_2)[p_1];

#line 386
    (*re_2)[p_1] = (*re_2)[q_0];

#line 386
    (*re_2)[q_0] = t_0;
    half2 t_1 = (*im_2)[p_1];

#line 387
    (*im_2)[p_1] = (*im_2)[q_0];

#line 387
    (*im_2)[q_0] = t_1;
    return;
}


#line 383
void swap2_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint p_2, uint q_1)
{

    half2 t_2 = (*re_3)[p_2];

#line 386
    (*re_3)[p_2] = (*re_3)[q_1];

#line 386
    (*re_3)[q_1] = t_2;
    half2 t_3 = (*im_3)[p_2];

#line 387
    (*im_3)[p_2] = (*im_3)[q_1];

#line 387
    (*im_3)[q_1] = t_3;
    return;
}


#line 421
void dft16s_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4)
{

#line 421
    uint n1_0 = 0U;

    for(;;)
    {

#line 423
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 423
            break;
        }

#line 423
        r4s_0(re_4, im_4, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 423
        n1_0 = n1_0 + 1U;

#line 423
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

#line 434
    uint k2_0 = 0U;
    for(;;)
    {

#line 435
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 435
            break;
        }

#line 436
        uint _S13 = 4U * k2_0;

#line 436
        r4s_0(re_4, im_4, _S13, _S13 + 1U, _S13 + 2U, _S13 + 3U);

#line 435
        k2_0 = k2_0 + 1U;

#line 435
    }

    swap2_0(re_4, im_4, 1U, 4U);

#line 437
    swap2_0(re_4, im_4, 2U, 8U);

#line 437
    swap2_0(re_4, im_4, 3U, 12U);
    swap2_0(re_4, im_4, 6U, 9U);

#line 438
    swap2_0(re_4, im_4, 7U, 13U);

#line 438
    swap2_0(re_4, im_4, 11U, 14U);
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
    float c_2 = 1.0f + z_0 * (-0.5f + z_0 * (0.0416666679084301f + z_0 * (-0.00138888892251998f + z_0 * (0.00002480158764229f + z_0 * -2.75573199814971304e-07f))));

    float s_1 = x_0 * (1.0f + z_0 * (-0.1666666716337204f + z_0 * (0.00833333376795053f + z_0 * (-0.0001984127011383f + z_0 * (2.75573188446287531e-06f + z_0 * -2.50521079436794025e-08f)))));


    switch(quadrant_0 & int(3))
    {
    case int(1):
        {

#line 117
            return float2(- s_1, c_2);
        }
    case int(2):
        {

#line 118
            return float2(- c_2, - s_1);
        }
    case int(3):
        {

#line 119
            return float2(s_1, - c_2);
        }
    default:
        {

#line 120
            return float2(c_2, s_1);
        }
    }

#line 120
}


#line 326 "mm_64_fusedTierB_c16t4.slang"
uint computeWant_0(uint d_3, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S18 = max(TB_0, 1U);

#line 328
    uint j_0 = d_3 / _S18;

#line 328
    uint m_0 = d_3 % _S18;

#line 328
    uint _S19;
    if(TB_0 <= 16U)
    {

#line 329
        _S19 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 329
    }
    else
    {

#line 329
        _S19 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_3;

#line 329
    }

#line 329
    return _S19;
}


#line 302
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 302
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 302
    return;
}


#line 303
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_2)
{

#line 303
    return half2(as_type<half>(ushort(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 459
void exchangeS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_3)
{
    uint j_1;

    thread array<half2, int(16)> outr_0;

#line 463
    thread array<half2, int(16)> outi_0;

#line 463
    uint z_1 = 0U;
    for(;;)
    {

#line 464
        if(z_1 < 16U)
        {
        }
        else
        {

#line 464
            break;
        }

#line 464
        half2 _S20 = half2(float2(0.0f) );

#line 464
        outr_0[z_1] = _S20;

#line 464
        outi_0[z_1] = _S20;

#line 464
        z_1 = z_1 + 1U;

#line 464
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S21 = p0_0 & lenMask_0;
    uint _S22 = (_S21 >> lgSpan_0) * 4U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S21 & spanMask_0);

#line 469
    uint c_3 = 0U;
    for(;;)
    {

#line 470
        if(c_3 < 1U)
        {
        }
        else
        {

#line 470
            break;
        }

#line 470
        for(;;)
        {

#line 470
            for(;;)
            {

#line 471
                for(;;)
                {

#line 472
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 472
                    j_1 = 0U;
                    for(;;)
                    {

#line 473
                        if(j_1 < 16U)
                        {
                        }
                        else
                        {

#line 473
                            break;
                        }

#line 474
                        uint _S23 = j_1 * 4U + kernelContext_3->_tid_0;

#line 474
                        stgPut_0(_S23, (*re_5)[c_3 * 16U + j_1], kernelContext_3);

#line 473
                        j_1 = j_1 + 1U;

#line 473
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 475
                    uint d_4 = 0U;
                    for(;;)
                    {

#line 476
                        if(d_4 < 16U)
                        {
                        }
                        else
                        {

#line 476
                            break;
                        }
                        uint pz_0 = computeWant_0(d_4, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S24 = pz_0 & lenMask_0;
                        uint az_0 = (_S24 >> lgSpan_0) * 4U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S24 & spanMask_0);

#line 480
                        half2 _S25 = stgGet_0(_S22 + az_0 - c_3 * 16U * 4U, kernelContext_3);



                        outr_0[d_4] = _S25;

#line 476
                        d_4 = d_4 + 1U;

#line 476
                    }

#line 471
                    break;
                }

#line 471
                break;
            }

#line 471
            for(;;)
            {

#line 471
                for(;;)
                {

#line 472
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 472
                    uint j_2 = 0U;
                    for(;;)
                    {

#line 473
                        if(j_2 < 16U)
                        {
                        }
                        else
                        {

#line 473
                            break;
                        }

#line 474
                        uint _S26 = j_2 * 4U + kernelContext_3->_tid_0;

#line 474
                        stgPut_0(_S26, (*im_5)[c_3 * 16U + j_2], kernelContext_3);

#line 473
                        j_2 = j_2 + 1U;

#line 473
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 475
                    uint d_5 = 0U;
                    for(;;)
                    {

#line 476
                        if(d_5 < 16U)
                        {
                        }
                        else
                        {

#line 476
                            break;
                        }
                        uint pz_1 = computeWant_0(d_5, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S27 = pz_1 & lenMask_0;
                        uint az_1 = (_S27 >> lgSpan_0) * 4U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S27 & spanMask_0);

#line 480
                        half2 _S28 = stgGet_0(_S22 + az_1 - c_3 * 16U * 4U, kernelContext_3);



                        outi_0[d_5] = _S28;

#line 476
                        d_5 = d_5 + 1U;

#line 476
                    }

#line 471
                    break;
                }

#line 471
                break;
            }

#line 471
            break;
        }

#line 470
        c_3 = c_3 + 1U;

#line 470
    }

#line 470
    j_1 = 0U;

#line 489
    for(;;)
    {

#line 489
        if(j_1 < 16U)
        {
        }
        else
        {

#line 489
            break;
        }

#line 489
        (*re_5)[j_1] = outr_0[j_1];

#line 489
        (*im_5)[j_1] = outi_0[j_1];

#line 489
        j_1 = j_1 + 1U;

#line 489
    }
    return;
}


#line 397
void dft4s_0(array<half2, int(16)> thread* re_6, array<half2, int(16)> thread* im_6, uint o_0)
{
    uint _S29 = o_0 + 1U;

#line 399
    uint _S30 = o_0 + 2U;

#line 399
    r4s_1(re_6, im_6, o_0, _S29, _S30, o_0 + 3U);
    swap2_1(re_6, im_6, _S29, _S30);
    return;
}


#line 492
void innermostS_0(array<half2, int(16)> thread* re_7, array<half2, int(16)> thread* im_7)
{

#line 492
    uint b_4 = 0U;



    for(;;)
    {

#line 496
        if(b_4 < 4U)
        {
        }
        else
        {

#line 496
            break;
        }

#line 496
        dft4s_0(re_7, im_7, b_4 * 4U);

#line 496
        b_4 = b_4 + 1U;

#line 496
    }

    return;
}


#line 785
uint lgOf_0(uint i_4)
{

#line 785
    uint _S31;

#line 785
    if(i_4 < 1U)
    {

#line 785
        _S31 = 4U;

#line 785
    }
    else
    {

#line 785
        _S31 = 1U;

#line 785
    }

#line 785
    return _S31;
}


#line 787
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 791
    uint lg_1 = lgOf_0(1U);

#line 791
    uint lg_2 = lgOf_0(0U);

#line 796
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 445
half2 mag2s_0(half2 re_8, half2 im_8)
{

#line 445
    return re_8 * re_8 + im_8 * im_8;
}


#line 1326
uint mfShflXor_0(uint v_1, uint s_2, KernelContext_0 thread* kernelContext_4)
{

#line 1326
    uint _S32 = (simd_shuffle((v_1), ushort((int((kernelContext_4->_S3) ^ s_2)))));

#line 1326
    return _S32;
}


#line 1428
void peakTwoGate_0(uint pairA_0, uint pairB_0, uint tid_0, const array<half2, int(16)> thread* re_9, const array<half2, int(16)> thread* im_9, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, float thr_0, KernelContext_0 thread* kernelContext_5)
{


    uint _S33 = slotToIndex_0(tid_0 * 16U) - winStart_2;
    uint _S34 = winEnd_2 - winStart_2;
    half2 _S35 = half2(float2(0.0f) );
    half2 _S36 = half2(float2(0.015625f) );

#line 1435
    uint i_5 = 0U;

#line 1435
    half2 best_0 = _S35;

#line 1435
    half2 en_0 = _S35;
    for(;;)
    {

#line 1436
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1436
            break;
        }

#line 1436
        half2 _S37;

        if((_S33 + slotToIndex_0(i_5)) < _S34)
        {

#line 1438
            _S37 = mag2s_0((*re_9)[i_5], (*im_9)[i_5]);

#line 1438
        }
        else
        {

#line 1438
            _S37 = _S35;

#line 1438
        }

#line 1438
        half2 _S38 = max(best_0, _S37);
        half2 sr_0 = (*re_9)[i_5] * _S36;

#line 1439
        half2 si_0 = (*im_9)[i_5] * _S36;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1436
        i_5 = i_5 + 1U;

#line 1436
        best_0 = _S38;

#line 1436
        en_0 = en_1;

#line 1436
    }

#line 1436
    uint _S39 = mfShflXor_0((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U), 1U, kernelContext_5);

#line 1443
    half2 _S40 = max(best_0, half2(as_type<half>(ushort(_S39 & 65535U)), as_type<half>(ushort((_S39 >> 16U) & 65535U))));

#line 1443
    uint _S41 = mfShflXor_0((uint(as_type<ushort>(en_0[0U])) & 65535U) | (uint(as_type<ushort>(en_0[1U])) << 16U), 1U, kernelContext_5);
    half2 en_2 = en_0 + half2(as_type<half>(ushort(_S41 & 65535U)), as_type<half>(ushort((_S41 >> 16U) & 65535U)));

#line 1444
    uint _S42 = mfShflXor_0((uint(as_type<ushort>(_S40[0U])) & 65535U) | (uint(as_type<ushort>(_S40[1U])) << 16U), 2U, kernelContext_5);

#line 1443
    half2 best_1 = max(_S40, half2(as_type<half>(ushort(_S42 & 65535U)), as_type<half>(ushort((_S42 >> 16U) & 65535U))));

#line 1443
    uint _S43 = mfShflXor_0((uint(as_type<ushort>(en_2[0U])) & 65535U) | (uint(as_type<ushort>(en_2[1U])) << 16U), 2U, kernelContext_5);
    half2 en_3 = en_2 + half2(as_type<half>(ushort(_S43 & 65535U)), as_type<half>(ushort((_S43 >> 16U) & 65535U)));

#line 1444
    uint _S44 = (uint(as_type<ushort>(en_3[0U])) & 65535U) | (uint(as_type<ushort>(en_3[1U])) << 16U);

#line 1444
    uint _S45 = (uint(as_type<ushort>(best_1[0U])) & 65535U) | (uint(as_type<ushort>(best_1[1U])) << 16U);

#line 1444
    bool infA_0;

#line 1452
    if((_S44 & 31744U) == 31744U)
    {

#line 1452
        infA_0 = true;

#line 1452
    }
    else
    {

#line 1452
        infA_0 = (_S45 & 31744U) == 31744U;

#line 1452
    }

#line 1452
    bool infB_0;
    if((_S44 & 2080374784U) == 2080374784U)
    {

#line 1453
        infB_0 = true;

#line 1453
    }
    else
    {

#line 1453
        infB_0 = (_S45 & 2080374784U) == 2080374784U;

#line 1453
    }
    float bA_0 = sqrt(float(best_1.x));

#line 1454
    float bB_0 = sqrt(float(best_1.y));

#line 1454
    bool hitA_0;
    if(infA_0)
    {

#line 1455
        hitA_0 = true;

#line 1455
    }
    else
    {

#line 1455
        if(bA_0 > 0.0f)
        {

#line 1455
            hitA_0 = bA_0 >= thr_0;

#line 1455
        }
        else
        {

#line 1455
            hitA_0 = false;

#line 1455
        }

#line 1455
    }

#line 1455
    bool hitB_0;
    if(infB_0)
    {

#line 1456
        hitB_0 = true;

#line 1456
    }
    else
    {

#line 1456
        if(bB_0 > 0.0f)
        {

#line 1456
            hitB_0 = bB_0 >= thr_0;

#line 1456
        }
        else
        {

#line 1456
            hitB_0 = false;

#line 1456
        }

#line 1456
    }
    bool _S46 = tid_0 == 0U;

#line 1457
    bool _S47;

#line 1457
    if(_S46)
    {

#line 1457
        _S47 = pairA_0 != 4294967295U;

#line 1457
    }
    else
    {

#line 1457
        _S47 = false;

#line 1457
    }

#line 1457
    int _S48;

#line 1457
    float2 _S49;

#line 1457
    if(_S47)
    {

#line 1458
        int device* _S50 = peakIdx_0+pairA_0;

#line 1458
        if(hitA_0)
        {

#line 1458
            _S48 = int(0);

#line 1458
        }
        else
        {

#line 1458
            _S48 = int(-1);

#line 1458
        }

#line 1458
        *_S50 = _S48;

#line 1458
        packed_float2 device* _S51 = peakVal_0+pairA_0;
        if(infA_0)
        {

#line 1459
            _S49 = float2(3.40282306073709653e+38f, 0.0f);

#line 1459
        }
        else
        {

#line 1459
            if(hitA_0)
            {

#line 1459
                _S49 = float2(bA_0, 0.0f);

#line 1459
            }
            else
            {

#line 1459
                _S49 = float2(0.0f, 0.0f);

#line 1459
            }

#line 1459
        }

#line 1459
        *_S51 = packed_float2(_S49) ;

#line 1457
    }



    if(_S46)
    {

#line 1461
        infA_0 = pairB_0 != 4294967295U;

#line 1461
    }
    else
    {

#line 1461
        infA_0 = false;

#line 1461
    }

#line 1461
    if(infA_0)
    {

#line 1462
        int device* _S52 = peakIdx_0+pairB_0;

#line 1462
        if(hitB_0)
        {

#line 1462
            _S48 = int(0);

#line 1462
        }
        else
        {

#line 1462
            _S48 = int(-1);

#line 1462
        }

#line 1462
        *_S52 = _S48;

#line 1462
        packed_float2 device* _S53 = peakVal_0+pairB_0;
        if(infB_0)
        {

#line 1463
            _S49 = float2(3.40282306073709653e+38f, 0.0f);

#line 1463
        }
        else
        {

#line 1463
            if(hitB_0)
            {

#line 1463
                _S49 = float2(bB_0, 0.0f);

#line 1463
            }
            else
            {

#line 1463
                _S49 = float2(0.0f, 0.0f);

#line 1463
            }

#line 1463
        }

#line 1463
        *_S53 = packed_float2(_S49) ;

#line 1461
    }



    return;
}


#line 1329
void peakTwoWave_0(uint pairA_1, uint pairB_1, uint tid_1, const array<half2, int(16)> thread* re_10, const array<half2, int(16)> thread* im_10, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_1, KernelContext_0 thread* kernelContext_6)
{
    uint m_1;

#line 1331
    bool _S54;

#line 1331
    bool _S55;

    uint _S56 = slotToIndex_0(tid_1 * 16U) - winStart_3;
    uint _S57 = winEnd_3 - winStart_3;

#line 1334
    uint i_6 = 0U;

#line 1334
    uint ovAcc_0 = 0U;

#line 1334
    uint kA_0 = 0U;

#line 1334
    uint kB_0 = 0U;

#line 1339
    for(;;)
    {

#line 1339
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1339
            break;
        }
        half2 mg_0 = mag2s_0((*re_10)[i_6], (*im_10)[i_6]);
        if((_S56 + slotToIndex_0(i_6)) < _S57)
        {

#line 1342
            m_1 = (uint(as_type<ushort>(mg_0[0U])) & 65535U) | (uint(as_type<ushort>(mg_0[1U])) << 16U);

#line 1342
        }
        else
        {

#line 1342
            m_1 = 0U;

#line 1342
        }

#line 1348
        uint ovAcc_1 = ovAcc_0 | (((((uint(as_type<ushort>((*re_10)[i_6].x)) & 65535U) | (uint(as_type<ushort>((*re_10)[i_6].y)) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>((*im_10)[i_6].x)) & 65535U) | (uint(as_type<ushort>((*im_10)[i_6].y)) << 16U)) & 2080406528U) + 67109888U));


        uint _S58 = 15U - i_6;

#line 1351
        uint _S59 = max(kA_0, (m_1 << 16U) | _S58);
        uint _S60 = max(kB_0, (m_1 & 4294901760U) | _S58);

#line 1339
        i_6 = i_6 + 1U;

#line 1339
        ovAcc_0 = ovAcc_1;

#line 1339
        kA_0 = _S59;

#line 1339
        kB_0 = _S60;

#line 1339
    }

#line 1356
    if((ovAcc_0 & 32768U) != 0U)
    {

#line 1356
        kA_0 = max(kA_0, 2080374799U);

#line 1356
    }
    if((ovAcc_0 & 2147483648U) != 0U)
    {

#line 1357
        kB_0 = max(kB_0, 2080374799U);

#line 1357
    }


    uint _S61 = (4095U - tid_1) << 4U;

#line 1360
    uint kA_1 = kA_0 | _S61;
    uint kB_1 = kB_0 | _S61;

#line 1361
    uint _S62 = mfShflXor_0(kA_1, 1U, kernelContext_6);

    uint _S63 = max(kA_1, _S62);

#line 1363
    uint _S64 = mfShflXor_0(kB_1, 1U, kernelContext_6);
    uint _S65 = max(kB_1, _S64);

#line 1364
    uint _S66 = mfShflXor_0(_S63, 2U, kernelContext_6);

#line 1363
    uint _S67 = max(_S63, _S66);

#line 1363
    uint _S68 = mfShflXor_0(_S65, 2U, kernelContext_6);
    uint _S69 = max(_S65, _S68);

    uint slotA_0 = 65535U - (_S67 & 65535U);

#line 1366
    uint slotB_0 = 65535U - (_S69 & 65535U);

#line 1372
    uint _S70 = _S67 >> 16U;

#line 1372
    bool infA_1 = _S70 >= 31744U;

#line 1372
    uint _S71 = _S69 >> 16U;

#line 1372
    bool infB_1 = _S71 >= 31744U;

#line 1372
    bool hitA_1;



    if(infA_1)
    {

#line 1376
        hitA_1 = true;

#line 1376
    }
    else
    {

#line 1376
        hitA_1 = (as_type<half>((ushort)((_S70)))) > (as_type<float>((thrBits_1)));

#line 1376
    }

#line 1376
    bool hitB_1;
    if(infB_1)
    {

#line 1377
        hitB_1 = true;

#line 1377
    }
    else
    {

#line 1377
        hitB_1 = (as_type<half>((ushort)((_S71)))) > (as_type<float>((thrBits_1)));

#line 1377
    }

#line 1385
    uint _S72 = slotA_0 >> 4U;

#line 1385
    uint _S73 = slotA_0 & 15U;

#line 1385
    uint _S74 = slotB_0 >> 4U;

#line 1385
    uint _S75 = slotB_0 & 15U;
    thread array<float, int(2)> vA_0;

#line 1386
    thread array<float, int(2)> vB_0;
    vB_0[int(1)] = 0.0f;

#line 1387
    vB_0[int(0)] = 0.0f;

#line 1387
    vA_0[int(1)] = 0.0f;

#line 1387
    vA_0[int(0)] = 0.0f;

#line 1387
    for(;;)
    {

#line 1387
        for(;;)
        {

#line 1388
            for(;;)
            {

#line 1388
                for(;;)
                {

#line 1388
                    for(;;)
                    {

#line 1389
                        for(;;)
                        {

#line 1390
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1390
                            m_1 = 0U;
                            for(;;)
                            {

#line 1391
                                if(m_1 < 16U)
                                {
                                }
                                else
                                {

#line 1391
                                    break;
                                }

#line 1392
                                (*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + m_1 * 4U + tid_1] = (uint(as_type<ushort>((*re_10)[m_1].x)) & 65535U) | (uint(as_type<ushort>((*re_10)[m_1].y)) << 16U);

#line 1391
                                m_1 = m_1 + 1U;

#line 1391
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            bool _S76 = tid_1 == 0U;

#line 1394
                            _S54 = _S76;

#line 1394
                            if(_S76)
                            {

#line 1395
                                if(_S73 >= 0U)
                                {

#line 1395
                                    _S55 = _S73 < 16U;

#line 1395
                                }
                                else
                                {

#line 1395
                                    _S55 = false;

#line 1395
                                }

#line 1395
                                if(_S55)
                                {

#line 1396
                                    vA_0[0U] = (as_type<half>((ushort)(((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S73 * 4U + _S72]))));

#line 1395
                                }

                                if(_S75 >= 0U)
                                {

#line 1397
                                    _S55 = _S75 < 16U;

#line 1397
                                }
                                else
                                {

#line 1397
                                    _S55 = false;

#line 1397
                                }

#line 1397
                                if(_S55)
                                {

#line 1398
                                    vB_0[0U] = (as_type<half>((ushort)((((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S75 * 4U + _S74]) >> 16U))));

#line 1397
                                }

#line 1394
                            }

#line 1389
                            break;
                        }

#line 1389
                        break;
                    }

#line 1389
                    break;
                }

#line 1388
                break;
            }

#line 1388
            break;
        }

#line 1388
        for(;;)
        {

#line 1388
            for(;;)
            {

#line 1388
                for(;;)
                {

#line 1388
                    for(;;)
                    {

#line 1389
                        for(;;)
                        {

#line 1390
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1390
                            m_1 = 0U;
                            for(;;)
                            {

#line 1391
                                if(m_1 < 16U)
                                {
                                }
                                else
                                {

#line 1391
                                    break;
                                }

#line 1392
                                (*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + m_1 * 4U + tid_1] = (uint(as_type<ushort>((*im_10)[m_1].x)) & 65535U) | (uint(as_type<ushort>((*im_10)[m_1].y)) << 16U);

#line 1391
                                m_1 = m_1 + 1U;

#line 1391
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            if(_S54)
                            {

#line 1395
                                if(_S73 >= 0U)
                                {

#line 1395
                                    _S55 = _S73 < 16U;

#line 1395
                                }
                                else
                                {

#line 1395
                                    _S55 = false;

#line 1395
                                }

#line 1395
                                if(_S55)
                                {

#line 1396
                                    vA_0[1U] = (as_type<half>((ushort)(((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S73 * 4U + _S72]))));

#line 1395
                                }

                                if(_S75 >= 0U)
                                {

#line 1397
                                    _S55 = _S75 < 16U;

#line 1397
                                }
                                else
                                {

#line 1397
                                    _S55 = false;

#line 1397
                                }

#line 1397
                                if(_S55)
                                {

#line 1398
                                    vB_0[1U] = (as_type<half>((ushort)((((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S75 * 4U + _S74]) >> 16U))));

#line 1397
                                }

#line 1394
                            }

#line 1389
                            break;
                        }

#line 1389
                        break;
                    }

#line 1389
                    break;
                }

#line 1388
                break;
            }

#line 1388
            break;
        }

#line 1388
        break;
    }

#line 1402
    if(_S54)
    {

#line 1402
        _S55 = pairA_1 != 4294967295U;

#line 1402
    }
    else
    {

#line 1402
        _S55 = false;

#line 1402
    }

#line 1402
    int _S77;

#line 1402
    float2 _S78;

#line 1402
    if(_S55)
    {

#line 1403
        int device* _S79 = peakIdx_1+pairA_1;

#line 1403
        if(hitA_1)
        {

#line 1403
            _S77 = int(slotToIndex_0(slotA_0));

#line 1403
        }
        else
        {

#line 1403
            _S77 = int(-1);

#line 1403
        }

#line 1403
        *_S79 = _S77;

#line 1403
        packed_float2 device* _S80 = peakVal_1+pairA_1;
        if(infA_1)
        {

#line 1404
            _S78 = float2(3.40282306073709653e+38f, 0.0f);

#line 1404
        }
        else
        {

#line 1405
            if(hitA_1)
            {

#line 1405
                _S78 = float2(vA_0[int(0)], vA_0[int(1)]);

#line 1405
            }
            else
            {

#line 1405
                _S78 = float2(0.0f, 0.0f);

#line 1405
            }

#line 1404
        }

#line 1404
        *_S80 = packed_float2(_S78) ;

#line 1402
    }

#line 1407
    if(_S54)
    {

#line 1407
        hitA_1 = pairB_1 != 4294967295U;

#line 1407
    }
    else
    {

#line 1407
        hitA_1 = false;

#line 1407
    }

#line 1407
    if(hitA_1)
    {

#line 1408
        int device* _S81 = peakIdx_1+pairB_1;

#line 1408
        if(hitB_1)
        {

#line 1408
            _S77 = int(slotToIndex_0(slotB_0));

#line 1408
        }
        else
        {

#line 1408
            _S77 = int(-1);

#line 1408
        }

#line 1408
        *_S81 = _S77;

#line 1408
        packed_float2 device* _S82 = peakVal_1+pairB_1;
        if(infB_1)
        {

#line 1409
            _S78 = float2(3.40282306073709653e+38f, 0.0f);

#line 1409
        }
        else
        {

#line 1410
            if(hitB_1)
            {

#line 1410
                _S78 = float2(vB_0[int(0)], vB_0[int(1)]);

#line 1410
            }
            else
            {

#line 1410
                _S78 = float2(0.0f, 0.0f);

#line 1410
            }

#line 1409
        }

#line 1409
        *_S82 = packed_float2(_S78) ;

#line 1407
    }

#line 1412
    return;
}


#line 1471
void filterTwo_0(uint pairA_2, uint pairB_2, uint tA_0, uint tB_0, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* tmpl_0, int device* peakIdx_2, packed_float2 device* peakVal_2, uint winStart_4, uint winEnd_4, uint thrBits_2, KernelContext_0 thread* kernelContext_7)
{



    thread array<half2, int(16)> re_11;

#line 1476
    thread array<half2, int(16)> im_11;

#line 1476
    uint n2_0 = 0U;
    for(;;)
    {

#line 1477
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 1477
            break;
        }

#line 1478
        uint _S83 = 4U * n2_0;

#line 1478
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 64U + tid_2 + _S83);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 64U + tid_2 + _S83);
        half _S84 = (*dreg_0)[n2_0].x;
        half _S85 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S84, _S84), half2(_S85, _S85), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_11[n2_0], &im_11[n2_0]);

#line 1477
        n2_0 = n2_0 + 1U;

#line 1477
    }

#line 1490
    uint lgTB_0 = firstbithigh_0(4U);
    uint lgLn_0 = firstbithigh_0(64U);
    uint blk_2 = tid_2 >> lgTB_0;
    uint lane_2 = tid_2 & 3U;

    dft16s_0(&re_11, &im_11);

#line 52 "twiddle.slang"
    uint _S86 = mfCoarseTwtFlag_0();

#line 52
    uint k2_1;

#line 1497 "mm_64_fusedTierB_c16t4.slang"
    if(_S86 != 0U)
    {

#line 1497
        k2_1 = 0U;

#line 1504
        for(;;)
        {

#line 1504
            if(k2_1 < 16U)
            {
            }
            else
            {

#line 1504
                break;
            }

#line 1505
            uint _S87 = lane_2 * 16U + k2_1;
            cmulw_0(&re_11[k2_1], &im_11[k2_1], as_type<half>(ushort((COARSE_TWT_DATA_0[_S87]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S87]) >> 16U) & 65535U)));

#line 1504
            k2_1 = k2_1 + 1U;

#line 1504
        }

#line 1497
    }
    else
    {

#line 1513
        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 64.0f);
        float _S88 = tw_0.x;

#line 1514
        float _S89 = tw_0.y;

#line 1514
        k2_1 = 0U;

#line 1514
        float cr_0 = 1.0f;

#line 1514
        float ci_0 = 0.0f;

        for(;;)
        {

#line 1516
            if(k2_1 < 16U)
            {
            }
            else
            {

#line 1516
                break;
            }

#line 1517
            cmulw_0(&re_11[k2_1], &im_11[k2_1], half(cr_0), half(ci_0));
            float nr_0 = cr_0 * _S88 - ci_0 * _S89;
            float _S90 = cr_0 * _S89 + ci_0 * _S88;

#line 1516
            k2_1 = k2_1 + 1U;

#line 1516
            cr_0 = nr_0;

#line 1516
            ci_0 = _S90;

#line 1516
        }

#line 1497
    }

#line 1523
    uint per_2 = 16U / max(4U, 1U);
    uint _S91 = max(0U, 1U);
    uint blk2_2 = tid_2 / _S91;

#line 1525
    uint lane2_2 = tid_2 % _S91;

#line 1525
    exchangeS_0(&re_11, &im_11, lgLn_0, lgTB_0, 4U, 64U, blk_2, lane_2, per_2, _S91, 4U, blk2_2, lane2_2, kernelContext_7);


    innermostS_0(&re_11, &im_11);

#line 1547
    if(thrBits_2 != 0U)
    {

#line 1548
        float _S92 = (as_type<float>((thrBits_2)));

#line 1548
        thread array<half2, int(16)> _S93 = re_11;

#line 1548
        thread array<half2, int(16)> _S94 = im_11;

#line 1548
        peakTwoGate_0(pairA_2, pairB_2, tid_2, &_S93, &_S94, peakIdx_2, peakVal_2, winStart_4, winEnd_4, _S92, kernelContext_7);

#line 1547
    }
    else
    {

#line 1547
        thread array<half2, int(16)> _S95 = re_11;

#line 1547
        thread array<half2, int(16)> _S96 = im_11;

#line 1547
        peakTwoWave_0(pairA_2, pairB_2, tid_2, &_S95, &_S96, peakIdx_2, peakVal_2, winStart_4, winEnd_4, thrBits_2, kernelContext_7);

#line 1547
    }

#line 1575
    return;
}


void filterPair_0(uint pair_0, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_3, packed_float2 device* peakVal_3, uint ntmpl_1, uint winStart_5, uint winEnd_5, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, uint device* rowWin_1, KernelContext_0 thread* kernelContext_8)
{

#line 1579
    thread uint _S97 = winStart_5;

#line 1579
    thread uint _S98 = winEnd_5;

#line 1585
    kernelContext_8->_tid_0 = tid_3;

#line 1605
    uint tiles_0 = (ntmpl_1 + 4U - 1U) / 4U;
    uint slots_0 = binsize_1 * tiles_0;
    bool slotOk_0 = pair_0 < slots_0;

#line 1607
    uint q_2;
    if(slotOk_0)
    {

#line 1608
        q_2 = pair_0;

#line 1608
    }
    else
    {

#line 1608
        q_2 = slots_0 - 1U;

#line 1608
    }
    uint d_6 = q_2 / tiles_0;

#line 1609
    uint t0_0 = (q_2 - d_6 * tiles_0) * 4U;
    uint _S99 = d_6 * ntmpl_1 + t0_0;

#line 1610
    rowWindow_0(d_6, &_S97, &_S98, rowWin_1, kernelContext_8);

#line 1635
    thread array<half2, int(16)> dreg_1;

#line 1635
    uint n2_1 = 0U;

    for(;;)
    {

#line 1637
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1637
            break;
        }

#line 63 "twiddle.slang"
        uint _S100 = mfDataStrideFlag_0();

#line 178 "mm_64_fusedTierB_c16t4.slang"
        if(_S100 != 0U)
        {

#line 63 "twiddle.slang"
            uint _S101 = mfDataStrideFlag_0();

#line 63
            q_2 = _S101;

#line 178 "mm_64_fusedTierB_c16t4.slang"
        }
        else
        {

#line 178
            q_2 = 64U;

#line 178
        }

#line 1638
        half2 _S102 = dload_0(data_0, d_6 * q_2 + tid_3 + 4U * n2_1);

#line 1638
        dreg_1[n2_1] = _S102;

#line 1637
        n2_1 = n2_1 + 1U;

#line 1637
    }

#line 1637
    uint k_0 = 0U;

#line 1645
    for(;;)
    {

#line 1645
        if(k_0 < 4U)
        {
        }
        else
        {

#line 1645
            break;
        }

#line 1645
        bool okA_0;
        if(slotOk_0)
        {

#line 1646
            okA_0 = (t0_0 + k_0) < ntmpl_1;

#line 1646
        }
        else
        {

#line 1646
            okA_0 = false;

#line 1646
        }

#line 1646
        bool okB_0;

#line 1646
        if(slotOk_0)
        {

#line 1646
            okB_0 = (t0_0 + k_0 + 1U) < ntmpl_1;

#line 1646
        }
        else
        {

#line 1646
            okB_0 = false;

#line 1646
        }
        if(okA_0)
        {

#line 1647
            q_2 = _S99 + k_0;

#line 1647
        }
        else
        {

#line 1647
            q_2 = 4294967295U;

#line 1647
        }

#line 1647
        if(okB_0)
        {

#line 1647
            n2_1 = _S99 + k_0 + 1U;

#line 1647
        }
        else
        {

#line 1647
            n2_1 = 4294967295U;

#line 1647
        }
        uint _S103 = t0_0 + k_0;

#line 1648
        uint _S104 = ntmpl_1 - 1U;

#line 1648
        uint _S105 = min(_S103, _S104);

#line 1648
        uint _S106 = min(_S103 + 1U, _S104);

#line 1648
        thread array<half2, int(16)> _S107 = dreg_1;

#line 1648
        filterTwo_0(q_2, n2_1, _S105, _S106, tid_3, &_S107, tmpl_1, peakIdx_3, peakVal_3, _S97, _S98, thrBits_3, kernelContext_8);

#line 1645
        k_0 = k_0 + 2U;

#line 1645
    }

#line 1661
    return;
}


#line 1674
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], uint _builtinWaveLaneIndex_0 [[thread_index_in_simdgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1674
    thread KernelContext_0 kernelContext_9;

#line 1674
    (&kernelContext_9)->entryPointParams_0 = entryPointParams_1;

#line 1674
    (&kernelContext_9)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1674
    (&kernelContext_9)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1674
    (&kernelContext_9)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1674
    (&kernelContext_9)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1674
    (&kernelContext_9)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1674
    threadgroup array<uint, int(64)> stg_1;

#line 1674
    (&kernelContext_9)->stg_0 = &stg_1;

#line 1674
    (&kernelContext_9)->_binPhase_0 = 0U;

#line 1674
    (&kernelContext_9)->_S3 = _builtinWaveLaneIndex_0;

#line 1691
    uint _pr_0 = gid_0.x;

#line 1691
    uint _t_0 = lid_0.x;
    (&kernelContext_9)->_stgBase_0 = 0U;

#line 1692
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, entryPointParams_rowWin_1, &kernelContext_9);

#line 1709
    return;
}
