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


#line 345 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/python/matchedfilter/metal/tc_fwd2_524288.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 347
    float2 t1_0 = *a_0 - *c_0;

#line 347
    float2 t2_0 = *b_0 + *d_0;

#line 347
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 349
    *b_0 = t1_0 + j3_0;

#line 349
    *c_0 = t0_0 - t2_0;

#line 349
    *d_0 = t1_0 - j3_0;
    return;
}


#line 187
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 187
    float _S2 = a_1.x;

#line 187
    float _S3 = b_1.x;

#line 187
    float _S4 = a_1.y;

#line 187
    float _S5 = b_1.y;

#line 187
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 381
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 388
    uint n1_0 = 0U;
    for(;;)
    {

#line 389
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 389
            break;
        }

#line 389
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 389
        n1_0 = n1_0 + 1U;

#line 389
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 390
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 390
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 391
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 391
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 392
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 392
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 392
    uint k2_0 = 0U;
    for(;;)
    {

#line 393
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 393
            break;
        }

#line 393
        uint _S6 = 4U * k2_0;

#line 393
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 393
        k2_0 = k2_0 + 1U;

#line 393
    }

    float2 t_0 = (*r_0)[int(1)];

#line 395
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 395
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 396
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 396
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 397
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 397
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 398
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 398
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 399
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 399
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 400
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 400
    (*r_0)[int(14)] = t_5;
    return;
}


#line 12 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 176 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/python/matchedfilter/metal/tc_fwd2_524288.slang"
struct KernelContext_0
{
    packed_float2 device* entryPointParams_scratch_0;
    packed_float2 device* entryPointParams_spectra_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 176
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 176
    uint _S7 = 2U * i_0;

#line 176
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S7] = (as_type<uint>((v_0.x)));

#line 176
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S7 + 1U] = (as_type<uint>((v_0.y)));

#line 176
    return;
}


#line 189
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S8 = max(TB_0, 1U);

#line 191
    uint j_0 = d_1 / _S8;

#line 191
    uint m_0 = d_1 % _S8;

#line 191
    uint _S9;
    if(TB_0 <= 16U)
    {

#line 192
        _S9 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 192
    }
    else
    {

#line 192
        _S9 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 192
    }

#line 192
    return _S9;
}


#line 177
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 177
    uint _S10 = 2U * i_1;

#line 177
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10 + 1U]))));
}


#line 506
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 507
    uint j_1;

#line 518
    thread array<float2, int(16)> out_0;

#line 518
    uint z_0 = 0U;
    for(;;)
    {

#line 519
        if(z_0 < 16U)
        {
        }
        else
        {

#line 519
            break;
        }

#line 519
        out_0[z_0] = float2(0.0, 0.0);

#line 519
        z_0 = z_0 + 1U;

#line 519
    }
    uint _S11 = (1U << lgSpan_0) - 1U;
    uint _S12 = (1U << lgLen_0) - 1U;

#line 521
    uint c_1 = 0U;
    for(;;)
    {

#line 522
        if(c_1 < 1U)
        {
        }
        else
        {

#line 522
            break;
        }

#line 523
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 523
        j_1 = 0U;
        for(;;)
        {

#line 524
            if(j_1 < 16U)
            {
            }
            else
            {

#line 524
                break;
            }

#line 524
            stgPut_0(j_1 * 32U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 524
            j_1 = j_1 + 1U;

#line 524
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 525
        uint d_2 = 0U;
        for(;;)
        {

#line 526
            if(d_2 < 16U)
            {
            }
            else
            {

#line 526
                break;
            }

#line 527
            uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
            uint b_2 = p_0 >> lgLen_0;

#line 528
            uint rem_0 = p_0 & _S12;
            uint i_2 = rem_0 >> lgSpan_0;

#line 529
            uint ln_0 = rem_0 & _S11;
            uint _S13 = c_1 * 16U;

#line 530
            bool _S14;

#line 530
            if(i_2 >= _S13)
            {

#line 530
                _S14 = i_2 < ((c_1 + 1U) * 16U);

#line 530
            }
            else
            {

#line 530
                _S14 = false;

#line 530
            }

#line 530
            if(_S14)
            {

#line 530
                float2 _S15 = stgGet_0((i_2 - _S13) * 32U + (b_2 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_2] = _S15;

#line 530
            }

#line 526
            d_2 = d_2 + 1U;

#line 526
        }

#line 522
        c_1 = c_1 + 1U;

#line 522
    }

#line 522
    j_1 = 0U;

#line 534
    for(;;)
    {

#line 534
        if(j_1 < 16U)
        {
        }
        else
        {

#line 534
            break;
        }

#line 534
        (*r_1)[j_1] = out_0[j_1];

#line 534
        j_1 = j_1 + 1U;

#line 534
    }
    return;
}


#line 356
void dft2_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    float2 a_2 = (*r_2)[o_0];

#line 358
    float2 b_3 = (*r_2)[o_0 + 1U];

#line 358
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 358
    (*r_2)[o_0 + 1U] = a_2 - b_3;
    return;
}


#line 484
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 484
    uint b_4 = 0U;

#line 494
    for(;;)
    {

#line 494
        if(b_4 < 8U)
        {
        }
        else
        {

#line 494
            break;
        }

#line 494
        dft2_0(r_3, b_4 * 2U);

#line 494
        b_4 = b_4 + 1U;

#line 494
    }

    return;
}


#line 589
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 589
    uint _S16;

#line 589
    uint k2_1;

#line 589
    float cr_0;

#line 589
    float ci_0;

#line 589
    uint _S17;

#line 589
    for(;;)
    {

#line 589
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(32U);

#line 11
                _S16 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(512U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 31U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 512.0);
                float _S18 = tw_0.x;

#line 27
                float _S19 = tw_0.y;

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
                    float nr_0 = cr_0 * _S18 - ci_0 * _S19;
                    float _S20 = cr_0 * _S19 + ci_0 * _S18;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S20;

#line 29
                }

#line 37
                uint per_2 = 16U / max(32U, 1U);
                uint _S21 = max(2U, 1U);

#line 38
                _S17 = _S21;
                uint blk2_2 = tid_0 / _S21;

#line 39
                uint lane2_2 = tid_0 % _S21;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 32U, 512U, blk_2, lane_2, per_2, _S21, 32U, blk2_2, lane2_2, kernelContext_3);

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

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 32.0);
                float _S22 = tw_1.x;

#line 27
                float _S23 = tw_1.y;

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
                    float nr_1 = cr_0 * _S22 - ci_0 * _S23;
                    float _S24 = cr_0 * _S23 + ci_0 * _S22;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S24;

#line 29
                }

#line 37
                uint per_3 = 16U / _S17;
                uint _S25 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S25;

#line 39
                uint lane2_3 = tid_0 % _S25;

#line 39
                exchange_0(r_4, _S16, lgTB_1, 2U, 32U, blk_3, lane_3, per_3, _S25, 2U, blk2_3, lane2_3, kernelContext_3);

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

#line 592 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/python/matchedfilter/metal/tc_fwd2_524288.slang"
    return;
}


#line 558
uint lgOf_0(uint i_3)
{

#line 558
    uint _S26;

#line 558
    if(i_3 < 2U)
    {

#line 558
        _S26 = 4U;

#line 558
    }
    else
    {

#line 558
        _S26 = 1U;

#line 558
    }

#line 558
    return _S26;
}


#line 560
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 564
    uint lg_1 = lgOf_0(1U);

#line 564
    uint lg_2 = lgOf_0(0U);

#line 569
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1343
[[kernel]] void tcForwardStage3(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], packed_float2 device* entryPointParams_scratch_1 [[buffer(0)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(1)]])
{

#line 1343
    thread KernelContext_0 kernelContext_4;

#line 1343
    (&kernelContext_4)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 1343
    (&kernelContext_4)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 1343
    threadgroup array<uint, int(1024)> stg_1;

#line 1343
    (&kernelContext_4)->stg_0 = &stg_1;



    uint _S27 = gid_0.x;

#line 1347
    uint _S28 = _S27 / 1024U;

#line 1347
    uint _S29 = _S27 % 1024U;
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 1351
    uint m_1 = 0U;
    for(;;)
    {

#line 1352
        if(m_1 < 16U)
        {
        }
        else
        {

#line 1352
            break;
        }

#line 1353
        r_5[m_1] = float2(*((&kernelContext_4)->entryPointParams_scratch_0+(_S28 * 524288U + _S29 * 512U + tid_1 + 32U * m_1))) ;

#line 1352
        m_1 = m_1 + 1U;

#line 1352
    }

#line 1352
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 1352
    uint i_4 = 0U;


    for(;;)
    {

#line 1355
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1355
            break;
        }

#line 1355
        *((&kernelContext_4)->entryPointParams_spectra_0+(_S28 * 524288U + slotToIndex_0(tid_1 * 16U + i_4) * 1024U + _S29)) = packed_float2(float2(r_5[i_4].x, - r_5[i_4].y)) ;

#line 1355
        i_4 = i_4 + 1U;

#line 1355
    }



    return;
}
