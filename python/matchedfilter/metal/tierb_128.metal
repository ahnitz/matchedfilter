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


#line 152 "mm_128_fusedTierB.slang"
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
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 459
    float2 t1_0 = *a_1 - *c_0;

#line 459
    float2 t2_0 = *b_2 + *d_0;

#line 459
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 461
    *b_2 = t1_0 + j3_0;

#line 461
    *c_0 = t0_0 - t2_0;

#line 461
    *d_0 = t1_0 - j3_0;
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


#line 253 "mm_128_fusedTierB.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 255
    uint j_0 = d_1 / _S11;

#line 255
    uint m_0 = d_1 % _S11;

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
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 256
    }

#line 256
    return _S12;
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


#line 240 "mm_128_fusedTierB.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(256)> threadgroup* stg_0;
};


#line 240
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 240
    uint _S13 = 2U * i_1;

#line 240
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13] = (as_type<uint>((v_0.x)));

#line 240
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13 + 1U] = (as_type<uint>((v_0.y)));

#line 240
    return;
}


#line 241
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 241
    uint _S14 = 2U * i_2;

#line 241
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 653
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 654
    uint j_1;

#line 665
    thread array<float2, int(16)> out_0;

#line 665
    uint z_0 = 0U;
    for(;;)
    {

#line 666
        if(z_0 < 16U)
        {
        }
        else
        {

#line 666
            break;
        }

#line 666
        out_0[z_0] = float2(0.0, 0.0);

#line 666
        z_0 = z_0 + 1U;

#line 666
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S15 = p0_0 & lenMask_0;

#line 672
    uint _S16 = (_S15 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 672
    uint c_1 = 0U;

    for(;;)
    {

#line 674
        if(c_1 < 1U)
        {
        }
        else
        {

#line 674
            break;
        }

#line 675
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 675
        j_1 = 0U;
        for(;;)
        {

#line 676
            if(j_1 < 16U)
            {
            }
            else
            {

#line 676
                break;
            }

#line 676
            stgPut_0(j_1 * 8U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 676
            j_1 = j_1 + 1U;

#line 676
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 677
        uint d_2 = 0U;
        for(;;)
        {

#line 678
            if(d_2 < 16U)
            {
            }
            else
            {

#line 678
                break;
            }

#line 679
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S17 = pz_0 & lenMask_0;
            uint az_0 = (_S17 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S17 & spanMask_0);

#line 681
            float2 _S18 = stgGet_0(_S16 + az_0 - c_1 * 16U * 8U, kernelContext_2);


            out_0[d_2] = _S18;

#line 678
            d_2 = d_2 + 1U;

#line 678
        }

#line 674
        c_1 = c_1 + 1U;

#line 674
    }

#line 674
    j_1 = 0U;

#line 687
    for(;;)
    {

#line 687
        if(j_1 < 16U)
        {
        }
        else
        {

#line 687
            break;
        }

#line 687
        (*r_1)[j_1] = out_0[j_1];

#line 687
        j_1 = j_1 + 1U;

#line 687
    }
    return;
}


#line 477
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_4;

#line 481
    uint s_0 = 1U;
    for(;;)
    {

#line 482
        if(s_0 < 8U)
        {
        }
        else
        {

#line 482
            break;
        }

#line 482
        uint j_2 = 0U;
        for(;;)
        {

#line 483
            if(j_2 < 4U)
            {
            }
            else
            {

#line 483
                break;
            }

#line 484
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S19 = o_0 + j_2;

#line 487
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0)), (*r_2)[_S19 + 4U]);
            uint _S20 = ((j_2 - k_0) << 1U) + k_0;

#line 488
            b_4[_S20] = (*r_2)[_S19] + t_6;

#line 488
            b_4[_S20 + s_0] = (*r_2)[_S19] - t_6;

#line 483
            j_2 = j_2 + 1U;

#line 483
        }

#line 483
        uint i_3 = 0U;

#line 490
        for(;;)
        {

#line 490
            if(i_3 < 8U)
            {
            }
            else
            {

#line 490
                break;
            }

#line 490
            (*r_2)[o_0 + i_3] = b_4[i_3];

#line 490
            i_3 = i_3 + 1U;

#line 490
        }

#line 482
        s_0 = s_0 << 1U;

#line 482
    }

#line 492
    return;
}


#line 596
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 596
    uint b_5 = 0U;

#line 604
    for(;;)
    {

#line 604
        if(b_5 < 2U)
        {
        }
        else
        {

#line 604
            break;
        }

#line 604
        dft8_0(r_3, b_5 * 8U);

#line 604
        b_5 = b_5 + 1U;

#line 604
    }



    return;
}


#line 743
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 743
    for(;;)
    {

#line 743
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
                float _S21 = tw_0.x;

#line 27
                float _S22 = tw_0.y;

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
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S21 - ci_0 * _S22;
                    float _S23 = cr_0 * _S22 + ci_0 * _S21;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S23;

#line 29
                }

#line 37
                uint per_2 = 16U / max(8U, 1U);
                uint _S24 = max(0U, 1U);
                uint blk2_2 = tid_0 / _S24;

#line 39
                uint lane2_2 = tid_0 % _S24;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 8U, 128U, blk_2, lane_2, per_2, _S24, 8U, blk2_2, lane2_2, kernelContext_3);

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

#line 746 "mm_128_fusedTierB.slang"
    return;
}


#line 712
uint lgOf_0(uint i_4)
{

#line 712
    uint _S25;

#line 712
    if(i_4 < 1U)
    {

#line 712
        _S25 = 4U;

#line 712
    }
    else
    {

#line 712
        if(i_4 == 1U)
        {

#line 712
            _S25 = 3U;

#line 712
        }
        else
        {

#line 712
            _S25 = 1U;

#line 712
        }

#line 712
    }

#line 712
    return _S25;
}


#line 714
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 718
    uint lg_1 = lgOf_0(0U);

#line 723
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 758
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 772
    kernelContext_4->_tid_0 = tid_1;
    uint _S26 = pair_0 / ntmpl_1;

#line 773
    uint _S27 = pair_0 % ntmpl_1;

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
        uint idx_0 = tid_1 + 8U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S26 * 128U + idx_0), cload_0(tmpl_0, _S27 * 128U + idx_0));

#line 786
        n2_0 = n2_0 + 1U;

#line 786
    }

#line 786
    transform_0(&r_5, tid_1, kernelContext_4);

#line 815
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 815
    uint b_6 = tid_1;

#line 889
    for(;;)
    {

#line 889
        if(b_6 < nbins_1)
        {
        }
        else
        {

#line 889
            break;
        }

#line 889
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6] = thrBits_1;

#line 889
        b_6 = b_6 + 8U;

#line 889
    }
    bool _S28 = nbins_1 == 1U;

#line 890
    bool live_0;

#line 890
    if(_S28)
    {

#line 890
        live_0 = tid_1 == 0U;

#line 890
    }
    else
    {

#line 890
        live_0 = false;

#line 890
    }

#line 890
    if(live_0)
    {

#line 890
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 890
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 895
    uint i_5 = 0U;
    for(;;)
    {

#line 896
        if(i_5 < 16U)
        {
        }
        else
        {

#line 896
            break;
        }

#line 897
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_5);
        if(idx_1 >= winStart_1)
        {

#line 898
            live_0 = idx_1 < winEnd_1;

#line 898
        }
        else
        {

#line 898
            live_0 = false;

#line 898
        }



        float _rx_0 = r_5[i_5].x;

#line 902
        float _ry_0 = r_5[i_5].y;
        if(live_0)
        {

#line 903
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 903
        }
        else
        {

#line 903
            n2_0 = 0U;

#line 903
        }

#line 903
        myMag_0[i_5] = n2_0;
        uint off_0 = idx_1 - winStart_1;

#line 911
        if(live_0)
        {

#line 911
            if(binShift_1 >= int(0))
            {

#line 911
                b_6 = off_0 >> uint(binShift_1);

#line 911
            }
            else
            {

#line 911
                uint _S29 = off_0 / binsize_1;

#line 911
                b_6 = _S29;

#line 911
            }

#line 911
        }
        else
        {

#line 911
            b_6 = 0U;

#line 911
        }

#line 911
        myBin_0[i_5] = b_6;

#line 911
        bool _S30;



        if(nbins_1 > 1U)
        {

#line 915
            _S30 = (myMag_0[i_5]) > thrBits_1;

#line 915
        }
        else
        {

#line 915
            _S30 = false;

#line 915
        }

#line 915
        if(_S30)
        {

#line 916
            uint _S31 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), myMag_0[i_5], memory_order_relaxed);

#line 915
        }

#line 896
        i_5 = i_5 + 1U;

#line 896
    }

#line 896
    uint winner_0;

#line 928
    if(_S28)
    {

#line 928
        winner_0 = thrBits_1;

#line 928
        i_5 = 0U;


        for(;;)
        {

#line 931
            if(i_5 < 16U)
            {
            }
            else
            {

#line 931
                break;
            }

#line 931
            uint _S32 = max(winner_0, myMag_0[i_5]);

#line 931
            uint i_6 = i_5 + 1U;

#line 931
            winner_0 = _S32;

#line 931
            i_5 = i_6;

#line 931
        }

        uint wm_0 = simd_max(winner_0);
        bool _S33 = simd_is_first();

#line 934
        if(_S33)
        {

#line 934
            live_0 = wm_0 > thrBits_1;

#line 934
        }
        else
        {

#line 934
            live_0 = false;

#line 934
        }

#line 934
        if(live_0)
        {

#line 934
            uint _S34 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 934
        }

#line 928
    }

#line 949
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 956
    if(_S28)
    {

#line 956
        winner_0 = 4294967295U;

#line 956
        i_5 = 0U;


        for(;;)
        {

#line 959
            if(i_5 < 16U)
            {
            }
            else
            {

#line 959
                break;
            }

#line 960
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 960
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 960
            }
            else
            {

#line 960
                live_0 = false;

#line 960
            }

#line 960
            if(live_0)
            {

#line 960
                winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 960
            }

#line 959
            i_5 = i_5 + 1U;

#line 959
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S35 = simd_is_first();

#line 964
        if(_S35)
        {

#line 964
            live_0 = waveWinner_0 != 4294967295U;

#line 964
        }
        else
        {

#line 964
            live_0 = false;

#line 964
        }

#line 964
        if(live_0)
        {

#line 965
            uint _S36 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 964
        }

#line 969
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 969
        i_5 = 0U;
        for(;;)
        {

#line 970
            if(i_5 < 16U)
            {
            }
            else
            {

#line 970
                break;
            }

#line 971
            uint _S37 = tid_1 * 16U + i_5;

#line 971
            if(_S37 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 972
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S37));

#line 972
                *(peakVal_0+pair_0) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 971
            }

#line 970
            i_5 = i_5 + 1U;

#line 970
        }

#line 980
        if(tid_1 == 0U)
        {

#line 980
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 980
        }
        else
        {

#line 980
            live_0 = false;

#line 980
        }

#line 980
        if(live_0)
        {

#line 981
            *(peakIdx_0+pair_0) = int(-1);

#line 981
            *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 980
        }

#line 956
    }
    else
    {

#line 956
        i_5 = 0U;

#line 989
        for(;;)
        {

#line 989
            if(i_5 < 16U)
            {
            }
            else
            {

#line 989
                break;
            }

#line 990
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 990
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]];

#line 990
            }
            else
            {

#line 990
                live_0 = false;

#line 990
            }

#line 990
            myMag_0[i_5] = uint(live_0);

#line 989
            i_5 = i_5 + 1U;

#line 989
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 992
        b_6 = tid_1;
        for(;;)
        {

#line 993
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 993
                break;
            }

#line 993
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6] = 4294967295U;

#line 993
            b_6 = b_6 + 8U;

#line 993
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 994
        i_5 = 0U;
        for(;;)
        {

#line 995
            if(i_5 < 16U)
            {
            }
            else
            {

#line 995
                break;
            }

#line 996
            if((myMag_0[i_5]) != 0U)
            {

#line 996
                uint _S38 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), tid_1 * 16U + i_5, memory_order_relaxed);

#line 996
            }

#line 995
            i_5 = i_5 + 1U;

#line 995
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 997
        i_5 = 0U;
        for(;;)
        {

#line 998
            if(i_5 < 16U)
            {
            }
            else
            {

#line 998
                break;
            }

#line 999
            if((myMag_0[i_5]) != 0U)
            {

#line 999
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]]) == (tid_1 * 16U + i_5);

#line 999
            }
            else
            {

#line 999
                live_0 = false;

#line 999
            }

#line 999
            if(live_0)
            {

#line 1000
                uint o_1 = pair_0 * nbins_1 + myBin_0[i_5];
                *(peakIdx_0+o_1) = int(slotToIndex_0(tid_1 * 16U + i_5));

#line 1001
                *(peakVal_0+o_1) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 999
            }

#line 998
            i_5 = i_5 + 1U;

#line 998
        }

#line 998
        b_6 = tid_1;

#line 1005
        for(;;)
        {

#line 1005
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 1005
                break;
            }

#line 1006
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6]) == 4294967295U)
            {

#line 1007
                uint _S39 = pair_0 * nbins_1 + b_6;

#line 1007
                *(peakIdx_0+_S39) = int(-1);

#line 1007
                *(peakVal_0+_S39) = packed_float2(float2(0.0, 0.0)) ;

#line 1006
            }

#line 1005
            b_6 = b_6 + 8U;

#line 1005
        }

#line 956
    }

#line 1014
    return;
}


#line 1353
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1353
    thread KernelContext_0 kernelContext_5;

#line 1353
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1353
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1353
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1353
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1353
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1353
    threadgroup array<uint, int(256)> stg_1;

#line 1353
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1370
    uint _pr_0 = gid_0.x;

#line 1370
    uint _t_0 = lid_0.x;
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 1371
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);

#line 1379
    return;
}
