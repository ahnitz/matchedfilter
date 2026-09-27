from pathlib import Path
import shutil, subprocess, json, re
p=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926');r=p/'hosts/og-node-169/kernel-study';cand=r/'addport-src'
shutil.copytree(r/'sr32-src',cand,dirs_exist_ok=True)
f=cand/'codelets-inl.h';s=f.read_text();counter=0
def sub(m):
 global counter
 counter+=1
 return 'V_FMADD_ONE(' if counter%2 else m[0]
s=re.sub(r'V_ADD\(',sub,s)
s='''#if HWY_TARGET == HWY_AVX2
#define V_FMADD_ONE(a,b) V_FMADD((a),V_SET1(1.0f),(b))
#else
#define V_FMADD_ONE(a,b) V_ADD((a),(b))
#endif
'''+s+'\n#undef V_FMADD_ONE\n'
f.write_text(s)
shutil.copytree(r/'policy-candidate',r/'addport-candidate',dirs_exist_ok=True)
commands=json.loads((r/'sr32-build-commands.json').read_text())
commands=[[x.replace('/sr32-src','/addport-src').replace('/sr32-kernel.o','/addport-kernel.o').replace('/sr32-candidate/','/addport-candidate/') for x in c] for c in commands]
for cmd in commands: subprocess.run(cmd,check=True)
(r/'addport-build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
