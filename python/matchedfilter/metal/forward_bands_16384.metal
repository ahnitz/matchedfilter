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


#line 2186 "bands.slang"
float2 seriesSample_0(packed_float2 device* series_0, uint i_0, uint layout_0)
{
    if(layout_0 == 0U)
    {

#line 2189
        return float2(*(series_0+i_0)) ;
    }

#line 2190
    uint f_0 = (layout_0 >> 2U) + (layout_0 & 3U) * i_0;

#line 2190
    float2 _S2 = float2(*(series_0+(f_0 >> 1U))) ;

#line 2190
    float _S3;

    if((f_0 & 1U) != 0U)
    {

#line 2192
        _S3 = _S2.y;

#line 2192
    }
    else
    {

#line 2192
        _S3 = _S2.x;

#line 2192
    }

#line 2192
    return float2(_S3, 0.0f);
}


#line 577
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 579
    float2 t1_0 = *a_0 - *c_0;

#line 579
    float2 t2_0 = *b_0 + *d_0;

#line 579
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 581
    *b_0 = t1_0 + j3_0;

#line 581
    *c_0 = t0_0 - t2_0;

#line 581
    *d_0 = t1_0 - j3_0;
    return;
}


#line 317
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 317
    float _S4 = a_1.x;

#line 317
    float _S5 = b_1.x;

#line 317
    float _S6 = a_1.y;

#line 317
    float _S7 = b_1.y;

#line 317
    return float2(_S4 * _S5 - _S6 * _S7, _S4 * _S7 + _S6 * _S5);
}


#line 613
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 620
    uint n1_0 = 0U;
    for(;;)
    {

#line 621
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 621
            break;
        }

#line 621
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 621
        n1_0 = n1_0 + 1U;

#line 621
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 622
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 622
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 623
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 623
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 624
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 624
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 624
    uint k2_0 = 0U;
    for(;;)
    {

#line 625
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 625
            break;
        }

#line 625
        uint _S8 = 4U * k2_0;

#line 625
        r4_0(&(*r_0)[_S8], &(*r_0)[_S8 + 1U], &(*r_0)[_S8 + 2U], &(*r_0)[_S8 + 3U]);

#line 625
        k2_0 = k2_0 + 1U;

#line 625
    }

    float2 t_0 = (*r_0)[int(1)];

#line 627
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 627
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 628
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 628
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 629
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 629
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 630
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 630
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 631
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 631
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 632
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 632
    (*r_0)[int(14)] = t_5;
    return;
}


#line 101 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 319 "bands.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S9 = max(TB_0, 1U);

#line 321
    uint j_0 = d_1 / _S9;

#line 321
    uint m_0 = d_1 % _S9;

#line 321
    uint _S10;
    if(TB_0 <= 16U)
    {

#line 322
        _S10 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 322
    }
    else
    {

#line 322
        _S10 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 322
    }

#line 322
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


#line 306 "bands.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_bands_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 306
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 306
    uint _S11 = 2U * i_1;

#line 306
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11] = (as_type<uint>((v_0.x)));

#line 306
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S11 + 1U] = (as_type<uint>((v_0.y)));

#line 306
    return;
}


#line 307
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 307
    uint _S12 = 2U * i_2;

#line 307
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S12 + 1U]))));
}


#line 592
void dft4_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    r4_0(&(*r_1)[o_0], &(*r_1)[o_0 + 1U], &(*r_1)[o_0 + 2U], &(*r_1)[o_0 + 3U]);
    float2 t_6 = (*r_1)[o_0 + 1U];

#line 595
    (*r_1)[o_0 + 1U] = (*r_1)[o_0 + 2U];

#line 595
    (*r_1)[o_0 + 2U] = t_6;
    return;
}


#line 716
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 716
    uint b_2 = 0U;

#line 725
    for(;;)
    {

#line 725
        if(b_2 < 4U)
        {
        }
        else
        {

#line 725
            break;
        }

#line 725
        dft4_0(r_2, b_2 * 4U);

#line 725
        b_2 = b_2 + 1U;

#line 725
    }


    return;
}


#line 863
uint lgOf_0(uint i_3)
{

#line 863
    uint _S13;

#line 863
    if(i_3 < 3U)
    {

#line 863
        _S13 = 4U;

#line 863
    }
    else
    {

#line 863
        _S13 = 1U;

#line 863
    }

#line 863
    return _S13;
}


#line 865
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(4U);

    uint x_0 = slot_0 >> lg_0;

#line 869
    uint lg_1 = lgOf_0(3U);

    uint x_1 = x_0 >> lg_1;

#line 869
    uint lg_2 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_2;

#line 869
    uint lg_3 = lgOf_0(1U);

#line 869
    uint lg_4 = lgOf_0(0U);

#line 874
    return (((((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | (x_2 & ((1U << lg_3) - 1U))) << lg_4) | ((x_2 >> lg_3) & ((1U << lg_4) - 1U));
}


#line 2240
[[kernel]] void seriesForwardBands(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_bands_1 [[buffer(3)]])
{

#line 2240
    bool _S14;

#line 2240
    float2 x_3;

#line 2240
    uint _S15;

#line 2240
    uint k2_1;

#line 2240
    float cr_0;

#line 2240
    float ci_0;

#line 2240
    uint _S16;

#line 2240
    uint z_0;

#line 2240
    uint _S17;

#line 2240
    uint c_1;

#line 2240
    uint d_2;

#line 2240
    uint j_1;

#line 2240
    uint _S18;

#line 2240
    uint _S19;

#line 2240
    uint _S20;

#line 2240
    thread KernelContext_0 kernelContext_2;

#line 2240
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2240
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2240
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2240
    (&kernelContext_2)->entryPointParams_bands_0 = entryPointParams_bands_1;

#line 2240
    threadgroup array<uint, int(8192)> stg_1;

#line 2240
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2246
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S21 = gid_0.x;

#line 2249
    uint _S22 = entryPointParams_starts_1[_S21];
    thread array<float2, int(16)> r_3;

#line 2250
    uint k_0 = 0U;
    for(;;)
    {

#line 2251
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2251
            break;
        }

#line 2252
        uint offset_0 = tid_0 + 1024U * k_0;
        float2 _S23 = float2(0.0f, 0.0f);
        if(_S22 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2254
            _S14 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S22);

#line 2254
        }
        else
        {

#line 2254
            _S14 = false;

#line 2254
        }

#line 2254
        if(_S14)
        {

#line 2254
            x_3 = seriesSample_0((&kernelContext_2)->entryPointParams_series_0, _S22 + offset_0, (&kernelContext_2)->entryPointParams_0->seriesLayout_0);

#line 2254
        }
        else
        {

#line 2254
            x_3 = _S23;

#line 2254
        }

        r_3[k_0] = float2(x_3.x / 16384.0f, - x_3.y / 16384.0f);

#line 2251
        k_0 = k_0 + 1U;

#line 2251
    }

#line 2258
    for(;;)
    {

#line 2258
        for(;;)
        {

#line 2258
            for(;;)
            {

#line 2258
                for(;;)
                {

#line 2258
                    uint lgTB_0 = firstbithigh_0(1024U);

#line 2258
                    _S15 = lgTB_0;

#line 2258
                    uint lgLn_0 = firstbithigh_0(16384U);

#line 2258
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2258
                    uint lane_1 = tid_0 & 1023U;

#line 2258
                    dft16_0(&r_3);

#line 2258
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 16384.0f);

#line 2258
                    float _S24 = tw_0.x;

#line 2258
                    float _S25 = tw_0.y;

#line 2258
                    k2_1 = 0U;

#line 2258
                    cr_0 = 1.0f;

#line 2258
                    ci_0 = 0.0f;

#line 2258
                    for(;;)
                    {

#line 2258
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2258
                            break;
                        }

#line 2258
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2258
                        float nr_0 = cr_0 * _S24 - ci_0 * _S25;

#line 2258
                        float _S26 = cr_0 * _S25 + ci_0 * _S24;

#line 2258
                        k2_1 = k2_1 + 1U;

#line 2258
                        cr_0 = nr_0;

#line 2258
                        ci_0 = _S26;

#line 2258
                    }

#line 2258
                    uint per_1 = 16U / max(1024U, 1U);

#line 2258
                    uint _S27 = max(64U, 1U);

#line 2258
                    _S16 = _S27;

#line 2258
                    uint blk2_1 = tid_0 / _S27;

#line 2258
                    uint lane2_1 = tid_0 % _S27;

#line 2258
                    for(;;)
                    {

#line 2258
                        thread array<float2, int(16)> out_0;

#line 2258
                        z_0 = 0U;

#line 2258
                        for(;;)
                        {

#line 2258
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2258
                                break;
                            }

#line 2258
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2258
                            z_0 = z_0 + 1U;

#line 2258
                        }

#line 2258
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2258
                        _S17 = spanMask_0;

#line 2258
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2258
                        uint p0_0 = computeWant_0(0U, 1024U, 16384U, blk_1, lane_1, per_1, _S27, 1024U, blk2_1, lane2_1);

#line 2258
                        uint _S28 = p0_0 & lenMask_0;

#line 2258
                        uint _S29 = _S28 >> lgTB_0;

#line 2258
                        uint _S30 = _S29 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S28 & spanMask_0);

#line 2258
                        c_1 = 0U;

#line 2258
                        for(;;)
                        {

#line 2258
                            if(c_1 < 4U)
                            {
                            }
                            else
                            {

#line 2258
                                break;
                            }

#line 2258
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2258
                            j_1 = 0U;

#line 2258
                            for(;;)
                            {

#line 2258
                                if(j_1 < 4U)
                                {
                                }
                                else
                                {

#line 2258
                                    break;
                                }

#line 2258
                                stgPut_0(j_1 * 1024U + (&kernelContext_2)->_tid_0, r_3[c_1 * 4U + j_1], &kernelContext_2);

#line 2258
                                j_1 = j_1 + 1U;

#line 2258
                            }

#line 2258
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2258
                            d_2 = 0U;

#line 2258
                            for(;;)
                            {

#line 2258
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2258
                                    break;
                                }

#line 2258
                                uint pz_0 = computeWant_0(d_2, 1024U, 16384U, 0U, 0U, per_1, _S27, 1024U, 0U, 0U);

#line 2258
                                uint _S31 = pz_0 & lenMask_0;

#line 2258
                                uint iz_0 = _S31 >> lgTB_0;

#line 2258
                                uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S31 & spanMask_0);

#line 2258
                                uint i_4 = _S29 + iz_0;

#line 2258
                                uint _S32 = c_1 * 4U;

#line 2258
                                if(i_4 >= _S32)
                                {

#line 2258
                                    _S14 = i_4 < ((c_1 + 1U) * 4U);

#line 2258
                                }
                                else
                                {

#line 2258
                                    _S14 = false;

#line 2258
                                }

#line 2258
                                if(_S14)
                                {

#line 2258
                                    float2 _S33 = stgGet_0(_S30 + az_0 - _S32 * 1024U, &kernelContext_2);

#line 2258
                                    out_0[d_2] = _S33;

#line 2258
                                }

#line 2258
                                d_2 = d_2 + 1U;

#line 2258
                            }

#line 2258
                            c_1 = c_1 + 1U;

#line 2258
                        }

#line 2258
                        d_2 = 0U;

#line 2258
                        for(;;)
                        {

#line 2258
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2258
                                break;
                            }

#line 2258
                            r_3[d_2] = out_0[d_2];

#line 2258
                            d_2 = d_2 + 1U;

#line 2258
                        }

#line 2258
                        break;
                    }

#line 2258
                    break;
                }

#line 2258
                break;
            }

#line 2258
            for(;;)
            {

#line 2258
                for(;;)
                {

#line 2258
                    uint lgTB_1 = firstbithigh_0(64U);

#line 2258
                    _S18 = lgTB_1;

#line 2258
                    uint blk_2 = tid_0 >> lgTB_1;

#line 2258
                    uint lane_2 = tid_0 & 63U;

#line 2258
                    dft16_0(&r_3);

#line 2258
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 2258
                    float _S34 = tw_1.x;

#line 2258
                    float _S35 = tw_1.y;

#line 2258
                    k2_1 = 0U;

#line 2258
                    cr_0 = 1.0f;

#line 2258
                    ci_0 = 0.0f;

#line 2258
                    for(;;)
                    {

#line 2258
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2258
                            break;
                        }

#line 2258
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2258
                        float nr_1 = cr_0 * _S34 - ci_0 * _S35;

#line 2258
                        float _S36 = cr_0 * _S35 + ci_0 * _S34;

#line 2258
                        k2_1 = k2_1 + 1U;

#line 2258
                        cr_0 = nr_1;

#line 2258
                        ci_0 = _S36;

#line 2258
                    }

#line 2258
                    uint per_2 = 16U / _S16;

#line 2258
                    uint _S37 = max(4U, 1U);

#line 2258
                    _S19 = _S37;

#line 2258
                    uint blk2_2 = tid_0 / _S37;

#line 2258
                    uint lane2_2 = tid_0 % _S37;

#line 2258
                    for(;;)
                    {

#line 2258
                        thread array<float2, int(16)> out_1;

#line 2258
                        z_0 = 0U;

#line 2258
                        for(;;)
                        {

#line 2258
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2258
                                break;
                            }

#line 2258
                            out_1[z_0] = float2(0.0f, 0.0f);

#line 2258
                            z_0 = z_0 + 1U;

#line 2258
                        }

#line 2258
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2258
                        _S20 = spanMask_1;

#line 2258
                        uint p0_1 = computeWant_0(0U, 64U, 1024U, blk_2, lane_2, per_2, _S37, 64U, blk2_2, lane2_2);

#line 2258
                        uint _S38 = p0_1 & _S17;

#line 2258
                        uint _S39 = _S38 >> lgTB_1;

#line 2258
                        uint _S40 = _S39 * 1024U + ((p0_1 >> _S15) << lgTB_1) + (_S38 & spanMask_1);

#line 2258
                        c_1 = 0U;

#line 2258
                        for(;;)
                        {

#line 2258
                            if(c_1 < 4U)
                            {
                            }
                            else
                            {

#line 2258
                                break;
                            }

#line 2258
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2258
                            j_1 = 0U;

#line 2258
                            for(;;)
                            {

#line 2258
                                if(j_1 < 4U)
                                {
                                }
                                else
                                {

#line 2258
                                    break;
                                }

#line 2258
                                stgPut_0(j_1 * 1024U + (&kernelContext_2)->_tid_0, r_3[c_1 * 4U + j_1], &kernelContext_2);

#line 2258
                                j_1 = j_1 + 1U;

#line 2258
                            }

#line 2258
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2258
                            d_2 = 0U;

#line 2258
                            for(;;)
                            {

#line 2258
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2258
                                    break;
                                }

#line 2258
                                uint pz_1 = computeWant_0(d_2, 64U, 1024U, 0U, 0U, per_2, _S37, 64U, 0U, 0U);

#line 2258
                                uint _S41 = pz_1 & _S17;

#line 2258
                                uint iz_1 = _S41 >> lgTB_1;

#line 2258
                                uint az_1 = iz_1 * 1024U + ((pz_1 >> _S15) << lgTB_1) + (_S41 & spanMask_1);

#line 2258
                                uint i_5 = _S39 + iz_1;

#line 2258
                                uint _S42 = c_1 * 4U;

#line 2258
                                if(i_5 >= _S42)
                                {

#line 2258
                                    _S14 = i_5 < ((c_1 + 1U) * 4U);

#line 2258
                                }
                                else
                                {

#line 2258
                                    _S14 = false;

#line 2258
                                }

#line 2258
                                if(_S14)
                                {

#line 2258
                                    float2 _S43 = stgGet_0(_S40 + az_1 - _S42 * 1024U, &kernelContext_2);

#line 2258
                                    out_1[d_2] = _S43;

#line 2258
                                }

#line 2258
                                d_2 = d_2 + 1U;

#line 2258
                            }

#line 2258
                            c_1 = c_1 + 1U;

#line 2258
                        }

#line 2258
                        d_2 = 0U;

#line 2258
                        for(;;)
                        {

#line 2258
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2258
                                break;
                            }

#line 2258
                            r_3[d_2] = out_1[d_2];

#line 2258
                            d_2 = d_2 + 1U;

#line 2258
                        }

#line 2258
                        break;
                    }

#line 2258
                    break;
                }

#line 2258
                break;
            }

#line 2258
            for(;;)
            {

#line 2258
                for(;;)
                {

#line 2258
                    uint lgTB_2 = firstbithigh_0(4U);

#line 2258
                    uint blk_3 = tid_0 >> lgTB_2;

#line 2258
                    uint lane_3 = tid_0 & 3U;

#line 2258
                    dft16_0(&r_3);

#line 2258
                    float2 tw_2 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 64.0f);

#line 2258
                    float _S44 = tw_2.x;

#line 2258
                    float _S45 = tw_2.y;

#line 2258
                    k2_1 = 0U;

#line 2258
                    cr_0 = 1.0f;

#line 2258
                    ci_0 = 0.0f;

#line 2258
                    for(;;)
                    {

#line 2258
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2258
                            break;
                        }

#line 2258
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2258
                        float nr_2 = cr_0 * _S44 - ci_0 * _S45;

#line 2258
                        float _S46 = cr_0 * _S45 + ci_0 * _S44;

#line 2258
                        k2_1 = k2_1 + 1U;

#line 2258
                        cr_0 = nr_2;

#line 2258
                        ci_0 = _S46;

#line 2258
                    }

#line 2258
                    uint per_3 = 16U / _S19;

#line 2258
                    uint _S47 = max(0U, 1U);

#line 2258
                    uint blk2_3 = tid_0 / _S47;

#line 2258
                    uint lane2_3 = tid_0 % _S47;

#line 2258
                    for(;;)
                    {

#line 2258
                        thread array<float2, int(16)> out_2;

#line 2258
                        z_0 = 0U;

#line 2258
                        for(;;)
                        {

#line 2258
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2258
                                break;
                            }

#line 2258
                            out_2[z_0] = float2(0.0f, 0.0f);

#line 2258
                            z_0 = z_0 + 1U;

#line 2258
                        }

#line 2258
                        uint spanMask_2 = (1U << lgTB_2) - 1U;

#line 2258
                        uint p0_2 = computeWant_0(0U, 4U, 64U, blk_3, lane_3, per_3, _S47, 4U, blk2_3, lane2_3);

#line 2258
                        uint _S48 = p0_2 & _S20;

#line 2258
                        uint _S49 = _S48 >> lgTB_2;

#line 2258
                        uint _S50 = _S49 * 1024U + ((p0_2 >> _S18) << lgTB_2) + (_S48 & spanMask_2);

#line 2258
                        c_1 = 0U;

#line 2258
                        for(;;)
                        {

#line 2258
                            if(c_1 < 4U)
                            {
                            }
                            else
                            {

#line 2258
                                break;
                            }

#line 2258
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2258
                            j_1 = 0U;

#line 2258
                            for(;;)
                            {

#line 2258
                                if(j_1 < 4U)
                                {
                                }
                                else
                                {

#line 2258
                                    break;
                                }

#line 2258
                                stgPut_0(j_1 * 1024U + (&kernelContext_2)->_tid_0, r_3[c_1 * 4U + j_1], &kernelContext_2);

#line 2258
                                j_1 = j_1 + 1U;

#line 2258
                            }

#line 2258
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2258
                            d_2 = 0U;

#line 2258
                            for(;;)
                            {

#line 2258
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2258
                                    break;
                                }

#line 2258
                                uint pz_2 = computeWant_0(d_2, 4U, 64U, 0U, 0U, per_3, _S47, 4U, 0U, 0U);

#line 2258
                                uint _S51 = pz_2 & _S20;

#line 2258
                                uint iz_2 = _S51 >> lgTB_2;

#line 2258
                                uint az_2 = iz_2 * 1024U + ((pz_2 >> _S18) << lgTB_2) + (_S51 & spanMask_2);

#line 2258
                                uint i_6 = _S49 + iz_2;

#line 2258
                                uint _S52 = c_1 * 4U;

#line 2258
                                if(i_6 >= _S52)
                                {

#line 2258
                                    _S14 = i_6 < ((c_1 + 1U) * 4U);

#line 2258
                                }
                                else
                                {

#line 2258
                                    _S14 = false;

#line 2258
                                }

#line 2258
                                if(_S14)
                                {

#line 2258
                                    float2 _S53 = stgGet_0(_S50 + az_2 - _S52 * 1024U, &kernelContext_2);

#line 2258
                                    out_2[d_2] = _S53;

#line 2258
                                }

#line 2258
                                d_2 = d_2 + 1U;

#line 2258
                            }

#line 2258
                            c_1 = c_1 + 1U;

#line 2258
                        }

#line 2258
                        d_2 = 0U;

#line 2258
                        for(;;)
                        {

#line 2258
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2258
                                break;
                            }

#line 2258
                            r_3[d_2] = out_2[d_2];

#line 2258
                            d_2 = d_2 + 1U;

#line 2258
                        }

#line 2258
                        break;
                    }

#line 2258
                    break;
                }

#line 2258
                break;
            }

#line 2258
            break;
        }

#line 2258
        innermost_0(&r_3);

#line 2258
        break;
    }

#line 2258
    k_0 = 0U;
    for(;;)
    {

#line 2259
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2259
            break;
        }

#line 2260
        uint index_0 = slotToIndex_0(tid_0 * 16U + k_0);
        if(((&kernelContext_2)->entryPointParams_0->k0_0) == 0U)
        {

#line 2262
            if(index_0 < ((&kernelContext_2)->entryPointParams_0->B_0))
            {

#line 2262
                *((&kernelContext_2)->entryPointParams_bands_0+(_S21 * (&kernelContext_2)->entryPointParams_0->B_0 + index_0)) = packed_float2(float2(r_3[k_0].x, - r_3[k_0].y)) ;

#line 2262
            }

#line 2261
        }
        else
        {
            if(index_0 >= ((&kernelContext_2)->entryPointParams_0->k0_0))
            {

#line 2264
                _S14 = index_0 < ((&kernelContext_2)->entryPointParams_0->k0_0 + (&kernelContext_2)->entryPointParams_0->B_0);

#line 2264
            }
            else
            {

#line 2264
                _S14 = false;

#line 2264
            }

#line 2264
            if(_S14)
            {

#line 2264
                packed_float2 device* _S54 = (&kernelContext_2)->entryPointParams_bands_0+(_S21 * (&kernelContext_2)->entryPointParams_0->B_0 + (index_0 & ((&kernelContext_2)->entryPointParams_0->B_0 - 1U)));

                if(index_0 < 8192U)
                {

#line 2266
                    x_3 = float2(r_3[k_0].x, - r_3[k_0].y);

#line 2266
                }
                else
                {

#line 2266
                    x_3 = float2(0.0f, 0.0f);

#line 2266
                }

#line 2266
                *_S54 = packed_float2(x_3) ;

#line 2264
            }

#line 2261
        }

#line 2259
        k_0 = k_0 + 1U;

#line 2259
    }

#line 2269
    return;
}
