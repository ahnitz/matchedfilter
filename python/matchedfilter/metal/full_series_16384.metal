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


#line 152 "mm_16384_fullCorrelationSeries.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 152
    return float2(*(b_0+i_0)) ;
}


#line 226
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 226
    float _S2 = a_0.x;

#line 226
    float _S3 = b_1.x;

#line 226
    float _S4 = a_0.y;

#line 226
    float _S5 = b_1.y;

#line 226
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 393
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 395
    float2 t1_0 = *a_1 - *c_0;

#line 395
    float2 t2_0 = *b_2 + *d_0;

#line 395
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 397
    *b_2 = t1_0 + j3_0;

#line 397
    *c_0 = t0_0 - t2_0;

#line 397
    *d_0 = t1_0 - j3_0;
    return;
}


#line 225
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 225
    float _S6 = a_2.x;

#line 225
    float _S7 = b_3.x;

#line 225
    float _S8 = a_2.y;

#line 225
    float _S9 = b_3.y;

#line 225
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 429
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 436
    uint n1_0 = 0U;
    for(;;)
    {

#line 437
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 437
            break;
        }

#line 437
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 437
        n1_0 = n1_0 + 1U;

#line 437
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 438
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 438
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 439
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 439
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 440
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 440
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 440
    uint k2_0 = 0U;
    for(;;)
    {

#line 441
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 441
            break;
        }

#line 441
        uint _S10 = 4U * k2_0;

#line 441
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 441
        k2_0 = k2_0 + 1U;

#line 441
    }

    float2 t_0 = (*r_0)[int(1)];

#line 443
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 443
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 444
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 444
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 445
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 445
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 446
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 446
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 447
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 447
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 448
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 448
    (*r_0)[int(14)] = t_5;
    return;
}


#line 17 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 227 "mm_16384_fullCorrelationSeries.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 229
    uint j_0 = d_1 / _S11;

#line 229
    uint m_0 = d_1 % _S11;

#line 229
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 230
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 230
    }
    else
    {

#line 230
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 230
    }

#line 230
    return _S12;
}


#line 1280
struct EntryPointParams_0
{
    uint4 params_0;
};


#line 580
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


#line 567
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S13 = (1U << lgSpan_0) - 1U;
    uint _S14 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

#line 572
    uint d_2 = 0U;
    for(;;)
    {

#line 573
        if(d_2 < 16U)
        {
        }
        else
        {

#line 573
            break;
        }

#line 574
        uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
        uint rem_0 = p_0 & _S14;
        src_0[d_2] = (rem_0 >> lgSpan_0) * 1024U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S13);

#line 573
        d_2 = d_2 + 1U;

#line 573
    }

#line 578
    thread array<float, int(16)> xr_0;
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 579
    uint j_1 = 0U;
    for(;;)
    {

#line 580
        if(j_1 < 16U)
        {
        }
        else
        {

#line 580
            break;
        }

#line 580
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 1024U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].x)));

#line 580
        j_1 = j_1 + 1U;

#line 580
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 581
    d_2 = 0U;
    for(;;)
    {

#line 582
        if(d_2 < 16U)
        {
        }
        else
        {

#line 582
            break;
        }

#line 582
        xr_0[d_2] = (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]])));

#line 582
        d_2 = d_2 + 1U;

#line 582
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 583
    j_1 = 0U;
    for(;;)
    {

#line 584
        if(j_1 < 16U)
        {
        }
        else
        {

#line 584
            break;
        }

#line 584
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 1024U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].y)));

#line 584
        j_1 = j_1 + 1U;

#line 584
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 585
    d_2 = 0U;
    for(;;)
    {

#line 586
        if(d_2 < 16U)
        {
        }
        else
        {

#line 586
            break;
        }

#line 586
        (*r_1)[d_2] = float2(xr_0[d_2], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]]))));

#line 586
        d_2 = d_2 + 1U;

#line 586
    }
    return;
}


#line 408
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 411
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 411
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 532
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 532
    uint b_4 = 0U;

#line 541
    for(;;)
    {

#line 541
        if(b_4 < 4U)
        {
        }
        else
        {

#line 541
            break;
        }

#line 541
        dft4_0(r_3, b_4 * 4U);

#line 541
        b_4 = b_4 + 1U;

#line 541
    }


    return;
}


#line 679
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 679
    uint _S15;

#line 679
    uint k2_1;

#line 679
    float cr_0;

#line 679
    float ci_0;

#line 679
    uint _S16;

#line 679
    uint _S17;

#line 679
    uint _S18;

#line 679
    for(;;)
    {

#line 679
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S15 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(16384U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 16384.0);
                float _S19 = tw_0.x;

#line 27
                float _S20 = tw_0.y;

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
                    float nr_0 = cr_0 * _S19 - ci_0 * _S20;
                    float _S21 = cr_0 * _S20 + ci_0 * _S19;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S21;

#line 29
                }

#line 37
                uint per_2 = 16U / max(1024U, 1U);
                uint _S22 = max(64U, 1U);

#line 38
                _S16 = _S22;
                uint blk2_2 = tid_0 / _S22;

#line 39
                uint lane2_2 = tid_0 % _S22;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 1024U, 16384U, blk_2, lane_2, per_2, _S22, 1024U, blk2_2, lane2_2, kernelContext_1);

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
                _S17 = lgTB_1;

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 63U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 1024.0);
                float _S23 = tw_1.x;

#line 27
                float _S24 = tw_1.y;

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
                    float nr_1 = cr_0 * _S23 - ci_0 * _S24;
                    float _S25 = cr_0 * _S24 + ci_0 * _S23;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S25;

#line 29
                }

#line 37
                uint per_3 = 16U / _S16;
                uint _S26 = max(4U, 1U);

#line 38
                _S18 = _S26;
                uint blk2_3 = tid_0 / _S26;

#line 39
                uint lane2_3 = tid_0 % _S26;

#line 39
                exchange_0(r_4, _S15, lgTB_1, 64U, 1024U, blk_3, lane_3, per_3, _S26, 64U, blk2_3, lane2_3, kernelContext_1);

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
                float2 tw_2 = mfTwiddle_0(6.28318548202514648 * float(lane_4) / 64.0);
                float _S27 = tw_2.x;

#line 27
                float _S28 = tw_2.y;

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
                    float nr_2 = cr_0 * _S27 - ci_0 * _S28;
                    float _S29 = cr_0 * _S28 + ci_0 * _S27;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_2;

#line 29
                    ci_0 = _S29;

#line 29
                }

#line 37
                uint per_4 = 16U / _S18;
                uint _S30 = max(0U, 1U);
                uint blk2_4 = tid_0 / _S30;

#line 39
                uint lane2_4 = tid_0 % _S30;

#line 39
                exchange_0(r_4, _S17, lgTB_2, 4U, 64U, blk_4, lane_4, per_4, _S30, 4U, blk2_4, lane2_4, kernelContext_1);

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

#line 682 "mm_16384_fullCorrelationSeries.slang"
    return;
}


#line 648
uint lgOf_0(uint i_1)
{

#line 648
    uint _S31;

#line 648
    if(i_1 < 3U)
    {

#line 648
        _S31 = 4U;

#line 648
    }
    else
    {

#line 648
        _S31 = 1U;

#line 648
    }

#line 648
    return _S31;
}


#line 650
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(4U);

    uint x_0 = slot_0 >> lg_0;

#line 654
    uint lg_1 = lgOf_0(3U);

    uint x_1 = x_0 >> lg_1;

#line 654
    uint lg_2 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_2;

#line 654
    uint lg_3 = lgOf_0(1U);

#line 654
    uint lg_4 = lgOf_0(0U);

#line 659
    return (((((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | (x_2 & ((1U << lg_3) - 1U))) << lg_4) | ((x_2 >> lg_3) & ((1U << lg_4) - 1U));
}


#line 1280
[[kernel]] void fullCorrelationSeries(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], uint device* entryPointParams_starts_1 [[buffer(3)]], packed_float2 device* entryPointParams_output_1 [[buffer(4)]])
{

#line 1280
    thread KernelContext_0 kernelContext_2;

#line 1280
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 1280
    (&kernelContext_2)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1280
    (&kernelContext_2)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1280
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1280
    (&kernelContext_2)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1280
    threadgroup array<uint, int(16384)> stg_1;

#line 1280
    (&kernelContext_2)->stg_0 = &stg_1;

#line 1285
    uint pair_0 = gid_0.x;

#line 1285
    uint tid_1 = lid_0.x;
    uint d_3 = pair_0 / entryPointParams_1->params_0.x;

#line 1286
    uint _S32 = pair_0 % entryPointParams_1->params_0.x;
    uint _S33 = (&kernelContext_2)->entryPointParams_starts_0[d_3];
    (&kernelContext_2)->_tid_0 = tid_1;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 1290
    uint i_2 = 0U;
    for(;;)
    {

#line 1291
        if(i_2 < 16U)
        {
        }
        else
        {

#line 1291
            break;
        }

#line 1292
        uint idx_0 = tid_1 + 1024U * i_2;
        r_5[i_2] = cmulConj_0(cload_0((&kernelContext_2)->entryPointParams_data_0, d_3 * 16384U + idx_0), cload_0((&kernelContext_2)->entryPointParams_tmpl_0, _S32 * 16384U + idx_0));

#line 1291
        i_2 = i_2 + 1U;

#line 1291
    }

#line 1291
    transform_0(&r_5, tid_1, &kernelContext_2);

#line 1291
    i_2 = 0U;

#line 1296
    for(;;)
    {

#line 1296
        if(i_2 < 16U)
        {
        }
        else
        {

#line 1296
            break;
        }

#line 1297
        uint lag_0 = slotToIndex_0(tid_1 * 16U + i_2);

#line 1297
        bool _S34;
        if(lag_0 >= (entryPointParams_1->params_0.z))
        {

#line 1298
            _S34 = lag_0 < (entryPointParams_1->params_0.w);

#line 1298
        }
        else
        {

#line 1298
            _S34 = false;

#line 1298
        }

#line 1298
        bool _S35;

#line 1298
        if(_S34)
        {

#line 1298
            _S35 = lag_0 < (entryPointParams_1->params_0.y - _S33);

#line 1298
        }
        else
        {

#line 1298
            _S35 = false;

#line 1298
        }

#line 1298
        if(_S35)
        {

#line 1298
            *((&kernelContext_2)->entryPointParams_output_0+(_S32 * entryPointParams_1->params_0.y + _S33 + lag_0)) = packed_float2(float2(r_5[i_2].x, r_5[i_2].y)) ;

#line 1298
        }

#line 1296
        i_2 = i_2 + 1U;

#line 1296
    }

#line 1301
    return;
}
