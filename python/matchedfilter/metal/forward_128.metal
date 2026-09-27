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


#line 338 "/tmp/tmpjybyhagl/forward.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 340
    float2 t1_0 = *a_0 - *c_0;

#line 340
    float2 t2_0 = *b_0 + *d_0;

#line 340
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 342
    *b_0 = t1_0 + j3_0;

#line 342
    *c_0 = t0_0 - t2_0;

#line 342
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


#line 374
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

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
        uint _S6 = 4U * k2_0;

#line 386
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

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


#line 10 "/home/ahnitz/projects/claude/searchdev/work/mf-main-merge/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 90 "core"
struct EntryPointParams_0
{
    uint seriesLength_0;
};


#line 176 "/tmp/tmpjybyhagl/forward.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_spectra_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(256)> threadgroup* stg_0;
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


#line 177
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 177
    uint _S8 = 2U * i_1;

#line 177
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S8]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S8 + 1U]))));
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
        out_0[z_0] = float2(0.0f, 0.0f);

#line 511
        z_0 = z_0 + 1U;

#line 511
    }
    uint _S9 = (1U << lgSpan_0) - 1U;
    uint _S10 = (1U << lgLen_0) - 1U;

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
            stgPut_0(j_0 * 8U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_0], kernelContext_2);

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
            uint b_2 = ((*want_0)[d_1]) >> lgLen_0;

#line 520
            uint rem_0 = ((*want_0)[d_1]) & _S10;
            uint i_2 = rem_0 >> lgSpan_0;

#line 521
            uint ln_0 = rem_0 & _S9;
            uint _S11 = c_1 * 16U;

#line 522
            bool _S12;

#line 522
            if(i_2 >= _S11)
            {

#line 522
                _S12 = i_2 < ((c_1 + 1U) * 16U);

#line 522
            }
            else
            {

#line 522
                _S12 = false;

#line 522
            }

#line 522
            if(_S12)
            {

#line 522
                float2 _S13 = stgGet_0((i_2 - _S11) * 8U + (b_2 << lgSpan_0) + ln_0, kernelContext_2);
                out_0[d_1] = _S13;

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


    thread array<float2, int(8)> b_3;

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


            uint _S14 = o_0 + j_1;

#line 368
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_0)), (*r_2)[_S14 + 4U]);
            uint _S15 = ((j_1 - k_0) << 1U) + k_0;

#line 369
            b_3[_S15] = (*r_2)[_S14] + t_6;

#line 369
            b_3[_S15 + s_0] = (*r_2)[_S14] - t_6;

#line 364
            j_1 = j_1 + 1U;

#line 364
        }

#line 364
        uint i_3 = 0U;

#line 371
        for(;;)
        {

#line 371
            if(i_3 < 8U)
            {
            }
            else
            {

#line 371
                break;
            }

#line 371
            (*r_2)[o_0 + i_3] = b_3[i_3];

#line 371
            i_3 = i_3 + 1U;

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
    uint b_4 = 0U;

#line 485
    for(;;)
    {

#line 485
        if(b_4 < 2U)
        {
        }
        else
        {

#line 485
            break;
        }

#line 485
        dft8_0(r_3, b_4 * 8U);

#line 485
        b_4 = b_4 + 1U;

#line 485
    }



    return;
}


#line 1299
void forwardTransform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 1299
    for(;;)
    {

#line 1299
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/mf-main-merge/src/gpu/fft_transform.slang"
            for(;;)
            {

#line 8
                thread array<uint, int(16)> want_1;

#line 8
                uint z_1 = 0U;
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



                uint lgTB_0 = firstbithigh_0(8U);
                uint lgLn_0 = firstbithigh_0(128U);
                uint _S16 = tid_0 >> lgTB_0;
                uint lane_0 = tid_0 & 7U;


                dft16_0(r_4);

#line 28
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_0) / 128.0f);
                float _S17 = tw_0.x;

#line 29
                float _S18 = tw_0.y;

#line 29
                uint k2_1 = 0U;

#line 29
                float cr_0 = 1.0f;

#line 29
                float ci_0 = 0.0f;

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
                    float nr_0 = cr_0 * _S17 - ci_0 * _S18;
                    float _S19 = cr_0 * _S18 + ci_0 * _S17;

#line 31
                    k2_1 = k2_1 + 1U;

#line 31
                    cr_0 = nr_0;

#line 31
                    ci_0 = _S19;

#line 31
                }

#line 41
                uint _S20 = max(8U, 1U);

#line 41
                uint _S21 = 16U / _S20;
                uint _S22 = max(0U, 1U);
                uint _S23 = tid_0 / _S22;

#line 43
                uint _S24 = tid_0 % _S22;

#line 43
                uint d_2 = 0U;
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
                    uint j_2 = d_2 / _S20;

#line 45
                    uint m_0 = d_2 % _S20;
                    want_1[d_2] = _S16 * 128U + (lane_0 * _S21 + j_2) * 8U + m_0;

#line 44
                    d_2 = d_2 + 1U;

#line 44
                }

#line 44
                thread array<uint, int(16)> _S25 = want_1;

#line 44
                exchange_0(r_4, &_S25, lgLn_0, lgTB_0, kernelContext_3);

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

#line 1302 "/tmp/tmpjybyhagl/forward.slang"
    return;
}


#line 550
uint lgOf_0(uint i_4)
{

#line 550
    uint _S26;

#line 550
    if(i_4 < 1U)
    {

#line 550
        _S26 = 4U;

#line 550
    }
    else
    {

#line 550
        if(i_4 == 1U)
        {

#line 550
            _S26 = 3U;

#line 550
        }
        else
        {

#line 550
            _S26 = 1U;

#line 550
        }

#line 550
    }

#line 550
    return _S26;
}


#line 552
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 556
    uint lg_1 = lgOf_0(0U);

#line 561
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 1307
[[kernel]] void seriesForward(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]])
{

#line 1307
    thread KernelContext_0 kernelContext_4;

#line 1307
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1307
    (&kernelContext_4)->entryPointParams_series_0 = entryPointParams_series_1;

#line 1307
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1307
    (&kernelContext_4)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 1307
    threadgroup array<uint, int(256)> stg_1;

#line 1307
    (&kernelContext_4)->stg_0 = &stg_1;

#line 1313
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    uint _S27 = gid_0.x;

#line 1316
    uint _S28 = entryPointParams_starts_1[_S27];
    thread array<float2, int(16)> r_5;

#line 1317
    uint k_1 = 0U;
    for(;;)
    {

#line 1318
        if(k_1 < 16U)
        {
        }
        else
        {

#line 1318
            break;
        }

#line 1319
        uint offset_0 = tid_1 + 8U * k_1;
        float2 _S29 = float2(0.0f, 0.0f);

#line 1320
        bool _S30;

        if(_S28 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0))
        {

#line 1322
            _S30 = offset_0 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0 - _S28);

#line 1322
        }
        else
        {

#line 1322
            _S30 = false;

#line 1322
        }

#line 1322
        float2 x_0;

#line 1322
        if(_S30)
        {

#line 1322
            x_0 = float2(*((&kernelContext_4)->entryPointParams_series_0+(_S28 + offset_0))) ;

#line 1322
        }
        else
        {

#line 1322
            x_0 = _S29;

#line 1322
        }

        r_5[k_1] = float2(x_0.x / 128.0f, - x_0.y / 128.0f);

#line 1318
        k_1 = k_1 + 1U;

#line 1318
    }

#line 1318
    forwardTransform_0(&r_5, tid_1, &kernelContext_4);

#line 1318
    k_1 = 0U;

#line 1327
    for(;;)
    {

#line 1327
        if(k_1 < 16U)
        {
        }
        else
        {

#line 1327
            break;
        }

#line 1327
        *((&kernelContext_4)->entryPointParams_spectra_0+(_S27 * 128U + slotToIndex_0(tid_1 * 16U + k_1))) = packed_float2(float2(r_5[k_1].x, - r_5[k_1].y)) ;

#line 1327
        k_1 = k_1 + 1U;

#line 1327
    }



    return;
}
