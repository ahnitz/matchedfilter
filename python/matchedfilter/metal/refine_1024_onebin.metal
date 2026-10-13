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


#line 196 "mm_1024_refineListed_onebin.slang"
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
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

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


#line 269 "mm_1024_refineListed_onebin.slang"
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


#line 8599 "hlsl.meta.slang"
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


#line 256 "mm_1024_refineListed_onebin.slang"
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
    array<uint, int(2048)> threadgroup* stg_0;
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


#line 698
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 699
    uint j_1;

#line 710
    thread array<float2, int(16)> out_0;

#line 710
    uint z_0 = 0U;
    for(;;)
    {

#line 711
        if(z_0 < 16U)
        {
        }
        else
        {

#line 711
            break;
        }

#line 711
        out_0[z_0] = float2(0.0f, 0.0f);

#line 711
        z_0 = z_0 + 1U;

#line 711
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S15 = p0_0 & lenMask_0;

#line 717
    uint _S16 = (_S15 >> lgSpan_0) * 64U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 717
    uint c_1 = 0U;

    for(;;)
    {

#line 719
        if(c_1 < 1U)
        {
        }
        else
        {

#line 719
            break;
        }

#line 720
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 720
        j_1 = 0U;
        for(;;)
        {

#line 721
            if(j_1 < 16U)
            {
            }
            else
            {

#line 721
                break;
            }

#line 721
            stgPut_0(j_1 * 64U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 721
            j_1 = j_1 + 1U;

#line 721
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 722
        uint d_3 = 0U;
        for(;;)
        {

#line 723
            if(d_3 < 16U)
            {
            }
            else
            {

#line 723
                break;
            }

#line 724
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S17 = pz_0 & lenMask_0;
            uint az_0 = (_S17 >> lgSpan_0) * 64U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S17 & spanMask_0);

#line 726
            float2 _S18 = stgGet_0(_S16 + az_0 - c_1 * 16U * 64U, kernelContext_2);


            out_0[d_3] = _S18;

#line 723
            d_3 = d_3 + 1U;

#line 723
        }

#line 719
        c_1 = c_1 + 1U;

#line 719
    }

#line 719
    j_1 = 0U;

#line 732
    for(;;)
    {

#line 732
        if(j_1 < 16U)
        {
        }
        else
        {

#line 732
            break;
        }

#line 732
        (*r_1)[j_1] = out_0[j_1];

#line 732
        j_1 = j_1 + 1U;

#line 732
    }
    return;
}


#line 488
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 491
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 491
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 612
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 612
    uint b_4 = 0U;

#line 621
    for(;;)
    {

#line 621
        if(b_4 < 4U)
        {
        }
        else
        {

#line 621
            break;
        }

#line 621
        dft4_0(r_3, b_4 * 4U);

#line 621
        b_4 = b_4 + 1U;

#line 621
    }


    return;
}


#line 788
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 788
    uint _S19;

#line 788
    uint k2_1;

#line 788
    float cr_0;

#line 788
    float ci_0;

#line 788
    uint _S20;

#line 788
    for(;;)
    {

#line 788
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(64U);

#line 11
                _S19 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(1024U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 63U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);
                float _S21 = tw_0.x;

#line 27
                float _S22 = tw_0.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0f;

#line 27
                ci_0 = 0.0f;

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
                uint per_2 = 16U / max(64U, 1U);
                uint _S24 = max(4U, 1U);

#line 38
                _S20 = _S24;
                uint blk2_2 = tid_0 / _S24;

#line 39
                uint lane2_2 = tid_0 % _S24;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 64U, 1024U, blk_2, lane_2, per_2, _S24, 64U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(4U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 3U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 64.0f);
                float _S25 = tw_1.x;

#line 27
                float _S26 = tw_1.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0f;

#line 27
                ci_0 = 0.0f;

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
                exchange_0(r_4, _S19, lgTB_1, 4U, 64U, blk_3, lane_3, per_3, _S28, 4U, blk2_3, lane2_3, kernelContext_3);

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

#line 791 "mm_1024_refineListed_onebin.slang"
    return;
}


#line 757
uint lgOf_0(uint i_3)
{

#line 757
    uint _S29;

#line 757
    if(i_3 < 2U)
    {

#line 757
        _S29 = 4U;

#line 757
    }
    else
    {

#line 757
        _S29 = 1U;

#line 757
    }

#line 757
    return _S29;
}


#line 759
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 763
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 763
    uint lg_2 = lgOf_0(1U);

#line 763
    uint lg_3 = lgOf_0(0U);

#line 768
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 811
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 824
    bool gateOnly_0 = nbins_1 == 0U;

#line 831
    kernelContext_4->_tid_0 = tid_1;
    uint _S30 = pair_0 / ntmpl_1;

#line 832
    uint _S31 = pair_0 % ntmpl_1;

#line 837
    thread array<float2, int(16)> r_5;

#line 837
    uint n2_0 = 0U;

#line 848
    for(;;)
    {

#line 848
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 848
            break;
        }

#line 849
        uint idx_0 = tid_1 + 64U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S30 * 1024U + idx_0), cload_0(tmpl_0, _S31 * 1024U + idx_0));

#line 848
        n2_0 = n2_0 + 1U;

#line 848
    }

#line 848
    transform_0(&r_5, tid_1, kernelContext_4);

#line 877
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 877
    uint m_1;

#line 877
    uint k_0;

#line 877
    uint i_4;

#line 877
    bool live_0;

#line 886
    if(gateOnly_0)
    {



        if(winStart_2 == 0U)
        {

#line 891
            live_0 = winEnd_2 >= 1024U;

#line 891
        }
        else
        {

#line 891
            live_0 = false;

#line 891
        }

#line 891
        if(live_0)
        {

#line 891
            m_1 = 0U;

#line 891
            i_4 = 0U;
            for(;;)
            {

#line 892
                if(i_4 < 16U)
                {
                }
                else
                {

#line 892
                    break;
                }

#line 893
                uint _S32 = max(m_1, (as_type<uint>((r_5[i_4].x * r_5[i_4].x + r_5[i_4].y * r_5[i_4].y))));

#line 892
                uint i_5 = i_4 + 1U;

#line 892
                m_1 = _S32;

#line 892
                i_4 = i_5;

#line 892
            }

#line 891
        }
        else
        {

#line 891
            m_1 = 0U;

#line 891
            i_4 = 0U;



            for(;;)
            {

#line 895
                if(i_4 < 16U)
                {
                }
                else
                {

#line 895
                    break;
                }

#line 896
                uint idx_1 = slotToIndex_0(tid_1 * 16U + i_4);
                if(idx_1 >= winStart_2)
                {

#line 897
                    live_0 = idx_1 < winEnd_2;

#line 897
                }
                else
                {

#line 897
                    live_0 = false;

#line 897
                }
                uint b_5 = (as_type<uint>((r_5[i_4].x * r_5[i_4].x + r_5[i_4].y * r_5[i_4].y)));
                if(live_0)
                {

#line 899
                    n2_0 = max(m_1, b_5);

#line 899
                }
                else
                {

#line 899
                    n2_0 = m_1;

#line 899
                }

#line 895
                uint i_6 = i_4 + 1U;

#line 895
                m_1 = n2_0;

#line 895
                i_4 = i_6;

#line 895
            }

#line 891
        }

#line 902
        uint m_2 = simd_max(m_1);


        bool _S33 = simd_is_first();

#line 905
        if(_S33)
        {

#line 905
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_1 / 32U] = m_2;

#line 905
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 906
        m_1 = 0U;

#line 906
        k_0 = 0U;

        for(;;)
        {

#line 908
            if(k_0 < 2U)
            {
            }
            else
            {

#line 908
                break;
            }

#line 908
            uint _S34 = max(m_1, (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_0]);

#line 908
            uint k_1 = k_0 + 1U;

#line 908
            m_1 = _S34;

#line 908
            k_0 = k_1;

#line 908
        }

        if(tid_1 == 0U)
        {

#line 911
            int device* _S35 = peakIdx_0+pair_0;

#line 911
            int _S36;

#line 911
            if(m_1 > 0U)
            {

#line 911
                _S36 = int(0);

#line 911
            }
            else
            {

#line 911
                _S36 = int(-1);

#line 911
            }

#line 911
            *_S35 = _S36;

#line 911
            *(peakVal_0+pair_0) = packed_float2(float2(sqrt((as_type<float>((m_1)))), 0.0f)) ;

#line 910
        }



        return;
    }

#line 920
    bool _S37 = tid_1 == 0U;

#line 920
    if(_S37)
    {

#line 920
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 920
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 920
    }



    float2 _S38 = float2(0.0f, 0.0f);

    if(winStart_2 == 0U)
    {

#line 926
        live_0 = winEnd_2 >= 1024U;

#line 926
    }
    else
    {

#line 926
        live_0 = false;

#line 926
    }

#line 926
    float2 threadBestVal_0;

#line 926
    if(live_0)
    {

#line 926
        m_1 = thrBits_1;

#line 926
        k_0 = 4294967295U;

#line 926
        threadBestVal_0 = _S38;

#line 926
        i_4 = 0U;
        for(;;)
        {

#line 927
            if(i_4 < 16U)
            {
            }
            else
            {

#line 927
                break;
            }

#line 928
            float _rx_0 = r_5[i_4].x;

#line 928
            float _ry_0 = r_5[i_4].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > m_1)
            {
                uint _S39 = tid_1 * 16U + i_4;
                float2 _S40 = float2(_rx_0, _ry_0);

#line 933
                m_1 = magBits_0;

#line 933
                k_0 = _S39;

#line 933
                threadBestVal_0 = _S40;

#line 930
            }

#line 927
            i_4 = i_4 + 1U;

#line 927
        }

#line 926
    }
    else
    {

#line 926
        m_1 = thrBits_1;

#line 926
        k_0 = 4294967295U;

#line 926
        threadBestVal_0 = _S38;

#line 926
        i_4 = 0U;

#line 937
        for(;;)
        {

#line 937
            if(i_4 < 16U)
            {
            }
            else
            {

#line 937
                break;
            }

#line 938
            uint _S41 = tid_1 * 16U + i_4;

#line 938
            uint idx_2 = slotToIndex_0(_S41);
            if(idx_2 >= winStart_2)
            {

#line 939
                live_0 = idx_2 < winEnd_2;

#line 939
            }
            else
            {

#line 939
                live_0 = false;

#line 939
            }
            float _rx_1 = r_5[i_4].x;

#line 940
            float _ry_1 = r_5[i_4].y;

#line 940
            uint magBits_1;
            if(live_0)
            {

#line 941
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 941
            }
            else
            {

#line 941
                magBits_1 = 0U;

#line 941
            }
            if(magBits_1 > m_1)
            {

                float2 _S42 = float2(_rx_1, _ry_1);

#line 945
                m_1 = magBits_1;

#line 945
                k_0 = _S41;

#line 945
                threadBestVal_0 = _S42;

#line 942
            }

#line 937
            i_4 = i_4 + 1U;

#line 937
        }

#line 926
    }

#line 950
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(m_1);
    bool _S43 = simd_is_first();

#line 954
    if(_S43)
    {

#line 954
        live_0 = wm_0 > thrBits_1;

#line 954
    }
    else
    {

#line 954
        live_0 = false;

#line 954
    }

#line 954
    if(live_0)
    {

#line 954
        uint _S44 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 954
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(m_1 > thrBits_1)
    {

#line 961
        live_0 = m_1 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

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
        i_4 = k_0;

#line 961
    }
    else
    {

#line 961
        i_4 = 4294967295U;

#line 961
    }



    uint waveWinner_0 = simd_min(i_4);
    bool _S45 = simd_is_first();

#line 966
    if(_S45)
    {

#line 966
        live_0 = waveWinner_0 != 4294967295U;

#line 966
    }
    else
    {

#line 966
        live_0 = false;

#line 966
    }

#line 966
    if(live_0)
    {

#line 967
        uint _S46 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 966
    }

#line 971
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(k_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
    {

#line 973
        live_0 = k_0 != 4294967295U;

#line 973
    }
    else
    {

#line 973
        live_0 = false;

#line 973
    }

#line 973
    if(live_0)
    {

#line 974
        *(peakIdx_0+pair_0) = int(slotToIndex_0(k_0));

#line 974
        *(peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 973
    }



    if(_S37)
    {

#line 977
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 977
    }
    else
    {

#line 977
        live_0 = false;

#line 977
    }

#line 977
    if(live_0)
    {

#line 978
        *(peakIdx_0+pair_0) = int(-1);

#line 978
        *(peakVal_0+pair_0) = packed_float2(_S38) ;

#line 977
    }

#line 1135
    return;
}


#line 1759
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1759
    thread KernelContext_0 kernelContext_5;

#line 1759
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1759
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1759
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1759
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1759
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1759
    (&kernelContext_5)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1759
    threadgroup array<uint, int(2048)> stg_1;

#line 1759
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1768
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1774
    (&kernelContext_5)->_stgBase_0 = 0U;
    thread uint ws_0 = entryPointParams_1->winStart_1;

#line 1775
    thread uint we_0 = entryPointParams_1->winEnd_1;
    uint _S47 = pair_1 / entryPointParams_1->ntmpl_0;

#line 1776
    rowWindow_0(_S47, &ws_0, &we_0);

#line 1776
    filterPair_0(pair_1, lid_0.x, (&kernelContext_5)->entryPointParams_data_0, (&kernelContext_5)->entryPointParams_tmpl_0, (&kernelContext_5)->entryPointParams_peakIdx_0, (&kernelContext_5)->entryPointParams_peakVal_0, entryPointParams_1->ntmpl_0, ws_0, we_0, (&kernelContext_5)->entryPointParams_0->binsize_0, (&kernelContext_5)->entryPointParams_0->binShift_0, (&kernelContext_5)->entryPointParams_0->nbins_0, (&kernelContext_5)->entryPointParams_0->thrBits_0, &kernelContext_5);


    return;
}
