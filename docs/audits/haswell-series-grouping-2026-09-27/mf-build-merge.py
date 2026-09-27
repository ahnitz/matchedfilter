from pathlib import Path
import json,shutil,subprocess,sysconfig,shlex
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/kernel-study')
shutil.copytree(r/'sinkbound-candidate',r/'merge-candidate',dirs_exist_ok=True)
commands=json.loads((r/'sinkbound-build-commands.json').read_text())
includes=[x.replace('/sinkfinal-src','/merge-src') for x in commands[0] if x.startswith('-I')]
for i,name in enumerate(('dispatch','matchfilt'),1):
 commands[i]=['gcc',*shlex.split(sysconfig.get_config_var('CFLAGS')),'-fPIC','-O3','-fno-math-errno',*includes,'-c',str(r/'merge-src'/f'{name}.c'),'-o',str(r/f'merge-{name}.o')]
 subprocess.run(commands[i],check=True)
commands[-1]=[x.replace('/sinkbound-candidate/','/merge-candidate/').replace('/sinkbound-dispatch.o','/merge-dispatch.o').replace('/sinkbound-matchfilt.o','/merge-matchfilt.o') for x in commands[-1]]
subprocess.run(commands[-1],check=True)
(r/'merge-build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
