#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
#ifndef MF_ACCURATE_TRIG
#define MF_ACCURATE_TRIG 0u
#endif

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


#line 173 "mm_2048_fullCorrelationSeries.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 173
    return float2(*(b_0+i_0)) ;
}


#line 329
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 329
    float _S2 = a_0.x;

#line 329
    float _S3 = b_1.x;

#line 329
    float _S4 = a_0.y;

#line 329
    float _S5 = b_1.y;

#line 329
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 615
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 617
    float2 t1_0 = *a_1 - *c_0;

#line 617
    float2 t2_0 = *b_2 + *d_0;

#line 617
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 619
    *b_2 = t1_0 + j3_0;

#line 619
    *c_0 = t0_0 - t2_0;

#line 619
    *d_0 = t1_0 - j3_0;
    return;
}


#line 328
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 328
    float _S6 = a_2.x;

#line 328
    float _S7 = b_3.x;

#line 328
    float _S8 = a_2.y;

#line 328
    float _S9 = b_3.y;

#line 328
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 651
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 658
    uint n1_0 = 0U;
    for(;;)
    {

#line 659
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 659
            break;
        }

#line 659
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 659
        n1_0 = n1_0 + 1U;

#line 659
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 660
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 660
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 661
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 661
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 662
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 662
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 662
    uint k2_0 = 0U;
    for(;;)
    {

#line 663
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 663
            break;
        }

#line 663
        uint _S10 = 4U * k2_0;

#line 663
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 663
        k2_0 = k2_0 + 1U;

#line 663
    }

    float2 t_0 = (*r_0)[int(1)];

#line 665
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 665
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 666
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 666
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 667
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 667
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 668
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 668
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 669
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 669
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 670
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 670
    (*r_0)[int(14)] = t_5;
    return;
}


#line 76 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S11 = ((MF_ACCURATE_TRIG));

#line 79
    return _S11;
}


#line 103
float2 mfTwiddle_0(float angle_0)
{

#line 81
    uint _S12 = mfAccurateTrigFlag_0();

#line 105
    if(_S12 == 0U)
    {

#line 106
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S13 = float(quadrant_0);
    float x_0 = angle_0 - _S13 * 1.57079625129699707f - _S13 * 7.54978941586159635e-08f;
    float z_0 = x_0 * x_0;
    float c_1 = 1.0f + z_0 * (-0.5f + z_0 * (0.0416666679084301f + z_0 * (-0.00138888892251998f + z_0 * (0.00002480158764229f + z_0 * -2.75573199814971304e-07f))));

    float s_0 = x_0 * (1.0f + z_0 * (-0.1666666716337204f + z_0 * (0.00833333376795053f + z_0 * (-0.0001984127011383f + z_0 * (2.75573188446287531e-06f + z_0 * -2.50521079436794025e-08f)))));


    switch(quadrant_0 & int(3))
    {
    case int(1):
        {

#line 119
            return float2(- s_0, c_1);
        }
    case int(2):
        {

#line 120
            return float2(- c_1, - s_0);
        }
    case int(3):
        {

#line 121
            return float2(s_0, - c_1);
        }
    default:
        {

#line 122
            return float2(c_1, s_0);
        }
    }

#line 122
}


#line 330 "mm_2048_fullCorrelationSeries.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S14 = max(TB_0, 1U);

#line 332
    uint j_0 = d_1 / _S14;

#line 332
    uint m_0 = d_1 % _S14;

#line 332
    uint _S15;
    if(TB_0 <= 16U)
    {

#line 333
        _S15 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 333
    }
    else
    {

#line 333
        _S15 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 333
    }

#line 333
    return _S15;
}


#line 1917
struct EntryPointParams_0
{
    uint4 params_0;
};


#line 317
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(4096)> threadgroup* stg_0;
};


#line 317
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 317
    uint _S16 = 2U * i_1;

#line 317
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S16] = (as_type<uint>((v_0.x)));

#line 317
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S16 + 1U] = (as_type<uint>((v_0.y)));

#line 317
    return;
}


#line 318
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 318
    uint _S17 = 2U * i_2;

#line 318
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S17]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S17 + 1U]))));
}


#line 635
void dft8_0(array<float2, int(16)> thread* r_1, uint o_0)
{


    thread array<float2, int(8)> b_4;

#line 639
    uint s_1 = 1U;
    for(;;)
    {

#line 640
        if(s_1 < 8U)
        {
        }
        else
        {

#line 640
            break;
        }

#line 640
        uint j_1 = 0U;
        for(;;)
        {

#line 641
            if(j_1 < 4U)
            {
            }
            else
            {

#line 641
                break;
            }

#line 642
            uint k_0 = j_1 & (s_1 - 1U);

#line 642
            uint base_0 = (j_1 - k_0) << 1U;

            float2 w_0 = mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_1));
            uint _S18 = o_0 + j_1;

#line 645
            float2 t_6 = cmul_0(w_0, (*r_1)[_S18 + 4U]);
            uint _S19 = base_0 + k_0;

#line 646
            b_4[_S19] = (*r_1)[_S18] + t_6;

#line 646
            b_4[_S19 + s_1] = (*r_1)[_S18] - t_6;

#line 641
            j_1 = j_1 + 1U;

#line 641
        }

#line 641
        uint i_3 = 0U;

#line 648
        for(;;)
        {

#line 648
            if(i_3 < 8U)
            {
            }
            else
            {

#line 648
                break;
            }

#line 648
            (*r_1)[o_0 + i_3] = b_4[i_3];

#line 648
            i_3 = i_3 + 1U;

#line 648
        }

#line 640
        s_1 = s_1 << 1U;

#line 640
    }

#line 650
    return;
}


#line 754
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 754
    uint b_5 = 0U;

#line 762
    for(;;)
    {

#line 762
        if(b_5 < 2U)
        {
        }
        else
        {

#line 762
            break;
        }

#line 762
        dft8_0(r_2, b_5 * 8U);

#line 762
        b_5 = b_5 + 1U;

#line 762
    }



    return;
}


#line 882
uint lgOf_0(uint i_4)
{

#line 882
    uint _S20;

#line 882
    if(i_4 < 2U)
    {

#line 882
        _S20 = 4U;

#line 882
    }
    else
    {

#line 882
        if(i_4 == 2U)
        {

#line 882
            _S20 = 3U;

#line 882
        }
        else
        {

#line 882
            _S20 = 1U;

#line 882
        }

#line 882
    }

#line 882
    return _S20;
}


#line 884
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 888
    uint lg_1 = lgOf_0(1U);

#line 888
    uint lg_2 = lgOf_0(0U);

#line 893
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1917
[[kernel]] void fullCorrelationSeries(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], uint device* entryPointParams_starts_1 [[buffer(3)]], packed_float2 device* entryPointParams_output_1 [[buffer(4)]])
{

#line 1917
    uint _S21;

#line 1917
    uint k2_1;

#line 1917
    float cr_0;

#line 1917
    float ci_0;

#line 1917
    uint _S22;

#line 1917
    uint z_1;

#line 1917
    uint _S23;

#line 1917
    uint c_2;

#line 1917
    uint d_2;

#line 1917
    uint j_2;

#line 1917
    thread KernelContext_0 kernelContext_2;

#line 1917
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 1917
    (&kernelContext_2)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1917
    (&kernelContext_2)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1917
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1917
    (&kernelContext_2)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1917
    threadgroup array<uint, int(4096)> stg_1;

#line 1917
    (&kernelContext_2)->stg_0 = &stg_1;

#line 1922
    uint pair_0 = gid_0.x;

#line 1922
    uint tid_0 = lid_0.x;
    uint d_3 = pair_0 / entryPointParams_1->params_0.x;

#line 1923
    uint _S24 = pair_0 % entryPointParams_1->params_0.x;
    uint _S25 = (&kernelContext_2)->entryPointParams_starts_0[d_3];
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_3;

#line 1927
    uint i_5 = 0U;
    for(;;)
    {

#line 1928
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1928
            break;
        }

#line 1929
        uint idx_0 = tid_0 + 128U * i_5;
        r_3[i_5] = cmulConj_0(cload_0((&kernelContext_2)->entryPointParams_data_0, d_3 * 2048U + idx_0), cload_0((&kernelContext_2)->entryPointParams_tmpl_0, _S24 * 2048U + idx_0));

#line 1928
        i_5 = i_5 + 1U;

#line 1928
    }



    for(;;)
    {

#line 1932
        for(;;)
        {

#line 1932
            for(;;)
            {

#line 1932
                for(;;)
                {

#line 1932
                    uint lgTB_0 = firstbithigh_0(128U);

#line 1932
                    _S21 = lgTB_0;

#line 1932
                    uint lgLn_0 = firstbithigh_0(2048U);

#line 1932
                    uint blk_1 = tid_0 >> lgTB_0;

#line 1932
                    uint lane_1 = tid_0 & 127U;

#line 1932
                    dft16_0(&r_3);

#line 1932
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 2048.0f);

#line 1932
                    float _S26 = tw_0.x;

#line 1932
                    float _S27 = tw_0.y;

#line 1932
                    k2_1 = 0U;

#line 1932
                    cr_0 = 1.0f;

#line 1932
                    ci_0 = 0.0f;

#line 1932
                    for(;;)
                    {

#line 1932
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 1932
                            break;
                        }

#line 1932
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 1932
                        float nr_0 = cr_0 * _S26 - ci_0 * _S27;

#line 1932
                        float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 1932
                        k2_1 = k2_1 + 1U;

#line 1932
                        cr_0 = nr_0;

#line 1932
                        ci_0 = _S28;

#line 1932
                    }

#line 1932
                    uint per_1 = 16U / max(128U, 1U);

#line 1932
                    uint _S29 = max(8U, 1U);

#line 1932
                    _S22 = _S29;

#line 1932
                    uint blk2_1 = tid_0 / _S29;

#line 1932
                    uint lane2_1 = tid_0 % _S29;

#line 1932
                    for(;;)
                    {

#line 1932
                        thread array<float2, int(16)> out_0;

#line 1932
                        z_1 = 0U;

#line 1932
                        for(;;)
                        {

#line 1932
                            if(z_1 < 16U)
                            {
                            }
                            else
                            {

#line 1932
                                break;
                            }

#line 1932
                            out_0[z_1] = float2(0.0f, 0.0f);

#line 1932
                            z_1 = z_1 + 1U;

#line 1932
                        }

#line 1932
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 1932
                        _S23 = spanMask_0;

#line 1932
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1932
                        uint p0_0 = computeWant_0(0U, 128U, 2048U, blk_1, lane_1, per_1, _S29, 128U, blk2_1, lane2_1);

#line 1932
                        uint _S30 = p0_0 & lenMask_0;

#line 1932
                        uint _S31 = (_S30 >> lgTB_0) * 128U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S30 & spanMask_0);

#line 1932
                        c_2 = 0U;

#line 1932
                        for(;;)
                        {

#line 1932
                            if(c_2 < 1U)
                            {
                            }
                            else
                            {

#line 1932
                                break;
                            }

#line 1932
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1932
                            j_2 = 0U;

#line 1932
                            for(;;)
                            {

#line 1932
                                if(j_2 < 16U)
                                {
                                }
                                else
                                {

#line 1932
                                    break;
                                }

#line 1932
                                stgPut_0(j_2 * 128U + (&kernelContext_2)->_tid_0, r_3[c_2 * 16U + j_2], &kernelContext_2);

#line 1932
                                j_2 = j_2 + 1U;

#line 1932
                            }

#line 1932
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1932
                            d_2 = 0U;

#line 1932
                            for(;;)
                            {

#line 1932
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 1932
                                    break;
                                }

#line 1932
                                uint pz_0 = computeWant_0(d_2, 128U, 2048U, 0U, 0U, per_1, _S29, 128U, 0U, 0U);

#line 1932
                                uint _S32 = pz_0 & lenMask_0;

#line 1932
                                uint az_0 = (_S32 >> lgTB_0) * 128U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S32 & spanMask_0);

#line 1932
                                float2 _S33 = stgGet_0(_S31 + az_0 - c_2 * 16U * 128U, &kernelContext_2);

#line 1932
                                out_0[d_2] = _S33;

#line 1932
                                d_2 = d_2 + 1U;

#line 1932
                            }

#line 1932
                            c_2 = c_2 + 1U;

#line 1932
                        }

#line 1932
                        d_2 = 0U;

#line 1932
                        for(;;)
                        {

#line 1932
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 1932
                                break;
                            }

#line 1932
                            r_3[d_2] = out_0[d_2];

#line 1932
                            d_2 = d_2 + 1U;

#line 1932
                        }

#line 1932
                        break;
                    }

#line 1932
                    break;
                }

#line 1932
                break;
            }

#line 1932
            for(;;)
            {

#line 1932
                for(;;)
                {

#line 1932
                    uint lgTB_1 = firstbithigh_0(8U);

#line 1932
                    uint blk_2 = tid_0 >> lgTB_1;

#line 1932
                    uint lane_2 = tid_0 & 7U;

#line 1932
                    dft16_0(&r_3);

#line 1932
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 128.0f);

#line 1932
                    float _S34 = tw_1.x;

#line 1932
                    float _S35 = tw_1.y;

#line 1932
                    k2_1 = 0U;

#line 1932
                    cr_0 = 1.0f;

#line 1932
                    ci_0 = 0.0f;

#line 1932
                    for(;;)
                    {

#line 1932
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 1932
                            break;
                        }

#line 1932
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 1932
                        float nr_1 = cr_0 * _S34 - ci_0 * _S35;

#line 1932
                        float _S36 = cr_0 * _S35 + ci_0 * _S34;

#line 1932
                        k2_1 = k2_1 + 1U;

#line 1932
                        cr_0 = nr_1;

#line 1932
                        ci_0 = _S36;

#line 1932
                    }

#line 1932
                    uint per_2 = 16U / _S22;

#line 1932
                    uint _S37 = max(0U, 1U);

#line 1932
                    uint blk2_2 = tid_0 / _S37;

#line 1932
                    uint lane2_2 = tid_0 % _S37;

#line 1932
                    for(;;)
                    {

#line 1932
                        thread array<float2, int(16)> out_1;

#line 1932
                        z_1 = 0U;

#line 1932
                        for(;;)
                        {

#line 1932
                            if(z_1 < 16U)
                            {
                            }
                            else
                            {

#line 1932
                                break;
                            }

#line 1932
                            out_1[z_1] = float2(0.0f, 0.0f);

#line 1932
                            z_1 = z_1 + 1U;

#line 1932
                        }

#line 1932
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 1932
                        uint p0_1 = computeWant_0(0U, 8U, 128U, blk_2, lane_2, per_2, _S37, 8U, blk2_2, lane2_2);

#line 1932
                        uint _S38 = p0_1 & _S23;

#line 1932
                        uint _S39 = (_S38 >> lgTB_1) * 128U + ((p0_1 >> _S21) << lgTB_1) + (_S38 & spanMask_1);

#line 1932
                        c_2 = 0U;

#line 1932
                        for(;;)
                        {

#line 1932
                            if(c_2 < 1U)
                            {
                            }
                            else
                            {

#line 1932
                                break;
                            }

#line 1932
                            bool _S40 = c_2 == 0U;

#line 1932
                            if(!_S40)
                            {

#line 1932
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1932
                            }
                            else
                            {

#line 1932
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1932
                            }

#line 1932
                            j_2 = 0U;

#line 1932
                            for(;;)
                            {

#line 1932
                                if(j_2 < 16U)
                                {
                                }
                                else
                                {

#line 1932
                                    break;
                                }

#line 1932
                                stgPut_0(j_2 * 128U + (&kernelContext_2)->_tid_0, r_3[c_2 * 16U + j_2], &kernelContext_2);

#line 1932
                                j_2 = j_2 + 1U;

#line 1932
                            }

#line 1932
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1932
                            d_2 = 0U;

#line 1932
                            for(;;)
                            {

#line 1932
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 1932
                                    break;
                                }

#line 1932
                                uint pz_1 = computeWant_0(d_2, 8U, 128U, 0U, 0U, per_2, _S37, 8U, 0U, 0U);

#line 1932
                                uint _S41 = pz_1 & _S23;

#line 1932
                                uint az_1 = (_S41 >> lgTB_1) * 128U + ((pz_1 >> _S21) << lgTB_1) + (_S41 & spanMask_1);

#line 1932
                                float2 _S42 = stgGet_0(_S39 + az_1 - c_2 * 16U * 128U, &kernelContext_2);

#line 1932
                                out_1[d_2] = _S42;

#line 1932
                                d_2 = d_2 + 1U;

#line 1932
                            }

#line 1932
                            c_2 = c_2 + 1U;

#line 1932
                        }

#line 1932
                        d_2 = 0U;

#line 1932
                        for(;;)
                        {

#line 1932
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 1932
                                break;
                            }

#line 1932
                            r_3[d_2] = out_1[d_2];

#line 1932
                            d_2 = d_2 + 1U;

#line 1932
                        }

#line 1932
                        break;
                    }

#line 1932
                    break;
                }

#line 1932
                break;
            }

#line 1932
            break;
        }

#line 1932
        innermost_0(&r_3);

#line 1932
        break;
    }

#line 1932
    i_5 = 0U;
    for(;;)
    {

#line 1933
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1933
            break;
        }

#line 1934
        uint lag_0 = slotToIndex_0(tid_0 * 16U + i_5);

#line 1934
        bool _S43;
        if(lag_0 >= (entryPointParams_1->params_0.z))
        {

#line 1935
            _S43 = lag_0 < (entryPointParams_1->params_0.w);

#line 1935
        }
        else
        {

#line 1935
            _S43 = false;

#line 1935
        }

#line 1935
        bool _S44;

#line 1935
        if(_S43)
        {

#line 1935
            _S44 = lag_0 < (entryPointParams_1->params_0.y - _S25);

#line 1935
        }
        else
        {

#line 1935
            _S44 = false;

#line 1935
        }

#line 1935
        if(_S44)
        {

#line 1935
            *((&kernelContext_2)->entryPointParams_output_0+(_S24 * entryPointParams_1->params_0.y + _S25 + lag_0)) = packed_float2(float2(r_3[i_5].x, r_3[i_5].y)) ;

#line 1935
        }

#line 1933
        i_5 = i_5 + 1U;

#line 1933
    }

#line 1938
    return;
}
