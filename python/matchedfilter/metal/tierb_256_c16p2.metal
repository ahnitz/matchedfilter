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


#line 180 "mm_256_fusedTierB_c16p2.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 180
    return;
}


#line 148
half2 cload_0(uint device* b_0, uint i_0)
{

#line 149
    uint p_0 = b_0[i_0];

#line 149
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 186
half2 dload_0(uint device* b_1, uint i_1)
{


    return cload_0(b_1, i_1);
}


#line 252
half2 cmulConj_0(half2 a_0, half2 b_2)
{

#line 252
    half _S2 = a_0.x;

#line 252
    half _S3 = b_2.x;

#line 252
    half _S4 = a_0.y;

#line 252
    half _S5 = b_2.y;

#line 252
    return half2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 419
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 421
    half2 t1_0 = *a_1 - *c_0;

#line 421
    half2 t2_0 = *b_3 + *d_1;

#line 421
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 423
    *b_3 = t1_0 + j3_0;

#line 423
    *c_0 = t0_0 - t2_0;

#line 423
    *d_1 = t1_0 - j3_0;
    return;
}


#line 251
half2 cmul_0(half2 a_2, half2 b_4)
{

#line 251
    half _S6 = a_2.x;

#line 251
    half _S7 = b_4.x;

#line 251
    half _S8 = a_2.y;

#line 251
    half _S9 = b_4.y;

#line 251
    return half2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 455
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125, 0.382568359375);
    half2 W2_0 = half2(0.70703125, 0.70703125);
    half2 W3_0 = half2(0.382568359375, 0.923828125);
    half2 W4_0 = half2(0.0, 1.0);
    half2 W6_0 = half2(-0.70703125, 0.70703125);
    half2 W9_0 = half2(-0.923828125, -0.382568359375);

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

    half2 t_0 = (*r_0)[int(1)];

#line 469
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 469
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 470
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 470
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 471
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 471
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 472
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 472
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 473
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 473
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 474
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 474
    (*r_0)[int(14)] = t_5;
    return;
}


#line 455
void dft16_1(array<half2, int(16)> thread* r_1)
{
    half2 W1_1 = half2(0.923828125, 0.382568359375);
    half2 W2_1 = half2(0.70703125, 0.70703125);
    half2 W3_1 = half2(0.382568359375, 0.923828125);
    half2 W4_1 = half2(0.0, 1.0);
    half2 W6_1 = half2(-0.70703125, 0.70703125);
    half2 W9_1 = half2(-0.923828125, -0.382568359375);

#line 462
    uint n1_1 = 0U;
    for(;;)
    {

#line 463
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 463
            break;
        }

#line 463
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 463
        n1_1 = n1_1 + 1U;

#line 463
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 464
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 464
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 465
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 465
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 466
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 466
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 466
    uint k2_1 = 0U;
    for(;;)
    {

#line 467
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 467
            break;
        }

#line 467
        uint _S11 = 4U * k2_1;

#line 467
        r4_0(&(*r_1)[_S11], &(*r_1)[_S11 + 1U], &(*r_1)[_S11 + 2U], &(*r_1)[_S11 + 3U]);

#line 467
        k2_1 = k2_1 + 1U;

#line 467
    }

    half2 t_6 = (*r_1)[int(1)];

#line 469
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 469
    (*r_1)[int(4)] = t_6;
    half2 t_7 = (*r_1)[int(2)];

#line 470
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 470
    (*r_1)[int(8)] = t_7;
    half2 t_8 = (*r_1)[int(3)];

#line 471
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 471
    (*r_1)[int(12)] = t_8;
    half2 t_9 = (*r_1)[int(6)];

#line 472
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 472
    (*r_1)[int(9)] = t_9;
    half2 t_10 = (*r_1)[int(7)];

#line 473
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 473
    (*r_1)[int(13)] = t_10;
    half2 t_11 = (*r_1)[int(11)];

#line 474
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 474
    (*r_1)[int(14)] = t_11;
    return;
}


#line 22 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 253 "mm_256_fusedTierB_c16p2.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 255
    uint j_0 = d_2 / _S12;

#line 255
    uint m_0 = d_2 % _S12;

#line 255
    uint _S13;
    if(TB_0 <= 16U)
    {

#line 256
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 256
    }
    else
    {

#line 256
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 256
    }

#line 256
    return _S13;
}


#line 90 "core"
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


#line 229 "mm_256_fusedTierB_c16p2.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(512)> threadgroup* stg_0;
};


#line 229
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 229
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 229
    return;
}


#line 230
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 230
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 615
void exchange_0(array<half2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 616
    uint j_1;

#line 627
    thread array<half2, int(16)> out_0;

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
        out_0[z_0] = half2(0.0, 0.0);

#line 628
        z_0 = z_0 + 1U;

#line 628
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S14 = p0_0 & lenMask_0;

#line 634
    uint _S15 = (_S14 >> lgSpan_0) * 16U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);

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
            stgPut_0(j_1 * 16U + kernelContext_2->_tid_0, (*r_2)[c_1 * 16U + j_1], kernelContext_2);

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
            uint _S16 = pz_0 & lenMask_0;
            uint az_0 = (_S16 >> lgSpan_0) * 16U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 643
            half2 _S17 = stgGet_0(_S15 + az_0 - c_1 * 16U * 16U, kernelContext_2);


            out_0[d_3] = _S17;

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
        (*r_2)[j_1] = out_0[j_1];

#line 649
        j_1 = j_1 + 1U;

#line 649
    }
    return;
}


#line 558
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 565
    dft16_1(r_3);

#line 570
    return;
}


#line 705
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 705
    for(;;)
    {

#line 705
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(16U);
                uint lgLn_0 = firstbithigh_0(256U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 15U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 256.0);
                float _S18 = tw_0.x;

#line 27
                float _S19 = tw_0.y;

#line 27
                uint k2_2 = 0U;

#line 27
                float cr_0 = 1.0;

#line 27
                float ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], half2(half(cr_0), half(ci_0)));
                    float nr_0 = cr_0 * _S18 - ci_0 * _S19;
                    float _S20 = cr_0 * _S19 + ci_0 * _S18;

#line 29
                    k2_2 = k2_2 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S20;

#line 29
                }

#line 37
                uint per_2 = 16U / max(16U, 1U);
                uint _S21 = max(1U, 1U);
                uint blk2_2 = tid_0 / _S21;

#line 39
                uint lane2_2 = tid_0 % _S21;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 16U, 256U, blk_2, lane_2, per_2, _S21, 16U, blk2_2, lane2_2, kernelContext_3);

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

#line 708 "mm_256_fusedTierB_c16p2.slang"
    return;
}


#line 674
uint lgOf_0(uint i_4)
{

#line 674
    uint _S22;

#line 674
    if(i_4 < 1U)
    {

#line 674
        _S22 = 4U;

#line 674
    }
    else
    {

#line 674
        if(i_4 == 1U)
        {

#line 674
            _S22 = 4U;

#line 674
        }
        else
        {

#line 674
            _S22 = 1U;

#line 674
        }

#line 674
    }

#line 674
    return _S22;
}


#line 676
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 680
    uint lg_1 = lgOf_0(0U);

#line 685
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 714
void filterOne_0(uint pair_0, uint d_4, uint t_12, uint tid_1, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{


    bool live_0;

#line 737
    thread array<half2, int(16)> r_5;

#line 737
    uint n2_0 = 0U;



    for(;;)
    {

#line 741
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 741
            break;
        }

#line 742
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_12 * 256U + tid_1 + 16U * n2_0));

#line 741
        n2_0 = n2_0 + 1U;

#line 741
    }

#line 741
    transform_0(&r_5, tid_1, kernelContext_4);

#line 767
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 839
    bool _S23 = tid_1 == 0U;

#line 839
    if(_S23)
    {

#line 839
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 839
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 839
    }

#line 844
    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;

#line 846
    uint i_5 = 0U;

    for(;;)
    {

#line 848
        if(i_5 < 16U)
        {
        }
        else
        {

#line 848
            break;
        }

#line 849
        uint idx_0 = slotToIndex_0(tid_1 * 16U + i_5);
        if(idx_0 >= winStart_2)
        {

#line 850
            live_0 = idx_0 < winEnd_2;

#line 850
        }
        else
        {

#line 850
            live_0 = false;

#line 850
        }



        float _rx_0 = float(r_5[i_5].x);

#line 854
        float _ry_0 = float(r_5[i_5].y);
        if(live_0)
        {

#line 855
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 855
        }
        else
        {

#line 855
            n2_0 = 0U;

#line 855
        }

#line 855
        myMag_0[i_5] = n2_0;

#line 848
        i_5 = i_5 + 1U;

#line 848
    }

#line 848
    uint bestBits_0 = thrBits_1;

#line 848
    i_5 = 0U;

#line 883
    for(;;)
    {

#line 883
        if(i_5 < 16U)
        {
        }
        else
        {

#line 883
            break;
        }

#line 883
        uint _S24 = max(bestBits_0, myMag_0[i_5]);

#line 883
        uint i_6 = i_5 + 1U;

#line 883
        bestBits_0 = _S24;

#line 883
        i_5 = i_6;

#line 883
    }

#line 898
    if(bestBits_0 > thrBits_1)
    {

#line 898
        uint _S25 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), bestBits_0, memory_order_relaxed);

#line 898
    }


    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 901
    uint winner_0 = 4294967295U;

#line 901
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
            live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 912
        }
        else
        {

#line 912
            live_0 = false;

#line 912
        }

#line 912
        if(live_0)
        {

#line 912
            winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 912
        }

#line 911
        i_5 = i_5 + 1U;

#line 911
    }

#line 919
    if(winner_0 != 4294967295U)
    {

#line 919
        uint _S26 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 919
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 921
    i_5 = 0U;
    for(;;)
    {

#line 922
        if(i_5 < 16U)
        {
        }
        else
        {

#line 922
            break;
        }

#line 923
        uint _S27 = tid_1 * 16U + i_5;

#line 923
        if(_S27 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
        {

#line 924
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S27));

#line 924
            *(peakVal_0+pair_0) = packed_float2(float2(float(r_5[i_5].x), float(r_5[i_5].y))) ;

#line 923
        }

#line 922
        i_5 = i_5 + 1U;

#line 922
    }

#line 928
    if(_S23)
    {

#line 928
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 928
    }
    else
    {

#line 928
        live_0 = false;

#line 928
    }

#line 928
    if(live_0)
    {

#line 929
        *(peakIdx_0+pair_0) = int(-1);

#line 929
        *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 928
    }

#line 962
    return;
}


#line 1213
void filterPair_0(uint pair_1, uint tid_2, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_5)
{

#line 1213
    thread uint _S28 = winStart_3;

#line 1213
    thread uint _S29 = winEnd_3;

#line 1219
    kernelContext_5->_tid_0 = tid_2;

#line 1248
    uint d_5 = pair_1 / ntmpl_1;

#line 1248
    uint _S30 = pair_1 % ntmpl_1;

#line 1253
    rowWindow_0(d_5, &_S28, &_S29);


    thread array<half2, int(16)> dreg_1;

#line 1256
    uint n2_1 = 0U;

    for(;;)
    {

#line 1258
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1258
            break;
        }

#line 1259
        dreg_1[n2_1] = dload_0(data_1, d_5 * 256U + tid_2 + 16U * n2_1);

#line 1258
        n2_1 = n2_1 + 1U;

#line 1258
    }

#line 1258
    uint k_0 = 0U;

#line 1278
    for(;;)
    {

#line 1278
        if(k_0 < 1U)
        {
        }
        else
        {

#line 1278
            break;
        }

#line 1279
        uint _S31 = pair_1 + k_0;

#line 1279
        uint _S32 = _S30 + k_0;

#line 1279
        thread array<half2, int(16)> _S33 = dreg_1;

#line 1279
        filterOne_0(_S31, d_5, _S32, tid_2, &_S33, data_1, tmpl_1, peakIdx_1, peakVal_1, _S28, _S29, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_5);

#line 1278
        k_0 = k_0 + 1U;

#line 1278
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1286
    thread KernelContext_0 kernelContext_6;

#line 1286
    (&kernelContext_6)->entryPointParams_0 = entryPointParams_1;

#line 1286
    (&kernelContext_6)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1286
    (&kernelContext_6)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1286
    (&kernelContext_6)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1286
    (&kernelContext_6)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1286
    threadgroup array<uint, int(512)> stg_1;

#line 1286
    (&kernelContext_6)->stg_0 = &stg_1;

#line 1306
    uint _S34 = lid_0.x;

#line 1306
    uint _sub_0 = _S34 / 16U;
    uint _pr_0 = gid_0.x * 2U + _sub_0;

#line 1307
    uint _t_0 = _S34 % 16U;
    (&kernelContext_6)->_stgBase_0 = _sub_0 * 256U;

#line 1308
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_6);



    return;
}
