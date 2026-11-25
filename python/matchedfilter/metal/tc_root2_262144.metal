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


#line 610 "tc_root2_262144.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 612
    float2 t1_0 = *a_0 - *c_0;

#line 612
    float2 t2_0 = *b_0 + *d_0;

#line 612
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 614
    *b_0 = t1_0 + j3_0;

#line 614
    *c_0 = t0_0 - t2_0;

#line 614
    *d_0 = t1_0 - j3_0;
    return;
}


#line 323
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 323
    float _S2 = a_1.x;

#line 323
    float _S3 = b_1.x;

#line 323
    float _S4 = a_1.y;

#line 323
    float _S5 = b_1.y;

#line 323
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 646
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 653
    uint n1_0 = 0U;
    for(;;)
    {

#line 654
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 654
            break;
        }

#line 654
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 654
        n1_0 = n1_0 + 1U;

#line 654
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 655
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 655
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 656
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 656
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 657
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 657
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 657
    uint k2_0 = 0U;
    for(;;)
    {

#line 658
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 658
            break;
        }

#line 658
        uint _S6 = 4U * k2_0;

#line 658
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 658
        k2_0 = k2_0 + 1U;

#line 658
    }

    float2 t_0 = (*r_0)[int(1)];

#line 660
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 660
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 661
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 661
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 662
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 662
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 663
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 663
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 664
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 664
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 665
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 665
    (*r_0)[int(14)] = t_5;
    return;
}


#line 103 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 325 "tc_root2_262144.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S7 = max(TB_0, 1U);

#line 327
    uint j_0 = d_1 / _S7;

#line 327
    uint m_0 = d_1 % _S7;

#line 327
    uint _S8;
    if(TB_0 <= 16U)
    {

#line 328
        _S8 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 328
    }
    else
    {

#line 328
        _S8 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 328
    }

#line 328
    return _S8;
}


#line 312
struct KernelContext_0
{
    packed_float2 device* entryPointParams_scratch_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 312
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 312
    uint _S9 = 2U * i_0;

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9] = (as_type<uint>((v_0.x)));

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9 + 1U] = (as_type<uint>((v_0.y)));

#line 312
    return;
}


#line 313
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 313
    uint _S10 = 2U * i_1;

#line 313
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10 + 1U]))));
}


#line 621
void dft2_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    float2 a_2 = (*r_1)[o_0];

#line 623
    float2 b_2 = (*r_1)[o_0 + 1U];

#line 623
    (*r_1)[o_0] = (*r_1)[o_0] + (*r_1)[o_0 + 1U];

#line 623
    (*r_1)[o_0 + 1U] = a_2 - b_2;
    return;
}


#line 749
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 749
    uint b_3 = 0U;

#line 759
    for(;;)
    {

#line 759
        if(b_3 < 8U)
        {
        }
        else
        {

#line 759
            break;
        }

#line 759
        dft2_0(r_2, b_3 * 2U);

#line 759
        b_3 = b_3 + 1U;

#line 759
    }

    return;
}


#line 877
uint lgOf_0(uint i_2)
{

#line 877
    uint _S11;

#line 877
    if(i_2 < 2U)
    {

#line 877
        _S11 = 4U;

#line 877
    }
    else
    {

#line 877
        _S11 = 1U;

#line 877
    }

#line 877
    return _S11;
}


#line 879
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 883
    uint lg_1 = lgOf_0(1U);

#line 883
    uint lg_2 = lgOf_0(0U);

#line 888
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2415
void rootStageOut_0(const array<float2, int(16)> thread* r_3, uint tid_0, uint col_0, uint p_0, KernelContext_0 thread* kernelContext_2)
{

#line 2415
    uint i_3 = 0U;

    for(;;)
    {

#line 2417
        if(i_3 < 16U)
        {
        }
        else
        {

#line 2417
            break;
        }

#line 2418
        uint row_0 = slotToIndex_0(tid_0 * 16U + i_3);
        if((row_0 / 256U) == p_0)
        {

#line 2420
            uint a_3 = row_0 % 256U * 9U + col_0;

#line 2420
            float2 _S12 = (*r_3)[i_3];
            (*kernelContext_2->stg_0)[a_3] = (as_type<uint>(((*r_3)[i_3].x)));
            (*kernelContext_2->stg_0)[a_3 + 2304U] = (as_type<uint>((_S12.y)));

#line 2419
        }

#line 2417
        i_3 = i_3 + 1U;

#line 2417
    }

#line 2425
    return;
}


#line 2510
[[kernel]] void tcRootStage2(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], packed_float2 device* entryPointParams_scratch_1 [[buffer(0)]], packed_float2 device* entryPointParams_output_1 [[buffer(1)]])
{

#line 2510
    uint _S13;

#line 2510
    uint k2_1;

#line 2510
    float cr_0;

#line 2510
    float ci_0;

#line 2510
    uint _S14;

#line 2510
    uint z_0;

#line 2510
    uint _S15;

#line 2510
    uint c_1;

#line 2510
    uint d_2;

#line 2510
    uint j_1;

#line 2510
    thread KernelContext_0 kernelContext_3;

#line 2510
    (&kernelContext_3)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 2510
    (&kernelContext_3)->entryPointParams_output_0 = entryPointParams_output_1;

#line 2510
    threadgroup array<uint, int(8192)> stg_1;

#line 2510
    (&kernelContext_3)->stg_0 = &stg_1;


    uint _S16 = 8U * gid_0.x;
    uint l_0 = lid_0.x;

#line 2514
    uint col_1 = l_0 / 32U;

#line 2514
    uint tid_1 = l_0 % 32U;
    (&kernelContext_3)->_tid_0 = tid_1;
    (&kernelContext_3)->_stgBase_0 = col_1 * 1024U;
    thread array<float2, int(16)> r_4;

#line 2517
    uint m_1 = 0U;
    for(;;)
    {

#line 2518
        if(m_1 < 16U)
        {
        }
        else
        {

#line 2518
            break;
        }

#line 2519
        r_4[m_1] = float2(*((&kernelContext_3)->entryPointParams_scratch_0+((_S16 + col_1) * 512U + tid_1 + 32U * m_1))) ;

#line 2518
        m_1 = m_1 + 1U;

#line 2518
    }

    for(;;)
    {

#line 2520
        for(;;)
        {

#line 2520
            for(;;)
            {

#line 2520
                for(;;)
                {

#line 2520
                    uint lgTB_0 = firstbithigh_0(32U);

#line 2520
                    _S13 = lgTB_0;

#line 2520
                    uint lgLn_0 = firstbithigh_0(512U);

#line 2520
                    uint blk_1 = tid_1 >> lgTB_0;

#line 2520
                    uint lane_1 = tid_1 & 31U;

#line 2520
                    dft16_0(&r_4);

#line 2520
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 512.0f);

#line 2520
                    float _S17 = tw_0.x;

#line 2520
                    float _S18 = tw_0.y;

#line 2520
                    k2_1 = 0U;

#line 2520
                    cr_0 = 1.0f;

#line 2520
                    ci_0 = 0.0f;

#line 2520
                    for(;;)
                    {

#line 2520
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2520
                            break;
                        }

#line 2520
                        r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 2520
                        float nr_0 = cr_0 * _S17 - ci_0 * _S18;

#line 2520
                        float _S19 = cr_0 * _S18 + ci_0 * _S17;

#line 2520
                        k2_1 = k2_1 + 1U;

#line 2520
                        cr_0 = nr_0;

#line 2520
                        ci_0 = _S19;

#line 2520
                    }

#line 2520
                    uint per_1 = 16U / max(32U, 1U);

#line 2520
                    uint _S20 = max(2U, 1U);

#line 2520
                    _S14 = _S20;

#line 2520
                    uint blk2_1 = tid_1 / _S20;

#line 2520
                    uint lane2_1 = tid_1 % _S20;

#line 2520
                    for(;;)
                    {

#line 2520
                        thread array<float2, int(16)> out_0;

#line 2520
                        z_0 = 0U;

#line 2520
                        for(;;)
                        {

#line 2520
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2520
                                break;
                            }

#line 2520
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2520
                            z_0 = z_0 + 1U;

#line 2520
                        }

#line 2520
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2520
                        _S15 = spanMask_0;

#line 2520
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2520
                        uint p0_0 = computeWant_0(0U, 32U, 512U, blk_1, lane_1, per_1, _S20, 32U, blk2_1, lane2_1);

#line 2520
                        uint _S21 = p0_0 & lenMask_0;

#line 2520
                        uint _S22 = (_S21 >> lgTB_0) * 32U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S21 & spanMask_0);

#line 2520
                        c_1 = 0U;

#line 2520
                        for(;;)
                        {

#line 2520
                            if(c_1 < 1U)
                            {
                            }
                            else
                            {

#line 2520
                                break;
                            }

#line 2520
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2520
                            j_1 = 0U;

#line 2520
                            for(;;)
                            {

#line 2520
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 2520
                                    break;
                                }

#line 2520
                                stgPut_0(j_1 * 32U + (&kernelContext_3)->_tid_0, r_4[c_1 * 16U + j_1], &kernelContext_3);

#line 2520
                                j_1 = j_1 + 1U;

#line 2520
                            }

#line 2520
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2520
                            d_2 = 0U;

#line 2520
                            for(;;)
                            {

#line 2520
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2520
                                    break;
                                }

#line 2520
                                uint pz_0 = computeWant_0(d_2, 32U, 512U, 0U, 0U, per_1, _S20, 32U, 0U, 0U);

#line 2520
                                uint _S23 = pz_0 & lenMask_0;

#line 2520
                                uint az_0 = (_S23 >> lgTB_0) * 32U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S23 & spanMask_0);

#line 2520
                                float2 _S24 = stgGet_0(_S22 + az_0 - c_1 * 16U * 32U, &kernelContext_3);

#line 2520
                                out_0[d_2] = _S24;

#line 2520
                                d_2 = d_2 + 1U;

#line 2520
                            }

#line 2520
                            c_1 = c_1 + 1U;

#line 2520
                        }

#line 2520
                        d_2 = 0U;

#line 2520
                        for(;;)
                        {

#line 2520
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2520
                                break;
                            }

#line 2520
                            r_4[d_2] = out_0[d_2];

#line 2520
                            d_2 = d_2 + 1U;

#line 2520
                        }

#line 2520
                        break;
                    }

#line 2520
                    break;
                }

#line 2520
                break;
            }

#line 2520
            for(;;)
            {

#line 2520
                for(;;)
                {

#line 2520
                    uint lgTB_1 = firstbithigh_0(2U);

#line 2520
                    uint blk_2 = tid_1 >> lgTB_1;

#line 2520
                    uint lane_2 = tid_1 & 1U;

#line 2520
                    dft16_0(&r_4);

#line 2520
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 32.0f);

#line 2520
                    float _S25 = tw_1.x;

#line 2520
                    float _S26 = tw_1.y;

#line 2520
                    k2_1 = 0U;

#line 2520
                    cr_0 = 1.0f;

#line 2520
                    ci_0 = 0.0f;

#line 2520
                    for(;;)
                    {

#line 2520
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2520
                            break;
                        }

#line 2520
                        r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 2520
                        float nr_1 = cr_0 * _S25 - ci_0 * _S26;

#line 2520
                        float _S27 = cr_0 * _S26 + ci_0 * _S25;

#line 2520
                        k2_1 = k2_1 + 1U;

#line 2520
                        cr_0 = nr_1;

#line 2520
                        ci_0 = _S27;

#line 2520
                    }

#line 2520
                    uint per_2 = 16U / _S14;

#line 2520
                    uint _S28 = max(0U, 1U);

#line 2520
                    uint blk2_2 = tid_1 / _S28;

#line 2520
                    uint lane2_2 = tid_1 % _S28;

#line 2520
                    for(;;)
                    {

#line 2520
                        thread array<float2, int(16)> out_1;

#line 2520
                        z_0 = 0U;

#line 2520
                        for(;;)
                        {

#line 2520
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2520
                                break;
                            }

#line 2520
                            out_1[z_0] = float2(0.0f, 0.0f);

#line 2520
                            z_0 = z_0 + 1U;

#line 2520
                        }

#line 2520
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2520
                        uint p0_1 = computeWant_0(0U, 2U, 32U, blk_2, lane_2, per_2, _S28, 2U, blk2_2, lane2_2);

#line 2520
                        uint _S29 = p0_1 & _S15;

#line 2520
                        uint _S30 = (_S29 >> lgTB_1) * 32U + ((p0_1 >> _S13) << lgTB_1) + (_S29 & spanMask_1);

#line 2520
                        c_1 = 0U;

#line 2520
                        for(;;)
                        {

#line 2520
                            if(c_1 < 1U)
                            {
                            }
                            else
                            {

#line 2520
                                break;
                            }

#line 2520
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2520
                            j_1 = 0U;

#line 2520
                            for(;;)
                            {

#line 2520
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 2520
                                    break;
                                }

#line 2520
                                stgPut_0(j_1 * 32U + (&kernelContext_3)->_tid_0, r_4[c_1 * 16U + j_1], &kernelContext_3);

#line 2520
                                j_1 = j_1 + 1U;

#line 2520
                            }

#line 2520
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2520
                            d_2 = 0U;

#line 2520
                            for(;;)
                            {

#line 2520
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2520
                                    break;
                                }

#line 2520
                                uint pz_1 = computeWant_0(d_2, 2U, 32U, 0U, 0U, per_2, _S28, 2U, 0U, 0U);

#line 2520
                                uint _S31 = pz_1 & _S15;

#line 2520
                                uint az_1 = (_S31 >> lgTB_1) * 32U + ((pz_1 >> _S13) << lgTB_1) + (_S31 & spanMask_1);

#line 2520
                                float2 _S32 = stgGet_0(_S30 + az_1 - c_1 * 16U * 32U, &kernelContext_3);

#line 2520
                                out_1[d_2] = _S32;

#line 2520
                                d_2 = d_2 + 1U;

#line 2520
                            }

#line 2520
                            c_1 = c_1 + 1U;

#line 2520
                        }

#line 2520
                        d_2 = 0U;

#line 2520
                        for(;;)
                        {

#line 2520
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2520
                                break;
                            }

#line 2520
                            r_4[d_2] = out_1[d_2];

#line 2520
                            d_2 = d_2 + 1U;

#line 2520
                        }

#line 2520
                        break;
                    }

#line 2520
                    break;
                }

#line 2520
                break;
            }

#line 2520
            break;
        }

#line 2520
        innermost_0(&r_4);

#line 2520
        break;
    }

#line 2520
    j_1 = 0U;
    for(;;)
    {

#line 2521
        if(j_1 < 2U)
        {
        }
        else
        {

#line 2521
            break;
        }

#line 2522
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2522
        thread array<float2, int(16)> _S33 = r_4;

#line 2522
        rootStageOut_0(&_S33, tid_1, col_1, j_1, &kernelContext_3);

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2524
        uint s_0 = 0U;
        for(;;)
        {

#line 2525
            if(s_0 < 8U)
            {
            }
            else
            {

#line 2525
                break;
            }

#line 2526
            uint e_0 = l_0 + 256U * s_0;
            uint rr_0 = e_0 / 8U;

#line 2527
            uint c_2 = e_0 % 8U;
            uint a_4 = rr_0 * 9U + c_2;

#line 2528
            *((&kernelContext_3)->entryPointParams_output_0+((j_1 * 256U + rr_0) * 512U + _S16 + c_2)) = packed_float2(float2((as_type<float>(((*(&kernelContext_3)->stg_0)[a_4]))), (as_type<float>(((*(&kernelContext_3)->stg_0)[a_4 + 2304U]))))) ;

#line 2525
            s_0 = s_0 + 1U;

#line 2525
        }

#line 2521
        j_1 = j_1 + 1U;

#line 2521
    }

#line 2533
    return;
}
