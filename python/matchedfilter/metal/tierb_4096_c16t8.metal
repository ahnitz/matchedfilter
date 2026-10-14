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


#line 197 "mm_4096_fusedTierB_c16t8.slang"
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
void swap2_0(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint p_1, uint q_0)
{

    half2 t_0 = (*re_1)[p_1];

#line 359
    (*re_1)[p_1] = (*re_1)[q_0];

#line 359
    (*re_1)[q_0] = t_0;
    half2 t_1 = (*im_1)[p_1];

#line 360
    (*im_1)[p_1] = (*im_1)[q_0];

#line 360
    (*im_1)[q_0] = t_1;
    return;
}


#line 394
void dft16s_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2)
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
        r4s_0(re_2, im_2, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 396
        n1_0 = n1_0 + 1U;

#line 396
    }


    cmulw_0(&(*re_2)[int(5)], &(*im_2)[int(5)], 0.923828125h, 0.382568359375h);
    cmulw_0(&(*re_2)[int(9)], &(*im_2)[int(9)], 0.70703125h, 0.70703125h);
    cmulw_0(&(*re_2)[int(13)], &(*im_2)[int(13)], 0.382568359375h, 0.923828125h);
    cmulw_0(&(*re_2)[int(6)], &(*im_2)[int(6)], 0.70703125h, 0.70703125h);
    cmulw_0(&(*re_2)[int(10)], &(*im_2)[int(10)], 0.0h, 1.0h);
    cmulw_0(&(*re_2)[int(14)], &(*im_2)[int(14)], -0.70703125h, 0.70703125h);
    cmulw_0(&(*re_2)[int(7)], &(*im_2)[int(7)], 0.382568359375h, 0.923828125h);
    cmulw_0(&(*re_2)[int(11)], &(*im_2)[int(11)], -0.70703125h, 0.70703125h);
    cmulw_0(&(*re_2)[int(15)], &(*im_2)[int(15)], -0.923828125h, -0.382568359375h);

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
        r4s_0(re_2, im_2, _S4, _S4 + 1U, _S4 + 2U, _S4 + 3U);

#line 408
        k2_0 = k2_0 + 1U;

#line 408
    }

    swap2_0(re_2, im_2, 1U, 4U);

#line 410
    swap2_0(re_2, im_2, 2U, 8U);

#line 410
    swap2_0(re_2, im_2, 3U, 12U);
    swap2_0(re_2, im_2, 6U, 9U);

#line 411
    swap2_0(re_2, im_2, 7U, 13U);

#line 411
    swap2_0(re_2, im_2, 11U, 14U);
    return;
}


#line 394
void dft16s_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3)
{

#line 394
    uint n1_1 = 0U;

    for(;;)
    {

#line 396
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 396
            break;
        }

#line 396
        r4s_0(re_3, im_3, n1_1, n1_1 + 4U, n1_1 + 8U, n1_1 + 12U);

#line 396
        n1_1 = n1_1 + 1U;

#line 396
    }


    cmulw_0(&(*re_3)[int(5)], &(*im_3)[int(5)], 0.923828125h, 0.382568359375h);
    cmulw_0(&(*re_3)[int(9)], &(*im_3)[int(9)], 0.70703125h, 0.70703125h);
    cmulw_0(&(*re_3)[int(13)], &(*im_3)[int(13)], 0.382568359375h, 0.923828125h);
    cmulw_0(&(*re_3)[int(6)], &(*im_3)[int(6)], 0.70703125h, 0.70703125h);
    cmulw_0(&(*re_3)[int(10)], &(*im_3)[int(10)], 0.0h, 1.0h);
    cmulw_0(&(*re_3)[int(14)], &(*im_3)[int(14)], -0.70703125h, 0.70703125h);
    cmulw_0(&(*re_3)[int(7)], &(*im_3)[int(7)], 0.382568359375h, 0.923828125h);
    cmulw_0(&(*re_3)[int(11)], &(*im_3)[int(11)], -0.70703125h, 0.70703125h);
    cmulw_0(&(*re_3)[int(15)], &(*im_3)[int(15)], -0.923828125h, -0.382568359375h);

#line 407
    uint k2_1 = 0U;
    for(;;)
    {

#line 408
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 408
            break;
        }

#line 409
        uint _S5 = 4U * k2_1;

#line 409
        r4s_0(re_3, im_3, _S5, _S5 + 1U, _S5 + 2U, _S5 + 3U);

#line 408
        k2_1 = k2_1 + 1U;

#line 408
    }

    swap2_0(re_3, im_3, 1U, 4U);

#line 410
    swap2_0(re_3, im_3, 2U, 8U);

#line 410
    swap2_0(re_3, im_3, 3U, 12U);
    swap2_0(re_3, im_3, 6U, 9U);

#line 411
    swap2_0(re_3, im_3, 7U, 13U);

#line 411
    swap2_0(re_3, im_3, 11U, 14U);
    return;
}


#line 64 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 270 "mm_4096_fusedTierB_c16t8.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S6 = max(TB_0, 1U);

#line 272
    uint j_0 = d_2 / _S6;

#line 272
    uint m_0 = d_2 % _S6;

#line 272
    uint _S7;
    if(TB_0 <= 16U)
    {

#line 273
        _S7 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 273
    }
    else
    {

#line 273
        _S7 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 273
    }

#line 273
    return _S7;
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


#line 246 "mm_4096_fusedTierB_c16t8.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(4096)> threadgroup* stg_0;
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
void exchangeS_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
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
        half2 _S8 = half2(float2(0.0f) );

#line 437
        outr_0[z_0] = _S8;

#line 437
        outi_0[z_0] = _S8;

#line 437
        z_0 = z_0 + 1U;

#line 437
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S9 = p0_0 & lenMask_0;
    uint _S10 = (_S9 >> lgSpan_0) * 256U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S9 & spanMask_0);

#line 442
    uint c_1 = 0U;
    for(;;)
    {

#line 443
        if(c_1 < 1U)
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
                        uint _S11 = j_1 * 256U + kernelContext_2->_tid_0;

#line 447
                        stgPut_0(_S11, (*re_4)[c_1 * 16U + j_1], kernelContext_2);

#line 446
                        j_1 = j_1 + 1U;

#line 446
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 448
                    uint d_3 = 0U;
                    for(;;)
                    {

#line 449
                        if(d_3 < 16U)
                        {
                        }
                        else
                        {

#line 449
                            break;
                        }
                        uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S12 = pz_0 & lenMask_0;
                        uint az_0 = (_S12 >> lgSpan_0) * 256U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S12 & spanMask_0);

#line 453
                        half2 _S13 = stgGet_0(_S10 + az_0 - c_1 * 16U * 256U, kernelContext_2);



                        outr_0[d_3] = _S13;

#line 449
                        d_3 = d_3 + 1U;

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
                        uint _S14 = j_2 * 256U + kernelContext_2->_tid_0;

#line 447
                        stgPut_0(_S14, (*im_4)[c_1 * 16U + j_2], kernelContext_2);

#line 446
                        j_2 = j_2 + 1U;

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
                        uint pz_1 = computeWant_0(d_4, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S15 = pz_1 & lenMask_0;
                        uint az_1 = (_S15 >> lgSpan_0) * 256U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 453
                        half2 _S16 = stgGet_0(_S10 + az_1 - c_1 * 16U * 256U, kernelContext_2);



                        outi_0[d_4] = _S16;

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
            break;
        }

#line 443
        c_1 = c_1 + 1U;

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
        (*re_4)[j_1] = outr_0[j_1];

#line 462
        (*im_4)[j_1] = outi_0[j_1];

#line 462
        j_1 = j_1 + 1U;

#line 462
    }
    return;
}


#line 465
void innermostS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5)
{
    dft16s_1(re_5, im_5);



    return;
}


#line 758
uint lgOf_0(uint i_4)
{

#line 758
    uint _S17;

#line 758
    if(i_4 < 2U)
    {

#line 758
        _S17 = 4U;

#line 758
    }
    else
    {

#line 758
        if(i_4 == 2U)
        {

#line 758
            _S17 = 4U;

#line 758
        }
        else
        {

#line 758
            _S17 = 1U;

#line 758
        }

#line 758
    }

#line 758
    return _S17;
}


#line 760
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 764
    uint lg_1 = lgOf_0(1U);

#line 764
    uint lg_2 = lgOf_0(0U);

#line 769
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 418
half2 mag2s_0(half2 re_6, half2 im_6)
{

#line 418
    return re_6 * re_6 + im_6 * im_6;
}


#line 47 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S18 = ((MF_C16_RAW));

#line 50
    return _S18;
}


#line 299 "mm_4096_fusedTierB_c16t8.slang"
float2 c16Bound_0(float2 v_1, float energy_0)
{

#line 52 "twiddle.slang"
    uint _S19 = mfC16RawFlag_0();

#line 301 "mm_4096_fusedTierB_c16t8.slang"
    if((1U - _S19) == 0U)
    {

#line 301
        return v_1;
    }

#line 302
    float m_1 = length(v_1);
    float b_3 = m_1 * 1.00146484375f + 0.00893051736056805f * sqrt(energy_0);

#line 303
    float2 _S20;
    if(m_1 > 0.0f)
    {

#line 304
        _S20 = v_1 * float2((b_3 / m_1)) ;

#line 304
    }
    else
    {

#line 304
        _S20 = float2(b_3, 0.0f);

#line 304
    }

#line 304
    return _S20;
}



float pairSum_0(uint tid_0, float v_2, KernelContext_0 thread* kernelContext_3)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0 + tid_0] = (as_type<uint>((v_2)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 313
    uint k_0 = 0U;

#line 313
    float t_2 = 0.0f;

    for(;;)
    {

#line 315
        if(k_0 < 256U)
        {
        }
        else
        {

#line 315
            break;
        }

#line 315
        float t_3 = t_2 + (as_type<float>(((*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0 + k_0])));

#line 315
        k_0 = k_0 + 1U;

#line 315
        t_2 = t_3;

#line 315
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_2;
}


#line 1158
void peakLane_0(uint pair_0, uint tid_1, uint lane_2, const array<half2, int(16)> thread* magv_0, const array<half2, int(16)> thread* re_7, const array<half2, int(16)> thread* im_7, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint thrBits_1, float energy_1, KernelContext_0 thread* kernelContext_4)
{


    threadgroup_barrier(mem_flags::mem_threadgroup);
    bool _S21 = tid_1 == 0U;

#line 1163
    if(_S21)
    {

#line 1163
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 1163
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 1163
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1173
    half2 _S22 = half2(float2(0.0f) );

#line 1173
    half2 bestH_0 = _S22;

#line 1173
    uint i_5 = 0U;

#line 1173
    half2 poison_0 = _S22;
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
        half2 _S23 = max(bestH_0, (*magv_0)[i_5]);

#line 1174
        half2 poison_1 = poison_0 + (*magv_0)[i_5] * _S22;

#line 1174
        uint i_6 = i_5 + 1U;

#line 1174
        bestH_0 = _S23;

#line 1174
        i_5 = i_6;

#line 1174
        poison_0 = poison_1;

#line 1174
    }
    bool _S24 = lane_2 == 0U;

#line 1175
    half _S25;

#line 1175
    if(_S24)
    {

#line 1175
        _S25 = poison_0.x;

#line 1175
    }
    else
    {

#line 1175
        _S25 = poison_0.y;

#line 1175
    }
    if(isnan(float(_S25)))
    {

#line 1176
        i_5 = 2139095040U;

#line 1176
    }
    else
    {

#line 1176
        if(_S24)
        {

#line 1176
            _S25 = bestH_0.x;

#line 1176
        }
        else
        {

#line 1176
            _S25 = bestH_0.y;

#line 1176
        }

#line 1176
        i_5 = (as_type<uint>((float(_S25))));

#line 1176
    }

    uint wm_0 = simd_max(max(thrBits_1, i_5));
    bool _S26 = simd_is_first();

#line 1179
    bool _S27;

#line 1179
    if(_S26)
    {

#line 1179
        _S27 = wm_0 > thrBits_1;

#line 1179
    }
    else
    {

#line 1179
        _S27 = false;

#line 1179
    }

#line 1179
    if(_S27)
    {

#line 1179
        uint _S28 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

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
        if(_S24)
        {

#line 1187
            _S25 = (*magv_0)[i_5].x;

#line 1187
        }
        else
        {

#line 1187
            _S25 = (*magv_0)[i_5].y;

#line 1187
        }

#line 1187
        uint _S29 = min((as_type<uint>((float(_S25)))), 2139095040U);
        if(_S29 > thrBits_1)
        {

#line 1188
            _S27 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0]) == _S29;

#line 1188
        }
        else
        {

#line 1188
            _S27 = false;

#line 1188
        }

#line 1188
        if(_S27)
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
    bool _S30 = simd_is_first();

#line 1193
    if(_S30)
    {

#line 1193
        _S27 = waveWinner_0 != 4294967295U;

#line 1193
    }
    else
    {

#line 1193
        _S27 = false;

#line 1193
    }

#line 1193
    if(_S27)
    {

#line 1194
        uint _S31 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

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
            _S27 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == (tid_1 * 16U + i_5);

#line 1200
        }
        else
        {

#line 1200
            _S27 = false;

#line 1200
        }

#line 1200
        if(_S27)
        {

#line 1201
            *(peakIdx_0+pair_0) = int(slotToIndex_0(tid_1 * 16U + i_5));

#line 1201
            packed_float2 device* _S32 = peakVal_0+pair_0;
            if(_S24)
            {

#line 1202
                _S25 = (*re_7)[i_5].x;

#line 1202
            }
            else
            {

#line 1202
                _S25 = (*re_7)[i_5].y;

#line 1202
            }

#line 1202
            float _S33 = float(_S25);

#line 1202
            half _S34;
            if(_S24)
            {

#line 1203
                _S34 = (*im_7)[i_5].x;

#line 1203
            }
            else
            {

#line 1203
                _S34 = (*im_7)[i_5].y;

#line 1203
            }

#line 1202
            float2 _S35 = c16Bound_0(float2(_S33, float(_S34)), energy_1);

#line 1202
            *_S32 = packed_float2(_S35) ;

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
        _S27 = _S21;

#line 1206
    }
    else
    {

#line 1206
        _S27 = false;

#line 1206
    }

#line 1206
    if(_S27)
    {

#line 1206
        _S27 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1206
    }
    else
    {

#line 1206
        _S27 = false;

#line 1206
    }

#line 1206
    if(_S27)
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

    uint _S36;

#line 1419
    uint k2_2;

#line 1419
    float cr_0;

#line 1419
    float ci_0;

#line 1419
    uint _S37;

    thread array<half2, int(16)> re_8;

#line 1421
    thread array<half2, int(16)> im_8;

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
        uint _S38 = 256U * n2_0;

#line 1423
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 4096U + tid_2 + _S38);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 4096U + tid_2 + _S38);
        half _S39 = (*dreg_0)[n2_0].x;
        half _S40 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S39, _S39), half2(_S40, _S40), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_8[n2_0], &im_8[n2_0]);

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

                uint lgTB_0 = firstbithigh_0(256U);

#line 1435
                _S36 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(4096U);
                uint blk_2 = tid_2 >> lgTB_0;
                uint lane_3 = tid_2 & 255U;

                dft16s_0(&re_8, &im_8);

#line 1456
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 4096.0f);
                float _S41 = tw_0.x;

#line 1457
                float _S42 = tw_0.y;

#line 1457
                k2_2 = 0U;

#line 1457
                cr_0 = 1.0f;

#line 1457
                ci_0 = 0.0f;

                for(;;)
                {

#line 1459
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 1459
                        break;
                    }

#line 1460
                    cmulw_0(&re_8[k2_2], &im_8[k2_2], half(cr_0), half(ci_0));
                    float nr_0 = cr_0 * _S41 - ci_0 * _S42;
                    float _S43 = cr_0 * _S42 + ci_0 * _S41;

#line 1459
                    k2_2 = k2_2 + 1U;

#line 1459
                    cr_0 = nr_0;

#line 1459
                    ci_0 = _S43;

#line 1459
                }

#line 1467
                uint per_2 = 16U / max(256U, 1U);
                uint _S44 = max(16U, 1U);

#line 1468
                _S37 = _S44;
                uint blk2_2 = tid_2 / _S44;

#line 1469
                uint lane2_2 = tid_2 % _S44;

#line 1469
                exchangeS_0(&re_8, &im_8, lgLn_0, lgTB_0, 256U, 4096U, blk_2, lane_3, per_2, _S44, 256U, blk2_2, lane2_2, kernelContext_5);

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

                uint lgTB_1 = firstbithigh_0(16U);

                uint blk_3 = tid_2 >> lgTB_1;
                uint lane_4 = tid_2 & 15U;

                dft16s_0(&re_8, &im_8);

#line 1456
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_4) / 256.0f);
                float _S45 = tw_1.x;

#line 1457
                float _S46 = tw_1.y;

#line 1457
                k2_2 = 0U;

#line 1457
                cr_0 = 1.0f;

#line 1457
                ci_0 = 0.0f;

                for(;;)
                {

#line 1459
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 1459
                        break;
                    }

#line 1460
                    cmulw_0(&re_8[k2_2], &im_8[k2_2], half(cr_0), half(ci_0));
                    float nr_1 = cr_0 * _S45 - ci_0 * _S46;
                    float _S47 = cr_0 * _S46 + ci_0 * _S45;

#line 1459
                    k2_2 = k2_2 + 1U;

#line 1459
                    cr_0 = nr_1;

#line 1459
                    ci_0 = _S47;

#line 1459
                }

#line 1467
                uint per_3 = 16U / _S37;
                uint _S48 = max(1U, 1U);
                uint blk2_3 = tid_2 / _S48;

#line 1469
                uint lane2_3 = tid_2 % _S48;

#line 1469
                exchangeS_0(&re_8, &im_8, _S36, lgTB_1, 16U, 256U, blk_3, lane_4, per_3, _S48, 16U, blk2_3, lane2_3, kernelContext_5);

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
    innermostS_0(&re_8, &im_8);

#line 1496
    thread array<half2, int(16)> magv_1;



    half2 _S49 = half2(float2(0.0f) );
    half2 _S50 = half2(float2(0.015625f) );

#line 1501
    uint i_7 = 0U;

#line 1501
    half2 en_0 = _S49;
    for(;;)
    {

#line 1502
        if(i_7 < 16U)
        {
        }
        else
        {

#line 1502
            break;
        }

#line 1503
        uint idx_0 = slotToIndex_0(tid_2 * 16U + i_7);

#line 1503
        bool live_0;
        if(idx_0 >= winStart_3)
        {

#line 1504
            live_0 = idx_0 < winEnd_3;

#line 1504
        }
        else
        {

#line 1504
            live_0 = false;

#line 1504
        }
        half2 mg_0 = mag2s_0(re_8[i_7], im_8[i_7]);
        half2 sr_0 = re_8[i_7] * _S50;

#line 1506
        half2 si_0 = im_8[i_7] * _S50;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1507
        half2 _S51;
        if(live_0)
        {

#line 1508
            _S51 = mg_0;

#line 1508
        }
        else
        {

#line 1508
            _S51 = _S49;

#line 1508
        }

#line 1508
        magv_1[i_7] = _S51;

#line 1514
        if(live_0)
        {
            uint ov_0 = ((((uint(as_type<ushort>(re_8[i_7][0U])) & 65535U) | (uint(as_type<ushort>(re_8[i_7][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(im_8[i_7][0U])) & 65535U) | (uint(as_type<ushort>(im_8[i_7][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1516
            uint _S52 = (uint(as_type<ushort>(magv_1[i_7][0U])) & 65535U) | (uint(as_type<ushort>(magv_1[i_7][1U])) << 16U);

#line 1516
            uint mb_0;

            if((ov_0 & 32768U) != 0U)
            {

#line 1518
                mb_0 = (_S52 & 4294901760U) | 31744U;

#line 1518
            }
            else
            {

#line 1518
                mb_0 = _S52;

#line 1518
            }

#line 1518
            uint mb_1;
            if((ov_0 & 2147483648U) != 0U)
            {

#line 1519
                mb_1 = (mb_0 & 65535U) | 2080374784U;

#line 1519
            }
            else
            {

#line 1519
                mb_1 = mb_0;

#line 1519
            }
            magv_1[i_7] = half2(as_type<half>(ushort(mb_1 & 65535U)), as_type<half>(ushort((mb_1 >> 16U) & 65535U)));

#line 1514
        }

#line 1502
        i_7 = i_7 + 1U;

#line 1502
        en_0 = en_1;

#line 1502
    }

#line 1523
    float eB_0 = float(en_0.y) * 4096.0f;

#line 1523
    float _S53 = pairSum_0(tid_2, float(en_0.x) * 4096.0f, kernelContext_5);
    float eA_0 = _S53 / 4096.0f;

#line 1524
    float _S54 = pairSum_0(tid_2, eB_0, kernelContext_5);
    float eB_1 = _S54 / 4096.0f;

#line 1525
    thread array<half2, int(16)> _S55 = magv_1;

#line 1525
    thread array<half2, int(16)> _S56 = re_8;

#line 1525
    thread array<half2, int(16)> _S57 = im_8;

#line 1525
    peakLane_0(pairA_0, tid_2, 0U, &_S55, &_S56, &_S57, peakIdx_1, peakVal_1, winStart_3, winEnd_3, thrBits_2, eA_0, kernelContext_5);

#line 1525
    thread array<half2, int(16)> _S58 = magv_1;

#line 1525
    thread array<half2, int(16)> _S59 = re_8;

#line 1525
    thread array<half2, int(16)> _S60 = im_8;

#line 1525
    peakLane_0(pairB_0, tid_2, 1U, &_S58, &_S59, &_S60, peakIdx_1, peakVal_1, winStart_3, winEnd_3, thrBits_2, eB_1, kernelContext_5);



    return;
}


void filterPair_0(uint pair_1, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_2, packed_float2 device* peakVal_2, uint ntmpl_1, uint winStart_4, uint winEnd_4, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, KernelContext_0 thread* kernelContext_6)
{

#line 1533
    thread uint _S61 = winStart_4;

#line 1533
    thread uint _S62 = winEnd_4;

#line 1539
    kernelContext_6->_tid_0 = tid_3;

#line 1559
    uint tiles_0 = (ntmpl_1 + 8U - 1U) / 8U;
    uint slots_0 = binsize_1 * tiles_0;
    bool slotOk_0 = pair_1 < slots_0;

#line 1561
    uint q_1;
    if(slotOk_0)
    {

#line 1562
        q_1 = pair_1;

#line 1562
    }
    else
    {

#line 1562
        q_1 = slots_0 - 1U;

#line 1562
    }
    uint d_5 = q_1 / tiles_0;

#line 1563
    uint t0_0 = (q_1 - d_5 * tiles_0) * 8U;
    uint _S63 = d_5 * ntmpl_1 + t0_0;
    rowWindow_0(d_5, &_S61, &_S62);

#line 1576
    thread array<half2, int(16)> dreg_1;

#line 1576
    uint n2_1 = 0U;

    for(;;)
    {

#line 1578
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1578
            break;
        }

#line 1579
        dreg_1[n2_1] = dload_0(data_0, d_5 * 4096U + tid_3 + 256U * n2_1);

#line 1578
        n2_1 = n2_1 + 1U;

#line 1578
    }

#line 1578
    uint k_1 = 0U;

#line 1586
    for(;;)
    {

#line 1586
        if(k_1 < 8U)
        {
        }
        else
        {

#line 1586
            break;
        }

#line 1586
        bool okA_0;
        if(slotOk_0)
        {

#line 1587
            okA_0 = (t0_0 + k_1) < ntmpl_1;

#line 1587
        }
        else
        {

#line 1587
            okA_0 = false;

#line 1587
        }

#line 1587
        bool okB_0;

#line 1587
        if(slotOk_0)
        {

#line 1587
            okB_0 = (t0_0 + k_1 + 1U) < ntmpl_1;

#line 1587
        }
        else
        {

#line 1587
            okB_0 = false;

#line 1587
        }
        if(okA_0)
        {

#line 1588
            q_1 = _S63 + k_1;

#line 1588
        }
        else
        {

#line 1588
            q_1 = 4294967295U;

#line 1588
        }

#line 1588
        if(okB_0)
        {

#line 1588
            n2_1 = _S63 + k_1 + 1U;

#line 1588
        }
        else
        {

#line 1588
            n2_1 = 4294967295U;

#line 1588
        }
        uint _S64 = t0_0 + k_1;

#line 1589
        uint _S65 = ntmpl_1 - 1U;

#line 1589
        uint _S66 = min(_S64, _S65);

#line 1589
        uint _S67 = min(_S64 + 1U, _S65);

#line 1589
        thread array<half2, int(16)> _S68 = dreg_1;

#line 1589
        filterTwo_0(q_1, n2_1, _S66, _S67, tid_3, &_S68, tmpl_1, peakIdx_2, peakVal_2, _S61, _S62, thrBits_3, kernelContext_6);

#line 1586
        k_1 = k_1 + 2U;

#line 1586
    }

#line 1602
    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1606
    thread KernelContext_0 kernelContext_7;

#line 1606
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1606
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1606
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1606
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1606
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1606
    threadgroup array<uint, int(4096)> stg_1;

#line 1606
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1623
    uint _pr_0 = gid_0.x;

#line 1623
    uint _t_0 = lid_0.x;
    (&kernelContext_7)->_stgBase_0 = 0U;

#line 1624
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);

#line 1632
    return;
}
