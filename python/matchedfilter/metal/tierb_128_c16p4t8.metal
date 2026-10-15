#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
#ifndef MF_COARSE_TWT
#define MF_COARSE_TWT 0u
#endif
#ifndef MF_C16_RAW
#define MF_C16_RAW 0u
#endif

#line 11 "mm_128_fusedTierB_c16p4t8.slang"
constant array<uint, int(128)> COARSE_TWT_DATA_0 = { { 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 709377022U, 776354806U, 816987114U, 842939353U, 868629443U, 883243944U, 895761288U, 908016484U, 920075067U, 931871502U, 941439709U, 947010215U, 952384109U, 957561391U, 962542061U, 15360U, 776354806U, 842939353U, 883243944U, 908016484U, 931871502U, 947010215U, 957561391U, 967326120U, 976173331U, 984037490U, 990787467U, 996423199U, 1000879269U, 1004089918U, 1005989446U, 15360U, 816987114U, 883243944U, 920075067U, 947010215U, 962542061U, 976173331U, 987576349U, 996423199U, 1002648518U, 1005989446U, 1006545480U, 1004122686U, 998815076U, 990820235U, 980269252U, 15360U, 842939353U, 908016484U, 947010215U, 967326120U, 984037490U, 996423199U, 1004089918U, 1006632960U, 1004122686U, 996455967U, 984070258U, 967358888U, 947042983U, 908049252U, 842972121U, 15360U, 868629443U, 931871502U, 962542061U, 984037490U, 998782308U, 1005989446U, 1005236402U, 996455967U, 980269252U, 957594159U, 920107835U, 842972121U, 2856893438U, 3030760360U, 3088956125U, 15360U, 883243944U, 947010215U, 976173331U, 996423199U, 1005989446U, 1004122686U, 990820235U, 967358888U, 931904270U, 842972121U, 2923871222U, 3055532900U, 3105077807U, 3131553906U, 3148395685U, 15360U, 895761288U, 957561391U, 987576349U, 1004089918U, 1005236402U, 990820235U, 962574829U, 908049252U, 709409790U, 3030760360U, 3099900525U, 3131553906U, 3150164934U, 3153473094U, 3141220055U } };

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


#line 196 "mm_128_fusedTierB_c16p4t8.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 196
    return;
}


#line 167
half2 cload_0(uint device* b_0, uint i_0)
{

#line 168
    uint p_0 = b_0[i_0];

#line 168
    return half2(half((as_type<half>((ushort)((p_0 & 65535U))))), half((as_type<half>((ushort)((p_0 >> 16U))))));
}


#line 202
half2 dload_0(uint device* b_1, uint i_1)
{

#line 208
    return cload_0(b_1, i_1);
}


#line 332
void cmulconjs_0(half2 ar_0, half2 ai_0, half2 br_0, half2 bi_0, half2 thread* pr_0, half2 thread* pi_0)
{
    *pr_0 = ar_0 * br_0 + ai_0 * bi_0;
    *pi_0 = ai_0 * br_0 - ar_0 * bi_0;
    return;
}


#line 344
void r4s_0(array<half2, int(16)> thread* re_0, array<half2, int(16)> thread* im_0, uint a_0, uint b_2, uint c_0, uint d_1)
{
    half2 t0r_0 = (*re_0)[a_0] + (*re_0)[c_0];

#line 346
    half2 t0i_0 = (*im_0)[a_0] + (*im_0)[c_0];
    half2 t1r_0 = (*re_0)[a_0] - (*re_0)[c_0];

#line 347
    half2 t1i_0 = (*im_0)[a_0] - (*im_0)[c_0];
    half2 t2r_0 = (*re_0)[b_2] + (*re_0)[d_1];

#line 348
    half2 t2i_0 = (*im_0)[b_2] + (*im_0)[d_1];
    half2 t3r_0 = (*re_0)[b_2] - (*re_0)[d_1];
    half2 j3r_0 = - ((*im_0)[b_2] - (*im_0)[d_1]);
    (*re_0)[a_0] = t0r_0 + t2r_0;

#line 351
    (*im_0)[a_0] = t0i_0 + t2i_0;
    (*re_0)[b_2] = t1r_0 + j3r_0;

#line 352
    (*im_0)[b_2] = t1i_0 + t3r_0;
    (*re_0)[c_0] = t0r_0 - t2r_0;

#line 353
    (*im_0)[c_0] = t0i_0 - t2i_0;
    (*re_0)[d_1] = t1r_0 - j3r_0;

#line 354
    (*im_0)[d_1] = t1i_0 - t3r_0;
    return;
}


#line 323
void cmulw_0(half2 thread* xr_0, half2 thread* xi_0, half wr_0, half wi_0)
{

#line 323
    half2 _S2 = half2(wr_0) ;

#line 323
    half2 _S3 = half2(wi_0) ;


    half2 ni_0 = *xr_0 * _S3 + *xi_0 * _S2;
    *xr_0 = *xr_0 * _S2 - *xi_0 * _S3;

#line 327
    *xi_0 = ni_0;
    return;
}


#line 357
void swap2_0(array<half2, int(16)> thread* re_1, array<half2, int(16)> thread* im_1, uint p_1, uint q_0)
{

    half2 t_0 = (*re_1)[p_1];

#line 360
    (*re_1)[p_1] = (*re_1)[q_0];

#line 360
    (*re_1)[q_0] = t_0;
    half2 t_1 = (*im_1)[p_1];

#line 361
    (*im_1)[p_1] = (*im_1)[q_0];

#line 361
    (*im_1)[q_0] = t_1;
    return;
}


#line 395
void dft16s_0(array<half2, int(16)> thread* re_2, array<half2, int(16)> thread* im_2)
{

#line 395
    uint n1_0 = 0U;

    for(;;)
    {

#line 397
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 397
            break;
        }

#line 397
        r4s_0(re_2, im_2, n1_0, n1_0 + 4U, n1_0 + 8U, n1_0 + 12U);

#line 397
        n1_0 = n1_0 + 1U;

#line 397
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

#line 408
    uint k2_0 = 0U;
    for(;;)
    {

#line 409
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 409
            break;
        }

#line 410
        uint _S4 = 4U * k2_0;

#line 410
        r4s_0(re_2, im_2, _S4, _S4 + 1U, _S4 + 2U, _S4 + 3U);

#line 409
        k2_0 = k2_0 + 1U;

#line 409
    }

    swap2_0(re_2, im_2, 1U, 4U);

#line 411
    swap2_0(re_2, im_2, 2U, 8U);

#line 411
    swap2_0(re_2, im_2, 3U, 12U);
    swap2_0(re_2, im_2, 6U, 9U);

#line 412
    swap2_0(re_2, im_2, 7U, 13U);

#line 412
    swap2_0(re_2, im_2, 11U, 14U);
    return;
}


#line 52 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S5 = ((MF_COARSE_TWT));

#line 55
    return _S5;
}


#line 84
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 271 "mm_128_fusedTierB_c16p4t8.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S6 = max(TB_0, 1U);

#line 273
    uint j_0 = d_2 / _S6;

#line 273
    uint m_0 = d_2 % _S6;

#line 273
    uint _S7;
    if(TB_0 <= 16U)
    {

#line 274
        _S7 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 274
    }
    else
    {

#line 274
        _S7 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 274
    }

#line 274
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
    array<uint, int(512)> threadgroup* stg_0;
    uint _S8;
};


#line 247 "mm_128_fusedTierB_c16p4t8.slang"
void stgPut_0(uint i_2, half2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 247
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + i_2] = (uint(as_type<ushort>(v_0[0U])) & 65535U) | (uint(as_type<ushort>(v_0[1U])) << 16U);

#line 247
    return;
}


#line 248
half2 stgGet_0(uint i_3, KernelContext_0 thread* kernelContext_1)
{

#line 248
    return half2(as_type<half>(ushort(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) & 65535U)), as_type<half>(ushort((((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + i_3]) >> 16U) & 65535U)));
}


#line 433
void exchangeS_0(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{
    uint j_1;

    thread array<half2, int(16)> outr_0;

#line 437
    thread array<half2, int(16)> outi_0;

#line 437
    uint z_0 = 0U;
    for(;;)
    {

#line 438
        if(z_0 < 16U)
        {
        }
        else
        {

#line 438
            break;
        }

#line 438
        half2 _S9 = half2(float2(0.0f) );

#line 438
        outr_0[z_0] = _S9;

#line 438
        outi_0[z_0] = _S9;

#line 438
        z_0 = z_0 + 1U;

#line 438
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S10 = p0_0 & lenMask_0;
    uint _S11 = (_S10 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S10 & spanMask_0);

#line 443
    uint c_1 = 0U;
    for(;;)
    {

#line 444
        if(c_1 < 1U)
        {
        }
        else
        {

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
                for(;;)
                {

#line 446
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 446
                    j_1 = 0U;
                    for(;;)
                    {

#line 447
                        if(j_1 < 16U)
                        {
                        }
                        else
                        {

#line 447
                            break;
                        }

#line 448
                        uint _S12 = j_1 * 8U + kernelContext_2->_tid_0;

#line 448
                        stgPut_0(_S12, (*re_3)[c_1 * 16U + j_1], kernelContext_2);

#line 447
                        j_1 = j_1 + 1U;

#line 447
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 449
                    uint d_3 = 0U;
                    for(;;)
                    {

#line 450
                        if(d_3 < 16U)
                        {
                        }
                        else
                        {

#line 450
                            break;
                        }
                        uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S13 = pz_0 & lenMask_0;
                        uint az_0 = (_S13 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S13 & spanMask_0);

#line 454
                        half2 _S14 = stgGet_0(_S11 + az_0 - c_1 * 16U * 8U, kernelContext_2);



                        outr_0[d_3] = _S14;

#line 450
                        d_3 = d_3 + 1U;

#line 450
                    }

#line 445
                    break;
                }

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
                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 446
                    uint j_2 = 0U;
                    for(;;)
                    {

#line 447
                        if(j_2 < 16U)
                        {
                        }
                        else
                        {

#line 447
                            break;
                        }

#line 448
                        uint _S15 = j_2 * 8U + kernelContext_2->_tid_0;

#line 448
                        stgPut_0(_S15, (*im_3)[c_1 * 16U + j_2], kernelContext_2);

#line 447
                        j_2 = j_2 + 1U;

#line 447
                    }

                    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 449
                    uint d_4 = 0U;
                    for(;;)
                    {

#line 450
                        if(d_4 < 16U)
                        {
                        }
                        else
                        {

#line 450
                            break;
                        }
                        uint pz_1 = computeWant_0(d_4, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
                        uint _S16 = pz_1 & lenMask_0;
                        uint az_1 = (_S16 >> lgSpan_0) * 8U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 454
                        half2 _S17 = stgGet_0(_S11 + az_1 - c_1 * 16U * 8U, kernelContext_2);



                        outi_0[d_4] = _S17;

#line 450
                        d_4 = d_4 + 1U;

#line 450
                    }

#line 445
                    break;
                }

#line 445
                break;
            }

#line 445
            break;
        }

#line 444
        c_1 = c_1 + 1U;

#line 444
    }

#line 444
    j_1 = 0U;

#line 463
    for(;;)
    {

#line 463
        if(j_1 < 16U)
        {
        }
        else
        {

#line 463
            break;
        }

#line 463
        (*re_3)[j_1] = outr_0[j_1];

#line 463
        (*im_3)[j_1] = outi_0[j_1];

#line 463
        j_1 = j_1 + 1U;

#line 463
    }
    return;
}


#line 377
void dft8s_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4, uint o_0)
{
    thread array<half2, int(8)> br_1;

#line 379
    thread array<half2, int(8)> bi_1;

#line 379
    uint s_0 = 1U;
    for(;;)
    {

#line 380
        if(s_0 < 8U)
        {
        }
        else
        {

#line 380
            break;
        }

#line 380
        uint j_3 = 0U;
        for(;;)
        {

#line 381
            if(j_3 < 4U)
            {
            }
            else
            {

#line 381
                break;
            }

#line 382
            uint k_0 = j_3 & (s_0 - 1U);

#line 382
            uint base_0 = (j_3 - k_0) << 1U;
            float ang_0 = 3.14159274101257324f * float(k_0) / float(s_0);
            uint _S18 = o_0 + j_3;

#line 384
            uint _S19 = _S18 + 4U;

#line 384
            thread half2 vr_0 = (*re_4)[_S19];

#line 384
            thread half2 vi_0 = (*im_4)[_S19];
            float2 tw_0 = mfTwiddle_0(ang_0);
            cmulw_0(&vr_0, &vi_0, half(tw_0.x), half(tw_0.y));

            uint _S20 = base_0 + k_0;

#line 388
            br_1[_S20] = (*re_4)[_S18] + vr_0;

#line 388
            bi_1[_S20] = (*im_4)[_S18] + vi_0;
            uint _S21 = _S20 + s_0;

#line 389
            br_1[_S21] = (*re_4)[_S18] - vr_0;

#line 389
            bi_1[_S21] = (*im_4)[_S18] - vi_0;

#line 381
            j_3 = j_3 + 1U;

#line 381
        }

#line 381
        uint i_4 = 0U;

#line 391
        for(;;)
        {

#line 391
            if(i_4 < 8U)
            {
            }
            else
            {

#line 391
                break;
            }

#line 391
            uint _S22 = o_0 + i_4;

#line 391
            (*re_4)[_S22] = br_1[i_4];

#line 391
            (*im_4)[_S22] = bi_1[i_4];

#line 391
            i_4 = i_4 + 1U;

#line 391
        }

#line 380
        s_0 = s_0 << 1U;

#line 380
    }

#line 393
    return;
}


#line 466
void innermostS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5)
{

#line 466
    uint b_3 = 0U;


    for(;;)
    {

#line 469
        if(b_3 < 2U)
        {
        }
        else
        {

#line 469
            break;
        }

#line 469
        dft8s_0(re_5, im_5, b_3 * 8U);

#line 469
        b_3 = b_3 + 1U;

#line 469
    }


    return;
}


#line 759
uint lgOf_0(uint i_5)
{

#line 759
    uint _S23;

#line 759
    if(i_5 < 1U)
    {

#line 759
        _S23 = 4U;

#line 759
    }
    else
    {

#line 759
        if(i_5 == 1U)
        {

#line 759
            _S23 = 3U;

#line 759
        }
        else
        {

#line 759
            _S23 = 1U;

#line 759
        }

#line 759
    }

#line 759
    return _S23;
}


#line 761
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 765
    uint lg_1 = lgOf_0(0U);

#line 770
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 419
half2 mag2s_0(half2 re_6, half2 im_6)
{

#line 419
    return re_6 * re_6 + im_6 * im_6;
}


#line 1313
uint mfShflXor_0(uint v_1, uint s_1, KernelContext_0 thread* kernelContext_3)
{

#line 1313
    uint _S24 = (simd_shuffle((v_1), ushort((int((kernelContext_3->_S8) ^ s_1)))));

#line 1313
    return _S24;
}


#line 66 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S25 = ((MF_C16_RAW));

#line 69
    return _S25;
}


#line 1434 "mm_128_fusedTierB_c16p4t8.slang"
void peakTwoGate_0(uint pairA_0, uint pairB_0, uint tid_0, const array<half2, int(16)> thread* re_7, const array<half2, int(16)> thread* im_7, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, float thr_0, KernelContext_0 thread* kernelContext_4)
{


    uint _S26 = slotToIndex_0(tid_0 * 16U) - winStart_2;
    uint _S27 = winEnd_2 - winStart_2;
    half2 _S28 = half2(float2(0.0f) );
    half2 _S29 = half2(float2(0.015625f) );

#line 1441
    uint i_6 = 0U;

#line 1441
    half2 best_0 = _S28;

#line 1441
    half2 en_0 = _S28;
    for(;;)
    {

#line 1442
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1442
            break;
        }

#line 1442
        half2 _S30;

        if((_S26 + slotToIndex_0(i_6)) < _S27)
        {

#line 1444
            _S30 = mag2s_0((*re_7)[i_6], (*im_7)[i_6]);

#line 1444
        }
        else
        {

#line 1444
            _S30 = _S28;

#line 1444
        }

#line 1444
        half2 _S31 = max(best_0, _S30);
        half2 sr_0 = (*re_7)[i_6] * _S29;

#line 1445
        half2 si_0 = (*im_7)[i_6] * _S29;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1442
        i_6 = i_6 + 1U;

#line 1442
        best_0 = _S31;

#line 1442
        en_0 = en_1;

#line 1442
    }

#line 1442
    uint _S32 = mfShflXor_0((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U), 1U, kernelContext_4);

#line 1449
    half2 _S33 = max(best_0, half2(as_type<half>(ushort(_S32 & 65535U)), as_type<half>(ushort((_S32 >> 16U) & 65535U))));

#line 1449
    uint _S34 = mfShflXor_0((uint(as_type<ushort>(en_0[0U])) & 65535U) | (uint(as_type<ushort>(en_0[1U])) << 16U), 1U, kernelContext_4);
    half2 en_2 = en_0 + half2(as_type<half>(ushort(_S34 & 65535U)), as_type<half>(ushort((_S34 >> 16U) & 65535U)));

#line 1450
    uint _S35 = mfShflXor_0((uint(as_type<ushort>(_S33[0U])) & 65535U) | (uint(as_type<ushort>(_S33[1U])) << 16U), 2U, kernelContext_4);

#line 1449
    half2 _S36 = max(_S33, half2(as_type<half>(ushort(_S35 & 65535U)), as_type<half>(ushort((_S35 >> 16U) & 65535U))));

#line 1449
    uint _S37 = mfShflXor_0((uint(as_type<ushort>(en_2[0U])) & 65535U) | (uint(as_type<ushort>(en_2[1U])) << 16U), 2U, kernelContext_4);
    half2 en_3 = en_2 + half2(as_type<half>(ushort(_S37 & 65535U)), as_type<half>(ushort((_S37 >> 16U) & 65535U)));

#line 1450
    uint _S38 = mfShflXor_0((uint(as_type<ushort>(_S36[0U])) & 65535U) | (uint(as_type<ushort>(_S36[1U])) << 16U), 4U, kernelContext_4);

#line 1449
    half2 best_1 = max(_S36, half2(as_type<half>(ushort(_S38 & 65535U)), as_type<half>(ushort((_S38 >> 16U) & 65535U))));

#line 1449
    uint _S39 = mfShflXor_0((uint(as_type<ushort>(en_3[0U])) & 65535U) | (uint(as_type<ushort>(en_3[1U])) << 16U), 4U, kernelContext_4);
    half2 en_4 = en_3 + half2(as_type<half>(ushort(_S39 & 65535U)), as_type<half>(ushort((_S39 >> 16U) & 65535U)));

#line 1450
    uint _S40 = (uint(as_type<ushort>(en_4[0U])) & 65535U) | (uint(as_type<ushort>(en_4[1U])) << 16U);

#line 1450
    uint _S41 = (uint(as_type<ushort>(best_1[0U])) & 65535U) | (uint(as_type<ushort>(best_1[1U])) << 16U);

#line 1450
    bool infA_0;

#line 1458
    if((_S40 & 31744U) == 31744U)
    {

#line 1458
        infA_0 = true;

#line 1458
    }
    else
    {

#line 1458
        infA_0 = (_S41 & 31744U) == 31744U;

#line 1458
    }

#line 1458
    bool infB_0;
    if((_S40 & 2080374784U) == 2080374784U)
    {

#line 1459
        infB_0 = true;

#line 1459
    }
    else
    {

#line 1459
        infB_0 = (_S41 & 2080374784U) == 2080374784U;

#line 1459
    }

#line 71 "twiddle.slang"
    uint _S42 = mfC16RawFlag_0();

#line 71
    float _S43;

#line 1462 "mm_128_fusedTierB_c16p4t8.slang"
    if((1U - _S42) != 0U)
    {

#line 1462
        _S43 = 11.95860004425048828f;

#line 1462
    }
    else
    {

#line 1462
        _S43 = 0.0f;

#line 1462
    }

#line 1462
    float k2_1 = _S43 * 0.00048828125f * 1.00010001659393311f;
    float mA_0 = sqrt(float(best_1.x));

#line 1463
    float mB_0 = sqrt(float(best_1.y));

    float bA_0 = mA_0 * 1.00107669830322266f + k2_1 * sqrt(float(en_4.x) * 32.0f);
    float bB_0 = mB_0 * 1.00107669830322266f + k2_1 * sqrt(float(en_4.y) * 32.0f);

#line 1466
    bool hitA_0;
    if(infA_0)
    {

#line 1467
        hitA_0 = true;

#line 1467
    }
    else
    {

#line 1467
        if(mA_0 > 0.0f)
        {

#line 1467
            hitA_0 = bA_0 >= thr_0;

#line 1467
        }
        else
        {

#line 1467
            hitA_0 = false;

#line 1467
        }

#line 1467
    }

#line 1467
    bool hitB_0;
    if(infB_0)
    {

#line 1468
        hitB_0 = true;

#line 1468
    }
    else
    {

#line 1468
        if(mB_0 > 0.0f)
        {

#line 1468
            hitB_0 = bB_0 >= thr_0;

#line 1468
        }
        else
        {

#line 1468
            hitB_0 = false;

#line 1468
        }

#line 1468
    }
    bool _S44 = tid_0 == 0U;

#line 1469
    bool _S45;

#line 1469
    if(_S44)
    {

#line 1469
        _S45 = pairA_0 != 4294967295U;

#line 1469
    }
    else
    {

#line 1469
        _S45 = false;

#line 1469
    }

#line 1469
    int _S46;

#line 1469
    float2 _S47;

#line 1469
    if(_S45)
    {

#line 1470
        int device* _S48 = peakIdx_0+pairA_0;

#line 1470
        if(hitA_0)
        {

#line 1470
            _S46 = int(0);

#line 1470
        }
        else
        {

#line 1470
            _S46 = int(-1);

#line 1470
        }

#line 1470
        *_S48 = _S46;

#line 1470
        packed_float2 device* _S49 = peakVal_0+pairA_0;
        if(infA_0)
        {

#line 1471
            _S47 = float2(3.40282306073709653e+38f, 0.0f);

#line 1471
        }
        else
        {

#line 1471
            if(hitA_0)
            {

#line 1471
                _S47 = float2(bA_0, 0.0f);

#line 1471
            }
            else
            {

#line 1471
                _S47 = float2(0.0f, 0.0f);

#line 1471
            }

#line 1471
        }

#line 1471
        *_S49 = packed_float2(_S47) ;

#line 1469
    }



    if(_S44)
    {

#line 1473
        infA_0 = pairB_0 != 4294967295U;

#line 1473
    }
    else
    {

#line 1473
        infA_0 = false;

#line 1473
    }

#line 1473
    if(infA_0)
    {

#line 1474
        int device* _S50 = peakIdx_0+pairB_0;

#line 1474
        if(hitB_0)
        {

#line 1474
            _S46 = int(0);

#line 1474
        }
        else
        {

#line 1474
            _S46 = int(-1);

#line 1474
        }

#line 1474
        *_S50 = _S46;

#line 1474
        packed_float2 device* _S51 = peakVal_0+pairB_0;
        if(infB_0)
        {

#line 1475
            _S47 = float2(3.40282306073709653e+38f, 0.0f);

#line 1475
        }
        else
        {

#line 1475
            if(hitB_0)
            {

#line 1475
                _S47 = float2(bB_0, 0.0f);

#line 1475
            }
            else
            {

#line 1475
                _S47 = float2(0.0f, 0.0f);

#line 1475
            }

#line 1475
        }

#line 1475
        *_S51 = packed_float2(_S47) ;

#line 1473
    }



    return;
}


#line 300
float2 c16Bound_0(float2 v_2, float energy_0)
{

#line 71 "twiddle.slang"
    uint _S52 = mfC16RawFlag_0();

#line 302 "mm_128_fusedTierB_c16p4t8.slang"
    if((1U - _S52) == 0U)
    {

#line 302
        return v_2;
    }

#line 303
    float m_1 = length(v_2);
    float b_4 = m_1 * 1.00146484375f + 0.00583916017785668f * sqrt(energy_0);

#line 304
    float2 _S53;
    if(m_1 > 0.0f)
    {

#line 305
        _S53 = v_2 * float2((b_4 / m_1)) ;

#line 305
    }
    else
    {

#line 305
        _S53 = float2(b_4, 0.0f);

#line 305
    }

#line 305
    return _S53;
}


#line 1316
void peakTwoWave_0(uint pairA_1, uint pairB_1, uint tid_1, const array<half2, int(16)> thread* re_8, const array<half2, int(16)> thread* im_8, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{
    uint m_2;

#line 1318
    bool _S54;

#line 1318
    bool _S55;

    uint _S56 = slotToIndex_0(tid_1 * 16U) - winStart_3;
    uint _S57 = winEnd_3 - winStart_3;

#line 1328
    half2 _S58 = half2(float2(0.0f) );
    half2 _S59 = half2(float2(0.015625f) );

#line 1329
    uint i_7 = 0U;

#line 1329
    half2 en_5 = _S58;

#line 1329
    uint ovAcc_0 = 0U;

#line 1329
    uint kA_0 = 0U;

#line 1329
    uint kB_0 = 0U;



    for(;;)
    {

#line 1333
        if(i_7 < 16U)
        {
        }
        else
        {

#line 1333
            break;
        }
        half2 mg_0 = mag2s_0((*re_8)[i_7], (*im_8)[i_7]);
        half2 sr_1 = (*re_8)[i_7] * _S59;

#line 1336
        half2 si_1 = (*im_8)[i_7] * _S59;
        half2 en_6 = en_5 + (sr_1 * sr_1 + si_1 * si_1);
        if((_S56 + slotToIndex_0(i_7)) < _S57)
        {

#line 1338
            m_2 = (uint(as_type<ushort>(mg_0[0U])) & 65535U) | (uint(as_type<ushort>(mg_0[1U])) << 16U);

#line 1338
        }
        else
        {

#line 1338
            m_2 = 0U;

#line 1338
        }

#line 1344
        uint ovAcc_1 = ovAcc_0 | (((((uint(as_type<ushort>((*re_8)[i_7].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[i_7].y)) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>((*im_8)[i_7].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[i_7].y)) << 16U)) & 2080406528U) + 67109888U));


        uint _S60 = 15U - i_7;

#line 1347
        uint _S61 = max(kA_0, (m_2 << 16U) | _S60);
        uint _S62 = max(kB_0, (m_2 & 4294901760U) | _S60);

#line 1333
        i_7 = i_7 + 1U;

#line 1333
        en_5 = en_6;

#line 1333
        ovAcc_0 = ovAcc_1;

#line 1333
        kA_0 = _S61;

#line 1333
        kB_0 = _S62;

#line 1333
    }

#line 1352
    if((ovAcc_0 & 32768U) != 0U)
    {

#line 1352
        kA_0 = max(kA_0, 2080374799U);

#line 1352
    }
    if((ovAcc_0 & 2147483648U) != 0U)
    {

#line 1353
        kB_0 = max(kB_0, 2080374799U);

#line 1353
    }


    uint _S63 = (4095U - tid_1) << 4U;

#line 1356
    uint kA_1 = kA_0 | _S63;
    uint kB_1 = kB_0 | _S63;

#line 1357
    uint _S64 = mfShflXor_0(kA_1, 1U, kernelContext_5);

    uint _S65 = max(kA_1, _S64);

#line 1359
    uint _S66 = mfShflXor_0(kB_1, 1U, kernelContext_5);
    uint _S67 = max(kB_1, _S66);

#line 1360
    uint _S68 = mfShflXor_0((uint(as_type<ushort>(en_5[0U])) & 65535U) | (uint(as_type<ushort>(en_5[1U])) << 16U), 1U, kernelContext_5);
    half2 en_7 = en_5 + half2(as_type<half>(ushort(_S68 & 65535U)), as_type<half>(ushort((_S68 >> 16U) & 65535U)));

#line 1361
    uint _S69 = mfShflXor_0(_S65, 2U, kernelContext_5);

#line 1359
    uint _S70 = max(_S65, _S69);

#line 1359
    uint _S71 = mfShflXor_0(_S67, 2U, kernelContext_5);
    uint _S72 = max(_S67, _S71);

#line 1360
    uint _S73 = mfShflXor_0((uint(as_type<ushort>(en_7[0U])) & 65535U) | (uint(as_type<ushort>(en_7[1U])) << 16U), 2U, kernelContext_5);
    half2 en_8 = en_7 + half2(as_type<half>(ushort(_S73 & 65535U)), as_type<half>(ushort((_S73 >> 16U) & 65535U)));

#line 1361
    uint _S74 = mfShflXor_0(_S70, 4U, kernelContext_5);

#line 1359
    uint _S75 = max(_S70, _S74);

#line 1359
    uint _S76 = mfShflXor_0(_S72, 4U, kernelContext_5);
    uint _S77 = max(_S72, _S76);

#line 1360
    uint _S78 = mfShflXor_0((uint(as_type<ushort>(en_8[0U])) & 65535U) | (uint(as_type<ushort>(en_8[1U])) << 16U), 4U, kernelContext_5);
    half2 en_9 = en_8 + half2(as_type<half>(ushort(_S78 & 65535U)), as_type<half>(ushort((_S78 >> 16U) & 65535U)));



    float enA_0 = float(en_9.x) * 32.0f;

#line 1365
    float enB_0 = float(en_9.y) * 32.0f;
    uint slotA_0 = 65535U - (_S75 & 65535U);

#line 1366
    uint slotB_0 = 65535U - (_S77 & 65535U);

#line 1372
    uint _S79 = _S75 >> 16U;

#line 1372
    bool infA_1 = _S79 >= 31744U;

#line 1372
    uint _S80 = _S77 >> 16U;

#line 1372
    bool infB_1 = _S80 >= 31744U;

#line 1372
    bool hitA_1;



    if(infA_1)
    {

#line 1376
        hitA_1 = true;

#line 1376
    }
    else
    {

#line 1376
        hitA_1 = (as_type<half>((ushort)((_S79)))) > (as_type<float>((thrBits_1)));

#line 1376
    }

#line 1376
    bool hitB_1;
    if(infB_1)
    {

#line 1377
        hitB_1 = true;

#line 1377
    }
    else
    {

#line 1377
        hitB_1 = (as_type<half>((ushort)((_S80)))) > (as_type<float>((thrBits_1)));

#line 1377
    }

#line 1385
    uint _S81 = slotA_0 >> 4U;

#line 1385
    uint _S82 = slotA_0 & 15U;

#line 1385
    uint _S83 = slotB_0 >> 4U;

#line 1385
    uint _S84 = slotB_0 & 15U;
    thread array<float, int(2)> vA_0;

#line 1386
    thread array<float, int(2)> vB_0;
    vB_0[int(1)] = 0.0f;

#line 1387
    vB_0[int(0)] = 0.0f;

#line 1387
    vA_0[int(1)] = 0.0f;

#line 1387
    vA_0[int(0)] = 0.0f;

#line 1387
    for(;;)
    {

#line 1387
        for(;;)
        {

#line 1388
            for(;;)
            {

#line 1388
                for(;;)
                {

#line 1388
                    for(;;)
                    {

#line 1389
                        for(;;)
                        {

#line 1390
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1390
                            m_2 = 0U;
                            for(;;)
                            {

#line 1391
                                if(m_2 < 16U)
                                {
                                }
                                else
                                {

#line 1391
                                    break;
                                }

#line 1392
                                (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + m_2 * 8U + tid_1] = (uint(as_type<ushort>((*re_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[m_2].y)) << 16U);

#line 1391
                                m_2 = m_2 + 1U;

#line 1391
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            bool _S85 = tid_1 == 0U;

#line 1394
                            _S54 = _S85;

#line 1394
                            if(_S85)
                            {

#line 1395
                                if(_S82 >= 0U)
                                {

#line 1395
                                    _S55 = _S82 < 16U;

#line 1395
                                }
                                else
                                {

#line 1395
                                    _S55 = false;

#line 1395
                                }

#line 1395
                                if(_S55)
                                {

#line 1396
                                    vA_0[0U] = (as_type<half>((ushort)(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S82 * 8U + _S81]))));

#line 1395
                                }

                                if(_S84 >= 0U)
                                {

#line 1397
                                    _S55 = _S84 < 16U;

#line 1397
                                }
                                else
                                {

#line 1397
                                    _S55 = false;

#line 1397
                                }

#line 1397
                                if(_S55)
                                {

#line 1398
                                    vB_0[0U] = (as_type<half>((ushort)((((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S84 * 8U + _S83]) >> 16U))));

#line 1397
                                }

#line 1394
                            }

#line 1389
                            break;
                        }

#line 1389
                        break;
                    }

#line 1389
                    break;
                }

#line 1388
                break;
            }

#line 1388
            break;
        }

#line 1388
        for(;;)
        {

#line 1388
            for(;;)
            {

#line 1388
                for(;;)
                {

#line 1388
                    for(;;)
                    {

#line 1389
                        for(;;)
                        {

#line 1390
                            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1390
                            m_2 = 0U;
                            for(;;)
                            {

#line 1391
                                if(m_2 < 16U)
                                {
                                }
                                else
                                {

#line 1391
                                    break;
                                }

#line 1392
                                (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + m_2 * 8U + tid_1] = (uint(as_type<ushort>((*im_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[m_2].y)) << 16U);

#line 1391
                                m_2 = m_2 + 1U;

#line 1391
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            if(_S54)
                            {

#line 1395
                                if(_S82 >= 0U)
                                {

#line 1395
                                    _S55 = _S82 < 16U;

#line 1395
                                }
                                else
                                {

#line 1395
                                    _S55 = false;

#line 1395
                                }

#line 1395
                                if(_S55)
                                {

#line 1396
                                    vA_0[1U] = (as_type<half>((ushort)(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S82 * 8U + _S81]))));

#line 1395
                                }

                                if(_S84 >= 0U)
                                {

#line 1397
                                    _S55 = _S84 < 16U;

#line 1397
                                }
                                else
                                {

#line 1397
                                    _S55 = false;

#line 1397
                                }

#line 1397
                                if(_S55)
                                {

#line 1398
                                    vB_0[1U] = (as_type<half>((ushort)((((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S84 * 8U + _S83]) >> 16U))));

#line 1397
                                }

#line 1394
                            }

#line 1389
                            break;
                        }

#line 1389
                        break;
                    }

#line 1389
                    break;
                }

#line 1388
                break;
            }

#line 1388
            break;
        }

#line 1388
        break;
    }

#line 1402
    if(_S54)
    {

#line 1402
        _S55 = pairA_1 != 4294967295U;

#line 1402
    }
    else
    {

#line 1402
        _S55 = false;

#line 1402
    }

#line 1402
    int _S86;

#line 1402
    float2 _S87;

#line 1402
    if(_S55)
    {

#line 1403
        int device* _S88 = peakIdx_1+pairA_1;

#line 1403
        if(hitA_1)
        {

#line 1403
            _S86 = int(slotToIndex_0(slotA_0));

#line 1403
        }
        else
        {

#line 1403
            _S86 = int(-1);

#line 1403
        }

#line 1403
        *_S88 = _S86;

#line 1403
        packed_float2 device* _S89 = peakVal_1+pairA_1;
        if(infA_1)
        {

#line 1404
            _S87 = float2(3.40282306073709653e+38f, 0.0f);

#line 1404
        }
        else
        {

#line 1405
            if(hitA_1)
            {

#line 1405
                float2 _S90 = c16Bound_0(float2(vA_0[int(0)], vA_0[int(1)]), enA_0);

#line 1405
                _S87 = _S90;

#line 1405
            }
            else
            {

#line 1405
                _S87 = float2(0.0f, 0.0f);

#line 1405
            }

#line 1404
        }

#line 1404
        *_S89 = packed_float2(_S87) ;

#line 1402
    }

#line 1407
    if(_S54)
    {

#line 1407
        hitA_1 = pairB_1 != 4294967295U;

#line 1407
    }
    else
    {

#line 1407
        hitA_1 = false;

#line 1407
    }

#line 1407
    if(hitA_1)
    {

#line 1408
        int device* _S91 = peakIdx_1+pairB_1;

#line 1408
        if(hitB_1)
        {

#line 1408
            _S86 = int(slotToIndex_0(slotB_0));

#line 1408
        }
        else
        {

#line 1408
            _S86 = int(-1);

#line 1408
        }

#line 1408
        *_S91 = _S86;

#line 1408
        packed_float2 device* _S92 = peakVal_1+pairB_1;
        if(infB_1)
        {

#line 1409
            _S87 = float2(3.40282306073709653e+38f, 0.0f);

#line 1409
        }
        else
        {

#line 1410
            if(hitB_1)
            {

#line 1410
                float2 _S93 = c16Bound_0(float2(vB_0[int(0)], vB_0[int(1)]), enB_0);

#line 1410
                _S87 = _S93;

#line 1410
            }
            else
            {

#line 1410
                _S87 = float2(0.0f, 0.0f);

#line 1410
            }

#line 1409
        }

#line 1409
        *_S92 = packed_float2(_S87) ;

#line 1407
    }

#line 1412
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
        uint _S94 = 8U * n2_0;

#line 1490
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 128U + tid_2 + _S94);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 128U + tid_2 + _S94);
        half _S95 = (*dreg_0)[n2_0].x;
        half _S96 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S95, _S95), half2(_S96, _S96), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_9[n2_0], &im_9[n2_0]);

#line 1489
        n2_0 = n2_0 + 1U;

#line 1489
    }

#line 1502
    uint lgTB_0 = firstbithigh_0(8U);
    uint lgLn_0 = firstbithigh_0(128U);
    uint blk_2 = tid_2 >> lgTB_0;
    uint lane_2 = tid_2 & 7U;

    dft16s_0(&re_9, &im_9);

#line 57 "twiddle.slang"
    uint _S97 = mfCoarseTwtFlag_0();

#line 57
    uint k2_2;

#line 1509 "mm_128_fusedTierB_c16p4t8.slang"
    if(_S97 != 0U)
    {

#line 1509
        k2_2 = 0U;

#line 1516
        for(;;)
        {

#line 1516
            if(k2_2 < 16U)
            {
            }
            else
            {

#line 1516
                break;
            }

#line 1517
            uint _S98 = lane_2 * 16U + k2_2;
            cmulw_0(&re_9[k2_2], &im_9[k2_2], as_type<half>(ushort((COARSE_TWT_DATA_0[_S98]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S98]) >> 16U) & 65535U)));

#line 1516
            k2_2 = k2_2 + 1U;

#line 1516
        }

#line 1509
    }
    else
    {

#line 1525
        float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 128.0f);
        float _S99 = tw_1.x;

#line 1526
        float _S100 = tw_1.y;

#line 1526
        k2_2 = 0U;

#line 1526
        float cr_0 = 1.0f;

#line 1526
        float ci_0 = 0.0f;

        for(;;)
        {

#line 1528
            if(k2_2 < 16U)
            {
            }
            else
            {

#line 1528
                break;
            }

#line 1529
            cmulw_0(&re_9[k2_2], &im_9[k2_2], half(cr_0), half(ci_0));
            float nr_0 = cr_0 * _S99 - ci_0 * _S100;
            float _S101 = cr_0 * _S100 + ci_0 * _S99;

#line 1528
            k2_2 = k2_2 + 1U;

#line 1528
            cr_0 = nr_0;

#line 1528
            ci_0 = _S101;

#line 1528
        }

#line 1509
    }

#line 1535
    uint per_2 = 16U / max(8U, 1U);
    uint _S102 = max(0U, 1U);
    uint blk2_2 = tid_2 / _S102;

#line 1537
    uint lane2_2 = tid_2 % _S102;

#line 1537
    exchangeS_0(&re_9, &im_9, lgLn_0, lgTB_0, 8U, 128U, blk_2, lane_2, per_2, _S102, 8U, blk2_2, lane2_2, kernelContext_6);


    innermostS_0(&re_9, &im_9);

#line 1559
    if(thrBits_2 != 0U)
    {

#line 1560
        float _S103 = (as_type<float>((thrBits_2)));

#line 1560
        thread array<half2, int(16)> _S104 = re_9;

#line 1560
        thread array<half2, int(16)> _S105 = im_9;

#line 1560
        peakTwoGate_0(pairA_2, pairB_2, tid_2, &_S104, &_S105, peakIdx_2, peakVal_2, winStart_4, winEnd_4, _S103, kernelContext_6);

#line 1559
    }
    else
    {

#line 1559
        thread array<half2, int(16)> _S106 = re_9;

#line 1559
        thread array<half2, int(16)> _S107 = im_9;

#line 1559
        peakTwoWave_0(pairA_2, pairB_2, tid_2, &_S106, &_S107, peakIdx_2, peakVal_2, winStart_4, winEnd_4, thrBits_2, kernelContext_6);

#line 1559
    }

#line 1597
    return;
}


void filterPair_0(uint pair_0, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_3, packed_float2 device* peakVal_3, uint ntmpl_1, uint winStart_5, uint winEnd_5, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, KernelContext_0 thread* kernelContext_7)
{

#line 1601
    thread uint _S108 = winStart_5;

#line 1601
    thread uint _S109 = winEnd_5;

#line 1607
    kernelContext_7->_tid_0 = tid_3;

#line 1627
    uint tiles_0 = (ntmpl_1 + 8U - 1U) / 8U;
    uint slots_0 = binsize_1 * tiles_0;
    bool slotOk_0 = pair_0 < slots_0;

#line 1629
    uint q_1;
    if(slotOk_0)
    {

#line 1630
        q_1 = pair_0;

#line 1630
    }
    else
    {

#line 1630
        q_1 = slots_0 - 1U;

#line 1630
    }
    uint d_5 = q_1 / tiles_0;

#line 1631
    uint t0_0 = (q_1 - d_5 * tiles_0) * 8U;
    uint _S110 = d_5 * ntmpl_1 + t0_0;
    rowWindow_0(d_5, &_S108, &_S109);

#line 1657
    thread array<half2, int(16)> dreg_1;

#line 1657
    uint n2_1 = 0U;

    for(;;)
    {

#line 1659
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1659
            break;
        }

#line 1660
        dreg_1[n2_1] = dload_0(data_0, d_5 * 128U + tid_3 + 8U * n2_1);

#line 1659
        n2_1 = n2_1 + 1U;

#line 1659
    }

#line 1659
    uint k_1 = 0U;

#line 1667
    for(;;)
    {

#line 1667
        if(k_1 < 8U)
        {
        }
        else
        {

#line 1667
            break;
        }

#line 1667
        bool okA_0;
        if(slotOk_0)
        {

#line 1668
            okA_0 = (t0_0 + k_1) < ntmpl_1;

#line 1668
        }
        else
        {

#line 1668
            okA_0 = false;

#line 1668
        }

#line 1668
        bool okB_0;

#line 1668
        if(slotOk_0)
        {

#line 1668
            okB_0 = (t0_0 + k_1 + 1U) < ntmpl_1;

#line 1668
        }
        else
        {

#line 1668
            okB_0 = false;

#line 1668
        }
        if(okA_0)
        {

#line 1669
            q_1 = _S110 + k_1;

#line 1669
        }
        else
        {

#line 1669
            q_1 = 4294967295U;

#line 1669
        }

#line 1669
        if(okB_0)
        {

#line 1669
            n2_1 = _S110 + k_1 + 1U;

#line 1669
        }
        else
        {

#line 1669
            n2_1 = 4294967295U;

#line 1669
        }
        uint _S111 = t0_0 + k_1;

#line 1670
        uint _S112 = ntmpl_1 - 1U;

#line 1670
        uint _S113 = min(_S111, _S112);

#line 1670
        uint _S114 = min(_S111 + 1U, _S112);

#line 1670
        thread array<half2, int(16)> _S115 = dreg_1;

#line 1670
        filterTwo_0(q_1, n2_1, _S113, _S114, tid_3, &_S115, tmpl_1, peakIdx_3, peakVal_3, _S108, _S109, thrBits_3, kernelContext_7);

#line 1667
        k_1 = k_1 + 2U;

#line 1667
    }

#line 1683
    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], uint _builtinWaveLaneIndex_0 [[thread_index_in_simdgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1687
    thread KernelContext_0 kernelContext_8;

#line 1687
    (&kernelContext_8)->entryPointParams_0 = entryPointParams_1;

#line 1687
    (&kernelContext_8)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1687
    (&kernelContext_8)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1687
    (&kernelContext_8)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1687
    (&kernelContext_8)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1687
    threadgroup array<uint, int(512)> stg_1;

#line 1687
    (&kernelContext_8)->stg_0 = &stg_1;

#line 1687
    (&kernelContext_8)->_S8 = _builtinWaveLaneIndex_0;

#line 1707
    uint _S116 = lid_0.x;

#line 1707
    uint _sub_0 = _S116 / 8U;
    uint _pr_0 = gid_0.x * 4U + _sub_0;

#line 1708
    uint _t_0 = _S116 % 8U;
    (&kernelContext_8)->_stgBase_0 = _sub_0 * 128U;

#line 1709
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_8);



    return;
}
