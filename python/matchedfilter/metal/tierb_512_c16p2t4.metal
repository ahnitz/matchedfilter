#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
#ifndef MF_C16_RAW
#define MF_C16_RAW 0u
#endif

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


#line 197 "mm_512_fusedTierB_c16p2t4.slang"
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


    cmulw_0(&(*re_2)[int(5)], &(*im_2)[int(5)], 0.923828125, 0.382568359375);
    cmulw_0(&(*re_2)[int(9)], &(*im_2)[int(9)], 0.70703125, 0.70703125);
    cmulw_0(&(*re_2)[int(13)], &(*im_2)[int(13)], 0.382568359375, 0.923828125);
    cmulw_0(&(*re_2)[int(6)], &(*im_2)[int(6)], 0.70703125, 0.70703125);
    cmulw_0(&(*re_2)[int(10)], &(*im_2)[int(10)], 0.0, 1.0);
    cmulw_0(&(*re_2)[int(14)], &(*im_2)[int(14)], -0.70703125, 0.70703125);
    cmulw_0(&(*re_2)[int(7)], &(*im_2)[int(7)], 0.382568359375, 0.923828125);
    cmulw_0(&(*re_2)[int(11)], &(*im_2)[int(11)], -0.70703125, 0.70703125);
    cmulw_0(&(*re_2)[int(15)], &(*im_2)[int(15)], -0.923828125, -0.382568359375);

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


#line 64 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 270 "mm_512_fusedTierB_c16p2t4.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S5 = max(TB_0, 1U);

#line 272
    uint j_0 = d_2 / _S5;

#line 272
    uint m_0 = d_2 % _S5;

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
        _S6 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

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


#line 246 "mm_512_fusedTierB_c16p2t4.slang"
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
    uint _S7;
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
void exchangeS_0(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
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
        half2 _S8 = half2(float2(0.0) );

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
    uint _S10 = (_S9 >> lgSpan_0) * 32U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S9 & spanMask_0);

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
                        uint _S11 = j_1 * 32U + kernelContext_2->_tid_0;

#line 447
                        stgPut_0(_S11, (*re_3)[c_1 * 16U + j_1], kernelContext_2);

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
                        uint az_0 = (_S12 >> lgSpan_0) * 32U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S12 & spanMask_0);

#line 453
                        half2 _S13 = stgGet_0(_S10 + az_0 - c_1 * 16U * 32U, kernelContext_2);



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
                        uint _S14 = j_2 * 32U + kernelContext_2->_tid_0;

#line 447
                        stgPut_0(_S14, (*im_3)[c_1 * 16U + j_2], kernelContext_2);

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
                        uint az_1 = (_S15 >> lgSpan_0) * 32U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 453
                        half2 _S16 = stgGet_0(_S10 + az_1 - c_1 * 16U * 32U, kernelContext_2);



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
        (*re_3)[j_1] = outr_0[j_1];

#line 462
        (*im_3)[j_1] = outi_0[j_1];

#line 462
        j_1 = j_1 + 1U;

#line 462
    }
    return;
}


#line 363
void dft2s_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4, uint o_0)
{
    half2 ar_1 = (*re_4)[o_0];

#line 365
    half2 ai_1 = (*im_4)[o_0];

#line 365
    uint _S17 = o_0 + 1U;

#line 365
    half2 br_1 = (*re_4)[_S17];

#line 365
    half2 bi_1 = (*im_4)[_S17];
    (*re_4)[o_0] = (*re_4)[o_0] + (*re_4)[_S17];

#line 366
    (*im_4)[o_0] = ai_1 + bi_1;
    (*re_4)[_S17] = ar_1 - br_1;

#line 367
    (*im_4)[_S17] = ai_1 - bi_1;
    return;
}


#line 465
void innermostS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5)
{

#line 465
    uint b_3 = 0U;

#line 470
    for(;;)
    {

#line 470
        if(b_3 < 8U)
        {
        }
        else
        {

#line 470
            break;
        }

#line 470
        dft2s_0(re_5, im_5, b_3 * 2U);

#line 470
        b_3 = b_3 + 1U;

#line 470
    }
    return;
}


#line 729
uint lgOf_0(uint i_4)
{

#line 729
    uint _S18;

#line 729
    if(i_4 < 2U)
    {

#line 729
        _S18 = 4U;

#line 729
    }
    else
    {

#line 729
        _S18 = 1U;

#line 729
    }

#line 729
    return _S18;
}


#line 731
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 735
    uint lg_1 = lgOf_0(1U);

#line 735
    uint lg_2 = lgOf_0(0U);

#line 740
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 418
half2 mag2s_0(half2 re_6, half2 im_6)
{

#line 418
    return re_6 * re_6 + im_6 * im_6;
}


#line 1215
uint mfShflXor_0(uint v_1, uint s_0, KernelContext_0 thread* kernelContext_3)
{

#line 1215
    uint _S19 = (simd_shuffle((v_1), ushort((int((kernelContext_3->_S7) ^ s_0)))));

#line 1215
    return _S19;
}


#line 47 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S20 = ((MF_C16_RAW));

#line 50
    return _S20;
}


#line 1337 "mm_512_fusedTierB_c16p2t4.slang"
void peakTwoGate_0(uint pairA_0, uint pairB_0, uint tid_0, const array<half2, int(16)> thread* re_7, const array<half2, int(16)> thread* im_7, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, float thr_0, KernelContext_0 thread* kernelContext_4)
{


    uint _S21 = slotToIndex_0(tid_0 * 16U) - winStart_2;
    uint _S22 = winEnd_2 - winStart_2;
    half2 _S23 = half2(float2(0.0) );
    half2 _S24 = half2(float2(0.015625) );

#line 1344
    uint i_5 = 0U;

#line 1344
    half2 best_0 = _S23;

#line 1344
    half2 en_0 = _S23;
    for(;;)
    {

#line 1345
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1345
            break;
        }

#line 1345
        half2 _S25;

        if((_S21 + slotToIndex_0(i_5)) < _S22)
        {

#line 1347
            _S25 = mag2s_0((*re_7)[i_5], (*im_7)[i_5]);

#line 1347
        }
        else
        {

#line 1347
            _S25 = _S23;

#line 1347
        }

#line 1347
        half2 _S26 = max(best_0, _S25);
        half2 sr_0 = (*re_7)[i_5] * _S24;

#line 1348
        half2 si_0 = (*im_7)[i_5] * _S24;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1345
        i_5 = i_5 + 1U;

#line 1345
        best_0 = _S26;

#line 1345
        en_0 = en_1;

#line 1345
    }

#line 1345
    uint _S27 = mfShflXor_0((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U), 1U, kernelContext_4);

#line 1352
    half2 _S28 = max(best_0, half2(as_type<half>(ushort(_S27 & 65535U)), as_type<half>(ushort((_S27 >> 16U) & 65535U))));

#line 1352
    uint _S29 = mfShflXor_0((uint(as_type<ushort>(en_0[0U])) & 65535U) | (uint(as_type<ushort>(en_0[1U])) << 16U), 1U, kernelContext_4);
    half2 en_2 = en_0 + half2(as_type<half>(ushort(_S29 & 65535U)), as_type<half>(ushort((_S29 >> 16U) & 65535U)));

#line 1353
    uint _S30 = mfShflXor_0((uint(as_type<ushort>(_S28[0U])) & 65535U) | (uint(as_type<ushort>(_S28[1U])) << 16U), 2U, kernelContext_4);

#line 1352
    half2 _S31 = max(_S28, half2(as_type<half>(ushort(_S30 & 65535U)), as_type<half>(ushort((_S30 >> 16U) & 65535U))));

#line 1352
    uint _S32 = mfShflXor_0((uint(as_type<ushort>(en_2[0U])) & 65535U) | (uint(as_type<ushort>(en_2[1U])) << 16U), 2U, kernelContext_4);
    half2 en_3 = en_2 + half2(as_type<half>(ushort(_S32 & 65535U)), as_type<half>(ushort((_S32 >> 16U) & 65535U)));

#line 1353
    uint _S33 = mfShflXor_0((uint(as_type<ushort>(_S31[0U])) & 65535U) | (uint(as_type<ushort>(_S31[1U])) << 16U), 4U, kernelContext_4);

#line 1352
    half2 _S34 = max(_S31, half2(as_type<half>(ushort(_S33 & 65535U)), as_type<half>(ushort((_S33 >> 16U) & 65535U))));

#line 1352
    uint _S35 = mfShflXor_0((uint(as_type<ushort>(en_3[0U])) & 65535U) | (uint(as_type<ushort>(en_3[1U])) << 16U), 4U, kernelContext_4);
    half2 en_4 = en_3 + half2(as_type<half>(ushort(_S35 & 65535U)), as_type<half>(ushort((_S35 >> 16U) & 65535U)));

#line 1353
    uint _S36 = mfShflXor_0((uint(as_type<ushort>(_S34[0U])) & 65535U) | (uint(as_type<ushort>(_S34[1U])) << 16U), 8U, kernelContext_4);

#line 1352
    half2 _S37 = max(_S34, half2(as_type<half>(ushort(_S36 & 65535U)), as_type<half>(ushort((_S36 >> 16U) & 65535U))));

#line 1352
    uint _S38 = mfShflXor_0((uint(as_type<ushort>(en_4[0U])) & 65535U) | (uint(as_type<ushort>(en_4[1U])) << 16U), 8U, kernelContext_4);
    half2 en_5 = en_4 + half2(as_type<half>(ushort(_S38 & 65535U)), as_type<half>(ushort((_S38 >> 16U) & 65535U)));

#line 1353
    uint _S39 = mfShflXor_0((uint(as_type<ushort>(_S37[0U])) & 65535U) | (uint(as_type<ushort>(_S37[1U])) << 16U), 16U, kernelContext_4);

#line 1352
    half2 best_1 = max(_S37, half2(as_type<half>(ushort(_S39 & 65535U)), as_type<half>(ushort((_S39 >> 16U) & 65535U))));

#line 1352
    uint _S40 = mfShflXor_0((uint(as_type<ushort>(en_5[0U])) & 65535U) | (uint(as_type<ushort>(en_5[1U])) << 16U), 16U, kernelContext_4);
    half2 en_6 = en_5 + half2(as_type<half>(ushort(_S40 & 65535U)), as_type<half>(ushort((_S40 >> 16U) & 65535U)));

#line 1353
    uint _S41 = (uint(as_type<ushort>(en_6[0U])) & 65535U) | (uint(as_type<ushort>(en_6[1U])) << 16U);

#line 1353
    uint _S42 = (uint(as_type<ushort>(best_1[0U])) & 65535U) | (uint(as_type<ushort>(best_1[1U])) << 16U);

#line 1353
    bool infA_0;

#line 1361
    if((_S41 & 31744U) == 31744U)
    {

#line 1361
        infA_0 = true;

#line 1361
    }
    else
    {

#line 1361
        infA_0 = (_S42 & 31744U) == 31744U;

#line 1361
    }

#line 1361
    bool infB_0;
    if((_S41 & 2080374784U) == 2080374784U)
    {

#line 1362
        infB_0 = true;

#line 1362
    }
    else
    {

#line 1362
        infB_0 = (_S42 & 2080374784U) == 2080374784U;

#line 1362
    }

#line 52 "twiddle.slang"
    uint _S43 = mfC16RawFlag_0();

#line 52
    float _S44;

#line 1365 "mm_512_fusedTierB_c16p2t4.slang"
    if((1U - _S43) != 0U)
    {

#line 1365
        _S44 = 14.069000244140625;

#line 1365
    }
    else
    {

#line 1365
        _S44 = 0.0;

#line 1365
    }

#line 1365
    float k2_1 = _S44 * 0.00048828125 * 1.00010001659393311;
    float mA_0 = sqrt(float(best_1.x));

#line 1366
    float mB_0 = sqrt(float(best_1.y));

    float bA_0 = mA_0 * 1.00107669830322266 + k2_1 * sqrt(float(en_6.x) * 8.0);
    float bB_0 = mB_0 * 1.00107669830322266 + k2_1 * sqrt(float(en_6.y) * 8.0);

#line 1369
    bool hitA_0;
    if(infA_0)
    {

#line 1370
        hitA_0 = true;

#line 1370
    }
    else
    {

#line 1370
        if(mA_0 > 0.0)
        {

#line 1370
            hitA_0 = bA_0 >= thr_0;

#line 1370
        }
        else
        {

#line 1370
            hitA_0 = false;

#line 1370
        }

#line 1370
    }

#line 1370
    bool hitB_0;
    if(infB_0)
    {

#line 1371
        hitB_0 = true;

#line 1371
    }
    else
    {

#line 1371
        if(mB_0 > 0.0)
        {

#line 1371
            hitB_0 = bB_0 >= thr_0;

#line 1371
        }
        else
        {

#line 1371
            hitB_0 = false;

#line 1371
        }

#line 1371
    }
    bool _S45 = tid_0 == 0U;

#line 1372
    bool _S46;

#line 1372
    if(_S45)
    {

#line 1372
        _S46 = pairA_0 != 4294967295U;

#line 1372
    }
    else
    {

#line 1372
        _S46 = false;

#line 1372
    }

#line 1372
    int _S47;

#line 1372
    float2 _S48;

#line 1372
    if(_S46)
    {

#line 1373
        int device* _S49 = peakIdx_0+pairA_0;

#line 1373
        if(hitA_0)
        {

#line 1373
            _S47 = int(0);

#line 1373
        }
        else
        {

#line 1373
            _S47 = int(-1);

#line 1373
        }

#line 1373
        *_S49 = _S47;

#line 1373
        packed_float2 device* _S50 = peakVal_0+pairA_0;
        if(infA_0)
        {

#line 1374
            _S48 = float2(3.40282306073709653e+38, 0.0);

#line 1374
        }
        else
        {

#line 1374
            if(hitA_0)
            {

#line 1374
                _S48 = float2(bA_0, 0.0);

#line 1374
            }
            else
            {

#line 1374
                _S48 = float2(0.0, 0.0);

#line 1374
            }

#line 1374
        }

#line 1374
        *_S50 = packed_float2(_S48) ;

#line 1372
    }



    if(_S45)
    {

#line 1376
        infA_0 = pairB_0 != 4294967295U;

#line 1376
    }
    else
    {

#line 1376
        infA_0 = false;

#line 1376
    }

#line 1376
    if(infA_0)
    {

#line 1377
        int device* _S51 = peakIdx_0+pairB_0;

#line 1377
        if(hitB_0)
        {

#line 1377
            _S47 = int(0);

#line 1377
        }
        else
        {

#line 1377
            _S47 = int(-1);

#line 1377
        }

#line 1377
        *_S51 = _S47;

#line 1377
        packed_float2 device* _S52 = peakVal_0+pairB_0;
        if(infB_0)
        {

#line 1378
            _S48 = float2(3.40282306073709653e+38, 0.0);

#line 1378
        }
        else
        {

#line 1378
            if(hitB_0)
            {

#line 1378
                _S48 = float2(bB_0, 0.0);

#line 1378
            }
            else
            {

#line 1378
                _S48 = float2(0.0, 0.0);

#line 1378
            }

#line 1378
        }

#line 1378
        *_S52 = packed_float2(_S48) ;

#line 1376
    }



    return;
}


#line 299
float2 c16Bound_0(float2 v_2, float energy_0)
{

#line 52 "twiddle.slang"
    uint _S53 = mfC16RawFlag_0();

#line 301 "mm_512_fusedTierB_c16p2t4.slang"
    if((1U - _S53) == 0U)
    {

#line 301
        return v_2;
    }

#line 302
    float m_1 = length(v_2);
    float b_4 = m_1 * 1.00146484375 + 0.00686962902545929 * sqrt(energy_0);

#line 303
    float2 _S54;
    if(m_1 > 0.0)
    {

#line 304
        _S54 = v_2 * float2((b_4 / m_1)) ;

#line 304
    }
    else
    {

#line 304
        _S54 = float2(b_4, 0.0);

#line 304
    }

#line 304
    return _S54;
}


#line 1218
void peakTwoWave_0(uint pairA_1, uint pairB_1, uint tid_1, const array<half2, int(16)> thread* re_8, const array<half2, int(16)> thread* im_8, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{
    uint m_2;

#line 1220
    bool _S55;

#line 1220
    bool _S56;

    uint _S57 = slotToIndex_0(tid_1 * 16U) - winStart_3;
    uint _S58 = winEnd_3 - winStart_3;

#line 1230
    half2 _S59 = half2(float2(0.0) );
    half2 _S60 = half2(float2(0.015625) );

#line 1231
    uint i_6 = 0U;

#line 1231
    half2 en_7 = _S59;

#line 1231
    uint ovAcc_0 = 0U;

#line 1231
    uint kA_0 = 0U;

#line 1231
    uint kB_0 = 0U;



    for(;;)
    {

#line 1235
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1235
            break;
        }
        half2 mg_0 = mag2s_0((*re_8)[i_6], (*im_8)[i_6]);
        half2 sr_1 = (*re_8)[i_6] * _S60;

#line 1238
        half2 si_1 = (*im_8)[i_6] * _S60;
        half2 en_8 = en_7 + (sr_1 * sr_1 + si_1 * si_1);
        if((_S57 + slotToIndex_0(i_6)) < _S58)
        {

#line 1240
            m_2 = (uint(as_type<ushort>(mg_0[0U])) & 65535U) | (uint(as_type<ushort>(mg_0[1U])) << 16U);

#line 1240
        }
        else
        {

#line 1240
            m_2 = 0U;

#line 1240
        }

#line 1246
        uint ovAcc_1 = ovAcc_0 | (((((uint(as_type<ushort>((*re_8)[i_6].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[i_6].y)) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>((*im_8)[i_6].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[i_6].y)) << 16U)) & 2080406528U) + 67109888U));


        uint _S61 = 15U - i_6;

#line 1249
        uint _S62 = max(kA_0, (m_2 << 16U) | _S61);
        uint _S63 = max(kB_0, (m_2 & 4294901760U) | _S61);

#line 1235
        i_6 = i_6 + 1U;

#line 1235
        en_7 = en_8;

#line 1235
        ovAcc_0 = ovAcc_1;

#line 1235
        kA_0 = _S62;

#line 1235
        kB_0 = _S63;

#line 1235
    }

#line 1254
    if((ovAcc_0 & 32768U) != 0U)
    {

#line 1254
        kA_0 = max(kA_0, 2080374799U);

#line 1254
    }
    if((ovAcc_0 & 2147483648U) != 0U)
    {

#line 1255
        kB_0 = max(kB_0, 2080374799U);

#line 1255
    }


    uint _S64 = (4095U - tid_1) << 4U;

#line 1258
    uint kA_1 = kA_0 | _S64;
    uint kB_1 = kB_0 | _S64;

#line 1259
    uint _S65 = mfShflXor_0(kA_1, 1U, kernelContext_5);

    uint _S66 = max(kA_1, _S65);

#line 1261
    uint _S67 = mfShflXor_0(kB_1, 1U, kernelContext_5);
    uint _S68 = max(kB_1, _S67);

#line 1262
    uint _S69 = mfShflXor_0((uint(as_type<ushort>(en_7[0U])) & 65535U) | (uint(as_type<ushort>(en_7[1U])) << 16U), 1U, kernelContext_5);
    half2 en_9 = en_7 + half2(as_type<half>(ushort(_S69 & 65535U)), as_type<half>(ushort((_S69 >> 16U) & 65535U)));

#line 1263
    uint _S70 = mfShflXor_0(_S66, 2U, kernelContext_5);

#line 1261
    uint _S71 = max(_S66, _S70);

#line 1261
    uint _S72 = mfShflXor_0(_S68, 2U, kernelContext_5);
    uint _S73 = max(_S68, _S72);

#line 1262
    uint _S74 = mfShflXor_0((uint(as_type<ushort>(en_9[0U])) & 65535U) | (uint(as_type<ushort>(en_9[1U])) << 16U), 2U, kernelContext_5);
    half2 en_10 = en_9 + half2(as_type<half>(ushort(_S74 & 65535U)), as_type<half>(ushort((_S74 >> 16U) & 65535U)));

#line 1263
    uint _S75 = mfShflXor_0(_S71, 4U, kernelContext_5);

#line 1261
    uint _S76 = max(_S71, _S75);

#line 1261
    uint _S77 = mfShflXor_0(_S73, 4U, kernelContext_5);
    uint _S78 = max(_S73, _S77);

#line 1262
    uint _S79 = mfShflXor_0((uint(as_type<ushort>(en_10[0U])) & 65535U) | (uint(as_type<ushort>(en_10[1U])) << 16U), 4U, kernelContext_5);
    half2 en_11 = en_10 + half2(as_type<half>(ushort(_S79 & 65535U)), as_type<half>(ushort((_S79 >> 16U) & 65535U)));

#line 1263
    uint _S80 = mfShflXor_0(_S76, 8U, kernelContext_5);

#line 1261
    uint _S81 = max(_S76, _S80);

#line 1261
    uint _S82 = mfShflXor_0(_S78, 8U, kernelContext_5);
    uint _S83 = max(_S78, _S82);

#line 1262
    uint _S84 = mfShflXor_0((uint(as_type<ushort>(en_11[0U])) & 65535U) | (uint(as_type<ushort>(en_11[1U])) << 16U), 8U, kernelContext_5);
    half2 en_12 = en_11 + half2(as_type<half>(ushort(_S84 & 65535U)), as_type<half>(ushort((_S84 >> 16U) & 65535U)));

#line 1263
    uint _S85 = mfShflXor_0(_S81, 16U, kernelContext_5);

#line 1261
    uint _S86 = max(_S81, _S85);

#line 1261
    uint _S87 = mfShflXor_0(_S83, 16U, kernelContext_5);
    uint _S88 = max(_S83, _S87);

#line 1262
    uint _S89 = mfShflXor_0((uint(as_type<ushort>(en_12[0U])) & 65535U) | (uint(as_type<ushort>(en_12[1U])) << 16U), 16U, kernelContext_5);
    half2 en_13 = en_12 + half2(as_type<half>(ushort(_S89 & 65535U)), as_type<half>(ushort((_S89 >> 16U) & 65535U)));



    float enA_0 = float(en_13.x) * 8.0;

#line 1267
    float enB_0 = float(en_13.y) * 8.0;
    uint slotA_0 = 65535U - (_S86 & 65535U);

#line 1268
    uint slotB_0 = 65535U - (_S88 & 65535U);

#line 1274
    uint _S90 = _S86 >> 16U;

#line 1274
    bool infA_1 = _S90 >= 31744U;

#line 1274
    uint _S91 = _S88 >> 16U;

#line 1274
    bool infB_1 = _S91 >= 31744U;

#line 1274
    bool hitA_1;



    if(infA_1)
    {

#line 1278
        hitA_1 = true;

#line 1278
    }
    else
    {

#line 1278
        hitA_1 = (as_type<half>((ushort)((_S90)))) > (as_type<float>((thrBits_1)));

#line 1278
    }

#line 1278
    bool hitB_1;
    if(infB_1)
    {

#line 1279
        hitB_1 = true;

#line 1279
    }
    else
    {

#line 1279
        hitB_1 = (as_type<half>((ushort)((_S91)))) > (as_type<float>((thrBits_1)));

#line 1279
    }

#line 1287
    uint _S92 = slotA_0 >> 4U;

#line 1287
    uint _S93 = slotA_0 & 15U;

#line 1287
    uint _S94 = slotB_0 >> 4U;

#line 1287
    uint _S95 = slotB_0 & 15U;
    thread array<float, int(2)> vA_0;

#line 1288
    thread array<float, int(2)> vB_0;
    vB_0[int(1)] = 0.0;

#line 1289
    vB_0[int(0)] = 0.0;

#line 1289
    vA_0[int(1)] = 0.0;

#line 1289
    vA_0[int(0)] = 0.0;

#line 1289
    for(;;)
    {

#line 1289
        for(;;)
        {

#line 1290
            for(;;)
            {

#line 1290
                for(;;)
                {

#line 1290
                    for(;;)
                    {

#line 1291
                        for(;;)
                        {

#line 1292
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1292
                            m_2 = 0U;
                            for(;;)
                            {

#line 1293
                                if(m_2 < 16U)
                                {
                                }
                                else
                                {

#line 1293
                                    break;
                                }

#line 1294
                                (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + m_2 * 32U + tid_1] = (uint(as_type<ushort>((*re_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[m_2].y)) << 16U);

#line 1293
                                m_2 = m_2 + 1U;

#line 1293
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            bool _S96 = tid_1 == 0U;

#line 1296
                            _S55 = _S96;

#line 1296
                            if(_S96)
                            {

#line 1297
                                if(_S93 >= 0U)
                                {

#line 1297
                                    _S56 = _S93 < 16U;

#line 1297
                                }
                                else
                                {

#line 1297
                                    _S56 = false;

#line 1297
                                }

#line 1297
                                if(_S56)
                                {

#line 1298
                                    vA_0[0U] = (as_type<half>((ushort)(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S93 * 32U + _S92]))));

#line 1297
                                }

                                if(_S95 >= 0U)
                                {

#line 1299
                                    _S56 = _S95 < 16U;

#line 1299
                                }
                                else
                                {

#line 1299
                                    _S56 = false;

#line 1299
                                }

#line 1299
                                if(_S56)
                                {

#line 1300
                                    vB_0[0U] = (as_type<half>((ushort)((((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S95 * 32U + _S94]) >> 16U))));

#line 1299
                                }

#line 1296
                            }

#line 1291
                            break;
                        }

#line 1291
                        break;
                    }

#line 1291
                    break;
                }

#line 1290
                break;
            }

#line 1290
            break;
        }

#line 1290
        for(;;)
        {

#line 1290
            for(;;)
            {

#line 1290
                for(;;)
                {

#line 1290
                    for(;;)
                    {

#line 1291
                        for(;;)
                        {

#line 1292
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1292
                            m_2 = 0U;
                            for(;;)
                            {

#line 1293
                                if(m_2 < 16U)
                                {
                                }
                                else
                                {

#line 1293
                                    break;
                                }

#line 1294
                                (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + m_2 * 32U + tid_1] = (uint(as_type<ushort>((*im_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[m_2].y)) << 16U);

#line 1293
                                m_2 = m_2 + 1U;

#line 1293
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            if(_S55)
                            {

#line 1297
                                if(_S93 >= 0U)
                                {

#line 1297
                                    _S56 = _S93 < 16U;

#line 1297
                                }
                                else
                                {

#line 1297
                                    _S56 = false;

#line 1297
                                }

#line 1297
                                if(_S56)
                                {

#line 1298
                                    vA_0[1U] = (as_type<half>((ushort)(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S93 * 32U + _S92]))));

#line 1297
                                }

                                if(_S95 >= 0U)
                                {

#line 1299
                                    _S56 = _S95 < 16U;

#line 1299
                                }
                                else
                                {

#line 1299
                                    _S56 = false;

#line 1299
                                }

#line 1299
                                if(_S56)
                                {

#line 1300
                                    vB_0[1U] = (as_type<half>((ushort)((((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S95 * 32U + _S94]) >> 16U))));

#line 1299
                                }

#line 1296
                            }

#line 1291
                            break;
                        }

#line 1291
                        break;
                    }

#line 1291
                    break;
                }

#line 1290
                break;
            }

#line 1290
            break;
        }

#line 1290
        break;
    }

#line 1304
    if(_S55)
    {

#line 1304
        _S56 = pairA_1 != 4294967295U;

#line 1304
    }
    else
    {

#line 1304
        _S56 = false;

#line 1304
    }

#line 1304
    int _S97;

#line 1304
    float2 _S98;

#line 1304
    if(_S56)
    {

#line 1305
        int device* _S99 = peakIdx_1+pairA_1;

#line 1305
        if(hitA_1)
        {

#line 1305
            _S97 = int(slotToIndex_0(slotA_0));

#line 1305
        }
        else
        {

#line 1305
            _S97 = int(-1);

#line 1305
        }

#line 1305
        *_S99 = _S97;

#line 1305
        packed_float2 device* _S100 = peakVal_1+pairA_1;
        if(infA_1)
        {

#line 1306
            _S98 = float2(3.40282306073709653e+38, 0.0);

#line 1306
        }
        else
        {

#line 1307
            if(hitA_1)
            {

#line 1307
                float2 _S101 = c16Bound_0(float2(vA_0[int(0)], vA_0[int(1)]), enA_0);

#line 1307
                _S98 = _S101;

#line 1307
            }
            else
            {

#line 1307
                _S98 = float2(0.0, 0.0);

#line 1307
            }

#line 1306
        }

#line 1306
        *_S100 = packed_float2(_S98) ;

#line 1304
    }

#line 1309
    if(_S55)
    {

#line 1309
        hitA_1 = pairB_1 != 4294967295U;

#line 1309
    }
    else
    {

#line 1309
        hitA_1 = false;

#line 1309
    }

#line 1309
    if(hitA_1)
    {

#line 1310
        int device* _S102 = peakIdx_1+pairB_1;

#line 1310
        if(hitB_1)
        {

#line 1310
            _S97 = int(slotToIndex_0(slotB_0));

#line 1310
        }
        else
        {

#line 1310
            _S97 = int(-1);

#line 1310
        }

#line 1310
        *_S102 = _S97;

#line 1310
        packed_float2 device* _S103 = peakVal_1+pairB_1;
        if(infB_1)
        {

#line 1311
            _S98 = float2(3.40282306073709653e+38, 0.0);

#line 1311
        }
        else
        {

#line 1312
            if(hitB_1)
            {

#line 1312
                float2 _S104 = c16Bound_0(float2(vB_0[int(0)], vB_0[int(1)]), enB_0);

#line 1312
                _S98 = _S104;

#line 1312
            }
            else
            {

#line 1312
                _S98 = float2(0.0, 0.0);

#line 1312
            }

#line 1311
        }

#line 1311
        *_S103 = packed_float2(_S98) ;

#line 1309
    }

#line 1314
    return;
}


#line 1387
void filterTwo_0(uint pairA_2, uint pairB_2, uint tA_0, uint tB_0, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* tmpl_0, int device* peakIdx_2, packed_float2 device* peakVal_2, uint winStart_4, uint winEnd_4, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{

    uint _S105;

#line 1390
    uint k2_2;

#line 1390
    float cr_0;

#line 1390
    float ci_0;

#line 1390
    uint _S106;

    thread array<half2, int(16)> re_9;

#line 1392
    thread array<half2, int(16)> im_9;

#line 1392
    uint n2_0 = 0U;
    for(;;)
    {

#line 1393
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 1393
            break;
        }

#line 1394
        uint _S107 = 32U * n2_0;

#line 1394
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 512U + tid_2 + _S107);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 512U + tid_2 + _S107);
        half _S108 = (*dreg_0)[n2_0].x;
        half _S109 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S108, _S108), half2(_S109, _S109), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_9[n2_0], &im_9[n2_0]);

#line 1393
        n2_0 = n2_0 + 1U;

#line 1393
    }

#line 1393
    for(;;)
    {

#line 1393
        for(;;)
        {

#line 1403
            for(;;)
            {

                uint lgTB_0 = firstbithigh_0(32U);

#line 1406
                _S105 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(512U);
                uint blk_2 = tid_2 >> lgTB_0;
                uint lane_2 = tid_2 & 31U;

                dft16s_0(&re_9, &im_9);

#line 1427
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 512.0);
                float _S110 = tw_0.x;

#line 1428
                float _S111 = tw_0.y;

#line 1428
                k2_2 = 0U;

#line 1428
                cr_0 = 1.0;

#line 1428
                ci_0 = 0.0;

                for(;;)
                {

#line 1430
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 1430
                        break;
                    }

#line 1431
                    cmulw_0(&re_9[k2_2], &im_9[k2_2], half(cr_0), half(ci_0));
                    float nr_0 = cr_0 * _S110 - ci_0 * _S111;
                    float _S112 = cr_0 * _S111 + ci_0 * _S110;

#line 1430
                    k2_2 = k2_2 + 1U;

#line 1430
                    cr_0 = nr_0;

#line 1430
                    ci_0 = _S112;

#line 1430
                }

#line 1438
                uint per_2 = 16U / max(32U, 1U);
                uint _S113 = max(2U, 1U);

#line 1439
                _S106 = _S113;
                uint blk2_2 = tid_2 / _S113;

#line 1440
                uint lane2_2 = tid_2 % _S113;

#line 1440
                exchangeS_0(&re_9, &im_9, lgLn_0, lgTB_0, 32U, 512U, blk_2, lane_2, per_2, _S113, 32U, blk2_2, lane2_2, kernelContext_6);

#line 1403
                break;
            }

#line 1403
            break;
        }

#line 1403
        for(;;)
        {

#line 1403
            for(;;)
            {

                uint lgTB_1 = firstbithigh_0(2U);

                uint blk_3 = tid_2 >> lgTB_1;
                uint lane_3 = tid_2 & 1U;

                dft16s_0(&re_9, &im_9);

#line 1427
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 32.0);
                float _S114 = tw_1.x;

#line 1428
                float _S115 = tw_1.y;

#line 1428
                k2_2 = 0U;

#line 1428
                cr_0 = 1.0;

#line 1428
                ci_0 = 0.0;

                for(;;)
                {

#line 1430
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 1430
                        break;
                    }

#line 1431
                    cmulw_0(&re_9[k2_2], &im_9[k2_2], half(cr_0), half(ci_0));
                    float nr_1 = cr_0 * _S114 - ci_0 * _S115;
                    float _S116 = cr_0 * _S115 + ci_0 * _S114;

#line 1430
                    k2_2 = k2_2 + 1U;

#line 1430
                    cr_0 = nr_1;

#line 1430
                    ci_0 = _S116;

#line 1430
                }

#line 1438
                uint per_3 = 16U / _S106;
                uint _S117 = max(0U, 1U);
                uint blk2_3 = tid_2 / _S117;

#line 1440
                uint lane2_3 = tid_2 % _S117;

#line 1440
                exchangeS_0(&re_9, &im_9, _S105, lgTB_1, 2U, 32U, blk_3, lane_3, per_3, _S117, 2U, blk2_3, lane2_3, kernelContext_6);

#line 1403
                break;
            }

#line 1403
            break;
        }

#line 1403
        break;
    }

#line 1443
    innermostS_0(&re_9, &im_9);

#line 1461
    if(thrBits_2 != 0U)
    {

#line 1462
        float _S118 = (as_type<float>((thrBits_2)));

#line 1462
        thread array<half2, int(16)> _S119 = re_9;

#line 1462
        thread array<half2, int(16)> _S120 = im_9;

#line 1462
        peakTwoGate_0(pairA_2, pairB_2, tid_2, &_S119, &_S120, peakIdx_2, peakVal_2, winStart_4, winEnd_4, _S118, kernelContext_6);

#line 1461
    }
    else
    {

#line 1461
        thread array<half2, int(16)> _S121 = re_9;

#line 1461
        thread array<half2, int(16)> _S122 = im_9;

#line 1461
        peakTwoWave_0(pairA_2, pairB_2, tid_2, &_S121, &_S122, peakIdx_2, peakVal_2, winStart_4, winEnd_4, thrBits_2, kernelContext_6);

#line 1461
    }

#line 1494
    return;
}


void filterPair_0(uint pair_0, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_3, packed_float2 device* peakVal_3, uint ntmpl_1, uint winStart_5, uint winEnd_5, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, KernelContext_0 thread* kernelContext_7)
{

#line 1498
    thread uint _S123 = winStart_5;

#line 1498
    thread uint _S124 = winEnd_5;

#line 1504
    kernelContext_7->_tid_0 = tid_3;

#line 1524
    uint tiles_0 = (ntmpl_1 + 4U - 1U) / 4U;
    uint slots_0 = binsize_1 * tiles_0;
    bool slotOk_0 = pair_0 < slots_0;

#line 1526
    uint q_1;
    if(slotOk_0)
    {

#line 1527
        q_1 = pair_0;

#line 1527
    }
    else
    {

#line 1527
        q_1 = slots_0 - 1U;

#line 1527
    }
    uint d_5 = q_1 / tiles_0;

#line 1528
    uint t0_0 = (q_1 - d_5 * tiles_0) * 4U;
    uint _S125 = d_5 * ntmpl_1 + t0_0;
    rowWindow_0(d_5, &_S123, &_S124);

#line 1541
    thread array<half2, int(16)> dreg_1;

#line 1541
    uint n2_1 = 0U;

    for(;;)
    {

#line 1543
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1543
            break;
        }

#line 1544
        dreg_1[n2_1] = dload_0(data_0, d_5 * 512U + tid_3 + 32U * n2_1);

#line 1543
        n2_1 = n2_1 + 1U;

#line 1543
    }

#line 1543
    uint k_0 = 0U;

#line 1551
    for(;;)
    {

#line 1551
        if(k_0 < 4U)
        {
        }
        else
        {

#line 1551
            break;
        }

#line 1551
        bool okA_0;
        if(slotOk_0)
        {

#line 1552
            okA_0 = (t0_0 + k_0) < ntmpl_1;

#line 1552
        }
        else
        {

#line 1552
            okA_0 = false;

#line 1552
        }

#line 1552
        bool okB_0;

#line 1552
        if(slotOk_0)
        {

#line 1552
            okB_0 = (t0_0 + k_0 + 1U) < ntmpl_1;

#line 1552
        }
        else
        {

#line 1552
            okB_0 = false;

#line 1552
        }
        if(okA_0)
        {

#line 1553
            q_1 = _S125 + k_0;

#line 1553
        }
        else
        {

#line 1553
            q_1 = 4294967295U;

#line 1553
        }

#line 1553
        if(okB_0)
        {

#line 1553
            n2_1 = _S125 + k_0 + 1U;

#line 1553
        }
        else
        {

#line 1553
            n2_1 = 4294967295U;

#line 1553
        }
        uint _S126 = t0_0 + k_0;

#line 1554
        uint _S127 = ntmpl_1 - 1U;

#line 1554
        uint _S128 = min(_S126, _S127);

#line 1554
        uint _S129 = min(_S126 + 1U, _S127);

#line 1554
        thread array<half2, int(16)> _S130 = dreg_1;

#line 1554
        filterTwo_0(q_1, n2_1, _S128, _S129, tid_3, &_S130, tmpl_1, peakIdx_3, peakVal_3, _S123, _S124, thrBits_3, kernelContext_7);

#line 1551
        k_0 = k_0 + 2U;

#line 1551
    }

#line 1567
    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], uint _builtinWaveLaneIndex_0 [[thread_index_in_simdgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1571
    thread KernelContext_0 kernelContext_8;

#line 1571
    (&kernelContext_8)->entryPointParams_0 = entryPointParams_1;

#line 1571
    (&kernelContext_8)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1571
    (&kernelContext_8)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1571
    (&kernelContext_8)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1571
    (&kernelContext_8)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1571
    threadgroup array<uint, int(1024)> stg_1;

#line 1571
    (&kernelContext_8)->stg_0 = &stg_1;

#line 1571
    (&kernelContext_8)->_S7 = _builtinWaveLaneIndex_0;

#line 1591
    uint _S131 = lid_0.x;

#line 1591
    uint _sub_0 = _S131 / 32U;
    uint _pr_0 = gid_0.x * 2U + _sub_0;

#line 1592
    uint _t_0 = _S131 % 32U;
    (&kernelContext_8)->_stgBase_0 = _sub_0 * 512U;

#line 1593
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_8);



    return;
}
