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


#line 148 "mm_2048_fusedTierB_c16.slang"
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
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_0)
{
    half2 t0_0 = *a_1 + *c_0;

#line 421
    half2 t1_0 = *a_1 - *c_0;

#line 421
    half2 t2_0 = *b_3 + *d_0;

#line 421
    half2 t3_0 = *b_3 - *d_0;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 423
    *b_3 = t1_0 + j3_0;

#line 423
    *c_0 = t0_0 - t2_0;

#line 423
    *d_0 = t1_0 - j3_0;
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


#line 22 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 253 "mm_2048_fusedTierB_c16.slang"
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


#line 229 "mm_2048_fusedTierB_c16.slang"
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
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
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
    uint _S13 = p0_0 & lenMask_0;

#line 634
    uint _S14 = (_S13 >> lgSpan_0) * 128U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

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
        uint d_2 = 0U;
        for(;;)
        {

#line 640
            if(d_2 < 16U)
            {
            }
            else
            {

#line 640
                break;
            }

#line 641
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S15 = pz_0 & lenMask_0;
            uint az_0 = (_S15 >> lgSpan_0) * 128U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 643
            half2 _S16 = stgGet_0(_S14 + az_0 - c_1 * 16U * 128U, kernelContext_2);


            out_0[d_2] = _S16;

#line 640
            d_2 = d_2 + 1U;

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
void dft8_0(array<half2, int(16)> thread* r_2, uint o_0)
{


    thread array<half2, int(8)> b_5;

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


            uint _S17 = o_0 + j_2;

#line 449
            half2 t_6 = cmul_0(half2(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0))), (*r_2)[_S17 + 4U]);
            uint _S18 = ((j_2 - k_0) << 1U) + k_0;

#line 450
            b_5[_S18] = (*r_2)[_S17] + t_6;

#line 450
            b_5[_S18 + s_0] = (*r_2)[_S17] - t_6;

#line 445
            j_2 = j_2 + 1U;

#line 445
        }

#line 445
        uint i_4 = 0U;

#line 452
        for(;;)
        {

#line 452
            if(i_4 < 8U)
            {
            }
            else
            {

#line 452
                break;
            }

#line 452
            (*r_2)[o_0 + i_4] = b_5[i_4];

#line 452
            i_4 = i_4 + 1U;

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
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 558
    uint b_6 = 0U;

#line 566
    for(;;)
    {

#line 566
        if(b_6 < 2U)
        {
        }
        else
        {

#line 566
            break;
        }

#line 566
        dft8_0(r_3, b_6 * 8U);

#line 566
        b_6 = b_6 + 1U;

#line 566
    }



    return;
}


#line 705
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 705
    uint _S19;

#line 705
    uint k2_1;

#line 705
    float cr_0;

#line 705
    float ci_0;

#line 705
    uint _S20;

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
                _S19 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(2048U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 127U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 2048.0);
                float _S21 = tw_0.x;

#line 27
                float _S22 = tw_0.y;

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
                uint per_2 = 16U / max(128U, 1U);
                uint _S24 = max(8U, 1U);

#line 38
                _S20 = _S24;
                uint blk2_2 = tid_0 / _S24;

#line 39
                uint lane2_2 = tid_0 % _S24;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 128U, 2048U, blk_2, lane_2, per_2, _S24, 128U, blk2_2, lane2_2, kernelContext_3);

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
                float _S25 = tw_1.x;

#line 27
                float _S26 = tw_1.y;

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
                    float nr_1 = cr_0 * _S25 - ci_0 * _S26;
                    float _S27 = cr_0 * _S26 + ci_0 * _S25;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S27;

#line 29
                }

#line 37
                uint per_3 = 16U / _S20;
                uint _S28 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S28;

#line 39
                uint lane2_3 = tid_0 % _S28;

#line 39
                exchange_0(r_4, _S19, lgTB_1, 8U, 128U, blk_3, lane_3, per_3, _S28, 8U, blk2_3, lane2_3, kernelContext_3);

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

#line 708 "mm_2048_fusedTierB_c16.slang"
    return;
}


#line 674
uint lgOf_0(uint i_5)
{

#line 674
    uint _S29;

#line 674
    if(i_5 < 2U)
    {

#line 674
        _S29 = 4U;

#line 674
    }
    else
    {

#line 674
        if(i_5 == 2U)
        {

#line 674
            _S29 = 3U;

#line 674
        }
        else
        {

#line 674
            _S29 = 1U;

#line 674
        }

#line 674
    }

#line 674
    return _S29;
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


#line 714
void filterOne_0(uint pair_0, uint d_3, uint t_7, uint tid_1, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
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
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_7 * 2048U + tid_1 + 128U * n2_0));

#line 741
        n2_0 = n2_0 + 1U;

#line 741
    }

#line 741
    transform_0(&r_5, tid_1, kernelContext_4);

#line 767
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 839
    bool _S30 = tid_1 == 0U;

#line 839
    if(_S30)
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
    uint i_6 = 0U;

    for(;;)
    {

#line 848
        if(i_6 < 16U)
        {
        }
        else
        {

#line 848
            break;
        }

#line 849
        uint idx_0 = slotToIndex_0(tid_1 * 16U + i_6);
        if(idx_0 >= winStart_1)
        {

#line 850
            live_0 = idx_0 < winEnd_1;

#line 850
        }
        else
        {

#line 850
            live_0 = false;

#line 850
        }



        float _rx_0 = float(r_5[i_6].x);

#line 854
        float _ry_0 = float(r_5[i_6].y);
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
        myMag_0[i_6] = n2_0;

#line 848
        i_6 = i_6 + 1U;

#line 848
    }

#line 848
    uint bestBits_0 = thrBits_1;

#line 848
    i_6 = 0U;

#line 883
    for(;;)
    {

#line 883
        if(i_6 < 16U)
        {
        }
        else
        {

#line 883
            break;
        }

#line 883
        uint _S31 = max(bestBits_0, myMag_0[i_6]);

#line 883
        uint i_7 = i_6 + 1U;

#line 883
        bestBits_0 = _S31;

#line 883
        i_6 = i_7;

#line 883
    }

    uint wm_0 = simd_max(bestBits_0);
    bool _S32 = simd_is_first();

#line 886
    if(_S32)
    {

#line 886
        live_0 = wm_0 > thrBits_1;

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
        uint _S33 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 886
    }

#line 901
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 901
    uint winner_0 = 4294967295U;

#line 901
    i_6 = 0U;

#line 911
    for(;;)
    {

#line 911
        if(i_6 < 16U)
        {
        }
        else
        {

#line 911
            break;
        }

#line 912
        if((myMag_0[i_6]) > thrBits_1)
        {

#line 912
            live_0 = (myMag_0[i_6]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

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
            winner_0 = min(winner_0, tid_1 * 16U + i_6);

#line 912
        }

#line 911
        i_6 = i_6 + 1U;

#line 911
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S34 = simd_is_first();

#line 916
    if(_S34)
    {

#line 916
        live_0 = waveWinner_0 != 4294967295U;

#line 916
    }
    else
    {

#line 916
        live_0 = false;

#line 916
    }

#line 916
    if(live_0)
    {

#line 917
        uint _S35 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 916
    }

#line 921
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 921
    i_6 = 0U;
    for(;;)
    {

#line 922
        if(i_6 < 16U)
        {
        }
        else
        {

#line 922
            break;
        }

#line 923
        uint _S36 = tid_1 * 16U + i_6;

#line 923
        if(_S36 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
        {

#line 924
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S36));

#line 924
            *(peakVal_0+pair_0) = packed_float2(float2(float(r_5[i_6].x), float(r_5[i_6].y))) ;

#line 923
        }

#line 922
        i_6 = i_6 + 1U;

#line 922
    }

#line 928
    if(_S30)
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


#line 1187
void filterPair_0(uint pair_1, uint tid_2, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_5)
{

#line 1193
    kernelContext_5->_tid_0 = tid_2;

#line 1222
    uint _S37 = pair_1 / ntmpl_1;

#line 1222
    uint _S38 = pair_1 % ntmpl_1;

    thread array<half2, int(16)> dreg_1;

#line 1224
    uint n2_1 = 0U;

    for(;;)
    {

#line 1226
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1226
            break;
        }

#line 1227
        dreg_1[n2_1] = dload_0(data_1, _S37 * 2048U + tid_2 + 128U * n2_1);

#line 1226
        n2_1 = n2_1 + 1U;

#line 1226
    }

#line 1226
    uint k_1 = 0U;

#line 1246
    for(;;)
    {

#line 1246
        if(k_1 < 1U)
        {
        }
        else
        {

#line 1246
            break;
        }

#line 1247
        uint _S39 = pair_1 + k_1;

#line 1247
        uint _S40 = _S38 + k_1;

#line 1247
        thread array<half2, int(16)> _S41 = dreg_1;

#line 1247
        filterOne_0(_S39, _S37, _S40, tid_2, &_S41, data_1, tmpl_1, peakIdx_1, peakVal_1, winStart_2, winEnd_2, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_5);

#line 1246
        k_1 = k_1 + 1U;

#line 1246
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1254
    thread KernelContext_0 kernelContext_6;

#line 1254
    (&kernelContext_6)->entryPointParams_0 = entryPointParams_1;

#line 1254
    (&kernelContext_6)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1254
    (&kernelContext_6)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1254
    (&kernelContext_6)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1254
    (&kernelContext_6)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1254
    threadgroup array<uint, int(2048)> stg_1;

#line 1254
    (&kernelContext_6)->stg_0 = &stg_1;

#line 1271
    uint _pr_0 = gid_0.x;

#line 1271
    uint _t_0 = lid_0.x;
    (&kernelContext_6)->_stgBase_0 = 0U;

#line 1272
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_6);

#line 1280
    return;
}
