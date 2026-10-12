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


#line 196 "mm_8192_refineListed.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 196
    return;
}


#line 168
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


#line 473
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 475
    float2 t1_0 = *a_1 - *c_0;

#line 475
    float2 t2_0 = *b_2 + *d_1;

#line 475
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 477
    *b_2 = t1_0 + j3_0;

#line 477
    *c_0 = t0_0 - t2_0;

#line 477
    *d_1 = t1_0 - j3_0;
    return;
}


#line 267
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 267
    float _S6 = a_2.x;

#line 267
    float _S7 = b_3.x;

#line 267
    float _S8 = a_2.y;

#line 267
    float _S9 = b_3.y;

#line 267
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
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


#line 64 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 269 "mm_8192_refineListed.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 271
    uint j_0 = d_2 / _S11;

#line 271
    uint m_0 = d_2 % _S11;

#line 271
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 272
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 272
    }
    else
    {

#line 272
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 272
    }

#line 272
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


#line 256 "mm_8192_refineListed.slang"
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
    array<uint, int(16384)> threadgroup* stg_0;
};


#line 256
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 256
    uint _S13 = 2U * i_1;

#line 256
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13] = (as_type<uint>((v_0.x)));

#line 256
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13 + 1U] = (as_type<uint>((v_0.y)));

#line 256
    return;
}


#line 257
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 257
    uint _S14 = 2U * i_2;

#line 257
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 669
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 670
    uint j_1;

#line 681
    thread array<float2, int(16)> out_0;

#line 681
    uint z_0 = 0U;
    for(;;)
    {

#line 682
        if(z_0 < 16U)
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
    uint _S15 = p0_0 & lenMask_0;

#line 688
    uint _S16 = (_S15 >> lgSpan_0) * 512U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 688
    uint c_1 = 0U;

    for(;;)
    {

#line 690
        if(c_1 < 1U)
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
        j_1 = 0U;
        for(;;)
        {

#line 692
            if(j_1 < 16U)
            {
            }
            else
            {

#line 692
                break;
            }

#line 692
            stgPut_0(j_1 * 512U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 692
            j_1 = j_1 + 1U;

#line 692
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 693
        uint d_3 = 0U;
        for(;;)
        {

#line 694
            if(d_3 < 16U)
            {
            }
            else
            {

#line 694
                break;
            }

#line 695
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S17 = pz_0 & lenMask_0;
            uint az_0 = (_S17 >> lgSpan_0) * 512U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S17 & spanMask_0);

#line 697
            float2 _S18 = stgGet_0(_S16 + az_0 - c_1 * 16U * 512U, kernelContext_2);


            out_0[d_3] = _S18;

#line 694
            d_3 = d_3 + 1U;

#line 694
        }

#line 690
        c_1 = c_1 + 1U;

#line 690
    }

#line 690
    j_1 = 0U;

#line 703
    for(;;)
    {

#line 703
        if(j_1 < 16U)
        {
        }
        else
        {

#line 703
            break;
        }

#line 703
        (*r_1)[j_1] = out_0[j_1];

#line 703
        j_1 = j_1 + 1U;

#line 703
    }
    return;
}


#line 484
void dft2_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    float2 a_3 = (*r_2)[o_0];

#line 486
    float2 b_4 = (*r_2)[o_0 + 1U];

#line 486
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 486
    (*r_2)[o_0 + 1U] = a_3 - b_4;
    return;
}


#line 612
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 612
    uint b_5 = 0U;

#line 622
    for(;;)
    {

#line 622
        if(b_5 < 8U)
        {
        }
        else
        {

#line 622
            break;
        }

#line 622
        dft2_0(r_3, b_5 * 2U);

#line 622
        b_5 = b_5 + 1U;

#line 622
    }

    return;
}


#line 759
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 759
    uint _S19;

#line 759
    uint k2_1;

#line 759
    float cr_0;

#line 759
    float ci_0;

#line 759
    uint _S20;

#line 759
    uint _S21;

#line 759
    uint _S22;

#line 759
    for(;;)
    {

#line 759
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(512U);

#line 11
                _S19 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(8192U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 511U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 8192.0);
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
                uint per_2 = 16U / max(512U, 1U);
                uint _S26 = max(32U, 1U);

#line 38
                _S20 = _S26;
                uint blk2_2 = tid_0 / _S26;

#line 39
                uint lane2_2 = tid_0 % _S26;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 512U, 8192U, blk_2, lane_2, per_2, _S26, 512U, blk2_2, lane2_2, kernelContext_3);

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

#line 11
                _S21 = lgTB_1;

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 31U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 512.0);
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
                uint per_3 = 16U / _S20;
                uint _S30 = max(2U, 1U);

#line 38
                _S22 = _S30;
                uint blk2_3 = tid_0 / _S30;

#line 39
                uint lane2_3 = tid_0 % _S30;

#line 39
                exchange_0(r_4, _S19, lgTB_1, 32U, 512U, blk_3, lane_3, per_3, _S30, 32U, blk2_3, lane2_3, kernelContext_3);

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


                uint lgTB_2 = firstbithigh_0(2U);

                uint blk_4 = tid_0 >> lgTB_2;
                uint lane_4 = tid_0 & 1U;


                dft16_0(r_4);

#line 26
                float2 tw_2 = mfTwiddle_0(6.28318548202514648 * float(lane_4) / 32.0);
                float _S31 = tw_2.x;

#line 27
                float _S32 = tw_2.y;

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
                    float nr_2 = cr_0 * _S31 - ci_0 * _S32;
                    float _S33 = cr_0 * _S32 + ci_0 * _S31;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_2;

#line 29
                    ci_0 = _S33;

#line 29
                }

#line 37
                uint per_4 = 16U / _S22;
                uint _S34 = max(0U, 1U);
                uint blk2_4 = tid_0 / _S34;

#line 39
                uint lane2_4 = tid_0 % _S34;

#line 39
                exchange_0(r_4, _S21, lgTB_2, 2U, 32U, blk_4, lane_4, per_4, _S34, 2U, blk2_4, lane2_4, kernelContext_3);

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

#line 762 "mm_8192_refineListed.slang"
    return;
}


#line 728
uint lgOf_0(uint i_3)
{

#line 728
    uint _S35;

#line 728
    if(i_3 < 3U)
    {

#line 728
        _S35 = 4U;

#line 728
    }
    else
    {

#line 728
        _S35 = 1U;

#line 728
    }

#line 728
    return _S35;
}


#line 730
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 734
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 734
    uint lg_2 = lgOf_0(1U);

#line 734
    uint lg_3 = lgOf_0(0U);

#line 739
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 782
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 802
    kernelContext_4->_tid_0 = tid_1;
    uint _S36 = pair_0 / ntmpl_1;

#line 803
    uint _S37 = pair_0 % ntmpl_1;

#line 808
    thread array<float2, int(16)> r_5;

#line 808
    uint n2_0 = 0U;

#line 819
    for(;;)
    {

#line 819
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 819
            break;
        }

#line 820
        uint idx_0 = tid_1 + 512U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S36 * 8192U + idx_0), cload_0(tmpl_0, _S37 * 8192U + idx_0));

#line 819
        n2_0 = n2_0 + 1U;

#line 819
    }

#line 819
    transform_0(&r_5, tid_1, kernelContext_4);

#line 848
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 848
    uint b_6 = tid_1;

#line 960
    for(;;)
    {

#line 960
        if(b_6 < nbins_1)
        {
        }
        else
        {

#line 960
            break;
        }

#line 960
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6] = thrBits_1;

#line 960
        b_6 = b_6 + 512U;

#line 960
    }
    bool _S38 = nbins_1 == 1U;

#line 961
    bool live_0;

#line 961
    if(_S38)
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

    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 966
    uint i_4 = 0U;



    for(;;)
    {

#line 970
        if(i_4 < 16U)
        {
        }
        else
        {

#line 970
            break;
        }

#line 971
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_4);
        if(idx_1 >= winStart_2)
        {

#line 972
            live_0 = idx_1 < winEnd_2;

#line 972
        }
        else
        {

#line 972
            live_0 = false;

#line 972
        }



        float _rx_0 = r_5[i_4].x;

#line 976
        float _ry_0 = r_5[i_4].y;
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
        myMag_0[i_4] = n2_0;

#line 985
        uint off_0 = idx_1 - winStart_2;

#line 992
        if(live_0)
        {

#line 992
            if(binShift_1 >= int(0))
            {

#line 992
                b_6 = off_0 >> uint(binShift_1);

#line 992
            }
            else
            {

#line 992
                uint _S39 = off_0 / binsize_1;

#line 992
                b_6 = _S39;

#line 992
            }

#line 992
        }
        else
        {

#line 992
            b_6 = 0U;

#line 992
        }

#line 992
        myBin_0[i_4] = b_6;

#line 992
        bool _S40;



        if(nbins_1 > 1U)
        {

#line 996
            _S40 = (myMag_0[i_4]) > thrBits_1;

#line 996
        }
        else
        {

#line 996
            _S40 = false;

#line 996
        }

#line 996
        if(_S40)
        {

#line 997
            uint _S41 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_4]])), myMag_0[i_4], memory_order_relaxed);

#line 996
        }

#line 970
        i_4 = i_4 + 1U;

#line 970
    }

#line 970
    uint winner_0;

#line 1020
    if(_S38)
    {

#line 1020
        winner_0 = thrBits_1;

#line 1020
        i_4 = 0U;


        for(;;)
        {

#line 1023
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1023
                break;
            }

#line 1023
            uint _S42 = max(winner_0, myMag_0[i_4]);

#line 1023
            uint i_5 = i_4 + 1U;

#line 1023
            winner_0 = _S42;

#line 1023
            i_4 = i_5;

#line 1023
        }

        uint wm_0 = simd_max(winner_0);
        bool _S43 = simd_is_first();

#line 1026
        if(_S43)
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
            uint _S44 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1026
        }

#line 1020
    }

#line 1041
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1048
    if(_S38)
    {

#line 1048
        winner_0 = 4294967295U;

#line 1048
        i_4 = 0U;


        for(;;)
        {

#line 1051
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1051
                break;
            }

#line 1052
            if((myMag_0[i_4]) > thrBits_1)
            {

#line 1052
                live_0 = (myMag_0[i_4]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

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
                winner_0 = min(winner_0, tid_1 * 16U + i_4);

#line 1052
            }

#line 1051
            i_4 = i_4 + 1U;

#line 1051
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S45 = simd_is_first();

#line 1056
        if(_S45)
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
            uint _S46 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1056
        }

#line 1061
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1061
        i_4 = 0U;
        for(;;)
        {

#line 1062
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1062
                break;
            }

#line 1063
            uint _S47 = tid_1 * 16U + i_4;

#line 1063
            if(_S47 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 1064
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S47));

#line 1064
                *(peakVal_0+pair_0) = packed_float2(float2(r_5[i_4].x, r_5[i_4].y)) ;

#line 1063
            }

#line 1062
            i_4 = i_4 + 1U;

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
        i_4 = 0U;

#line 1081
        for(;;)
        {

#line 1081
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1081
                break;
            }

#line 1082
            if((myMag_0[i_4]) > thrBits_1)
            {

#line 1082
                live_0 = (myMag_0[i_4]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_4]];

#line 1082
            }
            else
            {

#line 1082
                live_0 = false;

#line 1082
            }

#line 1082
            myMag_0[i_4] = uint(live_0);

#line 1081
            i_4 = i_4 + 1U;

#line 1081
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1084
        b_6 = tid_1;
        for(;;)
        {

#line 1085
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 1085
                break;
            }

#line 1085
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6] = 4294967295U;

#line 1085
            b_6 = b_6 + 512U;

#line 1085
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1086
        i_4 = 0U;
        for(;;)
        {

#line 1087
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1087
                break;
            }

#line 1088
            if((myMag_0[i_4]) != 0U)
            {

#line 1088
                uint _S48 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_4]])), tid_1 * 16U + i_4, memory_order_relaxed);

#line 1088
            }

#line 1087
            i_4 = i_4 + 1U;

#line 1087
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1089
        i_4 = 0U;
        for(;;)
        {

#line 1090
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1090
                break;
            }

#line 1091
            if((myMag_0[i_4]) != 0U)
            {

#line 1091
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_4]]) == (tid_1 * 16U + i_4);

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
                uint o_1 = pair_0 * nbins_1 + myBin_0[i_4];
                *(peakIdx_0+o_1) = int(slotToIndex_0(tid_1 * 16U + i_4));

#line 1093
                *(peakVal_0+o_1) = packed_float2(float2(r_5[i_4].x, r_5[i_4].y)) ;

#line 1091
            }

#line 1090
            i_4 = i_4 + 1U;

#line 1090
        }

#line 1090
        b_6 = tid_1;

#line 1097
        for(;;)
        {

#line 1097
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 1097
                break;
            }

#line 1098
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6]) == 4294967295U)
            {

#line 1099
                uint _S49 = pair_0 * nbins_1 + b_6;

#line 1099
                *(peakIdx_0+_S49) = int(-1);

#line 1099
                *(peakVal_0+_S49) = packed_float2(float2(0.0, 0.0)) ;

#line 1098
            }

#line 1097
            b_6 = b_6 + 512U;

#line 1097
        }

#line 1048
    }

#line 1106
    return;
}


#line 1730
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1730
    thread KernelContext_0 kernelContext_5;

#line 1730
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1730
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1730
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1730
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1730
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1730
    (&kernelContext_5)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1730
    threadgroup array<uint, int(16384)> stg_1;

#line 1730
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1739
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1745
    (&kernelContext_5)->_stgBase_0 = 0U;
    thread uint ws_0 = entryPointParams_1->winStart_1;

#line 1746
    thread uint we_0 = entryPointParams_1->winEnd_1;
    uint _S50 = pair_1 / entryPointParams_1->ntmpl_0;

#line 1747
    rowWindow_0(_S50, &ws_0, &we_0);

#line 1747
    filterPair_0(pair_1, lid_0.x, (&kernelContext_5)->entryPointParams_data_0, (&kernelContext_5)->entryPointParams_tmpl_0, (&kernelContext_5)->entryPointParams_peakIdx_0, (&kernelContext_5)->entryPointParams_peakVal_0, entryPointParams_1->ntmpl_0, ws_0, we_0, (&kernelContext_5)->entryPointParams_0->binsize_0, (&kernelContext_5)->entryPointParams_0->binShift_0, (&kernelContext_5)->entryPointParams_0->nbins_0, (&kernelContext_5)->entryPointParams_0->thrBits_0, &kernelContext_5);


    return;
}
