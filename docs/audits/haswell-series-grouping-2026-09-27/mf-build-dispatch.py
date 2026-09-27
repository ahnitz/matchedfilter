from pathlib import Path
import shutil, subprocess, sysconfig, json
p=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926')
r=p/'hosts/og-node-169/kernel-study'; src=p/'src/matchedfilter'
installed=p/'venv/lib/python3.11/site-packages/matchedfilter'
objects=sorted((src/'build').rglob('*.o'))
assert len(objects)==8
commands=[]
for name,source in [('baseline',src/'src/matchfilt.c'),('candidate',r/'matchfilt.c')]:
 package=r/name/'matchedfilter'; shutil.copytree(installed,package,dirs_exist_ok=True)
 obj=r/(name+'-matchfilt.o')
 cmd=['gcc','-Wsign-compare','-DNDEBUG','-g','-fwrapv','-O3','-Wall','-fPIC','-fno-math-errno','-I'+str(src/'src'),'-I'+str(src/'python/matchedfilter'),'-c',str(source),'-o',str(obj)]
 subprocess.run(cmd,check=True);commands.append(cmd)
 objs=[str(obj) if o.name=='matchfilt.o' else str(o) for o in objects]
 cmd=['g++','-shared',*objs,'-lm','-o',str(package/('_core'+sysconfig.get_config_var('EXT_SUFFIX')))]
 subprocess.run(cmd,check=True);commands.append(cmd)
(r/'build-commands.json').write_text(json.dumps(commands,indent=2)+'\n')
print('built baseline and candidate')
