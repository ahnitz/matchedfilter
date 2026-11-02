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


#line 2339 "bands.slang"
float2 seriesSample_0(packed_float2 device* series_0, uint i_0, uint layout_0)
{
    if(layout_0 == 0U)
    {

#line 2342
        return float2(*(series_0+i_0)) ;
    }

#line 2343
    uint f_0 = (layout_0 >> 2U) + (layout_0 & 3U) * i_0;

#line 2343
    float2 _S2 = float2(*(series_0+(f_0 >> 1U))) ;

#line 2343
    float _S3;

    if((f_0 & 1U) != 0U)
    {

#line 2345
        _S3 = _S2.y;

#line 2345
    }
    else
    {

#line 2345
        _S3 = _S2.x;

#line 2345
    }

#line 2345
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


#line 103 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 323 "bands.slang"
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


#line 710
void dft64_0(array<float2, int(64)> thread* r_1)
{

#line 710
    uint k_0;

#line 710
    uint j_0 = 0U;

    for(;;)
    {

#line 712
        if(j_0 < 16U)
        {
        }
        else
        {

#line 712
            break;
        }

#line 713
        r4_0(&(*r_1)[j_0], &(*r_1)[j_0 + 16U], &(*r_1)[j_0 + 32U], &(*r_1)[j_0 + 48U]);

#line 712
        j_0 = j_0 + 1U;

#line 712
    }

    thread array<float2, int(64)> o_0;

#line 714
    uint pp_0 = 0U;
    for(;;)
    {

#line 715
        if(pp_0 < 4U)
        {
        }
        else
        {

#line 715
            break;
        }

#line 716
        thread array<float2, int(16)> b_2;

#line 716
        j_0 = 0U;
        for(;;)
        {

#line 717
            if(j_0 < 16U)
            {
            }
            else
            {

#line 717
                break;
            }
            b_2[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f));

#line 717
            j_0 = j_0 + 1U;

#line 717
        }



        dft16_0(&b_2);

#line 721
        k_0 = 0U;
        for(;;)
        {

#line 722
            if(k_0 < 16U)
            {
            }
            else
            {

#line 722
                break;
            }

#line 722
            o_0[4U * k_0 + pp_0] = b_2[k_0];

#line 722
            k_0 = k_0 + 1U;

#line 722
        }

#line 715
        pp_0 = pp_0 + 1U;

#line 715
    }

#line 715
    k_0 = 0U;

#line 724
    for(;;)
    {

#line 724
        if(k_0 < 64U)
        {
        }
        else
        {

#line 724
            break;
        }

#line 724
        (*r_1)[k_0] = o_0[k_0];

#line 724
        k_0 = k_0 + 1U;

#line 724
    }
    return;
}


void dftR_0(array<float2, int(64)> thread* r_2)
{

#line 736
    dft64_0(r_2);

    return;
}


#line 325
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S9 = max(TB_0, 1U);

#line 327
    uint j_1 = d_1 / _S9;

#line 327
    uint m_0 = d_1 % _S9;

#line 327
    uint _S10;
    if(TB_0 <= 64U)
    {

#line 328
        _S10 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

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
    uint B0_0;
    uint B1_0;
    uint scaleBits_0;
    uint scaleBits1_0;
    uint k0_0_0;
    uint k0_1_0;
    uint seriesLayout_0;
};


#line 312 "bands.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    uint device* entryPointParams_band0_0;
    uint device* entryPointParams_band1_0;
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


#line 669
void dft16at_0(array<float2, int(64)> thread* r_3, uint o_1)
{



    thread array<float2, int(16)> b_3;

#line 674
    uint i_3 = 0U;
    for(;;)
    {

#line 675
        if(i_3 < 16U)
        {
        }
        else
        {

#line 675
            break;
        }

#line 675
        b_3[i_3] = (*r_3)[o_1 + i_3];

#line 675
        i_3 = i_3 + 1U;

#line 675
    }
    dft16_0(&b_3);

#line 676
    i_3 = 0U;
    for(;;)
    {

#line 677
        if(i_3 < 16U)
        {
        }
        else
        {

#line 677
            break;
        }

#line 677
        (*r_3)[o_1 + i_3] = b_3[i_3];

#line 677
        i_3 = i_3 + 1U;

#line 677
    }

    return;
}


#line 747
void innermost_0(array<float2, int(64)> thread* r_4)
{

#line 747
    uint b_4 = 0U;

#line 752
    for(;;)
    {

#line 752
        if(b_4 < 4U)
        {
        }
        else
        {

#line 752
            break;
        }

#line 752
        dft16at_0(r_4, b_4 * 16U);

#line 752
        b_4 = b_4 + 1U;

#line 752
    }

#line 759
    return;
}


#line 875
uint lgOf_0(uint i_4)
{

#line 875
    uint _S13;

#line 875
    if(i_4 < 2U)
    {

#line 875
        _S13 = 6U;

#line 875
    }
    else
    {

#line 875
        if(i_4 == 2U)
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
    }

#line 875
    return _S13;
}


#line 877
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 881
    uint lg_1 = lgOf_0(1U);

#line 881
    uint lg_2 = lgOf_0(0U);

#line 886
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2508
[[kernel]] void forwardTier0(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], uint device* entryPointParams_band0_1 [[buffer(3)]], uint device* entryPointParams_band1_1 [[buffer(4)]])
{

#line 2508
    bool _S14;

#line 2508
    float2 x_1;

#line 2508
    uint _S15;

#line 2508
    uint k2_1;

#line 2508
    float cr_0;

#line 2508
    float ci_0;

#line 2508
    uint _S16;

#line 2508
    uint z_0;

#line 2508
    uint _S17;

#line 2508
    uint c_1;

#line 2508
    uint d_2;

#line 2508
    uint j_2;

#line 2508
    thread KernelContext_0 kernelContext_2;

#line 2508
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2508
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2508
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2508
    (&kernelContext_2)->entryPointParams_band0_0 = entryPointParams_band0_1;

#line 2508
    (&kernelContext_2)->entryPointParams_band1_0 = entryPointParams_band1_1;

#line 2508
    threadgroup array<uint, int(8192)> stg_1;

#line 2508
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2517
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S18 = gid_0.x;

#line 2520
    uint _S19 = entryPointParams_starts_1[_S18];
    thread array<float2, int(64)> r_5;

#line 2521
    uint k_1 = 0U;
    for(;;)
    {

#line 2522
        if(k_1 < 64U)
        {
        }
        else
        {

#line 2522
            break;
        }

#line 2523
        uint offset_0 = tid_0 + 1024U * k_1;
        float2 _S20 = float2(0.0f, 0.0f);
        if(_S19 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2525
            _S14 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S19);

#line 2525
        }
        else
        {

#line 2525
            _S14 = false;

#line 2525
        }

#line 2525
        if(_S14)
        {

#line 2525
            x_1 = seriesSample_0((&kernelContext_2)->entryPointParams_series_0, _S19 + offset_0, (&kernelContext_2)->entryPointParams_0->seriesLayout_0);

#line 2525
        }
        else
        {

#line 2525
            x_1 = _S20;

#line 2525
        }

        r_5[k_1] = float2(x_1.x / 6.5536e+04f, - x_1.y / 6.5536e+04f);

#line 2522
        k_1 = k_1 + 1U;

#line 2522
    }

#line 2529
    for(;;)
    {

#line 2529
        for(;;)
        {

#line 2529
            for(;;)
            {

#line 2529
                for(;;)
                {

#line 2529
                    uint lgTB_0 = firstbithigh_0(1024U);

#line 2529
                    _S15 = lgTB_0;

#line 2529
                    uint lgLn_0 = firstbithigh_0(65536U);

#line 2529
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2529
                    uint lane_1 = tid_0 & 1023U;

#line 2529
                    dftR_0(&r_5);

#line 2529
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 6.5536e+04f);

#line 2529
                    float _S21 = tw_0.x;

#line 2529
                    float _S22 = tw_0.y;

#line 2529
                    k2_1 = 0U;

#line 2529
                    cr_0 = 1.0f;

#line 2529
                    ci_0 = 0.0f;

#line 2529
                    for(;;)
                    {

#line 2529
                        if(k2_1 < 64U)
                        {
                        }
                        else
                        {

#line 2529
                            break;
                        }

#line 2529
                        r_5[k2_1] = cmul_0(r_5[k2_1], float2(cr_0, ci_0));

#line 2529
                        float nr_0 = cr_0 * _S21 - ci_0 * _S22;

#line 2529
                        float _S23 = cr_0 * _S22 + ci_0 * _S21;

#line 2529
                        k2_1 = k2_1 + 1U;

#line 2529
                        cr_0 = nr_0;

#line 2529
                        ci_0 = _S23;

#line 2529
                    }

#line 2529
                    uint per_1 = 64U / max(1024U, 1U);

#line 2529
                    uint _S24 = max(16U, 1U);

#line 2529
                    _S16 = _S24;

#line 2529
                    uint blk2_1 = tid_0 / _S24;

#line 2529
                    uint lane2_1 = tid_0 % _S24;

#line 2529
                    for(;;)
                    {

#line 2529
                        thread array<float2, int(64)> out_0;

#line 2529
                        z_0 = 0U;

#line 2529
                        for(;;)
                        {

#line 2529
                            if(z_0 < 64U)
                            {
                            }
                            else
                            {

#line 2529
                                break;
                            }

#line 2529
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2529
                            z_0 = z_0 + 1U;

#line 2529
                        }

#line 2529
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2529
                        _S17 = spanMask_0;

#line 2529
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2529
                        uint p0_0 = computeWant_0(0U, 1024U, 65536U, blk_1, lane_1, per_1, _S24, 1024U, blk2_1, lane2_1);

#line 2529
                        uint _S25 = p0_0 & lenMask_0;

#line 2529
                        uint _S26 = _S25 >> lgTB_0;

#line 2529
                        uint _S27 = _S26 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S25 & spanMask_0);

#line 2529
                        c_1 = 0U;

#line 2529
                        for(;;)
                        {

#line 2529
                            if(c_1 < 16U)
                            {
                            }
                            else
                            {

#line 2529
                                break;
                            }

#line 2529
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2529
                            j_2 = 0U;

#line 2529
                            for(;;)
                            {

#line 2529
                                if(j_2 < 4U)
                                {
                                }
                                else
                                {

#line 2529
                                    break;
                                }

#line 2529
                                stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_5[c_1 * 4U + j_2], &kernelContext_2);

#line 2529
                                j_2 = j_2 + 1U;

#line 2529
                            }

#line 2529
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2529
                            d_2 = 0U;

#line 2529
                            for(;;)
                            {

#line 2529
                                if(d_2 < 64U)
                                {
                                }
                                else
                                {

#line 2529
                                    break;
                                }

#line 2529
                                uint pz_0 = computeWant_0(d_2, 1024U, 65536U, 0U, 0U, per_1, _S24, 1024U, 0U, 0U);

#line 2529
                                uint _S28 = pz_0 & lenMask_0;

#line 2529
                                uint iz_0 = _S28 >> lgTB_0;

#line 2529
                                uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S28 & spanMask_0);

#line 2529
                                uint i_5 = _S26 + iz_0;

#line 2529
                                uint _S29 = c_1 * 4U;

#line 2529
                                if(i_5 >= _S29)
                                {

#line 2529
                                    _S14 = i_5 < ((c_1 + 1U) * 4U);

#line 2529
                                }
                                else
                                {

#line 2529
                                    _S14 = false;

#line 2529
                                }

#line 2529
                                if(_S14)
                                {

#line 2529
                                    float2 _S30 = stgGet_0(_S27 + az_0 - _S29 * 1024U, &kernelContext_2);

#line 2529
                                    out_0[d_2] = _S30;

#line 2529
                                }

#line 2529
                                d_2 = d_2 + 1U;

#line 2529
                            }

#line 2529
                            c_1 = c_1 + 1U;

#line 2529
                        }

#line 2529
                        d_2 = 0U;

#line 2529
                        for(;;)
                        {

#line 2529
                            if(d_2 < 64U)
                            {
                            }
                            else
                            {

#line 2529
                                break;
                            }

#line 2529
                            r_5[d_2] = out_0[d_2];

#line 2529
                            d_2 = d_2 + 1U;

#line 2529
                        }

#line 2529
                        break;
                    }

#line 2529
                    break;
                }

#line 2529
                break;
            }

#line 2529
            for(;;)
            {

#line 2529
                for(;;)
                {

#line 2529
                    uint lgTB_1 = firstbithigh_0(16U);

#line 2529
                    uint blk_2 = tid_0 >> lgTB_1;

#line 2529
                    uint lane_2 = tid_0 & 15U;

#line 2529
                    dftR_0(&r_5);

#line 2529
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 2529
                    float _S31 = tw_1.x;

#line 2529
                    float _S32 = tw_1.y;

#line 2529
                    k2_1 = 0U;

#line 2529
                    cr_0 = 1.0f;

#line 2529
                    ci_0 = 0.0f;

#line 2529
                    for(;;)
                    {

#line 2529
                        if(k2_1 < 64U)
                        {
                        }
                        else
                        {

#line 2529
                            break;
                        }

#line 2529
                        r_5[k2_1] = cmul_0(r_5[k2_1], float2(cr_0, ci_0));

#line 2529
                        float nr_1 = cr_0 * _S31 - ci_0 * _S32;

#line 2529
                        float _S33 = cr_0 * _S32 + ci_0 * _S31;

#line 2529
                        k2_1 = k2_1 + 1U;

#line 2529
                        cr_0 = nr_1;

#line 2529
                        ci_0 = _S33;

#line 2529
                    }

#line 2529
                    uint per_2 = 64U / _S16;

#line 2529
                    uint _S34 = max(0U, 1U);

#line 2529
                    uint blk2_2 = tid_0 / _S34;

#line 2529
                    uint lane2_2 = tid_0 % _S34;

#line 2529
                    for(;;)
                    {

#line 2529
                        thread array<float2, int(64)> out_1;

#line 2529
                        z_0 = 0U;

#line 2529
                        for(;;)
                        {

#line 2529
                            if(z_0 < 64U)
                            {
                            }
                            else
                            {

#line 2529
                                break;
                            }

#line 2529
                            out_1[z_0] = float2(0.0f, 0.0f);

#line 2529
                            z_0 = z_0 + 1U;

#line 2529
                        }

#line 2529
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2529
                        uint p0_1 = computeWant_0(0U, 16U, 1024U, blk_2, lane_2, per_2, _S34, 16U, blk2_2, lane2_2);

#line 2529
                        uint _S35 = p0_1 & _S17;

#line 2529
                        uint _S36 = _S35 >> lgTB_1;

#line 2529
                        uint _S37 = _S36 * 1024U + ((p0_1 >> _S15) << lgTB_1) + (_S35 & spanMask_1);

#line 2529
                        c_1 = 0U;

#line 2529
                        for(;;)
                        {

#line 2529
                            if(c_1 < 16U)
                            {
                            }
                            else
                            {

#line 2529
                                break;
                            }

#line 2529
                            bool _S38 = c_1 == 0U;

#line 2529
                            if(!_S38)
                            {

#line 2529
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2529
                            }
                            else
                            {

#line 2529
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2529
                            }

#line 2529
                            j_2 = 0U;

#line 2529
                            for(;;)
                            {

#line 2529
                                if(j_2 < 4U)
                                {
                                }
                                else
                                {

#line 2529
                                    break;
                                }

#line 2529
                                stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_5[c_1 * 4U + j_2], &kernelContext_2);

#line 2529
                                j_2 = j_2 + 1U;

#line 2529
                            }

#line 2529
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2529
                            d_2 = 0U;

#line 2529
                            for(;;)
                            {

#line 2529
                                if(d_2 < 64U)
                                {
                                }
                                else
                                {

#line 2529
                                    break;
                                }

#line 2529
                                uint pz_1 = computeWant_0(d_2, 16U, 1024U, 0U, 0U, per_2, _S34, 16U, 0U, 0U);

#line 2529
                                uint _S39 = pz_1 & _S17;

#line 2529
                                uint iz_1 = _S39 >> lgTB_1;

#line 2529
                                uint az_1 = iz_1 * 1024U + ((pz_1 >> _S15) << lgTB_1) + (_S39 & spanMask_1);

#line 2529
                                uint i_6 = _S36 + iz_1;

#line 2529
                                uint _S40 = c_1 * 4U;

#line 2529
                                if(i_6 >= _S40)
                                {

#line 2529
                                    _S14 = i_6 < ((c_1 + 1U) * 4U);

#line 2529
                                }
                                else
                                {

#line 2529
                                    _S14 = false;

#line 2529
                                }

#line 2529
                                if(_S14)
                                {

#line 2529
                                    float2 _S41 = stgGet_0(_S37 + az_1 - _S40 * 1024U, &kernelContext_2);

#line 2529
                                    out_1[d_2] = _S41;

#line 2529
                                }

#line 2529
                                d_2 = d_2 + 1U;

#line 2529
                            }

#line 2529
                            c_1 = c_1 + 1U;

#line 2529
                        }

#line 2529
                        d_2 = 0U;

#line 2529
                        for(;;)
                        {

#line 2529
                            if(d_2 < 64U)
                            {
                            }
                            else
                            {

#line 2529
                                break;
                            }

#line 2529
                            r_5[d_2] = out_1[d_2];

#line 2529
                            d_2 = d_2 + 1U;

#line 2529
                        }

#line 2529
                        break;
                    }

#line 2529
                    break;
                }

#line 2529
                break;
            }

#line 2529
            break;
        }

#line 2529
        innermost_0(&r_5);

#line 2529
        break;
    }

#line 2529
    k_1 = 0U;
    for(;;)
    {

#line 2530
        if(k_1 < 64U)
        {
        }
        else
        {

#line 2530
            break;
        }

#line 2531
        uint index_0 = slotToIndex_0(tid_0 * 64U + k_1);
        float _S42 = r_5[k_1].x;

#line 2532
        float _S43 = - r_5[k_1].y;

#line 2532
        float2 v_1 = float2(_S42, _S43);
        if(((&kernelContext_2)->entryPointParams_0->k0_0_0) == 0U)
        {

#line 2534
            if(index_0 < ((&kernelContext_2)->entryPointParams_0->B0_0))
            {

#line 2535
                float s_0 = (as_type<float>(((&kernelContext_2)->entryPointParams_0->scaleBits_0)));
                *((&kernelContext_2)->entryPointParams_band0_0+(_S18 * (&kernelContext_2)->entryPointParams_0->B0_0 + index_0)) = (as_type<ushort>((half)((_S42 * s_0)))) | ((as_type<ushort>((half)((_S43 * s_0)))) << 16U);

#line 2534
            }

#line 2533
        }
        else
        {


            if(index_0 >= ((&kernelContext_2)->entryPointParams_0->k0_0_0))
            {

#line 2538
                _S14 = index_0 < ((&kernelContext_2)->entryPointParams_0->k0_0_0 + (&kernelContext_2)->entryPointParams_0->B0_0);

#line 2538
            }
            else
            {

#line 2538
                _S14 = false;

#line 2538
            }

#line 2538
            if(_S14)
            {
                if(index_0 < 32768U)
                {

#line 2541
                    float s_1 = (as_type<float>(((&kernelContext_2)->entryPointParams_0->scaleBits_0)));

#line 2541
                    j_2 = (as_type<ushort>((half)((_S42 * s_1)))) | ((as_type<ushort>((half)((_S43 * s_1)))) << 16U);

#line 2540
                }
                else
                {

#line 2540
                    j_2 = 0U;

#line 2540
                }



                *((&kernelContext_2)->entryPointParams_band0_0+(_S18 * (&kernelContext_2)->entryPointParams_0->B0_0 + (index_0 & ((&kernelContext_2)->entryPointParams_0->B0_0 - 1U)))) = j_2;

#line 2538
            }

#line 2533
        }

#line 2546
        if(((&kernelContext_2)->entryPointParams_0->k0_1_0) == 0U)
        {

#line 2547
            if(index_0 < ((&kernelContext_2)->entryPointParams_0->B1_0))
            {

#line 2548
                uint dst1_0 = _S18 * (&kernelContext_2)->entryPointParams_0->B1_0 + index_0;
                if(((&kernelContext_2)->entryPointParams_0->scaleBits1_0) != 0U)
                {

#line 2550
                    float s1_0 = (as_type<float>(((&kernelContext_2)->entryPointParams_0->scaleBits1_0)));
                    *((&kernelContext_2)->entryPointParams_band1_0+dst1_0) = (as_type<ushort>((half)((_S42 * s1_0)))) | ((as_type<ushort>((half)((_S43 * s1_0)))) << 16U);

#line 2549
                }
                else
                {

                    uint _S44 = 2U * dst1_0;

#line 2553
                    *((&kernelContext_2)->entryPointParams_band1_0+_S44) = (as_type<uint>((_S42)));
                    *((&kernelContext_2)->entryPointParams_band1_0+(_S44 + 1U)) = (as_type<uint>((_S43)));

#line 2549
                }

#line 2547
            }

#line 2546
        }
        else
        {

#line 2557
            if(((&kernelContext_2)->entryPointParams_0->B1_0) > 0U)
            {

#line 2557
                _S14 = index_0 >= ((&kernelContext_2)->entryPointParams_0->k0_1_0);

#line 2557
            }
            else
            {

#line 2557
                _S14 = false;

#line 2557
            }

#line 2557
            bool _S45;

#line 2557
            if(_S14)
            {

#line 2557
                _S45 = index_0 < ((&kernelContext_2)->entryPointParams_0->k0_1_0 + (&kernelContext_2)->entryPointParams_0->B1_0);

#line 2557
            }
            else
            {

#line 2557
                _S45 = false;

#line 2557
            }

#line 2557
            if(_S45)
            {

#line 2558
                uint dst1_1 = _S18 * (&kernelContext_2)->entryPointParams_0->B1_0 + (index_0 & ((&kernelContext_2)->entryPointParams_0->B1_0 - 1U));
                if(((&kernelContext_2)->entryPointParams_0->scaleBits1_0) != 0U)
                {
                    if(index_0 < 32768U)
                    {

#line 2562
                        float s1_1 = (as_type<float>(((&kernelContext_2)->entryPointParams_0->scaleBits1_0)));

#line 2562
                        j_2 = (as_type<ushort>((half)((_S42 * s1_1)))) | ((as_type<ushort>((half)((_S43 * s1_1)))) << 16U);

#line 2561
                    }
                    else
                    {

#line 2561
                        j_2 = 0U;

#line 2561
                    }



                    *((&kernelContext_2)->entryPointParams_band1_0+dst1_1) = j_2;

#line 2559
                }
                else
                {

#line 2567
                    if(index_0 < 32768U)
                    {

#line 2567
                        x_1 = v_1;

#line 2567
                    }
                    else
                    {

#line 2567
                        x_1 = float2(0.0f, 0.0f);

#line 2567
                    }
                    uint _S46 = 2U * dst1_1;

#line 2568
                    *((&kernelContext_2)->entryPointParams_band1_0+_S46) = (as_type<uint>((x_1.x)));
                    *((&kernelContext_2)->entryPointParams_band1_0+(_S46 + 1U)) = (as_type<uint>((x_1.y)));

#line 2559
                }

#line 2557
            }

#line 2546
        }

#line 2530
        k_1 = k_1 + 1U;

#line 2530
    }

#line 2573
    return;
}
