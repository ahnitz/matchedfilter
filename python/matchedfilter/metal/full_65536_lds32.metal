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


#line 168 "mm_65536_fullCorrelation_lds32.slang"
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
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 477
    float2 t1_0 = *a_1 - *c_0;

#line 477
    float2 t2_0 = *b_2 + *d_0;

#line 477
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 479
    *b_2 = t1_0 + j3_0;

#line 479
    *c_0 = t0_0 - t2_0;

#line 479
    *d_0 = t1_0 - j3_0;
    return;
}


#line 72 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 269 "mm_65536_fullCorrelation_lds32.slang"
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


#line 577
void dft64_0(array<float2, int(64)> thread* r_1)
{

#line 577
    uint k_0;

#line 577
    uint j_0 = 0U;

    for(;;)
    {

#line 579
        if(j_0 < 16U)
        {
        }
        else
        {

#line 579
            break;
        }

#line 580
        r4_0(&(*r_1)[j_0], &(*r_1)[j_0 + 16U], &(*r_1)[j_0 + 32U], &(*r_1)[j_0 + 48U]);

#line 579
        j_0 = j_0 + 1U;

#line 579
    }

    thread array<float2, int(64)> o_0;

#line 581
    uint pp_0 = 0U;
    for(;;)
    {

#line 582
        if(pp_0 < 4U)
        {
        }
        else
        {

#line 582
            break;
        }

#line 583
        thread array<float2, int(16)> b_4;

#line 583
        j_0 = 0U;
        for(;;)
        {

#line 584
            if(j_0 < 16U)
            {
            }
            else
            {

#line 584
                break;
            }
            b_4[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f));

#line 584
            j_0 = j_0 + 1U;

#line 584
        }



        dft16_0(&b_4);

#line 588
        k_0 = 0U;
        for(;;)
        {

#line 589
            if(k_0 < 16U)
            {
            }
            else
            {

#line 589
                break;
            }

#line 589
            o_0[4U * k_0 + pp_0] = b_4[k_0];

#line 589
            k_0 = k_0 + 1U;

#line 589
        }

#line 582
        pp_0 = pp_0 + 1U;

#line 582
    }

#line 582
    k_0 = 0U;

#line 591
    for(;;)
    {

#line 591
        if(k_0 < 64U)
        {
        }
        else
        {

#line 591
            break;
        }

#line 591
        (*r_1)[k_0] = o_0[k_0];

#line 591
        k_0 = k_0 + 1U;

#line 591
    }
    return;
}


void dftR_0(array<float2, int(64)> thread* r_2)
{

#line 603
    dft64_0(r_2);

    return;
}


#line 271
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 273
    uint j_1 = d_1 / _S11;

#line 273
    uint m_0 = d_1 % _S11;

#line 273
    uint _S12;
    if(TB_0 <= 64U)
    {

#line 274
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 274
    }
    else
    {

#line 274
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 274
    }

#line 274
    return _S12;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
};


#line 258 "mm_65536_fullCorrelation_lds32.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
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
void exchange_0(array<float2, int(64)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 701
    uint j_2;

#line 712
    thread array<float2, int(64)> out_0;

#line 712
    uint z_0 = 0U;
    for(;;)
    {

#line 713
        if(z_0 < 64U)
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
        if(c_1 < 16U)
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
        j_2 = 0U;
        for(;;)
        {

#line 723
            if(j_2 < 4U)
            {
            }
            else
            {

#line 723
                break;
            }

#line 723
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 4U + j_2], kernelContext_2);

#line 723
            j_2 = j_2 + 1U;

#line 723
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 724
        uint d_2 = 0U;
        for(;;)
        {

#line 725
            if(d_2 < 64U)
            {
            }
            else
            {

#line 725
                break;
            }

#line 726
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
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
                out_0[d_2] = _S21;

#line 730
            }

#line 725
            d_2 = d_2 + 1U;

#line 725
        }

#line 721
        c_1 = c_1 + 1U;

#line 721
    }

#line 721
    j_2 = 0U;

#line 734
    for(;;)
    {

#line 734
        if(j_2 < 64U)
        {
        }
        else
        {

#line 734
            break;
        }

#line 734
        (*r_3)[j_2] = out_0[j_2];

#line 734
        j_2 = j_2 + 1U;

#line 734
    }
    return;
}


#line 536
void dft16at_0(array<float2, int(64)> thread* r_4, uint o_1)
{



    thread array<float2, int(16)> b_5;

#line 541
    uint i_4 = 0U;
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
        b_5[i_4] = (*r_4)[o_1 + i_4];

#line 542
        i_4 = i_4 + 1U;

#line 542
    }
    dft16_0(&b_5);

#line 543
    i_4 = 0U;
    for(;;)
    {

#line 544
        if(i_4 < 16U)
        {
        }
        else
        {

#line 544
            break;
        }

#line 544
        (*r_4)[o_1 + i_4] = b_5[i_4];

#line 544
        i_4 = i_4 + 1U;

#line 544
    }

    return;
}


#line 614
void innermost_0(array<float2, int(64)> thread* r_5)
{

#line 614
    uint b_6 = 0U;

#line 619
    for(;;)
    {

#line 619
        if(b_6 < 4U)
        {
        }
        else
        {

#line 619
            break;
        }

#line 619
        dft16at_0(r_5, b_6 * 16U);

#line 619
        b_6 = b_6 + 1U;

#line 619
    }

#line 626
    return;
}


#line 802
void transform_0(array<float2, int(64)> thread* r_6, uint tid_0, KernelContext_0 thread* kernelContext_3)
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

#line 805 "mm_65536_fullCorrelation_lds32.slang"
    return;
}


#line 759
uint lgOf_0(uint i_5)
{

#line 759
    uint _S32;

#line 759
    if(i_5 < 2U)
    {

#line 759
        _S32 = 6U;

#line 759
    }
    else
    {

#line 759
        if(i_5 == 2U)
        {

#line 759
            _S32 = 4U;

#line 759
        }
        else
        {

#line 759
            _S32 = 1U;

#line 759
        }

#line 759
    }

#line 759
    return _S32;
}


#line 761
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 765
    uint lg_1 = lgOf_0(1U);

#line 765
    uint lg_2 = lgOf_0(0U);

#line 770
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1708
[[kernel]] void fullCorrelation(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], packed_float2 device* entryPointParams_output_1 [[buffer(3)]])
{

#line 1708
    thread KernelContext_0 kernelContext_4;

#line 1708
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1708
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1708
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1708
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1708
    threadgroup array<uint, int(8192)> stg_1;

#line 1708
    (&kernelContext_4)->stg_0 = &stg_1;



    uint pair_0 = gid_0.x;

#line 1712
    uint tid_1 = lid_0.x;
    uint _S33 = pair_0 / entryPointParams_1->ntmpl_0;

#line 1713
    uint _S34 = pair_0 % entryPointParams_1->ntmpl_0;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(64)> r_7;

#line 1716
    uint i_6 = 0U;
    for(;;)
    {

#line 1717
        if(i_6 < 64U)
        {
        }
        else
        {

#line 1717
            break;
        }

#line 1718
        uint idx_0 = tid_1 + 1024U * i_6;
        r_7[i_6] = cmulConj_0(cload_0((&kernelContext_4)->entryPointParams_data_0, _S33 * 65536U + idx_0), cload_0((&kernelContext_4)->entryPointParams_tmpl_0, _S34 * 65536U + idx_0));

#line 1717
        i_6 = i_6 + 1U;

#line 1717
    }

#line 1717
    transform_0(&r_7, tid_1, &kernelContext_4);

#line 1717
    i_6 = 0U;

#line 1722
    for(;;)
    {

#line 1722
        if(i_6 < 64U)
        {
        }
        else
        {

#line 1722
            break;
        }

#line 1722
        *((&kernelContext_4)->entryPointParams_output_0+(pair_0 * 65536U + slotToIndex_0(tid_1 * 64U + i_6))) = packed_float2(float2(r_7[i_6].x, r_7[i_6].y)) ;

#line 1722
        i_6 = i_6 + 1U;

#line 1722
    }

    return;
}
