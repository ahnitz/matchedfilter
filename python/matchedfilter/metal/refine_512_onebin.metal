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


#line 190 "mm_512_refineListed_onebin.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 190
    return;
}


#line 162
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 162
    return float2(*(b_0+i_0)) ;
}


#line 262
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 262
    float _S2 = a_0.x;

#line 262
    float _S3 = b_1.x;

#line 262
    float _S4 = a_0.y;

#line 262
    float _S5 = b_1.y;

#line 262
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 467
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 469
    float2 t1_0 = *a_1 - *c_0;

#line 469
    float2 t2_0 = *b_2 + *d_1;

#line 469
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 471
    *b_2 = t1_0 + j3_0;

#line 471
    *c_0 = t0_0 - t2_0;

#line 471
    *d_1 = t1_0 - j3_0;
    return;
}


#line 261
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 261
    float _S6 = a_2.x;

#line 261
    float _S7 = b_3.x;

#line 261
    float _S8 = a_2.y;

#line 261
    float _S9 = b_3.y;

#line 261
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 503
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 510
    uint n1_0 = 0U;
    for(;;)
    {

#line 511
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 511
            break;
        }

#line 511
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 511
        n1_0 = n1_0 + 1U;

#line 511
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 512
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 512
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 513
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 513
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 514
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 514
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 514
    uint k2_0 = 0U;
    for(;;)
    {

#line 515
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 515
            break;
        }

#line 515
        uint _S10 = 4U * k2_0;

#line 515
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 515
        k2_0 = k2_0 + 1U;

#line 515
    }

    float2 t_0 = (*r_0)[int(1)];

#line 517
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 517
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 518
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 518
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 519
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 519
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 520
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 520
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 521
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 521
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 522
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 522
    (*r_0)[int(14)] = t_5;
    return;
}


#line 64 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 263 "mm_512_refineListed_onebin.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 265
    uint j_0 = d_2 / _S11;

#line 265
    uint m_0 = d_2 % _S11;

#line 265
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 266
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 266
    }
    else
    {

#line 266
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 266
    }

#line 266
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


#line 250 "mm_512_refineListed_onebin.slang"
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
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 250
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 250
    uint _S13 = 2U * i_1;

#line 250
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13] = (as_type<uint>((v_0.x)));

#line 250
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13 + 1U] = (as_type<uint>((v_0.y)));

#line 250
    return;
}


#line 251
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 251
    uint _S14 = 2U * i_2;

#line 251
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 663
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 664
    uint j_1;

#line 675
    thread array<float2, int(16)> out_0;

#line 675
    uint z_0 = 0U;
    for(;;)
    {

#line 676
        if(z_0 < 16U)
        {
        }
        else
        {

#line 676
            break;
        }

#line 676
        out_0[z_0] = float2(0.0, 0.0);

#line 676
        z_0 = z_0 + 1U;

#line 676
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S15 = p0_0 & lenMask_0;

#line 682
    uint _S16 = (_S15 >> lgSpan_0) * 32U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 682
    uint c_1 = 0U;

    for(;;)
    {

#line 684
        if(c_1 < 1U)
        {
        }
        else
        {

#line 684
            break;
        }

#line 685
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 685
        j_1 = 0U;
        for(;;)
        {

#line 686
            if(j_1 < 16U)
            {
            }
            else
            {

#line 686
                break;
            }

#line 686
            stgPut_0(j_1 * 32U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 686
            j_1 = j_1 + 1U;

#line 686
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 687
        uint d_3 = 0U;
        for(;;)
        {

#line 688
            if(d_3 < 16U)
            {
            }
            else
            {

#line 688
                break;
            }

#line 689
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S17 = pz_0 & lenMask_0;
            uint az_0 = (_S17 >> lgSpan_0) * 32U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S17 & spanMask_0);

#line 691
            float2 _S18 = stgGet_0(_S16 + az_0 - c_1 * 16U * 32U, kernelContext_2);


            out_0[d_3] = _S18;

#line 688
            d_3 = d_3 + 1U;

#line 688
        }

#line 684
        c_1 = c_1 + 1U;

#line 684
    }

#line 684
    j_1 = 0U;

#line 697
    for(;;)
    {

#line 697
        if(j_1 < 16U)
        {
        }
        else
        {

#line 697
            break;
        }

#line 697
        (*r_1)[j_1] = out_0[j_1];

#line 697
        j_1 = j_1 + 1U;

#line 697
    }
    return;
}


#line 478
void dft2_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    float2 a_3 = (*r_2)[o_0];

#line 480
    float2 b_4 = (*r_2)[o_0 + 1U];

#line 480
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 480
    (*r_2)[o_0 + 1U] = a_3 - b_4;
    return;
}


#line 606
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 606
    uint b_5 = 0U;

#line 616
    for(;;)
    {

#line 616
        if(b_5 < 8U)
        {
        }
        else
        {

#line 616
            break;
        }

#line 616
        dft2_0(r_3, b_5 * 2U);

#line 616
        b_5 = b_5 + 1U;

#line 616
    }

    return;
}


#line 753
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 753
    uint _S19;

#line 753
    uint k2_1;

#line 753
    float cr_0;

#line 753
    float ci_0;

#line 753
    uint _S20;

#line 753
    for(;;)
    {

#line 753
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(32U);

#line 11
                _S19 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(512U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 31U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 512.0);
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
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
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
                uint per_2 = 16U / max(32U, 1U);
                uint _S24 = max(2U, 1U);

#line 38
                _S20 = _S24;
                uint blk2_2 = tid_0 / _S24;

#line 39
                uint lane2_2 = tid_0 % _S24;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 32U, 512U, blk_2, lane_2, per_2, _S24, 32U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(2U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 1U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 32.0);
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
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
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
                exchange_0(r_4, _S19, lgTB_1, 2U, 32U, blk_3, lane_3, per_3, _S28, 2U, blk2_3, lane2_3, kernelContext_3);

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

#line 756 "mm_512_refineListed_onebin.slang"
    return;
}


#line 722
uint lgOf_0(uint i_3)
{

#line 722
    uint _S29;

#line 722
    if(i_3 < 2U)
    {

#line 722
        _S29 = 4U;

#line 722
    }
    else
    {

#line 722
        _S29 = 1U;

#line 722
    }

#line 722
    return _S29;
}


#line 724
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 728
    uint lg_1 = lgOf_0(1U);

#line 728
    uint lg_2 = lgOf_0(0U);

#line 733
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 768
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 782
    kernelContext_4->_tid_0 = tid_1;
    uint _S30 = pair_0 / ntmpl_1;

#line 783
    uint _S31 = pair_0 % ntmpl_1;

    thread array<float2, int(16)> r_5;

#line 785
    uint n2_0 = 0U;

#line 796
    for(;;)
    {

#line 796
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 796
            break;
        }

#line 797
        uint idx_0 = tid_1 + 32U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S30 * 512U + idx_0), cload_0(tmpl_0, _S31 * 512U + idx_0));

#line 796
        n2_0 = n2_0 + 1U;

#line 796
    }

#line 796
    transform_0(&r_5, tid_1, kernelContext_4);

#line 825
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 830
    bool _S32 = tid_1 == 0U;

#line 830
    if(_S32)
    {

#line 830
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 830
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 830
    }



    float2 _S33 = float2(0.0, 0.0);

#line 834
    bool live_0;

    if(winStart_2 == 0U)
    {

#line 836
        live_0 = winEnd_2 >= 512U;

#line 836
    }
    else
    {

#line 836
        live_0 = false;

#line 836
    }

#line 836
    uint threadBestBits_0;

#line 836
    uint threadBestSlot_0;

#line 836
    uint winner_0;

#line 836
    float2 threadBestVal_0;

#line 836
    if(live_0)
    {

#line 836
        threadBestBits_0 = thrBits_1;

#line 836
        threadBestSlot_0 = 4294967295U;

#line 836
        threadBestVal_0 = _S33;

#line 836
        winner_0 = 0U;
        for(;;)
        {

#line 837
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 837
                break;
            }

#line 838
            float _rx_0 = r_5[winner_0].x;

#line 838
            float _ry_0 = r_5[winner_0].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > threadBestBits_0)
            {
                uint _S34 = tid_1 * 16U + winner_0;
                float2 _S35 = float2(_rx_0, _ry_0);

#line 843
                threadBestBits_0 = magBits_0;

#line 843
                threadBestSlot_0 = _S34;

#line 843
                threadBestVal_0 = _S35;

#line 840
            }

#line 837
            winner_0 = winner_0 + 1U;

#line 837
        }

#line 836
    }
    else
    {

#line 836
        threadBestBits_0 = thrBits_1;

#line 836
        threadBestSlot_0 = 4294967295U;

#line 836
        threadBestVal_0 = _S33;

#line 836
        winner_0 = 0U;

#line 847
        for(;;)
        {

#line 847
            if(winner_0 < 16U)
            {
            }
            else
            {

#line 847
                break;
            }

#line 848
            uint _S36 = tid_1 * 16U + winner_0;

#line 848
            uint idx_1 = slotToIndex_0(_S36);
            if(idx_1 >= winStart_2)
            {

#line 849
                live_0 = idx_1 < winEnd_2;

#line 849
            }
            else
            {

#line 849
                live_0 = false;

#line 849
            }
            float _rx_1 = r_5[winner_0].x;

#line 850
            float _ry_1 = r_5[winner_0].y;

#line 850
            uint magBits_1;
            if(live_0)
            {

#line 851
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 851
            }
            else
            {

#line 851
                magBits_1 = 0U;

#line 851
            }
            if(magBits_1 > threadBestBits_0)
            {

                float2 _S37 = float2(_rx_1, _ry_1);

#line 855
                threadBestBits_0 = magBits_1;

#line 855
                threadBestSlot_0 = _S36;

#line 855
                threadBestVal_0 = _S37;

#line 852
            }

#line 847
            winner_0 = winner_0 + 1U;

#line 847
        }

#line 836
    }

#line 860
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(threadBestBits_0);
    bool _S38 = simd_is_first();

#line 864
    if(_S38)
    {

#line 864
        live_0 = wm_0 > thrBits_1;

#line 864
    }
    else
    {

#line 864
        live_0 = false;

#line 864
    }

#line 864
    if(live_0)
    {

#line 864
        uint _S39 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 864
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(threadBestBits_0 > thrBits_1)
    {

#line 871
        live_0 = threadBestBits_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 871
    }
    else
    {

#line 871
        live_0 = false;

#line 871
    }

#line 871
    if(live_0)
    {

#line 871
        winner_0 = threadBestSlot_0;

#line 871
    }
    else
    {

#line 871
        winner_0 = 4294967295U;

#line 871
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S40 = simd_is_first();

#line 876
    if(_S40)
    {

#line 876
        live_0 = waveWinner_0 != 4294967295U;

#line 876
    }
    else
    {

#line 876
        live_0 = false;

#line 876
    }

#line 876
    if(live_0)
    {

#line 877
        uint _S41 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 876
    }

#line 881
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(threadBestSlot_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
    {

#line 883
        live_0 = threadBestSlot_0 != 4294967295U;

#line 883
    }
    else
    {

#line 883
        live_0 = false;

#line 883
    }

#line 883
    if(live_0)
    {

#line 884
        *(peakIdx_0+pair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 884
        *(peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 883
    }



    if(_S32)
    {

#line 887
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 887
    }
    else
    {

#line 887
        live_0 = false;

#line 887
    }

#line 887
    if(live_0)
    {

#line 888
        *(peakIdx_0+pair_0) = int(-1);

#line 888
        *(peakVal_0+pair_0) = packed_float2(_S33) ;

#line 887
    }

#line 1045
    return;
}


#line 1585
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1585
    thread KernelContext_0 kernelContext_5;

#line 1585
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1585
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1585
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1585
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1585
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1585
    (&kernelContext_5)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1585
    threadgroup array<uint, int(1024)> stg_1;

#line 1585
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1594
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1600
    (&kernelContext_5)->_stgBase_0 = 0U;
    thread uint ws_0 = entryPointParams_1->winStart_1;

#line 1601
    thread uint we_0 = entryPointParams_1->winEnd_1;
    uint _S42 = pair_1 / entryPointParams_1->ntmpl_0;

#line 1602
    rowWindow_0(_S42, &ws_0, &we_0);

#line 1602
    filterPair_0(pair_1, lid_0.x, (&kernelContext_5)->entryPointParams_data_0, (&kernelContext_5)->entryPointParams_tmpl_0, (&kernelContext_5)->entryPointParams_peakIdx_0, (&kernelContext_5)->entryPointParams_peakVal_0, entryPointParams_1->ntmpl_0, ws_0, we_0, (&kernelContext_5)->entryPointParams_0->binsize_0, (&kernelContext_5)->entryPointParams_0->binShift_0, (&kernelContext_5)->entryPointParams_0->nbins_0, (&kernelContext_5)->entryPointParams_0->thrBits_0, &kernelContext_5);


    return;
}
