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


#line 467 "/tmp/tmpoo7rlohu/tier0.slang"
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


#line 503
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_1 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_1 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_1 = float2(0.0f, 1.0f);
    float2 W6_1 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_1 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 510
    uint n1_1 = 0U;
    for(;;)
    {

#line 511
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 511
            break;
        }

#line 511
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 511
        n1_1 = n1_1 + 1U;

#line 511
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 512
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 512
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 513
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 513
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 514
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 514
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 514
    uint k2_1 = 0U;
    for(;;)
    {

#line 515
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 515
            break;
        }

#line 515
        uint _S7 = 4U * k2_1;

#line 515
        r4_0(&(*r_1)[_S7], &(*r_1)[_S7 + 1U], &(*r_1)[_S7 + 2U], &(*r_1)[_S7 + 3U]);

#line 515
        k2_1 = k2_1 + 1U;

#line 515
    }

    float2 t_6 = (*r_1)[int(1)];

#line 517
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 517
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 518
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 518
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 519
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 519
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 520
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 520
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 521
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 521
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 522
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 522
    (*r_1)[int(14)] = t_11;
    return;
}


#line 66 "/home/ahnitz/projects/claude/searchdev/work/mf-next/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 263 "/tmp/tmpoo7rlohu/tier0.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S8 = max(TB_0, 1U);

#line 265
    uint j_0 = d_1 / _S8;

#line 265
    uint m_0 = d_1 % _S8;

#line 265
    uint _S9;
    if(TB_0 <= 16U)
    {

#line 266
        _S9 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 266
    }
    else
    {

#line 266
        _S9 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 266
    }

#line 266
    return _S9;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint seriesLength_0;
    uint B0_0;
    uint B1_0;
};


#line 682 "/tmp/tmpoo7rlohu/tier0.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    uint device* entryPointParams_band0_0;
    packed_float2 device* entryPointParams_band1_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(4096)> threadgroup* stg_0;
};


#line 652
void exchange_0(array<float2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S10 = (1U << lgSpan_0) - 1U;
    uint _S11 = (1U << lgLen_0) - 1U;
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
        uint rem_0 = p_0 & _S11;
        src_0[d_2] = (rem_0 >> lgSpan_0) * 256U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S10);

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
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 256U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_2)[j_1].x)));

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
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 256U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_2)[j_1].y)));

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
        (*r_2)[d_2] = float2(xr_0[d_2], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]]))));

#line 688
        d_2 = d_2 + 1U;

#line 688
    }

    return;
}


#line 606
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 613
    dft16_1(r_3);

#line 618
    return;
}


#line 2068
void forwardTransform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 2068
    uint _S12;

#line 2068
    uint k2_2;

#line 2068
    float cr_0;

#line 2068
    float ci_0;

#line 2068
    uint _S13;

#line 2068
    for(;;)
    {

#line 2068
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/mf-next/src/gpu/fft_transform.slang"
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
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 4096.0f);
                float _S14 = tw_0.x;

#line 27
                float _S15 = tw_0.y;

#line 27
                k2_2 = 0U;

#line 27
                cr_0 = 1.0f;

#line 27
                ci_0 = 0.0f;

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
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 256.0f);
                float _S18 = tw_1.x;

#line 27
                float _S19 = tw_1.y;

#line 27
                k2_2 = 0U;

#line 27
                cr_0 = 1.0f;

#line 27
                ci_0 = 0.0f;

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

#line 2071 "/tmp/tmpoo7rlohu/tier0.slang"
    return;
}


#line 751
uint lgOf_0(uint i_0)
{

#line 751
    uint _S22;

#line 751
    if(i_0 < 2U)
    {

#line 751
        _S22 = 4U;

#line 751
    }
    else
    {

#line 751
        if(i_0 == 2U)
        {

#line 751
            _S22 = 4U;

#line 751
        }
        else
        {

#line 751
            _S22 = 1U;

#line 751
        }

#line 751
    }

#line 751
    return _S22;
}


#line 753
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 757
    uint lg_1 = lgOf_0(1U);

#line 757
    uint lg_2 = lgOf_0(0U);

#line 762
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2214
[[kernel]] void forwardTier0(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], uint device* entryPointParams_band0_1 [[buffer(3)]], packed_float2 device* entryPointParams_band1_1 [[buffer(4)]])
{

#line 2214
    thread KernelContext_0 kernelContext_2;

#line 2214
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2214
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2214
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2214
    (&kernelContext_2)->entryPointParams_band0_0 = entryPointParams_band0_1;

#line 2214
    (&kernelContext_2)->entryPointParams_band1_0 = entryPointParams_band1_1;

#line 2214
    threadgroup array<uint, int(4096)> stg_1;

#line 2214
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2221
    uint tid_1 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_1;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S23 = gid_0.x;

#line 2224
    uint _S24 = entryPointParams_starts_1[_S23];
    thread array<float2, int(16)> r_5;

#line 2225
    uint k_0 = 0U;
    for(;;)
    {

#line 2226
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2226
            break;
        }

#line 2227
        uint offset_0 = tid_1 + 256U * k_0;
        float2 _S25 = float2(0.0f, 0.0f);

#line 2228
        bool _S26;
        if(_S24 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2229
            _S26 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S24);

#line 2229
        }
        else
        {

#line 2229
            _S26 = false;

#line 2229
        }

#line 2229
        float2 x_1;

#line 2229
        if(_S26)
        {

#line 2229
            x_1 = float2(*((&kernelContext_2)->entryPointParams_series_0+(_S24 + offset_0))) ;

#line 2229
        }
        else
        {

#line 2229
            x_1 = _S25;

#line 2229
        }

        r_5[k_0] = float2(x_1.x / 4096.0f, - x_1.y / 4096.0f);

#line 2226
        k_0 = k_0 + 1U;

#line 2226
    }

#line 2226
    forwardTransform_0(&r_5, tid_1, &kernelContext_2);

#line 2226
    k_0 = 0U;

#line 2234
    for(;;)
    {

#line 2234
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2234
            break;
        }

#line 2235
        uint index_0 = slotToIndex_0(tid_1 * 16U + k_0);
        float _S27 = r_5[k_0].x;

#line 2236
        float _S28 = - r_5[k_0].y;

#line 2236
        float2 v_0 = float2(_S27, _S28);
        if(index_0 < ((&kernelContext_2)->entryPointParams_0->B0_0))
        {

#line 2238
            *((&kernelContext_2)->entryPointParams_band0_0+(_S23 * (&kernelContext_2)->entryPointParams_0->B0_0 + index_0)) = (as_type<ushort>((half)((_S27)))) | ((as_type<ushort>((half)((_S28)))) << 16U);

#line 2237
        }

        if(index_0 < ((&kernelContext_2)->entryPointParams_0->B1_0))
        {

#line 2239
            *((&kernelContext_2)->entryPointParams_band1_0+(_S23 * (&kernelContext_2)->entryPointParams_0->B1_0 + index_0)) = packed_float2(v_0) ;

#line 2239
        }

#line 2234
        k_0 = k_0 + 1U;

#line 2234
    }

#line 2242
    return;
}
