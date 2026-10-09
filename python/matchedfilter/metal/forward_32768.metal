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


#line 12 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 203 "/tmp/tmpkxwd5_fn/forward.slang"
float2 cmul_0(float2 a_0, float2 b_0)
{

#line 203
    float _S2 = a_0.x;

#line 203
    float _S3 = b_0.x;

#line 203
    float _S4 = a_0.y;

#line 203
    float _S5 = b_0.y;

#line 203
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 371
void r4_0(float2 thread* a_1, float2 thread* b_1, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 373
    float2 t1_0 = *a_1 - *c_0;

#line 373
    float2 t2_0 = *b_1 + *d_0;

#line 373
    float2 t3_0 = *b_1 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 375
    *b_1 = t1_0 + j3_0;

#line 375
    *c_0 = t0_0 - t2_0;

#line 375
    *d_0 = t1_0 - j3_0;
    return;
}


#line 407
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 414
    uint n1_0 = 0U;
    for(;;)
    {

#line 415
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 415
            break;
        }

#line 415
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 415
        n1_0 = n1_0 + 1U;

#line 415
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 416
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 416
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 417
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 417
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 418
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 418
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 418
    uint k2_0 = 0U;
    for(;;)
    {

#line 419
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 419
            break;
        }

#line 419
        uint _S6 = 4U * k2_0;

#line 419
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 419
        k2_0 = k2_0 + 1U;

#line 419
    }

    float2 t_0 = (*r_0)[int(1)];

#line 421
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 421
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 422
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 422
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 423
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 423
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 424
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 424
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 425
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 425
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 426
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 426
    (*r_0)[int(14)] = t_5;
    return;
}


#line 453
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 455
    thread array<float2, int(16)> v_0;

#line 455
    uint j_0 = 0U;
    for(;;)
    {

#line 456
        if(j_0 < 16U)
        {
        }
        else
        {

#line 456
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        v_0[j_0] = cmul_0((*r_1)[j_0] - (*r_1)[j_0 + 16U], mfTwiddle_0(6.28318548202514648 * float(j_0) / 32.0));

#line 456
        j_0 = j_0 + 1U;

#line 456
    }

#line 462
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 463
    uint k_0 = 0U;
    for(;;)
    {

#line 464
        if(k_0 < 16U)
        {
        }
        else
        {

#line 464
            break;
        }

#line 464
        uint _S7 = 2U * k_0;

#line 464
        (*r_1)[_S7] = u_0[k_0];

#line 464
        (*r_1)[_S7 + 1U] = v_0[k_0];

#line 464
        k_0 = k_0 + 1U;

#line 464
    }
    return;
}


#line 492
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint seriesLength_0;
};


#line 192 "/tmp/tmpkxwd5_fn/forward.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_spectra_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 192
void stgPut_0(uint i_0, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 192
    uint _S8 = 2U * i_0;

#line 192
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S8] = (as_type<uint>((v_1.x)));

#line 192
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S8 + 1U] = (as_type<uint>((v_1.y)));

#line 192
    return;
}


#line 205
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S9 = max(TB_0, 1U);

#line 207
    uint j_1 = d_1 / _S9;

#line 207
    uint m_0 = d_1 % _S9;

#line 207
    uint _S10;
    if(TB_0 <= 32U)
    {

#line 208
        _S10 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 208
    }
    else
    {

#line 208
        _S10 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 208
    }

#line 208
    return _S10;
}


#line 193
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 193
    uint _S11 = 2U * i_1;

#line 193
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S11]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S11 + 1U]))));
}


#line 567
void exchange_0(array<float2, int(32)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 568
    uint j_2;

#line 579
    thread array<float2, int(32)> out_0;

#line 579
    uint z_0 = 0U;
    for(;;)
    {

#line 580
        if(z_0 < 32U)
        {
        }
        else
        {

#line 580
            break;
        }

#line 580
        out_0[z_0] = float2(0.0, 0.0);

#line 580
        z_0 = z_0 + 1U;

#line 580
    }
    uint _S12 = (1U << lgSpan_0) - 1U;
    uint _S13 = (1U << lgLen_0) - 1U;

#line 582
    uint c_1 = 0U;
    for(;;)
    {

#line 583
        if(c_1 < 8U)
        {
        }
        else
        {

#line 583
            break;
        }

#line 584
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 584
        j_2 = 0U;
        for(;;)
        {

#line 585
            if(j_2 < 4U)
            {
            }
            else
            {

#line 585
                break;
            }

#line 585
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 4U + j_2], kernelContext_2);

#line 585
            j_2 = j_2 + 1U;

#line 585
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 586
        uint d_2 = 0U;
        for(;;)
        {

#line 587
            if(d_2 < 32U)
            {
            }
            else
            {

#line 587
                break;
            }

#line 588
            uint p_0 = computeWant_0(d_2, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
            uint b_2 = p_0 >> lgLen_0;

#line 589
            uint rem_0 = p_0 & _S13;
            uint i_2 = rem_0 >> lgSpan_0;

#line 590
            uint ln_0 = rem_0 & _S12;
            uint _S14 = c_1 * 4U;

#line 591
            bool _S15;

#line 591
            if(i_2 >= _S14)
            {

#line 591
                _S15 = i_2 < ((c_1 + 1U) * 4U);

#line 591
            }
            else
            {

#line 591
                _S15 = false;

#line 591
            }

#line 591
            if(_S15)
            {

#line 591
                float2 _S16 = stgGet_0((i_2 - _S14) * 1024U + (b_2 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_2] = _S16;

#line 591
            }

#line 587
            d_2 = d_2 + 1U;

#line 587
        }

#line 583
        c_1 = c_1 + 1U;

#line 583
    }

#line 583
    j_2 = 0U;

#line 595
    for(;;)
    {

#line 595
        if(j_2 < 32U)
        {
        }
        else
        {

#line 595
            break;
        }

#line 595
        (*r_3)[j_2] = out_0[j_2];

#line 595
        j_2 = j_2 + 1U;

#line 595
    }
    return;
}


#line 510
void innermost_0(array<float2, int(32)> thread* r_4)
{

    dft32_0(r_4);

#line 522
    return;
}


#line 1552
void forwardTransform_0(array<float2, int(32)> thread* r_5, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 1552
    uint _S17;

#line 1552
    uint k2_1;

#line 1552
    float cr_0;

#line 1552
    float ci_0;

#line 1552
    uint _S18;

#line 1552
    for(;;)
    {

#line 1552
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S17 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(32768U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;

#line 19
                dftR_0(r_5);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 32768.0);
                float _S19 = tw_0.x;

#line 27
                float _S20 = tw_0.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_1 < 32U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_5)[k2_1] = cmul_0((*r_5)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S19 - ci_0 * _S20;
                    float _S21 = cr_0 * _S20 + ci_0 * _S19;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S21;

#line 29
                }

#line 37
                uint per_2 = 32U / max(1024U, 1U);
                uint _S22 = max(32U, 1U);

#line 38
                _S18 = _S22;
                uint blk2_2 = tid_0 / _S22;

#line 39
                uint lane2_2 = tid_0 % _S22;

#line 39
                exchange_0(r_5, lgLn_0, lgTB_0, 1024U, 32768U, blk_2, lane_2, per_2, _S22, 1024U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(32U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 31U;

#line 19
                dftR_0(r_5);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 1024.0);
                float _S23 = tw_1.x;

#line 27
                float _S24 = tw_1.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_1 < 32U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_5)[k2_1] = cmul_0((*r_5)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S23 - ci_0 * _S24;
                    float _S25 = cr_0 * _S24 + ci_0 * _S23;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S25;

#line 29
                }

#line 37
                uint per_3 = 32U / _S18;
                uint _S26 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S26;

#line 39
                uint lane2_3 = tid_0 % _S26;

#line 39
                exchange_0(r_5, _S17, lgTB_1, 32U, 1024U, blk_3, lane_3, per_3, _S26, 32U, blk2_3, lane2_3, kernelContext_3);

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
    innermost_0(r_5);

#line 1555 "/tmp/tmpkxwd5_fn/forward.slang"
    return;
}


#line 620
uint lgOf_0(uint i_3)
{

#line 620
    uint _S27;

#line 620
    if(i_3 < 2U)
    {

#line 620
        _S27 = 5U;

#line 620
    }
    else
    {

#line 620
        if(i_3 == 2U)
        {

#line 620
            _S27 = 5U;

#line 620
        }
        else
        {

#line 620
            _S27 = 1U;

#line 620
        }

#line 620
    }

#line 620
    return _S27;
}


#line 622
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 626
    uint lg_1 = lgOf_0(1U);

#line 626
    uint lg_2 = lgOf_0(0U);

#line 631
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1560
[[kernel]] void seriesForward(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]])
{

#line 1560
    thread KernelContext_0 kernelContext_4;

#line 1560
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1560
    (&kernelContext_4)->entryPointParams_series_0 = entryPointParams_series_1;

#line 1560
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1560
    (&kernelContext_4)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 1560
    threadgroup array<uint, int(8192)> stg_1;

#line 1560
    (&kernelContext_4)->stg_0 = &stg_1;

#line 1566
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    uint _S28 = gid_0.x;

#line 1569
    uint _S29 = entryPointParams_starts_1[_S28];
    thread array<float2, int(32)> r_6;

#line 1570
    uint k_1 = 0U;
    for(;;)
    {

#line 1571
        if(k_1 < 32U)
        {
        }
        else
        {

#line 1571
            break;
        }

#line 1572
        uint offset_0 = tid_1 + 1024U * k_1;
        float2 _S30 = float2(0.0, 0.0);

#line 1573
        bool _S31;

        if(_S29 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0))
        {

#line 1575
            _S31 = offset_0 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0 - _S29);

#line 1575
        }
        else
        {

#line 1575
            _S31 = false;

#line 1575
        }

#line 1575
        float2 x_1;

#line 1575
        if(_S31)
        {

#line 1575
            x_1 = float2(*((&kernelContext_4)->entryPointParams_series_0+(_S29 + offset_0))) ;

#line 1575
        }
        else
        {

#line 1575
            x_1 = _S30;

#line 1575
        }

        r_6[k_1] = float2(x_1.x / 32768.0, - x_1.y / 32768.0);

#line 1571
        k_1 = k_1 + 1U;

#line 1571
    }

#line 1571
    forwardTransform_0(&r_6, tid_1, &kernelContext_4);

#line 1571
    k_1 = 0U;

#line 1580
    for(;;)
    {

#line 1580
        if(k_1 < 32U)
        {
        }
        else
        {

#line 1580
            break;
        }

#line 1580
        *((&kernelContext_4)->entryPointParams_spectra_0+(_S28 * 32768U + slotToIndex_0(tid_1 * 32U + k_1))) = packed_float2(float2(r_6[k_1].x, - r_6[k_1].y)) ;

#line 1580
        k_1 = k_1 + 1U;

#line 1580
    }



    return;
}
