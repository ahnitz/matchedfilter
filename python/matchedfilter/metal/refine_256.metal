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


#line 151 "mm_256_refineListed.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 151
    return float2(*(b_0+i_0)) ;
}


#line 191
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 191
    float _S2 = a_0.x;

#line 191
    float _S3 = b_1.x;

#line 191
    float _S4 = a_0.y;

#line 191
    float _S5 = b_1.y;

#line 191
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 348
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 350
    float2 t1_0 = *a_1 - *c_0;

#line 350
    float2 t2_0 = *b_2 + *d_0;

#line 350
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 352
    *b_2 = t1_0 + j3_0;

#line 352
    *c_0 = t0_0 - t2_0;

#line 352
    *d_0 = t1_0 - j3_0;
    return;
}


#line 190
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 190
    float _S6 = a_2.x;

#line 190
    float _S7 = b_3.x;

#line 190
    float _S8 = a_2.y;

#line 190
    float _S9 = b_3.y;

#line 190
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 384
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 391
    uint n1_0 = 0U;
    for(;;)
    {

#line 392
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 392
            break;
        }

#line 392
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 392
        n1_0 = n1_0 + 1U;

#line 392
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 393
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 393
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 394
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 394
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 395
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 395
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 395
    uint k2_0 = 0U;
    for(;;)
    {

#line 396
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 396
            break;
        }

#line 396
        uint _S10 = 4U * k2_0;

#line 396
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 396
        k2_0 = k2_0 + 1U;

#line 396
    }

    float2 t_0 = (*r_0)[int(1)];

#line 398
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 398
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 399
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 399
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 400
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 400
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 401
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 401
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 402
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 402
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 403
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 403
    (*r_0)[int(14)] = t_5;
    return;
}


#line 384
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_1 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_1 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_1 = float2(0.0, 1.0);
    float2 W6_1 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_1 = float2(-0.92387950420379639, -0.38268342614173889);

#line 391
    uint n1_1 = 0U;
    for(;;)
    {

#line 392
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 392
            break;
        }

#line 392
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 392
        n1_1 = n1_1 + 1U;

#line 392
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 393
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 393
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 394
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 394
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 395
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 395
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 395
    uint k2_1 = 0U;
    for(;;)
    {

#line 396
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 396
            break;
        }

#line 396
        uint _S11 = 4U * k2_1;

#line 396
        r4_0(&(*r_1)[_S11], &(*r_1)[_S11 + 1U], &(*r_1)[_S11 + 2U], &(*r_1)[_S11 + 3U]);

#line 396
        k2_1 = k2_1 + 1U;

#line 396
    }

    float2 t_6 = (*r_1)[int(1)];

#line 398
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 398
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 399
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 399
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 400
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 400
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 401
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 401
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 402
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 402
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 403
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 403
    (*r_1)[int(14)] = t_11;
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


#line 179 "mm_256_refineListed.slang"
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
    array<uint, int(512)> threadgroup* stg_0;
};


#line 179
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 179
    uint _S12 = 2U * i_1;

#line 179
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S12] = (as_type<uint>((v_0.x)));

#line 179
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S12 + 1U] = (as_type<uint>((v_0.y)));

#line 179
    return;
}


#line 192
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S13 = max(TB_0, 1U);

#line 194
    uint j_0 = d_1 / _S13;

#line 194
    uint m_0 = d_1 % _S13;

#line 194
    uint _S14;
    if(TB_0 <= 16U)
    {

#line 195
        _S14 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 195
    }
    else
    {

#line 195
        _S14 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 195
    }

#line 195
    return _S14;
}


#line 180
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 180
    uint _S15 = 2U * i_2;

#line 180
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15 + 1U]))));
}


#line 509
void exchange_0(array<float2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 510
    uint j_1;

#line 521
    thread array<float2, int(16)> out_0;

#line 521
    uint z_0 = 0U;
    for(;;)
    {

#line 522
        if(z_0 < 16U)
        {
        }
        else
        {

#line 522
            break;
        }

#line 522
        out_0[z_0] = float2(0.0, 0.0);

#line 522
        z_0 = z_0 + 1U;

#line 522
    }
    uint _S16 = (1U << lgSpan_0) - 1U;
    uint _S17 = (1U << lgLen_0) - 1U;

#line 524
    uint c_1 = 0U;
    for(;;)
    {

#line 525
        if(c_1 < 1U)
        {
        }
        else
        {

#line 525
            break;
        }

#line 526
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 526
        j_1 = 0U;
        for(;;)
        {

#line 527
            if(j_1 < 16U)
            {
            }
            else
            {

#line 527
                break;
            }

#line 527
            stgPut_0(j_1 * 16U + kernelContext_2->_tid_0, (*r_2)[c_1 * 16U + j_1], kernelContext_2);

#line 527
            j_1 = j_1 + 1U;

#line 527
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 528
        uint d_2 = 0U;
        for(;;)
        {

#line 529
            if(d_2 < 16U)
            {
            }
            else
            {

#line 529
                break;
            }

#line 530
            uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
            uint b_4 = p_0 >> lgLen_0;

#line 531
            uint rem_0 = p_0 & _S17;
            uint i_3 = rem_0 >> lgSpan_0;

#line 532
            uint ln_0 = rem_0 & _S16;
            uint _S18 = c_1 * 16U;

#line 533
            bool _S19;

#line 533
            if(i_3 >= _S18)
            {

#line 533
                _S19 = i_3 < ((c_1 + 1U) * 16U);

#line 533
            }
            else
            {

#line 533
                _S19 = false;

#line 533
            }

#line 533
            if(_S19)
            {

#line 533
                float2 _S20 = stgGet_0((i_3 - _S18) * 16U + (b_4 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_2] = _S20;

#line 533
            }

#line 529
            d_2 = d_2 + 1U;

#line 529
        }

#line 525
        c_1 = c_1 + 1U;

#line 525
    }

#line 525
    j_1 = 0U;

#line 537
    for(;;)
    {

#line 537
        if(j_1 < 16U)
        {
        }
        else
        {

#line 537
            break;
        }

#line 537
        (*r_2)[j_1] = out_0[j_1];

#line 537
        j_1 = j_1 + 1U;

#line 537
    }
    return;
}


#line 487
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 494
    dft16_1(r_3);

#line 499
    return;
}


#line 592
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 592
    for(;;)
    {

#line 592
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(16U);
                uint lgLn_0 = firstbithigh_0(256U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 15U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 256.0);
                float _S21 = tw_0.x;

#line 27
                float _S22 = tw_0.y;

#line 27
                uint k2_2 = 0U;

#line 27
                float cr_0 = 1.0;

#line 27
                float ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S21 - ci_0 * _S22;
                    float _S23 = cr_0 * _S22 + ci_0 * _S21;

#line 29
                    k2_2 = k2_2 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S23;

#line 29
                }

#line 37
                uint per_2 = 16U / max(16U, 1U);
                uint _S24 = max(1U, 1U);
                uint blk2_2 = tid_0 / _S24;

#line 39
                uint lane2_2 = tid_0 % _S24;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 16U, 256U, blk_2, lane_2, per_2, _S24, 16U, blk2_2, lane2_2, kernelContext_3);

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

#line 595 "mm_256_refineListed.slang"
    return;
}


#line 561
uint lgOf_0(uint i_4)
{

#line 561
    uint _S25;

#line 561
    if(i_4 < 1U)
    {

#line 561
        _S25 = 4U;

#line 561
    }
    else
    {

#line 561
        if(i_4 == 1U)
        {

#line 561
            _S25 = 4U;

#line 561
        }
        else
        {

#line 561
            _S25 = 1U;

#line 561
        }

#line 561
    }

#line 561
    return _S25;
}


#line 563
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 567
    uint lg_1 = lgOf_0(0U);

#line 572
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 607
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 621
    kernelContext_4->_tid_0 = tid_1;
    uint _S26 = pair_0 / ntmpl_1;

#line 622
    uint _S27 = pair_0 % ntmpl_1;

    thread array<float2, int(16)> r_5;

#line 624
    uint n2_0 = 0U;

#line 635
    for(;;)
    {

#line 635
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 635
            break;
        }

#line 636
        uint idx_0 = tid_1 + 16U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S26 * 256U + idx_0), cload_0(tmpl_0, _S27 * 256U + idx_0));

#line 635
        n2_0 = n2_0 + 1U;

#line 635
    }

#line 635
    transform_0(&r_5, tid_1, kernelContext_4);

#line 654
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 654
    uint b_5 = tid_1;

#line 662
    for(;;)
    {

#line 662
        if(b_5 < nbins_1)
        {
        }
        else
        {

#line 662
            break;
        }

#line 662
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_5] = thrBits_1;

#line 662
        b_5 = b_5 + 16U;

#line 662
    }
    bool _S28 = nbins_1 == 1U;

#line 663
    bool live_0;

#line 663
    if(_S28)
    {

#line 663
        live_0 = tid_1 == 0U;

#line 663
    }
    else
    {

#line 663
        live_0 = false;

#line 663
    }

#line 663
    if(live_0)
    {

#line 663
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 663
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 668
    uint i_5 = 0U;
    for(;;)
    {

#line 669
        if(i_5 < 16U)
        {
        }
        else
        {

#line 669
            break;
        }

#line 670
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_5);
        if(idx_1 >= winStart_1)
        {

#line 671
            live_0 = idx_1 < winEnd_1;

#line 671
        }
        else
        {

#line 671
            live_0 = false;

#line 671
        }



        float _rx_0 = r_5[i_5].x;

#line 675
        float _ry_0 = r_5[i_5].y;
        if(live_0)
        {

#line 676
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 676
        }
        else
        {

#line 676
            n2_0 = 0U;

#line 676
        }

#line 676
        myMag_0[i_5] = n2_0;
        uint off_0 = idx_1 - winStart_1;

#line 684
        if(live_0)
        {

#line 684
            if(binShift_1 >= int(0))
            {

#line 684
                b_5 = off_0 >> uint(binShift_1);

#line 684
            }
            else
            {

#line 684
                uint _S29 = off_0 / binsize_1;

#line 684
                b_5 = _S29;

#line 684
            }

#line 684
        }
        else
        {

#line 684
            b_5 = 0U;

#line 684
        }

#line 684
        myBin_0[i_5] = b_5;

#line 684
        bool _S30;



        if(nbins_1 > 1U)
        {

#line 688
            _S30 = (myMag_0[i_5]) > thrBits_1;

#line 688
        }
        else
        {

#line 688
            _S30 = false;

#line 688
        }

#line 688
        if(_S30)
        {

#line 689
            uint _S31 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), myMag_0[i_5], memory_order_relaxed);

#line 688
        }

#line 669
        i_5 = i_5 + 1U;

#line 669
    }

#line 669
    uint winner_0;

#line 701
    if(_S28)
    {

#line 701
        winner_0 = thrBits_1;

#line 701
        i_5 = 0U;


        for(;;)
        {

#line 704
            if(i_5 < 16U)
            {
            }
            else
            {

#line 704
                break;
            }

#line 704
            uint _S32 = max(winner_0, myMag_0[i_5]);

#line 704
            uint i_6 = i_5 + 1U;

#line 704
            winner_0 = _S32;

#line 704
            i_5 = i_6;

#line 704
        }

        uint wm_0 = simd_max(winner_0);
        bool _S33 = simd_is_first();

#line 707
        if(_S33)
        {

#line 707
            live_0 = wm_0 > thrBits_1;

#line 707
        }
        else
        {

#line 707
            live_0 = false;

#line 707
        }

#line 707
        if(live_0)
        {

#line 707
            uint _S34 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 707
        }

#line 701
    }

#line 722
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 729
    if(_S28)
    {

#line 729
        winner_0 = 4294967295U;

#line 729
        i_5 = 0U;


        for(;;)
        {

#line 732
            if(i_5 < 16U)
            {
            }
            else
            {

#line 732
                break;
            }

#line 733
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 733
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 733
            }
            else
            {

#line 733
                live_0 = false;

#line 733
            }

#line 733
            if(live_0)
            {

#line 733
                winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 733
            }

#line 732
            i_5 = i_5 + 1U;

#line 732
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S35 = simd_is_first();

#line 737
        if(_S35)
        {

#line 737
            live_0 = waveWinner_0 != 4294967295U;

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

#line 738
            uint _S36 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 737
        }

#line 742
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 742
        i_5 = 0U;
        for(;;)
        {

#line 743
            if(i_5 < 16U)
            {
            }
            else
            {

#line 743
                break;
            }

#line 744
            uint _S37 = tid_1 * 16U + i_5;

#line 744
            if(_S37 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 745
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S37));

#line 745
                *(peakVal_0+pair_0) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 744
            }

#line 743
            i_5 = i_5 + 1U;

#line 743
        }

#line 749
        if(tid_1 == 0U)
        {

#line 749
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

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
            *(peakIdx_0+pair_0) = int(-1);

#line 750
            *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 749
        }

#line 729
    }
    else
    {

#line 729
        i_5 = 0U;

#line 758
        for(;;)
        {

#line 758
            if(i_5 < 16U)
            {
            }
            else
            {

#line 758
                break;
            }

#line 759
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 759
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]];

#line 759
            }
            else
            {

#line 759
                live_0 = false;

#line 759
            }

#line 759
            myMag_0[i_5] = uint(live_0);

#line 758
            i_5 = i_5 + 1U;

#line 758
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 761
        b_5 = tid_1;
        for(;;)
        {

#line 762
            if(b_5 < nbins_1)
            {
            }
            else
            {

#line 762
                break;
            }

#line 762
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_5] = 4294967295U;

#line 762
            b_5 = b_5 + 16U;

#line 762
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 763
        i_5 = 0U;
        for(;;)
        {

#line 764
            if(i_5 < 16U)
            {
            }
            else
            {

#line 764
                break;
            }

#line 765
            if((myMag_0[i_5]) != 0U)
            {

#line 765
                uint _S38 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), tid_1 * 16U + i_5, memory_order_relaxed);

#line 765
            }

#line 764
            i_5 = i_5 + 1U;

#line 764
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 766
        i_5 = 0U;
        for(;;)
        {

#line 767
            if(i_5 < 16U)
            {
            }
            else
            {

#line 767
                break;
            }

#line 768
            if((myMag_0[i_5]) != 0U)
            {

#line 768
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]]) == (tid_1 * 16U + i_5);

#line 768
            }
            else
            {

#line 768
                live_0 = false;

#line 768
            }

#line 768
            if(live_0)
            {

#line 769
                uint o_0 = pair_0 * nbins_1 + myBin_0[i_5];
                *(peakIdx_0+o_0) = int(slotToIndex_0(tid_1 * 16U + i_5));

#line 770
                *(peakVal_0+o_0) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 768
            }

#line 767
            i_5 = i_5 + 1U;

#line 767
        }

#line 767
        b_5 = tid_1;

#line 774
        for(;;)
        {

#line 774
            if(b_5 < nbins_1)
            {
            }
            else
            {

#line 774
                break;
            }

#line 775
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_5]) == 4294967295U)
            {

#line 776
                uint _S39 = pair_0 * nbins_1 + b_5;

#line 776
                *(peakIdx_0+_S39) = int(-1);

#line 776
                *(peakVal_0+_S39) = packed_float2(float2(0.0, 0.0)) ;

#line 775
            }

#line 774
            b_5 = b_5 + 16U;

#line 774
        }

#line 729
    }

#line 782
    return;
}


#line 1069
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1069
    thread KernelContext_0 kernelContext_5;

#line 1069
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1069
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1069
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1069
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1069
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1069
    (&kernelContext_5)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1069
    threadgroup array<uint, int(512)> stg_1;

#line 1069
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1078
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1084
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 1084
    filterPair_0(pair_1, lid_0.x, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);


    return;
}
