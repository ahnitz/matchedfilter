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


#line 196 "mm_256_refineListed_onebin.slang"
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


#line 270
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 270
    float _S2 = a_0.x;

#line 270
    float _S3 = b_1.x;

#line 270
    float _S4 = a_0.y;

#line 270
    float _S5 = b_1.y;

#line 270
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 475
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 477
    float2 t1_0 = *a_1 - *c_0;

#line 477
    float2 t2_0 = *b_2 + *d_1;

#line 477
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 479
    *b_2 = t1_0 + j3_0;

#line 479
    *c_0 = t0_0 - t2_0;

#line 479
    *d_1 = t1_0 - j3_0;
    return;
}


#line 269
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 269
    float _S6 = a_2.x;

#line 269
    float _S7 = b_3.x;

#line 269
    float _S8 = a_2.y;

#line 269
    float _S9 = b_3.y;

#line 269
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 511
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 518
    uint n1_0 = 0U;
    for(;;)
    {

#line 519
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 519
            break;
        }

#line 519
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 519
        n1_0 = n1_0 + 1U;

#line 519
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 520
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 520
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 521
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 521
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 522
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 522
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 522
    uint k2_0 = 0U;
    for(;;)
    {

#line 523
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 523
            break;
        }

#line 523
        uint _S10 = 4U * k2_0;

#line 523
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 523
        k2_0 = k2_0 + 1U;

#line 523
    }

    float2 t_0 = (*r_0)[int(1)];

#line 525
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 525
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 526
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 526
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 527
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 527
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 528
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 528
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 529
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 529
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 530
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 530
    (*r_0)[int(14)] = t_5;
    return;
}


#line 511
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_1 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_1 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_1 = float2(0.0f, 1.0f);
    float2 W6_1 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_1 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 518
    uint n1_1 = 0U;
    for(;;)
    {

#line 519
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 519
            break;
        }

#line 519
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 519
        n1_1 = n1_1 + 1U;

#line 519
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 520
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 520
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 521
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 521
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 522
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 522
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 522
    uint k2_1 = 0U;
    for(;;)
    {

#line 523
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 523
            break;
        }

#line 523
        uint _S11 = 4U * k2_1;

#line 523
        r4_0(&(*r_1)[_S11], &(*r_1)[_S11 + 1U], &(*r_1)[_S11 + 2U], &(*r_1)[_S11 + 3U]);

#line 523
        k2_1 = k2_1 + 1U;

#line 523
    }

    float2 t_6 = (*r_1)[int(1)];

#line 525
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 525
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 526
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 526
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 527
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 527
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 528
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 528
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 529
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 529
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 530
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 530
    (*r_1)[int(14)] = t_11;
    return;
}


#line 72 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 271 "mm_256_refineListed_onebin.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 273
    uint j_0 = d_2 / _S12;

#line 273
    uint m_0 = d_2 % _S12;

#line 273
    uint _S13;
    if(TB_0 <= 16U)
    {

#line 274
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 274
    }
    else
    {

#line 274
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 274
    }

#line 274
    return _S13;
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


#line 258 "mm_256_refineListed_onebin.slang"
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
    array<uint, int(512)> threadgroup* stg_0;
};


#line 258
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 258
    uint _S14 = 2U * i_1;

#line 258
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14] = (as_type<uint>((v_0.x)));

#line 258
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14 + 1U] = (as_type<uint>((v_0.y)));

#line 258
    return;
}


#line 259
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 259
    uint _S15 = 2U * i_2;

#line 259
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15 + 1U]))));
}


#line 700
void exchange_0(array<float2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 701
    uint j_1;

#line 712
    thread array<float2, int(16)> out_0;

#line 712
    uint z_0 = 0U;
    for(;;)
    {

#line 713
        if(z_0 < 16U)
        {
        }
        else
        {

#line 713
            break;
        }

#line 713
        out_0[z_0] = float2(0.0f, 0.0f);

#line 713
        z_0 = z_0 + 1U;

#line 713
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S16 = p0_0 & lenMask_0;

#line 719
    uint _S17 = (_S16 >> lgSpan_0) * 16U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 719
    uint c_1 = 0U;

    for(;;)
    {

#line 721
        if(c_1 < 1U)
        {
        }
        else
        {

#line 721
            break;
        }

#line 722
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 722
        j_1 = 0U;
        for(;;)
        {

#line 723
            if(j_1 < 16U)
            {
            }
            else
            {

#line 723
                break;
            }

#line 723
            stgPut_0(j_1 * 16U + kernelContext_2->_tid_0, (*r_2)[c_1 * 16U + j_1], kernelContext_2);

#line 723
            j_1 = j_1 + 1U;

#line 723
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 724
        uint d_3 = 0U;
        for(;;)
        {

#line 725
            if(d_3 < 16U)
            {
            }
            else
            {

#line 725
                break;
            }

#line 726
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S18 = pz_0 & lenMask_0;
            uint az_0 = (_S18 >> lgSpan_0) * 16U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S18 & spanMask_0);

#line 728
            float2 _S19 = stgGet_0(_S17 + az_0 - c_1 * 16U * 16U, kernelContext_2);


            out_0[d_3] = _S19;

#line 725
            d_3 = d_3 + 1U;

#line 725
        }

#line 721
        c_1 = c_1 + 1U;

#line 721
    }

#line 721
    j_1 = 0U;

#line 734
    for(;;)
    {

#line 734
        if(j_1 < 16U)
        {
        }
        else
        {

#line 734
            break;
        }

#line 734
        (*r_2)[j_1] = out_0[j_1];

#line 734
        j_1 = j_1 + 1U;

#line 734
    }
    return;
}


#line 614
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 621
    dft16_1(r_3);

#line 626
    return;
}


#line 790
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 790
    for(;;)
    {

#line 790
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
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 256.0f);
                float _S20 = tw_0.x;

#line 27
                float _S21 = tw_0.y;

#line 27
                uint k2_2 = 0U;

#line 27
                float cr_0 = 1.0f;

#line 27
                float ci_0 = 0.0f;

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
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S20 - ci_0 * _S21;
                    float _S22 = cr_0 * _S21 + ci_0 * _S20;

#line 29
                    k2_2 = k2_2 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S22;

#line 29
                }

#line 37
                uint per_2 = 16U / max(16U, 1U);
                uint _S23 = max(1U, 1U);
                uint blk2_2 = tid_0 / _S23;

#line 39
                uint lane2_2 = tid_0 % _S23;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 16U, 256U, blk_2, lane_2, per_2, _S23, 16U, blk2_2, lane2_2, kernelContext_3);

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

#line 793 "mm_256_refineListed_onebin.slang"
    return;
}


#line 759
uint lgOf_0(uint i_3)
{

#line 759
    uint _S24;

#line 759
    if(i_3 < 1U)
    {

#line 759
        _S24 = 4U;

#line 759
    }
    else
    {

#line 759
        if(i_3 == 1U)
        {

#line 759
            _S24 = 4U;

#line 759
        }
        else
        {

#line 759
            _S24 = 1U;

#line 759
        }

#line 759
    }

#line 759
    return _S24;
}


#line 761
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 765
    uint lg_1 = lgOf_0(0U);

#line 770
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 813
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 826
    bool gateOnly_0 = nbins_1 == 0U;

#line 833
    kernelContext_4->_tid_0 = tid_1;
    uint _S25 = pair_0 / ntmpl_1;

#line 834
    uint _S26 = pair_0 % ntmpl_1;

#line 839
    thread array<float2, int(16)> r_5;

#line 839
    uint n2_0 = 0U;

#line 850
    for(;;)
    {

#line 850
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 850
            break;
        }

#line 851
        uint idx_0 = tid_1 + 16U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S25 * 256U + idx_0), cload_0(tmpl_0, _S26 * 256U + idx_0));

#line 850
        n2_0 = n2_0 + 1U;

#line 850
    }

#line 850
    transform_0(&r_5, tid_1, kernelContext_4);

#line 879
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 879
    uint m_1;

#line 879
    uint i_4;

#line 879
    bool live_0;

#line 888
    if(gateOnly_0)
    {



        if(winStart_2 == 0U)
        {

#line 893
            live_0 = winEnd_2 >= 256U;

#line 893
        }
        else
        {

#line 893
            live_0 = false;

#line 893
        }

#line 893
        if(live_0)
        {

#line 893
            m_1 = 0U;

#line 893
            i_4 = 0U;
            for(;;)
            {

#line 894
                if(i_4 < 16U)
                {
                }
                else
                {

#line 894
                    break;
                }

#line 895
                uint _S27 = max(m_1, (as_type<uint>((r_5[i_4].x * r_5[i_4].x + r_5[i_4].y * r_5[i_4].y))));

#line 894
                uint i_5 = i_4 + 1U;

#line 894
                m_1 = _S27;

#line 894
                i_4 = i_5;

#line 894
            }

#line 893
        }
        else
        {

#line 893
            m_1 = 0U;

#line 893
            i_4 = 0U;



            for(;;)
            {

#line 897
                if(i_4 < 16U)
                {
                }
                else
                {

#line 897
                    break;
                }

#line 898
                uint idx_1 = slotToIndex_0(tid_1 * 16U + i_4);
                if(idx_1 >= winStart_2)
                {

#line 899
                    live_0 = idx_1 < winEnd_2;

#line 899
                }
                else
                {

#line 899
                    live_0 = false;

#line 899
                }
                uint b_4 = (as_type<uint>((r_5[i_4].x * r_5[i_4].x + r_5[i_4].y * r_5[i_4].y)));
                if(live_0)
                {

#line 901
                    n2_0 = max(m_1, b_4);

#line 901
                }
                else
                {

#line 901
                    n2_0 = m_1;

#line 901
                }

#line 897
                uint i_6 = i_4 + 1U;

#line 897
                m_1 = n2_0;

#line 897
                i_4 = i_6;

#line 897
            }

#line 893
        }

#line 904
        uint m_2 = simd_max(m_1);

#line 912
        if(tid_1 == 0U)
        {

#line 913
            int device* _S28 = peakIdx_0+pair_0;

#line 913
            int _S29;

#line 913
            if(m_2 > 0U)
            {

#line 913
                _S29 = int(0);

#line 913
            }
            else
            {

#line 913
                _S29 = int(-1);

#line 913
            }

#line 913
            *_S28 = _S29;

#line 913
            *(peakVal_0+pair_0) = packed_float2(float2(sqrt((as_type<float>((m_2)))), 0.0f)) ;

#line 912
        }



        return;
    }

#line 922
    bool _S30 = tid_1 == 0U;

#line 922
    if(_S30)
    {

#line 922
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 922
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 922
    }



    float2 _S31 = float2(0.0f, 0.0f);

    if(winStart_2 == 0U)
    {

#line 928
        live_0 = winEnd_2 >= 256U;

#line 928
    }
    else
    {

#line 928
        live_0 = false;

#line 928
    }

#line 928
    uint threadBestSlot_0;

#line 928
    float2 threadBestVal_0;

#line 928
    if(live_0)
    {

#line 928
        m_1 = thrBits_1;

#line 928
        threadBestSlot_0 = 4294967295U;

#line 928
        threadBestVal_0 = _S31;

#line 928
        i_4 = 0U;
        for(;;)
        {

#line 929
            if(i_4 < 16U)
            {
            }
            else
            {

#line 929
                break;
            }

#line 930
            float _rx_0 = r_5[i_4].x;

#line 930
            float _ry_0 = r_5[i_4].y;
            uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));
            if(magBits_0 > m_1)
            {
                uint _S32 = tid_1 * 16U + i_4;
                float2 _S33 = float2(_rx_0, _ry_0);

#line 935
                m_1 = magBits_0;

#line 935
                threadBestSlot_0 = _S32;

#line 935
                threadBestVal_0 = _S33;

#line 932
            }

#line 929
            i_4 = i_4 + 1U;

#line 929
        }

#line 928
    }
    else
    {

#line 928
        m_1 = thrBits_1;

#line 928
        threadBestSlot_0 = 4294967295U;

#line 928
        threadBestVal_0 = _S31;

#line 928
        i_4 = 0U;

#line 939
        for(;;)
        {

#line 939
            if(i_4 < 16U)
            {
            }
            else
            {

#line 939
                break;
            }

#line 940
            uint _S34 = tid_1 * 16U + i_4;

#line 940
            uint idx_2 = slotToIndex_0(_S34);
            if(idx_2 >= winStart_2)
            {

#line 941
                live_0 = idx_2 < winEnd_2;

#line 941
            }
            else
            {

#line 941
                live_0 = false;

#line 941
            }
            float _rx_1 = r_5[i_4].x;

#line 942
            float _ry_1 = r_5[i_4].y;

#line 942
            uint magBits_1;
            if(live_0)
            {

#line 943
                magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 943
            }
            else
            {

#line 943
                magBits_1 = 0U;

#line 943
            }
            if(magBits_1 > m_1)
            {

                float2 _S35 = float2(_rx_1, _ry_1);

#line 947
                m_1 = magBits_1;

#line 947
                threadBestSlot_0 = _S34;

#line 947
                threadBestVal_0 = _S35;

#line 944
            }

#line 939
            i_4 = i_4 + 1U;

#line 939
        }

#line 928
    }

#line 952
    threadgroup_barrier(mem_flags::mem_threadgroup);


    uint wm_0 = simd_max(m_1);
    bool _S36 = simd_is_first();

#line 956
    if(_S36)
    {

#line 956
        live_0 = wm_0 > thrBits_1;

#line 956
    }
    else
    {

#line 956
        live_0 = false;

#line 956
    }

#line 956
    if(live_0)
    {

#line 956
        uint _S37 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 956
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);


    if(m_1 > thrBits_1)
    {

#line 963
        live_0 = m_1 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 963
    }
    else
    {

#line 963
        live_0 = false;

#line 963
    }

#line 963
    if(live_0)
    {

#line 963
        i_4 = threadBestSlot_0;

#line 963
    }
    else
    {

#line 963
        i_4 = 4294967295U;

#line 963
    }



    uint waveWinner_0 = simd_min(i_4);
    bool _S38 = simd_is_first();

#line 968
    if(_S38)
    {

#line 968
        live_0 = waveWinner_0 != 4294967295U;

#line 968
    }
    else
    {

#line 968
        live_0 = false;

#line 968
    }

#line 968
    if(live_0)
    {

#line 969
        uint _S39 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 968
    }

#line 973
    threadgroup_barrier(mem_flags::mem_threadgroup);

    if(threadBestSlot_0 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
    {

#line 975
        live_0 = threadBestSlot_0 != 4294967295U;

#line 975
    }
    else
    {

#line 975
        live_0 = false;

#line 975
    }

#line 975
    if(live_0)
    {

#line 976
        *(peakIdx_0+pair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 976
        *(peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 975
    }



    if(_S30)
    {

#line 979
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 979
    }
    else
    {

#line 979
        live_0 = false;

#line 979
    }

#line 979
    if(live_0)
    {

#line 980
        *(peakIdx_0+pair_0) = int(-1);

#line 980
        *(peakVal_0+pair_0) = packed_float2(_S31) ;

#line 979
    }

#line 1137
    return;
}


#line 1767
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1767
    thread KernelContext_0 kernelContext_5;

#line 1767
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1767
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1767
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1767
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1767
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1767
    (&kernelContext_5)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1767
    threadgroup array<uint, int(512)> stg_1;

#line 1767
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1776
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1782
    (&kernelContext_5)->_stgBase_0 = 0U;
    thread uint ws_0 = entryPointParams_1->winStart_1;

#line 1783
    thread uint we_0 = entryPointParams_1->winEnd_1;
    uint _S40 = pair_1 / entryPointParams_1->ntmpl_0;

#line 1784
    rowWindow_0(_S40, &ws_0, &we_0);

#line 1784
    filterPair_0(pair_1, lid_0.x, (&kernelContext_5)->entryPointParams_data_0, (&kernelContext_5)->entryPointParams_tmpl_0, (&kernelContext_5)->entryPointParams_peakIdx_0, (&kernelContext_5)->entryPointParams_peakVal_0, entryPointParams_1->ntmpl_0, ws_0, we_0, (&kernelContext_5)->entryPointParams_0->binsize_0, (&kernelContext_5)->entryPointParams_0->binShift_0, (&kernelContext_5)->entryPointParams_0->nbins_0, (&kernelContext_5)->entryPointParams_0->thrBits_0, &kernelContext_5);


    return;
}
