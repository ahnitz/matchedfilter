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


#line 607 "tc_fwd2_2097152.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 609
    float2 t1_0 = *a_0 - *c_0;

#line 609
    float2 t2_0 = *b_0 + *d_0;

#line 609
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 611
    *b_0 = t1_0 + j3_0;

#line 611
    *c_0 = t0_0 - t2_0;

#line 611
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
        uint _S6 = 4U * k2_0;

#line 655
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

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


#line 324 "tc_fwd2_2097152.slang"
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


#line 622
void dft4_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    r4_0(&(*r_1)[o_0], &(*r_1)[o_0 + 1U], &(*r_1)[o_0 + 2U], &(*r_1)[o_0 + 3U]);
    float2 t_6 = (*r_1)[o_0 + 1U];

#line 625
    (*r_1)[o_0 + 1U] = (*r_1)[o_0 + 2U];

#line 625
    (*r_1)[o_0 + 2U] = t_6;
    return;
}


#line 746
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 746
    uint b_2 = 0U;

#line 755
    for(;;)
    {

#line 755
        if(b_2 < 4U)
        {
        }
        else
        {

#line 755
            break;
        }

#line 755
        dft4_0(r_2, b_2 * 4U);

#line 755
        b_2 = b_2 + 1U;

#line 755
    }


    return;
}


#line 874
uint lgOf_0(uint i_2)
{

#line 874
    uint _S11;

#line 874
    if(i_2 < 2U)
    {

#line 874
        _S11 = 4U;

#line 874
    }
    else
    {

#line 874
        _S11 = 1U;

#line 874
    }

#line 874
    return _S11;
}


#line 876
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 880
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 880
    uint lg_2 = lgOf_0(1U);

#line 880
    uint lg_3 = lgOf_0(0U);

#line 885
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 2206
[[kernel]] void tcForwardStage3(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], packed_float2 device* entryPointParams_scratch_1 [[buffer(0)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(1)]])
{

#line 2206
    uint _S12;

#line 2206
    uint k2_1;

#line 2206
    float cr_0;

#line 2206
    float ci_0;

#line 2206
    uint _S13;

#line 2206
    uint z_0;

#line 2206
    uint _S14;

#line 2206
    uint c_1;

#line 2206
    uint d_2;

#line 2206
    uint j_1;

#line 2206
    bool _S15;

#line 2206
    thread KernelContext_0 kernelContext_2;

#line 2206
    (&kernelContext_2)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 2206
    (&kernelContext_2)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 2206
    threadgroup array<uint, int(1024)> stg_1;

#line 2206
    (&kernelContext_2)->stg_0 = &stg_1;



    uint _S16 = gid_0.x;

#line 2210
    uint _S17 = _S16 / 2048U;

#line 2210
    uint _S18 = _S16 % 2048U;
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_3;

#line 2214
    uint m_1 = 0U;
    for(;;)
    {

#line 2215
        if(m_1 < 16U)
        {
        }
        else
        {

#line 2215
            break;
        }

#line 2216
        r_3[m_1] = float2(*((&kernelContext_2)->entryPointParams_scratch_0+(_S17 * 2097152U + _S18 * 1024U + tid_0 + 64U * m_1))) ;

#line 2215
        m_1 = m_1 + 1U;

#line 2215
    }

    for(;;)
    {

#line 2217
        for(;;)
        {

#line 2217
            for(;;)
            {

#line 2217
                for(;;)
                {

#line 2217
                    uint lgTB_0 = firstbithigh_0(64U);

#line 2217
                    _S12 = lgTB_0;

#line 2217
                    uint lgLn_0 = firstbithigh_0(1024U);

#line 2217
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2217
                    uint lane_1 = tid_0 & 63U;

#line 2217
                    dft16_0(&r_3);

#line 2217
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 1024.0f);

#line 2217
                    float _S19 = tw_0.x;

#line 2217
                    float _S20 = tw_0.y;

#line 2217
                    k2_1 = 0U;

#line 2217
                    cr_0 = 1.0f;

#line 2217
                    ci_0 = 0.0f;

#line 2217
                    for(;;)
                    {

#line 2217
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2217
                            break;
                        }

#line 2217
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2217
                        float nr_0 = cr_0 * _S19 - ci_0 * _S20;

#line 2217
                        float _S21 = cr_0 * _S20 + ci_0 * _S19;

#line 2217
                        k2_1 = k2_1 + 1U;

#line 2217
                        cr_0 = nr_0;

#line 2217
                        ci_0 = _S21;

#line 2217
                    }

#line 2217
                    uint per_1 = 16U / max(64U, 1U);

#line 2217
                    uint _S22 = max(4U, 1U);

#line 2217
                    _S13 = _S22;

#line 2217
                    uint blk2_1 = tid_0 / _S22;

#line 2217
                    uint lane2_1 = tid_0 % _S22;

#line 2217
                    for(;;)
                    {

#line 2217
                        thread array<float2, int(16)> out_0;

#line 2217
                        z_0 = 0U;

#line 2217
                        for(;;)
                        {

#line 2217
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2217
                                break;
                            }

#line 2217
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2217
                            z_0 = z_0 + 1U;

#line 2217
                        }

#line 2217
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2217
                        _S14 = spanMask_0;

#line 2217
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2217
                        uint p0_0 = computeWant_0(0U, 64U, 1024U, blk_1, lane_1, per_1, _S22, 64U, blk2_1, lane2_1);

#line 2217
                        uint _S23 = p0_0 & lenMask_0;

#line 2217
                        uint _S24 = _S23 >> lgTB_0;

#line 2217
                        uint _S25 = _S24 * 64U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S23 & spanMask_0);

#line 2217
                        c_1 = 0U;

#line 2217
                        for(;;)
                        {

#line 2217
                            if(c_1 < 2U)
                            {
                            }
                            else
                            {

#line 2217
                                break;
                            }

#line 2217
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2217
                            j_1 = 0U;

#line 2217
                            for(;;)
                            {

#line 2217
                                if(j_1 < 8U)
                                {
                                }
                                else
                                {

#line 2217
                                    break;
                                }

#line 2217
                                stgPut_0(j_1 * 64U + (&kernelContext_2)->_tid_0, r_3[c_1 * 8U + j_1], &kernelContext_2);

#line 2217
                                j_1 = j_1 + 1U;

#line 2217
                            }

#line 2217
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2217
                            d_2 = 0U;

#line 2217
                            for(;;)
                            {

#line 2217
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2217
                                    break;
                                }

#line 2217
                                uint pz_0 = computeWant_0(d_2, 64U, 1024U, 0U, 0U, per_1, _S22, 64U, 0U, 0U);

#line 2217
                                uint _S26 = pz_0 & lenMask_0;

#line 2217
                                uint iz_0 = _S26 >> lgTB_0;

#line 2217
                                uint az_0 = iz_0 * 64U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S26 & spanMask_0);

#line 2217
                                uint i_3 = _S24 + iz_0;

#line 2217
                                uint _S27 = c_1 * 8U;

#line 2217
                                if(i_3 >= _S27)
                                {

#line 2217
                                    _S15 = i_3 < ((c_1 + 1U) * 8U);

#line 2217
                                }
                                else
                                {

#line 2217
                                    _S15 = false;

#line 2217
                                }

#line 2217
                                if(_S15)
                                {

#line 2217
                                    float2 _S28 = stgGet_0(_S25 + az_0 - _S27 * 64U, &kernelContext_2);

#line 2217
                                    out_0[d_2] = _S28;

#line 2217
                                }

#line 2217
                                d_2 = d_2 + 1U;

#line 2217
                            }

#line 2217
                            c_1 = c_1 + 1U;

#line 2217
                        }

#line 2217
                        d_2 = 0U;

#line 2217
                        for(;;)
                        {

#line 2217
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2217
                                break;
                            }

#line 2217
                            r_3[d_2] = out_0[d_2];

#line 2217
                            d_2 = d_2 + 1U;

#line 2217
                        }

#line 2217
                        break;
                    }

#line 2217
                    break;
                }

#line 2217
                break;
            }

#line 2217
            for(;;)
            {

#line 2217
                for(;;)
                {

#line 2217
                    uint lgTB_1 = firstbithigh_0(4U);

#line 2217
                    uint blk_2 = tid_0 >> lgTB_1;

#line 2217
                    uint lane_2 = tid_0 & 3U;

#line 2217
                    dft16_0(&r_3);

#line 2217
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 64.0f);

#line 2217
                    float _S29 = tw_1.x;

#line 2217
                    float _S30 = tw_1.y;

#line 2217
                    k2_1 = 0U;

#line 2217
                    cr_0 = 1.0f;

#line 2217
                    ci_0 = 0.0f;

#line 2217
                    for(;;)
                    {

#line 2217
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2217
                            break;
                        }

#line 2217
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2217
                        float nr_1 = cr_0 * _S29 - ci_0 * _S30;

#line 2217
                        float _S31 = cr_0 * _S30 + ci_0 * _S29;

#line 2217
                        k2_1 = k2_1 + 1U;

#line 2217
                        cr_0 = nr_1;

#line 2217
                        ci_0 = _S31;

#line 2217
                    }

#line 2217
                    uint per_2 = 16U / _S13;

#line 2217
                    uint _S32 = max(0U, 1U);

#line 2217
                    uint blk2_2 = tid_0 / _S32;

#line 2217
                    uint lane2_2 = tid_0 % _S32;

#line 2217
                    for(;;)
                    {

#line 2217
                        thread array<float2, int(16)> out_1;

#line 2217
                        z_0 = 0U;

#line 2217
                        for(;;)
                        {

#line 2217
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2217
                                break;
                            }

#line 2217
                            out_1[z_0] = float2(0.0f, 0.0f);

#line 2217
                            z_0 = z_0 + 1U;

#line 2217
                        }

#line 2217
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2217
                        uint p0_1 = computeWant_0(0U, 4U, 64U, blk_2, lane_2, per_2, _S32, 4U, blk2_2, lane2_2);

#line 2217
                        uint _S33 = p0_1 & _S14;

#line 2217
                        uint _S34 = _S33 >> lgTB_1;

#line 2217
                        uint _S35 = _S34 * 64U + ((p0_1 >> _S12) << lgTB_1) + (_S33 & spanMask_1);

#line 2217
                        c_1 = 0U;

#line 2217
                        for(;;)
                        {

#line 2217
                            if(c_1 < 2U)
                            {
                            }
                            else
                            {

#line 2217
                                break;
                            }

#line 2217
                            bool _S36 = c_1 == 0U;

#line 2217
                            if(!_S36)
                            {

#line 2217
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2217
                            }
                            else
                            {

#line 2217
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2217
                            }

#line 2217
                            j_1 = 0U;

#line 2217
                            for(;;)
                            {

#line 2217
                                if(j_1 < 8U)
                                {
                                }
                                else
                                {

#line 2217
                                    break;
                                }

#line 2217
                                stgPut_0(j_1 * 64U + (&kernelContext_2)->_tid_0, r_3[c_1 * 8U + j_1], &kernelContext_2);

#line 2217
                                j_1 = j_1 + 1U;

#line 2217
                            }

#line 2217
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2217
                            d_2 = 0U;

#line 2217
                            for(;;)
                            {

#line 2217
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2217
                                    break;
                                }

#line 2217
                                uint pz_1 = computeWant_0(d_2, 4U, 64U, 0U, 0U, per_2, _S32, 4U, 0U, 0U);

#line 2217
                                uint _S37 = pz_1 & _S14;

#line 2217
                                uint iz_1 = _S37 >> lgTB_1;

#line 2217
                                uint az_1 = iz_1 * 64U + ((pz_1 >> _S12) << lgTB_1) + (_S37 & spanMask_1);

#line 2217
                                uint i_4 = _S34 + iz_1;

#line 2217
                                uint _S38 = c_1 * 8U;

#line 2217
                                if(i_4 >= _S38)
                                {

#line 2217
                                    _S15 = i_4 < ((c_1 + 1U) * 8U);

#line 2217
                                }
                                else
                                {

#line 2217
                                    _S15 = false;

#line 2217
                                }

#line 2217
                                if(_S15)
                                {

#line 2217
                                    float2 _S39 = stgGet_0(_S35 + az_1 - _S38 * 64U, &kernelContext_2);

#line 2217
                                    out_1[d_2] = _S39;

#line 2217
                                }

#line 2217
                                d_2 = d_2 + 1U;

#line 2217
                            }

#line 2217
                            c_1 = c_1 + 1U;

#line 2217
                        }

#line 2217
                        d_2 = 0U;

#line 2217
                        for(;;)
                        {

#line 2217
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2217
                                break;
                            }

#line 2217
                            r_3[d_2] = out_1[d_2];

#line 2217
                            d_2 = d_2 + 1U;

#line 2217
                        }

#line 2217
                        break;
                    }

#line 2217
                    break;
                }

#line 2217
                break;
            }

#line 2217
            break;
        }

#line 2217
        innermost_0(&r_3);

#line 2217
        break;
    }

#line 2217
    j_1 = 0U;
    for(;;)
    {

#line 2218
        if(j_1 < 16U)
        {
        }
        else
        {

#line 2218
            break;
        }

#line 2218
        *((&kernelContext_2)->entryPointParams_spectra_0+(_S17 * 2097152U + slotToIndex_0(tid_0 * 16U + j_1) * 2048U + _S18)) = packed_float2(float2(r_3[j_1].x, - r_3[j_1].y)) ;

#line 2218
        j_1 = j_1 + 1U;

#line 2218
    }



    return;
}
