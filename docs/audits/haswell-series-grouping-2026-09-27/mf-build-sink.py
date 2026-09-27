from pathlib import Path
import json,shutil,subprocess
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/kernel-study')
shutil.copytree(r/'retained-candidate',r/'sink-candidate',dirs_exist_ok=True)
commands=json.loads((r/'retained-build-commands.json').read_text())
commands=[[x.replace('/retained-src','/sink-src').replace('/retained-kernel.o','/sink-kernel.o').replace('/retained-candidate/','/sink-candidate/') for x in c] for c in commands]
for cmd in commands:subprocess.run(cmd,check=True)
(r/'sink-build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
link=commands[-1]
objects=[x for x in link if x.endswith('.o') and ('kernel.o' in x or '/highway/' in x)]
subprocess.run(['g++','-shared',*objects,'-lm','-o',str(r/'native-sink.so')],check=True)
