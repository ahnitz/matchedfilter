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

#line 11 "mm_256_fusedTierB_c16t4.slang"
constant array<uint, int(256)> COARSE_TWT_DATA_0 = { { 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 15360U, 642268159U, 709377022U, 750074874U, 776354806U, 802569201U, 816987114U, 830028770U, 842939353U, 855849934U, 868629443U, 876886966U, 883243944U, 889535385U, 895761288U, 901921655U, 15360U, 709377022U, 776354806U, 816987114U, 842939353U, 868629443U, 883243944U, 895761288U, 908016484U, 920075067U, 931871502U, 941439709U, 947010215U, 952384109U, 957561391U, 962542061U, 15360U, 750074874U, 816987114U, 855849934U, 883243944U, 901921655U, 920075067U, 937638646U, 947010215U, 955005519U, 962542061U, 969619844U, 976173331U, 982136987U, 987576349U, 992294706U, 15360U, 776354806U, 842939353U, 883243944U, 908016484U, 931871502U, 947010215U, 957561391U, 967326120U, 976173331U, 984037490U, 990787467U, 996423199U, 1000879269U, 1004089918U, 1005989446U, 15360U, 802569201U, 868629443U, 901921655U, 931871502U, 949697162U, 962542061U, 974076218U, 984037490U, 992294706U, 998782308U, 1003369219U, 1005989446U, 1006609992U, 1005236402U, 1001829444U, 15360U, 816987114U, 883243944U, 920075067U, 947010215U, 962542061U, 976173331U, 987576349U, 996423199U, 1002648518U, 1005989446U, 1006545480U, 1004122686U, 998815076U, 990820235U, 980269252U, 15360U, 830028770U, 895761288U, 937638646U, 957561391U, 974076218U, 987576349U, 997668290U, 1004089918U, 1006577224U, 1005236402U, 999929093U, 990820235U, 978303212U, 962574829U, 944290498U, 15360U, 842939353U, 908016484U, 947010215U, 967326120U, 984037490U, 996423199U, 1004089918U, 1006632960U, 1004122686U, 996455967U, 984070258U, 967358888U, 947042983U, 908049252U, 842972121U, 15360U, 855849934U, 920075067U, 955005519U, 976173331U, 992294706U, 1002648518U, 1006577224U, 1004122686U, 995145340U, 980269252U, 960150031U, 931904270U, 876919734U, 709409790U, 2977545186U, 15360U, 868629443U, 931871502U, 962542061U, 984037490U, 998782308U, 1005989446U, 1005236402U, 996455967U, 980269252U, 957594159U, 920107835U, 842972121U, 2856893438U, 3030760360U, 3088956125U, 15360U, 876886966U, 941439709U, 969619844U, 990787467U, 1003369219U, 1006545480U, 999929093U, 984070258U, 960150031U, 920107835U, 830061538U, 2923871222U, 3049438071U, 3099900525U, 3125786860U, 15360U, 883243944U, 947010215U, 976173331U, 996423199U, 1005989446U, 1004122686U, 990820235U, 967358888U, 931904270U, 842972121U, 2923871222U, 3055532900U, 3105077807U, 3131553906U, 3148395685U, 15360U, 889535385U, 952384109U, 982136987U, 1000879269U, 1006609992U, 998815076U, 978303212U, 947042983U, 876919734U, 2856893438U, 3049438071U, 3105077807U, 3133323336U, 3150164934U, 3153734837U, 15360U, 895761288U, 957561391U, 987576349U, 1004089918U, 1005236402U, 990820235U, 962574829U, 908049252U, 709409790U, 3030760360U, 3099900525U, 3131553906U, 3150164934U, 3153473094U, 3141220055U, 15360U, 901921655U, 962542061U, 992294706U, 1005989446U, 1001829444U, 980269252U, 944290498U, 842972121U, 2977545186U, 3088956125U, 3125786860U, 3148395685U, 3153734837U, 3141220055U, 3112450507U } };

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


#line 196 "mm_256_fusedTierB_c16t4.slang"
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


#line 395
void dft16s_1(array<half2, int(16)> thread* re_3, array<half2, int(16)> thread* im_3)
{

#line 395
    uint n1_1 = 0U;

    for(;;)
    {

#line 397
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 397
            break;
        }

#line 397
        r4s_0(re_3, im_3, n1_1, n1_1 + 4U, n1_1 + 8U, n1_1 + 12U);

#line 397
        n1_1 = n1_1 + 1U;

#line 397
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

#line 408
    uint k2_1 = 0U;
    for(;;)
    {

#line 409
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 409
            break;
        }

#line 410
        uint _S5 = 4U * k2_1;

#line 410
        r4s_0(re_3, im_3, _S5, _S5 + 1U, _S5 + 2U, _S5 + 3U);

#line 409
        k2_1 = k2_1 + 1U;

#line 409
    }

    swap2_0(re_3, im_3, 1U, 4U);

#line 411
    swap2_0(re_3, im_3, 2U, 8U);

#line 411
    swap2_0(re_3, im_3, 3U, 12U);
    swap2_0(re_3, im_3, 6U, 9U);

#line 412
    swap2_0(re_3, im_3, 7U, 13U);

#line 412
    swap2_0(re_3, im_3, 11U, 14U);
    return;
}


#line 52 "twiddle.slang"
uint mfCoarseTwtFlag_0()
{
    ;
    uint _S6 = ((MF_COARSE_TWT));

#line 55
    return _S6;
}


#line 84
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 271 "mm_256_fusedTierB_c16t4.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S7 = max(TB_0, 1U);

#line 273
    uint j_0 = d_2 / _S7;

#line 273
    uint m_0 = d_2 % _S7;

#line 273
    uint _S8;
    if(TB_0 <= 16U)
    {

#line 274
        _S8 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 274
    }
    else
    {

#line 274
        _S8 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 274
    }

#line 274
    return _S8;
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
    uint _S9;
};


#line 247 "mm_256_fusedTierB_c16t4.slang"
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
void exchangeS_0(array<half2, int(16)> thread* re_4, array<half2, int(16)> thread* im_4, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
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
        half2 _S10 = half2(float2(0.0f) );

#line 438
        outr_0[z_0] = _S10;

#line 438
        outi_0[z_0] = _S10;

#line 438
        z_0 = z_0 + 1U;

#line 438
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;
    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S11 = p0_0 & lenMask_0;
    uint _S12 = (_S11 >> lgSpan_0) * 16U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S11 & spanMask_0);

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
                        uint _S13 = j_1 * 16U + kernelContext_2->_tid_0;

#line 448
                        stgPut_0(_S13, (*re_4)[c_1 * 16U + j_1], kernelContext_2);

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
                        uint _S14 = pz_0 & lenMask_0;
                        uint az_0 = (_S14 >> lgSpan_0) * 16U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);

#line 454
                        half2 _S15 = stgGet_0(_S12 + az_0 - c_1 * 16U * 16U, kernelContext_2);



                        outr_0[d_3] = _S15;

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
                        uint _S16 = j_2 * 16U + kernelContext_2->_tid_0;

#line 448
                        stgPut_0(_S16, (*im_4)[c_1 * 16U + j_2], kernelContext_2);

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
                        uint _S17 = pz_1 & lenMask_0;
                        uint az_1 = (_S17 >> lgSpan_0) * 16U + ((pz_1 >> lgLen_0) << lgSpan_0) + (_S17 & spanMask_0);

#line 454
                        half2 _S18 = stgGet_0(_S12 + az_1 - c_1 * 16U * 16U, kernelContext_2);



                        outi_0[d_4] = _S18;

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
        (*re_4)[j_1] = outr_0[j_1];

#line 463
        (*im_4)[j_1] = outi_0[j_1];

#line 463
        j_1 = j_1 + 1U;

#line 463
    }
    return;
}


#line 466
void innermostS_0(array<half2, int(16)> thread* re_5, array<half2, int(16)> thread* im_5)
{
    dft16s_1(re_5, im_5);



    return;
}


#line 759
uint lgOf_0(uint i_4)
{

#line 759
    uint _S19;

#line 759
    if(i_4 < 1U)
    {

#line 759
        _S19 = 4U;

#line 759
    }
    else
    {

#line 759
        if(i_4 == 1U)
        {

#line 759
            _S19 = 4U;

#line 759
        }
        else
        {

#line 759
            _S19 = 1U;

#line 759
        }

#line 759
    }

#line 759
    return _S19;
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
uint mfShflXor_0(uint v_1, uint s_0, KernelContext_0 thread* kernelContext_3)
{

#line 1313
    uint _S20 = (simd_shuffle((v_1), ushort((int((kernelContext_3->_S9) ^ s_0)))));

#line 1313
    return _S20;
}


#line 66 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S21 = ((MF_C16_RAW));

#line 69
    return _S21;
}


#line 1434 "mm_256_fusedTierB_c16t4.slang"
void peakTwoGate_0(uint pairA_0, uint pairB_0, uint tid_0, const array<half2, int(16)> thread* re_7, const array<half2, int(16)> thread* im_7, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, float thr_0, KernelContext_0 thread* kernelContext_4)
{


    uint _S22 = slotToIndex_0(tid_0 * 16U) - winStart_2;
    uint _S23 = winEnd_2 - winStart_2;
    half2 _S24 = half2(float2(0.0f) );
    half2 _S25 = half2(float2(0.015625f) );

#line 1441
    uint i_5 = 0U;

#line 1441
    half2 best_0 = _S24;

#line 1441
    half2 en_0 = _S24;
    for(;;)
    {

#line 1442
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1442
            break;
        }

#line 1442
        half2 _S26;

        if((_S22 + slotToIndex_0(i_5)) < _S23)
        {

#line 1444
            _S26 = mag2s_0((*re_7)[i_5], (*im_7)[i_5]);

#line 1444
        }
        else
        {

#line 1444
            _S26 = _S24;

#line 1444
        }

#line 1444
        half2 _S27 = max(best_0, _S26);
        half2 sr_0 = (*re_7)[i_5] * _S25;

#line 1445
        half2 si_0 = (*im_7)[i_5] * _S25;
        half2 en_1 = en_0 + (sr_0 * sr_0 + si_0 * si_0);

#line 1442
        i_5 = i_5 + 1U;

#line 1442
        best_0 = _S27;

#line 1442
        en_0 = en_1;

#line 1442
    }

#line 1442
    uint _S28 = mfShflXor_0((uint(as_type<ushort>(best_0[0U])) & 65535U) | (uint(as_type<ushort>(best_0[1U])) << 16U), 1U, kernelContext_4);

#line 1449
    half2 _S29 = max(best_0, half2(as_type<half>(ushort(_S28 & 65535U)), as_type<half>(ushort((_S28 >> 16U) & 65535U))));

#line 1449
    uint _S30 = mfShflXor_0((uint(as_type<ushort>(en_0[0U])) & 65535U) | (uint(as_type<ushort>(en_0[1U])) << 16U), 1U, kernelContext_4);
    half2 en_2 = en_0 + half2(as_type<half>(ushort(_S30 & 65535U)), as_type<half>(ushort((_S30 >> 16U) & 65535U)));

#line 1450
    uint _S31 = mfShflXor_0((uint(as_type<ushort>(_S29[0U])) & 65535U) | (uint(as_type<ushort>(_S29[1U])) << 16U), 2U, kernelContext_4);

#line 1449
    half2 _S32 = max(_S29, half2(as_type<half>(ushort(_S31 & 65535U)), as_type<half>(ushort((_S31 >> 16U) & 65535U))));

#line 1449
    uint _S33 = mfShflXor_0((uint(as_type<ushort>(en_2[0U])) & 65535U) | (uint(as_type<ushort>(en_2[1U])) << 16U), 2U, kernelContext_4);
    half2 en_3 = en_2 + half2(as_type<half>(ushort(_S33 & 65535U)), as_type<half>(ushort((_S33 >> 16U) & 65535U)));

#line 1450
    uint _S34 = mfShflXor_0((uint(as_type<ushort>(_S32[0U])) & 65535U) | (uint(as_type<ushort>(_S32[1U])) << 16U), 4U, kernelContext_4);

#line 1449
    half2 _S35 = max(_S32, half2(as_type<half>(ushort(_S34 & 65535U)), as_type<half>(ushort((_S34 >> 16U) & 65535U))));

#line 1449
    uint _S36 = mfShflXor_0((uint(as_type<ushort>(en_3[0U])) & 65535U) | (uint(as_type<ushort>(en_3[1U])) << 16U), 4U, kernelContext_4);
    half2 en_4 = en_3 + half2(as_type<half>(ushort(_S36 & 65535U)), as_type<half>(ushort((_S36 >> 16U) & 65535U)));

#line 1450
    uint _S37 = mfShflXor_0((uint(as_type<ushort>(_S35[0U])) & 65535U) | (uint(as_type<ushort>(_S35[1U])) << 16U), 8U, kernelContext_4);

#line 1449
    half2 best_1 = max(_S35, half2(as_type<half>(ushort(_S37 & 65535U)), as_type<half>(ushort((_S37 >> 16U) & 65535U))));

#line 1449
    uint _S38 = mfShflXor_0((uint(as_type<ushort>(en_4[0U])) & 65535U) | (uint(as_type<ushort>(en_4[1U])) << 16U), 8U, kernelContext_4);
    half2 en_5 = en_4 + half2(as_type<half>(ushort(_S38 & 65535U)), as_type<half>(ushort((_S38 >> 16U) & 65535U)));

#line 1450
    uint _S39 = (uint(as_type<ushort>(en_5[0U])) & 65535U) | (uint(as_type<ushort>(en_5[1U])) << 16U);

#line 1450
    uint _S40 = (uint(as_type<ushort>(best_1[0U])) & 65535U) | (uint(as_type<ushort>(best_1[1U])) << 16U);

#line 1450
    bool infA_0;

#line 1458
    if((_S39 & 31744U) == 31744U)
    {

#line 1458
        infA_0 = true;

#line 1458
    }
    else
    {

#line 1458
        infA_0 = (_S40 & 31744U) == 31744U;

#line 1458
    }

#line 1458
    bool infB_0;
    if((_S39 & 2080374784U) == 2080374784U)
    {

#line 1459
        infB_0 = true;

#line 1459
    }
    else
    {

#line 1459
        infB_0 = (_S40 & 2080374784U) == 2080374784U;

#line 1459
    }

#line 71 "twiddle.slang"
    uint _S41 = mfC16RawFlag_0();

#line 71
    float _S42;

#line 1462 "mm_256_fusedTierB_c16t4.slang"
    if((1U - _S41) != 0U)
    {

#line 1462
        _S42 = 12.66209983825683594f;

#line 1462
    }
    else
    {

#line 1462
        _S42 = 0.0f;

#line 1462
    }

#line 1462
    float k2_2 = _S42 * 0.00048828125f * 1.00010001659393311f;
    float mA_0 = sqrt(float(best_1.x));

#line 1463
    float mB_0 = sqrt(float(best_1.y));

    float bA_0 = mA_0 * 1.00107669830322266f + k2_2 * sqrt(float(en_5.x) * 16.0f);
    float bB_0 = mB_0 * 1.00107669830322266f + k2_2 * sqrt(float(en_5.y) * 16.0f);

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
    bool _S43 = tid_0 == 0U;

#line 1469
    bool _S44;

#line 1469
    if(_S43)
    {

#line 1469
        _S44 = pairA_0 != 4294967295U;

#line 1469
    }
    else
    {

#line 1469
        _S44 = false;

#line 1469
    }

#line 1469
    int _S45;

#line 1469
    float2 _S46;

#line 1469
    if(_S44)
    {

#line 1470
        int device* _S47 = peakIdx_0+pairA_0;

#line 1470
        if(hitA_0)
        {

#line 1470
            _S45 = int(0);

#line 1470
        }
        else
        {

#line 1470
            _S45 = int(-1);

#line 1470
        }

#line 1470
        *_S47 = _S45;

#line 1470
        packed_float2 device* _S48 = peakVal_0+pairA_0;
        if(infA_0)
        {

#line 1471
            _S46 = float2(3.40282306073709653e+38f, 0.0f);

#line 1471
        }
        else
        {

#line 1471
            if(hitA_0)
            {

#line 1471
                _S46 = float2(bA_0, 0.0f);

#line 1471
            }
            else
            {

#line 1471
                _S46 = float2(0.0f, 0.0f);

#line 1471
            }

#line 1471
        }

#line 1471
        *_S48 = packed_float2(_S46) ;

#line 1469
    }



    if(_S43)
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
        int device* _S49 = peakIdx_0+pairB_0;

#line 1474
        if(hitB_0)
        {

#line 1474
            _S45 = int(0);

#line 1474
        }
        else
        {

#line 1474
            _S45 = int(-1);

#line 1474
        }

#line 1474
        *_S49 = _S45;

#line 1474
        packed_float2 device* _S50 = peakVal_0+pairB_0;
        if(infB_0)
        {

#line 1475
            _S46 = float2(3.40282306073709653e+38f, 0.0f);

#line 1475
        }
        else
        {

#line 1475
            if(hitB_0)
            {

#line 1475
                _S46 = float2(bB_0, 0.0f);

#line 1475
            }
            else
            {

#line 1475
                _S46 = float2(0.0f, 0.0f);

#line 1475
            }

#line 1475
        }

#line 1475
        *_S50 = packed_float2(_S46) ;

#line 1473
    }



    return;
}


#line 300
float2 c16Bound_0(float2 v_2, float energy_0)
{

#line 71 "twiddle.slang"
    uint _S51 = mfC16RawFlag_0();

#line 302 "mm_256_fusedTierB_c16t4.slang"
    if((1U - _S51) == 0U)
    {

#line 302
        return v_2;
    }

#line 303
    float m_1 = length(v_2);
    float b_3 = m_1 * 1.00146484375f + 0.00618266593664885f * sqrt(energy_0);

#line 304
    float2 _S52;
    if(m_1 > 0.0f)
    {

#line 305
        _S52 = v_2 * float2((b_3 / m_1)) ;

#line 305
    }
    else
    {

#line 305
        _S52 = float2(b_3, 0.0f);

#line 305
    }

#line 305
    return _S52;
}


#line 1316
void peakTwoWave_0(uint pairA_1, uint pairB_1, uint tid_1, const array<half2, int(16)> thread* re_8, const array<half2, int(16)> thread* im_8, int device* peakIdx_1, packed_float2 device* peakVal_1, uint winStart_3, uint winEnd_3, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{
    uint m_2;

#line 1318
    bool _S53;

#line 1318
    bool _S54;

    uint _S55 = slotToIndex_0(tid_1 * 16U) - winStart_3;
    uint _S56 = winEnd_3 - winStart_3;

#line 1328
    half2 _S57 = half2(float2(0.0f) );
    half2 _S58 = half2(float2(0.015625f) );

#line 1329
    uint i_6 = 0U;

#line 1329
    half2 en_6 = _S57;

#line 1329
    uint ovAcc_0 = 0U;

#line 1329
    uint kA_0 = 0U;

#line 1329
    uint kB_0 = 0U;



    for(;;)
    {

#line 1333
        if(i_6 < 16U)
        {
        }
        else
        {

#line 1333
            break;
        }
        half2 mg_0 = mag2s_0((*re_8)[i_6], (*im_8)[i_6]);
        half2 sr_1 = (*re_8)[i_6] * _S58;

#line 1336
        half2 si_1 = (*im_8)[i_6] * _S58;
        half2 en_7 = en_6 + (sr_1 * sr_1 + si_1 * si_1);
        if((_S55 + slotToIndex_0(i_6)) < _S56)
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
        uint ovAcc_1 = ovAcc_0 | (((((uint(as_type<ushort>((*re_8)[i_6].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[i_6].y)) << 16U)) & 2080406528U) + 67109888U) | ((((uint(as_type<ushort>((*im_8)[i_6].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[i_6].y)) << 16U)) & 2080406528U) + 67109888U));


        uint _S59 = 15U - i_6;

#line 1347
        uint _S60 = max(kA_0, (m_2 << 16U) | _S59);
        uint _S61 = max(kB_0, (m_2 & 4294901760U) | _S59);

#line 1333
        i_6 = i_6 + 1U;

#line 1333
        en_6 = en_7;

#line 1333
        ovAcc_0 = ovAcc_1;

#line 1333
        kA_0 = _S60;

#line 1333
        kB_0 = _S61;

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


    uint _S62 = (4095U - tid_1) << 4U;

#line 1356
    uint kA_1 = kA_0 | _S62;
    uint kB_1 = kB_0 | _S62;

#line 1357
    uint _S63 = mfShflXor_0(kA_1, 1U, kernelContext_5);

    uint _S64 = max(kA_1, _S63);

#line 1359
    uint _S65 = mfShflXor_0(kB_1, 1U, kernelContext_5);
    uint _S66 = max(kB_1, _S65);

#line 1360
    uint _S67 = mfShflXor_0((uint(as_type<ushort>(en_6[0U])) & 65535U) | (uint(as_type<ushort>(en_6[1U])) << 16U), 1U, kernelContext_5);
    half2 en_8 = en_6 + half2(as_type<half>(ushort(_S67 & 65535U)), as_type<half>(ushort((_S67 >> 16U) & 65535U)));

#line 1361
    uint _S68 = mfShflXor_0(_S64, 2U, kernelContext_5);

#line 1359
    uint _S69 = max(_S64, _S68);

#line 1359
    uint _S70 = mfShflXor_0(_S66, 2U, kernelContext_5);
    uint _S71 = max(_S66, _S70);

#line 1360
    uint _S72 = mfShflXor_0((uint(as_type<ushort>(en_8[0U])) & 65535U) | (uint(as_type<ushort>(en_8[1U])) << 16U), 2U, kernelContext_5);
    half2 en_9 = en_8 + half2(as_type<half>(ushort(_S72 & 65535U)), as_type<half>(ushort((_S72 >> 16U) & 65535U)));

#line 1361
    uint _S73 = mfShflXor_0(_S69, 4U, kernelContext_5);

#line 1359
    uint _S74 = max(_S69, _S73);

#line 1359
    uint _S75 = mfShflXor_0(_S71, 4U, kernelContext_5);
    uint _S76 = max(_S71, _S75);

#line 1360
    uint _S77 = mfShflXor_0((uint(as_type<ushort>(en_9[0U])) & 65535U) | (uint(as_type<ushort>(en_9[1U])) << 16U), 4U, kernelContext_5);
    half2 en_10 = en_9 + half2(as_type<half>(ushort(_S77 & 65535U)), as_type<half>(ushort((_S77 >> 16U) & 65535U)));

#line 1361
    uint _S78 = mfShflXor_0(_S74, 8U, kernelContext_5);

#line 1359
    uint _S79 = max(_S74, _S78);

#line 1359
    uint _S80 = mfShflXor_0(_S76, 8U, kernelContext_5);
    uint _S81 = max(_S76, _S80);

#line 1360
    uint _S82 = mfShflXor_0((uint(as_type<ushort>(en_10[0U])) & 65535U) | (uint(as_type<ushort>(en_10[1U])) << 16U), 8U, kernelContext_5);
    half2 en_11 = en_10 + half2(as_type<half>(ushort(_S82 & 65535U)), as_type<half>(ushort((_S82 >> 16U) & 65535U)));



    float enA_0 = float(en_11.x) * 16.0f;

#line 1365
    float enB_0 = float(en_11.y) * 16.0f;
    uint slotA_0 = 65535U - (_S79 & 65535U);

#line 1366
    uint slotB_0 = 65535U - (_S81 & 65535U);

#line 1372
    uint _S83 = _S79 >> 16U;

#line 1372
    bool infA_1 = _S83 >= 31744U;

#line 1372
    uint _S84 = _S81 >> 16U;

#line 1372
    bool infB_1 = _S84 >= 31744U;

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
        hitA_1 = (as_type<half>((ushort)((_S83)))) > (as_type<float>((thrBits_1)));

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
        hitB_1 = (as_type<half>((ushort)((_S84)))) > (as_type<float>((thrBits_1)));

#line 1377
    }

#line 1385
    uint _S85 = slotA_0 >> 4U;

#line 1385
    uint _S86 = slotA_0 & 15U;

#line 1385
    uint _S87 = slotB_0 >> 4U;

#line 1385
    uint _S88 = slotB_0 & 15U;
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
                                (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + m_2 * 16U + tid_1] = (uint(as_type<ushort>((*re_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*re_8)[m_2].y)) << 16U);

#line 1391
                                m_2 = m_2 + 1U;

#line 1391
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            bool _S89 = tid_1 == 0U;

#line 1394
                            _S53 = _S89;

#line 1394
                            if(_S89)
                            {

#line 1395
                                if(_S86 >= 0U)
                                {

#line 1395
                                    _S54 = _S86 < 16U;

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
                                    vA_0[0U] = (as_type<half>((ushort)(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S86 * 16U + _S85]))));

#line 1395
                                }

                                if(_S88 >= 0U)
                                {

#line 1397
                                    _S54 = _S88 < 16U;

#line 1397
                                }
                                else
                                {

#line 1397
                                    _S54 = false;

#line 1397
                                }

#line 1397
                                if(_S54)
                                {

#line 1398
                                    vB_0[0U] = (as_type<half>((ushort)((((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S88 * 16U + _S87]) >> 16U))));

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
                                (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + m_2 * 16U + tid_1] = (uint(as_type<ushort>((*im_8)[m_2].x)) & 65535U) | (uint(as_type<ushort>((*im_8)[m_2].y)) << 16U);

#line 1391
                                m_2 = m_2 + 1U;

#line 1391
                            }

                            threadgroup_barrier(mem_flags::mem_threadgroup);
                            if(_S53)
                            {

#line 1395
                                if(_S86 >= 0U)
                                {

#line 1395
                                    _S54 = _S86 < 16U;

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
                                    vA_0[1U] = (as_type<half>((ushort)(((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S86 * 16U + _S85]))));

#line 1395
                                }

                                if(_S88 >= 0U)
                                {

#line 1397
                                    _S54 = _S88 < 16U;

#line 1397
                                }
                                else
                                {

#line 1397
                                    _S54 = false;

#line 1397
                                }

#line 1397
                                if(_S54)
                                {

#line 1398
                                    vB_0[1U] = (as_type<half>((ushort)((((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + _S88 * 16U + _S87]) >> 16U))));

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
    if(_S53)
    {

#line 1402
        _S54 = pairA_1 != 4294967295U;

#line 1402
    }
    else
    {

#line 1402
        _S54 = false;

#line 1402
    }

#line 1402
    int _S90;

#line 1402
    float2 _S91;

#line 1402
    if(_S54)
    {

#line 1403
        int device* _S92 = peakIdx_1+pairA_1;

#line 1403
        if(hitA_1)
        {

#line 1403
            _S90 = int(slotToIndex_0(slotA_0));

#line 1403
        }
        else
        {

#line 1403
            _S90 = int(-1);

#line 1403
        }

#line 1403
        *_S92 = _S90;

#line 1403
        packed_float2 device* _S93 = peakVal_1+pairA_1;
        if(infA_1)
        {

#line 1404
            _S91 = float2(3.40282306073709653e+38f, 0.0f);

#line 1404
        }
        else
        {

#line 1405
            if(hitA_1)
            {

#line 1405
                float2 _S94 = c16Bound_0(float2(vA_0[int(0)], vA_0[int(1)]), enA_0);

#line 1405
                _S91 = _S94;

#line 1405
            }
            else
            {

#line 1405
                _S91 = float2(0.0f, 0.0f);

#line 1405
            }

#line 1404
        }

#line 1404
        *_S93 = packed_float2(_S91) ;

#line 1402
    }

#line 1407
    if(_S53)
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
        int device* _S95 = peakIdx_1+pairB_1;

#line 1408
        if(hitB_1)
        {

#line 1408
            _S90 = int(slotToIndex_0(slotB_0));

#line 1408
        }
        else
        {

#line 1408
            _S90 = int(-1);

#line 1408
        }

#line 1408
        *_S95 = _S90;

#line 1408
        packed_float2 device* _S96 = peakVal_1+pairB_1;
        if(infB_1)
        {

#line 1409
            _S91 = float2(3.40282306073709653e+38f, 0.0f);

#line 1409
        }
        else
        {

#line 1410
            if(hitB_1)
            {

#line 1410
                float2 _S97 = c16Bound_0(float2(vB_0[int(0)], vB_0[int(1)]), enB_0);

#line 1410
                _S91 = _S97;

#line 1410
            }
            else
            {

#line 1410
                _S91 = float2(0.0f, 0.0f);

#line 1410
            }

#line 1409
        }

#line 1409
        *_S96 = packed_float2(_S91) ;

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
        uint _S98 = 16U * n2_0;

#line 1490
        half2 ta_0 = cload_0(tmpl_0, tA_0 * 256U + tid_2 + _S98);
        half2 tb_0 = cload_0(tmpl_0, tB_0 * 256U + tid_2 + _S98);
        half _S99 = (*dreg_0)[n2_0].x;
        half _S100 = (*dreg_0)[n2_0].y;


        cmulconjs_0(half2(_S99, _S99), half2(_S100, _S100), half2(ta_0.x, tb_0.x), half2(ta_0.y, tb_0.y), &re_9[n2_0], &im_9[n2_0]);

#line 1489
        n2_0 = n2_0 + 1U;

#line 1489
    }

#line 1502
    uint lgTB_0 = firstbithigh_0(16U);
    uint lgLn_0 = firstbithigh_0(256U);
    uint blk_2 = tid_2 >> lgTB_0;
    uint lane_2 = tid_2 & 15U;

    dft16s_0(&re_9, &im_9);

#line 57 "twiddle.slang"
    uint _S101 = mfCoarseTwtFlag_0();

#line 57
    uint k2_3;

#line 1509 "mm_256_fusedTierB_c16t4.slang"
    if(_S101 != 0U)
    {

#line 1509
        k2_3 = 0U;

#line 1516
        for(;;)
        {

#line 1516
            if(k2_3 < 16U)
            {
            }
            else
            {

#line 1516
                break;
            }

#line 1517
            uint _S102 = lane_2 * 16U + k2_3;
            cmulw_0(&re_9[k2_3], &im_9[k2_3], as_type<half>(ushort((COARSE_TWT_DATA_0[_S102]) & 65535U)), as_type<half>(ushort(((COARSE_TWT_DATA_0[_S102]) >> 16U) & 65535U)));

#line 1516
            k2_3 = k2_3 + 1U;

#line 1516
        }

#line 1509
    }
    else
    {

#line 1525
        float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 256.0f);
        float _S103 = tw_0.x;

#line 1526
        float _S104 = tw_0.y;

#line 1526
        k2_3 = 0U;

#line 1526
        float cr_0 = 1.0f;

#line 1526
        float ci_0 = 0.0f;

        for(;;)
        {

#line 1528
            if(k2_3 < 16U)
            {
            }
            else
            {

#line 1528
                break;
            }

#line 1529
            cmulw_0(&re_9[k2_3], &im_9[k2_3], half(cr_0), half(ci_0));
            float nr_0 = cr_0 * _S103 - ci_0 * _S104;
            float _S105 = cr_0 * _S104 + ci_0 * _S103;

#line 1528
            k2_3 = k2_3 + 1U;

#line 1528
            cr_0 = nr_0;

#line 1528
            ci_0 = _S105;

#line 1528
        }

#line 1509
    }

#line 1535
    uint per_2 = 16U / max(16U, 1U);
    uint _S106 = max(1U, 1U);
    uint blk2_2 = tid_2 / _S106;

#line 1537
    uint lane2_2 = tid_2 % _S106;

#line 1537
    exchangeS_0(&re_9, &im_9, lgLn_0, lgTB_0, 16U, 256U, blk_2, lane_2, per_2, _S106, 16U, blk2_2, lane2_2, kernelContext_6);


    innermostS_0(&re_9, &im_9);

#line 1559
    if(thrBits_2 != 0U)
    {

#line 1560
        float _S107 = (as_type<float>((thrBits_2)));

#line 1560
        thread array<half2, int(16)> _S108 = re_9;

#line 1560
        thread array<half2, int(16)> _S109 = im_9;

#line 1560
        peakTwoGate_0(pairA_2, pairB_2, tid_2, &_S108, &_S109, peakIdx_2, peakVal_2, winStart_4, winEnd_4, _S107, kernelContext_6);

#line 1559
    }
    else
    {

#line 1559
        thread array<half2, int(16)> _S110 = re_9;

#line 1559
        thread array<half2, int(16)> _S111 = im_9;

#line 1559
        peakTwoWave_0(pairA_2, pairB_2, tid_2, &_S110, &_S111, peakIdx_2, peakVal_2, winStart_4, winEnd_4, thrBits_2, kernelContext_6);

#line 1559
    }

#line 1597
    return;
}


void filterPair_0(uint pair_0, uint tid_3, uint device* data_0, uint device* tmpl_1, int device* peakIdx_3, packed_float2 device* peakVal_3, uint ntmpl_1, uint winStart_5, uint winEnd_5, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_3, KernelContext_0 thread* kernelContext_7)
{

#line 1601
    thread uint _S112 = winStart_5;

#line 1601
    thread uint _S113 = winEnd_5;

#line 1607
    kernelContext_7->_tid_0 = tid_3;

#line 1627
    uint tiles_0 = (ntmpl_1 + 4U - 1U) / 4U;
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
    uint t0_0 = (q_1 - d_5 * tiles_0) * 4U;
    uint _S114 = d_5 * ntmpl_1 + t0_0;
    rowWindow_0(d_5, &_S112, &_S113);

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
        dreg_1[n2_1] = dload_0(data_0, d_5 * 256U + tid_3 + 16U * n2_1);

#line 1659
        n2_1 = n2_1 + 1U;

#line 1659
    }

#line 1659
    uint k_0 = 0U;

#line 1667
    for(;;)
    {

#line 1667
        if(k_0 < 4U)
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
            okA_0 = (t0_0 + k_0) < ntmpl_1;

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
            okB_0 = (t0_0 + k_0 + 1U) < ntmpl_1;

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
            q_1 = _S114 + k_0;

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
            n2_1 = _S114 + k_0 + 1U;

#line 1669
        }
        else
        {

#line 1669
            n2_1 = 4294967295U;

#line 1669
        }
        uint _S115 = t0_0 + k_0;

#line 1670
        uint _S116 = ntmpl_1 - 1U;

#line 1670
        uint _S117 = min(_S115, _S116);

#line 1670
        uint _S118 = min(_S115 + 1U, _S116);

#line 1670
        thread array<half2, int(16)> _S119 = dreg_1;

#line 1670
        filterTwo_0(q_1, n2_1, _S117, _S118, tid_3, &_S119, tmpl_1, peakIdx_3, peakVal_3, _S112, _S113, thrBits_3, kernelContext_7);

#line 1667
        k_0 = k_0 + 2U;

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
    threadgroup array<uint, int(256)> stg_1;

#line 1687
    (&kernelContext_8)->stg_0 = &stg_1;

#line 1687
    (&kernelContext_8)->_S9 = _builtinWaveLaneIndex_0;

#line 1704
    uint _pr_0 = gid_0.x;

#line 1704
    uint _t_0 = lid_0.x;
    (&kernelContext_8)->_stgBase_0 = 0U;

#line 1705
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_8);

#line 1713
    return;
}
