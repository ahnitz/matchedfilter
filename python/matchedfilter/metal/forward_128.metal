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


#line 454 "/tmp/tmpn_cgxdwg/forward.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 456
    float2 t1_0 = *a_0 - *c_0;

#line 456
    float2 t2_0 = *b_0 + *d_0;

#line 456
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 458
    *b_0 = t1_0 + j3_0;

#line 458
    *c_0 = t0_0 - t2_0;

#line 458
    *d_0 = t1_0 - j3_0;
    return;
}


#line 248
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 248
    float _S2 = a_1.x;

#line 248
    float _S3 = b_1.x;

#line 248
    float _S4 = a_1.y;

#line 248
    float _S5 = b_1.y;

#line 248
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 490
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 497
    uint n1_0 = 0U;
    for(;;)
    {

#line 498
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 498
            break;
        }

#line 498
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 498
        n1_0 = n1_0 + 1U;

#line 498
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 499
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 499
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 500
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 500
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 501
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 501
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 501
    uint k2_0 = 0U;
    for(;;)
    {

#line 502
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 502
            break;
        }

#line 502
        uint _S6 = 4U * k2_0;

#line 502
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 502
        k2_0 = k2_0 + 1U;

#line 502
    }

    float2 t_0 = (*r_0)[int(1)];

#line 504
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 504
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 505
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 505
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 506
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 506
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 507
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 507
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 508
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 508
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 509
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 509
    (*r_0)[int(14)] = t_5;
    return;
}


#line 26 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 250 "/tmp/tmpn_cgxdwg/forward.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S7 = max(TB_0, 1U);

#line 252
    uint j_0 = d_1 / _S7;

#line 252
    uint m_0 = d_1 % _S7;

#line 252
    uint _S8;
    if(TB_0 <= 16U)
    {

#line 253
        _S8 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 253
    }
    else
    {

#line 253
        _S8 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 253
    }

#line 253
    return _S8;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint seriesLength_0;
};


#line 237 "/tmp/tmpn_cgxdwg/forward.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_spectra_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(256)> threadgroup* stg_0;
};


#line 237
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 237
    uint _S9 = 2U * i_0;

#line 237
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9] = (as_type<uint>((v_0.x)));

#line 237
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9 + 1U] = (as_type<uint>((v_0.y)));

#line 237
    return;
}


#line 238
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 238
    uint _S10 = 2U * i_1;

#line 238
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10 + 1U]))));
}


#line 650
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 651
    uint j_1;

#line 662
    thread array<float2, int(16)> out_0;

#line 662
    uint z_0 = 0U;
    for(;;)
    {

#line 663
        if(z_0 < 16U)
        {
        }
        else
        {

#line 663
            break;
        }

#line 663
        out_0[z_0] = float2(0.0, 0.0);

#line 663
        z_0 = z_0 + 1U;

#line 663
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S11 = p0_0 & lenMask_0;

#line 669
    uint _S12 = (_S11 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S11 & spanMask_0);

#line 669
    uint c_1 = 0U;

    for(;;)
    {

#line 671
        if(c_1 < 1U)
        {
        }
        else
        {

#line 671
            break;
        }

#line 672
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 672
        j_1 = 0U;
        for(;;)
        {

#line 673
            if(j_1 < 16U)
            {
            }
            else
            {

#line 673
                break;
            }

#line 673
            stgPut_0(j_1 * 8U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 673
            j_1 = j_1 + 1U;

#line 673
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 674
        uint d_2 = 0U;
        for(;;)
        {

#line 675
            if(d_2 < 16U)
            {
            }
            else
            {

#line 675
                break;
            }

#line 676
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S13 = pz_0 & lenMask_0;
            uint az_0 = (_S13 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

#line 678
            float2 _S14 = stgGet_0(_S12 + az_0 - c_1 * 16U * 8U, kernelContext_2);


            out_0[d_2] = _S14;

#line 675
            d_2 = d_2 + 1U;

#line 675
        }

#line 671
        c_1 = c_1 + 1U;

#line 671
    }

#line 671
    j_1 = 0U;

#line 684
    for(;;)
    {

#line 684
        if(j_1 < 16U)
        {
        }
        else
        {

#line 684
            break;
        }

#line 684
        (*r_1)[j_1] = out_0[j_1];

#line 684
        j_1 = j_1 + 1U;

#line 684
    }
    return;
}


#line 474
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_2;

#line 478
    uint s_0 = 1U;
    for(;;)
    {

#line 479
        if(s_0 < 8U)
        {
        }
        else
        {

#line 479
            break;
        }

#line 479
        uint j_2 = 0U;
        for(;;)
        {

#line 480
            if(j_2 < 4U)
            {
            }
            else
            {

#line 480
                break;
            }

#line 481
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S15 = o_0 + j_2;

#line 484
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0)), (*r_2)[_S15 + 4U]);
            uint _S16 = ((j_2 - k_0) << 1U) + k_0;

#line 485
            b_2[_S16] = (*r_2)[_S15] + t_6;

#line 485
            b_2[_S16 + s_0] = (*r_2)[_S15] - t_6;

#line 480
            j_2 = j_2 + 1U;

#line 480
        }

#line 480
        uint i_2 = 0U;

#line 487
        for(;;)
        {

#line 487
            if(i_2 < 8U)
            {
            }
            else
            {

#line 487
                break;
            }

#line 487
            (*r_2)[o_0 + i_2] = b_2[i_2];

#line 487
            i_2 = i_2 + 1U;

#line 487
        }

#line 479
        s_0 = s_0 << 1U;

#line 479
    }

#line 489
    return;
}


#line 593
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 593
    uint b_3 = 0U;

#line 601
    for(;;)
    {

#line 601
        if(b_3 < 2U)
        {
        }
        else
        {

#line 601
            break;
        }

#line 601
        dft8_0(r_3, b_3 * 8U);

#line 601
        b_3 = b_3 + 1U;

#line 601
    }



    return;
}


#line 1737
void forwardTransform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 1737
    for(;;)
    {

#line 1737
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(8U);
                uint lgLn_0 = firstbithigh_0(128U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 7U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 128.0);
                float _S17 = tw_0.x;

#line 27
                float _S18 = tw_0.y;

#line 27
                uint k2_1 = 0U;

#line 27
                float cr_0 = 1.0;

#line 27
                float ci_0 = 0.0;

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
                    float nr_0 = cr_0 * _S17 - ci_0 * _S18;
                    float _S19 = cr_0 * _S18 + ci_0 * _S17;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S19;

#line 29
                }

#line 37
                uint per_2 = 16U / max(8U, 1U);
                uint _S20 = max(0U, 1U);
                uint blk2_2 = tid_0 / _S20;

#line 39
                uint lane2_2 = tid_0 % _S20;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 8U, 128U, blk_2, lane_2, per_2, _S20, 8U, blk2_2, lane2_2, kernelContext_3);

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

#line 1740 "/tmp/tmpn_cgxdwg/forward.slang"
    return;
}


#line 709
uint lgOf_0(uint i_3)
{

#line 709
    uint _S21;

#line 709
    if(i_3 < 1U)
    {

#line 709
        _S21 = 4U;

#line 709
    }
    else
    {

#line 709
        if(i_3 == 1U)
        {

#line 709
            _S21 = 3U;

#line 709
        }
        else
        {

#line 709
            _S21 = 1U;

#line 709
        }

#line 709
    }

#line 709
    return _S21;
}


#line 711
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 715
    uint lg_1 = lgOf_0(0U);

#line 720
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 1745
[[kernel]] void seriesForward(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]])
{

#line 1745
    thread KernelContext_0 kernelContext_4;

#line 1745
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1745
    (&kernelContext_4)->entryPointParams_series_0 = entryPointParams_series_1;

#line 1745
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1745
    (&kernelContext_4)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 1745
    threadgroup array<uint, int(256)> stg_1;

#line 1745
    (&kernelContext_4)->stg_0 = &stg_1;

#line 1751
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    uint _S22 = gid_0.x;

#line 1754
    uint _S23 = entryPointParams_starts_1[_S22];
    thread array<float2, int(16)> r_5;

#line 1755
    uint k_1 = 0U;
    for(;;)
    {

#line 1756
        if(k_1 < 16U)
        {
        }
        else
        {

#line 1756
            break;
        }

#line 1757
        uint offset_0 = tid_1 + 8U * k_1;
        float2 _S24 = float2(0.0, 0.0);

#line 1758
        bool _S25;

        if(_S23 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0))
        {

#line 1760
            _S25 = offset_0 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0 - _S23);

#line 1760
        }
        else
        {

#line 1760
            _S25 = false;

#line 1760
        }

#line 1760
        float2 x_0;

#line 1760
        if(_S25)
        {

#line 1760
            x_0 = float2(*((&kernelContext_4)->entryPointParams_series_0+(_S23 + offset_0))) ;

#line 1760
        }
        else
        {

#line 1760
            x_0 = _S24;

#line 1760
        }

        r_5[k_1] = float2(x_0.x / 128.0, - x_0.y / 128.0);

#line 1756
        k_1 = k_1 + 1U;

#line 1756
    }

#line 1756
    forwardTransform_0(&r_5, tid_1, &kernelContext_4);

#line 1756
    k_1 = 0U;

#line 1765
    for(;;)
    {

#line 1765
        if(k_1 < 16U)
        {
        }
        else
        {

#line 1765
            break;
        }

#line 1765
        *((&kernelContext_4)->entryPointParams_spectra_0+(_S22 * 128U + slotToIndex_0(tid_1 * 16U + k_1))) = packed_float2(float2(r_5[k_1].x, - r_5[k_1].y)) ;

#line 1765
        k_1 = k_1 + 1U;

#line 1765
    }



    return;
}
