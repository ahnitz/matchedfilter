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


#line 2341 "bands.slang"
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


#line 103 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 325 "bands.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S9 = max(TB_0, 1U);

#line 327
    uint j_0 = d_1 / _S9;

#line 327
    uint m_0 = d_1 % _S9;

#line 327
    uint _S10;
    if(TB_0 <= 16U)
    {

#line 328
        _S10 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 328
    }
    else
    {

#line 328
        _S10 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 328
    }

#line 328
    return _S10;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint seriesLength_0;
    uint B_0;
    uint k0_0;
    uint seriesLayout_0;
};


#line 312 "bands.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_bands_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(128)> threadgroup* stg_0;
};


#line 312
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 312
    uint _S11 = 2U * i_1;

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11] = (as_type<uint>((v_0.x)));

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11 + 1U] = (as_type<uint>((v_0.y)));

#line 312
    return;
}


#line 313
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 313
    uint _S12 = 2U * i_2;

#line 313
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12 + 1U]))));
}


#line 625
void dft4_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    r4_0(&(*r_1)[o_0], &(*r_1)[o_0 + 1U], &(*r_1)[o_0 + 2U], &(*r_1)[o_0 + 3U]);
    float2 t_6 = (*r_1)[o_0 + 1U];

#line 628
    (*r_1)[o_0 + 1U] = (*r_1)[o_0 + 2U];

#line 628
    (*r_1)[o_0 + 2U] = t_6;
    return;
}


#line 749
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 749
    uint b_2 = 0U;

#line 758
    for(;;)
    {

#line 758
        if(b_2 < 4U)
        {
        }
        else
        {

#line 758
            break;
        }

#line 758
        dft4_0(r_2, b_2 * 4U);

#line 758
        b_2 = b_2 + 1U;

#line 758
    }


    return;
}


#line 877
uint lgOf_0(uint i_3)
{

#line 877
    uint _S13;

#line 877
    if(i_3 < 1U)
    {

#line 877
        _S13 = 4U;

#line 877
    }
    else
    {

#line 877
        _S13 = 1U;

#line 877
    }

#line 877
    return _S13;
}


#line 879
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 883
    uint lg_1 = lgOf_0(1U);

#line 883
    uint lg_2 = lgOf_0(0U);

#line 888
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2395
[[kernel]] void seriesForwardBands(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_bands_1 [[buffer(3)]])
{

#line 2395
    bool _S14;

#line 2395
    float2 x_1;

#line 2395
    uint j_1;

#line 2395
    thread KernelContext_0 kernelContext_2;

#line 2395
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2395
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2395
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2395
    (&kernelContext_2)->entryPointParams_bands_0 = entryPointParams_bands_1;

#line 2395
    threadgroup array<uint, int(128)> stg_1;

#line 2395
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2401
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S15 = gid_0.x;

#line 2404
    uint _S16 = entryPointParams_starts_1[_S15];
    thread array<float2, int(16)> r_3;

#line 2405
    uint k_0 = 0U;
    for(;;)
    {

#line 2406
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2406
            break;
        }

#line 2407
        uint offset_0 = tid_0 + 4U * k_0;
        float2 _S17 = float2(0.0f, 0.0f);
        if(_S16 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2409
            _S14 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S16);

#line 2409
        }
        else
        {

#line 2409
            _S14 = false;

#line 2409
        }

#line 2409
        if(_S14)
        {

#line 2409
            x_1 = seriesSample_0((&kernelContext_2)->entryPointParams_series_0, _S16 + offset_0, (&kernelContext_2)->entryPointParams_0->seriesLayout_0);

#line 2409
        }
        else
        {

#line 2409
            x_1 = _S17;

#line 2409
        }

        r_3[k_0] = float2(x_1.x / 64.0f, - x_1.y / 64.0f);

#line 2406
        k_0 = k_0 + 1U;

#line 2406
    }

#line 2413
    for(;;)
    {

#line 2413
        for(;;)
        {

#line 2413
            for(;;)
            {

#line 2413
                for(;;)
                {

#line 2413
                    uint lgTB_0 = firstbithigh_0(4U);

#line 2413
                    uint lgLn_0 = firstbithigh_0(64U);

#line 2413
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2413
                    uint lane_1 = tid_0 & 3U;

#line 2413
                    dft16_0(&r_3);

#line 2413
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 64.0f);

#line 2413
                    float _S18 = tw_0.x;

#line 2413
                    float _S19 = tw_0.y;

#line 2413
                    uint k2_1 = 0U;

#line 2413
                    float cr_0 = 1.0f;

#line 2413
                    float ci_0 = 0.0f;

#line 2413
                    for(;;)
                    {

#line 2413
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2413
                            break;
                        }

#line 2413
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2413
                        float nr_0 = cr_0 * _S18 - ci_0 * _S19;

#line 2413
                        float _S20 = cr_0 * _S19 + ci_0 * _S18;

#line 2413
                        k2_1 = k2_1 + 1U;

#line 2413
                        cr_0 = nr_0;

#line 2413
                        ci_0 = _S20;

#line 2413
                    }

#line 2413
                    uint per_1 = 16U / max(4U, 1U);

#line 2413
                    uint _S21 = max(0U, 1U);

#line 2413
                    uint blk2_1 = tid_0 / _S21;

#line 2413
                    uint lane2_1 = tid_0 % _S21;

#line 2413
                    for(;;)
                    {

#line 2413
                        thread array<float2, int(16)> out_0;

#line 2413
                        uint z_0 = 0U;

#line 2413
                        for(;;)
                        {

#line 2413
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2413
                                break;
                            }

#line 2413
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2413
                            z_0 = z_0 + 1U;

#line 2413
                        }

#line 2413
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2413
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2413
                        uint p0_0 = computeWant_0(0U, 4U, 64U, blk_1, lane_1, per_1, _S21, 4U, blk2_1, lane2_1);

#line 2413
                        uint _S22 = p0_0 & lenMask_0;

#line 2413
                        uint _S23 = (_S22 >> lgTB_0) * 4U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S22 & spanMask_0);

#line 2413
                        uint c_1 = 0U;

#line 2413
                        for(;;)
                        {

#line 2413
                            if(c_1 < 1U)
                            {
                            }
                            else
                            {

#line 2413
                                break;
                            }

#line 2413
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2413
                            j_1 = 0U;

#line 2413
                            for(;;)
                            {

#line 2413
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 2413
                                    break;
                                }

#line 2413
                                stgPut_0(j_1 * 4U + (&kernelContext_2)->_tid_0, r_3[c_1 * 16U + j_1], &kernelContext_2);

#line 2413
                                j_1 = j_1 + 1U;

#line 2413
                            }

#line 2413
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2413
                            uint d_2 = 0U;

#line 2413
                            for(;;)
                            {

#line 2413
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2413
                                    break;
                                }

#line 2413
                                uint pz_0 = computeWant_0(d_2, 4U, 64U, 0U, 0U, per_1, _S21, 4U, 0U, 0U);

#line 2413
                                uint _S24 = pz_0 & lenMask_0;

#line 2413
                                uint az_0 = (_S24 >> lgTB_0) * 4U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S24 & spanMask_0);

#line 2413
                                float2 _S25 = stgGet_0(_S23 + az_0 - c_1 * 16U * 4U, &kernelContext_2);

#line 2413
                                out_0[d_2] = _S25;

#line 2413
                                d_2 = d_2 + 1U;

#line 2413
                            }

#line 2413
                            c_1 = c_1 + 1U;

#line 2413
                        }

#line 2413
                        j_1 = 0U;

#line 2413
                        for(;;)
                        {

#line 2413
                            if(j_1 < 16U)
                            {
                            }
                            else
                            {

#line 2413
                                break;
                            }

#line 2413
                            r_3[j_1] = out_0[j_1];

#line 2413
                            j_1 = j_1 + 1U;

#line 2413
                        }

#line 2413
                        break;
                    }

#line 2413
                    break;
                }

#line 2413
                break;
            }

#line 2413
            break;
        }

#line 2413
        innermost_0(&r_3);

#line 2413
        break;
    }

#line 2413
    k_0 = 0U;
    for(;;)
    {

#line 2414
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2414
            break;
        }

#line 2415
        uint index_0 = slotToIndex_0(tid_0 * 16U + k_0);
        if(((&kernelContext_2)->entryPointParams_0->k0_0) == 0U)
        {

#line 2417
            if(index_0 < ((&kernelContext_2)->entryPointParams_0->B_0))
            {

#line 2417
                *((&kernelContext_2)->entryPointParams_bands_0+(_S15 * (&kernelContext_2)->entryPointParams_0->B_0 + index_0)) = packed_float2(float2(r_3[k_0].x, - r_3[k_0].y)) ;

#line 2417
            }

#line 2416
        }
        else
        {
            if(index_0 >= ((&kernelContext_2)->entryPointParams_0->k0_0))
            {

#line 2419
                _S14 = index_0 < ((&kernelContext_2)->entryPointParams_0->k0_0 + (&kernelContext_2)->entryPointParams_0->B_0);

#line 2419
            }
            else
            {

#line 2419
                _S14 = false;

#line 2419
            }

#line 2419
            if(_S14)
            {

#line 2419
                packed_float2 device* _S26 = (&kernelContext_2)->entryPointParams_bands_0+(_S15 * (&kernelContext_2)->entryPointParams_0->B_0 + (index_0 & ((&kernelContext_2)->entryPointParams_0->B_0 - 1U)));

                if(index_0 < 32U)
                {

#line 2421
                    x_1 = float2(r_3[k_0].x, - r_3[k_0].y);

#line 2421
                }
                else
                {

#line 2421
                    x_1 = float2(0.0f, 0.0f);

#line 2421
                }

#line 2421
                *_S26 = packed_float2(x_1) ;

#line 2419
            }

#line 2416
        }

#line 2414
        k_0 = k_0 + 1U;

#line 2414
    }

#line 2424
    return;
}
