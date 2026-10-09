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


#line 152 "mm_4096_fullCorrelation.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 152
    return float2(*(b_0+i_0)) ;
}


#line 226
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 226
    float _S2 = a_0.x;

#line 226
    float _S3 = b_1.x;

#line 226
    float _S4 = a_0.y;

#line 226
    float _S5 = b_1.y;

#line 226
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 393
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 395
    float2 t1_0 = *a_1 - *c_0;

#line 395
    float2 t2_0 = *b_2 + *d_0;

#line 395
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 397
    *b_2 = t1_0 + j3_0;

#line 397
    *c_0 = t0_0 - t2_0;

#line 397
    *d_0 = t1_0 - j3_0;
    return;
}


#line 225
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 225
    float _S6 = a_2.x;

#line 225
    float _S7 = b_3.x;

#line 225
    float _S8 = a_2.y;

#line 225
    float _S9 = b_3.y;

#line 225
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 429
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 436
    uint n1_0 = 0U;
    for(;;)
    {

#line 437
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 437
            break;
        }

#line 437
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 437
        n1_0 = n1_0 + 1U;

#line 437
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 438
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 438
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 439
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 439
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 440
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 440
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 440
    uint k2_0 = 0U;
    for(;;)
    {

#line 441
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 441
            break;
        }

#line 441
        uint _S10 = 4U * k2_0;

#line 441
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 441
        k2_0 = k2_0 + 1U;

#line 441
    }

    float2 t_0 = (*r_0)[int(1)];

#line 443
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 443
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 444
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 444
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 445
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 445
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 446
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 446
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 447
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 447
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 448
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 448
    (*r_0)[int(14)] = t_5;
    return;
}


#line 429
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_1 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_1 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_1 = float2(0.0, 1.0);
    float2 W6_1 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_1 = float2(-0.92387950420379639, -0.38268342614173889);

#line 436
    uint n1_1 = 0U;
    for(;;)
    {

#line 437
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 437
            break;
        }

#line 437
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 437
        n1_1 = n1_1 + 1U;

#line 437
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 438
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 438
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 439
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 439
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 440
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 440
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 440
    uint k2_1 = 0U;
    for(;;)
    {

#line 441
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 441
            break;
        }

#line 441
        uint _S11 = 4U * k2_1;

#line 441
        r4_0(&(*r_1)[_S11], &(*r_1)[_S11 + 1U], &(*r_1)[_S11 + 2U], &(*r_1)[_S11 + 3U]);

#line 441
        k2_1 = k2_1 + 1U;

#line 441
    }

    float2 t_6 = (*r_1)[int(1)];

#line 443
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 443
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 444
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 444
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 445
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 445
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 446
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 446
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 447
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 447
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 448
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 448
    (*r_1)[int(14)] = t_11;
    return;
}


#line 17 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 227 "mm_4096_fullCorrelation.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 229
    uint j_0 = d_1 / _S12;

#line 229
    uint m_0 = d_1 % _S12;

#line 229
    uint _S13;
    if(TB_0 <= 16U)
    {

#line 230
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 230
    }
    else
    {

#line 230
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 230
    }

#line 230
    return _S13;
}


#line 8402 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
};


#line 214 "mm_4096_fullCorrelation.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 214
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 214
    uint _S14 = 2U * i_1;

#line 214
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14] = (as_type<uint>((v_0.x)));

#line 214
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14 + 1U] = (as_type<uint>((v_0.y)));

#line 214
    return;
}


#line 215
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 215
    uint _S15 = 2U * i_2;

#line 215
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15 + 1U]))));
}


#line 589
void exchange_0(array<float2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 590
    uint j_1;

#line 601
    thread array<float2, int(16)> out_0;

#line 601
    uint z_0 = 0U;
    for(;;)
    {

#line 602
        if(z_0 < 16U)
        {
        }
        else
        {

#line 602
            break;
        }

#line 602
        out_0[z_0] = float2(0.0, 0.0);

#line 602
        z_0 = z_0 + 1U;

#line 602
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S16 = p0_0 & lenMask_0;

#line 608
    uint _S17 = (_S16 >> lgSpan_0) * 256U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 608
    uint c_1 = 0U;

    for(;;)
    {

#line 610
        if(c_1 < 1U)
        {
        }
        else
        {

#line 610
            break;
        }

#line 611
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 611
        j_1 = 0U;
        for(;;)
        {

#line 612
            if(j_1 < 16U)
            {
            }
            else
            {

#line 612
                break;
            }

#line 612
            stgPut_0(j_1 * 256U + kernelContext_2->_tid_0, (*r_2)[c_1 * 16U + j_1], kernelContext_2);

#line 612
            j_1 = j_1 + 1U;

#line 612
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 613
        uint d_2 = 0U;
        for(;;)
        {

#line 614
            if(d_2 < 16U)
            {
            }
            else
            {

#line 614
                break;
            }

#line 615
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S18 = pz_0 & lenMask_0;
            uint az_0 = (_S18 >> lgSpan_0) * 256U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S18 & spanMask_0);

#line 617
            float2 _S19 = stgGet_0(_S17 + az_0 - c_1 * 16U * 256U, kernelContext_2);


            out_0[d_2] = _S19;

#line 614
            d_2 = d_2 + 1U;

#line 614
        }

#line 610
        c_1 = c_1 + 1U;

#line 610
    }

#line 610
    j_1 = 0U;

#line 623
    for(;;)
    {

#line 623
        if(j_1 < 16U)
        {
        }
        else
        {

#line 623
            break;
        }

#line 623
        (*r_2)[j_1] = out_0[j_1];

#line 623
        j_1 = j_1 + 1U;

#line 623
    }
    return;
}


#line 532
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 539
    dft16_1(r_3);

#line 544
    return;
}


#line 679
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 679
    uint _S20;

#line 679
    uint k2_2;

#line 679
    float cr_0;

#line 679
    float ci_0;

#line 679
    uint _S21;

#line 679
    for(;;)
    {

#line 679
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(256U);

#line 11
                _S20 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(4096U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 255U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 4096.0);
                float _S22 = tw_0.x;

#line 27
                float _S23 = tw_0.y;

#line 27
                k2_2 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S22 - ci_0 * _S23;
                    float _S24 = cr_0 * _S23 + ci_0 * _S22;

#line 29
                    k2_2 = k2_2 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S24;

#line 29
                }

#line 37
                uint per_2 = 16U / max(256U, 1U);
                uint _S25 = max(16U, 1U);

#line 38
                _S21 = _S25;
                uint blk2_2 = tid_0 / _S25;

#line 39
                uint lane2_2 = tid_0 % _S25;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 256U, 4096U, blk_2, lane_2, per_2, _S25, 256U, blk2_2, lane2_2, kernelContext_3);

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


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 256.0);
                float _S26 = tw_1.x;

#line 27
                float _S27 = tw_1.y;

#line 27
                k2_2 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S26 - ci_0 * _S27;
                    float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 29
                    k2_2 = k2_2 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S28;

#line 29
                }

#line 37
                uint per_3 = 16U / _S21;
                uint _S29 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S29;

#line 39
                uint lane2_3 = tid_0 % _S29;

#line 39
                exchange_0(r_4, _S20, lgTB_1, 16U, 256U, blk_3, lane_3, per_3, _S29, 16U, blk2_3, lane2_3, kernelContext_3);

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

#line 682 "mm_4096_fullCorrelation.slang"
    return;
}


#line 648
uint lgOf_0(uint i_3)
{

#line 648
    uint _S30;

#line 648
    if(i_3 < 2U)
    {

#line 648
        _S30 = 4U;

#line 648
    }
    else
    {

#line 648
        if(i_3 == 2U)
        {

#line 648
            _S30 = 4U;

#line 648
        }
        else
        {

#line 648
            _S30 = 1U;

#line 648
        }

#line 648
    }

#line 648
    return _S30;
}


#line 650
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 654
    uint lg_1 = lgOf_0(1U);

#line 654
    uint lg_2 = lgOf_0(0U);

#line 659
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1259
[[kernel]] void fullCorrelation(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], packed_float2 device* entryPointParams_output_1 [[buffer(3)]])
{

#line 1259
    thread KernelContext_0 kernelContext_4;

#line 1259
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1259
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1259
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1259
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1259
    threadgroup array<uint, int(8192)> stg_1;

#line 1259
    (&kernelContext_4)->stg_0 = &stg_1;



    uint pair_0 = gid_0.x;

#line 1263
    uint tid_1 = lid_0.x;
    uint _S31 = pair_0 / entryPointParams_1->ntmpl_0;

#line 1264
    uint _S32 = pair_0 % entryPointParams_1->ntmpl_0;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(16)> r_5;

#line 1267
    uint i_4 = 0U;
    for(;;)
    {

#line 1268
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1268
            break;
        }

#line 1269
        uint idx_0 = tid_1 + 256U * i_4;
        r_5[i_4] = cmulConj_0(cload_0((&kernelContext_4)->entryPointParams_data_0, _S31 * 4096U + idx_0), cload_0((&kernelContext_4)->entryPointParams_tmpl_0, _S32 * 4096U + idx_0));

#line 1268
        i_4 = i_4 + 1U;

#line 1268
    }

#line 1268
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 1268
    i_4 = 0U;

#line 1273
    for(;;)
    {

#line 1273
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1273
            break;
        }

#line 1273
        *((&kernelContext_4)->entryPointParams_output_0+(pair_0 * 4096U + slotToIndex_0(tid_1 * 16U + i_4))) = packed_float2(float2(r_5[i_4].x, r_5[i_4].y)) ;

#line 1273
        i_4 = i_4 + 1U;

#line 1273
    }

    return;
}
