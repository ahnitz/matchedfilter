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


#line 148 "mm_512_fusedTierB_c16p4.slang"
half2 cload_0(uint device* b_0, uint i_0)
{

#line 149
    uint p_0 = b_0[i_0];

#line 149
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 213
half2 cmulConj_0(half2 a_0, half2 b_1)
{

#line 213
    half _S2 = a_0.x;

#line 213
    half _S3 = b_1.x;

#line 213
    half _S4 = a_0.y;

#line 213
    half _S5 = b_1.y;

#line 213
    return half2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 380
void r4_0(half2 thread* a_1, half2 thread* b_2, half2 thread* c_0, half2 thread* d_0)
{
    half2 t0_0 = *a_1 + *c_0;

#line 382
    half2 t1_0 = *a_1 - *c_0;

#line 382
    half2 t2_0 = *b_2 + *d_0;

#line 382
    half2 t3_0 = *b_2 - *d_0;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 384
    *b_2 = t1_0 + j3_0;

#line 384
    *c_0 = t0_0 - t2_0;

#line 384
    *d_0 = t1_0 - j3_0;
    return;
}


#line 212
half2 cmul_0(half2 a_2, half2 b_3)
{

#line 212
    half _S6 = a_2.x;

#line 212
    half _S7 = b_3.x;

#line 212
    half _S8 = a_2.y;

#line 212
    half _S9 = b_3.y;

#line 212
    return half2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 416
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125, 0.382568359375);
    half2 W2_0 = half2(0.70703125, 0.70703125);
    half2 W3_0 = half2(0.382568359375, 0.923828125);
    half2 W4_0 = half2(0.0, 1.0);
    half2 W6_0 = half2(-0.70703125, 0.70703125);
    half2 W9_0 = half2(-0.923828125, -0.382568359375);

#line 423
    uint n1_0 = 0U;
    for(;;)
    {

#line 424
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 424
            break;
        }

#line 424
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 424
        n1_0 = n1_0 + 1U;

#line 424
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 425
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 425
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 426
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 426
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 427
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 427
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 427
    uint k2_0 = 0U;
    for(;;)
    {

#line 428
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 428
            break;
        }

#line 428
        uint _S10 = 4U * k2_0;

#line 428
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 428
        k2_0 = k2_0 + 1U;

#line 428
    }

    half2 t_0 = (*r_0)[int(1)];

#line 430
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 430
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 431
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 431
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 432
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 432
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 433
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 433
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 434
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 434
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 435
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 435
    (*r_0)[int(14)] = t_5;
    return;
}


#line 12 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 214 "mm_512_fusedTierB_c16p4.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 216
    uint j_0 = d_1 / _S11;

#line 216
    uint m_0 = d_1 % _S11;

#line 216
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 217
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 217
    }
    else
    {

#line 217
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 217
    }

#line 217
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


#line 190 "mm_512_fusedTierB_c16p4.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 190
void stgPut_0(uint i_1, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 190
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_1] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 190
    return;
}


#line 191
half2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 191
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_2]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_2]) >> 16U) & 65535U)));
}


#line 576
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 577
    uint j_1;

#line 588
    thread array<half2, int(16)> out_0;

#line 588
    uint z_0 = 0U;
    for(;;)
    {

#line 589
        if(z_0 < 16U)
        {
        }
        else
        {

#line 589
            break;
        }

#line 589
        out_0[z_0] = half2(0.0, 0.0);

#line 589
        z_0 = z_0 + 1U;

#line 589
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S13 = p0_0 & lenMask_0;

#line 595
    uint _S14 = (_S13 >> lgSpan_0) * 32U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

#line 595
    uint c_1 = 0U;

    for(;;)
    {

#line 597
        if(c_1 < 1U)
        {
        }
        else
        {

#line 597
            break;
        }

#line 598
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 598
        j_1 = 0U;
        for(;;)
        {

#line 599
            if(j_1 < 16U)
            {
            }
            else
            {

#line 599
                break;
            }

#line 599
            stgPut_0(j_1 * 32U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 599
            j_1 = j_1 + 1U;

#line 599
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 600
        uint d_2 = 0U;
        for(;;)
        {

#line 601
            if(d_2 < 16U)
            {
            }
            else
            {

#line 601
                break;
            }

#line 602
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S15 = pz_0 & lenMask_0;
            uint az_0 = (_S15 >> lgSpan_0) * 32U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 604
            half2 _S16 = stgGet_0(_S14 + az_0 - c_1 * 16U * 32U, kernelContext_2);


            out_0[d_2] = _S16;

#line 601
            d_2 = d_2 + 1U;

#line 601
        }

#line 597
        c_1 = c_1 + 1U;

#line 597
    }

#line 597
    j_1 = 0U;

#line 610
    for(;;)
    {

#line 610
        if(j_1 < 16U)
        {
        }
        else
        {

#line 610
            break;
        }

#line 610
        (*r_1)[j_1] = out_0[j_1];

#line 610
        j_1 = j_1 + 1U;

#line 610
    }
    return;
}


#line 391
void dft2_0(array<half2, int(16)> thread* r_2, uint o_0)
{
    half2 a_3 = (*r_2)[o_0];

#line 393
    half2 b_4 = (*r_2)[o_0 + 1U];

#line 393
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 393
    (*r_2)[o_0 + 1U] = a_3 - b_4;
    return;
}


#line 519
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 519
    uint b_5 = 0U;

#line 529
    for(;;)
    {

#line 529
        if(b_5 < 8U)
        {
        }
        else
        {

#line 529
            break;
        }

#line 529
        dft2_0(r_3, b_5 * 2U);

#line 529
        b_5 = b_5 + 1U;

#line 529
    }

    return;
}


#line 666
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 666
    uint _S17;

#line 666
    uint k2_1;

#line 666
    float cr_0;

#line 666
    float ci_0;

#line 666
    uint _S18;

#line 666
    for(;;)
    {

#line 666
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

#line 669 "mm_512_fusedTierB_c16p4.slang"
    return;
}


#line 635
uint lgOf_0(uint i_3)
{

#line 635
    uint _S27;

#line 635
    if(i_3 < 2U)
    {

#line 635
        _S27 = 4U;

#line 635
    }
    else
    {

#line 635
        _S27 = 1U;

#line 635
    }

#line 635
    return _S27;
}


#line 637
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 641
    uint lg_1 = lgOf_0(1U);

#line 641
    uint lg_2 = lgOf_0(0U);

#line 646
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 675
void filterOne_0(uint pair_0, uint d_3, uint t_6, uint tid_1, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{


    bool live_0;

#line 698
    thread array<half2, int(16)> r_5;

#line 698
    uint n2_0 = 0U;



    for(;;)
    {

#line 702
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 702
            break;
        }

#line 703
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_6 * 512U + tid_1 + 32U * n2_0));

#line 702
        n2_0 = n2_0 + 1U;

#line 702
    }

#line 702
    transform_0(&r_5, tid_1, kernelContext_4);

#line 728
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 800
    bool _S28 = tid_1 == 0U;

#line 800
    if(_S28)
    {

#line 800
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 800
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 800
    }

#line 805
    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;

#line 807
    uint i_4 = 0U;

    for(;;)
    {

#line 809
        if(i_4 < 16U)
        {
        }
        else
        {

#line 809
            break;
        }

#line 810
        uint idx_0 = slotToIndex_0(tid_1 * 16U + i_4);
        if(idx_0 >= winStart_1)
        {

#line 811
            live_0 = idx_0 < winEnd_1;

#line 811
        }
        else
        {

#line 811
            live_0 = false;

#line 811
        }



        float _rx_0 = float(r_5[i_4].x);

#line 815
        float _ry_0 = float(r_5[i_4].y);
        if(live_0)
        {

#line 816
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 816
        }
        else
        {

#line 816
            n2_0 = 0U;

#line 816
        }

#line 816
        myMag_0[i_4] = n2_0;

#line 809
        i_4 = i_4 + 1U;

#line 809
    }

#line 809
    uint bestBits_0 = thrBits_1;

#line 809
    i_4 = 0U;

#line 844
    for(;;)
    {

#line 844
        if(i_4 < 16U)
        {
        }
        else
        {

#line 844
            break;
        }

#line 844
        uint _S29 = max(bestBits_0, myMag_0[i_4]);

#line 844
        uint i_5 = i_4 + 1U;

#line 844
        bestBits_0 = _S29;

#line 844
        i_4 = i_5;

#line 844
    }

#line 859
    if(bestBits_0 > thrBits_1)
    {

#line 859
        uint _S30 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), bestBits_0, memory_order_relaxed);

#line 859
    }


    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 862
    uint winner_0 = 4294967295U;

#line 862
    i_4 = 0U;

#line 872
    for(;;)
    {

#line 872
        if(i_4 < 16U)
        {
        }
        else
        {

#line 872
            break;
        }

#line 873
        if((myMag_0[i_4]) > thrBits_1)
        {

#line 873
            live_0 = (myMag_0[i_4]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 873
        }
        else
        {

#line 873
            live_0 = false;

#line 873
        }

#line 873
        if(live_0)
        {

#line 873
            winner_0 = min(winner_0, tid_1 * 16U + i_4);

#line 873
        }

#line 872
        i_4 = i_4 + 1U;

#line 872
    }

#line 880
    if(winner_0 != 4294967295U)
    {

#line 880
        uint _S31 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 880
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 882
    i_4 = 0U;
    for(;;)
    {

#line 883
        if(i_4 < 16U)
        {
        }
        else
        {

#line 883
            break;
        }

#line 884
        uint _S32 = tid_1 * 16U + i_4;

#line 884
        if(_S32 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
        {

#line 885
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S32));

#line 885
            *(peakVal_0+pair_0) = packed_float2(float2(float(r_5[i_4].x), float(r_5[i_4].y))) ;

#line 884
        }

#line 883
        i_4 = i_4 + 1U;

#line 883
    }

#line 889
    if(_S28)
    {

#line 889
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 889
    }
    else
    {

#line 889
        live_0 = false;

#line 889
    }

#line 889
    if(live_0)
    {

#line 890
        *(peakIdx_0+pair_0) = int(-1);

#line 890
        *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 889
    }

#line 923
    return;
}


#line 1148
void filterPair_0(uint pair_1, uint tid_2, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_5)
{

#line 1154
    kernelContext_5->_tid_0 = tid_2;

#line 1182
    uint _S33 = pair_1 / ntmpl_1;

#line 1182
    uint _S34 = pair_1 % ntmpl_1;

    thread array<half2, int(16)> dreg_1;

#line 1184
    uint n2_1 = 0U;

    for(;;)
    {

#line 1186
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1186
            break;
        }

#line 1187
        dreg_1[n2_1] = cload_0(data_1, _S33 * 512U + tid_2 + 32U * n2_1);

#line 1186
        n2_1 = n2_1 + 1U;

#line 1186
    }

#line 1186
    uint k_0 = 0U;

#line 1206
    for(;;)
    {

#line 1206
        if(k_0 < 1U)
        {
        }
        else
        {

#line 1206
            break;
        }

#line 1207
        uint _S35 = pair_1 + k_0;

#line 1207
        uint _S36 = _S34 + k_0;

#line 1207
        thread array<half2, int(16)> _S37 = dreg_1;

#line 1207
        filterOne_0(_S35, _S33, _S36, tid_2, &_S37, data_1, tmpl_1, peakIdx_1, peakVal_1, winStart_2, winEnd_2, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_5);

#line 1206
        k_0 = k_0 + 1U;

#line 1206
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1214
    thread KernelContext_0 kernelContext_6;

#line 1214
    (&kernelContext_6)->entryPointParams_0 = entryPointParams_1;

#line 1214
    (&kernelContext_6)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1214
    (&kernelContext_6)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1214
    (&kernelContext_6)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1214
    (&kernelContext_6)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1214
    threadgroup array<uint, int(2048)> stg_1;

#line 1214
    (&kernelContext_6)->stg_0 = &stg_1;

#line 1234
    uint _S38 = lid_0.x;

#line 1234
    uint _sub_0 = _S38 / 32U;
    uint _pr_0 = gid_0.x * 4U + _sub_0;

#line 1235
    uint _t_0 = _S38 % 32U;
    (&kernelContext_6)->_stgBase_0 = _sub_0 * 512U;

#line 1236
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_6);



    return;
}
