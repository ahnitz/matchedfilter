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


#line 84 "/home/ahnitz/projects/claude/searchdev/work/mf-gpu-c16/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 280 "/tmp/tmp4g202fvq/tier0.slang"
float2 cmul_0(float2 a_0, float2 b_0)
{

#line 280
    float _S2 = a_0.x;

#line 280
    float _S3 = b_0.x;

#line 280
    float _S4 = a_0.y;

#line 280
    float _S5 = b_0.y;

#line 280
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 486
void r4_0(float2 thread* a_1, float2 thread* b_1, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 488
    float2 t1_0 = *a_1 - *c_0;

#line 488
    float2 t2_0 = *b_1 + *d_0;

#line 488
    float2 t3_0 = *b_1 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 490
    *b_1 = t1_0 + j3_0;

#line 490
    *c_0 = t0_0 - t2_0;

#line 490
    *d_0 = t1_0 - j3_0;
    return;
}


#line 522
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 529
    uint n1_0 = 0U;
    for(;;)
    {

#line 530
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 530
            break;
        }

#line 530
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 530
        n1_0 = n1_0 + 1U;

#line 530
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 531
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 531
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 532
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 532
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 533
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 533
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 533
    uint k2_0 = 0U;
    for(;;)
    {

#line 534
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 534
            break;
        }

#line 534
        uint _S6 = 4U * k2_0;

#line 534
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 534
        k2_0 = k2_0 + 1U;

#line 534
    }

    float2 t_0 = (*r_0)[int(1)];

#line 536
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 536
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 537
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 537
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 538
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 538
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 539
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 539
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 540
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 540
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 541
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 541
    (*r_0)[int(14)] = t_5;
    return;
}


#line 568
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 570
    thread array<float2, int(16)> v_0;

#line 570
    uint j_0 = 0U;
    for(;;)
    {

#line 571
        if(j_0 < 16U)
        {
        }
        else
        {

#line 571
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        v_0[j_0] = cmul_0((*r_1)[j_0] - (*r_1)[j_0 + 16U], mfTwiddle_0(6.28318548202514648f * float(j_0) / 32.0f));

#line 571
        j_0 = j_0 + 1U;

#line 571
    }

#line 577
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 578
    uint k_0 = 0U;
    for(;;)
    {

#line 579
        if(k_0 < 16U)
        {
        }
        else
        {

#line 579
            break;
        }

#line 579
        uint _S7 = 2U * k_0;

#line 579
        (*r_1)[_S7] = u_0[k_0];

#line 579
        (*r_1)[_S7 + 1U] = v_0[k_0];

#line 579
        k_0 = k_0 + 1U;

#line 579
    }
    return;
}


#line 607
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 282
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S8 = max(TB_0, 1U);

#line 284
    uint j_1 = d_1 / _S8;

#line 284
    uint m_0 = d_1 % _S8;

#line 284
    uint _S9;
    if(TB_0 <= 32U)
    {

#line 285
        _S9 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 285
    }
    else
    {

#line 285
        _S9 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 285
    }

#line 285
    return _S9;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint seriesLength_0;
    uint B0_0;
    uint B1_0;
};


#line 269 "/tmp/tmp4g202fvq/tier0.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    uint device* entryPointParams_band0_0;
    packed_float2 device* entryPointParams_band1_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 269
void stgPut_0(uint i_0, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 269
    uint _S10 = 2U * i_0;

#line 269
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S10] = (as_type<uint>((v_1.x)));

#line 269
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S10 + 1U] = (as_type<uint>((v_1.y)));

#line 269
    return;
}


#line 270
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 270
    uint _S11 = 2U * i_1;

#line 270
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S11]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S11 + 1U]))));
}


#line 711
void exchange_0(array<float2, int(32)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 712
    uint j_2;

#line 723
    thread array<float2, int(32)> out_0;

#line 723
    uint z_0 = 0U;
    for(;;)
    {

#line 724
        if(z_0 < 32U)
        {
        }
        else
        {

#line 724
            break;
        }

#line 724
        out_0[z_0] = float2(0.0f, 0.0f);

#line 724
        z_0 = z_0 + 1U;

#line 724
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S12 = p0_0 & lenMask_0;

#line 730
    uint _S13 = _S12 >> lgSpan_0;

#line 730
    uint _S14 = _S13 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S12 & spanMask_0);

#line 730
    uint c_1 = 0U;

    for(;;)
    {

#line 732
        if(c_1 < 8U)
        {
        }
        else
        {

#line 732
            break;
        }

#line 733
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 733
        j_2 = 0U;
        for(;;)
        {

#line 734
            if(j_2 < 4U)
            {
            }
            else
            {

#line 734
                break;
            }

#line 734
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 4U + j_2], kernelContext_2);

#line 734
            j_2 = j_2 + 1U;

#line 734
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 735
        uint d_2 = 0U;
        for(;;)
        {

#line 736
            if(d_2 < 32U)
            {
            }
            else
            {

#line 736
                break;
            }

#line 737
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S15 = pz_0 & lenMask_0;

#line 738
            uint iz_0 = _S15 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);
            uint i_2 = _S13 + iz_0;
            uint _S16 = c_1 * 4U;

#line 741
            bool _S17;

#line 741
            if(i_2 >= _S16)
            {

#line 741
                _S17 = i_2 < ((c_1 + 1U) * 4U);

#line 741
            }
            else
            {

#line 741
                _S17 = false;

#line 741
            }

#line 741
            if(_S17)
            {

#line 741
                float2 _S18 = stgGet_0(_S14 + az_0 - _S16 * 1024U, kernelContext_2);
                out_0[d_2] = _S18;

#line 741
            }

#line 736
            d_2 = d_2 + 1U;

#line 736
        }

#line 732
        c_1 = c_1 + 1U;

#line 732
    }

#line 732
    j_2 = 0U;

#line 745
    for(;;)
    {

#line 745
        if(j_2 < 32U)
        {
        }
        else
        {

#line 745
            break;
        }

#line 745
        (*r_3)[j_2] = out_0[j_2];

#line 745
        j_2 = j_2 + 1U;

#line 745
    }
    return;
}


#line 625
void innermost_0(array<float2, int(32)> thread* r_4)
{

    dft32_0(r_4);

#line 637
    return;
}


#line 2102
void forwardTransform_0(array<float2, int(32)> thread* r_5, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 2102
    uint _S19;

#line 2102
    uint k2_1;

#line 2102
    float cr_0;

#line 2102
    float ci_0;

#line 2102
    uint _S20;

#line 2102
    for(;;)
    {

#line 2102
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/mf-gpu-c16/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S19 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(32768U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;

#line 19
                dftR_0(r_5);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 32768.0f);
                float _S21 = tw_0.x;

#line 40
                float _S22 = tw_0.y;

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
                    float nr_0 = cr_0 * _S21 - ci_0 * _S22;
                    float _S23 = cr_0 * _S22 + ci_0 * _S21;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S23;

#line 42
                }

#line 50
                uint per_2 = 32U / max(1024U, 1U);
                uint _S24 = max(32U, 1U);

#line 51
                _S20 = _S24;
                uint blk2_2 = tid_0 / _S24;

#line 52
                uint lane2_2 = tid_0 % _S24;

#line 52
                exchange_0(r_5, lgLn_0, lgTB_0, 1024U, 32768U, blk_2, lane_2, per_2, _S24, 1024U, blk2_2, lane2_2, kernelContext_3);

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
                float _S25 = tw_1.x;

#line 40
                float _S26 = tw_1.y;

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
                    float nr_1 = cr_0 * _S25 - ci_0 * _S26;
                    float _S27 = cr_0 * _S26 + ci_0 * _S25;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S27;

#line 42
                }

#line 50
                uint per_3 = 32U / _S20;
                uint _S28 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S28;

#line 52
                uint lane2_3 = tid_0 % _S28;

#line 52
                exchange_0(r_5, _S19, lgTB_1, 32U, 1024U, blk_3, lane_3, per_3, _S28, 32U, blk2_3, lane2_3, kernelContext_3);

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

#line 2105 "/tmp/tmp4g202fvq/tier0.slang"
    return;
}


#line 770
uint lgOf_0(uint i_3)
{

#line 770
    uint _S29;

#line 770
    if(i_3 < 2U)
    {

#line 770
        _S29 = 5U;

#line 770
    }
    else
    {

#line 770
        if(i_3 == 2U)
        {

#line 770
            _S29 = 5U;

#line 770
        }
        else
        {

#line 770
            _S29 = 1U;

#line 770
        }

#line 770
    }

#line 770
    return _S29;
}


#line 772
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 776
    uint lg_1 = lgOf_0(1U);

#line 776
    uint lg_2 = lgOf_0(0U);

#line 781
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2248
[[kernel]] void forwardTier0(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], uint device* entryPointParams_band0_1 [[buffer(3)]], packed_float2 device* entryPointParams_band1_1 [[buffer(4)]])
{

#line 2248
    thread KernelContext_0 kernelContext_4;

#line 2248
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 2248
    (&kernelContext_4)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2248
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2248
    (&kernelContext_4)->entryPointParams_band0_0 = entryPointParams_band0_1;

#line 2248
    (&kernelContext_4)->entryPointParams_band1_0 = entryPointParams_band1_1;

#line 2248
    threadgroup array<uint, int(8192)> stg_1;

#line 2248
    (&kernelContext_4)->stg_0 = &stg_1;

#line 2255
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    uint _S30 = gid_0.x;

#line 2258
    uint _S31 = entryPointParams_starts_1[_S30];
    thread array<float2, int(32)> r_6;

#line 2259
    uint k_1 = 0U;
    for(;;)
    {

#line 2260
        if(k_1 < 32U)
        {
        }
        else
        {

#line 2260
            break;
        }

#line 2261
        uint offset_0 = tid_1 + 1024U * k_1;
        float2 _S32 = float2(0.0f, 0.0f);

#line 2262
        bool _S33;
        if(_S31 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0))
        {

#line 2263
            _S33 = offset_0 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0 - _S31);

#line 2263
        }
        else
        {

#line 2263
            _S33 = false;

#line 2263
        }

#line 2263
        float2 x_1;

#line 2263
        if(_S33)
        {

#line 2263
            x_1 = float2(*((&kernelContext_4)->entryPointParams_series_0+(_S31 + offset_0))) ;

#line 2263
        }
        else
        {

#line 2263
            x_1 = _S32;

#line 2263
        }

        r_6[k_1] = float2(x_1.x / 32768.0f, - x_1.y / 32768.0f);

#line 2260
        k_1 = k_1 + 1U;

#line 2260
    }

#line 2260
    forwardTransform_0(&r_6, tid_1, &kernelContext_4);

#line 2260
    k_1 = 0U;

#line 2268
    for(;;)
    {

#line 2268
        if(k_1 < 32U)
        {
        }
        else
        {

#line 2268
            break;
        }

#line 2269
        uint index_0 = slotToIndex_0(tid_1 * 32U + k_1);
        float _S34 = r_6[k_1].x;

#line 2270
        float _S35 = - r_6[k_1].y;

#line 2270
        float2 v_2 = float2(_S34, _S35);
        if(index_0 < ((&kernelContext_4)->entryPointParams_0->B0_0))
        {

#line 2272
            *((&kernelContext_4)->entryPointParams_band0_0+(_S30 * (&kernelContext_4)->entryPointParams_0->B0_0 + index_0)) = (as_type<ushort>((half)((_S34)))) | ((as_type<ushort>((half)((_S35)))) << 16U);

#line 2271
        }

        if(index_0 < ((&kernelContext_4)->entryPointParams_0->B1_0))
        {

#line 2273
            *((&kernelContext_4)->entryPointParams_band1_0+(_S30 * (&kernelContext_4)->entryPointParams_0->B1_0 + index_0)) = packed_float2(v_2) ;

#line 2273
        }

#line 2268
        k_1 = k_1 + 1U;

#line 2268
    }

#line 2276
    return;
}
