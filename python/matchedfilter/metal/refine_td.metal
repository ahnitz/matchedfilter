#include <metal_stdlib>
#include <metal_math>
#include <metal_texture>
using namespace metal;
#ifndef MF_ROW_WINDOWS
#define MF_ROW_WINDOWS 0u
#endif

#line 87 "twiddle.slang"
uint mfRowWindowsFlag_0()
{
    ;
    uint _S1 = ((MF_ROW_WINDOWS));

#line 90
    return _S1;
}


#line 102 "refine_td.slang"
struct EntryPointParams_0
{
    uint n_0;
    uint lastBand_0;
    uint ntmpl_0;
    uint tmplOffset_0;
    uint seriesLength_0;
    uint seriesLayout_0;
    uint tapMeta_0;
    uint directHw_0;
    uint maxLagTap_0;
    uint winStart_0;
    uint winEnd_0;
    uint binsize_0;
    int binShift_0;
    uint nbins_0;
    uint thrBits_0;
    uint gridSize_0;
};


#line 312
struct KernelContext_0
{
    EntryPointParams_0 constant* entryPointParams_0;
    packed_float2 device* entryPointParams_series_0;
    uint device* entryPointParams_starts_0;
    uint device* entryPointParams_taps_0;
    int device* entryPointParams_cidx_0;
    packed_float2 device* entryPointParams_cval_0;
    uint device* entryPointParams_survivors_0;
    uint device* entryPointParams_survCount_0;
    uint device* entryPointParams_fbSurv_0;
    uint device* entryPointParams_fbArgs_0;
    int device* entryPointParams_peakIdx_0;
    packed_float2 device* entryPointParams_peakVal_0;
    uint device* entryPointParams_rowWin_0;
    array<float2, int(1972)> threadgroup* x_sh_0;
    array<uint, int(32)> threadgroup* bestM_sh_0;
    array<int, int(32)> threadgroup* bestK_sh_0;
    array<float2, int(32)> threadgroup* bestV_sh_0;
};


#line 102
[[kernel]] void refineDirect(uint3 gid_0 [[threadgroup_position_in_grid]], uint3 lid_0 [[thread_position_in_threadgroup]], EntryPointParams_0 constant* entryPointParams_1 [[buffer(0)]], packed_float2 device* entryPointParams_series_1 [[buffer(1)]], uint device* entryPointParams_starts_1 [[buffer(2)]], uint device* entryPointParams_taps_1 [[buffer(3)]], int device* entryPointParams_cidx_1 [[buffer(4)]], packed_float2 device* entryPointParams_cval_1 [[buffer(5)]], uint device* entryPointParams_survivors_1 [[buffer(6)]], uint device* entryPointParams_survCount_1 [[buffer(7)]], uint device* entryPointParams_fbSurv_1 [[buffer(8)]], uint device* entryPointParams_fbArgs_1 [[buffer(9)]], int device* entryPointParams_peakIdx_1 [[buffer(10)]], packed_float2 device* entryPointParams_peakVal_1 [[buffer(11)]], uint device* entryPointParams_rowWin_1 [[buffer(12)]])
{

#line 102
    uint we_0;

#line 102
    uint ws_0;

#line 102
    uint binPhase_0;

#line 102
    bool _S2;

#line 102
    float2 x_0;

#line 102
    uint mBits_0;

#line 102
    uint myBestM_0;

#line 102
    uint mBits_1;

#line 102
    uint myBestM_1;

#line 102
    bool _S3;

#line 102
    bool _S4;

#line 102
    bool _S5;

#line 102
    int myBestK_0;

#line 102
    int myBestK_1;

#line 102
    thread KernelContext_0 kernelContext_0;

#line 102
    (&kernelContext_0)->entryPointParams_0 = entryPointParams_1;

#line 102
    (&kernelContext_0)->entryPointParams_series_0 = entryPointParams_series_1;

#line 102
    (&kernelContext_0)->entryPointParams_starts_0 = entryPointParams_starts_1;

#line 102
    (&kernelContext_0)->entryPointParams_taps_0 = entryPointParams_taps_1;

#line 102
    (&kernelContext_0)->entryPointParams_cidx_0 = entryPointParams_cidx_1;

#line 102
    (&kernelContext_0)->entryPointParams_cval_0 = entryPointParams_cval_1;

#line 102
    (&kernelContext_0)->entryPointParams_survivors_0 = entryPointParams_survivors_1;

#line 102
    (&kernelContext_0)->entryPointParams_survCount_0 = entryPointParams_survCount_1;

#line 102
    (&kernelContext_0)->entryPointParams_fbSurv_0 = entryPointParams_fbSurv_1;

#line 102
    (&kernelContext_0)->entryPointParams_fbArgs_0 = entryPointParams_fbArgs_1;

#line 102
    (&kernelContext_0)->entryPointParams_peakIdx_0 = entryPointParams_peakIdx_1;

#line 102
    (&kernelContext_0)->entryPointParams_peakVal_0 = entryPointParams_peakVal_1;

#line 102
    (&kernelContext_0)->entryPointParams_rowWin_0 = entryPointParams_rowWin_1;

#line 102
    threadgroup array<float2, int(1972)> x_sh_1;

#line 102
    (&kernelContext_0)->x_sh_0 = &x_sh_1;

#line 102
    threadgroup array<uint, int(32)> bestM_sh_1;

#line 102
    (&kernelContext_0)->bestM_sh_0 = &bestM_sh_1;

#line 102
    threadgroup array<int, int(32)> bestK_sh_1;

#line 102
    (&kernelContext_0)->bestK_sh_0 = &bestK_sh_1;

#line 102
    threadgroup array<float2, int(32)> bestV_sh_1;

#line 102
    (&kernelContext_0)->bestV_sh_0 = &bestV_sh_1;

#line 131
    uint _S6 = lid_0.x;
    uint _S7 = entryPointParams_survCount_1[int(0)];
    uint tapStride_0 = (entryPointParams_1->tapMeta_0) >> 1U;
    bool isCplx_0 = ((entryPointParams_1->tapMeta_0) & 1U) != 0U;

#line 134
    uint item_0;
    if(isCplx_0)
    {

#line 135
        item_0 = 2U * tapStride_0;

#line 135
    }
    else
    {

#line 135
        item_0 = tapStride_0;

#line 135
    }

#line 135
    uint _S8 = 4U + item_0;

#line 135
    item_0 = gid_0.x;

    for(;;)
    {

#line 137
        if(item_0 < _S7)
        {
        }
        else
        {

#line 137
            break;
        }

#line 138
        uint pair_0 = (&kernelContext_0)->entryPointParams_survivors_0[item_0];
        uint d_0 = pair_0 / (&kernelContext_0)->entryPointParams_0->ntmpl_0;
        uint t_0 = pair_0 - d_0 * (&kernelContext_0)->entryPointParams_0->ntmpl_0;

#line 140
        uint _S9 = (&kernelContext_0)->entryPointParams_0->winStart_0;

#line 140
        uint _S10 = (&kernelContext_0)->entryPointParams_0->winEnd_0;

        for(;;)
        {

#line 142
            uint _S11 = mfRowWindowsFlag_0();

#line 142
            if(_S11 == 0U)
            {

#line 142
                we_0 = _S10;

#line 142
                ws_0 = _S9;

#line 142
                binPhase_0 = 0U;

#line 142
                break;
            }

#line 142
            uint _S12 = 3U * d_0;

#line 142
            uint _S13 = (&kernelContext_0)->entryPointParams_rowWin_0[_S12];

#line 142
            uint _S14 = (&kernelContext_0)->entryPointParams_rowWin_0[_S12 + 2U];

#line 142
            we_0 = (&kernelContext_0)->entryPointParams_rowWin_0[_S12 + 1U];

#line 142
            ws_0 = _S13;

#line 142
            binPhase_0 = _S14;

#line 142
            break;
        }

#line 143
        uint we_1 = min(we_0, (&kernelContext_0)->entryPointParams_0->n_0);

#line 143
        uint bin_0;


        if(ws_0 >= we_1)
        {

#line 147
            uint _S15 = pair_0 * (&kernelContext_0)->entryPointParams_0->nbins_0;

#line 147
            bin_0 = _S6;
            for(;;)
            {

#line 148
                if(bin_0 < ((&kernelContext_0)->entryPointParams_0->nbins_0))
                {
                }
                else
                {

#line 148
                    break;
                }

#line 149
                uint _S16 = _S15 + bin_0;

#line 149
                *((&kernelContext_0)->entryPointParams_peakIdx_0+_S16) = int(-1);

#line 149
                *((&kernelContext_0)->entryPointParams_peakVal_0+_S16) = packed_float2(float2(0.0f, 0.0f)) ;

#line 148
                bin_0 = bin_0 + 32U;

#line 148
            }



            item_0 = item_0 + (&kernelContext_0)->entryPointParams_0->gridSize_0;

#line 137
            continue;
        }

#line 137
        uint jb_0;

#line 156
        if(((&kernelContext_0)->entryPointParams_0->binShift_0) >= int(0))
        {

#line 156
            jb_0 = binPhase_0 >> uint((&kernelContext_0)->entryPointParams_0->binShift_0);

#line 156
        }
        else
        {

#line 156
            uint _S17 = binPhase_0 / (&kernelContext_0)->entryPointParams_0->binsize_0;

#line 156
            jb_0 = _S17;

#line 156
        }
        uint lastOff_0 = we_1 - 1U - ws_0 + binPhase_0;

#line 157
        uint jbLast_0;
        if(((&kernelContext_0)->entryPointParams_0->binShift_0) >= int(0))
        {

#line 158
            jbLast_0 = lastOff_0 >> uint((&kernelContext_0)->entryPointParams_0->binShift_0);

#line 158
        }
        else
        {

#line 158
            uint _S18 = lastOff_0 / (&kernelContext_0)->entryPointParams_0->binsize_0;

#line 158
            jbLast_0 = _S18;

#line 158
        }
        if(jb_0 != jbLast_0)
        {

#line 160
            if(_S6 == 0U)
            {
                uint slot_0 = atomic_fetch_add_explicit(((atomic_uint device*)((&kernelContext_0)->entryPointParams_fbArgs_0+int(0))), 1U, memory_order_relaxed);
                *((&kernelContext_0)->entryPointParams_fbSurv_0+slot_0) = pair_0;

#line 160
            }

#line 165
            item_0 = item_0 + (&kernelContext_0)->entryPointParams_0->gridSize_0;

#line 137
            continue;
        }

#line 169
        int ceIdx_0 = (&kernelContext_0)->entryPointParams_cidx_0[pair_0];

#line 169
        float2 _S19 = float2(*((&kernelContext_0)->entryPointParams_cval_0+pair_0)) ;

#line 169
        bool _S20;


        if(ceIdx_0 < int(0))
        {

#line 172
            _S20 = true;

#line 172
        }
        else
        {

#line 172
            _S20 = ((as_type<uint>((_S19.x))) & 2147483647U) >= 2139095039U;

#line 172
        }

#line 172
        bool badCoarse_0;
        if(_S20)
        {

#line 173
            badCoarse_0 = true;

#line 173
        }
        else
        {

#line 173
            badCoarse_0 = ((as_type<uint>((_S19.y))) & 2147483647U) >= 2139095039U;

#line 173
        }
        if(badCoarse_0)
        {

#line 175
            if(_S6 == 0U)
            {
                uint slot_1 = atomic_fetch_add_explicit(((atomic_uint device*)((&kernelContext_0)->entryPointParams_fbArgs_0+int(0))), 1U, memory_order_relaxed);
                *((&kernelContext_0)->entryPointParams_fbSurv_0+slot_1) = pair_0;

#line 175
            }

#line 180
            item_0 = item_0 + (&kernelContext_0)->entryPointParams_0->gridSize_0;

#line 137
            continue;
        }

#line 183
        uint _S21 = (&kernelContext_0)->entryPointParams_0->n_0 / (&kernelContext_0)->entryPointParams_0->lastBand_0;

#line 183
        int rStep_0 = int(_S21);
        int hwLags_0 = int((&kernelContext_0)->entryPointParams_0->directHw_0) * rStep_0;
        int _S22 = int(ws_0);

#line 185
        int _S23 = ceIdx_0 * rStep_0;

#line 185
        int _S24 = max(_S22, _S23 - hwLags_0);
        int _S25 = int(we_1);

#line 186
        int _S26 = min(_S25, _S23 + hwLags_0 + int(1));
        if(_S24 >= _S26)
        {

#line 188
            uint _S27 = pair_0 * (&kernelContext_0)->entryPointParams_0->nbins_0;

#line 188
            bin_0 = _S6;
            for(;;)
            {

#line 189
                if(bin_0 < ((&kernelContext_0)->entryPointParams_0->nbins_0))
                {
                }
                else
                {

#line 189
                    break;
                }

#line 190
                uint _S28 = _S27 + bin_0;

#line 190
                *((&kernelContext_0)->entryPointParams_peakIdx_0+_S28) = int(-1);

#line 190
                *((&kernelContext_0)->entryPointParams_peakVal_0+_S28) = packed_float2(float2(0.0f, 0.0f)) ;

#line 189
                bin_0 = bin_0 + 32U;

#line 189
            }



            item_0 = item_0 + (&kernelContext_0)->entryPointParams_0->gridSize_0;

#line 137
            continue;
        }

#line 196
        uint tRow_0 = (t_0 + (&kernelContext_0)->entryPointParams_0->tmplOffset_0) * _S8;
        int L_0 = int((&kernelContext_0)->entryPointParams_taps_0[tRow_0]);

        int s0_0 = _S24 - (L_0 >> 1U);
        int mLags_0 = _S26 - _S24;
        int need_0 = mLags_0 + L_0 - int(1);

#line 201
        bool _S29;
        if(s0_0 < int(0))
        {

#line 202
            _S29 = true;

#line 202
        }
        else
        {

#line 202
            _S29 = (s0_0 + need_0) > int((&kernelContext_0)->entryPointParams_0->n_0);

#line 202
        }

#line 202
        bool _S30;

#line 202
        if(_S29)
        {

#line 202
            _S30 = true;

#line 202
        }
        else
        {

#line 202
            _S30 = uint(need_0) > 1968U;

#line 202
        }

#line 202
        bool _S31;
        if(_S30)
        {

#line 203
            _S31 = true;

#line 203
        }
        else
        {

#line 203
            _S31 = (uint(mLags_0) * uint(L_0)) >= ((&kernelContext_0)->entryPointParams_0->maxLagTap_0);

#line 203
        }

#line 202
        if(_S31)
        {
            if(_S6 == 0U)
            {
                uint slot_2 = atomic_fetch_add_explicit(((atomic_uint device*)((&kernelContext_0)->entryPointParams_fbArgs_0+int(0))), 1U, memory_order_relaxed);
                *((&kernelContext_0)->entryPointParams_fbSurv_0+slot_2) = pair_0;

#line 204
            }

#line 209
            item_0 = item_0 + (&kernelContext_0)->entryPointParams_0->gridSize_0;

#line 137
            continue;
        }

#line 213
        uint _S32 = (&kernelContext_0)->entryPointParams_starts_0[d_0];
        uint uNeed_0 = uint(need_0);

#line 214
        uint i_0 = _S6;
        for(;;)
        {

#line 215
            if(i_0 < uNeed_0)
            {
            }
            else
            {

#line 215
                break;
            }

#line 216
            uint off_0 = uint(s0_0) + i_0;
            float2 _S33 = float2(0.0f, 0.0f);
            if(_S32 < ((&kernelContext_0)->entryPointParams_0->seriesLength_0))
            {

#line 218
                _S2 = off_0 < ((&kernelContext_0)->entryPointParams_0->seriesLength_0 - _S32);

#line 218
            }
            else
            {

#line 218
                _S2 = false;

#line 218
            }

#line 218
            if(_S2)
            {

#line 219
                uint _S34 = _S32 + off_0;

#line 219
                uint _S35 = (&kernelContext_0)->entryPointParams_0->seriesLayout_0;

#line 219
                for(;;)
                {

#line 219
                    if(_S35 == 0U)
                    {

#line 219
                        x_0 = float2(*((&kernelContext_0)->entryPointParams_series_0+_S34)) ;

#line 219
                        break;
                    }

#line 219
                    uint f_0 = (_S35 >> 2U) + (_S35 & 3U) * _S34;

#line 219
                    float2 _S36 = float2(*((&kernelContext_0)->entryPointParams_series_0+(f_0 >> 1U))) ;

#line 219
                    float _S37;

#line 219
                    if((f_0 & 1U) != 0U)
                    {

#line 219
                        _S37 = _S36.y;

#line 219
                    }
                    else
                    {

#line 219
                        _S37 = _S36.x;

#line 219
                    }

#line 219
                    x_0 = float2(_S37, 0.0f);

#line 219
                    break;
                }

#line 218
            }
            else
            {

#line 218
                x_0 = _S33;

#line 218
            }

            (*(&kernelContext_0)->x_sh_0)[i_0] = x_0;

#line 215
            i_0 = i_0 + 32U;

#line 215
        }

#line 222
        if(_S6 < 4U)
        {

#line 223
            (*(&kernelContext_0)->x_sh_0)[uNeed_0 + _S6] = float2(0.0f, 0.0f);

#line 222
        }

        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 229
        uint _S38 = uint(mLags_0);
        uint _S39 = (uint(L_0) + 3U) & 4294967292U;
        uint _S40 = tRow_0 + 4U;

#line 231
        uint _S41 = (&kernelContext_0)->entryPointParams_0->thrBits_0;


        float2 _S42 = float2(0.0f, 0.0f);

#line 234
        uint lagBase_0 = 0U;

#line 234
        uint myBestM_2 = _S41;

#line 234
        int myBestK_2 = int(-1);

#line 234
        x_0 = _S42;
        for(;;)
        {

#line 235
            if(lagBase_0 < _S38)
            {
            }
            else
            {

#line 235
                break;
            }

#line 236
            uint lag0_0 = lagBase_0 + _S6;
            uint _S43 = _S38 - 1U;

#line 237
            uint _S44 = min(lag0_0, _S43);

#line 237
            float2 myBestV_0;
            if((lagBase_0 + 32U) < _S38)
            {

#line 239
                uint lag1_0 = lag0_0 + 32U;
                uint _S45 = min(lag1_0, _S43);
                thread float2 acc0_0 = _S42;
                thread float2 acc1_0 = _S42;
                if(!isCplx_0)
                {

#line 243
                    mBits_0 = 0U;
                    for(;;)
                    {

#line 244
                        if(mBits_0 < _S39)
                        {
                        }
                        else
                        {

#line 244
                            break;
                        }

#line 245
                        uint _S46 = _S40 + mBits_0;



                        uint _S47 = _S44 + mBits_0;

#line 249
                        float2 _S48 = float2((as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[_S46])))) ;

#line 249
                        float2 _S49 = float2((as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[_S46 + 1U])))) ;

#line 249
                        float2 _S50 = float2((as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[_S46 + 2U])))) ;

#line 249
                        float2 _S51 = float2((as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[_S46 + 3U])))) ;

#line 249
                        acc0_0 = acc0_0 + (_S48 * (*(&kernelContext_0)->x_sh_0)[_S47] + _S49 * (*(&kernelContext_0)->x_sh_0)[_S47 + 1U] + _S50 * (*(&kernelContext_0)->x_sh_0)[_S47 + 2U] + _S51 * (*(&kernelContext_0)->x_sh_0)[_S47 + 3U]);



                        uint _S52 = _S45 + mBits_0;

#line 253
                        acc1_0 = acc1_0 + (_S48 * (*(&kernelContext_0)->x_sh_0)[_S52] + _S49 * (*(&kernelContext_0)->x_sh_0)[_S52 + 1U] + _S50 * (*(&kernelContext_0)->x_sh_0)[_S52 + 2U] + _S51 * (*(&kernelContext_0)->x_sh_0)[_S52 + 3U]);

#line 244
                        mBits_0 = mBits_0 + 4U;

#line 244
                    }

#line 243
                }
                else
                {

#line 243
                    mBits_0 = 0U;

#line 259
                    for(;;)
                    {

#line 259
                        if(mBits_0 < _S39)
                        {
                        }
                        else
                        {

#line 259
                            break;
                        }

#line 260
                        uint hk_0 = _S40 + 2U * mBits_0;
                        float hr0_0 = (as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[hk_0])));
                        float hi0_0 = (as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[hk_0 + 1U])));
                        float hr1_0 = (as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[hk_0 + 2U])));
                        float hi1_0 = (as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[hk_0 + 3U])));
                        uint _S53 = _S44 + mBits_0;

                        float _S54 = (*(&kernelContext_0)->x_sh_0)[_S53].x;

#line 267
                        float _S55 = (*(&kernelContext_0)->x_sh_0)[_S53].y;

#line 267
                        float _S56 = (*(&kernelContext_0)->x_sh_0)[_S53 + 1U].x;

#line 267
                        float _S57 = (*(&kernelContext_0)->x_sh_0)[_S53 + 1U].y;

#line 267
                        acc0_0.x = acc0_0.x + (hr0_0 * _S54 - hi0_0 * _S55 + hr1_0 * _S56 - hi1_0 * _S57);
                        acc0_0.y = acc0_0.y + (hr0_0 * _S55 + hi0_0 * _S54 + hr1_0 * _S57 + hi1_0 * _S56);
                        uint _S58 = _S45 + mBits_0;

                        float _S59 = (*(&kernelContext_0)->x_sh_0)[_S58].x;

#line 271
                        float _S60 = (*(&kernelContext_0)->x_sh_0)[_S58].y;

#line 271
                        float _S61 = (*(&kernelContext_0)->x_sh_0)[_S58 + 1U].x;

#line 271
                        float _S62 = (*(&kernelContext_0)->x_sh_0)[_S58 + 1U].y;

#line 271
                        acc1_0.x = acc1_0.x + (hr0_0 * _S59 - hi0_0 * _S60 + hr1_0 * _S61 - hi1_0 * _S62);
                        acc1_0.y = acc1_0.y + (hr0_0 * _S60 + hi0_0 * _S59 + hr1_0 * _S62 + hi1_0 * _S61);

#line 259
                        mBits_0 = mBits_0 + 2U;

#line 259
                    }

#line 243
                }

#line 275
                float2 _S63 = acc0_0;

#line 275
                int _S64 = _S24 + int(lag0_0);

#line 275
                float _S65 = _S63.x;

#line 275
                float _S66 = _S63.y;

#line 275
                uint zy_0 = (as_type<uint>((_S66))) & 2147483647U;

#line 275
                if(((as_type<uint>((_S65))) & 2147483647U) >= 2139095040U)
                {

#line 275
                    _S2 = true;

#line 275
                }
                else
                {

#line 275
                    _S2 = zy_0 >= 2139095040U;

#line 275
                }

#line 275
                if(_S2)
                {

#line 275
                    mBits_0 = 2139095040U;

#line 275
                }
                else
                {

#line 275
                    mBits_0 = (as_type<uint>((_S65 * _S65 + _S66 * _S66)));

#line 275
                }

#line 275
                if(mBits_0 > myBestM_2)
                {

#line 275
                    _S3 = true;

#line 275
                }
                else
                {

#line 275
                    if(mBits_0 == myBestM_2)
                    {

#line 275
                        _S3 = myBestK_2 < int(0);

#line 275
                    }
                    else
                    {

#line 275
                        _S3 = false;

#line 275
                    }

#line 275
                }

#line 275
                if(_S3)
                {

#line 275
                    myBestM_0 = mBits_0;

#line 275
                    myBestK_0 = _S64;

#line 275
                    myBestV_0 = _S63;

#line 275
                }
                else
                {

#line 275
                    myBestM_0 = myBestM_2;

#line 275
                    myBestK_0 = myBestK_2;

#line 275
                    myBestV_0 = x_0;

#line 275
                }

#line 275
                float2 myBestV_1;
                if(lag1_0 < _S38)
                {

#line 277
                    float2 _S67 = acc1_0;

#line 277
                    int _S68 = _S24 + int(lag1_0);

#line 277
                    float _S69 = acc1_0.x;

#line 277
                    float _S70 = acc1_0.y;

#line 277
                    uint zy_1 = (as_type<uint>((_S70))) & 2147483647U;

#line 277
                    if(((as_type<uint>((_S69))) & 2147483647U) >= 2139095040U)
                    {

#line 277
                        _S4 = true;

#line 277
                    }
                    else
                    {

#line 277
                        _S4 = zy_1 >= 2139095040U;

#line 277
                    }

#line 277
                    if(_S4)
                    {

#line 277
                        mBits_1 = 2139095040U;

#line 277
                    }
                    else
                    {

#line 277
                        mBits_1 = (as_type<uint>((_S69 * _S69 + _S70 * _S70)));

#line 277
                    }

#line 277
                    if(mBits_1 > myBestM_0)
                    {

#line 277
                        _S5 = true;

#line 277
                    }
                    else
                    {

#line 277
                        if(mBits_1 == myBestM_0)
                        {

#line 277
                            _S5 = myBestK_0 < int(0);

#line 277
                        }
                        else
                        {

#line 277
                            _S5 = false;

#line 277
                        }

#line 277
                    }

#line 277
                    if(_S5)
                    {

#line 277
                        myBestM_1 = mBits_1;

#line 277
                        myBestK_1 = _S68;

#line 277
                        myBestV_1 = _S67;

#line 277
                    }
                    else
                    {

#line 277
                        myBestM_1 = myBestM_0;

#line 277
                        myBestK_1 = myBestK_0;

#line 277
                        myBestV_1 = myBestV_0;

#line 277
                    }

#line 276
                }
                else
                {

#line 276
                    myBestM_1 = myBestM_0;

#line 276
                    myBestK_1 = myBestK_0;

#line 276
                    myBestV_1 = myBestV_0;

#line 276
                }

#line 276
                myBestM_0 = myBestM_1;

#line 276
                myBestK_0 = myBestK_1;

#line 276
                myBestV_0 = myBestV_1;

#line 238
            }
            else
            {

#line 279
                thread float2 acc0_1 = _S42;
                if(!isCplx_0)
                {

#line 280
                    mBits_0 = 0U;
                    for(;;)
                    {

#line 281
                        if(mBits_0 < _S39)
                        {
                        }
                        else
                        {

#line 281
                            break;
                        }

#line 282
                        uint _S71 = _S40 + mBits_0;



                        uint _S72 = _S44 + mBits_0;

#line 286
                        acc0_1 = acc0_1 + (float2((as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[_S71]))))  * (*(&kernelContext_0)->x_sh_0)[_S72] + float2((as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[_S71 + 1U]))))  * (*(&kernelContext_0)->x_sh_0)[_S72 + 1U] + float2((as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[_S71 + 2U]))))  * (*(&kernelContext_0)->x_sh_0)[_S72 + 2U] + float2((as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[_S71 + 3U]))))  * (*(&kernelContext_0)->x_sh_0)[_S72 + 3U]);

#line 281
                        mBits_0 = mBits_0 + 4U;

#line 281
                    }

#line 280
                }
                else
                {

#line 280
                    mBits_0 = 0U;

#line 292
                    for(;;)
                    {

#line 292
                        if(mBits_0 < _S39)
                        {
                        }
                        else
                        {

#line 292
                            break;
                        }

#line 293
                        uint hk_1 = _S40 + 2U * mBits_0;
                        float hr0_1 = (as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[hk_1])));
                        float hi0_1 = (as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[hk_1 + 1U])));
                        float hr1_1 = (as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[hk_1 + 2U])));
                        float hi1_1 = (as_type<float>(((&kernelContext_0)->entryPointParams_taps_0[hk_1 + 3U])));
                        uint _S73 = _S44 + mBits_0;

                        float _S74 = (*(&kernelContext_0)->x_sh_0)[_S73].x;

#line 300
                        float _S75 = (*(&kernelContext_0)->x_sh_0)[_S73].y;

#line 300
                        float _S76 = (*(&kernelContext_0)->x_sh_0)[_S73 + 1U].x;

#line 300
                        float _S77 = (*(&kernelContext_0)->x_sh_0)[_S73 + 1U].y;

#line 300
                        acc0_1.x = acc0_1.x + (hr0_1 * _S74 - hi0_1 * _S75 + hr1_1 * _S76 - hi1_1 * _S77);
                        acc0_1.y = acc0_1.y + (hr0_1 * _S75 + hi0_1 * _S74 + hr1_1 * _S77 + hi1_1 * _S76);

#line 292
                        mBits_0 = mBits_0 + 2U;

#line 292
                    }

#line 280
                }

#line 304
                if(lag0_0 < _S38)
                {

#line 305
                    float2 _S78 = acc0_1;

#line 305
                    int _S79 = _S24 + int(lag0_0);

#line 305
                    float _S80 = acc0_1.x;

#line 305
                    float _S81 = acc0_1.y;

#line 305
                    uint zy_2 = (as_type<uint>((_S81))) & 2147483647U;

#line 305
                    if(((as_type<uint>((_S80))) & 2147483647U) >= 2139095040U)
                    {

#line 305
                        _S2 = true;

#line 305
                    }
                    else
                    {

#line 305
                        _S2 = zy_2 >= 2139095040U;

#line 305
                    }

#line 305
                    if(_S2)
                    {

#line 305
                        mBits_0 = 2139095040U;

#line 305
                    }
                    else
                    {

#line 305
                        mBits_0 = (as_type<uint>((_S80 * _S80 + _S81 * _S81)));

#line 305
                    }

#line 305
                    if(mBits_0 > myBestM_2)
                    {

#line 305
                        _S3 = true;

#line 305
                    }
                    else
                    {

#line 305
                        if(mBits_0 == myBestM_2)
                        {

#line 305
                            _S3 = myBestK_2 < int(0);

#line 305
                        }
                        else
                        {

#line 305
                            _S3 = false;

#line 305
                        }

#line 305
                    }

#line 305
                    if(_S3)
                    {

#line 305
                        myBestM_0 = mBits_0;

#line 305
                        myBestK_0 = _S79;

#line 305
                        myBestV_0 = _S78;

#line 305
                    }
                    else
                    {

#line 305
                        myBestM_0 = myBestM_2;

#line 305
                        myBestK_0 = myBestK_2;

#line 305
                        myBestV_0 = x_0;

#line 305
                    }

#line 304
                }
                else
                {

#line 304
                    myBestM_0 = myBestM_2;

#line 304
                    myBestK_0 = myBestK_2;

#line 304
                    myBestV_0 = x_0;

#line 304
                }

#line 238
            }

#line 235
            lagBase_0 = lagBase_0 + 64U;

#line 235
            myBestM_2 = myBestM_0;

#line 235
            myBestK_2 = myBestK_0;

#line 235
            x_0 = myBestV_0;

#line 235
        }

#line 310
        (*(&kernelContext_0)->bestM_sh_0)[_S6] = myBestM_2;
        (*(&kernelContext_0)->bestK_sh_0)[_S6] = myBestK_2;
        (*(&kernelContext_0)->bestV_sh_0)[_S6] = x_0;
        threadgroup_barrier(mem_flags::mem_threadgroup);

#line 313
        uint _S82 = (&kernelContext_0)->entryPointParams_0->thrBits_0;

#line 319
        uint m_0 = (*(&kernelContext_0)->bestM_sh_0)[0U];
        int k_0 = (*(&kernelContext_0)->bestK_sh_0)[0U];
        if(((*(&kernelContext_0)->bestM_sh_0)[0U]) > _S82)
        {

#line 321
            _S2 = true;

#line 321
        }
        else
        {

#line 321
            if(m_0 == _S82)
            {

#line 321
                _S2 = k_0 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S2 = false;

#line 321
            }

#line 321
        }

#line 321
        if(_S2)
        {

#line 321
            mBits_0 = m_0;

#line 321
            myBestK_0 = k_0;

#line 321
        }
        else
        {

#line 321
            mBits_0 = _S82;

#line 321
            myBestK_0 = int(-1);

#line 321
        }

#line 319
        uint m_1 = (*(&kernelContext_0)->bestM_sh_0)[1U];
        int k_1 = (*(&kernelContext_0)->bestK_sh_0)[1U];
        if(((*(&kernelContext_0)->bestM_sh_0)[1U]) > mBits_0)
        {

#line 321
            _S3 = true;

#line 321
        }
        else
        {

#line 321
            if(m_1 == mBits_0)
            {

#line 321
                _S3 = k_1 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S3 = false;

#line 321
            }

#line 321
            if(_S3)
            {

#line 321
                if(myBestK_0 < int(0))
                {

#line 321
                    _S4 = true;

#line 321
                }
                else
                {

#line 321
                    _S4 = k_1 < myBestK_0;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S4 = false;

#line 321
            }

#line 321
            _S3 = _S4;

#line 321
        }

#line 321
        if(_S3)
        {

#line 321
            myBestM_0 = m_1;

#line 321
            myBestK_1 = k_1;

#line 321
            mBits_1 = 1U;

#line 321
        }
        else
        {

#line 321
            myBestM_0 = mBits_0;

#line 321
            myBestK_1 = myBestK_0;

#line 321
            mBits_1 = 0U;

#line 321
        }

#line 319
        uint m_2 = (*(&kernelContext_0)->bestM_sh_0)[2U];
        int k_2 = (*(&kernelContext_0)->bestK_sh_0)[2U];
        if(((*(&kernelContext_0)->bestM_sh_0)[2U]) > myBestM_0)
        {

#line 321
            _S4 = true;

#line 321
        }
        else
        {

#line 321
            if(m_2 == myBestM_0)
            {

#line 321
                _S4 = k_2 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S4 = false;

#line 321
            }

#line 321
            if(_S4)
            {

#line 321
                if(myBestK_1 < int(0))
                {

#line 321
                    _S5 = true;

#line 321
                }
                else
                {

#line 321
                    _S5 = k_2 < myBestK_1;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S5 = false;

#line 321
            }

#line 321
            _S4 = _S5;

#line 321
        }

#line 321
        uint bestLane_0;

#line 321
        int bestK_0;

#line 321
        if(_S4)
        {

#line 321
            myBestM_1 = m_2;

#line 321
            bestK_0 = k_2;

#line 321
            bestLane_0 = 2U;

#line 321
        }
        else
        {

#line 321
            myBestM_1 = myBestM_0;

#line 321
            bestK_0 = myBestK_1;

#line 321
            bestLane_0 = mBits_1;

#line 321
        }

#line 319
        uint m_3 = (*(&kernelContext_0)->bestM_sh_0)[3U];
        int k_3 = (*(&kernelContext_0)->bestK_sh_0)[3U];

#line 320
        bool _S83;
        if(((*(&kernelContext_0)->bestM_sh_0)[3U]) > myBestM_1)
        {

#line 321
            _S5 = true;

#line 321
        }
        else
        {

#line 321
            if(m_3 == myBestM_1)
            {

#line 321
                _S5 = k_3 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S5 = false;

#line 321
            }

#line 321
            if(_S5)
            {

#line 321
                if(bestK_0 < int(0))
                {

#line 321
                    _S83 = true;

#line 321
                }
                else
                {

#line 321
                    _S83 = k_3 < bestK_0;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S83 = false;

#line 321
            }

#line 321
            _S5 = _S83;

#line 321
        }

#line 321
        uint bestM_0;

#line 321
        uint bestLane_1;

#line 321
        int bestK_1;

#line 321
        if(_S5)
        {

#line 321
            bestM_0 = m_3;

#line 321
            bestK_1 = k_3;

#line 321
            bestLane_1 = 3U;

#line 321
        }
        else
        {

#line 321
            bestM_0 = myBestM_1;

#line 321
            bestK_1 = bestK_0;

#line 321
            bestLane_1 = bestLane_0;

#line 321
        }

#line 319
        uint m_4 = (*(&kernelContext_0)->bestM_sh_0)[4U];
        int k_4 = (*(&kernelContext_0)->bestK_sh_0)[4U];

#line 320
        bool _S84;
        if(((*(&kernelContext_0)->bestM_sh_0)[4U]) > bestM_0)
        {

#line 321
            _S83 = true;

#line 321
        }
        else
        {

#line 321
            if(m_4 == bestM_0)
            {

#line 321
                _S83 = k_4 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S83 = false;

#line 321
            }

#line 321
            if(_S83)
            {

#line 321
                if(bestK_1 < int(0))
                {

#line 321
                    _S84 = true;

#line 321
                }
                else
                {

#line 321
                    _S84 = k_4 < bestK_1;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S84 = false;

#line 321
            }

#line 321
            _S83 = _S84;

#line 321
        }

#line 321
        uint bestM_1;

#line 321
        uint bestLane_2;

#line 321
        int bestK_2;

#line 321
        if(_S83)
        {

#line 321
            bestM_1 = m_4;

#line 321
            bestK_2 = k_4;

#line 321
            bestLane_2 = 4U;

#line 321
        }
        else
        {

#line 321
            bestM_1 = bestM_0;

#line 321
            bestK_2 = bestK_1;

#line 321
            bestLane_2 = bestLane_1;

#line 321
        }

#line 319
        uint m_5 = (*(&kernelContext_0)->bestM_sh_0)[5U];
        int k_5 = (*(&kernelContext_0)->bestK_sh_0)[5U];

#line 320
        bool _S85;
        if(((*(&kernelContext_0)->bestM_sh_0)[5U]) > bestM_1)
        {

#line 321
            _S84 = true;

#line 321
        }
        else
        {

#line 321
            if(m_5 == bestM_1)
            {

#line 321
                _S84 = k_5 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S84 = false;

#line 321
            }

#line 321
            if(_S84)
            {

#line 321
                if(bestK_2 < int(0))
                {

#line 321
                    _S85 = true;

#line 321
                }
                else
                {

#line 321
                    _S85 = k_5 < bestK_2;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S85 = false;

#line 321
            }

#line 321
            _S84 = _S85;

#line 321
        }

#line 321
        uint bestM_2;

#line 321
        uint bestLane_3;

#line 321
        int bestK_3;

#line 321
        if(_S84)
        {

#line 321
            bestM_2 = m_5;

#line 321
            bestK_3 = k_5;

#line 321
            bestLane_3 = 5U;

#line 321
        }
        else
        {

#line 321
            bestM_2 = bestM_1;

#line 321
            bestK_3 = bestK_2;

#line 321
            bestLane_3 = bestLane_2;

#line 321
        }

#line 319
        uint m_6 = (*(&kernelContext_0)->bestM_sh_0)[6U];
        int k_6 = (*(&kernelContext_0)->bestK_sh_0)[6U];

#line 320
        bool _S86;
        if(((*(&kernelContext_0)->bestM_sh_0)[6U]) > bestM_2)
        {

#line 321
            _S85 = true;

#line 321
        }
        else
        {

#line 321
            if(m_6 == bestM_2)
            {

#line 321
                _S85 = k_6 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S85 = false;

#line 321
            }

#line 321
            if(_S85)
            {

#line 321
                if(bestK_3 < int(0))
                {

#line 321
                    _S86 = true;

#line 321
                }
                else
                {

#line 321
                    _S86 = k_6 < bestK_3;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S86 = false;

#line 321
            }

#line 321
            _S85 = _S86;

#line 321
        }

#line 321
        uint bestM_3;

#line 321
        uint bestLane_4;

#line 321
        int bestK_4;

#line 321
        if(_S85)
        {

#line 321
            bestM_3 = m_6;

#line 321
            bestK_4 = k_6;

#line 321
            bestLane_4 = 6U;

#line 321
        }
        else
        {

#line 321
            bestM_3 = bestM_2;

#line 321
            bestK_4 = bestK_3;

#line 321
            bestLane_4 = bestLane_3;

#line 321
        }

#line 319
        uint m_7 = (*(&kernelContext_0)->bestM_sh_0)[7U];
        int k_7 = (*(&kernelContext_0)->bestK_sh_0)[7U];

#line 320
        bool _S87;
        if(((*(&kernelContext_0)->bestM_sh_0)[7U]) > bestM_3)
        {

#line 321
            _S86 = true;

#line 321
        }
        else
        {

#line 321
            if(m_7 == bestM_3)
            {

#line 321
                _S86 = k_7 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S86 = false;

#line 321
            }

#line 321
            if(_S86)
            {

#line 321
                if(bestK_4 < int(0))
                {

#line 321
                    _S87 = true;

#line 321
                }
                else
                {

#line 321
                    _S87 = k_7 < bestK_4;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S87 = false;

#line 321
            }

#line 321
            _S86 = _S87;

#line 321
        }

#line 321
        uint bestM_4;

#line 321
        uint bestLane_5;

#line 321
        int bestK_5;

#line 321
        if(_S86)
        {

#line 321
            bestM_4 = m_7;

#line 321
            bestK_5 = k_7;

#line 321
            bestLane_5 = 7U;

#line 321
        }
        else
        {

#line 321
            bestM_4 = bestM_3;

#line 321
            bestK_5 = bestK_4;

#line 321
            bestLane_5 = bestLane_4;

#line 321
        }

#line 319
        uint m_8 = (*(&kernelContext_0)->bestM_sh_0)[8U];
        int k_8 = (*(&kernelContext_0)->bestK_sh_0)[8U];

#line 320
        bool _S88;
        if(((*(&kernelContext_0)->bestM_sh_0)[8U]) > bestM_4)
        {

#line 321
            _S87 = true;

#line 321
        }
        else
        {

#line 321
            if(m_8 == bestM_4)
            {

#line 321
                _S87 = k_8 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S87 = false;

#line 321
            }

#line 321
            if(_S87)
            {

#line 321
                if(bestK_5 < int(0))
                {

#line 321
                    _S88 = true;

#line 321
                }
                else
                {

#line 321
                    _S88 = k_8 < bestK_5;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S88 = false;

#line 321
            }

#line 321
            _S87 = _S88;

#line 321
        }

#line 321
        uint bestM_5;

#line 321
        uint bestLane_6;

#line 321
        int bestK_6;

#line 321
        if(_S87)
        {

#line 321
            bestM_5 = m_8;

#line 321
            bestK_6 = k_8;

#line 321
            bestLane_6 = 8U;

#line 321
        }
        else
        {

#line 321
            bestM_5 = bestM_4;

#line 321
            bestK_6 = bestK_5;

#line 321
            bestLane_6 = bestLane_5;

#line 321
        }

#line 319
        uint m_9 = (*(&kernelContext_0)->bestM_sh_0)[9U];
        int k_9 = (*(&kernelContext_0)->bestK_sh_0)[9U];

#line 320
        bool _S89;
        if(((*(&kernelContext_0)->bestM_sh_0)[9U]) > bestM_5)
        {

#line 321
            _S88 = true;

#line 321
        }
        else
        {

#line 321
            if(m_9 == bestM_5)
            {

#line 321
                _S88 = k_9 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S88 = false;

#line 321
            }

#line 321
            if(_S88)
            {

#line 321
                if(bestK_6 < int(0))
                {

#line 321
                    _S89 = true;

#line 321
                }
                else
                {

#line 321
                    _S89 = k_9 < bestK_6;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S89 = false;

#line 321
            }

#line 321
            _S88 = _S89;

#line 321
        }

#line 321
        uint bestM_6;

#line 321
        uint bestLane_7;

#line 321
        int bestK_7;

#line 321
        if(_S88)
        {

#line 321
            bestM_6 = m_9;

#line 321
            bestK_7 = k_9;

#line 321
            bestLane_7 = 9U;

#line 321
        }
        else
        {

#line 321
            bestM_6 = bestM_5;

#line 321
            bestK_7 = bestK_6;

#line 321
            bestLane_7 = bestLane_6;

#line 321
        }

#line 319
        uint m_10 = (*(&kernelContext_0)->bestM_sh_0)[10U];
        int k_10 = (*(&kernelContext_0)->bestK_sh_0)[10U];

#line 320
        bool _S90;
        if(((*(&kernelContext_0)->bestM_sh_0)[10U]) > bestM_6)
        {

#line 321
            _S89 = true;

#line 321
        }
        else
        {

#line 321
            if(m_10 == bestM_6)
            {

#line 321
                _S89 = k_10 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S89 = false;

#line 321
            }

#line 321
            if(_S89)
            {

#line 321
                if(bestK_7 < int(0))
                {

#line 321
                    _S90 = true;

#line 321
                }
                else
                {

#line 321
                    _S90 = k_10 < bestK_7;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S90 = false;

#line 321
            }

#line 321
            _S89 = _S90;

#line 321
        }

#line 321
        uint bestM_7;

#line 321
        uint bestLane_8;

#line 321
        int bestK_8;

#line 321
        if(_S89)
        {

#line 321
            bestM_7 = m_10;

#line 321
            bestK_8 = k_10;

#line 321
            bestLane_8 = 10U;

#line 321
        }
        else
        {

#line 321
            bestM_7 = bestM_6;

#line 321
            bestK_8 = bestK_7;

#line 321
            bestLane_8 = bestLane_7;

#line 321
        }

#line 319
        uint m_11 = (*(&kernelContext_0)->bestM_sh_0)[11U];
        int k_11 = (*(&kernelContext_0)->bestK_sh_0)[11U];

#line 320
        bool _S91;
        if(((*(&kernelContext_0)->bestM_sh_0)[11U]) > bestM_7)
        {

#line 321
            _S90 = true;

#line 321
        }
        else
        {

#line 321
            if(m_11 == bestM_7)
            {

#line 321
                _S90 = k_11 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S90 = false;

#line 321
            }

#line 321
            if(_S90)
            {

#line 321
                if(bestK_8 < int(0))
                {

#line 321
                    _S91 = true;

#line 321
                }
                else
                {

#line 321
                    _S91 = k_11 < bestK_8;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S91 = false;

#line 321
            }

#line 321
            _S90 = _S91;

#line 321
        }

#line 321
        uint bestM_8;

#line 321
        uint bestLane_9;

#line 321
        int bestK_9;

#line 321
        if(_S90)
        {

#line 321
            bestM_8 = m_11;

#line 321
            bestK_9 = k_11;

#line 321
            bestLane_9 = 11U;

#line 321
        }
        else
        {

#line 321
            bestM_8 = bestM_7;

#line 321
            bestK_9 = bestK_8;

#line 321
            bestLane_9 = bestLane_8;

#line 321
        }

#line 319
        uint m_12 = (*(&kernelContext_0)->bestM_sh_0)[12U];
        int k_12 = (*(&kernelContext_0)->bestK_sh_0)[12U];

#line 320
        bool _S92;
        if(((*(&kernelContext_0)->bestM_sh_0)[12U]) > bestM_8)
        {

#line 321
            _S91 = true;

#line 321
        }
        else
        {

#line 321
            if(m_12 == bestM_8)
            {

#line 321
                _S91 = k_12 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S91 = false;

#line 321
            }

#line 321
            if(_S91)
            {

#line 321
                if(bestK_9 < int(0))
                {

#line 321
                    _S92 = true;

#line 321
                }
                else
                {

#line 321
                    _S92 = k_12 < bestK_9;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S92 = false;

#line 321
            }

#line 321
            _S91 = _S92;

#line 321
        }

#line 321
        uint bestM_9;

#line 321
        uint bestLane_10;

#line 321
        int bestK_10;

#line 321
        if(_S91)
        {

#line 321
            bestM_9 = m_12;

#line 321
            bestK_10 = k_12;

#line 321
            bestLane_10 = 12U;

#line 321
        }
        else
        {

#line 321
            bestM_9 = bestM_8;

#line 321
            bestK_10 = bestK_9;

#line 321
            bestLane_10 = bestLane_9;

#line 321
        }

#line 319
        uint m_13 = (*(&kernelContext_0)->bestM_sh_0)[13U];
        int k_13 = (*(&kernelContext_0)->bestK_sh_0)[13U];

#line 320
        bool _S93;
        if(((*(&kernelContext_0)->bestM_sh_0)[13U]) > bestM_9)
        {

#line 321
            _S92 = true;

#line 321
        }
        else
        {

#line 321
            if(m_13 == bestM_9)
            {

#line 321
                _S92 = k_13 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S92 = false;

#line 321
            }

#line 321
            if(_S92)
            {

#line 321
                if(bestK_10 < int(0))
                {

#line 321
                    _S93 = true;

#line 321
                }
                else
                {

#line 321
                    _S93 = k_13 < bestK_10;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S93 = false;

#line 321
            }

#line 321
            _S92 = _S93;

#line 321
        }

#line 321
        uint bestM_10;

#line 321
        uint bestLane_11;

#line 321
        int bestK_11;

#line 321
        if(_S92)
        {

#line 321
            bestM_10 = m_13;

#line 321
            bestK_11 = k_13;

#line 321
            bestLane_11 = 13U;

#line 321
        }
        else
        {

#line 321
            bestM_10 = bestM_9;

#line 321
            bestK_11 = bestK_10;

#line 321
            bestLane_11 = bestLane_10;

#line 321
        }

#line 319
        uint m_14 = (*(&kernelContext_0)->bestM_sh_0)[14U];
        int k_14 = (*(&kernelContext_0)->bestK_sh_0)[14U];

#line 320
        bool _S94;
        if(((*(&kernelContext_0)->bestM_sh_0)[14U]) > bestM_10)
        {

#line 321
            _S93 = true;

#line 321
        }
        else
        {

#line 321
            if(m_14 == bestM_10)
            {

#line 321
                _S93 = k_14 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S93 = false;

#line 321
            }

#line 321
            if(_S93)
            {

#line 321
                if(bestK_11 < int(0))
                {

#line 321
                    _S94 = true;

#line 321
                }
                else
                {

#line 321
                    _S94 = k_14 < bestK_11;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S94 = false;

#line 321
            }

#line 321
            _S93 = _S94;

#line 321
        }

#line 321
        uint bestM_11;

#line 321
        uint bestLane_12;

#line 321
        int bestK_12;

#line 321
        if(_S93)
        {

#line 321
            bestM_11 = m_14;

#line 321
            bestK_12 = k_14;

#line 321
            bestLane_12 = 14U;

#line 321
        }
        else
        {

#line 321
            bestM_11 = bestM_10;

#line 321
            bestK_12 = bestK_11;

#line 321
            bestLane_12 = bestLane_11;

#line 321
        }

#line 319
        uint m_15 = (*(&kernelContext_0)->bestM_sh_0)[15U];
        int k_15 = (*(&kernelContext_0)->bestK_sh_0)[15U];

#line 320
        bool _S95;
        if(((*(&kernelContext_0)->bestM_sh_0)[15U]) > bestM_11)
        {

#line 321
            _S94 = true;

#line 321
        }
        else
        {

#line 321
            if(m_15 == bestM_11)
            {

#line 321
                _S94 = k_15 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S94 = false;

#line 321
            }

#line 321
            if(_S94)
            {

#line 321
                if(bestK_12 < int(0))
                {

#line 321
                    _S95 = true;

#line 321
                }
                else
                {

#line 321
                    _S95 = k_15 < bestK_12;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S95 = false;

#line 321
            }

#line 321
            _S94 = _S95;

#line 321
        }

#line 321
        uint bestM_12;

#line 321
        uint bestLane_13;

#line 321
        int bestK_13;

#line 321
        if(_S94)
        {

#line 321
            bestM_12 = m_15;

#line 321
            bestK_13 = k_15;

#line 321
            bestLane_13 = 15U;

#line 321
        }
        else
        {

#line 321
            bestM_12 = bestM_11;

#line 321
            bestK_13 = bestK_12;

#line 321
            bestLane_13 = bestLane_12;

#line 321
        }

#line 319
        uint m_16 = (*(&kernelContext_0)->bestM_sh_0)[16U];
        int k_16 = (*(&kernelContext_0)->bestK_sh_0)[16U];

#line 320
        bool _S96;
        if(((*(&kernelContext_0)->bestM_sh_0)[16U]) > bestM_12)
        {

#line 321
            _S95 = true;

#line 321
        }
        else
        {

#line 321
            if(m_16 == bestM_12)
            {

#line 321
                _S95 = k_16 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S95 = false;

#line 321
            }

#line 321
            if(_S95)
            {

#line 321
                if(bestK_13 < int(0))
                {

#line 321
                    _S96 = true;

#line 321
                }
                else
                {

#line 321
                    _S96 = k_16 < bestK_13;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S96 = false;

#line 321
            }

#line 321
            _S95 = _S96;

#line 321
        }

#line 321
        uint bestM_13;

#line 321
        uint bestLane_14;

#line 321
        int bestK_14;

#line 321
        if(_S95)
        {

#line 321
            bestM_13 = m_16;

#line 321
            bestK_14 = k_16;

#line 321
            bestLane_14 = 16U;

#line 321
        }
        else
        {

#line 321
            bestM_13 = bestM_12;

#line 321
            bestK_14 = bestK_13;

#line 321
            bestLane_14 = bestLane_13;

#line 321
        }

#line 319
        uint m_17 = (*(&kernelContext_0)->bestM_sh_0)[17U];
        int k_17 = (*(&kernelContext_0)->bestK_sh_0)[17U];

#line 320
        bool _S97;
        if(((*(&kernelContext_0)->bestM_sh_0)[17U]) > bestM_13)
        {

#line 321
            _S96 = true;

#line 321
        }
        else
        {

#line 321
            if(m_17 == bestM_13)
            {

#line 321
                _S96 = k_17 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S96 = false;

#line 321
            }

#line 321
            if(_S96)
            {

#line 321
                if(bestK_14 < int(0))
                {

#line 321
                    _S97 = true;

#line 321
                }
                else
                {

#line 321
                    _S97 = k_17 < bestK_14;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S97 = false;

#line 321
            }

#line 321
            _S96 = _S97;

#line 321
        }

#line 321
        uint bestM_14;

#line 321
        uint bestLane_15;

#line 321
        int bestK_15;

#line 321
        if(_S96)
        {

#line 321
            bestM_14 = m_17;

#line 321
            bestK_15 = k_17;

#line 321
            bestLane_15 = 17U;

#line 321
        }
        else
        {

#line 321
            bestM_14 = bestM_13;

#line 321
            bestK_15 = bestK_14;

#line 321
            bestLane_15 = bestLane_14;

#line 321
        }

#line 319
        uint m_18 = (*(&kernelContext_0)->bestM_sh_0)[18U];
        int k_18 = (*(&kernelContext_0)->bestK_sh_0)[18U];

#line 320
        bool _S98;
        if(((*(&kernelContext_0)->bestM_sh_0)[18U]) > bestM_14)
        {

#line 321
            _S97 = true;

#line 321
        }
        else
        {

#line 321
            if(m_18 == bestM_14)
            {

#line 321
                _S97 = k_18 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S97 = false;

#line 321
            }

#line 321
            if(_S97)
            {

#line 321
                if(bestK_15 < int(0))
                {

#line 321
                    _S98 = true;

#line 321
                }
                else
                {

#line 321
                    _S98 = k_18 < bestK_15;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S98 = false;

#line 321
            }

#line 321
            _S97 = _S98;

#line 321
        }

#line 321
        uint bestM_15;

#line 321
        uint bestLane_16;

#line 321
        int bestK_16;

#line 321
        if(_S97)
        {

#line 321
            bestM_15 = m_18;

#line 321
            bestK_16 = k_18;

#line 321
            bestLane_16 = 18U;

#line 321
        }
        else
        {

#line 321
            bestM_15 = bestM_14;

#line 321
            bestK_16 = bestK_15;

#line 321
            bestLane_16 = bestLane_15;

#line 321
        }

#line 319
        uint m_19 = (*(&kernelContext_0)->bestM_sh_0)[19U];
        int k_19 = (*(&kernelContext_0)->bestK_sh_0)[19U];

#line 320
        bool _S99;
        if(((*(&kernelContext_0)->bestM_sh_0)[19U]) > bestM_15)
        {

#line 321
            _S98 = true;

#line 321
        }
        else
        {

#line 321
            if(m_19 == bestM_15)
            {

#line 321
                _S98 = k_19 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S98 = false;

#line 321
            }

#line 321
            if(_S98)
            {

#line 321
                if(bestK_16 < int(0))
                {

#line 321
                    _S99 = true;

#line 321
                }
                else
                {

#line 321
                    _S99 = k_19 < bestK_16;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S99 = false;

#line 321
            }

#line 321
            _S98 = _S99;

#line 321
        }

#line 321
        uint bestM_16;

#line 321
        uint bestLane_17;

#line 321
        int bestK_17;

#line 321
        if(_S98)
        {

#line 321
            bestM_16 = m_19;

#line 321
            bestK_17 = k_19;

#line 321
            bestLane_17 = 19U;

#line 321
        }
        else
        {

#line 321
            bestM_16 = bestM_15;

#line 321
            bestK_17 = bestK_16;

#line 321
            bestLane_17 = bestLane_16;

#line 321
        }

#line 319
        uint m_20 = (*(&kernelContext_0)->bestM_sh_0)[20U];
        int k_20 = (*(&kernelContext_0)->bestK_sh_0)[20U];

#line 320
        bool _S100;
        if(((*(&kernelContext_0)->bestM_sh_0)[20U]) > bestM_16)
        {

#line 321
            _S99 = true;

#line 321
        }
        else
        {

#line 321
            if(m_20 == bestM_16)
            {

#line 321
                _S99 = k_20 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S99 = false;

#line 321
            }

#line 321
            if(_S99)
            {

#line 321
                if(bestK_17 < int(0))
                {

#line 321
                    _S100 = true;

#line 321
                }
                else
                {

#line 321
                    _S100 = k_20 < bestK_17;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S100 = false;

#line 321
            }

#line 321
            _S99 = _S100;

#line 321
        }

#line 321
        uint bestM_17;

#line 321
        uint bestLane_18;

#line 321
        int bestK_18;

#line 321
        if(_S99)
        {

#line 321
            bestM_17 = m_20;

#line 321
            bestK_18 = k_20;

#line 321
            bestLane_18 = 20U;

#line 321
        }
        else
        {

#line 321
            bestM_17 = bestM_16;

#line 321
            bestK_18 = bestK_17;

#line 321
            bestLane_18 = bestLane_17;

#line 321
        }

#line 319
        uint m_21 = (*(&kernelContext_0)->bestM_sh_0)[21U];
        int k_21 = (*(&kernelContext_0)->bestK_sh_0)[21U];

#line 320
        bool _S101;
        if(((*(&kernelContext_0)->bestM_sh_0)[21U]) > bestM_17)
        {

#line 321
            _S100 = true;

#line 321
        }
        else
        {

#line 321
            if(m_21 == bestM_17)
            {

#line 321
                _S100 = k_21 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S100 = false;

#line 321
            }

#line 321
            if(_S100)
            {

#line 321
                if(bestK_18 < int(0))
                {

#line 321
                    _S101 = true;

#line 321
                }
                else
                {

#line 321
                    _S101 = k_21 < bestK_18;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S101 = false;

#line 321
            }

#line 321
            _S100 = _S101;

#line 321
        }

#line 321
        uint bestM_18;

#line 321
        uint bestLane_19;

#line 321
        int bestK_19;

#line 321
        if(_S100)
        {

#line 321
            bestM_18 = m_21;

#line 321
            bestK_19 = k_21;

#line 321
            bestLane_19 = 21U;

#line 321
        }
        else
        {

#line 321
            bestM_18 = bestM_17;

#line 321
            bestK_19 = bestK_18;

#line 321
            bestLane_19 = bestLane_18;

#line 321
        }

#line 319
        uint m_22 = (*(&kernelContext_0)->bestM_sh_0)[22U];
        int k_22 = (*(&kernelContext_0)->bestK_sh_0)[22U];

#line 320
        bool _S102;
        if(((*(&kernelContext_0)->bestM_sh_0)[22U]) > bestM_18)
        {

#line 321
            _S101 = true;

#line 321
        }
        else
        {

#line 321
            if(m_22 == bestM_18)
            {

#line 321
                _S101 = k_22 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S101 = false;

#line 321
            }

#line 321
            if(_S101)
            {

#line 321
                if(bestK_19 < int(0))
                {

#line 321
                    _S102 = true;

#line 321
                }
                else
                {

#line 321
                    _S102 = k_22 < bestK_19;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S102 = false;

#line 321
            }

#line 321
            _S101 = _S102;

#line 321
        }

#line 321
        uint bestM_19;

#line 321
        uint bestLane_20;

#line 321
        int bestK_20;

#line 321
        if(_S101)
        {

#line 321
            bestM_19 = m_22;

#line 321
            bestK_20 = k_22;

#line 321
            bestLane_20 = 22U;

#line 321
        }
        else
        {

#line 321
            bestM_19 = bestM_18;

#line 321
            bestK_20 = bestK_19;

#line 321
            bestLane_20 = bestLane_19;

#line 321
        }

#line 319
        uint m_23 = (*(&kernelContext_0)->bestM_sh_0)[23U];
        int k_23 = (*(&kernelContext_0)->bestK_sh_0)[23U];

#line 320
        bool _S103;
        if(((*(&kernelContext_0)->bestM_sh_0)[23U]) > bestM_19)
        {

#line 321
            _S102 = true;

#line 321
        }
        else
        {

#line 321
            if(m_23 == bestM_19)
            {

#line 321
                _S102 = k_23 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S102 = false;

#line 321
            }

#line 321
            if(_S102)
            {

#line 321
                if(bestK_20 < int(0))
                {

#line 321
                    _S103 = true;

#line 321
                }
                else
                {

#line 321
                    _S103 = k_23 < bestK_20;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S103 = false;

#line 321
            }

#line 321
            _S102 = _S103;

#line 321
        }

#line 321
        uint bestM_20;

#line 321
        uint bestLane_21;

#line 321
        int bestK_21;

#line 321
        if(_S102)
        {

#line 321
            bestM_20 = m_23;

#line 321
            bestK_21 = k_23;

#line 321
            bestLane_21 = 23U;

#line 321
        }
        else
        {

#line 321
            bestM_20 = bestM_19;

#line 321
            bestK_21 = bestK_20;

#line 321
            bestLane_21 = bestLane_20;

#line 321
        }

#line 319
        uint m_24 = (*(&kernelContext_0)->bestM_sh_0)[24U];
        int k_24 = (*(&kernelContext_0)->bestK_sh_0)[24U];

#line 320
        bool _S104;
        if(((*(&kernelContext_0)->bestM_sh_0)[24U]) > bestM_20)
        {

#line 321
            _S103 = true;

#line 321
        }
        else
        {

#line 321
            if(m_24 == bestM_20)
            {

#line 321
                _S103 = k_24 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S103 = false;

#line 321
            }

#line 321
            if(_S103)
            {

#line 321
                if(bestK_21 < int(0))
                {

#line 321
                    _S104 = true;

#line 321
                }
                else
                {

#line 321
                    _S104 = k_24 < bestK_21;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S104 = false;

#line 321
            }

#line 321
            _S103 = _S104;

#line 321
        }

#line 321
        uint bestM_21;

#line 321
        uint bestLane_22;

#line 321
        int bestK_22;

#line 321
        if(_S103)
        {

#line 321
            bestM_21 = m_24;

#line 321
            bestK_22 = k_24;

#line 321
            bestLane_22 = 24U;

#line 321
        }
        else
        {

#line 321
            bestM_21 = bestM_20;

#line 321
            bestK_22 = bestK_21;

#line 321
            bestLane_22 = bestLane_21;

#line 321
        }

#line 319
        uint m_25 = (*(&kernelContext_0)->bestM_sh_0)[25U];
        int k_25 = (*(&kernelContext_0)->bestK_sh_0)[25U];

#line 320
        bool _S105;
        if(((*(&kernelContext_0)->bestM_sh_0)[25U]) > bestM_21)
        {

#line 321
            _S104 = true;

#line 321
        }
        else
        {

#line 321
            if(m_25 == bestM_21)
            {

#line 321
                _S104 = k_25 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S104 = false;

#line 321
            }

#line 321
            if(_S104)
            {

#line 321
                if(bestK_22 < int(0))
                {

#line 321
                    _S105 = true;

#line 321
                }
                else
                {

#line 321
                    _S105 = k_25 < bestK_22;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S105 = false;

#line 321
            }

#line 321
            _S104 = _S105;

#line 321
        }

#line 321
        uint bestM_22;

#line 321
        uint bestLane_23;

#line 321
        int bestK_23;

#line 321
        if(_S104)
        {

#line 321
            bestM_22 = m_25;

#line 321
            bestK_23 = k_25;

#line 321
            bestLane_23 = 25U;

#line 321
        }
        else
        {

#line 321
            bestM_22 = bestM_21;

#line 321
            bestK_23 = bestK_22;

#line 321
            bestLane_23 = bestLane_22;

#line 321
        }

#line 319
        uint m_26 = (*(&kernelContext_0)->bestM_sh_0)[26U];
        int k_26 = (*(&kernelContext_0)->bestK_sh_0)[26U];

#line 320
        bool _S106;
        if(((*(&kernelContext_0)->bestM_sh_0)[26U]) > bestM_22)
        {

#line 321
            _S105 = true;

#line 321
        }
        else
        {

#line 321
            if(m_26 == bestM_22)
            {

#line 321
                _S105 = k_26 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S105 = false;

#line 321
            }

#line 321
            if(_S105)
            {

#line 321
                if(bestK_23 < int(0))
                {

#line 321
                    _S106 = true;

#line 321
                }
                else
                {

#line 321
                    _S106 = k_26 < bestK_23;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S106 = false;

#line 321
            }

#line 321
            _S105 = _S106;

#line 321
        }

#line 321
        uint bestM_23;

#line 321
        uint bestLane_24;

#line 321
        int bestK_24;

#line 321
        if(_S105)
        {

#line 321
            bestM_23 = m_26;

#line 321
            bestK_24 = k_26;

#line 321
            bestLane_24 = 26U;

#line 321
        }
        else
        {

#line 321
            bestM_23 = bestM_22;

#line 321
            bestK_24 = bestK_23;

#line 321
            bestLane_24 = bestLane_23;

#line 321
        }

#line 319
        uint m_27 = (*(&kernelContext_0)->bestM_sh_0)[27U];
        int k_27 = (*(&kernelContext_0)->bestK_sh_0)[27U];

#line 320
        bool _S107;
        if(((*(&kernelContext_0)->bestM_sh_0)[27U]) > bestM_23)
        {

#line 321
            _S106 = true;

#line 321
        }
        else
        {

#line 321
            if(m_27 == bestM_23)
            {

#line 321
                _S106 = k_27 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S106 = false;

#line 321
            }

#line 321
            if(_S106)
            {

#line 321
                if(bestK_24 < int(0))
                {

#line 321
                    _S107 = true;

#line 321
                }
                else
                {

#line 321
                    _S107 = k_27 < bestK_24;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S107 = false;

#line 321
            }

#line 321
            _S106 = _S107;

#line 321
        }

#line 321
        uint bestM_24;

#line 321
        uint bestLane_25;

#line 321
        int bestK_25;

#line 321
        if(_S106)
        {

#line 321
            bestM_24 = m_27;

#line 321
            bestK_25 = k_27;

#line 321
            bestLane_25 = 27U;

#line 321
        }
        else
        {

#line 321
            bestM_24 = bestM_23;

#line 321
            bestK_25 = bestK_24;

#line 321
            bestLane_25 = bestLane_24;

#line 321
        }

#line 319
        uint m_28 = (*(&kernelContext_0)->bestM_sh_0)[28U];
        int k_28 = (*(&kernelContext_0)->bestK_sh_0)[28U];

#line 320
        bool _S108;
        if(((*(&kernelContext_0)->bestM_sh_0)[28U]) > bestM_24)
        {

#line 321
            _S107 = true;

#line 321
        }
        else
        {

#line 321
            if(m_28 == bestM_24)
            {

#line 321
                _S107 = k_28 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S107 = false;

#line 321
            }

#line 321
            if(_S107)
            {

#line 321
                if(bestK_25 < int(0))
                {

#line 321
                    _S108 = true;

#line 321
                }
                else
                {

#line 321
                    _S108 = k_28 < bestK_25;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S108 = false;

#line 321
            }

#line 321
            _S107 = _S108;

#line 321
        }

#line 321
        uint bestM_25;

#line 321
        uint bestLane_26;

#line 321
        int bestK_26;

#line 321
        if(_S107)
        {

#line 321
            bestM_25 = m_28;

#line 321
            bestK_26 = k_28;

#line 321
            bestLane_26 = 28U;

#line 321
        }
        else
        {

#line 321
            bestM_25 = bestM_24;

#line 321
            bestK_26 = bestK_25;

#line 321
            bestLane_26 = bestLane_25;

#line 321
        }

#line 319
        uint m_29 = (*(&kernelContext_0)->bestM_sh_0)[29U];
        int k_29 = (*(&kernelContext_0)->bestK_sh_0)[29U];

#line 320
        bool _S109;
        if(((*(&kernelContext_0)->bestM_sh_0)[29U]) > bestM_25)
        {

#line 321
            _S108 = true;

#line 321
        }
        else
        {

#line 321
            if(m_29 == bestM_25)
            {

#line 321
                _S108 = k_29 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S108 = false;

#line 321
            }

#line 321
            if(_S108)
            {

#line 321
                if(bestK_26 < int(0))
                {

#line 321
                    _S109 = true;

#line 321
                }
                else
                {

#line 321
                    _S109 = k_29 < bestK_26;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S109 = false;

#line 321
            }

#line 321
            _S108 = _S109;

#line 321
        }

#line 321
        uint bestM_26;

#line 321
        uint bestLane_27;

#line 321
        int bestK_27;

#line 321
        if(_S108)
        {

#line 321
            bestM_26 = m_29;

#line 321
            bestK_27 = k_29;

#line 321
            bestLane_27 = 29U;

#line 321
        }
        else
        {

#line 321
            bestM_26 = bestM_25;

#line 321
            bestK_27 = bestK_26;

#line 321
            bestLane_27 = bestLane_26;

#line 321
        }

#line 319
        uint m_30 = (*(&kernelContext_0)->bestM_sh_0)[30U];
        int k_30 = (*(&kernelContext_0)->bestK_sh_0)[30U];

#line 320
        bool _S110;
        if(((*(&kernelContext_0)->bestM_sh_0)[30U]) > bestM_26)
        {

#line 321
            _S109 = true;

#line 321
        }
        else
        {

#line 321
            if(m_30 == bestM_26)
            {

#line 321
                _S109 = k_30 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S109 = false;

#line 321
            }

#line 321
            if(_S109)
            {

#line 321
                if(bestK_27 < int(0))
                {

#line 321
                    _S110 = true;

#line 321
                }
                else
                {

#line 321
                    _S110 = k_30 < bestK_27;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                _S110 = false;

#line 321
            }

#line 321
            _S109 = _S110;

#line 321
        }

#line 321
        uint bestM_27;

#line 321
        uint bestLane_28;

#line 321
        int bestK_28;

#line 321
        if(_S109)
        {

#line 321
            bestM_27 = m_30;

#line 321
            bestK_28 = k_30;

#line 321
            bestLane_28 = 30U;

#line 321
        }
        else
        {

#line 321
            bestM_27 = bestM_26;

#line 321
            bestK_28 = bestK_27;

#line 321
            bestLane_28 = bestLane_27;

#line 321
        }

#line 319
        uint m_31 = (*(&kernelContext_0)->bestM_sh_0)[31U];
        int k_31 = (*(&kernelContext_0)->bestK_sh_0)[31U];

#line 320
        bool edgeFallback_0;
        if(((*(&kernelContext_0)->bestM_sh_0)[31U]) > bestM_27)
        {

#line 321
            _S110 = true;

#line 321
        }
        else
        {

#line 321
            if(m_31 == bestM_27)
            {

#line 321
                _S110 = k_31 >= int(0);

#line 321
            }
            else
            {

#line 321
                _S110 = false;

#line 321
            }

#line 321
            if(_S110)
            {

#line 321
                if(bestK_28 < int(0))
                {

#line 321
                    edgeFallback_0 = true;

#line 321
                }
                else
                {

#line 321
                    edgeFallback_0 = k_31 < bestK_28;

#line 321
                }

#line 321
            }
            else
            {

#line 321
                edgeFallback_0 = false;

#line 321
            }

#line 321
            _S110 = edgeFallback_0;

#line 321
        }

#line 321
        uint bestLane_29;

#line 321
        int bestK_29;

#line 321
        if(_S110)
        {

#line 321
            bestK_29 = k_31;

#line 321
            bestLane_29 = 31U;

#line 321
        }
        else
        {

#line 321
            bestK_29 = bestK_28;

#line 321
            bestLane_29 = bestLane_28;

#line 321
        }

#line 330
        bool _S111 = bestK_29 >= int(0);

#line 330
        bool _S112;
        if(_S111)
        {

#line 331
            if(bestK_29 == _S24)
            {

#line 331
                edgeFallback_0 = _S24 > _S22;

#line 331
            }
            else
            {

#line 331
                edgeFallback_0 = false;

#line 331
            }

#line 331
            if(edgeFallback_0)
            {

#line 331
                _S112 = true;

#line 331
            }
            else
            {

#line 331
                if(bestK_29 == (_S26 - int(1)))
                {

#line 331
                    _S112 = _S26 < _S25;

#line 331
                }
                else
                {

#line 331
                    _S112 = false;

#line 331
                }

#line 331
            }

#line 331
            edgeFallback_0 = _S112;

#line 331
        }
        else
        {

#line 331
            edgeFallback_0 = false;

#line 331
        }
        if(edgeFallback_0)
        {

#line 333
            if(_S6 == 0U)
            {
                uint slot_3 = atomic_fetch_add_explicit(((atomic_uint device*)((&kernelContext_0)->entryPointParams_fbArgs_0+int(0))), 1U, memory_order_relaxed);
                *((&kernelContext_0)->entryPointParams_fbSurv_0+slot_3) = pair_0;

#line 333
            }

#line 332
        }
        else
        {

#line 339
            float2 _S113 = (*(&kernelContext_0)->bestV_sh_0)[bestLane_29];
            uint _S114 = pair_0 * (&kernelContext_0)->entryPointParams_0->nbins_0;

#line 340
            bin_0 = _S6;
            for(;;)
            {

#line 341
                if(bin_0 < ((&kernelContext_0)->entryPointParams_0->nbins_0))
                {
                }
                else
                {

#line 341
                    break;
                }

#line 342
                if(bin_0 == jb_0)
                {

#line 342
                    _S112 = _S111;

#line 342
                }
                else
                {

#line 342
                    _S112 = false;

#line 342
                }

#line 342
                if(_S112)
                {

#line 343
                    uint _S115 = _S114 + bin_0;

#line 343
                    *((&kernelContext_0)->entryPointParams_peakIdx_0+_S115) = bestK_29;

#line 343
                    *((&kernelContext_0)->entryPointParams_peakVal_0+_S115) = packed_float2(_S113) ;

#line 342
                }
                else
                {

                    uint _S116 = _S114 + bin_0;

#line 346
                    *((&kernelContext_0)->entryPointParams_peakIdx_0+_S116) = int(-1);

#line 346
                    *((&kernelContext_0)->entryPointParams_peakVal_0+_S116) = packed_float2(_S42) ;

#line 342
                }

#line 341
                bin_0 = bin_0 + 32U;

#line 341
            }

#line 332
        }

#line 351
        if((item_0 + (&kernelContext_0)->entryPointParams_0->gridSize_0) < _S7)
        {

#line 352
            threadgroup_barrier(mem_flags::mem_threadgroup);

#line 351
        }

#line 137
        item_0 = item_0 + (&kernelContext_0)->entryPointParams_0->gridSize_0;

#line 137
    }

#line 354
    return;
}
