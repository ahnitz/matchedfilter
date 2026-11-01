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


#line 317 "mm_32768_fusedTierB.slang"
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
    array<uint, int(16384)> threadgroup* stg_0;
};


#line 227
void rowWindow_0(uint d_0, uint thread* winStart_1, uint thread* winEnd_1, uint device* rowWin_0, KernelContext_0 thread* kernelContext_0)
{
    kernelContext_0->_binPhase_0 = 0U;

#line 92 "twiddle.slang"
    uint _S3 = mfRowWindowsFlag_0();

#line 230 "mm_32768_fusedTierB.slang"
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


#line 173 "mm_32768_fusedTierB.slang"
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
    float c_0 = 1.0f + z_0 * (-0.5f + z_0 * (0.0416666679084301f + z_0 * (-0.00138888892251998f + z_0 * (0.00002480158764229f + z_0 * -2.75573199814971304e-07f))));

    float s_0 = x_0 * (1.0f + z_0 * (-0.1666666716337204f + z_0 * (0.00833333376795053f + z_0 * (-0.0001984127011383f + z_0 * (2.75573188446287531e-06f + z_0 * -2.50521079436794025e-08f)))));


    switch(quadrant_0 & int(3))
    {
    case int(1):
        {

#line 119
            return float2(- s_0, c_0);
        }
    case int(2):
        {

#line 120
            return float2(- c_0, - s_0);
        }
    case int(3):
        {

#line 121
            return float2(s_0, - c_0);
        }
    default:
        {

#line 122
            return float2(c_0, s_0);
        }
    }

#line 122
}


#line 328 "mm_32768_fusedTierB.slang"
float2 cmul_0(float2 a_1, float2 b_2)
{

#line 328
    float _S13 = a_1.x;

#line 328
    float _S14 = b_2.x;

#line 328
    float _S15 = a_1.y;

#line 328
    float _S16 = b_2.y;

#line 328
    return float2(_S13 * _S14 - _S15 * _S16, _S13 * _S16 + _S15 * _S14);
}


#line 613
void r4_0(float2 thread* a_2, float2 thread* b_3, float2 thread* c_1, float2 thread* d_1)
{
    float2 t0_0 = *a_2 + *c_1;

#line 615
    float2 t1_0 = *a_2 - *c_1;

#line 615
    float2 t2_0 = *b_3 + *d_1;

#line 615
    float2 t3_0 = *b_3 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_2 = t0_0 + t2_0;

#line 617
    *b_3 = t1_0 + j3_0;

#line 617
    *c_1 = t0_0 - t2_0;

#line 617
    *d_1 = t1_0 - j3_0;
    return;
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
        uint _S17 = 4U * k2_0;

#line 661
        r4_0(&(*r_0)[_S17], &(*r_0)[_S17 + 1U], &(*r_0)[_S17 + 2U], &(*r_0)[_S17 + 3U]);

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


#line 695
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 697
    thread array<float2, int(16)> v_0;

#line 697
    uint j_0 = 0U;
    for(;;)
    {

#line 698
        if(j_0 < 16U)
        {
        }
        else
        {

#line 698
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        float2 _S18 = (*r_1)[j_0] - (*r_1)[j_0 + 16U];

#line 702
        float2 _S19 = mfTwiddle_0(6.28318548202514648f * float(j_0) / 32.0f);

#line 702
        v_0[j_0] = cmul_0(_S18, _S19);

#line 698
        j_0 = j_0 + 1U;

#line 698
    }

#line 704
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 705
    uint k_0 = 0U;
    for(;;)
    {

#line 706
        if(k_0 < 16U)
        {
        }
        else
        {

#line 706
            break;
        }

#line 706
        uint _S20 = 2U * k_0;

#line 706
        (*r_1)[_S20] = u_0[k_0];

#line 706
        (*r_1)[_S20 + 1U] = v_0[k_0];

#line 706
        k_0 = k_0 + 1U;

#line 706
    }
    return;
}


#line 734
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 330
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S21 = max(TB_0, 1U);

#line 332
    uint j_1 = d_2 / _S21;

#line 332
    uint m_0 = d_2 % _S21;

#line 332
    uint _S22;
    if(TB_0 <= 32U)
    {

#line 333
        _S22 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 333
    }
    else
    {

#line 333
        _S22 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 333
    }

#line 333
    return _S22;
}


#line 317
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_1)
{

#line 317
    uint _S23 = 2U * i_1;

#line 317
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S23] = (as_type<uint>((v_1.x)));

#line 317
    (*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S23 + 1U] = (as_type<uint>((v_1.y)));

#line 317
    return;
}


#line 318
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_2)
{

#line 318
    uint _S24 = 2U * i_2;

#line 318
    return float2((as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S24]))), (as_type<float>(((*kernelContext_2->stg_0)[kernelContext_2->_stgBase_0 + _S24 + 1U]))));
}


#line 752
void innermost_0(array<float2, int(32)> thread* r_3)
{

    dft32_0(r_3);

#line 764
    return;
}


#line 880
uint lgOf_0(uint i_3)
{

#line 880
    uint _S25;

#line 880
    if(i_3 < 2U)
    {

#line 880
        _S25 = 5U;

#line 880
    }
    else
    {

#line 880
        if(i_3 == 2U)
        {

#line 880
            _S25 = 5U;

#line 880
        }
        else
        {

#line 880
            _S25 = 1U;

#line 880
        }

#line 880
    }

#line 880
    return _S25;
}


#line 882
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_1 = slot_0 >> lg_0;

#line 886
    uint lg_1 = lgOf_0(1U);

#line 886
    uint lg_2 = lgOf_0(0U);

#line 891
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | ((x_1 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1815
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_rowWin_1 [[buffer(5)]])
{

#line 1815
    uint k2_1;

#line 1815
    uint _S26;

#line 1815
    float cr_0;

#line 1815
    float ci_0;

#line 1815
    uint _S27;

#line 1815
    uint z_1;

#line 1815
    uint _S28;

#line 1815
    uint c_2;

#line 1815
    uint d_3;

#line 1815
    uint j_2;

#line 1815
    bool isCand_0;

#line 1815
    uint b_4;

#line 1815
    uint m0_0;

#line 1815
    uint s0_0;

#line 1815
    uint m1_0;

#line 1815
    thread KernelContext_0 kernelContext_3;

#line 1815
    (&kernelContext_3)->entryPointParams_0 = entryPointParams_1;

#line 1815
    (&kernelContext_3)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1815
    (&kernelContext_3)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1815
    (&kernelContext_3)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1815
    (&kernelContext_3)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1815
    (&kernelContext_3)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 1815
    threadgroup array<uint, int(16384)> stg_1;

#line 1815
    (&kernelContext_3)->stg_0 = &stg_1;

#line 1815
    (&kernelContext_3)->_binPhase_0 = 0U;

#line 1833
    uint _pr_0 = gid_0.x;

#line 1833
    uint _t_0 = lid_0.x;
    (&kernelContext_3)->_stgBase_0 = 0U;

#line 1843
    thread uint _ws_0 = entryPointParams_1->winStart_0;

#line 1843
    thread uint _we_0 = entryPointParams_1->winEnd_0;
    uint _S29 = _pr_0 / entryPointParams_1->ntmpl_0;

#line 1844
    rowWindow_0(_S29, &_ws_0, &_we_0, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);
    uint _S30 = _ws_0;

#line 1845
    uint _S31 = _we_0;

#line 1845
    uint _S32 = entryPointParams_1->ntmpl_0;

#line 1845
    uint _S33 = (&kernelContext_3)->entryPointParams_0->binsize_0;

#line 1845
    int _S34 = (&kernelContext_3)->entryPointParams_0->binShift_0;

#line 1845
    uint _S35 = (&kernelContext_3)->entryPointParams_0->nbins_0;

#line 1845
    uint _S36 = (&kernelContext_3)->entryPointParams_0->thrBits_0;

#line 1845
    for(;;)
    {

#line 1845
        (&kernelContext_3)->_tid_0 = _t_0;

#line 1845
        uint _S37 = _pr_0 / _S32;

#line 1845
        uint _S38 = _pr_0 % _S32;

#line 1845
        thread array<float2, int(32)> r_4;

#line 1845
        uint n2_0 = 0U;

#line 1845
        for(;;)
        {

#line 1845
            if(n2_0 < 32U)
            {
            }
            else
            {

#line 1845
                break;
            }

#line 1845
            uint idx_0 = _t_0 + 1024U * n2_0;

#line 1845
            uint _S39 = mfDataStrideFlag_0();

#line 1845
            if(_S39 != 0U)
            {

#line 1845
                uint _S40 = mfDataStrideFlag_0();

#line 1845
                k2_1 = _S40;

#line 1845
            }
            else
            {

#line 1845
                k2_1 = 32768U;

#line 1845
            }

#line 1845
            r_4[n2_0] = cmulConj_0(cload_0((&kernelContext_3)->entryPointParams_data_0, _S37 * k2_1 + idx_0), cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S38 * 32768U + idx_0));

#line 1845
            n2_0 = n2_0 + 1U;

#line 1845
        }

#line 1845
        for(;;)
        {

#line 1845
            for(;;)
            {

#line 1845
                for(;;)
                {

#line 1845
                    for(;;)
                    {

#line 1845
                        uint lgTB_0 = firstbithigh_0(1024U);

#line 1845
                        _S26 = lgTB_0;

#line 1845
                        uint lgLn_0 = firstbithigh_0(32768U);

#line 1845
                        uint blk_1 = _t_0 >> lgTB_0;

#line 1845
                        uint lane_1 = _t_0 & 1023U;

#line 1845
                        dftR_0(&r_4);

#line 1845
                        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 32768.0f);

#line 1845
                        float _S41 = tw_0.x;

#line 1845
                        float _S42 = tw_0.y;

#line 1845
                        k2_1 = 0U;

#line 1845
                        cr_0 = 1.0f;

#line 1845
                        ci_0 = 0.0f;

#line 1845
                        for(;;)
                        {

#line 1845
                            if(k2_1 < 32U)
                            {
                            }
                            else
                            {

#line 1845
                                break;
                            }

#line 1845
                            r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 1845
                            float nr_0 = cr_0 * _S41 - ci_0 * _S42;

#line 1845
                            float _S43 = cr_0 * _S42 + ci_0 * _S41;

#line 1845
                            k2_1 = k2_1 + 1U;

#line 1845
                            cr_0 = nr_0;

#line 1845
                            ci_0 = _S43;

#line 1845
                        }

#line 1845
                        uint per_1 = 32U / max(1024U, 1U);

#line 1845
                        uint _S44 = max(32U, 1U);

#line 1845
                        _S27 = _S44;

#line 1845
                        uint blk2_1 = _t_0 / _S44;

#line 1845
                        uint lane2_1 = _t_0 % _S44;

#line 1845
                        for(;;)
                        {

#line 1845
                            thread array<float2, int(32)> out_0;

#line 1845
                            z_1 = 0U;

#line 1845
                            for(;;)
                            {

#line 1845
                                if(z_1 < 32U)
                                {
                                }
                                else
                                {

#line 1845
                                    break;
                                }

#line 1845
                                out_0[z_1] = float2(0.0f, 0.0f);

#line 1845
                                z_1 = z_1 + 1U;

#line 1845
                            }

#line 1845
                            uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 1845
                            _S28 = spanMask_0;

#line 1845
                            uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1845
                            uint p0_0 = computeWant_0(0U, 1024U, 32768U, blk_1, lane_1, per_1, _S44, 1024U, blk2_1, lane2_1);

#line 1845
                            uint _S45 = p0_0 & lenMask_0;

#line 1845
                            uint _S46 = _S45 >> lgTB_0;

#line 1845
                            uint _S47 = _S46 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S45 & spanMask_0);

#line 1845
                            c_2 = 0U;

#line 1845
                            for(;;)
                            {

#line 1845
                                if(c_2 < 4U)
                                {
                                }
                                else
                                {

#line 1845
                                    break;
                                }

#line 1845
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1845
                                j_2 = 0U;

#line 1845
                                for(;;)
                                {

#line 1845
                                    if(j_2 < 8U)
                                    {
                                    }
                                    else
                                    {

#line 1845
                                        break;
                                    }

#line 1845
                                    stgPut_0(j_2 * 1024U + (&kernelContext_3)->_tid_0, r_4[c_2 * 8U + j_2], &kernelContext_3);

#line 1845
                                    j_2 = j_2 + 1U;

#line 1845
                                }

#line 1845
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1845
                                d_3 = 0U;

#line 1845
                                for(;;)
                                {

#line 1845
                                    if(d_3 < 32U)
                                    {
                                    }
                                    else
                                    {

#line 1845
                                        break;
                                    }

#line 1845
                                    uint pz_0 = computeWant_0(d_3, 1024U, 32768U, 0U, 0U, per_1, _S44, 1024U, 0U, 0U);

#line 1845
                                    uint _S48 = pz_0 & lenMask_0;

#line 1845
                                    uint iz_0 = _S48 >> lgTB_0;

#line 1845
                                    uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S48 & spanMask_0);

#line 1845
                                    uint i_4 = _S46 + iz_0;

#line 1845
                                    uint _S49 = c_2 * 8U;

#line 1845
                                    if(i_4 >= _S49)
                                    {

#line 1845
                                        isCand_0 = i_4 < ((c_2 + 1U) * 8U);

#line 1845
                                    }
                                    else
                                    {

#line 1845
                                        isCand_0 = false;

#line 1845
                                    }

#line 1845
                                    if(isCand_0)
                                    {

#line 1845
                                        float2 _S50 = stgGet_0(_S47 + az_0 - _S49 * 1024U, &kernelContext_3);

#line 1845
                                        out_0[d_3] = _S50;

#line 1845
                                    }

#line 1845
                                    d_3 = d_3 + 1U;

#line 1845
                                }

#line 1845
                                c_2 = c_2 + 1U;

#line 1845
                            }

#line 1845
                            d_3 = 0U;

#line 1845
                            for(;;)
                            {

#line 1845
                                if(d_3 < 32U)
                                {
                                }
                                else
                                {

#line 1845
                                    break;
                                }

#line 1845
                                r_4[d_3] = out_0[d_3];

#line 1845
                                d_3 = d_3 + 1U;

#line 1845
                            }

#line 1845
                            break;
                        }

#line 1845
                        break;
                    }

#line 1845
                    break;
                }

#line 1845
                for(;;)
                {

#line 1845
                    for(;;)
                    {

#line 1845
                        uint lgTB_1 = firstbithigh_0(32U);

#line 1845
                        uint blk_2 = _t_0 >> lgTB_1;

#line 1845
                        uint lane_2 = _t_0 & 31U;

#line 1845
                        dftR_0(&r_4);

#line 1845
                        float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 1845
                        float _S51 = tw_1.x;

#line 1845
                        float _S52 = tw_1.y;

#line 1845
                        k2_1 = 0U;

#line 1845
                        cr_0 = 1.0f;

#line 1845
                        ci_0 = 0.0f;

#line 1845
                        for(;;)
                        {

#line 1845
                            if(k2_1 < 32U)
                            {
                            }
                            else
                            {

#line 1845
                                break;
                            }

#line 1845
                            r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 1845
                            float nr_1 = cr_0 * _S51 - ci_0 * _S52;

#line 1845
                            float _S53 = cr_0 * _S52 + ci_0 * _S51;

#line 1845
                            k2_1 = k2_1 + 1U;

#line 1845
                            cr_0 = nr_1;

#line 1845
                            ci_0 = _S53;

#line 1845
                        }

#line 1845
                        uint per_2 = 32U / _S27;

#line 1845
                        uint _S54 = max(1U, 1U);

#line 1845
                        uint blk2_2 = _t_0 / _S54;

#line 1845
                        uint lane2_2 = _t_0 % _S54;

#line 1845
                        for(;;)
                        {

#line 1845
                            thread array<float2, int(32)> out_1;

#line 1845
                            z_1 = 0U;

#line 1845
                            for(;;)
                            {

#line 1845
                                if(z_1 < 32U)
                                {
                                }
                                else
                                {

#line 1845
                                    break;
                                }

#line 1845
                                out_1[z_1] = float2(0.0f, 0.0f);

#line 1845
                                z_1 = z_1 + 1U;

#line 1845
                            }

#line 1845
                            uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 1845
                            uint p0_1 = computeWant_0(0U, 32U, 1024U, blk_2, lane_2, per_2, _S54, 32U, blk2_2, lane2_2);

#line 1845
                            uint _S55 = p0_1 & _S28;

#line 1845
                            uint _S56 = _S55 >> lgTB_1;

#line 1845
                            uint _S57 = _S56 * 1024U + ((p0_1 >> _S26) << lgTB_1) + (_S55 & spanMask_1);

#line 1845
                            c_2 = 0U;

#line 1845
                            for(;;)
                            {

#line 1845
                                if(c_2 < 4U)
                                {
                                }
                                else
                                {

#line 1845
                                    break;
                                }

#line 1845
                                bool _S58 = c_2 == 0U;

#line 1845
                                if(!_S58)
                                {

#line 1845
                                    simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 1845
                                }
                                else
                                {

#line 1845
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1845
                                }

#line 1845
                                j_2 = 0U;

#line 1845
                                for(;;)
                                {

#line 1845
                                    if(j_2 < 8U)
                                    {
                                    }
                                    else
                                    {

#line 1845
                                        break;
                                    }

#line 1845
                                    stgPut_0(j_2 * 1024U + (&kernelContext_3)->_tid_0, r_4[c_2 * 8U + j_2], &kernelContext_3);

#line 1845
                                    j_2 = j_2 + 1U;

#line 1845
                                }

#line 1845
                                simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 1845
                                d_3 = 0U;

#line 1845
                                for(;;)
                                {

#line 1845
                                    if(d_3 < 32U)
                                    {
                                    }
                                    else
                                    {

#line 1845
                                        break;
                                    }

#line 1845
                                    uint pz_1 = computeWant_0(d_3, 32U, 1024U, 0U, 0U, per_2, _S54, 32U, 0U, 0U);

#line 1845
                                    uint _S59 = pz_1 & _S28;

#line 1845
                                    uint iz_1 = _S59 >> lgTB_1;

#line 1845
                                    uint az_1 = iz_1 * 1024U + ((pz_1 >> _S26) << lgTB_1) + (_S59 & spanMask_1);

#line 1845
                                    uint i_5 = _S56 + iz_1;

#line 1845
                                    uint _S60 = c_2 * 8U;

#line 1845
                                    if(i_5 >= _S60)
                                    {

#line 1845
                                        isCand_0 = i_5 < ((c_2 + 1U) * 8U);

#line 1845
                                    }
                                    else
                                    {

#line 1845
                                        isCand_0 = false;

#line 1845
                                    }

#line 1845
                                    if(isCand_0)
                                    {

#line 1845
                                        float2 _S61 = stgGet_0(_S57 + az_1 - _S60 * 1024U, &kernelContext_3);

#line 1845
                                        out_1[d_3] = _S61;

#line 1845
                                    }

#line 1845
                                    d_3 = d_3 + 1U;

#line 1845
                                }

#line 1845
                                c_2 = c_2 + 1U;

#line 1845
                            }

#line 1845
                            d_3 = 0U;

#line 1845
                            for(;;)
                            {

#line 1845
                                if(d_3 < 32U)
                                {
                                }
                                else
                                {

#line 1845
                                    break;
                                }

#line 1845
                                r_4[d_3] = out_1[d_3];

#line 1845
                                d_3 = d_3 + 1U;

#line 1845
                            }

#line 1845
                            break;
                        }

#line 1845
                        break;
                    }

#line 1845
                    break;
                }

#line 1845
                break;
            }

#line 1845
            innermost_0(&r_4);

#line 1845
            break;
        }

#line 1845
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1845
        uint i_6;

#line 1845
        uint s0_1;

#line 1845
        uint m1_1;

#line 1845
        uint s1_0;

#line 1845
        uint m2_0;

#line 1845
        uint s2_0;

#line 1845
        uint m3_0;

#line 1845
        if(_S35 <= 4U)
        {

#line 1845
            if(_t_0 < 4U)
            {

#line 1845
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + _t_0] = _S36;

#line 1845
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _t_0] = 4294967295U;

#line 1845
            }

#line 1845
            float2 _S62 = float2(0.0f, 0.0f);

#line 1845
            i_6 = 0U;

#line 1845
            j_2 = _S36;

#line 1845
            s0_1 = 4294967295U;

#line 1845
            float2 v0_0 = _S62;

#line 1845
            m1_1 = _S36;

#line 1845
            s1_0 = 4294967295U;

#line 1845
            float2 v1_0 = _S62;

#line 1845
            m2_0 = _S36;

#line 1845
            s2_0 = 4294967295U;

#line 1845
            float2 v2_0 = _S62;

#line 1845
            m3_0 = _S36;

#line 1845
            uint s3_0 = 4294967295U;

#line 1845
            float2 v3_0 = _S62;

#line 1845
            for(;;)
            {

#line 1845
                if(i_6 < 32U)
                {
                }
                else
                {

#line 1845
                    break;
                }

#line 1845
                uint slot_1 = _t_0 * 32U + i_6;

#line 1845
                uint idx_1 = slotToIndex_0(slot_1);

#line 1845
                if(idx_1 >= _S30)
                {

#line 1845
                    isCand_0 = idx_1 < _S31;

#line 1845
                }
                else
                {

#line 1845
                    isCand_0 = false;

#line 1845
                }

#line 1845
                if(isCand_0)
                {

#line 1845
                    float rx_0 = r_4[i_6].x;

#line 1845
                    float ry_0 = r_4[i_6].y;

#line 1845
                    uint mag_0 = (as_type<uint>((rx_0 * rx_0 + ry_0 * ry_0)));

#line 1845
                    uint off_0 = idx_1 - _S30 + (&kernelContext_3)->_binPhase_0;

#line 1845
                    if(_S35 == 1U)
                    {

#line 1845
                        b_4 = 0U;

#line 1845
                    }
                    else
                    {

#line 1845
                        if(_S34 >= int(0))
                        {

#line 1845
                            n2_0 = off_0 >> uint(_S34);

#line 1845
                        }
                        else
                        {

#line 1845
                            uint _S63 = off_0 / _S33;

#line 1845
                            n2_0 = _S63;

#line 1845
                        }

#line 1845
                        b_4 = n2_0;

#line 1845
                    }

#line 1845
                    bool _S64;

#line 1845
                    if(b_4 == 0U)
                    {

#line 1845
                        _S64 = mag_0 > j_2;

#line 1845
                    }
                    else
                    {

#line 1845
                        _S64 = false;

#line 1845
                    }

#line 1845
                    float2 v0_1;

#line 1845
                    if(_S64)
                    {

#line 1845
                        float2 _S65 = float2(rx_0, ry_0);

#line 1845
                        m0_0 = mag_0;

#line 1845
                        s0_0 = slot_1;

#line 1845
                        v0_1 = _S65;

#line 1845
                    }
                    else
                    {

#line 1845
                        m0_0 = j_2;

#line 1845
                        s0_0 = s0_1;

#line 1845
                        v0_1 = v0_0;

#line 1845
                    }

#line 1845
                    bool _S66;

#line 1845
                    if(_S35 >= 2U)
                    {

#line 1845
                        _S66 = b_4 == 1U;

#line 1845
                    }
                    else
                    {

#line 1845
                        _S66 = false;

#line 1845
                    }

#line 1845
                    bool _S67;

#line 1845
                    if(_S66)
                    {

#line 1845
                        _S67 = mag_0 > m1_1;

#line 1845
                    }
                    else
                    {

#line 1845
                        _S67 = false;

#line 1845
                    }

#line 1845
                    uint s1_1;

#line 1845
                    float2 v1_1;

#line 1845
                    if(_S67)
                    {

#line 1845
                        float2 _S68 = float2(rx_0, ry_0);

#line 1845
                        m1_0 = mag_0;

#line 1845
                        s1_1 = slot_1;

#line 1845
                        v1_1 = _S68;

#line 1845
                    }
                    else
                    {

#line 1845
                        m1_0 = m1_1;

#line 1845
                        s1_1 = s1_0;

#line 1845
                        v1_1 = v1_0;

#line 1845
                    }

#line 1845
                    bool _S69;

#line 1845
                    if(_S35 >= 3U)
                    {

#line 1845
                        _S69 = b_4 == 2U;

#line 1845
                    }
                    else
                    {

#line 1845
                        _S69 = false;

#line 1845
                    }

#line 1845
                    bool _S70;

#line 1845
                    if(_S69)
                    {

#line 1845
                        _S70 = mag_0 > m2_0;

#line 1845
                    }
                    else
                    {

#line 1845
                        _S70 = false;

#line 1845
                    }

#line 1845
                    uint m2_1;

#line 1845
                    uint s2_1;

#line 1845
                    float2 v2_1;

#line 1845
                    if(_S70)
                    {

#line 1845
                        float2 _S71 = float2(rx_0, ry_0);

#line 1845
                        m2_1 = mag_0;

#line 1845
                        s2_1 = slot_1;

#line 1845
                        v2_1 = _S71;

#line 1845
                    }
                    else
                    {

#line 1845
                        m2_1 = m2_0;

#line 1845
                        s2_1 = s2_0;

#line 1845
                        v2_1 = v2_0;

#line 1845
                    }

#line 1845
                    bool _S72;

#line 1845
                    if(_S35 >= 4U)
                    {

#line 1845
                        _S72 = b_4 == 3U;

#line 1845
                    }
                    else
                    {

#line 1845
                        _S72 = false;

#line 1845
                    }

#line 1845
                    bool _S73;

#line 1845
                    if(_S72)
                    {

#line 1845
                        _S73 = mag_0 > m3_0;

#line 1845
                    }
                    else
                    {

#line 1845
                        _S73 = false;

#line 1845
                    }

#line 1845
                    uint m3_1;

#line 1845
                    uint s3_1;

#line 1845
                    float2 v3_1;

#line 1845
                    if(_S73)
                    {

#line 1845
                        float2 _S74 = float2(rx_0, ry_0);

#line 1845
                        m3_1 = mag_0;

#line 1845
                        s3_1 = slot_1;

#line 1845
                        v3_1 = _S74;

#line 1845
                    }
                    else
                    {

#line 1845
                        m3_1 = m3_0;

#line 1845
                        s3_1 = s3_0;

#line 1845
                        v3_1 = v3_0;

#line 1845
                    }

#line 1845
                    j_2 = m0_0;

#line 1845
                    m1_1 = m1_0;

#line 1845
                    m2_0 = m2_1;

#line 1845
                    m3_0 = m3_1;

#line 1845
                    s0_1 = s0_0;

#line 1845
                    s1_0 = s1_1;

#line 1845
                    s2_0 = s2_1;

#line 1845
                    s3_0 = s3_1;

#line 1845
                    v0_0 = v0_1;

#line 1845
                    v1_0 = v1_1;

#line 1845
                    v2_0 = v2_1;

#line 1845
                    v3_0 = v3_1;

#line 1845
                }

#line 1845
                i_6 = i_6 + 1U;

#line 1845
            }

#line 1845
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1845
            uint wm0_0 = simd_max(j_2);

#line 1845
            bool _S75 = simd_is_first();

#line 1845
            if(_S75)
            {

#line 1845
                isCand_0 = wm0_0 > _S36;

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                uint _S76 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), wm0_0, memory_order_relaxed);

#line 1845
            }

#line 1845
            bool _S77 = _S35 >= 2U;

#line 1845
            if(_S77)
            {

#line 1845
                uint wm1_0 = simd_max(m1_1);

#line 1845
                bool _S78 = simd_is_first();

#line 1845
                if(_S78)
                {

#line 1845
                    isCand_0 = wm1_0 > _S36;

#line 1845
                }
                else
                {

#line 1845
                    isCand_0 = false;

#line 1845
                }

#line 1845
                if(isCand_0)
                {

#line 1845
                    uint _S79 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), wm1_0, memory_order_relaxed);

#line 1845
                }

#line 1845
            }

#line 1845
            bool _S80 = _S35 >= 3U;

#line 1845
            if(_S80)
            {

#line 1845
                uint wm2_0 = simd_max(m2_0);

#line 1845
                bool _S81 = simd_is_first();

#line 1845
                if(_S81)
                {

#line 1845
                    isCand_0 = wm2_0 > _S36;

#line 1845
                }
                else
                {

#line 1845
                    isCand_0 = false;

#line 1845
                }

#line 1845
                if(isCand_0)
                {

#line 1845
                    uint _S82 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U])), wm2_0, memory_order_relaxed);

#line 1845
                }

#line 1845
            }

#line 1845
            bool _S83 = _S35 >= 4U;

#line 1845
            if(_S83)
            {

#line 1845
                uint wm3_0 = simd_max(m3_0);

#line 1845
                bool _S84 = simd_is_first();

#line 1845
                if(_S84)
                {

#line 1845
                    isCand_0 = wm3_0 > _S36;

#line 1845
                }
                else
                {

#line 1845
                    isCand_0 = false;

#line 1845
                }

#line 1845
                if(isCand_0)
                {

#line 1845
                    uint _S85 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U])), wm3_0, memory_order_relaxed);

#line 1845
                }

#line 1845
            }

#line 1845
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1845
            if(s0_1 != 4294967295U)
            {

#line 1845
                isCand_0 = j_2 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0];

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                b_4 = s0_1;

#line 1845
            }
            else
            {

#line 1845
                b_4 = 4294967295U;

#line 1845
            }

#line 1845
            if(_S77)
            {

#line 1845
                isCand_0 = s1_0 != 4294967295U;

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                isCand_0 = m1_1 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U];

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                m0_0 = s1_0;

#line 1845
            }
            else
            {

#line 1845
                m0_0 = 4294967295U;

#line 1845
            }

#line 1845
            if(_S80)
            {

#line 1845
                isCand_0 = s2_0 != 4294967295U;

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                isCand_0 = m2_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 2U];

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                s0_0 = s2_0;

#line 1845
            }
            else
            {

#line 1845
                s0_0 = 4294967295U;

#line 1845
            }

#line 1845
            if(_S83)
            {

#line 1845
                isCand_0 = s3_0 != 4294967295U;

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                isCand_0 = m3_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 3U];

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                m1_0 = s3_0;

#line 1845
            }
            else
            {

#line 1845
                m1_0 = 4294967295U;

#line 1845
            }

#line 1845
            uint ww0_0 = simd_min(b_4);

#line 1845
            bool _S86 = simd_is_first();

#line 1845
            if(_S86)
            {

#line 1845
                isCand_0 = ww0_0 != 4294967295U;

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                uint _S87 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U])), ww0_0, memory_order_relaxed);

#line 1845
            }

#line 1845
            if(_S77)
            {

#line 1845
                uint ww1_0 = simd_min(m0_0);

#line 1845
                bool _S88 = simd_is_first();

#line 1845
                if(_S88)
                {

#line 1845
                    isCand_0 = ww1_0 != 4294967295U;

#line 1845
                }
                else
                {

#line 1845
                    isCand_0 = false;

#line 1845
                }

#line 1845
                if(isCand_0)
                {

#line 1845
                    uint _S89 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U])), ww1_0, memory_order_relaxed);

#line 1845
                }

#line 1845
            }

#line 1845
            if(_S80)
            {

#line 1845
                uint ww2_0 = simd_min(s0_0);

#line 1845
                bool _S90 = simd_is_first();

#line 1845
                if(_S90)
                {

#line 1845
                    isCand_0 = ww2_0 != 4294967295U;

#line 1845
                }
                else
                {

#line 1845
                    isCand_0 = false;

#line 1845
                }

#line 1845
                if(isCand_0)
                {

#line 1845
                    uint _S91 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U])), ww2_0, memory_order_relaxed);

#line 1845
                }

#line 1845
            }

#line 1845
            if(_S83)
            {

#line 1845
                uint ww3_0 = simd_min(m1_0);

#line 1845
                bool _S92 = simd_is_first();

#line 1845
                if(_S92)
                {

#line 1845
                    isCand_0 = ww3_0 != 4294967295U;

#line 1845
                }
                else
                {

#line 1845
                    isCand_0 = false;

#line 1845
                }

#line 1845
                if(isCand_0)
                {

#line 1845
                    uint _S93 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U])), ww3_0, memory_order_relaxed);

#line 1845
                }

#line 1845
            }

#line 1845
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1845
            uint baseOut_0 = _pr_0 * _S35;

#line 1845
            if(b_4 != 4294967295U)
            {

#line 1845
                isCand_0 = b_4 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U];

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                *((&kernelContext_3)->entryPointParams_peakIdx_0+baseOut_0) = int(slotToIndex_0(b_4));

#line 1845
                *((&kernelContext_3)->entryPointParams_peakVal_0+baseOut_0) = packed_float2(v0_0) ;

#line 1845
            }

#line 1845
            if(_S77)
            {

#line 1845
                isCand_0 = m0_0 != 4294967295U;

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                isCand_0 = m0_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 5U];

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                uint _S94 = baseOut_0 + 1U;

#line 1845
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S94) = int(slotToIndex_0(m0_0));

#line 1845
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S94) = packed_float2(v1_0) ;

#line 1845
            }

#line 1845
            if(_S80)
            {

#line 1845
                isCand_0 = s0_0 != 4294967295U;

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                isCand_0 = s0_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 6U];

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                uint _S95 = baseOut_0 + 2U;

#line 1845
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S95) = int(slotToIndex_0(s0_0));

#line 1845
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S95) = packed_float2(v2_0) ;

#line 1845
            }

#line 1845
            if(_S83)
            {

#line 1845
                isCand_0 = m1_0 != 4294967295U;

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                isCand_0 = m1_0 == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 7U];

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                uint _S96 = baseOut_0 + 3U;

#line 1845
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S96) = int(slotToIndex_0(m1_0));

#line 1845
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S96) = packed_float2(v3_0) ;

#line 1845
            }

#line 1845
            if(_t_0 < _S35)
            {

#line 1845
                isCand_0 = ((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 4U + _t_0]) == 4294967295U;

#line 1845
            }
            else
            {

#line 1845
                isCand_0 = false;

#line 1845
            }

#line 1845
            if(isCand_0)
            {

#line 1845
                uint _S97 = baseOut_0 + _t_0;

#line 1845
                *((&kernelContext_3)->entryPointParams_peakIdx_0+_S97) = int(-1);

#line 1845
                *((&kernelContext_3)->entryPointParams_peakVal_0+_S97) = packed_float2(_S62) ;

#line 1845
            }

#line 1845
        }
        else
        {

#line 1845
            j_2 = _t_0;

#line 1845
            for(;;)
            {

#line 1845
                if(j_2 < _S35)
                {
                }
                else
                {

#line 1845
                    break;
                }

#line 1845
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2] = _S36;

#line 1845
                j_2 = j_2 + 1024U;

#line 1845
            }

#line 1845
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1845
            i_6 = 0U;

#line 1845
            s0_1 = 0U;

#line 1845
            m1_1 = 0U;

#line 1845
            for(;;)
            {

#line 1845
                bool _S98 = i_6 < 32U;

#line 1845
                if(_S98)
                {
                }
                else
                {

#line 1845
                    break;
                }

#line 1845
                uint idx_2 = slotToIndex_0(_t_0 * 32U + i_6);

#line 1845
                if(idx_2 >= _S30)
                {

#line 1845
                    isCand_0 = idx_2 < _S31;

#line 1845
                }
                else
                {

#line 1845
                    isCand_0 = false;

#line 1845
                }

#line 1845
                if(isCand_0)
                {

#line 1845
                    float rx_1 = r_4[i_6].x;

#line 1845
                    float ry_1 = r_4[i_6].y;

#line 1845
                    uint mag_1 = (as_type<uint>((rx_1 * rx_1 + ry_1 * ry_1)));

#line 1845
                    if(mag_1 > _S36)
                    {

#line 1845
                        uint off_1 = idx_2 - _S30 + (&kernelContext_3)->_binPhase_0;

#line 1845
                        if(_S34 >= int(0))
                        {

#line 1845
                            j_2 = off_1 >> uint(_S34);

#line 1845
                        }
                        else
                        {

#line 1845
                            uint _S99 = off_1 / _S33;

#line 1845
                            j_2 = _S99;

#line 1845
                        }

#line 1845
                        uint _S100 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2])), mag_1, memory_order_relaxed);

#line 1845
                        uint bit_0 = 1U << (i_6 & 31U);

#line 1845
                        if(_S98)
                        {

#line 1845
                            s1_0 = s0_1 | bit_0;

#line 1845
                            m2_0 = m1_1;

#line 1845
                        }
                        else
                        {

#line 1845
                            uint aboveHi_0 = m1_1 | bit_0;

#line 1845
                            s1_0 = s0_1;

#line 1845
                            m2_0 = aboveHi_0;

#line 1845
                        }

#line 1845
                    }
                    else
                    {

#line 1845
                        s1_0 = s0_1;

#line 1845
                        m2_0 = m1_1;

#line 1845
                    }

#line 1845
                }
                else
                {

#line 1845
                    s1_0 = s0_1;

#line 1845
                    m2_0 = m1_1;

#line 1845
                }

#line 1845
                i_6 = i_6 + 1U;

#line 1845
                s0_1 = s1_0;

#line 1845
                m1_1 = m2_0;

#line 1845
            }

#line 1845
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1845
            if((s0_1 | m1_1) != 0U)
            {

#line 1845
                i_6 = 0U;

#line 1845
                s1_0 = 0U;

#line 1845
                m2_0 = 0U;

#line 1845
                for(;;)
                {

#line 1845
                    bool _S101 = i_6 < 32U;

#line 1845
                    if(_S101)
                    {
                    }
                    else
                    {

#line 1845
                        break;
                    }

#line 1845
                    uint bit_1 = 1U << (i_6 & 31U);

#line 1845
                    if(_S101)
                    {

#line 1845
                        isCand_0 = (s0_1 & bit_1) != 0U;

#line 1845
                    }
                    else
                    {

#line 1845
                        isCand_0 = (m1_1 & bit_1) != 0U;

#line 1845
                    }

#line 1845
                    if(isCand_0)
                    {

#line 1845
                        uint off_2 = slotToIndex_0(_t_0 * 32U + i_6) - _S30 + (&kernelContext_3)->_binPhase_0;

#line 1845
                        if(_S34 >= int(0))
                        {

#line 1845
                            j_2 = off_2 >> uint(_S34);

#line 1845
                        }
                        else
                        {

#line 1845
                            uint _S102 = off_2 / _S33;

#line 1845
                            j_2 = _S102;

#line 1845
                        }

#line 1845
                        float rx_2 = r_4[i_6].x;

#line 1845
                        float ry_2 = r_4[i_6].y;

#line 1845
                        if((as_type<uint>((rx_2 * rx_2 + ry_2 * ry_2))) == (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2])
                        {

#line 1845
                            if(_S101)
                            {

#line 1845
                                s2_0 = s1_0 | bit_1;

#line 1845
                                m3_0 = m2_0;

#line 1845
                            }
                            else
                            {

#line 1845
                                uint candHi_0 = m2_0 | bit_1;

#line 1845
                                s2_0 = s1_0;

#line 1845
                                m3_0 = candHi_0;

#line 1845
                            }

#line 1845
                        }
                        else
                        {

#line 1845
                            s2_0 = s1_0;

#line 1845
                            m3_0 = m2_0;

#line 1845
                        }

#line 1845
                    }
                    else
                    {

#line 1845
                        s2_0 = s1_0;

#line 1845
                        m3_0 = m2_0;

#line 1845
                    }

#line 1845
                    i_6 = i_6 + 1U;

#line 1845
                    s1_0 = s2_0;

#line 1845
                    m2_0 = m3_0;

#line 1845
                }

#line 1845
                s2_0 = s1_0;

#line 1845
                m3_0 = m2_0;

#line 1845
            }
            else
            {

#line 1845
                s2_0 = 0U;

#line 1845
                m3_0 = 0U;

#line 1845
            }

#line 1845
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1845
            j_2 = _t_0;

#line 1845
            for(;;)
            {

#line 1845
                if(j_2 < _S35)
                {
                }
                else
                {

#line 1845
                    break;
                }

#line 1845
                (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2] = 4294967295U;

#line 1845
                j_2 = j_2 + 1024U;

#line 1845
            }

#line 1845
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1845
            bool _S103 = (s2_0 | m3_0) != 0U;

#line 1845
            if(_S103)
            {

#line 1845
                i_6 = 0U;

#line 1845
                for(;;)
                {

#line 1845
                    bool _S104 = i_6 < 32U;

#line 1845
                    if(_S104)
                    {
                    }
                    else
                    {

#line 1845
                        break;
                    }

#line 1845
                    uint bit_2 = 1U << (i_6 & 31U);

#line 1845
                    if(_S104)
                    {

#line 1845
                        isCand_0 = (s2_0 & bit_2) != 0U;

#line 1845
                    }
                    else
                    {

#line 1845
                        isCand_0 = (m3_0 & bit_2) != 0U;

#line 1845
                    }

#line 1845
                    if(isCand_0)
                    {

#line 1845
                        uint _S105 = _t_0 * 32U + i_6;

#line 1845
                        uint off_3 = slotToIndex_0(_S105) - _S30 + (&kernelContext_3)->_binPhase_0;

#line 1845
                        if(_S34 >= int(0))
                        {

#line 1845
                            j_2 = off_3 >> uint(_S34);

#line 1845
                        }
                        else
                        {

#line 1845
                            uint _S106 = off_3 / _S33;

#line 1845
                            j_2 = _S106;

#line 1845
                        }

#line 1845
                        uint _S107 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2])), _S105, memory_order_relaxed);

#line 1845
                    }

#line 1845
                    i_6 = i_6 + 1U;

#line 1845
                }

#line 1845
            }

#line 1845
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1845
            if(_S103)
            {

#line 1845
                i_6 = 0U;

#line 1845
                for(;;)
                {

#line 1845
                    bool _S108 = i_6 < 32U;

#line 1845
                    if(_S108)
                    {
                    }
                    else
                    {

#line 1845
                        break;
                    }

#line 1845
                    uint bit_3 = 1U << (i_6 & 31U);

#line 1845
                    if(_S108)
                    {

#line 1845
                        isCand_0 = (s2_0 & bit_3) != 0U;

#line 1845
                    }
                    else
                    {

#line 1845
                        isCand_0 = (m3_0 & bit_3) != 0U;

#line 1845
                    }

#line 1845
                    if(isCand_0)
                    {

#line 1845
                        uint _S109 = _t_0 * 32U + i_6;

#line 1845
                        uint idx_3 = slotToIndex_0(_S109);

#line 1845
                        uint off_4 = idx_3 - _S30 + (&kernelContext_3)->_binPhase_0;

#line 1845
                        if(_S34 >= int(0))
                        {

#line 1845
                            j_2 = off_4 >> uint(_S34);

#line 1845
                        }
                        else
                        {

#line 1845
                            uint _S110 = off_4 / _S33;

#line 1845
                            j_2 = _S110;

#line 1845
                        }

#line 1845
                        if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2]) == _S109)
                        {

#line 1845
                            uint o_0 = _pr_0 * _S35 + j_2;

#line 1845
                            *((&kernelContext_3)->entryPointParams_peakIdx_0+o_0) = int(idx_3);

#line 1845
                            *((&kernelContext_3)->entryPointParams_peakVal_0+o_0) = packed_float2(float2(r_4[i_6].x, r_4[i_6].y)) ;

#line 1845
                        }

#line 1845
                    }

#line 1845
                    i_6 = i_6 + 1U;

#line 1845
                }

#line 1845
            }

#line 1845
            j_2 = _t_0;

#line 1845
            for(;;)
            {

#line 1845
                if(j_2 < _S35)
                {
                }
                else
                {

#line 1845
                    break;
                }

#line 1845
                if(((*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + j_2]) == 4294967295U)
                {

#line 1845
                    uint _S111 = _pr_0 * _S35 + j_2;

#line 1845
                    *((&kernelContext_3)->entryPointParams_peakIdx_0+_S111) = int(-1);

#line 1845
                    *((&kernelContext_3)->entryPointParams_peakVal_0+_S111) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1845
                }

#line 1845
                j_2 = j_2 + 1024U;

#line 1845
            }

#line 1845
        }

#line 1845
        break;
    }

#line 1851
    return;
}
