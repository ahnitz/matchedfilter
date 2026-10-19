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

#line 11 "mm_128_fusedTierB_c16.slang"
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


#line 210 "mm_128_fusedTierB_c16.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0, uint device* rowWin_0)
{

#line 104 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 212 "mm_128_fusedTierB_c16.slang"
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


#line 167 "mm_128_fusedTierB_c16.slang"
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

#line 236 "mm_128_fusedTierB_c16.slang"
    if(_S7 != 0U)
    {

#line 85 "twiddle.slang"
        uint _S8 = mfDataScaleFlag_0();

#line 237 "mm_128_fusedTierB_c16.slang"
        float s_0 = (as_type<float>((_S8)));
        uint _S9 = 2U * i_1;

#line 238
        return half2(half((as_type<float>((b_1[_S9]))) * s_0), half((as_type<float>((b_1[_S9 + 1U]))) * s_0));
    }
    return cload_0(b_1, i_1);
}


#line 302
half2 cmulConj_0(half2 a_0, half2 b_2)
{

#line 302
    half _S10 = a_0.x;

#line 302
    half _S11 = b_2.x;

#line 302
    half _S12 = a_0.y;

#line 302
    half _S13 = b_2.y;

#line 302
    return half2(_S10 * _S11 + _S12 * _S13, _S12 * _S11 - _S10 * _S13);
}


#line 507
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 509
    half2 t1_0 = *a_1 - *c_0;

#line 509
    half2 t2_0 = *b_3 + *d_1;

#line 509
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 511
    *b_3 = t1_0 + j3_0;

#line 511
    *c_0 = t0_0 - t2_0;

#line 511
    *d_1 = t1_0 - j3_0;
    return;
}


#line 301
half2 cmul_0(half2 a_2, half2 b_4)
{

#line 301
    half _S14 = a_2.x;

#line 301
    half _S15 = b_4.x;

#line 301
    half _S16 = a_2.y;

#line 301
    half _S17 = b_4.y;

#line 301
    return half2(_S14 * _S15 - _S16 * _S17, _S14 * _S17 + _S16 * _S15);
}


#line 543
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125h, 0.382568359375h);
    half2 W2_0 = half2(0.70703125h, 0.70703125h);
    half2 W3_0 = half2(0.382568359375h, 0.923828125h);
    half2 W4_0 = half2(0.0h, 1.0h);
    half2 W6_0 = half2(-0.70703125h, 0.70703125h);
    half2 W9_0 = half2(-0.923828125h, -0.382568359375h);

#line 550
    uint n1_0 = 0U;
    for(;;)
    {

#line 551
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 551
            break;
        }

#line 551
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 551
        n1_0 = n1_0 + 1U;

#line 551
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 552
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 552
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 553
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 553
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 554
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 554
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 554
    uint k2_0 = 0U;
    for(;;)
    {

#line 555
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 555
            break;
        }

#line 555
        uint _S18 = 4U * k2_0;

#line 555
        r4_0(&(*r_0)[_S18], &(*r_0)[_S18 + 1U], &(*r_0)[_S18 + 2U], &(*r_0)[_S18 + 3U]);

#line 555
        k2_0 = k2_0 + 1U;

#line 555
    }

    half2 t_0 = (*r_0)[int(1)];

#line 557
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 557
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 558
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 558
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 559
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 559
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 560
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 560
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 561
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 561
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 562
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 562
    (*r_0)[int(14)] = t_5;
    return;
}


#line 61 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S19 = ((MF_COARSE_TWT));

#line 64
    return _S19;
}


#line 88
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S20 = ((MF_ACCURATE_TRIG));

#line 91
    return _S20;
}


#line 127
float2 mfTwiddle_0(float angle_0)
{

#line 93
    uint _S21 = mfAccurateTrigFlag_0();

#line 129
    if(_S21 == 0U)
    {

#line 130
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S22 = float(quadrant_0);
    float x_0 = angle_0 - _S22 * 1.57079625129699707f - _S22 * 7.54978941586159635e-08f;
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


#line 303 "mm_128_fusedTierB_c16.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S23 = max(TB_0, 1U);

#line 305
    uint j_0 = d_2 / _S23;

#line 305
    uint m_0 = d_2 % _S23;

#line 305
    uint _S24;
    if(TB_0 <= 16U)
    {

#line 306
        _S24 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 306
    }
    else
    {

#line 306
        _S24 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 306
    }

#line 306
    return _S24;
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


#line 271 "mm_128_fusedTierB_c16.slang"
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
    array<uint, int(128)> threadgroup* stg_0;
};


#line 279
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


#line 732
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 733
    uint j_1;

#line 744
    thread array<half2, int(16)> out_0;

#line 744
    uint z_1 = 0U;
    for(;;)
    {

#line 745
        if(z_1 < 16U)
        {
        }
        else
        {

#line 745
            break;
        }

#line 745
        out_0[z_1] = half2(0.0h, 0.0h);

#line 745
        z_1 = z_1 + 1U;

#line 745
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S25 = p0_0 & lenMask_0;

#line 751
    uint _S26 = (_S25 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S25 & spanMask_0);

#line 751
    uint c_2 = 0U;

    for(;;)
    {

#line 753
        if(c_2 < 1U)
        {
        }
        else
        {

#line 753
            break;
        }

#line 754
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 754
        j_1 = 0U;
        for(;;)
        {

#line 755
            if(j_1 < 16U)
            {
            }
            else
            {

#line 755
                break;
            }

#line 755
            stgPut_0(j_1 * 8U + kernelContext_2->_tid_0, (*r_1)[c_2 * 16U + j_1], kernelContext_2);

#line 755
            j_1 = j_1 + 1U;

#line 755
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 756
        uint d_3 = 0U;
        for(;;)
        {

#line 757
            if(d_3 < 16U)
            {
            }
            else
            {

#line 757
                break;
            }

#line 758
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S27 = pz_0 & lenMask_0;
            uint az_0 = (_S27 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S27 & spanMask_0);

#line 760
            half2 _S28 = stgGet_0(_S26 + az_0 - c_2 * 16U * 8U, kernelContext_2);


            out_0[d_3] = _S28;

#line 757
            d_3 = d_3 + 1U;

#line 757
        }

#line 753
        c_2 = c_2 + 1U;

#line 753
    }

#line 753
    j_1 = 0U;

#line 766
    for(;;)
    {

#line 766
        if(j_1 < 16U)
        {
        }
        else
        {

#line 766
            break;
        }

#line 766
        (*r_1)[j_1] = out_0[j_1];

#line 766
        j_1 = j_1 + 1U;

#line 766
    }
    return;
}


#line 527
void dft8_0(array<half2, int(16)> thread* r_2, uint o_0)
{


    thread array<half2, int(8)> b_5;

#line 531
    uint s_2 = 1U;
    for(;;)
    {

#line 532
        if(s_2 < 8U)
        {
        }
        else
        {

#line 532
            break;
        }

#line 532
        uint j_2 = 0U;
        for(;;)
        {

#line 533
            if(j_2 < 4U)
            {
            }
            else
            {

#line 533
                break;
            }

#line 534
            uint k_0 = j_2 & (s_2 - 1U);

#line 534
            uint base_0 = (j_2 - k_0) << 1U;

            float2 _S29 = mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_2));
            uint _S30 = o_0 + j_2;

#line 537
            half2 t_6 = cmul_0(half2(_S29), (*r_2)[_S30 + 4U]);
            uint _S31 = base_0 + k_0;

#line 538
            b_5[_S31] = (*r_2)[_S30] + t_6;

#line 538
            b_5[_S31 + s_2] = (*r_2)[_S30] - t_6;

#line 533
            j_2 = j_2 + 1U;

#line 533
        }

#line 533
        uint i_4 = 0U;

#line 540
        for(;;)
        {

#line 540
            if(i_4 < 8U)
            {
            }
            else
            {

#line 540
                break;
            }

#line 540
            (*r_2)[o_0 + i_4] = b_5[i_4];

#line 540
            i_4 = i_4 + 1U;

#line 540
        }

#line 532
        s_2 = s_2 << 1U;

#line 532
    }

#line 542
    return;
}


#line 646
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 646
    uint b_6 = 0U;

#line 654
    for(;;)
    {

#line 654
        if(b_6 < 2U)
        {
        }
        else
        {

#line 654
            break;
        }

#line 654
        dft8_0(r_3, b_6 * 8U);

#line 654
        b_6 = b_6 + 1U;

#line 654
    }



    return;
}


#line 834
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 11 "fft_transform.slang"
    uint lgTB_0 = firstbithigh_0(8U);
    uint lgLn_0 = firstbithigh_0(128U);
    uint blk_2 = tid_0 >> lgTB_0;
    uint lane_2 = tid_0 & 7U;


    dft16_0(r_4);

#line 66 "twiddle.slang"
    uint _S32 = mfCoarseTwtFlag_0();

#line 66
    uint k2_1;

#line 27 "fft_transform.slang"
    if(_S32 != 0U)
    {

#line 27
        k2_1 = 0U;


        for(;;)
        {

#line 30
            if(k2_1 < 16U)
            {
            }
            else
            {

#line 30
                break;
            }

#line 31
            uint _S33 = lane_2 * 16U + k2_1;

#line 31
            (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(as_type<half>(ushort((COARSE_TWT_DATA_0[_S33]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S33]) >> 16U) & 65535U))));

#line 30
            k2_1 = k2_1 + 1U;

#line 30
        }

#line 27
    }
    else
    {

#line 39
        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 128.0f);
        float _S34 = tw_0.x;

#line 40
        float _S35 = tw_0.y;

#line 40
        k2_1 = 0U;

#line 40
        float cr_0 = 1.0f;

#line 40
        float ci_0 = 0.0f;

        for(;;)
        {

#line 42
            if(k2_1 < 16U)
            {
            }
            else
            {

#line 42
                break;
            }

#line 43
            (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(half(cr_0), half(ci_0)));
            float nr_0 = cr_0 * _S34 - ci_0 * _S35;
            float _S36 = cr_0 * _S35 + ci_0 * _S34;

#line 42
            k2_1 = k2_1 + 1U;

#line 42
            cr_0 = nr_0;

#line 42
            ci_0 = _S36;

#line 42
        }

#line 27
    }

#line 50
    uint per_2 = 16U / max(8U, 1U);
    uint _S37 = max(0U, 1U);
    uint blk2_2 = tid_0 / _S37;

#line 52
    uint lane2_2 = tid_0 % _S37;

#line 52
    exchange_0(r_4, lgLn_0, lgTB_0, 8U, 128U, blk_2, lane_2, per_2, _S37, 8U, blk2_2, lane2_2, kernelContext_3);



    innermost_0(r_4);

#line 837 "mm_128_fusedTierB_c16.slang"
    return;
}


#line 342
float pairSum_0(uint tid_1, float v_1, KernelContext_0 thread* kernelContext_4)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_1] = (as_type<uint>((v_1)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 346
    uint k_1 = 0U;

#line 346
    float t_7 = 0.0f;

    for(;;)
    {

#line 348
        if(k_1 < 8U)
        {
        }
        else
        {

#line 348
            break;
        }

#line 348
        float t_8 = t_7 + (as_type<float>(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_1])));

#line 348
        k_1 = k_1 + 1U;

#line 348
        t_7 = t_8;

#line 348
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_7;
}


#line 791
uint lgOf_0(uint i_5)
{

#line 791
    uint _S38;

#line 791
    if(i_5 < 1U)
    {

#line 791
        _S38 = 4U;

#line 791
    }
    else
    {

#line 791
        if(i_5 == 1U)
        {

#line 791
            _S38 = 3U;

#line 791
        }
        else
        {

#line 791
            _S38 = 1U;

#line 791
        }

#line 791
    }

#line 791
    return _S38;
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



uint c16Mag_0(half2 v_2, uint slot_1, uint ws_0, uint we_0, bool ov_0)
{
    uint idx_0 = slotToIndex_0(slot_1);

#line 809
    bool live_0;
    if(idx_0 >= ws_0)
    {

#line 810
        live_0 = idx_0 < we_0;

#line 810
    }
    else
    {

#line 810
        live_0 = false;

#line 810
    }
    float x_1 = float(v_2.x);

#line 811
    float y_0 = float(v_2.y);

#line 811
    uint m_1;
    if(live_0)
    {

#line 812
        m_1 = (as_type<uint>((x_1 * x_1 + y_0 * y_0)));

#line 812
    }
    else
    {

#line 812
        m_1 = 0U;

#line 812
    }
    if(ov_0)
    {
    }
    else
    {

#line 813
        live_0 = false;

#line 813
    }

#line 813
    if(live_0)
    {

#line 813
        m_1 = 2139095040U;

#line 813
    }

#line 813
    return m_1;
}


#line 110 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S39 = ((MF_C16_RAW));

#line 113
    return _S39;
}


#line 332 "mm_128_fusedTierB_c16.slang"
float2 c16Bound_0(float2 v_3, float energy_0)
{

#line 115 "twiddle.slang"
    uint _S40 = mfC16RawFlag_0();

#line 334 "mm_128_fusedTierB_c16.slang"
    if((1U - _S40) == 0U)
    {

#line 334
        return v_3;
    }

#line 335
    float m_2 = length(v_3);
    float b_7 = m_2 * 1.00146484375f + 0.00583916017785668f * sqrt(energy_0);

#line 336
    float2 _S41;
    if(m_2 > 0.0f)
    {

#line 337
        _S41 = v_3 * float2((b_7 / m_2)) ;

#line 337
    }
    else
    {

#line 337
        _S41 = float2(b_7, 0.0f);

#line 337
    }

#line 337
    return _S41;
}


#line 843
void filterOne_0(uint pair_0, uint d_4, uint t_9, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{

#line 883
    thread array<half2, int(16)> r_5;

#line 883
    uint n2_0 = 0U;



    for(;;)
    {

#line 887
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 887
            break;
        }

#line 888
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_9 * 128U + tid_2 + 8U * n2_0));

#line 887
        n2_0 = n2_0 + 1U;

#line 887
    }

#line 887
    transform_0(&r_5, tid_2, kernelContext_5);

#line 887
    uint i_6 = 0U;

#line 887
    float energy_1 = 0.0f;

#line 917
    for(;;)
    {

#line 917
        if(i_6 < 16U)
        {
        }
        else
        {

#line 917
            break;
        }

#line 918
        float _ex_0 = float(r_5[i_6].x);

#line 918
        float _ey_0 = float(r_5[i_6].y);
        float energy_2 = energy_1 + (_ex_0 * _ex_0 + _ey_0 * _ey_0);

#line 917
        i_6 = i_6 + 1U;

#line 917
        energy_1 = energy_2;

#line 917
    }

#line 917
    float _S42 = pairSum_0(tid_2, energy_1, kernelContext_5);



    float energy_3 = _S42 / 128.0f;

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1033
    bool _S43 = tid_2 == 0U;

#line 1033
    if(_S43)
    {

#line 1033
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 1033
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 1033
    }

#line 1038
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1038
    i_6 = 0U;

#line 1038
    uint ovAcc_0 = 0U;

#line 1052
    for(;;)
    {

#line 1052
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1052
            break;
        }

#line 1053
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_6][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_6][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1052
        i_6 = i_6 + 1U;

#line 1052
        ovAcc_0 = ovAcc_1;

#line 1052
    }

    bool _S44 = (ovAcc_0 & 2147516416U) != 0U;

#line 1060
    half2 _S45 = half2(0.0h, 0.0h);

#line 1060
    uint bestBits_0 = thrBits_1;

#line 1060
    uint bestSlot_0 = 4294967295U;

#line 1060
    half2 bestV_0 = _S45;

#line 1060
    i_6 = 0U;
    for(;;)
    {

#line 1061
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1061
            break;
        }

#line 1062
        uint _S46 = tid_2 * 16U + i_6;

#line 1062
        uint m_3 = c16Mag_0(r_5[i_6], _S46, winStart_2, winEnd_2, _S44);
        if(m_3 > bestBits_0)
        {

#line 1063
            bestBits_0 = m_3;

#line 1063
            bestSlot_0 = _S46;

#line 1063
            bestV_0 = r_5[i_6];

#line 1063
        }

#line 1061
        i_6 = i_6 + 1U;

#line 1061
    }

#line 1066
    uint wm_0 = simd_max(bestBits_0);
    bool _S47 = simd_is_first();

#line 1067
    bool _S48;

#line 1067
    if(_S47)
    {

#line 1067
        _S48 = wm_0 > thrBits_1;

#line 1067
    }
    else
    {

#line 1067
        _S48 = false;

#line 1067
    }

#line 1067
    if(_S48)
    {

#line 1067
        uint _S49 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1067
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);

    uint best_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];
    if(bestSlot_0 != 4294967295U)
    {

#line 1074
        _S48 = bestBits_0 == best_0;

#line 1074
    }
    else
    {

#line 1074
        _S48 = false;

#line 1074
    }

#line 1074
    uint winner_0;

#line 1074
    if(_S48)
    {

#line 1074
        winner_0 = bestSlot_0;

#line 1074
    }
    else
    {

#line 1074
        winner_0 = 4294967295U;

#line 1074
    }

    uint waveWinner_0 = simd_min(winner_0);
    bool _S50 = simd_is_first();

#line 1077
    if(_S50)
    {

#line 1077
        _S48 = waveWinner_0 != 4294967295U;

#line 1077
    }
    else
    {

#line 1077
        _S48 = false;

#line 1077
    }

#line 1077
    if(_S48)
    {

#line 1078
        uint _S51 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1077
    }

#line 1082
    threadgroup_barrier(mem_flags::mem_threadgroup);
    uint wslot_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U];

    bool _S52 = pair_0 != 4294967295U;

#line 1085
    if(_S52)
    {

#line 1085
        _S48 = winner_0 != 4294967295U;

#line 1085
    }
    else
    {

#line 1085
        _S48 = false;

#line 1085
    }

#line 1085
    if(_S48)
    {

#line 1085
        _S48 = winner_0 == wslot_0;

#line 1085
    }
    else
    {

#line 1085
        _S48 = false;

#line 1085
    }

#line 1085
    if(_S48)
    {

#line 1086
        *(peakIdx_0+pair_0) = int(slotToIndex_0(wslot_0));

#line 1086
        packed_float2 device* _S53 = peakVal_0+pair_0;
        float2 _S54 = c16Bound_0(float2(float(bestV_0.x), float(bestV_0.y)), energy_3);

#line 1087
        *_S53 = packed_float2(_S54) ;

#line 1085
    }



    if(_S52)
    {

#line 1089
        _S48 = _S43;

#line 1089
    }
    else
    {

#line 1089
        _S48 = false;

#line 1089
    }

#line 1089
    if(_S48)
    {

#line 1089
        _S48 = wslot_0 == 4294967295U;

#line 1089
    }
    else
    {

#line 1089
        _S48 = false;

#line 1089
    }

#line 1089
    if(_S48)
    {

#line 1090
        *(peakIdx_0+pair_0) = int(-1);

#line 1090
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1089
    }

#line 1237
    return;
}


#line 1633
void filterPair_0(uint pair_1, uint tid_3, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, uint device* rowWin_1, KernelContext_0 thread* kernelContext_6)
{

#line 208
    uint k_2;

#line 1633
    thread uint _S55 = winStart_3;

#line 1633
    thread uint _S56 = winEnd_3;

#line 1639
    kernelContext_6->_tid_0 = tid_3;

#line 1681
    uint d_5 = pair_1 / ntmpl_1;

#line 1681
    uint _S57 = pair_1 % ntmpl_1;

#line 1686
    rowWindow_0(d_5, &_S55, &_S56, rowWin_1);


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
        uint _S58 = mfDataStrideFlag_0();

#line 174 "mm_128_fusedTierB_c16.slang"
        if(_S58 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S59 = mfDataStrideFlag_0();

#line 77
            k_2 = _S59;

#line 174 "mm_128_fusedTierB_c16.slang"
        }
        else
        {

#line 174
            k_2 = 128U;

#line 174
        }

#line 1692
        half2 _S60 = dload_0(data_1, d_5 * k_2 + tid_3 + 8U * n2_1);

#line 1692
        dreg_1[n2_1] = _S60;

#line 1691
        n2_1 = n2_1 + 1U;

#line 1691
    }

#line 1691
    k_2 = 0U;

#line 1711
    for(;;)
    {

#line 1711
        if(k_2 < 1U)
        {
        }
        else
        {

#line 1711
            break;
        }

#line 1712
        uint _S61 = pair_1 + k_2;

#line 1712
        uint _S62 = _S57 + k_2;

#line 1712
        thread array<half2, int(16)> _S63 = dreg_1;

#line 1712
        filterOne_0(_S61, d_5, _S62, tid_3, &_S63, data_1, tmpl_1, peakIdx_1, peakVal_1, _S55, _S56, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1711
        k_2 = k_2 + 1U;

#line 1711
    }



    return;
}


#line 1728
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1728
    thread KernelContext_0 kernelContext_7;

#line 1728
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1728
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1728
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1728
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1728
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1728
    (&kernelContext_7)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1728
    threadgroup array<uint, int(128)> stg_1;

#line 1728
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1745
    uint _pr_0 = gid_0.x;

#line 1745
    uint _t_0 = lid_0.x;
    (&kernelContext_7)->_stgBase_0 = 0U;

#line 1746
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, entryPointParams_rowWin_1, &kernelContext_7);

#line 1761
    return;
}
