import argparse
import json
from pathlib import Path
import sys

from .runner import aggregate, campaign, run_scenario
from .reports import write_reports


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
            if any(type(r) is not dict or not r.get('source_sha256') for r in runs):
                raise ValueError('replay requires source digests')
            if sum(r.get('limits',{}).get('wall_timeout',5) for r in runs)>120:
                raise ValueError('replay wall-time budget exceeds 120 seconds')
            result=aggregate(replay['scenario'],[
                run_scenario(replay['scenario'],r.get('plan'),r.get('limits'),expected_source_sha256=r['source_sha256'])
                for r in runs],{'mode':'replay','source_scope':'scenario module only'})
        if getattr(args,'output',None):write_reports(result,args.output)
        # ASCII escaping works with legacy Windows redirected stdout without losing Unicode data.
        print(json.dumps(result,ensure_ascii=True,allow_nan=False))
        if result.get('input_error') or any(r.get('input_error') for r in result.get('runs',[])):return 1
        return {'PASS':0,'FAIL':2,'INCONCLUSIVE':3,'NOT_RUN':3}.get(result.get('verdict'),0)
    except (ValueError,TypeError,OSError,KeyError) as exc:
        print('CancelProof input/output error: '+type(exc).__name__+': '+str(exc),file=sys.stderr)
        return 1
