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


#line 180 "mm_128_fusedTierB_c16.slang"
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


#line 457
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 459
    half2 t1_0 = *a_1 - *c_0;

#line 459
    half2 t2_0 = *b_3 + *d_1;

#line 459
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 461
    *b_3 = t1_0 + j3_0;

#line 461
    *c_0 = t0_0 - t2_0;

#line 461
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


#line 493
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125, 0.382568359375);
    half2 W2_0 = half2(0.70703125, 0.70703125);
    half2 W3_0 = half2(0.382568359375, 0.923828125);
    half2 W4_0 = half2(0.0, 1.0);
    half2 W6_0 = half2(-0.70703125, 0.70703125);
    half2 W9_0 = half2(-0.923828125, -0.382568359375);

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

    half2 t_0 = (*r_0)[int(1)];

#line 507
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 507
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 508
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 508
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 509
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 509
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 510
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 510
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 511
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 511
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

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


#line 253 "mm_128_fusedTierB_c16.slang"
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


#line 229 "mm_128_fusedTierB_c16.slang"
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


#line 653
void exchange_0(array<half2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 654
    uint j_1;

#line 665
    thread array<half2, int(16)> out_0;

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
        out_0[z_0] = half2(0.0, 0.0);

#line 666
        z_0 = z_0 + 1U;

#line 666
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S13 = p0_0 & lenMask_0;

#line 672
    uint _S14 = (_S13 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

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
        uint d_3 = 0U;
        for(;;)
        {

#line 678
            if(d_3 < 16U)
            {
            }
            else
            {

#line 678
                break;
            }

#line 679
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S15 = pz_0 & lenMask_0;
            uint az_0 = (_S15 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 681
            half2 _S16 = stgGet_0(_S14 + az_0 - c_1 * 16U * 8U, kernelContext_2);


            out_0[d_3] = _S16;

#line 678
            d_3 = d_3 + 1U;

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
void dft8_0(array<half2, int(16)> thread* r_2, uint o_0)
{


    thread array<half2, int(8)> b_5;

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


            uint _S17 = o_0 + j_2;

#line 487
            half2 t_6 = cmul_0(half2(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0))), (*r_2)[_S17 + 4U]);
            uint _S18 = ((j_2 - k_0) << 1U) + k_0;

#line 488
            b_5[_S18] = (*r_2)[_S17] + t_6;

#line 488
            b_5[_S18 + s_0] = (*r_2)[_S17] - t_6;

#line 483
            j_2 = j_2 + 1U;

#line 483
        }

#line 483
        uint i_4 = 0U;

#line 490
        for(;;)
        {

#line 490
            if(i_4 < 8U)
            {
            }
            else
            {

#line 490
                break;
            }

#line 490
            (*r_2)[o_0 + i_4] = b_5[i_4];

#line 490
            i_4 = i_4 + 1U;

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
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 596
    uint b_6 = 0U;

#line 604
    for(;;)
    {

#line 604
        if(b_6 < 2U)
        {
        }
        else
        {

#line 604
            break;
        }

#line 604
        dft8_0(r_3, b_6 * 8U);

#line 604
        b_6 = b_6 + 1U;

#line 604
    }



    return;
}


#line 743
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
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
                float _S19 = tw_0.x;

#line 27
                float _S20 = tw_0.y;

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
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], half2(half(cr_0), half(ci_0)));
                    float nr_0 = cr_0 * _S19 - ci_0 * _S20;
                    float _S21 = cr_0 * _S20 + ci_0 * _S19;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S21;

#line 29
                }

#line 37
                uint per_2 = 16U / max(8U, 1U);
                uint _S22 = max(0U, 1U);
                uint blk2_2 = tid_0 / _S22;

#line 39
                uint lane2_2 = tid_0 % _S22;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 8U, 128U, blk_2, lane_2, per_2, _S22, 8U, blk2_2, lane2_2, kernelContext_3);

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

#line 746 "mm_128_fusedTierB_c16.slang"
    return;
}


#line 292
float pairSum_0(uint tid_1, float v_1, KernelContext_0 thread* kernelContext_4)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_1] = (as_type<uint>((v_1)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 296
    uint k_1 = 0U;

#line 296
    float t_7 = 0.0;

    for(;;)
    {

#line 298
        if(k_1 < 8U)
        {
        }
        else
        {

#line 298
            break;
        }

#line 298
        float t_8 = t_7 + (as_type<float>(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_1])));

#line 298
        k_1 = k_1 + 1U;

#line 298
        t_7 = t_8;

#line 298
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_7;
}


#line 712
uint lgOf_0(uint i_5)
{

#line 712
    uint _S23;

#line 712
    if(i_5 < 1U)
    {

#line 712
        _S23 = 4U;

#line 712
    }
    else
    {

#line 712
        if(i_5 == 1U)
        {

#line 712
            _S23 = 3U;

#line 712
        }
        else
        {

#line 712
            _S23 = 1U;

#line 712
        }

#line 712
    }

#line 712
    return _S23;
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


#line 282
float2 c16Bound_0(float2 v_2, float energy_0)
{

    float m_1 = length(v_2);
    float b_7 = m_1 * 1.00146484375 + 0.0 * sqrt(energy_0);

#line 286
    float2 _S24;
    if(m_1 > 0.0)
    {

#line 287
        _S24 = v_2 * float2((b_7 / m_1)) ;

#line 287
    }
    else
    {

#line 287
        _S24 = float2(b_7, 0.0);

#line 287
    }

#line 287
    return _S24;
}


#line 752
void filterOne_0(uint pair_0, uint d_4, uint t_9, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{


    bool live_0;

#line 775
    thread array<half2, int(16)> r_5;

#line 775
    uint n2_0 = 0U;



    for(;;)
    {

#line 779
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 779
            break;
        }

#line 780
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_9 * 128U + tid_2 + 8U * n2_0));

#line 779
        n2_0 = n2_0 + 1U;

#line 779
    }

#line 779
    transform_0(&r_5, tid_2, kernelContext_5);

#line 779
    uint i_6 = 0U;

#line 779
    float energy_1 = 0.0;

#line 809
    for(;;)
    {

#line 809
        if(i_6 < 16U)
        {
        }
        else
        {

#line 809
            break;
        }

#line 810
        float _ex_0 = float(r_5[i_6].x);

#line 810
        float _ey_0 = float(r_5[i_6].y);
        float energy_2 = energy_1 + (_ex_0 * _ex_0 + _ey_0 * _ey_0);

#line 809
        i_6 = i_6 + 1U;

#line 809
        energy_1 = energy_2;

#line 809
    }

#line 809
    float _S25 = pairSum_0(tid_2, energy_1, kernelContext_5);



    float _S26 = _S25 / 128.0;

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 887
    bool _S27 = tid_2 == 0U;

#line 887
    if(_S27)
    {

#line 887
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 887
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 887
    }

#line 892
    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;

#line 894
    i_6 = 0U;

    for(;;)
    {

#line 896
        if(i_6 < 16U)
        {
        }
        else
        {

#line 896
            break;
        }

#line 897
        uint idx_0 = slotToIndex_0(tid_2 * 16U + i_6);
        if(idx_0 >= winStart_2)
        {

#line 898
            live_0 = idx_0 < winEnd_2;

#line 898
        }
        else
        {

#line 898
            live_0 = false;

#line 898
        }



        float _rx_0 = float(r_5[i_6].x);

#line 902
        float _ry_0 = float(r_5[i_6].y);
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
        myMag_0[i_6] = n2_0;

#line 896
        i_6 = i_6 + 1U;

#line 896
    }

#line 896
    uint bestBits_0 = thrBits_1;

#line 896
    i_6 = 0U;

#line 931
    for(;;)
    {

#line 931
        if(i_6 < 16U)
        {
        }
        else
        {

#line 931
            break;
        }

#line 931
        uint _S28 = max(bestBits_0, myMag_0[i_6]);

#line 931
        uint i_7 = i_6 + 1U;

#line 931
        bestBits_0 = _S28;

#line 931
        i_6 = i_7;

#line 931
    }

    uint wm_0 = simd_max(bestBits_0);
    bool _S29 = simd_is_first();

#line 934
    if(_S29)
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
        uint _S30 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), wm_0, memory_order_relaxed);

#line 934
    }

#line 949
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 949
    uint winner_0 = 4294967295U;

#line 949
    i_6 = 0U;

#line 959
    for(;;)
    {

#line 959
        if(i_6 < 16U)
        {
        }
        else
        {

#line 959
            break;
        }

#line 960
        if((myMag_0[i_6]) > thrBits_1)
        {

#line 960
            live_0 = (myMag_0[i_6]) == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

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
            winner_0 = min(winner_0, tid_2 * 16U + i_6);

#line 960
        }

#line 959
        i_6 = i_6 + 1U;

#line 959
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S31 = simd_is_first();

#line 964
    if(_S31)
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
        uint _S32 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 964
    }

#line 969
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 969
    i_6 = 0U;
    for(;;)
    {

#line 970
        if(i_6 < 16U)
        {
        }
        else
        {

#line 970
            break;
        }

#line 971
        uint _S33 = tid_2 * 16U + i_6;

#line 971
        if(_S33 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])
        {

#line 972
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S33));

#line 972
            *(peakVal_0+pair_0) = packed_float2(c16Bound_0(float2(float(r_5[i_6].x), float(r_5[i_6].y)), _S26)) ;

#line 971
        }

#line 970
        i_6 = i_6 + 1U;

#line 970
    }

#line 980
    if(_S27)
    {

#line 980
        live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U]) == 4294967295U;

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

#line 1014
    return;
}


#line 1284
void filterPair_0(uint pair_1, uint tid_3, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{

#line 1284
    thread uint _S34 = winStart_3;

#line 1284
    thread uint _S35 = winEnd_3;

#line 1290
    kernelContext_6->_tid_0 = tid_3;

#line 1319
    uint d_5 = pair_1 / ntmpl_1;

#line 1319
    uint _S36 = pair_1 % ntmpl_1;

#line 1324
    rowWindow_0(d_5, &_S34, &_S35);


    thread array<half2, int(16)> dreg_1;

#line 1327
    uint n2_1 = 0U;

    for(;;)
    {

#line 1329
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1329
            break;
        }

#line 1330
        dreg_1[n2_1] = dload_0(data_1, d_5 * 128U + tid_3 + 8U * n2_1);

#line 1329
        n2_1 = n2_1 + 1U;

#line 1329
    }

#line 1329
    uint k_2 = 0U;

#line 1349
    for(;;)
    {

#line 1349
        if(k_2 < 1U)
        {
        }
        else
        {

#line 1349
            break;
        }

#line 1350
        uint _S37 = pair_1 + k_2;

#line 1350
        uint _S38 = _S36 + k_2;

#line 1350
        thread array<half2, int(16)> _S39 = dreg_1;

#line 1350
        filterOne_0(_S37, d_5, _S38, tid_3, &_S39, data_1, tmpl_1, peakIdx_1, peakVal_1, _S34, _S35, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1349
        k_2 = k_2 + 1U;

#line 1349
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1357
    thread KernelContext_0 kernelContext_7;

#line 1357
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1357
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1357
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1357
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1357
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1357
    threadgroup array<uint, int(128)> stg_1;

#line 1357
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1374
    uint _pr_0 = gid_0.x;

#line 1374
    uint _t_0 = lid_0.x;
    (&kernelContext_7)->_stgBase_0 = 0U;

#line 1375
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);

#line 1383
    return;
}
