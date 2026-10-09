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


#line 152 "mm_2048_refineListed.slang"
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


#line 195 "mm_2048_refineListed.slang"
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
    array<uint, int(4096)> threadgroup* stg_0;
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
            stgPut_0(j_1 * 128U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

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
                float2 _S19 = stgGet_0((i_3 - _S17) * 128U + (b_4 << lgSpan_0) + ln_0, kernelContext_2);
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


#line 394
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_5;

#line 398
    uint s_0 = 1U;
    for(;;)
    {

#line 399
        if(s_0 < 8U)
        {
        }
        else
        {

#line 399
            break;
        }

#line 399
        uint j_2 = 0U;
        for(;;)
        {

#line 400
            if(j_2 < 4U)
            {
            }
            else
            {

#line 400
                break;
            }

#line 401
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S20 = o_0 + j_2;

#line 404
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0)), (*r_2)[_S20 + 4U]);
            uint _S21 = ((j_2 - k_0) << 1U) + k_0;

#line 405
            b_5[_S21] = (*r_2)[_S20] + t_6;

#line 405
            b_5[_S21 + s_0] = (*r_2)[_S20] - t_6;

#line 400
            j_2 = j_2 + 1U;

#line 400
        }

#line 400
        uint i_4 = 0U;

#line 407
        for(;;)
        {

#line 407
            if(i_4 < 8U)
            {
            }
            else
            {

#line 407
                break;
            }

#line 407
            (*r_2)[o_0 + i_4] = b_5[i_4];

#line 407
            i_4 = i_4 + 1U;

#line 407
        }

#line 399
        s_0 = s_0 << 1U;

#line 399
    }

#line 409
    return;
}


#line 513
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 513
    uint b_6 = 0U;

#line 521
    for(;;)
    {

#line 521
        if(b_6 < 2U)
        {
        }
        else
        {

#line 521
            break;
        }

#line 521
        dft8_0(r_3, b_6 * 8U);

#line 521
        b_6 = b_6 + 1U;

#line 521
    }



    return;
}


#line 654
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 654
    uint _S22;

#line 654
    uint k2_1;

#line 654
    float cr_0;

#line 654
    float ci_0;

#line 654
    uint _S23;

#line 654
    for(;;)
    {

#line 654
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(128U);

#line 11
                _S22 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(2048U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 127U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 2048.0);
                float _S24 = tw_0.x;

#line 27
                float _S25 = tw_0.y;

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
                    float nr_0 = cr_0 * _S24 - ci_0 * _S25;
                    float _S26 = cr_0 * _S25 + ci_0 * _S24;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S26;

#line 29
                }

#line 37
                uint per_2 = 16U / max(128U, 1U);
                uint _S27 = max(8U, 1U);

#line 38
                _S23 = _S27;
                uint blk2_2 = tid_0 / _S27;

#line 39
                uint lane2_2 = tid_0 % _S27;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 128U, 2048U, blk_2, lane_2, per_2, _S27, 128U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(8U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 7U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 128.0);
                float _S28 = tw_1.x;

#line 27
                float _S29 = tw_1.y;

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
                    float nr_1 = cr_0 * _S28 - ci_0 * _S29;
                    float _S30 = cr_0 * _S29 + ci_0 * _S28;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S30;

#line 29
                }

#line 37
                uint per_3 = 16U / _S23;
                uint _S31 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S31;

#line 39
                uint lane2_3 = tid_0 % _S31;

#line 39
                exchange_0(r_4, _S22, lgTB_1, 8U, 128U, blk_3, lane_3, per_3, _S31, 8U, blk2_3, lane2_3, kernelContext_3);

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

#line 657 "mm_2048_refineListed.slang"
    return;
}


#line 623
uint lgOf_0(uint i_5)
{

#line 623
    uint _S32;

#line 623
    if(i_5 < 2U)
    {

#line 623
        _S32 = 4U;

#line 623
    }
    else
    {

#line 623
        if(i_5 == 2U)
        {

#line 623
            _S32 = 3U;

#line 623
        }
        else
        {

#line 623
            _S32 = 1U;

#line 623
        }

#line 623
    }

#line 623
    return _S32;
}


#line 625
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 629
    uint lg_1 = lgOf_0(1U);

#line 629
    uint lg_2 = lgOf_0(0U);

#line 634
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 669
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 683
    kernelContext_4->_tid_0 = tid_1;
    uint _S33 = pair_0 / ntmpl_1;

#line 684
    uint _S34 = pair_0 % ntmpl_1;

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
        uint idx_0 = tid_1 + 128U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S33 * 2048U + idx_0), cload_0(tmpl_0, _S34 * 2048U + idx_0));

#line 697
        n2_0 = n2_0 + 1U;

#line 697
    }

#line 697
    transform_0(&r_5, tid_1, kernelContext_4);

#line 716
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 716
    uint b_7 = tid_1;

#line 790
    for(;;)
    {

#line 790
        if(b_7 < nbins_1)
        {
        }
        else
        {

#line 790
            break;
        }

#line 790
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_7] = thrBits_1;

#line 790
        b_7 = b_7 + 128U;

#line 790
    }
    bool _S35 = nbins_1 == 1U;

#line 791
    bool live_0;

#line 791
    if(_S35)
    {

#line 791
        live_0 = tid_1 == 0U;

#line 791
    }
    else
    {

#line 791
        live_0 = false;

#line 791
    }

#line 791
    if(live_0)
    {

#line 791
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 791
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 796
    uint i_6 = 0U;
    for(;;)
    {

#line 797
        if(i_6 < 16U)
        {
        }
        else
        {

#line 797
            break;
        }

#line 798
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_6);
        if(idx_1 >= winStart_1)
        {

#line 799
            live_0 = idx_1 < winEnd_1;

#line 799
        }
        else
        {

#line 799
            live_0 = false;

#line 799
        }



        float _rx_0 = r_5[i_6].x;

#line 803
        float _ry_0 = r_5[i_6].y;
        if(live_0)
        {

#line 804
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 804
        }
        else
        {

#line 804
            n2_0 = 0U;

#line 804
        }

#line 804
        myMag_0[i_6] = n2_0;
        uint off_0 = idx_1 - winStart_1;

#line 812
        if(live_0)
        {

#line 812
            if(binShift_1 >= int(0))
            {

#line 812
                b_7 = off_0 >> uint(binShift_1);

#line 812
            }
            else
            {

#line 812
                uint _S36 = off_0 / binsize_1;

#line 812
                b_7 = _S36;

#line 812
            }

#line 812
        }
        else
        {

#line 812
            b_7 = 0U;

#line 812
        }

#line 812
        myBin_0[i_6] = b_7;

#line 812
        bool _S37;



        if(nbins_1 > 1U)
        {

#line 816
            _S37 = (myMag_0[i_6]) > thrBits_1;

#line 816
        }
        else
        {

#line 816
            _S37 = false;

#line 816
        }

#line 816
        if(_S37)
        {

#line 817
            uint _S38 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_6]])), myMag_0[i_6], memory_order_relaxed);

#line 816
        }

#line 797
        i_6 = i_6 + 1U;

#line 797
    }

#line 797
    uint winner_0;

#line 829
    if(_S35)
    {

#line 829
        winner_0 = thrBits_1;

#line 829
        i_6 = 0U;


        for(;;)
        {

#line 832
            if(i_6 < 16U)
            {
            }
            else
            {

#line 832
                break;
            }

#line 832
            uint _S39 = max(winner_0, myMag_0[i_6]);

#line 832
            uint i_7 = i_6 + 1U;

#line 832
            winner_0 = _S39;

#line 832
            i_6 = i_7;

#line 832
        }

        uint wm_0 = simd_max(winner_0);
        bool _S40 = simd_is_first();

#line 835
        if(_S40)
        {

#line 835
            live_0 = wm_0 > thrBits_1;

#line 835
        }
        else
        {

#line 835
            live_0 = false;

#line 835
        }

#line 835
        if(live_0)
        {

#line 835
            uint _S41 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 835
        }

#line 829
    }

#line 850
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 857
    if(_S35)
    {

#line 857
        winner_0 = 4294967295U;

#line 857
        i_6 = 0U;


        for(;;)
        {

#line 860
            if(i_6 < 16U)
            {
            }
            else
            {

#line 860
                break;
            }

#line 861
            if((myMag_0[i_6]) > thrBits_1)
            {

#line 861
                live_0 = (myMag_0[i_6]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

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
                winner_0 = min(winner_0, tid_1 * 16U + i_6);

#line 861
            }

#line 860
            i_6 = i_6 + 1U;

#line 860
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S42 = simd_is_first();

#line 865
        if(_S42)
        {

#line 865
            live_0 = waveWinner_0 != 4294967295U;

#line 865
        }
        else
        {

#line 865
            live_0 = false;

#line 865
        }

#line 865
        if(live_0)
        {

#line 866
            uint _S43 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 865
        }

#line 870
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 870
        i_6 = 0U;
        for(;;)
        {

#line 871
            if(i_6 < 16U)
            {
            }
            else
            {

#line 871
                break;
            }

#line 872
            uint _S44 = tid_1 * 16U + i_6;

#line 872
            if(_S44 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 873
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S44));

#line 873
                *(peakVal_0+pair_0) = packed_float2(float2(r_5[i_6].x, r_5[i_6].y)) ;

#line 872
            }

#line 871
            i_6 = i_6 + 1U;

#line 871
        }

#line 877
        if(tid_1 == 0U)
        {

#line 877
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

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
            *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 877
        }

#line 857
    }
    else
    {

#line 857
        i_6 = 0U;

#line 886
        for(;;)
        {

#line 886
            if(i_6 < 16U)
            {
            }
            else
            {

#line 886
                break;
            }

#line 887
            if((myMag_0[i_6]) > thrBits_1)
            {

#line 887
                live_0 = (myMag_0[i_6]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_6]];

#line 887
            }
            else
            {

#line 887
                live_0 = false;

#line 887
            }

#line 887
            myMag_0[i_6] = uint(live_0);

#line 886
            i_6 = i_6 + 1U;

#line 886
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 889
        b_7 = tid_1;
        for(;;)
        {

#line 890
            if(b_7 < nbins_1)
            {
            }
            else
            {

#line 890
                break;
            }

#line 890
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_7] = 4294967295U;

#line 890
            b_7 = b_7 + 128U;

#line 890
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 891
        i_6 = 0U;
        for(;;)
        {

#line 892
            if(i_6 < 16U)
            {
            }
            else
            {

#line 892
                break;
            }

#line 893
            if((myMag_0[i_6]) != 0U)
            {

#line 893
                uint _S45 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_6]])), tid_1 * 16U + i_6, memory_order_relaxed);

#line 893
            }

#line 892
            i_6 = i_6 + 1U;

#line 892
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 894
        i_6 = 0U;
        for(;;)
        {

#line 895
            if(i_6 < 16U)
            {
            }
            else
            {

#line 895
                break;
            }

#line 896
            if((myMag_0[i_6]) != 0U)
            {

#line 896
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_6]]) == (tid_1 * 16U + i_6);

#line 896
            }
            else
            {

#line 896
                live_0 = false;

#line 896
            }

#line 896
            if(live_0)
            {

#line 897
                uint o_1 = pair_0 * nbins_1 + myBin_0[i_6];
                *(peakIdx_0+o_1) = int(slotToIndex_0(tid_1 * 16U + i_6));

#line 898
                *(peakVal_0+o_1) = packed_float2(float2(r_5[i_6].x, r_5[i_6].y)) ;

#line 896
            }

#line 895
            i_6 = i_6 + 1U;

#line 895
        }

#line 895
        b_7 = tid_1;

#line 902
        for(;;)
        {

#line 902
            if(b_7 < nbins_1)
            {
            }
            else
            {

#line 902
                break;
            }

#line 903
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_7]) == 4294967295U)
            {

#line 904
                uint _S46 = pair_0 * nbins_1 + b_7;

#line 904
                *(peakIdx_0+_S46) = int(-1);

#line 904
                *(peakVal_0+_S46) = packed_float2(float2(0.0, 0.0)) ;

#line 903
            }

#line 902
            b_7 = b_7 + 128U;

#line 902
        }

#line 857
    }

#line 911
    return;
}


#line 1329
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1329
    thread KernelContext_0 kernelContext_5;

#line 1329
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1329
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1329
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1329
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1329
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1329
    (&kernelContext_5)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1329
    threadgroup array<uint, int(4096)> stg_1;

#line 1329
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1338
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1344
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 1344
    filterPair_0(pair_1, lid_0.x, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);


    return;
}
