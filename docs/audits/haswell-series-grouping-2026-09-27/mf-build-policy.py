from pathlib import Path
import shutil, subprocess, sysconfig, json
p=Path('/home/ahnitz/pycbc-wider-cpu-benchmark-20260926');r=p/'hosts/og-node-169/kernel-study';src=p/'src/matchedfilter';changes=r/'policy-src'
package=r/'policy-candidate/matchedfilter'
shutil.copytree(p/'venv/lib/python3.11/site-packages/matchedfilter',package,dirs_exist_ok=True)
for file in (changes/'python/matchedfilter').iterdir():
 if file.suffix in ('.py','.json'): shutil.copy2(file,package/file.name)
objects=sorted((src/'build').rglob('*.o'));assert len(objects)==8
commands=[]; replacements={}
for source in (changes/'src/hmf.c',changes/'python/matchedfilter/_core.c'):
 obj=r/('policy-'+source.stem+'.o')
 cmd=['gcc','-Wsign-compare','-DNDEBUG','-g','-fwrapv','-O3','-Wall','-fPIC','-fno-math-errno','-I'+str(changes/'python/matchedfilter'),'-I'+str(src/'src'),'-I'+sysconfig.get_path('include'),'-c',str(source),'-o',str(obj)]
 subprocess.run(cmd,check=True);commands.append(cmd);replacements[source.stem+'.o']=str(obj)
cmd=['g++','-shared',*[replacements.get(o.name,str(o)) for o in objects],'-lm','-o',str(package/('_core'+sysconfig.get_config_var('EXT_SUFFIX')))]
subprocess.run(cmd,check=True);commands.append(cmd)
(r/'policy-build-commands.json').write_text(json.dumps(commands,indent=2)+'\n');print('policy candidate built')
