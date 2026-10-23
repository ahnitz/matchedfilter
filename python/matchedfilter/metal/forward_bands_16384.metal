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


#line 523
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 525
    float2 t1_0 = *a_0 - *c_0;

#line 525
    float2 t2_0 = *b_0 + *d_0;

#line 525
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 527
    *b_0 = t1_0 + j3_0;

#line 527
    *c_0 = t0_0 - t2_0;

#line 527
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


#line 127 "twiddle.slang"
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


#line 748
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 749
    uint j_1;

#line 760
    thread array<float2, int(16)> out_0;

#line 760
    uint z_0 = 0U;
    for(;;)
    {

#line 761
        if(z_0 < 16U)
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
    uint _S13 = p0_0 & lenMask_0;

#line 767
    uint _S14 = _S13 >> lgSpan_0;

#line 767
    uint _S15 = _S14 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

#line 767
    uint c_1 = 0U;

    for(;;)
    {

#line 769
        if(c_1 < 4U)
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
        j_1 = 0U;
        for(;;)
        {

#line 771
            if(j_1 < 4U)
            {
            }
            else
            {

#line 771
                break;
            }

#line 771
            stgPut_0(j_1 * 1024U + kernelContext_2->_tid_0, (*r_1)[c_1 * 4U + j_1], kernelContext_2);

#line 771
            j_1 = j_1 + 1U;

#line 771
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 772
        uint d_2 = 0U;
        for(;;)
        {

#line 773
            if(d_2 < 16U)
            {
            }
            else
            {

#line 773
                break;
            }

#line 774
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S16 = pz_0 & lenMask_0;

#line 775
            uint iz_0 = _S16 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);
            uint i_3 = _S14 + iz_0;
            uint _S17 = c_1 * 4U;

#line 778
            bool _S18;

#line 778
            if(i_3 >= _S17)
            {

#line 778
                _S18 = i_3 < ((c_1 + 1U) * 4U);

#line 778
            }
            else
            {

#line 778
                _S18 = false;

#line 778
            }

#line 778
            if(_S18)
            {

#line 778
                float2 _S19 = stgGet_0(_S15 + az_0 - _S17 * 1024U, kernelContext_2);
                out_0[d_2] = _S19;

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
    j_1 = 0U;

#line 782
    for(;;)
    {

#line 782
        if(j_1 < 16U)
        {
        }
        else
        {

#line 782
            break;
        }

#line 782
        (*r_1)[j_1] = out_0[j_1];

#line 782
        j_1 = j_1 + 1U;

#line 782
    }
    return;
}


#line 538
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 541
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 541
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 662
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 662
    uint b_2 = 0U;

#line 671
    for(;;)
    {

#line 671
        if(b_2 < 4U)
        {
        }
        else
        {

#line 671
            break;
        }

#line 671
        dft4_0(r_3, b_2 * 4U);

#line 671
        b_2 = b_2 + 1U;

#line 671
    }


    return;
}


#line 2151
void forwardTransform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 2151
    uint _S20;

#line 2151
    uint k2_1;

#line 2151
    float cr_0;

#line 2151
    float ci_0;

#line 2151
    uint _S21;

#line 2151
    uint _S22;

#line 2151
    uint _S23;

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
                _S20 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(16384U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 16384.0f);
                float _S24 = tw_0.x;

#line 40
                float _S25 = tw_0.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S24 - ci_0 * _S25;
                    float _S26 = cr_0 * _S25 + ci_0 * _S24;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S26;

#line 42
                }

#line 50
                uint per_2 = 16U / max(1024U, 1U);
                uint _S27 = max(64U, 1U);

#line 51
                _S21 = _S27;
                uint blk2_2 = tid_0 / _S27;

#line 52
                uint lane2_2 = tid_0 % _S27;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 1024U, 16384U, blk_2, lane_2, per_2, _S27, 1024U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(64U);

#line 11
                _S22 = lgTB_1;

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 63U;


                dft16_0(r_4);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 1024.0f);
                float _S28 = tw_1.x;

#line 40
                float _S29 = tw_1.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S28 - ci_0 * _S29;
                    float _S30 = cr_0 * _S29 + ci_0 * _S28;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S30;

#line 42
                }

#line 50
                uint per_3 = 16U / _S21;
                uint _S31 = max(4U, 1U);

#line 51
                _S23 = _S31;
                uint blk2_3 = tid_0 / _S31;

#line 52
                uint lane2_3 = tid_0 % _S31;

#line 52
                exchange_0(r_4, _S20, lgTB_1, 64U, 1024U, blk_3, lane_3, per_3, _S31, 64U, blk2_3, lane2_3, kernelContext_3);

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


                uint lgTB_2 = firstbithigh_0(4U);

                uint blk_4 = tid_0 >> lgTB_2;
                uint lane_4 = tid_0 & 3U;


                dft16_0(r_4);

#line 39
                float2 tw_2 = mfTwiddle_0(6.28318548202514648f * float(lane_4) / 64.0f);
                float _S32 = tw_2.x;

#line 40
                float _S33 = tw_2.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_2 = cr_0 * _S32 - ci_0 * _S33;
                    float _S34 = cr_0 * _S33 + ci_0 * _S32;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_2;

#line 42
                    ci_0 = _S34;

#line 42
                }

#line 50
                uint per_4 = 16U / _S23;
                uint _S35 = max(0U, 1U);
                uint blk2_4 = tid_0 / _S35;

#line 52
                uint lane2_4 = tid_0 % _S35;

#line 52
                exchange_0(r_4, _S22, lgTB_2, 4U, 64U, blk_4, lane_4, per_4, _S35, 4U, blk2_4, lane2_4, kernelContext_3);

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
    innermost_0(r_4);

#line 2154 "bands.slang"
    return;
}


#line 807
uint lgOf_0(uint i_4)
{

#line 807
    uint _S36;

#line 807
    if(i_4 < 3U)
    {

#line 807
        _S36 = 4U;

#line 807
    }
    else
    {

#line 807
        _S36 = 1U;

#line 807
    }

#line 807
    return _S36;
}


#line 809
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(4U);

    uint x_0 = slot_0 >> lg_0;

#line 813
    uint lg_1 = lgOf_0(3U);

    uint x_1 = x_0 >> lg_1;

#line 813
    uint lg_2 = lgOf_0(2U);

    uint x_2 = x_1 >> lg_2;

#line 813
    uint lg_3 = lgOf_0(1U);

#line 813
    uint lg_4 = lgOf_0(0U);

#line 818
    return (((((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | (x_2 & ((1U << lg_3) - 1U))) << lg_4) | ((x_2 >> lg_3) & ((1U << lg_4) - 1U));
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
    uint _S37 = gid_0.x;

#line 2224
    uint _S38 = entryPointParams_starts_1[_S37];
    thread array<float2, int(16)> r_5;

#line 2225
    uint k_0 = 0U;
    for(;;)
    {

#line 2226
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2226
            break;
        }

#line 2227
        uint offset_0 = tid_1 + 1024U * k_0;
        float2 _S39 = float2(0.0f, 0.0f);

#line 2228
        bool _S40;
        if(_S38 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0))
        {

#line 2229
            _S40 = offset_0 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0 - _S38);

#line 2229
        }
        else
        {

#line 2229
            _S40 = false;

#line 2229
        }

#line 2229
        float2 x_3;

#line 2229
        if(_S40)
        {

#line 2229
            x_3 = seriesSample_0((&kernelContext_4)->entryPointParams_series_0, _S38 + offset_0, (&kernelContext_4)->entryPointParams_0->seriesLayout_0);

#line 2229
        }
        else
        {

#line 2229
            x_3 = _S39;

#line 2229
        }

        r_5[k_0] = float2(x_3.x / 16384.0f, - x_3.y / 16384.0f);

#line 2226
        k_0 = k_0 + 1U;

#line 2226
    }

#line 2226
    forwardTransform_0(&r_5, tid_1, &kernelContext_4);

#line 2226
    k_0 = 0U;

#line 2234
    for(;;)
    {

#line 2234
        if(k_0 < 16U)
        {
        }
        else
        {

#line 2234
            break;
        }

#line 2235
        uint index_0 = slotToIndex_0(tid_1 * 16U + k_0);
        if(index_0 < ((&kernelContext_4)->entryPointParams_0->B_0))
        {

#line 2236
            *((&kernelContext_4)->entryPointParams_bands_0+(_S37 * (&kernelContext_4)->entryPointParams_0->B_0 + index_0)) = packed_float2(float2(r_5[k_0].x, - r_5[k_0].y)) ;

#line 2236
        }

#line 2234
        k_0 = k_0 + 1U;

#line 2234
    }

#line 2239
    return;
}
