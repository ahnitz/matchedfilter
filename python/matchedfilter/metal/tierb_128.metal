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


#line 168 "mm_128_fusedTierB.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 168
    return float2(*(b_0+i_0)) ;
}


#line 286
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 286
    float _S2 = a_0.x;

#line 286
    float _S3 = b_1.x;

#line 286
    float _S4 = a_0.y;

#line 286
    float _S5 = b_1.y;

#line 286
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 491
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 493
    float2 t1_0 = *a_1 - *c_0;

#line 493
    float2 t2_0 = *b_2 + *d_0;

#line 493
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 495
    *b_2 = t1_0 + j3_0;

#line 495
    *c_0 = t0_0 - t2_0;

#line 495
    *d_0 = t1_0 - j3_0;
    return;
}


#line 285
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 285
    float _S6 = a_2.x;

#line 285
    float _S7 = b_3.x;

#line 285
    float _S8 = a_2.y;

#line 285
    float _S9 = b_3.y;

#line 285
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 527
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 534
    uint n1_0 = 0U;
    for(;;)
    {

#line 535
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 535
            break;
        }

#line 535
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 535
        n1_0 = n1_0 + 1U;

#line 535
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 536
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 536
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 537
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 537
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 538
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 538
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 538
    uint k2_0 = 0U;
    for(;;)
    {

#line 539
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 539
            break;
        }

#line 539
        uint _S10 = 4U * k2_0;

#line 539
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 539
        k2_0 = k2_0 + 1U;

#line 539
    }

    float2 t_0 = (*r_0)[int(1)];

#line 541
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 541
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 542
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 542
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 543
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 543
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 544
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 544
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 545
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 545
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 546
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 546
    (*r_0)[int(14)] = t_5;
    return;
}


#line 84 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 287 "mm_128_fusedTierB.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 289
    uint j_0 = d_1 / _S11;

#line 289
    uint m_0 = d_1 % _S11;

#line 289
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 290
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 290
    }
    else
    {

#line 290
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 290
    }

#line 290
    return _S12;
}


#line 8599 "hlsl.meta.slang"
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


#line 274 "mm_128_fusedTierB.slang"
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


#line 274
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 274
    uint _S13 = 2U * i_1;

#line 274
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13] = (as_type<uint>((v_0.x)));

#line 274
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13 + 1U] = (as_type<uint>((v_0.y)));

#line 274
    return;
}


#line 275
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 275
    uint _S14 = 2U * i_2;

#line 275
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 716
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 717
    uint j_1;

#line 728
    thread array<float2, int(16)> out_0;

#line 728
    uint z_0 = 0U;
    for(;;)
    {

#line 729
        if(z_0 < 16U)
        {
        }
        else
        {

#line 729
            break;
        }

#line 729
        out_0[z_0] = float2(0.0f, 0.0f);

#line 729
        z_0 = z_0 + 1U;

#line 729
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S15 = p0_0 & lenMask_0;

#line 735
    uint _S16 = (_S15 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 735
    uint c_1 = 0U;

    for(;;)
    {

#line 737
        if(c_1 < 1U)
        {
        }
        else
        {

#line 737
            break;
        }

#line 738
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 738
        j_1 = 0U;
        for(;;)
        {

#line 739
            if(j_1 < 16U)
            {
            }
            else
            {

#line 739
                break;
            }

#line 739
            stgPut_0(j_1 * 8U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 739
            j_1 = j_1 + 1U;

#line 739
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 740
        uint d_2 = 0U;
        for(;;)
        {

#line 741
            if(d_2 < 16U)
            {
            }
            else
            {

#line 741
                break;
            }

#line 742
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S17 = pz_0 & lenMask_0;
            uint az_0 = (_S17 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S17 & spanMask_0);

#line 744
            float2 _S18 = stgGet_0(_S16 + az_0 - c_1 * 16U * 8U, kernelContext_2);


            out_0[d_2] = _S18;

#line 741
            d_2 = d_2 + 1U;

#line 741
        }

#line 737
        c_1 = c_1 + 1U;

#line 737
    }

#line 737
    j_1 = 0U;

#line 750
    for(;;)
    {

#line 750
        if(j_1 < 16U)
        {
        }
        else
        {

#line 750
            break;
        }

#line 750
        (*r_1)[j_1] = out_0[j_1];

#line 750
        j_1 = j_1 + 1U;

#line 750
    }
    return;
}


#line 511
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_4;

#line 515
    uint s_0 = 1U;
    for(;;)
    {

#line 516
        if(s_0 < 8U)
        {
        }
        else
        {

#line 516
            break;
        }

#line 516
        uint j_2 = 0U;
        for(;;)
        {

#line 517
            if(j_2 < 4U)
            {
            }
            else
            {

#line 517
                break;
            }

#line 518
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S19 = o_0 + j_2;

#line 521
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_0)), (*r_2)[_S19 + 4U]);
            uint _S20 = ((j_2 - k_0) << 1U) + k_0;

#line 522
            b_4[_S20] = (*r_2)[_S19] + t_6;

#line 522
            b_4[_S20 + s_0] = (*r_2)[_S19] - t_6;

#line 517
            j_2 = j_2 + 1U;

#line 517
        }

#line 517
        uint i_3 = 0U;

#line 524
        for(;;)
        {

#line 524
            if(i_3 < 8U)
            {
            }
            else
            {

#line 524
                break;
            }

#line 524
            (*r_2)[o_0 + i_3] = b_4[i_3];

#line 524
            i_3 = i_3 + 1U;

#line 524
        }

#line 516
        s_0 = s_0 << 1U;

#line 516
    }

#line 526
    return;
}


#line 630
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 630
    uint b_5 = 0U;

#line 638
    for(;;)
    {

#line 638
        if(b_5 < 2U)
        {
        }
        else
        {

#line 638
            break;
        }

#line 638
        dft8_0(r_3, b_5 * 8U);

#line 638
        b_5 = b_5 + 1U;

#line 638
    }



    return;
}


#line 818
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 818
    for(;;)
    {

#line 818
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

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 128.0f);
                float _S21 = tw_0.x;

#line 40
                float _S22 = tw_0.y;

#line 40
                uint k2_1 = 0U;

#line 40
                float cr_0 = 1.0f;

#line 40
                float ci_0 = 0.0f;

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
                    float nr_0 = cr_0 * _S21 - ci_0 * _S22;
                    float _S23 = cr_0 * _S22 + ci_0 * _S21;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S23;

#line 42
                }

#line 50
                uint per_2 = 16U / max(8U, 1U);
                uint _S24 = max(0U, 1U);
                uint blk2_2 = tid_0 / _S24;

#line 52
                uint lane2_2 = tid_0 % _S24;

#line 52
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

#line 56
    innermost_0(r_4);

#line 821 "mm_128_fusedTierB.slang"
    return;
}


#line 775
uint lgOf_0(uint i_4)
{

#line 775
    uint _S25;

#line 775
    if(i_4 < 1U)
    {

#line 775
        _S25 = 4U;

#line 775
    }
    else
    {

#line 775
        if(i_4 == 1U)
        {

#line 775
            _S25 = 3U;

#line 775
        }
        else
        {

#line 775
            _S25 = 1U;

#line 775
        }

#line 775
    }

#line 775
    return _S25;
}


#line 777
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 781
    uint lg_1 = lgOf_0(0U);

#line 786
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 841
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 861
    kernelContext_4->_tid_0 = tid_1;
    uint _S26 = pair_0 / ntmpl_1;

#line 862
    uint _S27 = pair_0 % ntmpl_1;

#line 867
    thread array<float2, int(16)> r_5;

#line 867
    uint n2_0 = 0U;

#line 878
    for(;;)
    {

#line 878
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 878
            break;
        }

#line 879
        uint idx_0 = tid_1 + 8U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S26 * 128U + idx_0), cload_0(tmpl_0, _S27 * 128U + idx_0));

#line 878
        n2_0 = n2_0 + 1U;

#line 878
    }

#line 878
    transform_0(&r_5, tid_1, kernelContext_4);

#line 907
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 907
    uint b_6 = tid_1;

#line 1019
    for(;;)
    {

#line 1019
        if(b_6 < nbins_1)
        {
        }
        else
        {

#line 1019
            break;
        }

#line 1019
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6] = thrBits_1;

#line 1019
        b_6 = b_6 + 8U;

#line 1019
    }
    bool _S28 = nbins_1 == 1U;

#line 1020
    bool live_0;

#line 1020
    if(_S28)
    {

#line 1020
        live_0 = tid_1 == 0U;

#line 1020
    }
    else
    {

#line 1020
        live_0 = false;

#line 1020
    }

#line 1020
    if(live_0)
    {

#line 1020
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 1020
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1079
    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 1080
    uint i_5 = 0U;



    for(;;)
    {

#line 1084
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1084
            break;
        }

#line 1085
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_5);
        if(idx_1 >= winStart_1)
        {

#line 1086
            live_0 = idx_1 < winEnd_1;

#line 1086
        }
        else
        {

#line 1086
            live_0 = false;

#line 1086
        }



        float _rx_0 = r_5[i_5].x;

#line 1090
        float _ry_0 = r_5[i_5].y;
        if(live_0)
        {

#line 1091
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1091
        }
        else
        {

#line 1091
            n2_0 = 0U;

#line 1091
        }

#line 1091
        myMag_0[i_5] = n2_0;

#line 1099
        uint off_0 = idx_1 - winStart_1;

#line 1106
        if(live_0)
        {

#line 1106
            if(binShift_1 >= int(0))
            {

#line 1106
                b_6 = off_0 >> uint(binShift_1);

#line 1106
            }
            else
            {

#line 1106
                uint _S29 = off_0 / binsize_1;

#line 1106
                b_6 = _S29;

#line 1106
            }

#line 1106
        }
        else
        {

#line 1106
            b_6 = 0U;

#line 1106
        }

#line 1106
        myBin_0[i_5] = b_6;

#line 1106
        bool _S30;



        if(nbins_1 > 1U)
        {

#line 1110
            _S30 = (myMag_0[i_5]) > thrBits_1;

#line 1110
        }
        else
        {

#line 1110
            _S30 = false;

#line 1110
        }

#line 1110
        if(_S30)
        {

#line 1111
            uint _S31 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), myMag_0[i_5], memory_order_relaxed);

#line 1110
        }

#line 1084
        i_5 = i_5 + 1U;

#line 1084
    }

#line 1084
    uint winner_0;

#line 1134
    if(_S28)
    {

#line 1134
        winner_0 = thrBits_1;

#line 1134
        i_5 = 0U;


        for(;;)
        {

#line 1137
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1137
                break;
            }

#line 1137
            uint _S32 = max(winner_0, myMag_0[i_5]);

#line 1137
            uint i_6 = i_5 + 1U;

#line 1137
            winner_0 = _S32;

#line 1137
            i_5 = i_6;

#line 1137
        }

        uint wm_0 = simd_max(winner_0);
        bool _S33 = simd_is_first();

#line 1140
        if(_S33)
        {

#line 1140
            live_0 = wm_0 > thrBits_1;

#line 1140
        }
        else
        {

#line 1140
            live_0 = false;

#line 1140
        }

#line 1140
        if(live_0)
        {

#line 1140
            uint _S34 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1140
        }

#line 1134
    }

#line 1155
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1162
    if(_S28)
    {

#line 1162
        winner_0 = 4294967295U;

#line 1162
        i_5 = 0U;


        for(;;)
        {

#line 1165
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1165
                break;
            }

#line 1166
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1166
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 1166
            }
            else
            {

#line 1166
                live_0 = false;

#line 1166
            }

#line 1166
            if(live_0)
            {

#line 1166
                winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 1166
            }

#line 1165
            i_5 = i_5 + 1U;

#line 1165
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S35 = simd_is_first();

#line 1170
        if(_S35)
        {

#line 1170
            live_0 = waveWinner_0 != 4294967295U;

#line 1170
        }
        else
        {

#line 1170
            live_0 = false;

#line 1170
        }

#line 1170
        if(live_0)
        {

#line 1171
            uint _S36 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1170
        }

#line 1175
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1175
        i_5 = 0U;
        for(;;)
        {

#line 1176
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1176
                break;
            }

#line 1177
            uint _S37 = tid_1 * 16U + i_5;

#line 1177
            if(_S37 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 1178
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S37));

#line 1178
                *(peakVal_0+pair_0) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 1177
            }

#line 1176
            i_5 = i_5 + 1U;

#line 1176
        }

#line 1186
        if(tid_1 == 0U)
        {

#line 1186
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1186
        }
        else
        {

#line 1186
            live_0 = false;

#line 1186
        }

#line 1186
        if(live_0)
        {

#line 1187
            *(peakIdx_0+pair_0) = int(-1);

#line 1187
            *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1186
        }

#line 1162
    }
    else
    {

#line 1162
        i_5 = 0U;

#line 1195
        for(;;)
        {

#line 1195
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1195
                break;
            }

#line 1196
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1196
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]];

#line 1196
            }
            else
            {

#line 1196
                live_0 = false;

#line 1196
            }

#line 1196
            myMag_0[i_5] = uint(live_0);

#line 1195
            i_5 = i_5 + 1U;

#line 1195
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1198
        b_6 = tid_1;
        for(;;)
        {

#line 1199
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 1199
                break;
            }

#line 1199
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6] = 4294967295U;

#line 1199
            b_6 = b_6 + 8U;

#line 1199
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1200
        i_5 = 0U;
        for(;;)
        {

#line 1201
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1201
                break;
            }

#line 1202
            if((myMag_0[i_5]) != 0U)
            {

#line 1202
                uint _S38 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), tid_1 * 16U + i_5, memory_order_relaxed);

#line 1202
            }

#line 1201
            i_5 = i_5 + 1U;

#line 1201
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1203
        i_5 = 0U;
        for(;;)
        {

#line 1204
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1204
                break;
            }

#line 1205
            if((myMag_0[i_5]) != 0U)
            {

#line 1205
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]]) == (tid_1 * 16U + i_5);

#line 1205
            }
            else
            {

#line 1205
                live_0 = false;

#line 1205
            }

#line 1205
            if(live_0)
            {

#line 1206
                uint o_1 = pair_0 * nbins_1 + myBin_0[i_5];
                *(peakIdx_0+o_1) = int(slotToIndex_0(tid_1 * 16U + i_5));

#line 1207
                *(peakVal_0+o_1) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 1205
            }

#line 1204
            i_5 = i_5 + 1U;

#line 1204
        }

#line 1204
        b_6 = tid_1;

#line 1211
        for(;;)
        {

#line 1211
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 1211
                break;
            }

#line 1212
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6]) == 4294967295U)
            {

#line 1213
                uint _S39 = pair_0 * nbins_1 + b_6;

#line 1213
                *(peakIdx_0+_S39) = int(-1);

#line 1213
                *(peakVal_0+_S39) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1212
            }

#line 1211
            b_6 = b_6 + 8U;

#line 1211
        }

#line 1162
    }

#line 1221
    return;
}


#line 1712
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1712
    thread KernelContext_0 kernelContext_5;

#line 1712
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1712
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1712
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1712
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1712
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1712
    threadgroup array<uint, int(256)> stg_1;

#line 1712
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1729
    uint _pr_0 = gid_0.x;

#line 1729
    uint _t_0 = lid_0.x;
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 1730
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);

#line 1745
    return;
}
