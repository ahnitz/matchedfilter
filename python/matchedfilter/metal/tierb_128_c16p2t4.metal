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


#line 194 "mm_128_fusedTierB_c16p2t4.slang"
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


#line 74 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 269 "mm_128_fusedTierB_c16p2t4.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S5 = max(TB_0, 1U);

#line 271
    uint j_0 = d_2 / _S5;

#line 271
    uint m_0 = d_2 % _S5;

#line 271
    uint _S6;
    if(TB_0 <= 16U)
    {

#line 272
        _S6 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 272
    }
    else
    {

#line 272
        _S6 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 272
    }

#line 272
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
    array<uint, int(256)> threadgroup* stg_0;
    uint _S7;
};


#line 245 "mm_128_fusedTierB_c16p2t4.slang"
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
void exchangeS_0(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
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
        half2 _S8 = half2(float2(0.0f) );

#line 436
        outr_0[z_0] = _S8;

#line 436
        outi_0[z_0] = _S8;

#line 436
        z_0 = z_0 + 1U;

#line 436
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S9 = p0_0 & lenMask_0;
    uint _S10 = (_S9 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S9 & spanMask_0);

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
                        uint _S11 = j_1 * 8U + kernelContext_2->_tid_0;

#line 446
                        stgPut_0(_S11, (*re_3)[c_1 * 16U + j_1], kernelContext_2);

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
                        uint _S12 = pz_0 & lenMask_0;
                        uint az_0 = (_S12 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S12 & spanMask_0);

#line 452
                        half2 _S13 = stgGet_0(_S10 + az_0 - c_1 * 16U * 8U, kernelContext_2);



                        outr_0[d_3] = _S13;

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
                        uint _S14 = j_2 * 8U + kernelContext_2->_tid_0;

#line 446
                        stgPut_0(_S14, (*im_3)[c_1 * 16U + j_2], kernelContext_2);

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
                        uint _S15 = pz_1 & lenMask_0;
                        uint az_1 = (_S15 >> lgSpan_0) * 8U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 452
                        half2 _S16 = stgGet_0(_S10 + az_1 - c_1 * 16U * 8U, kernelContext_2);



                        outi_0[d_4] = _S16;

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
        (*re_3)[j_1] = outr_0[j_1];

#line 461
        (*im_3)[j_1] = outi_0[j_1];

#line 461
        j_1 = j_1 + 1U;

#line 461
    }
    return;
}


#line 375
void dft8s_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4, uint o_0)
{
    thread array<half2, int(8)> br_1;

#line 377
    thread array<half2, int(8)> bi_1;

#line 377
    uint s_0 = 1U;
    for(;;)
    {

#line 378
        if(s_0 < 8U)
        {
        }
        else
        {

#line 378
            break;
        }

#line 378
        uint j_3 = 0U;
        for(;;)
        {

#line 379
            if(j_3 < 4U)
            {
            }
            else
            {

#line 379
                break;
            }

#line 380
            uint k_0 = j_3 & (s_0 - 1U);

#line 380
            uint base_0 = (j_3 - k_0) << 1U;
            float ang_0 = 3.14159274101257324f * float(k_0) / float(s_0);
            uint _S17 = o_0 + j_3;

#line 382
            uint _S18 = _S17 + 4U;

#line 382
            thread half2 vr_0 = (*re_4)[_S18];

#line 382
            thread half2 vi_0 = (*im_4)[_S18];
            float2 tw_0 = mfTwiddle_0(ang_0);
            cmulw_0(&vr_0, &vi_0, half(tw_0.x), half(tw_0.y));

            uint _S19 = base_0 + k_0;

#line 386
            br_1[_S19] = (*re_4)[_S17] + vr_0;

#line 386
            bi_1[_S19] = (*im_4)[_S17] + vi_0;
            uint _S20 = _S19 + s_0;

#line 387
            br_1[_S20] = (*re_4)[_S17] - vr_0;

#line 387
            bi_1[_S20] = (*im_4)[_S17] - vi_0;

#line 379
            j_3 = j_3 + 1U;

#line 379
        }

#line 379
        uint i_4 = 0U;

#line 389
        for(;;)
        {

#line 389
            if(i_4 < 8U)
            {
            }
            else
            {

#line 389
                break;
            }

#line 389
            uint _S21 = o_0 + i_4;

#line 389
            (*re_4)[_S21] = br_1[i_4];

#line 389
            (*im_4)[_S21] = bi_1[i_4];

#line 389
            i_4 = i_4 + 1U;

#line 389
        }

#line 378
        s_0 = s_0 << 1U;

#line 378
    }

#line 391
    return;
}


#line 464
void innermostS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5)
{

#line 464
    uint b_3 = 0U;


    for(;;)
    {

#line 467
        if(b_3 < 2U)
        {
        }
        else
        {

#line 467
            break;
        }

#line 467
        dft8s_0(re_5, im_5, b_3 * 8U);

#line 467
        b_3 = b_3 + 1U;

#line 467
    }


    return;
}


#line 757
uint lgOf_0(uint i_5)
{

#line 757
    uint _S22;

#line 757
    if(i_5 < 1U)
    {

#line 757
        _S22 = 4U;

#line 757
    }
    else
    {

#line 757
        if(i_5 == 1U)
        {

#line 757
            _S22 = 3U;

#line 757
        }
        else
        {

#line 757
            _S22 = 1U;

#line 757
        }

#line 757
    }

#line 757
    return _S22;
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
uint mfShflXor_0(uint v_1, uint s_1, KernelContext_0 thread* kernelContext_3)
{

#line 1311
    uint _S23 = (simd_shuffle((v_1), ushort((int((kernelContext_3->_S7) ^ s_1)))));

#line 1311
    return _S23;
}


#line 56 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S24 = ((MF_C16_RAW));

#line 59
    return _S24;
}


#line 1433 "mm_128_fusedTierB_c16p2t4.slang"
void peakTwoGate_0(uint pairA_0, uint pairB_0, uint tid_0, const array<half2, int(16)> thread* re_7, const array<half2, int(16)> thread* im_7, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, float thr_0, KernelContext_0 thread* kernelContext_4)
{


    uint _S25 = slotToIndex_0(tid_0 * 16U) - winStart_2;
    uint _S26 = winEnd_2 - winStart_2;
    half2 _S27 = half2(float2(0.0f) );
    half2 _S28 = half2(float2(0.015625f) );

#line 1440
    uint i_6 = 0U;

#line 1440
    half2 best_0 = _S27;

#line 1440
    half2 en_0 = _S27;
    for(;;)
    {

#line 1441
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1441
            break;
        }

#line 1441
        half2 _S29;

        if((_S25 + slotToIndex_0(i_6)) < _S26)
        {

#line 1443
            _S29 = mag2s_0((*re_7)[i_6], (*im_7)[i_6]);

#line 1443
        }
        else
        {

#line 1443
            _S29 = _S27;

#line 1443
        }

#line 1443
        half2 _S30 = max(best_0, _S29);
        half2 sr_0 = (*re_7)[i_6] * _S28;

#line 1444
        half2 si_0 = (*im_7)[i_6] * _S28;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1441
        i_6 = i_6 + 1U;

#line 1441
        best_0 = _S30;

#line 1441
        en_0 = en_1;

#line 1441
    }

#line 1441
    uint _S31 = mfShflXor_0((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U), 1U, kernelContext_4);

#line 1448
    half2 _S32 = max(best_0, half2(as_type<half>(ushort(_S31 & 65535U)), as_type<half>(ushort((_S31 >> 16U) & 65535U))));

#line 1448
    uint _S33 = mfShflXor_0((uint(as_type<ushort>(en_0[0U])) & 65535U) | (uint(as_type<ushort>(en_0[1U])) << 16U), 1U, kernelContext_4);
    half2 en_2 = en_0 + half2(as_type<half>(ushort(_S33 & 65535U)), as_type<half>(ushort((_S33 >> 16U) & 65535U)));

#line 1449
    uint _S34 = mfShflXor_0((uint(as_type<ushort>(_S32[0U])) & 65535U) | (uint(as_type<ushort>(_S32[1U])) << 16U), 2U, kernelContext_4);

#line 1448
    half2 _S35 = max(_S32, half2(as_type<half>(ushort(_S34 & 65535U)), as_type<half>(ushort((_S34 >> 16U) & 65535U))));

#line 1448
    uint _S36 = mfShflXor_0((uint(as_type<ushort>(en_2[0U])) & 65535U) | (uint(as_type<ushort>(en_2[1U])) << 16U), 2U, kernelContext_4);
    half2 en_3 = en_2 + half2(as_type<half>(ushort(_S36 & 65535U)), as_type<half>(ushort((_S36 >> 16U) & 65535U)));

#line 1449
    uint _S37 = mfShflXor_0((uint(as_type<ushort>(_S35[0U])) & 65535U) | (uint(as_type<ushort>(_S35[1U])) << 16U), 4U, kernelContext_4);

#line 1448
    half2 best_1 = max(_S35, half2(as_type<half>(ushort(_S37 & 65535U)), as_type<half>(ushort((_S37 >> 16U) & 65535U))));

#line 1448
    uint _S38 = mfShflXor_0((uint(as_type<ushort>(en_3[0U])) & 65535U) | (uint(as_type<ushort>(en_3[1U])) << 16U), 4U, kernelContext_4);
    half2 en_4 = en_3 + half2(as_type<half>(ushort(_S38 & 65535U)), as_type<half>(ushort((_S38 >> 16U) & 65535U)));

#line 1449
    uint _S39 = (uint(as_type<ushort>(en_4[0U])) & 65535U) | (uint(as_type<ushort>(en_4[1U])) << 16U);

#line 1449
    uint _S40 = (uint(as_type<ushort>(best_1[0U])) & 65535U) | (uint(as_type<ushort>(best_1[1U])) << 16U);

#line 1449
    bool infA_0;

#line 1457
    if((_S39 & 31744U) == 31744U)
    {

#line 1457
        infA_0 = true;

#line 1457
    }
    else
    {

#line 1457
        infA_0 = (_S40 & 31744U) == 31744U;

#line 1457
    }

#line 1457
    bool infB_0;
    if((_S39 & 2080374784U) == 2080374784U)
    {

#line 1458
        infB_0 = true;

#line 1458
    }
    else
    {

#line 1458
        infB_0 = (_S40 & 2080374784U) == 2080374784U;

#line 1458
    }

#line 61 "twiddle.slang"
    uint _S41 = mfC16RawFlag_0();

#line 61
    float _S42;

#line 1461 "mm_128_fusedTierB_c16p2t4.slang"
    if((1U - _S41) != 0U)
    {

#line 1461
        _S42 = 11.95860004425048828f;

#line 1461
    }
    else
    {

#line 1461
        _S42 = 0.0f;

#line 1461
    }

#line 1461
    float k2_1 = _S42 * 0.00048828125f * 1.00010001659393311f;
    float mA_0 = sqrt(float(best_1.x));

#line 1462
    float mB_0 = sqrt(float(best_1.y));

    float bA_0 = mA_0 * 1.00107669830322266f + k2_1 * sqrt(float(en_4.x) * 32.0f);
    float bB_0 = mB_0 * 1.00107669830322266f + k2_1 * sqrt(float(en_4.y) * 32.0f);

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
    bool _S43 = tid_0 == 0U;

#line 1468
    bool _S44;

#line 1468
    if(_S43)
    {

#line 1468
        _S44 = pairA_0 != 4294967295U;

#line 1468
    }
    else
    {

#line 1468
        _S44 = false;

#line 1468
    }

#line 1468
    int _S45;

#line 1468
    float2 _S46;

#line 1468
    if(_S44)
    {

#line 1469
        int device* _S47 = peakIdx_0+pairA_0;

#line 1469
        if(hitA_0)
        {

#line 1469
            _S45 = int(0);

#line 1469
        }
        else
        {

#line 1469
            _S45 = int(-1);

#line 1469
        }

#line 1469
        *_S47 = _S45;

#line 1469
        packed_float2 device* _S48 = peakVal_0+pairA_0;
        if(infA_0)
        {

#line 1470
            _S46 = float2(3.40282306073709653e+38f, 0.0f);

#line 1470
        }
        else
        {

#line 1470
            if(hitA_0)
            {

#line 1470
                _S46 = float2(bA_0, 0.0f);

#line 1470
            }
            else
            {

#line 1470
                _S46 = float2(0.0f, 0.0f);

#line 1470
            }

#line 1470
        }

#line 1470
        *_S48 = packed_float2(_S46) ;

#line 1468
    }



    if(_S43)
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
        int device* _S49 = peakIdx_0+pairB_0;

#line 1473
        if(hitB_0)
        {

#line 1473
            _S45 = int(0);

#line 1473
        }
        else
        {

#line 1473
            _S45 = int(-1);

#line 1473
        }

#line 1473
        *_S49 = _S45;

#line 1473
        packed_float2 device* _S50 = peakVal_0+pairB_0;
        if(infB_0)
        {

#line 1474
            _S46 = float2(3.40282306073709653e+38f, 0.0f);

#line 1474
        }
        else
        {

#line 1474
            if(hitB_0)
            {

#line 1474
                _S46 = float2(bB_0, 0.0f);

#line 1474
            }
            else
            {

#line 1474
                _S46 = float2(0.0f, 0.0f);

#line 1474
            }

#line 1474
        }

#line 1474
        *_S50 = packed_float2(_S46) ;

#line 1472
    }



    return;
}


#line 298
float2 c16Bound_0(float2 v_2, float energy_0)
{

#line 61 "twiddle.slang"
    uint _S51 = mfC16RawFlag_0();

#line 300 "mm_128_fusedTierB_c16p2t4.slang"
    if((1U - _S51) == 0U)
    {

#line 300
        return v_2;
    }

#line 301
    float m_1 = length(v_2);
    float b_4 = m_1 * 1.00146484375f + 0.00583916017785668f * sqrt(energy_0);

#line 302
    float2 _S52;
    if(m_1 > 0.0f)
    {

#line 303
        _S52 = v_2 * float2((b_4 / m_1)) ;

#line 303
    }
    else
    {

#line 303
        _S52 = float2(b_4, 0.0f);

#line 303
    }

#line 303
    return _S52;
}


#line 1314
void peakTwoWave_0(uint pairA_1, uint pairB_1, uint tid_1, const array<half2, int(16)> thread* re_8, const array<half2, int(16)> thread* im_8, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{
    uint m_2;

#line 1316
    bool _S53;

#line 1316
    bool _S54;

    uint _S55 = slotToIndex_0(tid_1 * 16U) - winStart_3;
    uint _S56 = winEnd_3 - winStart_3;

#line 1326
    half2 _S57 = half2(float2(0.0f) );
    half2 _S58 = half2(float2(0.015625f) );

#line 1327
    uint i_7 = 0U;

#line 1327
    half2 en_5 = _S57;

#line 1327
    uint ovAcc_0 = 0U;

#line 1327
    uint kA_0 = 0U;

#line 1327
    uint kB_0 = 0U;



    for(;;)
    {

#line 1331
        if(i_7 < 16U)
        {
        }
        else
        {

#line 1331
            break;
        }
        half2 mg_0 = mag2s_0((*re_8)[i_7], (*im_8)[i_7]);
        half2 sr_1 = (*re_8)[i_7] * _S58;

#line 1334
        half2 si_1 = (*im_8)[i_7] * _S58;
        half2 en_6 = en_5 + (sr_1 * sr_1 + si_1 * si_1);
        if((_S55 + slotToIndex_0(i_7)) < _S56)
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
        uint ovAcc_1 = ovAcc_0 | (((((uint(as_type<ushort>((*re_8)[i_7].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[i_7].y)) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>((*im_8)[i_7].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[i_7].y)) << 16U)) & 2080406528U) + 67109888U));


        uint _S59 = 15U - i_7;

#line 1345
        uint _S60 = max(kA_0, (m_2 << 16U) | _S59);
        uint _S61 = max(kB_0, (m_2 & 4294901760U) | _S59);

#line 1331
        i_7 = i_7 + 1U;

#line 1331
        en_5 = en_6;

#line 1331
        ovAcc_0 = ovAcc_1;

#line 1331
        kA_0 = _S60;

#line 1331
        kB_0 = _S61;

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


    uint _S62 = (4095U - tid_1) << 4U;

#line 1354
    uint kA_1 = kA_0 | _S62;
    uint kB_1 = kB_0 | _S62;

#line 1355
    uint _S63 = mfShflXor_0(kA_1, 1U, kernelContext_5);

    uint _S64 = max(kA_1, _S63);

#line 1357
    uint _S65 = mfShflXor_0(kB_1, 1U, kernelContext_5);
    uint _S66 = max(kB_1, _S65);

#line 1358
    uint _S67 = mfShflXor_0((uint(as_type<ushort>(en_5[0U])) & 65535U) | (uint(as_type<ushort>(en_5[1U])) << 16U), 1U, kernelContext_5);
    half2 en_7 = en_5 + half2(as_type<half>(ushort(_S67 & 65535U)), as_type<half>(ushort((_S67 >> 16U) & 65535U)));

#line 1359
    uint _S68 = mfShflXor_0(_S64, 2U, kernelContext_5);

#line 1357
    uint _S69 = max(_S64, _S68);

#line 1357
    uint _S70 = mfShflXor_0(_S66, 2U, kernelContext_5);
    uint _S71 = max(_S66, _S70);

#line 1358
    uint _S72 = mfShflXor_0((uint(as_type<ushort>(en_7[0U])) & 65535U) | (uint(as_type<ushort>(en_7[1U])) << 16U), 2U, kernelContext_5);
    half2 en_8 = en_7 + half2(as_type<half>(ushort(_S72 & 65535U)), as_type<half>(ushort((_S72 >> 16U) & 65535U)));

#line 1359
    uint _S73 = mfShflXor_0(_S69, 4U, kernelContext_5);

#line 1357
    uint _S74 = max(_S69, _S73);

#line 1357
    uint _S75 = mfShflXor_0(_S71, 4U, kernelContext_5);
    uint _S76 = max(_S71, _S75);

#line 1358
    uint _S77 = mfShflXor_0((uint(as_type<ushort>(en_8[0U])) & 65535U) | (uint(as_type<ushort>(en_8[1U])) << 16U), 4U, kernelContext_5);
    half2 en_9 = en_8 + half2(as_type<half>(ushort(_S77 & 65535U)), as_type<half>(ushort((_S77 >> 16U) & 65535U)));



    float enA_0 = float(en_9.x) * 32.0f;

#line 1363
    float enB_0 = float(en_9.y) * 32.0f;
    uint slotA_0 = 65535U - (_S74 & 65535U);

#line 1364
    uint slotB_0 = 65535U - (_S76 & 65535U);

#line 1370
    uint _S78 = _S74 >> 16U;

#line 1370
    bool infA_1 = _S78 >= 31744U;

#line 1370
    uint _S79 = _S76 >> 16U;

#line 1370
    bool infB_1 = _S79 >= 31744U;

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
        hitA_1 = (as_type<half>((ushort)((_S78)))) > (as_type<float>((thrBits_1)));

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
        hitB_1 = (as_type<half>((ushort)((_S79)))) > (as_type<float>((thrBits_1)));

#line 1375
    }

#line 1383
    uint _S80 = slotA_0 >> 4U;

#line 1383
    uint _S81 = slotA_0 & 15U;

#line 1383
    uint _S82 = slotB_0 >> 4U;

#line 1383
    uint _S83 = slotB_0 & 15U;
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
                                (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + m_2 * 8U + tid_1] = (uint(as_type<ushort>((*re_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[m_2].y)) << 16U);

#line 1389
                                m_2 = m_2 + 1U;

#line 1389
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            bool _S84 = tid_1 == 0U;

#line 1392
                            _S53 = _S84;

#line 1392
                            if(_S84)
                            {

#line 1393
                                if(_S81 >= 0U)
                                {

#line 1393
                                    _S54 = _S81 < 16U;

#line 1393
                                }
                                else
                                {

#line 1393
                                    _S54 = false;

#line 1393
                                }

#line 1393
                                if(_S54)
                                {

#line 1394
                                    vA_0[0U] = (as_type<half>((ushort)(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S81 * 8U + _S80]))));

#line 1393
                                }

                                if(_S83 >= 0U)
                                {

#line 1395
                                    _S54 = _S83 < 16U;

#line 1395
                                }
                                else
                                {

#line 1395
                                    _S54 = false;

#line 1395
                                }

#line 1395
                                if(_S54)
                                {

#line 1396
                                    vB_0[0U] = (as_type<half>((ushort)((((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S83 * 8U + _S82]) >> 16U))));

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
                                (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + m_2 * 8U + tid_1] = (uint(as_type<ushort>((*im_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[m_2].y)) << 16U);

#line 1389
                                m_2 = m_2 + 1U;

#line 1389
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            if(_S53)
                            {

#line 1393
                                if(_S81 >= 0U)
                                {

#line 1393
                                    _S54 = _S81 < 16U;

#line 1393
                                }
                                else
                                {

#line 1393
                                    _S54 = false;

#line 1393
                                }

#line 1393
                                if(_S54)
                                {

#line 1394
                                    vA_0[1U] = (as_type<half>((ushort)(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S81 * 8U + _S80]))));

#line 1393
                                }

                                if(_S83 >= 0U)
                                {

#line 1395
                                    _S54 = _S83 < 16U;

#line 1395
                                }
                                else
                                {

#line 1395
                                    _S54 = false;

#line 1395
                                }

#line 1395
                                if(_S54)
                                {

#line 1396
                                    vB_0[1U] = (as_type<half>((ushort)((((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S83 * 8U + _S82]) >> 16U))));

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
    if(_S53)
    {

#line 1400
        _S54 = pairA_1 != 4294967295U;

#line 1400
    }
    else
    {

#line 1400
        _S54 = false;

#line 1400
    }

#line 1400
    int _S85;

#line 1400
    float2 _S86;

#line 1400
    if(_S54)
    {

#line 1401
        int device* _S87 = peakIdx_1+pairA_1;

#line 1401
        if(hitA_1)
        {

#line 1401
            _S85 = int(slotToIndex_0(slotA_0));

#line 1401
        }
        else
        {

#line 1401
            _S85 = int(-1);

#line 1401
        }

#line 1401
        *_S87 = _S85;

#line 1401
        packed_float2 device* _S88 = peakVal_1+pairA_1;
        if(infA_1)
        {

#line 1402
            _S86 = float2(3.40282306073709653e+38f, 0.0f);

#line 1402
        }
        else
        {

#line 1403
            if(hitA_1)
            {

#line 1403
                float2 _S89 = c16Bound_0(float2(vA_0[int(0)], vA_0[int(1)]), enA_0);

#line 1403
                _S86 = _S89;

#line 1403
            }
            else
            {

#line 1403
                _S86 = float2(0.0f, 0.0f);

#line 1403
            }

#line 1402
        }

#line 1402
        *_S88 = packed_float2(_S86) ;

#line 1400
    }

#line 1405
    if(_S53)
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
        int device* _S90 = peakIdx_1+pairB_1;

#line 1406
        if(hitB_1)
        {

#line 1406
            _S85 = int(slotToIndex_0(slotB_0));

#line 1406
        }
        else
        {

#line 1406
            _S85 = int(-1);

#line 1406
        }

#line 1406
        *_S90 = _S85;

#line 1406
        packed_float2 device* _S91 = peakVal_1+pairB_1;
        if(infB_1)
        {

#line 1407
            _S86 = float2(3.40282306073709653e+38f, 0.0f);

#line 1407
        }
        else
        {

#line 1408
            if(hitB_1)
            {

#line 1408
                float2 _S92 = c16Bound_0(float2(vB_0[int(0)], vB_0[int(1)]), enB_0);

#line 1408
                _S86 = _S92;

#line 1408
            }
            else
            {

#line 1408
                _S86 = float2(0.0f, 0.0f);

#line 1408
            }

#line 1407
        }

#line 1407
        *_S91 = packed_float2(_S86) ;

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
        uint _S93 = 8U * n2_0;

#line 1490
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 128U + tid_2 + _S93);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 128U + tid_2 + _S93);
        half _S94 = (*dreg_0)[n2_0].x;
        half _S95 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S94, _S94), half2(_S95, _S95), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_9[n2_0], &im_9[n2_0]);

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

                uint lgTB_0 = firstbithigh_0(8U);
                uint lgLn_0 = firstbithigh_0(128U);
                uint blk_2 = tid_2 >> lgTB_0;
                uint lane_2 = tid_2 & 7U;

                dft16s_0(&re_9, &im_9);

#line 1523
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 128.0f);
                float _S96 = tw_1.x;

#line 1524
                float _S97 = tw_1.y;

#line 1524
                uint k2_2 = 0U;

#line 1524
                float cr_0 = 1.0f;

#line 1524
                float ci_0 = 0.0f;

                for(;;)
                {

#line 1526
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 1526
                        break;
                    }

#line 1527
                    cmulw_0(&re_9[k2_2], &im_9[k2_2], half(cr_0), half(ci_0));
                    float nr_0 = cr_0 * _S96 - ci_0 * _S97;
                    float _S98 = cr_0 * _S97 + ci_0 * _S96;

#line 1526
                    k2_2 = k2_2 + 1U;

#line 1526
                    cr_0 = nr_0;

#line 1526
                    ci_0 = _S98;

#line 1526
                }

#line 1534
                uint per_2 = 16U / max(8U, 1U);
                uint _S99 = max(0U, 1U);
                uint blk2_2 = tid_2 / _S99;

#line 1536
                uint lane2_2 = tid_2 % _S99;

#line 1536
                exchangeS_0(&re_9, &im_9, lgLn_0, lgTB_0, 8U, 128U, blk_2, lane_2, per_2, _S99, 8U, blk2_2, lane2_2, kernelContext_6);

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
        float _S100 = (as_type<float>((thrBits_2)));

#line 1558
        thread array<half2, int(16)> _S101 = re_9;

#line 1558
        thread array<half2, int(16)> _S102 = im_9;

#line 1558
        peakTwoGate_0(pairA_2, pairB_2, tid_2, &_S101, &_S102, peakIdx_2, peakVal_2, winStart_4, winEnd_4, _S100, kernelContext_6);

#line 1557
    }
    else
    {

#line 1557
        thread array<half2, int(16)> _S103 = re_9;

#line 1557
        thread array<half2, int(16)> _S104 = im_9;

#line 1557
        peakTwoWave_0(pairA_2, pairB_2, tid_2, &_S103, &_S104, peakIdx_2, peakVal_2, winStart_4, winEnd_4, thrBits_2, kernelContext_6);

#line 1557
    }

#line 1596
    return;
}


void filterPair_0(uint pair_0, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_3, packed_float2 device* peakVal_3, uint ntmpl_1, uint winStart_5, uint winEnd_5, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, KernelContext_0 thread* kernelContext_7)
{

#line 1600
    thread uint _S105 = winStart_5;

#line 1600
    thread uint _S106 = winEnd_5;

#line 1606
    kernelContext_7->_tid_0 = tid_3;

#line 1626
    uint tiles_0 = (ntmpl_1 + 4U - 1U) / 4U;
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
    uint t0_0 = (q_1 - d_5 * tiles_0) * 4U;
    uint _S107 = d_5 * ntmpl_1 + t0_0;
    rowWindow_0(d_5, &_S105, &_S106);

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
        dreg_1[n2_1] = dload_0(data_0, d_5 * 128U + tid_3 + 8U * n2_1);

#line 1658
        n2_1 = n2_1 + 1U;

#line 1658
    }

#line 1658
    uint k_1 = 0U;

#line 1666
    for(;;)
    {

#line 1666
        if(k_1 < 4U)
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
            okA_0 = (t0_0 + k_1) < ntmpl_1;

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
            okB_0 = (t0_0 + k_1 + 1U) < ntmpl_1;

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
            q_1 = _S107 + k_1;

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
            n2_1 = _S107 + k_1 + 1U;

#line 1668
        }
        else
        {

#line 1668
            n2_1 = 4294967295U;

#line 1668
        }
        uint _S108 = t0_0 + k_1;

#line 1669
        uint _S109 = ntmpl_1 - 1U;

#line 1669
        uint _S110 = min(_S108, _S109);

#line 1669
        uint _S111 = min(_S108 + 1U, _S109);

#line 1669
        thread array<half2, int(16)> _S112 = dreg_1;

#line 1669
        filterTwo_0(q_1, n2_1, _S110, _S111, tid_3, &_S112, tmpl_1, peakIdx_3, peakVal_3, _S105, _S106, thrBits_3, kernelContext_7);

#line 1666
        k_1 = k_1 + 2U;

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
    threadgroup array<uint, int(256)> stg_1;

#line 1686
    (&kernelContext_8)->stg_0 = &stg_1;

#line 1686
    (&kernelContext_8)->_S7 = _builtinWaveLaneIndex_0;

#line 1706
    uint _S113 = lid_0.x;

#line 1706
    uint _sub_0 = _S113 / 8U;
    uint _pr_0 = gid_0.x * 2U + _sub_0;

#line 1707
    uint _t_0 = _S113 % 8U;
    (&kernelContext_8)->_stgBase_0 = _sub_0 * 128U;

#line 1708
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_8);



    return;
}
