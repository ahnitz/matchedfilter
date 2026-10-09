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


#line 193 "mm_16384_refineListed.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 195
    uint j_0 = d_1 / _S11;

#line 195
    uint m_0 = d_1 % _S11;

#line 195
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 196
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 196
    }
    else
    {

#line 196
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 196
    }

#line 196
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


#line 536 "mm_16384_refineListed.slang"
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


#line 523
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S13 = (1U << lgSpan_0) - 1U;
    uint _S14 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

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
        uint rem_0 = p_0 & _S14;
        src_0[d_2] = (rem_0 >> lgSpan_0) * 1024U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S13);

#line 529
        d_2 = d_2 + 1U;

#line 529
    }

#line 534
    thread array<float, int(16)> xr_0;
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 535
    uint j_1 = 0U;
    for(;;)
    {

#line 536
        if(j_1 < 16U)
        {
        }
        else
        {

#line 536
            break;
        }

#line 536
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 1024U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].x)));

#line 536
        j_1 = j_1 + 1U;

#line 536
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 537
    d_2 = 0U;
    for(;;)
    {

#line 538
        if(d_2 < 16U)
        {
        }
        else
        {

#line 538
            break;
        }

#line 538
        xr_0[d_2] = (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]])));

#line 538
        d_2 = d_2 + 1U;

#line 538
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 539
    j_1 = 0U;
    for(;;)
    {

#line 540
        if(j_1 < 16U)
        {
        }
        else
        {

#line 540
            break;
        }

#line 540
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 1024U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].y)));

#line 540
        j_1 = j_1 + 1U;

#line 540
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 541
    d_2 = 0U;
    for(;;)
    {

#line 542
        if(d_2 < 16U)
        {
        }
        else
        {

#line 542
            break;
        }

#line 542
        (*r_1)[d_2] = float2(xr_0[d_2], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]]))));

#line 542
        d_2 = d_2 + 1U;

#line 542
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
    uint b_4 = 0U;

#line 497
    for(;;)
    {

#line 497
        if(b_4 < 4U)
        {
        }
        else
        {

#line 497
            break;
        }

#line 497
        dft4_0(r_3, b_4 * 4U);

#line 497
        b_4 = b_4 + 1U;

#line 497
    }


    return;
}


#line 629
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 629
    uint _S15;

#line 629
    uint k2_1;

#line 629
    float cr_0;

#line 629
    float ci_0;

#line 629
    uint _S16;

#line 629
    uint _S17;

#line 629
    uint _S18;

#line 629
    for(;;)
    {

#line 629
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

#line 632 "mm_16384_refineListed.slang"
    return;
}


#line 598
uint lgOf_0(uint i_1)
{

#line 598
    uint _S31;

#line 598
    if(i_1 < 3U)
    {

#line 598
        _S31 = 4U;

#line 598
    }
    else
    {

#line 598
        _S31 = 1U;

#line 598
    }

#line 598
    return _S31;
}


#line 600
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(4U);

    uint x_0 = slot_0 >> lg_0;

#line 604
    uint lg_1 = lgOf_0(3U);

    uint x_1 = x_0 >> lg_1;

#line 604
    uint lg_2 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_2;

#line 604
    uint lg_3 = lgOf_0(1U);

#line 604
    uint lg_4 = lgOf_0(0U);

#line 609
    return (((((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | (x_2 & ((1U << lg_3) - 1U))) << lg_4) | ((x_2 >> lg_3) & ((1U << lg_4) - 1U));
}


#line 644
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_2)
{

#line 658
    kernelContext_2->_tid_0 = tid_1;
    uint _S32 = pair_0 / ntmpl_1;

#line 659
    uint _S33 = pair_0 % ntmpl_1;

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
        uint idx_0 = tid_1 + 1024U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S32 * 16384U + idx_0), cload_0(tmpl_0, _S33 * 16384U + idx_0));

#line 672
        n2_0 = n2_0 + 1U;

#line 672
    }

#line 672
    transform_0(&r_5, tid_1, kernelContext_2);

#line 691
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 691
    uint b_5 = tid_1;

#line 765
    for(;;)
    {

#line 765
        if(b_5 < nbins_1)
        {
        }
        else
        {

#line 765
            break;
        }

#line 765
        (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + b_5] = thrBits_1;

#line 765
        b_5 = b_5 + 1024U;

#line 765
    }
    bool _S34 = nbins_1 == 1U;

#line 766
    bool live_0;

#line 766
    if(_S34)
    {

#line 766
        live_0 = tid_1 == 0U;

#line 766
    }
    else
    {

#line 766
        live_0 = false;

#line 766
    }

#line 766
    if(live_0)
    {

#line 766
        (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U] = 4294967295U;

#line 766
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 771
    uint i_2 = 0U;
    for(;;)
    {

#line 772
        if(i_2 < 16U)
        {
        }
        else
        {

#line 772
            break;
        }

#line 773
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_2);
        if(idx_1 >= winStart_1)
        {

#line 774
            live_0 = idx_1 < winEnd_1;

#line 774
        }
        else
        {

#line 774
            live_0 = false;

#line 774
        }



        float _rx_0 = r_5[i_2].x;

#line 778
        float _ry_0 = r_5[i_2].y;
        if(live_0)
        {

#line 779
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 779
        }
        else
        {

#line 779
            n2_0 = 0U;

#line 779
        }

#line 779
        myMag_0[i_2] = n2_0;
        uint off_0 = idx_1 - winStart_1;

#line 787
        if(live_0)
        {

#line 787
            if(binShift_1 >= int(0))
            {

#line 787
                b_5 = off_0 >> uint(binShift_1);

#line 787
            }
            else
            {

#line 787
                uint _S35 = off_0 / binsize_1;

#line 787
                b_5 = _S35;

#line 787
            }

#line 787
        }
        else
        {

#line 787
            b_5 = 0U;

#line 787
        }

#line 787
        myBin_0[i_2] = b_5;

#line 787
        bool _S36;



        if(nbins_1 > 1U)
        {

#line 791
            _S36 = (myMag_0[i_2]) > thrBits_1;

#line 791
        }
        else
        {

#line 791
            _S36 = false;

#line 791
        }

#line 791
        if(_S36)
        {

#line 792
            uint _S37 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + myBin_0[i_2]])), myMag_0[i_2], memory_order_relaxed);

#line 791
        }

#line 772
        i_2 = i_2 + 1U;

#line 772
    }

#line 772
    uint winner_0;

#line 804
    if(_S34)
    {

#line 804
        winner_0 = thrBits_1;

#line 804
        i_2 = 0U;


        for(;;)
        {

#line 807
            if(i_2 < 16U)
            {
            }
            else
            {

#line 807
                break;
            }

#line 807
            uint _S38 = max(winner_0, myMag_0[i_2]);

#line 807
            uint i_3 = i_2 + 1U;

#line 807
            winner_0 = _S38;

#line 807
            i_2 = i_3;

#line 807
        }

        uint wm_0 = simd_max(winner_0);
        bool _S39 = simd_is_first();

#line 810
        if(_S39)
        {

#line 810
            live_0 = wm_0 > thrBits_1;

#line 810
        }
        else
        {

#line 810
            live_0 = false;

#line 810
        }

#line 810
        if(live_0)
        {

#line 810
            uint _S40 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0])), wm_0, memory_order_relaxed);

#line 810
        }

#line 804
    }

#line 825
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 832
    if(_S34)
    {

#line 832
        winner_0 = 4294967295U;

#line 832
        i_2 = 0U;


        for(;;)
        {

#line 835
            if(i_2 < 16U)
            {
            }
            else
            {

#line 835
                break;
            }

#line 836
            if((myMag_0[i_2]) > thrBits_1)
            {

#line 836
                live_0 = (myMag_0[i_2]) == (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0];

#line 836
            }
            else
            {

#line 836
                live_0 = false;

#line 836
            }

#line 836
            if(live_0)
            {

#line 836
                winner_0 = min(winner_0, tid_1 * 16U + i_2);

#line 836
            }

#line 835
            i_2 = i_2 + 1U;

#line 835
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S41 = simd_is_first();

#line 840
        if(_S41)
        {

#line 840
            live_0 = waveWinner_0 != 4294967295U;

#line 840
        }
        else
        {

#line 840
            live_0 = false;

#line 840
        }

#line 840
        if(live_0)
        {

#line 841
            uint _S42 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 840
        }

#line 845
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 845
        i_2 = 0U;
        for(;;)
        {

#line 846
            if(i_2 < 16U)
            {
            }
            else
            {

#line 846
                break;
            }

#line 847
            uint _S43 = tid_1 * 16U + i_2;

#line 847
            if(_S43 == (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U])
            {

#line 848
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S43));

#line 848
                *(peakVal_0+pair_0) = packed_float2(float2(r_5[i_2].x, r_5[i_2].y)) ;

#line 847
            }

#line 846
            i_2 = i_2 + 1U;

#line 846
        }

#line 852
        if(tid_1 == 0U)
        {

#line 852
            live_0 = ((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U]) == 4294967295U;

#line 852
        }
        else
        {

#line 852
            live_0 = false;

#line 852
        }

#line 852
        if(live_0)
        {

#line 853
            *(peakIdx_0+pair_0) = int(-1);

#line 853
            *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 852
        }

#line 832
    }
    else
    {

#line 832
        i_2 = 0U;

#line 861
        for(;;)
        {

#line 861
            if(i_2 < 16U)
            {
            }
            else
            {

#line 861
                break;
            }

#line 862
            if((myMag_0[i_2]) > thrBits_1)
            {

#line 862
                live_0 = (myMag_0[i_2]) == (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + myBin_0[i_2]];

#line 862
            }
            else
            {

#line 862
                live_0 = false;

#line 862
            }

#line 862
            myMag_0[i_2] = uint(live_0);

#line 861
            i_2 = i_2 + 1U;

#line 861
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 864
        b_5 = tid_1;
        for(;;)
        {

#line 865
            if(b_5 < nbins_1)
            {
            }
            else
            {

#line 865
                break;
            }

#line 865
            (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + b_5] = 4294967295U;

#line 865
            b_5 = b_5 + 1024U;

#line 865
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 866
        i_2 = 0U;
        for(;;)
        {

#line 867
            if(i_2 < 16U)
            {
            }
            else
            {

#line 867
                break;
            }

#line 868
            if((myMag_0[i_2]) != 0U)
            {

#line 868
                uint _S44 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + myBin_0[i_2]])), tid_1 * 16U + i_2, memory_order_relaxed);

#line 868
            }

#line 867
            i_2 = i_2 + 1U;

#line 867
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 869
        i_2 = 0U;
        for(;;)
        {

#line 870
            if(i_2 < 16U)
            {
            }
            else
            {

#line 870
                break;
            }

#line 871
            if((myMag_0[i_2]) != 0U)
            {

#line 871
                live_0 = ((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + myBin_0[i_2]]) == (tid_1 * 16U + i_2);

#line 871
            }
            else
            {

#line 871
                live_0 = false;

#line 871
            }

#line 871
            if(live_0)
            {

#line 872
                uint o_1 = pair_0 * nbins_1 + myBin_0[i_2];
                *(peakIdx_0+o_1) = int(slotToIndex_0(tid_1 * 16U + i_2));

#line 873
                *(peakVal_0+o_1) = packed_float2(float2(r_5[i_2].x, r_5[i_2].y)) ;

#line 871
            }

#line 870
            i_2 = i_2 + 1U;

#line 870
        }

#line 870
        b_5 = tid_1;

#line 877
        for(;;)
        {

#line 877
            if(b_5 < nbins_1)
            {
            }
            else
            {

#line 877
                break;
            }

#line 878
            if(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + b_5]) == 4294967295U)
            {

#line 879
                uint _S45 = pair_0 * nbins_1 + b_5;

#line 879
                *(peakIdx_0+_S45) = int(-1);

#line 879
                *(peakVal_0+_S45) = packed_float2(float2(0.0, 0.0)) ;

#line 878
            }

#line 877
            b_5 = b_5 + 1024U;

#line 877
        }

#line 832
    }

#line 886
    return;
}


#line 1176
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1176
    thread KernelContext_0 kernelContext_3;

#line 1176
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 1176
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1176
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1176
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1176
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1176
    (&kernelContext_3)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1176
    threadgroup array<uint, int(16384)> stg_1;

#line 1176
    (&kernelContext_3)->stg_0 = &stg_1;

#line 1185
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1191
    (&kernelContext_3)->_stgBase_0 = 0U;

#line 1191
    filterPair_0(pair_1, lid_0.x, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_3);


    return;
}
