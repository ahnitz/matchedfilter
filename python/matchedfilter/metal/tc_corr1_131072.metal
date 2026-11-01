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


#line 323 "tc_corr1_131072.slang"
float2 cmulConj_0(float2 a_0, float2 b_0)
{

#line 323
    float _S2 = a_0.x;

#line 323
    float _S3 = b_0.x;

#line 323
    float _S4 = a_0.y;

#line 323
    float _S5 = b_0.y;

#line 323
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 607
void r4_0(float2 thread* a_1, float2 thread* b_1, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 609
    float2 t1_0 = *a_1 - *c_0;

#line 609
    float2 t2_0 = *b_1 + *d_0;

#line 609
    float2 t3_0 = *b_1 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 611
    *b_1 = t1_0 + j3_0;

#line 611
    *c_0 = t0_0 - t2_0;

#line 611
    *d_0 = t1_0 - j3_0;
    return;
}


#line 322
float2 cmul_0(float2 a_2, float2 b_2)
{

#line 322
    float _S6 = a_2.x;

#line 322
    float _S7 = b_2.x;

#line 322
    float _S8 = a_2.y;

#line 322
    float _S9 = b_2.y;

#line 322
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 643
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 650
    uint n1_0 = 0U;
    for(;;)
    {

#line 651
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 651
            break;
        }

#line 651
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 651
        n1_0 = n1_0 + 1U;

#line 651
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 652
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 652
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 653
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 653
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 654
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 654
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 654
    uint k2_0 = 0U;
    for(;;)
    {

#line 655
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 655
            break;
        }

#line 655
        uint _S10 = 4U * k2_0;

#line 655
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 655
        k2_0 = k2_0 + 1U;

#line 655
    }

    float2 t_0 = (*r_0)[int(1)];

#line 657
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 657
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 658
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 658
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 659
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 659
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 660
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 660
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 661
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 661
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 662
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 662
    (*r_0)[int(14)] = t_5;
    return;
}


#line 103 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 324 "tc_corr1_131072.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 326
    uint j_0 = d_1 / _S11;

#line 326
    uint m_0 = d_1 % _S11;

#line 326
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 327
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 327
    }
    else
    {

#line 327
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 327
    }

#line 327
    return _S12;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint ntmpl_0;
};


#line 311 "tc_corr1_131072.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    packed_float2 device* entryPointParams_scratch_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 311
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 311
    uint _S13 = 2U * i_0;

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13] = (as_type<uint>((v_0.x)));

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13 + 1U] = (as_type<uint>((v_0.y)));

#line 311
    return;
}


#line 312
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 312
    uint _S14 = 2U * i_1;

#line 312
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 618
void dft2_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    float2 a_3 = (*r_1)[o_0];

#line 620
    float2 b_3 = (*r_1)[o_0 + 1U];

#line 620
    (*r_1)[o_0] = (*r_1)[o_0] + (*r_1)[o_0 + 1U];

#line 620
    (*r_1)[o_0 + 1U] = a_3 - b_3;
    return;
}


#line 746
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 746
    uint b_4 = 0U;

#line 756
    for(;;)
    {

#line 756
        if(b_4 < 8U)
        {
        }
        else
        {

#line 756
            break;
        }

#line 756
        dft2_0(r_2, b_4 * 2U);

#line 756
        b_4 = b_4 + 1U;

#line 756
    }

    return;
}


#line 874
uint lgOf_0(uint i_2)
{

#line 874
    uint _S15;

#line 874
    if(i_2 < 2U)
    {

#line 874
        _S15 = 4U;

#line 874
    }
    else
    {

#line 874
        _S15 = 1U;

#line 874
    }

#line 874
    return _S15;
}


#line 876
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 880
    uint lg_1 = lgOf_0(1U);

#line 880
    uint lg_2 = lgOf_0(0U);

#line 885
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2086
[[kernel]] void tcStage1(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], packed_float2 device* entryPointParams_scratch_1 [[buffer(3)]])
{

#line 2086
    uint _S16;

#line 2086
    uint k2_1;

#line 2086
    float cr_0;

#line 2086
    float ci_0;

#line 2086
    uint _S17;

#line 2086
    uint z_0;

#line 2086
    uint _S18;

#line 2086
    uint c_1;

#line 2086
    uint d_2;

#line 2086
    uint j_1;

#line 2086
    thread KernelContext_0 kernelContext_2;

#line 2086
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2086
    (&kernelContext_2)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2086
    (&kernelContext_2)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2086
    (&kernelContext_2)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 2086
    threadgroup array<uint, int(1024)> stg_1;

#line 2086
    (&kernelContext_2)->stg_0 = &stg_1;



    uint _S19 = gid_0.x;

#line 2090
    uint pair_0 = _S19 / 256U;

#line 2090
    uint _S20 = _S19 % 256U;
    uint _S21 = pair_0 / entryPointParams_1->ntmpl_0;

#line 2091
    uint _S22 = pair_0 % entryPointParams_1->ntmpl_0;
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;

    thread array<float2, int(16)> r_3;

#line 2096
    uint m_1 = 0U;
    for(;;)
    {

#line 2097
        if(m_1 < 16U)
        {
        }
        else
        {

#line 2097
            break;
        }

#line 2098
        uint j_2 = _S20 + 256U * (tid_0 + 32U * m_1);
        r_3[m_1] = cmulConj_0(float2(*((&kernelContext_2)->entryPointParams_data_0+(_S21 * 131072U + j_2))) , float2(*((&kernelContext_2)->entryPointParams_tmpl_0+(_S22 * 131072U + j_2))) );

#line 2097
        m_1 = m_1 + 1U;

#line 2097
    }



    for(;;)
    {

#line 2101
        for(;;)
        {

#line 2101
            for(;;)
            {

#line 2101
                for(;;)
                {

#line 2101
                    uint lgTB_0 = firstbithigh_0(32U);

#line 2101
                    _S16 = lgTB_0;

#line 2101
                    uint lgLn_0 = firstbithigh_0(512U);

#line 2101
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2101
                    uint lane_1 = tid_0 & 31U;

#line 2101
                    dft16_0(&r_3);

#line 2101
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 512.0f);

#line 2101
                    float _S23 = tw_0.x;

#line 2101
                    float _S24 = tw_0.y;

#line 2101
                    k2_1 = 0U;

#line 2101
                    cr_0 = 1.0f;

#line 2101
                    ci_0 = 0.0f;

#line 2101
                    for(;;)
                    {

#line 2101
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2101
                            break;
                        }

#line 2101
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2101
                        float nr_0 = cr_0 * _S23 - ci_0 * _S24;

#line 2101
                        float _S25 = cr_0 * _S24 + ci_0 * _S23;

#line 2101
                        k2_1 = k2_1 + 1U;

#line 2101
                        cr_0 = nr_0;

#line 2101
                        ci_0 = _S25;

#line 2101
                    }

#line 2101
                    uint per_1 = 16U / max(32U, 1U);

#line 2101
                    uint _S26 = max(2U, 1U);

#line 2101
                    _S17 = _S26;

#line 2101
                    uint blk2_1 = tid_0 / _S26;

#line 2101
                    uint lane2_1 = tid_0 % _S26;

#line 2101
                    for(;;)
                    {

#line 2101
                        thread array<float2, int(16)> out_0;

#line 2101
                        z_0 = 0U;

#line 2101
                        for(;;)
                        {

#line 2101
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2101
                                break;
                            }

#line 2101
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2101
                            z_0 = z_0 + 1U;

#line 2101
                        }

#line 2101
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2101
                        _S18 = spanMask_0;

#line 2101
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2101
                        uint p0_0 = computeWant_0(0U, 32U, 512U, blk_1, lane_1, per_1, _S26, 32U, blk2_1, lane2_1);

#line 2101
                        uint _S27 = p0_0 & lenMask_0;

#line 2101
                        uint _S28 = (_S27 >> lgTB_0) * 32U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S27 & spanMask_0);

#line 2101
                        c_1 = 0U;

#line 2101
                        for(;;)
                        {

#line 2101
                            if(c_1 < 1U)
                            {
                            }
                            else
                            {

#line 2101
                                break;
                            }

#line 2101
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2101
                            j_1 = 0U;

#line 2101
                            for(;;)
                            {

#line 2101
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 2101
                                    break;
                                }

#line 2101
                                stgPut_0(j_1 * 32U + (&kernelContext_2)->_tid_0, r_3[c_1 * 16U + j_1], &kernelContext_2);

#line 2101
                                j_1 = j_1 + 1U;

#line 2101
                            }

#line 2101
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2101
                            d_2 = 0U;

#line 2101
                            for(;;)
                            {

#line 2101
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2101
                                    break;
                                }

#line 2101
                                uint pz_0 = computeWant_0(d_2, 32U, 512U, 0U, 0U, per_1, _S26, 32U, 0U, 0U);

#line 2101
                                uint _S29 = pz_0 & lenMask_0;

#line 2101
                                uint az_0 = (_S29 >> lgTB_0) * 32U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S29 & spanMask_0);

#line 2101
                                float2 _S30 = stgGet_0(_S28 + az_0 - c_1 * 16U * 32U, &kernelContext_2);

#line 2101
                                out_0[d_2] = _S30;

#line 2101
                                d_2 = d_2 + 1U;

#line 2101
                            }

#line 2101
                            c_1 = c_1 + 1U;

#line 2101
                        }

#line 2101
                        d_2 = 0U;

#line 2101
                        for(;;)
                        {

#line 2101
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2101
                                break;
                            }

#line 2101
                            r_3[d_2] = out_0[d_2];

#line 2101
                            d_2 = d_2 + 1U;

#line 2101
                        }

#line 2101
                        break;
                    }

#line 2101
                    break;
                }

#line 2101
                break;
            }

#line 2101
            for(;;)
            {

#line 2101
                for(;;)
                {

#line 2101
                    uint lgTB_1 = firstbithigh_0(2U);

#line 2101
                    uint blk_2 = tid_0 >> lgTB_1;

#line 2101
                    uint lane_2 = tid_0 & 1U;

#line 2101
                    dft16_0(&r_3);

#line 2101
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 32.0f);

#line 2101
                    float _S31 = tw_1.x;

#line 2101
                    float _S32 = tw_1.y;

#line 2101
                    k2_1 = 0U;

#line 2101
                    cr_0 = 1.0f;

#line 2101
                    ci_0 = 0.0f;

#line 2101
                    for(;;)
                    {

#line 2101
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2101
                            break;
                        }

#line 2101
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2101
                        float nr_1 = cr_0 * _S31 - ci_0 * _S32;

#line 2101
                        float _S33 = cr_0 * _S32 + ci_0 * _S31;

#line 2101
                        k2_1 = k2_1 + 1U;

#line 2101
                        cr_0 = nr_1;

#line 2101
                        ci_0 = _S33;

#line 2101
                    }

#line 2101
                    uint per_2 = 16U / _S17;

#line 2101
                    uint _S34 = max(0U, 1U);

#line 2101
                    uint blk2_2 = tid_0 / _S34;

#line 2101
                    uint lane2_2 = tid_0 % _S34;

#line 2101
                    for(;;)
                    {

#line 2101
                        thread array<float2, int(16)> out_1;

#line 2101
                        z_0 = 0U;

#line 2101
                        for(;;)
                        {

#line 2101
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2101
                                break;
                            }

#line 2101
                            out_1[z_0] = float2(0.0f, 0.0f);

#line 2101
                            z_0 = z_0 + 1U;

#line 2101
                        }

#line 2101
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2101
                        uint p0_1 = computeWant_0(0U, 2U, 32U, blk_2, lane_2, per_2, _S34, 2U, blk2_2, lane2_2);

#line 2101
                        uint _S35 = p0_1 & _S18;

#line 2101
                        uint _S36 = (_S35 >> lgTB_1) * 32U + ((p0_1 >> _S16) << lgTB_1) + (_S35 & spanMask_1);

#line 2101
                        c_1 = 0U;

#line 2101
                        for(;;)
                        {

#line 2101
                            if(c_1 < 1U)
                            {
                            }
                            else
                            {

#line 2101
                                break;
                            }

#line 2101
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2101
                            j_1 = 0U;

#line 2101
                            for(;;)
                            {

#line 2101
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 2101
                                    break;
                                }

#line 2101
                                stgPut_0(j_1 * 32U + (&kernelContext_2)->_tid_0, r_3[c_1 * 16U + j_1], &kernelContext_2);

#line 2101
                                j_1 = j_1 + 1U;

#line 2101
                            }

#line 2101
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2101
                            d_2 = 0U;

#line 2101
                            for(;;)
                            {

#line 2101
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2101
                                    break;
                                }

#line 2101
                                uint pz_1 = computeWant_0(d_2, 2U, 32U, 0U, 0U, per_2, _S34, 2U, 0U, 0U);

#line 2101
                                uint _S37 = pz_1 & _S18;

#line 2101
                                uint az_1 = (_S37 >> lgTB_1) * 32U + ((pz_1 >> _S16) << lgTB_1) + (_S37 & spanMask_1);

#line 2101
                                float2 _S38 = stgGet_0(_S36 + az_1 - c_1 * 16U * 32U, &kernelContext_2);

#line 2101
                                out_1[d_2] = _S38;

#line 2101
                                d_2 = d_2 + 1U;

#line 2101
                            }

#line 2101
                            c_1 = c_1 + 1U;

#line 2101
                        }

#line 2101
                        d_2 = 0U;

#line 2101
                        for(;;)
                        {

#line 2101
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2101
                                break;
                            }

#line 2101
                            r_3[d_2] = out_1[d_2];

#line 2101
                            d_2 = d_2 + 1U;

#line 2101
                        }

#line 2101
                        break;
                    }

#line 2101
                    break;
                }

#line 2101
                break;
            }

#line 2101
            break;
        }

#line 2101
        innermost_0(&r_3);

#line 2101
        break;
    }

#line 2101
    j_1 = 0U;

#line 2106
    for(;;)
    {

#line 2106
        if(j_1 < 16U)
        {
        }
        else
        {

#line 2106
            break;
        }

#line 2107
        uint k2_2 = slotToIndex_0(tid_0 * 16U + j_1);

#line 2107
        *((&kernelContext_2)->entryPointParams_scratch_0+(pair_0 * 131072U + k2_2 * 256U + _S20)) = packed_float2(cmul_0(r_3[j_1], mfTwiddle_0(6.28318548202514648f * float(_S20 * k2_2) / 1.31072e+05f))) ;

#line 2106
        j_1 = j_1 + 1U;

#line 2106
    }

#line 2111
    return;
}
