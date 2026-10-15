#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;

#line 11218 "hlsl.meta.slang"
uint firstbithigh_0(uint value_0)
{

#line 11231
    if(value_0 == 0U)
    {

#line 11232
        return 4294967295U;
    }

#line 11233
    uint _S1 = clz(value_0);

#line 11233
    return 31U - _S1;
}


#line 193 "mm_8192_refineListed_onebin.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 193
    return;
}


#line 168
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 168
    return float2(*(b_0+i_0)) ;
}


#line 267
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 267
    float _S2 = a_0.x;

#line 267
    float _S3 = b_1.x;

#line 267
    float _S4 = a_0.y;

#line 267
    float _S5 = b_1.y;

#line 267
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 472
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 474
    float2 t1_0 = *a_1 - *c_0;

#line 474
    float2 t2_0 = *b_2 + *d_1;

#line 474
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 476
    *b_2 = t1_0 + j3_0;

#line 476
    *c_0 = t0_0 - t2_0;

#line 476
    *d_1 = t1_0 - j3_0;
    return;
}


#line 266
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 266
    float _S6 = a_2.x;

#line 266
    float _S7 = b_3.x;

#line 266
    float _S8 = a_2.y;

#line 266
    float _S9 = b_3.y;

#line 266
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 508
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 515
    uint n1_0 = 0U;
    for(;;)
    {

#line 516
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 516
            break;
        }

#line 516
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 516
        n1_0 = n1_0 + 1U;

#line 516
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 517
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 517
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 518
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 518
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 519
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 519
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 519
    uint k2_0 = 0U;
    for(;;)
    {

#line 520
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 520
            break;
        }

#line 520
        uint _S10 = 4U * k2_0;

#line 520
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 520
        k2_0 = k2_0 + 1U;

#line 520
    }

    float2 t_0 = (*r_0)[int(1)];

#line 522
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 522
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 523
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 523
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 524
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 524
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 525
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 525
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 526
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 526
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 527
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 527
    (*r_0)[int(14)] = t_5;
    return;
}


#line 84 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 268 "mm_8192_refineListed_onebin.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 270
    uint j_0 = d_2 / _S11;

#line 270
    uint m_0 = d_2 % _S11;

#line 270
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 271
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 271
    }
    else
    {

#line 271
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 271
    }

#line 271
    return _S12;
}


#line 8225 "hlsl.meta.slang"
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


#line 678 "mm_8192_refineListed_onebin.slang"
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


#line 657
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S13 = (1U << lgSpan_0) - 1U;
    uint _S14 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

#line 662
    uint d_3 = 0U;
    for(;;)
    {

#line 663
        if(d_3 < 16U)
        {
        }
        else
        {

#line 663
            break;
        }

#line 664
        uint p_0 = computeWant_0(d_3, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
        uint rem_0 = p_0 & _S14;
        src_0[d_3] = (rem_0 >> lgSpan_0) * 512U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S13);

#line 663
        d_3 = d_3 + 1U;

#line 663
    }

#line 668
    thread array<float, int(16)> xr_0;

#line 675
    bool local_0 = TB_1 <= 32U;

    if((TB_1 << 4U) <= 32U)
    {

#line 677
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 677
    }
    else
    {

#line 677
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 677
    }

#line 677
    uint j_1 = 0U;
    for(;;)
    {

#line 678
        if(j_1 < 16U)
        {
        }
        else
        {

#line 678
            break;
        }

#line 678
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 512U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].x)));

#line 678
        j_1 = j_1 + 1U;

#line 678
    }
    if(local_0)
    {

#line 679
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 679
    }
    else
    {

#line 679
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 679
    }

#line 679
    d_3 = 0U;
    for(;;)
    {

#line 680
        if(d_3 < 16U)
        {
        }
        else
        {

#line 680
            break;
        }

#line 680
        xr_0[d_3] = (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_3]])));

#line 680
        d_3 = d_3 + 1U;

#line 680
    }
    if(local_0)
    {

#line 681
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 681
    }
    else
    {

#line 681
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 681
    }

#line 681
    j_1 = 0U;
    for(;;)
    {

#line 682
        if(j_1 < 16U)
        {
        }
        else
        {

#line 682
            break;
        }

#line 682
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 512U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].y)));

#line 682
        j_1 = j_1 + 1U;

#line 682
    }
    if(local_0)
    {

#line 683
        simdgroup_barrier(mem_flags::mem_threadgroup);

#line 683
    }
    else
    {

#line 683
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 683
    }

#line 683
    d_3 = 0U;
    for(;;)
    {

#line 684
        if(d_3 < 16U)
        {
        }
        else
        {

#line 684
            break;
        }

#line 684
        (*r_1)[d_3] = float2(xr_0[d_3], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_3]]))));

#line 684
        d_3 = d_3 + 1U;

#line 684
    }

#line 695
    return;
}


#line 483
void dft2_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    float2 a_3 = (*r_2)[o_0];

#line 485
    float2 b_4 = (*r_2)[o_0 + 1U];

#line 485
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 485
    (*r_2)[o_0 + 1U] = a_3 - b_4;
    return;
}


#line 611
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 611
    uint b_5 = 0U;

#line 621
    for(;;)
    {

#line 621
        if(b_5 < 8U)
        {
        }
        else
        {

#line 621
            break;
        }

#line 621
        dft2_0(r_3, b_5 * 2U);

#line 621
        b_5 = b_5 + 1U;

#line 621
    }

    return;
}


#line 799
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 799
    uint _S15;

#line 799
    uint k2_1;

#line 799
    float cr_0;

#line 799
    float ci_0;

#line 799
    uint _S16;

#line 799
    uint _S17;

#line 799
    uint _S18;

#line 799
    for(;;)
    {

#line 799
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

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 8192.0f);
                float _S19 = tw_0.x;

#line 40
                float _S20 = tw_0.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S19 - ci_0 * _S20;
                    float _S21 = cr_0 * _S20 + ci_0 * _S19;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S21;

#line 42
                }

#line 50
                uint per_2 = 16U / max(512U, 1U);
                uint _S22 = max(32U, 1U);

#line 51
                _S16 = _S22;
                uint blk2_2 = tid_0 / _S22;

#line 52
                uint lane2_2 = tid_0 % _S22;

#line 52
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

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 512.0f);
                float _S23 = tw_1.x;

#line 40
                float _S24 = tw_1.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S23 - ci_0 * _S24;
                    float _S25 = cr_0 * _S24 + ci_0 * _S23;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S25;

#line 42
                }

#line 50
                uint per_3 = 16U / _S16;
                uint _S26 = max(2U, 1U);

#line 51
                _S18 = _S26;
                uint blk2_3 = tid_0 / _S26;

#line 52
                uint lane2_3 = tid_0 % _S26;

#line 52
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

#line 39
                float2 tw_2 = mfTwiddle_0(6.28318548202514648f * float(lane_4) / 32.0f);
                float _S27 = tw_2.x;

#line 40
                float _S28 = tw_2.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_2 = cr_0 * _S27 - ci_0 * _S28;
                    float _S29 = cr_0 * _S28 + ci_0 * _S27;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_2;

#line 42
                    ci_0 = _S29;

#line 42
                }

#line 50
                uint per_4 = 16U / _S18;
                uint _S30 = max(0U, 1U);
                uint blk2_4 = tid_0 / _S30;

#line 52
                uint lane2_4 = tid_0 % _S30;

#line 52
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

#line 56
    innermost_0(r_4);

#line 802 "mm_8192_refineListed_onebin.slang"
    return;
}


#line 756
uint lgOf_0(uint i_1)
{

#line 756
    uint _S31;

#line 756
    if(i_1 < 3U)
    {

#line 756
        _S31 = 4U;

#line 756
    }
    else
    {

#line 756
        _S31 = 1U;

#line 756
    }

#line 756
    return _S31;
}


#line 758
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 762
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 762
    uint lg_2 = lgOf_0(1U);

#line 762
    uint lg_3 = lgOf_0(0U);

#line 767
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 822
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_2)
{

#line 842
    kernelContext_2->_tid_0 = tid_1;
    uint _S32 = pair_0 / ntmpl_1;

#line 843
    uint _S33 = pair_0 % ntmpl_1;

#line 848
    thread array<float2, int(16)> r_5;

#line 848
    uint n2_0 = 0U;

#line 859
    for(;;)
    {

#line 859
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 859
            break;
        }

#line 860
        uint idx_0 = tid_1 + 512U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S32 * 8192U + idx_0), cload_0(tmpl_0, _S33 * 8192U + idx_0));

#line 859
        n2_0 = n2_0 + 1U;

#line 859
    }

#line 859
    transform_0(&r_5, tid_1, kernelContext_2);

#line 888
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 931
    bool _S34 = tid_1 == 0U;

#line 931
    if(_S34)
    {

#line 931
        (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0] = thrBits_1;

#line 931
        (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U] = 4294967295U;

#line 931
    }



    float2 _S35 = float2(0.0f, 0.0f);

#line 935
    bool live_0;

    if(winStart_2 == 0U)
    {

#line 937
        live_0 = winEnd_2 >= 8192U;

#line 937
    }
    else
    {

#line 937
        live_0 = false;

#line 937
    }

#line 937
    uint threadBestBits_0;

#line 937
    uint threadBestSlot_0;

#line 937
    uint winner_0;

#line 937
    float2 threadBestVal_0;

#line 937
    if(live_0)
    {

#line 937
        threadBestBits_0 = thrBits_1;

#line 937
        threadBestSlot_0 = 4294967295U;

#line 937
        threadBestVal_0 = _S35;

#line 937
        winner_0 = 0U;
        for(;;)
        {

#line 938
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 938
                break;
            }

#line 939
            float _rx_0 = r_5[winner_0].x;

#line 939
            float _ry_0 = r_5[winner_0].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > threadBestBits_0)
            {
                uint _S36 = tid_1 * 16U + winner_0;
                float2 _S37 = float2(_rx_0, _ry_0);

#line 944
                threadBestBits_0 = magBits_0;

#line 944
                threadBestSlot_0 = _S36;

#line 944
                threadBestVal_0 = _S37;

#line 941
            }

#line 938
            winner_0 = winner_0 + 1U;

#line 938
        }

#line 937
    }
    else
    {

#line 937
        threadBestBits_0 = thrBits_1;

#line 937
        threadBestSlot_0 = 4294967295U;

#line 937
        threadBestVal_0 = _S35;

#line 937
        winner_0 = 0U;

#line 948
        for(;;)
        {

#line 948
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 948
                break;
            }

#line 949
            uint _S38 = tid_1 * 16U + winner_0;

#line 949
            uint idx_1 = slotToIndex_0(_S38);
            if(idx_1 >= winStart_2)
            {

#line 950
                live_0 = idx_1 < winEnd_2;

#line 950
            }
            else
            {

#line 950
                live_0 = false;

#line 950
            }
            float _rx_1 = r_5[winner_0].x;

#line 951
            float _ry_1 = r_5[winner_0].y;

#line 951
            uint magBits_1;
            if(live_0)
            {

#line 952
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 952
            }
            else
            {

#line 952
                magBits_1 = 0U;

#line 952
            }
            if(magBits_1 > threadBestBits_0)
            {

                float2 _S39 = float2(_rx_1, _ry_1);

#line 956
                threadBestBits_0 = magBits_1;

#line 956
                threadBestSlot_0 = _S38;

#line 956
                threadBestVal_0 = _S39;

#line 953
            }

#line 948
            winner_0 = winner_0 + 1U;

#line 948
        }

#line 937
    }

#line 961
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(threadBestBits_0);
    bool _S40 = simd_is_first();

#line 965
    if(_S40)
    {

#line 965
        live_0 = wm_0 > thrBits_1;

#line 965
    }
    else
    {

#line 965
        live_0 = false;

#line 965
    }

#line 965
    if(live_0)
    {

#line 965
        uint _S41 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0])), wm_0, memory_order_relaxed);

#line 965
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(threadBestBits_0 > thrBits_1)
    {

#line 972
        live_0 = threadBestBits_0 == (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0];

#line 972
    }
    else
    {

#line 972
        live_0 = false;

#line 972
    }

#line 972
    if(live_0)
    {

#line 972
        winner_0 = threadBestSlot_0;

#line 972
    }
    else
    {

#line 972
        winner_0 = 4294967295U;

#line 972
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S42 = simd_is_first();

#line 977
    if(_S42)
    {

#line 977
        live_0 = waveWinner_0 != 4294967295U;

#line 977
    }
    else
    {

#line 977
        live_0 = false;

#line 977
    }

#line 977
    if(live_0)
    {

#line 978
        uint _S43 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 977
    }

#line 982
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(threadBestSlot_0 == (*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U])
    {

#line 984
        live_0 = threadBestSlot_0 != 4294967295U;

#line 984
    }
    else
    {

#line 984
        live_0 = false;

#line 984
    }

#line 984
    if(live_0)
    {

#line 985
        *(peakIdx_0+pair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 985
        *(peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 984
    }



    if(_S34)
    {

#line 988
        live_0 = ((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + 1U]) == 4294967295U;

#line 988
    }
    else
    {

#line 988
        live_0 = false;

#line 988
    }

#line 988
    if(live_0)
    {

#line 989
        *(peakIdx_0+pair_0) = int(-1);

#line 989
        *(peakVal_0+pair_0) = packed_float2(_S35) ;

#line 988
    }

#line 1202
    return;
}


#line 1844
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1844
    thread KernelContext_0 kernelContext_3;

#line 1844
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 1844
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1844
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1844
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1844
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1844
    (&kernelContext_3)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1844
    threadgroup array<uint, int(8192)> stg_1;

#line 1844
    (&kernelContext_3)->stg_0 = &stg_1;

#line 1853
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1859
    (&kernelContext_3)->_stgBase_0 = 0U;
    thread uint ws_0 = entryPointParams_1->winStart_1;

#line 1860
    thread uint we_0 = entryPointParams_1->winEnd_1;
    uint _S44 = pair_1 / entryPointParams_1->ntmpl_0;

#line 1861
    rowWindow_0(_S44, &ws_0, &we_0);

#line 1861
    filterPair_0(pair_1, lid_0.x, (&kernelContext_3)->entryPointParams_data_0, (&kernelContext_3)->entryPointParams_tmpl_0, (&kernelContext_3)->entryPointParams_peakIdx_0, (&kernelContext_3)->entryPointParams_peakVal_0, entryPointParams_1->ntmpl_0, ws_0, we_0, (&kernelContext_3)->entryPointParams_0->binsize_0, (&kernelContext_3)->entryPointParams_0->binShift_0, (&kernelContext_3)->entryPointParams_0->nbins_0, (&kernelContext_3)->entryPointParams_0->thrBits_0, &kernelContext_3);


    return;
}
