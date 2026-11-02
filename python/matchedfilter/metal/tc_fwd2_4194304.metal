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


#line 609 "tc_fwd2_4194304.slang"
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


#line 324 "tc_fwd2_4194304.slang"
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


#line 311
struct KernelContext_0
{
    packed_float2 device* entryPointParams_scratch_0;
    packed_float2 device* entryPointParams_spectra_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(2048)> threadgroup* stg_0;
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


#line 629
void dft8_0(array<float2, int(16)> thread* r_1, uint o_0)
{


    thread array<float2, int(8)> b_2;

#line 633
    uint s_0 = 1U;
    for(;;)
    {

#line 634
        if(s_0 < 8U)
        {
        }
        else
        {

#line 634
            break;
        }

#line 634
        uint j_1 = 0U;
        for(;;)
        {

#line 635
            if(j_1 < 4U)
            {
            }
            else
            {

#line 635
                break;
            }

#line 636
            uint k_0 = j_1 & (s_0 - 1U);


            uint _S11 = o_0 + j_1;

#line 639
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_0)), (*r_1)[_S11 + 4U]);
            uint _S12 = ((j_1 - k_0) << 1U) + k_0;

#line 640
            b_2[_S12] = (*r_1)[_S11] + t_6;

#line 640
            b_2[_S12 + s_0] = (*r_1)[_S11] - t_6;

#line 635
            j_1 = j_1 + 1U;

#line 635
        }

#line 635
        uint i_2 = 0U;

#line 642
        for(;;)
        {

#line 642
            if(i_2 < 8U)
            {
            }
            else
            {

#line 642
                break;
            }

#line 642
            (*r_1)[o_0 + i_2] = b_2[i_2];

#line 642
            i_2 = i_2 + 1U;

#line 642
        }

#line 634
        s_0 = s_0 << 1U;

#line 634
    }

#line 644
    return;
}


#line 748
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 748
    uint b_3 = 0U;

#line 756
    for(;;)
    {

#line 756
        if(b_3 < 2U)
        {
        }
        else
        {

#line 756
            break;
        }

#line 756
        dft8_0(r_2, b_3 * 8U);

#line 756
        b_3 = b_3 + 1U;

#line 756
    }



    return;
}


#line 876
uint lgOf_0(uint i_3)
{

#line 876
    uint _S13;

#line 876
    if(i_3 < 2U)
    {

#line 876
        _S13 = 4U;

#line 876
    }
    else
    {

#line 876
        if(i_3 == 2U)
        {

#line 876
            _S13 = 3U;

#line 876
        }
        else
        {

#line 876
            _S13 = 1U;

#line 876
        }

#line 876
    }

#line 876
    return _S13;
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


#line 2310
[[kernel]] void tcForwardStage3(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], packed_float2 device* entryPointParams_scratch_1 [[buffer(0)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(1)]])
{

#line 2310
    uint _S14;

#line 2310
    uint k2_1;

#line 2310
    float cr_0;

#line 2310
    float ci_0;

#line 2310
    uint _S15;

#line 2310
    uint z_0;

#line 2310
    uint _S16;

#line 2310
    uint c_1;

#line 2310
    uint d_2;

#line 2310
    uint j_2;

#line 2310
    bool _S17;

#line 2310
    thread KernelContext_0 kernelContext_2;

#line 2310
    (&kernelContext_2)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 2310
    (&kernelContext_2)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 2310
    threadgroup array<uint, int(2048)> stg_1;

#line 2310
    (&kernelContext_2)->stg_0 = &stg_1;



    uint _S18 = gid_0.x;

#line 2314
    uint _S19 = _S18 / 2048U;

#line 2314
    uint _S20 = _S18 % 2048U;
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_3;

#line 2318
    uint m_1 = 0U;
    for(;;)
    {

#line 2319
        if(m_1 < 16U)
        {
        }
        else
        {

#line 2319
            break;
        }

#line 2320
        r_3[m_1] = float2(*((&kernelContext_2)->entryPointParams_scratch_0+(_S19 * 4194304U + _S20 * 2048U + tid_0 + 128U * m_1))) ;

#line 2319
        m_1 = m_1 + 1U;

#line 2319
    }

    for(;;)
    {

#line 2321
        for(;;)
        {

#line 2321
            for(;;)
            {

#line 2321
                for(;;)
                {

#line 2321
                    uint lgTB_0 = firstbithigh_0(128U);

#line 2321
                    _S14 = lgTB_0;

#line 2321
                    uint lgLn_0 = firstbithigh_0(2048U);

#line 2321
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2321
                    uint lane_1 = tid_0 & 127U;

#line 2321
                    dft16_0(&r_3);

#line 2321
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 2048.0f);

#line 2321
                    float _S21 = tw_0.x;

#line 2321
                    float _S22 = tw_0.y;

#line 2321
                    k2_1 = 0U;

#line 2321
                    cr_0 = 1.0f;

#line 2321
                    ci_0 = 0.0f;

#line 2321
                    for(;;)
                    {

#line 2321
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2321
                            break;
                        }

#line 2321
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2321
                        float nr_0 = cr_0 * _S21 - ci_0 * _S22;

#line 2321
                        float _S23 = cr_0 * _S22 + ci_0 * _S21;

#line 2321
                        k2_1 = k2_1 + 1U;

#line 2321
                        cr_0 = nr_0;

#line 2321
                        ci_0 = _S23;

#line 2321
                    }

#line 2321
                    uint per_1 = 16U / max(128U, 1U);

#line 2321
                    uint _S24 = max(8U, 1U);

#line 2321
                    _S15 = _S24;

#line 2321
                    uint blk2_1 = tid_0 / _S24;

#line 2321
                    uint lane2_1 = tid_0 % _S24;

#line 2321
                    for(;;)
                    {

#line 2321
                        thread array<float2, int(16)> out_0;

#line 2321
                        z_0 = 0U;

#line 2321
                        for(;;)
                        {

#line 2321
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2321
                                break;
                            }

#line 2321
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2321
                            z_0 = z_0 + 1U;

#line 2321
                        }

#line 2321
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2321
                        _S16 = spanMask_0;

#line 2321
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2321
                        uint p0_0 = computeWant_0(0U, 128U, 2048U, blk_1, lane_1, per_1, _S24, 128U, blk2_1, lane2_1);

#line 2321
                        uint _S25 = p0_0 & lenMask_0;

#line 2321
                        uint _S26 = _S25 >> lgTB_0;

#line 2321
                        uint _S27 = _S26 * 128U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S25 & spanMask_0);

#line 2321
                        c_1 = 0U;

#line 2321
                        for(;;)
                        {

#line 2321
                            if(c_1 < 2U)
                            {
                            }
                            else
                            {

#line 2321
                                break;
                            }

#line 2321
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2321
                            j_2 = 0U;

#line 2321
                            for(;;)
                            {

#line 2321
                                if(j_2 < 8U)
                                {
                                }
                                else
                                {

#line 2321
                                    break;
                                }

#line 2321
                                stgPut_0(j_2 * 128U + (&kernelContext_2)->_tid_0, r_3[c_1 * 8U + j_2], &kernelContext_2);

#line 2321
                                j_2 = j_2 + 1U;

#line 2321
                            }

#line 2321
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2321
                            d_2 = 0U;

#line 2321
                            for(;;)
                            {

#line 2321
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2321
                                    break;
                                }

#line 2321
                                uint pz_0 = computeWant_0(d_2, 128U, 2048U, 0U, 0U, per_1, _S24, 128U, 0U, 0U);

#line 2321
                                uint _S28 = pz_0 & lenMask_0;

#line 2321
                                uint iz_0 = _S28 >> lgTB_0;

#line 2321
                                uint az_0 = iz_0 * 128U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S28 & spanMask_0);

#line 2321
                                uint i_4 = _S26 + iz_0;

#line 2321
                                uint _S29 = c_1 * 8U;

#line 2321
                                if(i_4 >= _S29)
                                {

#line 2321
                                    _S17 = i_4 < ((c_1 + 1U) * 8U);

#line 2321
                                }
                                else
                                {

#line 2321
                                    _S17 = false;

#line 2321
                                }

#line 2321
                                if(_S17)
                                {

#line 2321
                                    float2 _S30 = stgGet_0(_S27 + az_0 - _S29 * 128U, &kernelContext_2);

#line 2321
                                    out_0[d_2] = _S30;

#line 2321
                                }

#line 2321
                                d_2 = d_2 + 1U;

#line 2321
                            }

#line 2321
                            c_1 = c_1 + 1U;

#line 2321
                        }

#line 2321
                        d_2 = 0U;

#line 2321
                        for(;;)
                        {

#line 2321
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2321
                                break;
                            }

#line 2321
                            r_3[d_2] = out_0[d_2];

#line 2321
                            d_2 = d_2 + 1U;

#line 2321
                        }

#line 2321
                        break;
                    }

#line 2321
                    break;
                }

#line 2321
                break;
            }

#line 2321
            for(;;)
            {

#line 2321
                for(;;)
                {

#line 2321
                    uint lgTB_1 = firstbithigh_0(8U);

#line 2321
                    uint blk_2 = tid_0 >> lgTB_1;

#line 2321
                    uint lane_2 = tid_0 & 7U;

#line 2321
                    dft16_0(&r_3);

#line 2321
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 128.0f);

#line 2321
                    float _S31 = tw_1.x;

#line 2321
                    float _S32 = tw_1.y;

#line 2321
                    k2_1 = 0U;

#line 2321
                    cr_0 = 1.0f;

#line 2321
                    ci_0 = 0.0f;

#line 2321
                    for(;;)
                    {

#line 2321
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2321
                            break;
                        }

#line 2321
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2321
                        float nr_1 = cr_0 * _S31 - ci_0 * _S32;

#line 2321
                        float _S33 = cr_0 * _S32 + ci_0 * _S31;

#line 2321
                        k2_1 = k2_1 + 1U;

#line 2321
                        cr_0 = nr_1;

#line 2321
                        ci_0 = _S33;

#line 2321
                    }

#line 2321
                    uint per_2 = 16U / _S15;

#line 2321
                    uint _S34 = max(0U, 1U);

#line 2321
                    uint blk2_2 = tid_0 / _S34;

#line 2321
                    uint lane2_2 = tid_0 % _S34;

#line 2321
                    for(;;)
                    {

#line 2321
                        thread array<float2, int(16)> out_1;

#line 2321
                        z_0 = 0U;

#line 2321
                        for(;;)
                        {

#line 2321
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2321
                                break;
                            }

#line 2321
                            out_1[z_0] = float2(0.0f, 0.0f);

#line 2321
                            z_0 = z_0 + 1U;

#line 2321
                        }

#line 2321
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2321
                        uint p0_1 = computeWant_0(0U, 8U, 128U, blk_2, lane_2, per_2, _S34, 8U, blk2_2, lane2_2);

#line 2321
                        uint _S35 = p0_1 & _S16;

#line 2321
                        uint _S36 = _S35 >> lgTB_1;

#line 2321
                        uint _S37 = _S36 * 128U + ((p0_1 >> _S14) << lgTB_1) + (_S35 & spanMask_1);

#line 2321
                        c_1 = 0U;

#line 2321
                        for(;;)
                        {

#line 2321
                            if(c_1 < 2U)
                            {
                            }
                            else
                            {

#line 2321
                                break;
                            }

#line 2321
                            bool _S38 = c_1 == 0U;

#line 2321
                            if(!_S38)
                            {

#line 2321
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2321
                            }
                            else
                            {

#line 2321
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2321
                            }

#line 2321
                            j_2 = 0U;

#line 2321
                            for(;;)
                            {

#line 2321
                                if(j_2 < 8U)
                                {
                                }
                                else
                                {

#line 2321
                                    break;
                                }

#line 2321
                                stgPut_0(j_2 * 128U + (&kernelContext_2)->_tid_0, r_3[c_1 * 8U + j_2], &kernelContext_2);

#line 2321
                                j_2 = j_2 + 1U;

#line 2321
                            }

#line 2321
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2321
                            d_2 = 0U;

#line 2321
                            for(;;)
                            {

#line 2321
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2321
                                    break;
                                }

#line 2321
                                uint pz_1 = computeWant_0(d_2, 8U, 128U, 0U, 0U, per_2, _S34, 8U, 0U, 0U);

#line 2321
                                uint _S39 = pz_1 & _S16;

#line 2321
                                uint iz_1 = _S39 >> lgTB_1;

#line 2321
                                uint az_1 = iz_1 * 128U + ((pz_1 >> _S14) << lgTB_1) + (_S39 & spanMask_1);

#line 2321
                                uint i_5 = _S36 + iz_1;

#line 2321
                                uint _S40 = c_1 * 8U;

#line 2321
                                if(i_5 >= _S40)
                                {

#line 2321
                                    _S17 = i_5 < ((c_1 + 1U) * 8U);

#line 2321
                                }
                                else
                                {

#line 2321
                                    _S17 = false;

#line 2321
                                }

#line 2321
                                if(_S17)
                                {

#line 2321
                                    float2 _S41 = stgGet_0(_S37 + az_1 - _S40 * 128U, &kernelContext_2);

#line 2321
                                    out_1[d_2] = _S41;

#line 2321
                                }

#line 2321
                                d_2 = d_2 + 1U;

#line 2321
                            }

#line 2321
                            c_1 = c_1 + 1U;

#line 2321
                        }

#line 2321
                        d_2 = 0U;

#line 2321
                        for(;;)
                        {

#line 2321
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2321
                                break;
                            }

#line 2321
                            r_3[d_2] = out_1[d_2];

#line 2321
                            d_2 = d_2 + 1U;

#line 2321
                        }

#line 2321
                        break;
                    }

#line 2321
                    break;
                }

#line 2321
                break;
            }

#line 2321
            break;
        }

#line 2321
        innermost_0(&r_3);

#line 2321
        break;
    }

#line 2321
    j_2 = 0U;
    for(;;)
    {

#line 2322
        if(j_2 < 16U)
        {
        }
        else
        {

#line 2322
            break;
        }

#line 2322
        *((&kernelContext_2)->entryPointParams_spectra_0+(_S19 * 4194304U + slotToIndex_0(tid_0 * 16U + j_2) * 2048U + _S20)) = packed_float2(float2(r_3[j_2].x, - r_3[j_2].y)) ;

#line 2322
        j_2 = j_2 + 1U;

#line 2322
    }



    return;
}
