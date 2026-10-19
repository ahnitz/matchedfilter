"""Generate the Q15 (int16 fixed-point) split-radix codelets in codelets-q15-inl.h.

Same DAGs as gen.py's split-radix codelets, on a vector of int16 lanes (`vq`,
twice the float lane count at a given vector width). The arithmetic is exact
integer add/subtract plus Q15 rounding multiplies (Q_MUL = round(a*b / 2^15),
vpmulhrsw on x86) and multiply-accumulates (Q_MLAH/Q_MLSH = acc +- round(a*b / 2^15),
one SQRDMLAH/SQRDMLSH on AArch64, Q_ADD/Q_SUB(acc, Q_MUL) elsewhere; every rounding is to
nearest, within 1/2 LSB), and nothing in a codelet rescales: the caller sizes its
inputs so that every intermediate stays in range (see q15-inl.h for the bound).
Twiddle constants are |cos|, |sin| rounded to Q15 and the signs ride on the
adds, as gen.py does for the float FMAs.

    python src/gen_q15.py          # rewrites src/codelets-q15-inl.h
"""
import os
import re

from gen import SRGen, fold_negations, trivial, wconst


def q15(v):
    return max(-32767, min(32767, int(round(v * 32768.0))))


class QGen(SRGen):
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
        cc = s.const("c", abs(c)); ss = s.const("s", abs(sn))
        # x1 = ar*cc, x2 = ai*ss, y1 = ar*ss, y2 = ai*cc; real = sc*x1 - sg*x2,
        # imag = sg*y1 + sc*y2. One product of each pair is a plain Q_MUL and the other
        # rides in a rounding multiply-accumulate (Q_MLAH/Q_MLSH: acc +- round(a*b/2^15),
        # one instruction where the target has it, else Q_ADD/Q_SUB(acc, Q_MUL)).
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
            # conj(d*t) = (dr*tr - di*ti) + i(-di*tr - dr*ti). The data element
            # is stored as (dr, di, -di) so the imaginary part is one subtract.
            s.emit("vf tR%d=Q_LOADU(tr+TS*%d), tI%d=Q_LOADU(ti+TS*%d);" % (idx, idx, idx, idx))
            s.emit("vf dR%d=Q_SET1(dq[DS*%d]), dI%d=Q_SET1(dq[DS*%d+1]), nI%d=Q_SET1(dq[DS*%d+2]);"
                   % (idx, idx, idx, idx, idx, idx))
            s.emit("vf %s=Q_MLSH(Q_MUL(dR%d,tR%d),dI%d,tI%d);" % (o[0], idx, idx, idx, idx))
            s.emit("vf %s=Q_MLSH(Q_MUL(nI%d,tR%d),dR%d,tI%d);" % (o[1], idx, idx, idx, idx))
            return o
        if s.tw and idx != 0:
            s.emit("const vf W%dr=Q_SET1(twr[%d]), W%di=Q_SET1(twi[%d]);" % (idx, idx, idx, idx))
            s.emit("vf %s=Q_MLSH(Q_MUL(ar[S*%d],W%dr),ai[S*%d],W%di);" % (o[0], idx, idx, idx, idx))
            s.emit("vf %s=Q_MLAH(Q_MUL(ar[S*%d],W%di),ai[S*%d],W%dr);" % (o[1], idx, idx, idx, idx))
            return o
        s.emit("vf %s=ar[S*%d], %s=ai[S*%d];" % (o[0], idx, o[1], idx))
        return o


class QGenClassic(SRGen):
    """The separate-multiply form (Q_ADD/Q_SUB of Q_MULs), emitted for every target
    without a fused rounding multiply-accumulate: its text, and so its code, is unchanged."""
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
        cc = s.const("c", abs(c)); ss = s.const("s", abs(sn))
        k = s.nc; s.nc += 1
        x1, x2, y1, y2 = ("m%d_%d" % (k, j) for j in range(4))
        s.emit("vf %s=Q_MUL(%s,%s), %s=Q_MUL(%s,%s);" % (x1, ar, cc, x2, ai, ss))
        s.emit("vf %s=Q_MUL(%s,%s), %s=Q_MUL(%s,%s);" % (y1, ar, ss, y2, ai, cc))
        sc = 1 if c >= 0 else -1
        sg = 1 if sn >= 0 else -1
        # real = sc*x1 - sg*x2
        if (sc, sg) == (1, 1):
            s.emit("vf %s=V_SUB(%s,%s);" % (orr, x1, x2))
        elif (sc, sg) == (1, -1):
            s.emit("vf %s=V_ADD(%s,%s);" % (orr, x1, x2))
        elif (sc, sg) == (-1, -1):
            s.emit("vf %s=V_SUB(%s,%s);" % (orr, x2, x1))
        else:
            s.emit("vf n%s=V_ADD(%s,%s);" % (orr, x1, x2))
            s.emit("vf %s=V_SUB(Z,n%s);" % (orr, orr))
        # imag = sg*y1 + sc*y2
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
            # conj(d*t) = (dr*tr - di*ti) + i(-di*tr - dr*ti). The data element
            # is stored as (dr, di, -di) so the imaginary part is one subtract.
            s.emit("vf tR%d=Q_LOADU(tr+TS*%d), tI%d=Q_LOADU(ti+TS*%d);" % (idx, idx, idx, idx))
            s.emit("vf dR%d=Q_SET1(dq[DS*%d]), dI%d=Q_SET1(dq[DS*%d+1]), nI%d=Q_SET1(dq[DS*%d+2]);"
                   % (idx, idx, idx, idx, idx, idx))
            s.emit("vf %s=V_SUB(Q_MUL(dR%d,tR%d),Q_MUL(dI%d,tI%d));" % (o[0], idx, idx, idx, idx))
            s.emit("vf %s=V_SUB(Q_MUL(nI%d,tR%d),Q_MUL(dR%d,tI%d));" % (o[1], idx, idx, idx, idx))
            return o
        if s.tw and idx != 0:
            s.emit("const vf W%dr=Q_SET1(twr[%d]), W%di=Q_SET1(twi[%d]);" % (idx, idx, idx, idx))
            s.emit("vf %s=V_SUB(Q_MUL(ar[S*%d],W%dr),Q_MUL(ai[S*%d],W%di));" % (o[0], idx, idx, idx, idx))
            s.emit("vf %s=V_ADD(Q_MUL(ar[S*%d],W%di),Q_MUL(ai[S*%d],W%dr));" % (o[1], idx, idx, idx, idx))
            return o
        s.emit("vf %s=ar[S*%d], %s=ai[S*%d];" % (o[0], idx, o[1], idx))
        return o


def build_q(n, name, tw=False, prod=False, fused=True, maxout=False, max_interior=None, tile=False):
    """maxout: instead of storing the n outputs, accumulate max(|z|^2) of those with index
    in [lo, hi) into mx[0] (even k) and mx[1] (odd k) -- the screen's window maximum fused
    into its last pass, so the outputs never go back to memory. Same Q_MUL squares as the
    separate maximum loop: bit-identical maxima. max_interior=(a,b) additionally
    requires lo <= a and hi >= b, removing the output tests inside that interval."""
    g = (QGen if fused else QGenClassic)(n, name, tw, False, prod)
    X = g.rec(list(range(n)))
    for k in range(n):
        if maxout:
            condition = "" if max_interior and max_interior[0] <= k < max_interior[1] else (
                "if(%d>=lo && %d<hi) " % (k, k))
            g.emit(condition + "M%d=hn::Max(M%d,hn::SaturatedAdd(Q_MUL(%s,%s),Q_MUL(%s,%s)));"
                   % (k & 1, k & 1, X[k][0], X[k][0], X[k][1], X[k][1]))
        else:
            g.emit("ar[S*%d]=%s; ai[S*%d]=%s;" % (k, X[k][0], k, X[k][1]))
    if maxout:
        g.emit("mx[0]=M0; mx[1]=M1;")
    body = fold_negations("\n".join(g.L))
    body = re.sub(r"\bvf\b", "vq", body)
    body = body.replace("V_ADD(", "Q_ADD(").replace("V_SUB(", "Q_SUB(")
    if tile:
        body = re.sub(r"Q_LOADU\((t[ri]\+TS\*\d+)\)", r"q15_tile_template<T>(\1)", body)
        body = re.sub(r"Q_SET1\(dq\[(DS\*\d+(?:\+[12])?)\]\)",
                      r"q15_tile_data<T, B>(dq+\1)", body)
    cdefs = "\n".join("  const vq %s=Q_SET1(%s);" % (v, k) for k, v in g.consts.items())
    if prod:
        args = ("const int16_t*restrict dq,const int16_t*restrict tr,const int16_t*restrict ti,"
                "vq*restrict ar,vq*restrict ai,const long S,const long DS,const long TS")
    elif tw and maxout:
        args = ("const vq*restrict ar,const vq*restrict ai,const long S,"
                "const int16_t*restrict twr,const int16_t*restrict twi,"
                "const long lo,const long hi,vq*restrict mx")
    elif tw:
        args = ("vq*restrict ar,vq*restrict ai,const long S,"
                "const int16_t*restrict twr,const int16_t*restrict twi")
    else:
        args = "vq*restrict ar,vq*restrict ai,const long S"
    zero = "  const vq Z=Q_ZERO();\n" if re.search(r"\bZ\b", body) else ""
    if maxout:
        zero += "  vq M0=mx[0], M1=mx[1];\n"
    # tile: T templates per block, B int16 between consecutive blocks' data (3 N)
    prefix = "template<int T, long B>\n" if tile else ""
    return prefix + ("static HWY_INLINE void %s(%s){\n%s%s\n%s\n}\n" % (name, args, zero, cdefs, body))


if __name__ == "__main__":
    out = ["/* generated by gen_q15.py - do not edit.  Q15 split-radix codelets on vq,",
           "   the int16 vector q15-inl.h defines for the current target. */",
           "#if defined(AP_CODELETS_Q15_INL_H_) == defined(HWY_TARGET_TOGGLE)",
           "#ifdef AP_CODELETS_Q15_INL_H_", "#undef AP_CODELETS_Q15_INL_H_",
           "#else", "#define AP_CODELETS_Q15_INL_H_", "#endif", "",
           "HWY_BEFORE_NAMESPACE();", "namespace ap {", "namespace HWY_NAMESPACE {", ""]
    # AP_Q15_FUSED (q15-inl.h): the target has a one-instruction Q_MLAH/Q_MLSH (AArch64
    # FEAT_RDM). Elsewhere the separate-multiply codelets, byte for byte as before.
    out.append("#if AP_Q15_FUSED")
    for nn in (8, 16, 32):
        out.append(build_q(nn, "qsr%d_prod" % nn, prod=True))
        out.append(build_q(nn, "qsr%d_tw" % nn, tw=True))
        out.append(build_q(nn, "qsr%d_twmax" % nn, tw=True, maxout=True))
        if nn == 16:
            out.append(build_q(nn, "qsr16_twmax_middle", tw=True, maxout=True,
                               max_interior=(2, 14)))
    out.append("#else")
    for nn in (8, 16, 32):
        out.append(build_q(nn, "qsr%d_prod" % nn, prod=True, fused=False))
        out.append(build_q(nn, "qsr%d_tw" % nn, tw=True, fused=False))
        out.append(build_q(nn, "qsr%d_twmax" % nn, tw=True, fused=False, maxout=True))
        if nn == 16:
            out.append(build_q(nn, "qsr16_twmax_middle", tw=True, fused=False,
                               maxout=True, max_interior=(2, 14)))
    out.append("#endif")
    out.append("#if AP_Q15_TAIL")
    for nn in (8, 16, 32):
        out.append(build_q(nn, "qsr%d_prod_tile" % nn, prod=True, fused=False, tile=True))
    out.append("#endif")
    out += ["}  // namespace HWY_NAMESPACE", "}  // namespace ap",
            "HWY_AFTER_NAMESPACE();", "", "#endif", ""]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "codelets-q15-inl.h")
    open(path, "w").write("\n".join(out))
    print("generated", path)
