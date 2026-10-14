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


#line 196 "mm_16384_refineListed_lds32.slang"
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


#line 72 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 271 "mm_16384_refineListed_lds32.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 273
    uint j_0 = d_2 / _S11;

#line 273
    uint m_0 = d_2 % _S11;

#line 273
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 274
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 274
    }
    else
    {

#line 274
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 274
    }

#line 274
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


#line 258 "mm_16384_refineListed_lds32.slang"
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
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 258
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 258
    uint _S13 = 2U * i_1;

#line 258
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13] = (as_type<uint>((v_0.x)));

#line 258
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13 + 1U] = (as_type<uint>((v_0.y)));

#line 258
    return;
}


#line 259
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 259
    uint _S14 = 2U * i_2;

#line 259
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 700
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
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
    uint _S15 = p0_0 & lenMask_0;

#line 719
    uint _S16 = _S15 >> lgSpan_0;

#line 719
    uint _S17 = _S16 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 719
    uint c_1 = 0U;

    for(;;)
    {

#line 721
        if(c_1 < 4U)
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
            if(j_1 < 4U)
            {
            }
            else
            {

#line 723
                break;
            }

#line 723
            stgPut_0(j_1 * 1024U + kernelContext_2->_tid_0, (*r_1)[c_1 * 4U + j_1], kernelContext_2);

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

#line 727
            uint iz_0 = _S18 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S18 & spanMask_0);
            uint i_3 = _S16 + iz_0;
            uint _S19 = c_1 * 4U;

#line 730
            bool _S20;

#line 730
            if(i_3 >= _S19)
            {

#line 730
                _S20 = i_3 < ((c_1 + 1U) * 4U);

#line 730
            }
            else
            {

#line 730
                _S20 = false;

#line 730
            }

#line 730
            if(_S20)
            {

#line 730
                float2 _S21 = stgGet_0(_S17 + az_0 - _S19 * 1024U, kernelContext_2);
                out_0[d_3] = _S21;

#line 730
            }

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
        (*r_1)[j_1] = out_0[j_1];

#line 734
        j_1 = j_1 + 1U;

#line 734
    }
    return;
}


#line 490
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 493
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 493
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 614
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 614
    uint b_4 = 0U;

#line 623
    for(;;)
    {

#line 623
        if(b_4 < 4U)
        {
        }
        else
        {

#line 623
            break;
        }

#line 623
        dft4_0(r_3, b_4 * 4U);

#line 623
        b_4 = b_4 + 1U;

#line 623
    }


    return;
}


#line 802
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 802
    uint _S22;

#line 802
    uint k2_1;

#line 802
    float cr_0;

#line 802
    float ci_0;

#line 802
    uint _S23;

#line 802
    uint _S24;

#line 802
    uint _S25;

#line 802
    for(;;)
    {

#line 802
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S22 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(16384U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 16384.0f);
                float _S26 = tw_0.x;

#line 27
                float _S27 = tw_0.y;

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
                    float nr_0 = cr_0 * _S26 - ci_0 * _S27;
                    float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S28;

#line 29
                }

#line 37
                uint per_2 = 16U / max(1024U, 1U);
                uint _S29 = max(64U, 1U);

#line 38
                _S23 = _S29;
                uint blk2_2 = tid_0 / _S29;

#line 39
                uint lane2_2 = tid_0 % _S29;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 1024U, 16384U, blk_2, lane_2, per_2, _S29, 1024U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(64U);

#line 11
                _S24 = lgTB_1;

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 63U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 1024.0f);
                float _S30 = tw_1.x;

#line 27
                float _S31 = tw_1.y;

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
                    float nr_1 = cr_0 * _S30 - ci_0 * _S31;
                    float _S32 = cr_0 * _S31 + ci_0 * _S30;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S32;

#line 29
                }

#line 37
                uint per_3 = 16U / _S23;
                uint _S33 = max(4U, 1U);

#line 38
                _S25 = _S33;
                uint blk2_3 = tid_0 / _S33;

#line 39
                uint lane2_3 = tid_0 % _S33;

#line 39
                exchange_0(r_4, _S22, lgTB_1, 64U, 1024U, blk_3, lane_3, per_3, _S33, 64U, blk2_3, lane2_3, kernelContext_3);

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


                uint lgTB_2 = firstbithigh_0(4U);

                uint blk_4 = tid_0 >> lgTB_2;
                uint lane_4 = tid_0 & 3U;


                dft16_0(r_4);

#line 26
                float2 tw_2 = mfTwiddle_0(6.28318548202514648f * float(lane_4) / 64.0f);
                float _S34 = tw_2.x;

#line 27
                float _S35 = tw_2.y;

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
                    float nr_2 = cr_0 * _S34 - ci_0 * _S35;
                    float _S36 = cr_0 * _S35 + ci_0 * _S34;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_2;

#line 29
                    ci_0 = _S36;

#line 29
                }

#line 37
                uint per_4 = 16U / _S25;
                uint _S37 = max(0U, 1U);
                uint blk2_4 = tid_0 / _S37;

#line 39
                uint lane2_4 = tid_0 % _S37;

#line 39
                exchange_0(r_4, _S24, lgTB_2, 4U, 64U, blk_4, lane_4, per_4, _S37, 4U, blk2_4, lane2_4, kernelContext_3);

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

#line 805 "mm_16384_refineListed_lds32.slang"
    return;
}


#line 759
uint lgOf_0(uint i_4)
{

#line 759
    uint _S38;

#line 759
    if(i_4 < 3U)
    {

#line 759
        _S38 = 4U;

#line 759
    }
    else
    {

#line 759
        _S38 = 1U;

#line 759
    }

#line 759
    return _S38;
}


#line 761
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(4U);

    uint x_0 = slot_0 >> lg_0;

#line 765
    uint lg_1 = lgOf_0(3U);

    uint x_1 = x_0 >> lg_1;

#line 765
    uint lg_2 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_2;

#line 765
    uint lg_3 = lgOf_0(1U);

#line 765
    uint lg_4 = lgOf_0(0U);

#line 770
    return (((((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | (x_2 & ((1U << lg_3) - 1U))) << lg_4) | ((x_2 >> lg_3) & ((1U << lg_4) - 1U));
}


#line 825
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 845
    kernelContext_4->_tid_0 = tid_1;
    uint _S39 = pair_0 / ntmpl_1;

#line 846
    uint _S40 = pair_0 % ntmpl_1;

#line 851
    thread array<float2, int(16)> r_5;

#line 851
    uint n2_0 = 0U;

#line 862
    for(;;)
    {

#line 862
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 862
            break;
        }

#line 863
        uint idx_0 = tid_1 + 1024U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S39 * 16384U + idx_0), cload_0(tmpl_0, _S40 * 16384U + idx_0));

#line 862
        n2_0 = n2_0 + 1U;

#line 862
    }

#line 862
    transform_0(&r_5, tid_1, kernelContext_4);

#line 891
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 891
    uint b_5 = tid_1;

#line 1003
    for(;;)
    {

#line 1003
        if(b_5 < nbins_1)
        {
        }
        else
        {

#line 1003
            break;
        }

#line 1003
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_5] = thrBits_1;

#line 1003
        b_5 = b_5 + 1024U;

#line 1003
    }
    bool _S41 = nbins_1 == 1U;

#line 1004
    bool live_0;

#line 1004
    if(_S41)
    {

#line 1004
        live_0 = tid_1 == 0U;

#line 1004
    }
    else
    {

#line 1004
        live_0 = false;

#line 1004
    }

#line 1004
    if(live_0)
    {

#line 1004
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 1004
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1064
    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 1065
    uint i_5 = 0U;



    for(;;)
    {

#line 1069
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1069
            break;
        }

#line 1070
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_5);
        if(idx_1 >= winStart_2)
        {

#line 1071
            live_0 = idx_1 < winEnd_2;

#line 1071
        }
        else
        {

#line 1071
            live_0 = false;

#line 1071
        }



        float _rx_0 = r_5[i_5].x;

#line 1075
        float _ry_0 = r_5[i_5].y;
        if(live_0)
        {

#line 1076
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1076
        }
        else
        {

#line 1076
            n2_0 = 0U;

#line 1076
        }

#line 1076
        myMag_0[i_5] = n2_0;

#line 1084
        uint off_0 = idx_1 - winStart_2;

#line 1091
        if(live_0)
        {

#line 1091
            if(binShift_1 >= int(0))
            {

#line 1091
                b_5 = off_0 >> uint(binShift_1);

#line 1091
            }
            else
            {

#line 1091
                uint _S42 = off_0 / binsize_1;

#line 1091
                b_5 = _S42;

#line 1091
            }

#line 1091
        }
        else
        {

#line 1091
            b_5 = 0U;

#line 1091
        }

#line 1091
        myBin_0[i_5] = b_5;

#line 1091
        bool _S43;



        if(nbins_1 > 1U)
        {

#line 1095
            _S43 = (myMag_0[i_5]) > thrBits_1;

#line 1095
        }
        else
        {

#line 1095
            _S43 = false;

#line 1095
        }

#line 1095
        if(_S43)
        {

#line 1096
            uint _S44 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), myMag_0[i_5], memory_order_relaxed);

#line 1095
        }

#line 1069
        i_5 = i_5 + 1U;

#line 1069
    }

#line 1069
    uint winner_0;

#line 1119
    if(_S41)
    {

#line 1119
        winner_0 = thrBits_1;

#line 1119
        i_5 = 0U;


        for(;;)
        {

#line 1122
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1122
                break;
            }

#line 1122
            uint _S45 = max(winner_0, myMag_0[i_5]);

#line 1122
            uint i_6 = i_5 + 1U;

#line 1122
            winner_0 = _S45;

#line 1122
            i_5 = i_6;

#line 1122
        }

        uint wm_0 = simd_max(winner_0);
        bool _S46 = simd_is_first();

#line 1125
        if(_S46)
        {

#line 1125
            live_0 = wm_0 > thrBits_1;

#line 1125
        }
        else
        {

#line 1125
            live_0 = false;

#line 1125
        }

#line 1125
        if(live_0)
        {

#line 1125
            uint _S47 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1125
        }

#line 1119
    }

#line 1140
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1147
    if(_S41)
    {

#line 1147
        winner_0 = 4294967295U;

#line 1147
        i_5 = 0U;


        for(;;)
        {

#line 1150
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1150
                break;
            }

#line 1151
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1151
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 1151
            }
            else
            {

#line 1151
                live_0 = false;

#line 1151
            }

#line 1151
            if(live_0)
            {

#line 1151
                winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 1151
            }

#line 1150
            i_5 = i_5 + 1U;

#line 1150
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S48 = simd_is_first();

#line 1155
        if(_S48)
        {

#line 1155
            live_0 = waveWinner_0 != 4294967295U;

#line 1155
        }
        else
        {

#line 1155
            live_0 = false;

#line 1155
        }

#line 1155
        if(live_0)
        {

#line 1156
            uint _S49 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1155
        }

#line 1160
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1160
        i_5 = 0U;
        for(;;)
        {

#line 1161
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1161
                break;
            }

#line 1162
            uint _S50 = tid_1 * 16U + i_5;

#line 1162
            if(_S50 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 1163
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S50));

#line 1163
                *(peakVal_0+pair_0) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 1162
            }

#line 1161
            i_5 = i_5 + 1U;

#line 1161
        }

#line 1171
        if(tid_1 == 0U)
        {

#line 1171
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1171
        }
        else
        {

#line 1171
            live_0 = false;

#line 1171
        }

#line 1171
        if(live_0)
        {

#line 1172
            *(peakIdx_0+pair_0) = int(-1);

#line 1172
            *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1171
        }

#line 1147
    }
    else
    {

#line 1147
        i_5 = 0U;

#line 1180
        for(;;)
        {

#line 1180
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1180
                break;
            }

#line 1181
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1181
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]];

#line 1181
            }
            else
            {

#line 1181
                live_0 = false;

#line 1181
            }

#line 1181
            myMag_0[i_5] = uint(live_0);

#line 1180
            i_5 = i_5 + 1U;

#line 1180
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1183
        b_5 = tid_1;
        for(;;)
        {

#line 1184
            if(b_5 < nbins_1)
            {
            }
            else
            {

#line 1184
                break;
            }

#line 1184
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_5] = 4294967295U;

#line 1184
            b_5 = b_5 + 1024U;

#line 1184
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1185
        i_5 = 0U;
        for(;;)
        {

#line 1186
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1186
                break;
            }

#line 1187
            if((myMag_0[i_5]) != 0U)
            {

#line 1187
                uint _S51 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), tid_1 * 16U + i_5, memory_order_relaxed);

#line 1187
            }

#line 1186
            i_5 = i_5 + 1U;

#line 1186
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1188
        i_5 = 0U;
        for(;;)
        {

#line 1189
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1189
                break;
            }

#line 1190
            if((myMag_0[i_5]) != 0U)
            {

#line 1190
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]]) == (tid_1 * 16U + i_5);

#line 1190
            }
            else
            {

#line 1190
                live_0 = false;

#line 1190
            }

#line 1190
            if(live_0)
            {

#line 1191
                uint o_1 = pair_0 * nbins_1 + myBin_0[i_5];
                *(peakIdx_0+o_1) = int(slotToIndex_0(tid_1 * 16U + i_5));

#line 1192
                *(peakVal_0+o_1) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 1190
            }

#line 1189
            i_5 = i_5 + 1U;

#line 1189
        }

#line 1189
        b_5 = tid_1;

#line 1196
        for(;;)
        {

#line 1196
            if(b_5 < nbins_1)
            {
            }
            else
            {

#line 1196
                break;
            }

#line 1197
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_5]) == 4294967295U)
            {

#line 1198
                uint _S52 = pair_0 * nbins_1 + b_5;

#line 1198
                *(peakIdx_0+_S52) = int(-1);

#line 1198
                *(peakVal_0+_S52) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1197
            }

#line 1196
            b_5 = b_5 + 1024U;

#line 1196
        }

#line 1147
    }

#line 1206
    return;
}


#line 1836
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1836
    thread KernelContext_0 kernelContext_5;

#line 1836
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1836
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1836
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1836
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1836
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1836
    (&kernelContext_5)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1836
    threadgroup array<uint, int(8192)> stg_1;

#line 1836
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1845
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1851
    (&kernelContext_5)->_stgBase_0 = 0U;
    thread uint ws_0 = entryPointParams_1->winStart_1;

#line 1852
    thread uint we_0 = entryPointParams_1->winEnd_1;
    uint _S53 = pair_1 / entryPointParams_1->ntmpl_0;

#line 1853
    rowWindow_0(_S53, &ws_0, &we_0);

#line 1853
    filterPair_0(pair_1, lid_0.x, (&kernelContext_5)->entryPointParams_data_0, (&kernelContext_5)->entryPointParams_tmpl_0, (&kernelContext_5)->entryPointParams_peakIdx_0, (&kernelContext_5)->entryPointParams_peakVal_0, entryPointParams_1->ntmpl_0, ws_0, we_0, (&kernelContext_5)->entryPointParams_0->binsize_0, (&kernelContext_5)->entryPointParams_0->binShift_0, (&kernelContext_5)->entryPointParams_0->nbins_0, (&kernelContext_5)->entryPointParams_0->thrBits_0, &kernelContext_5);


    return;
}
