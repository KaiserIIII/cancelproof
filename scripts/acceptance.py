"""Acceptance against the installed distribution; writes only the requested new directory."""
import json
from pathlib import Path
import platform
import subprocess
import sys


CASES=[('lock_broken','after_lock','FAIL',None),('lock_fixed','after_lock','PASS',None),
       ('token_broken','granted','FAIL','worker'),('token_fixed','granted','PASS','worker'),
       ('swallow_broken','work','FAIL',None),('swallow_fixed','work','PASS',None),
       ('background_broken','request','FAIL',None),('background_fixed','request','PASS',None),
       ('cleanup_broken','work','FAIL',None),('cleanup_fixed','work','PASS',None),
       ('taskgroup_ok','group_work','PASS','worker'),('asgi_broken','request_received','FAIL','request'),
       ('asgi_fixed','request_received','PASS','request')]


def main():
    from cancelproof import run_scenario
    from cancelproof.reports import write_reports
    folder=Path(sys.argv[1]);folder.mkdir(parents=True,exist_ok=False)
    results=[]
    for name,checkpoint,expected,task in CASES:
        action={'checkpoint':checkpoint,'task':task}
        if name.startswith('cleanup_'):action['repeat']=2
        r=run_scenario('cancelproof.examples:'+name,{'actions':[action]})
        write_reports(r,folder/name)
        assert r['verdict']==expected,(name,r['diagnostics'])
        assert r['process']['reaped']
        seqs={e['seq'] for e in r['events']}
        assert all(p['event_seq'] in seqs for p in r['checkpoints'])
        assert len(r['source_sha256'])==64
        results.append({'case':name,'verdict':r['verdict'],'outcome':r['outcome'],
                        'diagnostics':r['diagnostics'],'invariants':r['invariants'],
                        'tasks':[{k:t[k] for k in ('name','state','excluded')} for t in r['tasks']],
                        'actions':r['actions']})
    command_results=[]
    for target,code in [('lock_fixed',0),('missing_target',1)]:
        scenario='cancelproof.examples:'+target
        p=subprocess.run([sys.executable,'-m','cancelproof','run',scenario],capture_output=True,timeout=15)
        assert p.returncode==code
        command_results.append({'target':scenario,'exit':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode()})
    # Unknown checkpoint + Unicode JSON file prove machine-output encoding on redirected Windows stdout.
    plan=folder/'unicode-plan.json';plan.write_text('{"actions":[{"checkpoint":"中文检查点🙂"}]}',encoding='utf-8')
    p=subprocess.run([sys.executable,'-m','cancelproof','run','cancelproof.examples:lock_fixed','--plan',str(plan)],capture_output=True,timeout=15)
    assert p.returncode==3
    r=json.loads(p.stdout);assert r['actions'][0]['checkpoint']=='中文检查点🙂'
    command_results.append({'target':'Unicode unreached point','exit':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode()})
    data={'environment':{'python':platform.python_version(),'system':platform.system()},'cases':results,'cli':command_results}
    (folder/'ACCEPTANCE.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'environment':data['environment'],'cases':len(results),'status':'PASS'}))


if __name__=='__main__':main()
