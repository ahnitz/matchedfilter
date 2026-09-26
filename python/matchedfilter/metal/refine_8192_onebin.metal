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


#line 150 "mm_8192_refineListed_onebin.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 150
    return float2(*(b_0+i_0)) ;
}


#line 190
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 190
    float _S2 = a_0.x;

#line 190
    float _S3 = b_1.x;

#line 190
    float _S4 = a_0.y;

#line 190
    float _S5 = b_1.y;

#line 190
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 339
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 341
    float2 t1_0 = *a_1 - *c_0;

#line 341
    float2 t2_0 = *b_2 + *d_0;

#line 341
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 343
    *b_2 = t1_0 + j3_0;

#line 343
    *c_0 = t0_0 - t2_0;

#line 343
    *d_0 = t1_0 - j3_0;
    return;
}


#line 189
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 189
    float _S6 = a_2.x;

#line 189
    float _S7 = b_3.x;

#line 189
    float _S8 = a_2.y;

#line 189
    float _S9 = b_3.y;

#line 189
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 375
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 382
    uint n1_0 = 0U;
    for(;;)
    {

#line 383
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 383
            break;
        }

#line 383
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 383
        n1_0 = n1_0 + 1U;

#line 383
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 384
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 384
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 385
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 385
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 386
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 386
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 386
    uint k2_0 = 0U;
    for(;;)
    {

#line 387
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 387
            break;
        }

#line 387
        uint _S10 = 4U * k2_0;

#line 387
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 387
        k2_0 = k2_0 + 1U;

#line 387
    }

    float2 t_0 = (*r_0)[int(1)];

#line 389
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 389
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 390
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 390
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 391
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 391
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 392
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 392
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 393
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 393
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 394
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 394
    (*r_0)[int(14)] = t_5;
    return;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
    uint winStart_0;
    uint winEnd_0;
    uint binsize_0;
    int binShift_0;
    uint nbins_0;
    uint thrBits_0;
};


#line 178 "mm_8192_refineListed_onebin.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_survivors_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 178
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 178
    uint _S11 = 2U * i_1;

#line 178
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11] = (as_type<uint>((v_0.x)));

#line 178
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11 + 1U] = (as_type<uint>((v_0.y)));

#line 178
    return;
}


#line 179
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 179
    uint _S12 = 2U * i_2;

#line 179
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12 + 1U]))));
}


#line 500
void exchange_0(array<float2, int(16)> thread* r_1, const array<uint, int(16)> thread* want_0, uint lgLen_0, uint lgSpan_0, KernelContext_0 thread* kernelContext_2)
{

#line 500
    uint j_0;

#line 511
    thread array<float2, int(16)> out_0;

#line 511
    uint z_0 = 0U;
    for(;;)
    {

#line 512
        if(z_0 < 16U)
        {
        }
        else
        {

#line 512
            break;
        }

#line 512
        out_0[z_0] = float2(0.0f, 0.0f);

#line 512
        z_0 = z_0 + 1U;

#line 512
    }
    uint _S13 = (1U << lgSpan_0) - 1U;
    uint _S14 = (1U << lgLen_0) - 1U;

#line 514
    uint c_1 = 0U;
    for(;;)
    {

#line 515
        if(c_1 < 2U)
        {
        }
        else
        {

#line 515
            break;
        }

#line 516
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 516
        j_0 = 0U;
        for(;;)
        {

#line 517
            if(j_0 < 8U)
            {
            }
            else
            {

#line 517
                break;
            }

#line 517
            stgPut_0(j_0 * 512U + kernelContext_2->_tid_0, (*r_1)[c_1 * 8U + j_0], kernelContext_2);

#line 517
            j_0 = j_0 + 1U;

#line 517
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 518
        uint d_1 = 0U;
        for(;;)
        {

#line 519
            if(d_1 < 16U)
            {
            }
            else
            {

#line 519
                break;
            }
            uint b_4 = ((*want_0)[d_1]) >> lgLen_0;

#line 521
            uint rem_0 = ((*want_0)[d_1]) & _S14;
            uint i_3 = rem_0 >> lgSpan_0;

#line 522
            uint ln_0 = rem_0 & _S13;
            uint _S15 = c_1 * 8U;

#line 523
            bool _S16;

#line 523
            if(i_3 >= _S15)
            {

#line 523
                _S16 = i_3 < ((c_1 + 1U) * 8U);

#line 523
            }
            else
            {

#line 523
                _S16 = false;

#line 523
            }

#line 523
            if(_S16)
            {

#line 523
                float2 _S17 = stgGet_0((i_3 - _S15) * 512U + (b_4 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_1] = _S17;

#line 523
            }

#line 519
            d_1 = d_1 + 1U;

#line 519
        }

#line 515
        c_1 = c_1 + 1U;

#line 515
    }

#line 515
    j_0 = 0U;

#line 527
    for(;;)
    {

#line 527
        if(j_0 < 16U)
        {
        }
        else
        {

#line 527
            break;
        }

#line 527
        (*r_1)[j_0] = out_0[j_0];

#line 527
        j_0 = j_0 + 1U;

#line 527
    }
    return;
}


#line 350
void dft2_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    float2 a_3 = (*r_2)[o_0];

#line 352
    float2 b_5 = (*r_2)[o_0 + 1U];

#line 352
    (*r_2)[o_0] = (*r_2)[o_0] + (*r_2)[o_0 + 1U];

#line 352
    (*r_2)[o_0 + 1U] = a_3 - b_5;
    return;
}


#line 478
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 478
    uint b_6 = 0U;

#line 488
    for(;;)
    {

#line 488
        if(b_6 < 8U)
        {
        }
        else
        {

#line 488
            break;
        }

#line 488
        dft2_0(r_3, b_6 * 2U);

#line 488
        b_6 = b_6 + 1U;

#line 488
    }

    return;
}


#line 582
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 582
    uint z_1;

#line 582
    uint _S18;

#line 582
    uint k2_1;

#line 582
    float cr_0;

#line 582
    float ci_0;

#line 582
    uint _S19;

#line 582
    uint d_2;

#line 582
    uint _S20;

#line 582
    uint _S21;

#line 582
    for(;;)
    {

#line 582
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {

#line 8
                thread array<uint, int(16)> want_1;

#line 8
                z_1 = 0U;
                for(;;)
                {

#line 9
                    if(z_1 < 16U)
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



                uint lgTB_0 = firstbithigh_0(512U);

#line 13
                _S18 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(8192U);

                uint lane_0 = tid_0 & 511U;


                dft16_0(r_4);

#line 27
                float a1_0 = 6.28318548202514648f * float(lane_0) / 8192.0f;
                float _S22 = cos(a1_0);

#line 28
                float _S23 = sin(a1_0);

#line 28
                k2_1 = 0U;

#line 28
                cr_0 = 1.0f;

#line 28
                ci_0 = 0.0f;

                for(;;)
                {

#line 30
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 30
                        break;
                    }

#line 31
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S22 - ci_0 * _S23;
                    float _S24 = cr_0 * _S23 + ci_0 * _S22;

#line 30
                    k2_1 = k2_1 + 1U;

#line 30
                    cr_0 = nr_0;

#line 30
                    ci_0 = _S24;

#line 30
                }

#line 40
                uint _S25 = max(512U, 1U);

#line 40
                uint _S26 = 16U / _S25;
                uint _S27 = max(32U, 1U);

#line 41
                _S19 = _S27;
                uint _S28 = tid_0 / _S27;

#line 42
                uint _S29 = tid_0 % _S27;

#line 42
                d_2 = 0U;
                for(;;)
                {

#line 43
                    if(d_2 < 16U)
                    {
                    }
                    else
                    {

#line 43
                        break;
                    }

#line 44
                    uint j_1 = d_2 / _S25;

#line 44
                    uint m_0 = d_2 % _S25;
                    want_1[d_2] = _S28 * 512U + _S29 + _S27 * d_2;

#line 43
                    d_2 = d_2 + 1U;

#line 43
                }

#line 43
                thread array<uint, int(16)> _S30 = want_1;

#line 43
                exchange_0(r_4, &_S30, lgLn_0, lgTB_0, kernelContext_3);

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
                thread array<uint, int(16)> want_2;

#line 8
                z_1 = 0U;
                for(;;)
                {

#line 9
                    if(z_1 < 16U)
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



                uint lgTB_1 = firstbithigh_0(32U);

#line 13
                _S20 = lgTB_1;


                uint lane_1 = tid_0 & 31U;


                dft16_0(r_4);

#line 27
                float a1_1 = 6.28318548202514648f * float(lane_1) / 512.0f;
                float _S31 = cos(a1_1);

#line 28
                float _S32 = sin(a1_1);

#line 28
                k2_1 = 0U;

#line 28
                cr_0 = 1.0f;

#line 28
                ci_0 = 0.0f;

                for(;;)
                {

#line 30
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 30
                        break;
                    }

#line 31
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S31 - ci_0 * _S32;
                    float _S33 = cr_0 * _S32 + ci_0 * _S31;

#line 30
                    k2_1 = k2_1 + 1U;

#line 30
                    cr_0 = nr_1;

#line 30
                    ci_0 = _S33;

#line 30
                }

#line 40
                uint _S34 = 16U / _S19;
                uint _S35 = max(2U, 1U);

#line 41
                _S21 = _S35;
                uint _S36 = tid_0 / _S35;

#line 42
                uint _S37 = tid_0 % _S35;

#line 42
                d_2 = 0U;
                for(;;)
                {

#line 43
                    if(d_2 < 16U)
                    {
                    }
                    else
                    {

#line 43
                        break;
                    }

#line 44
                    uint j_2 = d_2 / _S19;

#line 44
                    uint m_1 = d_2 % _S19;
                    want_2[d_2] = _S36 * 32U + _S37 + _S35 * d_2;

#line 43
                    d_2 = d_2 + 1U;

#line 43
                }

#line 43
                thread array<uint, int(16)> _S38 = want_2;

#line 43
                exchange_0(r_4, &_S38, _S18, lgTB_1, kernelContext_3);

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
                thread array<uint, int(16)> want_3;

#line 8
                z_1 = 0U;
                for(;;)
                {

#line 9
                    if(z_1 < 16U)
                    {
                    }
                    else
                    {

#line 9
                        break;
                    }

#line 9
                    want_3[z_1] = 0U;

#line 9
                    z_1 = z_1 + 1U;

#line 9
                }



                uint lgTB_2 = firstbithigh_0(2U);

                uint _S39 = tid_0 >> lgTB_2;
                uint lane_2 = tid_0 & 1U;


                dft16_0(r_4);

#line 27
                float a1_2 = 6.28318548202514648f * float(lane_2) / 32.0f;
                float _S40 = cos(a1_2);

#line 28
                float _S41 = sin(a1_2);

#line 28
                k2_1 = 0U;

#line 28
                cr_0 = 1.0f;

#line 28
                ci_0 = 0.0f;

                for(;;)
                {

#line 30
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 30
                        break;
                    }

#line 31
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_2 = cr_0 * _S40 - ci_0 * _S41;
                    float _S42 = cr_0 * _S41 + ci_0 * _S40;

#line 30
                    k2_1 = k2_1 + 1U;

#line 30
                    cr_0 = nr_2;

#line 30
                    ci_0 = _S42;

#line 30
                }

#line 40
                uint _S43 = 16U / _S21;
                uint _S44 = max(0U, 1U);
                uint _S45 = tid_0 / _S44;

#line 42
                uint _S46 = tid_0 % _S44;

#line 42
                d_2 = 0U;
                for(;;)
                {

#line 43
                    if(d_2 < 16U)
                    {
                    }
                    else
                    {

#line 43
                        break;
                    }

#line 44
                    uint j_3 = d_2 / _S21;

#line 44
                    uint m_2 = d_2 % _S21;
                    want_3[d_2] = _S39 * 32U + (lane_2 * _S43 + j_3) * 2U + m_2;

#line 43
                    d_2 = d_2 + 1U;

#line 43
                }

#line 43
                thread array<uint, int(16)> _S47 = want_3;

#line 43
                exchange_0(r_4, &_S47, _S20, lgTB_2, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        break;
    }

#line 51
    innermost_0(r_4);

#line 585 "mm_8192_refineListed_onebin.slang"
    return;
}


#line 551
uint lgOf_0(uint i_4)
{

#line 551
    uint _S48;

#line 551
    if(i_4 < 3U)
    {

#line 551
        _S48 = 4U;

#line 551
    }
    else
    {

#line 551
        _S48 = 1U;

#line 551
    }

#line 551
    return _S48;
}


#line 553
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 557
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 557
    uint lg_2 = lgOf_0(1U);

#line 557
    uint lg_3 = lgOf_0(0U);

#line 562
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 597
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{


    bool live_0;

#line 611
    kernelContext_4->_tid_0 = tid_1;
    uint _S49 = pair_0 / ntmpl_1;

#line 612
    uint _S50 = pair_0 % ntmpl_1;

    thread array<float2, int(16)> r_5;

#line 614
    uint n2_0 = 0U;

#line 625
    for(;;)
    {

#line 625
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 625
            break;
        }

#line 626
        uint idx_0 = tid_1 + 512U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S49 * 8192U + idx_0), cload_0(tmpl_0, _S50 * 8192U + idx_0));

#line 625
        n2_0 = n2_0 + 1U;

#line 625
    }

#line 625
    transform_0(&r_5, tid_1, kernelContext_4);

#line 644
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 644
    uint b_7 = tid_1;

#line 652
    for(;;)
    {

#line 652
        if(b_7 < 1U)
        {
        }
        else
        {

#line 652
            break;
        }

#line 652
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_7] = thrBits_1;

#line 652
        b_7 = b_7 + 512U;

#line 652
    }
    bool _S51 = tid_1 == 0U;

#line 653
    if(_S51)
    {

#line 653
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 653
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;

#line 657
    uint i_5 = 0U;

    for(;;)
    {

#line 659
        if(i_5 < 16U)
        {
        }
        else
        {

#line 659
            break;
        }

#line 660
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_5);
        if(idx_1 >= winStart_1)
        {

#line 661
            live_0 = idx_1 < winEnd_1;

#line 661
        }
        else
        {

#line 661
            live_0 = false;

#line 661
        }



        float _rx_0 = r_5[i_5].x;

#line 665
        float _ry_0 = r_5[i_5].y;
        if(live_0)
        {

#line 666
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 666
        }
        else
        {

#line 666
            n2_0 = 0U;

#line 666
        }

#line 666
        myMag_0[i_5] = n2_0;
        uint off_0 = idx_1 - winStart_1;

#line 674
        if(live_0)
        {

#line 674
            if(binShift_1 >= int(0))
            {
            }
            else
            {

#line 674
                uint _S52 = off_0 / binsize_1;

#line 674
            }

#line 674
        }

#line 659
        i_5 = i_5 + 1U;

#line 659
    }

#line 659
    uint bestBits_0 = thrBits_1;

#line 659
    i_5 = 0U;

#line 694
    for(;;)
    {

#line 694
        if(i_5 < 16U)
        {
        }
        else
        {

#line 694
            break;
        }

#line 694
        uint _S53 = max(bestBits_0, myMag_0[i_5]);

#line 694
        uint i_6 = i_5 + 1U;

#line 694
        bestBits_0 = _S53;

#line 694
        i_5 = i_6;

#line 694
    }

    uint wm_0 = simd_max(bestBits_0);
    bool _S54 = simd_is_first();

#line 697
    if(_S54)
    {

#line 697
        live_0 = wm_0 > thrBits_1;

#line 697
    }
    else
    {

#line 697
        live_0 = false;

#line 697
    }

#line 697
    if(live_0)
    {

#line 697
        uint _S55 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 697
    }

#line 712
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 712
    uint winner_0 = 4294967295U;

#line 712
    i_5 = 0U;

#line 722
    for(;;)
    {

#line 722
        if(i_5 < 16U)
        {
        }
        else
        {

#line 722
            break;
        }

#line 723
        if((myMag_0[i_5]) > thrBits_1)
        {

#line 723
            live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 723
        }
        else
        {

#line 723
            live_0 = false;

#line 723
        }

#line 723
        if(live_0)
        {

#line 723
            winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 723
        }

#line 722
        i_5 = i_5 + 1U;

#line 722
    }



    uint waveWinner_0 = simd_min(winner_0);
    bool _S56 = simd_is_first();

#line 727
    if(_S56)
    {

#line 727
        live_0 = waveWinner_0 != 4294967295U;

#line 727
    }
    else
    {

#line 727
        live_0 = false;

#line 727
    }

#line 727
    if(live_0)
    {

#line 728
        uint _S57 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 727
    }

#line 732
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 732
    i_5 = 0U;
    for(;;)
    {

#line 733
        if(i_5 < 16U)
        {
        }
        else
        {

#line 733
            break;
        }

#line 734
        uint _S58 = tid_1 * 16U + i_5;

#line 734
        if(_S58 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
        {

#line 735
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S58));

#line 735
            *(peakVal_0+pair_0) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 734
        }

#line 733
        i_5 = i_5 + 1U;

#line 733
    }

#line 739
    if(_S51)
    {

#line 739
        live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 739
    }
    else
    {

#line 739
        live_0 = false;

#line 739
    }

#line 739
    if(live_0)
    {

#line 740
        *(peakIdx_0+pair_0) = int(-1);

#line 740
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 739
    }

#line 772
    return;
}


#line 1073
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1073
    thread KernelContext_0 kernelContext_5;

#line 1073
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1073
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1073
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1073
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1073
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1073
    (&kernelContext_5)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1073
    threadgroup array<uint, int(8192)> stg_1;

#line 1073
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1082
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1088
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 1088
    filterPair_0(pair_1, lid_0.x, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);


    return;
}
