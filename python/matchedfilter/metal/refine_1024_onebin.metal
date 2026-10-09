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


#line 152 "mm_1024_refineListed_onebin.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 152
    return float2(*(b_0+i_0)) ;
}


#line 192
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 192
    float _S2 = a_0.x;

#line 192
    float _S3 = b_1.x;

#line 192
    float _S4 = a_0.y;

#line 192
    float _S5 = b_1.y;

#line 192
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 349
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 351
    float2 t1_0 = *a_1 - *c_0;

#line 351
    float2 t2_0 = *b_2 + *d_0;

#line 351
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 353
    *b_2 = t1_0 + j3_0;

#line 353
    *c_0 = t0_0 - t2_0;

#line 353
    *d_0 = t1_0 - j3_0;
    return;
}


#line 191
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 191
    float _S6 = a_2.x;

#line 191
    float _S7 = b_3.x;

#line 191
    float _S8 = a_2.y;

#line 191
    float _S9 = b_3.y;

#line 191
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 385
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 392
    uint n1_0 = 0U;
    for(;;)
    {

#line 393
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 393
            break;
        }

#line 393
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 393
        n1_0 = n1_0 + 1U;

#line 393
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 394
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 394
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 395
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 395
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 396
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 396
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 396
    uint k2_0 = 0U;
    for(;;)
    {

#line 397
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 397
            break;
        }

#line 397
        uint _S10 = 4U * k2_0;

#line 397
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 397
        k2_0 = k2_0 + 1U;

#line 397
    }

    float2 t_0 = (*r_0)[int(1)];

#line 399
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 399
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 400
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 400
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 401
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 401
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 402
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 402
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 403
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 403
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 404
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 404
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


#line 180 "mm_1024_refineListed_onebin.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_survivors_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 180
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 180
    uint _S11 = 2U * i_1;

#line 180
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11] = (as_type<uint>((v_0.x)));

#line 180
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11 + 1U] = (as_type<uint>((v_0.y)));

#line 180
    return;
}


#line 193
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 195
    uint j_0 = d_1 / _S12;

#line 195
    uint m_0 = d_1 % _S12;

#line 195
    uint _S13;
    if(TB_0 <= 16U)
    {

#line 196
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 196
    }
    else
    {

#line 196
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 196
    }

#line 196
    return _S13;
}


#line 181
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 181
    uint _S14 = 2U * i_2;

#line 181
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 545
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 546
    uint j_1;

#line 557
    thread array<float2, int(16)> out_0;

#line 557
    uint z_0 = 0U;
    for(;;)
    {

#line 558
        if(z_0 < 16U)
        {
        }
        else
        {

#line 558
            break;
        }

#line 558
        out_0[z_0] = float2(0.0, 0.0);

#line 558
        z_0 = z_0 + 1U;

#line 558
    }
    uint _S15 = (1U << lgSpan_0) - 1U;
    uint _S16 = (1U << lgLen_0) - 1U;

#line 560
    uint c_1 = 0U;
    for(;;)
    {

#line 561
        if(c_1 < 1U)
        {
        }
        else
        {

#line 561
            break;
        }

#line 562
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 562
        j_1 = 0U;
        for(;;)
        {

#line 563
            if(j_1 < 16U)
            {
            }
            else
            {

#line 563
                break;
            }

#line 563
            stgPut_0(j_1 * 64U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 563
            j_1 = j_1 + 1U;

#line 563
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 564
        uint d_2 = 0U;
        for(;;)
        {

#line 565
            if(d_2 < 16U)
            {
            }
            else
            {

#line 565
                break;
            }

#line 566
            uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
            uint b_4 = p_0 >> lgLen_0;

#line 567
            uint rem_0 = p_0 & _S16;
            uint i_3 = rem_0 >> lgSpan_0;

#line 568
            uint ln_0 = rem_0 & _S15;
            uint _S17 = c_1 * 16U;

#line 569
            bool _S18;

#line 569
            if(i_3 >= _S17)
            {

#line 569
                _S18 = i_3 < ((c_1 + 1U) * 16U);

#line 569
            }
            else
            {

#line 569
                _S18 = false;

#line 569
            }

#line 569
            if(_S18)
            {

#line 569
                float2 _S19 = stgGet_0((i_3 - _S17) * 64U + (b_4 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_2] = _S19;

#line 569
            }

#line 565
            d_2 = d_2 + 1U;

#line 565
        }

#line 561
        c_1 = c_1 + 1U;

#line 561
    }

#line 561
    j_1 = 0U;

#line 573
    for(;;)
    {

#line 573
        if(j_1 < 16U)
        {
        }
        else
        {

#line 573
            break;
        }

#line 573
        (*r_1)[j_1] = out_0[j_1];

#line 573
        j_1 = j_1 + 1U;

#line 573
    }
    return;
}


#line 364
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 367
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 367
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 488
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 488
    uint b_5 = 0U;

#line 497
    for(;;)
    {

#line 497
        if(b_5 < 4U)
        {
        }
        else
        {

#line 497
            break;
        }

#line 497
        dft4_0(r_3, b_5 * 4U);

#line 497
        b_5 = b_5 + 1U;

#line 497
    }


    return;
}


#line 629
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 629
    uint _S20;

#line 629
    uint k2_1;

#line 629
    float cr_0;

#line 629
    float ci_0;

#line 629
    uint _S21;

#line 629
    for(;;)
    {

#line 629
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

#line 632 "mm_1024_refineListed_onebin.slang"
    return;
}


#line 598
uint lgOf_0(uint i_4)
{

#line 598
    uint _S30;

#line 598
    if(i_4 < 2U)
    {

#line 598
        _S30 = 4U;

#line 598
    }
    else
    {

#line 598
        _S30 = 1U;

#line 598
    }

#line 598
    return _S30;
}


#line 600
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 604
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 604
    uint lg_2 = lgOf_0(1U);

#line 604
    uint lg_3 = lgOf_0(0U);

#line 609
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 644
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 658
    kernelContext_4->_tid_0 = tid_1;
    uint _S31 = pair_0 / ntmpl_1;

#line 659
    uint _S32 = pair_0 % ntmpl_1;

    thread array<float2, int(16)> r_5;

#line 661
    uint n2_0 = 0U;

#line 672
    for(;;)
    {

#line 672
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 672
            break;
        }

#line 673
        uint idx_0 = tid_1 + 64U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S31 * 1024U + idx_0), cload_0(tmpl_0, _S32 * 1024U + idx_0));

#line 672
        n2_0 = n2_0 + 1U;

#line 672
    }

#line 672
    transform_0(&r_5, tid_1, kernelContext_4);

#line 691
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 696
    bool _S33 = tid_1 == 0U;

#line 696
    if(_S33)
    {

#line 696
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 696
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 696
    }



    float2 _S34 = float2(0.0, 0.0);

#line 700
    bool live_0;

    if(winStart_1 == 0U)
    {

#line 702
        live_0 = winEnd_1 >= 1024U;

#line 702
    }
    else
    {

#line 702
        live_0 = false;

#line 702
    }

#line 702
    uint threadBestBits_0;

#line 702
    uint threadBestSlot_0;

#line 702
    uint winner_0;

#line 702
    float2 threadBestVal_0;

#line 702
    if(live_0)
    {

#line 702
        threadBestBits_0 = thrBits_1;

#line 702
        threadBestSlot_0 = 4294967295U;

#line 702
        threadBestVal_0 = _S34;

#line 702
        winner_0 = 0U;
        for(;;)
        {

#line 703
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 703
                break;
            }

#line 704
            float _rx_0 = r_5[winner_0].x;

#line 704
            float _ry_0 = r_5[winner_0].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > threadBestBits_0)
            {
                uint _S35 = tid_1 * 16U + winner_0;
                float2 _S36 = float2(_rx_0, _ry_0);

#line 709
                threadBestBits_0 = magBits_0;

#line 709
                threadBestSlot_0 = _S35;

#line 709
                threadBestVal_0 = _S36;

#line 706
            }

#line 703
            winner_0 = winner_0 + 1U;

#line 703
        }

#line 702
    }
    else
    {

#line 702
        threadBestBits_0 = thrBits_1;

#line 702
        threadBestSlot_0 = 4294967295U;

#line 702
        threadBestVal_0 = _S34;

#line 702
        winner_0 = 0U;

#line 713
        for(;;)
        {

#line 713
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 713
                break;
            }

#line 714
            uint _S37 = tid_1 * 16U + winner_0;

#line 714
            uint idx_1 = slotToIndex_0(_S37);
            if(idx_1 >= winStart_1)
            {

#line 715
                live_0 = idx_1 < winEnd_1;

#line 715
            }
            else
            {

#line 715
                live_0 = false;

#line 715
            }
            float _rx_1 = r_5[winner_0].x;

#line 716
            float _ry_1 = r_5[winner_0].y;

#line 716
            uint magBits_1;
            if(live_0)
            {

#line 717
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 717
            }
            else
            {

#line 717
                magBits_1 = 0U;

#line 717
            }
            if(magBits_1 > threadBestBits_0)
            {

                float2 _S38 = float2(_rx_1, _ry_1);

#line 721
                threadBestBits_0 = magBits_1;

#line 721
                threadBestSlot_0 = _S37;

#line 721
                threadBestVal_0 = _S38;

#line 718
            }

#line 713
            winner_0 = winner_0 + 1U;

#line 713
        }

#line 702
    }

#line 726
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(threadBestBits_0);
    bool _S39 = simd_is_first();

#line 730
    if(_S39)
    {

#line 730
        live_0 = wm_0 > thrBits_1;

#line 730
    }
    else
    {

#line 730
        live_0 = false;

#line 730
    }

#line 730
    if(live_0)
    {

#line 730
        uint _S40 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 730
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(threadBestBits_0 > thrBits_1)
    {

#line 737
        live_0 = threadBestBits_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 737
    }
    else
    {

#line 737
        live_0 = false;

#line 737
    }

#line 737
    if(live_0)
    {

#line 737
        winner_0 = threadBestSlot_0;

#line 737
    }
    else
    {

#line 737
        winner_0 = 4294967295U;

#line 737
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S41 = simd_is_first();

#line 742
    if(_S41)
    {

#line 742
        live_0 = waveWinner_0 != 4294967295U;

#line 742
    }
    else
    {

#line 742
        live_0 = false;

#line 742
    }

#line 742
    if(live_0)
    {

#line 743
        uint _S42 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 742
    }

#line 747
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(threadBestSlot_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
    {

#line 749
        live_0 = threadBestSlot_0 != 4294967295U;

#line 749
    }
    else
    {

#line 749
        live_0 = false;

#line 749
    }

#line 749
    if(live_0)
    {

#line 750
        *(peakIdx_0+pair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 750
        *(peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 749
    }



    if(_S33)
    {

#line 753
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 753
    }
    else
    {

#line 753
        live_0 = false;

#line 753
    }

#line 753
    if(live_0)
    {

#line 754
        *(peakIdx_0+pair_0) = int(-1);

#line 754
        *(peakVal_0+pair_0) = packed_float2(_S34) ;

#line 753
    }

#line 886
    return;
}


#line 1176
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1176
    thread KernelContext_0 kernelContext_5;

#line 1176
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1176
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1176
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1176
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1176
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1176
    (&kernelContext_5)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1176
    threadgroup array<uint, int(2048)> stg_1;

#line 1176
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1185
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1191
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 1191
    filterPair_0(pair_1, lid_0.x, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);


    return;
}
