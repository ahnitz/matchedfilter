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


#line 486 "/tmp/tmpqg750mrc/tier0.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 488
    float2 t1_0 = *a_0 - *c_0;

#line 488
    float2 t2_0 = *b_0 + *d_0;

#line 488
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 490
    *b_0 = t1_0 + j3_0;

#line 490
    *c_0 = t0_0 - t2_0;

#line 490
    *d_0 = t1_0 - j3_0;
    return;
}


#line 280
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 280
    float _S2 = a_1.x;

#line 280
    float _S3 = b_1.x;

#line 280
    float _S4 = a_1.y;

#line 280
    float _S5 = b_1.y;

#line 280
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 522
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 529
    uint n1_0 = 0U;
    for(;;)
    {

#line 530
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 530
            break;
        }

#line 530
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 530
        n1_0 = n1_0 + 1U;

#line 530
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 531
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 531
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 532
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 532
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 533
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 533
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 533
    uint k2_0 = 0U;
    for(;;)
    {

#line 534
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 534
            break;
        }

#line 534
        uint _S6 = 4U * k2_0;

#line 534
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 534
        k2_0 = k2_0 + 1U;

#line 534
    }

    float2 t_0 = (*r_0)[int(1)];

#line 536
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 536
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 537
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 537
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 538
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 538
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 539
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 539
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 540
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 540
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 541
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 541
    (*r_0)[int(14)] = t_5;
    return;
}


#line 84 "/home/ahnitz/projects/claude/searchdev/work/mf-gpu-c16/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 282 "/tmp/tmpqg750mrc/tier0.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S7 = max(TB_0, 1U);

#line 284
    uint j_0 = d_1 / _S7;

#line 284
    uint m_0 = d_1 % _S7;

#line 284
    uint _S8;
    if(TB_0 <= 16U)
    {

#line 285
        _S8 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 285
    }
    else
    {

#line 285
        _S8 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 285
    }

#line 285
    return _S8;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint seriesLength_0;
    uint B0_0;
    uint B1_0;
};


#line 701 "/tmp/tmpqg750mrc/tier0.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    uint device* entryPointParams_band0_0;
    packed_float2 device* entryPointParams_band1_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 671
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S9 = (1U << lgSpan_0) - 1U;
    uint _S10 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

#line 676
    uint d_2 = 0U;
    for(;;)
    {

#line 677
        if(d_2 < 16U)
        {
        }
        else
        {

#line 677
            break;
        }

#line 678
        uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
        uint rem_0 = p_0 & _S10;
        src_0[d_2] = (rem_0 >> lgSpan_0) * 512U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S9);

#line 677
        d_2 = d_2 + 1U;

#line 677
    }

#line 682
    thread array<float, int(16)> xr_0;

#line 700
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 700
    uint j_1 = 0U;
    for(;;)
    {

#line 701
        if(j_1 < 16U)
        {
        }
        else
        {

#line 701
            break;
        }

#line 701
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 512U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].x)));

#line 701
        j_1 = j_1 + 1U;

#line 701
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 702
    d_2 = 0U;
    for(;;)
    {

#line 703
        if(d_2 < 16U)
        {
        }
        else
        {

#line 703
            break;
        }

#line 703
        xr_0[d_2] = (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]])));

#line 703
        d_2 = d_2 + 1U;

#line 703
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 704
    j_1 = 0U;
    for(;;)
    {

#line 705
        if(j_1 < 16U)
        {
        }
        else
        {

#line 705
            break;
        }

#line 705
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 512U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].y)));

#line 705
        j_1 = j_1 + 1U;

#line 705
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 706
    d_2 = 0U;
    for(;;)
    {

#line 707
        if(d_2 < 16U)
        {
        }
        else
        {

#line 707
            break;
        }

#line 707
        (*r_1)[d_2] = float2(xr_0[d_2], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]]))));

#line 707
        d_2 = d_2 + 1U;

#line 707
    }

    return;
}


#line 497
void dft2_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    float2 a_2 = (*r_2)[o_0];

#line 499
    float2 b_2 = (*r_2)[o_0 + 1U];

#line 499
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 499
    (*r_2)[o_0 + 1U] = a_2 - b_2;
    return;
}


#line 625
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 625
    uint b_3 = 0U;

#line 635
    for(;;)
    {

#line 635
        if(b_3 < 8U)
        {
        }
        else
        {

#line 635
            break;
        }

#line 635
        dft2_0(r_3, b_3 * 2U);

#line 635
        b_3 = b_3 + 1U;

#line 635
    }

    return;
}


#line 2102
void forwardTransform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 2102
    uint _S11;

#line 2102
    uint k2_1;

#line 2102
    float cr_0;

#line 2102
    float ci_0;

#line 2102
    uint _S12;

#line 2102
    uint _S13;

#line 2102
    uint _S14;

#line 2102
    for(;;)
    {

#line 2102
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/mf-gpu-c16/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(512U);

#line 11
                _S11 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(8192U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 511U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 8192.0f);
                float _S15 = tw_0.x;

#line 40
                float _S16 = tw_0.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S15 - ci_0 * _S16;
                    float _S17 = cr_0 * _S16 + ci_0 * _S15;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S17;

#line 42
                }

#line 50
                uint per_2 = 16U / max(512U, 1U);
                uint _S18 = max(32U, 1U);

#line 51
                _S12 = _S18;
                uint blk2_2 = tid_0 / _S18;

#line 52
                uint lane2_2 = tid_0 % _S18;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 512U, 8192U, blk_2, lane_2, per_2, _S18, 512U, blk2_2, lane2_2, kernelContext_1);

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


                uint lgTB_1 = firstbithigh_0(32U);

#line 11
                _S13 = lgTB_1;

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 31U;


                dft16_0(r_4);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 512.0f);
                float _S19 = tw_1.x;

#line 40
                float _S20 = tw_1.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S19 - ci_0 * _S20;
                    float _S21 = cr_0 * _S20 + ci_0 * _S19;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S21;

#line 42
                }

#line 50
                uint per_3 = 16U / _S12;
                uint _S22 = max(2U, 1U);

#line 51
                _S14 = _S22;
                uint blk2_3 = tid_0 / _S22;

#line 52
                uint lane2_3 = tid_0 % _S22;

#line 52
                exchange_0(r_4, _S11, lgTB_1, 32U, 512U, blk_3, lane_3, per_3, _S22, 32U, blk2_3, lane2_3, kernelContext_1);

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


                uint lgTB_2 = firstbithigh_0(2U);

                uint blk_4 = tid_0 >> lgTB_2;
                uint lane_4 = tid_0 & 1U;


                dft16_0(r_4);

#line 39
                float2 tw_2 = mfTwiddle_0(6.28318548202514648f * float(lane_4) / 32.0f);
                float _S23 = tw_2.x;

#line 40
                float _S24 = tw_2.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_2 = cr_0 * _S23 - ci_0 * _S24;
                    float _S25 = cr_0 * _S24 + ci_0 * _S23;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_2;

#line 42
                    ci_0 = _S25;

#line 42
                }

#line 50
                uint per_4 = 16U / _S14;
                uint _S26 = max(0U, 1U);
                uint blk2_4 = tid_0 / _S26;

#line 52
                uint lane2_4 = tid_0 % _S26;

#line 52
                exchange_0(r_4, _S13, lgTB_2, 2U, 32U, blk_4, lane_4, per_4, _S26, 2U, blk2_4, lane2_4, kernelContext_1);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        break;
    }

#line 56
    innermost_0(r_4);

#line 2105 "/tmp/tmpqg750mrc/tier0.slang"
    return;
}


#line 770
uint lgOf_0(uint i_0)
{

#line 770
    uint _S27;

#line 770
    if(i_0 < 3U)
    {

#line 770
        _S27 = 4U;

#line 770
    }
    else
    {

#line 770
        _S27 = 1U;

#line 770
    }

#line 770
    return _S27;
}


#line 772
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 776
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 776
    uint lg_2 = lgOf_0(1U);

#line 776
    uint lg_3 = lgOf_0(0U);

#line 781
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 2248
[[kernel]] void forwardTier0(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], uint device* entryPointParams_band0_1 [[buffer(3)]], packed_float2 device* entryPointParams_band1_1 [[buffer(4)]])
{

#line 2248
    thread KernelContext_0 kernelContext_2;

#line 2248
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2248
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2248
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2248
    (&kernelContext_2)->entryPointParams_band0_0 = entryPointParams_band0_1;

#line 2248
    (&kernelContext_2)->entryPointParams_band1_0 = entryPointParams_band1_1;

#line 2248
    threadgroup array<uint, int(8192)> stg_1;

#line 2248
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2255
    uint tid_1 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_1;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S28 = gid_0.x;

#line 2258
    uint _S29 = entryPointParams_starts_1[_S28];
    thread array<float2, int(16)> r_5;

#line 2259
    uint k_0 = 0U;
    for(;;)
    {

#line 2260
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2260
            break;
        }

#line 2261
        uint offset_0 = tid_1 + 512U * k_0;
        float2 _S30 = float2(0.0f, 0.0f);

#line 2262
        bool _S31;
        if(_S29 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2263
            _S31 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S29);

#line 2263
        }
        else
        {

#line 2263
            _S31 = false;

#line 2263
        }

#line 2263
        float2 x_2;

#line 2263
        if(_S31)
        {

#line 2263
            x_2 = float2(*((&kernelContext_2)->entryPointParams_series_0+(_S29 + offset_0))) ;

#line 2263
        }
        else
        {

#line 2263
            x_2 = _S30;

#line 2263
        }

        r_5[k_0] = float2(x_2.x / 8192.0f, - x_2.y / 8192.0f);

#line 2260
        k_0 = k_0 + 1U;

#line 2260
    }

#line 2260
    forwardTransform_0(&r_5, tid_1, &kernelContext_2);

#line 2260
    k_0 = 0U;

#line 2268
    for(;;)
    {

#line 2268
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2268
            break;
        }

#line 2269
        uint index_0 = slotToIndex_0(tid_1 * 16U + k_0);
        float _S32 = r_5[k_0].x;

#line 2270
        float _S33 = - r_5[k_0].y;

#line 2270
        float2 v_0 = float2(_S32, _S33);
        if(index_0 < ((&kernelContext_2)->entryPointParams_0->B0_0))
        {

#line 2272
            *((&kernelContext_2)->entryPointParams_band0_0+(_S28 * (&kernelContext_2)->entryPointParams_0->B0_0 + index_0)) = (as_type<ushort>((half)((_S32)))) | ((as_type<ushort>((half)((_S33)))) << 16U);

#line 2271
        }

        if(index_0 < ((&kernelContext_2)->entryPointParams_0->B1_0))
        {

#line 2273
            *((&kernelContext_2)->entryPointParams_band1_0+(_S28 * (&kernelContext_2)->entryPointParams_0->B1_0 + index_0)) = packed_float2(v_0) ;

#line 2273
        }

#line 2268
        k_0 = k_0 + 1U;

#line 2268
    }

#line 2276
    return;
}
