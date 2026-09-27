from pathlib import Path
import subprocess,re,json,collections
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169')
for variant in ('policy','sr32'):
 lib=next((r/('kernel-study/'+variant+'-candidate/matchedfilter')).glob('_core*.so'))
 asm=subprocess.check_output(['objdump','-d','-C','--no-show-raw-insn',str(lib)],text=True)
 out=[];blocks=[]
 for m in re.finditer(r'^([0-9a-f]+) <([^\n]+)>:\n(.*?)(?=^[0-9a-f]+ <|\Z)',asm,re.M|re.S):
  if not m[2].startswith('ap::N_AVX2::'):continue
  if not any('::'+x+'(' in m[2] for x in ('fft32_prod','fftsr32_prod','fftsr32','stageA_prod_gm')):continue
  ins=re.findall(r'^\s*[0-9a-f]+:\s+([\w.]+)\s*(.*)$',m[3],re.M)
  counts=collections.Counter(op for op,arg in ins)
  flops=sum((2 if re.match('v(fm|fnm)',op) else 1)*8 for op,arg in ins if '%ymm' in arg and (re.match('v(fm|fnm)',op) or op in ('vaddps','vsubps','vmulps')))
  out.append(dict(symbol=m[2],opcodes=dict(counts),static_ymm_flops=flops,instructions=len(ins),stack_memory_operands=sum(('(%rsp' in arg or '(%rbp' in arg) for op,arg in ins)))
  blocks.append(m[0])
 (r/('results/hot-'+variant+'.json')).write_text(json.dumps(out,indent=2)+'\n')
 (r/('results/hot-'+variant+'.asm')).write_text('\n'.join(blocks))
 print(variant,[(x['symbol'].split('(')[0],x['instructions'],x['static_ymm_flops'],x['stack_memory_operands']) for x in out])
for v in ('sr32','twiddle'):
 p=json.loads((r/('results/kernel-floor-'+v+'.json')).read_text());print(v,p)
