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


#line 317 "mm_65536_fusedTierB_lds32.slang"
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

#line 230 "mm_65536_fusedTierB_lds32.slang"
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


#line 173 "mm_65536_fusedTierB_lds32.slang"
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


#line 328 "mm_65536_fusedTierB_lds32.slang"
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
    bool isCand_0;

#line 1854
    uint b_7;

#line 1854
    uint m0_0;

#line 1854
    uint s0_0;

#line 1854
    uint m1_0;

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
    uint _S31 = (&kernelContext_3)->entryPointParams_0->binsize_0;

#line 1884
    int _S32 = (&kernelContext_3)->entryPointParams_0->binShift_0;

#line 1884
    uint _S33 = (&kernelContext_3)->entryPointParams_0->nbins_0;

#line 1884
    uint _S34 = (&kernelContext_3)->entryPointParams_0->thrBits_0;

#line 1884
    for(;;)
    {

#line 1884
        (&kernelContext_3)->_tid_0 = _t_0;

#line 1884
        uint _S35 = _pr_0 / _S30;

#line 1884
        uint _S36 = _pr_0 % _S30;

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
            uint _S37 = mfDataStrideFlag_0();

#line 1884
            if(_S37 != 0U)
            {

#line 1884
                uint _S38 = mfDataStrideFlag_0();

#line 1884
                k2_1 = _S38;

#line 1884
            }
            else
            {

#line 1884
                k2_1 = 65536U;

#line 1884
            }

#line 1884
            r_5[n2_0] = cmulConj_0(cload_0((&kernelContext_3)->entryPointParams_data_0, _S35 * k2_1 + idx_0), cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S36 * 65536U + idx_0));

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
                        float _S39 = tw_0.x;

#line 1884
                        float _S40 = tw_0.y;

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
                            float nr_0 = cr_0 * _S39 - ci_0 * _S40;

#line 1884
                            float _S41 = cr_0 * _S40 + ci_0 * _S39;

#line 1884
                            k2_1 = k2_1 + 1U;

#line 1884
                            cr_0 = nr_0;

#line 1884
                            ci_0 = _S41;

#line 1884
                        }

#line 1884
                        uint per_1 = 64U / max(1024U, 1U);

#line 1884
                        uint _S42 = max(16U, 1U);

#line 1884
                        _S25 = _S42;

#line 1884
                        uint blk2_1 = _t_0 / _S42;

#line 1884
                        uint lane2_1 = _t_0 % _S42;

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
                            uint p0_0 = computeWant_0(0U, 1024U, 65536U, blk_1, lane_1, per_1, _S42, 1024U, blk2_1, lane2_1);

#line 1884
                            uint _S43 = p0_0 & lenMask_0;

#line 1884
                            uint _S44 = _S43 >> lgTB_0;

#line 1884
                            uint _S45 = _S44 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S43 & spanMask_0);

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
                                    uint pz_0 = computeWant_0(d_3, 1024U, 65536U, 0U, 0U, per_1, _S42, 1024U, 0U, 0U);

#line 1884
                                    uint _S46 = pz_0 & lenMask_0;

#line 1884
                                    uint iz_0 = _S46 >> lgTB_0;

#line 1884
                                    uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S46 & spanMask_0);

#line 1884
                                    uint i_5 = _S44 + iz_0;

#line 1884
                                    uint _S47 = c_2 * 4U;

#line 1884
                                    if(i_5 >= _S47)
                                    {

#line 1884
                                        isCand_0 = i_5 < ((c_2 + 1U) * 4U);

#line 1884
                                    }
                                    else
                                    {

#line 1884
                                        isCand_0 = false;

#line 1884
                                    }

#line 1884
                                    if(isCand_0)
                                    {

#line 1884
                                        float2 _S48 = stgGet_0(_S45 + az_0 - _S47 * 1024U, &kernelContext_3);

#line 1884
                                        out_0[d_3] = _S48;

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
                        float _S49 = tw_1.x;

#line 1884
                        float _S50 = tw_1.y;

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
                            float nr_1 = cr_0 * _S49 - ci_0 * _S50;

#line 1884
                            float _S51 = cr_0 * _S50 + ci_0 * _S49;

#line 1884
                            k2_1 = k2_1 + 1U;

#line 1884
                            cr_0 = nr_1;

#line 1884
                            ci_0 = _S51;

#line 1884
                        }

#line 1884
                        uint per_2 = 64U / _S25;

#line 1884
                        uint _S52 = max(0U, 1U);

#line 1884
                        uint blk2_2 = _t_0 / _S52;

#line 1884
                        uint lane2_2 = _t_0 % _S52;

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
                            uint p0_1 = computeWant_0(0U, 16U, 1024U, blk_2, lane_2, per_2, _S52, 16U, blk2_2, lane2_2);

#line 1884
                            uint _S53 = p0_1 & _S26;

#line 1884
                            uint _S54 = _S53 >> lgTB_1;

#line 1884
                            uint _S55 = _S54 * 1024U + ((p0_1 >> _S24) << lgTB_1) + (_S53 & spanMask_1);

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
                                bool _S56 = c_2 == 0U;

#line 1884
                                if(!_S56)
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
                                    uint pz_1 = computeWant_0(d_3, 16U, 1024U, 0U, 0U, per_2, _S52, 16U, 0U, 0U);

#line 1884
                                    uint _S57 = pz_1 & _S26;

#line 1884
                                    uint iz_1 = _S57 >> lgTB_1;

#line 1884
                                    uint az_1 = iz_1 * 1024U + ((pz_1 >> _S24) << lgTB_1) + (_S57 & spanMask_1);

#line 1884
                                    uint i_6 = _S54 + iz_1;

#line 1884
                                    uint _S58 = c_2 * 4U;

#line 1884
                                    if(i_6 >= _S58)
                                    {

#line 1884
                                        isCand_0 = i_6 < ((c_2 + 1U) * 4U);

#line 1884
                                    }
                                    else
                                    {

#line 1884
                                        isCand_0 = false;

#line 1884
                                    }

#line 1884
                                    if(isCand_0)
                                    {

#line 1884
                                        float2 _S59 = stgGet_0(_S55 + az_1 - _S58 * 1024U, &kernelContext_3);

#line 1884
                                        out_1[d_3] = _S59;

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
        uint i_7;

#line 1884
        uint s0_1;

#line 1884
        uint m1_1;

#line 1884
        uint s1_0;

#line 1884
        uint m2_0;

#line 1884
        uint s2_0;

#line 1884
        uint m3_0;

#line 1884
        if(_S33 <= 4U)
        {

#line 1884
            if(_t_0 < 4U)
            {

#line 1884
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + _t_0] = _S34;

#line 1884
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _t_0] = 4294967295U;

#line 1884
            }

#line 1884
            float2 _S60 = float2(0.0f, 0.0f);

#line 1884
            i_7 = 0U;

#line 1884
            j_2 = _S34;

#line 1884
            s0_1 = 4294967295U;

#line 1884
            float2 v0_0 = _S60;

#line 1884
            m1_1 = _S34;

#line 1884
            s1_0 = 4294967295U;

#line 1884
            float2 v1_0 = _S60;

#line 1884
            m2_0 = _S34;

#line 1884
            s2_0 = 4294967295U;

#line 1884
            float2 v2_0 = _S60;

#line 1884
            m3_0 = _S34;

#line 1884
            uint s3_0 = 4294967295U;

#line 1884
            float2 v3_0 = _S60;

#line 1884
            for(;;)
            {

#line 1884
                if(i_7 < 64U)
                {
                }
                else
                {

#line 1884
                    break;
                }

#line 1884
                uint slot_1 = _t_0 * 64U + i_7;

#line 1884
                uint idx_1 = slotToIndex_0(slot_1);

#line 1884
                if(idx_1 >= _S28)
                {

#line 1884
                    isCand_0 = idx_1 < _S29;

#line 1884
                }
                else
                {

#line 1884
                    isCand_0 = false;

#line 1884
                }

#line 1884
                if(isCand_0)
                {

#line 1884
                    float rx_0 = r_5[i_7].x;

#line 1884
                    float ry_0 = r_5[i_7].y;

#line 1884
                    uint mag_0 = (as_type<uint>((rx_0 * rx_0 + ry_0 * ry_0)));

#line 1884
                    uint off_0 = idx_1 - _S28 + (&kernelContext_3)->_binPhase_0;

#line 1884
                    if(_S33 == 1U)
                    {

#line 1884
                        b_7 = 0U;

#line 1884
                    }
                    else
                    {

#line 1884
                        if(_S32 >= int(0))
                        {

#line 1884
                            n2_0 = off_0 >> uint(_S32);

#line 1884
                        }
                        else
                        {

#line 1884
                            uint _S61 = off_0 / _S31;

#line 1884
                            n2_0 = _S61;

#line 1884
                        }

#line 1884
                        b_7 = n2_0;

#line 1884
                    }

#line 1884
                    bool _S62;

#line 1884
                    if(b_7 == 0U)
                    {

#line 1884
                        _S62 = mag_0 > j_2;

#line 1884
                    }
                    else
                    {

#line 1884
                        _S62 = false;

#line 1884
                    }

#line 1884
                    float2 v0_1;

#line 1884
                    if(_S62)
                    {

#line 1884
                        float2 _S63 = float2(rx_0, ry_0);

#line 1884
                        m0_0 = mag_0;

#line 1884
                        s0_0 = slot_1;

#line 1884
                        v0_1 = _S63;

#line 1884
                    }
                    else
                    {

#line 1884
                        m0_0 = j_2;

#line 1884
                        s0_0 = s0_1;

#line 1884
                        v0_1 = v0_0;

#line 1884
                    }

#line 1884
                    bool _S64;

#line 1884
                    if(_S33 >= 2U)
                    {

#line 1884
                        _S64 = b_7 == 1U;

#line 1884
                    }
                    else
                    {

#line 1884
                        _S64 = false;

#line 1884
                    }

#line 1884
                    bool _S65;

#line 1884
                    if(_S64)
                    {

#line 1884
                        _S65 = mag_0 > m1_1;

#line 1884
                    }
                    else
                    {

#line 1884
                        _S65 = false;

#line 1884
                    }

#line 1884
                    uint s1_1;

#line 1884
                    float2 v1_1;

#line 1884
                    if(_S65)
                    {

#line 1884
                        float2 _S66 = float2(rx_0, ry_0);

#line 1884
                        m1_0 = mag_0;

#line 1884
                        s1_1 = slot_1;

#line 1884
                        v1_1 = _S66;

#line 1884
                    }
                    else
                    {

#line 1884
                        m1_0 = m1_1;

#line 1884
                        s1_1 = s1_0;

#line 1884
                        v1_1 = v1_0;

#line 1884
                    }

#line 1884
                    bool _S67;

#line 1884
                    if(_S33 >= 3U)
                    {

#line 1884
                        _S67 = b_7 == 2U;

#line 1884
                    }
                    else
                    {

#line 1884
                        _S67 = false;

#line 1884
                    }

#line 1884
                    bool _S68;

#line 1884
                    if(_S67)
                    {

#line 1884
                        _S68 = mag_0 > m2_0;

#line 1884
                    }
                    else
                    {

#line 1884
                        _S68 = false;

#line 1884
                    }

#line 1884
                    uint m2_1;

#line 1884
                    uint s2_1;

#line 1884
                    float2 v2_1;

#line 1884
                    if(_S68)
                    {

#line 1884
                        float2 _S69 = float2(rx_0, ry_0);

#line 1884
                        m2_1 = mag_0;

#line 1884
                        s2_1 = slot_1;

#line 1884
                        v2_1 = _S69;

#line 1884
                    }
                    else
                    {

#line 1884
                        m2_1 = m2_0;

#line 1884
                        s2_1 = s2_0;

#line 1884
                        v2_1 = v2_0;

#line 1884
                    }

#line 1884
                    bool _S70;

#line 1884
                    if(_S33 >= 4U)
                    {

#line 1884
                        _S70 = b_7 == 3U;

#line 1884
                    }
                    else
                    {

#line 1884
                        _S70 = false;

#line 1884
                    }

#line 1884
                    bool _S71;

#line 1884
                    if(_S70)
                    {

#line 1884
                        _S71 = mag_0 > m3_0;

#line 1884
                    }
                    else
                    {

#line 1884
                        _S71 = false;

#line 1884
                    }

#line 1884
                    uint m3_1;

#line 1884
                    uint s3_1;

#line 1884
                    float2 v3_1;

#line 1884
                    if(_S71)
                    {

#line 1884
                        float2 _S72 = float2(rx_0, ry_0);

#line 1884
                        m3_1 = mag_0;

#line 1884
                        s3_1 = slot_1;

#line 1884
                        v3_1 = _S72;

#line 1884
                    }
                    else
                    {

#line 1884
                        m3_1 = m3_0;

#line 1884
                        s3_1 = s3_0;

#line 1884
                        v3_1 = v3_0;

#line 1884
                    }

#line 1884
                    j_2 = m0_0;

#line 1884
                    m1_1 = m1_0;

#line 1884
                    m2_0 = m2_1;

#line 1884
                    m3_0 = m3_1;

#line 1884
                    s0_1 = s0_0;

#line 1884
                    s1_0 = s1_1;

#line 1884
                    s2_0 = s2_1;

#line 1884
                    s3_0 = s3_1;

#line 1884
                    v0_0 = v0_1;

#line 1884
                    v1_0 = v1_1;

#line 1884
                    v2_0 = v2_1;

#line 1884
                    v3_0 = v3_1;

#line 1884
                }

#line 1884
                i_7 = i_7 + 1U;

#line 1884
            }

#line 1884
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
            uint wm0_0 = simd_max(j_2);

#line 1884
            bool _S73 = simd_is_first();

#line 1884
            if(_S73)
            {

#line 1884
                isCand_0 = wm0_0 > _S34;

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                uint _S74 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), wm0_0, memory_order_relaxed);

#line 1884
            }

#line 1884
            bool _S75 = _S33 >= 2U;

#line 1884
            if(_S75)
            {

#line 1884
                uint wm1_0 = simd_max(m1_1);

#line 1884
                bool _S76 = simd_is_first();

#line 1884
                if(_S76)
                {

#line 1884
                    isCand_0 = wm1_0 > _S34;

#line 1884
                }
                else
                {

#line 1884
                    isCand_0 = false;

#line 1884
                }

#line 1884
                if(isCand_0)
                {

#line 1884
                    uint _S77 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), wm1_0, memory_order_relaxed);

#line 1884
                }

#line 1884
            }

#line 1884
            bool _S78 = _S33 >= 3U;

#line 1884
            if(_S78)
            {

#line 1884
                uint wm2_0 = simd_max(m2_0);

#line 1884
                bool _S79 = simd_is_first();

#line 1884
                if(_S79)
                {

#line 1884
                    isCand_0 = wm2_0 > _S34;

#line 1884
                }
                else
                {

#line 1884
                    isCand_0 = false;

#line 1884
                }

#line 1884
                if(isCand_0)
                {

#line 1884
                    uint _S80 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U])), wm2_0, memory_order_relaxed);

#line 1884
                }

#line 1884
            }

#line 1884
            bool _S81 = _S33 >= 4U;

#line 1884
            if(_S81)
            {

#line 1884
                uint wm3_0 = simd_max(m3_0);

#line 1884
                bool _S82 = simd_is_first();

#line 1884
                if(_S82)
                {

#line 1884
                    isCand_0 = wm3_0 > _S34;

#line 1884
                }
                else
                {

#line 1884
                    isCand_0 = false;

#line 1884
                }

#line 1884
                if(isCand_0)
                {

#line 1884
                    uint _S83 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U])), wm3_0, memory_order_relaxed);

#line 1884
                }

#line 1884
            }

#line 1884
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
            if(s0_1 != 4294967295U)
            {

#line 1884
                isCand_0 = j_2 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0];

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                b_7 = s0_1;

#line 1884
            }
            else
            {

#line 1884
                b_7 = 4294967295U;

#line 1884
            }

#line 1884
            if(_S75)
            {

#line 1884
                isCand_0 = s1_0 != 4294967295U;

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                isCand_0 = m1_1 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U];

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                m0_0 = s1_0;

#line 1884
            }
            else
            {

#line 1884
                m0_0 = 4294967295U;

#line 1884
            }

#line 1884
            if(_S78)
            {

#line 1884
                isCand_0 = s2_0 != 4294967295U;

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                isCand_0 = m2_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U];

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                s0_0 = s2_0;

#line 1884
            }
            else
            {

#line 1884
                s0_0 = 4294967295U;

#line 1884
            }

#line 1884
            if(_S81)
            {

#line 1884
                isCand_0 = s3_0 != 4294967295U;

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                isCand_0 = m3_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U];

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                m1_0 = s3_0;

#line 1884
            }
            else
            {

#line 1884
                m1_0 = 4294967295U;

#line 1884
            }

#line 1884
            uint ww0_0 = simd_min(b_7);

#line 1884
            bool _S84 = simd_is_first();

#line 1884
            if(_S84)
            {

#line 1884
                isCand_0 = ww0_0 != 4294967295U;

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                uint _S85 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U])), ww0_0, memory_order_relaxed);

#line 1884
            }

#line 1884
            if(_S75)
            {

#line 1884
                uint ww1_0 = simd_min(m0_0);

#line 1884
                bool _S86 = simd_is_first();

#line 1884
                if(_S86)
                {

#line 1884
                    isCand_0 = ww1_0 != 4294967295U;

#line 1884
                }
                else
                {

#line 1884
                    isCand_0 = false;

#line 1884
                }

#line 1884
                if(isCand_0)
                {

#line 1884
                    uint _S87 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U])), ww1_0, memory_order_relaxed);

#line 1884
                }

#line 1884
            }

#line 1884
            if(_S78)
            {

#line 1884
                uint ww2_0 = simd_min(s0_0);

#line 1884
                bool _S88 = simd_is_first();

#line 1884
                if(_S88)
                {

#line 1884
                    isCand_0 = ww2_0 != 4294967295U;

#line 1884
                }
                else
                {

#line 1884
                    isCand_0 = false;

#line 1884
                }

#line 1884
                if(isCand_0)
                {

#line 1884
                    uint _S89 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U])), ww2_0, memory_order_relaxed);

#line 1884
                }

#line 1884
            }

#line 1884
            if(_S81)
            {

#line 1884
                uint ww3_0 = simd_min(m1_0);

#line 1884
                bool _S90 = simd_is_first();

#line 1884
                if(_S90)
                {

#line 1884
                    isCand_0 = ww3_0 != 4294967295U;

#line 1884
                }
                else
                {

#line 1884
                    isCand_0 = false;

#line 1884
                }

#line 1884
                if(isCand_0)
                {

#line 1884
                    uint _S91 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U])), ww3_0, memory_order_relaxed);

#line 1884
                }

#line 1884
            }

#line 1884
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
            uint baseOut_0 = _pr_0 * _S33;

#line 1884
            if(b_7 != 4294967295U)
            {

#line 1884
                isCand_0 = b_7 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U];

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                *((&kernelContext_3)->entryPointParams_peakIdx_0+baseOut_0) = int(slotToIndex_0(b_7));

#line 1884
                *((&kernelContext_3)->entryPointParams_peakVal_0+baseOut_0) = packed_float2(v0_0) ;

#line 1884
            }

#line 1884
            if(_S75)
            {

#line 1884
                isCand_0 = m0_0 != 4294967295U;

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                isCand_0 = m0_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U];

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                uint _S92 = baseOut_0 + 1U;

#line 1884
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S92) = int(slotToIndex_0(m0_0));

#line 1884
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S92) = packed_float2(v1_0) ;

#line 1884
            }

#line 1884
            if(_S78)
            {

#line 1884
                isCand_0 = s0_0 != 4294967295U;

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                isCand_0 = s0_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U];

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                uint _S93 = baseOut_0 + 2U;

#line 1884
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S93) = int(slotToIndex_0(s0_0));

#line 1884
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S93) = packed_float2(v2_0) ;

#line 1884
            }

#line 1884
            if(_S81)
            {

#line 1884
                isCand_0 = m1_0 != 4294967295U;

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                isCand_0 = m1_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U];

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                uint _S94 = baseOut_0 + 3U;

#line 1884
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S94) = int(slotToIndex_0(m1_0));

#line 1884
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S94) = packed_float2(v3_0) ;

#line 1884
            }

#line 1884
            if(_t_0 < _S33)
            {

#line 1884
                isCand_0 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _t_0]) == 4294967295U;

#line 1884
            }
            else
            {

#line 1884
                isCand_0 = false;

#line 1884
            }

#line 1884
            if(isCand_0)
            {

#line 1884
                uint _S95 = baseOut_0 + _t_0;

#line 1884
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S95) = int(-1);

#line 1884
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S95) = packed_float2(_S60) ;

#line 1884
            }

#line 1884
        }
        else
        {

#line 1884
            j_2 = _t_0;

#line 1884
            for(;;)
            {

#line 1884
                if(j_2 < _S33)
                {
                }
                else
                {

#line 1884
                    break;
                }

#line 1884
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2] = _S34;

#line 1884
                j_2 = j_2 + 1024U;

#line 1884
            }

#line 1884
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
            i_7 = 0U;

#line 1884
            s0_1 = 0U;

#line 1884
            m1_1 = 0U;

#line 1884
            for(;;)
            {

#line 1884
                if(i_7 < 64U)
                {
                }
                else
                {

#line 1884
                    break;
                }

#line 1884
                uint idx_2 = slotToIndex_0(_t_0 * 64U + i_7);

#line 1884
                if(idx_2 >= _S28)
                {

#line 1884
                    isCand_0 = idx_2 < _S29;

#line 1884
                }
                else
                {

#line 1884
                    isCand_0 = false;

#line 1884
                }

#line 1884
                if(isCand_0)
                {

#line 1884
                    float rx_1 = r_5[i_7].x;

#line 1884
                    float ry_1 = r_5[i_7].y;

#line 1884
                    uint mag_1 = (as_type<uint>((rx_1 * rx_1 + ry_1 * ry_1)));

#line 1884
                    if(mag_1 > _S34)
                    {

#line 1884
                        uint off_1 = idx_2 - _S28 + (&kernelContext_3)->_binPhase_0;

#line 1884
                        if(_S32 >= int(0))
                        {

#line 1884
                            j_2 = off_1 >> uint(_S32);

#line 1884
                        }
                        else
                        {

#line 1884
                            uint _S96 = off_1 / _S31;

#line 1884
                            j_2 = _S96;

#line 1884
                        }

#line 1884
                        uint _S97 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2])), mag_1, memory_order_relaxed);

#line 1884
                        uint bit_0 = 1U << (i_7 & 31U);

#line 1884
                        if(i_7 < 32U)
                        {

#line 1884
                            s1_0 = s0_1 | bit_0;

#line 1884
                            m2_0 = m1_1;

#line 1884
                        }
                        else
                        {

#line 1884
                            uint aboveHi_0 = m1_1 | bit_0;

#line 1884
                            s1_0 = s0_1;

#line 1884
                            m2_0 = aboveHi_0;

#line 1884
                        }

#line 1884
                    }
                    else
                    {

#line 1884
                        s1_0 = s0_1;

#line 1884
                        m2_0 = m1_1;

#line 1884
                    }

#line 1884
                }
                else
                {

#line 1884
                    s1_0 = s0_1;

#line 1884
                    m2_0 = m1_1;

#line 1884
                }

#line 1884
                i_7 = i_7 + 1U;

#line 1884
                s0_1 = s1_0;

#line 1884
                m1_1 = m2_0;

#line 1884
            }

#line 1884
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
            if((s0_1 | m1_1) != 0U)
            {

#line 1884
                i_7 = 0U;

#line 1884
                s1_0 = 0U;

#line 1884
                m2_0 = 0U;

#line 1884
                for(;;)
                {

#line 1884
                    if(i_7 < 64U)
                    {
                    }
                    else
                    {

#line 1884
                        break;
                    }

#line 1884
                    uint bit_1 = 1U << (i_7 & 31U);

#line 1884
                    bool _S98 = i_7 < 32U;

#line 1884
                    if(_S98)
                    {

#line 1884
                        isCand_0 = (s0_1 & bit_1) != 0U;

#line 1884
                    }
                    else
                    {

#line 1884
                        isCand_0 = (m1_1 & bit_1) != 0U;

#line 1884
                    }

#line 1884
                    if(isCand_0)
                    {

#line 1884
                        uint off_2 = slotToIndex_0(_t_0 * 64U + i_7) - _S28 + (&kernelContext_3)->_binPhase_0;

#line 1884
                        if(_S32 >= int(0))
                        {

#line 1884
                            j_2 = off_2 >> uint(_S32);

#line 1884
                        }
                        else
                        {

#line 1884
                            uint _S99 = off_2 / _S31;

#line 1884
                            j_2 = _S99;

#line 1884
                        }

#line 1884
                        float rx_2 = r_5[i_7].x;

#line 1884
                        float ry_2 = r_5[i_7].y;

#line 1884
                        if((as_type<uint>((rx_2 * rx_2 + ry_2 * ry_2))) == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2])
                        {

#line 1884
                            if(_S98)
                            {

#line 1884
                                s2_0 = s1_0 | bit_1;

#line 1884
                                m3_0 = m2_0;

#line 1884
                            }
                            else
                            {

#line 1884
                                uint candHi_0 = m2_0 | bit_1;

#line 1884
                                s2_0 = s1_0;

#line 1884
                                m3_0 = candHi_0;

#line 1884
                            }

#line 1884
                        }
                        else
                        {

#line 1884
                            s2_0 = s1_0;

#line 1884
                            m3_0 = m2_0;

#line 1884
                        }

#line 1884
                    }
                    else
                    {

#line 1884
                        s2_0 = s1_0;

#line 1884
                        m3_0 = m2_0;

#line 1884
                    }

#line 1884
                    i_7 = i_7 + 1U;

#line 1884
                    s1_0 = s2_0;

#line 1884
                    m2_0 = m3_0;

#line 1884
                }

#line 1884
                s2_0 = s1_0;

#line 1884
                m3_0 = m2_0;

#line 1884
            }
            else
            {

#line 1884
                s2_0 = 0U;

#line 1884
                m3_0 = 0U;

#line 1884
            }

#line 1884
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
            j_2 = _t_0;

#line 1884
            for(;;)
            {

#line 1884
                if(j_2 < _S33)
                {
                }
                else
                {

#line 1884
                    break;
                }

#line 1884
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2] = 4294967295U;

#line 1884
                j_2 = j_2 + 1024U;

#line 1884
            }

#line 1884
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
            bool _S100 = (s2_0 | m3_0) != 0U;

#line 1884
            if(_S100)
            {

#line 1884
                i_7 = 0U;

#line 1884
                for(;;)
                {

#line 1884
                    if(i_7 < 64U)
                    {
                    }
                    else
                    {

#line 1884
                        break;
                    }

#line 1884
                    uint bit_2 = 1U << (i_7 & 31U);

#line 1884
                    if(i_7 < 32U)
                    {

#line 1884
                        isCand_0 = (s2_0 & bit_2) != 0U;

#line 1884
                    }
                    else
                    {

#line 1884
                        isCand_0 = (m3_0 & bit_2) != 0U;

#line 1884
                    }

#line 1884
                    if(isCand_0)
                    {

#line 1884
                        uint _S101 = _t_0 * 64U + i_7;

#line 1884
                        uint off_3 = slotToIndex_0(_S101) - _S28 + (&kernelContext_3)->_binPhase_0;

#line 1884
                        if(_S32 >= int(0))
                        {

#line 1884
                            j_2 = off_3 >> uint(_S32);

#line 1884
                        }
                        else
                        {

#line 1884
                            uint _S102 = off_3 / _S31;

#line 1884
                            j_2 = _S102;

#line 1884
                        }

#line 1884
                        uint _S103 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2])), _S101, memory_order_relaxed);

#line 1884
                    }

#line 1884
                    i_7 = i_7 + 1U;

#line 1884
                }

#line 1884
            }

#line 1884
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
            if(_S100)
            {

#line 1884
                i_7 = 0U;

#line 1884
                for(;;)
                {

#line 1884
                    if(i_7 < 64U)
                    {
                    }
                    else
                    {

#line 1884
                        break;
                    }

#line 1884
                    uint bit_3 = 1U << (i_7 & 31U);

#line 1884
                    if(i_7 < 32U)
                    {

#line 1884
                        isCand_0 = (s2_0 & bit_3) != 0U;

#line 1884
                    }
                    else
                    {

#line 1884
                        isCand_0 = (m3_0 & bit_3) != 0U;

#line 1884
                    }

#line 1884
                    if(isCand_0)
                    {

#line 1884
                        uint _S104 = _t_0 * 64U + i_7;

#line 1884
                        uint idx_3 = slotToIndex_0(_S104);

#line 1884
                        uint off_4 = idx_3 - _S28 + (&kernelContext_3)->_binPhase_0;

#line 1884
                        if(_S32 >= int(0))
                        {

#line 1884
                            j_2 = off_4 >> uint(_S32);

#line 1884
                        }
                        else
                        {

#line 1884
                            uint _S105 = off_4 / _S31;

#line 1884
                            j_2 = _S105;

#line 1884
                        }

#line 1884
                        if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2]) == _S104)
                        {

#line 1884
                            uint o_2 = _pr_0 * _S33 + j_2;

#line 1884
                            *((&kernelContext_3)->entryPointParams_peakIdx_0+o_2) = int(idx_3);

#line 1884
                            *((&kernelContext_3)->entryPointParams_peakVal_0+o_2) = packed_float2(float2(r_5[i_7].x, r_5[i_7].y)) ;

#line 1884
                        }

#line 1884
                    }

#line 1884
                    i_7 = i_7 + 1U;

#line 1884
                }

#line 1884
            }

#line 1884
            j_2 = _t_0;

#line 1884
            for(;;)
            {

#line 1884
                if(j_2 < _S33)
                {
                }
                else
                {

#line 1884
                    break;
                }

#line 1884
                if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2]) == 4294967295U)
                {

#line 1884
                    uint _S106 = _pr_0 * _S33 + j_2;

#line 1884
                    *((&kernelContext_3)->entryPointParams_peakIdx_0+_S106) = int(-1);

#line 1884
                    *((&kernelContext_3)->entryPointParams_peakVal_0+_S106) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1884
                }

#line 1884
                j_2 = j_2 + 1024U;

#line 1884
            }

#line 1884
        }

#line 1884
        break;
    }

#line 1890
    return;
}
