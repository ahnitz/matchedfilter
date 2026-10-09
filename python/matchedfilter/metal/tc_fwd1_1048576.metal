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


#line 370 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/python/matchedfilter/metal/tc_fwd1_1048576.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 372
    float2 t1_0 = *a_0 - *c_0;

#line 372
    float2 t2_0 = *b_0 + *d_0;

#line 372
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 374
    *b_0 = t1_0 + j3_0;

#line 374
    *c_0 = t0_0 - t2_0;

#line 374
    *d_0 = t1_0 - j3_0;
    return;
}


#line 202
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 202
    float _S2 = a_1.x;

#line 202
    float _S3 = b_1.x;

#line 202
    float _S4 = a_1.y;

#line 202
    float _S5 = b_1.y;

#line 202
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 406
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 413
    uint n1_0 = 0U;
    for(;;)
    {

#line 414
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 414
            break;
        }

#line 414
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 414
        n1_0 = n1_0 + 1U;

#line 414
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 415
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 415
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 416
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 416
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 417
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 417
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 417
    uint k2_0 = 0U;
    for(;;)
    {

#line 418
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 418
            break;
        }

#line 418
        uint _S6 = 4U * k2_0;

#line 418
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 418
        k2_0 = k2_0 + 1U;

#line 418
    }

    float2 t_0 = (*r_0)[int(1)];

#line 420
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 420
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 421
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 421
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 422
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 422
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 423
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 423
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 424
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 424
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 425
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 425
    (*r_0)[int(14)] = t_5;
    return;
}


#line 12 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 90 "core"
struct EntryPointParams_0
{
    uint seriesLength_0;
};


#line 191 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/python/matchedfilter/metal/tc_fwd1_1048576.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_scratch_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 191
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 191
    uint _S7 = 2U * i_0;

#line 191
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S7] = (as_type<uint>((v_0.x)));

#line 191
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S7 + 1U] = (as_type<uint>((v_0.y)));

#line 191
    return;
}


#line 204
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S8 = max(TB_0, 1U);

#line 206
    uint j_0 = d_1 / _S8;

#line 206
    uint m_0 = d_1 % _S8;

#line 206
    uint _S9;
    if(TB_0 <= 16U)
    {

#line 207
        _S9 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 207
    }
    else
    {

#line 207
        _S9 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 207
    }

#line 207
    return _S9;
}


#line 192
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 192
    uint _S10 = 2U * i_1;

#line 192
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10 + 1U]))));
}


#line 566
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 567
    uint j_1;

#line 578
    thread array<float2, int(16)> out_0;

#line 578
    uint z_0 = 0U;
    for(;;)
    {

#line 579
        if(z_0 < 16U)
        {
        }
        else
        {

#line 579
            break;
        }

#line 579
        out_0[z_0] = float2(0.0, 0.0);

#line 579
        z_0 = z_0 + 1U;

#line 579
    }
    uint _S11 = (1U << lgSpan_0) - 1U;
    uint _S12 = (1U << lgLen_0) - 1U;

#line 581
    uint c_1 = 0U;
    for(;;)
    {

#line 582
        if(c_1 < 2U)
        {
        }
        else
        {

#line 582
            break;
        }

#line 583
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 583
        j_1 = 0U;
        for(;;)
        {

#line 584
            if(j_1 < 8U)
            {
            }
            else
            {

#line 584
                break;
            }

#line 584
            stgPut_0(j_1 * 64U + kernelContext_2->_tid_0, (*r_1)[c_1 * 8U + j_1], kernelContext_2);

#line 584
            j_1 = j_1 + 1U;

#line 584
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 585
        uint d_2 = 0U;
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

#line 587
            uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
            uint b_2 = p_0 >> lgLen_0;

#line 588
            uint rem_0 = p_0 & _S12;
            uint i_2 = rem_0 >> lgSpan_0;

#line 589
            uint ln_0 = rem_0 & _S11;
            uint _S13 = c_1 * 8U;

#line 590
            bool _S14;

#line 590
            if(i_2 >= _S13)
            {

#line 590
                _S14 = i_2 < ((c_1 + 1U) * 8U);

#line 590
            }
            else
            {

#line 590
                _S14 = false;

#line 590
            }

#line 590
            if(_S14)
            {

#line 590
                float2 _S15 = stgGet_0((i_2 - _S13) * 64U + (b_2 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_2] = _S15;

#line 590
            }

#line 586
            d_2 = d_2 + 1U;

#line 586
        }

#line 582
        c_1 = c_1 + 1U;

#line 582
    }

#line 582
    j_1 = 0U;

#line 594
    for(;;)
    {

#line 594
        if(j_1 < 16U)
        {
        }
        else
        {

#line 594
            break;
        }

#line 594
        (*r_1)[j_1] = out_0[j_1];

#line 594
        j_1 = j_1 + 1U;

#line 594
    }
    return;
}


#line 385
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 388
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 388
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 509
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 509
    uint b_3 = 0U;

#line 518
    for(;;)
    {

#line 518
        if(b_3 < 4U)
        {
        }
        else
        {

#line 518
            break;
        }

#line 518
        dft4_0(r_3, b_3 * 4U);

#line 518
        b_3 = b_3 + 1U;

#line 518
    }


    return;
}


#line 650
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 650
    uint _S16;

#line 650
    uint k2_1;

#line 650
    float cr_0;

#line 650
    float ci_0;

#line 650
    uint _S17;

#line 650
    for(;;)
    {

#line 650
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(64U);

#line 11
                _S16 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(1024U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 63U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 1024.0);
                float _S18 = tw_0.x;

#line 27
                float _S19 = tw_0.y;

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
                    float nr_0 = cr_0 * _S18 - ci_0 * _S19;
                    float _S20 = cr_0 * _S19 + ci_0 * _S18;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S20;

#line 29
                }

#line 37
                uint per_2 = 16U / max(64U, 1U);
                uint _S21 = max(4U, 1U);

#line 38
                _S17 = _S21;
                uint blk2_2 = tid_0 / _S21;

#line 39
                uint lane2_2 = tid_0 % _S21;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 64U, 1024U, blk_2, lane_2, per_2, _S21, 64U, blk2_2, lane2_2, kernelContext_3);

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
                float _S22 = tw_1.x;

#line 27
                float _S23 = tw_1.y;

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
                    float nr_1 = cr_0 * _S22 - ci_0 * _S23;
                    float _S24 = cr_0 * _S23 + ci_0 * _S22;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S24;

#line 29
                }

#line 37
                uint per_3 = 16U / _S17;
                uint _S25 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S25;

#line 39
                uint lane2_3 = tid_0 % _S25;

#line 39
                exchange_0(r_4, _S16, lgTB_1, 4U, 64U, blk_3, lane_3, per_3, _S25, 4U, blk2_3, lane2_3, kernelContext_3);

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

#line 653 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/python/matchedfilter/metal/tc_fwd1_1048576.slang"
    return;
}


#line 619
uint lgOf_0(uint i_3)
{

#line 619
    uint _S26;

#line 619
    if(i_3 < 2U)
    {

#line 619
        _S26 = 4U;

#line 619
    }
    else
    {

#line 619
        _S26 = 1U;

#line 619
    }

#line 619
    return _S26;
}


#line 621
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 625
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 625
    uint lg_2 = lgOf_0(1U);

#line 625
    uint lg_3 = lgOf_0(0U);

#line 630
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 1504
[[kernel]] void tcForwardStage1(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_scratch_1 [[buffer(3)]])
{

#line 1504
    thread KernelContext_0 kernelContext_4;

#line 1504
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1504
    (&kernelContext_4)->entryPointParams_series_0 = entryPointParams_series_1;

#line 1504
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1504
    (&kernelContext_4)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 1504
    threadgroup array<uint, int(1024)> stg_1;

#line 1504
    (&kernelContext_4)->stg_0 = &stg_1;

#line 1510
    uint _S27 = gid_0.x;

#line 1510
    uint block_0 = _S27 / 1024U;

#line 1510
    uint _S28 = _S27 % 1024U;
    uint tid_1 = lid_0.x;
    uint _S29 = entryPointParams_starts_1[block_0];
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 1515
    uint m_1 = 0U;
    for(;;)
    {

#line 1516
        if(m_1 < 16U)
        {
        }
        else
        {

#line 1516
            break;
        }

#line 1517
        uint j_2 = _S28 + 1024U * (tid_1 + 64U * m_1);
        float2 _S30 = float2(0.0, 0.0);

#line 1518
        bool _S31;
        if(_S29 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0))
        {

#line 1519
            _S31 = j_2 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0 - _S29);

#line 1519
        }
        else
        {

#line 1519
            _S31 = false;

#line 1519
        }

#line 1519
        float2 x_2;

#line 1519
        if(_S31)
        {

#line 1519
            x_2 = float2(*((&kernelContext_4)->entryPointParams_series_0+(_S29 + j_2))) ;

#line 1519
        }
        else
        {

#line 1519
            x_2 = _S30;

#line 1519
        }

        r_5[m_1] = float2(x_2.x / 1.048576e+06, - x_2.y / 1.048576e+06);

#line 1516
        m_1 = m_1 + 1U;

#line 1516
    }

#line 1516
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 1516
    uint i_4 = 0U;

#line 1524
    for(;;)
    {

#line 1524
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1524
            break;
        }

#line 1525
        uint k2_2 = slotToIndex_0(tid_1 * 16U + i_4);

#line 1525
        *((&kernelContext_4)->entryPointParams_scratch_0+(block_0 * 1048576U + k2_2 * 1024U + _S28)) = packed_float2(cmul_0(r_5[i_4], mfTwiddle_0(6.28318548202514648 * float(_S28 * k2_2) / 1.048576e+06))) ;

#line 1524
        i_4 = i_4 + 1U;

#line 1524
    }

#line 1529
    return;
}
