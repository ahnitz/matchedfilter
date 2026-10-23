#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
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


#line 173 "mm_1024_fullCorrelation.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 173
    return float2(*(b_0+i_0)) ;
}


#line 323
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 323
    float _S2 = a_0.x;

#line 323
    float _S3 = b_1.x;

#line 323
    float _S4 = a_0.y;

#line 323
    float _S5 = b_1.y;

#line 323
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 528
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 530
    float2 t1_0 = *a_1 - *c_0;

#line 530
    float2 t2_0 = *b_2 + *d_0;

#line 530
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 532
    *b_2 = t1_0 + j3_0;

#line 532
    *c_0 = t0_0 - t2_0;

#line 532
    *d_0 = t1_0 - j3_0;
    return;
}


#line 322
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 322
    float _S6 = a_2.x;

#line 322
    float _S7 = b_3.x;

#line 322
    float _S8 = a_2.y;

#line 322
    float _S9 = b_3.y;

#line 322
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 564
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 571
    uint n1_0 = 0U;
    for(;;)
    {

#line 572
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 572
            break;
        }

#line 572
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 572
        n1_0 = n1_0 + 1U;

#line 572
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 573
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 573
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 574
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 574
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 575
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 575
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 575
    uint k2_0 = 0U;
    for(;;)
    {

#line 576
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 576
            break;
        }

#line 576
        uint _S10 = 4U * k2_0;

#line 576
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 576
        k2_0 = k2_0 + 1U;

#line 576
    }

    float2 t_0 = (*r_0)[int(1)];

#line 578
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 578
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 579
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 579
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 580
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 580
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 581
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 581
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 582
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 582
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 583
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 583
    (*r_0)[int(14)] = t_5;
    return;
}


#line 88 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S11 = ((MF_ACCURATE_TRIG));

#line 91
    return _S11;
}


#line 127
float2 mfTwiddle_0(float angle_0)
{

#line 93
    uint _S12 = mfAccurateTrigFlag_0();

#line 129
    if(_S12 == 0U)
    {

#line 130
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S13 = float(quadrant_0);
    float x_0 = angle_0 - _S13 * 1.57079625129699707f - _S13 * 7.54978941586159635e-08f;
    float z_0 = x_0 * x_0;
    float c_1 = 1.0f + z_0 * (-0.5f + z_0 * (0.0416666679084301f + z_0 * (-0.00138888892251998f + z_0 * (0.00002480158764229f + z_0 * -2.75573199814971304e-07f))));

    float s_0 = x_0 * (1.0f + z_0 * (-0.1666666716337204f + z_0 * (0.00833333376795053f + z_0 * (-0.0001984127011383f + z_0 * (2.75573188446287531e-06f + z_0 * -2.50521079436794025e-08f)))));


    switch(quadrant_0 & int(3))
    {
    case int(1):
        {

#line 143
            return float2(- s_0, c_1);
        }
    case int(2):
        {

#line 144
            return float2(- c_1, - s_0);
        }
    case int(3):
        {

#line 145
            return float2(s_0, - c_1);
        }
    default:
        {

#line 146
            return float2(c_1, s_0);
        }
    }

#line 146
}


#line 324 "mm_1024_fullCorrelation.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S14 = max(TB_0, 1U);

#line 326
    uint j_0 = d_1 / _S14;

#line 326
    uint m_0 = d_1 % _S14;

#line 326
    uint _S15;
    if(TB_0 <= 16U)
    {

#line 327
        _S15 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 327
    }
    else
    {

#line 327
        _S15 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 327
    }

#line 327
    return _S15;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
};


#line 311 "mm_1024_fullCorrelation.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 311
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 311
    uint _S16 = 2U * i_1;

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S16] = (as_type<uint>((v_0.x)));

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S16 + 1U] = (as_type<uint>((v_0.y)));

#line 311
    return;
}


#line 312
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 312
    uint _S17 = 2U * i_2;

#line 312
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S17]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S17 + 1U]))));
}


#line 753
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 754
    uint j_1;

#line 765
    thread array<float2, int(16)> out_0;

#line 765
    uint z_1 = 0U;
    for(;;)
    {

#line 766
        if(z_1 < 16U)
        {
        }
        else
        {

#line 766
            break;
        }

#line 766
        out_0[z_1] = float2(0.0f, 0.0f);

#line 766
        z_1 = z_1 + 1U;

#line 766
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S18 = p0_0 & lenMask_0;

#line 772
    uint _S19 = (_S18 >> lgSpan_0) * 64U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S18 & spanMask_0);

#line 772
    uint c_2 = 0U;

    for(;;)
    {

#line 774
        if(c_2 < 1U)
        {
        }
        else
        {

#line 774
            break;
        }

#line 775
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 775
        j_1 = 0U;
        for(;;)
        {

#line 776
            if(j_1 < 16U)
            {
            }
            else
            {

#line 776
                break;
            }

#line 776
            stgPut_0(j_1 * 64U + kernelContext_2->_tid_0, (*r_1)[c_2 * 16U + j_1], kernelContext_2);

#line 776
            j_1 = j_1 + 1U;

#line 776
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 777
        uint d_2 = 0U;
        for(;;)
        {

#line 778
            if(d_2 < 16U)
            {
            }
            else
            {

#line 778
                break;
            }

#line 779
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S20 = pz_0 & lenMask_0;
            uint az_0 = (_S20 >> lgSpan_0) * 64U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S20 & spanMask_0);

#line 781
            float2 _S21 = stgGet_0(_S19 + az_0 - c_2 * 16U * 64U, kernelContext_2);


            out_0[d_2] = _S21;

#line 778
            d_2 = d_2 + 1U;

#line 778
        }

#line 774
        c_2 = c_2 + 1U;

#line 774
    }

#line 774
    j_1 = 0U;

#line 787
    for(;;)
    {

#line 787
        if(j_1 < 16U)
        {
        }
        else
        {

#line 787
            break;
        }

#line 787
        (*r_1)[j_1] = out_0[j_1];

#line 787
        j_1 = j_1 + 1U;

#line 787
    }
    return;
}


#line 543
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 546
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 546
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 667
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 667
    uint b_4 = 0U;

#line 676
    for(;;)
    {

#line 676
        if(b_4 < 4U)
        {
        }
        else
        {

#line 676
            break;
        }

#line 676
        dft4_0(r_3, b_4 * 4U);

#line 676
        b_4 = b_4 + 1U;

#line 676
    }


    return;
}


#line 855
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 855
    uint _S22;

#line 855
    uint k2_1;

#line 855
    float cr_0;

#line 855
    float ci_0;

#line 855
    uint _S23;

#line 855
    for(;;)
    {

#line 855
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(64U);

#line 11
                _S22 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(1024U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 63U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);
                float _S24 = tw_0.x;

#line 40
                float _S25 = tw_0.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S24 - ci_0 * _S25;
                    float _S26 = cr_0 * _S25 + ci_0 * _S24;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S26;

#line 42
                }

#line 50
                uint per_2 = 16U / max(64U, 1U);
                uint _S27 = max(4U, 1U);

#line 51
                _S23 = _S27;
                uint blk2_2 = tid_0 / _S27;

#line 52
                uint lane2_2 = tid_0 % _S27;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 64U, 1024U, blk_2, lane_2, per_2, _S27, 64U, blk2_2, lane2_2, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        for(;;)
        {

#line 7
            for(;;)
            {


                uint lgTB_1 = firstbithigh_0(4U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 3U;


                dft16_0(r_4);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 64.0f);
                float _S28 = tw_1.x;

#line 40
                float _S29 = tw_1.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S28 - ci_0 * _S29;
                    float _S30 = cr_0 * _S29 + ci_0 * _S28;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S30;

#line 42
                }

#line 50
                uint per_3 = 16U / _S23;
                uint _S31 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S31;

#line 52
                uint lane2_3 = tid_0 % _S31;

#line 52
                exchange_0(r_4, _S22, lgTB_1, 4U, 64U, blk_3, lane_3, per_3, _S31, 4U, blk2_3, lane2_3, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        break;
    }

#line 56
    innermost_0(r_4);

#line 858 "mm_1024_fullCorrelation.slang"
    return;
}


#line 812
uint lgOf_0(uint i_3)
{

#line 812
    uint _S32;

#line 812
    if(i_3 < 2U)
    {

#line 812
        _S32 = 4U;

#line 812
    }
    else
    {

#line 812
        _S32 = 1U;

#line 812
    }

#line 812
    return _S32;
}


#line 814
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_1 = slot_0 >> lg_0;

#line 818
    uint lg_1 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_1;

#line 818
    uint lg_2 = lgOf_0(1U);

#line 818
    uint lg_3 = lgOf_0(0U);

#line 823
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_1 & ((1U << lg_1) - 1U))) << lg_2) | (x_2 & ((1U << lg_2) - 1U))) << lg_3) | ((x_2 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 1791
[[kernel]] void fullCorrelation(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], packed_float2 device* entryPointParams_output_1 [[buffer(3)]])
{

#line 1791
    thread KernelContext_0 kernelContext_4;

#line 1791
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1791
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1791
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1791
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1791
    threadgroup array<uint, int(2048)> stg_1;

#line 1791
    (&kernelContext_4)->stg_0 = &stg_1;



    uint pair_0 = gid_0.x;

#line 1795
    uint tid_1 = lid_0.x;
    uint _S33 = pair_0 / entryPointParams_1->ntmpl_0;

#line 1796
    uint _S34 = pair_0 % entryPointParams_1->ntmpl_0;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 1799
    uint i_4 = 0U;
    for(;;)
    {

#line 1800
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1800
            break;
        }

#line 1801
        uint idx_0 = tid_1 + 64U * i_4;
        r_5[i_4] = cmulConj_0(cload_0((&kernelContext_4)->entryPointParams_data_0, _S33 * 1024U + idx_0), cload_0((&kernelContext_4)->entryPointParams_tmpl_0, _S34 * 1024U + idx_0));

#line 1800
        i_4 = i_4 + 1U;

#line 1800
    }

#line 1800
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 1800
    i_4 = 0U;

#line 1805
    for(;;)
    {

#line 1805
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1805
            break;
        }

#line 1805
        *((&kernelContext_4)->entryPointParams_output_0+(pair_0 * 1024U + slotToIndex_0(tid_1 * 16U + i_4))) = packed_float2(float2(r_5[i_4].x, r_5[i_4].y)) ;

#line 1805
        i_4 = i_4 + 1U;

#line 1805
    }

    return;
}
