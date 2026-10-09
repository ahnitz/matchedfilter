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


#line 376 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/python/matchedfilter/metal/tc_fwd2_131072.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 378
    float2 t1_0 = *a_0 - *c_0;

#line 378
    float2 t2_0 = *b_0 + *d_0;

#line 378
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 380
    *b_0 = t1_0 + j3_0;

#line 380
    *c_0 = t0_0 - t2_0;

#line 380
    *d_0 = t1_0 - j3_0;
    return;
}


#line 208
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 208
    float _S2 = a_1.x;

#line 208
    float _S3 = b_1.x;

#line 208
    float _S4 = a_1.y;

#line 208
    float _S5 = b_1.y;

#line 208
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 412
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 419
    uint n1_0 = 0U;
    for(;;)
    {

#line 420
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 420
            break;
        }

#line 420
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 420
        n1_0 = n1_0 + 1U;

#line 420
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 421
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 421
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 422
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 422
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 423
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 423
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 423
    uint k2_0 = 0U;
    for(;;)
    {

#line 424
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 424
            break;
        }

#line 424
        uint _S6 = 4U * k2_0;

#line 424
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 424
        k2_0 = k2_0 + 1U;

#line 424
    }

    float2 t_0 = (*r_0)[int(1)];

#line 426
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 426
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 427
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 427
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 428
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 428
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 429
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 429
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 430
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 430
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 431
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 431
    (*r_0)[int(14)] = t_5;
    return;
}


#line 412
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_1 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_1 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_1 = float2(0.0, 1.0);
    float2 W6_1 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_1 = float2(-0.92387950420379639, -0.38268342614173889);

#line 419
    uint n1_1 = 0U;
    for(;;)
    {

#line 420
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 420
            break;
        }

#line 420
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 420
        n1_1 = n1_1 + 1U;

#line 420
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 421
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 421
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 422
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 422
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 423
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 423
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 423
    uint k2_1 = 0U;
    for(;;)
    {

#line 424
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 424
            break;
        }

#line 424
        uint _S7 = 4U * k2_1;

#line 424
        r4_0(&(*r_1)[_S7], &(*r_1)[_S7 + 1U], &(*r_1)[_S7 + 2U], &(*r_1)[_S7 + 3U]);

#line 424
        k2_1 = k2_1 + 1U;

#line 424
    }

    float2 t_6 = (*r_1)[int(1)];

#line 426
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 426
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 427
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 427
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 428
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 428
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 429
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 429
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 430
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 430
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 431
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 431
    (*r_1)[int(14)] = t_11;
    return;
}


#line 12 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 210 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/python/matchedfilter/metal/tc_fwd2_131072.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S8 = max(TB_0, 1U);

#line 212
    uint j_0 = d_1 / _S8;

#line 212
    uint m_0 = d_1 % _S8;

#line 212
    uint _S9;
    if(TB_0 <= 16U)
    {

#line 213
        _S9 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 213
    }
    else
    {

#line 213
        _S9 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 213
    }

#line 213
    return _S9;
}


#line 197
struct KernelContext_0
{
    packed_float2 device* entryPointParams_scratch_0;
    packed_float2 device* entryPointParams_spectra_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(512)> threadgroup* stg_0;
};


#line 197
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 197
    uint _S10 = 2U * i_0;

#line 197
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S10] = (as_type<uint>((v_0.x)));

#line 197
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S10 + 1U] = (as_type<uint>((v_0.y)));

#line 197
    return;
}


#line 198
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 198
    uint _S11 = 2U * i_1;

#line 198
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S11]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S11 + 1U]))));
}


#line 572
void exchange_0(array<float2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 573
    uint j_1;

#line 584
    thread array<float2, int(16)> out_0;

#line 584
    uint z_0 = 0U;
    for(;;)
    {

#line 585
        if(z_0 < 16U)
        {
        }
        else
        {

#line 585
            break;
        }

#line 585
        out_0[z_0] = float2(0.0, 0.0);

#line 585
        z_0 = z_0 + 1U;

#line 585
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S12 = p0_0 & lenMask_0;

#line 591
    uint _S13 = (_S12 >> lgSpan_0) * 16U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S12 & spanMask_0);

#line 591
    uint c_1 = 0U;

    for(;;)
    {

#line 593
        if(c_1 < 1U)
        {
        }
        else
        {

#line 593
            break;
        }

#line 594
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 594
        j_1 = 0U;
        for(;;)
        {

#line 595
            if(j_1 < 16U)
            {
            }
            else
            {

#line 595
                break;
            }

#line 595
            stgPut_0(j_1 * 16U + kernelContext_2->_tid_0, (*r_2)[c_1 * 16U + j_1], kernelContext_2);

#line 595
            j_1 = j_1 + 1U;

#line 595
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 596
        uint d_2 = 0U;
        for(;;)
        {

#line 597
            if(d_2 < 16U)
            {
            }
            else
            {

#line 597
                break;
            }

#line 598
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S14 = pz_0 & lenMask_0;
            uint az_0 = (_S14 >> lgSpan_0) * 16U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);

#line 600
            float2 _S15 = stgGet_0(_S13 + az_0 - c_1 * 16U * 16U, kernelContext_2);


            out_0[d_2] = _S15;

#line 597
            d_2 = d_2 + 1U;

#line 597
        }

#line 593
        c_1 = c_1 + 1U;

#line 593
    }

#line 593
    j_1 = 0U;

#line 606
    for(;;)
    {

#line 606
        if(j_1 < 16U)
        {
        }
        else
        {

#line 606
            break;
        }

#line 606
        (*r_2)[j_1] = out_0[j_1];

#line 606
        j_1 = j_1 + 1U;

#line 606
    }
    return;
}


#line 515
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 522
    dft16_1(r_3);

#line 527
    return;
}


#line 662
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 662
    for(;;)
    {

#line 662
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(16U);
                uint lgLn_0 = firstbithigh_0(256U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 15U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 256.0);
                float _S16 = tw_0.x;

#line 27
                float _S17 = tw_0.y;

#line 27
                uint k2_2 = 0U;

#line 27
                float cr_0 = 1.0;

#line 27
                float ci_0 = 0.0;

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
                    float nr_0 = cr_0 * _S16 - ci_0 * _S17;
                    float _S18 = cr_0 * _S17 + ci_0 * _S16;

#line 29
                    k2_2 = k2_2 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S18;

#line 29
                }

#line 37
                uint per_2 = 16U / max(16U, 1U);
                uint _S19 = max(1U, 1U);
                uint blk2_2 = tid_0 / _S19;

#line 39
                uint lane2_2 = tid_0 % _S19;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 16U, 256U, blk_2, lane_2, per_2, _S19, 16U, blk2_2, lane2_2, kernelContext_3);

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

#line 665 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/python/matchedfilter/metal/tc_fwd2_131072.slang"
    return;
}


#line 631
uint lgOf_0(uint i_2)
{

#line 631
    uint _S20;

#line 631
    if(i_2 < 1U)
    {

#line 631
        _S20 = 4U;

#line 631
    }
    else
    {

#line 631
        if(i_2 == 1U)
        {

#line 631
            _S20 = 4U;

#line 631
        }
        else
        {

#line 631
            _S20 = 1U;

#line 631
        }

#line 631
    }

#line 631
    return _S20;
}


#line 633
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 637
    uint lg_1 = lgOf_0(0U);

#line 642
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 1544
[[kernel]] void tcForwardStage3(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], packed_float2 device* entryPointParams_scratch_1 [[buffer(0)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(1)]])
{

#line 1544
    thread KernelContext_0 kernelContext_4;

#line 1544
    (&kernelContext_4)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 1544
    (&kernelContext_4)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 1544
    threadgroup array<uint, int(512)> stg_1;

#line 1544
    (&kernelContext_4)->stg_0 = &stg_1;



    uint _S21 = gid_0.x;

#line 1548
    uint _S22 = _S21 / 512U;

#line 1548
    uint _S23 = _S21 % 512U;
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 1552
    uint m_1 = 0U;
    for(;;)
    {

#line 1553
        if(m_1 < 16U)
        {
        }
        else
        {

#line 1553
            break;
        }

#line 1554
        r_5[m_1] = float2(*((&kernelContext_4)->entryPointParams_scratch_0+(_S22 * 131072U + _S23 * 256U + tid_1 + 16U * m_1))) ;

#line 1553
        m_1 = m_1 + 1U;

#line 1553
    }

#line 1553
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 1553
    uint i_3 = 0U;


    for(;;)
    {

#line 1556
        if(i_3 < 16U)
        {
        }
        else
        {

#line 1556
            break;
        }

#line 1556
        *((&kernelContext_4)->entryPointParams_spectra_0+(_S22 * 131072U + slotToIndex_0(tid_1 * 16U + i_3) * 512U + _S23)) = packed_float2(float2(r_5[i_3].x, - r_5[i_3].y)) ;

#line 1556
        i_3 = i_3 + 1U;

#line 1556
    }



    return;
}
