from pathlib import Path
import shutil, subprocess, json
p=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926');r=p/'hosts/og-node-169/kernel-study';src=p/'src/matchedfilter';cand=r/'sr32-src'
shutil.copytree(src/'src',cand,dirs_exist_ok=True)
f=cand/'product-inl.h';s=f.read_text();needle='  if(ap_srprod()) switch(m){';assert needle in s
s=s.replace(needle,'''  if constexpr (AP_W == 8) {
    if(m==32 && ap_srprod()) return AP_PROD_FN(fftsr32_prod)(dr,di,tr,ti,ar,ai,br,bi,S,DS);
  }
'''+needle);f.write_text(s)
shutil.copytree(r/'policy-candidate',r/'sr32-candidate',dirs_exist_ok=True)
hwy=src/'third_party/highway'
disabled='HWY_SCALAR|HWY_SVE|HWY_SVE2|HWY_SVE_256|HWY_SVE2_128|HWY_RVV|HWY_AVX3_DL|HWY_AVX3_ZEN4|HWY_AVX3_SPR|HWY_AVX10_2|HWY_SSE2|HWY_SSSE3'
obj=r/'sr32-kernel.o'
cmd=['g++','-Wsign-compare','-DNDEBUG','-g','-fwrapv','-O3','-Wall','-fPIC','-fno-math-errno','-std=c++17','-msse4.2','-maes','-mpclmul','-DHWY_DISABLED_TARGETS=('+disabled+')','-I'+str(cand),'-I'+str(src/'python/matchedfilter'),'-I'+str(hwy),'-c',str(cand/'kernel.cc'),'-o',str(obj)]
subprocess.run(cmd,check=True)
commands=json.loads((r/'policy-build-commands.json').read_text());link=commands[-1]
link=[str(obj) if v.endswith('/g0/src/kernel.o') else v for v in link]
link[-1]=link[-1].replace('/policy-candidate/','/sr32-candidate/')
subprocess.run(link,check=True)
(r/'sr32-build-commands.json').write_text(json.dumps([cmd,link],indent=2)+'\n');print('sr32 kernel built')
