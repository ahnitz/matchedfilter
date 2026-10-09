#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;

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


#line 148 "mm_128_fusedTierB_c16p2.slang"
half2 cload_0(uint device* b_0, uint i_0)
{

#line 149
    uint p_0 = b_0[i_0];

#line 149
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 207
half2 cmulConj_0(half2 a_0, half2 b_1)
{

#line 207
    half _S2 = a_0.x;

#line 207
    half _S3 = b_1.x;

#line 207
    half _S4 = a_0.y;

#line 207
    half _S5 = b_1.y;

#line 207
    return half2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 374
void r4_0(half2 thread* a_1, half2 thread* b_2, half2 thread* c_0, half2 thread* d_0)
{
    half2 t0_0 = *a_1 + *c_0;

#line 376
    half2 t1_0 = *a_1 - *c_0;

#line 376
    half2 t2_0 = *b_2 + *d_0;

#line 376
    half2 t3_0 = *b_2 - *d_0;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 378
    *b_2 = t1_0 + j3_0;

#line 378
    *c_0 = t0_0 - t2_0;

#line 378
    *d_0 = t1_0 - j3_0;
    return;
}


#line 206
half2 cmul_0(half2 a_2, half2 b_3)
{

#line 206
    half _S6 = a_2.x;

#line 206
    half _S7 = b_3.x;

#line 206
    half _S8 = a_2.y;

#line 206
    half _S9 = b_3.y;

#line 206
    return half2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 410
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125, 0.382568359375);
    half2 W2_0 = half2(0.70703125, 0.70703125);
    half2 W3_0 = half2(0.382568359375, 0.923828125);
    half2 W4_0 = half2(0.0, 1.0);
    half2 W6_0 = half2(-0.70703125, 0.70703125);
    half2 W9_0 = half2(-0.923828125, -0.382568359375);

#line 417
    uint n1_0 = 0U;
    for(;;)
    {

#line 418
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 418
            break;
        }

#line 418
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 418
        n1_0 = n1_0 + 1U;

#line 418
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 419
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 419
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 420
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 420
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 421
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 421
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 421
    uint k2_0 = 0U;
    for(;;)
    {

#line 422
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 422
            break;
        }

#line 422
        uint _S10 = 4U * k2_0;

#line 422
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 422
        k2_0 = k2_0 + 1U;

#line 422
    }

    half2 t_0 = (*r_0)[int(1)];

#line 424
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 424
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 425
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 425
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 426
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 426
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 427
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 427
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 428
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 428
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 429
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 429
    (*r_0)[int(14)] = t_5;
    return;
}


#line 12 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
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


#line 189 "mm_128_fusedTierB_c16p2.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(256)> threadgroup* stg_0;
};


#line 189
void stgPut_0(uint i_1, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 189
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_1] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 189
    return;
}


#line 208
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 210
    uint j_0 = d_1 / _S11;

#line 210
    uint m_0 = d_1 % _S11;

#line 210
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 211
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 211
    }
    else
    {

#line 211
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 211
    }

#line 211
    return _S12;
}


#line 190
half2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 190
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_2]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_2]) >> 16U) & 65535U)));
}


#line 570
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 571
    uint j_1;

#line 582
    thread array<half2, int(16)> out_0;

#line 582
    uint z_0 = 0U;
    for(;;)
    {

#line 583
        if(z_0 < 16U)
        {
        }
        else
        {

#line 583
            break;
        }

#line 583
        out_0[z_0] = half2(0.0, 0.0);

#line 583
        z_0 = z_0 + 1U;

#line 583
    }
    uint _S13 = (1U << lgSpan_0) - 1U;
    uint _S14 = (1U << lgLen_0) - 1U;

#line 585
    uint c_1 = 0U;
    for(;;)
    {

#line 586
        if(c_1 < 1U)
        {
        }
        else
        {

#line 586
            break;
        }

#line 587
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 587
        j_1 = 0U;
        for(;;)
        {

#line 588
            if(j_1 < 16U)
            {
            }
            else
            {

#line 588
                break;
            }

#line 588
            stgPut_0(j_1 * 8U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 588
            j_1 = j_1 + 1U;

#line 588
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 589
        uint d_2 = 0U;
        for(;;)
        {

#line 590
            if(d_2 < 16U)
            {
            }
            else
            {

#line 590
                break;
            }

#line 591
            uint p_1 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
            uint b_4 = p_1 >> lgLen_0;

#line 592
            uint rem_0 = p_1 & _S14;
            uint i_3 = rem_0 >> lgSpan_0;

#line 593
            uint ln_0 = rem_0 & _S13;
            uint _S15 = c_1 * 16U;

#line 594
            bool _S16;

#line 594
            if(i_3 >= _S15)
            {

#line 594
                _S16 = i_3 < ((c_1 + 1U) * 16U);

#line 594
            }
            else
            {

#line 594
                _S16 = false;

#line 594
            }

#line 594
            if(_S16)
            {

#line 594
                half2 _S17 = stgGet_0((i_3 - _S15) * 8U + (b_4 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_2] = _S17;

#line 594
            }

#line 590
            d_2 = d_2 + 1U;

#line 590
        }

#line 586
        c_1 = c_1 + 1U;

#line 586
    }

#line 586
    j_1 = 0U;

#line 598
    for(;;)
    {

#line 598
        if(j_1 < 16U)
        {
        }
        else
        {

#line 598
            break;
        }

#line 598
        (*r_1)[j_1] = out_0[j_1];

#line 598
        j_1 = j_1 + 1U;

#line 598
    }
    return;
}


#line 394
void dft8_0(array<half2, int(16)> thread* r_2, uint o_0)
{


    thread array<half2, int(8)> b_5;

#line 398
    uint s_0 = 1U;
    for(;;)
    {

#line 399
        if(s_0 < 8U)
        {
        }
        else
        {

#line 399
            break;
        }

#line 399
        uint j_2 = 0U;
        for(;;)
        {

#line 400
            if(j_2 < 4U)
            {
            }
            else
            {

#line 400
                break;
            }

#line 401
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S18 = o_0 + j_2;

#line 404
            half2 t_6 = cmul_0(half2(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0))), (*r_2)[_S18 + 4U]);
            uint _S19 = ((j_2 - k_0) << 1U) + k_0;

#line 405
            b_5[_S19] = (*r_2)[_S18] + t_6;

#line 405
            b_5[_S19 + s_0] = (*r_2)[_S18] - t_6;

#line 400
            j_2 = j_2 + 1U;

#line 400
        }

#line 400
        uint i_4 = 0U;

#line 407
        for(;;)
        {

#line 407
            if(i_4 < 8U)
            {
            }
            else
            {

#line 407
                break;
            }

#line 407
            (*r_2)[o_0 + i_4] = b_5[i_4];

#line 407
            i_4 = i_4 + 1U;

#line 407
        }

#line 399
        s_0 = s_0 << 1U;

#line 399
    }

#line 409
    return;
}


#line 513
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 513
    uint b_6 = 0U;

#line 521
    for(;;)
    {

#line 521
        if(b_6 < 2U)
        {
        }
        else
        {

#line 521
            break;
        }

#line 521
        dft8_0(r_3, b_6 * 8U);

#line 521
        b_6 = b_6 + 1U;

#line 521
    }



    return;
}


#line 654
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 654
    for(;;)
    {

#line 654
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
                float _S20 = tw_0.x;

#line 27
                float _S21 = tw_0.y;

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
                    float nr_0 = cr_0 * _S20 - ci_0 * _S21;
                    float _S22 = cr_0 * _S21 + ci_0 * _S20;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S22;

#line 29
                }

#line 37
                uint per_2 = 16U / max(8U, 1U);
                uint _S23 = max(0U, 1U);
                uint blk2_2 = tid_0 / _S23;

#line 39
                uint lane2_2 = tid_0 % _S23;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 8U, 128U, blk_2, lane_2, per_2, _S23, 8U, blk2_2, lane2_2, kernelContext_3);

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

#line 657 "mm_128_fusedTierB_c16p2.slang"
    return;
}


#line 623
uint lgOf_0(uint i_5)
{

#line 623
    uint _S24;

#line 623
    if(i_5 < 1U)
    {

#line 623
        _S24 = 4U;

#line 623
    }
    else
    {

#line 623
        if(i_5 == 1U)
        {

#line 623
            _S24 = 3U;

#line 623
        }
        else
        {

#line 623
            _S24 = 1U;

#line 623
        }

#line 623
    }

#line 623
    return _S24;
}


#line 625
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 629
    uint lg_1 = lgOf_0(0U);

#line 634
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 663
void filterOne_0(uint pair_0, uint d_3, uint t_7, uint tid_1, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{


    bool live_0;

#line 686
    thread array<half2, int(16)> r_5;

#line 686
    uint n2_0 = 0U;



    for(;;)
    {

#line 690
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 690
            break;
        }

#line 691
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_7 * 128U + tid_1 + 8U * n2_0));

#line 690
        n2_0 = n2_0 + 1U;

#line 690
    }

#line 690
    transform_0(&r_5, tid_1, kernelContext_4);

#line 716
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 788
    bool _S25 = tid_1 == 0U;

#line 788
    if(_S25)
    {

#line 788
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 788
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 788
    }

#line 793
    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;

#line 795
    uint i_6 = 0U;

    for(;;)
    {

#line 797
        if(i_6 < 16U)
        {
        }
        else
        {

#line 797
            break;
        }

#line 798
        uint idx_0 = slotToIndex_0(tid_1 * 16U + i_6);
        if(idx_0 >= winStart_1)
        {

#line 799
            live_0 = idx_0 < winEnd_1;

#line 799
        }
        else
        {

#line 799
            live_0 = false;

#line 799
        }



        float _rx_0 = float(r_5[i_6].x);

#line 803
        float _ry_0 = float(r_5[i_6].y);
        if(live_0)
        {

#line 804
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 804
        }
        else
        {

#line 804
            n2_0 = 0U;

#line 804
        }

#line 804
        myMag_0[i_6] = n2_0;

#line 797
        i_6 = i_6 + 1U;

#line 797
    }

#line 797
    uint bestBits_0 = thrBits_1;

#line 797
    i_6 = 0U;

#line 832
    for(;;)
    {

#line 832
        if(i_6 < 16U)
        {
        }
        else
        {

#line 832
            break;
        }

#line 832
        uint _S26 = max(bestBits_0, myMag_0[i_6]);

#line 832
        uint i_7 = i_6 + 1U;

#line 832
        bestBits_0 = _S26;

#line 832
        i_6 = i_7;

#line 832
    }

#line 847
    if(bestBits_0 > thrBits_1)
    {

#line 847
        uint _S27 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), bestBits_0, memory_order_relaxed);

#line 847
    }


    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 850
    uint winner_0 = 4294967295U;

#line 850
    i_6 = 0U;

#line 860
    for(;;)
    {

#line 860
        if(i_6 < 16U)
        {
        }
        else
        {

#line 860
            break;
        }

#line 861
        if((myMag_0[i_6]) > thrBits_1)
        {

#line 861
            live_0 = (myMag_0[i_6]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 861
        }
        else
        {

#line 861
            live_0 = false;

#line 861
        }

#line 861
        if(live_0)
        {

#line 861
            winner_0 = min(winner_0, tid_1 * 16U + i_6);

#line 861
        }

#line 860
        i_6 = i_6 + 1U;

#line 860
    }

#line 868
    if(winner_0 != 4294967295U)
    {

#line 868
        uint _S28 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 868
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 870
    i_6 = 0U;
    for(;;)
    {

#line 871
        if(i_6 < 16U)
        {
        }
        else
        {

#line 871
            break;
        }

#line 872
        uint _S29 = tid_1 * 16U + i_6;

#line 872
        if(_S29 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
        {

#line 873
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S29));

#line 873
            *(peakVal_0+pair_0) = packed_float2(float2(float(r_5[i_6].x), float(r_5[i_6].y))) ;

#line 872
        }

#line 871
        i_6 = i_6 + 1U;

#line 871
    }

#line 877
    if(_S25)
    {

#line 877
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 877
    }
    else
    {

#line 877
        live_0 = false;

#line 877
    }

#line 877
    if(live_0)
    {

#line 878
        *(peakIdx_0+pair_0) = int(-1);

#line 878
        *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 877
    }

#line 911
    return;
}


#line 1136
void filterPair_0(uint pair_1, uint tid_2, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_5)
{

#line 1142
    kernelContext_5->_tid_0 = tid_2;

#line 1170
    uint _S30 = pair_1 / ntmpl_1;

#line 1170
    uint _S31 = pair_1 % ntmpl_1;

    thread array<half2, int(16)> dreg_1;

#line 1172
    uint n2_1 = 0U;

    for(;;)
    {

#line 1174
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1174
            break;
        }

#line 1175
        dreg_1[n2_1] = cload_0(data_1, _S30 * 128U + tid_2 + 8U * n2_1);

#line 1174
        n2_1 = n2_1 + 1U;

#line 1174
    }

#line 1174
    uint k_1 = 0U;

#line 1194
    for(;;)
    {

#line 1194
        if(k_1 < 1U)
        {
        }
        else
        {

#line 1194
            break;
        }

#line 1195
        uint _S32 = pair_1 + k_1;

#line 1195
        uint _S33 = _S31 + k_1;

#line 1195
        thread array<half2, int(16)> _S34 = dreg_1;

#line 1195
        filterOne_0(_S32, _S30, _S33, tid_2, &_S34, data_1, tmpl_1, peakIdx_1, peakVal_1, winStart_2, winEnd_2, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_5);

#line 1194
        k_1 = k_1 + 1U;

#line 1194
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1202
    thread KernelContext_0 kernelContext_6;

#line 1202
    (&kernelContext_6)->entryPointParams_0 = entryPointParams_1;

#line 1202
    (&kernelContext_6)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1202
    (&kernelContext_6)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1202
    (&kernelContext_6)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1202
    (&kernelContext_6)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1202
    threadgroup array<uint, int(256)> stg_1;

#line 1202
    (&kernelContext_6)->stg_0 = &stg_1;

#line 1222
    uint _S35 = lid_0.x;

#line 1222
    uint _sub_0 = _S35 / 8U;
    uint _pr_0 = gid_0.x * 2U + _sub_0;

#line 1223
    uint _t_0 = _S35 % 8U;
    (&kernelContext_6)->_stgBase_0 = _sub_0 * 128U;

#line 1224
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_6);



    return;
}
