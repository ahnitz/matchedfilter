import subprocess,re,difflib
paths=['/tmp/mf-haswell-signxor-lib/matchedfilter/_core.cpython-313-x86_64-linux-gnu.so','/tmp/mf-haswell-sinksection-lib/matchedfilter/_core.cpython-313-x86_64-linux-gnu.so']
def functions(path):
 s=subprocess.check_output(['objdump','-dC','--no-show-raw-insn',path],text=True); d={}; key=None
 for l in s.splitlines():
  m=re.match(r'^[0-9a-f]+ <(.*)>:',l)
  if m:key=m[1];d[key]=[]
  elif key and re.match(r'^\s*[0-9a-f]+:',l):
   l=l.split(':',1)[1].strip();l=re.sub(r'0x[0-9a-f]+\(%rip\)', 'OFFSET(%rip)',l);l=re.sub(r'# .*','# ADDRESS',l);l=re.sub(r'(?<![\w])(?:0x)?[0-9a-f]+ <', 'ADDRESS <',l);l=re.sub(r'\+0x[0-9a-f]+>','+OFFSET>',l)
   d[key].append(l)
 return d
x,y=map(functions,paths)
for k in x:
 if 'N_AVX2::' in k and k in y and any(z in k for z in ['stageA_prod','stageB(', 'binmax_core','binmax_prod(']):
  print(k,len(x[k]),len(y[k]),'same',x[k]==y[k]);diff=list(difflib.unified_diff(x[k],y[k]));print('\n'.join(diff[:70]))
