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


#line 191 "mm_512_fusedTierB_c16t4.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 191
    return;
}


#line 159
half2 cload_0(uint device* b_0, uint i_0)
{

#line 160
    uint p_0 = b_0[i_0];

#line 160
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 197
half2 dload_0(uint device* b_1, uint i_1)
{


    return cload_0(b_1, i_1);
}


#line 325
void cmulconjs_0(half2 ar_0, half2 ai_0, half2 br_0, half2 bi_0, half2 thread* pr_0, half2 thread* pi_0)
{
    *pr_0 = ar_0 * br_0 + ai_0 * bi_0;
    *pi_0 = ai_0 * br_0 - ar_0 * bi_0;
    return;
}


#line 337
void r4s_0(array<half2, int(16)> thread* re_0, array<half2, int(16)> thread* im_0, uint a_0, uint b_2, uint c_0, uint d_1)
{
    half2 t0r_0 = (*re_0)[a_0] + (*re_0)[c_0];

#line 339
    half2 t0i_0 = (*im_0)[a_0] + (*im_0)[c_0];
    half2 t1r_0 = (*re_0)[a_0] - (*re_0)[c_0];

#line 340
    half2 t1i_0 = (*im_0)[a_0] - (*im_0)[c_0];
    half2 t2r_0 = (*re_0)[b_2] + (*re_0)[d_1];

#line 341
    half2 t2i_0 = (*im_0)[b_2] + (*im_0)[d_1];
    half2 t3r_0 = (*re_0)[b_2] - (*re_0)[d_1];
    half2 j3r_0 = - ((*im_0)[b_2] - (*im_0)[d_1]);
    (*re_0)[a_0] = t0r_0 + t2r_0;

#line 344
    (*im_0)[a_0] = t0i_0 + t2i_0;
    (*re_0)[b_2] = t1r_0 + j3r_0;

#line 345
    (*im_0)[b_2] = t1i_0 + t3r_0;
    (*re_0)[c_0] = t0r_0 - t2r_0;

#line 346
    (*im_0)[c_0] = t0i_0 - t2i_0;
    (*re_0)[d_1] = t1r_0 - j3r_0;

#line 347
    (*im_0)[d_1] = t1i_0 - t3r_0;
    return;
}


#line 316
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 316
    half2 _S2 = half2(wr_0) ;

#line 316
    half2 _S3 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S3 + *xi_0 * _S2;
    *xr_0 = *xr_0 * _S2 - *xi_0 * _S3;

#line 320
    *xi_0 = ni_0;
    return;
}


#line 350
void swap2_0(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint p_1, uint q_0)
{

    half2 t_0 = (*re_1)[p_1];

#line 353
    (*re_1)[p_1] = (*re_1)[q_0];

#line 353
    (*re_1)[q_0] = t_0;
    half2 t_1 = (*im_1)[p_1];

#line 354
    (*im_1)[p_1] = (*im_1)[q_0];

#line 354
    (*im_1)[q_0] = t_1;
    return;
}


#line 388
void dft16s_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2)
{

#line 388
    uint n1_0 = 0U;

    for(;;)
    {

#line 390
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 390
            break;
        }

#line 390
        r4s_0(re_2, im_2, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 390
        n1_0 = n1_0 + 1U;

#line 390
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

#line 401
    uint k2_0 = 0U;
    for(;;)
    {

#line 402
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 402
            break;
        }

#line 403
        uint _S4 = 4U * k2_0;

#line 403
        r4s_0(re_2, im_2, _S4, _S4 + 1U, _S4 + 2U, _S4 + 3U);

#line 402
        k2_0 = k2_0 + 1U;

#line 402
    }

    swap2_0(re_2, im_2, 1U, 4U);

#line 404
    swap2_0(re_2, im_2, 2U, 8U);

#line 404
    swap2_0(re_2, im_2, 3U, 12U);
    swap2_0(re_2, im_2, 6U, 9U);

#line 405
    swap2_0(re_2, im_2, 7U, 13U);

#line 405
    swap2_0(re_2, im_2, 11U, 14U);
    return;
}


#line 58 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 264 "mm_512_fusedTierB_c16t4.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S5 = max(TB_0, 1U);

#line 266
    uint j_0 = d_2 / _S5;

#line 266
    uint m_0 = d_2 % _S5;

#line 266
    uint _S6;
    if(TB_0 <= 16U)
    {

#line 267
        _S6 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 267
    }
    else
    {

#line 267
        _S6 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 267
    }

#line 267
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


#line 240 "mm_512_fusedTierB_c16t4.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    uint device* entryPointParams_data_0;
    uint device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(512)> threadgroup* stg_0;
    uint _S7;
};


#line 240
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 240
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 240
    return;
}


#line 241
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 241
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 426
void exchangeS_0(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{
    uint j_1;

    thread array<half2, int(16)> outr_0;

#line 430
    thread array<half2, int(16)> outi_0;

#line 430
    uint z_0 = 0U;
    for(;;)
    {

#line 431
        if(z_0 < 16U)
        {
        }
        else
        {

#line 431
            break;
        }

#line 431
        half2 _S8 = half2(float2(0.0) );

#line 431
        outr_0[z_0] = _S8;

#line 431
        outi_0[z_0] = _S8;

#line 431
        z_0 = z_0 + 1U;

#line 431
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S9 = p0_0 & lenMask_0;
    uint _S10 = (_S9 >> lgSpan_0) * 32U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S9 & spanMask_0);

#line 436
    uint c_1 = 0U;
    for(;;)
    {

#line 437
        if(c_1 < 1U)
        {
        }
        else
        {

#line 437
            break;
        }

#line 437
        for(;;)
        {

#line 437
            for(;;)
            {

#line 438
                for(;;)
                {

#line 439
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 439
                    j_1 = 0U;
                    for(;;)
                    {

#line 440
                        if(j_1 < 16U)
                        {
                        }
                        else
                        {

#line 440
                            break;
                        }

#line 441
                        uint _S11 = j_1 * 32U + kernelContext_2->_tid_0;

#line 441
                        stgPut_0(_S11, (*re_3)[c_1 * 16U + j_1], kernelContext_2);

#line 440
                        j_1 = j_1 + 1U;

#line 440
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 442
                    uint d_3 = 0U;
                    for(;;)
                    {

#line 443
                        if(d_3 < 16U)
                        {
                        }
                        else
                        {

#line 443
                            break;
                        }
                        uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S12 = pz_0 & lenMask_0;
                        uint az_0 = (_S12 >> lgSpan_0) * 32U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S12 & spanMask_0);

#line 447
                        half2 _S13 = stgGet_0(_S10 + az_0 - c_1 * 16U * 32U, kernelContext_2);



                        outr_0[d_3] = _S13;

#line 443
                        d_3 = d_3 + 1U;

#line 443
                    }

#line 438
                    break;
                }

#line 438
                break;
            }

#line 438
            for(;;)
            {

#line 438
                for(;;)
                {

#line 439
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 439
                    uint j_2 = 0U;
                    for(;;)
                    {

#line 440
                        if(j_2 < 16U)
                        {
                        }
                        else
                        {

#line 440
                            break;
                        }

#line 441
                        uint _S14 = j_2 * 32U + kernelContext_2->_tid_0;

#line 441
                        stgPut_0(_S14, (*im_3)[c_1 * 16U + j_2], kernelContext_2);

#line 440
                        j_2 = j_2 + 1U;

#line 440
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 442
                    uint d_4 = 0U;
                    for(;;)
                    {

#line 443
                        if(d_4 < 16U)
                        {
                        }
                        else
                        {

#line 443
                            break;
                        }
                        uint pz_1 = computeWant_0(d_4, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S15 = pz_1 & lenMask_0;
                        uint az_1 = (_S15 >> lgSpan_0) * 32U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 447
                        half2 _S16 = stgGet_0(_S10 + az_1 - c_1 * 16U * 32U, kernelContext_2);



                        outi_0[d_4] = _S16;

#line 443
                        d_4 = d_4 + 1U;

#line 443
                    }

#line 438
                    break;
                }

#line 438
                break;
            }

#line 438
            break;
        }

#line 437
        c_1 = c_1 + 1U;

#line 437
    }

#line 437
    j_1 = 0U;

#line 456
    for(;;)
    {

#line 456
        if(j_1 < 16U)
        {
        }
        else
        {

#line 456
            break;
        }

#line 456
        (*re_3)[j_1] = outr_0[j_1];

#line 456
        (*im_3)[j_1] = outi_0[j_1];

#line 456
        j_1 = j_1 + 1U;

#line 456
    }
    return;
}


#line 357
void dft2s_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4, uint o_0)
{
    half2 ar_1 = (*re_4)[o_0];

#line 359
    half2 ai_1 = (*im_4)[o_0];

#line 359
    uint _S17 = o_0 + 1U;

#line 359
    half2 br_1 = (*re_4)[_S17];

#line 359
    half2 bi_1 = (*im_4)[_S17];
    (*re_4)[o_0] = (*re_4)[o_0] + (*re_4)[_S17];

#line 360
    (*im_4)[o_0] = ai_1 + bi_1;
    (*re_4)[_S17] = ar_1 - br_1;

#line 361
    (*im_4)[_S17] = ai_1 - bi_1;
    return;
}


#line 459
void innermostS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5)
{

#line 459
    uint b_3 = 0U;

#line 464
    for(;;)
    {

#line 464
        if(b_3 < 8U)
        {
        }
        else
        {

#line 464
            break;
        }

#line 464
        dft2s_0(re_5, im_5, b_3 * 2U);

#line 464
        b_3 = b_3 + 1U;

#line 464
    }
    return;
}


#line 723
uint lgOf_0(uint i_4)
{

#line 723
    uint _S18;

#line 723
    if(i_4 < 2U)
    {

#line 723
        _S18 = 4U;

#line 723
    }
    else
    {

#line 723
        _S18 = 1U;

#line 723
    }

#line 723
    return _S18;
}


#line 725
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 729
    uint lg_1 = lgOf_0(1U);

#line 729
    uint lg_2 = lgOf_0(0U);

#line 734
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 412
half2 mag2s_0(half2 re_6, half2 im_6)
{

#line 412
    return re_6 * re_6 + im_6 * im_6;
}


#line 1142
uint mfShflXor_0(uint v_1, uint s_0, KernelContext_0 thread* kernelContext_3)
{

#line 1142
    uint _S19 = (simd_shuffle((v_1), ushort((int((kernelContext_3->_S7) ^ s_0)))));

#line 1142
    return _S19;
}


#line 42 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S20 = ((MF_C16_RAW));

#line 45
    return _S20;
}


#line 293 "mm_512_fusedTierB_c16t4.slang"
float2 c16Bound_0(float2 v_2, float energy_0)
{

#line 47 "twiddle.slang"
    uint _S21 = mfC16RawFlag_0();

#line 295 "mm_512_fusedTierB_c16t4.slang"
    if((1U - _S21) == 0U)
    {

#line 295
        return v_2;
    }

#line 296
    float m_1 = length(v_2);
    float b_4 = m_1 * 1.00146484375 + 0.00686962902545929 * sqrt(energy_0);

#line 297
    float2 _S22;
    if(m_1 > 0.0)
    {

#line 298
        _S22 = v_2 * float2((b_4 / m_1)) ;

#line 298
    }
    else
    {

#line 298
        _S22 = float2(b_4, 0.0);

#line 298
    }

#line 298
    return _S22;
}


#line 1145
void peakTwoWave_0(uint pairA_0, uint pairB_0, uint tid_0, const array<half2, int(16)> thread* re_7, const array<half2, int(16)> thread* im_7, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{
    uint m_2;

#line 1147
    bool _S23;

#line 1147
    bool _S24;

    uint _S25 = slotToIndex_0(tid_0 * 16U) - winStart_2;
    uint _S26 = winEnd_2 - winStart_2;

#line 1157
    half2 _S27 = half2(float2(0.0) );
    half2 _S28 = half2(float2(0.015625) );

#line 1158
    uint i_5 = 0U;

#line 1158
    half2 en_0 = _S27;

#line 1158
    uint ovAcc_0 = 0U;

#line 1158
    uint kA_0 = 0U;

#line 1158
    uint kB_0 = 0U;



    for(;;)
    {

#line 1162
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1162
            break;
        }
        half2 mg_0 = mag2s_0((*re_7)[i_5], (*im_7)[i_5]);
        half2 sr_0 = (*re_7)[i_5] * _S28;

#line 1165
        half2 si_0 = (*im_7)[i_5] * _S28;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);
        if((_S25 + slotToIndex_0(i_5)) < _S26)
        {

#line 1167
            m_2 = (uint(as_type<ushort>(mg_0[0U])) & 65535U) | (uint(as_type<ushort>(mg_0[1U])) << 16U);

#line 1167
        }
        else
        {

#line 1167
            m_2 = 0U;

#line 1167
        }

#line 1173
        uint ovAcc_1 = ovAcc_0 | (((((uint(as_type<ushort>((*re_7)[i_5].x)) & 65535U) | (uint(as_type<ushort>((*re_7)[i_5].y)) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>((*im_7)[i_5].x)) & 65535U) | (uint(as_type<ushort>((*im_7)[i_5].y)) << 16U)) & 2080406528U) + 67109888U));


        uint _S29 = 15U - i_5;

#line 1176
        uint _S30 = max(kA_0, (m_2 << 16U) | _S29);
        uint _S31 = max(kB_0, (m_2 & 4294901760U) | _S29);

#line 1162
        i_5 = i_5 + 1U;

#line 1162
        en_0 = en_1;

#line 1162
        ovAcc_0 = ovAcc_1;

#line 1162
        kA_0 = _S30;

#line 1162
        kB_0 = _S31;

#line 1162
    }

#line 1181
    if((ovAcc_0 & 32768U) != 0U)
    {

#line 1181
        kA_0 = max(kA_0, 2080374799U);

#line 1181
    }
    if((ovAcc_0 & 2147483648U) != 0U)
    {

#line 1182
        kB_0 = max(kB_0, 2080374799U);

#line 1182
    }


    uint _S32 = (4095U - tid_0) << 4U;

#line 1185
    uint kA_1 = kA_0 | _S32;
    uint kB_1 = kB_0 | _S32;

#line 1186
    uint _S33 = mfShflXor_0(kA_1, 1U, kernelContext_4);

    uint _S34 = max(kA_1, _S33);

#line 1188
    uint _S35 = mfShflXor_0(kB_1, 1U, kernelContext_4);
    uint _S36 = max(kB_1, _S35);

#line 1189
    uint _S37 = mfShflXor_0((uint(as_type<ushort>(en_0[0U])) & 65535U) | (uint(as_type<ushort>(en_0[1U])) << 16U), 1U, kernelContext_4);
    half2 en_2 = en_0 + half2(as_type<half>(ushort(_S37 & 65535U)), as_type<half>(ushort((_S37 >> 16U) & 65535U)));

#line 1190
    uint _S38 = mfShflXor_0(_S34, 2U, kernelContext_4);

#line 1188
    uint _S39 = max(_S34, _S38);

#line 1188
    uint _S40 = mfShflXor_0(_S36, 2U, kernelContext_4);
    uint _S41 = max(_S36, _S40);

#line 1189
    uint _S42 = mfShflXor_0((uint(as_type<ushort>(en_2[0U])) & 65535U) | (uint(as_type<ushort>(en_2[1U])) << 16U), 2U, kernelContext_4);
    half2 en_3 = en_2 + half2(as_type<half>(ushort(_S42 & 65535U)), as_type<half>(ushort((_S42 >> 16U) & 65535U)));

#line 1190
    uint _S43 = mfShflXor_0(_S39, 4U, kernelContext_4);

#line 1188
    uint _S44 = max(_S39, _S43);

#line 1188
    uint _S45 = mfShflXor_0(_S41, 4U, kernelContext_4);
    uint _S46 = max(_S41, _S45);

#line 1189
    uint _S47 = mfShflXor_0((uint(as_type<ushort>(en_3[0U])) & 65535U) | (uint(as_type<ushort>(en_3[1U])) << 16U), 4U, kernelContext_4);
    half2 en_4 = en_3 + half2(as_type<half>(ushort(_S47 & 65535U)), as_type<half>(ushort((_S47 >> 16U) & 65535U)));

#line 1190
    uint _S48 = mfShflXor_0(_S44, 8U, kernelContext_4);

#line 1188
    uint _S49 = max(_S44, _S48);

#line 1188
    uint _S50 = mfShflXor_0(_S46, 8U, kernelContext_4);
    uint _S51 = max(_S46, _S50);

#line 1189
    uint _S52 = mfShflXor_0((uint(as_type<ushort>(en_4[0U])) & 65535U) | (uint(as_type<ushort>(en_4[1U])) << 16U), 8U, kernelContext_4);
    half2 en_5 = en_4 + half2(as_type<half>(ushort(_S52 & 65535U)), as_type<half>(ushort((_S52 >> 16U) & 65535U)));

#line 1190
    uint _S53 = mfShflXor_0(_S49, 16U, kernelContext_4);

#line 1188
    uint _S54 = max(_S49, _S53);

#line 1188
    uint _S55 = mfShflXor_0(_S51, 16U, kernelContext_4);
    uint _S56 = max(_S51, _S55);

#line 1189
    uint _S57 = mfShflXor_0((uint(as_type<ushort>(en_5[0U])) & 65535U) | (uint(as_type<ushort>(en_5[1U])) << 16U), 16U, kernelContext_4);
    half2 en_6 = en_5 + half2(as_type<half>(ushort(_S57 & 65535U)), as_type<half>(ushort((_S57 >> 16U) & 65535U)));



    float enA_0 = float(en_6.x) * 8.0;

#line 1194
    float enB_0 = float(en_6.y) * 8.0;
    uint slotA_0 = 65535U - (_S54 & 65535U);

#line 1195
    uint slotB_0 = 65535U - (_S56 & 65535U);

#line 1201
    uint _S58 = _S54 >> 16U;

#line 1201
    bool infA_0 = _S58 >= 31744U;

#line 1201
    uint _S59 = _S56 >> 16U;

#line 1201
    bool infB_0 = _S59 >= 31744U;

#line 1201
    bool hitA_0;



    if(infA_0)
    {

#line 1205
        hitA_0 = true;

#line 1205
    }
    else
    {

#line 1205
        hitA_0 = (as_type<half>((ushort)((_S58)))) > (as_type<float>((thrBits_1)));

#line 1205
    }

#line 1205
    bool hitB_0;
    if(infB_0)
    {

#line 1206
        hitB_0 = true;

#line 1206
    }
    else
    {

#line 1206
        hitB_0 = (as_type<half>((ushort)((_S59)))) > (as_type<float>((thrBits_1)));

#line 1206
    }

#line 1214
    uint _S60 = slotA_0 >> 4U;

#line 1214
    uint _S61 = slotA_0 & 15U;

#line 1214
    uint _S62 = slotB_0 >> 4U;

#line 1214
    uint _S63 = slotB_0 & 15U;
    thread array<float, int(2)> vA_0;

#line 1215
    thread array<float, int(2)> vB_0;
    vB_0[int(1)] = 0.0;

#line 1216
    vB_0[int(0)] = 0.0;

#line 1216
    vA_0[int(1)] = 0.0;

#line 1216
    vA_0[int(0)] = 0.0;

#line 1216
    for(;;)
    {

#line 1216
        for(;;)
        {

#line 1217
            for(;;)
            {

#line 1217
                for(;;)
                {

#line 1217
                    for(;;)
                    {

#line 1218
                        for(;;)
                        {

#line 1219
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1219
                            m_2 = 0U;
                            for(;;)
                            {

#line 1220
                                if(m_2 < 16U)
                                {
                                }
                                else
                                {

#line 1220
                                    break;
                                }

#line 1221
                                (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + m_2 * 32U + tid_0] = (uint(as_type<ushort>((*re_7)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*re_7)[m_2].y)) << 16U);

#line 1220
                                m_2 = m_2 + 1U;

#line 1220
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            bool _S64 = tid_0 == 0U;

#line 1223
                            _S23 = _S64;

#line 1223
                            if(_S64)
                            {

#line 1224
                                if(_S61 >= 0U)
                                {

#line 1224
                                    _S24 = _S61 < 16U;

#line 1224
                                }
                                else
                                {

#line 1224
                                    _S24 = false;

#line 1224
                                }

#line 1224
                                if(_S24)
                                {

#line 1225
                                    vA_0[0U] = (as_type<half>((ushort)(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + _S61 * 32U + _S60]))));

#line 1224
                                }

                                if(_S63 >= 0U)
                                {

#line 1226
                                    _S24 = _S63 < 16U;

#line 1226
                                }
                                else
                                {

#line 1226
                                    _S24 = false;

#line 1226
                                }

#line 1226
                                if(_S24)
                                {

#line 1227
                                    vB_0[0U] = (as_type<half>((ushort)((((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + _S63 * 32U + _S62]) >> 16U))));

#line 1226
                                }

#line 1223
                            }

#line 1218
                            break;
                        }

#line 1218
                        break;
                    }

#line 1218
                    break;
                }

#line 1217
                break;
            }

#line 1217
            break;
        }

#line 1217
        for(;;)
        {

#line 1217
            for(;;)
            {

#line 1217
                for(;;)
                {

#line 1217
                    for(;;)
                    {

#line 1218
                        for(;;)
                        {

#line 1219
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1219
                            m_2 = 0U;
                            for(;;)
                            {

#line 1220
                                if(m_2 < 16U)
                                {
                                }
                                else
                                {

#line 1220
                                    break;
                                }

#line 1221
                                (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + m_2 * 32U + tid_0] = (uint(as_type<ushort>((*im_7)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*im_7)[m_2].y)) << 16U);

#line 1220
                                m_2 = m_2 + 1U;

#line 1220
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            if(_S23)
                            {

#line 1224
                                if(_S61 >= 0U)
                                {

#line 1224
                                    _S24 = _S61 < 16U;

#line 1224
                                }
                                else
                                {

#line 1224
                                    _S24 = false;

#line 1224
                                }

#line 1224
                                if(_S24)
                                {

#line 1225
                                    vA_0[1U] = (as_type<half>((ushort)(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + _S61 * 32U + _S60]))));

#line 1224
                                }

                                if(_S63 >= 0U)
                                {

#line 1226
                                    _S24 = _S63 < 16U;

#line 1226
                                }
                                else
                                {

#line 1226
                                    _S24 = false;

#line 1226
                                }

#line 1226
                                if(_S24)
                                {

#line 1227
                                    vB_0[1U] = (as_type<half>((ushort)((((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + _S63 * 32U + _S62]) >> 16U))));

#line 1226
                                }

#line 1223
                            }

#line 1218
                            break;
                        }

#line 1218
                        break;
                    }

#line 1218
                    break;
                }

#line 1217
                break;
            }

#line 1217
            break;
        }

#line 1217
        break;
    }

#line 1231
    if(_S23)
    {

#line 1231
        _S24 = pairA_0 != 4294967295U;

#line 1231
    }
    else
    {

#line 1231
        _S24 = false;

#line 1231
    }

#line 1231
    int _S65;

#line 1231
    float2 _S66;

#line 1231
    if(_S24)
    {

#line 1232
        int device* _S67 = peakIdx_0+pairA_0;

#line 1232
        if(hitA_0)
        {

#line 1232
            _S65 = int(slotToIndex_0(slotA_0));

#line 1232
        }
        else
        {

#line 1232
            _S65 = int(-1);

#line 1232
        }

#line 1232
        *_S67 = _S65;

#line 1232
        packed_float2 device* _S68 = peakVal_0+pairA_0;
        if(infA_0)
        {

#line 1233
            _S66 = float2(3.40282306073709653e+38, 0.0);

#line 1233
        }
        else
        {

#line 1234
            if(hitA_0)
            {

#line 1234
                float2 _S69 = c16Bound_0(float2(vA_0[int(0)], vA_0[int(1)]), enA_0);

#line 1234
                _S66 = _S69;

#line 1234
            }
            else
            {

#line 1234
                _S66 = float2(0.0, 0.0);

#line 1234
            }

#line 1233
        }

#line 1233
        *_S68 = packed_float2(_S66) ;

#line 1231
    }

#line 1236
    if(_S23)
    {

#line 1236
        hitA_0 = pairB_0 != 4294967295U;

#line 1236
    }
    else
    {

#line 1236
        hitA_0 = false;

#line 1236
    }

#line 1236
    if(hitA_0)
    {

#line 1237
        int device* _S70 = peakIdx_0+pairB_0;

#line 1237
        if(hitB_0)
        {

#line 1237
            _S65 = int(slotToIndex_0(slotB_0));

#line 1237
        }
        else
        {

#line 1237
            _S65 = int(-1);

#line 1237
        }

#line 1237
        *_S70 = _S65;

#line 1237
        packed_float2 device* _S71 = peakVal_0+pairB_0;
        if(infB_0)
        {

#line 1238
            _S66 = float2(3.40282306073709653e+38, 0.0);

#line 1238
        }
        else
        {

#line 1239
            if(hitB_0)
            {

#line 1239
                float2 _S72 = c16Bound_0(float2(vB_0[int(0)], vB_0[int(1)]), enB_0);

#line 1239
                _S66 = _S72;

#line 1239
            }
            else
            {

#line 1239
                _S66 = float2(0.0, 0.0);

#line 1239
            }

#line 1238
        }

#line 1238
        *_S71 = packed_float2(_S66) ;

#line 1236
    }

#line 1241
    return;
}




void filterTwo_0(uint pairA_1, uint pairB_1, uint tA_0, uint tB_0, uint tid_1, const array<half2, int(16)> thread* dreg_0, uint device* tmpl_0, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_2, KernelContext_0 thread* kernelContext_5)
{

    uint _S73;

#line 1250
    uint k2_1;

#line 1250
    float cr_0;

#line 1250
    float ci_0;

#line 1250
    uint _S74;

    thread array<half2, int(16)> re_8;

#line 1252
    thread array<half2, int(16)> im_8;

#line 1252
    uint n2_0 = 0U;
    for(;;)
    {

#line 1253
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 1253
            break;
        }

#line 1254
        uint _S75 = 32U * n2_0;

#line 1254
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 512U + tid_1 + _S75);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 512U + tid_1 + _S75);
        half _S76 = (*dreg_0)[n2_0].x;
        half _S77 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S76, _S76), half2(_S77, _S77), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_8[n2_0], &im_8[n2_0]);

#line 1253
        n2_0 = n2_0 + 1U;

#line 1253
    }

#line 1253
    for(;;)
    {

#line 1253
        for(;;)
        {

#line 1263
            for(;;)
            {

                uint lgTB_0 = firstbithigh_0(32U);

#line 1266
                _S73 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(512U);
                uint blk_2 = tid_1 >> lgTB_0;
                uint lane_2 = tid_1 & 31U;

                dft16s_0(&re_8, &im_8);

#line 1287
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 512.0);
                float _S78 = tw_0.x;

#line 1288
                float _S79 = tw_0.y;

#line 1288
                k2_1 = 0U;

#line 1288
                cr_0 = 1.0;

#line 1288
                ci_0 = 0.0;

                for(;;)
                {

#line 1290
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 1290
                        break;
                    }

#line 1291
                    cmulw_0(&re_8[k2_1], &im_8[k2_1], half(cr_0), half(ci_0));
                    float nr_0 = cr_0 * _S78 - ci_0 * _S79;
                    float _S80 = cr_0 * _S79 + ci_0 * _S78;

#line 1290
                    k2_1 = k2_1 + 1U;

#line 1290
                    cr_0 = nr_0;

#line 1290
                    ci_0 = _S80;

#line 1290
                }

#line 1298
                uint per_2 = 16U / max(32U, 1U);
                uint _S81 = max(2U, 1U);

#line 1299
                _S74 = _S81;
                uint blk2_2 = tid_1 / _S81;

#line 1300
                uint lane2_2 = tid_1 % _S81;

#line 1300
                exchangeS_0(&re_8, &im_8, lgLn_0, lgTB_0, 32U, 512U, blk_2, lane_2, per_2, _S81, 32U, blk2_2, lane2_2, kernelContext_5);

#line 1263
                break;
            }

#line 1263
            break;
        }

#line 1263
        for(;;)
        {

#line 1263
            for(;;)
            {

                uint lgTB_1 = firstbithigh_0(2U);

                uint blk_3 = tid_1 >> lgTB_1;
                uint lane_3 = tid_1 & 1U;

                dft16s_0(&re_8, &im_8);

#line 1287
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 32.0);
                float _S82 = tw_1.x;

#line 1288
                float _S83 = tw_1.y;

#line 1288
                k2_1 = 0U;

#line 1288
                cr_0 = 1.0;

#line 1288
                ci_0 = 0.0;

                for(;;)
                {

#line 1290
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 1290
                        break;
                    }

#line 1291
                    cmulw_0(&re_8[k2_1], &im_8[k2_1], half(cr_0), half(ci_0));
                    float nr_1 = cr_0 * _S82 - ci_0 * _S83;
                    float _S84 = cr_0 * _S83 + ci_0 * _S82;

#line 1290
                    k2_1 = k2_1 + 1U;

#line 1290
                    cr_0 = nr_1;

#line 1290
                    ci_0 = _S84;

#line 1290
                }

#line 1298
                uint per_3 = 16U / _S74;
                uint _S85 = max(0U, 1U);
                uint blk2_3 = tid_1 / _S85;

#line 1300
                uint lane2_3 = tid_1 % _S85;

#line 1300
                exchangeS_0(&re_8, &im_8, _S73, lgTB_1, 2U, 32U, blk_3, lane_3, per_3, _S85, 2U, blk2_3, lane2_3, kernelContext_5);

#line 1263
                break;
            }

#line 1263
            break;
        }

#line 1263
        break;
    }

#line 1303
    innermostS_0(&re_8, &im_8);

#line 1303
    thread array<half2, int(16)> _S86 = re_8;

#line 1303
    thread array<half2, int(16)> _S87 = im_8;

#line 1303
    peakTwoWave_0(pairA_1, pairB_1, tid_1, &_S86, &_S87, peakIdx_1, peakVal_1, winStart_3, winEnd_3, thrBits_2, kernelContext_5);

#line 1349
    return;
}


void filterPair_0(uint pair_0, uint tid_2, uint device* data_0, uint device* tmpl_1, int device* peakIdx_2, packed_float2 device* peakVal_2, uint ntmpl_1, uint winStart_4, uint winEnd_4, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, KernelContext_0 thread* kernelContext_6)
{

#line 1353
    thread uint _S88 = winStart_4;

#line 1353
    thread uint _S89 = winEnd_4;

#line 1359
    kernelContext_6->_tid_0 = tid_2;

#line 1379
    uint tiles_0 = (ntmpl_1 + 4U - 1U) / 4U;
    uint slots_0 = binsize_1 * tiles_0;
    bool slotOk_0 = pair_0 < slots_0;

#line 1381
    uint q_1;
    if(slotOk_0)
    {

#line 1382
        q_1 = pair_0;

#line 1382
    }
    else
    {

#line 1382
        q_1 = slots_0 - 1U;

#line 1382
    }
    uint d_5 = q_1 / tiles_0;

#line 1383
    uint t0_0 = (q_1 - d_5 * tiles_0) * 4U;
    uint _S90 = d_5 * ntmpl_1 + t0_0;
    rowWindow_0(d_5, &_S88, &_S89);

#line 1396
    thread array<half2, int(16)> dreg_1;

#line 1396
    uint n2_1 = 0U;

    for(;;)
    {

#line 1398
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1398
            break;
        }

#line 1399
        dreg_1[n2_1] = dload_0(data_0, d_5 * 512U + tid_2 + 32U * n2_1);

#line 1398
        n2_1 = n2_1 + 1U;

#line 1398
    }

#line 1398
    uint k_0 = 0U;

#line 1406
    for(;;)
    {

#line 1406
        if(k_0 < 4U)
        {
        }
        else
        {

#line 1406
            break;
        }

#line 1406
        bool okA_0;
        if(slotOk_0)
        {

#line 1407
            okA_0 = (t0_0 + k_0) < ntmpl_1;

#line 1407
        }
        else
        {

#line 1407
            okA_0 = false;

#line 1407
        }

#line 1407
        bool okB_0;

#line 1407
        if(slotOk_0)
        {

#line 1407
            okB_0 = (t0_0 + k_0 + 1U) < ntmpl_1;

#line 1407
        }
        else
        {

#line 1407
            okB_0 = false;

#line 1407
        }
        if(okA_0)
        {

#line 1408
            q_1 = _S90 + k_0;

#line 1408
        }
        else
        {

#line 1408
            q_1 = 4294967295U;

#line 1408
        }

#line 1408
        if(okB_0)
        {

#line 1408
            n2_1 = _S90 + k_0 + 1U;

#line 1408
        }
        else
        {

#line 1408
            n2_1 = 4294967295U;

#line 1408
        }
        uint _S91 = t0_0 + k_0;

#line 1409
        uint _S92 = ntmpl_1 - 1U;

#line 1409
        uint _S93 = min(_S91, _S92);

#line 1409
        uint _S94 = min(_S91 + 1U, _S92);

#line 1409
        thread array<half2, int(16)> _S95 = dreg_1;

#line 1409
        filterTwo_0(q_1, n2_1, _S93, _S94, tid_2, &_S95, tmpl_1, peakIdx_2, peakVal_2, _S88, _S89, thrBits_3, kernelContext_6);

#line 1406
        k_0 = k_0 + 2U;

#line 1406
    }

#line 1422
    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], uint _builtinWaveLaneIndex_0 [[thread_index_in_simdgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1426
    thread KernelContext_0 kernelContext_7;

#line 1426
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1426
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1426
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1426
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1426
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1426
    threadgroup array<uint, int(512)> stg_1;

#line 1426
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1426
    (&kernelContext_7)->_S7 = _builtinWaveLaneIndex_0;

#line 1443
    uint _pr_0 = gid_0.x;

#line 1443
    uint _t_0 = lid_0.x;
    (&kernelContext_7)->_stgBase_0 = 0U;

#line 1444
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);

#line 1452
    return;
}
