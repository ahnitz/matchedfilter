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


#line 197 "mm_512_fusedTierB_c16.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 197
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


#line 203
half2 dload_0(uint device* b_1, uint i_1)
{

#line 209
    return cload_0(b_1, i_1);
}


#line 271
half2 cmulConj_0(half2 a_0, half2 b_2)
{

#line 271
    half _S2 = a_0.x;

#line 271
    half _S3 = b_2.x;

#line 271
    half _S4 = a_0.y;

#line 271
    half _S5 = b_2.y;

#line 271
    return half2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 476
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 478
    half2 t1_0 = *a_1 - *c_0;

#line 478
    half2 t2_0 = *b_3 + *d_1;

#line 478
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 480
    *b_3 = t1_0 + j3_0;

#line 480
    *c_0 = t0_0 - t2_0;

#line 480
    *d_1 = t1_0 - j3_0;
    return;
}


#line 270
half2 cmul_0(half2 a_2, half2 b_4)
{

#line 270
    half _S6 = a_2.x;

#line 270
    half _S7 = b_4.x;

#line 270
    half _S8 = a_2.y;

#line 270
    half _S9 = b_4.y;

#line 270
    return half2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 512
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125h, 0.382568359375h);
    half2 W2_0 = half2(0.70703125h, 0.70703125h);
    half2 W3_0 = half2(0.382568359375h, 0.923828125h);
    half2 W4_0 = half2(0.0h, 1.0h);
    half2 W6_0 = half2(-0.70703125h, 0.70703125h);
    half2 W9_0 = half2(-0.923828125h, -0.382568359375h);

#line 519
    uint n1_0 = 0U;
    for(;;)
    {

#line 520
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 520
            break;
        }

#line 520
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 520
        n1_0 = n1_0 + 1U;

#line 520
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 521
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 521
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 522
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 522
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 523
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 523
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 523
    uint k2_0 = 0U;
    for(;;)
    {

#line 524
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 524
            break;
        }

#line 524
        uint _S10 = 4U * k2_0;

#line 524
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 524
        k2_0 = k2_0 + 1U;

#line 524
    }

    half2 t_0 = (*r_0)[int(1)];

#line 526
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 526
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 527
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 527
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 528
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 528
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 529
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 529
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 530
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 530
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 531
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 531
    (*r_0)[int(14)] = t_5;
    return;
}


#line 72 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 272 "mm_512_fusedTierB_c16.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 274
    uint j_0 = d_2 / _S11;

#line 274
    uint m_0 = d_2 % _S11;

#line 274
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 275
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 275
    }
    else
    {

#line 275
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 275
    }

#line 275
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


#line 248 "mm_512_fusedTierB_c16.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(512)> threadgroup* stg_0;
};


#line 248
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 248
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 248
    return;
}


#line 249
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 249
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 701
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 702
    uint j_1;

#line 713
    thread array<half2, int(16)> out_0;

#line 713
    uint z_0 = 0U;
    for(;;)
    {

#line 714
        if(z_0 < 16U)
        {
        }
        else
        {

#line 714
            break;
        }

#line 714
        out_0[z_0] = half2(0.0h, 0.0h);

#line 714
        z_0 = z_0 + 1U;

#line 714
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S13 = p0_0 & lenMask_0;

#line 720
    uint _S14 = (_S13 >> lgSpan_0) * 32U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

#line 720
    uint c_1 = 0U;

    for(;;)
    {

#line 722
        if(c_1 < 1U)
        {
        }
        else
        {

#line 722
            break;
        }

#line 723
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 723
        j_1 = 0U;
        for(;;)
        {

#line 724
            if(j_1 < 16U)
            {
            }
            else
            {

#line 724
                break;
            }

#line 724
            stgPut_0(j_1 * 32U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 724
            j_1 = j_1 + 1U;

#line 724
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 725
        uint d_3 = 0U;
        for(;;)
        {

#line 726
            if(d_3 < 16U)
            {
            }
            else
            {

#line 726
                break;
            }

#line 727
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S15 = pz_0 & lenMask_0;
            uint az_0 = (_S15 >> lgSpan_0) * 32U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 729
            half2 _S16 = stgGet_0(_S14 + az_0 - c_1 * 16U * 32U, kernelContext_2);


            out_0[d_3] = _S16;

#line 726
            d_3 = d_3 + 1U;

#line 726
        }

#line 722
        c_1 = c_1 + 1U;

#line 722
    }

#line 722
    j_1 = 0U;

#line 735
    for(;;)
    {

#line 735
        if(j_1 < 16U)
        {
        }
        else
        {

#line 735
            break;
        }

#line 735
        (*r_1)[j_1] = out_0[j_1];

#line 735
        j_1 = j_1 + 1U;

#line 735
    }
    return;
}


#line 487
void dft2_0(array<half2, int(16)> thread* r_2, uint o_0)
{
    half2 a_3 = (*r_2)[o_0];

#line 489
    half2 b_5 = (*r_2)[o_0 + 1U];

#line 489
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 489
    (*r_2)[o_0 + 1U] = a_3 - b_5;
    return;
}


#line 615
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 615
    uint b_6 = 0U;

#line 625
    for(;;)
    {

#line 625
        if(b_6 < 8U)
        {
        }
        else
        {

#line 625
            break;
        }

#line 625
        dft2_0(r_3, b_6 * 2U);

#line 625
        b_6 = b_6 + 1U;

#line 625
    }

    return;
}


#line 803
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 803
    uint _S17;

#line 803
    uint k2_1;

#line 803
    float cr_0;

#line 803
    float ci_0;

#line 803
    uint _S18;

#line 803
    for(;;)
    {

#line 803
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(32U);

#line 11
                _S17 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(512U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 31U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 512.0f);
                float _S19 = tw_0.x;

#line 27
                float _S20 = tw_0.y;

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
                    float nr_0 = cr_0 * _S19 - ci_0 * _S20;
                    float _S21 = cr_0 * _S20 + ci_0 * _S19;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S21;

#line 29
                }

#line 37
                uint per_2 = 16U / max(32U, 1U);
                uint _S22 = max(2U, 1U);

#line 38
                _S18 = _S22;
                uint blk2_2 = tid_0 / _S22;

#line 39
                uint lane2_2 = tid_0 % _S22;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 32U, 512U, blk_2, lane_2, per_2, _S22, 32U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(2U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 1U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 32.0f);
                float _S23 = tw_1.x;

#line 27
                float _S24 = tw_1.y;

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
                    float nr_1 = cr_0 * _S23 - ci_0 * _S24;
                    float _S25 = cr_0 * _S24 + ci_0 * _S23;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S25;

#line 29
                }

#line 37
                uint per_3 = 16U / _S18;
                uint _S26 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S26;

#line 39
                uint lane2_3 = tid_0 % _S26;

#line 39
                exchange_0(r_4, _S17, lgTB_1, 2U, 32U, blk_3, lane_3, per_3, _S26, 2U, blk2_3, lane2_3, kernelContext_3);

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

#line 806 "mm_512_fusedTierB_c16.slang"
    return;
}


#line 311
float pairSum_0(uint tid_1, float v_1, KernelContext_0 thread* kernelContext_4)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_1] = (as_type<uint>((v_1)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 315
    uint k_0 = 0U;

#line 315
    float t_6 = 0.0f;

    for(;;)
    {

#line 317
        if(k_0 < 32U)
        {
        }
        else
        {

#line 317
            break;
        }

#line 317
        float t_7 = t_6 + (as_type<float>(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_0])));

#line 317
        k_0 = k_0 + 1U;

#line 317
        t_6 = t_7;

#line 317
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_6;
}


#line 760
uint lgOf_0(uint i_4)
{

#line 760
    uint _S27;

#line 760
    if(i_4 < 2U)
    {

#line 760
        _S27 = 4U;

#line 760
    }
    else
    {

#line 760
        _S27 = 1U;

#line 760
    }

#line 760
    return _S27;
}


#line 762
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 766
    uint lg_1 = lgOf_0(1U);

#line 766
    uint lg_2 = lgOf_0(0U);

#line 771
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}



uint c16Mag_0(half2 v_2, uint slot_1, uint ws_0, uint we_0, bool ov_0)
{
    uint idx_0 = slotToIndex_0(slot_1);

#line 778
    bool live_0;
    if(idx_0 >= ws_0)
    {

#line 779
        live_0 = idx_0 < we_0;

#line 779
    }
    else
    {

#line 779
        live_0 = false;

#line 779
    }
    float x_1 = float(v_2.x);

#line 780
    float y_0 = float(v_2.y);

#line 780
    uint m_1;
    if(live_0)
    {

#line 781
        m_1 = (as_type<uint>((x_1 * x_1 + y_0 * y_0)));

#line 781
    }
    else
    {

#line 781
        m_1 = 0U;

#line 781
    }
    if(ov_0)
    {
    }
    else
    {

#line 782
        live_0 = false;

#line 782
    }

#line 782
    if(live_0)
    {

#line 782
        m_1 = 2139095040U;

#line 782
    }

#line 782
    return m_1;
}


#line 54 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S28 = ((MF_C16_RAW));

#line 57
    return _S28;
}


#line 301 "mm_512_fusedTierB_c16.slang"
float2 c16Bound_0(float2 v_3, float energy_0)
{

#line 59 "twiddle.slang"
    uint _S29 = mfC16RawFlag_0();

#line 303 "mm_512_fusedTierB_c16.slang"
    if((1U - _S29) == 0U)
    {

#line 303
        return v_3;
    }

#line 304
    float m_2 = length(v_3);
    float b_7 = m_2 * 1.00146484375f + 0.00686962902545929f * sqrt(energy_0);

#line 305
    float2 _S30;
    if(m_2 > 0.0f)
    {

#line 306
        _S30 = v_3 * float2((b_7 / m_2)) ;

#line 306
    }
    else
    {

#line 306
        _S30 = float2(b_7, 0.0f);

#line 306
    }

#line 306
    return _S30;
}


#line 812
void filterOne_0(uint pair_0, uint d_4, uint t_8, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{

#line 852
    thread array<half2, int(16)> r_5;

#line 852
    uint n2_0 = 0U;



    for(;;)
    {

#line 856
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 856
            break;
        }

#line 857
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_8 * 512U + tid_2 + 32U * n2_0));

#line 856
        n2_0 = n2_0 + 1U;

#line 856
    }

#line 856
    transform_0(&r_5, tid_2, kernelContext_5);

#line 856
    uint i_5 = 0U;

#line 856
    float energy_1 = 0.0f;

#line 886
    for(;;)
    {

#line 886
        if(i_5 < 16U)
        {
        }
        else
        {

#line 886
            break;
        }

#line 887
        float _ex_0 = float(r_5[i_5].x);

#line 887
        float _ey_0 = float(r_5[i_5].y);
        float energy_2 = energy_1 + (_ex_0 * _ex_0 + _ey_0 * _ey_0);

#line 886
        i_5 = i_5 + 1U;

#line 886
        energy_1 = energy_2;

#line 886
    }

#line 886
    float _S31 = pairSum_0(tid_2, energy_1, kernelContext_5);



    float _S32 = _S31 / 512.0f;

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1002
    bool _S33 = tid_2 == 0U;

#line 1002
    if(_S33)
    {

#line 1002
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 1002
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 1002
    }

#line 1007
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1007
    i_5 = 0U;

#line 1007
    uint ovAcc_0 = 0U;

#line 1019
    for(;;)
    {

#line 1019
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1019
            break;
        }

#line 1020
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_5][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_5][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1019
        i_5 = i_5 + 1U;

#line 1019
        ovAcc_0 = ovAcc_1;

#line 1019
    }

    bool _S34 = (ovAcc_0 & 2147516416U) != 0U;

#line 1021
    uint bestBits_0 = thrBits_1;

#line 1021
    i_5 = 0U;

#line 1027
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
        uint _S35 = max(bestBits_0, c16Mag_0(r_5[i_5], tid_2 * 16U + i_5, winStart_2, winEnd_2, _S34));

#line 1027
        uint i_6 = i_5 + 1U;

#line 1027
        bestBits_0 = _S35;

#line 1027
        i_5 = i_6;

#line 1027
    }


    uint wm_0 = simd_max(bestBits_0);
    bool _S36 = simd_is_first();

#line 1031
    bool _S37;

#line 1031
    if(_S36)
    {

#line 1031
        _S37 = wm_0 > thrBits_1;

#line 1031
    }
    else
    {

#line 1031
        _S37 = false;

#line 1031
    }

#line 1031
    if(_S37)
    {

#line 1031
        uint _S38 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1031
    }

#line 1036
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint _S39 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1039
    uint winner_0 = 4294967295U;

#line 1039
    i_5 = 0U;
    for(;;)
    {

#line 1040
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1040
            break;
        }

#line 1041
        uint _S40 = tid_2 * 16U + i_5;

#line 1041
        uint m_3 = c16Mag_0(r_5[i_5], _S40, winStart_2, winEnd_2, _S34);
        if(m_3 > thrBits_1)
        {

#line 1042
            _S37 = m_3 == _S39;

#line 1042
        }
        else
        {

#line 1042
            _S37 = false;

#line 1042
        }

#line 1042
        if(_S37)
        {

#line 1042
            winner_0 = min(winner_0, _S40);

#line 1042
        }

#line 1040
        i_5 = i_5 + 1U;

#line 1040
    }

#line 1045
    uint waveWinner_0 = simd_min(winner_0);
    bool _S41 = simd_is_first();

#line 1046
    if(_S41)
    {

#line 1046
        _S37 = waveWinner_0 != 4294967295U;

#line 1046
    }
    else
    {

#line 1046
        _S37 = false;

#line 1046
    }

#line 1046
    if(_S37)
    {

#line 1047
        uint _S42 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1046
    }

#line 1051
    threadgroup_barrier(mem_flags::mem_threadgroup);
    uint wslot_0 = (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U];

#line 1052
    i_5 = 0U;
    for(;;)
    {

#line 1053
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1053
            break;
        }

#line 1054
        uint _S43 = tid_2 * 16U + i_5;

#line 1054
        if(_S43 == wslot_0)
        {

#line 1055
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S43));

#line 1055
            packed_float2 device* _S44 = peakVal_0+pair_0;
            float2 _S45 = c16Bound_0(float2(float(r_5[i_5].x), float(r_5[i_5].y)), _S32);

#line 1056
            *_S44 = packed_float2(_S45) ;

#line 1054
        }

#line 1053
        i_5 = i_5 + 1U;

#line 1053
    }

#line 1059
    if(_S33)
    {

#line 1059
        _S37 = wslot_0 == 4294967295U;

#line 1059
    }
    else
    {

#line 1059
        _S37 = false;

#line 1059
    }

#line 1059
    if(_S37)
    {

#line 1060
        *(peakIdx_0+pair_0) = int(-1);

#line 1060
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1059
    }

#line 1207
    return;
}


#line 1604
void filterPair_0(uint pair_1, uint tid_3, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{

#line 1604
    thread uint _S46 = winStart_3;

#line 1604
    thread uint _S47 = winEnd_3;

#line 1610
    kernelContext_6->_tid_0 = tid_3;

#line 1639
    uint d_5 = pair_1 / ntmpl_1;

#line 1639
    uint _S48 = pair_1 % ntmpl_1;

#line 1644
    rowWindow_0(d_5, &_S46, &_S47);


    thread array<half2, int(16)> dreg_1;

#line 1647
    uint n2_1 = 0U;

    for(;;)
    {

#line 1649
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1649
            break;
        }

#line 1650
        dreg_1[n2_1] = dload_0(data_1, d_5 * 512U + tid_3 + 32U * n2_1);

#line 1649
        n2_1 = n2_1 + 1U;

#line 1649
    }

#line 1649
    uint k_1 = 0U;

#line 1669
    for(;;)
    {

#line 1669
        if(k_1 < 1U)
        {
        }
        else
        {

#line 1669
            break;
        }

#line 1670
        uint _S49 = pair_1 + k_1;

#line 1670
        uint _S50 = _S48 + k_1;

#line 1670
        thread array<half2, int(16)> _S51 = dreg_1;

#line 1670
        filterOne_0(_S49, d_5, _S50, tid_3, &_S51, data_1, tmpl_1, peakIdx_1, peakVal_1, _S46, _S47, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1669
        k_1 = k_1 + 1U;

#line 1669
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1677
    thread KernelContext_0 kernelContext_7;

#line 1677
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1677
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1677
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1677
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1677
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1677
    threadgroup array<uint, int(512)> stg_1;

#line 1677
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1694
    uint _pr_0 = gid_0.x;

#line 1694
    uint _t_0 = lid_0.x;
    (&kernelContext_7)->_stgBase_0 = 0U;

#line 1695
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);

#line 1703
    return;
}
