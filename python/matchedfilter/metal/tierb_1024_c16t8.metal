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


#line 194 "mm_1024_fusedTierB_c16t8.slang"
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


#line 342
void r4s_1(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint a_1, uint b_3, uint c_1, uint d_2)
{
    half2 t0r_1 = (*re_1)[a_1] + (*re_1)[c_1];

#line 344
    half2 t0i_1 = (*im_1)[a_1] + (*im_1)[c_1];
    half2 t1r_1 = (*re_1)[a_1] - (*re_1)[c_1];

#line 345
    half2 t1i_1 = (*im_1)[a_1] - (*im_1)[c_1];
    half2 t2r_1 = (*re_1)[b_3] + (*re_1)[d_2];

#line 346
    half2 t2i_1 = (*im_1)[b_3] + (*im_1)[d_2];
    half2 t3r_1 = (*re_1)[b_3] - (*re_1)[d_2];
    half2 j3r_1 = - ((*im_1)[b_3] - (*im_1)[d_2]);
    (*re_1)[a_1] = t0r_1 + t2r_1;

#line 349
    (*im_1)[a_1] = t0i_1 + t2i_1;
    (*re_1)[b_3] = t1r_1 + j3r_1;

#line 350
    (*im_1)[b_3] = t1i_1 + t3r_1;
    (*re_1)[c_1] = t0r_1 - t2r_1;

#line 351
    (*im_1)[c_1] = t0i_1 - t2i_1;
    (*re_1)[d_2] = t1r_1 - j3r_1;

#line 352
    (*im_1)[d_2] = t1i_1 - t3r_1;
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
void swap2_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2, uint p_1, uint q_0)
{

    half2 t_0 = (*re_2)[p_1];

#line 358
    (*re_2)[p_1] = (*re_2)[q_0];

#line 358
    (*re_2)[q_0] = t_0;
    half2 t_1 = (*im_2)[p_1];

#line 359
    (*im_2)[p_1] = (*im_2)[q_0];

#line 359
    (*im_2)[q_0] = t_1;
    return;
}


#line 355
void swap2_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint p_2, uint q_1)
{

    half2 t_2 = (*re_3)[p_2];

#line 358
    (*re_3)[p_2] = (*re_3)[q_1];

#line 358
    (*re_3)[q_1] = t_2;
    half2 t_3 = (*im_3)[p_2];

#line 359
    (*im_3)[p_2] = (*im_3)[q_1];

#line 359
    (*im_3)[q_1] = t_3;
    return;
}


#line 393
void dft16s_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4)
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
        r4s_0(re_4, im_4, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 395
        n1_0 = n1_0 + 1U;

#line 395
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
        r4s_0(re_4, im_4, _S4, _S4 + 1U, _S4 + 2U, _S4 + 3U);

#line 407
        k2_0 = k2_0 + 1U;

#line 407
    }

    swap2_0(re_4, im_4, 1U, 4U);

#line 409
    swap2_0(re_4, im_4, 2U, 8U);

#line 409
    swap2_0(re_4, im_4, 3U, 12U);
    swap2_0(re_4, im_4, 6U, 9U);

#line 410
    swap2_0(re_4, im_4, 7U, 13U);

#line 410
    swap2_0(re_4, im_4, 11U, 14U);
    return;
}


#line 74 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 269 "mm_1024_fusedTierB_c16t8.slang"
uint computeWant_0(uint d_3, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S5 = max(TB_0, 1U);

#line 271
    uint j_0 = d_3 / _S5;

#line 271
    uint m_0 = d_3 % _S5;

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
        _S6 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_3;

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


#line 245 "mm_1024_fusedTierB_c16t8.slang"
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


#line 245
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
void exchangeS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
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
        half2 _S7 = half2(float2(0.0f) );

#line 436
        outr_0[z_0] = _S7;

#line 436
        outi_0[z_0] = _S7;

#line 436
        z_0 = z_0 + 1U;

#line 436
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S8 = p0_0 & lenMask_0;
    uint _S9 = (_S8 >> lgSpan_0) * 64U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S8 & spanMask_0);

#line 441
    uint c_2 = 0U;
    for(;;)
    {

#line 442
        if(c_2 < 1U)
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
                        uint _S10 = j_1 * 64U + kernelContext_2->_tid_0;

#line 446
                        stgPut_0(_S10, (*re_5)[c_2 * 16U + j_1], kernelContext_2);

#line 445
                        j_1 = j_1 + 1U;

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
                        uint pz_0 = computeWant_0(d_4, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S11 = pz_0 & lenMask_0;
                        uint az_0 = (_S11 >> lgSpan_0) * 64U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S11 & spanMask_0);

#line 452
                        half2 _S12 = stgGet_0(_S9 + az_0 - c_2 * 16U * 64U, kernelContext_2);



                        outr_0[d_4] = _S12;

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
                        uint _S13 = j_2 * 64U + kernelContext_2->_tid_0;

#line 446
                        stgPut_0(_S13, (*im_5)[c_2 * 16U + j_2], kernelContext_2);

#line 445
                        j_2 = j_2 + 1U;

#line 445
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 447
                    uint d_5 = 0U;
                    for(;;)
                    {

#line 448
                        if(d_5 < 16U)
                        {
                        }
                        else
                        {

#line 448
                            break;
                        }
                        uint pz_1 = computeWant_0(d_5, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S14 = pz_1 & lenMask_0;
                        uint az_1 = (_S14 >> lgSpan_0) * 64U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);

#line 452
                        half2 _S15 = stgGet_0(_S9 + az_1 - c_2 * 16U * 64U, kernelContext_2);



                        outi_0[d_5] = _S15;

#line 448
                        d_5 = d_5 + 1U;

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
        c_2 = c_2 + 1U;

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
        (*re_5)[j_1] = outr_0[j_1];

#line 461
        (*im_5)[j_1] = outi_0[j_1];

#line 461
        j_1 = j_1 + 1U;

#line 461
    }
    return;
}


#line 369
void dft4s_0(array<half2, int(16)> thread* re_6, array<half2, int(16)> thread* im_6, uint o_0)
{
    uint _S16 = o_0 + 1U;

#line 371
    uint _S17 = o_0 + 2U;

#line 371
    r4s_1(re_6, im_6, o_0, _S16, _S17, o_0 + 3U);
    swap2_1(re_6, im_6, _S16, _S17);
    return;
}


#line 464
void innermostS_0(array<half2, int(16)> thread* re_7, array<half2, int(16)> thread* im_7)
{

#line 464
    uint b_4 = 0U;



    for(;;)
    {

#line 468
        if(b_4 < 4U)
        {
        }
        else
        {

#line 468
            break;
        }

#line 468
        dft4s_0(re_7, im_7, b_4 * 4U);

#line 468
        b_4 = b_4 + 1U;

#line 468
    }

    return;
}


#line 757
uint lgOf_0(uint i_4)
{

#line 757
    uint _S18;

#line 757
    if(i_4 < 2U)
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
    return _S18;
}


#line 759
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 763
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 763
    uint lg_2 = lgOf_0(1U);

#line 763
    uint lg_3 = lgOf_0(0U);

#line 768
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 417
half2 mag2s_0(half2 re_8, half2 im_8)
{

#line 417
    return re_8 * re_8 + im_8 * im_8;
}


#line 56 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S19 = ((MF_C16_RAW));

#line 59
    return _S19;
}


#line 298 "mm_1024_fusedTierB_c16t8.slang"
float2 c16Bound_0(float2 v_1, float energy_0)
{

#line 61 "twiddle.slang"
    uint _S20 = mfC16RawFlag_0();

#line 300 "mm_1024_fusedTierB_c16t8.slang"
    if((1U - _S20) == 0U)
    {

#line 300
        return v_1;
    }

#line 301
    float m_1 = length(v_1);
    float b_5 = m_1 * 1.00146484375f + 0.00755659164860845f * sqrt(energy_0);

#line 302
    float2 _S21;
    if(m_1 > 0.0f)
    {

#line 303
        _S21 = v_1 * float2((b_5 / m_1)) ;

#line 303
    }
    else
    {

#line 303
        _S21 = float2(b_5, 0.0f);

#line 303
    }

#line 303
    return _S21;
}



float pairSum_0(uint tid_0, float v_2, KernelContext_0 thread* kernelContext_3)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0 + tid_0] = (as_type<uint>((v_2)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 312
    uint k_0 = 0U;

#line 312
    float t_4 = 0.0f;

    for(;;)
    {

#line 314
        if(k_0 < 64U)
        {
        }
        else
        {

#line 314
            break;
        }

#line 314
        float t_5 = t_4 + (as_type<float>(((*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0 + k_0])));

#line 314
        k_0 = k_0 + 1U;

#line 314
        t_4 = t_5;

#line 314
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_4;
}


#line 1225
void peakLane_0(uint pair_0, uint tid_1, uint lane_2, const array<half2, int(16)> thread* magv_0, const array<half2, int(16)> thread* re_9, const array<half2, int(16)> thread* im_9, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint thrBits_1, float energy_1, KernelContext_0 thread* kernelContext_4)
{


    threadgroup_barrier(mem_flags::mem_threadgroup);
    bool _S22 = tid_1 == 0U;

#line 1230
    if(_S22)
    {

#line 1230
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 1230
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 1230
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1240
    half2 _S23 = half2(float2(0.0f) );

#line 1240
    half2 bestH_0 = _S23;

#line 1240
    uint i_5 = 0U;

#line 1240
    half2 poison_0 = _S23;
    for(;;)
    {

#line 1241
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1241
            break;
        }

#line 1241
        half2 _S24 = max(bestH_0, (*magv_0)[i_5]);

#line 1241
        half2 poison_1 = poison_0 + (*magv_0)[i_5] * _S23;

#line 1241
        uint i_6 = i_5 + 1U;

#line 1241
        bestH_0 = _S24;

#line 1241
        i_5 = i_6;

#line 1241
        poison_0 = poison_1;

#line 1241
    }
    bool _S25 = lane_2 == 0U;

#line 1242
    half _S26;

#line 1242
    if(_S25)
    {

#line 1242
        _S26 = poison_0.x;

#line 1242
    }
    else
    {

#line 1242
        _S26 = poison_0.y;

#line 1242
    }
    if(isnan(float(_S26)))
    {

#line 1243
        i_5 = 2139095040U;

#line 1243
    }
    else
    {

#line 1243
        if(_S25)
        {

#line 1243
            _S26 = bestH_0.x;

#line 1243
        }
        else
        {

#line 1243
            _S26 = bestH_0.y;

#line 1243
        }

#line 1243
        i_5 = (as_type<uint>((float(_S26))));

#line 1243
    }

    uint wm_0 = simd_max(max(thrBits_1, i_5));
    bool _S27 = simd_is_first();

#line 1246
    bool _S28;

#line 1246
    if(_S27)
    {

#line 1246
        _S28 = wm_0 > thrBits_1;

#line 1246
    }
    else
    {

#line 1246
        _S28 = false;

#line 1246
    }

#line 1246
    if(_S28)
    {

#line 1246
        uint _S29 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1246
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1250
    uint winner_0 = 4294967295U;

#line 1250
    i_5 = 0U;


    for(;;)
    {

#line 1253
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1253
            break;
        }

#line 1254
        if(_S25)
        {

#line 1254
            _S26 = (*magv_0)[i_5].x;

#line 1254
        }
        else
        {

#line 1254
            _S26 = (*magv_0)[i_5].y;

#line 1254
        }

#line 1254
        uint _S30 = min((as_type<uint>((float(_S26)))), 2139095040U);
        if(_S30 > thrBits_1)
        {

#line 1255
            _S28 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0]) == _S30;

#line 1255
        }
        else
        {

#line 1255
            _S28 = false;

#line 1255
        }

#line 1255
        if(_S28)
        {

#line 1255
            winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 1255
        }

#line 1253
        i_5 = i_5 + 1U;

#line 1253
    }

#line 1259
    uint waveWinner_0 = simd_min(winner_0);
    bool _S31 = simd_is_first();

#line 1260
    if(_S31)
    {

#line 1260
        _S28 = waveWinner_0 != 4294967295U;

#line 1260
    }
    else
    {

#line 1260
        _S28 = false;

#line 1260
    }

#line 1260
    if(_S28)
    {

#line 1261
        uint _S32 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1260
    }

#line 1265
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1265
    i_5 = 0U;
    for(;;)
    {

#line 1266
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1266
            break;
        }

#line 1267
        if(pair_0 != 4294967295U)
        {

#line 1267
            _S28 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == (tid_1 * 16U + i_5);

#line 1267
        }
        else
        {

#line 1267
            _S28 = false;

#line 1267
        }

#line 1267
        if(_S28)
        {

#line 1268
            *(peakIdx_0+pair_0) = int(slotToIndex_0(tid_1 * 16U + i_5));

#line 1268
            packed_float2 device* _S33 = peakVal_0+pair_0;
            if(_S25)
            {

#line 1269
                _S26 = (*re_9)[i_5].x;

#line 1269
            }
            else
            {

#line 1269
                _S26 = (*re_9)[i_5].y;

#line 1269
            }

#line 1269
            float _S34 = float(_S26);

#line 1269
            half _S35;
            if(_S25)
            {

#line 1270
                _S35 = (*im_9)[i_5].x;

#line 1270
            }
            else
            {

#line 1270
                _S35 = (*im_9)[i_5].y;

#line 1270
            }

#line 1269
            float2 _S36 = c16Bound_0(float2(_S34, float(_S35)), energy_1);

#line 1269
            *_S33 = packed_float2(_S36) ;

#line 1267
        }

#line 1266
        i_5 = i_5 + 1U;

#line 1266
    }

#line 1273
    if(pair_0 != 4294967295U)
    {

#line 1273
        _S28 = _S22;

#line 1273
    }
    else
    {

#line 1273
        _S28 = false;

#line 1273
    }

#line 1273
    if(_S28)
    {

#line 1273
        _S28 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1273
    }
    else
    {

#line 1273
        _S28 = false;

#line 1273
    }

#line 1273
    if(_S28)
    {

#line 1274
        *(peakIdx_0+pair_0) = int(-1);

#line 1274
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1273
    }



    return;
}


#line 1483
void filterTwo_0(uint pairA_0, uint pairB_0, uint tA_0, uint tB_0, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* tmpl_0, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_2, KernelContext_0 thread* kernelContext_5)
{

    uint _S37;

#line 1486
    uint k2_1;

#line 1486
    float cr_0;

#line 1486
    float ci_0;

#line 1486
    uint _S38;

    thread array<half2, int(16)> re_10;

#line 1488
    thread array<half2, int(16)> im_10;

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
        uint _S39 = 64U * n2_0;

#line 1490
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 1024U + tid_2 + _S39);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 1024U + tid_2 + _S39);
        half _S40 = (*dreg_0)[n2_0].x;
        half _S41 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S40, _S40), half2(_S41, _S41), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_10[n2_0], &im_10[n2_0]);

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

                uint lgTB_0 = firstbithigh_0(64U);

#line 1502
                _S37 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(1024U);
                uint blk_2 = tid_2 >> lgTB_0;
                uint lane_3 = tid_2 & 63U;

                dft16s_0(&re_10, &im_10);

#line 1523
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 1024.0f);
                float _S42 = tw_0.x;

#line 1524
                float _S43 = tw_0.y;

#line 1524
                k2_1 = 0U;

#line 1524
                cr_0 = 1.0f;

#line 1524
                ci_0 = 0.0f;

                for(;;)
                {

#line 1526
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 1526
                        break;
                    }

#line 1527
                    cmulw_0(&re_10[k2_1], &im_10[k2_1], half(cr_0), half(ci_0));
                    float nr_0 = cr_0 * _S42 - ci_0 * _S43;
                    float _S44 = cr_0 * _S43 + ci_0 * _S42;

#line 1526
                    k2_1 = k2_1 + 1U;

#line 1526
                    cr_0 = nr_0;

#line 1526
                    ci_0 = _S44;

#line 1526
                }

#line 1534
                uint per_2 = 16U / max(64U, 1U);
                uint _S45 = max(4U, 1U);

#line 1535
                _S38 = _S45;
                uint blk2_2 = tid_2 / _S45;

#line 1536
                uint lane2_2 = tid_2 % _S45;

#line 1536
                exchangeS_0(&re_10, &im_10, lgLn_0, lgTB_0, 64U, 1024U, blk_2, lane_3, per_2, _S45, 64U, blk2_2, lane2_2, kernelContext_5);

#line 1499
                break;
            }

#line 1499
            break;
        }

#line 1499
        for(;;)
        {

#line 1499
            for(;;)
            {

                uint lgTB_1 = firstbithigh_0(4U);

                uint blk_3 = tid_2 >> lgTB_1;
                uint lane_4 = tid_2 & 3U;

                dft16s_0(&re_10, &im_10);

#line 1523
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_4) / 64.0f);
                float _S46 = tw_1.x;

#line 1524
                float _S47 = tw_1.y;

#line 1524
                k2_1 = 0U;

#line 1524
                cr_0 = 1.0f;

#line 1524
                ci_0 = 0.0f;

                for(;;)
                {

#line 1526
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 1526
                        break;
                    }

#line 1527
                    cmulw_0(&re_10[k2_1], &im_10[k2_1], half(cr_0), half(ci_0));
                    float nr_1 = cr_0 * _S46 - ci_0 * _S47;
                    float _S48 = cr_0 * _S47 + ci_0 * _S46;

#line 1526
                    k2_1 = k2_1 + 1U;

#line 1526
                    cr_0 = nr_1;

#line 1526
                    ci_0 = _S48;

#line 1526
                }

#line 1534
                uint per_3 = 16U / _S38;
                uint _S49 = max(0U, 1U);
                uint blk2_3 = tid_2 / _S49;

#line 1536
                uint lane2_3 = tid_2 % _S49;

#line 1536
                exchangeS_0(&re_10, &im_10, _S37, lgTB_1, 4U, 64U, blk_3, lane_4, per_3, _S49, 4U, blk2_3, lane2_3, kernelContext_5);

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
    innermostS_0(&re_10, &im_10);

#line 1563
    thread array<half2, int(16)> magv_1;



    half2 _S50 = half2(float2(0.0f) );
    half2 _S51 = half2(float2(0.015625f) );

#line 1568
    uint i_7 = 0U;

#line 1568
    half2 en_0 = _S50;
    for(;;)
    {

#line 1569
        if(i_7 < 16U)
        {
        }
        else
        {

#line 1569
            break;
        }

#line 1570
        uint idx_0 = slotToIndex_0(tid_2 * 16U + i_7);

#line 1570
        bool live_0;
        if(idx_0 >= winStart_3)
        {

#line 1571
            live_0 = idx_0 < winEnd_3;

#line 1571
        }
        else
        {

#line 1571
            live_0 = false;

#line 1571
        }
        half2 mg_0 = mag2s_0(re_10[i_7], im_10[i_7]);
        half2 sr_0 = re_10[i_7] * _S51;

#line 1573
        half2 si_0 = im_10[i_7] * _S51;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1574
        half2 _S52;
        if(live_0)
        {

#line 1575
            _S52 = mg_0;

#line 1575
        }
        else
        {

#line 1575
            _S52 = _S50;

#line 1575
        }

#line 1575
        magv_1[i_7] = _S52;

#line 1581
        if(live_0)
        {
            uint ov_0 = ((((uint(as_type<ushort>(re_10[i_7][0U])) & 65535U) | (uint(as_type<ushort>(re_10[i_7][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(im_10[i_7][0U])) & 65535U) | (uint(as_type<ushort>(im_10[i_7][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1583
            uint _S53 = (uint(as_type<ushort>(magv_1[i_7][0U])) & 65535U) | (uint(as_type<ushort>(magv_1[i_7][1U])) << 16U);

#line 1583
            uint mb_0;

            if((ov_0 & 32768U) != 0U)
            {

#line 1585
                mb_0 = (_S53 & 4294901760U) | 31744U;

#line 1585
            }
            else
            {

#line 1585
                mb_0 = _S53;

#line 1585
            }

#line 1585
            uint mb_1;
            if((ov_0 & 2147483648U) != 0U)
            {

#line 1586
                mb_1 = (mb_0 & 65535U) | 2080374784U;

#line 1586
            }
            else
            {

#line 1586
                mb_1 = mb_0;

#line 1586
            }
            magv_1[i_7] = half2(as_type<half>(ushort(mb_1 & 65535U)), as_type<half>(ushort((mb_1 >> 16U) & 65535U)));

#line 1581
        }

#line 1569
        i_7 = i_7 + 1U;

#line 1569
        en_0 = en_1;

#line 1569
    }

#line 1590
    float eB_0 = float(en_0.y) * 4096.0f;

#line 1590
    float _S54 = pairSum_0(tid_2, float(en_0.x) * 4096.0f, kernelContext_5);
    float eA_0 = _S54 / 1024.0f;

#line 1591
    float _S55 = pairSum_0(tid_2, eB_0, kernelContext_5);
    float eB_1 = _S55 / 1024.0f;

#line 1592
    thread array<half2, int(16)> _S56 = magv_1;

#line 1592
    thread array<half2, int(16)> _S57 = re_10;

#line 1592
    thread array<half2, int(16)> _S58 = im_10;

#line 1592
    peakLane_0(pairA_0, tid_2, 0U, &_S56, &_S57, &_S58, peakIdx_1, peakVal_1, winStart_3, winEnd_3, thrBits_2, eA_0, kernelContext_5);

#line 1592
    thread array<half2, int(16)> _S59 = magv_1;

#line 1592
    thread array<half2, int(16)> _S60 = re_10;

#line 1592
    thread array<half2, int(16)> _S61 = im_10;

#line 1592
    peakLane_0(pairB_0, tid_2, 1U, &_S59, &_S60, &_S61, peakIdx_1, peakVal_1, winStart_3, winEnd_3, thrBits_2, eB_1, kernelContext_5);



    return;
}


void filterPair_0(uint pair_1, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_2, packed_float2 device* peakVal_2, uint ntmpl_1, uint winStart_4, uint winEnd_4, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, KernelContext_0 thread* kernelContext_6)
{

#line 1600
    thread uint _S62 = winStart_4;

#line 1600
    thread uint _S63 = winEnd_4;

#line 1606
    kernelContext_6->_tid_0 = tid_3;

#line 1626
    uint tiles_0 = (ntmpl_1 + 8U - 1U) / 8U;
    uint slots_0 = binsize_1 * tiles_0;
    bool slotOk_0 = pair_1 < slots_0;

#line 1628
    uint q_2;
    if(slotOk_0)
    {

#line 1629
        q_2 = pair_1;

#line 1629
    }
    else
    {

#line 1629
        q_2 = slots_0 - 1U;

#line 1629
    }
    uint d_6 = q_2 / tiles_0;

#line 1630
    uint t0_0 = (q_2 - d_6 * tiles_0) * 8U;
    uint _S64 = d_6 * ntmpl_1 + t0_0;
    rowWindow_0(d_6, &_S62, &_S63);

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
        dreg_1[n2_1] = dload_0(data_0, d_6 * 1024U + tid_3 + 64U * n2_1);

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
        if(k_1 < 8U)
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
            q_2 = _S64 + k_1;

#line 1668
        }
        else
        {

#line 1668
            q_2 = 4294967295U;

#line 1668
        }

#line 1668
        if(okB_0)
        {

#line 1668
            n2_1 = _S64 + k_1 + 1U;

#line 1668
        }
        else
        {

#line 1668
            n2_1 = 4294967295U;

#line 1668
        }
        uint _S65 = t0_0 + k_1;

#line 1669
        uint _S66 = ntmpl_1 - 1U;

#line 1669
        uint _S67 = min(_S65, _S66);

#line 1669
        uint _S68 = min(_S65 + 1U, _S66);

#line 1669
        thread array<half2, int(16)> _S69 = dreg_1;

#line 1669
        filterTwo_0(q_2, n2_1, _S67, _S68, tid_3, &_S69, tmpl_1, peakIdx_2, peakVal_2, _S62, _S63, thrBits_3, kernelContext_6);

#line 1666
        k_1 = k_1 + 2U;

#line 1666
    }

#line 1682
    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1686
    thread KernelContext_0 kernelContext_7;

#line 1686
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1686
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1686
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1686
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1686
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1686
    threadgroup array<uint, int(1024)> stg_1;

#line 1686
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1703
    uint _pr_0 = gid_0.x;

#line 1703
    uint _t_0 = lid_0.x;
    (&kernelContext_7)->_stgBase_0 = 0U;

#line 1704
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);

#line 1712
    return;
}
