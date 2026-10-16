#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
#ifndef MF_COARSE_TWT
#define MF_COARSE_TWT 0u
#endif
#ifndef MF_C16_RAW
#define MF_C16_RAW 0u
#endif

#line 11 "mm_64_fusedTierB_c16p16.slang"
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


#line 215 "mm_64_fusedTierB_c16p16.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 215
    return;
}


#line 167
half2 cload_0(uint device* b_0, uint i_0)
{

#line 168
    uint p_0 = b_0[i_0];

#line 168
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 221
half2 dload_0(uint device* b_1, uint i_1)
{

#line 227
    return cload_0(b_1, i_1);
}


#line 289
half2 cmulConj_0(half2 a_0, half2 b_2)
{

#line 289
    half _S2 = a_0.x;

#line 289
    half _S3 = b_2.x;

#line 289
    half _S4 = a_0.y;

#line 289
    half _S5 = b_2.y;

#line 289
    return half2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 494
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 496
    half2 t1_0 = *a_1 - *c_0;

#line 496
    half2 t2_0 = *b_3 + *d_1;

#line 496
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 498
    *b_3 = t1_0 + j3_0;

#line 498
    *c_0 = t0_0 - t2_0;

#line 498
    *d_1 = t1_0 - j3_0;
    return;
}


#line 288
half2 cmul_0(half2 a_2, half2 b_4)
{

#line 288
    half _S6 = a_2.x;

#line 288
    half _S7 = b_4.x;

#line 288
    half _S8 = a_2.y;

#line 288
    half _S9 = b_4.y;

#line 288
    return half2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 530
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125h, 0.382568359375h);
    half2 W2_0 = half2(0.70703125h, 0.70703125h);
    half2 W3_0 = half2(0.382568359375h, 0.923828125h);
    half2 W4_0 = half2(0.0h, 1.0h);
    half2 W6_0 = half2(-0.70703125h, 0.70703125h);
    half2 W9_0 = half2(-0.923828125h, -0.382568359375h);

#line 537
    uint n1_0 = 0U;
    for(;;)
    {

#line 538
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 538
            break;
        }

#line 538
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 538
        n1_0 = n1_0 + 1U;

#line 538
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 539
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 539
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 540
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 540
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 541
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 541
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 541
    uint k2_0 = 0U;
    for(;;)
    {

#line 542
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 542
            break;
        }

#line 542
        uint _S10 = 4U * k2_0;

#line 542
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 542
        k2_0 = k2_0 + 1U;

#line 542
    }

    half2 t_0 = (*r_0)[int(1)];

#line 544
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 544
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 545
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 545
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 546
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 546
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 547
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 547
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 548
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 548
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 549
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 549
    (*r_0)[int(14)] = t_5;
    return;
}


#line 52 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S11 = ((MF_COARSE_TWT));

#line 55
    return _S11;
}


#line 84
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 290 "mm_64_fusedTierB_c16p16.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 292
    uint j_0 = d_2 / _S12;

#line 292
    uint m_0 = d_2 % _S12;

#line 292
    uint _S13;
    if(TB_0 <= 16U)
    {

#line 293
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 293
    }
    else
    {

#line 293
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 293
    }

#line 293
    return _S13;
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


#line 266 "mm_64_fusedTierB_c16p16.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 266
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 266
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 266
    return;
}


#line 267
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 267
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 719
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 720
    uint j_1;

#line 731
    thread array<half2, int(16)> out_0;

#line 731
    uint z_0 = 0U;
    for(;;)
    {

#line 732
        if(z_0 < 16U)
        {
        }
        else
        {

#line 732
            break;
        }

#line 732
        out_0[z_0] = half2(0.0h, 0.0h);

#line 732
        z_0 = z_0 + 1U;

#line 732
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S14 = p0_0 & lenMask_0;

#line 738
    uint _S15 = (_S14 >> lgSpan_0) * 4U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);

#line 738
    uint c_1 = 0U;

    for(;;)
    {

#line 740
        if(c_1 < 1U)
        {
        }
        else
        {

#line 740
            break;
        }

#line 741
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 741
        j_1 = 0U;
        for(;;)
        {

#line 742
            if(j_1 < 16U)
            {
            }
            else
            {

#line 742
                break;
            }

#line 742
            stgPut_0(j_1 * 4U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 742
            j_1 = j_1 + 1U;

#line 742
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 743
        uint d_3 = 0U;
        for(;;)
        {

#line 744
            if(d_3 < 16U)
            {
            }
            else
            {

#line 744
                break;
            }

#line 745
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S16 = pz_0 & lenMask_0;
            uint az_0 = (_S16 >> lgSpan_0) * 4U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 747
            half2 _S17 = stgGet_0(_S15 + az_0 - c_1 * 16U * 4U, kernelContext_2);


            out_0[d_3] = _S17;

#line 744
            d_3 = d_3 + 1U;

#line 744
        }

#line 740
        c_1 = c_1 + 1U;

#line 740
    }

#line 740
    j_1 = 0U;

#line 753
    for(;;)
    {

#line 753
        if(j_1 < 16U)
        {
        }
        else
        {

#line 753
            break;
        }

#line 753
        (*r_1)[j_1] = out_0[j_1];

#line 753
        j_1 = j_1 + 1U;

#line 753
    }
    return;
}


#line 509
void dft4_0(array<half2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    half2 t_6 = (*r_2)[o_0 + 1U];

#line 512
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 512
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 633
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 633
    uint b_5 = 0U;

#line 642
    for(;;)
    {

#line 642
        if(b_5 < 4U)
        {
        }
        else
        {

#line 642
            break;
        }

#line 642
        dft4_0(r_3, b_5 * 4U);

#line 642
        b_5 = b_5 + 1U;

#line 642
    }


    return;
}


#line 821
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 11 "fft_transform.slang"
    uint lgTB_0 = firstbithigh_0(4U);
    uint lgLn_0 = firstbithigh_0(64U);
    uint blk_2 = tid_0 >> lgTB_0;
    uint lane_2 = tid_0 & 3U;


    dft16_0(r_4);

#line 57 "twiddle.slang"
    uint _S18 = mfCoarseTwtFlag_0();

#line 57
    uint k2_1;

#line 27 "fft_transform.slang"
    if(_S18 != 0U)
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
            uint _S19 = lane_2 * 16U + k2_1;

#line 31
            (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(as_type<half>(ushort((COARSE_TWT_DATA_0[_S19]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S19]) >> 16U) & 65535U))));

#line 30
            k2_1 = k2_1 + 1U;

#line 30
        }

#line 27
    }
    else
    {

#line 39
        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 64.0f);
        float _S20 = tw_0.x;

#line 40
        float _S21 = tw_0.y;

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
            float nr_0 = cr_0 * _S20 - ci_0 * _S21;
            float _S22 = cr_0 * _S21 + ci_0 * _S20;

#line 42
            k2_1 = k2_1 + 1U;

#line 42
            cr_0 = nr_0;

#line 42
            ci_0 = _S22;

#line 42
        }

#line 27
    }

#line 50
    uint per_2 = 16U / max(4U, 1U);
    uint _S23 = max(0U, 1U);
    uint blk2_2 = tid_0 / _S23;

#line 52
    uint lane2_2 = tid_0 % _S23;

#line 52
    exchange_0(r_4, lgLn_0, lgTB_0, 4U, 64U, blk_2, lane_2, per_2, _S23, 4U, blk2_2, lane2_2, kernelContext_3);



    innermost_0(r_4);

#line 824 "mm_64_fusedTierB_c16p16.slang"
    return;
}


#line 329
float pairSum_0(uint tid_1, float v_1, KernelContext_0 thread* kernelContext_4)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_1] = (as_type<uint>((v_1)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 333
    uint k_0 = 0U;

#line 333
    float t_7 = 0.0f;

    for(;;)
    {

#line 335
        if(k_0 < 4U)
        {
        }
        else
        {

#line 335
            break;
        }

#line 335
        float t_8 = t_7 + (as_type<float>(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_0])));

#line 335
        k_0 = k_0 + 1U;

#line 335
        t_7 = t_8;

#line 335
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_7;
}


#line 778
uint lgOf_0(uint i_4)
{

#line 778
    uint _S24;

#line 778
    if(i_4 < 1U)
    {

#line 778
        _S24 = 4U;

#line 778
    }
    else
    {

#line 778
        _S24 = 1U;

#line 778
    }

#line 778
    return _S24;
}


#line 780
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 784
    uint lg_1 = lgOf_0(1U);

#line 784
    uint lg_2 = lgOf_0(0U);

#line 789
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}



uint c16Mag_0(half2 v_2, uint slot_1, uint ws_0, uint we_0, bool ov_0)
{
    uint idx_0 = slotToIndex_0(slot_1);

#line 796
    bool live_0;
    if(idx_0 >= ws_0)
    {

#line 797
        live_0 = idx_0 < we_0;

#line 797
    }
    else
    {

#line 797
        live_0 = false;

#line 797
    }
    float x_1 = float(v_2.x);

#line 798
    float y_0 = float(v_2.y);

#line 798
    uint m_1;
    if(live_0)
    {

#line 799
        m_1 = (as_type<uint>((x_1 * x_1 + y_0 * y_0)));

#line 799
    }
    else
    {

#line 799
        m_1 = 0U;

#line 799
    }
    if(ov_0)
    {
    }
    else
    {

#line 800
        live_0 = false;

#line 800
    }

#line 800
    if(live_0)
    {

#line 800
        m_1 = 2139095040U;

#line 800
    }

#line 800
    return m_1;
}


#line 66 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S25 = ((MF_C16_RAW));

#line 69
    return _S25;
}


#line 319 "mm_64_fusedTierB_c16p16.slang"
float2 c16Bound_0(float2 v_3, float energy_0)
{

#line 71 "twiddle.slang"
    uint _S26 = mfC16RawFlag_0();

#line 321 "mm_64_fusedTierB_c16p16.slang"
    if((1U - _S26) == 0U)
    {

#line 321
        return v_3;
    }

#line 322
    float m_2 = length(v_3);
    float b_6 = m_2 * 1.00146484375f + 0.00515219708904624f * sqrt(energy_0);

#line 323
    float2 _S27;
    if(m_2 > 0.0f)
    {

#line 324
        _S27 = v_3 * float2((b_6 / m_2)) ;

#line 324
    }
    else
    {

#line 324
        _S27 = float2(b_6, 0.0f);

#line 324
    }

#line 324
    return _S27;
}


#line 830
void filterOne_0(uint pair_0, uint d_4, uint t_9, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{

#line 870
    thread array<half2, int(16)> r_5;

#line 870
    uint n2_0 = 0U;



    for(;;)
    {

#line 874
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 874
            break;
        }

#line 875
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_9 * 64U + tid_2 + 4U * n2_0));

#line 874
        n2_0 = n2_0 + 1U;

#line 874
    }

#line 874
    transform_0(&r_5, tid_2, kernelContext_5);

#line 874
    uint i_5 = 0U;

#line 874
    float energy_1 = 0.0f;

#line 904
    for(;;)
    {

#line 904
        if(i_5 < 16U)
        {
        }
        else
        {

#line 904
            break;
        }

#line 905
        float _ex_0 = float(r_5[i_5].x);

#line 905
        float _ey_0 = float(r_5[i_5].y);
        float energy_2 = energy_1 + (_ex_0 * _ex_0 + _ey_0 * _ey_0);

#line 904
        i_5 = i_5 + 1U;

#line 904
        energy_1 = energy_2;

#line 904
    }

#line 904
    float _S28 = pairSum_0(tid_2, energy_1, kernelContext_5);



    float energy_3 = _S28 / 64.0f;

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1020
    bool _S29 = tid_2 == 0U;

#line 1020
    if(_S29)
    {

#line 1020
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 1020
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 1020
    }

#line 1025
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1025
    i_5 = 0U;

#line 1025
    uint ovAcc_0 = 0U;

#line 1039
    for(;;)
    {

#line 1039
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1039
            break;
        }

#line 1040
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_5][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_5][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1039
        i_5 = i_5 + 1U;

#line 1039
        ovAcc_0 = ovAcc_1;

#line 1039
    }

    bool _S30 = (ovAcc_0 & 2147516416U) != 0U;

#line 1047
    half2 _S31 = half2(0.0h, 0.0h);

#line 1047
    uint bestBits_0 = thrBits_1;

#line 1047
    uint bestSlot_0 = 4294967295U;

#line 1047
    half2 bestV_0 = _S31;

#line 1047
    i_5 = 0U;
    for(;;)
    {

#line 1048
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1048
            break;
        }

#line 1049
        uint _S32 = tid_2 * 16U + i_5;

#line 1049
        uint m_3 = c16Mag_0(r_5[i_5], _S32, winStart_2, winEnd_2, _S30);
        if(m_3 > bestBits_0)
        {

#line 1050
            bestBits_0 = m_3;

#line 1050
            bestSlot_0 = _S32;

#line 1050
            bestV_0 = r_5[i_5];

#line 1050
        }

#line 1048
        i_5 = i_5 + 1U;

#line 1048
    }

#line 1056
    if(bestBits_0 > thrBits_1)
    {

#line 1056
        uint _S33 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), bestBits_0, memory_order_relaxed);

#line 1056
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    uint best_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1060
    bool _S34;
    if(bestSlot_0 != 4294967295U)
    {

#line 1061
        _S34 = bestBits_0 == best_0;

#line 1061
    }
    else
    {

#line 1061
        _S34 = false;

#line 1061
    }

#line 1061
    uint winner_0;

#line 1061
    if(_S34)
    {

#line 1061
        winner_0 = bestSlot_0;

#line 1061
    }
    else
    {

#line 1061
        winner_0 = 4294967295U;

#line 1061
    }

#line 1067
    bool _S35 = winner_0 != 4294967295U;

#line 1067
    if(_S35)
    {

#line 1067
        uint _S36 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 1067
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);
    uint wslot_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U];

    bool _S37 = pair_0 != 4294967295U;

#line 1072
    if(_S37)
    {

#line 1072
        _S34 = _S35;

#line 1072
    }
    else
    {

#line 1072
        _S34 = false;

#line 1072
    }

#line 1072
    if(_S34)
    {

#line 1072
        _S34 = winner_0 == wslot_0;

#line 1072
    }
    else
    {

#line 1072
        _S34 = false;

#line 1072
    }

#line 1072
    if(_S34)
    {

#line 1073
        *(peakIdx_0+pair_0) = int(slotToIndex_0(wslot_0));

#line 1073
        packed_float2 device* _S38 = peakVal_0+pair_0;
        float2 _S39 = c16Bound_0(float2(float(bestV_0.x), float(bestV_0.y)), energy_3);

#line 1074
        *_S38 = packed_float2(_S39) ;

#line 1072
    }



    if(_S37)
    {

#line 1076
        _S34 = _S29;

#line 1076
    }
    else
    {

#line 1076
        _S34 = false;

#line 1076
    }

#line 1076
    if(_S34)
    {

#line 1076
        _S34 = wslot_0 == 4294967295U;

#line 1076
    }
    else
    {

#line 1076
        _S34 = false;

#line 1076
    }

#line 1076
    if(_S34)
    {

#line 1077
        *(peakIdx_0+pair_0) = int(-1);

#line 1077
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1076
    }

#line 1224
    return;
}


#line 1620
void filterPair_0(uint pair_1, uint tid_3, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{

#line 1620
    thread uint _S40 = winStart_3;

#line 1620
    thread uint _S41 = winEnd_3;

#line 1626
    kernelContext_6->_tid_0 = tid_3;

#line 1660
    uint pairs_0 = binsize_2 * ntmpl_1;
    bool slotOk_0 = pair_1 < pairs_0;

#line 1661
    uint q_0;
    if(slotOk_0)
    {

#line 1662
        q_0 = pair_1;

#line 1662
    }
    else
    {

#line 1662
        q_0 = pairs_0 - 1U;

#line 1662
    }

#line 1662
    uint _S42;
    if(slotOk_0)
    {

#line 1663
        _S42 = q_0;

#line 1663
    }
    else
    {

#line 1663
        _S42 = 4294967295U;

#line 1663
    }
    uint d_5 = q_0 / ntmpl_1;

#line 1664
    uint _S43 = q_0 - d_5 * ntmpl_1;
    rowWindow_0(d_5, &_S40, &_S41);

#line 1676
    thread array<half2, int(16)> dreg_1;

#line 1676
    uint n2_1 = 0U;

    for(;;)
    {

#line 1678
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1678
            break;
        }

#line 1679
        dreg_1[n2_1] = dload_0(data_1, d_5 * 64U + tid_3 + 4U * n2_1);

#line 1678
        n2_1 = n2_1 + 1U;

#line 1678
    }

#line 1678
    uint k_1 = 0U;

#line 1698
    for(;;)
    {

#line 1698
        if(k_1 < 1U)
        {
        }
        else
        {

#line 1698
            break;
        }

#line 1699
        uint _S44 = _S42 + k_1;

#line 1699
        uint _S45 = _S43 + k_1;

#line 1699
        thread array<half2, int(16)> _S46 = dreg_1;

#line 1699
        filterOne_0(_S44, d_5, _S45, tid_3, &_S46, data_1, tmpl_1, peakIdx_1, peakVal_1, _S40, _S41, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1698
        k_1 = k_1 + 1U;

#line 1698
    }



    return;
}


#line 1715
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1715
    thread KernelContext_0 kernelContext_7;

#line 1715
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1715
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1715
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1715
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1715
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1715
    threadgroup array<uint, int(1024)> stg_1;

#line 1715
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1735
    uint _S47 = lid_0.x;

#line 1735
    uint _sub_0 = _S47 / 4U;
    uint _pr_0 = gid_0.x * 16U + _sub_0;

#line 1736
    uint _t_0 = _S47 % 4U;
    (&kernelContext_7)->_stgBase_0 = _sub_0 * 64U;

#line 1737
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);

#line 1748
    return;
}
