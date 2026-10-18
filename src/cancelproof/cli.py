import argparse
import json
from pathlib import Path
import sys
import time

from .runner import aggregate, campaign, run_scenario
from .reports import write_reports
from .config import validate


def load(path):
    file=Path(path)
    if file.stat().st_size > 65536:
        raise ValueError('input JSON exceeds 64 KiB')
    return json.loads(file.read_text(encoding='utf-8-sig'))


def main(argv=None):
    parser=argparse.ArgumentParser(description='Bounded cancellation tests for TRUSTED local async targets.')
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ('run','explore'):
        p=sub.add_parser(name);p.add_argument('scenario');p.add_argument('--limits');p.add_argument('--output')
        if name=='run':p.add_argument('--plan')
        else:
            p.add_argument('--max-runs',type=int,default=12)
            p.add_argument('--seed',type=int,default=0)
            p.add_argument('--repeats',type=int,default=1)
    p=sub.add_parser('replay');p.add_argument('file');p.add_argument('--output')
    sub.add_parser('examples')
    args=parser.parse_args(argv)
    try:
        # Preflight output prevents rerunning side-effectful trusted targets on an overwrite error.
        if getattr(args,'output',None) and Path(args.output).exists():
            raise FileExistsError('output directory already exists')
        if args.command=='examples':
            result={'examples':['lock_broken','lock_fixed','token_broken','token_fixed','swallow_broken','swallow_fixed',
                                'background_broken','background_fixed','cleanup_broken','cleanup_fixed','taskgroup_ok',
                                'asgi_broken','asgi_fixed'], 'module':'cancelproof.examples'}
        elif args.command=='run':
            result=run_scenario(args.scenario,load(args.plan) if args.plan else None,load(args.limits) if args.limits else None)
        elif args.command=='explore':
            result=campaign(args.scenario,args.max_runs,args.seed,args.repeats,load(args.limits) if args.limits else None)
        else:
            replay=load(args.file)
            if type(replay) is not dict or replay.get('schema_version')!=1 or not isinstance(replay.get('scenario'),str):
                raise ValueError('invalid replay')
            runs=replay.get('runs')
            if type(runs) is not list or not 1<=len(runs)<=64:
                raise ValueError('replay requires 1..64 runs')
            prepared=[]
            for r in runs:
                if type(r) is not dict or set(r)-{'plan','limits','source_sha256'}:
                    raise ValueError('invalid replay run fields')
                digest=r.get('source_sha256')
                if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
                    raise ValueError('replay requires lowercase SHA256 digests')
                if type(r.get('limits')) is not dict:
                    raise ValueError('replay limits must be an object')
                plan,limits=validate(replay['scenario'],r.get('plan'),r['limits'])
                prepared.append((plan,limits,digest))
            if sum(limits['wall_timeout'] for _,limits,_ in prepared)>120:
                raise ValueError('replay wall-time budget exceeds 120 seconds')
            started=time.monotonic();executed=[]
            for plan,limits,digest in prepared:
                if time.monotonic()-started+limits['wall_timeout']+2.6>120:
                    executed.append({'verdict':'NOT_RUN','outcome':'not_run','scenario':replay['scenario'],
                                     'plan':plan,'limits':limits,'source_sha256':digest,
                                     'diagnostics':[{'code':'REPLAY_TOTAL_BUDGET'}]})
                    break
                executed.append(run_scenario(replay['scenario'],plan,limits,expected_source_sha256=digest))
            result=aggregate(replay['scenario'],executed,{'mode':'replay','source_scope':'scenario module only',
                                                        'requested':len(prepared),'executed':len(executed),
                                                        'total_seconds_limit':120})
        if getattr(args,'output',None):write_reports(result,args.output)
        # ASCII escaping works with legacy Windows redirected stdout without losing Unicode data.
        print(json.dumps(result,ensure_ascii=True,allow_nan=False))
        if result.get('input_error') or any(r.get('input_error') for r in result.get('runs',[])):return 1
        return {'PASS':0,'FAIL':2,'INCONCLUSIVE':3,'NOT_RUN':3}.get(result.get('verdict'),0)
    except (ValueError,TypeError,OSError,KeyError) as exc:
        print('CancelProof input/output error: '+type(exc).__name__+': '+str(exc),file=sys.stderr)
        return 1
