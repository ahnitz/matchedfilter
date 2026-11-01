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


#line 2285 "forward.slang"
float2 seriesSample_0(packed_float2 device* series_0, uint i_0, uint layout_0)
{
    if(layout_0 == 0U)
    {

#line 2288
        return float2(*(series_0+i_0)) ;
    }

#line 2289
    uint f_0 = (layout_0 >> 2U) + (layout_0 & 3U) * i_0;

#line 2289
    float2 _S2 = float2(*(series_0+(f_0 >> 1U))) ;

#line 2289
    float _S3;

    if((f_0 & 1U) != 0U)
    {

#line 2291
        _S3 = _S2.y;

#line 2291
    }
    else
    {

#line 2291
        _S3 = _S2.x;

#line 2291
    }

#line 2291
    return float2(_S3, 0.0f);
}


#line 608
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 610
    float2 t1_0 = *a_0 - *c_0;

#line 610
    float2 t2_0 = *b_0 + *d_0;

#line 610
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 612
    *b_0 = t1_0 + j3_0;

#line 612
    *c_0 = t0_0 - t2_0;

#line 612
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


#line 644
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 651
    uint n1_0 = 0U;
    for(;;)
    {

#line 652
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 652
            break;
        }

#line 652
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 652
        n1_0 = n1_0 + 1U;

#line 652
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 653
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 653
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 654
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 654
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 655
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 655
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 655
    uint k2_0 = 0U;
    for(;;)
    {

#line 656
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 656
            break;
        }

#line 656
        uint _S8 = 4U * k2_0;

#line 656
        r4_0(&(*r_0)[_S8], &(*r_0)[_S8 + 1U], &(*r_0)[_S8 + 2U], &(*r_0)[_S8 + 3U]);

#line 656
        k2_0 = k2_0 + 1U;

#line 656
    }

    float2 t_0 = (*r_0)[int(1)];

#line 658
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 658
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 659
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 659
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 660
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 660
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 661
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 661
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 662
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 662
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 663
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 663
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
    array<uint, int(8192)> threadgroup* stg_0;
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


#line 623
void dft4_0(array<float2, int(16)> thread* r_1, uint o_0)
{
    r4_0(&(*r_1)[o_0], &(*r_1)[o_0 + 1U], &(*r_1)[o_0 + 2U], &(*r_1)[o_0 + 3U]);
    float2 t_6 = (*r_1)[o_0 + 1U];

#line 626
    (*r_1)[o_0 + 1U] = (*r_1)[o_0 + 2U];

#line 626
    (*r_1)[o_0 + 2U] = t_6;
    return;
}


#line 747
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 747
    uint b_2 = 0U;

#line 756
    for(;;)
    {

#line 756
        if(b_2 < 4U)
        {
        }
        else
        {

#line 756
            break;
        }

#line 756
        dft4_0(r_2, b_2 * 4U);

#line 756
        b_2 = b_2 + 1U;

#line 756
    }


    return;
}


#line 875
uint lgOf_0(uint i_3)
{

#line 875
    uint _S13;

#line 875
    if(i_3 < 3U)
    {

#line 875
        _S13 = 4U;

#line 875
    }
    else
    {

#line 875
        _S13 = 1U;

#line 875
    }

#line 875
    return _S13;
}


#line 877
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(4U);

    uint x_0 = slot_0 >> lg_0;

#line 881
    uint lg_1 = lgOf_0(3U);

    uint x_1 = x_0 >> lg_1;

#line 881
    uint lg_2 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_2;

#line 881
    uint lg_3 = lgOf_0(1U);

#line 881
    uint lg_4 = lgOf_0(0U);

#line 886
    return (((((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | (x_2 & ((1U << lg_3) - 1U))) << lg_4) | ((x_2 >> lg_3) & ((1U << lg_4) - 1U));
}


#line 2299
[[kernel]] void seriesForward(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]])
{

#line 2299
    bool _S14;

#line 2299
    uint _S15;

#line 2299
    uint k2_1;

#line 2299
    float cr_0;

#line 2299
    float ci_0;

#line 2299
    uint _S16;

#line 2299
    uint z_0;

#line 2299
    uint _S17;

#line 2299
    uint c_1;

#line 2299
    uint d_2;

#line 2299
    uint j_1;

#line 2299
    uint _S18;

#line 2299
    uint _S19;

#line 2299
    uint _S20;

#line 2299
    thread KernelContext_0 kernelContext_2;

#line 2299
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2299
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2299
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2299
    (&kernelContext_2)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 2299
    threadgroup array<uint, int(8192)> stg_1;

#line 2299
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2305
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S21 = gid_0.x;

#line 2308
    uint _S22 = entryPointParams_starts_1[_S21];
    thread array<float2, int(16)> r_3;

#line 2309
    uint k_0 = 0U;
    for(;;)
    {

#line 2310
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2310
            break;
        }

#line 2311
        uint offset_0 = tid_0 + 1024U * k_0;
        float2 _S23 = float2(0.0f, 0.0f);

        if(_S22 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2314
            _S14 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S22);

#line 2314
        }
        else
        {

#line 2314
            _S14 = false;

#line 2314
        }

#line 2314
        float2 x_3;

#line 2314
        if(_S14)
        {

#line 2314
            x_3 = seriesSample_0((&kernelContext_2)->entryPointParams_series_0, _S22 + offset_0, (&kernelContext_2)->entryPointParams_0->seriesLayout_0);

#line 2314
        }
        else
        {

#line 2314
            x_3 = _S23;

#line 2314
        }

        r_3[k_0] = float2(x_3.x / 16384.0f, - x_3.y / 16384.0f);

#line 2310
        k_0 = k_0 + 1U;

#line 2310
    }

#line 2318
    for(;;)
    {

#line 2318
        for(;;)
        {

#line 2318
            for(;;)
            {

#line 2318
                for(;;)
                {

#line 2318
                    uint lgTB_0 = firstbithigh_0(1024U);

#line 2318
                    _S15 = lgTB_0;

#line 2318
                    uint lgLn_0 = firstbithigh_0(16384U);

#line 2318
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2318
                    uint lane_1 = tid_0 & 1023U;

#line 2318
                    dft16_0(&r_3);

#line 2318
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 16384.0f);

#line 2318
                    float _S24 = tw_0.x;

#line 2318
                    float _S25 = tw_0.y;

#line 2318
                    k2_1 = 0U;

#line 2318
                    cr_0 = 1.0f;

#line 2318
                    ci_0 = 0.0f;

#line 2318
                    for(;;)
                    {

#line 2318
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2318
                            break;
                        }

#line 2318
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2318
                        float nr_0 = cr_0 * _S24 - ci_0 * _S25;

#line 2318
                        float _S26 = cr_0 * _S25 + ci_0 * _S24;

#line 2318
                        k2_1 = k2_1 + 1U;

#line 2318
                        cr_0 = nr_0;

#line 2318
                        ci_0 = _S26;

#line 2318
                    }

#line 2318
                    uint per_1 = 16U / max(1024U, 1U);

#line 2318
                    uint _S27 = max(64U, 1U);

#line 2318
                    _S16 = _S27;

#line 2318
                    uint blk2_1 = tid_0 / _S27;

#line 2318
                    uint lane2_1 = tid_0 % _S27;

#line 2318
                    for(;;)
                    {

#line 2318
                        thread array<float2, int(16)> out_0;

#line 2318
                        z_0 = 0U;

#line 2318
                        for(;;)
                        {

#line 2318
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2318
                                break;
                            }

#line 2318
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2318
                            z_0 = z_0 + 1U;

#line 2318
                        }

#line 2318
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2318
                        _S17 = spanMask_0;

#line 2318
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2318
                        uint p0_0 = computeWant_0(0U, 1024U, 16384U, blk_1, lane_1, per_1, _S27, 1024U, blk2_1, lane2_1);

#line 2318
                        uint _S28 = p0_0 & lenMask_0;

#line 2318
                        uint _S29 = _S28 >> lgTB_0;

#line 2318
                        uint _S30 = _S29 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S28 & spanMask_0);

#line 2318
                        c_1 = 0U;

#line 2318
                        for(;;)
                        {

#line 2318
                            if(c_1 < 4U)
                            {
                            }
                            else
                            {

#line 2318
                                break;
                            }

#line 2318
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2318
                            j_1 = 0U;

#line 2318
                            for(;;)
                            {

#line 2318
                                if(j_1 < 4U)
                                {
                                }
                                else
                                {

#line 2318
                                    break;
                                }

#line 2318
                                stgPut_0(j_1 * 1024U + (&kernelContext_2)->_tid_0, r_3[c_1 * 4U + j_1], &kernelContext_2);

#line 2318
                                j_1 = j_1 + 1U;

#line 2318
                            }

#line 2318
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2318
                            d_2 = 0U;

#line 2318
                            for(;;)
                            {

#line 2318
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2318
                                    break;
                                }

#line 2318
                                uint pz_0 = computeWant_0(d_2, 1024U, 16384U, 0U, 0U, per_1, _S27, 1024U, 0U, 0U);

#line 2318
                                uint _S31 = pz_0 & lenMask_0;

#line 2318
                                uint iz_0 = _S31 >> lgTB_0;

#line 2318
                                uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S31 & spanMask_0);

#line 2318
                                uint i_4 = _S29 + iz_0;

#line 2318
                                uint _S32 = c_1 * 4U;

#line 2318
                                if(i_4 >= _S32)
                                {

#line 2318
                                    _S14 = i_4 < ((c_1 + 1U) * 4U);

#line 2318
                                }
                                else
                                {

#line 2318
                                    _S14 = false;

#line 2318
                                }

#line 2318
                                if(_S14)
                                {

#line 2318
                                    float2 _S33 = stgGet_0(_S30 + az_0 - _S32 * 1024U, &kernelContext_2);

#line 2318
                                    out_0[d_2] = _S33;

#line 2318
                                }

#line 2318
                                d_2 = d_2 + 1U;

#line 2318
                            }

#line 2318
                            c_1 = c_1 + 1U;

#line 2318
                        }

#line 2318
                        d_2 = 0U;

#line 2318
                        for(;;)
                        {

#line 2318
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2318
                                break;
                            }

#line 2318
                            r_3[d_2] = out_0[d_2];

#line 2318
                            d_2 = d_2 + 1U;

#line 2318
                        }

#line 2318
                        break;
                    }

#line 2318
                    break;
                }

#line 2318
                break;
            }

#line 2318
            for(;;)
            {

#line 2318
                for(;;)
                {

#line 2318
                    uint lgTB_1 = firstbithigh_0(64U);

#line 2318
                    _S18 = lgTB_1;

#line 2318
                    uint blk_2 = tid_0 >> lgTB_1;

#line 2318
                    uint lane_2 = tid_0 & 63U;

#line 2318
                    dft16_0(&r_3);

#line 2318
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 2318
                    float _S34 = tw_1.x;

#line 2318
                    float _S35 = tw_1.y;

#line 2318
                    k2_1 = 0U;

#line 2318
                    cr_0 = 1.0f;

#line 2318
                    ci_0 = 0.0f;

#line 2318
                    for(;;)
                    {

#line 2318
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2318
                            break;
                        }

#line 2318
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2318
                        float nr_1 = cr_0 * _S34 - ci_0 * _S35;

#line 2318
                        float _S36 = cr_0 * _S35 + ci_0 * _S34;

#line 2318
                        k2_1 = k2_1 + 1U;

#line 2318
                        cr_0 = nr_1;

#line 2318
                        ci_0 = _S36;

#line 2318
                    }

#line 2318
                    uint per_2 = 16U / _S16;

#line 2318
                    uint _S37 = max(4U, 1U);

#line 2318
                    _S19 = _S37;

#line 2318
                    uint blk2_2 = tid_0 / _S37;

#line 2318
                    uint lane2_2 = tid_0 % _S37;

#line 2318
                    for(;;)
                    {

#line 2318
                        thread array<float2, int(16)> out_1;

#line 2318
                        z_0 = 0U;

#line 2318
                        for(;;)
                        {

#line 2318
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2318
                                break;
                            }

#line 2318
                            out_1[z_0] = float2(0.0f, 0.0f);

#line 2318
                            z_0 = z_0 + 1U;

#line 2318
                        }

#line 2318
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2318
                        _S20 = spanMask_1;

#line 2318
                        uint p0_1 = computeWant_0(0U, 64U, 1024U, blk_2, lane_2, per_2, _S37, 64U, blk2_2, lane2_2);

#line 2318
                        uint _S38 = p0_1 & _S17;

#line 2318
                        uint _S39 = _S38 >> lgTB_1;

#line 2318
                        uint _S40 = _S39 * 1024U + ((p0_1 >> _S15) << lgTB_1) + (_S38 & spanMask_1);

#line 2318
                        c_1 = 0U;

#line 2318
                        for(;;)
                        {

#line 2318
                            if(c_1 < 4U)
                            {
                            }
                            else
                            {

#line 2318
                                break;
                            }

#line 2318
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2318
                            j_1 = 0U;

#line 2318
                            for(;;)
                            {

#line 2318
                                if(j_1 < 4U)
                                {
                                }
                                else
                                {

#line 2318
                                    break;
                                }

#line 2318
                                stgPut_0(j_1 * 1024U + (&kernelContext_2)->_tid_0, r_3[c_1 * 4U + j_1], &kernelContext_2);

#line 2318
                                j_1 = j_1 + 1U;

#line 2318
                            }

#line 2318
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2318
                            d_2 = 0U;

#line 2318
                            for(;;)
                            {

#line 2318
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2318
                                    break;
                                }

#line 2318
                                uint pz_1 = computeWant_0(d_2, 64U, 1024U, 0U, 0U, per_2, _S37, 64U, 0U, 0U);

#line 2318
                                uint _S41 = pz_1 & _S17;

#line 2318
                                uint iz_1 = _S41 >> lgTB_1;

#line 2318
                                uint az_1 = iz_1 * 1024U + ((pz_1 >> _S15) << lgTB_1) + (_S41 & spanMask_1);

#line 2318
                                uint i_5 = _S39 + iz_1;

#line 2318
                                uint _S42 = c_1 * 4U;

#line 2318
                                if(i_5 >= _S42)
                                {

#line 2318
                                    _S14 = i_5 < ((c_1 + 1U) * 4U);

#line 2318
                                }
                                else
                                {

#line 2318
                                    _S14 = false;

#line 2318
                                }

#line 2318
                                if(_S14)
                                {

#line 2318
                                    float2 _S43 = stgGet_0(_S40 + az_1 - _S42 * 1024U, &kernelContext_2);

#line 2318
                                    out_1[d_2] = _S43;

#line 2318
                                }

#line 2318
                                d_2 = d_2 + 1U;

#line 2318
                            }

#line 2318
                            c_1 = c_1 + 1U;

#line 2318
                        }

#line 2318
                        d_2 = 0U;

#line 2318
                        for(;;)
                        {

#line 2318
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2318
                                break;
                            }

#line 2318
                            r_3[d_2] = out_1[d_2];

#line 2318
                            d_2 = d_2 + 1U;

#line 2318
                        }

#line 2318
                        break;
                    }

#line 2318
                    break;
                }

#line 2318
                break;
            }

#line 2318
            for(;;)
            {

#line 2318
                for(;;)
                {

#line 2318
                    uint lgTB_2 = firstbithigh_0(4U);

#line 2318
                    uint blk_3 = tid_0 >> lgTB_2;

#line 2318
                    uint lane_3 = tid_0 & 3U;

#line 2318
                    dft16_0(&r_3);

#line 2318
                    float2 tw_2 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 64.0f);

#line 2318
                    float _S44 = tw_2.x;

#line 2318
                    float _S45 = tw_2.y;

#line 2318
                    k2_1 = 0U;

#line 2318
                    cr_0 = 1.0f;

#line 2318
                    ci_0 = 0.0f;

#line 2318
                    for(;;)
                    {

#line 2318
                        if(k2_1 < 16U)
                        {
                        }
                        else
                        {

#line 2318
                            break;
                        }

#line 2318
                        r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2318
                        float nr_2 = cr_0 * _S44 - ci_0 * _S45;

#line 2318
                        float _S46 = cr_0 * _S45 + ci_0 * _S44;

#line 2318
                        k2_1 = k2_1 + 1U;

#line 2318
                        cr_0 = nr_2;

#line 2318
                        ci_0 = _S46;

#line 2318
                    }

#line 2318
                    uint per_3 = 16U / _S19;

#line 2318
                    uint _S47 = max(0U, 1U);

#line 2318
                    uint blk2_3 = tid_0 / _S47;

#line 2318
                    uint lane2_3 = tid_0 % _S47;

#line 2318
                    for(;;)
                    {

#line 2318
                        thread array<float2, int(16)> out_2;

#line 2318
                        z_0 = 0U;

#line 2318
                        for(;;)
                        {

#line 2318
                            if(z_0 < 16U)
                            {
                            }
                            else
                            {

#line 2318
                                break;
                            }

#line 2318
                            out_2[z_0] = float2(0.0f, 0.0f);

#line 2318
                            z_0 = z_0 + 1U;

#line 2318
                        }

#line 2318
                        uint spanMask_2 = (1U << lgTB_2) - 1U;

#line 2318
                        uint p0_2 = computeWant_0(0U, 4U, 64U, blk_3, lane_3, per_3, _S47, 4U, blk2_3, lane2_3);

#line 2318
                        uint _S48 = p0_2 & _S20;

#line 2318
                        uint _S49 = _S48 >> lgTB_2;

#line 2318
                        uint _S50 = _S49 * 1024U + ((p0_2 >> _S18) << lgTB_2) + (_S48 & spanMask_2);

#line 2318
                        c_1 = 0U;

#line 2318
                        for(;;)
                        {

#line 2318
                            if(c_1 < 4U)
                            {
                            }
                            else
                            {

#line 2318
                                break;
                            }

#line 2318
                            bool _S51 = c_1 == 0U;

#line 2318
                            if(!_S51)
                            {

#line 2318
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2318
                            }
                            else
                            {

#line 2318
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2318
                            }

#line 2318
                            j_1 = 0U;

#line 2318
                            for(;;)
                            {

#line 2318
                                if(j_1 < 4U)
                                {
                                }
                                else
                                {

#line 2318
                                    break;
                                }

#line 2318
                                stgPut_0(j_1 * 1024U + (&kernelContext_2)->_tid_0, r_3[c_1 * 4U + j_1], &kernelContext_2);

#line 2318
                                j_1 = j_1 + 1U;

#line 2318
                            }

#line 2318
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2318
                            d_2 = 0U;

#line 2318
                            for(;;)
                            {

#line 2318
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2318
                                    break;
                                }

#line 2318
                                uint pz_2 = computeWant_0(d_2, 4U, 64U, 0U, 0U, per_3, _S47, 4U, 0U, 0U);

#line 2318
                                uint _S52 = pz_2 & _S20;

#line 2318
                                uint iz_2 = _S52 >> lgTB_2;

#line 2318
                                uint az_2 = iz_2 * 1024U + ((pz_2 >> _S18) << lgTB_2) + (_S52 & spanMask_2);

#line 2318
                                uint i_6 = _S49 + iz_2;

#line 2318
                                uint _S53 = c_1 * 4U;

#line 2318
                                if(i_6 >= _S53)
                                {

#line 2318
                                    _S14 = i_6 < ((c_1 + 1U) * 4U);

#line 2318
                                }
                                else
                                {

#line 2318
                                    _S14 = false;

#line 2318
                                }

#line 2318
                                if(_S14)
                                {

#line 2318
                                    float2 _S54 = stgGet_0(_S50 + az_2 - _S53 * 1024U, &kernelContext_2);

#line 2318
                                    out_2[d_2] = _S54;

#line 2318
                                }

#line 2318
                                d_2 = d_2 + 1U;

#line 2318
                            }

#line 2318
                            c_1 = c_1 + 1U;

#line 2318
                        }

#line 2318
                        d_2 = 0U;

#line 2318
                        for(;;)
                        {

#line 2318
                            if(d_2 < 16U)
                            {
                            }
                            else
                            {

#line 2318
                                break;
                            }

#line 2318
                            r_3[d_2] = out_2[d_2];

#line 2318
                            d_2 = d_2 + 1U;

#line 2318
                        }

#line 2318
                        break;
                    }

#line 2318
                    break;
                }

#line 2318
                break;
            }

#line 2318
            break;
        }

#line 2318
        innermost_0(&r_3);

#line 2318
        break;
    }

#line 2318
    k_0 = 0U;
    for(;;)
    {

#line 2319
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2319
            break;
        }

#line 2319
        *((&kernelContext_2)->entryPointParams_spectra_0+(_S21 * 16384U + slotToIndex_0(tid_0 * 16U + k_0))) = packed_float2(float2(r_3[k_0].x, - r_3[k_0].y)) ;

#line 2319
        k_0 = k_0 + 1U;

#line 2319
    }



    return;
}
