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


#line 318 "mm_65536_refineListed.slang"
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

#line 231 "mm_65536_refineListed.slang"
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


#line 174 "mm_65536_refineListed.slang"
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


#line 76 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S10 = ((MF_ACCURATE_TRIG));

#line 79
    return _S10;
}


#line 103
float2 mfTwiddle_0(float angle_0)
{

#line 81
    uint _S11 = mfAccurateTrigFlag_0();

#line 105
    if(_S11 == 0U)
    {

#line 106
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S12 = float(quadrant_0);
    float x_0 = angle_0 - _S12 * 1.57079625129699707f - _S12 * 7.54978941586159635e-08f;
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


#line 329 "mm_65536_refineListed.slang"
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 329
    float _S13 = a_2.x;

#line 329
    float _S14 = b_3.x;

#line 329
    float _S15 = a_2.y;

#line 329
    float _S16 = b_3.y;

#line 329
    return float2(_S13 * _S14 - _S15 * _S16, _S13 * _S16 + _S15 * _S14);
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
        uint _S17 = 4U * k2_0;

#line 662
        r4_0(&(*r_0)[_S17], &(*r_0)[_S17 + 1U], &(*r_0)[_S17 + 2U], &(*r_0)[_S17 + 3U]);

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


#line 716
void dft64_0(array<float2, int(64)> thread* r_1)
{

#line 716
    uint k_0;

#line 716
    uint j_0 = 0U;

    for(;;)
    {

#line 718
        if(j_0 < 16U)
        {
        }
        else
        {

#line 718
            break;
        }

#line 719
        r4_0(&(*r_1)[j_0], &(*r_1)[j_0 + 16U], &(*r_1)[j_0 + 32U], &(*r_1)[j_0 + 48U]);

#line 718
        j_0 = j_0 + 1U;

#line 718
    }

    thread array<float2, int(64)> o_0;

#line 720
    uint pp_0 = 0U;
    for(;;)
    {

#line 721
        if(pp_0 < 4U)
        {
        }
        else
        {

#line 721
            break;
        }

#line 722
        thread array<float2, int(16)> b_4;

#line 722
        j_0 = 0U;
        for(;;)
        {

#line 723
            if(j_0 < 16U)
            {
            }
            else
            {

#line 723
                break;
            }
            float2 _S18 = mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f);

#line 725
            b_4[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], _S18);

#line 723
            j_0 = j_0 + 1U;

#line 723
        }



        dft16_0(&b_4);

#line 727
        k_0 = 0U;
        for(;;)
        {

#line 728
            if(k_0 < 16U)
            {
            }
            else
            {

#line 728
                break;
            }

#line 728
            o_0[4U * k_0 + pp_0] = b_4[k_0];

#line 728
            k_0 = k_0 + 1U;

#line 728
        }

#line 721
        pp_0 = pp_0 + 1U;

#line 721
    }

#line 721
    k_0 = 0U;

#line 730
    for(;;)
    {

#line 730
        if(k_0 < 64U)
        {
        }
        else
        {

#line 730
            break;
        }

#line 730
        (*r_1)[k_0] = o_0[k_0];

#line 730
        k_0 = k_0 + 1U;

#line 730
    }
    return;
}


void dftR_0(array<float2, int(64)> thread* r_2)
{

#line 742
    dft64_0(r_2);

    return;
}


#line 331
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S19 = max(TB_0, 1U);

#line 333
    uint j_1 = d_2 / _S19;

#line 333
    uint m_0 = d_2 % _S19;

#line 333
    uint _S20;
    if(TB_0 <= 64U)
    {

#line 334
        _S20 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 334
    }
    else
    {

#line 334
        _S20 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 334
    }

#line 334
    return _S20;
}


#line 318
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 318
    uint _S21 = 2U * i_1;

#line 318
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S21] = (as_type<uint>((v_0.x)));

#line 318
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S21 + 1U] = (as_type<uint>((v_0.y)));

#line 318
    return;
}


#line 319
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_2)
{

#line 319
    uint _S22 = 2U * i_2;

#line 319
    return float2((as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S22]))), (as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S22 + 1U]))));
}


#line 675
void dft16at_0(array<float2, int(64)> thread* r_3, uint o_1)
{



    thread array<float2, int(16)> b_5;

#line 680
    uint i_3 = 0U;
    for(;;)
    {

#line 681
        if(i_3 < 16U)
        {
        }
        else
        {

#line 681
            break;
        }

#line 681
        b_5[i_3] = (*r_3)[o_1 + i_3];

#line 681
        i_3 = i_3 + 1U;

#line 681
    }
    dft16_0(&b_5);

#line 682
    i_3 = 0U;
    for(;;)
    {

#line 683
        if(i_3 < 16U)
        {
        }
        else
        {

#line 683
            break;
        }

#line 683
        (*r_3)[o_1 + i_3] = b_5[i_3];

#line 683
        i_3 = i_3 + 1U;

#line 683
    }

    return;
}


#line 753
void innermost_0(array<float2, int(64)> thread* r_4)
{

#line 753
    uint b_6 = 0U;

#line 758
    for(;;)
    {

#line 758
        if(b_6 < 4U)
        {
        }
        else
        {

#line 758
            break;
        }

#line 758
        dft16at_0(r_4, b_6 * 16U);

#line 758
        b_6 = b_6 + 1U;

#line 758
    }

#line 765
    return;
}


#line 881
uint lgOf_0(uint i_4)
{

#line 881
    uint _S23;

#line 881
    if(i_4 < 2U)
    {

#line 881
        _S23 = 6U;

#line 881
    }
    else
    {

#line 881
        if(i_4 == 2U)
        {

#line 881
            _S23 = 4U;

#line 881
        }
        else
        {

#line 881
            _S23 = 1U;

#line 881
        }

#line 881
    }

#line 881
    return _S23;
}


#line 883
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 887
    uint lg_1 = lgOf_0(1U);

#line 887
    uint lg_2 = lgOf_0(0U);

#line 892
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2244
[[kernel]] void refineListedBounded(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]], uint device* entryPointParams_rowWin_1 [[buffer(7)]])
{

#line 2244
    uint k2_1;

#line 2244
    uint _S24;

#line 2244
    uint _S25;

#line 2244
    uint _S26;

#line 2244
    uint d_3;

#line 2244
    uint j_2;

#line 2244
    bool isCand_0;

#line 2244
    uint d_4;

#line 2244
    uint m0_0;

#line 2244
    uint s0_0;

#line 2244
    uint m1_0;

#line 2244
    bool _S27;

#line 2244
    bool _S28;

#line 2244
    bool _S29;

#line 2244
    bool _S30;

#line 2244
    bool _S31;

#line 2244
    bool _S32;

#line 2244
    bool _S33;

#line 2244
    thread KernelContext_0 kernelContext_3;

#line 2244
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 2244
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2244
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2244
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2244
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2244
    (&kernelContext_3)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2244
    (&kernelContext_3)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2244
    (&kernelContext_3)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 2244
    threadgroup array<uint, int(16384)> stg_1;

#line 2244
    (&kernelContext_3)->stg_0 = &stg_1;

#line 2244
    (&kernelContext_3)->_binPhase_0 = 0U;

#line 2255
    uint _S34 = entryPointParams_count_1[int(0)];

#line 2255
    uint i_5 = gid_0.x;
    for(;;)
    {

#line 2256
        if(i_5 < _S34)
        {
        }
        else
        {

#line 2256
            break;
        }

#line 2257
        (&kernelContext_3)->_stgBase_0 = 0U;
        uint pair_0 = (&kernelContext_3)->entryPointParams_survivors_0[i_5];

#line 2258
        thread uint ws_0 = (&kernelContext_3)->entryPointParams_0->winStart_0;

#line 2258
        thread uint we_0 = (&kernelContext_3)->entryPointParams_0->winEnd_0;
        uint _S35 = pair_0 / (&kernelContext_3)->entryPointParams_0->ntmpl_0;

#line 2259
        rowWindow_0(_S35, &ws_0, &we_0, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);
        uint _S36 = lid_0.x;

#line 2260
        uint _S37 = ws_0;

#line 2260
        uint _S38 = we_0;

#line 2260
        uint _S39 = (&kernelContext_3)->entryPointParams_0->ntmpl_0;

#line 2260
        uint _S40 = (&kernelContext_3)->entryPointParams_0->binsize_0;

#line 2260
        int _S41 = (&kernelContext_3)->entryPointParams_0->binShift_0;

#line 2260
        uint _S42 = (&kernelContext_3)->entryPointParams_0->nbins_0;

#line 2260
        uint _S43 = (&kernelContext_3)->entryPointParams_0->thrBits_0;

#line 2260
        for(;;)
        {

#line 2260
            for(;;)
            {

#line 2260
                (&kernelContext_3)->_tid_0 = _S36;

#line 2260
                uint _S44 = pair_0 / _S39;

#line 2260
                uint _S45 = pair_0 % _S39;

#line 2260
                thread array<float2, int(64)> r_5;

#line 2260
                uint n2_0 = 0U;

#line 2260
                for(;;)
                {

#line 2260
                    if(n2_0 < 64U)
                    {
                    }
                    else
                    {

#line 2260
                        break;
                    }

#line 2260
                    uint idx_0 = _S36 + 1024U * n2_0;

#line 2260
                    uint _S46 = mfDataStrideFlag_0();

#line 2260
                    if(_S46 != 0U)
                    {

#line 2260
                        uint _S47 = mfDataStrideFlag_0();

#line 2260
                        k2_1 = _S47;

#line 2260
                    }
                    else
                    {

#line 2260
                        k2_1 = 65536U;

#line 2260
                    }

#line 2260
                    r_5[n2_0] = cmulConj_0(cload_0((&kernelContext_3)->entryPointParams_data_0, _S44 * k2_1 + idx_0), cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S45 * 65536U + idx_0));

#line 2260
                    n2_0 = n2_0 + 1U;

#line 2260
                }

#line 2260
                for(;;)
                {

#line 2260
                    for(;;)
                    {

#line 2260
                        for(;;)
                        {

#line 2260
                            for(;;)
                            {

#line 2260
                                uint lgTB_0 = firstbithigh_0(1024U);

#line 2260
                                _S24 = lgTB_0;

#line 2260
                                uint lgLn_0 = firstbithigh_0(65536U);

#line 2260
                                uint blk_1 = _S36 >> lgTB_0;

#line 2260
                                uint lane_1 = _S36 & 1023U;

#line 2260
                                dftR_0(&r_5);

#line 2260
                                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 6.5536e+04f);

#line 2260
                                float _S48 = tw_0.x;

#line 2260
                                float _S49 = tw_0.y;

#line 2260
                                k2_1 = 0U;

#line 2260
                                float cr_0 = 1.0f;

#line 2260
                                float ci_0 = 0.0f;

#line 2260
                                for(;;)
                                {

#line 2260
                                    if(k2_1 < 64U)
                                    {
                                    }
                                    else
                                    {

#line 2260
                                        break;
                                    }

#line 2260
                                    r_5[k2_1] = cmul_0(r_5[k2_1], float2(cr_0, ci_0));

#line 2260
                                    float nr_0 = cr_0 * _S48 - ci_0 * _S49;

#line 2260
                                    float _S50 = cr_0 * _S49 + ci_0 * _S48;

#line 2260
                                    k2_1 = k2_1 + 1U;

#line 2260
                                    cr_0 = nr_0;

#line 2260
                                    ci_0 = _S50;

#line 2260
                                }

#line 2260
                                uint per_1 = 64U / max(1024U, 1U);

#line 2260
                                uint _S51 = max(16U, 1U);

#line 2260
                                _S25 = _S51;

#line 2260
                                uint blk2_1 = _S36 / _S51;

#line 2260
                                uint lane2_1 = _S36 % _S51;

#line 2260
                                for(;;)
                                {

#line 2260
                                    thread array<float2, int(64)> out_0;

#line 2260
                                    uint z_1 = 0U;

#line 2260
                                    for(;;)
                                    {

#line 2260
                                        if(z_1 < 64U)
                                        {
                                        }
                                        else
                                        {

#line 2260
                                            break;
                                        }

#line 2260
                                        out_0[z_1] = float2(0.0f, 0.0f);

#line 2260
                                        z_1 = z_1 + 1U;

#line 2260
                                    }

#line 2260
                                    uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2260
                                    _S26 = spanMask_0;

#line 2260
                                    uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2260
                                    uint p0_0 = computeWant_0(0U, 1024U, 65536U, blk_1, lane_1, per_1, _S51, 1024U, blk2_1, lane2_1);

#line 2260
                                    uint _S52 = p0_0 & lenMask_0;

#line 2260
                                    uint _S53 = _S52 >> lgTB_0;

#line 2260
                                    uint _S54 = _S53 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S52 & spanMask_0);

#line 2260
                                    uint c_2 = 0U;

#line 2260
                                    for(;;)
                                    {

#line 2260
                                        if(c_2 < 8U)
                                        {
                                        }
                                        else
                                        {

#line 2260
                                            break;
                                        }

#line 2260
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2260
                                        j_2 = 0U;

#line 2260
                                        for(;;)
                                        {

#line 2260
                                            if(j_2 < 8U)
                                            {
                                            }
                                            else
                                            {

#line 2260
                                                break;
                                            }

#line 2260
                                            stgPut_0(j_2 * 1024U + (&kernelContext_3)->_tid_0, r_5[c_2 * 8U + j_2], &kernelContext_3);

#line 2260
                                            j_2 = j_2 + 1U;

#line 2260
                                        }

#line 2260
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2260
                                        d_3 = 0U;

#line 2260
                                        for(;;)
                                        {

#line 2260
                                            if(d_3 < 64U)
                                            {
                                            }
                                            else
                                            {

#line 2260
                                                break;
                                            }

#line 2260
                                            uint pz_0 = computeWant_0(d_3, 1024U, 65536U, 0U, 0U, per_1, _S51, 1024U, 0U, 0U);

#line 2260
                                            uint _S55 = pz_0 & lenMask_0;

#line 2260
                                            uint iz_0 = _S55 >> lgTB_0;

#line 2260
                                            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S55 & spanMask_0);

#line 2260
                                            uint i_6 = _S53 + iz_0;

#line 2260
                                            uint _S56 = c_2 * 8U;

#line 2260
                                            if(i_6 >= _S56)
                                            {

#line 2260
                                                isCand_0 = i_6 < ((c_2 + 1U) * 8U);

#line 2260
                                            }
                                            else
                                            {

#line 2260
                                                isCand_0 = false;

#line 2260
                                            }

#line 2260
                                            if(isCand_0)
                                            {

#line 2260
                                                float2 _S57 = stgGet_0(_S54 + az_0 - _S56 * 1024U, &kernelContext_3);

#line 2260
                                                out_0[d_3] = _S57;

#line 2260
                                            }

#line 2260
                                            d_3 = d_3 + 1U;

#line 2260
                                        }

#line 2260
                                        c_2 = c_2 + 1U;

#line 2260
                                    }

#line 2260
                                    d_3 = 0U;

#line 2260
                                    for(;;)
                                    {

#line 2260
                                        if(d_3 < 64U)
                                        {
                                        }
                                        else
                                        {

#line 2260
                                            break;
                                        }

#line 2260
                                        r_5[d_3] = out_0[d_3];

#line 2260
                                        d_3 = d_3 + 1U;

#line 2260
                                    }

#line 2260
                                    break;
                                }

#line 2260
                                break;
                            }

#line 2260
                            break;
                        }

#line 2260
                        for(;;)
                        {

#line 2260
                            for(;;)
                            {

#line 2260
                                uint lgTB_1 = firstbithigh_0(16U);

#line 2260
                                uint blk_2 = _S36 >> lgTB_1;

#line 2260
                                uint lane_2 = _S36 & 15U;

#line 2260
                                dftR_0(&r_5);

#line 2260
                                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 2260
                                float _S58 = tw_1.x;

#line 2260
                                float _S59 = tw_1.y;

#line 2260
                                uint k2_2 = 0U;

#line 2260
                                float cr_1 = 1.0f;

#line 2260
                                float ci_1 = 0.0f;

#line 2260
                                for(;;)
                                {

#line 2260
                                    if(k2_2 < 64U)
                                    {
                                    }
                                    else
                                    {

#line 2260
                                        break;
                                    }

#line 2260
                                    r_5[k2_2] = cmul_0(r_5[k2_2], float2(cr_1, ci_1));

#line 2260
                                    float nr_1 = cr_1 * _S58 - ci_1 * _S59;

#line 2260
                                    float _S60 = cr_1 * _S59 + ci_1 * _S58;

#line 2260
                                    k2_2 = k2_2 + 1U;

#line 2260
                                    cr_1 = nr_1;

#line 2260
                                    ci_1 = _S60;

#line 2260
                                }

#line 2260
                                uint per_2 = 64U / _S25;

#line 2260
                                uint _S61 = max(0U, 1U);

#line 2260
                                uint blk2_2 = _S36 / _S61;

#line 2260
                                uint lane2_2 = _S36 % _S61;

#line 2260
                                for(;;)
                                {

#line 2260
                                    thread array<float2, int(64)> out_1;

#line 2260
                                    uint z_2 = 0U;

#line 2260
                                    for(;;)
                                    {

#line 2260
                                        if(z_2 < 64U)
                                        {
                                        }
                                        else
                                        {

#line 2260
                                            break;
                                        }

#line 2260
                                        out_1[z_2] = float2(0.0f, 0.0f);

#line 2260
                                        z_2 = z_2 + 1U;

#line 2260
                                    }

#line 2260
                                    uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2260
                                    uint p0_1 = computeWant_0(0U, 16U, 1024U, blk_2, lane_2, per_2, _S61, 16U, blk2_2, lane2_2);

#line 2260
                                    uint _S62 = p0_1 & _S26;

#line 2260
                                    uint _S63 = _S62 >> lgTB_1;

#line 2260
                                    uint _S64 = _S63 * 1024U + ((p0_1 >> _S24) << lgTB_1) + (_S62 & spanMask_1);

#line 2260
                                    uint c_3 = 0U;

#line 2260
                                    for(;;)
                                    {

#line 2260
                                        if(c_3 < 8U)
                                        {
                                        }
                                        else
                                        {

#line 2260
                                            break;
                                        }

#line 2260
                                        bool _S65 = c_3 == 0U;

#line 2260
                                        if(!_S65)
                                        {

#line 2260
                                            simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2260
                                        }
                                        else
                                        {

#line 2260
                                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2260
                                        }

#line 2260
                                        j_2 = 0U;

#line 2260
                                        for(;;)
                                        {

#line 2260
                                            if(j_2 < 8U)
                                            {
                                            }
                                            else
                                            {

#line 2260
                                                break;
                                            }

#line 2260
                                            stgPut_0(j_2 * 1024U + (&kernelContext_3)->_tid_0, r_5[c_3 * 8U + j_2], &kernelContext_3);

#line 2260
                                            j_2 = j_2 + 1U;

#line 2260
                                        }

#line 2260
                                        simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2260
                                        d_4 = 0U;

#line 2260
                                        for(;;)
                                        {

#line 2260
                                            if(d_4 < 64U)
                                            {
                                            }
                                            else
                                            {

#line 2260
                                                break;
                                            }

#line 2260
                                            uint pz_1 = computeWant_0(d_4, 16U, 1024U, 0U, 0U, per_2, _S61, 16U, 0U, 0U);

#line 2260
                                            uint _S66 = pz_1 & _S26;

#line 2260
                                            uint iz_1 = _S66 >> lgTB_1;

#line 2260
                                            uint az_1 = iz_1 * 1024U + ((pz_1 >> _S24) << lgTB_1) + (_S66 & spanMask_1);

#line 2260
                                            uint i_7 = _S63 + iz_1;

#line 2260
                                            uint _S67 = c_3 * 8U;

#line 2260
                                            if(i_7 >= _S67)
                                            {

#line 2260
                                                isCand_0 = i_7 < ((c_3 + 1U) * 8U);

#line 2260
                                            }
                                            else
                                            {

#line 2260
                                                isCand_0 = false;

#line 2260
                                            }

#line 2260
                                            if(isCand_0)
                                            {

#line 2260
                                                float2 _S68 = stgGet_0(_S64 + az_1 - _S67 * 1024U, &kernelContext_3);

#line 2260
                                                out_1[d_4] = _S68;

#line 2260
                                            }

#line 2260
                                            d_4 = d_4 + 1U;

#line 2260
                                        }

#line 2260
                                        c_3 = c_3 + 1U;

#line 2260
                                    }

#line 2260
                                    j_2 = 0U;

#line 2260
                                    for(;;)
                                    {

#line 2260
                                        if(j_2 < 64U)
                                        {
                                        }
                                        else
                                        {

#line 2260
                                            break;
                                        }

#line 2260
                                        r_5[j_2] = out_1[j_2];

#line 2260
                                        j_2 = j_2 + 1U;

#line 2260
                                    }

#line 2260
                                    break;
                                }

#line 2260
                                break;
                            }

#line 2260
                            break;
                        }

#line 2260
                        break;
                    }

#line 2260
                    innermost_0(&r_5);

#line 2260
                    break;
                }

#line 2260
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2260
                uint s0_1;

#line 2260
                uint m1_1;

#line 2260
                uint s1_0;

#line 2260
                uint i_8;

#line 2260
                uint m2_0;

#line 2260
                uint s2_0;

#line 2260
                uint m3_0;

#line 2260
                uint s3_0;

#line 2260
                uint b_7;

#line 2260
                if(_S42 <= 4U)
                {

#line 2260
                    if(_S36 < 4U)
                    {

#line 2260
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + _S36] = _S43;

#line 2260
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _S36] = 4294967295U;

#line 2260
                    }

#line 2260
                    float2 _S69 = float2(0.0f, 0.0f);

#line 2260
                    i_8 = 0U;

#line 2260
                    d_4 = _S43;

#line 2260
                    s0_1 = 4294967295U;

#line 2260
                    float2 v0_0 = _S69;

#line 2260
                    m1_1 = _S43;

#line 2260
                    s1_0 = 4294967295U;

#line 2260
                    float2 v1_0 = _S69;

#line 2260
                    m2_0 = _S43;

#line 2260
                    s2_0 = 4294967295U;

#line 2260
                    float2 v2_0 = _S69;

#line 2260
                    m3_0 = _S43;

#line 2260
                    s3_0 = 4294967295U;

#line 2260
                    float2 v3_0 = _S69;

#line 2260
                    for(;;)
                    {

#line 2260
                        if(i_8 < 64U)
                        {
                        }
                        else
                        {

#line 2260
                            break;
                        }

#line 2260
                        uint slot_1 = _S36 * 64U + i_8;

#line 2260
                        uint idx_1 = slotToIndex_0(slot_1);

#line 2260
                        if(idx_1 >= _S37)
                        {

#line 2260
                            isCand_0 = idx_1 < _S38;

#line 2260
                        }
                        else
                        {

#line 2260
                            isCand_0 = false;

#line 2260
                        }

#line 2260
                        if(isCand_0)
                        {

#line 2260
                            float rx_0 = r_5[i_8].x;

#line 2260
                            float ry_0 = r_5[i_8].y;

#line 2260
                            uint mag_0 = (as_type<uint>((rx_0 * rx_0 + ry_0 * ry_0)));

#line 2260
                            uint off_0 = idx_1 - _S37 + (&kernelContext_3)->_binPhase_0;

#line 2260
                            if(_S42 == 1U)
                            {

#line 2260
                                b_7 = 0U;

#line 2260
                            }
                            else
                            {

#line 2260
                                if(_S41 >= int(0))
                                {

#line 2260
                                    b_7 = off_0 >> uint(_S41);

#line 2260
                                }
                                else
                                {

#line 2260
                                    uint _S70 = off_0 / _S40;

#line 2260
                                    b_7 = _S70;

#line 2260
                                }

#line 2260
                            }

#line 2260
                            if(b_7 == 0U)
                            {

#line 2260
                                _S27 = mag_0 > d_4;

#line 2260
                            }
                            else
                            {

#line 2260
                                _S27 = false;

#line 2260
                            }

#line 2260
                            float2 v0_1;

#line 2260
                            if(_S27)
                            {

#line 2260
                                float2 _S71 = float2(rx_0, ry_0);

#line 2260
                                m0_0 = mag_0;

#line 2260
                                s0_0 = slot_1;

#line 2260
                                v0_1 = _S71;

#line 2260
                            }
                            else
                            {

#line 2260
                                m0_0 = d_4;

#line 2260
                                s0_0 = s0_1;

#line 2260
                                v0_1 = v0_0;

#line 2260
                            }

#line 2260
                            if(_S42 >= 2U)
                            {

#line 2260
                                _S28 = b_7 == 1U;

#line 2260
                            }
                            else
                            {

#line 2260
                                _S28 = false;

#line 2260
                            }

#line 2260
                            if(_S28)
                            {

#line 2260
                                _S29 = mag_0 > m1_1;

#line 2260
                            }
                            else
                            {

#line 2260
                                _S29 = false;

#line 2260
                            }

#line 2260
                            uint s1_1;

#line 2260
                            float2 v1_1;

#line 2260
                            if(_S29)
                            {

#line 2260
                                float2 _S72 = float2(rx_0, ry_0);

#line 2260
                                m1_0 = mag_0;

#line 2260
                                s1_1 = slot_1;

#line 2260
                                v1_1 = _S72;

#line 2260
                            }
                            else
                            {

#line 2260
                                m1_0 = m1_1;

#line 2260
                                s1_1 = s1_0;

#line 2260
                                v1_1 = v1_0;

#line 2260
                            }

#line 2260
                            if(_S42 >= 3U)
                            {

#line 2260
                                _S30 = b_7 == 2U;

#line 2260
                            }
                            else
                            {

#line 2260
                                _S30 = false;

#line 2260
                            }

#line 2260
                            if(_S30)
                            {

#line 2260
                                _S31 = mag_0 > m2_0;

#line 2260
                            }
                            else
                            {

#line 2260
                                _S31 = false;

#line 2260
                            }

#line 2260
                            uint m2_1;

#line 2260
                            uint s2_1;

#line 2260
                            float2 v2_1;

#line 2260
                            if(_S31)
                            {

#line 2260
                                float2 _S73 = float2(rx_0, ry_0);

#line 2260
                                m2_1 = mag_0;

#line 2260
                                s2_1 = slot_1;

#line 2260
                                v2_1 = _S73;

#line 2260
                            }
                            else
                            {

#line 2260
                                m2_1 = m2_0;

#line 2260
                                s2_1 = s2_0;

#line 2260
                                v2_1 = v2_0;

#line 2260
                            }

#line 2260
                            if(_S42 >= 4U)
                            {

#line 2260
                                _S32 = b_7 == 3U;

#line 2260
                            }
                            else
                            {

#line 2260
                                _S32 = false;

#line 2260
                            }

#line 2260
                            if(_S32)
                            {

#line 2260
                                _S33 = mag_0 > m3_0;

#line 2260
                            }
                            else
                            {

#line 2260
                                _S33 = false;

#line 2260
                            }

#line 2260
                            uint m3_1;

#line 2260
                            uint s3_1;

#line 2260
                            float2 v3_1;

#line 2260
                            if(_S33)
                            {

#line 2260
                                float2 _S74 = float2(rx_0, ry_0);

#line 2260
                                m3_1 = mag_0;

#line 2260
                                s3_1 = slot_1;

#line 2260
                                v3_1 = _S74;

#line 2260
                            }
                            else
                            {

#line 2260
                                m3_1 = m3_0;

#line 2260
                                s3_1 = s3_0;

#line 2260
                                v3_1 = v3_0;

#line 2260
                            }

#line 2260
                            d_4 = m0_0;

#line 2260
                            m1_1 = m1_0;

#line 2260
                            m2_0 = m2_1;

#line 2260
                            m3_0 = m3_1;

#line 2260
                            s0_1 = s0_0;

#line 2260
                            s1_0 = s1_1;

#line 2260
                            s2_0 = s2_1;

#line 2260
                            s3_0 = s3_1;

#line 2260
                            v0_0 = v0_1;

#line 2260
                            v1_0 = v1_1;

#line 2260
                            v2_0 = v2_1;

#line 2260
                            v3_0 = v3_1;

#line 2260
                        }

#line 2260
                        i_8 = i_8 + 1U;

#line 2260
                    }

#line 2260
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2260
                    uint wm0_0 = simd_max(d_4);

#line 2260
                    bool _S75 = simd_is_first();

#line 2260
                    if(_S75)
                    {

#line 2260
                        isCand_0 = wm0_0 > _S43;

#line 2260
                    }
                    else
                    {

#line 2260
                        isCand_0 = false;

#line 2260
                    }

#line 2260
                    if(isCand_0)
                    {

#line 2260
                        uint _S76 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), wm0_0, memory_order_relaxed);

#line 2260
                    }

#line 2260
                    bool _S77 = _S42 >= 2U;

#line 2260
                    if(_S77)
                    {

#line 2260
                        uint wm1_0 = simd_max(m1_1);

#line 2260
                        bool _S78 = simd_is_first();

#line 2260
                        if(_S78)
                        {

#line 2260
                            _S27 = wm1_0 > _S43;

#line 2260
                        }
                        else
                        {

#line 2260
                            _S27 = false;

#line 2260
                        }

#line 2260
                        if(_S27)
                        {

#line 2260
                            uint _S79 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), wm1_0, memory_order_relaxed);

#line 2260
                        }

#line 2260
                    }

#line 2260
                    bool _S80 = _S42 >= 3U;

#line 2260
                    if(_S80)
                    {

#line 2260
                        uint wm2_0 = simd_max(m2_0);

#line 2260
                        bool _S81 = simd_is_first();

#line 2260
                        if(_S81)
                        {

#line 2260
                            _S27 = wm2_0 > _S43;

#line 2260
                        }
                        else
                        {

#line 2260
                            _S27 = false;

#line 2260
                        }

#line 2260
                        if(_S27)
                        {

#line 2260
                            uint _S82 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U])), wm2_0, memory_order_relaxed);

#line 2260
                        }

#line 2260
                    }

#line 2260
                    bool _S83 = _S42 >= 4U;

#line 2260
                    if(_S83)
                    {

#line 2260
                        uint wm3_0 = simd_max(m3_0);

#line 2260
                        bool _S84 = simd_is_first();

#line 2260
                        if(_S84)
                        {

#line 2260
                            _S27 = wm3_0 > _S43;

#line 2260
                        }
                        else
                        {

#line 2260
                            _S27 = false;

#line 2260
                        }

#line 2260
                        if(_S27)
                        {

#line 2260
                            uint _S85 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U])), wm3_0, memory_order_relaxed);

#line 2260
                        }

#line 2260
                    }

#line 2260
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2260
                    if(s0_1 != 4294967295U)
                    {

#line 2260
                        _S27 = d_4 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0];

#line 2260
                    }
                    else
                    {

#line 2260
                        _S27 = false;

#line 2260
                    }

#line 2260
                    if(_S27)
                    {

#line 2260
                        b_7 = s0_1;

#line 2260
                    }
                    else
                    {

#line 2260
                        b_7 = 4294967295U;

#line 2260
                    }

#line 2260
                    if(_S77)
                    {

#line 2260
                        _S28 = s1_0 != 4294967295U;

#line 2260
                    }
                    else
                    {

#line 2260
                        _S28 = false;

#line 2260
                    }

#line 2260
                    if(_S28)
                    {

#line 2260
                        _S29 = m1_1 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U];

#line 2260
                    }
                    else
                    {

#line 2260
                        _S29 = false;

#line 2260
                    }

#line 2260
                    if(_S29)
                    {

#line 2260
                        m0_0 = s1_0;

#line 2260
                    }
                    else
                    {

#line 2260
                        m0_0 = 4294967295U;

#line 2260
                    }

#line 2260
                    if(_S80)
                    {

#line 2260
                        _S30 = s2_0 != 4294967295U;

#line 2260
                    }
                    else
                    {

#line 2260
                        _S30 = false;

#line 2260
                    }

#line 2260
                    if(_S30)
                    {

#line 2260
                        _S31 = m2_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U];

#line 2260
                    }
                    else
                    {

#line 2260
                        _S31 = false;

#line 2260
                    }

#line 2260
                    if(_S31)
                    {

#line 2260
                        s0_0 = s2_0;

#line 2260
                    }
                    else
                    {

#line 2260
                        s0_0 = 4294967295U;

#line 2260
                    }

#line 2260
                    if(_S83)
                    {

#line 2260
                        _S32 = s3_0 != 4294967295U;

#line 2260
                    }
                    else
                    {

#line 2260
                        _S32 = false;

#line 2260
                    }

#line 2260
                    if(_S32)
                    {

#line 2260
                        _S33 = m3_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U];

#line 2260
                    }
                    else
                    {

#line 2260
                        _S33 = false;

#line 2260
                    }

#line 2260
                    if(_S33)
                    {

#line 2260
                        m1_0 = s3_0;

#line 2260
                    }
                    else
                    {

#line 2260
                        m1_0 = 4294967295U;

#line 2260
                    }

#line 2260
                    uint ww0_0 = simd_min(b_7);

#line 2260
                    bool _S86 = simd_is_first();

#line 2260
                    bool _S87;

#line 2260
                    if(_S86)
                    {

#line 2260
                        _S87 = ww0_0 != 4294967295U;

#line 2260
                    }
                    else
                    {

#line 2260
                        _S87 = false;

#line 2260
                    }

#line 2260
                    if(_S87)
                    {

#line 2260
                        uint _S88 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U])), ww0_0, memory_order_relaxed);

#line 2260
                    }

#line 2260
                    bool _S89;

#line 2260
                    if(_S77)
                    {

#line 2260
                        uint ww1_0 = simd_min(m0_0);

#line 2260
                        bool _S90 = simd_is_first();

#line 2260
                        if(_S90)
                        {

#line 2260
                            _S89 = ww1_0 != 4294967295U;

#line 2260
                        }
                        else
                        {

#line 2260
                            _S89 = false;

#line 2260
                        }

#line 2260
                        if(_S89)
                        {

#line 2260
                            uint _S91 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U])), ww1_0, memory_order_relaxed);

#line 2260
                        }

#line 2260
                    }

#line 2260
                    if(_S80)
                    {

#line 2260
                        uint ww2_0 = simd_min(s0_0);

#line 2260
                        bool _S92 = simd_is_first();

#line 2260
                        if(_S92)
                        {

#line 2260
                            _S89 = ww2_0 != 4294967295U;

#line 2260
                        }
                        else
                        {

#line 2260
                            _S89 = false;

#line 2260
                        }

#line 2260
                        if(_S89)
                        {

#line 2260
                            uint _S93 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U])), ww2_0, memory_order_relaxed);

#line 2260
                        }

#line 2260
                    }

#line 2260
                    if(_S83)
                    {

#line 2260
                        uint ww3_0 = simd_min(m1_0);

#line 2260
                        bool _S94 = simd_is_first();

#line 2260
                        if(_S94)
                        {

#line 2260
                            _S89 = ww3_0 != 4294967295U;

#line 2260
                        }
                        else
                        {

#line 2260
                            _S89 = false;

#line 2260
                        }

#line 2260
                        if(_S89)
                        {

#line 2260
                            uint _S95 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U])), ww3_0, memory_order_relaxed);

#line 2260
                        }

#line 2260
                    }

#line 2260
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2260
                    uint baseOut_0 = pair_0 * _S42;

#line 2260
                    if(b_7 != 4294967295U)
                    {

#line 2260
                        _S89 = b_7 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U];

#line 2260
                    }
                    else
                    {

#line 2260
                        _S89 = false;

#line 2260
                    }

#line 2260
                    if(_S89)
                    {

#line 2260
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+baseOut_0) = int(slotToIndex_0(b_7));

#line 2260
                        *((&kernelContext_3)->entryPointParams_peakVal_0+baseOut_0) = packed_float2(v0_0) ;

#line 2260
                    }

#line 2260
                    bool _S96;

#line 2260
                    if(_S77)
                    {

#line 2260
                        _S96 = m0_0 != 4294967295U;

#line 2260
                    }
                    else
                    {

#line 2260
                        _S96 = false;

#line 2260
                    }

#line 2260
                    bool _S97;

#line 2260
                    if(_S96)
                    {

#line 2260
                        _S97 = m0_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U];

#line 2260
                    }
                    else
                    {

#line 2260
                        _S97 = false;

#line 2260
                    }

#line 2260
                    if(_S97)
                    {

#line 2260
                        uint _S98 = baseOut_0 + 1U;

#line 2260
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+_S98) = int(slotToIndex_0(m0_0));

#line 2260
                        *((&kernelContext_3)->entryPointParams_peakVal_0+_S98) = packed_float2(v1_0) ;

#line 2260
                    }

#line 2260
                    bool _S99;

#line 2260
                    if(_S80)
                    {

#line 2260
                        _S99 = s0_0 != 4294967295U;

#line 2260
                    }
                    else
                    {

#line 2260
                        _S99 = false;

#line 2260
                    }

#line 2260
                    bool _S100;

#line 2260
                    if(_S99)
                    {

#line 2260
                        _S100 = s0_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U];

#line 2260
                    }
                    else
                    {

#line 2260
                        _S100 = false;

#line 2260
                    }

#line 2260
                    if(_S100)
                    {

#line 2260
                        uint _S101 = baseOut_0 + 2U;

#line 2260
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+_S101) = int(slotToIndex_0(s0_0));

#line 2260
                        *((&kernelContext_3)->entryPointParams_peakVal_0+_S101) = packed_float2(v2_0) ;

#line 2260
                    }

#line 2260
                    bool _S102;

#line 2260
                    if(_S83)
                    {

#line 2260
                        _S102 = m1_0 != 4294967295U;

#line 2260
                    }
                    else
                    {

#line 2260
                        _S102 = false;

#line 2260
                    }

#line 2260
                    bool _S103;

#line 2260
                    if(_S102)
                    {

#line 2260
                        _S103 = m1_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U];

#line 2260
                    }
                    else
                    {

#line 2260
                        _S103 = false;

#line 2260
                    }

#line 2260
                    if(_S103)
                    {

#line 2260
                        uint _S104 = baseOut_0 + 3U;

#line 2260
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+_S104) = int(slotToIndex_0(m1_0));

#line 2260
                        *((&kernelContext_3)->entryPointParams_peakVal_0+_S104) = packed_float2(v3_0) ;

#line 2260
                    }

#line 2260
                    bool _S105;

#line 2260
                    if(_S36 < _S42)
                    {

#line 2260
                        _S105 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _S36]) == 4294967295U;

#line 2260
                    }
                    else
                    {

#line 2260
                        _S105 = false;

#line 2260
                    }

#line 2260
                    if(_S105)
                    {

#line 2260
                        uint _S106 = baseOut_0 + _S36;

#line 2260
                        *((&kernelContext_3)->entryPointParams_peakIdx_0+_S106) = int(-1);

#line 2260
                        *((&kernelContext_3)->entryPointParams_peakVal_0+_S106) = packed_float2(_S69) ;

#line 2260
                    }

#line 2260
                }
                else
                {

#line 2260
                    d_4 = _S36;

#line 2260
                    for(;;)
                    {

#line 2260
                        if(d_4 < _S42)
                        {
                        }
                        else
                        {

#line 2260
                            break;
                        }

#line 2260
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + d_4] = _S43;

#line 2260
                        d_4 = d_4 + 1024U;

#line 2260
                    }

#line 2260
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2260
                    s0_1 = 0U;

#line 2260
                    m1_1 = 0U;

#line 2260
                    s1_0 = 0U;

#line 2260
                    for(;;)
                    {

#line 2260
                        if(s0_1 < 64U)
                        {
                        }
                        else
                        {

#line 2260
                            break;
                        }

#line 2260
                        uint idx_2 = slotToIndex_0(_S36 * 64U + s0_1);

#line 2260
                        if(idx_2 >= _S37)
                        {

#line 2260
                            isCand_0 = idx_2 < _S38;

#line 2260
                        }
                        else
                        {

#line 2260
                            isCand_0 = false;

#line 2260
                        }

#line 2260
                        if(isCand_0)
                        {

#line 2260
                            float rx_1 = r_5[s0_1].x;

#line 2260
                            float ry_1 = r_5[s0_1].y;

#line 2260
                            uint mag_1 = (as_type<uint>((rx_1 * rx_1 + ry_1 * ry_1)));

#line 2260
                            if(mag_1 > _S43)
                            {

#line 2260
                                uint off_1 = idx_2 - _S37 + (&kernelContext_3)->_binPhase_0;

#line 2260
                                if(_S41 >= int(0))
                                {

#line 2260
                                    m2_0 = off_1 >> uint(_S41);

#line 2260
                                }
                                else
                                {

#line 2260
                                    uint _S107 = off_1 / _S40;

#line 2260
                                    m2_0 = _S107;

#line 2260
                                }

#line 2260
                                uint _S108 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m2_0])), mag_1, memory_order_relaxed);

#line 2260
                                uint bit_0 = 1U << (s0_1 & 31U);

#line 2260
                                if(s0_1 < 32U)
                                {

#line 2260
                                    i_8 = m1_1 | bit_0;

#line 2260
                                    s2_0 = s1_0;

#line 2260
                                }
                                else
                                {

#line 2260
                                    uint aboveHi_0 = s1_0 | bit_0;

#line 2260
                                    i_8 = m1_1;

#line 2260
                                    s2_0 = aboveHi_0;

#line 2260
                                }

#line 2260
                            }
                            else
                            {

#line 2260
                                i_8 = m1_1;

#line 2260
                                s2_0 = s1_0;

#line 2260
                            }

#line 2260
                        }
                        else
                        {

#line 2260
                            i_8 = m1_1;

#line 2260
                            s2_0 = s1_0;

#line 2260
                        }

#line 2260
                        s0_1 = s0_1 + 1U;

#line 2260
                        m1_1 = i_8;

#line 2260
                        s1_0 = s2_0;

#line 2260
                    }

#line 2260
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2260
                    if((m1_1 | s1_0) != 0U)
                    {

#line 2260
                        i_8 = 0U;

#line 2260
                        m2_0 = 0U;

#line 2260
                        s2_0 = 0U;

#line 2260
                        for(;;)
                        {

#line 2260
                            if(i_8 < 64U)
                            {
                            }
                            else
                            {

#line 2260
                                break;
                            }

#line 2260
                            uint bit_1 = 1U << (i_8 & 31U);

#line 2260
                            bool _S109 = i_8 < 32U;

#line 2260
                            if(_S109)
                            {

#line 2260
                                isCand_0 = (m1_1 & bit_1) != 0U;

#line 2260
                            }
                            else
                            {

#line 2260
                                isCand_0 = (s1_0 & bit_1) != 0U;

#line 2260
                            }

#line 2260
                            if(isCand_0)
                            {

#line 2260
                                uint off_2 = slotToIndex_0(_S36 * 64U + i_8) - _S37 + (&kernelContext_3)->_binPhase_0;

#line 2260
                                if(_S41 >= int(0))
                                {

#line 2260
                                    m3_0 = off_2 >> uint(_S41);

#line 2260
                                }
                                else
                                {

#line 2260
                                    uint _S110 = off_2 / _S40;

#line 2260
                                    m3_0 = _S110;

#line 2260
                                }

#line 2260
                                float rx_2 = r_5[i_8].x;

#line 2260
                                float ry_2 = r_5[i_8].y;

#line 2260
                                if((as_type<uint>((rx_2 * rx_2 + ry_2 * ry_2))) == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m3_0])
                                {

#line 2260
                                    if(_S109)
                                    {

#line 2260
                                        s3_0 = m2_0 | bit_1;

#line 2260
                                        b_7 = s2_0;

#line 2260
                                    }
                                    else
                                    {

#line 2260
                                        uint candHi_0 = s2_0 | bit_1;

#line 2260
                                        s3_0 = m2_0;

#line 2260
                                        b_7 = candHi_0;

#line 2260
                                    }

#line 2260
                                }
                                else
                                {

#line 2260
                                    s3_0 = m2_0;

#line 2260
                                    b_7 = s2_0;

#line 2260
                                }

#line 2260
                            }
                            else
                            {

#line 2260
                                s3_0 = m2_0;

#line 2260
                                b_7 = s2_0;

#line 2260
                            }

#line 2260
                            i_8 = i_8 + 1U;

#line 2260
                            m2_0 = s3_0;

#line 2260
                            s2_0 = b_7;

#line 2260
                        }

#line 2260
                        s3_0 = m2_0;

#line 2260
                        b_7 = s2_0;

#line 2260
                    }
                    else
                    {

#line 2260
                        s3_0 = 0U;

#line 2260
                        b_7 = 0U;

#line 2260
                    }

#line 2260
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2260
                    m3_0 = _S36;

#line 2260
                    for(;;)
                    {

#line 2260
                        if(m3_0 < _S42)
                        {
                        }
                        else
                        {

#line 2260
                            break;
                        }

#line 2260
                        (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m3_0] = 4294967295U;

#line 2260
                        m3_0 = m3_0 + 1024U;

#line 2260
                    }

#line 2260
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2260
                    bool _S111 = (s3_0 | b_7) != 0U;

#line 2260
                    if(_S111)
                    {

#line 2260
                        i_8 = 0U;

#line 2260
                        for(;;)
                        {

#line 2260
                            if(i_8 < 64U)
                            {
                            }
                            else
                            {

#line 2260
                                break;
                            }

#line 2260
                            uint bit_2 = 1U << (i_8 & 31U);

#line 2260
                            if(i_8 < 32U)
                            {

#line 2260
                                isCand_0 = (s3_0 & bit_2) != 0U;

#line 2260
                            }
                            else
                            {

#line 2260
                                isCand_0 = (b_7 & bit_2) != 0U;

#line 2260
                            }

#line 2260
                            if(isCand_0)
                            {

#line 2260
                                uint _S112 = _S36 * 64U + i_8;

#line 2260
                                uint off_3 = slotToIndex_0(_S112) - _S37 + (&kernelContext_3)->_binPhase_0;

#line 2260
                                if(_S41 >= int(0))
                                {

#line 2260
                                    m2_0 = off_3 >> uint(_S41);

#line 2260
                                }
                                else
                                {

#line 2260
                                    uint _S113 = off_3 / _S40;

#line 2260
                                    m2_0 = _S113;

#line 2260
                                }

#line 2260
                                uint _S114 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m2_0])), _S112, memory_order_relaxed);

#line 2260
                            }

#line 2260
                            i_8 = i_8 + 1U;

#line 2260
                        }

#line 2260
                    }

#line 2260
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2260
                    if(_S111)
                    {

#line 2260
                        i_8 = 0U;

#line 2260
                        for(;;)
                        {

#line 2260
                            if(i_8 < 64U)
                            {
                            }
                            else
                            {

#line 2260
                                break;
                            }

#line 2260
                            uint bit_3 = 1U << (i_8 & 31U);

#line 2260
                            if(i_8 < 32U)
                            {

#line 2260
                                isCand_0 = (s3_0 & bit_3) != 0U;

#line 2260
                            }
                            else
                            {

#line 2260
                                isCand_0 = (b_7 & bit_3) != 0U;

#line 2260
                            }

#line 2260
                            if(isCand_0)
                            {

#line 2260
                                uint _S115 = _S36 * 64U + i_8;

#line 2260
                                uint idx_3 = slotToIndex_0(_S115);

#line 2260
                                uint off_4 = idx_3 - _S37 + (&kernelContext_3)->_binPhase_0;

#line 2260
                                if(_S41 >= int(0))
                                {

#line 2260
                                    m2_0 = off_4 >> uint(_S41);

#line 2260
                                }
                                else
                                {

#line 2260
                                    uint _S116 = off_4 / _S40;

#line 2260
                                    m2_0 = _S116;

#line 2260
                                }

#line 2260
                                if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m2_0]) == _S115)
                                {

#line 2260
                                    uint o_2 = pair_0 * _S42 + m2_0;

#line 2260
                                    *((&kernelContext_3)->entryPointParams_peakIdx_0+o_2) = int(idx_3);

#line 2260
                                    *((&kernelContext_3)->entryPointParams_peakVal_0+o_2) = packed_float2(float2(r_5[i_8].x, r_5[i_8].y)) ;

#line 2260
                                }

#line 2260
                            }

#line 2260
                            i_8 = i_8 + 1U;

#line 2260
                        }

#line 2260
                    }

#line 2260
                    m2_0 = _S36;

#line 2260
                    for(;;)
                    {

#line 2260
                        if(m2_0 < _S42)
                        {
                        }
                        else
                        {

#line 2260
                            break;
                        }

#line 2260
                        if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + m2_0]) == 4294967295U)
                        {

#line 2260
                            uint _S117 = pair_0 * _S42 + m2_0;

#line 2260
                            *((&kernelContext_3)->entryPointParams_peakIdx_0+_S117) = int(-1);

#line 2260
                            *((&kernelContext_3)->entryPointParams_peakVal_0+_S117) = packed_float2(float2(0.0f, 0.0f)) ;

#line 2260
                        }

#line 2260
                        m2_0 = m2_0 + 1024U;

#line 2260
                    }

#line 2260
                }

#line 2260
                break;
            }

#line 2260
            break;
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2256
        i_5 = i_5 + (&kernelContext_3)->entryPointParams_0->gridSize_0;

#line 2256
    }

#line 2264
    return;
}
