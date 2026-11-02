#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
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


#line 60 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S2 = ((MF_DATA_STRIDE));

#line 63
    return _S2;
}


#line 174 "mm_65536_refineItems_lds32.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 174
    return float2(*(b_0+i_0)) ;
}


#line 330
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 330
    float _S3 = a_0.x;

#line 330
    float _S4 = b_1.x;

#line 330
    float _S5 = a_0.y;

#line 330
    float _S6 = b_1.y;

#line 330
    return float2(_S3 * _S4 + _S5 * _S6, _S5 * _S4 - _S3 * _S6);
}


#line 616
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 618
    float2 t1_0 = *a_1 - *c_0;

#line 618
    float2 t2_0 = *b_2 + *d_0;

#line 618
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 620
    *b_2 = t1_0 + j3_0;

#line 620
    *c_0 = t0_0 - t2_0;

#line 620
    *d_0 = t1_0 - j3_0;
    return;
}


#line 76 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S7 = ((MF_ACCURATE_TRIG));

#line 79
    return _S7;
}


#line 103
float2 mfTwiddle_0(float angle_0)
{

#line 81
    uint _S8 = mfAccurateTrigFlag_0();

#line 105
    if(_S8 == 0U)
    {

#line 106
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S9 = float(quadrant_0);
    float x_0 = angle_0 - _S9 * 1.57079625129699707f - _S9 * 7.54978941586159635e-08f;
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


#line 329 "mm_65536_refineItems_lds32.slang"
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 329
    float _S10 = a_2.x;

#line 329
    float _S11 = b_3.x;

#line 329
    float _S12 = a_2.y;

#line 329
    float _S13 = b_3.y;

#line 329
    return float2(_S10 * _S11 - _S12 * _S13, _S10 * _S13 + _S12 * _S11);
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
        uint _S14 = 4U * k2_0;

#line 664
        r4_0(&(*r_0)[_S14], &(*r_0)[_S14 + 1U], &(*r_0)[_S14 + 2U], &(*r_0)[_S14 + 3U]);

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
            float2 _S15 = mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f);

#line 727
            b_4[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], _S15);

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
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S16 = max(TB_0, 1U);

#line 333
    uint j_1 = d_1 / _S16;

#line 333
    uint m_0 = d_1 % _S16;

#line 333
    uint _S17;
    if(TB_0 <= 64U)
    {

#line 334
        _S17 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 334
    }
    else
    {

#line 334
        _S17 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 334
    }

#line 334
    return _S17;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
    uint binsize_0;
    int binShift_0;
    uint nbins_0;
    uint thrBits_0;
    uint gridSize_0;
};


#line 318 "mm_65536_refineItems_lds32.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_items_0;
    uint device* entryPointParams_count_0;
    uint _stgBase_0;
    uint _binPhase_0;
    uint _tid_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 318
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 318
    uint _S18 = 2U * i_1;

#line 318
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S18] = (as_type<uint>((v_0.x)));

#line 318
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S18 + 1U] = (as_type<uint>((v_0.y)));

#line 318
    return;
}


#line 319
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 319
    uint _S19 = 2U * i_2;

#line 319
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S19]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S19 + 1U]))));
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
    uint _S20;

#line 883
    if(i_4 < 2U)
    {

#line 883
        _S20 = 6U;

#line 883
    }
    else
    {

#line 883
        if(i_4 == 2U)
        {

#line 883
            _S20 = 4U;

#line 883
        }
        else
        {

#line 883
            _S20 = 1U;

#line 883
        }

#line 883
    }

#line 883
    return _S20;
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


#line 2409
[[kernel]] void refineItems(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_items_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]])
{

#line 2409
    uint k2_1;

#line 2409
    uint _S21;

#line 2409
    uint _S22;

#line 2409
    uint _S23;

#line 2409
    uint d_2;

#line 2409
    uint j_2;

#line 2409
    bool isCand_0;

#line 2409
    uint d_3;

#line 2409
    uint m0_0;

#line 2409
    uint s0_0;

#line 2409
    uint m1_0;

#line 2409
    bool _S24;

#line 2409
    bool _S25;

#line 2409
    bool _S26;

#line 2409
    bool _S27;

#line 2409
    bool _S28;

#line 2409
    bool _S29;

#line 2409
    bool _S30;

#line 2409
    thread KernelContext_0 kernelContext_2;

#line 2409
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2409
    (&kernelContext_2)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2409
    (&kernelContext_2)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2409
    (&kernelContext_2)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2409
    (&kernelContext_2)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2409
    (&kernelContext_2)->entryPointParams_items_0 = entryPointParams_items_1;

#line 2409
    (&kernelContext_2)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2409
    threadgroup array<uint, int(8192)> stg_1;

#line 2409
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2409
    (&kernelContext_2)->_binPhase_0 = 0U;

#line 2418
    uint _S31 = entryPointParams_count_1[int(0)];

#line 2418
    uint i_5 = gid_0.x;
    for(;;)
    {

#line 2419
        if(i_5 < _S31)
        {
        }
        else
        {

#line 2419
            break;
        }

#line 2420
        (&kernelContext_2)->_stgBase_0 = 0U;
        uint _S32 = 6U * i_5;

#line 2421
        uint d_4 = (&kernelContext_2)->entryPointParams_items_0[_S32];

#line 2421
        uint t_6 = (&kernelContext_2)->entryPointParams_items_0[_S32 + 1U];
        (&kernelContext_2)->_binPhase_0 = (&kernelContext_2)->entryPointParams_items_0[_S32 + 5U];
        uint _S33 = d_4 * (&kernelContext_2)->entryPointParams_0->ntmpl_0 + t_6;

#line 2423
        uint _S34 = (&kernelContext_2)->entryPointParams_items_0[_S32 + 4U];

#line 2423
        uint _S35 = lid_0.x;
        uint _S36 = (&kernelContext_2)->entryPointParams_items_0[_S32 + 2U];

#line 2424
        uint _S37 = (&kernelContext_2)->entryPointParams_items_0[_S32 + 3U];

#line 2424
        uint _S38 = (&kernelContext_2)->entryPointParams_0->ntmpl_0;

#line 2424
        uint _S39 = (&kernelContext_2)->entryPointParams_0->binsize_0;

#line 2424
        int _S40 = (&kernelContext_2)->entryPointParams_0->binShift_0;

#line 2424
        uint _S41 = (&kernelContext_2)->entryPointParams_0->nbins_0;

#line 2424
        uint _S42 = (&kernelContext_2)->entryPointParams_0->thrBits_0;

#line 2423
        for(;;)
        {

#line 2423
            (&kernelContext_2)->_tid_0 = _S35;

#line 2423
            uint _S43 = _S33 / _S38;

#line 2423
            uint _S44 = _S33 % _S38;

#line 2423
            thread array<float2, int(64)> r_5;

#line 2423
            uint n2_0 = 0U;

#line 2423
            for(;;)
            {

#line 2423
                if(n2_0 < 64U)
                {
                }
                else
                {

#line 2423
                    break;
                }

#line 2423
                uint idx_0 = _S35 + 1024U * n2_0;

#line 2423
                uint _S45 = mfDataStrideFlag_0();

#line 2423
                if(_S45 != 0U)
                {

#line 2423
                    uint _S46 = mfDataStrideFlag_0();

#line 2423
                    k2_1 = _S46;

#line 2423
                }
                else
                {

#line 2423
                    k2_1 = 65536U;

#line 2423
                }

#line 2423
                r_5[n2_0] = cmulConj_0(cload_0((&kernelContext_2)->entryPointParams_data_0, _S43 * k2_1 + idx_0), cload_0((&kernelContext_2)->entryPointParams_tmpl_0, _S44 * 65536U + idx_0));

#line 2423
                n2_0 = n2_0 + 1U;

#line 2423
            }

#line 2423
            for(;;)
            {

#line 2423
                for(;;)
                {

#line 2423
                    for(;;)
                    {

#line 2423
                        for(;;)
                        {

#line 2423
                            uint lgTB_0 = firstbithigh_0(1024U);

#line 2423
                            _S21 = lgTB_0;

#line 2423
                            uint lgLn_0 = firstbithigh_0(65536U);

#line 2423
                            uint blk_1 = _S35 >> lgTB_0;

#line 2423
                            uint lane_1 = _S35 & 1023U;

#line 2423
                            dftR_0(&r_5);

#line 2423
                            float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 6.5536e+04f);

#line 2423
                            float _S47 = tw_0.x;

#line 2423
                            float _S48 = tw_0.y;

#line 2423
                            k2_1 = 0U;

#line 2423
                            float cr_0 = 1.0f;

#line 2423
                            float ci_0 = 0.0f;

#line 2423
                            for(;;)
                            {

#line 2423
                                if(k2_1 < 64U)
                                {
                                }
                                else
                                {

#line 2423
                                    break;
                                }

#line 2423
                                r_5[k2_1] = cmul_0(r_5[k2_1], float2(cr_0, ci_0));

#line 2423
                                float nr_0 = cr_0 * _S47 - ci_0 * _S48;

#line 2423
                                float _S49 = cr_0 * _S48 + ci_0 * _S47;

#line 2423
                                k2_1 = k2_1 + 1U;

#line 2423
                                cr_0 = nr_0;

#line 2423
                                ci_0 = _S49;

#line 2423
                            }

#line 2423
                            uint per_1 = 64U / max(1024U, 1U);

#line 2423
                            uint _S50 = max(16U, 1U);

#line 2423
                            _S22 = _S50;

#line 2423
                            uint blk2_1 = _S35 / _S50;

#line 2423
                            uint lane2_1 = _S35 % _S50;

#line 2423
                            for(;;)
                            {

#line 2423
                                thread array<float2, int(64)> out_0;

#line 2423
                                uint z_1 = 0U;

#line 2423
                                for(;;)
                                {

#line 2423
                                    if(z_1 < 64U)
                                    {
                                    }
                                    else
                                    {

#line 2423
                                        break;
                                    }

#line 2423
                                    out_0[z_1] = float2(0.0f, 0.0f);

#line 2423
                                    z_1 = z_1 + 1U;

#line 2423
                                }

#line 2423
                                uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2423
                                _S23 = spanMask_0;

#line 2423
                                uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2423
                                uint p0_0 = computeWant_0(0U, 1024U, 65536U, blk_1, lane_1, per_1, _S50, 1024U, blk2_1, lane2_1);

#line 2423
                                uint _S51 = p0_0 & lenMask_0;

#line 2423
                                uint _S52 = _S51 >> lgTB_0;

#line 2423
                                uint _S53 = _S52 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S51 & spanMask_0);

#line 2423
                                uint c_2 = 0U;

#line 2423
                                for(;;)
                                {

#line 2423
                                    if(c_2 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2423
                                        break;
                                    }

#line 2423
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2423
                                    j_2 = 0U;

#line 2423
                                    for(;;)
                                    {

#line 2423
                                        if(j_2 < 4U)
                                        {
                                        }
                                        else
                                        {

#line 2423
                                            break;
                                        }

#line 2423
                                        stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_5[c_2 * 4U + j_2], &kernelContext_2);

#line 2423
                                        j_2 = j_2 + 1U;

#line 2423
                                    }

#line 2423
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2423
                                    d_2 = 0U;

#line 2423
                                    for(;;)
                                    {

#line 2423
                                        if(d_2 < 64U)
                                        {
                                        }
                                        else
                                        {

#line 2423
                                            break;
                                        }

#line 2423
                                        uint pz_0 = computeWant_0(d_2, 1024U, 65536U, 0U, 0U, per_1, _S50, 1024U, 0U, 0U);

#line 2423
                                        uint _S54 = pz_0 & lenMask_0;

#line 2423
                                        uint iz_0 = _S54 >> lgTB_0;

#line 2423
                                        uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S54 & spanMask_0);

#line 2423
                                        uint i_6 = _S52 + iz_0;

#line 2423
                                        uint _S55 = c_2 * 4U;

#line 2423
                                        if(i_6 >= _S55)
                                        {

#line 2423
                                            isCand_0 = i_6 < ((c_2 + 1U) * 4U);

#line 2423
                                        }
                                        else
                                        {

#line 2423
                                            isCand_0 = false;

#line 2423
                                        }

#line 2423
                                        if(isCand_0)
                                        {

#line 2423
                                            float2 _S56 = stgGet_0(_S53 + az_0 - _S55 * 1024U, &kernelContext_2);

#line 2423
                                            out_0[d_2] = _S56;

#line 2423
                                        }

#line 2423
                                        d_2 = d_2 + 1U;

#line 2423
                                    }

#line 2423
                                    c_2 = c_2 + 1U;

#line 2423
                                }

#line 2423
                                d_2 = 0U;

#line 2423
                                for(;;)
                                {

#line 2423
                                    if(d_2 < 64U)
                                    {
                                    }
                                    else
                                    {

#line 2423
                                        break;
                                    }

#line 2423
                                    r_5[d_2] = out_0[d_2];

#line 2423
                                    d_2 = d_2 + 1U;

#line 2423
                                }

#line 2423
                                break;
                            }

#line 2423
                            break;
                        }

#line 2423
                        break;
                    }

#line 2423
                    for(;;)
                    {

#line 2423
                        for(;;)
                        {

#line 2423
                            uint lgTB_1 = firstbithigh_0(16U);

#line 2423
                            uint blk_2 = _S35 >> lgTB_1;

#line 2423
                            uint lane_2 = _S35 & 15U;

#line 2423
                            dftR_0(&r_5);

#line 2423
                            float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 2423
                            float _S57 = tw_1.x;

#line 2423
                            float _S58 = tw_1.y;

#line 2423
                            uint k2_2 = 0U;

#line 2423
                            float cr_1 = 1.0f;

#line 2423
                            float ci_1 = 0.0f;

#line 2423
                            for(;;)
                            {

#line 2423
                                if(k2_2 < 64U)
                                {
                                }
                                else
                                {

#line 2423
                                    break;
                                }

#line 2423
                                r_5[k2_2] = cmul_0(r_5[k2_2], float2(cr_1, ci_1));

#line 2423
                                float nr_1 = cr_1 * _S57 - ci_1 * _S58;

#line 2423
                                float _S59 = cr_1 * _S58 + ci_1 * _S57;

#line 2423
                                k2_2 = k2_2 + 1U;

#line 2423
                                cr_1 = nr_1;

#line 2423
                                ci_1 = _S59;

#line 2423
                            }

#line 2423
                            uint per_2 = 64U / _S22;

#line 2423
                            uint _S60 = max(0U, 1U);

#line 2423
                            uint blk2_2 = _S35 / _S60;

#line 2423
                            uint lane2_2 = _S35 % _S60;

#line 2423
                            for(;;)
                            {

#line 2423
                                thread array<float2, int(64)> out_1;

#line 2423
                                uint z_2 = 0U;

#line 2423
                                for(;;)
                                {

#line 2423
                                    if(z_2 < 64U)
                                    {
                                    }
                                    else
                                    {

#line 2423
                                        break;
                                    }

#line 2423
                                    out_1[z_2] = float2(0.0f, 0.0f);

#line 2423
                                    z_2 = z_2 + 1U;

#line 2423
                                }

#line 2423
                                uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2423
                                uint p0_1 = computeWant_0(0U, 16U, 1024U, blk_2, lane_2, per_2, _S60, 16U, blk2_2, lane2_2);

#line 2423
                                uint _S61 = p0_1 & _S23;

#line 2423
                                uint _S62 = _S61 >> lgTB_1;

#line 2423
                                uint _S63 = _S62 * 1024U + ((p0_1 >> _S21) << lgTB_1) + (_S61 & spanMask_1);

#line 2423
                                uint c_3 = 0U;

#line 2423
                                for(;;)
                                {

#line 2423
                                    if(c_3 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2423
                                        break;
                                    }

#line 2423
                                    bool _S64 = c_3 == 0U;

#line 2423
                                    if(!_S64)
                                    {

#line 2423
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2423
                                    }
                                    else
                                    {

#line 2423
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2423
                                    }

#line 2423
                                    j_2 = 0U;

#line 2423
                                    for(;;)
                                    {

#line 2423
                                        if(j_2 < 4U)
                                        {
                                        }
                                        else
                                        {

#line 2423
                                            break;
                                        }

#line 2423
                                        stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_5[c_3 * 4U + j_2], &kernelContext_2);

#line 2423
                                        j_2 = j_2 + 1U;

#line 2423
                                    }

#line 2423
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2423
                                    d_3 = 0U;

#line 2423
                                    for(;;)
                                    {

#line 2423
                                        if(d_3 < 64U)
                                        {
                                        }
                                        else
                                        {

#line 2423
                                            break;
                                        }

#line 2423
                                        uint pz_1 = computeWant_0(d_3, 16U, 1024U, 0U, 0U, per_2, _S60, 16U, 0U, 0U);

#line 2423
                                        uint _S65 = pz_1 & _S23;

#line 2423
                                        uint iz_1 = _S65 >> lgTB_1;

#line 2423
                                        uint az_1 = iz_1 * 1024U + ((pz_1 >> _S21) << lgTB_1) + (_S65 & spanMask_1);

#line 2423
                                        uint i_7 = _S62 + iz_1;

#line 2423
                                        uint _S66 = c_3 * 4U;

#line 2423
                                        if(i_7 >= _S66)
                                        {

#line 2423
                                            isCand_0 = i_7 < ((c_3 + 1U) * 4U);

#line 2423
                                        }
                                        else
                                        {

#line 2423
                                            isCand_0 = false;

#line 2423
                                        }

#line 2423
                                        if(isCand_0)
                                        {

#line 2423
                                            float2 _S67 = stgGet_0(_S63 + az_1 - _S66 * 1024U, &kernelContext_2);

#line 2423
                                            out_1[d_3] = _S67;

#line 2423
                                        }

#line 2423
                                        d_3 = d_3 + 1U;

#line 2423
                                    }

#line 2423
                                    c_3 = c_3 + 1U;

#line 2423
                                }

#line 2423
                                j_2 = 0U;

#line 2423
                                for(;;)
                                {

#line 2423
                                    if(j_2 < 64U)
                                    {
                                    }
                                    else
                                    {

#line 2423
                                        break;
                                    }

#line 2423
                                    r_5[j_2] = out_1[j_2];

#line 2423
                                    j_2 = j_2 + 1U;

#line 2423
                                }

#line 2423
                                break;
                            }

#line 2423
                            break;
                        }

#line 2423
                        break;
                    }

#line 2423
                    break;
                }

#line 2423
                innermost_0(&r_5);

#line 2423
                break;
            }

#line 2423
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2423
            uint s0_1;

#line 2423
            uint m1_1;

#line 2423
            uint s1_0;

#line 2423
            uint i_8;

#line 2423
            uint m2_0;

#line 2423
            uint s2_0;

#line 2423
            uint m3_0;

#line 2423
            uint s3_0;

#line 2423
            uint b_7;

#line 2423
            if(_S41 <= 4U)
            {

#line 2423
                if(_S35 < 4U)
                {

#line 2423
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + _S35] = _S42;

#line 2423
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U + _S35] = 4294967295U;

#line 2423
                }

#line 2423
                float2 _S68 = float2(0.0f, 0.0f);

#line 2423
                i_8 = 0U;

#line 2423
                d_3 = _S42;

#line 2423
                s0_1 = 4294967295U;

#line 2423
                float2 v0_0 = _S68;

#line 2423
                m1_1 = _S42;

#line 2423
                s1_0 = 4294967295U;

#line 2423
                float2 v1_0 = _S68;

#line 2423
                m2_0 = _S42;

#line 2423
                s2_0 = 4294967295U;

#line 2423
                float2 v2_0 = _S68;

#line 2423
                m3_0 = _S42;

#line 2423
                s3_0 = 4294967295U;

#line 2423
                float2 v3_0 = _S68;

#line 2423
                for(;;)
                {

#line 2423
                    if(i_8 < 64U)
                    {
                    }
                    else
                    {

#line 2423
                        break;
                    }

#line 2423
                    uint slot_1 = _S35 * 64U + i_8;

#line 2423
                    uint idx_1 = slotToIndex_0(slot_1);

#line 2423
                    if(idx_1 >= _S36)
                    {

#line 2423
                        isCand_0 = idx_1 < _S37;

#line 2423
                    }
                    else
                    {

#line 2423
                        isCand_0 = false;

#line 2423
                    }

#line 2423
                    if(isCand_0)
                    {

#line 2423
                        float rx_0 = r_5[i_8].x;

#line 2423
                        float ry_0 = r_5[i_8].y;

#line 2423
                        uint mag_0 = (as_type<uint>((rx_0 * rx_0 + ry_0 * ry_0)));

#line 2423
                        uint off_0 = idx_1 - _S36 + (&kernelContext_2)->_binPhase_0;

#line 2423
                        if(_S41 == 1U)
                        {

#line 2423
                            b_7 = 0U;

#line 2423
                        }
                        else
                        {

#line 2423
                            if(_S40 >= int(0))
                            {

#line 2423
                                b_7 = off_0 >> uint(_S40);

#line 2423
                            }
                            else
                            {

#line 2423
                                uint _S69 = off_0 / _S39;

#line 2423
                                b_7 = _S69;

#line 2423
                            }

#line 2423
                        }

#line 2423
                        if(b_7 == 0U)
                        {

#line 2423
                            _S24 = mag_0 > d_3;

#line 2423
                        }
                        else
                        {

#line 2423
                            _S24 = false;

#line 2423
                        }

#line 2423
                        float2 v0_1;

#line 2423
                        if(_S24)
                        {

#line 2423
                            float2 _S70 = float2(rx_0, ry_0);

#line 2423
                            m0_0 = mag_0;

#line 2423
                            s0_0 = slot_1;

#line 2423
                            v0_1 = _S70;

#line 2423
                        }
                        else
                        {

#line 2423
                            m0_0 = d_3;

#line 2423
                            s0_0 = s0_1;

#line 2423
                            v0_1 = v0_0;

#line 2423
                        }

#line 2423
                        if(_S41 >= 2U)
                        {

#line 2423
                            _S25 = b_7 == 1U;

#line 2423
                        }
                        else
                        {

#line 2423
                            _S25 = false;

#line 2423
                        }

#line 2423
                        if(_S25)
                        {

#line 2423
                            _S26 = mag_0 > m1_1;

#line 2423
                        }
                        else
                        {

#line 2423
                            _S26 = false;

#line 2423
                        }

#line 2423
                        uint s1_1;

#line 2423
                        float2 v1_1;

#line 2423
                        if(_S26)
                        {

#line 2423
                            float2 _S71 = float2(rx_0, ry_0);

#line 2423
                            m1_0 = mag_0;

#line 2423
                            s1_1 = slot_1;

#line 2423
                            v1_1 = _S71;

#line 2423
                        }
                        else
                        {

#line 2423
                            m1_0 = m1_1;

#line 2423
                            s1_1 = s1_0;

#line 2423
                            v1_1 = v1_0;

#line 2423
                        }

#line 2423
                        if(_S41 >= 3U)
                        {

#line 2423
                            _S27 = b_7 == 2U;

#line 2423
                        }
                        else
                        {

#line 2423
                            _S27 = false;

#line 2423
                        }

#line 2423
                        if(_S27)
                        {

#line 2423
                            _S28 = mag_0 > m2_0;

#line 2423
                        }
                        else
                        {

#line 2423
                            _S28 = false;

#line 2423
                        }

#line 2423
                        uint m2_1;

#line 2423
                        uint s2_1;

#line 2423
                        float2 v2_1;

#line 2423
                        if(_S28)
                        {

#line 2423
                            float2 _S72 = float2(rx_0, ry_0);

#line 2423
                            m2_1 = mag_0;

#line 2423
                            s2_1 = slot_1;

#line 2423
                            v2_1 = _S72;

#line 2423
                        }
                        else
                        {

#line 2423
                            m2_1 = m2_0;

#line 2423
                            s2_1 = s2_0;

#line 2423
                            v2_1 = v2_0;

#line 2423
                        }

#line 2423
                        if(_S41 >= 4U)
                        {

#line 2423
                            _S29 = b_7 == 3U;

#line 2423
                        }
                        else
                        {

#line 2423
                            _S29 = false;

#line 2423
                        }

#line 2423
                        if(_S29)
                        {

#line 2423
                            _S30 = mag_0 > m3_0;

#line 2423
                        }
                        else
                        {

#line 2423
                            _S30 = false;

#line 2423
                        }

#line 2423
                        uint m3_1;

#line 2423
                        uint s3_1;

#line 2423
                        float2 v3_1;

#line 2423
                        if(_S30)
                        {

#line 2423
                            float2 _S73 = float2(rx_0, ry_0);

#line 2423
                            m3_1 = mag_0;

#line 2423
                            s3_1 = slot_1;

#line 2423
                            v3_1 = _S73;

#line 2423
                        }
                        else
                        {

#line 2423
                            m3_1 = m3_0;

#line 2423
                            s3_1 = s3_0;

#line 2423
                            v3_1 = v3_0;

#line 2423
                        }

#line 2423
                        d_3 = m0_0;

#line 2423
                        m1_1 = m1_0;

#line 2423
                        m2_0 = m2_1;

#line 2423
                        m3_0 = m3_1;

#line 2423
                        s0_1 = s0_0;

#line 2423
                        s1_0 = s1_1;

#line 2423
                        s2_0 = s2_1;

#line 2423
                        s3_0 = s3_1;

#line 2423
                        v0_0 = v0_1;

#line 2423
                        v1_0 = v1_1;

#line 2423
                        v2_0 = v2_1;

#line 2423
                        v3_0 = v3_1;

#line 2423
                    }

#line 2423
                    i_8 = i_8 + 1U;

#line 2423
                }

#line 2423
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2423
                uint wm0_0 = simd_max(d_3);

#line 2423
                bool _S74 = simd_is_first();

#line 2423
                if(_S74)
                {

#line 2423
                    isCand_0 = wm0_0 > _S42;

#line 2423
                }
                else
                {

#line 2423
                    isCand_0 = false;

#line 2423
                }

#line 2423
                if(isCand_0)
                {

#line 2423
                    uint _S75 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0])), wm0_0, memory_order_relaxed);

#line 2423
                }

#line 2423
                bool _S76 = _S41 >= 2U;

#line 2423
                if(_S76)
                {

#line 2423
                    uint wm1_0 = simd_max(m1_1);

#line 2423
                    bool _S77 = simd_is_first();

#line 2423
                    if(_S77)
                    {

#line 2423
                        _S24 = wm1_0 > _S42;

#line 2423
                    }
                    else
                    {

#line 2423
                        _S24 = false;

#line 2423
                    }

#line 2423
                    if(_S24)
                    {

#line 2423
                        uint _S78 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 1U])), wm1_0, memory_order_relaxed);

#line 2423
                    }

#line 2423
                }

#line 2423
                bool _S79 = _S41 >= 3U;

#line 2423
                if(_S79)
                {

#line 2423
                    uint wm2_0 = simd_max(m2_0);

#line 2423
                    bool _S80 = simd_is_first();

#line 2423
                    if(_S80)
                    {

#line 2423
                        _S24 = wm2_0 > _S42;

#line 2423
                    }
                    else
                    {

#line 2423
                        _S24 = false;

#line 2423
                    }

#line 2423
                    if(_S24)
                    {

#line 2423
                        uint _S81 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 2U])), wm2_0, memory_order_relaxed);

#line 2423
                    }

#line 2423
                }

#line 2423
                bool _S82 = _S41 >= 4U;

#line 2423
                if(_S82)
                {

#line 2423
                    uint wm3_0 = simd_max(m3_0);

#line 2423
                    bool _S83 = simd_is_first();

#line 2423
                    if(_S83)
                    {

#line 2423
                        _S24 = wm3_0 > _S42;

#line 2423
                    }
                    else
                    {

#line 2423
                        _S24 = false;

#line 2423
                    }

#line 2423
                    if(_S24)
                    {

#line 2423
                        uint _S84 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 3U])), wm3_0, memory_order_relaxed);

#line 2423
                    }

#line 2423
                }

#line 2423
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2423
                if(s0_1 != 4294967295U)
                {

#line 2423
                    _S24 = d_3 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0];

#line 2423
                }
                else
                {

#line 2423
                    _S24 = false;

#line 2423
                }

#line 2423
                if(_S24)
                {

#line 2423
                    b_7 = s0_1;

#line 2423
                }
                else
                {

#line 2423
                    b_7 = 4294967295U;

#line 2423
                }

#line 2423
                if(_S76)
                {

#line 2423
                    _S25 = s1_0 != 4294967295U;

#line 2423
                }
                else
                {

#line 2423
                    _S25 = false;

#line 2423
                }

#line 2423
                if(_S25)
                {

#line 2423
                    _S26 = m1_1 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 1U];

#line 2423
                }
                else
                {

#line 2423
                    _S26 = false;

#line 2423
                }

#line 2423
                if(_S26)
                {

#line 2423
                    m0_0 = s1_0;

#line 2423
                }
                else
                {

#line 2423
                    m0_0 = 4294967295U;

#line 2423
                }

#line 2423
                if(_S79)
                {

#line 2423
                    _S27 = s2_0 != 4294967295U;

#line 2423
                }
                else
                {

#line 2423
                    _S27 = false;

#line 2423
                }

#line 2423
                if(_S27)
                {

#line 2423
                    _S28 = m2_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 2U];

#line 2423
                }
                else
                {

#line 2423
                    _S28 = false;

#line 2423
                }

#line 2423
                if(_S28)
                {

#line 2423
                    s0_0 = s2_0;

#line 2423
                }
                else
                {

#line 2423
                    s0_0 = 4294967295U;

#line 2423
                }

#line 2423
                if(_S82)
                {

#line 2423
                    _S29 = s3_0 != 4294967295U;

#line 2423
                }
                else
                {

#line 2423
                    _S29 = false;

#line 2423
                }

#line 2423
                if(_S29)
                {

#line 2423
                    _S30 = m3_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 3U];

#line 2423
                }
                else
                {

#line 2423
                    _S30 = false;

#line 2423
                }

#line 2423
                if(_S30)
                {

#line 2423
                    m1_0 = s3_0;

#line 2423
                }
                else
                {

#line 2423
                    m1_0 = 4294967295U;

#line 2423
                }

#line 2423
                uint ww0_0 = simd_min(b_7);

#line 2423
                bool _S85 = simd_is_first();

#line 2423
                bool _S86;

#line 2423
                if(_S85)
                {

#line 2423
                    _S86 = ww0_0 != 4294967295U;

#line 2423
                }
                else
                {

#line 2423
                    _S86 = false;

#line 2423
                }

#line 2423
                if(_S86)
                {

#line 2423
                    uint _S87 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U])), ww0_0, memory_order_relaxed);

#line 2423
                }

#line 2423
                bool _S88;

#line 2423
                if(_S76)
                {

#line 2423
                    uint ww1_0 = simd_min(m0_0);

#line 2423
                    bool _S89 = simd_is_first();

#line 2423
                    if(_S89)
                    {

#line 2423
                        _S88 = ww1_0 != 4294967295U;

#line 2423
                    }
                    else
                    {

#line 2423
                        _S88 = false;

#line 2423
                    }

#line 2423
                    if(_S88)
                    {

#line 2423
                        uint _S90 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 5U])), ww1_0, memory_order_relaxed);

#line 2423
                    }

#line 2423
                }

#line 2423
                if(_S79)
                {

#line 2423
                    uint ww2_0 = simd_min(s0_0);

#line 2423
                    bool _S91 = simd_is_first();

#line 2423
                    if(_S91)
                    {

#line 2423
                        _S88 = ww2_0 != 4294967295U;

#line 2423
                    }
                    else
                    {

#line 2423
                        _S88 = false;

#line 2423
                    }

#line 2423
                    if(_S88)
                    {

#line 2423
                        uint _S92 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 6U])), ww2_0, memory_order_relaxed);

#line 2423
                    }

#line 2423
                }

#line 2423
                if(_S82)
                {

#line 2423
                    uint ww3_0 = simd_min(m1_0);

#line 2423
                    bool _S93 = simd_is_first();

#line 2423
                    if(_S93)
                    {

#line 2423
                        _S88 = ww3_0 != 4294967295U;

#line 2423
                    }
                    else
                    {

#line 2423
                        _S88 = false;

#line 2423
                    }

#line 2423
                    if(_S88)
                    {

#line 2423
                        uint _S94 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 7U])), ww3_0, memory_order_relaxed);

#line 2423
                    }

#line 2423
                }

#line 2423
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2423
                uint baseOut_0 = _S34 * _S41;

#line 2423
                if(b_7 != 4294967295U)
                {

#line 2423
                    _S88 = b_7 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U];

#line 2423
                }
                else
                {

#line 2423
                    _S88 = false;

#line 2423
                }

#line 2423
                if(_S88)
                {

#line 2423
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+baseOut_0) = int(slotToIndex_0(b_7));

#line 2423
                    *((&kernelContext_2)->entryPointParams_peakVal_0+baseOut_0) = packed_float2(v0_0) ;

#line 2423
                }

#line 2423
                bool _S95;

#line 2423
                if(_S76)
                {

#line 2423
                    _S95 = m0_0 != 4294967295U;

#line 2423
                }
                else
                {

#line 2423
                    _S95 = false;

#line 2423
                }

#line 2423
                bool _S96;

#line 2423
                if(_S95)
                {

#line 2423
                    _S96 = m0_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 5U];

#line 2423
                }
                else
                {

#line 2423
                    _S96 = false;

#line 2423
                }

#line 2423
                if(_S96)
                {

#line 2423
                    uint _S97 = baseOut_0 + 1U;

#line 2423
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S97) = int(slotToIndex_0(m0_0));

#line 2423
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S97) = packed_float2(v1_0) ;

#line 2423
                }

#line 2423
                bool _S98;

#line 2423
                if(_S79)
                {

#line 2423
                    _S98 = s0_0 != 4294967295U;

#line 2423
                }
                else
                {

#line 2423
                    _S98 = false;

#line 2423
                }

#line 2423
                bool _S99;

#line 2423
                if(_S98)
                {

#line 2423
                    _S99 = s0_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 6U];

#line 2423
                }
                else
                {

#line 2423
                    _S99 = false;

#line 2423
                }

#line 2423
                if(_S99)
                {

#line 2423
                    uint _S100 = baseOut_0 + 2U;

#line 2423
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S100) = int(slotToIndex_0(s0_0));

#line 2423
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S100) = packed_float2(v2_0) ;

#line 2423
                }

#line 2423
                bool _S101;

#line 2423
                if(_S82)
                {

#line 2423
                    _S101 = m1_0 != 4294967295U;

#line 2423
                }
                else
                {

#line 2423
                    _S101 = false;

#line 2423
                }

#line 2423
                bool _S102;

#line 2423
                if(_S101)
                {

#line 2423
                    _S102 = m1_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 7U];

#line 2423
                }
                else
                {

#line 2423
                    _S102 = false;

#line 2423
                }

#line 2423
                if(_S102)
                {

#line 2423
                    uint _S103 = baseOut_0 + 3U;

#line 2423
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S103) = int(slotToIndex_0(m1_0));

#line 2423
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S103) = packed_float2(v3_0) ;

#line 2423
                }

#line 2423
                bool _S104;

#line 2423
                if(_S35 < _S41)
                {

#line 2423
                    _S104 = ((*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U + _S35]) == 4294967295U;

#line 2423
                }
                else
                {

#line 2423
                    _S104 = false;

#line 2423
                }

#line 2423
                if(_S104)
                {

#line 2423
                    uint _S105 = baseOut_0 + _S35;

#line 2423
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S105) = int(-1);

#line 2423
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S105) = packed_float2(_S68) ;

#line 2423
                }

#line 2423
            }
            else
            {

#line 2423
                d_3 = _S35;

#line 2423
                for(;;)
                {

#line 2423
                    if(d_3 < _S41)
                    {
                    }
                    else
                    {

#line 2423
                        break;
                    }

#line 2423
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + d_3] = _S42;

#line 2423
                    d_3 = d_3 + 1024U;

#line 2423
                }

#line 2423
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2423
                s0_1 = 0U;

#line 2423
                m1_1 = 0U;

#line 2423
                s1_0 = 0U;

#line 2423
                for(;;)
                {

#line 2423
                    if(s0_1 < 64U)
                    {
                    }
                    else
                    {

#line 2423
                        break;
                    }

#line 2423
                    uint idx_2 = slotToIndex_0(_S35 * 64U + s0_1);

#line 2423
                    if(idx_2 >= _S36)
                    {

#line 2423
                        isCand_0 = idx_2 < _S37;

#line 2423
                    }
                    else
                    {

#line 2423
                        isCand_0 = false;

#line 2423
                    }

#line 2423
                    if(isCand_0)
                    {

#line 2423
                        float rx_1 = r_5[s0_1].x;

#line 2423
                        float ry_1 = r_5[s0_1].y;

#line 2423
                        uint mag_1 = (as_type<uint>((rx_1 * rx_1 + ry_1 * ry_1)));

#line 2423
                        if(mag_1 > _S42)
                        {

#line 2423
                            uint off_1 = idx_2 - _S36 + (&kernelContext_2)->_binPhase_0;

#line 2423
                            if(_S40 >= int(0))
                            {

#line 2423
                                m2_0 = off_1 >> uint(_S40);

#line 2423
                            }
                            else
                            {

#line 2423
                                uint _S106 = off_1 / _S39;

#line 2423
                                m2_0 = _S106;

#line 2423
                            }

#line 2423
                            uint _S107 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0])), mag_1, memory_order_relaxed);

#line 2423
                            uint bit_0 = 1U << (s0_1 & 31U);

#line 2423
                            if(s0_1 < 32U)
                            {

#line 2423
                                i_8 = m1_1 | bit_0;

#line 2423
                                s2_0 = s1_0;

#line 2423
                            }
                            else
                            {

#line 2423
                                uint aboveHi_0 = s1_0 | bit_0;

#line 2423
                                i_8 = m1_1;

#line 2423
                                s2_0 = aboveHi_0;

#line 2423
                            }

#line 2423
                        }
                        else
                        {

#line 2423
                            i_8 = m1_1;

#line 2423
                            s2_0 = s1_0;

#line 2423
                        }

#line 2423
                    }
                    else
                    {

#line 2423
                        i_8 = m1_1;

#line 2423
                        s2_0 = s1_0;

#line 2423
                    }

#line 2423
                    s0_1 = s0_1 + 1U;

#line 2423
                    m1_1 = i_8;

#line 2423
                    s1_0 = s2_0;

#line 2423
                }

#line 2423
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2423
                if((m1_1 | s1_0) != 0U)
                {

#line 2423
                    i_8 = 0U;

#line 2423
                    m2_0 = 0U;

#line 2423
                    s2_0 = 0U;

#line 2423
                    for(;;)
                    {

#line 2423
                        if(i_8 < 64U)
                        {
                        }
                        else
                        {

#line 2423
                            break;
                        }

#line 2423
                        uint bit_1 = 1U << (i_8 & 31U);

#line 2423
                        bool _S108 = i_8 < 32U;

#line 2423
                        if(_S108)
                        {

#line 2423
                            isCand_0 = (m1_1 & bit_1) != 0U;

#line 2423
                        }
                        else
                        {

#line 2423
                            isCand_0 = (s1_0 & bit_1) != 0U;

#line 2423
                        }

#line 2423
                        if(isCand_0)
                        {

#line 2423
                            uint off_2 = slotToIndex_0(_S35 * 64U + i_8) - _S36 + (&kernelContext_2)->_binPhase_0;

#line 2423
                            if(_S40 >= int(0))
                            {

#line 2423
                                m3_0 = off_2 >> uint(_S40);

#line 2423
                            }
                            else
                            {

#line 2423
                                uint _S109 = off_2 / _S39;

#line 2423
                                m3_0 = _S109;

#line 2423
                            }

#line 2423
                            float rx_2 = r_5[i_8].x;

#line 2423
                            float ry_2 = r_5[i_8].y;

#line 2423
                            if((as_type<uint>((rx_2 * rx_2 + ry_2 * ry_2))) == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m3_0])
                            {

#line 2423
                                if(_S108)
                                {

#line 2423
                                    s3_0 = m2_0 | bit_1;

#line 2423
                                    b_7 = s2_0;

#line 2423
                                }
                                else
                                {

#line 2423
                                    uint candHi_0 = s2_0 | bit_1;

#line 2423
                                    s3_0 = m2_0;

#line 2423
                                    b_7 = candHi_0;

#line 2423
                                }

#line 2423
                            }
                            else
                            {

#line 2423
                                s3_0 = m2_0;

#line 2423
                                b_7 = s2_0;

#line 2423
                            }

#line 2423
                        }
                        else
                        {

#line 2423
                            s3_0 = m2_0;

#line 2423
                            b_7 = s2_0;

#line 2423
                        }

#line 2423
                        i_8 = i_8 + 1U;

#line 2423
                        m2_0 = s3_0;

#line 2423
                        s2_0 = b_7;

#line 2423
                    }

#line 2423
                    s3_0 = m2_0;

#line 2423
                    b_7 = s2_0;

#line 2423
                }
                else
                {

#line 2423
                    s3_0 = 0U;

#line 2423
                    b_7 = 0U;

#line 2423
                }

#line 2423
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2423
                m3_0 = _S35;

#line 2423
                for(;;)
                {

#line 2423
                    if(m3_0 < _S41)
                    {
                    }
                    else
                    {

#line 2423
                        break;
                    }

#line 2423
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m3_0] = 4294967295U;

#line 2423
                    m3_0 = m3_0 + 1024U;

#line 2423
                }

#line 2423
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2423
                bool _S110 = (s3_0 | b_7) != 0U;

#line 2423
                if(_S110)
                {

#line 2423
                    i_8 = 0U;

#line 2423
                    for(;;)
                    {

#line 2423
                        if(i_8 < 64U)
                        {
                        }
                        else
                        {

#line 2423
                            break;
                        }

#line 2423
                        uint bit_2 = 1U << (i_8 & 31U);

#line 2423
                        if(i_8 < 32U)
                        {

#line 2423
                            isCand_0 = (s3_0 & bit_2) != 0U;

#line 2423
                        }
                        else
                        {

#line 2423
                            isCand_0 = (b_7 & bit_2) != 0U;

#line 2423
                        }

#line 2423
                        if(isCand_0)
                        {

#line 2423
                            uint _S111 = _S35 * 64U + i_8;

#line 2423
                            uint off_3 = slotToIndex_0(_S111) - _S36 + (&kernelContext_2)->_binPhase_0;

#line 2423
                            if(_S40 >= int(0))
                            {

#line 2423
                                m2_0 = off_3 >> uint(_S40);

#line 2423
                            }
                            else
                            {

#line 2423
                                uint _S112 = off_3 / _S39;

#line 2423
                                m2_0 = _S112;

#line 2423
                            }

#line 2423
                            uint _S113 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0])), _S111, memory_order_relaxed);

#line 2423
                        }

#line 2423
                        i_8 = i_8 + 1U;

#line 2423
                    }

#line 2423
                }

#line 2423
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2423
                if(_S110)
                {

#line 2423
                    i_8 = 0U;

#line 2423
                    for(;;)
                    {

#line 2423
                        if(i_8 < 64U)
                        {
                        }
                        else
                        {

#line 2423
                            break;
                        }

#line 2423
                        uint bit_3 = 1U << (i_8 & 31U);

#line 2423
                        if(i_8 < 32U)
                        {

#line 2423
                            isCand_0 = (s3_0 & bit_3) != 0U;

#line 2423
                        }
                        else
                        {

#line 2423
                            isCand_0 = (b_7 & bit_3) != 0U;

#line 2423
                        }

#line 2423
                        if(isCand_0)
                        {

#line 2423
                            uint _S114 = _S35 * 64U + i_8;

#line 2423
                            uint idx_3 = slotToIndex_0(_S114);

#line 2423
                            uint off_4 = idx_3 - _S36 + (&kernelContext_2)->_binPhase_0;

#line 2423
                            if(_S40 >= int(0))
                            {

#line 2423
                                m2_0 = off_4 >> uint(_S40);

#line 2423
                            }
                            else
                            {

#line 2423
                                uint _S115 = off_4 / _S39;

#line 2423
                                m2_0 = _S115;

#line 2423
                            }

#line 2423
                            if(((*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0]) == _S114)
                            {

#line 2423
                                uint o_2 = _S34 * _S41 + m2_0;

#line 2423
                                *((&kernelContext_2)->entryPointParams_peakIdx_0+o_2) = int(idx_3);

#line 2423
                                *((&kernelContext_2)->entryPointParams_peakVal_0+o_2) = packed_float2(float2(r_5[i_8].x, r_5[i_8].y)) ;

#line 2423
                            }

#line 2423
                        }

#line 2423
                        i_8 = i_8 + 1U;

#line 2423
                    }

#line 2423
                }

#line 2423
                m2_0 = _S35;

#line 2423
                for(;;)
                {

#line 2423
                    if(m2_0 < _S41)
                    {
                    }
                    else
                    {

#line 2423
                        break;
                    }

#line 2423
                    if(((*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0]) == 4294967295U)
                    {

#line 2423
                        uint _S116 = _S34 * _S41 + m2_0;

#line 2423
                        *((&kernelContext_2)->entryPointParams_peakIdx_0+_S116) = int(-1);

#line 2423
                        *((&kernelContext_2)->entryPointParams_peakVal_0+_S116) = packed_float2(float2(0.0f, 0.0f)) ;

#line 2423
                    }

#line 2423
                    m2_0 = m2_0 + 1024U;

#line 2423
                }

#line 2423
            }

#line 2423
            break;
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2419
        i_5 = i_5 + (&kernelContext_2)->entryPointParams_0->gridSize_0;

#line 2419
    }

#line 2428
    return;
}
