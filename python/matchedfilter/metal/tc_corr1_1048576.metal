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


#line 187 "/home/ahnitz/projects/claude/searchdev/work/mf-full-corr/python/matchedfilter/metal/tc_corr1_1048576.slang"
float2 cmulConj_0(float2 a_0, float2 b_0)
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
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 336
void r4_0(float2 thread* a_1, float2 thread* b_1, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 338
    float2 t1_0 = *a_1 - *c_0;

#line 338
    float2 t2_0 = *b_1 + *d_0;

#line 338
    float2 t3_0 = *b_1 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 340
    *b_1 = t1_0 + j3_0;

#line 340
    *c_0 = t0_0 - t2_0;

#line 340
    *d_0 = t1_0 - j3_0;
    return;
}


#line 186
float2 cmul_0(float2 a_2, float2 b_2)
{

#line 186
    float _S6 = a_2.x;

#line 186
    float _S7 = b_2.x;

#line 186
    float _S8 = a_2.y;

#line 186
    float _S9 = b_2.y;

#line 186
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 372
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 379
    uint n1_0 = 0U;
    for(;;)
    {

#line 380
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 380
            break;
        }

#line 380
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 380
        n1_0 = n1_0 + 1U;

#line 380
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 381
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 381
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 382
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 382
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 383
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 383
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 383
    uint k2_0 = 0U;
    for(;;)
    {

#line 384
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 384
            break;
        }

#line 384
        uint _S10 = 4U * k2_0;

#line 384
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 384
        k2_0 = k2_0 + 1U;

#line 384
    }

    float2 t_0 = (*r_0)[int(1)];

#line 386
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 386
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 387
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 387
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 388
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 388
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 389
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 389
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 390
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 390
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 391
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 391
    (*r_0)[int(14)] = t_5;
    return;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint ntmpl_0;
};


#line 175 "/home/ahnitz/projects/claude/searchdev/work/mf-full-corr/python/matchedfilter/metal/tc_corr1_1048576.slang"
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


#line 175
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 175
    uint _S11 = 2U * i_0;

#line 175
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11] = (as_type<uint>((v_0.x)));

#line 175
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11 + 1U] = (as_type<uint>((v_0.y)));

#line 175
    return;
}


#line 176
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 176
    uint _S12 = 2U * i_1;

#line 176
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12 + 1U]))));
}


#line 497
void exchange_0(array<float2, int(16)> thread* r_1, const array<uint, int(16)> thread* want_0, uint lgLen_0, uint lgSpan_0, KernelContext_0 thread* kernelContext_2)
{

#line 497
    uint j_0;

#line 508
    thread array<float2, int(16)> out_0;

#line 508
    uint z_0 = 0U;
    for(;;)
    {

#line 509
        if(z_0 < 16U)
        {
        }
        else
        {

#line 509
            break;
        }

#line 509
        out_0[z_0] = float2(0.0, 0.0);

#line 509
        z_0 = z_0 + 1U;

#line 509
    }
    uint _S13 = (1U << lgSpan_0) - 1U;
    uint _S14 = (1U << lgLen_0) - 1U;

#line 511
    uint c_1 = 0U;
    for(;;)
    {

#line 512
        if(c_1 < 2U)
        {
        }
        else
        {

#line 512
            break;
        }

#line 513
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 513
        j_0 = 0U;
        for(;;)
        {

#line 514
            if(j_0 < 8U)
            {
            }
            else
            {

#line 514
                break;
            }

#line 514
            stgPut_0(j_0 * 64U + kernelContext_2->_tid_0, (*r_1)[c_1 * 8U + j_0], kernelContext_2);

#line 514
            j_0 = j_0 + 1U;

#line 514
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 515
        uint d_1 = 0U;
        for(;;)
        {

#line 516
            if(d_1 < 16U)
            {
            }
            else
            {

#line 516
                break;
            }
            uint b_3 = ((*want_0)[d_1]) >> lgLen_0;

#line 518
            uint rem_0 = ((*want_0)[d_1]) & _S14;
            uint i_2 = rem_0 >> lgSpan_0;

#line 519
            uint ln_0 = rem_0 & _S13;
            uint _S15 = c_1 * 8U;

#line 520
            bool _S16;

#line 520
            if(i_2 >= _S15)
            {

#line 520
                _S16 = i_2 < ((c_1 + 1U) * 8U);

#line 520
            }
            else
            {

#line 520
                _S16 = false;

#line 520
            }

#line 520
            if(_S16)
            {

#line 520
                float2 _S17 = stgGet_0((i_2 - _S15) * 64U + (b_3 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_1] = _S17;

#line 520
            }

#line 516
            d_1 = d_1 + 1U;

#line 516
        }

#line 512
        c_1 = c_1 + 1U;

#line 512
    }

#line 512
    j_0 = 0U;

#line 524
    for(;;)
    {

#line 524
        if(j_0 < 16U)
        {
        }
        else
        {

#line 524
            break;
        }

#line 524
        (*r_1)[j_0] = out_0[j_0];

#line 524
        j_0 = j_0 + 1U;

#line 524
    }
    return;
}


#line 351
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 354
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 354
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 475
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 475
    uint b_4 = 0U;

#line 484
    for(;;)
    {

#line 484
        if(b_4 < 4U)
        {
        }
        else
        {

#line 484
            break;
        }

#line 484
        dft4_0(r_3, b_4 * 4U);

#line 484
        b_4 = b_4 + 1U;

#line 484
    }


    return;
}


#line 579
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 579
    uint z_1;

#line 579
    uint _S18;

#line 579
    uint k2_1;

#line 579
    float cr_0;

#line 579
    float ci_0;

#line 579
    uint _S19;

#line 579
    uint d_2;

#line 579
    for(;;)
    {

#line 579
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/mf-full-corr/src/gpu/fft_transform.slang"
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



                uint lgTB_0 = firstbithigh_0(64U);

#line 13
                _S18 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(1024U);

                uint lane_0 = tid_0 & 63U;


                dft16_0(r_4);

#line 27
                float a1_0 = 6.28318548202514648 * float(lane_0) / 1024.0;
                float _S20 = cos(a1_0);

#line 28
                float _S21 = sin(a1_0);

#line 28
                k2_1 = 0U;

#line 28
                cr_0 = 1.0;

#line 28
                ci_0 = 0.0;

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
                    float nr_0 = cr_0 * _S20 - ci_0 * _S21;
                    float _S22 = cr_0 * _S21 + ci_0 * _S20;

#line 30
                    k2_1 = k2_1 + 1U;

#line 30
                    cr_0 = nr_0;

#line 30
                    ci_0 = _S22;

#line 30
                }

#line 40
                uint _S23 = max(64U, 1U);

#line 40
                uint _S24 = 16U / _S23;
                uint _S25 = max(4U, 1U);

#line 41
                _S19 = _S25;
                uint _S26 = tid_0 / _S25;

#line 42
                uint _S27 = tid_0 % _S25;

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
                    uint j_1 = d_2 / _S23;

#line 44
                    uint m_0 = d_2 % _S23;
                    want_1[d_2] = _S26 * 64U + _S27 + _S25 * d_2;

#line 43
                    d_2 = d_2 + 1U;

#line 43
                }

#line 43
                thread array<uint, int(16)> _S28 = want_1;

#line 43
                exchange_0(r_4, &_S28, lgLn_0, lgTB_0, kernelContext_3);

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



                uint lgTB_1 = firstbithigh_0(4U);

                uint _S29 = tid_0 >> lgTB_1;
                uint lane_1 = tid_0 & 3U;


                dft16_0(r_4);

#line 27
                float a1_1 = 6.28318548202514648 * float(lane_1) / 64.0;
                float _S30 = cos(a1_1);

#line 28
                float _S31 = sin(a1_1);

#line 28
                k2_1 = 0U;

#line 28
                cr_0 = 1.0;

#line 28
                ci_0 = 0.0;

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
                    float nr_1 = cr_0 * _S30 - ci_0 * _S31;
                    float _S32 = cr_0 * _S31 + ci_0 * _S30;

#line 30
                    k2_1 = k2_1 + 1U;

#line 30
                    cr_0 = nr_1;

#line 30
                    ci_0 = _S32;

#line 30
                }

#line 40
                uint _S33 = 16U / _S19;
                uint _S34 = max(0U, 1U);
                uint _S35 = tid_0 / _S34;

#line 42
                uint _S36 = tid_0 % _S34;

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
                    want_2[d_2] = _S29 * 64U + (lane_1 * _S33 + j_2) * 4U + m_1;

#line 43
                    d_2 = d_2 + 1U;

#line 43
                }

#line 43
                thread array<uint, int(16)> _S37 = want_2;

#line 43
                exchange_0(r_4, &_S37, _S18, lgTB_1, kernelContext_3);

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

#line 582 "/home/ahnitz/projects/claude/searchdev/work/mf-full-corr/python/matchedfilter/metal/tc_corr1_1048576.slang"
    return;
}


#line 548
uint lgOf_0(uint i_3)
{

#line 548
    uint _S38;

#line 548
    if(i_3 < 2U)
    {

#line 548
        _S38 = 4U;

#line 548
    }
    else
    {

#line 548
        _S38 = 1U;

#line 548
    }

#line 548
    return _S38;
}


#line 550
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 554
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 554
    uint lg_2 = lgOf_0(1U);

#line 554
    uint lg_3 = lgOf_0(0U);

#line 559
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 1092
[[kernel]] void tcStage1(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], packed_float2 device* entryPointParams_scratch_1 [[buffer(3)]])
{

#line 1092
    thread KernelContext_0 kernelContext_4;

#line 1092
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1092
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1092
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1092
    (&kernelContext_4)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 1092
    threadgroup array<uint, int(1024)> stg_1;

#line 1092
    (&kernelContext_4)->stg_0 = &stg_1;



    uint _S39 = gid_0.x;

#line 1096
    uint pair_0 = _S39 / 1024U;

#line 1096
    uint _S40 = _S39 % 1024U;
    uint _S41 = pair_0 / entryPointParams_1->ntmpl_0;

#line 1097
    uint _S42 = pair_0 % entryPointParams_1->ntmpl_0;
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;

    thread array<float2, int(16)> r_5;

#line 1102
    uint m_2 = 0U;
    for(;;)
    {

#line 1103
        if(m_2 < 16U)
        {
        }
        else
        {

#line 1103
            break;
        }

#line 1104
        uint j_3 = _S40 + 1024U * (tid_1 + 64U * m_2);
        r_5[m_2] = cmulConj_0(float2(*((&kernelContext_4)->entryPointParams_data_0+(_S41 * 1048576U + j_3))) , float2(*((&kernelContext_4)->entryPointParams_tmpl_0+(_S42 * 1048576U + j_3))) );

#line 1103
        m_2 = m_2 + 1U;

#line 1103
    }

#line 1103
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 1103
    uint i_4 = 0U;

#line 1112
    for(;;)
    {

#line 1112
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1112
            break;
        }

#line 1113
        uint k2_2 = slotToIndex_0(tid_1 * 16U + i_4);
        float a_3 = 6.28318548202514648 * float(_S40 * k2_2) / 1.048576e+06;

#line 1114
        *((&kernelContext_4)->entryPointParams_scratch_0+(pair_0 * 1048576U + k2_2 * 1024U + _S40)) = packed_float2(cmul_0(r_5[i_4], float2(cos(a_3), sin(a_3)))) ;

#line 1112
        i_4 = i_4 + 1U;

#line 1112
    }

#line 1117
    return;
}
