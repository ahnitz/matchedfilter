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
    array<uint, int(256)> threadgroup* stg_0;
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


#line 628
void dft8_0(array<float2, int(16)> thread* r_1, uint o_0)
{


    thread array<float2, int(8)> b_2;

#line 632
    uint s_0 = 1U;
    for(;;)
    {

#line 633
        if(s_0 < 8U)
        {
        }
        else
        {

#line 633
            break;
        }

#line 633
        uint j_1 = 0U;
        for(;;)
        {

#line 634
            if(j_1 < 4U)
            {
            }
            else
            {

#line 634
                break;
            }

#line 635
            uint k_0 = j_1 & (s_0 - 1U);


            uint _S13 = o_0 + j_1;

#line 638
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_0)), (*r_1)[_S13 + 4U]);
            uint _S14 = ((j_1 - k_0) << 1U) + k_0;

#line 639
            b_2[_S14] = (*r_1)[_S13] + t_6;

#line 639
            b_2[_S14 + s_0] = (*r_1)[_S13] - t_6;

#line 634
            j_1 = j_1 + 1U;

#line 634
        }

#line 634
        uint i_3 = 0U;

#line 641
        for(;;)
        {

#line 641
            if(i_3 < 8U)
            {
            }
            else
            {

#line 641
                break;
            }

#line 641
            (*r_1)[o_0 + i_3] = b_2[i_3];

#line 641
            i_3 = i_3 + 1U;

#line 641
        }

#line 633
        s_0 = s_0 << 1U;

#line 633
    }

#line 643
    return;
}


#line 747
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 747
    uint b_3 = 0U;

#line 755
    for(;;)
    {

#line 755
        if(b_3 < 2U)
        {
        }
        else
        {

#line 755
            break;
        }

#line 755
        dft8_0(r_2, b_3 * 8U);

#line 755
        b_3 = b_3 + 1U;

#line 755
    }



    return;
}


#line 875
uint lgOf_0(uint i_4)
{

#line 875
    uint _S15;

#line 875
    if(i_4 < 1U)
    {

#line 875
        _S15 = 4U;

#line 875
    }
    else
    {

#line 875
        if(i_4 == 1U)
        {

#line 875
            _S15 = 3U;

#line 875
        }
        else
        {

#line 875
            _S15 = 1U;

#line 875
        }

#line 875
    }

#line 875
    return _S15;
}


#line 877
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 881
    uint lg_1 = lgOf_0(0U);

#line 886
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 2299
[[kernel]] void seriesForward(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]])
{

#line 2299
    uint j_2;

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
    threadgroup array<uint, int(256)> stg_1;

#line 2299
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2305
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S16 = gid_0.x;

#line 2308
    uint _S17 = entryPointParams_starts_1[_S16];
    thread array<float2, int(16)> r_3;

#line 2309
    uint k_1 = 0U;
    for(;;)
    {

#line 2310
        if(k_1 < 16U)
        {
        }
        else
        {

#line 2310
            break;
        }

#line 2311
        uint offset_0 = tid_0 + 8U * k_1;
        float2 _S18 = float2(0.0f, 0.0f);

#line 2312
        bool _S19;

        if(_S17 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2314
            _S19 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S17);

#line 2314
        }
        else
        {

#line 2314
            _S19 = false;

#line 2314
        }

#line 2314
        float2 x_0;

#line 2314
        if(_S19)
        {

#line 2314
            x_0 = seriesSample_0((&kernelContext_2)->entryPointParams_series_0, _S17 + offset_0, (&kernelContext_2)->entryPointParams_0->seriesLayout_0);

#line 2314
        }
        else
        {

#line 2314
            x_0 = _S18;

#line 2314
        }

        r_3[k_1] = float2(x_0.x / 128.0f, - x_0.y / 128.0f);

#line 2310
        k_1 = k_1 + 1U;

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
                    uint lgTB_0 = firstbithigh_0(8U);

#line 2318
                    uint lgLn_0 = firstbithigh_0(128U);

#line 2318
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2318
                    uint lane_1 = tid_0 & 7U;

#line 2318
                    dft16_0(&r_3);

#line 2318
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 128.0f);

#line 2318
                    float _S20 = tw_0.x;

#line 2318
                    float _S21 = tw_0.y;

#line 2318
                    uint k2_1 = 0U;

#line 2318
                    float cr_0 = 1.0f;

#line 2318
                    float ci_0 = 0.0f;

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
                        float nr_0 = cr_0 * _S20 - ci_0 * _S21;

#line 2318
                        float _S22 = cr_0 * _S21 + ci_0 * _S20;

#line 2318
                        k2_1 = k2_1 + 1U;

#line 2318
                        cr_0 = nr_0;

#line 2318
                        ci_0 = _S22;

#line 2318
                    }

#line 2318
                    uint per_1 = 16U / max(8U, 1U);

#line 2318
                    uint _S23 = max(0U, 1U);

#line 2318
                    uint blk2_1 = tid_0 / _S23;

#line 2318
                    uint lane2_1 = tid_0 % _S23;

#line 2318
                    for(;;)
                    {

#line 2318
                        thread array<float2, int(16)> out_0;

#line 2318
                        uint z_0 = 0U;

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
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2318
                        uint p0_0 = computeWant_0(0U, 8U, 128U, blk_1, lane_1, per_1, _S23, 8U, blk2_1, lane2_1);

#line 2318
                        uint _S24 = p0_0 & lenMask_0;

#line 2318
                        uint _S25 = (_S24 >> lgTB_0) * 8U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S24 & spanMask_0);

#line 2318
                        uint c_1 = 0U;

#line 2318
                        for(;;)
                        {

#line 2318
                            if(c_1 < 1U)
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
                            j_2 = 0U;

#line 2318
                            for(;;)
                            {

#line 2318
                                if(j_2 < 16U)
                                {
                                }
                                else
                                {

#line 2318
                                    break;
                                }

#line 2318
                                stgPut_0(j_2 * 8U + (&kernelContext_2)->_tid_0, r_3[c_1 * 16U + j_2], &kernelContext_2);

#line 2318
                                j_2 = j_2 + 1U;

#line 2318
                            }

#line 2318
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2318
                            uint d_2 = 0U;

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
                                uint pz_0 = computeWant_0(d_2, 8U, 128U, 0U, 0U, per_1, _S23, 8U, 0U, 0U);

#line 2318
                                uint _S26 = pz_0 & lenMask_0;

#line 2318
                                uint az_0 = (_S26 >> lgTB_0) * 8U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S26 & spanMask_0);

#line 2318
                                float2 _S27 = stgGet_0(_S25 + az_0 - c_1 * 16U * 8U, &kernelContext_2);

#line 2318
                                out_0[d_2] = _S27;

#line 2318
                                d_2 = d_2 + 1U;

#line 2318
                            }

#line 2318
                            c_1 = c_1 + 1U;

#line 2318
                        }

#line 2318
                        j_2 = 0U;

#line 2318
                        for(;;)
                        {

#line 2318
                            if(j_2 < 16U)
                            {
                            }
                            else
                            {

#line 2318
                                break;
                            }

#line 2318
                            r_3[j_2] = out_0[j_2];

#line 2318
                            j_2 = j_2 + 1U;

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
    k_1 = 0U;
    for(;;)
    {

#line 2319
        if(k_1 < 16U)
        {
        }
        else
        {

#line 2319
            break;
        }

#line 2319
        *((&kernelContext_2)->entryPointParams_spectra_0+(_S16 * 128U + slotToIndex_0(tid_0 * 16U + k_1))) = packed_float2(float2(r_3[k_1].x, - r_3[k_1].y)) ;

#line 2319
        k_1 = k_1 + 1U;

#line 2319
    }



    return;
}
