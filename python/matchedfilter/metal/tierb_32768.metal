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


#line 168 "mm_32768_fusedTierB.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 168
    return float2(*(b_0+i_0)) ;
}


#line 268
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 268
    float _S2 = a_0.x;

#line 268
    float _S3 = b_1.x;

#line 268
    float _S4 = a_0.y;

#line 268
    float _S5 = b_1.y;

#line 268
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 64 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 267 "mm_32768_fusedTierB.slang"
float2 cmul_0(float2 a_1, float2 b_2)
{

#line 267
    float _S6 = a_1.x;

#line 267
    float _S7 = b_2.x;

#line 267
    float _S8 = a_1.y;

#line 267
    float _S9 = b_2.y;

#line 267
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 473
void r4_0(float2 thread* a_2, float2 thread* b_3, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_2 + *c_0;

#line 475
    float2 t1_0 = *a_2 - *c_0;

#line 475
    float2 t2_0 = *b_3 + *d_0;

#line 475
    float2 t3_0 = *b_3 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_2 = t0_0 + t2_0;

#line 477
    *b_3 = t1_0 + j3_0;

#line 477
    *c_0 = t0_0 - t2_0;

#line 477
    *d_0 = t1_0 - j3_0;
    return;
}


#line 509
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 516
    uint n1_0 = 0U;
    for(;;)
    {

#line 517
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 517
            break;
        }

#line 517
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 517
        n1_0 = n1_0 + 1U;

#line 517
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 518
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 518
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 519
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 519
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 520
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 520
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 520
    uint k2_0 = 0U;
    for(;;)
    {

#line 521
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 521
            break;
        }

#line 521
        uint _S10 = 4U * k2_0;

#line 521
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 521
        k2_0 = k2_0 + 1U;

#line 521
    }

    float2 t_0 = (*r_0)[int(1)];

#line 523
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 523
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 524
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 524
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 525
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 525
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 526
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 526
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 527
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 527
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 528
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 528
    (*r_0)[int(14)] = t_5;
    return;
}


#line 555
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 557
    thread array<float2, int(16)> v_0;

#line 557
    uint j_0 = 0U;
    for(;;)
    {

#line 558
        if(j_0 < 16U)
        {
        }
        else
        {

#line 558
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        v_0[j_0] = cmul_0((*r_1)[j_0] - (*r_1)[j_0 + 16U], mfTwiddle_0(6.28318548202514648 * float(j_0) / 32.0));

#line 558
        j_0 = j_0 + 1U;

#line 558
    }

#line 564
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 565
    uint k_0 = 0U;
    for(;;)
    {

#line 566
        if(k_0 < 16U)
        {
        }
        else
        {

#line 566
            break;
        }

#line 566
        uint _S11 = 2U * k_0;

#line 566
        (*r_1)[_S11] = u_0[k_0];

#line 566
        (*r_1)[_S11 + 1U] = v_0[k_0];

#line 566
        k_0 = k_0 + 1U;

#line 566
    }
    return;
}


#line 594
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 269
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 271
    uint j_1 = d_1 / _S12;

#line 271
    uint m_0 = d_1 % _S12;

#line 271
    uint _S13;
    if(TB_0 <= 32U)
    {

#line 272
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 272
    }
    else
    {

#line 272
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 272
    }

#line 272
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


#line 256 "mm_32768_fusedTierB.slang"
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


#line 256
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 256
    uint _S14 = 2U * i_1;

#line 256
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14] = (as_type<uint>((v_1.x)));

#line 256
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14 + 1U] = (as_type<uint>((v_1.y)));

#line 256
    return;
}


#line 257
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 257
    uint _S15 = 2U * i_2;

#line 257
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15 + 1U]))));
}


#line 669
void exchange_0(array<float2, int(32)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 670
    uint j_2;

#line 681
    thread array<float2, int(32)> out_0;

#line 681
    uint z_0 = 0U;
    for(;;)
    {

#line 682
        if(z_0 < 32U)
        {
        }
        else
        {

#line 682
            break;
        }

#line 682
        out_0[z_0] = float2(0.0, 0.0);

#line 682
        z_0 = z_0 + 1U;

#line 682
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S16 = p0_0 & lenMask_0;

#line 688
    uint _S17 = _S16 >> lgSpan_0;

#line 688
    uint _S18 = _S17 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 688
    uint c_1 = 0U;

    for(;;)
    {

#line 690
        if(c_1 < 4U)
        {
        }
        else
        {

#line 690
            break;
        }

#line 691
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 691
        j_2 = 0U;
        for(;;)
        {

#line 692
            if(j_2 < 8U)
            {
            }
            else
            {

#line 692
                break;
            }

#line 692
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 8U + j_2], kernelContext_2);

#line 692
            j_2 = j_2 + 1U;

#line 692
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 693
        uint d_2 = 0U;
        for(;;)
        {

#line 694
            if(d_2 < 32U)
            {
            }
            else
            {

#line 694
                break;
            }

#line 695
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S19 = pz_0 & lenMask_0;

#line 696
            uint iz_0 = _S19 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S19 & spanMask_0);
            uint i_3 = _S17 + iz_0;
            uint _S20 = c_1 * 8U;

#line 699
            bool _S21;

#line 699
            if(i_3 >= _S20)
            {

#line 699
                _S21 = i_3 < ((c_1 + 1U) * 8U);

#line 699
            }
            else
            {

#line 699
                _S21 = false;

#line 699
            }

#line 699
            if(_S21)
            {

#line 699
                float2 _S22 = stgGet_0(_S18 + az_0 - _S20 * 1024U, kernelContext_2);
                out_0[d_2] = _S22;

#line 699
            }

#line 694
            d_2 = d_2 + 1U;

#line 694
        }

#line 690
        c_1 = c_1 + 1U;

#line 690
    }

#line 690
    j_2 = 0U;

#line 703
    for(;;)
    {

#line 703
        if(j_2 < 32U)
        {
        }
        else
        {

#line 703
            break;
        }

#line 703
        (*r_3)[j_2] = out_0[j_2];

#line 703
        j_2 = j_2 + 1U;

#line 703
    }
    return;
}


#line 612
void innermost_0(array<float2, int(32)> thread* r_4)
{

    dft32_0(r_4);

#line 624
    return;
}


#line 759
void transform_0(array<float2, int(32)> thread* r_5, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 759
    uint _S23;

#line 759
    uint k2_1;

#line 759
    float cr_0;

#line 759
    float ci_0;

#line 759
    uint _S24;

#line 759
    for(;;)
    {

#line 759
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

#line 762 "mm_32768_fusedTierB.slang"
    return;
}


#line 728
uint lgOf_0(uint i_4)
{

#line 728
    uint _S33;

#line 728
    if(i_4 < 2U)
    {

#line 728
        _S33 = 5U;

#line 728
    }
    else
    {

#line 728
        if(i_4 == 2U)
        {

#line 728
            _S33 = 5U;

#line 728
        }
        else
        {

#line 728
            _S33 = 1U;

#line 728
        }

#line 728
    }

#line 728
    return _S33;
}


#line 730
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 734
    uint lg_1 = lgOf_0(1U);

#line 734
    uint lg_2 = lgOf_0(0U);

#line 739
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 782
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 802
    kernelContext_4->_tid_0 = tid_1;
    uint _S34 = pair_0 / ntmpl_1;

#line 803
    uint _S35 = pair_0 % ntmpl_1;

#line 808
    thread array<float2, int(32)> r_6;

#line 808
    uint n2_0 = 0U;

#line 819
    for(;;)
    {

#line 819
        if(n2_0 < 32U)
        {
        }
        else
        {

#line 819
            break;
        }

#line 820
        uint idx_0 = tid_1 + 1024U * n2_0;
        r_6[n2_0] = cmulConj_0(cload_0(data_0, _S34 * 32768U + idx_0), cload_0(tmpl_0, _S35 * 32768U + idx_0));

#line 819
        n2_0 = n2_0 + 1U;

#line 819
    }

#line 819
    transform_0(&r_6, tid_1, kernelContext_4);

#line 848
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 848
    uint b_4 = tid_1;

#line 960
    for(;;)
    {

#line 960
        if(b_4 < nbins_1)
        {
        }
        else
        {

#line 960
            break;
        }

#line 960
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4] = thrBits_1;

#line 960
        b_4 = b_4 + 1024U;

#line 960
    }
    bool _S36 = nbins_1 == 1U;

#line 961
    bool live_0;

#line 961
    if(_S36)
    {

#line 961
        live_0 = tid_1 == 0U;

#line 961
    }
    else
    {

#line 961
        live_0 = false;

#line 961
    }

#line 961
    if(live_0)
    {

#line 961
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 961
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(32)> myMag_0;
    thread array<uint, int(32)> myBin_0;

#line 966
    uint i_5 = 0U;



    for(;;)
    {

#line 970
        if(i_5 < 32U)
        {
        }
        else
        {

#line 970
            break;
        }

#line 971
        uint idx_1 = slotToIndex_0(tid_1 * 32U + i_5);
        if(idx_1 >= winStart_1)
        {

#line 972
            live_0 = idx_1 < winEnd_1;

#line 972
        }
        else
        {

#line 972
            live_0 = false;

#line 972
        }



        float _rx_0 = r_6[i_5].x;

#line 976
        float _ry_0 = r_6[i_5].y;
        if(live_0)
        {

#line 977
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 977
        }
        else
        {

#line 977
            n2_0 = 0U;

#line 977
        }

#line 977
        myMag_0[i_5] = n2_0;

#line 985
        uint off_0 = idx_1 - winStart_1;

#line 992
        if(live_0)
        {

#line 992
            if(binShift_1 >= int(0))
            {

#line 992
                b_4 = off_0 >> uint(binShift_1);

#line 992
            }
            else
            {

#line 992
                uint _S37 = off_0 / binsize_1;

#line 992
                b_4 = _S37;

#line 992
            }

#line 992
        }
        else
        {

#line 992
            b_4 = 0U;

#line 992
        }

#line 992
        myBin_0[i_5] = b_4;

#line 992
        bool _S38;



        if(nbins_1 > 1U)
        {

#line 996
            _S38 = (myMag_0[i_5]) > thrBits_1;

#line 996
        }
        else
        {

#line 996
            _S38 = false;

#line 996
        }

#line 996
        if(_S38)
        {

#line 997
            uint _S39 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), myMag_0[i_5], memory_order_relaxed);

#line 996
        }

#line 970
        i_5 = i_5 + 1U;

#line 970
    }

#line 970
    uint winner_0;

#line 1020
    if(_S36)
    {

#line 1020
        winner_0 = thrBits_1;

#line 1020
        i_5 = 0U;


        for(;;)
        {

#line 1023
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1023
                break;
            }

#line 1023
            uint _S40 = max(winner_0, myMag_0[i_5]);

#line 1023
            uint i_6 = i_5 + 1U;

#line 1023
            winner_0 = _S40;

#line 1023
            i_5 = i_6;

#line 1023
        }

        uint wm_0 = simd_max(winner_0);
        bool _S41 = simd_is_first();

#line 1026
        if(_S41)
        {

#line 1026
            live_0 = wm_0 > thrBits_1;

#line 1026
        }
        else
        {

#line 1026
            live_0 = false;

#line 1026
        }

#line 1026
        if(live_0)
        {

#line 1026
            uint _S42 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1026
        }

#line 1020
    }

#line 1041
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1048
    if(_S36)
    {

#line 1048
        winner_0 = 4294967295U;

#line 1048
        i_5 = 0U;


        for(;;)
        {

#line 1051
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1051
                break;
            }

#line 1052
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1052
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 1052
            }
            else
            {

#line 1052
                live_0 = false;

#line 1052
            }

#line 1052
            if(live_0)
            {

#line 1052
                winner_0 = min(winner_0, tid_1 * 32U + i_5);

#line 1052
            }

#line 1051
            i_5 = i_5 + 1U;

#line 1051
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S43 = simd_is_first();

#line 1056
        if(_S43)
        {

#line 1056
            live_0 = waveWinner_0 != 4294967295U;

#line 1056
        }
        else
        {

#line 1056
            live_0 = false;

#line 1056
        }

#line 1056
        if(live_0)
        {

#line 1057
            uint _S44 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1056
        }

#line 1061
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1061
        i_5 = 0U;
        for(;;)
        {

#line 1062
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1062
                break;
            }

#line 1063
            uint _S45 = tid_1 * 32U + i_5;

#line 1063
            if(_S45 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 1064
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S45));

#line 1064
                *(peakVal_0+pair_0) = packed_float2(float2(r_6[i_5].x, r_6[i_5].y)) ;

#line 1063
            }

#line 1062
            i_5 = i_5 + 1U;

#line 1062
        }

#line 1072
        if(tid_1 == 0U)
        {

#line 1072
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1072
        }
        else
        {

#line 1072
            live_0 = false;

#line 1072
        }

#line 1072
        if(live_0)
        {

#line 1073
            *(peakIdx_0+pair_0) = int(-1);

#line 1073
            *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 1072
        }

#line 1048
    }
    else
    {

#line 1048
        i_5 = 0U;

#line 1081
        for(;;)
        {

#line 1081
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1081
                break;
            }

#line 1082
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1082
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]];

#line 1082
            }
            else
            {

#line 1082
                live_0 = false;

#line 1082
            }

#line 1082
            myMag_0[i_5] = uint(live_0);

#line 1081
            i_5 = i_5 + 1U;

#line 1081
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1084
        b_4 = tid_1;
        for(;;)
        {

#line 1085
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 1085
                break;
            }

#line 1085
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4] = 4294967295U;

#line 1085
            b_4 = b_4 + 1024U;

#line 1085
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1086
        i_5 = 0U;
        for(;;)
        {

#line 1087
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1087
                break;
            }

#line 1088
            if((myMag_0[i_5]) != 0U)
            {

#line 1088
                uint _S46 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), tid_1 * 32U + i_5, memory_order_relaxed);

#line 1088
            }

#line 1087
            i_5 = i_5 + 1U;

#line 1087
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1089
        i_5 = 0U;
        for(;;)
        {

#line 1090
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1090
                break;
            }

#line 1091
            if((myMag_0[i_5]) != 0U)
            {

#line 1091
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]]) == (tid_1 * 32U + i_5);

#line 1091
            }
            else
            {

#line 1091
                live_0 = false;

#line 1091
            }

#line 1091
            if(live_0)
            {

#line 1092
                uint o_0 = pair_0 * nbins_1 + myBin_0[i_5];
                *(peakIdx_0+o_0) = int(slotToIndex_0(tid_1 * 32U + i_5));

#line 1093
                *(peakVal_0+o_0) = packed_float2(float2(r_6[i_5].x, r_6[i_5].y)) ;

#line 1091
            }

#line 1090
            i_5 = i_5 + 1U;

#line 1090
        }

#line 1090
        b_4 = tid_1;

#line 1097
        for(;;)
        {

#line 1097
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 1097
                break;
            }

#line 1098
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4]) == 4294967295U)
            {

#line 1099
                uint _S47 = pair_0 * nbins_1 + b_4;

#line 1099
                *(peakIdx_0+_S47) = int(-1);

#line 1099
                *(peakVal_0+_S47) = packed_float2(float2(0.0, 0.0)) ;

#line 1098
            }

#line 1097
            b_4 = b_4 + 1024U;

#line 1097
        }

#line 1048
    }

#line 1106
    return;
}


#line 1570
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1570
    thread KernelContext_0 kernelContext_5;

#line 1570
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1570
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1570
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1570
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1570
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1570
    threadgroup array<uint, int(16384)> stg_1;

#line 1570
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1587
    uint _pr_0 = gid_0.x;

#line 1587
    uint _t_0 = lid_0.x;
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 1588
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);

#line 1596
    return;
}
