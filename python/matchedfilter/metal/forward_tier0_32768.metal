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


#line 103 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 323 "bands.slang"
float2 cmul_0(float2 a_0, float2 b_0)
{

#line 323
    float _S4 = a_0.x;

#line 323
    float _S5 = b_0.x;

#line 323
    float _S6 = a_0.y;

#line 323
    float _S7 = b_0.y;

#line 323
    return float2(_S4 * _S5 - _S6 * _S7, _S4 * _S7 + _S6 * _S5);
}


#line 610
void r4_0(float2 thread* a_1, float2 thread* b_1, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 612
    float2 t1_0 = *a_1 - *c_0;

#line 612
    float2 t2_0 = *b_1 + *d_0;

#line 612
    float2 t3_0 = *b_1 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 614
    *b_1 = t1_0 + j3_0;

#line 614
    *c_0 = t0_0 - t2_0;

#line 614
    *d_0 = t1_0 - j3_0;
    return;
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


#line 692
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 694
    thread array<float2, int(16)> v_0;

#line 694
    uint j_0 = 0U;
    for(;;)
    {

#line 695
        if(j_0 < 16U)
        {
        }
        else
        {

#line 695
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        v_0[j_0] = cmul_0((*r_1)[j_0] - (*r_1)[j_0 + 16U], mfTwiddle_0(6.28318548202514648f * float(j_0) / 32.0f));

#line 695
        j_0 = j_0 + 1U;

#line 695
    }

#line 701
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 702
    uint k_0 = 0U;
    for(;;)
    {

#line 703
        if(k_0 < 16U)
        {
        }
        else
        {

#line 703
            break;
        }

#line 703
        uint _S9 = 2U * k_0;

#line 703
        (*r_1)[_S9] = u_0[k_0];

#line 703
        (*r_1)[_S9 + 1U] = v_0[k_0];

#line 703
        k_0 = k_0 + 1U;

#line 703
    }
    return;
}


#line 731
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 325
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S10 = max(TB_0, 1U);

#line 327
    uint j_1 = d_1 / _S10;

#line 327
    uint m_0 = d_1 % _S10;

#line 327
    uint _S11;
    if(TB_0 <= 32U)
    {

#line 328
        _S11 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

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
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 312
    uint _S12 = 2U * i_1;

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S12] = (as_type<uint>((v_1.x)));

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S12 + 1U] = (as_type<uint>((v_1.y)));

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
void innermost_0(array<float2, int(32)> thread* r_3)
{

    dft32_0(r_3);

#line 761
    return;
}


#line 877
uint lgOf_0(uint i_3)
{

#line 877
    uint _S14;

#line 877
    if(i_3 < 2U)
    {

#line 877
        _S14 = 5U;

#line 877
    }
    else
    {

#line 877
        if(i_3 == 2U)
        {

#line 877
            _S14 = 5U;

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


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 883
    uint lg_1 = lgOf_0(1U);

#line 883
    uint lg_2 = lgOf_0(0U);

#line 888
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2510
[[kernel]] void forwardTier0(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], uint device* entryPointParams_band0_1 [[buffer(3)]], uint device* entryPointParams_band1_1 [[buffer(4)]])
{

#line 2510
    bool _S15;

#line 2510
    float2 x_1;

#line 2510
    uint _S16;

#line 2510
    uint k2_1;

#line 2510
    float cr_0;

#line 2510
    float ci_0;

#line 2510
    uint _S17;

#line 2510
    uint z_0;

#line 2510
    uint _S18;

#line 2510
    uint c_1;

#line 2510
    uint d_2;

#line 2510
    uint j_2;

#line 2510
    thread KernelContext_0 kernelContext_2;

#line 2510
    (&kernelContext_2)->entryPointParams_0 = entryPointParams_1;

#line 2510
    (&kernelContext_2)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2510
    (&kernelContext_2)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2510
    (&kernelContext_2)->entryPointParams_band0_0 = entryPointParams_band0_1;

#line 2510
    (&kernelContext_2)->entryPointParams_band1_0 = entryPointParams_band1_1;

#line 2510
    threadgroup array<uint, int(8192)> stg_1;

#line 2510
    (&kernelContext_2)->stg_0 = &stg_1;

#line 2519
    uint tid_0 = lid_0.x;
    (&kernelContext_2)->_tid_0 = tid_0;
    (&kernelContext_2)->_stgBase_0 = 0U;
    uint _S19 = gid_0.x;

#line 2522
    uint _S20 = entryPointParams_starts_1[_S19];
    thread array<float2, int(32)> r_4;

#line 2523
    uint k_1 = 0U;
    for(;;)
    {

#line 2524
        if(k_1 < 32U)
        {
        }
        else
        {

#line 2524
            break;
        }

#line 2525
        uint offset_0 = tid_0 + 1024U * k_1;
        float2 _S21 = float2(0.0f, 0.0f);
        if(_S20 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0))
        {

#line 2527
            _S15 = offset_0 < ((&kernelContext_2)->entryPointParams_0->seriesLength_0 - _S20);

#line 2527
        }
        else
        {

#line 2527
            _S15 = false;

#line 2527
        }

#line 2527
        if(_S15)
        {

#line 2527
            x_1 = seriesSample_0((&kernelContext_2)->entryPointParams_series_0, _S20 + offset_0, (&kernelContext_2)->entryPointParams_0->seriesLayout_0);

#line 2527
        }
        else
        {

#line 2527
            x_1 = _S21;

#line 2527
        }

        r_4[k_1] = float2(x_1.x / 32768.0f, - x_1.y / 32768.0f);

#line 2524
        k_1 = k_1 + 1U;

#line 2524
    }

#line 2531
    for(;;)
    {

#line 2531
        for(;;)
        {

#line 2531
            for(;;)
            {

#line 2531
                for(;;)
                {

#line 2531
                    uint lgTB_0 = firstbithigh_0(1024U);

#line 2531
                    _S16 = lgTB_0;

#line 2531
                    uint lgLn_0 = firstbithigh_0(32768U);

#line 2531
                    uint blk_1 = tid_0 >> lgTB_0;

#line 2531
                    uint lane_1 = tid_0 & 1023U;

#line 2531
                    dftR_0(&r_4);

#line 2531
                    float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_1) / 32768.0f);

#line 2531
                    float _S22 = tw_0.x;

#line 2531
                    float _S23 = tw_0.y;

#line 2531
                    k2_1 = 0U;

#line 2531
                    cr_0 = 1.0f;

#line 2531
                    ci_0 = 0.0f;

#line 2531
                    for(;;)
                    {

#line 2531
                        if(k2_1 < 32U)
                        {
                        }
                        else
                        {

#line 2531
                            break;
                        }

#line 2531
                        r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 2531
                        float nr_0 = cr_0 * _S22 - ci_0 * _S23;

#line 2531
                        float _S24 = cr_0 * _S23 + ci_0 * _S22;

#line 2531
                        k2_1 = k2_1 + 1U;

#line 2531
                        cr_0 = nr_0;

#line 2531
                        ci_0 = _S24;

#line 2531
                    }

#line 2531
                    uint per_1 = 32U / max(1024U, 1U);

#line 2531
                    uint _S25 = max(32U, 1U);

#line 2531
                    _S17 = _S25;

#line 2531
                    uint blk2_1 = tid_0 / _S25;

#line 2531
                    uint lane2_1 = tid_0 % _S25;

#line 2531
                    for(;;)
                    {

#line 2531
                        thread array<float2, int(32)> out_0;

#line 2531
                        z_0 = 0U;

#line 2531
                        for(;;)
                        {

#line 2531
                            if(z_0 < 32U)
                            {
                            }
                            else
                            {

#line 2531
                                break;
                            }

#line 2531
                            out_0[z_0] = float2(0.0f, 0.0f);

#line 2531
                            z_0 = z_0 + 1U;

#line 2531
                        }

#line 2531
                        uint spanMask_0 = (1U << lgTB_0) - 1U;

#line 2531
                        _S18 = spanMask_0;

#line 2531
                        uint lenMask_0 = (1U << lgLn_0) - 1U;

#line 2531
                        uint p0_0 = computeWant_0(0U, 1024U, 32768U, blk_1, lane_1, per_1, _S25, 1024U, blk2_1, lane2_1);

#line 2531
                        uint _S26 = p0_0 & lenMask_0;

#line 2531
                        uint _S27 = _S26 >> lgTB_0;

#line 2531
                        uint _S28 = _S27 * 1024U + ((p0_0 >> lgLn_0) << lgTB_0) + (_S26 & spanMask_0);

#line 2531
                        c_1 = 0U;

#line 2531
                        for(;;)
                        {

#line 2531
                            if(c_1 < 8U)
                            {
                            }
                            else
                            {

#line 2531
                                break;
                            }

#line 2531
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2531
                            j_2 = 0U;

#line 2531
                            for(;;)
                            {

#line 2531
                                if(j_2 < 4U)
                                {
                                }
                                else
                                {

#line 2531
                                    break;
                                }

#line 2531
                                stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_4[c_1 * 4U + j_2], &kernelContext_2);

#line 2531
                                j_2 = j_2 + 1U;

#line 2531
                            }

#line 2531
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2531
                            d_2 = 0U;

#line 2531
                            for(;;)
                            {

#line 2531
                                if(d_2 < 32U)
                                {
                                }
                                else
                                {

#line 2531
                                    break;
                                }

#line 2531
                                uint pz_0 = computeWant_0(d_2, 1024U, 32768U, 0U, 0U, per_1, _S25, 1024U, 0U, 0U);

#line 2531
                                uint _S29 = pz_0 & lenMask_0;

#line 2531
                                uint iz_0 = _S29 >> lgTB_0;

#line 2531
                                uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLn_0) << lgTB_0) + (_S29 & spanMask_0);

#line 2531
                                uint i_4 = _S27 + iz_0;

#line 2531
                                uint _S30 = c_1 * 4U;

#line 2531
                                if(i_4 >= _S30)
                                {

#line 2531
                                    _S15 = i_4 < ((c_1 + 1U) * 4U);

#line 2531
                                }
                                else
                                {

#line 2531
                                    _S15 = false;

#line 2531
                                }

#line 2531
                                if(_S15)
                                {

#line 2531
                                    float2 _S31 = stgGet_0(_S28 + az_0 - _S30 * 1024U, &kernelContext_2);

#line 2531
                                    out_0[d_2] = _S31;

#line 2531
                                }

#line 2531
                                d_2 = d_2 + 1U;

#line 2531
                            }

#line 2531
                            c_1 = c_1 + 1U;

#line 2531
                        }

#line 2531
                        d_2 = 0U;

#line 2531
                        for(;;)
                        {

#line 2531
                            if(d_2 < 32U)
                            {
                            }
                            else
                            {

#line 2531
                                break;
                            }

#line 2531
                            r_4[d_2] = out_0[d_2];

#line 2531
                            d_2 = d_2 + 1U;

#line 2531
                        }

#line 2531
                        break;
                    }

#line 2531
                    break;
                }

#line 2531
                break;
            }

#line 2531
            for(;;)
            {

#line 2531
                for(;;)
                {

#line 2531
                    uint lgTB_1 = firstbithigh_0(32U);

#line 2531
                    uint blk_2 = tid_0 >> lgTB_1;

#line 2531
                    uint lane_2 = tid_0 & 31U;

#line 2531
                    dftR_0(&r_4);

#line 2531
                    float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 1024.0f);

#line 2531
                    float _S32 = tw_1.x;

#line 2531
                    float _S33 = tw_1.y;

#line 2531
                    k2_1 = 0U;

#line 2531
                    cr_0 = 1.0f;

#line 2531
                    ci_0 = 0.0f;

#line 2531
                    for(;;)
                    {

#line 2531
                        if(k2_1 < 32U)
                        {
                        }
                        else
                        {

#line 2531
                            break;
                        }

#line 2531
                        r_4[k2_1] = cmul_0(r_4[k2_1], float2(cr_0, ci_0));

#line 2531
                        float nr_1 = cr_0 * _S32 - ci_0 * _S33;

#line 2531
                        float _S34 = cr_0 * _S33 + ci_0 * _S32;

#line 2531
                        k2_1 = k2_1 + 1U;

#line 2531
                        cr_0 = nr_1;

#line 2531
                        ci_0 = _S34;

#line 2531
                    }

#line 2531
                    uint per_2 = 32U / _S17;

#line 2531
                    uint _S35 = max(1U, 1U);

#line 2531
                    uint blk2_2 = tid_0 / _S35;

#line 2531
                    uint lane2_2 = tid_0 % _S35;

#line 2531
                    for(;;)
                    {

#line 2531
                        thread array<float2, int(32)> out_1;

#line 2531
                        z_0 = 0U;

#line 2531
                        for(;;)
                        {

#line 2531
                            if(z_0 < 32U)
                            {
                            }
                            else
                            {

#line 2531
                                break;
                            }

#line 2531
                            out_1[z_0] = float2(0.0f, 0.0f);

#line 2531
                            z_0 = z_0 + 1U;

#line 2531
                        }

#line 2531
                        uint spanMask_1 = (1U << lgTB_1) - 1U;

#line 2531
                        uint p0_1 = computeWant_0(0U, 32U, 1024U, blk_2, lane_2, per_2, _S35, 32U, blk2_2, lane2_2);

#line 2531
                        uint _S36 = p0_1 & _S18;

#line 2531
                        uint _S37 = _S36 >> lgTB_1;

#line 2531
                        uint _S38 = _S37 * 1024U + ((p0_1 >> _S16) << lgTB_1) + (_S36 & spanMask_1);

#line 2531
                        c_1 = 0U;

#line 2531
                        for(;;)
                        {

#line 2531
                            if(c_1 < 8U)
                            {
                            }
                            else
                            {

#line 2531
                                break;
                            }

#line 2531
                            bool _S39 = c_1 == 0U;

#line 2531
                            if(!_S39)
                            {

#line 2531
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2531
                            }
                            else
                            {

#line 2531
                                threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2531
                            }

#line 2531
                            j_2 = 0U;

#line 2531
                            for(;;)
                            {

#line 2531
                                if(j_2 < 4U)
                                {
                                }
                                else
                                {

#line 2531
                                    break;
                                }

#line 2531
                                stgPut_0(j_2 * 1024U + (&kernelContext_2)->_tid_0, r_4[c_1 * 4U + j_2], &kernelContext_2);

#line 2531
                                j_2 = j_2 + 1U;

#line 2531
                            }

#line 2531
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2531
                            d_2 = 0U;

#line 2531
                            for(;;)
                            {

#line 2531
                                if(d_2 < 32U)
                                {
                                }
                                else
                                {

#line 2531
                                    break;
                                }

#line 2531
                                uint pz_1 = computeWant_0(d_2, 32U, 1024U, 0U, 0U, per_2, _S35, 32U, 0U, 0U);

#line 2531
                                uint _S40 = pz_1 & _S18;

#line 2531
                                uint iz_1 = _S40 >> lgTB_1;

#line 2531
                                uint az_1 = iz_1 * 1024U + ((pz_1 >> _S16) << lgTB_1) + (_S40 & spanMask_1);

#line 2531
                                uint i_5 = _S37 + iz_1;

#line 2531
                                uint _S41 = c_1 * 4U;

#line 2531
                                if(i_5 >= _S41)
                                {

#line 2531
                                    _S15 = i_5 < ((c_1 + 1U) * 4U);

#line 2531
                                }
                                else
                                {

#line 2531
                                    _S15 = false;

#line 2531
                                }

#line 2531
                                if(_S15)
                                {

#line 2531
                                    float2 _S42 = stgGet_0(_S38 + az_1 - _S41 * 1024U, &kernelContext_2);

#line 2531
                                    out_1[d_2] = _S42;

#line 2531
                                }

#line 2531
                                d_2 = d_2 + 1U;

#line 2531
                            }

#line 2531
                            c_1 = c_1 + 1U;

#line 2531
                        }

#line 2531
                        d_2 = 0U;

#line 2531
                        for(;;)
                        {

#line 2531
                            if(d_2 < 32U)
                            {
                            }
                            else
                            {

#line 2531
                                break;
                            }

#line 2531
                            r_4[d_2] = out_1[d_2];

#line 2531
                            d_2 = d_2 + 1U;

#line 2531
                        }

#line 2531
                        break;
                    }

#line 2531
                    break;
                }

#line 2531
                break;
            }

#line 2531
            break;
        }

#line 2531
        innermost_0(&r_4);

#line 2531
        break;
    }

#line 2531
    k_1 = 0U;
    for(;;)
    {

#line 2532
        if(k_1 < 32U)
        {
        }
        else
        {

#line 2532
            break;
        }

#line 2533
        uint index_0 = slotToIndex_0(tid_0 * 32U + k_1);
        float _S43 = r_4[k_1].x;

#line 2534
        float _S44 = - r_4[k_1].y;

#line 2534
        float2 v_2 = float2(_S43, _S44);
        if(((&kernelContext_2)->entryPointParams_0->k0_0_0) == 0U)
        {

#line 2536
            if(index_0 < ((&kernelContext_2)->entryPointParams_0->B0_0))
            {

#line 2537
                float s_0 = (as_type<float>(((&kernelContext_2)->entryPointParams_0->scaleBits_0)));
                *((&kernelContext_2)->entryPointParams_band0_0+(_S19 * (&kernelContext_2)->entryPointParams_0->B0_0 + index_0)) = (as_type<ushort>((half)((_S43 * s_0)))) | ((as_type<ushort>((half)((_S44 * s_0)))) << 16U);

#line 2536
            }

#line 2535
        }
        else
        {


            if(index_0 >= ((&kernelContext_2)->entryPointParams_0->k0_0_0))
            {

#line 2540
                _S15 = index_0 < ((&kernelContext_2)->entryPointParams_0->k0_0_0 + (&kernelContext_2)->entryPointParams_0->B0_0);

#line 2540
            }
            else
            {

#line 2540
                _S15 = false;

#line 2540
            }

#line 2540
            if(_S15)
            {
                if(index_0 < 16384U)
                {

#line 2543
                    float s_1 = (as_type<float>(((&kernelContext_2)->entryPointParams_0->scaleBits_0)));

#line 2543
                    j_2 = (as_type<ushort>((half)((_S43 * s_1)))) | ((as_type<ushort>((half)((_S44 * s_1)))) << 16U);

#line 2542
                }
                else
                {

#line 2542
                    j_2 = 0U;

#line 2542
                }



                *((&kernelContext_2)->entryPointParams_band0_0+(_S19 * (&kernelContext_2)->entryPointParams_0->B0_0 + (index_0 & ((&kernelContext_2)->entryPointParams_0->B0_0 - 1U)))) = j_2;

#line 2540
            }

#line 2535
        }

#line 2548
        if(((&kernelContext_2)->entryPointParams_0->k0_1_0) == 0U)
        {

#line 2549
            if(index_0 < ((&kernelContext_2)->entryPointParams_0->B1_0))
            {

#line 2550
                uint dst1_0 = _S19 * (&kernelContext_2)->entryPointParams_0->B1_0 + index_0;
                if(((&kernelContext_2)->entryPointParams_0->scaleBits1_0) != 0U)
                {

#line 2552
                    float s1_0 = (as_type<float>(((&kernelContext_2)->entryPointParams_0->scaleBits1_0)));
                    *((&kernelContext_2)->entryPointParams_band1_0+dst1_0) = (as_type<ushort>((half)((_S43 * s1_0)))) | ((as_type<ushort>((half)((_S44 * s1_0)))) << 16U);

#line 2551
                }
                else
                {

                    uint _S45 = 2U * dst1_0;

#line 2555
                    *((&kernelContext_2)->entryPointParams_band1_0+_S45) = (as_type<uint>((_S43)));
                    *((&kernelContext_2)->entryPointParams_band1_0+(_S45 + 1U)) = (as_type<uint>((_S44)));

#line 2551
                }

#line 2549
            }

#line 2548
        }
        else
        {

#line 2559
            if(((&kernelContext_2)->entryPointParams_0->B1_0) > 0U)
            {

#line 2559
                _S15 = index_0 >= ((&kernelContext_2)->entryPointParams_0->k0_1_0);

#line 2559
            }
            else
            {

#line 2559
                _S15 = false;

#line 2559
            }

#line 2559
            bool _S46;

#line 2559
            if(_S15)
            {

#line 2559
                _S46 = index_0 < ((&kernelContext_2)->entryPointParams_0->k0_1_0 + (&kernelContext_2)->entryPointParams_0->B1_0);

#line 2559
            }
            else
            {

#line 2559
                _S46 = false;

#line 2559
            }

#line 2559
            if(_S46)
            {

#line 2560
                uint dst1_1 = _S19 * (&kernelContext_2)->entryPointParams_0->B1_0 + (index_0 & ((&kernelContext_2)->entryPointParams_0->B1_0 - 1U));
                if(((&kernelContext_2)->entryPointParams_0->scaleBits1_0) != 0U)
                {
                    if(index_0 < 16384U)
                    {

#line 2564
                        float s1_1 = (as_type<float>(((&kernelContext_2)->entryPointParams_0->scaleBits1_0)));

#line 2564
                        j_2 = (as_type<ushort>((half)((_S43 * s1_1)))) | ((as_type<ushort>((half)((_S44 * s1_1)))) << 16U);

#line 2563
                    }
                    else
                    {

#line 2563
                        j_2 = 0U;

#line 2563
                    }



                    *((&kernelContext_2)->entryPointParams_band1_0+dst1_1) = j_2;

#line 2561
                }
                else
                {

#line 2569
                    if(index_0 < 16384U)
                    {

#line 2569
                        x_1 = v_2;

#line 2569
                    }
                    else
                    {

#line 2569
                        x_1 = float2(0.0f, 0.0f);

#line 2569
                    }
                    uint _S47 = 2U * dst1_1;

#line 2570
                    *((&kernelContext_2)->entryPointParams_band1_0+_S47) = (as_type<uint>((x_1.x)));
                    *((&kernelContext_2)->entryPointParams_band1_0+(_S47 + 1U)) = (as_type<uint>((x_1.y)));

#line 2561
                }

#line 2559
            }

#line 2548
        }

#line 2532
        k_1 = k_1 + 1U;

#line 2532
    }

#line 2575
    return;
}
