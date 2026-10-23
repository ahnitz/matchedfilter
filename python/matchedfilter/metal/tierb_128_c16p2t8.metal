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

#line 11 "mm_128_fusedTierB_c16p2t8.slang"
constant array<uint, int(128)> COARSE_TWT_DATA_0 = { { 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 709377022U, 776354806U, 816987114U, 842939353U, 868629443U, 883243944U, 895761288U, 908016484U, 920075067U, 931871502U, 941439709U, 947010215U, 952384109U, 957561391U, 962542061U, 15360U, 776354806U, 842939353U, 883243944U, 908016484U, 931871502U, 947010215U, 957561391U, 967326120U, 976173331U, 984037490U, 990787467U, 996423199U, 1000879269U, 1004089918U, 1005989446U, 15360U, 816987114U, 883243944U, 920075067U, 947010215U, 962542061U, 976173331U, 987576349U, 996423199U, 1002648518U, 1005989446U, 1006545480U, 1004122686U, 998815076U, 990820235U, 980269252U, 15360U, 842939353U, 908016484U, 947010215U, 967326120U, 984037490U, 996423199U, 1004089918U, 1006632960U, 1004122686U, 996455967U, 984070258U, 967358888U, 947042983U, 908049252U, 842972121U, 15360U, 868629443U, 931871502U, 962542061U, 984037490U, 998782308U, 1005989446U, 1005236402U, 996455967U, 980269252U, 957594159U, 920107835U, 842972121U, 2856893438U, 3030760360U, 3088956125U, 15360U, 883243944U, 947010215U, 976173331U, 996423199U, 1005989446U, 1004122686U, 990820235U, 967358888U, 931904270U, 842972121U, 2923871222U, 3055532900U, 3105077807U, 3131553906U, 3148395685U, 15360U, 895761288U, 957561391U, 987576349U, 1004089918U, 1005236402U, 990820235U, 962574829U, 908049252U, 709409790U, 3030760360U, 3099900525U, 3131553906U, 3150164934U, 3153473094U, 3141220055U } };

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
    array<uint, int(256)> threadgroup* stg_0;
    uint _S3;
};


#line 230 "mm_128_fusedTierB_c16p2t8.slang"
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 104 "twiddle.slang"
    uint _S4 = mfRowWindowsFlag_0();

#line 233 "mm_128_fusedTierB_c16p2t8.slang"
    if(_S4 == 0U)
    {

#line 233
        return;
    }

#line 234
    uint _S5 = 3U * d_0;

#line 234
    *winStart_1 = rowWin_0[_S5];
    *winEnd_1 = rowWin_0[_S5 + 1U];
    kernelContext_0->_binPhase_0 = rowWin_0[_S5 + 2U];
    return;
}


#line 72 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S6 = ((MF_DATA_STRIDE));

#line 75
    return _S6;
}



uint mfDataScaleFlag_0()
{
    ;
    uint _S7 = ((MF_DATA_SCALE_BITS));

#line 83
    return _S7;
}


#line 172 "mm_128_fusedTierB_c16p2t8.slang"
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
    uint _S8 = mfDataStrideFlag_0();

#line 260 "mm_128_fusedTierB_c16p2t8.slang"
    if(_S8 != 0U)
    {

#line 85 "twiddle.slang"
        uint _S9 = mfDataScaleFlag_0();

#line 261 "mm_128_fusedTierB_c16p2t8.slang"
        float s_0 = (as_type<float>((_S9)));
        uint _S10 = 2U * i_1;

#line 262
        return half2(half((as_type<float>((b_1[_S10]))) * s_0), half((as_type<float>((b_1[_S10 + 1U]))) * s_0));
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


#line 379
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 379
    half2 _S11 = half2(wr_0) ;

#line 379
    half2 _S12 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S12 + *xi_0 * _S11;
    *xr_0 = *xr_0 * _S11 - *xi_0 * _S12;

#line 383
    *xi_0 = ni_0;
    return;
}


#line 413
void swap2_0(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint p_1, uint q_0)
{

    half2 t_0 = (*re_1)[p_1];

#line 416
    (*re_1)[p_1] = (*re_1)[q_0];

#line 416
    (*re_1)[q_0] = t_0;
    half2 t_1 = (*im_1)[p_1];

#line 417
    (*im_1)[p_1] = (*im_1)[q_0];

#line 417
    (*im_1)[q_0] = t_1;
    return;
}


#line 451
void dft16s_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2)
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
        r4s_0(re_2, im_2, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 453
        n1_0 = n1_0 + 1U;

#line 453
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
        uint _S13 = 4U * k2_0;

#line 466
        r4s_0(re_2, im_2, _S13, _S13 + 1U, _S13 + 2U, _S13 + 3U);

#line 465
        k2_0 = k2_0 + 1U;

#line 465
    }

    swap2_0(re_2, im_2, 1U, 4U);

#line 467
    swap2_0(re_2, im_2, 2U, 8U);

#line 467
    swap2_0(re_2, im_2, 3U, 12U);
    swap2_0(re_2, im_2, 6U, 9U);

#line 468
    swap2_0(re_2, im_2, 7U, 13U);

#line 468
    swap2_0(re_2, im_2, 11U, 14U);
    return;
}


#line 61 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S14 = ((MF_COARSE_TWT));

#line 64
    return _S14;
}


#line 88
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S15 = ((MF_ACCURATE_TRIG));

#line 91
    return _S15;
}


#line 127
float2 mfTwiddle_0(float angle_0)
{

#line 93
    uint _S16 = mfAccurateTrigFlag_0();

#line 129
    if(_S16 == 0U)
    {

#line 130
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


#line 327 "mm_128_fusedTierB_c16p2t8.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S18 = max(TB_0, 1U);

#line 329
    uint j_0 = d_2 / _S18;

#line 329
    uint m_0 = d_2 % _S18;

#line 329
    uint _S19;
    if(TB_0 <= 16U)
    {

#line 330
        _S19 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 330
    }
    else
    {

#line 330
        _S19 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 330
    }

#line 330
    return _S19;
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
void exchangeS_0(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_3)
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
        half2 _S20 = half2(float2(0.0f) );

#line 494
        outr_0[z_1] = _S20;

#line 494
        outi_0[z_1] = _S20;

#line 494
        z_1 = z_1 + 1U;

#line 494
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S21 = p0_0 & lenMask_0;
    uint _S22 = (_S21 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S21 & spanMask_0);

#line 499
    uint c_2 = 0U;
    for(;;)
    {

#line 500
        if(c_2 < 1U)
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
                        uint _S23 = j_1 * 8U + kernelContext_3->_tid_0;

#line 504
                        stgPut_0(_S23, (*re_3)[c_2 * 16U + j_1], kernelContext_3);

#line 503
                        j_1 = j_1 + 1U;

#line 503
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 505
                    uint d_3 = 0U;
                    for(;;)
                    {

#line 506
                        if(d_3 < 16U)
                        {
                        }
                        else
                        {

#line 506
                            break;
                        }
                        uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S24 = pz_0 & lenMask_0;
                        uint az_0 = (_S24 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S24 & spanMask_0);

#line 510
                        half2 _S25 = stgGet_0(_S22 + az_0 - c_2 * 16U * 8U, kernelContext_3);



                        outr_0[d_3] = _S25;

#line 506
                        d_3 = d_3 + 1U;

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
                        uint _S26 = j_2 * 8U + kernelContext_3->_tid_0;

#line 504
                        stgPut_0(_S26, (*im_3)[c_2 * 16U + j_2], kernelContext_3);

#line 503
                        j_2 = j_2 + 1U;

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
                        uint pz_1 = computeWant_0(d_4, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S27 = pz_1 & lenMask_0;
                        uint az_1 = (_S27 >> lgSpan_0) * 8U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S27 & spanMask_0);

#line 510
                        half2 _S28 = stgGet_0(_S22 + az_1 - c_2 * 16U * 8U, kernelContext_3);



                        outi_0[d_4] = _S28;

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
            break;
        }

#line 500
        c_2 = c_2 + 1U;

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
        (*re_3)[j_1] = outr_0[j_1];

#line 519
        (*im_3)[j_1] = outi_0[j_1];

#line 519
        j_1 = j_1 + 1U;

#line 519
    }
    return;
}


#line 433
void dft8s_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4, uint o_0)
{
    thread array<half2, int(8)> br_1;

#line 435
    thread array<half2, int(8)> bi_1;

#line 435
    uint s_2 = 1U;
    for(;;)
    {

#line 436
        if(s_2 < 8U)
        {
        }
        else
        {

#line 436
            break;
        }

#line 436
        uint j_3 = 0U;
        for(;;)
        {

#line 437
            if(j_3 < 4U)
            {
            }
            else
            {

#line 437
                break;
            }

#line 438
            uint k_0 = j_3 & (s_2 - 1U);

#line 438
            uint base_0 = (j_3 - k_0) << 1U;
            float ang_0 = 3.14159274101257324f * float(k_0) / float(s_2);
            uint _S29 = o_0 + j_3;

#line 440
            uint _S30 = _S29 + 4U;

#line 440
            thread half2 vr_0 = (*re_4)[_S30];

#line 440
            thread half2 vi_0 = (*im_4)[_S30];
            float2 tw_0 = mfTwiddle_0(ang_0);
            cmulw_0(&vr_0, &vi_0, half(tw_0.x), half(tw_0.y));

            uint _S31 = base_0 + k_0;

#line 444
            br_1[_S31] = (*re_4)[_S29] + vr_0;

#line 444
            bi_1[_S31] = (*im_4)[_S29] + vi_0;
            uint _S32 = _S31 + s_2;

#line 445
            br_1[_S32] = (*re_4)[_S29] - vr_0;

#line 445
            bi_1[_S32] = (*im_4)[_S29] - vi_0;

#line 437
            j_3 = j_3 + 1U;

#line 437
        }

#line 437
        uint i_4 = 0U;

#line 447
        for(;;)
        {

#line 447
            if(i_4 < 8U)
            {
            }
            else
            {

#line 447
                break;
            }

#line 447
            uint _S33 = o_0 + i_4;

#line 447
            (*re_4)[_S33] = br_1[i_4];

#line 447
            (*im_4)[_S33] = bi_1[i_4];

#line 447
            i_4 = i_4 + 1U;

#line 447
        }

#line 436
        s_2 = s_2 << 1U;

#line 436
    }

#line 449
    return;
}


#line 522
void innermostS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5)
{

#line 522
    uint b_3 = 0U;


    for(;;)
    {

#line 525
        if(b_3 < 2U)
        {
        }
        else
        {

#line 525
            break;
        }

#line 525
        dft8s_0(re_5, im_5, b_3 * 8U);

#line 525
        b_3 = b_3 + 1U;

#line 525
    }


    return;
}


#line 815
uint lgOf_0(uint i_5)
{

#line 815
    uint _S34;

#line 815
    if(i_5 < 1U)
    {

#line 815
        _S34 = 4U;

#line 815
    }
    else
    {

#line 815
        if(i_5 == 1U)
        {

#line 815
            _S34 = 3U;

#line 815
        }
        else
        {

#line 815
            _S34 = 1U;

#line 815
        }

#line 815
    }

#line 815
    return _S34;
}


#line 817
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 821
    uint lg_1 = lgOf_0(0U);

#line 826
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 475
half2 mag2s_0(half2 re_6, half2 im_6)
{

#line 475
    return re_6 * re_6 + im_6 * im_6;
}


#line 1370
uint mfShflXor_0(uint v_1, uint s_3, KernelContext_0 thread* kernelContext_4)
{

#line 1370
    uint _S35 = (simd_shuffle((v_1), ushort((int((kernelContext_4->_S3) ^ s_3)))));

#line 1370
    return _S35;
}


#line 110 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S36 = ((MF_C16_RAW));

#line 113
    return _S36;
}


#line 1491 "mm_128_fusedTierB_c16p2t8.slang"
void peakTwoGate_0(uint pairA_0, uint pairB_0, uint tid_0, const array<half2, int(16)> thread* re_7, const array<half2, int(16)> thread* im_7, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, float thr_0, KernelContext_0 thread* kernelContext_5)
{


    uint _S37 = slotToIndex_0(tid_0 * 16U) - winStart_2;
    uint _S38 = winEnd_2 - winStart_2;
    half2 _S39 = half2(float2(0.0f) );
    half2 _S40 = half2(float2(0.015625f) );

#line 1498
    uint i_6 = 0U;

#line 1498
    half2 best_0 = _S39;

#line 1498
    half2 en_0 = _S39;
    for(;;)
    {

#line 1499
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1499
            break;
        }

#line 1499
        half2 _S41;

        if((_S37 + slotToIndex_0(i_6)) < _S38)
        {

#line 1501
            _S41 = mag2s_0((*re_7)[i_6], (*im_7)[i_6]);

#line 1501
        }
        else
        {

#line 1501
            _S41 = _S39;

#line 1501
        }

#line 1501
        half2 _S42 = max(best_0, _S41);
        half2 sr_0 = (*re_7)[i_6] * _S40;

#line 1502
        half2 si_0 = (*im_7)[i_6] * _S40;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1499
        i_6 = i_6 + 1U;

#line 1499
        best_0 = _S42;

#line 1499
        en_0 = en_1;

#line 1499
    }

#line 1499
    uint _S43 = mfShflXor_0((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U), 1U, kernelContext_5);

#line 1506
    half2 _S44 = max(best_0, half2(as_type<half>(ushort(_S43 & 65535U)), as_type<half>(ushort((_S43 >> 16U) & 65535U))));

#line 1506
    uint _S45 = mfShflXor_0((uint(as_type<ushort>(en_0[0U])) & 65535U) | (uint(as_type<ushort>(en_0[1U])) << 16U), 1U, kernelContext_5);
    half2 en_2 = en_0 + half2(as_type<half>(ushort(_S45 & 65535U)), as_type<half>(ushort((_S45 >> 16U) & 65535U)));

#line 1507
    uint _S46 = mfShflXor_0((uint(as_type<ushort>(_S44[0U])) & 65535U) | (uint(as_type<ushort>(_S44[1U])) << 16U), 2U, kernelContext_5);

#line 1506
    half2 _S47 = max(_S44, half2(as_type<half>(ushort(_S46 & 65535U)), as_type<half>(ushort((_S46 >> 16U) & 65535U))));

#line 1506
    uint _S48 = mfShflXor_0((uint(as_type<ushort>(en_2[0U])) & 65535U) | (uint(as_type<ushort>(en_2[1U])) << 16U), 2U, kernelContext_5);
    half2 en_3 = en_2 + half2(as_type<half>(ushort(_S48 & 65535U)), as_type<half>(ushort((_S48 >> 16U) & 65535U)));

#line 1507
    uint _S49 = mfShflXor_0((uint(as_type<ushort>(_S47[0U])) & 65535U) | (uint(as_type<ushort>(_S47[1U])) << 16U), 4U, kernelContext_5);

#line 1506
    half2 best_1 = max(_S47, half2(as_type<half>(ushort(_S49 & 65535U)), as_type<half>(ushort((_S49 >> 16U) & 65535U))));

#line 1506
    uint _S50 = mfShflXor_0((uint(as_type<ushort>(en_3[0U])) & 65535U) | (uint(as_type<ushort>(en_3[1U])) << 16U), 4U, kernelContext_5);
    half2 en_4 = en_3 + half2(as_type<half>(ushort(_S50 & 65535U)), as_type<half>(ushort((_S50 >> 16U) & 65535U)));

#line 1507
    uint _S51 = (uint(as_type<ushort>(en_4[0U])) & 65535U) | (uint(as_type<ushort>(en_4[1U])) << 16U);

#line 1507
    uint _S52 = (uint(as_type<ushort>(best_1[0U])) & 65535U) | (uint(as_type<ushort>(best_1[1U])) << 16U);

#line 1507
    bool infA_0;

#line 1515
    if((_S51 & 31744U) == 31744U)
    {

#line 1515
        infA_0 = true;

#line 1515
    }
    else
    {

#line 1515
        infA_0 = (_S52 & 31744U) == 31744U;

#line 1515
    }

#line 1515
    bool infB_0;
    if((_S51 & 2080374784U) == 2080374784U)
    {

#line 1516
        infB_0 = true;

#line 1516
    }
    else
    {

#line 1516
        infB_0 = (_S52 & 2080374784U) == 2080374784U;

#line 1516
    }

#line 115 "twiddle.slang"
    uint _S53 = mfC16RawFlag_0();

#line 115
    float _S54;

#line 1519 "mm_128_fusedTierB_c16p2t8.slang"
    if((1U - _S53) != 0U)
    {

#line 1519
        _S54 = 11.95860004425048828f;

#line 1519
    }
    else
    {

#line 1519
        _S54 = 0.0f;

#line 1519
    }

#line 1519
    float k2_1 = _S54 * 0.00048828125f * 1.00010001659393311f;
    float mA_0 = sqrt(float(best_1.x));

#line 1520
    float mB_0 = sqrt(float(best_1.y));

    float bA_0 = mA_0 * 1.00107669830322266f + k2_1 * sqrt(float(en_4.x) * 32.0f);
    float bB_0 = mB_0 * 1.00107669830322266f + k2_1 * sqrt(float(en_4.y) * 32.0f);

#line 1523
    bool hitA_0;
    if(infA_0)
    {

#line 1524
        hitA_0 = true;

#line 1524
    }
    else
    {

#line 1524
        if(mA_0 > 0.0f)
        {

#line 1524
            hitA_0 = bA_0 >= thr_0;

#line 1524
        }
        else
        {

#line 1524
            hitA_0 = false;

#line 1524
        }

#line 1524
    }

#line 1524
    bool hitB_0;
    if(infB_0)
    {

#line 1525
        hitB_0 = true;

#line 1525
    }
    else
    {

#line 1525
        if(mB_0 > 0.0f)
        {

#line 1525
            hitB_0 = bB_0 >= thr_0;

#line 1525
        }
        else
        {

#line 1525
            hitB_0 = false;

#line 1525
        }

#line 1525
    }
    bool _S55 = tid_0 == 0U;

#line 1526
    bool _S56;

#line 1526
    if(_S55)
    {

#line 1526
        _S56 = pairA_0 != 4294967295U;

#line 1526
    }
    else
    {

#line 1526
        _S56 = false;

#line 1526
    }

#line 1526
    int _S57;

#line 1526
    float2 _S58;

#line 1526
    if(_S56)
    {

#line 1527
        int device* _S59 = peakIdx_0+pairA_0;

#line 1527
        if(hitA_0)
        {

#line 1527
            _S57 = int(0);

#line 1527
        }
        else
        {

#line 1527
            _S57 = int(-1);

#line 1527
        }

#line 1527
        *_S59 = _S57;

#line 1527
        packed_float2 device* _S60 = peakVal_0+pairA_0;
        if(infA_0)
        {

#line 1528
            _S58 = float2(3.40282306073709653e+38f, 0.0f);

#line 1528
        }
        else
        {

#line 1528
            if(hitA_0)
            {

#line 1528
                _S58 = float2(bA_0, 0.0f);

#line 1528
            }
            else
            {

#line 1528
                _S58 = float2(0.0f, 0.0f);

#line 1528
            }

#line 1528
        }

#line 1528
        *_S60 = packed_float2(_S58) ;

#line 1526
    }



    if(_S55)
    {

#line 1530
        infA_0 = pairB_0 != 4294967295U;

#line 1530
    }
    else
    {

#line 1530
        infA_0 = false;

#line 1530
    }

#line 1530
    if(infA_0)
    {

#line 1531
        int device* _S61 = peakIdx_0+pairB_0;

#line 1531
        if(hitB_0)
        {

#line 1531
            _S57 = int(0);

#line 1531
        }
        else
        {

#line 1531
            _S57 = int(-1);

#line 1531
        }

#line 1531
        *_S61 = _S57;

#line 1531
        packed_float2 device* _S62 = peakVal_0+pairB_0;
        if(infB_0)
        {

#line 1532
            _S58 = float2(3.40282306073709653e+38f, 0.0f);

#line 1532
        }
        else
        {

#line 1532
            if(hitB_0)
            {

#line 1532
                _S58 = float2(bB_0, 0.0f);

#line 1532
            }
            else
            {

#line 1532
                _S58 = float2(0.0f, 0.0f);

#line 1532
            }

#line 1532
        }

#line 1532
        *_S62 = packed_float2(_S58) ;

#line 1530
    }



    return;
}


#line 356
float2 c16Bound_0(float2 v_2, float energy_0)
{

#line 115 "twiddle.slang"
    uint _S63 = mfC16RawFlag_0();

#line 358 "mm_128_fusedTierB_c16p2t8.slang"
    if((1U - _S63) == 0U)
    {

#line 358
        return v_2;
    }

#line 359
    float m_1 = length(v_2);
    float b_4 = m_1 * 1.00146484375f + 0.00583916017785668f * sqrt(energy_0);

#line 360
    float2 _S64;
    if(m_1 > 0.0f)
    {

#line 361
        _S64 = v_2 * float2((b_4 / m_1)) ;

#line 361
    }
    else
    {

#line 361
        _S64 = float2(b_4, 0.0f);

#line 361
    }

#line 361
    return _S64;
}


#line 1373
void peakTwoWave_0(uint pairA_1, uint pairB_1, uint tid_1, const array<half2, int(16)> thread* re_8, const array<half2, int(16)> thread* im_8, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_1, KernelContext_0 thread* kernelContext_6)
{
    uint m_2;

#line 1375
    bool _S65;

#line 1375
    bool _S66;

    uint _S67 = slotToIndex_0(tid_1 * 16U) - winStart_3;
    uint _S68 = winEnd_3 - winStart_3;

#line 1385
    half2 _S69 = half2(float2(0.0f) );
    half2 _S70 = half2(float2(0.015625f) );

#line 1386
    uint i_7 = 0U;

#line 1386
    half2 en_5 = _S69;

#line 1386
    uint ovAcc_0 = 0U;

#line 1386
    uint kA_0 = 0U;

#line 1386
    uint kB_0 = 0U;



    for(;;)
    {

#line 1390
        if(i_7 < 16U)
        {
        }
        else
        {

#line 1390
            break;
        }
        half2 mg_0 = mag2s_0((*re_8)[i_7], (*im_8)[i_7]);
        half2 sr_1 = (*re_8)[i_7] * _S70;

#line 1393
        half2 si_1 = (*im_8)[i_7] * _S70;
        half2 en_6 = en_5 + (sr_1 * sr_1 + si_1 * si_1);
        if((_S67 + slotToIndex_0(i_7)) < _S68)
        {

#line 1395
            m_2 = (uint(as_type<ushort>(mg_0[0U])) & 65535U) | (uint(as_type<ushort>(mg_0[1U])) << 16U);

#line 1395
        }
        else
        {

#line 1395
            m_2 = 0U;

#line 1395
        }

#line 1401
        uint ovAcc_1 = ovAcc_0 | (((((uint(as_type<ushort>((*re_8)[i_7].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[i_7].y)) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>((*im_8)[i_7].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[i_7].y)) << 16U)) & 2080406528U) + 67109888U));


        uint _S71 = 15U - i_7;

#line 1404
        uint _S72 = max(kA_0, (m_2 << 16U) | _S71);
        uint _S73 = max(kB_0, (m_2 & 4294901760U) | _S71);

#line 1390
        i_7 = i_7 + 1U;

#line 1390
        en_5 = en_6;

#line 1390
        ovAcc_0 = ovAcc_1;

#line 1390
        kA_0 = _S72;

#line 1390
        kB_0 = _S73;

#line 1390
    }

#line 1409
    if((ovAcc_0 & 32768U) != 0U)
    {

#line 1409
        kA_0 = max(kA_0, 2080374799U);

#line 1409
    }
    if((ovAcc_0 & 2147483648U) != 0U)
    {

#line 1410
        kB_0 = max(kB_0, 2080374799U);

#line 1410
    }


    uint _S74 = (4095U - tid_1) << 4U;

#line 1413
    uint kA_1 = kA_0 | _S74;
    uint kB_1 = kB_0 | _S74;

#line 1414
    uint _S75 = mfShflXor_0(kA_1, 1U, kernelContext_6);

    uint _S76 = max(kA_1, _S75);

#line 1416
    uint _S77 = mfShflXor_0(kB_1, 1U, kernelContext_6);
    uint _S78 = max(kB_1, _S77);

#line 1417
    uint _S79 = mfShflXor_0((uint(as_type<ushort>(en_5[0U])) & 65535U) | (uint(as_type<ushort>(en_5[1U])) << 16U), 1U, kernelContext_6);
    half2 en_7 = en_5 + half2(as_type<half>(ushort(_S79 & 65535U)), as_type<half>(ushort((_S79 >> 16U) & 65535U)));

#line 1418
    uint _S80 = mfShflXor_0(_S76, 2U, kernelContext_6);

#line 1416
    uint _S81 = max(_S76, _S80);

#line 1416
    uint _S82 = mfShflXor_0(_S78, 2U, kernelContext_6);
    uint _S83 = max(_S78, _S82);

#line 1417
    uint _S84 = mfShflXor_0((uint(as_type<ushort>(en_7[0U])) & 65535U) | (uint(as_type<ushort>(en_7[1U])) << 16U), 2U, kernelContext_6);
    half2 en_8 = en_7 + half2(as_type<half>(ushort(_S84 & 65535U)), as_type<half>(ushort((_S84 >> 16U) & 65535U)));

#line 1418
    uint _S85 = mfShflXor_0(_S81, 4U, kernelContext_6);

#line 1416
    uint _S86 = max(_S81, _S85);

#line 1416
    uint _S87 = mfShflXor_0(_S83, 4U, kernelContext_6);
    uint _S88 = max(_S83, _S87);

#line 1417
    uint _S89 = mfShflXor_0((uint(as_type<ushort>(en_8[0U])) & 65535U) | (uint(as_type<ushort>(en_8[1U])) << 16U), 4U, kernelContext_6);
    half2 en_9 = en_8 + half2(as_type<half>(ushort(_S89 & 65535U)), as_type<half>(ushort((_S89 >> 16U) & 65535U)));



    float enA_0 = float(en_9.x) * 32.0f;

#line 1422
    float enB_0 = float(en_9.y) * 32.0f;
    uint slotA_0 = 65535U - (_S86 & 65535U);

#line 1423
    uint slotB_0 = 65535U - (_S88 & 65535U);

#line 1429
    uint _S90 = _S86 >> 16U;

#line 1429
    bool infA_1 = _S90 >= 31744U;

#line 1429
    uint _S91 = _S88 >> 16U;

#line 1429
    bool infB_1 = _S91 >= 31744U;

#line 1429
    bool hitA_1;



    if(infA_1)
    {

#line 1433
        hitA_1 = true;

#line 1433
    }
    else
    {

#line 1433
        hitA_1 = (as_type<half>((ushort)((_S90)))) > (as_type<float>((thrBits_1)));

#line 1433
    }

#line 1433
    bool hitB_1;
    if(infB_1)
    {

#line 1434
        hitB_1 = true;

#line 1434
    }
    else
    {

#line 1434
        hitB_1 = (as_type<half>((ushort)((_S91)))) > (as_type<float>((thrBits_1)));

#line 1434
    }

#line 1442
    uint _S92 = slotA_0 >> 4U;

#line 1442
    uint _S93 = slotA_0 & 15U;

#line 1442
    uint _S94 = slotB_0 >> 4U;

#line 1442
    uint _S95 = slotB_0 & 15U;
    thread array<float, int(2)> vA_0;

#line 1443
    thread array<float, int(2)> vB_0;
    vB_0[int(1)] = 0.0f;

#line 1444
    vB_0[int(0)] = 0.0f;

#line 1444
    vA_0[int(1)] = 0.0f;

#line 1444
    vA_0[int(0)] = 0.0f;

#line 1444
    for(;;)
    {

#line 1444
        for(;;)
        {

#line 1445
            for(;;)
            {

#line 1445
                for(;;)
                {

#line 1445
                    for(;;)
                    {

#line 1446
                        for(;;)
                        {

#line 1447
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1447
                            m_2 = 0U;
                            for(;;)
                            {

#line 1448
                                if(m_2 < 16U)
                                {
                                }
                                else
                                {

#line 1448
                                    break;
                                }

#line 1449
                                (*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + m_2 * 8U + tid_1] = (uint(as_type<ushort>((*re_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[m_2].y)) << 16U);

#line 1448
                                m_2 = m_2 + 1U;

#line 1448
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            bool _S96 = tid_1 == 0U;

#line 1451
                            _S65 = _S96;

#line 1451
                            if(_S96)
                            {

#line 1452
                                if(_S93 >= 0U)
                                {

#line 1452
                                    _S66 = _S93 < 16U;

#line 1452
                                }
                                else
                                {

#line 1452
                                    _S66 = false;

#line 1452
                                }

#line 1452
                                if(_S66)
                                {

#line 1453
                                    vA_0[0U] = (as_type<half>((ushort)(((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S93 * 8U + _S92]))));

#line 1452
                                }

                                if(_S95 >= 0U)
                                {

#line 1454
                                    _S66 = _S95 < 16U;

#line 1454
                                }
                                else
                                {

#line 1454
                                    _S66 = false;

#line 1454
                                }

#line 1454
                                if(_S66)
                                {

#line 1455
                                    vB_0[0U] = (as_type<half>((ushort)((((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S95 * 8U + _S94]) >> 16U))));

#line 1454
                                }

#line 1451
                            }

#line 1446
                            break;
                        }

#line 1446
                        break;
                    }

#line 1446
                    break;
                }

#line 1445
                break;
            }

#line 1445
            break;
        }

#line 1445
        for(;;)
        {

#line 1445
            for(;;)
            {

#line 1445
                for(;;)
                {

#line 1445
                    for(;;)
                    {

#line 1446
                        for(;;)
                        {

#line 1447
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1447
                            m_2 = 0U;
                            for(;;)
                            {

#line 1448
                                if(m_2 < 16U)
                                {
                                }
                                else
                                {

#line 1448
                                    break;
                                }

#line 1449
                                (*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + m_2 * 8U + tid_1] = (uint(as_type<ushort>((*im_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[m_2].y)) << 16U);

#line 1448
                                m_2 = m_2 + 1U;

#line 1448
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            if(_S65)
                            {

#line 1452
                                if(_S93 >= 0U)
                                {

#line 1452
                                    _S66 = _S93 < 16U;

#line 1452
                                }
                                else
                                {

#line 1452
                                    _S66 = false;

#line 1452
                                }

#line 1452
                                if(_S66)
                                {

#line 1453
                                    vA_0[1U] = (as_type<half>((ushort)(((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S93 * 8U + _S92]))));

#line 1452
                                }

                                if(_S95 >= 0U)
                                {

#line 1454
                                    _S66 = _S95 < 16U;

#line 1454
                                }
                                else
                                {

#line 1454
                                    _S66 = false;

#line 1454
                                }

#line 1454
                                if(_S66)
                                {

#line 1455
                                    vB_0[1U] = (as_type<half>((ushort)((((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S95 * 8U + _S94]) >> 16U))));

#line 1454
                                }

#line 1451
                            }

#line 1446
                            break;
                        }

#line 1446
                        break;
                    }

#line 1446
                    break;
                }

#line 1445
                break;
            }

#line 1445
            break;
        }

#line 1445
        break;
    }

#line 1459
    if(_S65)
    {

#line 1459
        _S66 = pairA_1 != 4294967295U;

#line 1459
    }
    else
    {

#line 1459
        _S66 = false;

#line 1459
    }

#line 1459
    int _S97;

#line 1459
    float2 _S98;

#line 1459
    if(_S66)
    {

#line 1460
        int device* _S99 = peakIdx_1+pairA_1;

#line 1460
        if(hitA_1)
        {

#line 1460
            _S97 = int(slotToIndex_0(slotA_0));

#line 1460
        }
        else
        {

#line 1460
            _S97 = int(-1);

#line 1460
        }

#line 1460
        *_S99 = _S97;

#line 1460
        packed_float2 device* _S100 = peakVal_1+pairA_1;
        if(infA_1)
        {

#line 1461
            _S98 = float2(3.40282306073709653e+38f, 0.0f);

#line 1461
        }
        else
        {

#line 1462
            if(hitA_1)
            {

#line 1462
                float2 _S101 = c16Bound_0(float2(vA_0[int(0)], vA_0[int(1)]), enA_0);

#line 1462
                _S98 = _S101;

#line 1462
            }
            else
            {

#line 1462
                _S98 = float2(0.0f, 0.0f);

#line 1462
            }

#line 1461
        }

#line 1461
        *_S100 = packed_float2(_S98) ;

#line 1459
    }

#line 1464
    if(_S65)
    {

#line 1464
        hitA_1 = pairB_1 != 4294967295U;

#line 1464
    }
    else
    {

#line 1464
        hitA_1 = false;

#line 1464
    }

#line 1464
    if(hitA_1)
    {

#line 1465
        int device* _S102 = peakIdx_1+pairB_1;

#line 1465
        if(hitB_1)
        {

#line 1465
            _S97 = int(slotToIndex_0(slotB_0));

#line 1465
        }
        else
        {

#line 1465
            _S97 = int(-1);

#line 1465
        }

#line 1465
        *_S102 = _S97;

#line 1465
        packed_float2 device* _S103 = peakVal_1+pairB_1;
        if(infB_1)
        {

#line 1466
            _S98 = float2(3.40282306073709653e+38f, 0.0f);

#line 1466
        }
        else
        {

#line 1467
            if(hitB_1)
            {

#line 1467
                float2 _S104 = c16Bound_0(float2(vB_0[int(0)], vB_0[int(1)]), enB_0);

#line 1467
                _S98 = _S104;

#line 1467
            }
            else
            {

#line 1467
                _S98 = float2(0.0f, 0.0f);

#line 1467
            }

#line 1466
        }

#line 1466
        *_S103 = packed_float2(_S98) ;

#line 1464
    }

#line 1469
    return;
}


#line 1540
void filterTwo_0(uint pairA_2, uint pairB_2, uint tA_0, uint tB_0, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* tmpl_0, int device* peakIdx_2, packed_float2 device* peakVal_2, uint winStart_4, uint winEnd_4, uint thrBits_2, KernelContext_0 thread* kernelContext_7)
{



    thread array<half2, int(16)> re_9;

#line 1545
    thread array<half2, int(16)> im_9;

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
        uint _S105 = 8U * n2_0;

#line 1547
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 128U + tid_2 + _S105);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 128U + tid_2 + _S105);
        half _S106 = (*dreg_0)[n2_0].x;
        half _S107 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S106, _S106), half2(_S107, _S107), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_9[n2_0], &im_9[n2_0]);

#line 1546
        n2_0 = n2_0 + 1U;

#line 1546
    }

#line 1559
    uint lgTB_0 = firstbithigh_0(8U);
    uint lgLn_0 = firstbithigh_0(128U);
    uint blk_2 = tid_2 >> lgTB_0;
    uint lane_2 = tid_2 & 7U;

    dft16s_0(&re_9, &im_9);

#line 66 "twiddle.slang"
    uint _S108 = mfCoarseTwtFlag_0();

#line 66
    uint k2_2;

#line 1566 "mm_128_fusedTierB_c16p2t8.slang"
    if(_S108 != 0U)
    {

#line 1566
        k2_2 = 0U;

#line 1573
        for(;;)
        {

#line 1573
            if(k2_2 < 16U)
            {
            }
            else
            {

#line 1573
                break;
            }

#line 1574
            uint _S109 = lane_2 * 16U + k2_2;
            cmulw_0(&re_9[k2_2], &im_9[k2_2], as_type<half>(ushort((COARSE_TWT_DATA_0[_S109]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S109]) >> 16U) & 65535U)));

#line 1573
            k2_2 = k2_2 + 1U;

#line 1573
        }

#line 1566
    }
    else
    {

#line 1582
        float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 128.0f);
        float _S110 = tw_1.x;

#line 1583
        float _S111 = tw_1.y;

#line 1583
        k2_2 = 0U;

#line 1583
        float cr_0 = 1.0f;

#line 1583
        float ci_0 = 0.0f;

        for(;;)
        {

#line 1585
            if(k2_2 < 16U)
            {
            }
            else
            {

#line 1585
                break;
            }

#line 1586
            cmulw_0(&re_9[k2_2], &im_9[k2_2], half(cr_0), half(ci_0));
            float nr_0 = cr_0 * _S110 - ci_0 * _S111;
            float _S112 = cr_0 * _S111 + ci_0 * _S110;

#line 1585
            k2_2 = k2_2 + 1U;

#line 1585
            cr_0 = nr_0;

#line 1585
            ci_0 = _S112;

#line 1585
        }

#line 1566
    }

#line 1592
    uint per_2 = 16U / max(8U, 1U);
    uint _S113 = max(0U, 1U);
    uint blk2_2 = tid_2 / _S113;

#line 1594
    uint lane2_2 = tid_2 % _S113;

#line 1594
    exchangeS_0(&re_9, &im_9, lgLn_0, lgTB_0, 8U, 128U, blk_2, lane_2, per_2, _S113, 8U, blk2_2, lane2_2, kernelContext_7);


    innermostS_0(&re_9, &im_9);

#line 1616
    if(thrBits_2 != 0U)
    {

#line 1617
        float _S114 = (as_type<float>((thrBits_2)));

#line 1617
        thread array<half2, int(16)> _S115 = re_9;

#line 1617
        thread array<half2, int(16)> _S116 = im_9;

#line 1617
        peakTwoGate_0(pairA_2, pairB_2, tid_2, &_S115, &_S116, peakIdx_2, peakVal_2, winStart_4, winEnd_4, _S114, kernelContext_7);

#line 1616
    }
    else
    {

#line 1616
        thread array<half2, int(16)> _S117 = re_9;

#line 1616
        thread array<half2, int(16)> _S118 = im_9;

#line 1616
        peakTwoWave_0(pairA_2, pairB_2, tid_2, &_S117, &_S118, peakIdx_2, peakVal_2, winStart_4, winEnd_4, thrBits_2, kernelContext_7);

#line 1616
    }

#line 1654
    return;
}


void filterPair_0(uint pair_0, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_3, packed_float2 device* peakVal_3, uint ntmpl_1, uint winStart_5, uint winEnd_5, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, uint device* rowWin_1, KernelContext_0 thread* kernelContext_8)
{

#line 1658
    thread uint _S119 = winStart_5;

#line 1658
    thread uint _S120 = winEnd_5;

#line 1664
    kernelContext_8->_tid_0 = tid_3;

#line 1684
    uint tiles_0 = (ntmpl_1 + 8U - 1U) / 8U;
    uint slots_0 = binsize_1 * tiles_0;
    bool slotOk_0 = pair_0 < slots_0;

#line 1686
    uint q_1;
    if(slotOk_0)
    {

#line 1687
        q_1 = pair_0;

#line 1687
    }
    else
    {

#line 1687
        q_1 = slots_0 - 1U;

#line 1687
    }
    uint d_5 = q_1 / tiles_0;

#line 1688
    uint t0_0 = (q_1 - d_5 * tiles_0) * 8U;
    uint _S121 = d_5 * ntmpl_1 + t0_0;

#line 1689
    rowWindow_0(d_5, &_S119, &_S120, rowWin_1, kernelContext_8);

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
        uint _S122 = mfDataStrideFlag_0();

#line 179 "mm_128_fusedTierB_c16p2t8.slang"
        if(_S122 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S123 = mfDataStrideFlag_0();

#line 77
            q_1 = _S123;

#line 179 "mm_128_fusedTierB_c16p2t8.slang"
        }
        else
        {

#line 179
            q_1 = 128U;

#line 179
        }

#line 1717
        half2 _S124 = dload_0(data_0, d_5 * q_1 + tid_3 + 8U * n2_1);

#line 1717
        dreg_1[n2_1] = _S124;

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
            q_1 = _S121 + k_1;

#line 1726
        }
        else
        {

#line 1726
            q_1 = 4294967295U;

#line 1726
        }

#line 1726
        if(okB_0)
        {

#line 1726
            n2_1 = _S121 + k_1 + 1U;

#line 1726
        }
        else
        {

#line 1726
            n2_1 = 4294967295U;

#line 1726
        }
        uint _S125 = t0_0 + k_1;

#line 1727
        uint _S126 = ntmpl_1 - 1U;

#line 1727
        uint _S127 = min(_S125, _S126);

#line 1727
        uint _S128 = min(_S125 + 1U, _S126);

#line 1727
        thread array<half2, int(16)> _S129 = dreg_1;

#line 1727
        filterTwo_0(q_1, n2_1, _S127, _S128, tid_3, &_S129, tmpl_1, peakIdx_3, peakVal_3, _S119, _S120, thrBits_3, kernelContext_8);

#line 1724
        k_1 = k_1 + 2U;

#line 1724
    }

#line 1740
    return;
}


#line 1753
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], uint _builtinWaveLaneIndex_0 [[thread_index_in_simdgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1753
    thread KernelContext_0 kernelContext_9;

#line 1753
    (&kernelContext_9)->entryPointParams_0 = entryPointParams_1;

#line 1753
    (&kernelContext_9)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1753
    (&kernelContext_9)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1753
    (&kernelContext_9)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1753
    (&kernelContext_9)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1753
    (&kernelContext_9)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1753
    threadgroup array<uint, int(256)> stg_1;

#line 1753
    (&kernelContext_9)->stg_0 = &stg_1;

#line 1753
    (&kernelContext_9)->_binPhase_0 = 0U;

#line 1753
    (&kernelContext_9)->_S3 = _builtinWaveLaneIndex_0;

#line 1773
    uint _S130 = lid_0.x;

#line 1773
    uint _sub_0 = _S130 / 8U;
    uint _pr_0 = gid_0.x * 2U + _sub_0;

#line 1774
    uint _t_0 = _S130 % 8U;
    (&kernelContext_9)->_stgBase_0 = _sub_0 * 128U;

#line 1775
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, entryPointParams_rowWin_1, &kernelContext_9);

#line 1788
    return;
}
