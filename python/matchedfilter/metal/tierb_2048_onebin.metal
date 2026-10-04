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


#line 151 "mm_2048_fusedTierB_onebin.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 151
    return float2(*(b_0+i_0)) ;
}


#line 191
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 191
    float _S2 = a_0.x;

#line 191
    float _S3 = b_1.x;

#line 191
    float _S4 = a_0.y;

#line 191
    float _S5 = b_1.y;

#line 191
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 348
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 350
    float2 t1_0 = *a_1 - *c_0;

#line 350
    float2 t2_0 = *b_2 + *d_0;

#line 350
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
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
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 190
    float _S6 = a_2.x;

#line 190
    float _S7 = b_3.x;

#line 190
    float _S8 = a_2.y;

#line 190
    float _S9 = b_3.y;

#line 190
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 384
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

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

    float2 t_0 = (*r_0)[int(1)];

#line 398
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 398
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 399
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 399
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 400
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 400
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 401
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 401
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 402
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 402
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

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


#line 179 "mm_2048_fusedTierB_onebin.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(4096)> threadgroup* stg_0;
};


#line 179
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 179
    uint _S11 = 2U * i_1;

#line 179
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11] = (as_type<uint>((v_0.x)));

#line 179
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11 + 1U] = (as_type<uint>((v_0.y)));

#line 179
    return;
}


#line 192
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 194
    uint j_0 = d_1 / _S12;

#line 194
    uint m_0 = d_1 % _S12;

#line 194
    uint _S13;
    if(TB_0 <= 16U)
    {

#line 195
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 195
    }
    else
    {

#line 195
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 195
    }

#line 195
    return _S13;
}


#line 180
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 180
    uint _S14 = 2U * i_2;

#line 180
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 509
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 510
    uint j_1;

#line 521
    thread array<float2, int(16)> out_0;

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
        out_0[z_0] = float2(0.0, 0.0);

#line 522
        z_0 = z_0 + 1U;

#line 522
    }
    uint _S15 = (1U << lgSpan_0) - 1U;
    uint _S16 = (1U << lgLen_0) - 1U;

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
            uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
            uint b_4 = p_0 >> lgLen_0;

#line 531
            uint rem_0 = p_0 & _S16;
            uint i_3 = rem_0 >> lgSpan_0;

#line 532
            uint ln_0 = rem_0 & _S15;
            uint _S17 = c_1 * 16U;

#line 533
            bool _S18;

#line 533
            if(i_3 >= _S17)
            {

#line 533
                _S18 = i_3 < ((c_1 + 1U) * 16U);

#line 533
            }
            else
            {

#line 533
                _S18 = false;

#line 533
            }

#line 533
            if(_S18)
            {

#line 533
                float2 _S19 = stgGet_0((i_3 - _S17) * 128U + (b_4 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_2] = _S19;

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
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_5;

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


            uint _S20 = o_0 + j_2;

#line 378
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0)), (*r_2)[_S20 + 4U]);
            uint _S21 = ((j_2 - k_0) << 1U) + k_0;

#line 379
            b_5[_S21] = (*r_2)[_S20] + t_6;

#line 379
            b_5[_S21 + s_0] = (*r_2)[_S20] - t_6;

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
void innermost_0(array<float2, int(16)> thread* r_3)
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
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 592
    uint _S22;

#line 592
    uint k2_1;

#line 592
    float cr_0;

#line 592
    float ci_0;

#line 592
    uint _S23;

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

#line 595 "mm_2048_fusedTierB_onebin.slang"
    return;
}


#line 561
uint lgOf_0(uint i_5)
{

#line 561
    uint _S32;

#line 561
    if(i_5 < 2U)
    {

#line 561
        _S32 = 4U;

#line 561
    }
    else
    {

#line 561
        if(i_5 == 2U)
        {

#line 561
            _S32 = 3U;

#line 561
        }
        else
        {

#line 561
            _S32 = 1U;

#line 561
        }

#line 561
    }

#line 561
    return _S32;
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


#line 607
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 621
    kernelContext_4->_tid_0 = tid_1;
    uint _S33 = pair_0 / ntmpl_1;

#line 622
    uint _S34 = pair_0 % ntmpl_1;

    thread array<float2, int(16)> r_5;

#line 624
    uint n2_0 = 0U;

#line 635
    for(;;)
    {

#line 635
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 635
            break;
        }

#line 636
        uint idx_0 = tid_1 + 128U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S33 * 2048U + idx_0), cload_0(tmpl_0, _S34 * 2048U + idx_0));

#line 635
        n2_0 = n2_0 + 1U;

#line 635
    }

#line 635
    transform_0(&r_5, tid_1, kernelContext_4);

#line 654
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 659
    bool _S35 = tid_1 == 0U;

#line 659
    if(_S35)
    {

#line 659
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 659
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 659
    }



    float2 _S36 = float2(0.0, 0.0);

#line 663
    bool live_0;

    if(winStart_1 == 0U)
    {

#line 665
        live_0 = winEnd_1 >= 2048U;

#line 665
    }
    else
    {

#line 665
        live_0 = false;

#line 665
    }

#line 665
    uint threadBestBits_0;

#line 665
    uint threadBestSlot_0;

#line 665
    uint winner_0;

#line 665
    float2 threadBestVal_0;

#line 665
    if(live_0)
    {

#line 665
        threadBestBits_0 = thrBits_1;

#line 665
        threadBestSlot_0 = 4294967295U;

#line 665
        threadBestVal_0 = _S36;

#line 665
        winner_0 = 0U;
        for(;;)
        {

#line 666
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 666
                break;
            }

#line 667
            float _rx_0 = r_5[winner_0].x;

#line 667
            float _ry_0 = r_5[winner_0].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > threadBestBits_0)
            {
                uint _S37 = tid_1 * 16U + winner_0;
                float2 _S38 = float2(_rx_0, _ry_0);

#line 672
                threadBestBits_0 = magBits_0;

#line 672
                threadBestSlot_0 = _S37;

#line 672
                threadBestVal_0 = _S38;

#line 669
            }

#line 666
            winner_0 = winner_0 + 1U;

#line 666
        }

#line 665
    }
    else
    {

#line 665
        threadBestBits_0 = thrBits_1;

#line 665
        threadBestSlot_0 = 4294967295U;

#line 665
        threadBestVal_0 = _S36;

#line 665
        winner_0 = 0U;

#line 676
        for(;;)
        {

#line 676
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 676
                break;
            }

#line 677
            uint _S39 = tid_1 * 16U + winner_0;

#line 677
            uint idx_1 = slotToIndex_0(_S39);
            if(idx_1 >= winStart_1)
            {

#line 678
                live_0 = idx_1 < winEnd_1;

#line 678
            }
            else
            {

#line 678
                live_0 = false;

#line 678
            }
            float _rx_1 = r_5[winner_0].x;

#line 679
            float _ry_1 = r_5[winner_0].y;

#line 679
            uint magBits_1;
            if(live_0)
            {

#line 680
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 680
            }
            else
            {

#line 680
                magBits_1 = 0U;

#line 680
            }
            if(magBits_1 > threadBestBits_0)
            {

                float2 _S40 = float2(_rx_1, _ry_1);

#line 684
                threadBestBits_0 = magBits_1;

#line 684
                threadBestSlot_0 = _S39;

#line 684
                threadBestVal_0 = _S40;

#line 681
            }

#line 676
            winner_0 = winner_0 + 1U;

#line 676
        }

#line 665
    }

#line 689
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(threadBestBits_0);
    bool _S41 = simd_is_first();

#line 693
    if(_S41)
    {

#line 693
        live_0 = wm_0 > thrBits_1;

#line 693
    }
    else
    {

#line 693
        live_0 = false;

#line 693
    }

#line 693
    if(live_0)
    {

#line 693
        uint _S42 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 693
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(threadBestBits_0 > thrBits_1)
    {

#line 700
        live_0 = threadBestBits_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 700
    }
    else
    {

#line 700
        live_0 = false;

#line 700
    }

#line 700
    if(live_0)
    {

#line 700
        winner_0 = threadBestSlot_0;

#line 700
    }
    else
    {

#line 700
        winner_0 = 4294967295U;

#line 700
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S43 = simd_is_first();

#line 705
    if(_S43)
    {

#line 705
        live_0 = waveWinner_0 != 4294967295U;

#line 705
    }
    else
    {

#line 705
        live_0 = false;

#line 705
    }

#line 705
    if(live_0)
    {

#line 706
        uint _S44 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 705
    }

#line 710
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(threadBestSlot_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
    {

#line 712
        live_0 = threadBestSlot_0 != 4294967295U;

#line 712
    }
    else
    {

#line 712
        live_0 = false;

#line 712
    }

#line 712
    if(live_0)
    {

#line 713
        *(peakIdx_0+pair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 713
        *(peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 712
    }



    if(_S35)
    {

#line 716
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 716
    }
    else
    {

#line 716
        live_0 = false;

#line 716
    }

#line 716
    if(live_0)
    {

#line 717
        *(peakIdx_0+pair_0) = int(-1);

#line 717
        *(peakVal_0+pair_0) = packed_float2(_S36) ;

#line 716
    }

#line 849
    return;
}


#line 1012
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1012
    thread KernelContext_0 kernelContext_5;

#line 1012
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1012
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1012
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1012
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1012
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1012
    threadgroup array<uint, int(4096)> stg_1;

#line 1012
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1029
    uint _pr_0 = gid_0.x;

#line 1029
    uint _t_0 = lid_0.x;
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 1030
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);

#line 1038
    return;
}
