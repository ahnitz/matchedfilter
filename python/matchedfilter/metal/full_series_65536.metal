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


#line 151 "mm_65536_fullCorrelationSeries.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 151
    return float2(*(b_0+i_0)) ;
}


#line 191
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 191
    float _S2 = a_0.x;

#line 191
    float _S3 = b_1.x;

#line 191
    float _S4 = a_0.y;

#line 191
    float _S5 = b_1.y;

#line 191
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 341
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 343
    float2 t1_0 = *a_1 - *c_0;

#line 343
    float2 t2_0 = *b_2 + *d_0;

#line 343
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 345
    *b_2 = t1_0 + j3_0;

#line 345
    *c_0 = t0_0 - t2_0;

#line 345
    *d_0 = t1_0 - j3_0;
    return;
}


#line 10 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 190 "mm_65536_fullCorrelationSeries.slang"
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 190
    float _S6 = a_2.x;

#line 190
    float _S7 = b_3.x;

#line 190
    float _S8 = a_2.y;

#line 190
    float _S9 = b_3.y;

#line 190
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 377
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 384
    uint n1_0 = 0U;
    for(;;)
    {

#line 385
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 385
            break;
        }

#line 385
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 385
        n1_0 = n1_0 + 1U;

#line 385
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 386
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 386
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 387
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 387
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 388
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 388
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 388
    uint k2_0 = 0U;
    for(;;)
    {

#line 389
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 389
            break;
        }

#line 389
        uint _S10 = 4U * k2_0;

#line 389
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 389
        k2_0 = k2_0 + 1U;

#line 389
    }

    float2 t_0 = (*r_0)[int(1)];

#line 391
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 391
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 392
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 392
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 393
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 393
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 394
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 394
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 395
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 395
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 396
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 396
    (*r_0)[int(14)] = t_5;
    return;
}


#line 443
void dft64_0(array<float2, int(64)> thread* r_1)
{

#line 443
    uint k_0;

#line 443
    uint j_0 = 0U;

    for(;;)
    {

#line 445
        if(j_0 < 16U)
        {
        }
        else
        {

#line 445
            break;
        }

#line 446
        r4_0(&(*r_1)[j_0], &(*r_1)[j_0 + 16U], &(*r_1)[j_0 + 32U], &(*r_1)[j_0 + 48U]);

#line 445
        j_0 = j_0 + 1U;

#line 445
    }

    thread array<float2, int(64)> o_0;

#line 447
    uint pp_0 = 0U;
    for(;;)
    {

#line 448
        if(pp_0 < 4U)
        {
        }
        else
        {

#line 448
            break;
        }

#line 449
        thread array<float2, int(16)> b_4;

#line 449
        j_0 = 0U;
        for(;;)
        {

#line 450
            if(j_0 < 16U)
            {
            }
            else
            {

#line 450
                break;
            }
            b_4[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f));

#line 450
            j_0 = j_0 + 1U;

#line 450
        }



        dft16_0(&b_4);

#line 454
        k_0 = 0U;
        for(;;)
        {

#line 455
            if(k_0 < 16U)
            {
            }
            else
            {

#line 455
                break;
            }

#line 455
            o_0[4U * k_0 + pp_0] = b_4[k_0];

#line 455
            k_0 = k_0 + 1U;

#line 455
        }

#line 448
        pp_0 = pp_0 + 1U;

#line 448
    }

#line 448
    k_0 = 0U;

#line 457
    for(;;)
    {

#line 457
        if(k_0 < 64U)
        {
        }
        else
        {

#line 457
            break;
        }

#line 457
        (*r_1)[k_0] = o_0[k_0];

#line 457
        k_0 = k_0 + 1U;

#line 457
    }
    return;
}


void dftR_0(array<float2, int(64)> thread* r_2)
{

#line 469
    dft64_0(r_2);

    return;
}


#line 1005
struct EntryPointParams_0
{
    uint4 params_0;
};


#line 179
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(16384)> threadgroup* stg_0;
};


#line 179
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 179
    uint _S11 = 2U * i_1;

#line 179
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11] = (as_type<uint>((v_0.x)));

#line 179
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11 + 1U] = (as_type<uint>((v_0.y)));

#line 179
    return;
}


#line 180
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 180
    uint _S12 = 2U * i_2;

#line 180
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12 + 1U]))));
}


#line 502
void exchange_0(array<float2, int(64)> thread* r_3, const array<uint, int(64)> thread* want_0, uint lgLen_0, uint lgSpan_0, KernelContext_0 thread* kernelContext_2)
{

#line 502
    uint j_1;

#line 513
    thread array<float2, int(64)> out_0;

#line 513
    uint z_0 = 0U;
    for(;;)
    {

#line 514
        if(z_0 < 64U)
        {
        }
        else
        {

#line 514
            break;
        }

#line 514
        out_0[z_0] = float2(0.0f, 0.0f);

#line 514
        z_0 = z_0 + 1U;

#line 514
    }
    uint _S13 = (1U << lgSpan_0) - 1U;
    uint _S14 = (1U << lgLen_0) - 1U;

#line 516
    uint c_1 = 0U;
    for(;;)
    {

#line 517
        if(c_1 < 8U)
        {
        }
        else
        {

#line 517
            break;
        }

#line 518
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 518
        j_1 = 0U;
        for(;;)
        {

#line 519
            if(j_1 < 8U)
            {
            }
            else
            {

#line 519
                break;
            }

#line 519
            stgPut_0(j_1 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 8U + j_1], kernelContext_2);

#line 519
            j_1 = j_1 + 1U;

#line 519
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 520
        uint d_1 = 0U;
        for(;;)
        {

#line 521
            if(d_1 < 64U)
            {
            }
            else
            {

#line 521
                break;
            }
            uint b_5 = ((*want_0)[d_1]) >> lgLen_0;

#line 523
            uint rem_0 = ((*want_0)[d_1]) & _S14;
            uint i_3 = rem_0 >> lgSpan_0;

#line 524
            uint ln_0 = rem_0 & _S13;
            uint _S15 = c_1 * 8U;

#line 525
            bool _S16;

#line 525
            if(i_3 >= _S15)
            {

#line 525
                _S16 = i_3 < ((c_1 + 1U) * 8U);

#line 525
            }
            else
            {

#line 525
                _S16 = false;

#line 525
            }

#line 525
            if(_S16)
            {

#line 525
                float2 _S17 = stgGet_0((i_3 - _S15) * 1024U + (b_5 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_1] = _S17;

#line 525
            }

#line 521
            d_1 = d_1 + 1U;

#line 521
        }

#line 517
        c_1 = c_1 + 1U;

#line 517
    }

#line 517
    j_1 = 0U;

#line 529
    for(;;)
    {

#line 529
        if(j_1 < 64U)
        {
        }
        else
        {

#line 529
            break;
        }

#line 529
        (*r_3)[j_1] = out_0[j_1];

#line 529
        j_1 = j_1 + 1U;

#line 529
    }
    return;
}


#line 402
void dft16at_0(array<float2, int(64)> thread* r_4, uint o_1)
{



    thread array<float2, int(16)> b_6;

#line 407
    uint i_4 = 0U;
    for(;;)
    {

#line 408
        if(i_4 < 16U)
        {
        }
        else
        {

#line 408
            break;
        }

#line 408
        b_6[i_4] = (*r_4)[o_1 + i_4];

#line 408
        i_4 = i_4 + 1U;

#line 408
    }
    dft16_0(&b_6);

#line 409
    i_4 = 0U;
    for(;;)
    {

#line 410
        if(i_4 < 16U)
        {
        }
        else
        {

#line 410
            break;
        }

#line 410
        (*r_4)[o_1 + i_4] = b_6[i_4];

#line 410
        i_4 = i_4 + 1U;

#line 410
    }

    return;
}


#line 480
void innermost_0(array<float2, int(64)> thread* r_5)
{

#line 480
    uint b_7 = 0U;

#line 485
    for(;;)
    {

#line 485
        if(b_7 < 4U)
        {
        }
        else
        {

#line 485
            break;
        }

#line 485
        dft16at_0(r_5, b_7 * 16U);

#line 485
        b_7 = b_7 + 1U;

#line 485
    }

#line 492
    return;
}


#line 584
void transform_0(array<float2, int(64)> thread* r_6, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 584
    uint z_1;

#line 584
    uint _S18;

#line 584
    uint k2_1;

#line 584
    float cr_0;

#line 584
    float ci_0;

#line 584
    uint _S19;

#line 584
    uint d_2;

#line 584
    for(;;)
    {

#line 584
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {

#line 8
                thread array<uint, int(64)> want_1;

#line 8
                z_1 = 0U;
                for(;;)
                {

#line 9
                    if(z_1 < 64U)
                    {
                    }
                    else
                    {

#line 9
                        break;
                    }

#line 9
                    want_1[z_1] = 0U;

#line 9
                    z_1 = z_1 + 1U;

#line 9
                }



                uint lgTB_0 = firstbithigh_0(1024U);

#line 13
                _S18 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(65536U);

                uint lane_0 = tid_0 & 1023U;

#line 21
                dftR_0(r_6);

#line 28
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_0) / 6.5536e+04f);
                float _S20 = tw_0.x;

#line 29
                float _S21 = tw_0.y;

#line 29
                k2_1 = 0U;

#line 29
                cr_0 = 1.0f;

#line 29
                ci_0 = 0.0f;

                for(;;)
                {

#line 31
                    if(k2_1 < 64U)
                    {
                    }
                    else
                    {

#line 31
                        break;
                    }

#line 32
                    (*r_6)[k2_1] = cmul_0((*r_6)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S20 - ci_0 * _S21;
                    float _S22 = cr_0 * _S21 + ci_0 * _S20;

#line 31
                    k2_1 = k2_1 + 1U;

#line 31
                    cr_0 = nr_0;

#line 31
                    ci_0 = _S22;

#line 31
                }

#line 41
                uint _S23 = max(1024U, 1U);

#line 41
                uint _S24 = 64U / _S23;
                uint _S25 = max(16U, 1U);

#line 42
                _S19 = _S25;
                uint _S26 = tid_0 / _S25;

#line 43
                uint _S27 = tid_0 % _S25;

#line 43
                d_2 = 0U;
                for(;;)
                {

#line 44
                    if(d_2 < 64U)
                    {
                    }
                    else
                    {

#line 44
                        break;
                    }

#line 45
                    uint j_2 = d_2 / _S23;

#line 45
                    uint m_0 = d_2 % _S23;
                    want_1[d_2] = _S26 * 1024U + _S27 + _S25 * d_2;

#line 44
                    d_2 = d_2 + 1U;

#line 44
                }

#line 44
                thread array<uint, int(64)> _S28 = want_1;

#line 44
                exchange_0(r_6, &_S28, lgLn_0, lgTB_0, kernelContext_3);

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

#line 8
                thread array<uint, int(64)> want_2;

#line 8
                z_1 = 0U;
                for(;;)
                {

#line 9
                    if(z_1 < 64U)
                    {
                    }
                    else
                    {

#line 9
                        break;
                    }

#line 9
                    want_2[z_1] = 0U;

#line 9
                    z_1 = z_1 + 1U;

#line 9
                }



                uint lgTB_1 = firstbithigh_0(16U);

                uint _S29 = tid_0 >> lgTB_1;
                uint lane_1 = tid_0 & 15U;

#line 21
                dftR_0(r_6);

#line 28
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 1024.0f);
                float _S30 = tw_1.x;

#line 29
                float _S31 = tw_1.y;

#line 29
                k2_1 = 0U;

#line 29
                cr_0 = 1.0f;

#line 29
                ci_0 = 0.0f;

                for(;;)
                {

#line 31
                    if(k2_1 < 64U)
                    {
                    }
                    else
                    {

#line 31
                        break;
                    }

#line 32
                    (*r_6)[k2_1] = cmul_0((*r_6)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S30 - ci_0 * _S31;
                    float _S32 = cr_0 * _S31 + ci_0 * _S30;

#line 31
                    k2_1 = k2_1 + 1U;

#line 31
                    cr_0 = nr_1;

#line 31
                    ci_0 = _S32;

#line 31
                }

#line 41
                uint _S33 = 64U / _S19;
                uint _S34 = max(0U, 1U);
                uint _S35 = tid_0 / _S34;

#line 43
                uint _S36 = tid_0 % _S34;

#line 43
                d_2 = 0U;
                for(;;)
                {

#line 44
                    if(d_2 < 64U)
                    {
                    }
                    else
                    {

#line 44
                        break;
                    }

#line 45
                    uint j_3 = d_2 / _S19;

#line 45
                    uint m_1 = d_2 % _S19;
                    want_2[d_2] = _S29 * 1024U + (lane_1 * _S33 + j_3) * 16U + m_1;

#line 44
                    d_2 = d_2 + 1U;

#line 44
                }

#line 44
                thread array<uint, int(64)> _S37 = want_2;

#line 44
                exchange_0(r_6, &_S37, _S18, lgTB_1, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        break;
    }

#line 52
    innermost_0(r_6);

#line 587 "mm_65536_fullCorrelationSeries.slang"
    return;
}


#line 553
uint lgOf_0(uint i_5)
{

#line 553
    uint _S38;

#line 553
    if(i_5 < 2U)
    {

#line 553
        _S38 = 6U;

#line 553
    }
    else
    {

#line 553
        if(i_5 == 2U)
        {

#line 553
            _S38 = 4U;

#line 553
        }
        else
        {

#line 553
            _S38 = 1U;

#line 553
        }

#line 553
    }

#line 553
    return _S38;
}


#line 555
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 559
    uint lg_1 = lgOf_0(1U);

#line 559
    uint lg_2 = lgOf_0(0U);

#line 564
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1005
[[kernel]] void fullCorrelationSeries(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], uint device* entryPointParams_starts_1 [[buffer(3)]], packed_float2 device* entryPointParams_output_1 [[buffer(4)]])
{

#line 1005
    thread KernelContext_0 kernelContext_4;

#line 1005
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1005
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1005
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1005
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1005
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1005
    threadgroup array<uint, int(16384)> stg_1;

#line 1005
    (&kernelContext_4)->stg_0 = &stg_1;

#line 1010
    uint pair_0 = gid_0.x;

#line 1010
    uint tid_1 = lid_0.x;
    uint d_3 = pair_0 / entryPointParams_1->params_0.x;

#line 1011
    uint _S39 = pair_0 % entryPointParams_1->params_0.x;
    uint _S40 = (&kernelContext_4)->entryPointParams_starts_0[d_3];
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(64)> r_7;

#line 1015
    uint i_6 = 0U;
    for(;;)
    {

#line 1016
        if(i_6 < 64U)
        {
        }
        else
        {

#line 1016
            break;
        }

#line 1017
        uint idx_0 = tid_1 + 1024U * i_6;
        r_7[i_6] = cmulConj_0(cload_0((&kernelContext_4)->entryPointParams_data_0, d_3 * 65536U + idx_0), cload_0((&kernelContext_4)->entryPointParams_tmpl_0, _S39 * 65536U + idx_0));

#line 1016
        i_6 = i_6 + 1U;

#line 1016
    }

#line 1016
    transform_0(&r_7, tid_1, &kernelContext_4);

#line 1016
    i_6 = 0U;

#line 1021
    for(;;)
    {

#line 1021
        if(i_6 < 64U)
        {
        }
        else
        {

#line 1021
            break;
        }

#line 1022
        uint lag_0 = slotToIndex_0(tid_1 * 64U + i_6);

#line 1022
        bool _S41;
        if(lag_0 >= (entryPointParams_1->params_0.z))
        {

#line 1023
            _S41 = lag_0 < (entryPointParams_1->params_0.w);

#line 1023
        }
        else
        {

#line 1023
            _S41 = false;

#line 1023
        }

#line 1023
        bool _S42;

#line 1023
        if(_S41)
        {

#line 1023
            _S42 = lag_0 < (entryPointParams_1->params_0.y - _S40);

#line 1023
        }
        else
        {

#line 1023
            _S42 = false;

#line 1023
        }

#line 1023
        if(_S42)
        {

#line 1023
            *((&kernelContext_4)->entryPointParams_output_0+(_S39 * entryPointParams_1->params_0.y + _S40 + lag_0)) = packed_float2(float2(r_7[i_6].x, r_7[i_6].y)) ;

#line 1023
        }

#line 1021
        i_6 = i_6 + 1U;

#line 1021
    }

#line 1026
    return;
}
