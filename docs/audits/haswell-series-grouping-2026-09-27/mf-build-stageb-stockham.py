from pathlib import Path
import json,shutil,subprocess,importlib.util,re,sys
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/kernel-study')
variant=sys.argv[1]
radices={'stageb48':[4,8],'stageb84':[8,4]}[variant]
shutil.copytree(r/'isolated-src',r/(variant+'-src'),dirs_exist_ok=True)
spec=importlib.util.spec_from_file_location('mfgen',r/(variant+'-src/gen.py'));gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
f=r/(variant+'-src/codelets-inl.h');s=f.read_text();name='fftsr32_unit_inplace';a=s.index('static inline int '+name+'(');b=s.index('\n}',a)+2
block=gen.build(32,radices,name)
block=block.replace('vf*restrict ar,vf*restrict ai','float*restrict ar,float*restrict ai').replace('const long S)','const long unused_S)')
brace=block.index('{');block=block[:brace+1]+'\n (void)unused_S; const long S=1;\n'+block[brace+1:]
block=re.sub(r'(ar|ai)\[S\*(\d+)\]=(\w+);',lambda m:'V_STOREU(%s+AP_W*%s,%s);'%m.groups(),block)
block=re.sub(r'(ar|ai)\[S\*(\d+)\]',lambda m:'V_LOADU(%s+AP_W*%s)'%m.groups(),block)
assert 'return 0;' in block
f.write_text(s[:a]+block+s[b:])
shutil.copytree(r/'isolated-candidate',r/(variant+'-candidate'),dirs_exist_ok=True)
commands=json.loads((r/'isolated-build-commands.json').read_text())
commands=[[x.replace('/isolated-src','/'+variant+'-src').replace('/isolated-kernel.o','/'+variant+'-kernel.o').replace('/isolated-candidate/','/'+variant+'-candidate/') for x in c] for c in commands]
for cmd in commands:subprocess.run(cmd,check=True)
(r/(variant+'-build-commands.json')).write_text(json.dumps(commands,indent=2)+'\n')
