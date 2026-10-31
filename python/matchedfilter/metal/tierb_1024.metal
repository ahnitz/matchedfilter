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
};


#line 311 "mm_1024_fusedTierB.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_rowWin_0;
    uint _stgBase_0;
    uint _binPhase_0;
    uint _tid_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 227
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 90 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 230 "mm_1024_fusedTierB.slang"
    if(_S3 == 0U)
    {

#line 230
        return;
    }

#line 231
    uint _S4 = 3U * d_0;

#line 231
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


#line 173 "mm_1024_fusedTierB.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 173
    return float2(*(b_0+i_0)) ;
}


#line 323
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 323
    float _S6 = a_0.x;

#line 323
    float _S7 = b_1.x;

#line 323
    float _S8 = a_0.y;

#line 323
    float _S9 = b_1.y;

#line 323
    return float2(_S6 * _S7 + _S8 * _S9, _S8 * _S7 - _S6 * _S9);
}


#line 582
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 584
    float2 t1_0 = *a_1 - *c_0;

#line 584
    float2 t2_0 = *b_2 + *d_1;

#line 584
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 586
    *b_2 = t1_0 + j3_0;

#line 586
    *c_0 = t0_0 - t2_0;

#line 586
    *d_1 = t1_0 - j3_0;
    return;
}


#line 322
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 322
    float _S10 = a_2.x;

#line 322
    float _S11 = b_3.x;

#line 322
    float _S12 = a_2.y;

#line 322
    float _S13 = b_3.y;

#line 322
    return float2(_S10 * _S11 - _S12 * _S13, _S10 * _S13 + _S12 * _S11);
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
        uint _S14 = 4U * k2_0;

#line 630
        r4_0(&(*r_0)[_S14], &(*r_0)[_S14 + 1U], &(*r_0)[_S14 + 2U], &(*r_0)[_S14 + 3U]);

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


#line 324 "mm_1024_fusedTierB.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S18 = max(TB_0, 1U);

#line 326
    uint j_0 = d_2 / _S18;

#line 326
    uint m_0 = d_2 % _S18;

#line 326
    uint _S19;
    if(TB_0 <= 16U)
    {

#line 327
        _S19 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 327
    }
    else
    {

#line 327
        _S19 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 327
    }

#line 327
    return _S19;
}


#line 311
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 311
    uint _S20 = 2U * i_1;

#line 311
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20] = (as_type<uint>((v_0.x)));

#line 311
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20 + 1U] = (as_type<uint>((v_0.y)));

#line 311
    return;
}


#line 312
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_2)
{

#line 312
    uint _S21 = 2U * i_2;

#line 312
    return float2((as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S21]))), (as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S21 + 1U]))));
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
    uint _S22;

#line 868
    if(i_3 < 2U)
    {

#line 868
        _S22 = 4U;

#line 868
    }
    else
    {

#line 868
        _S22 = 1U;

#line 868
    }

#line 868
    return _S22;
}


#line 870
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_1 = slot_0 >> lg_0;

#line 874
    uint lg_1 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_1;

#line 874
    uint lg_2 = lgOf_0(1U);

#line 874
    uint lg_3 = lgOf_0(0U);

#line 879
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | (x_2 & ((1U << lg_2) - 1U))) << lg_3) | ((x_2 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 1765
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1765
    uint k2_1;

#line 1765
    uint _S23;

#line 1765
    float cr_0;

#line 1765
    float ci_0;

#line 1765
    uint _S24;

#line 1765
    uint z_1;

#line 1765
    uint _S25;

#line 1765
    uint c_2;

#line 1765
    uint d_3;

#line 1765
    uint j_1;

#line 1765
    uint b_5;

#line 1765
    uint m0_0;

#line 1765
    uint s0_0;

#line 1765
    uint m1_0;

#line 1765
    thread KernelContext_0 kernelContext_3;

#line 1765
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 1765
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1765
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1765
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1765
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1765
    (&kernelContext_3)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1765
    threadgroup array<uint, int(2048)> stg_1;

#line 1765
    (&kernelContext_3)->stg_0 = &stg_1;

#line 1765
    (&kernelContext_3)->_binPhase_0 = 0U;

#line 1782
    uint _pr_0 = gid_0.x;

#line 1782
    uint _t_0 = lid_0.x;
    (&kernelContext_3)->_stgBase_0 = 0U;

#line 1792
    thread uint _ws_0 = entryPointParams_1->winStart_0;

#line 1792
    thread uint _we_0 = entryPointParams_1->winEnd_0;
    uint _S26 = _pr_0 / entryPointParams_1->ntmpl_0;

#line 1793
    rowWindow_0(_S26, &_ws_0, &_we_0, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);
    uint _S27 = _ws_0;

#line 1794
    uint _S28 = _we_0;

#line 1794
    uint _S29 = entryPointParams_1->ntmpl_0;

#line 1794
    uint _S30 = (&kernelContext_3)->entryPointParams_0->binsize_0;

#line 1794
    int _S31 = (&kernelContext_3)->entryPointParams_0->binShift_0;

#line 1794
    uint _S32 = (&kernelContext_3)->entryPointParams_0->nbins_0;

#line 1794
    uint _S33 = (&kernelContext_3)->entryPointParams_0->thrBits_0;

#line 1794
    for(;;)
    {

#line 1794
        (&kernelContext_3)->_tid_0 = _t_0;

#line 1794
        uint _S34 = _pr_0 / _S29;

#line 1794
        uint _S35 = _pr_0 % _S29;

#line 1794
        thread array<float2, int(16)> r_3;

#line 1794
        uint n2_0 = 0U;

#line 1794
        for(;;)
        {

#line 1794
            if(n2_0 < 16U)
            {
            }
            else
            {

#line 1794
                break;
            }

#line 1794
            uint idx_0 = _t_0 + 64U * n2_0;

#line 1794
            uint _S36 = mfDataStrideFlag_0();

#line 1794
            if(_S36 != 0U)
            {

#line 1794
                uint _S37 = mfDataStrideFlag_0();

#line 1794
                k2_1 = _S37;

#line 1794
            }
            else
            {

#line 1794
                k2_1 = 1024U;

#line 1794
            }

#line 1794
            r_3[n2_0] = cmulConj_0(cload_0((&kernelContext_3)->entryPointParams_data_0, _S34 * k2_1 + idx_0), cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S35 * 1024U + idx_0));

#line 1794
            n2_0 = n2_0 + 1U;

#line 1794
        }

#line 1794
        for(;;)
        {

#line 1794
            for(;;)
            {

#line 1794
                for(;;)
                {

#line 1794
                    for(;;)
                    {

#line 1794
                        uint lgTB_0 = firstbithigh_0(64U);

#line 1794
                        _S23 = lgTB_0;

#line 1794
                        uint lgLn_0 = firstbithigh_0(1024U);

#line 1794
                        uint blk_1 = _t_0 >> lgTB_0;

#line 1794
                        uint lane_1 = _t_0 & 63U;

#line 1794
                        dft16_0(&r_3);

#line 1794
                        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 1024.0f);

#line 1794
                        float _S38 = tw_0.x;

#line 1794
                        float _S39 = tw_0.y;

#line 1794
                        k2_1 = 0U;

#line 1794
                        cr_0 = 1.0f;

#line 1794
                        ci_0 = 0.0f;

#line 1794
                        for(;;)
                        {

#line 1794
                            if(k2_1 < 16U)
                            {
                            }
                            else
                            {

#line 1794
                                break;
                            }

#line 1794
                            r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 1794
                            float nr_0 = cr_0 * _S38 - ci_0 * _S39;

#line 1794
                            float _S40 = cr_0 * _S39 + ci_0 * _S38;

#line 1794
                            k2_1 = k2_1 + 1U;

#line 1794
                            cr_0 = nr_0;

#line 1794
                            ci_0 = _S40;

#line 1794
                        }

#line 1794
                        uint per_1 = 16U / max(64U, 1U);

#line 1794
                        uint _S41 = max(4U, 1U);

#line 1794
                        _S24 = _S41;

#line 1794
                        uint blk2_1 = _t_0 / _S41;

#line 1794
                        uint lane2_1 = _t_0 % _S41;

#line 1794
                        for(;;)
                        {

#line 1794
                            thread array<float2, int(16)> out_0;

#line 1794
                            z_1 = 0U;

#line 1794
                            for(;;)
                            {

#line 1794
                                if(z_1 < 16U)
                                {
                                }
                                else
                                {

#line 1794
                                    break;
                                }

#line 1794
                                out_0[z_1] = float2(0.0f, 0.0f);

#line 1794
                                z_1 = z_1 + 1U;

#line 1794
                            }

#line 1794
                            uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 1794
                            _S25 = spanMask_0;

#line 1794
                            uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1794
                            uint p0_0 = computeWant_0(0U, 64U, 1024U, blk_1, lane_1, per_1, _S41, 64U, blk2_1, lane2_1);

#line 1794
                            uint _S42 = p0_0 & lenMask_0;

#line 1794
                            uint _S43 = (_S42 >> lgTB_0) * 64U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S42 & spanMask_0);

#line 1794
                            c_2 = 0U;

#line 1794
                            for(;;)
                            {

#line 1794
                                if(c_2 < 1U)
                                {
                                }
                                else
                                {

#line 1794
                                    break;
                                }

#line 1794
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
                                j_1 = 0U;

#line 1794
                                for(;;)
                                {

#line 1794
                                    if(j_1 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1794
                                        break;
                                    }

#line 1794
                                    stgPut_0(j_1 * 64U + (&kernelContext_3)->_tid_0, r_3[c_2 * 16U + j_1], &kernelContext_3);

#line 1794
                                    j_1 = j_1 + 1U;

#line 1794
                                }

#line 1794
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
                                d_3 = 0U;

#line 1794
                                for(;;)
                                {

#line 1794
                                    if(d_3 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1794
                                        break;
                                    }

#line 1794
                                    uint pz_0 = computeWant_0(d_3, 64U, 1024U, 0U, 0U, per_1, _S41, 64U, 0U, 0U);

#line 1794
                                    uint _S44 = pz_0 & lenMask_0;

#line 1794
                                    uint az_0 = (_S44 >> lgTB_0) * 64U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S44 & spanMask_0);

#line 1794
                                    float2 _S45 = stgGet_0(_S43 + az_0 - c_2 * 16U * 64U, &kernelContext_3);

#line 1794
                                    out_0[d_3] = _S45;

#line 1794
                                    d_3 = d_3 + 1U;

#line 1794
                                }

#line 1794
                                c_2 = c_2 + 1U;

#line 1794
                            }

#line 1794
                            d_3 = 0U;

#line 1794
                            for(;;)
                            {

#line 1794
                                if(d_3 < 16U)
                                {
                                }
                                else
                                {

#line 1794
                                    break;
                                }

#line 1794
                                r_3[d_3] = out_0[d_3];

#line 1794
                                d_3 = d_3 + 1U;

#line 1794
                            }

#line 1794
                            break;
                        }

#line 1794
                        break;
                    }

#line 1794
                    break;
                }

#line 1794
                for(;;)
                {

#line 1794
                    for(;;)
                    {

#line 1794
                        uint lgTB_1 = firstbithigh_0(4U);

#line 1794
                        uint blk_2 = _t_0 >> lgTB_1;

#line 1794
                        uint lane_2 = _t_0 & 3U;

#line 1794
                        dft16_0(&r_3);

#line 1794
                        float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 64.0f);

#line 1794
                        float _S46 = tw_1.x;

#line 1794
                        float _S47 = tw_1.y;

#line 1794
                        k2_1 = 0U;

#line 1794
                        cr_0 = 1.0f;

#line 1794
                        ci_0 = 0.0f;

#line 1794
                        for(;;)
                        {

#line 1794
                            if(k2_1 < 16U)
                            {
                            }
                            else
                            {

#line 1794
                                break;
                            }

#line 1794
                            r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 1794
                            float nr_1 = cr_0 * _S46 - ci_0 * _S47;

#line 1794
                            float _S48 = cr_0 * _S47 + ci_0 * _S46;

#line 1794
                            k2_1 = k2_1 + 1U;

#line 1794
                            cr_0 = nr_1;

#line 1794
                            ci_0 = _S48;

#line 1794
                        }

#line 1794
                        uint per_2 = 16U / _S24;

#line 1794
                        uint _S49 = max(0U, 1U);

#line 1794
                        uint blk2_2 = _t_0 / _S49;

#line 1794
                        uint lane2_2 = _t_0 % _S49;

#line 1794
                        for(;;)
                        {

#line 1794
                            thread array<float2, int(16)> out_1;

#line 1794
                            z_1 = 0U;

#line 1794
                            for(;;)
                            {

#line 1794
                                if(z_1 < 16U)
                                {
                                }
                                else
                                {

#line 1794
                                    break;
                                }

#line 1794
                                out_1[z_1] = float2(0.0f, 0.0f);

#line 1794
                                z_1 = z_1 + 1U;

#line 1794
                            }

#line 1794
                            uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 1794
                            uint p0_1 = computeWant_0(0U, 4U, 64U, blk_2, lane_2, per_2, _S49, 4U, blk2_2, lane2_2);

#line 1794
                            uint _S50 = p0_1 & _S25;

#line 1794
                            uint _S51 = (_S50 >> lgTB_1) * 64U + ((p0_1 >> _S23) << lgTB_1) + (_S50 & spanMask_1);

#line 1794
                            c_2 = 0U;

#line 1794
                            for(;;)
                            {

#line 1794
                                if(c_2 < 1U)
                                {
                                }
                                else
                                {

#line 1794
                                    break;
                                }

#line 1794
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
                                j_1 = 0U;

#line 1794
                                for(;;)
                                {

#line 1794
                                    if(j_1 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1794
                                        break;
                                    }

#line 1794
                                    stgPut_0(j_1 * 64U + (&kernelContext_3)->_tid_0, r_3[c_2 * 16U + j_1], &kernelContext_3);

#line 1794
                                    j_1 = j_1 + 1U;

#line 1794
                                }

#line 1794
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
                                d_3 = 0U;

#line 1794
                                for(;;)
                                {

#line 1794
                                    if(d_3 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1794
                                        break;
                                    }

#line 1794
                                    uint pz_1 = computeWant_0(d_3, 4U, 64U, 0U, 0U, per_2, _S49, 4U, 0U, 0U);

#line 1794
                                    uint _S52 = pz_1 & _S25;

#line 1794
                                    uint az_1 = (_S52 >> lgTB_1) * 64U + ((pz_1 >> _S23) << lgTB_1) + (_S52 & spanMask_1);

#line 1794
                                    float2 _S53 = stgGet_0(_S51 + az_1 - c_2 * 16U * 64U, &kernelContext_3);

#line 1794
                                    out_1[d_3] = _S53;

#line 1794
                                    d_3 = d_3 + 1U;

#line 1794
                                }

#line 1794
                                c_2 = c_2 + 1U;

#line 1794
                            }

#line 1794
                            d_3 = 0U;

#line 1794
                            for(;;)
                            {

#line 1794
                                if(d_3 < 16U)
                                {
                                }
                                else
                                {

#line 1794
                                    break;
                                }

#line 1794
                                r_3[d_3] = out_1[d_3];

#line 1794
                                d_3 = d_3 + 1U;

#line 1794
                            }

#line 1794
                            break;
                        }

#line 1794
                        break;
                    }

#line 1794
                    break;
                }

#line 1794
                break;
            }

#line 1794
            innermost_0(&r_3);

#line 1794
            break;
        }

#line 1794
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
        uint i_4;

#line 1794
        uint s0_1;

#line 1794
        uint m1_1;

#line 1794
        uint s1_0;

#line 1794
        uint m2_0;

#line 1794
        uint s2_0;

#line 1794
        uint m3_0;

#line 1794
        bool isCand_0;

#line 1794
        if(_S32 <= 4U)
        {

#line 1794
            if(_t_0 < 4U)
            {

#line 1794
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + _t_0] = _S33;

#line 1794
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _t_0] = 4294967295U;

#line 1794
            }

#line 1794
            float2 _S54 = float2(0.0f, 0.0f);

#line 1794
            i_4 = 0U;

#line 1794
            j_1 = _S33;

#line 1794
            s0_1 = 4294967295U;

#line 1794
            float2 v0_0 = _S54;

#line 1794
            m1_1 = _S33;

#line 1794
            s1_0 = 4294967295U;

#line 1794
            float2 v1_0 = _S54;

#line 1794
            m2_0 = _S33;

#line 1794
            s2_0 = 4294967295U;

#line 1794
            float2 v2_0 = _S54;

#line 1794
            m3_0 = _S33;

#line 1794
            uint s3_0 = 4294967295U;

#line 1794
            float2 v3_0 = _S54;

#line 1794
            for(;;)
            {

#line 1794
                if(i_4 < 16U)
                {
                }
                else
                {

#line 1794
                    break;
                }

#line 1794
                uint slot_1 = _t_0 * 16U + i_4;

#line 1794
                uint idx_1 = slotToIndex_0(slot_1);

#line 1794
                if(idx_1 >= _S27)
                {

#line 1794
                    isCand_0 = idx_1 < _S28;

#line 1794
                }
                else
                {

#line 1794
                    isCand_0 = false;

#line 1794
                }

#line 1794
                if(isCand_0)
                {

#line 1794
                    float rx_0 = r_3[i_4].x;

#line 1794
                    float ry_0 = r_3[i_4].y;

#line 1794
                    uint mag_0 = (as_type<uint>((rx_0 * rx_0 + ry_0 * ry_0)));

#line 1794
                    uint off_0 = idx_1 - _S27 + (&kernelContext_3)->_binPhase_0;

#line 1794
                    if(_S32 == 1U)
                    {

#line 1794
                        b_5 = 0U;

#line 1794
                    }
                    else
                    {

#line 1794
                        if(_S31 >= int(0))
                        {

#line 1794
                            n2_0 = off_0 >> uint(_S31);

#line 1794
                        }
                        else
                        {

#line 1794
                            uint _S55 = off_0 / _S30;

#line 1794
                            n2_0 = _S55;

#line 1794
                        }

#line 1794
                        b_5 = n2_0;

#line 1794
                    }

#line 1794
                    bool _S56;

#line 1794
                    if(b_5 == 0U)
                    {

#line 1794
                        _S56 = mag_0 > j_1;

#line 1794
                    }
                    else
                    {

#line 1794
                        _S56 = false;

#line 1794
                    }

#line 1794
                    float2 v0_1;

#line 1794
                    if(_S56)
                    {

#line 1794
                        float2 _S57 = float2(rx_0, ry_0);

#line 1794
                        m0_0 = mag_0;

#line 1794
                        s0_0 = slot_1;

#line 1794
                        v0_1 = _S57;

#line 1794
                    }
                    else
                    {

#line 1794
                        m0_0 = j_1;

#line 1794
                        s0_0 = s0_1;

#line 1794
                        v0_1 = v0_0;

#line 1794
                    }

#line 1794
                    bool _S58;

#line 1794
                    if(_S32 >= 2U)
                    {

#line 1794
                        _S58 = b_5 == 1U;

#line 1794
                    }
                    else
                    {

#line 1794
                        _S58 = false;

#line 1794
                    }

#line 1794
                    bool _S59;

#line 1794
                    if(_S58)
                    {

#line 1794
                        _S59 = mag_0 > m1_1;

#line 1794
                    }
                    else
                    {

#line 1794
                        _S59 = false;

#line 1794
                    }

#line 1794
                    uint s1_1;

#line 1794
                    float2 v1_1;

#line 1794
                    if(_S59)
                    {

#line 1794
                        float2 _S60 = float2(rx_0, ry_0);

#line 1794
                        m1_0 = mag_0;

#line 1794
                        s1_1 = slot_1;

#line 1794
                        v1_1 = _S60;

#line 1794
                    }
                    else
                    {

#line 1794
                        m1_0 = m1_1;

#line 1794
                        s1_1 = s1_0;

#line 1794
                        v1_1 = v1_0;

#line 1794
                    }

#line 1794
                    bool _S61;

#line 1794
                    if(_S32 >= 3U)
                    {

#line 1794
                        _S61 = b_5 == 2U;

#line 1794
                    }
                    else
                    {

#line 1794
                        _S61 = false;

#line 1794
                    }

#line 1794
                    bool _S62;

#line 1794
                    if(_S61)
                    {

#line 1794
                        _S62 = mag_0 > m2_0;

#line 1794
                    }
                    else
                    {

#line 1794
                        _S62 = false;

#line 1794
                    }

#line 1794
                    uint m2_1;

#line 1794
                    uint s2_1;

#line 1794
                    float2 v2_1;

#line 1794
                    if(_S62)
                    {

#line 1794
                        float2 _S63 = float2(rx_0, ry_0);

#line 1794
                        m2_1 = mag_0;

#line 1794
                        s2_1 = slot_1;

#line 1794
                        v2_1 = _S63;

#line 1794
                    }
                    else
                    {

#line 1794
                        m2_1 = m2_0;

#line 1794
                        s2_1 = s2_0;

#line 1794
                        v2_1 = v2_0;

#line 1794
                    }

#line 1794
                    bool _S64;

#line 1794
                    if(_S32 >= 4U)
                    {

#line 1794
                        _S64 = b_5 == 3U;

#line 1794
                    }
                    else
                    {

#line 1794
                        _S64 = false;

#line 1794
                    }

#line 1794
                    bool _S65;

#line 1794
                    if(_S64)
                    {

#line 1794
                        _S65 = mag_0 > m3_0;

#line 1794
                    }
                    else
                    {

#line 1794
                        _S65 = false;

#line 1794
                    }

#line 1794
                    uint m3_1;

#line 1794
                    uint s3_1;

#line 1794
                    float2 v3_1;

#line 1794
                    if(_S65)
                    {

#line 1794
                        float2 _S66 = float2(rx_0, ry_0);

#line 1794
                        m3_1 = mag_0;

#line 1794
                        s3_1 = slot_1;

#line 1794
                        v3_1 = _S66;

#line 1794
                    }
                    else
                    {

#line 1794
                        m3_1 = m3_0;

#line 1794
                        s3_1 = s3_0;

#line 1794
                        v3_1 = v3_0;

#line 1794
                    }

#line 1794
                    j_1 = m0_0;

#line 1794
                    m1_1 = m1_0;

#line 1794
                    m2_0 = m2_1;

#line 1794
                    m3_0 = m3_1;

#line 1794
                    s0_1 = s0_0;

#line 1794
                    s1_0 = s1_1;

#line 1794
                    s2_0 = s2_1;

#line 1794
                    s3_0 = s3_1;

#line 1794
                    v0_0 = v0_1;

#line 1794
                    v1_0 = v1_1;

#line 1794
                    v2_0 = v2_1;

#line 1794
                    v3_0 = v3_1;

#line 1794
                }

#line 1794
                i_4 = i_4 + 1U;

#line 1794
            }

#line 1794
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
            uint wm0_0 = simd_max(j_1);

#line 1794
            bool _S67 = simd_is_first();

#line 1794
            if(_S67)
            {

#line 1794
                isCand_0 = wm0_0 > _S33;

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                uint _S68 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), wm0_0, memory_order_relaxed);

#line 1794
            }

#line 1794
            bool _S69 = _S32 >= 2U;

#line 1794
            if(_S69)
            {

#line 1794
                uint wm1_0 = simd_max(m1_1);

#line 1794
                bool _S70 = simd_is_first();

#line 1794
                if(_S70)
                {

#line 1794
                    isCand_0 = wm1_0 > _S33;

#line 1794
                }
                else
                {

#line 1794
                    isCand_0 = false;

#line 1794
                }

#line 1794
                if(isCand_0)
                {

#line 1794
                    uint _S71 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), wm1_0, memory_order_relaxed);

#line 1794
                }

#line 1794
            }

#line 1794
            bool _S72 = _S32 >= 3U;

#line 1794
            if(_S72)
            {

#line 1794
                uint wm2_0 = simd_max(m2_0);

#line 1794
                bool _S73 = simd_is_first();

#line 1794
                if(_S73)
                {

#line 1794
                    isCand_0 = wm2_0 > _S33;

#line 1794
                }
                else
                {

#line 1794
                    isCand_0 = false;

#line 1794
                }

#line 1794
                if(isCand_0)
                {

#line 1794
                    uint _S74 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U])), wm2_0, memory_order_relaxed);

#line 1794
                }

#line 1794
            }

#line 1794
            bool _S75 = _S32 >= 4U;

#line 1794
            if(_S75)
            {

#line 1794
                uint wm3_0 = simd_max(m3_0);

#line 1794
                bool _S76 = simd_is_first();

#line 1794
                if(_S76)
                {

#line 1794
                    isCand_0 = wm3_0 > _S33;

#line 1794
                }
                else
                {

#line 1794
                    isCand_0 = false;

#line 1794
                }

#line 1794
                if(isCand_0)
                {

#line 1794
                    uint _S77 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U])), wm3_0, memory_order_relaxed);

#line 1794
                }

#line 1794
            }

#line 1794
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
            if(s0_1 != 4294967295U)
            {

#line 1794
                isCand_0 = j_1 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0];

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                b_5 = s0_1;

#line 1794
            }
            else
            {

#line 1794
                b_5 = 4294967295U;

#line 1794
            }

#line 1794
            if(_S69)
            {

#line 1794
                isCand_0 = s1_0 != 4294967295U;

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                isCand_0 = m1_1 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U];

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                m0_0 = s1_0;

#line 1794
            }
            else
            {

#line 1794
                m0_0 = 4294967295U;

#line 1794
            }

#line 1794
            if(_S72)
            {

#line 1794
                isCand_0 = s2_0 != 4294967295U;

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                isCand_0 = m2_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U];

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                s0_0 = s2_0;

#line 1794
            }
            else
            {

#line 1794
                s0_0 = 4294967295U;

#line 1794
            }

#line 1794
            if(_S75)
            {

#line 1794
                isCand_0 = s3_0 != 4294967295U;

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                isCand_0 = m3_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U];

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                m1_0 = s3_0;

#line 1794
            }
            else
            {

#line 1794
                m1_0 = 4294967295U;

#line 1794
            }

#line 1794
            uint ww0_0 = simd_min(b_5);

#line 1794
            bool _S78 = simd_is_first();

#line 1794
            if(_S78)
            {

#line 1794
                isCand_0 = ww0_0 != 4294967295U;

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                uint _S79 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U])), ww0_0, memory_order_relaxed);

#line 1794
            }

#line 1794
            if(_S69)
            {

#line 1794
                uint ww1_0 = simd_min(m0_0);

#line 1794
                bool _S80 = simd_is_first();

#line 1794
                if(_S80)
                {

#line 1794
                    isCand_0 = ww1_0 != 4294967295U;

#line 1794
                }
                else
                {

#line 1794
                    isCand_0 = false;

#line 1794
                }

#line 1794
                if(isCand_0)
                {

#line 1794
                    uint _S81 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U])), ww1_0, memory_order_relaxed);

#line 1794
                }

#line 1794
            }

#line 1794
            if(_S72)
            {

#line 1794
                uint ww2_0 = simd_min(s0_0);

#line 1794
                bool _S82 = simd_is_first();

#line 1794
                if(_S82)
                {

#line 1794
                    isCand_0 = ww2_0 != 4294967295U;

#line 1794
                }
                else
                {

#line 1794
                    isCand_0 = false;

#line 1794
                }

#line 1794
                if(isCand_0)
                {

#line 1794
                    uint _S83 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U])), ww2_0, memory_order_relaxed);

#line 1794
                }

#line 1794
            }

#line 1794
            if(_S75)
            {

#line 1794
                uint ww3_0 = simd_min(m1_0);

#line 1794
                bool _S84 = simd_is_first();

#line 1794
                if(_S84)
                {

#line 1794
                    isCand_0 = ww3_0 != 4294967295U;

#line 1794
                }
                else
                {

#line 1794
                    isCand_0 = false;

#line 1794
                }

#line 1794
                if(isCand_0)
                {

#line 1794
                    uint _S85 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U])), ww3_0, memory_order_relaxed);

#line 1794
                }

#line 1794
            }

#line 1794
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
            uint baseOut_0 = _pr_0 * _S32;

#line 1794
            if(b_5 != 4294967295U)
            {

#line 1794
                isCand_0 = b_5 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U];

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                *((&kernelContext_3)->entryPointParams_peakIdx_0+baseOut_0) = int(slotToIndex_0(b_5));

#line 1794
                *((&kernelContext_3)->entryPointParams_peakVal_0+baseOut_0) = packed_float2(v0_0) ;

#line 1794
            }

#line 1794
            if(_S69)
            {

#line 1794
                isCand_0 = m0_0 != 4294967295U;

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                isCand_0 = m0_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U];

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                uint _S86 = baseOut_0 + 1U;

#line 1794
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S86) = int(slotToIndex_0(m0_0));

#line 1794
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S86) = packed_float2(v1_0) ;

#line 1794
            }

#line 1794
            if(_S72)
            {

#line 1794
                isCand_0 = s0_0 != 4294967295U;

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                isCand_0 = s0_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U];

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                uint _S87 = baseOut_0 + 2U;

#line 1794
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S87) = int(slotToIndex_0(s0_0));

#line 1794
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S87) = packed_float2(v2_0) ;

#line 1794
            }

#line 1794
            if(_S75)
            {

#line 1794
                isCand_0 = m1_0 != 4294967295U;

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                isCand_0 = m1_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U];

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                uint _S88 = baseOut_0 + 3U;

#line 1794
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S88) = int(slotToIndex_0(m1_0));

#line 1794
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S88) = packed_float2(v3_0) ;

#line 1794
            }

#line 1794
            if(_t_0 < _S32)
            {

#line 1794
                isCand_0 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _t_0]) == 4294967295U;

#line 1794
            }
            else
            {

#line 1794
                isCand_0 = false;

#line 1794
            }

#line 1794
            if(isCand_0)
            {

#line 1794
                uint _S89 = baseOut_0 + _t_0;

#line 1794
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S89) = int(-1);

#line 1794
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S89) = packed_float2(_S54) ;

#line 1794
            }

#line 1794
        }
        else
        {

#line 1794
            j_1 = _t_0;

#line 1794
            for(;;)
            {

#line 1794
                if(j_1 < _S32)
                {
                }
                else
                {

#line 1794
                    break;
                }

#line 1794
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_1] = _S33;

#line 1794
                j_1 = j_1 + 64U;

#line 1794
            }

#line 1794
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
            i_4 = 0U;

#line 1794
            s0_1 = 0U;

#line 1794
            m1_1 = 0U;

#line 1794
            for(;;)
            {

#line 1794
                if(i_4 < 16U)
                {
                }
                else
                {

#line 1794
                    break;
                }

#line 1794
                uint idx_2 = slotToIndex_0(_t_0 * 16U + i_4);

#line 1794
                if(idx_2 >= _S27)
                {

#line 1794
                    isCand_0 = idx_2 < _S28;

#line 1794
                }
                else
                {

#line 1794
                    isCand_0 = false;

#line 1794
                }

#line 1794
                if(isCand_0)
                {

#line 1794
                    float rx_1 = r_3[i_4].x;

#line 1794
                    float ry_1 = r_3[i_4].y;

#line 1794
                    uint mag_1 = (as_type<uint>((rx_1 * rx_1 + ry_1 * ry_1)));

#line 1794
                    if(mag_1 > _S33)
                    {

#line 1794
                        uint off_1 = idx_2 - _S27 + (&kernelContext_3)->_binPhase_0;

#line 1794
                        if(_S31 >= int(0))
                        {

#line 1794
                            j_1 = off_1 >> uint(_S31);

#line 1794
                        }
                        else
                        {

#line 1794
                            uint _S90 = off_1 / _S30;

#line 1794
                            j_1 = _S90;

#line 1794
                        }

#line 1794
                        uint _S91 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_1])), mag_1, memory_order_relaxed);

#line 1794
                        uint bit_0 = 1U << (i_4 & 31U);

#line 1794
                        if(i_4 < 32U)
                        {

#line 1794
                            s1_0 = s0_1 | bit_0;

#line 1794
                            m2_0 = m1_1;

#line 1794
                        }
                        else
                        {

#line 1794
                            uint aboveHi_0 = m1_1 | bit_0;

#line 1794
                            s1_0 = s0_1;

#line 1794
                            m2_0 = aboveHi_0;

#line 1794
                        }

#line 1794
                    }
                    else
                    {

#line 1794
                        s1_0 = s0_1;

#line 1794
                        m2_0 = m1_1;

#line 1794
                    }

#line 1794
                }
                else
                {

#line 1794
                    s1_0 = s0_1;

#line 1794
                    m2_0 = m1_1;

#line 1794
                }

#line 1794
                i_4 = i_4 + 1U;

#line 1794
                s0_1 = s1_0;

#line 1794
                m1_1 = m2_0;

#line 1794
            }

#line 1794
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
            if((s0_1 | m1_1) != 0U)
            {

#line 1794
                i_4 = 0U;

#line 1794
                s1_0 = 0U;

#line 1794
                m2_0 = 0U;

#line 1794
                for(;;)
                {

#line 1794
                    if(i_4 < 16U)
                    {
                    }
                    else
                    {

#line 1794
                        break;
                    }

#line 1794
                    uint bit_1 = 1U << (i_4 & 31U);

#line 1794
                    bool _S92 = i_4 < 32U;

#line 1794
                    if(_S92)
                    {

#line 1794
                        isCand_0 = (s0_1 & bit_1) != 0U;

#line 1794
                    }
                    else
                    {

#line 1794
                        isCand_0 = (m1_1 & bit_1) != 0U;

#line 1794
                    }

#line 1794
                    if(isCand_0)
                    {

#line 1794
                        uint off_2 = slotToIndex_0(_t_0 * 16U + i_4) - _S27 + (&kernelContext_3)->_binPhase_0;

#line 1794
                        if(_S31 >= int(0))
                        {

#line 1794
                            j_1 = off_2 >> uint(_S31);

#line 1794
                        }
                        else
                        {

#line 1794
                            uint _S93 = off_2 / _S30;

#line 1794
                            j_1 = _S93;

#line 1794
                        }

#line 1794
                        float rx_2 = r_3[i_4].x;

#line 1794
                        float ry_2 = r_3[i_4].y;

#line 1794
                        if((as_type<uint>((rx_2 * rx_2 + ry_2 * ry_2))) == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_1])
                        {

#line 1794
                            if(_S92)
                            {

#line 1794
                                s2_0 = s1_0 | bit_1;

#line 1794
                                m3_0 = m2_0;

#line 1794
                            }
                            else
                            {

#line 1794
                                uint candHi_0 = m2_0 | bit_1;

#line 1794
                                s2_0 = s1_0;

#line 1794
                                m3_0 = candHi_0;

#line 1794
                            }

#line 1794
                        }
                        else
                        {

#line 1794
                            s2_0 = s1_0;

#line 1794
                            m3_0 = m2_0;

#line 1794
                        }

#line 1794
                    }
                    else
                    {

#line 1794
                        s2_0 = s1_0;

#line 1794
                        m3_0 = m2_0;

#line 1794
                    }

#line 1794
                    i_4 = i_4 + 1U;

#line 1794
                    s1_0 = s2_0;

#line 1794
                    m2_0 = m3_0;

#line 1794
                }

#line 1794
                s2_0 = s1_0;

#line 1794
                m3_0 = m2_0;

#line 1794
            }
            else
            {

#line 1794
                s2_0 = 0U;

#line 1794
                m3_0 = 0U;

#line 1794
            }

#line 1794
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
            j_1 = _t_0;

#line 1794
            for(;;)
            {

#line 1794
                if(j_1 < _S32)
                {
                }
                else
                {

#line 1794
                    break;
                }

#line 1794
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_1] = 4294967295U;

#line 1794
                j_1 = j_1 + 64U;

#line 1794
            }

#line 1794
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
            bool _S94 = (s2_0 | m3_0) != 0U;

#line 1794
            if(_S94)
            {

#line 1794
                i_4 = 0U;

#line 1794
                for(;;)
                {

#line 1794
                    if(i_4 < 16U)
                    {
                    }
                    else
                    {

#line 1794
                        break;
                    }

#line 1794
                    uint bit_2 = 1U << (i_4 & 31U);

#line 1794
                    if(i_4 < 32U)
                    {

#line 1794
                        isCand_0 = (s2_0 & bit_2) != 0U;

#line 1794
                    }
                    else
                    {

#line 1794
                        isCand_0 = (m3_0 & bit_2) != 0U;

#line 1794
                    }

#line 1794
                    if(isCand_0)
                    {

#line 1794
                        uint _S95 = _t_0 * 16U + i_4;

#line 1794
                        uint off_3 = slotToIndex_0(_S95) - _S27 + (&kernelContext_3)->_binPhase_0;

#line 1794
                        if(_S31 >= int(0))
                        {

#line 1794
                            j_1 = off_3 >> uint(_S31);

#line 1794
                        }
                        else
                        {

#line 1794
                            uint _S96 = off_3 / _S30;

#line 1794
                            j_1 = _S96;

#line 1794
                        }

#line 1794
                        uint _S97 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_1])), _S95, memory_order_relaxed);

#line 1794
                    }

#line 1794
                    i_4 = i_4 + 1U;

#line 1794
                }

#line 1794
            }

#line 1794
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
            if(_S94)
            {

#line 1794
                i_4 = 0U;

#line 1794
                for(;;)
                {

#line 1794
                    if(i_4 < 16U)
                    {
                    }
                    else
                    {

#line 1794
                        break;
                    }

#line 1794
                    uint bit_3 = 1U << (i_4 & 31U);

#line 1794
                    if(i_4 < 32U)
                    {

#line 1794
                        isCand_0 = (s2_0 & bit_3) != 0U;

#line 1794
                    }
                    else
                    {

#line 1794
                        isCand_0 = (m3_0 & bit_3) != 0U;

#line 1794
                    }

#line 1794
                    if(isCand_0)
                    {

#line 1794
                        uint _S98 = _t_0 * 16U + i_4;

#line 1794
                        uint idx_3 = slotToIndex_0(_S98);

#line 1794
                        uint off_4 = idx_3 - _S27 + (&kernelContext_3)->_binPhase_0;

#line 1794
                        if(_S31 >= int(0))
                        {

#line 1794
                            j_1 = off_4 >> uint(_S31);

#line 1794
                        }
                        else
                        {

#line 1794
                            uint _S99 = off_4 / _S30;

#line 1794
                            j_1 = _S99;

#line 1794
                        }

#line 1794
                        if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_1]) == _S98)
                        {

#line 1794
                            uint o_1 = _pr_0 * _S32 + j_1;

#line 1794
                            *((&kernelContext_3)->entryPointParams_peakIdx_0+o_1) = int(idx_3);

#line 1794
                            *((&kernelContext_3)->entryPointParams_peakVal_0+o_1) = packed_float2(float2(r_3[i_4].x, r_3[i_4].y)) ;

#line 1794
                        }

#line 1794
                    }

#line 1794
                    i_4 = i_4 + 1U;

#line 1794
                }

#line 1794
            }

#line 1794
            j_1 = _t_0;

#line 1794
            for(;;)
            {

#line 1794
                if(j_1 < _S32)
                {
                }
                else
                {

#line 1794
                    break;
                }

#line 1794
                if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_1]) == 4294967295U)
                {

#line 1794
                    uint _S100 = _pr_0 * _S32 + j_1;

#line 1794
                    *((&kernelContext_3)->entryPointParams_peakIdx_0+_S100) = int(-1);

#line 1794
                    *((&kernelContext_3)->entryPointParams_peakVal_0+_S100) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1794
                }

#line 1794
                j_1 = j_1 + 64U;

#line 1794
            }

#line 1794
        }

#line 1794
        break;
    }

#line 1800
    return;
}
