from pathlib import Path
import subprocess,shlex,shutil
root=Path('/tmp/mf-haswell-pbscan-exact-lib');shutil.copytree('/tmp/mf-haswell-sinkbound-lib',root,dirs_exist_ok=True)
lines=Path('/tmp/mf-haswell-sinkbound-build.log').read_text().splitlines()
replacements={}
for name in ['dispatch','matchfilt']:
 cmd=shlex.split(next(l for l in lines if l.startswith('gcc ') and f'-c src/{name}.c ' in l))
 i=cmd.index('-o')+1;replacements[cmd[i]]=f'/tmp/mf-pbscan-exact-{name}.o';cmd[i]=replacements[cmd[i]]
 subprocess.run(cmd,check=True)
link=shlex.split(lines[-1]);link=[replacements.get(x,x) for x in link];link[link.index('-o')+1]=str(root/'matchedfilter/_core.cpython-313-x86_64-linux-gnu.so')
subprocess.run(link,check=True)
