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


#line 174 "mm_2048_refineItems.slang"
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


#line 614
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 616
    float2 t1_0 = *a_1 - *c_0;

#line 616
    float2 t2_0 = *b_2 + *d_0;

#line 616
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 618
    *b_2 = t1_0 + j3_0;

#line 618
    *c_0 = t0_0 - t2_0;

#line 618
    *d_0 = t1_0 - j3_0;
    return;
}


#line 329
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 329
    float _S7 = a_2.x;

#line 329
    float _S8 = b_3.x;

#line 329
    float _S9 = a_2.y;

#line 329
    float _S10 = b_3.y;

#line 329
    return float2(_S7 * _S8 - _S9 * _S10, _S7 * _S10 + _S9 * _S8);
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
        uint _S11 = 4U * k2_0;

#line 662
        r4_0(&(*r_0)[_S11], &(*r_0)[_S11 + 1U], &(*r_0)[_S11 + 2U], &(*r_0)[_S11 + 3U]);

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


#line 76 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S12 = ((MF_ACCURATE_TRIG));

#line 79
    return _S12;
}


#line 103
float2 mfTwiddle_0(float angle_0)
{

#line 81
    uint _S13 = mfAccurateTrigFlag_0();

#line 105
    if(_S13 == 0U)
    {

#line 106
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S14 = float(quadrant_0);
    float x_0 = angle_0 - _S14 * 1.57079625129699707f - _S14 * 7.54978941586159635e-08f;
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


#line 331 "mm_2048_refineItems.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S15 = max(TB_0, 1U);

#line 333
    uint j_0 = d_1 / _S15;

#line 333
    uint m_0 = d_1 % _S15;

#line 333
    uint _S16;
    if(TB_0 <= 16U)
    {

#line 334
        _S16 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 334
    }
    else
    {

#line 334
        _S16 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 334
    }

#line 334
    return _S16;
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


#line 318 "mm_2048_refineItems.slang"
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
    array<uint, int(4096)> threadgroup* stg_0;
};


#line 318
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 318
    uint _S17 = 2U * i_1;

#line 318
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S17] = (as_type<uint>((v_0.x)));

#line 318
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S17 + 1U] = (as_type<uint>((v_0.y)));

#line 318
    return;
}


#line 319
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 319
    uint _S18 = 2U * i_2;

#line 319
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S18]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S18 + 1U]))));
}


#line 634
void dft8_0(array<float2, int(16)> thread* r_1, uint o_0)
{


    thread array<float2, int(8)> b_4;

#line 638
    uint s_1 = 1U;
    for(;;)
    {

#line 639
        if(s_1 < 8U)
        {
        }
        else
        {

#line 639
            break;
        }

#line 639
        uint j_1 = 0U;
        for(;;)
        {

#line 640
            if(j_1 < 4U)
            {
            }
            else
            {

#line 640
                break;
            }

#line 641
            uint k_0 = j_1 & (s_1 - 1U);

#line 641
            uint base_0 = (j_1 - k_0) << 1U;

            float2 w_0 = mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_1));
            uint _S19 = o_0 + j_1;

#line 644
            float2 t_6 = cmul_0(w_0, (*r_1)[_S19 + 4U]);
            uint _S20 = base_0 + k_0;

#line 645
            b_4[_S20] = (*r_1)[_S19] + t_6;

#line 645
            b_4[_S20 + s_1] = (*r_1)[_S19] - t_6;

#line 640
            j_1 = j_1 + 1U;

#line 640
        }

#line 640
        uint i_3 = 0U;

#line 647
        for(;;)
        {

#line 647
            if(i_3 < 8U)
            {
            }
            else
            {

#line 647
                break;
            }

#line 647
            (*r_1)[o_0 + i_3] = b_4[i_3];

#line 647
            i_3 = i_3 + 1U;

#line 647
        }

#line 639
        s_1 = s_1 << 1U;

#line 639
    }

#line 649
    return;
}


#line 753
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 753
    uint b_5 = 0U;

#line 761
    for(;;)
    {

#line 761
        if(b_5 < 2U)
        {
        }
        else
        {

#line 761
            break;
        }

#line 761
        dft8_0(r_2, b_5 * 8U);

#line 761
        b_5 = b_5 + 1U;

#line 761
    }



    return;
}


#line 881
uint lgOf_0(uint i_4)
{

#line 881
    uint _S21;

#line 881
    if(i_4 < 2U)
    {

#line 881
        _S21 = 4U;

#line 881
    }
    else
    {

#line 881
        if(i_4 == 2U)
        {

#line 881
            _S21 = 3U;

#line 881
        }
        else
        {

#line 881
            _S21 = 1U;

#line 881
        }

#line 881
    }

#line 881
    return _S21;
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


#line 2321
[[kernel]] void refineItems(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_items_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]])
{

#line 2321
    uint k2_1;

#line 2321
    uint _S22;

#line 2321
    uint _S23;

#line 2321
    uint _S24;

#line 2321
    uint d_2;

#line 2321
    uint j_2;

#line 2321
    uint d_3;

#line 2321
    uint m0_0;

#line 2321
    uint s0_0;

#line 2321
    uint m1_0;

#line 2321
    bool _S25;

#line 2321
    bool _S26;

#line 2321
    bool _S27;

#line 2321
    bool _S28;

#line 2321
    bool _S29;

#line 2321
    bool _S30;

#line 2321
    bool _S31;

#line 2321
    thread KernelContext_0 kernelContext_2;

#line 2321
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2321
    (&kernelContext_2)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2321
    (&kernelContext_2)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2321
    (&kernelContext_2)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2321
    (&kernelContext_2)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2321
    (&kernelContext_2)->entryPointParams_items_0 = entryPointParams_items_1;

#line 2321
    (&kernelContext_2)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2321
    threadgroup array<uint, int(4096)> stg_1;

#line 2321
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2321
    (&kernelContext_2)->_binPhase_0 = 0U;

#line 2330
    uint _S32 = entryPointParams_count_1[int(0)];

#line 2330
    uint i_5 = gid_0.x;
    for(;;)
    {

#line 2331
        if(i_5 < _S32)
        {
        }
        else
        {

#line 2331
            break;
        }

#line 2332
        (&kernelContext_2)->_stgBase_0 = 0U;
        uint _S33 = 6U * i_5;

#line 2333
        uint d_4 = (&kernelContext_2)->entryPointParams_items_0[_S33];

#line 2333
        uint t_7 = (&kernelContext_2)->entryPointParams_items_0[_S33 + 1U];
        (&kernelContext_2)->_binPhase_0 = (&kernelContext_2)->entryPointParams_items_0[_S33 + 5U];
        uint _S34 = d_4 * (&kernelContext_2)->entryPointParams_0->ntmpl_0 + t_7;

#line 2335
        uint _S35 = (&kernelContext_2)->entryPointParams_items_0[_S33 + 4U];

#line 2335
        uint _S36 = lid_0.x;
        uint _S37 = (&kernelContext_2)->entryPointParams_items_0[_S33 + 2U];

#line 2336
        uint _S38 = (&kernelContext_2)->entryPointParams_items_0[_S33 + 3U];

#line 2336
        uint _S39 = (&kernelContext_2)->entryPointParams_0->ntmpl_0;

#line 2336
        uint _S40 = (&kernelContext_2)->entryPointParams_0->binsize_0;

#line 2336
        int _S41 = (&kernelContext_2)->entryPointParams_0->binShift_0;

#line 2336
        uint _S42 = (&kernelContext_2)->entryPointParams_0->nbins_0;

#line 2336
        uint _S43 = (&kernelContext_2)->entryPointParams_0->thrBits_0;

#line 2335
        for(;;)
        {

#line 2335
            (&kernelContext_2)->_tid_0 = _S36;

#line 2335
            uint _S44 = _S34 / _S39;

#line 2335
            uint _S45 = _S34 % _S39;

#line 2335
            thread array<float2, int(16)> r_3;

#line 2335
            uint n2_0 = 0U;

#line 2335
            for(;;)
            {

#line 2335
                if(n2_0 < 16U)
                {
                }
                else
                {

#line 2335
                    break;
                }

#line 2335
                uint idx_0 = _S36 + 128U * n2_0;

#line 2335
                uint _S46 = mfDataStrideFlag_0();

#line 2335
                if(_S46 != 0U)
                {

#line 2335
                    uint _S47 = mfDataStrideFlag_0();

#line 2335
                    k2_1 = _S47;

#line 2335
                }
                else
                {

#line 2335
                    k2_1 = 2048U;

#line 2335
                }

#line 2335
                r_3[n2_0] = cmulConj_0(cload_0((&kernelContext_2)->entryPointParams_data_0, _S44 * k2_1 + idx_0), cload_0((&kernelContext_2)->entryPointParams_tmpl_0, _S45 * 2048U + idx_0));

#line 2335
                n2_0 = n2_0 + 1U;

#line 2335
            }

#line 2335
            for(;;)
            {

#line 2335
                for(;;)
                {

#line 2335
                    for(;;)
                    {

#line 2335
                        for(;;)
                        {

#line 2335
                            uint lgTB_0 = firstbithigh_0(128U);

#line 2335
                            _S22 = lgTB_0;

#line 2335
                            uint lgLn_0 = firstbithigh_0(2048U);

#line 2335
                            uint blk_1 = _S36 >> lgTB_0;

#line 2335
                            uint lane_1 = _S36 & 127U;

#line 2335
                            dft16_0(&r_3);

#line 2335
                            float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 2048.0f);

#line 2335
                            float _S48 = tw_0.x;

#line 2335
                            float _S49 = tw_0.y;

#line 2335
                            k2_1 = 0U;

#line 2335
                            float cr_0 = 1.0f;

#line 2335
                            float ci_0 = 0.0f;

#line 2335
                            for(;;)
                            {

#line 2335
                                if(k2_1 < 16U)
                                {
                                }
                                else
                                {

#line 2335
                                    break;
                                }

#line 2335
                                r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2335
                                float nr_0 = cr_0 * _S48 - ci_0 * _S49;

#line 2335
                                float _S50 = cr_0 * _S49 + ci_0 * _S48;

#line 2335
                                k2_1 = k2_1 + 1U;

#line 2335
                                cr_0 = nr_0;

#line 2335
                                ci_0 = _S50;

#line 2335
                            }

#line 2335
                            uint per_1 = 16U / max(128U, 1U);

#line 2335
                            uint _S51 = max(8U, 1U);

#line 2335
                            _S23 = _S51;

#line 2335
                            uint blk2_1 = _S36 / _S51;

#line 2335
                            uint lane2_1 = _S36 % _S51;

#line 2335
                            for(;;)
                            {

#line 2335
                                thread array<float2, int(16)> out_0;

#line 2335
                                uint z_1 = 0U;

#line 2335
                                for(;;)
                                {

#line 2335
                                    if(z_1 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2335
                                        break;
                                    }

#line 2335
                                    out_0[z_1] = float2(0.0f, 0.0f);

#line 2335
                                    z_1 = z_1 + 1U;

#line 2335
                                }

#line 2335
                                uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2335
                                _S24 = spanMask_0;

#line 2335
                                uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2335
                                uint p0_0 = computeWant_0(0U, 128U, 2048U, blk_1, lane_1, per_1, _S51, 128U, blk2_1, lane2_1);

#line 2335
                                uint _S52 = p0_0 & lenMask_0;

#line 2335
                                uint _S53 = (_S52 >> lgTB_0) * 128U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S52 & spanMask_0);

#line 2335
                                uint c_2 = 0U;

#line 2335
                                for(;;)
                                {

#line 2335
                                    if(c_2 < 1U)
                                    {
                                    }
                                    else
                                    {

#line 2335
                                        break;
                                    }

#line 2335
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2335
                                    j_2 = 0U;

#line 2335
                                    for(;;)
                                    {

#line 2335
                                        if(j_2 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2335
                                            break;
                                        }

#line 2335
                                        stgPut_0(j_2 * 128U + (&kernelContext_2)->_tid_0, r_3[c_2 * 16U + j_2], &kernelContext_2);

#line 2335
                                        j_2 = j_2 + 1U;

#line 2335
                                    }

#line 2335
                                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2335
                                    d_2 = 0U;

#line 2335
                                    for(;;)
                                    {

#line 2335
                                        if(d_2 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2335
                                            break;
                                        }

#line 2335
                                        uint pz_0 = computeWant_0(d_2, 128U, 2048U, 0U, 0U, per_1, _S51, 128U, 0U, 0U);

#line 2335
                                        uint _S54 = pz_0 & lenMask_0;

#line 2335
                                        uint az_0 = (_S54 >> lgTB_0) * 128U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S54 & spanMask_0);

#line 2335
                                        float2 _S55 = stgGet_0(_S53 + az_0 - c_2 * 16U * 128U, &kernelContext_2);

#line 2335
                                        out_0[d_2] = _S55;

#line 2335
                                        d_2 = d_2 + 1U;

#line 2335
                                    }

#line 2335
                                    c_2 = c_2 + 1U;

#line 2335
                                }

#line 2335
                                d_2 = 0U;

#line 2335
                                for(;;)
                                {

#line 2335
                                    if(d_2 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2335
                                        break;
                                    }

#line 2335
                                    r_3[d_2] = out_0[d_2];

#line 2335
                                    d_2 = d_2 + 1U;

#line 2335
                                }

#line 2335
                                break;
                            }

#line 2335
                            break;
                        }

#line 2335
                        break;
                    }

#line 2335
                    for(;;)
                    {

#line 2335
                        for(;;)
                        {

#line 2335
                            uint lgTB_1 = firstbithigh_0(8U);

#line 2335
                            uint blk_2 = _S36 >> lgTB_1;

#line 2335
                            uint lane_2 = _S36 & 7U;

#line 2335
                            dft16_0(&r_3);

#line 2335
                            float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 128.0f);

#line 2335
                            float _S56 = tw_1.x;

#line 2335
                            float _S57 = tw_1.y;

#line 2335
                            uint k2_2 = 0U;

#line 2335
                            float cr_1 = 1.0f;

#line 2335
                            float ci_1 = 0.0f;

#line 2335
                            for(;;)
                            {

#line 2335
                                if(k2_2 < 16U)
                                {
                                }
                                else
                                {

#line 2335
                                    break;
                                }

#line 2335
                                r_3[k2_2] = cmul_0(r_3[k2_2], float2(cr_1, ci_1));

#line 2335
                                float nr_1 = cr_1 * _S56 - ci_1 * _S57;

#line 2335
                                float _S58 = cr_1 * _S57 + ci_1 * _S56;

#line 2335
                                k2_2 = k2_2 + 1U;

#line 2335
                                cr_1 = nr_1;

#line 2335
                                ci_1 = _S58;

#line 2335
                            }

#line 2335
                            uint per_2 = 16U / _S23;

#line 2335
                            uint _S59 = max(0U, 1U);

#line 2335
                            uint blk2_2 = _S36 / _S59;

#line 2335
                            uint lane2_2 = _S36 % _S59;

#line 2335
                            for(;;)
                            {

#line 2335
                                thread array<float2, int(16)> out_1;

#line 2335
                                uint z_2 = 0U;

#line 2335
                                for(;;)
                                {

#line 2335
                                    if(z_2 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2335
                                        break;
                                    }

#line 2335
                                    out_1[z_2] = float2(0.0f, 0.0f);

#line 2335
                                    z_2 = z_2 + 1U;

#line 2335
                                }

#line 2335
                                uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2335
                                uint p0_1 = computeWant_0(0U, 8U, 128U, blk_2, lane_2, per_2, _S59, 8U, blk2_2, lane2_2);

#line 2335
                                uint _S60 = p0_1 & _S24;

#line 2335
                                uint _S61 = (_S60 >> lgTB_1) * 128U + ((p0_1 >> _S22) << lgTB_1) + (_S60 & spanMask_1);

#line 2335
                                uint c_3 = 0U;

#line 2335
                                for(;;)
                                {

#line 2335
                                    if(c_3 < 1U)
                                    {
                                    }
                                    else
                                    {

#line 2335
                                        break;
                                    }

#line 2335
                                    bool _S62 = c_3 == 0U;

#line 2335
                                    if(!_S62)
                                    {

#line 2335
                                        simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2335
                                    }
                                    else
                                    {

#line 2335
                                        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2335
                                    }

#line 2335
                                    j_2 = 0U;

#line 2335
                                    for(;;)
                                    {

#line 2335
                                        if(j_2 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2335
                                            break;
                                        }

#line 2335
                                        stgPut_0(j_2 * 128U + (&kernelContext_2)->_tid_0, r_3[c_3 * 16U + j_2], &kernelContext_2);

#line 2335
                                        j_2 = j_2 + 1U;

#line 2335
                                    }

#line 2335
                                    simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 2335
                                    d_3 = 0U;

#line 2335
                                    for(;;)
                                    {

#line 2335
                                        if(d_3 < 16U)
                                        {
                                        }
                                        else
                                        {

#line 2335
                                            break;
                                        }

#line 2335
                                        uint pz_1 = computeWant_0(d_3, 8U, 128U, 0U, 0U, per_2, _S59, 8U, 0U, 0U);

#line 2335
                                        uint _S63 = pz_1 & _S24;

#line 2335
                                        uint az_1 = (_S63 >> lgTB_1) * 128U + ((pz_1 >> _S22) << lgTB_1) + (_S63 & spanMask_1);

#line 2335
                                        float2 _S64 = stgGet_0(_S61 + az_1 - c_3 * 16U * 128U, &kernelContext_2);

#line 2335
                                        out_1[d_3] = _S64;

#line 2335
                                        d_3 = d_3 + 1U;

#line 2335
                                    }

#line 2335
                                    c_3 = c_3 + 1U;

#line 2335
                                }

#line 2335
                                j_2 = 0U;

#line 2335
                                for(;;)
                                {

#line 2335
                                    if(j_2 < 16U)
                                    {
                                    }
                                    else
                                    {

#line 2335
                                        break;
                                    }

#line 2335
                                    r_3[j_2] = out_1[j_2];

#line 2335
                                    j_2 = j_2 + 1U;

#line 2335
                                }

#line 2335
                                break;
                            }

#line 2335
                            break;
                        }

#line 2335
                        break;
                    }

#line 2335
                    break;
                }

#line 2335
                innermost_0(&r_3);

#line 2335
                break;
            }

#line 2335
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2335
            uint s0_1;

#line 2335
            uint m1_1;

#line 2335
            uint s1_0;

#line 2335
            uint i_6;

#line 2335
            uint m2_0;

#line 2335
            uint s2_0;

#line 2335
            uint m3_0;

#line 2335
            uint s3_0;

#line 2335
            uint b_6;

#line 2335
            bool isCand_0;

#line 2335
            if(_S42 <= 4U)
            {

#line 2335
                if(_S36 < 4U)
                {

#line 2335
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + _S36] = _S43;

#line 2335
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U + _S36] = 4294967295U;

#line 2335
                }

#line 2335
                float2 _S65 = float2(0.0f, 0.0f);

#line 2335
                i_6 = 0U;

#line 2335
                d_3 = _S43;

#line 2335
                s0_1 = 4294967295U;

#line 2335
                float2 v0_0 = _S65;

#line 2335
                m1_1 = _S43;

#line 2335
                s1_0 = 4294967295U;

#line 2335
                float2 v1_0 = _S65;

#line 2335
                m2_0 = _S43;

#line 2335
                s2_0 = 4294967295U;

#line 2335
                float2 v2_0 = _S65;

#line 2335
                m3_0 = _S43;

#line 2335
                s3_0 = 4294967295U;

#line 2335
                float2 v3_0 = _S65;

#line 2335
                for(;;)
                {

#line 2335
                    if(i_6 < 16U)
                    {
                    }
                    else
                    {

#line 2335
                        break;
                    }

#line 2335
                    uint slot_1 = _S36 * 16U + i_6;

#line 2335
                    uint idx_1 = slotToIndex_0(slot_1);

#line 2335
                    if(idx_1 >= _S37)
                    {

#line 2335
                        isCand_0 = idx_1 < _S38;

#line 2335
                    }
                    else
                    {

#line 2335
                        isCand_0 = false;

#line 2335
                    }

#line 2335
                    if(isCand_0)
                    {

#line 2335
                        float rx_0 = r_3[i_6].x;

#line 2335
                        float ry_0 = r_3[i_6].y;

#line 2335
                        uint mag_0 = (as_type<uint>((rx_0 * rx_0 + ry_0 * ry_0)));

#line 2335
                        uint off_0 = idx_1 - _S37 + (&kernelContext_2)->_binPhase_0;

#line 2335
                        if(_S42 == 1U)
                        {

#line 2335
                            b_6 = 0U;

#line 2335
                        }
                        else
                        {

#line 2335
                            if(_S41 >= int(0))
                            {

#line 2335
                                b_6 = off_0 >> uint(_S41);

#line 2335
                            }
                            else
                            {

#line 2335
                                uint _S66 = off_0 / _S40;

#line 2335
                                b_6 = _S66;

#line 2335
                            }

#line 2335
                        }

#line 2335
                        if(b_6 == 0U)
                        {

#line 2335
                            _S25 = mag_0 > d_3;

#line 2335
                        }
                        else
                        {

#line 2335
                            _S25 = false;

#line 2335
                        }

#line 2335
                        float2 v0_1;

#line 2335
                        if(_S25)
                        {

#line 2335
                            float2 _S67 = float2(rx_0, ry_0);

#line 2335
                            m0_0 = mag_0;

#line 2335
                            s0_0 = slot_1;

#line 2335
                            v0_1 = _S67;

#line 2335
                        }
                        else
                        {

#line 2335
                            m0_0 = d_3;

#line 2335
                            s0_0 = s0_1;

#line 2335
                            v0_1 = v0_0;

#line 2335
                        }

#line 2335
                        if(_S42 >= 2U)
                        {

#line 2335
                            _S26 = b_6 == 1U;

#line 2335
                        }
                        else
                        {

#line 2335
                            _S26 = false;

#line 2335
                        }

#line 2335
                        if(_S26)
                        {

#line 2335
                            _S27 = mag_0 > m1_1;

#line 2335
                        }
                        else
                        {

#line 2335
                            _S27 = false;

#line 2335
                        }

#line 2335
                        uint s1_1;

#line 2335
                        float2 v1_1;

#line 2335
                        if(_S27)
                        {

#line 2335
                            float2 _S68 = float2(rx_0, ry_0);

#line 2335
                            m1_0 = mag_0;

#line 2335
                            s1_1 = slot_1;

#line 2335
                            v1_1 = _S68;

#line 2335
                        }
                        else
                        {

#line 2335
                            m1_0 = m1_1;

#line 2335
                            s1_1 = s1_0;

#line 2335
                            v1_1 = v1_0;

#line 2335
                        }

#line 2335
                        if(_S42 >= 3U)
                        {

#line 2335
                            _S28 = b_6 == 2U;

#line 2335
                        }
                        else
                        {

#line 2335
                            _S28 = false;

#line 2335
                        }

#line 2335
                        if(_S28)
                        {

#line 2335
                            _S29 = mag_0 > m2_0;

#line 2335
                        }
                        else
                        {

#line 2335
                            _S29 = false;

#line 2335
                        }

#line 2335
                        uint m2_1;

#line 2335
                        uint s2_1;

#line 2335
                        float2 v2_1;

#line 2335
                        if(_S29)
                        {

#line 2335
                            float2 _S69 = float2(rx_0, ry_0);

#line 2335
                            m2_1 = mag_0;

#line 2335
                            s2_1 = slot_1;

#line 2335
                            v2_1 = _S69;

#line 2335
                        }
                        else
                        {

#line 2335
                            m2_1 = m2_0;

#line 2335
                            s2_1 = s2_0;

#line 2335
                            v2_1 = v2_0;

#line 2335
                        }

#line 2335
                        if(_S42 >= 4U)
                        {

#line 2335
                            _S30 = b_6 == 3U;

#line 2335
                        }
                        else
                        {

#line 2335
                            _S30 = false;

#line 2335
                        }

#line 2335
                        if(_S30)
                        {

#line 2335
                            _S31 = mag_0 > m3_0;

#line 2335
                        }
                        else
                        {

#line 2335
                            _S31 = false;

#line 2335
                        }

#line 2335
                        uint m3_1;

#line 2335
                        uint s3_1;

#line 2335
                        float2 v3_1;

#line 2335
                        if(_S31)
                        {

#line 2335
                            float2 _S70 = float2(rx_0, ry_0);

#line 2335
                            m3_1 = mag_0;

#line 2335
                            s3_1 = slot_1;

#line 2335
                            v3_1 = _S70;

#line 2335
                        }
                        else
                        {

#line 2335
                            m3_1 = m3_0;

#line 2335
                            s3_1 = s3_0;

#line 2335
                            v3_1 = v3_0;

#line 2335
                        }

#line 2335
                        d_3 = m0_0;

#line 2335
                        m1_1 = m1_0;

#line 2335
                        m2_0 = m2_1;

#line 2335
                        m3_0 = m3_1;

#line 2335
                        s0_1 = s0_0;

#line 2335
                        s1_0 = s1_1;

#line 2335
                        s2_0 = s2_1;

#line 2335
                        s3_0 = s3_1;

#line 2335
                        v0_0 = v0_1;

#line 2335
                        v1_0 = v1_1;

#line 2335
                        v2_0 = v2_1;

#line 2335
                        v3_0 = v3_1;

#line 2335
                    }

#line 2335
                    i_6 = i_6 + 1U;

#line 2335
                }

#line 2335
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2335
                uint wm0_0 = simd_max(d_3);

#line 2335
                bool _S71 = simd_is_first();

#line 2335
                if(_S71)
                {

#line 2335
                    isCand_0 = wm0_0 > _S43;

#line 2335
                }
                else
                {

#line 2335
                    isCand_0 = false;

#line 2335
                }

#line 2335
                if(isCand_0)
                {

#line 2335
                    uint _S72 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0])), wm0_0, memory_order_relaxed);

#line 2335
                }

#line 2335
                bool _S73 = _S42 >= 2U;

#line 2335
                if(_S73)
                {

#line 2335
                    uint wm1_0 = simd_max(m1_1);

#line 2335
                    bool _S74 = simd_is_first();

#line 2335
                    if(_S74)
                    {

#line 2335
                        _S25 = wm1_0 > _S43;

#line 2335
                    }
                    else
                    {

#line 2335
                        _S25 = false;

#line 2335
                    }

#line 2335
                    if(_S25)
                    {

#line 2335
                        uint _S75 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 1U])), wm1_0, memory_order_relaxed);

#line 2335
                    }

#line 2335
                }

#line 2335
                bool _S76 = _S42 >= 3U;

#line 2335
                if(_S76)
                {

#line 2335
                    uint wm2_0 = simd_max(m2_0);

#line 2335
                    bool _S77 = simd_is_first();

#line 2335
                    if(_S77)
                    {

#line 2335
                        _S25 = wm2_0 > _S43;

#line 2335
                    }
                    else
                    {

#line 2335
                        _S25 = false;

#line 2335
                    }

#line 2335
                    if(_S25)
                    {

#line 2335
                        uint _S78 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 2U])), wm2_0, memory_order_relaxed);

#line 2335
                    }

#line 2335
                }

#line 2335
                bool _S79 = _S42 >= 4U;

#line 2335
                if(_S79)
                {

#line 2335
                    uint wm3_0 = simd_max(m3_0);

#line 2335
                    bool _S80 = simd_is_first();

#line 2335
                    if(_S80)
                    {

#line 2335
                        _S25 = wm3_0 > _S43;

#line 2335
                    }
                    else
                    {

#line 2335
                        _S25 = false;

#line 2335
                    }

#line 2335
                    if(_S25)
                    {

#line 2335
                        uint _S81 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 3U])), wm3_0, memory_order_relaxed);

#line 2335
                    }

#line 2335
                }

#line 2335
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2335
                if(s0_1 != 4294967295U)
                {

#line 2335
                    _S25 = d_3 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0];

#line 2335
                }
                else
                {

#line 2335
                    _S25 = false;

#line 2335
                }

#line 2335
                if(_S25)
                {

#line 2335
                    b_6 = s0_1;

#line 2335
                }
                else
                {

#line 2335
                    b_6 = 4294967295U;

#line 2335
                }

#line 2335
                if(_S73)
                {

#line 2335
                    _S26 = s1_0 != 4294967295U;

#line 2335
                }
                else
                {

#line 2335
                    _S26 = false;

#line 2335
                }

#line 2335
                if(_S26)
                {

#line 2335
                    _S27 = m1_1 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 1U];

#line 2335
                }
                else
                {

#line 2335
                    _S27 = false;

#line 2335
                }

#line 2335
                if(_S27)
                {

#line 2335
                    m0_0 = s1_0;

#line 2335
                }
                else
                {

#line 2335
                    m0_0 = 4294967295U;

#line 2335
                }

#line 2335
                if(_S76)
                {

#line 2335
                    _S28 = s2_0 != 4294967295U;

#line 2335
                }
                else
                {

#line 2335
                    _S28 = false;

#line 2335
                }

#line 2335
                if(_S28)
                {

#line 2335
                    _S29 = m2_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 2U];

#line 2335
                }
                else
                {

#line 2335
                    _S29 = false;

#line 2335
                }

#line 2335
                if(_S29)
                {

#line 2335
                    s0_0 = s2_0;

#line 2335
                }
                else
                {

#line 2335
                    s0_0 = 4294967295U;

#line 2335
                }

#line 2335
                if(_S79)
                {

#line 2335
                    _S30 = s3_0 != 4294967295U;

#line 2335
                }
                else
                {

#line 2335
                    _S30 = false;

#line 2335
                }

#line 2335
                if(_S30)
                {

#line 2335
                    _S31 = m3_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 3U];

#line 2335
                }
                else
                {

#line 2335
                    _S31 = false;

#line 2335
                }

#line 2335
                if(_S31)
                {

#line 2335
                    m1_0 = s3_0;

#line 2335
                }
                else
                {

#line 2335
                    m1_0 = 4294967295U;

#line 2335
                }

#line 2335
                uint ww0_0 = simd_min(b_6);

#line 2335
                bool _S82 = simd_is_first();

#line 2335
                bool _S83;

#line 2335
                if(_S82)
                {

#line 2335
                    _S83 = ww0_0 != 4294967295U;

#line 2335
                }
                else
                {

#line 2335
                    _S83 = false;

#line 2335
                }

#line 2335
                if(_S83)
                {

#line 2335
                    uint _S84 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U])), ww0_0, memory_order_relaxed);

#line 2335
                }

#line 2335
                bool _S85;

#line 2335
                if(_S73)
                {

#line 2335
                    uint ww1_0 = simd_min(m0_0);

#line 2335
                    bool _S86 = simd_is_first();

#line 2335
                    if(_S86)
                    {

#line 2335
                        _S85 = ww1_0 != 4294967295U;

#line 2335
                    }
                    else
                    {

#line 2335
                        _S85 = false;

#line 2335
                    }

#line 2335
                    if(_S85)
                    {

#line 2335
                        uint _S87 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 5U])), ww1_0, memory_order_relaxed);

#line 2335
                    }

#line 2335
                }

#line 2335
                if(_S76)
                {

#line 2335
                    uint ww2_0 = simd_min(s0_0);

#line 2335
                    bool _S88 = simd_is_first();

#line 2335
                    if(_S88)
                    {

#line 2335
                        _S85 = ww2_0 != 4294967295U;

#line 2335
                    }
                    else
                    {

#line 2335
                        _S85 = false;

#line 2335
                    }

#line 2335
                    if(_S85)
                    {

#line 2335
                        uint _S89 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 6U])), ww2_0, memory_order_relaxed);

#line 2335
                    }

#line 2335
                }

#line 2335
                if(_S79)
                {

#line 2335
                    uint ww3_0 = simd_min(m1_0);

#line 2335
                    bool _S90 = simd_is_first();

#line 2335
                    if(_S90)
                    {

#line 2335
                        _S85 = ww3_0 != 4294967295U;

#line 2335
                    }
                    else
                    {

#line 2335
                        _S85 = false;

#line 2335
                    }

#line 2335
                    if(_S85)
                    {

#line 2335
                        uint _S91 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 7U])), ww3_0, memory_order_relaxed);

#line 2335
                    }

#line 2335
                }

#line 2335
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2335
                uint baseOut_0 = _S35 * _S42;

#line 2335
                if(b_6 != 4294967295U)
                {

#line 2335
                    _S85 = b_6 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U];

#line 2335
                }
                else
                {

#line 2335
                    _S85 = false;

#line 2335
                }

#line 2335
                if(_S85)
                {

#line 2335
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+baseOut_0) = int(slotToIndex_0(b_6));

#line 2335
                    *((&kernelContext_2)->entryPointParams_peakVal_0+baseOut_0) = packed_float2(v0_0) ;

#line 2335
                }

#line 2335
                bool _S92;

#line 2335
                if(_S73)
                {

#line 2335
                    _S92 = m0_0 != 4294967295U;

#line 2335
                }
                else
                {

#line 2335
                    _S92 = false;

#line 2335
                }

#line 2335
                bool _S93;

#line 2335
                if(_S92)
                {

#line 2335
                    _S93 = m0_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 5U];

#line 2335
                }
                else
                {

#line 2335
                    _S93 = false;

#line 2335
                }

#line 2335
                if(_S93)
                {

#line 2335
                    uint _S94 = baseOut_0 + 1U;

#line 2335
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S94) = int(slotToIndex_0(m0_0));

#line 2335
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S94) = packed_float2(v1_0) ;

#line 2335
                }

#line 2335
                bool _S95;

#line 2335
                if(_S76)
                {

#line 2335
                    _S95 = s0_0 != 4294967295U;

#line 2335
                }
                else
                {

#line 2335
                    _S95 = false;

#line 2335
                }

#line 2335
                bool _S96;

#line 2335
                if(_S95)
                {

#line 2335
                    _S96 = s0_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 6U];

#line 2335
                }
                else
                {

#line 2335
                    _S96 = false;

#line 2335
                }

#line 2335
                if(_S96)
                {

#line 2335
                    uint _S97 = baseOut_0 + 2U;

#line 2335
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S97) = int(slotToIndex_0(s0_0));

#line 2335
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S97) = packed_float2(v2_0) ;

#line 2335
                }

#line 2335
                bool _S98;

#line 2335
                if(_S79)
                {

#line 2335
                    _S98 = m1_0 != 4294967295U;

#line 2335
                }
                else
                {

#line 2335
                    _S98 = false;

#line 2335
                }

#line 2335
                bool _S99;

#line 2335
                if(_S98)
                {

#line 2335
                    _S99 = m1_0 == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 7U];

#line 2335
                }
                else
                {

#line 2335
                    _S99 = false;

#line 2335
                }

#line 2335
                if(_S99)
                {

#line 2335
                    uint _S100 = baseOut_0 + 3U;

#line 2335
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S100) = int(slotToIndex_0(m1_0));

#line 2335
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S100) = packed_float2(v3_0) ;

#line 2335
                }

#line 2335
                bool _S101;

#line 2335
                if(_S36 < _S42)
                {

#line 2335
                    _S101 = ((*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + 4U + _S36]) == 4294967295U;

#line 2335
                }
                else
                {

#line 2335
                    _S101 = false;

#line 2335
                }

#line 2335
                if(_S101)
                {

#line 2335
                    uint _S102 = baseOut_0 + _S36;

#line 2335
                    *((&kernelContext_2)->entryPointParams_peakIdx_0+_S102) = int(-1);

#line 2335
                    *((&kernelContext_2)->entryPointParams_peakVal_0+_S102) = packed_float2(_S65) ;

#line 2335
                }

#line 2335
            }
            else
            {

#line 2335
                d_3 = _S36;

#line 2335
                for(;;)
                {

#line 2335
                    if(d_3 < _S42)
                    {
                    }
                    else
                    {

#line 2335
                        break;
                    }

#line 2335
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + d_3] = _S43;

#line 2335
                    d_3 = d_3 + 128U;

#line 2335
                }

#line 2335
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2335
                s0_1 = 0U;

#line 2335
                m1_1 = 0U;

#line 2335
                s1_0 = 0U;

#line 2335
                for(;;)
                {

#line 2335
                    if(s0_1 < 16U)
                    {
                    }
                    else
                    {

#line 2335
                        break;
                    }

#line 2335
                    uint idx_2 = slotToIndex_0(_S36 * 16U + s0_1);

#line 2335
                    if(idx_2 >= _S37)
                    {

#line 2335
                        isCand_0 = idx_2 < _S38;

#line 2335
                    }
                    else
                    {

#line 2335
                        isCand_0 = false;

#line 2335
                    }

#line 2335
                    if(isCand_0)
                    {

#line 2335
                        float rx_1 = r_3[s0_1].x;

#line 2335
                        float ry_1 = r_3[s0_1].y;

#line 2335
                        uint mag_1 = (as_type<uint>((rx_1 * rx_1 + ry_1 * ry_1)));

#line 2335
                        if(mag_1 > _S43)
                        {

#line 2335
                            uint off_1 = idx_2 - _S37 + (&kernelContext_2)->_binPhase_0;

#line 2335
                            if(_S41 >= int(0))
                            {

#line 2335
                                m2_0 = off_1 >> uint(_S41);

#line 2335
                            }
                            else
                            {

#line 2335
                                uint _S103 = off_1 / _S40;

#line 2335
                                m2_0 = _S103;

#line 2335
                            }

#line 2335
                            uint _S104 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0])), mag_1, memory_order_relaxed);

#line 2335
                            uint bit_0 = 1U << (s0_1 & 31U);

#line 2335
                            if(s0_1 < 32U)
                            {

#line 2335
                                i_6 = m1_1 | bit_0;

#line 2335
                                s2_0 = s1_0;

#line 2335
                            }
                            else
                            {

#line 2335
                                uint aboveHi_0 = s1_0 | bit_0;

#line 2335
                                i_6 = m1_1;

#line 2335
                                s2_0 = aboveHi_0;

#line 2335
                            }

#line 2335
                        }
                        else
                        {

#line 2335
                            i_6 = m1_1;

#line 2335
                            s2_0 = s1_0;

#line 2335
                        }

#line 2335
                    }
                    else
                    {

#line 2335
                        i_6 = m1_1;

#line 2335
                        s2_0 = s1_0;

#line 2335
                    }

#line 2335
                    s0_1 = s0_1 + 1U;

#line 2335
                    m1_1 = i_6;

#line 2335
                    s1_0 = s2_0;

#line 2335
                }

#line 2335
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2335
                if((m1_1 | s1_0) != 0U)
                {

#line 2335
                    i_6 = 0U;

#line 2335
                    m2_0 = 0U;

#line 2335
                    s2_0 = 0U;

#line 2335
                    for(;;)
                    {

#line 2335
                        if(i_6 < 16U)
                        {
                        }
                        else
                        {

#line 2335
                            break;
                        }

#line 2335
                        uint bit_1 = 1U << (i_6 & 31U);

#line 2335
                        bool _S105 = i_6 < 32U;

#line 2335
                        if(_S105)
                        {

#line 2335
                            isCand_0 = (m1_1 & bit_1) != 0U;

#line 2335
                        }
                        else
                        {

#line 2335
                            isCand_0 = (s1_0 & bit_1) != 0U;

#line 2335
                        }

#line 2335
                        if(isCand_0)
                        {

#line 2335
                            uint off_2 = slotToIndex_0(_S36 * 16U + i_6) - _S37 + (&kernelContext_2)->_binPhase_0;

#line 2335
                            if(_S41 >= int(0))
                            {

#line 2335
                                m3_0 = off_2 >> uint(_S41);

#line 2335
                            }
                            else
                            {

#line 2335
                                uint _S106 = off_2 / _S40;

#line 2335
                                m3_0 = _S106;

#line 2335
                            }

#line 2335
                            float rx_2 = r_3[i_6].x;

#line 2335
                            float ry_2 = r_3[i_6].y;

#line 2335
                            if((as_type<uint>((rx_2 * rx_2 + ry_2 * ry_2))) == (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m3_0])
                            {

#line 2335
                                if(_S105)
                                {

#line 2335
                                    s3_0 = m2_0 | bit_1;

#line 2335
                                    b_6 = s2_0;

#line 2335
                                }
                                else
                                {

#line 2335
                                    uint candHi_0 = s2_0 | bit_1;

#line 2335
                                    s3_0 = m2_0;

#line 2335
                                    b_6 = candHi_0;

#line 2335
                                }

#line 2335
                            }
                            else
                            {

#line 2335
                                s3_0 = m2_0;

#line 2335
                                b_6 = s2_0;

#line 2335
                            }

#line 2335
                        }
                        else
                        {

#line 2335
                            s3_0 = m2_0;

#line 2335
                            b_6 = s2_0;

#line 2335
                        }

#line 2335
                        i_6 = i_6 + 1U;

#line 2335
                        m2_0 = s3_0;

#line 2335
                        s2_0 = b_6;

#line 2335
                    }

#line 2335
                    s3_0 = m2_0;

#line 2335
                    b_6 = s2_0;

#line 2335
                }
                else
                {

#line 2335
                    s3_0 = 0U;

#line 2335
                    b_6 = 0U;

#line 2335
                }

#line 2335
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2335
                m3_0 = _S36;

#line 2335
                for(;;)
                {

#line 2335
                    if(m3_0 < _S42)
                    {
                    }
                    else
                    {

#line 2335
                        break;
                    }

#line 2335
                    (*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m3_0] = 4294967295U;

#line 2335
                    m3_0 = m3_0 + 128U;

#line 2335
                }

#line 2335
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2335
                bool _S107 = (s3_0 | b_6) != 0U;

#line 2335
                if(_S107)
                {

#line 2335
                    i_6 = 0U;

#line 2335
                    for(;;)
                    {

#line 2335
                        if(i_6 < 16U)
                        {
                        }
                        else
                        {

#line 2335
                            break;
                        }

#line 2335
                        uint bit_2 = 1U << (i_6 & 31U);

#line 2335
                        if(i_6 < 32U)
                        {

#line 2335
                            isCand_0 = (s3_0 & bit_2) != 0U;

#line 2335
                        }
                        else
                        {

#line 2335
                            isCand_0 = (b_6 & bit_2) != 0U;

#line 2335
                        }

#line 2335
                        if(isCand_0)
                        {

#line 2335
                            uint _S108 = _S36 * 16U + i_6;

#line 2335
                            uint off_3 = slotToIndex_0(_S108) - _S37 + (&kernelContext_2)->_binPhase_0;

#line 2335
                            if(_S41 >= int(0))
                            {

#line 2335
                                m2_0 = off_3 >> uint(_S41);

#line 2335
                            }
                            else
                            {

#line 2335
                                uint _S109 = off_3 / _S40;

#line 2335
                                m2_0 = _S109;

#line 2335
                            }

#line 2335
                            uint _S110 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0])), _S108, memory_order_relaxed);

#line 2335
                        }

#line 2335
                        i_6 = i_6 + 1U;

#line 2335
                    }

#line 2335
                }

#line 2335
                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2335
                if(_S107)
                {

#line 2335
                    i_6 = 0U;

#line 2335
                    for(;;)
                    {

#line 2335
                        if(i_6 < 16U)
                        {
                        }
                        else
                        {

#line 2335
                            break;
                        }

#line 2335
                        uint bit_3 = 1U << (i_6 & 31U);

#line 2335
                        if(i_6 < 32U)
                        {

#line 2335
                            isCand_0 = (s3_0 & bit_3) != 0U;

#line 2335
                        }
                        else
                        {

#line 2335
                            isCand_0 = (b_6 & bit_3) != 0U;

#line 2335
                        }

#line 2335
                        if(isCand_0)
                        {

#line 2335
                            uint _S111 = _S36 * 16U + i_6;

#line 2335
                            uint idx_3 = slotToIndex_0(_S111);

#line 2335
                            uint off_4 = idx_3 - _S37 + (&kernelContext_2)->_binPhase_0;

#line 2335
                            if(_S41 >= int(0))
                            {

#line 2335
                                m2_0 = off_4 >> uint(_S41);

#line 2335
                            }
                            else
                            {

#line 2335
                                uint _S112 = off_4 / _S40;

#line 2335
                                m2_0 = _S112;

#line 2335
                            }

#line 2335
                            if(((*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0]) == _S111)
                            {

#line 2335
                                uint o_1 = _S35 * _S42 + m2_0;

#line 2335
                                *((&kernelContext_2)->entryPointParams_peakIdx_0+o_1) = int(idx_3);

#line 2335
                                *((&kernelContext_2)->entryPointParams_peakVal_0+o_1) = packed_float2(float2(r_3[i_6].x, r_3[i_6].y)) ;

#line 2335
                            }

#line 2335
                        }

#line 2335
                        i_6 = i_6 + 1U;

#line 2335
                    }

#line 2335
                }

#line 2335
                m2_0 = _S36;

#line 2335
                for(;;)
                {

#line 2335
                    if(m2_0 < _S42)
                    {
                    }
                    else
                    {

#line 2335
                        break;
                    }

#line 2335
                    if(((*(&kernelContext_2)->stg_0)[(&kernelContext_2)->_stgBase_0 + m2_0]) == 4294967295U)
                    {

#line 2335
                        uint _S113 = _S35 * _S42 + m2_0;

#line 2335
                        *((&kernelContext_2)->entryPointParams_peakIdx_0+_S113) = int(-1);

#line 2335
                        *((&kernelContext_2)->entryPointParams_peakVal_0+_S113) = packed_float2(float2(0.0f, 0.0f)) ;

#line 2335
                    }

#line 2335
                    m2_0 = m2_0 + 128U;

#line 2335
                }

#line 2335
            }

#line 2335
            break;
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2331
        i_5 = i_5 + (&kernelContext_2)->entryPointParams_0->gridSize_0;

#line 2331
    }

#line 2340
    return;
}
