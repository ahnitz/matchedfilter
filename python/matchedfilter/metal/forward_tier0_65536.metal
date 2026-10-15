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


#line 467 "/tmp/tmpvk_r8ec4/tier0.slang"
void r4_0(float2 thread* a_0, float2 thread* b_0, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_0 + *c_0;

#line 469
    float2 t1_0 = *a_0 - *c_0;

#line 469
    float2 t2_0 = *b_0 + *d_0;

#line 469
    float2 t3_0 = *b_0 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_0 = t0_0 + t2_0;

#line 471
    *b_0 = t1_0 + j3_0;

#line 471
    *c_0 = t0_0 - t2_0;

#line 471
    *d_0 = t1_0 - j3_0;
    return;
}


#line 74 "/home/ahnitz/projects/claude/searchdev/work/mf-gpu-c16/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 261 "/tmp/tmpvk_r8ec4/tier0.slang"
float2 cmul_0(float2 a_1, float2 b_1)
{

#line 261
    float _S2 = a_1.x;

#line 261
    float _S3 = b_1.x;

#line 261
    float _S4 = a_1.y;

#line 261
    float _S5 = b_1.y;

#line 261
    return float2(_S2 * _S3 - _S4 * _S5, _S2 * _S5 + _S4 * _S3);
}


#line 503
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 510
    uint n1_0 = 0U;
    for(;;)
    {

#line 511
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 511
            break;
        }

#line 511
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 511
        n1_0 = n1_0 + 1U;

#line 511
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 512
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 512
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 513
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 513
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 514
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 514
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 514
    uint k2_0 = 0U;
    for(;;)
    {

#line 515
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 515
            break;
        }

#line 515
        uint _S6 = 4U * k2_0;

#line 515
        r4_0(&(*r_0)[_S6], &(*r_0)[_S6 + 1U], &(*r_0)[_S6 + 2U], &(*r_0)[_S6 + 3U]);

#line 515
        k2_0 = k2_0 + 1U;

#line 515
    }

    float2 t_0 = (*r_0)[int(1)];

#line 517
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 517
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 518
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 518
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 519
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 519
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 520
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 520
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 521
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 521
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 522
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 522
    (*r_0)[int(14)] = t_5;
    return;
}


#line 569
void dft64_0(array<float2, int(64)> thread* r_1)
{

#line 569
    uint k_0;

#line 569
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

#line 572
        r4_0(&(*r_1)[j_0], &(*r_1)[j_0 + 16U], &(*r_1)[j_0 + 32U], &(*r_1)[j_0 + 48U]);

#line 571
        j_0 = j_0 + 1U;

#line 571
    }

    thread array<float2, int(64)> o_0;

#line 573
    uint pp_0 = 0U;
    for(;;)
    {

#line 574
        if(pp_0 < 4U)
        {
        }
        else
        {

#line 574
            break;
        }

#line 575
        thread array<float2, int(16)> b_2;

#line 575
        j_0 = 0U;
        for(;;)
        {

#line 576
            if(j_0 < 16U)
            {
            }
            else
            {

#line 576
                break;
            }
            b_2[j_0] = cmul_0((*r_1)[pp_0 * 16U + j_0], mfTwiddle_0(6.28318548202514648f * float(pp_0 * j_0) / 64.0f));

#line 576
            j_0 = j_0 + 1U;

#line 576
        }



        dft16_0(&b_2);

#line 580
        k_0 = 0U;
        for(;;)
        {

#line 581
            if(k_0 < 16U)
            {
            }
            else
            {

#line 581
                break;
            }

#line 581
            o_0[4U * k_0 + pp_0] = b_2[k_0];

#line 581
            k_0 = k_0 + 1U;

#line 581
        }

#line 574
        pp_0 = pp_0 + 1U;

#line 574
    }

#line 574
    k_0 = 0U;

#line 583
    for(;;)
    {

#line 583
        if(k_0 < 64U)
        {
        }
        else
        {

#line 583
            break;
        }

#line 583
        (*r_1)[k_0] = o_0[k_0];

#line 583
        k_0 = k_0 + 1U;

#line 583
    }
    return;
}


void dftR_0(array<float2, int(64)> thread* r_2)
{

#line 595
    dft64_0(r_2);

    return;
}


#line 263
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S7 = max(TB_0, 1U);

#line 265
    uint j_1 = d_1 / _S7;

#line 265
    uint m_0 = d_1 % _S7;

#line 265
    uint _S8;
    if(TB_0 <= 64U)
    {

#line 266
        _S8 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 266
    }
    else
    {

#line 266
        _S8 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 266
    }

#line 266
    return _S8;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint seriesLength_0;
    uint B0_0;
    uint B1_0;
};


#line 250 "/tmp/tmpvk_r8ec4/tier0.slang"
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


#line 250
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 250
    uint _S9 = 2U * i_0;

#line 250
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9] = (as_type<uint>((v_0.x)));

#line 250
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S9 + 1U] = (as_type<uint>((v_0.y)));

#line 250
    return;
}


#line 251
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 251
    uint _S10 = 2U * i_1;

#line 251
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S10 + 1U]))));
}


#line 692
void exchange_0(array<float2, int(64)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 693
    uint j_2;

#line 704
    thread array<float2, int(64)> out_0;

#line 704
    uint z_0 = 0U;
    for(;;)
    {

#line 705
        if(z_0 < 64U)
        {
        }
        else
        {

#line 705
            break;
        }

#line 705
        out_0[z_0] = float2(0.0f, 0.0f);

#line 705
        z_0 = z_0 + 1U;

#line 705
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S11 = p0_0 & lenMask_0;

#line 711
    uint _S12 = _S11 >> lgSpan_0;

#line 711
    uint _S13 = _S12 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S11 & spanMask_0);

#line 711
    uint c_1 = 0U;

    for(;;)
    {

#line 713
        if(c_1 < 16U)
        {
        }
        else
        {

#line 713
            break;
        }

#line 714
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 714
        j_2 = 0U;
        for(;;)
        {

#line 715
            if(j_2 < 4U)
            {
            }
            else
            {

#line 715
                break;
            }

#line 715
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 4U + j_2], kernelContext_2);

#line 715
            j_2 = j_2 + 1U;

#line 715
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 716
        uint d_2 = 0U;
        for(;;)
        {

#line 717
            if(d_2 < 64U)
            {
            }
            else
            {

#line 717
                break;
            }

#line 718
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S14 = pz_0 & lenMask_0;

#line 719
            uint iz_0 = _S14 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);
            uint i_2 = _S12 + iz_0;
            uint _S15 = c_1 * 4U;

#line 722
            bool _S16;

#line 722
            if(i_2 >= _S15)
            {

#line 722
                _S16 = i_2 < ((c_1 + 1U) * 4U);

#line 722
            }
            else
            {

#line 722
                _S16 = false;

#line 722
            }

#line 722
            if(_S16)
            {

#line 722
                float2 _S17 = stgGet_0(_S13 + az_0 - _S15 * 1024U, kernelContext_2);
                out_0[d_2] = _S17;

#line 722
            }

#line 717
            d_2 = d_2 + 1U;

#line 717
        }

#line 713
        c_1 = c_1 + 1U;

#line 713
    }

#line 713
    j_2 = 0U;

#line 726
    for(;;)
    {

#line 726
        if(j_2 < 64U)
        {
        }
        else
        {

#line 726
            break;
        }

#line 726
        (*r_3)[j_2] = out_0[j_2];

#line 726
        j_2 = j_2 + 1U;

#line 726
    }
    return;
}


#line 528
void dft16at_0(array<float2, int(64)> thread* r_4, uint o_1)
{



    thread array<float2, int(16)> b_3;

#line 533
    uint i_3 = 0U;
    for(;;)
    {

#line 534
        if(i_3 < 16U)
        {
        }
        else
        {

#line 534
            break;
        }

#line 534
        b_3[i_3] = (*r_4)[o_1 + i_3];

#line 534
        i_3 = i_3 + 1U;

#line 534
    }
    dft16_0(&b_3);

#line 535
    i_3 = 0U;
    for(;;)
    {

#line 536
        if(i_3 < 16U)
        {
        }
        else
        {

#line 536
            break;
        }

#line 536
        (*r_4)[o_1 + i_3] = b_3[i_3];

#line 536
        i_3 = i_3 + 1U;

#line 536
    }

    return;
}


#line 606
void innermost_0(array<float2, int(64)> thread* r_5)
{

#line 606
    uint b_4 = 0U;

#line 611
    for(;;)
    {

#line 611
        if(b_4 < 4U)
        {
        }
        else
        {

#line 611
            break;
        }

#line 611
        dft16at_0(r_5, b_4 * 16U);

#line 611
        b_4 = b_4 + 1U;

#line 611
    }

#line 618
    return;
}


#line 2068
void forwardTransform_0(array<float2, int(64)> thread* r_6, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 2068
    uint _S18;

#line 2068
    uint k2_1;

#line 2068
    float cr_0;

#line 2068
    float ci_0;

#line 2068
    uint _S19;

#line 2068
    for(;;)
    {

#line 2068
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/mf-gpu-c16/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S18 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(65536U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;

#line 19
                dftR_0(r_6);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 6.5536e+04f);
                float _S20 = tw_0.x;

#line 40
                float _S21 = tw_0.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 64U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_6)[k2_1] = cmul_0((*r_6)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S20 - ci_0 * _S21;
                    float _S22 = cr_0 * _S21 + ci_0 * _S20;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S22;

#line 42
                }

#line 50
                uint per_2 = 64U / max(1024U, 1U);
                uint _S23 = max(16U, 1U);

#line 51
                _S19 = _S23;
                uint blk2_2 = tid_0 / _S23;

#line 52
                uint lane2_2 = tid_0 % _S23;

#line 52
                exchange_0(r_6, lgLn_0, lgTB_0, 1024U, 65536U, blk_2, lane_2, per_2, _S23, 1024U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(16U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 15U;

#line 19
                dftR_0(r_6);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 1024.0f);
                float _S24 = tw_1.x;

#line 40
                float _S25 = tw_1.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 64U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_6)[k2_1] = cmul_0((*r_6)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S24 - ci_0 * _S25;
                    float _S26 = cr_0 * _S25 + ci_0 * _S24;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S26;

#line 42
                }

#line 50
                uint per_3 = 64U / _S19;
                uint _S27 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S27;

#line 52
                uint lane2_3 = tid_0 % _S27;

#line 52
                exchange_0(r_6, _S18, lgTB_1, 16U, 1024U, blk_3, lane_3, per_3, _S27, 16U, blk2_3, lane2_3, kernelContext_3);

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
    innermost_0(r_6);

#line 2071 "/tmp/tmpvk_r8ec4/tier0.slang"
    return;
}


#line 751
uint lgOf_0(uint i_4)
{

#line 751
    uint _S28;

#line 751
    if(i_4 < 2U)
    {

#line 751
        _S28 = 6U;

#line 751
    }
    else
    {

#line 751
        if(i_4 == 2U)
        {

#line 751
            _S28 = 4U;

#line 751
        }
        else
        {

#line 751
            _S28 = 1U;

#line 751
        }

#line 751
    }

#line 751
    return _S28;
}


#line 753
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 757
    uint lg_1 = lgOf_0(1U);

#line 757
    uint lg_2 = lgOf_0(0U);

#line 762
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 2214
[[kernel]] void forwardTier0(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], uint device* entryPointParams_band0_1 [[buffer(3)]], packed_float2 device* entryPointParams_band1_1 [[buffer(4)]])
{

#line 2214
    thread KernelContext_0 kernelContext_4;

#line 2214
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 2214
    (&kernelContext_4)->entryPointParams_series_0 = entryPointParams_series_1;

#line 2214
    (&kernelContext_4)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 2214
    (&kernelContext_4)->entryPointParams_band0_0 = entryPointParams_band0_1;

#line 2214
    (&kernelContext_4)->entryPointParams_band1_0 = entryPointParams_band1_1;

#line 2214
    threadgroup array<uint, int(8192)> stg_1;

#line 2214
    (&kernelContext_4)->stg_0 = &stg_1;

#line 2221
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    uint _S29 = gid_0.x;

#line 2224
    uint _S30 = entryPointParams_starts_1[_S29];
    thread array<float2, int(64)> r_7;

#line 2225
    uint k_1 = 0U;
    for(;;)
    {

#line 2226
        if(k_1 < 64U)
        {
        }
        else
        {

#line 2226
            break;
        }

#line 2227
        uint offset_0 = tid_1 + 1024U * k_1;
        float2 _S31 = float2(0.0f, 0.0f);

#line 2228
        bool _S32;
        if(_S30 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0))
        {

#line 2229
            _S32 = offset_0 < ((&kernelContext_4)->entryPointParams_0->seriesLength_0 - _S30);

#line 2229
        }
        else
        {

#line 2229
            _S32 = false;

#line 2229
        }

#line 2229
        float2 x_1;

#line 2229
        if(_S32)
        {

#line 2229
            x_1 = float2(*((&kernelContext_4)->entryPointParams_series_0+(_S30 + offset_0))) ;

#line 2229
        }
        else
        {

#line 2229
            x_1 = _S31;

#line 2229
        }

        r_7[k_1] = float2(x_1.x / 6.5536e+04f, - x_1.y / 6.5536e+04f);

#line 2226
        k_1 = k_1 + 1U;

#line 2226
    }

#line 2226
    forwardTransform_0(&r_7, tid_1, &kernelContext_4);

#line 2226
    k_1 = 0U;

#line 2234
    for(;;)
    {

#line 2234
        if(k_1 < 64U)
        {
        }
        else
        {

#line 2234
            break;
        }

#line 2235
        uint index_0 = slotToIndex_0(tid_1 * 64U + k_1);
        float _S33 = r_7[k_1].x;

#line 2236
        float _S34 = - r_7[k_1].y;

#line 2236
        float2 v_1 = float2(_S33, _S34);
        if(index_0 < ((&kernelContext_4)->entryPointParams_0->B0_0))
        {

#line 2238
            *((&kernelContext_4)->entryPointParams_band0_0+(_S29 * (&kernelContext_4)->entryPointParams_0->B0_0 + index_0)) = (as_type<ushort>((half)((_S33)))) | ((as_type<ushort>((half)((_S34)))) << 16U);

#line 2237
        }

        if(index_0 < ((&kernelContext_4)->entryPointParams_0->B1_0))
        {

#line 2239
            *((&kernelContext_4)->entryPointParams_band1_0+(_S29 * (&kernelContext_4)->entryPointParams_0->B1_0 + index_0)) = packed_float2(v_1) ;

#line 2239
        }

#line 2234
        k_1 = k_1 + 1U;

#line 2234
    }

#line 2242
    return;
}
