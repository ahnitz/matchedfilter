from pathlib import Path
import json,shutil,subprocess
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/kernel-study')
shutil.copytree(r/'sinkgate-candidate',r/'sinkfinal-candidate',dirs_exist_ok=True)
commands=json.loads((r/'sinkgate-build-commands.json').read_text())
commands=[[x.replace('/sinkgate-src','/sinkfinal-src').replace('/sinkgate-kernel.o','/sinkfinal-kernel.o').replace('/sinkgate-candidate/','/sinkfinal-candidate/') for x in c] for c in commands]
compile,link=commands
subprocess.run(compile,check=True)
for name in ('dispatch','matchfilt'):
 cmd=['gcc','-O3','-fPIC','-fno-math-errno',*[x for x in compile if x.startswith('-I')],'-c',str(r/'sinkfinal-src'/f'{name}.c'),'-o',str(r/f'sinkfinal-{name}.o')]
 subprocess.run(cmd,check=True)
 link=[str(r/f'sinkfinal-{name}.o') if x.endswith(f'/src/{name}.o') else x for x in link]
 commands.insert(-1,cmd)
commands[-1]=link
subprocess.run(link,check=True)
(r/'sinkfinal-build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
