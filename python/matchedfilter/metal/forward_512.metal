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


#line 2395 "forward.slang"
float2 seriesSample_0(packed_float2 device* series_0, uint i_0, uint layout_0)
{
    if(layout_0 == 0U)
    {

#line 2398
        return float2(*(series_0+i_0)) ;
    }

#line 2399
    uint f_0 = (layout_0 >> 2U) + (layout_0 & 3U) * i_0;

#line 2399
    float2 _S2 = float2(*(series_0+(f_0 >> 1U))) ;

#line 2399
    float _S3;

    if((f_0 & 1U) != 0U)
    {

#line 2401
        _S3 = _S2.y;

#line 2401
    }
    else
    {

#line 2401
        _S3 = _S2.x;

#line 2401
    }

#line 2401
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


#line 325 "forward.slang"
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
    array<uint, int(1024)> threadgroup* stg_0;
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


#line 621
void dft2_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    float2 a_2 = (*r_1)[o_0];

#line 623
    float2 b_2 = (*r_1)[o_0 + 1U];

#line 623
    (*r_1)[o_0] = (*r_1)[o_0] + (*r_1)[o_0 + 1U];

#line 623
    (*r_1)[o_0 + 1U] = a_2 - b_2;
    return;
}


#line 749
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 749
    uint b_3 = 0U;

#line 759
    for(;;)
    {

#line 759
        if(b_3 < 8U)
        {
        }
        else
        {

#line 759
            break;
        }

#line 759
        dft2_0(r_2, b_3 * 2U);

#line 759
        b_3 = b_3 + 1U;

#line 759
    }

    return;
}


#line 877
uint lgOf_0(uint i_3)
{

#line 877
    uint _S13;

#line 877
    if(i_3 < 2U)
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


#line 1900
uint natSqueeze_0(uint x_1, uint fixedBits_0)
{

#line 1900
    uint k_0;

#line 1900
    uint o_1;

#line 1905
    if(((fixedBits_0 >> 0U) & 1U) == 0U)
    {

#line 1905
        uint o_2 = 0U | (((x_1 >> 0U) & 1U) << 0U);

#line 1905
        k_0 = 1U;

#line 1905
        o_1 = o_2;

#line 1905
    }
    else
    {

#line 1905
        k_0 = 0U;

#line 1905
        o_1 = 0U;

#line 1905
    }

#line 1905
    if(((fixedBits_0 >> 1U) & 1U) == 0U)
    {

#line 1905
        uint o_3 = o_1 | (((x_1 >> 1U) & 1U) << k_0);

#line 1905
        k_0 = k_0 + 1U;

#line 1905
        o_1 = o_3;

#line 1905
    }

#line 1905
    if(((fixedBits_0 >> 2U) & 1U) == 0U)
    {

#line 1905
        uint o_4 = o_1 | (((x_1 >> 2U) & 1U) << k_0);

#line 1905
        k_0 = k_0 + 1U;

#line 1905
        o_1 = o_4;

#line 1905
    }

#line 1905
    if(((fixedBits_0 >> 3U) & 1U) == 0U)
    {

#line 1905
        uint o_5 = o_1 | (((x_1 >> 3U) & 1U) << k_0);

#line 1905
        k_0 = k_0 + 1U;

#line 1905
        o_1 = o_5;

#line 1905
    }

#line 1905
    if(((fixedBits_0 >> 4U) & 1U) == 0U)
    {

#line 1905
        uint o_6 = o_1 | (((x_1 >> 4U) & 1U) << k_0);

#line 1905
        k_0 = k_0 + 1U;

#line 1905
        o_1 = o_6;

#line 1905
    }

#line 1905
    if(((fixedBits_0 >> 5U) & 1U) == 0U)
    {

#line 1905
        uint o_7 = o_1 | (((x_1 >> 5U) & 1U) << k_0);

#line 1905
        k_0 = k_0 + 1U;

#line 1905
        o_1 = o_7;

#line 1905
    }

#line 1905
    if(((fixedBits_0 >> 6U) & 1U) == 0U)
    {

#line 1905
        uint o_8 = o_1 | (((x_1 >> 6U) & 1U) << k_0);

#line 1905
        k_0 = k_0 + 1U;

#line 1905
        o_1 = o_8;

#line 1905
    }

#line 1905
    if(((fixedBits_0 >> 7U) & 1U) == 0U)
    {

#line 1905
        uint o_9 = o_1 | (((x_1 >> 7U) & 1U) << k_0);

#line 1905
        k_0 = k_0 + 1U;

#line 1905
        o_1 = o_9;

#line 1905
    }

#line 1905
    if(((fixedBits_0 >> 8U) & 1U) == 0U)
    {

#line 1905
        o_1 = o_1 | (((x_1 >> 8U) & 1U) << k_0);

#line 1905
    }

    return o_1;
}


#line 1920
uint natSwizzle_0(uint x_2)
{

#line 1920
    return x_2 ^ ((x_2 >> 5U) & 31U);
}


#line 1910
uint natExpand_0(uint x_3, uint fixedBits_1)
{

#line 1910
    uint k_1;

#line 1910
    uint o_10;

#line 1915
    if(((fixedBits_1 >> 0U) & 1U) == 0U)
    {

#line 1915
        uint o_11 = 0U | (((x_3 >> 0U) & 1U) << 0U);

#line 1915
        k_1 = 1U;

#line 1915
        o_10 = o_11;

#line 1915
    }
    else
    {

#line 1915
        k_1 = 0U;

#line 1915
        o_10 = 0U;

#line 1915
    }

#line 1915
    if(((fixedBits_1 >> 1U) & 1U) == 0U)
    {

#line 1915
        uint o_12 = o_10 | (((x_3 >> k_1) & 1U) << 1U);

#line 1915
        k_1 = k_1 + 1U;

#line 1915
        o_10 = o_12;

#line 1915
    }

#line 1915
    if(((fixedBits_1 >> 2U) & 1U) == 0U)
    {

#line 1915
        uint o_13 = o_10 | (((x_3 >> k_1) & 1U) << 2U);

#line 1915
        k_1 = k_1 + 1U;

#line 1915
        o_10 = o_13;

#line 1915
    }

#line 1915
    if(((fixedBits_1 >> 3U) & 1U) == 0U)
    {

#line 1915
        uint o_14 = o_10 | (((x_3 >> k_1) & 1U) << 3U);

#line 1915
        k_1 = k_1 + 1U;

#line 1915
        o_10 = o_14;

#line 1915
    }

#line 1915
    if(((fixedBits_1 >> 4U) & 1U) == 0U)
    {

#line 1915
        uint o_15 = o_10 | (((x_3 >> k_1) & 1U) << 4U);

#line 1915
        k_1 = k_1 + 1U;

#line 1915
        o_10 = o_15;

#line 1915
    }

#line 1915
    if(((fixedBits_1 >> 5U) & 1U) == 0U)
    {

#line 1915
        uint o_16 = o_10 | (((x_3 >> k_1) & 1U) << 5U);

#line 1915
        k_1 = k_1 + 1U;

#line 1915
        o_10 = o_16;

#line 1915
    }

#line 1915
    if(((fixedBits_1 >> 6U) & 1U) == 0U)
    {

#line 1915
        uint o_17 = o_10 | (((x_3 >> k_1) & 1U) << 6U);

#line 1915
        k_1 = k_1 + 1U;

#line 1915
        o_10 = o_17;

#line 1915
    }

#line 1915
    if(((fixedBits_1 >> 7U) & 1U) == 0U)
    {

#line 1915
        uint o_18 = o_10 | (((x_3 >> k_1) & 1U) << 7U);

#line 1915
        k_1 = k_1 + 1U;

#line 1915
        o_10 = o_18;

#line 1915
    }

#line 1915
    if(((fixedBits_1 >> 8U) & 1U) == 0U)
    {

#line 1915
        o_10 = o_10 | (((x_3 >> k_1) & 1U) << 8U);

#line 1915
    }

    return o_10;
}


#line 2409
[[kernel]] void seriesForward(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]])
{

#line 2409
    bool _S14;

#line 2409
    uint _S15;

#line 2409
    uint k2_1;

#line 2409
    float cr_0;

#line 2409
    float ci_0;

#line 2409
    uint _S16;

#line 2409
    uint z_0;

#line 2409
    uint _S17;

#line 2409
    uint c_1;

#line 2409
    uint d_2;

#line 2409
    uint j_1;

#line 2409
    thread KernelContext_0 kernelContext_2;

#line 2409
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2409
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2409
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2409
    (&kernelContext_2)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 2409
    threadgroup array<uint, int(1024)> stg_1;

#line 2409
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2415
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S18 = gid_0.x;

#line 2418
    uint _S19 = entryPointParams_starts_1[_S18];
    thread array<float2, int(16)> r_3;

#line 2419
    uint k_2 = 0U;
    for(;;)
    {

#line 2420
        if(k_2 < 16U)
        {
        }
        else
        {

#line 2420
            break;
        }

#line 2421
        uint offset_0 = tid_0 + 32U * k_2;
        float2 _S20 = float2(0.0f, 0.0f);

        if(_S19 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2424
            _S14 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S19);

#line 2424
        }
        else
        {

#line 2424
            _S14 = false;

#line 2424
        }

#line 2424
        float2 x_4;

#line 2424
        if(_S14)
        {

#line 2424
            x_4 = seriesSample_0((&kernelContext_2)->entryPointParams_series_0, _S19 + offset_0, (&kernelContext_2)->entryPointParams_0->seriesLayout_0);

#line 2424
        }
        else
        {

#line 2424
            x_4 = _S20;

#line 2424
        }

        r_3[k_2] = float2(x_4.x / 512.0f, - x_4.y / 512.0f);

#line 2420
        k_2 = k_2 + 1U;

#line 2420
    }

#line 2428
    for(;;)
    {

#line 2428
        for(;;)
        {

#line 2428
            for(;;)
            {

#line 2428
                for(;;)
                {

#line 2428
                    uint lgTB_0 = firstbithigh_0(32U);

#line 2428
                    _S15 = lgTB_0;

#line 2428
                    uint lgLn_0 = firstbithigh_0(512U);

#line 2428
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2428
                    uint lane_1 = tid_0 & 31U;

#line 2428
                    dft16_0(&r_3);

#line 2428
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 512.0f);

#line 2428
                    float _S21 = tw_0.x;

#line 2428
                    float _S22 = tw_0.y;

#line 2428
                    k2_1 = 0U;

#line 2428
                    cr_0 = 1.0f;

#line 2428
                    ci_0 = 0.0f;

#line 2428
                    for(;;)
                    {

#line 2428
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2428
                            break;
                        }

#line 2428
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2428
                        float nr_0 = cr_0 * _S21 - ci_0 * _S22;

#line 2428
                        float _S23 = cr_0 * _S22 + ci_0 * _S21;

#line 2428
                        k2_1 = k2_1 + 1U;

#line 2428
                        cr_0 = nr_0;

#line 2428
                        ci_0 = _S23;

#line 2428
                    }

#line 2428
                    uint per_1 = 16U / max(32U, 1U);

#line 2428
                    uint _S24 = max(2U, 1U);

#line 2428
                    _S16 = _S24;

#line 2428
                    uint blk2_1 = tid_0 / _S24;

#line 2428
                    uint lane2_1 = tid_0 % _S24;

#line 2428
                    for(;;)
                    {

#line 2428
                        thread array<float2, int(16)> out_0;

#line 2428
                        z_0 = 0U;

#line 2428
                        for(;;)
                        {

#line 2428
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2428
                                break;
                            }

#line 2428
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2428
                            z_0 = z_0 + 1U;

#line 2428
                        }

#line 2428
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2428
                        _S17 = spanMask_0;

#line 2428
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2428
                        uint p0_0 = computeWant_0(0U, 32U, 512U, blk_1, lane_1, per_1, _S24, 32U, blk2_1, lane2_1);

#line 2428
                        uint _S25 = p0_0 & lenMask_0;

#line 2428
                        uint _S26 = (_S25 >> lgTB_0) * 32U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S25 & spanMask_0);

#line 2428
                        c_1 = 0U;

#line 2428
                        for(;;)
                        {

#line 2428
                            if(c_1 < 1U)
                            {
                            }
                            else
                            {

#line 2428
                                break;
                            }

#line 2428
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2428
                            j_1 = 0U;

#line 2428
                            for(;;)
                            {

#line 2428
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 2428
                                    break;
                                }

#line 2428
                                stgPut_0(j_1 * 32U + (&kernelContext_2)->_tid_0, r_3[c_1 * 16U + j_1], &kernelContext_2);

#line 2428
                                j_1 = j_1 + 1U;

#line 2428
                            }

#line 2428
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2428
                            d_2 = 0U;

#line 2428
                            for(;;)
                            {

#line 2428
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2428
                                    break;
                                }

#line 2428
                                uint pz_0 = computeWant_0(d_2, 32U, 512U, 0U, 0U, per_1, _S24, 32U, 0U, 0U);

#line 2428
                                uint _S27 = pz_0 & lenMask_0;

#line 2428
                                uint az_0 = (_S27 >> lgTB_0) * 32U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S27 & spanMask_0);

#line 2428
                                float2 _S28 = stgGet_0(_S26 + az_0 - c_1 * 16U * 32U, &kernelContext_2);

#line 2428
                                out_0[d_2] = _S28;

#line 2428
                                d_2 = d_2 + 1U;

#line 2428
                            }

#line 2428
                            c_1 = c_1 + 1U;

#line 2428
                        }

#line 2428
                        d_2 = 0U;

#line 2428
                        for(;;)
                        {

#line 2428
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2428
                                break;
                            }

#line 2428
                            r_3[d_2] = out_0[d_2];

#line 2428
                            d_2 = d_2 + 1U;

#line 2428
                        }

#line 2428
                        break;
                    }

#line 2428
                    break;
                }

#line 2428
                break;
            }

#line 2428
            for(;;)
            {

#line 2428
                for(;;)
                {

#line 2428
                    uint lgTB_1 = firstbithigh_0(2U);

#line 2428
                    uint blk_2 = tid_0 >> lgTB_1;

#line 2428
                    uint lane_2 = tid_0 & 1U;

#line 2428
                    dft16_0(&r_3);

#line 2428
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 32.0f);

#line 2428
                    float _S29 = tw_1.x;

#line 2428
                    float _S30 = tw_1.y;

#line 2428
                    k2_1 = 0U;

#line 2428
                    cr_0 = 1.0f;

#line 2428
                    ci_0 = 0.0f;

#line 2428
                    for(;;)
                    {

#line 2428
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2428
                            break;
                        }

#line 2428
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2428
                        float nr_1 = cr_0 * _S29 - ci_0 * _S30;

#line 2428
                        float _S31 = cr_0 * _S30 + ci_0 * _S29;

#line 2428
                        k2_1 = k2_1 + 1U;

#line 2428
                        cr_0 = nr_1;

#line 2428
                        ci_0 = _S31;

#line 2428
                    }

#line 2428
                    uint per_2 = 16U / _S16;

#line 2428
                    uint _S32 = max(0U, 1U);

#line 2428
                    uint blk2_2 = tid_0 / _S32;

#line 2428
                    uint lane2_2 = tid_0 % _S32;

#line 2428
                    for(;;)
                    {

#line 2428
                        thread array<float2, int(16)> out_1;

#line 2428
                        z_0 = 0U;

#line 2428
                        for(;;)
                        {

#line 2428
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2428
                                break;
                            }

#line 2428
                            out_1[z_0] = float2(0.0f, 0.0f);

#line 2428
                            z_0 = z_0 + 1U;

#line 2428
                        }

#line 2428
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2428
                        uint p0_1 = computeWant_0(0U, 2U, 32U, blk_2, lane_2, per_2, _S32, 2U, blk2_2, lane2_2);

#line 2428
                        uint _S33 = p0_1 & _S17;

#line 2428
                        uint _S34 = (_S33 >> lgTB_1) * 32U + ((p0_1 >> _S15) << lgTB_1) + (_S33 & spanMask_1);

#line 2428
                        c_1 = 0U;

#line 2428
                        for(;;)
                        {

#line 2428
                            if(c_1 < 1U)
                            {
                            }
                            else
                            {

#line 2428
                                break;
                            }

#line 2428
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2428
                            j_1 = 0U;

#line 2428
                            for(;;)
                            {

#line 2428
                                if(j_1 < 16U)
                                {
                                }
                                else
                                {

#line 2428
                                    break;
                                }

#line 2428
                                stgPut_0(j_1 * 32U + (&kernelContext_2)->_tid_0, r_3[c_1 * 16U + j_1], &kernelContext_2);

#line 2428
                                j_1 = j_1 + 1U;

#line 2428
                            }

#line 2428
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2428
                            d_2 = 0U;

#line 2428
                            for(;;)
                            {

#line 2428
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2428
                                    break;
                                }

#line 2428
                                uint pz_1 = computeWant_0(d_2, 2U, 32U, 0U, 0U, per_2, _S32, 2U, 0U, 0U);

#line 2428
                                uint _S35 = pz_1 & _S17;

#line 2428
                                uint az_1 = (_S35 >> lgTB_1) * 32U + ((pz_1 >> _S15) << lgTB_1) + (_S35 & spanMask_1);

#line 2428
                                float2 _S36 = stgGet_0(_S34 + az_1 - c_1 * 16U * 32U, &kernelContext_2);

#line 2428
                                out_1[d_2] = _S36;

#line 2428
                                d_2 = d_2 + 1U;

#line 2428
                            }

#line 2428
                            c_1 = c_1 + 1U;

#line 2428
                        }

#line 2428
                        d_2 = 0U;

#line 2428
                        for(;;)
                        {

#line 2428
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2428
                                break;
                            }

#line 2428
                            r_3[d_2] = out_1[d_2];

#line 2428
                            d_2 = d_2 + 1U;

#line 2428
                        }

#line 2428
                        break;
                    }

#line 2428
                    break;
                }

#line 2428
                break;
            }

#line 2428
            break;
        }

#line 2428
        innermost_0(&r_3);

#line 2428
        break;
    }

#line 2428
    k_2 = 0U;

    for(;;)
    {

#line 2430
        if(k_2 < 16U)
        {
        }
        else
        {

#line 2430
            break;
        }

#line 2431
        r_3[k_2] = float2(r_3[k_2].x, - r_3[k_2].y);

#line 2430
        k_2 = k_2 + 1U;

#line 2430
    }

    uint _S37 = _S18 * 512U;

#line 2432
    for(;;)
    {

#line 2432
        uint fixedBits_2 = slotToIndex_0(0U);

#line 2432
        uint _S38 = natSwizzle_0(natSqueeze_0(slotToIndex_0(tid_0 << 4U), fixedBits_2));

#line 2432
        uint _S39 = natExpand_0(tid_0, fixedBits_2);

#line 2432
        uint _S40 = natSwizzle_0(tid_0);

#line 2432
        c_1 = 0U;

#line 2432
        for(;;)
        {

#line 2432
            if(c_1 < 1U)
            {
            }
            else
            {

#line 2432
                break;
            }

#line 2432
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2432
            j_1 = 0U;

#line 2432
            for(;;)
            {

#line 2432
                if(j_1 < 16U)
                {
                }
                else
                {

#line 2432
                    break;
                }

#line 2432
                uint _S41 = c_1 * 16U + j_1;

#line 2432
                stgPut_0(_S38 ^ (natSwizzle_0(natSqueeze_0(slotToIndex_0(_S41), fixedBits_2))), float2(r_3[_S41].x, r_3[_S41].y), &kernelContext_2);

#line 2432
                j_1 = j_1 + 1U;

#line 2432
            }

#line 2432
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2432
            uint _S42 = slotToIndex_0(c_1 * 16U);

#line 2432
            uint j_2 = 0U;

#line 2432
            for(;;)
            {

#line 2432
                if(j_2 < 16U)
                {
                }
                else
                {

#line 2432
                    break;
                }

#line 2432
                uint _S43 = j_2 * 32U;

#line 2432
                uint lag_0 = (_S39 | (natExpand_0(_S43, fixedBits_2))) | _S42;

#line 2432
                float2 _S44 = stgGet_0(_S40 ^ (natSwizzle_0(_S43)), &kernelContext_2);

#line 2432
                if(lag_0 >= 0U)
                {

#line 2432
                    _S14 = lag_0 < 512U;

#line 2432
                }
                else
                {

#line 2432
                    _S14 = false;

#line 2432
                }

#line 2432
                if(_S14)
                {

#line 2432
                    *((&kernelContext_2)->entryPointParams_spectra_0+(_S37 + lag_0)) = packed_float2(_S44) ;

#line 2432
                }

#line 2432
                j_2 = j_2 + 1U;

#line 2432
            }

#line 2432
            c_1 = c_1 + 1U;

#line 2432
        }

#line 2432
        break;
    }

#line 2433
    return;
}
