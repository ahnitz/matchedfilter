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


#line 311 "mm_2048_fusedTierB_onebin.slang"
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
    array<uint, int(4096)> threadgroup* stg_0;
};


#line 227
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 90 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 230 "mm_2048_fusedTierB_onebin.slang"
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


#line 173 "mm_2048_fusedTierB_onebin.slang"
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


#line 324 "mm_2048_fusedTierB_onebin.slang"
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


#line 602
void dft8_0(array<float2, int(16)> thread* r_1, uint o_0)
{


    thread array<float2, int(8)> b_4;

#line 606
    uint s_1 = 1U;
    for(;;)
    {

#line 607
        if(s_1 < 8U)
        {
        }
        else
        {

#line 607
            break;
        }

#line 607
        uint j_1 = 0U;
        for(;;)
        {

#line 608
            if(j_1 < 4U)
            {
            }
            else
            {

#line 608
                break;
            }

#line 609
            uint k_0 = j_1 & (s_1 - 1U);

#line 609
            uint base_0 = (j_1 - k_0) << 1U;

            float2 w_0 = mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_1));
            uint _S22 = o_0 + j_1;

#line 612
            float2 t_6 = cmul_0(w_0, (*r_1)[_S22 + 4U]);
            uint _S23 = base_0 + k_0;

#line 613
            b_4[_S23] = (*r_1)[_S22] + t_6;

#line 613
            b_4[_S23 + s_1] = (*r_1)[_S22] - t_6;

#line 608
            j_1 = j_1 + 1U;

#line 608
        }

#line 608
        uint i_3 = 0U;

#line 615
        for(;;)
        {

#line 615
            if(i_3 < 8U)
            {
            }
            else
            {

#line 615
                break;
            }

#line 615
            (*r_1)[o_0 + i_3] = b_4[i_3];

#line 615
            i_3 = i_3 + 1U;

#line 615
        }

#line 607
        s_1 = s_1 << 1U;

#line 607
    }

#line 617
    return;
}


#line 721
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 721
    uint b_5 = 0U;

#line 729
    for(;;)
    {

#line 729
        if(b_5 < 2U)
        {
        }
        else
        {

#line 729
            break;
        }

#line 729
        dft8_0(r_2, b_5 * 8U);

#line 729
        b_5 = b_5 + 1U;

#line 729
    }



    return;
}


#line 868
uint lgOf_0(uint i_4)
{

#line 868
    uint _S24;

#line 868
    if(i_4 < 2U)
    {

#line 868
        _S24 = 4U;

#line 868
    }
    else
    {

#line 868
        if(i_4 == 2U)
        {

#line 868
            _S24 = 3U;

#line 868
        }
        else
        {

#line 868
            _S24 = 1U;

#line 868
        }

#line 868
    }

#line 868
    return _S24;
}


#line 870
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 874
    uint lg_1 = lgOf_0(1U);

#line 874
    uint lg_2 = lgOf_0(0U);

#line 879
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1765
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1765
    uint k2_1;

#line 1765
    uint _S25;

#line 1765
    float cr_0;

#line 1765
    float ci_0;

#line 1765
    uint _S26;

#line 1765
    uint z_1;

#line 1765
    uint _S27;

#line 1765
    uint c_2;

#line 1765
    uint d_3;

#line 1765
    uint j_2;

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
    threadgroup array<uint, int(4096)> stg_1;

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
    uint _S28 = _pr_0 / entryPointParams_1->ntmpl_0;

#line 1793
    rowWindow_0(_S28, &_ws_0, &_we_0, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);
    uint _S29 = _ws_0;

#line 1794
    uint _S30 = _we_0;

#line 1794
    uint _S31 = entryPointParams_1->ntmpl_0;

#line 1794
    uint _S32 = (&kernelContext_3)->entryPointParams_0->thrBits_0;

#line 1794
    for(;;)
    {

#line 1794
        (&kernelContext_3)->_tid_0 = _t_0;

#line 1794
        uint _S33 = _pr_0 / _S31;

#line 1794
        uint _S34 = _pr_0 % _S31;

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
            uint idx_0 = _t_0 + 128U * n2_0;

#line 1794
            uint _S35 = mfDataStrideFlag_0();

#line 1794
            if(_S35 != 0U)
            {

#line 1794
                uint _S36 = mfDataStrideFlag_0();

#line 1794
                k2_1 = _S36;

#line 1794
            }
            else
            {

#line 1794
                k2_1 = 2048U;

#line 1794
            }

#line 1794
            r_3[n2_0] = cmulConj_0(cload_0((&kernelContext_3)->entryPointParams_data_0, _S33 * k2_1 + idx_0), cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S34 * 2048U + idx_0));

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
                        uint lgTB_0 = firstbithigh_0(128U);

#line 1794
                        _S25 = lgTB_0;

#line 1794
                        uint lgLn_0 = firstbithigh_0(2048U);

#line 1794
                        uint blk_1 = _t_0 >> lgTB_0;

#line 1794
                        uint lane_1 = _t_0 & 127U;

#line 1794
                        dft16_0(&r_3);

#line 1794
                        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 2048.0f);

#line 1794
                        float _S37 = tw_0.x;

#line 1794
                        float _S38 = tw_0.y;

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
                            float nr_0 = cr_0 * _S37 - ci_0 * _S38;

#line 1794
                            float _S39 = cr_0 * _S38 + ci_0 * _S37;

#line 1794
                            k2_1 = k2_1 + 1U;

#line 1794
                            cr_0 = nr_0;

#line 1794
                            ci_0 = _S39;

#line 1794
                        }

#line 1794
                        uint per_1 = 16U / max(128U, 1U);

#line 1794
                        uint _S40 = max(8U, 1U);

#line 1794
                        _S26 = _S40;

#line 1794
                        uint blk2_1 = _t_0 / _S40;

#line 1794
                        uint lane2_1 = _t_0 % _S40;

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
                            _S27 = spanMask_0;

#line 1794
                            uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1794
                            uint p0_0 = computeWant_0(0U, 128U, 2048U, blk_1, lane_1, per_1, _S40, 128U, blk2_1, lane2_1);

#line 1794
                            uint _S41 = p0_0 & lenMask_0;

#line 1794
                            uint _S42 = (_S41 >> lgTB_0) * 128U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S41 & spanMask_0);

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
                                j_2 = 0U;

#line 1794
                                for(;;)
                                {

#line 1794
                                    if(j_2 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1794
                                        break;
                                    }

#line 1794
                                    stgPut_0(j_2 * 128U + (&kernelContext_3)->_tid_0, r_3[c_2 * 16U + j_2], &kernelContext_3);

#line 1794
                                    j_2 = j_2 + 1U;

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
                                    uint pz_0 = computeWant_0(d_3, 128U, 2048U, 0U, 0U, per_1, _S40, 128U, 0U, 0U);

#line 1794
                                    uint _S43 = pz_0 & lenMask_0;

#line 1794
                                    uint az_0 = (_S43 >> lgTB_0) * 128U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S43 & spanMask_0);

#line 1794
                                    float2 _S44 = stgGet_0(_S42 + az_0 - c_2 * 16U * 128U, &kernelContext_3);

#line 1794
                                    out_0[d_3] = _S44;

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
                        uint lgTB_1 = firstbithigh_0(8U);

#line 1794
                        uint blk_2 = _t_0 >> lgTB_1;

#line 1794
                        uint lane_2 = _t_0 & 7U;

#line 1794
                        dft16_0(&r_3);

#line 1794
                        float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 128.0f);

#line 1794
                        float _S45 = tw_1.x;

#line 1794
                        float _S46 = tw_1.y;

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
                            float nr_1 = cr_0 * _S45 - ci_0 * _S46;

#line 1794
                            float _S47 = cr_0 * _S46 + ci_0 * _S45;

#line 1794
                            k2_1 = k2_1 + 1U;

#line 1794
                            cr_0 = nr_1;

#line 1794
                            ci_0 = _S47;

#line 1794
                        }

#line 1794
                        uint per_2 = 16U / _S26;

#line 1794
                        uint _S48 = max(0U, 1U);

#line 1794
                        uint blk2_2 = _t_0 / _S48;

#line 1794
                        uint lane2_2 = _t_0 % _S48;

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
                            uint p0_1 = computeWant_0(0U, 8U, 128U, blk_2, lane_2, per_2, _S48, 8U, blk2_2, lane2_2);

#line 1794
                            uint _S49 = p0_1 & _S27;

#line 1794
                            uint _S50 = (_S49 >> lgTB_1) * 128U + ((p0_1 >> _S25) << lgTB_1) + (_S49 & spanMask_1);

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
                                j_2 = 0U;

#line 1794
                                for(;;)
                                {

#line 1794
                                    if(j_2 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1794
                                        break;
                                    }

#line 1794
                                    stgPut_0(j_2 * 128U + (&kernelContext_3)->_tid_0, r_3[c_2 * 16U + j_2], &kernelContext_3);

#line 1794
                                    j_2 = j_2 + 1U;

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
                                    uint pz_1 = computeWant_0(d_3, 8U, 128U, 0U, 0U, per_2, _S48, 8U, 0U, 0U);

#line 1794
                                    uint _S51 = pz_1 & _S27;

#line 1794
                                    uint az_1 = (_S51 >> lgTB_1) * 128U + ((pz_1 >> _S25) << lgTB_1) + (_S51 & spanMask_1);

#line 1794
                                    float2 _S52 = stgGet_0(_S50 + az_1 - c_2 * 16U * 128U, &kernelContext_3);

#line 1794
                                    out_1[d_3] = _S52;

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
        float2 _S53 = float2(0.0f, 0.0f);

#line 1794
        bool live_0;

#line 1794
        if(_S29 == 0U)
        {

#line 1794
            live_0 = _S30 >= 2048U;

#line 1794
        }
        else
        {

#line 1794
            live_0 = false;

#line 1794
        }

#line 1794
        uint threadBestBits_0;

#line 1794
        uint threadBestSlot_0;

#line 1794
        float2 threadBestVal_0;

#line 1794
        if(live_0)
        {

#line 1794
            j_2 = 0U;

#line 1794
            threadBestBits_0 = _S32;

#line 1794
            threadBestSlot_0 = 4294967295U;

#line 1794
            threadBestVal_0 = _S53;

#line 1794
            for(;;)
            {

#line 1794
                if(j_2 < 16U)
                {
                }
                else
                {

#line 1794
                    break;
                }

#line 1794
                float _rx_0 = r_3[j_2].x;

#line 1794
                float _ry_0 = r_3[j_2].y;

#line 1794
                uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1794
                if(magBits_0 > threadBestBits_0)
                {

#line 1794
                    uint _S54 = _t_0 * 16U + j_2;

#line 1794
                    float2 _S55 = float2(_rx_0, _ry_0);

#line 1794
                    threadBestBits_0 = magBits_0;

#line 1794
                    threadBestSlot_0 = _S54;

#line 1794
                    threadBestVal_0 = _S55;

#line 1794
                }

#line 1794
                j_2 = j_2 + 1U;

#line 1794
            }

#line 1794
        }
        else
        {

#line 1794
            j_2 = 0U;

#line 1794
            threadBestBits_0 = _S32;

#line 1794
            threadBestSlot_0 = 4294967295U;

#line 1794
            threadBestVal_0 = _S53;

#line 1794
            for(;;)
            {

#line 1794
                if(j_2 < 16U)
                {
                }
                else
                {

#line 1794
                    break;
                }

#line 1794
                uint _S56 = _t_0 * 16U + j_2;

#line 1794
                uint idx_1 = slotToIndex_0(_S56);

#line 1794
                if(idx_1 >= _S29)
                {

#line 1794
                    live_0 = idx_1 < _S30;

#line 1794
                }
                else
                {

#line 1794
                    live_0 = false;

#line 1794
                }

#line 1794
                float _rx_1 = r_3[j_2].x;

#line 1794
                float _ry_1 = r_3[j_2].y;

#line 1794
                uint magBits_1;

#line 1794
                if(live_0)
                {

#line 1794
                    magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 1794
                }
                else
                {

#line 1794
                    magBits_1 = 0U;

#line 1794
                }

#line 1794
                if(magBits_1 > threadBestBits_0)
                {

#line 1794
                    float2 _S57 = float2(_rx_1, _ry_1);

#line 1794
                    threadBestBits_0 = magBits_1;

#line 1794
                    threadBestSlot_0 = _S56;

#line 1794
                    threadBestVal_0 = _S57;

#line 1794
                }

#line 1794
                j_2 = j_2 + 1U;

#line 1794
            }

#line 1794
        }

#line 1794
        bool _S58 = _t_0 == 0U;

#line 1794
        if(_S58)
        {

#line 1794
            (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0] = _S32;

#line 1794
            (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U] = 4294967295U;

#line 1794
        }

#line 1794
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
        uint wm_0 = simd_max(threadBestBits_0);

#line 1794
        bool _S59 = simd_is_first();

#line 1794
        if(_S59)
        {

#line 1794
            live_0 = wm_0 > _S32;

#line 1794
        }
        else
        {

#line 1794
            live_0 = false;

#line 1794
        }

#line 1794
        if(live_0)
        {

#line 1794
            uint _S60 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1794
        }

#line 1794
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
        if(threadBestBits_0 > _S32)
        {

#line 1794
            live_0 = threadBestBits_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0];

#line 1794
        }
        else
        {

#line 1794
            live_0 = false;

#line 1794
        }

#line 1794
        if(live_0)
        {

#line 1794
            j_2 = threadBestSlot_0;

#line 1794
        }
        else
        {

#line 1794
            j_2 = 4294967295U;

#line 1794
        }

#line 1794
        uint waveWinner_0 = simd_min(j_2);

#line 1794
        bool _S61 = simd_is_first();

#line 1794
        if(_S61)
        {

#line 1794
            live_0 = waveWinner_0 != 4294967295U;

#line 1794
        }
        else
        {

#line 1794
            live_0 = false;

#line 1794
        }

#line 1794
        if(live_0)
        {

#line 1794
            uint _S62 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1794
        }

#line 1794
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
        if(threadBestSlot_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])
        {

#line 1794
            live_0 = threadBestSlot_0 != 4294967295U;

#line 1794
        }
        else
        {

#line 1794
            live_0 = false;

#line 1794
        }

#line 1794
        if(live_0)
        {

#line 1794
            *((&kernelContext_3)->entryPointParams_peakIdx_0+_pr_0) = int(slotToIndex_0(threadBestSlot_0));

#line 1794
            *((&kernelContext_3)->entryPointParams_peakVal_0+_pr_0) = packed_float2(threadBestVal_0) ;

#line 1794
        }

#line 1794
        if(_S58)
        {

#line 1794
            live_0 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U]) == 4294967295U;

#line 1794
        }
        else
        {

#line 1794
            live_0 = false;

#line 1794
        }

#line 1794
        if(live_0)
        {

#line 1794
            *((&kernelContext_3)->entryPointParams_peakIdx_0+_pr_0) = int(-1);

#line 1794
            *((&kernelContext_3)->entryPointParams_peakVal_0+_pr_0) = packed_float2(_S53) ;

#line 1794
        }

#line 1794
        break;
    }

#line 1800
    return;
}
