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


#line 173 "mm_65536_fullCorrelationSeries_lds32.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 173
    return float2(*(b_0+i_0)) ;
}


#line 329
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 329
    float _S2 = a_0.x;

#line 329
    float _S3 = b_1.x;

#line 329
    float _S4 = a_0.y;

#line 329
    float _S5 = b_1.y;

#line 329
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 613
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 615
    float2 t1_0 = *a_1 - *c_0;

#line 615
    float2 t2_0 = *b_2 + *d_0;

#line 615
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 617
    *b_2 = t1_0 + j3_0;

#line 617
    *c_0 = t0_0 - t2_0;

#line 617
    *d_0 = t1_0 - j3_0;
    return;
}


#line 76 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S6 = ((MF_ACCURATE_TRIG));

#line 79
    return _S6;
}


#line 103
float2 mfTwiddle_0(float angle_0)
{

#line 81
    uint _S7 = mfAccurateTrigFlag_0();

#line 105
    if(_S7 == 0U)
    {

#line 106
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


#line 328 "mm_65536_fullCorrelationSeries_lds32.slang"
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 328
    float _S9 = a_2.x;

#line 328
    float _S10 = b_3.x;

#line 328
    float _S11 = a_2.y;

#line 328
    float _S12 = b_3.y;

#line 328
    return float2(_S9 * _S10 - _S11 * _S12, _S9 * _S12 + _S11 * _S10);
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
        uint _S13 = 4U * k2_0;

#line 661
        r4_0(&(*r_0)[_S13], &(*r_0)[_S13 + 1U], &(*r_0)[_S13 + 2U], &(*r_0)[_S13 + 3U]);

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


#line 715
void dft64_0(array<float2, int(64)> thread* r_1)
{

#line 715
    uint k_0;

#line 715
    uint j_0 = 0U;

    for(;;)
    {

#line 717
        if(j_0 < 16U)
        {
        }
        else
        {

#line 717
            break;
        }

#line 718
        r4_0(&(*r_1)[j_0], &(*r_1)[j_0 + 16U], &(*r_1)[j_0 + 32U], &(*r_1)[j_0 + 48U]);

#line 717
        j_0 = j_0 + 1U;

#line 717
    }

    thread array<float2, int(64)> o_0;

#line 719
    uint pp_0 = 0U;
    for(;;)
    {

#line 720
        if(pp_0 < 4U)
        {
        }
        else
        {

#line 720
            break;
        }

#line 721
        thread array<float2, int(16)> b_4;

#line 721
        j_0 = 0U;
        for(;;)
        {

#line 722
            if(j_0 < 16U)
            {
            }
            else
            {

#line 722
                break;
            }
            float2 _S14 = mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f);

#line 724
            b_4[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], _S14);

#line 722
            j_0 = j_0 + 1U;

#line 722
        }



        dft16_0(&b_4);

#line 726
        k_0 = 0U;
        for(;;)
        {

#line 727
            if(k_0 < 16U)
            {
            }
            else
            {

#line 727
                break;
            }

#line 727
            o_0[4U * k_0 + pp_0] = b_4[k_0];

#line 727
            k_0 = k_0 + 1U;

#line 727
        }

#line 720
        pp_0 = pp_0 + 1U;

#line 720
    }

#line 720
    k_0 = 0U;

#line 729
    for(;;)
    {

#line 729
        if(k_0 < 64U)
        {
        }
        else
        {

#line 729
            break;
        }

#line 729
        (*r_1)[k_0] = o_0[k_0];

#line 729
        k_0 = k_0 + 1U;

#line 729
    }
    return;
}


void dftR_0(array<float2, int(64)> thread* r_2)
{

#line 741
    dft64_0(r_2);

    return;
}


#line 330
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S15 = max(TB_0, 1U);

#line 332
    uint j_1 = d_1 / _S15;

#line 332
    uint m_0 = d_1 % _S15;

#line 332
    uint _S16;
    if(TB_0 <= 64U)
    {

#line 333
        _S16 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 333
    }
    else
    {

#line 333
        _S16 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 333
    }

#line 333
    return _S16;
}


#line 1915
struct EntryPointParams_0
{
    uint4 params_0;
};


#line 317
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 317
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 317
    uint _S17 = 2U * i_1;

#line 317
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S17] = (as_type<uint>((v_0.x)));

#line 317
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S17 + 1U] = (as_type<uint>((v_0.y)));

#line 317
    return;
}


#line 318
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 318
    uint _S18 = 2U * i_2;

#line 318
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S18]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S18 + 1U]))));
}


#line 674
void dft16at_0(array<float2, int(64)> thread* r_3, uint o_1)
{



    thread array<float2, int(16)> b_5;

#line 679
    uint i_3 = 0U;
    for(;;)
    {

#line 680
        if(i_3 < 16U)
        {
        }
        else
        {

#line 680
            break;
        }

#line 680
        b_5[i_3] = (*r_3)[o_1 + i_3];

#line 680
        i_3 = i_3 + 1U;

#line 680
    }
    dft16_0(&b_5);

#line 681
    i_3 = 0U;
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
        (*r_3)[o_1 + i_3] = b_5[i_3];

#line 682
        i_3 = i_3 + 1U;

#line 682
    }

    return;
}


#line 752
void innermost_0(array<float2, int(64)> thread* r_4)
{

#line 752
    uint b_6 = 0U;

#line 757
    for(;;)
    {

#line 757
        if(b_6 < 4U)
        {
        }
        else
        {

#line 757
            break;
        }

#line 757
        dft16at_0(r_4, b_6 * 16U);

#line 757
        b_6 = b_6 + 1U;

#line 757
    }

#line 764
    return;
}


#line 880
uint lgOf_0(uint i_4)
{

#line 880
    uint _S19;

#line 880
    if(i_4 < 2U)
    {

#line 880
        _S19 = 6U;

#line 880
    }
    else
    {

#line 880
        if(i_4 == 2U)
        {

#line 880
            _S19 = 4U;

#line 880
        }
        else
        {

#line 880
            _S19 = 1U;

#line 880
        }

#line 880
    }

#line 880
    return _S19;
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


#line 1915
[[kernel]] void fullCorrelationSeries(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], uint device* entryPointParams_starts_1 [[buffer(3)]], packed_float2 device* entryPointParams_output_1 [[buffer(4)]])
{

#line 1915
    uint _S20;

#line 1915
    uint k2_1;

#line 1915
    float cr_0;

#line 1915
    float ci_0;

#line 1915
    uint _S21;

#line 1915
    uint z_1;

#line 1915
    uint _S22;

#line 1915
    uint c_2;

#line 1915
    uint d_2;

#line 1915
    uint j_2;

#line 1915
    bool _S23;

#line 1915
    thread KernelContext_0 kernelContext_2;

#line 1915
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 1915
    (&kernelContext_2)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1915
    (&kernelContext_2)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1915
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1915
    (&kernelContext_2)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1915
    threadgroup array<uint, int(8192)> stg_1;

#line 1915
    (&kernelContext_2)->stg_0 = &stg_1;

#line 1920
    uint pair_0 = gid_0.x;

#line 1920
    uint tid_0 = lid_0.x;
    uint d_3 = pair_0 / entryPointParams_1->params_0.x;

#line 1921
    uint _S24 = pair_0 % entryPointParams_1->params_0.x;
    uint _S25 = (&kernelContext_2)->entryPointParams_starts_0[d_3];
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(64)> r_5;

#line 1925
    uint i_5 = 0U;
    for(;;)
    {

#line 1926
        if(i_5 < 64U)
        {
        }
        else
        {

#line 1926
            break;
        }

#line 1927
        uint idx_0 = tid_0 + 1024U * i_5;
        r_5[i_5] = cmulConj_0(cload_0((&kernelContext_2)->entryPointParams_data_0, d_3 * 65536U + idx_0), cload_0((&kernelContext_2)->entryPointParams_tmpl_0, _S24 * 65536U + idx_0));

#line 1926
        i_5 = i_5 + 1U;

#line 1926
    }



    for(;;)
    {

#line 1930
        for(;;)
        {

#line 1930
            for(;;)
            {

#line 1930
                for(;;)
                {

#line 1930
                    uint lgTB_0 = firstbithigh_0(1024U);

#line 1930
                    _S20 = lgTB_0;

#line 1930
                    uint lgLn_0 = firstbithigh_0(65536U);

#line 1930
                    uint blk_1 = tid_0 >> lgTB_0;

#line 1930
                    uint lane_1 = tid_0 & 1023U;

#line 1930
                    dftR_0(&r_5);

#line 1930
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 6.5536e+04f);

#line 1930
                    float _S26 = tw_0.x;

#line 1930
                    float _S27 = tw_0.y;

#line 1930
                    k2_1 = 0U;

#line 1930
                    cr_0 = 1.0f;

#line 1930
                    ci_0 = 0.0f;

#line 1930
                    for(;;)
                    {

#line 1930
                        if(k2_1 < 64U)
                        {
                        }
                        else
                        {

#line 1930
                            break;
                        }

#line 1930
                        r_5[k2_1] = cmul_0(r_5[k2_1], float2(cr_0, ci_0));

#line 1930
                        float nr_0 = cr_0 * _S26 - ci_0 * _S27;

#line 1930
                        float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 1930
                        k2_1 = k2_1 + 1U;

#line 1930
                        cr_0 = nr_0;

#line 1930
                        ci_0 = _S28;

#line 1930
                    }

#line 1930
                    uint per_1 = 64U / max(1024U, 1U);

#line 1930
                    uint _S29 = max(16U, 1U);

#line 1930
                    _S21 = _S29;

#line 1930
                    uint blk2_1 = tid_0 / _S29;

#line 1930
                    uint lane2_1 = tid_0 % _S29;

#line 1930
                    for(;;)
                    {

#line 1930
                        thread array<float2, int(64)> out_0;

#line 1930
                        z_1 = 0U;

#line 1930
                        for(;;)
                        {

#line 1930
                            if(z_1 < 64U)
                            {
                            }
                            else
                            {

#line 1930
                                break;
                            }

#line 1930
                            out_0[z_1] = float2(0.0f, 0.0f);

#line 1930
                            z_1 = z_1 + 1U;

#line 1930
                        }

#line 1930
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 1930
                        _S22 = spanMask_0;

#line 1930
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1930
                        uint p0_0 = computeWant_0(0U, 1024U, 65536U, blk_1, lane_1, per_1, _S29, 1024U, blk2_1, lane2_1);

#line 1930
                        uint _S30 = p0_0 & lenMask_0;

#line 1930
                        uint _S31 = _S30 >> lgTB_0;

#line 1930
                        uint _S32 = _S31 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S30 & spanMask_0);

#line 1930
                        c_2 = 0U;

#line 1930
                        for(;;)
                        {

#line 1930
                            if(c_2 < 16U)
                            {
                            }
                            else
                            {

#line 1930
                                break;
                            }

#line 1930
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1930
                            j_2 = 0U;

#line 1930
                            for(;;)
                            {

#line 1930
                                if(j_2 < 4U)
                                {
                                }
                                else
                                {

#line 1930
                                    break;
                                }

#line 1930
                                stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_5[c_2 * 4U + j_2], &kernelContext_2);

#line 1930
                                j_2 = j_2 + 1U;

#line 1930
                            }

#line 1930
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1930
                            d_2 = 0U;

#line 1930
                            for(;;)
                            {

#line 1930
                                if(d_2 < 64U)
                                {
                                }
                                else
                                {

#line 1930
                                    break;
                                }

#line 1930
                                uint pz_0 = computeWant_0(d_2, 1024U, 65536U, 0U, 0U, per_1, _S29, 1024U, 0U, 0U);

#line 1930
                                uint _S33 = pz_0 & lenMask_0;

#line 1930
                                uint iz_0 = _S33 >> lgTB_0;

#line 1930
                                uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S33 & spanMask_0);

#line 1930
                                uint i_6 = _S31 + iz_0;

#line 1930
                                uint _S34 = c_2 * 4U;

#line 1930
                                if(i_6 >= _S34)
                                {

#line 1930
                                    _S23 = i_6 < ((c_2 + 1U) * 4U);

#line 1930
                                }
                                else
                                {

#line 1930
                                    _S23 = false;

#line 1930
                                }

#line 1930
                                if(_S23)
                                {

#line 1930
                                    float2 _S35 = stgGet_0(_S32 + az_0 - _S34 * 1024U, &kernelContext_2);

#line 1930
                                    out_0[d_2] = _S35;

#line 1930
                                }

#line 1930
                                d_2 = d_2 + 1U;

#line 1930
                            }

#line 1930
                            c_2 = c_2 + 1U;

#line 1930
                        }

#line 1930
                        d_2 = 0U;

#line 1930
                        for(;;)
                        {

#line 1930
                            if(d_2 < 64U)
                            {
                            }
                            else
                            {

#line 1930
                                break;
                            }

#line 1930
                            r_5[d_2] = out_0[d_2];

#line 1930
                            d_2 = d_2 + 1U;

#line 1930
                        }

#line 1930
                        break;
                    }

#line 1930
                    break;
                }

#line 1930
                break;
            }

#line 1930
            for(;;)
            {

#line 1930
                for(;;)
                {

#line 1930
                    uint lgTB_1 = firstbithigh_0(16U);

#line 1930
                    uint blk_2 = tid_0 >> lgTB_1;

#line 1930
                    uint lane_2 = tid_0 & 15U;

#line 1930
                    dftR_0(&r_5);

#line 1930
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 1930
                    float _S36 = tw_1.x;

#line 1930
                    float _S37 = tw_1.y;

#line 1930
                    k2_1 = 0U;

#line 1930
                    cr_0 = 1.0f;

#line 1930
                    ci_0 = 0.0f;

#line 1930
                    for(;;)
                    {

#line 1930
                        if(k2_1 < 64U)
                        {
                        }
                        else
                        {

#line 1930
                            break;
                        }

#line 1930
                        r_5[k2_1] = cmul_0(r_5[k2_1], float2(cr_0, ci_0));

#line 1930
                        float nr_1 = cr_0 * _S36 - ci_0 * _S37;

#line 1930
                        float _S38 = cr_0 * _S37 + ci_0 * _S36;

#line 1930
                        k2_1 = k2_1 + 1U;

#line 1930
                        cr_0 = nr_1;

#line 1930
                        ci_0 = _S38;

#line 1930
                    }

#line 1930
                    uint per_2 = 64U / _S21;

#line 1930
                    uint _S39 = max(0U, 1U);

#line 1930
                    uint blk2_2 = tid_0 / _S39;

#line 1930
                    uint lane2_2 = tid_0 % _S39;

#line 1930
                    for(;;)
                    {

#line 1930
                        thread array<float2, int(64)> out_1;

#line 1930
                        z_1 = 0U;

#line 1930
                        for(;;)
                        {

#line 1930
                            if(z_1 < 64U)
                            {
                            }
                            else
                            {

#line 1930
                                break;
                            }

#line 1930
                            out_1[z_1] = float2(0.0f, 0.0f);

#line 1930
                            z_1 = z_1 + 1U;

#line 1930
                        }

#line 1930
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 1930
                        uint p0_1 = computeWant_0(0U, 16U, 1024U, blk_2, lane_2, per_2, _S39, 16U, blk2_2, lane2_2);

#line 1930
                        uint _S40 = p0_1 & _S22;

#line 1930
                        uint _S41 = _S40 >> lgTB_1;

#line 1930
                        uint _S42 = _S41 * 1024U + ((p0_1 >> _S20) << lgTB_1) + (_S40 & spanMask_1);

#line 1930
                        c_2 = 0U;

#line 1930
                        for(;;)
                        {

#line 1930
                            if(c_2 < 16U)
                            {
                            }
                            else
                            {

#line 1930
                                break;
                            }

#line 1930
                            bool _S43 = c_2 == 0U;

#line 1930
                            if(!_S43)
                            {

#line 1930
                                simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 1930
                            }
                            else
                            {

#line 1930
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1930
                            }

#line 1930
                            j_2 = 0U;

#line 1930
                            for(;;)
                            {

#line 1930
                                if(j_2 < 4U)
                                {
                                }
                                else
                                {

#line 1930
                                    break;
                                }

#line 1930
                                stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_5[c_2 * 4U + j_2], &kernelContext_2);

#line 1930
                                j_2 = j_2 + 1U;

#line 1930
                            }

#line 1930
                            simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 1930
                            d_2 = 0U;

#line 1930
                            for(;;)
                            {

#line 1930
                                if(d_2 < 64U)
                                {
                                }
                                else
                                {

#line 1930
                                    break;
                                }

#line 1930
                                uint pz_1 = computeWant_0(d_2, 16U, 1024U, 0U, 0U, per_2, _S39, 16U, 0U, 0U);

#line 1930
                                uint _S44 = pz_1 & _S22;

#line 1930
                                uint iz_1 = _S44 >> lgTB_1;

#line 1930
                                uint az_1 = iz_1 * 1024U + ((pz_1 >> _S20) << lgTB_1) + (_S44 & spanMask_1);

#line 1930
                                uint i_7 = _S41 + iz_1;

#line 1930
                                uint _S45 = c_2 * 4U;

#line 1930
                                if(i_7 >= _S45)
                                {

#line 1930
                                    _S23 = i_7 < ((c_2 + 1U) * 4U);

#line 1930
                                }
                                else
                                {

#line 1930
                                    _S23 = false;

#line 1930
                                }

#line 1930
                                if(_S23)
                                {

#line 1930
                                    float2 _S46 = stgGet_0(_S42 + az_1 - _S45 * 1024U, &kernelContext_2);

#line 1930
                                    out_1[d_2] = _S46;

#line 1930
                                }

#line 1930
                                d_2 = d_2 + 1U;

#line 1930
                            }

#line 1930
                            c_2 = c_2 + 1U;

#line 1930
                        }

#line 1930
                        d_2 = 0U;

#line 1930
                        for(;;)
                        {

#line 1930
                            if(d_2 < 64U)
                            {
                            }
                            else
                            {

#line 1930
                                break;
                            }

#line 1930
                            r_5[d_2] = out_1[d_2];

#line 1930
                            d_2 = d_2 + 1U;

#line 1930
                        }

#line 1930
                        break;
                    }

#line 1930
                    break;
                }

#line 1930
                break;
            }

#line 1930
            break;
        }

#line 1930
        innermost_0(&r_5);

#line 1930
        break;
    }

#line 1930
    i_5 = 0U;
    for(;;)
    {

#line 1931
        if(i_5 < 64U)
        {
        }
        else
        {

#line 1931
            break;
        }

#line 1932
        uint lag_0 = slotToIndex_0(tid_0 * 64U + i_5);
        if(lag_0 >= (entryPointParams_1->params_0.z))
        {

#line 1933
            _S23 = lag_0 < (entryPointParams_1->params_0.w);

#line 1933
        }
        else
        {

#line 1933
            _S23 = false;

#line 1933
        }

#line 1933
        bool _S47;

#line 1933
        if(_S23)
        {

#line 1933
            _S47 = lag_0 < (entryPointParams_1->params_0.y - _S25);

#line 1933
        }
        else
        {

#line 1933
            _S47 = false;

#line 1933
        }

#line 1933
        if(_S47)
        {

#line 1933
            *((&kernelContext_2)->entryPointParams_output_0+(_S24 * entryPointParams_1->params_0.y + _S25 + lag_0)) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 1933
        }

#line 1931
        i_5 = i_5 + 1U;

#line 1931
    }

#line 1936
    return;
}
