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


#line 149 "/home/ahnitz/projects/claude/searchdev/work/mf-full-corr/python/matchedfilter/metal/mm_2048_fullCorrelation.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 149
    return float2(*(b_0+i_0)) ;
}


#line 189
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 189
    float _S2 = a_0.x;

#line 189
    float _S3 = b_1.x;

#line 189
    float _S4 = a_0.y;

#line 189
    float _S5 = b_1.y;

#line 189
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 338
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 340
    float2 t1_0 = *a_1 - *c_0;

#line 340
    float2 t2_0 = *b_2 + *d_0;

#line 340
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 342
    *b_2 = t1_0 + j3_0;

#line 342
    *c_0 = t0_0 - t2_0;

#line 342
    *d_0 = t1_0 - j3_0;
    return;
}


#line 188
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 188
    float _S6 = a_2.x;

#line 188
    float _S7 = b_3.x;

#line 188
    float _S8 = a_2.y;

#line 188
    float _S9 = b_3.y;

#line 188
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 374
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 381
    uint n1_0 = 0U;
    for(;;)
    {

#line 382
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 382
            break;
        }

#line 382
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 382
        n1_0 = n1_0 + 1U;

#line 382
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 383
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 383
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 384
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 384
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 385
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 385
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 385
    uint k2_0 = 0U;
    for(;;)
    {

#line 386
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 386
            break;
        }

#line 386
        uint _S10 = 4U * k2_0;

#line 386
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 386
        k2_0 = k2_0 + 1U;

#line 386
    }

    float2 t_0 = (*r_0)[int(1)];

#line 388
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 388
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 389
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 389
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 390
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 390
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 391
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 391
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 392
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 392
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 393
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 393
    (*r_0)[int(14)] = t_5;
    return;
}


#line 8402 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
};


#line 177 "/home/ahnitz/projects/claude/searchdev/work/mf-full-corr/python/matchedfilter/metal/mm_2048_fullCorrelation.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(4096)> threadgroup* stg_0;
};


#line 177
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 177
    uint _S11 = 2U * i_1;

#line 177
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11] = (as_type<uint>((v_0.x)));

#line 177
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11 + 1U] = (as_type<uint>((v_0.y)));

#line 177
    return;
}


#line 178
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 178
    uint _S12 = 2U * i_2;

#line 178
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12 + 1U]))));
}


#line 499
void exchange_0(array<float2, int(16)> thread* r_1, const array<uint, int(16)> thread* want_0, uint lgLen_0, uint lgSpan_0, KernelContext_0 thread* kernelContext_2)
{

#line 499
    uint j_0;

#line 510
    thread array<float2, int(16)> out_0;

#line 510
    uint z_0 = 0U;
    for(;;)
    {

#line 511
        if(z_0 < 16U)
        {
        }
        else
        {

#line 511
            break;
        }

#line 511
        out_0[z_0] = float2(0.0, 0.0);

#line 511
        z_0 = z_0 + 1U;

#line 511
    }
    uint _S13 = (1U << lgSpan_0) - 1U;
    uint _S14 = (1U << lgLen_0) - 1U;

#line 513
    uint c_1 = 0U;
    for(;;)
    {

#line 514
        if(c_1 < 1U)
        {
        }
        else
        {

#line 514
            break;
        }

#line 515
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 515
        j_0 = 0U;
        for(;;)
        {

#line 516
            if(j_0 < 16U)
            {
            }
            else
            {

#line 516
                break;
            }

#line 516
            stgPut_0(j_0 * 128U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_0], kernelContext_2);

#line 516
            j_0 = j_0 + 1U;

#line 516
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 517
        uint d_1 = 0U;
        for(;;)
        {

#line 518
            if(d_1 < 16U)
            {
            }
            else
            {

#line 518
                break;
            }
            uint b_4 = ((*want_0)[d_1]) >> lgLen_0;

#line 520
            uint rem_0 = ((*want_0)[d_1]) & _S14;
            uint i_3 = rem_0 >> lgSpan_0;

#line 521
            uint ln_0 = rem_0 & _S13;
            uint _S15 = c_1 * 16U;

#line 522
            bool _S16;

#line 522
            if(i_3 >= _S15)
            {

#line 522
                _S16 = i_3 < ((c_1 + 1U) * 16U);

#line 522
            }
            else
            {

#line 522
                _S16 = false;

#line 522
            }

#line 522
            if(_S16)
            {

#line 522
                float2 _S17 = stgGet_0((i_3 - _S15) * 128U + (b_4 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_1] = _S17;

#line 522
            }

#line 518
            d_1 = d_1 + 1U;

#line 518
        }

#line 514
        c_1 = c_1 + 1U;

#line 514
    }

#line 514
    j_0 = 0U;

#line 526
    for(;;)
    {

#line 526
        if(j_0 < 16U)
        {
        }
        else
        {

#line 526
            break;
        }

#line 526
        (*r_1)[j_0] = out_0[j_0];

#line 526
        j_0 = j_0 + 1U;

#line 526
    }
    return;
}


#line 358
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_5;

#line 362
    uint s_0 = 1U;
    for(;;)
    {

#line 363
        if(s_0 < 8U)
        {
        }
        else
        {

#line 363
            break;
        }

#line 363
        uint j_1 = 0U;
        for(;;)
        {

#line 364
            if(j_1 < 4U)
            {
            }
            else
            {

#line 364
                break;
            }

#line 365
            uint k_0 = j_1 & (s_0 - 1U);
            float ang_0 = 3.14159274101257324 * float(k_0) / float(s_0);

            uint _S18 = o_0 + j_1;

#line 368
            float2 t_6 = cmul_0(float2(cos(ang_0), sin(ang_0)), (*r_2)[_S18 + 4U]);
            uint _S19 = ((j_1 - k_0) << 1U) + k_0;

#line 369
            b_5[_S19] = (*r_2)[_S18] + t_6;

#line 369
            b_5[_S19 + s_0] = (*r_2)[_S18] - t_6;

#line 364
            j_1 = j_1 + 1U;

#line 364
        }

#line 364
        uint i_4 = 0U;

#line 371
        for(;;)
        {

#line 371
            if(i_4 < 8U)
            {
            }
            else
            {

#line 371
                break;
            }

#line 371
            (*r_2)[o_0 + i_4] = b_5[i_4];

#line 371
            i_4 = i_4 + 1U;

#line 371
        }

#line 363
        s_0 = s_0 << 1U;

#line 363
    }

#line 373
    return;
}


#line 477
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 477
    uint b_6 = 0U;

#line 485
    for(;;)
    {

#line 485
        if(b_6 < 2U)
        {
        }
        else
        {

#line 485
            break;
        }

#line 485
        dft8_0(r_3, b_6 * 8U);

#line 485
        b_6 = b_6 + 1U;

#line 485
    }



    return;
}


#line 581
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 581
    uint z_1;

#line 581
    uint _S20;

#line 581
    uint k2_1;

#line 581
    float cr_0;

#line 581
    float ci_0;

#line 581
    uint _S21;

#line 581
    uint d_2;

#line 581
    for(;;)
    {

#line 581
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



                uint lgTB_0 = firstbithigh_0(128U);

#line 13
                _S20 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(2048U);

                uint lane_0 = tid_0 & 127U;


                dft16_0(r_4);

#line 27
                float a1_0 = 6.28318548202514648 * float(lane_0) / 2048.0;
                float _S22 = cos(a1_0);

#line 28
                float _S23 = sin(a1_0);

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
                uint _S25 = max(128U, 1U);

#line 40
                uint _S26 = 16U / _S25;
                uint _S27 = max(8U, 1U);

#line 41
                _S21 = _S27;
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
                    uint j_2 = d_2 / _S25;

#line 44
                    uint m_0 = d_2 % _S25;
                    want_1[d_2] = _S28 * 128U + _S29 + _S27 * d_2;

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



                uint lgTB_1 = firstbithigh_0(8U);

                uint _S31 = tid_0 >> lgTB_1;
                uint lane_1 = tid_0 & 7U;


                dft16_0(r_4);

#line 27
                float a1_1 = 6.28318548202514648 * float(lane_1) / 128.0;
                float _S32 = cos(a1_1);

#line 28
                float _S33 = sin(a1_1);

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
                    float nr_1 = cr_0 * _S32 - ci_0 * _S33;
                    float _S34 = cr_0 * _S33 + ci_0 * _S32;

#line 30
                    k2_1 = k2_1 + 1U;

#line 30
                    cr_0 = nr_1;

#line 30
                    ci_0 = _S34;

#line 30
                }

#line 40
                uint _S35 = 16U / _S21;
                uint _S36 = max(0U, 1U);
                uint _S37 = tid_0 / _S36;

#line 42
                uint _S38 = tid_0 % _S36;

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
                    uint m_1 = d_2 % _S21;
                    want_2[d_2] = _S31 * 128U + (lane_1 * _S35 + j_3) * 8U + m_1;

#line 43
                    d_2 = d_2 + 1U;

#line 43
                }

#line 43
                thread array<uint, int(16)> _S39 = want_2;

#line 43
                exchange_0(r_4, &_S39, _S20, lgTB_1, kernelContext_3);

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

#line 584 "/home/ahnitz/projects/claude/searchdev/work/mf-full-corr/python/matchedfilter/metal/mm_2048_fullCorrelation.slang"
    return;
}


#line 550
uint lgOf_0(uint i_5)
{

#line 550
    uint _S40;

#line 550
    if(i_5 < 2U)
    {

#line 550
        _S40 = 4U;

#line 550
    }
    else
    {

#line 550
        if(i_5 == 2U)
        {

#line 550
            _S40 = 3U;

#line 550
        }
        else
        {

#line 550
            _S40 = 1U;

#line 550
        }

#line 550
    }

#line 550
    return _S40;
}


#line 552
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 556
    uint lg_1 = lgOf_0(1U);

#line 556
    uint lg_2 = lgOf_0(0U);

#line 561
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 980
[[kernel]] void fullCorrelation(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], packed_float2 device* entryPointParams_output_1 [[buffer(3)]])
{

#line 980
    thread KernelContext_0 kernelContext_4;

#line 980
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 980
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 980
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 980
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 980
    threadgroup array<uint, int(4096)> stg_1;

#line 980
    (&kernelContext_4)->stg_0 = &stg_1;



    uint pair_0 = gid_0.x;

#line 984
    uint tid_1 = lid_0.x;
    uint _S41 = pair_0 / entryPointParams_1->ntmpl_0;

#line 985
    uint _S42 = pair_0 % entryPointParams_1->ntmpl_0;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 988
    uint i_6 = 0U;
    for(;;)
    {

#line 989
        if(i_6 < 16U)
        {
        }
        else
        {

#line 989
            break;
        }

#line 990
        uint idx_0 = tid_1 + 128U * i_6;
        r_5[i_6] = cmulConj_0(cload_0((&kernelContext_4)->entryPointParams_data_0, _S41 * 2048U + idx_0), cload_0((&kernelContext_4)->entryPointParams_tmpl_0, _S42 * 2048U + idx_0));

#line 989
        i_6 = i_6 + 1U;

#line 989
    }

#line 989
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 989
    i_6 = 0U;

#line 994
    for(;;)
    {

#line 994
        if(i_6 < 16U)
        {
        }
        else
        {

#line 994
            break;
        }

#line 994
        *((&kernelContext_4)->entryPointParams_output_0+(pair_0 * 2048U + slotToIndex_0(tid_1 * 16U + i_6))) = packed_float2(float2(r_5[i_6].x, r_5[i_6].y)) ;

#line 994
        i_6 = i_6 + 1U;

#line 994
    }

    return;
}
