#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
#ifndef MF_DATA_STRIDE
#define MF_DATA_STRIDE 0u
#endif
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


#line 58 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S2 = ((MF_DATA_STRIDE));

#line 61
    return _S2;
}


#line 174 "mm_64_refineItems.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 174
    return float2(*(b_0+i_0)) ;
}


#line 324
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 324
    float _S3 = a_0.x;

#line 324
    float _S4 = b_1.x;

#line 324
    float _S5 = a_0.y;

#line 324
    float _S6 = b_1.y;

#line 324
    return float2(_S3 * _S4 + _S5 * _S6, _S5 * _S4 - _S3 * _S6);
}


#line 583
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 585
    float2 t1_0 = *a_1 - *c_0;

#line 585
    float2 t2_0 = *b_2 + *d_0;

#line 585
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 587
    *b_2 = t1_0 + j3_0;

#line 587
    *c_0 = t0_0 - t2_0;

#line 587
    *d_0 = t1_0 - j3_0;
    return;
}


#line 323
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 323
    float _S7 = a_2.x;

#line 323
    float _S8 = b_3.x;

#line 323
    float _S9 = a_2.y;

#line 323
    float _S10 = b_3.y;

#line 323
    return float2(_S7 * _S8 - _S9 * _S10, _S7 * _S10 + _S9 * _S8);
}


#line 619
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 626
    uint n1_0 = 0U;
    for(;;)
    {

#line 627
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 627
            break;
        }

#line 627
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 627
        n1_0 = n1_0 + 1U;

#line 627
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 628
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 628
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 629
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 629
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 630
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 630
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 630
    uint k2_0 = 0U;
    for(;;)
    {

#line 631
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 631
            break;
        }

#line 631
        uint _S11 = 4U * k2_0;

#line 631
        r4_0(&(*r_0)[_S11], &(*r_0)[_S11 + 1U], &(*r_0)[_S11 + 2U], &(*r_0)[_S11 + 3U]);

#line 631
        k2_0 = k2_0 + 1U;

#line 631
    }

    float2 t_0 = (*r_0)[int(1)];

#line 633
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 633
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 634
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 634
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 635
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 635
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 636
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 636
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 637
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 637
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 638
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 638
    (*r_0)[int(14)] = t_5;
    return;
}


#line 74 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S12 = ((MF_ACCURATE_TRIG));

#line 77
    return _S12;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S13 = mfAccurateTrigFlag_0();

#line 103
    if(_S13 == 0U)
    {

#line 104
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S14 = float(quadrant_0);
    float x_0 = angle_0 - _S14 * 1.57079625129699707f - _S14 * 7.54978941586159635e-08f;
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


#line 325 "mm_64_refineItems.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S15 = max(TB_0, 1U);

#line 327
    uint j_0 = d_1 / _S15;

#line 327
    uint m_0 = d_1 % _S15;

#line 327
    uint _S16;
    if(TB_0 <= 16U)
    {

#line 328
        _S16 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 328
    }
    else
    {

#line 328
        _S16 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 328
    }

#line 328
    return _S16;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
    uint binsize_0;
    int binShift_0;
    uint nbins_0;
    uint thrBits_0;
    uint gridSize_0;
};


#line 312 "mm_64_refineItems.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_items_0;
    uint device* entryPointParams_count_0;
    uint _stgBase_0;
    uint _binPhase_0;
    uint _tid_0;
    array<uint, int(128)> threadgroup* stg_0;
};


#line 312
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 312
    uint _S17 = 2U * i_1;

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S17] = (as_type<uint>((v_0.x)));

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S17 + 1U] = (as_type<uint>((v_0.y)));

#line 312
    return;
}


#line 313
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 313
    uint _S18 = 2U * i_2;

#line 313
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S18]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S18 + 1U]))));
}


#line 598
void dft4_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    r4_0(&(*r_1)[o_0], &(*r_1)[o_0 + 1U], &(*r_1)[o_0 + 2U], &(*r_1)[o_0 + 3U]);
    float2 t_6 = (*r_1)[o_0 + 1U];

#line 601
    (*r_1)[o_0 + 1U] = (*r_1)[o_0 + 2U];

#line 601
    (*r_1)[o_0 + 2U] = t_6;
    return;
}


#line 722
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 722
    uint b_4 = 0U;

#line 731
    for(;;)
    {

#line 731
        if(b_4 < 4U)
        {
        }
        else
        {

#line 731
            break;
        }

#line 731
        dft4_0(r_2, b_4 * 4U);

#line 731
        b_4 = b_4 + 1U;

#line 731
    }


    return;
}


#line 869
uint lgOf_0(uint i_3)
{

#line 869
    uint _S19;

#line 869
    if(i_3 < 1U)
    {

#line 869
        _S19 = 4U;

#line 869
    }
    else
    {

#line 869
        _S19 = 1U;

#line 869
    }

#line 869
    return _S19;
}


#line 871
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 875
    uint lg_1 = lgOf_0(1U);

#line 875
    uint lg_2 = lgOf_0(0U);

#line 880
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2221
[[kernel]] void refineItems(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_items_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]])
{

#line 2221
    uint k2_1;

#line 2221
    uint j_1;

#line 2221
    uint d_2;

#line 2221
    uint m0_0;

#line 2221
    uint s0_0;

#line 2221
    uint m1_0;

#line 2221
    bool _S20;

#line 2221
    bool _S21;

#line 2221
    bool _S22;

#line 2221
    bool _S23;

#line 2221
    bool _S24;

#line 2221
    bool _S25;

#line 2221
    bool _S26;

#line 2221
    thread KernelContext_0 kernelContext_2;

#line 2221
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2221
    (&kernelContext_2)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2221
    (&kernelContext_2)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2221
    (&kernelContext_2)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2221
    (&kernelContext_2)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2221
    (&kernelContext_2)->entryPointParams_items_0 = entryPointParams_items_1;

#line 2221
    (&kernelContext_2)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2221
    threadgroup array<uint, int(128)> stg_1;

#line 2221
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2221
    (&kernelContext_2)->_binPhase_0 = 0U;

#line 2230
    uint _S27 = entryPointParams_count_1[int(0)];

#line 2230
    uint i_4 = gid_0.x;
    for(;;)
    {

#line 2231
        if(i_4 < _S27)
        {
        }
        else
        {

#line 2231
            break;
        }

#line 2232
        (&kernelContext_2)->_stgBase_0 = 0U;
        uint _S28 = 6U * i_4;

#line 2233
        uint d_3 = (&kernelContext_2)->entryPointParams_items_0[_S28];

#line 2233
        uint t_7 = (&kernelContext_2)->entryPointParams_items_0[_S28 + 1U];
        (&kernelContext_2)->_binPhase_0 = (&kernelContext_2)->entryPointParams_items_0[_S28 + 5U];
        uint _S29 = d_3 * (&kernelContext_2)->entryPointParams_0->ntmpl_0 + t_7;

#line 2235
        uint _S30 = (&kernelContext_2)->entryPointParams_items_0[_S28 + 4U];

#line 2235
        uint _S31 = lid_0.x;
        uint _S32 = (&kernelContext_2)->entryPointParams_items_0[_S28 + 2U];

#line 2236
        uint _S33 = (&kernelContext_2)->entryPointParams_items_0[_S28 + 3U];

#line 2236
        uint _S34 = (&kernelContext_2)->entryPointParams_0->ntmpl_0;

#line 2236
        uint _S35 = (&kernelContext_2)->entryPointParams_0->binsize_0;

#line 2236
        int _S36 = (&kernelContext_2)->entryPointParams_0->binShift_0;

#line 2236
        uint _S37 = (&kernelContext_2)->entryPointParams_0->nbins_0;

#line 2236
        uint _S38 = (&kernelContext_2)->entryPointParams_0->thrBits_0;

#line 2235
        for(;;)
        {

#line 2235
            (&kernelContext_2)->_tid_0 = _S31;

#line 2235
            uint _S39 = _S29 / _S34;

#line 2235
            uint _S40 = _S29 % _S34;

#line 2235
            thread array<float2, int(16)> r_3;

#line 2235
            uint n2_0 = 0U;

#line 2235
            for(;;)
            {

#line 2235
                if(n2_0 < 16U)
                {
                }
                else
                {

#line 2235
                    break;
                }

#line 2235
                uint idx_0 = _S31 + 4U * n2_0;

#line 2235
                uint _S41 = mfDataStrideFlag_0();

#line 2235
                if(_S41 != 0U)
                {

#line 2235
                    uint _S42 = mfDataStrideFlag_0();

#line 2235
                    k2_1 = _S42;

#line 2235
                }
                else
                {

#line 2235
                    k2_1 = 64U;

#line 2235
                }

#line 2235
                r_3[n2_0] = cmulConj_0(cload_0((&kernelContext_2)->entryPointParams_data_0, _S39 * k2_1 + idx_0), cload_0((&kernelContext_2)->entryPointParams_tmpl_0, _S40 * 64U + idx_0));

#line 2235
                n2_0 = n2_0 + 1U;

#line 2235
            }

#line 2235
            for(;;)
            {

#line 2235
                for(;;)
                {

#line 2235
                    for(;;)
                    {

#line 2235
                        for(;;)
                        {

#line 2235
                            uint lgTB_0 = firstbithigh_0(4U);

#line 2235
                            uint lgLn_0 = firstbithigh_0(64U);

#line 2235
                            uint blk_1 = _S31 >> lgTB_0;

#line 2235
                            uint lane_1 = _S31 & 3U;

#line 2235
                            dft16_0(&r_3);

#line 2235
                            float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 64.0f);

#line 2235
                            float _S43 = tw_0.x;

#line 2235
                            float _S44 = tw_0.y;

#line 2235
                            k2_1 = 0U;

#line 2235
                            float cr_0 = 1.0f;

#line 2235
                            float ci_0 = 0.0f;

#line 2235
                            for(;;)
                            {

#line 2235
                                if(k2_1 < 16U)
                                {
                                }
                                else
                                {

#line 2235
                                    break;
                                }

#line 2235
                                r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2235
                                float nr_0 = cr_0 * _S43 - ci_0 * _S44;

#line 2235
                                float _S45 = cr_0 * _S44 + ci_0 * _S43;

#line 2235
                                k2_1 = k2_1 + 1U;

#line 2235
                                cr_0 = nr_0;

#line 2235
                                ci_0 = _S45;

#line 2235
                            }

#line 2235
                            uint per_1 = 16U / max(4U, 1U);

#line 2235
                            uint _S46 = max(0U, 1U);

#line 2235
                            uint blk2_1 = _S31 / _S46;

#line 2235
                            uint lane2_1 = _S31 % _S46;

#line 2235
                            for(;;)
                            {

#line 2235
                                thread array<float2, int(16)> out_0;

#line 2235
                                uint z_1 = 0U;

#line 2235
                                for(;;)
                                {

#line 2235
                                    if(z_1 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2235
                                        break;
                                    }

#line 2235
                                    out_0[z_1] = float2(0.0f, 0.0f);

#line 2235
                                    z_1 = z_1 + 1U;

#line 2235
                                }

#line 2235
                                uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2235
                                uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2235
                                uint p0_0 = computeWant_0(0U, 4U, 64U, blk_1, lane_1, per_1, _S46, 4U, blk2_1, lane2_1);

#line 2235
                                uint _S47 = p0_0 & lenMask_0;

#line 2235
                                uint _S48 = (_S47 >> lgTB_0) * 4U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S47 & spanMask_0);

#line 2235
                                uint c_2 = 0U;

#line 2235
                                for(;;)
                                {

#line 2235
                                    if(c_2 < 1U)
                                    {
                                    }
                                    else
                                    {

#line 2235
                                        break;
                                    }

#line 2235
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                                    j_1 = 0U;

#line 2235
                                    for(;;)
                                    {

#line 2235
                                        if(j_1 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2235
                                            break;
                                        }

#line 2235
                                        stgPut_0(j_1 * 4U + (&kernelContext_2)->_tid_0, r_3[c_2 * 16U + j_1], &kernelContext_2);

#line 2235
                                        j_1 = j_1 + 1U;

#line 2235
                                    }

#line 2235
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                                    d_2 = 0U;

#line 2235
                                    for(;;)
                                    {

#line 2235
                                        if(d_2 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2235
                                            break;
                                        }

#line 2235
                                        uint pz_0 = computeWant_0(d_2, 4U, 64U, 0U, 0U, per_1, _S46, 4U, 0U, 0U);

#line 2235
                                        uint _S49 = pz_0 & lenMask_0;

#line 2235
                                        uint az_0 = (_S49 >> lgTB_0) * 4U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S49 & spanMask_0);

#line 2235
                                        float2 _S50 = stgGet_0(_S48 + az_0 - c_2 * 16U * 4U, &kernelContext_2);

#line 2235
                                        out_0[d_2] = _S50;

#line 2235
                                        d_2 = d_2 + 1U;

#line 2235
                                    }

#line 2235
                                    c_2 = c_2 + 1U;

#line 2235
                                }

#line 2235
                                j_1 = 0U;

#line 2235
                                for(;;)
                                {

#line 2235
                                    if(j_1 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2235
                                        break;
                                    }

#line 2235
                                    r_3[j_1] = out_0[j_1];

#line 2235
                                    j_1 = j_1 + 1U;

#line 2235
                                }

#line 2235
                                break;
                            }

#line 2235
                            break;
                        }

#line 2235
                        break;
                    }

#line 2235
                    break;
                }

#line 2235
                innermost_0(&r_3);

#line 2235
                break;
            }

#line 2235
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
            uint s0_1;

#line 2235
            uint m1_1;

#line 2235
            uint s1_0;

#line 2235
            uint i_5;

#line 2235
            uint m2_0;

#line 2235
            uint s2_0;

#line 2235
            uint m3_0;

#line 2235
            uint s3_0;

#line 2235
            uint b_5;

#line 2235
            bool isCand_0;

#line 2235
            if(_S37 <= 4U)
            {

#line 2235
                if(_S31 < 4U)
                {

#line 2235
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + _S31] = _S38;

#line 2235
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U + _S31] = 4294967295U;

#line 2235
                }

#line 2235
                float2 _S51 = float2(0.0f, 0.0f);

#line 2235
                i_5 = 0U;

#line 2235
                d_2 = _S38;

#line 2235
                s0_1 = 4294967295U;

#line 2235
                float2 v0_0 = _S51;

#line 2235
                m1_1 = _S38;

#line 2235
                s1_0 = 4294967295U;

#line 2235
                float2 v1_0 = _S51;

#line 2235
                m2_0 = _S38;

#line 2235
                s2_0 = 4294967295U;

#line 2235
                float2 v2_0 = _S51;

#line 2235
                m3_0 = _S38;

#line 2235
                s3_0 = 4294967295U;

#line 2235
                float2 v3_0 = _S51;

#line 2235
                for(;;)
                {

#line 2235
                    if(i_5 < 16U)
                    {
                    }
                    else
                    {

#line 2235
                        break;
                    }

#line 2235
                    uint slot_1 = _S31 * 16U + i_5;

#line 2235
                    uint idx_1 = slotToIndex_0(slot_1);

#line 2235
                    if(idx_1 >= _S32)
                    {

#line 2235
                        isCand_0 = idx_1 < _S33;

#line 2235
                    }
                    else
                    {

#line 2235
                        isCand_0 = false;

#line 2235
                    }

#line 2235
                    if(isCand_0)
                    {

#line 2235
                        float rx_0 = r_3[i_5].x;

#line 2235
                        float ry_0 = r_3[i_5].y;

#line 2235
                        uint mag_0 = (as_type<uint>((rx_0 * rx_0 + ry_0 * ry_0)));

#line 2235
                        uint off_0 = idx_1 - _S32 + (&kernelContext_2)->_binPhase_0;

#line 2235
                        if(_S37 == 1U)
                        {

#line 2235
                            b_5 = 0U;

#line 2235
                        }
                        else
                        {

#line 2235
                            if(_S36 >= int(0))
                            {

#line 2235
                                b_5 = off_0 >> uint(_S36);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S52 = off_0 / _S35;

#line 2235
                                b_5 = _S52;

#line 2235
                            }

#line 2235
                        }

#line 2235
                        if(b_5 == 0U)
                        {

#line 2235
                            _S20 = mag_0 > d_2;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S20 = false;

#line 2235
                        }

#line 2235
                        float2 v0_1;

#line 2235
                        if(_S20)
                        {

#line 2235
                            float2 _S53 = float2(rx_0, ry_0);

#line 2235
                            m0_0 = mag_0;

#line 2235
                            s0_0 = slot_1;

#line 2235
                            v0_1 = _S53;

#line 2235
                        }
                        else
                        {

#line 2235
                            m0_0 = d_2;

#line 2235
                            s0_0 = s0_1;

#line 2235
                            v0_1 = v0_0;

#line 2235
                        }

#line 2235
                        if(_S37 >= 2U)
                        {

#line 2235
                            _S21 = b_5 == 1U;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S21 = false;

#line 2235
                        }

#line 2235
                        if(_S21)
                        {

#line 2235
                            _S22 = mag_0 > m1_1;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S22 = false;

#line 2235
                        }

#line 2235
                        uint s1_1;

#line 2235
                        float2 v1_1;

#line 2235
                        if(_S22)
                        {

#line 2235
                            float2 _S54 = float2(rx_0, ry_0);

#line 2235
                            m1_0 = mag_0;

#line 2235
                            s1_1 = slot_1;

#line 2235
                            v1_1 = _S54;

#line 2235
                        }
                        else
                        {

#line 2235
                            m1_0 = m1_1;

#line 2235
                            s1_1 = s1_0;

#line 2235
                            v1_1 = v1_0;

#line 2235
                        }

#line 2235
                        if(_S37 >= 3U)
                        {

#line 2235
                            _S23 = b_5 == 2U;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S23 = false;

#line 2235
                        }

#line 2235
                        if(_S23)
                        {

#line 2235
                            _S24 = mag_0 > m2_0;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S24 = false;

#line 2235
                        }

#line 2235
                        uint m2_1;

#line 2235
                        uint s2_1;

#line 2235
                        float2 v2_1;

#line 2235
                        if(_S24)
                        {

#line 2235
                            float2 _S55 = float2(rx_0, ry_0);

#line 2235
                            m2_1 = mag_0;

#line 2235
                            s2_1 = slot_1;

#line 2235
                            v2_1 = _S55;

#line 2235
                        }
                        else
                        {

#line 2235
                            m2_1 = m2_0;

#line 2235
                            s2_1 = s2_0;

#line 2235
                            v2_1 = v2_0;

#line 2235
                        }

#line 2235
                        if(_S37 >= 4U)
                        {

#line 2235
                            _S25 = b_5 == 3U;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S25 = false;

#line 2235
                        }

#line 2235
                        if(_S25)
                        {

#line 2235
                            _S26 = mag_0 > m3_0;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S26 = false;

#line 2235
                        }

#line 2235
                        uint m3_1;

#line 2235
                        uint s3_1;

#line 2235
                        float2 v3_1;

#line 2235
                        if(_S26)
                        {

#line 2235
                            float2 _S56 = float2(rx_0, ry_0);

#line 2235
                            m3_1 = mag_0;

#line 2235
                            s3_1 = slot_1;

#line 2235
                            v3_1 = _S56;

#line 2235
                        }
                        else
                        {

#line 2235
                            m3_1 = m3_0;

#line 2235
                            s3_1 = s3_0;

#line 2235
                            v3_1 = v3_0;

#line 2235
                        }

#line 2235
                        d_2 = m0_0;

#line 2235
                        m1_1 = m1_0;

#line 2235
                        m2_0 = m2_1;

#line 2235
                        m3_0 = m3_1;

#line 2235
                        s0_1 = s0_0;

#line 2235
                        s1_0 = s1_1;

#line 2235
                        s2_0 = s2_1;

#line 2235
                        s3_0 = s3_1;

#line 2235
                        v0_0 = v0_1;

#line 2235
                        v1_0 = v1_1;

#line 2235
                        v2_0 = v2_1;

#line 2235
                        v3_0 = v3_1;

#line 2235
                    }

#line 2235
                    i_5 = i_5 + 1U;

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                uint wm0_0 = simd_max(d_2);

#line 2235
                bool _S57 = simd_is_first();

#line 2235
                if(_S57)
                {

#line 2235
                    isCand_0 = wm0_0 > _S38;

#line 2235
                }
                else
                {

#line 2235
                    isCand_0 = false;

#line 2235
                }

#line 2235
                if(isCand_0)
                {

#line 2235
                    uint _S58 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0])), wm0_0, memory_order_relaxed);

#line 2235
                }

#line 2235
                bool _S59 = _S37 >= 2U;

#line 2235
                if(_S59)
                {

#line 2235
                    uint wm1_0 = simd_max(m1_1);

#line 2235
                    bool _S60 = simd_is_first();

#line 2235
                    if(_S60)
                    {

#line 2235
                        _S20 = wm1_0 > _S38;

#line 2235
                    }
                    else
                    {

#line 2235
                        _S20 = false;

#line 2235
                    }

#line 2235
                    if(_S20)
                    {

#line 2235
                        uint _S61 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 1U])), wm1_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                bool _S62 = _S37 >= 3U;

#line 2235
                if(_S62)
                {

#line 2235
                    uint wm2_0 = simd_max(m2_0);

#line 2235
                    bool _S63 = simd_is_first();

#line 2235
                    if(_S63)
                    {

#line 2235
                        _S20 = wm2_0 > _S38;

#line 2235
                    }
                    else
                    {

#line 2235
                        _S20 = false;

#line 2235
                    }

#line 2235
                    if(_S20)
                    {

#line 2235
                        uint _S64 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 2U])), wm2_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                bool _S65 = _S37 >= 4U;

#line 2235
                if(_S65)
                {

#line 2235
                    uint wm3_0 = simd_max(m3_0);

#line 2235
                    bool _S66 = simd_is_first();

#line 2235
                    if(_S66)
                    {

#line 2235
                        _S20 = wm3_0 > _S38;

#line 2235
                    }
                    else
                    {

#line 2235
                        _S20 = false;

#line 2235
                    }

#line 2235
                    if(_S20)
                    {

#line 2235
                        uint _S67 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 3U])), wm3_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                if(s0_1 != 4294967295U)
                {

#line 2235
                    _S20 = d_2 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0];

#line 2235
                }
                else
                {

#line 2235
                    _S20 = false;

#line 2235
                }

#line 2235
                if(_S20)
                {

#line 2235
                    b_5 = s0_1;

#line 2235
                }
                else
                {

#line 2235
                    b_5 = 4294967295U;

#line 2235
                }

#line 2235
                if(_S59)
                {

#line 2235
                    _S21 = s1_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S21 = false;

#line 2235
                }

#line 2235
                if(_S21)
                {

#line 2235
                    _S22 = m1_1 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 1U];

#line 2235
                }
                else
                {

#line 2235
                    _S22 = false;

#line 2235
                }

#line 2235
                if(_S22)
                {

#line 2235
                    m0_0 = s1_0;

#line 2235
                }
                else
                {

#line 2235
                    m0_0 = 4294967295U;

#line 2235
                }

#line 2235
                if(_S62)
                {

#line 2235
                    _S23 = s2_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S23 = false;

#line 2235
                }

#line 2235
                if(_S23)
                {

#line 2235
                    _S24 = m2_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 2U];

#line 2235
                }
                else
                {

#line 2235
                    _S24 = false;

#line 2235
                }

#line 2235
                if(_S24)
                {

#line 2235
                    s0_0 = s2_0;

#line 2235
                }
                else
                {

#line 2235
                    s0_0 = 4294967295U;

#line 2235
                }

#line 2235
                if(_S65)
                {

#line 2235
                    _S25 = s3_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S25 = false;

#line 2235
                }

#line 2235
                if(_S25)
                {

#line 2235
                    _S26 = m3_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 3U];

#line 2235
                }
                else
                {

#line 2235
                    _S26 = false;

#line 2235
                }

#line 2235
                if(_S26)
                {

#line 2235
                    m1_0 = s3_0;

#line 2235
                }
                else
                {

#line 2235
                    m1_0 = 4294967295U;

#line 2235
                }

#line 2235
                uint ww0_0 = simd_min(b_5);

#line 2235
                bool _S68 = simd_is_first();

#line 2235
                bool _S69;

#line 2235
                if(_S68)
                {

#line 2235
                    _S69 = ww0_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S69 = false;

#line 2235
                }

#line 2235
                if(_S69)
                {

#line 2235
                    uint _S70 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U])), ww0_0, memory_order_relaxed);

#line 2235
                }

#line 2235
                bool _S71;

#line 2235
                if(_S59)
                {

#line 2235
                    uint ww1_0 = simd_min(m0_0);

#line 2235
                    bool _S72 = simd_is_first();

#line 2235
                    if(_S72)
                    {

#line 2235
                        _S71 = ww1_0 != 4294967295U;

#line 2235
                    }
                    else
                    {

#line 2235
                        _S71 = false;

#line 2235
                    }

#line 2235
                    if(_S71)
                    {

#line 2235
                        uint _S73 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 5U])), ww1_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                if(_S62)
                {

#line 2235
                    uint ww2_0 = simd_min(s0_0);

#line 2235
                    bool _S74 = simd_is_first();

#line 2235
                    if(_S74)
                    {

#line 2235
                        _S71 = ww2_0 != 4294967295U;

#line 2235
                    }
                    else
                    {

#line 2235
                        _S71 = false;

#line 2235
                    }

#line 2235
                    if(_S71)
                    {

#line 2235
                        uint _S75 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 6U])), ww2_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                if(_S65)
                {

#line 2235
                    uint ww3_0 = simd_min(m1_0);

#line 2235
                    bool _S76 = simd_is_first();

#line 2235
                    if(_S76)
                    {

#line 2235
                        _S71 = ww3_0 != 4294967295U;

#line 2235
                    }
                    else
                    {

#line 2235
                        _S71 = false;

#line 2235
                    }

#line 2235
                    if(_S71)
                    {

#line 2235
                        uint _S77 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 7U])), ww3_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                uint baseOut_0 = _S30 * _S37;

#line 2235
                if(b_5 != 4294967295U)
                {

#line 2235
                    _S71 = b_5 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U];

#line 2235
                }
                else
                {

#line 2235
                    _S71 = false;

#line 2235
                }

#line 2235
                if(_S71)
                {

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+baseOut_0) = int(slotToIndex_0(b_5));

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+baseOut_0) = packed_float2(v0_0) ;

#line 2235
                }

#line 2235
                bool _S78;

#line 2235
                if(_S59)
                {

#line 2235
                    _S78 = m0_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S78 = false;

#line 2235
                }

#line 2235
                bool _S79;

#line 2235
                if(_S78)
                {

#line 2235
                    _S79 = m0_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 5U];

#line 2235
                }
                else
                {

#line 2235
                    _S79 = false;

#line 2235
                }

#line 2235
                if(_S79)
                {

#line 2235
                    uint _S80 = baseOut_0 + 1U;

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S80) = int(slotToIndex_0(m0_0));

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S80) = packed_float2(v1_0) ;

#line 2235
                }

#line 2235
                bool _S81;

#line 2235
                if(_S62)
                {

#line 2235
                    _S81 = s0_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S81 = false;

#line 2235
                }

#line 2235
                bool _S82;

#line 2235
                if(_S81)
                {

#line 2235
                    _S82 = s0_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 6U];

#line 2235
                }
                else
                {

#line 2235
                    _S82 = false;

#line 2235
                }

#line 2235
                if(_S82)
                {

#line 2235
                    uint _S83 = baseOut_0 + 2U;

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S83) = int(slotToIndex_0(s0_0));

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S83) = packed_float2(v2_0) ;

#line 2235
                }

#line 2235
                bool _S84;

#line 2235
                if(_S65)
                {

#line 2235
                    _S84 = m1_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S84 = false;

#line 2235
                }

#line 2235
                bool _S85;

#line 2235
                if(_S84)
                {

#line 2235
                    _S85 = m1_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 7U];

#line 2235
                }
                else
                {

#line 2235
                    _S85 = false;

#line 2235
                }

#line 2235
                if(_S85)
                {

#line 2235
                    uint _S86 = baseOut_0 + 3U;

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S86) = int(slotToIndex_0(m1_0));

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S86) = packed_float2(v3_0) ;

#line 2235
                }

#line 2235
                bool _S87;

#line 2235
                if(_S31 < _S37)
                {

#line 2235
                    _S87 = ((*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U + _S31]) == 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S87 = false;

#line 2235
                }

#line 2235
                if(_S87)
                {

#line 2235
                    uint _S88 = baseOut_0 + _S31;

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S88) = int(-1);

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S88) = packed_float2(_S51) ;

#line 2235
                }

#line 2235
            }
            else
            {

#line 2235
                d_2 = _S31;

#line 2235
                for(;;)
                {

#line 2235
                    if(d_2 < _S37)
                    {
                    }
                    else
                    {

#line 2235
                        break;
                    }

#line 2235
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + d_2] = _S38;

#line 2235
                    d_2 = d_2 + 4U;

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                s0_1 = 0U;

#line 2235
                m1_1 = 0U;

#line 2235
                s1_0 = 0U;

#line 2235
                for(;;)
                {

#line 2235
                    if(s0_1 < 16U)
                    {
                    }
                    else
                    {

#line 2235
                        break;
                    }

#line 2235
                    uint idx_2 = slotToIndex_0(_S31 * 16U + s0_1);

#line 2235
                    if(idx_2 >= _S32)
                    {

#line 2235
                        isCand_0 = idx_2 < _S33;

#line 2235
                    }
                    else
                    {

#line 2235
                        isCand_0 = false;

#line 2235
                    }

#line 2235
                    if(isCand_0)
                    {

#line 2235
                        float rx_1 = r_3[s0_1].x;

#line 2235
                        float ry_1 = r_3[s0_1].y;

#line 2235
                        uint mag_1 = (as_type<uint>((rx_1 * rx_1 + ry_1 * ry_1)));

#line 2235
                        if(mag_1 > _S38)
                        {

#line 2235
                            uint off_1 = idx_2 - _S32 + (&kernelContext_2)->_binPhase_0;

#line 2235
                            if(_S36 >= int(0))
                            {

#line 2235
                                m2_0 = off_1 >> uint(_S36);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S89 = off_1 / _S35;

#line 2235
                                m2_0 = _S89;

#line 2235
                            }

#line 2235
                            uint _S90 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0])), mag_1, memory_order_relaxed);

#line 2235
                            uint bit_0 = 1U << (s0_1 & 31U);

#line 2235
                            if(s0_1 < 32U)
                            {

#line 2235
                                i_5 = m1_1 | bit_0;

#line 2235
                                s2_0 = s1_0;

#line 2235
                            }
                            else
                            {

#line 2235
                                uint aboveHi_0 = s1_0 | bit_0;

#line 2235
                                i_5 = m1_1;

#line 2235
                                s2_0 = aboveHi_0;

#line 2235
                            }

#line 2235
                        }
                        else
                        {

#line 2235
                            i_5 = m1_1;

#line 2235
                            s2_0 = s1_0;

#line 2235
                        }

#line 2235
                    }
                    else
                    {

#line 2235
                        i_5 = m1_1;

#line 2235
                        s2_0 = s1_0;

#line 2235
                    }

#line 2235
                    s0_1 = s0_1 + 1U;

#line 2235
                    m1_1 = i_5;

#line 2235
                    s1_0 = s2_0;

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                if((m1_1 | s1_0) != 0U)
                {

#line 2235
                    i_5 = 0U;

#line 2235
                    m2_0 = 0U;

#line 2235
                    s2_0 = 0U;

#line 2235
                    for(;;)
                    {

#line 2235
                        if(i_5 < 16U)
                        {
                        }
                        else
                        {

#line 2235
                            break;
                        }

#line 2235
                        uint bit_1 = 1U << (i_5 & 31U);

#line 2235
                        bool _S91 = i_5 < 32U;

#line 2235
                        if(_S91)
                        {

#line 2235
                            isCand_0 = (m1_1 & bit_1) != 0U;

#line 2235
                        }
                        else
                        {

#line 2235
                            isCand_0 = (s1_0 & bit_1) != 0U;

#line 2235
                        }

#line 2235
                        if(isCand_0)
                        {

#line 2235
                            uint off_2 = slotToIndex_0(_S31 * 16U + i_5) - _S32 + (&kernelContext_2)->_binPhase_0;

#line 2235
                            if(_S36 >= int(0))
                            {

#line 2235
                                m3_0 = off_2 >> uint(_S36);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S92 = off_2 / _S35;

#line 2235
                                m3_0 = _S92;

#line 2235
                            }

#line 2235
                            float rx_2 = r_3[i_5].x;

#line 2235
                            float ry_2 = r_3[i_5].y;

#line 2235
                            if((as_type<uint>((rx_2 * rx_2 + ry_2 * ry_2))) == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m3_0])
                            {

#line 2235
                                if(_S91)
                                {

#line 2235
                                    s3_0 = m2_0 | bit_1;

#line 2235
                                    b_5 = s2_0;

#line 2235
                                }
                                else
                                {

#line 2235
                                    uint candHi_0 = s2_0 | bit_1;

#line 2235
                                    s3_0 = m2_0;

#line 2235
                                    b_5 = candHi_0;

#line 2235
                                }

#line 2235
                            }
                            else
                            {

#line 2235
                                s3_0 = m2_0;

#line 2235
                                b_5 = s2_0;

#line 2235
                            }

#line 2235
                        }
                        else
                        {

#line 2235
                            s3_0 = m2_0;

#line 2235
                            b_5 = s2_0;

#line 2235
                        }

#line 2235
                        i_5 = i_5 + 1U;

#line 2235
                        m2_0 = s3_0;

#line 2235
                        s2_0 = b_5;

#line 2235
                    }

#line 2235
                    s3_0 = m2_0;

#line 2235
                    b_5 = s2_0;

#line 2235
                }
                else
                {

#line 2235
                    s3_0 = 0U;

#line 2235
                    b_5 = 0U;

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                m3_0 = _S31;

#line 2235
                for(;;)
                {

#line 2235
                    if(m3_0 < _S37)
                    {
                    }
                    else
                    {

#line 2235
                        break;
                    }

#line 2235
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m3_0] = 4294967295U;

#line 2235
                    m3_0 = m3_0 + 4U;

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                bool _S93 = (s3_0 | b_5) != 0U;

#line 2235
                if(_S93)
                {

#line 2235
                    i_5 = 0U;

#line 2235
                    for(;;)
                    {

#line 2235
                        if(i_5 < 16U)
                        {
                        }
                        else
                        {

#line 2235
                            break;
                        }

#line 2235
                        uint bit_2 = 1U << (i_5 & 31U);

#line 2235
                        if(i_5 < 32U)
                        {

#line 2235
                            isCand_0 = (s3_0 & bit_2) != 0U;

#line 2235
                        }
                        else
                        {

#line 2235
                            isCand_0 = (b_5 & bit_2) != 0U;

#line 2235
                        }

#line 2235
                        if(isCand_0)
                        {

#line 2235
                            uint _S94 = _S31 * 16U + i_5;

#line 2235
                            uint off_3 = slotToIndex_0(_S94) - _S32 + (&kernelContext_2)->_binPhase_0;

#line 2235
                            if(_S36 >= int(0))
                            {

#line 2235
                                m2_0 = off_3 >> uint(_S36);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S95 = off_3 / _S35;

#line 2235
                                m2_0 = _S95;

#line 2235
                            }

#line 2235
                            uint _S96 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0])), _S94, memory_order_relaxed);

#line 2235
                        }

#line 2235
                        i_5 = i_5 + 1U;

#line 2235
                    }

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                if(_S93)
                {

#line 2235
                    i_5 = 0U;

#line 2235
                    for(;;)
                    {

#line 2235
                        if(i_5 < 16U)
                        {
                        }
                        else
                        {

#line 2235
                            break;
                        }

#line 2235
                        uint bit_3 = 1U << (i_5 & 31U);

#line 2235
                        if(i_5 < 32U)
                        {

#line 2235
                            isCand_0 = (s3_0 & bit_3) != 0U;

#line 2235
                        }
                        else
                        {

#line 2235
                            isCand_0 = (b_5 & bit_3) != 0U;

#line 2235
                        }

#line 2235
                        if(isCand_0)
                        {

#line 2235
                            uint _S97 = _S31 * 16U + i_5;

#line 2235
                            uint idx_3 = slotToIndex_0(_S97);

#line 2235
                            uint off_4 = idx_3 - _S32 + (&kernelContext_2)->_binPhase_0;

#line 2235
                            if(_S36 >= int(0))
                            {

#line 2235
                                m2_0 = off_4 >> uint(_S36);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S98 = off_4 / _S35;

#line 2235
                                m2_0 = _S98;

#line 2235
                            }

#line 2235
                            if(((*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0]) == _S97)
                            {

#line 2235
                                uint o_1 = _S30 * _S37 + m2_0;

#line 2235
                                *((&kernelContext_2)->entryPointParams_peakIdx_0+o_1) = int(idx_3);

#line 2235
                                *((&kernelContext_2)->entryPointParams_peakVal_0+o_1) = packed_float2(float2(r_3[i_5].x, r_3[i_5].y)) ;

#line 2235
                            }

#line 2235
                        }

#line 2235
                        i_5 = i_5 + 1U;

#line 2235
                    }

#line 2235
                }

#line 2235
                m2_0 = _S31;

#line 2235
                for(;;)
                {

#line 2235
                    if(m2_0 < _S37)
                    {
                    }
                    else
                    {

#line 2235
                        break;
                    }

#line 2235
                    if(((*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0]) == 4294967295U)
                    {

#line 2235
                        uint _S99 = _S30 * _S37 + m2_0;

#line 2235
                        *((&kernelContext_2)->entryPointParams_peakIdx_0+_S99) = int(-1);

#line 2235
                        *((&kernelContext_2)->entryPointParams_peakVal_0+_S99) = packed_float2(float2(0.0f, 0.0f)) ;

#line 2235
                    }

#line 2235
                    m2_0 = m2_0 + 4U;

#line 2235
                }

#line 2235
            }

#line 2235
            break;
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2231
        i_4 = i_4 + (&kernelContext_2)->entryPointParams_0->gridSize_0;

#line 2231
    }

#line 2240
    return;
}
