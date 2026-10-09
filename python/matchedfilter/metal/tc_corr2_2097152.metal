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


#line 389 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/python/matchedfilter/metal/tc_corr2_2097152.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 391
    float2 t1_0 = *a_0 - *c_0;

#line 391
    float2 t2_0 = *b_0 + *d_0;

#line 391
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 393
    *b_0 = t1_0 + j3_0;

#line 393
    *c_0 = t0_0 - t2_0;

#line 393
    *d_0 = t1_0 - j3_0;
    return;
}


#line 221
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 221
    float _S2 = a_1.x;

#line 221
    float _S3 = b_1.x;

#line 221
    float _S4 = a_1.y;

#line 221
    float _S5 = b_1.y;

#line 221
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 425
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 432
    uint n1_0 = 0U;
    for(;;)
    {

#line 433
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 433
            break;
        }

#line 433
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 433
        n1_0 = n1_0 + 1U;

#line 433
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 434
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 434
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 435
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 435
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 436
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 436
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 436
    uint k2_0 = 0U;
    for(;;)
    {

#line 437
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 437
            break;
        }

#line 437
        uint _S6 = 4U * k2_0;

#line 437
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 437
        k2_0 = k2_0 + 1U;

#line 437
    }

    float2 t_0 = (*r_0)[int(1)];

#line 439
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 439
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 440
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 440
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 441
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 441
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 442
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 442
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 443
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 443
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 444
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 444
    (*r_0)[int(14)] = t_5;
    return;
}


#line 17 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 223 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/python/matchedfilter/metal/tc_corr2_2097152.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S7 = max(TB_0, 1U);

#line 225
    uint j_0 = d_1 / _S7;

#line 225
    uint m_0 = d_1 % _S7;

#line 225
    uint _S8;
    if(TB_0 <= 16U)
    {

#line 226
        _S8 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 226
    }
    else
    {

#line 226
        _S8 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 226
    }

#line 226
    return _S8;
}


#line 210
struct KernelContext_0
{
    packed_float2 device* entryPointParams_scratch_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 210
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 210
    uint _S9 = 2U * i_0;

#line 210
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9] = (as_type<uint>((v_0.x)));

#line 210
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9 + 1U] = (as_type<uint>((v_0.y)));

#line 210
    return;
}


#line 211
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 211
    uint _S10 = 2U * i_1;

#line 211
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10 + 1U]))));
}


#line 585
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 586
    uint j_1;

#line 597
    thread array<float2, int(16)> out_0;

#line 597
    uint z_0 = 0U;
    for(;;)
    {

#line 598
        if(z_0 < 16U)
        {
        }
        else
        {

#line 598
            break;
        }

#line 598
        out_0[z_0] = float2(0.0, 0.0);

#line 598
        z_0 = z_0 + 1U;

#line 598
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S11 = p0_0 & lenMask_0;

#line 604
    uint _S12 = _S11 >> lgSpan_0;

#line 604
    uint _S13 = _S12 * 64U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S11 & spanMask_0);

#line 604
    uint c_1 = 0U;

    for(;;)
    {

#line 606
        if(c_1 < 2U)
        {
        }
        else
        {

#line 606
            break;
        }

#line 607
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 607
        j_1 = 0U;
        for(;;)
        {

#line 608
            if(j_1 < 8U)
            {
            }
            else
            {

#line 608
                break;
            }

#line 608
            stgPut_0(j_1 * 64U + kernelContext_2->_tid_0, (*r_1)[c_1 * 8U + j_1], kernelContext_2);

#line 608
            j_1 = j_1 + 1U;

#line 608
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 609
        uint d_2 = 0U;
        for(;;)
        {

#line 610
            if(d_2 < 16U)
            {
            }
            else
            {

#line 610
                break;
            }

#line 611
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S14 = pz_0 & lenMask_0;

#line 612
            uint iz_0 = _S14 >> lgSpan_0;
            uint az_0 = iz_0 * 64U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);
            uint i_2 = _S12 + iz_0;
            uint _S15 = c_1 * 8U;

#line 615
            bool _S16;

#line 615
            if(i_2 >= _S15)
            {

#line 615
                _S16 = i_2 < ((c_1 + 1U) * 8U);

#line 615
            }
            else
            {

#line 615
                _S16 = false;

#line 615
            }

#line 615
            if(_S16)
            {

#line 615
                float2 _S17 = stgGet_0(_S13 + az_0 - _S15 * 64U, kernelContext_2);
                out_0[d_2] = _S17;

#line 615
            }

#line 610
            d_2 = d_2 + 1U;

#line 610
        }

#line 606
        c_1 = c_1 + 1U;

#line 606
    }

#line 606
    j_1 = 0U;

#line 619
    for(;;)
    {

#line 619
        if(j_1 < 16U)
        {
        }
        else
        {

#line 619
            break;
        }

#line 619
        (*r_1)[j_1] = out_0[j_1];

#line 619
        j_1 = j_1 + 1U;

#line 619
    }
    return;
}


#line 404
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 407
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 407
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 528
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 528
    uint b_2 = 0U;

#line 537
    for(;;)
    {

#line 537
        if(b_2 < 4U)
        {
        }
        else
        {

#line 537
            break;
        }

#line 537
        dft4_0(r_3, b_2 * 4U);

#line 537
        b_2 = b_2 + 1U;

#line 537
    }


    return;
}


#line 675
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 675
    uint _S18;

#line 675
    uint k2_1;

#line 675
    float cr_0;

#line 675
    float ci_0;

#line 675
    uint _S19;

#line 675
    for(;;)
    {

#line 675
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(64U);

#line 11
                _S18 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(1024U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 63U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 1024.0);
                float _S20 = tw_0.x;

#line 27
                float _S21 = tw_0.y;

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
                    float nr_0 = cr_0 * _S20 - ci_0 * _S21;
                    float _S22 = cr_0 * _S21 + ci_0 * _S20;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S22;

#line 29
                }

#line 37
                uint per_2 = 16U / max(64U, 1U);
                uint _S23 = max(4U, 1U);

#line 38
                _S19 = _S23;
                uint blk2_2 = tid_0 / _S23;

#line 39
                uint lane2_2 = tid_0 % _S23;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 64U, 1024U, blk_2, lane_2, per_2, _S23, 64U, blk2_2, lane2_2, kernelContext_3);

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
                float _S24 = tw_1.x;

#line 27
                float _S25 = tw_1.y;

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
                    float nr_1 = cr_0 * _S24 - ci_0 * _S25;
                    float _S26 = cr_0 * _S25 + ci_0 * _S24;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S26;

#line 29
                }

#line 37
                uint per_3 = 16U / _S19;
                uint _S27 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S27;

#line 39
                uint lane2_3 = tid_0 % _S27;

#line 39
                exchange_0(r_4, _S18, lgTB_1, 4U, 64U, blk_3, lane_3, per_3, _S27, 4U, blk2_3, lane2_3, kernelContext_3);

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

#line 678 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/python/matchedfilter/metal/tc_corr2_2097152.slang"
    return;
}


#line 644
uint lgOf_0(uint i_3)
{

#line 644
    uint _S28;

#line 644
    if(i_3 < 2U)
    {

#line 644
        _S28 = 4U;

#line 644
    }
    else
    {

#line 644
        _S28 = 1U;

#line 644
    }

#line 644
    return _S28;
}


#line 646
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 650
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 650
    uint lg_2 = lgOf_0(1U);

#line 650
    uint lg_3 = lgOf_0(0U);

#line 655
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 1515
[[kernel]] void tcFullStage3(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], packed_float2 device* entryPointParams_scratch_1 [[buffer(0)]], packed_float2 device* entryPointParams_output_1 [[buffer(1)]])
{

#line 1515
    thread KernelContext_0 kernelContext_4;

#line 1515
    (&kernelContext_4)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 1515
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1515
    threadgroup array<uint, int(1024)> stg_1;

#line 1515
    (&kernelContext_4)->stg_0 = &stg_1;



    uint _S29 = gid_0.x;

#line 1519
    uint _S30 = _S29 / 2048U;

#line 1519
    uint _S31 = _S29 % 2048U;
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 1523
    uint m_1 = 0U;
    for(;;)
    {

#line 1524
        if(m_1 < 16U)
        {
        }
        else
        {

#line 1524
            break;
        }

#line 1525
        r_5[m_1] = float2(*((&kernelContext_4)->entryPointParams_scratch_0+(_S30 * 2097152U + _S31 * 1024U + tid_1 + 64U * m_1))) ;

#line 1524
        m_1 = m_1 + 1U;

#line 1524
    }

#line 1524
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 1524
    uint i_4 = 0U;


    for(;;)
    {

#line 1527
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1527
            break;
        }

#line 1527
        *((&kernelContext_4)->entryPointParams_output_0+(_S30 * 2097152U + slotToIndex_0(tid_1 * 16U + i_4) * 2048U + _S31)) = packed_float2(float2(r_5[i_4].x, r_5[i_4].y)) ;

#line 1527
        i_4 = i_4 + 1U;

#line 1527
    }



    return;
}
