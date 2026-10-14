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


#line 470 "/tmp/tmpt7hbzwbx/forward.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 472
    float2 t1_0 = *a_0 - *c_0;

#line 472
    float2 t2_0 = *b_0 + *d_0;

#line 472
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 474
    *b_0 = t1_0 + j3_0;

#line 474
    *c_0 = t0_0 - t2_0;

#line 474
    *d_0 = t1_0 - j3_0;
    return;
}


#line 264
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 264
    float _S2 = a_1.x;

#line 264
    float _S3 = b_1.x;

#line 264
    float _S4 = a_1.y;

#line 264
    float _S5 = b_1.y;

#line 264
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 506
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 513
    uint n1_0 = 0U;
    for(;;)
    {

#line 514
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 514
            break;
        }

#line 514
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 514
        n1_0 = n1_0 + 1U;

#line 514
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 515
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 515
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 516
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 516
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 517
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 517
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 517
    uint k2_0 = 0U;
    for(;;)
    {

#line 518
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 518
            break;
        }

#line 518
        uint _S6 = 4U * k2_0;

#line 518
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 518
        k2_0 = k2_0 + 1U;

#line 518
    }

    float2 t_0 = (*r_0)[int(1)];

#line 520
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 520
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 521
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 521
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 522
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 522
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 523
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 523
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 524
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 524
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 525
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 525
    (*r_0)[int(14)] = t_5;
    return;
}


#line 72 "/home/ahnitz/projects/claude/searchdev/work/mf-next/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 266 "/tmp/tmpt7hbzwbx/forward.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S7 = max(TB_0, 1U);

#line 268
    uint j_0 = d_1 / _S7;

#line 268
    uint m_0 = d_1 % _S7;

#line 268
    uint _S8;
    if(TB_0 <= 16U)
    {

#line 269
        _S8 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 269
    }
    else
    {

#line 269
        _S8 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 269
    }

#line 269
    return _S8;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint seriesLength_0;
};


#line 685 "/tmp/tmpt7hbzwbx/forward.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_spectra_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 655
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_0)
{

    uint _S9 = (1U << lgSpan_0) - 1U;
    uint _S10 = (1U << lgLen_0) - 1U;
    thread array<uint, int(16)> src_0;

#line 660
    uint d_2 = 0U;
    for(;;)
    {

#line 661
        if(d_2 < 16U)
        {
        }
        else
        {

#line 661
            break;
        }

#line 662
        uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
        uint rem_0 = p_0 & _S10;
        src_0[d_2] = (rem_0 >> lgSpan_0) * 64U + ((p_0 >> lgLen_0) << lgSpan_0) + (rem_0 & _S9);

#line 661
        d_2 = d_2 + 1U;

#line 661
    }

#line 666
    thread array<float, int(16)> xr_0;

#line 684
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 684
    uint j_1 = 0U;
    for(;;)
    {

#line 685
        if(j_1 < 16U)
        {
        }
        else
        {

#line 685
            break;
        }

#line 685
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 64U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].x)));

#line 685
        j_1 = j_1 + 1U;

#line 685
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 686
    d_2 = 0U;
    for(;;)
    {

#line 687
        if(d_2 < 16U)
        {
        }
        else
        {

#line 687
            break;
        }

#line 687
        xr_0[d_2] = (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]])));

#line 687
        d_2 = d_2 + 1U;

#line 687
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 688
    j_1 = 0U;
    for(;;)
    {

#line 689
        if(j_1 < 16U)
        {
        }
        else
        {

#line 689
            break;
        }

#line 689
        (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + j_1 * 64U + kernelContext_0->_tid_0] = (as_type<uint>(((*r_1)[j_1].y)));

#line 689
        j_1 = j_1 + 1U;

#line 689
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 690
    d_2 = 0U;
    for(;;)
    {

#line 691
        if(d_2 < 16U)
        {
        }
        else
        {

#line 691
            break;
        }

#line 691
        (*r_1)[d_2] = float2(xr_0[d_2], (as_type<float>(((*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + src_0[d_2]]))));

#line 691
        d_2 = d_2 + 1U;

#line 691
    }

    return;
}


#line 485
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 488
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 488
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 609
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 609
    uint b_2 = 0U;

#line 618
    for(;;)
    {

#line 618
        if(b_2 < 4U)
        {
        }
        else
        {

#line 618
            break;
        }

#line 618
        dft4_0(r_3, b_2 * 4U);

#line 618
        b_2 = b_2 + 1U;

#line 618
    }


    return;
}


#line 2059
void forwardTransform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_1)
{

#line 2059
    uint _S11;

#line 2059
    uint k2_1;

#line 2059
    float cr_0;

#line 2059
    float ci_0;

#line 2059
    uint _S12;

#line 2059
    for(;;)
    {

#line 2059
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/mf-next/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(64U);

#line 11
                _S11 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(1024U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 63U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);
                float _S13 = tw_0.x;

#line 27
                float _S14 = tw_0.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0f;

#line 27
                ci_0 = 0.0f;

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
                    float nr_0 = cr_0 * _S13 - ci_0 * _S14;
                    float _S15 = cr_0 * _S14 + ci_0 * _S13;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S15;

#line 29
                }

#line 37
                uint per_2 = 16U / max(64U, 1U);
                uint _S16 = max(4U, 1U);

#line 38
                _S12 = _S16;
                uint blk2_2 = tid_0 / _S16;

#line 39
                uint lane2_2 = tid_0 % _S16;

#line 39
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

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 64.0f);
                float _S17 = tw_1.x;

#line 27
                float _S18 = tw_1.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0f;

#line 27
                ci_0 = 0.0f;

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
                    float nr_1 = cr_0 * _S17 - ci_0 * _S18;
                    float _S19 = cr_0 * _S18 + ci_0 * _S17;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S19;

#line 29
                }

#line 37
                uint per_3 = 16U / _S12;
                uint _S20 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S20;

#line 39
                uint lane2_3 = tid_0 % _S20;

#line 39
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

#line 43
    innermost_0(r_4);

#line 2062 "/tmp/tmpt7hbzwbx/forward.slang"
    return;
}


#line 754
uint lgOf_0(uint i_0)
{

#line 754
    uint _S21;

#line 754
    if(i_0 < 2U)
    {

#line 754
        _S21 = 4U;

#line 754
    }
    else
    {

#line 754
        _S21 = 1U;

#line 754
    }

#line 754
    return _S21;
}


#line 756
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 760
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 760
    uint lg_2 = lgOf_0(1U);

#line 760
    uint lg_3 = lgOf_0(0U);

#line 765
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 2067
[[kernel]] void seriesForward(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]])
{

#line 2067
    thread KernelContext_0 kernelContext_2;

#line 2067
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2067
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2067
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2067
    (&kernelContext_2)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 2067
    threadgroup array<uint, int(1024)> stg_1;

#line 2067
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2073
    uint tid_1 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_1;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S22 = gid_0.x;

#line 2076
    uint _S23 = entryPointParams_starts_1[_S22];
    thread array<float2, int(16)> r_5;

#line 2077
    uint k_0 = 0U;
    for(;;)
    {

#line 2078
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2078
            break;
        }

#line 2079
        uint offset_0 = tid_1 + 64U * k_0;
        float2 _S24 = float2(0.0f, 0.0f);

#line 2080
        bool _S25;

        if(_S23 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2082
            _S25 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S23);

#line 2082
        }
        else
        {

#line 2082
            _S25 = false;

#line 2082
        }

#line 2082
        float2 x_2;

#line 2082
        if(_S25)
        {

#line 2082
            x_2 = float2(*((&kernelContext_2)->entryPointParams_series_0+(_S23 + offset_0))) ;

#line 2082
        }
        else
        {

#line 2082
            x_2 = _S24;

#line 2082
        }

        r_5[k_0] = float2(x_2.x / 1024.0f, - x_2.y / 1024.0f);

#line 2078
        k_0 = k_0 + 1U;

#line 2078
    }

#line 2078
    forwardTransform_0(&r_5, tid_1, &kernelContext_2);

#line 2078
    k_0 = 0U;

#line 2087
    for(;;)
    {

#line 2087
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2087
            break;
        }

#line 2087
        *((&kernelContext_2)->entryPointParams_spectra_0+(_S22 * 1024U + slotToIndex_0(tid_1 * 16U + k_0))) = packed_float2(float2(r_5[k_0].x, - r_5[k_0].y)) ;

#line 2087
        k_0 = k_0 + 1U;

#line 2087
    }



    return;
}
