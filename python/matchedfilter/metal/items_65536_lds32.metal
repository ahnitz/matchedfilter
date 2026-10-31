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


#line 174 "mm_65536_refineItems_lds32.slang"
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


#line 323 "mm_65536_refineItems_lds32.slang"
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 323
    float _S10 = a_2.x;

#line 323
    float _S11 = b_3.x;

#line 323
    float _S12 = a_2.y;

#line 323
    float _S13 = b_3.y;

#line 323
    return float2(_S10 * _S11 - _S12 * _S13, _S10 * _S13 + _S12 * _S11);
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


#line 685
void dft64_0(array<float2, int(64)> thread* r_1)
{

#line 685
    uint k_0;

#line 685
    uint j_0 = 0U;

    for(;;)
    {

#line 687
        if(j_0 < 16U)
        {
        }
        else
        {

#line 687
            break;
        }

#line 688
        r4_0(&(*r_1)[j_0], &(*r_1)[j_0 + 16U], &(*r_1)[j_0 + 32U], &(*r_1)[j_0 + 48U]);

#line 687
        j_0 = j_0 + 1U;

#line 687
    }

    thread array<float2, int(64)> o_0;

#line 689
    uint pp_0 = 0U;
    for(;;)
    {

#line 690
        if(pp_0 < 4U)
        {
        }
        else
        {

#line 690
            break;
        }

#line 691
        thread array<float2, int(16)> b_4;

#line 691
        j_0 = 0U;
        for(;;)
        {

#line 692
            if(j_0 < 16U)
            {
            }
            else
            {

#line 692
                break;
            }
            float2 _S15 = mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f);

#line 694
            b_4[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], _S15);

#line 692
            j_0 = j_0 + 1U;

#line 692
        }



        dft16_0(&b_4);

#line 696
        k_0 = 0U;
        for(;;)
        {

#line 697
            if(k_0 < 16U)
            {
            }
            else
            {

#line 697
                break;
            }

#line 697
            o_0[4U * k_0 + pp_0] = b_4[k_0];

#line 697
            k_0 = k_0 + 1U;

#line 697
        }

#line 690
        pp_0 = pp_0 + 1U;

#line 690
    }

#line 690
    k_0 = 0U;

#line 699
    for(;;)
    {

#line 699
        if(k_0 < 64U)
        {
        }
        else
        {

#line 699
            break;
        }

#line 699
        (*r_1)[k_0] = o_0[k_0];

#line 699
        k_0 = k_0 + 1U;

#line 699
    }
    return;
}


void dftR_0(array<float2, int(64)> thread* r_2)
{

#line 711
    dft64_0(r_2);

    return;
}


#line 325
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S16 = max(TB_0, 1U);

#line 327
    uint j_1 = d_1 / _S16;

#line 327
    uint m_0 = d_1 % _S16;

#line 327
    uint _S17;
    if(TB_0 <= 64U)
    {

#line 328
        _S17 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 328
    }
    else
    {

#line 328
        _S17 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 328
    }

#line 328
    return _S17;
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


#line 312 "mm_65536_refineItems_lds32.slang"
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
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 312
    uint _S18 = 2U * i_1;

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S18] = (as_type<uint>((v_0.x)));

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S18 + 1U] = (as_type<uint>((v_0.y)));

#line 312
    return;
}


#line 313
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 313
    uint _S19 = 2U * i_2;

#line 313
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S19]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S19 + 1U]))));
}


#line 644
void dft16at_0(array<float2, int(64)> thread* r_3, uint o_1)
{



    thread array<float2, int(16)> b_5;

#line 649
    uint i_3 = 0U;
    for(;;)
    {

#line 650
        if(i_3 < 16U)
        {
        }
        else
        {

#line 650
            break;
        }

#line 650
        b_5[i_3] = (*r_3)[o_1 + i_3];

#line 650
        i_3 = i_3 + 1U;

#line 650
    }
    dft16_0(&b_5);

#line 651
    i_3 = 0U;
    for(;;)
    {

#line 652
        if(i_3 < 16U)
        {
        }
        else
        {

#line 652
            break;
        }

#line 652
        (*r_3)[o_1 + i_3] = b_5[i_3];

#line 652
        i_3 = i_3 + 1U;

#line 652
    }

    return;
}


#line 722
void innermost_0(array<float2, int(64)> thread* r_4)
{

#line 722
    uint b_6 = 0U;

#line 727
    for(;;)
    {

#line 727
        if(b_6 < 4U)
        {
        }
        else
        {

#line 727
            break;
        }

#line 727
        dft16at_0(r_4, b_6 * 16U);

#line 727
        b_6 = b_6 + 1U;

#line 727
    }

#line 734
    return;
}


#line 869
uint lgOf_0(uint i_4)
{

#line 869
    uint _S20;

#line 869
    if(i_4 < 2U)
    {

#line 869
        _S20 = 6U;

#line 869
    }
    else
    {

#line 869
        if(i_4 == 2U)
        {

#line 869
            _S20 = 4U;

#line 869
        }
        else
        {

#line 869
            _S20 = 1U;

#line 869
        }

#line 869
    }

#line 869
    return _S20;
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
    uint _S21;

#line 2221
    uint _S22;

#line 2221
    uint _S23;

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
    bool _S24;

#line 2221
    bool _S25;

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
    uint _S31 = entryPointParams_count_1[int(0)];

#line 2230
    uint i_5 = gid_0.x;
    for(;;)
    {

#line 2231
        if(i_5 < _S31)
        {
        }
        else
        {

#line 2231
            break;
        }

#line 2232
        (&kernelContext_2)->_stgBase_0 = 0U;
        uint _S32 = 6U * i_5;

#line 2233
        uint d_4 = (&kernelContext_2)->entryPointParams_items_0[_S32];

#line 2233
        uint t_6 = (&kernelContext_2)->entryPointParams_items_0[_S32 + 1U];
        (&kernelContext_2)->_binPhase_0 = (&kernelContext_2)->entryPointParams_items_0[_S32 + 5U];
        uint _S33 = d_4 * (&kernelContext_2)->entryPointParams_0->ntmpl_0 + t_6;

#line 2235
        uint _S34 = (&kernelContext_2)->entryPointParams_items_0[_S32 + 4U];

#line 2235
        uint _S35 = lid_0.x;
        uint _S36 = (&kernelContext_2)->entryPointParams_items_0[_S32 + 2U];

#line 2236
        uint _S37 = (&kernelContext_2)->entryPointParams_items_0[_S32 + 3U];

#line 2236
        uint _S38 = (&kernelContext_2)->entryPointParams_0->ntmpl_0;

#line 2236
        uint _S39 = (&kernelContext_2)->entryPointParams_0->binsize_0;

#line 2236
        int _S40 = (&kernelContext_2)->entryPointParams_0->binShift_0;

#line 2236
        uint _S41 = (&kernelContext_2)->entryPointParams_0->nbins_0;

#line 2236
        uint _S42 = (&kernelContext_2)->entryPointParams_0->thrBits_0;

#line 2235
        for(;;)
        {

#line 2235
            (&kernelContext_2)->_tid_0 = _S35;

#line 2235
            uint _S43 = _S33 / _S38;

#line 2235
            uint _S44 = _S33 % _S38;

#line 2235
            thread array<float2, int(64)> r_5;

#line 2235
            uint n2_0 = 0U;

#line 2235
            for(;;)
            {

#line 2235
                if(n2_0 < 64U)
                {
                }
                else
                {

#line 2235
                    break;
                }

#line 2235
                uint idx_0 = _S35 + 1024U * n2_0;

#line 2235
                uint _S45 = mfDataStrideFlag_0();

#line 2235
                if(_S45 != 0U)
                {

#line 2235
                    uint _S46 = mfDataStrideFlag_0();

#line 2235
                    k2_1 = _S46;

#line 2235
                }
                else
                {

#line 2235
                    k2_1 = 65536U;

#line 2235
                }

#line 2235
                r_5[n2_0] = cmulConj_0(cload_0((&kernelContext_2)->entryPointParams_data_0, _S43 * k2_1 + idx_0), cload_0((&kernelContext_2)->entryPointParams_tmpl_0, _S44 * 65536U + idx_0));

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
                            _S21 = lgTB_0;

#line 2235
                            uint lgLn_0 = firstbithigh_0(65536U);

#line 2235
                            uint blk_1 = _S35 >> lgTB_0;

#line 2235
                            uint lane_1 = _S35 & 1023U;

#line 2235
                            dftR_0(&r_5);

#line 2235
                            float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 6.5536e+04f);

#line 2235
                            float _S47 = tw_0.x;

#line 2235
                            float _S48 = tw_0.y;

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
                                if(k2_1 < 64U)
                                {
                                }
                                else
                                {

#line 2235
                                    break;
                                }

#line 2235
                                r_5[k2_1] = cmul_0(r_5[k2_1], float2(cr_0, ci_0));

#line 2235
                                float nr_0 = cr_0 * _S47 - ci_0 * _S48;

#line 2235
                                float _S49 = cr_0 * _S48 + ci_0 * _S47;

#line 2235
                                k2_1 = k2_1 + 1U;

#line 2235
                                cr_0 = nr_0;

#line 2235
                                ci_0 = _S49;

#line 2235
                            }

#line 2235
                            uint per_1 = 64U / max(1024U, 1U);

#line 2235
                            uint _S50 = max(16U, 1U);

#line 2235
                            _S22 = _S50;

#line 2235
                            uint blk2_1 = _S35 / _S50;

#line 2235
                            uint lane2_1 = _S35 % _S50;

#line 2235
                            for(;;)
                            {

#line 2235
                                thread array<float2, int(64)> out_0;

#line 2235
                                uint z_1 = 0U;

#line 2235
                                for(;;)
                                {

#line 2235
                                    if(z_1 < 64U)
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
                                _S23 = spanMask_0;

#line 2235
                                uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2235
                                uint p0_0 = computeWant_0(0U, 1024U, 65536U, blk_1, lane_1, per_1, _S50, 1024U, blk2_1, lane2_1);

#line 2235
                                uint _S51 = p0_0 & lenMask_0;

#line 2235
                                uint _S52 = _S51 >> lgTB_0;

#line 2235
                                uint _S53 = _S52 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S51 & spanMask_0);

#line 2235
                                uint c_2 = 0U;

#line 2235
                                for(;;)
                                {

#line 2235
                                    if(c_2 < 16U)
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
                                        stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_5[c_2 * 4U + j_2], &kernelContext_2);

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
                                        if(d_2 < 64U)
                                        {
                                        }
                                        else
                                        {

#line 2235
                                            break;
                                        }

#line 2235
                                        uint pz_0 = computeWant_0(d_2, 1024U, 65536U, 0U, 0U, per_1, _S50, 1024U, 0U, 0U);

#line 2235
                                        uint _S54 = pz_0 & lenMask_0;

#line 2235
                                        uint iz_0 = _S54 >> lgTB_0;

#line 2235
                                        uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S54 & spanMask_0);

#line 2235
                                        uint i_6 = _S52 + iz_0;

#line 2235
                                        uint _S55 = c_2 * 4U;

#line 2235
                                        if(i_6 >= _S55)
                                        {

#line 2235
                                            isCand_0 = i_6 < ((c_2 + 1U) * 4U);

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
                                            float2 _S56 = stgGet_0(_S53 + az_0 - _S55 * 1024U, &kernelContext_2);

#line 2235
                                            out_0[d_2] = _S56;

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
                                    if(d_2 < 64U)
                                    {
                                    }
                                    else
                                    {

#line 2235
                                        break;
                                    }

#line 2235
                                    r_5[d_2] = out_0[d_2];

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
                            uint lgTB_1 = firstbithigh_0(16U);

#line 2235
                            uint blk_2 = _S35 >> lgTB_1;

#line 2235
                            uint lane_2 = _S35 & 15U;

#line 2235
                            dftR_0(&r_5);

#line 2235
                            float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 2235
                            float _S57 = tw_1.x;

#line 2235
                            float _S58 = tw_1.y;

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
                                if(k2_2 < 64U)
                                {
                                }
                                else
                                {

#line 2235
                                    break;
                                }

#line 2235
                                r_5[k2_2] = cmul_0(r_5[k2_2], float2(cr_1, ci_1));

#line 2235
                                float nr_1 = cr_1 * _S57 - ci_1 * _S58;

#line 2235
                                float _S59 = cr_1 * _S58 + ci_1 * _S57;

#line 2235
                                k2_2 = k2_2 + 1U;

#line 2235
                                cr_1 = nr_1;

#line 2235
                                ci_1 = _S59;

#line 2235
                            }

#line 2235
                            uint per_2 = 64U / _S22;

#line 2235
                            uint _S60 = max(0U, 1U);

#line 2235
                            uint blk2_2 = _S35 / _S60;

#line 2235
                            uint lane2_2 = _S35 % _S60;

#line 2235
                            for(;;)
                            {

#line 2235
                                thread array<float2, int(64)> out_1;

#line 2235
                                uint z_2 = 0U;

#line 2235
                                for(;;)
                                {

#line 2235
                                    if(z_2 < 64U)
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
                                uint p0_1 = computeWant_0(0U, 16U, 1024U, blk_2, lane_2, per_2, _S60, 16U, blk2_2, lane2_2);

#line 2235
                                uint _S61 = p0_1 & _S23;

#line 2235
                                uint _S62 = _S61 >> lgTB_1;

#line 2235
                                uint _S63 = _S62 * 1024U + ((p0_1 >> _S21) << lgTB_1) + (_S61 & spanMask_1);

#line 2235
                                uint c_3 = 0U;

#line 2235
                                for(;;)
                                {

#line 2235
                                    if(c_3 < 16U)
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
                                        stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_5[c_3 * 4U + j_2], &kernelContext_2);

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
                                        if(d_3 < 64U)
                                        {
                                        }
                                        else
                                        {

#line 2235
                                            break;
                                        }

#line 2235
                                        uint pz_1 = computeWant_0(d_3, 16U, 1024U, 0U, 0U, per_2, _S60, 16U, 0U, 0U);

#line 2235
                                        uint _S64 = pz_1 & _S23;

#line 2235
                                        uint iz_1 = _S64 >> lgTB_1;

#line 2235
                                        uint az_1 = iz_1 * 1024U + ((pz_1 >> _S21) << lgTB_1) + (_S64 & spanMask_1);

#line 2235
                                        uint i_7 = _S62 + iz_1;

#line 2235
                                        uint _S65 = c_3 * 4U;

#line 2235
                                        if(i_7 >= _S65)
                                        {

#line 2235
                                            isCand_0 = i_7 < ((c_3 + 1U) * 4U);

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
                                            float2 _S66 = stgGet_0(_S63 + az_1 - _S65 * 1024U, &kernelContext_2);

#line 2235
                                            out_1[d_3] = _S66;

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
                                    if(j_2 < 64U)
                                    {
                                    }
                                    else
                                    {

#line 2235
                                        break;
                                    }

#line 2235
                                    r_5[j_2] = out_1[j_2];

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
                innermost_0(&r_5);

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
            uint i_8;

#line 2235
            uint m2_0;

#line 2235
            uint s2_0;

#line 2235
            uint m3_0;

#line 2235
            uint s3_0;

#line 2235
            uint b_7;

#line 2235
            if(_S41 <= 4U)
            {

#line 2235
                if(_S35 < 4U)
                {

#line 2235
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + _S35] = _S42;

#line 2235
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U + _S35] = 4294967295U;

#line 2235
                }

#line 2235
                float2 _S67 = float2(0.0f, 0.0f);

#line 2235
                i_8 = 0U;

#line 2235
                d_3 = _S42;

#line 2235
                s0_1 = 4294967295U;

#line 2235
                float2 v0_0 = _S67;

#line 2235
                m1_1 = _S42;

#line 2235
                s1_0 = 4294967295U;

#line 2235
                float2 v1_0 = _S67;

#line 2235
                m2_0 = _S42;

#line 2235
                s2_0 = 4294967295U;

#line 2235
                float2 v2_0 = _S67;

#line 2235
                m3_0 = _S42;

#line 2235
                s3_0 = 4294967295U;

#line 2235
                float2 v3_0 = _S67;

#line 2235
                for(;;)
                {

#line 2235
                    if(i_8 < 64U)
                    {
                    }
                    else
                    {

#line 2235
                        break;
                    }

#line 2235
                    uint slot_1 = _S35 * 64U + i_8;

#line 2235
                    uint idx_1 = slotToIndex_0(slot_1);

#line 2235
                    if(idx_1 >= _S36)
                    {

#line 2235
                        isCand_0 = idx_1 < _S37;

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
                        float rx_0 = r_5[i_8].x;

#line 2235
                        float ry_0 = r_5[i_8].y;

#line 2235
                        uint mag_0 = (as_type<uint>((rx_0 * rx_0 + ry_0 * ry_0)));

#line 2235
                        uint off_0 = idx_1 - _S36 + (&kernelContext_2)->_binPhase_0;

#line 2235
                        if(_S41 == 1U)
                        {

#line 2235
                            b_7 = 0U;

#line 2235
                        }
                        else
                        {

#line 2235
                            if(_S40 >= int(0))
                            {

#line 2235
                                b_7 = off_0 >> uint(_S40);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S68 = off_0 / _S39;

#line 2235
                                b_7 = _S68;

#line 2235
                            }

#line 2235
                        }

#line 2235
                        if(b_7 == 0U)
                        {

#line 2235
                            _S24 = mag_0 > d_3;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S24 = false;

#line 2235
                        }

#line 2235
                        float2 v0_1;

#line 2235
                        if(_S24)
                        {

#line 2235
                            float2 _S69 = float2(rx_0, ry_0);

#line 2235
                            m0_0 = mag_0;

#line 2235
                            s0_0 = slot_1;

#line 2235
                            v0_1 = _S69;

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
                        if(_S41 >= 2U)
                        {

#line 2235
                            _S25 = b_7 == 1U;

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
                            _S26 = mag_0 > m1_1;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S26 = false;

#line 2235
                        }

#line 2235
                        uint s1_1;

#line 2235
                        float2 v1_1;

#line 2235
                        if(_S26)
                        {

#line 2235
                            float2 _S70 = float2(rx_0, ry_0);

#line 2235
                            m1_0 = mag_0;

#line 2235
                            s1_1 = slot_1;

#line 2235
                            v1_1 = _S70;

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
                        if(_S41 >= 3U)
                        {

#line 2235
                            _S27 = b_7 == 2U;

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
                            _S28 = mag_0 > m2_0;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S28 = false;

#line 2235
                        }

#line 2235
                        uint m2_1;

#line 2235
                        uint s2_1;

#line 2235
                        float2 v2_1;

#line 2235
                        if(_S28)
                        {

#line 2235
                            float2 _S71 = float2(rx_0, ry_0);

#line 2235
                            m2_1 = mag_0;

#line 2235
                            s2_1 = slot_1;

#line 2235
                            v2_1 = _S71;

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
                        if(_S41 >= 4U)
                        {

#line 2235
                            _S29 = b_7 == 3U;

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
                            _S30 = mag_0 > m3_0;

#line 2235
                        }
                        else
                        {

#line 2235
                            _S30 = false;

#line 2235
                        }

#line 2235
                        uint m3_1;

#line 2235
                        uint s3_1;

#line 2235
                        float2 v3_1;

#line 2235
                        if(_S30)
                        {

#line 2235
                            float2 _S72 = float2(rx_0, ry_0);

#line 2235
                            m3_1 = mag_0;

#line 2235
                            s3_1 = slot_1;

#line 2235
                            v3_1 = _S72;

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
                    i_8 = i_8 + 1U;

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                uint wm0_0 = simd_max(d_3);

#line 2235
                bool _S73 = simd_is_first();

#line 2235
                if(_S73)
                {

#line 2235
                    isCand_0 = wm0_0 > _S42;

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
                    uint _S74 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0])), wm0_0, memory_order_relaxed);

#line 2235
                }

#line 2235
                bool _S75 = _S41 >= 2U;

#line 2235
                if(_S75)
                {

#line 2235
                    uint wm1_0 = simd_max(m1_1);

#line 2235
                    bool _S76 = simd_is_first();

#line 2235
                    if(_S76)
                    {

#line 2235
                        _S24 = wm1_0 > _S42;

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
                        uint _S77 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 1U])), wm1_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                bool _S78 = _S41 >= 3U;

#line 2235
                if(_S78)
                {

#line 2235
                    uint wm2_0 = simd_max(m2_0);

#line 2235
                    bool _S79 = simd_is_first();

#line 2235
                    if(_S79)
                    {

#line 2235
                        _S24 = wm2_0 > _S42;

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
                        uint _S80 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 2U])), wm2_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                bool _S81 = _S41 >= 4U;

#line 2235
                if(_S81)
                {

#line 2235
                    uint wm3_0 = simd_max(m3_0);

#line 2235
                    bool _S82 = simd_is_first();

#line 2235
                    if(_S82)
                    {

#line 2235
                        _S24 = wm3_0 > _S42;

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
                        uint _S83 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 3U])), wm3_0, memory_order_relaxed);

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
                    _S24 = d_3 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0];

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
                    b_7 = s0_1;

#line 2235
                }
                else
                {

#line 2235
                    b_7 = 4294967295U;

#line 2235
                }

#line 2235
                if(_S75)
                {

#line 2235
                    _S25 = s1_0 != 4294967295U;

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
                    _S26 = m1_1 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 1U];

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
                if(_S78)
                {

#line 2235
                    _S27 = s2_0 != 4294967295U;

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
                    _S28 = m2_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 2U];

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
                if(_S81)
                {

#line 2235
                    _S29 = s3_0 != 4294967295U;

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
                    _S30 = m3_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 3U];

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
                uint ww0_0 = simd_min(b_7);

#line 2235
                bool _S84 = simd_is_first();

#line 2235
                bool _S85;

#line 2235
                if(_S84)
                {

#line 2235
                    _S85 = ww0_0 != 4294967295U;

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
                    uint _S86 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U])), ww0_0, memory_order_relaxed);

#line 2235
                }

#line 2235
                bool _S87;

#line 2235
                if(_S75)
                {

#line 2235
                    uint ww1_0 = simd_min(m0_0);

#line 2235
                    bool _S88 = simd_is_first();

#line 2235
                    if(_S88)
                    {

#line 2235
                        _S87 = ww1_0 != 4294967295U;

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
                        uint _S89 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 5U])), ww1_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                if(_S78)
                {

#line 2235
                    uint ww2_0 = simd_min(s0_0);

#line 2235
                    bool _S90 = simd_is_first();

#line 2235
                    if(_S90)
                    {

#line 2235
                        _S87 = ww2_0 != 4294967295U;

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
                        uint _S91 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 6U])), ww2_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                if(_S81)
                {

#line 2235
                    uint ww3_0 = simd_min(m1_0);

#line 2235
                    bool _S92 = simd_is_first();

#line 2235
                    if(_S92)
                    {

#line 2235
                        _S87 = ww3_0 != 4294967295U;

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
                        uint _S93 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 7U])), ww3_0, memory_order_relaxed);

#line 2235
                    }

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                uint baseOut_0 = _S34 * _S41;

#line 2235
                if(b_7 != 4294967295U)
                {

#line 2235
                    _S87 = b_7 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U];

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
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+baseOut_0) = int(slotToIndex_0(b_7));

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+baseOut_0) = packed_float2(v0_0) ;

#line 2235
                }

#line 2235
                bool _S94;

#line 2235
                if(_S75)
                {

#line 2235
                    _S94 = m0_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S94 = false;

#line 2235
                }

#line 2235
                bool _S95;

#line 2235
                if(_S94)
                {

#line 2235
                    _S95 = m0_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 5U];

#line 2235
                }
                else
                {

#line 2235
                    _S95 = false;

#line 2235
                }

#line 2235
                if(_S95)
                {

#line 2235
                    uint _S96 = baseOut_0 + 1U;

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S96) = int(slotToIndex_0(m0_0));

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S96) = packed_float2(v1_0) ;

#line 2235
                }

#line 2235
                bool _S97;

#line 2235
                if(_S78)
                {

#line 2235
                    _S97 = s0_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S97 = false;

#line 2235
                }

#line 2235
                bool _S98;

#line 2235
                if(_S97)
                {

#line 2235
                    _S98 = s0_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 6U];

#line 2235
                }
                else
                {

#line 2235
                    _S98 = false;

#line 2235
                }

#line 2235
                if(_S98)
                {

#line 2235
                    uint _S99 = baseOut_0 + 2U;

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S99) = int(slotToIndex_0(s0_0));

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S99) = packed_float2(v2_0) ;

#line 2235
                }

#line 2235
                bool _S100;

#line 2235
                if(_S81)
                {

#line 2235
                    _S100 = m1_0 != 4294967295U;

#line 2235
                }
                else
                {

#line 2235
                    _S100 = false;

#line 2235
                }

#line 2235
                bool _S101;

#line 2235
                if(_S100)
                {

#line 2235
                    _S101 = m1_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 7U];

#line 2235
                }
                else
                {

#line 2235
                    _S101 = false;

#line 2235
                }

#line 2235
                if(_S101)
                {

#line 2235
                    uint _S102 = baseOut_0 + 3U;

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S102) = int(slotToIndex_0(m1_0));

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S102) = packed_float2(v3_0) ;

#line 2235
                }

#line 2235
                bool _S103;

#line 2235
                if(_S35 < _S41)
                {

#line 2235
                    _S103 = ((*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U + _S35]) == 4294967295U;

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
                    uint _S104 = baseOut_0 + _S35;

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S104) = int(-1);

#line 2235
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S104) = packed_float2(_S67) ;

#line 2235
                }

#line 2235
            }
            else
            {

#line 2235
                d_3 = _S35;

#line 2235
                for(;;)
                {

#line 2235
                    if(d_3 < _S41)
                    {
                    }
                    else
                    {

#line 2235
                        break;
                    }

#line 2235
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + d_3] = _S42;

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
                    if(s0_1 < 64U)
                    {
                    }
                    else
                    {

#line 2235
                        break;
                    }

#line 2235
                    uint idx_2 = slotToIndex_0(_S35 * 64U + s0_1);

#line 2235
                    if(idx_2 >= _S36)
                    {

#line 2235
                        isCand_0 = idx_2 < _S37;

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
                        float rx_1 = r_5[s0_1].x;

#line 2235
                        float ry_1 = r_5[s0_1].y;

#line 2235
                        uint mag_1 = (as_type<uint>((rx_1 * rx_1 + ry_1 * ry_1)));

#line 2235
                        if(mag_1 > _S42)
                        {

#line 2235
                            uint off_1 = idx_2 - _S36 + (&kernelContext_2)->_binPhase_0;

#line 2235
                            if(_S40 >= int(0))
                            {

#line 2235
                                m2_0 = off_1 >> uint(_S40);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S105 = off_1 / _S39;

#line 2235
                                m2_0 = _S105;

#line 2235
                            }

#line 2235
                            uint _S106 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0])), mag_1, memory_order_relaxed);

#line 2235
                            uint bit_0 = 1U << (s0_1 & 31U);

#line 2235
                            if(s0_1 < 32U)
                            {

#line 2235
                                i_8 = m1_1 | bit_0;

#line 2235
                                s2_0 = s1_0;

#line 2235
                            }
                            else
                            {

#line 2235
                                uint aboveHi_0 = s1_0 | bit_0;

#line 2235
                                i_8 = m1_1;

#line 2235
                                s2_0 = aboveHi_0;

#line 2235
                            }

#line 2235
                        }
                        else
                        {

#line 2235
                            i_8 = m1_1;

#line 2235
                            s2_0 = s1_0;

#line 2235
                        }

#line 2235
                    }
                    else
                    {

#line 2235
                        i_8 = m1_1;

#line 2235
                        s2_0 = s1_0;

#line 2235
                    }

#line 2235
                    s0_1 = s0_1 + 1U;

#line 2235
                    m1_1 = i_8;

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
                    i_8 = 0U;

#line 2235
                    m2_0 = 0U;

#line 2235
                    s2_0 = 0U;

#line 2235
                    for(;;)
                    {

#line 2235
                        if(i_8 < 64U)
                        {
                        }
                        else
                        {

#line 2235
                            break;
                        }

#line 2235
                        uint bit_1 = 1U << (i_8 & 31U);

#line 2235
                        bool _S107 = i_8 < 32U;

#line 2235
                        if(_S107)
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
                            uint off_2 = slotToIndex_0(_S35 * 64U + i_8) - _S36 + (&kernelContext_2)->_binPhase_0;

#line 2235
                            if(_S40 >= int(0))
                            {

#line 2235
                                m3_0 = off_2 >> uint(_S40);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S108 = off_2 / _S39;

#line 2235
                                m3_0 = _S108;

#line 2235
                            }

#line 2235
                            float rx_2 = r_5[i_8].x;

#line 2235
                            float ry_2 = r_5[i_8].y;

#line 2235
                            if((as_type<uint>((rx_2 * rx_2 + ry_2 * ry_2))) == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m3_0])
                            {

#line 2235
                                if(_S107)
                                {

#line 2235
                                    s3_0 = m2_0 | bit_1;

#line 2235
                                    b_7 = s2_0;

#line 2235
                                }
                                else
                                {

#line 2235
                                    uint candHi_0 = s2_0 | bit_1;

#line 2235
                                    s3_0 = m2_0;

#line 2235
                                    b_7 = candHi_0;

#line 2235
                                }

#line 2235
                            }
                            else
                            {

#line 2235
                                s3_0 = m2_0;

#line 2235
                                b_7 = s2_0;

#line 2235
                            }

#line 2235
                        }
                        else
                        {

#line 2235
                            s3_0 = m2_0;

#line 2235
                            b_7 = s2_0;

#line 2235
                        }

#line 2235
                        i_8 = i_8 + 1U;

#line 2235
                        m2_0 = s3_0;

#line 2235
                        s2_0 = b_7;

#line 2235
                    }

#line 2235
                    s3_0 = m2_0;

#line 2235
                    b_7 = s2_0;

#line 2235
                }
                else
                {

#line 2235
                    s3_0 = 0U;

#line 2235
                    b_7 = 0U;

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                m3_0 = _S35;

#line 2235
                for(;;)
                {

#line 2235
                    if(m3_0 < _S41)
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
                bool _S109 = (s3_0 | b_7) != 0U;

#line 2235
                if(_S109)
                {

#line 2235
                    i_8 = 0U;

#line 2235
                    for(;;)
                    {

#line 2235
                        if(i_8 < 64U)
                        {
                        }
                        else
                        {

#line 2235
                            break;
                        }

#line 2235
                        uint bit_2 = 1U << (i_8 & 31U);

#line 2235
                        if(i_8 < 32U)
                        {

#line 2235
                            isCand_0 = (s3_0 & bit_2) != 0U;

#line 2235
                        }
                        else
                        {

#line 2235
                            isCand_0 = (b_7 & bit_2) != 0U;

#line 2235
                        }

#line 2235
                        if(isCand_0)
                        {

#line 2235
                            uint _S110 = _S35 * 64U + i_8;

#line 2235
                            uint off_3 = slotToIndex_0(_S110) - _S36 + (&kernelContext_2)->_binPhase_0;

#line 2235
                            if(_S40 >= int(0))
                            {

#line 2235
                                m2_0 = off_3 >> uint(_S40);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S111 = off_3 / _S39;

#line 2235
                                m2_0 = _S111;

#line 2235
                            }

#line 2235
                            uint _S112 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0])), _S110, memory_order_relaxed);

#line 2235
                        }

#line 2235
                        i_8 = i_8 + 1U;

#line 2235
                    }

#line 2235
                }

#line 2235
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2235
                if(_S109)
                {

#line 2235
                    i_8 = 0U;

#line 2235
                    for(;;)
                    {

#line 2235
                        if(i_8 < 64U)
                        {
                        }
                        else
                        {

#line 2235
                            break;
                        }

#line 2235
                        uint bit_3 = 1U << (i_8 & 31U);

#line 2235
                        if(i_8 < 32U)
                        {

#line 2235
                            isCand_0 = (s3_0 & bit_3) != 0U;

#line 2235
                        }
                        else
                        {

#line 2235
                            isCand_0 = (b_7 & bit_3) != 0U;

#line 2235
                        }

#line 2235
                        if(isCand_0)
                        {

#line 2235
                            uint _S113 = _S35 * 64U + i_8;

#line 2235
                            uint idx_3 = slotToIndex_0(_S113);

#line 2235
                            uint off_4 = idx_3 - _S36 + (&kernelContext_2)->_binPhase_0;

#line 2235
                            if(_S40 >= int(0))
                            {

#line 2235
                                m2_0 = off_4 >> uint(_S40);

#line 2235
                            }
                            else
                            {

#line 2235
                                uint _S114 = off_4 / _S39;

#line 2235
                                m2_0 = _S114;

#line 2235
                            }

#line 2235
                            if(((*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0]) == _S113)
                            {

#line 2235
                                uint o_2 = _S34 * _S41 + m2_0;

#line 2235
                                *((&kernelContext_2)->entryPointParams_peakIdx_0+o_2) = int(idx_3);

#line 2235
                                *((&kernelContext_2)->entryPointParams_peakVal_0+o_2) = packed_float2(float2(r_5[i_8].x, r_5[i_8].y)) ;

#line 2235
                            }

#line 2235
                        }

#line 2235
                        i_8 = i_8 + 1U;

#line 2235
                    }

#line 2235
                }

#line 2235
                m2_0 = _S35;

#line 2235
                for(;;)
                {

#line 2235
                    if(m2_0 < _S41)
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
                        uint _S115 = _S34 * _S41 + m2_0;

#line 2235
                        *((&kernelContext_2)->entryPointParams_peakIdx_0+_S115) = int(-1);

#line 2235
                        *((&kernelContext_2)->entryPointParams_peakVal_0+_S115) = packed_float2(float2(0.0f, 0.0f)) ;

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
        i_5 = i_5 + (&kernelContext_2)->entryPointParams_0->gridSize_0;

#line 2231
    }

#line 2240
    return;
}
