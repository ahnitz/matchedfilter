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


#line 173 "mm_16384_fullCorrelationSeries_lds32.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 173
    return float2(*(b_0+i_0)) ;
}


#line 323
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 323
    float _S2 = a_0.x;

#line 323
    float _S3 = b_1.x;

#line 323
    float _S4 = a_0.y;

#line 323
    float _S5 = b_1.y;

#line 323
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 582
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 584
    float2 t1_0 = *a_1 - *c_0;

#line 584
    float2 t2_0 = *b_2 + *d_0;

#line 584
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 586
    *b_2 = t1_0 + j3_0;

#line 586
    *c_0 = t0_0 - t2_0;

#line 586
    *d_0 = t1_0 - j3_0;
    return;
}


#line 322
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 322
    float _S6 = a_2.x;

#line 322
    float _S7 = b_3.x;

#line 322
    float _S8 = a_2.y;

#line 322
    float _S9 = b_3.y;

#line 322
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 618
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 625
    uint n1_0 = 0U;
    for(;;)
    {

#line 626
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 626
            break;
        }

#line 626
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 626
        n1_0 = n1_0 + 1U;

#line 626
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 627
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 627
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 628
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 628
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 629
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 629
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 629
    uint k2_0 = 0U;
    for(;;)
    {

#line 630
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 630
            break;
        }

#line 630
        uint _S10 = 4U * k2_0;

#line 630
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 630
        k2_0 = k2_0 + 1U;

#line 630
    }

    float2 t_0 = (*r_0)[int(1)];

#line 632
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 632
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 633
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 633
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 634
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 634
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 635
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 635
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 636
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 636
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 637
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 637
    (*r_0)[int(14)] = t_5;
    return;
}


#line 74 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S11 = ((MF_ACCURATE_TRIG));

#line 77
    return _S11;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S12 = mfAccurateTrigFlag_0();

#line 103
    if(_S12 == 0U)
    {

#line 104
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

#line 117
            return float2(- s_0, c_1);
        }
    case int(2):
        {

#line 118
            return float2(- c_1, - s_0);
        }
    case int(3):
        {

#line 119
            return float2(s_0, - c_1);
        }
    default:
        {

#line 120
            return float2(c_1, s_0);
        }
    }

#line 120
}


#line 324 "mm_16384_fullCorrelationSeries_lds32.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S14 = max(TB_0, 1U);

#line 326
    uint j_0 = d_1 / _S14;

#line 326
    uint m_0 = d_1 % _S14;

#line 326
    uint _S15;
    if(TB_0 <= 16U)
    {

#line 327
        _S15 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 327
    }
    else
    {

#line 327
        _S15 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 327
    }

#line 327
    return _S15;
}


#line 1827
struct EntryPointParams_0
{
    uint4 params_0;
};


#line 311
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 311
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 311
    uint _S16 = 2U * i_1;

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S16] = (as_type<uint>((v_0.x)));

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S16 + 1U] = (as_type<uint>((v_0.y)));

#line 311
    return;
}


#line 312
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 312
    uint _S17 = 2U * i_2;

#line 312
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S17]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S17 + 1U]))));
}


#line 597
void dft4_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    r4_0(&(*r_1)[o_0], &(*r_1)[o_0 + 1U], &(*r_1)[o_0 + 2U], &(*r_1)[o_0 + 3U]);
    float2 t_6 = (*r_1)[o_0 + 1U];

#line 600
    (*r_1)[o_0 + 1U] = (*r_1)[o_0 + 2U];

#line 600
    (*r_1)[o_0 + 2U] = t_6;
    return;
}


#line 721
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 721
    uint b_4 = 0U;

#line 730
    for(;;)
    {

#line 730
        if(b_4 < 4U)
        {
        }
        else
        {

#line 730
            break;
        }

#line 730
        dft4_0(r_2, b_4 * 4U);

#line 730
        b_4 = b_4 + 1U;

#line 730
    }


    return;
}


#line 868
uint lgOf_0(uint i_3)
{

#line 868
    uint _S18;

#line 868
    if(i_3 < 3U)
    {

#line 868
        _S18 = 4U;

#line 868
    }
    else
    {

#line 868
        _S18 = 1U;

#line 868
    }

#line 868
    return _S18;
}


#line 870
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(4U);

    uint x_1 = slot_0 >> lg_0;

#line 874
    uint lg_1 = lgOf_0(3U);

    uint x_2 = x_1 >> lg_1;

#line 874
    uint lg_2 = lgOf_0(2U);

    uint x_3 = x_2 >> lg_2;

#line 874
    uint lg_3 = lgOf_0(1U);

#line 874
    uint lg_4 = lgOf_0(0U);

#line 879
    return (((((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | (x_2 & ((1U << lg_2) - 1U))) << lg_3) | (x_3 & ((1U << lg_3) - 1U))) << lg_4) | ((x_3 >> lg_3) & ((1U << lg_4) - 1U));
}


#line 1827
[[kernel]] void fullCorrelationSeries(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], uint device* entryPointParams_starts_1 [[buffer(3)]], packed_float2 device* entryPointParams_output_1 [[buffer(4)]])
{

#line 1827
    uint _S19;

#line 1827
    uint k2_1;

#line 1827
    float cr_0;

#line 1827
    float ci_0;

#line 1827
    uint _S20;

#line 1827
    uint z_1;

#line 1827
    uint _S21;

#line 1827
    uint c_2;

#line 1827
    uint d_2;

#line 1827
    uint j_1;

#line 1827
    bool _S22;

#line 1827
    uint _S23;

#line 1827
    uint _S24;

#line 1827
    uint _S25;

#line 1827
    thread KernelContext_0 kernelContext_2;

#line 1827
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 1827
    (&kernelContext_2)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1827
    (&kernelContext_2)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1827
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1827
    (&kernelContext_2)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1827
    threadgroup array<uint, int(8192)> stg_1;

#line 1827
    (&kernelContext_2)->stg_0 = &stg_1;

#line 1832
    uint pair_0 = gid_0.x;

#line 1832
    uint tid_0 = lid_0.x;
    uint d_3 = pair_0 / entryPointParams_1->params_0.x;

#line 1833
    uint _S26 = pair_0 % entryPointParams_1->params_0.x;
    uint _S27 = (&kernelContext_2)->entryPointParams_starts_0[d_3];
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_3;

#line 1837
    uint i_4 = 0U;
    for(;;)
    {

#line 1838
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1838
            break;
        }

#line 1839
        uint idx_0 = tid_0 + 1024U * i_4;
        r_3[i_4] = cmulConj_0(cload_0((&kernelContext_2)->entryPointParams_data_0, d_3 * 16384U + idx_0), cload_0((&kernelContext_2)->entryPointParams_tmpl_0, _S26 * 16384U + idx_0));

#line 1838
        i_4 = i_4 + 1U;

#line 1838
    }



    for(;;)
    {

#line 1842
        for(;;)
        {

#line 1842
            for(;;)
            {

#line 1842
                for(;;)
                {

#line 1842
                    uint lgTB_0 = firstbithigh_0(1024U);

#line 1842
                    _S19 = lgTB_0;

#line 1842
                    uint lgLn_0 = firstbithigh_0(16384U);

#line 1842
                    uint blk_1 = tid_0 >> lgTB_0;

#line 1842
                    uint lane_1 = tid_0 & 1023U;

#line 1842
                    dft16_0(&r_3);

#line 1842
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 16384.0f);

#line 1842
                    float _S28 = tw_0.x;

#line 1842
                    float _S29 = tw_0.y;

#line 1842
                    k2_1 = 0U;

#line 1842
                    cr_0 = 1.0f;

#line 1842
                    ci_0 = 0.0f;

#line 1842
                    for(;;)
                    {

#line 1842
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 1842
                            break;
                        }

#line 1842
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 1842
                        float nr_0 = cr_0 * _S28 - ci_0 * _S29;

#line 1842
                        float _S30 = cr_0 * _S29 + ci_0 * _S28;

#line 1842
                        k2_1 = k2_1 + 1U;

#line 1842
                        cr_0 = nr_0;

#line 1842
                        ci_0 = _S30;

#line 1842
                    }

#line 1842
                    uint per_1 = 16U / max(1024U, 1U);

#line 1842
                    uint _S31 = max(64U, 1U);

#line 1842
                    _S20 = _S31;

#line 1842
                    uint blk2_1 = tid_0 / _S31;

#line 1842
                    uint lane2_1 = tid_0 % _S31;

#line 1842
                    for(;;)
                    {

#line 1842
                        thread array<float2, int(16)> out_0;

#line 1842
                        z_1 = 0U;

#line 1842
                        for(;;)
                        {

#line 1842
                            if(z_1 < 16U)
                            {
                            }
                            else
                            {

#line 1842
                                break;
                            }

#line 1842
                            out_0[z_1] = float2(0.0f, 0.0f);

#line 1842
                            z_1 = z_1 + 1U;

#line 1842
                        }

#line 1842
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 1842
                        _S21 = spanMask_0;

#line 1842
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1842
                        uint p0_0 = computeWant_0(0U, 1024U, 16384U, blk_1, lane_1, per_1, _S31, 1024U, blk2_1, lane2_1);

#line 1842
                        uint _S32 = p0_0 & lenMask_0;

#line 1842
                        uint _S33 = _S32 >> lgTB_0;

#line 1842
                        uint _S34 = _S33 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S32 & spanMask_0);

#line 1842
                        c_2 = 0U;

#line 1842
                        for(;;)
                        {

#line 1842
                            if(c_2 < 4U)
                            {
                            }
                            else
                            {

#line 1842
                                break;
                            }

#line 1842
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1842
                            j_1 = 0U;

#line 1842
                            for(;;)
                            {

#line 1842
                                if(j_1 < 4U)
                                {
                                }
                                else
                                {

#line 1842
                                    break;
                                }

#line 1842
                                stgPut_0(j_1 * 1024U + (&kernelContext_2)->_tid_0, r_3[c_2 * 4U + j_1], &kernelContext_2);

#line 1842
                                j_1 = j_1 + 1U;

#line 1842
                            }

#line 1842
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1842
                            d_2 = 0U;

#line 1842
                            for(;;)
                            {

#line 1842
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 1842
                                    break;
                                }

#line 1842
                                uint pz_0 = computeWant_0(d_2, 1024U, 16384U, 0U, 0U, per_1, _S31, 1024U, 0U, 0U);

#line 1842
                                uint _S35 = pz_0 & lenMask_0;

#line 1842
                                uint iz_0 = _S35 >> lgTB_0;

#line 1842
                                uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S35 & spanMask_0);

#line 1842
                                uint i_5 = _S33 + iz_0;

#line 1842
                                uint _S36 = c_2 * 4U;

#line 1842
                                if(i_5 >= _S36)
                                {

#line 1842
                                    _S22 = i_5 < ((c_2 + 1U) * 4U);

#line 1842
                                }
                                else
                                {

#line 1842
                                    _S22 = false;

#line 1842
                                }

#line 1842
                                if(_S22)
                                {

#line 1842
                                    float2 _S37 = stgGet_0(_S34 + az_0 - _S36 * 1024U, &kernelContext_2);

#line 1842
                                    out_0[d_2] = _S37;

#line 1842
                                }

#line 1842
                                d_2 = d_2 + 1U;

#line 1842
                            }

#line 1842
                            c_2 = c_2 + 1U;

#line 1842
                        }

#line 1842
                        d_2 = 0U;

#line 1842
                        for(;;)
                        {

#line 1842
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 1842
                                break;
                            }

#line 1842
                            r_3[d_2] = out_0[d_2];

#line 1842
                            d_2 = d_2 + 1U;

#line 1842
                        }

#line 1842
                        break;
                    }

#line 1842
                    break;
                }

#line 1842
                break;
            }

#line 1842
            for(;;)
            {

#line 1842
                for(;;)
                {

#line 1842
                    uint lgTB_1 = firstbithigh_0(64U);

#line 1842
                    _S23 = lgTB_1;

#line 1842
                    uint blk_2 = tid_0 >> lgTB_1;

#line 1842
                    uint lane_2 = tid_0 & 63U;

#line 1842
                    dft16_0(&r_3);

#line 1842
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 1842
                    float _S38 = tw_1.x;

#line 1842
                    float _S39 = tw_1.y;

#line 1842
                    k2_1 = 0U;

#line 1842
                    cr_0 = 1.0f;

#line 1842
                    ci_0 = 0.0f;

#line 1842
                    for(;;)
                    {

#line 1842
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 1842
                            break;
                        }

#line 1842
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 1842
                        float nr_1 = cr_0 * _S38 - ci_0 * _S39;

#line 1842
                        float _S40 = cr_0 * _S39 + ci_0 * _S38;

#line 1842
                        k2_1 = k2_1 + 1U;

#line 1842
                        cr_0 = nr_1;

#line 1842
                        ci_0 = _S40;

#line 1842
                    }

#line 1842
                    uint per_2 = 16U / _S20;

#line 1842
                    uint _S41 = max(4U, 1U);

#line 1842
                    _S24 = _S41;

#line 1842
                    uint blk2_2 = tid_0 / _S41;

#line 1842
                    uint lane2_2 = tid_0 % _S41;

#line 1842
                    for(;;)
                    {

#line 1842
                        thread array<float2, int(16)> out_1;

#line 1842
                        z_1 = 0U;

#line 1842
                        for(;;)
                        {

#line 1842
                            if(z_1 < 16U)
                            {
                            }
                            else
                            {

#line 1842
                                break;
                            }

#line 1842
                            out_1[z_1] = float2(0.0f, 0.0f);

#line 1842
                            z_1 = z_1 + 1U;

#line 1842
                        }

#line 1842
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 1842
                        _S25 = spanMask_1;

#line 1842
                        uint p0_1 = computeWant_0(0U, 64U, 1024U, blk_2, lane_2, per_2, _S41, 64U, blk2_2, lane2_2);

#line 1842
                        uint _S42 = p0_1 & _S21;

#line 1842
                        uint _S43 = _S42 >> lgTB_1;

#line 1842
                        uint _S44 = _S43 * 1024U + ((p0_1 >> _S19) << lgTB_1) + (_S42 & spanMask_1);

#line 1842
                        c_2 = 0U;

#line 1842
                        for(;;)
                        {

#line 1842
                            if(c_2 < 4U)
                            {
                            }
                            else
                            {

#line 1842
                                break;
                            }

#line 1842
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1842
                            j_1 = 0U;

#line 1842
                            for(;;)
                            {

#line 1842
                                if(j_1 < 4U)
                                {
                                }
                                else
                                {

#line 1842
                                    break;
                                }

#line 1842
                                stgPut_0(j_1 * 1024U + (&kernelContext_2)->_tid_0, r_3[c_2 * 4U + j_1], &kernelContext_2);

#line 1842
                                j_1 = j_1 + 1U;

#line 1842
                            }

#line 1842
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1842
                            d_2 = 0U;

#line 1842
                            for(;;)
                            {

#line 1842
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 1842
                                    break;
                                }

#line 1842
                                uint pz_1 = computeWant_0(d_2, 64U, 1024U, 0U, 0U, per_2, _S41, 64U, 0U, 0U);

#line 1842
                                uint _S45 = pz_1 & _S21;

#line 1842
                                uint iz_1 = _S45 >> lgTB_1;

#line 1842
                                uint az_1 = iz_1 * 1024U + ((pz_1 >> _S19) << lgTB_1) + (_S45 & spanMask_1);

#line 1842
                                uint i_6 = _S43 + iz_1;

#line 1842
                                uint _S46 = c_2 * 4U;

#line 1842
                                if(i_6 >= _S46)
                                {

#line 1842
                                    _S22 = i_6 < ((c_2 + 1U) * 4U);

#line 1842
                                }
                                else
                                {

#line 1842
                                    _S22 = false;

#line 1842
                                }

#line 1842
                                if(_S22)
                                {

#line 1842
                                    float2 _S47 = stgGet_0(_S44 + az_1 - _S46 * 1024U, &kernelContext_2);

#line 1842
                                    out_1[d_2] = _S47;

#line 1842
                                }

#line 1842
                                d_2 = d_2 + 1U;

#line 1842
                            }

#line 1842
                            c_2 = c_2 + 1U;

#line 1842
                        }

#line 1842
                        d_2 = 0U;

#line 1842
                        for(;;)
                        {

#line 1842
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 1842
                                break;
                            }

#line 1842
                            r_3[d_2] = out_1[d_2];

#line 1842
                            d_2 = d_2 + 1U;

#line 1842
                        }

#line 1842
                        break;
                    }

#line 1842
                    break;
                }

#line 1842
                break;
            }

#line 1842
            for(;;)
            {

#line 1842
                for(;;)
                {

#line 1842
                    uint lgTB_2 = firstbithigh_0(4U);

#line 1842
                    uint blk_3 = tid_0 >> lgTB_2;

#line 1842
                    uint lane_3 = tid_0 & 3U;

#line 1842
                    dft16_0(&r_3);

#line 1842
                    float2 tw_2 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 64.0f);

#line 1842
                    float _S48 = tw_2.x;

#line 1842
                    float _S49 = tw_2.y;

#line 1842
                    k2_1 = 0U;

#line 1842
                    cr_0 = 1.0f;

#line 1842
                    ci_0 = 0.0f;

#line 1842
                    for(;;)
                    {

#line 1842
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 1842
                            break;
                        }

#line 1842
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 1842
                        float nr_2 = cr_0 * _S48 - ci_0 * _S49;

#line 1842
                        float _S50 = cr_0 * _S49 + ci_0 * _S48;

#line 1842
                        k2_1 = k2_1 + 1U;

#line 1842
                        cr_0 = nr_2;

#line 1842
                        ci_0 = _S50;

#line 1842
                    }

#line 1842
                    uint per_3 = 16U / _S24;

#line 1842
                    uint _S51 = max(0U, 1U);

#line 1842
                    uint blk2_3 = tid_0 / _S51;

#line 1842
                    uint lane2_3 = tid_0 % _S51;

#line 1842
                    for(;;)
                    {

#line 1842
                        thread array<float2, int(16)> out_2;

#line 1842
                        z_1 = 0U;

#line 1842
                        for(;;)
                        {

#line 1842
                            if(z_1 < 16U)
                            {
                            }
                            else
                            {

#line 1842
                                break;
                            }

#line 1842
                            out_2[z_1] = float2(0.0f, 0.0f);

#line 1842
                            z_1 = z_1 + 1U;

#line 1842
                        }

#line 1842
                        uint spanMask_2 = (1U << lgTB_2) - 1U;

#line 1842
                        uint p0_2 = computeWant_0(0U, 4U, 64U, blk_3, lane_3, per_3, _S51, 4U, blk2_3, lane2_3);

#line 1842
                        uint _S52 = p0_2 & _S25;

#line 1842
                        uint _S53 = _S52 >> lgTB_2;

#line 1842
                        uint _S54 = _S53 * 1024U + ((p0_2 >> _S23) << lgTB_2) + (_S52 & spanMask_2);

#line 1842
                        c_2 = 0U;

#line 1842
                        for(;;)
                        {

#line 1842
                            if(c_2 < 4U)
                            {
                            }
                            else
                            {

#line 1842
                                break;
                            }

#line 1842
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1842
                            j_1 = 0U;

#line 1842
                            for(;;)
                            {

#line 1842
                                if(j_1 < 4U)
                                {
                                }
                                else
                                {

#line 1842
                                    break;
                                }

#line 1842
                                stgPut_0(j_1 * 1024U + (&kernelContext_2)->_tid_0, r_3[c_2 * 4U + j_1], &kernelContext_2);

#line 1842
                                j_1 = j_1 + 1U;

#line 1842
                            }

#line 1842
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1842
                            d_2 = 0U;

#line 1842
                            for(;;)
                            {

#line 1842
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 1842
                                    break;
                                }

#line 1842
                                uint pz_2 = computeWant_0(d_2, 4U, 64U, 0U, 0U, per_3, _S51, 4U, 0U, 0U);

#line 1842
                                uint _S55 = pz_2 & _S25;

#line 1842
                                uint iz_2 = _S55 >> lgTB_2;

#line 1842
                                uint az_2 = iz_2 * 1024U + ((pz_2 >> _S23) << lgTB_2) + (_S55 & spanMask_2);

#line 1842
                                uint i_7 = _S53 + iz_2;

#line 1842
                                uint _S56 = c_2 * 4U;

#line 1842
                                if(i_7 >= _S56)
                                {

#line 1842
                                    _S22 = i_7 < ((c_2 + 1U) * 4U);

#line 1842
                                }
                                else
                                {

#line 1842
                                    _S22 = false;

#line 1842
                                }

#line 1842
                                if(_S22)
                                {

#line 1842
                                    float2 _S57 = stgGet_0(_S54 + az_2 - _S56 * 1024U, &kernelContext_2);

#line 1842
                                    out_2[d_2] = _S57;

#line 1842
                                }

#line 1842
                                d_2 = d_2 + 1U;

#line 1842
                            }

#line 1842
                            c_2 = c_2 + 1U;

#line 1842
                        }

#line 1842
                        d_2 = 0U;

#line 1842
                        for(;;)
                        {

#line 1842
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 1842
                                break;
                            }

#line 1842
                            r_3[d_2] = out_2[d_2];

#line 1842
                            d_2 = d_2 + 1U;

#line 1842
                        }

#line 1842
                        break;
                    }

#line 1842
                    break;
                }

#line 1842
                break;
            }

#line 1842
            break;
        }

#line 1842
        innermost_0(&r_3);

#line 1842
        break;
    }

#line 1842
    i_4 = 0U;
    for(;;)
    {

#line 1843
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1843
            break;
        }

#line 1844
        uint lag_0 = slotToIndex_0(tid_0 * 16U + i_4);
        if(lag_0 >= (entryPointParams_1->params_0.z))
        {

#line 1845
            _S22 = lag_0 < (entryPointParams_1->params_0.w);

#line 1845
        }
        else
        {

#line 1845
            _S22 = false;

#line 1845
        }

#line 1845
        bool _S58;

#line 1845
        if(_S22)
        {

#line 1845
            _S58 = lag_0 < (entryPointParams_1->params_0.y - _S27);

#line 1845
        }
        else
        {

#line 1845
            _S58 = false;

#line 1845
        }

#line 1845
        if(_S58)
        {

#line 1845
            *((&kernelContext_2)->entryPointParams_output_0+(_S26 * entryPointParams_1->params_0.y + _S27 + lag_0)) = packed_float2(float2(r_3[i_4].x, r_3[i_4].y)) ;

#line 1845
        }

#line 1843
        i_4 = i_4 + 1U;

#line 1843
    }

#line 1848
    return;
}
