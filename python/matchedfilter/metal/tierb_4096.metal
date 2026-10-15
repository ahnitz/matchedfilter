#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;

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


#line 168 "mm_4096_fusedTierB.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 168
    return float2(*(b_0+i_0)) ;
}


#line 267
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 267
    float _S2 = a_0.x;

#line 267
    float _S3 = b_1.x;

#line 267
    float _S4 = a_0.y;

#line 267
    float _S5 = b_1.y;

#line 267
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 472
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 474
    float2 t1_0 = *a_1 - *c_0;

#line 474
    float2 t2_0 = *b_2 + *d_0;

#line 474
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 476
    *b_2 = t1_0 + j3_0;

#line 476
    *c_0 = t0_0 - t2_0;

#line 476
    *d_0 = t1_0 - j3_0;
    return;
}


#line 266
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 266
    float _S6 = a_2.x;

#line 266
    float _S7 = b_3.x;

#line 266
    float _S8 = a_2.y;

#line 266
    float _S9 = b_3.y;

#line 266
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 508
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 515
    uint n1_0 = 0U;
    for(;;)
    {

#line 516
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 516
            break;
        }

#line 516
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 516
        n1_0 = n1_0 + 1U;

#line 516
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 517
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 517
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 518
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 518
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 519
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 519
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 519
    uint k2_0 = 0U;
    for(;;)
    {

#line 520
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 520
            break;
        }

#line 520
        uint _S10 = 4U * k2_0;

#line 520
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 520
        k2_0 = k2_0 + 1U;

#line 520
    }

    float2 t_0 = (*r_0)[int(1)];

#line 522
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 522
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 523
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 523
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 524
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 524
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 525
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 525
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 526
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 526
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 527
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 527
    (*r_0)[int(14)] = t_5;
    return;
}


#line 508
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_1 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_1 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_1 = float2(0.0f, 1.0f);
    float2 W6_1 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_1 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 515
    uint n1_1 = 0U;
    for(;;)
    {

#line 516
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 516
            break;
        }

#line 516
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 516
        n1_1 = n1_1 + 1U;

#line 516
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 517
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 517
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 518
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 518
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 519
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 519
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 519
    uint k2_1 = 0U;
    for(;;)
    {

#line 520
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 520
            break;
        }

#line 520
        uint _S11 = 4U * k2_1;

#line 520
        r4_0(&(*r_1)[_S11], &(*r_1)[_S11 + 1U], &(*r_1)[_S11 + 2U], &(*r_1)[_S11 + 3U]);

#line 520
        k2_1 = k2_1 + 1U;

#line 520
    }

    float2 t_6 = (*r_1)[int(1)];

#line 522
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 522
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 523
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 523
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 524
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 524
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 525
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 525
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 526
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 526
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 527
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 527
    (*r_1)[int(14)] = t_11;
    return;
}


#line 84 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 268 "mm_4096_fusedTierB.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 270
    uint j_0 = d_1 / _S12;

#line 270
    uint m_0 = d_1 % _S12;

#line 270
    uint _S13;
    if(TB_0 <= 16U)
    {

#line 271
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 271
    }
    else
    {

#line 271
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 271
    }

#line 271
    return _S13;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
    uint winStart_0;
    uint winEnd_0;
    uint binsize_0;
    int binShift_0;
    uint nbins_0;
    uint thrBits_0;
};


#line 255 "mm_4096_fusedTierB.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 255
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 255
    uint _S14 = 2U * i_1;

#line 255
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14] = (as_type<uint>((v_0.x)));

#line 255
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14 + 1U] = (as_type<uint>((v_0.y)));

#line 255
    return;
}


#line 256
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 256
    uint _S15 = 2U * i_2;

#line 256
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15 + 1U]))));
}


#line 697
void exchange_0(array<float2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 698
    uint j_1;

#line 709
    thread array<float2, int(16)> out_0;

#line 709
    uint z_0 = 0U;
    for(;;)
    {

#line 710
        if(z_0 < 16U)
        {
        }
        else
        {

#line 710
            break;
        }

#line 710
        out_0[z_0] = float2(0.0f, 0.0f);

#line 710
        z_0 = z_0 + 1U;

#line 710
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S16 = p0_0 & lenMask_0;

#line 716
    uint _S17 = (_S16 >> lgSpan_0) * 256U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 716
    uint c_1 = 0U;

    for(;;)
    {

#line 718
        if(c_1 < 1U)
        {
        }
        else
        {

#line 718
            break;
        }

#line 719
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 719
        j_1 = 0U;
        for(;;)
        {

#line 720
            if(j_1 < 16U)
            {
            }
            else
            {

#line 720
                break;
            }

#line 720
            stgPut_0(j_1 * 256U + kernelContext_2->_tid_0, (*r_2)[c_1 * 16U + j_1], kernelContext_2);

#line 720
            j_1 = j_1 + 1U;

#line 720
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 721
        uint d_2 = 0U;
        for(;;)
        {

#line 722
            if(d_2 < 16U)
            {
            }
            else
            {

#line 722
                break;
            }

#line 723
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S18 = pz_0 & lenMask_0;
            uint az_0 = (_S18 >> lgSpan_0) * 256U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S18 & spanMask_0);

#line 725
            float2 _S19 = stgGet_0(_S17 + az_0 - c_1 * 16U * 256U, kernelContext_2);


            out_0[d_2] = _S19;

#line 722
            d_2 = d_2 + 1U;

#line 722
        }

#line 718
        c_1 = c_1 + 1U;

#line 718
    }

#line 718
    j_1 = 0U;

#line 731
    for(;;)
    {

#line 731
        if(j_1 < 16U)
        {
        }
        else
        {

#line 731
            break;
        }

#line 731
        (*r_2)[j_1] = out_0[j_1];

#line 731
        j_1 = j_1 + 1U;

#line 731
    }
    return;
}


#line 611
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 618
    dft16_1(r_3);

#line 623
    return;
}


#line 799
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 799
    uint _S20;

#line 799
    uint k2_2;

#line 799
    float cr_0;

#line 799
    float ci_0;

#line 799
    uint _S21;

#line 799
    for(;;)
    {

#line 799
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(256U);

#line 11
                _S20 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(4096U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 255U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 4096.0f);
                float _S22 = tw_0.x;

#line 40
                float _S23 = tw_0.y;

#line 40
                k2_2 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S22 - ci_0 * _S23;
                    float _S24 = cr_0 * _S23 + ci_0 * _S22;

#line 42
                    k2_2 = k2_2 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S24;

#line 42
                }

#line 50
                uint per_2 = 16U / max(256U, 1U);
                uint _S25 = max(16U, 1U);

#line 51
                _S21 = _S25;
                uint blk2_2 = tid_0 / _S25;

#line 52
                uint lane2_2 = tid_0 % _S25;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 256U, 4096U, blk_2, lane_2, per_2, _S25, 256U, blk2_2, lane2_2, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        for(;;)
        {

#line 7
            for(;;)
            {


                uint lgTB_1 = firstbithigh_0(16U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 15U;


                dft16_0(r_4);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 256.0f);
                float _S26 = tw_1.x;

#line 40
                float _S27 = tw_1.y;

#line 40
                k2_2 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_2 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S26 - ci_0 * _S27;
                    float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 42
                    k2_2 = k2_2 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S28;

#line 42
                }

#line 50
                uint per_3 = 16U / _S21;
                uint _S29 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S29;

#line 52
                uint lane2_3 = tid_0 % _S29;

#line 52
                exchange_0(r_4, _S20, lgTB_1, 16U, 256U, blk_3, lane_3, per_3, _S29, 16U, blk2_3, lane2_3, kernelContext_3);

#line 7
                break;
            }

#line 7
            break;
        }

#line 7
        break;
    }

#line 56
    innermost_0(r_4);

#line 802 "mm_4096_fusedTierB.slang"
    return;
}


#line 756
uint lgOf_0(uint i_3)
{

#line 756
    uint _S30;

#line 756
    if(i_3 < 2U)
    {

#line 756
        _S30 = 4U;

#line 756
    }
    else
    {

#line 756
        if(i_3 == 2U)
        {

#line 756
            _S30 = 4U;

#line 756
        }
        else
        {

#line 756
            _S30 = 1U;

#line 756
        }

#line 756
    }

#line 756
    return _S30;
}


#line 758
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 762
    uint lg_1 = lgOf_0(1U);

#line 762
    uint lg_2 = lgOf_0(0U);

#line 767
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 822
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 842
    kernelContext_4->_tid_0 = tid_1;
    uint _S31 = pair_0 / ntmpl_1;

#line 843
    uint _S32 = pair_0 % ntmpl_1;

#line 848
    thread array<float2, int(16)> r_5;

#line 848
    uint n2_0 = 0U;

#line 859
    for(;;)
    {

#line 859
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 859
            break;
        }

#line 860
        uint idx_0 = tid_1 + 256U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S31 * 4096U + idx_0), cload_0(tmpl_0, _S32 * 4096U + idx_0));

#line 859
        n2_0 = n2_0 + 1U;

#line 859
    }

#line 859
    transform_0(&r_5, tid_1, kernelContext_4);

#line 888
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 888
    uint b_4 = tid_1;

#line 1000
    for(;;)
    {

#line 1000
        if(b_4 < nbins_1)
        {
        }
        else
        {

#line 1000
            break;
        }

#line 1000
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4] = thrBits_1;

#line 1000
        b_4 = b_4 + 256U;

#line 1000
    }
    bool _S33 = nbins_1 == 1U;

#line 1001
    bool live_0;

#line 1001
    if(_S33)
    {

#line 1001
        live_0 = tid_1 == 0U;

#line 1001
    }
    else
    {

#line 1001
        live_0 = false;

#line 1001
    }

#line 1001
    if(live_0)
    {

#line 1001
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 1001
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1060
    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 1061
    uint i_4 = 0U;



    for(;;)
    {

#line 1065
        if(i_4 < 16U)
        {
        }
        else
        {

#line 1065
            break;
        }

#line 1066
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_4);
        if(idx_1 >= winStart_1)
        {

#line 1067
            live_0 = idx_1 < winEnd_1;

#line 1067
        }
        else
        {

#line 1067
            live_0 = false;

#line 1067
        }



        float _rx_0 = r_5[i_4].x;

#line 1071
        float _ry_0 = r_5[i_4].y;
        if(live_0)
        {

#line 1072
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1072
        }
        else
        {

#line 1072
            n2_0 = 0U;

#line 1072
        }

#line 1072
        myMag_0[i_4] = n2_0;

#line 1080
        uint off_0 = idx_1 - winStart_1;

#line 1087
        if(live_0)
        {

#line 1087
            if(binShift_1 >= int(0))
            {

#line 1087
                b_4 = off_0 >> uint(binShift_1);

#line 1087
            }
            else
            {

#line 1087
                uint _S34 = off_0 / binsize_1;

#line 1087
                b_4 = _S34;

#line 1087
            }

#line 1087
        }
        else
        {

#line 1087
            b_4 = 0U;

#line 1087
        }

#line 1087
        myBin_0[i_4] = b_4;

#line 1087
        bool _S35;



        if(nbins_1 > 1U)
        {

#line 1091
            _S35 = (myMag_0[i_4]) > thrBits_1;

#line 1091
        }
        else
        {

#line 1091
            _S35 = false;

#line 1091
        }

#line 1091
        if(_S35)
        {

#line 1092
            uint _S36 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_4]])), myMag_0[i_4], memory_order_relaxed);

#line 1091
        }

#line 1065
        i_4 = i_4 + 1U;

#line 1065
    }

#line 1065
    uint winner_0;

#line 1115
    if(_S33)
    {

#line 1115
        winner_0 = thrBits_1;

#line 1115
        i_4 = 0U;


        for(;;)
        {

#line 1118
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1118
                break;
            }

#line 1118
            uint _S37 = max(winner_0, myMag_0[i_4]);

#line 1118
            uint i_5 = i_4 + 1U;

#line 1118
            winner_0 = _S37;

#line 1118
            i_4 = i_5;

#line 1118
        }

        uint wm_0 = simd_max(winner_0);
        bool _S38 = simd_is_first();

#line 1121
        if(_S38)
        {

#line 1121
            live_0 = wm_0 > thrBits_1;

#line 1121
        }
        else
        {

#line 1121
            live_0 = false;

#line 1121
        }

#line 1121
        if(live_0)
        {

#line 1121
            uint _S39 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1121
        }

#line 1115
    }

#line 1136
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1143
    if(_S33)
    {

#line 1143
        winner_0 = 4294967295U;

#line 1143
        i_4 = 0U;


        for(;;)
        {

#line 1146
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1146
                break;
            }

#line 1147
            if((myMag_0[i_4]) > thrBits_1)
            {

#line 1147
                live_0 = (myMag_0[i_4]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 1147
            }
            else
            {

#line 1147
                live_0 = false;

#line 1147
            }

#line 1147
            if(live_0)
            {

#line 1147
                winner_0 = min(winner_0, tid_1 * 16U + i_4);

#line 1147
            }

#line 1146
            i_4 = i_4 + 1U;

#line 1146
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S40 = simd_is_first();

#line 1151
        if(_S40)
        {

#line 1151
            live_0 = waveWinner_0 != 4294967295U;

#line 1151
        }
        else
        {

#line 1151
            live_0 = false;

#line 1151
        }

#line 1151
        if(live_0)
        {

#line 1152
            uint _S41 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1151
        }

#line 1156
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1156
        i_4 = 0U;
        for(;;)
        {

#line 1157
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1157
                break;
            }

#line 1158
            uint _S42 = tid_1 * 16U + i_4;

#line 1158
            if(_S42 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 1159
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S42));

#line 1159
                *(peakVal_0+pair_0) = packed_float2(float2(r_5[i_4].x, r_5[i_4].y)) ;

#line 1158
            }

#line 1157
            i_4 = i_4 + 1U;

#line 1157
        }

#line 1167
        if(tid_1 == 0U)
        {

#line 1167
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1167
        }
        else
        {

#line 1167
            live_0 = false;

#line 1167
        }

#line 1167
        if(live_0)
        {

#line 1168
            *(peakIdx_0+pair_0) = int(-1);

#line 1168
            *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1167
        }

#line 1143
    }
    else
    {

#line 1143
        i_4 = 0U;

#line 1176
        for(;;)
        {

#line 1176
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1176
                break;
            }

#line 1177
            if((myMag_0[i_4]) > thrBits_1)
            {

#line 1177
                live_0 = (myMag_0[i_4]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_4]];

#line 1177
            }
            else
            {

#line 1177
                live_0 = false;

#line 1177
            }

#line 1177
            myMag_0[i_4] = uint(live_0);

#line 1176
            i_4 = i_4 + 1U;

#line 1176
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1179
        b_4 = tid_1;
        for(;;)
        {

#line 1180
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 1180
                break;
            }

#line 1180
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4] = 4294967295U;

#line 1180
            b_4 = b_4 + 256U;

#line 1180
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1181
        i_4 = 0U;
        for(;;)
        {

#line 1182
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1182
                break;
            }

#line 1183
            if((myMag_0[i_4]) != 0U)
            {

#line 1183
                uint _S43 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_4]])), tid_1 * 16U + i_4, memory_order_relaxed);

#line 1183
            }

#line 1182
            i_4 = i_4 + 1U;

#line 1182
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1184
        i_4 = 0U;
        for(;;)
        {

#line 1185
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1185
                break;
            }

#line 1186
            if((myMag_0[i_4]) != 0U)
            {

#line 1186
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_4]]) == (tid_1 * 16U + i_4);

#line 1186
            }
            else
            {

#line 1186
                live_0 = false;

#line 1186
            }

#line 1186
            if(live_0)
            {

#line 1187
                uint o_0 = pair_0 * nbins_1 + myBin_0[i_4];
                *(peakIdx_0+o_0) = int(slotToIndex_0(tid_1 * 16U + i_4));

#line 1188
                *(peakVal_0+o_0) = packed_float2(float2(r_5[i_4].x, r_5[i_4].y)) ;

#line 1186
            }

#line 1185
            i_4 = i_4 + 1U;

#line 1185
        }

#line 1185
        b_4 = tid_1;

#line 1192
        for(;;)
        {

#line 1192
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 1192
                break;
            }

#line 1193
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4]) == 4294967295U)
            {

#line 1194
                uint _S44 = pair_0 * nbins_1 + b_4;

#line 1194
                *(peakIdx_0+_S44) = int(-1);

#line 1194
                *(peakVal_0+_S44) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1193
            }

#line 1192
            b_4 = b_4 + 256U;

#line 1192
        }

#line 1143
    }

#line 1202
    return;
}


#line 1684
[[kernel]] void fusedTierB(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]])
{

#line 1684
    thread KernelContext_0 kernelContext_5;

#line 1684
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1684
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1684
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1684
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1684
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1684
    threadgroup array<uint, int(8192)> stg_1;

#line 1684
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1701
    uint _pr_0 = gid_0.x;

#line 1701
    uint _t_0 = lid_0.x;
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 1702
    filterPair_0(_pr_0, _t_0, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);

#line 1710
    return;
}
