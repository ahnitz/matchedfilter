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


#line 173 "mm_32768_fullCorrelation.slang"
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


#line 74 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S6 = ((MF_ACCURATE_TRIG));

#line 77
    return _S6;
}


#line 101
float2 mfTwiddle_0(float angle_0)
{

#line 79
    uint _S7 = mfAccurateTrigFlag_0();

#line 103
    if(_S7 == 0U)
    {

#line 104
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S8 = float(quadrant_0);
    float x_0 = angle_0 - _S8 * 1.57079625129699707f - _S8 * 7.54978941586159635e-08f;
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


#line 322 "mm_32768_fullCorrelation.slang"
float2 cmul_0(float2 a_1, float2 b_2)
{

#line 322
    float _S9 = a_1.x;

#line 322
    float _S10 = b_2.x;

#line 322
    float _S11 = a_1.y;

#line 322
    float _S12 = b_2.y;

#line 322
    return float2(_S9 * _S10 - _S11 * _S12, _S9 * _S12 + _S11 * _S10);
}


#line 582
void r4_0(float2 thread* a_2, float2 thread* b_3, float2 thread* c_1, float2 thread* d_0)
{
    float2 t0_0 = *a_2 + *c_1;

#line 584
    float2 t1_0 = *a_2 - *c_1;

#line 584
    float2 t2_0 = *b_3 + *d_0;

#line 584
    float2 t3_0 = *b_3 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_2 = t0_0 + t2_0;

#line 586
    *b_3 = t1_0 + j3_0;

#line 586
    *c_1 = t0_0 - t2_0;

#line 586
    *d_0 = t1_0 - j3_0;
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
        uint _S13 = 4U * k2_0;

#line 630
        r4_0(&(*r_0)[_S13], &(*r_0)[_S13 + 1U], &(*r_0)[_S13 + 2U], &(*r_0)[_S13 + 3U]);

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

        float2 _S14 = (*r_1)[j_0] - (*r_1)[j_0 + 16U];

#line 671
        float2 _S15 = mfTwiddle_0(6.28318548202514648f * float(j_0) / 32.0f);

#line 671
        v_0[j_0] = cmul_0(_S14, _S15);

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
        uint _S16 = 2U * k_0;

#line 675
        (*r_1)[_S16] = u_0[k_0];

#line 675
        (*r_1)[_S16 + 1U] = v_0[k_0];

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
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S17 = max(TB_0, 1U);

#line 326
    uint j_1 = d_1 / _S17;

#line 326
    uint m_0 = d_1 % _S17;

#line 326
    uint _S18;
    if(TB_0 <= 32U)
    {

#line 327
        _S18 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 327
    }
    else
    {

#line 327
        _S18 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 327
    }

#line 327
    return _S18;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
};


#line 311 "mm_32768_fullCorrelation.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(16384)> threadgroup* stg_0;
};


#line 311
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 311
    uint _S19 = 2U * i_1;

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S19] = (as_type<uint>((v_1.x)));

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S19 + 1U] = (as_type<uint>((v_1.y)));

#line 311
    return;
}


#line 312
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 312
    uint _S20 = 2U * i_2;

#line 312
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20 + 1U]))));
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
    uint _S21;

#line 868
    if(i_3 < 2U)
    {

#line 868
        _S21 = 5U;

#line 868
    }
    else
    {

#line 868
        if(i_3 == 2U)
        {

#line 868
            _S21 = 5U;

#line 868
        }
        else
        {

#line 868
            _S21 = 1U;

#line 868
        }

#line 868
    }

#line 868
    return _S21;
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


#line 1806
[[kernel]] void fullCorrelation(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], packed_float2 device* entryPointParams_output_1 [[buffer(3)]])
{

#line 1806
    uint _S22;

#line 1806
    uint k2_1;

#line 1806
    float cr_0;

#line 1806
    float ci_0;

#line 1806
    uint _S23;

#line 1806
    uint z_1;

#line 1806
    uint _S24;

#line 1806
    uint c_2;

#line 1806
    uint d_2;

#line 1806
    uint j_2;

#line 1806
    bool _S25;

#line 1806
    thread KernelContext_0 kernelContext_2;

#line 1806
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 1806
    (&kernelContext_2)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1806
    (&kernelContext_2)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1806
    (&kernelContext_2)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1806
    threadgroup array<uint, int(16384)> stg_1;

#line 1806
    (&kernelContext_2)->stg_0 = &stg_1;



    uint pair_0 = gid_0.x;

#line 1810
    uint tid_0 = lid_0.x;
    uint _S26 = pair_0 / entryPointParams_1->ntmpl_0;

#line 1811
    uint _S27 = pair_0 % entryPointParams_1->ntmpl_0;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(32)> r_4;

#line 1814
    uint i_4 = 0U;
    for(;;)
    {

#line 1815
        if(i_4 < 32U)
        {
        }
        else
        {

#line 1815
            break;
        }

#line 1816
        uint idx_0 = tid_0 + 1024U * i_4;
        r_4[i_4] = cmulConj_0(cload_0((&kernelContext_2)->entryPointParams_data_0, _S26 * 32768U + idx_0), cload_0((&kernelContext_2)->entryPointParams_tmpl_0, _S27 * 32768U + idx_0));

#line 1815
        i_4 = i_4 + 1U;

#line 1815
    }



    for(;;)
    {

#line 1819
        for(;;)
        {

#line 1819
            for(;;)
            {

#line 1819
                for(;;)
                {

#line 1819
                    uint lgTB_0 = firstbithigh_0(1024U);

#line 1819
                    _S22 = lgTB_0;

#line 1819
                    uint lgLn_0 = firstbithigh_0(32768U);

#line 1819
                    uint blk_1 = tid_0 >> lgTB_0;

#line 1819
                    uint lane_1 = tid_0 & 1023U;

#line 1819
                    dftR_0(&r_4);

#line 1819
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 32768.0f);

#line 1819
                    float _S28 = tw_0.x;

#line 1819
                    float _S29 = tw_0.y;

#line 1819
                    k2_1 = 0U;

#line 1819
                    cr_0 = 1.0f;

#line 1819
                    ci_0 = 0.0f;

#line 1819
                    for(;;)
                    {

#line 1819
                        if(k2_1 < 32U)
                        {
                        }
                        else
                        {

#line 1819
                            break;
                        }

#line 1819
                        r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 1819
                        float nr_0 = cr_0 * _S28 - ci_0 * _S29;

#line 1819
                        float _S30 = cr_0 * _S29 + ci_0 * _S28;

#line 1819
                        k2_1 = k2_1 + 1U;

#line 1819
                        cr_0 = nr_0;

#line 1819
                        ci_0 = _S30;

#line 1819
                    }

#line 1819
                    uint per_1 = 32U / max(1024U, 1U);

#line 1819
                    uint _S31 = max(32U, 1U);

#line 1819
                    _S23 = _S31;

#line 1819
                    uint blk2_1 = tid_0 / _S31;

#line 1819
                    uint lane2_1 = tid_0 % _S31;

#line 1819
                    for(;;)
                    {

#line 1819
                        thread array<float2, int(32)> out_0;

#line 1819
                        z_1 = 0U;

#line 1819
                        for(;;)
                        {

#line 1819
                            if(z_1 < 32U)
                            {
                            }
                            else
                            {

#line 1819
                                break;
                            }

#line 1819
                            out_0[z_1] = float2(0.0f, 0.0f);

#line 1819
                            z_1 = z_1 + 1U;

#line 1819
                        }

#line 1819
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 1819
                        _S24 = spanMask_0;

#line 1819
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1819
                        uint p0_0 = computeWant_0(0U, 1024U, 32768U, blk_1, lane_1, per_1, _S31, 1024U, blk2_1, lane2_1);

#line 1819
                        uint _S32 = p0_0 & lenMask_0;

#line 1819
                        uint _S33 = _S32 >> lgTB_0;

#line 1819
                        uint _S34 = _S33 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S32 & spanMask_0);

#line 1819
                        c_2 = 0U;

#line 1819
                        for(;;)
                        {

#line 1819
                            if(c_2 < 4U)
                            {
                            }
                            else
                            {

#line 1819
                                break;
                            }

#line 1819
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1819
                            j_2 = 0U;

#line 1819
                            for(;;)
                            {

#line 1819
                                if(j_2 < 8U)
                                {
                                }
                                else
                                {

#line 1819
                                    break;
                                }

#line 1819
                                stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_4[c_2 * 8U + j_2], &kernelContext_2);

#line 1819
                                j_2 = j_2 + 1U;

#line 1819
                            }

#line 1819
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1819
                            d_2 = 0U;

#line 1819
                            for(;;)
                            {

#line 1819
                                if(d_2 < 32U)
                                {
                                }
                                else
                                {

#line 1819
                                    break;
                                }

#line 1819
                                uint pz_0 = computeWant_0(d_2, 1024U, 32768U, 0U, 0U, per_1, _S31, 1024U, 0U, 0U);

#line 1819
                                uint _S35 = pz_0 & lenMask_0;

#line 1819
                                uint iz_0 = _S35 >> lgTB_0;

#line 1819
                                uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S35 & spanMask_0);

#line 1819
                                uint i_5 = _S33 + iz_0;

#line 1819
                                uint _S36 = c_2 * 8U;

#line 1819
                                if(i_5 >= _S36)
                                {

#line 1819
                                    _S25 = i_5 < ((c_2 + 1U) * 8U);

#line 1819
                                }
                                else
                                {

#line 1819
                                    _S25 = false;

#line 1819
                                }

#line 1819
                                if(_S25)
                                {

#line 1819
                                    float2 _S37 = stgGet_0(_S34 + az_0 - _S36 * 1024U, &kernelContext_2);

#line 1819
                                    out_0[d_2] = _S37;

#line 1819
                                }

#line 1819
                                d_2 = d_2 + 1U;

#line 1819
                            }

#line 1819
                            c_2 = c_2 + 1U;

#line 1819
                        }

#line 1819
                        d_2 = 0U;

#line 1819
                        for(;;)
                        {

#line 1819
                            if(d_2 < 32U)
                            {
                            }
                            else
                            {

#line 1819
                                break;
                            }

#line 1819
                            r_4[d_2] = out_0[d_2];

#line 1819
                            d_2 = d_2 + 1U;

#line 1819
                        }

#line 1819
                        break;
                    }

#line 1819
                    break;
                }

#line 1819
                break;
            }

#line 1819
            for(;;)
            {

#line 1819
                for(;;)
                {

#line 1819
                    uint lgTB_1 = firstbithigh_0(32U);

#line 1819
                    uint blk_2 = tid_0 >> lgTB_1;

#line 1819
                    uint lane_2 = tid_0 & 31U;

#line 1819
                    dftR_0(&r_4);

#line 1819
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 1819
                    float _S38 = tw_1.x;

#line 1819
                    float _S39 = tw_1.y;

#line 1819
                    k2_1 = 0U;

#line 1819
                    cr_0 = 1.0f;

#line 1819
                    ci_0 = 0.0f;

#line 1819
                    for(;;)
                    {

#line 1819
                        if(k2_1 < 32U)
                        {
                        }
                        else
                        {

#line 1819
                            break;
                        }

#line 1819
                        r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 1819
                        float nr_1 = cr_0 * _S38 - ci_0 * _S39;

#line 1819
                        float _S40 = cr_0 * _S39 + ci_0 * _S38;

#line 1819
                        k2_1 = k2_1 + 1U;

#line 1819
                        cr_0 = nr_1;

#line 1819
                        ci_0 = _S40;

#line 1819
                    }

#line 1819
                    uint per_2 = 32U / _S23;

#line 1819
                    uint _S41 = max(1U, 1U);

#line 1819
                    uint blk2_2 = tid_0 / _S41;

#line 1819
                    uint lane2_2 = tid_0 % _S41;

#line 1819
                    for(;;)
                    {

#line 1819
                        thread array<float2, int(32)> out_1;

#line 1819
                        z_1 = 0U;

#line 1819
                        for(;;)
                        {

#line 1819
                            if(z_1 < 32U)
                            {
                            }
                            else
                            {

#line 1819
                                break;
                            }

#line 1819
                            out_1[z_1] = float2(0.0f, 0.0f);

#line 1819
                            z_1 = z_1 + 1U;

#line 1819
                        }

#line 1819
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 1819
                        uint p0_1 = computeWant_0(0U, 32U, 1024U, blk_2, lane_2, per_2, _S41, 32U, blk2_2, lane2_2);

#line 1819
                        uint _S42 = p0_1 & _S24;

#line 1819
                        uint _S43 = _S42 >> lgTB_1;

#line 1819
                        uint _S44 = _S43 * 1024U + ((p0_1 >> _S22) << lgTB_1) + (_S42 & spanMask_1);

#line 1819
                        c_2 = 0U;

#line 1819
                        for(;;)
                        {

#line 1819
                            if(c_2 < 4U)
                            {
                            }
                            else
                            {

#line 1819
                                break;
                            }

#line 1819
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1819
                            j_2 = 0U;

#line 1819
                            for(;;)
                            {

#line 1819
                                if(j_2 < 8U)
                                {
                                }
                                else
                                {

#line 1819
                                    break;
                                }

#line 1819
                                stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_4[c_2 * 8U + j_2], &kernelContext_2);

#line 1819
                                j_2 = j_2 + 1U;

#line 1819
                            }

#line 1819
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1819
                            d_2 = 0U;

#line 1819
                            for(;;)
                            {

#line 1819
                                if(d_2 < 32U)
                                {
                                }
                                else
                                {

#line 1819
                                    break;
                                }

#line 1819
                                uint pz_1 = computeWant_0(d_2, 32U, 1024U, 0U, 0U, per_2, _S41, 32U, 0U, 0U);

#line 1819
                                uint _S45 = pz_1 & _S24;

#line 1819
                                uint iz_1 = _S45 >> lgTB_1;

#line 1819
                                uint az_1 = iz_1 * 1024U + ((pz_1 >> _S22) << lgTB_1) + (_S45 & spanMask_1);

#line 1819
                                uint i_6 = _S43 + iz_1;

#line 1819
                                uint _S46 = c_2 * 8U;

#line 1819
                                if(i_6 >= _S46)
                                {

#line 1819
                                    _S25 = i_6 < ((c_2 + 1U) * 8U);

#line 1819
                                }
                                else
                                {

#line 1819
                                    _S25 = false;

#line 1819
                                }

#line 1819
                                if(_S25)
                                {

#line 1819
                                    float2 _S47 = stgGet_0(_S44 + az_1 - _S46 * 1024U, &kernelContext_2);

#line 1819
                                    out_1[d_2] = _S47;

#line 1819
                                }

#line 1819
                                d_2 = d_2 + 1U;

#line 1819
                            }

#line 1819
                            c_2 = c_2 + 1U;

#line 1819
                        }

#line 1819
                        d_2 = 0U;

#line 1819
                        for(;;)
                        {

#line 1819
                            if(d_2 < 32U)
                            {
                            }
                            else
                            {

#line 1819
                                break;
                            }

#line 1819
                            r_4[d_2] = out_1[d_2];

#line 1819
                            d_2 = d_2 + 1U;

#line 1819
                        }

#line 1819
                        break;
                    }

#line 1819
                    break;
                }

#line 1819
                break;
            }

#line 1819
            break;
        }

#line 1819
        innermost_0(&r_4);

#line 1819
        break;
    }

#line 1819
    i_4 = 0U;
    for(;;)
    {

#line 1820
        if(i_4 < 32U)
        {
        }
        else
        {

#line 1820
            break;
        }

#line 1820
        *((&kernelContext_2)->entryPointParams_output_0+(pair_0 * 32768U + slotToIndex_0(tid_0 * 32U + i_4))) = packed_float2(float2(r_4[i_4].x, r_4[i_4].y)) ;

#line 1820
        i_4 = i_4 + 1U;

#line 1820
    }

    return;
}
