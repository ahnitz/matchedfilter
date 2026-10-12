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


#line 197 "mm_256_fusedTierB_c16p16.slang"
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


#line 269
half2 cmulConj_0(half2 a_0, half2 b_2)
{

#line 269
    half _S2 = a_0.x;

#line 269
    half _S3 = b_2.x;

#line 269
    half _S4 = a_0.y;

#line 269
    half _S5 = b_2.y;

#line 269
    return half2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 474
void r4_0(half2 thread* a_1, half2 thread* b_3, half2 thread* c_0, half2 thread* d_1)
{
    half2 t0_0 = *a_1 + *c_0;

#line 476
    half2 t1_0 = *a_1 - *c_0;

#line 476
    half2 t2_0 = *b_3 + *d_1;

#line 476
    half2 t3_0 = *b_3 - *d_1;
    half2 j3_0 = half2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 478
    *b_3 = t1_0 + j3_0;

#line 478
    *c_0 = t0_0 - t2_0;

#line 478
    *d_1 = t1_0 - j3_0;
    return;
}


#line 268
half2 cmul_0(half2 a_2, half2 b_4)
{

#line 268
    half _S6 = a_2.x;

#line 268
    half _S7 = b_4.x;

#line 268
    half _S8 = a_2.y;

#line 268
    half _S9 = b_4.y;

#line 268
    return half2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 510
void dft16_0(array<half2, int(16)> thread* r_0)
{
    half2 W1_0 = half2(0.923828125, 0.382568359375);
    half2 W2_0 = half2(0.70703125, 0.70703125);
    half2 W3_0 = half2(0.382568359375, 0.923828125);
    half2 W4_0 = half2(0.0, 1.0);
    half2 W6_0 = half2(-0.70703125, 0.70703125);
    half2 W9_0 = half2(-0.923828125, -0.382568359375);

#line 517
    uint n1_0 = 0U;
    for(;;)
    {

#line 518
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 518
            break;
        }

#line 518
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 518
        n1_0 = n1_0 + 1U;

#line 518
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 519
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 519
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 520
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 520
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 521
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 521
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 521
    uint k2_0 = 0U;
    for(;;)
    {

#line 522
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 522
            break;
        }

#line 522
        uint _S10 = 4U * k2_0;

#line 522
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 522
        k2_0 = k2_0 + 1U;

#line 522
    }

    half2 t_0 = (*r_0)[int(1)];

#line 524
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 524
    (*r_0)[int(4)] = t_0;
    half2 t_1 = (*r_0)[int(2)];

#line 525
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 525
    (*r_0)[int(8)] = t_1;
    half2 t_2 = (*r_0)[int(3)];

#line 526
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 526
    (*r_0)[int(12)] = t_2;
    half2 t_3 = (*r_0)[int(6)];

#line 527
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 527
    (*r_0)[int(9)] = t_3;
    half2 t_4 = (*r_0)[int(7)];

#line 528
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 528
    (*r_0)[int(13)] = t_4;
    half2 t_5 = (*r_0)[int(11)];

#line 529
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 529
    (*r_0)[int(14)] = t_5;
    return;
}


#line 510
void dft16_1(array<half2, int(16)> thread* r_1)
{
    half2 W1_1 = half2(0.923828125, 0.382568359375);
    half2 W2_1 = half2(0.70703125, 0.70703125);
    half2 W3_1 = half2(0.382568359375, 0.923828125);
    half2 W4_1 = half2(0.0, 1.0);
    half2 W6_1 = half2(-0.70703125, 0.70703125);
    half2 W9_1 = half2(-0.923828125, -0.382568359375);

#line 517
    uint n1_1 = 0U;
    for(;;)
    {

#line 518
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 518
            break;
        }

#line 518
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 518
        n1_1 = n1_1 + 1U;

#line 518
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 519
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 519
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 520
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 520
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 521
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 521
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 521
    uint k2_1 = 0U;
    for(;;)
    {

#line 522
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 522
            break;
        }

#line 522
        uint _S11 = 4U * k2_1;

#line 522
        r4_0(&(*r_1)[_S11], &(*r_1)[_S11 + 1U], &(*r_1)[_S11 + 2U], &(*r_1)[_S11 + 3U]);

#line 522
        k2_1 = k2_1 + 1U;

#line 522
    }

    half2 t_6 = (*r_1)[int(1)];

#line 524
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 524
    (*r_1)[int(4)] = t_6;
    half2 t_7 = (*r_1)[int(2)];

#line 525
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 525
    (*r_1)[int(8)] = t_7;
    half2 t_8 = (*r_1)[int(3)];

#line 526
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 526
    (*r_1)[int(12)] = t_8;
    half2 t_9 = (*r_1)[int(6)];

#line 527
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 527
    (*r_1)[int(9)] = t_9;
    half2 t_10 = (*r_1)[int(7)];

#line 528
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 528
    (*r_1)[int(13)] = t_10;
    half2 t_11 = (*r_1)[int(11)];

#line 529
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 529
    (*r_1)[int(14)] = t_11;
    return;
}


#line 64 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 270 "mm_256_fusedTierB_c16p16.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 272
    uint j_0 = d_2 / _S12;

#line 272
    uint m_0 = d_2 % _S12;

#line 272
    uint _S13;
    if(TB_0 <= 16U)
    {

#line 273
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 273
    }
    else
    {

#line 273
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 273
    }

#line 273
    return _S13;
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


#line 246 "mm_256_fusedTierB_c16p16.slang"
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


#line 699
void exchange_0(array<half2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 700
    uint j_1;

#line 711
    thread array<half2, int(16)> out_0;

#line 711
    uint z_0 = 0U;
    for(;;)
    {

#line 712
        if(z_0 < 16U)
        {
        }
        else
        {

#line 712
            break;
        }

#line 712
        out_0[z_0] = half2(0.0, 0.0);

#line 712
        z_0 = z_0 + 1U;

#line 712
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S14 = p0_0 & lenMask_0;

#line 718
    uint _S15 = (_S14 >> lgSpan_0) * 16U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S14 & spanMask_0);

#line 718
    uint c_1 = 0U;

    for(;;)
    {

#line 720
        if(c_1 < 1U)
        {
        }
        else
        {

#line 720
            break;
        }

#line 721
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 721
        j_1 = 0U;
        for(;;)
        {

#line 722
            if(j_1 < 16U)
            {
            }
            else
            {

#line 722
                break;
            }

#line 722
            stgPut_0(j_1 * 16U + kernelContext_2->_tid_0, (*r_2)[c_1 * 16U + j_1], kernelContext_2);

#line 722
            j_1 = j_1 + 1U;

#line 722
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 723
        uint d_3 = 0U;
        for(;;)
        {

#line 724
            if(d_3 < 16U)
            {
            }
            else
            {

#line 724
                break;
            }

#line 725
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S16 = pz_0 & lenMask_0;
            uint az_0 = (_S16 >> lgSpan_0) * 16U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 727
            half2 _S17 = stgGet_0(_S15 + az_0 - c_1 * 16U * 16U, kernelContext_2);


            out_0[d_3] = _S17;

#line 724
            d_3 = d_3 + 1U;

#line 724
        }

#line 720
        c_1 = c_1 + 1U;

#line 720
    }

#line 720
    j_1 = 0U;

#line 733
    for(;;)
    {

#line 733
        if(j_1 < 16U)
        {
        }
        else
        {

#line 733
            break;
        }

#line 733
        (*r_2)[j_1] = out_0[j_1];

#line 733
        j_1 = j_1 + 1U;

#line 733
    }
    return;
}


#line 613
void innermost_0(array<half2, int(16)> thread* r_3)
{

#line 620
    dft16_1(r_3);

#line 625
    return;
}


#line 789
void transform_0(array<half2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 789
    for(;;)
    {

#line 789
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(16U);
                uint lgLn_0 = firstbithigh_0(256U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 15U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 256.0);
                float _S18 = tw_0.x;

#line 27
                float _S19 = tw_0.y;

#line 27
                uint k2_2 = 0U;

#line 27
                float cr_0 = 1.0;

#line 27
                float ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], half2(half(cr_0), half(ci_0)));
                    float nr_0 = cr_0 * _S18 - ci_0 * _S19;
                    float _S20 = cr_0 * _S19 + ci_0 * _S18;

#line 29
                    k2_2 = k2_2 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S20;

#line 29
                }

#line 37
                uint per_2 = 16U / max(16U, 1U);
                uint _S21 = max(1U, 1U);
                uint blk2_2 = tid_0 / _S21;

#line 39
                uint lane2_2 = tid_0 % _S21;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 16U, 256U, blk_2, lane_2, per_2, _S21, 16U, blk2_2, lane2_2, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        break;
    }

#line 43
    innermost_0(r_4);

#line 792 "mm_256_fusedTierB_c16p16.slang"
    return;
}


#line 309
float pairSum_0(uint tid_1, float v_1, KernelContext_0 thread* kernelContext_4)
{
    threadgroup_barrier(mem_flags::mem_threadgroup);
    (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + tid_1] = (as_type<uint>((v_1)));
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 313
    uint k_0 = 0U;

#line 313
    float t_12 = 0.0;

    for(;;)
    {

#line 315
        if(k_0 < 16U)
        {
        }
        else
        {

#line 315
            break;
        }

#line 315
        float t_13 = t_12 + (as_type<float>(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + k_0])));

#line 315
        k_0 = k_0 + 1U;

#line 315
        t_12 = t_13;

#line 315
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);
    return t_12;
}


#line 758
uint lgOf_0(uint i_4)
{

#line 758
    uint _S22;

#line 758
    if(i_4 < 1U)
    {

#line 758
        _S22 = 4U;

#line 758
    }
    else
    {

#line 758
        if(i_4 == 1U)
        {

#line 758
            _S22 = 4U;

#line 758
        }
        else
        {

#line 758
            _S22 = 1U;

#line 758
        }

#line 758
    }

#line 758
    return _S22;
}


#line 760
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 764
    uint lg_1 = lgOf_0(0U);

#line 769
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 47 "twiddle.slang"
uint mfC16RawFlag_0()
{
    ;
    uint _S23 = ((MF_C16_RAW));

#line 50
    return _S23;
}


#line 299 "mm_256_fusedTierB_c16p16.slang"
float2 c16Bound_0(float2 v_2, float energy_0)
{

#line 52 "twiddle.slang"
    uint _S24 = mfC16RawFlag_0();

#line 301 "mm_256_fusedTierB_c16p16.slang"
    if((1U - _S24) == 0U)
    {

#line 301
        return v_2;
    }

#line 302
    float m_1 = length(v_2);
    float b_5 = m_1 * 1.00146484375 + 0.00618266593664885 * sqrt(energy_0);

#line 303
    float2 _S25;
    if(m_1 > 0.0)
    {

#line 304
        _S25 = v_2 * float2((b_5 / m_1)) ;

#line 304
    }
    else
    {

#line 304
        _S25 = float2(b_5, 0.0);

#line 304
    }

#line 304
    return _S25;
}


#line 798
void filterOne_0(uint pair_0, uint d_4, uint t_14, uint tid_2, const array<half2, int(16)> thread* dreg_0, uint device* data_0, uint device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_5)
{


    bool live_0;

#line 838
    thread array<half2, int(16)> r_5;

#line 838
    uint n2_0 = 0U;



    for(;;)
    {

#line 842
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 842
            break;
        }

#line 843
        r_5[n2_0] = cmulConj_0((*dreg_0)[n2_0], cload_0(tmpl_0, t_14 * 256U + tid_2 + 16U * n2_0));

#line 842
        n2_0 = n2_0 + 1U;

#line 842
    }

#line 842
    transform_0(&r_5, tid_2, kernelContext_5);

#line 842
    uint i_5 = 0U;

#line 842
    float energy_1 = 0.0;

#line 872
    for(;;)
    {

#line 872
        if(i_5 < 16U)
        {
        }
        else
        {

#line 872
            break;
        }

#line 873
        float _ex_0 = float(r_5[i_5].x);

#line 873
        float _ey_0 = float(r_5[i_5].y);
        float energy_2 = energy_1 + (_ex_0 * _ex_0 + _ey_0 * _ey_0);

#line 872
        i_5 = i_5 + 1U;

#line 872
        energy_1 = energy_2;

#line 872
    }

#line 872
    float _S26 = pairSum_0(tid_2, energy_1, kernelContext_5);



    float _S27 = _S26 / 256.0;

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 988
    bool _S28 = tid_2 == 0U;

#line 988
    if(_S28)
    {

#line 988
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0] = thrBits_1;

#line 988
        (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U] = 4294967295U;

#line 988
    }

#line 993
    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;

#line 995
    i_5 = 0U;

#line 995
    uint ovAcc_0 = 0U;

#line 1000
    for(;;)
    {

#line 1000
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1000
            break;
        }

#line 1001
        uint idx_0 = slotToIndex_0(tid_2 * 16U + i_5);
        if(idx_0 >= winStart_2)
        {

#line 1002
            live_0 = idx_0 < winEnd_2;

#line 1002
        }
        else
        {

#line 1002
            live_0 = false;

#line 1002
        }



        float _rx_0 = float(r_5[i_5].x);

#line 1006
        float _ry_0 = float(r_5[i_5].y);
        if(live_0)
        {

#line 1007
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1007
        }
        else
        {

#line 1007
            n2_0 = 0U;

#line 1007
        }

#line 1007
        myMag_0[i_5] = n2_0;

#line 1013
        uint ovAcc_1 = ovAcc_0 | ((((uint(as_type<ushort>(r_5[i_5][0U])) & 65535U) | (uint(as_type<ushort>(r_5[i_5][1U])) << 16U)) & 2080406528U) + 67109888U);

#line 1000
        i_5 = i_5 + 1U;

#line 1000
        ovAcc_0 = ovAcc_1;

#line 1000
    }

#line 1034
    if((ovAcc_0 & 2147516416U) != 0U)
    {

#line 1034
        i_5 = 0U;
        for(;;)
        {

#line 1035
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1035
                break;
            }

#line 1036
            if((myMag_0[i_5]) != 0U)
            {

#line 1036
                live_0 = true;

#line 1036
            }
            else
            {

#line 1036
                uint _S29 = slotToIndex_0(tid_2 * 16U + i_5);
                if(_S29 >= winStart_2)
                {

#line 1037
                    live_0 = _S29 < winEnd_2;

#line 1037
                }
                else
                {

#line 1037
                    live_0 = false;

#line 1037
                }

#line 1036
            }

#line 1036
            if(live_0)
            {
                myMag_0[i_5] = 2139095040U;

#line 1036
            }

#line 1035
            i_5 = i_5 + 1U;

#line 1035
        }

#line 1034
    }

#line 1034
    uint bestBits_0 = thrBits_1;

#line 1034
    i_5 = 0U;

#line 1053
    for(;;)
    {

#line 1053
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1053
            break;
        }

#line 1053
        uint _S30 = max(bestBits_0, myMag_0[i_5]);

#line 1053
        uint i_6 = i_5 + 1U;

#line 1053
        bestBits_0 = _S30;

#line 1053
        i_5 = i_6;

#line 1053
    }

#line 1068
    if(bestBits_0 > thrBits_1)
    {

#line 1068
        uint _S31 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0])), bestBits_0, memory_order_relaxed);

#line 1068
    }


    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1071
    uint winner_0 = 4294967295U;

#line 1071
    i_5 = 0U;

#line 1081
    for(;;)
    {

#line 1081
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1081
            break;
        }

#line 1082
        if((myMag_0[i_5]) > thrBits_1)
        {

#line 1082
            live_0 = (myMag_0[i_5]) == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0];

#line 1082
        }
        else
        {

#line 1082
            live_0 = false;

#line 1082
        }

#line 1082
        if(live_0)
        {

#line 1082
            winner_0 = min(winner_0, tid_2 * 16U + i_5);

#line 1082
        }

#line 1081
        i_5 = i_5 + 1U;

#line 1081
    }

#line 1089
    if(winner_0 != 4294967295U)
    {

#line 1089
        uint _S32 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])), winner_0, memory_order_relaxed);

#line 1089
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1091
    i_5 = 0U;
    for(;;)
    {

#line 1092
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1092
            break;
        }

#line 1093
        uint _S33 = tid_2 * 16U + i_5;

#line 1093
        if(_S33 == (*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U])
        {

#line 1094
            *(peakIdx_0+pair_0) = int(slotToIndex_0(_S33));

#line 1094
            packed_float2 device* _S34 = peakVal_0+pair_0;

            float2 _S35 = c16Bound_0(float2(float(r_5[i_5].x), float(r_5[i_5].y)), _S27);

#line 1096
            *_S34 = packed_float2(_S35) ;

#line 1093
        }

#line 1092
        i_5 = i_5 + 1U;

#line 1092
    }

#line 1102
    if(_S28)
    {

#line 1102
        live_0 = ((*kernelContext_5->stg_0)[kernelContext_5->_stgBase_0 + 1U]) == 4294967295U;

#line 1102
    }
    else
    {

#line 1102
        live_0 = false;

#line 1102
    }

#line 1102
    if(live_0)
    {

#line 1103
        *(peakIdx_0+pair_0) = int(-1);

#line 1103
        *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 1102
    }

#line 1136
    return;
}


#line 1527
void filterPair_0(uint pair_1, uint tid_3, uint device* data_1, uint device* tmpl_1, int device* peakIdx_1, packed_float2 device* peakVal_1, uint ntmpl_1, uint winStart_3, uint winEnd_3, uint binsize_2, int binShift_2, uint nbins_2, uint thrBits_2, KernelContext_0 thread* kernelContext_6)
{

#line 1527
    thread uint _S36 = winStart_3;

#line 1527
    thread uint _S37 = winEnd_3;

#line 1533
    kernelContext_6->_tid_0 = tid_3;

#line 1562
    uint d_5 = pair_1 / ntmpl_1;

#line 1562
    uint _S38 = pair_1 % ntmpl_1;

#line 1567
    rowWindow_0(d_5, &_S36, &_S37);


    thread array<half2, int(16)> dreg_1;

#line 1570
    uint n2_1 = 0U;

    for(;;)
    {

#line 1572
        if(n2_1 < 16U)
        {
        }
        else
        {

#line 1572
            break;
        }

#line 1573
        dreg_1[n2_1] = dload_0(data_1, d_5 * 256U + tid_3 + 16U * n2_1);

#line 1572
        n2_1 = n2_1 + 1U;

#line 1572
    }

#line 1572
    uint k_1 = 0U;

#line 1592
    for(;;)
    {

#line 1592
        if(k_1 < 1U)
        {
        }
        else
        {

#line 1592
            break;
        }

#line 1593
        uint _S39 = pair_1 + k_1;

#line 1593
        uint _S40 = _S38 + k_1;

#line 1593
        thread array<half2, int(16)> _S41 = dreg_1;

#line 1593
        filterOne_0(_S39, d_5, _S40, tid_3, &_S41, data_1, tmpl_1, peakIdx_1, peakVal_1, _S36, _S37, binsize_2, binShift_2, nbins_2, thrBits_2, kernelContext_6);

#line 1592
        k_1 = k_1 + 1U;

#line 1592
    }



    return;
}


[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], uint device* entryPointParams_data_1 [[buffer(1)]], uint device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1600
    thread KernelContext_0 kernelContext_7;

#line 1600
    (&kernelContext_7)->entryPointParams_0 = entryPointParams_1;

#line 1600
    (&kernelContext_7)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1600
    (&kernelContext_7)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1600
    (&kernelContext_7)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1600
    (&kernelContext_7)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1600
    threadgroup array<uint, int(4096)> stg_1;

#line 1600
    (&kernelContext_7)->stg_0 = &stg_1;

#line 1620
    uint _S42 = lid_0.x;

#line 1620
    uint _sub_0 = _S42 / 16U;
    uint _pr_0 = gid_0.x * 16U + _sub_0;

#line 1621
    uint _t_0 = _S42 % 16U;
    (&kernelContext_7)->_stgBase_0 = _sub_0 * 256U;

#line 1622
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_1, entryPointParams_1->winEnd_1, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_7);



    return;
}
