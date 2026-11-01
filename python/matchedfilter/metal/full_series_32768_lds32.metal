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


#line 173 "mm_32768_fullCorrelationSeries_lds32.slang"
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


#line 328 "mm_32768_fullCorrelationSeries_lds32.slang"
float2 cmul_0(float2 a_1, float2 b_2)
{

#line 328
    float _S9 = a_1.x;

#line 328
    float _S10 = b_2.x;

#line 328
    float _S11 = a_1.y;

#line 328
    float _S12 = b_2.y;

#line 328
    return float2(_S9 * _S10 - _S11 * _S12, _S9 * _S12 + _S11 * _S10);
}


#line 613
void r4_0(float2 thread* a_2, float2 thread* b_3, float2 thread* c_1, float2 thread* d_0)
{
    float2 t0_0 = *a_2 + *c_1;

#line 615
    float2 t1_0 = *a_2 - *c_1;

#line 615
    float2 t2_0 = *b_3 + *d_0;

#line 615
    float2 t3_0 = *b_3 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_2 = t0_0 + t2_0;

#line 617
    *b_3 = t1_0 + j3_0;

#line 617
    *c_1 = t0_0 - t2_0;

#line 617
    *d_0 = t1_0 - j3_0;
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

        float2 _S14 = (*r_1)[j_0] - (*r_1)[j_0 + 16U];

#line 702
        float2 _S15 = mfTwiddle_0(6.28318548202514648f * float(j_0) / 32.0f);

#line 702
        v_0[j_0] = cmul_0(_S14, _S15);

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
        uint _S16 = 2U * k_0;

#line 706
        (*r_1)[_S16] = u_0[k_0];

#line 706
        (*r_1)[_S16 + 1U] = v_0[k_0];

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
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S17 = max(TB_0, 1U);

#line 332
    uint j_1 = d_1 / _S17;

#line 332
    uint m_0 = d_1 % _S17;

#line 332
    uint _S18;
    if(TB_0 <= 32U)
    {

#line 333
        _S18 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 333
    }
    else
    {

#line 333
        _S18 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 333
    }

#line 333
    return _S18;
}


#line 1878
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
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 317
    uint _S19 = 2U * i_1;

#line 317
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S19] = (as_type<uint>((v_1.x)));

#line 317
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S19 + 1U] = (as_type<uint>((v_1.y)));

#line 317
    return;
}


#line 318
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 318
    uint _S20 = 2U * i_2;

#line 318
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S20 + 1U]))));
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
    uint _S21;

#line 880
    if(i_3 < 2U)
    {

#line 880
        _S21 = 5U;

#line 880
    }
    else
    {

#line 880
        if(i_3 == 2U)
        {

#line 880
            _S21 = 5U;

#line 880
        }
        else
        {

#line 880
            _S21 = 1U;

#line 880
        }

#line 880
    }

#line 880
    return _S21;
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


#line 1878
[[kernel]] void fullCorrelationSeries(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], uint device* entryPointParams_starts_1 [[buffer(3)]], packed_float2 device* entryPointParams_output_1 [[buffer(4)]])
{

#line 1878
    uint _S22;

#line 1878
    uint k2_1;

#line 1878
    float cr_0;

#line 1878
    float ci_0;

#line 1878
    uint _S23;

#line 1878
    uint z_1;

#line 1878
    uint _S24;

#line 1878
    uint c_2;

#line 1878
    uint d_2;

#line 1878
    uint j_2;

#line 1878
    bool _S25;

#line 1878
    thread KernelContext_0 kernelContext_2;

#line 1878
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 1878
    (&kernelContext_2)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1878
    (&kernelContext_2)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1878
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1878
    (&kernelContext_2)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1878
    threadgroup array<uint, int(8192)> stg_1;

#line 1878
    (&kernelContext_2)->stg_0 = &stg_1;

#line 1883
    uint pair_0 = gid_0.x;

#line 1883
    uint tid_0 = lid_0.x;
    uint d_3 = pair_0 / entryPointParams_1->params_0.x;

#line 1884
    uint _S26 = pair_0 % entryPointParams_1->params_0.x;
    uint _S27 = (&kernelContext_2)->entryPointParams_starts_0[d_3];
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    thread array<float2, int(32)> r_4;

#line 1888
    uint i_4 = 0U;
    for(;;)
    {

#line 1889
        if(i_4 < 32U)
        {
        }
        else
        {

#line 1889
            break;
        }

#line 1890
        uint idx_0 = tid_0 + 1024U * i_4;
        r_4[i_4] = cmulConj_0(cload_0((&kernelContext_2)->entryPointParams_data_0, d_3 * 32768U + idx_0), cload_0((&kernelContext_2)->entryPointParams_tmpl_0, _S26 * 32768U + idx_0));

#line 1889
        i_4 = i_4 + 1U;

#line 1889
    }



    for(;;)
    {

#line 1893
        for(;;)
        {

#line 1893
            for(;;)
            {

#line 1893
                for(;;)
                {

#line 1893
                    uint lgTB_0 = firstbithigh_0(1024U);

#line 1893
                    _S22 = lgTB_0;

#line 1893
                    uint lgLn_0 = firstbithigh_0(32768U);

#line 1893
                    uint blk_1 = tid_0 >> lgTB_0;

#line 1893
                    uint lane_1 = tid_0 & 1023U;

#line 1893
                    dftR_0(&r_4);

#line 1893
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 32768.0f);

#line 1893
                    float _S28 = tw_0.x;

#line 1893
                    float _S29 = tw_0.y;

#line 1893
                    k2_1 = 0U;

#line 1893
                    cr_0 = 1.0f;

#line 1893
                    ci_0 = 0.0f;

#line 1893
                    for(;;)
                    {

#line 1893
                        if(k2_1 < 32U)
                        {
                        }
                        else
                        {

#line 1893
                            break;
                        }

#line 1893
                        r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 1893
                        float nr_0 = cr_0 * _S28 - ci_0 * _S29;

#line 1893
                        float _S30 = cr_0 * _S29 + ci_0 * _S28;

#line 1893
                        k2_1 = k2_1 + 1U;

#line 1893
                        cr_0 = nr_0;

#line 1893
                        ci_0 = _S30;

#line 1893
                    }

#line 1893
                    uint per_1 = 32U / max(1024U, 1U);

#line 1893
                    uint _S31 = max(32U, 1U);

#line 1893
                    _S23 = _S31;

#line 1893
                    uint blk2_1 = tid_0 / _S31;

#line 1893
                    uint lane2_1 = tid_0 % _S31;

#line 1893
                    for(;;)
                    {

#line 1893
                        thread array<float2, int(32)> out_0;

#line 1893
                        z_1 = 0U;

#line 1893
                        for(;;)
                        {

#line 1893
                            if(z_1 < 32U)
                            {
                            }
                            else
                            {

#line 1893
                                break;
                            }

#line 1893
                            out_0[z_1] = float2(0.0f, 0.0f);

#line 1893
                            z_1 = z_1 + 1U;

#line 1893
                        }

#line 1893
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 1893
                        _S24 = spanMask_0;

#line 1893
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 1893
                        uint p0_0 = computeWant_0(0U, 1024U, 32768U, blk_1, lane_1, per_1, _S31, 1024U, blk2_1, lane2_1);

#line 1893
                        uint _S32 = p0_0 & lenMask_0;

#line 1893
                        uint _S33 = _S32 >> lgTB_0;

#line 1893
                        uint _S34 = _S33 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S32 & spanMask_0);

#line 1893
                        c_2 = 0U;

#line 1893
                        for(;;)
                        {

#line 1893
                            if(c_2 < 8U)
                            {
                            }
                            else
                            {

#line 1893
                                break;
                            }

#line 1893
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1893
                            j_2 = 0U;

#line 1893
                            for(;;)
                            {

#line 1893
                                if(j_2 < 4U)
                                {
                                }
                                else
                                {

#line 1893
                                    break;
                                }

#line 1893
                                stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_4[c_2 * 4U + j_2], &kernelContext_2);

#line 1893
                                j_2 = j_2 + 1U;

#line 1893
                            }

#line 1893
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1893
                            d_2 = 0U;

#line 1893
                            for(;;)
                            {

#line 1893
                                if(d_2 < 32U)
                                {
                                }
                                else
                                {

#line 1893
                                    break;
                                }

#line 1893
                                uint pz_0 = computeWant_0(d_2, 1024U, 32768U, 0U, 0U, per_1, _S31, 1024U, 0U, 0U);

#line 1893
                                uint _S35 = pz_0 & lenMask_0;

#line 1893
                                uint iz_0 = _S35 >> lgTB_0;

#line 1893
                                uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S35 & spanMask_0);

#line 1893
                                uint i_5 = _S33 + iz_0;

#line 1893
                                uint _S36 = c_2 * 4U;

#line 1893
                                if(i_5 >= _S36)
                                {

#line 1893
                                    _S25 = i_5 < ((c_2 + 1U) * 4U);

#line 1893
                                }
                                else
                                {

#line 1893
                                    _S25 = false;

#line 1893
                                }

#line 1893
                                if(_S25)
                                {

#line 1893
                                    float2 _S37 = stgGet_0(_S34 + az_0 - _S36 * 1024U, &kernelContext_2);

#line 1893
                                    out_0[d_2] = _S37;

#line 1893
                                }

#line 1893
                                d_2 = d_2 + 1U;

#line 1893
                            }

#line 1893
                            c_2 = c_2 + 1U;

#line 1893
                        }

#line 1893
                        d_2 = 0U;

#line 1893
                        for(;;)
                        {

#line 1893
                            if(d_2 < 32U)
                            {
                            }
                            else
                            {

#line 1893
                                break;
                            }

#line 1893
                            r_4[d_2] = out_0[d_2];

#line 1893
                            d_2 = d_2 + 1U;

#line 1893
                        }

#line 1893
                        break;
                    }

#line 1893
                    break;
                }

#line 1893
                break;
            }

#line 1893
            for(;;)
            {

#line 1893
                for(;;)
                {

#line 1893
                    uint lgTB_1 = firstbithigh_0(32U);

#line 1893
                    uint blk_2 = tid_0 >> lgTB_1;

#line 1893
                    uint lane_2 = tid_0 & 31U;

#line 1893
                    dftR_0(&r_4);

#line 1893
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 1893
                    float _S38 = tw_1.x;

#line 1893
                    float _S39 = tw_1.y;

#line 1893
                    k2_1 = 0U;

#line 1893
                    cr_0 = 1.0f;

#line 1893
                    ci_0 = 0.0f;

#line 1893
                    for(;;)
                    {

#line 1893
                        if(k2_1 < 32U)
                        {
                        }
                        else
                        {

#line 1893
                            break;
                        }

#line 1893
                        r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 1893
                        float nr_1 = cr_0 * _S38 - ci_0 * _S39;

#line 1893
                        float _S40 = cr_0 * _S39 + ci_0 * _S38;

#line 1893
                        k2_1 = k2_1 + 1U;

#line 1893
                        cr_0 = nr_1;

#line 1893
                        ci_0 = _S40;

#line 1893
                    }

#line 1893
                    uint per_2 = 32U / _S23;

#line 1893
                    uint _S41 = max(1U, 1U);

#line 1893
                    uint blk2_2 = tid_0 / _S41;

#line 1893
                    uint lane2_2 = tid_0 % _S41;

#line 1893
                    for(;;)
                    {

#line 1893
                        thread array<float2, int(32)> out_1;

#line 1893
                        z_1 = 0U;

#line 1893
                        for(;;)
                        {

#line 1893
                            if(z_1 < 32U)
                            {
                            }
                            else
                            {

#line 1893
                                break;
                            }

#line 1893
                            out_1[z_1] = float2(0.0f, 0.0f);

#line 1893
                            z_1 = z_1 + 1U;

#line 1893
                        }

#line 1893
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 1893
                        uint p0_1 = computeWant_0(0U, 32U, 1024U, blk_2, lane_2, per_2, _S41, 32U, blk2_2, lane2_2);

#line 1893
                        uint _S42 = p0_1 & _S24;

#line 1893
                        uint _S43 = _S42 >> lgTB_1;

#line 1893
                        uint _S44 = _S43 * 1024U + ((p0_1 >> _S22) << lgTB_1) + (_S42 & spanMask_1);

#line 1893
                        c_2 = 0U;

#line 1893
                        for(;;)
                        {

#line 1893
                            if(c_2 < 8U)
                            {
                            }
                            else
                            {

#line 1893
                                break;
                            }

#line 1893
                            bool _S45 = c_2 == 0U;

#line 1893
                            if(!_S45)
                            {

#line 1893
                                simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 1893
                            }
                            else
                            {

#line 1893
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1893
                            }

#line 1893
                            j_2 = 0U;

#line 1893
                            for(;;)
                            {

#line 1893
                                if(j_2 < 4U)
                                {
                                }
                                else
                                {

#line 1893
                                    break;
                                }

#line 1893
                                stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_4[c_2 * 4U + j_2], &kernelContext_2);

#line 1893
                                j_2 = j_2 + 1U;

#line 1893
                            }

#line 1893
                            simdgroup_barrier(metal::mem_flags::mem_threadgroup);

#line 1893
                            d_2 = 0U;

#line 1893
                            for(;;)
                            {

#line 1893
                                if(d_2 < 32U)
                                {
                                }
                                else
                                {

#line 1893
                                    break;
                                }

#line 1893
                                uint pz_1 = computeWant_0(d_2, 32U, 1024U, 0U, 0U, per_2, _S41, 32U, 0U, 0U);

#line 1893
                                uint _S46 = pz_1 & _S24;

#line 1893
                                uint iz_1 = _S46 >> lgTB_1;

#line 1893
                                uint az_1 = iz_1 * 1024U + ((pz_1 >> _S22) << lgTB_1) + (_S46 & spanMask_1);

#line 1893
                                uint i_6 = _S43 + iz_1;

#line 1893
                                uint _S47 = c_2 * 4U;

#line 1893
                                if(i_6 >= _S47)
                                {

#line 1893
                                    _S25 = i_6 < ((c_2 + 1U) * 4U);

#line 1893
                                }
                                else
                                {

#line 1893
                                    _S25 = false;

#line 1893
                                }

#line 1893
                                if(_S25)
                                {

#line 1893
                                    float2 _S48 = stgGet_0(_S44 + az_1 - _S47 * 1024U, &kernelContext_2);

#line 1893
                                    out_1[d_2] = _S48;

#line 1893
                                }

#line 1893
                                d_2 = d_2 + 1U;

#line 1893
                            }

#line 1893
                            c_2 = c_2 + 1U;

#line 1893
                        }

#line 1893
                        d_2 = 0U;

#line 1893
                        for(;;)
                        {

#line 1893
                            if(d_2 < 32U)
                            {
                            }
                            else
                            {

#line 1893
                                break;
                            }

#line 1893
                            r_4[d_2] = out_1[d_2];

#line 1893
                            d_2 = d_2 + 1U;

#line 1893
                        }

#line 1893
                        break;
                    }

#line 1893
                    break;
                }

#line 1893
                break;
            }

#line 1893
            break;
        }

#line 1893
        innermost_0(&r_4);

#line 1893
        break;
    }

#line 1893
    i_4 = 0U;
    for(;;)
    {

#line 1894
        if(i_4 < 32U)
        {
        }
        else
        {

#line 1894
            break;
        }

#line 1895
        uint lag_0 = slotToIndex_0(tid_0 * 32U + i_4);
        if(lag_0 >= (entryPointParams_1->params_0.z))
        {

#line 1896
            _S25 = lag_0 < (entryPointParams_1->params_0.w);

#line 1896
        }
        else
        {

#line 1896
            _S25 = false;

#line 1896
        }

#line 1896
        bool _S49;

#line 1896
        if(_S25)
        {

#line 1896
            _S49 = lag_0 < (entryPointParams_1->params_0.y - _S27);

#line 1896
        }
        else
        {

#line 1896
            _S49 = false;

#line 1896
        }

#line 1896
        if(_S49)
        {

#line 1896
            *((&kernelContext_2)->entryPointParams_output_0+(_S26 * entryPointParams_1->params_0.y + _S27 + lag_0)) = packed_float2(float2(r_4[i_4].x, r_4[i_4].y)) ;

#line 1896
        }

#line 1894
        i_4 = i_4 + 1U;

#line 1894
    }

#line 1899
    return;
}
