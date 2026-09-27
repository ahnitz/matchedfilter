from pathlib import Path
import json,shutil,subprocess,importlib.util,sys
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/kernel-study')
variant=sys.argv[1]
assert variant in ('difb','difab')
shutil.copytree(r/'signfinal-src',r/(variant+'-src'),dirs_exist_ok=True)
spec=importlib.util.spec_from_file_location('mfgen',r/(variant+'-src/gen.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
def rec(self,idx):
 def dif(x):
  n=len(x)
  if n==1:return x
  if n==2:return [self.add(x[0],x[1]),self.sub(x[0],x[1])]
  q=n//4;u=[None]*(2*q);z=[];zp=[]
  for k in range(q):
   u[k]=self.add(x[k],x[k+2*q]);u[k+q]=self.add(x[k+q],x[k+3*q])
   b=self.sub(x[k],x[k+2*q]);d=self.mi(self.sub(x[k+q],x[k+3*q]))
   z.append(self.twmul(self.add(b,d),k,n))
   zp.append(self.twmul(self.sub(b,d),3*k,n))
  U,Z,Zp=dif(u),dif(z),dif(zp);out=[None]*n
  for k,v in enumerate(U):out[2*k]=v
  for k,v in enumerate(Z):out[4*k+1]=v
  for k,v in enumerate(Zp):out[4*k+3]=v
  return out
 return dif([self.load(i) for i in idx])
g.SRGen.rec=rec
f=r/(variant+'-src/codelets-inl.h');s=f.read_text()
names=[('fftsr32_unit_inplace',False,True)]
if variant=='difab':names += [('fftsr32_prod_unit',True,False)]
for name,prod,inplace in names:
 a=s.index('static inline int '+name+'(');b=s.index('\n}',a)+2
 s=s[:a]+g.build_sr(32,name,unit=True,prod=prod,inplace=inplace)+s[b:]
f.write_text(s)
shutil.copytree(r/'signfinal-candidate',r/(variant+'-candidate'),dirs_exist_ok=True)
commands=json.loads((r/'signfinal-build-commands.json').read_text())
commands=[[x.replace('/signfinal-src','/'+variant+'-src').replace('/signfinal-kernel.o','/'+variant+'-kernel.o').replace('/signfinal-candidate/','/'+variant+'-candidate/') for x in c] for c in commands]
for cmd in commands:subprocess.run(cmd,check=True)
(r/(variant+'-build-commands.json')).write_text(json.dumps(commands,indent=2)+'\n')
