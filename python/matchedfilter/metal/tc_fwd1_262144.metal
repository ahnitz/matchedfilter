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


#line 609 "tc_fwd1_262144.slang"
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


#line 103 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 324 "tc_fwd1_262144.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S7 = max(TB_0, 1U);

#line 326
    uint j_0 = d_1 / _S7;

#line 326
    uint m_0 = d_1 % _S7;

#line 326
    uint _S8;
    if(TB_0 <= 16U)
    {

#line 327
        _S8 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 327
    }
    else
    {

#line 327
        _S8 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 327
    }

#line 327
    return _S8;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint seriesLength_0;
};


#line 311 "tc_fwd1_262144.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_scratch_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 311
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 311
    uint _S9 = 2U * i_0;

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9] = (as_type<uint>((v_0.x)));

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9 + 1U] = (as_type<uint>((v_0.y)));

#line 311
    return;
}


#line 312
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 312
    uint _S10 = 2U * i_1;

#line 312
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10 + 1U]))));
}


#line 620
void dft2_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    float2 a_2 = (*r_1)[o_0];

#line 622
    float2 b_2 = (*r_1)[o_0 + 1U];

#line 622
    (*r_1)[o_0] = (*r_1)[o_0] + (*r_1)[o_0 + 1U];

#line 622
    (*r_1)[o_0 + 1U] = a_2 - b_2;
    return;
}


#line 748
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 748
    uint b_3 = 0U;

#line 758
    for(;;)
    {

#line 758
        if(b_3 < 8U)
        {
        }
        else
        {

#line 758
            break;
        }

#line 758
        dft2_0(r_2, b_3 * 2U);

#line 758
        b_3 = b_3 + 1U;

#line 758
    }

    return;
}


#line 876
uint lgOf_0(uint i_2)
{

#line 876
    uint _S11;

#line 876
    if(i_2 < 2U)
    {

#line 876
        _S11 = 4U;

#line 876
    }
    else
    {

#line 876
        _S11 = 1U;

#line 876
    }

#line 876
    return _S11;
}


#line 878
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 882
    uint lg_1 = lgOf_0(1U);

#line 882
    uint lg_2 = lgOf_0(0U);

#line 887
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2282
[[kernel]] void tcForwardStage1(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_scratch_1 [[buffer(3)]])
{

#line 2282
    uint _S12;

#line 2282
    uint k2_1;

#line 2282
    float cr_0;

#line 2282
    float ci_0;

#line 2282
    uint _S13;

#line 2282
    uint z_0;

#line 2282
    uint _S14;

#line 2282
    uint c_1;

#line 2282
    uint d_2;

#line 2282
    uint j_1;

#line 2282
    thread KernelContext_0 kernelContext_2;

#line 2282
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2282
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2282
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2282
    (&kernelContext_2)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 2282
    threadgroup array<uint, int(1024)> stg_1;

#line 2282
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2288
    uint _S15 = gid_0.x;

#line 2288
    uint block_0 = _S15 / 512U;

#line 2288
    uint _S16 = _S15 % 512U;
    uint tid_0 = lid_0.x;
    uint _S17 = entryPointParams_starts_1[block_0];
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_3;

#line 2293
    uint m_1 = 0U;
    for(;;)
    {

#line 2294
        if(m_1 < 16U)
        {
        }
        else
        {

#line 2294
            break;
        }

#line 2295
        uint j_2 = _S16 + 512U * (tid_0 + 32U * m_1);
        float2 _S18 = float2(0.0f, 0.0f);

#line 2296
        bool _S19;
        if(_S17 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2297
            _S19 = j_2 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S17);

#line 2297
        }
        else
        {

#line 2297
            _S19 = false;

#line 2297
        }

#line 2297
        float2 x_1;

#line 2297
        if(_S19)
        {

#line 2297
            x_1 = float2(*((&kernelContext_2)->entryPointParams_series_0+(_S17 + j_2))) ;

#line 2297
        }
        else
        {

#line 2297
            x_1 = _S18;

#line 2297
        }

        r_3[m_1] = float2(x_1.x / 2.62144e+05f, - x_1.y / 2.62144e+05f);

#line 2294
        m_1 = m_1 + 1U;

#line 2294
    }

#line 2301
    for(;;)
    {

#line 2301
        for(;;)
        {

#line 2301
            for(;;)
            {

#line 2301
                for(;;)
                {

#line 2301
                    uint lgTB_0 = firstbithigh_0(32U);

#line 2301
                    _S12 = lgTB_0;

#line 2301
                    uint lgLn_0 = firstbithigh_0(512U);

#line 2301
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2301
                    uint lane_1 = tid_0 & 31U;

#line 2301
                    dft16_0(&r_3);

#line 2301
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 512.0f);

#line 2301
                    float _S20 = tw_0.x;

#line 2301
                    float _S21 = tw_0.y;

#line 2301
                    k2_1 = 0U;

#line 2301
                    cr_0 = 1.0f;

#line 2301
                    ci_0 = 0.0f;

#line 2301
                    for(;;)
                    {

#line 2301
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2301
                            break;
                        }

#line 2301
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2301
                        float nr_0 = cr_0 * _S20 - ci_0 * _S21;

#line 2301
                        float _S22 = cr_0 * _S21 + ci_0 * _S20;

#line 2301
                        k2_1 = k2_1 + 1U;

#line 2301
                        cr_0 = nr_0;

#line 2301
                        ci_0 = _S22;

#line 2301
                    }

#line 2301
                    uint per_1 = 16U / max(32U, 1U);

#line 2301
                    uint _S23 = max(2U, 1U);

#line 2301
                    _S13 = _S23;

#line 2301
                    uint blk2_1 = tid_0 / _S23;

#line 2301
                    uint lane2_1 = tid_0 % _S23;

#line 2301
                    for(;;)
                    {

#line 2301
                        thread array<float2, int(16)> out_0;

#line 2301
                        z_0 = 0U;

#line 2301
                        for(;;)
                        {

#line 2301
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2301
                                break;
                            }

#line 2301
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2301
                            z_0 = z_0 + 1U;

#line 2301
                        }

#line 2301
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2301
                        _S14 = spanMask_0;

#line 2301
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2301
                        uint p0_0 = computeWant_0(0U, 32U, 512U, blk_1, lane_1, per_1, _S23, 32U, blk2_1, lane2_1);

#line 2301
                        uint _S24 = p0_0 & lenMask_0;

#line 2301
                        uint _S25 = (_S24 >> lgTB_0) * 32U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S24 & spanMask_0);

#line 2301
                        c_1 = 0U;

#line 2301
                        for(;;)
                        {

#line 2301
                            if(c_1 < 1U)
                            {
                            }
                            else
                            {

#line 2301
                                break;
                            }

#line 2301
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2301
                            j_1 = 0U;

#line 2301
                            for(;;)
                            {

#line 2301
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 2301
                                    break;
                                }

#line 2301
                                stgPut_0(j_1 * 32U + (&kernelContext_2)->_tid_0, r_3[c_1 * 16U + j_1], &kernelContext_2);

#line 2301
                                j_1 = j_1 + 1U;

#line 2301
                            }

#line 2301
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2301
                            d_2 = 0U;

#line 2301
                            for(;;)
                            {

#line 2301
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2301
                                    break;
                                }

#line 2301
                                uint pz_0 = computeWant_0(d_2, 32U, 512U, 0U, 0U, per_1, _S23, 32U, 0U, 0U);

#line 2301
                                uint _S26 = pz_0 & lenMask_0;

#line 2301
                                uint az_0 = (_S26 >> lgTB_0) * 32U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S26 & spanMask_0);

#line 2301
                                float2 _S27 = stgGet_0(_S25 + az_0 - c_1 * 16U * 32U, &kernelContext_2);

#line 2301
                                out_0[d_2] = _S27;

#line 2301
                                d_2 = d_2 + 1U;

#line 2301
                            }

#line 2301
                            c_1 = c_1 + 1U;

#line 2301
                        }

#line 2301
                        d_2 = 0U;

#line 2301
                        for(;;)
                        {

#line 2301
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2301
                                break;
                            }

#line 2301
                            r_3[d_2] = out_0[d_2];

#line 2301
                            d_2 = d_2 + 1U;

#line 2301
                        }

#line 2301
                        break;
                    }

#line 2301
                    break;
                }

#line 2301
                break;
            }

#line 2301
            for(;;)
            {

#line 2301
                for(;;)
                {

#line 2301
                    uint lgTB_1 = firstbithigh_0(2U);

#line 2301
                    uint blk_2 = tid_0 >> lgTB_1;

#line 2301
                    uint lane_2 = tid_0 & 1U;

#line 2301
                    dft16_0(&r_3);

#line 2301
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 32.0f);

#line 2301
                    float _S28 = tw_1.x;

#line 2301
                    float _S29 = tw_1.y;

#line 2301
                    k2_1 = 0U;

#line 2301
                    cr_0 = 1.0f;

#line 2301
                    ci_0 = 0.0f;

#line 2301
                    for(;;)
                    {

#line 2301
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2301
                            break;
                        }

#line 2301
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2301
                        float nr_1 = cr_0 * _S28 - ci_0 * _S29;

#line 2301
                        float _S30 = cr_0 * _S29 + ci_0 * _S28;

#line 2301
                        k2_1 = k2_1 + 1U;

#line 2301
                        cr_0 = nr_1;

#line 2301
                        ci_0 = _S30;

#line 2301
                    }

#line 2301
                    uint per_2 = 16U / _S13;

#line 2301
                    uint _S31 = max(0U, 1U);

#line 2301
                    uint blk2_2 = tid_0 / _S31;

#line 2301
                    uint lane2_2 = tid_0 % _S31;

#line 2301
                    for(;;)
                    {

#line 2301
                        thread array<float2, int(16)> out_1;

#line 2301
                        z_0 = 0U;

#line 2301
                        for(;;)
                        {

#line 2301
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2301
                                break;
                            }

#line 2301
                            out_1[z_0] = float2(0.0f, 0.0f);

#line 2301
                            z_0 = z_0 + 1U;

#line 2301
                        }

#line 2301
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2301
                        uint p0_1 = computeWant_0(0U, 2U, 32U, blk_2, lane_2, per_2, _S31, 2U, blk2_2, lane2_2);

#line 2301
                        uint _S32 = p0_1 & _S14;

#line 2301
                        uint _S33 = (_S32 >> lgTB_1) * 32U + ((p0_1 >> _S12) << lgTB_1) + (_S32 & spanMask_1);

#line 2301
                        c_1 = 0U;

#line 2301
                        for(;;)
                        {

#line 2301
                            if(c_1 < 1U)
                            {
                            }
                            else
                            {

#line 2301
                                break;
                            }

#line 2301
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2301
                            j_1 = 0U;

#line 2301
                            for(;;)
                            {

#line 2301
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 2301
                                    break;
                                }

#line 2301
                                stgPut_0(j_1 * 32U + (&kernelContext_2)->_tid_0, r_3[c_1 * 16U + j_1], &kernelContext_2);

#line 2301
                                j_1 = j_1 + 1U;

#line 2301
                            }

#line 2301
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2301
                            d_2 = 0U;

#line 2301
                            for(;;)
                            {

#line 2301
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2301
                                    break;
                                }

#line 2301
                                uint pz_1 = computeWant_0(d_2, 2U, 32U, 0U, 0U, per_2, _S31, 2U, 0U, 0U);

#line 2301
                                uint _S34 = pz_1 & _S14;

#line 2301
                                uint az_1 = (_S34 >> lgTB_1) * 32U + ((pz_1 >> _S12) << lgTB_1) + (_S34 & spanMask_1);

#line 2301
                                float2 _S35 = stgGet_0(_S33 + az_1 - c_1 * 16U * 32U, &kernelContext_2);

#line 2301
                                out_1[d_2] = _S35;

#line 2301
                                d_2 = d_2 + 1U;

#line 2301
                            }

#line 2301
                            c_1 = c_1 + 1U;

#line 2301
                        }

#line 2301
                        d_2 = 0U;

#line 2301
                        for(;;)
                        {

#line 2301
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2301
                                break;
                            }

#line 2301
                            r_3[d_2] = out_1[d_2];

#line 2301
                            d_2 = d_2 + 1U;

#line 2301
                        }

#line 2301
                        break;
                    }

#line 2301
                    break;
                }

#line 2301
                break;
            }

#line 2301
            break;
        }

#line 2301
        innermost_0(&r_3);

#line 2301
        break;
    }

#line 2301
    j_1 = 0U;
    for(;;)
    {

#line 2302
        if(j_1 < 16U)
        {
        }
        else
        {

#line 2302
            break;
        }

#line 2303
        uint k2_2 = slotToIndex_0(tid_0 * 16U + j_1);

#line 2303
        *((&kernelContext_2)->entryPointParams_scratch_0+(block_0 * 262144U + k2_2 * 512U + _S16)) = packed_float2(cmul_0(r_3[j_1], mfTwiddle_0(6.28318548202514648f * float(_S16 * k2_2) / 2.62144e+05f))) ;

#line 2302
        j_1 = j_1 + 1U;

#line 2302
    }

#line 2307
    return;
}
