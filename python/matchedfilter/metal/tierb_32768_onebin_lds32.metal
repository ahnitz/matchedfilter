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


#line 317 "mm_32768_fusedTierB_onebin_lds32.slang"
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

#line 230 "mm_32768_fusedTierB_onebin_lds32.slang"
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


#line 173 "mm_32768_fusedTierB_onebin_lds32.slang"
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


#line 328 "mm_32768_fusedTierB_onebin_lds32.slang"
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


#line 615
void r4_0(float2 thread* a_2, float2 thread* b_3, float2 thread* c_1, float2 thread* d_1)
{
    float2 t0_0 = *a_2 + *c_1;

#line 617
    float2 t1_0 = *a_2 - *c_1;

#line 617
    float2 t2_0 = *b_3 + *d_1;

#line 617
    float2 t3_0 = *b_3 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_2 = t0_0 + t2_0;

#line 619
    *b_3 = t1_0 + j3_0;

#line 619
    *c_1 = t0_0 - t2_0;

#line 619
    *d_1 = t1_0 - j3_0;
    return;
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


#line 697
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 699
    thread array<float2, int(16)> v_0;

#line 699
    uint j_0 = 0U;
    for(;;)
    {

#line 700
        if(j_0 < 16U)
        {
        }
        else
        {

#line 700
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        float2 _S18 = (*r_1)[j_0] - (*r_1)[j_0 + 16U];

#line 704
        float2 _S19 = mfTwiddle_0(6.28318548202514648f * float(j_0) / 32.0f);

#line 704
        v_0[j_0] = cmul_0(_S18, _S19);

#line 700
        j_0 = j_0 + 1U;

#line 700
    }

#line 706
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 707
    uint k_0 = 0U;
    for(;;)
    {

#line 708
        if(k_0 < 16U)
        {
        }
        else
        {

#line 708
            break;
        }

#line 708
        uint _S20 = 2U * k_0;

#line 708
        (*r_1)[_S20] = u_0[k_0];

#line 708
        (*r_1)[_S20 + 1U] = v_0[k_0];

#line 708
        k_0 = k_0 + 1U;

#line 708
    }
    return;
}


#line 736
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


#line 754
void innermost_0(array<float2, int(32)> thread* r_3)
{

    dft32_0(r_3);

#line 766
    return;
}


#line 882
uint lgOf_0(uint i_3)
{

#line 882
    uint _S25;

#line 882
    if(i_3 < 2U)
    {

#line 882
        _S25 = 5U;

#line 882
    }
    else
    {

#line 882
        if(i_3 == 2U)
        {

#line 882
            _S25 = 5U;

#line 882
        }
        else
        {

#line 882
            _S25 = 1U;

#line 882
        }

#line 882
    }

#line 882
    return _S25;
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
    uint _S26;

#line 1854
    float cr_0;

#line 1854
    float ci_0;

#line 1854
    uint _S27;

#line 1854
    uint z_1;

#line 1854
    uint _S28;

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
    uint _S29 = _pr_0 / entryPointParams_1->ntmpl_0;

#line 1883
    rowWindow_0(_S29, &_ws_0, &_we_0, (&kernelContext_3)->entryPointParams_rowWin_0, &kernelContext_3);
    uint _S30 = _ws_0;

#line 1884
    uint _S31 = _we_0;

#line 1884
    uint _S32 = entryPointParams_1->ntmpl_0;

#line 1884
    uint _S33 = (&kernelContext_3)->entryPointParams_0->thrBits_0;

#line 1884
    for(;;)
    {

#line 1884
        (&kernelContext_3)->_tid_0 = _t_0;

#line 1884
        uint _S34 = _pr_0 / _S32;

#line 1884
        uint _S35 = _pr_0 % _S32;

#line 1884
        thread array<float2, int(32)> r_4;

#line 1884
        uint n2_0 = 0U;

#line 1884
        for(;;)
        {

#line 1884
            if(n2_0 < 32U)
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
            uint _S36 = mfDataStrideFlag_0();

#line 1884
            if(_S36 != 0U)
            {

#line 1884
                uint _S37 = mfDataStrideFlag_0();

#line 1884
                k2_1 = _S37;

#line 1884
            }
            else
            {

#line 1884
                k2_1 = 32768U;

#line 1884
            }

#line 1884
            r_4[n2_0] = cmulConj_0(cload_0((&kernelContext_3)->entryPointParams_data_0, _S34 * k2_1 + idx_0), cload_0((&kernelContext_3)->entryPointParams_tmpl_0, _S35 * 32768U + idx_0));

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
                        _S26 = lgTB_0;

#line 1884
                        uint lgLn_0 = firstbithigh_0(32768U);

#line 1884
                        uint blk_1 = _t_0 >> lgTB_0;

#line 1884
                        uint lane_1 = _t_0 & 1023U;

#line 1884
                        dftR_0(&r_4);

#line 1884
                        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 32768.0f);

#line 1884
                        float _S38 = tw_0.x;

#line 1884
                        float _S39 = tw_0.y;

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
                            if(k2_1 < 32U)
                            {
                            }
                            else
                            {

#line 1884
                                break;
                            }

#line 1884
                            r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 1884
                            float nr_0 = cr_0 * _S38 - ci_0 * _S39;

#line 1884
                            float _S40 = cr_0 * _S39 + ci_0 * _S38;

#line 1884
                            k2_1 = k2_1 + 1U;

#line 1884
                            cr_0 = nr_0;

#line 1884
                            ci_0 = _S40;

#line 1884
                        }

#line 1884
                        uint per_1 = 32U / max(1024U, 1U);

#line 1884
                        uint _S41 = max(32U, 1U);

#line 1884
                        _S27 = _S41;

#line 1884
                        uint blk2_1 = _t_0 / _S41;

#line 1884
                        uint lane2_1 = _t_0 % _S41;

#line 1884
                        for(;;)
                        {

#line 1884
                            thread array<float2, int(32)> out_0;

#line 1884
                            z_1 = 0U;

#line 1884
                            for(;;)
                            {

#line 1884
                                if(z_1 < 32U)
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
                            _S28 = spanMask_0;

#line 1884
                            uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1884
                            uint p0_0 = computeWant_0(0U, 1024U, 32768U, blk_1, lane_1, per_1, _S41, 1024U, blk2_1, lane2_1);

#line 1884
                            uint _S42 = p0_0 & lenMask_0;

#line 1884
                            uint _S43 = _S42 >> lgTB_0;

#line 1884
                            uint _S44 = _S43 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S42 & spanMask_0);

#line 1884
                            c_2 = 0U;

#line 1884
                            for(;;)
                            {

#line 1884
                                if(c_2 < 8U)
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
                                    stgPut_0(j_2 * 1024U + (&kernelContext_3)->_tid_0, r_4[c_2 * 4U + j_2], &kernelContext_3);

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
                                    if(d_3 < 32U)
                                    {
                                    }
                                    else
                                    {

#line 1884
                                        break;
                                    }

#line 1884
                                    uint pz_0 = computeWant_0(d_3, 1024U, 32768U, 0U, 0U, per_1, _S41, 1024U, 0U, 0U);

#line 1884
                                    uint _S45 = pz_0 & lenMask_0;

#line 1884
                                    uint iz_0 = _S45 >> lgTB_0;

#line 1884
                                    uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S45 & spanMask_0);

#line 1884
                                    uint i_4 = _S43 + iz_0;

#line 1884
                                    uint _S46 = c_2 * 4U;

#line 1884
                                    if(i_4 >= _S46)
                                    {

#line 1884
                                        live_0 = i_4 < ((c_2 + 1U) * 4U);

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
                                        float2 _S47 = stgGet_0(_S44 + az_0 - _S46 * 1024U, &kernelContext_3);

#line 1884
                                        out_0[d_3] = _S47;

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
                                if(d_3 < 32U)
                                {
                                }
                                else
                                {

#line 1884
                                    break;
                                }

#line 1884
                                r_4[d_3] = out_0[d_3];

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
                        uint lgTB_1 = firstbithigh_0(32U);

#line 1884
                        uint blk_2 = _t_0 >> lgTB_1;

#line 1884
                        uint lane_2 = _t_0 & 31U;

#line 1884
                        dftR_0(&r_4);

#line 1884
                        float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 1884
                        float _S48 = tw_1.x;

#line 1884
                        float _S49 = tw_1.y;

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
                            if(k2_1 < 32U)
                            {
                            }
                            else
                            {

#line 1884
                                break;
                            }

#line 1884
                            r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 1884
                            float nr_1 = cr_0 * _S48 - ci_0 * _S49;

#line 1884
                            float _S50 = cr_0 * _S49 + ci_0 * _S48;

#line 1884
                            k2_1 = k2_1 + 1U;

#line 1884
                            cr_0 = nr_1;

#line 1884
                            ci_0 = _S50;

#line 1884
                        }

#line 1884
                        uint per_2 = 32U / _S27;

#line 1884
                        uint _S51 = max(1U, 1U);

#line 1884
                        uint blk2_2 = _t_0 / _S51;

#line 1884
                        uint lane2_2 = _t_0 % _S51;

#line 1884
                        for(;;)
                        {

#line 1884
                            thread array<float2, int(32)> out_1;

#line 1884
                            z_1 = 0U;

#line 1884
                            for(;;)
                            {

#line 1884
                                if(z_1 < 32U)
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
                            uint p0_1 = computeWant_0(0U, 32U, 1024U, blk_2, lane_2, per_2, _S51, 32U, blk2_2, lane2_2);

#line 1884
                            uint _S52 = p0_1 & _S28;

#line 1884
                            uint _S53 = _S52 >> lgTB_1;

#line 1884
                            uint _S54 = _S53 * 1024U + ((p0_1 >> _S26) << lgTB_1) + (_S52 & spanMask_1);

#line 1884
                            c_2 = 0U;

#line 1884
                            for(;;)
                            {

#line 1884
                                if(c_2 < 8U)
                                {
                                }
                                else
                                {

#line 1884
                                    break;
                                }

#line 1884
                                bool _S55 = c_2 == 0U;

#line 1884
                                if(!_S55)
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
                                    stgPut_0(j_2 * 1024U + (&kernelContext_3)->_tid_0, r_4[c_2 * 4U + j_2], &kernelContext_3);

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
                                    if(d_3 < 32U)
                                    {
                                    }
                                    else
                                    {

#line 1884
                                        break;
                                    }

#line 1884
                                    uint pz_1 = computeWant_0(d_3, 32U, 1024U, 0U, 0U, per_2, _S51, 32U, 0U, 0U);

#line 1884
                                    uint _S56 = pz_1 & _S28;

#line 1884
                                    uint iz_1 = _S56 >> lgTB_1;

#line 1884
                                    uint az_1 = iz_1 * 1024U + ((pz_1 >> _S26) << lgTB_1) + (_S56 & spanMask_1);

#line 1884
                                    uint i_5 = _S53 + iz_1;

#line 1884
                                    uint _S57 = c_2 * 4U;

#line 1884
                                    if(i_5 >= _S57)
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
                                        float2 _S58 = stgGet_0(_S54 + az_1 - _S57 * 1024U, &kernelContext_3);

#line 1884
                                        out_1[d_3] = _S58;

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
                                if(d_3 < 32U)
                                {
                                }
                                else
                                {

#line 1884
                                    break;
                                }

#line 1884
                                r_4[d_3] = out_1[d_3];

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
            innermost_0(&r_4);

#line 1884
            break;
        }

#line 1884
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
        float2 _S59 = float2(0.0f, 0.0f);

#line 1884
        if(_S30 == 0U)
        {

#line 1884
            live_0 = _S31 >= 32768U;

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
            threadBestBits_0 = _S33;

#line 1884
            threadBestSlot_0 = 4294967295U;

#line 1884
            threadBestVal_0 = _S59;

#line 1884
            for(;;)
            {

#line 1884
                if(j_2 < 32U)
                {
                }
                else
                {

#line 1884
                    break;
                }

#line 1884
                float _rx_0 = r_4[j_2].x;

#line 1884
                float _ry_0 = r_4[j_2].y;

#line 1884
                uint magBits_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1884
                if(magBits_0 > threadBestBits_0)
                {

#line 1884
                    uint _S60 = _t_0 * 32U + j_2;

#line 1884
                    float2 _S61 = float2(_rx_0, _ry_0);

#line 1884
                    threadBestBits_0 = magBits_0;

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
        else
        {

#line 1884
            j_2 = 0U;

#line 1884
            threadBestBits_0 = _S33;

#line 1884
            threadBestSlot_0 = 4294967295U;

#line 1884
            threadBestVal_0 = _S59;

#line 1884
            for(;;)
            {

#line 1884
                if(j_2 < 32U)
                {
                }
                else
                {

#line 1884
                    break;
                }

#line 1884
                uint _S62 = _t_0 * 32U + j_2;

#line 1884
                uint idx_1 = slotToIndex_0(_S62);

#line 1884
                if(idx_1 >= _S30)
                {

#line 1884
                    live_0 = idx_1 < _S31;

#line 1884
                }
                else
                {

#line 1884
                    live_0 = false;

#line 1884
                }

#line 1884
                float _rx_1 = r_4[j_2].x;

#line 1884
                float _ry_1 = r_4[j_2].y;

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
                    float2 _S63 = float2(_rx_1, _ry_1);

#line 1884
                    threadBestBits_0 = magBits_1;

#line 1884
                    threadBestSlot_0 = _S62;

#line 1884
                    threadBestVal_0 = _S63;

#line 1884
                }

#line 1884
                j_2 = j_2 + 1U;

#line 1884
            }

#line 1884
        }

#line 1884
        bool _S64 = _t_0 == 0U;

#line 1884
        if(_S64)
        {

#line 1884
            (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0] = _S33;

#line 1884
            (*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U] = 4294967295U;

#line 1884
        }

#line 1884
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
        uint wm_0 = simd_max(threadBestBits_0);

#line 1884
        bool _S65 = simd_is_first();

#line 1884
        if(_S65)
        {

#line 1884
            live_0 = wm_0 > _S33;

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
            uint _S66 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1884
        }

#line 1884
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1884
        if(threadBestBits_0 > _S33)
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
        bool _S67 = simd_is_first();

#line 1884
        if(_S67)
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
            uint _S68 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_3)->stg_0)[(&kernelContext_3)->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

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
        if(_S64)
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
            *((&kernelContext_3)->entryPointParams_peakVal_0+_pr_0) = packed_float2(_S59) ;

#line 1884
        }

#line 1884
        break;
    }

#line 1890
    return;
}
