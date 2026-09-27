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


#line 151 "mm_16384_fusedTierB.slang"
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


#line 190
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


#line 10 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
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


#line 179 "mm_16384_fusedTierB.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
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
void exchange_0(array<float2, int(16)> thread* r_1, const array<uint, int(16)> thread* want_0, uint lgLen_0, uint lgSpan_0, KernelContext_0 thread* kernelContext_2)
{

#line 502
    uint j_0;

#line 513
    thread array<float2, int(16)> out_0;

#line 513
    uint z_0 = 0U;
    for(;;)
    {

#line 514
        if(z_0 < 16U)
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
        if(c_1 < 2U)
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
        j_0 = 0U;
        for(;;)
        {

#line 519
            if(j_0 < 8U)
            {
            }
            else
            {

#line 519
                break;
            }

#line 519
            stgPut_0(j_0 * 1024U + kernelContext_2->_tid_0, (*r_1)[c_1 * 8U + j_0], kernelContext_2);

#line 519
            j_0 = j_0 + 1U;

#line 519
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 520
        uint d_1 = 0U;
        for(;;)
        {

#line 521
            if(d_1 < 16U)
            {
            }
            else
            {

#line 521
                break;
            }
            uint b_4 = ((*want_0)[d_1]) >> lgLen_0;

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
                float2 _S17 = stgGet_0((i_3 - _S15) * 1024U + (b_4 << lgSpan_0) + ln_0, kernelContext_2);
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
    j_0 = 0U;

#line 529
    for(;;)
    {

#line 529
        if(j_0 < 16U)
        {
        }
        else
        {

#line 529
            break;
        }

#line 529
        (*r_1)[j_0] = out_0[j_0];

#line 529
        j_0 = j_0 + 1U;

#line 529
    }
    return;
}


#line 356
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 359
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 359
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 480
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 480
    uint b_5 = 0U;

#line 489
    for(;;)
    {

#line 489
        if(b_5 < 4U)
        {
        }
        else
        {

#line 489
            break;
        }

#line 489
        dft4_0(r_3, b_5 * 4U);

#line 489
        b_5 = b_5 + 1U;

#line 489
    }


    return;
}


#line 584
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
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
    uint _S20;

#line 584
    uint _S21;

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



                uint lgTB_0 = firstbithigh_0(1024U);

#line 13
                _S18 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(16384U);

                uint lane_0 = tid_0 & 1023U;


                dft16_0(r_4);

#line 28
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_0) / 16384.0f);
                float _S22 = tw_0.x;

#line 29
                float _S23 = tw_0.y;

#line 29
                k2_1 = 0U;

#line 29
                cr_0 = 1.0f;

#line 29
                ci_0 = 0.0f;

                for(;;)
                {

#line 31
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 31
                        break;
                    }

#line 32
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S22 - ci_0 * _S23;
                    float _S24 = cr_0 * _S23 + ci_0 * _S22;

#line 31
                    k2_1 = k2_1 + 1U;

#line 31
                    cr_0 = nr_0;

#line 31
                    ci_0 = _S24;

#line 31
                }

#line 41
                uint _S25 = max(1024U, 1U);

#line 41
                uint _S26 = 16U / _S25;
                uint _S27 = max(64U, 1U);

#line 42
                _S19 = _S27;
                uint _S28 = tid_0 / _S27;

#line 43
                uint _S29 = tid_0 % _S27;

#line 43
                d_2 = 0U;
                for(;;)
                {

#line 44
                    if(d_2 < 16U)
                    {
                    }
                    else
                    {

#line 44
                        break;
                    }

#line 45
                    uint j_1 = d_2 / _S25;

#line 45
                    uint m_0 = d_2 % _S25;
                    want_1[d_2] = _S28 * 1024U + _S29 + _S27 * d_2;

#line 44
                    d_2 = d_2 + 1U;

#line 44
                }

#line 44
                thread array<uint, int(16)> _S30 = want_1;

#line 44
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



                uint lgTB_1 = firstbithigh_0(64U);

#line 13
                _S20 = lgTB_1;


                uint lane_1 = tid_0 & 63U;


                dft16_0(r_4);

#line 28
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 1024.0f);
                float _S31 = tw_1.x;

#line 29
                float _S32 = tw_1.y;

#line 29
                k2_1 = 0U;

#line 29
                cr_0 = 1.0f;

#line 29
                ci_0 = 0.0f;

                for(;;)
                {

#line 31
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 31
                        break;
                    }

#line 32
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S31 - ci_0 * _S32;
                    float _S33 = cr_0 * _S32 + ci_0 * _S31;

#line 31
                    k2_1 = k2_1 + 1U;

#line 31
                    cr_0 = nr_1;

#line 31
                    ci_0 = _S33;

#line 31
                }

#line 41
                uint _S34 = 16U / _S19;
                uint _S35 = max(4U, 1U);

#line 42
                _S21 = _S35;
                uint _S36 = tid_0 / _S35;

#line 43
                uint _S37 = tid_0 % _S35;

#line 43
                d_2 = 0U;
                for(;;)
                {

#line 44
                    if(d_2 < 16U)
                    {
                    }
                    else
                    {

#line 44
                        break;
                    }

#line 45
                    uint j_2 = d_2 / _S19;

#line 45
                    uint m_1 = d_2 % _S19;
                    want_2[d_2] = _S36 * 64U + _S37 + _S35 * d_2;

#line 44
                    d_2 = d_2 + 1U;

#line 44
                }

#line 44
                thread array<uint, int(16)> _S38 = want_2;

#line 44
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



                uint lgTB_2 = firstbithigh_0(4U);

                uint _S39 = tid_0 >> lgTB_2;
                uint lane_2 = tid_0 & 3U;


                dft16_0(r_4);

#line 28
                float2 tw_2 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 64.0f);
                float _S40 = tw_2.x;

#line 29
                float _S41 = tw_2.y;

#line 29
                k2_1 = 0U;

#line 29
                cr_0 = 1.0f;

#line 29
                ci_0 = 0.0f;

                for(;;)
                {

#line 31
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 31
                        break;
                    }

#line 32
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_2 = cr_0 * _S40 - ci_0 * _S41;
                    float _S42 = cr_0 * _S41 + ci_0 * _S40;

#line 31
                    k2_1 = k2_1 + 1U;

#line 31
                    cr_0 = nr_2;

#line 31
                    ci_0 = _S42;

#line 31
                }

#line 41
                uint _S43 = 16U / _S21;
                uint _S44 = max(0U, 1U);
                uint _S45 = tid_0 / _S44;

#line 43
                uint _S46 = tid_0 % _S44;

#line 43
                d_2 = 0U;
                for(;;)
                {

#line 44
                    if(d_2 < 16U)
                    {
                    }
                    else
                    {

#line 44
                        break;
                    }

#line 45
                    uint j_3 = d_2 / _S21;

#line 45
                    uint m_2 = d_2 % _S21;
                    want_3[d_2] = _S39 * 64U + (lane_2 * _S43 + j_3) * 4U + m_2;

#line 44
                    d_2 = d_2 + 1U;

#line 44
                }

#line 44
                thread array<uint, int(16)> _S47 = want_3;

#line 44
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

#line 52
    innermost_0(r_4);

#line 587 "mm_16384_fusedTierB.slang"
    return;
}


#line 553
uint lgOf_0(uint i_4)
{

#line 553
    uint _S48;

#line 553
    if(i_4 < 3U)
    {

#line 553
        _S48 = 4U;

#line 553
    }
    else
    {

#line 553
        _S48 = 1U;

#line 553
    }

#line 553
    return _S48;
}


#line 555
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(4U);

    uint x_0 = slot_0 >> lg_0;

#line 559
    uint lg_1 = lgOf_0(3U);

    uint x_1 = x_0 >> lg_1;

#line 559
    uint lg_2 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_2;

#line 559
    uint lg_3 = lgOf_0(1U);

#line 559
    uint lg_4 = lgOf_0(0U);

#line 564
    return (((((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | (x_2 & ((1U << lg_3) - 1U))) << lg_4) | ((x_2 >> lg_3) & ((1U << lg_4) - 1U));
}


#line 599
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 613
    kernelContext_4->_tid_0 = tid_1;
    uint _S49 = pair_0 / ntmpl_1;

#line 614
    uint _S50 = pair_0 % ntmpl_1;

    thread array<float2, int(16)> r_5;

#line 616
    uint n2_0 = 0U;

#line 627
    for(;;)
    {

#line 627
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 627
            break;
        }

#line 628
        uint idx_0 = tid_1 + 1024U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S49 * 16384U + idx_0), cload_0(tmpl_0, _S50 * 16384U + idx_0));

#line 627
        n2_0 = n2_0 + 1U;

#line 627
    }

#line 627
    transform_0(&r_5, tid_1, kernelContext_4);

#line 646
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 646
    uint b_6 = tid_1;

#line 654
    for(;;)
    {

#line 654
        if(b_6 < nbins_1)
        {
        }
        else
        {

#line 654
            break;
        }

#line 654
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6] = thrBits_1;

#line 654
        b_6 = b_6 + 1024U;

#line 654
    }
    bool _S51 = nbins_1 == 1U;

#line 655
    bool live_0;

#line 655
    if(_S51)
    {

#line 655
        live_0 = tid_1 == 0U;

#line 655
    }
    else
    {

#line 655
        live_0 = false;

#line 655
    }

#line 655
    if(live_0)
    {

#line 655
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 655
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 660
    uint i_5 = 0U;
    for(;;)
    {

#line 661
        if(i_5 < 16U)
        {
        }
        else
        {

#line 661
            break;
        }

#line 662
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_5);
        if(idx_1 >= winStart_1)
        {

#line 663
            live_0 = idx_1 < winEnd_1;

#line 663
        }
        else
        {

#line 663
            live_0 = false;

#line 663
        }



        float _rx_0 = r_5[i_5].x;

#line 667
        float _ry_0 = r_5[i_5].y;
        if(live_0)
        {

#line 668
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 668
        }
        else
        {

#line 668
            n2_0 = 0U;

#line 668
        }

#line 668
        myMag_0[i_5] = n2_0;
        uint off_0 = idx_1 - winStart_1;

#line 676
        if(live_0)
        {

#line 676
            if(binShift_1 >= int(0))
            {

#line 676
                b_6 = off_0 >> uint(binShift_1);

#line 676
            }
            else
            {

#line 676
                uint _S52 = off_0 / binsize_1;

#line 676
                b_6 = _S52;

#line 676
            }

#line 676
        }
        else
        {

#line 676
            b_6 = 0U;

#line 676
        }

#line 676
        myBin_0[i_5] = b_6;

#line 676
        bool _S53;



        if(nbins_1 > 1U)
        {

#line 680
            _S53 = (myMag_0[i_5]) > thrBits_1;

#line 680
        }
        else
        {

#line 680
            _S53 = false;

#line 680
        }

#line 680
        if(_S53)
        {

#line 681
            uint _S54 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), myMag_0[i_5], memory_order_relaxed);

#line 680
        }

#line 661
        i_5 = i_5 + 1U;

#line 661
    }

#line 661
    uint winner_0;

#line 693
    if(_S51)
    {

#line 693
        winner_0 = thrBits_1;

#line 693
        i_5 = 0U;


        for(;;)
        {

#line 696
            if(i_5 < 16U)
            {
            }
            else
            {

#line 696
                break;
            }

#line 696
            uint _S55 = max(winner_0, myMag_0[i_5]);

#line 696
            uint i_6 = i_5 + 1U;

#line 696
            winner_0 = _S55;

#line 696
            i_5 = i_6;

#line 696
        }

        uint wm_0 = simd_max(winner_0);
        bool _S56 = simd_is_first();

#line 699
        if(_S56)
        {

#line 699
            live_0 = wm_0 > thrBits_1;

#line 699
        }
        else
        {

#line 699
            live_0 = false;

#line 699
        }

#line 699
        if(live_0)
        {

#line 699
            uint _S57 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 699
        }

#line 693
    }

#line 714
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 721
    if(_S51)
    {

#line 721
        winner_0 = 4294967295U;

#line 721
        i_5 = 0U;


        for(;;)
        {

#line 724
            if(i_5 < 16U)
            {
            }
            else
            {

#line 724
                break;
            }

#line 725
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 725
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 725
            }
            else
            {

#line 725
                live_0 = false;

#line 725
            }

#line 725
            if(live_0)
            {

#line 725
                winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 725
            }

#line 724
            i_5 = i_5 + 1U;

#line 724
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S58 = simd_is_first();

#line 729
        if(_S58)
        {

#line 729
            live_0 = waveWinner_0 != 4294967295U;

#line 729
        }
        else
        {

#line 729
            live_0 = false;

#line 729
        }

#line 729
        if(live_0)
        {

#line 730
            uint _S59 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 729
        }

#line 734
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 734
        i_5 = 0U;
        for(;;)
        {

#line 735
            if(i_5 < 16U)
            {
            }
            else
            {

#line 735
                break;
            }

#line 736
            uint _S60 = tid_1 * 16U + i_5;

#line 736
            if(_S60 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 737
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S60));

#line 737
                *(peakVal_0+pair_0) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 736
            }

#line 735
            i_5 = i_5 + 1U;

#line 735
        }

#line 741
        if(tid_1 == 0U)
        {

#line 741
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 741
        }
        else
        {

#line 741
            live_0 = false;

#line 741
        }

#line 741
        if(live_0)
        {

#line 742
            *(peakIdx_0+pair_0) = int(-1);

#line 742
            *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 741
        }

#line 721
    }
    else
    {

#line 721
        i_5 = 0U;

#line 750
        for(;;)
        {

#line 750
            if(i_5 < 16U)
            {
            }
            else
            {

#line 750
                break;
            }

#line 751
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 751
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]];

#line 751
            }
            else
            {

#line 751
                live_0 = false;

#line 751
            }

#line 751
            myMag_0[i_5] = uint(live_0);

#line 750
            i_5 = i_5 + 1U;

#line 750
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 753
        b_6 = tid_1;
        for(;;)
        {

#line 754
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 754
                break;
            }

#line 754
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6] = 4294967295U;

#line 754
            b_6 = b_6 + 1024U;

#line 754
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 755
        i_5 = 0U;
        for(;;)
        {

#line 756
            if(i_5 < 16U)
            {
            }
            else
            {

#line 756
                break;
            }

#line 757
            if((myMag_0[i_5]) != 0U)
            {

#line 757
                uint _S61 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), tid_1 * 16U + i_5, memory_order_relaxed);

#line 757
            }

#line 756
            i_5 = i_5 + 1U;

#line 756
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 758
        i_5 = 0U;
        for(;;)
        {

#line 759
            if(i_5 < 16U)
            {
            }
            else
            {

#line 759
                break;
            }

#line 760
            if((myMag_0[i_5]) != 0U)
            {

#line 760
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]]) == (tid_1 * 16U + i_5);

#line 760
            }
            else
            {

#line 760
                live_0 = false;

#line 760
            }

#line 760
            if(live_0)
            {

#line 761
                uint o_1 = pair_0 * nbins_1 + myBin_0[i_5];
                *(peakIdx_0+o_1) = int(slotToIndex_0(tid_1 * 16U + i_5));

#line 762
                *(peakVal_0+o_1) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 760
            }

#line 759
            i_5 = i_5 + 1U;

#line 759
        }

#line 759
        b_6 = tid_1;

#line 766
        for(;;)
        {

#line 766
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 766
                break;
            }

#line 767
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6]) == 4294967295U)
            {

#line 768
                uint _S62 = pair_0 * nbins_1 + b_6;

#line 768
                *(peakIdx_0+_S62) = int(-1);

#line 768
                *(peakVal_0+_S62) = packed_float2(float2(0.0f, 0.0f)) ;

#line 767
            }

#line 766
            b_6 = b_6 + 1024U;

#line 766
        }

#line 721
    }

#line 774
    return;
}


#line 952
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 952
    thread KernelContext_0 kernelContext_5;

#line 952
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 952
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 952
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 952
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 952
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 952
    threadgroup array<uint, int(16384)> stg_1;

#line 952
    (&kernelContext_5)->stg_0 = &stg_1;

#line 969
    uint _pr_0 = gid_0.x;

#line 969
    uint _t_0 = lid_0.x;
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 970
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);

#line 978
    return;
}
