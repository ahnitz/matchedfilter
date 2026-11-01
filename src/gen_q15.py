"""Generate the Q15 (int16 fixed-point) split-radix codelets in codelets-q15-inl.h.

Same split-radix DAGs as gen.py, evaluated in conjugated (+2*pi*i) form on a vector of
int16 lanes (`vq`, twice the float lane count at a given vector width): computing
conj(Z_k) = sum_j (d_j * t_j) exp(+2*pi*i * j*k / N) preserves every lag index k and
magnitude |Z_k|^2 while forming d_j * t_j directly from (dr, di) without a negated -di
data stream.  The arithmetic is exact integer add/subtract plus Q15 rounding multiplies
(Q_MUL = round(a*b / 2^15), vpmulhrsw on x86) and multiply-accumulates (Q_MLAH/Q_MLSH =
acc +- round(a*b / 2^15), one SQRDMLAH/SQRDMLSH on AArch64, Q_ADD/Q_SUB(acc, Q_MUL)
elsewhere; every rounding is to nearest, within 1/2 LSB), and nothing in a codelet
rescales: the caller sizes its inputs so that every intermediate stays in range (see
q15-inl.h for the bound).  Twiddle constants are |cos|, |sin| rounded to Q15 and the
signs ride on the adds, as gen.py does for the float FMAs.

    python src/gen_q15.py          # rewrites src/codelets-q15-inl.h
"""
import os
import re

from gen import SRGen, fold_negations, trivial, wconst


def q15(v):
    return max(-32767, min(32767, int(round(v * 32768.0))))


class QScheduleMixin:
    """Register-conscious split-radix schedule: evaluate U(n/2) first while 0 outer vectors are
    live (so n=8 fits in 16 registers and n=16 fits in 32 registers), then Zc(n/4) and Zp(n/4),
    deferring both twiddle multiplies into the combination loop so n-level twiddle constants
    never overlap Zp's subtree and draining subproblem outputs in LIFO order.  On 16-register
    x86 targets (SSE4, AVX1, AVX2) at n = 32 (stream_z32=True), U(16)'s 32 vectors already
    exceed 16 registers, so streaming Zc(8) -> t1 and Zp(8) -> (su, pdf) first (32 outer vectors
    instead of 48) and streaming U(16) directly into the root sink cuts ~50-90 stack spills; on
    32-register targets (AVX-512, AArch64 NEON), keeping U(16) first lets Zc(8) and Zp(8) run
    spill-free in the 32-register file.  At the root (sink_fn != None), emit each store or
    window-maximum reduction immediately (loading M0, M1 lazily on the first output)."""

    stream_z32 = False

    def twmul(s, a, k, n):
        c, sn = wconst(k, n)
        o = ("t%d_r" % s.nc, "t%d_i" % s.nc)
        s.nc += 1
        s.cmul(a[0], a[1], c, -sn, o)
        return o

    def rec(s, idxs, sink_fn=None):
        n = len(idxs)
        if n == 1:
            v = s.load(idxs[0])
            if sink_fn is not None:
                sink_fn(0, v)
                return None
            return [v]
        if n == 2:
            a = s.load(idxs[0])
            b = s.load(idxs[1])
            out = [s.add(a, b), s.sub(a, b)]
            if sink_fn is not None:
                sink_fn(0, out[0])
                sink_fn(1, out[1])
                return None
            return out
        q = n // 4
        if n >= 32 and sink_fn is not None and s.stream_z32:
            t1 = [None] * q

            def zc_sink(k, zc_val):
                t1[k] = s.twmul(zc_val, k, n)

            s.rec(idxs[1::4], sink_fn=zc_sink)
            su = [None] * q
            pdf = [None] * q

            def zp_sink(k, zp_val):
                t2 = s.twmul(zp_val, 3 * k, n)
                su[k] = s.add(t1[k], t2)
                pdf[k] = s.pi_(s.sub(t1[k], t2))

            s.rec(idxs[3::4], sink_fn=zp_sink)

            def u_sink(uk_idx, uk_val):
                if uk_idx < q:
                    sink_fn(uk_idx, s.add(uk_val, su[uk_idx]))
                    sink_fn(uk_idx + 2 * q, s.sub(uk_val, su[uk_idx]))
                else:
                    k = uk_idx - q
                    sink_fn(k + q, s.add(uk_val, pdf[k]))
                    sink_fn(k + 3 * q, s.sub(uk_val, pdf[k]))

            s.rec(idxs[0::2], sink_fn=u_sink)
            return None
        U = s.rec(idxs[0::2])
        Zc = s.rec(idxs[1::4])
        Zp = s.rec(idxs[3::4])
        if sink_fn is not None:
            for k in range(q):
                t1 = s.twmul(Zc[k], k, n)
                t2 = s.twmul(Zp[k], 3 * k, n)
                su = s.add(t1, t2)
                pdf = s.pi_(s.sub(t1, t2))
                sink_fn(k, s.add(U[k], su))
                sink_fn(k + 2 * q, s.sub(U[k], su))
                sink_fn(k + q, s.add(U[k + q], pdf))
                sink_fn(k + 3 * q, s.sub(U[k + q], pdf))
            return None
        X = [None] * n
        for k in reversed(range(q)):
            t1 = s.twmul(Zc[k], k, n)
            t2 = s.twmul(Zp[k], 3 * k, n)
            su = s.add(t1, t2)
            pdf = s.pi_(s.sub(t1, t2))
            X[k] = s.add(U[k], su)
            X[k + 2 * q] = s.sub(U[k], su)
            X[k + q] = s.add(U[k + q], pdf)
            X[k + 3 * q] = s.sub(U[k + q], pdf)
        return X


def _emit_eighth_turn(s, ar, ai, c, sn, out):
    """Eighth-turn (|c| == |sn| = 23170): two Q_MULs instead of four, bit-identical."""
    orr, oii = out
    cc = s.const("c", abs(c))
    k = s.nc
    s.nc += 1
    u, v = "m%d_0" % k, "m%d_1" % k
    s.emit("vf %s=Q_MUL(%s,%s), %s=Q_MUL(%s,%s);" % (u, ar, cc, v, ai, cc))
    sc = 1 if c >= 0 else -1
    sg = 1 if sn >= 0 else -1
    if (sc, sg) == (1, 1):
        s.emit("vf %s=V_SUB(%s,%s), %s=V_ADD(%s,%s);" % (orr, u, v, oii, u, v))
    elif (sc, sg) == (1, -1):
        s.emit("vf %s=V_ADD(%s,%s), %s=V_SUB(%s,%s);" % (orr, u, v, oii, v, u))
    elif (sc, sg) == (-1, 1):
        s.emit("vf n%s=V_ADD(%s,%s);" % (orr, u, v))
        s.emit("vf %s=V_SUB(Z,n%s), %s=V_SUB(%s,%s);" % (orr, orr, oii, u, v))
    else:
        s.emit("vf n%s=V_ADD(%s,%s);" % (oii, u, v))
        s.emit("vf %s=V_SUB(%s,%s), %s=V_SUB(Z,n%s);" % (orr, v, u, oii, oii))


class QGen(QScheduleMixin, SRGen):
    def const(s, c, v):
        key = "%d" % q15(v)
        if key not in s.consts:
            s.consts[key] = "c%d" % len(s.consts)
        return s.consts[key]

    def cmul(s, ar, ai, c, sn, out):
        t = trivial(c, sn)
        orr, oii = out
        if t == "1":
            s.emit("vf %s=%s, %s=%s;" % (orr, ar, oii, ai)); return
        if t == "-1":
            s.emit("vf %s=V_SUB(Z,%s), %s=V_SUB(Z,%s);" % (orr, ar, oii, ai)); return
        if t == "-i":
            s.emit("vf %s=%s, %s=V_SUB(Z,%s);" % (orr, ai, oii, ar)); return
        if t == "+i":
            s.emit("vf %s=V_SUB(Z,%s), %s=%s;" % (orr, ai, oii, ar)); return
        if q15(abs(c)) == q15(abs(sn)):
            _emit_eighth_turn(s, ar, ai, c, sn, out); return
        cc = s.const("c", abs(c)); ss = s.const("s", abs(sn))
        sc = 1 if c >= 0 else -1
        sg = 1 if sn >= 0 else -1
        if (sc, sg) == (1, 1):
            s.emit("vf %s=Q_MLSH(Q_MUL(%s,%s),%s,%s);" % (orr, ar, cc, ai, ss))
        elif (sc, sg) == (1, -1):
            s.emit("vf %s=Q_MLAH(Q_MUL(%s,%s),%s,%s);" % (orr, ar, cc, ai, ss))
        elif (sc, sg) == (-1, -1):
            s.emit("vf %s=Q_MLSH(Q_MUL(%s,%s),%s,%s);" % (orr, ai, ss, ar, cc))
        else:
            s.emit("vf n%s=Q_MLAH(Q_MUL(%s,%s),%s,%s);" % (orr, ar, cc, ai, ss))
            s.emit("vf %s=V_SUB(Z,n%s);" % (orr, orr))
        if (sg, sc) == (1, 1):
            s.emit("vf %s=Q_MLAH(Q_MUL(%s,%s),%s,%s);" % (oii, ar, ss, ai, cc))
        elif (sg, sc) == (1, -1):
            s.emit("vf %s=Q_MLSH(Q_MUL(%s,%s),%s,%s);" % (oii, ar, ss, ai, cc))
        elif (sg, sc) == (-1, 1):
            s.emit("vf %s=Q_MLSH(Q_MUL(%s,%s),%s,%s);" % (oii, ai, cc, ar, ss))
        else:
            s.emit("vf n%s=Q_MLAH(Q_MUL(%s,%s),%s,%s);" % (oii, ar, ss, ai, cc))
            s.emit("vf %s=V_SUB(Z,n%s);" % (oii, oii))

    def load(s, idx):
        o = ("q%d_r" % idx, "q%d_i" % idx)
        if s.prod:
            # d * t = (dr*tr - di*ti) + i*(dr*ti + di*tr) for the +2*pi*i transform.
            s.emit("vf tR%d=Q_LOADU(tr+TS*%d), tI%d=Q_LOADU(ti+TS*%d);" % (idx, idx, idx, idx))
            s.emit("vf dR%d=Q_DUP32(dr[DS*%d]), dI%d=Q_SET1(di[DS*%d]);" % (idx, idx, idx, idx))
            s.emit("vf %s=Q_MLSH(Q_MUL(dR%d,tR%d),dI%d,tI%d);" % (o[0], idx, idx, idx, idx))
            s.emit("vf %s=Q_MLAH(Q_MUL(dR%d,tI%d),dI%d,tR%d);" % (o[1], idx, idx, idx, idx))
            return o
        if s.tw and idx != 0:
            # ap_q15_tw_tab holds W = exp(-2*pi*i*e1*k2/N); conj(W) = Wr - i*Wi.
            s.emit("const vf W%dr=Q_TWLOAD(twr[%d]), W%di=Q_TWLOAD(twi[%d]);" % (idx, idx, idx, idx))
            s.emit("vf %s=Q_MLAH(Q_MUL(ar[S*%d],W%dr),ai[S*%d],W%di);" % (o[0], idx, idx, idx, idx))
            s.emit("vf %s=Q_MLSH(Q_MUL(ai[S*%d],W%dr),ar[S*%d],W%di);" % (o[1], idx, idx, idx, idx))
            return o
        s.emit("vf %s=ar[S*%d], %s=ai[S*%d];" % (o[0], idx, o[1], idx))
        return o


class QGenClassic(QScheduleMixin, SRGen):
    """The separate-multiply form (Q_ADD/Q_SUB of Q_MULs), emitted for targets without
    a single-instruction rounding multiply-accumulate."""
    def const(s, c, v):
        key = "%d" % q15(v)
        if key not in s.consts:
            s.consts[key] = "c%d" % len(s.consts)
        return s.consts[key]

    def cmul(s, ar, ai, c, sn, out):
        t = trivial(c, sn)
        orr, oii = out
        if t == "1":
            s.emit("vf %s=%s, %s=%s;" % (orr, ar, oii, ai)); return
        if t == "-1":
            s.emit("vf %s=V_SUB(Z,%s), %s=V_SUB(Z,%s);" % (orr, ar, oii, ai)); return
        if t == "-i":
            s.emit("vf %s=%s, %s=V_SUB(Z,%s);" % (orr, ai, oii, ar)); return
        if t == "+i":
            s.emit("vf %s=V_SUB(Z,%s), %s=%s;" % (orr, ai, oii, ar)); return
        if q15(abs(c)) == q15(abs(sn)):
            _emit_eighth_turn(s, ar, ai, c, sn, out); return
        cc = s.const("c", abs(c)); ss = s.const("s", abs(sn))
        k = s.nc; s.nc += 1
        x1, x2, y1, y2 = ("m%d_%d" % (k, j) for j in range(4))
        s.emit("vf %s=Q_MUL(%s,%s), %s=Q_MUL(%s,%s);" % (x1, ar, cc, x2, ai, ss))
        s.emit("vf %s=Q_MUL(%s,%s), %s=Q_MUL(%s,%s);" % (y1, ar, ss, y2, ai, cc))
        sc = 1 if c >= 0 else -1
        sg = 1 if sn >= 0 else -1
        if (sc, sg) == (1, 1):
            s.emit("vf %s=V_SUB(%s,%s);" % (orr, x1, x2))
        elif (sc, sg) == (1, -1):
            s.emit("vf %s=V_ADD(%s,%s);" % (orr, x1, x2))
        elif (sc, sg) == (-1, -1):
            s.emit("vf %s=V_SUB(%s,%s);" % (orr, x2, x1))
        else:
            s.emit("vf n%s=V_ADD(%s,%s);" % (orr, x1, x2))
            s.emit("vf %s=V_SUB(Z,n%s);" % (orr, orr))
        if (sg, sc) == (1, 1):
            s.emit("vf %s=V_ADD(%s,%s);" % (oii, y1, y2))
        elif (sg, sc) == (1, -1):
            s.emit("vf %s=V_SUB(%s,%s);" % (oii, y1, y2))
        elif (sg, sc) == (-1, 1):
            s.emit("vf %s=V_SUB(%s,%s);" % (oii, y2, y1))
        else:
            s.emit("vf n%s=V_ADD(%s,%s);" % (oii, y1, y2))
            s.emit("vf %s=V_SUB(Z,n%s);" % (oii, oii))

    def load(s, idx):
        o = ("q%d_r" % idx, "q%d_i" % idx)
        if s.prod:
            s.emit("vf tR%d=Q_LOADU(tr+TS*%d), tI%d=Q_LOADU(ti+TS*%d);" % (idx, idx, idx, idx))
            s.emit("vf dR%d=Q_DUP32(dr[DS*%d]), dI%d=Q_SET1(di[DS*%d]);" % (idx, idx, idx, idx))
            s.emit("vf %s=V_SUB(Q_MUL(dR%d,tR%d),Q_MUL(dI%d,tI%d));" % (o[0], idx, idx, idx, idx))
            s.emit("vf %s=V_ADD(Q_MUL(dR%d,tI%d),Q_MUL(dI%d,tR%d));" % (o[1], idx, idx, idx, idx))
            return o
        if s.tw and idx != 0:
            s.emit("const vf W%dr=Q_TWLOAD(twr[%d]), W%di=Q_TWLOAD(twi[%d]);" % (idx, idx, idx, idx))
            s.emit("vf %s=V_ADD(Q_MUL(ar[S*%d],W%dr),Q_MUL(ai[S*%d],W%di));" % (o[0], idx, idx, idx, idx))
            s.emit("vf %s=V_SUB(Q_MUL(ai[S*%d],W%dr),Q_MUL(ar[S*%d],W%di));" % (o[1], idx, idx, idx, idx))
            return o
        s.emit("vf %s=ar[S*%d], %s=ai[S*%d];" % (o[0], idx, o[1], idx))
        return o


def build_q(n, name, tw=False, prod=False, fused=True, maxout=False, max_interior=None, tile=False,
            perm=False, stream_z32=False):
    """maxout: instead of storing the n outputs, accumulate max(|z|^2) of those with index
    in [lo, hi) into mx[0] and mx[1] -- the screen's window maximum fused into its last pass,
    so the outputs never go back to memory.  Same Q_MUL squares as the separate maximum loop:
    bit-identical maxima.  max_interior=(a,b) additionally requires lo <= a and hi >= b,
    removing the output tests inside that interval.
    perm: each lane's product operands are looked up in vectors of the element across blocks and
    across templates instead of broadcast from one block: data from dr/di ([element][block],
    the templates' layout and stride) through Q_DLOAD, templates from two template groups
    (the second TW further) through Q_TLOAD, with index vectors dix/tix (q15-inl.h)."""
    g = (QGen if fused else QGenClassic)(n, name, tw, False, prod)
    g.stream_z32 = stream_z32
    acc_toggle = [0]
    first_sink = [True]

    def emit_sink(k, xk):
        if maxout:
            if first_sink[0]:
                first_sink[0] = False
                g.emit("vf M0=mx[0], M1=mx[1];")
            acc = acc_toggle[0]
            acc_toggle[0] ^= 1
            condition = "" if max_interior and max_interior[0] <= k < max_interior[1] else (
                "if(%d>=lo && %d<hi) " % (k, k))
            g.emit(condition + "M%d=Q_MAX(M%d,Q_ADDS(Q_MUL(%s,%s),Q_MUL(%s,%s)));"
                   % (acc, acc, xk[0], xk[0], xk[1], xk[1]))
        else:
            g.emit("ar[S*%d]=%s; ai[S*%d]=%s;" % (k, xk[0], k, xk[1]))

    g.rec(list(range(n)), sink_fn=emit_sink)
    if maxout:
        g.emit("mx[0]=M0; mx[1]=M1;")
    body = fold_negations("\n".join(g.L))
    body = re.sub(r"\bvf\b", "vq", body)
    body = body.replace("V_ADD(", "Q_ADD(").replace("V_SUB(", "Q_SUB(")
    if tile:
        body = re.sub(r"Q_LOADU\((t[ri]\+TS\*\d+)\)", r"q15_tile_template<T>(\1)", body)
        body = re.sub(r"Q_DUP32\(dr\[(DS\*\d+)\]\)", r"q15_tile_data32<T, B>(dr+\1)", body)
        body = re.sub(r"Q_SET1\(di\[(DS\*\d+)\]\)", r"q15_tile_data16<T, B>(di+\1)", body)
    if perm:
        body = re.sub(r"Q_DUP32\(dr\[DS\*(\d+)\]\)", r"Q_DLOAD(dr+TS*\1)", body)
        body = re.sub(r"Q_SET1\(di\[DS\*(\d+)\]\)", r"Q_DLOAD(di+TS*\1)", body)
        body = re.sub(r"Q_LOADU\((t[ri]\+TS\*\d+)\)", r"Q_TLOAD(\1)", body)
        assert "dr[" not in body and "di[" not in body and "Q_LOADU(t" not in body
    cdefs = "\n".join("  const vq %s=Q_SET1(%s);" % (v, k) for k, v in g.consts.items())
    if prod and perm:
        args = ("const int16_t*restrict dr,const int16_t*restrict di,const int16_t*restrict tr,"
                "const int16_t*restrict ti,vq*restrict ar,vq*restrict ai,const long S,const long TS,"
                "const long TW,const qidx dix,const qidx tix")
    elif prod:
        args = ("const int32_t*restrict dr,const int16_t*restrict di,const int16_t*restrict tr,"
                "const int16_t*restrict ti,vq*restrict ar,vq*restrict ai,const long S,const long DS,"
                "const long TS")
    elif tw and maxout:
        args = ("const vq*restrict ar,const vq*restrict ai,const long S,"
                "const qtw_elem*restrict twr,const qtw_elem*restrict twi,"
                "const long lo,const long hi,vq*restrict mx")
    elif maxout:
        args = ("const vq*restrict ar,const vq*restrict ai,const long S,"
                "const long lo,const long hi,vq*restrict mx")
    elif tw:
        args = ("vq*restrict ar,vq*restrict ai,const long S,"
                "const qtw_elem*restrict twr,const qtw_elem*restrict twi")
    else:
        args = "vq*restrict ar,vq*restrict ai,const long S"
    zero = "  const vq Z=Q_ZERO();\n" if re.search(r"\bZ\b", body) else ""
    prefix = "template<int T, long B>\n" if tile else ""
    return prefix + ("static HWY_INLINE void %s(%s){\n%s%s\n%s\n}\n" % (name, args, zero, cdefs, body))


def _emit_32(out, fused, stream_z32):
    out.append(build_q(32, "qsr32", fused=fused, stream_z32=stream_z32))
    out.append(build_q(32, "qsr32_prod", prod=True, fused=fused, stream_z32=stream_z32))
    out.append(build_q(32, "qsr32_prod_perm", prod=True, fused=fused, perm=True, stream_z32=stream_z32))
    out.append(build_q(32, "qsr32_tw", tw=True, fused=fused, stream_z32=stream_z32))
    out.append(build_q(32, "qsr32_twmax", tw=True, fused=fused, maxout=True, stream_z32=stream_z32))
    out.append(build_q(32, "qsr32_twmax_middle", tw=True, fused=fused,
                       maxout=True, max_interior=(4, 28), stream_z32=stream_z32))
    out.append(build_q(32, "qsr32_twmax_wide", tw=True, fused=fused,
                       maxout=True, max_interior=(8, 24), stream_z32=stream_z32))


def _emit_family(out, fused):
    for nn in (8, 16):
        out.append(build_q(nn, "qsr%d" % nn, fused=fused))
        out.append(build_q(nn, "qsr%d_prod" % nn, prod=True, fused=fused))
        out.append(build_q(nn, "qsr%d_prod_perm" % nn, prod=True, fused=fused, perm=True))
        out.append(build_q(nn, "qsr%d_tw" % nn, tw=True, fused=fused))
        out.append(build_q(nn, "qsr%d_twmax" % nn, tw=True, fused=fused, maxout=True))
        if nn == 8:
            out.append(build_q(nn, "qsr8_twmax_middle", tw=True, fused=fused,
                               maxout=True, max_interior=(2, 6)))
        if nn == 16:
            out.append(build_q(nn, "qsr16_twmax_middle", tw=True, fused=fused,
                               maxout=True, max_interior=(2, 14)))
            out.append(build_q(nn, "qsr16_twmax_wide", tw=True, fused=fused,
                               maxout=True, max_interior=(4, 12)))
    if fused:
        _emit_32(out, fused=True, stream_z32=False)
    else:
        out.append("#if defined(AP_SIMD_AVX1) || (defined(HWY_ARCH_X86) && HWY_ARCH_X86 && (!defined(HWY_MAX_BYTES) || HWY_MAX_BYTES < 64))")
        _emit_32(out, fused=False, stream_z32=True)
        out.append("#else")
        _emit_32(out, fused=False, stream_z32=False)
        out.append("#endif")


if __name__ == "__main__":
    out = ["/* generated by gen_q15.py - do not edit.  Q15 split-radix codelets on vq,",
           "   the int16 vector q15-inl.h defines for the current target. */",
           "#if defined(AP_CODELETS_Q15_INL_H_) == defined(HWY_TARGET_TOGGLE)",
           "#ifdef AP_CODELETS_Q15_INL_H_", "#undef AP_CODELETS_Q15_INL_H_",
           "#else", "#define AP_CODELETS_Q15_INL_H_", "#endif", "",
           "HWY_BEFORE_NAMESPACE();", "namespace ap {", "namespace HWY_NAMESPACE {", ""]
    out.append("#if AP_Q15_FUSED")
    _emit_family(out, fused=True)
    out.append("#else")
    _emit_family(out, fused=False)
    out.append("#endif")
    out.append("#if AP_Q15_TAIL")
    for nn in (8, 16):
        out.append(build_q(nn, "qsr%d_prod_tile" % nn, prod=True, fused=False, tile=True))
    out.append("#if defined(AP_SIMD_AVX1) || (defined(HWY_ARCH_X86) && HWY_ARCH_X86 && (!defined(HWY_MAX_BYTES) || HWY_MAX_BYTES < 64))")
    out.append(build_q(32, "qsr32_prod_tile", prod=True, fused=False, tile=True, stream_z32=True))
    out.append("#else")
    out.append(build_q(32, "qsr32_prod_tile", prod=True, fused=False, tile=True, stream_z32=False))
    out.append("#endif")
    out.append("#endif")
    out += ["}  // namespace HWY_NAMESPACE", "}  // namespace ap",
            "HWY_AFTER_NAMESPACE();", "", "#endif", ""]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "codelets-q15-inl.h")
    open(path, "w").write("\n".join(out))
    print("generated", path)
