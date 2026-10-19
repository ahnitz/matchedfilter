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


#line 210 "mm_256_fusedTierB_c16p4t8.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0, uint device* rowWin_0)
{

#line 104 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 212 "mm_256_fusedTierB_c16p4t8.slang"
    if(_S3 == 0U)
    {

#line 212
        return;
    }

#line 213
    uint _S4 = 2U * d_0;

#line 213
    *winStart_0 = rowWin_0[_S4];
    *winEnd_0 = rowWin_0[_S4 + 1U];
    return;
}


#line 72 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S5 = ((MF_DATA_STRIDE));

#line 75
    return _S5;
}



uint mfDataScaleFlag_0()
{
    ;
    uint _S6 = ((MF_DATA_SCALE_BITS));

#line 83
    return _S6;
}


#line 167 "mm_256_fusedTierB_c16p4t8.slang"
half2 cload_0(uint device* b_0, uint i_0)
{

#line 168
    uint p_0 = b_0[i_0];

#line 168
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 234
half2 dload_0(uint device* b_1, uint i_1)
{

#line 77 "twiddle.slang"
    uint _S7 = mfDataStrideFlag_0();

#line 236 "mm_256_fusedTierB_c16p4t8.slang"
    if(_S7 != 0U)
    {

#line 85 "twiddle.slang"
        uint _S8 = mfDataScaleFlag_0();

#line 237 "mm_256_fusedTierB_c16p4t8.slang"
        float s_0 = (as_type<float>((_S8)));
        uint _S9 = 2U * i_1;

#line 238
        return half2(half((as_type<float>((b_1[_S9]))) * s_0), half((as_type<float>((b_1[_S9 + 1U]))) * s_0));
    }
    return cload_0(b_1, i_1);
}


#line 364
void cmulconjs_0(half2 ar_0, half2 ai_0, half2 br_0, half2 bi_0, half2 thread* pr_0, half2 thread* pi_0)
{
    *pr_0 = ar_0 * br_0 + ai_0 * bi_0;
    *pi_0 = ai_0 * br_0 - ar_0 * bi_0;
    return;
}


#line 376
void r4s_0(array<half2, int(16)> thread* re_0, array<half2, int(16)> thread* im_0, uint a_0, uint b_2, uint c_0, uint d_1)
{
    half2 t0r_0 = (*re_0)[a_0] + (*re_0)[c_0];

#line 378
    half2 t0i_0 = (*im_0)[a_0] + (*im_0)[c_0];
    half2 t1r_0 = (*re_0)[a_0] - (*re_0)[c_0];

#line 379
    half2 t1i_0 = (*im_0)[a_0] - (*im_0)[c_0];
    half2 t2r_0 = (*re_0)[b_2] + (*re_0)[d_1];

#line 380
    half2 t2i_0 = (*im_0)[b_2] + (*im_0)[d_1];
    half2 t3r_0 = (*re_0)[b_2] - (*re_0)[d_1];
    half2 j3r_0 = - ((*im_0)[b_2] - (*im_0)[d_1]);
    (*re_0)[a_0] = t0r_0 + t2r_0;

#line 383
    (*im_0)[a_0] = t0i_0 + t2i_0;
    (*re_0)[b_2] = t1r_0 + j3r_0;

#line 384
    (*im_0)[b_2] = t1i_0 + t3r_0;
    (*re_0)[c_0] = t0r_0 - t2r_0;

#line 385
    (*im_0)[c_0] = t0i_0 - t2i_0;
    (*re_0)[d_1] = t1r_0 - j3r_0;

#line 386
    (*im_0)[d_1] = t1i_0 - t3r_0;
    return;
}


#line 355
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 355
    half2 _S10 = half2(wr_0) ;

#line 355
    half2 _S11 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S11 + *xi_0 * _S10;
    *xr_0 = *xr_0 * _S10 - *xi_0 * _S11;

#line 359
    *xi_0 = ni_0;
    return;
}


#line 389
void swap2_0(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint p_1, uint q_0)
{

    half2 t_0 = (*re_1)[p_1];

#line 392
    (*re_1)[p_1] = (*re_1)[q_0];

#line 392
    (*re_1)[q_0] = t_0;
    half2 t_1 = (*im_1)[p_1];

#line 393
    (*im_1)[p_1] = (*im_1)[q_0];

#line 393
    (*im_1)[q_0] = t_1;
    return;
}


#line 427
void dft16s_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2)
{

#line 427
    uint n1_0 = 0U;

    for(;;)
    {

#line 429
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 429
            break;
        }

#line 429
        r4s_0(re_2, im_2, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 429
        n1_0 = n1_0 + 1U;

#line 429
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

#line 440
    uint k2_0 = 0U;
    for(;;)
    {

#line 441
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 441
            break;
        }

#line 442
        uint _S12 = 4U * k2_0;

#line 442
        r4s_0(re_2, im_2, _S12, _S12 + 1U, _S12 + 2U, _S12 + 3U);

#line 441
        k2_0 = k2_0 + 1U;

#line 441
    }

    swap2_0(re_2, im_2, 1U, 4U);

#line 443
    swap2_0(re_2, im_2, 2U, 8U);

#line 443
    swap2_0(re_2, im_2, 3U, 12U);
    swap2_0(re_2, im_2, 6U, 9U);

#line 444
    swap2_0(re_2, im_2, 7U, 13U);

#line 444
    swap2_0(re_2, im_2, 11U, 14U);
    return;
}


#line 427
void dft16s_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3)
{

#line 427
    uint n1_1 = 0U;

    for(;;)
    {

#line 429
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 429
            break;
        }

#line 429
        r4s_0(re_3, im_3, n1_1, n1_1 + 4U, n1_1 + 8U, n1_1 + 12U);

#line 429
        n1_1 = n1_1 + 1U;

#line 429
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

#line 440
    uint k2_1 = 0U;
    for(;;)
    {

#line 441
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 441
            break;
        }

#line 442
        uint _S13 = 4U * k2_1;

#line 442
        r4s_0(re_3, im_3, _S13, _S13 + 1U, _S13 + 2U, _S13 + 3U);

#line 441
        k2_1 = k2_1 + 1U;

#line 441
    }

    swap2_0(re_3, im_3, 1U, 4U);

#line 443
    swap2_0(re_3, im_3, 2U, 8U);

#line 443
    swap2_0(re_3, im_3, 3U, 12U);
    swap2_0(re_3, im_3, 6U, 9U);

#line 444
    swap2_0(re_3, im_3, 7U, 13U);

#line 444
    swap2_0(re_3, im_3, 11U, 14U);
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


#line 303 "mm_256_fusedTierB_c16p4t8.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S18 = max(TB_0, 1U);

#line 305
    uint j_0 = d_2 / _S18;

#line 305
    uint m_0 = d_2 % _S18;

#line 305
    uint _S19;
    if(TB_0 <= 16U)
    {

#line 306
        _S19 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 306
    }
    else
    {

#line 306
        _S19 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 306
    }

#line 306
    return _S19;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint ntmpl_0;
    uint winStart_1;
    uint winEnd_1;
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
    array<uint, int(1024)> threadgroup* stg_0;
    uint _S20;
};


#line 279 "mm_256_fusedTierB_c16p4t8.slang"
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 279
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 279
    return;
}


#line 280
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 280
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 465
void exchangeS_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{
    uint j_1;

    thread array<half2, int(16)> outr_0;

#line 469
    thread array<half2, int(16)> outi_0;

#line 469
    uint z_1 = 0U;
    for(;;)
    {

#line 470
        if(z_1 < 16U)
        {
        }
        else
        {

#line 470
            break;
        }

#line 470
        half2 _S21 = half2(float2(0.0f) );

#line 470
        outr_0[z_1] = _S21;

#line 470
        outi_0[z_1] = _S21;

#line 470
        z_1 = z_1 + 1U;

#line 470
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S22 = p0_0 & lenMask_0;
    uint _S23 = (_S22 >> lgSpan_0) * 16U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S22 & spanMask_0);

#line 475
    uint c_2 = 0U;
    for(;;)
    {

#line 476
        if(c_2 < 1U)
        {
        }
        else
        {

#line 476
            break;
        }

#line 476
        for(;;)
        {

#line 476
            for(;;)
            {

#line 477
                for(;;)
                {

#line 478
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 478
                    j_1 = 0U;
                    for(;;)
                    {

#line 479
                        if(j_1 < 16U)
                        {
                        }
                        else
                        {

#line 479
                            break;
                        }

#line 480
                        uint _S24 = j_1 * 16U + kernelContext_2->_tid_0;

#line 480
                        stgPut_0(_S24, (*re_4)[c_2 * 16U + j_1], kernelContext_2);

#line 479
                        j_1 = j_1 + 1U;

#line 479
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 481
                    uint d_3 = 0U;
                    for(;;)
                    {

#line 482
                        if(d_3 < 16U)
                        {
                        }
                        else
                        {

#line 482
                            break;
                        }
                        uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S25 = pz_0 & lenMask_0;
                        uint az_0 = (_S25 >> lgSpan_0) * 16U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S25 & spanMask_0);

#line 486
                        half2 _S26 = stgGet_0(_S23 + az_0 - c_2 * 16U * 16U, kernelContext_2);



                        outr_0[d_3] = _S26;

#line 482
                        d_3 = d_3 + 1U;

#line 482
                    }

#line 477
                    break;
                }

#line 477
                break;
            }

#line 477
            for(;;)
            {

#line 477
                for(;;)
                {

#line 478
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 478
                    uint j_2 = 0U;
                    for(;;)
                    {

#line 479
                        if(j_2 < 16U)
                        {
                        }
                        else
                        {

#line 479
                            break;
                        }

#line 480
                        uint _S27 = j_2 * 16U + kernelContext_2->_tid_0;

#line 480
                        stgPut_0(_S27, (*im_4)[c_2 * 16U + j_2], kernelContext_2);

#line 479
                        j_2 = j_2 + 1U;

#line 479
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 481
                    uint d_4 = 0U;
                    for(;;)
                    {

#line 482
                        if(d_4 < 16U)
                        {
                        }
                        else
                        {

#line 482
                            break;
                        }
                        uint pz_1 = computeWant_0(d_4, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S28 = pz_1 & lenMask_0;
                        uint az_1 = (_S28 >> lgSpan_0) * 16U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S28 & spanMask_0);

#line 486
                        half2 _S29 = stgGet_0(_S23 + az_1 - c_2 * 16U * 16U, kernelContext_2);



                        outi_0[d_4] = _S29;

#line 482
                        d_4 = d_4 + 1U;

#line 482
                    }

#line 477
                    break;
                }

#line 477
                break;
            }

#line 477
            break;
        }

#line 476
        c_2 = c_2 + 1U;

#line 476
    }

#line 476
    j_1 = 0U;

#line 495
    for(;;)
    {

#line 495
        if(j_1 < 16U)
        {
        }
        else
        {

#line 495
            break;
        }

#line 495
        (*re_4)[j_1] = outr_0[j_1];

#line 495
        (*im_4)[j_1] = outi_0[j_1];

#line 495
        j_1 = j_1 + 1U;

#line 495
    }
    return;
}


#line 498
void innermostS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5)
{
    dft16s_1(re_5, im_5);



    return;
}


#line 791
uint lgOf_0(uint i_4)
{

#line 791
    uint _S30;

#line 791
    if(i_4 < 1U)
    {

#line 791
        _S30 = 4U;

#line 791
    }
    else
    {

#line 791
        if(i_4 == 1U)
        {

#line 791
            _S30 = 4U;

#line 791
        }
        else
        {

#line 791
            _S30 = 1U;

#line 791
        }

#line 791
    }

#line 791
    return _S30;
}


#line 793
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 797
    uint lg_1 = lgOf_0(0U);

#line 802
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 451
half2 mag2s_0(half2 re_6, half2 im_6)
{

#line 451
    return re_6 * re_6 + im_6 * im_6;
}


#line 1345
uint mfShflXor_0(uint v_1, uint s_2, KernelContext_0 thread* kernelContext_3)
{

#line 1345
    uint _S31 = (simd_shuffle((v_1), ushort((int((kernelContext_3->_S20) ^ s_2)))));

#line 1345
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


#line 1466 "mm_256_fusedTierB_c16p4t8.slang"
void peakTwoGate_0(uint pairA_0, uint pairB_0, uint tid_0, const array<half2, int(16)> thread* re_7, const array<half2, int(16)> thread* im_7, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, float thr_0, KernelContext_0 thread* kernelContext_4)
{


    uint _S33 = slotToIndex_0(tid_0 * 16U) - winStart_2;
    uint _S34 = winEnd_2 - winStart_2;
    half2 _S35 = half2(float2(0.0f) );
    half2 _S36 = half2(float2(0.015625f) );

#line 1473
    uint i_5 = 0U;

#line 1473
    half2 best_0 = _S35;

#line 1473
    half2 en_0 = _S35;
    for(;;)
    {

#line 1474
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1474
            break;
        }

#line 1474
        half2 _S37;

        if((_S33 + slotToIndex_0(i_5)) < _S34)
        {

#line 1476
            _S37 = mag2s_0((*re_7)[i_5], (*im_7)[i_5]);

#line 1476
        }
        else
        {

#line 1476
            _S37 = _S35;

#line 1476
        }

#line 1476
        half2 _S38 = max(best_0, _S37);
        half2 sr_0 = (*re_7)[i_5] * _S36;

#line 1477
        half2 si_0 = (*im_7)[i_5] * _S36;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1474
        i_5 = i_5 + 1U;

#line 1474
        best_0 = _S38;

#line 1474
        en_0 = en_1;

#line 1474
    }

#line 1474
    uint _S39 = mfShflXor_0((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U), 1U, kernelContext_4);

#line 1481
    half2 _S40 = max(best_0, half2(as_type<half>(ushort(_S39 & 65535U)), as_type<half>(ushort((_S39 >> 16U) & 65535U))));

#line 1481
    uint _S41 = mfShflXor_0((uint(as_type<ushort>(en_0[0U])) & 65535U) | (uint(as_type<ushort>(en_0[1U])) << 16U), 1U, kernelContext_4);
    half2 en_2 = en_0 + half2(as_type<half>(ushort(_S41 & 65535U)), as_type<half>(ushort((_S41 >> 16U) & 65535U)));

#line 1482
    uint _S42 = mfShflXor_0((uint(as_type<ushort>(_S40[0U])) & 65535U) | (uint(as_type<ushort>(_S40[1U])) << 16U), 2U, kernelContext_4);

#line 1481
    half2 _S43 = max(_S40, half2(as_type<half>(ushort(_S42 & 65535U)), as_type<half>(ushort((_S42 >> 16U) & 65535U))));

#line 1481
    uint _S44 = mfShflXor_0((uint(as_type<ushort>(en_2[0U])) & 65535U) | (uint(as_type<ushort>(en_2[1U])) << 16U), 2U, kernelContext_4);
    half2 en_3 = en_2 + half2(as_type<half>(ushort(_S44 & 65535U)), as_type<half>(ushort((_S44 >> 16U) & 65535U)));

#line 1482
    uint _S45 = mfShflXor_0((uint(as_type<ushort>(_S43[0U])) & 65535U) | (uint(as_type<ushort>(_S43[1U])) << 16U), 4U, kernelContext_4);

#line 1481
    half2 _S46 = max(_S43, half2(as_type<half>(ushort(_S45 & 65535U)), as_type<half>(ushort((_S45 >> 16U) & 65535U))));

#line 1481
    uint _S47 = mfShflXor_0((uint(as_type<ushort>(en_3[0U])) & 65535U) | (uint(as_type<ushort>(en_3[1U])) << 16U), 4U, kernelContext_4);
    half2 en_4 = en_3 + half2(as_type<half>(ushort(_S47 & 65535U)), as_type<half>(ushort((_S47 >> 16U) & 65535U)));

#line 1482
    uint _S48 = mfShflXor_0((uint(as_type<ushort>(_S46[0U])) & 65535U) | (uint(as_type<ushort>(_S46[1U])) << 16U), 8U, kernelContext_4);

#line 1481
    half2 best_1 = max(_S46, half2(as_type<half>(ushort(_S48 & 65535U)), as_type<half>(ushort((_S48 >> 16U) & 65535U))));

#line 1481
    uint _S49 = mfShflXor_0((uint(as_type<ushort>(en_4[0U])) & 65535U) | (uint(as_type<ushort>(en_4[1U])) << 16U), 8U, kernelContext_4);
    half2 en_5 = en_4 + half2(as_type<half>(ushort(_S49 & 65535U)), as_type<half>(ushort((_S49 >> 16U) & 65535U)));

#line 1482
    uint _S50 = (uint(as_type<ushort>(en_5[0U])) & 65535U) | (uint(as_type<ushort>(en_5[1U])) << 16U);

#line 1482
    uint _S51 = (uint(as_type<ushort>(best_1[0U])) & 65535U) | (uint(as_type<ushort>(best_1[1U])) << 16U);

#line 1482
    bool infA_0;

#line 1490
    if((_S50 & 31744U) == 31744U)
    {

#line 1490
        infA_0 = true;

#line 1490
    }
    else
    {

#line 1490
        infA_0 = (_S51 & 31744U) == 31744U;

#line 1490
    }

#line 1490
    bool infB_0;
    if((_S50 & 2080374784U) == 2080374784U)
    {

#line 1491
        infB_0 = true;

#line 1491
    }
    else
    {

#line 1491
        infB_0 = (_S51 & 2080374784U) == 2080374784U;

#line 1491
    }

#line 115 "twiddle.slang"
    uint _S52 = mfC16RawFlag_0();

#line 115
    float _S53;

#line 1494 "mm_256_fusedTierB_c16p4t8.slang"
    if((1U - _S52) != 0U)
    {

#line 1494
        _S53 = 12.66209983825683594f;

#line 1494
    }
    else
    {

#line 1494
        _S53 = 0.0f;

#line 1494
    }

#line 1494
    float k2_2 = _S53 * 0.00048828125f * 1.00010001659393311f;
    float mA_0 = sqrt(float(best_1.x));

#line 1495
    float mB_0 = sqrt(float(best_1.y));

    float bA_0 = mA_0 * 1.00107669830322266f + k2_2 * sqrt(float(en_5.x) * 16.0f);
    float bB_0 = mB_0 * 1.00107669830322266f + k2_2 * sqrt(float(en_5.y) * 16.0f);

#line 1498
    bool hitA_0;
    if(infA_0)
    {

#line 1499
        hitA_0 = true;

#line 1499
    }
    else
    {

#line 1499
        if(mA_0 > 0.0f)
        {

#line 1499
            hitA_0 = bA_0 >= thr_0;

#line 1499
        }
        else
        {

#line 1499
            hitA_0 = false;

#line 1499
        }

#line 1499
    }

#line 1499
    bool hitB_0;
    if(infB_0)
    {

#line 1500
        hitB_0 = true;

#line 1500
    }
    else
    {

#line 1500
        if(mB_0 > 0.0f)
        {

#line 1500
            hitB_0 = bB_0 >= thr_0;

#line 1500
        }
        else
        {

#line 1500
            hitB_0 = false;

#line 1500
        }

#line 1500
    }
    bool _S54 = tid_0 == 0U;

#line 1501
    bool _S55;

#line 1501
    if(_S54)
    {

#line 1501
        _S55 = pairA_0 != 4294967295U;

#line 1501
    }
    else
    {

#line 1501
        _S55 = false;

#line 1501
    }

#line 1501
    int _S56;

#line 1501
    float2 _S57;

#line 1501
    if(_S55)
    {

#line 1502
        int device* _S58 = peakIdx_0+pairA_0;

#line 1502
        if(hitA_0)
        {

#line 1502
            _S56 = int(0);

#line 1502
        }
        else
        {

#line 1502
            _S56 = int(-1);

#line 1502
        }

#line 1502
        *_S58 = _S56;

#line 1502
        packed_float2 device* _S59 = peakVal_0+pairA_0;
        if(infA_0)
        {

#line 1503
            _S57 = float2(3.40282306073709653e+38f, 0.0f);

#line 1503
        }
        else
        {

#line 1503
            if(hitA_0)
            {

#line 1503
                _S57 = float2(bA_0, 0.0f);

#line 1503
            }
            else
            {

#line 1503
                _S57 = float2(0.0f, 0.0f);

#line 1503
            }

#line 1503
        }

#line 1503
        *_S59 = packed_float2(_S57) ;

#line 1501
    }



    if(_S54)
    {

#line 1505
        infA_0 = pairB_0 != 4294967295U;

#line 1505
    }
    else
    {

#line 1505
        infA_0 = false;

#line 1505
    }

#line 1505
    if(infA_0)
    {

#line 1506
        int device* _S60 = peakIdx_0+pairB_0;

#line 1506
        if(hitB_0)
        {

#line 1506
            _S56 = int(0);

#line 1506
        }
        else
        {

#line 1506
            _S56 = int(-1);

#line 1506
        }

#line 1506
        *_S60 = _S56;

#line 1506
        packed_float2 device* _S61 = peakVal_0+pairB_0;
        if(infB_0)
        {

#line 1507
            _S57 = float2(3.40282306073709653e+38f, 0.0f);

#line 1507
        }
        else
        {

#line 1507
            if(hitB_0)
            {

#line 1507
                _S57 = float2(bB_0, 0.0f);

#line 1507
            }
            else
            {

#line 1507
                _S57 = float2(0.0f, 0.0f);

#line 1507
            }

#line 1507
        }

#line 1507
        *_S61 = packed_float2(_S57) ;

#line 1505
    }



    return;
}


#line 332
float2 c16Bound_0(float2 v_2, float energy_0)
{

#line 115 "twiddle.slang"
    uint _S62 = mfC16RawFlag_0();

#line 334 "mm_256_fusedTierB_c16p4t8.slang"
    if((1U - _S62) == 0U)
    {

#line 334
        return v_2;
    }

#line 335
    float m_1 = length(v_2);
    float b_3 = m_1 * 1.00146484375f + 0.00618266593664885f * sqrt(energy_0);

#line 336
    float2 _S63;
    if(m_1 > 0.0f)
    {

#line 337
        _S63 = v_2 * float2((b_3 / m_1)) ;

#line 337
    }
    else
    {

#line 337
        _S63 = float2(b_3, 0.0f);

#line 337
    }

#line 337
    return _S63;
}


#line 1348
void peakTwoWave_0(uint pairA_1, uint pairB_1, uint tid_1, const array<half2, int(16)> thread* re_8, const array<half2, int(16)> thread* im_8, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{
    uint m_2;

#line 1350
    bool _S64;

#line 1350
    bool _S65;

    uint _S66 = slotToIndex_0(tid_1 * 16U) - winStart_3;
    uint _S67 = winEnd_3 - winStart_3;

#line 1360
    half2 _S68 = half2(float2(0.0f) );
    half2 _S69 = half2(float2(0.015625f) );

#line 1361
    uint i_6 = 0U;

#line 1361
    half2 en_6 = _S68;

#line 1361
    uint ovAcc_0 = 0U;

#line 1361
    uint kA_0 = 0U;

#line 1361
    uint kB_0 = 0U;



    for(;;)
    {

#line 1365
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1365
            break;
        }
        half2 mg_0 = mag2s_0((*re_8)[i_6], (*im_8)[i_6]);
        half2 sr_1 = (*re_8)[i_6] * _S69;

#line 1368
        half2 si_1 = (*im_8)[i_6] * _S69;
        half2 en_7 = en_6 + (sr_1 * sr_1 + si_1 * si_1);
        if((_S66 + slotToIndex_0(i_6)) < _S67)
        {

#line 1370
            m_2 = (uint(as_type<ushort>(mg_0[0U])) & 65535U) | (uint(as_type<ushort>(mg_0[1U])) << 16U);

#line 1370
        }
        else
        {

#line 1370
            m_2 = 0U;

#line 1370
        }

#line 1376
        uint ovAcc_1 = ovAcc_0 | (((((uint(as_type<ushort>((*re_8)[i_6].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[i_6].y)) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>((*im_8)[i_6].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[i_6].y)) << 16U)) & 2080406528U) + 67109888U));


        uint _S70 = 15U - i_6;

#line 1379
        uint _S71 = max(kA_0, (m_2 << 16U) | _S70);
        uint _S72 = max(kB_0, (m_2 & 4294901760U) | _S70);

#line 1365
        i_6 = i_6 + 1U;

#line 1365
        en_6 = en_7;

#line 1365
        ovAcc_0 = ovAcc_1;

#line 1365
        kA_0 = _S71;

#line 1365
        kB_0 = _S72;

#line 1365
    }

#line 1384
    if((ovAcc_0 & 32768U) != 0U)
    {

#line 1384
        kA_0 = max(kA_0, 2080374799U);

#line 1384
    }
    if((ovAcc_0 & 2147483648U) != 0U)
    {

#line 1385
        kB_0 = max(kB_0, 2080374799U);

#line 1385
    }


    uint _S73 = (4095U - tid_1) << 4U;

#line 1388
    uint kA_1 = kA_0 | _S73;
    uint kB_1 = kB_0 | _S73;

#line 1389
    uint _S74 = mfShflXor_0(kA_1, 1U, kernelContext_5);

    uint _S75 = max(kA_1, _S74);

#line 1391
    uint _S76 = mfShflXor_0(kB_1, 1U, kernelContext_5);
    uint _S77 = max(kB_1, _S76);

#line 1392
    uint _S78 = mfShflXor_0((uint(as_type<ushort>(en_6[0U])) & 65535U) | (uint(as_type<ushort>(en_6[1U])) << 16U), 1U, kernelContext_5);
    half2 en_8 = en_6 + half2(as_type<half>(ushort(_S78 & 65535U)), as_type<half>(ushort((_S78 >> 16U) & 65535U)));

#line 1393
    uint _S79 = mfShflXor_0(_S75, 2U, kernelContext_5);

#line 1391
    uint _S80 = max(_S75, _S79);

#line 1391
    uint _S81 = mfShflXor_0(_S77, 2U, kernelContext_5);
    uint _S82 = max(_S77, _S81);

#line 1392
    uint _S83 = mfShflXor_0((uint(as_type<ushort>(en_8[0U])) & 65535U) | (uint(as_type<ushort>(en_8[1U])) << 16U), 2U, kernelContext_5);
    half2 en_9 = en_8 + half2(as_type<half>(ushort(_S83 & 65535U)), as_type<half>(ushort((_S83 >> 16U) & 65535U)));

#line 1393
    uint _S84 = mfShflXor_0(_S80, 4U, kernelContext_5);

#line 1391
    uint _S85 = max(_S80, _S84);

#line 1391
    uint _S86 = mfShflXor_0(_S82, 4U, kernelContext_5);
    uint _S87 = max(_S82, _S86);

#line 1392
    uint _S88 = mfShflXor_0((uint(as_type<ushort>(en_9[0U])) & 65535U) | (uint(as_type<ushort>(en_9[1U])) << 16U), 4U, kernelContext_5);
    half2 en_10 = en_9 + half2(as_type<half>(ushort(_S88 & 65535U)), as_type<half>(ushort((_S88 >> 16U) & 65535U)));

#line 1393
    uint _S89 = mfShflXor_0(_S85, 8U, kernelContext_5);

#line 1391
    uint _S90 = max(_S85, _S89);

#line 1391
    uint _S91 = mfShflXor_0(_S87, 8U, kernelContext_5);
    uint _S92 = max(_S87, _S91);

#line 1392
    uint _S93 = mfShflXor_0((uint(as_type<ushort>(en_10[0U])) & 65535U) | (uint(as_type<ushort>(en_10[1U])) << 16U), 8U, kernelContext_5);
    half2 en_11 = en_10 + half2(as_type<half>(ushort(_S93 & 65535U)), as_type<half>(ushort((_S93 >> 16U) & 65535U)));



    float enA_0 = float(en_11.x) * 16.0f;

#line 1397
    float enB_0 = float(en_11.y) * 16.0f;
    uint slotA_0 = 65535U - (_S90 & 65535U);

#line 1398
    uint slotB_0 = 65535U - (_S92 & 65535U);

#line 1404
    uint _S94 = _S90 >> 16U;

#line 1404
    bool infA_1 = _S94 >= 31744U;

#line 1404
    uint _S95 = _S92 >> 16U;

#line 1404
    bool infB_1 = _S95 >= 31744U;

#line 1404
    bool hitA_1;



    if(infA_1)
    {

#line 1408
        hitA_1 = true;

#line 1408
    }
    else
    {

#line 1408
        hitA_1 = (as_type<half>((ushort)((_S94)))) > (as_type<float>((thrBits_1)));

#line 1408
    }

#line 1408
    bool hitB_1;
    if(infB_1)
    {

#line 1409
        hitB_1 = true;

#line 1409
    }
    else
    {

#line 1409
        hitB_1 = (as_type<half>((ushort)((_S95)))) > (as_type<float>((thrBits_1)));

#line 1409
    }

#line 1417
    uint _S96 = slotA_0 >> 4U;

#line 1417
    uint _S97 = slotA_0 & 15U;

#line 1417
    uint _S98 = slotB_0 >> 4U;

#line 1417
    uint _S99 = slotB_0 & 15U;
    thread array<float, int(2)> vA_0;

#line 1418
    thread array<float, int(2)> vB_0;
    vB_0[int(1)] = 0.0f;

#line 1419
    vB_0[int(0)] = 0.0f;

#line 1419
    vA_0[int(1)] = 0.0f;

#line 1419
    vA_0[int(0)] = 0.0f;

#line 1419
    for(;;)
    {

#line 1419
        for(;;)
        {

#line 1420
            for(;;)
            {

#line 1420
                for(;;)
                {

#line 1420
                    for(;;)
                    {

#line 1421
                        for(;;)
                        {

#line 1422
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1422
                            m_2 = 0U;
                            for(;;)
                            {

#line 1423
                                if(m_2 < 16U)
                                {
                                }
                                else
                                {

#line 1423
                                    break;
                                }

#line 1424
                                (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + m_2 * 16U + tid_1] = (uint(as_type<ushort>((*re_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[m_2].y)) << 16U);

#line 1423
                                m_2 = m_2 + 1U;

#line 1423
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            bool _S100 = tid_1 == 0U;

#line 1426
                            _S64 = _S100;

#line 1426
                            if(_S100)
                            {

#line 1427
                                if(_S97 >= 0U)
                                {

#line 1427
                                    _S65 = _S97 < 16U;

#line 1427
                                }
                                else
                                {

#line 1427
                                    _S65 = false;

#line 1427
                                }

#line 1427
                                if(_S65)
                                {

#line 1428
                                    vA_0[0U] = (as_type<half>((ushort)(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S97 * 16U + _S96]))));

#line 1427
                                }

                                if(_S99 >= 0U)
                                {

#line 1429
                                    _S65 = _S99 < 16U;

#line 1429
                                }
                                else
                                {

#line 1429
                                    _S65 = false;

#line 1429
                                }

#line 1429
                                if(_S65)
                                {

#line 1430
                                    vB_0[0U] = (as_type<half>((ushort)((((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S99 * 16U + _S98]) >> 16U))));

#line 1429
                                }

#line 1426
                            }

#line 1421
                            break;
                        }

#line 1421
                        break;
                    }

#line 1421
                    break;
                }

#line 1420
                break;
            }

#line 1420
            break;
        }

#line 1420
        for(;;)
        {

#line 1420
            for(;;)
            {

#line 1420
                for(;;)
                {

#line 1420
                    for(;;)
                    {

#line 1421
                        for(;;)
                        {

#line 1422
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1422
                            m_2 = 0U;
                            for(;;)
                            {

#line 1423
                                if(m_2 < 16U)
                                {
                                }
                                else
                                {

#line 1423
                                    break;
                                }

#line 1424
                                (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + m_2 * 16U + tid_1] = (uint(as_type<ushort>((*im_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[m_2].y)) << 16U);

#line 1423
                                m_2 = m_2 + 1U;

#line 1423
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            if(_S64)
                            {

#line 1427
                                if(_S97 >= 0U)
                                {

#line 1427
                                    _S65 = _S97 < 16U;

#line 1427
                                }
                                else
                                {

#line 1427
                                    _S65 = false;

#line 1427
                                }

#line 1427
                                if(_S65)
                                {

#line 1428
                                    vA_0[1U] = (as_type<half>((ushort)(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S97 * 16U + _S96]))));

#line 1427
                                }

                                if(_S99 >= 0U)
                                {

#line 1429
                                    _S65 = _S99 < 16U;

#line 1429
                                }
                                else
                                {

#line 1429
                                    _S65 = false;

#line 1429
                                }

#line 1429
                                if(_S65)
                                {

#line 1430
                                    vB_0[1U] = (as_type<half>((ushort)((((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S99 * 16U + _S98]) >> 16U))));

#line 1429
                                }

#line 1426
                            }

#line 1421
                            break;
                        }

#line 1421
                        break;
                    }

#line 1421
                    break;
                }

#line 1420
                break;
            }

#line 1420
            break;
        }

#line 1420
        break;
    }

#line 1434
    if(_S64)
    {

#line 1434
        _S65 = pairA_1 != 4294967295U;

#line 1434
    }
    else
    {

#line 1434
        _S65 = false;

#line 1434
    }

#line 1434
    int _S101;

#line 1434
    float2 _S102;

#line 1434
    if(_S65)
    {

#line 1435
        int device* _S103 = peakIdx_1+pairA_1;

#line 1435
        if(hitA_1)
        {

#line 1435
            _S101 = int(slotToIndex_0(slotA_0));

#line 1435
        }
        else
        {

#line 1435
            _S101 = int(-1);

#line 1435
        }

#line 1435
        *_S103 = _S101;

#line 1435
        packed_float2 device* _S104 = peakVal_1+pairA_1;
        if(infA_1)
        {

#line 1436
            _S102 = float2(3.40282306073709653e+38f, 0.0f);

#line 1436
        }
        else
        {

#line 1437
            if(hitA_1)
            {

#line 1437
                float2 _S105 = c16Bound_0(float2(vA_0[int(0)], vA_0[int(1)]), enA_0);

#line 1437
                _S102 = _S105;

#line 1437
            }
            else
            {

#line 1437
                _S102 = float2(0.0f, 0.0f);

#line 1437
            }

#line 1436
        }

#line 1436
        *_S104 = packed_float2(_S102) ;

#line 1434
    }

#line 1439
    if(_S64)
    {

#line 1439
        hitA_1 = pairB_1 != 4294967295U;

#line 1439
    }
    else
    {

#line 1439
        hitA_1 = false;

#line 1439
    }

#line 1439
    if(hitA_1)
    {

#line 1440
        int device* _S106 = peakIdx_1+pairB_1;

#line 1440
        if(hitB_1)
        {

#line 1440
            _S101 = int(slotToIndex_0(slotB_0));

#line 1440
        }
        else
        {

#line 1440
            _S101 = int(-1);

#line 1440
        }

#line 1440
        *_S106 = _S101;

#line 1440
        packed_float2 device* _S107 = peakVal_1+pairB_1;
        if(infB_1)
        {

#line 1441
            _S102 = float2(3.40282306073709653e+38f, 0.0f);

#line 1441
        }
        else
        {

#line 1442
            if(hitB_1)
            {

#line 1442
                float2 _S108 = c16Bound_0(float2(vB_0[int(0)], vB_0[int(1)]), enB_0);

#line 1442
                _S102 = _S108;

#line 1442
            }
            else
            {

#line 1442
                _S102 = float2(0.0f, 0.0f);

#line 1442
            }

#line 1441
        }

#line 1441
        *_S107 = packed_float2(_S102) ;

#line 1439
    }

#line 1444
    return;
}


#line 1515
void filterTwo_0(uint pairA_2, uint pairB_2, uint tA_0, uint tB_0, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* tmpl_0, int device* peakIdx_2, packed_float2 device* peakVal_2, uint winStart_4, uint winEnd_4, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{



    thread array<half2, int(16)> re_9;

#line 1520
    thread array<half2, int(16)> im_9;

#line 1520
    uint n2_0 = 0U;
    for(;;)
    {

#line 1521
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 1521
            break;
        }

#line 1522
        uint _S109 = 16U * n2_0;

#line 1522
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 256U + tid_2 + _S109);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 256U + tid_2 + _S109);
        half _S110 = (*dreg_0)[n2_0].x;
        half _S111 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S110, _S110), half2(_S111, _S111), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_9[n2_0], &im_9[n2_0]);

#line 1521
        n2_0 = n2_0 + 1U;

#line 1521
    }

#line 1534
    uint lgTB_0 = firstbithigh_0(16U);
    uint lgLn_0 = firstbithigh_0(256U);
    uint blk_2 = tid_2 >> lgTB_0;
    uint lane_2 = tid_2 & 15U;

    dft16s_0(&re_9, &im_9);

#line 66 "twiddle.slang"
    uint _S112 = mfCoarseTwtFlag_0();

#line 66
    uint k2_3;

#line 1541 "mm_256_fusedTierB_c16p4t8.slang"
    if(_S112 != 0U)
    {

#line 1541
        k2_3 = 0U;

#line 1548
        for(;;)
        {

#line 1548
            if(k2_3 < 16U)
            {
            }
            else
            {

#line 1548
                break;
            }

#line 1549
            uint _S113 = lane_2 * 16U + k2_3;
            cmulw_0(&re_9[k2_3], &im_9[k2_3], as_type<half>(ushort((COARSE_TWT_DATA_0[_S113]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S113]) >> 16U) & 65535U)));

#line 1548
            k2_3 = k2_3 + 1U;

#line 1548
        }

#line 1541
    }
    else
    {

#line 1557
        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 256.0f);
        float _S114 = tw_0.x;

#line 1558
        float _S115 = tw_0.y;

#line 1558
        k2_3 = 0U;

#line 1558
        float cr_0 = 1.0f;

#line 1558
        float ci_0 = 0.0f;

        for(;;)
        {

#line 1560
            if(k2_3 < 16U)
            {
            }
            else
            {

#line 1560
                break;
            }

#line 1561
            cmulw_0(&re_9[k2_3], &im_9[k2_3], half(cr_0), half(ci_0));
            float nr_0 = cr_0 * _S114 - ci_0 * _S115;
            float _S116 = cr_0 * _S115 + ci_0 * _S114;

#line 1560
            k2_3 = k2_3 + 1U;

#line 1560
            cr_0 = nr_0;

#line 1560
            ci_0 = _S116;

#line 1560
        }

#line 1541
    }

#line 1567
    uint per_2 = 16U / max(16U, 1U);
    uint _S117 = max(1U, 1U);
    uint blk2_2 = tid_2 / _S117;

#line 1569
    uint lane2_2 = tid_2 % _S117;

#line 1569
    exchangeS_0(&re_9, &im_9, lgLn_0, lgTB_0, 16U, 256U, blk_2, lane_2, per_2, _S117, 16U, blk2_2, lane2_2, kernelContext_6);


    innermostS_0(&re_9, &im_9);

#line 1591
    if(thrBits_2 != 0U)
    {

#line 1592
        float _S118 = (as_type<float>((thrBits_2)));

#line 1592
        thread array<half2, int(16)> _S119 = re_9;

#line 1592
        thread array<half2, int(16)> _S120 = im_9;

#line 1592
        peakTwoGate_0(pairA_2, pairB_2, tid_2, &_S119, &_S120, peakIdx_2, peakVal_2, winStart_4, winEnd_4, _S118, kernelContext_6);

#line 1591
    }
    else
    {

#line 1591
        thread array<half2, int(16)> _S121 = re_9;

#line 1591
        thread array<half2, int(16)> _S122 = im_9;

#line 1591
        peakTwoWave_0(pairA_2, pairB_2, tid_2, &_S121, &_S122, peakIdx_2, peakVal_2, winStart_4, winEnd_4, thrBits_2, kernelContext_6);

#line 1591
    }

#line 1629
    return;
}


void filterPair_0(uint pair_0, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_3, packed_float2 device* peakVal_3, uint ntmpl_1, uint winStart_5, uint winEnd_5, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, uint device* rowWin_1, KernelContext_0 thread* kernelContext_7)
{

#line 1633
    thread uint _S123 = winStart_5;

#line 1633
    thread uint _S124 = winEnd_5;

#line 1639
    kernelContext_7->_tid_0 = tid_3;

#line 1659
    uint tiles_0 = (ntmpl_1 + 8U - 1U) / 8U;
    uint slots_0 = binsize_1 * tiles_0;
    bool slotOk_0 = pair_0 < slots_0;

#line 1661
    uint q_1;
    if(slotOk_0)
    {

#line 1662
        q_1 = pair_0;

#line 1662
    }
    else
    {

#line 1662
        q_1 = slots_0 - 1U;

#line 1662
    }
    uint d_5 = q_1 / tiles_0;

#line 1663
    uint t0_0 = (q_1 - d_5 * tiles_0) * 8U;
    uint _S125 = d_5 * ntmpl_1 + t0_0;
    rowWindow_0(d_5, &_S123, &_S124, rowWin_1);

#line 1689
    thread array<half2, int(16)> dreg_1;

#line 1689
    uint n2_1 = 0U;

    for(;;)
    {

#line 1691
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1691
            break;
        }

#line 77 "twiddle.slang"
        uint _S126 = mfDataStrideFlag_0();

#line 174 "mm_256_fusedTierB_c16p4t8.slang"
        if(_S126 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S127 = mfDataStrideFlag_0();

#line 77
            q_1 = _S127;

#line 174 "mm_256_fusedTierB_c16p4t8.slang"
        }
        else
        {

#line 174
            q_1 = 256U;

#line 174
        }

#line 1692
        half2 _S128 = dload_0(data_0, d_5 * q_1 + tid_3 + 16U * n2_1);

#line 1692
        dreg_1[n2_1] = _S128;

#line 1691
        n2_1 = n2_1 + 1U;

#line 1691
    }

#line 1691
    uint k_0 = 0U;

#line 1699
    for(;;)
    {

#line 1699
        if(k_0 < 8U)
        {
        }
        else
        {

#line 1699
            break;
        }

#line 1699
        bool okA_0;
        if(slotOk_0)
        {

#line 1700
            okA_0 = (t0_0 + k_0) < ntmpl_1;

#line 1700
        }
        else
        {

#line 1700
            okA_0 = false;

#line 1700
        }

#line 1700
        bool okB_0;

#line 1700
        if(slotOk_0)
        {

#line 1700
            okB_0 = (t0_0 + k_0 + 1U) < ntmpl_1;

#line 1700
        }
        else
        {

#line 1700
            okB_0 = false;

#line 1700
        }
        if(okA_0)
        {

#line 1701
            q_1 = _S125 + k_0;

#line 1701
        }
        else
        {

#line 1701
            q_1 = 4294967295U;

#line 1701
        }

#line 1701
        if(okB_0)
        {

#line 1701
            n2_1 = _S125 + k_0 + 1U;

#line 1701
        }
        else
        {

#line 1701
            n2_1 = 4294967295U;

#line 1701
        }
        uint _S129 = t0_0 + k_0;

#line 1702
        uint _S130 = ntmpl_1 - 1U;

#line 1702
        uint _S131 = min(_S129, _S130);

#line 1702
        uint _S132 = min(_S129 + 1U, _S130);

#line 1702
        thread array<half2, int(16)> _S133 = dreg_1;

#line 1702
        filterTwo_0(q_1, n2_1, _S131, _S132, tid_3, &_S133, tmpl_1, peakIdx_3, peakVal_3, _S123, _S124, thrBits_3, kernelContext_7);

#line 1699
        k_0 = k_0 + 2U;

#line 1699
    }

#line 1715
    return;
}


#line 1728
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], uint _builtinWaveLaneIndex_0 [[thread_index_in_simdgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1728
    thread KernelContext_0 kernelContext_8;

#line 1728
    (&kernelContext_8)->entryPointParams_0 = entryPointParams_1;

#line 1728
    (&kernelContext_8)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1728
    (&kernelContext_8)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1728
    (&kernelContext_8)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1728
    (&kernelContext_8)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1728
    (&kernelContext_8)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1728
    threadgroup array<uint, int(1024)> stg_1;

#line 1728
    (&kernelContext_8)->stg_0 = &stg_1;

#line 1728
    (&kernelContext_8)->_S20 = _builtinWaveLaneIndex_0;

#line 1748
    uint _S134 = lid_0.x;

#line 1748
    uint _sub_0 = _S134 / 16U;
    uint _pr_0 = gid_0.x * 4U + _sub_0;

#line 1749
    uint _t_0 = _S134 % 16U;
    (&kernelContext_8)->_stgBase_0 = _sub_0 * 256U;

#line 1750
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, entryPointParams_rowWin_1, &kernelContext_8);

#line 1761
    return;
}
