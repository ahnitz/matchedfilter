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


#line 160
half2 dload_0(uint device* b_1, uint i_1)
{


    return cload_0(b_1, i_1);
}


#line 226
half2 cmulConj_0(half2 a_0, half2 b_2)
{

#line 226
    half _S2 = a_0.x;

#line 226
    half _S3 = b_2.x;

#line 226
    half _S4 = a_0.y;

#line 226
    half _S5 = b_2.y;

#line 226
    return half2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 393
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_0)
{
    half2 t0_0 = *a_1 + *c_0;

#line 395
    half2 t1_0 = *a_1 - *c_0;

#line 395
    half2 t2_0 = *b_3 + *d_0;

#line 395
    half2 t3_0 = *b_3 - *d_0;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 397
    *b_3 = t1_0 + j3_0;

#line 397
    *c_0 = t0_0 - t2_0;

#line 397
    *d_0 = t1_0 - j3_0;
    return;
}


#line 225
half2 cmul_0(half2 a_2, half2 b_4)
{

#line 225
    half _S6 = a_2.x;

#line 225
    half _S7 = b_4.x;

#line 225
    half _S8 = a_2.y;

#line 225
    half _S9 = b_4.y;

#line 225
    return half2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 429
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125, 0.382568359375);
    half2 W2_0 = half2(0.70703125, 0.70703125);
    half2 W3_0 = half2(0.382568359375, 0.923828125);
    half2 W4_0 = half2(0.0, 1.0);
    half2 W6_0 = half2(-0.70703125, 0.70703125);
    half2 W9_0 = half2(-0.923828125, -0.382568359375);

#line 436
    uint n1_0 = 0U;
    for(;;)
    {

#line 437
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 437
            break;
        }

#line 437
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 437
        n1_0 = n1_0 + 1U;

#line 437
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 438
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 438
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 439
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 439
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 440
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 440
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 440
    uint k2_0 = 0U;
    for(;;)
    {

#line 441
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 441
            break;
        }

#line 441
        uint _S10 = 4U * k2_0;

#line 441
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 441
        k2_0 = k2_0 + 1U;

#line 441
    }

    half2 t_0 = (*r_0)[int(1)];

#line 443
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 443
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 444
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 444
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 445
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 445
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 446
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 446
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 447
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 447
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 448
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 448
    (*r_0)[int(14)] = t_5;
    return;
}


#line 17 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 227 "mm_128_fusedTierB_c16p2.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 229
    uint j_0 = d_1 / _S11;

#line 229
    uint m_0 = d_1 % _S11;

#line 229
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 230
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 230
    }
    else
    {

#line 230
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 230
    }

#line 230
    return _S12;
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


#line 203 "mm_128_fusedTierB_c16p2.slang"
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


#line 203
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 203
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 203
    return;
}


#line 204
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 204
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 589
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 590
    uint j_1;

#line 601
    thread array<half2, int(16)> out_0;

#line 601
    uint z_0 = 0U;
    for(;;)
    {

#line 602
        if(z_0 < 16U)
        {
        }
        else
        {

#line 602
            break;
        }

#line 602
        out_0[z_0] = half2(0.0, 0.0);

#line 602
        z_0 = z_0 + 1U;

#line 602
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S13 = p0_0 & lenMask_0;

#line 608
    uint _S14 = (_S13 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

#line 608
    uint c_1 = 0U;

    for(;;)
    {

#line 610
        if(c_1 < 1U)
        {
        }
        else
        {

#line 610
            break;
        }

#line 611
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 611
        j_1 = 0U;
        for(;;)
        {

#line 612
            if(j_1 < 16U)
            {
            }
            else
            {

#line 612
                break;
            }

#line 612
            stgPut_0(j_1 * 8U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 612
            j_1 = j_1 + 1U;

#line 612
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 613
        uint d_2 = 0U;
        for(;;)
        {

#line 614
            if(d_2 < 16U)
            {
            }
            else
            {

#line 614
                break;
            }

#line 615
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S15 = pz_0 & lenMask_0;
            uint az_0 = (_S15 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 617
            half2 _S16 = stgGet_0(_S14 + az_0 - c_1 * 16U * 8U, kernelContext_2);


            out_0[d_2] = _S16;

#line 614
            d_2 = d_2 + 1U;

#line 614
        }

#line 610
        c_1 = c_1 + 1U;

#line 610
    }

#line 610
    j_1 = 0U;

#line 623
    for(;;)
    {

#line 623
        if(j_1 < 16U)
        {
        }
        else
        {

#line 623
            break;
        }

#line 623
        (*r_1)[j_1] = out_0[j_1];

#line 623
        j_1 = j_1 + 1U;

#line 623
    }
    return;
}


#line 413
void dft8_0(array<half2, int(16)> thread* r_2, uint o_0)
{


    thread array<half2, int(8)> b_5;

#line 417
    uint s_0 = 1U;
    for(;;)
    {

#line 418
        if(s_0 < 8U)
        {
        }
        else
        {

#line 418
            break;
        }

#line 418
        uint j_2 = 0U;
        for(;;)
        {

#line 419
            if(j_2 < 4U)
            {
            }
            else
            {

#line 419
                break;
            }

#line 420
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S17 = o_0 + j_2;

#line 423
            half2 t_6 = cmul_0(half2(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0))), (*r_2)[_S17 + 4U]);
            uint _S18 = ((j_2 - k_0) << 1U) + k_0;

#line 424
            b_5[_S18] = (*r_2)[_S17] + t_6;

#line 424
            b_5[_S18 + s_0] = (*r_2)[_S17] - t_6;

#line 419
            j_2 = j_2 + 1U;

#line 419
        }

#line 419
        uint i_4 = 0U;

#line 426
        for(;;)
        {

#line 426
            if(i_4 < 8U)
            {
            }
            else
            {

#line 426
                break;
            }

#line 426
            (*r_2)[o_0 + i_4] = b_5[i_4];

#line 426
            i_4 = i_4 + 1U;

#line 426
        }

#line 418
        s_0 = s_0 << 1U;

#line 418
    }

#line 428
    return;
}


#line 532
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 532
    uint b_6 = 0U;

#line 540
    for(;;)
    {

#line 540
        if(b_6 < 2U)
        {
        }
        else
        {

#line 540
            break;
        }

#line 540
        dft8_0(r_3, b_6 * 8U);

#line 540
        b_6 = b_6 + 1U;

#line 540
    }



    return;
}


#line 679
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 679
    for(;;)
    {

#line 679
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

#line 682 "mm_128_fusedTierB_c16p2.slang"
    return;
}


#line 648
uint lgOf_0(uint i_5)
{

#line 648
    uint _S23;

#line 648
    if(i_5 < 1U)
    {

#line 648
        _S23 = 4U;

#line 648
    }
    else
    {

#line 648
        if(i_5 == 1U)
        {

#line 648
            _S23 = 3U;

#line 648
        }
        else
        {

#line 648
            _S23 = 1U;

#line 648
        }

#line 648
    }

#line 648
    return _S23;
}


#line 650
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 654
    uint lg_1 = lgOf_0(0U);

#line 659
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 688
void filterOne_0(uint pair_0, uint d_3, uint t_7, uint tid_1, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{


    bool live_0;

#line 711
    thread array<half2, int(16)> r_5;

#line 711
    uint n2_0 = 0U;



    for(;;)
    {

#line 715
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 715
            break;
        }

#line 716
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_7 * 128U + tid_1 + 8U * n2_0));

#line 715
        n2_0 = n2_0 + 1U;

#line 715
    }

#line 715
    transform_0(&r_5, tid_1, kernelContext_4);

#line 741
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 813
    bool _S24 = tid_1 == 0U;

#line 813
    if(_S24)
    {

#line 813
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 813
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 813
    }

#line 818
    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;

#line 820
    uint i_6 = 0U;

    for(;;)
    {

#line 822
        if(i_6 < 16U)
        {
        }
        else
        {

#line 822
            break;
        }

#line 823
        uint idx_0 = slotToIndex_0(tid_1 * 16U + i_6);
        if(idx_0 >= winStart_1)
        {

#line 824
            live_0 = idx_0 < winEnd_1;

#line 824
        }
        else
        {

#line 824
            live_0 = false;

#line 824
        }



        float _rx_0 = float(r_5[i_6].x);

#line 828
        float _ry_0 = float(r_5[i_6].y);
        if(live_0)
        {

#line 829
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 829
        }
        else
        {

#line 829
            n2_0 = 0U;

#line 829
        }

#line 829
        myMag_0[i_6] = n2_0;

#line 822
        i_6 = i_6 + 1U;

#line 822
    }

#line 822
    uint bestBits_0 = thrBits_1;

#line 822
    i_6 = 0U;

#line 857
    for(;;)
    {

#line 857
        if(i_6 < 16U)
        {
        }
        else
        {

#line 857
            break;
        }

#line 857
        uint _S25 = max(bestBits_0, myMag_0[i_6]);

#line 857
        uint i_7 = i_6 + 1U;

#line 857
        bestBits_0 = _S25;

#line 857
        i_6 = i_7;

#line 857
    }

#line 872
    if(bestBits_0 > thrBits_1)
    {

#line 872
        uint _S26 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), bestBits_0, memory_order_relaxed);

#line 872
    }


    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 875
    uint winner_0 = 4294967295U;

#line 875
    i_6 = 0U;

#line 885
    for(;;)
    {

#line 885
        if(i_6 < 16U)
        {
        }
        else
        {

#line 885
            break;
        }

#line 886
        if((myMag_0[i_6]) > thrBits_1)
        {

#line 886
            live_0 = (myMag_0[i_6]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 886
        }
        else
        {

#line 886
            live_0 = false;

#line 886
        }

#line 886
        if(live_0)
        {

#line 886
            winner_0 = min(winner_0, tid_1 * 16U + i_6);

#line 886
        }

#line 885
        i_6 = i_6 + 1U;

#line 885
    }

#line 893
    if(winner_0 != 4294967295U)
    {

#line 893
        uint _S27 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 893
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 895
    i_6 = 0U;
    for(;;)
    {

#line 896
        if(i_6 < 16U)
        {
        }
        else
        {

#line 896
            break;
        }

#line 897
        uint _S28 = tid_1 * 16U + i_6;

#line 897
        if(_S28 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
        {

#line 898
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S28));

#line 898
            *(peakVal_0+pair_0) = packed_float2(float2(float(r_5[i_6].x), float(r_5[i_6].y))) ;

#line 897
        }

#line 896
        i_6 = i_6 + 1U;

#line 896
    }

#line 902
    if(_S24)
    {

#line 902
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 902
    }
    else
    {

#line 902
        live_0 = false;

#line 902
    }

#line 902
    if(live_0)
    {

#line 903
        *(peakIdx_0+pair_0) = int(-1);

#line 903
        *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 902
    }

#line 936
    return;
}


#line 1161
void filterPair_0(uint pair_1, uint tid_2, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_5)
{

#line 1167
    kernelContext_5->_tid_0 = tid_2;

#line 1195
    uint _S29 = pair_1 / ntmpl_1;

#line 1195
    uint _S30 = pair_1 % ntmpl_1;

    thread array<half2, int(16)> dreg_1;

#line 1197
    uint n2_1 = 0U;

    for(;;)
    {

#line 1199
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1199
            break;
        }

#line 1200
        dreg_1[n2_1] = dload_0(data_1, _S29 * 128U + tid_2 + 8U * n2_1);

#line 1199
        n2_1 = n2_1 + 1U;

#line 1199
    }

#line 1199
    uint k_1 = 0U;

#line 1219
    for(;;)
    {

#line 1219
        if(k_1 < 1U)
        {
        }
        else
        {

#line 1219
            break;
        }

#line 1220
        uint _S31 = pair_1 + k_1;

#line 1220
        uint _S32 = _S30 + k_1;

#line 1220
        thread array<half2, int(16)> _S33 = dreg_1;

#line 1220
        filterOne_0(_S31, _S29, _S32, tid_2, &_S33, data_1, tmpl_1, peakIdx_1, peakVal_1, winStart_2, winEnd_2, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_5);

#line 1219
        k_1 = k_1 + 1U;

#line 1219
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1227
    thread KernelContext_0 kernelContext_6;

#line 1227
    (&kernelContext_6)->entryPointParams_0 = entryPointParams_1;

#line 1227
    (&kernelContext_6)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1227
    (&kernelContext_6)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1227
    (&kernelContext_6)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1227
    (&kernelContext_6)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1227
    threadgroup array<uint, int(256)> stg_1;

#line 1227
    (&kernelContext_6)->stg_0 = &stg_1;

#line 1247
    uint _S34 = lid_0.x;

#line 1247
    uint _sub_0 = _S34 / 8U;
    uint _pr_0 = gid_0.x * 2U + _sub_0;

#line 1248
    uint _t_0 = _S34 % 8U;
    (&kernelContext_6)->_stgBase_0 = _sub_0 * 128U;

#line 1249
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_6);



    return;
}
