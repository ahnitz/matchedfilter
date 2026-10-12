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


#line 168 "mm_65536_fullCorrelationSeries.slang"
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
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 475
    float2 t1_0 = *a_1 - *c_0;

#line 475
    float2 t2_0 = *b_2 + *d_0;

#line 475
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 477
    *b_2 = t1_0 + j3_0;

#line 477
    *c_0 = t0_0 - t2_0;

#line 477
    *d_0 = t1_0 - j3_0;
    return;
}


#line 64 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 267 "mm_65536_fullCorrelationSeries.slang"
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
            b_4[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], mfTwiddle_0(6.28318548202514648 * float(pp_0 * j_0) / 64.0));

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
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 271
    uint j_1 = d_1 / _S11;

#line 271
    uint m_0 = d_1 % _S11;

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
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 272
    }

#line 272
    return _S12;
}


#line 1652
struct EntryPointParams_0
{
    uint4 params_0;
};


#line 256
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
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
        out_0[z_0] = float2(0.0, 0.0);

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
        if(c_1 < 8U)
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
            if(j_2 < 8U)
            {
            }
            else
            {

#line 721
                break;
            }

#line 721
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 8U + j_2], kernelContext_2);

#line 721
            j_2 = j_2 + 1U;

#line 721
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 722
        uint d_2 = 0U;
        for(;;)
        {

#line 723
            if(d_2 < 64U)
            {
            }
            else
            {

#line 723
                break;
            }

#line 724
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S18 = pz_0 & lenMask_0;

#line 725
            uint iz_0 = _S18 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S18 & spanMask_0);
            uint i_3 = _S16 + iz_0;
            uint _S19 = c_1 * 8U;

#line 728
            bool _S20;

#line 728
            if(i_3 >= _S19)
            {

#line 728
                _S20 = i_3 < ((c_1 + 1U) * 8U);

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
                out_0[d_2] = _S21;

#line 728
            }

#line 723
            d_2 = d_2 + 1U;

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
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 6.5536e+04);
                float _S24 = tw_0.x;

#line 27
                float _S25 = tw_0.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

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
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 1024.0);
                float _S28 = tw_1.x;

#line 27
                float _S29 = tw_1.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

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

#line 791 "mm_65536_fullCorrelationSeries.slang"
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


#line 1652
[[kernel]] void fullCorrelationSeries(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], uint device* entryPointParams_starts_1 [[buffer(3)]], packed_float2 device* entryPointParams_output_1 [[buffer(4)]])
{

#line 1652
    thread KernelContext_0 kernelContext_4;

#line 1652
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1652
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1652
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1652
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1652
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1652
    threadgroup array<uint, int(16384)> stg_1;

#line 1652
    (&kernelContext_4)->stg_0 = &stg_1;

#line 1657
    uint pair_0 = gid_0.x;

#line 1657
    uint tid_1 = lid_0.x;
    uint d_3 = pair_0 / entryPointParams_1->params_0.x;

#line 1658
    uint _S33 = pair_0 % entryPointParams_1->params_0.x;
    uint _S34 = (&kernelContext_4)->entryPointParams_starts_0[d_3];
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(64)> r_7;

#line 1662
    uint i_6 = 0U;
    for(;;)
    {

#line 1663
        if(i_6 < 64U)
        {
        }
        else
        {

#line 1663
            break;
        }

#line 1664
        uint idx_0 = tid_1 + 1024U * i_6;
        r_7[i_6] = cmulConj_0(cload_0((&kernelContext_4)->entryPointParams_data_0, d_3 * 65536U + idx_0), cload_0((&kernelContext_4)->entryPointParams_tmpl_0, _S33 * 65536U + idx_0));

#line 1663
        i_6 = i_6 + 1U;

#line 1663
    }

#line 1663
    transform_0(&r_7, tid_1, &kernelContext_4);

#line 1663
    i_6 = 0U;

#line 1668
    for(;;)
    {

#line 1668
        if(i_6 < 64U)
        {
        }
        else
        {

#line 1668
            break;
        }

#line 1669
        uint lag_0 = slotToIndex_0(tid_1 * 64U + i_6);

#line 1669
        bool _S35;
        if(lag_0 >= (entryPointParams_1->params_0.z))
        {

#line 1670
            _S35 = lag_0 < (entryPointParams_1->params_0.w);

#line 1670
        }
        else
        {

#line 1670
            _S35 = false;

#line 1670
        }

#line 1670
        bool _S36;

#line 1670
        if(_S35)
        {

#line 1670
            _S36 = lag_0 < (entryPointParams_1->params_0.y - _S34);

#line 1670
        }
        else
        {

#line 1670
            _S36 = false;

#line 1670
        }

#line 1670
        if(_S36)
        {

#line 1670
            *((&kernelContext_4)->entryPointParams_output_0+(_S33 * entryPointParams_1->params_0.y + _S34 + lag_0)) = packed_float2(float2(r_7[i_6].x, r_7[i_6].y)) ;

#line 1670
        }

#line 1668
        i_6 = i_6 + 1U;

#line 1668
    }

#line 1673
    return;
}
