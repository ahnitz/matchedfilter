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

#line 10 "mm_256_fusedTierB_c16t2.slang"
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


#line 229 "mm_256_fusedTierB_c16t2.slang"
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 90 "twiddle.slang"
    uint _S4 = mfRowWindowsFlag_0();

#line 232 "mm_256_fusedTierB_c16t2.slang"
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


#line 171 "mm_256_fusedTierB_c16t2.slang"
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

#line 259 "mm_256_fusedTierB_c16t2.slang"
    if(_S8 != 0U)
    {

#line 71 "twiddle.slang"
        uint _S9 = mfDataScaleFlag_0();

#line 260 "mm_256_fusedTierB_c16t2.slang"
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
void swap2_0(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint p_1, uint q_0)
{

    half2 t_0 = (*re_1)[p_1];

#line 386
    (*re_1)[p_1] = (*re_1)[q_0];

#line 386
    (*re_1)[q_0] = t_0;
    half2 t_1 = (*im_1)[p_1];

#line 387
    (*im_1)[p_1] = (*im_1)[q_0];

#line 387
    (*im_1)[q_0] = t_1;
    return;
}


#line 421
void dft16s_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2)
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
        r4s_0(re_2, im_2, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 423
        n1_0 = n1_0 + 1U;

#line 423
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
        r4s_0(re_2, im_2, _S13, _S13 + 1U, _S13 + 2U, _S13 + 3U);

#line 435
        k2_0 = k2_0 + 1U;

#line 435
    }

    swap2_0(re_2, im_2, 1U, 4U);

#line 437
    swap2_0(re_2, im_2, 2U, 8U);

#line 437
    swap2_0(re_2, im_2, 3U, 12U);
    swap2_0(re_2, im_2, 6U, 9U);

#line 438
    swap2_0(re_2, im_2, 7U, 13U);

#line 438
    swap2_0(re_2, im_2, 11U, 14U);
    return;
}


#line 421
void dft16s_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3)
{

#line 421
    uint n1_1 = 0U;

    for(;;)
    {

#line 423
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 423
            break;
        }

#line 423
        r4s_0(re_3, im_3, n1_1, n1_1 + 4U, n1_1 + 8U, n1_1 + 12U);

#line 423
        n1_1 = n1_1 + 1U;

#line 423
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

#line 434
    uint k2_1 = 0U;
    for(;;)
    {

#line 435
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 435
            break;
        }

#line 436
        uint _S14 = 4U * k2_1;

#line 436
        r4s_0(re_3, im_3, _S14, _S14 + 1U, _S14 + 2U, _S14 + 3U);

#line 435
        k2_1 = k2_1 + 1U;

#line 435
    }

    swap2_0(re_3, im_3, 1U, 4U);

#line 437
    swap2_0(re_3, im_3, 2U, 8U);

#line 437
    swap2_0(re_3, im_3, 3U, 12U);
    swap2_0(re_3, im_3, 6U, 9U);

#line 438
    swap2_0(re_3, im_3, 7U, 13U);

#line 438
    swap2_0(re_3, im_3, 11U, 14U);
    return;
}


#line 47 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S15 = ((MF_COARSE_TWT));

#line 50
    return _S15;
}


#line 74
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S16 = ((MF_ACCURATE_TRIG));

#line 77
    return _S16;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S17 = mfAccurateTrigFlag_0();

#line 103
    if(_S17 == 0U)
    {

#line 104
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


#line 326 "mm_256_fusedTierB_c16t2.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S19 = max(TB_0, 1U);

#line 328
    uint j_0 = d_2 / _S19;

#line 328
    uint m_0 = d_2 % _S19;

#line 328
    uint _S20;
    if(TB_0 <= 16U)
    {

#line 329
        _S20 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 329
    }
    else
    {

#line 329
        _S20 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 329
    }

#line 329
    return _S20;
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
void exchangeS_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_3)
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
        half2 _S21 = half2(float2(0.0f) );

#line 464
        outr_0[z_1] = _S21;

#line 464
        outi_0[z_1] = _S21;

#line 464
        z_1 = z_1 + 1U;

#line 464
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S22 = p0_0 & lenMask_0;
    uint _S23 = (_S22 >> lgSpan_0) * 16U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S22 & spanMask_0);

#line 469
    uint c_2 = 0U;
    for(;;)
    {

#line 470
        if(c_2 < 1U)
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
                        uint _S24 = j_1 * 16U + kernelContext_3->_tid_0;

#line 474
                        stgPut_0(_S24, (*re_4)[c_2 * 16U + j_1], kernelContext_3);

#line 473
                        j_1 = j_1 + 1U;

#line 473
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 475
                    uint d_3 = 0U;
                    for(;;)
                    {

#line 476
                        if(d_3 < 16U)
                        {
                        }
                        else
                        {

#line 476
                            break;
                        }
                        uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S25 = pz_0 & lenMask_0;
                        uint az_0 = (_S25 >> lgSpan_0) * 16U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S25 & spanMask_0);

#line 480
                        half2 _S26 = stgGet_0(_S23 + az_0 - c_2 * 16U * 16U, kernelContext_3);



                        outr_0[d_3] = _S26;

#line 476
                        d_3 = d_3 + 1U;

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
                        uint _S27 = j_2 * 16U + kernelContext_3->_tid_0;

#line 474
                        stgPut_0(_S27, (*im_4)[c_2 * 16U + j_2], kernelContext_3);

#line 473
                        j_2 = j_2 + 1U;

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
                        uint pz_1 = computeWant_0(d_4, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S28 = pz_1 & lenMask_0;
                        uint az_1 = (_S28 >> lgSpan_0) * 16U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S28 & spanMask_0);

#line 480
                        half2 _S29 = stgGet_0(_S23 + az_1 - c_2 * 16U * 16U, kernelContext_3);



                        outi_0[d_4] = _S29;

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
            break;
        }

#line 470
        c_2 = c_2 + 1U;

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
        (*re_4)[j_1] = outr_0[j_1];

#line 489
        (*im_4)[j_1] = outi_0[j_1];

#line 489
        j_1 = j_1 + 1U;

#line 489
    }
    return;
}


#line 492
void innermostS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5)
{
    dft16s_1(re_5, im_5);



    return;
}


#line 785
uint lgOf_0(uint i_4)
{

#line 785
    uint _S30;

#line 785
    if(i_4 < 1U)
    {

#line 785
        _S30 = 4U;

#line 785
    }
    else
    {

#line 785
        if(i_4 == 1U)
        {

#line 785
            _S30 = 4U;

#line 785
        }
        else
        {

#line 785
            _S30 = 1U;

#line 785
        }

#line 785
    }

#line 785
    return _S30;
}


#line 787
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 791
    uint lg_1 = lgOf_0(0U);

#line 796
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 445
half2 mag2s_0(half2 re_6, half2 im_6)
{

#line 445
    return re_6 * re_6 + im_6 * im_6;
}


#line 1326
uint mfShflXor_0(uint v_1, uint s_2, KernelContext_0 thread* kernelContext_4)
{

#line 1326
    uint _S31 = (simd_shuffle((v_1), ushort((int((kernelContext_4->_S3) ^ s_2)))));

#line 1326
    return _S31;
}


#line 1428
void peakTwoGate_0(uint pairA_0, uint pairB_0, uint tid_0, const array<half2, int(16)> thread* re_7, const array<half2, int(16)> thread* im_7, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, float thr_0, KernelContext_0 thread* kernelContext_5)
{


    uint _S32 = slotToIndex_0(tid_0 * 16U) - winStart_2;
    uint _S33 = winEnd_2 - winStart_2;
    half2 _S34 = half2(float2(0.0f) );
    half2 _S35 = half2(float2(0.015625f) );

#line 1435
    uint i_5 = 0U;

#line 1435
    half2 best_0 = _S34;

#line 1435
    half2 en_0 = _S34;
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
        half2 _S36;

        if((_S32 + slotToIndex_0(i_5)) < _S33)
        {

#line 1438
            _S36 = mag2s_0((*re_7)[i_5], (*im_7)[i_5]);

#line 1438
        }
        else
        {

#line 1438
            _S36 = _S34;

#line 1438
        }

#line 1438
        half2 _S37 = max(best_0, _S36);
        half2 sr_0 = (*re_7)[i_5] * _S35;

#line 1439
        half2 si_0 = (*im_7)[i_5] * _S35;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1436
        i_5 = i_5 + 1U;

#line 1436
        best_0 = _S37;

#line 1436
        en_0 = en_1;

#line 1436
    }

#line 1436
    uint _S38 = mfShflXor_0((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U), 1U, kernelContext_5);

#line 1443
    half2 _S39 = max(best_0, half2(as_type<half>(ushort(_S38 & 65535U)), as_type<half>(ushort((_S38 >> 16U) & 65535U))));

#line 1443
    uint _S40 = mfShflXor_0((uint(as_type<ushort>(en_0[0U])) & 65535U) | (uint(as_type<ushort>(en_0[1U])) << 16U), 1U, kernelContext_5);
    half2 en_2 = en_0 + half2(as_type<half>(ushort(_S40 & 65535U)), as_type<half>(ushort((_S40 >> 16U) & 65535U)));

#line 1444
    uint _S41 = mfShflXor_0((uint(as_type<ushort>(_S39[0U])) & 65535U) | (uint(as_type<ushort>(_S39[1U])) << 16U), 2U, kernelContext_5);

#line 1443
    half2 _S42 = max(_S39, half2(as_type<half>(ushort(_S41 & 65535U)), as_type<half>(ushort((_S41 >> 16U) & 65535U))));

#line 1443
    uint _S43 = mfShflXor_0((uint(as_type<ushort>(en_2[0U])) & 65535U) | (uint(as_type<ushort>(en_2[1U])) << 16U), 2U, kernelContext_5);
    half2 en_3 = en_2 + half2(as_type<half>(ushort(_S43 & 65535U)), as_type<half>(ushort((_S43 >> 16U) & 65535U)));

#line 1444
    uint _S44 = mfShflXor_0((uint(as_type<ushort>(_S42[0U])) & 65535U) | (uint(as_type<ushort>(_S42[1U])) << 16U), 4U, kernelContext_5);

#line 1443
    half2 _S45 = max(_S42, half2(as_type<half>(ushort(_S44 & 65535U)), as_type<half>(ushort((_S44 >> 16U) & 65535U))));

#line 1443
    uint _S46 = mfShflXor_0((uint(as_type<ushort>(en_3[0U])) & 65535U) | (uint(as_type<ushort>(en_3[1U])) << 16U), 4U, kernelContext_5);
    half2 en_4 = en_3 + half2(as_type<half>(ushort(_S46 & 65535U)), as_type<half>(ushort((_S46 >> 16U) & 65535U)));

#line 1444
    uint _S47 = mfShflXor_0((uint(as_type<ushort>(_S45[0U])) & 65535U) | (uint(as_type<ushort>(_S45[1U])) << 16U), 8U, kernelContext_5);

#line 1443
    half2 best_1 = max(_S45, half2(as_type<half>(ushort(_S47 & 65535U)), as_type<half>(ushort((_S47 >> 16U) & 65535U))));

#line 1443
    uint _S48 = mfShflXor_0((uint(as_type<ushort>(en_4[0U])) & 65535U) | (uint(as_type<ushort>(en_4[1U])) << 16U), 8U, kernelContext_5);
    half2 en_5 = en_4 + half2(as_type<half>(ushort(_S48 & 65535U)), as_type<half>(ushort((_S48 >> 16U) & 65535U)));

#line 1444
    uint _S49 = (uint(as_type<ushort>(en_5[0U])) & 65535U) | (uint(as_type<ushort>(en_5[1U])) << 16U);

#line 1444
    uint _S50 = (uint(as_type<ushort>(best_1[0U])) & 65535U) | (uint(as_type<ushort>(best_1[1U])) << 16U);

#line 1444
    bool infA_0;

#line 1452
    if((_S49 & 31744U) == 31744U)
    {

#line 1452
        infA_0 = true;

#line 1452
    }
    else
    {

#line 1452
        infA_0 = (_S50 & 31744U) == 31744U;

#line 1452
    }

#line 1452
    bool infB_0;
    if((_S49 & 2080374784U) == 2080374784U)
    {

#line 1453
        infB_0 = true;

#line 1453
    }
    else
    {

#line 1453
        infB_0 = (_S50 & 2080374784U) == 2080374784U;

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
    bool _S51 = tid_0 == 0U;

#line 1457
    bool _S52;

#line 1457
    if(_S51)
    {

#line 1457
        _S52 = pairA_0 != 4294967295U;

#line 1457
    }
    else
    {

#line 1457
        _S52 = false;

#line 1457
    }

#line 1457
    int _S53;

#line 1457
    float2 _S54;

#line 1457
    if(_S52)
    {

#line 1458
        int device* _S55 = peakIdx_0+pairA_0;

#line 1458
        if(hitA_0)
        {

#line 1458
            _S53 = int(0);

#line 1458
        }
        else
        {

#line 1458
            _S53 = int(-1);

#line 1458
        }

#line 1458
        *_S55 = _S53;

#line 1458
        packed_float2 device* _S56 = peakVal_0+pairA_0;
        if(infA_0)
        {

#line 1459
            _S54 = float2(3.40282306073709653e+38f, 0.0f);

#line 1459
        }
        else
        {

#line 1459
            if(hitA_0)
            {

#line 1459
                _S54 = float2(bA_0, 0.0f);

#line 1459
            }
            else
            {

#line 1459
                _S54 = float2(0.0f, 0.0f);

#line 1459
            }

#line 1459
        }

#line 1459
        *_S56 = packed_float2(_S54) ;

#line 1457
    }



    if(_S51)
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
        int device* _S57 = peakIdx_0+pairB_0;

#line 1462
        if(hitB_0)
        {

#line 1462
            _S53 = int(0);

#line 1462
        }
        else
        {

#line 1462
            _S53 = int(-1);

#line 1462
        }

#line 1462
        *_S57 = _S53;

#line 1462
        packed_float2 device* _S58 = peakVal_0+pairB_0;
        if(infB_0)
        {

#line 1463
            _S54 = float2(3.40282306073709653e+38f, 0.0f);

#line 1463
        }
        else
        {

#line 1463
            if(hitB_0)
            {

#line 1463
                _S54 = float2(bB_0, 0.0f);

#line 1463
            }
            else
            {

#line 1463
                _S54 = float2(0.0f, 0.0f);

#line 1463
            }

#line 1463
        }

#line 1463
        *_S58 = packed_float2(_S54) ;

#line 1461
    }



    return;
}


#line 1329
void peakTwoWave_0(uint pairA_1, uint pairB_1, uint tid_1, const array<half2, int(16)> thread* re_8, const array<half2, int(16)> thread* im_8, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_1, KernelContext_0 thread* kernelContext_6)
{
    uint m_1;

#line 1331
    bool _S59;

#line 1331
    bool _S60;

    uint _S61 = slotToIndex_0(tid_1 * 16U) - winStart_3;
    uint _S62 = winEnd_3 - winStart_3;

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
        half2 mg_0 = mag2s_0((*re_8)[i_6], (*im_8)[i_6]);
        if((_S61 + slotToIndex_0(i_6)) < _S62)
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
        uint ovAcc_1 = ovAcc_0 | (((((uint(as_type<ushort>((*re_8)[i_6].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[i_6].y)) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>((*im_8)[i_6].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[i_6].y)) << 16U)) & 2080406528U) + 67109888U));


        uint _S63 = 15U - i_6;

#line 1351
        uint _S64 = max(kA_0, (m_1 << 16U) | _S63);
        uint _S65 = max(kB_0, (m_1 & 4294901760U) | _S63);

#line 1339
        i_6 = i_6 + 1U;

#line 1339
        ovAcc_0 = ovAcc_1;

#line 1339
        kA_0 = _S64;

#line 1339
        kB_0 = _S65;

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


    uint _S66 = (4095U - tid_1) << 4U;

#line 1360
    uint kA_1 = kA_0 | _S66;
    uint kB_1 = kB_0 | _S66;

#line 1361
    uint _S67 = mfShflXor_0(kA_1, 1U, kernelContext_6);

    uint _S68 = max(kA_1, _S67);

#line 1363
    uint _S69 = mfShflXor_0(kB_1, 1U, kernelContext_6);
    uint _S70 = max(kB_1, _S69);

#line 1364
    uint _S71 = mfShflXor_0(_S68, 2U, kernelContext_6);

#line 1363
    uint _S72 = max(_S68, _S71);

#line 1363
    uint _S73 = mfShflXor_0(_S70, 2U, kernelContext_6);
    uint _S74 = max(_S70, _S73);

#line 1364
    uint _S75 = mfShflXor_0(_S72, 4U, kernelContext_6);

#line 1363
    uint _S76 = max(_S72, _S75);

#line 1363
    uint _S77 = mfShflXor_0(_S74, 4U, kernelContext_6);
    uint _S78 = max(_S74, _S77);

#line 1364
    uint _S79 = mfShflXor_0(_S76, 8U, kernelContext_6);

#line 1363
    uint _S80 = max(_S76, _S79);

#line 1363
    uint _S81 = mfShflXor_0(_S78, 8U, kernelContext_6);
    uint _S82 = max(_S78, _S81);

    uint slotA_0 = 65535U - (_S80 & 65535U);

#line 1366
    uint slotB_0 = 65535U - (_S82 & 65535U);

#line 1372
    uint _S83 = _S80 >> 16U;

#line 1372
    bool infA_1 = _S83 >= 31744U;

#line 1372
    uint _S84 = _S82 >> 16U;

#line 1372
    bool infB_1 = _S84 >= 31744U;

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
        hitA_1 = (as_type<half>((ushort)((_S83)))) > (as_type<float>((thrBits_1)));

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
        hitB_1 = (as_type<half>((ushort)((_S84)))) > (as_type<float>((thrBits_1)));

#line 1377
    }

#line 1385
    uint _S85 = slotA_0 >> 4U;

#line 1385
    uint _S86 = slotA_0 & 15U;

#line 1385
    uint _S87 = slotB_0 >> 4U;

#line 1385
    uint _S88 = slotB_0 & 15U;
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
                                (*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + m_1 * 16U + tid_1] = (uint(as_type<ushort>((*re_8)[m_1].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[m_1].y)) << 16U);

#line 1391
                                m_1 = m_1 + 1U;

#line 1391
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            bool _S89 = tid_1 == 0U;

#line 1394
                            _S59 = _S89;

#line 1394
                            if(_S89)
                            {

#line 1395
                                if(_S86 >= 0U)
                                {

#line 1395
                                    _S60 = _S86 < 16U;

#line 1395
                                }
                                else
                                {

#line 1395
                                    _S60 = false;

#line 1395
                                }

#line 1395
                                if(_S60)
                                {

#line 1396
                                    vA_0[0U] = (as_type<half>((ushort)(((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S86 * 16U + _S85]))));

#line 1395
                                }

                                if(_S88 >= 0U)
                                {

#line 1397
                                    _S60 = _S88 < 16U;

#line 1397
                                }
                                else
                                {

#line 1397
                                    _S60 = false;

#line 1397
                                }

#line 1397
                                if(_S60)
                                {

#line 1398
                                    vB_0[0U] = (as_type<half>((ushort)((((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S88 * 16U + _S87]) >> 16U))));

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
                                (*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + m_1 * 16U + tid_1] = (uint(as_type<ushort>((*im_8)[m_1].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[m_1].y)) << 16U);

#line 1391
                                m_1 = m_1 + 1U;

#line 1391
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            if(_S59)
                            {

#line 1395
                                if(_S86 >= 0U)
                                {

#line 1395
                                    _S60 = _S86 < 16U;

#line 1395
                                }
                                else
                                {

#line 1395
                                    _S60 = false;

#line 1395
                                }

#line 1395
                                if(_S60)
                                {

#line 1396
                                    vA_0[1U] = (as_type<half>((ushort)(((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S86 * 16U + _S85]))));

#line 1395
                                }

                                if(_S88 >= 0U)
                                {

#line 1397
                                    _S60 = _S88 < 16U;

#line 1397
                                }
                                else
                                {

#line 1397
                                    _S60 = false;

#line 1397
                                }

#line 1397
                                if(_S60)
                                {

#line 1398
                                    vB_0[1U] = (as_type<half>((ushort)((((*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + _S88 * 16U + _S87]) >> 16U))));

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
    if(_S59)
    {

#line 1402
        _S60 = pairA_1 != 4294967295U;

#line 1402
    }
    else
    {

#line 1402
        _S60 = false;

#line 1402
    }

#line 1402
    int _S90;

#line 1402
    float2 _S91;

#line 1402
    if(_S60)
    {

#line 1403
        int device* _S92 = peakIdx_1+pairA_1;

#line 1403
        if(hitA_1)
        {

#line 1403
            _S90 = int(slotToIndex_0(slotA_0));

#line 1403
        }
        else
        {

#line 1403
            _S90 = int(-1);

#line 1403
        }

#line 1403
        *_S92 = _S90;

#line 1403
        packed_float2 device* _S93 = peakVal_1+pairA_1;
        if(infA_1)
        {

#line 1404
            _S91 = float2(3.40282306073709653e+38f, 0.0f);

#line 1404
        }
        else
        {

#line 1405
            if(hitA_1)
            {

#line 1405
                _S91 = float2(vA_0[int(0)], vA_0[int(1)]);

#line 1405
            }
            else
            {

#line 1405
                _S91 = float2(0.0f, 0.0f);

#line 1405
            }

#line 1404
        }

#line 1404
        *_S93 = packed_float2(_S91) ;

#line 1402
    }

#line 1407
    if(_S59)
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
        int device* _S94 = peakIdx_1+pairB_1;

#line 1408
        if(hitB_1)
        {

#line 1408
            _S90 = int(slotToIndex_0(slotB_0));

#line 1408
        }
        else
        {

#line 1408
            _S90 = int(-1);

#line 1408
        }

#line 1408
        *_S94 = _S90;

#line 1408
        packed_float2 device* _S95 = peakVal_1+pairB_1;
        if(infB_1)
        {

#line 1409
            _S91 = float2(3.40282306073709653e+38f, 0.0f);

#line 1409
        }
        else
        {

#line 1410
            if(hitB_1)
            {

#line 1410
                _S91 = float2(vB_0[int(0)], vB_0[int(1)]);

#line 1410
            }
            else
            {

#line 1410
                _S91 = float2(0.0f, 0.0f);

#line 1410
            }

#line 1409
        }

#line 1409
        *_S95 = packed_float2(_S91) ;

#line 1407
    }

#line 1412
    return;
}


#line 1471
void filterTwo_0(uint pairA_2, uint pairB_2, uint tA_0, uint tB_0, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* tmpl_0, int device* peakIdx_2, packed_float2 device* peakVal_2, uint winStart_4, uint winEnd_4, uint thrBits_2, KernelContext_0 thread* kernelContext_7)
{



    thread array<half2, int(16)> re_9;

#line 1476
    thread array<half2, int(16)> im_9;

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
        uint _S96 = 16U * n2_0;

#line 1478
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 256U + tid_2 + _S96);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 256U + tid_2 + _S96);
        half _S97 = (*dreg_0)[n2_0].x;
        half _S98 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S97, _S97), half2(_S98, _S98), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_9[n2_0], &im_9[n2_0]);

#line 1477
        n2_0 = n2_0 + 1U;

#line 1477
    }

#line 1490
    uint lgTB_0 = firstbithigh_0(16U);
    uint lgLn_0 = firstbithigh_0(256U);
    uint blk_2 = tid_2 >> lgTB_0;
    uint lane_2 = tid_2 & 15U;

    dft16s_0(&re_9, &im_9);

#line 52 "twiddle.slang"
    uint _S99 = mfCoarseTwtFlag_0();

#line 52
    uint k2_2;

#line 1497 "mm_256_fusedTierB_c16t2.slang"
    if(_S99 != 0U)
    {

#line 1497
        k2_2 = 0U;

#line 1504
        for(;;)
        {

#line 1504
            if(k2_2 < 16U)
            {
            }
            else
            {

#line 1504
                break;
            }

#line 1505
            uint _S100 = lane_2 * 16U + k2_2;
            cmulw_0(&re_9[k2_2], &im_9[k2_2], as_type<half>(ushort((COARSE_TWT_DATA_0[_S100]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S100]) >> 16U) & 65535U)));

#line 1504
            k2_2 = k2_2 + 1U;

#line 1504
        }

#line 1497
    }
    else
    {

#line 1513
        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 256.0f);
        float _S101 = tw_0.x;

#line 1514
        float _S102 = tw_0.y;

#line 1514
        k2_2 = 0U;

#line 1514
        float cr_0 = 1.0f;

#line 1514
        float ci_0 = 0.0f;

        for(;;)
        {

#line 1516
            if(k2_2 < 16U)
            {
            }
            else
            {

#line 1516
                break;
            }

#line 1517
            cmulw_0(&re_9[k2_2], &im_9[k2_2], half(cr_0), half(ci_0));
            float nr_0 = cr_0 * _S101 - ci_0 * _S102;
            float _S103 = cr_0 * _S102 + ci_0 * _S101;

#line 1516
            k2_2 = k2_2 + 1U;

#line 1516
            cr_0 = nr_0;

#line 1516
            ci_0 = _S103;

#line 1516
        }

#line 1497
    }

#line 1523
    uint per_2 = 16U / max(16U, 1U);
    uint _S104 = max(1U, 1U);
    uint blk2_2 = tid_2 / _S104;

#line 1525
    uint lane2_2 = tid_2 % _S104;

#line 1525
    exchangeS_0(&re_9, &im_9, lgLn_0, lgTB_0, 16U, 256U, blk_2, lane_2, per_2, _S104, 16U, blk2_2, lane2_2, kernelContext_7);


    innermostS_0(&re_9, &im_9);

#line 1547
    if(thrBits_2 != 0U)
    {

#line 1548
        float _S105 = (as_type<float>((thrBits_2)));

#line 1548
        thread array<half2, int(16)> _S106 = re_9;

#line 1548
        thread array<half2, int(16)> _S107 = im_9;

#line 1548
        peakTwoGate_0(pairA_2, pairB_2, tid_2, &_S106, &_S107, peakIdx_2, peakVal_2, winStart_4, winEnd_4, _S105, kernelContext_7);

#line 1547
    }
    else
    {

#line 1547
        thread array<half2, int(16)> _S108 = re_9;

#line 1547
        thread array<half2, int(16)> _S109 = im_9;

#line 1547
        peakTwoWave_0(pairA_2, pairB_2, tid_2, &_S108, &_S109, peakIdx_2, peakVal_2, winStart_4, winEnd_4, thrBits_2, kernelContext_7);

#line 1547
    }

#line 1575
    return;
}


void filterPair_0(uint pair_0, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_3, packed_float2 device* peakVal_3, uint ntmpl_1, uint winStart_5, uint winEnd_5, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, uint device* rowWin_1, KernelContext_0 thread* kernelContext_8)
{

#line 1579
    thread uint _S110 = winStart_5;

#line 1579
    thread uint _S111 = winEnd_5;

#line 1585
    kernelContext_8->_tid_0 = tid_3;

#line 1605
    uint tiles_0 = (ntmpl_1 + 2U - 1U) / 2U;
    uint slots_0 = binsize_1 * tiles_0;
    bool slotOk_0 = pair_0 < slots_0;

#line 1607
    uint q_1;
    if(slotOk_0)
    {

#line 1608
        q_1 = pair_0;

#line 1608
    }
    else
    {

#line 1608
        q_1 = slots_0 - 1U;

#line 1608
    }
    uint d_5 = q_1 / tiles_0;

#line 1609
    uint t0_0 = (q_1 - d_5 * tiles_0) * 2U;
    uint _S112 = d_5 * ntmpl_1 + t0_0;

#line 1610
    rowWindow_0(d_5, &_S110, &_S111, rowWin_1, kernelContext_8);

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
        uint _S113 = mfDataStrideFlag_0();

#line 178 "mm_256_fusedTierB_c16t2.slang"
        if(_S113 != 0U)
        {

#line 63 "twiddle.slang"
            uint _S114 = mfDataStrideFlag_0();

#line 63
            q_1 = _S114;

#line 178 "mm_256_fusedTierB_c16t2.slang"
        }
        else
        {

#line 178
            q_1 = 256U;

#line 178
        }

#line 1638
        half2 _S115 = dload_0(data_0, d_5 * q_1 + tid_3 + 16U * n2_1);

#line 1638
        dreg_1[n2_1] = _S115;

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
        if(k_0 < 2U)
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
            q_1 = _S112 + k_0;

#line 1647
        }
        else
        {

#line 1647
            q_1 = 4294967295U;

#line 1647
        }

#line 1647
        if(okB_0)
        {

#line 1647
            n2_1 = _S112 + k_0 + 1U;

#line 1647
        }
        else
        {

#line 1647
            n2_1 = 4294967295U;

#line 1647
        }
        uint _S116 = t0_0 + k_0;

#line 1648
        uint _S117 = ntmpl_1 - 1U;

#line 1648
        uint _S118 = min(_S116, _S117);

#line 1648
        uint _S119 = min(_S116 + 1U, _S117);

#line 1648
        thread array<half2, int(16)> _S120 = dreg_1;

#line 1648
        filterTwo_0(q_1, n2_1, _S118, _S119, tid_3, &_S120, tmpl_1, peakIdx_3, peakVal_3, _S110, _S111, thrBits_3, kernelContext_8);

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
    threadgroup array<uint, int(256)> stg_1;

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
