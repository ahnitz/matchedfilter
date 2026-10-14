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


#line 197 "mm_8192_fusedTierB_c16.slang"
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


#line 272 "mm_8192_fusedTierB_c16.slang"
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


#line 248 "mm_8192_fusedTierB_c16.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(8192)> threadgroup* stg_0;
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
    uint _S14 = (_S13 >> lgSpan_0) * 512U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

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
            stgPut_0(j_1 * 512U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

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
            uint az_0 = (_S15 >> lgSpan_0) * 512U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 729
            half2 _S16 = stgGet_0(_S14 + az_0 - c_1 * 16U * 512U, kernelContext_2);


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


#line 791
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 791
    uint _S17;

#line 791
    uint k2_1;

#line 791
    float cr_0;

#line 791
    float ci_0;

#line 791
    uint _S18;

#line 791
    uint _S19;

#line 791
    uint _S20;

#line 791
    for(;;)
    {

#line 791
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(512U);

#line 11
                _S17 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(8192U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 511U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 8192.0f);
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
                uint per_2 = 16U / max(512U, 1U);
                uint _S24 = max(32U, 1U);

#line 38
                _S18 = _S24;
                uint blk2_2 = tid_0 / _S24;

#line 39
                uint lane2_2 = tid_0 % _S24;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 512U, 8192U, blk_2, lane_2, per_2, _S24, 512U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(32U);

#line 11
                _S19 = lgTB_1;

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 31U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 512.0f);
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
                uint per_3 = 16U / _S18;
                uint _S28 = max(2U, 1U);

#line 38
                _S20 = _S28;
                uint blk2_3 = tid_0 / _S28;

#line 39
                uint lane2_3 = tid_0 % _S28;

#line 39
                exchange_0(r_4, _S17, lgTB_1, 32U, 512U, blk_3, lane_3, per_3, _S28, 32U, blk2_3, lane2_3, kernelContext_3);

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


                uint lgTB_2 = firstbithigh_0(2U);

                uint blk_4 = tid_0 >> lgTB_2;
                uint lane_4 = tid_0 & 1U;


                dft16_0(r_4);

#line 26
                float2 tw_2 = mfTwiddle_0(6.28318548202514648f * float(lane_4) / 32.0f);
                float _S29 = tw_2.x;

#line 27
                float _S30 = tw_2.y;

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
                    float nr_2 = cr_0 * _S29 - ci_0 * _S30;
                    float _S31 = cr_0 * _S30 + ci_0 * _S29;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_2;

#line 29
                    ci_0 = _S31;

#line 29
                }

#line 37
                uint per_4 = 16U / _S20;
                uint _S32 = max(0U, 1U);
                uint blk2_4 = tid_0 / _S32;

#line 39
                uint lane2_4 = tid_0 % _S32;

#line 39
                exchange_0(r_4, _S19, lgTB_2, 2U, 32U, blk_4, lane_4, per_4, _S32, 2U, blk2_4, lane2_4, kernelContext_3);

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

#line 794 "mm_8192_fusedTierB_c16.slang"
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
        if(k_0 < 512U)
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
    uint _S33;

#line 760
    if(i_4 < 3U)
    {

#line 760
        _S33 = 4U;

#line 760
    }
    else
    {

#line 760
        _S33 = 1U;

#line 760
    }

#line 760
    return _S33;
}


#line 762
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 766
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 766
    uint lg_2 = lgOf_0(1U);

#line 766
    uint lg_3 = lgOf_0(0U);

#line 771
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 54 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S34 = ((MF_C16_RAW));

#line 57
    return _S34;
}


#line 301 "mm_8192_fusedTierB_c16.slang"
float2 c16Bound_0(float2 v_2, float energy_0)
{

#line 59 "twiddle.slang"
    uint _S35 = mfC16RawFlag_0();

#line 303 "mm_8192_fusedTierB_c16.slang"
    if((1U - _S35) == 0U)
    {

#line 303
        return v_2;
    }

#line 304
    float m_1 = length(v_2);
    float b_7 = m_1 * 1.00146484375f + 0.00893051736056805f * sqrt(energy_0);

#line 305
    float2 _S36;
    if(m_1 > 0.0f)
    {

#line 306
        _S36 = v_2 * float2((b_7 / m_1)) ;

#line 306
    }
    else
    {

#line 306
        _S36 = float2(b_7, 0.0f);

#line 306
    }

#line 306
    return _S36;
}


#line 800
void filterOne_0(uint pair_0, uint d_4, uint t_8, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{


    bool live_0;

#line 840
    thread array<half2, int(16)> r_5;

#line 840
    uint n2_0 = 0U;



    for(;;)
    {

#line 844
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 844
            break;
        }

#line 845
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_8 * 8192U + tid_2 + 512U * n2_0));

#line 844
        n2_0 = n2_0 + 1U;

#line 844
    }

#line 844
    transform_0(&r_5, tid_2, kernelContext_5);

#line 844
    uint i_5 = 0U;

#line 844
    float energy_1 = 0.0f;

#line 874
    for(;;)
    {

#line 874
        if(i_5 < 16U)
        {
        }
        else
        {

#line 874
            break;
        }

#line 875
        float _ex_0 = float(r_5[i_5].x);

#line 875
        float _ey_0 = float(r_5[i_5].y);
        float energy_2 = energy_1 + (_ex_0 * _ex_0 + _ey_0 * _ey_0);

#line 874
        i_5 = i_5 + 1U;

#line 874
        energy_1 = energy_2;

#line 874
    }

#line 874
    float _S37 = pairSum_0(tid_2, energy_1, kernelContext_5);



    float _S38 = _S37 / 8192.0f;

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 990
    bool _S39 = tid_2 == 0U;

#line 990
    if(_S39)
    {

#line 990
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 990
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 990
    }

#line 995
    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;

#line 997
    i_5 = 0U;

#line 997
    uint ovAcc_0 = 0U;

#line 1002
    for(;;)
    {

#line 1002
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1002
            break;
        }

#line 1003
        uint idx_0 = slotToIndex_0(tid_2 * 16U + i_5);
        if(idx_0 >= winStart_2)
        {

#line 1004
            live_0 = idx_0 < winEnd_2;

#line 1004
        }
        else
        {

#line 1004
            live_0 = false;

#line 1004
        }



        float _rx_0 = float(r_5[i_5].x);

#line 1008
        float _ry_0 = float(r_5[i_5].y);
        if(live_0)
        {

#line 1009
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1009
        }
        else
        {

#line 1009
            n2_0 = 0U;

#line 1009
        }

#line 1009
        myMag_0[i_5] = n2_0;

#line 1015
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_5][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_5][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1002
        i_5 = i_5 + 1U;

#line 1002
        ovAcc_0 = ovAcc_1;

#line 1002
    }

#line 1036
    if((ovAcc_0 & 2147516416U) != 0U)
    {

#line 1036
        i_5 = 0U;
        for(;;)
        {

#line 1037
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1037
                break;
            }

#line 1038
            if((myMag_0[i_5]) != 0U)
            {

#line 1038
                live_0 = true;

#line 1038
            }
            else
            {

#line 1038
                uint _S40 = slotToIndex_0(tid_2 * 16U + i_5);
                if(_S40 >= winStart_2)
                {

#line 1039
                    live_0 = _S40 < winEnd_2;

#line 1039
                }
                else
                {

#line 1039
                    live_0 = false;

#line 1039
                }

#line 1038
            }

#line 1038
            if(live_0)
            {
                myMag_0[i_5] = 2139095040U;

#line 1038
            }

#line 1037
            i_5 = i_5 + 1U;

#line 1037
        }

#line 1036
    }

#line 1036
    uint bestBits_0 = thrBits_1;

#line 1036
    i_5 = 0U;

#line 1055
    for(;;)
    {

#line 1055
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1055
            break;
        }

#line 1055
        uint _S41 = max(bestBits_0, myMag_0[i_5]);

#line 1055
        uint i_6 = i_5 + 1U;

#line 1055
        bestBits_0 = _S41;

#line 1055
        i_5 = i_6;

#line 1055
    }

    uint wm_0 = simd_max(bestBits_0);
    bool _S42 = simd_is_first();

#line 1058
    if(_S42)
    {

#line 1058
        live_0 = wm_0 > thrBits_1;

#line 1058
    }
    else
    {

#line 1058
        live_0 = false;

#line 1058
    }

#line 1058
    if(live_0)
    {

#line 1058
        uint _S43 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1058
    }

#line 1073
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1073
    uint winner_0 = 4294967295U;

#line 1073
    i_5 = 0U;

#line 1083
    for(;;)
    {

#line 1083
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1083
            break;
        }

#line 1084
        if((myMag_0[i_5]) > thrBits_1)
        {

#line 1084
            live_0 = (myMag_0[i_5]) == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1084
        }
        else
        {

#line 1084
            live_0 = false;

#line 1084
        }

#line 1084
        if(live_0)
        {

#line 1084
            winner_0 = min(winner_0, tid_2 * 16U + i_5);

#line 1084
        }

#line 1083
        i_5 = i_5 + 1U;

#line 1083
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S44 = simd_is_first();

#line 1088
    if(_S44)
    {

#line 1088
        live_0 = waveWinner_0 != 4294967295U;

#line 1088
    }
    else
    {

#line 1088
        live_0 = false;

#line 1088
    }

#line 1088
    if(live_0)
    {

#line 1089
        uint _S45 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1088
    }

#line 1093
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1093
    i_5 = 0U;
    for(;;)
    {

#line 1094
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1094
            break;
        }

#line 1095
        uint _S46 = tid_2 * 16U + i_5;

#line 1095
        if(_S46 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])
        {

#line 1096
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S46));

#line 1096
            packed_float2 device* _S47 = peakVal_0+pair_0;

            float2 _S48 = c16Bound_0(float2(float(r_5[i_5].x), float(r_5[i_5].y)), _S38);

#line 1098
            *_S47 = packed_float2(_S48) ;

#line 1095
        }

#line 1094
        i_5 = i_5 + 1U;

#line 1094
    }

#line 1104
    if(_S39)
    {

#line 1104
        live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U]) == 4294967295U;

#line 1104
    }
    else
    {

#line 1104
        live_0 = false;

#line 1104
    }

#line 1104
    if(live_0)
    {

#line 1105
        *(peakIdx_0+pair_0) = int(-1);

#line 1105
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1104
    }

#line 1138
    return;
}


#line 1535
void filterPair_0(uint pair_1, uint tid_3, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{

#line 1535
    thread uint _S49 = winStart_3;

#line 1535
    thread uint _S50 = winEnd_3;

#line 1541
    kernelContext_6->_tid_0 = tid_3;

#line 1570
    uint d_5 = pair_1 / ntmpl_1;

#line 1570
    uint _S51 = pair_1 % ntmpl_1;

#line 1575
    rowWindow_0(d_5, &_S49, &_S50);


    thread array<half2, int(16)> dreg_1;

#line 1578
    uint n2_1 = 0U;

    for(;;)
    {

#line 1580
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1580
            break;
        }

#line 1581
        dreg_1[n2_1] = dload_0(data_1, d_5 * 8192U + tid_3 + 512U * n2_1);

#line 1580
        n2_1 = n2_1 + 1U;

#line 1580
    }

#line 1580
    uint k_1 = 0U;

#line 1600
    for(;;)
    {

#line 1600
        if(k_1 < 1U)
        {
        }
        else
        {

#line 1600
            break;
        }

#line 1601
        uint _S52 = pair_1 + k_1;

#line 1601
        uint _S53 = _S51 + k_1;

#line 1601
        thread array<half2, int(16)> _S54 = dreg_1;

#line 1601
        filterOne_0(_S52, d_5, _S53, tid_3, &_S54, data_1, tmpl_1, peakIdx_1, peakVal_1, _S49, _S50, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1600
        k_1 = k_1 + 1U;

#line 1600
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1608
    thread KernelContext_0 kernelContext_7;

#line 1608
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1608
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1608
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1608
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1608
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1608
    threadgroup array<uint, int(8192)> stg_1;

#line 1608
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1625
    uint _pr_0 = gid_0.x;

#line 1625
    uint _t_0 = lid_0.x;
    (&kernelContext_7)->_stgBase_0 = 0U;

#line 1626
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);

#line 1634
    return;
}
