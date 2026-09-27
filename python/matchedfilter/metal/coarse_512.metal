#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;

#line 70 "/home/ahnitz/projects/claude/searchdev/work/mf-main-merge/python/matchedfilter/spirv/ct_512_m.slang"
float2 cmulConj_0(float2 a_0, float2 b_0)
{

#line 70
    float _S1 = a_0.x;

#line 70
    float _S2 = b_0.x;

#line 70
    float _S3 = a_0.y;

#line 70
    float _S4 = b_0.y;

#line 70
    return float2(_S1 * _S2 + _S3 * _S4, _S3 * _S2 - _S1 * _S4);
}


#line 72
void r4_0(float2 thread* a_1, float2 thread* b_1, float2 thread* c_0, float2 thread* d_0)
{
    float2 t0_0 = *a_1 + *c_0;

#line 74
    float2 t1_0 = *a_1 - *c_0;

#line 74
    float2 t2_0 = *b_1 + *d_0;

#line 74
    float2 t3_0 = *b_1 - *d_0;
    float2 j3_0 = float2(- t3_0.y, t3_0.x);
    *a_1 = t0_0 + t2_0;

#line 76
    *b_1 = t1_0 + j3_0;

#line 76
    *c_0 = t0_0 - t2_0;

#line 76
    *d_0 = t1_0 - j3_0;
    return;
}


#line 69
float2 cmul_0(float2 a_2, float2 b_2)
{

#line 69
    float _S5 = a_2.x;

#line 69
    float _S6 = b_2.x;

#line 69
    float _S7 = a_2.y;

#line 69
    float _S8 = b_2.y;

#line 69
    return float2(_S5 * _S6 - _S7 * _S8, _S5 * _S8 + _S7 * _S6);
}


#line 78
void dft16_0(array<float2, int(16)> thread* r_0)
{
    float2 W1_0 = float2(0.92387950420379639f, 0.38268342614173889f);
    float2 W2_0 = float2(0.70710676908493042f, 0.70710676908493042f);
    float2 W3_0 = float2(0.38268342614173889f, 0.92387950420379639f);
    float2 W4_0 = float2(0.0f, 1.0f);
    float2 W6_0 = float2(-0.70710676908493042f, 0.70710676908493042f);
    float2 W9_0 = float2(-0.92387950420379639f, -0.38268342614173889f);

#line 85
    uint n1_0 = 0U;
    for(;;)
    {

#line 86
        if(n1_0 < 4U)
        {
        }
        else
        {

#line 86
            break;
        }

#line 86
        r4_0(&(*r_0)[n1_0], &(*r_0)[n1_0 + 4U], &(*r_0)[n1_0 + 8U], &(*r_0)[n1_0 + 12U]);

#line 86
        n1_0 = n1_0 + 1U;

#line 86
    }
    (*r_0)[int(5)] = cmul_0((*r_0)[int(5)], W1_0);

#line 87
    (*r_0)[int(9)] = cmul_0((*r_0)[int(9)], W2_0);

#line 87
    (*r_0)[int(13)] = cmul_0((*r_0)[int(13)], W3_0);
    (*r_0)[int(6)] = cmul_0((*r_0)[int(6)], W2_0);

#line 88
    (*r_0)[int(10)] = cmul_0((*r_0)[int(10)], W4_0);

#line 88
    (*r_0)[int(14)] = cmul_0((*r_0)[int(14)], W6_0);
    (*r_0)[int(7)] = cmul_0((*r_0)[int(7)], W3_0);

#line 89
    (*r_0)[int(11)] = cmul_0((*r_0)[int(11)], W6_0);

#line 89
    (*r_0)[int(15)] = cmul_0((*r_0)[int(15)], W9_0);

#line 89
    uint k2_0 = 0U;
    for(;;)
    {

#line 90
        if(k2_0 < 4U)
        {
        }
        else
        {

#line 90
            break;
        }

#line 90
        uint _S9 = 4U * k2_0;

#line 90
        r4_0(&(*r_0)[_S9], &(*r_0)[_S9 + 1U], &(*r_0)[_S9 + 2U], &(*r_0)[_S9 + 3U]);

#line 90
        k2_0 = k2_0 + 1U;

#line 90
    }

    float2 t_0 = (*r_0)[int(1)];

#line 92
    (*r_0)[int(1)] = (*r_0)[int(4)];

#line 92
    (*r_0)[int(4)] = t_0;
    float2 t_1 = (*r_0)[int(2)];

#line 93
    (*r_0)[int(2)] = (*r_0)[int(8)];

#line 93
    (*r_0)[int(8)] = t_1;
    float2 t_2 = (*r_0)[int(3)];

#line 94
    (*r_0)[int(3)] = (*r_0)[int(12)];

#line 94
    (*r_0)[int(12)] = t_2;
    float2 t_3 = (*r_0)[int(6)];

#line 95
    (*r_0)[int(6)] = (*r_0)[int(9)];

#line 95
    (*r_0)[int(9)] = t_3;
    float2 t_4 = (*r_0)[int(7)];

#line 96
    (*r_0)[int(7)] = (*r_0)[int(13)];

#line 96
    (*r_0)[int(13)] = t_4;
    float2 t_5 = (*r_0)[int(11)];

#line 97
    (*r_0)[int(11)] = (*r_0)[int(14)];

#line 97
    (*r_0)[int(14)] = t_5;
    return;
}


#line 10 "/home/ahnitz/projects/claude/searchdev/work/mf-main-merge/src/gpu/twiddle.slang"
float2 mfTwiddle_0(float angle_0)
{

    return float2(cos(angle_0), sin(angle_0));
}


#line 108 "/home/ahnitz/projects/claude/searchdev/work/mf-main-merge/python/matchedfilter/spirv/ct_512_m.slang"
void dft32_0(array<float2, int(32)> thread* r_1)
{
    thread array<float2, int(16)> e_0;

#line 110
    thread array<float2, int(16)> o_0;

#line 110
    uint i_0 = 0U;
    for(;;)
    {

#line 111
        if(i_0 < 16U)
        {
        }
        else
        {

#line 111
            break;
        }

#line 111
        uint _S10 = 2U * i_0;

#line 111
        e_0[i_0] = (*r_1)[_S10];

#line 111
        o_0[i_0] = (*r_1)[_S10 + 1U];

#line 111
        i_0 = i_0 + 1U;

#line 111
    }
    dft16_0(&e_0);
    dft16_0(&o_0);

#line 113
    uint k_0 = 0U;
    for(;;)
    {

#line 114
        if(k_0 < 16U)
        {
        }
        else
        {

#line 114
            break;
        }
        float2 w_0 = cmul_0(o_0[k_0], mfTwiddle_0(6.28318548202514648f * float(k_0) / 32.0f));
        (*r_1)[k_0] = e_0[k_0] + w_0;
        (*r_1)[k_0 + 16U] = e_0[k_0] - w_0;

#line 114
        k_0 = k_0 + 1U;

#line 114
    }

#line 120
    return;
}

void dftR_0(array<float2, int(32)> thread* r_2)
{



    dft32_0(r_2);

    return;
}


#line 137
void stage2_0(array<float2, int(32)> thread* r_3)
{

#line 143
    thread array<float2, int(16)> a_3;

#line 143
    uint q_0 = 0U;
    for(;;)
    {

#line 144
        if(q_0 < 16U)
        {
        }
        else
        {

#line 144
            break;
        }

#line 144
        a_3[q_0] = (*r_3)[q_0];

#line 144
        q_0 = q_0 + 1U;

#line 144
    }
    dft16_0(&a_3);

#line 145
    q_0 = 0U;
    for(;;)
    {

#line 146
        if(q_0 < 16U)
        {
        }
        else
        {

#line 146
            break;
        }

#line 146
        (*r_3)[q_0] = a_3[q_0];

#line 146
        q_0 = q_0 + 1U;

#line 146
    }

#line 146
    q_0 = 0U;
    for(;;)
    {

#line 147
        if(q_0 < 16U)
        {
        }
        else
        {

#line 147
            break;
        }

#line 147
        a_3[q_0] = (*r_3)[16U + q_0];

#line 147
        q_0 = q_0 + 1U;

#line 147
    }
    dft16_0(&a_3);

#line 148
    q_0 = 0U;
    for(;;)
    {

#line 149
        if(q_0 < 16U)
        {
        }
        else
        {

#line 149
            break;
        }

#line 149
        (*r_3)[16U + q_0] = a_3[q_0];

#line 149
        q_0 = q_0 + 1U;

#line 149
    }

#line 154
    return;
}


#line 90 "core"
struct EntryPointParams_0
{
    uint ntmpl_0;
    uint npairs_0;
};


#line 182 "/home/ahnitz/projects/claude/searchdev/work/mf-main-merge/python/matchedfilter/spirv/ct_512_m.slang"
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_data_0;
    packed_float2 device* entryPointParams_tmpl_0;
    packed_float2 device* entryPointParams_out_0;
    array<float2, int(2048)> threadgroup* sh_0;
};


#line 159
[[kernel]] void coarseTile(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_data_1 [[buffer(1)]], packed_float2 device* entryPointParams_tmpl_1 [[buffer(2)]], packed_float2 device* entryPointParams_out_1 [[buffer(3)]])
{

#line 159
    thread KernelContext_0 kernelContext_0;

#line 159
    (&kernelContext_0)->entryPointParams_0 = entryPointParams_1;

#line 159
    (&kernelContext_0)->entryPointParams_data_0 = entryPointParams_data_1;

#line 159
    (&kernelContext_0)->entryPointParams_tmpl_0 = entryPointParams_tmpl_1;

#line 159
    (&kernelContext_0)->entryPointParams_out_0 = entryPointParams_out_1;

#line 159
    threadgroup array<float2, int(2048)> sh_1;

#line 159
    (&kernelContext_0)->sh_0 = &sh_1;

#line 164
    uint tid_0 = lid_0.x;

#line 164
    uint slot_0 = tid_0 / 16U;

#line 164
    uint lane_0 = tid_0 % 16U;
    uint pair_0 = gid_0.x * 4U + slot_0;
    uint base_0 = slot_0 * 512U;
    if(pair_0 >= (entryPointParams_1->npairs_0))
    {

#line 167
        return;
    }

#line 168
    uint _S11 = pair_0 / (&kernelContext_0)->entryPointParams_0->ntmpl_0;

#line 168
    uint _S12 = pair_0 % (&kernelContext_0)->entryPointParams_0->ntmpl_0;

    thread array<float2, int(32)> r_4;

#line 170
    uint i_1 = 0U;
    for(;;)
    {

#line 171
        if(i_1 < 32U)
        {
        }
        else
        {

#line 171
            break;
        }

#line 172
        uint k_1 = lane_0 + 16U * i_1;
        r_4[i_1] = cmulConj_0(float2(*((&kernelContext_0)->entryPointParams_data_0+(_S11 * 512U + k_1))) , float2(*((&kernelContext_0)->entryPointParams_tmpl_0+(_S12 * 512U + k_1))) );

#line 171
        i_1 = i_1 + 1U;

#line 171
    }



    dftR_0(&r_4);

#line 175
    uint k2_1 = 0U;
    for(;;)
    {

#line 176
        if(k2_1 < 32U)
        {
        }
        else
        {

#line 176
            break;
        }
        r_4[k2_1] = cmul_0(r_4[k2_1], mfTwiddle_0(6.28318548202514648f * float(lane_0 * k2_1) / 512.0f));

#line 176
        k2_1 = k2_1 + 1U;

#line 176
    }

#line 181
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 181
    i_1 = 0U;
    for(;;)
    {

#line 182
        if(i_1 < 32U)
        {
        }
        else
        {

#line 182
            break;
        }

#line 182
        (*(&kernelContext_0)->sh_0)[base_0 + i_1 * 16U + lane_0] = r_4[i_1];

#line 182
        i_1 = i_1 + 1U;

#line 182
    }
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 183
    i_1 = 0U;
    for(;;)
    {

#line 184
        if(i_1 < 32U)
        {
        }
        else
        {

#line 184
            break;
        }

#line 184
        r_4[i_1] = (*(&kernelContext_0)->sh_0)[base_0 + lane_0 * 32U + i_1];

#line 184
        i_1 = i_1 + 1U;

#line 184
    }
    stage2_0(&r_4);

#line 185
    float best_0 = 0.0f;

#line 185
    i_1 = 0U;


    for(;;)
    {

#line 188
        if(i_1 < 32U)
        {
        }
        else
        {

#line 188
            break;
        }

#line 188
        float _S13 = max(best_0, r_4[i_1].x * r_4[i_1].x + r_4[i_1].y * r_4[i_1].y);

#line 188
        uint i_2 = i_1 + 1U;

#line 188
        best_0 = _S13;

#line 188
        i_1 = i_2;

#line 188
    }



    threadgroup_barrier(mem_flags::mem_threadgroup);
    uint _S14 = base_0 + lane_0;

#line 193
    (*(&kernelContext_0)->sh_0)[_S14] = float2(best_0, 0.0f);
    threadgroup_barrier(mem_flags::mem_threadgroup);

#line 194
    uint st_0 = 8U;
    for(;;)
    {

#line 195
        if(st_0 > 0U)
        {
        }
        else
        {

#line 195
            break;
        }

#line 196
        if(lane_0 < st_0)
        {

#line 196
            (*(&kernelContext_0)->sh_0)[_S14] = float2(max((*(&kernelContext_0)->sh_0)[_S14].x, (*(&kernelContext_0)->sh_0)[_S14 + st_0].x), 0.0f);

#line 196
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 195
        st_0 = st_0 >> 1U;

#line 195
    }

#line 203
    if(lane_0 == 0U)
    {

#line 203
        *((&kernelContext_0)->entryPointParams_out_0+pair_0) = packed_float2(float2(sqrt((*(&kernelContext_0)->sh_0)[base_0].x), 0.0f)) ;

#line 203
    }
    return;
}

