import hashlib,json,os,pathlib,shutil,subprocess,sys,time
root=pathlib.Path('/tmp/mf-cpu-trial-reliability-20261015')
study=root/'study-v1'
# Timing starts only after the single-threaded cold-start study has finished.
while True:
    try:
        summary=json.loads((study/'summary.json').read_text())
        if len(summary)==10:
            assert all(r['settled'] for r in summary), 'cold starts did not settle'
            break
    except (FileNotFoundError,json.JSONDecodeError):
        pass
    time.sleep(20)
subprocess.run([sys.executable, str(root/'final/tools/cpu_trial_check.py'), '--bank', str(pathlib.Path.home()/'mf-data/fir_three_level_modern_v1_bottomup_cap401.hdf'), '--profiles', str(pathlib.Path.home()/'mf-data/ladder_profiles_H1.npz'), '--out', str(root/'final-cold-confirmation'), '--starts', '1'], check=True)
seed=json.loads((study/'cost-00.json').read_text())
out=root/'paired-throughput-v1'
out.mkdir(exist_ok=False)
records=[]
def locks(d):
    return {k:{f:v[f] for f in ('winner','chain','q15','rechecked') if f in v} for k,v in d.items()
            if k.startswith(('block-trial|','chain-trial|','q15-trial|')) and not k.endswith('|batches')}
for screen in (True,False):
    forced=json.loads(json.dumps(seed))
    for k,v in forced.items():
        if k.startswith('q15-trial|'): v['q15']=screen
    for rnd in range(4):
        for arm in (('baseline','candidate') if rnd%2==0 else ('candidate','baseline')):
            source=root/'baseline' if arm=='baseline' else root/'final'
            tag=f'{screen}-{rnd}-{arm}'
            cost=out/(tag+'-cost.json'); cost.write_text(json.dumps(forced))
            report=out/(tag+'.json')
            env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
                     PYTHONPATH=str(source/'python'),MF_COST_FILE=str(cost),MF_AUTOTUNE='1',MF_TRIAL_RECHECK='0')
            cmd=[sys.executable,str(source/'tools/ladder.py'),'--bank',str(pathlib.Path.home()/'mf-data/fir_three_level_modern_v1_bottomup_cap401.hdf'),
                 '--profiles',str(pathlib.Path.home()/'mf-data/ladder_profiles_H1.npz'),'--device','cpu','--tops','1','--pure','--segments','10','--out',str(report)]
            with (out/(tag+'.log')).open('w') as log:
                subprocess.run(cmd,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
            after=json.loads(cost.read_text()); assert locks(after)==locks(forced),tag
            r=json.loads(report.read_text())
            if arm=='candidate': assert r['steady_valid'],tag
            records.append(dict(arm=arm,q15=screen,round=rnd,throughput=r['templates_in_real_time']['total'],
                                steady=r['steady_s'],counts=r['counts'],locks=locks(after),
                                core_sha256=hashlib.sha256(next((source/'python/matchedfilter').glob('_core*.so')).read_bytes()).hexdigest()))
            (out/'summary.json').write_text(json.dumps(records,indent=2))
            print(tag,records[-1]['throughput'],flush=True)
