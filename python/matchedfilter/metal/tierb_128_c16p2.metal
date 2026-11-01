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

#line 10 "mm_128_fusedTierB_c16p2.slang"
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


#line 87 "twiddle.slang"
uint mfRowWindowsFlag_0()
{
    ;
    uint _S2 = ((MF_ROW_WINDOWS));

#line 90
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


#line 308 "mm_128_fusedTierB_c16p2.slang"
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
};


#line 229
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 92 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 232 "mm_128_fusedTierB_c16p2.slang"
    if(_S3 == 0U)
    {

#line 232
        return;
    }

#line 233
    uint _S4 = 3U * d_0;

#line 233
    *winStart_1 = rowWin_0[_S4];
    *winEnd_1 = rowWin_0[_S4 + 1U];
    kernelContext_0->_binPhase_0 = rowWin_0[_S4 + 2U];
    return;
}


#line 60 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S5 = ((MF_DATA_STRIDE));

#line 63
    return _S5;
}



uint mfDataScaleFlag_0()
{
    ;
    uint _S6 = ((MF_DATA_SCALE_BITS));

#line 71
    return _S6;
}


#line 171 "mm_128_fusedTierB_c16p2.slang"
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
    uint _S7 = mfDataStrideFlag_0();

#line 265 "mm_128_fusedTierB_c16p2.slang"
    if(_S7 != 0U)
    {

#line 73 "twiddle.slang"
        uint _S8 = mfDataScaleFlag_0();

#line 266 "mm_128_fusedTierB_c16p2.slang"
        float s_0 = (as_type<float>((_S8)));
        uint _S9 = 2U * i_1;

#line 267
        return half2(half((as_type<float>((b_1[_S9]))) * s_0), half((as_type<float>((b_1[_S9 + 1U]))) * s_0));
    }
    return cload_0(b_1, i_1);
}


#line 331
half2 cmulConj_0(half2 a_0, half2 b_2)
{

#line 331
    half _S10 = a_0.x;

#line 331
    half _S11 = b_2.x;

#line 331
    half _S12 = a_0.y;

#line 331
    half _S13 = b_2.y;

#line 331
    return half2(_S10 * _S11 + _S12 * _S13, _S12 * _S11 - _S10 * _S13);
}


#line 615
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 617
    half2 t1_0 = *a_1 - *c_0;

#line 617
    half2 t2_0 = *b_3 + *d_1;

#line 617
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 619
    *b_3 = t1_0 + j3_0;

#line 619
    *c_0 = t0_0 - t2_0;

#line 619
    *d_1 = t1_0 - j3_0;
    return;
}


#line 330
half2 cmul_0(half2 a_2, half2 b_4)
{

#line 330
    half _S14 = a_2.x;

#line 330
    half _S15 = b_4.x;

#line 330
    half _S16 = a_2.y;

#line 330
    half _S17 = b_4.y;

#line 330
    return half2(_S14 * _S15 - _S16 * _S17, _S14 * _S17 + _S16 * _S15);
}


#line 651
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125h, 0.382568359375h);
    half2 W2_0 = half2(0.70703125h, 0.70703125h);
    half2 W3_0 = half2(0.382568359375h, 0.923828125h);
    half2 W4_0 = half2(0.0h, 1.0h);
    half2 W6_0 = half2(-0.70703125h, 0.70703125h);
    half2 W9_0 = half2(-0.923828125h, -0.382568359375h);

#line 658
    uint n1_0 = 0U;
    for(;;)
    {

#line 659
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 659
            break;
        }

#line 659
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 659
        n1_0 = n1_0 + 1U;

#line 659
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 660
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 660
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 661
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 661
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 662
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 662
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 662
    uint k2_0 = 0U;
    for(;;)
    {

#line 663
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 663
            break;
        }

#line 663
        uint _S18 = 4U * k2_0;

#line 663
        r4_0(&(*r_0)[_S18], &(*r_0)[_S18 + 1U], &(*r_0)[_S18 + 2U], &(*r_0)[_S18 + 3U]);

#line 663
        k2_0 = k2_0 + 1U;

#line 663
    }

    half2 t_0 = (*r_0)[int(1)];

#line 665
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 665
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 666
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 666
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 667
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 667
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 668
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 668
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 669
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 669
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 670
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 670
    (*r_0)[int(14)] = t_5;
    return;
}


#line 49 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S19 = ((MF_COARSE_TWT));

#line 52
    return _S19;
}


#line 76
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S20 = ((MF_ACCURATE_TRIG));

#line 79
    return _S20;
}


#line 103
float2 mfTwiddle_0(float angle_0)
{

#line 81
    uint _S21 = mfAccurateTrigFlag_0();

#line 105
    if(_S21 == 0U)
    {

#line 106
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


#line 332 "mm_128_fusedTierB_c16p2.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S23 = max(TB_0, 1U);

#line 334
    uint j_0 = d_2 / _S23;

#line 334
    uint m_0 = d_2 % _S23;

#line 334
    uint _S24;
    if(TB_0 <= 16U)
    {

#line 335
        _S24 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 335
    }
    else
    {

#line 335
        _S24 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 335
    }

#line 335
    return _S24;
}


#line 308
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 308
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 308
    return;
}


#line 309
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_2)
{

#line 309
    return half2(as_type<half>(ushort(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 635
void dft8_0(array<half2, int(16)> thread* r_1, uint o_0)
{


    thread array<half2, int(8)> b_5;

#line 639
    uint s_2 = 1U;
    for(;;)
    {

#line 640
        if(s_2 < 8U)
        {
        }
        else
        {

#line 640
            break;
        }

#line 640
        uint j_1 = 0U;
        for(;;)
        {

#line 641
            if(j_1 < 4U)
            {
            }
            else
            {

#line 641
                break;
            }

#line 642
            uint k_0 = j_1 & (s_2 - 1U);

#line 642
            uint base_0 = (j_1 - k_0) << 1U;

            float2 _S25 = mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_2));
            uint _S26 = o_0 + j_1;

#line 645
            half2 t_6 = cmul_0(half2(_S25), (*r_1)[_S26 + 4U]);
            uint _S27 = base_0 + k_0;

#line 646
            b_5[_S27] = (*r_1)[_S26] + t_6;

#line 646
            b_5[_S27 + s_2] = (*r_1)[_S26] - t_6;

#line 641
            j_1 = j_1 + 1U;

#line 641
        }

#line 641
        uint i_4 = 0U;

#line 648
        for(;;)
        {

#line 648
            if(i_4 < 8U)
            {
            }
            else
            {

#line 648
                break;
            }

#line 648
            (*r_1)[o_0 + i_4] = b_5[i_4];

#line 648
            i_4 = i_4 + 1U;

#line 648
        }

#line 640
        s_2 = s_2 << 1U;

#line 640
    }

#line 650
    return;
}


#line 754
void innermost_0(array<half2, int(16)> thread* r_2)
{

#line 754
    uint b_6 = 0U;

#line 762
    for(;;)
    {

#line 762
        if(b_6 < 2U)
        {
        }
        else
        {

#line 762
            break;
        }

#line 762
        dft8_0(r_2, b_6 * 8U);

#line 762
        b_6 = b_6 + 1U;

#line 762
    }



    return;
}


#line 882
uint lgOf_0(uint i_5)
{

#line 882
    uint _S28;

#line 882
    if(i_5 < 1U)
    {

#line 882
        _S28 = 4U;

#line 882
    }
    else
    {

#line 882
        if(i_5 == 1U)
        {

#line 882
            _S28 = 3U;

#line 882
        }
        else
        {

#line 882
            _S28 = 1U;

#line 882
        }

#line 882
    }

#line 882
    return _S28;
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




uint c16Mag_0(half2 v_1, uint slot_1, uint ws_0, uint we_0, bool ov_0)
{
    uint idx_0 = slotToIndex_0(slot_1);

#line 901
    bool live_0;
    if(idx_0 >= ws_0)
    {

#line 902
        live_0 = idx_0 < we_0;

#line 902
    }
    else
    {

#line 902
        live_0 = false;

#line 902
    }
    uint nonfin_0 = ((((uint(as_type<ushort>(v_1[0U])) & 65535U) | (uint(as_type<ushort>(v_1[1U])) << 16U)) & 2080406528U) + 67109888U) & 2147516416U;
    float x_1 = float(v_1.x);

#line 904
    float y_0 = float(v_1.y);

#line 904
    uint m_1;
    if(live_0)
    {

#line 905
        m_1 = min((as_type<uint>((x_1 * x_1 + y_0 * y_0))), 2139095040U);

#line 905
    }
    else
    {

#line 905
        m_1 = 0U;

#line 905
    }

#line 905
    bool _S29;
    if(ov_0)
    {

#line 906
        _S29 = true;

#line 906
    }
    else
    {

#line 906
        _S29 = nonfin_0 != 0U;

#line 906
    }

#line 906
    if(_S29)
    {
    }
    else
    {

#line 906
        live_0 = false;

#line 906
    }

#line 906
    if(live_0)
    {

#line 906
        m_1 = 2139095040U;

#line 906
    }

#line 906
    return m_1;
}


#line 1854
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1854
    uint j_2;

#line 1854
    uint d_3;

#line 1854
    thread KernelContext_0 kernelContext_3;

#line 1854
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 1854
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1854
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1854
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1854
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1854
    (&kernelContext_3)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1854
    threadgroup array<uint, int(256)> stg_1;

#line 1854
    (&kernelContext_3)->stg_0 = &stg_1;

#line 1854
    (&kernelContext_3)->_binPhase_0 = 0U;

#line 1875
    uint _S30 = lid_0.x;

#line 1875
    uint _sub_0 = _S30 / 8U;
    uint _pr_0 = gid_0.x * 2U + _sub_0;

#line 1876
    uint _t_0 = _S30 % 8U;
    (&kernelContext_3)->_stgBase_0 = _sub_0 * 128U;

#line 1877
    uint _S31 = entryPointParams_1->ntmpl_0;

#line 1877
    uint _S32 = entryPointParams_1->winStart_0;

#line 1877
    uint _S33 = entryPointParams_1->winEnd_0;

#line 1877
    uint _S34 = entryPointParams_1->binsize_0;

#line 1877
    uint _S35 = entryPointParams_1->thrBits_0;

#line 1887
    for(;;)
    {

#line 1887
        thread uint _S36 = _S32;

#line 1887
        thread uint _S37 = _S33;

#line 1887
        (&kernelContext_3)->_tid_0 = _t_0;

#line 1887
        uint pairs_0 = _S34 * _S31;

#line 1887
        bool slotOk_0 = _pr_0 < pairs_0;

#line 1887
        uint q_0;

#line 1887
        if(slotOk_0)
        {

#line 1887
            q_0 = _pr_0;

#line 1887
        }
        else
        {

#line 1887
            q_0 = pairs_0 - 1U;

#line 1887
        }

#line 1887
        uint _S38;

#line 1887
        if(slotOk_0)
        {

#line 1887
            _S38 = q_0;

#line 1887
        }
        else
        {

#line 1887
            _S38 = 4294967295U;

#line 1887
        }

#line 1887
        uint d_4 = q_0 / _S31;

#line 1887
        uint _S39 = q_0 - d_4 * _S31;

#line 1887
        rowWindow_0(d_4, &_S36, &_S37, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);

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
            uint _S40 = mfDataStrideFlag_0();

#line 1887
            if(_S40 != 0U)
            {

#line 1887
                uint _S41 = mfDataStrideFlag_0();

#line 1887
                q_0 = _S41;

#line 1887
            }
            else
            {

#line 1887
                q_0 = 128U;

#line 1887
            }

#line 1887
            half2 _S42 = dload_0((&kernelContext_3)->entryPointParams_data_0, d_4 * q_0 + _t_0 + 8U * n2_0);

#line 1887
            dreg_0[n2_0] = _S42;

#line 1887
            n2_0 = n2_0 + 1U;

#line 1887
        }

#line 1887
        uint k_1 = 0U;

#line 1887
        for(;;)
        {

#line 1887
            if(k_1 < 1U)
            {
            }
            else
            {

#line 1887
                break;
            }

#line 1887
            uint _S43 = _S38 + k_1;

#line 1887
            uint _S44 = _S39 + k_1;

#line 1887
            uint _S45 = _S36;

#line 1887
            uint _S46 = _S37;

#line 1887
            for(;;)
            {

#line 1887
                thread array<half2, int(16)> r_3;

#line 1887
                n2_0 = 0U;

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
                    r_3[n2_0] = cmulConj_0(dreg_0[n2_0], cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S44 * 128U + _t_0 + 8U * n2_0));

#line 1887
                    n2_0 = n2_0 + 1U;

#line 1887
                }

#line 1887
                for(;;)
                {

#line 1887
                    for(;;)
                    {

#line 1887
                        uint lgTB_0 = firstbithigh_0(8U);

#line 1887
                        uint lgLn_0 = firstbithigh_0(128U);

#line 1887
                        uint blk_1 = _t_0 >> lgTB_0;

#line 1887
                        uint lane_1 = _t_0 & 7U;

#line 1887
                        dft16_0(&r_3);

#line 1887
                        uint _S47 = mfCoarseTwtFlag_0();

#line 1887
                        uint z_1;

#line 1887
                        if(_S47 != 0U)
                        {

#line 1887
                            z_1 = 0U;

#line 1887
                            for(;;)
                            {

#line 1887
                                if(z_1 < 16U)
                                {
                                }
                                else
                                {

#line 1887
                                    break;
                                }

#line 1887
                                uint _S48 = lane_1 * 16U + z_1;

#line 1887
                                r_3[z_1] = cmul_0(r_3[z_1], half2(as_type<half>(ushort((COARSE_TWT_DATA_0[_S48]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S48]) >> 16U) & 65535U))));

#line 1887
                                z_1 = z_1 + 1U;

#line 1887
                            }

#line 1887
                        }
                        else
                        {

#line 1887
                            float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 128.0f);

#line 1887
                            float _S49 = tw_0.x;

#line 1887
                            float _S50 = tw_0.y;

#line 1887
                            z_1 = 0U;

#line 1887
                            float cr_0 = 1.0f;

#line 1887
                            float ci_0 = 0.0f;

#line 1887
                            for(;;)
                            {

#line 1887
                                if(z_1 < 16U)
                                {
                                }
                                else
                                {

#line 1887
                                    break;
                                }

#line 1887
                                r_3[z_1] = cmul_0(r_3[z_1], half2(half(cr_0), half(ci_0)));

#line 1887
                                float nr_0 = cr_0 * _S49 - ci_0 * _S50;

#line 1887
                                float _S51 = cr_0 * _S50 + ci_0 * _S49;

#line 1887
                                z_1 = z_1 + 1U;

#line 1887
                                cr_0 = nr_0;

#line 1887
                                ci_0 = _S51;

#line 1887
                            }

#line 1887
                        }

#line 1887
                        uint per_1 = 16U / max(8U, 1U);

#line 1887
                        uint _S52 = max(0U, 1U);

#line 1887
                        uint blk2_1 = _t_0 / _S52;

#line 1887
                        uint lane2_1 = _t_0 % _S52;

#line 1887
                        for(;;)
                        {

#line 1887
                            thread array<half2, int(16)> out_0;

#line 1887
                            z_1 = 0U;

#line 1887
                            for(;;)
                            {

#line 1887
                                if(z_1 < 16U)
                                {
                                }
                                else
                                {

#line 1887
                                    break;
                                }

#line 1887
                                out_0[z_1] = half2(0.0h, 0.0h);

#line 1887
                                z_1 = z_1 + 1U;

#line 1887
                            }

#line 1887
                            uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 1887
                            uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1887
                            uint p0_0 = computeWant_0(0U, 8U, 128U, blk_1, lane_1, per_1, _S52, 8U, blk2_1, lane2_1);

#line 1887
                            uint _S53 = p0_0 & lenMask_0;

#line 1887
                            uint _S54 = (_S53 >> lgTB_0) * 8U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S53 & spanMask_0);

#line 1887
                            uint c_2 = 0U;

#line 1887
                            for(;;)
                            {

#line 1887
                                if(c_2 < 1U)
                                {
                                }
                                else
                                {

#line 1887
                                    break;
                                }

#line 1887
                                simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 1887
                                j_2 = 0U;

#line 1887
                                for(;;)
                                {

#line 1887
                                    if(j_2 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1887
                                        break;
                                    }

#line 1887
                                    stgPut_0(j_2 * 8U + (&kernelContext_3)->_tid_0, r_3[c_2 * 16U + j_2], &kernelContext_3);

#line 1887
                                    j_2 = j_2 + 1U;

#line 1887
                                }

#line 1887
                                simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 1887
                                d_3 = 0U;

#line 1887
                                for(;;)
                                {

#line 1887
                                    if(d_3 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1887
                                        break;
                                    }

#line 1887
                                    uint pz_0 = computeWant_0(d_3, 8U, 128U, 0U, 0U, per_1, _S52, 8U, 0U, 0U);

#line 1887
                                    uint _S55 = pz_0 & lenMask_0;

#line 1887
                                    uint az_0 = (_S55 >> lgTB_0) * 8U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S55 & spanMask_0);

#line 1887
                                    half2 _S56 = stgGet_0(_S54 + az_0 - c_2 * 16U * 8U, &kernelContext_3);

#line 1887
                                    out_0[d_3] = _S56;

#line 1887
                                    d_3 = d_3 + 1U;

#line 1887
                                }

#line 1887
                                c_2 = c_2 + 1U;

#line 1887
                            }

#line 1887
                            j_2 = 0U;

#line 1887
                            for(;;)
                            {

#line 1887
                                if(j_2 < 16U)
                                {
                                }
                                else
                                {

#line 1887
                                    break;
                                }

#line 1887
                                r_3[j_2] = out_0[j_2];

#line 1887
                                j_2 = j_2 + 1U;

#line 1887
                            }

#line 1887
                            break;
                        }

#line 1887
                        break;
                    }

#line 1887
                    innermost_0(&r_3);

#line 1887
                    break;
                }

#line 1887
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1887
                bool _S57 = _t_0 == 0U;

#line 1887
                if(_S57)
                {

#line 1887
                    (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0] = _S35;

#line 1887
                    (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U] = 4294967295U;

#line 1887
                }

#line 1887
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1887
                d_3 = 0U;

#line 1887
                uint ovAcc_0 = 0U;

#line 1887
                for(;;)
                {

#line 1887
                    if(d_3 < 16U)
                    {
                    }
                    else
                    {

#line 1887
                        break;
                    }

#line 1887
                    uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_3[d_3][0U])) & 65535U) | (uint(as_type<ushort>(r_3[d_3][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1887
                    d_3 = d_3 + 1U;

#line 1887
                    ovAcc_0 = ovAcc_1;

#line 1887
                }

#line 1887
                bool _S58 = (ovAcc_0 & 2147516416U) != 0U;

#line 1887
                half2 _S59 = half2(0.0h, 0.0h);

#line 1887
                uint i_6 = 0U;

#line 1887
                uint bestBits_0 = _S35;

#line 1887
                uint bestSlot_0 = 4294967295U;

#line 1887
                half2 bestV_0 = _S59;

#line 1887
                for(;;)
                {

#line 1887
                    if(i_6 < 16U)
                    {
                    }
                    else
                    {

#line 1887
                        break;
                    }

#line 1887
                    uint _S60 = _t_0 * 16U + i_6;

#line 1887
                    uint m_2 = c16Mag_0(r_3[i_6], _S60, _S45, _S46, _S58);

#line 1887
                    if(m_2 > bestBits_0)
                    {

#line 1887
                        bestBits_0 = m_2;

#line 1887
                        bestSlot_0 = _S60;

#line 1887
                        bestV_0 = r_3[i_6];

#line 1887
                    }

#line 1887
                    i_6 = i_6 + 1U;

#line 1887
                }

#line 1887
                if(bestBits_0 > _S35)
                {

#line 1887
                    uint _S61 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), bestBits_0, memory_order_relaxed);

#line 1887
                }

#line 1887
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1887
                uint best_0 = (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0];

#line 1887
                bool _S62;

#line 1887
                if(bestSlot_0 != 4294967295U)
                {

#line 1887
                    _S62 = bestBits_0 == best_0;

#line 1887
                }
                else
                {

#line 1887
                    _S62 = false;

#line 1887
                }

#line 1887
                uint winner_0;

#line 1887
                if(_S62)
                {

#line 1887
                    winner_0 = bestSlot_0;

#line 1887
                }
                else
                {

#line 1887
                    winner_0 = 4294967295U;

#line 1887
                }

#line 1887
                bool _S63 = winner_0 != 4294967295U;

#line 1887
                if(_S63)
                {

#line 1887
                    uint _S64 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 1887
                }

#line 1887
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1887
                uint wslot_0 = (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U];

#line 1887
                bool _S65 = _S43 != 4294967295U;

#line 1887
                bool _S66;

#line 1887
                if(_S65)
                {

#line 1887
                    _S66 = _S63;

#line 1887
                }
                else
                {

#line 1887
                    _S66 = false;

#line 1887
                }

#line 1887
                bool _S67;

#line 1887
                if(_S66)
                {

#line 1887
                    _S67 = winner_0 == wslot_0;

#line 1887
                }
                else
                {

#line 1887
                    _S67 = false;

#line 1887
                }

#line 1887
                if(_S67)
                {

#line 1887
                    *((&kernelContext_3)->entryPointParams_peakIdx_0+_S43) = int(slotToIndex_0(wslot_0));

#line 1887
                    packed_float2 device* _S68 = (&kernelContext_3)->entryPointParams_peakVal_0+_S43;

#line 1887
                    float2 _S69;

#line 1887
                    if(best_0 >= 2139095040U)
                    {

#line 1887
                        _S69 = float2(3.40282306073709653e+38f, 0.0f);

#line 1887
                    }
                    else
                    {

#line 1887
                        _S69 = float2(float(bestV_0.x), float(bestV_0.y));

#line 1887
                    }

#line 1887
                    *_S68 = packed_float2(_S69) ;

#line 1887
                }

#line 1887
                bool _S70;

#line 1887
                if(_S65)
                {

#line 1887
                    _S70 = _S57;

#line 1887
                }
                else
                {

#line 1887
                    _S70 = false;

#line 1887
                }

#line 1887
                bool _S71;

#line 1887
                if(_S70)
                {

#line 1887
                    _S71 = wslot_0 == 4294967295U;

#line 1887
                }
                else
                {

#line 1887
                    _S71 = false;

#line 1887
                }

#line 1887
                if(_S71)
                {

#line 1887
                    *((&kernelContext_3)->entryPointParams_peakIdx_0+_S43) = int(-1);

#line 1887
                    *((&kernelContext_3)->entryPointParams_peakVal_0+_S43) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1887
                }

#line 1887
                break;
            }

#line 1887
            k_1 = k_1 + 1U;

#line 1887
        }

#line 1887
        break;
    }

    return;
}
