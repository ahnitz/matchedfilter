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


#line 191 "mm_1024_fusedTierB_c16p4t2.slang"
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


#line 337
void r4s_1(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint a_1, uint b_3, uint c_1, uint d_2)
{
    half2 t0r_1 = (*re_1)[a_1] + (*re_1)[c_1];

#line 339
    half2 t0i_1 = (*im_1)[a_1] + (*im_1)[c_1];
    half2 t1r_1 = (*re_1)[a_1] - (*re_1)[c_1];

#line 340
    half2 t1i_1 = (*im_1)[a_1] - (*im_1)[c_1];
    half2 t2r_1 = (*re_1)[b_3] + (*re_1)[d_2];

#line 341
    half2 t2i_1 = (*im_1)[b_3] + (*im_1)[d_2];
    half2 t3r_1 = (*re_1)[b_3] - (*re_1)[d_2];
    half2 j3r_1 = - ((*im_1)[b_3] - (*im_1)[d_2]);
    (*re_1)[a_1] = t0r_1 + t2r_1;

#line 344
    (*im_1)[a_1] = t0i_1 + t2i_1;
    (*re_1)[b_3] = t1r_1 + j3r_1;

#line 345
    (*im_1)[b_3] = t1i_1 + t3r_1;
    (*re_1)[c_1] = t0r_1 - t2r_1;

#line 346
    (*im_1)[c_1] = t0i_1 - t2i_1;
    (*re_1)[d_2] = t1r_1 - j3r_1;

#line 347
    (*im_1)[d_2] = t1i_1 - t3r_1;
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
void swap2_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2, uint p_1, uint q_0)
{

    half2 t_0 = (*re_2)[p_1];

#line 353
    (*re_2)[p_1] = (*re_2)[q_0];

#line 353
    (*re_2)[q_0] = t_0;
    half2 t_1 = (*im_2)[p_1];

#line 354
    (*im_2)[p_1] = (*im_2)[q_0];

#line 354
    (*im_2)[q_0] = t_1;
    return;
}


#line 350
void swap2_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint p_2, uint q_1)
{

    half2 t_2 = (*re_3)[p_2];

#line 353
    (*re_3)[p_2] = (*re_3)[q_1];

#line 353
    (*re_3)[q_1] = t_2;
    half2 t_3 = (*im_3)[p_2];

#line 354
    (*im_3)[p_2] = (*im_3)[q_1];

#line 354
    (*im_3)[q_1] = t_3;
    return;
}


#line 388
void dft16s_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4)
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
        r4s_0(re_4, im_4, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 390
        n1_0 = n1_0 + 1U;

#line 390
    }


    cmulw_0(&(*re_4)[int(5)], &(*im_4)[int(5)], 0.923828125, 0.382568359375);
    cmulw_0(&(*re_4)[int(9)], &(*im_4)[int(9)], 0.70703125, 0.70703125);
    cmulw_0(&(*re_4)[int(13)], &(*im_4)[int(13)], 0.382568359375, 0.923828125);
    cmulw_0(&(*re_4)[int(6)], &(*im_4)[int(6)], 0.70703125, 0.70703125);
    cmulw_0(&(*re_4)[int(10)], &(*im_4)[int(10)], 0.0, 1.0);
    cmulw_0(&(*re_4)[int(14)], &(*im_4)[int(14)], -0.70703125, 0.70703125);
    cmulw_0(&(*re_4)[int(7)], &(*im_4)[int(7)], 0.382568359375, 0.923828125);
    cmulw_0(&(*re_4)[int(11)], &(*im_4)[int(11)], -0.70703125, 0.70703125);
    cmulw_0(&(*re_4)[int(15)], &(*im_4)[int(15)], -0.923828125, -0.382568359375);

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
        r4s_0(re_4, im_4, _S4, _S4 + 1U, _S4 + 2U, _S4 + 3U);

#line 402
        k2_0 = k2_0 + 1U;

#line 402
    }

    swap2_0(re_4, im_4, 1U, 4U);

#line 404
    swap2_0(re_4, im_4, 2U, 8U);

#line 404
    swap2_0(re_4, im_4, 3U, 12U);
    swap2_0(re_4, im_4, 6U, 9U);

#line 405
    swap2_0(re_4, im_4, 7U, 13U);

#line 405
    swap2_0(re_4, im_4, 11U, 14U);
    return;
}


#line 64 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 264 "mm_1024_fusedTierB_c16p4t2.slang"
uint computeWant_0(uint d_3, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S5 = max(TB_0, 1U);

#line 266
    uint j_0 = d_3 / _S5;

#line 266
    uint m_0 = d_3 % _S5;

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
        _S6 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_3;

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


#line 240 "mm_1024_fusedTierB_c16p4t2.slang"
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
void exchangeS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
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
        half2 _S7 = half2(float2(0.0) );

#line 431
        outr_0[z_0] = _S7;

#line 431
        outi_0[z_0] = _S7;

#line 431
        z_0 = z_0 + 1U;

#line 431
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S8 = p0_0 & lenMask_0;
    uint _S9 = (_S8 >> lgSpan_0) * 64U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S8 & spanMask_0);

#line 436
    uint c_2 = 0U;
    for(;;)
    {

#line 437
        if(c_2 < 1U)
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
                        uint _S10 = j_1 * 64U + kernelContext_2->_tid_0;

#line 441
                        stgPut_0(_S10, (*re_5)[c_2 * 16U + j_1], kernelContext_2);

#line 440
                        j_1 = j_1 + 1U;

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
                        uint pz_0 = computeWant_0(d_4, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S11 = pz_0 & lenMask_0;
                        uint az_0 = (_S11 >> lgSpan_0) * 64U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S11 & spanMask_0);

#line 447
                        half2 _S12 = stgGet_0(_S9 + az_0 - c_2 * 16U * 64U, kernelContext_2);



                        outr_0[d_4] = _S12;

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
                        uint _S13 = j_2 * 64U + kernelContext_2->_tid_0;

#line 441
                        stgPut_0(_S13, (*im_5)[c_2 * 16U + j_2], kernelContext_2);

#line 440
                        j_2 = j_2 + 1U;

#line 440
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 442
                    uint d_5 = 0U;
                    for(;;)
                    {

#line 443
                        if(d_5 < 16U)
                        {
                        }
                        else
                        {

#line 443
                            break;
                        }
                        uint pz_1 = computeWant_0(d_5, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S14 = pz_1 & lenMask_0;
                        uint az_1 = (_S14 >> lgSpan_0) * 64U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);

#line 447
                        half2 _S15 = stgGet_0(_S9 + az_1 - c_2 * 16U * 64U, kernelContext_2);



                        outi_0[d_5] = _S15;

#line 443
                        d_5 = d_5 + 1U;

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
        c_2 = c_2 + 1U;

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
        (*re_5)[j_1] = outr_0[j_1];

#line 456
        (*im_5)[j_1] = outi_0[j_1];

#line 456
        j_1 = j_1 + 1U;

#line 456
    }
    return;
}


#line 364
void dft4s_0(array<half2, int(16)> thread* re_6, array<half2, int(16)> thread* im_6, uint o_0)
{
    uint _S16 = o_0 + 1U;

#line 366
    uint _S17 = o_0 + 2U;

#line 366
    r4s_1(re_6, im_6, o_0, _S16, _S17, o_0 + 3U);
    swap2_1(re_6, im_6, _S16, _S17);
    return;
}


#line 459
void innermostS_0(array<half2, int(16)> thread* re_7, array<half2, int(16)> thread* im_7)
{

#line 459
    uint b_4 = 0U;



    for(;;)
    {

#line 463
        if(b_4 < 4U)
        {
        }
        else
        {

#line 463
            break;
        }

#line 463
        dft4s_0(re_7, im_7, b_4 * 4U);

#line 463
        b_4 = b_4 + 1U;

#line 463
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


    uint lg_0 = lgOf_0(3U);

    uint x_0 = slot_0 >> lg_0;

#line 729
    uint lg_1 = lgOf_0(2U);

    uint x_1 = x_0 >> lg_1;

#line 729
    uint lg_2 = lgOf_0(1U);

#line 729
    uint lg_3 = lgOf_0(0U);

#line 734
    return (((((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | (x_1 & ((1U << lg_2) - 1U))) << lg_3) | ((x_1 >> lg_2) & ((1U << lg_3) - 1U));
}


#line 412
half2 mag2s_0(half2 re_8, half2 im_8)
{

#line 412
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


#line 293 "mm_1024_fusedTierB_c16p4t2.slang"
float2 c16Bound_0(float2 v_1, float energy_0)
{

#line 52 "twiddle.slang"
    uint _S20 = mfC16RawFlag_0();

#line 295 "mm_1024_fusedTierB_c16p4t2.slang"
    if((1U - _S20) == 0U)
    {

#line 295
        return v_1;
    }

#line 296
    float m_1 = length(v_1);
    float b_5 = m_1 * 1.00146484375 + 0.00755659164860845 * sqrt(energy_0);

#line 297
    float2 _S21;
    if(m_1 > 0.0)
    {

#line 298
        _S21 = v_1 * float2((b_5 / m_1)) ;

#line 298
    }
    else
    {

#line 298
        _S21 = float2(b_5, 0.0);

#line 298
    }

#line 298
    return _S21;
}



float pairSum_0(uint tid_0, float v_2, KernelContext_0 thread* kernelContext_3)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0 + tid_0] = (as_type<uint>((v_2)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 307
    uint k_0 = 0U;

#line 307
    float t_4 = 0.0;

    for(;;)
    {

#line 309
        if(k_0 < 64U)
        {
        }
        else
        {

#line 309
            break;
        }

#line 309
        float t_5 = t_4 + (as_type<float>(((*kernelContext_3->stg_0)[kernelContext_3->_stgBase_0 + k_0])));

#line 309
        k_0 = k_0 + 1U;

#line 309
        t_4 = t_5;

#line 309
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_4;
}


#line 1056
void peakLane_0(uint pair_0, uint tid_1, uint lane_2, const array<half2, int(16)> thread* magv_0, const array<half2, int(16)> thread* re_9, const array<half2, int(16)> thread* im_9, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint thrBits_1, float energy_1, KernelContext_0 thread* kernelContext_4)
{
    bool _S22;

    threadgroup_barrier(mem_flags::mem_threadgroup);
    bool _S23 = tid_1 == 0U;

#line 1061
    if(_S23)
    {

#line 1061
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0] = thrBits_1;

#line 1061
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 1061
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1071
    half2 _S24 = half2(float2(0.0) );

#line 1071
    half2 bestH_0 = _S24;

#line 1071
    uint i_5 = 0U;

#line 1071
    half2 poison_0 = _S24;
    for(;;)
    {

#line 1072
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1072
            break;
        }

#line 1072
        half2 _S25 = max(bestH_0, (*magv_0)[i_5]);

#line 1072
        half2 poison_1 = poison_0 + (*magv_0)[i_5] * _S24;

#line 1072
        uint i_6 = i_5 + 1U;

#line 1072
        bestH_0 = _S25;

#line 1072
        i_5 = i_6;

#line 1072
        poison_0 = poison_1;

#line 1072
    }
    bool _S26 = lane_2 == 0U;

#line 1073
    half _S27;

#line 1073
    if(_S26)
    {

#line 1073
        _S27 = poison_0.x;

#line 1073
    }
    else
    {

#line 1073
        _S27 = poison_0.y;

#line 1073
    }
    if(isnan(float(_S27)))
    {

#line 1074
        i_5 = 2139095040U;

#line 1074
    }
    else
    {

#line 1074
        if(_S26)
        {

#line 1074
            _S27 = bestH_0.x;

#line 1074
        }
        else
        {

#line 1074
            _S27 = bestH_0.y;

#line 1074
        }

#line 1074
        i_5 = (as_type<uint>((float(_S27))));

#line 1074
    }

#line 1074
    uint _S28 = max(thrBits_1, i_5);

#line 1079
    if(_S28 > thrBits_1)
    {

#line 1079
        uint _S29 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), _S28, memory_order_relaxed);

#line 1079
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1081
    uint winner_0 = 4294967295U;

#line 1081
    i_5 = 0U;


    for(;;)
    {

#line 1084
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1084
            break;
        }

#line 1085
        if(_S26)
        {

#line 1085
            _S27 = (*magv_0)[i_5].x;

#line 1085
        }
        else
        {

#line 1085
            _S27 = (*magv_0)[i_5].y;

#line 1085
        }

#line 1085
        uint _S30 = min((as_type<uint>((float(_S27)))), 2139095040U);
        if(_S30 > thrBits_1)
        {

#line 1086
            _S22 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0]) == _S30;

#line 1086
        }
        else
        {

#line 1086
            _S22 = false;

#line 1086
        }

#line 1086
        if(_S22)
        {

#line 1086
            winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 1086
        }

#line 1084
        i_5 = i_5 + 1U;

#line 1084
    }

#line 1094
    if(winner_0 != 4294967295U)
    {

#line 1094
        uint _S31 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 1094
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1096
    i_5 = 0U;
    for(;;)
    {

#line 1097
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1097
            break;
        }

#line 1098
        if(pair_0 != 4294967295U)
        {

#line 1098
            _S22 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == (tid_1 * 16U + i_5);

#line 1098
        }
        else
        {

#line 1098
            _S22 = false;

#line 1098
        }

#line 1098
        if(_S22)
        {

#line 1099
            *(peakIdx_0+pair_0) = int(slotToIndex_0(tid_1 * 16U + i_5));

#line 1099
            packed_float2 device* _S32 = peakVal_0+pair_0;
            if(_S26)
            {

#line 1100
                _S27 = (*re_9)[i_5].x;

#line 1100
            }
            else
            {

#line 1100
                _S27 = (*re_9)[i_5].y;

#line 1100
            }

#line 1100
            float _S33 = float(_S27);

#line 1100
            half _S34;
            if(_S26)
            {

#line 1101
                _S34 = (*im_9)[i_5].x;

#line 1101
            }
            else
            {

#line 1101
                _S34 = (*im_9)[i_5].y;

#line 1101
            }

#line 1100
            float2 _S35 = c16Bound_0(float2(_S33, float(_S34)), energy_1);

#line 1100
            *_S32 = packed_float2(_S35) ;

#line 1098
        }

#line 1097
        i_5 = i_5 + 1U;

#line 1097
    }

#line 1104
    if(pair_0 != 4294967295U)
    {

#line 1104
        _S22 = _S23;

#line 1104
    }
    else
    {

#line 1104
        _S22 = false;

#line 1104
    }

#line 1104
    if(_S22)
    {

#line 1104
        _S22 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1104
    }
    else
    {

#line 1104
        _S22 = false;

#line 1104
    }

#line 1104
    if(_S22)
    {

#line 1105
        *(peakIdx_0+pair_0) = int(-1);

#line 1105
        *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 1104
    }



    return;
}


#line 1247
void filterTwo_0(uint pairA_0, uint pairB_0, uint tA_0, uint tB_0, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* tmpl_0, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_2, KernelContext_0 thread* kernelContext_5)
{

    uint _S36;

#line 1250
    uint k2_1;

#line 1250
    float cr_0;

#line 1250
    float ci_0;

#line 1250
    uint _S37;

    thread array<half2, int(16)> re_10;

#line 1252
    thread array<half2, int(16)> im_10;

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
        uint _S38 = 64U * n2_0;

#line 1254
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 1024U + tid_2 + _S38);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 1024U + tid_2 + _S38);
        half _S39 = (*dreg_0)[n2_0].x;
        half _S40 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S39, _S39), half2(_S40, _S40), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_10[n2_0], &im_10[n2_0]);

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

                uint lgTB_0 = firstbithigh_0(64U);

#line 1266
                _S36 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(1024U);
                uint blk_2 = tid_2 >> lgTB_0;
                uint lane_3 = tid_2 & 63U;

                dft16s_0(&re_10, &im_10);

#line 1287
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 1024.0);
                float _S41 = tw_0.x;

#line 1288
                float _S42 = tw_0.y;

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
                    cmulw_0(&re_10[k2_1], &im_10[k2_1], half(cr_0), half(ci_0));
                    float nr_0 = cr_0 * _S41 - ci_0 * _S42;
                    float _S43 = cr_0 * _S42 + ci_0 * _S41;

#line 1290
                    k2_1 = k2_1 + 1U;

#line 1290
                    cr_0 = nr_0;

#line 1290
                    ci_0 = _S43;

#line 1290
                }

#line 1298
                uint per_2 = 16U / max(64U, 1U);
                uint _S44 = max(4U, 1U);

#line 1299
                _S37 = _S44;
                uint blk2_2 = tid_2 / _S44;

#line 1300
                uint lane2_2 = tid_2 % _S44;

#line 1300
                exchangeS_0(&re_10, &im_10, lgLn_0, lgTB_0, 64U, 1024U, blk_2, lane_3, per_2, _S44, 64U, blk2_2, lane2_2, kernelContext_5);

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

                uint lgTB_1 = firstbithigh_0(4U);

                uint blk_3 = tid_2 >> lgTB_1;
                uint lane_4 = tid_2 & 3U;

                dft16s_0(&re_10, &im_10);

#line 1287
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_4) / 64.0);
                float _S45 = tw_1.x;

#line 1288
                float _S46 = tw_1.y;

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
                    cmulw_0(&re_10[k2_1], &im_10[k2_1], half(cr_0), half(ci_0));
                    float nr_1 = cr_0 * _S45 - ci_0 * _S46;
                    float _S47 = cr_0 * _S46 + ci_0 * _S45;

#line 1290
                    k2_1 = k2_1 + 1U;

#line 1290
                    cr_0 = nr_1;

#line 1290
                    ci_0 = _S47;

#line 1290
                }

#line 1298
                uint per_3 = 16U / _S37;
                uint _S48 = max(0U, 1U);
                uint blk2_3 = tid_2 / _S48;

#line 1300
                uint lane2_3 = tid_2 % _S48;

#line 1300
                exchangeS_0(&re_10, &im_10, _S36, lgTB_1, 4U, 64U, blk_3, lane_4, per_3, _S48, 4U, blk2_3, lane2_3, kernelContext_5);

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
    innermostS_0(&re_10, &im_10);

#line 1322
    thread array<half2, int(16)> magv_1;

#line 1322
    uint i_7 = 0U;

#line 1322
    float eA_0 = 0.0;

#line 1322
    float eB_0 = 0.0;

    for(;;)
    {

#line 1324
        if(i_7 < 16U)
        {
        }
        else
        {

#line 1324
            break;
        }

#line 1325
        uint idx_0 = slotToIndex_0(tid_2 * 16U + i_7);

#line 1325
        bool live_0;
        if(idx_0 >= winStart_3)
        {

#line 1326
            live_0 = idx_0 < winEnd_3;

#line 1326
        }
        else
        {

#line 1326
            live_0 = false;

#line 1326
        }
        half2 mg_0 = mag2s_0(re_10[i_7], im_10[i_7]);
        float eA_1 = eA_0 + float(mg_0.x);

#line 1328
        float eB_1 = eB_0 + float(mg_0.y);

#line 1328
        half2 _S49;
        if(live_0)
        {

#line 1329
            _S49 = mg_0;

#line 1329
        }
        else
        {

#line 1329
            _S49 = half2(float2(0.0) );

#line 1329
        }

#line 1329
        magv_1[i_7] = _S49;

#line 1334
        if(live_0)
        {
            uint ov_0 = ((((uint(as_type<ushort>(re_10[i_7][0U])) & 65535U) | (uint(as_type<ushort>(re_10[i_7][1U])) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>(im_10[i_7][0U])) & 65535U) | (uint(as_type<ushort>(im_10[i_7][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1336
            uint _S50 = (uint(as_type<ushort>(magv_1[i_7][0U])) & 65535U) | (uint(as_type<ushort>(magv_1[i_7][1U])) << 16U);

#line 1336
            uint mb_0;

            if((ov_0 & 32768U) != 0U)
            {

#line 1338
                mb_0 = (_S50 & 4294901760U) | 31744U;

#line 1338
            }
            else
            {

#line 1338
                mb_0 = _S50;

#line 1338
            }

#line 1338
            uint mb_1;
            if((ov_0 & 2147483648U) != 0U)
            {

#line 1339
                mb_1 = (mb_0 & 65535U) | 2080374784U;

#line 1339
            }
            else
            {

#line 1339
                mb_1 = mb_0;

#line 1339
            }
            magv_1[i_7] = half2(as_type<half>(ushort(mb_1 & 65535U)), as_type<half>(ushort((mb_1 >> 16U) & 65535U)));

#line 1334
        }

#line 1324
        i_7 = i_7 + 1U;

#line 1324
        eA_0 = eA_1;

#line 1324
        eB_0 = eB_1;

#line 1324
    }

#line 1324
    float _S51 = pairSum_0(tid_2, eA_0, kernelContext_5);

#line 1344
    float eA_2 = _S51 / 1024.0;

#line 1344
    float _S52 = pairSum_0(tid_2, eB_0, kernelContext_5);
    float eB_2 = _S52 / 1024.0;

#line 1345
    thread array<half2, int(16)> _S53 = magv_1;

#line 1345
    thread array<half2, int(16)> _S54 = re_10;

#line 1345
    thread array<half2, int(16)> _S55 = im_10;

#line 1345
    peakLane_0(pairA_0, tid_2, 0U, &_S53, &_S54, &_S55, peakIdx_1, peakVal_1, winStart_3, winEnd_3, thrBits_2, eA_2, kernelContext_5);

#line 1345
    thread array<half2, int(16)> _S56 = magv_1;

#line 1345
    thread array<half2, int(16)> _S57 = re_10;

#line 1345
    thread array<half2, int(16)> _S58 = im_10;

#line 1345
    peakLane_0(pairB_0, tid_2, 1U, &_S56, &_S57, &_S58, peakIdx_1, peakVal_1, winStart_3, winEnd_3, thrBits_2, eB_2, kernelContext_5);



    return;
}


void filterPair_0(uint pair_1, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_2, packed_float2 device* peakVal_2, uint ntmpl_1, uint winStart_4, uint winEnd_4, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, KernelContext_0 thread* kernelContext_6)
{

#line 1353
    thread uint _S59 = winStart_4;

#line 1353
    thread uint _S60 = winEnd_4;

#line 1359
    kernelContext_6->_tid_0 = tid_3;

#line 1379
    uint tiles_0 = (ntmpl_1 + 2U - 1U) / 2U;
    uint slots_0 = binsize_1 * tiles_0;
    bool slotOk_0 = pair_1 < slots_0;

#line 1381
    uint q_2;
    if(slotOk_0)
    {

#line 1382
        q_2 = pair_1;

#line 1382
    }
    else
    {

#line 1382
        q_2 = slots_0 - 1U;

#line 1382
    }
    uint d_6 = q_2 / tiles_0;

#line 1383
    uint t0_0 = (q_2 - d_6 * tiles_0) * 2U;
    uint _S61 = d_6 * ntmpl_1 + t0_0;
    rowWindow_0(d_6, &_S59, &_S60);

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
        dreg_1[n2_1] = dload_0(data_0, d_6 * 1024U + tid_3 + 64U * n2_1);

#line 1398
        n2_1 = n2_1 + 1U;

#line 1398
    }

#line 1398
    uint k_1 = 0U;

#line 1406
    for(;;)
    {

#line 1406
        if(k_1 < 2U)
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
            okA_0 = (t0_0 + k_1) < ntmpl_1;

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
            okB_0 = (t0_0 + k_1 + 1U) < ntmpl_1;

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
            q_2 = _S61 + k_1;

#line 1408
        }
        else
        {

#line 1408
            q_2 = 4294967295U;

#line 1408
        }

#line 1408
        if(okB_0)
        {

#line 1408
            n2_1 = _S61 + k_1 + 1U;

#line 1408
        }
        else
        {

#line 1408
            n2_1 = 4294967295U;

#line 1408
        }
        uint _S62 = t0_0 + k_1;

#line 1409
        uint _S63 = ntmpl_1 - 1U;

#line 1409
        uint _S64 = min(_S62, _S63);

#line 1409
        uint _S65 = min(_S62 + 1U, _S63);

#line 1409
        thread array<half2, int(16)> _S66 = dreg_1;

#line 1409
        filterTwo_0(q_2, n2_1, _S64, _S65, tid_3, &_S66, tmpl_1, peakIdx_2, peakVal_2, _S59, _S60, thrBits_3, kernelContext_6);

#line 1406
        k_1 = k_1 + 2U;

#line 1406
    }

#line 1422
    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
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
    threadgroup array<uint, int(4096)> stg_1;

#line 1426
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1446
    uint _S67 = lid_0.x;

#line 1446
    uint _sub_0 = _S67 / 64U;
    uint _pr_0 = gid_0.x * 4U + _sub_0;

#line 1447
    uint _t_0 = _S67 % 64U;
    (&kernelContext_7)->_stgBase_0 = _sub_0 * 1024U;

#line 1448
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);



    return;
}
