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


#line 2161 "bands.slang"
float2 seriesSample_0(packed_float2 device* series_0, uint i_0, uint layout_0)
{
    if(layout_0 == 0U)
    {

#line 2164
        return float2(*(series_0+i_0)) ;
    }

#line 2165
    uint f_0 = (layout_0 >> 2U) + (layout_0 & 3U) * i_0;

#line 2165
    float2 _S2 = float2(*(series_0+(f_0 >> 1U))) ;

#line 2165
    float _S3;

    if((f_0 & 1U) != 0U)
    {

#line 2167
        _S3 = _S2.y;

#line 2167
    }
    else
    {

#line 2167
        _S3 = _S2.x;

#line 2167
    }

#line 2167
    return float2(_S3, 0.0f);
}


#line 127 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 317 "bands.slang"
float2 cmul_0(float2 a_0, float2 b_0)
{

#line 317
    float _S4 = a_0.x;

#line 317
    float _S5 = b_0.x;

#line 317
    float _S6 = a_0.y;

#line 317
    float _S7 = b_0.y;

#line 317
    return float2(_S4 * _S5 - _S6 * _S7, _S4 * _S7 + _S6 * _S5);
}


#line 523
void r4_0(float2 thread* a_1, float2 thread* b_1, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 525
    float2 t1_0 = *a_1 - *c_0;

#line 525
    float2 t2_0 = *b_1 + *d_0;

#line 525
    float2 t3_0 = *b_1 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 527
    *b_1 = t1_0 + j3_0;

#line 527
    *c_0 = t0_0 - t2_0;

#line 527
    *d_0 = t1_0 - j3_0;
    return;
}


#line 559
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 566
    uint n1_0 = 0U;
    for(;;)
    {

#line 567
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 567
            break;
        }

#line 567
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 567
        n1_0 = n1_0 + 1U;

#line 567
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 568
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 568
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 569
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 569
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 570
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 570
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 570
    uint k2_0 = 0U;
    for(;;)
    {

#line 571
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 571
            break;
        }

#line 571
        uint _S8 = 4U * k2_0;

#line 571
        r4_0(&(*r_0)[_S8], &(*r_0)[_S8 + 1U], &(*r_0)[_S8 + 2U], &(*r_0)[_S8 + 3U]);

#line 571
        k2_0 = k2_0 + 1U;

#line 571
    }

    float2 t_0 = (*r_0)[int(1)];

#line 573
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 573
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 574
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 574
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 575
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 575
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 576
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 576
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 577
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 577
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 578
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 578
    (*r_0)[int(14)] = t_5;
    return;
}


#line 605
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 607
    thread array<float2, int(16)> v_0;

#line 607
    uint j_0 = 0U;
    for(;;)
    {

#line 608
        if(j_0 < 16U)
        {
        }
        else
        {

#line 608
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        v_0[j_0] = cmul_0((*r_1)[j_0] - (*r_1)[j_0 + 16U], mfTwiddle_0(6.28318548202514648f * float(j_0) / 32.0f));

#line 608
        j_0 = j_0 + 1U;

#line 608
    }

#line 614
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 615
    uint k_0 = 0U;
    for(;;)
    {

#line 616
        if(k_0 < 16U)
        {
        }
        else
        {

#line 616
            break;
        }

#line 616
        uint _S9 = 2U * k_0;

#line 616
        (*r_1)[_S9] = u_0[k_0];

#line 616
        (*r_1)[_S9 + 1U] = v_0[k_0];

#line 616
        k_0 = k_0 + 1U;

#line 616
    }
    return;
}


#line 644
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 319
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S10 = max(TB_0, 1U);

#line 321
    uint j_1 = d_1 / _S10;

#line 321
    uint m_0 = d_1 % _S10;

#line 321
    uint _S11;
    if(TB_0 <= 32U)
    {

#line 322
        _S11 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 322
    }
    else
    {

#line 322
        _S11 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 322
    }

#line 322
    return _S11;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint seriesLength_0;
    uint B_0;
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
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 306
    uint _S12 = 2U * i_1;

#line 306
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S12] = (as_type<uint>((v_1.x)));

#line 306
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S12 + 1U] = (as_type<uint>((v_1.y)));

#line 306
    return;
}


#line 307
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 307
    uint _S13 = 2U * i_2;

#line 307
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S13]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S13 + 1U]))));
}


#line 748
void exchange_0(array<float2, int(32)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 749
    uint j_2;

#line 760
    thread array<float2, int(32)> out_0;

#line 760
    uint z_0 = 0U;
    for(;;)
    {

#line 761
        if(z_0 < 32U)
        {
        }
        else
        {

#line 761
            break;
        }

#line 761
        out_0[z_0] = float2(0.0f, 0.0f);

#line 761
        z_0 = z_0 + 1U;

#line 761
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S14 = p0_0 & lenMask_0;

#line 767
    uint _S15 = _S14 >> lgSpan_0;

#line 767
    uint _S16 = _S15 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);

#line 767
    uint c_1 = 0U;

    for(;;)
    {

#line 769
        if(c_1 < 8U)
        {
        }
        else
        {

#line 769
            break;
        }

#line 770
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 770
        j_2 = 0U;
        for(;;)
        {

#line 771
            if(j_2 < 4U)
            {
            }
            else
            {

#line 771
                break;
            }

#line 771
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 4U + j_2], kernelContext_2);

#line 771
            j_2 = j_2 + 1U;

#line 771
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 772
        uint d_2 = 0U;
        for(;;)
        {

#line 773
            if(d_2 < 32U)
            {
            }
            else
            {

#line 773
                break;
            }

#line 774
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S17 = pz_0 & lenMask_0;

#line 775
            uint iz_0 = _S17 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S17 & spanMask_0);
            uint i_3 = _S15 + iz_0;
            uint _S18 = c_1 * 4U;

#line 778
            bool _S19;

#line 778
            if(i_3 >= _S18)
            {

#line 778
                _S19 = i_3 < ((c_1 + 1U) * 4U);

#line 778
            }
            else
            {

#line 778
                _S19 = false;

#line 778
            }

#line 778
            if(_S19)
            {

#line 778
                float2 _S20 = stgGet_0(_S16 + az_0 - _S18 * 1024U, kernelContext_2);
                out_0[d_2] = _S20;

#line 778
            }

#line 773
            d_2 = d_2 + 1U;

#line 773
        }

#line 769
        c_1 = c_1 + 1U;

#line 769
    }

#line 769
    j_2 = 0U;

#line 782
    for(;;)
    {

#line 782
        if(j_2 < 32U)
        {
        }
        else
        {

#line 782
            break;
        }

#line 782
        (*r_3)[j_2] = out_0[j_2];

#line 782
        j_2 = j_2 + 1U;

#line 782
    }
    return;
}


#line 662
void innermost_0(array<float2, int(32)> thread* r_4)
{

    dft32_0(r_4);

#line 674
    return;
}


#line 2151
void forwardTransform_0(array<float2, int(32)> thread* r_5, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 2151
    uint _S21;

#line 2151
    uint k2_1;

#line 2151
    float cr_0;

#line 2151
    float ci_0;

#line 2151
    uint _S22;

#line 2151
    for(;;)
    {

#line 2151
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S21 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(32768U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;

#line 19
                dftR_0(r_5);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 32768.0f);
                float _S23 = tw_0.x;

#line 40
                float _S24 = tw_0.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 32U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_5)[k2_1] = cmul_0((*r_5)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S23 - ci_0 * _S24;
                    float _S25 = cr_0 * _S24 + ci_0 * _S23;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S25;

#line 42
                }

#line 50
                uint per_2 = 32U / max(1024U, 1U);
                uint _S26 = max(32U, 1U);

#line 51
                _S22 = _S26;
                uint blk2_2 = tid_0 / _S26;

#line 52
                uint lane2_2 = tid_0 % _S26;

#line 52
                exchange_0(r_5, lgLn_0, lgTB_0, 1024U, 32768U, blk_2, lane_2, per_2, _S26, 1024U, blk2_2, lane2_2, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        for(;;)
        {

#line 7
            for(;;)
            {


                uint lgTB_1 = firstbithigh_0(32U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 31U;

#line 19
                dftR_0(r_5);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 1024.0f);
                float _S27 = tw_1.x;

#line 40
                float _S28 = tw_1.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 32U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_5)[k2_1] = cmul_0((*r_5)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S27 - ci_0 * _S28;
                    float _S29 = cr_0 * _S28 + ci_0 * _S27;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S29;

#line 42
                }

#line 50
                uint per_3 = 32U / _S22;
                uint _S30 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S30;

#line 52
                uint lane2_3 = tid_0 % _S30;

#line 52
                exchange_0(r_5, _S21, lgTB_1, 32U, 1024U, blk_3, lane_3, per_3, _S30, 32U, blk2_3, lane2_3, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        break;
    }

#line 56
    innermost_0(r_5);

#line 2154 "bands.slang"
    return;
}


#line 807
uint lgOf_0(uint i_4)
{

#line 807
    uint _S31;

#line 807
    if(i_4 < 2U)
    {

#line 807
        _S31 = 5U;

#line 807
    }
    else
    {

#line 807
        if(i_4 == 2U)
        {

#line 807
            _S31 = 5U;

#line 807
        }
        else
        {

#line 807
            _S31 = 1U;

#line 807
        }

#line 807
    }

#line 807
    return _S31;
}


#line 809
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 813
    uint lg_1 = lgOf_0(1U);

#line 813
    uint lg_2 = lgOf_0(0U);

#line 818
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2215
[[kernel]] void seriesForwardBands(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_bands_1 [[buffer(3)]])
{

#line 2215
    thread KernelContext_0 kernelContext_4;

#line 2215
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 2215
    (&kernelContext_4)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2215
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2215
    (&kernelContext_4)->entryPointParams_bands_0 = entryPointParams_bands_1;

#line 2215
    threadgroup array<uint, int(8192)> stg_1;

#line 2215
    (&kernelContext_4)->stg_0 = &stg_1;

#line 2221
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    uint _S32 = gid_0.x;

#line 2224
    uint _S33 = entryPointParams_starts_1[_S32];
    thread array<float2, int(32)> r_6;

#line 2225
    uint k_1 = 0U;
    for(;;)
    {

#line 2226
        if(k_1 < 32U)
        {
        }
        else
        {

#line 2226
            break;
        }

#line 2227
        uint offset_0 = tid_1 + 1024U * k_1;
        float2 _S34 = float2(0.0f, 0.0f);

#line 2228
        bool _S35;
        if(_S33 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0))
        {

#line 2229
            _S35 = offset_0 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0 - _S33);

#line 2229
        }
        else
        {

#line 2229
            _S35 = false;

#line 2229
        }

#line 2229
        float2 x_1;

#line 2229
        if(_S35)
        {

#line 2229
            x_1 = seriesSample_0((&kernelContext_4)->entryPointParams_series_0, _S33 + offset_0, (&kernelContext_4)->entryPointParams_0->seriesLayout_0);

#line 2229
        }
        else
        {

#line 2229
            x_1 = _S34;

#line 2229
        }

        r_6[k_1] = float2(x_1.x / 32768.0f, - x_1.y / 32768.0f);

#line 2226
        k_1 = k_1 + 1U;

#line 2226
    }

#line 2226
    forwardTransform_0(&r_6, tid_1, &kernelContext_4);

#line 2226
    k_1 = 0U;

#line 2234
    for(;;)
    {

#line 2234
        if(k_1 < 32U)
        {
        }
        else
        {

#line 2234
            break;
        }

#line 2235
        uint index_0 = slotToIndex_0(tid_1 * 32U + k_1);
        if(index_0 < ((&kernelContext_4)->entryPointParams_0->B_0))
        {

#line 2236
            *((&kernelContext_4)->entryPointParams_bands_0+(_S32 * (&kernelContext_4)->entryPointParams_0->B_0 + index_0)) = packed_float2(float2(r_6[k_1].x, - r_6[k_1].y)) ;

#line 2236
        }

#line 2234
        k_1 = k_1 + 1U;

#line 2234
    }

#line 2239
    return;
}
