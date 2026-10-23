#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
#ifndef MF_DATA_STRIDE
#define MF_DATA_STRIDE 0u
#endif
#ifndef MF_ACCURATE_TRIG
#define MF_ACCURATE_TRIG 0u
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


#line 72 "twiddle.slang"
uint mfDataStrideFlag_0()
{
    ;
    uint _S2 = ((MF_DATA_STRIDE));

#line 75
    return _S2;
}


#line 174 "mm_128_refineItems.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 174
    return float2(*(b_0+i_0)) ;
}


#line 324
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 324
    float _S3 = a_0.x;

#line 324
    float _S4 = b_1.x;

#line 324
    float _S5 = a_0.y;

#line 324
    float _S6 = b_1.y;

#line 324
    return float2(_S3 * _S4 + _S5 * _S6, _S5 * _S4 - _S3 * _S6);
}


#line 529
void r4_0(float2 thread* a_1, float2 thread* b_2, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 531
    float2 t1_0 = *a_1 - *c_0;

#line 531
    float2 t2_0 = *b_2 + *d_0;

#line 531
    float2 t3_0 = *b_2 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 533
    *b_2 = t1_0 + j3_0;

#line 533
    *c_0 = t0_0 - t2_0;

#line 533
    *d_0 = t1_0 - j3_0;
    return;
}


#line 323
float2 cmul_0(float2 a_2, float2 b_3)
{

#line 323
    float _S7 = a_2.x;

#line 323
    float _S8 = b_3.x;

#line 323
    float _S9 = a_2.y;

#line 323
    float _S10 = b_3.y;

#line 323
    return float2(_S7 * _S8 - _S9 * _S10, _S7 * _S10 + _S9 * _S8);
}


#line 565
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 572
    uint n1_0 = 0U;
    for(;;)
    {

#line 573
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 573
            break;
        }

#line 573
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 573
        n1_0 = n1_0 + 1U;

#line 573
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 574
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 574
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 575
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 575
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 576
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 576
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 576
    uint k2_0 = 0U;
    for(;;)
    {

#line 577
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 577
            break;
        }

#line 577
        uint _S11 = 4U * k2_0;

#line 577
        r4_0(&(*r_0)[_S11], &(*r_0)[_S11 + 1U], &(*r_0)[_S11 + 2U], &(*r_0)[_S11 + 3U]);

#line 577
        k2_0 = k2_0 + 1U;

#line 577
    }

    float2 t_0 = (*r_0)[int(1)];

#line 579
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 579
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 580
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 580
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 581
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 581
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 582
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 582
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 583
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 583
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 584
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 584
    (*r_0)[int(14)] = t_5;
    return;
}


#line 88 "twiddle.slang"
uint mfAccurateTrigFlag_0()
{
    ;
    uint _S12 = ((MF_ACCURATE_TRIG));

#line 91
    return _S12;
}


#line 127
float2 mfTwiddle_0(float angle_0)
{

#line 93
    uint _S13 = mfAccurateTrigFlag_0();

#line 129
    if(_S13 == 0U)
    {

#line 130
        return float2(cos(angle_0), sin(angle_0));
    }

    int quadrant_0 = int(floor(angle_0 * 0.63661974668502808f + 0.5f));
    float _S14 = float(quadrant_0);
    float x_0 = angle_0 - _S14 * 1.57079625129699707f - _S14 * 7.54978941586159635e-08f;
    float z_0 = x_0 * x_0;
    float c_1 = 1.0f + z_0 * (-0.5f + z_0 * (0.0416666679084301f + z_0 * (-0.00138888892251998f + z_0 * (0.00002480158764229f + z_0 * -2.75573199814971304e-07f))));

    float s_0 = x_0 * (1.0f + z_0 * (-0.1666666716337204f + z_0 * (0.00833333376795053f + z_0 * (-0.0001984127011383f + z_0 * (2.75573188446287531e-06f + z_0 * -2.50521079436794025e-08f)))));


    switch(quadrant_0 & int(3))
    {
    case int(1):
        {

#line 143
            return float2(- s_0, c_1);
        }
    case int(2):
        {

#line 144
            return float2(- c_1, - s_0);
        }
    case int(3):
        {

#line 145
            return float2(s_0, - c_1);
        }
    default:
        {

#line 146
            return float2(c_1, s_0);
        }
    }

#line 146
}


#line 325 "mm_128_refineItems.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S15 = max(TB_0, 1U);

#line 327
    uint j_0 = d_1 / _S15;

#line 327
    uint m_0 = d_1 % _S15;

#line 327
    uint _S16;
    if(TB_0 <= 16U)
    {

#line 328
        _S16 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 328
    }
    else
    {

#line 328
        _S16 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 328
    }

#line 328
    return _S16;
}


#line 8599 "hlsl.meta.slang"
struct EntryPointParams_0
{
    uint ntmpl_0;
    uint binsize_0;
    int binShift_0;
    uint nbins_0;
    uint thrBits_0;
    uint gridSize_0;
};


#line 312 "mm_128_refineItems.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_items_0;
    uint device* entryPointParams_count_0;
    uint _stgBase_0;
    uint _binPhase_0;
    uint _tid_0;
    array<uint, int(256)> threadgroup* stg_0;
};


#line 312
void stgPut_0(uint i_1, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 312
    uint _S17 = 2U * i_1;

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S17] = (as_type<uint>((v_0.x)));

#line 312
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S17 + 1U] = (as_type<uint>((v_0.y)));

#line 312
    return;
}


#line 313
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 313
    uint _S18 = 2U * i_2;

#line 313
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S18]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S18 + 1U]))));
}


#line 754
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 755
    uint j_1;

#line 766
    thread array<float2, int(16)> out_0;

#line 766
    uint z_1 = 0U;
    for(;;)
    {

#line 767
        if(z_1 < 16U)
        {
        }
        else
        {

#line 767
            break;
        }

#line 767
        out_0[z_1] = float2(0.0f, 0.0f);

#line 767
        z_1 = z_1 + 1U;

#line 767
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S19 = p0_0 & lenMask_0;

#line 773
    uint _S20 = (_S19 >> lgSpan_0) * 8U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S19 & spanMask_0);

#line 773
    uint c_2 = 0U;

    for(;;)
    {

#line 775
        if(c_2 < 1U)
        {
        }
        else
        {

#line 775
            break;
        }

#line 776
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 776
        j_1 = 0U;
        for(;;)
        {

#line 777
            if(j_1 < 16U)
            {
            }
            else
            {

#line 777
                break;
            }

#line 777
            stgPut_0(j_1 * 8U + kernelContext_2->_tid_0, (*r_1)[c_2 * 16U + j_1], kernelContext_2);

#line 777
            j_1 = j_1 + 1U;

#line 777
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 778
        uint d_2 = 0U;
        for(;;)
        {

#line 779
            if(d_2 < 16U)
            {
            }
            else
            {

#line 779
                break;
            }

#line 780
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S21 = pz_0 & lenMask_0;
            uint az_0 = (_S21 >> lgSpan_0) * 8U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S21 & spanMask_0);

#line 782
            float2 _S22 = stgGet_0(_S20 + az_0 - c_2 * 16U * 8U, kernelContext_2);


            out_0[d_2] = _S22;

#line 779
            d_2 = d_2 + 1U;

#line 779
        }

#line 775
        c_2 = c_2 + 1U;

#line 775
    }

#line 775
    j_1 = 0U;

#line 788
    for(;;)
    {

#line 788
        if(j_1 < 16U)
        {
        }
        else
        {

#line 788
            break;
        }

#line 788
        (*r_1)[j_1] = out_0[j_1];

#line 788
        j_1 = j_1 + 1U;

#line 788
    }
    return;
}


#line 549
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_4;

#line 553
    uint s_1 = 1U;
    for(;;)
    {

#line 554
        if(s_1 < 8U)
        {
        }
        else
        {

#line 554
            break;
        }

#line 554
        uint j_2 = 0U;
        for(;;)
        {

#line 555
            if(j_2 < 4U)
            {
            }
            else
            {

#line 555
                break;
            }

#line 556
            uint k_0 = j_2 & (s_1 - 1U);

#line 556
            uint base_0 = (j_2 - k_0) << 1U;

            float2 w_0 = mfTwiddle_0(3.14159274101257324f * float(k_0) / float(s_1));
            uint _S23 = o_0 + j_2;

#line 559
            float2 t_6 = cmul_0(w_0, (*r_2)[_S23 + 4U]);
            uint _S24 = base_0 + k_0;

#line 560
            b_4[_S24] = (*r_2)[_S23] + t_6;

#line 560
            b_4[_S24 + s_1] = (*r_2)[_S23] - t_6;

#line 555
            j_2 = j_2 + 1U;

#line 555
        }

#line 555
        uint i_3 = 0U;

#line 562
        for(;;)
        {

#line 562
            if(i_3 < 8U)
            {
            }
            else
            {

#line 562
                break;
            }

#line 562
            (*r_2)[o_0 + i_3] = b_4[i_3];

#line 562
            i_3 = i_3 + 1U;

#line 562
        }

#line 554
        s_1 = s_1 << 1U;

#line 554
    }

#line 564
    return;
}


#line 668
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 668
    uint b_5 = 0U;

#line 676
    for(;;)
    {

#line 676
        if(b_5 < 2U)
        {
        }
        else
        {

#line 676
            break;
        }

#line 676
        dft8_0(r_3, b_5 * 8U);

#line 676
        b_5 = b_5 + 1U;

#line 676
    }



    return;
}


#line 856
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 856
    for(;;)
    {

#line 856
        for(;;)
        {

#line 7 "fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(8U);
                uint lgLn_0 = firstbithigh_0(128U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 7U;


                dft16_0(r_4);

#line 39
                float2 tw_0 = mfTwiddle_0(6.28318548202514648f * float(lane_2) / 128.0f);
                float _S25 = tw_0.x;

#line 40
                float _S26 = tw_0.y;

#line 40
                uint k2_1 = 0U;

#line 40
                float cr_0 = 1.0f;

#line 40
                float ci_0 = 0.0f;

                for(;;)
                {

#line 42
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 42
                        break;
                    }

#line 43
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
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
                uint per_2 = 16U / max(8U, 1U);
                uint _S28 = max(0U, 1U);
                uint blk2_2 = tid_0 / _S28;

#line 52
                uint lane2_2 = tid_0 % _S28;

#line 52
                exchange_0(r_4, lgLn_0, lgTB_0, 8U, 128U, blk_2, lane_2, per_2, _S28, 8U, blk2_2, lane2_2, kernelContext_3);

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

#line 859 "mm_128_refineItems.slang"
    return;
}


#line 813
uint lgOf_0(uint i_4)
{

#line 813
    uint _S29;

#line 813
    if(i_4 < 1U)
    {

#line 813
        _S29 = 4U;

#line 813
    }
    else
    {

#line 813
        if(i_4 == 1U)
        {

#line 813
            _S29 = 3U;

#line 813
        }
        else
        {

#line 813
            _S29 = 1U;

#line 813
        }

#line 813
    }

#line 813
    return _S29;
}


#line 815
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(1U);

#line 819
    uint lg_1 = lgOf_0(0U);

#line 824
    return (((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | ((slot_0 >> lg_0) & ((1U << lg_1) - 1U));
}


#line 873
void filterPairOut_0(uint pair_0, uint opair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_0, uint winEnd_0, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{


    uint b_6;

#line 900
    kernelContext_4->_tid_0 = tid_1;
    uint _S30 = pair_0 / ntmpl_1;

#line 901
    uint _S31 = pair_0 % ntmpl_1;

#line 906
    thread array<float2, int(16)> r_5;

#line 906
    uint n2_0 = 0U;

#line 917
    for(;;)
    {

#line 917
        if(n2_0 < 16U)
        {
        }
        else
        {

#line 917
            break;
        }

#line 918
        uint idx_0 = tid_1 + 8U * n2_0;

#line 77 "twiddle.slang"
        uint _S32 = mfDataStrideFlag_0();

#line 177 "mm_128_refineItems.slang"
        if(_S32 != 0U)
        {

#line 77 "twiddle.slang"
            uint _S33 = mfDataStrideFlag_0();

#line 77
            b_6 = _S33;

#line 177 "mm_128_refineItems.slang"
        }
        else
        {

#line 177
            b_6 = 128U;

#line 177
        }

#line 919
        r_5[n2_0] = cmulConj_0(cload_0(data_0, _S30 * b_6 + idx_0), cload_0(tmpl_0, _S31 * 128U + idx_0));

#line 917
        n2_0 = n2_0 + 1U;

#line 917
    }

#line 917
    transform_0(&r_5, tid_1, kernelContext_4);

#line 946
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 946
    b_6 = tid_1;

#line 1058
    for(;;)
    {

#line 1058
        if(b_6 < nbins_1)
        {
        }
        else
        {

#line 1058
            break;
        }

#line 1058
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6] = thrBits_1;

#line 1058
        b_6 = b_6 + 8U;

#line 1058
    }
    bool _S34 = nbins_1 == 1U;

#line 1059
    bool live_0;

#line 1059
    if(_S34)
    {

#line 1059
        live_0 = tid_1 == 0U;

#line 1059
    }
    else
    {

#line 1059
        live_0 = false;

#line 1059
    }

#line 1059
    if(live_0)
    {

#line 1059
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 1059
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1118
    thread array<uint, int(16)> myMag_0;
    thread array<uint, int(16)> myBin_0;

#line 1119
    uint i_5 = 0U;



    for(;;)
    {

#line 1123
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1123
            break;
        }

#line 1124
        uint idx_1 = slotToIndex_0(tid_1 * 16U + i_5);
        if(idx_1 >= winStart_0)
        {

#line 1125
            live_0 = idx_1 < winEnd_0;

#line 1125
        }
        else
        {

#line 1125
            live_0 = false;

#line 1125
        }



        float _rx_0 = r_5[i_5].x;

#line 1129
        float _ry_0 = r_5[i_5].y;
        if(live_0)
        {

#line 1130
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 1130
        }
        else
        {

#line 1130
            n2_0 = 0U;

#line 1130
        }

#line 1130
        myMag_0[i_5] = n2_0;

#line 1138
        uint off_0 = idx_1 - winStart_0 + kernelContext_4->_binPhase_0;

#line 1145
        if(live_0)
        {

#line 1145
            if(binShift_1 >= int(0))
            {

#line 1145
                b_6 = off_0 >> uint(binShift_1);

#line 1145
            }
            else
            {

#line 1145
                uint _S35 = off_0 / binsize_1;

#line 1145
                b_6 = _S35;

#line 1145
            }

#line 1145
        }
        else
        {

#line 1145
            b_6 = 0U;

#line 1145
        }

#line 1145
        myBin_0[i_5] = b_6;

#line 1145
        bool _S36;



        if(nbins_1 > 1U)
        {

#line 1149
            _S36 = (myMag_0[i_5]) > thrBits_1;

#line 1149
        }
        else
        {

#line 1149
            _S36 = false;

#line 1149
        }

#line 1149
        if(_S36)
        {

#line 1150
            uint _S37 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), myMag_0[i_5], memory_order_relaxed);

#line 1149
        }

#line 1123
        i_5 = i_5 + 1U;

#line 1123
    }

#line 1123
    uint winner_0;

#line 1173
    if(_S34)
    {

#line 1173
        winner_0 = thrBits_1;

#line 1173
        i_5 = 0U;


        for(;;)
        {

#line 1176
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1176
                break;
            }

#line 1176
            uint _S38 = max(winner_0, myMag_0[i_5]);

#line 1176
            uint i_6 = i_5 + 1U;

#line 1176
            winner_0 = _S38;

#line 1176
            i_5 = i_6;

#line 1176
        }

        uint wm_0 = simd_max(winner_0);
        bool _S39 = simd_is_first();

#line 1179
        if(_S39)
        {

#line 1179
            live_0 = wm_0 > thrBits_1;

#line 1179
        }
        else
        {

#line 1179
            live_0 = false;

#line 1179
        }

#line 1179
        if(live_0)
        {

#line 1179
            uint _S40 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 1179
        }

#line 1173
    }

#line 1194
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1201
    if(_S34)
    {

#line 1201
        winner_0 = 4294967295U;

#line 1201
        i_5 = 0U;


        for(;;)
        {

#line 1204
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1204
                break;
            }

#line 1205
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1205
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

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

#line 1205
                winner_0 = min(winner_0, tid_1 * 16U + i_5);

#line 1205
            }

#line 1204
            i_5 = i_5 + 1U;

#line 1204
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S41 = simd_is_first();

#line 1209
        if(_S41)
        {

#line 1209
            live_0 = waveWinner_0 != 4294967295U;

#line 1209
        }
        else
        {

#line 1209
            live_0 = false;

#line 1209
        }

#line 1209
        if(live_0)
        {

#line 1210
            uint _S42 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 1209
        }

#line 1214
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1214
        i_5 = 0U;
        for(;;)
        {

#line 1215
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1215
                break;
            }

#line 1216
            uint _S43 = tid_1 * 16U + i_5;

#line 1216
            if(_S43 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 1217
                *(peakIdx_0+opair_0) = int(slotToIndex_0(_S43));

#line 1217
                *(peakVal_0+opair_0) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 1216
            }

#line 1215
            i_5 = i_5 + 1U;

#line 1215
        }

#line 1225
        if(tid_1 == 0U)
        {

#line 1225
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 1225
        }
        else
        {

#line 1225
            live_0 = false;

#line 1225
        }

#line 1225
        if(live_0)
        {

#line 1226
            *(peakIdx_0+opair_0) = int(-1);

#line 1226
            *(peakVal_0+opair_0) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1225
        }

#line 1201
    }
    else
    {

#line 1201
        i_5 = 0U;

#line 1234
        for(;;)
        {

#line 1234
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1234
                break;
            }

#line 1235
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 1235
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]];

#line 1235
            }
            else
            {

#line 1235
                live_0 = false;

#line 1235
            }

#line 1235
            myMag_0[i_5] = uint(live_0);

#line 1234
            i_5 = i_5 + 1U;

#line 1234
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1237
        b_6 = tid_1;
        for(;;)
        {

#line 1238
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 1238
                break;
            }

#line 1238
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6] = 4294967295U;

#line 1238
            b_6 = b_6 + 8U;

#line 1238
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1239
        i_5 = 0U;
        for(;;)
        {

#line 1240
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1240
                break;
            }

#line 1241
            if((myMag_0[i_5]) != 0U)
            {

#line 1241
                uint _S44 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), tid_1 * 16U + i_5, memory_order_relaxed);

#line 1241
            }

#line 1240
            i_5 = i_5 + 1U;

#line 1240
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 1242
        i_5 = 0U;
        for(;;)
        {

#line 1243
            if(i_5 < 16U)
            {
            }
            else
            {

#line 1243
                break;
            }

#line 1244
            if((myMag_0[i_5]) != 0U)
            {

#line 1244
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]]) == (tid_1 * 16U + i_5);

#line 1244
            }
            else
            {

#line 1244
                live_0 = false;

#line 1244
            }

#line 1244
            if(live_0)
            {

#line 1245
                uint o_1 = opair_0 * nbins_1 + myBin_0[i_5];
                *(peakIdx_0+o_1) = int(slotToIndex_0(tid_1 * 16U + i_5));

#line 1246
                *(peakVal_0+o_1) = packed_float2(float2(r_5[i_5].x, r_5[i_5].y)) ;

#line 1244
            }

#line 1243
            i_5 = i_5 + 1U;

#line 1243
        }

#line 1243
        b_6 = tid_1;

#line 1250
        for(;;)
        {

#line 1250
            if(b_6 < nbins_1)
            {
            }
            else
            {

#line 1250
                break;
            }

#line 1251
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_6]) == 4294967295U)
            {

#line 1252
                uint _S45 = opair_0 * nbins_1 + b_6;

#line 1252
                *(peakIdx_0+_S45) = int(-1);

#line 1252
                *(peakVal_0+_S45) = packed_float2(float2(0.0f, 0.0f)) ;

#line 1251
            }

#line 1250
            b_6 = b_6 + 8U;

#line 1250
        }

#line 1201
    }

#line 1260
    return;
}


#line 2197
[[kernel]] void refineItems(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_items_1 [[buffer(5)]], uint device* entryPointParams_count_1 [[buffer(6)]])
{

#line 2197
    thread KernelContext_0 kernelContext_5;

#line 2197
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 2197
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 2197
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 2197
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 2197
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 2197
    (&kernelContext_5)->entryPointParams_items_0 = entryPointParams_items_1;

#line 2197
    (&kernelContext_5)->entryPointParams_count_0 = entryPointParams_count_1;

#line 2197
    threadgroup array<uint, int(256)> stg_1;

#line 2197
    (&kernelContext_5)->stg_0 = &stg_1;

#line 2197
    (&kernelContext_5)->_binPhase_0 = 0U;

#line 2206
    uint _S46 = entryPointParams_count_1[int(0)];

#line 2206
    uint i_7 = gid_0.x;
    for(;;)
    {

#line 2207
        if(i_7 < _S46)
        {
        }
        else
        {

#line 2207
            break;
        }

#line 2208
        (&kernelContext_5)->_stgBase_0 = 0U;
        uint _S47 = 6U * i_7;

#line 2209
        uint d_3 = (&kernelContext_5)->entryPointParams_items_0[_S47];

#line 2209
        uint t_7 = (&kernelContext_5)->entryPointParams_items_0[_S47 + 1U];
        (&kernelContext_5)->_binPhase_0 = (&kernelContext_5)->entryPointParams_items_0[_S47 + 5U];

#line 2210
        filterPairOut_0(d_3 * (&kernelContext_5)->entryPointParams_0->ntmpl_0 + t_7, (&kernelContext_5)->entryPointParams_items_0[_S47 + 4U], lid_0.x, (&kernelContext_5)->entryPointParams_data_0, (&kernelContext_5)->entryPointParams_tmpl_0, (&kernelContext_5)->entryPointParams_peakIdx_0, (&kernelContext_5)->entryPointParams_peakVal_0, (&kernelContext_5)->entryPointParams_0->ntmpl_0, (&kernelContext_5)->entryPointParams_items_0[_S47 + 2U], (&kernelContext_5)->entryPointParams_items_0[_S47 + 3U], (&kernelContext_5)->entryPointParams_0->binsize_0, (&kernelContext_5)->entryPointParams_0->binShift_0, (&kernelContext_5)->entryPointParams_0->nbins_0, (&kernelContext_5)->entryPointParams_0->thrBits_0, &kernelContext_5);



        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 2207
        i_7 = i_7 + (&kernelContext_5)->entryPointParams_0->gridSize_0;

#line 2207
    }

#line 2216
    return;
}
