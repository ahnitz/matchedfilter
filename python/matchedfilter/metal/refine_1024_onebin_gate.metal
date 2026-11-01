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


#line 319 "mm_1024_refineListed_onebin_gate.slang"
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
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 229
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 92 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 232 "mm_1024_refineListed_onebin_gate.slang"
    if(_S3 == 0U)
    {

#line 232
        return;
    }

#line 233
    uint _S4 = 3U * d_0;

#line 233
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


#line 175 "mm_1024_refineListed_onebin_gate.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 175
    return float2(*(b_0+i_0)) ;
}


#line 331
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 331
    float _S6 = a_0.x;

#line 331
    float _S7 = b_1.x;

#line 331
    float _S8 = a_0.y;

#line 331
    float _S9 = b_1.y;

#line 331
    return float2(_S6 * _S7 + _S8 * _S9, _S8 * _S7 - _S6 * _S9);
}


#line 615
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 617
    float2 t1_0 = *a_1 - *c_0;

#line 617
    float2 t2_0 = *b_2 + *d_1;

#line 617
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 619
    *b_2 = t1_0 + j3_0;

#line 619
    *c_0 = t0_0 - t2_0;

#line 619
    *d_1 = t1_0 - j3_0;
    return;
}


#line 330
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 330
    float _S10 = a_2.x;

#line 330
    float _S11 = b_3.x;

#line 330
    float _S12 = a_2.y;

#line 330
    float _S13 = b_3.y;

#line 330
    return float2(_S10 * _S11 - _S12 * _S13, _S10 * _S13 + _S12 * _S11);
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
        uint _S14 = 4U * k2_0;

#line 663
        r4_0(&(*r_0)[_S14], &(*r_0)[_S14 + 1U], &(*r_0)[_S14 + 2U], &(*r_0)[_S14 + 3U]);

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


#line 332 "mm_1024_refineListed_onebin_gate.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S18 = max(TB_0, 1U);

#line 334
    uint j_0 = d_2 / _S18;

#line 334
    uint m_0 = d_2 % _S18;

#line 334
    uint _S19;
    if(TB_0 <= 16U)
    {

#line 335
        _S19 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 335
    }
    else
    {

#line 335
        _S19 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 335
    }

#line 335
    return _S19;
}


#line 319
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 319
    uint _S20 = 2U * i_1;

#line 319
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20] = (as_type<uint>((v_0.x)));

#line 319
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20 + 1U] = (as_type<uint>((v_0.y)));

#line 319
    return;
}


#line 320
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_2)
{

#line 320
    uint _S21 = 2U * i_2;

#line 320
    return float2((as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S21]))), (as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S21 + 1U]))));
}


#line 630
void dft4_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    r4_0(&(*r_1)[o_0], &(*r_1)[o_0 + 1U], &(*r_1)[o_0 + 2U], &(*r_1)[o_0 + 3U]);
    float2 t_6 = (*r_1)[o_0 + 1U];

#line 633
    (*r_1)[o_0 + 1U] = (*r_1)[o_0 + 2U];

#line 633
    (*r_1)[o_0 + 2U] = t_6;
    return;
}


#line 754
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 754
    uint b_4 = 0U;

#line 763
    for(;;)
    {

#line 763
        if(b_4 < 4U)
        {
        }
        else
        {

#line 763
            break;
        }

#line 763
        dft4_0(r_2, b_4 * 4U);

#line 763
        b_4 = b_4 + 1U;

#line 763
    }


    return;
}


#line 882
uint lgOf_0(uint i_3)
{

#line 882
    uint _S22;

#line 882
    if(i_3 < 2U)
    {

#line 882
        _S22 = 4U;

#line 882
    }
    else
    {

#line 882
        _S22 = 1U;

#line 882
    }

#line 882
    return _S22;
}


#line 884
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_1 = slot_0 >> lg_0;

#line 888
    uint lg_1 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_1;

#line 888
    uint lg_2 = lgOf_0(1U);

#line 888
    uint lg_3 = lgOf_0(0U);

#line 893
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | (x_2 & ((1U << lg_2) - 1U))) << lg_3) | ((x_2 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 2245
[[kernel]] void refineListedBounded(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]], uint device* entryPointParams_rowWin_1 [[buffer(7)]])
{

#line 2245
    uint k2_1;

#line 2245
    uint _S23;

#line 2245
    uint _S24;

#line 2245
    uint _S25;

#line 2245
    uint d_3;

#line 2245
    uint j_1;

#line 2245
    uint d_4;

#line 2245
    thread KernelContext_0 kernelContext_3;

#line 2245
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 2245
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2245
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2245
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2245
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2245
    (&kernelContext_3)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2245
    (&kernelContext_3)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2245
    (&kernelContext_3)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 2245
    threadgroup array<uint, int(2048)> stg_1;

#line 2245
    (&kernelContext_3)->stg_0 = &stg_1;

#line 2245
    (&kernelContext_3)->_binPhase_0 = 0U;

#line 2256
    uint _S26 = entryPointParams_count_1[int(0)];

#line 2256
    uint i_4 = gid_0.x;
    for(;;)
    {

#line 2257
        if(i_4 < _S26)
        {
        }
        else
        {

#line 2257
            break;
        }

#line 2258
        (&kernelContext_3)->_stgBase_0 = 0U;
        uint pair_0 = (&kernelContext_3)->entryPointParams_survivors_0[i_4];

#line 2259
        thread uint ws_0 = (&kernelContext_3)->entryPointParams_0->winStart_0;

#line 2259
        thread uint we_0 = (&kernelContext_3)->entryPointParams_0->winEnd_0;
        uint _S27 = pair_0 / (&kernelContext_3)->entryPointParams_0->ntmpl_0;

#line 2260
        rowWindow_0(_S27, &ws_0, &we_0, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);
        uint _S28 = lid_0.x;

#line 2261
        uint _S29 = ws_0;

#line 2261
        uint _S30 = we_0;

#line 2261
        uint _S31 = (&kernelContext_3)->entryPointParams_0->ntmpl_0;

#line 2261
        uint _S32 = (&kernelContext_3)->entryPointParams_0->nbins_0;

#line 2261
        uint _S33 = (&kernelContext_3)->entryPointParams_0->thrBits_0;

#line 2261
        for(;;)
        {

#line 2261
            for(;;)
            {

#line 2261
                bool gateOnly_0 = _S32 == 0U;

#line 2261
                (&kernelContext_3)->_tid_0 = _S28;

#line 2261
                uint _S34 = pair_0 / _S31;

#line 2261
                uint _S35 = pair_0 % _S31;

#line 2261
                thread array<float2, int(16)> r_3;

#line 2261
                uint n2_0 = 0U;

#line 2261
                for(;;)
                {

#line 2261
                    if(n2_0 < 16U)
                    {
                    }
                    else
                    {

#line 2261
                        break;
                    }

#line 2261
                    uint idx_0 = _S28 + 64U * n2_0;

#line 2261
                    uint _S36 = mfDataStrideFlag_0();

#line 2261
                    if(_S36 != 0U)
                    {

#line 2261
                        uint _S37 = mfDataStrideFlag_0();

#line 2261
                        k2_1 = _S37;

#line 2261
                    }
                    else
                    {

#line 2261
                        k2_1 = 1024U;

#line 2261
                    }

#line 2261
                    r_3[n2_0] = cmulConj_0(cload_0((&kernelContext_3)->entryPointParams_data_0, _S34 * k2_1 + idx_0), cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S35 * 1024U + idx_0));

#line 2261
                    n2_0 = n2_0 + 1U;

#line 2261
                }

#line 2261
                for(;;)
                {

#line 2261
                    for(;;)
                    {

#line 2261
                        for(;;)
                        {

#line 2261
                            for(;;)
                            {

#line 2261
                                uint lgTB_0 = firstbithigh_0(64U);

#line 2261
                                _S23 = lgTB_0;

#line 2261
                                uint lgLn_0 = firstbithigh_0(1024U);

#line 2261
                                uint blk_1 = _S28 >> lgTB_0;

#line 2261
                                uint lane_1 = _S28 & 63U;

#line 2261
                                dft16_0(&r_3);

#line 2261
                                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 1024.0f);

#line 2261
                                float _S38 = tw_0.x;

#line 2261
                                float _S39 = tw_0.y;

#line 2261
                                k2_1 = 0U;

#line 2261
                                float cr_0 = 1.0f;

#line 2261
                                float ci_0 = 0.0f;

#line 2261
                                for(;;)
                                {

#line 2261
                                    if(k2_1 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2261
                                        break;
                                    }

#line 2261
                                    r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2261
                                    float nr_0 = cr_0 * _S38 - ci_0 * _S39;

#line 2261
                                    float _S40 = cr_0 * _S39 + ci_0 * _S38;

#line 2261
                                    k2_1 = k2_1 + 1U;

#line 2261
                                    cr_0 = nr_0;

#line 2261
                                    ci_0 = _S40;

#line 2261
                                }

#line 2261
                                uint per_1 = 16U / max(64U, 1U);

#line 2261
                                uint _S41 = max(4U, 1U);

#line 2261
                                _S24 = _S41;

#line 2261
                                uint blk2_1 = _S28 / _S41;

#line 2261
                                uint lane2_1 = _S28 % _S41;

#line 2261
                                for(;;)
                                {

#line 2261
                                    thread array<float2, int(16)> out_0;

#line 2261
                                    uint z_1 = 0U;

#line 2261
                                    for(;;)
                                    {

#line 2261
                                        if(z_1 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2261
                                            break;
                                        }

#line 2261
                                        out_0[z_1] = float2(0.0f, 0.0f);

#line 2261
                                        z_1 = z_1 + 1U;

#line 2261
                                    }

#line 2261
                                    uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2261
                                    _S25 = spanMask_0;

#line 2261
                                    uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2261
                                    uint p0_0 = computeWant_0(0U, 64U, 1024U, blk_1, lane_1, per_1, _S41, 64U, blk2_1, lane2_1);

#line 2261
                                    uint _S42 = p0_0 & lenMask_0;

#line 2261
                                    uint _S43 = (_S42 >> lgTB_0) * 64U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S42 & spanMask_0);

#line 2261
                                    uint c_2 = 0U;

#line 2261
                                    for(;;)
                                    {

#line 2261
                                        if(c_2 < 1U)
                                        {
                                        }
                                        else
                                        {

#line 2261
                                            break;
                                        }

#line 2261
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2261
                                        j_1 = 0U;

#line 2261
                                        for(;;)
                                        {

#line 2261
                                            if(j_1 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 2261
                                                break;
                                            }

#line 2261
                                            stgPut_0(j_1 * 64U + (&kernelContext_3)->_tid_0, r_3[c_2 * 16U + j_1], &kernelContext_3);

#line 2261
                                            j_1 = j_1 + 1U;

#line 2261
                                        }

#line 2261
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2261
                                        d_3 = 0U;

#line 2261
                                        for(;;)
                                        {

#line 2261
                                            if(d_3 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 2261
                                                break;
                                            }

#line 2261
                                            uint pz_0 = computeWant_0(d_3, 64U, 1024U, 0U, 0U, per_1, _S41, 64U, 0U, 0U);

#line 2261
                                            uint _S44 = pz_0 & lenMask_0;

#line 2261
                                            uint az_0 = (_S44 >> lgTB_0) * 64U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S44 & spanMask_0);

#line 2261
                                            float2 _S45 = stgGet_0(_S43 + az_0 - c_2 * 16U * 64U, &kernelContext_3);

#line 2261
                                            out_0[d_3] = _S45;

#line 2261
                                            d_3 = d_3 + 1U;

#line 2261
                                        }

#line 2261
                                        c_2 = c_2 + 1U;

#line 2261
                                    }

#line 2261
                                    d_3 = 0U;

#line 2261
                                    for(;;)
                                    {

#line 2261
                                        if(d_3 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2261
                                            break;
                                        }

#line 2261
                                        r_3[d_3] = out_0[d_3];

#line 2261
                                        d_3 = d_3 + 1U;

#line 2261
                                    }

#line 2261
                                    break;
                                }

#line 2261
                                break;
                            }

#line 2261
                            break;
                        }

#line 2261
                        for(;;)
                        {

#line 2261
                            for(;;)
                            {

#line 2261
                                uint lgTB_1 = firstbithigh_0(4U);

#line 2261
                                uint blk_2 = _S28 >> lgTB_1;

#line 2261
                                uint lane_2 = _S28 & 3U;

#line 2261
                                dft16_0(&r_3);

#line 2261
                                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 64.0f);

#line 2261
                                float _S46 = tw_1.x;

#line 2261
                                float _S47 = tw_1.y;

#line 2261
                                uint k2_2 = 0U;

#line 2261
                                float cr_1 = 1.0f;

#line 2261
                                float ci_1 = 0.0f;

#line 2261
                                for(;;)
                                {

#line 2261
                                    if(k2_2 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2261
                                        break;
                                    }

#line 2261
                                    r_3[k2_2] = cmul_0(r_3[k2_2], float2(cr_1, ci_1));

#line 2261
                                    float nr_1 = cr_1 * _S46 - ci_1 * _S47;

#line 2261
                                    float _S48 = cr_1 * _S47 + ci_1 * _S46;

#line 2261
                                    k2_2 = k2_2 + 1U;

#line 2261
                                    cr_1 = nr_1;

#line 2261
                                    ci_1 = _S48;

#line 2261
                                }

#line 2261
                                uint per_2 = 16U / _S24;

#line 2261
                                uint _S49 = max(0U, 1U);

#line 2261
                                uint blk2_2 = _S28 / _S49;

#line 2261
                                uint lane2_2 = _S28 % _S49;

#line 2261
                                for(;;)
                                {

#line 2261
                                    thread array<float2, int(16)> out_1;

#line 2261
                                    uint z_2 = 0U;

#line 2261
                                    for(;;)
                                    {

#line 2261
                                        if(z_2 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2261
                                            break;
                                        }

#line 2261
                                        out_1[z_2] = float2(0.0f, 0.0f);

#line 2261
                                        z_2 = z_2 + 1U;

#line 2261
                                    }

#line 2261
                                    uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2261
                                    uint p0_1 = computeWant_0(0U, 4U, 64U, blk_2, lane_2, per_2, _S49, 4U, blk2_2, lane2_2);

#line 2261
                                    uint _S50 = p0_1 & _S25;

#line 2261
                                    uint _S51 = (_S50 >> lgTB_1) * 64U + ((p0_1 >> _S23) << lgTB_1) + (_S50 & spanMask_1);

#line 2261
                                    uint c_3 = 0U;

#line 2261
                                    for(;;)
                                    {

#line 2261
                                        if(c_3 < 1U)
                                        {
                                        }
                                        else
                                        {

#line 2261
                                            break;
                                        }

#line 2261
                                        bool _S52 = c_3 == 0U;

#line 2261
                                        if(!_S52)
                                        {

#line 2261
                                            simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2261
                                        }
                                        else
                                        {

#line 2261
                                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2261
                                        }

#line 2261
                                        j_1 = 0U;

#line 2261
                                        for(;;)
                                        {

#line 2261
                                            if(j_1 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 2261
                                                break;
                                            }

#line 2261
                                            stgPut_0(j_1 * 64U + (&kernelContext_3)->_tid_0, r_3[c_3 * 16U + j_1], &kernelContext_3);

#line 2261
                                            j_1 = j_1 + 1U;

#line 2261
                                        }

#line 2261
                                        simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2261
                                        d_4 = 0U;

#line 2261
                                        for(;;)
                                        {

#line 2261
                                            if(d_4 < 16U)
                                            {
                                            }
                                            else
                                            {

#line 2261
                                                break;
                                            }

#line 2261
                                            uint pz_1 = computeWant_0(d_4, 4U, 64U, 0U, 0U, per_2, _S49, 4U, 0U, 0U);

#line 2261
                                            uint _S53 = pz_1 & _S25;

#line 2261
                                            uint az_1 = (_S53 >> lgTB_1) * 64U + ((pz_1 >> _S23) << lgTB_1) + (_S53 & spanMask_1);

#line 2261
                                            float2 _S54 = stgGet_0(_S51 + az_1 - c_3 * 16U * 64U, &kernelContext_3);

#line 2261
                                            out_1[d_4] = _S54;

#line 2261
                                            d_4 = d_4 + 1U;

#line 2261
                                        }

#line 2261
                                        c_3 = c_3 + 1U;

#line 2261
                                    }

#line 2261
                                    j_1 = 0U;

#line 2261
                                    for(;;)
                                    {

#line 2261
                                        if(j_1 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2261
                                            break;
                                        }

#line 2261
                                        r_3[j_1] = out_1[j_1];

#line 2261
                                        j_1 = j_1 + 1U;

#line 2261
                                    }

#line 2261
                                    break;
                                }

#line 2261
                                break;
                            }

#line 2261
                            break;
                        }

#line 2261
                        break;
                    }

#line 2261
                    innermost_0(&r_3);

#line 2261
                    break;
                }

#line 2261
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2261
                float2 _S55 = float2(0.0f, 0.0f);

#line 2261
                bool _S56;

#line 2261
                if(_S29 == 0U)
                {

#line 2261
                    _S56 = _S30 >= 1024U;

#line 2261
                }
                else
                {

#line 2261
                    _S56 = false;

#line 2261
                }

#line 2261
                uint gateMaxBits_0;

#line 2261
                uint threadBestBits_0;

#line 2261
                uint threadBestSlot_0;

#line 2261
                uint m_1;

#line 2261
                bool live_0;

#line 2261
                float2 threadBestVal_0;

#line 2261
                if(_S56)
                {

#line 2261
                    d_4 = 0U;

#line 2261
                    gateMaxBits_0 = 0U;

#line 2261
                    threadBestBits_0 = _S33;

#line 2261
                    threadBestSlot_0 = 4294967295U;

#line 2261
                    threadBestVal_0 = _S55;

#line 2261
                    for(;;)
                    {

#line 2261
                        if(d_4 < 16U)
                        {
                        }
                        else
                        {

#line 2261
                            break;
                        }

#line 2261
                        float _rx_0 = r_3[d_4].x;

#line 2261
                        float _ry_0 = r_3[d_4].y;

#line 2261
                        uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 2261
                        uint _S57 = max(gateMaxBits_0, magBits_0);

#line 2261
                        if(magBits_0 > threadBestBits_0)
                        {

#line 2261
                            uint _S58 = _S28 * 16U + d_4;

#line 2261
                            float2 _S59 = float2(_rx_0, _ry_0);

#line 2261
                            threadBestBits_0 = magBits_0;

#line 2261
                            threadBestSlot_0 = _S58;

#line 2261
                            threadBestVal_0 = _S59;

#line 2261
                        }

#line 2261
                        d_4 = d_4 + 1U;

#line 2261
                        gateMaxBits_0 = _S57;

#line 2261
                    }

#line 2261
                }
                else
                {

#line 2261
                    d_4 = 0U;

#line 2261
                    gateMaxBits_0 = 0U;

#line 2261
                    threadBestBits_0 = _S33;

#line 2261
                    threadBestSlot_0 = 4294967295U;

#line 2261
                    threadBestVal_0 = _S55;

#line 2261
                    for(;;)
                    {

#line 2261
                        if(d_4 < 16U)
                        {
                        }
                        else
                        {

#line 2261
                            break;
                        }

#line 2261
                        uint _S60 = _S28 * 16U + d_4;

#line 2261
                        uint idx_1 = slotToIndex_0(_S60);

#line 2261
                        if(idx_1 >= _S29)
                        {

#line 2261
                            live_0 = idx_1 < _S30;

#line 2261
                        }
                        else
                        {

#line 2261
                            live_0 = false;

#line 2261
                        }

#line 2261
                        float _rx_1 = r_3[d_4].x;

#line 2261
                        float _ry_1 = r_3[d_4].y;

#line 2261
                        if(live_0)
                        {

#line 2261
                            m_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 2261
                        }
                        else
                        {

#line 2261
                            m_1 = 0U;

#line 2261
                        }

#line 2261
                        uint _S61 = max(gateMaxBits_0, m_1);

#line 2261
                        if(m_1 > threadBestBits_0)
                        {

#line 2261
                            float2 _S62 = float2(_rx_1, _ry_1);

#line 2261
                            threadBestBits_0 = m_1;

#line 2261
                            threadBestSlot_0 = _S60;

#line 2261
                            threadBestVal_0 = _S62;

#line 2261
                        }

#line 2261
                        d_4 = d_4 + 1U;

#line 2261
                        gateMaxBits_0 = _S61;

#line 2261
                    }

#line 2261
                }

#line 2261
                if(gateOnly_0)
                {

#line 2261
                    uint m_2 = simd_max(gateMaxBits_0);

#line 2261
                    bool _S63 = simd_is_first();

#line 2261
                    if(_S63)
                    {

#line 2261
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + _S28 / 32U] = m_2;

#line 2261
                    }

#line 2261
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2261
                    d_4 = 0U;

#line 2261
                    m_1 = 0U;

#line 2261
                    for(;;)
                    {

#line 2261
                        if(d_4 < 2U)
                        {
                        }
                        else
                        {

#line 2261
                            break;
                        }

#line 2261
                        uint _S64 = max(m_1, (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + d_4]);

#line 2261
                        d_4 = d_4 + 1U;

#line 2261
                        m_1 = _S64;

#line 2261
                    }

#line 2261
                    if(_S28 == 0U)
                    {

#line 2261
                        int device* _S65 = (&kernelContext_3)->entryPointParams_peakIdx_0+pair_0;

#line 2261
                        int _S66;

#line 2261
                        if(m_1 > 0U)
                        {

#line 2261
                            _S66 = int(0);

#line 2261
                        }
                        else
                        {

#line 2261
                            _S66 = int(-1);

#line 2261
                        }

#line 2261
                        *_S65 = _S66;

#line 2261
                        *((&kernelContext_3)->entryPointParams_peakVal_0+pair_0) = packed_float2(float2(sqrt((as_type<float>((m_1)))), 0.0f)) ;

#line 2261
                    }

#line 2261
                    break;
                }

#line 2261
                bool _S67 = _S28 == 0U;

#line 2261
                if(_S67)
                {

#line 2261
                    (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0] = _S33;

#line 2261
                    (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U] = 4294967295U;

#line 2261
                }

#line 2261
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2261
                uint wm_0 = simd_max(threadBestBits_0);

#line 2261
                bool _S68 = simd_is_first();

#line 2261
                if(_S68)
                {

#line 2261
                    live_0 = wm_0 > _S33;

#line 2261
                }
                else
                {

#line 2261
                    live_0 = false;

#line 2261
                }

#line 2261
                if(live_0)
                {

#line 2261
                    uint _S69 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), wm_0, memory_order_relaxed);

#line 2261
                }

#line 2261
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2261
                bool _S70;

#line 2261
                if(threadBestBits_0 > _S33)
                {

#line 2261
                    _S70 = threadBestBits_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0];

#line 2261
                }
                else
                {

#line 2261
                    _S70 = false;

#line 2261
                }

#line 2261
                if(_S70)
                {

#line 2261
                    d_4 = threadBestSlot_0;

#line 2261
                }
                else
                {

#line 2261
                    d_4 = 4294967295U;

#line 2261
                }

#line 2261
                uint waveWinner_0 = simd_min(d_4);

#line 2261
                bool _S71 = simd_is_first();

#line 2261
                bool _S72;

#line 2261
                if(_S71)
                {

#line 2261
                    _S72 = waveWinner_0 != 4294967295U;

#line 2261
                }
                else
                {

#line 2261
                    _S72 = false;

#line 2261
                }

#line 2261
                if(_S72)
                {

#line 2261
                    uint _S73 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 2261
                }

#line 2261
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2261
                bool _S74;

#line 2261
                if(threadBestSlot_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])
                {

#line 2261
                    _S74 = threadBestSlot_0 != 4294967295U;

#line 2261
                }
                else
                {

#line 2261
                    _S74 = false;

#line 2261
                }

#line 2261
                if(_S74)
                {

#line 2261
                    *((&kernelContext_3)->entryPointParams_peakIdx_0+pair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 2261
                    *((&kernelContext_3)->entryPointParams_peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 2261
                }

#line 2261
                bool _S75;

#line 2261
                if(_S67)
                {

#line 2261
                    _S75 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U]) == 4294967295U;

#line 2261
                }
                else
                {

#line 2261
                    _S75 = false;

#line 2261
                }

#line 2261
                if(_S75)
                {

#line 2261
                    *((&kernelContext_3)->entryPointParams_peakIdx_0+pair_0) = int(-1);

#line 2261
                    *((&kernelContext_3)->entryPointParams_peakVal_0+pair_0) = packed_float2(_S55) ;

#line 2261
                }

#line 2261
                break;
            }

#line 2261
            break;
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2257
        i_4 = i_4 + (&kernelContext_3)->entryPointParams_0->gridSize_0;

#line 2257
    }

#line 2265
    return;
}
