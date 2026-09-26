"""Package the existing built UI, all vehicle/aircraft assets, and verified sedan replay."""
import argparse
import json
from pathlib import Path
import re
import shutil
from zephyr.artifacts import _file_sha256
from zephyr.local.cars import CARS
from zephyr.local.geometry import HANDLES, BODY_HANDLES, COMPARISONS
from zephyr.local.exports import candidate_bundle
from zephyr.local.studies import run_history
from zephyr.run_answers import summarize_run
from zephyr.research.runtime import ROOT, save, utc


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--additional-run-id', action='append', default=[], help='Include another recorded sedan scenario in Previous runs')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    run_ids = [args.run_id, *args.additional_run_id]
    if len(set(run_ids)) != len(run_ids) or any(not re.fullmatch(r'local-[a-f0-9]{32}', rid) for rid in run_ids):
        p.error('Expected distinct local run IDs')
    if args.output.exists(): p.error('Use a new bundle directory')
    if not (ROOT / 'frontend/dist/index.html').exists(): p.error('Build the frontend first')
    # Verify full-resolution exports before writing any deployable package.
    recordings = []
    for rid in run_ids:
        source = ROOT / '.local/runs' / rid
        run = json.loads((source / 'result.json').read_text())
        e = json.loads((source / 'evidence.json').read_text())
        if run['geometryId'] != 'drivaer-1' or run['candidate'] is None:
            p.error('A completed sedan comparison is required')
        if run['runId'] != rid or e['runId'] != rid:
            p.error('Run identity mismatch')
        for key in ('forces', 'provenance', 'validation', 'trust', 'research', 'syntheticDent'):
            if run.get(key) != e.get(key): p.error('Viewer payload differs from evidence: '+key)
        if _file_sha256(source / 'baseline.vtk') != e['artifacts']['baseline.vtk']['sha256']:
            p.error('Baseline artifact differs from evidence')
        recordings.append((rid, source, e, candidate_bundle(source)))
    output = args.output.resolve(); output.mkdir(parents=True)
    shutil.copytree(ROOT / 'frontend/dist', output / 'web')
    artifacts = output / 'evidence'; artifacts.mkdir()
    routes = {}
    def route(url, name, value):
        path = artifacts / name; save(path, value); routes[url] = str(path.relative_to(output)).replace('\\', '/')
    for rid, source, e, archive in recordings:
        prefix = '/api/runs/' + rid
        for item in ('baseline', 'result', 'evidence'):
            value = json.loads((source / (item + '.json')).read_text())
            route(prefix + '/' + item, rid + '-' + item + '.json', value)
        route(prefix, rid + '-job.json', {'runId': rid, 'geometryId': 'drivaer-1', 'source': 'live',
            'state': 'complete', 'stage': 'complete', 'detail': e['trust']['reason'], 'sequence': 1,
            'baselineReady': True, 'resultReady': True, 'createdAt': e['createdAt'], 'restored': True,
            'events': [{'runId': rid, 'source': 'live', 'sequence': 1, 'stage': 'complete', 'detail': 'Recorded completed evaluation'}]})
        route(prefix + '/summary', rid + '-summary.json', summarize_run(e))
        (artifacts / (rid + '-candidate.zip')).write_bytes(archive)
        routes[prefix + '/candidate.zip'] = 'evidence/' + rid + '-candidate.zip'
    route('/api/health', 'health.json', {'service': 'zephyr-recorded-demo', 'activeRunId': None,
        'geometryId': 'drivaer-1', 'copilot': {'enabled': False}, 'execution': 'recorded-only'})
    route('/api/geometries', 'geometries.json', {'cars': CARS})
    route('/api/body-regions', 'body-regions.json', {'handles': [
        {'id': h, 'label': label, 'bodySearch': h in BODY_HANDLES} for h, label in HANDLES.items()],
        'comparisons': {k: list(v) for k, v in COMPARISONS.items()}, 'maximumBudgetMm': 4})
    route('/api/runs', 'runs.json', {'runs': [r for r in run_history(ROOT/'.local/runs') if r['runId'] in run_ids]})
    shutil.copyfile(ROOT / 'scripts/serve-sedan-demo.py', output / 'serve.py')
    shutil.copyfile(ROOT / 'LICENSE', output / 'LICENSE')
    shutil.copytree(ROOT / 'config/licenses', output / 'licenses')
    (output / 'Dockerfile').write_text('FROM python:3.12-alpine\nWORKDIR /app\nCOPY . .\nEXPOSE 8080\nCMD ["python", "serve.py", "--host", "0.0.0.0", "--port", "8080"]\n')
    (output / '.dockerignore').write_text('__pycache__/\n')
    (output / 'README.md').write_text(
        '# Zephyr recorded demo deployment\n\n'
        'Run `python serve.py`, then open http://127.0.0.1:8780/. '
        'The original UI and all bundled aircraft previews remain available.\n\n'
        'Use Previous runs to switch between the included recorded scenarios.\n\n'
        'This is explicitly a recorded sedan result. Fresh inference and Nemotron '
        'calls remain in the local workstation app; deployment needs no GPU or credentials. '
        'Interactive compute requests explain this limit.\n\n'
        'To host the prepared bundle: `docker build -t zephyr-demo .`, then '
        '`docker run --rm -p 8080:8080 zephyr-demo`. Provide HTTPS using your host. '
        'No hosting service is provisioned by this package command.\n\n'
        'Aircraft, data and model limitations and source credits remain in the app. '
        'DrivAerML geometry attribution and license text are included in licenses/ '
        'and in the candidate download. '
        'A predicted drag reduction is not physical validation.\n', encoding='utf-8')
    manifest = {'createdAt': utc(), 'defaultRunId': args.run_id, 'runIds': run_ids, 'routes': routes,
        'mode': 'recorded-only', 'credentialsIncluded': False,
        'files': {str(p.relative_to(output)).replace('\\', '/'): _file_sha256(p)
                  for p in sorted(output.rglob('*')) if p.is_file()}}
    save(output / 'manifest.json', manifest)
    print(output)


if __name__ == '__main__': main()
