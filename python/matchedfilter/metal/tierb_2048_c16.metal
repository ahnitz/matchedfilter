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


#line 147 "mm_2048_fusedTierB_c16.slang"
half2 cload_0(uint device* b_0, uint i_0)
{

#line 148
    uint p_0 = b_0[i_0];

#line 148
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 191
half2 cmulConj_0(half2 a_0, half2 b_1)
{

#line 191
    half _S2 = a_0.x;

#line 191
    half _S3 = b_1.x;

#line 191
    half _S4 = a_0.y;

#line 191
    half _S5 = b_1.y;

#line 191
    return half2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 348
void r4_0(half2 thread* a_1, half2 thread* b_2, half2 thread* c_0, half2 thread* d_0)
{
    half2 t0_0 = *a_1 + *c_0;

#line 350
    half2 t1_0 = *a_1 - *c_0;

#line 350
    half2 t2_0 = *b_2 + *d_0;

#line 350
    half2 t3_0 = *b_2 - *d_0;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
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
half2 cmul_0(half2 a_2, half2 b_3)
{

#line 190
    half _S6 = a_2.x;

#line 190
    half _S7 = b_3.x;

#line 190
    half _S8 = a_2.y;

#line 190
    half _S9 = b_3.y;

#line 190
    return half2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 384
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125, 0.382568359375);
    half2 W2_0 = half2(0.70703125, 0.70703125);
    half2 W3_0 = half2(0.382568359375, 0.923828125);
    half2 W4_0 = half2(0.0, 1.0);
    half2 W6_0 = half2(-0.70703125, 0.70703125);
    half2 W9_0 = half2(-0.923828125, -0.382568359375);

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

    half2 t_0 = (*r_0)[int(1)];

#line 398
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 398
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 399
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 399
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 400
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 400
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 401
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 401
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 402
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 402
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 403
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 403
    (*r_0)[int(14)] = t_5;
    return;
}


#line 12 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 90 "core"
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


#line 173 "mm_2048_fusedTierB_c16.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 173
void stgPut_0(uint i_1, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 173
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_1] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 173
    return;
}


#line 192
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 194
    uint j_0 = d_1 / _S11;

#line 194
    uint m_0 = d_1 % _S11;

#line 194
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 195
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 195
    }
    else
    {

#line 195
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 195
    }

#line 195
    return _S12;
}


#line 174
half2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 174
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_2]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_2]) >> 16U) & 65535U)));
}


#line 509
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 510
    uint j_1;

#line 521
    thread array<half2, int(16)> out_0;

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
        out_0[z_0] = half2(0.0, 0.0);

#line 522
        z_0 = z_0 + 1U;

#line 522
    }
    uint _S13 = (1U << lgSpan_0) - 1U;
    uint _S14 = (1U << lgLen_0) - 1U;

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
            stgPut_0(j_1 * 128U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

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
            uint p_1 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
            uint b_4 = p_1 >> lgLen_0;

#line 531
            uint rem_0 = p_1 & _S14;
            uint i_3 = rem_0 >> lgSpan_0;

#line 532
            uint ln_0 = rem_0 & _S13;
            uint _S15 = c_1 * 16U;

#line 533
            bool _S16;

#line 533
            if(i_3 >= _S15)
            {

#line 533
                _S16 = i_3 < ((c_1 + 1U) * 16U);

#line 533
            }
            else
            {

#line 533
                _S16 = false;

#line 533
            }

#line 533
            if(_S16)
            {

#line 533
                half2 _S17 = stgGet_0((i_3 - _S15) * 128U + (b_4 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_2] = _S17;

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
        (*r_1)[j_1] = out_0[j_1];

#line 537
        j_1 = j_1 + 1U;

#line 537
    }
    return;
}


#line 368
void dft8_0(array<half2, int(16)> thread* r_2, uint o_0)
{


    thread array<half2, int(8)> b_5;

#line 372
    uint s_0 = 1U;
    for(;;)
    {

#line 373
        if(s_0 < 8U)
        {
        }
        else
        {

#line 373
            break;
        }

#line 373
        uint j_2 = 0U;
        for(;;)
        {

#line 374
            if(j_2 < 4U)
            {
            }
            else
            {

#line 374
                break;
            }

#line 375
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S18 = o_0 + j_2;

#line 378
            half2 t_6 = cmul_0(half2(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0))), (*r_2)[_S18 + 4U]);
            uint _S19 = ((j_2 - k_0) << 1U) + k_0;

#line 379
            b_5[_S19] = (*r_2)[_S18] + t_6;

#line 379
            b_5[_S19 + s_0] = (*r_2)[_S18] - t_6;

#line 374
            j_2 = j_2 + 1U;

#line 374
        }

#line 374
        uint i_4 = 0U;

#line 381
        for(;;)
        {

#line 381
            if(i_4 < 8U)
            {
            }
            else
            {

#line 381
                break;
            }

#line 381
            (*r_2)[o_0 + i_4] = b_5[i_4];

#line 381
            i_4 = i_4 + 1U;

#line 381
        }

#line 373
        s_0 = s_0 << 1U;

#line 373
    }

#line 383
    return;
}


#line 487
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 487
    uint b_6 = 0U;

#line 495
    for(;;)
    {

#line 495
        if(b_6 < 2U)
        {
        }
        else
        {

#line 495
            break;
        }

#line 495
        dft8_0(r_3, b_6 * 8U);

#line 495
        b_6 = b_6 + 1U;

#line 495
    }



    return;
}


#line 592
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 592
    uint _S20;

#line 592
    uint k2_1;

#line 592
    float cr_0;

#line 592
    float ci_0;

#line 592
    uint _S21;

#line 592
    for(;;)
    {

#line 592
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(128U);

#line 11
                _S20 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(2048U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 127U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 2048.0);
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
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(half(cr_0), half(ci_0)));
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
                uint per_2 = 16U / max(128U, 1U);
                uint _S25 = max(8U, 1U);

#line 38
                _S21 = _S25;
                uint blk2_2 = tid_0 / _S25;

#line 39
                uint lane2_2 = tid_0 % _S25;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 128U, 2048U, blk_2, lane_2, per_2, _S25, 128U, blk2_2, lane2_2, kernelContext_3);

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
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(half(cr_0), half(ci_0)));
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
                exchange_0(r_4, _S20, lgTB_1, 8U, 128U, blk_3, lane_3, per_3, _S29, 8U, blk2_3, lane2_3, kernelContext_3);

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

#line 595 "mm_2048_fusedTierB_c16.slang"
    return;
}


#line 561
uint lgOf_0(uint i_5)
{

#line 561
    uint _S30;

#line 561
    if(i_5 < 2U)
    {

#line 561
        _S30 = 4U;

#line 561
    }
    else
    {

#line 561
        if(i_5 == 2U)
        {

#line 561
            _S30 = 3U;

#line 561
        }
        else
        {

#line 561
            _S30 = 1U;

#line 561
        }

#line 561
    }

#line 561
    return _S30;
}


#line 563
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 567
    uint lg_1 = lgOf_0(1U);

#line 567
    uint lg_2 = lgOf_0(0U);

#line 572
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 601
void filterOne_0(uint pair_0, uint d_3, uint t_7, uint tid_1, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{


    bool live_0;

#line 624
    thread array<half2, int(16)> r_5;

#line 624
    uint n2_0 = 0U;



    for(;;)
    {

#line 628
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 628
            break;
        }

#line 629
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_7 * 2048U + tid_1 + 128U * n2_0));

#line 628
        n2_0 = n2_0 + 1U;

#line 628
    }

#line 628
    transform_0(&r_5, tid_1, kernelContext_4);

#line 654
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 713
    bool _S31 = tid_1 == 0U;

#line 713
    if(_S31)
    {

#line 713
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 713
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 713
    }

#line 718
    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;

#line 720
    uint i_6 = 0U;

    for(;;)
    {

#line 722
        if(i_6 < 16U)
        {
        }
        else
        {

#line 722
            break;
        }

#line 723
        uint idx_0 = slotToIndex_0(tid_1 * 16U + i_6);
        if(idx_0 >= winStart_1)
        {

#line 724
            live_0 = idx_0 < winEnd_1;

#line 724
        }
        else
        {

#line 724
            live_0 = false;

#line 724
        }



        float _rx_0 = float(r_5[i_6].x);

#line 728
        float _ry_0 = float(r_5[i_6].y);
        if(live_0)
        {

#line 729
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 729
        }
        else
        {

#line 729
            n2_0 = 0U;

#line 729
        }

#line 729
        myMag_0[i_6] = n2_0;

#line 722
        i_6 = i_6 + 1U;

#line 722
    }

#line 722
    uint bestBits_0 = thrBits_1;

#line 722
    i_6 = 0U;

#line 757
    for(;;)
    {

#line 757
        if(i_6 < 16U)
        {
        }
        else
        {

#line 757
            break;
        }

#line 757
        uint _S32 = max(bestBits_0, myMag_0[i_6]);

#line 757
        uint i_7 = i_6 + 1U;

#line 757
        bestBits_0 = _S32;

#line 757
        i_6 = i_7;

#line 757
    }

    uint wm_0 = simd_max(bestBits_0);
    bool _S33 = simd_is_first();

#line 760
    if(_S33)
    {

#line 760
        live_0 = wm_0 > thrBits_1;

#line 760
    }
    else
    {

#line 760
        live_0 = false;

#line 760
    }

#line 760
    if(live_0)
    {

#line 760
        uint _S34 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 760
    }

#line 775
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 775
    uint winner_0 = 4294967295U;

#line 775
    i_6 = 0U;

#line 785
    for(;;)
    {

#line 785
        if(i_6 < 16U)
        {
        }
        else
        {

#line 785
            break;
        }

#line 786
        if((myMag_0[i_6]) > thrBits_1)
        {

#line 786
            live_0 = (myMag_0[i_6]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 786
        }
        else
        {

#line 786
            live_0 = false;

#line 786
        }

#line 786
        if(live_0)
        {

#line 786
            winner_0 = min(winner_0, tid_1 * 16U + i_6);

#line 786
        }

#line 785
        i_6 = i_6 + 1U;

#line 785
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S35 = simd_is_first();

#line 790
    if(_S35)
    {

#line 790
        live_0 = waveWinner_0 != 4294967295U;

#line 790
    }
    else
    {

#line 790
        live_0 = false;

#line 790
    }

#line 790
    if(live_0)
    {

#line 791
        uint _S36 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 790
    }

#line 795
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 795
    i_6 = 0U;
    for(;;)
    {

#line 796
        if(i_6 < 16U)
        {
        }
        else
        {

#line 796
            break;
        }

#line 797
        uint _S37 = tid_1 * 16U + i_6;

#line 797
        if(_S37 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
        {

#line 798
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S37));

#line 798
            *(peakVal_0+pair_0) = packed_float2(float2(float(r_5[i_6].x), float(r_5[i_6].y))) ;

#line 797
        }

#line 796
        i_6 = i_6 + 1U;

#line 796
    }

#line 802
    if(_S31)
    {

#line 802
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 802
    }
    else
    {

#line 802
        live_0 = false;

#line 802
    }

#line 802
    if(live_0)
    {

#line 803
        *(peakIdx_0+pair_0) = int(-1);

#line 803
        *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 802
    }

#line 836
    return;
}


#line 961
void filterPair_0(uint pair_1, uint tid_2, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_5)
{

#line 967
    kernelContext_5->_tid_0 = tid_2;

#line 977
    uint _S38 = pair_1 / ntmpl_1;

#line 977
    uint _S39 = pair_1 % ntmpl_1;
    thread array<half2, int(16)> dreg_1;

#line 978
    uint n2_1 = 0U;

    for(;;)
    {

#line 980
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 980
            break;
        }

#line 981
        dreg_1[n2_1] = cload_0(data_1, _S38 * 2048U + tid_2 + 128U * n2_1);

#line 980
        n2_1 = n2_1 + 1U;

#line 980
    }

#line 980
    uint k_1 = 0U;

#line 991
    for(;;)
    {

#line 991
        if(k_1 < 1U)
        {
        }
        else
        {

#line 991
            break;
        }

#line 992
        uint _S40 = pair_1 + k_1;

#line 992
        uint _S41 = _S39 + k_1;

#line 992
        thread array<half2, int(16)> _S42 = dreg_1;

#line 992
        filterOne_0(_S40, _S38, _S41, tid_2, &_S42, data_1, tmpl_1, peakIdx_1, peakVal_1, winStart_2, winEnd_2, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_5);

#line 991
        k_1 = k_1 + 1U;

#line 991
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 999
    thread KernelContext_0 kernelContext_6;

#line 999
    (&kernelContext_6)->entryPointParams_0 = entryPointParams_1;

#line 999
    (&kernelContext_6)->entryPointParams_data_0 = entryPointParams_data_1;

#line 999
    (&kernelContext_6)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 999
    (&kernelContext_6)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 999
    (&kernelContext_6)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 999
    threadgroup array<uint, int(2048)> stg_1;

#line 999
    (&kernelContext_6)->stg_0 = &stg_1;

#line 1016
    uint _pr_0 = gid_0.x;

#line 1016
    uint _t_0 = lid_0.x;
    (&kernelContext_6)->_stgBase_0 = 0U;

#line 1017
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_6);

#line 1025
    return;
}
