#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;

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


#line 317 "tc_corr1_1048576.slang"
float2 cmulConj_0(float2 a_0, float2 b_0)
{

#line 317
    float _S2 = a_0.x;

#line 317
    float _S3 = b_0.x;

#line 317
    float _S4 = a_0.y;

#line 317
    float _S5 = b_0.y;

#line 317
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 522
void r4_0(float2 thread* a_1, float2 thread* b_1, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 524
    float2 t1_0 = *a_1 - *c_0;

#line 524
    float2 t2_0 = *b_1 + *d_0;

#line 524
    float2 t3_0 = *b_1 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 526
    *b_1 = t1_0 + j3_0;

#line 526
    *c_0 = t0_0 - t2_0;

#line 526
    *d_0 = t1_0 - j3_0;
    return;
}


#line 316
float2 cmul_0(float2 a_2, float2 b_2)
{

#line 316
    float _S6 = a_2.x;

#line 316
    float _S7 = b_2.x;

#line 316
    float _S8 = a_2.y;

#line 316
    float _S9 = b_2.y;

#line 316
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 558
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 565
    uint n1_0 = 0U;
    for(;;)
    {

#line 566
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 566
            break;
        }

#line 566
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 566
        n1_0 = n1_0 + 1U;

#line 566
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 567
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 567
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 568
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 568
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 569
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 569
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 569
    uint k2_0 = 0U;
    for(;;)
    {

#line 570
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 570
            break;
        }

#line 570
        uint _S10 = 4U * k2_0;

#line 570
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 570
        k2_0 = k2_0 + 1U;

#line 570
    }

    float2 t_0 = (*r_0)[int(1)];

#line 572
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 572
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 573
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 573
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 574
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 574
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 575
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 575
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 576
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 576
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 577
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 577
    (*r_0)[int(14)] = t_5;
    return;
}


#line 127 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 318 "tc_corr1_1048576.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 320
    uint j_0 = d_1 / _S11;

#line 320
    uint m_0 = d_1 % _S11;

#line 320
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 321
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 321
    }
    else
    {

#line 321
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 321
    }

#line 321
    return _S12;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint ntmpl_0;
};


#line 305 "tc_corr1_1048576.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    packed_float2 device* entryPointParams_scratch_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 305
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 305
    uint _S13 = 2U * i_0;

#line 305
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13] = (as_type<uint>((v_0.x)));

#line 305
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13 + 1U] = (as_type<uint>((v_0.y)));

#line 305
    return;
}


#line 306
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 306
    uint _S14 = 2U * i_1;

#line 306
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 747
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 748
    uint j_1;

#line 759
    thread array<float2, int(16)> out_0;

#line 759
    uint z_0 = 0U;
    for(;;)
    {

#line 760
        if(z_0 < 16U)
        {
        }
        else
        {

#line 760
            break;
        }

#line 760
        out_0[z_0] = float2(0.0f, 0.0f);

#line 760
        z_0 = z_0 + 1U;

#line 760
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S15 = p0_0 & lenMask_0;

#line 766
    uint _S16 = _S15 >> lgSpan_0;

#line 766
    uint _S17 = _S16 * 64U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 766
    uint c_1 = 0U;

    for(;;)
    {

#line 768
        if(c_1 < 2U)
        {
        }
        else
        {

#line 768
            break;
        }

#line 769
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 769
        j_1 = 0U;
        for(;;)
        {

#line 770
            if(j_1 < 8U)
            {
            }
            else
            {

#line 770
                break;
            }

#line 770
            stgPut_0(j_1 * 64U + kernelContext_2->_tid_0, (*r_1)[c_1 * 8U + j_1], kernelContext_2);

#line 770
            j_1 = j_1 + 1U;

#line 770
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 771
        uint d_2 = 0U;
        for(;;)
        {

#line 772
            if(d_2 < 16U)
            {
            }
            else
            {

#line 772
                break;
            }

#line 773
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S18 = pz_0 & lenMask_0;

#line 774
            uint iz_0 = _S18 >> lgSpan_0;
            uint az_0 = iz_0 * 64U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S18 & spanMask_0);
            uint i_2 = _S16 + iz_0;
            uint _S19 = c_1 * 8U;

#line 777
            bool _S20;

#line 777
            if(i_2 >= _S19)
            {

#line 777
                _S20 = i_2 < ((c_1 + 1U) * 8U);

#line 777
            }
            else
            {

#line 777
                _S20 = false;

#line 777
            }

#line 777
            if(_S20)
            {

#line 777
                float2 _S21 = stgGet_0(_S17 + az_0 - _S19 * 64U, kernelContext_2);
                out_0[d_2] = _S21;

#line 777
            }

#line 772
            d_2 = d_2 + 1U;

#line 772
        }

#line 768
        c_1 = c_1 + 1U;

#line 768
    }

#line 768
    j_1 = 0U;

#line 781
    for(;;)
    {

#line 781
        if(j_1 < 16U)
        {
        }
        else
        {

#line 781
            break;
        }

#line 781
        (*r_1)[j_1] = out_0[j_1];

#line 781
        j_1 = j_1 + 1U;

#line 781
    }
    return;
}


#line 537
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 540
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 540
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 661
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 661
    uint b_3 = 0U;

#line 670
    for(;;)
    {

#line 670
        if(b_3 < 4U)
        {
        }
        else
        {

#line 670
            break;
        }

#line 670
        dft4_0(r_3, b_3 * 4U);

#line 670
        b_3 = b_3 + 1U;

#line 670
    }


    return;
}


#line 849
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 849
    uint _S22;

#line 849
    uint k2_1;

#line 849
    float cr_0;

#line 849
    float ci_0;

#line 849
    uint _S23;

#line 849
    for(;;)
    {

#line 849
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

#line 852 "tc_corr1_1048576.slang"
    return;
}


#line 806
uint lgOf_0(uint i_3)
{

#line 806
    uint _S32;

#line 806
    if(i_3 < 2U)
    {

#line 806
        _S32 = 4U;

#line 806
    }
    else
    {

#line 806
        _S32 = 1U;

#line 806
    }

#line 806
    return _S32;
}


#line 808
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 812
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 812
    uint lg_2 = lgOf_0(1U);

#line 812
    uint lg_3 = lgOf_0(0U);

#line 817
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 1972
[[kernel]] void tcStage1(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], packed_float2 device* entryPointParams_scratch_1 [[buffer(3)]])
{

#line 1972
    thread KernelContext_0 kernelContext_4;

#line 1972
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1972
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1972
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1972
    (&kernelContext_4)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 1972
    threadgroup array<uint, int(1024)> stg_1;

#line 1972
    (&kernelContext_4)->stg_0 = &stg_1;



    uint _S33 = gid_0.x;

#line 1976
    uint pair_0 = _S33 / 1024U;

#line 1976
    uint _S34 = _S33 % 1024U;
    uint _S35 = pair_0 / entryPointParams_1->ntmpl_0;

#line 1977
    uint _S36 = pair_0 % entryPointParams_1->ntmpl_0;
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;

    thread array<float2, int(16)> r_5;

#line 1982
    uint m_1 = 0U;
    for(;;)
    {

#line 1983
        if(m_1 < 16U)
        {
        }
        else
        {

#line 1983
            break;
        }

#line 1984
        uint j_2 = _S34 + 1024U * (tid_1 + 64U * m_1);
        r_5[m_1] = cmulConj_0(float2(*((&kernelContext_4)->entryPointParams_data_0+(_S35 * 1048576U + j_2))) , float2(*((&kernelContext_4)->entryPointParams_tmpl_0+(_S36 * 1048576U + j_2))) );

#line 1983
        m_1 = m_1 + 1U;

#line 1983
    }

#line 1983
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 1983
    uint i_4 = 0U;

#line 1992
    for(;;)
    {

#line 1992
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1992
            break;
        }

#line 1993
        uint k2_2 = slotToIndex_0(tid_1 * 16U + i_4);

#line 1993
        *((&kernelContext_4)->entryPointParams_scratch_0+(pair_0 * 1048576U + k2_2 * 1024U + _S34)) = packed_float2(cmul_0(r_5[i_4], mfTwiddle_0(6.28318548202514648f * float(_S34 * k2_2) / 1.048576e+06f))) ;

#line 1992
        i_4 = i_4 + 1U;

#line 1992
    }

#line 1997
    return;
}
