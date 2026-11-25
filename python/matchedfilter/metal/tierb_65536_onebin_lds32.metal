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


#line 317 "mm_65536_fusedTierB_onebin_lds32.slang"
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
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 227
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 92 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 230 "mm_65536_fusedTierB_onebin_lds32.slang"
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


#line 173 "mm_65536_fusedTierB_onebin_lds32.slang"
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


#line 328 "mm_65536_fusedTierB_onebin_lds32.slang"
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 328
    float _S13 = a_2.x;

#line 328
    float _S14 = b_3.x;

#line 328
    float _S15 = a_2.y;

#line 328
    float _S16 = b_3.y;

#line 328
    return float2(_S13 * _S14 - _S15 * _S16, _S13 * _S16 + _S15 * _S14);
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
        uint _S17 = 4U * k2_0;

#line 663
        r4_0(&(*r_0)[_S17], &(*r_0)[_S17 + 1U], &(*r_0)[_S17 + 2U], &(*r_0)[_S17 + 3U]);

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


#line 717
void dft64_0(array<float2, int(64)> thread* r_1)
{

#line 717
    uint k_0;

#line 717
    uint j_0 = 0U;

    for(;;)
    {

#line 719
        if(j_0 < 16U)
        {
        }
        else
        {

#line 719
            break;
        }

#line 720
        r4_0(&(*r_1)[j_0], &(*r_1)[j_0 + 16U], &(*r_1)[j_0 + 32U], &(*r_1)[j_0 + 48U]);

#line 719
        j_0 = j_0 + 1U;

#line 719
    }

    thread array<float2, int(64)> o_0;

#line 721
    uint pp_0 = 0U;
    for(;;)
    {

#line 722
        if(pp_0 < 4U)
        {
        }
        else
        {

#line 722
            break;
        }

#line 723
        thread array<float2, int(16)> b_4;

#line 723
        j_0 = 0U;
        for(;;)
        {

#line 724
            if(j_0 < 16U)
            {
            }
            else
            {

#line 724
                break;
            }
            float2 _S18 = mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f);

#line 726
            b_4[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], _S18);

#line 724
            j_0 = j_0 + 1U;

#line 724
        }



        dft16_0(&b_4);

#line 728
        k_0 = 0U;
        for(;;)
        {

#line 729
            if(k_0 < 16U)
            {
            }
            else
            {

#line 729
                break;
            }

#line 729
            o_0[4U * k_0 + pp_0] = b_4[k_0];

#line 729
            k_0 = k_0 + 1U;

#line 729
        }

#line 722
        pp_0 = pp_0 + 1U;

#line 722
    }

#line 722
    k_0 = 0U;

#line 731
    for(;;)
    {

#line 731
        if(k_0 < 64U)
        {
        }
        else
        {

#line 731
            break;
        }

#line 731
        (*r_1)[k_0] = o_0[k_0];

#line 731
        k_0 = k_0 + 1U;

#line 731
    }
    return;
}


void dftR_0(array<float2, int(64)> thread* r_2)
{

#line 743
    dft64_0(r_2);

    return;
}


#line 330
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S19 = max(TB_0, 1U);

#line 332
    uint j_1 = d_2 / _S19;

#line 332
    uint m_0 = d_2 % _S19;

#line 332
    uint _S20;
    if(TB_0 <= 64U)
    {

#line 333
        _S20 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 333
    }
    else
    {

#line 333
        _S20 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 333
    }

#line 333
    return _S20;
}


#line 317
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_1)
{

#line 317
    uint _S21 = 2U * i_1;

#line 317
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S21] = (as_type<uint>((v_0.x)));

#line 317
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S21 + 1U] = (as_type<uint>((v_0.y)));

#line 317
    return;
}


#line 318
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_2)
{

#line 318
    uint _S22 = 2U * i_2;

#line 318
    return float2((as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S22]))), (as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S22 + 1U]))));
}


#line 676
void dft16at_0(array<float2, int(64)> thread* r_3, uint o_1)
{



    thread array<float2, int(16)> b_5;

#line 681
    uint i_3 = 0U;
    for(;;)
    {

#line 682
        if(i_3 < 16U)
        {
        }
        else
        {

#line 682
            break;
        }

#line 682
        b_5[i_3] = (*r_3)[o_1 + i_3];

#line 682
        i_3 = i_3 + 1U;

#line 682
    }
    dft16_0(&b_5);

#line 683
    i_3 = 0U;
    for(;;)
    {

#line 684
        if(i_3 < 16U)
        {
        }
        else
        {

#line 684
            break;
        }

#line 684
        (*r_3)[o_1 + i_3] = b_5[i_3];

#line 684
        i_3 = i_3 + 1U;

#line 684
    }

    return;
}


#line 754
void innermost_0(array<float2, int(64)> thread* r_4)
{

#line 754
    uint b_6 = 0U;

#line 759
    for(;;)
    {

#line 759
        if(b_6 < 4U)
        {
        }
        else
        {

#line 759
            break;
        }

#line 759
        dft16at_0(r_4, b_6 * 16U);

#line 759
        b_6 = b_6 + 1U;

#line 759
    }

#line 766
    return;
}


#line 882
uint lgOf_0(uint i_4)
{

#line 882
    uint _S23;

#line 882
    if(i_4 < 2U)
    {

#line 882
        _S23 = 6U;

#line 882
    }
    else
    {

#line 882
        if(i_4 == 2U)
        {

#line 882
            _S23 = 4U;

#line 882
        }
        else
        {

#line 882
            _S23 = 1U;

#line 882
        }

#line 882
    }

#line 882
    return _S23;
}


#line 884
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 888
    uint lg_1 = lgOf_0(1U);

#line 888
    uint lg_2 = lgOf_0(0U);

#line 893
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1854
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1854
    uint k2_1;

#line 1854
    uint _S24;

#line 1854
    float cr_0;

#line 1854
    float ci_0;

#line 1854
    uint _S25;

#line 1854
    uint z_1;

#line 1854
    uint _S26;

#line 1854
    uint c_2;

#line 1854
    uint d_3;

#line 1854
    uint j_2;

#line 1854
    bool live_0;

#line 1854
    thread KernelContext_0 kernelContext_3;

#line 1854
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 1854
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1854
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1854
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1854
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1854
    (&kernelContext_3)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1854
    threadgroup array<uint, int(8192)> stg_1;

#line 1854
    (&kernelContext_3)->stg_0 = &stg_1;

#line 1854
    (&kernelContext_3)->_binPhase_0 = 0U;

#line 1872
    uint _pr_0 = gid_0.x;

#line 1872
    uint _t_0 = lid_0.x;
    (&kernelContext_3)->_stgBase_0 = 0U;

#line 1882
    thread uint _ws_0 = entryPointParams_1->winStart_0;

#line 1882
    thread uint _we_0 = entryPointParams_1->winEnd_0;
    uint _S27 = _pr_0 / entryPointParams_1->ntmpl_0;

#line 1883
    rowWindow_0(_S27, &_ws_0, &_we_0, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);
    uint _S28 = _ws_0;

#line 1884
    uint _S29 = _we_0;

#line 1884
    uint _S30 = entryPointParams_1->ntmpl_0;

#line 1884
    uint _S31 = (&kernelContext_3)->entryPointParams_0->thrBits_0;

#line 1884
    for(;;)
    {

#line 1884
        (&kernelContext_3)->_tid_0 = _t_0;

#line 1884
        uint _S32 = _pr_0 / _S30;

#line 1884
        uint _S33 = _pr_0 % _S30;

#line 1884
        thread array<float2, int(64)> r_5;

#line 1884
        uint n2_0 = 0U;

#line 1884
        for(;;)
        {

#line 1884
            if(n2_0 < 64U)
            {
            }
            else
            {

#line 1884
                break;
            }

#line 1884
            uint idx_0 = _t_0 + 1024U * n2_0;

#line 1884
            uint _S34 = mfDataStrideFlag_0();

#line 1884
            if(_S34 != 0U)
            {

#line 1884
                uint _S35 = mfDataStrideFlag_0();

#line 1884
                k2_1 = _S35;

#line 1884
            }
            else
            {

#line 1884
                k2_1 = 65536U;

#line 1884
            }

#line 1884
            r_5[n2_0] = cmulConj_0(cload_0((&kernelContext_3)->entryPointParams_data_0, _S32 * k2_1 + idx_0), cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S33 * 65536U + idx_0));

#line 1884
            n2_0 = n2_0 + 1U;

#line 1884
        }

#line 1884
        for(;;)
        {

#line 1884
            for(;;)
            {

#line 1884
                for(;;)
                {

#line 1884
                    for(;;)
                    {

#line 1884
                        uint lgTB_0 = firstbithigh_0(1024U);

#line 1884
                        _S24 = lgTB_0;

#line 1884
                        uint lgLn_0 = firstbithigh_0(65536U);

#line 1884
                        uint blk_1 = _t_0 >> lgTB_0;

#line 1884
                        uint lane_1 = _t_0 & 1023U;

#line 1884
                        dftR_0(&r_5);

#line 1884
                        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 6.5536e+04f);

#line 1884
                        float _S36 = tw_0.x;

#line 1884
                        float _S37 = tw_0.y;

#line 1884
                        k2_1 = 0U;

#line 1884
                        cr_0 = 1.0f;

#line 1884
                        ci_0 = 0.0f;

#line 1884
                        for(;;)
                        {

#line 1884
                            if(k2_1 < 64U)
                            {
                            }
                            else
                            {

#line 1884
                                break;
                            }

#line 1884
                            r_5[k2_1] = cmul_0(r_5[k2_1], float2(cr_0, ci_0));

#line 1884
                            float nr_0 = cr_0 * _S36 - ci_0 * _S37;

#line 1884
                            float _S38 = cr_0 * _S37 + ci_0 * _S36;

#line 1884
                            k2_1 = k2_1 + 1U;

#line 1884
                            cr_0 = nr_0;

#line 1884
                            ci_0 = _S38;

#line 1884
                        }

#line 1884
                        uint per_1 = 64U / max(1024U, 1U);

#line 1884
                        uint _S39 = max(16U, 1U);

#line 1884
                        _S25 = _S39;

#line 1884
                        uint blk2_1 = _t_0 / _S39;

#line 1884
                        uint lane2_1 = _t_0 % _S39;

#line 1884
                        for(;;)
                        {

#line 1884
                            thread array<float2, int(64)> out_0;

#line 1884
                            z_1 = 0U;

#line 1884
                            for(;;)
                            {

#line 1884
                                if(z_1 < 64U)
                                {
                                }
                                else
                                {

#line 1884
                                    break;
                                }

#line 1884
                                out_0[z_1] = float2(0.0f, 0.0f);

#line 1884
                                z_1 = z_1 + 1U;

#line 1884
                            }

#line 1884
                            uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 1884
                            _S26 = spanMask_0;

#line 1884
                            uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1884
                            uint p0_0 = computeWant_0(0U, 1024U, 65536U, blk_1, lane_1, per_1, _S39, 1024U, blk2_1, lane2_1);

#line 1884
                            uint _S40 = p0_0 & lenMask_0;

#line 1884
                            uint _S41 = _S40 >> lgTB_0;

#line 1884
                            uint _S42 = _S41 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S40 & spanMask_0);

#line 1884
                            c_2 = 0U;

#line 1884
                            for(;;)
                            {

#line 1884
                                if(c_2 < 16U)
                                {
                                }
                                else
                                {

#line 1884
                                    break;
                                }

#line 1884
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
                                j_2 = 0U;

#line 1884
                                for(;;)
                                {

#line 1884
                                    if(j_2 < 4U)
                                    {
                                    }
                                    else
                                    {

#line 1884
                                        break;
                                    }

#line 1884
                                    stgPut_0(j_2 * 1024U + (&kernelContext_3)->_tid_0, r_5[c_2 * 4U + j_2], &kernelContext_3);

#line 1884
                                    j_2 = j_2 + 1U;

#line 1884
                                }

#line 1884
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
                                d_3 = 0U;

#line 1884
                                for(;;)
                                {

#line 1884
                                    if(d_3 < 64U)
                                    {
                                    }
                                    else
                                    {

#line 1884
                                        break;
                                    }

#line 1884
                                    uint pz_0 = computeWant_0(d_3, 1024U, 65536U, 0U, 0U, per_1, _S39, 1024U, 0U, 0U);

#line 1884
                                    uint _S43 = pz_0 & lenMask_0;

#line 1884
                                    uint iz_0 = _S43 >> lgTB_0;

#line 1884
                                    uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S43 & spanMask_0);

#line 1884
                                    uint i_5 = _S41 + iz_0;

#line 1884
                                    uint _S44 = c_2 * 4U;

#line 1884
                                    if(i_5 >= _S44)
                                    {

#line 1884
                                        live_0 = i_5 < ((c_2 + 1U) * 4U);

#line 1884
                                    }
                                    else
                                    {

#line 1884
                                        live_0 = false;

#line 1884
                                    }

#line 1884
                                    if(live_0)
                                    {

#line 1884
                                        float2 _S45 = stgGet_0(_S42 + az_0 - _S44 * 1024U, &kernelContext_3);

#line 1884
                                        out_0[d_3] = _S45;

#line 1884
                                    }

#line 1884
                                    d_3 = d_3 + 1U;

#line 1884
                                }

#line 1884
                                c_2 = c_2 + 1U;

#line 1884
                            }

#line 1884
                            d_3 = 0U;

#line 1884
                            for(;;)
                            {

#line 1884
                                if(d_3 < 64U)
                                {
                                }
                                else
                                {

#line 1884
                                    break;
                                }

#line 1884
                                r_5[d_3] = out_0[d_3];

#line 1884
                                d_3 = d_3 + 1U;

#line 1884
                            }

#line 1884
                            break;
                        }

#line 1884
                        break;
                    }

#line 1884
                    break;
                }

#line 1884
                for(;;)
                {

#line 1884
                    for(;;)
                    {

#line 1884
                        uint lgTB_1 = firstbithigh_0(16U);

#line 1884
                        uint blk_2 = _t_0 >> lgTB_1;

#line 1884
                        uint lane_2 = _t_0 & 15U;

#line 1884
                        dftR_0(&r_5);

#line 1884
                        float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 1884
                        float _S46 = tw_1.x;

#line 1884
                        float _S47 = tw_1.y;

#line 1884
                        k2_1 = 0U;

#line 1884
                        cr_0 = 1.0f;

#line 1884
                        ci_0 = 0.0f;

#line 1884
                        for(;;)
                        {

#line 1884
                            if(k2_1 < 64U)
                            {
                            }
                            else
                            {

#line 1884
                                break;
                            }

#line 1884
                            r_5[k2_1] = cmul_0(r_5[k2_1], float2(cr_0, ci_0));

#line 1884
                            float nr_1 = cr_0 * _S46 - ci_0 * _S47;

#line 1884
                            float _S48 = cr_0 * _S47 + ci_0 * _S46;

#line 1884
                            k2_1 = k2_1 + 1U;

#line 1884
                            cr_0 = nr_1;

#line 1884
                            ci_0 = _S48;

#line 1884
                        }

#line 1884
                        uint per_2 = 64U / _S25;

#line 1884
                        uint _S49 = max(0U, 1U);

#line 1884
                        uint blk2_2 = _t_0 / _S49;

#line 1884
                        uint lane2_2 = _t_0 % _S49;

#line 1884
                        for(;;)
                        {

#line 1884
                            thread array<float2, int(64)> out_1;

#line 1884
                            z_1 = 0U;

#line 1884
                            for(;;)
                            {

#line 1884
                                if(z_1 < 64U)
                                {
                                }
                                else
                                {

#line 1884
                                    break;
                                }

#line 1884
                                out_1[z_1] = float2(0.0f, 0.0f);

#line 1884
                                z_1 = z_1 + 1U;

#line 1884
                            }

#line 1884
                            uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 1884
                            uint p0_1 = computeWant_0(0U, 16U, 1024U, blk_2, lane_2, per_2, _S49, 16U, blk2_2, lane2_2);

#line 1884
                            uint _S50 = p0_1 & _S26;

#line 1884
                            uint _S51 = _S50 >> lgTB_1;

#line 1884
                            uint _S52 = _S51 * 1024U + ((p0_1 >> _S24) << lgTB_1) + (_S50 & spanMask_1);

#line 1884
                            c_2 = 0U;

#line 1884
                            for(;;)
                            {

#line 1884
                                if(c_2 < 16U)
                                {
                                }
                                else
                                {

#line 1884
                                    break;
                                }

#line 1884
                                bool _S53 = c_2 == 0U;

#line 1884
                                if(!_S53)
                                {

#line 1884
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
                                }
                                else
                                {

#line 1884
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
                                }

#line 1884
                                j_2 = 0U;

#line 1884
                                for(;;)
                                {

#line 1884
                                    if(j_2 < 4U)
                                    {
                                    }
                                    else
                                    {

#line 1884
                                        break;
                                    }

#line 1884
                                    stgPut_0(j_2 * 1024U + (&kernelContext_3)->_tid_0, r_5[c_2 * 4U + j_2], &kernelContext_3);

#line 1884
                                    j_2 = j_2 + 1U;

#line 1884
                                }

#line 1884
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
                                d_3 = 0U;

#line 1884
                                for(;;)
                                {

#line 1884
                                    if(d_3 < 64U)
                                    {
                                    }
                                    else
                                    {

#line 1884
                                        break;
                                    }

#line 1884
                                    uint pz_1 = computeWant_0(d_3, 16U, 1024U, 0U, 0U, per_2, _S49, 16U, 0U, 0U);

#line 1884
                                    uint _S54 = pz_1 & _S26;

#line 1884
                                    uint iz_1 = _S54 >> lgTB_1;

#line 1884
                                    uint az_1 = iz_1 * 1024U + ((pz_1 >> _S24) << lgTB_1) + (_S54 & spanMask_1);

#line 1884
                                    uint i_6 = _S51 + iz_1;

#line 1884
                                    uint _S55 = c_2 * 4U;

#line 1884
                                    if(i_6 >= _S55)
                                    {

#line 1884
                                        live_0 = i_6 < ((c_2 + 1U) * 4U);

#line 1884
                                    }
                                    else
                                    {

#line 1884
                                        live_0 = false;

#line 1884
                                    }

#line 1884
                                    if(live_0)
                                    {

#line 1884
                                        float2 _S56 = stgGet_0(_S52 + az_1 - _S55 * 1024U, &kernelContext_3);

#line 1884
                                        out_1[d_3] = _S56;

#line 1884
                                    }

#line 1884
                                    d_3 = d_3 + 1U;

#line 1884
                                }

#line 1884
                                c_2 = c_2 + 1U;

#line 1884
                            }

#line 1884
                            d_3 = 0U;

#line 1884
                            for(;;)
                            {

#line 1884
                                if(d_3 < 64U)
                                {
                                }
                                else
                                {

#line 1884
                                    break;
                                }

#line 1884
                                r_5[d_3] = out_1[d_3];

#line 1884
                                d_3 = d_3 + 1U;

#line 1884
                            }

#line 1884
                            break;
                        }

#line 1884
                        break;
                    }

#line 1884
                    break;
                }

#line 1884
                break;
            }

#line 1884
            innermost_0(&r_5);

#line 1884
            break;
        }

#line 1884
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
        float2 _S57 = float2(0.0f, 0.0f);

#line 1884
        if(_S28 == 0U)
        {

#line 1884
            live_0 = _S29 >= 65536U;

#line 1884
        }
        else
        {

#line 1884
            live_0 = false;

#line 1884
        }

#line 1884
        uint threadBestBits_0;

#line 1884
        uint threadBestSlot_0;

#line 1884
        float2 threadBestVal_0;

#line 1884
        if(live_0)
        {

#line 1884
            j_2 = 0U;

#line 1884
            threadBestBits_0 = _S31;

#line 1884
            threadBestSlot_0 = 4294967295U;

#line 1884
            threadBestVal_0 = _S57;

#line 1884
            for(;;)
            {

#line 1884
                if(j_2 < 64U)
                {
                }
                else
                {

#line 1884
                    break;
                }

#line 1884
                float _rx_0 = r_5[j_2].x;

#line 1884
                float _ry_0 = r_5[j_2].y;

#line 1884
                uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1884
                if(magBits_0 > threadBestBits_0)
                {

#line 1884
                    uint _S58 = _t_0 * 64U + j_2;

#line 1884
                    float2 _S59 = float2(_rx_0, _ry_0);

#line 1884
                    threadBestBits_0 = magBits_0;

#line 1884
                    threadBestSlot_0 = _S58;

#line 1884
                    threadBestVal_0 = _S59;

#line 1884
                }

#line 1884
                j_2 = j_2 + 1U;

#line 1884
            }

#line 1884
        }
        else
        {

#line 1884
            j_2 = 0U;

#line 1884
            threadBestBits_0 = _S31;

#line 1884
            threadBestSlot_0 = 4294967295U;

#line 1884
            threadBestVal_0 = _S57;

#line 1884
            for(;;)
            {

#line 1884
                if(j_2 < 64U)
                {
                }
                else
                {

#line 1884
                    break;
                }

#line 1884
                uint _S60 = _t_0 * 64U + j_2;

#line 1884
                uint idx_1 = slotToIndex_0(_S60);

#line 1884
                if(idx_1 >= _S28)
                {

#line 1884
                    live_0 = idx_1 < _S29;

#line 1884
                }
                else
                {

#line 1884
                    live_0 = false;

#line 1884
                }

#line 1884
                float _rx_1 = r_5[j_2].x;

#line 1884
                float _ry_1 = r_5[j_2].y;

#line 1884
                uint magBits_1;

#line 1884
                if(live_0)
                {

#line 1884
                    magBits_1 = (as_type<uint>((_rx_1 * _rx_1 + _ry_1 * _ry_1)));

#line 1884
                }
                else
                {

#line 1884
                    magBits_1 = 0U;

#line 1884
                }

#line 1884
                if(magBits_1 > threadBestBits_0)
                {

#line 1884
                    float2 _S61 = float2(_rx_1, _ry_1);

#line 1884
                    threadBestBits_0 = magBits_1;

#line 1884
                    threadBestSlot_0 = _S60;

#line 1884
                    threadBestVal_0 = _S61;

#line 1884
                }

#line 1884
                j_2 = j_2 + 1U;

#line 1884
            }

#line 1884
        }

#line 1884
        bool _S62 = _t_0 == 0U;

#line 1884
        if(_S62)
        {

#line 1884
            (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0] = _S31;

#line 1884
            (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U] = 4294967295U;

#line 1884
        }

#line 1884
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
        uint wm_0 = simd_max(threadBestBits_0);

#line 1884
        bool _S63 = simd_is_first();

#line 1884
        if(_S63)
        {

#line 1884
            live_0 = wm_0 > _S31;

#line 1884
        }
        else
        {

#line 1884
            live_0 = false;

#line 1884
        }

#line 1884
        if(live_0)
        {

#line 1884
            uint _S64 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1884
        }

#line 1884
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
        if(threadBestBits_0 > _S31)
        {

#line 1884
            live_0 = threadBestBits_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0];

#line 1884
        }
        else
        {

#line 1884
            live_0 = false;

#line 1884
        }

#line 1884
        if(live_0)
        {

#line 1884
            j_2 = threadBestSlot_0;

#line 1884
        }
        else
        {

#line 1884
            j_2 = 4294967295U;

#line 1884
        }

#line 1884
        uint waveWinner_0 = simd_min(j_2);

#line 1884
        bool _S65 = simd_is_first();

#line 1884
        if(_S65)
        {

#line 1884
            live_0 = waveWinner_0 != 4294967295U;

#line 1884
        }
        else
        {

#line 1884
            live_0 = false;

#line 1884
        }

#line 1884
        if(live_0)
        {

#line 1884
            uint _S66 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1884
        }

#line 1884
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
        if(threadBestSlot_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])
        {

#line 1884
            live_0 = threadBestSlot_0 != 4294967295U;

#line 1884
        }
        else
        {

#line 1884
            live_0 = false;

#line 1884
        }

#line 1884
        if(live_0)
        {

#line 1884
            *((&kernelContext_3)->entryPointParams_peakIdx_0+_pr_0) = int(slotToIndex_0(threadBestSlot_0));

#line 1884
            *((&kernelContext_3)->entryPointParams_peakVal_0+_pr_0) = packed_float2(threadBestVal_0) ;

#line 1884
        }

#line 1884
        if(_S62)
        {

#line 1884
            live_0 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U]) == 4294967295U;

#line 1884
        }
        else
        {

#line 1884
            live_0 = false;

#line 1884
        }

#line 1884
        if(live_0)
        {

#line 1884
            *((&kernelContext_3)->entryPointParams_peakIdx_0+_pr_0) = int(-1);

#line 1884
            *((&kernelContext_3)->entryPointParams_peakVal_0+_pr_0) = packed_float2(_S57) ;

#line 1884
        }

#line 1884
        break;
    }

#line 1890
    return;
}
