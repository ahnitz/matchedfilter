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


#line 212 "mm_32768_refineListed.slang"
void rowWindow_0(uint d_0, uint thread* winStart_0, uint thread* winEnd_0)
{

#line 212
    return;
}


#line 168
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 168
    return float2(*(b_0+i_0)) ;
}


#line 286
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 286
    float _S2 = a_0.x;

#line 286
    float _S3 = b_1.x;

#line 286
    float _S4 = a_0.y;

#line 286
    float _S5 = b_1.y;

#line 286
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 84 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 285 "mm_32768_refineListed.slang"
float2 cmul_0(float2 a_1, float2 b_2)
{

#line 285
    float _S6 = a_1.x;

#line 285
    float _S7 = b_2.x;

#line 285
    float _S8 = a_1.y;

#line 285
    float _S9 = b_2.y;

#line 285
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 491
void r4_0(float2 thread* a_2, float2 thread* b_3, float2 thread* c_0, float2 thread* d_1)
{
    float2 t0_0 = *a_2 + *c_0;

#line 493
    float2 t1_0 = *a_2 - *c_0;

#line 493
    float2 t2_0 = *b_3 + *d_1;

#line 493
    float2 t3_0 = *b_3 - *d_1;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_2 = t0_0 + t2_0;

#line 495
    *b_3 = t1_0 + j3_0;

#line 495
    *c_0 = t0_0 - t2_0;

#line 495
    *d_1 = t1_0 - j3_0;
    return;
}


#line 527
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 534
    uint n1_0 = 0U;
    for(;;)
    {

#line 535
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 535
            break;
        }

#line 535
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 535
        n1_0 = n1_0 + 1U;

#line 535
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 536
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 536
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 537
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 537
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 538
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 538
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 538
    uint k2_0 = 0U;
    for(;;)
    {

#line 539
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 539
            break;
        }

#line 539
        uint _S10 = 4U * k2_0;

#line 539
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 539
        k2_0 = k2_0 + 1U;

#line 539
    }

    float2 t_0 = (*r_0)[int(1)];

#line 541
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 541
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 542
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 542
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 543
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 543
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 544
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 544
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 545
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 545
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 546
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 546
    (*r_0)[int(14)] = t_5;
    return;
}


#line 573
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 575
    thread array<float2, int(16)> v_0;

#line 575
    uint j_0 = 0U;
    for(;;)
    {

#line 576
        if(j_0 < 16U)
        {
        }
        else
        {

#line 576
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        v_0[j_0] = cmul_0((*r_1)[j_0] - (*r_1)[j_0 + 16U], mfTwiddle_0(6.28318548202514648f * float(j_0) / 32.0f));

#line 576
        j_0 = j_0 + 1U;

#line 576
    }

#line 582
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 583
    uint k_0 = 0U;
    for(;;)
    {

#line 584
        if(k_0 < 16U)
        {
        }
        else
        {

#line 584
            break;
        }

#line 584
        uint _S11 = 2U * k_0;

#line 584
        (*r_1)[_S11] = u_0[k_0];

#line 584
        (*r_1)[_S11 + 1U] = v_0[k_0];

#line 584
        k_0 = k_0 + 1U;

#line 584
    }
    return;
}


#line 612
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 287
uint computeWant_0(uint d_2, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 289
    uint j_1 = d_2 / _S12;

#line 289
    uint m_0 = d_2 % _S12;

#line 289
    uint _S13;
    if(TB_0 <= 32U)
    {

#line 290
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 290
    }
    else
    {

#line 290
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_2;

#line 290
    }

#line 290
    return _S13;
}


#line 8599 "hlsl.meta.slang"
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


#line 274 "mm_32768_refineListed.slang"
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
    array<uint, int(16384)> threadgroup* stg_0;
};


#line 274
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 274
    uint _S14 = 2U * i_1;

#line 274
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14] = (as_type<uint>((v_1.x)));

#line 274
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14 + 1U] = (as_type<uint>((v_1.y)));

#line 274
    return;
}


#line 275
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 275
    uint _S15 = 2U * i_2;

#line 275
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15 + 1U]))));
}


#line 716
void exchange_0(array<float2, int(32)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 717
    uint j_2;

#line 728
    thread array<float2, int(32)> out_0;

#line 728
    uint z_0 = 0U;
    for(;;)
    {

#line 729
        if(z_0 < 32U)
        {
        }
        else
        {

#line 729
            break;
        }

#line 729
        out_0[z_0] = float2(0.0f, 0.0f);

#line 729
        z_0 = z_0 + 1U;

#line 729
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S16 = p0_0 & lenMask_0;

#line 735
    uint _S17 = _S16 >> lgSpan_0;

#line 735
    uint _S18 = _S17 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 735
    uint c_1 = 0U;

    for(;;)
    {

#line 737
        if(c_1 < 4U)
        {
        }
        else
        {

#line 737
            break;
        }

#line 738
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 738
        j_2 = 0U;
        for(;;)
        {

#line 739
            if(j_2 < 8U)
            {
            }
            else
            {

#line 739
                break;
            }

#line 739
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 8U + j_2], kernelContext_2);

#line 739
            j_2 = j_2 + 1U;

#line 739
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 740
        uint d_3 = 0U;
        for(;;)
        {

#line 741
            if(d_3 < 32U)
            {
            }
            else
            {

#line 741
                break;
            }

#line 742
            uint pz_0 = computeWant_0(d_3, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S19 = pz_0 & lenMask_0;

#line 743
            uint iz_0 = _S19 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S19 & spanMask_0);
            uint i_3 = _S17 + iz_0;
            uint _S20 = c_1 * 8U;

#line 746
            bool _S21;

#line 746
            if(i_3 >= _S20)
            {

#line 746
                _S21 = i_3 < ((c_1 + 1U) * 8U);

#line 746
            }
            else
            {

#line 746
                _S21 = false;

#line 746
            }

#line 746
            if(_S21)
            {

#line 746
                float2 _S22 = stgGet_0(_S18 + az_0 - _S20 * 1024U, kernelContext_2);
                out_0[d_3] = _S22;

#line 746
            }

#line 741
            d_3 = d_3 + 1U;

#line 741
        }

#line 737
        c_1 = c_1 + 1U;

#line 737
    }

#line 737
    j_2 = 0U;

#line 750
    for(;;)
    {

#line 750
        if(j_2 < 32U)
        {
        }
        else
        {

#line 750
            break;
        }

#line 750
        (*r_3)[j_2] = out_0[j_2];

#line 750
        j_2 = j_2 + 1U;

#line 750
    }
    return;
}


#line 630
void innermost_0(array<float2, int(32)> thread* r_4)
{

    dft32_0(r_4);

#line 642
    return;
}


#line 818
void transform_0(array<float2, int(32)> thread* r_5, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 818
    uint _S23;

#line 818
    uint k2_1;

#line 818
    float cr_0;

#line 818
    float ci_0;

#line 818
    uint _S24;

#line 818
    for(;;)
    {

#line 818
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(1024U);

#line 11
                _S23 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(32768U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 1023U;

#line 19
                dftR_0(r_5);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 32768.0f);
                float _S25 = tw_0.x;

#line 40
                float _S26 = tw_0.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 32U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_5)[k2_1] = cmul_0((*r_5)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S25 - ci_0 * _S26;
                    float _S27 = cr_0 * _S26 + ci_0 * _S25;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_0;

#line 42
                    ci_0 = _S27;

#line 42
                }

#line 50
                uint per_2 = 32U / max(1024U, 1U);
                uint _S28 = max(32U, 1U);

#line 51
                _S24 = _S28;
                uint blk2_2 = tid_0 / _S28;

#line 52
                uint lane2_2 = tid_0 % _S28;

#line 52
                exchange_0(r_5, lgLn_0, lgTB_0, 1024U, 32768U, blk_2, lane_2, per_2, _S28, 1024U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(32U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 31U;

#line 19
                dftR_0(r_5);

#line 39
                float2 tw_1 = mfTwiddle_0(6.28318548202514648f * float(lane_3) / 1024.0f);
                float _S29 = tw_1.x;

#line 40
                float _S30 = tw_1.y;

#line 40
                k2_1 = 0U;

#line 40
                cr_0 = 1.0f;

#line 40
                ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 32U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_5)[k2_1] = cmul_0((*r_5)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S29 - ci_0 * _S30;
                    float _S31 = cr_0 * _S30 + ci_0 * _S29;

#line 42
                    k2_1 = k2_1 + 1U;

#line 42
                    cr_0 = nr_1;

#line 42
                    ci_0 = _S31;

#line 42
                }

#line 50
                uint per_3 = 32U / _S24;
                uint _S32 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S32;

#line 52
                uint lane2_3 = tid_0 % _S32;

#line 52
                exchange_0(r_5, _S23, lgTB_1, 32U, 1024U, blk_3, lane_3, per_3, _S32, 32U, blk2_3, lane2_3, kernelContext_3);

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
    innermost_0(r_5);

#line 821 "mm_32768_refineListed.slang"
    return;
}


#line 775
uint lgOf_0(uint i_4)
{

#line 775
    uint _S33;

#line 775
    if(i_4 < 2U)
    {

#line 775
        _S33 = 5U;

#line 775
    }
    else
    {

#line 775
        if(i_4 == 2U)
        {

#line 775
            _S33 = 5U;

#line 775
        }
        else
        {

#line 775
            _S33 = 1U;

#line 775
        }

#line 775
    }

#line 775
    return _S33;
}


#line 777
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 781
    uint lg_1 = lgOf_0(1U);

#line 781
    uint lg_2 = lgOf_0(0U);

#line 786
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 841
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_2, uint winEnd_2, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 861
    kernelContext_4->_tid_0 = tid_1;
    uint _S34 = pair_0 / ntmpl_1;

#line 862
    uint _S35 = pair_0 % ntmpl_1;

#line 867
    thread array<float2, int(32)> r_6;

#line 867
    uint n2_0 = 0U;

#line 878
    for(;;)
    {

#line 878
        if(n2_0 < 32U)
        {
        }
        else
        {

#line 878
            break;
        }

#line 879
        uint idx_0 = tid_1 + 1024U * n2_0;
        r_6[n2_0] = cmulConj_0(cload_0(data_0, _S34 * 32768U + idx_0), cload_0(tmpl_0, _S35 * 32768U + idx_0));

#line 878
        n2_0 = n2_0 + 1U;

#line 878
    }

#line 878
    transform_0(&r_6, tid_1, kernelContext_4);

#line 907
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 907
    uint b_4 = tid_1;

#line 1019
    for(;;)
    {

#line 1019
        if(b_4 < nbins_1)
        {
        }
        else
        {

#line 1019
            break;
        }

#line 1019
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4] = thrBits_1;

#line 1019
        b_4 = b_4 + 1024U;

#line 1019
    }
    bool _S36 = nbins_1 == 1U;

#line 1020
    bool live_0;

#line 1020
    if(_S36)
    {

#line 1020
        live_0 = tid_1 == 0U;

#line 1020
    }
    else
    {

#line 1020
        live_0 = false;

#line 1020
    }

#line 1020
    if(live_0)
    {

#line 1020
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 1020
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1079
    thread array<uint, int(32)> myMag_0;
    thread array<uint, int(32)> myBin_0;

#line 1080
    uint i_5 = 0U;



    for(;;)
    {

#line 1084
        if(i_5 < 32U)
        {
        }
        else
        {

#line 1084
            break;
        }

#line 1085
        uint idx_1 = slotToIndex_0(tid_1 * 32U + i_5);
        if(idx_1 >= winStart_2)
        {

#line 1086
            live_0 = idx_1 < winEnd_2;

#line 1086
        }
        else
        {

#line 1086
            live_0 = false;

#line 1086
        }



        float _rx_0 = r_6[i_5].x;

#line 1090
        float _ry_0 = r_6[i_5].y;
        if(live_0)
        {

#line 1091
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1091
        }
        else
        {

#line 1091
            n2_0 = 0U;

#line 1091
        }

#line 1091
        myMag_0[i_5] = n2_0;

#line 1099
        uint off_0 = idx_1 - winStart_2;

#line 1106
        if(live_0)
        {

#line 1106
            if(binShift_1 >= int(0))
            {

#line 1106
                b_4 = off_0 >> uint(binShift_1);

#line 1106
            }
            else
            {

#line 1106
                uint _S37 = off_0 / binsize_1;

#line 1106
                b_4 = _S37;

#line 1106
            }

#line 1106
        }
        else
        {

#line 1106
            b_4 = 0U;

#line 1106
        }

#line 1106
        myBin_0[i_5] = b_4;

#line 1106
        bool _S38;



        if(nbins_1 > 1U)
        {

#line 1110
            _S38 = (myMag_0[i_5]) > thrBits_1;

#line 1110
        }
        else
        {

#line 1110
            _S38 = false;

#line 1110
        }

#line 1110
        if(_S38)
        {

#line 1111
            uint _S39 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), myMag_0[i_5], memory_order_relaxed);

#line 1110
        }

#line 1084
        i_5 = i_5 + 1U;

#line 1084
    }

#line 1084
    uint winner_0;

#line 1134
    if(_S36)
    {

#line 1134
        winner_0 = thrBits_1;

#line 1134
        i_5 = 0U;


        for(;;)
        {

#line 1137
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1137
                break;
            }

#line 1137
            uint _S40 = max(winner_0, myMag_0[i_5]);

#line 1137
            uint i_6 = i_5 + 1U;

#line 1137
            winner_0 = _S40;

#line 1137
            i_5 = i_6;

#line 1137
        }

        uint wm_0 = simd_max(winner_0);
        bool _S41 = simd_is_first();

#line 1140
        if(_S41)
        {

#line 1140
            live_0 = wm_0 > thrBits_1;

#line 1140
        }
        else
        {

#line 1140
            live_0 = false;

#line 1140
        }

#line 1140
        if(live_0)
        {

#line 1140
            uint _S42 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1140
        }

#line 1134
    }

#line 1155
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1162
    if(_S36)
    {

#line 1162
        winner_0 = 4294967295U;

#line 1162
        i_5 = 0U;


        for(;;)
        {

#line 1165
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1165
                break;
            }

#line 1166
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1166
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 1166
            }
            else
            {

#line 1166
                live_0 = false;

#line 1166
            }

#line 1166
            if(live_0)
            {

#line 1166
                winner_0 = min(winner_0, tid_1 * 32U + i_5);

#line 1166
            }

#line 1165
            i_5 = i_5 + 1U;

#line 1165
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S43 = simd_is_first();

#line 1170
        if(_S43)
        {

#line 1170
            live_0 = waveWinner_0 != 4294967295U;

#line 1170
        }
        else
        {

#line 1170
            live_0 = false;

#line 1170
        }

#line 1170
        if(live_0)
        {

#line 1171
            uint _S44 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1170
        }

#line 1175
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1175
        i_5 = 0U;
        for(;;)
        {

#line 1176
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1176
                break;
            }

#line 1177
            uint _S45 = tid_1 * 32U + i_5;

#line 1177
            if(_S45 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 1178
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S45));

#line 1178
                *(peakVal_0+pair_0) = packed_float2(float2(r_6[i_5].x, r_6[i_5].y)) ;

#line 1177
            }

#line 1176
            i_5 = i_5 + 1U;

#line 1176
        }

#line 1186
        if(tid_1 == 0U)
        {

#line 1186
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

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
            *(peakIdx_0+pair_0) = int(-1);

#line 1187
            *(peakVal_0+pair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1186
        }

#line 1162
    }
    else
    {

#line 1162
        i_5 = 0U;

#line 1195
        for(;;)
        {

#line 1195
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1195
                break;
            }

#line 1196
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1196
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]];

#line 1196
            }
            else
            {

#line 1196
                live_0 = false;

#line 1196
            }

#line 1196
            myMag_0[i_5] = uint(live_0);

#line 1195
            i_5 = i_5 + 1U;

#line 1195
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1198
        b_4 = tid_1;
        for(;;)
        {

#line 1199
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 1199
                break;
            }

#line 1199
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4] = 4294967295U;

#line 1199
            b_4 = b_4 + 1024U;

#line 1199
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1200
        i_5 = 0U;
        for(;;)
        {

#line 1201
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1201
                break;
            }

#line 1202
            if((myMag_0[i_5]) != 0U)
            {

#line 1202
                uint _S46 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), tid_1 * 32U + i_5, memory_order_relaxed);

#line 1202
            }

#line 1201
            i_5 = i_5 + 1U;

#line 1201
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1203
        i_5 = 0U;
        for(;;)
        {

#line 1204
            if(i_5 < 32U)
            {
            }
            else
            {

#line 1204
                break;
            }

#line 1205
            if((myMag_0[i_5]) != 0U)
            {

#line 1205
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]]) == (tid_1 * 32U + i_5);

#line 1205
            }
            else
            {

#line 1205
                live_0 = false;

#line 1205
            }

#line 1205
            if(live_0)
            {

#line 1206
                uint o_0 = pair_0 * nbins_1 + myBin_0[i_5];
                *(peakIdx_0+o_0) = int(slotToIndex_0(tid_1 * 32U + i_5));

#line 1207
                *(peakVal_0+o_0) = packed_float2(float2(r_6[i_5].x, r_6[i_5].y)) ;

#line 1205
            }

#line 1204
            i_5 = i_5 + 1U;

#line 1204
        }

#line 1204
        b_4 = tid_1;

#line 1211
        for(;;)
        {

#line 1211
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 1211
                break;
            }

#line 1212
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4]) == 4294967295U)
            {

#line 1213
                uint _S47 = pair_0 * nbins_1 + b_4;

#line 1213
                *(peakIdx_0+_S47) = int(-1);

#line 1213
                *(peakVal_0+_S47) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1212
            }

#line 1211
            b_4 = b_4 + 1024U;

#line 1211
        }

#line 1162
    }

#line 1221
    return;
}


#line 1879
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1879
    thread KernelContext_0 kernelContext_5;

#line 1879
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1879
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1879
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1879
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1879
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1879
    (&kernelContext_5)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1879
    threadgroup array<uint, int(16384)> stg_1;

#line 1879
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1888
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1894
    (&kernelContext_5)->_stgBase_0 = 0U;
    thread uint ws_0 = entryPointParams_1->winStart_1;

#line 1895
    thread uint we_0 = entryPointParams_1->winEnd_1;
    uint _S48 = pair_1 / entryPointParams_1->ntmpl_0;

#line 1896
    rowWindow_0(_S48, &ws_0, &we_0);

#line 1896
    filterPair_0(pair_1, lid_0.x, (&kernelContext_5)->entryPointParams_data_0, (&kernelContext_5)->entryPointParams_tmpl_0, (&kernelContext_5)->entryPointParams_peakIdx_0, (&kernelContext_5)->entryPointParams_peakVal_0, entryPointParams_1->ntmpl_0, ws_0, we_0, (&kernelContext_5)->entryPointParams_0->binsize_0, (&kernelContext_5)->entryPointParams_0->binShift_0, (&kernelContext_5)->entryPointParams_0->nbins_0, (&kernelContext_5)->entryPointParams_0->thrBits_0, &kernelContext_5);


    return;
}
