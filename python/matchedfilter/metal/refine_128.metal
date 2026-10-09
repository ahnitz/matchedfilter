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


#line 152 "mm_128_refineListed.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 152
    return float2(*(b_0+i_0)) ;
}


#line 226
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 226
    float _S2 = a_0.x;

#line 226
    float _S3 = b_1.x;

#line 226
    float _S4 = a_0.y;

#line 226
    float _S5 = b_1.y;

#line 226
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 393
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 395
    float2 t1_0 = *a_1 - *c_0;

#line 395
    float2 t2_0 = *b_2 + *d_0;

#line 395
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 397
    *b_2 = t1_0 + j3_0;

#line 397
    *c_0 = t0_0 - t2_0;

#line 397
    *d_0 = t1_0 - j3_0;
    return;
}


#line 225
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 225
    float _S6 = a_2.x;

#line 225
    float _S7 = b_3.x;

#line 225
    float _S8 = a_2.y;

#line 225
    float _S9 = b_3.y;

#line 225
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 429
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 436
    uint n1_0 = 0U;
    for(;;)
    {

#line 437
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 437
            break;
        }

#line 437
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 437
        n1_0 = n1_0 + 1U;

#line 437
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 438
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 438
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 439
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 439
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 440
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 440
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 440
    uint k2_0 = 0U;
    for(;;)
    {

#line 441
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 441
            break;
        }

#line 441
        uint _S10 = 4U * k2_0;

#line 441
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 441
        k2_0 = k2_0 + 1U;

#line 441
    }

    float2 t_0 = (*r_0)[int(1)];

#line 443
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 443
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 444
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 444
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 445
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 445
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 446
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 446
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 447
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 447
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 448
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 448
    (*r_0)[int(14)] = t_5;
    return;
}


#line 17 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 227 "mm_128_refineListed.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 229
    uint j_0 = d_1 / _S11;

#line 229
    uint m_0 = d_1 % _S11;

#line 229
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 230
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 230
    }
    else
    {

#line 230
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 230
    }

#line 230
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


#line 214 "mm_128_refineListed.slang"
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
    array<uint, int(256)> threadgroup* stg_0;
};


#line 214
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 214
    uint _S13 = 2U * i_1;

#line 214
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13] = (as_type<uint>((v_0.x)));

#line 214
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13 + 1U] = (as_type<uint>((v_0.y)));

#line 214
    return;
}


#line 215
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 215
    uint _S14 = 2U * i_2;

#line 215
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 589
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 590
    uint j_1;

#line 601
    thread array<float2, int(16)> out_0;

#line 601
    uint z_0 = 0U;
    for(;;)
    {

#line 602
        if(z_0 < 16U)
        {
        }
        else
        {

#line 602
            break;
        }

#line 602
        out_0[z_0] = float2(0.0, 0.0);

#line 602
        z_0 = z_0 + 1U;

#line 602
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S15 = p0_0 & lenMask_0;

#line 608
    uint _S16 = (_S15 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 608
    uint c_1 = 0U;

    for(;;)
    {

#line 610
        if(c_1 < 1U)
        {
        }
        else
        {

#line 610
            break;
        }

#line 611
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 611
        j_1 = 0U;
        for(;;)
        {

#line 612
            if(j_1 < 16U)
            {
            }
            else
            {

#line 612
                break;
            }

#line 612
            stgPut_0(j_1 * 8U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 612
            j_1 = j_1 + 1U;

#line 612
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 613
        uint d_2 = 0U;
        for(;;)
        {

#line 614
            if(d_2 < 16U)
            {
            }
            else
            {

#line 614
                break;
            }

#line 615
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S17 = pz_0 & lenMask_0;
            uint az_0 = (_S17 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S17 & spanMask_0);

#line 617
            float2 _S18 = stgGet_0(_S16 + az_0 - c_1 * 16U * 8U, kernelContext_2);


            out_0[d_2] = _S18;

#line 614
            d_2 = d_2 + 1U;

#line 614
        }

#line 610
        c_1 = c_1 + 1U;

#line 610
    }

#line 610
    j_1 = 0U;

#line 623
    for(;;)
    {

#line 623
        if(j_1 < 16U)
        {
        }
        else
        {

#line 623
            break;
        }

#line 623
        (*r_1)[j_1] = out_0[j_1];

#line 623
        j_1 = j_1 + 1U;

#line 623
    }
    return;
}


#line 413
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_4;

#line 417
    uint s_0 = 1U;
    for(;;)
    {

#line 418
        if(s_0 < 8U)
        {
        }
        else
        {

#line 418
            break;
        }

#line 418
        uint j_2 = 0U;
        for(;;)
        {

#line 419
            if(j_2 < 4U)
            {
            }
            else
            {

#line 419
                break;
            }

#line 420
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S19 = o_0 + j_2;

#line 423
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0)), (*r_2)[_S19 + 4U]);
            uint _S20 = ((j_2 - k_0) << 1U) + k_0;

#line 424
            b_4[_S20] = (*r_2)[_S19] + t_6;

#line 424
            b_4[_S20 + s_0] = (*r_2)[_S19] - t_6;

#line 419
            j_2 = j_2 + 1U;

#line 419
        }

#line 419
        uint i_3 = 0U;

#line 426
        for(;;)
        {

#line 426
            if(i_3 < 8U)
            {
            }
            else
            {

#line 426
                break;
            }

#line 426
            (*r_2)[o_0 + i_3] = b_4[i_3];

#line 426
            i_3 = i_3 + 1U;

#line 426
        }

#line 418
        s_0 = s_0 << 1U;

#line 418
    }

#line 428
    return;
}


#line 532
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 532
    uint b_5 = 0U;

#line 540
    for(;;)
    {

#line 540
        if(b_5 < 2U)
        {
        }
        else
        {

#line 540
            break;
        }

#line 540
        dft8_0(r_3, b_5 * 8U);

#line 540
        b_5 = b_5 + 1U;

#line 540
    }



    return;
}


#line 679
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 679
    for(;;)
    {

#line 679
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

#line 682 "mm_128_refineListed.slang"
    return;
}


#line 648
uint lgOf_0(uint i_4)
{

#line 648
    uint _S25;

#line 648
    if(i_4 < 1U)
    {

#line 648
        _S25 = 4U;

#line 648
    }
    else
    {

#line 648
        if(i_4 == 1U)
        {

#line 648
            _S25 = 3U;

#line 648
        }
        else
        {

#line 648
            _S25 = 1U;

#line 648
        }

#line 648
    }

#line 648
    return _S25;
}


#line 650
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 654
    uint lg_1 = lgOf_0(0U);

#line 659
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 694
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 708
    kernelContext_4->_tid_0 = tid_1;
    uint _S26 = pair_0 / ntmpl_1;

#line 709
    uint _S27 = pair_0 % ntmpl_1;

    thread array<float2, int(16)> r_5;

#line 711
    uint n2_0 = 0U;

#line 722
    for(;;)
    {

#line 722
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 722
            break;
        }

#line 723
        uint idx_0 = tid_1 + 8U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S26 * 128U + idx_0), cload_0(tmpl_0, _S27 * 128U + idx_0));

#line 722
        n2_0 = n2_0 + 1U;

#line 722
    }

#line 722
    transform_0(&r_5, tid_1, kernelContext_4);

#line 741
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 741
    uint b_6 = tid_1;

#line 815
    for(;;)
    {

#line 815
        if(b_6 < nbins_1)
        {
        }
        else
        {

#line 815
            break;
        }

#line 815
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6] = thrBits_1;

#line 815
        b_6 = b_6 + 8U;

#line 815
    }
    bool _S28 = nbins_1 == 1U;

#line 816
    bool live_0;

#line 816
    if(_S28)
    {

#line 816
        live_0 = tid_1 == 0U;

#line 816
    }
    else
    {

#line 816
        live_0 = false;

#line 816
    }

#line 816
    if(live_0)
    {

#line 816
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 816
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 821
    uint i_5 = 0U;
    for(;;)
    {

#line 822
        if(i_5 < 16U)
        {
        }
        else
        {

#line 822
            break;
        }

#line 823
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_5);
        if(idx_1 >= winStart_1)
        {

#line 824
            live_0 = idx_1 < winEnd_1;

#line 824
        }
        else
        {

#line 824
            live_0 = false;

#line 824
        }



        float _rx_0 = r_5[i_5].x;

#line 828
        float _ry_0 = r_5[i_5].y;
        if(live_0)
        {

#line 829
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 829
        }
        else
        {

#line 829
            n2_0 = 0U;

#line 829
        }

#line 829
        myMag_0[i_5] = n2_0;
        uint off_0 = idx_1 - winStart_1;

#line 837
        if(live_0)
        {

#line 837
            if(binShift_1 >= int(0))
            {

#line 837
                b_6 = off_0 >> uint(binShift_1);

#line 837
            }
            else
            {

#line 837
                uint _S29 = off_0 / binsize_1;

#line 837
                b_6 = _S29;

#line 837
            }

#line 837
        }
        else
        {

#line 837
            b_6 = 0U;

#line 837
        }

#line 837
        myBin_0[i_5] = b_6;

#line 837
        bool _S30;



        if(nbins_1 > 1U)
        {

#line 841
            _S30 = (myMag_0[i_5]) > thrBits_1;

#line 841
        }
        else
        {

#line 841
            _S30 = false;

#line 841
        }

#line 841
        if(_S30)
        {

#line 842
            uint _S31 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), myMag_0[i_5], memory_order_relaxed);

#line 841
        }

#line 822
        i_5 = i_5 + 1U;

#line 822
    }

#line 822
    uint winner_0;

#line 854
    if(_S28)
    {

#line 854
        winner_0 = thrBits_1;

#line 854
        i_5 = 0U;


        for(;;)
        {

#line 857
            if(i_5 < 16U)
            {
            }
            else
            {

#line 857
                break;
            }

#line 857
            uint _S32 = max(winner_0, myMag_0[i_5]);

#line 857
            uint i_6 = i_5 + 1U;

#line 857
            winner_0 = _S32;

#line 857
            i_5 = i_6;

#line 857
        }

        uint wm_0 = simd_max(winner_0);
        bool _S33 = simd_is_first();

#line 860
        if(_S33)
        {

#line 860
            live_0 = wm_0 > thrBits_1;

#line 860
        }
        else
        {

#line 860
            live_0 = false;

#line 860
        }

#line 860
        if(live_0)
        {

#line 860
            uint _S34 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 860
        }

#line 854
    }

#line 875
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 882
    if(_S28)
    {

#line 882
        winner_0 = 4294967295U;

#line 882
        i_5 = 0U;


        for(;;)
        {

#line 885
            if(i_5 < 16U)
            {
            }
            else
            {

#line 885
                break;
            }

#line 886
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 886
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 886
            }
            else
            {

#line 886
                live_0 = false;

#line 886
            }

#line 886
            if(live_0)
            {

#line 886
                winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 886
            }

#line 885
            i_5 = i_5 + 1U;

#line 885
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S35 = simd_is_first();

#line 890
        if(_S35)
        {

#line 890
            live_0 = waveWinner_0 != 4294967295U;

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

#line 891
            uint _S36 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 890
        }

#line 895
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 895
        i_5 = 0U;
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
            uint _S37 = tid_1 * 16U + i_5;

#line 897
            if(_S37 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 898
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S37));

#line 898
                *(peakVal_0+pair_0) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 897
            }

#line 896
            i_5 = i_5 + 1U;

#line 896
        }

#line 902
        if(tid_1 == 0U)
        {

#line 902
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 902
        }
        else
        {

#line 902
            live_0 = false;

#line 902
        }

#line 902
        if(live_0)
        {

#line 903
            *(peakIdx_0+pair_0) = int(-1);

#line 903
            *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 902
        }

#line 882
    }
    else
    {

#line 882
        i_5 = 0U;

#line 911
        for(;;)
        {

#line 911
            if(i_5 < 16U)
            {
            }
            else
            {

#line 911
                break;
            }

#line 912
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 912
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]];

#line 912
            }
            else
            {

#line 912
                live_0 = false;

#line 912
            }

#line 912
            myMag_0[i_5] = uint(live_0);

#line 911
            i_5 = i_5 + 1U;

#line 911
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 914
        b_6 = tid_1;
        for(;;)
        {

#line 915
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 915
                break;
            }

#line 915
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6] = 4294967295U;

#line 915
            b_6 = b_6 + 8U;

#line 915
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 916
        i_5 = 0U;
        for(;;)
        {

#line 917
            if(i_5 < 16U)
            {
            }
            else
            {

#line 917
                break;
            }

#line 918
            if((myMag_0[i_5]) != 0U)
            {

#line 918
                uint _S38 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), tid_1 * 16U + i_5, memory_order_relaxed);

#line 918
            }

#line 917
            i_5 = i_5 + 1U;

#line 917
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 919
        i_5 = 0U;
        for(;;)
        {

#line 920
            if(i_5 < 16U)
            {
            }
            else
            {

#line 920
                break;
            }

#line 921
            if((myMag_0[i_5]) != 0U)
            {

#line 921
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]]) == (tid_1 * 16U + i_5);

#line 921
            }
            else
            {

#line 921
                live_0 = false;

#line 921
            }

#line 921
            if(live_0)
            {

#line 922
                uint o_1 = pair_0 * nbins_1 + myBin_0[i_5];
                *(peakIdx_0+o_1) = int(slotToIndex_0(tid_1 * 16U + i_5));

#line 923
                *(peakVal_0+o_1) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 921
            }

#line 920
            i_5 = i_5 + 1U;

#line 920
        }

#line 920
        b_6 = tid_1;

#line 927
        for(;;)
        {

#line 927
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 927
                break;
            }

#line 928
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6]) == 4294967295U)
            {

#line 929
                uint _S39 = pair_0 * nbins_1 + b_6;

#line 929
                *(peakIdx_0+_S39) = int(-1);

#line 929
                *(peakVal_0+_S39) = packed_float2(float2(0.0, 0.0)) ;

#line 928
            }

#line 927
            b_6 = b_6 + 8U;

#line 927
        }

#line 882
    }

#line 936
    return;
}


#line 1384
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1384
    thread KernelContext_0 kernelContext_5;

#line 1384
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1384
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1384
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1384
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1384
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1384
    (&kernelContext_5)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1384
    threadgroup array<uint, int(256)> stg_1;

#line 1384
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1393
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1399
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 1399
    filterPair_0(pair_1, lid_0.x, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);


    return;
}
