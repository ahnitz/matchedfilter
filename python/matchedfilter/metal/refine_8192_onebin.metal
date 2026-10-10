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


#line 180 "mm_8192_refineListed_onebin.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 180
    return;
}


#line 152
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 152
    return float2(*(b_0+i_0)) ;
}


#line 252
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 252
    float _S2 = a_0.x;

#line 252
    float _S3 = b_1.x;

#line 252
    float _S4 = a_0.y;

#line 252
    float _S5 = b_1.y;

#line 252
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 457
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 459
    float2 t1_0 = *a_1 - *c_0;

#line 459
    float2 t2_0 = *b_2 + *d_1;

#line 459
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 461
    *b_2 = t1_0 + j3_0;

#line 461
    *c_0 = t0_0 - t2_0;

#line 461
    *d_1 = t1_0 - j3_0;
    return;
}


#line 251
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 251
    float _S6 = a_2.x;

#line 251
    float _S7 = b_3.x;

#line 251
    float _S8 = a_2.y;

#line 251
    float _S9 = b_3.y;

#line 251
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 493
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 500
    uint n1_0 = 0U;
    for(;;)
    {

#line 501
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 501
            break;
        }

#line 501
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 501
        n1_0 = n1_0 + 1U;

#line 501
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 502
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 502
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 503
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 503
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 504
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 504
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 504
    uint k2_0 = 0U;
    for(;;)
    {

#line 505
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 505
            break;
        }

#line 505
        uint _S10 = 4U * k2_0;

#line 505
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 505
        k2_0 = k2_0 + 1U;

#line 505
    }

    float2 t_0 = (*r_0)[int(1)];

#line 507
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 507
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 508
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 508
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 509
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 509
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 510
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 510
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 511
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 511
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 512
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 512
    (*r_0)[int(14)] = t_5;
    return;
}


#line 26 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 253 "mm_8192_refineListed_onebin.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 255
    uint j_0 = d_2 / _S11;

#line 255
    uint m_0 = d_2 % _S11;

#line 255
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 256
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 256
    }
    else
    {

#line 256
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 256
    }

#line 256
    return _S12;
}


#line 8028 "hlsl.meta.slang"
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


#line 644 "mm_8192_refineListed_onebin.slang"
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
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 631
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S13 = (1U << lgSpan_0) - 1U;
    uint _S14 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

#line 636
    uint d_3 = 0U;
    for(;;)
    {

#line 637
        if(d_3 < 16U)
        {
        }
        else
        {

#line 637
            break;
        }

#line 638
        uint p_0 = computeWant_0(d_3, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
        uint rem_0 = p_0 & _S14;
        src_0[d_3] = (rem_0 >> lgSpan_0) * 512U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S13);

#line 637
        d_3 = d_3 + 1U;

#line 637
    }

#line 642
    thread array<float, int(16)> xr_0;
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 643
    uint j_1 = 0U;
    for(;;)
    {

#line 644
        if(j_1 < 16U)
        {
        }
        else
        {

#line 644
            break;
        }

#line 644
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 512U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].x)));

#line 644
        j_1 = j_1 + 1U;

#line 644
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 645
    d_3 = 0U;
    for(;;)
    {

#line 646
        if(d_3 < 16U)
        {
        }
        else
        {

#line 646
            break;
        }

#line 646
        xr_0[d_3] = (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_3]])));

#line 646
        d_3 = d_3 + 1U;

#line 646
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 647
    j_1 = 0U;
    for(;;)
    {

#line 648
        if(j_1 < 16U)
        {
        }
        else
        {

#line 648
            break;
        }

#line 648
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 512U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].y)));

#line 648
        j_1 = j_1 + 1U;

#line 648
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 649
    d_3 = 0U;
    for(;;)
    {

#line 650
        if(d_3 < 16U)
        {
        }
        else
        {

#line 650
            break;
        }

#line 650
        (*r_1)[d_3] = float2(xr_0[d_3], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_3]]))));

#line 650
        d_3 = d_3 + 1U;

#line 650
    }
    return;
}


#line 468
void dft2_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    float2 a_3 = (*r_2)[o_0];

#line 470
    float2 b_4 = (*r_2)[o_0 + 1U];

#line 470
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 470
    (*r_2)[o_0 + 1U] = a_3 - b_4;
    return;
}


#line 596
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 596
    uint b_5 = 0U;

#line 606
    for(;;)
    {

#line 606
        if(b_5 < 8U)
        {
        }
        else
        {

#line 606
            break;
        }

#line 606
        dft2_0(r_3, b_5 * 2U);

#line 606
        b_5 = b_5 + 1U;

#line 606
    }

    return;
}


#line 743
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 743
    uint _S15;

#line 743
    uint k2_1;

#line 743
    float cr_0;

#line 743
    float ci_0;

#line 743
    uint _S16;

#line 743
    uint _S17;

#line 743
    uint _S18;

#line 743
    for(;;)
    {

#line 743
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(512U);

#line 11
                _S15 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(8192U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 511U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 8192.0);
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
                uint per_2 = 16U / max(512U, 1U);
                uint _S22 = max(32U, 1U);

#line 38
                _S16 = _S22;
                uint blk2_2 = tid_0 / _S22;

#line 39
                uint lane2_2 = tid_0 % _S22;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 512U, 8192U, blk_2, lane_2, per_2, _S22, 512U, blk2_2, lane2_2, kernelContext_1);

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


                uint lgTB_1 = firstbithigh_0(32U);

#line 11
                _S17 = lgTB_1;

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 31U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 512.0);
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
                uint _S26 = max(2U, 1U);

#line 38
                _S18 = _S26;
                uint blk2_3 = tid_0 / _S26;

#line 39
                uint lane2_3 = tid_0 % _S26;

#line 39
                exchange_0(r_4, _S15, lgTB_1, 32U, 512U, blk_3, lane_3, per_3, _S26, 32U, blk2_3, lane2_3, kernelContext_1);

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


                uint lgTB_2 = firstbithigh_0(2U);

                uint blk_4 = tid_0 >> lgTB_2;
                uint lane_4 = tid_0 & 1U;


                dft16_0(r_4);

#line 26
                float2 tw_2 = mfTwiddle_0(6.28318548202514648 * float(lane_4) / 32.0);
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
                exchange_0(r_4, _S17, lgTB_2, 2U, 32U, blk_4, lane_4, per_4, _S30, 2U, blk2_4, lane2_4, kernelContext_1);

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

#line 746 "mm_8192_refineListed_onebin.slang"
    return;
}


#line 712
uint lgOf_0(uint i_1)
{

#line 712
    uint _S31;

#line 712
    if(i_1 < 3U)
    {

#line 712
        _S31 = 4U;

#line 712
    }
    else
    {

#line 712
        _S31 = 1U;

#line 712
    }

#line 712
    return _S31;
}


#line 714
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 718
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 718
    uint lg_2 = lgOf_0(1U);

#line 718
    uint lg_3 = lgOf_0(0U);

#line 723
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 758
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_2)
{

#line 772
    kernelContext_2->_tid_0 = tid_1;
    uint _S32 = pair_0 / ntmpl_1;

#line 773
    uint _S33 = pair_0 % ntmpl_1;

    thread array<float2, int(16)> r_5;

#line 775
    uint n2_0 = 0U;

#line 786
    for(;;)
    {

#line 786
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 786
            break;
        }

#line 787
        uint idx_0 = tid_1 + 512U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S32 * 8192U + idx_0), cload_0(tmpl_0, _S33 * 8192U + idx_0));

#line 786
        n2_0 = n2_0 + 1U;

#line 786
    }

#line 786
    transform_0(&r_5, tid_1, kernelContext_2);

#line 815
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 820
    bool _S34 = tid_1 == 0U;

#line 820
    if(_S34)
    {

#line 820
        (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0] = thrBits_1;

#line 820
        (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U] = 4294967295U;

#line 820
    }



    float2 _S35 = float2(0.0, 0.0);

#line 824
    bool live_0;

    if(winStart_2 == 0U)
    {

#line 826
        live_0 = winEnd_2 >= 8192U;

#line 826
    }
    else
    {

#line 826
        live_0 = false;

#line 826
    }

#line 826
    uint threadBestBits_0;

#line 826
    uint threadBestSlot_0;

#line 826
    uint winner_0;

#line 826
    float2 threadBestVal_0;

#line 826
    if(live_0)
    {

#line 826
        threadBestBits_0 = thrBits_1;

#line 826
        threadBestSlot_0 = 4294967295U;

#line 826
        threadBestVal_0 = _S35;

#line 826
        winner_0 = 0U;
        for(;;)
        {

#line 827
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 827
                break;
            }

#line 828
            float _rx_0 = r_5[winner_0].x;

#line 828
            float _ry_0 = r_5[winner_0].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > threadBestBits_0)
            {
                uint _S36 = tid_1 * 16U + winner_0;
                float2 _S37 = float2(_rx_0, _ry_0);

#line 833
                threadBestBits_0 = magBits_0;

#line 833
                threadBestSlot_0 = _S36;

#line 833
                threadBestVal_0 = _S37;

#line 830
            }

#line 827
            winner_0 = winner_0 + 1U;

#line 827
        }

#line 826
    }
    else
    {

#line 826
        threadBestBits_0 = thrBits_1;

#line 826
        threadBestSlot_0 = 4294967295U;

#line 826
        threadBestVal_0 = _S35;

#line 826
        winner_0 = 0U;

#line 837
        for(;;)
        {

#line 837
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 837
                break;
            }

#line 838
            uint _S38 = tid_1 * 16U + winner_0;

#line 838
            uint idx_1 = slotToIndex_0(_S38);
            if(idx_1 >= winStart_2)
            {

#line 839
                live_0 = idx_1 < winEnd_2;

#line 839
            }
            else
            {

#line 839
                live_0 = false;

#line 839
            }
            float _rx_1 = r_5[winner_0].x;

#line 840
            float _ry_1 = r_5[winner_0].y;

#line 840
            uint magBits_1;
            if(live_0)
            {

#line 841
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 841
            }
            else
            {

#line 841
                magBits_1 = 0U;

#line 841
            }
            if(magBits_1 > threadBestBits_0)
            {

                float2 _S39 = float2(_rx_1, _ry_1);

#line 845
                threadBestBits_0 = magBits_1;

#line 845
                threadBestSlot_0 = _S38;

#line 845
                threadBestVal_0 = _S39;

#line 842
            }

#line 837
            winner_0 = winner_0 + 1U;

#line 837
        }

#line 826
    }

#line 850
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(threadBestBits_0);
    bool _S40 = simd_is_first();

#line 854
    if(_S40)
    {

#line 854
        live_0 = wm_0 > thrBits_1;

#line 854
    }
    else
    {

#line 854
        live_0 = false;

#line 854
    }

#line 854
    if(live_0)
    {

#line 854
        uint _S41 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0])), wm_0, memory_order_relaxed);

#line 854
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(threadBestBits_0 > thrBits_1)
    {

#line 861
        live_0 = threadBestBits_0 == (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0];

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
        winner_0 = threadBestSlot_0;

#line 861
    }
    else
    {

#line 861
        winner_0 = 4294967295U;

#line 861
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S42 = simd_is_first();

#line 866
    if(_S42)
    {

#line 866
        live_0 = waveWinner_0 != 4294967295U;

#line 866
    }
    else
    {

#line 866
        live_0 = false;

#line 866
    }

#line 866
    if(live_0)
    {

#line 867
        uint _S43 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 866
    }

#line 871
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(threadBestSlot_0 == (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U])
    {

#line 873
        live_0 = threadBestSlot_0 != 4294967295U;

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

#line 874
        *(peakIdx_0+pair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 874
        *(peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 873
    }



    if(_S34)
    {

#line 877
        live_0 = ((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U]) == 4294967295U;

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
        *(peakVal_0+pair_0) = packed_float2(_S35) ;

#line 877
    }

#line 1014
    return;
}


#line 1512
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1512
    thread KernelContext_0 kernelContext_3;

#line 1512
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 1512
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1512
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1512
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1512
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1512
    (&kernelContext_3)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1512
    threadgroup array<uint, int(8192)> stg_1;

#line 1512
    (&kernelContext_3)->stg_0 = &stg_1;

#line 1521
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1527
    (&kernelContext_3)->_stgBase_0 = 0U;
    thread uint ws_0 = entryPointParams_1->winStart_1;

#line 1528
    thread uint we_0 = entryPointParams_1->winEnd_1;
    uint _S44 = pair_1 / entryPointParams_1->ntmpl_0;

#line 1529
    rowWindow_0(_S44, &ws_0, &we_0);

#line 1529
    filterPair_0(pair_1, lid_0.x, (&kernelContext_3)->entryPointParams_data_0, (&kernelContext_3)->entryPointParams_tmpl_0, (&kernelContext_3)->entryPointParams_peakIdx_0, (&kernelContext_3)->entryPointParams_peakVal_0, entryPointParams_1->ntmpl_0, ws_0, we_0, (&kernelContext_3)->entryPointParams_0->binsize_0, (&kernelContext_3)->entryPointParams_0->binShift_0, (&kernelContext_3)->entryPointParams_0->nbins_0, (&kernelContext_3)->entryPointParams_0->thrBits_0, &kernelContext_3);


    return;
}
