#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
#ifndef MF_C16_RAW
#define MF_C16_RAW 0u
#endif

#line 10912 "hlsl.meta.slang"
uint firstbithigh_0(uint value_0)
{

#line 10925
    if(value_0 == 0U)
    {

#line 10926
        return 4294967295U;
    }

#line 10927
    uint _S1 = clz(value_0);

#line 10927
    return 31U - _S1;
}


#line 197 "mm_16384_fusedTierB_c16.slang"
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


    return cload_0(b_1, i_1);
}


#line 269
half2 cmulConj_0(half2 a_0, half2 b_2)
{

#line 269
    half _S2 = a_0.x;

#line 269
    half _S3 = b_2.x;

#line 269
    half _S4 = a_0.y;

#line 269
    half _S5 = b_2.y;

#line 269
    return half2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 474
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 476
    half2 t1_0 = *a_1 - *c_0;

#line 476
    half2 t2_0 = *b_3 + *d_1;

#line 476
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 478
    *b_3 = t1_0 + j3_0;

#line 478
    *c_0 = t0_0 - t2_0;

#line 478
    *d_1 = t1_0 - j3_0;
    return;
}


#line 268
half2 cmul_0(half2 a_2, half2 b_4)
{

#line 268
    half _S6 = a_2.x;

#line 268
    half _S7 = b_4.x;

#line 268
    half _S8 = a_2.y;

#line 268
    half _S9 = b_4.y;

#line 268
    return half2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 510
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125, 0.382568359375);
    half2 W2_0 = half2(0.70703125, 0.70703125);
    half2 W3_0 = half2(0.382568359375, 0.923828125);
    half2 W4_0 = half2(0.0, 1.0);
    half2 W6_0 = half2(-0.70703125, 0.70703125);
    half2 W9_0 = half2(-0.923828125, -0.382568359375);

#line 517
    uint n1_0 = 0U;
    for(;;)
    {

#line 518
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 518
            break;
        }

#line 518
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 518
        n1_0 = n1_0 + 1U;

#line 518
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 519
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 519
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 520
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 520
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 521
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 521
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 521
    uint k2_0 = 0U;
    for(;;)
    {

#line 522
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 522
            break;
        }

#line 522
        uint _S10 = 4U * k2_0;

#line 522
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 522
        k2_0 = k2_0 + 1U;

#line 522
    }

    half2 t_0 = (*r_0)[int(1)];

#line 524
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 524
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 525
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 525
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 526
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 526
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 527
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 527
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 528
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 528
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 529
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 529
    (*r_0)[int(14)] = t_5;
    return;
}


#line 64 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 270 "mm_16384_fusedTierB_c16.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 272
    uint j_0 = d_2 / _S11;

#line 272
    uint m_0 = d_2 % _S11;

#line 272
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 273
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 273
    }
    else
    {

#line 273
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 273
    }

#line 273
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


#line 246 "mm_16384_fusedTierB_c16.slang"
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


#line 246
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 246
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 246
    return;
}


#line 247
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 247
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 670
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 671
    uint j_1;

#line 682
    thread array<half2, int(16)> out_0;

#line 682
    uint z_0 = 0U;
    for(;;)
    {

#line 683
        if(z_0 < 16U)
        {
        }
        else
        {

#line 683
            break;
        }

#line 683
        out_0[z_0] = half2(0.0, 0.0);

#line 683
        z_0 = z_0 + 1U;

#line 683
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S13 = p0_0 & lenMask_0;

#line 689
    uint _S14 = _S13 >> lgSpan_0;

#line 689
    uint _S15 = _S14 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

#line 689
    uint c_1 = 0U;

    for(;;)
    {

#line 691
        if(c_1 < 2U)
        {
        }
        else
        {

#line 691
            break;
        }

#line 692
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 692
        j_1 = 0U;
        for(;;)
        {

#line 693
            if(j_1 < 8U)
            {
            }
            else
            {

#line 693
                break;
            }

#line 693
            stgPut_0(j_1 * 1024U + kernelContext_2->_tid_0, (*r_1)[c_1 * 8U + j_1], kernelContext_2);

#line 693
            j_1 = j_1 + 1U;

#line 693
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 694
        uint d_3 = 0U;
        for(;;)
        {

#line 695
            if(d_3 < 16U)
            {
            }
            else
            {

#line 695
                break;
            }

#line 696
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S16 = pz_0 & lenMask_0;

#line 697
            uint iz_0 = _S16 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);
            uint i_4 = _S14 + iz_0;
            uint _S17 = c_1 * 8U;

#line 700
            bool _S18;

#line 700
            if(i_4 >= _S17)
            {

#line 700
                _S18 = i_4 < ((c_1 + 1U) * 8U);

#line 700
            }
            else
            {

#line 700
                _S18 = false;

#line 700
            }

#line 700
            if(_S18)
            {

#line 700
                half2 _S19 = stgGet_0(_S15 + az_0 - _S17 * 1024U, kernelContext_2);
                out_0[d_3] = _S19;

#line 700
            }

#line 695
            d_3 = d_3 + 1U;

#line 695
        }

#line 691
        c_1 = c_1 + 1U;

#line 691
    }

#line 691
    j_1 = 0U;

#line 704
    for(;;)
    {

#line 704
        if(j_1 < 16U)
        {
        }
        else
        {

#line 704
            break;
        }

#line 704
        (*r_1)[j_1] = out_0[j_1];

#line 704
        j_1 = j_1 + 1U;

#line 704
    }
    return;
}


#line 489
void dft4_0(array<half2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    half2 t_6 = (*r_2)[o_0 + 1U];

#line 492
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 492
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 613
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 613
    uint b_5 = 0U;

#line 622
    for(;;)
    {

#line 622
        if(b_5 < 4U)
        {
        }
        else
        {

#line 622
            break;
        }

#line 622
        dft4_0(r_3, b_5 * 4U);

#line 622
        b_5 = b_5 + 1U;

#line 622
    }


    return;
}


#line 760
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 760
    uint _S20;

#line 760
    uint k2_1;

#line 760
    float cr_0;

#line 760
    float ci_0;

#line 760
    uint _S21;

#line 760
    uint _S22;

#line 760
    uint _S23;

#line 760
    for(;;)
    {

#line 760
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S20 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(16384U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 16384.0);
                float _S24 = tw_0.x;

#line 27
                float _S25 = tw_0.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

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
                    float nr_0 = cr_0 * _S24 - ci_0 * _S25;
                    float _S26 = cr_0 * _S25 + ci_0 * _S24;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S26;

#line 29
                }

#line 37
                uint per_2 = 16U / max(1024U, 1U);
                uint _S27 = max(64U, 1U);

#line 38
                _S21 = _S27;
                uint blk2_2 = tid_0 / _S27;

#line 39
                uint lane2_2 = tid_0 % _S27;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 1024U, 16384U, blk_2, lane_2, per_2, _S27, 1024U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(64U);

#line 11
                _S22 = lgTB_1;

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 63U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 1024.0);
                float _S28 = tw_1.x;

#line 27
                float _S29 = tw_1.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

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
                    float nr_1 = cr_0 * _S28 - ci_0 * _S29;
                    float _S30 = cr_0 * _S29 + ci_0 * _S28;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S30;

#line 29
                }

#line 37
                uint per_3 = 16U / _S21;
                uint _S31 = max(4U, 1U);

#line 38
                _S23 = _S31;
                uint blk2_3 = tid_0 / _S31;

#line 39
                uint lane2_3 = tid_0 % _S31;

#line 39
                exchange_0(r_4, _S20, lgTB_1, 64U, 1024U, blk_3, lane_3, per_3, _S31, 64U, blk2_3, lane2_3, kernelContext_3);

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


                uint lgTB_2 = firstbithigh_0(4U);

                uint blk_4 = tid_0 >> lgTB_2;
                uint lane_4 = tid_0 & 3U;


                dft16_0(r_4);

#line 26
                float2 tw_2 = mfTwiddle_0(6.28318548202514648 * float(lane_4) / 64.0);
                float _S32 = tw_2.x;

#line 27
                float _S33 = tw_2.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

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
                    float nr_2 = cr_0 * _S32 - ci_0 * _S33;
                    float _S34 = cr_0 * _S33 + ci_0 * _S32;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_2;

#line 29
                    ci_0 = _S34;

#line 29
                }

#line 37
                uint per_4 = 16U / _S23;
                uint _S35 = max(0U, 1U);
                uint blk2_4 = tid_0 / _S35;

#line 39
                uint lane2_4 = tid_0 % _S35;

#line 39
                exchange_0(r_4, _S22, lgTB_2, 4U, 64U, blk_4, lane_4, per_4, _S35, 4U, blk2_4, lane2_4, kernelContext_3);

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

#line 763 "mm_16384_fusedTierB_c16.slang"
    return;
}


#line 309
float pairSum_0(uint tid_1, float v_1, KernelContext_0 thread* kernelContext_4)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_1] = (as_type<uint>((v_1)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 313
    uint k_0 = 0U;

#line 313
    float t_7 = 0.0;

    for(;;)
    {

#line 315
        if(k_0 < 1024U)
        {
        }
        else
        {

#line 315
            break;
        }

#line 315
        float t_8 = t_7 + (as_type<float>(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_0])));

#line 315
        k_0 = k_0 + 1U;

#line 315
        t_7 = t_8;

#line 315
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_7;
}


#line 729
uint lgOf_0(uint i_5)
{

#line 729
    uint _S36;

#line 729
    if(i_5 < 3U)
    {

#line 729
        _S36 = 4U;

#line 729
    }
    else
    {

#line 729
        _S36 = 1U;

#line 729
    }

#line 729
    return _S36;
}


#line 731
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(4U);

    uint x_0 = slot_0 >> lg_0;

#line 735
    uint lg_1 = lgOf_0(3U);

    uint x_1 = x_0 >> lg_1;

#line 735
    uint lg_2 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_2;

#line 735
    uint lg_3 = lgOf_0(1U);

#line 735
    uint lg_4 = lgOf_0(0U);

#line 740
    return (((((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | (x_2 & ((1U << lg_3) - 1U))) << lg_4) | ((x_2 >> lg_3) & ((1U << lg_4) - 1U));
}


#line 47 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S37 = ((MF_C16_RAW));

#line 50
    return _S37;
}


#line 299 "mm_16384_fusedTierB_c16.slang"
float2 c16Bound_0(float2 v_2, float energy_0)
{

#line 52 "twiddle.slang"
    uint _S38 = mfC16RawFlag_0();

#line 301 "mm_16384_fusedTierB_c16.slang"
    if((1U - _S38) == 0U)
    {

#line 301
        return v_2;
    }

#line 302
    float m_1 = length(v_2);
    float b_6 = m_1 * 1.00146484375 + 0.00893051736056805 * sqrt(energy_0);

#line 303
    float2 _S39;
    if(m_1 > 0.0)
    {

#line 304
        _S39 = v_2 * float2((b_6 / m_1)) ;

#line 304
    }
    else
    {

#line 304
        _S39 = float2(b_6, 0.0);

#line 304
    }

#line 304
    return _S39;
}


#line 769
void filterOne_0(uint pair_0, uint d_4, uint t_9, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{


    bool live_0;

#line 803
    thread array<half2, int(16)> r_5;

#line 803
    uint n2_0 = 0U;



    for(;;)
    {

#line 807
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 807
            break;
        }

#line 808
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_9 * 16384U + tid_2 + 1024U * n2_0));

#line 807
        n2_0 = n2_0 + 1U;

#line 807
    }

#line 807
    transform_0(&r_5, tid_2, kernelContext_5);

#line 807
    uint i_6 = 0U;

#line 807
    float energy_1 = 0.0;

#line 837
    for(;;)
    {

#line 837
        if(i_6 < 16U)
        {
        }
        else
        {

#line 837
            break;
        }

#line 838
        float _ex_0 = float(r_5[i_6].x);

#line 838
        float _ey_0 = float(r_5[i_6].y);
        float energy_2 = energy_1 + (_ex_0 * _ex_0 + _ey_0 * _ey_0);

#line 837
        i_6 = i_6 + 1U;

#line 837
        energy_1 = energy_2;

#line 837
    }

#line 837
    float _S40 = pairSum_0(tid_2, energy_1, kernelContext_5);



    float _S41 = _S40 / 16384.0;

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 915
    bool _S42 = tid_2 == 0U;

#line 915
    if(_S42)
    {

#line 915
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 915
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 915
    }

#line 920
    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;

#line 922
    i_6 = 0U;

#line 922
    uint ovAcc_0 = 0U;

#line 927
    for(;;)
    {

#line 927
        if(i_6 < 16U)
        {
        }
        else
        {

#line 927
            break;
        }

#line 928
        uint idx_0 = slotToIndex_0(tid_2 * 16U + i_6);
        if(idx_0 >= winStart_2)
        {

#line 929
            live_0 = idx_0 < winEnd_2;

#line 929
        }
        else
        {

#line 929
            live_0 = false;

#line 929
        }



        float _rx_0 = float(r_5[i_6].x);

#line 933
        float _ry_0 = float(r_5[i_6].y);
        if(live_0)
        {

#line 934
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 934
        }
        else
        {

#line 934
            n2_0 = 0U;

#line 934
        }

#line 934
        myMag_0[i_6] = n2_0;

#line 940
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_6][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_6][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 927
        i_6 = i_6 + 1U;

#line 927
        ovAcc_0 = ovAcc_1;

#line 927
    }

#line 961
    if((ovAcc_0 & 2147516416U) != 0U)
    {

#line 961
        i_6 = 0U;
        for(;;)
        {

#line 962
            if(i_6 < 16U)
            {
            }
            else
            {

#line 962
                break;
            }

#line 963
            if((myMag_0[i_6]) != 0U)
            {

#line 963
                live_0 = true;

#line 963
            }
            else
            {

#line 963
                uint _S43 = slotToIndex_0(tid_2 * 16U + i_6);
                if(_S43 >= winStart_2)
                {

#line 964
                    live_0 = _S43 < winEnd_2;

#line 964
                }
                else
                {

#line 964
                    live_0 = false;

#line 964
                }

#line 963
            }

#line 963
            if(live_0)
            {
                myMag_0[i_6] = 2139095040U;

#line 963
            }

#line 962
            i_6 = i_6 + 1U;

#line 962
        }

#line 961
    }

#line 961
    uint bestBits_0 = thrBits_1;

#line 961
    i_6 = 0U;

#line 980
    for(;;)
    {

#line 980
        if(i_6 < 16U)
        {
        }
        else
        {

#line 980
            break;
        }

#line 980
        uint _S44 = max(bestBits_0, myMag_0[i_6]);

#line 980
        uint i_7 = i_6 + 1U;

#line 980
        bestBits_0 = _S44;

#line 980
        i_6 = i_7;

#line 980
    }

    uint wm_0 = simd_max(bestBits_0);
    bool _S45 = simd_is_first();

#line 983
    if(_S45)
    {

#line 983
        live_0 = wm_0 > thrBits_1;

#line 983
    }
    else
    {

#line 983
        live_0 = false;

#line 983
    }

#line 983
    if(live_0)
    {

#line 983
        uint _S46 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), wm_0, memory_order_relaxed);

#line 983
    }

#line 998
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 998
    uint winner_0 = 4294967295U;

#line 998
    i_6 = 0U;

#line 1008
    for(;;)
    {

#line 1008
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1008
            break;
        }

#line 1009
        if((myMag_0[i_6]) > thrBits_1)
        {

#line 1009
            live_0 = (myMag_0[i_6]) == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1009
        }
        else
        {

#line 1009
            live_0 = false;

#line 1009
        }

#line 1009
        if(live_0)
        {

#line 1009
            winner_0 = min(winner_0, tid_2 * 16U + i_6);

#line 1009
        }

#line 1008
        i_6 = i_6 + 1U;

#line 1008
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S47 = simd_is_first();

#line 1013
    if(_S47)
    {

#line 1013
        live_0 = waveWinner_0 != 4294967295U;

#line 1013
    }
    else
    {

#line 1013
        live_0 = false;

#line 1013
    }

#line 1013
    if(live_0)
    {

#line 1014
        uint _S48 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1013
    }

#line 1018
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1018
    i_6 = 0U;
    for(;;)
    {

#line 1019
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1019
            break;
        }

#line 1020
        uint _S49 = tid_2 * 16U + i_6;

#line 1020
        if(_S49 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])
        {

#line 1021
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S49));

#line 1021
            packed_float2 device* _S50 = peakVal_0+pair_0;

            float2 _S51 = c16Bound_0(float2(float(r_5[i_6].x), float(r_5[i_6].y)), _S41);

#line 1023
            *_S50 = packed_float2(_S51) ;

#line 1020
        }

#line 1019
        i_6 = i_6 + 1U;

#line 1019
    }

#line 1029
    if(_S42)
    {

#line 1029
        live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U]) == 4294967295U;

#line 1029
    }
    else
    {

#line 1029
        live_0 = false;

#line 1029
    }

#line 1029
    if(live_0)
    {

#line 1030
        *(peakIdx_0+pair_0) = int(-1);

#line 1030
        *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 1029
    }

#line 1063
    return;
}


#line 1454
void filterPair_0(uint pair_1, uint tid_3, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{

#line 1454
    thread uint _S52 = winStart_3;

#line 1454
    thread uint _S53 = winEnd_3;

#line 1460
    kernelContext_6->_tid_0 = tid_3;

#line 1489
    uint d_5 = pair_1 / ntmpl_1;

#line 1489
    uint _S54 = pair_1 % ntmpl_1;

#line 1494
    rowWindow_0(d_5, &_S52, &_S53);


    thread array<half2, int(16)> dreg_1;

#line 1497
    uint n2_1 = 0U;

    for(;;)
    {

#line 1499
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1499
            break;
        }

#line 1500
        dreg_1[n2_1] = dload_0(data_1, d_5 * 16384U + tid_3 + 1024U * n2_1);

#line 1499
        n2_1 = n2_1 + 1U;

#line 1499
    }

#line 1499
    uint k_1 = 0U;

#line 1519
    for(;;)
    {

#line 1519
        if(k_1 < 1U)
        {
        }
        else
        {

#line 1519
            break;
        }

#line 1520
        uint _S55 = pair_1 + k_1;

#line 1520
        uint _S56 = _S54 + k_1;

#line 1520
        thread array<half2, int(16)> _S57 = dreg_1;

#line 1520
        filterOne_0(_S55, d_5, _S56, tid_3, &_S57, data_1, tmpl_1, peakIdx_1, peakVal_1, _S52, _S53, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1519
        k_1 = k_1 + 1U;

#line 1519
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1527
    thread KernelContext_0 kernelContext_7;

#line 1527
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1527
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1527
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1527
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1527
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1527
    threadgroup array<uint, int(8192)> stg_1;

#line 1527
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1544
    uint _pr_0 = gid_0.x;

#line 1544
    uint _t_0 = lid_0.x;
    (&kernelContext_7)->_stgBase_0 = 0U;

#line 1545
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);

#line 1553
    return;
}
