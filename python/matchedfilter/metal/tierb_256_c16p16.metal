#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
#ifndef MF_C16_RAW
#define MF_C16_RAW 0u
#endif

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


#line 194 "mm_256_fusedTierB_c16p16.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 194
    return;
}


#line 165
half2 cload_0(uint device* b_0, uint i_0)
{

#line 166
    uint p_0 = b_0[i_0];

#line 166
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 200
half2 dload_0(uint device* b_1, uint i_1)
{

#line 206
    return cload_0(b_1, i_1);
}


#line 268
half2 cmulConj_0(half2 a_0, half2 b_2)
{

#line 268
    half _S2 = a_0.x;

#line 268
    half _S3 = b_2.x;

#line 268
    half _S4 = a_0.y;

#line 268
    half _S5 = b_2.y;

#line 268
    return half2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 473
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 475
    half2 t1_0 = *a_1 - *c_0;

#line 475
    half2 t2_0 = *b_3 + *d_1;

#line 475
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 477
    *b_3 = t1_0 + j3_0;

#line 477
    *c_0 = t0_0 - t2_0;

#line 477
    *d_1 = t1_0 - j3_0;
    return;
}


#line 267
half2 cmul_0(half2 a_2, half2 b_4)
{

#line 267
    half _S6 = a_2.x;

#line 267
    half _S7 = b_4.x;

#line 267
    half _S8 = a_2.y;

#line 267
    half _S9 = b_4.y;

#line 267
    return half2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 509
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125h, 0.382568359375h);
    half2 W2_0 = half2(0.70703125h, 0.70703125h);
    half2 W3_0 = half2(0.382568359375h, 0.923828125h);
    half2 W4_0 = half2(0.0h, 1.0h);
    half2 W6_0 = half2(-0.70703125h, 0.70703125h);
    half2 W9_0 = half2(-0.923828125h, -0.382568359375h);

#line 516
    uint n1_0 = 0U;
    for(;;)
    {

#line 517
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 517
            break;
        }

#line 517
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 517
        n1_0 = n1_0 + 1U;

#line 517
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 518
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 518
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 519
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 519
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 520
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 520
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 520
    uint k2_0 = 0U;
    for(;;)
    {

#line 521
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 521
            break;
        }

#line 521
        uint _S10 = 4U * k2_0;

#line 521
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 521
        k2_0 = k2_0 + 1U;

#line 521
    }

    half2 t_0 = (*r_0)[int(1)];

#line 523
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 523
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 524
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 524
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 525
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 525
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 526
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 526
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 527
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 527
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 528
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 528
    (*r_0)[int(14)] = t_5;
    return;
}


#line 509
void dft16_1(array<half2, int(16)> thread* r_1)
{
    half2 W1_1 = half2(0.923828125h, 0.382568359375h);
    half2 W2_1 = half2(0.70703125h, 0.70703125h);
    half2 W3_1 = half2(0.382568359375h, 0.923828125h);
    half2 W4_1 = half2(0.0h, 1.0h);
    half2 W6_1 = half2(-0.70703125h, 0.70703125h);
    half2 W9_1 = half2(-0.923828125h, -0.382568359375h);

#line 516
    uint n1_1 = 0U;
    for(;;)
    {

#line 517
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 517
            break;
        }

#line 517
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 517
        n1_1 = n1_1 + 1U;

#line 517
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 518
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 518
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 519
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 519
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 520
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 520
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 520
    uint k2_1 = 0U;
    for(;;)
    {

#line 521
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 521
            break;
        }

#line 521
        uint _S11 = 4U * k2_1;

#line 521
        r4_0(&(*r_1)[_S11], &(*r_1)[_S11 + 1U], &(*r_1)[_S11 + 2U], &(*r_1)[_S11 + 3U]);

#line 521
        k2_1 = k2_1 + 1U;

#line 521
    }

    half2 t_6 = (*r_1)[int(1)];

#line 523
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 523
    (*r_1)[int(4)] = t_6;
    half2 t_7 = (*r_1)[int(2)];

#line 524
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 524
    (*r_1)[int(8)] = t_7;
    half2 t_8 = (*r_1)[int(3)];

#line 525
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 525
    (*r_1)[int(12)] = t_8;
    half2 t_9 = (*r_1)[int(6)];

#line 526
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 526
    (*r_1)[int(9)] = t_9;
    half2 t_10 = (*r_1)[int(7)];

#line 527
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 527
    (*r_1)[int(13)] = t_10;
    half2 t_11 = (*r_1)[int(11)];

#line 528
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 528
    (*r_1)[int(14)] = t_11;
    return;
}


#line 74 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 269 "mm_256_fusedTierB_c16p16.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 271
    uint j_0 = d_2 / _S12;

#line 271
    uint m_0 = d_2 % _S12;

#line 271
    uint _S13;
    if(TB_0 <= 16U)
    {

#line 272
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 272
    }
    else
    {

#line 272
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 272
    }

#line 272
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


#line 245 "mm_256_fusedTierB_c16p16.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(4096)> threadgroup* stg_0;
};


#line 245
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 245
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 245
    return;
}


#line 246
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 246
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 698
void exchange_0(array<half2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 699
    uint j_1;

#line 710
    thread array<half2, int(16)> out_0;

#line 710
    uint z_0 = 0U;
    for(;;)
    {

#line 711
        if(z_0 < 16U)
        {
        }
        else
        {

#line 711
            break;
        }

#line 711
        out_0[z_0] = half2(0.0h, 0.0h);

#line 711
        z_0 = z_0 + 1U;

#line 711
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S14 = p0_0 & lenMask_0;

#line 717
    uint _S15 = (_S14 >> lgSpan_0) * 16U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);

#line 717
    uint c_1 = 0U;

    for(;;)
    {

#line 719
        if(c_1 < 1U)
        {
        }
        else
        {

#line 719
            break;
        }

#line 720
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 720
        j_1 = 0U;
        for(;;)
        {

#line 721
            if(j_1 < 16U)
            {
            }
            else
            {

#line 721
                break;
            }

#line 721
            stgPut_0(j_1 * 16U + kernelContext_2->_tid_0, (*r_2)[c_1 * 16U + j_1], kernelContext_2);

#line 721
            j_1 = j_1 + 1U;

#line 721
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 722
        uint d_3 = 0U;
        for(;;)
        {

#line 723
            if(d_3 < 16U)
            {
            }
            else
            {

#line 723
                break;
            }

#line 724
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S16 = pz_0 & lenMask_0;
            uint az_0 = (_S16 >> lgSpan_0) * 16U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 726
            half2 _S17 = stgGet_0(_S15 + az_0 - c_1 * 16U * 16U, kernelContext_2);


            out_0[d_3] = _S17;

#line 723
            d_3 = d_3 + 1U;

#line 723
        }

#line 719
        c_1 = c_1 + 1U;

#line 719
    }

#line 719
    j_1 = 0U;

#line 732
    for(;;)
    {

#line 732
        if(j_1 < 16U)
        {
        }
        else
        {

#line 732
            break;
        }

#line 732
        (*r_2)[j_1] = out_0[j_1];

#line 732
        j_1 = j_1 + 1U;

#line 732
    }
    return;
}


#line 612
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 619
    dft16_1(r_3);

#line 624
    return;
}


#line 800
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 800
    for(;;)
    {

#line 800
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(16U);
                uint lgLn_0 = firstbithigh_0(256U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 15U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 256.0f);
                float _S18 = tw_0.x;

#line 40
                float _S19 = tw_0.y;

#line 40
                uint k2_2 = 0U;

#line 40
                float cr_0 = 1.0f;

#line 40
                float ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], half2(half(cr_0), half(ci_0)));
                    float nr_0 = cr_0 * _S18 - ci_0 * _S19;
                    float _S20 = cr_0 * _S19 + ci_0 * _S18;

#line 42
                    k2_2 = k2_2 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S20;

#line 42
                }

#line 50
                uint per_2 = 16U / max(16U, 1U);
                uint _S21 = max(1U, 1U);
                uint blk2_2 = tid_0 / _S21;

#line 52
                uint lane2_2 = tid_0 % _S21;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 16U, 256U, blk_2, lane_2, per_2, _S21, 16U, blk2_2, lane2_2, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        break;
    }

#line 56
    innermost_0(r_4);

#line 803 "mm_256_fusedTierB_c16p16.slang"
    return;
}


#line 308
float pairSum_0(uint tid_1, float v_1, KernelContext_0 thread* kernelContext_4)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_1] = (as_type<uint>((v_1)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 312
    uint k_0 = 0U;

#line 312
    float t_12 = 0.0f;

    for(;;)
    {

#line 314
        if(k_0 < 16U)
        {
        }
        else
        {

#line 314
            break;
        }

#line 314
        float t_13 = t_12 + (as_type<float>(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_0])));

#line 314
        k_0 = k_0 + 1U;

#line 314
        t_12 = t_13;

#line 314
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_12;
}


#line 757
uint lgOf_0(uint i_4)
{

#line 757
    uint _S22;

#line 757
    if(i_4 < 1U)
    {

#line 757
        _S22 = 4U;

#line 757
    }
    else
    {

#line 757
        if(i_4 == 1U)
        {

#line 757
            _S22 = 4U;

#line 757
        }
        else
        {

#line 757
            _S22 = 1U;

#line 757
        }

#line 757
    }

#line 757
    return _S22;
}


#line 759
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 763
    uint lg_1 = lgOf_0(0U);

#line 768
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}



uint c16Mag_0(half2 v_2, uint slot_1, uint ws_0, uint we_0, bool ov_0)
{
    uint idx_0 = slotToIndex_0(slot_1);

#line 775
    bool live_0;
    if(idx_0 >= ws_0)
    {

#line 776
        live_0 = idx_0 < we_0;

#line 776
    }
    else
    {

#line 776
        live_0 = false;

#line 776
    }
    float x_0 = float(v_2.x);

#line 777
    float y_0 = float(v_2.y);

#line 777
    uint m_1;
    if(live_0)
    {

#line 778
        m_1 = (as_type<uint>((x_0 * x_0 + y_0 * y_0)));

#line 778
    }
    else
    {

#line 778
        m_1 = 0U;

#line 778
    }
    if(ov_0)
    {
    }
    else
    {

#line 779
        live_0 = false;

#line 779
    }

#line 779
    if(live_0)
    {

#line 779
        m_1 = 2139095040U;

#line 779
    }

#line 779
    return m_1;
}


#line 56 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S23 = ((MF_C16_RAW));

#line 59
    return _S23;
}


#line 298 "mm_256_fusedTierB_c16p16.slang"
float2 c16Bound_0(float2 v_3, float energy_0)
{

#line 61 "twiddle.slang"
    uint _S24 = mfC16RawFlag_0();

#line 300 "mm_256_fusedTierB_c16p16.slang"
    if((1U - _S24) == 0U)
    {

#line 300
        return v_3;
    }

#line 301
    float m_2 = length(v_3);
    float b_5 = m_2 * 1.00146484375f + 0.00618266593664885f * sqrt(energy_0);

#line 302
    float2 _S25;
    if(m_2 > 0.0f)
    {

#line 303
        _S25 = v_3 * float2((b_5 / m_2)) ;

#line 303
    }
    else
    {

#line 303
        _S25 = float2(b_5, 0.0f);

#line 303
    }

#line 303
    return _S25;
}


#line 809
void filterOne_0(uint pair_0, uint d_4, uint t_14, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{

#line 849
    thread array<half2, int(16)> r_5;

#line 849
    uint n2_0 = 0U;



    for(;;)
    {

#line 853
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 853
            break;
        }

#line 854
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_14 * 256U + tid_2 + 16U * n2_0));

#line 853
        n2_0 = n2_0 + 1U;

#line 853
    }

#line 853
    transform_0(&r_5, tid_2, kernelContext_5);

#line 853
    uint i_5 = 0U;

#line 853
    float energy_1 = 0.0f;

#line 883
    for(;;)
    {

#line 883
        if(i_5 < 16U)
        {
        }
        else
        {

#line 883
            break;
        }

#line 884
        float _ex_0 = float(r_5[i_5].x);

#line 884
        float _ey_0 = float(r_5[i_5].y);
        float energy_2 = energy_1 + (_ex_0 * _ex_0 + _ey_0 * _ey_0);

#line 883
        i_5 = i_5 + 1U;

#line 883
        energy_1 = energy_2;

#line 883
    }

#line 883
    float _S26 = pairSum_0(tid_2, energy_1, kernelContext_5);



    float energy_3 = _S26 / 256.0f;

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 999
    bool _S27 = tid_2 == 0U;

#line 999
    if(_S27)
    {

#line 999
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 999
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 999
    }

#line 1004
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1004
    i_5 = 0U;

#line 1004
    uint ovAcc_0 = 0U;

#line 1018
    for(;;)
    {

#line 1018
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1018
            break;
        }

#line 1019
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_5][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_5][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1018
        i_5 = i_5 + 1U;

#line 1018
        ovAcc_0 = ovAcc_1;

#line 1018
    }

    bool _S28 = (ovAcc_0 & 2147516416U) != 0U;

#line 1026
    half2 _S29 = half2(0.0h, 0.0h);

#line 1026
    uint bestBits_0 = thrBits_1;

#line 1026
    uint bestSlot_0 = 4294967295U;

#line 1026
    half2 bestV_0 = _S29;

#line 1026
    i_5 = 0U;
    for(;;)
    {

#line 1027
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1027
            break;
        }

#line 1028
        uint _S30 = tid_2 * 16U + i_5;

#line 1028
        uint m_3 = c16Mag_0(r_5[i_5], _S30, winStart_2, winEnd_2, _S28);
        if(m_3 > bestBits_0)
        {

#line 1029
            bestBits_0 = m_3;

#line 1029
            bestSlot_0 = _S30;

#line 1029
            bestV_0 = r_5[i_5];

#line 1029
        }

#line 1027
        i_5 = i_5 + 1U;

#line 1027
    }

#line 1035
    if(bestBits_0 > thrBits_1)
    {

#line 1035
        uint _S31 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), bestBits_0, memory_order_relaxed);

#line 1035
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    uint best_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1039
    bool _S32;
    if(bestSlot_0 != 4294967295U)
    {

#line 1040
        _S32 = bestBits_0 == best_0;

#line 1040
    }
    else
    {

#line 1040
        _S32 = false;

#line 1040
    }

#line 1040
    uint winner_0;

#line 1040
    if(_S32)
    {

#line 1040
        winner_0 = bestSlot_0;

#line 1040
    }
    else
    {

#line 1040
        winner_0 = 4294967295U;

#line 1040
    }

#line 1046
    bool _S33 = winner_0 != 4294967295U;

#line 1046
    if(_S33)
    {

#line 1046
        uint _S34 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 1046
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);
    uint wslot_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U];

    bool _S35 = pair_0 != 4294967295U;

#line 1051
    if(_S35)
    {

#line 1051
        _S32 = _S33;

#line 1051
    }
    else
    {

#line 1051
        _S32 = false;

#line 1051
    }

#line 1051
    if(_S32)
    {

#line 1051
        _S32 = winner_0 == wslot_0;

#line 1051
    }
    else
    {

#line 1051
        _S32 = false;

#line 1051
    }

#line 1051
    if(_S32)
    {

#line 1052
        *(peakIdx_0+pair_0) = int(slotToIndex_0(wslot_0));

#line 1052
        packed_float2 device* _S36 = peakVal_0+pair_0;
        float2 _S37 = c16Bound_0(float2(float(bestV_0.x), float(bestV_0.y)), energy_3);

#line 1053
        *_S36 = packed_float2(_S37) ;

#line 1051
    }



    if(_S35)
    {

#line 1055
        _S32 = _S27;

#line 1055
    }
    else
    {

#line 1055
        _S32 = false;

#line 1055
    }

#line 1055
    if(_S32)
    {

#line 1055
        _S32 = wslot_0 == 4294967295U;

#line 1055
    }
    else
    {

#line 1055
        _S32 = false;

#line 1055
    }

#line 1055
    if(_S32)
    {

#line 1056
        *(peakIdx_0+pair_0) = int(-1);

#line 1056
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1055
    }

#line 1203
    return;
}


#line 1600
void filterPair_0(uint pair_1, uint tid_3, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{

#line 1600
    thread uint _S38 = winStart_3;

#line 1600
    thread uint _S39 = winEnd_3;

#line 1606
    kernelContext_6->_tid_0 = tid_3;

#line 1640
    uint pairs_0 = binsize_2 * ntmpl_1;
    bool slotOk_0 = pair_1 < pairs_0;

#line 1641
    uint q_0;
    if(slotOk_0)
    {

#line 1642
        q_0 = pair_1;

#line 1642
    }
    else
    {

#line 1642
        q_0 = pairs_0 - 1U;

#line 1642
    }

#line 1642
    uint _S40;
    if(slotOk_0)
    {

#line 1643
        _S40 = q_0;

#line 1643
    }
    else
    {

#line 1643
        _S40 = 4294967295U;

#line 1643
    }
    uint d_5 = q_0 / ntmpl_1;

#line 1644
    uint _S41 = q_0 - d_5 * ntmpl_1;
    rowWindow_0(d_5, &_S38, &_S39);

#line 1656
    thread array<half2, int(16)> dreg_1;

#line 1656
    uint n2_1 = 0U;

    for(;;)
    {

#line 1658
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1658
            break;
        }

#line 1659
        dreg_1[n2_1] = dload_0(data_1, d_5 * 256U + tid_3 + 16U * n2_1);

#line 1658
        n2_1 = n2_1 + 1U;

#line 1658
    }

#line 1658
    uint k_1 = 0U;

#line 1678
    for(;;)
    {

#line 1678
        if(k_1 < 1U)
        {
        }
        else
        {

#line 1678
            break;
        }

#line 1679
        uint _S42 = _S40 + k_1;

#line 1679
        uint _S43 = _S41 + k_1;

#line 1679
        thread array<half2, int(16)> _S44 = dreg_1;

#line 1679
        filterOne_0(_S42, d_5, _S43, tid_3, &_S44, data_1, tmpl_1, peakIdx_1, peakVal_1, _S38, _S39, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1678
        k_1 = k_1 + 1U;

#line 1678
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1686
    thread KernelContext_0 kernelContext_7;

#line 1686
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1686
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1686
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1686
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1686
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1686
    threadgroup array<uint, int(4096)> stg_1;

#line 1686
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1706
    uint _S45 = lid_0.x;

#line 1706
    uint _sub_0 = _S45 / 16U;
    uint _pr_0 = gid_0.x * 16U + _sub_0;

#line 1707
    uint _t_0 = _S45 % 16U;
    (&kernelContext_7)->_stgBase_0 = _sub_0 * 256U;

#line 1708
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);



    return;
}
