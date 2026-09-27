from pathlib import Path
import subprocess,re,json,collections
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169')
report={}
for variant in ('signfinal','difb','difab','fusedpeak'):
 libs=list((r/'kernel-study'/f'{variant}-candidate/matchedfilter').glob('_core*.so'))
 if not libs:continue
 asm=subprocess.check_output(['objdump','-d','-C','--no-show-raw-insn',str(libs[0])],text=True)
 rows=[]
 for m in re.finditer(r'^([0-9a-f]+) <([^\n]+)>:\n(.*?)(?=^[0-9a-f]+ <|\Z)',asm,re.M|re.S):
  if not m[2].startswith('ap::N_AVX2::'):continue
  if not any('::'+name+'(' in m[2] for name in ('stageB_inplace32','fftsr32_prod_unit','stageA_prod_32','binmax_fused32','fftsr32_unit_peak')):continue
  ins=re.findall(r'^\s*[0-9a-f]+:\s+([\w.]+)\s*(.*)$',m[3],re.M)
  rows.append({'symbol':m[2],'instructions':len(ins),'stack_adjustments':[arg for op,arg in ins if op=='sub' and arg.endswith(',%rsp')],'static_stack_operands':sum('(%rsp' in arg or '(%rbp' in arg for op,arg in ins),'opcodes':dict(collections.Counter(op for op,arg in ins))})
 report[variant]=rows
(r/'results/kernel-dataflow-assembly.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({v:[(x['symbol'].split('(')[0],x['instructions'],x['stack_adjustments'],x['static_stack_operands']) for x in rows] for v,rows in report.items()},indent=2))
