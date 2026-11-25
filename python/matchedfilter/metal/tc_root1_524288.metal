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


#line 2448 "tc_root1_524288.slang"
uint rootColumn_0(uint g_0, uint p_0)
{
    uint i_0 = p_0 >> 1U;

#line 2450
    uint _S2;
    if(g_0 == 0U)
    {

#line 2452
        if(p_0 == 0U)
        {

#line 2452
            return 0U;
        }

#line 2453
        if(p_0 == 1U)
        {

#line 2453
            return 256U;
        }
        if((p_0 & 1U) == 0U)
        {

#line 2455
            _S2 = i_0;

#line 2455
        }
        else
        {

#line 2455
            _S2 = 512U - i_0;

#line 2455
        }

#line 2455
        return _S2;
    }
    uint c_0 = g_0 * 4U + i_0;
    if((p_0 & 1U) == 0U)
    {

#line 2458
        _S2 = c_0;

#line 2458
    }
    else
    {

#line 2458
        _S2 = 512U - c_0;

#line 2458
    }

#line 2458
    return _S2;
}


uint rootMirror_0(uint g_1, uint p_1)
{

#line 2462
    bool _S3;

    if(g_1 == 0U)
    {

#line 2464
        _S3 = p_1 < 2U;

#line 2464
    }
    else
    {

#line 2464
        _S3 = false;

#line 2464
    }

#line 2464
    uint _S4;

#line 2464
    if(_S3)
    {

#line 2464
        _S4 = p_1;

#line 2464
    }
    else
    {

#line 2464
        _S4 = p_1 ^ 1U;

#line 2464
    }

#line 2464
    return _S4;
}


#line 2433
float2 rootProduct_0(packed_float2 device* data_0, packed_float2 device* tmpl_0, uint k_0, uint k0_0, uint k1_0, float scale_0)
{

#line 2434
    bool _S5;

    if(k_0 < k0_0)
    {

#line 2436
        _S5 = true;

#line 2436
    }
    else
    {

#line 2436
        _S5 = k_0 >= k1_0;

#line 2436
    }

#line 2436
    if(_S5)
    {

#line 2437
        return float2(0.0f, 0.0f);
    }

#line 2437
    float2 _S6 = float2(*(data_0+k_0)) ;

#line 2437
    float2 _S7 = float2(*(tmpl_0+k_0)) ;

    if(k_0 == 0U)
    {

#line 2439
        _S5 = true;

#line 2439
    }
    else
    {

#line 2439
        _S5 = k_0 == 524288U;

#line 2439
    }

#line 2439
    float im_0;

#line 2439
    if(_S5)
    {

#line 2439
        im_0 = 0.0f;

#line 2439
    }
    else
    {

#line 2439
        im_0 = scale_0 * (_S7.x * _S6.y - _S7.y * _S6.x);

#line 2439
    }
    return float2(scale_0 * (_S7.x * _S6.x + _S7.y * _S6.y), im_0);
}


#line 103 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 610 "tc_root1_524288.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_1, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_1;

#line 612
    float2 t1_0 = *a_0 - *c_1;

#line 612
    float2 t2_0 = *b_0 + *d_0;

#line 612
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 614
    *b_0 = t1_0 + j3_0;

#line 614
    *c_1 = t0_0 - t2_0;

#line 614
    *d_0 = t1_0 - j3_0;
    return;
}


#line 323
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 323
    float _S8 = a_1.x;

#line 323
    float _S9 = b_1.x;

#line 323
    float _S10 = a_1.y;

#line 323
    float _S11 = b_1.y;

#line 323
    return float2(_S8 * _S9 - _S10 * _S11, _S8 * _S11 + _S10 * _S9);
}


#line 646
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 653
    uint n1_0 = 0U;
    for(;;)
    {

#line 654
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 654
            break;
        }

#line 654
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 654
        n1_0 = n1_0 + 1U;

#line 654
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 655
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 655
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 656
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 656
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 657
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 657
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 657
    uint k2_0 = 0U;
    for(;;)
    {

#line 658
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 658
            break;
        }

#line 658
        uint _S12 = 4U * k2_0;

#line 658
        r4_0(&(*r_0)[_S12], &(*r_0)[_S12 + 1U], &(*r_0)[_S12 + 2U], &(*r_0)[_S12 + 3U]);

#line 658
        k2_0 = k2_0 + 1U;

#line 658
    }

    float2 t_0 = (*r_0)[int(1)];

#line 660
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 660
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 661
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 661
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 662
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 662
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 663
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 663
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 664
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 664
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 665
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 665
    (*r_0)[int(14)] = t_5;
    return;
}


#line 325
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S13 = max(TB_0, 1U);

#line 327
    uint j_0 = d_1 / _S13;

#line 327
    uint m_0 = d_1 % _S13;

#line 327
    uint _S14;
    if(TB_0 <= 16U)
    {

#line 328
        _S14 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 328
    }
    else
    {

#line 328
        _S14 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 328
    }

#line 328
    return _S14;
}


#line 328
struct EntryPointParams_0
{
    uint slot_0;
};


#line 311
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    uint device* entryPointParams_params_0;
    packed_float2 device* entryPointParams_scratch_0;
    array<uint, int(8192)> threadgroup* stg_0;
    uint _tid_0;
    uint _stgBase_0;
};


#line 312
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 312
    uint _S15 = 2U * i_1;

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S15] = (as_type<uint>((v_0.x)));

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S15 + 1U] = (as_type<uint>((v_0.y)));

#line 312
    return;
}


#line 313
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 313
    uint _S16 = 2U * i_2;

#line 313
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S16]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S16 + 1U]))));
}


#line 625
void dft4_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    r4_0(&(*r_1)[o_0], &(*r_1)[o_0 + 1U], &(*r_1)[o_0 + 2U], &(*r_1)[o_0 + 3U]);
    float2 t_6 = (*r_1)[o_0 + 1U];

#line 628
    (*r_1)[o_0 + 1U] = (*r_1)[o_0 + 2U];

#line 628
    (*r_1)[o_0 + 2U] = t_6;
    return;
}


#line 749
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 749
    uint b_2 = 0U;

#line 758
    for(;;)
    {

#line 758
        if(b_2 < 4U)
        {
        }
        else
        {

#line 758
            break;
        }

#line 758
        dft4_0(r_2, b_2 * 4U);

#line 758
        b_2 = b_2 + 1U;

#line 758
    }


    return;
}


#line 877
uint lgOf_0(uint i_3)
{

#line 877
    uint _S17;

#line 877
    if(i_3 < 2U)
    {

#line 877
        _S17 = 4U;

#line 877
    }
    else
    {

#line 877
        _S17 = 1U;

#line 877
    }

#line 877
    return _S17;
}


#line 879
uint slotToIndex_0(uint slot_1)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_1 >> lg_0;

#line 883
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 883
    uint lg_2 = lgOf_0(1U);

#line 883
    uint lg_3 = lgOf_0(0U);

#line 888
    return (((((((0U << lg_0) | (slot_1 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 2469
void rootStageOut_0(const array<float2, int(16)> thread* r_3, uint tid_0, uint col_0, uint p_2, KernelContext_0 thread* kernelContext_2)
{

#line 2469
    uint i_4 = 0U;

    for(;;)
    {

#line 2471
        if(i_4 < 16U)
        {
        }
        else
        {

#line 2471
            break;
        }

#line 2472
        uint row_0 = slotToIndex_0(tid_0 * 16U + i_4);
        if((row_0 / 256U) == p_2)
        {

#line 2474
            uint a_2 = row_0 % 256U * 9U + col_0;

#line 2474
            float2 _S18 = (*r_3)[i_4];
            (*kernelContext_2->stg_0)[a_2] = (as_type<uint>(((*r_3)[i_4].x)));
            (*kernelContext_2->stg_0)[a_2 + 2304U] = (as_type<uint>((_S18.y)));

#line 2473
        }

#line 2471
        i_4 = i_4 + 1U;

#line 2471
    }

#line 2479
    return;
}



[[kernel]] void tcRootStage1(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], uint device* entryPointParams_params_1 [[buffer(3)]], packed_float2 device* entryPointParams_scratch_1 [[buffer(4)]])
{

#line 2484
    uint half_0;

#line 2484
    uint z_0;

#line 2484
    uint mm_0;

#line 2484
    uint s_0;

#line 2484
    uint _S19;

#line 2484
    float cr_0;

#line 2484
    float ci_0;

#line 2484
    uint _S20;

#line 2484
    uint _S21;

#line 2484
    uint d_2;

#line 2484
    uint j_1;

#line 2484
    bool _S22;

#line 2484
    thread KernelContext_0 kernelContext_3;

#line 2484
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 2484
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2484
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2484
    (&kernelContext_3)->entryPointParams_params_0 = entryPointParams_params_1;

#line 2484
    (&kernelContext_3)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 2484
    threadgroup array<uint, int(8192)> stg_1;

#line 2484
    (&kernelContext_3)->stg_0 = &stg_1;

#line 2489
    uint g_2 = gid_0.x;
    uint l_0 = lid_0.x;

#line 2490
    uint col_1 = l_0 / 64U;

#line 2490
    uint tid_1 = l_0 % 64U;
    uint _S23 = rootColumn_0(g_2, col_1);

#line 2491
    uint _S24 = rootMirror_0(g_2, col_1);
    uint _S25 = entryPointParams_params_1[4U * entryPointParams_1->slot_0];

#line 2492
    uint _S26 = entryPointParams_params_1[4U * entryPointParams_1->slot_0 + 1U];
    float _S27 = (as_type<float>((entryPointParams_params_1[4U * entryPointParams_1->slot_0 + 2U])));

#line 2499
    thread array<float2, int(16)> r_4;

#line 2499
    uint q_0 = 0U;

    for(;;)
    {

#line 2501
        if(q_0 < 4U)
        {
        }
        else
        {

#line 2501
            break;
        }

#line 2502
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2502
        s_0 = 0U;
        for(;;)
        {

#line 2503
            if(s_0 < 4U)
            {
            }
            else
            {

#line 2503
                break;
            }

#line 2504
            uint e_0 = l_0 + 512U * s_0;
            uint half_1 = e_0 / 1024U;

#line 2505
            uint w_0 = e_0 % 1024U;
            uint rr_0 = w_0 / 8U;

#line 2506
            uint p_3 = w_0 % 8U;
            if(half_1 == 0U)
            {

#line 2507
                half_0 = q_0;

#line 2507
            }
            else
            {

#line 2507
                half_0 = 7U - q_0;

#line 2507
            }

#line 2507
            float2 _S28 = rootProduct_0((&kernelContext_3)->entryPointParams_data_0, (&kernelContext_3)->entryPointParams_tmpl_0, rootColumn_0(g_2, p_3) + 512U * (half_0 * 128U + rr_0), _S25, _S26, _S27);

            uint a_3 = half_1 * 2U * 1152U + rr_0 * 9U + p_3;
            (*(&kernelContext_3)->stg_0)[a_3] = (as_type<uint>((_S28.x)));
            (*(&kernelContext_3)->stg_0)[a_3 + 1152U] = (as_type<uint>((_S28.y)));

#line 2503
            s_0 = s_0 + 1U;

#line 2503
        }

#line 2513
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2513
        half_0 = 0U;
        for(;;)
        {

#line 2514
            if(half_0 < 2U)
            {
            }
            else
            {

#line 2514
                break;
            }

#line 2515
            if(half_0 == 0U)
            {

#line 2515
                z_0 = q_0;

#line 2515
            }
            else
            {

#line 2515
                z_0 = 7U - q_0;

#line 2515
            }

#line 2515
            mm_0 = 0U;
            for(;;)
            {

#line 2516
                if(mm_0 < 2U)
                {
                }
                else
                {

#line 2516
                    break;
                }

#line 2517
                uint m_1 = z_0 * 2U + mm_0;
                uint rr_1 = tid_1 + 64U * mm_0;
                uint a_4 = half_0 * 2U * 1152U + rr_1 * 9U + col_1;
                float _S29 = (as_type<float>(((*(&kernelContext_3)->stg_0)[a_4])));

#line 2520
                float _S30 = (as_type<float>(((*(&kernelContext_3)->stg_0)[a_4 + 1152U])));
                uint j_2 = _S23 + 512U * (tid_1 + 64U * m_1);

#line 2521
                float2 pb_0;

                if(_S23 == 0U)
                {

#line 2523
                    pb_0 = rootProduct_0((&kernelContext_3)->entryPointParams_data_0, (&kernelContext_3)->entryPointParams_tmpl_0, 524288U - j_2, _S25, _S26, _S27);

#line 2523
                }
                else
                {

                    uint b_3 = (1U - half_0) * 2U * 1152U + (127U - rr_1) * 9U + _S24;

#line 2527
                    pb_0 = float2((as_type<float>(((*(&kernelContext_3)->stg_0)[b_3]))), (as_type<float>(((*(&kernelContext_3)->stg_0)[b_3 + 1152U]))));

#line 2523
                }

#line 2530
                float _S31 = pb_0.x;

#line 2530
                float _S32 = pb_0.y;

#line 2530
                float er_0 = _S29 - _S31;

#line 2530
                float ei_0 = _S30 + _S32;
                float2 w_1 = mfTwiddle_0(3.14159274101257324f * float(j_2) / 5.24288e+05f);
                float _S33 = w_1.x;

#line 2532
                float _S34 = w_1.y;
                r_4[m_1] = float2(_S29 + _S31 - (_S33 * ei_0 + _S34 * er_0), _S30 - _S32 + (_S33 * er_0 - _S34 * ei_0));

#line 2516
                mm_0 = mm_0 + 1U;

#line 2516
            }

#line 2514
            half_0 = half_0 + 1U;

#line 2514
        }

#line 2501
        q_0 = q_0 + 1U;

#line 2501
    }

#line 2537
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (&kernelContext_3)->_tid_0 = tid_1;
    (&kernelContext_3)->_stgBase_0 = col_1 * 1024U;
    for(;;)
    {

#line 2540
        for(;;)
        {

#line 2540
            for(;;)
            {

#line 2540
                for(;;)
                {

#line 2540
                    uint lgTB_0 = firstbithigh_0(64U);

#line 2540
                    _S19 = lgTB_0;

#line 2540
                    uint lgLn_0 = firstbithigh_0(1024U);

#line 2540
                    uint blk_1 = tid_1 >> lgTB_0;

#line 2540
                    uint lane_1 = tid_1 & 63U;

#line 2540
                    dft16_0(&r_4);

#line 2540
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 1024.0f);

#line 2540
                    float _S35 = tw_0.x;

#line 2540
                    float _S36 = tw_0.y;

#line 2540
                    half_0 = 0U;

#line 2540
                    cr_0 = 1.0f;

#line 2540
                    ci_0 = 0.0f;

#line 2540
                    for(;;)
                    {

#line 2540
                        if(half_0 < 16U)
                        {
                        }
                        else
                        {

#line 2540
                            break;
                        }

#line 2540
                        r_4[half_0] = cmul_0(r_4[half_0], float2(cr_0, ci_0));

#line 2540
                        float nr_0 = cr_0 * _S35 - ci_0 * _S36;

#line 2540
                        float _S37 = cr_0 * _S36 + ci_0 * _S35;

#line 2540
                        half_0 = half_0 + 1U;

#line 2540
                        cr_0 = nr_0;

#line 2540
                        ci_0 = _S37;

#line 2540
                    }

#line 2540
                    uint per_1 = 16U / max(64U, 1U);

#line 2540
                    uint _S38 = max(4U, 1U);

#line 2540
                    _S20 = _S38;

#line 2540
                    uint blk2_1 = tid_1 / _S38;

#line 2540
                    uint lane2_1 = tid_1 % _S38;

#line 2540
                    for(;;)
                    {

#line 2540
                        thread array<float2, int(16)> out_0;

#line 2540
                        z_0 = 0U;

#line 2540
                        for(;;)
                        {

#line 2540
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2540
                                break;
                            }

#line 2540
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2540
                            z_0 = z_0 + 1U;

#line 2540
                        }

#line 2540
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2540
                        _S21 = spanMask_0;

#line 2540
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2540
                        uint p0_0 = computeWant_0(0U, 64U, 1024U, blk_1, lane_1, per_1, _S38, 64U, blk2_1, lane2_1);

#line 2540
                        uint _S39 = p0_0 & lenMask_0;

#line 2540
                        uint _S40 = _S39 >> lgTB_0;

#line 2540
                        uint _S41 = _S40 * 64U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S39 & spanMask_0);

#line 2540
                        mm_0 = 0U;

#line 2540
                        for(;;)
                        {

#line 2540
                            if(mm_0 < 2U)
                            {
                            }
                            else
                            {

#line 2540
                                break;
                            }

#line 2540
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2540
                            j_1 = 0U;

#line 2540
                            for(;;)
                            {

#line 2540
                                if(j_1 < 8U)
                                {
                                }
                                else
                                {

#line 2540
                                    break;
                                }

#line 2540
                                stgPut_0(j_1 * 64U + (&kernelContext_3)->_tid_0, r_4[mm_0 * 8U + j_1], &kernelContext_3);

#line 2540
                                j_1 = j_1 + 1U;

#line 2540
                            }

#line 2540
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2540
                            d_2 = 0U;

#line 2540
                            for(;;)
                            {

#line 2540
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2540
                                    break;
                                }

#line 2540
                                uint pz_0 = computeWant_0(d_2, 64U, 1024U, 0U, 0U, per_1, _S38, 64U, 0U, 0U);

#line 2540
                                uint _S42 = pz_0 & lenMask_0;

#line 2540
                                uint iz_0 = _S42 >> lgTB_0;

#line 2540
                                uint az_0 = iz_0 * 64U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S42 & spanMask_0);

#line 2540
                                uint i_5 = _S40 + iz_0;

#line 2540
                                uint _S43 = mm_0 * 8U;

#line 2540
                                if(i_5 >= _S43)
                                {

#line 2540
                                    _S22 = i_5 < ((mm_0 + 1U) * 8U);

#line 2540
                                }
                                else
                                {

#line 2540
                                    _S22 = false;

#line 2540
                                }

#line 2540
                                if(_S22)
                                {

#line 2540
                                    float2 _S44 = stgGet_0(_S41 + az_0 - _S43 * 64U, &kernelContext_3);

#line 2540
                                    out_0[d_2] = _S44;

#line 2540
                                }

#line 2540
                                d_2 = d_2 + 1U;

#line 2540
                            }

#line 2540
                            mm_0 = mm_0 + 1U;

#line 2540
                        }

#line 2540
                        d_2 = 0U;

#line 2540
                        for(;;)
                        {

#line 2540
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2540
                                break;
                            }

#line 2540
                            r_4[d_2] = out_0[d_2];

#line 2540
                            d_2 = d_2 + 1U;

#line 2540
                        }

#line 2540
                        break;
                    }

#line 2540
                    break;
                }

#line 2540
                break;
            }

#line 2540
            for(;;)
            {

#line 2540
                for(;;)
                {

#line 2540
                    uint lgTB_1 = firstbithigh_0(4U);

#line 2540
                    uint blk_2 = tid_1 >> lgTB_1;

#line 2540
                    uint lane_2 = tid_1 & 3U;

#line 2540
                    dft16_0(&r_4);

#line 2540
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 64.0f);

#line 2540
                    float _S45 = tw_1.x;

#line 2540
                    float _S46 = tw_1.y;

#line 2540
                    half_0 = 0U;

#line 2540
                    cr_0 = 1.0f;

#line 2540
                    ci_0 = 0.0f;

#line 2540
                    for(;;)
                    {

#line 2540
                        if(half_0 < 16U)
                        {
                        }
                        else
                        {

#line 2540
                            break;
                        }

#line 2540
                        r_4[half_0] = cmul_0(r_4[half_0], float2(cr_0, ci_0));

#line 2540
                        float nr_1 = cr_0 * _S45 - ci_0 * _S46;

#line 2540
                        float _S47 = cr_0 * _S46 + ci_0 * _S45;

#line 2540
                        half_0 = half_0 + 1U;

#line 2540
                        cr_0 = nr_1;

#line 2540
                        ci_0 = _S47;

#line 2540
                    }

#line 2540
                    uint per_2 = 16U / _S20;

#line 2540
                    uint _S48 = max(0U, 1U);

#line 2540
                    uint blk2_2 = tid_1 / _S48;

#line 2540
                    uint lane2_2 = tid_1 % _S48;

#line 2540
                    for(;;)
                    {

#line 2540
                        thread array<float2, int(16)> out_1;

#line 2540
                        z_0 = 0U;

#line 2540
                        for(;;)
                        {

#line 2540
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2540
                                break;
                            }

#line 2540
                            out_1[z_0] = float2(0.0f, 0.0f);

#line 2540
                            z_0 = z_0 + 1U;

#line 2540
                        }

#line 2540
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2540
                        uint p0_1 = computeWant_0(0U, 4U, 64U, blk_2, lane_2, per_2, _S48, 4U, blk2_2, lane2_2);

#line 2540
                        uint _S49 = p0_1 & _S21;

#line 2540
                        uint _S50 = _S49 >> lgTB_1;

#line 2540
                        uint _S51 = _S50 * 64U + ((p0_1 >> _S19) << lgTB_1) + (_S49 & spanMask_1);

#line 2540
                        mm_0 = 0U;

#line 2540
                        for(;;)
                        {

#line 2540
                            if(mm_0 < 2U)
                            {
                            }
                            else
                            {

#line 2540
                                break;
                            }

#line 2540
                            bool _S52 = mm_0 == 0U;

#line 2540
                            if(!_S52)
                            {

#line 2540
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2540
                            }
                            else
                            {

#line 2540
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2540
                            }

#line 2540
                            j_1 = 0U;

#line 2540
                            for(;;)
                            {

#line 2540
                                if(j_1 < 8U)
                                {
                                }
                                else
                                {

#line 2540
                                    break;
                                }

#line 2540
                                stgPut_0(j_1 * 64U + (&kernelContext_3)->_tid_0, r_4[mm_0 * 8U + j_1], &kernelContext_3);

#line 2540
                                j_1 = j_1 + 1U;

#line 2540
                            }

#line 2540
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2540
                            d_2 = 0U;

#line 2540
                            for(;;)
                            {

#line 2540
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2540
                                    break;
                                }

#line 2540
                                uint pz_1 = computeWant_0(d_2, 4U, 64U, 0U, 0U, per_2, _S48, 4U, 0U, 0U);

#line 2540
                                uint _S53 = pz_1 & _S21;

#line 2540
                                uint iz_1 = _S53 >> lgTB_1;

#line 2540
                                uint az_1 = iz_1 * 64U + ((pz_1 >> _S19) << lgTB_1) + (_S53 & spanMask_1);

#line 2540
                                uint i_6 = _S50 + iz_1;

#line 2540
                                uint _S54 = mm_0 * 8U;

#line 2540
                                if(i_6 >= _S54)
                                {

#line 2540
                                    _S22 = i_6 < ((mm_0 + 1U) * 8U);

#line 2540
                                }
                                else
                                {

#line 2540
                                    _S22 = false;

#line 2540
                                }

#line 2540
                                if(_S22)
                                {

#line 2540
                                    float2 _S55 = stgGet_0(_S51 + az_1 - _S54 * 64U, &kernelContext_3);

#line 2540
                                    out_1[d_2] = _S55;

#line 2540
                                }

#line 2540
                                d_2 = d_2 + 1U;

#line 2540
                            }

#line 2540
                            mm_0 = mm_0 + 1U;

#line 2540
                        }

#line 2540
                        d_2 = 0U;

#line 2540
                        for(;;)
                        {

#line 2540
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2540
                                break;
                            }

#line 2540
                            r_4[d_2] = out_1[d_2];

#line 2540
                            d_2 = d_2 + 1U;

#line 2540
                        }

#line 2540
                        break;
                    }

#line 2540
                    break;
                }

#line 2540
                break;
            }

#line 2540
            break;
        }

#line 2540
        innermost_0(&r_4);

#line 2540
        break;
    }

#line 2540
    j_1 = 0U;

    for(;;)
    {

#line 2542
        if(j_1 < 16U)
        {
        }
        else
        {

#line 2542
            break;
        }
        r_4[j_1] = cmul_0(r_4[j_1], mfTwiddle_0(6.28318548202514648f * float(_S23 * slotToIndex_0(tid_1 * 16U + j_1)) / 5.24288e+05f));

#line 2542
        j_1 = j_1 + 1U;

#line 2542
    }

#line 2542
    uint p_4 = 0U;

#line 2547
    for(;;)
    {

#line 2547
        if(p_4 < 4U)
        {
        }
        else
        {

#line 2547
            break;
        }

#line 2548
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2548
        thread array<float2, int(16)> _S56 = r_4;

#line 2548
        rootStageOut_0(&_S56, tid_1, col_1, p_4, &kernelContext_3);

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2550
        s_0 = 0U;
        for(;;)
        {

#line 2551
            if(s_0 < 4U)
            {
            }
            else
            {

#line 2551
                break;
            }

#line 2552
            uint e_1 = l_0 + 512U * s_0;
            uint rr_2 = e_1 / 8U;

#line 2553
            uint c_2 = e_1 % 8U;
            uint a_5 = rr_2 * 9U + c_2;

#line 2554
            *((&kernelContext_3)->entryPointParams_scratch_0+((p_4 * 256U + rr_2) * 512U + rootColumn_0(g_2, c_2))) = packed_float2(float2((as_type<float>(((*(&kernelContext_3)->stg_0)[a_5]))), (as_type<float>(((*(&kernelContext_3)->stg_0)[a_5 + 2304U]))))) ;

#line 2551
            s_0 = s_0 + 1U;

#line 2551
        }

#line 2547
        p_4 = p_4 + 1U;

#line 2547
    }

#line 2559
    return;
}
