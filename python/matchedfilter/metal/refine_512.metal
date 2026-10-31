#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
#ifndef MF_ROW_WINDOWS
#define MF_ROW_WINDOWS 0u
#endif
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


#line 85 "twiddle.slang"
uint mfRowWindowsFlag_0()
{
    ;
    uint _S2 = ((MF_ROW_WINDOWS));

#line 88
    return _S2;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint ntmpl_0;
    uint winStart_0;
    uint winEnd_0;
    uint binsize_0;
    int binShift_0;
    uint nbins_0;
    uint thrBits_0;
    uint gridSize_0;
};


#line 312 "mm_512_refineListed.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_survivors_0;
    uint device* entryPointParams_count_0;
    uint device* entryPointParams_rowWin_0;
    uint _stgBase_0;
    uint _binPhase_0;
    uint _tid_0;
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 228
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 90 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 231 "mm_512_refineListed.slang"
    if(_S3 == 0U)
    {

#line 231
        return;
    }

#line 232
    uint _S4 = 3U * d_0;

#line 232
    *winStart_1 = rowWin_0[_S4];
    *winEnd_1 = rowWin_0[_S4 + 1U];
    kernelContext_0->_binPhase_0 = rowWin_0[_S4 + 2U];
    return;
}


#line 58 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S5 = ((MF_DATA_STRIDE));

#line 61
    return _S5;
}


#line 174 "mm_512_refineListed.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 174
    return float2(*(b_0+i_0)) ;
}


#line 324
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 324
    float _S6 = a_0.x;

#line 324
    float _S7 = b_1.x;

#line 324
    float _S8 = a_0.y;

#line 324
    float _S9 = b_1.y;

#line 324
    return float2(_S6 * _S7 + _S8 * _S9, _S8 * _S7 - _S6 * _S9);
}


#line 583
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 585
    float2 t1_0 = *a_1 - *c_0;

#line 585
    float2 t2_0 = *b_2 + *d_1;

#line 585
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 587
    *b_2 = t1_0 + j3_0;

#line 587
    *c_0 = t0_0 - t2_0;

#line 587
    *d_1 = t1_0 - j3_0;
    return;
}


#line 323
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


#line 74 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S15 = ((MF_ACCURATE_TRIG));

#line 77
    return _S15;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S16 = mfAccurateTrigFlag_0();

#line 103
    if(_S16 == 0U)
    {

#line 104
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S17 = float(quadrant_0);
    float x_0 = angle_0 - _S17 * 1.57079625129699707f - _S17 * 7.54978941586159635e-08f;
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


#line 325 "mm_512_refineListed.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S18 = max(TB_0, 1U);

#line 327
    uint j_0 = d_2 / _S18;

#line 327
    uint m_0 = d_2 % _S18;

#line 327
    uint _S19;
    if(TB_0 <= 16U)
    {

#line 328
        _S19 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 328
    }
    else
    {

#line 328
        _S19 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 328
    }

#line 328
    return _S19;
}


#line 312
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 312
    uint _S20 = 2U * i_1;

#line 312
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20] = (as_type<uint>((v_0.x)));

#line 312
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20 + 1U] = (as_type<uint>((v_0.y)));

#line 312
    return;
}


#line 313
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_2)
{

#line 313
    uint _S21 = 2U * i_2;

#line 313
    return float2((as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S21]))), (as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S21 + 1U]))));
}


#line 594
void dft2_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    float2 a_3 = (*r_1)[o_0];

#line 596
    float2 b_4 = (*r_1)[o_0 + 1U];

#line 596
    (*r_1)[o_0] = (*r_1)[o_0] + (*r_1)[o_0 + 1U];

#line 596
    (*r_1)[o_0 + 1U] = a_3 - b_4;
    return;
}


#line 722
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 722
    uint b_5 = 0U;

#line 732
    for(;;)
    {

#line 732
        if(b_5 < 8U)
        {
        }
        else
        {

#line 732
            break;
        }

#line 732
        dft2_0(r_2, b_5 * 2U);

#line 732
        b_5 = b_5 + 1U;

#line 732
    }

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
        _S22 = 4U;

#line 869
    }
    else
    {

#line 869
        _S22 = 1U;

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


#line 2193
[[kernel]] void refineListedBounded(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]], uint device* entryPointParams_rowWin_1 [[buffer(7)]])
{

#line 2193
    uint k2_1;

#line 2193
    uint _S23;

#line 2193
    uint _S24;

#line 2193
    uint _S25;

#line 2193
    uint d_3;

#line 2193
    uint j_1;

#line 2193
    uint d_4;

#line 2193
    uint m0_0;

#line 2193
    uint s0_0;

#line 2193
    uint m1_0;

#line 2193
    bool _S26;

#line 2193
    bool _S27;

#line 2193
    bool _S28;

#line 2193
    bool _S29;

#line 2193
    bool _S30;

#line 2193
    bool _S31;

#line 2193
    bool _S32;

#line 2193
    thread KernelContext_0 kernelContext_3;

#line 2193
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 2193
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2193
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2193
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2193
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2193
    (&kernelContext_3)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2193
    (&kernelContext_3)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2193
    (&kernelContext_3)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 2193
    threadgroup array<uint, int(1024)> stg_1;

#line 2193
    (&kernelContext_3)->stg_0 = &stg_1;

#line 2193
    (&kernelContext_3)->_binPhase_0 = 0U;

#line 2203
    uint _S33 = entryPointParams_count_1[int(0)];

#line 2203
    uint i_4 = gid_0.x;
    for(;;)
    {

#line 2204
        if(i_4 < _S33)
        {
        }
        else
        {

#line 2204
            break;
        }

#line 2205
        (&kernelContext_3)->_stgBase_0 = 0U;
        uint pair_0 = (&kernelContext_3)->entryPointParams_survivors_0[i_4];

#line 2206
        thread uint ws_0 = (&kernelContext_3)->entryPointParams_0->winStart_0;

#line 2206
        thread uint we_0 = (&kernelContext_3)->entryPointParams_0->winEnd_0;
        uint _S34 = pair_0 / (&kernelContext_3)->entryPointParams_0->ntmpl_0;

#line 2207
        rowWindow_0(_S34, &ws_0, &we_0, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);
        uint _S35 = lid_0.x;

#line 2208
        uint _S36 = ws_0;

#line 2208
        uint _S37 = we_0;

#line 2208
        uint _S38 = (&kernelContext_3)->entryPointParams_0->ntmpl_0;

#line 2208
        uint _S39 = (&kernelContext_3)->entryPointParams_0->binsize_0;

#line 2208
        int _S40 = (&kernelContext_3)->entryPointParams_0->binShift_0;

#line 2208
        uint _S41 = (&kernelContext_3)->entryPointParams_0->nbins_0;

#line 2208
        uint _S42 = (&kernelContext_3)->entryPointParams_0->thrBits_0;

#line 2208
        for(;;)
        {

#line 2208
            for(;;)
            {

#line 2208
                (&kernelContext_3)->_tid_0 = _S35;

#line 2208
                uint _S43 = pair_0 / _S38;

#line 2208
                uint _S44 = pair_0 % _S38;

#line 2208
                thread array<float2, int(16)> r_3;

#line 2208
                uint n2_0 = 0U;

#line 2208
                for(;;)
                {

#line 2208
                    if(n2_0 < 16U)
                    {
                    }
                    else
                    {

#line 2208
                        break;
                    }

#line 2208
                    uint idx_0 = _S35 + 32U * n2_0;

#line 2208
                    uint _S45 = mfDataStrideFlag_0();

#line 2208
                    if(_S45 != 0U)
                    {

#line 2208
                        uint _S46 = mfDataStrideFlag_0();

#line 2208
                        k2_1 = _S46;

#line 2208
                    }
                    else
                    {

#line 2208
                        k2_1 = 512U;

#line 2208
                    }

#line 2208
                    r_3[n2_0] = cmulConj_0(cload_0((&kernelContext_3)->entryPointParams_data_0, _S43 * k2_1 + idx_0), cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S44 * 512U + idx_0));

#line 2208
                    n2_0 = n2_0 + 1U;

#line 2208
                }

#line 2208
                for(;;)
                {

#line 2208
                    for(;;)
                    {

#line 2208
                        for(;;)
                        {

#line 2208
                            for(;;)
                            {

#line 2208
                                uint lgTB_0 = firstbithigh_0(32U);

#line 2208
                                _S23 = lgTB_0;

#line 2208
                                uint lgLn_0 = firstbithigh_0(512U);

#line 2208
                                uint blk_1 = _S35 >> lgTB_0;

#line 2208
                                uint lane_1 = _S35 & 31U;

#line 2208
                                dft16_0(&r_3);

#line 2208
                                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 512.0f);

#line 2208
                                float _S47 = tw_0.x;

#line 2208
                                float _S48 = tw_0.y;

#line 2208
                                k2_1 = 0U;

#line 2208
                                float cr_0 = 1.0f;

#line 2208
                                float ci_0 = 0.0f;

#line 2208
                                for(;;)
                                {

#line 2208
                                    if(k2_1 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2208
                                        break;
                                    }

#line 2208
                                    r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2208
                                    float nr_0 = cr_0 * _S47 - ci_0 * _S48;

#line 2208
                                    float _S49 = cr_0 * _S48 + ci_0 * _S47;

#line 2208
                                    k2_1 = k2_1 + 1U;

#line 2208
                                    cr_0 = nr_0;

#line 2208
                                    ci_0 = _S49;

#line 2208
                                }

#line 2208
                                uint per_1 = 16U / max(32U, 1U);

#line 2208
                                uint _S50 = max(2U, 1U);

#line 2208
                                _S24 = _S50;

#line 2208
                                uint blk2_1 = _S35 / _S50;

#line 2208
                                uint lane2_1 = _S35 % _S50;

#line 2208
                                for(;;)
                                {

#line 2208
                                    thread array<float2, int(16)> out_0;

#line 2208
                                    uint z_1 = 0U;

#line 2208
                                    for(;;)
                                    {

#line 2208
                                        if(z_1 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2208
                                            break;
                                        }

#line 2208
                                        out_0[z_1] = float2(0.0f, 0.0f);

#line 2208
                                        z_1 = z_1 + 1U;

#line 2208
                                    }

#line 2208
                                    uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2208
                                    _S25 = spanMask_0;

#line 2208
                                    uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2208
                                    uint p0_0 = computeWant_0(0U, 32U, 512U, blk_1, lane_1, per_1, _S50, 32U, blk2_1, lane2_1);

#line 2208
                                    uint _S51 = p0_0 & lenMask_0;

#line 2208
                                    uint _S52 = (_S51 >> lgTB_0) * 32U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S51 & spanMask_0);

#line 2208
                                    uint c_2 = 0U;

#line 2208
                                    for(;;)
                                    {

#line 2208
                                        if(c_2 < 1U)
                                        {
                                        }
                                        else
                                        {

#line 2208
                                            break;
                                        }

#line 2208
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2208
                                        j_1 = 0U;

#line 2208
                                        for(;;)
                                        {

#line 2208
                                            if(j_1 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 2208
                                                break;
                                            }

#line 2208
                                            stgPut_0(j_1 * 32U + (&kernelContext_3)->_tid_0, r_3[c_2 * 16U + j_1], &kernelContext_3);

#line 2208
                                            j_1 = j_1 + 1U;

#line 2208
                                        }

#line 2208
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2208
                                        d_3 = 0U;

#line 2208
                                        for(;;)
                                        {

#line 2208
                                            if(d_3 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 2208
                                                break;
                                            }

#line 2208
                                            uint pz_0 = computeWant_0(d_3, 32U, 512U, 0U, 0U, per_1, _S50, 32U, 0U, 0U);

#line 2208
                                            uint _S53 = pz_0 & lenMask_0;

#line 2208
                                            uint az_0 = (_S53 >> lgTB_0) * 32U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S53 & spanMask_0);

#line 2208
                                            float2 _S54 = stgGet_0(_S52 + az_0 - c_2 * 16U * 32U, &kernelContext_3);

#line 2208
                                            out_0[d_3] = _S54;

#line 2208
                                            d_3 = d_3 + 1U;

#line 2208
                                        }

#line 2208
                                        c_2 = c_2 + 1U;

#line 2208
                                    }

#line 2208
                                    d_3 = 0U;

#line 2208
                                    for(;;)
                                    {

#line 2208
                                        if(d_3 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2208
                                            break;
                                        }

#line 2208
                                        r_3[d_3] = out_0[d_3];

#line 2208
                                        d_3 = d_3 + 1U;

#line 2208
                                    }

#line 2208
                                    break;
                                }

#line 2208
                                break;
                            }

#line 2208
                            break;
                        }

#line 2208
                        for(;;)
                        {

#line 2208
                            for(;;)
                            {

#line 2208
                                uint lgTB_1 = firstbithigh_0(2U);

#line 2208
                                uint blk_2 = _S35 >> lgTB_1;

#line 2208
                                uint lane_2 = _S35 & 1U;

#line 2208
                                dft16_0(&r_3);

#line 2208
                                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 32.0f);

#line 2208
                                float _S55 = tw_1.x;

#line 2208
                                float _S56 = tw_1.y;

#line 2208
                                uint k2_2 = 0U;

#line 2208
                                float cr_1 = 1.0f;

#line 2208
                                float ci_1 = 0.0f;

#line 2208
                                for(;;)
                                {

#line 2208
                                    if(k2_2 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2208
                                        break;
                                    }

#line 2208
                                    r_3[k2_2] = cmul_0(r_3[k2_2], float2(cr_1, ci_1));

#line 2208
                                    float nr_1 = cr_1 * _S55 - ci_1 * _S56;

#line 2208
                                    float _S57 = cr_1 * _S56 + ci_1 * _S55;

#line 2208
                                    k2_2 = k2_2 + 1U;

#line 2208
                                    cr_1 = nr_1;

#line 2208
                                    ci_1 = _S57;

#line 2208
                                }

#line 2208
                                uint per_2 = 16U / _S24;

#line 2208
                                uint _S58 = max(0U, 1U);

#line 2208
                                uint blk2_2 = _S35 / _S58;

#line 2208
                                uint lane2_2 = _S35 % _S58;

#line 2208
                                for(;;)
                                {

#line 2208
                                    thread array<float2, int(16)> out_1;

#line 2208
                                    uint z_2 = 0U;

#line 2208
                                    for(;;)
                                    {

#line 2208
                                        if(z_2 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2208
                                            break;
                                        }

#line 2208
                                        out_1[z_2] = float2(0.0f, 0.0f);

#line 2208
                                        z_2 = z_2 + 1U;

#line 2208
                                    }

#line 2208
                                    uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2208
                                    uint p0_1 = computeWant_0(0U, 2U, 32U, blk_2, lane_2, per_2, _S58, 2U, blk2_2, lane2_2);

#line 2208
                                    uint _S59 = p0_1 & _S25;

#line 2208
                                    uint _S60 = (_S59 >> lgTB_1) * 32U + ((p0_1 >> _S23) << lgTB_1) + (_S59 & spanMask_1);

#line 2208
                                    uint c_3 = 0U;

#line 2208
                                    for(;;)
                                    {

#line 2208
                                        if(c_3 < 1U)
                                        {
                                        }
                                        else
                                        {

#line 2208
                                            break;
                                        }

#line 2208
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2208
                                        j_1 = 0U;

#line 2208
                                        for(;;)
                                        {

#line 2208
                                            if(j_1 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 2208
                                                break;
                                            }

#line 2208
                                            stgPut_0(j_1 * 32U + (&kernelContext_3)->_tid_0, r_3[c_3 * 16U + j_1], &kernelContext_3);

#line 2208
                                            j_1 = j_1 + 1U;

#line 2208
                                        }

#line 2208
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2208
                                        d_4 = 0U;

#line 2208
                                        for(;;)
                                        {

#line 2208
                                            if(d_4 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 2208
                                                break;
                                            }

#line 2208
                                            uint pz_1 = computeWant_0(d_4, 2U, 32U, 0U, 0U, per_2, _S58, 2U, 0U, 0U);

#line 2208
                                            uint _S61 = pz_1 & _S25;

#line 2208
                                            uint az_1 = (_S61 >> lgTB_1) * 32U + ((pz_1 >> _S23) << lgTB_1) + (_S61 & spanMask_1);

#line 2208
                                            float2 _S62 = stgGet_0(_S60 + az_1 - c_3 * 16U * 32U, &kernelContext_3);

#line 2208
                                            out_1[d_4] = _S62;

#line 2208
                                            d_4 = d_4 + 1U;

#line 2208
                                        }

#line 2208
                                        c_3 = c_3 + 1U;

#line 2208
                                    }

#line 2208
                                    j_1 = 0U;

#line 2208
                                    for(;;)
                                    {

#line 2208
                                        if(j_1 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2208
                                            break;
                                        }

#line 2208
                                        r_3[j_1] = out_1[j_1];

#line 2208
                                        j_1 = j_1 + 1U;

#line 2208
                                    }

#line 2208
                                    break;
                                }

#line 2208
                                break;
                            }

#line 2208
                            break;
                        }

#line 2208
                        break;
                    }

#line 2208
                    innermost_0(&r_3);

#line 2208
                    break;
                }

#line 2208
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2208
                uint s0_1;

#line 2208
                uint m1_1;

#line 2208
                uint s1_0;

#line 2208
                uint i_5;

#line 2208
                uint m2_0;

#line 2208
                uint s2_0;

#line 2208
                uint m3_0;

#line 2208
                uint s3_0;

#line 2208
                uint b_6;

#line 2208
                bool isCand_0;

#line 2208
                if(_S41 <= 4U)
                {

#line 2208
                    if(_S35 < 4U)
                    {

#line 2208
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + _S35] = _S42;

#line 2208
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _S35] = 4294967295U;

#line 2208
                    }

#line 2208
                    float2 _S63 = float2(0.0f, 0.0f);

#line 2208
                    i_5 = 0U;

#line 2208
                    d_4 = _S42;

#line 2208
                    s0_1 = 4294967295U;

#line 2208
                    float2 v0_0 = _S63;

#line 2208
                    m1_1 = _S42;

#line 2208
                    s1_0 = 4294967295U;

#line 2208
                    float2 v1_0 = _S63;

#line 2208
                    m2_0 = _S42;

#line 2208
                    s2_0 = 4294967295U;

#line 2208
                    float2 v2_0 = _S63;

#line 2208
                    m3_0 = _S42;

#line 2208
                    s3_0 = 4294967295U;

#line 2208
                    float2 v3_0 = _S63;

#line 2208
                    for(;;)
                    {

#line 2208
                        if(i_5 < 16U)
                        {
                        }
                        else
                        {

#line 2208
                            break;
                        }

#line 2208
                        uint slot_1 = _S35 * 16U + i_5;

#line 2208
                        uint idx_1 = slotToIndex_0(slot_1);

#line 2208
                        if(idx_1 >= _S36)
                        {

#line 2208
                            isCand_0 = idx_1 < _S37;

#line 2208
                        }
                        else
                        {

#line 2208
                            isCand_0 = false;

#line 2208
                        }

#line 2208
                        if(isCand_0)
                        {

#line 2208
                            float rx_0 = r_3[i_5].x;

#line 2208
                            float ry_0 = r_3[i_5].y;

#line 2208
                            uint mag_0 = (as_type<uint>((rx_0 * rx_0 + ry_0 * ry_0)));

#line 2208
                            uint off_0 = idx_1 - _S36 + (&kernelContext_3)->_binPhase_0;

#line 2208
                            if(_S41 == 1U)
                            {

#line 2208
                                b_6 = 0U;

#line 2208
                            }
                            else
                            {

#line 2208
                                if(_S40 >= int(0))
                                {

#line 2208
                                    b_6 = off_0 >> uint(_S40);

#line 2208
                                }
                                else
                                {

#line 2208
                                    uint _S64 = off_0 / _S39;

#line 2208
                                    b_6 = _S64;

#line 2208
                                }

#line 2208
                            }

#line 2208
                            if(b_6 == 0U)
                            {

#line 2208
                                _S26 = mag_0 > d_4;

#line 2208
                            }
                            else
                            {

#line 2208
                                _S26 = false;

#line 2208
                            }

#line 2208
                            float2 v0_1;

#line 2208
                            if(_S26)
                            {

#line 2208
                                float2 _S65 = float2(rx_0, ry_0);

#line 2208
                                m0_0 = mag_0;

#line 2208
                                s0_0 = slot_1;

#line 2208
                                v0_1 = _S65;

#line 2208
                            }
                            else
                            {

#line 2208
                                m0_0 = d_4;

#line 2208
                                s0_0 = s0_1;

#line 2208
                                v0_1 = v0_0;

#line 2208
                            }

#line 2208
                            if(_S41 >= 2U)
                            {

#line 2208
                                _S27 = b_6 == 1U;

#line 2208
                            }
                            else
                            {

#line 2208
                                _S27 = false;

#line 2208
                            }

#line 2208
                            if(_S27)
                            {

#line 2208
                                _S28 = mag_0 > m1_1;

#line 2208
                            }
                            else
                            {

#line 2208
                                _S28 = false;

#line 2208
                            }

#line 2208
                            uint s1_1;

#line 2208
                            float2 v1_1;

#line 2208
                            if(_S28)
                            {

#line 2208
                                float2 _S66 = float2(rx_0, ry_0);

#line 2208
                                m1_0 = mag_0;

#line 2208
                                s1_1 = slot_1;

#line 2208
                                v1_1 = _S66;

#line 2208
                            }
                            else
                            {

#line 2208
                                m1_0 = m1_1;

#line 2208
                                s1_1 = s1_0;

#line 2208
                                v1_1 = v1_0;

#line 2208
                            }

#line 2208
                            if(_S41 >= 3U)
                            {

#line 2208
                                _S29 = b_6 == 2U;

#line 2208
                            }
                            else
                            {

#line 2208
                                _S29 = false;

#line 2208
                            }

#line 2208
                            if(_S29)
                            {

#line 2208
                                _S30 = mag_0 > m2_0;

#line 2208
                            }
                            else
                            {

#line 2208
                                _S30 = false;

#line 2208
                            }

#line 2208
                            uint m2_1;

#line 2208
                            uint s2_1;

#line 2208
                            float2 v2_1;

#line 2208
                            if(_S30)
                            {

#line 2208
                                float2 _S67 = float2(rx_0, ry_0);

#line 2208
                                m2_1 = mag_0;

#line 2208
                                s2_1 = slot_1;

#line 2208
                                v2_1 = _S67;

#line 2208
                            }
                            else
                            {

#line 2208
                                m2_1 = m2_0;

#line 2208
                                s2_1 = s2_0;

#line 2208
                                v2_1 = v2_0;

#line 2208
                            }

#line 2208
                            if(_S41 >= 4U)
                            {

#line 2208
                                _S31 = b_6 == 3U;

#line 2208
                            }
                            else
                            {

#line 2208
                                _S31 = false;

#line 2208
                            }

#line 2208
                            if(_S31)
                            {

#line 2208
                                _S32 = mag_0 > m3_0;

#line 2208
                            }
                            else
                            {

#line 2208
                                _S32 = false;

#line 2208
                            }

#line 2208
                            uint m3_1;

#line 2208
                            uint s3_1;

#line 2208
                            float2 v3_1;

#line 2208
                            if(_S32)
                            {

#line 2208
                                float2 _S68 = float2(rx_0, ry_0);

#line 2208
                                m3_1 = mag_0;

#line 2208
                                s3_1 = slot_1;

#line 2208
                                v3_1 = _S68;

#line 2208
                            }
                            else
                            {

#line 2208
                                m3_1 = m3_0;

#line 2208
                                s3_1 = s3_0;

#line 2208
                                v3_1 = v3_0;

#line 2208
                            }

#line 2208
                            d_4 = m0_0;

#line 2208
                            m1_1 = m1_0;

#line 2208
                            m2_0 = m2_1;

#line 2208
                            m3_0 = m3_1;

#line 2208
                            s0_1 = s0_0;

#line 2208
                            s1_0 = s1_1;

#line 2208
                            s2_0 = s2_1;

#line 2208
                            s3_0 = s3_1;

#line 2208
                            v0_0 = v0_1;

#line 2208
                            v1_0 = v1_1;

#line 2208
                            v2_0 = v2_1;

#line 2208
                            v3_0 = v3_1;

#line 2208
                        }

#line 2208
                        i_5 = i_5 + 1U;

#line 2208
                    }

#line 2208
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2208
                    uint wm0_0 = simd_max(d_4);

#line 2208
                    bool _S69 = simd_is_first();

#line 2208
                    if(_S69)
                    {

#line 2208
                        isCand_0 = wm0_0 > _S42;

#line 2208
                    }
                    else
                    {

#line 2208
                        isCand_0 = false;

#line 2208
                    }

#line 2208
                    if(isCand_0)
                    {

#line 2208
                        uint _S70 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), wm0_0, memory_order_relaxed);

#line 2208
                    }

#line 2208
                    bool _S71 = _S41 >= 2U;

#line 2208
                    if(_S71)
                    {

#line 2208
                        uint wm1_0 = simd_max(m1_1);

#line 2208
                        bool _S72 = simd_is_first();

#line 2208
                        if(_S72)
                        {

#line 2208
                            _S26 = wm1_0 > _S42;

#line 2208
                        }
                        else
                        {

#line 2208
                            _S26 = false;

#line 2208
                        }

#line 2208
                        if(_S26)
                        {

#line 2208
                            uint _S73 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), wm1_0, memory_order_relaxed);

#line 2208
                        }

#line 2208
                    }

#line 2208
                    bool _S74 = _S41 >= 3U;

#line 2208
                    if(_S74)
                    {

#line 2208
                        uint wm2_0 = simd_max(m2_0);

#line 2208
                        bool _S75 = simd_is_first();

#line 2208
                        if(_S75)
                        {

#line 2208
                            _S26 = wm2_0 > _S42;

#line 2208
                        }
                        else
                        {

#line 2208
                            _S26 = false;

#line 2208
                        }

#line 2208
                        if(_S26)
                        {

#line 2208
                            uint _S76 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U])), wm2_0, memory_order_relaxed);

#line 2208
                        }

#line 2208
                    }

#line 2208
                    bool _S77 = _S41 >= 4U;

#line 2208
                    if(_S77)
                    {

#line 2208
                        uint wm3_0 = simd_max(m3_0);

#line 2208
                        bool _S78 = simd_is_first();

#line 2208
                        if(_S78)
                        {

#line 2208
                            _S26 = wm3_0 > _S42;

#line 2208
                        }
                        else
                        {

#line 2208
                            _S26 = false;

#line 2208
                        }

#line 2208
                        if(_S26)
                        {

#line 2208
                            uint _S79 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U])), wm3_0, memory_order_relaxed);

#line 2208
                        }

#line 2208
                    }

#line 2208
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2208
                    if(s0_1 != 4294967295U)
                    {

#line 2208
                        _S26 = d_4 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0];

#line 2208
                    }
                    else
                    {

#line 2208
                        _S26 = false;

#line 2208
                    }

#line 2208
                    if(_S26)
                    {

#line 2208
                        b_6 = s0_1;

#line 2208
                    }
                    else
                    {

#line 2208
                        b_6 = 4294967295U;

#line 2208
                    }

#line 2208
                    if(_S71)
                    {

#line 2208
                        _S27 = s1_0 != 4294967295U;

#line 2208
                    }
                    else
                    {

#line 2208
                        _S27 = false;

#line 2208
                    }

#line 2208
                    if(_S27)
                    {

#line 2208
                        _S28 = m1_1 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U];

#line 2208
                    }
                    else
                    {

#line 2208
                        _S28 = false;

#line 2208
                    }

#line 2208
                    if(_S28)
                    {

#line 2208
                        m0_0 = s1_0;

#line 2208
                    }
                    else
                    {

#line 2208
                        m0_0 = 4294967295U;

#line 2208
                    }

#line 2208
                    if(_S74)
                    {

#line 2208
                        _S29 = s2_0 != 4294967295U;

#line 2208
                    }
                    else
                    {

#line 2208
                        _S29 = false;

#line 2208
                    }

#line 2208
                    if(_S29)
                    {

#line 2208
                        _S30 = m2_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U];

#line 2208
                    }
                    else
                    {

#line 2208
                        _S30 = false;

#line 2208
                    }

#line 2208
                    if(_S30)
                    {

#line 2208
                        s0_0 = s2_0;

#line 2208
                    }
                    else
                    {

#line 2208
                        s0_0 = 4294967295U;

#line 2208
                    }

#line 2208
                    if(_S77)
                    {

#line 2208
                        _S31 = s3_0 != 4294967295U;

#line 2208
                    }
                    else
                    {

#line 2208
                        _S31 = false;

#line 2208
                    }

#line 2208
                    if(_S31)
                    {

#line 2208
                        _S32 = m3_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U];

#line 2208
                    }
                    else
                    {

#line 2208
                        _S32 = false;

#line 2208
                    }

#line 2208
                    if(_S32)
                    {

#line 2208
                        m1_0 = s3_0;

#line 2208
                    }
                    else
                    {

#line 2208
                        m1_0 = 4294967295U;

#line 2208
                    }

#line 2208
                    uint ww0_0 = simd_min(b_6);

#line 2208
                    bool _S80 = simd_is_first();

#line 2208
                    bool _S81;

#line 2208
                    if(_S80)
                    {

#line 2208
                        _S81 = ww0_0 != 4294967295U;

#line 2208
                    }
                    else
                    {

#line 2208
                        _S81 = false;

#line 2208
                    }

#line 2208
                    if(_S81)
                    {

#line 2208
                        uint _S82 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U])), ww0_0, memory_order_relaxed);

#line 2208
                    }

#line 2208
                    bool _S83;

#line 2208
                    if(_S71)
                    {

#line 2208
                        uint ww1_0 = simd_min(m0_0);

#line 2208
                        bool _S84 = simd_is_first();

#line 2208
                        if(_S84)
                        {

#line 2208
                            _S83 = ww1_0 != 4294967295U;

#line 2208
                        }
                        else
                        {

#line 2208
                            _S83 = false;

#line 2208
                        }

#line 2208
                        if(_S83)
                        {

#line 2208
                            uint _S85 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U])), ww1_0, memory_order_relaxed);

#line 2208
                        }

#line 2208
                    }

#line 2208
                    if(_S74)
                    {

#line 2208
                        uint ww2_0 = simd_min(s0_0);

#line 2208
                        bool _S86 = simd_is_first();

#line 2208
                        if(_S86)
                        {

#line 2208
                            _S83 = ww2_0 != 4294967295U;

#line 2208
                        }
                        else
                        {

#line 2208
                            _S83 = false;

#line 2208
                        }

#line 2208
                        if(_S83)
                        {

#line 2208
                            uint _S87 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U])), ww2_0, memory_order_relaxed);

#line 2208
                        }

#line 2208
                    }

#line 2208
                    if(_S77)
                    {

#line 2208
                        uint ww3_0 = simd_min(m1_0);

#line 2208
                        bool _S88 = simd_is_first();

#line 2208
                        if(_S88)
                        {

#line 2208
                            _S83 = ww3_0 != 4294967295U;

#line 2208
                        }
                        else
                        {

#line 2208
                            _S83 = false;

#line 2208
                        }

#line 2208
                        if(_S83)
                        {

#line 2208
                            uint _S89 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U])), ww3_0, memory_order_relaxed);

#line 2208
                        }

#line 2208
                    }

#line 2208
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2208
                    uint baseOut_0 = pair_0 * _S41;

#line 2208
                    if(b_6 != 4294967295U)
                    {

#line 2208
                        _S83 = b_6 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U];

#line 2208
                    }
                    else
                    {

#line 2208
                        _S83 = false;

#line 2208
                    }

#line 2208
                    if(_S83)
                    {

#line 2208
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+baseOut_0) = int(slotToIndex_0(b_6));

#line 2208
                        *((&kernelContext_3)->entryPointParams_peakVal_0+baseOut_0) = packed_float2(v0_0) ;

#line 2208
                    }

#line 2208
                    bool _S90;

#line 2208
                    if(_S71)
                    {

#line 2208
                        _S90 = m0_0 != 4294967295U;

#line 2208
                    }
                    else
                    {

#line 2208
                        _S90 = false;

#line 2208
                    }

#line 2208
                    bool _S91;

#line 2208
                    if(_S90)
                    {

#line 2208
                        _S91 = m0_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U];

#line 2208
                    }
                    else
                    {

#line 2208
                        _S91 = false;

#line 2208
                    }

#line 2208
                    if(_S91)
                    {

#line 2208
                        uint _S92 = baseOut_0 + 1U;

#line 2208
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+_S92) = int(slotToIndex_0(m0_0));

#line 2208
                        *((&kernelContext_3)->entryPointParams_peakVal_0+_S92) = packed_float2(v1_0) ;

#line 2208
                    }

#line 2208
                    bool _S93;

#line 2208
                    if(_S74)
                    {

#line 2208
                        _S93 = s0_0 != 4294967295U;

#line 2208
                    }
                    else
                    {

#line 2208
                        _S93 = false;

#line 2208
                    }

#line 2208
                    bool _S94;

#line 2208
                    if(_S93)
                    {

#line 2208
                        _S94 = s0_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U];

#line 2208
                    }
                    else
                    {

#line 2208
                        _S94 = false;

#line 2208
                    }

#line 2208
                    if(_S94)
                    {

#line 2208
                        uint _S95 = baseOut_0 + 2U;

#line 2208
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+_S95) = int(slotToIndex_0(s0_0));

#line 2208
                        *((&kernelContext_3)->entryPointParams_peakVal_0+_S95) = packed_float2(v2_0) ;

#line 2208
                    }

#line 2208
                    bool _S96;

#line 2208
                    if(_S77)
                    {

#line 2208
                        _S96 = m1_0 != 4294967295U;

#line 2208
                    }
                    else
                    {

#line 2208
                        _S96 = false;

#line 2208
                    }

#line 2208
                    bool _S97;

#line 2208
                    if(_S96)
                    {

#line 2208
                        _S97 = m1_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U];

#line 2208
                    }
                    else
                    {

#line 2208
                        _S97 = false;

#line 2208
                    }

#line 2208
                    if(_S97)
                    {

#line 2208
                        uint _S98 = baseOut_0 + 3U;

#line 2208
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+_S98) = int(slotToIndex_0(m1_0));

#line 2208
                        *((&kernelContext_3)->entryPointParams_peakVal_0+_S98) = packed_float2(v3_0) ;

#line 2208
                    }

#line 2208
                    bool _S99;

#line 2208
                    if(_S35 < _S41)
                    {

#line 2208
                        _S99 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _S35]) == 4294967295U;

#line 2208
                    }
                    else
                    {

#line 2208
                        _S99 = false;

#line 2208
                    }

#line 2208
                    if(_S99)
                    {

#line 2208
                        uint _S100 = baseOut_0 + _S35;

#line 2208
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+_S100) = int(-1);

#line 2208
                        *((&kernelContext_3)->entryPointParams_peakVal_0+_S100) = packed_float2(_S63) ;

#line 2208
                    }

#line 2208
                }
                else
                {

#line 2208
                    d_4 = _S35;

#line 2208
                    for(;;)
                    {

#line 2208
                        if(d_4 < _S41)
                        {
                        }
                        else
                        {

#line 2208
                            break;
                        }

#line 2208
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + d_4] = _S42;

#line 2208
                        d_4 = d_4 + 32U;

#line 2208
                    }

#line 2208
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2208
                    s0_1 = 0U;

#line 2208
                    m1_1 = 0U;

#line 2208
                    s1_0 = 0U;

#line 2208
                    for(;;)
                    {

#line 2208
                        if(s0_1 < 16U)
                        {
                        }
                        else
                        {

#line 2208
                            break;
                        }

#line 2208
                        uint idx_2 = slotToIndex_0(_S35 * 16U + s0_1);

#line 2208
                        if(idx_2 >= _S36)
                        {

#line 2208
                            isCand_0 = idx_2 < _S37;

#line 2208
                        }
                        else
                        {

#line 2208
                            isCand_0 = false;

#line 2208
                        }

#line 2208
                        if(isCand_0)
                        {

#line 2208
                            float rx_1 = r_3[s0_1].x;

#line 2208
                            float ry_1 = r_3[s0_1].y;

#line 2208
                            uint mag_1 = (as_type<uint>((rx_1 * rx_1 + ry_1 * ry_1)));

#line 2208
                            if(mag_1 > _S42)
                            {

#line 2208
                                uint off_1 = idx_2 - _S36 + (&kernelContext_3)->_binPhase_0;

#line 2208
                                if(_S40 >= int(0))
                                {

#line 2208
                                    m2_0 = off_1 >> uint(_S40);

#line 2208
                                }
                                else
                                {

#line 2208
                                    uint _S101 = off_1 / _S39;

#line 2208
                                    m2_0 = _S101;

#line 2208
                                }

#line 2208
                                uint _S102 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m2_0])), mag_1, memory_order_relaxed);

#line 2208
                                uint bit_0 = 1U << (s0_1 & 31U);

#line 2208
                                if(s0_1 < 32U)
                                {

#line 2208
                                    i_5 = m1_1 | bit_0;

#line 2208
                                    s2_0 = s1_0;

#line 2208
                                }
                                else
                                {

#line 2208
                                    uint aboveHi_0 = s1_0 | bit_0;

#line 2208
                                    i_5 = m1_1;

#line 2208
                                    s2_0 = aboveHi_0;

#line 2208
                                }

#line 2208
                            }
                            else
                            {

#line 2208
                                i_5 = m1_1;

#line 2208
                                s2_0 = s1_0;

#line 2208
                            }

#line 2208
                        }
                        else
                        {

#line 2208
                            i_5 = m1_1;

#line 2208
                            s2_0 = s1_0;

#line 2208
                        }

#line 2208
                        s0_1 = s0_1 + 1U;

#line 2208
                        m1_1 = i_5;

#line 2208
                        s1_0 = s2_0;

#line 2208
                    }

#line 2208
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2208
                    if((m1_1 | s1_0) != 0U)
                    {

#line 2208
                        i_5 = 0U;

#line 2208
                        m2_0 = 0U;

#line 2208
                        s2_0 = 0U;

#line 2208
                        for(;;)
                        {

#line 2208
                            if(i_5 < 16U)
                            {
                            }
                            else
                            {

#line 2208
                                break;
                            }

#line 2208
                            uint bit_1 = 1U << (i_5 & 31U);

#line 2208
                            bool _S103 = i_5 < 32U;

#line 2208
                            if(_S103)
                            {

#line 2208
                                isCand_0 = (m1_1 & bit_1) != 0U;

#line 2208
                            }
                            else
                            {

#line 2208
                                isCand_0 = (s1_0 & bit_1) != 0U;

#line 2208
                            }

#line 2208
                            if(isCand_0)
                            {

#line 2208
                                uint off_2 = slotToIndex_0(_S35 * 16U + i_5) - _S36 + (&kernelContext_3)->_binPhase_0;

#line 2208
                                if(_S40 >= int(0))
                                {

#line 2208
                                    m3_0 = off_2 >> uint(_S40);

#line 2208
                                }
                                else
                                {

#line 2208
                                    uint _S104 = off_2 / _S39;

#line 2208
                                    m3_0 = _S104;

#line 2208
                                }

#line 2208
                                float rx_2 = r_3[i_5].x;

#line 2208
                                float ry_2 = r_3[i_5].y;

#line 2208
                                if((as_type<uint>((rx_2 * rx_2 + ry_2 * ry_2))) == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m3_0])
                                {

#line 2208
                                    if(_S103)
                                    {

#line 2208
                                        s3_0 = m2_0 | bit_1;

#line 2208
                                        b_6 = s2_0;

#line 2208
                                    }
                                    else
                                    {

#line 2208
                                        uint candHi_0 = s2_0 | bit_1;

#line 2208
                                        s3_0 = m2_0;

#line 2208
                                        b_6 = candHi_0;

#line 2208
                                    }

#line 2208
                                }
                                else
                                {

#line 2208
                                    s3_0 = m2_0;

#line 2208
                                    b_6 = s2_0;

#line 2208
                                }

#line 2208
                            }
                            else
                            {

#line 2208
                                s3_0 = m2_0;

#line 2208
                                b_6 = s2_0;

#line 2208
                            }

#line 2208
                            i_5 = i_5 + 1U;

#line 2208
                            m2_0 = s3_0;

#line 2208
                            s2_0 = b_6;

#line 2208
                        }

#line 2208
                        s3_0 = m2_0;

#line 2208
                        b_6 = s2_0;

#line 2208
                    }
                    else
                    {

#line 2208
                        s3_0 = 0U;

#line 2208
                        b_6 = 0U;

#line 2208
                    }

#line 2208
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2208
                    m3_0 = _S35;

#line 2208
                    for(;;)
                    {

#line 2208
                        if(m3_0 < _S41)
                        {
                        }
                        else
                        {

#line 2208
                            break;
                        }

#line 2208
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m3_0] = 4294967295U;

#line 2208
                        m3_0 = m3_0 + 32U;

#line 2208
                    }

#line 2208
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2208
                    bool _S105 = (s3_0 | b_6) != 0U;

#line 2208
                    if(_S105)
                    {

#line 2208
                        i_5 = 0U;

#line 2208
                        for(;;)
                        {

#line 2208
                            if(i_5 < 16U)
                            {
                            }
                            else
                            {

#line 2208
                                break;
                            }

#line 2208
                            uint bit_2 = 1U << (i_5 & 31U);

#line 2208
                            if(i_5 < 32U)
                            {

#line 2208
                                isCand_0 = (s3_0 & bit_2) != 0U;

#line 2208
                            }
                            else
                            {

#line 2208
                                isCand_0 = (b_6 & bit_2) != 0U;

#line 2208
                            }

#line 2208
                            if(isCand_0)
                            {

#line 2208
                                uint _S106 = _S35 * 16U + i_5;

#line 2208
                                uint off_3 = slotToIndex_0(_S106) - _S36 + (&kernelContext_3)->_binPhase_0;

#line 2208
                                if(_S40 >= int(0))
                                {

#line 2208
                                    m2_0 = off_3 >> uint(_S40);

#line 2208
                                }
                                else
                                {

#line 2208
                                    uint _S107 = off_3 / _S39;

#line 2208
                                    m2_0 = _S107;

#line 2208
                                }

#line 2208
                                uint _S108 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m2_0])), _S106, memory_order_relaxed);

#line 2208
                            }

#line 2208
                            i_5 = i_5 + 1U;

#line 2208
                        }

#line 2208
                    }

#line 2208
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2208
                    if(_S105)
                    {

#line 2208
                        i_5 = 0U;

#line 2208
                        for(;;)
                        {

#line 2208
                            if(i_5 < 16U)
                            {
                            }
                            else
                            {

#line 2208
                                break;
                            }

#line 2208
                            uint bit_3 = 1U << (i_5 & 31U);

#line 2208
                            if(i_5 < 32U)
                            {

#line 2208
                                isCand_0 = (s3_0 & bit_3) != 0U;

#line 2208
                            }
                            else
                            {

#line 2208
                                isCand_0 = (b_6 & bit_3) != 0U;

#line 2208
                            }

#line 2208
                            if(isCand_0)
                            {

#line 2208
                                uint _S109 = _S35 * 16U + i_5;

#line 2208
                                uint idx_3 = slotToIndex_0(_S109);

#line 2208
                                uint off_4 = idx_3 - _S36 + (&kernelContext_3)->_binPhase_0;

#line 2208
                                if(_S40 >= int(0))
                                {

#line 2208
                                    m2_0 = off_4 >> uint(_S40);

#line 2208
                                }
                                else
                                {

#line 2208
                                    uint _S110 = off_4 / _S39;

#line 2208
                                    m2_0 = _S110;

#line 2208
                                }

#line 2208
                                if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m2_0]) == _S109)
                                {

#line 2208
                                    uint o_1 = pair_0 * _S41 + m2_0;

#line 2208
                                    *((&kernelContext_3)->entryPointParams_peakIdx_0+o_1) = int(idx_3);

#line 2208
                                    *((&kernelContext_3)->entryPointParams_peakVal_0+o_1) = packed_float2(float2(r_3[i_5].x, r_3[i_5].y)) ;

#line 2208
                                }

#line 2208
                            }

#line 2208
                            i_5 = i_5 + 1U;

#line 2208
                        }

#line 2208
                    }

#line 2208
                    m2_0 = _S35;

#line 2208
                    for(;;)
                    {

#line 2208
                        if(m2_0 < _S41)
                        {
                        }
                        else
                        {

#line 2208
                            break;
                        }

#line 2208
                        if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m2_0]) == 4294967295U)
                        {

#line 2208
                            uint _S111 = pair_0 * _S41 + m2_0;

#line 2208
                            *((&kernelContext_3)->entryPointParams_peakIdx_0+_S111) = int(-1);

#line 2208
                            *((&kernelContext_3)->entryPointParams_peakVal_0+_S111) = packed_float2(float2(0.0f, 0.0f)) ;

#line 2208
                        }

#line 2208
                        m2_0 = m2_0 + 32U;

#line 2208
                    }

#line 2208
                }

#line 2208
                break;
            }

#line 2208
            break;
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2204
        i_4 = i_4 + (&kernelContext_3)->entryPointParams_0->gridSize_0;

#line 2204
    }

#line 2212
    return;
}
