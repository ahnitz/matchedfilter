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


#line 174 "mm_32768_refineItems_lds32.slang"
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


#line 74 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S7 = ((MF_ACCURATE_TRIG));

#line 77
    return _S7;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S8 = mfAccurateTrigFlag_0();

#line 103
    if(_S8 == 0U)
    {

#line 104
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S9 = float(quadrant_0);
    float x_0 = angle_0 - _S9 * 1.57079625129699707f - _S9 * 7.54978941586159635e-08f;
    float z_0 = x_0 * x_0;
    float c_0 = 1.0f + z_0 * (-0.5f + z_0 * (0.0416666679084301f + z_0 * (-0.00138888892251998f + z_0 * (0.00002480158764229f + z_0 * -2.75573199814971304e-07f))));

    float s_0 = x_0 * (1.0f + z_0 * (-0.1666666716337204f + z_0 * (0.00833333376795053f + z_0 * (-0.0001984127011383f + z_0 * (2.75573188446287531e-06f + z_0 * -2.50521079436794025e-08f)))));


    switch(quadrant_0 & int(3))
    {
    case int(1):
        {

#line 117
            return float2(- s_0, c_0);
        }
    case int(2):
        {

#line 118
            return float2(- c_0, - s_0);
        }
    case int(3):
        {

#line 119
            return float2(s_0, - c_0);
        }
    default:
        {

#line 120
            return float2(c_0, s_0);
        }
    }

#line 120
}


#line 323 "mm_32768_refineItems_lds32.slang"
float2 cmul_0(float2 a_1, float2 b_2)
{

#line 323
    float _S10 = a_1.x;

#line 323
    float _S11 = b_2.x;

#line 323
    float _S12 = a_1.y;

#line 323
    float _S13 = b_2.y;

#line 323
    return float2(_S10 * _S11 - _S12 * _S13, _S10 * _S13 + _S12 * _S11);
}


#line 583
void r4_0(float2 thread* a_2, float2 thread* b_3, float2 thread* c_1, float2 thread* d_0)
{
    float2 t0_0 = *a_2 + *c_1;

#line 585
    float2 t1_0 = *a_2 - *c_1;

#line 585
    float2 t2_0 = *b_3 + *d_0;

#line 585
    float2 t3_0 = *b_3 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_2 = t0_0 + t2_0;

#line 587
    *b_3 = t1_0 + j3_0;

#line 587
    *c_1 = t0_0 - t2_0;

#line 587
    *d_0 = t1_0 - j3_0;
    return;
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
        uint _S14 = 4U * k2_0;

#line 631
        r4_0(&(*r_0)[_S14], &(*r_0)[_S14 + 1U], &(*r_0)[_S14 + 2U], &(*r_0)[_S14 + 3U]);

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


#line 665
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 667
    thread array<float2, int(16)> v_0;

#line 667
    uint j_0 = 0U;
    for(;;)
    {

#line 668
        if(j_0 < 16U)
        {
        }
        else
        {

#line 668
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        float2 _S15 = (*r_1)[j_0] - (*r_1)[j_0 + 16U];

#line 672
        float2 _S16 = mfTwiddle_0(6.28318548202514648f * float(j_0) / 32.0f);

#line 672
        v_0[j_0] = cmul_0(_S15, _S16);

#line 668
        j_0 = j_0 + 1U;

#line 668
    }

#line 674
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 675
    uint k_0 = 0U;
    for(;;)
    {

#line 676
        if(k_0 < 16U)
        {
        }
        else
        {

#line 676
            break;
        }

#line 676
        uint _S17 = 2U * k_0;

#line 676
        (*r_1)[_S17] = u_0[k_0];

#line 676
        (*r_1)[_S17 + 1U] = v_0[k_0];

#line 676
        k_0 = k_0 + 1U;

#line 676
    }
    return;
}


#line 704
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 325
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S18 = max(TB_0, 1U);

#line 327
    uint j_1 = d_1 / _S18;

#line 327
    uint m_0 = d_1 % _S18;

#line 327
    uint _S19;
    if(TB_0 <= 32U)
    {

#line 328
        _S19 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 328
    }
    else
    {

#line 328
        _S19 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 328
    }

#line 328
    return _S19;
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


#line 312 "mm_32768_refineItems_lds32.slang"
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
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 312
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 312
    uint _S20 = 2U * i_1;

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S20] = (as_type<uint>((v_1.x)));

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S20 + 1U] = (as_type<uint>((v_1.y)));

#line 312
    return;
}


#line 313
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 313
    uint _S21 = 2U * i_2;

#line 313
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S21]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S21 + 1U]))));
}


#line 722
void innermost_0(array<float2, int(32)> thread* r_3)
{

    dft32_0(r_3);

#line 734
    return;
}


#line 869
uint lgOf_0(uint i_3)
{

#line 869
    uint _S22;

#line 869
    if(i_3 < 2U)
    {

#line 869
        _S22 = 5U;

#line 869
    }
    else
    {

#line 869
        if(i_3 == 2U)
        {

#line 869
            _S22 = 5U;

#line 869
        }
        else
        {

#line 869
            _S22 = 1U;

#line 869
        }

#line 869
    }

#line 869
    return _S22;
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
    uint _S23;

#line 2221
    uint _S24;

#line 2221
    uint _S25;

#line 2221
    uint d_2;

#line 2221
    uint j_2;

#line 2221
    bool isCand_0;

#line 2221
    uint d_3;

#line 2221
    uint m0_0;

#line 2221
    uint s0_0;

#line 2221
    uint m1_0;

#line 2221
    bool _S26;

#line 2221
    bool _S27;

#line 2221
    bool _S28;

#line 2221
    bool _S29;

#line 2221
    bool _S30;

#line 2221
    bool _S31;

#line 2221
    bool _S32;

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
    threadgroup array<uint, int(8192)> stg_1;

#line 2221
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2221
    (&kernelContext_2)->_binPhase_0 = 0U;

#line 2230
    uint _S33 = entryPointParams_count_1[int(0)];

#line 2230
    uint i_4 = gid_0.x;
    for(;;)
    {

#line 2231
        if(i_4 < _S33)
        {
        }
        else
        {

#line 2231
            break;
        }

#line 2232
        (&kernelContext_2)->_stgBase_0 = 0U;
        uint _S34 = 6U * i_4;

#line 2233
        uint d_4 = (&kernelContext_2)->entryPointParams_items_0[_S34];

#line 2233
        uint t_6 = (&kernelContext_2)->entryPointParams_items_0[_S34 + 1U];
        (&kernelContext_2)->_binPhase_0 = (&kernelContext_2)->entryPointParams_items_0[_S34 + 5U];
        uint _S35 = d_4 * (&kernelContext_2)->entryPointParams_0->ntmpl_0 + t_6;

#line 2235
        uint _S36 = (&kernelContext_2)->entryPointParams_items_0[_S34 + 4U];

#line 2235
        uint _S37 = lid_0.x;
        uint _S38 = (&kernelContext_2)->entryPointParams_items_0[_S34 + 2U];

#line 2236
        uint _S39 = (&kernelContext_2)->entryPointParams_items_0[_S34 + 3U];

#line 2236
        uint _S40 = (&kernelContext_2)->entryPointParams_0->ntmpl_0;

#line 2236
        uint _S41 = (&kernelContext_2)->entryPointParams_0->binsize_0;

#line 2236
        int _S42 = (&kernelContext_2)->entryPointParams_0->binShift_0;

#line 2236
        uint _S43 = (&kernelContext_2)->entryPointParams_0->nbins_0;

#line 2236
        uint _S44 = (&kernelContext_2)->entryPointParams_0->thrBits_0;

#line 2235
        for(;;)
        {

#line 2235
            (&kernelContext_2)->_tid_0 = _S37;

#line 2235
            uint _S45 = _S35 / _S40;

#line 2235
            uint _S46 = _S35 % _S40;

#line 2235
            thread array<float2, int(32)> r_4;

#line 2235
            uint n2_0 = 0U;

#line 2235
            for(;;)
            {

#line 2235
                if(n2_0 < 32U)
                {
                }
                else
                {

#line 2235
                    break;
                }

#line 2235
                uint idx_0 = _S37 + 1024U * n2_0;

#line 2235
                uint _S47 = mfDataStrideFlag_0();

#line 2235
                if(_S47 != 0U)
                {

#line 2235
                    uint _S48 = mfDataStrideFlag_0();

#line 2235
                    k2_1 = _S48;

#line 2235
                }
                else
                {

#line 2235
                    k2_1 = 32768U;

#line 2235
                }

#line 2235
                r_4[n2_0] = cmulConj_0(cload_0((&kernelContext_2)->entryPointParams_data_0, _S45 * k2_1 + idx_0), cload_0((&kernelContext_2)->entryPointParams_tmpl_0, _S46 * 32768U + idx_0));

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
                            uint lgTB_0 = firstbithigh_0(1024U);

#line 2235
                            _S23 = lgTB_0;

#line 2235
                            uint lgLn_0 = firstbithigh_0(32768U);

#line 2235
                            uint blk_1 = _S37 >> lgTB_0;

#line 2235
                            uint lane_1 = _S37 & 1023U;

#line 2235
                            dftR_0(&r_4);

#line 2235
                            float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 32768.0f);

#line 2235
                            float _S49 = tw_0.x;

#line 2235
                            float _S50 = tw_0.y;

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
                                if(k2_1 < 32U)
                                {
                                }
                                else
                                {

#line 2235
                                    break;
                                }

#line 2235
                                r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 2235
                                float nr_0 = cr_0 * _S49 - ci_0 * _S50;

#line 2235
                                float _S51 = cr_0 * _S50 + ci_0 * _S49;

#line 2235
                                k2_1 = k2_1 + 1U;

#line 2235
                                cr_0 = nr_0;

#line 2235
                                ci_0 = _S51;

#line 2235
                            }

#line 2235
                            uint per_1 = 32U / max(1024U, 1U);

#line 2235
                            uint _S52 = max(32U, 1U);

#line 2235
                            _S24 = _S52;

#line 2235
                            uint blk2_1 = _S37 / _S52;

#line 2235
                            uint lane2_1 = _S37 % _S52;

#line 2235
                            for(;;)
                            {

#line 2235
                                thread array<float2, int(32)> out_0;

#line 2235
                                uint z_1 = 0U;

#line 2235
                                for(;;)
                                {

#line 2235
                                    if(z_1 < 32U)
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
                                _S25 = spanMask_0;

#line 2235
                                uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2235
                                uint p0_0 = computeWant_0(0U, 1024U, 32768U, blk_1, lane_1, per_1, _S52, 1024U, blk2_1, lane2_1);

#line 2235
                                uint _S53 = p0_0 & lenMask_0;

#line 2235
                                uint _S54 = _S53 >> lgTB_0;

#line 2235
                                uint _S55 = _S54 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S53 & spanMask_0);

#line 2235
                                uint c_2 = 0U;

#line 2235
                                for(;;)
                                {

#line 2235
                                    if(c_2 < 8U)
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
                                    j_2 = 0U;

#line 2235
                                    for(;;)
                                    {

#line 2235
                                        if(j_2 < 4U)
                                        {
                                        }
                                        else
                                        {

#line 2235
                                            break;
                                        }

#line 2235
                                        stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_4[c_2 * 4U + j_2], &kernelContext_2);

#line 2235
                                        j_2 = j_2 + 1U;

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
                                        if(d_2 < 32U)
                                        {
                                        }
                                        else
                                        {

#line 2235
                                            break;
                                        }

#line 2235
                                        uint pz_0 = computeWant_0(d_2, 1024U, 32768U, 0U, 0U, per_1, _S52, 1024U, 0U, 0U);

#line 2235
                                        uint _S56 = pz_0 & lenMask_0;

#line 2235
                                        uint iz_0 = _S56 >> lgTB_0;

#line 2235
                                        uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S56 & spanMask_0);

#line 2235
                                        uint i_5 = _S54 + iz_0;

#line 2235
                                        uint _S57 = c_2 * 4U;

#line 2235
                                        if(i_5 >= _S57)
                                        {

#line 2235
                                            isCand_0 = i_5 < ((c_2 + 1U) * 4U);

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
                                            float2 _S58 = stgGet_0(_S55 + az_0 - _S57 * 1024U, &kernelContext_2);

#line 2235
                                            out_0[d_2] = _S58;

#line 2235
                                        }

#line 2235
                                        d_2 = d_2 + 1U;

#line 2235
                                    }

#line 2235
                                    c_2 = c_2 + 1U;

#line 2235
                                }

#line 2235
                                d_2 = 0U;

#line 2235
                                for(;;)
                                {

#line 2235
                                    if(d_2 < 32U)
                                    {
                                    }
                                    else
                                    {

#line 2235
                                        break;
                                    }

#line 2235
                                    r_4[d_2] = out_0[d_2];

#line 2235
                                    d_2 = d_2 + 1U;

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
                    for(;;)
                    {

#line 2235
                        for(;;)
                        {

#line 2235
                            uint lgTB_1 = firstbithigh_0(32U);

#line 2235
                            uint blk_2 = _S37 >> lgTB_1;

#line 2235
                            uint lane_2 = _S37 & 31U;

#line 2235
                            dftR_0(&r_4);

#line 2235
                            float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 2235
                            float _S59 = tw_1.x;

#line 2235
                            float _S60 = tw_1.y;

#line 2235
                            uint k2_2 = 0U;

#line 2235
                            float cr_1 = 1.0f;

#line 2235
                            float ci_1 = 0.0f;

#line 2235
                            for(;;)
                            {

#line 2235
                                if(k2_2 < 32U)
                                {
                                }
                                else
                                {

#line 2235
                                    break;
                                }

#line 2235
                                r_4[k2_2] = cmul_0(r_4[k2_2], float2(cr_1, ci_1));

#line 2235
                                float nr_1 = cr_1 * _S59 - ci_1 * _S60;

#line 2235
                                float _S61 = cr_1 * _S60 + ci_1 * _S59;

#line 2235
                                k2_2 = k2_2 + 1U;

#line 2235
                                cr_1 = nr_1;

#line 2235
                                ci_1 = _S61;

#line 2235
                            }

#line 2235
                            uint per_2 = 32U / _S24;

#line 2235
                            uint _S62 = max(1U, 1U);

#line 2235
                            uint blk2_2 = _S37 / _S62;

#line 2235
                            uint lane2_2 = _S37 % _S62;

#line 2235
                            for(;;)
                            {

#line 2235
                                thread array<float2, int(32)> out_1;

#line 2235
                                uint z_2 = 0U;

#line 2235
                                for(;;)
                                {

#line 2235
                                    if(z_2 < 32U)
                                    {
                                    }
                                    else
                                    {

#line 2235
                                        break;
                                    }

#line 2235
                                    out_1[z_2] = float2(0.0f, 0.0f);

#line 2235
                                    z_2 = z_2 + 1U;

#line 2235
                                }

#line 2235
                                uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2235
                                uint p0_1 = computeWant_0(0U, 32U, 1024U, blk_2, lane_2, per_2, _S62, 32U, blk2_2, lane2_2);

#line 2235
                                uint _S63 = p0_1 & _S25;

#line 2235
                                uint _S64 = _S63 >> lgTB_1;

#line 2235
                                uint _S65 = _S64 * 1024U + ((p0_1 >> _S23) << lgTB_1) + (_S63 & spanMask_1);

#line 2235
                                uint c_3 = 0U;

#line 2235
                                for(;;)
                                {

#line 2235
                                    if(c_3 < 8U)
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
                                    j_2 = 0U;

#line 2235
                                    for(;;)
                                    {

#line 2235
                                        if(j_2 < 4U)
                                        {
                                        }
                                        else
                                        {

#line 2235
                                            break;
                                        }

#line 2235
                                        stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_4[c_3 * 4U + j_2], &kernelContext_2);

#line 2235
                                        j_2 = j_2 + 1U;

#line 2235
                                    }

#line 2235
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                                    d_3 = 0U;

#line 2235
                                    for(;;)
                                    {

#line 2235
                                        if(d_3 < 32U)
                                        {
                                        }
                                        else
                                        {

#line 2235
                                            break;
                                        }

#line 2235
                                        uint pz_1 = computeWant_0(d_3, 32U, 1024U, 0U, 0U, per_2, _S62, 32U, 0U, 0U);

#line 2235
                                        uint _S66 = pz_1 & _S25;

#line 2235
                                        uint iz_1 = _S66 >> lgTB_1;

#line 2235
                                        uint az_1 = iz_1 * 1024U + ((pz_1 >> _S23) << lgTB_1) + (_S66 & spanMask_1);

#line 2235
                                        uint i_6 = _S64 + iz_1;

#line 2235
                                        uint _S67 = c_3 * 4U;

#line 2235
                                        if(i_6 >= _S67)
                                        {

#line 2235
                                            isCand_0 = i_6 < ((c_3 + 1U) * 4U);

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
                                            float2 _S68 = stgGet_0(_S65 + az_1 - _S67 * 1024U, &kernelContext_2);

#line 2235
                                            out_1[d_3] = _S68;

#line 2235
                                        }

#line 2235
                                        d_3 = d_3 + 1U;

#line 2235
                                    }

#line 2235
                                    c_3 = c_3 + 1U;

#line 2235
                                }

#line 2235
                                j_2 = 0U;

#line 2235
                                for(;;)
                                {

#line 2235
                                    if(j_2 < 32U)
                                    {
                                    }
                                    else
                                    {

#line 2235
                                        break;
                                    }

#line 2235
                                    r_4[j_2] = out_1[j_2];

#line 2235
                                    j_2 = j_2 + 1U;

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
                innermost_0(&r_4);

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
            uint i_7;

#line 2235
            uint m2_0;

#line 2235
            uint s2_0;

#line 2235
            uint m3_0;

#line 2235
            uint s3_0;

#line 2235
            uint b_4;

#line 2235
            if(_S43 <= 4U)
            {

#line 2235
                if(_S37 < 4U)
                {

#line 2235
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + _S37] = _S44;

#line 2235
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U + _S37] = 4294967295U;

#line 2235
                }

#line 2235
                float2 _S69 = float2(0.0f, 0.0f);

#line 2235
                i_7 = 0U;

#line 2235
                d_3 = _S44;

#line 2235
                s0_1 = 4294967295U;

#line 2235
                float2 v0_0 = _S69;

#line 2235
                m1_1 = _S44;

#line 2235
                s1_0 = 4294967295U;

#line 2235
                float2 v1_0 = _S69;

#line 2235
                m2_0 = _S44;

#line 2235
                s2_0 = 4294967295U;

#line 2235
                float2 v2_0 = _S69;

#line 2235
                m3_0 = _S44;

#line 2235
                s3_0 = 4294967295U;

#line 2235
                float2 v3_0 = _S69;

#line 2235
                for(;;)
                {

#line 2235
                    if(i_7 < 32U)
                    {
                    }
                    else
                    {

#line 2235
                        break;
                    }

#line 2235
                    uint slot_1 = _S37 * 32U + i_7;

#line 2235
                    uint idx_1 = slotToIndex_0(slot_1);

#line 2235
                    if(idx_1 >= _S38)
                    {

#line 2235
                        isCand_0 = idx_1 < _S39;

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
                        float rx_0 = r_4[i_7].x;

#line 2235
                        float ry_0 = r_4[i_7].y;

#line 2235
                        uint mag_0 = (as_type<uint>((rx_0 * rx_0 + ry_0 * ry_0)));

#line 2235
                        uint off_0 = idx_1 - _S38 + (&kernelContext_2)->_binPhase_0;

#line 2235
                        if(_S43 == 1U)
                        {

#line 2235
                            b_4 = 0U;

#line 2235
                        }
                        else
                        {

#line 2235
                            if(_S42 >= int(0))
                            {

#line 2235
                                b_4 = off_0 >> uint(_S42);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S70 = off_0 / _S41;

#line 2235
                                b_4 = _S70;

#line 2235
                            }

#line 2235
                        }

#line 2235
                        if(b_4 == 0U)
                        {

#line 2235
                            _S26 = mag_0 > d_3;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S26 = false;

#line 2235
                        }

#line 2235
                        float2 v0_1;

#line 2235
                        if(_S26)
                        {

#line 2235
                            float2 _S71 = float2(rx_0, ry_0);

#line 2235
                            m0_0 = mag_0;

#line 2235
                            s0_0 = slot_1;

#line 2235
                            v0_1 = _S71;

#line 2235
                        }
                        else
                        {

#line 2235
                            m0_0 = d_3;

#line 2235
                            s0_0 = s0_1;

#line 2235
                            v0_1 = v0_0;

#line 2235
                        }

#line 2235
                        if(_S43 >= 2U)
                        {

#line 2235
                            _S27 = b_4 == 1U;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S27 = false;

#line 2235
                        }

#line 2235
                        if(_S27)
                        {

#line 2235
                            _S28 = mag_0 > m1_1;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S28 = false;

#line 2235
                        }

#line 2235
                        uint s1_1;

#line 2235
                        float2 v1_1;

#line 2235
                        if(_S28)
                        {

#line 2235
                            float2 _S72 = float2(rx_0, ry_0);

#line 2235
                            m1_0 = mag_0;

#line 2235
                            s1_1 = slot_1;

#line 2235
                            v1_1 = _S72;

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
                        if(_S43 >= 3U)
                        {

#line 2235
                            _S29 = b_4 == 2U;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S29 = false;

#line 2235
                        }

#line 2235
                        if(_S29)
                        {

#line 2235
                            _S30 = mag_0 > m2_0;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S30 = false;

#line 2235
                        }

#line 2235
                        uint m2_1;

#line 2235
                        uint s2_1;

#line 2235
                        float2 v2_1;

#line 2235
                        if(_S30)
                        {

#line 2235
                            float2 _S73 = float2(rx_0, ry_0);

#line 2235
                            m2_1 = mag_0;

#line 2235
                            s2_1 = slot_1;

#line 2235
                            v2_1 = _S73;

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
                        if(_S43 >= 4U)
                        {

#line 2235
                            _S31 = b_4 == 3U;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S31 = false;

#line 2235
                        }

#line 2235
                        if(_S31)
                        {

#line 2235
                            _S32 = mag_0 > m3_0;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S32 = false;

#line 2235
                        }

#line 2235
                        uint m3_1;

#line 2235
                        uint s3_1;

#line 2235
                        float2 v3_1;

#line 2235
                        if(_S32)
                        {

#line 2235
                            float2 _S74 = float2(rx_0, ry_0);

#line 2235
                            m3_1 = mag_0;

#line 2235
                            s3_1 = slot_1;

#line 2235
                            v3_1 = _S74;

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
                        d_3 = m0_0;

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
                    i_7 = i_7 + 1U;

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                uint wm0_0 = simd_max(d_3);

#line 2235
                bool _S75 = simd_is_first();

#line 2235
                if(_S75)
                {

#line 2235
                    isCand_0 = wm0_0 > _S44;

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
                    uint _S76 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0])), wm0_0, memory_order_relaxed);

#line 2235
                }

#line 2235
                bool _S77 = _S43 >= 2U;

#line 2235
                if(_S77)
                {

#line 2235
                    uint wm1_0 = simd_max(m1_1);

#line 2235
                    bool _S78 = simd_is_first();

#line 2235
                    if(_S78)
                    {

#line 2235
                        _S26 = wm1_0 > _S44;

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
                        uint _S79 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 1U])), wm1_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                bool _S80 = _S43 >= 3U;

#line 2235
                if(_S80)
                {

#line 2235
                    uint wm2_0 = simd_max(m2_0);

#line 2235
                    bool _S81 = simd_is_first();

#line 2235
                    if(_S81)
                    {

#line 2235
                        _S26 = wm2_0 > _S44;

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
                        uint _S82 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 2U])), wm2_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                bool _S83 = _S43 >= 4U;

#line 2235
                if(_S83)
                {

#line 2235
                    uint wm3_0 = simd_max(m3_0);

#line 2235
                    bool _S84 = simd_is_first();

#line 2235
                    if(_S84)
                    {

#line 2235
                        _S26 = wm3_0 > _S44;

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
                        uint _S85 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 3U])), wm3_0, memory_order_relaxed);

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
                    _S26 = d_3 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0];

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
                    b_4 = s0_1;

#line 2235
                }
                else
                {

#line 2235
                    b_4 = 4294967295U;

#line 2235
                }

#line 2235
                if(_S77)
                {

#line 2235
                    _S27 = s1_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S27 = false;

#line 2235
                }

#line 2235
                if(_S27)
                {

#line 2235
                    _S28 = m1_1 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 1U];

#line 2235
                }
                else
                {

#line 2235
                    _S28 = false;

#line 2235
                }

#line 2235
                if(_S28)
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
                if(_S80)
                {

#line 2235
                    _S29 = s2_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S29 = false;

#line 2235
                }

#line 2235
                if(_S29)
                {

#line 2235
                    _S30 = m2_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 2U];

#line 2235
                }
                else
                {

#line 2235
                    _S30 = false;

#line 2235
                }

#line 2235
                if(_S30)
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
                if(_S83)
                {

#line 2235
                    _S31 = s3_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S31 = false;

#line 2235
                }

#line 2235
                if(_S31)
                {

#line 2235
                    _S32 = m3_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 3U];

#line 2235
                }
                else
                {

#line 2235
                    _S32 = false;

#line 2235
                }

#line 2235
                if(_S32)
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
                uint ww0_0 = simd_min(b_4);

#line 2235
                bool _S86 = simd_is_first();

#line 2235
                bool _S87;

#line 2235
                if(_S86)
                {

#line 2235
                    _S87 = ww0_0 != 4294967295U;

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
                    uint _S88 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U])), ww0_0, memory_order_relaxed);

#line 2235
                }

#line 2235
                bool _S89;

#line 2235
                if(_S77)
                {

#line 2235
                    uint ww1_0 = simd_min(m0_0);

#line 2235
                    bool _S90 = simd_is_first();

#line 2235
                    if(_S90)
                    {

#line 2235
                        _S89 = ww1_0 != 4294967295U;

#line 2235
                    }
                    else
                    {

#line 2235
                        _S89 = false;

#line 2235
                    }

#line 2235
                    if(_S89)
                    {

#line 2235
                        uint _S91 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 5U])), ww1_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                if(_S80)
                {

#line 2235
                    uint ww2_0 = simd_min(s0_0);

#line 2235
                    bool _S92 = simd_is_first();

#line 2235
                    if(_S92)
                    {

#line 2235
                        _S89 = ww2_0 != 4294967295U;

#line 2235
                    }
                    else
                    {

#line 2235
                        _S89 = false;

#line 2235
                    }

#line 2235
                    if(_S89)
                    {

#line 2235
                        uint _S93 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 6U])), ww2_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                if(_S83)
                {

#line 2235
                    uint ww3_0 = simd_min(m1_0);

#line 2235
                    bool _S94 = simd_is_first();

#line 2235
                    if(_S94)
                    {

#line 2235
                        _S89 = ww3_0 != 4294967295U;

#line 2235
                    }
                    else
                    {

#line 2235
                        _S89 = false;

#line 2235
                    }

#line 2235
                    if(_S89)
                    {

#line 2235
                        uint _S95 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 7U])), ww3_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                uint baseOut_0 = _S36 * _S43;

#line 2235
                if(b_4 != 4294967295U)
                {

#line 2235
                    _S89 = b_4 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U];

#line 2235
                }
                else
                {

#line 2235
                    _S89 = false;

#line 2235
                }

#line 2235
                if(_S89)
                {

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+baseOut_0) = int(slotToIndex_0(b_4));

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+baseOut_0) = packed_float2(v0_0) ;

#line 2235
                }

#line 2235
                bool _S96;

#line 2235
                if(_S77)
                {

#line 2235
                    _S96 = m0_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S96 = false;

#line 2235
                }

#line 2235
                bool _S97;

#line 2235
                if(_S96)
                {

#line 2235
                    _S97 = m0_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 5U];

#line 2235
                }
                else
                {

#line 2235
                    _S97 = false;

#line 2235
                }

#line 2235
                if(_S97)
                {

#line 2235
                    uint _S98 = baseOut_0 + 1U;

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S98) = int(slotToIndex_0(m0_0));

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S98) = packed_float2(v1_0) ;

#line 2235
                }

#line 2235
                bool _S99;

#line 2235
                if(_S80)
                {

#line 2235
                    _S99 = s0_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S99 = false;

#line 2235
                }

#line 2235
                bool _S100;

#line 2235
                if(_S99)
                {

#line 2235
                    _S100 = s0_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 6U];

#line 2235
                }
                else
                {

#line 2235
                    _S100 = false;

#line 2235
                }

#line 2235
                if(_S100)
                {

#line 2235
                    uint _S101 = baseOut_0 + 2U;

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S101) = int(slotToIndex_0(s0_0));

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S101) = packed_float2(v2_0) ;

#line 2235
                }

#line 2235
                bool _S102;

#line 2235
                if(_S83)
                {

#line 2235
                    _S102 = m1_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S102 = false;

#line 2235
                }

#line 2235
                bool _S103;

#line 2235
                if(_S102)
                {

#line 2235
                    _S103 = m1_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 7U];

#line 2235
                }
                else
                {

#line 2235
                    _S103 = false;

#line 2235
                }

#line 2235
                if(_S103)
                {

#line 2235
                    uint _S104 = baseOut_0 + 3U;

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S104) = int(slotToIndex_0(m1_0));

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S104) = packed_float2(v3_0) ;

#line 2235
                }

#line 2235
                bool _S105;

#line 2235
                if(_S37 < _S43)
                {

#line 2235
                    _S105 = ((*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U + _S37]) == 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S105 = false;

#line 2235
                }

#line 2235
                if(_S105)
                {

#line 2235
                    uint _S106 = baseOut_0 + _S37;

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S106) = int(-1);

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S106) = packed_float2(_S69) ;

#line 2235
                }

#line 2235
            }
            else
            {

#line 2235
                d_3 = _S37;

#line 2235
                for(;;)
                {

#line 2235
                    if(d_3 < _S43)
                    {
                    }
                    else
                    {

#line 2235
                        break;
                    }

#line 2235
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + d_3] = _S44;

#line 2235
                    d_3 = d_3 + 1024U;

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
                    bool _S107 = s0_1 < 32U;

#line 2235
                    if(_S107)
                    {
                    }
                    else
                    {

#line 2235
                        break;
                    }

#line 2235
                    uint idx_2 = slotToIndex_0(_S37 * 32U + s0_1);

#line 2235
                    if(idx_2 >= _S38)
                    {

#line 2235
                        isCand_0 = idx_2 < _S39;

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
                        float rx_1 = r_4[s0_1].x;

#line 2235
                        float ry_1 = r_4[s0_1].y;

#line 2235
                        uint mag_1 = (as_type<uint>((rx_1 * rx_1 + ry_1 * ry_1)));

#line 2235
                        if(mag_1 > _S44)
                        {

#line 2235
                            uint off_1 = idx_2 - _S38 + (&kernelContext_2)->_binPhase_0;

#line 2235
                            if(_S42 >= int(0))
                            {

#line 2235
                                m2_0 = off_1 >> uint(_S42);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S108 = off_1 / _S41;

#line 2235
                                m2_0 = _S108;

#line 2235
                            }

#line 2235
                            uint _S109 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0])), mag_1, memory_order_relaxed);

#line 2235
                            uint bit_0 = 1U << (s0_1 & 31U);

#line 2235
                            if(_S107)
                            {

#line 2235
                                i_7 = m1_1 | bit_0;

#line 2235
                                s2_0 = s1_0;

#line 2235
                            }
                            else
                            {

#line 2235
                                uint aboveHi_0 = s1_0 | bit_0;

#line 2235
                                i_7 = m1_1;

#line 2235
                                s2_0 = aboveHi_0;

#line 2235
                            }

#line 2235
                        }
                        else
                        {

#line 2235
                            i_7 = m1_1;

#line 2235
                            s2_0 = s1_0;

#line 2235
                        }

#line 2235
                    }
                    else
                    {

#line 2235
                        i_7 = m1_1;

#line 2235
                        s2_0 = s1_0;

#line 2235
                    }

#line 2235
                    s0_1 = s0_1 + 1U;

#line 2235
                    m1_1 = i_7;

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
                    i_7 = 0U;

#line 2235
                    m2_0 = 0U;

#line 2235
                    s2_0 = 0U;

#line 2235
                    for(;;)
                    {

#line 2235
                        bool _S110 = i_7 < 32U;

#line 2235
                        if(_S110)
                        {
                        }
                        else
                        {

#line 2235
                            break;
                        }

#line 2235
                        uint bit_1 = 1U << (i_7 & 31U);

#line 2235
                        if(_S110)
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
                            uint off_2 = slotToIndex_0(_S37 * 32U + i_7) - _S38 + (&kernelContext_2)->_binPhase_0;

#line 2235
                            if(_S42 >= int(0))
                            {

#line 2235
                                m3_0 = off_2 >> uint(_S42);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S111 = off_2 / _S41;

#line 2235
                                m3_0 = _S111;

#line 2235
                            }

#line 2235
                            float rx_2 = r_4[i_7].x;

#line 2235
                            float ry_2 = r_4[i_7].y;

#line 2235
                            if((as_type<uint>((rx_2 * rx_2 + ry_2 * ry_2))) == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m3_0])
                            {

#line 2235
                                if(_S110)
                                {

#line 2235
                                    s3_0 = m2_0 | bit_1;

#line 2235
                                    b_4 = s2_0;

#line 2235
                                }
                                else
                                {

#line 2235
                                    uint candHi_0 = s2_0 | bit_1;

#line 2235
                                    s3_0 = m2_0;

#line 2235
                                    b_4 = candHi_0;

#line 2235
                                }

#line 2235
                            }
                            else
                            {

#line 2235
                                s3_0 = m2_0;

#line 2235
                                b_4 = s2_0;

#line 2235
                            }

#line 2235
                        }
                        else
                        {

#line 2235
                            s3_0 = m2_0;

#line 2235
                            b_4 = s2_0;

#line 2235
                        }

#line 2235
                        i_7 = i_7 + 1U;

#line 2235
                        m2_0 = s3_0;

#line 2235
                        s2_0 = b_4;

#line 2235
                    }

#line 2235
                    s3_0 = m2_0;

#line 2235
                    b_4 = s2_0;

#line 2235
                }
                else
                {

#line 2235
                    s3_0 = 0U;

#line 2235
                    b_4 = 0U;

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                m3_0 = _S37;

#line 2235
                for(;;)
                {

#line 2235
                    if(m3_0 < _S43)
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
                    m3_0 = m3_0 + 1024U;

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                bool _S112 = (s3_0 | b_4) != 0U;

#line 2235
                if(_S112)
                {

#line 2235
                    i_7 = 0U;

#line 2235
                    for(;;)
                    {

#line 2235
                        bool _S113 = i_7 < 32U;

#line 2235
                        if(_S113)
                        {
                        }
                        else
                        {

#line 2235
                            break;
                        }

#line 2235
                        uint bit_2 = 1U << (i_7 & 31U);

#line 2235
                        if(_S113)
                        {

#line 2235
                            isCand_0 = (s3_0 & bit_2) != 0U;

#line 2235
                        }
                        else
                        {

#line 2235
                            isCand_0 = (b_4 & bit_2) != 0U;

#line 2235
                        }

#line 2235
                        if(isCand_0)
                        {

#line 2235
                            uint _S114 = _S37 * 32U + i_7;

#line 2235
                            uint off_3 = slotToIndex_0(_S114) - _S38 + (&kernelContext_2)->_binPhase_0;

#line 2235
                            if(_S42 >= int(0))
                            {

#line 2235
                                m2_0 = off_3 >> uint(_S42);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S115 = off_3 / _S41;

#line 2235
                                m2_0 = _S115;

#line 2235
                            }

#line 2235
                            uint _S116 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0])), _S114, memory_order_relaxed);

#line 2235
                        }

#line 2235
                        i_7 = i_7 + 1U;

#line 2235
                    }

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                if(_S112)
                {

#line 2235
                    i_7 = 0U;

#line 2235
                    for(;;)
                    {

#line 2235
                        bool _S117 = i_7 < 32U;

#line 2235
                        if(_S117)
                        {
                        }
                        else
                        {

#line 2235
                            break;
                        }

#line 2235
                        uint bit_3 = 1U << (i_7 & 31U);

#line 2235
                        if(_S117)
                        {

#line 2235
                            isCand_0 = (s3_0 & bit_3) != 0U;

#line 2235
                        }
                        else
                        {

#line 2235
                            isCand_0 = (b_4 & bit_3) != 0U;

#line 2235
                        }

#line 2235
                        if(isCand_0)
                        {

#line 2235
                            uint _S118 = _S37 * 32U + i_7;

#line 2235
                            uint idx_3 = slotToIndex_0(_S118);

#line 2235
                            uint off_4 = idx_3 - _S38 + (&kernelContext_2)->_binPhase_0;

#line 2235
                            if(_S42 >= int(0))
                            {

#line 2235
                                m2_0 = off_4 >> uint(_S42);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S119 = off_4 / _S41;

#line 2235
                                m2_0 = _S119;

#line 2235
                            }

#line 2235
                            if(((*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0]) == _S118)
                            {

#line 2235
                                uint o_0 = _S36 * _S43 + m2_0;

#line 2235
                                *((&kernelContext_2)->entryPointParams_peakIdx_0+o_0) = int(idx_3);

#line 2235
                                *((&kernelContext_2)->entryPointParams_peakVal_0+o_0) = packed_float2(float2(r_4[i_7].x, r_4[i_7].y)) ;

#line 2235
                            }

#line 2235
                        }

#line 2235
                        i_7 = i_7 + 1U;

#line 2235
                    }

#line 2235
                }

#line 2235
                m2_0 = _S37;

#line 2235
                for(;;)
                {

#line 2235
                    if(m2_0 < _S43)
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
                        uint _S120 = _S36 * _S43 + m2_0;

#line 2235
                        *((&kernelContext_2)->entryPointParams_peakIdx_0+_S120) = int(-1);

#line 2235
                        *((&kernelContext_2)->entryPointParams_peakVal_0+_S120) = packed_float2(float2(0.0f, 0.0f)) ;

#line 2235
                    }

#line 2235
                    m2_0 = m2_0 + 1024U;

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
