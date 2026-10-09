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


#line 152 "mm_32768_fusedTierB.slang"
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


#line 22 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 251 "mm_32768_fusedTierB.slang"
float2 cmul_0(float2 a_1, float2 b_2)
{

#line 251
    float _S6 = a_1.x;

#line 251
    float _S7 = b_2.x;

#line 251
    float _S8 = a_1.y;

#line 251
    float _S9 = b_2.y;

#line 251
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 419
void r4_0(float2 thread* a_2, float2 thread* b_3, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_2 + *c_0;

#line 421
    float2 t1_0 = *a_2 - *c_0;

#line 421
    float2 t2_0 = *b_3 + *d_0;

#line 421
    float2 t3_0 = *b_3 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_2 = t0_0 + t2_0;

#line 423
    *b_3 = t1_0 + j3_0;

#line 423
    *c_0 = t0_0 - t2_0;

#line 423
    *d_0 = t1_0 - j3_0;
    return;
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


#line 501
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 503
    thread array<float2, int(16)> v_0;

#line 503
    uint j_0 = 0U;
    for(;;)
    {

#line 504
        if(j_0 < 16U)
        {
        }
        else
        {

#line 504
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        v_0[j_0] = cmul_0((*r_1)[j_0] - (*r_1)[j_0 + 16U], mfTwiddle_0(6.28318548202514648 * float(j_0) / 32.0));

#line 504
        j_0 = j_0 + 1U;

#line 504
    }

#line 510
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 511
    uint k_0 = 0U;
    for(;;)
    {

#line 512
        if(k_0 < 16U)
        {
        }
        else
        {

#line 512
            break;
        }

#line 512
        uint _S11 = 2U * k_0;

#line 512
        (*r_1)[_S11] = u_0[k_0];

#line 512
        (*r_1)[_S11 + 1U] = v_0[k_0];

#line 512
        k_0 = k_0 + 1U;

#line 512
    }
    return;
}


#line 540
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 253
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 255
    uint j_1 = d_1 / _S12;

#line 255
    uint m_0 = d_1 % _S12;

#line 255
    uint _S13;
    if(TB_0 <= 32U)
    {

#line 256
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 256
    }
    else
    {

#line 256
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 256
    }

#line 256
    return _S13;
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


#line 240 "mm_32768_fusedTierB.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(16384)> threadgroup* stg_0;
};


#line 240
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 240
    uint _S14 = 2U * i_1;

#line 240
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14] = (as_type<uint>((v_1.x)));

#line 240
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14 + 1U] = (as_type<uint>((v_1.y)));

#line 240
    return;
}


#line 241
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 241
    uint _S15 = 2U * i_2;

#line 241
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15 + 1U]))));
}


#line 615
void exchange_0(array<float2, int(32)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 616
    uint j_2;

#line 627
    thread array<float2, int(32)> out_0;

#line 627
    uint z_0 = 0U;
    for(;;)
    {

#line 628
        if(z_0 < 32U)
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
    uint _S16 = p0_0 & lenMask_0;

#line 634
    uint _S17 = _S16 >> lgSpan_0;

#line 634
    uint _S18 = _S17 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 634
    uint c_1 = 0U;

    for(;;)
    {

#line 636
        if(c_1 < 4U)
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
        j_2 = 0U;
        for(;;)
        {

#line 638
            if(j_2 < 8U)
            {
            }
            else
            {

#line 638
                break;
            }

#line 638
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 8U + j_2], kernelContext_2);

#line 638
            j_2 = j_2 + 1U;

#line 638
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 639
        uint d_2 = 0U;
        for(;;)
        {

#line 640
            if(d_2 < 32U)
            {
            }
            else
            {

#line 640
                break;
            }

#line 641
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S19 = pz_0 & lenMask_0;

#line 642
            uint iz_0 = _S19 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S19 & spanMask_0);
            uint i_3 = _S17 + iz_0;
            uint _S20 = c_1 * 8U;

#line 645
            bool _S21;

#line 645
            if(i_3 >= _S20)
            {

#line 645
                _S21 = i_3 < ((c_1 + 1U) * 8U);

#line 645
            }
            else
            {

#line 645
                _S21 = false;

#line 645
            }

#line 645
            if(_S21)
            {

#line 645
                float2 _S22 = stgGet_0(_S18 + az_0 - _S20 * 1024U, kernelContext_2);
                out_0[d_2] = _S22;

#line 645
            }

#line 640
            d_2 = d_2 + 1U;

#line 640
        }

#line 636
        c_1 = c_1 + 1U;

#line 636
    }

#line 636
    j_2 = 0U;

#line 649
    for(;;)
    {

#line 649
        if(j_2 < 32U)
        {
        }
        else
        {

#line 649
            break;
        }

#line 649
        (*r_3)[j_2] = out_0[j_2];

#line 649
        j_2 = j_2 + 1U;

#line 649
    }
    return;
}


#line 558
void innermost_0(array<float2, int(32)> thread* r_4)
{

    dft32_0(r_4);

#line 570
    return;
}


#line 705
void transform_0(array<float2, int(32)> thread* r_5, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 705
    uint _S23;

#line 705
    uint k2_1;

#line 705
    float cr_0;

#line 705
    float ci_0;

#line 705
    uint _S24;

#line 705
    for(;;)
    {

#line 705
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S23 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(32768U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;

#line 19
                dftR_0(r_5);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 32768.0);
                float _S25 = tw_0.x;

#line 27
                float _S26 = tw_0.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_1 < 32U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_5)[k2_1] = cmul_0((*r_5)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S25 - ci_0 * _S26;
                    float _S27 = cr_0 * _S26 + ci_0 * _S25;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S27;

#line 29
                }

#line 37
                uint per_2 = 32U / max(1024U, 1U);
                uint _S28 = max(32U, 1U);

#line 38
                _S24 = _S28;
                uint blk2_2 = tid_0 / _S28;

#line 39
                uint lane2_2 = tid_0 % _S28;

#line 39
                exchange_0(r_5, lgLn_0, lgTB_0, 1024U, 32768U, blk_2, lane_2, per_2, _S28, 1024U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(32U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 31U;

#line 19
                dftR_0(r_5);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 1024.0);
                float _S29 = tw_1.x;

#line 27
                float _S30 = tw_1.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_1 < 32U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_5)[k2_1] = cmul_0((*r_5)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S29 - ci_0 * _S30;
                    float _S31 = cr_0 * _S30 + ci_0 * _S29;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S31;

#line 29
                }

#line 37
                uint per_3 = 32U / _S24;
                uint _S32 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S32;

#line 39
                uint lane2_3 = tid_0 % _S32;

#line 39
                exchange_0(r_5, _S23, lgTB_1, 32U, 1024U, blk_3, lane_3, per_3, _S32, 32U, blk2_3, lane2_3, kernelContext_3);

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
    innermost_0(r_5);

#line 708 "mm_32768_fusedTierB.slang"
    return;
}


#line 674
uint lgOf_0(uint i_4)
{

#line 674
    uint _S33;

#line 674
    if(i_4 < 2U)
    {

#line 674
        _S33 = 5U;

#line 674
    }
    else
    {

#line 674
        if(i_4 == 2U)
        {

#line 674
            _S33 = 5U;

#line 674
        }
        else
        {

#line 674
            _S33 = 1U;

#line 674
        }

#line 674
    }

#line 674
    return _S33;
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
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 734
    kernelContext_4->_tid_0 = tid_1;
    uint _S34 = pair_0 / ntmpl_1;

#line 735
    uint _S35 = pair_0 % ntmpl_1;

    thread array<float2, int(32)> r_6;

#line 737
    uint n2_0 = 0U;

#line 748
    for(;;)
    {

#line 748
        if(n2_0 < 32U)
        {
        }
        else
        {

#line 748
            break;
        }

#line 749
        uint idx_0 = tid_1 + 1024U * n2_0;
        r_6[n2_0] = cmulConj_0(cload_0(data_0, _S34 * 32768U + idx_0), cload_0(tmpl_0, _S35 * 32768U + idx_0));

#line 748
        n2_0 = n2_0 + 1U;

#line 748
    }

#line 748
    transform_0(&r_6, tid_1, kernelContext_4);

#line 767
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 767
    uint b_4 = tid_1;

#line 841
    for(;;)
    {

#line 841
        if(b_4 < nbins_1)
        {
        }
        else
        {

#line 841
            break;
        }

#line 841
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4] = thrBits_1;

#line 841
        b_4 = b_4 + 1024U;

#line 841
    }
    bool _S36 = nbins_1 == 1U;

#line 842
    bool live_0;

#line 842
    if(_S36)
    {

#line 842
        live_0 = tid_1 == 0U;

#line 842
    }
    else
    {

#line 842
        live_0 = false;

#line 842
    }

#line 842
    if(live_0)
    {

#line 842
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 842
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(32)> myMag_0;
    thread array<uint, int(32)> myBin_0;

#line 847
    uint i_5 = 0U;
    for(;;)
    {

#line 848
        if(i_5 < 32U)
        {
        }
        else
        {

#line 848
            break;
        }

#line 849
        uint idx_1 = slotToIndex_0(tid_1 * 32U + i_5);
        if(idx_1 >= winStart_1)
        {

#line 850
            live_0 = idx_1 < winEnd_1;

#line 850
        }
        else
        {

#line 850
            live_0 = false;

#line 850
        }



        float _rx_0 = r_6[i_5].x;

#line 854
        float _ry_0 = r_6[i_5].y;
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
        uint off_0 = idx_1 - winStart_1;

#line 863
        if(live_0)
        {

#line 863
            if(binShift_1 >= int(0))
            {

#line 863
                b_4 = off_0 >> uint(binShift_1);

#line 863
            }
            else
            {

#line 863
                uint _S37 = off_0 / binsize_1;

#line 863
                b_4 = _S37;

#line 863
            }

#line 863
        }
        else
        {

#line 863
            b_4 = 0U;

#line 863
        }

#line 863
        myBin_0[i_5] = b_4;

#line 863
        bool _S38;



        if(nbins_1 > 1U)
        {

#line 867
            _S38 = (myMag_0[i_5]) > thrBits_1;

#line 867
        }
        else
        {

#line 867
            _S38 = false;

#line 867
        }

#line 867
        if(_S38)
        {

#line 868
            uint _S39 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), myMag_0[i_5], memory_order_relaxed);

#line 867
        }

#line 848
        i_5 = i_5 + 1U;

#line 848
    }

#line 848
    uint winner_0;

#line 880
    if(_S36)
    {

#line 880
        winner_0 = thrBits_1;

#line 880
        i_5 = 0U;


        for(;;)
        {

#line 883
            if(i_5 < 32U)
            {
            }
            else
            {

#line 883
                break;
            }

#line 883
            uint _S40 = max(winner_0, myMag_0[i_5]);

#line 883
            uint i_6 = i_5 + 1U;

#line 883
            winner_0 = _S40;

#line 883
            i_5 = i_6;

#line 883
        }

        uint wm_0 = simd_max(winner_0);
        bool _S41 = simd_is_first();

#line 886
        if(_S41)
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
            uint _S42 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 886
        }

#line 880
    }

#line 901
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 908
    if(_S36)
    {

#line 908
        winner_0 = 4294967295U;

#line 908
        i_5 = 0U;


        for(;;)
        {

#line 911
            if(i_5 < 32U)
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
                winner_0 = min(winner_0, tid_1 * 32U + i_5);

#line 912
            }

#line 911
            i_5 = i_5 + 1U;

#line 911
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S43 = simd_is_first();

#line 916
        if(_S43)
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
            uint _S44 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 916
        }

#line 921
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 921
        i_5 = 0U;
        for(;;)
        {

#line 922
            if(i_5 < 32U)
            {
            }
            else
            {

#line 922
                break;
            }

#line 923
            uint _S45 = tid_1 * 32U + i_5;

#line 923
            if(_S45 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 924
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S45));

#line 924
                *(peakVal_0+pair_0) = packed_float2(float2(r_6[i_5].x, r_6[i_5].y)) ;

#line 923
            }

#line 922
            i_5 = i_5 + 1U;

#line 922
        }

#line 928
        if(tid_1 == 0U)
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

#line 908
    }
    else
    {

#line 908
        i_5 = 0U;

#line 937
        for(;;)
        {

#line 937
            if(i_5 < 32U)
            {
            }
            else
            {

#line 937
                break;
            }

#line 938
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 938
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]];

#line 938
            }
            else
            {

#line 938
                live_0 = false;

#line 938
            }

#line 938
            myMag_0[i_5] = uint(live_0);

#line 937
            i_5 = i_5 + 1U;

#line 937
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 940
        b_4 = tid_1;
        for(;;)
        {

#line 941
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 941
                break;
            }

#line 941
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4] = 4294967295U;

#line 941
            b_4 = b_4 + 1024U;

#line 941
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 942
        i_5 = 0U;
        for(;;)
        {

#line 943
            if(i_5 < 32U)
            {
            }
            else
            {

#line 943
                break;
            }

#line 944
            if((myMag_0[i_5]) != 0U)
            {

#line 944
                uint _S46 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), tid_1 * 32U + i_5, memory_order_relaxed);

#line 944
            }

#line 943
            i_5 = i_5 + 1U;

#line 943
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 945
        i_5 = 0U;
        for(;;)
        {

#line 946
            if(i_5 < 32U)
            {
            }
            else
            {

#line 946
                break;
            }

#line 947
            if((myMag_0[i_5]) != 0U)
            {

#line 947
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]]) == (tid_1 * 32U + i_5);

#line 947
            }
            else
            {

#line 947
                live_0 = false;

#line 947
            }

#line 947
            if(live_0)
            {

#line 948
                uint o_0 = pair_0 * nbins_1 + myBin_0[i_5];
                *(peakIdx_0+o_0) = int(slotToIndex_0(tid_1 * 32U + i_5));

#line 949
                *(peakVal_0+o_0) = packed_float2(float2(r_6[i_5].x, r_6[i_5].y)) ;

#line 947
            }

#line 946
            i_5 = i_5 + 1U;

#line 946
        }

#line 946
        b_4 = tid_1;

#line 953
        for(;;)
        {

#line 953
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 953
                break;
            }

#line 954
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4]) == 4294967295U)
            {

#line 955
                uint _S47 = pair_0 * nbins_1 + b_4;

#line 955
                *(peakIdx_0+_S47) = int(-1);

#line 955
                *(peakVal_0+_S47) = packed_float2(float2(0.0, 0.0)) ;

#line 954
            }

#line 953
            b_4 = b_4 + 1024U;

#line 953
        }

#line 908
    }

#line 962
    return;
}


#line 1260
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1260
    thread KernelContext_0 kernelContext_5;

#line 1260
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1260
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1260
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1260
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1260
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1260
    threadgroup array<uint, int(16384)> stg_1;

#line 1260
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1277
    uint _pr_0 = gid_0.x;

#line 1277
    uint _t_0 = lid_0.x;
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 1278
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);

#line 1286
    return;
}
