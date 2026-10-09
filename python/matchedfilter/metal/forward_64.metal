#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;

#line 10912 "hlsl.meta.slang"
uint firstbithigh_0(uint value_0)
{

#line 10925
    if(value_0 == 0U)
    {

#line 10926
        return 4294967295U;
    }

#line 10927
    uint _S1 = clz(value_0);

#line 10927
    return 31U - _S1;
}


#line 416 "/tmp/tmpepnu74ei/forward.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 418
    float2 t1_0 = *a_0 - *c_0;

#line 418
    float2 t2_0 = *b_0 + *d_0;

#line 418
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 420
    *b_0 = t1_0 + j3_0;

#line 420
    *c_0 = t0_0 - t2_0;

#line 420
    *d_0 = t1_0 - j3_0;
    return;
}


#line 248
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 248
    float _S2 = a_1.x;

#line 248
    float _S3 = b_1.x;

#line 248
    float _S4 = a_1.y;

#line 248
    float _S5 = b_1.y;

#line 248
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 452
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 459
    uint n1_0 = 0U;
    for(;;)
    {

#line 460
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 460
            break;
        }

#line 460
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 460
        n1_0 = n1_0 + 1U;

#line 460
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 461
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 461
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 462
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 462
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 463
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 463
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 463
    uint k2_0 = 0U;
    for(;;)
    {

#line 464
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 464
            break;
        }

#line 464
        uint _S6 = 4U * k2_0;

#line 464
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 464
        k2_0 = k2_0 + 1U;

#line 464
    }

    float2 t_0 = (*r_0)[int(1)];

#line 466
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 466
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 467
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 467
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 468
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 468
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 469
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 469
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 470
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 470
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 471
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 471
    (*r_0)[int(14)] = t_5;
    return;
}


#line 22 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 250 "/tmp/tmpepnu74ei/forward.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S7 = max(TB_0, 1U);

#line 252
    uint j_0 = d_1 / _S7;

#line 252
    uint m_0 = d_1 % _S7;

#line 252
    uint _S8;
    if(TB_0 <= 16U)
    {

#line 253
        _S8 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 253
    }
    else
    {

#line 253
        _S8 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 253
    }

#line 253
    return _S8;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint seriesLength_0;
};


#line 237 "/tmp/tmpepnu74ei/forward.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    packed_float2 device* entryPointParams_spectra_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(128)> threadgroup* stg_0;
};


#line 237
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 237
    uint _S9 = 2U * i_0;

#line 237
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9] = (as_type<uint>((v_0.x)));

#line 237
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9 + 1U] = (as_type<uint>((v_0.y)));

#line 237
    return;
}


#line 238
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 238
    uint _S10 = 2U * i_1;

#line 238
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10 + 1U]))));
}


#line 612
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 613
    uint j_1;

#line 624
    thread array<float2, int(16)> out_0;

#line 624
    uint z_0 = 0U;
    for(;;)
    {

#line 625
        if(z_0 < 16U)
        {
        }
        else
        {

#line 625
            break;
        }

#line 625
        out_0[z_0] = float2(0.0, 0.0);

#line 625
        z_0 = z_0 + 1U;

#line 625
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S11 = p0_0 & lenMask_0;

#line 631
    uint _S12 = (_S11 >> lgSpan_0) * 4U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S11 & spanMask_0);

#line 631
    uint c_1 = 0U;

    for(;;)
    {

#line 633
        if(c_1 < 1U)
        {
        }
        else
        {

#line 633
            break;
        }

#line 634
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 634
        j_1 = 0U;
        for(;;)
        {

#line 635
            if(j_1 < 16U)
            {
            }
            else
            {

#line 635
                break;
            }

#line 635
            stgPut_0(j_1 * 4U + kernelContext_2->_tid_0, (*r_1)[c_1 * 16U + j_1], kernelContext_2);

#line 635
            j_1 = j_1 + 1U;

#line 635
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 636
        uint d_2 = 0U;
        for(;;)
        {

#line 637
            if(d_2 < 16U)
            {
            }
            else
            {

#line 637
                break;
            }

#line 638
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S13 = pz_0 & lenMask_0;
            uint az_0 = (_S13 >> lgSpan_0) * 4U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

#line 640
            float2 _S14 = stgGet_0(_S12 + az_0 - c_1 * 16U * 4U, kernelContext_2);


            out_0[d_2] = _S14;

#line 637
            d_2 = d_2 + 1U;

#line 637
        }

#line 633
        c_1 = c_1 + 1U;

#line 633
    }

#line 633
    j_1 = 0U;

#line 646
    for(;;)
    {

#line 646
        if(j_1 < 16U)
        {
        }
        else
        {

#line 646
            break;
        }

#line 646
        (*r_1)[j_1] = out_0[j_1];

#line 646
        j_1 = j_1 + 1U;

#line 646
    }
    return;
}


#line 431
void dft4_0(array<float2, int(16)> thread* r_2, uint o_0)
{
    r4_0(&(*r_2)[o_0], &(*r_2)[o_0 + 1U], &(*r_2)[o_0 + 2U], &(*r_2)[o_0 + 3U]);
    float2 t_6 = (*r_2)[o_0 + 1U];

#line 434
    (*r_2)[o_0 + 1U] = (*r_2)[o_0 + 2U];

#line 434
    (*r_2)[o_0 + 2U] = t_6;
    return;
}


#line 555
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 555
    uint b_2 = 0U;

#line 564
    for(;;)
    {

#line 564
        if(b_2 < 4U)
        {
        }
        else
        {

#line 564
            break;
        }

#line 564
        dft4_0(r_3, b_2 * 4U);

#line 564
        b_2 = b_2 + 1U;

#line 564
    }


    return;
}


#line 1636
void forwardTransform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 1636
    for(;;)
    {

#line 1636
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(4U);
                uint lgLn_0 = firstbithigh_0(64U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 3U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 64.0);
                float _S15 = tw_0.x;

#line 27
                float _S16 = tw_0.y;

#line 27
                uint k2_1 = 0U;

#line 27
                float cr_0 = 1.0;

#line 27
                float ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S15 - ci_0 * _S16;
                    float _S17 = cr_0 * _S16 + ci_0 * _S15;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S17;

#line 29
                }

#line 37
                uint per_2 = 16U / max(4U, 1U);
                uint _S18 = max(0U, 1U);
                uint blk2_2 = tid_0 / _S18;

#line 39
                uint lane2_2 = tid_0 % _S18;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 4U, 64U, blk_2, lane_2, per_2, _S18, 4U, blk2_2, lane2_2, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        break;
    }

#line 43
    innermost_0(r_4);

#line 1639 "/tmp/tmpepnu74ei/forward.slang"
    return;
}


#line 671
uint lgOf_0(uint i_2)
{

#line 671
    uint _S19;

#line 671
    if(i_2 < 1U)
    {

#line 671
        _S19 = 4U;

#line 671
    }
    else
    {

#line 671
        _S19 = 1U;

#line 671
    }

#line 671
    return _S19;
}


#line 673
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 677
    uint lg_1 = lgOf_0(1U);

#line 677
    uint lg_2 = lgOf_0(0U);

#line 682
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1644
[[kernel]] void seriesForward(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], packed_float2 device* entryPointParams_spectra_1 [[buffer(3)]])
{

#line 1644
    thread KernelContext_0 kernelContext_4;

#line 1644
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1644
    (&kernelContext_4)->entryPointParams_series_0 = entryPointParams_series_1;

#line 1644
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 1644
    (&kernelContext_4)->entryPointParams_spectra_0 = entryPointParams_spectra_1;

#line 1644
    threadgroup array<uint, int(128)> stg_1;

#line 1644
    (&kernelContext_4)->stg_0 = &stg_1;

#line 1650
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    uint _S20 = gid_0.x;

#line 1653
    uint _S21 = entryPointParams_starts_1[_S20];
    thread array<float2, int(16)> r_5;

#line 1654
    uint k_0 = 0U;
    for(;;)
    {

#line 1655
        if(k_0 < 16U)
        {
        }
        else
        {

#line 1655
            break;
        }

#line 1656
        uint offset_0 = tid_1 + 4U * k_0;
        float2 _S22 = float2(0.0, 0.0);

#line 1657
        bool _S23;

        if(_S21 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0))
        {

#line 1659
            _S23 = offset_0 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0 - _S21);

#line 1659
        }
        else
        {

#line 1659
            _S23 = false;

#line 1659
        }

#line 1659
        float2 x_1;

#line 1659
        if(_S23)
        {

#line 1659
            x_1 = float2(*((&kernelContext_4)->entryPointParams_series_0+(_S21 + offset_0))) ;

#line 1659
        }
        else
        {

#line 1659
            x_1 = _S22;

#line 1659
        }

        r_5[k_0] = float2(x_1.x / 64.0, - x_1.y / 64.0);

#line 1655
        k_0 = k_0 + 1U;

#line 1655
    }

#line 1655
    forwardTransform_0(&r_5, tid_1, &kernelContext_4);

#line 1655
    k_0 = 0U;

#line 1664
    for(;;)
    {

#line 1664
        if(k_0 < 16U)
        {
        }
        else
        {

#line 1664
            break;
        }

#line 1664
        *((&kernelContext_4)->entryPointParams_spectra_0+(_S20 * 64U + slotToIndex_0(tid_1 * 16U + k_0))) = packed_float2(float2(r_5[k_0].x, - r_5[k_0].y)) ;

#line 1664
        k_0 = k_0 + 1U;

#line 1664
    }



    return;
}
