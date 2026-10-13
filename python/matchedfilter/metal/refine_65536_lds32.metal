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


#line 196 "mm_65536_refineListed_lds32.slang"
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


#line 64 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 267 "mm_65536_refineListed_lds32.slang"
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


#line 575
void dft64_0(array<float2, int(64)> thread* r_1)
{

#line 575
    uint k_0;

#line 575
    uint j_0 = 0U;

    for(;;)
    {

#line 577
        if(j_0 < 16U)
        {
        }
        else
        {

#line 577
            break;
        }

#line 578
        r4_0(&(*r_1)[j_0], &(*r_1)[j_0 + 16U], &(*r_1)[j_0 + 32U], &(*r_1)[j_0 + 48U]);

#line 577
        j_0 = j_0 + 1U;

#line 577
    }

    thread array<float2, int(64)> o_0;

#line 579
    uint pp_0 = 0U;
    for(;;)
    {

#line 580
        if(pp_0 < 4U)
        {
        }
        else
        {

#line 580
            break;
        }

#line 581
        thread array<float2, int(16)> b_4;

#line 581
        j_0 = 0U;
        for(;;)
        {

#line 582
            if(j_0 < 16U)
            {
            }
            else
            {

#line 582
                break;
            }
            b_4[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f));

#line 582
            j_0 = j_0 + 1U;

#line 582
        }



        dft16_0(&b_4);

#line 586
        k_0 = 0U;
        for(;;)
        {

#line 587
            if(k_0 < 16U)
            {
            }
            else
            {

#line 587
                break;
            }

#line 587
            o_0[4U * k_0 + pp_0] = b_4[k_0];

#line 587
            k_0 = k_0 + 1U;

#line 587
        }

#line 580
        pp_0 = pp_0 + 1U;

#line 580
    }

#line 580
    k_0 = 0U;

#line 589
    for(;;)
    {

#line 589
        if(k_0 < 64U)
        {
        }
        else
        {

#line 589
            break;
        }

#line 589
        (*r_1)[k_0] = o_0[k_0];

#line 589
        k_0 = k_0 + 1U;

#line 589
    }
    return;
}


void dftR_0(array<float2, int(64)> thread* r_2)
{

#line 601
    dft64_0(r_2);

    return;
}


#line 269
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 271
    uint j_1 = d_2 / _S11;

#line 271
    uint m_0 = d_2 % _S11;

#line 271
    uint _S12;
    if(TB_0 <= 64U)
    {

#line 272
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

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


#line 256 "mm_65536_refineListed_lds32.slang"
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
void exchange_0(array<float2, int(64)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 699
    uint j_2;

#line 710
    thread array<float2, int(64)> out_0;

#line 710
    uint z_0 = 0U;
    for(;;)
    {

#line 711
        if(z_0 < 64U)
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
    uint _S16 = _S15 >> lgSpan_0;

#line 717
    uint _S17 = _S16 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 717
    uint c_1 = 0U;

    for(;;)
    {

#line 719
        if(c_1 < 16U)
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
        j_2 = 0U;
        for(;;)
        {

#line 721
            if(j_2 < 4U)
            {
            }
            else
            {

#line 721
                break;
            }

#line 721
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 4U + j_2], kernelContext_2);

#line 721
            j_2 = j_2 + 1U;

#line 721
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 722
        uint d_3 = 0U;
        for(;;)
        {

#line 723
            if(d_3 < 64U)
            {
            }
            else
            {

#line 723
                break;
            }

#line 724
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S18 = pz_0 & lenMask_0;

#line 725
            uint iz_0 = _S18 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S18 & spanMask_0);
            uint i_3 = _S16 + iz_0;
            uint _S19 = c_1 * 4U;

#line 728
            bool _S20;

#line 728
            if(i_3 >= _S19)
            {

#line 728
                _S20 = i_3 < ((c_1 + 1U) * 4U);

#line 728
            }
            else
            {

#line 728
                _S20 = false;

#line 728
            }

#line 728
            if(_S20)
            {

#line 728
                float2 _S21 = stgGet_0(_S17 + az_0 - _S19 * 1024U, kernelContext_2);
                out_0[d_3] = _S21;

#line 728
            }

#line 723
            d_3 = d_3 + 1U;

#line 723
        }

#line 719
        c_1 = c_1 + 1U;

#line 719
    }

#line 719
    j_2 = 0U;

#line 732
    for(;;)
    {

#line 732
        if(j_2 < 64U)
        {
        }
        else
        {

#line 732
            break;
        }

#line 732
        (*r_3)[j_2] = out_0[j_2];

#line 732
        j_2 = j_2 + 1U;

#line 732
    }
    return;
}


#line 534
void dft16at_0(array<float2, int(64)> thread* r_4, uint o_1)
{



    thread array<float2, int(16)> b_5;

#line 539
    uint i_4 = 0U;
    for(;;)
    {

#line 540
        if(i_4 < 16U)
        {
        }
        else
        {

#line 540
            break;
        }

#line 540
        b_5[i_4] = (*r_4)[o_1 + i_4];

#line 540
        i_4 = i_4 + 1U;

#line 540
    }
    dft16_0(&b_5);

#line 541
    i_4 = 0U;
    for(;;)
    {

#line 542
        if(i_4 < 16U)
        {
        }
        else
        {

#line 542
            break;
        }

#line 542
        (*r_4)[o_1 + i_4] = b_5[i_4];

#line 542
        i_4 = i_4 + 1U;

#line 542
    }

    return;
}


#line 612
void innermost_0(array<float2, int(64)> thread* r_5)
{

#line 612
    uint b_6 = 0U;

#line 617
    for(;;)
    {

#line 617
        if(b_6 < 4U)
        {
        }
        else
        {

#line 617
            break;
        }

#line 617
        dft16at_0(r_5, b_6 * 16U);

#line 617
        b_6 = b_6 + 1U;

#line 617
    }

#line 624
    return;
}


#line 788
void transform_0(array<float2, int(64)> thread* r_6, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 788
    uint _S22;

#line 788
    uint k2_1;

#line 788
    float cr_0;

#line 788
    float ci_0;

#line 788
    uint _S23;

#line 788
    for(;;)
    {

#line 788
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S22 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(65536U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;

#line 19
                dftR_0(r_6);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 6.5536e+04f);
                float _S24 = tw_0.x;

#line 27
                float _S25 = tw_0.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0f;

#line 27
                ci_0 = 0.0f;

                for(;;)
                {

#line 29
                    if(k2_1 < 64U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_6)[k2_1] = cmul_0((*r_6)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S24 - ci_0 * _S25;
                    float _S26 = cr_0 * _S25 + ci_0 * _S24;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S26;

#line 29
                }

#line 37
                uint per_2 = 64U / max(1024U, 1U);
                uint _S27 = max(16U, 1U);

#line 38
                _S23 = _S27;
                uint blk2_2 = tid_0 / _S27;

#line 39
                uint lane2_2 = tid_0 % _S27;

#line 39
                exchange_0(r_6, lgLn_0, lgTB_0, 1024U, 65536U, blk_2, lane_2, per_2, _S27, 1024U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(16U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 15U;

#line 19
                dftR_0(r_6);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 1024.0f);
                float _S28 = tw_1.x;

#line 27
                float _S29 = tw_1.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0f;

#line 27
                ci_0 = 0.0f;

                for(;;)
                {

#line 29
                    if(k2_1 < 64U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_6)[k2_1] = cmul_0((*r_6)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S28 - ci_0 * _S29;
                    float _S30 = cr_0 * _S29 + ci_0 * _S28;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S30;

#line 29
                }

#line 37
                uint per_3 = 64U / _S23;
                uint _S31 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S31;

#line 39
                uint lane2_3 = tid_0 % _S31;

#line 39
                exchange_0(r_6, _S22, lgTB_1, 16U, 1024U, blk_3, lane_3, per_3, _S31, 16U, blk2_3, lane2_3, kernelContext_3);

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
    innermost_0(r_6);

#line 791 "mm_65536_refineListed_lds32.slang"
    return;
}


#line 757
uint lgOf_0(uint i_5)
{

#line 757
    uint _S32;

#line 757
    if(i_5 < 2U)
    {

#line 757
        _S32 = 6U;

#line 757
    }
    else
    {

#line 757
        if(i_5 == 2U)
        {

#line 757
            _S32 = 4U;

#line 757
        }
        else
        {

#line 757
            _S32 = 1U;

#line 757
        }

#line 757
    }

#line 757
    return _S32;
}


#line 759
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 763
    uint lg_1 = lgOf_0(1U);

#line 763
    uint lg_2 = lgOf_0(0U);

#line 768
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 811
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 831
    kernelContext_4->_tid_0 = tid_1;
    uint _S33 = pair_0 / ntmpl_1;

#line 832
    uint _S34 = pair_0 % ntmpl_1;

#line 837
    thread array<float2, int(64)> r_7;

#line 837
    uint n2_0 = 0U;

#line 848
    for(;;)
    {

#line 848
        if(n2_0 < 64U)
        {
        }
        else
        {

#line 848
            break;
        }

#line 849
        uint idx_0 = tid_1 + 1024U * n2_0;
        r_7[n2_0] = cmulConj_0(cload_0(data_0, _S33 * 65536U + idx_0), cload_0(tmpl_0, _S34 * 65536U + idx_0));

#line 848
        n2_0 = n2_0 + 1U;

#line 848
    }

#line 848
    transform_0(&r_7, tid_1, kernelContext_4);

#line 877
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 877
    uint b_7 = tid_1;

#line 989
    for(;;)
    {

#line 989
        if(b_7 < nbins_1)
        {
        }
        else
        {

#line 989
            break;
        }

#line 989
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_7] = thrBits_1;

#line 989
        b_7 = b_7 + 1024U;

#line 989
    }
    bool _S35 = nbins_1 == 1U;

#line 990
    bool live_0;

#line 990
    if(_S35)
    {

#line 990
        live_0 = tid_1 == 0U;

#line 990
    }
    else
    {

#line 990
        live_0 = false;

#line 990
    }

#line 990
    if(live_0)
    {

#line 990
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 990
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(64)> myMag_0;
    thread array<uint, int(64)> myBin_0;

#line 995
    uint i_6 = 0U;



    for(;;)
    {

#line 999
        if(i_6 < 64U)
        {
        }
        else
        {

#line 999
            break;
        }

#line 1000
        uint idx_1 = slotToIndex_0(tid_1 * 64U + i_6);
        if(idx_1 >= winStart_2)
        {

#line 1001
            live_0 = idx_1 < winEnd_2;

#line 1001
        }
        else
        {

#line 1001
            live_0 = false;

#line 1001
        }



        float _rx_0 = r_7[i_6].x;

#line 1005
        float _ry_0 = r_7[i_6].y;
        if(live_0)
        {

#line 1006
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1006
        }
        else
        {

#line 1006
            n2_0 = 0U;

#line 1006
        }

#line 1006
        myMag_0[i_6] = n2_0;

#line 1014
        uint off_0 = idx_1 - winStart_2;

#line 1021
        if(live_0)
        {

#line 1021
            if(binShift_1 >= int(0))
            {

#line 1021
                b_7 = off_0 >> uint(binShift_1);

#line 1021
            }
            else
            {

#line 1021
                uint _S36 = off_0 / binsize_1;

#line 1021
                b_7 = _S36;

#line 1021
            }

#line 1021
        }
        else
        {

#line 1021
            b_7 = 0U;

#line 1021
        }

#line 1021
        myBin_0[i_6] = b_7;

#line 1021
        bool _S37;



        if(nbins_1 > 1U)
        {

#line 1025
            _S37 = (myMag_0[i_6]) > thrBits_1;

#line 1025
        }
        else
        {

#line 1025
            _S37 = false;

#line 1025
        }

#line 1025
        if(_S37)
        {

#line 1026
            uint _S38 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_6]])), myMag_0[i_6], memory_order_relaxed);

#line 1025
        }

#line 999
        i_6 = i_6 + 1U;

#line 999
    }

#line 999
    uint winner_0;

#line 1049
    if(_S35)
    {

#line 1049
        winner_0 = thrBits_1;

#line 1049
        i_6 = 0U;


        for(;;)
        {

#line 1052
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1052
                break;
            }

#line 1052
            uint _S39 = max(winner_0, myMag_0[i_6]);

#line 1052
            uint i_7 = i_6 + 1U;

#line 1052
            winner_0 = _S39;

#line 1052
            i_6 = i_7;

#line 1052
        }

        uint wm_0 = simd_max(winner_0);
        bool _S40 = simd_is_first();

#line 1055
        if(_S40)
        {

#line 1055
            live_0 = wm_0 > thrBits_1;

#line 1055
        }
        else
        {

#line 1055
            live_0 = false;

#line 1055
        }

#line 1055
        if(live_0)
        {

#line 1055
            uint _S41 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1055
        }

#line 1049
    }

#line 1070
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1077
    if(_S35)
    {

#line 1077
        winner_0 = 4294967295U;

#line 1077
        i_6 = 0U;


        for(;;)
        {

#line 1080
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1080
                break;
            }

#line 1081
            if((myMag_0[i_6]) > thrBits_1)
            {

#line 1081
                live_0 = (myMag_0[i_6]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 1081
            }
            else
            {

#line 1081
                live_0 = false;

#line 1081
            }

#line 1081
            if(live_0)
            {

#line 1081
                winner_0 = min(winner_0, tid_1 * 64U + i_6);

#line 1081
            }

#line 1080
            i_6 = i_6 + 1U;

#line 1080
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S42 = simd_is_first();

#line 1085
        if(_S42)
        {

#line 1085
            live_0 = waveWinner_0 != 4294967295U;

#line 1085
        }
        else
        {

#line 1085
            live_0 = false;

#line 1085
        }

#line 1085
        if(live_0)
        {

#line 1086
            uint _S43 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1085
        }

#line 1090
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1090
        i_6 = 0U;
        for(;;)
        {

#line 1091
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1091
                break;
            }

#line 1092
            uint _S44 = tid_1 * 64U + i_6;

#line 1092
            if(_S44 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 1093
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S44));

#line 1093
                *(peakVal_0+pair_0) = packed_float2(float2(r_7[i_6].x, r_7[i_6].y)) ;

#line 1092
            }

#line 1091
            i_6 = i_6 + 1U;

#line 1091
        }

#line 1101
        if(tid_1 == 0U)
        {

#line 1101
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1101
        }
        else
        {

#line 1101
            live_0 = false;

#line 1101
        }

#line 1101
        if(live_0)
        {

#line 1102
            *(peakIdx_0+pair_0) = int(-1);

#line 1102
            *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1101
        }

#line 1077
    }
    else
    {

#line 1077
        i_6 = 0U;

#line 1110
        for(;;)
        {

#line 1110
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1110
                break;
            }

#line 1111
            if((myMag_0[i_6]) > thrBits_1)
            {

#line 1111
                live_0 = (myMag_0[i_6]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_6]];

#line 1111
            }
            else
            {

#line 1111
                live_0 = false;

#line 1111
            }

#line 1111
            myMag_0[i_6] = uint(live_0);

#line 1110
            i_6 = i_6 + 1U;

#line 1110
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1113
        b_7 = tid_1;
        for(;;)
        {

#line 1114
            if(b_7 < nbins_1)
            {
            }
            else
            {

#line 1114
                break;
            }

#line 1114
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_7] = 4294967295U;

#line 1114
            b_7 = b_7 + 1024U;

#line 1114
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1115
        i_6 = 0U;
        for(;;)
        {

#line 1116
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1116
                break;
            }

#line 1117
            if((myMag_0[i_6]) != 0U)
            {

#line 1117
                uint _S45 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_6]])), tid_1 * 64U + i_6, memory_order_relaxed);

#line 1117
            }

#line 1116
            i_6 = i_6 + 1U;

#line 1116
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1118
        i_6 = 0U;
        for(;;)
        {

#line 1119
            if(i_6 < 64U)
            {
            }
            else
            {

#line 1119
                break;
            }

#line 1120
            if((myMag_0[i_6]) != 0U)
            {

#line 1120
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_6]]) == (tid_1 * 64U + i_6);

#line 1120
            }
            else
            {

#line 1120
                live_0 = false;

#line 1120
            }

#line 1120
            if(live_0)
            {

#line 1121
                uint o_2 = pair_0 * nbins_1 + myBin_0[i_6];
                *(peakIdx_0+o_2) = int(slotToIndex_0(tid_1 * 64U + i_6));

#line 1122
                *(peakVal_0+o_2) = packed_float2(float2(r_7[i_6].x, r_7[i_6].y)) ;

#line 1120
            }

#line 1119
            i_6 = i_6 + 1U;

#line 1119
        }

#line 1119
        b_7 = tid_1;

#line 1126
        for(;;)
        {

#line 1126
            if(b_7 < nbins_1)
            {
            }
            else
            {

#line 1126
                break;
            }

#line 1127
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_7]) == 4294967295U)
            {

#line 1128
                uint _S46 = pair_0 * nbins_1 + b_7;

#line 1128
                *(peakIdx_0+_S46) = int(-1);

#line 1128
                *(peakVal_0+_S46) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1127
            }

#line 1126
            b_7 = b_7 + 1024U;

#line 1126
        }

#line 1077
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
    threadgroup array<uint, int(8192)> stg_1;

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
