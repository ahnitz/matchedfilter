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


#line 222 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/python/matchedfilter/metal/tc_corr1_2097152.slang"
float2 cmulConj_0(float2 a_0, float2 b_0)
{

#line 222
    float _S2 = a_0.x;

#line 222
    float _S3 = b_0.x;

#line 222
    float _S4 = a_0.y;

#line 222
    float _S5 = b_0.y;

#line 222
    return float2(_S2 * _S3 + _S4 * _S5, _S4 * _S3 - _S2 * _S5);
}


#line 389
void r4_0(float2 thread* a_1, float2 thread* b_1, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 391
    float2 t1_0 = *a_1 - *c_0;

#line 391
    float2 t2_0 = *b_1 + *d_0;

#line 391
    float2 t3_0 = *b_1 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 393
    *b_1 = t1_0 + j3_0;

#line 393
    *c_0 = t0_0 - t2_0;

#line 393
    *d_0 = t1_0 - j3_0;
    return;
}


#line 221
float2 cmul_0(float2 a_2, float2 b_2)
{

#line 221
    float _S6 = a_2.x;

#line 221
    float _S7 = b_2.x;

#line 221
    float _S8 = a_2.y;

#line 221
    float _S9 = b_2.y;

#line 221
    return float2(_S6 * _S7 - _S8 * _S9, _S6 * _S9 + _S8 * _S7);
}


#line 425
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639, 0.38268342614173889);
    float2 W2_0 = float2(0.70710676908493042, 0.70710676908493042);
    float2 W3_0 = float2(0.38268342614173889, 0.92387950420379639);
    float2 W4_0 = float2(0.0, 1.0);
    float2 W6_0 = float2(-0.70710676908493042, 0.70710676908493042);
    float2 W9_0 = float2(-0.92387950420379639, -0.38268342614173889);

#line 432
    uint n1_0 = 0U;
    for(;;)
    {

#line 433
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 433
            break;
        }

#line 433
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 433
        n1_0 = n1_0 + 1U;

#line 433
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 434
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 434
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 435
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 435
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 436
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 436
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 436
    uint k2_0 = 0U;
    for(;;)
    {

#line 437
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 437
            break;
        }

#line 437
        uint _S10 = 4U * k2_0;

#line 437
        r4_0(&(*r_0)[_S10], &(*r_0)[_S10 + 1U], &(*r_0)[_S10 + 2U], &(*r_0)[_S10 + 3U]);

#line 437
        k2_0 = k2_0 + 1U;

#line 437
    }

    float2 t_0 = (*r_0)[int(1)];

#line 439
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 439
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 440
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 440
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 441
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 441
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 442
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 442
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 443
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 443
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 444
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 444
    (*r_0)[int(14)] = t_5;
    return;
}


#line 17 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 223 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/python/matchedfilter/metal/tc_corr1_2097152.slang"
uint computeWant_0(uint d_1, uint TB_0, uint len_0, uint blk_0, uint lane_0, uint per_0, uint TB2_0, uint len2_0, uint blk2_0, uint lane2_0)
{
    uint _S11 = max(TB_0, 1U);

#line 225
    uint j_0 = d_1 / _S11;

#line 225
    uint m_0 = d_1 % _S11;

#line 225
    uint _S12;
    if(TB_0 <= 16U)
    {

#line 226
        _S12 = blk_0 * len_0 + (lane_0 * per_0 + j_0) * TB_0 + m_0;

#line 226
    }
    else
    {

#line 226
        _S12 = blk2_0 * len2_0 + lane2_0 + TB2_0 * d_1;

#line 226
    }

#line 226
    return _S12;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint ntmpl_0;
};


#line 210 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/python/matchedfilter/metal/tc_corr1_2097152.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    packed_float2 device* entryPointParams_scratch_0;
    uint _tid_0;
    uint _stgBase_0;
    array<uint, int(2048)> threadgroup* stg_0;
};


#line 210
void stgPut_0(uint i_0, float2 v_0, KernelContext_0 thread* kernelContext_0)
{

#line 210
    uint _S13 = 2U * i_0;

#line 210
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13] = (as_type<uint>((v_0.x)));

#line 210
    (*kernelContext_0->stg_0)[kernelContext_0->_stgBase_0 + _S13 + 1U] = (as_type<uint>((v_0.y)));

#line 210
    return;
}


#line 211
float2 stgGet_0(uint i_1, KernelContext_0 thread* kernelContext_1)
{

#line 211
    uint _S14 = 2U * i_1;

#line 211
    return float2((as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14]))), (as_type<float>(((*kernelContext_1->stg_0)[kernelContext_1->_stgBase_0 + _S14 + 1U]))));
}


#line 585
void exchange_0(array<float2, int(16)> thread* r_1, uint lgLen_0, uint lgSpan_0, uint TB_1, uint len_1, uint blk_1, uint lane_1, uint per_1, uint TB2_1, uint len2_1, uint blk2_1, uint lane2_1, KernelContext_0 thread* kernelContext_2)
{

#line 586
    uint j_1;

#line 597
    thread array<float2, int(16)> out_0;

#line 597
    uint z_0 = 0U;
    for(;;)
    {

#line 598
        if(z_0 < 16U)
        {
        }
        else
        {

#line 598
            break;
        }

#line 598
        out_0[z_0] = float2(0.0, 0.0);

#line 598
        z_0 = z_0 + 1U;

#line 598
    }
    uint spanMask_0 = (1U << lgSpan_0) - 1U;
    uint lenMask_0 = (1U << lgLen_0) - 1U;


    uint p0_0 = computeWant_0(0U, TB_1, len_1, blk_1, lane_1, per_1, TB2_1, len2_1, blk2_1, lane2_1);
    uint _S15 = p0_0 & lenMask_0;

#line 604
    uint _S16 = _S15 >> lgSpan_0;

#line 604
    uint _S17 = _S16 * 128U + ((p0_0 >> lgLen_0) << lgSpan_0) + (_S15 & spanMask_0);

#line 604
    uint c_1 = 0U;

    for(;;)
    {

#line 606
        if(c_1 < 2U)
        {
        }
        else
        {

#line 606
            break;
        }

#line 607
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 607
        j_1 = 0U;
        for(;;)
        {

#line 608
            if(j_1 < 8U)
            {
            }
            else
            {

#line 608
                break;
            }

#line 608
            stgPut_0(j_1 * 128U + kernelContext_2->_tid_0, (*r_1)[c_1 * 8U + j_1], kernelContext_2);

#line 608
            j_1 = j_1 + 1U;

#line 608
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 609
        uint d_2 = 0U;
        for(;;)
        {

#line 610
            if(d_2 < 16U)
            {
            }
            else
            {

#line 610
                break;
            }

#line 611
            uint pz_0 = computeWant_0(d_2, TB_1, len_1, 0U, 0U, per_1, TB2_1, len2_1, 0U, 0U);
            uint _S18 = pz_0 & lenMask_0;

#line 612
            uint iz_0 = _S18 >> lgSpan_0;
            uint az_0 = iz_0 * 128U + ((pz_0 >> lgLen_0) << lgSpan_0) + (_S18 & spanMask_0);
            uint i_2 = _S16 + iz_0;
            uint _S19 = c_1 * 8U;

#line 615
            bool _S20;

#line 615
            if(i_2 >= _S19)
            {

#line 615
                _S20 = i_2 < ((c_1 + 1U) * 8U);

#line 615
            }
            else
            {

#line 615
                _S20 = false;

#line 615
            }

#line 615
            if(_S20)
            {

#line 615
                float2 _S21 = stgGet_0(_S17 + az_0 - _S19 * 128U, kernelContext_2);
                out_0[d_2] = _S21;

#line 615
            }

#line 610
            d_2 = d_2 + 1U;

#line 610
        }

#line 606
        c_1 = c_1 + 1U;

#line 606
    }

#line 606
    j_1 = 0U;

#line 619
    for(;;)
    {

#line 619
        if(j_1 < 16U)
        {
        }
        else
        {

#line 619
            break;
        }

#line 619
        (*r_1)[j_1] = out_0[j_1];

#line 619
        j_1 = j_1 + 1U;

#line 619
    }
    return;
}


#line 409
void dft8_0(array<float2, int(16)> thread* r_2, uint o_0)
{


    thread array<float2, int(8)> b_3;

#line 413
    uint s_0 = 1U;
    for(;;)
    {

#line 414
        if(s_0 < 8U)
        {
        }
        else
        {

#line 414
            break;
        }

#line 414
        uint j_2 = 0U;
        for(;;)
        {

#line 415
            if(j_2 < 4U)
            {
            }
            else
            {

#line 415
                break;
            }

#line 416
            uint k_0 = j_2 & (s_0 - 1U);


            uint _S22 = o_0 + j_2;

#line 419
            float2 t_6 = cmul_0(mfTwiddle_0(3.14159274101257324 * float(k_0) / float(s_0)), (*r_2)[_S22 + 4U]);
            uint _S23 = ((j_2 - k_0) << 1U) + k_0;

#line 420
            b_3[_S23] = (*r_2)[_S22] + t_6;

#line 420
            b_3[_S23 + s_0] = (*r_2)[_S22] - t_6;

#line 415
            j_2 = j_2 + 1U;

#line 415
        }

#line 415
        uint i_3 = 0U;

#line 422
        for(;;)
        {

#line 422
            if(i_3 < 8U)
            {
            }
            else
            {

#line 422
                break;
            }

#line 422
            (*r_2)[o_0 + i_3] = b_3[i_3];

#line 422
            i_3 = i_3 + 1U;

#line 422
        }

#line 414
        s_0 = s_0 << 1U;

#line 414
    }

#line 424
    return;
}


#line 528
void innermost_0(array<float2, int(16)> thread* r_3)
{

#line 528
    uint b_4 = 0U;

#line 536
    for(;;)
    {

#line 536
        if(b_4 < 2U)
        {
        }
        else
        {

#line 536
            break;
        }

#line 536
        dft8_0(r_3, b_4 * 8U);

#line 536
        b_4 = b_4 + 1U;

#line 536
    }



    return;
}


#line 675
void transform_0(array<float2, int(16)> thread* r_4, uint tid_0, KernelContext_0 thread* kernelContext_3)
{

#line 675
    uint _S24;

#line 675
    uint k2_1;

#line 675
    float cr_0;

#line 675
    float ci_0;

#line 675
    uint _S25;

#line 675
    for(;;)
    {

#line 675
        for(;;)
        {

#line 7 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/src/gpu/fft_transform.slang"
            for(;;)
            {


                uint lgTB_0 = firstbithigh_0(128U);

#line 11
                _S24 = lgTB_0;
                uint lgLn_0 = firstbithigh_0(2048U);
                uint blk_2 = tid_0 >> lgTB_0;
                uint lane_2 = tid_0 & 127U;


                dft16_0(r_4);

#line 26
                float2 tw_0 = mfTwiddle_0(6.28318548202514648 * float(lane_2) / 2048.0);
                float _S26 = tw_0.x;

#line 27
                float _S27 = tw_0.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_0 = cr_0 * _S26 - ci_0 * _S27;
                    float _S28 = cr_0 * _S27 + ci_0 * _S26;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_0;

#line 29
                    ci_0 = _S28;

#line 29
                }

#line 37
                uint per_2 = 16U / max(128U, 1U);
                uint _S29 = max(8U, 1U);

#line 38
                _S25 = _S29;
                uint blk2_2 = tid_0 / _S29;

#line 39
                uint lane2_2 = tid_0 % _S29;

#line 39
                exchange_0(r_4, lgLn_0, lgTB_0, 128U, 2048U, blk_2, lane_2, per_2, _S29, 128U, blk2_2, lane2_2, kernelContext_3);

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


                uint lgTB_1 = firstbithigh_0(8U);

                uint blk_3 = tid_0 >> lgTB_1;
                uint lane_3 = tid_0 & 7U;


                dft16_0(r_4);

#line 26
                float2 tw_1 = mfTwiddle_0(6.28318548202514648 * float(lane_3) / 128.0);
                float _S30 = tw_1.x;

#line 27
                float _S31 = tw_1.y;

#line 27
                k2_1 = 0U;

#line 27
                cr_0 = 1.0;

#line 27
                ci_0 = 0.0;

                for(;;)
                {

#line 29
                    if(k2_1 < 16U)
                    {
                    }
                    else
                    {

#line 29
                        break;
                    }

#line 30
                    (*r_4)[k2_1] = cmul_0((*r_4)[k2_1], float2(cr_0, ci_0));
                    float nr_1 = cr_0 * _S30 - ci_0 * _S31;
                    float _S32 = cr_0 * _S31 + ci_0 * _S30;

#line 29
                    k2_1 = k2_1 + 1U;

#line 29
                    cr_0 = nr_1;

#line 29
                    ci_0 = _S32;

#line 29
                }

#line 37
                uint per_3 = 16U / _S25;
                uint _S33 = max(0U, 1U);
                uint blk2_3 = tid_0 / _S33;

#line 39
                uint lane2_3 = tid_0 % _S33;

#line 39
                exchange_0(r_4, _S24, lgTB_1, 8U, 128U, blk_3, lane_3, per_3, _S33, 8U, blk2_3, lane2_3, kernelContext_3);

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

#line 678 "/home/ahnitz/projects/claude/searchdev/work/peak-fft/.claude/worktrees/agent-aaf230abdd173dffa/python/matchedfilter/metal/tc_corr1_2097152.slang"
    return;
}


#line 644
uint lgOf_0(uint i_4)
{

#line 644
    uint _S34;

#line 644
    if(i_4 < 2U)
    {

#line 644
        _S34 = 4U;

#line 644
    }
    else
    {

#line 644
        if(i_4 == 2U)
        {

#line 644
            _S34 = 3U;

#line 644
        }
        else
        {

#line 644
            _S34 = 1U;

#line 644
        }

#line 644
    }

#line 644
    return _S34;
}


#line 646
uint slotToIndex_0(uint slot_0)
{


    uint lg_0 = lgOf_0(2U);

    uint x_0 = slot_0 >> lg_0;

#line 650
    uint lg_1 = lgOf_0(1U);

#line 650
    uint lg_2 = lgOf_0(0U);

#line 655
    return (((((0U << lg_0) | (slot_0 & ((1U << lg_0) - 1U))) << lg_1) | (x_0 & ((1U << lg_1) - 1U))) << lg_2) | ((x_0 >> lg_1) & ((1U << lg_2) - 1U));
}


#line 1428
[[kernel]] void tcStage1(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], packed_float2 device* entryPointParams_scratch_1 [[buffer(3)]])
{

#line 1428
    thread KernelContext_0 kernelContext_4;

#line 1428
    (&kernelContext_4)->entryPointParams_0 = entryPointParams_1;

#line 1428
    (&kernelContext_4)->entryPointParams_data_0 = entryPointParams_data_1;

#line 1428
    (&kernelContext_4)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 1428
    (&kernelContext_4)->entryPointParams_scratch_0 = entryPointParams_scratch_1;

#line 1428
    threadgroup array<uint, int(2048)> stg_1;

#line 1428
    (&kernelContext_4)->stg_0 = &stg_1;



    uint _S35 = gid_0.x;

#line 1432
    uint pair_0 = _S35 / 1024U;

#line 1432
    uint _S36 = _S35 % 1024U;
    uint _S37 = pair_0 / entryPointParams_1->ntmpl_0;

#line 1433
    uint _S38 = pair_0 % entryPointParams_1->ntmpl_0;
    uint tid_1 = lid_0.x;
    (&kernelContext_4)->_tid_0 = tid_1;
    (&kernelContext_4)->_stgBase_0 = 0U;

    thread array<float2, int(16)> r_5;

#line 1438
    uint m_1 = 0U;
    for(;;)
    {

#line 1439
        if(m_1 < 16U)
        {
        }
        else
        {

#line 1439
            break;
        }

#line 1440
        uint j_3 = _S36 + 1024U * (tid_1 + 128U * m_1);
        r_5[m_1] = cmulConj_0(float2(*((&kernelContext_4)->entryPointParams_data_0+(_S37 * 2097152U + j_3))) , float2(*((&kernelContext_4)->entryPointParams_tmpl_0+(_S38 * 2097152U + j_3))) );

#line 1439
        m_1 = m_1 + 1U;

#line 1439
    }

#line 1439
    transform_0(&r_5, tid_1, &kernelContext_4);

#line 1439
    uint i_5 = 0U;

#line 1448
    for(;;)
    {

#line 1448
        if(i_5 < 16U)
        {
        }
        else
        {

#line 1448
            break;
        }

#line 1449
        uint k2_2 = slotToIndex_0(tid_1 * 16U + i_5);

#line 1449
        *((&kernelContext_4)->entryPointParams_scratch_0+(pair_0 * 2097152U + k2_2 * 1024U + _S36)) = packed_float2(cmul_0(r_5[i_5], mfTwiddle_0(6.28318548202514648 * float(_S36 * k2_2) / 2.097152e+06))) ;

#line 1448
        i_5 = i_5 + 1U;

#line 1448
    }

#line 1453
    return;
}
