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


#line 152 "mm_1024_fusedTierB_onebin.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 152
    return float2(*(b_0+i_0)) ;
}


#line 207
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 207
    float _S2 = a_0.x;

#line 207
    float _S3 = b_1.x;

#line 207
    float _S4 = a_0.y;

#line 207
    float _S5 = b_1.y;

#line 207
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 374
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 376
    float2 t1_0 = *a_1 - *c_0;

#line 376
    float2 t2_0 = *b_2 + *d_0;

#line 376
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
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
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 206
    float _S6 = a_2.x;

#line 206
    float _S7 = b_3.x;

#line 206
    float _S8 = a_2.y;

#line 206
    float _S9 = b_3.y;

#line 206
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 410
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

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

    float2 t_0 = (*r_0)[int(1)];

#line 424
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 424
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 425
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 425
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 426
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 426
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 427
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 427
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 428
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 428
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

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


#line 8402 "hlsl.meta.slang"
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


#line 195 "mm_1024_fusedTierB_onebin.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 195
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 195
    uint _S11 = 2U * i_1;

#line 195
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11] = (as_type<uint>((v_0.x)));

#line 195
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11 + 1U] = (as_type<uint>((v_0.y)));

#line 195
    return;
}


#line 208
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 210
    uint j_0 = d_1 / _S12;

#line 210
    uint m_0 = d_1 % _S12;

#line 210
    uint _S13;
    if(TB_0 <= 16U)
    {

#line 211
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 211
    }
    else
    {

#line 211
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 211
    }

#line 211
    return _S13;
}


#line 196
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 196
    uint _S14 = 2U * i_2;

#line 196
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 570
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 571
    uint j_1;

#line 582
    thread array<float2, int(16)> out_0;

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
        out_0[z_0] = float2(0.0, 0.0);

#line 583
        z_0 = z_0 + 1U;

#line 583
    }
    uint _S15 = (1U << lgSpan_0) - 1U;
    uint _S16 = (1U << lgLen_0) - 1U;

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
            stgPut_0(j_1 * 64U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

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
            uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
            uint b_4 = p_0 >> lgLen_0;

#line 592
            uint rem_0 = p_0 & _S16;
            uint i_3 = rem_0 >> lgSpan_0;

#line 593
            uint ln_0 = rem_0 & _S15;
            uint _S17 = c_1 * 16U;

#line 594
            bool _S18;

#line 594
            if(i_3 >= _S17)
            {

#line 594
                _S18 = i_3 < ((c_1 + 1U) * 16U);

#line 594
            }
            else
            {

#line 594
                _S18 = false;

#line 594
            }

#line 594
            if(_S18)
            {

#line 594
                float2 _S19 = stgGet_0((i_3 - _S17) * 64U + (b_4 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_2] = _S19;

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


#line 389
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 392
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 392
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 513
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 513
    uint b_5 = 0U;

#line 522
    for(;;)
    {

#line 522
        if(b_5 < 4U)
        {
        }
        else
        {

#line 522
            break;
        }

#line 522
        dft4_0(r_3, b_5 * 4U);

#line 522
        b_5 = b_5 + 1U;

#line 522
    }


    return;
}


#line 654
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 654
    uint _S20;

#line 654
    uint k2_1;

#line 654
    float cr_0;

#line 654
    float ci_0;

#line 654
    uint _S21;

#line 654
    for(;;)
    {

#line 654
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(64U);

#line 11
                _S20 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(1024U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 63U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 1024.0);
                float _S22 = tw_0.x;

#line 27
                float _S23 = tw_0.y;

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
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S22 - ci_0 * _S23;
                    float _S24 = cr_0 * _S23 + ci_0 * _S22;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S24;

#line 29
                }

#line 37
                uint per_2 = 16U / max(64U, 1U);
                uint _S25 = max(4U, 1U);

#line 38
                _S21 = _S25;
                uint blk2_2 = tid_0 / _S25;

#line 39
                uint lane2_2 = tid_0 % _S25;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 64U, 1024U, blk_2, lane_2, per_2, _S25, 64U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(4U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 3U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 64.0);
                float _S26 = tw_1.x;

#line 27
                float _S27 = tw_1.y;

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
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S26 - ci_0 * _S27;
                    float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S28;

#line 29
                }

#line 37
                uint per_3 = 16U / _S21;
                uint _S29 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S29;

#line 39
                uint lane2_3 = tid_0 % _S29;

#line 39
                exchange_0(r_4, _S20, lgTB_1, 4U, 64U, blk_3, lane_3, per_3, _S29, 4U, blk2_3, lane2_3, kernelContext_3);

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

#line 657 "mm_1024_fusedTierB_onebin.slang"
    return;
}


#line 623
uint lgOf_0(uint i_4)
{

#line 623
    uint _S30;

#line 623
    if(i_4 < 2U)
    {

#line 623
        _S30 = 4U;

#line 623
    }
    else
    {

#line 623
        _S30 = 1U;

#line 623
    }

#line 623
    return _S30;
}


#line 625
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 629
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 629
    uint lg_2 = lgOf_0(1U);

#line 629
    uint lg_3 = lgOf_0(0U);

#line 634
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 669
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 683
    kernelContext_4->_tid_0 = tid_1;
    uint _S31 = pair_0 / ntmpl_1;

#line 684
    uint _S32 = pair_0 % ntmpl_1;

    thread array<float2, int(16)> r_5;

#line 686
    uint n2_0 = 0U;

#line 697
    for(;;)
    {

#line 697
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 697
            break;
        }

#line 698
        uint idx_0 = tid_1 + 64U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S31 * 1024U + idx_0), cload_0(tmpl_0, _S32 * 1024U + idx_0));

#line 697
        n2_0 = n2_0 + 1U;

#line 697
    }

#line 697
    transform_0(&r_5, tid_1, kernelContext_4);

#line 716
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 721
    bool _S33 = tid_1 == 0U;

#line 721
    if(_S33)
    {

#line 721
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 721
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 721
    }



    float2 _S34 = float2(0.0, 0.0);

#line 725
    bool live_0;

    if(winStart_1 == 0U)
    {

#line 727
        live_0 = winEnd_1 >= 1024U;

#line 727
    }
    else
    {

#line 727
        live_0 = false;

#line 727
    }

#line 727
    uint threadBestBits_0;

#line 727
    uint threadBestSlot_0;

#line 727
    uint winner_0;

#line 727
    float2 threadBestVal_0;

#line 727
    if(live_0)
    {

#line 727
        threadBestBits_0 = thrBits_1;

#line 727
        threadBestSlot_0 = 4294967295U;

#line 727
        threadBestVal_0 = _S34;

#line 727
        winner_0 = 0U;
        for(;;)
        {

#line 728
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 728
                break;
            }

#line 729
            float _rx_0 = r_5[winner_0].x;

#line 729
            float _ry_0 = r_5[winner_0].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > threadBestBits_0)
            {
                uint _S35 = tid_1 * 16U + winner_0;
                float2 _S36 = float2(_rx_0, _ry_0);

#line 734
                threadBestBits_0 = magBits_0;

#line 734
                threadBestSlot_0 = _S35;

#line 734
                threadBestVal_0 = _S36;

#line 731
            }

#line 728
            winner_0 = winner_0 + 1U;

#line 728
        }

#line 727
    }
    else
    {

#line 727
        threadBestBits_0 = thrBits_1;

#line 727
        threadBestSlot_0 = 4294967295U;

#line 727
        threadBestVal_0 = _S34;

#line 727
        winner_0 = 0U;

#line 738
        for(;;)
        {

#line 738
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 738
                break;
            }

#line 739
            uint _S37 = tid_1 * 16U + winner_0;

#line 739
            uint idx_1 = slotToIndex_0(_S37);
            if(idx_1 >= winStart_1)
            {

#line 740
                live_0 = idx_1 < winEnd_1;

#line 740
            }
            else
            {

#line 740
                live_0 = false;

#line 740
            }
            float _rx_1 = r_5[winner_0].x;

#line 741
            float _ry_1 = r_5[winner_0].y;

#line 741
            uint magBits_1;
            if(live_0)
            {

#line 742
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 742
            }
            else
            {

#line 742
                magBits_1 = 0U;

#line 742
            }
            if(magBits_1 > threadBestBits_0)
            {

                float2 _S38 = float2(_rx_1, _ry_1);

#line 746
                threadBestBits_0 = magBits_1;

#line 746
                threadBestSlot_0 = _S37;

#line 746
                threadBestVal_0 = _S38;

#line 743
            }

#line 738
            winner_0 = winner_0 + 1U;

#line 738
        }

#line 727
    }

#line 751
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(threadBestBits_0);
    bool _S39 = simd_is_first();

#line 755
    if(_S39)
    {

#line 755
        live_0 = wm_0 > thrBits_1;

#line 755
    }
    else
    {

#line 755
        live_0 = false;

#line 755
    }

#line 755
    if(live_0)
    {

#line 755
        uint _S40 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 755
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(threadBestBits_0 > thrBits_1)
    {

#line 762
        live_0 = threadBestBits_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 762
    }
    else
    {

#line 762
        live_0 = false;

#line 762
    }

#line 762
    if(live_0)
    {

#line 762
        winner_0 = threadBestSlot_0;

#line 762
    }
    else
    {

#line 762
        winner_0 = 4294967295U;

#line 762
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S41 = simd_is_first();

#line 767
    if(_S41)
    {

#line 767
        live_0 = waveWinner_0 != 4294967295U;

#line 767
    }
    else
    {

#line 767
        live_0 = false;

#line 767
    }

#line 767
    if(live_0)
    {

#line 768
        uint _S42 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 767
    }

#line 772
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(threadBestSlot_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
    {

#line 774
        live_0 = threadBestSlot_0 != 4294967295U;

#line 774
    }
    else
    {

#line 774
        live_0 = false;

#line 774
    }

#line 774
    if(live_0)
    {

#line 775
        *(peakIdx_0+pair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 775
        *(peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 774
    }



    if(_S33)
    {

#line 778
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 778
    }
    else
    {

#line 778
        live_0 = false;

#line 778
    }

#line 778
    if(live_0)
    {

#line 779
        *(peakIdx_0+pair_0) = int(-1);

#line 779
        *(peakVal_0+pair_0) = packed_float2(_S34) ;

#line 778
    }

#line 911
    return;
}


#line 1202
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1202
    thread KernelContext_0 kernelContext_5;

#line 1202
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1202
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1202
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1202
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1202
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1202
    threadgroup array<uint, int(2048)> stg_1;

#line 1202
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1219
    uint _pr_0 = gid_0.x;

#line 1219
    uint _t_0 = lid_0.x;
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 1220
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);

#line 1228
    return;
}
