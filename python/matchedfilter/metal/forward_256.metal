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


#line 2341 "forward.slang"
float2 seriesSample_0(packed_float2 device* series_0, uint i_0, uint layout_0)
{
    if(layout_0 == 0U)
    {

#line 2344
        return float2(*(series_0+i_0)) ;
    }

#line 2345
    uint f_0 = (layout_0 >> 2U) + (layout_0 & 3U) * i_0;

#line 2345
    float2 _S2 = float2(*(series_0+(f_0 >> 1U))) ;

#line 2345
    float _S3;

    if((f_0 & 1U) != 0U)
    {

#line 2347
        _S3 = _S2.y;

#line 2347
    }
    else
    {

#line 2347
        _S3 = _S2.x;

#line 2347
    }

#line 2347
    return float2(_S3, 0.0f);
}


#line 610
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 612
    float2 t1_0 = *a_0 - *c_0;

#line 612
    float2 t2_0 = *b_0 + *d_0;

#line 612
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 614
    *b_0 = t1_0 + j3_0;

#line 614
    *c_0 = t0_0 - t2_0;

#line 614
    *d_0 = t1_0 - j3_0;
    return;
}


#line 323
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 323
    float _S4 = a_1.x;

#line 323
    float _S5 = b_1.x;

#line 323
    float _S6 = a_1.y;

#line 323
    float _S7 = b_1.y;

#line 323
    return float2(_S4 * _S5 - _S6 * _S7, _S4 * _S7 + _S6 * _S5);
}


#line 646
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 653
    uint n1_0 = 0U;
    for(;;)
    {

#line 654
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 654
            break;
        }

#line 654
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 654
        n1_0 = n1_0 + 1U;

#line 654
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 655
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 655
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 656
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 656
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 657
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 657
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 657
    uint k2_0 = 0U;
    for(;;)
    {

#line 658
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 658
            break;
        }

#line 658
        uint _S8 = 4U * k2_0;

#line 658
        r4_0(&(*r_0)[_S8], &(*r_0)[_S8 + 1U], &(*r_0)[_S8 + 2U], &(*r_0)[_S8 + 3U]);

#line 658
        k2_0 = k2_0 + 1U;

#line 658
    }

    float2 t_0 = (*r_0)[int(1)];

#line 660
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 660
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 661
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 661
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 662
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 662
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 663
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 663
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 664
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 664
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 665
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 665
    (*r_0)[int(14)] = t_5;
    return;
}


#line 646
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_1 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_1 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_1 = float2(0.0f, 1.0f);
    float2 W6_1 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_1 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 653
    uint n1_1 = 0U;
    for(;;)
    {

#line 654
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 654
            break;
        }

#line 654
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 654
        n1_1 = n1_1 + 1U;

#line 654
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 655
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 655
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 656
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 656
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 657
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 657
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 657
    uint k2_1 = 0U;
    for(;;)
    {

#line 658
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 658
            break;
        }

#line 658
        uint _S9 = 4U * k2_1;

#line 658
        r4_0(&(*r_1)[_S9], &(*r_1)[_S9 + 1U], &(*r_1)[_S9 + 2U], &(*r_1)[_S9 + 3U]);

#line 658
        k2_1 = k2_1 + 1U;

#line 658
    }

    float2 t_6 = (*r_1)[int(1)];

#line 660
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 660
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 661
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 661
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 662
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 662
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 663
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 663
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 664
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 664
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 665
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 665
    (*r_1)[int(14)] = t_11;
    return;
}


#line 103 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 325 "forward.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S10 = max(TB_0, 1U);

#line 327
    uint j_0 = d_1 / _S10;

#line 327
    uint m_0 = d_1 % _S10;

#line 327
    uint _S11;
    if(TB_0 <= 16U)
    {

#line 328
        _S11 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 328
    }
    else
    {

#line 328
        _S11 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 328
    }

#line 328
    return _S11;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint seriesLength_0;
    uint seriesLayout_0;
};


#line 312 "forward.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_spectra_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(512)> threadgroup* stg_0;
};


#line 312
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 312
    uint _S12 = 2U * i_1;

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S12] = (as_type<uint>((v_0.x)));

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S12 + 1U] = (as_type<uint>((v_0.y)));

#line 312
    return;
}


#line 313
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 313
    uint _S13 = 2U * i_2;

#line 313
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S13]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S13 + 1U]))));
}


#line 749
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 756
    dft16_1(r_2);

#line 761
    return;
}


#line 877
uint lgOf_0(uint i_3)
{

#line 877
    uint _S14;

#line 877
    if(i_3 < 1U)
    {

#line 877
        _S14 = 4U;

#line 877
    }
    else
    {

#line 877
        if(i_3 == 1U)
        {

#line 877
            _S14 = 4U;

#line 877
        }
        else
        {

#line 877
            _S14 = 1U;

#line 877
        }

#line 877
    }

#line 877
    return _S14;
}


#line 879
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 883
    uint lg_1 = lgOf_0(0U);

#line 888
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 2355
[[kernel]] void seriesForward(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]])
{

#line 2355
    uint j_1;

#line 2355
    thread KernelContext_0 kernelContext_2;

#line 2355
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2355
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2355
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2355
    (&kernelContext_2)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 2355
    threadgroup array<uint, int(512)> stg_1;

#line 2355
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2361
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S15 = gid_0.x;

#line 2364
    uint _S16 = entryPointParams_starts_1[_S15];
    thread array<float2, int(16)> r_3;

#line 2365
    uint k_0 = 0U;
    for(;;)
    {

#line 2366
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2366
            break;
        }

#line 2367
        uint offset_0 = tid_0 + 16U * k_0;
        float2 _S17 = float2(0.0f, 0.0f);

#line 2368
        bool _S18;

        if(_S16 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2370
            _S18 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S16);

#line 2370
        }
        else
        {

#line 2370
            _S18 = false;

#line 2370
        }

#line 2370
        float2 x_0;

#line 2370
        if(_S18)
        {

#line 2370
            x_0 = seriesSample_0((&kernelContext_2)->entryPointParams_series_0, _S16 + offset_0, (&kernelContext_2)->entryPointParams_0->seriesLayout_0);

#line 2370
        }
        else
        {

#line 2370
            x_0 = _S17;

#line 2370
        }

        r_3[k_0] = float2(x_0.x / 256.0f, - x_0.y / 256.0f);

#line 2366
        k_0 = k_0 + 1U;

#line 2366
    }

#line 2374
    for(;;)
    {

#line 2374
        for(;;)
        {

#line 2374
            for(;;)
            {

#line 2374
                for(;;)
                {

#line 2374
                    uint lgTB_0 = firstbithigh_0(16U);

#line 2374
                    uint lgLn_0 = firstbithigh_0(256U);

#line 2374
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2374
                    uint lane_1 = tid_0 & 15U;

#line 2374
                    dft16_0(&r_3);

#line 2374
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 256.0f);

#line 2374
                    float _S19 = tw_0.x;

#line 2374
                    float _S20 = tw_0.y;

#line 2374
                    uint k2_2 = 0U;

#line 2374
                    float cr_0 = 1.0f;

#line 2374
                    float ci_0 = 0.0f;

#line 2374
                    for(;;)
                    {

#line 2374
                        if(k2_2 < 16U)
                        {
                        }
                        else
                        {

#line 2374
                            break;
                        }

#line 2374
                        r_3[k2_2] = cmul_0(r_3[k2_2], float2(cr_0, ci_0));

#line 2374
                        float nr_0 = cr_0 * _S19 - ci_0 * _S20;

#line 2374
                        float _S21 = cr_0 * _S20 + ci_0 * _S19;

#line 2374
                        k2_2 = k2_2 + 1U;

#line 2374
                        cr_0 = nr_0;

#line 2374
                        ci_0 = _S21;

#line 2374
                    }

#line 2374
                    uint per_1 = 16U / max(16U, 1U);

#line 2374
                    uint _S22 = max(1U, 1U);

#line 2374
                    uint blk2_1 = tid_0 / _S22;

#line 2374
                    uint lane2_1 = tid_0 % _S22;

#line 2374
                    for(;;)
                    {

#line 2374
                        thread array<float2, int(16)> out_0;

#line 2374
                        uint z_0 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2374
                            z_0 = z_0 + 1U;

#line 2374
                        }

#line 2374
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2374
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2374
                        uint p0_0 = computeWant_0(0U, 16U, 256U, blk_1, lane_1, per_1, _S22, 16U, blk2_1, lane2_1);

#line 2374
                        uint _S23 = p0_0 & lenMask_0;

#line 2374
                        uint _S24 = (_S23 >> lgTB_0) * 16U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S23 & spanMask_0);

#line 2374
                        uint c_1 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(c_1 < 1U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2374
                            j_1 = 0U;

#line 2374
                            for(;;)
                            {

#line 2374
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 2374
                                    break;
                                }

#line 2374
                                stgPut_0(j_1 * 16U + (&kernelContext_2)->_tid_0, r_3[c_1 * 16U + j_1], &kernelContext_2);

#line 2374
                                j_1 = j_1 + 1U;

#line 2374
                            }

#line 2374
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2374
                            uint d_2 = 0U;

#line 2374
                            for(;;)
                            {

#line 2374
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2374
                                    break;
                                }

#line 2374
                                uint pz_0 = computeWant_0(d_2, 16U, 256U, 0U, 0U, per_1, _S22, 16U, 0U, 0U);

#line 2374
                                uint _S25 = pz_0 & lenMask_0;

#line 2374
                                uint az_0 = (_S25 >> lgTB_0) * 16U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S25 & spanMask_0);

#line 2374
                                float2 _S26 = stgGet_0(_S24 + az_0 - c_1 * 16U * 16U, &kernelContext_2);

#line 2374
                                out_0[d_2] = _S26;

#line 2374
                                d_2 = d_2 + 1U;

#line 2374
                            }

#line 2374
                            c_1 = c_1 + 1U;

#line 2374
                        }

#line 2374
                        j_1 = 0U;

#line 2374
                        for(;;)
                        {

#line 2374
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2374
                                break;
                            }

#line 2374
                            r_3[j_1] = out_0[j_1];

#line 2374
                            j_1 = j_1 + 1U;

#line 2374
                        }

#line 2374
                        break;
                    }

#line 2374
                    break;
                }

#line 2374
                break;
            }

#line 2374
            break;
        }

#line 2374
        innermost_0(&r_3);

#line 2374
        break;
    }

#line 2374
    k_0 = 0U;
    for(;;)
    {

#line 2375
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2375
            break;
        }

#line 2375
        *((&kernelContext_2)->entryPointParams_spectra_0+(_S15 * 256U + slotToIndex_0(tid_0 * 16U + k_0))) = packed_float2(float2(r_3[k_0].x, - r_3[k_0].y)) ;

#line 2375
        k_0 = k_0 + 1U;

#line 2375
    }



    return;
}
