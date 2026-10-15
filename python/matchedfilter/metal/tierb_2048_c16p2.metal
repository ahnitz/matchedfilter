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


#line 194 "mm_2048_fusedTierB_c16p2.slang"
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


#line 66 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 269 "mm_2048_fusedTierB_c16p2.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 271
    uint j_0 = d_2 / _S11;

#line 271
    uint m_0 = d_2 % _S11;

#line 271
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 272
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 272
    }
    else
    {

#line 272
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 272
    }

#line 272
    return _S12;
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


#line 245 "mm_2048_fusedTierB_c16p2.slang"
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
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
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
    uint _S13 = p0_0 & lenMask_0;

#line 717
    uint _S14 = (_S13 >> lgSpan_0) * 128U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

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
            stgPut_0(j_1 * 128U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

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
            uint _S15 = pz_0 & lenMask_0;
            uint az_0 = (_S15 >> lgSpan_0) * 128U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 726
            half2 _S16 = stgGet_0(_S14 + az_0 - c_1 * 16U * 128U, kernelContext_2);


            out_0[d_3] = _S16;

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
        (*r_1)[j_1] = out_0[j_1];

#line 732
        j_1 = j_1 + 1U;

#line 732
    }
    return;
}


#line 493
void dft8_0(array<half2, int(16)> thread* r_2, uint o_0)
{


    thread array<half2, int(8)> b_5;

#line 497
    uint s_0 = 1U;
    for(;;)
    {

#line 498
        if(s_0 < 8U)
        {
        }
        else
        {

#line 498
            break;
        }

#line 498
        uint j_2 = 0U;
        for(;;)
        {

#line 499
            if(j_2 < 4U)
            {
            }
            else
            {

#line 499
                break;
            }

#line 500
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S17 = o_0 + j_2;

#line 503
            half2 t_6 = cmul_0(half2(mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_0))), (*r_2)[_S17 + 4U]);
            uint _S18 = ((j_2 - k_0) << 1U) + k_0;

#line 504
            b_5[_S18] = (*r_2)[_S17] + t_6;

#line 504
            b_5[_S18 + s_0] = (*r_2)[_S17] - t_6;

#line 499
            j_2 = j_2 + 1U;

#line 499
        }

#line 499
        uint i_4 = 0U;

#line 506
        for(;;)
        {

#line 506
            if(i_4 < 8U)
            {
            }
            else
            {

#line 506
                break;
            }

#line 506
            (*r_2)[o_0 + i_4] = b_5[i_4];

#line 506
            i_4 = i_4 + 1U;

#line 506
        }

#line 498
        s_0 = s_0 << 1U;

#line 498
    }

#line 508
    return;
}


#line 612
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 612
    uint b_6 = 0U;

#line 620
    for(;;)
    {

#line 620
        if(b_6 < 2U)
        {
        }
        else
        {

#line 620
            break;
        }

#line 620
        dft8_0(r_3, b_6 * 8U);

#line 620
        b_6 = b_6 + 1U;

#line 620
    }



    return;
}


#line 800
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 800
    uint _S19;

#line 800
    uint k2_1;

#line 800
    float cr_0;

#line 800
    float ci_0;

#line 800
    uint _S20;

#line 800
    for(;;)
    {

#line 800
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(128U);

#line 11
                _S19 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(2048U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 127U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 2048.0f);
                float _S21 = tw_0.x;

#line 27
                float _S22 = tw_0.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0f;

#line 27
                ci_0 = 0.0f;

                for(;;)
                {

#line 29
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(half(cr_0), half(ci_0)));
                    float nr_0 = cr_0 * _S21 - ci_0 * _S22;
                    float _S23 = cr_0 * _S22 + ci_0 * _S21;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S23;

#line 29
                }

#line 37
                uint per_2 = 16U / max(128U, 1U);
                uint _S24 = max(8U, 1U);

#line 38
                _S20 = _S24;
                uint blk2_2 = tid_0 / _S24;

#line 39
                uint lane2_2 = tid_0 % _S24;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 128U, 2048U, blk_2, lane_2, per_2, _S24, 128U, blk2_2, lane2_2, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        for(;;)
        {

#line 7
            for(;;)
            {


                uint lgTB_1 = firstbithigh_0(8U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 7U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 128.0f);
                float _S25 = tw_1.x;

#line 27
                float _S26 = tw_1.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0f;

#line 27
                ci_0 = 0.0f;

                for(;;)
                {

#line 29
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(half(cr_0), half(ci_0)));
                    float nr_1 = cr_0 * _S25 - ci_0 * _S26;
                    float _S27 = cr_0 * _S26 + ci_0 * _S25;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S27;

#line 29
                }

#line 37
                uint per_3 = 16U / _S20;
                uint _S28 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S28;

#line 39
                uint lane2_3 = tid_0 % _S28;

#line 39
                exchange_0(r_4, _S19, lgTB_1, 8U, 128U, blk_3, lane_3, per_3, _S28, 8U, blk2_3, lane2_3, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        break;
    }

#line 43
    innermost_0(r_4);

#line 803 "mm_2048_fusedTierB_c16p2.slang"
    return;
}


#line 308
float pairSum_0(uint tid_1, float v_1, KernelContext_0 thread* kernelContext_4)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_1] = (as_type<uint>((v_1)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 312
    uint k_1 = 0U;

#line 312
    float t_7 = 0.0f;

    for(;;)
    {

#line 314
        if(k_1 < 128U)
        {
        }
        else
        {

#line 314
            break;
        }

#line 314
        float t_8 = t_7 + (as_type<float>(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_1])));

#line 314
        k_1 = k_1 + 1U;

#line 314
        t_7 = t_8;

#line 314
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_7;
}


#line 757
uint lgOf_0(uint i_5)
{

#line 757
    uint _S29;

#line 757
    if(i_5 < 2U)
    {

#line 757
        _S29 = 4U;

#line 757
    }
    else
    {

#line 757
        if(i_5 == 2U)
        {

#line 757
            _S29 = 3U;

#line 757
        }
        else
        {

#line 757
            _S29 = 1U;

#line 757
        }

#line 757
    }

#line 757
    return _S29;
}


#line 759
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 763
    uint lg_1 = lgOf_0(1U);

#line 763
    uint lg_2 = lgOf_0(0U);

#line 768
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
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
    float x_1 = float(v_2.x);

#line 777
    float y_0 = float(v_2.y);

#line 777
    uint m_1;
    if(live_0)
    {

#line 778
        m_1 = (as_type<uint>((x_1 * x_1 + y_0 * y_0)));

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


#line 49 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S30 = ((MF_C16_RAW));

#line 52
    return _S30;
}


#line 298 "mm_2048_fusedTierB_c16p2.slang"
float2 c16Bound_0(float2 v_3, float energy_0)
{

#line 54 "twiddle.slang"
    uint _S31 = mfC16RawFlag_0();

#line 300 "mm_2048_fusedTierB_c16p2.slang"
    if((1U - _S31) == 0U)
    {

#line 300
        return v_3;
    }

#line 301
    float m_2 = length(v_3);
    float b_7 = m_2 * 1.00146484375f + 0.00893051736056805f * sqrt(energy_0);

#line 302
    float2 _S32;
    if(m_2 > 0.0f)
    {

#line 303
        _S32 = v_3 * float2((b_7 / m_2)) ;

#line 303
    }
    else
    {

#line 303
        _S32 = float2(b_7, 0.0f);

#line 303
    }

#line 303
    return _S32;
}


#line 809
void filterOne_0(uint pair_0, uint d_4, uint t_9, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
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
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_9 * 2048U + tid_2 + 128U * n2_0));

#line 853
        n2_0 = n2_0 + 1U;

#line 853
    }

#line 853
    transform_0(&r_5, tid_2, kernelContext_5);

#line 853
    uint i_6 = 0U;

#line 853
    float energy_1 = 0.0f;

#line 883
    for(;;)
    {

#line 883
        if(i_6 < 16U)
        {
        }
        else
        {

#line 883
            break;
        }

#line 884
        float _ex_0 = float(r_5[i_6].x);

#line 884
        float _ey_0 = float(r_5[i_6].y);
        float energy_2 = energy_1 + (_ex_0 * _ex_0 + _ey_0 * _ey_0);

#line 883
        i_6 = i_6 + 1U;

#line 883
        energy_1 = energy_2;

#line 883
    }

#line 883
    float _S33 = pairSum_0(tid_2, energy_1, kernelContext_5);



    float energy_3 = _S33 / 2048.0f;

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 999
    bool _S34 = tid_2 == 0U;

#line 999
    if(_S34)
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
    i_6 = 0U;

#line 1004
    uint ovAcc_0 = 0U;

#line 1018
    for(;;)
    {

#line 1018
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1018
            break;
        }

#line 1019
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_6][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_6][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1018
        i_6 = i_6 + 1U;

#line 1018
        ovAcc_0 = ovAcc_1;

#line 1018
    }

    bool _S35 = (ovAcc_0 & 2147516416U) != 0U;

#line 1026
    half2 _S36 = half2(0.0h, 0.0h);

#line 1026
    uint bestBits_0 = thrBits_1;

#line 1026
    uint bestSlot_0 = 4294967295U;

#line 1026
    half2 bestV_0 = _S36;

#line 1026
    i_6 = 0U;
    for(;;)
    {

#line 1027
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1027
            break;
        }

#line 1028
        uint _S37 = tid_2 * 16U + i_6;

#line 1028
        uint m_3 = c16Mag_0(r_5[i_6], _S37, winStart_2, winEnd_2, _S35);
        if(m_3 > bestBits_0)
        {

#line 1029
            bestBits_0 = m_3;

#line 1029
            bestSlot_0 = _S37;

#line 1029
            bestV_0 = r_5[i_6];

#line 1029
        }

#line 1027
        i_6 = i_6 + 1U;

#line 1027
    }

#line 1035
    if(bestBits_0 > thrBits_1)
    {

#line 1035
        uint _S38 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), bestBits_0, memory_order_relaxed);

#line 1035
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    uint best_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1039
    bool _S39;
    if(bestSlot_0 != 4294967295U)
    {

#line 1040
        _S39 = bestBits_0 == best_0;

#line 1040
    }
    else
    {

#line 1040
        _S39 = false;

#line 1040
    }

#line 1040
    uint winner_0;

#line 1040
    if(_S39)
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
    bool _S40 = winner_0 != 4294967295U;

#line 1046
    if(_S40)
    {

#line 1046
        uint _S41 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 1046
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);
    uint wslot_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U];

    bool _S42 = pair_0 != 4294967295U;

#line 1051
    if(_S42)
    {

#line 1051
        _S39 = _S40;

#line 1051
    }
    else
    {

#line 1051
        _S39 = false;

#line 1051
    }

#line 1051
    if(_S39)
    {

#line 1051
        _S39 = winner_0 == wslot_0;

#line 1051
    }
    else
    {

#line 1051
        _S39 = false;

#line 1051
    }

#line 1051
    if(_S39)
    {

#line 1052
        *(peakIdx_0+pair_0) = int(slotToIndex_0(wslot_0));

#line 1052
        packed_float2 device* _S43 = peakVal_0+pair_0;
        float2 _S44 = c16Bound_0(float2(float(bestV_0.x), float(bestV_0.y)), energy_3);

#line 1053
        *_S43 = packed_float2(_S44) ;

#line 1051
    }



    if(_S42)
    {

#line 1055
        _S39 = _S34;

#line 1055
    }
    else
    {

#line 1055
        _S39 = false;

#line 1055
    }

#line 1055
    if(_S39)
    {

#line 1055
        _S39 = wslot_0 == 4294967295U;

#line 1055
    }
    else
    {

#line 1055
        _S39 = false;

#line 1055
    }

#line 1055
    if(_S39)
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
    thread uint _S45 = winStart_3;

#line 1600
    thread uint _S46 = winEnd_3;

#line 1606
    kernelContext_6->_tid_0 = tid_3;

#line 1648
    uint d_5 = pair_1 / ntmpl_1;

#line 1648
    uint _S47 = pair_1 % ntmpl_1;

#line 1653
    rowWindow_0(d_5, &_S45, &_S46);


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
        dreg_1[n2_1] = dload_0(data_1, d_5 * 2048U + tid_3 + 128U * n2_1);

#line 1658
        n2_1 = n2_1 + 1U;

#line 1658
    }

#line 1658
    uint k_2 = 0U;

#line 1678
    for(;;)
    {

#line 1678
        if(k_2 < 1U)
        {
        }
        else
        {

#line 1678
            break;
        }

#line 1679
        uint _S48 = pair_1 + k_2;

#line 1679
        uint _S49 = _S47 + k_2;

#line 1679
        thread array<half2, int(16)> _S50 = dreg_1;

#line 1679
        filterOne_0(_S48, d_5, _S49, tid_3, &_S50, data_1, tmpl_1, peakIdx_1, peakVal_1, _S45, _S46, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1678
        k_2 = k_2 + 1U;

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
    uint _S51 = lid_0.x;

#line 1706
    uint _sub_0 = _S51 / 128U;
    uint _pr_0 = gid_0.x * 2U + _sub_0;

#line 1707
    uint _t_0 = _S51 % 128U;
    (&kernelContext_7)->_stgBase_0 = _sub_0 * 2048U;

#line 1708
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);



    return;
}
