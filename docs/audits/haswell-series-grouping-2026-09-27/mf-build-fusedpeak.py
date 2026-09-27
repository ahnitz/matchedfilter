from pathlib import Path
import json,shutil,subprocess,re
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/kernel-study');v='fusedpeak'
shutil.copytree(r/'signfinal-src',r/(v+'-src'),dirs_exist_ok=True)
f=r/(v+'-src/codelets-inl.h');s=f.read_text();a=s.index('static inline int fftsr32_unit_inplace(');b=s.index('\n}',a)+2
block=s[a:b].replace('fftsr32_unit_inplace(', 'fftsr32_unit_peak(').replace('const long unused_S)', 'const long unused_S,long base,size_t ws,size_t we,int conj,ap_peak*out)')
helper='''static AP_ALWAYS_INLINE void fft_peak_consider(vf rr,vf ii,long k,size_t ws,size_t we,int conj,ap_peak*out){
  if(k>=(long)we || k+AP_W<=(long)ws) return;
  vf m=V_FMADD(rr,rr,V_MUL(ii,ii));
  if(__builtin_expect(V_MASK_ANY(V_CMP_GT(m,V_SET1(out->magnitude))),0)){
    float mv[AP_W],rv[AP_W],iv[AP_W];
    V_STOREU(mv,m); V_STOREU(rv,rr); V_STOREU(iv,ii);
    for(int l=0;l<AP_W;l++) if(k+l>=(long)ws && k+l<(long)we && mv[l]>out->magnitude){
      out->index=k+l;out->re=rv[l];out->im=conj?-iv[l]:iv[l];out->magnitude=mv[l];
    }
  }
}
'''
block,count=re.subn(r'V_STOREU\(ar\+AP_W\*(\d+),(\w+)\); V_STOREU\(ai\+AP_W\*\1,(\w+)\);',lambda m:'fft_peak_consider(%s,%s,base+%s*32,ws,we,conj,out);'%(m[2],m[3],m[1]),block)
assert count==32,count
s=s[:b]+'\n'+helper+block+'\n'+s[b:];f.write_text(s)
f=r/(v+'-src/balanced-inl.h');s=f.read_text();idx=s.index('template <bool STORE, bool INPLACE=false>')
helper='''static void binmax_fused32(BP*p,float thr,ap_peak*out,int conj,size_t ws,size_t we){
  out->index=-1;out->re=0;out->im=0;out->magnitude=thr>0?thr*thr:0;
  for(int b=0;b<4;b++){
    float *ar=p->ire+(size_t)b*32*AP_W,*ai=p->iim+(size_t)b*32*AP_W;
    fftsr32_unit_peak(ar,ai,p->sR,p->sI,1,b*AP_W,ws,we,conj,out);
  }
  out->magnitude=out->index>=0?sqrtf(out->magnitude):0;
}

'''
s=s[:idx]+helper+s[idx:]
needle='''      if(p->fuse==2 && p->ilay) {
        if(p->ser && !p->nostore)'''
repl='''      if(p->fuse==2 && p->ilay) {
        if(!(p->ser && !p->nostore) && p->bblk==1) return binmax_fused32(p,thr,out,conj,ws,we);
        if(p->ser && !p->nostore)'''
assert needle in s;s=s.replace(needle,repl);f.write_text(s)
shutil.copytree(r/'signfinal-candidate',r/(v+'-candidate'),dirs_exist_ok=True)
commands=json.loads((r/'signfinal-build-commands.json').read_text())
commands=[[x.replace('/signfinal-src','/'+v+'-src').replace('/signfinal-kernel.o','/'+v+'-kernel.o').replace('/signfinal-candidate/','/'+v+'-candidate/') for x in c] for c in commands]
for cmd in commands:subprocess.run(cmd,check=True)
(r/(v+'-build-commands.json')).write_text(json.dumps(commands,indent=2)+'\n')
