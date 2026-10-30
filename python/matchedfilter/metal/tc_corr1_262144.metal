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


#line 317 "tc_corr1_262144.slang"
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


#line 493
void r4_0(float2 thread* a_1, float2 thread* b_1, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 495
    float2 t1_0 = *a_1 - *c_0;

#line 495
    float2 t2_0 = *b_1 + *d_0;

#line 495
    float2 t3_0 = *b_1 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 497
    *b_1 = t1_0 + j3_0;

#line 497
    *c_0 = t0_0 - t2_0;

#line 497
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


#line 529
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 536
    uint n1_0 = 0U;
    for(;;)
    {

#line 537
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 537
            break;
        }

#line 537
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 537
        n1_0 = n1_0 + 1U;

#line 537
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 538
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 538
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 539
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 539
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 540
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 540
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 540
    uint k2_0 = 0U;
    for(;;)
    {

#line 541
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 541
            break;
        }

#line 541
        uint _S10 = 4U * k2_0;

#line 541
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 541
        k2_0 = k2_0 + 1U;

#line 541
    }

    float2 t_0 = (*r_0)[int(1)];

#line 543
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 543
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 544
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 544
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 545
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 545
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 546
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 546
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 547
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 547
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 548
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 548
    (*r_0)[int(14)] = t_5;
    return;
}


#line 101 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 318 "tc_corr1_262144.slang"
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


#line 305 "tc_corr1_262144.slang"
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


#line 718
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 719
    uint j_1;

#line 730
    thread array<float2, int(16)> out_0;

#line 730
    uint z_0 = 0U;
    for(;;)
    {

#line 731
        if(z_0 < 16U)
        {
        }
        else
        {

#line 731
            break;
        }

#line 731
        out_0[z_0] = float2(0.0f, 0.0f);

#line 731
        z_0 = z_0 + 1U;

#line 731
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S15 = p0_0 & lenMask_0;

#line 737
    uint _S16 = (_S15 >> lgSpan_0) * 32U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 737
    uint c_1 = 0U;

    for(;;)
    {

#line 739
        if(c_1 < 1U)
        {
        }
        else
        {

#line 739
            break;
        }

#line 740
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 740
        j_1 = 0U;
        for(;;)
        {

#line 741
            if(j_1 < 16U)
            {
            }
            else
            {

#line 741
                break;
            }

#line 741
            stgPut_0(j_1 * 32U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 741
            j_1 = j_1 + 1U;

#line 741
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 742
        uint d_2 = 0U;
        for(;;)
        {

#line 743
            if(d_2 < 16U)
            {
            }
            else
            {

#line 743
                break;
            }

#line 744
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S17 = pz_0 & lenMask_0;
            uint az_0 = (_S17 >> lgSpan_0) * 32U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S17 & spanMask_0);

#line 746
            float2 _S18 = stgGet_0(_S16 + az_0 - c_1 * 16U * 32U, kernelContext_2);


            out_0[d_2] = _S18;

#line 743
            d_2 = d_2 + 1U;

#line 743
        }

#line 739
        c_1 = c_1 + 1U;

#line 739
    }

#line 739
    j_1 = 0U;

#line 752
    for(;;)
    {

#line 752
        if(j_1 < 16U)
        {
        }
        else
        {

#line 752
            break;
        }

#line 752
        (*r_1)[j_1] = out_0[j_1];

#line 752
        j_1 = j_1 + 1U;

#line 752
    }
    return;
}


#line 504
void dft2_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    float2 a_3 = (*r_2)[o_0];

#line 506
    float2 b_3 = (*r_2)[o_0 + 1U];

#line 506
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 506
    (*r_2)[o_0 + 1U] = a_3 - b_3;
    return;
}


#line 632
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 632
    uint b_4 = 0U;

#line 642
    for(;;)
    {

#line 642
        if(b_4 < 8U)
        {
        }
        else
        {

#line 642
            break;
        }

#line 642
        dft2_0(r_3, b_4 * 2U);

#line 642
        b_4 = b_4 + 1U;

#line 642
    }

    return;
}


#line 820
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 820
    uint _S19;

#line 820
    uint k2_1;

#line 820
    float cr_0;

#line 820
    float ci_0;

#line 820
    uint _S20;

#line 820
    for(;;)
    {

#line 820
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(32U);

#line 11
                _S19 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(512U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 31U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 512.0f);
                float _S21 = tw_0.x;

#line 40
                float _S22 = tw_0.y;

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
                    float nr_0 = cr_0 * _S21 - ci_0 * _S22;
                    float _S23 = cr_0 * _S22 + ci_0 * _S21;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S23;

#line 42
                }

#line 50
                uint per_2 = 16U / max(32U, 1U);
                uint _S24 = max(2U, 1U);

#line 51
                _S20 = _S24;
                uint blk2_2 = tid_0 / _S24;

#line 52
                uint lane2_2 = tid_0 % _S24;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 32U, 512U, blk_2, lane_2, per_2, _S24, 32U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(2U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 1U;


                dft16_0(r_4);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 32.0f);
                float _S25 = tw_1.x;

#line 40
                float _S26 = tw_1.y;

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
                    float nr_1 = cr_0 * _S25 - ci_0 * _S26;
                    float _S27 = cr_0 * _S26 + ci_0 * _S25;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S27;

#line 42
                }

#line 50
                uint per_3 = 16U / _S20;
                uint _S28 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S28;

#line 52
                uint lane2_3 = tid_0 % _S28;

#line 52
                exchange_0(r_4, _S19, lgTB_1, 2U, 32U, blk_3, lane_3, per_3, _S28, 2U, blk2_3, lane2_3, kernelContext_3);

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

#line 823 "tc_corr1_262144.slang"
    return;
}


#line 777
uint lgOf_0(uint i_2)
{

#line 777
    uint _S29;

#line 777
    if(i_2 < 2U)
    {

#line 777
        _S29 = 4U;

#line 777
    }
    else
    {

#line 777
        _S29 = 1U;

#line 777
    }

#line 777
    return _S29;
}


#line 779
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 783
    uint lg_1 = lgOf_0(1U);

#line 783
    uint lg_2 = lgOf_0(0U);

#line 788
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1894
[[kernel]] void tcStage1(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], packed_float2 device* entryPointParams_scratch_1 [[buffer(3)]])
{

#line 1894
    thread KernelContext_0 kernelContext_4;

#line 1894
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1894
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1894
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1894
    (&kernelContext_4)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 1894
    threadgroup array<uint, int(1024)> stg_1;

#line 1894
    (&kernelContext_4)->stg_0 = &stg_1;



    uint _S30 = gid_0.x;

#line 1898
    uint pair_0 = _S30 / 512U;

#line 1898
    uint _S31 = _S30 % 512U;
    uint _S32 = pair_0 / entryPointParams_1->ntmpl_0;

#line 1899
    uint _S33 = pair_0 % entryPointParams_1->ntmpl_0;
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;

    thread array<float2, int(16)> r_5;

#line 1904
    uint m_1 = 0U;
    for(;;)
    {

#line 1905
        if(m_1 < 16U)
        {
        }
        else
        {

#line 1905
            break;
        }

#line 1906
        uint j_2 = _S31 + 512U * (tid_1 + 32U * m_1);
        r_5[m_1] = cmulConj_0(float2(*((&kernelContext_4)->entryPointParams_data_0+(_S32 * 262144U + j_2))) , float2(*((&kernelContext_4)->entryPointParams_tmpl_0+(_S33 * 262144U + j_2))) );

#line 1905
        m_1 = m_1 + 1U;

#line 1905
    }

#line 1905
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 1905
    uint i_3 = 0U;

#line 1914
    for(;;)
    {

#line 1914
        if(i_3 < 16U)
        {
        }
        else
        {

#line 1914
            break;
        }

#line 1915
        uint k2_2 = slotToIndex_0(tid_1 * 16U + i_3);

#line 1915
        *((&kernelContext_4)->entryPointParams_scratch_0+(pair_0 * 262144U + k2_2 * 512U + _S31)) = packed_float2(cmul_0(r_5[i_3], mfTwiddle_0(6.28318548202514648f * float(_S31 * k2_2) / 2.62144e+05f))) ;

#line 1914
        i_3 = i_3 + 1U;

#line 1914
    }

#line 1919
    return;
}
