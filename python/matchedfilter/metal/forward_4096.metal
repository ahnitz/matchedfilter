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


#line 390 "/tmp/tmpl0wjzcl9/forward.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 392
    float2 t1_0 = *a_0 - *c_0;

#line 392
    float2 t2_0 = *b_0 + *d_0;

#line 392
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 394
    *b_0 = t1_0 + j3_0;

#line 394
    *c_0 = t0_0 - t2_0;

#line 394
    *d_0 = t1_0 - j3_0;
    return;
}


#line 222
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 222
    float _S2 = a_1.x;

#line 222
    float _S3 = b_1.x;

#line 222
    float _S4 = a_1.y;

#line 222
    float _S5 = b_1.y;

#line 222
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 426
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 433
    uint n1_0 = 0U;
    for(;;)
    {

#line 434
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 434
            break;
        }

#line 434
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 434
        n1_0 = n1_0 + 1U;

#line 434
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 435
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 435
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 436
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 436
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 437
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 437
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 437
    uint k2_0 = 0U;
    for(;;)
    {

#line 438
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 438
            break;
        }

#line 438
        uint _S6 = 4U * k2_0;

#line 438
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 438
        k2_0 = k2_0 + 1U;

#line 438
    }

    float2 t_0 = (*r_0)[int(1)];

#line 440
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 440
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 441
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 441
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 442
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 442
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 443
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 443
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 444
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 444
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 445
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 445
    (*r_0)[int(14)] = t_5;
    return;
}


#line 426
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_1 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_1 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_1 = float2(0.0, 1.0);
    float2 W6_1 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_1 = float2(-0.92387950420379639, -0.38268342614173889);

#line 433
    uint n1_1 = 0U;
    for(;;)
    {

#line 434
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 434
            break;
        }

#line 434
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 434
        n1_1 = n1_1 + 1U;

#line 434
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 435
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 435
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 436
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 436
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 437
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 437
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 437
    uint k2_1 = 0U;
    for(;;)
    {

#line 438
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 438
            break;
        }

#line 438
        uint _S7 = 4U * k2_1;

#line 438
        r4_0(&(*r_1)[_S7], &(*r_1)[_S7 + 1U], &(*r_1)[_S7 + 2U], &(*r_1)[_S7 + 3U]);

#line 438
        k2_1 = k2_1 + 1U;

#line 438
    }

    float2 t_6 = (*r_1)[int(1)];

#line 440
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 440
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 441
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 441
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 442
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 442
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 443
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 443
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 444
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 444
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 445
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 445
    (*r_1)[int(14)] = t_11;
    return;
}


#line 17 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 224 "/tmp/tmpl0wjzcl9/forward.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S8 = max(TB_0, 1U);

#line 226
    uint j_0 = d_1 / _S8;

#line 226
    uint m_0 = d_1 % _S8;

#line 226
    uint _S9;
    if(TB_0 <= 16U)
    {

#line 227
        _S9 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 227
    }
    else
    {

#line 227
        _S9 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 227
    }

#line 227
    return _S9;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint seriesLength_0;
};


#line 577 "/tmp/tmpl0wjzcl9/forward.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_spectra_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(4096)> threadgroup* stg_0;
};


#line 564
void exchange_0(array<float2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S10 = (1U << lgSpan_0) - 1U;
    uint _S11 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

#line 569
    uint d_2 = 0U;
    for(;;)
    {

#line 570
        if(d_2 < 16U)
        {
        }
        else
        {

#line 570
            break;
        }

#line 571
        uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
        uint rem_0 = p_0 & _S11;
        src_0[d_2] = (rem_0 >> lgSpan_0) * 256U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S10);

#line 570
        d_2 = d_2 + 1U;

#line 570
    }

#line 575
    thread array<float, int(16)> xr_0;
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 576
    uint j_1 = 0U;
    for(;;)
    {

#line 577
        if(j_1 < 16U)
        {
        }
        else
        {

#line 577
            break;
        }

#line 577
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 256U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_2)[j_1].x)));

#line 577
        j_1 = j_1 + 1U;

#line 577
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 578
    d_2 = 0U;
    for(;;)
    {

#line 579
        if(d_2 < 16U)
        {
        }
        else
        {

#line 579
            break;
        }

#line 579
        xr_0[d_2] = (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]])));

#line 579
        d_2 = d_2 + 1U;

#line 579
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 580
    j_1 = 0U;
    for(;;)
    {

#line 581
        if(j_1 < 16U)
        {
        }
        else
        {

#line 581
            break;
        }

#line 581
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 256U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_2)[j_1].y)));

#line 581
        j_1 = j_1 + 1U;

#line 581
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 582
    d_2 = 0U;
    for(;;)
    {

#line 583
        if(d_2 < 16U)
        {
        }
        else
        {

#line 583
            break;
        }

#line 583
        (*r_2)[d_2] = float2(xr_0[d_2], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]]))));

#line 583
        d_2 = d_2 + 1U;

#line 583
    }
    return;
}


#line 529
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 536
    dft16_1(r_3);

#line 541
    return;
}


#line 1607
void forwardTransform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 1607
    uint _S12;

#line 1607
    uint k2_2;

#line 1607
    float cr_0;

#line 1607
    float ci_0;

#line 1607
    uint _S13;

#line 1607
    for(;;)
    {

#line 1607
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(256U);

#line 11
                _S12 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(4096U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 255U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 4096.0);
                float _S14 = tw_0.x;

#line 27
                float _S15 = tw_0.y;

#line 27
                k2_2 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S14 - ci_0 * _S15;
                    float _S16 = cr_0 * _S15 + ci_0 * _S14;

#line 29
                    k2_2 = k2_2 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S16;

#line 29
                }

#line 37
                uint per_2 = 16U / max(256U, 1U);
                uint _S17 = max(16U, 1U);

#line 38
                _S13 = _S17;
                uint blk2_2 = tid_0 / _S17;

#line 39
                uint lane2_2 = tid_0 % _S17;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 256U, 4096U, blk_2, lane_2, per_2, _S17, 256U, blk2_2, lane2_2, kernelContext_1);

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


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 256.0);
                float _S18 = tw_1.x;

#line 27
                float _S19 = tw_1.y;

#line 27
                k2_2 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S18 - ci_0 * _S19;
                    float _S20 = cr_0 * _S19 + ci_0 * _S18;

#line 29
                    k2_2 = k2_2 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S20;

#line 29
                }

#line 37
                uint per_3 = 16U / _S13;
                uint _S21 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S21;

#line 39
                uint lane2_3 = tid_0 % _S21;

#line 39
                exchange_0(r_4, _S12, lgTB_1, 16U, 256U, blk_3, lane_3, per_3, _S21, 16U, blk2_3, lane2_3, kernelContext_1);

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

#line 1610 "/tmp/tmpl0wjzcl9/forward.slang"
    return;
}


#line 645
uint lgOf_0(uint i_0)
{

#line 645
    uint _S22;

#line 645
    if(i_0 < 2U)
    {

#line 645
        _S22 = 4U;

#line 645
    }
    else
    {

#line 645
        if(i_0 == 2U)
        {

#line 645
            _S22 = 4U;

#line 645
        }
        else
        {

#line 645
            _S22 = 1U;

#line 645
        }

#line 645
    }

#line 645
    return _S22;
}


#line 647
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 651
    uint lg_1 = lgOf_0(1U);

#line 651
    uint lg_2 = lgOf_0(0U);

#line 656
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1615
[[kernel]] void seriesForward(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]])
{

#line 1615
    thread KernelContext_0 kernelContext_2;

#line 1615
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 1615
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 1615
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1615
    (&kernelContext_2)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 1615
    threadgroup array<uint, int(4096)> stg_1;

#line 1615
    (&kernelContext_2)->stg_0 = &stg_1;

#line 1621
    uint tid_1 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_1;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S23 = gid_0.x;

#line 1624
    uint _S24 = entryPointParams_starts_1[_S23];
    thread array<float2, int(16)> r_5;

#line 1625
    uint k_0 = 0U;
    for(;;)
    {

#line 1626
        if(k_0 < 16U)
        {
        }
        else
        {

#line 1626
            break;
        }

#line 1627
        uint offset_0 = tid_1 + 256U * k_0;
        float2 _S25 = float2(0.0, 0.0);

#line 1628
        bool _S26;

        if(_S24 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 1630
            _S26 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S24);

#line 1630
        }
        else
        {

#line 1630
            _S26 = false;

#line 1630
        }

#line 1630
        float2 x_1;

#line 1630
        if(_S26)
        {

#line 1630
            x_1 = float2(*((&kernelContext_2)->entryPointParams_series_0+(_S24 + offset_0))) ;

#line 1630
        }
        else
        {

#line 1630
            x_1 = _S25;

#line 1630
        }

        r_5[k_0] = float2(x_1.x / 4096.0, - x_1.y / 4096.0);

#line 1626
        k_0 = k_0 + 1U;

#line 1626
    }

#line 1626
    forwardTransform_0(&r_5, tid_1, &kernelContext_2);

#line 1626
    k_0 = 0U;

#line 1635
    for(;;)
    {

#line 1635
        if(k_0 < 16U)
        {
        }
        else
        {

#line 1635
            break;
        }

#line 1635
        *((&kernelContext_2)->entryPointParams_spectra_0+(_S23 * 4096U + slotToIndex_0(tid_1 * 16U + k_0))) = packed_float2(float2(r_5[k_0].x, - r_5[k_0].y)) ;

#line 1635
        k_0 = k_0 + 1U;

#line 1635
    }



    return;
}
