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


#line 152 "mm_1024_fullCorrelationSeries.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 152
    return float2(*(b_0+i_0)) ;
}


#line 252
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 252
    float _S2 = a_0.x;

#line 252
    float _S3 = b_1.x;

#line 252
    float _S4 = a_0.y;

#line 252
    float _S5 = b_1.y;

#line 252
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 457
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 459
    float2 t1_0 = *a_1 - *c_0;

#line 459
    float2 t2_0 = *b_2 + *d_0;

#line 459
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 461
    *b_2 = t1_0 + j3_0;

#line 461
    *c_0 = t0_0 - t2_0;

#line 461
    *d_0 = t1_0 - j3_0;
    return;
}


#line 251
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 251
    float _S6 = a_2.x;

#line 251
    float _S7 = b_3.x;

#line 251
    float _S8 = a_2.y;

#line 251
    float _S9 = b_3.y;

#line 251
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 493
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 500
    uint n1_0 = 0U;
    for(;;)
    {

#line 501
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 501
            break;
        }

#line 501
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 501
        n1_0 = n1_0 + 1U;

#line 501
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 502
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 502
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 503
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 503
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 504
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 504
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 504
    uint k2_0 = 0U;
    for(;;)
    {

#line 505
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 505
            break;
        }

#line 505
        uint _S10 = 4U * k2_0;

#line 505
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 505
        k2_0 = k2_0 + 1U;

#line 505
    }

    float2 t_0 = (*r_0)[int(1)];

#line 507
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 507
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 508
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 508
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 509
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 509
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 510
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 510
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 511
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 511
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 512
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 512
    (*r_0)[int(14)] = t_5;
    return;
}


#line 26 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 253 "mm_1024_fullCorrelationSeries.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 255
    uint j_0 = d_1 / _S11;

#line 255
    uint m_0 = d_1 % _S11;

#line 255
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 256
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 256
    }
    else
    {

#line 256
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 256
    }

#line 256
    return _S12;
}


#line 1410
struct EntryPointParams_0
{
    uint4 params_0;
};


#line 240
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 240
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 240
    uint _S13 = 2U * i_1;

#line 240
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13] = (as_type<uint>((v_0.x)));

#line 240
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13 + 1U] = (as_type<uint>((v_0.y)));

#line 240
    return;
}


#line 241
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 241
    uint _S14 = 2U * i_2;

#line 241
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 653
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 654
    uint j_1;

#line 665
    thread array<float2, int(16)> out_0;

#line 665
    uint z_0 = 0U;
    for(;;)
    {

#line 666
        if(z_0 < 16U)
        {
        }
        else
        {

#line 666
            break;
        }

#line 666
        out_0[z_0] = float2(0.0, 0.0);

#line 666
        z_0 = z_0 + 1U;

#line 666
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S15 = p0_0 & lenMask_0;

#line 672
    uint _S16 = (_S15 >> lgSpan_0) * 64U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 672
    uint c_1 = 0U;

    for(;;)
    {

#line 674
        if(c_1 < 1U)
        {
        }
        else
        {

#line 674
            break;
        }

#line 675
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 675
        j_1 = 0U;
        for(;;)
        {

#line 676
            if(j_1 < 16U)
            {
            }
            else
            {

#line 676
                break;
            }

#line 676
            stgPut_0(j_1 * 64U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 676
            j_1 = j_1 + 1U;

#line 676
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 677
        uint d_2 = 0U;
        for(;;)
        {

#line 678
            if(d_2 < 16U)
            {
            }
            else
            {

#line 678
                break;
            }

#line 679
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S17 = pz_0 & lenMask_0;
            uint az_0 = (_S17 >> lgSpan_0) * 64U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S17 & spanMask_0);

#line 681
            float2 _S18 = stgGet_0(_S16 + az_0 - c_1 * 16U * 64U, kernelContext_2);


            out_0[d_2] = _S18;

#line 678
            d_2 = d_2 + 1U;

#line 678
        }

#line 674
        c_1 = c_1 + 1U;

#line 674
    }

#line 674
    j_1 = 0U;

#line 687
    for(;;)
    {

#line 687
        if(j_1 < 16U)
        {
        }
        else
        {

#line 687
            break;
        }

#line 687
        (*r_1)[j_1] = out_0[j_1];

#line 687
        j_1 = j_1 + 1U;

#line 687
    }
    return;
}


#line 472
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 475
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 475
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 596
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 596
    uint b_4 = 0U;

#line 605
    for(;;)
    {

#line 605
        if(b_4 < 4U)
        {
        }
        else
        {

#line 605
            break;
        }

#line 605
        dft4_0(r_3, b_4 * 4U);

#line 605
        b_4 = b_4 + 1U;

#line 605
    }


    return;
}


#line 743
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 743
    uint _S19;

#line 743
    uint k2_1;

#line 743
    float cr_0;

#line 743
    float ci_0;

#line 743
    uint _S20;

#line 743
    for(;;)
    {

#line 743
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
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 1024.0);
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
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 64.0);
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

#line 746 "mm_1024_fullCorrelationSeries.slang"
    return;
}


#line 712
uint lgOf_0(uint i_3)
{

#line 712
    uint _S29;

#line 712
    if(i_3 < 2U)
    {

#line 712
        _S29 = 4U;

#line 712
    }
    else
    {

#line 712
        _S29 = 1U;

#line 712
    }

#line 712
    return _S29;
}


#line 714
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 718
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 718
    uint lg_2 = lgOf_0(1U);

#line 718
    uint lg_3 = lgOf_0(0U);

#line 723
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 1410
[[kernel]] void fullCorrelationSeries(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], uint device* entryPointParams_starts_1 [[buffer(3)]], packed_float2 device* entryPointParams_output_1 [[buffer(4)]])
{

#line 1410
    thread KernelContext_0 kernelContext_4;

#line 1410
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1410
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1410
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1410
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1410
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1410
    threadgroup array<uint, int(2048)> stg_1;

#line 1410
    (&kernelContext_4)->stg_0 = &stg_1;

#line 1415
    uint pair_0 = gid_0.x;

#line 1415
    uint tid_1 = lid_0.x;
    uint d_3 = pair_0 / entryPointParams_1->params_0.x;

#line 1416
    uint _S30 = pair_0 % entryPointParams_1->params_0.x;
    uint _S31 = (&kernelContext_4)->entryPointParams_starts_0[d_3];
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 1420
    uint i_4 = 0U;
    for(;;)
    {

#line 1421
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1421
            break;
        }

#line 1422
        uint idx_0 = tid_1 + 64U * i_4;
        r_5[i_4] = cmulConj_0(cload_0((&kernelContext_4)->entryPointParams_data_0, d_3 * 1024U + idx_0), cload_0((&kernelContext_4)->entryPointParams_tmpl_0, _S30 * 1024U + idx_0));

#line 1421
        i_4 = i_4 + 1U;

#line 1421
    }

#line 1421
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 1421
    i_4 = 0U;

#line 1426
    for(;;)
    {

#line 1426
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1426
            break;
        }

#line 1427
        uint lag_0 = slotToIndex_0(tid_1 * 16U + i_4);

#line 1427
        bool _S32;
        if(lag_0 >= (entryPointParams_1->params_0.z))
        {

#line 1428
            _S32 = lag_0 < (entryPointParams_1->params_0.w);

#line 1428
        }
        else
        {

#line 1428
            _S32 = false;

#line 1428
        }

#line 1428
        bool _S33;

#line 1428
        if(_S32)
        {

#line 1428
            _S33 = lag_0 < (entryPointParams_1->params_0.y - _S31);

#line 1428
        }
        else
        {

#line 1428
            _S33 = false;

#line 1428
        }

#line 1428
        if(_S33)
        {

#line 1428
            *((&kernelContext_4)->entryPointParams_output_0+(_S30 * entryPointParams_1->params_0.y + _S31 + lag_0)) = packed_float2(float2(r_5[i_4].x, r_5[i_4].y)) ;

#line 1428
        }

#line 1426
        i_4 = i_4 + 1U;

#line 1426
    }

#line 1431
    return;
}
