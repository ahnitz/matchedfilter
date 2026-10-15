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


#line 194 "mm_256_fusedTierB_c16p8t2.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 194
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


#line 200
half2 dload_0(uint device* b_1, uint i_1)
{

#line 206
    return cload_0(b_1, i_1);
}


#line 330
void cmulconjs_0(half2 ar_0, half2 ai_0, half2 br_0, half2 bi_0, half2 thread* pr_0, half2 thread* pi_0)
{
    *pr_0 = ar_0 * br_0 + ai_0 * bi_0;
    *pi_0 = ai_0 * br_0 - ar_0 * bi_0;
    return;
}


#line 342
void r4s_0(array<half2, int(16)> thread* re_0, array<half2, int(16)> thread* im_0, uint a_0, uint b_2, uint c_0, uint d_1)
{
    half2 t0r_0 = (*re_0)[a_0] + (*re_0)[c_0];

#line 344
    half2 t0i_0 = (*im_0)[a_0] + (*im_0)[c_0];
    half2 t1r_0 = (*re_0)[a_0] - (*re_0)[c_0];

#line 345
    half2 t1i_0 = (*im_0)[a_0] - (*im_0)[c_0];
    half2 t2r_0 = (*re_0)[b_2] + (*re_0)[d_1];

#line 346
    half2 t2i_0 = (*im_0)[b_2] + (*im_0)[d_1];
    half2 t3r_0 = (*re_0)[b_2] - (*re_0)[d_1];
    half2 j3r_0 = - ((*im_0)[b_2] - (*im_0)[d_1]);
    (*re_0)[a_0] = t0r_0 + t2r_0;

#line 349
    (*im_0)[a_0] = t0i_0 + t2i_0;
    (*re_0)[b_2] = t1r_0 + j3r_0;

#line 350
    (*im_0)[b_2] = t1i_0 + t3r_0;
    (*re_0)[c_0] = t0r_0 - t2r_0;

#line 351
    (*im_0)[c_0] = t0i_0 - t2i_0;
    (*re_0)[d_1] = t1r_0 - j3r_0;

#line 352
    (*im_0)[d_1] = t1i_0 - t3r_0;
    return;
}


#line 321
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 321
    half2 _S2 = half2(wr_0) ;

#line 321
    half2 _S3 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S3 + *xi_0 * _S2;
    *xr_0 = *xr_0 * _S2 - *xi_0 * _S3;

#line 325
    *xi_0 = ni_0;
    return;
}


#line 355
void swap2_0(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint p_1, uint q_0)
{

    half2 t_0 = (*re_1)[p_1];

#line 358
    (*re_1)[p_1] = (*re_1)[q_0];

#line 358
    (*re_1)[q_0] = t_0;
    half2 t_1 = (*im_1)[p_1];

#line 359
    (*im_1)[p_1] = (*im_1)[q_0];

#line 359
    (*im_1)[q_0] = t_1;
    return;
}


#line 393
void dft16s_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2)
{

#line 393
    uint n1_0 = 0U;

    for(;;)
    {

#line 395
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 395
            break;
        }

#line 395
        r4s_0(re_2, im_2, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 395
        n1_0 = n1_0 + 1U;

#line 395
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

#line 406
    uint k2_0 = 0U;
    for(;;)
    {

#line 407
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 407
            break;
        }

#line 408
        uint _S4 = 4U * k2_0;

#line 408
        r4s_0(re_2, im_2, _S4, _S4 + 1U, _S4 + 2U, _S4 + 3U);

#line 407
        k2_0 = k2_0 + 1U;

#line 407
    }

    swap2_0(re_2, im_2, 1U, 4U);

#line 409
    swap2_0(re_2, im_2, 2U, 8U);

#line 409
    swap2_0(re_2, im_2, 3U, 12U);
    swap2_0(re_2, im_2, 6U, 9U);

#line 410
    swap2_0(re_2, im_2, 7U, 13U);

#line 410
    swap2_0(re_2, im_2, 11U, 14U);
    return;
}


#line 393
void dft16s_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3)
{

#line 393
    uint n1_1 = 0U;

    for(;;)
    {

#line 395
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 395
            break;
        }

#line 395
        r4s_0(re_3, im_3, n1_1, n1_1 + 4U, n1_1 + 8U, n1_1 + 12U);

#line 395
        n1_1 = n1_1 + 1U;

#line 395
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

#line 406
    uint k2_1 = 0U;
    for(;;)
    {

#line 407
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 407
            break;
        }

#line 408
        uint _S5 = 4U * k2_1;

#line 408
        r4s_0(re_3, im_3, _S5, _S5 + 1U, _S5 + 2U, _S5 + 3U);

#line 407
        k2_1 = k2_1 + 1U;

#line 407
    }

    swap2_0(re_3, im_3, 1U, 4U);

#line 409
    swap2_0(re_3, im_3, 2U, 8U);

#line 409
    swap2_0(re_3, im_3, 3U, 12U);
    swap2_0(re_3, im_3, 6U, 9U);

#line 410
    swap2_0(re_3, im_3, 7U, 13U);

#line 410
    swap2_0(re_3, im_3, 11U, 14U);
    return;
}


#line 74 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 269 "mm_256_fusedTierB_c16p8t2.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S6 = max(TB_0, 1U);

#line 271
    uint j_0 = d_2 / _S6;

#line 271
    uint m_0 = d_2 % _S6;

#line 271
    uint _S7;
    if(TB_0 <= 16U)
    {

#line 272
        _S7 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 272
    }
    else
    {

#line 272
        _S7 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 272
    }

#line 272
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


#line 5534 "core.meta.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(2048)> threadgroup* stg_0;
    uint _S8;
};


#line 245 "mm_256_fusedTierB_c16p8t2.slang"
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 245
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 245
    return;
}


#line 246
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 246
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 431
void exchangeS_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{
    uint j_1;

    thread array<half2, int(16)> outr_0;

#line 435
    thread array<half2, int(16)> outi_0;

#line 435
    uint z_0 = 0U;
    for(;;)
    {

#line 436
        if(z_0 < 16U)
        {
        }
        else
        {

#line 436
            break;
        }

#line 436
        half2 _S9 = half2(float2(0.0f) );

#line 436
        outr_0[z_0] = _S9;

#line 436
        outi_0[z_0] = _S9;

#line 436
        z_0 = z_0 + 1U;

#line 436
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S10 = p0_0 & lenMask_0;
    uint _S11 = (_S10 >> lgSpan_0) * 16U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S10 & spanMask_0);

#line 441
    uint c_1 = 0U;
    for(;;)
    {

#line 442
        if(c_1 < 1U)
        {
        }
        else
        {

#line 442
            break;
        }

#line 442
        for(;;)
        {

#line 442
            for(;;)
            {

#line 443
                for(;;)
                {

#line 444
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 444
                    j_1 = 0U;
                    for(;;)
                    {

#line 445
                        if(j_1 < 16U)
                        {
                        }
                        else
                        {

#line 445
                            break;
                        }

#line 446
                        uint _S12 = j_1 * 16U + kernelContext_2->_tid_0;

#line 446
                        stgPut_0(_S12, (*re_4)[c_1 * 16U + j_1], kernelContext_2);

#line 445
                        j_1 = j_1 + 1U;

#line 445
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 447
                    uint d_3 = 0U;
                    for(;;)
                    {

#line 448
                        if(d_3 < 16U)
                        {
                        }
                        else
                        {

#line 448
                            break;
                        }
                        uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S13 = pz_0 & lenMask_0;
                        uint az_0 = (_S13 >> lgSpan_0) * 16U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

#line 452
                        half2 _S14 = stgGet_0(_S11 + az_0 - c_1 * 16U * 16U, kernelContext_2);



                        outr_0[d_3] = _S14;

#line 448
                        d_3 = d_3 + 1U;

#line 448
                    }

#line 443
                    break;
                }

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
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 444
                    uint j_2 = 0U;
                    for(;;)
                    {

#line 445
                        if(j_2 < 16U)
                        {
                        }
                        else
                        {

#line 445
                            break;
                        }

#line 446
                        uint _S15 = j_2 * 16U + kernelContext_2->_tid_0;

#line 446
                        stgPut_0(_S15, (*im_4)[c_1 * 16U + j_2], kernelContext_2);

#line 445
                        j_2 = j_2 + 1U;

#line 445
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 447
                    uint d_4 = 0U;
                    for(;;)
                    {

#line 448
                        if(d_4 < 16U)
                        {
                        }
                        else
                        {

#line 448
                            break;
                        }
                        uint pz_1 = computeWant_0(d_4, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S16 = pz_1 & lenMask_0;
                        uint az_1 = (_S16 >> lgSpan_0) * 16U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 452
                        half2 _S17 = stgGet_0(_S11 + az_1 - c_1 * 16U * 16U, kernelContext_2);



                        outi_0[d_4] = _S17;

#line 448
                        d_4 = d_4 + 1U;

#line 448
                    }

#line 443
                    break;
                }

#line 443
                break;
            }

#line 443
            break;
        }

#line 442
        c_1 = c_1 + 1U;

#line 442
    }

#line 442
    j_1 = 0U;

#line 461
    for(;;)
    {

#line 461
        if(j_1 < 16U)
        {
        }
        else
        {

#line 461
            break;
        }

#line 461
        (*re_4)[j_1] = outr_0[j_1];

#line 461
        (*im_4)[j_1] = outi_0[j_1];

#line 461
        j_1 = j_1 + 1U;

#line 461
    }
    return;
}


#line 464
void innermostS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5)
{
    dft16s_1(re_5, im_5);



    return;
}


#line 757
uint lgOf_0(uint i_4)
{

#line 757
    uint _S18;

#line 757
    if(i_4 < 1U)
    {

#line 757
        _S18 = 4U;

#line 757
    }
    else
    {

#line 757
        if(i_4 == 1U)
        {

#line 757
            _S18 = 4U;

#line 757
        }
        else
        {

#line 757
            _S18 = 1U;

#line 757
        }

#line 757
    }

#line 757
    return _S18;
}


#line 759
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 763
    uint lg_1 = lgOf_0(0U);

#line 768
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 417
half2 mag2s_0(half2 re_6, half2 im_6)
{

#line 417
    return re_6 * re_6 + im_6 * im_6;
}


#line 1311
uint mfShflXor_0(uint v_1, uint s_0, KernelContext_0 thread* kernelContext_3)
{

#line 1311
    uint _S19 = (simd_shuffle((v_1), ushort((int((kernelContext_3->_S8) ^ s_0)))));

#line 1311
    return _S19;
}


#line 56 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S20 = ((MF_C16_RAW));

#line 59
    return _S20;
}


#line 1433 "mm_256_fusedTierB_c16p8t2.slang"
void peakTwoGate_0(uint pairA_0, uint pairB_0, uint tid_0, const array<half2, int(16)> thread* re_7, const array<half2, int(16)> thread* im_7, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, float thr_0, KernelContext_0 thread* kernelContext_4)
{


    uint _S21 = slotToIndex_0(tid_0 * 16U) - winStart_2;
    uint _S22 = winEnd_2 - winStart_2;
    half2 _S23 = half2(float2(0.0f) );
    half2 _S24 = half2(float2(0.015625f) );

#line 1440
    uint i_5 = 0U;

#line 1440
    half2 best_0 = _S23;

#line 1440
    half2 en_0 = _S23;
    for(;;)
    {

#line 1441
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1441
            break;
        }

#line 1441
        half2 _S25;

        if((_S21 + slotToIndex_0(i_5)) < _S22)
        {

#line 1443
            _S25 = mag2s_0((*re_7)[i_5], (*im_7)[i_5]);

#line 1443
        }
        else
        {

#line 1443
            _S25 = _S23;

#line 1443
        }

#line 1443
        half2 _S26 = max(best_0, _S25);
        half2 sr_0 = (*re_7)[i_5] * _S24;

#line 1444
        half2 si_0 = (*im_7)[i_5] * _S24;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1441
        i_5 = i_5 + 1U;

#line 1441
        best_0 = _S26;

#line 1441
        en_0 = en_1;

#line 1441
    }

#line 1441
    uint _S27 = mfShflXor_0((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U), 1U, kernelContext_4);

#line 1448
    half2 _S28 = max(best_0, half2(as_type<half>(ushort(_S27 & 65535U)), as_type<half>(ushort((_S27 >> 16U) & 65535U))));

#line 1448
    uint _S29 = mfShflXor_0((uint(as_type<ushort>(en_0[0U])) & 65535U) | (uint(as_type<ushort>(en_0[1U])) << 16U), 1U, kernelContext_4);
    half2 en_2 = en_0 + half2(as_type<half>(ushort(_S29 & 65535U)), as_type<half>(ushort((_S29 >> 16U) & 65535U)));

#line 1449
    uint _S30 = mfShflXor_0((uint(as_type<ushort>(_S28[0U])) & 65535U) | (uint(as_type<ushort>(_S28[1U])) << 16U), 2U, kernelContext_4);

#line 1448
    half2 _S31 = max(_S28, half2(as_type<half>(ushort(_S30 & 65535U)), as_type<half>(ushort((_S30 >> 16U) & 65535U))));

#line 1448
    uint _S32 = mfShflXor_0((uint(as_type<ushort>(en_2[0U])) & 65535U) | (uint(as_type<ushort>(en_2[1U])) << 16U), 2U, kernelContext_4);
    half2 en_3 = en_2 + half2(as_type<half>(ushort(_S32 & 65535U)), as_type<half>(ushort((_S32 >> 16U) & 65535U)));

#line 1449
    uint _S33 = mfShflXor_0((uint(as_type<ushort>(_S31[0U])) & 65535U) | (uint(as_type<ushort>(_S31[1U])) << 16U), 4U, kernelContext_4);

#line 1448
    half2 _S34 = max(_S31, half2(as_type<half>(ushort(_S33 & 65535U)), as_type<half>(ushort((_S33 >> 16U) & 65535U))));

#line 1448
    uint _S35 = mfShflXor_0((uint(as_type<ushort>(en_3[0U])) & 65535U) | (uint(as_type<ushort>(en_3[1U])) << 16U), 4U, kernelContext_4);
    half2 en_4 = en_3 + half2(as_type<half>(ushort(_S35 & 65535U)), as_type<half>(ushort((_S35 >> 16U) & 65535U)));

#line 1449
    uint _S36 = mfShflXor_0((uint(as_type<ushort>(_S34[0U])) & 65535U) | (uint(as_type<ushort>(_S34[1U])) << 16U), 8U, kernelContext_4);

#line 1448
    half2 best_1 = max(_S34, half2(as_type<half>(ushort(_S36 & 65535U)), as_type<half>(ushort((_S36 >> 16U) & 65535U))));

#line 1448
    uint _S37 = mfShflXor_0((uint(as_type<ushort>(en_4[0U])) & 65535U) | (uint(as_type<ushort>(en_4[1U])) << 16U), 8U, kernelContext_4);
    half2 en_5 = en_4 + half2(as_type<half>(ushort(_S37 & 65535U)), as_type<half>(ushort((_S37 >> 16U) & 65535U)));

#line 1449
    uint _S38 = (uint(as_type<ushort>(en_5[0U])) & 65535U) | (uint(as_type<ushort>(en_5[1U])) << 16U);

#line 1449
    uint _S39 = (uint(as_type<ushort>(best_1[0U])) & 65535U) | (uint(as_type<ushort>(best_1[1U])) << 16U);

#line 1449
    bool infA_0;

#line 1457
    if((_S38 & 31744U) == 31744U)
    {

#line 1457
        infA_0 = true;

#line 1457
    }
    else
    {

#line 1457
        infA_0 = (_S39 & 31744U) == 31744U;

#line 1457
    }

#line 1457
    bool infB_0;
    if((_S38 & 2080374784U) == 2080374784U)
    {

#line 1458
        infB_0 = true;

#line 1458
    }
    else
    {

#line 1458
        infB_0 = (_S39 & 2080374784U) == 2080374784U;

#line 1458
    }

#line 61 "twiddle.slang"
    uint _S40 = mfC16RawFlag_0();

#line 61
    float _S41;

#line 1461 "mm_256_fusedTierB_c16p8t2.slang"
    if((1U - _S40) != 0U)
    {

#line 1461
        _S41 = 12.66209983825683594f;

#line 1461
    }
    else
    {

#line 1461
        _S41 = 0.0f;

#line 1461
    }

#line 1461
    float k2_2 = _S41 * 0.00048828125f * 1.00010001659393311f;
    float mA_0 = sqrt(float(best_1.x));

#line 1462
    float mB_0 = sqrt(float(best_1.y));

    float bA_0 = mA_0 * 1.00107669830322266f + k2_2 * sqrt(float(en_5.x) * 16.0f);
    float bB_0 = mB_0 * 1.00107669830322266f + k2_2 * sqrt(float(en_5.y) * 16.0f);

#line 1465
    bool hitA_0;
    if(infA_0)
    {

#line 1466
        hitA_0 = true;

#line 1466
    }
    else
    {

#line 1466
        if(mA_0 > 0.0f)
        {

#line 1466
            hitA_0 = bA_0 >= thr_0;

#line 1466
        }
        else
        {

#line 1466
            hitA_0 = false;

#line 1466
        }

#line 1466
    }

#line 1466
    bool hitB_0;
    if(infB_0)
    {

#line 1467
        hitB_0 = true;

#line 1467
    }
    else
    {

#line 1467
        if(mB_0 > 0.0f)
        {

#line 1467
            hitB_0 = bB_0 >= thr_0;

#line 1467
        }
        else
        {

#line 1467
            hitB_0 = false;

#line 1467
        }

#line 1467
    }
    bool _S42 = tid_0 == 0U;

#line 1468
    bool _S43;

#line 1468
    if(_S42)
    {

#line 1468
        _S43 = pairA_0 != 4294967295U;

#line 1468
    }
    else
    {

#line 1468
        _S43 = false;

#line 1468
    }

#line 1468
    int _S44;

#line 1468
    float2 _S45;

#line 1468
    if(_S43)
    {

#line 1469
        int device* _S46 = peakIdx_0+pairA_0;

#line 1469
        if(hitA_0)
        {

#line 1469
            _S44 = int(0);

#line 1469
        }
        else
        {

#line 1469
            _S44 = int(-1);

#line 1469
        }

#line 1469
        *_S46 = _S44;

#line 1469
        packed_float2 device* _S47 = peakVal_0+pairA_0;
        if(infA_0)
        {

#line 1470
            _S45 = float2(3.40282306073709653e+38f, 0.0f);

#line 1470
        }
        else
        {

#line 1470
            if(hitA_0)
            {

#line 1470
                _S45 = float2(bA_0, 0.0f);

#line 1470
            }
            else
            {

#line 1470
                _S45 = float2(0.0f, 0.0f);

#line 1470
            }

#line 1470
        }

#line 1470
        *_S47 = packed_float2(_S45) ;

#line 1468
    }



    if(_S42)
    {

#line 1472
        infA_0 = pairB_0 != 4294967295U;

#line 1472
    }
    else
    {

#line 1472
        infA_0 = false;

#line 1472
    }

#line 1472
    if(infA_0)
    {

#line 1473
        int device* _S48 = peakIdx_0+pairB_0;

#line 1473
        if(hitB_0)
        {

#line 1473
            _S44 = int(0);

#line 1473
        }
        else
        {

#line 1473
            _S44 = int(-1);

#line 1473
        }

#line 1473
        *_S48 = _S44;

#line 1473
        packed_float2 device* _S49 = peakVal_0+pairB_0;
        if(infB_0)
        {

#line 1474
            _S45 = float2(3.40282306073709653e+38f, 0.0f);

#line 1474
        }
        else
        {

#line 1474
            if(hitB_0)
            {

#line 1474
                _S45 = float2(bB_0, 0.0f);

#line 1474
            }
            else
            {

#line 1474
                _S45 = float2(0.0f, 0.0f);

#line 1474
            }

#line 1474
        }

#line 1474
        *_S49 = packed_float2(_S45) ;

#line 1472
    }



    return;
}


#line 298
float2 c16Bound_0(float2 v_2, float energy_0)
{

#line 61 "twiddle.slang"
    uint _S50 = mfC16RawFlag_0();

#line 300 "mm_256_fusedTierB_c16p8t2.slang"
    if((1U - _S50) == 0U)
    {

#line 300
        return v_2;
    }

#line 301
    float m_1 = length(v_2);
    float b_3 = m_1 * 1.00146484375f + 0.00618266593664885f * sqrt(energy_0);

#line 302
    float2 _S51;
    if(m_1 > 0.0f)
    {

#line 303
        _S51 = v_2 * float2((b_3 / m_1)) ;

#line 303
    }
    else
    {

#line 303
        _S51 = float2(b_3, 0.0f);

#line 303
    }

#line 303
    return _S51;
}


#line 1314
void peakTwoWave_0(uint pairA_1, uint pairB_1, uint tid_1, const array<half2, int(16)> thread* re_8, const array<half2, int(16)> thread* im_8, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{
    uint m_2;

#line 1316
    bool _S52;

#line 1316
    bool _S53;

    uint _S54 = slotToIndex_0(tid_1 * 16U) - winStart_3;
    uint _S55 = winEnd_3 - winStart_3;

#line 1326
    half2 _S56 = half2(float2(0.0f) );
    half2 _S57 = half2(float2(0.015625f) );

#line 1327
    uint i_6 = 0U;

#line 1327
    half2 en_6 = _S56;

#line 1327
    uint ovAcc_0 = 0U;

#line 1327
    uint kA_0 = 0U;

#line 1327
    uint kB_0 = 0U;



    for(;;)
    {

#line 1331
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1331
            break;
        }
        half2 mg_0 = mag2s_0((*re_8)[i_6], (*im_8)[i_6]);
        half2 sr_1 = (*re_8)[i_6] * _S57;

#line 1334
        half2 si_1 = (*im_8)[i_6] * _S57;
        half2 en_7 = en_6 + (sr_1 * sr_1 + si_1 * si_1);
        if((_S54 + slotToIndex_0(i_6)) < _S55)
        {

#line 1336
            m_2 = (uint(as_type<ushort>(mg_0[0U])) & 65535U) | (uint(as_type<ushort>(mg_0[1U])) << 16U);

#line 1336
        }
        else
        {

#line 1336
            m_2 = 0U;

#line 1336
        }

#line 1342
        uint ovAcc_1 = ovAcc_0 | (((((uint(as_type<ushort>((*re_8)[i_6].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[i_6].y)) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>((*im_8)[i_6].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[i_6].y)) << 16U)) & 2080406528U) + 67109888U));


        uint _S58 = 15U - i_6;

#line 1345
        uint _S59 = max(kA_0, (m_2 << 16U) | _S58);
        uint _S60 = max(kB_0, (m_2 & 4294901760U) | _S58);

#line 1331
        i_6 = i_6 + 1U;

#line 1331
        en_6 = en_7;

#line 1331
        ovAcc_0 = ovAcc_1;

#line 1331
        kA_0 = _S59;

#line 1331
        kB_0 = _S60;

#line 1331
    }

#line 1350
    if((ovAcc_0 & 32768U) != 0U)
    {

#line 1350
        kA_0 = max(kA_0, 2080374799U);

#line 1350
    }
    if((ovAcc_0 & 2147483648U) != 0U)
    {

#line 1351
        kB_0 = max(kB_0, 2080374799U);

#line 1351
    }


    uint _S61 = (4095U - tid_1) << 4U;

#line 1354
    uint kA_1 = kA_0 | _S61;
    uint kB_1 = kB_0 | _S61;

#line 1355
    uint _S62 = mfShflXor_0(kA_1, 1U, kernelContext_5);

    uint _S63 = max(kA_1, _S62);

#line 1357
    uint _S64 = mfShflXor_0(kB_1, 1U, kernelContext_5);
    uint _S65 = max(kB_1, _S64);

#line 1358
    uint _S66 = mfShflXor_0((uint(as_type<ushort>(en_6[0U])) & 65535U) | (uint(as_type<ushort>(en_6[1U])) << 16U), 1U, kernelContext_5);
    half2 en_8 = en_6 + half2(as_type<half>(ushort(_S66 & 65535U)), as_type<half>(ushort((_S66 >> 16U) & 65535U)));

#line 1359
    uint _S67 = mfShflXor_0(_S63, 2U, kernelContext_5);

#line 1357
    uint _S68 = max(_S63, _S67);

#line 1357
    uint _S69 = mfShflXor_0(_S65, 2U, kernelContext_5);
    uint _S70 = max(_S65, _S69);

#line 1358
    uint _S71 = mfShflXor_0((uint(as_type<ushort>(en_8[0U])) & 65535U) | (uint(as_type<ushort>(en_8[1U])) << 16U), 2U, kernelContext_5);
    half2 en_9 = en_8 + half2(as_type<half>(ushort(_S71 & 65535U)), as_type<half>(ushort((_S71 >> 16U) & 65535U)));

#line 1359
    uint _S72 = mfShflXor_0(_S68, 4U, kernelContext_5);

#line 1357
    uint _S73 = max(_S68, _S72);

#line 1357
    uint _S74 = mfShflXor_0(_S70, 4U, kernelContext_5);
    uint _S75 = max(_S70, _S74);

#line 1358
    uint _S76 = mfShflXor_0((uint(as_type<ushort>(en_9[0U])) & 65535U) | (uint(as_type<ushort>(en_9[1U])) << 16U), 4U, kernelContext_5);
    half2 en_10 = en_9 + half2(as_type<half>(ushort(_S76 & 65535U)), as_type<half>(ushort((_S76 >> 16U) & 65535U)));

#line 1359
    uint _S77 = mfShflXor_0(_S73, 8U, kernelContext_5);

#line 1357
    uint _S78 = max(_S73, _S77);

#line 1357
    uint _S79 = mfShflXor_0(_S75, 8U, kernelContext_5);
    uint _S80 = max(_S75, _S79);

#line 1358
    uint _S81 = mfShflXor_0((uint(as_type<ushort>(en_10[0U])) & 65535U) | (uint(as_type<ushort>(en_10[1U])) << 16U), 8U, kernelContext_5);
    half2 en_11 = en_10 + half2(as_type<half>(ushort(_S81 & 65535U)), as_type<half>(ushort((_S81 >> 16U) & 65535U)));



    float enA_0 = float(en_11.x) * 16.0f;

#line 1363
    float enB_0 = float(en_11.y) * 16.0f;
    uint slotA_0 = 65535U - (_S78 & 65535U);

#line 1364
    uint slotB_0 = 65535U - (_S80 & 65535U);

#line 1370
    uint _S82 = _S78 >> 16U;

#line 1370
    bool infA_1 = _S82 >= 31744U;

#line 1370
    uint _S83 = _S80 >> 16U;

#line 1370
    bool infB_1 = _S83 >= 31744U;

#line 1370
    bool hitA_1;



    if(infA_1)
    {

#line 1374
        hitA_1 = true;

#line 1374
    }
    else
    {

#line 1374
        hitA_1 = (as_type<half>((ushort)((_S82)))) > (as_type<float>((thrBits_1)));

#line 1374
    }

#line 1374
    bool hitB_1;
    if(infB_1)
    {

#line 1375
        hitB_1 = true;

#line 1375
    }
    else
    {

#line 1375
        hitB_1 = (as_type<half>((ushort)((_S83)))) > (as_type<float>((thrBits_1)));

#line 1375
    }

#line 1383
    uint _S84 = slotA_0 >> 4U;

#line 1383
    uint _S85 = slotA_0 & 15U;

#line 1383
    uint _S86 = slotB_0 >> 4U;

#line 1383
    uint _S87 = slotB_0 & 15U;
    thread array<float, int(2)> vA_0;

#line 1384
    thread array<float, int(2)> vB_0;
    vB_0[int(1)] = 0.0f;

#line 1385
    vB_0[int(0)] = 0.0f;

#line 1385
    vA_0[int(1)] = 0.0f;

#line 1385
    vA_0[int(0)] = 0.0f;

#line 1385
    for(;;)
    {

#line 1385
        for(;;)
        {

#line 1386
            for(;;)
            {

#line 1386
                for(;;)
                {

#line 1386
                    for(;;)
                    {

#line 1387
                        for(;;)
                        {

#line 1388
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1388
                            m_2 = 0U;
                            for(;;)
                            {

#line 1389
                                if(m_2 < 16U)
                                {
                                }
                                else
                                {

#line 1389
                                    break;
                                }

#line 1390
                                (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + m_2 * 16U + tid_1] = (uint(as_type<ushort>((*re_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[m_2].y)) << 16U);

#line 1389
                                m_2 = m_2 + 1U;

#line 1389
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            bool _S88 = tid_1 == 0U;

#line 1392
                            _S52 = _S88;

#line 1392
                            if(_S88)
                            {

#line 1393
                                if(_S85 >= 0U)
                                {

#line 1393
                                    _S53 = _S85 < 16U;

#line 1393
                                }
                                else
                                {

#line 1393
                                    _S53 = false;

#line 1393
                                }

#line 1393
                                if(_S53)
                                {

#line 1394
                                    vA_0[0U] = (as_type<half>((ushort)(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S85 * 16U + _S84]))));

#line 1393
                                }

                                if(_S87 >= 0U)
                                {

#line 1395
                                    _S53 = _S87 < 16U;

#line 1395
                                }
                                else
                                {

#line 1395
                                    _S53 = false;

#line 1395
                                }

#line 1395
                                if(_S53)
                                {

#line 1396
                                    vB_0[0U] = (as_type<half>((ushort)((((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S87 * 16U + _S86]) >> 16U))));

#line 1395
                                }

#line 1392
                            }

#line 1387
                            break;
                        }

#line 1387
                        break;
                    }

#line 1387
                    break;
                }

#line 1386
                break;
            }

#line 1386
            break;
        }

#line 1386
        for(;;)
        {

#line 1386
            for(;;)
            {

#line 1386
                for(;;)
                {

#line 1386
                    for(;;)
                    {

#line 1387
                        for(;;)
                        {

#line 1388
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1388
                            m_2 = 0U;
                            for(;;)
                            {

#line 1389
                                if(m_2 < 16U)
                                {
                                }
                                else
                                {

#line 1389
                                    break;
                                }

#line 1390
                                (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + m_2 * 16U + tid_1] = (uint(as_type<ushort>((*im_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[m_2].y)) << 16U);

#line 1389
                                m_2 = m_2 + 1U;

#line 1389
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            if(_S52)
                            {

#line 1393
                                if(_S85 >= 0U)
                                {

#line 1393
                                    _S53 = _S85 < 16U;

#line 1393
                                }
                                else
                                {

#line 1393
                                    _S53 = false;

#line 1393
                                }

#line 1393
                                if(_S53)
                                {

#line 1394
                                    vA_0[1U] = (as_type<half>((ushort)(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S85 * 16U + _S84]))));

#line 1393
                                }

                                if(_S87 >= 0U)
                                {

#line 1395
                                    _S53 = _S87 < 16U;

#line 1395
                                }
                                else
                                {

#line 1395
                                    _S53 = false;

#line 1395
                                }

#line 1395
                                if(_S53)
                                {

#line 1396
                                    vB_0[1U] = (as_type<half>((ushort)((((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S87 * 16U + _S86]) >> 16U))));

#line 1395
                                }

#line 1392
                            }

#line 1387
                            break;
                        }

#line 1387
                        break;
                    }

#line 1387
                    break;
                }

#line 1386
                break;
            }

#line 1386
            break;
        }

#line 1386
        break;
    }

#line 1400
    if(_S52)
    {

#line 1400
        _S53 = pairA_1 != 4294967295U;

#line 1400
    }
    else
    {

#line 1400
        _S53 = false;

#line 1400
    }

#line 1400
    int _S89;

#line 1400
    float2 _S90;

#line 1400
    if(_S53)
    {

#line 1401
        int device* _S91 = peakIdx_1+pairA_1;

#line 1401
        if(hitA_1)
        {

#line 1401
            _S89 = int(slotToIndex_0(slotA_0));

#line 1401
        }
        else
        {

#line 1401
            _S89 = int(-1);

#line 1401
        }

#line 1401
        *_S91 = _S89;

#line 1401
        packed_float2 device* _S92 = peakVal_1+pairA_1;
        if(infA_1)
        {

#line 1402
            _S90 = float2(3.40282306073709653e+38f, 0.0f);

#line 1402
        }
        else
        {

#line 1403
            if(hitA_1)
            {

#line 1403
                float2 _S93 = c16Bound_0(float2(vA_0[int(0)], vA_0[int(1)]), enA_0);

#line 1403
                _S90 = _S93;

#line 1403
            }
            else
            {

#line 1403
                _S90 = float2(0.0f, 0.0f);

#line 1403
            }

#line 1402
        }

#line 1402
        *_S92 = packed_float2(_S90) ;

#line 1400
    }

#line 1405
    if(_S52)
    {

#line 1405
        hitA_1 = pairB_1 != 4294967295U;

#line 1405
    }
    else
    {

#line 1405
        hitA_1 = false;

#line 1405
    }

#line 1405
    if(hitA_1)
    {

#line 1406
        int device* _S94 = peakIdx_1+pairB_1;

#line 1406
        if(hitB_1)
        {

#line 1406
            _S89 = int(slotToIndex_0(slotB_0));

#line 1406
        }
        else
        {

#line 1406
            _S89 = int(-1);

#line 1406
        }

#line 1406
        *_S94 = _S89;

#line 1406
        packed_float2 device* _S95 = peakVal_1+pairB_1;
        if(infB_1)
        {

#line 1407
            _S90 = float2(3.40282306073709653e+38f, 0.0f);

#line 1407
        }
        else
        {

#line 1408
            if(hitB_1)
            {

#line 1408
                float2 _S96 = c16Bound_0(float2(vB_0[int(0)], vB_0[int(1)]), enB_0);

#line 1408
                _S90 = _S96;

#line 1408
            }
            else
            {

#line 1408
                _S90 = float2(0.0f, 0.0f);

#line 1408
            }

#line 1407
        }

#line 1407
        *_S95 = packed_float2(_S90) ;

#line 1405
    }

#line 1410
    return;
}


#line 1483
void filterTwo_0(uint pairA_2, uint pairB_2, uint tA_0, uint tB_0, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* tmpl_0, int device* peakIdx_2, packed_float2 device* peakVal_2, uint winStart_4, uint winEnd_4, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{



    thread array<half2, int(16)> re_9;

#line 1488
    thread array<half2, int(16)> im_9;

#line 1488
    uint n2_0 = 0U;
    for(;;)
    {

#line 1489
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 1489
            break;
        }

#line 1490
        uint _S97 = 16U * n2_0;

#line 1490
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 256U + tid_2 + _S97);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 256U + tid_2 + _S97);
        half _S98 = (*dreg_0)[n2_0].x;
        half _S99 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S98, _S98), half2(_S99, _S99), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_9[n2_0], &im_9[n2_0]);

#line 1489
        n2_0 = n2_0 + 1U;

#line 1489
    }

#line 1489
    for(;;)
    {

#line 1489
        for(;;)
        {

#line 1499
            for(;;)
            {

                uint lgTB_0 = firstbithigh_0(16U);
                uint lgLn_0 = firstbithigh_0(256U);
                uint blk_2 = tid_2 >> lgTB_0;
                uint lane_2 = tid_2 & 15U;

                dft16s_0(&re_9, &im_9);

#line 1523
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 256.0f);
                float _S100 = tw_0.x;

#line 1524
                float _S101 = tw_0.y;

#line 1524
                uint k2_3 = 0U;

#line 1524
                float cr_0 = 1.0f;

#line 1524
                float ci_0 = 0.0f;

                for(;;)
                {

#line 1526
                    if(k2_3 < 16U)
                    {
                    }
                    else
                    {

#line 1526
                        break;
                    }

#line 1527
                    cmulw_0(&re_9[k2_3], &im_9[k2_3], half(cr_0), half(ci_0));
                    float nr_0 = cr_0 * _S100 - ci_0 * _S101;
                    float _S102 = cr_0 * _S101 + ci_0 * _S100;

#line 1526
                    k2_3 = k2_3 + 1U;

#line 1526
                    cr_0 = nr_0;

#line 1526
                    ci_0 = _S102;

#line 1526
                }

#line 1534
                uint per_2 = 16U / max(16U, 1U);
                uint _S103 = max(1U, 1U);
                uint blk2_2 = tid_2 / _S103;

#line 1536
                uint lane2_2 = tid_2 % _S103;

#line 1536
                exchangeS_0(&re_9, &im_9, lgLn_0, lgTB_0, 16U, 256U, blk_2, lane_2, per_2, _S103, 16U, blk2_2, lane2_2, kernelContext_6);

#line 1499
                break;
            }

#line 1499
            break;
        }

#line 1499
        break;
    }

#line 1539
    innermostS_0(&re_9, &im_9);

#line 1557
    if(thrBits_2 != 0U)
    {

#line 1558
        float _S104 = (as_type<float>((thrBits_2)));

#line 1558
        thread array<half2, int(16)> _S105 = re_9;

#line 1558
        thread array<half2, int(16)> _S106 = im_9;

#line 1558
        peakTwoGate_0(pairA_2, pairB_2, tid_2, &_S105, &_S106, peakIdx_2, peakVal_2, winStart_4, winEnd_4, _S104, kernelContext_6);

#line 1557
    }
    else
    {

#line 1557
        thread array<half2, int(16)> _S107 = re_9;

#line 1557
        thread array<half2, int(16)> _S108 = im_9;

#line 1557
        peakTwoWave_0(pairA_2, pairB_2, tid_2, &_S107, &_S108, peakIdx_2, peakVal_2, winStart_4, winEnd_4, thrBits_2, kernelContext_6);

#line 1557
    }

#line 1596
    return;
}


void filterPair_0(uint pair_0, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_3, packed_float2 device* peakVal_3, uint ntmpl_1, uint winStart_5, uint winEnd_5, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, KernelContext_0 thread* kernelContext_7)
{

#line 1600
    thread uint _S109 = winStart_5;

#line 1600
    thread uint _S110 = winEnd_5;

#line 1606
    kernelContext_7->_tid_0 = tid_3;

#line 1626
    uint tiles_0 = (ntmpl_1 + 2U - 1U) / 2U;
    uint slots_0 = binsize_1 * tiles_0;
    bool slotOk_0 = pair_0 < slots_0;

#line 1628
    uint q_1;
    if(slotOk_0)
    {

#line 1629
        q_1 = pair_0;

#line 1629
    }
    else
    {

#line 1629
        q_1 = slots_0 - 1U;

#line 1629
    }
    uint d_5 = q_1 / tiles_0;

#line 1630
    uint t0_0 = (q_1 - d_5 * tiles_0) * 2U;
    uint _S111 = d_5 * ntmpl_1 + t0_0;
    rowWindow_0(d_5, &_S109, &_S110);

#line 1656
    thread array<half2, int(16)> dreg_1;

#line 1656
    uint n2_1 = 0U;

    for(;;)
    {

#line 1658
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1658
            break;
        }

#line 1659
        dreg_1[n2_1] = dload_0(data_0, d_5 * 256U + tid_3 + 16U * n2_1);

#line 1658
        n2_1 = n2_1 + 1U;

#line 1658
    }

#line 1658
    uint k_0 = 0U;

#line 1666
    for(;;)
    {

#line 1666
        if(k_0 < 2U)
        {
        }
        else
        {

#line 1666
            break;
        }

#line 1666
        bool okA_0;
        if(slotOk_0)
        {

#line 1667
            okA_0 = (t0_0 + k_0) < ntmpl_1;

#line 1667
        }
        else
        {

#line 1667
            okA_0 = false;

#line 1667
        }

#line 1667
        bool okB_0;

#line 1667
        if(slotOk_0)
        {

#line 1667
            okB_0 = (t0_0 + k_0 + 1U) < ntmpl_1;

#line 1667
        }
        else
        {

#line 1667
            okB_0 = false;

#line 1667
        }
        if(okA_0)
        {

#line 1668
            q_1 = _S111 + k_0;

#line 1668
        }
        else
        {

#line 1668
            q_1 = 4294967295U;

#line 1668
        }

#line 1668
        if(okB_0)
        {

#line 1668
            n2_1 = _S111 + k_0 + 1U;

#line 1668
        }
        else
        {

#line 1668
            n2_1 = 4294967295U;

#line 1668
        }
        uint _S112 = t0_0 + k_0;

#line 1669
        uint _S113 = ntmpl_1 - 1U;

#line 1669
        uint _S114 = min(_S112, _S113);

#line 1669
        uint _S115 = min(_S112 + 1U, _S113);

#line 1669
        thread array<half2, int(16)> _S116 = dreg_1;

#line 1669
        filterTwo_0(q_1, n2_1, _S114, _S115, tid_3, &_S116, tmpl_1, peakIdx_3, peakVal_3, _S109, _S110, thrBits_3, kernelContext_7);

#line 1666
        k_0 = k_0 + 2U;

#line 1666
    }

#line 1682
    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], uint _builtinWaveLaneIndex_0 [[thread_index_in_simdgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1686
    thread KernelContext_0 kernelContext_8;

#line 1686
    (&kernelContext_8)->entryPointParams_0 = entryPointParams_1;

#line 1686
    (&kernelContext_8)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1686
    (&kernelContext_8)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1686
    (&kernelContext_8)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1686
    (&kernelContext_8)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1686
    threadgroup array<uint, int(2048)> stg_1;

#line 1686
    (&kernelContext_8)->stg_0 = &stg_1;

#line 1686
    (&kernelContext_8)->_S8 = _builtinWaveLaneIndex_0;

#line 1706
    uint _S117 = lid_0.x;

#line 1706
    uint _sub_0 = _S117 / 16U;
    uint _pr_0 = gid_0.x * 8U + _sub_0;

#line 1707
    uint _t_0 = _S117 % 16U;
    (&kernelContext_8)->_stgBase_0 = _sub_0 * 256U;

#line 1708
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_8);



    return;
}
