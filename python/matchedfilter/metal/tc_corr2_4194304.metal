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


#line 576 "tc_corr2_4194304.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 578
    float2 t1_0 = *a_0 - *c_0;

#line 578
    float2 t2_0 = *b_0 + *d_0;

#line 578
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 580
    *b_0 = t1_0 + j3_0;

#line 580
    *c_0 = t0_0 - t2_0;

#line 580
    *d_0 = t1_0 - j3_0;
    return;
}


#line 316
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 316
    float _S2 = a_1.x;

#line 316
    float _S3 = b_1.x;

#line 316
    float _S4 = a_1.y;

#line 316
    float _S5 = b_1.y;

#line 316
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
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
        uint _S6 = 4U * k2_0;

#line 624
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

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


#line 318 "tc_corr2_4194304.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S7 = max(TB_0, 1U);

#line 320
    uint j_0 = d_1 / _S7;

#line 320
    uint m_0 = d_1 % _S7;

#line 320
    uint _S8;
    if(TB_0 <= 16U)
    {

#line 321
        _S8 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 321
    }
    else
    {

#line 321
        _S8 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 321
    }

#line 321
    return _S8;
}


#line 305
struct KernelContext_0
{
    packed_float2 device* entryPointParams_scratch_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 305
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 305
    uint _S9 = 2U * i_0;

#line 305
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9] = (as_type<uint>((v_0.x)));

#line 305
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9 + 1U] = (as_type<uint>((v_0.y)));

#line 305
    return;
}


#line 306
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 306
    uint _S10 = 2U * i_1;

#line 306
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10 + 1U]))));
}


#line 596
void dft8_0(array<float2, int(16)> thread* r_1, uint o_0)
{


    thread array<float2, int(8)> b_2;

#line 600
    uint s_0 = 1U;
    for(;;)
    {

#line 601
        if(s_0 < 8U)
        {
        }
        else
        {

#line 601
            break;
        }

#line 601
        uint j_1 = 0U;
        for(;;)
        {

#line 602
            if(j_1 < 4U)
            {
            }
            else
            {

#line 602
                break;
            }

#line 603
            uint k_0 = j_1 & (s_0 - 1U);


            uint _S11 = o_0 + j_1;

#line 606
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_0)), (*r_1)[_S11 + 4U]);
            uint _S12 = ((j_1 - k_0) << 1U) + k_0;

#line 607
            b_2[_S12] = (*r_1)[_S11] + t_6;

#line 607
            b_2[_S12 + s_0] = (*r_1)[_S11] - t_6;

#line 602
            j_1 = j_1 + 1U;

#line 602
        }

#line 602
        uint i_2 = 0U;

#line 609
        for(;;)
        {

#line 609
            if(i_2 < 8U)
            {
            }
            else
            {

#line 609
                break;
            }

#line 609
            (*r_1)[o_0 + i_2] = b_2[i_2];

#line 609
            i_2 = i_2 + 1U;

#line 609
        }

#line 601
        s_0 = s_0 << 1U;

#line 601
    }

#line 611
    return;
}


#line 715
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 715
    uint b_3 = 0U;

#line 723
    for(;;)
    {

#line 723
        if(b_3 < 2U)
        {
        }
        else
        {

#line 723
            break;
        }

#line 723
        dft8_0(r_2, b_3 * 8U);

#line 723
        b_3 = b_3 + 1U;

#line 723
    }



    return;
}


#line 862
uint lgOf_0(uint i_3)
{

#line 862
    uint _S13;

#line 862
    if(i_3 < 2U)
    {

#line 862
        _S13 = 4U;

#line 862
    }
    else
    {

#line 862
        if(i_3 == 2U)
        {

#line 862
            _S13 = 3U;

#line 862
        }
        else
        {

#line 862
            _S13 = 1U;

#line 862
        }

#line 862
    }

#line 862
    return _S13;
}


#line 864
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 868
    uint lg_1 = lgOf_0(1U);

#line 868
    uint lg_2 = lgOf_0(0U);

#line 873
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2083
[[kernel]] void tcFullStage3(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], packed_float2 device* entryPointParams_scratch_1 [[buffer(0)]], packed_float2 device* entryPointParams_output_1 [[buffer(1)]])
{

#line 2083
    uint _S14;

#line 2083
    uint k2_1;

#line 2083
    float cr_0;

#line 2083
    float ci_0;

#line 2083
    uint _S15;

#line 2083
    uint z_0;

#line 2083
    uint _S16;

#line 2083
    uint c_1;

#line 2083
    uint d_2;

#line 2083
    uint j_2;

#line 2083
    bool _S17;

#line 2083
    thread KernelContext_0 kernelContext_2;

#line 2083
    (&kernelContext_2)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 2083
    (&kernelContext_2)->entryPointParams_output_0 = entryPointParams_output_1;

#line 2083
    threadgroup array<uint, int(2048)> stg_1;

#line 2083
    (&kernelContext_2)->stg_0 = &stg_1;



    uint _S18 = gid_0.x;

#line 2087
    uint _S19 = _S18 / 2048U;

#line 2087
    uint _S20 = _S18 % 2048U;
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_3;

#line 2091
    uint m_1 = 0U;
    for(;;)
    {

#line 2092
        if(m_1 < 16U)
        {
        }
        else
        {

#line 2092
            break;
        }

#line 2093
        r_3[m_1] = float2(*((&kernelContext_2)->entryPointParams_scratch_0+(_S19 * 4194304U + _S20 * 2048U + tid_0 + 128U * m_1))) ;

#line 2092
        m_1 = m_1 + 1U;

#line 2092
    }

    for(;;)
    {

#line 2094
        for(;;)
        {

#line 2094
            for(;;)
            {

#line 2094
                for(;;)
                {

#line 2094
                    uint lgTB_0 = firstbithigh_0(128U);

#line 2094
                    _S14 = lgTB_0;

#line 2094
                    uint lgLn_0 = firstbithigh_0(2048U);

#line 2094
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2094
                    uint lane_1 = tid_0 & 127U;

#line 2094
                    dft16_0(&r_3);

#line 2094
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 2048.0f);

#line 2094
                    float _S21 = tw_0.x;

#line 2094
                    float _S22 = tw_0.y;

#line 2094
                    k2_1 = 0U;

#line 2094
                    cr_0 = 1.0f;

#line 2094
                    ci_0 = 0.0f;

#line 2094
                    for(;;)
                    {

#line 2094
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2094
                            break;
                        }

#line 2094
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2094
                        float nr_0 = cr_0 * _S21 - ci_0 * _S22;

#line 2094
                        float _S23 = cr_0 * _S22 + ci_0 * _S21;

#line 2094
                        k2_1 = k2_1 + 1U;

#line 2094
                        cr_0 = nr_0;

#line 2094
                        ci_0 = _S23;

#line 2094
                    }

#line 2094
                    uint per_1 = 16U / max(128U, 1U);

#line 2094
                    uint _S24 = max(8U, 1U);

#line 2094
                    _S15 = _S24;

#line 2094
                    uint blk2_1 = tid_0 / _S24;

#line 2094
                    uint lane2_1 = tid_0 % _S24;

#line 2094
                    for(;;)
                    {

#line 2094
                        thread array<float2, int(16)> out_0;

#line 2094
                        z_0 = 0U;

#line 2094
                        for(;;)
                        {

#line 2094
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2094
                                break;
                            }

#line 2094
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2094
                            z_0 = z_0 + 1U;

#line 2094
                        }

#line 2094
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2094
                        _S16 = spanMask_0;

#line 2094
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2094
                        uint p0_0 = computeWant_0(0U, 128U, 2048U, blk_1, lane_1, per_1, _S24, 128U, blk2_1, lane2_1);

#line 2094
                        uint _S25 = p0_0 & lenMask_0;

#line 2094
                        uint _S26 = _S25 >> lgTB_0;

#line 2094
                        uint _S27 = _S26 * 128U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S25 & spanMask_0);

#line 2094
                        c_1 = 0U;

#line 2094
                        for(;;)
                        {

#line 2094
                            if(c_1 < 2U)
                            {
                            }
                            else
                            {

#line 2094
                                break;
                            }

#line 2094
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2094
                            j_2 = 0U;

#line 2094
                            for(;;)
                            {

#line 2094
                                if(j_2 < 8U)
                                {
                                }
                                else
                                {

#line 2094
                                    break;
                                }

#line 2094
                                stgPut_0(j_2 * 128U + (&kernelContext_2)->_tid_0, r_3[c_1 * 8U + j_2], &kernelContext_2);

#line 2094
                                j_2 = j_2 + 1U;

#line 2094
                            }

#line 2094
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2094
                            d_2 = 0U;

#line 2094
                            for(;;)
                            {

#line 2094
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2094
                                    break;
                                }

#line 2094
                                uint pz_0 = computeWant_0(d_2, 128U, 2048U, 0U, 0U, per_1, _S24, 128U, 0U, 0U);

#line 2094
                                uint _S28 = pz_0 & lenMask_0;

#line 2094
                                uint iz_0 = _S28 >> lgTB_0;

#line 2094
                                uint az_0 = iz_0 * 128U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S28 & spanMask_0);

#line 2094
                                uint i_4 = _S26 + iz_0;

#line 2094
                                uint _S29 = c_1 * 8U;

#line 2094
                                if(i_4 >= _S29)
                                {

#line 2094
                                    _S17 = i_4 < ((c_1 + 1U) * 8U);

#line 2094
                                }
                                else
                                {

#line 2094
                                    _S17 = false;

#line 2094
                                }

#line 2094
                                if(_S17)
                                {

#line 2094
                                    float2 _S30 = stgGet_0(_S27 + az_0 - _S29 * 128U, &kernelContext_2);

#line 2094
                                    out_0[d_2] = _S30;

#line 2094
                                }

#line 2094
                                d_2 = d_2 + 1U;

#line 2094
                            }

#line 2094
                            c_1 = c_1 + 1U;

#line 2094
                        }

#line 2094
                        d_2 = 0U;

#line 2094
                        for(;;)
                        {

#line 2094
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2094
                                break;
                            }

#line 2094
                            r_3[d_2] = out_0[d_2];

#line 2094
                            d_2 = d_2 + 1U;

#line 2094
                        }

#line 2094
                        break;
                    }

#line 2094
                    break;
                }

#line 2094
                break;
            }

#line 2094
            for(;;)
            {

#line 2094
                for(;;)
                {

#line 2094
                    uint lgTB_1 = firstbithigh_0(8U);

#line 2094
                    uint blk_2 = tid_0 >> lgTB_1;

#line 2094
                    uint lane_2 = tid_0 & 7U;

#line 2094
                    dft16_0(&r_3);

#line 2094
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 128.0f);

#line 2094
                    float _S31 = tw_1.x;

#line 2094
                    float _S32 = tw_1.y;

#line 2094
                    k2_1 = 0U;

#line 2094
                    cr_0 = 1.0f;

#line 2094
                    ci_0 = 0.0f;

#line 2094
                    for(;;)
                    {

#line 2094
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2094
                            break;
                        }

#line 2094
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2094
                        float nr_1 = cr_0 * _S31 - ci_0 * _S32;

#line 2094
                        float _S33 = cr_0 * _S32 + ci_0 * _S31;

#line 2094
                        k2_1 = k2_1 + 1U;

#line 2094
                        cr_0 = nr_1;

#line 2094
                        ci_0 = _S33;

#line 2094
                    }

#line 2094
                    uint per_2 = 16U / _S15;

#line 2094
                    uint _S34 = max(0U, 1U);

#line 2094
                    uint blk2_2 = tid_0 / _S34;

#line 2094
                    uint lane2_2 = tid_0 % _S34;

#line 2094
                    for(;;)
                    {

#line 2094
                        thread array<float2, int(16)> out_1;

#line 2094
                        z_0 = 0U;

#line 2094
                        for(;;)
                        {

#line 2094
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2094
                                break;
                            }

#line 2094
                            out_1[z_0] = float2(0.0f, 0.0f);

#line 2094
                            z_0 = z_0 + 1U;

#line 2094
                        }

#line 2094
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2094
                        uint p0_1 = computeWant_0(0U, 8U, 128U, blk_2, lane_2, per_2, _S34, 8U, blk2_2, lane2_2);

#line 2094
                        uint _S35 = p0_1 & _S16;

#line 2094
                        uint _S36 = _S35 >> lgTB_1;

#line 2094
                        uint _S37 = _S36 * 128U + ((p0_1 >> _S14) << lgTB_1) + (_S35 & spanMask_1);

#line 2094
                        c_1 = 0U;

#line 2094
                        for(;;)
                        {

#line 2094
                            if(c_1 < 2U)
                            {
                            }
                            else
                            {

#line 2094
                                break;
                            }

#line 2094
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2094
                            j_2 = 0U;

#line 2094
                            for(;;)
                            {

#line 2094
                                if(j_2 < 8U)
                                {
                                }
                                else
                                {

#line 2094
                                    break;
                                }

#line 2094
                                stgPut_0(j_2 * 128U + (&kernelContext_2)->_tid_0, r_3[c_1 * 8U + j_2], &kernelContext_2);

#line 2094
                                j_2 = j_2 + 1U;

#line 2094
                            }

#line 2094
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2094
                            d_2 = 0U;

#line 2094
                            for(;;)
                            {

#line 2094
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2094
                                    break;
                                }

#line 2094
                                uint pz_1 = computeWant_0(d_2, 8U, 128U, 0U, 0U, per_2, _S34, 8U, 0U, 0U);

#line 2094
                                uint _S38 = pz_1 & _S16;

#line 2094
                                uint iz_1 = _S38 >> lgTB_1;

#line 2094
                                uint az_1 = iz_1 * 128U + ((pz_1 >> _S14) << lgTB_1) + (_S38 & spanMask_1);

#line 2094
                                uint i_5 = _S36 + iz_1;

#line 2094
                                uint _S39 = c_1 * 8U;

#line 2094
                                if(i_5 >= _S39)
                                {

#line 2094
                                    _S17 = i_5 < ((c_1 + 1U) * 8U);

#line 2094
                                }
                                else
                                {

#line 2094
                                    _S17 = false;

#line 2094
                                }

#line 2094
                                if(_S17)
                                {

#line 2094
                                    float2 _S40 = stgGet_0(_S37 + az_1 - _S39 * 128U, &kernelContext_2);

#line 2094
                                    out_1[d_2] = _S40;

#line 2094
                                }

#line 2094
                                d_2 = d_2 + 1U;

#line 2094
                            }

#line 2094
                            c_1 = c_1 + 1U;

#line 2094
                        }

#line 2094
                        d_2 = 0U;

#line 2094
                        for(;;)
                        {

#line 2094
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2094
                                break;
                            }

#line 2094
                            r_3[d_2] = out_1[d_2];

#line 2094
                            d_2 = d_2 + 1U;

#line 2094
                        }

#line 2094
                        break;
                    }

#line 2094
                    break;
                }

#line 2094
                break;
            }

#line 2094
            break;
        }

#line 2094
        innermost_0(&r_3);

#line 2094
        break;
    }

#line 2094
    j_2 = 0U;
    for(;;)
    {

#line 2095
        if(j_2 < 16U)
        {
        }
        else
        {

#line 2095
            break;
        }

#line 2095
        *((&kernelContext_2)->entryPointParams_output_0+(_S19 * 4194304U + slotToIndex_0(tid_0 * 16U + j_2) * 2048U + _S20)) = packed_float2(float2(r_3[j_2].x, r_3[j_2].y)) ;

#line 2095
        j_2 = j_2 + 1U;

#line 2095
    }



    return;
}
