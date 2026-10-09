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


#line 152 "mm_16384_refineListed.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 152
    return float2(*(b_0+i_0)) ;
}


#line 213
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 213
    float _S2 = a_0.x;

#line 213
    float _S3 = b_1.x;

#line 213
    float _S4 = a_0.y;

#line 213
    float _S5 = b_1.y;

#line 213
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 380
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 382
    float2 t1_0 = *a_1 - *c_0;

#line 382
    float2 t2_0 = *b_2 + *d_0;

#line 382
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
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
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 212
    float _S6 = a_2.x;

#line 212
    float _S7 = b_3.x;

#line 212
    float _S8 = a_2.y;

#line 212
    float _S9 = b_3.y;

#line 212
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 416
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

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

    float2 t_0 = (*r_0)[int(1)];

#line 430
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 430
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 431
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 431
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 432
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 432
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 433
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 433
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 434
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 434
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

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


#line 214 "mm_16384_refineListed.slang"
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


#line 8028 "hlsl.meta.slang"
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


#line 567 "mm_16384_refineListed.slang"
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
    array<uint, int(16384)> threadgroup* stg_0;
};


#line 554
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S13 = (1U << lgSpan_0) - 1U;
    uint _S14 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

#line 559
    uint d_2 = 0U;
    for(;;)
    {

#line 560
        if(d_2 < 16U)
        {
        }
        else
        {

#line 560
            break;
        }

#line 561
        uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
        uint rem_0 = p_0 & _S14;
        src_0[d_2] = (rem_0 >> lgSpan_0) * 1024U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S13);

#line 560
        d_2 = d_2 + 1U;

#line 560
    }

#line 565
    thread array<float, int(16)> xr_0;
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 566
    uint j_1 = 0U;
    for(;;)
    {

#line 567
        if(j_1 < 16U)
        {
        }
        else
        {

#line 567
            break;
        }

#line 567
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 1024U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].x)));

#line 567
        j_1 = j_1 + 1U;

#line 567
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 568
    d_2 = 0U;
    for(;;)
    {

#line 569
        if(d_2 < 16U)
        {
        }
        else
        {

#line 569
            break;
        }

#line 569
        xr_0[d_2] = (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]])));

#line 569
        d_2 = d_2 + 1U;

#line 569
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 570
    j_1 = 0U;
    for(;;)
    {

#line 571
        if(j_1 < 16U)
        {
        }
        else
        {

#line 571
            break;
        }

#line 571
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 1024U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].y)));

#line 571
        j_1 = j_1 + 1U;

#line 571
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 572
    d_2 = 0U;
    for(;;)
    {

#line 573
        if(d_2 < 16U)
        {
        }
        else
        {

#line 573
            break;
        }

#line 573
        (*r_1)[d_2] = float2(xr_0[d_2], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]]))));

#line 573
        d_2 = d_2 + 1U;

#line 573
    }
    return;
}


#line 395
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 398
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 398
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 519
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 519
    uint b_4 = 0U;

#line 528
    for(;;)
    {

#line 528
        if(b_4 < 4U)
        {
        }
        else
        {

#line 528
            break;
        }

#line 528
        dft4_0(r_3, b_4 * 4U);

#line 528
        b_4 = b_4 + 1U;

#line 528
    }


    return;
}


#line 666
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 666
    uint _S15;

#line 666
    uint k2_1;

#line 666
    float cr_0;

#line 666
    float ci_0;

#line 666
    uint _S16;

#line 666
    uint _S17;

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


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S15 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(16384U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 16384.0);
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
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
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
                uint per_2 = 16U / max(1024U, 1U);
                uint _S22 = max(64U, 1U);

#line 38
                _S16 = _S22;
                uint blk2_2 = tid_0 / _S22;

#line 39
                uint lane2_2 = tid_0 % _S22;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 1024U, 16384U, blk_2, lane_2, per_2, _S22, 1024U, blk2_2, lane2_2, kernelContext_1);

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
                _S17 = lgTB_1;

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 63U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 1024.0);
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
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
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
                uint per_3 = 16U / _S16;
                uint _S26 = max(4U, 1U);

#line 38
                _S18 = _S26;
                uint blk2_3 = tid_0 / _S26;

#line 39
                uint lane2_3 = tid_0 % _S26;

#line 39
                exchange_0(r_4, _S15, lgTB_1, 64U, 1024U, blk_3, lane_3, per_3, _S26, 64U, blk2_3, lane2_3, kernelContext_1);

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
                float _S27 = tw_2.x;

#line 27
                float _S28 = tw_2.y;

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
                    float nr_2 = cr_0 * _S27 - ci_0 * _S28;
                    float _S29 = cr_0 * _S28 + ci_0 * _S27;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_2;

#line 29
                    ci_0 = _S29;

#line 29
                }

#line 37
                uint per_4 = 16U / _S18;
                uint _S30 = max(0U, 1U);
                uint blk2_4 = tid_0 / _S30;

#line 39
                uint lane2_4 = tid_0 % _S30;

#line 39
                exchange_0(r_4, _S17, lgTB_2, 4U, 64U, blk_4, lane_4, per_4, _S30, 4U, blk2_4, lane2_4, kernelContext_1);

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

#line 669 "mm_16384_refineListed.slang"
    return;
}


#line 635
uint lgOf_0(uint i_1)
{

#line 635
    uint _S31;

#line 635
    if(i_1 < 3U)
    {

#line 635
        _S31 = 4U;

#line 635
    }
    else
    {

#line 635
        _S31 = 1U;

#line 635
    }

#line 635
    return _S31;
}


#line 637
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(4U);

    uint x_0 = slot_0 >> lg_0;

#line 641
    uint lg_1 = lgOf_0(3U);

    uint x_1 = x_0 >> lg_1;

#line 641
    uint lg_2 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_2;

#line 641
    uint lg_3 = lgOf_0(1U);

#line 641
    uint lg_4 = lgOf_0(0U);

#line 646
    return (((((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | (x_2 & ((1U << lg_3) - 1U))) << lg_4) | ((x_2 >> lg_3) & ((1U << lg_4) - 1U));
}


#line 681
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_2)
{

#line 695
    kernelContext_2->_tid_0 = tid_1;
    uint _S32 = pair_0 / ntmpl_1;

#line 696
    uint _S33 = pair_0 % ntmpl_1;

    thread array<float2, int(16)> r_5;

#line 698
    uint n2_0 = 0U;

#line 709
    for(;;)
    {

#line 709
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 709
            break;
        }

#line 710
        uint idx_0 = tid_1 + 1024U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S32 * 16384U + idx_0), cload_0(tmpl_0, _S33 * 16384U + idx_0));

#line 709
        n2_0 = n2_0 + 1U;

#line 709
    }

#line 709
    transform_0(&r_5, tid_1, kernelContext_2);

#line 728
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 728
    uint b_5 = tid_1;

#line 802
    for(;;)
    {

#line 802
        if(b_5 < nbins_1)
        {
        }
        else
        {

#line 802
            break;
        }

#line 802
        (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + b_5] = thrBits_1;

#line 802
        b_5 = b_5 + 1024U;

#line 802
    }
    bool _S34 = nbins_1 == 1U;

#line 803
    bool live_0;

#line 803
    if(_S34)
    {

#line 803
        live_0 = tid_1 == 0U;

#line 803
    }
    else
    {

#line 803
        live_0 = false;

#line 803
    }

#line 803
    if(live_0)
    {

#line 803
        (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U] = 4294967295U;

#line 803
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 808
    uint i_2 = 0U;
    for(;;)
    {

#line 809
        if(i_2 < 16U)
        {
        }
        else
        {

#line 809
            break;
        }

#line 810
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_2);
        if(idx_1 >= winStart_1)
        {

#line 811
            live_0 = idx_1 < winEnd_1;

#line 811
        }
        else
        {

#line 811
            live_0 = false;

#line 811
        }



        float _rx_0 = r_5[i_2].x;

#line 815
        float _ry_0 = r_5[i_2].y;
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
        myMag_0[i_2] = n2_0;
        uint off_0 = idx_1 - winStart_1;

#line 824
        if(live_0)
        {

#line 824
            if(binShift_1 >= int(0))
            {

#line 824
                b_5 = off_0 >> uint(binShift_1);

#line 824
            }
            else
            {

#line 824
                uint _S35 = off_0 / binsize_1;

#line 824
                b_5 = _S35;

#line 824
            }

#line 824
        }
        else
        {

#line 824
            b_5 = 0U;

#line 824
        }

#line 824
        myBin_0[i_2] = b_5;

#line 824
        bool _S36;



        if(nbins_1 > 1U)
        {

#line 828
            _S36 = (myMag_0[i_2]) > thrBits_1;

#line 828
        }
        else
        {

#line 828
            _S36 = false;

#line 828
        }

#line 828
        if(_S36)
        {

#line 829
            uint _S37 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + myBin_0[i_2]])), myMag_0[i_2], memory_order_relaxed);

#line 828
        }

#line 809
        i_2 = i_2 + 1U;

#line 809
    }

#line 809
    uint winner_0;

#line 841
    if(_S34)
    {

#line 841
        winner_0 = thrBits_1;

#line 841
        i_2 = 0U;


        for(;;)
        {

#line 844
            if(i_2 < 16U)
            {
            }
            else
            {

#line 844
                break;
            }

#line 844
            uint _S38 = max(winner_0, myMag_0[i_2]);

#line 844
            uint i_3 = i_2 + 1U;

#line 844
            winner_0 = _S38;

#line 844
            i_2 = i_3;

#line 844
        }

        uint wm_0 = simd_max(winner_0);
        bool _S39 = simd_is_first();

#line 847
        if(_S39)
        {

#line 847
            live_0 = wm_0 > thrBits_1;

#line 847
        }
        else
        {

#line 847
            live_0 = false;

#line 847
        }

#line 847
        if(live_0)
        {

#line 847
            uint _S40 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0])), wm_0, memory_order_relaxed);

#line 847
        }

#line 841
    }

#line 862
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 869
    if(_S34)
    {

#line 869
        winner_0 = 4294967295U;

#line 869
        i_2 = 0U;


        for(;;)
        {

#line 872
            if(i_2 < 16U)
            {
            }
            else
            {

#line 872
                break;
            }

#line 873
            if((myMag_0[i_2]) > thrBits_1)
            {

#line 873
                live_0 = (myMag_0[i_2]) == (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0];

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
                winner_0 = min(winner_0, tid_1 * 16U + i_2);

#line 873
            }

#line 872
            i_2 = i_2 + 1U;

#line 872
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S41 = simd_is_first();

#line 877
        if(_S41)
        {

#line 877
            live_0 = waveWinner_0 != 4294967295U;

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
            uint _S42 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 877
        }

#line 882
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 882
        i_2 = 0U;
        for(;;)
        {

#line 883
            if(i_2 < 16U)
            {
            }
            else
            {

#line 883
                break;
            }

#line 884
            uint _S43 = tid_1 * 16U + i_2;

#line 884
            if(_S43 == (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U])
            {

#line 885
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S43));

#line 885
                *(peakVal_0+pair_0) = packed_float2(float2(r_5[i_2].x, r_5[i_2].y)) ;

#line 884
            }

#line 883
            i_2 = i_2 + 1U;

#line 883
        }

#line 889
        if(tid_1 == 0U)
        {

#line 889
            live_0 = ((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U]) == 4294967295U;

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

#line 869
    }
    else
    {

#line 869
        i_2 = 0U;

#line 898
        for(;;)
        {

#line 898
            if(i_2 < 16U)
            {
            }
            else
            {

#line 898
                break;
            }

#line 899
            if((myMag_0[i_2]) > thrBits_1)
            {

#line 899
                live_0 = (myMag_0[i_2]) == (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + myBin_0[i_2]];

#line 899
            }
            else
            {

#line 899
                live_0 = false;

#line 899
            }

#line 899
            myMag_0[i_2] = uint(live_0);

#line 898
            i_2 = i_2 + 1U;

#line 898
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 901
        b_5 = tid_1;
        for(;;)
        {

#line 902
            if(b_5 < nbins_1)
            {
            }
            else
            {

#line 902
                break;
            }

#line 902
            (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + b_5] = 4294967295U;

#line 902
            b_5 = b_5 + 1024U;

#line 902
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 903
        i_2 = 0U;
        for(;;)
        {

#line 904
            if(i_2 < 16U)
            {
            }
            else
            {

#line 904
                break;
            }

#line 905
            if((myMag_0[i_2]) != 0U)
            {

#line 905
                uint _S44 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + myBin_0[i_2]])), tid_1 * 16U + i_2, memory_order_relaxed);

#line 905
            }

#line 904
            i_2 = i_2 + 1U;

#line 904
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 906
        i_2 = 0U;
        for(;;)
        {

#line 907
            if(i_2 < 16U)
            {
            }
            else
            {

#line 907
                break;
            }

#line 908
            if((myMag_0[i_2]) != 0U)
            {

#line 908
                live_0 = ((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + myBin_0[i_2]]) == (tid_1 * 16U + i_2);

#line 908
            }
            else
            {

#line 908
                live_0 = false;

#line 908
            }

#line 908
            if(live_0)
            {

#line 909
                uint o_1 = pair_0 * nbins_1 + myBin_0[i_2];
                *(peakIdx_0+o_1) = int(slotToIndex_0(tid_1 * 16U + i_2));

#line 910
                *(peakVal_0+o_1) = packed_float2(float2(r_5[i_2].x, r_5[i_2].y)) ;

#line 908
            }

#line 907
            i_2 = i_2 + 1U;

#line 907
        }

#line 907
        b_5 = tid_1;

#line 914
        for(;;)
        {

#line 914
            if(b_5 < nbins_1)
            {
            }
            else
            {

#line 914
                break;
            }

#line 915
            if(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + b_5]) == 4294967295U)
            {

#line 916
                uint _S45 = pair_0 * nbins_1 + b_5;

#line 916
                *(peakIdx_0+_S45) = int(-1);

#line 916
                *(peakVal_0+_S45) = packed_float2(float2(0.0, 0.0)) ;

#line 915
            }

#line 914
            b_5 = b_5 + 1024U;

#line 914
        }

#line 869
    }

#line 923
    return;
}


#line 1341
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1341
    thread KernelContext_0 kernelContext_3;

#line 1341
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 1341
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1341
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1341
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1341
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1341
    (&kernelContext_3)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1341
    threadgroup array<uint, int(16384)> stg_1;

#line 1341
    (&kernelContext_3)->stg_0 = &stg_1;

#line 1350
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1356
    (&kernelContext_3)->_stgBase_0 = 0U;

#line 1356
    filterPair_0(pair_1, lid_0.x, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_3);


    return;
}
