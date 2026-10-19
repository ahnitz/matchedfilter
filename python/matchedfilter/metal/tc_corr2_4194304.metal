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


#line 498 "/home/ahnitz/projects/claude/searchdev/work/mf-backends/python/matchedfilter/metal/tc_corr2_4194304.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 500
    float2 t1_0 = *a_0 - *c_0;

#line 500
    float2 t2_0 = *b_0 + *d_0;

#line 500
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 502
    *b_0 = t1_0 + j3_0;

#line 502
    *c_0 = t0_0 - t2_0;

#line 502
    *d_0 = t1_0 - j3_0;
    return;
}


#line 292
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 292
    float _S2 = a_1.x;

#line 292
    float _S3 = b_1.x;

#line 292
    float _S4 = a_1.y;

#line 292
    float _S5 = b_1.y;

#line 292
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 534
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 541
    uint n1_0 = 0U;
    for(;;)
    {

#line 542
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 542
            break;
        }

#line 542
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 542
        n1_0 = n1_0 + 1U;

#line 542
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 543
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 543
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 544
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 544
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 545
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 545
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 545
    uint k2_0 = 0U;
    for(;;)
    {

#line 546
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 546
            break;
        }

#line 546
        uint _S6 = 4U * k2_0;

#line 546
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 546
        k2_0 = k2_0 + 1U;

#line 546
    }

    float2 t_0 = (*r_0)[int(1)];

#line 548
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 548
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 549
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 549
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 550
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 550
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 551
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 551
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 552
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 552
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 553
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 553
    (*r_0)[int(14)] = t_5;
    return;
}


#line 127 "/home/ahnitz/projects/claude/searchdev/work/mf-backends/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 294 "/home/ahnitz/projects/claude/searchdev/work/mf-backends/python/matchedfilter/metal/tc_corr2_4194304.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S7 = max(TB_0, 1U);

#line 296
    uint j_0 = d_1 / _S7;

#line 296
    uint m_0 = d_1 % _S7;

#line 296
    uint _S8;
    if(TB_0 <= 16U)
    {

#line 297
        _S8 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 297
    }
    else
    {

#line 297
        _S8 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 297
    }

#line 297
    return _S8;
}


#line 281
struct KernelContext_0
{
    packed_float2 device* entryPointParams_scratch_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 281
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 281
    uint _S9 = 2U * i_0;

#line 281
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9] = (as_type<uint>((v_0.x)));

#line 281
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9 + 1U] = (as_type<uint>((v_0.y)));

#line 281
    return;
}


#line 282
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 282
    uint _S10 = 2U * i_1;

#line 282
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10 + 1U]))));
}


#line 723
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 724
    uint j_1;

#line 735
    thread array<float2, int(16)> out_0;

#line 735
    uint z_0 = 0U;
    for(;;)
    {

#line 736
        if(z_0 < 16U)
        {
        }
        else
        {

#line 736
            break;
        }

#line 736
        out_0[z_0] = float2(0.0f, 0.0f);

#line 736
        z_0 = z_0 + 1U;

#line 736
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S11 = p0_0 & lenMask_0;

#line 742
    uint _S12 = _S11 >> lgSpan_0;

#line 742
    uint _S13 = _S12 * 128U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S11 & spanMask_0);

#line 742
    uint c_1 = 0U;

    for(;;)
    {

#line 744
        if(c_1 < 2U)
        {
        }
        else
        {

#line 744
            break;
        }

#line 745
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 745
        j_1 = 0U;
        for(;;)
        {

#line 746
            if(j_1 < 8U)
            {
            }
            else
            {

#line 746
                break;
            }

#line 746
            stgPut_0(j_1 * 128U + kernelContext_2->_tid_0, (*r_1)[c_1 * 8U + j_1], kernelContext_2);

#line 746
            j_1 = j_1 + 1U;

#line 746
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 747
        uint d_2 = 0U;
        for(;;)
        {

#line 748
            if(d_2 < 16U)
            {
            }
            else
            {

#line 748
                break;
            }

#line 749
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S14 = pz_0 & lenMask_0;

#line 750
            uint iz_0 = _S14 >> lgSpan_0;
            uint az_0 = iz_0 * 128U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);
            uint i_2 = _S12 + iz_0;
            uint _S15 = c_1 * 8U;

#line 753
            bool _S16;

#line 753
            if(i_2 >= _S15)
            {

#line 753
                _S16 = i_2 < ((c_1 + 1U) * 8U);

#line 753
            }
            else
            {

#line 753
                _S16 = false;

#line 753
            }

#line 753
            if(_S16)
            {

#line 753
                float2 _S17 = stgGet_0(_S13 + az_0 - _S15 * 128U, kernelContext_2);
                out_0[d_2] = _S17;

#line 753
            }

#line 748
            d_2 = d_2 + 1U;

#line 748
        }

#line 744
        c_1 = c_1 + 1U;

#line 744
    }

#line 744
    j_1 = 0U;

#line 757
    for(;;)
    {

#line 757
        if(j_1 < 16U)
        {
        }
        else
        {

#line 757
            break;
        }

#line 757
        (*r_1)[j_1] = out_0[j_1];

#line 757
        j_1 = j_1 + 1U;

#line 757
    }
    return;
}


#line 518
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_2;

#line 522
    uint s_0 = 1U;
    for(;;)
    {

#line 523
        if(s_0 < 8U)
        {
        }
        else
        {

#line 523
            break;
        }

#line 523
        uint j_2 = 0U;
        for(;;)
        {

#line 524
            if(j_2 < 4U)
            {
            }
            else
            {

#line 524
                break;
            }

#line 525
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S18 = o_0 + j_2;

#line 528
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_0)), (*r_2)[_S18 + 4U]);
            uint _S19 = ((j_2 - k_0) << 1U) + k_0;

#line 529
            b_2[_S19] = (*r_2)[_S18] + t_6;

#line 529
            b_2[_S19 + s_0] = (*r_2)[_S18] - t_6;

#line 524
            j_2 = j_2 + 1U;

#line 524
        }

#line 524
        uint i_3 = 0U;

#line 531
        for(;;)
        {

#line 531
            if(i_3 < 8U)
            {
            }
            else
            {

#line 531
                break;
            }

#line 531
            (*r_2)[o_0 + i_3] = b_2[i_3];

#line 531
            i_3 = i_3 + 1U;

#line 531
        }

#line 523
        s_0 = s_0 << 1U;

#line 523
    }

#line 533
    return;
}


#line 637
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 637
    uint b_3 = 0U;

#line 645
    for(;;)
    {

#line 645
        if(b_3 < 2U)
        {
        }
        else
        {

#line 645
            break;
        }

#line 645
        dft8_0(r_3, b_3 * 8U);

#line 645
        b_3 = b_3 + 1U;

#line 645
    }



    return;
}


#line 825
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 825
    uint _S20;

#line 825
    uint k2_1;

#line 825
    float cr_0;

#line 825
    float ci_0;

#line 825
    uint _S21;

#line 825
    for(;;)
    {

#line 825
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/mf-backends/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(128U);

#line 11
                _S20 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(2048U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 127U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 2048.0f);
                float _S22 = tw_0.x;

#line 40
                float _S23 = tw_0.y;

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
                    float nr_0 = cr_0 * _S22 - ci_0 * _S23;
                    float _S24 = cr_0 * _S23 + ci_0 * _S22;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S24;

#line 42
                }

#line 50
                uint per_2 = 16U / max(128U, 1U);
                uint _S25 = max(8U, 1U);

#line 51
                _S21 = _S25;
                uint blk2_2 = tid_0 / _S25;

#line 52
                uint lane2_2 = tid_0 % _S25;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 128U, 2048U, blk_2, lane_2, per_2, _S25, 128U, blk2_2, lane2_2, kernelContext_3);

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

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 128.0f);
                float _S26 = tw_1.x;

#line 40
                float _S27 = tw_1.y;

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
                    float nr_1 = cr_0 * _S26 - ci_0 * _S27;
                    float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S28;

#line 42
                }

#line 50
                uint per_3 = 16U / _S21;
                uint _S29 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S29;

#line 52
                uint lane2_3 = tid_0 % _S29;

#line 52
                exchange_0(r_4, _S20, lgTB_1, 8U, 128U, blk_3, lane_3, per_3, _S29, 8U, blk2_3, lane2_3, kernelContext_3);

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

#line 828 "/home/ahnitz/projects/claude/searchdev/work/mf-backends/python/matchedfilter/metal/tc_corr2_4194304.slang"
    return;
}


#line 782
uint lgOf_0(uint i_4)
{

#line 782
    uint _S30;

#line 782
    if(i_4 < 2U)
    {

#line 782
        _S30 = 4U;

#line 782
    }
    else
    {

#line 782
        if(i_4 == 2U)
        {

#line 782
            _S30 = 3U;

#line 782
        }
        else
        {

#line 782
            _S30 = 1U;

#line 782
        }

#line 782
    }

#line 782
    return _S30;
}


#line 784
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 788
    uint lg_1 = lgOf_0(1U);

#line 788
    uint lg_2 = lgOf_0(0U);

#line 793
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2032
[[kernel]] void tcFullStage3(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], packed_float2 device* entryPointParams_scratch_1 [[buffer(0)]], packed_float2 device* entryPointParams_output_1 [[buffer(1)]])
{

#line 2032
    thread KernelContext_0 kernelContext_4;

#line 2032
    (&kernelContext_4)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 2032
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 2032
    threadgroup array<uint, int(2048)> stg_1;

#line 2032
    (&kernelContext_4)->stg_0 = &stg_1;



    uint _S31 = gid_0.x;

#line 2036
    uint _S32 = _S31 / 2048U;

#line 2036
    uint _S33 = _S31 % 2048U;
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 2040
    uint m_1 = 0U;
    for(;;)
    {

#line 2041
        if(m_1 < 16U)
        {
        }
        else
        {

#line 2041
            break;
        }

#line 2042
        r_5[m_1] = float2(*((&kernelContext_4)->entryPointParams_scratch_0+(_S32 * 4194304U + _S33 * 2048U + tid_1 + 128U * m_1))) ;

#line 2041
        m_1 = m_1 + 1U;

#line 2041
    }

#line 2041
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 2041
    uint i_5 = 0U;


    for(;;)
    {

#line 2044
        if(i_5 < 16U)
        {
        }
        else
        {

#line 2044
            break;
        }

#line 2044
        *((&kernelContext_4)->entryPointParams_output_0+(_S32 * 4194304U + slotToIndex_0(tid_1 * 16U + i_5) * 2048U + _S33)) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 2044
        i_5 = i_5 + 1U;

#line 2044
    }



    return;
}
