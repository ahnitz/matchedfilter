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


#line 180 "mm_2048_refineListed_onebin.slang"
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


#line 419
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 421
    float2 t1_0 = *a_1 - *c_0;

#line 421
    float2 t2_0 = *b_2 + *d_1;

#line 421
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 423
    *b_2 = t1_0 + j3_0;

#line 423
    *c_0 = t0_0 - t2_0;

#line 423
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


#line 455
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 462
    uint n1_0 = 0U;
    for(;;)
    {

#line 463
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 463
            break;
        }

#line 463
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 463
        n1_0 = n1_0 + 1U;

#line 463
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 464
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 464
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 465
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 465
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 466
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 466
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 466
    uint k2_0 = 0U;
    for(;;)
    {

#line 467
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 467
            break;
        }

#line 467
        uint _S10 = 4U * k2_0;

#line 467
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 467
        k2_0 = k2_0 + 1U;

#line 467
    }

    float2 t_0 = (*r_0)[int(1)];

#line 469
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 469
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 470
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 470
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 471
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 471
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 472
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 472
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 473
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 473
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 474
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 474
    (*r_0)[int(14)] = t_5;
    return;
}


#line 22 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 253 "mm_2048_refineListed_onebin.slang"
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


#line 8402 "hlsl.meta.slang"
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


#line 240 "mm_2048_refineListed_onebin.slang"
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


#line 615
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 616
    uint j_1;

#line 627
    thread array<float2, int(16)> out_0;

#line 627
    uint z_0 = 0U;
    for(;;)
    {

#line 628
        if(z_0 < 16U)
        {
        }
        else
        {

#line 628
            break;
        }

#line 628
        out_0[z_0] = float2(0.0, 0.0);

#line 628
        z_0 = z_0 + 1U;

#line 628
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S15 = p0_0 & lenMask_0;

#line 634
    uint _S16 = (_S15 >> lgSpan_0) * 128U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 634
    uint c_1 = 0U;

    for(;;)
    {

#line 636
        if(c_1 < 1U)
        {
        }
        else
        {

#line 636
            break;
        }

#line 637
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 637
        j_1 = 0U;
        for(;;)
        {

#line 638
            if(j_1 < 16U)
            {
            }
            else
            {

#line 638
                break;
            }

#line 638
            stgPut_0(j_1 * 128U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 638
            j_1 = j_1 + 1U;

#line 638
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 639
        uint d_3 = 0U;
        for(;;)
        {

#line 640
            if(d_3 < 16U)
            {
            }
            else
            {

#line 640
                break;
            }

#line 641
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S17 = pz_0 & lenMask_0;
            uint az_0 = (_S17 >> lgSpan_0) * 128U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S17 & spanMask_0);

#line 643
            float2 _S18 = stgGet_0(_S16 + az_0 - c_1 * 16U * 128U, kernelContext_2);


            out_0[d_3] = _S18;

#line 640
            d_3 = d_3 + 1U;

#line 640
        }

#line 636
        c_1 = c_1 + 1U;

#line 636
    }

#line 636
    j_1 = 0U;

#line 649
    for(;;)
    {

#line 649
        if(j_1 < 16U)
        {
        }
        else
        {

#line 649
            break;
        }

#line 649
        (*r_1)[j_1] = out_0[j_1];

#line 649
        j_1 = j_1 + 1U;

#line 649
    }
    return;
}


#line 439
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_4;

#line 443
    uint s_0 = 1U;
    for(;;)
    {

#line 444
        if(s_0 < 8U)
        {
        }
        else
        {

#line 444
            break;
        }

#line 444
        uint j_2 = 0U;
        for(;;)
        {

#line 445
            if(j_2 < 4U)
            {
            }
            else
            {

#line 445
                break;
            }

#line 446
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S19 = o_0 + j_2;

#line 449
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0)), (*r_2)[_S19 + 4U]);
            uint _S20 = ((j_2 - k_0) << 1U) + k_0;

#line 450
            b_4[_S20] = (*r_2)[_S19] + t_6;

#line 450
            b_4[_S20 + s_0] = (*r_2)[_S19] - t_6;

#line 445
            j_2 = j_2 + 1U;

#line 445
        }

#line 445
        uint i_3 = 0U;

#line 452
        for(;;)
        {

#line 452
            if(i_3 < 8U)
            {
            }
            else
            {

#line 452
                break;
            }

#line 452
            (*r_2)[o_0 + i_3] = b_4[i_3];

#line 452
            i_3 = i_3 + 1U;

#line 452
        }

#line 444
        s_0 = s_0 << 1U;

#line 444
    }

#line 454
    return;
}


#line 558
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 558
    uint b_5 = 0U;

#line 566
    for(;;)
    {

#line 566
        if(b_5 < 2U)
        {
        }
        else
        {

#line 566
            break;
        }

#line 566
        dft8_0(r_3, b_5 * 8U);

#line 566
        b_5 = b_5 + 1U;

#line 566
    }



    return;
}


#line 705
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 705
    uint _S21;

#line 705
    uint k2_1;

#line 705
    float cr_0;

#line 705
    float ci_0;

#line 705
    uint _S22;

#line 705
    for(;;)
    {

#line 705
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(128U);

#line 11
                _S21 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(2048U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 127U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 2048.0);
                float _S23 = tw_0.x;

#line 27
                float _S24 = tw_0.y;

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
                    float nr_0 = cr_0 * _S23 - ci_0 * _S24;
                    float _S25 = cr_0 * _S24 + ci_0 * _S23;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S25;

#line 29
                }

#line 37
                uint per_2 = 16U / max(128U, 1U);
                uint _S26 = max(8U, 1U);

#line 38
                _S22 = _S26;
                uint blk2_2 = tid_0 / _S26;

#line 39
                uint lane2_2 = tid_0 % _S26;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 128U, 2048U, blk_2, lane_2, per_2, _S26, 128U, blk2_2, lane2_2, kernelContext_3);

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
                float _S27 = tw_1.x;

#line 27
                float _S28 = tw_1.y;

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
                    float nr_1 = cr_0 * _S27 - ci_0 * _S28;
                    float _S29 = cr_0 * _S28 + ci_0 * _S27;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S29;

#line 29
                }

#line 37
                uint per_3 = 16U / _S22;
                uint _S30 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S30;

#line 39
                uint lane2_3 = tid_0 % _S30;

#line 39
                exchange_0(r_4, _S21, lgTB_1, 8U, 128U, blk_3, lane_3, per_3, _S30, 8U, blk2_3, lane2_3, kernelContext_3);

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

#line 708 "mm_2048_refineListed_onebin.slang"
    return;
}


#line 674
uint lgOf_0(uint i_4)
{

#line 674
    uint _S31;

#line 674
    if(i_4 < 2U)
    {

#line 674
        _S31 = 4U;

#line 674
    }
    else
    {

#line 674
        if(i_4 == 2U)
        {

#line 674
            _S31 = 3U;

#line 674
        }
        else
        {

#line 674
            _S31 = 1U;

#line 674
        }

#line 674
    }

#line 674
    return _S31;
}


#line 676
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 680
    uint lg_1 = lgOf_0(1U);

#line 680
    uint lg_2 = lgOf_0(0U);

#line 685
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 720
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 734
    kernelContext_4->_tid_0 = tid_1;
    uint _S32 = pair_0 / ntmpl_1;

#line 735
    uint _S33 = pair_0 % ntmpl_1;

    thread array<float2, int(16)> r_5;

#line 737
    uint n2_0 = 0U;

#line 748
    for(;;)
    {

#line 748
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 748
            break;
        }

#line 749
        uint idx_0 = tid_1 + 128U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S32 * 2048U + idx_0), cload_0(tmpl_0, _S33 * 2048U + idx_0));

#line 748
        n2_0 = n2_0 + 1U;

#line 748
    }

#line 748
    transform_0(&r_5, tid_1, kernelContext_4);

#line 767
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 772
    bool _S34 = tid_1 == 0U;

#line 772
    if(_S34)
    {

#line 772
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 772
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 772
    }



    float2 _S35 = float2(0.0, 0.0);

#line 776
    bool live_0;

    if(winStart_2 == 0U)
    {

#line 778
        live_0 = winEnd_2 >= 2048U;

#line 778
    }
    else
    {

#line 778
        live_0 = false;

#line 778
    }

#line 778
    uint threadBestBits_0;

#line 778
    uint threadBestSlot_0;

#line 778
    uint winner_0;

#line 778
    float2 threadBestVal_0;

#line 778
    if(live_0)
    {

#line 778
        threadBestBits_0 = thrBits_1;

#line 778
        threadBestSlot_0 = 4294967295U;

#line 778
        threadBestVal_0 = _S35;

#line 778
        winner_0 = 0U;
        for(;;)
        {

#line 779
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 779
                break;
            }

#line 780
            float _rx_0 = r_5[winner_0].x;

#line 780
            float _ry_0 = r_5[winner_0].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > threadBestBits_0)
            {
                uint _S36 = tid_1 * 16U + winner_0;
                float2 _S37 = float2(_rx_0, _ry_0);

#line 785
                threadBestBits_0 = magBits_0;

#line 785
                threadBestSlot_0 = _S36;

#line 785
                threadBestVal_0 = _S37;

#line 782
            }

#line 779
            winner_0 = winner_0 + 1U;

#line 779
        }

#line 778
    }
    else
    {

#line 778
        threadBestBits_0 = thrBits_1;

#line 778
        threadBestSlot_0 = 4294967295U;

#line 778
        threadBestVal_0 = _S35;

#line 778
        winner_0 = 0U;

#line 789
        for(;;)
        {

#line 789
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 789
                break;
            }

#line 790
            uint _S38 = tid_1 * 16U + winner_0;

#line 790
            uint idx_1 = slotToIndex_0(_S38);
            if(idx_1 >= winStart_2)
            {

#line 791
                live_0 = idx_1 < winEnd_2;

#line 791
            }
            else
            {

#line 791
                live_0 = false;

#line 791
            }
            float _rx_1 = r_5[winner_0].x;

#line 792
            float _ry_1 = r_5[winner_0].y;

#line 792
            uint magBits_1;
            if(live_0)
            {

#line 793
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 793
            }
            else
            {

#line 793
                magBits_1 = 0U;

#line 793
            }
            if(magBits_1 > threadBestBits_0)
            {

                float2 _S39 = float2(_rx_1, _ry_1);

#line 797
                threadBestBits_0 = magBits_1;

#line 797
                threadBestSlot_0 = _S38;

#line 797
                threadBestVal_0 = _S39;

#line 794
            }

#line 789
            winner_0 = winner_0 + 1U;

#line 789
        }

#line 778
    }

#line 802
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(threadBestBits_0);
    bool _S40 = simd_is_first();

#line 806
    if(_S40)
    {

#line 806
        live_0 = wm_0 > thrBits_1;

#line 806
    }
    else
    {

#line 806
        live_0 = false;

#line 806
    }

#line 806
    if(live_0)
    {

#line 806
        uint _S41 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 806
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(threadBestBits_0 > thrBits_1)
    {

#line 813
        live_0 = threadBestBits_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 813
    }
    else
    {

#line 813
        live_0 = false;

#line 813
    }

#line 813
    if(live_0)
    {

#line 813
        winner_0 = threadBestSlot_0;

#line 813
    }
    else
    {

#line 813
        winner_0 = 4294967295U;

#line 813
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S42 = simd_is_first();

#line 818
    if(_S42)
    {

#line 818
        live_0 = waveWinner_0 != 4294967295U;

#line 818
    }
    else
    {

#line 818
        live_0 = false;

#line 818
    }

#line 818
    if(live_0)
    {

#line 819
        uint _S43 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 818
    }

#line 823
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(threadBestSlot_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
    {

#line 825
        live_0 = threadBestSlot_0 != 4294967295U;

#line 825
    }
    else
    {

#line 825
        live_0 = false;

#line 825
    }

#line 825
    if(live_0)
    {

#line 826
        *(peakIdx_0+pair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 826
        *(peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 825
    }



    if(_S34)
    {

#line 829
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 829
    }
    else
    {

#line 829
        live_0 = false;

#line 829
    }

#line 829
    if(live_0)
    {

#line 830
        *(peakIdx_0+pair_0) = int(-1);

#line 830
        *(peakVal_0+pair_0) = packed_float2(_S35) ;

#line 829
    }

#line 962
    return;
}


#line 1417
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1417
    thread KernelContext_0 kernelContext_5;

#line 1417
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1417
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1417
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1417
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1417
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1417
    (&kernelContext_5)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1417
    threadgroup array<uint, int(4096)> stg_1;

#line 1417
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1426
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1432
    (&kernelContext_5)->_stgBase_0 = 0U;
    thread uint ws_0 = entryPointParams_1->winStart_1;

#line 1433
    thread uint we_0 = entryPointParams_1->winEnd_1;
    uint _S44 = pair_1 / entryPointParams_1->ntmpl_0;

#line 1434
    rowWindow_0(_S44, &ws_0, &we_0);

#line 1434
    filterPair_0(pair_1, lid_0.x, (&kernelContext_5)->entryPointParams_data_0, (&kernelContext_5)->entryPointParams_tmpl_0, (&kernelContext_5)->entryPointParams_peakIdx_0, (&kernelContext_5)->entryPointParams_peakVal_0, entryPointParams_1->ntmpl_0, ws_0, we_0, (&kernelContext_5)->entryPointParams_0->binsize_0, (&kernelContext_5)->entryPointParams_0->binShift_0, (&kernelContext_5)->entryPointParams_0->nbins_0, (&kernelContext_5)->entryPointParams_0->thrBits_0, &kernelContext_5);


    return;
}
