from pathlib import Path
import json,shutil,subprocess
r=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926/hosts/og-node-169/kernel-study')
shutil.copytree(r/'sinkfinal-candidate',r/'sinkbound-candidate',dirs_exist_ok=True)
commands=json.loads((r/'sinkfinal-build-commands.json').read_text())
# The kernel and Highway objects are unchanged; rebuild both C callers.
for i in (1,2):
 commands[i]=[x.replace('/sinkfinal-src','/sinkbound-src').replace('/sinkfinal-dispatch.o','/sinkbound-dispatch.o').replace('/sinkfinal-matchfilt.o','/sinkbound-matchfilt.o') for x in commands[i]]
 subprocess.run(commands[i],check=True)
commands[-1]=[x.replace('/sinkfinal-candidate/','/sinkbound-candidate/').replace('/sinkfinal-dispatch.o','/sinkbound-dispatch.o').replace('/sinkfinal-matchfilt.o','/sinkbound-matchfilt.o') for x in commands[-1]]
subprocess.run(commands[-1],check=True)
(r/'sinkbound-build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
