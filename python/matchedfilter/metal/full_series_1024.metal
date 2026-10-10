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


#line 162 "mm_1024_fullCorrelationSeries.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 162
    return float2(*(b_0+i_0)) ;
}


#line 262
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 262
    float _S2 = a_0.x;

#line 262
    float _S3 = b_1.x;

#line 262
    float _S4 = a_0.y;

#line 262
    float _S5 = b_1.y;

#line 262
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 467
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 469
    float2 t1_0 = *a_1 - *c_0;

#line 469
    float2 t2_0 = *b_2 + *d_0;

#line 469
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 471
    *b_2 = t1_0 + j3_0;

#line 471
    *c_0 = t0_0 - t2_0;

#line 471
    *d_0 = t1_0 - j3_0;
    return;
}


#line 261
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 261
    float _S6 = a_2.x;

#line 261
    float _S7 = b_3.x;

#line 261
    float _S8 = a_2.y;

#line 261
    float _S9 = b_3.y;

#line 261
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 503
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 510
    uint n1_0 = 0U;
    for(;;)
    {

#line 511
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 511
            break;
        }

#line 511
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 511
        n1_0 = n1_0 + 1U;

#line 511
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 512
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 512
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 513
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 513
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 514
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 514
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 514
    uint k2_0 = 0U;
    for(;;)
    {

#line 515
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 515
            break;
        }

#line 515
        uint _S10 = 4U * k2_0;

#line 515
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 515
        k2_0 = k2_0 + 1U;

#line 515
    }

    float2 t_0 = (*r_0)[int(1)];

#line 517
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 517
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 518
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 518
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 519
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 519
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 520
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 520
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 521
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 521
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 522
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 522
    (*r_0)[int(14)] = t_5;
    return;
}


#line 58 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 263 "mm_1024_fullCorrelationSeries.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 265
    uint j_0 = d_1 / _S11;

#line 265
    uint m_0 = d_1 % _S11;

#line 265
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 266
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 266
    }
    else
    {

#line 266
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 266
    }

#line 266
    return _S12;
}


#line 1478
struct EntryPointParams_0
{
    uint4 params_0;
};


#line 250
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


#line 250
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 250
    uint _S13 = 2U * i_1;

#line 250
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13] = (as_type<uint>((v_0.x)));

#line 250
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13 + 1U] = (as_type<uint>((v_0.y)));

#line 250
    return;
}


#line 251
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 251
    uint _S14 = 2U * i_2;

#line 251
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 663
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 664
    uint j_1;

#line 675
    thread array<float2, int(16)> out_0;

#line 675
    uint z_0 = 0U;
    for(;;)
    {

#line 676
        if(z_0 < 16U)
        {
        }
        else
        {

#line 676
            break;
        }

#line 676
        out_0[z_0] = float2(0.0, 0.0);

#line 676
        z_0 = z_0 + 1U;

#line 676
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S15 = p0_0 & lenMask_0;

#line 682
    uint _S16 = (_S15 >> lgSpan_0) * 64U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 682
    uint c_1 = 0U;

    for(;;)
    {

#line 684
        if(c_1 < 1U)
        {
        }
        else
        {

#line 684
            break;
        }

#line 685
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 685
        j_1 = 0U;
        for(;;)
        {

#line 686
            if(j_1 < 16U)
            {
            }
            else
            {

#line 686
                break;
            }

#line 686
            stgPut_0(j_1 * 64U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 686
            j_1 = j_1 + 1U;

#line 686
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 687
        uint d_2 = 0U;
        for(;;)
        {

#line 688
            if(d_2 < 16U)
            {
            }
            else
            {

#line 688
                break;
            }

#line 689
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S17 = pz_0 & lenMask_0;
            uint az_0 = (_S17 >> lgSpan_0) * 64U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S17 & spanMask_0);

#line 691
            float2 _S18 = stgGet_0(_S16 + az_0 - c_1 * 16U * 64U, kernelContext_2);


            out_0[d_2] = _S18;

#line 688
            d_2 = d_2 + 1U;

#line 688
        }

#line 684
        c_1 = c_1 + 1U;

#line 684
    }

#line 684
    j_1 = 0U;

#line 697
    for(;;)
    {

#line 697
        if(j_1 < 16U)
        {
        }
        else
        {

#line 697
            break;
        }

#line 697
        (*r_1)[j_1] = out_0[j_1];

#line 697
        j_1 = j_1 + 1U;

#line 697
    }
    return;
}


#line 482
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 485
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 485
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 606
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 606
    uint b_4 = 0U;

#line 615
    for(;;)
    {

#line 615
        if(b_4 < 4U)
        {
        }
        else
        {

#line 615
            break;
        }

#line 615
        dft4_0(r_3, b_4 * 4U);

#line 615
        b_4 = b_4 + 1U;

#line 615
    }


    return;
}


#line 753
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 753
    uint _S19;

#line 753
    uint k2_1;

#line 753
    float cr_0;

#line 753
    float ci_0;

#line 753
    uint _S20;

#line 753
    for(;;)
    {

#line 753
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

#line 756 "mm_1024_fullCorrelationSeries.slang"
    return;
}


#line 722
uint lgOf_0(uint i_3)
{

#line 722
    uint _S29;

#line 722
    if(i_3 < 2U)
    {

#line 722
        _S29 = 4U;

#line 722
    }
    else
    {

#line 722
        _S29 = 1U;

#line 722
    }

#line 722
    return _S29;
}


#line 724
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 728
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 728
    uint lg_2 = lgOf_0(1U);

#line 728
    uint lg_3 = lgOf_0(0U);

#line 733
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 1478
[[kernel]] void fullCorrelationSeries(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], uint device* entryPointParams_starts_1 [[buffer(3)]], packed_float2 device* entryPointParams_output_1 [[buffer(4)]])
{

#line 1478
    thread KernelContext_0 kernelContext_4;

#line 1478
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1478
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1478
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1478
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1478
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1478
    threadgroup array<uint, int(2048)> stg_1;

#line 1478
    (&kernelContext_4)->stg_0 = &stg_1;

#line 1483
    uint pair_0 = gid_0.x;

#line 1483
    uint tid_1 = lid_0.x;
    uint d_3 = pair_0 / entryPointParams_1->params_0.x;

#line 1484
    uint _S30 = pair_0 % entryPointParams_1->params_0.x;
    uint _S31 = (&kernelContext_4)->entryPointParams_starts_0[d_3];
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 1488
    uint i_4 = 0U;
    for(;;)
    {

#line 1489
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1489
            break;
        }

#line 1490
        uint idx_0 = tid_1 + 64U * i_4;
        r_5[i_4] = cmulConj_0(cload_0((&kernelContext_4)->entryPointParams_data_0, d_3 * 1024U + idx_0), cload_0((&kernelContext_4)->entryPointParams_tmpl_0, _S30 * 1024U + idx_0));

#line 1489
        i_4 = i_4 + 1U;

#line 1489
    }

#line 1489
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 1489
    i_4 = 0U;

#line 1494
    for(;;)
    {

#line 1494
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1494
            break;
        }

#line 1495
        uint lag_0 = slotToIndex_0(tid_1 * 16U + i_4);

#line 1495
        bool _S32;
        if(lag_0 >= (entryPointParams_1->params_0.z))
        {

#line 1496
            _S32 = lag_0 < (entryPointParams_1->params_0.w);

#line 1496
        }
        else
        {

#line 1496
            _S32 = false;

#line 1496
        }

#line 1496
        bool _S33;

#line 1496
        if(_S32)
        {

#line 1496
            _S33 = lag_0 < (entryPointParams_1->params_0.y - _S31);

#line 1496
        }
        else
        {

#line 1496
            _S33 = false;

#line 1496
        }

#line 1496
        if(_S33)
        {

#line 1496
            *((&kernelContext_4)->entryPointParams_output_0+(_S30 * entryPointParams_1->params_0.y + _S31 + lag_0)) = packed_float2(float2(r_5[i_4].x, r_5[i_4].y)) ;

#line 1496
        }

#line 1494
        i_4 = i_4 + 1U;

#line 1494
    }

#line 1499
    return;
}
