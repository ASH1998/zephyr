"""Opt-in production worker matrix for multi-region model compatibility."""
import argparse
import json
from pathlib import Path
import time
from zephyr.local.server import Jobs, preset_plan

parser = argparse.ArgumentParser()
parser.add_argument('--live', action='store_true')
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--geometry', choices=('drivaer-1', 'hatchback'))
parser.add_argument('--handle', choices=('nose-width-v1','hood-height-v1','side-shoulder-v1','deck-height-v1','rear-width-upper-v1'))
args = parser.parse_args()
if not args.live: parser.error('Requires --live for local GPU work')
if args.output.exists(): parser.error('Preserve previous evidence; choose a fresh output')
cases = [('hatchback', h) for h in ('nose-width-v1','hood-height-v1','side-shoulder-v1','deck-height-v1')]
cases += [('drivaer-1','hood-height-v1'), ('drivaer-1','rear-width-upper-v1')]
if bool(args.geometry) != bool(args.handle): parser.error('Provide both --geometry and --handle for a focused check')
if args.geometry: cases = [(args.geometry,args.handle)]
report = {'requestedBudgetMm': 4, 'plannedCases': cases, 'cases': [],
    'scope': 'Production runtime compatibility; acceptance and physical accuracy are distinct.'}
args.output.parent.mkdir(parents=True, exist_ok=True)
jobs = Jobs()
try:
    for geometry, handle in cases:
        authorized = preset_plan({'geometryId':geometry,'handle':handle,'budgetMm':4})
        intent = authorized.pop('intent'); authorized['mode'] = 'iteration'
        job = jobs.start(authorized, intent=intent)
        print(json.dumps({'geometry':geometry,'handle':handle,'runId':job['runId']}), flush=True)
        stage = None
        while job['state'] not in ('complete','failed','cancelled'):
            if stage != job['stage']:
                print(json.dumps({'runId':job['runId'],'stage':job['stage'],'detail':job['detail']}), flush=True)
                stage = job['stage']
            time.sleep(1); job = jobs.snapshot(job['runId'])
        row = {'geometry':geometry,'handle':handle,'runId':job['runId'],'state':job['state']}
        if job['state'] == 'complete':
            e = json.loads((jobs.root/job['runId']/'evidence.json').read_text())
            target = args.output.parent/(args.output.stem+'-'+geometry+'-'+handle+'.json')
            if target.exists(): raise FileExistsError('Refusing to replace previous run evidence: '+str(target))
            target.write_text(json.dumps(e, indent=2, allow_nan=False))
            row.update(forces=e['forces'], trust=e['trust'], timings=e['timings'], validation=e['validation'],
                modelCompatibility=e.get('modelCompatibility'), airflowStatus=e.get('airflowStatus'),
                effectiveAmplitudeMm=e.get('handle',{}).get('amplitudeM',0)*1000)
        else: row['detail'] = job['detail']
        report['cases'].append(row)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False))
        print(json.dumps(row), flush=True)
        while jobs.active is not None: time.sleep(.1)
finally: jobs.close()
