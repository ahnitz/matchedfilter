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


#line 808 "mm_8192_refineListed_onebin.slang"
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
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 228
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 92 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 231 "mm_8192_refineListed_onebin.slang"
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


#line 174 "mm_8192_refineListed_onebin.slang"
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


#line 331 "mm_8192_refineListed_onebin.slang"
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
uint lgOf_0(uint i_1)
{

#line 881
    uint _S20;

#line 881
    if(i_1 < 3U)
    {

#line 881
        _S20 = 4U;

#line 881
    }
    else
    {

#line 881
        _S20 = 1U;

#line 881
    }

#line 881
    return _S20;
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
    uint _S21;

#line 2292
    uint _S22;

#line 2292
    uint _S23;

#line 2292
    uint _S24;

#line 2292
    uint _S25;

#line 2292
    uint _S26;

#line 2292
    thread KernelContext_0 kernelContext_1;

#line 2292
    (&kernelContext_1)->entryPointParams_0 = entryPointParams_1;

#line 2292
    (&kernelContext_1)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2292
    (&kernelContext_1)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2292
    (&kernelContext_1)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2292
    (&kernelContext_1)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2292
    (&kernelContext_1)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2292
    (&kernelContext_1)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2292
    (&kernelContext_1)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 2292
    threadgroup array<uint, int(8192)> stg_1;

#line 2292
    (&kernelContext_1)->stg_0 = &stg_1;

#line 2292
    (&kernelContext_1)->_binPhase_0 = 0U;

#line 2303
    uint _S27 = entryPointParams_count_1[int(0)];

#line 2303
    uint i_2 = gid_0.x;
    for(;;)
    {

#line 2304
        if(i_2 < _S27)
        {
        }
        else
        {

#line 2304
            break;
        }

#line 2305
        (&kernelContext_1)->_stgBase_0 = 0U;
        uint pair_0 = (&kernelContext_1)->entryPointParams_survivors_0[i_2];

#line 2306
        thread uint ws_0 = (&kernelContext_1)->entryPointParams_0->winStart_0;

#line 2306
        thread uint we_0 = (&kernelContext_1)->entryPointParams_0->winEnd_0;
        uint _S28 = pair_0 / (&kernelContext_1)->entryPointParams_0->ntmpl_0;

#line 2307
        rowWindow_0(_S28, &ws_0, &we_0, (&kernelContext_1)->entryPointParams_rowWin_0, &kernelContext_1);
        uint _S29 = lid_0.x;

#line 2308
        uint _S30 = ws_0;

#line 2308
        uint _S31 = we_0;

#line 2308
        uint _S32 = (&kernelContext_1)->entryPointParams_0->ntmpl_0;

#line 2308
        uint _S33 = (&kernelContext_1)->entryPointParams_0->thrBits_0;

#line 2308
        for(;;)
        {

#line 2308
            for(;;)
            {

#line 2308
                (&kernelContext_1)->_tid_0 = _S29;

#line 2308
                uint _S34 = pair_0 / _S32;

#line 2308
                uint _S35 = pair_0 % _S32;

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
                    uint idx_0 = _S29 + 512U * n2_0;

#line 2308
                    uint _S36 = mfDataStrideFlag_0();

#line 2308
                    if(_S36 != 0U)
                    {

#line 2308
                        uint _S37 = mfDataStrideFlag_0();

#line 2308
                        k2_1 = _S37;

#line 2308
                    }
                    else
                    {

#line 2308
                        k2_1 = 8192U;

#line 2308
                    }

#line 2308
                    r_3[n2_0] = cmulConj_0(cload_0((&kernelContext_1)->entryPointParams_data_0, _S34 * k2_1 + idx_0), cload_0((&kernelContext_1)->entryPointParams_tmpl_0, _S35 * 8192U + idx_0));

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
                                _S21 = lgTB_0;

#line 2308
                                uint lgLn_0 = firstbithigh_0(8192U);

#line 2308
                                uint blk_1 = _S29 >> lgTB_0;

#line 2308
                                uint lane_1 = _S29 & 511U;

#line 2308
                                dft16_0(&r_3);

#line 2308
                                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 8192.0f);

#line 2308
                                float _S38 = tw_0.x;

#line 2308
                                float _S39 = tw_0.y;

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
                                    float nr_0 = cr_0 * _S38 - ci_0 * _S39;

#line 2308
                                    float _S40 = cr_0 * _S39 + ci_0 * _S38;

#line 2308
                                    k2_1 = k2_1 + 1U;

#line 2308
                                    cr_0 = nr_0;

#line 2308
                                    ci_0 = _S40;

#line 2308
                                }

#line 2308
                                uint per_1 = 16U / max(512U, 1U);

#line 2308
                                uint _S41 = max(32U, 1U);

#line 2308
                                _S22 = _S41;

#line 2308
                                uint blk2_1 = _S29 / _S41;

#line 2308
                                uint lane2_1 = _S29 % _S41;

#line 2308
                                for(;;)
                                {

#line 2308
                                    uint _S42 = (1U << lgTB_0) - 1U;

#line 2308
                                    _S23 = _S42;

#line 2308
                                    uint _S43 = (1U << lgLn_0) - 1U;

#line 2308
                                    thread array<uint, int(16)> src_0;

#line 2308
                                    uint d_3 = 0U;

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
                                        uint p_0 = computeWant_0(d_3, 512U, 8192U, blk_1, lane_1, per_1, _S41, 512U, blk2_1, lane2_1);

#line 2308
                                        uint rem_0 = p_0 & _S43;

#line 2308
                                        src_0[d_3] = (rem_0 >> lgTB_0) * 512U + ((p_0 >> lgLn_0) << lgTB_0) + (rem_0 & _S42);

#line 2308
                                        d_3 = d_3 + 1U;

#line 2308
                                    }

#line 2308
                                    thread array<float, int(16)> xr_0;

#line 2308
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                                    uint j_1 = 0U;

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
                                        (*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + j_1 * 512U + (&kernelContext_1)->_tid_0] = (as_type<uint>((r_3[j_1].x)));

#line 2308
                                        j_1 = j_1 + 1U;

#line 2308
                                    }

#line 2308
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                                    uint d_4 = 0U;

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
                                        xr_0[d_4] = (as_type<float>(((*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + src_0[d_4]])));

#line 2308
                                        d_4 = d_4 + 1U;

#line 2308
                                    }

#line 2308
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                                    uint j_2 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(j_2 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        (*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + j_2 * 512U + (&kernelContext_1)->_tid_0] = (as_type<uint>((r_3[j_2].y)));

#line 2308
                                        j_2 = j_2 + 1U;

#line 2308
                                    }

#line 2308
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

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
                                        r_3[d_5] = float2(xr_0[d_5], (as_type<float>(((*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + src_0[d_5]]))));

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
                                _S24 = lgTB_1;

#line 2308
                                uint blk_2 = _S29 >> lgTB_1;

#line 2308
                                uint lane_2 = _S29 & 31U;

#line 2308
                                dft16_0(&r_3);

#line 2308
                                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 512.0f);

#line 2308
                                float _S44 = tw_1.x;

#line 2308
                                float _S45 = tw_1.y;

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
                                    float nr_1 = cr_1 * _S44 - ci_1 * _S45;

#line 2308
                                    float _S46 = cr_1 * _S45 + ci_1 * _S44;

#line 2308
                                    k2_2 = k2_2 + 1U;

#line 2308
                                    cr_1 = nr_1;

#line 2308
                                    ci_1 = _S46;

#line 2308
                                }

#line 2308
                                uint per_2 = 16U / _S22;

#line 2308
                                uint _S47 = max(2U, 1U);

#line 2308
                                _S25 = _S47;

#line 2308
                                uint blk2_2 = _S29 / _S47;

#line 2308
                                uint lane2_2 = _S29 % _S47;

#line 2308
                                for(;;)
                                {

#line 2308
                                    uint _S48 = (1U << lgTB_1) - 1U;

#line 2308
                                    _S26 = _S48;

#line 2308
                                    thread array<uint, int(16)> src_1;

#line 2308
                                    uint d_6 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(d_6 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        uint p_1 = computeWant_0(d_6, 32U, 512U, blk_2, lane_2, per_2, _S47, 32U, blk2_2, lane2_2);

#line 2308
                                        uint rem_1 = p_1 & _S23;

#line 2308
                                        src_1[d_6] = (rem_1 >> lgTB_1) * 512U + ((p_1 >> _S21) << lgTB_1) + (rem_1 & _S48);

#line 2308
                                        d_6 = d_6 + 1U;

#line 2308
                                    }

#line 2308
                                    thread array<float, int(16)> xr_1;

#line 2308
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                                    uint j_3 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(j_3 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        (*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + j_3 * 512U + (&kernelContext_1)->_tid_0] = (as_type<uint>((r_3[j_3].x)));

#line 2308
                                        j_3 = j_3 + 1U;

#line 2308
                                    }

#line 2308
                                    simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2308
                                    uint d_7 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(d_7 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        xr_1[d_7] = (as_type<float>(((*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + src_1[d_7]])));

#line 2308
                                        d_7 = d_7 + 1U;

#line 2308
                                    }

#line 2308
                                    simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2308
                                    uint j_4 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(j_4 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        (*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + j_4 * 512U + (&kernelContext_1)->_tid_0] = (as_type<uint>((r_3[j_4].y)));

#line 2308
                                        j_4 = j_4 + 1U;

#line 2308
                                    }

#line 2308
                                    simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2308
                                    uint d_8 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(d_8 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        r_3[d_8] = float2(xr_1[d_8], (as_type<float>(((*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + src_1[d_8]]))));

#line 2308
                                        d_8 = d_8 + 1U;

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
                                uint blk_3 = _S29 >> lgTB_2;

#line 2308
                                uint lane_3 = _S29 & 1U;

#line 2308
                                dft16_0(&r_3);

#line 2308
                                float2 tw_2 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 32.0f);

#line 2308
                                float _S49 = tw_2.x;

#line 2308
                                float _S50 = tw_2.y;

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
                                    float nr_2 = cr_2 * _S49 - ci_2 * _S50;

#line 2308
                                    float _S51 = cr_2 * _S50 + ci_2 * _S49;

#line 2308
                                    k2_3 = k2_3 + 1U;

#line 2308
                                    cr_2 = nr_2;

#line 2308
                                    ci_2 = _S51;

#line 2308
                                }

#line 2308
                                uint per_3 = 16U / _S25;

#line 2308
                                uint _S52 = max(0U, 1U);

#line 2308
                                uint blk2_3 = _S29 / _S52;

#line 2308
                                uint lane2_3 = _S29 % _S52;

#line 2308
                                for(;;)
                                {

#line 2308
                                    uint _S53 = (1U << lgTB_2) - 1U;

#line 2308
                                    thread array<uint, int(16)> src_2;

#line 2308
                                    uint d_9 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(d_9 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        uint p_2 = computeWant_0(d_9, 2U, 32U, blk_3, lane_3, per_3, _S52, 2U, blk2_3, lane2_3);

#line 2308
                                        uint rem_2 = p_2 & _S26;

#line 2308
                                        src_2[d_9] = (rem_2 >> lgTB_2) * 512U + ((p_2 >> _S24) << lgTB_2) + (rem_2 & _S53);

#line 2308
                                        d_9 = d_9 + 1U;

#line 2308
                                    }

#line 2308
                                    thread array<float, int(16)> xr_2;

#line 2308
                                    simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2308
                                    uint j_5 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(j_5 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        (*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + j_5 * 512U + (&kernelContext_1)->_tid_0] = (as_type<uint>((r_3[j_5].x)));

#line 2308
                                        j_5 = j_5 + 1U;

#line 2308
                                    }

#line 2308
                                    simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2308
                                    uint d_10 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(d_10 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        xr_2[d_10] = (as_type<float>(((*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + src_2[d_10]])));

#line 2308
                                        d_10 = d_10 + 1U;

#line 2308
                                    }

#line 2308
                                    simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2308
                                    uint j_6 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(j_6 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        (*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + j_6 * 512U + (&kernelContext_1)->_tid_0] = (as_type<uint>((r_3[j_6].y)));

#line 2308
                                        j_6 = j_6 + 1U;

#line 2308
                                    }

#line 2308
                                    simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2308
                                    uint d_11 = 0U;

#line 2308
                                    for(;;)
                                    {

#line 2308
                                        if(d_11 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2308
                                            break;
                                        }

#line 2308
                                        r_3[d_11] = float2(xr_2[d_11], (as_type<float>(((*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + src_2[d_11]]))));

#line 2308
                                        d_11 = d_11 + 1U;

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
                float2 _S54 = float2(0.0f, 0.0f);

#line 2308
                bool _S55;

#line 2308
                if(_S30 == 0U)
                {

#line 2308
                    _S55 = _S31 >= 8192U;

#line 2308
                }
                else
                {

#line 2308
                    _S55 = false;

#line 2308
                }

#line 2308
                uint winner_0;

#line 2308
                uint threadBestBits_0;

#line 2308
                uint threadBestSlot_0;

#line 2308
                bool live_0;

#line 2308
                float2 threadBestVal_0;

#line 2308
                if(_S55)
                {

#line 2308
                    winner_0 = 0U;

#line 2308
                    threadBestBits_0 = _S33;

#line 2308
                    threadBestSlot_0 = 4294967295U;

#line 2308
                    threadBestVal_0 = _S54;

#line 2308
                    for(;;)
                    {

#line 2308
                        if(winner_0 < 16U)
                        {
                        }
                        else
                        {

#line 2308
                            break;
                        }

#line 2308
                        float _rx_0 = r_3[winner_0].x;

#line 2308
                        float _ry_0 = r_3[winner_0].y;

#line 2308
                        uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 2308
                        if(magBits_0 > threadBestBits_0)
                        {

#line 2308
                            uint _S56 = _S29 * 16U + winner_0;

#line 2308
                            float2 _S57 = float2(_rx_0, _ry_0);

#line 2308
                            threadBestBits_0 = magBits_0;

#line 2308
                            threadBestSlot_0 = _S56;

#line 2308
                            threadBestVal_0 = _S57;

#line 2308
                        }

#line 2308
                        winner_0 = winner_0 + 1U;

#line 2308
                    }

#line 2308
                }
                else
                {

#line 2308
                    winner_0 = 0U;

#line 2308
                    threadBestBits_0 = _S33;

#line 2308
                    threadBestSlot_0 = 4294967295U;

#line 2308
                    threadBestVal_0 = _S54;

#line 2308
                    for(;;)
                    {

#line 2308
                        if(winner_0 < 16U)
                        {
                        }
                        else
                        {

#line 2308
                            break;
                        }

#line 2308
                        uint _S58 = _S29 * 16U + winner_0;

#line 2308
                        uint idx_1 = slotToIndex_0(_S58);

#line 2308
                        if(idx_1 >= _S30)
                        {

#line 2308
                            live_0 = idx_1 < _S31;

#line 2308
                        }
                        else
                        {

#line 2308
                            live_0 = false;

#line 2308
                        }

#line 2308
                        float _rx_1 = r_3[winner_0].x;

#line 2308
                        float _ry_1 = r_3[winner_0].y;

#line 2308
                        uint magBits_1;

#line 2308
                        if(live_0)
                        {

#line 2308
                            magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 2308
                        }
                        else
                        {

#line 2308
                            magBits_1 = 0U;

#line 2308
                        }

#line 2308
                        if(magBits_1 > threadBestBits_0)
                        {

#line 2308
                            float2 _S59 = float2(_rx_1, _ry_1);

#line 2308
                            threadBestBits_0 = magBits_1;

#line 2308
                            threadBestSlot_0 = _S58;

#line 2308
                            threadBestVal_0 = _S59;

#line 2308
                        }

#line 2308
                        winner_0 = winner_0 + 1U;

#line 2308
                    }

#line 2308
                }

#line 2308
                bool _S60 = _S29 == 0U;

#line 2308
                if(_S60)
                {

#line 2308
                    (*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0] = _S33;

#line 2308
                    (*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + 1U] = 4294967295U;

#line 2308
                }

#line 2308
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                uint wm_0 = simd_max(threadBestBits_0);

#line 2308
                bool _S61 = simd_is_first();

#line 2308
                if(_S61)
                {

#line 2308
                    live_0 = wm_0 > _S33;

#line 2308
                }
                else
                {

#line 2308
                    live_0 = false;

#line 2308
                }

#line 2308
                if(live_0)
                {

#line 2308
                    uint _S62 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0])), wm_0, memory_order_relaxed);

#line 2308
                }

#line 2308
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                bool _S63;

#line 2308
                if(threadBestBits_0 > _S33)
                {

#line 2308
                    _S63 = threadBestBits_0 == (*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0];

#line 2308
                }
                else
                {

#line 2308
                    _S63 = false;

#line 2308
                }

#line 2308
                if(_S63)
                {

#line 2308
                    winner_0 = threadBestSlot_0;

#line 2308
                }
                else
                {

#line 2308
                    winner_0 = 4294967295U;

#line 2308
                }

#line 2308
                uint waveWinner_0 = simd_min(winner_0);

#line 2308
                bool _S64 = simd_is_first();

#line 2308
                bool _S65;

#line 2308
                if(_S64)
                {

#line 2308
                    _S65 = waveWinner_0 != 4294967295U;

#line 2308
                }
                else
                {

#line 2308
                    _S65 = false;

#line 2308
                }

#line 2308
                if(_S65)
                {

#line 2308
                    uint _S66 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 2308
                }

#line 2308
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2308
                bool _S67;

#line 2308
                if(threadBestSlot_0 == (*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + 1U])
                {

#line 2308
                    _S67 = threadBestSlot_0 != 4294967295U;

#line 2308
                }
                else
                {

#line 2308
                    _S67 = false;

#line 2308
                }

#line 2308
                if(_S67)
                {

#line 2308
                    *((&kernelContext_1)->entryPointParams_peakIdx_0+pair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 2308
                    *((&kernelContext_1)->entryPointParams_peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 2308
                }

#line 2308
                bool _S68;

#line 2308
                if(_S60)
                {

#line 2308
                    _S68 = ((*(&kernelContext_1)->stg_0)[(&kernelContext_1)->_stgBase_0 + 1U]) == 4294967295U;

#line 2308
                }
                else
                {

#line 2308
                    _S68 = false;

#line 2308
                }

#line 2308
                if(_S68)
                {

#line 2308
                    *((&kernelContext_1)->entryPointParams_peakIdx_0+pair_0) = int(-1);

#line 2308
                    *((&kernelContext_1)->entryPointParams_peakVal_0+pair_0) = packed_float2(_S54) ;

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
        i_2 = i_2 + (&kernelContext_1)->entryPointParams_0->gridSize_0;

#line 2304
    }

#line 2312
    return;
}
