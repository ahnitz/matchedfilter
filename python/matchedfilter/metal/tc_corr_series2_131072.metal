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


#line 609 "tc_corr_series2_131072.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 611
    float2 t1_0 = *a_0 - *c_0;

#line 611
    float2 t2_0 = *b_0 + *d_0;

#line 611
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 613
    *b_0 = t1_0 + j3_0;

#line 613
    *c_0 = t0_0 - t2_0;

#line 613
    *d_0 = t1_0 - j3_0;
    return;
}


#line 322
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 322
    float _S2 = a_1.x;

#line 322
    float _S3 = b_1.x;

#line 322
    float _S4 = a_1.y;

#line 322
    float _S5 = b_1.y;

#line 322
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 645
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 652
    uint n1_0 = 0U;
    for(;;)
    {

#line 653
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 653
            break;
        }

#line 653
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 653
        n1_0 = n1_0 + 1U;

#line 653
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 654
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 654
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 655
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 655
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 656
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 656
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 656
    uint k2_0 = 0U;
    for(;;)
    {

#line 657
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 657
            break;
        }

#line 657
        uint _S6 = 4U * k2_0;

#line 657
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 657
        k2_0 = k2_0 + 1U;

#line 657
    }

    float2 t_0 = (*r_0)[int(1)];

#line 659
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 659
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 660
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 660
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 661
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 661
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 662
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 662
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 663
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 663
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 664
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 664
    (*r_0)[int(14)] = t_5;
    return;
}


#line 645
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_1 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_1 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_1 = float2(0.0f, 1.0f);
    float2 W6_1 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_1 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 652
    uint n1_1 = 0U;
    for(;;)
    {

#line 653
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 653
            break;
        }

#line 653
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 653
        n1_1 = n1_1 + 1U;

#line 653
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 654
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 654
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 655
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 655
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 656
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 656
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 656
    uint k2_1 = 0U;
    for(;;)
    {

#line 657
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 657
            break;
        }

#line 657
        uint _S7 = 4U * k2_1;

#line 657
        r4_0(&(*r_1)[_S7], &(*r_1)[_S7 + 1U], &(*r_1)[_S7 + 2U], &(*r_1)[_S7 + 3U]);

#line 657
        k2_1 = k2_1 + 1U;

#line 657
    }

    float2 t_6 = (*r_1)[int(1)];

#line 659
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 659
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 660
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 660
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 661
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 661
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 662
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 662
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 663
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 663
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 664
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 664
    (*r_1)[int(14)] = t_11;
    return;
}


#line 103 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 324 "tc_corr_series2_131072.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S8 = max(TB_0, 1U);

#line 326
    uint j_0 = d_1 / _S8;

#line 326
    uint m_0 = d_1 % _S8;

#line 326
    uint _S9;
    if(TB_0 <= 16U)
    {

#line 327
        _S9 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 327
    }
    else
    {

#line 327
        _S9 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 327
    }

#line 327
    return _S9;
}


#line 2257
struct EntryPointParams_0
{
    uint4 params_0;
};


#line 311
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_scratch_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(512)> threadgroup* stg_0;
};


#line 311
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 311
    uint _S10 = 2U * i_0;

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S10] = (as_type<uint>((v_0.x)));

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S10 + 1U] = (as_type<uint>((v_0.y)));

#line 311
    return;
}


#line 312
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 312
    uint _S11 = 2U * i_1;

#line 312
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S11]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S11 + 1U]))));
}


#line 748
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 755
    dft16_1(r_2);

#line 760
    return;
}


#line 876
uint lgOf_0(uint i_2)
{

#line 876
    uint _S12;

#line 876
    if(i_2 < 1U)
    {

#line 876
        _S12 = 4U;

#line 876
    }
    else
    {

#line 876
        if(i_2 == 1U)
        {

#line 876
            _S12 = 4U;

#line 876
        }
        else
        {

#line 876
            _S12 = 1U;

#line 876
        }

#line 876
    }

#line 876
    return _S12;
}


#line 878
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 882
    uint lg_1 = lgOf_0(0U);

#line 887
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 2257
[[kernel]] void tcFullSeriesStage3(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_scratch_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_output_1 [[buffer(3)]])
{

#line 2257
    uint j_1;

#line 2257
    uint d_2;

#line 2257
    thread KernelContext_0 kernelContext_2;

#line 2257
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2257
    (&kernelContext_2)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 2257
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2257
    (&kernelContext_2)->entryPointParams_output_0 = entryPointParams_output_1;

#line 2257
    threadgroup array<uint, int(512)> stg_1;

#line 2257
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2262
    uint _S13 = gid_0.x;

#line 2262
    uint pair_0 = _S13 / 512U;

#line 2262
    uint _S14 = _S13 % 512U;
    uint d_3 = pair_0 / entryPointParams_1->params_0.x;

#line 2263
    uint _S15 = pair_0 % entryPointParams_1->params_0.x;
    uint _S16 = (&kernelContext_2)->entryPointParams_starts_0[d_3];
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_3;

#line 2268
    uint m_1 = 0U;
    for(;;)
    {

#line 2269
        if(m_1 < 16U)
        {
        }
        else
        {

#line 2269
            break;
        }

#line 2270
        r_3[m_1] = float2(*((&kernelContext_2)->entryPointParams_scratch_0+(pair_0 * 131072U + _S14 * 256U + tid_0 + 16U * m_1))) ;

#line 2269
        m_1 = m_1 + 1U;

#line 2269
    }

    for(;;)
    {

#line 2271
        for(;;)
        {

#line 2271
            for(;;)
            {

#line 2271
                for(;;)
                {

#line 2271
                    uint lgTB_0 = firstbithigh_0(16U);

#line 2271
                    uint lgLn_0 = firstbithigh_0(256U);

#line 2271
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2271
                    uint lane_1 = tid_0 & 15U;

#line 2271
                    dft16_0(&r_3);

#line 2271
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 256.0f);

#line 2271
                    float _S17 = tw_0.x;

#line 2271
                    float _S18 = tw_0.y;

#line 2271
                    uint k2_2 = 0U;

#line 2271
                    float cr_0 = 1.0f;

#line 2271
                    float ci_0 = 0.0f;

#line 2271
                    for(;;)
                    {

#line 2271
                        if(k2_2 < 16U)
                        {
                        }
                        else
                        {

#line 2271
                            break;
                        }

#line 2271
                        r_3[k2_2] = cmul_0(r_3[k2_2], float2(cr_0, ci_0));

#line 2271
                        float nr_0 = cr_0 * _S17 - ci_0 * _S18;

#line 2271
                        float _S19 = cr_0 * _S18 + ci_0 * _S17;

#line 2271
                        k2_2 = k2_2 + 1U;

#line 2271
                        cr_0 = nr_0;

#line 2271
                        ci_0 = _S19;

#line 2271
                    }

#line 2271
                    uint per_1 = 16U / max(16U, 1U);

#line 2271
                    uint _S20 = max(1U, 1U);

#line 2271
                    uint blk2_1 = tid_0 / _S20;

#line 2271
                    uint lane2_1 = tid_0 % _S20;

#line 2271
                    for(;;)
                    {

#line 2271
                        thread array<float2, int(16)> out_0;

#line 2271
                        uint z_0 = 0U;

#line 2271
                        for(;;)
                        {

#line 2271
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2271
                                break;
                            }

#line 2271
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2271
                            z_0 = z_0 + 1U;

#line 2271
                        }

#line 2271
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2271
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2271
                        uint p0_0 = computeWant_0(0U, 16U, 256U, blk_1, lane_1, per_1, _S20, 16U, blk2_1, lane2_1);

#line 2271
                        uint _S21 = p0_0 & lenMask_0;

#line 2271
                        uint _S22 = (_S21 >> lgTB_0) * 16U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S21 & spanMask_0);

#line 2271
                        uint c_1 = 0U;

#line 2271
                        for(;;)
                        {

#line 2271
                            if(c_1 < 1U)
                            {
                            }
                            else
                            {

#line 2271
                                break;
                            }

#line 2271
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2271
                            j_1 = 0U;

#line 2271
                            for(;;)
                            {

#line 2271
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 2271
                                    break;
                                }

#line 2271
                                stgPut_0(j_1 * 16U + (&kernelContext_2)->_tid_0, r_3[c_1 * 16U + j_1], &kernelContext_2);

#line 2271
                                j_1 = j_1 + 1U;

#line 2271
                            }

#line 2271
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2271
                            d_2 = 0U;

#line 2271
                            for(;;)
                            {

#line 2271
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2271
                                    break;
                                }

#line 2271
                                uint pz_0 = computeWant_0(d_2, 16U, 256U, 0U, 0U, per_1, _S20, 16U, 0U, 0U);

#line 2271
                                uint _S23 = pz_0 & lenMask_0;

#line 2271
                                uint az_0 = (_S23 >> lgTB_0) * 16U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S23 & spanMask_0);

#line 2271
                                float2 _S24 = stgGet_0(_S22 + az_0 - c_1 * 16U * 16U, &kernelContext_2);

#line 2271
                                out_0[d_2] = _S24;

#line 2271
                                d_2 = d_2 + 1U;

#line 2271
                            }

#line 2271
                            c_1 = c_1 + 1U;

#line 2271
                        }

#line 2271
                        j_1 = 0U;

#line 2271
                        for(;;)
                        {

#line 2271
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2271
                                break;
                            }

#line 2271
                            r_3[j_1] = out_0[j_1];

#line 2271
                            j_1 = j_1 + 1U;

#line 2271
                        }

#line 2271
                        break;
                    }

#line 2271
                    break;
                }

#line 2271
                break;
            }

#line 2271
            break;
        }

#line 2271
        innermost_0(&r_3);

#line 2271
        break;
    }

#line 2271
    d_2 = 0U;
    for(;;)
    {

#line 2272
        if(d_2 < 16U)
        {
        }
        else
        {

#line 2272
            break;
        }

#line 2273
        uint lag_0 = slotToIndex_0(tid_0 * 16U + d_2) * 512U + _S14;

#line 2273
        bool _S25;
        if(lag_0 >= (entryPointParams_1->params_0.z))
        {

#line 2274
            _S25 = lag_0 < (entryPointParams_1->params_0.w);

#line 2274
        }
        else
        {

#line 2274
            _S25 = false;

#line 2274
        }

#line 2274
        bool _S26;

#line 2274
        if(_S25)
        {

#line 2274
            _S26 = lag_0 < (entryPointParams_1->params_0.y - _S16);

#line 2274
        }
        else
        {

#line 2274
            _S26 = false;

#line 2274
        }

#line 2274
        if(_S26)
        {

#line 2274
            *((&kernelContext_2)->entryPointParams_output_0+(_S15 * entryPointParams_1->params_0.y + _S16 + lag_0)) = packed_float2(float2(r_3[d_2].x, r_3[d_2].y)) ;

#line 2274
        }

#line 2272
        d_2 = d_2 + 1U;

#line 2272
    }

#line 2277
    return;
}
