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


#line 191 "mm_512_fusedTierB_c16.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 191
    return;
}


#line 159
half2 cload_0(uint device* b_0, uint i_0)
{

#line 160
    uint p_0 = b_0[i_0];

#line 160
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 197
half2 dload_0(uint device* b_1, uint i_1)
{


    return cload_0(b_1, i_1);
}


#line 263
half2 cmulConj_0(half2 a_0, half2 b_2)
{

#line 263
    half _S2 = a_0.x;

#line 263
    half _S3 = b_2.x;

#line 263
    half _S4 = a_0.y;

#line 263
    half _S5 = b_2.y;

#line 263
    return half2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 468
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 470
    half2 t1_0 = *a_1 - *c_0;

#line 470
    half2 t2_0 = *b_3 + *d_1;

#line 470
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 472
    *b_3 = t1_0 + j3_0;

#line 472
    *c_0 = t0_0 - t2_0;

#line 472
    *d_1 = t1_0 - j3_0;
    return;
}


#line 262
half2 cmul_0(half2 a_2, half2 b_4)
{

#line 262
    half _S6 = a_2.x;

#line 262
    half _S7 = b_4.x;

#line 262
    half _S8 = a_2.y;

#line 262
    half _S9 = b_4.y;

#line 262
    return half2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 504
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125, 0.382568359375);
    half2 W2_0 = half2(0.70703125, 0.70703125);
    half2 W3_0 = half2(0.382568359375, 0.923828125);
    half2 W4_0 = half2(0.0, 1.0);
    half2 W6_0 = half2(-0.70703125, 0.70703125);
    half2 W9_0 = half2(-0.923828125, -0.382568359375);

#line 511
    uint n1_0 = 0U;
    for(;;)
    {

#line 512
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 512
            break;
        }

#line 512
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 512
        n1_0 = n1_0 + 1U;

#line 512
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 513
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 513
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 514
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 514
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 515
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 515
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 515
    uint k2_0 = 0U;
    for(;;)
    {

#line 516
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 516
            break;
        }

#line 516
        uint _S10 = 4U * k2_0;

#line 516
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 516
        k2_0 = k2_0 + 1U;

#line 516
    }

    half2 t_0 = (*r_0)[int(1)];

#line 518
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 518
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 519
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 519
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 520
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 520
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 521
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 521
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 522
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 522
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 523
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 523
    (*r_0)[int(14)] = t_5;
    return;
}


#line 64 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 264 "mm_512_fusedTierB_c16.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 266
    uint j_0 = d_2 / _S11;

#line 266
    uint m_0 = d_2 % _S11;

#line 266
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 267
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 267
    }
    else
    {

#line 267
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 267
    }

#line 267
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


#line 240 "mm_512_fusedTierB_c16.slang"
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


#line 240
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 240
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 240
    return;
}


#line 241
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 241
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 664
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 665
    uint j_1;

#line 676
    thread array<half2, int(16)> out_0;

#line 676
    uint z_0 = 0U;
    for(;;)
    {

#line 677
        if(z_0 < 16U)
        {
        }
        else
        {

#line 677
            break;
        }

#line 677
        out_0[z_0] = half2(0.0, 0.0);

#line 677
        z_0 = z_0 + 1U;

#line 677
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S13 = p0_0 & lenMask_0;

#line 683
    uint _S14 = (_S13 >> lgSpan_0) * 32U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

#line 683
    uint c_1 = 0U;

    for(;;)
    {

#line 685
        if(c_1 < 1U)
        {
        }
        else
        {

#line 685
            break;
        }

#line 686
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 686
        j_1 = 0U;
        for(;;)
        {

#line 687
            if(j_1 < 16U)
            {
            }
            else
            {

#line 687
                break;
            }

#line 687
            stgPut_0(j_1 * 32U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 687
            j_1 = j_1 + 1U;

#line 687
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 688
        uint d_3 = 0U;
        for(;;)
        {

#line 689
            if(d_3 < 16U)
            {
            }
            else
            {

#line 689
                break;
            }

#line 690
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S15 = pz_0 & lenMask_0;
            uint az_0 = (_S15 >> lgSpan_0) * 32U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 692
            half2 _S16 = stgGet_0(_S14 + az_0 - c_1 * 16U * 32U, kernelContext_2);


            out_0[d_3] = _S16;

#line 689
            d_3 = d_3 + 1U;

#line 689
        }

#line 685
        c_1 = c_1 + 1U;

#line 685
    }

#line 685
    j_1 = 0U;

#line 698
    for(;;)
    {

#line 698
        if(j_1 < 16U)
        {
        }
        else
        {

#line 698
            break;
        }

#line 698
        (*r_1)[j_1] = out_0[j_1];

#line 698
        j_1 = j_1 + 1U;

#line 698
    }
    return;
}


#line 479
void dft2_0(array<half2, int(16)> thread* r_2, uint o_0)
{
    half2 a_3 = (*r_2)[o_0];

#line 481
    half2 b_5 = (*r_2)[o_0 + 1U];

#line 481
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 481
    (*r_2)[o_0 + 1U] = a_3 - b_5;
    return;
}


#line 607
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 607
    uint b_6 = 0U;

#line 617
    for(;;)
    {

#line 617
        if(b_6 < 8U)
        {
        }
        else
        {

#line 617
            break;
        }

#line 617
        dft2_0(r_3, b_6 * 2U);

#line 617
        b_6 = b_6 + 1U;

#line 617
    }

    return;
}


#line 754
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 754
    uint _S17;

#line 754
    uint k2_1;

#line 754
    float cr_0;

#line 754
    float ci_0;

#line 754
    uint _S18;

#line 754
    for(;;)
    {

#line 754
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
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 512.0);
                float _S19 = tw_0.x;

#line 27
                float _S20 = tw_0.y;

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
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 32.0);
                float _S23 = tw_1.x;

#line 27
                float _S24 = tw_1.y;

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

#line 757 "mm_512_fusedTierB_c16.slang"
    return;
}


#line 303
float pairSum_0(uint tid_1, float v_1, KernelContext_0 thread* kernelContext_4)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_1] = (as_type<uint>((v_1)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 307
    uint k_0 = 0U;

#line 307
    float t_6 = 0.0;

    for(;;)
    {

#line 309
        if(k_0 < 32U)
        {
        }
        else
        {

#line 309
            break;
        }

#line 309
        float t_7 = t_6 + (as_type<float>(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_0])));

#line 309
        k_0 = k_0 + 1U;

#line 309
        t_6 = t_7;

#line 309
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_6;
}


#line 723
uint lgOf_0(uint i_4)
{

#line 723
    uint _S27;

#line 723
    if(i_4 < 2U)
    {

#line 723
        _S27 = 4U;

#line 723
    }
    else
    {

#line 723
        _S27 = 1U;

#line 723
    }

#line 723
    return _S27;
}


#line 725
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 729
    uint lg_1 = lgOf_0(1U);

#line 729
    uint lg_2 = lgOf_0(0U);

#line 734
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 47 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S28 = ((MF_C16_RAW));

#line 50
    return _S28;
}


#line 293 "mm_512_fusedTierB_c16.slang"
float2 c16Bound_0(float2 v_2, float energy_0)
{

#line 52 "twiddle.slang"
    uint _S29 = mfC16RawFlag_0();

#line 295 "mm_512_fusedTierB_c16.slang"
    if((1U - _S29) == 0U)
    {

#line 295
        return v_2;
    }

#line 296
    float m_1 = length(v_2);
    float b_7 = m_1 * 1.00146484375 + 0.00686962902545929 * sqrt(energy_0);

#line 297
    float2 _S30;
    if(m_1 > 0.0)
    {

#line 298
        _S30 = v_2 * float2((b_7 / m_1)) ;

#line 298
    }
    else
    {

#line 298
        _S30 = float2(b_7, 0.0);

#line 298
    }

#line 298
    return _S30;
}


#line 763
void filterOne_0(uint pair_0, uint d_4, uint t_8, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{


    bool live_0;

#line 786
    thread array<half2, int(16)> r_5;

#line 786
    uint n2_0 = 0U;



    for(;;)
    {

#line 790
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 790
            break;
        }

#line 791
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_8 * 512U + tid_2 + 32U * n2_0));

#line 790
        n2_0 = n2_0 + 1U;

#line 790
    }

#line 790
    transform_0(&r_5, tid_2, kernelContext_5);

#line 790
    uint i_5 = 0U;

#line 790
    float energy_1 = 0.0;

#line 820
    for(;;)
    {

#line 820
        if(i_5 < 16U)
        {
        }
        else
        {

#line 820
            break;
        }

#line 821
        float _ex_0 = float(r_5[i_5].x);

#line 821
        float _ey_0 = float(r_5[i_5].y);
        float energy_2 = energy_1 + (_ex_0 * _ex_0 + _ey_0 * _ey_0);

#line 820
        i_5 = i_5 + 1U;

#line 820
        energy_1 = energy_2;

#line 820
    }

#line 820
    float _S31 = pairSum_0(tid_2, energy_1, kernelContext_5);



    float _S32 = _S31 / 512.0;

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 898
    bool _S33 = tid_2 == 0U;

#line 898
    if(_S33)
    {

#line 898
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 898
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 898
    }

#line 903
    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;

#line 905
    i_5 = 0U;

#line 905
    uint ovAcc_0 = 0U;

#line 910
    for(;;)
    {

#line 910
        if(i_5 < 16U)
        {
        }
        else
        {

#line 910
            break;
        }

#line 911
        uint idx_0 = slotToIndex_0(tid_2 * 16U + i_5);
        if(idx_0 >= winStart_2)
        {

#line 912
            live_0 = idx_0 < winEnd_2;

#line 912
        }
        else
        {

#line 912
            live_0 = false;

#line 912
        }



        float _rx_0 = float(r_5[i_5].x);

#line 916
        float _ry_0 = float(r_5[i_5].y);
        if(live_0)
        {

#line 917
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 917
        }
        else
        {

#line 917
            n2_0 = 0U;

#line 917
        }

#line 917
        myMag_0[i_5] = n2_0;

#line 923
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_5][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_5][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 910
        i_5 = i_5 + 1U;

#line 910
        ovAcc_0 = ovAcc_1;

#line 910
    }

#line 944
    if((ovAcc_0 & 2147516416U) != 0U)
    {

#line 944
        i_5 = 0U;
        for(;;)
        {

#line 945
            if(i_5 < 16U)
            {
            }
            else
            {

#line 945
                break;
            }

#line 946
            if((myMag_0[i_5]) != 0U)
            {

#line 946
                live_0 = true;

#line 946
            }
            else
            {

#line 946
                uint _S34 = slotToIndex_0(tid_2 * 16U + i_5);
                if(_S34 >= winStart_2)
                {

#line 947
                    live_0 = _S34 < winEnd_2;

#line 947
                }
                else
                {

#line 947
                    live_0 = false;

#line 947
                }

#line 946
            }

#line 946
            if(live_0)
            {
                myMag_0[i_5] = 2139095040U;

#line 946
            }

#line 945
            i_5 = i_5 + 1U;

#line 945
        }

#line 944
    }

#line 944
    uint bestBits_0 = thrBits_1;

#line 944
    i_5 = 0U;

#line 963
    for(;;)
    {

#line 963
        if(i_5 < 16U)
        {
        }
        else
        {

#line 963
            break;
        }

#line 963
        uint _S35 = max(bestBits_0, myMag_0[i_5]);

#line 963
        uint i_6 = i_5 + 1U;

#line 963
        bestBits_0 = _S35;

#line 963
        i_5 = i_6;

#line 963
    }

    uint wm_0 = simd_max(bestBits_0);
    bool _S36 = simd_is_first();

#line 966
    if(_S36)
    {

#line 966
        live_0 = wm_0 > thrBits_1;

#line 966
    }
    else
    {

#line 966
        live_0 = false;

#line 966
    }

#line 966
    if(live_0)
    {

#line 966
        uint _S37 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), wm_0, memory_order_relaxed);

#line 966
    }

#line 981
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 981
    uint winner_0 = 4294967295U;

#line 981
    i_5 = 0U;

#line 991
    for(;;)
    {

#line 991
        if(i_5 < 16U)
        {
        }
        else
        {

#line 991
            break;
        }

#line 992
        if((myMag_0[i_5]) > thrBits_1)
        {

#line 992
            live_0 = (myMag_0[i_5]) == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 992
        }
        else
        {

#line 992
            live_0 = false;

#line 992
        }

#line 992
        if(live_0)
        {

#line 992
            winner_0 = min(winner_0, tid_2 * 16U + i_5);

#line 992
        }

#line 991
        i_5 = i_5 + 1U;

#line 991
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S38 = simd_is_first();

#line 996
    if(_S38)
    {

#line 996
        live_0 = waveWinner_0 != 4294967295U;

#line 996
    }
    else
    {

#line 996
        live_0 = false;

#line 996
    }

#line 996
    if(live_0)
    {

#line 997
        uint _S39 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 996
    }

#line 1001
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1001
    i_5 = 0U;
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
        uint _S40 = tid_2 * 16U + i_5;

#line 1003
        if(_S40 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])
        {

#line 1004
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S40));

#line 1004
            packed_float2 device* _S41 = peakVal_0+pair_0;

            float2 _S42 = c16Bound_0(float2(float(r_5[i_5].x), float(r_5[i_5].y)), _S32);

#line 1006
            *_S41 = packed_float2(_S42) ;

#line 1003
        }

#line 1002
        i_5 = i_5 + 1U;

#line 1002
    }

#line 1012
    if(_S33)
    {

#line 1012
        live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U]) == 4294967295U;

#line 1012
    }
    else
    {

#line 1012
        live_0 = false;

#line 1012
    }

#line 1012
    if(live_0)
    {

#line 1013
        *(peakIdx_0+pair_0) = int(-1);

#line 1013
        *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 1012
    }

#line 1046
    return;
}


#line 1353
void filterPair_0(uint pair_1, uint tid_3, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{

#line 1353
    thread uint _S43 = winStart_3;

#line 1353
    thread uint _S44 = winEnd_3;

#line 1359
    kernelContext_6->_tid_0 = tid_3;

#line 1388
    uint d_5 = pair_1 / ntmpl_1;

#line 1388
    uint _S45 = pair_1 % ntmpl_1;

#line 1393
    rowWindow_0(d_5, &_S43, &_S44);


    thread array<half2, int(16)> dreg_1;

#line 1396
    uint n2_1 = 0U;

    for(;;)
    {

#line 1398
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1398
            break;
        }

#line 1399
        dreg_1[n2_1] = dload_0(data_1, d_5 * 512U + tid_3 + 32U * n2_1);

#line 1398
        n2_1 = n2_1 + 1U;

#line 1398
    }

#line 1398
    uint k_1 = 0U;

#line 1418
    for(;;)
    {

#line 1418
        if(k_1 < 1U)
        {
        }
        else
        {

#line 1418
            break;
        }

#line 1419
        uint _S46 = pair_1 + k_1;

#line 1419
        uint _S47 = _S45 + k_1;

#line 1419
        thread array<half2, int(16)> _S48 = dreg_1;

#line 1419
        filterOne_0(_S46, d_5, _S47, tid_3, &_S48, data_1, tmpl_1, peakIdx_1, peakVal_1, _S43, _S44, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1418
        k_1 = k_1 + 1U;

#line 1418
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1426
    thread KernelContext_0 kernelContext_7;

#line 1426
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1426
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1426
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1426
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1426
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1426
    threadgroup array<uint, int(512)> stg_1;

#line 1426
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1443
    uint _pr_0 = gid_0.x;

#line 1443
    uint _t_0 = lid_0.x;
    (&kernelContext_7)->_stgBase_0 = 0U;

#line 1444
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);

#line 1452
    return;
}
