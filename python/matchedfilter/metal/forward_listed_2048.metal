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


#line 630
void dft8_0(array<float2, int(16)> thread* r_1, uint o_0)
{


    thread array<float2, int(8)> b_2;

#line 634
    uint s_0 = 1U;
    for(;;)
    {

#line 635
        if(s_0 < 8U)
        {
        }
        else
        {

#line 635
            break;
        }

#line 635
        uint j_1 = 0U;
        for(;;)
        {

#line 636
            if(j_1 < 4U)
            {
            }
            else
            {

#line 636
                break;
            }

#line 637
            uint k_0 = j_1 & (s_0 - 1U);


            uint _S11 = o_0 + j_1;

#line 640
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_0)), (*r_1)[_S11 + 4U]);
            uint _S12 = ((j_1 - k_0) << 1U) + k_0;

#line 641
            b_2[_S12] = (*r_1)[_S11] + t_6;

#line 641
            b_2[_S12 + s_0] = (*r_1)[_S11] - t_6;

#line 636
            j_1 = j_1 + 1U;

#line 636
        }

#line 636
        uint i_1 = 0U;

#line 643
        for(;;)
        {

#line 643
            if(i_1 < 8U)
            {
            }
            else
            {

#line 643
                break;
            }

#line 643
            (*r_1)[o_0 + i_1] = b_2[i_1];

#line 643
            i_1 = i_1 + 1U;

#line 643
        }

#line 635
        s_0 = s_0 << 1U;

#line 635
    }

#line 645
    return;
}


#line 749
void innermost_0(array<float2, int(16)> thread* r_2)
{

#line 749
    uint b_3 = 0U;

#line 757
    for(;;)
    {

#line 757
        if(b_3 < 2U)
        {
        }
        else
        {

#line 757
            break;
        }

#line 757
        dft8_0(r_2, b_3 * 8U);

#line 757
        b_3 = b_3 + 1U;

#line 757
    }



    return;
}


#line 877
uint lgOf_0(uint i_2)
{

#line 877
    uint _S13;

#line 877
    if(i_2 < 2U)
    {

#line 877
        _S13 = 4U;

#line 877
    }
    else
    {

#line 877
        if(i_2 == 2U)
        {

#line 877
            _S13 = 3U;

#line 877
        }
        else
        {

#line 877
            _S13 = 1U;

#line 877
        }

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


#line 2458
struct EntryPointParams_0
{
    uint seriesLength_0;
    uint seriesLayout_0;
    uint gridSize_0;
};


#line 804
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_spectra_0;
    uint device* entryPointParams_blockList_0;
    uint device* entryPointParams_blockArgs_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 2458
[[kernel]] void seriesForwardListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]], uint device* entryPointParams_blockList_1 [[buffer(4)]], uint device* entryPointParams_blockArgs_1 [[buffer(5)]])
{

#line 2458
    uint _S14;

#line 2458
    uint _S15;

#line 2458
    uint _S16;

#line 2458
    thread KernelContext_0 kernelContext_0;

#line 2458
    (&kernelContext_0)->entryPointParams_0 = entryPointParams_1;

#line 2458
    (&kernelContext_0)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2458
    (&kernelContext_0)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2458
    (&kernelContext_0)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 2458
    (&kernelContext_0)->entryPointParams_blockList_0 = entryPointParams_blockList_1;

#line 2458
    (&kernelContext_0)->entryPointParams_blockArgs_0 = entryPointParams_blockArgs_1;

#line 2458
    threadgroup array<uint, int(2048)> stg_1;

#line 2458
    (&kernelContext_0)->stg_0 = &stg_1;

#line 2466
    uint tid_0 = lid_0.x;
    (&kernelContext_0)->_tid_0 = tid_0;
    (&kernelContext_0)->_stgBase_0 = 0U;
    uint _S17 = entryPointParams_blockArgs_1[int(0)];

#line 2469
    uint item_0 = gid_0.x;
    for(;;)
    {

#line 2470
        if(item_0 < _S17)
        {
        }
        else
        {

#line 2470
            break;
        }

#line 2471
        uint row_0 = (&kernelContext_0)->entryPointParams_blockList_0[item_0];
        uint _S18 = (&kernelContext_0)->entryPointParams_starts_0[row_0];
        thread array<float2, int(16)> r_3;

#line 2473
        uint k_1 = 0U;
        for(;;)
        {

#line 2474
            if(k_1 < 16U)
            {
            }
            else
            {

#line 2474
                break;
            }

#line 2475
            uint offset_0 = tid_0 + 128U * k_1;
            float2 _S19 = float2(0.0f, 0.0f);

#line 2476
            bool _S20;
            if(_S18 < ((&kernelContext_0)->entryPointParams_0->seriesLength_0))
            {

#line 2477
                _S20 = offset_0 < ((&kernelContext_0)->entryPointParams_0->seriesLength_0 - _S18);

#line 2477
            }
            else
            {

#line 2477
                _S20 = false;

#line 2477
            }

#line 2477
            float2 x_1;

#line 2477
            if(_S20)
            {

#line 2477
                x_1 = seriesSample_0((&kernelContext_0)->entryPointParams_series_0, _S18 + offset_0, (&kernelContext_0)->entryPointParams_0->seriesLayout_0);

#line 2477
            }
            else
            {

#line 2477
                x_1 = _S19;

#line 2477
            }

            r_3[k_1] = float2(x_1.x / 2048.0f, - x_1.y / 2048.0f);

#line 2474
            k_1 = k_1 + 1U;

#line 2474
        }

#line 2481
        for(;;)
        {

#line 2481
            for(;;)
            {

#line 2481
                for(;;)
                {

#line 2481
                    for(;;)
                    {

#line 2481
                        uint lgTB_0 = firstbithigh_0(128U);

#line 2481
                        _S14 = lgTB_0;

#line 2481
                        uint lgLn_0 = firstbithigh_0(2048U);

#line 2481
                        uint blk_1 = tid_0 >> lgTB_0;

#line 2481
                        uint lane_1 = tid_0 & 127U;

#line 2481
                        dft16_0(&r_3);

#line 2481
                        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 2048.0f);

#line 2481
                        float _S21 = tw_0.x;

#line 2481
                        float _S22 = tw_0.y;

#line 2481
                        uint k2_1 = 0U;

#line 2481
                        float cr_0 = 1.0f;

#line 2481
                        float ci_0 = 0.0f;

#line 2481
                        for(;;)
                        {

#line 2481
                            if(k2_1 < 16U)
                            {
                            }
                            else
                            {

#line 2481
                                break;
                            }

#line 2481
                            r_3[k2_1] = cmul_0(r_3[k2_1], float2(cr_0, ci_0));

#line 2481
                            float nr_0 = cr_0 * _S21 - ci_0 * _S22;

#line 2481
                            float _S23 = cr_0 * _S22 + ci_0 * _S21;

#line 2481
                            k2_1 = k2_1 + 1U;

#line 2481
                            cr_0 = nr_0;

#line 2481
                            ci_0 = _S23;

#line 2481
                        }

#line 2481
                        uint per_1 = 16U / max(128U, 1U);

#line 2481
                        uint _S24 = max(8U, 1U);

#line 2481
                        _S15 = _S24;

#line 2481
                        uint blk2_1 = tid_0 / _S24;

#line 2481
                        uint lane2_1 = tid_0 % _S24;

#line 2481
                        for(;;)
                        {

#line 2481
                            uint _S25 = (1U << lgTB_0) - 1U;

#line 2481
                            _S16 = _S25;

#line 2481
                            uint _S26 = (1U << lgLn_0) - 1U;

#line 2481
                            thread array<uint, int(16)> src_0;

#line 2481
                            uint d_2 = 0U;

#line 2481
                            for(;;)
                            {

#line 2481
                                if(d_2 < 16U)
                                {
                                }
                                else
                                {

#line 2481
                                    break;
                                }

#line 2481
                                uint p_0 = computeWant_0(d_2, 128U, 2048U, blk_1, lane_1, per_1, _S24, 128U, blk2_1, lane2_1);

#line 2481
                                uint rem_0 = p_0 & _S26;

#line 2481
                                src_0[d_2] = (rem_0 >> lgTB_0) * 128U + ((p_0 >> lgLn_0) << lgTB_0) + (rem_0 & _S25);

#line 2481
                                d_2 = d_2 + 1U;

#line 2481
                            }

#line 2481
                            thread array<float, int(16)> xr_0;

#line 2481
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2481
                            uint j_2 = 0U;

#line 2481
                            for(;;)
                            {

#line 2481
                                if(j_2 < 16U)
                                {
                                }
                                else
                                {

#line 2481
                                    break;
                                }

#line 2481
                                (*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + j_2 * 128U + (&kernelContext_0)->_tid_0] = (as_type<uint>((r_3[j_2].x)));

#line 2481
                                j_2 = j_2 + 1U;

#line 2481
                            }

#line 2481
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2481
                            uint d_3 = 0U;

#line 2481
                            for(;;)
                            {

#line 2481
                                if(d_3 < 16U)
                                {
                                }
                                else
                                {

#line 2481
                                    break;
                                }

#line 2481
                                xr_0[d_3] = (as_type<float>(((*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + src_0[d_3]])));

#line 2481
                                d_3 = d_3 + 1U;

#line 2481
                            }

#line 2481
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2481
                            uint j_3 = 0U;

#line 2481
                            for(;;)
                            {

#line 2481
                                if(j_3 < 16U)
                                {
                                }
                                else
                                {

#line 2481
                                    break;
                                }

#line 2481
                                (*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + j_3 * 128U + (&kernelContext_0)->_tid_0] = (as_type<uint>((r_3[j_3].y)));

#line 2481
                                j_3 = j_3 + 1U;

#line 2481
                            }

#line 2481
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2481
                            uint d_4 = 0U;

#line 2481
                            for(;;)
                            {

#line 2481
                                if(d_4 < 16U)
                                {
                                }
                                else
                                {

#line 2481
                                    break;
                                }

#line 2481
                                r_3[d_4] = float2(xr_0[d_4], (as_type<float>(((*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + src_0[d_4]]))));

#line 2481
                                d_4 = d_4 + 1U;

#line 2481
                            }

#line 2481
                            break;
                        }

#line 2481
                        break;
                    }

#line 2481
                    break;
                }

#line 2481
                for(;;)
                {

#line 2481
                    for(;;)
                    {

#line 2481
                        uint lgTB_1 = firstbithigh_0(8U);

#line 2481
                        uint blk_2 = tid_0 >> lgTB_1;

#line 2481
                        uint lane_2 = tid_0 & 7U;

#line 2481
                        dft16_0(&r_3);

#line 2481
                        float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 128.0f);

#line 2481
                        float _S27 = tw_1.x;

#line 2481
                        float _S28 = tw_1.y;

#line 2481
                        uint k2_2 = 0U;

#line 2481
                        float cr_1 = 1.0f;

#line 2481
                        float ci_1 = 0.0f;

#line 2481
                        for(;;)
                        {

#line 2481
                            if(k2_2 < 16U)
                            {
                            }
                            else
                            {

#line 2481
                                break;
                            }

#line 2481
                            r_3[k2_2] = cmul_0(r_3[k2_2], float2(cr_1, ci_1));

#line 2481
                            float nr_1 = cr_1 * _S27 - ci_1 * _S28;

#line 2481
                            float _S29 = cr_1 * _S28 + ci_1 * _S27;

#line 2481
                            k2_2 = k2_2 + 1U;

#line 2481
                            cr_1 = nr_1;

#line 2481
                            ci_1 = _S29;

#line 2481
                        }

#line 2481
                        uint per_2 = 16U / _S15;

#line 2481
                        uint _S30 = max(0U, 1U);

#line 2481
                        uint blk2_2 = tid_0 / _S30;

#line 2481
                        uint lane2_2 = tid_0 % _S30;

#line 2481
                        for(;;)
                        {

#line 2481
                            uint _S31 = (1U << lgTB_1) - 1U;

#line 2481
                            thread array<uint, int(16)> src_1;

#line 2481
                            uint d_5 = 0U;

#line 2481
                            for(;;)
                            {

#line 2481
                                if(d_5 < 16U)
                                {
                                }
                                else
                                {

#line 2481
                                    break;
                                }

#line 2481
                                uint p_1 = computeWant_0(d_5, 8U, 128U, blk_2, lane_2, per_2, _S30, 8U, blk2_2, lane2_2);

#line 2481
                                uint rem_1 = p_1 & _S16;

#line 2481
                                src_1[d_5] = (rem_1 >> lgTB_1) * 128U + ((p_1 >> _S14) << lgTB_1) + (rem_1 & _S31);

#line 2481
                                d_5 = d_5 + 1U;

#line 2481
                            }

#line 2481
                            thread array<float, int(16)> xr_1;

#line 2481
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2481
                            uint j_4 = 0U;

#line 2481
                            for(;;)
                            {

#line 2481
                                if(j_4 < 16U)
                                {
                                }
                                else
                                {

#line 2481
                                    break;
                                }

#line 2481
                                (*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + j_4 * 128U + (&kernelContext_0)->_tid_0] = (as_type<uint>((r_3[j_4].x)));

#line 2481
                                j_4 = j_4 + 1U;

#line 2481
                            }

#line 2481
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2481
                            uint d_6 = 0U;

#line 2481
                            for(;;)
                            {

#line 2481
                                if(d_6 < 16U)
                                {
                                }
                                else
                                {

#line 2481
                                    break;
                                }

#line 2481
                                xr_1[d_6] = (as_type<float>(((*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + src_1[d_6]])));

#line 2481
                                d_6 = d_6 + 1U;

#line 2481
                            }

#line 2481
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2481
                            uint j_5 = 0U;

#line 2481
                            for(;;)
                            {

#line 2481
                                if(j_5 < 16U)
                                {
                                }
                                else
                                {

#line 2481
                                    break;
                                }

#line 2481
                                (*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + j_5 * 128U + (&kernelContext_0)->_tid_0] = (as_type<uint>((r_3[j_5].y)));

#line 2481
                                j_5 = j_5 + 1U;

#line 2481
                            }

#line 2481
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2481
                            uint d_7 = 0U;

#line 2481
                            for(;;)
                            {

#line 2481
                                if(d_7 < 16U)
                                {
                                }
                                else
                                {

#line 2481
                                    break;
                                }

#line 2481
                                r_3[d_7] = float2(xr_1[d_7], (as_type<float>(((*(&kernelContext_0)->stg_0)[(&kernelContext_0)->_stgBase_0 + src_1[d_7]]))));

#line 2481
                                d_7 = d_7 + 1U;

#line 2481
                            }

#line 2481
                            break;
                        }

#line 2481
                        break;
                    }

#line 2481
                    break;
                }

#line 2481
                break;
            }

#line 2481
            innermost_0(&r_3);

#line 2481
            break;
        }

#line 2481
        uint k_2 = 0U;
        for(;;)
        {

#line 2482
            if(k_2 < 16U)
            {
            }
            else
            {

#line 2482
                break;
            }

#line 2482
            *((&kernelContext_0)->entryPointParams_spectra_0+(row_0 * 2048U + slotToIndex_0(tid_0 * 16U + k_2))) = packed_float2(float2(r_3[k_2].x, - r_3[k_2].y)) ;

#line 2482
            k_2 = k_2 + 1U;

#line 2482
        }



        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2470
        item_0 = item_0 + (&kernelContext_0)->entryPointParams_0->gridSize_0;

#line 2470
    }

#line 2488
    return;
}
