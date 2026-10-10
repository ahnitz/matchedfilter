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


#line 152 "mm_32768_fullCorrelation.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 152
    return float2(*(b_0+i_0)) ;
}


#line 252
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 252
    float _S2 = a_0.x;

#line 252
    float _S3 = b_1.x;

#line 252
    float _S4 = a_0.y;

#line 252
    float _S5 = b_1.y;

#line 252
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 26 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 251 "mm_32768_fullCorrelation.slang"
float2 cmul_0(float2 a_1, float2 b_2)
{

#line 251
    float _S6 = a_1.x;

#line 251
    float _S7 = b_2.x;

#line 251
    float _S8 = a_1.y;

#line 251
    float _S9 = b_2.y;

#line 251
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 457
void r4_0(float2 thread* a_2, float2 thread* b_3, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_2 + *c_0;

#line 459
    float2 t1_0 = *a_2 - *c_0;

#line 459
    float2 t2_0 = *b_3 + *d_0;

#line 459
    float2 t3_0 = *b_3 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_2 = t0_0 + t2_0;

#line 461
    *b_3 = t1_0 + j3_0;

#line 461
    *c_0 = t0_0 - t2_0;

#line 461
    *d_0 = t1_0 - j3_0;
    return;
}


#line 493
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 500
    uint n1_0 = 0U;
    for(;;)
    {

#line 501
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 501
            break;
        }

#line 501
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 501
        n1_0 = n1_0 + 1U;

#line 501
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 502
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 502
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 503
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 503
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 504
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 504
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 504
    uint k2_0 = 0U;
    for(;;)
    {

#line 505
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 505
            break;
        }

#line 505
        uint _S10 = 4U * k2_0;

#line 505
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 505
        k2_0 = k2_0 + 1U;

#line 505
    }

    float2 t_0 = (*r_0)[int(1)];

#line 507
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 507
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 508
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 508
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 509
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 509
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 510
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 510
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 511
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 511
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 512
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 512
    (*r_0)[int(14)] = t_5;
    return;
}


#line 539
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 541
    thread array<float2, int(16)> v_0;

#line 541
    uint j_0 = 0U;
    for(;;)
    {

#line 542
        if(j_0 < 16U)
        {
        }
        else
        {

#line 542
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        v_0[j_0] = cmul_0((*r_1)[j_0] - (*r_1)[j_0 + 16U], mfTwiddle_0(6.28318548202514648 * float(j_0) / 32.0));

#line 542
        j_0 = j_0 + 1U;

#line 542
    }

#line 548
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 549
    uint k_0 = 0U;
    for(;;)
    {

#line 550
        if(k_0 < 16U)
        {
        }
        else
        {

#line 550
            break;
        }

#line 550
        uint _S11 = 2U * k_0;

#line 550
        (*r_1)[_S11] = u_0[k_0];

#line 550
        (*r_1)[_S11 + 1U] = v_0[k_0];

#line 550
        k_0 = k_0 + 1U;

#line 550
    }
    return;
}


#line 578
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 253
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 255
    uint j_1 = d_1 / _S12;

#line 255
    uint m_0 = d_1 % _S12;

#line 255
    uint _S13;
    if(TB_0 <= 32U)
    {

#line 256
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 256
    }
    else
    {

#line 256
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 256
    }

#line 256
    return _S13;
}


#line 8402 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
};


#line 240 "mm_32768_fullCorrelation.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    packed_float2 device* entryPointParams_output_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(16384)> threadgroup* stg_0;
};


#line 240
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 240
    uint _S14 = 2U * i_1;

#line 240
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14] = (as_type<uint>((v_1.x)));

#line 240
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14 + 1U] = (as_type<uint>((v_1.y)));

#line 240
    return;
}


#line 241
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 241
    uint _S15 = 2U * i_2;

#line 241
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15 + 1U]))));
}


#line 653
void exchange_0(array<float2, int(32)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 654
    uint j_2;

#line 665
    thread array<float2, int(32)> out_0;

#line 665
    uint z_0 = 0U;
    for(;;)
    {

#line 666
        if(z_0 < 32U)
        {
        }
        else
        {

#line 666
            break;
        }

#line 666
        out_0[z_0] = float2(0.0, 0.0);

#line 666
        z_0 = z_0 + 1U;

#line 666
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S16 = p0_0 & lenMask_0;

#line 672
    uint _S17 = _S16 >> lgSpan_0;

#line 672
    uint _S18 = _S17 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 672
    uint c_1 = 0U;

    for(;;)
    {

#line 674
        if(c_1 < 4U)
        {
        }
        else
        {

#line 674
            break;
        }

#line 675
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 675
        j_2 = 0U;
        for(;;)
        {

#line 676
            if(j_2 < 8U)
            {
            }
            else
            {

#line 676
                break;
            }

#line 676
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 8U + j_2], kernelContext_2);

#line 676
            j_2 = j_2 + 1U;

#line 676
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 677
        uint d_2 = 0U;
        for(;;)
        {

#line 678
            if(d_2 < 32U)
            {
            }
            else
            {

#line 678
                break;
            }

#line 679
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S19 = pz_0 & lenMask_0;

#line 680
            uint iz_0 = _S19 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S19 & spanMask_0);
            uint i_3 = _S17 + iz_0;
            uint _S20 = c_1 * 8U;

#line 683
            bool _S21;

#line 683
            if(i_3 >= _S20)
            {

#line 683
                _S21 = i_3 < ((c_1 + 1U) * 8U);

#line 683
            }
            else
            {

#line 683
                _S21 = false;

#line 683
            }

#line 683
            if(_S21)
            {

#line 683
                float2 _S22 = stgGet_0(_S18 + az_0 - _S20 * 1024U, kernelContext_2);
                out_0[d_2] = _S22;

#line 683
            }

#line 678
            d_2 = d_2 + 1U;

#line 678
        }

#line 674
        c_1 = c_1 + 1U;

#line 674
    }

#line 674
    j_2 = 0U;

#line 687
    for(;;)
    {

#line 687
        if(j_2 < 32U)
        {
        }
        else
        {

#line 687
            break;
        }

#line 687
        (*r_3)[j_2] = out_0[j_2];

#line 687
        j_2 = j_2 + 1U;

#line 687
    }
    return;
}


#line 596
void innermost_0(array<float2, int(32)> thread* r_4)
{

    dft32_0(r_4);

#line 608
    return;
}


#line 743
void transform_0(array<float2, int(32)> thread* r_5, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 743
    uint _S23;

#line 743
    uint k2_1;

#line 743
    float cr_0;

#line 743
    float ci_0;

#line 743
    uint _S24;

#line 743
    for(;;)
    {

#line 743
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S23 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(32768U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;

#line 19
                dftR_0(r_5);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 32768.0);
                float _S25 = tw_0.x;

#line 27
                float _S26 = tw_0.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_1 < 32U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_5)[k2_1] = cmul_0((*r_5)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S25 - ci_0 * _S26;
                    float _S27 = cr_0 * _S26 + ci_0 * _S25;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S27;

#line 29
                }

#line 37
                uint per_2 = 32U / max(1024U, 1U);
                uint _S28 = max(32U, 1U);

#line 38
                _S24 = _S28;
                uint blk2_2 = tid_0 / _S28;

#line 39
                uint lane2_2 = tid_0 % _S28;

#line 39
                exchange_0(r_5, lgLn_0, lgTB_0, 1024U, 32768U, blk_2, lane_2, per_2, _S28, 1024U, blk2_2, lane2_2, kernelContext_3);

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

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 1024.0);
                float _S29 = tw_1.x;

#line 27
                float _S30 = tw_1.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_1 < 32U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_5)[k2_1] = cmul_0((*r_5)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S29 - ci_0 * _S30;
                    float _S31 = cr_0 * _S30 + ci_0 * _S29;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S31;

#line 29
                }

#line 37
                uint per_3 = 32U / _S24;
                uint _S32 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S32;

#line 39
                uint lane2_3 = tid_0 % _S32;

#line 39
                exchange_0(r_5, _S23, lgTB_1, 32U, 1024U, blk_3, lane_3, per_3, _S32, 32U, blk2_3, lane2_3, kernelContext_3);

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
    innermost_0(r_5);

#line 746 "mm_32768_fullCorrelation.slang"
    return;
}


#line 712
uint lgOf_0(uint i_4)
{

#line 712
    uint _S33;

#line 712
    if(i_4 < 2U)
    {

#line 712
        _S33 = 5U;

#line 712
    }
    else
    {

#line 712
        if(i_4 == 2U)
        {

#line 712
            _S33 = 5U;

#line 712
        }
        else
        {

#line 712
            _S33 = 1U;

#line 712
        }

#line 712
    }

#line 712
    return _S33;
}


#line 714
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 718
    uint lg_1 = lgOf_0(1U);

#line 718
    uint lg_2 = lgOf_0(0U);

#line 723
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1389
[[kernel]] void fullCorrelation(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], packed_float2 device* entryPointParams_output_1 [[buffer(3)]])
{

#line 1389
    thread KernelContext_0 kernelContext_4;

#line 1389
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1389
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1389
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1389
    (&kernelContext_4)->entryPointParams_output_0 = entryPointParams_output_1;

#line 1389
    threadgroup array<uint, int(16384)> stg_1;

#line 1389
    (&kernelContext_4)->stg_0 = &stg_1;



    uint pair_0 = gid_0.x;

#line 1393
    uint tid_1 = lid_0.x;
    uint _S34 = pair_0 / entryPointParams_1->ntmpl_0;

#line 1394
    uint _S35 = pair_0 % entryPointParams_1->ntmpl_0;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;
    thread array<float2, int(32)> r_6;

#line 1397
    uint i_5 = 0U;
    for(;;)
    {

#line 1398
        if(i_5 < 32U)
        {
        }
        else
        {

#line 1398
            break;
        }

#line 1399
        uint idx_0 = tid_1 + 1024U * i_5;
        r_6[i_5] = cmulConj_0(cload_0((&kernelContext_4)->entryPointParams_data_0, _S34 * 32768U + idx_0), cload_0((&kernelContext_4)->entryPointParams_tmpl_0, _S35 * 32768U + idx_0));

#line 1398
        i_5 = i_5 + 1U;

#line 1398
    }

#line 1398
    transform_0(&r_6, tid_1, &kernelContext_4);

#line 1398
    i_5 = 0U;

#line 1403
    for(;;)
    {

#line 1403
        if(i_5 < 32U)
        {
        }
        else
        {

#line 1403
            break;
        }

#line 1403
        *((&kernelContext_4)->entryPointParams_output_0+(pair_0 * 32768U + slotToIndex_0(tid_1 * 32U + i_5))) = packed_float2(float2(r_6[i_5].x, r_6[i_5].y)) ;

#line 1403
        i_5 = i_5 + 1U;

#line 1403
    }

    return;
}
