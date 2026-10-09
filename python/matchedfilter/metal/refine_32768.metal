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


#line 152 "mm_32768_refineListed.slang"
float2 cload_0(packed_float2 device* b_0, uint i_0)
{

#line 152
    return float2(*(b_0+i_0)) ;
}


#line 213
float2 cmulConj_0(float2 a_0, float2 b_1)
{

#line 213
    float _S2 = a_0.x;

#line 213
    float _S3 = b_1.x;

#line 213
    float _S4 = a_0.y;

#line 213
    float _S5 = b_1.y;

#line 213
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 12 "twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 212 "mm_32768_refineListed.slang"
float2 cmul_0(float2 a_1, float2 b_2)
{

#line 212
    float _S6 = a_1.x;

#line 212
    float _S7 = b_2.x;

#line 212
    float _S8 = a_1.y;

#line 212
    float _S9 = b_2.y;

#line 212
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 380
void r4_0(float2 thread* a_2, float2 thread* b_3, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_2 + *c_0;

#line 382
    float2 t1_0 = *a_2 - *c_0;

#line 382
    float2 t2_0 = *b_3 + *d_0;

#line 382
    float2 t3_0 = *b_3 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_2 = t0_0 + t2_0;

#line 384
    *b_3 = t1_0 + j3_0;

#line 384
    *c_0 = t0_0 - t2_0;

#line 384
    *d_0 = t1_0 - j3_0;
    return;
}


#line 416
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 423
    uint n1_0 = 0U;
    for(;;)
    {

#line 424
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 424
            break;
        }

#line 424
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 424
        n1_0 = n1_0 + 1U;

#line 424
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 425
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 425
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 426
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 426
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 427
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 427
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 427
    uint k2_0 = 0U;
    for(;;)
    {

#line 428
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 428
            break;
        }

#line 428
        uint _S10 = 4U * k2_0;

#line 428
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 428
        k2_0 = k2_0 + 1U;

#line 428
    }

    float2 t_0 = (*r_0)[int(1)];

#line 430
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 430
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 431
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 431
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 432
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 432
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 433
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 433
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 434
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 434
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 435
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 435
    (*r_0)[int(14)] = t_5;
    return;
}


#line 462
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> u_0;

#line 464
    thread array<float2, int(16)> v_0;

#line 464
    uint j_0 = 0U;
    for(;;)
    {

#line 465
        if(j_0 < 16U)
        {
        }
        else
        {

#line 465
            break;
        }
        u_0[j_0] = (*r_1)[j_0] + (*r_1)[j_0 + 16U];

        v_0[j_0] = cmul_0((*r_1)[j_0] - (*r_1)[j_0 + 16U], mfTwiddle_0(6.28318548202514648 * float(j_0) / 32.0));

#line 465
        j_0 = j_0 + 1U;

#line 465
    }

#line 471
    dft16_0(&u_0);
    dft16_0(&v_0);

#line 472
    uint k_0 = 0U;
    for(;;)
    {

#line 473
        if(k_0 < 16U)
        {
        }
        else
        {

#line 473
            break;
        }

#line 473
        uint _S11 = 2U * k_0;

#line 473
        (*r_1)[_S11] = u_0[k_0];

#line 473
        (*r_1)[_S11 + 1U] = v_0[k_0];

#line 473
        k_0 = k_0 + 1U;

#line 473
    }
    return;
}


#line 501
void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);



    return;
}


#line 214
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S12 = max(TB_0, 1U);

#line 216
    uint j_1 = d_1 / _S12;

#line 216
    uint m_0 = d_1 % _S12;

#line 216
    uint _S13;
    if(TB_0 <= 32U)
    {

#line 217
        _S13 = blk_0 * len_0 + (lane_0 * per_0 + j_1) * TB_0 + m_0;

#line 217
    }
    else
    {

#line 217
        _S13 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 217
    }

#line 217
    return _S13;
}


#line 8402 "hlsl.meta.slang"
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


#line 201 "mm_32768_refineListed.slang"
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


#line 201
void stgPut_0(uint i_1, float2 v_1, KernelContext_0 thread* kernelContext_0)
{

#line 201
    uint _S14 = 2U * i_1;

#line 201
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14] = (as_type<uint>((v_1.x)));

#line 201
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S14 + 1U] = (as_type<uint>((v_1.y)));

#line 201
    return;
}


#line 202
float2 stgGet_0(uint i_2, KernelContext_0 thread* kernelContext_1)
{

#line 202
    uint _S15 = 2U * i_2;

#line 202
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S15 + 1U]))));
}


#line 576
void exchange_0(array<float2, int(32)> thread* r_3, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 577
    uint j_2;

#line 588
    thread array<float2, int(32)> out_0;

#line 588
    uint z_0 = 0U;
    for(;;)
    {

#line 589
        if(z_0 < 32U)
        {
        }
        else
        {

#line 589
            break;
        }

#line 589
        out_0[z_0] = float2(0.0, 0.0);

#line 589
        z_0 = z_0 + 1U;

#line 589
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S16 = p0_0 & lenMask_0;

#line 595
    uint _S17 = _S16 >> lgSpan_0;

#line 595
    uint _S18 = _S17 * 1024U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S16 & spanMask_0);

#line 595
    uint c_1 = 0U;

    for(;;)
    {

#line 597
        if(c_1 < 4U)
        {
        }
        else
        {

#line 597
            break;
        }

#line 598
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 598
        j_2 = 0U;
        for(;;)
        {

#line 599
            if(j_2 < 8U)
            {
            }
            else
            {

#line 599
                break;
            }

#line 599
            stgPut_0(j_2 * 1024U + kernelContext_2->_tid_0, (*r_3)[c_1 * 8U + j_2], kernelContext_2);

#line 599
            j_2 = j_2 + 1U;

#line 599
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 600
        uint d_2 = 0U;
        for(;;)
        {

#line 601
            if(d_2 < 32U)
            {
            }
            else
            {

#line 601
                break;
            }

#line 602
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S19 = pz_0 & lenMask_0;

#line 603
            uint iz_0 = _S19 >> lgSpan_0;
            uint az_0 = iz_0 * 1024U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S19 & spanMask_0);
            uint i_3 = _S17 + iz_0;
            uint _S20 = c_1 * 8U;

#line 606
            bool _S21;

#line 606
            if(i_3 >= _S20)
            {

#line 606
                _S21 = i_3 < ((c_1 + 1U) * 8U);

#line 606
            }
            else
            {

#line 606
                _S21 = false;

#line 606
            }

#line 606
            if(_S21)
            {

#line 606
                float2 _S22 = stgGet_0(_S18 + az_0 - _S20 * 1024U, kernelContext_2);
                out_0[d_2] = _S22;

#line 606
            }

#line 601
            d_2 = d_2 + 1U;

#line 601
        }

#line 597
        c_1 = c_1 + 1U;

#line 597
    }

#line 597
    j_2 = 0U;

#line 610
    for(;;)
    {

#line 610
        if(j_2 < 32U)
        {
        }
        else
        {

#line 610
            break;
        }

#line 610
        (*r_3)[j_2] = out_0[j_2];

#line 610
        j_2 = j_2 + 1U;

#line 610
    }
    return;
}


#line 519
void innermost_0(array<float2, int(32)> thread* r_4)
{

    dft32_0(r_4);

#line 531
    return;
}


#line 666
void transform_0(array<float2, int(32)> thread* r_5, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 666
    uint _S23;

#line 666
    uint k2_1;

#line 666
    float cr_0;

#line 666
    float ci_0;

#line 666
    uint _S24;

#line 666
    for(;;)
    {

#line 666
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

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 32768.0);
                float _S25 = tw_0.x;

#line 27
                float _S26 = tw_0.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_1 < 32U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_5)[k2_1] = cmul_0((*r_5)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S25 - ci_0 * _S26;
                    float _S27 = cr_0 * _S26 + ci_0 * _S25;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S27;

#line 29
                }

#line 37
                uint per_2 = 32U / max(1024U, 1U);
                uint _S28 = max(32U, 1U);

#line 38
                _S24 = _S28;
                uint blk2_2 = tid_0 / _S28;

#line 39
                uint lane2_2 = tid_0 % _S28;

#line 39
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

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 1024.0);
                float _S29 = tw_1.x;

#line 27
                float _S30 = tw_1.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_1 < 32U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_5)[k2_1] = cmul_0((*r_5)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S29 - ci_0 * _S30;
                    float _S31 = cr_0 * _S30 + ci_0 * _S29;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S31;

#line 29
                }

#line 37
                uint per_3 = 32U / _S24;
                uint _S32 = max(1U, 1U);
                uint blk2_3 = tid_0 / _S32;

#line 39
                uint lane2_3 = tid_0 % _S32;

#line 39
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

#line 43
    innermost_0(r_5);

#line 669 "mm_32768_refineListed.slang"
    return;
}


#line 635
uint lgOf_0(uint i_4)
{

#line 635
    uint _S33;

#line 635
    if(i_4 < 2U)
    {

#line 635
        _S33 = 5U;

#line 635
    }
    else
    {

#line 635
        if(i_4 == 2U)
        {

#line 635
            _S33 = 5U;

#line 635
        }
        else
        {

#line 635
            _S33 = 1U;

#line 635
        }

#line 635
    }

#line 635
    return _S33;
}


#line 637
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 641
    uint lg_1 = lgOf_0(1U);

#line 641
    uint lg_2 = lgOf_0(0U);

#line 646
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 681
void filterPair_0(uint pair_0, uint tid_1, packed_float2 device* data_0, packed_float2 device* tmpl_0, int device* peakIdx_0, packed_float2 device* peakVal_0, uint ntmpl_1, uint winStart_1, uint winEnd_1, uint binsize_1, int binShift_1, uint nbins_1, uint thrBits_1, KernelContext_0 thread* kernelContext_4)
{

#line 695
    kernelContext_4->_tid_0 = tid_1;
    uint _S34 = pair_0 / ntmpl_1;

#line 696
    uint _S35 = pair_0 % ntmpl_1;

    thread array<float2, int(32)> r_6;

#line 698
    uint n2_0 = 0U;

#line 709
    for(;;)
    {

#line 709
        if(n2_0 < 32U)
        {
        }
        else
        {

#line 709
            break;
        }

#line 710
        uint idx_0 = tid_1 + 1024U * n2_0;
        r_6[n2_0] = cmulConj_0(cload_0(data_0, _S34 * 32768U + idx_0), cload_0(tmpl_0, _S35 * 32768U + idx_0));

#line 709
        n2_0 = n2_0 + 1U;

#line 709
    }

#line 709
    transform_0(&r_6, tid_1, kernelContext_4);

#line 728
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 728
    uint b_4 = tid_1;

#line 802
    for(;;)
    {

#line 802
        if(b_4 < nbins_1)
        {
        }
        else
        {

#line 802
            break;
        }

#line 802
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4] = thrBits_1;

#line 802
        b_4 = b_4 + 1024U;

#line 802
    }
    bool _S36 = nbins_1 == 1U;

#line 803
    bool live_0;

#line 803
    if(_S36)
    {

#line 803
        live_0 = tid_1 == 0U;

#line 803
    }
    else
    {

#line 803
        live_0 = false;

#line 803
    }

#line 803
    if(live_0)
    {

#line 803
        (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U] = 4294967295U;

#line 803
    }

    threadgroup_barrier(mem_flags::mem_threadgroup);

    thread array<uint, int(32)> myMag_0;
    thread array<uint, int(32)> myBin_0;

#line 808
    uint i_5 = 0U;
    for(;;)
    {

#line 809
        if(i_5 < 32U)
        {
        }
        else
        {

#line 809
            break;
        }

#line 810
        uint idx_1 = slotToIndex_0(tid_1 * 32U + i_5);
        if(idx_1 >= winStart_1)
        {

#line 811
            live_0 = idx_1 < winEnd_1;

#line 811
        }
        else
        {

#line 811
            live_0 = false;

#line 811
        }



        float _rx_0 = r_6[i_5].x;

#line 815
        float _ry_0 = r_6[i_5].y;
        if(live_0)
        {

#line 816
            n2_0 = (as_type<uint>((_rx_0 * _rx_0 + _ry_0 * _ry_0)));

#line 816
        }
        else
        {

#line 816
            n2_0 = 0U;

#line 816
        }

#line 816
        myMag_0[i_5] = n2_0;
        uint off_0 = idx_1 - winStart_1;

#line 824
        if(live_0)
        {

#line 824
            if(binShift_1 >= int(0))
            {

#line 824
                b_4 = off_0 >> uint(binShift_1);

#line 824
            }
            else
            {

#line 824
                uint _S37 = off_0 / binsize_1;

#line 824
                b_4 = _S37;

#line 824
            }

#line 824
        }
        else
        {

#line 824
            b_4 = 0U;

#line 824
        }

#line 824
        myBin_0[i_5] = b_4;

#line 824
        bool _S38;



        if(nbins_1 > 1U)
        {

#line 828
            _S38 = (myMag_0[i_5]) > thrBits_1;

#line 828
        }
        else
        {

#line 828
            _S38 = false;

#line 828
        }

#line 828
        if(_S38)
        {

#line 829
            uint _S39 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), myMag_0[i_5], memory_order_relaxed);

#line 828
        }

#line 809
        i_5 = i_5 + 1U;

#line 809
    }

#line 809
    uint winner_0;

#line 841
    if(_S36)
    {

#line 841
        winner_0 = thrBits_1;

#line 841
        i_5 = 0U;


        for(;;)
        {

#line 844
            if(i_5 < 32U)
            {
            }
            else
            {

#line 844
                break;
            }

#line 844
            uint _S40 = max(winner_0, myMag_0[i_5]);

#line 844
            uint i_6 = i_5 + 1U;

#line 844
            winner_0 = _S40;

#line 844
            i_5 = i_6;

#line 844
        }

        uint wm_0 = simd_max(winner_0);
        bool _S41 = simd_is_first();

#line 847
        if(_S41)
        {

#line 847
            live_0 = wm_0 > thrBits_1;

#line 847
        }
        else
        {

#line 847
            live_0 = false;

#line 847
        }

#line 847
        if(live_0)
        {

#line 847
            uint _S42 = atomic_fetch_max_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0])), wm_0, memory_order_relaxed);

#line 847
        }

#line 841
    }

#line 862
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 869
    if(_S36)
    {

#line 869
        winner_0 = 4294967295U;

#line 869
        i_5 = 0U;


        for(;;)
        {

#line 872
            if(i_5 < 32U)
            {
            }
            else
            {

#line 872
                break;
            }

#line 873
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 873
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0];

#line 873
            }
            else
            {

#line 873
                live_0 = false;

#line 873
            }

#line 873
            if(live_0)
            {

#line 873
                winner_0 = min(winner_0, tid_1 * 32U + i_5);

#line 873
            }

#line 872
            i_5 = i_5 + 1U;

#line 872
        }



        uint waveWinner_0 = simd_min(winner_0);
        bool _S43 = simd_is_first();

#line 877
        if(_S43)
        {

#line 877
            live_0 = waveWinner_0 != 4294967295U;

#line 877
        }
        else
        {

#line 877
            live_0 = false;

#line 877
        }

#line 877
        if(live_0)
        {

#line 878
            uint _S44 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])), waveWinner_0, memory_order_relaxed);

#line 877
        }

#line 882
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 882
        i_5 = 0U;
        for(;;)
        {

#line 883
            if(i_5 < 32U)
            {
            }
            else
            {

#line 883
                break;
            }

#line 884
            uint _S45 = tid_1 * 32U + i_5;

#line 884
            if(_S45 == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U])
            {

#line 885
                *(peakIdx_0+pair_0) = int(slotToIndex_0(_S45));

#line 885
                *(peakVal_0+pair_0) = packed_float2(float2(r_6[i_5].x, r_6[i_5].y)) ;

#line 884
            }

#line 883
            i_5 = i_5 + 1U;

#line 883
        }

#line 889
        if(tid_1 == 0U)
        {

#line 889
            live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + 1U]) == 4294967295U;

#line 889
        }
        else
        {

#line 889
            live_0 = false;

#line 889
        }

#line 889
        if(live_0)
        {

#line 890
            *(peakIdx_0+pair_0) = int(-1);

#line 890
            *(peakVal_0+pair_0) = packed_float2(float2(0.0, 0.0)) ;

#line 889
        }

#line 869
    }
    else
    {

#line 869
        i_5 = 0U;

#line 898
        for(;;)
        {

#line 898
            if(i_5 < 32U)
            {
            }
            else
            {

#line 898
                break;
            }

#line 899
            if((myMag_0[i_5]) > thrBits_1)
            {

#line 899
                live_0 = (myMag_0[i_5]) == (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]];

#line 899
            }
            else
            {

#line 899
                live_0 = false;

#line 899
            }

#line 899
            myMag_0[i_5] = uint(live_0);

#line 898
            i_5 = i_5 + 1U;

#line 898
        }


        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 901
        b_4 = tid_1;
        for(;;)
        {

#line 902
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 902
                break;
            }

#line 902
            (*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4] = 4294967295U;

#line 902
            b_4 = b_4 + 1024U;

#line 902
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 903
        i_5 = 0U;
        for(;;)
        {

#line 904
            if(i_5 < 32U)
            {
            }
            else
            {

#line 904
                break;
            }

#line 905
            if((myMag_0[i_5]) != 0U)
            {

#line 905
                uint _S46 = atomic_fetch_min_explicit(((atomic_uint threadgroup*)(&(*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]])), tid_1 * 32U + i_5, memory_order_relaxed);

#line 905
            }

#line 904
            i_5 = i_5 + 1U;

#line 904
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 906
        i_5 = 0U;
        for(;;)
        {

#line 907
            if(i_5 < 32U)
            {
            }
            else
            {

#line 907
                break;
            }

#line 908
            if((myMag_0[i_5]) != 0U)
            {

#line 908
                live_0 = ((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + myBin_0[i_5]]) == (tid_1 * 32U + i_5);

#line 908
            }
            else
            {

#line 908
                live_0 = false;

#line 908
            }

#line 908
            if(live_0)
            {

#line 909
                uint o_0 = pair_0 * nbins_1 + myBin_0[i_5];
                *(peakIdx_0+o_0) = int(slotToIndex_0(tid_1 * 32U + i_5));

#line 910
                *(peakVal_0+o_0) = packed_float2(float2(r_6[i_5].x, r_6[i_5].y)) ;

#line 908
            }

#line 907
            i_5 = i_5 + 1U;

#line 907
        }

#line 907
        b_4 = tid_1;

#line 914
        for(;;)
        {

#line 914
            if(b_4 < nbins_1)
            {
            }
            else
            {

#line 914
                break;
            }

#line 915
            if(((*kernelContext_4->stg_0)[kernelContext_4->_stgBase_0 + b_4]) == 4294967295U)
            {

#line 916
                uint _S47 = pair_0 * nbins_1 + b_4;

#line 916
                *(peakIdx_0+_S47) = int(-1);

#line 916
                *(peakVal_0+_S47) = packed_float2(float2(0.0, 0.0)) ;

#line 915
            }

#line 914
            b_4 = b_4 + 1024U;

#line 914
        }

#line 869
    }

#line 923
    return;
}


#line 1371
[[kernel]] void refineListed(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], int device* entryPointParams_peakIdx_1 [[buffer(3)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(4)]], uint device* entryPointParams_survivors_1 [[buffer(5)]])
{

#line 1371
    thread KernelContext_0 kernelContext_5;

#line 1371
    (&kernelContext_5)->entryPointParams_0 = entryPointParams_1;

#line 1371
    (&kernelContext_5)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1371
    (&kernelContext_5)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1371
    (&kernelContext_5)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 1371
    (&kernelContext_5)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 1371
    (&kernelContext_5)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 1371
    threadgroup array<uint, int(16384)> stg_1;

#line 1371
    (&kernelContext_5)->stg_0 = &stg_1;

#line 1380
    uint pair_1 = entryPointParams_survivors_1[gid_0.x];

#line 1386
    (&kernelContext_5)->_stgBase_0 = 0U;

#line 1386
    filterPair_0(pair_1, lid_0.x, entryPointParams_data_1, entryPointParams_tmpl_1, entryPointParams_peakIdx_1, entryPointParams_peakVal_1, entryPointParams_1->ntmpl_0, entryPointParams_1->winStart_0, entryPointParams_1->winEnd_0, entryPointParams_1->binsize_0, entryPointParams_1->binShift_0, entryPointParams_1->nbins_0, entryPointParams_1->thrBits_0, &kernelContext_5);


    return;
}
