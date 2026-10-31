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


#line 2186 "forward.slang"
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


#line 101 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 317 "forward.slang"
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


#line 679
void dft64_0(array<float2, int(64)> thread* r_1)
{

#line 679
    uint k_0;

#line 679
    uint j_0 = 0U;

    for(;;)
    {

#line 681
        if(j_0 < 16U)
        {
        }
        else
        {

#line 681
            break;
        }

#line 682
        r4_0(&(*r_1)[j_0], &(*r_1)[j_0 + 16U], &(*r_1)[j_0 + 32U], &(*r_1)[j_0 + 48U]);

#line 681
        j_0 = j_0 + 1U;

#line 681
    }

    thread array<float2, int(64)> o_0;

#line 683
    uint pp_0 = 0U;
    for(;;)
    {

#line 684
        if(pp_0 < 4U)
        {
        }
        else
        {

#line 684
            break;
        }

#line 685
        thread array<float2, int(16)> b_2;

#line 685
        j_0 = 0U;
        for(;;)
        {

#line 686
            if(j_0 < 16U)
            {
            }
            else
            {

#line 686
                break;
            }
            b_2[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f));

#line 686
            j_0 = j_0 + 1U;

#line 686
        }



        dft16_0(&b_2);

#line 690
        k_0 = 0U;
        for(;;)
        {

#line 691
            if(k_0 < 16U)
            {
            }
            else
            {

#line 691
                break;
            }

#line 691
            o_0[4U * k_0 + pp_0] = b_2[k_0];

#line 691
            k_0 = k_0 + 1U;

#line 691
        }

#line 684
        pp_0 = pp_0 + 1U;

#line 684
    }

#line 684
    k_0 = 0U;

#line 693
    for(;;)
    {

#line 693
        if(k_0 < 64U)
        {
        }
        else
        {

#line 693
            break;
        }

#line 693
        (*r_1)[k_0] = o_0[k_0];

#line 693
        k_0 = k_0 + 1U;

#line 693
    }
    return;
}


void dftR_0(array<float2, int(64)> thread* r_2)
{

#line 705
    dft64_0(r_2);

    return;
}


#line 319
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S9 = max(TB_0, 1U);

#line 321
    uint j_1 = d_1 / _S9;

#line 321
    uint m_0 = d_1 % _S9;

#line 321
    uint _S10;
    if(TB_0 <= 64U)
    {

#line 322
        _S10 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

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
    uint seriesLayout_0;
};


#line 306 "forward.slang"
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


#line 638
void dft16at_0(array<float2, int(64)> thread* r_3, uint o_1)
{



    thread array<float2, int(16)> b_3;

#line 643
    uint i_3 = 0U;
    for(;;)
    {

#line 644
        if(i_3 < 16U)
        {
        }
        else
        {

#line 644
            break;
        }

#line 644
        b_3[i_3] = (*r_3)[o_1 + i_3];

#line 644
        i_3 = i_3 + 1U;

#line 644
    }
    dft16_0(&b_3);

#line 645
    i_3 = 0U;
    for(;;)
    {

#line 646
        if(i_3 < 16U)
        {
        }
        else
        {

#line 646
            break;
        }

#line 646
        (*r_3)[o_1 + i_3] = b_3[i_3];

#line 646
        i_3 = i_3 + 1U;

#line 646
    }

    return;
}


#line 716
void innermost_0(array<float2, int(64)> thread* r_4)
{

#line 716
    uint b_4 = 0U;

#line 721
    for(;;)
    {

#line 721
        if(b_4 < 4U)
        {
        }
        else
        {

#line 721
            break;
        }

#line 721
        dft16at_0(r_4, b_4 * 16U);

#line 721
        b_4 = b_4 + 1U;

#line 721
    }

#line 728
    return;
}


#line 863
uint lgOf_0(uint i_4)
{

#line 863
    uint _S13;

#line 863
    if(i_4 < 2U)
    {

#line 863
        _S13 = 6U;

#line 863
    }
    else
    {

#line 863
        if(i_4 == 2U)
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
    }

#line 863
    return _S13;
}


#line 865
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 869
    uint lg_1 = lgOf_0(1U);

#line 869
    uint lg_2 = lgOf_0(0U);

#line 874
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2200
[[kernel]] void seriesForward(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]])
{

#line 2200
    bool _S14;

#line 2200
    uint _S15;

#line 2200
    uint k2_1;

#line 2200
    float cr_0;

#line 2200
    float ci_0;

#line 2200
    uint _S16;

#line 2200
    uint z_0;

#line 2200
    uint _S17;

#line 2200
    uint c_1;

#line 2200
    uint d_2;

#line 2200
    uint j_2;

#line 2200
    thread KernelContext_0 kernelContext_2;

#line 2200
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2200
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2200
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2200
    (&kernelContext_2)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 2200
    threadgroup array<uint, int(8192)> stg_1;

#line 2200
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2206
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S18 = gid_0.x;

#line 2209
    uint _S19 = entryPointParams_starts_1[_S18];
    thread array<float2, int(64)> r_5;

#line 2210
    uint k_1 = 0U;
    for(;;)
    {

#line 2211
        if(k_1 < 64U)
        {
        }
        else
        {

#line 2211
            break;
        }

#line 2212
        uint offset_0 = tid_0 + 1024U * k_1;
        float2 _S20 = float2(0.0f, 0.0f);

        if(_S19 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2215
            _S14 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S19);

#line 2215
        }
        else
        {

#line 2215
            _S14 = false;

#line 2215
        }

#line 2215
        float2 x_1;

#line 2215
        if(_S14)
        {

#line 2215
            x_1 = seriesSample_0((&kernelContext_2)->entryPointParams_series_0, _S19 + offset_0, (&kernelContext_2)->entryPointParams_0->seriesLayout_0);

#line 2215
        }
        else
        {

#line 2215
            x_1 = _S20;

#line 2215
        }

        r_5[k_1] = float2(x_1.x / 6.5536e+04f, - x_1.y / 6.5536e+04f);

#line 2211
        k_1 = k_1 + 1U;

#line 2211
    }

#line 2219
    for(;;)
    {

#line 2219
        for(;;)
        {

#line 2219
            for(;;)
            {

#line 2219
                for(;;)
                {

#line 2219
                    uint lgTB_0 = firstbithigh_0(1024U);

#line 2219
                    _S15 = lgTB_0;

#line 2219
                    uint lgLn_0 = firstbithigh_0(65536U);

#line 2219
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2219
                    uint lane_1 = tid_0 & 1023U;

#line 2219
                    dftR_0(&r_5);

#line 2219
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 6.5536e+04f);

#line 2219
                    float _S21 = tw_0.x;

#line 2219
                    float _S22 = tw_0.y;

#line 2219
                    k2_1 = 0U;

#line 2219
                    cr_0 = 1.0f;

#line 2219
                    ci_0 = 0.0f;

#line 2219
                    for(;;)
                    {

#line 2219
                        if(k2_1 < 64U)
                        {
                        }
                        else
                        {

#line 2219
                            break;
                        }

#line 2219
                        r_5[k2_1] = cmul_0(r_5[k2_1], float2(cr_0, ci_0));

#line 2219
                        float nr_0 = cr_0 * _S21 - ci_0 * _S22;

#line 2219
                        float _S23 = cr_0 * _S22 + ci_0 * _S21;

#line 2219
                        k2_1 = k2_1 + 1U;

#line 2219
                        cr_0 = nr_0;

#line 2219
                        ci_0 = _S23;

#line 2219
                    }

#line 2219
                    uint per_1 = 64U / max(1024U, 1U);

#line 2219
                    uint _S24 = max(16U, 1U);

#line 2219
                    _S16 = _S24;

#line 2219
                    uint blk2_1 = tid_0 / _S24;

#line 2219
                    uint lane2_1 = tid_0 % _S24;

#line 2219
                    for(;;)
                    {

#line 2219
                        thread array<float2, int(64)> out_0;

#line 2219
                        z_0 = 0U;

#line 2219
                        for(;;)
                        {

#line 2219
                            if(z_0 < 64U)
                            {
                            }
                            else
                            {

#line 2219
                                break;
                            }

#line 2219
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2219
                            z_0 = z_0 + 1U;

#line 2219
                        }

#line 2219
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2219
                        _S17 = spanMask_0;

#line 2219
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2219
                        uint p0_0 = computeWant_0(0U, 1024U, 65536U, blk_1, lane_1, per_1, _S24, 1024U, blk2_1, lane2_1);

#line 2219
                        uint _S25 = p0_0 & lenMask_0;

#line 2219
                        uint _S26 = _S25 >> lgTB_0;

#line 2219
                        uint _S27 = _S26 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S25 & spanMask_0);

#line 2219
                        c_1 = 0U;

#line 2219
                        for(;;)
                        {

#line 2219
                            if(c_1 < 16U)
                            {
                            }
                            else
                            {

#line 2219
                                break;
                            }

#line 2219
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2219
                            j_2 = 0U;

#line 2219
                            for(;;)
                            {

#line 2219
                                if(j_2 < 4U)
                                {
                                }
                                else
                                {

#line 2219
                                    break;
                                }

#line 2219
                                stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_5[c_1 * 4U + j_2], &kernelContext_2);

#line 2219
                                j_2 = j_2 + 1U;

#line 2219
                            }

#line 2219
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2219
                            d_2 = 0U;

#line 2219
                            for(;;)
                            {

#line 2219
                                if(d_2 < 64U)
                                {
                                }
                                else
                                {

#line 2219
                                    break;
                                }

#line 2219
                                uint pz_0 = computeWant_0(d_2, 1024U, 65536U, 0U, 0U, per_1, _S24, 1024U, 0U, 0U);

#line 2219
                                uint _S28 = pz_0 & lenMask_0;

#line 2219
                                uint iz_0 = _S28 >> lgTB_0;

#line 2219
                                uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S28 & spanMask_0);

#line 2219
                                uint i_5 = _S26 + iz_0;

#line 2219
                                uint _S29 = c_1 * 4U;

#line 2219
                                if(i_5 >= _S29)
                                {

#line 2219
                                    _S14 = i_5 < ((c_1 + 1U) * 4U);

#line 2219
                                }
                                else
                                {

#line 2219
                                    _S14 = false;

#line 2219
                                }

#line 2219
                                if(_S14)
                                {

#line 2219
                                    float2 _S30 = stgGet_0(_S27 + az_0 - _S29 * 1024U, &kernelContext_2);

#line 2219
                                    out_0[d_2] = _S30;

#line 2219
                                }

#line 2219
                                d_2 = d_2 + 1U;

#line 2219
                            }

#line 2219
                            c_1 = c_1 + 1U;

#line 2219
                        }

#line 2219
                        d_2 = 0U;

#line 2219
                        for(;;)
                        {

#line 2219
                            if(d_2 < 64U)
                            {
                            }
                            else
                            {

#line 2219
                                break;
                            }

#line 2219
                            r_5[d_2] = out_0[d_2];

#line 2219
                            d_2 = d_2 + 1U;

#line 2219
                        }

#line 2219
                        break;
                    }

#line 2219
                    break;
                }

#line 2219
                break;
            }

#line 2219
            for(;;)
            {

#line 2219
                for(;;)
                {

#line 2219
                    uint lgTB_1 = firstbithigh_0(16U);

#line 2219
                    uint blk_2 = tid_0 >> lgTB_1;

#line 2219
                    uint lane_2 = tid_0 & 15U;

#line 2219
                    dftR_0(&r_5);

#line 2219
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 2219
                    float _S31 = tw_1.x;

#line 2219
                    float _S32 = tw_1.y;

#line 2219
                    k2_1 = 0U;

#line 2219
                    cr_0 = 1.0f;

#line 2219
                    ci_0 = 0.0f;

#line 2219
                    for(;;)
                    {

#line 2219
                        if(k2_1 < 64U)
                        {
                        }
                        else
                        {

#line 2219
                            break;
                        }

#line 2219
                        r_5[k2_1] = cmul_0(r_5[k2_1], float2(cr_0, ci_0));

#line 2219
                        float nr_1 = cr_0 * _S31 - ci_0 * _S32;

#line 2219
                        float _S33 = cr_0 * _S32 + ci_0 * _S31;

#line 2219
                        k2_1 = k2_1 + 1U;

#line 2219
                        cr_0 = nr_1;

#line 2219
                        ci_0 = _S33;

#line 2219
                    }

#line 2219
                    uint per_2 = 64U / _S16;

#line 2219
                    uint _S34 = max(0U, 1U);

#line 2219
                    uint blk2_2 = tid_0 / _S34;

#line 2219
                    uint lane2_2 = tid_0 % _S34;

#line 2219
                    for(;;)
                    {

#line 2219
                        thread array<float2, int(64)> out_1;

#line 2219
                        z_0 = 0U;

#line 2219
                        for(;;)
                        {

#line 2219
                            if(z_0 < 64U)
                            {
                            }
                            else
                            {

#line 2219
                                break;
                            }

#line 2219
                            out_1[z_0] = float2(0.0f, 0.0f);

#line 2219
                            z_0 = z_0 + 1U;

#line 2219
                        }

#line 2219
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2219
                        uint p0_1 = computeWant_0(0U, 16U, 1024U, blk_2, lane_2, per_2, _S34, 16U, blk2_2, lane2_2);

#line 2219
                        uint _S35 = p0_1 & _S17;

#line 2219
                        uint _S36 = _S35 >> lgTB_1;

#line 2219
                        uint _S37 = _S36 * 1024U + ((p0_1 >> _S15) << lgTB_1) + (_S35 & spanMask_1);

#line 2219
                        c_1 = 0U;

#line 2219
                        for(;;)
                        {

#line 2219
                            if(c_1 < 16U)
                            {
                            }
                            else
                            {

#line 2219
                                break;
                            }

#line 2219
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2219
                            j_2 = 0U;

#line 2219
                            for(;;)
                            {

#line 2219
                                if(j_2 < 4U)
                                {
                                }
                                else
                                {

#line 2219
                                    break;
                                }

#line 2219
                                stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_5[c_1 * 4U + j_2], &kernelContext_2);

#line 2219
                                j_2 = j_2 + 1U;

#line 2219
                            }

#line 2219
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2219
                            d_2 = 0U;

#line 2219
                            for(;;)
                            {

#line 2219
                                if(d_2 < 64U)
                                {
                                }
                                else
                                {

#line 2219
                                    break;
                                }

#line 2219
                                uint pz_1 = computeWant_0(d_2, 16U, 1024U, 0U, 0U, per_2, _S34, 16U, 0U, 0U);

#line 2219
                                uint _S38 = pz_1 & _S17;

#line 2219
                                uint iz_1 = _S38 >> lgTB_1;

#line 2219
                                uint az_1 = iz_1 * 1024U + ((pz_1 >> _S15) << lgTB_1) + (_S38 & spanMask_1);

#line 2219
                                uint i_6 = _S36 + iz_1;

#line 2219
                                uint _S39 = c_1 * 4U;

#line 2219
                                if(i_6 >= _S39)
                                {

#line 2219
                                    _S14 = i_6 < ((c_1 + 1U) * 4U);

#line 2219
                                }
                                else
                                {

#line 2219
                                    _S14 = false;

#line 2219
                                }

#line 2219
                                if(_S14)
                                {

#line 2219
                                    float2 _S40 = stgGet_0(_S37 + az_1 - _S39 * 1024U, &kernelContext_2);

#line 2219
                                    out_1[d_2] = _S40;

#line 2219
                                }

#line 2219
                                d_2 = d_2 + 1U;

#line 2219
                            }

#line 2219
                            c_1 = c_1 + 1U;

#line 2219
                        }

#line 2219
                        d_2 = 0U;

#line 2219
                        for(;;)
                        {

#line 2219
                            if(d_2 < 64U)
                            {
                            }
                            else
                            {

#line 2219
                                break;
                            }

#line 2219
                            r_5[d_2] = out_1[d_2];

#line 2219
                            d_2 = d_2 + 1U;

#line 2219
                        }

#line 2219
                        break;
                    }

#line 2219
                    break;
                }

#line 2219
                break;
            }

#line 2219
            break;
        }

#line 2219
        innermost_0(&r_5);

#line 2219
        break;
    }

#line 2219
    k_1 = 0U;
    for(;;)
    {

#line 2220
        if(k_1 < 64U)
        {
        }
        else
        {

#line 2220
            break;
        }

#line 2220
        *((&kernelContext_2)->entryPointParams_spectra_0+(_S18 * 65536U + slotToIndex_0(tid_0 * 64U + k_1))) = packed_float2(float2(r_5[k_1].x, - r_5[k_1].y)) ;

#line 2220
        k_1 = k_1 + 1U;

#line 2220
    }



    return;
}
