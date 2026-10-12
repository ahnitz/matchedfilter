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


#line 197 "mm_128_fusedTierB_c16p32.slang"
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


#line 270 "mm_128_fusedTierB_c16p32.slang"
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


#line 246 "mm_128_fusedTierB_c16p32.slang"
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
    uint _S14 = (_S13 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

#line 689
    uint c_1 = 0U;

    for(;;)
    {

#line 691
        if(c_1 < 1U)
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
            if(j_1 < 16U)
            {
            }
            else
            {

#line 693
                break;
            }

#line 693
            stgPut_0(j_1 * 8U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

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
            uint _S15 = pz_0 & lenMask_0;
            uint az_0 = (_S15 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 698
            half2 _S16 = stgGet_0(_S14 + az_0 - c_1 * 16U * 8U, kernelContext_2);


            out_0[d_3] = _S16;

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


#line 494
void dft8_0(array<half2, int(16)> thread* r_2, uint o_0)
{


    thread array<half2, int(8)> b_5;

#line 498
    uint s_0 = 1U;
    for(;;)
    {

#line 499
        if(s_0 < 8U)
        {
        }
        else
        {

#line 499
            break;
        }

#line 499
        uint j_2 = 0U;
        for(;;)
        {

#line 500
            if(j_2 < 4U)
            {
            }
            else
            {

#line 500
                break;
            }

#line 501
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S17 = o_0 + j_2;

#line 504
            half2 t_6 = cmul_0(half2(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0))), (*r_2)[_S17 + 4U]);
            uint _S18 = ((j_2 - k_0) << 1U) + k_0;

#line 505
            b_5[_S18] = (*r_2)[_S17] + t_6;

#line 505
            b_5[_S18 + s_0] = (*r_2)[_S17] - t_6;

#line 500
            j_2 = j_2 + 1U;

#line 500
        }

#line 500
        uint i_4 = 0U;

#line 507
        for(;;)
        {

#line 507
            if(i_4 < 8U)
            {
            }
            else
            {

#line 507
                break;
            }

#line 507
            (*r_2)[o_0 + i_4] = b_5[i_4];

#line 507
            i_4 = i_4 + 1U;

#line 507
        }

#line 499
        s_0 = s_0 << 1U;

#line 499
    }

#line 509
    return;
}


#line 613
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 613
    uint b_6 = 0U;

#line 621
    for(;;)
    {

#line 621
        if(b_6 < 2U)
        {
        }
        else
        {

#line 621
            break;
        }

#line 621
        dft8_0(r_3, b_6 * 8U);

#line 621
        b_6 = b_6 + 1U;

#line 621
    }



    return;
}


#line 760
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 760
    for(;;)
    {

#line 760
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(8U);
                uint lgLn_0 = firstbithigh_0(128U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 7U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 128.0);
                float _S19 = tw_0.x;

#line 27
                float _S20 = tw_0.y;

#line 27
                uint k2_1 = 0U;

#line 27
                float cr_0 = 1.0;

#line 27
                float ci_0 = 0.0;

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
                uint per_2 = 16U / max(8U, 1U);
                uint _S22 = max(0U, 1U);
                uint blk2_2 = tid_0 / _S22;

#line 39
                uint lane2_2 = tid_0 % _S22;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 8U, 128U, blk_2, lane_2, per_2, _S22, 8U, blk2_2, lane2_2, kernelContext_3);

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

#line 763 "mm_128_fusedTierB_c16p32.slang"
    return;
}


#line 309
float pairSum_0(uint tid_1, float v_1, KernelContext_0 thread* kernelContext_4)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_1] = (as_type<uint>((v_1)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 313
    uint k_1 = 0U;

#line 313
    float t_7 = 0.0;

    for(;;)
    {

#line 315
        if(k_1 < 8U)
        {
        }
        else
        {

#line 315
            break;
        }

#line 315
        float t_8 = t_7 + (as_type<float>(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_1])));

#line 315
        k_1 = k_1 + 1U;

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
    uint _S23;

#line 729
    if(i_5 < 1U)
    {

#line 729
        _S23 = 4U;

#line 729
    }
    else
    {

#line 729
        if(i_5 == 1U)
        {

#line 729
            _S23 = 3U;

#line 729
        }
        else
        {

#line 729
            _S23 = 1U;

#line 729
        }

#line 729
    }

#line 729
    return _S23;
}


#line 731
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 735
    uint lg_1 = lgOf_0(0U);

#line 740
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 47 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S24 = ((MF_C16_RAW));

#line 50
    return _S24;
}


#line 299 "mm_128_fusedTierB_c16p32.slang"
float2 c16Bound_0(float2 v_2, float energy_0)
{

#line 52 "twiddle.slang"
    uint _S25 = mfC16RawFlag_0();

#line 301 "mm_128_fusedTierB_c16p32.slang"
    if((1U - _S25) == 0U)
    {

#line 301
        return v_2;
    }

#line 302
    float m_1 = length(v_2);
    float b_7 = m_1 * 1.00146484375 + 0.00583916017785668 * sqrt(energy_0);

#line 303
    float2 _S26;
    if(m_1 > 0.0)
    {

#line 304
        _S26 = v_2 * float2((b_7 / m_1)) ;

#line 304
    }
    else
    {

#line 304
        _S26 = float2(b_7, 0.0);

#line 304
    }

#line 304
    return _S26;
}


#line 769
void filterOne_0(uint pair_0, uint d_4, uint t_9, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{


    bool live_0;

#line 809
    thread array<half2, int(16)> r_5;

#line 809
    uint n2_0 = 0U;



    for(;;)
    {

#line 813
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 813
            break;
        }

#line 814
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_9 * 128U + tid_2 + 8U * n2_0));

#line 813
        n2_0 = n2_0 + 1U;

#line 813
    }

#line 813
    transform_0(&r_5, tid_2, kernelContext_5);

#line 813
    uint i_6 = 0U;

#line 813
    float energy_1 = 0.0;

#line 843
    for(;;)
    {

#line 843
        if(i_6 < 16U)
        {
        }
        else
        {

#line 843
            break;
        }

#line 844
        float _ex_0 = float(r_5[i_6].x);

#line 844
        float _ey_0 = float(r_5[i_6].y);
        float energy_2 = energy_1 + (_ex_0 * _ex_0 + _ey_0 * _ey_0);

#line 843
        i_6 = i_6 + 1U;

#line 843
        energy_1 = energy_2;

#line 843
    }

#line 843
    float _S27 = pairSum_0(tid_2, energy_1, kernelContext_5);



    float _S28 = _S27 / 128.0;

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 959
    bool _S29 = tid_2 == 0U;

#line 959
    if(_S29)
    {

#line 959
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 959
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 959
    }

#line 964
    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;

#line 966
    i_6 = 0U;

#line 966
    uint ovAcc_0 = 0U;

#line 971
    for(;;)
    {

#line 971
        if(i_6 < 16U)
        {
        }
        else
        {

#line 971
            break;
        }

#line 972
        uint idx_0 = slotToIndex_0(tid_2 * 16U + i_6);
        if(idx_0 >= winStart_2)
        {

#line 973
            live_0 = idx_0 < winEnd_2;

#line 973
        }
        else
        {

#line 973
            live_0 = false;

#line 973
        }



        float _rx_0 = float(r_5[i_6].x);

#line 977
        float _ry_0 = float(r_5[i_6].y);
        if(live_0)
        {

#line 978
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 978
        }
        else
        {

#line 978
            n2_0 = 0U;

#line 978
        }

#line 978
        myMag_0[i_6] = n2_0;

#line 984
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_6][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_6][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 971
        i_6 = i_6 + 1U;

#line 971
        ovAcc_0 = ovAcc_1;

#line 971
    }

#line 1005
    if((ovAcc_0 & 2147516416U) != 0U)
    {

#line 1005
        i_6 = 0U;
        for(;;)
        {

#line 1006
            if(i_6 < 16U)
            {
            }
            else
            {

#line 1006
                break;
            }

#line 1007
            if((myMag_0[i_6]) != 0U)
            {

#line 1007
                live_0 = true;

#line 1007
            }
            else
            {

#line 1007
                uint _S30 = slotToIndex_0(tid_2 * 16U + i_6);
                if(_S30 >= winStart_2)
                {

#line 1008
                    live_0 = _S30 < winEnd_2;

#line 1008
                }
                else
                {

#line 1008
                    live_0 = false;

#line 1008
                }

#line 1007
            }

#line 1007
            if(live_0)
            {
                myMag_0[i_6] = 2139095040U;

#line 1007
            }

#line 1006
            i_6 = i_6 + 1U;

#line 1006
        }

#line 1005
    }

#line 1005
    uint bestBits_0 = thrBits_1;

#line 1005
    i_6 = 0U;

#line 1024
    for(;;)
    {

#line 1024
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1024
            break;
        }

#line 1024
        uint _S31 = max(bestBits_0, myMag_0[i_6]);

#line 1024
        uint i_7 = i_6 + 1U;

#line 1024
        bestBits_0 = _S31;

#line 1024
        i_6 = i_7;

#line 1024
    }

#line 1039
    if(bestBits_0 > thrBits_1)
    {

#line 1039
        uint _S32 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), bestBits_0, memory_order_relaxed);

#line 1039
    }


    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1042
    uint winner_0 = 4294967295U;

#line 1042
    i_6 = 0U;

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
        if((myMag_0[i_6]) > thrBits_1)
        {

#line 1053
            live_0 = (myMag_0[i_6]) == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1053
        }
        else
        {

#line 1053
            live_0 = false;

#line 1053
        }

#line 1053
        if(live_0)
        {

#line 1053
            winner_0 = min(winner_0, tid_2 * 16U + i_6);

#line 1053
        }

#line 1052
        i_6 = i_6 + 1U;

#line 1052
    }

#line 1060
    if(winner_0 != 4294967295U)
    {

#line 1060
        uint _S33 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 1060
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1062
    i_6 = 0U;
    for(;;)
    {

#line 1063
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1063
            break;
        }

#line 1064
        uint _S34 = tid_2 * 16U + i_6;

#line 1064
        if(_S34 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])
        {

#line 1065
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S34));

#line 1065
            packed_float2 device* _S35 = peakVal_0+pair_0;

            float2 _S36 = c16Bound_0(float2(float(r_5[i_6].x), float(r_5[i_6].y)), _S28);

#line 1067
            *_S35 = packed_float2(_S36) ;

#line 1064
        }

#line 1063
        i_6 = i_6 + 1U;

#line 1063
    }

#line 1073
    if(_S29)
    {

#line 1073
        live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U]) == 4294967295U;

#line 1073
    }
    else
    {

#line 1073
        live_0 = false;

#line 1073
    }

#line 1073
    if(live_0)
    {

#line 1074
        *(peakIdx_0+pair_0) = int(-1);

#line 1074
        *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 1073
    }

#line 1107
    return;
}


#line 1498
void filterPair_0(uint pair_1, uint tid_3, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{

#line 1498
    thread uint _S37 = winStart_3;

#line 1498
    thread uint _S38 = winEnd_3;

#line 1504
    kernelContext_6->_tid_0 = tid_3;

#line 1533
    uint d_5 = pair_1 / ntmpl_1;

#line 1533
    uint _S39 = pair_1 % ntmpl_1;

#line 1538
    rowWindow_0(d_5, &_S37, &_S38);


    thread array<half2, int(16)> dreg_1;

#line 1541
    uint n2_1 = 0U;

    for(;;)
    {

#line 1543
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1543
            break;
        }

#line 1544
        dreg_1[n2_1] = dload_0(data_1, d_5 * 128U + tid_3 + 8U * n2_1);

#line 1543
        n2_1 = n2_1 + 1U;

#line 1543
    }

#line 1543
    uint k_2 = 0U;

#line 1563
    for(;;)
    {

#line 1563
        if(k_2 < 1U)
        {
        }
        else
        {

#line 1563
            break;
        }

#line 1564
        uint _S40 = pair_1 + k_2;

#line 1564
        uint _S41 = _S39 + k_2;

#line 1564
        thread array<half2, int(16)> _S42 = dreg_1;

#line 1564
        filterOne_0(_S40, d_5, _S41, tid_3, &_S42, data_1, tmpl_1, peakIdx_1, peakVal_1, _S37, _S38, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1563
        k_2 = k_2 + 1U;

#line 1563
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1571
    thread KernelContext_0 kernelContext_7;

#line 1571
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1571
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1571
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1571
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1571
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1571
    threadgroup array<uint, int(4096)> stg_1;

#line 1571
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1591
    uint _S43 = lid_0.x;

#line 1591
    uint _sub_0 = _S43 / 8U;
    uint _pr_0 = gid_0.x * 32U + _sub_0;

#line 1592
    uint _t_0 = _S43 % 8U;
    (&kernelContext_7)->_stgBase_0 = _sub_0 * 128U;

#line 1593
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);



    return;
}
