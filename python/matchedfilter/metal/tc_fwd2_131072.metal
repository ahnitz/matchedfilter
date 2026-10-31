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


#line 576 "tc_fwd2_131072.slang"
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


#line 612
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_1 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_1 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_1 = float2(0.0f, 1.0f);
    float2 W6_1 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_1 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 619
    uint n1_1 = 0U;
    for(;;)
    {

#line 620
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 620
            break;
        }

#line 620
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 620
        n1_1 = n1_1 + 1U;

#line 620
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 621
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 621
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 622
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 622
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 623
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 623
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 623
    uint k2_1 = 0U;
    for(;;)
    {

#line 624
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 624
            break;
        }

#line 624
        uint _S7 = 4U * k2_1;

#line 624
        r4_0(&(*r_1)[_S7], &(*r_1)[_S7 + 1U], &(*r_1)[_S7 + 2U], &(*r_1)[_S7 + 3U]);

#line 624
        k2_1 = k2_1 + 1U;

#line 624
    }

    float2 t_6 = (*r_1)[int(1)];

#line 626
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 626
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 627
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 627
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 628
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 628
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 629
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 629
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 630
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 630
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 631
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 631
    (*r_1)[int(14)] = t_11;
    return;
}


#line 101 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 318 "tc_fwd2_131072.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S8 = max(TB_0, 1U);

#line 320
    uint j_0 = d_1 / _S8;

#line 320
    uint m_0 = d_1 % _S8;

#line 320
    uint _S9;
    if(TB_0 <= 16U)
    {

#line 321
        _S9 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 321
    }
    else
    {

#line 321
        _S9 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 321
    }

#line 321
    return _S9;
}


#line 305
struct KernelContext_0
{
    packed_float2 device* entryPointParams_scratch_0;
    packed_float2 device* entryPointParams_spectra_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(512)> threadgroup* stg_0;
};


#line 305
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 305
    uint _S10 = 2U * i_0;

#line 305
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S10] = (as_type<uint>((v_0.x)));

#line 305
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S10 + 1U] = (as_type<uint>((v_0.y)));

#line 305
    return;
}


#line 306
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 306
    uint _S11 = 2U * i_1;

#line 306
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S11]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S11 + 1U]))));
}


#line 715
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 722
    dft16_1(r_2);

#line 727
    return;
}


#line 862
uint lgOf_0(uint i_2)
{

#line 862
    uint _S12;

#line 862
    if(i_2 < 1U)
    {

#line 862
        _S12 = 4U;

#line 862
    }
    else
    {

#line 862
        if(i_2 == 1U)
        {

#line 862
            _S12 = 4U;

#line 862
        }
        else
        {

#line 862
            _S12 = 1U;

#line 862
        }

#line 862
    }

#line 862
    return _S12;
}


#line 864
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 868
    uint lg_1 = lgOf_0(0U);

#line 873
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 2155
[[kernel]] void tcForwardStage3(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], packed_float2 device* entryPointParams_scratch_1 [[buffer(0)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(1)]])
{

#line 2155
    uint j_1;

#line 2155
    uint d_2;

#line 2155
    thread KernelContext_0 kernelContext_2;

#line 2155
    (&kernelContext_2)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 2155
    (&kernelContext_2)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 2155
    threadgroup array<uint, int(512)> stg_1;

#line 2155
    (&kernelContext_2)->stg_0 = &stg_1;



    uint _S13 = gid_0.x;

#line 2159
    uint _S14 = _S13 / 512U;

#line 2159
    uint _S15 = _S13 % 512U;
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_3;

#line 2163
    uint m_1 = 0U;
    for(;;)
    {

#line 2164
        if(m_1 < 16U)
        {
        }
        else
        {

#line 2164
            break;
        }

#line 2165
        r_3[m_1] = float2(*((&kernelContext_2)->entryPointParams_scratch_0+(_S14 * 131072U + _S15 * 256U + tid_0 + 16U * m_1))) ;

#line 2164
        m_1 = m_1 + 1U;

#line 2164
    }

    for(;;)
    {

#line 2166
        for(;;)
        {

#line 2166
            for(;;)
            {

#line 2166
                for(;;)
                {

#line 2166
                    uint lgTB_0 = firstbithigh_0(16U);

#line 2166
                    uint lgLn_0 = firstbithigh_0(256U);

#line 2166
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2166
                    uint lane_1 = tid_0 & 15U;

#line 2166
                    dft16_0(&r_3);

#line 2166
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 256.0f);

#line 2166
                    float _S16 = tw_0.x;

#line 2166
                    float _S17 = tw_0.y;

#line 2166
                    uint k2_2 = 0U;

#line 2166
                    float cr_0 = 1.0f;

#line 2166
                    float ci_0 = 0.0f;

#line 2166
                    for(;;)
                    {

#line 2166
                        if(k2_2 < 16U)
                        {
                        }
                        else
                        {

#line 2166
                            break;
                        }

#line 2166
                        r_3[k2_2] = cmul_0(r_3[k2_2], float2(cr_0, ci_0));

#line 2166
                        float nr_0 = cr_0 * _S16 - ci_0 * _S17;

#line 2166
                        float _S18 = cr_0 * _S17 + ci_0 * _S16;

#line 2166
                        k2_2 = k2_2 + 1U;

#line 2166
                        cr_0 = nr_0;

#line 2166
                        ci_0 = _S18;

#line 2166
                    }

#line 2166
                    uint per_1 = 16U / max(16U, 1U);

#line 2166
                    uint _S19 = max(1U, 1U);

#line 2166
                    uint blk2_1 = tid_0 / _S19;

#line 2166
                    uint lane2_1 = tid_0 % _S19;

#line 2166
                    for(;;)
                    {

#line 2166
                        thread array<float2, int(16)> out_0;

#line 2166
                        uint z_0 = 0U;

#line 2166
                        for(;;)
                        {

#line 2166
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2166
                                break;
                            }

#line 2166
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2166
                            z_0 = z_0 + 1U;

#line 2166
                        }

#line 2166
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2166
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2166
                        uint p0_0 = computeWant_0(0U, 16U, 256U, blk_1, lane_1, per_1, _S19, 16U, blk2_1, lane2_1);

#line 2166
                        uint _S20 = p0_0 & lenMask_0;

#line 2166
                        uint _S21 = (_S20 >> lgTB_0) * 16U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S20 & spanMask_0);

#line 2166
                        uint c_1 = 0U;

#line 2166
                        for(;;)
                        {

#line 2166
                            if(c_1 < 1U)
                            {
                            }
                            else
                            {

#line 2166
                                break;
                            }

#line 2166
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2166
                            j_1 = 0U;

#line 2166
                            for(;;)
                            {

#line 2166
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 2166
                                    break;
                                }

#line 2166
                                stgPut_0(j_1 * 16U + (&kernelContext_2)->_tid_0, r_3[c_1 * 16U + j_1], &kernelContext_2);

#line 2166
                                j_1 = j_1 + 1U;

#line 2166
                            }

#line 2166
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2166
                            d_2 = 0U;

#line 2166
                            for(;;)
                            {

#line 2166
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2166
                                    break;
                                }

#line 2166
                                uint pz_0 = computeWant_0(d_2, 16U, 256U, 0U, 0U, per_1, _S19, 16U, 0U, 0U);

#line 2166
                                uint _S22 = pz_0 & lenMask_0;

#line 2166
                                uint az_0 = (_S22 >> lgTB_0) * 16U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S22 & spanMask_0);

#line 2166
                                float2 _S23 = stgGet_0(_S21 + az_0 - c_1 * 16U * 16U, &kernelContext_2);

#line 2166
                                out_0[d_2] = _S23;

#line 2166
                                d_2 = d_2 + 1U;

#line 2166
                            }

#line 2166
                            c_1 = c_1 + 1U;

#line 2166
                        }

#line 2166
                        j_1 = 0U;

#line 2166
                        for(;;)
                        {

#line 2166
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2166
                                break;
                            }

#line 2166
                            r_3[j_1] = out_0[j_1];

#line 2166
                            j_1 = j_1 + 1U;

#line 2166
                        }

#line 2166
                        break;
                    }

#line 2166
                    break;
                }

#line 2166
                break;
            }

#line 2166
            break;
        }

#line 2166
        innermost_0(&r_3);

#line 2166
        break;
    }

#line 2166
    d_2 = 0U;
    for(;;)
    {

#line 2167
        if(d_2 < 16U)
        {
        }
        else
        {

#line 2167
            break;
        }

#line 2167
        *((&kernelContext_2)->entryPointParams_spectra_0+(_S14 * 131072U + slotToIndex_0(tid_0 * 16U + d_2) * 512U + _S15)) = packed_float2(float2(r_3[d_2].x, - r_3[d_2].y)) ;

#line 2167
        d_2 = d_2 + 1U;

#line 2167
    }



    return;
}
