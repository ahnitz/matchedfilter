#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
#ifndef MF_C16_RAW
#define MF_C16_RAW 0u
#endif

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


#line 197 "mm_1024_fusedTierB_c16t2.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 197
    return;
}


#line 165
half2 cload_0(uint device* b_0, uint i_0)
{

#line 166
    uint p_0 = b_0[i_0];

#line 166
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 203
half2 dload_0(uint device* b_1, uint i_1)
{


    return cload_0(b_1, i_1);
}


#line 331
void cmulconjs_0(half2 ar_0, half2 ai_0, half2 br_0, half2 bi_0, half2 thread* pr_0, half2 thread* pi_0)
{
    *pr_0 = ar_0 * br_0 + ai_0 * bi_0;
    *pi_0 = ai_0 * br_0 - ar_0 * bi_0;
    return;
}


#line 343
void r4s_0(array<half2, int(16)> thread* re_0, array<half2, int(16)> thread* im_0, uint a_0, uint b_2, uint c_0, uint d_1)
{
    half2 t0r_0 = (*re_0)[a_0] + (*re_0)[c_0];

#line 345
    half2 t0i_0 = (*im_0)[a_0] + (*im_0)[c_0];
    half2 t1r_0 = (*re_0)[a_0] - (*re_0)[c_0];

#line 346
    half2 t1i_0 = (*im_0)[a_0] - (*im_0)[c_0];
    half2 t2r_0 = (*re_0)[b_2] + (*re_0)[d_1];

#line 347
    half2 t2i_0 = (*im_0)[b_2] + (*im_0)[d_1];
    half2 t3r_0 = (*re_0)[b_2] - (*re_0)[d_1];
    half2 j3r_0 = - ((*im_0)[b_2] - (*im_0)[d_1]);
    (*re_0)[a_0] = t0r_0 + t2r_0;

#line 350
    (*im_0)[a_0] = t0i_0 + t2i_0;
    (*re_0)[b_2] = t1r_0 + j3r_0;

#line 351
    (*im_0)[b_2] = t1i_0 + t3r_0;
    (*re_0)[c_0] = t0r_0 - t2r_0;

#line 352
    (*im_0)[c_0] = t0i_0 - t2i_0;
    (*re_0)[d_1] = t1r_0 - j3r_0;

#line 353
    (*im_0)[d_1] = t1i_0 - t3r_0;
    return;
}


#line 343
void r4s_1(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint a_1, uint b_3, uint c_1, uint d_2)
{
    half2 t0r_1 = (*re_1)[a_1] + (*re_1)[c_1];

#line 345
    half2 t0i_1 = (*im_1)[a_1] + (*im_1)[c_1];
    half2 t1r_1 = (*re_1)[a_1] - (*re_1)[c_1];

#line 346
    half2 t1i_1 = (*im_1)[a_1] - (*im_1)[c_1];
    half2 t2r_1 = (*re_1)[b_3] + (*re_1)[d_2];

#line 347
    half2 t2i_1 = (*im_1)[b_3] + (*im_1)[d_2];
    half2 t3r_1 = (*re_1)[b_3] - (*re_1)[d_2];
    half2 j3r_1 = - ((*im_1)[b_3] - (*im_1)[d_2]);
    (*re_1)[a_1] = t0r_1 + t2r_1;

#line 350
    (*im_1)[a_1] = t0i_1 + t2i_1;
    (*re_1)[b_3] = t1r_1 + j3r_1;

#line 351
    (*im_1)[b_3] = t1i_1 + t3r_1;
    (*re_1)[c_1] = t0r_1 - t2r_1;

#line 352
    (*im_1)[c_1] = t0i_1 - t2i_1;
    (*re_1)[d_2] = t1r_1 - j3r_1;

#line 353
    (*im_1)[d_2] = t1i_1 - t3r_1;
    return;
}


#line 322
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 322
    half2 _S2 = half2(wr_0) ;

#line 322
    half2 _S3 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S3 + *xi_0 * _S2;
    *xr_0 = *xr_0 * _S2 - *xi_0 * _S3;

#line 326
    *xi_0 = ni_0;
    return;
}


#line 356
void swap2_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2, uint p_1, uint q_0)
{

    half2 t_0 = (*re_2)[p_1];

#line 359
    (*re_2)[p_1] = (*re_2)[q_0];

#line 359
    (*re_2)[q_0] = t_0;
    half2 t_1 = (*im_2)[p_1];

#line 360
    (*im_2)[p_1] = (*im_2)[q_0];

#line 360
    (*im_2)[q_0] = t_1;
    return;
}


#line 356
void swap2_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint p_2, uint q_1)
{

    half2 t_2 = (*re_3)[p_2];

#line 359
    (*re_3)[p_2] = (*re_3)[q_1];

#line 359
    (*re_3)[q_1] = t_2;
    half2 t_3 = (*im_3)[p_2];

#line 360
    (*im_3)[p_2] = (*im_3)[q_1];

#line 360
    (*im_3)[q_1] = t_3;
    return;
}


#line 394
void dft16s_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4)
{

#line 394
    uint n1_0 = 0U;

    for(;;)
    {

#line 396
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 396
            break;
        }

#line 396
        r4s_0(re_4, im_4, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 396
        n1_0 = n1_0 + 1U;

#line 396
    }


    cmulw_0(&(*re_4)[int(5)], &(*im_4)[int(5)], 0.923828125h, 0.382568359375h);
    cmulw_0(&(*re_4)[int(9)], &(*im_4)[int(9)], 0.70703125h, 0.70703125h);
    cmulw_0(&(*re_4)[int(13)], &(*im_4)[int(13)], 0.382568359375h, 0.923828125h);
    cmulw_0(&(*re_4)[int(6)], &(*im_4)[int(6)], 0.70703125h, 0.70703125h);
    cmulw_0(&(*re_4)[int(10)], &(*im_4)[int(10)], 0.0h, 1.0h);
    cmulw_0(&(*re_4)[int(14)], &(*im_4)[int(14)], -0.70703125h, 0.70703125h);
    cmulw_0(&(*re_4)[int(7)], &(*im_4)[int(7)], 0.382568359375h, 0.923828125h);
    cmulw_0(&(*re_4)[int(11)], &(*im_4)[int(11)], -0.70703125h, 0.70703125h);
    cmulw_0(&(*re_4)[int(15)], &(*im_4)[int(15)], -0.923828125h, -0.382568359375h);

#line 407
    uint k2_0 = 0U;
    for(;;)
    {

#line 408
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 408
            break;
        }

#line 409
        uint _S4 = 4U * k2_0;

#line 409
        r4s_0(re_4, im_4, _S4, _S4 + 1U, _S4 + 2U, _S4 + 3U);

#line 408
        k2_0 = k2_0 + 1U;

#line 408
    }

    swap2_0(re_4, im_4, 1U, 4U);

#line 410
    swap2_0(re_4, im_4, 2U, 8U);

#line 410
    swap2_0(re_4, im_4, 3U, 12U);
    swap2_0(re_4, im_4, 6U, 9U);

#line 411
    swap2_0(re_4, im_4, 7U, 13U);

#line 411
    swap2_0(re_4, im_4, 11U, 14U);
    return;
}


#line 64 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 270 "mm_1024_fusedTierB_c16t2.slang"
uint computeWant_0(uint d_3, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S5 = max(TB_0, 1U);

#line 272
    uint j_0 = d_3 / _S5;

#line 272
    uint m_0 = d_3 % _S5;

#line 272
    uint _S6;
    if(TB_0 <= 16U)
    {

#line 273
        _S6 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 273
    }
    else
    {

#line 273
        _S6 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_3;

#line 273
    }

#line 273
    return _S6;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint ntmpl_0;
    uint winStart_1;
    uint winEnd_1;
    uint binsize_0;
    int binShift_0;
    uint nbins_0;
    uint thrBits_0;
};


#line 246 "mm_1024_fusedTierB_c16t2.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(1024)> threadgroup* stg_0;
};


#line 246
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 246
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 246
    return;
}


#line 247
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 247
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 432
void exchangeS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{
    uint j_1;

    thread array<half2, int(16)> outr_0;

#line 436
    thread array<half2, int(16)> outi_0;

#line 436
    uint z_0 = 0U;
    for(;;)
    {

#line 437
        if(z_0 < 16U)
        {
        }
        else
        {

#line 437
            break;
        }

#line 437
        half2 _S7 = half2(float2(0.0f) );

#line 437
        outr_0[z_0] = _S7;

#line 437
        outi_0[z_0] = _S7;

#line 437
        z_0 = z_0 + 1U;

#line 437
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S8 = p0_0 & lenMask_0;
    uint _S9 = (_S8 >> lgSpan_0) * 64U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S8 & spanMask_0);

#line 442
    uint c_2 = 0U;
    for(;;)
    {

#line 443
        if(c_2 < 1U)
        {
        }
        else
        {

#line 443
            break;
        }

#line 443
        for(;;)
        {

#line 443
            for(;;)
            {

#line 444
                for(;;)
                {

#line 445
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 445
                    j_1 = 0U;
                    for(;;)
                    {

#line 446
                        if(j_1 < 16U)
                        {
                        }
                        else
                        {

#line 446
                            break;
                        }

#line 447
                        uint _S10 = j_1 * 64U + kernelContext_2->_tid_0;

#line 447
                        stgPut_0(_S10, (*re_5)[c_2 * 16U + j_1], kernelContext_2);

#line 446
                        j_1 = j_1 + 1U;

#line 446
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 448
                    uint d_4 = 0U;
                    for(;;)
                    {

#line 449
                        if(d_4 < 16U)
                        {
                        }
                        else
                        {

#line 449
                            break;
                        }
                        uint pz_0 = computeWant_0(d_4, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S11 = pz_0 & lenMask_0;
                        uint az_0 = (_S11 >> lgSpan_0) * 64U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S11 & spanMask_0);

#line 453
                        half2 _S12 = stgGet_0(_S9 + az_0 - c_2 * 16U * 64U, kernelContext_2);



                        outr_0[d_4] = _S12;

#line 449
                        d_4 = d_4 + 1U;

#line 449
                    }

#line 444
                    break;
                }

#line 444
                break;
            }

#line 444
            for(;;)
            {

#line 444
                for(;;)
                {

#line 445
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 445
                    uint j_2 = 0U;
                    for(;;)
                    {

#line 446
                        if(j_2 < 16U)
                        {
                        }
                        else
                        {

#line 446
                            break;
                        }

#line 447
                        uint _S13 = j_2 * 64U + kernelContext_2->_tid_0;

#line 447
                        stgPut_0(_S13, (*im_5)[c_2 * 16U + j_2], kernelContext_2);

#line 446
                        j_2 = j_2 + 1U;

#line 446
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 448
                    uint d_5 = 0U;
                    for(;;)
                    {

#line 449
                        if(d_5 < 16U)
                        {
                        }
                        else
                        {

#line 449
                            break;
                        }
                        uint pz_1 = computeWant_0(d_5, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S14 = pz_1 & lenMask_0;
                        uint az_1 = (_S14 >> lgSpan_0) * 64U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);

#line 453
                        half2 _S15 = stgGet_0(_S9 + az_1 - c_2 * 16U * 64U, kernelContext_2);



                        outi_0[d_5] = _S15;

#line 449
                        d_5 = d_5 + 1U;

#line 449
                    }

#line 444
                    break;
                }

#line 444
                break;
            }

#line 444
            break;
        }

#line 443
        c_2 = c_2 + 1U;

#line 443
    }

#line 443
    j_1 = 0U;

#line 462
    for(;;)
    {

#line 462
        if(j_1 < 16U)
        {
        }
        else
        {

#line 462
            break;
        }

#line 462
        (*re_5)[j_1] = outr_0[j_1];

#line 462
        (*im_5)[j_1] = outi_0[j_1];

#line 462
        j_1 = j_1 + 1U;

#line 462
    }
    return;
}


#line 370
void dft4s_0(array<half2, int(16)> thread* re_6, array<half2, int(16)> thread* im_6, uint o_0)
{
    uint _S16 = o_0 + 1U;

#line 372
    uint _S17 = o_0 + 2U;

#line 372
    r4s_1(re_6, im_6, o_0, _S16, _S17, o_0 + 3U);
    swap2_1(re_6, im_6, _S16, _S17);
    return;
}


#line 465
void innermostS_0(array<half2, int(16)> thread* re_7, array<half2, int(16)> thread* im_7)
{

#line 465
    uint b_4 = 0U;



    for(;;)
    {

#line 469
        if(b_4 < 4U)
        {
        }
        else
        {

#line 469
            break;
        }

#line 469
        dft4s_0(re_7, im_7, b_4 * 4U);

#line 469
        b_4 = b_4 + 1U;

#line 469
    }

    return;
}


#line 758
uint lgOf_0(uint i_4)
{

#line 758
    uint _S18;

#line 758
    if(i_4 < 2U)
    {

#line 758
        _S18 = 4U;

#line 758
    }
    else
    {

#line 758
        _S18 = 1U;

#line 758
    }

#line 758
    return _S18;
}


#line 760
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 764
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 764
    uint lg_2 = lgOf_0(1U);

#line 764
    uint lg_3 = lgOf_0(0U);

#line 769
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 418
half2 mag2s_0(half2 re_8, half2 im_8)
{

#line 418
    return re_8 * re_8 + im_8 * im_8;
}


#line 47 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S19 = ((MF_C16_RAW));

#line 50
    return _S19;
}


#line 299 "mm_1024_fusedTierB_c16t2.slang"
float2 c16Bound_0(float2 v_1, float energy_0)
{

#line 52 "twiddle.slang"
    uint _S20 = mfC16RawFlag_0();

#line 301 "mm_1024_fusedTierB_c16t2.slang"
    if((1U - _S20) == 0U)
    {

#line 301
        return v_1;
    }

#line 302
    float m_1 = length(v_1);
    float b_5 = m_1 * 1.00146484375f + 0.00755659164860845f * sqrt(energy_0);

#line 303
    float2 _S21;
    if(m_1 > 0.0f)
    {

#line 304
        _S21 = v_1 * float2((b_5 / m_1)) ;

#line 304
    }
    else
    {

#line 304
        _S21 = float2(b_5, 0.0f);

#line 304
    }

#line 304
    return _S21;
}



float pairSum_0(uint tid_0, float v_2, KernelContext_0 thread* kernelContext_3)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0 + tid_0] = (as_type<uint>((v_2)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 313
    uint k_0 = 0U;

#line 313
    float t_4 = 0.0f;

    for(;;)
    {

#line 315
        if(k_0 < 64U)
        {
        }
        else
        {

#line 315
            break;
        }

#line 315
        float t_5 = t_4 + (as_type<float>(((*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0 + k_0])));

#line 315
        k_0 = k_0 + 1U;

#line 315
        t_4 = t_5;

#line 315
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_4;
}


#line 1158
void peakLane_0(uint pair_0, uint tid_1, uint lane_2, const array<half2, int(16)> thread* magv_0, const array<half2, int(16)> thread* re_9, const array<half2, int(16)> thread* im_9, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint thrBits_1, float energy_1, KernelContext_0 thread* kernelContext_4)
{


    threadgroup_barrier(mem_flags::mem_threadgroup);
    bool _S22 = tid_1 == 0U;

#line 1163
    if(_S22)
    {

#line 1163
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 1163
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 1163
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1173
    half2 _S23 = half2(float2(0.0f) );

#line 1173
    half2 bestH_0 = _S23;

#line 1173
    uint i_5 = 0U;

#line 1173
    half2 poison_0 = _S23;
    for(;;)
    {

#line 1174
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1174
            break;
        }

#line 1174
        half2 _S24 = max(bestH_0, (*magv_0)[i_5]);

#line 1174
        half2 poison_1 = poison_0 + (*magv_0)[i_5] * _S23;

#line 1174
        uint i_6 = i_5 + 1U;

#line 1174
        bestH_0 = _S24;

#line 1174
        i_5 = i_6;

#line 1174
        poison_0 = poison_1;

#line 1174
    }
    bool _S25 = lane_2 == 0U;

#line 1175
    half _S26;

#line 1175
    if(_S25)
    {

#line 1175
        _S26 = poison_0.x;

#line 1175
    }
    else
    {

#line 1175
        _S26 = poison_0.y;

#line 1175
    }
    if(isnan(float(_S26)))
    {

#line 1176
        i_5 = 2139095040U;

#line 1176
    }
    else
    {

#line 1176
        if(_S25)
        {

#line 1176
            _S26 = bestH_0.x;

#line 1176
        }
        else
        {

#line 1176
            _S26 = bestH_0.y;

#line 1176
        }

#line 1176
        i_5 = (as_type<uint>((float(_S26))));

#line 1176
    }

    uint wm_0 = simd_max(max(thrBits_1, i_5));
    bool _S27 = simd_is_first();

#line 1179
    bool _S28;

#line 1179
    if(_S27)
    {

#line 1179
        _S28 = wm_0 > thrBits_1;

#line 1179
    }
    else
    {

#line 1179
        _S28 = false;

#line 1179
    }

#line 1179
    if(_S28)
    {

#line 1179
        uint _S29 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1179
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1183
    uint winner_0 = 4294967295U;

#line 1183
    i_5 = 0U;


    for(;;)
    {

#line 1186
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1186
            break;
        }

#line 1187
        if(_S25)
        {

#line 1187
            _S26 = (*magv_0)[i_5].x;

#line 1187
        }
        else
        {

#line 1187
            _S26 = (*magv_0)[i_5].y;

#line 1187
        }

#line 1187
        uint _S30 = min((as_type<uint>((float(_S26)))), 2139095040U);
        if(_S30 > thrBits_1)
        {

#line 1188
            _S28 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0]) == _S30;

#line 1188
        }
        else
        {

#line 1188
            _S28 = false;

#line 1188
        }

#line 1188
        if(_S28)
        {

#line 1188
            winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 1188
        }

#line 1186
        i_5 = i_5 + 1U;

#line 1186
    }

#line 1192
    uint waveWinner_0 = simd_min(winner_0);
    bool _S31 = simd_is_first();

#line 1193
    if(_S31)
    {

#line 1193
        _S28 = waveWinner_0 != 4294967295U;

#line 1193
    }
    else
    {

#line 1193
        _S28 = false;

#line 1193
    }

#line 1193
    if(_S28)
    {

#line 1194
        uint _S32 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1193
    }

#line 1198
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1198
    i_5 = 0U;
    for(;;)
    {

#line 1199
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1199
            break;
        }

#line 1200
        if(pair_0 != 4294967295U)
        {

#line 1200
            _S28 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == (tid_1 * 16U + i_5);

#line 1200
        }
        else
        {

#line 1200
            _S28 = false;

#line 1200
        }

#line 1200
        if(_S28)
        {

#line 1201
            *(peakIdx_0+pair_0) = int(slotToIndex_0(tid_1 * 16U + i_5));

#line 1201
            packed_float2 device* _S33 = peakVal_0+pair_0;
            if(_S25)
            {

#line 1202
                _S26 = (*re_9)[i_5].x;

#line 1202
            }
            else
            {

#line 1202
                _S26 = (*re_9)[i_5].y;

#line 1202
            }

#line 1202
            float _S34 = float(_S26);

#line 1202
            half _S35;
            if(_S25)
            {

#line 1203
                _S35 = (*im_9)[i_5].x;

#line 1203
            }
            else
            {

#line 1203
                _S35 = (*im_9)[i_5].y;

#line 1203
            }

#line 1202
            float2 _S36 = c16Bound_0(float2(_S34, float(_S35)), energy_1);

#line 1202
            *_S33 = packed_float2(_S36) ;

#line 1200
        }

#line 1199
        i_5 = i_5 + 1U;

#line 1199
    }

#line 1206
    if(pair_0 != 4294967295U)
    {

#line 1206
        _S28 = _S22;

#line 1206
    }
    else
    {

#line 1206
        _S28 = false;

#line 1206
    }

#line 1206
    if(_S28)
    {

#line 1206
        _S28 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1206
    }
    else
    {

#line 1206
        _S28 = false;

#line 1206
    }

#line 1206
    if(_S28)
    {

#line 1207
        *(peakIdx_0+pair_0) = int(-1);

#line 1207
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1206
    }



    return;
}


#line 1416
void filterTwo_0(uint pairA_0, uint pairB_0, uint tA_0, uint tB_0, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* tmpl_0, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_2, KernelContext_0 thread* kernelContext_5)
{

    uint _S37;

#line 1419
    uint k2_1;

#line 1419
    float cr_0;

#line 1419
    float ci_0;

#line 1419
    uint _S38;

    thread array<half2, int(16)> re_10;

#line 1421
    thread array<half2, int(16)> im_10;

#line 1421
    uint n2_0 = 0U;
    for(;;)
    {

#line 1422
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 1422
            break;
        }

#line 1423
        uint _S39 = 64U * n2_0;

#line 1423
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 1024U + tid_2 + _S39);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 1024U + tid_2 + _S39);
        half _S40 = (*dreg_0)[n2_0].x;
        half _S41 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S40, _S40), half2(_S41, _S41), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_10[n2_0], &im_10[n2_0]);

#line 1422
        n2_0 = n2_0 + 1U;

#line 1422
    }

#line 1422
    for(;;)
    {

#line 1422
        for(;;)
        {

#line 1432
            for(;;)
            {

                uint lgTB_0 = firstbithigh_0(64U);

#line 1435
                _S37 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(1024U);
                uint blk_2 = tid_2 >> lgTB_0;
                uint lane_3 = tid_2 & 63U;

                dft16s_0(&re_10, &im_10);

#line 1456
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 1024.0f);
                float _S42 = tw_0.x;

#line 1457
                float _S43 = tw_0.y;

#line 1457
                k2_1 = 0U;

#line 1457
                cr_0 = 1.0f;

#line 1457
                ci_0 = 0.0f;

                for(;;)
                {

#line 1459
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 1459
                        break;
                    }

#line 1460
                    cmulw_0(&re_10[k2_1], &im_10[k2_1], half(cr_0), half(ci_0));
                    float nr_0 = cr_0 * _S42 - ci_0 * _S43;
                    float _S44 = cr_0 * _S43 + ci_0 * _S42;

#line 1459
                    k2_1 = k2_1 + 1U;

#line 1459
                    cr_0 = nr_0;

#line 1459
                    ci_0 = _S44;

#line 1459
                }

#line 1467
                uint per_2 = 16U / max(64U, 1U);
                uint _S45 = max(4U, 1U);

#line 1468
                _S38 = _S45;
                uint blk2_2 = tid_2 / _S45;

#line 1469
                uint lane2_2 = tid_2 % _S45;

#line 1469
                exchangeS_0(&re_10, &im_10, lgLn_0, lgTB_0, 64U, 1024U, blk_2, lane_3, per_2, _S45, 64U, blk2_2, lane2_2, kernelContext_5);

#line 1432
                break;
            }

#line 1432
            break;
        }

#line 1432
        for(;;)
        {

#line 1432
            for(;;)
            {

                uint lgTB_1 = firstbithigh_0(4U);

                uint blk_3 = tid_2 >> lgTB_1;
                uint lane_4 = tid_2 & 3U;

                dft16s_0(&re_10, &im_10);

#line 1456
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_4) / 64.0f);
                float _S46 = tw_1.x;

#line 1457
                float _S47 = tw_1.y;

#line 1457
                k2_1 = 0U;

#line 1457
                cr_0 = 1.0f;

#line 1457
                ci_0 = 0.0f;

                for(;;)
                {

#line 1459
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 1459
                        break;
                    }

#line 1460
                    cmulw_0(&re_10[k2_1], &im_10[k2_1], half(cr_0), half(ci_0));
                    float nr_1 = cr_0 * _S46 - ci_0 * _S47;
                    float _S48 = cr_0 * _S47 + ci_0 * _S46;

#line 1459
                    k2_1 = k2_1 + 1U;

#line 1459
                    cr_0 = nr_1;

#line 1459
                    ci_0 = _S48;

#line 1459
                }

#line 1467
                uint per_3 = 16U / _S38;
                uint _S49 = max(0U, 1U);
                uint blk2_3 = tid_2 / _S49;

#line 1469
                uint lane2_3 = tid_2 % _S49;

#line 1469
                exchangeS_0(&re_10, &im_10, _S37, lgTB_1, 4U, 64U, blk_3, lane_4, per_3, _S49, 4U, blk2_3, lane2_3, kernelContext_5);

#line 1432
                break;
            }

#line 1432
            break;
        }

#line 1432
        break;
    }

#line 1472
    innermostS_0(&re_10, &im_10);

#line 1496
    thread array<half2, int(16)> magv_1;

#line 1496
    uint i_7 = 0U;

#line 1496
    float eA_0 = 0.0f;

#line 1496
    float eB_0 = 0.0f;

    for(;;)
    {

#line 1498
        if(i_7 < 16U)
        {
        }
        else
        {

#line 1498
            break;
        }

#line 1499
        uint idx_0 = slotToIndex_0(tid_2 * 16U + i_7);

#line 1499
        bool live_0;
        if(idx_0 >= winStart_3)
        {

#line 1500
            live_0 = idx_0 < winEnd_3;

#line 1500
        }
        else
        {

#line 1500
            live_0 = false;

#line 1500
        }
        half2 mg_0 = mag2s_0(re_10[i_7], im_10[i_7]);
        float eA_1 = eA_0 + float(mg_0.x);

#line 1502
        float eB_1 = eB_0 + float(mg_0.y);

#line 1502
        half2 _S50;
        if(live_0)
        {

#line 1503
            _S50 = mg_0;

#line 1503
        }
        else
        {

#line 1503
            _S50 = half2(float2(0.0f) );

#line 1503
        }

#line 1503
        magv_1[i_7] = _S50;

#line 1508
        if(live_0)
        {
            uint ov_0 = ((((uint(as_type<ushort>(re_10[i_7][0U])) & 65535U) | (uint(as_type<ushort>(re_10[i_7][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(im_10[i_7][0U])) & 65535U) | (uint(as_type<ushort>(im_10[i_7][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1510
            uint _S51 = (uint(as_type<ushort>(magv_1[i_7][0U])) & 65535U) | (uint(as_type<ushort>(magv_1[i_7][1U])) << 16U);

#line 1510
            uint mb_0;

            if((ov_0 & 32768U) != 0U)
            {

#line 1512
                mb_0 = (_S51 & 4294901760U) | 31744U;

#line 1512
            }
            else
            {

#line 1512
                mb_0 = _S51;

#line 1512
            }

#line 1512
            uint mb_1;
            if((ov_0 & 2147483648U) != 0U)
            {

#line 1513
                mb_1 = (mb_0 & 65535U) | 2080374784U;

#line 1513
            }
            else
            {

#line 1513
                mb_1 = mb_0;

#line 1513
            }
            magv_1[i_7] = half2(as_type<half>(ushort(mb_1 & 65535U)), as_type<half>(ushort((mb_1 >> 16U) & 65535U)));

#line 1508
        }

#line 1498
        i_7 = i_7 + 1U;

#line 1498
        eA_0 = eA_1;

#line 1498
        eB_0 = eB_1;

#line 1498
    }

#line 1498
    float _S52 = pairSum_0(tid_2, eA_0, kernelContext_5);

#line 1518
    float eA_2 = _S52 / 1024.0f;

#line 1518
    float _S53 = pairSum_0(tid_2, eB_0, kernelContext_5);
    float eB_2 = _S53 / 1024.0f;

#line 1519
    thread array<half2, int(16)> _S54 = magv_1;

#line 1519
    thread array<half2, int(16)> _S55 = re_10;

#line 1519
    thread array<half2, int(16)> _S56 = im_10;

#line 1519
    peakLane_0(pairA_0, tid_2, 0U, &_S54, &_S55, &_S56, peakIdx_1, peakVal_1, winStart_3, winEnd_3, thrBits_2, eA_2, kernelContext_5);

#line 1519
    thread array<half2, int(16)> _S57 = magv_1;

#line 1519
    thread array<half2, int(16)> _S58 = re_10;

#line 1519
    thread array<half2, int(16)> _S59 = im_10;

#line 1519
    peakLane_0(pairB_0, tid_2, 1U, &_S57, &_S58, &_S59, peakIdx_1, peakVal_1, winStart_3, winEnd_3, thrBits_2, eB_2, kernelContext_5);



    return;
}


void filterPair_0(uint pair_1, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_2, packed_float2 device* peakVal_2, uint ntmpl_1, uint winStart_4, uint winEnd_4, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, KernelContext_0 thread* kernelContext_6)
{

#line 1527
    thread uint _S60 = winStart_4;

#line 1527
    thread uint _S61 = winEnd_4;

#line 1533
    kernelContext_6->_tid_0 = tid_3;

#line 1553
    uint tiles_0 = (ntmpl_1 + 2U - 1U) / 2U;
    uint slots_0 = binsize_1 * tiles_0;
    bool slotOk_0 = pair_1 < slots_0;

#line 1555
    uint q_2;
    if(slotOk_0)
    {

#line 1556
        q_2 = pair_1;

#line 1556
    }
    else
    {

#line 1556
        q_2 = slots_0 - 1U;

#line 1556
    }
    uint d_6 = q_2 / tiles_0;

#line 1557
    uint t0_0 = (q_2 - d_6 * tiles_0) * 2U;
    uint _S62 = d_6 * ntmpl_1 + t0_0;
    rowWindow_0(d_6, &_S60, &_S61);

#line 1570
    thread array<half2, int(16)> dreg_1;

#line 1570
    uint n2_1 = 0U;

    for(;;)
    {

#line 1572
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1572
            break;
        }

#line 1573
        dreg_1[n2_1] = dload_0(data_0, d_6 * 1024U + tid_3 + 64U * n2_1);

#line 1572
        n2_1 = n2_1 + 1U;

#line 1572
    }

#line 1572
    uint k_1 = 0U;

#line 1580
    for(;;)
    {

#line 1580
        if(k_1 < 2U)
        {
        }
        else
        {

#line 1580
            break;
        }

#line 1580
        bool okA_0;
        if(slotOk_0)
        {

#line 1581
            okA_0 = (t0_0 + k_1) < ntmpl_1;

#line 1581
        }
        else
        {

#line 1581
            okA_0 = false;

#line 1581
        }

#line 1581
        bool okB_0;

#line 1581
        if(slotOk_0)
        {

#line 1581
            okB_0 = (t0_0 + k_1 + 1U) < ntmpl_1;

#line 1581
        }
        else
        {

#line 1581
            okB_0 = false;

#line 1581
        }
        if(okA_0)
        {

#line 1582
            q_2 = _S62 + k_1;

#line 1582
        }
        else
        {

#line 1582
            q_2 = 4294967295U;

#line 1582
        }

#line 1582
        if(okB_0)
        {

#line 1582
            n2_1 = _S62 + k_1 + 1U;

#line 1582
        }
        else
        {

#line 1582
            n2_1 = 4294967295U;

#line 1582
        }
        uint _S63 = t0_0 + k_1;

#line 1583
        uint _S64 = ntmpl_1 - 1U;

#line 1583
        uint _S65 = min(_S63, _S64);

#line 1583
        uint _S66 = min(_S63 + 1U, _S64);

#line 1583
        thread array<half2, int(16)> _S67 = dreg_1;

#line 1583
        filterTwo_0(q_2, n2_1, _S65, _S66, tid_3, &_S67, tmpl_1, peakIdx_2, peakVal_2, _S60, _S61, thrBits_3, kernelContext_6);

#line 1580
        k_1 = k_1 + 2U;

#line 1580
    }

#line 1596
    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1600
    thread KernelContext_0 kernelContext_7;

#line 1600
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1600
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1600
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1600
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1600
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1600
    threadgroup array<uint, int(1024)> stg_1;

#line 1600
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1617
    uint _pr_0 = gid_0.x;

#line 1617
    uint _t_0 = lid_0.x;
    (&kernelContext_7)->_stgBase_0 = 0U;

#line 1618
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);

#line 1626
    return;
}
