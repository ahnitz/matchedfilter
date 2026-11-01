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


#line 87 "twiddle.slang"
uint mfRowWindowsFlag_0()
{
    ;
    uint _S2 = ((MF_ROW_WINDOWS));

#line 90
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


#line 318 "mm_8192_refineListed.slang"
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
    array<uint, int(16384)> threadgroup* stg_0;
};


#line 228
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 92 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 231 "mm_8192_refineListed.slang"
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


#line 60 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S5 = ((MF_DATA_STRIDE));

#line 63
    return _S5;
}


#line 174 "mm_8192_refineListed.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 174
    return float2(*(b_0+i_0)) ;
}


#line 330
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 330
    float _S6 = a_0.x;

#line 330
    float _S7 = b_1.x;

#line 330
    float _S8 = a_0.y;

#line 330
    float _S9 = b_1.y;

#line 330
    return float2(_S6 * _S7 + _S8 * _S9, _S8 * _S7 - _S6 * _S9);
}


#line 614
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 616
    float2 t1_0 = *a_1 - *c_0;

#line 616
    float2 t2_0 = *b_2 + *d_1;

#line 616
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 618
    *b_2 = t1_0 + j3_0;

#line 618
    *c_0 = t0_0 - t2_0;

#line 618
    *d_1 = t1_0 - j3_0;
    return;
}


#line 329
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 329
    float _S10 = a_2.x;

#line 329
    float _S11 = b_3.x;

#line 329
    float _S12 = a_2.y;

#line 329
    float _S13 = b_3.y;

#line 329
    return float2(_S10 * _S11 - _S12 * _S13, _S10 * _S13 + _S12 * _S11);
}


#line 650
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 657
    uint n1_0 = 0U;
    for(;;)
    {

#line 658
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 658
            break;
        }

#line 658
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 658
        n1_0 = n1_0 + 1U;

#line 658
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 659
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 659
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 660
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 660
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 661
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 661
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 661
    uint k2_0 = 0U;
    for(;;)
    {

#line 662
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 662
            break;
        }

#line 662
        uint _S14 = 4U * k2_0;

#line 662
        r4_0(&(*r_0)[_S14], &(*r_0)[_S14 + 1U], &(*r_0)[_S14 + 2U], &(*r_0)[_S14 + 3U]);

#line 662
        k2_0 = k2_0 + 1U;

#line 662
    }

    float2 t_0 = (*r_0)[int(1)];

#line 664
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 664
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 665
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 665
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 666
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 666
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 667
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 667
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 668
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 668
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 669
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 669
    (*r_0)[int(14)] = t_5;
    return;
}


#line 76 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S15 = ((MF_ACCURATE_TRIG));

#line 79
    return _S15;
}


#line 103
float2 mfTwiddle_0(float angle_0)
{

#line 81
    uint _S16 = mfAccurateTrigFlag_0();

#line 105
    if(_S16 == 0U)
    {

#line 106
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


#line 331 "mm_8192_refineListed.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S18 = max(TB_0, 1U);

#line 333
    uint j_0 = d_2 / _S18;

#line 333
    uint m_0 = d_2 % _S18;

#line 333
    uint _S19;
    if(TB_0 <= 16U)
    {

#line 334
        _S19 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 334
    }
    else
    {

#line 334
        _S19 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 334
    }

#line 334
    return _S19;
}


#line 318
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 318
    uint _S20 = 2U * i_1;

#line 318
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20] = (as_type<uint>((v_0.x)));

#line 318
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20 + 1U] = (as_type<uint>((v_0.y)));

#line 318
    return;
}


#line 319
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_2)
{

#line 319
    uint _S21 = 2U * i_2;

#line 319
    return float2((as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S21]))), (as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S21 + 1U]))));
}


#line 625
void dft2_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    float2 a_3 = (*r_1)[o_0];

#line 627
    float2 b_4 = (*r_1)[o_0 + 1U];

#line 627
    (*r_1)[o_0] = (*r_1)[o_0] + (*r_1)[o_0 + 1U];

#line 627
    (*r_1)[o_0 + 1U] = a_3 - b_4;
    return;
}


#line 753
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 753
    uint b_5 = 0U;

#line 763
    for(;;)
    {

#line 763
        if(b_5 < 8U)
        {
        }
        else
        {

#line 763
            break;
        }

#line 763
        dft2_0(r_2, b_5 * 2U);

#line 763
        b_5 = b_5 + 1U;

#line 763
    }

    return;
}


#line 881
uint lgOf_0(uint i_3)
{

#line 881
    uint _S22;

#line 881
    if(i_3 < 3U)
    {

#line 881
        _S22 = 4U;

#line 881
    }
    else
    {

#line 881
        _S22 = 1U;

#line 881
    }

#line 881
    return _S22;
}


#line 883
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_1 = slot_0 >> lg_0;

#line 887
    uint lg_1 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_1;

#line 887
    uint lg_2 = lgOf_0(1U);

#line 887
    uint lg_3 = lgOf_0(0U);

#line 892
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | (x_2 & ((1U << lg_2) - 1U))) << lg_3) | ((x_2 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 2292
[[kernel]] void refineListedBounded(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]], uint device* entryPointParams_rowWin_1 [[buffer(7)]])
{

#line 2292
    uint k2_1;

#line 2292
    uint _S23;

#line 2292
    uint _S24;

#line 2292
    uint _S25;

#line 2292
    uint d_3;

#line 2292
    uint j_1;

#line 2292
    uint _S26;

#line 2292
    uint _S27;

#line 2292
    uint _S28;

#line 2292
    uint d_4;

#line 2292
    uint m0_0;

#line 2292
    uint s0_0;

#line 2292
    uint m1_0;

#line 2292
    bool _S29;

#line 2292
    bool _S30;

#line 2292
    bool _S31;

#line 2292
    bool _S32;

#line 2292
    bool _S33;

#line 2292
    bool _S34;

#line 2292
    bool _S35;

#line 2292
    thread KernelContext_0 kernelContext_3;

#line 2292
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 2292
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2292
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2292
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2292
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2292
    (&kernelContext_3)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2292
    (&kernelContext_3)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2292
    (&kernelContext_3)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 2292
    threadgroup array<uint, int(16384)> stg_1;

#line 2292
    (&kernelContext_3)->stg_0 = &stg_1;

#line 2292
    (&kernelContext_3)->_binPhase_0 = 0U;

#line 2303
    uint _S36 = entryPointParams_count_1[int(0)];

#line 2303
    uint i_4 = gid_0.x;
    for(;;)
    {

#line 2304
        if(i_4 < _S36)
        {
        }
        else
        {

#line 2304
            break;
        }

#line 2305
        (&kernelContext_3)->_stgBase_0 = 0U;
        uint pair_0 = (&kernelContext_3)->entryPointParams_survivors_0[i_4];

#line 2306
        thread uint ws_0 = (&kernelContext_3)->entryPointParams_0->winStart_0;

#line 2306
        thread uint we_0 = (&kernelContext_3)->entryPointParams_0->winEnd_0;
        uint _S37 = pair_0 / (&kernelContext_3)->entryPointParams_0->ntmpl_0;

#line 2307
        rowWindow_0(_S37, &ws_0, &we_0, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);
        uint _S38 = lid_0.x;

#line 2308
        uint _S39 = ws_0;

#line 2308
        uint _S40 = we_0;

#line 2308
        uint _S41 = (&kernelContext_3)->entryPointParams_0->ntmpl_0;

#line 2308
        uint _S42 = (&kernelContext_3)->entryPointParams_0->binsize_0;

#line 2308
        int _S43 = (&kernelContext_3)->entryPointParams_0->binShift_0;

#line 2308
        uint _S44 = (&kernelContext_3)->entryPointParams_0->nbins_0;

#line 2308
        uint _S45 = (&kernelContext_3)->entryPointParams_0->thrBits_0;

#line 2308
        for(;;)
        {

#line 2308
            for(;;)
            {

#line 2308
                (&kernelContext_3)->_tid_0 = _S38;

#line 2308
                uint _S46 = pair_0 / _S41;

#line 2308
                uint _S47 = pair_0 % _S41;

#line 2308
                thread array<float2, int(16)> r_3;

#line 2308
                uint n2_0 = 0U;

#line 2308
                for(;;)
                {

#line 2308
                    if(n2_0 < 16U)
                    {
                    }
                    else
                    {

#line 2308
                        break;
                    }

#line 2308
                    uint idx_0 = _S38 + 512U * n2_0;

#line 2308
                    uint _S48 = mfDataStrideFlag_0();

#line 2308
                    if(_S48 != 0U)
                    {

#line 2308
                        uint _S49 = mfDataStrideFlag_0();

#line 2308
                        k2_1 = _S49;

#line 2308
                    }
                    else
                    {

#line 2308
                        k2_1 = 8192U;

#line 2308
                    }

#line 2308
                    r_3[n2_0] = cmulConj_0(cload_0((&kernelContext_3)->entryPointParams_data_0, _S46 * k2_1 + idx_0), cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S47 * 8192U + idx_0));

#line 2308
                    n2_0 = n2_0 + 1U;

#line 2308
                }

#line 2308
                for(;;)
                {

#line 2308
                    for(;;)
                    {

#line 2308
                        for(;;)
                        {

#line 2308
                            for(;;)
                            {

#line 2308
                                uint lgTB_0 = firstbithigh_0(512U);

#line 2308
                                _S23 = lgTB_0;

#line 2308
                                uint lgLn_0 = firstbithigh_0(8192U);

#line 2308
                                uint blk_1 = _S38 >> lgTB_0;

#line 2308
                                uint lane_1 = _S38 & 511U;

#line 2308
                                dft16_0(&r_3);

#line 2308
                                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 8192.0f);

#line 2308
                                float _S50 = tw_0.x;

#line 2308
                                float _S51 = tw_0.y;

#line 2308
                                k2_1 = 0U;

#line 2308
                                float cr_0 = 1.0f;

#line 2308
                                float ci_0 = 0.0f;

#line 2308
                                for(;;)
                                {

#line 2308
                                    if(k2_1 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2308
                                        break;
                                    }

#line 2308
                                    r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2308
                                    float nr_0 = cr_0 * _S50 - ci_0 * _S51;

#line 2308
                                    float _S52 = cr_0 * _S51 + ci_0 * _S50;

#line 2308
                                    k2_1 = k2_1 + 1U;

#line 2308
                                    cr_0 = nr_0;

#line 2308
                                    ci_0 = _S52;

#line 2308
                                }

#line 2308
                                uint per_1 = 16U / max(512U, 1U);

#line 2308
                                uint _S53 = max(32U, 1U);

#line 2308
                                _S24 = _S53;

#line 2308
                                uint blk2_1 = _S38 / _S53;

#line 2308
                                uint lane2_1 = _S38 % _S53;

#line 2308
                                for(;;)
                                {

#line 2308
                                    thread array<float2, int(16)> out_0;

#line 2308
                                    uint z_1 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(z_1 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        out_0[z_1] = float2(0.0f, 0.0f);

#line 2308
                                        z_1 = z_1 + 1U;

#line 2308
                                    }

#line 2308
                                    uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2308
                                    _S25 = spanMask_0;

#line 2308
                                    uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2308
                                    uint p0_0 = computeWant_0(0U, 512U, 8192U, blk_1, lane_1, per_1, _S53, 512U, blk2_1, lane2_1);

#line 2308
                                    uint _S54 = p0_0 & lenMask_0;

#line 2308
                                    uint _S55 = (_S54 >> lgTB_0) * 512U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S54 & spanMask_0);

#line 2308
                                    uint c_2 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(c_2 < 1U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                                        j_1 = 0U;

#line 2308
                                        for(;;)
                                        {

#line 2308
                                            if(j_1 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 2308
                                                break;
                                            }

#line 2308
                                            stgPut_0(j_1 * 512U + (&kernelContext_3)->_tid_0, r_3[c_2 * 16U + j_1], &kernelContext_3);

#line 2308
                                            j_1 = j_1 + 1U;

#line 2308
                                        }

#line 2308
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                                        d_3 = 0U;

#line 2308
                                        for(;;)
                                        {

#line 2308
                                            if(d_3 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 2308
                                                break;
                                            }

#line 2308
                                            uint pz_0 = computeWant_0(d_3, 512U, 8192U, 0U, 0U, per_1, _S53, 512U, 0U, 0U);

#line 2308
                                            uint _S56 = pz_0 & lenMask_0;

#line 2308
                                            uint az_0 = (_S56 >> lgTB_0) * 512U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S56 & spanMask_0);

#line 2308
                                            float2 _S57 = stgGet_0(_S55 + az_0 - c_2 * 16U * 512U, &kernelContext_3);

#line 2308
                                            out_0[d_3] = _S57;

#line 2308
                                            d_3 = d_3 + 1U;

#line 2308
                                        }

#line 2308
                                        c_2 = c_2 + 1U;

#line 2308
                                    }

#line 2308
                                    uint d_5 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(d_5 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        r_3[d_5] = out_0[d_5];

#line 2308
                                        d_5 = d_5 + 1U;

#line 2308
                                    }

#line 2308
                                    break;
                                }

#line 2308
                                break;
                            }

#line 2308
                            break;
                        }

#line 2308
                        for(;;)
                        {

#line 2308
                            for(;;)
                            {

#line 2308
                                uint lgTB_1 = firstbithigh_0(32U);

#line 2308
                                _S26 = lgTB_1;

#line 2308
                                uint blk_2 = _S38 >> lgTB_1;

#line 2308
                                uint lane_2 = _S38 & 31U;

#line 2308
                                dft16_0(&r_3);

#line 2308
                                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 512.0f);

#line 2308
                                float _S58 = tw_1.x;

#line 2308
                                float _S59 = tw_1.y;

#line 2308
                                uint k2_2 = 0U;

#line 2308
                                float cr_1 = 1.0f;

#line 2308
                                float ci_1 = 0.0f;

#line 2308
                                for(;;)
                                {

#line 2308
                                    if(k2_2 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2308
                                        break;
                                    }

#line 2308
                                    r_3[k2_2] = cmul_0(r_3[k2_2], float2(cr_1, ci_1));

#line 2308
                                    float nr_1 = cr_1 * _S58 - ci_1 * _S59;

#line 2308
                                    float _S60 = cr_1 * _S59 + ci_1 * _S58;

#line 2308
                                    k2_2 = k2_2 + 1U;

#line 2308
                                    cr_1 = nr_1;

#line 2308
                                    ci_1 = _S60;

#line 2308
                                }

#line 2308
                                uint per_2 = 16U / _S24;

#line 2308
                                uint _S61 = max(2U, 1U);

#line 2308
                                _S27 = _S61;

#line 2308
                                uint blk2_2 = _S38 / _S61;

#line 2308
                                uint lane2_2 = _S38 % _S61;

#line 2308
                                for(;;)
                                {

#line 2308
                                    thread array<float2, int(16)> out_1;

#line 2308
                                    uint z_2 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(z_2 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        out_1[z_2] = float2(0.0f, 0.0f);

#line 2308
                                        z_2 = z_2 + 1U;

#line 2308
                                    }

#line 2308
                                    uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2308
                                    _S28 = spanMask_1;

#line 2308
                                    uint p0_1 = computeWant_0(0U, 32U, 512U, blk_2, lane_2, per_2, _S61, 32U, blk2_2, lane2_2);

#line 2308
                                    uint _S62 = p0_1 & _S25;

#line 2308
                                    uint _S63 = (_S62 >> lgTB_1) * 512U + ((p0_1 >> _S23) << lgTB_1) + (_S62 & spanMask_1);

#line 2308
                                    uint c_3 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(c_3 < 1U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        bool _S64 = c_3 == 0U;

#line 2308
                                        if(!_S64)
                                        {

#line 2308
                                            simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2308
                                        }
                                        else
                                        {

#line 2308
                                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                                        }

#line 2308
                                        j_1 = 0U;

#line 2308
                                        for(;;)
                                        {

#line 2308
                                            if(j_1 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 2308
                                                break;
                                            }

#line 2308
                                            stgPut_0(j_1 * 512U + (&kernelContext_3)->_tid_0, r_3[c_3 * 16U + j_1], &kernelContext_3);

#line 2308
                                            j_1 = j_1 + 1U;

#line 2308
                                        }

#line 2308
                                        simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2308
                                        d_3 = 0U;

#line 2308
                                        for(;;)
                                        {

#line 2308
                                            if(d_3 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 2308
                                                break;
                                            }

#line 2308
                                            uint pz_1 = computeWant_0(d_3, 32U, 512U, 0U, 0U, per_2, _S61, 32U, 0U, 0U);

#line 2308
                                            uint _S65 = pz_1 & _S25;

#line 2308
                                            uint az_1 = (_S65 >> lgTB_1) * 512U + ((pz_1 >> _S23) << lgTB_1) + (_S65 & spanMask_1);

#line 2308
                                            float2 _S66 = stgGet_0(_S63 + az_1 - c_3 * 16U * 512U, &kernelContext_3);

#line 2308
                                            out_1[d_3] = _S66;

#line 2308
                                            d_3 = d_3 + 1U;

#line 2308
                                        }

#line 2308
                                        c_3 = c_3 + 1U;

#line 2308
                                    }

#line 2308
                                    d_3 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(d_3 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        r_3[d_3] = out_1[d_3];

#line 2308
                                        d_3 = d_3 + 1U;

#line 2308
                                    }

#line 2308
                                    break;
                                }

#line 2308
                                break;
                            }

#line 2308
                            break;
                        }

#line 2308
                        for(;;)
                        {

#line 2308
                            for(;;)
                            {

#line 2308
                                uint lgTB_2 = firstbithigh_0(2U);

#line 2308
                                uint blk_3 = _S38 >> lgTB_2;

#line 2308
                                uint lane_3 = _S38 & 1U;

#line 2308
                                dft16_0(&r_3);

#line 2308
                                float2 tw_2 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 32.0f);

#line 2308
                                float _S67 = tw_2.x;

#line 2308
                                float _S68 = tw_2.y;

#line 2308
                                uint k2_3 = 0U;

#line 2308
                                float cr_2 = 1.0f;

#line 2308
                                float ci_2 = 0.0f;

#line 2308
                                for(;;)
                                {

#line 2308
                                    if(k2_3 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2308
                                        break;
                                    }

#line 2308
                                    r_3[k2_3] = cmul_0(r_3[k2_3], float2(cr_2, ci_2));

#line 2308
                                    float nr_2 = cr_2 * _S67 - ci_2 * _S68;

#line 2308
                                    float _S69 = cr_2 * _S68 + ci_2 * _S67;

#line 2308
                                    k2_3 = k2_3 + 1U;

#line 2308
                                    cr_2 = nr_2;

#line 2308
                                    ci_2 = _S69;

#line 2308
                                }

#line 2308
                                uint per_3 = 16U / _S27;

#line 2308
                                uint _S70 = max(0U, 1U);

#line 2308
                                uint blk2_3 = _S38 / _S70;

#line 2308
                                uint lane2_3 = _S38 % _S70;

#line 2308
                                for(;;)
                                {

#line 2308
                                    thread array<float2, int(16)> out_2;

#line 2308
                                    uint z_3 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(z_3 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        out_2[z_3] = float2(0.0f, 0.0f);

#line 2308
                                        z_3 = z_3 + 1U;

#line 2308
                                    }

#line 2308
                                    uint spanMask_2 = (1U << lgTB_2) - 1U;

#line 2308
                                    uint p0_2 = computeWant_0(0U, 2U, 32U, blk_3, lane_3, per_3, _S70, 2U, blk2_3, lane2_3);

#line 2308
                                    uint _S71 = p0_2 & _S28;

#line 2308
                                    uint _S72 = (_S71 >> lgTB_2) * 512U + ((p0_2 >> _S26) << lgTB_2) + (_S71 & spanMask_2);

#line 2308
                                    uint c_4 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(c_4 < 1U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2308
                                        j_1 = 0U;

#line 2308
                                        for(;;)
                                        {

#line 2308
                                            if(j_1 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 2308
                                                break;
                                            }

#line 2308
                                            stgPut_0(j_1 * 512U + (&kernelContext_3)->_tid_0, r_3[c_4 * 16U + j_1], &kernelContext_3);

#line 2308
                                            j_1 = j_1 + 1U;

#line 2308
                                        }

#line 2308
                                        simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2308
                                        d_4 = 0U;

#line 2308
                                        for(;;)
                                        {

#line 2308
                                            if(d_4 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 2308
                                                break;
                                            }

#line 2308
                                            uint pz_2 = computeWant_0(d_4, 2U, 32U, 0U, 0U, per_3, _S70, 2U, 0U, 0U);

#line 2308
                                            uint _S73 = pz_2 & _S28;

#line 2308
                                            uint az_2 = (_S73 >> lgTB_2) * 512U + ((pz_2 >> _S26) << lgTB_2) + (_S73 & spanMask_2);

#line 2308
                                            float2 _S74 = stgGet_0(_S72 + az_2 - c_4 * 16U * 512U, &kernelContext_3);

#line 2308
                                            out_2[d_4] = _S74;

#line 2308
                                            d_4 = d_4 + 1U;

#line 2308
                                        }

#line 2308
                                        c_4 = c_4 + 1U;

#line 2308
                                    }

#line 2308
                                    j_1 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(j_1 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        r_3[j_1] = out_2[j_1];

#line 2308
                                        j_1 = j_1 + 1U;

#line 2308
                                    }

#line 2308
                                    break;
                                }

#line 2308
                                break;
                            }

#line 2308
                            break;
                        }

#line 2308
                        break;
                    }

#line 2308
                    innermost_0(&r_3);

#line 2308
                    break;
                }

#line 2308
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                uint s0_1;

#line 2308
                uint m1_1;

#line 2308
                uint s1_0;

#line 2308
                uint i_5;

#line 2308
                uint m2_0;

#line 2308
                uint s2_0;

#line 2308
                uint m3_0;

#line 2308
                uint s3_0;

#line 2308
                uint b_6;

#line 2308
                bool isCand_0;

#line 2308
                if(_S44 <= 4U)
                {

#line 2308
                    if(_S38 < 4U)
                    {

#line 2308
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + _S38] = _S45;

#line 2308
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _S38] = 4294967295U;

#line 2308
                    }

#line 2308
                    float2 _S75 = float2(0.0f, 0.0f);

#line 2308
                    i_5 = 0U;

#line 2308
                    d_4 = _S45;

#line 2308
                    s0_1 = 4294967295U;

#line 2308
                    float2 v0_0 = _S75;

#line 2308
                    m1_1 = _S45;

#line 2308
                    s1_0 = 4294967295U;

#line 2308
                    float2 v1_0 = _S75;

#line 2308
                    m2_0 = _S45;

#line 2308
                    s2_0 = 4294967295U;

#line 2308
                    float2 v2_0 = _S75;

#line 2308
                    m3_0 = _S45;

#line 2308
                    s3_0 = 4294967295U;

#line 2308
                    float2 v3_0 = _S75;

#line 2308
                    for(;;)
                    {

#line 2308
                        if(i_5 < 16U)
                        {
                        }
                        else
                        {

#line 2308
                            break;
                        }

#line 2308
                        uint slot_1 = _S38 * 16U + i_5;

#line 2308
                        uint idx_1 = slotToIndex_0(slot_1);

#line 2308
                        if(idx_1 >= _S39)
                        {

#line 2308
                            isCand_0 = idx_1 < _S40;

#line 2308
                        }
                        else
                        {

#line 2308
                            isCand_0 = false;

#line 2308
                        }

#line 2308
                        if(isCand_0)
                        {

#line 2308
                            float rx_0 = r_3[i_5].x;

#line 2308
                            float ry_0 = r_3[i_5].y;

#line 2308
                            uint mag_0 = (as_type<uint>((rx_0 * rx_0 + ry_0 * ry_0)));

#line 2308
                            uint off_0 = idx_1 - _S39 + (&kernelContext_3)->_binPhase_0;

#line 2308
                            if(_S44 == 1U)
                            {

#line 2308
                                b_6 = 0U;

#line 2308
                            }
                            else
                            {

#line 2308
                                if(_S43 >= int(0))
                                {

#line 2308
                                    b_6 = off_0 >> uint(_S43);

#line 2308
                                }
                                else
                                {

#line 2308
                                    uint _S76 = off_0 / _S42;

#line 2308
                                    b_6 = _S76;

#line 2308
                                }

#line 2308
                            }

#line 2308
                            if(b_6 == 0U)
                            {

#line 2308
                                _S29 = mag_0 > d_4;

#line 2308
                            }
                            else
                            {

#line 2308
                                _S29 = false;

#line 2308
                            }

#line 2308
                            float2 v0_1;

#line 2308
                            if(_S29)
                            {

#line 2308
                                float2 _S77 = float2(rx_0, ry_0);

#line 2308
                                m0_0 = mag_0;

#line 2308
                                s0_0 = slot_1;

#line 2308
                                v0_1 = _S77;

#line 2308
                            }
                            else
                            {

#line 2308
                                m0_0 = d_4;

#line 2308
                                s0_0 = s0_1;

#line 2308
                                v0_1 = v0_0;

#line 2308
                            }

#line 2308
                            if(_S44 >= 2U)
                            {

#line 2308
                                _S30 = b_6 == 1U;

#line 2308
                            }
                            else
                            {

#line 2308
                                _S30 = false;

#line 2308
                            }

#line 2308
                            if(_S30)
                            {

#line 2308
                                _S31 = mag_0 > m1_1;

#line 2308
                            }
                            else
                            {

#line 2308
                                _S31 = false;

#line 2308
                            }

#line 2308
                            uint s1_1;

#line 2308
                            float2 v1_1;

#line 2308
                            if(_S31)
                            {

#line 2308
                                float2 _S78 = float2(rx_0, ry_0);

#line 2308
                                m1_0 = mag_0;

#line 2308
                                s1_1 = slot_1;

#line 2308
                                v1_1 = _S78;

#line 2308
                            }
                            else
                            {

#line 2308
                                m1_0 = m1_1;

#line 2308
                                s1_1 = s1_0;

#line 2308
                                v1_1 = v1_0;

#line 2308
                            }

#line 2308
                            if(_S44 >= 3U)
                            {

#line 2308
                                _S32 = b_6 == 2U;

#line 2308
                            }
                            else
                            {

#line 2308
                                _S32 = false;

#line 2308
                            }

#line 2308
                            if(_S32)
                            {

#line 2308
                                _S33 = mag_0 > m2_0;

#line 2308
                            }
                            else
                            {

#line 2308
                                _S33 = false;

#line 2308
                            }

#line 2308
                            uint m2_1;

#line 2308
                            uint s2_1;

#line 2308
                            float2 v2_1;

#line 2308
                            if(_S33)
                            {

#line 2308
                                float2 _S79 = float2(rx_0, ry_0);

#line 2308
                                m2_1 = mag_0;

#line 2308
                                s2_1 = slot_1;

#line 2308
                                v2_1 = _S79;

#line 2308
                            }
                            else
                            {

#line 2308
                                m2_1 = m2_0;

#line 2308
                                s2_1 = s2_0;

#line 2308
                                v2_1 = v2_0;

#line 2308
                            }

#line 2308
                            if(_S44 >= 4U)
                            {

#line 2308
                                _S34 = b_6 == 3U;

#line 2308
                            }
                            else
                            {

#line 2308
                                _S34 = false;

#line 2308
                            }

#line 2308
                            if(_S34)
                            {

#line 2308
                                _S35 = mag_0 > m3_0;

#line 2308
                            }
                            else
                            {

#line 2308
                                _S35 = false;

#line 2308
                            }

#line 2308
                            uint m3_1;

#line 2308
                            uint s3_1;

#line 2308
                            float2 v3_1;

#line 2308
                            if(_S35)
                            {

#line 2308
                                float2 _S80 = float2(rx_0, ry_0);

#line 2308
                                m3_1 = mag_0;

#line 2308
                                s3_1 = slot_1;

#line 2308
                                v3_1 = _S80;

#line 2308
                            }
                            else
                            {

#line 2308
                                m3_1 = m3_0;

#line 2308
                                s3_1 = s3_0;

#line 2308
                                v3_1 = v3_0;

#line 2308
                            }

#line 2308
                            d_4 = m0_0;

#line 2308
                            m1_1 = m1_0;

#line 2308
                            m2_0 = m2_1;

#line 2308
                            m3_0 = m3_1;

#line 2308
                            s0_1 = s0_0;

#line 2308
                            s1_0 = s1_1;

#line 2308
                            s2_0 = s2_1;

#line 2308
                            s3_0 = s3_1;

#line 2308
                            v0_0 = v0_1;

#line 2308
                            v1_0 = v1_1;

#line 2308
                            v2_0 = v2_1;

#line 2308
                            v3_0 = v3_1;

#line 2308
                        }

#line 2308
                        i_5 = i_5 + 1U;

#line 2308
                    }

#line 2308
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                    uint wm0_0 = simd_max(d_4);

#line 2308
                    bool _S81 = simd_is_first();

#line 2308
                    if(_S81)
                    {

#line 2308
                        isCand_0 = wm0_0 > _S45;

#line 2308
                    }
                    else
                    {

#line 2308
                        isCand_0 = false;

#line 2308
                    }

#line 2308
                    if(isCand_0)
                    {

#line 2308
                        uint _S82 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), wm0_0, memory_order_relaxed);

#line 2308
                    }

#line 2308
                    bool _S83 = _S44 >= 2U;

#line 2308
                    if(_S83)
                    {

#line 2308
                        uint wm1_0 = simd_max(m1_1);

#line 2308
                        bool _S84 = simd_is_first();

#line 2308
                        if(_S84)
                        {

#line 2308
                            _S29 = wm1_0 > _S45;

#line 2308
                        }
                        else
                        {

#line 2308
                            _S29 = false;

#line 2308
                        }

#line 2308
                        if(_S29)
                        {

#line 2308
                            uint _S85 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), wm1_0, memory_order_relaxed);

#line 2308
                        }

#line 2308
                    }

#line 2308
                    bool _S86 = _S44 >= 3U;

#line 2308
                    if(_S86)
                    {

#line 2308
                        uint wm2_0 = simd_max(m2_0);

#line 2308
                        bool _S87 = simd_is_first();

#line 2308
                        if(_S87)
                        {

#line 2308
                            _S29 = wm2_0 > _S45;

#line 2308
                        }
                        else
                        {

#line 2308
                            _S29 = false;

#line 2308
                        }

#line 2308
                        if(_S29)
                        {

#line 2308
                            uint _S88 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U])), wm2_0, memory_order_relaxed);

#line 2308
                        }

#line 2308
                    }

#line 2308
                    bool _S89 = _S44 >= 4U;

#line 2308
                    if(_S89)
                    {

#line 2308
                        uint wm3_0 = simd_max(m3_0);

#line 2308
                        bool _S90 = simd_is_first();

#line 2308
                        if(_S90)
                        {

#line 2308
                            _S29 = wm3_0 > _S45;

#line 2308
                        }
                        else
                        {

#line 2308
                            _S29 = false;

#line 2308
                        }

#line 2308
                        if(_S29)
                        {

#line 2308
                            uint _S91 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U])), wm3_0, memory_order_relaxed);

#line 2308
                        }

#line 2308
                    }

#line 2308
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                    if(s0_1 != 4294967295U)
                    {

#line 2308
                        _S29 = d_4 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0];

#line 2308
                    }
                    else
                    {

#line 2308
                        _S29 = false;

#line 2308
                    }

#line 2308
                    if(_S29)
                    {

#line 2308
                        b_6 = s0_1;

#line 2308
                    }
                    else
                    {

#line 2308
                        b_6 = 4294967295U;

#line 2308
                    }

#line 2308
                    if(_S83)
                    {

#line 2308
                        _S30 = s1_0 != 4294967295U;

#line 2308
                    }
                    else
                    {

#line 2308
                        _S30 = false;

#line 2308
                    }

#line 2308
                    if(_S30)
                    {

#line 2308
                        _S31 = m1_1 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U];

#line 2308
                    }
                    else
                    {

#line 2308
                        _S31 = false;

#line 2308
                    }

#line 2308
                    if(_S31)
                    {

#line 2308
                        m0_0 = s1_0;

#line 2308
                    }
                    else
                    {

#line 2308
                        m0_0 = 4294967295U;

#line 2308
                    }

#line 2308
                    if(_S86)
                    {

#line 2308
                        _S32 = s2_0 != 4294967295U;

#line 2308
                    }
                    else
                    {

#line 2308
                        _S32 = false;

#line 2308
                    }

#line 2308
                    if(_S32)
                    {

#line 2308
                        _S33 = m2_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U];

#line 2308
                    }
                    else
                    {

#line 2308
                        _S33 = false;

#line 2308
                    }

#line 2308
                    if(_S33)
                    {

#line 2308
                        s0_0 = s2_0;

#line 2308
                    }
                    else
                    {

#line 2308
                        s0_0 = 4294967295U;

#line 2308
                    }

#line 2308
                    if(_S89)
                    {

#line 2308
                        _S34 = s3_0 != 4294967295U;

#line 2308
                    }
                    else
                    {

#line 2308
                        _S34 = false;

#line 2308
                    }

#line 2308
                    if(_S34)
                    {

#line 2308
                        _S35 = m3_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U];

#line 2308
                    }
                    else
                    {

#line 2308
                        _S35 = false;

#line 2308
                    }

#line 2308
                    if(_S35)
                    {

#line 2308
                        m1_0 = s3_0;

#line 2308
                    }
                    else
                    {

#line 2308
                        m1_0 = 4294967295U;

#line 2308
                    }

#line 2308
                    uint ww0_0 = simd_min(b_6);

#line 2308
                    bool _S92 = simd_is_first();

#line 2308
                    bool _S93;

#line 2308
                    if(_S92)
                    {

#line 2308
                        _S93 = ww0_0 != 4294967295U;

#line 2308
                    }
                    else
                    {

#line 2308
                        _S93 = false;

#line 2308
                    }

#line 2308
                    if(_S93)
                    {

#line 2308
                        uint _S94 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U])), ww0_0, memory_order_relaxed);

#line 2308
                    }

#line 2308
                    bool _S95;

#line 2308
                    if(_S83)
                    {

#line 2308
                        uint ww1_0 = simd_min(m0_0);

#line 2308
                        bool _S96 = simd_is_first();

#line 2308
                        if(_S96)
                        {

#line 2308
                            _S95 = ww1_0 != 4294967295U;

#line 2308
                        }
                        else
                        {

#line 2308
                            _S95 = false;

#line 2308
                        }

#line 2308
                        if(_S95)
                        {

#line 2308
                            uint _S97 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U])), ww1_0, memory_order_relaxed);

#line 2308
                        }

#line 2308
                    }

#line 2308
                    if(_S86)
                    {

#line 2308
                        uint ww2_0 = simd_min(s0_0);

#line 2308
                        bool _S98 = simd_is_first();

#line 2308
                        if(_S98)
                        {

#line 2308
                            _S95 = ww2_0 != 4294967295U;

#line 2308
                        }
                        else
                        {

#line 2308
                            _S95 = false;

#line 2308
                        }

#line 2308
                        if(_S95)
                        {

#line 2308
                            uint _S99 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U])), ww2_0, memory_order_relaxed);

#line 2308
                        }

#line 2308
                    }

#line 2308
                    if(_S89)
                    {

#line 2308
                        uint ww3_0 = simd_min(m1_0);

#line 2308
                        bool _S100 = simd_is_first();

#line 2308
                        if(_S100)
                        {

#line 2308
                            _S95 = ww3_0 != 4294967295U;

#line 2308
                        }
                        else
                        {

#line 2308
                            _S95 = false;

#line 2308
                        }

#line 2308
                        if(_S95)
                        {

#line 2308
                            uint _S101 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U])), ww3_0, memory_order_relaxed);

#line 2308
                        }

#line 2308
                    }

#line 2308
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                    uint baseOut_0 = pair_0 * _S44;

#line 2308
                    if(b_6 != 4294967295U)
                    {

#line 2308
                        _S95 = b_6 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U];

#line 2308
                    }
                    else
                    {

#line 2308
                        _S95 = false;

#line 2308
                    }

#line 2308
                    if(_S95)
                    {

#line 2308
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+baseOut_0) = int(slotToIndex_0(b_6));

#line 2308
                        *((&kernelContext_3)->entryPointParams_peakVal_0+baseOut_0) = packed_float2(v0_0) ;

#line 2308
                    }

#line 2308
                    bool _S102;

#line 2308
                    if(_S83)
                    {

#line 2308
                        _S102 = m0_0 != 4294967295U;

#line 2308
                    }
                    else
                    {

#line 2308
                        _S102 = false;

#line 2308
                    }

#line 2308
                    bool _S103;

#line 2308
                    if(_S102)
                    {

#line 2308
                        _S103 = m0_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U];

#line 2308
                    }
                    else
                    {

#line 2308
                        _S103 = false;

#line 2308
                    }

#line 2308
                    if(_S103)
                    {

#line 2308
                        uint _S104 = baseOut_0 + 1U;

#line 2308
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+_S104) = int(slotToIndex_0(m0_0));

#line 2308
                        *((&kernelContext_3)->entryPointParams_peakVal_0+_S104) = packed_float2(v1_0) ;

#line 2308
                    }

#line 2308
                    bool _S105;

#line 2308
                    if(_S86)
                    {

#line 2308
                        _S105 = s0_0 != 4294967295U;

#line 2308
                    }
                    else
                    {

#line 2308
                        _S105 = false;

#line 2308
                    }

#line 2308
                    bool _S106;

#line 2308
                    if(_S105)
                    {

#line 2308
                        _S106 = s0_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U];

#line 2308
                    }
                    else
                    {

#line 2308
                        _S106 = false;

#line 2308
                    }

#line 2308
                    if(_S106)
                    {

#line 2308
                        uint _S107 = baseOut_0 + 2U;

#line 2308
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+_S107) = int(slotToIndex_0(s0_0));

#line 2308
                        *((&kernelContext_3)->entryPointParams_peakVal_0+_S107) = packed_float2(v2_0) ;

#line 2308
                    }

#line 2308
                    bool _S108;

#line 2308
                    if(_S89)
                    {

#line 2308
                        _S108 = m1_0 != 4294967295U;

#line 2308
                    }
                    else
                    {

#line 2308
                        _S108 = false;

#line 2308
                    }

#line 2308
                    bool _S109;

#line 2308
                    if(_S108)
                    {

#line 2308
                        _S109 = m1_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U];

#line 2308
                    }
                    else
                    {

#line 2308
                        _S109 = false;

#line 2308
                    }

#line 2308
                    if(_S109)
                    {

#line 2308
                        uint _S110 = baseOut_0 + 3U;

#line 2308
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+_S110) = int(slotToIndex_0(m1_0));

#line 2308
                        *((&kernelContext_3)->entryPointParams_peakVal_0+_S110) = packed_float2(v3_0) ;

#line 2308
                    }

#line 2308
                    bool _S111;

#line 2308
                    if(_S38 < _S44)
                    {

#line 2308
                        _S111 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _S38]) == 4294967295U;

#line 2308
                    }
                    else
                    {

#line 2308
                        _S111 = false;

#line 2308
                    }

#line 2308
                    if(_S111)
                    {

#line 2308
                        uint _S112 = baseOut_0 + _S38;

#line 2308
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+_S112) = int(-1);

#line 2308
                        *((&kernelContext_3)->entryPointParams_peakVal_0+_S112) = packed_float2(_S75) ;

#line 2308
                    }

#line 2308
                }
                else
                {

#line 2308
                    d_4 = _S38;

#line 2308
                    for(;;)
                    {

#line 2308
                        if(d_4 < _S44)
                        {
                        }
                        else
                        {

#line 2308
                            break;
                        }

#line 2308
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + d_4] = _S45;

#line 2308
                        d_4 = d_4 + 512U;

#line 2308
                    }

#line 2308
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                    s0_1 = 0U;

#line 2308
                    m1_1 = 0U;

#line 2308
                    s1_0 = 0U;

#line 2308
                    for(;;)
                    {

#line 2308
                        if(s0_1 < 16U)
                        {
                        }
                        else
                        {

#line 2308
                            break;
                        }

#line 2308
                        uint idx_2 = slotToIndex_0(_S38 * 16U + s0_1);

#line 2308
                        if(idx_2 >= _S39)
                        {

#line 2308
                            isCand_0 = idx_2 < _S40;

#line 2308
                        }
                        else
                        {

#line 2308
                            isCand_0 = false;

#line 2308
                        }

#line 2308
                        if(isCand_0)
                        {

#line 2308
                            float rx_1 = r_3[s0_1].x;

#line 2308
                            float ry_1 = r_3[s0_1].y;

#line 2308
                            uint mag_1 = (as_type<uint>((rx_1 * rx_1 + ry_1 * ry_1)));

#line 2308
                            if(mag_1 > _S45)
                            {

#line 2308
                                uint off_1 = idx_2 - _S39 + (&kernelContext_3)->_binPhase_0;

#line 2308
                                if(_S43 >= int(0))
                                {

#line 2308
                                    m2_0 = off_1 >> uint(_S43);

#line 2308
                                }
                                else
                                {

#line 2308
                                    uint _S113 = off_1 / _S42;

#line 2308
                                    m2_0 = _S113;

#line 2308
                                }

#line 2308
                                uint _S114 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m2_0])), mag_1, memory_order_relaxed);

#line 2308
                                uint bit_0 = 1U << (s0_1 & 31U);

#line 2308
                                if(s0_1 < 32U)
                                {

#line 2308
                                    i_5 = m1_1 | bit_0;

#line 2308
                                    s2_0 = s1_0;

#line 2308
                                }
                                else
                                {

#line 2308
                                    uint aboveHi_0 = s1_0 | bit_0;

#line 2308
                                    i_5 = m1_1;

#line 2308
                                    s2_0 = aboveHi_0;

#line 2308
                                }

#line 2308
                            }
                            else
                            {

#line 2308
                                i_5 = m1_1;

#line 2308
                                s2_0 = s1_0;

#line 2308
                            }

#line 2308
                        }
                        else
                        {

#line 2308
                            i_5 = m1_1;

#line 2308
                            s2_0 = s1_0;

#line 2308
                        }

#line 2308
                        s0_1 = s0_1 + 1U;

#line 2308
                        m1_1 = i_5;

#line 2308
                        s1_0 = s2_0;

#line 2308
                    }

#line 2308
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                    if((m1_1 | s1_0) != 0U)
                    {

#line 2308
                        i_5 = 0U;

#line 2308
                        m2_0 = 0U;

#line 2308
                        s2_0 = 0U;

#line 2308
                        for(;;)
                        {

#line 2308
                            if(i_5 < 16U)
                            {
                            }
                            else
                            {

#line 2308
                                break;
                            }

#line 2308
                            uint bit_1 = 1U << (i_5 & 31U);

#line 2308
                            bool _S115 = i_5 < 32U;

#line 2308
                            if(_S115)
                            {

#line 2308
                                isCand_0 = (m1_1 & bit_1) != 0U;

#line 2308
                            }
                            else
                            {

#line 2308
                                isCand_0 = (s1_0 & bit_1) != 0U;

#line 2308
                            }

#line 2308
                            if(isCand_0)
                            {

#line 2308
                                uint off_2 = slotToIndex_0(_S38 * 16U + i_5) - _S39 + (&kernelContext_3)->_binPhase_0;

#line 2308
                                if(_S43 >= int(0))
                                {

#line 2308
                                    m3_0 = off_2 >> uint(_S43);

#line 2308
                                }
                                else
                                {

#line 2308
                                    uint _S116 = off_2 / _S42;

#line 2308
                                    m3_0 = _S116;

#line 2308
                                }

#line 2308
                                float rx_2 = r_3[i_5].x;

#line 2308
                                float ry_2 = r_3[i_5].y;

#line 2308
                                if((as_type<uint>((rx_2 * rx_2 + ry_2 * ry_2))) == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m3_0])
                                {

#line 2308
                                    if(_S115)
                                    {

#line 2308
                                        s3_0 = m2_0 | bit_1;

#line 2308
                                        b_6 = s2_0;

#line 2308
                                    }
                                    else
                                    {

#line 2308
                                        uint candHi_0 = s2_0 | bit_1;

#line 2308
                                        s3_0 = m2_0;

#line 2308
                                        b_6 = candHi_0;

#line 2308
                                    }

#line 2308
                                }
                                else
                                {

#line 2308
                                    s3_0 = m2_0;

#line 2308
                                    b_6 = s2_0;

#line 2308
                                }

#line 2308
                            }
                            else
                            {

#line 2308
                                s3_0 = m2_0;

#line 2308
                                b_6 = s2_0;

#line 2308
                            }

#line 2308
                            i_5 = i_5 + 1U;

#line 2308
                            m2_0 = s3_0;

#line 2308
                            s2_0 = b_6;

#line 2308
                        }

#line 2308
                        s3_0 = m2_0;

#line 2308
                        b_6 = s2_0;

#line 2308
                    }
                    else
                    {

#line 2308
                        s3_0 = 0U;

#line 2308
                        b_6 = 0U;

#line 2308
                    }

#line 2308
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                    m3_0 = _S38;

#line 2308
                    for(;;)
                    {

#line 2308
                        if(m3_0 < _S44)
                        {
                        }
                        else
                        {

#line 2308
                            break;
                        }

#line 2308
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m3_0] = 4294967295U;

#line 2308
                        m3_0 = m3_0 + 512U;

#line 2308
                    }

#line 2308
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                    bool _S117 = (s3_0 | b_6) != 0U;

#line 2308
                    if(_S117)
                    {

#line 2308
                        i_5 = 0U;

#line 2308
                        for(;;)
                        {

#line 2308
                            if(i_5 < 16U)
                            {
                            }
                            else
                            {

#line 2308
                                break;
                            }

#line 2308
                            uint bit_2 = 1U << (i_5 & 31U);

#line 2308
                            if(i_5 < 32U)
                            {

#line 2308
                                isCand_0 = (s3_0 & bit_2) != 0U;

#line 2308
                            }
                            else
                            {

#line 2308
                                isCand_0 = (b_6 & bit_2) != 0U;

#line 2308
                            }

#line 2308
                            if(isCand_0)
                            {

#line 2308
                                uint _S118 = _S38 * 16U + i_5;

#line 2308
                                uint off_3 = slotToIndex_0(_S118) - _S39 + (&kernelContext_3)->_binPhase_0;

#line 2308
                                if(_S43 >= int(0))
                                {

#line 2308
                                    m2_0 = off_3 >> uint(_S43);

#line 2308
                                }
                                else
                                {

#line 2308
                                    uint _S119 = off_3 / _S42;

#line 2308
                                    m2_0 = _S119;

#line 2308
                                }

#line 2308
                                uint _S120 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m2_0])), _S118, memory_order_relaxed);

#line 2308
                            }

#line 2308
                            i_5 = i_5 + 1U;

#line 2308
                        }

#line 2308
                    }

#line 2308
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                    if(_S117)
                    {

#line 2308
                        i_5 = 0U;

#line 2308
                        for(;;)
                        {

#line 2308
                            if(i_5 < 16U)
                            {
                            }
                            else
                            {

#line 2308
                                break;
                            }

#line 2308
                            uint bit_3 = 1U << (i_5 & 31U);

#line 2308
                            if(i_5 < 32U)
                            {

#line 2308
                                isCand_0 = (s3_0 & bit_3) != 0U;

#line 2308
                            }
                            else
                            {

#line 2308
                                isCand_0 = (b_6 & bit_3) != 0U;

#line 2308
                            }

#line 2308
                            if(isCand_0)
                            {

#line 2308
                                uint _S121 = _S38 * 16U + i_5;

#line 2308
                                uint idx_3 = slotToIndex_0(_S121);

#line 2308
                                uint off_4 = idx_3 - _S39 + (&kernelContext_3)->_binPhase_0;

#line 2308
                                if(_S43 >= int(0))
                                {

#line 2308
                                    m2_0 = off_4 >> uint(_S43);

#line 2308
                                }
                                else
                                {

#line 2308
                                    uint _S122 = off_4 / _S42;

#line 2308
                                    m2_0 = _S122;

#line 2308
                                }

#line 2308
                                if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m2_0]) == _S121)
                                {

#line 2308
                                    uint o_1 = pair_0 * _S44 + m2_0;

#line 2308
                                    *((&kernelContext_3)->entryPointParams_peakIdx_0+o_1) = int(idx_3);

#line 2308
                                    *((&kernelContext_3)->entryPointParams_peakVal_0+o_1) = packed_float2(float2(r_3[i_5].x, r_3[i_5].y)) ;

#line 2308
                                }

#line 2308
                            }

#line 2308
                            i_5 = i_5 + 1U;

#line 2308
                        }

#line 2308
                    }

#line 2308
                    m2_0 = _S38;

#line 2308
                    for(;;)
                    {

#line 2308
                        if(m2_0 < _S44)
                        {
                        }
                        else
                        {

#line 2308
                            break;
                        }

#line 2308
                        if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m2_0]) == 4294967295U)
                        {

#line 2308
                            uint _S123 = pair_0 * _S44 + m2_0;

#line 2308
                            *((&kernelContext_3)->entryPointParams_peakIdx_0+_S123) = int(-1);

#line 2308
                            *((&kernelContext_3)->entryPointParams_peakVal_0+_S123) = packed_float2(float2(0.0f, 0.0f)) ;

#line 2308
                        }

#line 2308
                        m2_0 = m2_0 + 512U;

#line 2308
                    }

#line 2308
                }

#line 2308
                break;
            }

#line 2308
            break;
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2304
        i_4 = i_4 + (&kernelContext_3)->entryPointParams_0->gridSize_0;

#line 2304
    }

#line 2312
    return;
}
