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


#line 147 "mm_128_fusedTierB_c16.slang"
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


#line 341
void r4_0(half2 thread* a_1, half2 thread* b_2, half2 thread* c_0, half2 thread* d_0)
{
    half2 t0_0 = *a_1 + *c_0;

#line 343
    half2 t1_0 = *a_1 - *c_0;

#line 343
    half2 t2_0 = *b_2 + *d_0;

#line 343
    half2 t3_0 = *b_2 - *d_0;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 345
    *b_2 = t1_0 + j3_0;

#line 345
    *c_0 = t0_0 - t2_0;

#line 345
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


#line 377
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125h, 0.382568359375h);
    half2 W2_0 = half2(0.70703125h, 0.70703125h);
    half2 W3_0 = half2(0.382568359375h, 0.923828125h);
    half2 W4_0 = half2(0.0h, 1.0h);
    half2 W6_0 = half2(-0.70703125h, 0.70703125h);
    half2 W9_0 = half2(-0.923828125h, -0.382568359375h);

#line 384
    uint n1_0 = 0U;
    for(;;)
    {

#line 385
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 385
            break;
        }

#line 385
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 385
        n1_0 = n1_0 + 1U;

#line 385
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 386
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 386
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 387
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 387
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 388
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 388
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 388
    uint k2_0 = 0U;
    for(;;)
    {

#line 389
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 389
            break;
        }

#line 389
        uint _S10 = 4U * k2_0;

#line 389
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 389
        k2_0 = k2_0 + 1U;

#line 389
    }

    half2 t_0 = (*r_0)[int(1)];

#line 391
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 391
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 392
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 392
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 393
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 393
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 394
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 394
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 395
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 395
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 396
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 396
    (*r_0)[int(14)] = t_5;
    return;
}


#line 10 "twiddle.slang"
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


#line 173 "mm_128_fusedTierB_c16.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(128)> threadgroup* stg_0;
};


#line 173
void stgPut_0(uint i_1, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 173
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_1] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 173
    return;
}


#line 174
half2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 174
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_2]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_2]) >> 16U) & 65535U)));
}


#line 502
void exchange_0(array<half2, int(16)> thread* r_1, const array<uint, int(16)> thread* want_0, uint lgLen_0, uint lgSpan_0, KernelContext_0 thread* kernelContext_2)
{

#line 502
    uint j_0;

#line 513
    thread array<half2, int(16)> out_0;

#line 513
    uint z_0 = 0U;
    for(;;)
    {

#line 514
        if(z_0 < 16U)
        {
        }
        else
        {

#line 514
            break;
        }

#line 514
        out_0[z_0] = half2(0.0h, 0.0h);

#line 514
        z_0 = z_0 + 1U;

#line 514
    }
    uint _S11 = (1U << lgSpan_0) - 1U;
    uint _S12 = (1U << lgLen_0) - 1U;

#line 516
    uint c_1 = 0U;
    for(;;)
    {

#line 517
        if(c_1 < 1U)
        {
        }
        else
        {

#line 517
            break;
        }

#line 518
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 518
        j_0 = 0U;
        for(;;)
        {

#line 519
            if(j_0 < 16U)
            {
            }
            else
            {

#line 519
                break;
            }

#line 519
            stgPut_0(j_0 * 8U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_0], kernelContext_2);

#line 519
            j_0 = j_0 + 1U;

#line 519
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 520
        uint d_1 = 0U;
        for(;;)
        {

#line 521
            if(d_1 < 16U)
            {
            }
            else
            {

#line 521
                break;
            }
            uint b_4 = ((*want_0)[d_1]) >> lgLen_0;

#line 523
            uint rem_0 = ((*want_0)[d_1]) & _S12;
            uint i_3 = rem_0 >> lgSpan_0;

#line 524
            uint ln_0 = rem_0 & _S11;
            uint _S13 = c_1 * 16U;

#line 525
            bool _S14;

#line 525
            if(i_3 >= _S13)
            {

#line 525
                _S14 = i_3 < ((c_1 + 1U) * 16U);

#line 525
            }
            else
            {

#line 525
                _S14 = false;

#line 525
            }

#line 525
            if(_S14)
            {

#line 525
                half2 _S15 = stgGet_0((i_3 - _S13) * 8U + (b_4 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_1] = _S15;

#line 525
            }

#line 521
            d_1 = d_1 + 1U;

#line 521
        }

#line 517
        c_1 = c_1 + 1U;

#line 517
    }

#line 517
    j_0 = 0U;

#line 529
    for(;;)
    {

#line 529
        if(j_0 < 16U)
        {
        }
        else
        {

#line 529
            break;
        }

#line 529
        (*r_1)[j_0] = out_0[j_0];

#line 529
        j_0 = j_0 + 1U;

#line 529
    }
    return;
}


#line 361
void dft8_0(array<half2, int(16)> thread* r_2, uint o_0)
{


    thread array<half2, int(8)> b_5;

#line 365
    uint s_0 = 1U;
    for(;;)
    {

#line 366
        if(s_0 < 8U)
        {
        }
        else
        {

#line 366
            break;
        }

#line 366
        uint j_1 = 0U;
        for(;;)
        {

#line 367
            if(j_1 < 4U)
            {
            }
            else
            {

#line 367
                break;
            }

#line 368
            uint k_0 = j_1 & (s_0 - 1U);


            uint _S16 = o_0 + j_1;

#line 371
            half2 t_6 = cmul_0(half2(mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_0))), (*r_2)[_S16 + 4U]);
            uint _S17 = ((j_1 - k_0) << 1U) + k_0;

#line 372
            b_5[_S17] = (*r_2)[_S16] + t_6;

#line 372
            b_5[_S17 + s_0] = (*r_2)[_S16] - t_6;

#line 367
            j_1 = j_1 + 1U;

#line 367
        }

#line 367
        uint i_4 = 0U;

#line 374
        for(;;)
        {

#line 374
            if(i_4 < 8U)
            {
            }
            else
            {

#line 374
                break;
            }

#line 374
            (*r_2)[o_0 + i_4] = b_5[i_4];

#line 374
            i_4 = i_4 + 1U;

#line 374
        }

#line 366
        s_0 = s_0 << 1U;

#line 366
    }

#line 376
    return;
}


#line 480
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 480
    uint b_6 = 0U;

#line 488
    for(;;)
    {

#line 488
        if(b_6 < 2U)
        {
        }
        else
        {

#line 488
            break;
        }

#line 488
        dft8_0(r_3, b_6 * 8U);

#line 488
        b_6 = b_6 + 1U;

#line 488
    }



    return;
}


#line 584
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 584
    for(;;)
    {

#line 584
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {

#line 8
                thread array<uint, int(16)> want_1;

#line 8
                uint z_1 = 0U;
                for(;;)
                {

#line 9
                    if(z_1 < 16U)
                    {
                    }
                    else
                    {

#line 9
                        break;
                    }

#line 9
                    want_1[z_1] = 0U;

#line 9
                    z_1 = z_1 + 1U;

#line 9
                }



                uint lgTB_0 = firstbithigh_0(8U);
                uint lgLn_0 = firstbithigh_0(128U);
                uint _S18 = tid_0 >> lgTB_0;
                uint lane_0 = tid_0 & 7U;


                dft16_0(r_4);

#line 28
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_0) / 128.0f);
                float _S19 = tw_0.x;

#line 29
                float _S20 = tw_0.y;

#line 29
                uint k2_1 = 0U;

#line 29
                float cr_0 = 1.0f;

#line 29
                float ci_0 = 0.0f;

                for(;;)
                {

#line 31
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 31
                        break;
                    }

#line 32
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(half(cr_0), half(ci_0)));
                    float nr_0 = cr_0 * _S19 - ci_0 * _S20;
                    float _S21 = cr_0 * _S20 + ci_0 * _S19;

#line 31
                    k2_1 = k2_1 + 1U;

#line 31
                    cr_0 = nr_0;

#line 31
                    ci_0 = _S21;

#line 31
                }

#line 41
                uint _S22 = max(8U, 1U);

#line 41
                uint _S23 = 16U / _S22;
                uint _S24 = max(0U, 1U);
                uint _S25 = tid_0 / _S24;

#line 43
                uint _S26 = tid_0 % _S24;

#line 43
                uint d_2 = 0U;
                for(;;)
                {

#line 44
                    if(d_2 < 16U)
                    {
                    }
                    else
                    {

#line 44
                        break;
                    }

#line 45
                    uint j_2 = d_2 / _S22;

#line 45
                    uint m_0 = d_2 % _S22;
                    want_1[d_2] = _S18 * 128U + (lane_0 * _S23 + j_2) * 8U + m_0;

#line 44
                    d_2 = d_2 + 1U;

#line 44
                }

#line 44
                thread array<uint, int(16)> _S27 = want_1;

#line 44
                exchange_0(r_4, &_S27, lgLn_0, lgTB_0, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        break;
    }

#line 52
    innermost_0(r_4);

#line 587 "mm_128_fusedTierB_c16.slang"
    return;
}


#line 553
uint lgOf_0(uint i_5)
{

#line 553
    uint _S28;

#line 553
    if(i_5 < 1U)
    {

#line 553
        _S28 = 4U;

#line 553
    }
    else
    {

#line 553
        if(i_5 == 1U)
        {

#line 553
            _S28 = 3U;

#line 553
        }
        else
        {

#line 553
            _S28 = 1U;

#line 553
        }

#line 553
    }

#line 553
    return _S28;
}


#line 555
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 559
    uint lg_1 = lgOf_0(0U);

#line 564
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 593
void filterOne_0(uint pair_0, uint d_3, uint t_7, uint tid_1, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{


    bool live_0;

#line 616
    thread array<half2, int(16)> r_5;

#line 616
    uint n2_0 = 0U;



    for(;;)
    {

#line 620
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 620
            break;
        }

#line 621
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_7 * 128U + tid_1 + 8U * n2_0));

#line 620
        n2_0 = n2_0 + 1U;

#line 620
    }

#line 620
    transform_0(&r_5, tid_1, kernelContext_4);

#line 646
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 652
    bool _S29 = tid_1 == 0U;

#line 652
    if(_S29)
    {

#line 652
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 652
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 652
    }

#line 657
    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;

#line 659
    uint i_6 = 0U;

    for(;;)
    {

#line 661
        if(i_6 < 16U)
        {
        }
        else
        {

#line 661
            break;
        }

#line 662
        uint idx_0 = slotToIndex_0(tid_1 * 16U + i_6);
        if(idx_0 >= winStart_1)
        {

#line 663
            live_0 = idx_0 < winEnd_1;

#line 663
        }
        else
        {

#line 663
            live_0 = false;

#line 663
        }



        float _rx_0 = float(r_5[i_6].x);

#line 667
        float _ry_0 = float(r_5[i_6].y);
        if(live_0)
        {

#line 668
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 668
        }
        else
        {

#line 668
            n2_0 = 0U;

#line 668
        }

#line 668
        myMag_0[i_6] = n2_0;

#line 661
        i_6 = i_6 + 1U;

#line 661
    }

#line 661
    uint bestBits_0 = thrBits_1;

#line 661
    i_6 = 0U;

#line 696
    for(;;)
    {

#line 696
        if(i_6 < 16U)
        {
        }
        else
        {

#line 696
            break;
        }

#line 696
        uint _S30 = max(bestBits_0, myMag_0[i_6]);

#line 696
        uint i_7 = i_6 + 1U;

#line 696
        bestBits_0 = _S30;

#line 696
        i_6 = i_7;

#line 696
    }

    uint wm_0 = simd_max(bestBits_0);
    bool _S31 = simd_is_first();

#line 699
    if(_S31)
    {

#line 699
        live_0 = wm_0 > thrBits_1;

#line 699
    }
    else
    {

#line 699
        live_0 = false;

#line 699
    }

#line 699
    if(live_0)
    {

#line 699
        uint _S32 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 699
    }

#line 714
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 714
    uint winner_0 = 4294967295U;

#line 714
    i_6 = 0U;

#line 724
    for(;;)
    {

#line 724
        if(i_6 < 16U)
        {
        }
        else
        {

#line 724
            break;
        }

#line 725
        if((myMag_0[i_6]) > thrBits_1)
        {

#line 725
            live_0 = (myMag_0[i_6]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 725
        }
        else
        {

#line 725
            live_0 = false;

#line 725
        }

#line 725
        if(live_0)
        {

#line 725
            winner_0 = min(winner_0, tid_1 * 16U + i_6);

#line 725
        }

#line 724
        i_6 = i_6 + 1U;

#line 724
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S33 = simd_is_first();

#line 729
    if(_S33)
    {

#line 729
        live_0 = waveWinner_0 != 4294967295U;

#line 729
    }
    else
    {

#line 729
        live_0 = false;

#line 729
    }

#line 729
    if(live_0)
    {

#line 730
        uint _S34 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 729
    }

#line 734
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 734
    i_6 = 0U;
    for(;;)
    {

#line 735
        if(i_6 < 16U)
        {
        }
        else
        {

#line 735
            break;
        }

#line 736
        uint _S35 = tid_1 * 16U + i_6;

#line 736
        if(_S35 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
        {

#line 737
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S35));

#line 737
            *(peakVal_0+pair_0) = packed_float2(float2(float(r_5[i_6].x), float(r_5[i_6].y))) ;

#line 736
        }

#line 735
        i_6 = i_6 + 1U;

#line 735
    }

#line 741
    if(_S29)
    {

#line 741
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 741
    }
    else
    {

#line 741
        live_0 = false;

#line 741
    }

#line 741
    if(live_0)
    {

#line 742
        *(peakIdx_0+pair_0) = int(-1);

#line 742
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 741
    }

#line 774
    return;
}


#line 914
void filterPair_0(uint pair_1, uint tid_2, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_5)
{

#line 920
    kernelContext_5->_tid_0 = tid_2;

#line 930
    uint _S36 = pair_1 / ntmpl_1;

#line 930
    uint _S37 = pair_1 % ntmpl_1;
    thread array<half2, int(16)> dreg_1;

#line 931
    uint n2_1 = 0U;

    for(;;)
    {

#line 933
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 933
            break;
        }

#line 934
        dreg_1[n2_1] = cload_0(data_1, _S36 * 128U + tid_2 + 8U * n2_1);

#line 933
        n2_1 = n2_1 + 1U;

#line 933
    }

#line 933
    uint k_1 = 0U;

#line 944
    for(;;)
    {

#line 944
        if(k_1 < 1U)
        {
        }
        else
        {

#line 944
            break;
        }

#line 945
        uint _S38 = pair_1 + k_1;

#line 945
        uint _S39 = _S37 + k_1;

#line 945
        thread array<half2, int(16)> _S40 = dreg_1;

#line 945
        filterOne_0(_S38, _S36, _S39, tid_2, &_S40, data_1, tmpl_1, peakIdx_1, peakVal_1, winStart_2, winEnd_2, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_5);

#line 944
        k_1 = k_1 + 1U;

#line 944
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 952
    thread KernelContext_0 kernelContext_6;

#line 952
    (&kernelContext_6)->entryPointParams_0 = entryPointParams_1;

#line 952
    (&kernelContext_6)->entryPointParams_data_0 = entryPointParams_data_1;

#line 952
    (&kernelContext_6)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 952
    (&kernelContext_6)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 952
    (&kernelContext_6)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 952
    threadgroup array<uint, int(128)> stg_1;

#line 952
    (&kernelContext_6)->stg_0 = &stg_1;

#line 969
    uint _pr_0 = gid_0.x;

#line 969
    uint _t_0 = lid_0.x;
    (&kernelContext_6)->_stgBase_0 = 0U;

#line 970
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_6);

#line 978
    return;
}
