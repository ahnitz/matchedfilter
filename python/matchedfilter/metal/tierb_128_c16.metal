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


#line 295 "mm_128_fusedTierB_c16.slang"
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
    array<uint, int(128)> threadgroup* stg_0;
};


#line 230
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 104 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 233 "mm_128_fusedTierB_c16.slang"
    if(_S3 == 0U)
    {

#line 233
        return;
    }

#line 234
    uint _S4 = 3U * d_0;

#line 234
    *winStart_1 = rowWin_0[_S4];
    *winEnd_1 = rowWin_0[_S4 + 1U];
    kernelContext_0->_binPhase_0 = rowWin_0[_S4 + 2U];
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


#line 172 "mm_128_fusedTierB_c16.slang"
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
    uint _S7 = mfDataStrideFlag_0();

#line 260 "mm_128_fusedTierB_c16.slang"
    if(_S7 != 0U)
    {

#line 85 "twiddle.slang"
        uint _S8 = mfDataScaleFlag_0();

#line 261 "mm_128_fusedTierB_c16.slang"
        float s_0 = (as_type<float>((_S8)));
        uint _S9 = 2U * i_1;

#line 262
        return half2(half((as_type<float>((b_1[_S9]))) * s_0), half((as_type<float>((b_1[_S9 + 1U]))) * s_0));
    }
    return cload_0(b_1, i_1);
}


#line 326
half2 cmulConj_0(half2 a_0, half2 b_2)
{

#line 326
    half _S10 = a_0.x;

#line 326
    half _S11 = b_2.x;

#line 326
    half _S12 = a_0.y;

#line 326
    half _S13 = b_2.y;

#line 326
    return half2(_S10 * _S11 + _S12 * _S13, _S12 * _S11 - _S10 * _S13);
}


#line 531
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 533
    half2 t1_0 = *a_1 - *c_0;

#line 533
    half2 t2_0 = *b_3 + *d_1;

#line 533
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 535
    *b_3 = t1_0 + j3_0;

#line 535
    *c_0 = t0_0 - t2_0;

#line 535
    *d_1 = t1_0 - j3_0;
    return;
}


#line 325
half2 cmul_0(half2 a_2, half2 b_4)
{

#line 325
    half _S14 = a_2.x;

#line 325
    half _S15 = b_4.x;

#line 325
    half _S16 = a_2.y;

#line 325
    half _S17 = b_4.y;

#line 325
    return half2(_S14 * _S15 - _S16 * _S17, _S14 * _S17 + _S16 * _S15);
}


#line 567
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125h, 0.382568359375h);
    half2 W2_0 = half2(0.70703125h, 0.70703125h);
    half2 W3_0 = half2(0.382568359375h, 0.923828125h);
    half2 W4_0 = half2(0.0h, 1.0h);
    half2 W6_0 = half2(-0.70703125h, 0.70703125h);
    half2 W9_0 = half2(-0.923828125h, -0.382568359375h);

#line 574
    uint n1_0 = 0U;
    for(;;)
    {

#line 575
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 575
            break;
        }

#line 575
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 575
        n1_0 = n1_0 + 1U;

#line 575
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 576
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 576
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 577
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 577
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 578
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 578
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 578
    uint k2_0 = 0U;
    for(;;)
    {

#line 579
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 579
            break;
        }

#line 579
        uint _S18 = 4U * k2_0;

#line 579
        r4_0(&(*r_0)[_S18], &(*r_0)[_S18 + 1U], &(*r_0)[_S18 + 2U], &(*r_0)[_S18 + 3U]);

#line 579
        k2_0 = k2_0 + 1U;

#line 579
    }

    half2 t_0 = (*r_0)[int(1)];

#line 581
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 581
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 582
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 582
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 583
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 583
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 584
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 584
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 585
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 585
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 586
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 586
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


#line 327 "mm_128_fusedTierB_c16.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S23 = max(TB_0, 1U);

#line 329
    uint j_0 = d_2 / _S23;

#line 329
    uint m_0 = d_2 % _S23;

#line 329
    uint _S24;
    if(TB_0 <= 16U)
    {

#line 330
        _S24 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 330
    }
    else
    {

#line 330
        _S24 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 330
    }

#line 330
    return _S24;
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


#line 756
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_3)
{

#line 757
    uint j_1;

#line 768
    thread array<half2, int(16)> out_0;

#line 768
    uint z_1 = 0U;
    for(;;)
    {

#line 769
        if(z_1 < 16U)
        {
        }
        else
        {

#line 769
            break;
        }

#line 769
        out_0[z_1] = half2(0.0h, 0.0h);

#line 769
        z_1 = z_1 + 1U;

#line 769
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S25 = p0_0 & lenMask_0;

#line 775
    uint _S26 = (_S25 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S25 & spanMask_0);

#line 775
    uint c_2 = 0U;

    for(;;)
    {

#line 777
        if(c_2 < 1U)
        {
        }
        else
        {

#line 777
            break;
        }

#line 778
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 778
        j_1 = 0U;
        for(;;)
        {

#line 779
            if(j_1 < 16U)
            {
            }
            else
            {

#line 779
                break;
            }

#line 779
            stgPut_0(j_1 * 8U + kernelContext_3->_tid_0, (*r_1)[c_2 * 16U + j_1], kernelContext_3);

#line 779
            j_1 = j_1 + 1U;

#line 779
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 780
        uint d_3 = 0U;
        for(;;)
        {

#line 781
            if(d_3 < 16U)
            {
            }
            else
            {

#line 781
                break;
            }

#line 782
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S27 = pz_0 & lenMask_0;
            uint az_0 = (_S27 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S27 & spanMask_0);

#line 784
            half2 _S28 = stgGet_0(_S26 + az_0 - c_2 * 16U * 8U, kernelContext_3);


            out_0[d_3] = _S28;

#line 781
            d_3 = d_3 + 1U;

#line 781
        }

#line 777
        c_2 = c_2 + 1U;

#line 777
    }

#line 777
    j_1 = 0U;

#line 790
    for(;;)
    {

#line 790
        if(j_1 < 16U)
        {
        }
        else
        {

#line 790
            break;
        }

#line 790
        (*r_1)[j_1] = out_0[j_1];

#line 790
        j_1 = j_1 + 1U;

#line 790
    }
    return;
}


#line 551
void dft8_0(array<half2, int(16)> thread* r_2, uint o_0)
{


    thread array<half2, int(8)> b_5;

#line 555
    uint s_2 = 1U;
    for(;;)
    {

#line 556
        if(s_2 < 8U)
        {
        }
        else
        {

#line 556
            break;
        }

#line 556
        uint j_2 = 0U;
        for(;;)
        {

#line 557
            if(j_2 < 4U)
            {
            }
            else
            {

#line 557
                break;
            }

#line 558
            uint k_0 = j_2 & (s_2 - 1U);

#line 558
            uint base_0 = (j_2 - k_0) << 1U;

            float2 _S29 = mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_2));
            uint _S30 = o_0 + j_2;

#line 561
            half2 t_6 = cmul_0(half2(_S29), (*r_2)[_S30 + 4U]);
            uint _S31 = base_0 + k_0;

#line 562
            b_5[_S31] = (*r_2)[_S30] + t_6;

#line 562
            b_5[_S31 + s_2] = (*r_2)[_S30] - t_6;

#line 557
            j_2 = j_2 + 1U;

#line 557
        }

#line 557
        uint i_4 = 0U;

#line 564
        for(;;)
        {

#line 564
            if(i_4 < 8U)
            {
            }
            else
            {

#line 564
                break;
            }

#line 564
            (*r_2)[o_0 + i_4] = b_5[i_4];

#line 564
            i_4 = i_4 + 1U;

#line 564
        }

#line 556
        s_2 = s_2 << 1U;

#line 556
    }

#line 566
    return;
}


#line 670
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 670
    uint b_6 = 0U;

#line 678
    for(;;)
    {

#line 678
        if(b_6 < 2U)
        {
        }
        else
        {

#line 678
            break;
        }

#line 678
        dft8_0(r_3, b_6 * 8U);

#line 678
        b_6 = b_6 + 1U;

#line 678
    }



    return;
}


#line 858
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_4)
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
    exchange_0(r_4, lgLn_0, lgTB_0, 8U, 128U, blk_2, lane_2, per_2, _S37, 8U, blk2_2, lane2_2, kernelContext_4);



    innermost_0(r_4);

#line 861 "mm_128_fusedTierB_c16.slang"
    return;
}


#line 366
float pairSum_0(uint tid_1, float v_1, KernelContext_0 thread* kernelContext_5)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + tid_1] = (as_type<uint>((v_1)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 370
    uint k_1 = 0U;

#line 370
    float t_7 = 0.0f;

    for(;;)
    {

#line 372
        if(k_1 < 8U)
        {
        }
        else
        {

#line 372
            break;
        }

#line 372
        float t_8 = t_7 + (as_type<float>(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + k_1])));

#line 372
        k_1 = k_1 + 1U;

#line 372
        t_7 = t_8;

#line 372
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_7;
}


#line 815
uint lgOf_0(uint i_5)
{

#line 815
    uint _S38;

#line 815
    if(i_5 < 1U)
    {

#line 815
        _S38 = 4U;

#line 815
    }
    else
    {

#line 815
        if(i_5 == 1U)
        {

#line 815
            _S38 = 3U;

#line 815
        }
        else
        {

#line 815
            _S38 = 1U;

#line 815
        }

#line 815
    }

#line 815
    return _S38;
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



uint c16Mag_0(half2 v_2, uint slot_1, uint ws_0, uint we_0, bool ov_0)
{
    uint idx_0 = slotToIndex_0(slot_1);

#line 833
    bool live_0;
    if(idx_0 >= ws_0)
    {

#line 834
        live_0 = idx_0 < we_0;

#line 834
    }
    else
    {

#line 834
        live_0 = false;

#line 834
    }
    float x_1 = float(v_2.x);

#line 835
    float y_0 = float(v_2.y);

#line 835
    uint m_1;
    if(live_0)
    {

#line 836
        m_1 = (as_type<uint>((x_1 * x_1 + y_0 * y_0)));

#line 836
    }
    else
    {

#line 836
        m_1 = 0U;

#line 836
    }
    if(ov_0)
    {
    }
    else
    {

#line 837
        live_0 = false;

#line 837
    }

#line 837
    if(live_0)
    {

#line 837
        m_1 = 2139095040U;

#line 837
    }

#line 837
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


#line 356 "mm_128_fusedTierB_c16.slang"
float2 c16Bound_0(float2 v_3, float energy_0)
{

#line 115 "twiddle.slang"
    uint _S40 = mfC16RawFlag_0();

#line 358 "mm_128_fusedTierB_c16.slang"
    if((1U - _S40) == 0U)
    {

#line 358
        return v_3;
    }

#line 359
    float m_2 = length(v_3);
    float b_7 = m_2 * 1.00146484375f + 0.00583916017785668f * sqrt(energy_0);

#line 360
    float2 _S41;
    if(m_2 > 0.0f)
    {

#line 361
        _S41 = v_3 * float2((b_7 / m_2)) ;

#line 361
    }
    else
    {

#line 361
        _S41 = float2(b_7, 0.0f);

#line 361
    }

#line 361
    return _S41;
}


#line 867
void filterOne_0(uint pair_0, uint d_4, uint t_9, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_6)
{

#line 908
    thread array<half2, int(16)> r_5;

#line 908
    uint n2_0 = 0U;



    for(;;)
    {

#line 912
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 912
            break;
        }

#line 913
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_9 * 128U + tid_2 + 8U * n2_0));

#line 912
        n2_0 = n2_0 + 1U;

#line 912
    }

#line 912
    transform_0(&r_5, tid_2, kernelContext_6);

#line 912
    uint i_6 = 0U;

#line 912
    float energy_1 = 0.0f;

#line 942
    for(;;)
    {

#line 942
        if(i_6 < 16U)
        {
        }
        else
        {

#line 942
            break;
        }

#line 943
        float _ex_0 = float(r_5[i_6].x);

#line 943
        float _ey_0 = float(r_5[i_6].y);
        float energy_2 = energy_1 + (_ex_0 * _ex_0 + _ey_0 * _ey_0);

#line 942
        i_6 = i_6 + 1U;

#line 942
        energy_1 = energy_2;

#line 942
    }

#line 942
    float _S42 = pairSum_0(tid_2, energy_1, kernelContext_6);



    float energy_3 = _S42 / 128.0f;

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1058
    bool _S43 = tid_2 == 0U;

#line 1058
    if(_S43)
    {

#line 1058
        (*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0] = thrBits_1;

#line 1058
        (*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + 1U] = 4294967295U;

#line 1058
    }

#line 1063
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1063
    i_6 = 0U;

#line 1063
    uint ovAcc_0 = 0U;

#line 1077
    for(;;)
    {

#line 1077
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1077
            break;
        }

#line 1078
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_6][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_6][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1077
        i_6 = i_6 + 1U;

#line 1077
        ovAcc_0 = ovAcc_1;

#line 1077
    }

    bool _S44 = (ovAcc_0 & 2147516416U) != 0U;

#line 1085
    half2 _S45 = half2(0.0h, 0.0h);

#line 1085
    uint bestBits_0 = thrBits_1;

#line 1085
    uint bestSlot_0 = 4294967295U;

#line 1085
    half2 bestV_0 = _S45;

#line 1085
    i_6 = 0U;
    for(;;)
    {

#line 1086
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1086
            break;
        }

#line 1087
        uint _S46 = tid_2 * 16U + i_6;

#line 1087
        uint m_3 = c16Mag_0(r_5[i_6], _S46, winStart_2, winEnd_2, _S44);
        if(m_3 > bestBits_0)
        {

#line 1088
            bestBits_0 = m_3;

#line 1088
            bestSlot_0 = _S46;

#line 1088
            bestV_0 = r_5[i_6];

#line 1088
        }

#line 1086
        i_6 = i_6 + 1U;

#line 1086
    }

#line 1091
    uint wm_0 = simd_max(bestBits_0);
    bool _S47 = simd_is_first();

#line 1092
    bool _S48;

#line 1092
    if(_S47)
    {

#line 1092
        _S48 = wm_0 > thrBits_1;

#line 1092
    }
    else
    {

#line 1092
        _S48 = false;

#line 1092
    }

#line 1092
    if(_S48)
    {

#line 1092
        uint _S49 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1092
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);

    uint best_0 = (*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0];
    if(bestSlot_0 != 4294967295U)
    {

#line 1099
        _S48 = bestBits_0 == best_0;

#line 1099
    }
    else
    {

#line 1099
        _S48 = false;

#line 1099
    }

#line 1099
    uint winner_0;

#line 1099
    if(_S48)
    {

#line 1099
        winner_0 = bestSlot_0;

#line 1099
    }
    else
    {

#line 1099
        winner_0 = 4294967295U;

#line 1099
    }

    uint waveWinner_0 = simd_min(winner_0);
    bool _S50 = simd_is_first();

#line 1102
    if(_S50)
    {

#line 1102
        _S48 = waveWinner_0 != 4294967295U;

#line 1102
    }
    else
    {

#line 1102
        _S48 = false;

#line 1102
    }

#line 1102
    if(_S48)
    {

#line 1103
        uint _S51 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1102
    }

#line 1107
    threadgroup_barrier(mem_flags::mem_threadgroup);
    uint wslot_0 = (*kernelContext_6->stg_0)[kernelContext_6->_stgBase_0 + 1U];

    bool _S52 = pair_0 != 4294967295U;

#line 1110
    if(_S52)
    {

#line 1110
        _S48 = winner_0 != 4294967295U;

#line 1110
    }
    else
    {

#line 1110
        _S48 = false;

#line 1110
    }

#line 1110
    if(_S48)
    {

#line 1110
        _S48 = winner_0 == wslot_0;

#line 1110
    }
    else
    {

#line 1110
        _S48 = false;

#line 1110
    }

#line 1110
    if(_S48)
    {

#line 1111
        *(peakIdx_0+pair_0) = int(slotToIndex_0(wslot_0));

#line 1111
        packed_float2 device* _S53 = peakVal_0+pair_0;
        float2 _S54 = c16Bound_0(float2(float(bestV_0.x), float(bestV_0.y)), energy_3);

#line 1112
        *_S53 = packed_float2(_S54) ;

#line 1110
    }



    if(_S52)
    {

#line 1114
        _S48 = _S43;

#line 1114
    }
    else
    {

#line 1114
        _S48 = false;

#line 1114
    }

#line 1114
    if(_S48)
    {

#line 1114
        _S48 = wslot_0 == 4294967295U;

#line 1114
    }
    else
    {

#line 1114
        _S48 = false;

#line 1114
    }

#line 1114
    if(_S48)
    {

#line 1115
        *(peakIdx_0+pair_0) = int(-1);

#line 1115
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1114
    }

#line 1262
    return;
}


#line 1658
void filterPair_0(uint pair_1, uint tid_3, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, uint device* rowWin_1, KernelContext_0 thread* kernelContext_7)
{

#line 228
    uint k_2;

#line 1658
    thread uint _S55 = winStart_3;

#line 1658
    thread uint _S56 = winEnd_3;

#line 1664
    kernelContext_7->_tid_0 = tid_3;

#line 1706
    uint d_5 = pair_1 / ntmpl_1;

#line 1706
    uint _S57 = pair_1 % ntmpl_1;

#line 1706
    rowWindow_0(d_5, &_S55, &_S56, rowWin_1, kernelContext_7);

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
        uint _S58 = mfDataStrideFlag_0();

#line 179 "mm_128_fusedTierB_c16.slang"
        if(_S58 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S59 = mfDataStrideFlag_0();

#line 77
            k_2 = _S59;

#line 179 "mm_128_fusedTierB_c16.slang"
        }
        else
        {

#line 179
            k_2 = 128U;

#line 179
        }

#line 1717
        half2 _S60 = dload_0(data_1, d_5 * k_2 + tid_3 + 8U * n2_1);

#line 1717
        dreg_1[n2_1] = _S60;

#line 1716
        n2_1 = n2_1 + 1U;

#line 1716
    }

#line 1716
    k_2 = 0U;

#line 1736
    for(;;)
    {

#line 1736
        if(k_2 < 1U)
        {
        }
        else
        {

#line 1736
            break;
        }

#line 1737
        uint _S61 = pair_1 + k_2;

#line 1737
        uint _S62 = _S57 + k_2;

#line 1737
        thread array<half2, int(16)> _S63 = dreg_1;

#line 1737
        filterOne_0(_S61, d_5, _S62, tid_3, &_S63, data_1, tmpl_1, peakIdx_1, peakVal_1, _S55, _S56, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_7);

#line 1736
        k_2 = k_2 + 1U;

#line 1736
    }



    return;
}


#line 1753
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1753
    thread KernelContext_0 kernelContext_8;

#line 1753
    (&kernelContext_8)->entryPointParams_0 = entryPointParams_1;

#line 1753
    (&kernelContext_8)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1753
    (&kernelContext_8)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1753
    (&kernelContext_8)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1753
    (&kernelContext_8)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1753
    (&kernelContext_8)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1753
    threadgroup array<uint, int(128)> stg_1;

#line 1753
    (&kernelContext_8)->stg_0 = &stg_1;

#line 1753
    (&kernelContext_8)->_binPhase_0 = 0U;

#line 1770
    uint _pr_0 = gid_0.x;

#line 1770
    uint _t_0 = lid_0.x;
    (&kernelContext_8)->_stgBase_0 = 0U;

#line 1771
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, entryPointParams_rowWin_1, &kernelContext_8);

#line 1788
    return;
}
