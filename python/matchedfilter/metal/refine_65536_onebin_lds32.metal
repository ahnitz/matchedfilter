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


#line 318 "mm_65536_refineListed_onebin_lds32.slang"
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

#line 231 "mm_65536_refineListed_onebin_lds32.slang"
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


#line 174 "mm_65536_refineListed_onebin_lds32.slang"
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


#line 616
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 618
    float2 t1_0 = *a_1 - *c_0;

#line 618
    float2 t2_0 = *b_2 + *d_1;

#line 618
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 620
    *b_2 = t1_0 + j3_0;

#line 620
    *c_0 = t0_0 - t2_0;

#line 620
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


#line 329 "mm_65536_refineListed_onebin_lds32.slang"
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


#line 652
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 659
    uint n1_0 = 0U;
    for(;;)
    {

#line 660
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 660
            break;
        }

#line 660
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 660
        n1_0 = n1_0 + 1U;

#line 660
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 661
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 661
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 662
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 662
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 663
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 663
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 663
    uint k2_0 = 0U;
    for(;;)
    {

#line 664
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 664
            break;
        }

#line 664
        uint _S17 = 4U * k2_0;

#line 664
        r4_0(&(*r_0)[_S17], &(*r_0)[_S17 + 1U], &(*r_0)[_S17 + 2U], &(*r_0)[_S17 + 3U]);

#line 664
        k2_0 = k2_0 + 1U;

#line 664
    }

    float2 t_0 = (*r_0)[int(1)];

#line 666
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 666
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 667
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 667
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 668
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 668
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 669
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 669
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 670
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 670
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 671
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 671
    (*r_0)[int(14)] = t_5;
    return;
}


#line 718
void dft64_0(array<float2, int(64)> thread* r_1)
{

#line 718
    uint k_0;

#line 718
    uint j_0 = 0U;

    for(;;)
    {

#line 720
        if(j_0 < 16U)
        {
        }
        else
        {

#line 720
            break;
        }

#line 721
        r4_0(&(*r_1)[j_0], &(*r_1)[j_0 + 16U], &(*r_1)[j_0 + 32U], &(*r_1)[j_0 + 48U]);

#line 720
        j_0 = j_0 + 1U;

#line 720
    }

    thread array<float2, int(64)> o_0;

#line 722
    uint pp_0 = 0U;
    for(;;)
    {

#line 723
        if(pp_0 < 4U)
        {
        }
        else
        {

#line 723
            break;
        }

#line 724
        thread array<float2, int(16)> b_4;

#line 724
        j_0 = 0U;
        for(;;)
        {

#line 725
            if(j_0 < 16U)
            {
            }
            else
            {

#line 725
                break;
            }
            float2 _S18 = mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f);

#line 727
            b_4[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], _S18);

#line 725
            j_0 = j_0 + 1U;

#line 725
        }



        dft16_0(&b_4);

#line 729
        k_0 = 0U;
        for(;;)
        {

#line 730
            if(k_0 < 16U)
            {
            }
            else
            {

#line 730
                break;
            }

#line 730
            o_0[4U * k_0 + pp_0] = b_4[k_0];

#line 730
            k_0 = k_0 + 1U;

#line 730
        }

#line 723
        pp_0 = pp_0 + 1U;

#line 723
    }

#line 723
    k_0 = 0U;

#line 732
    for(;;)
    {

#line 732
        if(k_0 < 64U)
        {
        }
        else
        {

#line 732
            break;
        }

#line 732
        (*r_1)[k_0] = o_0[k_0];

#line 732
        k_0 = k_0 + 1U;

#line 732
    }
    return;
}


void dftR_0(array<float2, int(64)> thread* r_2)
{

#line 744
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


#line 677
void dft16at_0(array<float2, int(64)> thread* r_3, uint o_1)
{



    thread array<float2, int(16)> b_5;

#line 682
    uint i_3 = 0U;
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
        b_5[i_3] = (*r_3)[o_1 + i_3];

#line 683
        i_3 = i_3 + 1U;

#line 683
    }
    dft16_0(&b_5);

#line 684
    i_3 = 0U;
    for(;;)
    {

#line 685
        if(i_3 < 16U)
        {
        }
        else
        {

#line 685
            break;
        }

#line 685
        (*r_3)[o_1 + i_3] = b_5[i_3];

#line 685
        i_3 = i_3 + 1U;

#line 685
    }

    return;
}


#line 755
void innermost_0(array<float2, int(64)> thread* r_4)
{

#line 755
    uint b_6 = 0U;

#line 760
    for(;;)
    {

#line 760
        if(b_6 < 4U)
        {
        }
        else
        {

#line 760
            break;
        }

#line 760
        dft16at_0(r_4, b_6 * 16U);

#line 760
        b_6 = b_6 + 1U;

#line 760
    }

#line 767
    return;
}


#line 883
uint lgOf_0(uint i_4)
{

#line 883
    uint _S23;

#line 883
    if(i_4 < 2U)
    {

#line 883
        _S23 = 6U;

#line 883
    }
    else
    {

#line 883
        if(i_4 == 2U)
        {

#line 883
            _S23 = 4U;

#line 883
        }
        else
        {

#line 883
            _S23 = 1U;

#line 883
        }

#line 883
    }

#line 883
    return _S23;
}


#line 885
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 889
    uint lg_1 = lgOf_0(1U);

#line 889
    uint lg_2 = lgOf_0(0U);

#line 894
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2402
[[kernel]] void refineListedBounded(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]], uint device* entryPointParams_rowWin_1 [[buffer(7)]])
{

#line 2402
    uint k2_1;

#line 2402
    uint _S24;

#line 2402
    uint _S25;

#line 2402
    uint _S26;

#line 2402
    uint d_3;

#line 2402
    uint j_2;

#line 2402
    bool _S27;

#line 2402
    uint d_4;

#line 2402
    thread KernelContext_0 kernelContext_3;

#line 2402
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 2402
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2402
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2402
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2402
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2402
    (&kernelContext_3)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 2402
    (&kernelContext_3)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2402
    (&kernelContext_3)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 2402
    threadgroup array<uint, int(8192)> stg_1;

#line 2402
    (&kernelContext_3)->stg_0 = &stg_1;

#line 2402
    (&kernelContext_3)->_binPhase_0 = 0U;

#line 2413
    uint _S28 = entryPointParams_count_1[int(0)];

#line 2413
    uint i_5 = gid_0.x;

#line 2444
    for(;;)
    {

#line 2444
        if(i_5 < _S28)
        {
        }
        else
        {

#line 2444
            break;
        }

#line 2445
        (&kernelContext_3)->_stgBase_0 = 0U;
        uint pair_0 = (&kernelContext_3)->entryPointParams_survivors_0[i_5];

#line 2446
        thread uint ws_0 = (&kernelContext_3)->entryPointParams_0->winStart_0;

#line 2446
        thread uint we_0 = (&kernelContext_3)->entryPointParams_0->winEnd_0;
        uint _S29 = pair_0 / (&kernelContext_3)->entryPointParams_0->ntmpl_0;

#line 2447
        rowWindow_0(_S29, &ws_0, &we_0, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);
        uint _S30 = lid_0.x;

#line 2448
        uint _S31 = ws_0;

#line 2448
        uint _S32 = we_0;

#line 2448
        uint _S33 = (&kernelContext_3)->entryPointParams_0->ntmpl_0;

#line 2448
        uint _S34 = (&kernelContext_3)->entryPointParams_0->thrBits_0;

#line 2448
        for(;;)
        {

#line 2448
            for(;;)
            {

#line 2448
                (&kernelContext_3)->_tid_0 = _S30;

#line 2448
                uint _S35 = pair_0 / _S33;

#line 2448
                uint _S36 = pair_0 % _S33;

#line 2448
                thread array<float2, int(64)> r_5;

#line 2448
                uint n2_0 = 0U;

#line 2448
                for(;;)
                {

#line 2448
                    if(n2_0 < 64U)
                    {
                    }
                    else
                    {

#line 2448
                        break;
                    }

#line 2448
                    uint idx_0 = _S30 + 1024U * n2_0;

#line 2448
                    uint _S37 = mfDataStrideFlag_0();

#line 2448
                    if(_S37 != 0U)
                    {

#line 2448
                        uint _S38 = mfDataStrideFlag_0();

#line 2448
                        k2_1 = _S38;

#line 2448
                    }
                    else
                    {

#line 2448
                        k2_1 = 65536U;

#line 2448
                    }

#line 2448
                    r_5[n2_0] = cmulConj_0(cload_0((&kernelContext_3)->entryPointParams_data_0, _S35 * k2_1 + idx_0), cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S36 * 65536U + idx_0));

#line 2448
                    n2_0 = n2_0 + 1U;

#line 2448
                }

#line 2448
                for(;;)
                {

#line 2448
                    for(;;)
                    {

#line 2448
                        for(;;)
                        {

#line 2448
                            for(;;)
                            {

#line 2448
                                uint lgTB_0 = firstbithigh_0(1024U);

#line 2448
                                _S24 = lgTB_0;

#line 2448
                                uint lgLn_0 = firstbithigh_0(65536U);

#line 2448
                                uint blk_1 = _S30 >> lgTB_0;

#line 2448
                                uint lane_1 = _S30 & 1023U;

#line 2448
                                dftR_0(&r_5);

#line 2448
                                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 6.5536e+04f);

#line 2448
                                float _S39 = tw_0.x;

#line 2448
                                float _S40 = tw_0.y;

#line 2448
                                k2_1 = 0U;

#line 2448
                                float cr_0 = 1.0f;

#line 2448
                                float ci_0 = 0.0f;

#line 2448
                                for(;;)
                                {

#line 2448
                                    if(k2_1 < 64U)
                                    {
                                    }
                                    else
                                    {

#line 2448
                                        break;
                                    }

#line 2448
                                    r_5[k2_1] = cmul_0(r_5[k2_1], float2(cr_0, ci_0));

#line 2448
                                    float nr_0 = cr_0 * _S39 - ci_0 * _S40;

#line 2448
                                    float _S41 = cr_0 * _S40 + ci_0 * _S39;

#line 2448
                                    k2_1 = k2_1 + 1U;

#line 2448
                                    cr_0 = nr_0;

#line 2448
                                    ci_0 = _S41;

#line 2448
                                }

#line 2448
                                uint per_1 = 64U / max(1024U, 1U);

#line 2448
                                uint _S42 = max(16U, 1U);

#line 2448
                                _S25 = _S42;

#line 2448
                                uint blk2_1 = _S30 / _S42;

#line 2448
                                uint lane2_1 = _S30 % _S42;

#line 2448
                                for(;;)
                                {

#line 2448
                                    thread array<float2, int(64)> out_0;

#line 2448
                                    uint z_1 = 0U;

#line 2448
                                    for(;;)
                                    {

#line 2448
                                        if(z_1 < 64U)
                                        {
                                        }
                                        else
                                        {

#line 2448
                                            break;
                                        }

#line 2448
                                        out_0[z_1] = float2(0.0f, 0.0f);

#line 2448
                                        z_1 = z_1 + 1U;

#line 2448
                                    }

#line 2448
                                    uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2448
                                    _S26 = spanMask_0;

#line 2448
                                    uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2448
                                    uint p0_0 = computeWant_0(0U, 1024U, 65536U, blk_1, lane_1, per_1, _S42, 1024U, blk2_1, lane2_1);

#line 2448
                                    uint _S43 = p0_0 & lenMask_0;

#line 2448
                                    uint _S44 = _S43 >> lgTB_0;

#line 2448
                                    uint _S45 = _S44 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S43 & spanMask_0);

#line 2448
                                    uint c_2 = 0U;

#line 2448
                                    for(;;)
                                    {

#line 2448
                                        if(c_2 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2448
                                            break;
                                        }

#line 2448
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2448
                                        j_2 = 0U;

#line 2448
                                        for(;;)
                                        {

#line 2448
                                            if(j_2 < 4U)
                                            {
                                            }
                                            else
                                            {

#line 2448
                                                break;
                                            }

#line 2448
                                            stgPut_0(j_2 * 1024U + (&kernelContext_3)->_tid_0, r_5[c_2 * 4U + j_2], &kernelContext_3);

#line 2448
                                            j_2 = j_2 + 1U;

#line 2448
                                        }

#line 2448
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2448
                                        d_3 = 0U;

#line 2448
                                        for(;;)
                                        {

#line 2448
                                            if(d_3 < 64U)
                                            {
                                            }
                                            else
                                            {

#line 2448
                                                break;
                                            }

#line 2448
                                            uint pz_0 = computeWant_0(d_3, 1024U, 65536U, 0U, 0U, per_1, _S42, 1024U, 0U, 0U);

#line 2448
                                            uint _S46 = pz_0 & lenMask_0;

#line 2448
                                            uint iz_0 = _S46 >> lgTB_0;

#line 2448
                                            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S46 & spanMask_0);

#line 2448
                                            uint i_6 = _S44 + iz_0;

#line 2448
                                            uint _S47 = c_2 * 4U;

#line 2448
                                            if(i_6 >= _S47)
                                            {

#line 2448
                                                _S27 = i_6 < ((c_2 + 1U) * 4U);

#line 2448
                                            }
                                            else
                                            {

#line 2448
                                                _S27 = false;

#line 2448
                                            }

#line 2448
                                            if(_S27)
                                            {

#line 2448
                                                float2 _S48 = stgGet_0(_S45 + az_0 - _S47 * 1024U, &kernelContext_3);

#line 2448
                                                out_0[d_3] = _S48;

#line 2448
                                            }

#line 2448
                                            d_3 = d_3 + 1U;

#line 2448
                                        }

#line 2448
                                        c_2 = c_2 + 1U;

#line 2448
                                    }

#line 2448
                                    d_3 = 0U;

#line 2448
                                    for(;;)
                                    {

#line 2448
                                        if(d_3 < 64U)
                                        {
                                        }
                                        else
                                        {

#line 2448
                                            break;
                                        }

#line 2448
                                        r_5[d_3] = out_0[d_3];

#line 2448
                                        d_3 = d_3 + 1U;

#line 2448
                                    }

#line 2448
                                    break;
                                }

#line 2448
                                break;
                            }

#line 2448
                            break;
                        }

#line 2448
                        for(;;)
                        {

#line 2448
                            for(;;)
                            {

#line 2448
                                uint lgTB_1 = firstbithigh_0(16U);

#line 2448
                                uint blk_2 = _S30 >> lgTB_1;

#line 2448
                                uint lane_2 = _S30 & 15U;

#line 2448
                                dftR_0(&r_5);

#line 2448
                                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 2448
                                float _S49 = tw_1.x;

#line 2448
                                float _S50 = tw_1.y;

#line 2448
                                uint k2_2 = 0U;

#line 2448
                                float cr_1 = 1.0f;

#line 2448
                                float ci_1 = 0.0f;

#line 2448
                                for(;;)
                                {

#line 2448
                                    if(k2_2 < 64U)
                                    {
                                    }
                                    else
                                    {

#line 2448
                                        break;
                                    }

#line 2448
                                    r_5[k2_2] = cmul_0(r_5[k2_2], float2(cr_1, ci_1));

#line 2448
                                    float nr_1 = cr_1 * _S49 - ci_1 * _S50;

#line 2448
                                    float _S51 = cr_1 * _S50 + ci_1 * _S49;

#line 2448
                                    k2_2 = k2_2 + 1U;

#line 2448
                                    cr_1 = nr_1;

#line 2448
                                    ci_1 = _S51;

#line 2448
                                }

#line 2448
                                uint per_2 = 64U / _S25;

#line 2448
                                uint _S52 = max(0U, 1U);

#line 2448
                                uint blk2_2 = _S30 / _S52;

#line 2448
                                uint lane2_2 = _S30 % _S52;

#line 2448
                                for(;;)
                                {

#line 2448
                                    thread array<float2, int(64)> out_1;

#line 2448
                                    uint z_2 = 0U;

#line 2448
                                    for(;;)
                                    {

#line 2448
                                        if(z_2 < 64U)
                                        {
                                        }
                                        else
                                        {

#line 2448
                                            break;
                                        }

#line 2448
                                        out_1[z_2] = float2(0.0f, 0.0f);

#line 2448
                                        z_2 = z_2 + 1U;

#line 2448
                                    }

#line 2448
                                    uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2448
                                    uint p0_1 = computeWant_0(0U, 16U, 1024U, blk_2, lane_2, per_2, _S52, 16U, blk2_2, lane2_2);

#line 2448
                                    uint _S53 = p0_1 & _S26;

#line 2448
                                    uint _S54 = _S53 >> lgTB_1;

#line 2448
                                    uint _S55 = _S54 * 1024U + ((p0_1 >> _S24) << lgTB_1) + (_S53 & spanMask_1);

#line 2448
                                    uint c_3 = 0U;

#line 2448
                                    for(;;)
                                    {

#line 2448
                                        if(c_3 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2448
                                            break;
                                        }

#line 2448
                                        bool _S56 = c_3 == 0U;

#line 2448
                                        if(!_S56)
                                        {

#line 2448
                                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2448
                                        }
                                        else
                                        {

#line 2448
                                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2448
                                        }

#line 2448
                                        j_2 = 0U;

#line 2448
                                        for(;;)
                                        {

#line 2448
                                            if(j_2 < 4U)
                                            {
                                            }
                                            else
                                            {

#line 2448
                                                break;
                                            }

#line 2448
                                            stgPut_0(j_2 * 1024U + (&kernelContext_3)->_tid_0, r_5[c_3 * 4U + j_2], &kernelContext_3);

#line 2448
                                            j_2 = j_2 + 1U;

#line 2448
                                        }

#line 2448
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2448
                                        d_4 = 0U;

#line 2448
                                        for(;;)
                                        {

#line 2448
                                            if(d_4 < 64U)
                                            {
                                            }
                                            else
                                            {

#line 2448
                                                break;
                                            }

#line 2448
                                            uint pz_1 = computeWant_0(d_4, 16U, 1024U, 0U, 0U, per_2, _S52, 16U, 0U, 0U);

#line 2448
                                            uint _S57 = pz_1 & _S26;

#line 2448
                                            uint iz_1 = _S57 >> lgTB_1;

#line 2448
                                            uint az_1 = iz_1 * 1024U + ((pz_1 >> _S24) << lgTB_1) + (_S57 & spanMask_1);

#line 2448
                                            uint i_7 = _S54 + iz_1;

#line 2448
                                            uint _S58 = c_3 * 4U;

#line 2448
                                            if(i_7 >= _S58)
                                            {

#line 2448
                                                _S27 = i_7 < ((c_3 + 1U) * 4U);

#line 2448
                                            }
                                            else
                                            {

#line 2448
                                                _S27 = false;

#line 2448
                                            }

#line 2448
                                            if(_S27)
                                            {

#line 2448
                                                float2 _S59 = stgGet_0(_S55 + az_1 - _S58 * 1024U, &kernelContext_3);

#line 2448
                                                out_1[d_4] = _S59;

#line 2448
                                            }

#line 2448
                                            d_4 = d_4 + 1U;

#line 2448
                                        }

#line 2448
                                        c_3 = c_3 + 1U;

#line 2448
                                    }

#line 2448
                                    j_2 = 0U;

#line 2448
                                    for(;;)
                                    {

#line 2448
                                        if(j_2 < 64U)
                                        {
                                        }
                                        else
                                        {

#line 2448
                                            break;
                                        }

#line 2448
                                        r_5[j_2] = out_1[j_2];

#line 2448
                                        j_2 = j_2 + 1U;

#line 2448
                                    }

#line 2448
                                    break;
                                }

#line 2448
                                break;
                            }

#line 2448
                            break;
                        }

#line 2448
                        break;
                    }

#line 2448
                    innermost_0(&r_5);

#line 2448
                    break;
                }

#line 2448
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2448
                float2 _S60 = float2(0.0f, 0.0f);

#line 2448
                if(_S31 == 0U)
                {

#line 2448
                    _S27 = _S32 >= 65536U;

#line 2448
                }
                else
                {

#line 2448
                    _S27 = false;

#line 2448
                }

#line 2448
                uint threadBestBits_0;

#line 2448
                uint threadBestSlot_0;

#line 2448
                bool live_0;

#line 2448
                float2 threadBestVal_0;

#line 2448
                if(_S27)
                {

#line 2448
                    d_4 = 0U;

#line 2448
                    threadBestBits_0 = _S34;

#line 2448
                    threadBestSlot_0 = 4294967295U;

#line 2448
                    threadBestVal_0 = _S60;

#line 2448
                    for(;;)
                    {

#line 2448
                        if(d_4 < 64U)
                        {
                        }
                        else
                        {

#line 2448
                            break;
                        }

#line 2448
                        float _rx_0 = r_5[d_4].x;

#line 2448
                        float _ry_0 = r_5[d_4].y;

#line 2448
                        uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 2448
                        if(magBits_0 > threadBestBits_0)
                        {

#line 2448
                            uint _S61 = _S30 * 64U + d_4;

#line 2448
                            float2 _S62 = float2(_rx_0, _ry_0);

#line 2448
                            threadBestBits_0 = magBits_0;

#line 2448
                            threadBestSlot_0 = _S61;

#line 2448
                            threadBestVal_0 = _S62;

#line 2448
                        }

#line 2448
                        d_4 = d_4 + 1U;

#line 2448
                    }

#line 2448
                }
                else
                {

#line 2448
                    d_4 = 0U;

#line 2448
                    threadBestBits_0 = _S34;

#line 2448
                    threadBestSlot_0 = 4294967295U;

#line 2448
                    threadBestVal_0 = _S60;

#line 2448
                    for(;;)
                    {

#line 2448
                        if(d_4 < 64U)
                        {
                        }
                        else
                        {

#line 2448
                            break;
                        }

#line 2448
                        uint _S63 = _S30 * 64U + d_4;

#line 2448
                        uint idx_1 = slotToIndex_0(_S63);

#line 2448
                        if(idx_1 >= _S31)
                        {

#line 2448
                            live_0 = idx_1 < _S32;

#line 2448
                        }
                        else
                        {

#line 2448
                            live_0 = false;

#line 2448
                        }

#line 2448
                        float _rx_1 = r_5[d_4].x;

#line 2448
                        float _ry_1 = r_5[d_4].y;

#line 2448
                        uint magBits_1;

#line 2448
                        if(live_0)
                        {

#line 2448
                            magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 2448
                        }
                        else
                        {

#line 2448
                            magBits_1 = 0U;

#line 2448
                        }

#line 2448
                        if(magBits_1 > threadBestBits_0)
                        {

#line 2448
                            float2 _S64 = float2(_rx_1, _ry_1);

#line 2448
                            threadBestBits_0 = magBits_1;

#line 2448
                            threadBestSlot_0 = _S63;

#line 2448
                            threadBestVal_0 = _S64;

#line 2448
                        }

#line 2448
                        d_4 = d_4 + 1U;

#line 2448
                    }

#line 2448
                }

#line 2448
                bool _S65 = _S30 == 0U;

#line 2448
                if(_S65)
                {

#line 2448
                    (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0] = _S34;

#line 2448
                    (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U] = 4294967295U;

#line 2448
                }

#line 2448
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2448
                uint wm_0 = simd_max(threadBestBits_0);

#line 2448
                bool _S66 = simd_is_first();

#line 2448
                if(_S66)
                {

#line 2448
                    live_0 = wm_0 > _S34;

#line 2448
                }
                else
                {

#line 2448
                    live_0 = false;

#line 2448
                }

#line 2448
                if(live_0)
                {

#line 2448
                    uint _S67 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), wm_0, memory_order_relaxed);

#line 2448
                }

#line 2448
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2448
                bool _S68;

#line 2448
                if(threadBestBits_0 > _S34)
                {

#line 2448
                    _S68 = threadBestBits_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0];

#line 2448
                }
                else
                {

#line 2448
                    _S68 = false;

#line 2448
                }

#line 2448
                if(_S68)
                {

#line 2448
                    d_4 = threadBestSlot_0;

#line 2448
                }
                else
                {

#line 2448
                    d_4 = 4294967295U;

#line 2448
                }

#line 2448
                uint waveWinner_0 = simd_min(d_4);

#line 2448
                bool _S69 = simd_is_first();

#line 2448
                bool _S70;

#line 2448
                if(_S69)
                {

#line 2448
                    _S70 = waveWinner_0 != 4294967295U;

#line 2448
                }
                else
                {

#line 2448
                    _S70 = false;

#line 2448
                }

#line 2448
                if(_S70)
                {

#line 2448
                    uint _S71 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 2448
                }

#line 2448
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2448
                bool _S72;

#line 2448
                if(threadBestSlot_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])
                {

#line 2448
                    _S72 = threadBestSlot_0 != 4294967295U;

#line 2448
                }
                else
                {

#line 2448
                    _S72 = false;

#line 2448
                }

#line 2448
                if(_S72)
                {

#line 2448
                    *((&kernelContext_3)->entryPointParams_peakIdx_0+pair_0) = int(slotToIndex_0(threadBestSlot_0));

#line 2448
                    *((&kernelContext_3)->entryPointParams_peakVal_0+pair_0) = packed_float2(threadBestVal_0) ;

#line 2448
                }

#line 2448
                bool _S73;

#line 2448
                if(_S65)
                {

#line 2448
                    _S73 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U]) == 4294967295U;

#line 2448
                }
                else
                {

#line 2448
                    _S73 = false;

#line 2448
                }

#line 2448
                if(_S73)
                {

#line 2448
                    *((&kernelContext_3)->entryPointParams_peakIdx_0+pair_0) = int(-1);

#line 2448
                    *((&kernelContext_3)->entryPointParams_peakVal_0+pair_0) = packed_float2(_S60) ;

#line 2448
                }

#line 2448
                break;
            }

#line 2448
            break;
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2444
        i_5 = i_5 + (&kernelContext_3)->entryPointParams_0->gridSize_0;

#line 2444
    }

#line 2453
    return;
}
