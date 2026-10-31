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


#line 311 "mm_32768_fusedTierB_lds32.slang"
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

#line 90 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 230 "mm_32768_fusedTierB_lds32.slang"
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


#line 173 "mm_32768_fusedTierB_lds32.slang"
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


#line 74 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S10 = ((MF_ACCURATE_TRIG));

#line 77
    return _S10;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S11 = mfAccurateTrigFlag_0();

#line 103
    if(_S11 == 0U)
    {

#line 104
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S12 = float(quadrant_0);
    float x_0 = angle_0 - _S12 * 1.57079625129699707f - _S12 * 7.54978941586159635e-08f;
    float z_0 = x_0 * x_0;
    float c_0 = 1.0f + z_0 * (-0.5f + z_0 * (0.0416666679084301f + z_0 * (-0.00138888892251998f + z_0 * (0.00002480158764229f + z_0 * -2.75573199814971304e-07f))));

    float s_0 = x_0 * (1.0f + z_0 * (-0.1666666716337204f + z_0 * (0.00833333376795053f + z_0 * (-0.0001984127011383f + z_0 * (2.75573188446287531e-06f + z_0 * -2.50521079436794025e-08f)))));


    switch(quadrant_0 & int(3))
    {
    case int(1):
        {

#line 117
            return float2(- s_0, c_0);
        }
    case int(2):
        {

#line 118
            return float2(- c_0, - s_0);
        }
    case int(3):
        {

#line 119
            return float2(s_0, - c_0);
        }
    default:
        {

#line 120
            return float2(c_0, s_0);
        }
    }

#line 120
}


#line 322 "mm_32768_fusedTierB_lds32.slang"
float2 cmul_0(float2 a_1, float2 b_2)
{

#line 322
    float _S13 = a_1.x;

#line 322
    float _S14 = b_2.x;

#line 322
    float _S15 = a_1.y;

#line 322
    float _S16 = b_2.y;

#line 322
    return float2(_S13 * _S14 - _S15 * _S16, _S13 * _S16 + _S15 * _S14);
}


#line 582
void r4_0(float2 thread* a_2, float2 thread* b_3, float2 thread* c_1, float2 thread* d_1)
{
    float2 t0_0 = *a_2 + *c_1;

#line 584
    float2 t1_0 = *a_2 - *c_1;

#line 584
    float2 t2_0 = *b_3 + *d_1;

#line 584
    float2 t3_0 = *b_3 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_2 = t0_0 + t2_0;

#line 586
    *b_3 = t1_0 + j3_0;

#line 586
    *c_1 = t0_0 - t2_0;

#line 586
    *d_1 = t1_0 - j3_0;
    return;
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
        uint _S17 = 4U * k2_0;

#line 630
        r4_0(&(*r_0)[_S17], &(*r_0)[_S17 + 1U], &(*r_0)[_S17 + 2U], &(*r_0)[_S17 + 3U]);

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


#line 664
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 666
    thread array<float2, int(16)> v_0;

#line 666
    uint j_0 = 0U;
    for(;;)
    {

#line 667
        if(j_0 < 16U)
        {
        }
        else
        {

#line 667
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        float2 _S18 = (*r_1)[j_0] - (*r_1)[j_0 + 16U];

#line 671
        float2 _S19 = mfTwiddle_0(6.28318548202514648f * float(j_0) / 32.0f);

#line 671
        v_0[j_0] = cmul_0(_S18, _S19);

#line 667
        j_0 = j_0 + 1U;

#line 667
    }

#line 673
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 674
    uint k_0 = 0U;
    for(;;)
    {

#line 675
        if(k_0 < 16U)
        {
        }
        else
        {

#line 675
            break;
        }

#line 675
        uint _S20 = 2U * k_0;

#line 675
        (*r_1)[_S20] = u_0[k_0];

#line 675
        (*r_1)[_S20 + 1U] = v_0[k_0];

#line 675
        k_0 = k_0 + 1U;

#line 675
    }
    return;
}


#line 703
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 324
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S21 = max(TB_0, 1U);

#line 326
    uint j_1 = d_2 / _S21;

#line 326
    uint m_0 = d_2 % _S21;

#line 326
    uint _S22;
    if(TB_0 <= 32U)
    {

#line 327
        _S22 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 327
    }
    else
    {

#line 327
        _S22 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 327
    }

#line 327
    return _S22;
}


#line 311
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_1)
{

#line 311
    uint _S23 = 2U * i_1;

#line 311
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S23] = (as_type<uint>((v_1.x)));

#line 311
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S23 + 1U] = (as_type<uint>((v_1.y)));

#line 311
    return;
}


#line 312
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_2)
{

#line 312
    uint _S24 = 2U * i_2;

#line 312
    return float2((as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S24]))), (as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S24 + 1U]))));
}


#line 721
void innermost_0(array<float2, int(32)> thread* r_3)
{

    dft32_0(r_3);

#line 733
    return;
}


#line 868
uint lgOf_0(uint i_3)
{

#line 868
    uint _S25;

#line 868
    if(i_3 < 2U)
    {

#line 868
        _S25 = 5U;

#line 868
    }
    else
    {

#line 868
        if(i_3 == 2U)
        {

#line 868
            _S25 = 5U;

#line 868
        }
        else
        {

#line 868
            _S25 = 1U;

#line 868
        }

#line 868
    }

#line 868
    return _S25;
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
    uint _S26;

#line 1765
    float cr_0;

#line 1765
    float ci_0;

#line 1765
    uint _S27;

#line 1765
    uint z_1;

#line 1765
    uint _S28;

#line 1765
    uint c_2;

#line 1765
    uint d_3;

#line 1765
    uint j_2;

#line 1765
    bool isCand_0;

#line 1765
    uint b_4;

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
    threadgroup array<uint, int(8192)> stg_1;

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
    uint _S29 = _pr_0 / entryPointParams_1->ntmpl_0;

#line 1793
    rowWindow_0(_S29, &_ws_0, &_we_0, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);
    uint _S30 = _ws_0;

#line 1794
    uint _S31 = _we_0;

#line 1794
    uint _S32 = entryPointParams_1->ntmpl_0;

#line 1794
    uint _S33 = (&kernelContext_3)->entryPointParams_0->binsize_0;

#line 1794
    int _S34 = (&kernelContext_3)->entryPointParams_0->binShift_0;

#line 1794
    uint _S35 = (&kernelContext_3)->entryPointParams_0->nbins_0;

#line 1794
    uint _S36 = (&kernelContext_3)->entryPointParams_0->thrBits_0;

#line 1794
    for(;;)
    {

#line 1794
        (&kernelContext_3)->_tid_0 = _t_0;

#line 1794
        uint _S37 = _pr_0 / _S32;

#line 1794
        uint _S38 = _pr_0 % _S32;

#line 1794
        thread array<float2, int(32)> r_4;

#line 1794
        uint n2_0 = 0U;

#line 1794
        for(;;)
        {

#line 1794
            if(n2_0 < 32U)
            {
            }
            else
            {

#line 1794
                break;
            }

#line 1794
            uint idx_0 = _t_0 + 1024U * n2_0;

#line 1794
            uint _S39 = mfDataStrideFlag_0();

#line 1794
            if(_S39 != 0U)
            {

#line 1794
                uint _S40 = mfDataStrideFlag_0();

#line 1794
                k2_1 = _S40;

#line 1794
            }
            else
            {

#line 1794
                k2_1 = 32768U;

#line 1794
            }

#line 1794
            r_4[n2_0] = cmulConj_0(cload_0((&kernelContext_3)->entryPointParams_data_0, _S37 * k2_1 + idx_0), cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S38 * 32768U + idx_0));

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
                        uint lgTB_0 = firstbithigh_0(1024U);

#line 1794
                        _S26 = lgTB_0;

#line 1794
                        uint lgLn_0 = firstbithigh_0(32768U);

#line 1794
                        uint blk_1 = _t_0 >> lgTB_0;

#line 1794
                        uint lane_1 = _t_0 & 1023U;

#line 1794
                        dftR_0(&r_4);

#line 1794
                        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 32768.0f);

#line 1794
                        float _S41 = tw_0.x;

#line 1794
                        float _S42 = tw_0.y;

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
                            if(k2_1 < 32U)
                            {
                            }
                            else
                            {

#line 1794
                                break;
                            }

#line 1794
                            r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 1794
                            float nr_0 = cr_0 * _S41 - ci_0 * _S42;

#line 1794
                            float _S43 = cr_0 * _S42 + ci_0 * _S41;

#line 1794
                            k2_1 = k2_1 + 1U;

#line 1794
                            cr_0 = nr_0;

#line 1794
                            ci_0 = _S43;

#line 1794
                        }

#line 1794
                        uint per_1 = 32U / max(1024U, 1U);

#line 1794
                        uint _S44 = max(32U, 1U);

#line 1794
                        _S27 = _S44;

#line 1794
                        uint blk2_1 = _t_0 / _S44;

#line 1794
                        uint lane2_1 = _t_0 % _S44;

#line 1794
                        for(;;)
                        {

#line 1794
                            thread array<float2, int(32)> out_0;

#line 1794
                            z_1 = 0U;

#line 1794
                            for(;;)
                            {

#line 1794
                                if(z_1 < 32U)
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
                            _S28 = spanMask_0;

#line 1794
                            uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1794
                            uint p0_0 = computeWant_0(0U, 1024U, 32768U, blk_1, lane_1, per_1, _S44, 1024U, blk2_1, lane2_1);

#line 1794
                            uint _S45 = p0_0 & lenMask_0;

#line 1794
                            uint _S46 = _S45 >> lgTB_0;

#line 1794
                            uint _S47 = _S46 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S45 & spanMask_0);

#line 1794
                            c_2 = 0U;

#line 1794
                            for(;;)
                            {

#line 1794
                                if(c_2 < 8U)
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
                                    if(j_2 < 4U)
                                    {
                                    }
                                    else
                                    {

#line 1794
                                        break;
                                    }

#line 1794
                                    stgPut_0(j_2 * 1024U + (&kernelContext_3)->_tid_0, r_4[c_2 * 4U + j_2], &kernelContext_3);

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
                                    if(d_3 < 32U)
                                    {
                                    }
                                    else
                                    {

#line 1794
                                        break;
                                    }

#line 1794
                                    uint pz_0 = computeWant_0(d_3, 1024U, 32768U, 0U, 0U, per_1, _S44, 1024U, 0U, 0U);

#line 1794
                                    uint _S48 = pz_0 & lenMask_0;

#line 1794
                                    uint iz_0 = _S48 >> lgTB_0;

#line 1794
                                    uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S48 & spanMask_0);

#line 1794
                                    uint i_4 = _S46 + iz_0;

#line 1794
                                    uint _S49 = c_2 * 4U;

#line 1794
                                    if(i_4 >= _S49)
                                    {

#line 1794
                                        isCand_0 = i_4 < ((c_2 + 1U) * 4U);

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
                                        float2 _S50 = stgGet_0(_S47 + az_0 - _S49 * 1024U, &kernelContext_3);

#line 1794
                                        out_0[d_3] = _S50;

#line 1794
                                    }

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
                                if(d_3 < 32U)
                                {
                                }
                                else
                                {

#line 1794
                                    break;
                                }

#line 1794
                                r_4[d_3] = out_0[d_3];

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
                        uint lgTB_1 = firstbithigh_0(32U);

#line 1794
                        uint blk_2 = _t_0 >> lgTB_1;

#line 1794
                        uint lane_2 = _t_0 & 31U;

#line 1794
                        dftR_0(&r_4);

#line 1794
                        float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 1794
                        float _S51 = tw_1.x;

#line 1794
                        float _S52 = tw_1.y;

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
                            if(k2_1 < 32U)
                            {
                            }
                            else
                            {

#line 1794
                                break;
                            }

#line 1794
                            r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 1794
                            float nr_1 = cr_0 * _S51 - ci_0 * _S52;

#line 1794
                            float _S53 = cr_0 * _S52 + ci_0 * _S51;

#line 1794
                            k2_1 = k2_1 + 1U;

#line 1794
                            cr_0 = nr_1;

#line 1794
                            ci_0 = _S53;

#line 1794
                        }

#line 1794
                        uint per_2 = 32U / _S27;

#line 1794
                        uint _S54 = max(1U, 1U);

#line 1794
                        uint blk2_2 = _t_0 / _S54;

#line 1794
                        uint lane2_2 = _t_0 % _S54;

#line 1794
                        for(;;)
                        {

#line 1794
                            thread array<float2, int(32)> out_1;

#line 1794
                            z_1 = 0U;

#line 1794
                            for(;;)
                            {

#line 1794
                                if(z_1 < 32U)
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
                            uint p0_1 = computeWant_0(0U, 32U, 1024U, blk_2, lane_2, per_2, _S54, 32U, blk2_2, lane2_2);

#line 1794
                            uint _S55 = p0_1 & _S28;

#line 1794
                            uint _S56 = _S55 >> lgTB_1;

#line 1794
                            uint _S57 = _S56 * 1024U + ((p0_1 >> _S26) << lgTB_1) + (_S55 & spanMask_1);

#line 1794
                            c_2 = 0U;

#line 1794
                            for(;;)
                            {

#line 1794
                                if(c_2 < 8U)
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
                                    if(j_2 < 4U)
                                    {
                                    }
                                    else
                                    {

#line 1794
                                        break;
                                    }

#line 1794
                                    stgPut_0(j_2 * 1024U + (&kernelContext_3)->_tid_0, r_4[c_2 * 4U + j_2], &kernelContext_3);

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
                                    if(d_3 < 32U)
                                    {
                                    }
                                    else
                                    {

#line 1794
                                        break;
                                    }

#line 1794
                                    uint pz_1 = computeWant_0(d_3, 32U, 1024U, 0U, 0U, per_2, _S54, 32U, 0U, 0U);

#line 1794
                                    uint _S58 = pz_1 & _S28;

#line 1794
                                    uint iz_1 = _S58 >> lgTB_1;

#line 1794
                                    uint az_1 = iz_1 * 1024U + ((pz_1 >> _S26) << lgTB_1) + (_S58 & spanMask_1);

#line 1794
                                    uint i_5 = _S56 + iz_1;

#line 1794
                                    uint _S59 = c_2 * 4U;

#line 1794
                                    if(i_5 >= _S59)
                                    {

#line 1794
                                        isCand_0 = i_5 < ((c_2 + 1U) * 4U);

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
                                        float2 _S60 = stgGet_0(_S57 + az_1 - _S59 * 1024U, &kernelContext_3);

#line 1794
                                        out_1[d_3] = _S60;

#line 1794
                                    }

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
                                if(d_3 < 32U)
                                {
                                }
                                else
                                {

#line 1794
                                    break;
                                }

#line 1794
                                r_4[d_3] = out_1[d_3];

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
            innermost_0(&r_4);

#line 1794
            break;
        }

#line 1794
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
        uint i_6;

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
        if(_S35 <= 4U)
        {

#line 1794
            if(_t_0 < 4U)
            {

#line 1794
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + _t_0] = _S36;

#line 1794
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _t_0] = 4294967295U;

#line 1794
            }

#line 1794
            float2 _S61 = float2(0.0f, 0.0f);

#line 1794
            i_6 = 0U;

#line 1794
            j_2 = _S36;

#line 1794
            s0_1 = 4294967295U;

#line 1794
            float2 v0_0 = _S61;

#line 1794
            m1_1 = _S36;

#line 1794
            s1_0 = 4294967295U;

#line 1794
            float2 v1_0 = _S61;

#line 1794
            m2_0 = _S36;

#line 1794
            s2_0 = 4294967295U;

#line 1794
            float2 v2_0 = _S61;

#line 1794
            m3_0 = _S36;

#line 1794
            uint s3_0 = 4294967295U;

#line 1794
            float2 v3_0 = _S61;

#line 1794
            for(;;)
            {

#line 1794
                if(i_6 < 32U)
                {
                }
                else
                {

#line 1794
                    break;
                }

#line 1794
                uint slot_1 = _t_0 * 32U + i_6;

#line 1794
                uint idx_1 = slotToIndex_0(slot_1);

#line 1794
                if(idx_1 >= _S30)
                {

#line 1794
                    isCand_0 = idx_1 < _S31;

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
                    float rx_0 = r_4[i_6].x;

#line 1794
                    float ry_0 = r_4[i_6].y;

#line 1794
                    uint mag_0 = (as_type<uint>((rx_0 * rx_0 + ry_0 * ry_0)));

#line 1794
                    uint off_0 = idx_1 - _S30 + (&kernelContext_3)->_binPhase_0;

#line 1794
                    if(_S35 == 1U)
                    {

#line 1794
                        b_4 = 0U;

#line 1794
                    }
                    else
                    {

#line 1794
                        if(_S34 >= int(0))
                        {

#line 1794
                            n2_0 = off_0 >> uint(_S34);

#line 1794
                        }
                        else
                        {

#line 1794
                            uint _S62 = off_0 / _S33;

#line 1794
                            n2_0 = _S62;

#line 1794
                        }

#line 1794
                        b_4 = n2_0;

#line 1794
                    }

#line 1794
                    bool _S63;

#line 1794
                    if(b_4 == 0U)
                    {

#line 1794
                        _S63 = mag_0 > j_2;

#line 1794
                    }
                    else
                    {

#line 1794
                        _S63 = false;

#line 1794
                    }

#line 1794
                    float2 v0_1;

#line 1794
                    if(_S63)
                    {

#line 1794
                        float2 _S64 = float2(rx_0, ry_0);

#line 1794
                        m0_0 = mag_0;

#line 1794
                        s0_0 = slot_1;

#line 1794
                        v0_1 = _S64;

#line 1794
                    }
                    else
                    {

#line 1794
                        m0_0 = j_2;

#line 1794
                        s0_0 = s0_1;

#line 1794
                        v0_1 = v0_0;

#line 1794
                    }

#line 1794
                    bool _S65;

#line 1794
                    if(_S35 >= 2U)
                    {

#line 1794
                        _S65 = b_4 == 1U;

#line 1794
                    }
                    else
                    {

#line 1794
                        _S65 = false;

#line 1794
                    }

#line 1794
                    bool _S66;

#line 1794
                    if(_S65)
                    {

#line 1794
                        _S66 = mag_0 > m1_1;

#line 1794
                    }
                    else
                    {

#line 1794
                        _S66 = false;

#line 1794
                    }

#line 1794
                    uint s1_1;

#line 1794
                    float2 v1_1;

#line 1794
                    if(_S66)
                    {

#line 1794
                        float2 _S67 = float2(rx_0, ry_0);

#line 1794
                        m1_0 = mag_0;

#line 1794
                        s1_1 = slot_1;

#line 1794
                        v1_1 = _S67;

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
                    bool _S68;

#line 1794
                    if(_S35 >= 3U)
                    {

#line 1794
                        _S68 = b_4 == 2U;

#line 1794
                    }
                    else
                    {

#line 1794
                        _S68 = false;

#line 1794
                    }

#line 1794
                    bool _S69;

#line 1794
                    if(_S68)
                    {

#line 1794
                        _S69 = mag_0 > m2_0;

#line 1794
                    }
                    else
                    {

#line 1794
                        _S69 = false;

#line 1794
                    }

#line 1794
                    uint m2_1;

#line 1794
                    uint s2_1;

#line 1794
                    float2 v2_1;

#line 1794
                    if(_S69)
                    {

#line 1794
                        float2 _S70 = float2(rx_0, ry_0);

#line 1794
                        m2_1 = mag_0;

#line 1794
                        s2_1 = slot_1;

#line 1794
                        v2_1 = _S70;

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
                    bool _S71;

#line 1794
                    if(_S35 >= 4U)
                    {

#line 1794
                        _S71 = b_4 == 3U;

#line 1794
                    }
                    else
                    {

#line 1794
                        _S71 = false;

#line 1794
                    }

#line 1794
                    bool _S72;

#line 1794
                    if(_S71)
                    {

#line 1794
                        _S72 = mag_0 > m3_0;

#line 1794
                    }
                    else
                    {

#line 1794
                        _S72 = false;

#line 1794
                    }

#line 1794
                    uint m3_1;

#line 1794
                    uint s3_1;

#line 1794
                    float2 v3_1;

#line 1794
                    if(_S72)
                    {

#line 1794
                        float2 _S73 = float2(rx_0, ry_0);

#line 1794
                        m3_1 = mag_0;

#line 1794
                        s3_1 = slot_1;

#line 1794
                        v3_1 = _S73;

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
                    j_2 = m0_0;

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
                i_6 = i_6 + 1U;

#line 1794
            }

#line 1794
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
            uint wm0_0 = simd_max(j_2);

#line 1794
            bool _S74 = simd_is_first();

#line 1794
            if(_S74)
            {

#line 1794
                isCand_0 = wm0_0 > _S36;

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
                uint _S75 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), wm0_0, memory_order_relaxed);

#line 1794
            }

#line 1794
            bool _S76 = _S35 >= 2U;

#line 1794
            if(_S76)
            {

#line 1794
                uint wm1_0 = simd_max(m1_1);

#line 1794
                bool _S77 = simd_is_first();

#line 1794
                if(_S77)
                {

#line 1794
                    isCand_0 = wm1_0 > _S36;

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
                    uint _S78 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), wm1_0, memory_order_relaxed);

#line 1794
                }

#line 1794
            }

#line 1794
            bool _S79 = _S35 >= 3U;

#line 1794
            if(_S79)
            {

#line 1794
                uint wm2_0 = simd_max(m2_0);

#line 1794
                bool _S80 = simd_is_first();

#line 1794
                if(_S80)
                {

#line 1794
                    isCand_0 = wm2_0 > _S36;

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
                    uint _S81 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U])), wm2_0, memory_order_relaxed);

#line 1794
                }

#line 1794
            }

#line 1794
            bool _S82 = _S35 >= 4U;

#line 1794
            if(_S82)
            {

#line 1794
                uint wm3_0 = simd_max(m3_0);

#line 1794
                bool _S83 = simd_is_first();

#line 1794
                if(_S83)
                {

#line 1794
                    isCand_0 = wm3_0 > _S36;

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
                    uint _S84 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U])), wm3_0, memory_order_relaxed);

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
                isCand_0 = j_2 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0];

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
                b_4 = s0_1;

#line 1794
            }
            else
            {

#line 1794
                b_4 = 4294967295U;

#line 1794
            }

#line 1794
            if(_S76)
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
            if(_S79)
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
            if(_S82)
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
            uint ww0_0 = simd_min(b_4);

#line 1794
            bool _S85 = simd_is_first();

#line 1794
            if(_S85)
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
                uint _S86 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U])), ww0_0, memory_order_relaxed);

#line 1794
            }

#line 1794
            if(_S76)
            {

#line 1794
                uint ww1_0 = simd_min(m0_0);

#line 1794
                bool _S87 = simd_is_first();

#line 1794
                if(_S87)
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
                    uint _S88 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U])), ww1_0, memory_order_relaxed);

#line 1794
                }

#line 1794
            }

#line 1794
            if(_S79)
            {

#line 1794
                uint ww2_0 = simd_min(s0_0);

#line 1794
                bool _S89 = simd_is_first();

#line 1794
                if(_S89)
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
                    uint _S90 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U])), ww2_0, memory_order_relaxed);

#line 1794
                }

#line 1794
            }

#line 1794
            if(_S82)
            {

#line 1794
                uint ww3_0 = simd_min(m1_0);

#line 1794
                bool _S91 = simd_is_first();

#line 1794
                if(_S91)
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
                    uint _S92 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U])), ww3_0, memory_order_relaxed);

#line 1794
                }

#line 1794
            }

#line 1794
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
            uint baseOut_0 = _pr_0 * _S35;

#line 1794
            if(b_4 != 4294967295U)
            {

#line 1794
                isCand_0 = b_4 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U];

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
                *((&kernelContext_3)->entryPointParams_peakIdx_0+baseOut_0) = int(slotToIndex_0(b_4));

#line 1794
                *((&kernelContext_3)->entryPointParams_peakVal_0+baseOut_0) = packed_float2(v0_0) ;

#line 1794
            }

#line 1794
            if(_S76)
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
                uint _S93 = baseOut_0 + 1U;

#line 1794
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S93) = int(slotToIndex_0(m0_0));

#line 1794
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S93) = packed_float2(v1_0) ;

#line 1794
            }

#line 1794
            if(_S79)
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
                uint _S94 = baseOut_0 + 2U;

#line 1794
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S94) = int(slotToIndex_0(s0_0));

#line 1794
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S94) = packed_float2(v2_0) ;

#line 1794
            }

#line 1794
            if(_S82)
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
                uint _S95 = baseOut_0 + 3U;

#line 1794
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S95) = int(slotToIndex_0(m1_0));

#line 1794
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S95) = packed_float2(v3_0) ;

#line 1794
            }

#line 1794
            if(_t_0 < _S35)
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
                uint _S96 = baseOut_0 + _t_0;

#line 1794
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S96) = int(-1);

#line 1794
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S96) = packed_float2(_S61) ;

#line 1794
            }

#line 1794
        }
        else
        {

#line 1794
            j_2 = _t_0;

#line 1794
            for(;;)
            {

#line 1794
                if(j_2 < _S35)
                {
                }
                else
                {

#line 1794
                    break;
                }

#line 1794
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2] = _S36;

#line 1794
                j_2 = j_2 + 1024U;

#line 1794
            }

#line 1794
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
            i_6 = 0U;

#line 1794
            s0_1 = 0U;

#line 1794
            m1_1 = 0U;

#line 1794
            for(;;)
            {

#line 1794
                bool _S97 = i_6 < 32U;

#line 1794
                if(_S97)
                {
                }
                else
                {

#line 1794
                    break;
                }

#line 1794
                uint idx_2 = slotToIndex_0(_t_0 * 32U + i_6);

#line 1794
                if(idx_2 >= _S30)
                {

#line 1794
                    isCand_0 = idx_2 < _S31;

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
                    float rx_1 = r_4[i_6].x;

#line 1794
                    float ry_1 = r_4[i_6].y;

#line 1794
                    uint mag_1 = (as_type<uint>((rx_1 * rx_1 + ry_1 * ry_1)));

#line 1794
                    if(mag_1 > _S36)
                    {

#line 1794
                        uint off_1 = idx_2 - _S30 + (&kernelContext_3)->_binPhase_0;

#line 1794
                        if(_S34 >= int(0))
                        {

#line 1794
                            j_2 = off_1 >> uint(_S34);

#line 1794
                        }
                        else
                        {

#line 1794
                            uint _S98 = off_1 / _S33;

#line 1794
                            j_2 = _S98;

#line 1794
                        }

#line 1794
                        uint _S99 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2])), mag_1, memory_order_relaxed);

#line 1794
                        uint bit_0 = 1U << (i_6 & 31U);

#line 1794
                        if(_S97)
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
                i_6 = i_6 + 1U;

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
                i_6 = 0U;

#line 1794
                s1_0 = 0U;

#line 1794
                m2_0 = 0U;

#line 1794
                for(;;)
                {

#line 1794
                    bool _S100 = i_6 < 32U;

#line 1794
                    if(_S100)
                    {
                    }
                    else
                    {

#line 1794
                        break;
                    }

#line 1794
                    uint bit_1 = 1U << (i_6 & 31U);

#line 1794
                    if(_S100)
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
                        uint off_2 = slotToIndex_0(_t_0 * 32U + i_6) - _S30 + (&kernelContext_3)->_binPhase_0;

#line 1794
                        if(_S34 >= int(0))
                        {

#line 1794
                            j_2 = off_2 >> uint(_S34);

#line 1794
                        }
                        else
                        {

#line 1794
                            uint _S101 = off_2 / _S33;

#line 1794
                            j_2 = _S101;

#line 1794
                        }

#line 1794
                        float rx_2 = r_4[i_6].x;

#line 1794
                        float ry_2 = r_4[i_6].y;

#line 1794
                        if((as_type<uint>((rx_2 * rx_2 + ry_2 * ry_2))) == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2])
                        {

#line 1794
                            if(_S100)
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
                    i_6 = i_6 + 1U;

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
            j_2 = _t_0;

#line 1794
            for(;;)
            {

#line 1794
                if(j_2 < _S35)
                {
                }
                else
                {

#line 1794
                    break;
                }

#line 1794
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2] = 4294967295U;

#line 1794
                j_2 = j_2 + 1024U;

#line 1794
            }

#line 1794
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
            bool _S102 = (s2_0 | m3_0) != 0U;

#line 1794
            if(_S102)
            {

#line 1794
                i_6 = 0U;

#line 1794
                for(;;)
                {

#line 1794
                    bool _S103 = i_6 < 32U;

#line 1794
                    if(_S103)
                    {
                    }
                    else
                    {

#line 1794
                        break;
                    }

#line 1794
                    uint bit_2 = 1U << (i_6 & 31U);

#line 1794
                    if(_S103)
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
                        uint _S104 = _t_0 * 32U + i_6;

#line 1794
                        uint off_3 = slotToIndex_0(_S104) - _S30 + (&kernelContext_3)->_binPhase_0;

#line 1794
                        if(_S34 >= int(0))
                        {

#line 1794
                            j_2 = off_3 >> uint(_S34);

#line 1794
                        }
                        else
                        {

#line 1794
                            uint _S105 = off_3 / _S33;

#line 1794
                            j_2 = _S105;

#line 1794
                        }

#line 1794
                        uint _S106 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2])), _S104, memory_order_relaxed);

#line 1794
                    }

#line 1794
                    i_6 = i_6 + 1U;

#line 1794
                }

#line 1794
            }

#line 1794
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1794
            if(_S102)
            {

#line 1794
                i_6 = 0U;

#line 1794
                for(;;)
                {

#line 1794
                    bool _S107 = i_6 < 32U;

#line 1794
                    if(_S107)
                    {
                    }
                    else
                    {

#line 1794
                        break;
                    }

#line 1794
                    uint bit_3 = 1U << (i_6 & 31U);

#line 1794
                    if(_S107)
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
                        uint _S108 = _t_0 * 32U + i_6;

#line 1794
                        uint idx_3 = slotToIndex_0(_S108);

#line 1794
                        uint off_4 = idx_3 - _S30 + (&kernelContext_3)->_binPhase_0;

#line 1794
                        if(_S34 >= int(0))
                        {

#line 1794
                            j_2 = off_4 >> uint(_S34);

#line 1794
                        }
                        else
                        {

#line 1794
                            uint _S109 = off_4 / _S33;

#line 1794
                            j_2 = _S109;

#line 1794
                        }

#line 1794
                        if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2]) == _S108)
                        {

#line 1794
                            uint o_0 = _pr_0 * _S35 + j_2;

#line 1794
                            *((&kernelContext_3)->entryPointParams_peakIdx_0+o_0) = int(idx_3);

#line 1794
                            *((&kernelContext_3)->entryPointParams_peakVal_0+o_0) = packed_float2(float2(r_4[i_6].x, r_4[i_6].y)) ;

#line 1794
                        }

#line 1794
                    }

#line 1794
                    i_6 = i_6 + 1U;

#line 1794
                }

#line 1794
            }

#line 1794
            j_2 = _t_0;

#line 1794
            for(;;)
            {

#line 1794
                if(j_2 < _S35)
                {
                }
                else
                {

#line 1794
                    break;
                }

#line 1794
                if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2]) == 4294967295U)
                {

#line 1794
                    uint _S110 = _pr_0 * _S35 + j_2;

#line 1794
                    *((&kernelContext_3)->entryPointParams_peakIdx_0+_S110) = int(-1);

#line 1794
                    *((&kernelContext_3)->entryPointParams_peakVal_0+_S110) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1794
                }

#line 1794
                j_2 = j_2 + 1024U;

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
