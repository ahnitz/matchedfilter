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


#line 197 "mm_1024_fusedTierB_c16p4t4.slang"
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

#line 209
    return cload_0(b_1, i_1);
}


#line 333
void cmulconjs_0(half2 ar_0, half2 ai_0, half2 br_0, half2 bi_0, half2 thread* pr_0, half2 thread* pi_0)
{
    *pr_0 = ar_0 * br_0 + ai_0 * bi_0;
    *pi_0 = ai_0 * br_0 - ar_0 * bi_0;
    return;
}


#line 345
void r4s_0(array<half2, int(16)> thread* re_0, array<half2, int(16)> thread* im_0, uint a_0, uint b_2, uint c_0, uint d_1)
{
    half2 t0r_0 = (*re_0)[a_0] + (*re_0)[c_0];

#line 347
    half2 t0i_0 = (*im_0)[a_0] + (*im_0)[c_0];
    half2 t1r_0 = (*re_0)[a_0] - (*re_0)[c_0];

#line 348
    half2 t1i_0 = (*im_0)[a_0] - (*im_0)[c_0];
    half2 t2r_0 = (*re_0)[b_2] + (*re_0)[d_1];

#line 349
    half2 t2i_0 = (*im_0)[b_2] + (*im_0)[d_1];
    half2 t3r_0 = (*re_0)[b_2] - (*re_0)[d_1];
    half2 j3r_0 = - ((*im_0)[b_2] - (*im_0)[d_1]);
    (*re_0)[a_0] = t0r_0 + t2r_0;

#line 352
    (*im_0)[a_0] = t0i_0 + t2i_0;
    (*re_0)[b_2] = t1r_0 + j3r_0;

#line 353
    (*im_0)[b_2] = t1i_0 + t3r_0;
    (*re_0)[c_0] = t0r_0 - t2r_0;

#line 354
    (*im_0)[c_0] = t0i_0 - t2i_0;
    (*re_0)[d_1] = t1r_0 - j3r_0;

#line 355
    (*im_0)[d_1] = t1i_0 - t3r_0;
    return;
}


#line 345
void r4s_1(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint a_1, uint b_3, uint c_1, uint d_2)
{
    half2 t0r_1 = (*re_1)[a_1] + (*re_1)[c_1];

#line 347
    half2 t0i_1 = (*im_1)[a_1] + (*im_1)[c_1];
    half2 t1r_1 = (*re_1)[a_1] - (*re_1)[c_1];

#line 348
    half2 t1i_1 = (*im_1)[a_1] - (*im_1)[c_1];
    half2 t2r_1 = (*re_1)[b_3] + (*re_1)[d_2];

#line 349
    half2 t2i_1 = (*im_1)[b_3] + (*im_1)[d_2];
    half2 t3r_1 = (*re_1)[b_3] - (*re_1)[d_2];
    half2 j3r_1 = - ((*im_1)[b_3] - (*im_1)[d_2]);
    (*re_1)[a_1] = t0r_1 + t2r_1;

#line 352
    (*im_1)[a_1] = t0i_1 + t2i_1;
    (*re_1)[b_3] = t1r_1 + j3r_1;

#line 353
    (*im_1)[b_3] = t1i_1 + t3r_1;
    (*re_1)[c_1] = t0r_1 - t2r_1;

#line 354
    (*im_1)[c_1] = t0i_1 - t2i_1;
    (*re_1)[d_2] = t1r_1 - j3r_1;

#line 355
    (*im_1)[d_2] = t1i_1 - t3r_1;
    return;
}


#line 324
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 324
    half2 _S2 = half2(wr_0) ;

#line 324
    half2 _S3 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S3 + *xi_0 * _S2;
    *xr_0 = *xr_0 * _S2 - *xi_0 * _S3;

#line 328
    *xi_0 = ni_0;
    return;
}


#line 358
void swap2_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2, uint p_1, uint q_0)
{

    half2 t_0 = (*re_2)[p_1];

#line 361
    (*re_2)[p_1] = (*re_2)[q_0];

#line 361
    (*re_2)[q_0] = t_0;
    half2 t_1 = (*im_2)[p_1];

#line 362
    (*im_2)[p_1] = (*im_2)[q_0];

#line 362
    (*im_2)[q_0] = t_1;
    return;
}


#line 358
void swap2_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint p_2, uint q_1)
{

    half2 t_2 = (*re_3)[p_2];

#line 361
    (*re_3)[p_2] = (*re_3)[q_1];

#line 361
    (*re_3)[q_1] = t_2;
    half2 t_3 = (*im_3)[p_2];

#line 362
    (*im_3)[p_2] = (*im_3)[q_1];

#line 362
    (*im_3)[q_1] = t_3;
    return;
}


#line 396
void dft16s_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4)
{

#line 396
    uint n1_0 = 0U;

    for(;;)
    {

#line 398
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 398
            break;
        }

#line 398
        r4s_0(re_4, im_4, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 398
        n1_0 = n1_0 + 1U;

#line 398
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

#line 409
    uint k2_0 = 0U;
    for(;;)
    {

#line 410
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 410
            break;
        }

#line 411
        uint _S4 = 4U * k2_0;

#line 411
        r4s_0(re_4, im_4, _S4, _S4 + 1U, _S4 + 2U, _S4 + 3U);

#line 410
        k2_0 = k2_0 + 1U;

#line 410
    }

    swap2_0(re_4, im_4, 1U, 4U);

#line 412
    swap2_0(re_4, im_4, 2U, 8U);

#line 412
    swap2_0(re_4, im_4, 3U, 12U);
    swap2_0(re_4, im_4, 6U, 9U);

#line 413
    swap2_0(re_4, im_4, 7U, 13U);

#line 413
    swap2_0(re_4, im_4, 11U, 14U);
    return;
}


#line 72 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 272 "mm_1024_fusedTierB_c16p4t4.slang"
uint computeWant_0(uint d_3, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S5 = max(TB_0, 1U);

#line 274
    uint j_0 = d_3 / _S5;

#line 274
    uint m_0 = d_3 % _S5;

#line 274
    uint _S6;
    if(TB_0 <= 16U)
    {

#line 275
        _S6 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 275
    }
    else
    {

#line 275
        _S6 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_3;

#line 275
    }

#line 275
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


#line 248 "mm_1024_fusedTierB_c16p4t4.slang"
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


#line 248
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 248
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 248
    return;
}


#line 249
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 249
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 434
void exchangeS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{
    uint j_1;

    thread array<half2, int(16)> outr_0;

#line 438
    thread array<half2, int(16)> outi_0;

#line 438
    uint z_0 = 0U;
    for(;;)
    {

#line 439
        if(z_0 < 16U)
        {
        }
        else
        {

#line 439
            break;
        }

#line 439
        half2 _S7 = half2(float2(0.0f) );

#line 439
        outr_0[z_0] = _S7;

#line 439
        outi_0[z_0] = _S7;

#line 439
        z_0 = z_0 + 1U;

#line 439
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S8 = p0_0 & lenMask_0;
    uint _S9 = (_S8 >> lgSpan_0) * 64U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S8 & spanMask_0);

#line 444
    uint c_2 = 0U;
    for(;;)
    {

#line 445
        if(c_2 < 1U)
        {
        }
        else
        {

#line 445
            break;
        }

#line 445
        for(;;)
        {

#line 445
            for(;;)
            {

#line 446
                for(;;)
                {

#line 447
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 447
                    j_1 = 0U;
                    for(;;)
                    {

#line 448
                        if(j_1 < 16U)
                        {
                        }
                        else
                        {

#line 448
                            break;
                        }

#line 449
                        uint _S10 = j_1 * 64U + kernelContext_2->_tid_0;

#line 449
                        stgPut_0(_S10, (*re_5)[c_2 * 16U + j_1], kernelContext_2);

#line 448
                        j_1 = j_1 + 1U;

#line 448
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 450
                    uint d_4 = 0U;
                    for(;;)
                    {

#line 451
                        if(d_4 < 16U)
                        {
                        }
                        else
                        {

#line 451
                            break;
                        }
                        uint pz_0 = computeWant_0(d_4, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S11 = pz_0 & lenMask_0;
                        uint az_0 = (_S11 >> lgSpan_0) * 64U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S11 & spanMask_0);

#line 455
                        half2 _S12 = stgGet_0(_S9 + az_0 - c_2 * 16U * 64U, kernelContext_2);



                        outr_0[d_4] = _S12;

#line 451
                        d_4 = d_4 + 1U;

#line 451
                    }

#line 446
                    break;
                }

#line 446
                break;
            }

#line 446
            for(;;)
            {

#line 446
                for(;;)
                {

#line 447
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 447
                    uint j_2 = 0U;
                    for(;;)
                    {

#line 448
                        if(j_2 < 16U)
                        {
                        }
                        else
                        {

#line 448
                            break;
                        }

#line 449
                        uint _S13 = j_2 * 64U + kernelContext_2->_tid_0;

#line 449
                        stgPut_0(_S13, (*im_5)[c_2 * 16U + j_2], kernelContext_2);

#line 448
                        j_2 = j_2 + 1U;

#line 448
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 450
                    uint d_5 = 0U;
                    for(;;)
                    {

#line 451
                        if(d_5 < 16U)
                        {
                        }
                        else
                        {

#line 451
                            break;
                        }
                        uint pz_1 = computeWant_0(d_5, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S14 = pz_1 & lenMask_0;
                        uint az_1 = (_S14 >> lgSpan_0) * 64U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);

#line 455
                        half2 _S15 = stgGet_0(_S9 + az_1 - c_2 * 16U * 64U, kernelContext_2);



                        outi_0[d_5] = _S15;

#line 451
                        d_5 = d_5 + 1U;

#line 451
                    }

#line 446
                    break;
                }

#line 446
                break;
            }

#line 446
            break;
        }

#line 445
        c_2 = c_2 + 1U;

#line 445
    }

#line 445
    j_1 = 0U;

#line 464
    for(;;)
    {

#line 464
        if(j_1 < 16U)
        {
        }
        else
        {

#line 464
            break;
        }

#line 464
        (*re_5)[j_1] = outr_0[j_1];

#line 464
        (*im_5)[j_1] = outi_0[j_1];

#line 464
        j_1 = j_1 + 1U;

#line 464
    }
    return;
}


#line 372
void dft4s_0(array<half2, int(16)> thread* re_6, array<half2, int(16)> thread* im_6, uint o_0)
{
    uint _S16 = o_0 + 1U;

#line 374
    uint _S17 = o_0 + 2U;

#line 374
    r4s_1(re_6, im_6, o_0, _S16, _S17, o_0 + 3U);
    swap2_1(re_6, im_6, _S16, _S17);
    return;
}


#line 467
void innermostS_0(array<half2, int(16)> thread* re_7, array<half2, int(16)> thread* im_7)
{

#line 467
    uint b_4 = 0U;



    for(;;)
    {

#line 471
        if(b_4 < 4U)
        {
        }
        else
        {

#line 471
            break;
        }

#line 471
        dft4s_0(re_7, im_7, b_4 * 4U);

#line 471
        b_4 = b_4 + 1U;

#line 471
    }

    return;
}


#line 760
uint lgOf_0(uint i_4)
{

#line 760
    uint _S18;

#line 760
    if(i_4 < 2U)
    {

#line 760
        _S18 = 4U;

#line 760
    }
    else
    {

#line 760
        _S18 = 1U;

#line 760
    }

#line 760
    return _S18;
}


#line 762
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 766
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 766
    uint lg_2 = lgOf_0(1U);

#line 766
    uint lg_3 = lgOf_0(0U);

#line 771
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 420
half2 mag2s_0(half2 re_8, half2 im_8)
{

#line 420
    return re_8 * re_8 + im_8 * im_8;
}


#line 54 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S19 = ((MF_C16_RAW));

#line 57
    return _S19;
}


#line 301 "mm_1024_fusedTierB_c16p4t4.slang"
float2 c16Bound_0(float2 v_1, float energy_0)
{

#line 59 "twiddle.slang"
    uint _S20 = mfC16RawFlag_0();

#line 303 "mm_1024_fusedTierB_c16p4t4.slang"
    if((1U - _S20) == 0U)
    {

#line 303
        return v_1;
    }

#line 304
    float m_1 = length(v_1);
    float b_5 = m_1 * 1.00146484375f + 0.00755659164860845f * sqrt(energy_0);

#line 305
    float2 _S21;
    if(m_1 > 0.0f)
    {

#line 306
        _S21 = v_1 * float2((b_5 / m_1)) ;

#line 306
    }
    else
    {

#line 306
        _S21 = float2(b_5, 0.0f);

#line 306
    }

#line 306
    return _S21;
}



float pairSum_0(uint tid_0, float v_2, KernelContext_0 thread* kernelContext_3)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0 + tid_0] = (as_type<uint>((v_2)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 315
    uint k_0 = 0U;

#line 315
    float t_4 = 0.0f;

    for(;;)
    {

#line 317
        if(k_0 < 64U)
        {
        }
        else
        {

#line 317
            break;
        }

#line 317
        float t_5 = t_4 + (as_type<float>(((*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0 + k_0])));

#line 317
        k_0 = k_0 + 1U;

#line 317
        t_4 = t_5;

#line 317
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_4;
}


#line 1229
void peakLane_0(uint pair_0, uint tid_1, uint lane_2, const array<half2, int(16)> thread* magv_0, const array<half2, int(16)> thread* re_9, const array<half2, int(16)> thread* im_9, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint thrBits_1, float energy_1, KernelContext_0 thread* kernelContext_4)
{
    bool _S22;

    threadgroup_barrier(mem_flags::mem_threadgroup);
    bool _S23 = tid_1 == 0U;

#line 1234
    if(_S23)
    {

#line 1234
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 1234
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 1234
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1244
    half2 _S24 = half2(float2(0.0f) );

#line 1244
    half2 bestH_0 = _S24;

#line 1244
    uint i_5 = 0U;

#line 1244
    half2 poison_0 = _S24;
    for(;;)
    {

#line 1245
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1245
            break;
        }

#line 1245
        half2 _S25 = max(bestH_0, (*magv_0)[i_5]);

#line 1245
        half2 poison_1 = poison_0 + (*magv_0)[i_5] * _S24;

#line 1245
        uint i_6 = i_5 + 1U;

#line 1245
        bestH_0 = _S25;

#line 1245
        i_5 = i_6;

#line 1245
        poison_0 = poison_1;

#line 1245
    }
    bool _S26 = lane_2 == 0U;

#line 1246
    half _S27;

#line 1246
    if(_S26)
    {

#line 1246
        _S27 = poison_0.x;

#line 1246
    }
    else
    {

#line 1246
        _S27 = poison_0.y;

#line 1246
    }
    if(isnan(float(_S27)))
    {

#line 1247
        i_5 = 2139095040U;

#line 1247
    }
    else
    {

#line 1247
        if(_S26)
        {

#line 1247
            _S27 = bestH_0.x;

#line 1247
        }
        else
        {

#line 1247
            _S27 = bestH_0.y;

#line 1247
        }

#line 1247
        i_5 = (as_type<uint>((float(_S27))));

#line 1247
    }

#line 1247
    uint _S28 = max(thrBits_1, i_5);

#line 1252
    if(_S28 > thrBits_1)
    {

#line 1252
        uint _S29 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), _S28, memory_order_relaxed);

#line 1252
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1254
    uint winner_0 = 4294967295U;

#line 1254
    i_5 = 0U;


    for(;;)
    {

#line 1257
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1257
            break;
        }

#line 1258
        if(_S26)
        {

#line 1258
            _S27 = (*magv_0)[i_5].x;

#line 1258
        }
        else
        {

#line 1258
            _S27 = (*magv_0)[i_5].y;

#line 1258
        }

#line 1258
        uint _S30 = min((as_type<uint>((float(_S27)))), 2139095040U);
        if(_S30 > thrBits_1)
        {

#line 1259
            _S22 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0]) == _S30;

#line 1259
        }
        else
        {

#line 1259
            _S22 = false;

#line 1259
        }

#line 1259
        if(_S22)
        {

#line 1259
            winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 1259
        }

#line 1257
        i_5 = i_5 + 1U;

#line 1257
    }

#line 1267
    if(winner_0 != 4294967295U)
    {

#line 1267
        uint _S31 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 1267
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1269
    i_5 = 0U;
    for(;;)
    {

#line 1270
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1270
            break;
        }

#line 1271
        if(pair_0 != 4294967295U)
        {

#line 1271
            _S22 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == (tid_1 * 16U + i_5);

#line 1271
        }
        else
        {

#line 1271
            _S22 = false;

#line 1271
        }

#line 1271
        if(_S22)
        {

#line 1272
            *(peakIdx_0+pair_0) = int(slotToIndex_0(tid_1 * 16U + i_5));

#line 1272
            packed_float2 device* _S32 = peakVal_0+pair_0;
            if(_S26)
            {

#line 1273
                _S27 = (*re_9)[i_5].x;

#line 1273
            }
            else
            {

#line 1273
                _S27 = (*re_9)[i_5].y;

#line 1273
            }

#line 1273
            float _S33 = float(_S27);

#line 1273
            half _S34;
            if(_S26)
            {

#line 1274
                _S34 = (*im_9)[i_5].x;

#line 1274
            }
            else
            {

#line 1274
                _S34 = (*im_9)[i_5].y;

#line 1274
            }

#line 1273
            float2 _S35 = c16Bound_0(float2(_S33, float(_S34)), energy_1);

#line 1273
            *_S32 = packed_float2(_S35) ;

#line 1271
        }

#line 1270
        i_5 = i_5 + 1U;

#line 1270
    }

#line 1277
    if(pair_0 != 4294967295U)
    {

#line 1277
        _S22 = _S23;

#line 1277
    }
    else
    {

#line 1277
        _S22 = false;

#line 1277
    }

#line 1277
    if(_S22)
    {

#line 1277
        _S22 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1277
    }
    else
    {

#line 1277
        _S22 = false;

#line 1277
    }

#line 1277
    if(_S22)
    {

#line 1278
        *(peakIdx_0+pair_0) = int(-1);

#line 1278
        *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1277
    }



    return;
}


#line 1487
void filterTwo_0(uint pairA_0, uint pairB_0, uint tA_0, uint tB_0, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* tmpl_0, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_2, KernelContext_0 thread* kernelContext_5)
{

    uint _S36;

#line 1490
    uint k2_1;

#line 1490
    float cr_0;

#line 1490
    float ci_0;

#line 1490
    uint _S37;

    thread array<half2, int(16)> re_10;

#line 1492
    thread array<half2, int(16)> im_10;

#line 1492
    uint n2_0 = 0U;
    for(;;)
    {

#line 1493
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 1493
            break;
        }

#line 1494
        uint _S38 = 64U * n2_0;

#line 1494
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 1024U + tid_2 + _S38);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 1024U + tid_2 + _S38);
        half _S39 = (*dreg_0)[n2_0].x;
        half _S40 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S39, _S39), half2(_S40, _S40), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_10[n2_0], &im_10[n2_0]);

#line 1493
        n2_0 = n2_0 + 1U;

#line 1493
    }

#line 1493
    for(;;)
    {

#line 1493
        for(;;)
        {

#line 1503
            for(;;)
            {

                uint lgTB_0 = firstbithigh_0(64U);

#line 1506
                _S36 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(1024U);
                uint blk_2 = tid_2 >> lgTB_0;
                uint lane_3 = tid_2 & 63U;

                dft16s_0(&re_10, &im_10);

#line 1527
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 1024.0f);
                float _S41 = tw_0.x;

#line 1528
                float _S42 = tw_0.y;

#line 1528
                k2_1 = 0U;

#line 1528
                cr_0 = 1.0f;

#line 1528
                ci_0 = 0.0f;

                for(;;)
                {

#line 1530
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 1530
                        break;
                    }

#line 1531
                    cmulw_0(&re_10[k2_1], &im_10[k2_1], half(cr_0), half(ci_0));
                    float nr_0 = cr_0 * _S41 - ci_0 * _S42;
                    float _S43 = cr_0 * _S42 + ci_0 * _S41;

#line 1530
                    k2_1 = k2_1 + 1U;

#line 1530
                    cr_0 = nr_0;

#line 1530
                    ci_0 = _S43;

#line 1530
                }

#line 1538
                uint per_2 = 16U / max(64U, 1U);
                uint _S44 = max(4U, 1U);

#line 1539
                _S37 = _S44;
                uint blk2_2 = tid_2 / _S44;

#line 1540
                uint lane2_2 = tid_2 % _S44;

#line 1540
                exchangeS_0(&re_10, &im_10, lgLn_0, lgTB_0, 64U, 1024U, blk_2, lane_3, per_2, _S44, 64U, blk2_2, lane2_2, kernelContext_5);

#line 1503
                break;
            }

#line 1503
            break;
        }

#line 1503
        for(;;)
        {

#line 1503
            for(;;)
            {

                uint lgTB_1 = firstbithigh_0(4U);

                uint blk_3 = tid_2 >> lgTB_1;
                uint lane_4 = tid_2 & 3U;

                dft16s_0(&re_10, &im_10);

#line 1527
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_4) / 64.0f);
                float _S45 = tw_1.x;

#line 1528
                float _S46 = tw_1.y;

#line 1528
                k2_1 = 0U;

#line 1528
                cr_0 = 1.0f;

#line 1528
                ci_0 = 0.0f;

                for(;;)
                {

#line 1530
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 1530
                        break;
                    }

#line 1531
                    cmulw_0(&re_10[k2_1], &im_10[k2_1], half(cr_0), half(ci_0));
                    float nr_1 = cr_0 * _S45 - ci_0 * _S46;
                    float _S47 = cr_0 * _S46 + ci_0 * _S45;

#line 1530
                    k2_1 = k2_1 + 1U;

#line 1530
                    cr_0 = nr_1;

#line 1530
                    ci_0 = _S47;

#line 1530
                }

#line 1538
                uint per_3 = 16U / _S37;
                uint _S48 = max(0U, 1U);
                uint blk2_3 = tid_2 / _S48;

#line 1540
                uint lane2_3 = tid_2 % _S48;

#line 1540
                exchangeS_0(&re_10, &im_10, _S36, lgTB_1, 4U, 64U, blk_3, lane_4, per_3, _S48, 4U, blk2_3, lane2_3, kernelContext_5);

#line 1503
                break;
            }

#line 1503
            break;
        }

#line 1503
        break;
    }

#line 1543
    innermostS_0(&re_10, &im_10);

#line 1567
    thread array<half2, int(16)> magv_1;



    half2 _S49 = half2(float2(0.0f) );
    half2 _S50 = half2(float2(0.015625f) );

#line 1572
    uint i_7 = 0U;

#line 1572
    half2 en_0 = _S49;
    for(;;)
    {

#line 1573
        if(i_7 < 16U)
        {
        }
        else
        {

#line 1573
            break;
        }

#line 1574
        uint idx_0 = slotToIndex_0(tid_2 * 16U + i_7);

#line 1574
        bool live_0;
        if(idx_0 >= winStart_3)
        {

#line 1575
            live_0 = idx_0 < winEnd_3;

#line 1575
        }
        else
        {

#line 1575
            live_0 = false;

#line 1575
        }
        half2 mg_0 = mag2s_0(re_10[i_7], im_10[i_7]);
        half2 sr_0 = re_10[i_7] * _S50;

#line 1577
        half2 si_0 = im_10[i_7] * _S50;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1578
        half2 _S51;
        if(live_0)
        {

#line 1579
            _S51 = mg_0;

#line 1579
        }
        else
        {

#line 1579
            _S51 = _S49;

#line 1579
        }

#line 1579
        magv_1[i_7] = _S51;

#line 1585
        if(live_0)
        {
            uint ov_0 = ((((uint(as_type<ushort>(re_10[i_7][0U])) & 65535U) | (uint(as_type<ushort>(re_10[i_7][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(im_10[i_7][0U])) & 65535U) | (uint(as_type<ushort>(im_10[i_7][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1587
            uint _S52 = (uint(as_type<ushort>(magv_1[i_7][0U])) & 65535U) | (uint(as_type<ushort>(magv_1[i_7][1U])) << 16U);

#line 1587
            uint mb_0;

            if((ov_0 & 32768U) != 0U)
            {

#line 1589
                mb_0 = (_S52 & 4294901760U) | 31744U;

#line 1589
            }
            else
            {

#line 1589
                mb_0 = _S52;

#line 1589
            }

#line 1589
            uint mb_1;
            if((ov_0 & 2147483648U) != 0U)
            {

#line 1590
                mb_1 = (mb_0 & 65535U) | 2080374784U;

#line 1590
            }
            else
            {

#line 1590
                mb_1 = mb_0;

#line 1590
            }
            magv_1[i_7] = half2(as_type<half>(ushort(mb_1 & 65535U)), as_type<half>(ushort((mb_1 >> 16U) & 65535U)));

#line 1585
        }

#line 1573
        i_7 = i_7 + 1U;

#line 1573
        en_0 = en_1;

#line 1573
    }

#line 1594
    float eB_0 = float(en_0.y) * 4096.0f;

#line 1594
    float _S53 = pairSum_0(tid_2, float(en_0.x) * 4096.0f, kernelContext_5);
    float eA_0 = _S53 / 1024.0f;

#line 1595
    float _S54 = pairSum_0(tid_2, eB_0, kernelContext_5);
    float eB_1 = _S54 / 1024.0f;

#line 1596
    thread array<half2, int(16)> _S55 = magv_1;

#line 1596
    thread array<half2, int(16)> _S56 = re_10;

#line 1596
    thread array<half2, int(16)> _S57 = im_10;

#line 1596
    peakLane_0(pairA_0, tid_2, 0U, &_S55, &_S56, &_S57, peakIdx_1, peakVal_1, winStart_3, winEnd_3, thrBits_2, eA_0, kernelContext_5);

#line 1596
    thread array<half2, int(16)> _S58 = magv_1;

#line 1596
    thread array<half2, int(16)> _S59 = re_10;

#line 1596
    thread array<half2, int(16)> _S60 = im_10;

#line 1596
    peakLane_0(pairB_0, tid_2, 1U, &_S58, &_S59, &_S60, peakIdx_1, peakVal_1, winStart_3, winEnd_3, thrBits_2, eB_1, kernelContext_5);



    return;
}


void filterPair_0(uint pair_1, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_2, packed_float2 device* peakVal_2, uint ntmpl_1, uint winStart_4, uint winEnd_4, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, KernelContext_0 thread* kernelContext_6)
{

#line 1604
    thread uint _S61 = winStart_4;

#line 1604
    thread uint _S62 = winEnd_4;

#line 1610
    kernelContext_6->_tid_0 = tid_3;

#line 1630
    uint tiles_0 = (ntmpl_1 + 4U - 1U) / 4U;
    uint slots_0 = binsize_1 * tiles_0;
    bool slotOk_0 = pair_1 < slots_0;

#line 1632
    uint q_2;
    if(slotOk_0)
    {

#line 1633
        q_2 = pair_1;

#line 1633
    }
    else
    {

#line 1633
        q_2 = slots_0 - 1U;

#line 1633
    }
    uint d_6 = q_2 / tiles_0;

#line 1634
    uint t0_0 = (q_2 - d_6 * tiles_0) * 4U;
    uint _S63 = d_6 * ntmpl_1 + t0_0;
    rowWindow_0(d_6, &_S61, &_S62);

#line 1647
    thread array<half2, int(16)> dreg_1;

#line 1647
    uint n2_1 = 0U;

    for(;;)
    {

#line 1649
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1649
            break;
        }

#line 1650
        dreg_1[n2_1] = dload_0(data_0, d_6 * 1024U + tid_3 + 64U * n2_1);

#line 1649
        n2_1 = n2_1 + 1U;

#line 1649
    }

#line 1649
    uint k_1 = 0U;

#line 1657
    for(;;)
    {

#line 1657
        if(k_1 < 4U)
        {
        }
        else
        {

#line 1657
            break;
        }

#line 1657
        bool okA_0;
        if(slotOk_0)
        {

#line 1658
            okA_0 = (t0_0 + k_1) < ntmpl_1;

#line 1658
        }
        else
        {

#line 1658
            okA_0 = false;

#line 1658
        }

#line 1658
        bool okB_0;

#line 1658
        if(slotOk_0)
        {

#line 1658
            okB_0 = (t0_0 + k_1 + 1U) < ntmpl_1;

#line 1658
        }
        else
        {

#line 1658
            okB_0 = false;

#line 1658
        }
        if(okA_0)
        {

#line 1659
            q_2 = _S63 + k_1;

#line 1659
        }
        else
        {

#line 1659
            q_2 = 4294967295U;

#line 1659
        }

#line 1659
        if(okB_0)
        {

#line 1659
            n2_1 = _S63 + k_1 + 1U;

#line 1659
        }
        else
        {

#line 1659
            n2_1 = 4294967295U;

#line 1659
        }
        uint _S64 = t0_0 + k_1;

#line 1660
        uint _S65 = ntmpl_1 - 1U;

#line 1660
        uint _S66 = min(_S64, _S65);

#line 1660
        uint _S67 = min(_S64 + 1U, _S65);

#line 1660
        thread array<half2, int(16)> _S68 = dreg_1;

#line 1660
        filterTwo_0(q_2, n2_1, _S66, _S67, tid_3, &_S68, tmpl_1, peakIdx_2, peakVal_2, _S61, _S62, thrBits_3, kernelContext_6);

#line 1657
        k_1 = k_1 + 2U;

#line 1657
    }

#line 1673
    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1677
    thread KernelContext_0 kernelContext_7;

#line 1677
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1677
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1677
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1677
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1677
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1677
    threadgroup array<uint, int(4096)> stg_1;

#line 1677
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1697
    uint _S69 = lid_0.x;

#line 1697
    uint _sub_0 = _S69 / 64U;
    uint _pr_0 = gid_0.x * 4U + _sub_0;

#line 1698
    uint _t_0 = _S69 % 64U;
    (&kernelContext_7)->_stgBase_0 = _sub_0 * 1024U;

#line 1699
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);



    return;
}
