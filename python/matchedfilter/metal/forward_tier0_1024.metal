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


#line 467 "/tmp/tmpulh0buh6/tier0.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 469
    float2 t1_0 = *a_0 - *c_0;

#line 469
    float2 t2_0 = *b_0 + *d_0;

#line 469
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 471
    *b_0 = t1_0 + j3_0;

#line 471
    *c_0 = t0_0 - t2_0;

#line 471
    *d_0 = t1_0 - j3_0;
    return;
}


#line 261
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 261
    float _S2 = a_1.x;

#line 261
    float _S3 = b_1.x;

#line 261
    float _S4 = a_1.y;

#line 261
    float _S5 = b_1.y;

#line 261
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 503
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

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
        uint _S6 = 4U * k2_0;

#line 515
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

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


#line 84 "/home/ahnitz/projects/claude/searchdev/work/mf-gpu-c16/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 263 "/tmp/tmpulh0buh6/tier0.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S7 = max(TB_0, 1U);

#line 265
    uint j_0 = d_1 / _S7;

#line 265
    uint m_0 = d_1 % _S7;

#line 265
    uint _S8;
    if(TB_0 <= 16U)
    {

#line 266
        _S8 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 266
    }
    else
    {

#line 266
        _S8 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 266
    }

#line 266
    return _S8;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint seriesLength_0;
    uint B0_0;
    uint B1_0;
};


#line 682 "/tmp/tmpulh0buh6/tier0.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    uint device* entryPointParams_band0_0;
    packed_float2 device* entryPointParams_band1_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 652
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S9 = (1U << lgSpan_0) - 1U;
    uint _S10 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

#line 657
    uint d_2 = 0U;
    for(;;)
    {

#line 658
        if(d_2 < 16U)
        {
        }
        else
        {

#line 658
            break;
        }

#line 659
        uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
        uint rem_0 = p_0 & _S10;
        src_0[d_2] = (rem_0 >> lgSpan_0) * 64U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S9);

#line 658
        d_2 = d_2 + 1U;

#line 658
    }

#line 663
    thread array<float, int(16)> xr_0;

#line 681
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 681
    uint j_1 = 0U;
    for(;;)
    {

#line 682
        if(j_1 < 16U)
        {
        }
        else
        {

#line 682
            break;
        }

#line 682
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 64U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].x)));

#line 682
        j_1 = j_1 + 1U;

#line 682
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 683
    d_2 = 0U;
    for(;;)
    {

#line 684
        if(d_2 < 16U)
        {
        }
        else
        {

#line 684
            break;
        }

#line 684
        xr_0[d_2] = (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]])));

#line 684
        d_2 = d_2 + 1U;

#line 684
    }
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
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 64U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].y)));

#line 686
        j_1 = j_1 + 1U;

#line 686
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 687
    d_2 = 0U;
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

#line 688
        (*r_1)[d_2] = float2(xr_0[d_2], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]]))));

#line 688
        d_2 = d_2 + 1U;

#line 688
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
    uint b_2 = 0U;

#line 615
    for(;;)
    {

#line 615
        if(b_2 < 4U)
        {
        }
        else
        {

#line 615
            break;
        }

#line 615
        dft4_0(r_3, b_2 * 4U);

#line 615
        b_2 = b_2 + 1U;

#line 615
    }


    return;
}


#line 2067
void forwardTransform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 2067
    uint _S11;

#line 2067
    uint k2_1;

#line 2067
    float cr_0;

#line 2067
    float ci_0;

#line 2067
    uint _S12;

#line 2067
    for(;;)
    {

#line 2067
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/mf-gpu-c16/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(64U);

#line 11
                _S11 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(1024U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 63U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);
                float _S13 = tw_0.x;

#line 40
                float _S14 = tw_0.y;

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
                    float nr_0 = cr_0 * _S13 - ci_0 * _S14;
                    float _S15 = cr_0 * _S14 + ci_0 * _S13;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S15;

#line 42
                }

#line 50
                uint per_2 = 16U / max(64U, 1U);
                uint _S16 = max(4U, 1U);

#line 51
                _S12 = _S16;
                uint blk2_2 = tid_0 / _S16;

#line 52
                uint lane2_2 = tid_0 % _S16;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 64U, 1024U, blk_2, lane_2, per_2, _S16, 64U, blk2_2, lane2_2, kernelContext_1);

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

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 64.0f);
                float _S17 = tw_1.x;

#line 40
                float _S18 = tw_1.y;

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
                    float nr_1 = cr_0 * _S17 - ci_0 * _S18;
                    float _S19 = cr_0 * _S18 + ci_0 * _S17;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S19;

#line 42
                }

#line 50
                uint per_3 = 16U / _S12;
                uint _S20 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S20;

#line 52
                uint lane2_3 = tid_0 % _S20;

#line 52
                exchange_0(r_4, _S11, lgTB_1, 4U, 64U, blk_3, lane_3, per_3, _S20, 4U, blk2_3, lane2_3, kernelContext_1);

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

#line 2070 "/tmp/tmpulh0buh6/tier0.slang"
    return;
}


#line 751
uint lgOf_0(uint i_0)
{

#line 751
    uint _S21;

#line 751
    if(i_0 < 2U)
    {

#line 751
        _S21 = 4U;

#line 751
    }
    else
    {

#line 751
        _S21 = 1U;

#line 751
    }

#line 751
    return _S21;
}


#line 753
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 757
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 757
    uint lg_2 = lgOf_0(1U);

#line 757
    uint lg_3 = lgOf_0(0U);

#line 762
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 2213
[[kernel]] void forwardTier0(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], uint device* entryPointParams_band0_1 [[buffer(3)]], packed_float2 device* entryPointParams_band1_1 [[buffer(4)]])
{

#line 2213
    thread KernelContext_0 kernelContext_2;

#line 2213
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2213
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2213
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2213
    (&kernelContext_2)->entryPointParams_band0_0 = entryPointParams_band0_1;

#line 2213
    (&kernelContext_2)->entryPointParams_band1_0 = entryPointParams_band1_1;

#line 2213
    threadgroup array<uint, int(1024)> stg_1;

#line 2213
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2220
    uint tid_1 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_1;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S22 = gid_0.x;

#line 2223
    uint _S23 = entryPointParams_starts_1[_S22];
    thread array<float2, int(16)> r_5;

#line 2224
    uint k_0 = 0U;
    for(;;)
    {

#line 2225
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2225
            break;
        }

#line 2226
        uint offset_0 = tid_1 + 64U * k_0;
        float2 _S24 = float2(0.0f, 0.0f);

#line 2227
        bool _S25;
        if(_S23 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2228
            _S25 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S23);

#line 2228
        }
        else
        {

#line 2228
            _S25 = false;

#line 2228
        }

#line 2228
        float2 x_2;

#line 2228
        if(_S25)
        {

#line 2228
            x_2 = float2(*((&kernelContext_2)->entryPointParams_series_0+(_S23 + offset_0))) ;

#line 2228
        }
        else
        {

#line 2228
            x_2 = _S24;

#line 2228
        }

        r_5[k_0] = float2(x_2.x / 1024.0f, - x_2.y / 1024.0f);

#line 2225
        k_0 = k_0 + 1U;

#line 2225
    }

#line 2225
    forwardTransform_0(&r_5, tid_1, &kernelContext_2);

#line 2225
    k_0 = 0U;

#line 2233
    for(;;)
    {

#line 2233
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2233
            break;
        }

#line 2234
        uint index_0 = slotToIndex_0(tid_1 * 16U + k_0);
        float _S26 = r_5[k_0].x;

#line 2235
        float _S27 = - r_5[k_0].y;

#line 2235
        float2 v_0 = float2(_S26, _S27);
        if(index_0 < ((&kernelContext_2)->entryPointParams_0->B0_0))
        {

#line 2237
            *((&kernelContext_2)->entryPointParams_band0_0+(_S22 * (&kernelContext_2)->entryPointParams_0->B0_0 + index_0)) = (as_type<ushort>((half)((_S26)))) | ((as_type<ushort>((half)((_S27)))) << 16U);

#line 2236
        }

        if(index_0 < ((&kernelContext_2)->entryPointParams_0->B1_0))
        {

#line 2238
            *((&kernelContext_2)->entryPointParams_band1_0+(_S22 * (&kernelContext_2)->entryPointParams_0->B1_0 + index_0)) = packed_float2(v_0) ;

#line 2238
        }

#line 2233
        k_0 = k_0 + 1U;

#line 2233
    }

#line 2241
    return;
}
