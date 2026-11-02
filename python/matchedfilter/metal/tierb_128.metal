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
};


#line 317 "mm_128_fusedTierB.slang"
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
    array<uint, int(256)> threadgroup* stg_0;
};


#line 227
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 92 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 230 "mm_128_fusedTierB.slang"
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


#line 60 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S5 = ((MF_DATA_STRIDE));

#line 63
    return _S5;
}


#line 173 "mm_128_fusedTierB.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 173
    return float2(*(b_0+i_0)) ;
}


#line 329
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 329
    float _S6 = a_0.x;

#line 329
    float _S7 = b_1.x;

#line 329
    float _S8 = a_0.y;

#line 329
    float _S9 = b_1.y;

#line 329
    return float2(_S6 * _S7 + _S8 * _S9, _S8 * _S7 - _S6 * _S9);
}


#line 613
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 615
    float2 t1_0 = *a_1 - *c_0;

#line 615
    float2 t2_0 = *b_2 + *d_1;

#line 615
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 617
    *b_2 = t1_0 + j3_0;

#line 617
    *c_0 = t0_0 - t2_0;

#line 617
    *d_1 = t1_0 - j3_0;
    return;
}


#line 328
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 328
    float _S10 = a_2.x;

#line 328
    float _S11 = b_3.x;

#line 328
    float _S12 = a_2.y;

#line 328
    float _S13 = b_3.y;

#line 328
    return float2(_S10 * _S11 - _S12 * _S13, _S10 * _S13 + _S12 * _S11);
}


#line 649
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 656
    uint n1_0 = 0U;
    for(;;)
    {

#line 657
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 657
            break;
        }

#line 657
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 657
        n1_0 = n1_0 + 1U;

#line 657
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 658
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 658
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 659
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 659
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 660
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 660
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 660
    uint k2_0 = 0U;
    for(;;)
    {

#line 661
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 661
            break;
        }

#line 661
        uint _S14 = 4U * k2_0;

#line 661
        r4_0(&(*r_0)[_S14], &(*r_0)[_S14 + 1U], &(*r_0)[_S14 + 2U], &(*r_0)[_S14 + 3U]);

#line 661
        k2_0 = k2_0 + 1U;

#line 661
    }

    float2 t_0 = (*r_0)[int(1)];

#line 663
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 663
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 664
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 664
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 665
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 665
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 666
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 666
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 667
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 667
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 668
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 668
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


#line 330 "mm_128_fusedTierB.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S18 = max(TB_0, 1U);

#line 332
    uint j_0 = d_2 / _S18;

#line 332
    uint m_0 = d_2 % _S18;

#line 332
    uint _S19;
    if(TB_0 <= 16U)
    {

#line 333
        _S19 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 333
    }
    else
    {

#line 333
        _S19 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 333
    }

#line 333
    return _S19;
}


#line 317
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 317
    uint _S20 = 2U * i_1;

#line 317
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20] = (as_type<uint>((v_0.x)));

#line 317
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20 + 1U] = (as_type<uint>((v_0.y)));

#line 317
    return;
}


#line 318
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_2)
{

#line 318
    uint _S21 = 2U * i_2;

#line 318
    return float2((as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S21]))), (as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S21 + 1U]))));
}


#line 633
void dft8_0(array<float2, int(16)> thread* r_1, uint o_0)
{


    thread array<float2, int(8)> b_4;

#line 637
    uint s_1 = 1U;
    for(;;)
    {

#line 638
        if(s_1 < 8U)
        {
        }
        else
        {

#line 638
            break;
        }

#line 638
        uint j_1 = 0U;
        for(;;)
        {

#line 639
            if(j_1 < 4U)
            {
            }
            else
            {

#line 639
                break;
            }

#line 640
            uint k_0 = j_1 & (s_1 - 1U);

#line 640
            uint base_0 = (j_1 - k_0) << 1U;

            float2 w_0 = mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_1));
            uint _S22 = o_0 + j_1;

#line 643
            float2 t_6 = cmul_0(w_0, (*r_1)[_S22 + 4U]);
            uint _S23 = base_0 + k_0;

#line 644
            b_4[_S23] = (*r_1)[_S22] + t_6;

#line 644
            b_4[_S23 + s_1] = (*r_1)[_S22] - t_6;

#line 639
            j_1 = j_1 + 1U;

#line 639
        }

#line 639
        uint i_3 = 0U;

#line 646
        for(;;)
        {

#line 646
            if(i_3 < 8U)
            {
            }
            else
            {

#line 646
                break;
            }

#line 646
            (*r_1)[o_0 + i_3] = b_4[i_3];

#line 646
            i_3 = i_3 + 1U;

#line 646
        }

#line 638
        s_1 = s_1 << 1U;

#line 638
    }

#line 648
    return;
}


#line 752
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 752
    uint b_5 = 0U;

#line 760
    for(;;)
    {

#line 760
        if(b_5 < 2U)
        {
        }
        else
        {

#line 760
            break;
        }

#line 760
        dft8_0(r_2, b_5 * 8U);

#line 760
        b_5 = b_5 + 1U;

#line 760
    }



    return;
}


#line 880
uint lgOf_0(uint i_4)
{

#line 880
    uint _S24;

#line 880
    if(i_4 < 1U)
    {

#line 880
        _S24 = 4U;

#line 880
    }
    else
    {

#line 880
        if(i_4 == 1U)
        {

#line 880
            _S24 = 3U;

#line 880
        }
        else
        {

#line 880
            _S24 = 1U;

#line 880
        }

#line 880
    }

#line 880
    return _S24;
}


#line 882
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 886
    uint lg_1 = lgOf_0(0U);

#line 891
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 1852
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1852
    uint k2_1;

#line 1852
    uint j_2;

#line 1852
    uint d_3;

#line 1852
    uint b_6;

#line 1852
    uint m0_0;

#line 1852
    uint s0_0;

#line 1852
    uint m1_0;

#line 1852
    thread KernelContext_0 kernelContext_3;

#line 1852
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 1852
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1852
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1852
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1852
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1852
    (&kernelContext_3)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1852
    threadgroup array<uint, int(256)> stg_1;

#line 1852
    (&kernelContext_3)->stg_0 = &stg_1;

#line 1852
    (&kernelContext_3)->_binPhase_0 = 0U;

#line 1870
    uint _pr_0 = gid_0.x;

#line 1870
    uint _t_0 = lid_0.x;
    (&kernelContext_3)->_stgBase_0 = 0U;

#line 1880
    thread uint _ws_0 = entryPointParams_1->winStart_0;

#line 1880
    thread uint _we_0 = entryPointParams_1->winEnd_0;
    uint _S25 = _pr_0 / entryPointParams_1->ntmpl_0;

#line 1881
    rowWindow_0(_S25, &_ws_0, &_we_0, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);
    uint _S26 = _ws_0;

#line 1882
    uint _S27 = _we_0;

#line 1882
    uint _S28 = entryPointParams_1->ntmpl_0;

#line 1882
    uint _S29 = (&kernelContext_3)->entryPointParams_0->binsize_0;

#line 1882
    int _S30 = (&kernelContext_3)->entryPointParams_0->binShift_0;

#line 1882
    uint _S31 = (&kernelContext_3)->entryPointParams_0->nbins_0;

#line 1882
    uint _S32 = (&kernelContext_3)->entryPointParams_0->thrBits_0;

#line 1882
    for(;;)
    {

#line 1882
        (&kernelContext_3)->_tid_0 = _t_0;

#line 1882
        uint _S33 = _pr_0 / _S28;

#line 1882
        uint _S34 = _pr_0 % _S28;

#line 1882
        thread array<float2, int(16)> r_3;

#line 1882
        uint n2_0 = 0U;

#line 1882
        for(;;)
        {

#line 1882
            if(n2_0 < 16U)
            {
            }
            else
            {

#line 1882
                break;
            }

#line 1882
            uint idx_0 = _t_0 + 8U * n2_0;

#line 1882
            uint _S35 = mfDataStrideFlag_0();

#line 1882
            if(_S35 != 0U)
            {

#line 1882
                uint _S36 = mfDataStrideFlag_0();

#line 1882
                k2_1 = _S36;

#line 1882
            }
            else
            {

#line 1882
                k2_1 = 128U;

#line 1882
            }

#line 1882
            r_3[n2_0] = cmulConj_0(cload_0((&kernelContext_3)->entryPointParams_data_0, _S33 * k2_1 + idx_0), cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S34 * 128U + idx_0));

#line 1882
            n2_0 = n2_0 + 1U;

#line 1882
        }

#line 1882
        for(;;)
        {

#line 1882
            for(;;)
            {

#line 1882
                for(;;)
                {

#line 1882
                    for(;;)
                    {

#line 1882
                        uint lgTB_0 = firstbithigh_0(8U);

#line 1882
                        uint lgLn_0 = firstbithigh_0(128U);

#line 1882
                        uint blk_1 = _t_0 >> lgTB_0;

#line 1882
                        uint lane_1 = _t_0 & 7U;

#line 1882
                        dft16_0(&r_3);

#line 1882
                        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 128.0f);

#line 1882
                        float _S37 = tw_0.x;

#line 1882
                        float _S38 = tw_0.y;

#line 1882
                        k2_1 = 0U;

#line 1882
                        float cr_0 = 1.0f;

#line 1882
                        float ci_0 = 0.0f;

#line 1882
                        for(;;)
                        {

#line 1882
                            if(k2_1 < 16U)
                            {
                            }
                            else
                            {

#line 1882
                                break;
                            }

#line 1882
                            r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 1882
                            float nr_0 = cr_0 * _S37 - ci_0 * _S38;

#line 1882
                            float _S39 = cr_0 * _S38 + ci_0 * _S37;

#line 1882
                            k2_1 = k2_1 + 1U;

#line 1882
                            cr_0 = nr_0;

#line 1882
                            ci_0 = _S39;

#line 1882
                        }

#line 1882
                        uint per_1 = 16U / max(8U, 1U);

#line 1882
                        uint _S40 = max(0U, 1U);

#line 1882
                        uint blk2_1 = _t_0 / _S40;

#line 1882
                        uint lane2_1 = _t_0 % _S40;

#line 1882
                        for(;;)
                        {

#line 1882
                            thread array<float2, int(16)> out_0;

#line 1882
                            uint z_1 = 0U;

#line 1882
                            for(;;)
                            {

#line 1882
                                if(z_1 < 16U)
                                {
                                }
                                else
                                {

#line 1882
                                    break;
                                }

#line 1882
                                out_0[z_1] = float2(0.0f, 0.0f);

#line 1882
                                z_1 = z_1 + 1U;

#line 1882
                            }

#line 1882
                            uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 1882
                            uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1882
                            uint p0_0 = computeWant_0(0U, 8U, 128U, blk_1, lane_1, per_1, _S40, 8U, blk2_1, lane2_1);

#line 1882
                            uint _S41 = p0_0 & lenMask_0;

#line 1882
                            uint _S42 = (_S41 >> lgTB_0) * 8U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S41 & spanMask_0);

#line 1882
                            uint c_2 = 0U;

#line 1882
                            for(;;)
                            {

#line 1882
                                if(c_2 < 1U)
                                {
                                }
                                else
                                {

#line 1882
                                    break;
                                }

#line 1882
                                simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 1882
                                j_2 = 0U;

#line 1882
                                for(;;)
                                {

#line 1882
                                    if(j_2 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1882
                                        break;
                                    }

#line 1882
                                    stgPut_0(j_2 * 8U + (&kernelContext_3)->_tid_0, r_3[c_2 * 16U + j_2], &kernelContext_3);

#line 1882
                                    j_2 = j_2 + 1U;

#line 1882
                                }

#line 1882
                                simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 1882
                                d_3 = 0U;

#line 1882
                                for(;;)
                                {

#line 1882
                                    if(d_3 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 1882
                                        break;
                                    }

#line 1882
                                    uint pz_0 = computeWant_0(d_3, 8U, 128U, 0U, 0U, per_1, _S40, 8U, 0U, 0U);

#line 1882
                                    uint _S43 = pz_0 & lenMask_0;

#line 1882
                                    uint az_0 = (_S43 >> lgTB_0) * 8U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S43 & spanMask_0);

#line 1882
                                    float2 _S44 = stgGet_0(_S42 + az_0 - c_2 * 16U * 8U, &kernelContext_3);

#line 1882
                                    out_0[d_3] = _S44;

#line 1882
                                    d_3 = d_3 + 1U;

#line 1882
                                }

#line 1882
                                c_2 = c_2 + 1U;

#line 1882
                            }

#line 1882
                            j_2 = 0U;

#line 1882
                            for(;;)
                            {

#line 1882
                                if(j_2 < 16U)
                                {
                                }
                                else
                                {

#line 1882
                                    break;
                                }

#line 1882
                                r_3[j_2] = out_0[j_2];

#line 1882
                                j_2 = j_2 + 1U;

#line 1882
                            }

#line 1882
                            break;
                        }

#line 1882
                        break;
                    }

#line 1882
                    break;
                }

#line 1882
                break;
            }

#line 1882
            innermost_0(&r_3);

#line 1882
            break;
        }

#line 1882
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1882
        uint i_5;

#line 1882
        uint s0_1;

#line 1882
        uint m1_1;

#line 1882
        uint s1_0;

#line 1882
        uint m2_0;

#line 1882
        uint s2_0;

#line 1882
        uint m3_0;

#line 1882
        bool isCand_0;

#line 1882
        if(_S31 <= 4U)
        {

#line 1882
            if(_t_0 < 4U)
            {

#line 1882
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + _t_0] = _S32;

#line 1882
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _t_0] = 4294967295U;

#line 1882
            }

#line 1882
            float2 _S45 = float2(0.0f, 0.0f);

#line 1882
            i_5 = 0U;

#line 1882
            d_3 = _S32;

#line 1882
            s0_1 = 4294967295U;

#line 1882
            float2 v0_0 = _S45;

#line 1882
            m1_1 = _S32;

#line 1882
            s1_0 = 4294967295U;

#line 1882
            float2 v1_0 = _S45;

#line 1882
            m2_0 = _S32;

#line 1882
            s2_0 = 4294967295U;

#line 1882
            float2 v2_0 = _S45;

#line 1882
            m3_0 = _S32;

#line 1882
            uint s3_0 = 4294967295U;

#line 1882
            float2 v3_0 = _S45;

#line 1882
            for(;;)
            {

#line 1882
                if(i_5 < 16U)
                {
                }
                else
                {

#line 1882
                    break;
                }

#line 1882
                uint slot_1 = _t_0 * 16U + i_5;

#line 1882
                uint idx_1 = slotToIndex_0(slot_1);

#line 1882
                if(idx_1 >= _S26)
                {

#line 1882
                    isCand_0 = idx_1 < _S27;

#line 1882
                }
                else
                {

#line 1882
                    isCand_0 = false;

#line 1882
                }

#line 1882
                if(isCand_0)
                {

#line 1882
                    float rx_0 = r_3[i_5].x;

#line 1882
                    float ry_0 = r_3[i_5].y;

#line 1882
                    uint mag_0 = (as_type<uint>((rx_0 * rx_0 + ry_0 * ry_0)));

#line 1882
                    uint off_0 = idx_1 - _S26 + (&kernelContext_3)->_binPhase_0;

#line 1882
                    if(_S31 == 1U)
                    {

#line 1882
                        b_6 = 0U;

#line 1882
                    }
                    else
                    {

#line 1882
                        if(_S30 >= int(0))
                        {

#line 1882
                            n2_0 = off_0 >> uint(_S30);

#line 1882
                        }
                        else
                        {

#line 1882
                            uint _S46 = off_0 / _S29;

#line 1882
                            n2_0 = _S46;

#line 1882
                        }

#line 1882
                        b_6 = n2_0;

#line 1882
                    }

#line 1882
                    bool _S47;

#line 1882
                    if(b_6 == 0U)
                    {

#line 1882
                        _S47 = mag_0 > d_3;

#line 1882
                    }
                    else
                    {

#line 1882
                        _S47 = false;

#line 1882
                    }

#line 1882
                    float2 v0_1;

#line 1882
                    if(_S47)
                    {

#line 1882
                        float2 _S48 = float2(rx_0, ry_0);

#line 1882
                        m0_0 = mag_0;

#line 1882
                        s0_0 = slot_1;

#line 1882
                        v0_1 = _S48;

#line 1882
                    }
                    else
                    {

#line 1882
                        m0_0 = d_3;

#line 1882
                        s0_0 = s0_1;

#line 1882
                        v0_1 = v0_0;

#line 1882
                    }

#line 1882
                    bool _S49;

#line 1882
                    if(_S31 >= 2U)
                    {

#line 1882
                        _S49 = b_6 == 1U;

#line 1882
                    }
                    else
                    {

#line 1882
                        _S49 = false;

#line 1882
                    }

#line 1882
                    bool _S50;

#line 1882
                    if(_S49)
                    {

#line 1882
                        _S50 = mag_0 > m1_1;

#line 1882
                    }
                    else
                    {

#line 1882
                        _S50 = false;

#line 1882
                    }

#line 1882
                    uint s1_1;

#line 1882
                    float2 v1_1;

#line 1882
                    if(_S50)
                    {

#line 1882
                        float2 _S51 = float2(rx_0, ry_0);

#line 1882
                        m1_0 = mag_0;

#line 1882
                        s1_1 = slot_1;

#line 1882
                        v1_1 = _S51;

#line 1882
                    }
                    else
                    {

#line 1882
                        m1_0 = m1_1;

#line 1882
                        s1_1 = s1_0;

#line 1882
                        v1_1 = v1_0;

#line 1882
                    }

#line 1882
                    bool _S52;

#line 1882
                    if(_S31 >= 3U)
                    {

#line 1882
                        _S52 = b_6 == 2U;

#line 1882
                    }
                    else
                    {

#line 1882
                        _S52 = false;

#line 1882
                    }

#line 1882
                    bool _S53;

#line 1882
                    if(_S52)
                    {

#line 1882
                        _S53 = mag_0 > m2_0;

#line 1882
                    }
                    else
                    {

#line 1882
                        _S53 = false;

#line 1882
                    }

#line 1882
                    uint m2_1;

#line 1882
                    uint s2_1;

#line 1882
                    float2 v2_1;

#line 1882
                    if(_S53)
                    {

#line 1882
                        float2 _S54 = float2(rx_0, ry_0);

#line 1882
                        m2_1 = mag_0;

#line 1882
                        s2_1 = slot_1;

#line 1882
                        v2_1 = _S54;

#line 1882
                    }
                    else
                    {

#line 1882
                        m2_1 = m2_0;

#line 1882
                        s2_1 = s2_0;

#line 1882
                        v2_1 = v2_0;

#line 1882
                    }

#line 1882
                    bool _S55;

#line 1882
                    if(_S31 >= 4U)
                    {

#line 1882
                        _S55 = b_6 == 3U;

#line 1882
                    }
                    else
                    {

#line 1882
                        _S55 = false;

#line 1882
                    }

#line 1882
                    bool _S56;

#line 1882
                    if(_S55)
                    {

#line 1882
                        _S56 = mag_0 > m3_0;

#line 1882
                    }
                    else
                    {

#line 1882
                        _S56 = false;

#line 1882
                    }

#line 1882
                    uint m3_1;

#line 1882
                    uint s3_1;

#line 1882
                    float2 v3_1;

#line 1882
                    if(_S56)
                    {

#line 1882
                        float2 _S57 = float2(rx_0, ry_0);

#line 1882
                        m3_1 = mag_0;

#line 1882
                        s3_1 = slot_1;

#line 1882
                        v3_1 = _S57;

#line 1882
                    }
                    else
                    {

#line 1882
                        m3_1 = m3_0;

#line 1882
                        s3_1 = s3_0;

#line 1882
                        v3_1 = v3_0;

#line 1882
                    }

#line 1882
                    d_3 = m0_0;

#line 1882
                    m1_1 = m1_0;

#line 1882
                    m2_0 = m2_1;

#line 1882
                    m3_0 = m3_1;

#line 1882
                    s0_1 = s0_0;

#line 1882
                    s1_0 = s1_1;

#line 1882
                    s2_0 = s2_1;

#line 1882
                    s3_0 = s3_1;

#line 1882
                    v0_0 = v0_1;

#line 1882
                    v1_0 = v1_1;

#line 1882
                    v2_0 = v2_1;

#line 1882
                    v3_0 = v3_1;

#line 1882
                }

#line 1882
                i_5 = i_5 + 1U;

#line 1882
            }

#line 1882
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1882
            uint wm0_0 = simd_max(d_3);

#line 1882
            bool _S58 = simd_is_first();

#line 1882
            if(_S58)
            {

#line 1882
                isCand_0 = wm0_0 > _S32;

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                uint _S59 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), wm0_0, memory_order_relaxed);

#line 1882
            }

#line 1882
            bool _S60 = _S31 >= 2U;

#line 1882
            if(_S60)
            {

#line 1882
                uint wm1_0 = simd_max(m1_1);

#line 1882
                bool _S61 = simd_is_first();

#line 1882
                if(_S61)
                {

#line 1882
                    isCand_0 = wm1_0 > _S32;

#line 1882
                }
                else
                {

#line 1882
                    isCand_0 = false;

#line 1882
                }

#line 1882
                if(isCand_0)
                {

#line 1882
                    uint _S62 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), wm1_0, memory_order_relaxed);

#line 1882
                }

#line 1882
            }

#line 1882
            bool _S63 = _S31 >= 3U;

#line 1882
            if(_S63)
            {

#line 1882
                uint wm2_0 = simd_max(m2_0);

#line 1882
                bool _S64 = simd_is_first();

#line 1882
                if(_S64)
                {

#line 1882
                    isCand_0 = wm2_0 > _S32;

#line 1882
                }
                else
                {

#line 1882
                    isCand_0 = false;

#line 1882
                }

#line 1882
                if(isCand_0)
                {

#line 1882
                    uint _S65 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U])), wm2_0, memory_order_relaxed);

#line 1882
                }

#line 1882
            }

#line 1882
            bool _S66 = _S31 >= 4U;

#line 1882
            if(_S66)
            {

#line 1882
                uint wm3_0 = simd_max(m3_0);

#line 1882
                bool _S67 = simd_is_first();

#line 1882
                if(_S67)
                {

#line 1882
                    isCand_0 = wm3_0 > _S32;

#line 1882
                }
                else
                {

#line 1882
                    isCand_0 = false;

#line 1882
                }

#line 1882
                if(isCand_0)
                {

#line 1882
                    uint _S68 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U])), wm3_0, memory_order_relaxed);

#line 1882
                }

#line 1882
            }

#line 1882
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1882
            if(s0_1 != 4294967295U)
            {

#line 1882
                isCand_0 = d_3 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0];

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                b_6 = s0_1;

#line 1882
            }
            else
            {

#line 1882
                b_6 = 4294967295U;

#line 1882
            }

#line 1882
            if(_S60)
            {

#line 1882
                isCand_0 = s1_0 != 4294967295U;

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                isCand_0 = m1_1 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U];

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                m0_0 = s1_0;

#line 1882
            }
            else
            {

#line 1882
                m0_0 = 4294967295U;

#line 1882
            }

#line 1882
            if(_S63)
            {

#line 1882
                isCand_0 = s2_0 != 4294967295U;

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                isCand_0 = m2_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U];

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                s0_0 = s2_0;

#line 1882
            }
            else
            {

#line 1882
                s0_0 = 4294967295U;

#line 1882
            }

#line 1882
            if(_S66)
            {

#line 1882
                isCand_0 = s3_0 != 4294967295U;

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                isCand_0 = m3_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U];

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                m1_0 = s3_0;

#line 1882
            }
            else
            {

#line 1882
                m1_0 = 4294967295U;

#line 1882
            }

#line 1882
            uint ww0_0 = simd_min(b_6);

#line 1882
            bool _S69 = simd_is_first();

#line 1882
            if(_S69)
            {

#line 1882
                isCand_0 = ww0_0 != 4294967295U;

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                uint _S70 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U])), ww0_0, memory_order_relaxed);

#line 1882
            }

#line 1882
            if(_S60)
            {

#line 1882
                uint ww1_0 = simd_min(m0_0);

#line 1882
                bool _S71 = simd_is_first();

#line 1882
                if(_S71)
                {

#line 1882
                    isCand_0 = ww1_0 != 4294967295U;

#line 1882
                }
                else
                {

#line 1882
                    isCand_0 = false;

#line 1882
                }

#line 1882
                if(isCand_0)
                {

#line 1882
                    uint _S72 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U])), ww1_0, memory_order_relaxed);

#line 1882
                }

#line 1882
            }

#line 1882
            if(_S63)
            {

#line 1882
                uint ww2_0 = simd_min(s0_0);

#line 1882
                bool _S73 = simd_is_first();

#line 1882
                if(_S73)
                {

#line 1882
                    isCand_0 = ww2_0 != 4294967295U;

#line 1882
                }
                else
                {

#line 1882
                    isCand_0 = false;

#line 1882
                }

#line 1882
                if(isCand_0)
                {

#line 1882
                    uint _S74 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U])), ww2_0, memory_order_relaxed);

#line 1882
                }

#line 1882
            }

#line 1882
            if(_S66)
            {

#line 1882
                uint ww3_0 = simd_min(m1_0);

#line 1882
                bool _S75 = simd_is_first();

#line 1882
                if(_S75)
                {

#line 1882
                    isCand_0 = ww3_0 != 4294967295U;

#line 1882
                }
                else
                {

#line 1882
                    isCand_0 = false;

#line 1882
                }

#line 1882
                if(isCand_0)
                {

#line 1882
                    uint _S76 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U])), ww3_0, memory_order_relaxed);

#line 1882
                }

#line 1882
            }

#line 1882
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1882
            uint baseOut_0 = _pr_0 * _S31;

#line 1882
            if(b_6 != 4294967295U)
            {

#line 1882
                isCand_0 = b_6 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U];

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                *((&kernelContext_3)->entryPointParams_peakIdx_0+baseOut_0) = int(slotToIndex_0(b_6));

#line 1882
                *((&kernelContext_3)->entryPointParams_peakVal_0+baseOut_0) = packed_float2(v0_0) ;

#line 1882
            }

#line 1882
            if(_S60)
            {

#line 1882
                isCand_0 = m0_0 != 4294967295U;

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                isCand_0 = m0_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U];

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                uint _S77 = baseOut_0 + 1U;

#line 1882
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S77) = int(slotToIndex_0(m0_0));

#line 1882
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S77) = packed_float2(v1_0) ;

#line 1882
            }

#line 1882
            if(_S63)
            {

#line 1882
                isCand_0 = s0_0 != 4294967295U;

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                isCand_0 = s0_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U];

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                uint _S78 = baseOut_0 + 2U;

#line 1882
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S78) = int(slotToIndex_0(s0_0));

#line 1882
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S78) = packed_float2(v2_0) ;

#line 1882
            }

#line 1882
            if(_S66)
            {

#line 1882
                isCand_0 = m1_0 != 4294967295U;

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                isCand_0 = m1_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U];

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                uint _S79 = baseOut_0 + 3U;

#line 1882
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S79) = int(slotToIndex_0(m1_0));

#line 1882
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S79) = packed_float2(v3_0) ;

#line 1882
            }

#line 1882
            if(_t_0 < _S31)
            {

#line 1882
                isCand_0 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _t_0]) == 4294967295U;

#line 1882
            }
            else
            {

#line 1882
                isCand_0 = false;

#line 1882
            }

#line 1882
            if(isCand_0)
            {

#line 1882
                uint _S80 = baseOut_0 + _t_0;

#line 1882
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S80) = int(-1);

#line 1882
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S80) = packed_float2(_S45) ;

#line 1882
            }

#line 1882
        }
        else
        {

#line 1882
            d_3 = _t_0;

#line 1882
            for(;;)
            {

#line 1882
                if(d_3 < _S31)
                {
                }
                else
                {

#line 1882
                    break;
                }

#line 1882
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + d_3] = _S32;

#line 1882
                d_3 = d_3 + 8U;

#line 1882
            }

#line 1882
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1882
            i_5 = 0U;

#line 1882
            s0_1 = 0U;

#line 1882
            m1_1 = 0U;

#line 1882
            for(;;)
            {

#line 1882
                if(i_5 < 16U)
                {
                }
                else
                {

#line 1882
                    break;
                }

#line 1882
                uint idx_2 = slotToIndex_0(_t_0 * 16U + i_5);

#line 1882
                if(idx_2 >= _S26)
                {

#line 1882
                    isCand_0 = idx_2 < _S27;

#line 1882
                }
                else
                {

#line 1882
                    isCand_0 = false;

#line 1882
                }

#line 1882
                if(isCand_0)
                {

#line 1882
                    float rx_1 = r_3[i_5].x;

#line 1882
                    float ry_1 = r_3[i_5].y;

#line 1882
                    uint mag_1 = (as_type<uint>((rx_1 * rx_1 + ry_1 * ry_1)));

#line 1882
                    if(mag_1 > _S32)
                    {

#line 1882
                        uint off_1 = idx_2 - _S26 + (&kernelContext_3)->_binPhase_0;

#line 1882
                        if(_S30 >= int(0))
                        {

#line 1882
                            d_3 = off_1 >> uint(_S30);

#line 1882
                        }
                        else
                        {

#line 1882
                            uint _S81 = off_1 / _S29;

#line 1882
                            d_3 = _S81;

#line 1882
                        }

#line 1882
                        uint _S82 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + d_3])), mag_1, memory_order_relaxed);

#line 1882
                        uint bit_0 = 1U << (i_5 & 31U);

#line 1882
                        if(i_5 < 32U)
                        {

#line 1882
                            s1_0 = s0_1 | bit_0;

#line 1882
                            m2_0 = m1_1;

#line 1882
                        }
                        else
                        {

#line 1882
                            uint aboveHi_0 = m1_1 | bit_0;

#line 1882
                            s1_0 = s0_1;

#line 1882
                            m2_0 = aboveHi_0;

#line 1882
                        }

#line 1882
                    }
                    else
                    {

#line 1882
                        s1_0 = s0_1;

#line 1882
                        m2_0 = m1_1;

#line 1882
                    }

#line 1882
                }
                else
                {

#line 1882
                    s1_0 = s0_1;

#line 1882
                    m2_0 = m1_1;

#line 1882
                }

#line 1882
                i_5 = i_5 + 1U;

#line 1882
                s0_1 = s1_0;

#line 1882
                m1_1 = m2_0;

#line 1882
            }

#line 1882
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1882
            if((s0_1 | m1_1) != 0U)
            {

#line 1882
                i_5 = 0U;

#line 1882
                s1_0 = 0U;

#line 1882
                m2_0 = 0U;

#line 1882
                for(;;)
                {

#line 1882
                    if(i_5 < 16U)
                    {
                    }
                    else
                    {

#line 1882
                        break;
                    }

#line 1882
                    uint bit_1 = 1U << (i_5 & 31U);

#line 1882
                    bool _S83 = i_5 < 32U;

#line 1882
                    if(_S83)
                    {

#line 1882
                        isCand_0 = (s0_1 & bit_1) != 0U;

#line 1882
                    }
                    else
                    {

#line 1882
                        isCand_0 = (m1_1 & bit_1) != 0U;

#line 1882
                    }

#line 1882
                    if(isCand_0)
                    {

#line 1882
                        uint off_2 = slotToIndex_0(_t_0 * 16U + i_5) - _S26 + (&kernelContext_3)->_binPhase_0;

#line 1882
                        if(_S30 >= int(0))
                        {

#line 1882
                            d_3 = off_2 >> uint(_S30);

#line 1882
                        }
                        else
                        {

#line 1882
                            uint _S84 = off_2 / _S29;

#line 1882
                            d_3 = _S84;

#line 1882
                        }

#line 1882
                        float rx_2 = r_3[i_5].x;

#line 1882
                        float ry_2 = r_3[i_5].y;

#line 1882
                        if((as_type<uint>((rx_2 * rx_2 + ry_2 * ry_2))) == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + d_3])
                        {

#line 1882
                            if(_S83)
                            {

#line 1882
                                s2_0 = s1_0 | bit_1;

#line 1882
                                m3_0 = m2_0;

#line 1882
                            }
                            else
                            {

#line 1882
                                uint candHi_0 = m2_0 | bit_1;

#line 1882
                                s2_0 = s1_0;

#line 1882
                                m3_0 = candHi_0;

#line 1882
                            }

#line 1882
                        }
                        else
                        {

#line 1882
                            s2_0 = s1_0;

#line 1882
                            m3_0 = m2_0;

#line 1882
                        }

#line 1882
                    }
                    else
                    {

#line 1882
                        s2_0 = s1_0;

#line 1882
                        m3_0 = m2_0;

#line 1882
                    }

#line 1882
                    i_5 = i_5 + 1U;

#line 1882
                    s1_0 = s2_0;

#line 1882
                    m2_0 = m3_0;

#line 1882
                }

#line 1882
                s2_0 = s1_0;

#line 1882
                m3_0 = m2_0;

#line 1882
            }
            else
            {

#line 1882
                s2_0 = 0U;

#line 1882
                m3_0 = 0U;

#line 1882
            }

#line 1882
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1882
            d_3 = _t_0;

#line 1882
            for(;;)
            {

#line 1882
                if(d_3 < _S31)
                {
                }
                else
                {

#line 1882
                    break;
                }

#line 1882
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + d_3] = 4294967295U;

#line 1882
                d_3 = d_3 + 8U;

#line 1882
            }

#line 1882
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1882
            bool _S85 = (s2_0 | m3_0) != 0U;

#line 1882
            if(_S85)
            {

#line 1882
                i_5 = 0U;

#line 1882
                for(;;)
                {

#line 1882
                    if(i_5 < 16U)
                    {
                    }
                    else
                    {

#line 1882
                        break;
                    }

#line 1882
                    uint bit_2 = 1U << (i_5 & 31U);

#line 1882
                    if(i_5 < 32U)
                    {

#line 1882
                        isCand_0 = (s2_0 & bit_2) != 0U;

#line 1882
                    }
                    else
                    {

#line 1882
                        isCand_0 = (m3_0 & bit_2) != 0U;

#line 1882
                    }

#line 1882
                    if(isCand_0)
                    {

#line 1882
                        uint _S86 = _t_0 * 16U + i_5;

#line 1882
                        uint off_3 = slotToIndex_0(_S86) - _S26 + (&kernelContext_3)->_binPhase_0;

#line 1882
                        if(_S30 >= int(0))
                        {

#line 1882
                            d_3 = off_3 >> uint(_S30);

#line 1882
                        }
                        else
                        {

#line 1882
                            uint _S87 = off_3 / _S29;

#line 1882
                            d_3 = _S87;

#line 1882
                        }

#line 1882
                        uint _S88 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + d_3])), _S86, memory_order_relaxed);

#line 1882
                    }

#line 1882
                    i_5 = i_5 + 1U;

#line 1882
                }

#line 1882
            }

#line 1882
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1882
            if(_S85)
            {

#line 1882
                i_5 = 0U;

#line 1882
                for(;;)
                {

#line 1882
                    if(i_5 < 16U)
                    {
                    }
                    else
                    {

#line 1882
                        break;
                    }

#line 1882
                    uint bit_3 = 1U << (i_5 & 31U);

#line 1882
                    if(i_5 < 32U)
                    {

#line 1882
                        isCand_0 = (s2_0 & bit_3) != 0U;

#line 1882
                    }
                    else
                    {

#line 1882
                        isCand_0 = (m3_0 & bit_3) != 0U;

#line 1882
                    }

#line 1882
                    if(isCand_0)
                    {

#line 1882
                        uint _S89 = _t_0 * 16U + i_5;

#line 1882
                        uint idx_3 = slotToIndex_0(_S89);

#line 1882
                        uint off_4 = idx_3 - _S26 + (&kernelContext_3)->_binPhase_0;

#line 1882
                        if(_S30 >= int(0))
                        {

#line 1882
                            d_3 = off_4 >> uint(_S30);

#line 1882
                        }
                        else
                        {

#line 1882
                            uint _S90 = off_4 / _S29;

#line 1882
                            d_3 = _S90;

#line 1882
                        }

#line 1882
                        if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + d_3]) == _S89)
                        {

#line 1882
                            uint o_1 = _pr_0 * _S31 + d_3;

#line 1882
                            *((&kernelContext_3)->entryPointParams_peakIdx_0+o_1) = int(idx_3);

#line 1882
                            *((&kernelContext_3)->entryPointParams_peakVal_0+o_1) = packed_float2(float2(r_3[i_5].x, r_3[i_5].y)) ;

#line 1882
                        }

#line 1882
                    }

#line 1882
                    i_5 = i_5 + 1U;

#line 1882
                }

#line 1882
            }

#line 1882
            d_3 = _t_0;

#line 1882
            for(;;)
            {

#line 1882
                if(d_3 < _S31)
                {
                }
                else
                {

#line 1882
                    break;
                }

#line 1882
                if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + d_3]) == 4294967295U)
                {

#line 1882
                    uint _S91 = _pr_0 * _S31 + d_3;

#line 1882
                    *((&kernelContext_3)->entryPointParams_peakIdx_0+_S91) = int(-1);

#line 1882
                    *((&kernelContext_3)->entryPointParams_peakVal_0+_S91) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1882
                }

#line 1882
                d_3 = d_3 + 8U;

#line 1882
            }

#line 1882
        }

#line 1882
        break;
    }

#line 1888
    return;
}
