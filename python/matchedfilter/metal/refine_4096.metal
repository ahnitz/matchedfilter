#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;

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


#line 190 "mm_4096_refineListed.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 190
    return;
}


#line 162
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 162
    return float2(*(b_0+i_0)) ;
}


#line 262
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 262
    float _S2 = a_0.x;

#line 262
    float _S3 = b_1.x;

#line 262
    float _S4 = a_0.y;

#line 262
    float _S5 = b_1.y;

#line 262
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 467
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_1 + *c_0;

#line 469
    float2 t1_0 = *a_1 - *c_0;

#line 469
    float2 t2_0 = *b_2 + *d_1;

#line 469
    float2 t3_0 = *b_2 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 471
    *b_2 = t1_0 + j3_0;

#line 471
    *c_0 = t0_0 - t2_0;

#line 471
    *d_1 = t1_0 - j3_0;
    return;
}


#line 261
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 261
    float _S6 = a_2.x;

#line 261
    float _S7 = b_3.x;

#line 261
    float _S8 = a_2.y;

#line 261
    float _S9 = b_3.y;

#line 261
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 503
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 510
    uint n1_0 = 0U;
    for(;;)
    {

#line 511
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 511
            break;
        }

#line 511
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 511
        n1_0 = n1_0 + 1U;

#line 511
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 512
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 512
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 513
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 513
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 514
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 514
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 514
    uint k2_0 = 0U;
    for(;;)
    {

#line 515
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 515
            break;
        }

#line 515
        uint _S10 = 4U * k2_0;

#line 515
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 515
        k2_0 = k2_0 + 1U;

#line 515
    }

    float2 t_0 = (*r_0)[int(1)];

#line 517
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 517
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 518
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 518
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 519
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 519
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 520
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 520
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 521
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 521
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 522
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 522
    (*r_0)[int(14)] = t_5;
    return;
}


#line 503
void dft16_1(array<float2, int(16)> thread* r_1)
{
    float2 W1_1 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_1 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_1 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_1 = float2(0.0, 1.0);
    float2 W6_1 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_1 = float2(-0.92387950420379639, -0.38268342614173889);

#line 510
    uint n1_1 = 0U;
    for(;;)
    {

#line 511
        if(n1_1 < 4U)
        {
        }
        else
        {

#line 511
            break;
        }

#line 511
        r4_0(&(*r_1)[n1_1], &(*r_1)[n1_1 + 4U], &(*r_1)[n1_1 + 8U], &(*r_1)[n1_1 + 12U]);

#line 511
        n1_1 = n1_1 + 1U;

#line 511
    }
    (*r_1)[int(5)] = cmul_0((*r_1)[int(5)], W1_1);

#line 512
    (*r_1)[int(9)] = cmul_0((*r_1)[int(9)], W2_1);

#line 512
    (*r_1)[int(13)] = cmul_0((*r_1)[int(13)], W3_1);
    (*r_1)[int(6)] = cmul_0((*r_1)[int(6)], W2_1);

#line 513
    (*r_1)[int(10)] = cmul_0((*r_1)[int(10)], W4_1);

#line 513
    (*r_1)[int(14)] = cmul_0((*r_1)[int(14)], W6_1);
    (*r_1)[int(7)] = cmul_0((*r_1)[int(7)], W3_1);

#line 514
    (*r_1)[int(11)] = cmul_0((*r_1)[int(11)], W6_1);

#line 514
    (*r_1)[int(15)] = cmul_0((*r_1)[int(15)], W9_1);

#line 514
    uint k2_1 = 0U;
    for(;;)
    {

#line 515
        if(k2_1 < 4U)
        {
        }
        else
        {

#line 515
            break;
        }

#line 515
        uint _S11 = 4U * k2_1;

#line 515
        r4_0(&(*r_1)[_S11], &(*r_1)[_S11 + 1U], &(*r_1)[_S11 + 2U], &(*r_1)[_S11 + 3U]);

#line 515
        k2_1 = k2_1 + 1U;

#line 515
    }

    float2 t_6 = (*r_1)[int(1)];

#line 517
    (*r_1)[int(1)] = (*r_1)[int(4)];

#line 517
    (*r_1)[int(4)] = t_6;
    float2 t_7 = (*r_1)[int(2)];

#line 518
    (*r_1)[int(2)] = (*r_1)[int(8)];

#line 518
    (*r_1)[int(8)] = t_7;
    float2 t_8 = (*r_1)[int(3)];

#line 519
    (*r_1)[int(3)] = (*r_1)[int(12)];

#line 519
    (*r_1)[int(12)] = t_8;
    float2 t_9 = (*r_1)[int(6)];

#line 520
    (*r_1)[int(6)] = (*r_1)[int(9)];

#line 520
    (*r_1)[int(9)] = t_9;
    float2 t_10 = (*r_1)[int(7)];

#line 521
    (*r_1)[int(7)] = (*r_1)[int(13)];

#line 521
    (*r_1)[int(13)] = t_10;
    float2 t_11 = (*r_1)[int(11)];

#line 522
    (*r_1)[int(11)] = (*r_1)[int(14)];

#line 522
    (*r_1)[int(14)] = t_11;
    return;
}


#line 64 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 263 "mm_4096_refineListed.slang"
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 265
    uint j_0 = d_2 / _S12;

#line 265
    uint m_0 = d_2 % _S12;

#line 265
    uint _S13;
    if(TB_0 <= 16U)
    {

#line 266
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 266
    }
    else
    {

#line 266
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 266
    }

#line 266
    return _S13;
}


#line 8402 "hlsl.meta.slang"
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


#line 250 "mm_4096_refineListed.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_survivors_0;
    uint _stgBase_0;
    uint _tid_0;
    array<uint, int(8192)> threadgroup* stg_0;
};


#line 250
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 250
    uint _S14 = 2U * i_1;

#line 250
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14] = (as_type<uint>((v_0.x)));

#line 250
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14 + 1U] = (as_type<uint>((v_0.y)));

#line 250
    return;
}


#line 251
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 251
    uint _S15 = 2U * i_2;

#line 251
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15 + 1U]))));
}


#line 663
void exchange_0(array<float2, int(16)> thread* r_2, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 664
    uint j_1;

#line 675
    thread array<float2, int(16)> out_0;

#line 675
    uint z_0 = 0U;
    for(;;)
    {

#line 676
        if(z_0 < 16U)
        {
        }
        else
        {

#line 676
            break;
        }

#line 676
        out_0[z_0] = float2(0.0, 0.0);

#line 676
        z_0 = z_0 + 1U;

#line 676
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S16 = p0_0 & lenMask_0;

#line 682
    uint _S17 = (_S16 >> lgSpan_0) * 256U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 682
    uint c_1 = 0U;

    for(;;)
    {

#line 684
        if(c_1 < 1U)
        {
        }
        else
        {

#line 684
            break;
        }

#line 685
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 685
        j_1 = 0U;
        for(;;)
        {

#line 686
            if(j_1 < 16U)
            {
            }
            else
            {

#line 686
                break;
            }

#line 686
            stgPut_0(j_1 * 256U + kernelContext_2->_tid_0, (*r_2)[c_1 * 16U + j_1], kernelContext_2);

#line 686
            j_1 = j_1 + 1U;

#line 686
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 687
        uint d_3 = 0U;
        for(;;)
        {

#line 688
            if(d_3 < 16U)
            {
            }
            else
            {

#line 688
                break;
            }

#line 689
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S18 = pz_0 & lenMask_0;
            uint az_0 = (_S18 >> lgSpan_0) * 256U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S18 & spanMask_0);

#line 691
            float2 _S19 = stgGet_0(_S17 + az_0 - c_1 * 16U * 256U, kernelContext_2);


            out_0[d_3] = _S19;

#line 688
            d_3 = d_3 + 1U;

#line 688
        }

#line 684
        c_1 = c_1 + 1U;

#line 684
    }

#line 684
    j_1 = 0U;

#line 697
    for(;;)
    {

#line 697
        if(j_1 < 16U)
        {
        }
        else
        {

#line 697
            break;
        }

#line 697
        (*r_2)[j_1] = out_0[j_1];

#line 697
        j_1 = j_1 + 1U;

#line 697
    }
    return;
}


#line 606
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 613
    dft16_1(r_3);

#line 618
    return;
}


#line 753
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 753
    uint _S20;

#line 753
    uint k2_2;

#line 753
    float cr_0;

#line 753
    float ci_0;

#line 753
    uint _S21;

#line 753
    for(;;)
    {

#line 753
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

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 4096.0);
                float _S22 = tw_0.x;

#line 27
                float _S23 = tw_0.y;

#line 27
                k2_2 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

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
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S22 - ci_0 * _S23;
                    float _S24 = cr_0 * _S23 + ci_0 * _S22;

#line 29
                    k2_2 = k2_2 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S24;

#line 29
                }

#line 37
                uint per_2 = 16U / max(256U, 1U);
                uint _S25 = max(16U, 1U);

#line 38
                _S21 = _S25;
                uint blk2_2 = tid_0 / _S25;

#line 39
                uint lane2_2 = tid_0 % _S25;

#line 39
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

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 256.0);
                float _S26 = tw_1.x;

#line 27
                float _S27 = tw_1.y;

#line 27
                k2_2 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

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
                    (*r_4)[k2_2] = cmul_0((*r_4)[k2_2], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S26 - ci_0 * _S27;
                    float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 29
                    k2_2 = k2_2 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S28;

#line 29
                }

#line 37
                uint per_3 = 16U / _S21;
                uint _S29 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S29;

#line 39
                uint lane2_3 = tid_0 % _S29;

#line 39
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

#line 43
    innermost_0(r_4);

#line 756 "mm_4096_refineListed.slang"
    return;
}


#line 722
uint lgOf_0(uint i_3)
{

#line 722
    uint _S30;

#line 722
    if(i_3 < 2U)
    {

#line 722
        _S30 = 4U;

#line 722
    }
    else
    {

#line 722
        if(i_3 == 2U)
        {

#line 722
            _S30 = 4U;

#line 722
        }
        else
        {

#line 722
            _S30 = 1U;

#line 722
        }

#line 722
    }

#line 722
    return _S30;
}


#line 724
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 728
    uint lg_1 = lgOf_0(1U);

#line 728
    uint lg_2 = lgOf_0(0U);

#line 733
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 768
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 782
    kernelContext_4->_tid_0 = tid_1;
    uint _S31 = pair_0 / ntmpl_1;

#line 783
    uint _S32 = pair_0 % ntmpl_1;

    thread array<float2, int(16)> r_5;

#line 785
    uint n2_0 = 0U;

#line 796
    for(;;)
    {

#line 796
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 796
            break;
        }

#line 797
        uint idx_0 = tid_1 + 256U * n2_0;
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S31 * 4096U + idx_0), cload_0(tmpl_0, _S32 * 4096U + idx_0));

#line 796
        n2_0 = n2_0 + 1U;

#line 796
    }

#line 796
    transform_0(&r_5, tid_1, kernelContext_4);

#line 825
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 825
    uint b_4 = tid_1;

#line 899
    for(;;)
    {

#line 899
        if(b_4 < nbins_1)
        {
        }
        else
        {

#line 899
            break;
        }

#line 899
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4] = thrBits_1;

#line 899
        b_4 = b_4 + 256U;

#line 899
    }
    bool _S33 = nbins_1 == 1U;

#line 900
    bool live_0;

#line 900
    if(_S33)
    {

#line 900
        live_0 = tid_1 == 0U;

#line 900
    }
    else
    {

#line 900
        live_0 = false;

#line 900
    }

#line 900
    if(live_0)
    {

#line 900
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 900
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 905
    uint i_4 = 0U;



    for(;;)
    {

#line 909
        if(i_4 < 16U)
        {
        }
        else
        {

#line 909
            break;
        }

#line 910
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_4);
        if(idx_1 >= winStart_2)
        {

#line 911
            live_0 = idx_1 < winEnd_2;

#line 911
        }
        else
        {

#line 911
            live_0 = false;

#line 911
        }



        float _rx_0 = r_5[i_4].x;

#line 915
        float _ry_0 = r_5[i_4].y;
        if(live_0)
        {

#line 916
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 916
        }
        else
        {

#line 916
            n2_0 = 0U;

#line 916
        }

#line 916
        myMag_0[i_4] = n2_0;

#line 924
        uint off_0 = idx_1 - winStart_2;

#line 931
        if(live_0)
        {

#line 931
            if(binShift_1 >= int(0))
            {

#line 931
                b_4 = off_0 >> uint(binShift_1);

#line 931
            }
            else
            {

#line 931
                uint _S34 = off_0 / binsize_1;

#line 931
                b_4 = _S34;

#line 931
            }

#line 931
        }
        else
        {

#line 931
            b_4 = 0U;

#line 931
        }

#line 931
        myBin_0[i_4] = b_4;

#line 931
        bool _S35;



        if(nbins_1 > 1U)
        {

#line 935
            _S35 = (myMag_0[i_4]) > thrBits_1;

#line 935
        }
        else
        {

#line 935
            _S35 = false;

#line 935
        }

#line 935
        if(_S35)
        {

#line 936
            uint _S36 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_4]])), myMag_0[i_4], memory_order_relaxed);

#line 935
        }

#line 909
        i_4 = i_4 + 1U;

#line 909
    }

#line 909
    uint winner_0;

#line 959
    if(_S33)
    {

#line 959
        winner_0 = thrBits_1;

#line 959
        i_4 = 0U;


        for(;;)
        {

#line 962
            if(i_4 < 16U)
            {
            }
            else
            {

#line 962
                break;
            }

#line 962
            uint _S37 = max(winner_0, myMag_0[i_4]);

#line 962
            uint i_5 = i_4 + 1U;

#line 962
            winner_0 = _S37;

#line 962
            i_4 = i_5;

#line 962
        }

        uint wm_0 = simd_max(winner_0);
        bool _S38 = simd_is_first();

#line 965
        if(_S38)
        {

#line 965
            live_0 = wm_0 > thrBits_1;

#line 965
        }
        else
        {

#line 965
            live_0 = false;

#line 965
        }

#line 965
        if(live_0)
        {

#line 965
            uint _S39 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 965
        }

#line 959
    }

#line 980
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 987
    if(_S33)
    {

#line 987
        winner_0 = 4294967295U;

#line 987
        i_4 = 0U;


        for(;;)
        {

#line 990
            if(i_4 < 16U)
            {
            }
            else
            {

#line 990
                break;
            }

#line 991
            if((myMag_0[i_4]) > thrBits_1)
            {

#line 991
                live_0 = (myMag_0[i_4]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 991
            }
            else
            {

#line 991
                live_0 = false;

#line 991
            }

#line 991
            if(live_0)
            {

#line 991
                winner_0 = min(winner_0, tid_1 * 16U + i_4);

#line 991
            }

#line 990
            i_4 = i_4 + 1U;

#line 990
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S40 = simd_is_first();

#line 995
        if(_S40)
        {

#line 995
            live_0 = waveWinner_0 != 4294967295U;

#line 995
        }
        else
        {

#line 995
            live_0 = false;

#line 995
        }

#line 995
        if(live_0)
        {

#line 996
            uint _S41 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 995
        }

#line 1000
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1000
        i_4 = 0U;
        for(;;)
        {

#line 1001
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1001
                break;
            }

#line 1002
            uint _S42 = tid_1 * 16U + i_4;

#line 1002
            if(_S42 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 1003
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S42));

#line 1003
                *(peakVal_0+pair_0) = packed_float2(float2(r_5[i_4].x, r_5[i_4].y)) ;

#line 1002
            }

#line 1001
            i_4 = i_4 + 1U;

#line 1001
        }

#line 1011
        if(tid_1 == 0U)
        {

#line 1011
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1011
        }
        else
        {

#line 1011
            live_0 = false;

#line 1011
        }

#line 1011
        if(live_0)
        {

#line 1012
            *(peakIdx_0+pair_0) = int(-1);

#line 1012
            *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 1011
        }

#line 987
    }
    else
    {

#line 987
        i_4 = 0U;

#line 1020
        for(;;)
        {

#line 1020
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1020
                break;
            }

#line 1021
            if((myMag_0[i_4]) > thrBits_1)
            {

#line 1021
                live_0 = (myMag_0[i_4]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_4]];

#line 1021
            }
            else
            {

#line 1021
                live_0 = false;

#line 1021
            }

#line 1021
            myMag_0[i_4] = uint(live_0);

#line 1020
            i_4 = i_4 + 1U;

#line 1020
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1023
        b_4 = tid_1;
        for(;;)
        {

#line 1024
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 1024
                break;
            }

#line 1024
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4] = 4294967295U;

#line 1024
            b_4 = b_4 + 256U;

#line 1024
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1025
        i_4 = 0U;
        for(;;)
        {

#line 1026
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1026
                break;
            }

#line 1027
            if((myMag_0[i_4]) != 0U)
            {

#line 1027
                uint _S43 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_4]])), tid_1 * 16U + i_4, memory_order_relaxed);

#line 1027
            }

#line 1026
            i_4 = i_4 + 1U;

#line 1026
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1028
        i_4 = 0U;
        for(;;)
        {

#line 1029
            if(i_4 < 16U)
            {
            }
            else
            {

#line 1029
                break;
            }

#line 1030
            if((myMag_0[i_4]) != 0U)
            {

#line 1030
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_4]]) == (tid_1 * 16U + i_4);

#line 1030
            }
            else
            {

#line 1030
                live_0 = false;

#line 1030
            }

#line 1030
            if(live_0)
            {

#line 1031
                uint o_0 = pair_0 * nbins_1 + myBin_0[i_4];
                *(peakIdx_0+o_0) = int(slotToIndex_0(tid_1 * 16U + i_4));

#line 1032
                *(peakVal_0+o_0) = packed_float2(float2(r_5[i_4].x, r_5[i_4].y)) ;

#line 1030
            }

#line 1029
            i_4 = i_4 + 1U;

#line 1029
        }

#line 1029
        b_4 = tid_1;

#line 1036
        for(;;)
        {

#line 1036
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 1036
                break;
            }

#line 1037
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4]) == 4294967295U)
            {

#line 1038
                uint _S44 = pair_0 * nbins_1 + b_4;

#line 1038
                *(peakIdx_0+_S44) = int(-1);

#line 1038
                *(peakVal_0+_S44) = packed_float2(float2(0.0, 0.0)) ;

#line 1037
            }

#line 1036
            b_4 = b_4 + 256U;

#line 1036
        }

#line 987
    }

#line 1045
    return;
}


#line 1585
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1585
    thread KernelContext_0 kernelContext_5;

#line 1585
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1585
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1585
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1585
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1585
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1585
    (&kernelContext_5)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1585
    threadgroup array<uint, int(8192)> stg_1;

#line 1585
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1594
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1600
    (&kernelContext_5)->_stgBase_0 = 0U;
    thread uint ws_0 = entryPointParams_1->winStart_1;

#line 1601
    thread uint we_0 = entryPointParams_1->winEnd_1;
    uint _S45 = pair_1 / entryPointParams_1->ntmpl_0;

#line 1602
    rowWindow_0(_S45, &ws_0, &we_0);

#line 1602
    filterPair_0(pair_1, lid_0.x, (&kernelContext_5)->entryPointParams_data_0, (&kernelContext_5)->entryPointParams_tmpl_0, (&kernelContext_5)->entryPointParams_peakIdx_0, (&kernelContext_5)->entryPointParams_peakVal_0, entryPointParams_1->ntmpl_0, ws_0, we_0, (&kernelContext_5)->entryPointParams_0->binsize_0, (&kernelContext_5)->entryPointParams_0->binShift_0, (&kernelContext_5)->entryPointParams_0->nbins_0, (&kernelContext_5)->entryPointParams_0->thrBits_0, &kernelContext_5);


    return;
}
