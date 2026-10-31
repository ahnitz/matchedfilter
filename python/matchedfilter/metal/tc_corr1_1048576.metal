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


#line 317 "tc_corr1_1048576.slang"
float2 cmulConj_0(float2 a_0, float2 b_0)
{

#line 317
    float _S2 = a_0.x;

#line 317
    float _S3 = b_0.x;

#line 317
    float _S4 = a_0.y;

#line 317
    float _S5 = b_0.y;

#line 317
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 576
void r4_0(float2 thread* a_1, float2 thread* b_1, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 578
    float2 t1_0 = *a_1 - *c_0;

#line 578
    float2 t2_0 = *b_1 + *d_0;

#line 578
    float2 t3_0 = *b_1 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 580
    *b_1 = t1_0 + j3_0;

#line 580
    *c_0 = t0_0 - t2_0;

#line 580
    *d_0 = t1_0 - j3_0;
    return;
}


#line 316
float2 cmul_0(float2 a_2, float2 b_2)
{

#line 316
    float _S6 = a_2.x;

#line 316
    float _S7 = b_2.x;

#line 316
    float _S8 = a_2.y;

#line 316
    float _S9 = b_2.y;

#line 316
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 612
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 619
    uint n1_0 = 0U;
    for(;;)
    {

#line 620
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 620
            break;
        }

#line 620
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 620
        n1_0 = n1_0 + 1U;

#line 620
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 621
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 621
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 622
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 622
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 623
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 623
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 623
    uint k2_0 = 0U;
    for(;;)
    {

#line 624
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 624
            break;
        }

#line 624
        uint _S10 = 4U * k2_0;

#line 624
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 624
        k2_0 = k2_0 + 1U;

#line 624
    }

    float2 t_0 = (*r_0)[int(1)];

#line 626
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 626
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 627
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 627
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 628
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 628
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 629
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 629
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 630
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 630
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 631
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 631
    (*r_0)[int(14)] = t_5;
    return;
}


#line 101 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 318 "tc_corr1_1048576.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 320
    uint j_0 = d_1 / _S11;

#line 320
    uint m_0 = d_1 % _S11;

#line 320
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 321
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 321
    }
    else
    {

#line 321
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 321
    }

#line 321
    return _S12;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint ntmpl_0;
};


#line 305 "tc_corr1_1048576.slang"
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


#line 305
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 305
    uint _S13 = 2U * i_0;

#line 305
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13] = (as_type<uint>((v_0.x)));

#line 305
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13 + 1U] = (as_type<uint>((v_0.y)));

#line 305
    return;
}


#line 306
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 306
    uint _S14 = 2U * i_1;

#line 306
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 591
void dft4_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    r4_0(&(*r_1)[o_0], &(*r_1)[o_0 + 1U], &(*r_1)[o_0 + 2U], &(*r_1)[o_0 + 3U]);
    float2 t_6 = (*r_1)[o_0 + 1U];

#line 594
    (*r_1)[o_0 + 1U] = (*r_1)[o_0 + 2U];

#line 594
    (*r_1)[o_0 + 2U] = t_6;
    return;
}


#line 715
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 715
    uint b_3 = 0U;

#line 724
    for(;;)
    {

#line 724
        if(b_3 < 4U)
        {
        }
        else
        {

#line 724
            break;
        }

#line 724
        dft4_0(r_2, b_3 * 4U);

#line 724
        b_3 = b_3 + 1U;

#line 724
    }


    return;
}


#line 862
uint lgOf_0(uint i_2)
{

#line 862
    uint _S15;

#line 862
    if(i_2 < 2U)
    {

#line 862
        _S15 = 4U;

#line 862
    }
    else
    {

#line 862
        _S15 = 1U;

#line 862
    }

#line 862
    return _S15;
}


#line 864
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 868
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 868
    uint lg_2 = lgOf_0(1U);

#line 868
    uint lg_3 = lgOf_0(0U);

#line 873
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 1987
[[kernel]] void tcStage1(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], packed_float2 device* entryPointParams_scratch_1 [[buffer(3)]])
{

#line 1987
    uint _S16;

#line 1987
    uint k2_1;

#line 1987
    float cr_0;

#line 1987
    float ci_0;

#line 1987
    uint _S17;

#line 1987
    uint z_0;

#line 1987
    uint _S18;

#line 1987
    uint c_1;

#line 1987
    uint d_2;

#line 1987
    uint j_1;

#line 1987
    bool _S19;

#line 1987
    thread KernelContext_0 kernelContext_2;

#line 1987
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 1987
    (&kernelContext_2)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1987
    (&kernelContext_2)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1987
    (&kernelContext_2)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 1987
    threadgroup array<uint, int(1024)> stg_1;

#line 1987
    (&kernelContext_2)->stg_0 = &stg_1;



    uint _S20 = gid_0.x;

#line 1991
    uint pair_0 = _S20 / 1024U;

#line 1991
    uint _S21 = _S20 % 1024U;
    uint _S22 = pair_0 / entryPointParams_1->ntmpl_0;

#line 1992
    uint _S23 = pair_0 % entryPointParams_1->ntmpl_0;
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;

    thread array<float2, int(16)> r_3;

#line 1997
    uint m_1 = 0U;
    for(;;)
    {

#line 1998
        if(m_1 < 16U)
        {
        }
        else
        {

#line 1998
            break;
        }

#line 1999
        uint j_2 = _S21 + 1024U * (tid_0 + 64U * m_1);
        r_3[m_1] = cmulConj_0(float2(*((&kernelContext_2)->entryPointParams_data_0+(_S22 * 1048576U + j_2))) , float2(*((&kernelContext_2)->entryPointParams_tmpl_0+(_S23 * 1048576U + j_2))) );

#line 1998
        m_1 = m_1 + 1U;

#line 1998
    }



    for(;;)
    {

#line 2002
        for(;;)
        {

#line 2002
            for(;;)
            {

#line 2002
                for(;;)
                {

#line 2002
                    uint lgTB_0 = firstbithigh_0(64U);

#line 2002
                    _S16 = lgTB_0;

#line 2002
                    uint lgLn_0 = firstbithigh_0(1024U);

#line 2002
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2002
                    uint lane_1 = tid_0 & 63U;

#line 2002
                    dft16_0(&r_3);

#line 2002
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 1024.0f);

#line 2002
                    float _S24 = tw_0.x;

#line 2002
                    float _S25 = tw_0.y;

#line 2002
                    k2_1 = 0U;

#line 2002
                    cr_0 = 1.0f;

#line 2002
                    ci_0 = 0.0f;

#line 2002
                    for(;;)
                    {

#line 2002
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2002
                            break;
                        }

#line 2002
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2002
                        float nr_0 = cr_0 * _S24 - ci_0 * _S25;

#line 2002
                        float _S26 = cr_0 * _S25 + ci_0 * _S24;

#line 2002
                        k2_1 = k2_1 + 1U;

#line 2002
                        cr_0 = nr_0;

#line 2002
                        ci_0 = _S26;

#line 2002
                    }

#line 2002
                    uint per_1 = 16U / max(64U, 1U);

#line 2002
                    uint _S27 = max(4U, 1U);

#line 2002
                    _S17 = _S27;

#line 2002
                    uint blk2_1 = tid_0 / _S27;

#line 2002
                    uint lane2_1 = tid_0 % _S27;

#line 2002
                    for(;;)
                    {

#line 2002
                        thread array<float2, int(16)> out_0;

#line 2002
                        z_0 = 0U;

#line 2002
                        for(;;)
                        {

#line 2002
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2002
                                break;
                            }

#line 2002
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2002
                            z_0 = z_0 + 1U;

#line 2002
                        }

#line 2002
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2002
                        _S18 = spanMask_0;

#line 2002
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2002
                        uint p0_0 = computeWant_0(0U, 64U, 1024U, blk_1, lane_1, per_1, _S27, 64U, blk2_1, lane2_1);

#line 2002
                        uint _S28 = p0_0 & lenMask_0;

#line 2002
                        uint _S29 = _S28 >> lgTB_0;

#line 2002
                        uint _S30 = _S29 * 64U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S28 & spanMask_0);

#line 2002
                        c_1 = 0U;

#line 2002
                        for(;;)
                        {

#line 2002
                            if(c_1 < 2U)
                            {
                            }
                            else
                            {

#line 2002
                                break;
                            }

#line 2002
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2002
                            j_1 = 0U;

#line 2002
                            for(;;)
                            {

#line 2002
                                if(j_1 < 8U)
                                {
                                }
                                else
                                {

#line 2002
                                    break;
                                }

#line 2002
                                stgPut_0(j_1 * 64U + (&kernelContext_2)->_tid_0, r_3[c_1 * 8U + j_1], &kernelContext_2);

#line 2002
                                j_1 = j_1 + 1U;

#line 2002
                            }

#line 2002
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2002
                            d_2 = 0U;

#line 2002
                            for(;;)
                            {

#line 2002
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2002
                                    break;
                                }

#line 2002
                                uint pz_0 = computeWant_0(d_2, 64U, 1024U, 0U, 0U, per_1, _S27, 64U, 0U, 0U);

#line 2002
                                uint _S31 = pz_0 & lenMask_0;

#line 2002
                                uint iz_0 = _S31 >> lgTB_0;

#line 2002
                                uint az_0 = iz_0 * 64U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S31 & spanMask_0);

#line 2002
                                uint i_3 = _S29 + iz_0;

#line 2002
                                uint _S32 = c_1 * 8U;

#line 2002
                                if(i_3 >= _S32)
                                {

#line 2002
                                    _S19 = i_3 < ((c_1 + 1U) * 8U);

#line 2002
                                }
                                else
                                {

#line 2002
                                    _S19 = false;

#line 2002
                                }

#line 2002
                                if(_S19)
                                {

#line 2002
                                    float2 _S33 = stgGet_0(_S30 + az_0 - _S32 * 64U, &kernelContext_2);

#line 2002
                                    out_0[d_2] = _S33;

#line 2002
                                }

#line 2002
                                d_2 = d_2 + 1U;

#line 2002
                            }

#line 2002
                            c_1 = c_1 + 1U;

#line 2002
                        }

#line 2002
                        d_2 = 0U;

#line 2002
                        for(;;)
                        {

#line 2002
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2002
                                break;
                            }

#line 2002
                            r_3[d_2] = out_0[d_2];

#line 2002
                            d_2 = d_2 + 1U;

#line 2002
                        }

#line 2002
                        break;
                    }

#line 2002
                    break;
                }

#line 2002
                break;
            }

#line 2002
            for(;;)
            {

#line 2002
                for(;;)
                {

#line 2002
                    uint lgTB_1 = firstbithigh_0(4U);

#line 2002
                    uint blk_2 = tid_0 >> lgTB_1;

#line 2002
                    uint lane_2 = tid_0 & 3U;

#line 2002
                    dft16_0(&r_3);

#line 2002
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 64.0f);

#line 2002
                    float _S34 = tw_1.x;

#line 2002
                    float _S35 = tw_1.y;

#line 2002
                    k2_1 = 0U;

#line 2002
                    cr_0 = 1.0f;

#line 2002
                    ci_0 = 0.0f;

#line 2002
                    for(;;)
                    {

#line 2002
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2002
                            break;
                        }

#line 2002
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2002
                        float nr_1 = cr_0 * _S34 - ci_0 * _S35;

#line 2002
                        float _S36 = cr_0 * _S35 + ci_0 * _S34;

#line 2002
                        k2_1 = k2_1 + 1U;

#line 2002
                        cr_0 = nr_1;

#line 2002
                        ci_0 = _S36;

#line 2002
                    }

#line 2002
                    uint per_2 = 16U / _S17;

#line 2002
                    uint _S37 = max(0U, 1U);

#line 2002
                    uint blk2_2 = tid_0 / _S37;

#line 2002
                    uint lane2_2 = tid_0 % _S37;

#line 2002
                    for(;;)
                    {

#line 2002
                        thread array<float2, int(16)> out_1;

#line 2002
                        z_0 = 0U;

#line 2002
                        for(;;)
                        {

#line 2002
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2002
                                break;
                            }

#line 2002
                            out_1[z_0] = float2(0.0f, 0.0f);

#line 2002
                            z_0 = z_0 + 1U;

#line 2002
                        }

#line 2002
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2002
                        uint p0_1 = computeWant_0(0U, 4U, 64U, blk_2, lane_2, per_2, _S37, 4U, blk2_2, lane2_2);

#line 2002
                        uint _S38 = p0_1 & _S18;

#line 2002
                        uint _S39 = _S38 >> lgTB_1;

#line 2002
                        uint _S40 = _S39 * 64U + ((p0_1 >> _S16) << lgTB_1) + (_S38 & spanMask_1);

#line 2002
                        c_1 = 0U;

#line 2002
                        for(;;)
                        {

#line 2002
                            if(c_1 < 2U)
                            {
                            }
                            else
                            {

#line 2002
                                break;
                            }

#line 2002
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2002
                            j_1 = 0U;

#line 2002
                            for(;;)
                            {

#line 2002
                                if(j_1 < 8U)
                                {
                                }
                                else
                                {

#line 2002
                                    break;
                                }

#line 2002
                                stgPut_0(j_1 * 64U + (&kernelContext_2)->_tid_0, r_3[c_1 * 8U + j_1], &kernelContext_2);

#line 2002
                                j_1 = j_1 + 1U;

#line 2002
                            }

#line 2002
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2002
                            d_2 = 0U;

#line 2002
                            for(;;)
                            {

#line 2002
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2002
                                    break;
                                }

#line 2002
                                uint pz_1 = computeWant_0(d_2, 4U, 64U, 0U, 0U, per_2, _S37, 4U, 0U, 0U);

#line 2002
                                uint _S41 = pz_1 & _S18;

#line 2002
                                uint iz_1 = _S41 >> lgTB_1;

#line 2002
                                uint az_1 = iz_1 * 64U + ((pz_1 >> _S16) << lgTB_1) + (_S41 & spanMask_1);

#line 2002
                                uint i_4 = _S39 + iz_1;

#line 2002
                                uint _S42 = c_1 * 8U;

#line 2002
                                if(i_4 >= _S42)
                                {

#line 2002
                                    _S19 = i_4 < ((c_1 + 1U) * 8U);

#line 2002
                                }
                                else
                                {

#line 2002
                                    _S19 = false;

#line 2002
                                }

#line 2002
                                if(_S19)
                                {

#line 2002
                                    float2 _S43 = stgGet_0(_S40 + az_1 - _S42 * 64U, &kernelContext_2);

#line 2002
                                    out_1[d_2] = _S43;

#line 2002
                                }

#line 2002
                                d_2 = d_2 + 1U;

#line 2002
                            }

#line 2002
                            c_1 = c_1 + 1U;

#line 2002
                        }

#line 2002
                        d_2 = 0U;

#line 2002
                        for(;;)
                        {

#line 2002
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2002
                                break;
                            }

#line 2002
                            r_3[d_2] = out_1[d_2];

#line 2002
                            d_2 = d_2 + 1U;

#line 2002
                        }

#line 2002
                        break;
                    }

#line 2002
                    break;
                }

#line 2002
                break;
            }

#line 2002
            break;
        }

#line 2002
        innermost_0(&r_3);

#line 2002
        break;
    }

#line 2002
    j_1 = 0U;

#line 2007
    for(;;)
    {

#line 2007
        if(j_1 < 16U)
        {
        }
        else
        {

#line 2007
            break;
        }

#line 2008
        uint k2_2 = slotToIndex_0(tid_0 * 16U + j_1);

#line 2008
        *((&kernelContext_2)->entryPointParams_scratch_0+(pair_0 * 1048576U + k2_2 * 1024U + _S21)) = packed_float2(cmul_0(r_3[j_1], mfTwiddle_0(6.28318548202514648f * float(_S21 * k2_2) / 1.048576e+06f))) ;

#line 2007
        j_1 = j_1 + 1U;

#line 2007
    }

#line 2012
    return;
}
