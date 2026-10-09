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


#line 152 "mm_65536_fullCorrelationSeries.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 152
    return float2(*(b_0+i_0)) ;
}


#line 207
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 207
    float _S2 = a_0.x;

#line 207
    float _S3 = b_1.x;

#line 207
    float _S4 = a_0.y;

#line 207
    float _S5 = b_1.y;

#line 207
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 374
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 376
    float2 t1_0 = *a_1 - *c_0;

#line 376
    float2 t2_0 = *b_2 + *d_0;

#line 376
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 378
    *b_2 = t1_0 + j3_0;

#line 378
    *c_0 = t0_0 - t2_0;

#line 378
    *d_0 = t1_0 - j3_0;
    return;
}


#line 12 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 206 "mm_65536_fullCorrelationSeries.slang"
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 206
    float _S6 = a_2.x;

#line 206
    float _S7 = b_3.x;

#line 206
    float _S8 = a_2.y;

#line 206
    float _S9 = b_3.y;

#line 206
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 410
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 417
    uint n1_0 = 0U;
    for(;;)
    {

#line 418
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 418
            break;
        }

#line 418
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 418
        n1_0 = n1_0 + 1U;

#line 418
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 419
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 419
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 420
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 420
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 421
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 421
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 421
    uint k2_0 = 0U;
    for(;;)
    {

#line 422
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 422
            break;
        }

#line 422
        uint _S10 = 4U * k2_0;

#line 422
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 422
        k2_0 = k2_0 + 1U;

#line 422
    }

    float2 t_0 = (*r_0)[int(1)];

#line 424
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 424
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 425
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 425
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 426
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 426
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 427
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 427
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 428
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 428
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 429
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 429
    (*r_0)[int(14)] = t_5;
    return;
}


#line 476
void dft64_0(array<float2, int(64)> thread* r_1)
{

#line 476
    uint k_0;

#line 476
    uint j_0 = 0U;

    for(;;)
    {

#line 478
        if(j_0 < 16U)
        {
        }
        else
        {

#line 478
            break;
        }

#line 479
        r4_0(&(*r_1)[j_0], &(*r_1)[j_0 + 16U], &(*r_1)[j_0 + 32U], &(*r_1)[j_0 + 48U]);

#line 478
        j_0 = j_0 + 1U;

#line 478
    }

    thread array<float2, int(64)> o_0;

#line 480
    uint pp_0 = 0U;
    for(;;)
    {

#line 481
        if(pp_0 < 4U)
        {
        }
        else
        {

#line 481
            break;
        }

#line 482
        thread array<float2, int(16)> b_4;

#line 482
        j_0 = 0U;
        for(;;)
        {

#line 483
            if(j_0 < 16U)
            {
            }
            else
            {

#line 483
                break;
            }
            b_4[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], mfTwiddle_0(6.28318548202514648 * float(pp_0 * j_0) / 64.0));

#line 483
            j_0 = j_0 + 1U;

#line 483
        }



        dft16_0(&b_4);

#line 487
        k_0 = 0U;
        for(;;)
        {

#line 488
            if(k_0 < 16U)
            {
            }
            else
            {

#line 488
                break;
            }

#line 488
            o_0[4U * k_0 + pp_0] = b_4[k_0];

#line 488
            k_0 = k_0 + 1U;

#line 488
        }

#line 481
        pp_0 = pp_0 + 1U;

#line 481
    }

#line 481
    k_0 = 0U;

#line 490
    for(;;)
    {

#line 490
        if(k_0 < 64U)
        {
        }
        else
        {

#line 490
            break;
        }

#line 490
        (*r_1)[k_0] = o_0[k_0];

#line 490
        k_0 = k_0 + 1U;

#line 490
    }
    return;
}


void dftR_0(array<float2, int(64)> thread* r_2)
{

#line 502
    dft64_0(r_2);

    return;
}


#line 1255
struct EntryPointParams_0
{
    uint4 params_0;
};


#line 195
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


#line 195
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 195
    uint _S11 = 2U * i_1;

#line 195
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11] = (as_type<uint>((v_0.x)));

#line 195
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11 + 1U] = (as_type<uint>((v_0.y)));

#line 195
    return;
}


#line 208
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 210
    uint j_1 = d_1 / _S12;

#line 210
    uint m_0 = d_1 % _S12;

#line 210
    uint _S13;
    if(TB_0 <= 64U)
    {

#line 211
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 211
    }
    else
    {

#line 211
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 211
    }

#line 211
    return _S13;
}


#line 196
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 196
    uint _S14 = 2U * i_2;

#line 196
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 570
void exchange_0(array<float2, int(64)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 571
    uint j_2;

#line 582
    thread array<float2, int(64)> out_0;

#line 582
    uint z_0 = 0U;
    for(;;)
    {

#line 583
        if(z_0 < 64U)
        {
        }
        else
        {

#line 583
            break;
        }

#line 583
        out_0[z_0] = float2(0.0, 0.0);

#line 583
        z_0 = z_0 + 1U;

#line 583
    }
    uint _S15 = (1U << lgSpan_0) - 1U;
    uint _S16 = (1U << lgLen_0) - 1U;

#line 585
    uint c_1 = 0U;
    for(;;)
    {

#line 586
        if(c_1 < 8U)
        {
        }
        else
        {

#line 586
            break;
        }

#line 587
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 587
        j_2 = 0U;
        for(;;)
        {

#line 588
            if(j_2 < 8U)
            {
            }
            else
            {

#line 588
                break;
            }

#line 588
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 8U + j_2], kernelContext_2);

#line 588
            j_2 = j_2 + 1U;

#line 588
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 589
        uint d_2 = 0U;
        for(;;)
        {

#line 590
            if(d_2 < 64U)
            {
            }
            else
            {

#line 590
                break;
            }

#line 591
            uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
            uint b_5 = p_0 >> lgLen_0;

#line 592
            uint rem_0 = p_0 & _S16;
            uint i_3 = rem_0 >> lgSpan_0;

#line 593
            uint ln_0 = rem_0 & _S15;
            uint _S17 = c_1 * 8U;

#line 594
            bool _S18;

#line 594
            if(i_3 >= _S17)
            {

#line 594
                _S18 = i_3 < ((c_1 + 1U) * 8U);

#line 594
            }
            else
            {

#line 594
                _S18 = false;

#line 594
            }

#line 594
            if(_S18)
            {

#line 594
                float2 _S19 = stgGet_0((i_3 - _S17) * 1024U + (b_5 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_2] = _S19;

#line 594
            }

#line 590
            d_2 = d_2 + 1U;

#line 590
        }

#line 586
        c_1 = c_1 + 1U;

#line 586
    }

#line 586
    j_2 = 0U;

#line 598
    for(;;)
    {

#line 598
        if(j_2 < 64U)
        {
        }
        else
        {

#line 598
            break;
        }

#line 598
        (*r_3)[j_2] = out_0[j_2];

#line 598
        j_2 = j_2 + 1U;

#line 598
    }
    return;
}


#line 435
void dft16at_0(array<float2, int(64)> thread* r_4, uint o_1)
{



    thread array<float2, int(16)> b_6;

#line 440
    uint i_4 = 0U;
    for(;;)
    {

#line 441
        if(i_4 < 16U)
        {
        }
        else
        {

#line 441
            break;
        }

#line 441
        b_6[i_4] = (*r_4)[o_1 + i_4];

#line 441
        i_4 = i_4 + 1U;

#line 441
    }
    dft16_0(&b_6);

#line 442
    i_4 = 0U;
    for(;;)
    {

#line 443
        if(i_4 < 16U)
        {
        }
        else
        {

#line 443
            break;
        }

#line 443
        (*r_4)[o_1 + i_4] = b_6[i_4];

#line 443
        i_4 = i_4 + 1U;

#line 443
    }

    return;
}


#line 513
void innermost_0(array<float2, int(64)> thread* r_5)
{

#line 513
    uint b_7 = 0U;

#line 518
    for(;;)
    {

#line 518
        if(b_7 < 4U)
        {
        }
        else
        {

#line 518
            break;
        }

#line 518
        dft16at_0(r_5, b_7 * 16U);

#line 518
        b_7 = b_7 + 1U;

#line 518
    }

#line 525
    return;
}


#line 654
void transform_0(array<float2, int(64)> thread* r_6, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 654
    uint _S20;

#line 654
    uint k2_1;

#line 654
    float cr_0;

#line 654
    float ci_0;

#line 654
    uint _S21;

#line 654
    for(;;)
    {

#line 654
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S20 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(65536U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;

#line 19
                dftR_0(r_6);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 6.5536e+04);
                float _S22 = tw_0.x;

#line 27
                float _S23 = tw_0.y;

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
                    float nr_0 = cr_0 * _S22 - ci_0 * _S23;
                    float _S24 = cr_0 * _S23 + ci_0 * _S22;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S24;

#line 29
                }

#line 37
                uint per_2 = 64U / max(1024U, 1U);
                uint _S25 = max(16U, 1U);

#line 38
                _S21 = _S25;
                uint blk2_2 = tid_0 / _S25;

#line 39
                uint lane2_2 = tid_0 % _S25;

#line 39
                exchange_0(r_6, lgLn_0, lgTB_0, 1024U, 65536U, blk_2, lane_2, per_2, _S25, 1024U, blk2_2, lane2_2, kernelContext_3);

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
                float _S26 = tw_1.x;

#line 27
                float _S27 = tw_1.y;

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
                    float nr_1 = cr_0 * _S26 - ci_0 * _S27;
                    float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S28;

#line 29
                }

#line 37
                uint per_3 = 64U / _S21;
                uint _S29 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S29;

#line 39
                uint lane2_3 = tid_0 % _S29;

#line 39
                exchange_0(r_6, _S20, lgTB_1, 16U, 1024U, blk_3, lane_3, per_3, _S29, 16U, blk2_3, lane2_3, kernelContext_3);

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

#line 657 "mm_65536_fullCorrelationSeries.slang"
    return;
}


#line 623
uint lgOf_0(uint i_5)
{

#line 623
    uint _S30;

#line 623
    if(i_5 < 2U)
    {

#line 623
        _S30 = 6U;

#line 623
    }
    else
    {

#line 623
        if(i_5 == 2U)
        {

#line 623
            _S30 = 4U;

#line 623
        }
        else
        {

#line 623
            _S30 = 1U;

#line 623
        }

#line 623
    }

#line 623
    return _S30;
}


#line 625
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 629
    uint lg_1 = lgOf_0(1U);

#line 629
    uint lg_2 = lgOf_0(0U);

#line 634
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1255
[[kernel]] void fullCorrelationSeries(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], uint device* entryPointParams_starts_1 [[buffer(3)]], packed_float2 device* entryPointParams_output_1 [[buffer(4)]])
{

#line 1255
    thread KernelContext_0 kernelContext_4;

#line 1255
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1255
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1255
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1255
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1255
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1255
    threadgroup array<uint, int(16384)> stg_1;

#line 1255
    (&kernelContext_4)->stg_0 = &stg_1;

#line 1260
    uint pair_0 = gid_0.x;

#line 1260
    uint tid_1 = lid_0.x;
    uint d_3 = pair_0 / entryPointParams_1->params_0.x;

#line 1261
    uint _S31 = pair_0 % entryPointParams_1->params_0.x;
    uint _S32 = (&kernelContext_4)->entryPointParams_starts_0[d_3];
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(64)> r_7;

#line 1265
    uint i_6 = 0U;
    for(;;)
    {

#line 1266
        if(i_6 < 64U)
        {
        }
        else
        {

#line 1266
            break;
        }

#line 1267
        uint idx_0 = tid_1 + 1024U * i_6;
        r_7[i_6] = cmulConj_0(cload_0((&kernelContext_4)->entryPointParams_data_0, d_3 * 65536U + idx_0), cload_0((&kernelContext_4)->entryPointParams_tmpl_0, _S31 * 65536U + idx_0));

#line 1266
        i_6 = i_6 + 1U;

#line 1266
    }

#line 1266
    transform_0(&r_7, tid_1, &kernelContext_4);

#line 1266
    i_6 = 0U;

#line 1271
    for(;;)
    {

#line 1271
        if(i_6 < 64U)
        {
        }
        else
        {

#line 1271
            break;
        }

#line 1272
        uint lag_0 = slotToIndex_0(tid_1 * 64U + i_6);

#line 1272
        bool _S33;
        if(lag_0 >= (entryPointParams_1->params_0.z))
        {

#line 1273
            _S33 = lag_0 < (entryPointParams_1->params_0.w);

#line 1273
        }
        else
        {

#line 1273
            _S33 = false;

#line 1273
        }

#line 1273
        bool _S34;

#line 1273
        if(_S33)
        {

#line 1273
            _S34 = lag_0 < (entryPointParams_1->params_0.y - _S32);

#line 1273
        }
        else
        {

#line 1273
            _S34 = false;

#line 1273
        }

#line 1273
        if(_S34)
        {

#line 1273
            *((&kernelContext_4)->entryPointParams_output_0+(_S31 * entryPointParams_1->params_0.y + _S32 + lag_0)) = packed_float2(float2(r_7[i_6].x, r_7[i_6].y)) ;

#line 1273
        }

#line 1271
        i_6 = i_6 + 1U;

#line 1271
    }

#line 1276
    return;
}
