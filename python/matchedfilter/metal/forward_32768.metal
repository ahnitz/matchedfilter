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


#line 12 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 187 "/tmp/tmpyjalno9v/forward.slang"
float2 cmul_0(float2 a_0, float2 b_0)
{

#line 187
    float _S2 = a_0.x;

#line 187
    float _S3 = b_0.x;

#line 187
    float _S4 = a_0.y;

#line 187
    float _S5 = b_0.y;

#line 187
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 345
void r4_0(float2 thread* a_1, float2 thread* b_1, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 347
    float2 t1_0 = *a_1 - *c_0;

#line 347
    float2 t2_0 = *b_1 + *d_0;

#line 347
    float2 t3_0 = *b_1 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 349
    *b_1 = t1_0 + j3_0;

#line 349
    *c_0 = t0_0 - t2_0;

#line 349
    *d_0 = t1_0 - j3_0;
    return;
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


#line 427
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 429
    thread array<float2, int(16)> v_0;

#line 429
    uint j_0 = 0U;
    for(;;)
    {

#line 430
        if(j_0 < 16U)
        {
        }
        else
        {

#line 430
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        v_0[j_0] = cmul_0((*r_1)[j_0] - (*r_1)[j_0 + 16U], mfTwiddle_0(6.28318548202514648 * float(j_0) / 32.0));

#line 430
        j_0 = j_0 + 1U;

#line 430
    }

#line 436
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 437
    uint k_0 = 0U;
    for(;;)
    {

#line 438
        if(k_0 < 16U)
        {
        }
        else
        {

#line 438
            break;
        }

#line 438
        uint _S7 = 2U * k_0;

#line 438
        (*r_1)[_S7] = u_0[k_0];

#line 438
        (*r_1)[_S7 + 1U] = v_0[k_0];

#line 438
        k_0 = k_0 + 1U;

#line 438
    }
    return;
}


#line 466
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


#line 176 "/tmp/tmpyjalno9v/forward.slang"
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


#line 176
void stgPut_0(uint i_0, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 176
    uint _S8 = 2U * i_0;

#line 176
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S8] = (as_type<uint>((v_1.x)));

#line 176
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S8 + 1U] = (as_type<uint>((v_1.y)));

#line 176
    return;
}


#line 189
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S9 = max(TB_0, 1U);

#line 191
    uint j_1 = d_1 / _S9;

#line 191
    uint m_0 = d_1 % _S9;

#line 191
    uint _S10;
    if(TB_0 <= 32U)
    {

#line 192
        _S10 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 192
    }
    else
    {

#line 192
        _S10 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 192
    }

#line 192
    return _S10;
}


#line 177
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 177
    uint _S11 = 2U * i_1;

#line 177
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S11]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S11 + 1U]))));
}


#line 506
void exchange_0(array<float2, int(32)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 507
    uint j_2;

#line 518
    thread array<float2, int(32)> out_0;

#line 518
    uint z_0 = 0U;
    for(;;)
    {

#line 519
        if(z_0 < 32U)
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
    uint _S12 = (1U << lgSpan_0) - 1U;
    uint _S13 = (1U << lgLen_0) - 1U;

#line 521
    uint c_1 = 0U;
    for(;;)
    {

#line 522
        if(c_1 < 8U)
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
        j_2 = 0U;
        for(;;)
        {

#line 524
            if(j_2 < 4U)
            {
            }
            else
            {

#line 524
                break;
            }

#line 524
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 4U + j_2], kernelContext_2);

#line 524
            j_2 = j_2 + 1U;

#line 524
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 525
        uint d_2 = 0U;
        for(;;)
        {

#line 526
            if(d_2 < 32U)
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
            uint rem_0 = p_0 & _S13;
            uint i_2 = rem_0 >> lgSpan_0;

#line 529
            uint ln_0 = rem_0 & _S12;
            uint _S14 = c_1 * 4U;

#line 530
            bool _S15;

#line 530
            if(i_2 >= _S14)
            {

#line 530
                _S15 = i_2 < ((c_1 + 1U) * 4U);

#line 530
            }
            else
            {

#line 530
                _S15 = false;

#line 530
            }

#line 530
            if(_S15)
            {

#line 530
                float2 _S16 = stgGet_0((i_2 - _S14) * 1024U + (b_2 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_2] = _S16;

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
    j_2 = 0U;

#line 534
    for(;;)
    {

#line 534
        if(j_2 < 32U)
        {
        }
        else
        {

#line 534
            break;
        }

#line 534
        (*r_3)[j_2] = out_0[j_2];

#line 534
        j_2 = j_2 + 1U;

#line 534
    }
    return;
}


#line 484
void innermost_0(array<float2, int(32)> thread* r_4)
{

    dft32_0(r_4);

#line 496
    return;
}


#line 1292
void forwardTransform_0(array<float2, int(32)> thread* r_5, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 1292
    uint _S17;

#line 1292
    uint k2_1;

#line 1292
    float cr_0;

#line 1292
    float ci_0;

#line 1292
    uint _S18;

#line 1292
    for(;;)
    {

#line 1292
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/src/gpu/fft_transform.slang"
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

#line 1295 "/tmp/tmpyjalno9v/forward.slang"
    return;
}


#line 558
uint lgOf_0(uint i_3)
{

#line 558
    uint _S27;

#line 558
    if(i_3 < 2U)
    {

#line 558
        _S27 = 5U;

#line 558
    }
    else
    {

#line 558
        if(i_3 == 2U)
        {

#line 558
            _S27 = 5U;

#line 558
        }
        else
        {

#line 558
            _S27 = 1U;

#line 558
        }

#line 558
    }

#line 558
    return _S27;
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


#line 1300
[[kernel]] void seriesForward(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]])
{

#line 1300
    thread KernelContext_0 kernelContext_4;

#line 1300
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1300
    (&kernelContext_4)->entryPointParams_series_0 = entryPointParams_series_1;

#line 1300
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1300
    (&kernelContext_4)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 1300
    threadgroup array<uint, int(8192)> stg_1;

#line 1300
    (&kernelContext_4)->stg_0 = &stg_1;

#line 1306
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    uint _S28 = gid_0.x;

#line 1309
    uint _S29 = entryPointParams_starts_1[_S28];
    thread array<float2, int(32)> r_6;

#line 1310
    uint k_1 = 0U;
    for(;;)
    {

#line 1311
        if(k_1 < 32U)
        {
        }
        else
        {

#line 1311
            break;
        }

#line 1312
        uint offset_0 = tid_1 + 1024U * k_1;
        float2 _S30 = float2(0.0, 0.0);

#line 1313
        bool _S31;

        if(_S29 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0))
        {

#line 1315
            _S31 = offset_0 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0 - _S29);

#line 1315
        }
        else
        {

#line 1315
            _S31 = false;

#line 1315
        }

#line 1315
        float2 x_1;

#line 1315
        if(_S31)
        {

#line 1315
            x_1 = float2(*((&kernelContext_4)->entryPointParams_series_0+(_S29 + offset_0))) ;

#line 1315
        }
        else
        {

#line 1315
            x_1 = _S30;

#line 1315
        }

        r_6[k_1] = float2(x_1.x / 32768.0, - x_1.y / 32768.0);

#line 1311
        k_1 = k_1 + 1U;

#line 1311
    }

#line 1311
    forwardTransform_0(&r_6, tid_1, &kernelContext_4);

#line 1311
    k_1 = 0U;

#line 1320
    for(;;)
    {

#line 1320
        if(k_1 < 32U)
        {
        }
        else
        {

#line 1320
            break;
        }

#line 1320
        *((&kernelContext_4)->entryPointParams_spectra_0+(_S28 * 32768U + slotToIndex_0(tid_1 * 32U + k_1))) = packed_float2(float2(r_6[k_1].x, - r_6[k_1].y)) ;

#line 1320
        k_1 = k_1 + 1U;

#line 1320
    }



    return;
}
