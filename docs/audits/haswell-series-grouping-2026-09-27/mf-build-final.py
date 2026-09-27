from pathlib import Path
import json,shutil,subprocess
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/kernel-study')
shutil.copytree(r/'policy-candidate',r/'final-candidate',dirs_exist_ok=True)
commands=json.loads((r/'unit-build-commands.json').read_text())
commands=[[x.replace('/unit-src','/final-src').replace('/unit-kernel.o','/final-kernel.o').replace('/unit-candidate/','/final-candidate/') for x in c] for c in commands]
for cmd in commands:subprocess.run(cmd,check=True)
(r/'final-build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
base=json.loads((r/'policy-build-commands.json').read_text())[-1]
hwy=[x for x in base if x.endswith('.o') and '/highway/' in x]
subprocess.run(['g++',str(r/'kernel_floor.o'),str(r/'final-kernel.o'),*hwy,'-lm','-o',str(r/'kernel_floor_final')],check=True)
