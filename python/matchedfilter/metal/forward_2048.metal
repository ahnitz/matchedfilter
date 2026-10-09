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


#line 371 "/tmp/tmpc5_9w2bh/forward.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 373
    float2 t1_0 = *a_0 - *c_0;

#line 373
    float2 t2_0 = *b_0 + *d_0;

#line 373
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 375
    *b_0 = t1_0 + j3_0;

#line 375
    *c_0 = t0_0 - t2_0;

#line 375
    *d_0 = t1_0 - j3_0;
    return;
}


#line 203
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 203
    float _S2 = a_1.x;

#line 203
    float _S3 = b_1.x;

#line 203
    float _S4 = a_1.y;

#line 203
    float _S5 = b_1.y;

#line 203
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 407
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 414
    uint n1_0 = 0U;
    for(;;)
    {

#line 415
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 415
            break;
        }

#line 415
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 415
        n1_0 = n1_0 + 1U;

#line 415
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 416
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 416
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 417
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 417
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 418
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 418
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 418
    uint k2_0 = 0U;
    for(;;)
    {

#line 419
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 419
            break;
        }

#line 419
        uint _S6 = 4U * k2_0;

#line 419
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 419
        k2_0 = k2_0 + 1U;

#line 419
    }

    float2 t_0 = (*r_0)[int(1)];

#line 421
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 421
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 422
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 422
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 423
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 423
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 424
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 424
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 425
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 425
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 426
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 426
    (*r_0)[int(14)] = t_5;
    return;
}


#line 12 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 205 "/tmp/tmpc5_9w2bh/forward.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S7 = max(TB_0, 1U);

#line 207
    uint j_0 = d_1 / _S7;

#line 207
    uint m_0 = d_1 % _S7;

#line 207
    uint _S8;
    if(TB_0 <= 16U)
    {

#line 208
        _S8 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 208
    }
    else
    {

#line 208
        _S8 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 208
    }

#line 208
    return _S8;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint seriesLength_0;
};


#line 558 "/tmp/tmpc5_9w2bh/forward.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_spectra_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 545
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S9 = (1U << lgSpan_0) - 1U;
    uint _S10 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

#line 550
    uint d_2 = 0U;
    for(;;)
    {

#line 551
        if(d_2 < 16U)
        {
        }
        else
        {

#line 551
            break;
        }

#line 552
        uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
        uint rem_0 = p_0 & _S10;
        src_0[d_2] = (rem_0 >> lgSpan_0) * 128U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S9);

#line 551
        d_2 = d_2 + 1U;

#line 551
    }

#line 556
    thread array<float, int(16)> xr_0;
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 557
    uint j_1 = 0U;
    for(;;)
    {

#line 558
        if(j_1 < 16U)
        {
        }
        else
        {

#line 558
            break;
        }

#line 558
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 128U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].x)));

#line 558
        j_1 = j_1 + 1U;

#line 558
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 559
    d_2 = 0U;
    for(;;)
    {

#line 560
        if(d_2 < 16U)
        {
        }
        else
        {

#line 560
            break;
        }

#line 560
        xr_0[d_2] = (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]])));

#line 560
        d_2 = d_2 + 1U;

#line 560
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 561
    j_1 = 0U;
    for(;;)
    {

#line 562
        if(j_1 < 16U)
        {
        }
        else
        {

#line 562
            break;
        }

#line 562
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 128U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].y)));

#line 562
        j_1 = j_1 + 1U;

#line 562
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 563
    d_2 = 0U;
    for(;;)
    {

#line 564
        if(d_2 < 16U)
        {
        }
        else
        {

#line 564
            break;
        }

#line 564
        (*r_1)[d_2] = float2(xr_0[d_2], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]]))));

#line 564
        d_2 = d_2 + 1U;

#line 564
    }
    return;
}


#line 391
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_2;

#line 395
    uint s_0 = 1U;
    for(;;)
    {

#line 396
        if(s_0 < 8U)
        {
        }
        else
        {

#line 396
            break;
        }

#line 396
        uint j_2 = 0U;
        for(;;)
        {

#line 397
            if(j_2 < 4U)
            {
            }
            else
            {

#line 397
                break;
            }

#line 398
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S11 = o_0 + j_2;

#line 401
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0)), (*r_2)[_S11 + 4U]);
            uint _S12 = ((j_2 - k_0) << 1U) + k_0;

#line 402
            b_2[_S12] = (*r_2)[_S11] + t_6;

#line 402
            b_2[_S12 + s_0] = (*r_2)[_S11] - t_6;

#line 397
            j_2 = j_2 + 1U;

#line 397
        }

#line 397
        uint i_0 = 0U;

#line 404
        for(;;)
        {

#line 404
            if(i_0 < 8U)
            {
            }
            else
            {

#line 404
                break;
            }

#line 404
            (*r_2)[o_0 + i_0] = b_2[i_0];

#line 404
            i_0 = i_0 + 1U;

#line 404
        }

#line 396
        s_0 = s_0 << 1U;

#line 396
    }

#line 406
    return;
}


#line 510
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 510
    uint b_3 = 0U;

#line 518
    for(;;)
    {

#line 518
        if(b_3 < 2U)
        {
        }
        else
        {

#line 518
            break;
        }

#line 518
        dft8_0(r_3, b_3 * 8U);

#line 518
        b_3 = b_3 + 1U;

#line 518
    }



    return;
}


#line 1552
void forwardTransform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 1552
    uint _S13;

#line 1552
    uint k2_1;

#line 1552
    float cr_0;

#line 1552
    float ci_0;

#line 1552
    uint _S14;

#line 1552
    for(;;)
    {

#line 1552
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(128U);

#line 11
                _S13 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(2048U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 127U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 2048.0);
                float _S15 = tw_0.x;

#line 27
                float _S16 = tw_0.y;

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
                    float nr_0 = cr_0 * _S15 - ci_0 * _S16;
                    float _S17 = cr_0 * _S16 + ci_0 * _S15;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S17;

#line 29
                }

#line 37
                uint per_2 = 16U / max(128U, 1U);
                uint _S18 = max(8U, 1U);

#line 38
                _S14 = _S18;
                uint blk2_2 = tid_0 / _S18;

#line 39
                uint lane2_2 = tid_0 % _S18;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 128U, 2048U, blk_2, lane_2, per_2, _S18, 128U, blk2_2, lane2_2, kernelContext_1);

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


                uint lgTB_1 = firstbithigh_0(8U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 7U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 128.0);
                float _S19 = tw_1.x;

#line 27
                float _S20 = tw_1.y;

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
                    float nr_1 = cr_0 * _S19 - ci_0 * _S20;
                    float _S21 = cr_0 * _S20 + ci_0 * _S19;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S21;

#line 29
                }

#line 37
                uint per_3 = 16U / _S14;
                uint _S22 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S22;

#line 39
                uint lane2_3 = tid_0 % _S22;

#line 39
                exchange_0(r_4, _S13, lgTB_1, 8U, 128U, blk_3, lane_3, per_3, _S22, 8U, blk2_3, lane2_3, kernelContext_1);

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

#line 1555 "/tmp/tmpc5_9w2bh/forward.slang"
    return;
}


#line 620
uint lgOf_0(uint i_1)
{

#line 620
    uint _S23;

#line 620
    if(i_1 < 2U)
    {

#line 620
        _S23 = 4U;

#line 620
    }
    else
    {

#line 620
        if(i_1 == 2U)
        {

#line 620
            _S23 = 3U;

#line 620
        }
        else
        {

#line 620
            _S23 = 1U;

#line 620
        }

#line 620
    }

#line 620
    return _S23;
}


#line 622
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 626
    uint lg_1 = lgOf_0(1U);

#line 626
    uint lg_2 = lgOf_0(0U);

#line 631
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1560
[[kernel]] void seriesForward(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]])
{

#line 1560
    thread KernelContext_0 kernelContext_2;

#line 1560
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 1560
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 1560
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1560
    (&kernelContext_2)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 1560
    threadgroup array<uint, int(2048)> stg_1;

#line 1560
    (&kernelContext_2)->stg_0 = &stg_1;

#line 1566
    uint tid_1 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_1;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S24 = gid_0.x;

#line 1569
    uint _S25 = entryPointParams_starts_1[_S24];
    thread array<float2, int(16)> r_5;

#line 1570
    uint k_1 = 0U;
    for(;;)
    {

#line 1571
        if(k_1 < 16U)
        {
        }
        else
        {

#line 1571
            break;
        }

#line 1572
        uint offset_0 = tid_1 + 128U * k_1;
        float2 _S26 = float2(0.0, 0.0);

#line 1573
        bool _S27;

        if(_S25 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 1575
            _S27 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S25);

#line 1575
        }
        else
        {

#line 1575
            _S27 = false;

#line 1575
        }

#line 1575
        float2 x_1;

#line 1575
        if(_S27)
        {

#line 1575
            x_1 = float2(*((&kernelContext_2)->entryPointParams_series_0+(_S25 + offset_0))) ;

#line 1575
        }
        else
        {

#line 1575
            x_1 = _S26;

#line 1575
        }

        r_5[k_1] = float2(x_1.x / 2048.0, - x_1.y / 2048.0);

#line 1571
        k_1 = k_1 + 1U;

#line 1571
    }

#line 1571
    forwardTransform_0(&r_5, tid_1, &kernelContext_2);

#line 1571
    k_1 = 0U;

#line 1580
    for(;;)
    {

#line 1580
        if(k_1 < 16U)
        {
        }
        else
        {

#line 1580
            break;
        }

#line 1580
        *((&kernelContext_2)->entryPointParams_spectra_0+(_S24 * 2048U + slotToIndex_0(tid_1 * 16U + k_1))) = packed_float2(float2(r_5[k_1].x, - r_5[k_1].y)) ;

#line 1580
        k_1 = k_1 + 1U;

#line 1580
    }



    return;
}
