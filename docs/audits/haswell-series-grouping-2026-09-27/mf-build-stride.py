from pathlib import Path
import shutil, subprocess, json,re
p=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926');r=p/'hosts/og-node-169/kernel-study';cand=r/'stride-src'
shutil.copytree(r/'sr32-src',cand,dirs_exist_ok=True)
f=cand/'codelets-inl.h';s=f.read_text()
for name in ('fftsr32_prod','fftsr32'):
 start=s.index('static inline int '+name+'('); brace=s.index('{',start);depth=1;end=brace+1
 while depth:
  depth+=(s[end]=='{')-(s[end]=='}');end+=1
 block=s[start:end]
 clone=block.replace(name+'(',name+'_unit(').replace('const long S,const long DS','const long ignored_S,const long ignored_DS').replace('const long S)', 'const long ignored_S)')
 clone=clone[:clone.index('{')+1]+('\n const long S=1,DS=AP_W;\n' if name.endswith('_prod') else '\n const long S=1;\n')+clone[clone.index('{')+1:]
 s=s[:end]+'\n'+clone+'\n'+s[end:]
f.write_text(s)
f=cand/'elemfft-inl.h';s=f.read_text().replace('case 32: return fftsr32 (ar,ai,br,bi,S);','case 32: if(S==1) return fftsr32_unit(ar,ai,br,bi,S);\n             return fftsr32(ar,ai,br,bi,S);');f.write_text(s)
f=cand/'product-inl.h';s=f.read_text().replace('if(m==32 && ap_srprod()) return AP_PROD_FN(fftsr32_prod)', 'if(m==32 && ap_srprod() && S==1 && DS==AP_W) return AP_PROD_FN(fftsr32_prod_unit)(dr,di,tr,ti,ar,ai,br,bi,S,DS);\n    if(m==32 && ap_srprod()) return AP_PROD_FN(fftsr32_prod)');f.write_text(s)
# Scalar-broadcast product dispatch also instantiates this name. Its generated
# body loads one scalar per element, just as the original broadcast variant.
f=cand/'codelets-inl.h';s=f.read_text()
# Existing broadcast family is emitted by generator, rather than macro rename.
# Supply the unit clone for it as well.
name='fftsr32_prod_broadcast'
if name+'(' in s:
 start=s.index('static inline int '+name+'(');brace=s.index('{',start);depth=1;end=brace+1
 while depth:depth+=(s[end]=='{')-(s[end]=='}');end+=1
 block=s[start:end];clone=block.replace(name+'(', 'fftsr32_prod_unit_broadcast(').replace('const long S,const long DS','const long ignored_S,const long ignored_DS');brace=clone.index('{');clone=clone[:brace+1]+'\n const long S=1,DS=AP_W;\n'+clone[brace+1:];s=s[:end]+'\n'+clone+'\n'+s[end:]
f.write_text(s)
shutil.copytree(r/'policy-candidate',r/'stride-candidate',dirs_exist_ok=True)
commands=json.loads((r/'sr32-build-commands.json').read_text())
commands=[[x.replace('/sr32-src','/stride-src').replace('/sr32-kernel.o','/stride-kernel.o').replace('/sr32-candidate/','/stride-candidate/') for x in c] for c in commands]
for cmd in commands: subprocess.run(cmd,check=True)
(r/'stride-build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
