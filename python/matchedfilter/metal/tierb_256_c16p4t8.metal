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

#line 11 "mm_256_fusedTierB_c16p4t8.slang"
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
    array<uint, int(1024)> threadgroup* stg_0;
    uint _S3;
};


#line 230 "mm_256_fusedTierB_c16p4t8.slang"
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 104 "twiddle.slang"
    uint _S4 = mfRowWindowsFlag_0();

#line 233 "mm_256_fusedTierB_c16p4t8.slang"
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


#line 172 "mm_256_fusedTierB_c16p4t8.slang"
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

#line 260 "mm_256_fusedTierB_c16p4t8.slang"
    if(_S8 != 0U)
    {

#line 85 "twiddle.slang"
        uint _S9 = mfDataScaleFlag_0();

#line 261 "mm_256_fusedTierB_c16p4t8.slang"
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


#line 451
void dft16s_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3)
{

#line 451
    uint n1_1 = 0U;

    for(;;)
    {

#line 453
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 453
            break;
        }

#line 453
        r4s_0(re_3, im_3, n1_1, n1_1 + 4U, n1_1 + 8U, n1_1 + 12U);

#line 453
        n1_1 = n1_1 + 1U;

#line 453
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

#line 464
    uint k2_1 = 0U;
    for(;;)
    {

#line 465
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 465
            break;
        }

#line 466
        uint _S14 = 4U * k2_1;

#line 466
        r4s_0(re_3, im_3, _S14, _S14 + 1U, _S14 + 2U, _S14 + 3U);

#line 465
        k2_1 = k2_1 + 1U;

#line 465
    }

    swap2_0(re_3, im_3, 1U, 4U);

#line 467
    swap2_0(re_3, im_3, 2U, 8U);

#line 467
    swap2_0(re_3, im_3, 3U, 12U);
    swap2_0(re_3, im_3, 6U, 9U);

#line 468
    swap2_0(re_3, im_3, 7U, 13U);

#line 468
    swap2_0(re_3, im_3, 11U, 14U);
    return;
}


#line 61 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S15 = ((MF_COARSE_TWT));

#line 64
    return _S15;
}


#line 88
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S16 = ((MF_ACCURATE_TRIG));

#line 91
    return _S16;
}


#line 127
float2 mfTwiddle_0(float angle_0)
{

#line 93
    uint _S17 = mfAccurateTrigFlag_0();

#line 129
    if(_S17 == 0U)
    {

#line 130
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S18 = float(quadrant_0);
    float x_0 = angle_0 - _S18 * 1.57079625129699707f - _S18 * 7.54978941586159635e-08f;
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


#line 327 "mm_256_fusedTierB_c16p4t8.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S19 = max(TB_0, 1U);

#line 329
    uint j_0 = d_2 / _S19;

#line 329
    uint m_0 = d_2 % _S19;

#line 329
    uint _S20;
    if(TB_0 <= 16U)
    {

#line 330
        _S20 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 330
    }
    else
    {

#line 330
        _S20 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 330
    }

#line 330
    return _S20;
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
void exchangeS_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_3)
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
        half2 _S21 = half2(float2(0.0f) );

#line 494
        outr_0[z_1] = _S21;

#line 494
        outi_0[z_1] = _S21;

#line 494
        z_1 = z_1 + 1U;

#line 494
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S22 = p0_0 & lenMask_0;
    uint _S23 = (_S22 >> lgSpan_0) * 16U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S22 & spanMask_0);

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
                        uint _S24 = j_1 * 16U + kernelContext_3->_tid_0;

#line 504
                        stgPut_0(_S24, (*re_4)[c_2 * 16U + j_1], kernelContext_3);

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
                        uint _S25 = pz_0 & lenMask_0;
                        uint az_0 = (_S25 >> lgSpan_0) * 16U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S25 & spanMask_0);

#line 510
                        half2 _S26 = stgGet_0(_S23 + az_0 - c_2 * 16U * 16U, kernelContext_3);



                        outr_0[d_3] = _S26;

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
                        uint _S27 = j_2 * 16U + kernelContext_3->_tid_0;

#line 504
                        stgPut_0(_S27, (*im_4)[c_2 * 16U + j_2], kernelContext_3);

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
                        uint _S28 = pz_1 & lenMask_0;
                        uint az_1 = (_S28 >> lgSpan_0) * 16U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S28 & spanMask_0);

#line 510
                        half2 _S29 = stgGet_0(_S23 + az_1 - c_2 * 16U * 16U, kernelContext_3);



                        outi_0[d_4] = _S29;

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
        (*re_4)[j_1] = outr_0[j_1];

#line 519
        (*im_4)[j_1] = outi_0[j_1];

#line 519
        j_1 = j_1 + 1U;

#line 519
    }
    return;
}


#line 522
void innermostS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5)
{
    dft16s_1(re_5, im_5);



    return;
}


#line 815
uint lgOf_0(uint i_4)
{

#line 815
    uint _S30;

#line 815
    if(i_4 < 1U)
    {

#line 815
        _S30 = 4U;

#line 815
    }
    else
    {

#line 815
        if(i_4 == 1U)
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
    }

#line 815
    return _S30;
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
uint mfShflXor_0(uint v_1, uint s_2, KernelContext_0 thread* kernelContext_4)
{

#line 1370
    uint _S31 = (simd_shuffle((v_1), ushort((int((kernelContext_4->_S3) ^ s_2)))));

#line 1370
    return _S31;
}


#line 110 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S32 = ((MF_C16_RAW));

#line 113
    return _S32;
}


#line 1491 "mm_256_fusedTierB_c16p4t8.slang"
void peakTwoGate_0(uint pairA_0, uint pairB_0, uint tid_0, const array<half2, int(16)> thread* re_7, const array<half2, int(16)> thread* im_7, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, float thr_0, KernelContext_0 thread* kernelContext_5)
{


    uint _S33 = slotToIndex_0(tid_0 * 16U) - winStart_2;
    uint _S34 = winEnd_2 - winStart_2;
    half2 _S35 = half2(float2(0.0f) );
    half2 _S36 = half2(float2(0.015625f) );

#line 1498
    uint i_5 = 0U;

#line 1498
    half2 best_0 = _S35;

#line 1498
    half2 en_0 = _S35;
    for(;;)
    {

#line 1499
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1499
            break;
        }

#line 1499
        half2 _S37;

        if((_S33 + slotToIndex_0(i_5)) < _S34)
        {

#line 1501
            _S37 = mag2s_0((*re_7)[i_5], (*im_7)[i_5]);

#line 1501
        }
        else
        {

#line 1501
            _S37 = _S35;

#line 1501
        }

#line 1501
        half2 _S38 = max(best_0, _S37);
        half2 sr_0 = (*re_7)[i_5] * _S36;

#line 1502
        half2 si_0 = (*im_7)[i_5] * _S36;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1499
        i_5 = i_5 + 1U;

#line 1499
        best_0 = _S38;

#line 1499
        en_0 = en_1;

#line 1499
    }

#line 1499
    uint _S39 = mfShflXor_0((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U), 1U, kernelContext_5);

#line 1506
    half2 _S40 = max(best_0, half2(as_type<half>(ushort(_S39 & 65535U)), as_type<half>(ushort((_S39 >> 16U) & 65535U))));

#line 1506
    uint _S41 = mfShflXor_0((uint(as_type<ushort>(en_0[0U])) & 65535U) | (uint(as_type<ushort>(en_0[1U])) << 16U), 1U, kernelContext_5);
    half2 en_2 = en_0 + half2(as_type<half>(ushort(_S41 & 65535U)), as_type<half>(ushort((_S41 >> 16U) & 65535U)));

#line 1507
    uint _S42 = mfShflXor_0((uint(as_type<ushort>(_S40[0U])) & 65535U) | (uint(as_type<ushort>(_S40[1U])) << 16U), 2U, kernelContext_5);

#line 1506
    half2 _S43 = max(_S40, half2(as_type<half>(ushort(_S42 & 65535U)), as_type<half>(ushort((_S42 >> 16U) & 65535U))));

#line 1506
    uint _S44 = mfShflXor_0((uint(as_type<ushort>(en_2[0U])) & 65535U) | (uint(as_type<ushort>(en_2[1U])) << 16U), 2U, kernelContext_5);
    half2 en_3 = en_2 + half2(as_type<half>(ushort(_S44 & 65535U)), as_type<half>(ushort((_S44 >> 16U) & 65535U)));

#line 1507
    uint _S45 = mfShflXor_0((uint(as_type<ushort>(_S43[0U])) & 65535U) | (uint(as_type<ushort>(_S43[1U])) << 16U), 4U, kernelContext_5);

#line 1506
    half2 _S46 = max(_S43, half2(as_type<half>(ushort(_S45 & 65535U)), as_type<half>(ushort((_S45 >> 16U) & 65535U))));

#line 1506
    uint _S47 = mfShflXor_0((uint(as_type<ushort>(en_3[0U])) & 65535U) | (uint(as_type<ushort>(en_3[1U])) << 16U), 4U, kernelContext_5);
    half2 en_4 = en_3 + half2(as_type<half>(ushort(_S47 & 65535U)), as_type<half>(ushort((_S47 >> 16U) & 65535U)));

#line 1507
    uint _S48 = mfShflXor_0((uint(as_type<ushort>(_S46[0U])) & 65535U) | (uint(as_type<ushort>(_S46[1U])) << 16U), 8U, kernelContext_5);

#line 1506
    half2 best_1 = max(_S46, half2(as_type<half>(ushort(_S48 & 65535U)), as_type<half>(ushort((_S48 >> 16U) & 65535U))));

#line 1506
    uint _S49 = mfShflXor_0((uint(as_type<ushort>(en_4[0U])) & 65535U) | (uint(as_type<ushort>(en_4[1U])) << 16U), 8U, kernelContext_5);
    half2 en_5 = en_4 + half2(as_type<half>(ushort(_S49 & 65535U)), as_type<half>(ushort((_S49 >> 16U) & 65535U)));

#line 1507
    uint _S50 = (uint(as_type<ushort>(en_5[0U])) & 65535U) | (uint(as_type<ushort>(en_5[1U])) << 16U);

#line 1507
    uint _S51 = (uint(as_type<ushort>(best_1[0U])) & 65535U) | (uint(as_type<ushort>(best_1[1U])) << 16U);

#line 1507
    bool infA_0;

#line 1515
    if((_S50 & 31744U) == 31744U)
    {

#line 1515
        infA_0 = true;

#line 1515
    }
    else
    {

#line 1515
        infA_0 = (_S51 & 31744U) == 31744U;

#line 1515
    }

#line 1515
    bool infB_0;
    if((_S50 & 2080374784U) == 2080374784U)
    {

#line 1516
        infB_0 = true;

#line 1516
    }
    else
    {

#line 1516
        infB_0 = (_S51 & 2080374784U) == 2080374784U;

#line 1516
    }

#line 115 "twiddle.slang"
    uint _S52 = mfC16RawFlag_0();

#line 115
    float _S53;

#line 1519 "mm_256_fusedTierB_c16p4t8.slang"
    if((1U - _S52) != 0U)
    {

#line 1519
        _S53 = 12.66209983825683594f;

#line 1519
    }
    else
    {

#line 1519
        _S53 = 0.0f;

#line 1519
    }

#line 1519
    float k2_2 = _S53 * 0.00048828125f * 1.00010001659393311f;
    float mA_0 = sqrt(float(best_1.x));

#line 1520
    float mB_0 = sqrt(float(best_1.y));

    float bA_0 = mA_0 * 1.00107669830322266f + k2_2 * sqrt(float(en_5.x) * 16.0f);
    float bB_0 = mB_0 * 1.00107669830322266f + k2_2 * sqrt(float(en_5.y) * 16.0f);

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
    bool _S54 = tid_0 == 0U;

#line 1526
    bool _S55;

#line 1526
    if(_S54)
    {

#line 1526
        _S55 = pairA_0 != 4294967295U;

#line 1526
    }
    else
    {

#line 1526
        _S55 = false;

#line 1526
    }

#line 1526
    int _S56;

#line 1526
    float2 _S57;

#line 1526
    if(_S55)
    {

#line 1527
        int device* _S58 = peakIdx_0+pairA_0;

#line 1527
        if(hitA_0)
        {

#line 1527
            _S56 = int(0);

#line 1527
        }
        else
        {

#line 1527
            _S56 = int(-1);

#line 1527
        }

#line 1527
        *_S58 = _S56;

#line 1527
        packed_float2 device* _S59 = peakVal_0+pairA_0;
        if(infA_0)
        {

#line 1528
            _S57 = float2(3.40282306073709653e+38f, 0.0f);

#line 1528
        }
        else
        {

#line 1528
            if(hitA_0)
            {

#line 1528
                _S57 = float2(bA_0, 0.0f);

#line 1528
            }
            else
            {

#line 1528
                _S57 = float2(0.0f, 0.0f);

#line 1528
            }

#line 1528
        }

#line 1528
        *_S59 = packed_float2(_S57) ;

#line 1526
    }



    if(_S54)
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
        int device* _S60 = peakIdx_0+pairB_0;

#line 1531
        if(hitB_0)
        {

#line 1531
            _S56 = int(0);

#line 1531
        }
        else
        {

#line 1531
            _S56 = int(-1);

#line 1531
        }

#line 1531
        *_S60 = _S56;

#line 1531
        packed_float2 device* _S61 = peakVal_0+pairB_0;
        if(infB_0)
        {

#line 1532
            _S57 = float2(3.40282306073709653e+38f, 0.0f);

#line 1532
        }
        else
        {

#line 1532
            if(hitB_0)
            {

#line 1532
                _S57 = float2(bB_0, 0.0f);

#line 1532
            }
            else
            {

#line 1532
                _S57 = float2(0.0f, 0.0f);

#line 1532
            }

#line 1532
        }

#line 1532
        *_S61 = packed_float2(_S57) ;

#line 1530
    }



    return;
}


#line 356
float2 c16Bound_0(float2 v_2, float energy_0)
{

#line 115 "twiddle.slang"
    uint _S62 = mfC16RawFlag_0();

#line 358 "mm_256_fusedTierB_c16p4t8.slang"
    if((1U - _S62) == 0U)
    {

#line 358
        return v_2;
    }

#line 359
    float m_1 = length(v_2);
    float b_3 = m_1 * 1.00146484375f + 0.00618266593664885f * sqrt(energy_0);

#line 360
    float2 _S63;
    if(m_1 > 0.0f)
    {

#line 361
        _S63 = v_2 * float2((b_3 / m_1)) ;

#line 361
    }
    else
    {

#line 361
        _S63 = float2(b_3, 0.0f);

#line 361
    }

#line 361
    return _S63;
}


#line 1373
void peakTwoWave_0(uint pairA_1, uint pairB_1, uint tid_1, const array<half2, int(16)> thread* re_8, const array<half2, int(16)> thread* im_8, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_1, KernelContext_0 thread* kernelContext_6)
{
    uint m_2;

#line 1375
    bool _S64;

#line 1375
    bool _S65;

    uint _S66 = slotToIndex_0(tid_1 * 16U) - winStart_3;
    uint _S67 = winEnd_3 - winStart_3;

#line 1385
    half2 _S68 = half2(float2(0.0f) );
    half2 _S69 = half2(float2(0.015625f) );

#line 1386
    uint i_6 = 0U;

#line 1386
    half2 en_6 = _S68;

#line 1386
    uint ovAcc_0 = 0U;

#line 1386
    uint kA_0 = 0U;

#line 1386
    uint kB_0 = 0U;



    for(;;)
    {

#line 1390
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1390
            break;
        }
        half2 mg_0 = mag2s_0((*re_8)[i_6], (*im_8)[i_6]);
        half2 sr_1 = (*re_8)[i_6] * _S69;

#line 1393
        half2 si_1 = (*im_8)[i_6] * _S69;
        half2 en_7 = en_6 + (sr_1 * sr_1 + si_1 * si_1);
        if((_S66 + slotToIndex_0(i_6)) < _S67)
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
        uint ovAcc_1 = ovAcc_0 | (((((uint(as_type<ushort>((*re_8)[i_6].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[i_6].y)) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>((*im_8)[i_6].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[i_6].y)) << 16U)) & 2080406528U) + 67109888U));


        uint _S70 = 15U - i_6;

#line 1404
        uint _S71 = max(kA_0, (m_2 << 16U) | _S70);
        uint _S72 = max(kB_0, (m_2 & 4294901760U) | _S70);

#line 1390
        i_6 = i_6 + 1U;

#line 1390
        en_6 = en_7;

#line 1390
        ovAcc_0 = ovAcc_1;

#line 1390
        kA_0 = _S71;

#line 1390
        kB_0 = _S72;

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


    uint _S73 = (4095U - tid_1) << 4U;

#line 1413
    uint kA_1 = kA_0 | _S73;
    uint kB_1 = kB_0 | _S73;

#line 1414
    uint _S74 = mfShflXor_0(kA_1, 1U, kernelContext_6);

    uint _S75 = max(kA_1, _S74);

#line 1416
    uint _S76 = mfShflXor_0(kB_1, 1U, kernelContext_6);
    uint _S77 = max(kB_1, _S76);

#line 1417
    uint _S78 = mfShflXor_0((uint(as_type<ushort>(en_6[0U])) & 65535U) | (uint(as_type<ushort>(en_6[1U])) << 16U), 1U, kernelContext_6);
    half2 en_8 = en_6 + half2(as_type<half>(ushort(_S78 & 65535U)), as_type<half>(ushort((_S78 >> 16U) & 65535U)));

#line 1418
    uint _S79 = mfShflXor_0(_S75, 2U, kernelContext_6);

#line 1416
    uint _S80 = max(_S75, _S79);

#line 1416
    uint _S81 = mfShflXor_0(_S77, 2U, kernelContext_6);
    uint _S82 = max(_S77, _S81);

#line 1417
    uint _S83 = mfShflXor_0((uint(as_type<ushort>(en_8[0U])) & 65535U) | (uint(as_type<ushort>(en_8[1U])) << 16U), 2U, kernelContext_6);
    half2 en_9 = en_8 + half2(as_type<half>(ushort(_S83 & 65535U)), as_type<half>(ushort((_S83 >> 16U) & 65535U)));

#line 1418
    uint _S84 = mfShflXor_0(_S80, 4U, kernelContext_6);

#line 1416
    uint _S85 = max(_S80, _S84);

#line 1416
    uint _S86 = mfShflXor_0(_S82, 4U, kernelContext_6);
    uint _S87 = max(_S82, _S86);

#line 1417
    uint _S88 = mfShflXor_0((uint(as_type<ushort>(en_9[0U])) & 65535U) | (uint(as_type<ushort>(en_9[1U])) << 16U), 4U, kernelContext_6);
    half2 en_10 = en_9 + half2(as_type<half>(ushort(_S88 & 65535U)), as_type<half>(ushort((_S88 >> 16U) & 65535U)));

#line 1418
    uint _S89 = mfShflXor_0(_S85, 8U, kernelContext_6);

#line 1416
    uint _S90 = max(_S85, _S89);

#line 1416
    uint _S91 = mfShflXor_0(_S87, 8U, kernelContext_6);
    uint _S92 = max(_S87, _S91);

#line 1417
    uint _S93 = mfShflXor_0((uint(as_type<ushort>(en_10[0U])) & 65535U) | (uint(as_type<ushort>(en_10[1U])) << 16U), 8U, kernelContext_6);
    half2 en_11 = en_10 + half2(as_type<half>(ushort(_S93 & 65535U)), as_type<half>(ushort((_S93 >> 16U) & 65535U)));



    float enA_0 = float(en_11.x) * 16.0f;

#line 1422
    float enB_0 = float(en_11.y) * 16.0f;
    uint slotA_0 = 65535U - (_S90 & 65535U);

#line 1423
    uint slotB_0 = 65535U - (_S92 & 65535U);

#line 1429
    uint _S94 = _S90 >> 16U;

#line 1429
    bool infA_1 = _S94 >= 31744U;

#line 1429
    uint _S95 = _S92 >> 16U;

#line 1429
    bool infB_1 = _S95 >= 31744U;

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
        hitA_1 = (as_type<half>((ushort)((_S94)))) > (as_type<float>((thrBits_1)));

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
        hitB_1 = (as_type<half>((ushort)((_S95)))) > (as_type<float>((thrBits_1)));

#line 1434
    }

#line 1442
    uint _S96 = slotA_0 >> 4U;

#line 1442
    uint _S97 = slotA_0 & 15U;

#line 1442
    uint _S98 = slotB_0 >> 4U;

#line 1442
    uint _S99 = slotB_0 & 15U;
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
                                (*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + m_2 * 16U + tid_1] = (uint(as_type<ushort>((*re_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[m_2].y)) << 16U);

#line 1448
                                m_2 = m_2 + 1U;

#line 1448
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            bool _S100 = tid_1 == 0U;

#line 1451
                            _S64 = _S100;

#line 1451
                            if(_S100)
                            {

#line 1452
                                if(_S97 >= 0U)
                                {

#line 1452
                                    _S65 = _S97 < 16U;

#line 1452
                                }
                                else
                                {

#line 1452
                                    _S65 = false;

#line 1452
                                }

#line 1452
                                if(_S65)
                                {

#line 1453
                                    vA_0[0U] = (as_type<half>((ushort)(((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S97 * 16U + _S96]))));

#line 1452
                                }

                                if(_S99 >= 0U)
                                {

#line 1454
                                    _S65 = _S99 < 16U;

#line 1454
                                }
                                else
                                {

#line 1454
                                    _S65 = false;

#line 1454
                                }

#line 1454
                                if(_S65)
                                {

#line 1455
                                    vB_0[0U] = (as_type<half>((ushort)((((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S99 * 16U + _S98]) >> 16U))));

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
                                (*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + m_2 * 16U + tid_1] = (uint(as_type<ushort>((*im_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[m_2].y)) << 16U);

#line 1448
                                m_2 = m_2 + 1U;

#line 1448
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            if(_S64)
                            {

#line 1452
                                if(_S97 >= 0U)
                                {

#line 1452
                                    _S65 = _S97 < 16U;

#line 1452
                                }
                                else
                                {

#line 1452
                                    _S65 = false;

#line 1452
                                }

#line 1452
                                if(_S65)
                                {

#line 1453
                                    vA_0[1U] = (as_type<half>((ushort)(((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S97 * 16U + _S96]))));

#line 1452
                                }

                                if(_S99 >= 0U)
                                {

#line 1454
                                    _S65 = _S99 < 16U;

#line 1454
                                }
                                else
                                {

#line 1454
                                    _S65 = false;

#line 1454
                                }

#line 1454
                                if(_S65)
                                {

#line 1455
                                    vB_0[1U] = (as_type<half>((ushort)((((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S99 * 16U + _S98]) >> 16U))));

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
    if(_S64)
    {

#line 1459
        _S65 = pairA_1 != 4294967295U;

#line 1459
    }
    else
    {

#line 1459
        _S65 = false;

#line 1459
    }

#line 1459
    int _S101;

#line 1459
    float2 _S102;

#line 1459
    if(_S65)
    {

#line 1460
        int device* _S103 = peakIdx_1+pairA_1;

#line 1460
        if(hitA_1)
        {

#line 1460
            _S101 = int(slotToIndex_0(slotA_0));

#line 1460
        }
        else
        {

#line 1460
            _S101 = int(-1);

#line 1460
        }

#line 1460
        *_S103 = _S101;

#line 1460
        packed_float2 device* _S104 = peakVal_1+pairA_1;
        if(infA_1)
        {

#line 1461
            _S102 = float2(3.40282306073709653e+38f, 0.0f);

#line 1461
        }
        else
        {

#line 1462
            if(hitA_1)
            {

#line 1462
                float2 _S105 = c16Bound_0(float2(vA_0[int(0)], vA_0[int(1)]), enA_0);

#line 1462
                _S102 = _S105;

#line 1462
            }
            else
            {

#line 1462
                _S102 = float2(0.0f, 0.0f);

#line 1462
            }

#line 1461
        }

#line 1461
        *_S104 = packed_float2(_S102) ;

#line 1459
    }

#line 1464
    if(_S64)
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
        int device* _S106 = peakIdx_1+pairB_1;

#line 1465
        if(hitB_1)
        {

#line 1465
            _S101 = int(slotToIndex_0(slotB_0));

#line 1465
        }
        else
        {

#line 1465
            _S101 = int(-1);

#line 1465
        }

#line 1465
        *_S106 = _S101;

#line 1465
        packed_float2 device* _S107 = peakVal_1+pairB_1;
        if(infB_1)
        {

#line 1466
            _S102 = float2(3.40282306073709653e+38f, 0.0f);

#line 1466
        }
        else
        {

#line 1467
            if(hitB_1)
            {

#line 1467
                float2 _S108 = c16Bound_0(float2(vB_0[int(0)], vB_0[int(1)]), enB_0);

#line 1467
                _S102 = _S108;

#line 1467
            }
            else
            {

#line 1467
                _S102 = float2(0.0f, 0.0f);

#line 1467
            }

#line 1466
        }

#line 1466
        *_S107 = packed_float2(_S102) ;

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
        uint _S109 = 16U * n2_0;

#line 1547
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 256U + tid_2 + _S109);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 256U + tid_2 + _S109);
        half _S110 = (*dreg_0)[n2_0].x;
        half _S111 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S110, _S110), half2(_S111, _S111), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_9[n2_0], &im_9[n2_0]);

#line 1546
        n2_0 = n2_0 + 1U;

#line 1546
    }

#line 1559
    uint lgTB_0 = firstbithigh_0(16U);
    uint lgLn_0 = firstbithigh_0(256U);
    uint blk_2 = tid_2 >> lgTB_0;
    uint lane_2 = tid_2 & 15U;

    dft16s_0(&re_9, &im_9);

#line 66 "twiddle.slang"
    uint _S112 = mfCoarseTwtFlag_0();

#line 66
    uint k2_3;

#line 1566 "mm_256_fusedTierB_c16p4t8.slang"
    if(_S112 != 0U)
    {

#line 1566
        k2_3 = 0U;

#line 1573
        for(;;)
        {

#line 1573
            if(k2_3 < 16U)
            {
            }
            else
            {

#line 1573
                break;
            }

#line 1574
            uint _S113 = lane_2 * 16U + k2_3;
            cmulw_0(&re_9[k2_3], &im_9[k2_3], as_type<half>(ushort((COARSE_TWT_DATA_0[_S113]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S113]) >> 16U) & 65535U)));

#line 1573
            k2_3 = k2_3 + 1U;

#line 1573
        }

#line 1566
    }
    else
    {

#line 1582
        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 256.0f);
        float _S114 = tw_0.x;

#line 1583
        float _S115 = tw_0.y;

#line 1583
        k2_3 = 0U;

#line 1583
        float cr_0 = 1.0f;

#line 1583
        float ci_0 = 0.0f;

        for(;;)
        {

#line 1585
            if(k2_3 < 16U)
            {
            }
            else
            {

#line 1585
                break;
            }

#line 1586
            cmulw_0(&re_9[k2_3], &im_9[k2_3], half(cr_0), half(ci_0));
            float nr_0 = cr_0 * _S114 - ci_0 * _S115;
            float _S116 = cr_0 * _S115 + ci_0 * _S114;

#line 1585
            k2_3 = k2_3 + 1U;

#line 1585
            cr_0 = nr_0;

#line 1585
            ci_0 = _S116;

#line 1585
        }

#line 1566
    }

#line 1592
    uint per_2 = 16U / max(16U, 1U);
    uint _S117 = max(1U, 1U);
    uint blk2_2 = tid_2 / _S117;

#line 1594
    uint lane2_2 = tid_2 % _S117;

#line 1594
    exchangeS_0(&re_9, &im_9, lgLn_0, lgTB_0, 16U, 256U, blk_2, lane_2, per_2, _S117, 16U, blk2_2, lane2_2, kernelContext_7);


    innermostS_0(&re_9, &im_9);

#line 1616
    if(thrBits_2 != 0U)
    {

#line 1617
        float _S118 = (as_type<float>((thrBits_2)));

#line 1617
        thread array<half2, int(16)> _S119 = re_9;

#line 1617
        thread array<half2, int(16)> _S120 = im_9;

#line 1617
        peakTwoGate_0(pairA_2, pairB_2, tid_2, &_S119, &_S120, peakIdx_2, peakVal_2, winStart_4, winEnd_4, _S118, kernelContext_7);

#line 1616
    }
    else
    {

#line 1616
        thread array<half2, int(16)> _S121 = re_9;

#line 1616
        thread array<half2, int(16)> _S122 = im_9;

#line 1616
        peakTwoWave_0(pairA_2, pairB_2, tid_2, &_S121, &_S122, peakIdx_2, peakVal_2, winStart_4, winEnd_4, thrBits_2, kernelContext_7);

#line 1616
    }

#line 1654
    return;
}


void filterPair_0(uint pair_0, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_3, packed_float2 device* peakVal_3, uint ntmpl_1, uint winStart_5, uint winEnd_5, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, uint device* rowWin_1, KernelContext_0 thread* kernelContext_8)
{

#line 1658
    thread uint _S123 = winStart_5;

#line 1658
    thread uint _S124 = winEnd_5;

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
    uint _S125 = d_5 * ntmpl_1 + t0_0;

#line 1689
    rowWindow_0(d_5, &_S123, &_S124, rowWin_1, kernelContext_8);

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
        uint _S126 = mfDataStrideFlag_0();

#line 179 "mm_256_fusedTierB_c16p4t8.slang"
        if(_S126 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S127 = mfDataStrideFlag_0();

#line 77
            q_1 = _S127;

#line 179 "mm_256_fusedTierB_c16p4t8.slang"
        }
        else
        {

#line 179
            q_1 = 256U;

#line 179
        }

#line 1717
        half2 _S128 = dload_0(data_0, d_5 * q_1 + tid_3 + 16U * n2_1);

#line 1717
        dreg_1[n2_1] = _S128;

#line 1716
        n2_1 = n2_1 + 1U;

#line 1716
    }

#line 1716
    uint k_0 = 0U;

#line 1724
    for(;;)
    {

#line 1724
        if(k_0 < 8U)
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
            okA_0 = (t0_0 + k_0) < ntmpl_1;

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
            okB_0 = (t0_0 + k_0 + 1U) < ntmpl_1;

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
            q_1 = _S125 + k_0;

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
            n2_1 = _S125 + k_0 + 1U;

#line 1726
        }
        else
        {

#line 1726
            n2_1 = 4294967295U;

#line 1726
        }
        uint _S129 = t0_0 + k_0;

#line 1727
        uint _S130 = ntmpl_1 - 1U;

#line 1727
        uint _S131 = min(_S129, _S130);

#line 1727
        uint _S132 = min(_S129 + 1U, _S130);

#line 1727
        thread array<half2, int(16)> _S133 = dreg_1;

#line 1727
        filterTwo_0(q_1, n2_1, _S131, _S132, tid_3, &_S133, tmpl_1, peakIdx_3, peakVal_3, _S123, _S124, thrBits_3, kernelContext_8);

#line 1724
        k_0 = k_0 + 2U;

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
    threadgroup array<uint, int(1024)> stg_1;

#line 1753
    (&kernelContext_9)->stg_0 = &stg_1;

#line 1753
    (&kernelContext_9)->_binPhase_0 = 0U;

#line 1753
    (&kernelContext_9)->_S3 = _builtinWaveLaneIndex_0;

#line 1773
    uint _S134 = lid_0.x;

#line 1773
    uint _sub_0 = _S134 / 16U;
    uint _pr_0 = gid_0.x * 4U + _sub_0;

#line 1774
    uint _t_0 = _S134 % 16U;
    (&kernelContext_9)->_stgBase_0 = _sub_0 * 256U;

#line 1775
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, entryPointParams_rowWin_1, &kernelContext_9);

#line 1788
    return;
}
