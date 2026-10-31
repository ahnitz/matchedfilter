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


#line 173 "mm_65536_fullCorrelation_lds32.slang"
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


#line 582
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 584
    float2 t1_0 = *a_1 - *c_0;

#line 584
    float2 t2_0 = *b_2 + *d_0;

#line 584
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 586
    *b_2 = t1_0 + j3_0;

#line 586
    *c_0 = t0_0 - t2_0;

#line 586
    *d_0 = t1_0 - j3_0;
    return;
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
    float c_1 = 1.0f + z_0 * (-0.5f + z_0 * (0.0416666679084301f + z_0 * (-0.00138888892251998f + z_0 * (0.00002480158764229f + z_0 * -2.75573199814971304e-07f))));

    float s_0 = x_0 * (1.0f + z_0 * (-0.1666666716337204f + z_0 * (0.00833333376795053f + z_0 * (-0.0001984127011383f + z_0 * (2.75573188446287531e-06f + z_0 * -2.50521079436794025e-08f)))));


    switch(quadrant_0 & int(3))
    {
    case int(1):
        {

#line 117
            return float2(- s_0, c_1);
        }
    case int(2):
        {

#line 118
            return float2(- c_1, - s_0);
        }
    case int(3):
        {

#line 119
            return float2(s_0, - c_1);
        }
    default:
        {

#line 120
            return float2(c_1, s_0);
        }
    }

#line 120
}


#line 322 "mm_65536_fullCorrelation_lds32.slang"
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 322
    float _S9 = a_2.x;

#line 322
    float _S10 = b_3.x;

#line 322
    float _S11 = a_2.y;

#line 322
    float _S12 = b_3.y;

#line 322
    return float2(_S9 * _S10 - _S11 * _S12, _S9 * _S12 + _S11 * _S10);
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


#line 684
void dft64_0(array<float2, int(64)> thread* r_1)
{

#line 684
    uint k_0;

#line 684
    uint j_0 = 0U;

    for(;;)
    {

#line 686
        if(j_0 < 16U)
        {
        }
        else
        {

#line 686
            break;
        }

#line 687
        r4_0(&(*r_1)[j_0], &(*r_1)[j_0 + 16U], &(*r_1)[j_0 + 32U], &(*r_1)[j_0 + 48U]);

#line 686
        j_0 = j_0 + 1U;

#line 686
    }

    thread array<float2, int(64)> o_0;

#line 688
    uint pp_0 = 0U;
    for(;;)
    {

#line 689
        if(pp_0 < 4U)
        {
        }
        else
        {

#line 689
            break;
        }

#line 690
        thread array<float2, int(16)> b_4;

#line 690
        j_0 = 0U;
        for(;;)
        {

#line 691
            if(j_0 < 16U)
            {
            }
            else
            {

#line 691
                break;
            }
            float2 _S14 = mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f);

#line 693
            b_4[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], _S14);

#line 691
            j_0 = j_0 + 1U;

#line 691
        }



        dft16_0(&b_4);

#line 695
        k_0 = 0U;
        for(;;)
        {

#line 696
            if(k_0 < 16U)
            {
            }
            else
            {

#line 696
                break;
            }

#line 696
            o_0[4U * k_0 + pp_0] = b_4[k_0];

#line 696
            k_0 = k_0 + 1U;

#line 696
        }

#line 689
        pp_0 = pp_0 + 1U;

#line 689
    }

#line 689
    k_0 = 0U;

#line 698
    for(;;)
    {

#line 698
        if(k_0 < 64U)
        {
        }
        else
        {

#line 698
            break;
        }

#line 698
        (*r_1)[k_0] = o_0[k_0];

#line 698
        k_0 = k_0 + 1U;

#line 698
    }
    return;
}


void dftR_0(array<float2, int(64)> thread* r_2)
{

#line 710
    dft64_0(r_2);

    return;
}


#line 324
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S15 = max(TB_0, 1U);

#line 326
    uint j_1 = d_1 / _S15;

#line 326
    uint m_0 = d_1 % _S15;

#line 326
    uint _S16;
    if(TB_0 <= 64U)
    {

#line 327
        _S16 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 327
    }
    else
    {

#line 327
        _S16 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 327
    }

#line 327
    return _S16;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
};


#line 311 "mm_65536_fullCorrelation_lds32.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 311
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 311
    uint _S17 = 2U * i_1;

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S17] = (as_type<uint>((v_0.x)));

#line 311
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S17 + 1U] = (as_type<uint>((v_0.y)));

#line 311
    return;
}


#line 312
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 312
    uint _S18 = 2U * i_2;

#line 312
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S18]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S18 + 1U]))));
}


#line 643
void dft16at_0(array<float2, int(64)> thread* r_3, uint o_1)
{



    thread array<float2, int(16)> b_5;

#line 648
    uint i_3 = 0U;
    for(;;)
    {

#line 649
        if(i_3 < 16U)
        {
        }
        else
        {

#line 649
            break;
        }

#line 649
        b_5[i_3] = (*r_3)[o_1 + i_3];

#line 649
        i_3 = i_3 + 1U;

#line 649
    }
    dft16_0(&b_5);

#line 650
    i_3 = 0U;
    for(;;)
    {

#line 651
        if(i_3 < 16U)
        {
        }
        else
        {

#line 651
            break;
        }

#line 651
        (*r_3)[o_1 + i_3] = b_5[i_3];

#line 651
        i_3 = i_3 + 1U;

#line 651
    }

    return;
}


#line 721
void innermost_0(array<float2, int(64)> thread* r_4)
{

#line 721
    uint b_6 = 0U;

#line 726
    for(;;)
    {

#line 726
        if(b_6 < 4U)
        {
        }
        else
        {

#line 726
            break;
        }

#line 726
        dft16at_0(r_4, b_6 * 16U);

#line 726
        b_6 = b_6 + 1U;

#line 726
    }

#line 733
    return;
}


#line 868
uint lgOf_0(uint i_4)
{

#line 868
    uint _S19;

#line 868
    if(i_4 < 2U)
    {

#line 868
        _S19 = 6U;

#line 868
    }
    else
    {

#line 868
        if(i_4 == 2U)
        {

#line 868
            _S19 = 4U;

#line 868
        }
        else
        {

#line 868
            _S19 = 1U;

#line 868
        }

#line 868
    }

#line 868
    return _S19;
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
    uint _S20;

#line 1806
    uint k2_1;

#line 1806
    float cr_0;

#line 1806
    float ci_0;

#line 1806
    uint _S21;

#line 1806
    uint z_1;

#line 1806
    uint _S22;

#line 1806
    uint c_2;

#line 1806
    uint d_2;

#line 1806
    uint j_2;

#line 1806
    bool _S23;

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
    threadgroup array<uint, int(8192)> stg_1;

#line 1806
    (&kernelContext_2)->stg_0 = &stg_1;



    uint pair_0 = gid_0.x;

#line 1810
    uint tid_0 = lid_0.x;
    uint _S24 = pair_0 / entryPointParams_1->ntmpl_0;

#line 1811
    uint _S25 = pair_0 % entryPointParams_1->ntmpl_0;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(64)> r_5;

#line 1814
    uint i_5 = 0U;
    for(;;)
    {

#line 1815
        if(i_5 < 64U)
        {
        }
        else
        {

#line 1815
            break;
        }

#line 1816
        uint idx_0 = tid_0 + 1024U * i_5;
        r_5[i_5] = cmulConj_0(cload_0((&kernelContext_2)->entryPointParams_data_0, _S24 * 65536U + idx_0), cload_0((&kernelContext_2)->entryPointParams_tmpl_0, _S25 * 65536U + idx_0));

#line 1815
        i_5 = i_5 + 1U;

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
                    _S20 = lgTB_0;

#line 1819
                    uint lgLn_0 = firstbithigh_0(65536U);

#line 1819
                    uint blk_1 = tid_0 >> lgTB_0;

#line 1819
                    uint lane_1 = tid_0 & 1023U;

#line 1819
                    dftR_0(&r_5);

#line 1819
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 6.5536e+04f);

#line 1819
                    float _S26 = tw_0.x;

#line 1819
                    float _S27 = tw_0.y;

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
                        if(k2_1 < 64U)
                        {
                        }
                        else
                        {

#line 1819
                            break;
                        }

#line 1819
                        r_5[k2_1] = cmul_0(r_5[k2_1], float2(cr_0, ci_0));

#line 1819
                        float nr_0 = cr_0 * _S26 - ci_0 * _S27;

#line 1819
                        float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 1819
                        k2_1 = k2_1 + 1U;

#line 1819
                        cr_0 = nr_0;

#line 1819
                        ci_0 = _S28;

#line 1819
                    }

#line 1819
                    uint per_1 = 64U / max(1024U, 1U);

#line 1819
                    uint _S29 = max(16U, 1U);

#line 1819
                    _S21 = _S29;

#line 1819
                    uint blk2_1 = tid_0 / _S29;

#line 1819
                    uint lane2_1 = tid_0 % _S29;

#line 1819
                    for(;;)
                    {

#line 1819
                        thread array<float2, int(64)> out_0;

#line 1819
                        z_1 = 0U;

#line 1819
                        for(;;)
                        {

#line 1819
                            if(z_1 < 64U)
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
                        _S22 = spanMask_0;

#line 1819
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1819
                        uint p0_0 = computeWant_0(0U, 1024U, 65536U, blk_1, lane_1, per_1, _S29, 1024U, blk2_1, lane2_1);

#line 1819
                        uint _S30 = p0_0 & lenMask_0;

#line 1819
                        uint _S31 = _S30 >> lgTB_0;

#line 1819
                        uint _S32 = _S31 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S30 & spanMask_0);

#line 1819
                        c_2 = 0U;

#line 1819
                        for(;;)
                        {

#line 1819
                            if(c_2 < 16U)
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
                                if(j_2 < 4U)
                                {
                                }
                                else
                                {

#line 1819
                                    break;
                                }

#line 1819
                                stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_5[c_2 * 4U + j_2], &kernelContext_2);

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
                                if(d_2 < 64U)
                                {
                                }
                                else
                                {

#line 1819
                                    break;
                                }

#line 1819
                                uint pz_0 = computeWant_0(d_2, 1024U, 65536U, 0U, 0U, per_1, _S29, 1024U, 0U, 0U);

#line 1819
                                uint _S33 = pz_0 & lenMask_0;

#line 1819
                                uint iz_0 = _S33 >> lgTB_0;

#line 1819
                                uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S33 & spanMask_0);

#line 1819
                                uint i_6 = _S31 + iz_0;

#line 1819
                                uint _S34 = c_2 * 4U;

#line 1819
                                if(i_6 >= _S34)
                                {

#line 1819
                                    _S23 = i_6 < ((c_2 + 1U) * 4U);

#line 1819
                                }
                                else
                                {

#line 1819
                                    _S23 = false;

#line 1819
                                }

#line 1819
                                if(_S23)
                                {

#line 1819
                                    float2 _S35 = stgGet_0(_S32 + az_0 - _S34 * 1024U, &kernelContext_2);

#line 1819
                                    out_0[d_2] = _S35;

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
                            if(d_2 < 64U)
                            {
                            }
                            else
                            {

#line 1819
                                break;
                            }

#line 1819
                            r_5[d_2] = out_0[d_2];

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
                    uint lgTB_1 = firstbithigh_0(16U);

#line 1819
                    uint blk_2 = tid_0 >> lgTB_1;

#line 1819
                    uint lane_2 = tid_0 & 15U;

#line 1819
                    dftR_0(&r_5);

#line 1819
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 1819
                    float _S36 = tw_1.x;

#line 1819
                    float _S37 = tw_1.y;

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
                        if(k2_1 < 64U)
                        {
                        }
                        else
                        {

#line 1819
                            break;
                        }

#line 1819
                        r_5[k2_1] = cmul_0(r_5[k2_1], float2(cr_0, ci_0));

#line 1819
                        float nr_1 = cr_0 * _S36 - ci_0 * _S37;

#line 1819
                        float _S38 = cr_0 * _S37 + ci_0 * _S36;

#line 1819
                        k2_1 = k2_1 + 1U;

#line 1819
                        cr_0 = nr_1;

#line 1819
                        ci_0 = _S38;

#line 1819
                    }

#line 1819
                    uint per_2 = 64U / _S21;

#line 1819
                    uint _S39 = max(0U, 1U);

#line 1819
                    uint blk2_2 = tid_0 / _S39;

#line 1819
                    uint lane2_2 = tid_0 % _S39;

#line 1819
                    for(;;)
                    {

#line 1819
                        thread array<float2, int(64)> out_1;

#line 1819
                        z_1 = 0U;

#line 1819
                        for(;;)
                        {

#line 1819
                            if(z_1 < 64U)
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
                        uint p0_1 = computeWant_0(0U, 16U, 1024U, blk_2, lane_2, per_2, _S39, 16U, blk2_2, lane2_2);

#line 1819
                        uint _S40 = p0_1 & _S22;

#line 1819
                        uint _S41 = _S40 >> lgTB_1;

#line 1819
                        uint _S42 = _S41 * 1024U + ((p0_1 >> _S20) << lgTB_1) + (_S40 & spanMask_1);

#line 1819
                        c_2 = 0U;

#line 1819
                        for(;;)
                        {

#line 1819
                            if(c_2 < 16U)
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
                                if(j_2 < 4U)
                                {
                                }
                                else
                                {

#line 1819
                                    break;
                                }

#line 1819
                                stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_5[c_2 * 4U + j_2], &kernelContext_2);

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
                                if(d_2 < 64U)
                                {
                                }
                                else
                                {

#line 1819
                                    break;
                                }

#line 1819
                                uint pz_1 = computeWant_0(d_2, 16U, 1024U, 0U, 0U, per_2, _S39, 16U, 0U, 0U);

#line 1819
                                uint _S43 = pz_1 & _S22;

#line 1819
                                uint iz_1 = _S43 >> lgTB_1;

#line 1819
                                uint az_1 = iz_1 * 1024U + ((pz_1 >> _S20) << lgTB_1) + (_S43 & spanMask_1);

#line 1819
                                uint i_7 = _S41 + iz_1;

#line 1819
                                uint _S44 = c_2 * 4U;

#line 1819
                                if(i_7 >= _S44)
                                {

#line 1819
                                    _S23 = i_7 < ((c_2 + 1U) * 4U);

#line 1819
                                }
                                else
                                {

#line 1819
                                    _S23 = false;

#line 1819
                                }

#line 1819
                                if(_S23)
                                {

#line 1819
                                    float2 _S45 = stgGet_0(_S42 + az_1 - _S44 * 1024U, &kernelContext_2);

#line 1819
                                    out_1[d_2] = _S45;

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
                            if(d_2 < 64U)
                            {
                            }
                            else
                            {

#line 1819
                                break;
                            }

#line 1819
                            r_5[d_2] = out_1[d_2];

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
        innermost_0(&r_5);

#line 1819
        break;
    }

#line 1819
    i_5 = 0U;
    for(;;)
    {

#line 1820
        if(i_5 < 64U)
        {
        }
        else
        {

#line 1820
            break;
        }

#line 1820
        *((&kernelContext_2)->entryPointParams_output_0+(pair_0 * 65536U + slotToIndex_0(tid_0 * 64U + i_5))) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 1820
        i_5 = i_5 + 1U;

#line 1820
    }

    return;
}
