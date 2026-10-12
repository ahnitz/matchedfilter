#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;

#line 10912 "hlsl.meta.slang"
uint firstbithigh_0(uint value_0)
{

#line 10925
    if(value_0 == 0U)
    {

#line 10926
        return 4294967295U;
    }

#line 10927
    uint _S1 = clz(value_0);

#line 10927
    return 31U - _S1;
}


#line 467 "/home/ahnitz/projects/claude/searchdev/work/mf-metal-50/python/matchedfilter/metal/tc_corr2_4194304.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 469
    float2 t1_0 = *a_0 - *c_0;

#line 469
    float2 t2_0 = *b_0 + *d_0;

#line 469
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 471
    *b_0 = t1_0 + j3_0;

#line 471
    *c_0 = t0_0 - t2_0;

#line 471
    *d_0 = t1_0 - j3_0;
    return;
}


#line 261
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 261
    float _S2 = a_1.x;

#line 261
    float _S3 = b_1.x;

#line 261
    float _S4 = a_1.y;

#line 261
    float _S5 = b_1.y;

#line 261
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 503
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 510
    uint n1_0 = 0U;
    for(;;)
    {

#line 511
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 511
            break;
        }

#line 511
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 511
        n1_0 = n1_0 + 1U;

#line 511
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 512
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 512
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 513
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 513
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 514
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 514
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 514
    uint k2_0 = 0U;
    for(;;)
    {

#line 515
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 515
            break;
        }

#line 515
        uint _S6 = 4U * k2_0;

#line 515
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 515
        k2_0 = k2_0 + 1U;

#line 515
    }

    float2 t_0 = (*r_0)[int(1)];

#line 517
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 517
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 518
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 518
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 519
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 519
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 520
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 520
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 521
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 521
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 522
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 522
    (*r_0)[int(14)] = t_5;
    return;
}


#line 64 "/home/ahnitz/projects/claude/searchdev/work/mf-metal-50/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 263 "/home/ahnitz/projects/claude/searchdev/work/mf-metal-50/python/matchedfilter/metal/tc_corr2_4194304.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S7 = max(TB_0, 1U);

#line 265
    uint j_0 = d_1 / _S7;

#line 265
    uint m_0 = d_1 % _S7;

#line 265
    uint _S8;
    if(TB_0 <= 16U)
    {

#line 266
        _S8 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 266
    }
    else
    {

#line 266
        _S8 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 266
    }

#line 266
    return _S8;
}


#line 250
struct KernelContext_0
{
    packed_float2 device* entryPointParams_scratch_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 250
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 250
    uint _S9 = 2U * i_0;

#line 250
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9] = (as_type<uint>((v_0.x)));

#line 250
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9 + 1U] = (as_type<uint>((v_0.y)));

#line 250
    return;
}


#line 251
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 251
    uint _S10 = 2U * i_1;

#line 251
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10 + 1U]))));
}


#line 692
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 693
    uint j_1;

#line 704
    thread array<float2, int(16)> out_0;

#line 704
    uint z_0 = 0U;
    for(;;)
    {

#line 705
        if(z_0 < 16U)
        {
        }
        else
        {

#line 705
            break;
        }

#line 705
        out_0[z_0] = float2(0.0, 0.0);

#line 705
        z_0 = z_0 + 1U;

#line 705
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S11 = p0_0 & lenMask_0;

#line 711
    uint _S12 = _S11 >> lgSpan_0;

#line 711
    uint _S13 = _S12 * 128U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S11 & spanMask_0);

#line 711
    uint c_1 = 0U;

    for(;;)
    {

#line 713
        if(c_1 < 2U)
        {
        }
        else
        {

#line 713
            break;
        }

#line 714
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 714
        j_1 = 0U;
        for(;;)
        {

#line 715
            if(j_1 < 8U)
            {
            }
            else
            {

#line 715
                break;
            }

#line 715
            stgPut_0(j_1 * 128U + kernelContext_2->_tid_0, (*r_1)[c_1 * 8U + j_1], kernelContext_2);

#line 715
            j_1 = j_1 + 1U;

#line 715
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 716
        uint d_2 = 0U;
        for(;;)
        {

#line 717
            if(d_2 < 16U)
            {
            }
            else
            {

#line 717
                break;
            }

#line 718
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S14 = pz_0 & lenMask_0;

#line 719
            uint iz_0 = _S14 >> lgSpan_0;
            uint az_0 = iz_0 * 128U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);
            uint i_2 = _S12 + iz_0;
            uint _S15 = c_1 * 8U;

#line 722
            bool _S16;

#line 722
            if(i_2 >= _S15)
            {

#line 722
                _S16 = i_2 < ((c_1 + 1U) * 8U);

#line 722
            }
            else
            {

#line 722
                _S16 = false;

#line 722
            }

#line 722
            if(_S16)
            {

#line 722
                float2 _S17 = stgGet_0(_S13 + az_0 - _S15 * 128U, kernelContext_2);
                out_0[d_2] = _S17;

#line 722
            }

#line 717
            d_2 = d_2 + 1U;

#line 717
        }

#line 713
        c_1 = c_1 + 1U;

#line 713
    }

#line 713
    j_1 = 0U;

#line 726
    for(;;)
    {

#line 726
        if(j_1 < 16U)
        {
        }
        else
        {

#line 726
            break;
        }

#line 726
        (*r_1)[j_1] = out_0[j_1];

#line 726
        j_1 = j_1 + 1U;

#line 726
    }
    return;
}


#line 487
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_2;

#line 491
    uint s_0 = 1U;
    for(;;)
    {

#line 492
        if(s_0 < 8U)
        {
        }
        else
        {

#line 492
            break;
        }

#line 492
        uint j_2 = 0U;
        for(;;)
        {

#line 493
            if(j_2 < 4U)
            {
            }
            else
            {

#line 493
                break;
            }

#line 494
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S18 = o_0 + j_2;

#line 497
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0)), (*r_2)[_S18 + 4U]);
            uint _S19 = ((j_2 - k_0) << 1U) + k_0;

#line 498
            b_2[_S19] = (*r_2)[_S18] + t_6;

#line 498
            b_2[_S19 + s_0] = (*r_2)[_S18] - t_6;

#line 493
            j_2 = j_2 + 1U;

#line 493
        }

#line 493
        uint i_3 = 0U;

#line 500
        for(;;)
        {

#line 500
            if(i_3 < 8U)
            {
            }
            else
            {

#line 500
                break;
            }

#line 500
            (*r_2)[o_0 + i_3] = b_2[i_3];

#line 500
            i_3 = i_3 + 1U;

#line 500
        }

#line 492
        s_0 = s_0 << 1U;

#line 492
    }

#line 502
    return;
}


#line 606
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 606
    uint b_3 = 0U;

#line 614
    for(;;)
    {

#line 614
        if(b_3 < 2U)
        {
        }
        else
        {

#line 614
            break;
        }

#line 614
        dft8_0(r_3, b_3 * 8U);

#line 614
        b_3 = b_3 + 1U;

#line 614
    }



    return;
}


#line 782
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 782
    uint _S20;

#line 782
    uint k2_1;

#line 782
    float cr_0;

#line 782
    float ci_0;

#line 782
    uint _S21;

#line 782
    for(;;)
    {

#line 782
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/mf-metal-50/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(128U);

#line 11
                _S20 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(2048U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 127U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 2048.0);
                float _S22 = tw_0.x;

#line 27
                float _S23 = tw_0.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S22 - ci_0 * _S23;
                    float _S24 = cr_0 * _S23 + ci_0 * _S22;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S24;

#line 29
                }

#line 37
                uint per_2 = 16U / max(128U, 1U);
                uint _S25 = max(8U, 1U);

#line 38
                _S21 = _S25;
                uint blk2_2 = tid_0 / _S25;

#line 39
                uint lane2_2 = tid_0 % _S25;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 128U, 2048U, blk_2, lane_2, per_2, _S25, 128U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(8U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 7U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 128.0);
                float _S26 = tw_1.x;

#line 27
                float _S27 = tw_1.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S26 - ci_0 * _S27;
                    float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S28;

#line 29
                }

#line 37
                uint per_3 = 16U / _S21;
                uint _S29 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S29;

#line 39
                uint lane2_3 = tid_0 % _S29;

#line 39
                exchange_0(r_4, _S20, lgTB_1, 8U, 128U, blk_3, lane_3, per_3, _S29, 8U, blk2_3, lane2_3, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        break;
    }

#line 43
    innermost_0(r_4);

#line 785 "/home/ahnitz/projects/claude/searchdev/work/mf-metal-50/python/matchedfilter/metal/tc_corr2_4194304.slang"
    return;
}


#line 751
uint lgOf_0(uint i_4)
{

#line 751
    uint _S30;

#line 751
    if(i_4 < 2U)
    {

#line 751
        _S30 = 4U;

#line 751
    }
    else
    {

#line 751
        if(i_4 == 2U)
        {

#line 751
            _S30 = 3U;

#line 751
        }
        else
        {

#line 751
            _S30 = 1U;

#line 751
        }

#line 751
    }

#line 751
    return _S30;
}


#line 753
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 757
    uint lg_1 = lgOf_0(1U);

#line 757
    uint lg_2 = lgOf_0(0U);

#line 762
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1890
[[kernel]] void tcFullStage3(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], packed_float2 device* entryPointParams_scratch_1 [[buffer(0)]], packed_float2 device* entryPointParams_output_1 [[buffer(1)]])
{

#line 1890
    thread KernelContext_0 kernelContext_4;

#line 1890
    (&kernelContext_4)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 1890
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1890
    threadgroup array<uint, int(2048)> stg_1;

#line 1890
    (&kernelContext_4)->stg_0 = &stg_1;



    uint _S31 = gid_0.x;

#line 1894
    uint _S32 = _S31 / 2048U;

#line 1894
    uint _S33 = _S31 % 2048U;
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 1898
    uint m_1 = 0U;
    for(;;)
    {

#line 1899
        if(m_1 < 16U)
        {
        }
        else
        {

#line 1899
            break;
        }

#line 1900
        r_5[m_1] = float2(*((&kernelContext_4)->entryPointParams_scratch_0+(_S32 * 4194304U + _S33 * 2048U + tid_1 + 128U * m_1))) ;

#line 1899
        m_1 = m_1 + 1U;

#line 1899
    }

#line 1899
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 1899
    uint i_5 = 0U;


    for(;;)
    {

#line 1902
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1902
            break;
        }

#line 1902
        *((&kernelContext_4)->entryPointParams_output_0+(_S32 * 4194304U + slotToIndex_0(tid_1 * 16U + i_5) * 2048U + _S33)) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 1902
        i_5 = i_5 + 1U;

#line 1902
    }



    return;
}
