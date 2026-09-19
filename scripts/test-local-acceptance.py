"""Opt-in end-to-end GPU regression using the production worker and GPU leases."""
import argparse
import json
import time
from zephyr.local.server import Jobs

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--live', action='store_true', help='Authorize local GPU inference')
parser.add_argument('--geometry', choices=['drivaer-1', 'hatchback'], required=True)
parser.add_argument('--budget-mm', type=float, default=3.)
args = parser.parse_args()
if not args.live:
    parser.error('GPU inference requires --live')
jobs = Jobs()
try:
    job = jobs.start({'geometryId': args.geometry, 'budgetMm': args.budget_mm,
                      'brief': 'Reduce drag. Keep the cabin unchanged.', 'mode': 'iteration'})
    print(json.dumps({'runId': job['runId']}), flush=True)
    previous = None
    while True:
        job = jobs.snapshot(job['runId'])
        if job['stage'] != previous:
            print(json.dumps({k: job[k] for k in ('runId', 'state', 'stage', 'detail')}), flush=True)
            previous = job['stage']
        if job['state'] in ('complete', 'failed', 'cancelled'):
            break
        time.sleep(1)
    if job['state'] != 'complete':
        raise RuntimeError(job['detail'])
    e = json.loads((jobs.root / job['runId'] / 'evidence.json').read_text(encoding='utf-8'))
    print(json.dumps({k: e[k] for k in ('runId', 'forces', 'trust', 'calibration', 'timings')}), flush=True)
finally:
    jobs.close()
