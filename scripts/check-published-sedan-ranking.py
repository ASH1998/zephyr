"""Geometry-selected DrivAerML ranking fallback, separate from candidate validation."""
import argparse
import csv
import gc
import hashlib
import itertools
import json
import math
from pathlib import Path
import shutil
import time
import urllib.request

from zephyr.artifacts import _file_sha256
from zephyr.research.runtime import Evidence, Runtime, digest, save, utc
from zephyr.research.study import verify_runtime

REVISION = '5d448b209bf654503c64ce7261c34fa125f46392'
# Table 5 ranges; Pitch is degrees, all other source parameters are millimetres.
WIDTHS = {'Vehicle_Length': 350, 'Vehicle_Width': 200, 'Vehicle_Height': 200,
    'Front_Overhang': 250, 'Front_Planview': 150, 'Hood_Angle': 100,
    'Approach_Angle': 70, 'Windscreen_Angle': 300, 'Greenhouse_Tapering': 200,
    'Backlight_Angle': 300, 'Decklid_Height': 100, 'Rearend_tapering': 160,
    'Rear_Overhang': 250, 'Rear_Diffusor_Angle': 100,
    'Vehicle_Ride_Height': 100, 'Vehicle_Pitch': 2}


def select_cases(parameters, available):
    rows = [{k.strip(): float(v) for k, v in row.items()}
            for row in csv.DictReader(parameters.splitlines())]
    base = next(row for row in rows if row['Run'] == 1)
    def distance(row):
        return math.sqrt(sum(((row[k]-base[k])/width)**2 for k, width in WIDTHS.items()))
    selected = sorted((row for row in rows if int(row['Run']) in available),
                      key=lambda row: (distance(row), row['Run']))[:5]
    if len(selected) != 5 or selected[0]['Run'] != 1:
        raise ValueError('Require baseline plus four available nearest variants')
    return [{'run': int(row.pop('Run')), 'normalizedDistance': distance(row),
             'parameters': row} for row in selected]


def ranking(rows):
    def ranks(values):
        return [1 + sum(v < x for v in values) + (sum(v == x for v in values)-1)/2
                for x in values]
    reference = [r['publishedForceN'] for r in rows]
    predicted = [r['dragN'] for r in rows]
    a, b = ranks(reference), ranks(predicted)
    ma, mb = sum(a)/len(a), sum(b)/len(b)
    denominator = math.sqrt(sum((v-ma)**2 for v in a)*sum((v-mb)**2 for v in b))
    correlation = sum((x-ma)*(y-mb) for x, y in zip(a, b))/denominator if denominator else None
    pairs = []
    for i, j in itertools.combinations(range(len(rows)), 2):
        actual, estimate = reference[i]-reference[j], predicted[i]-predicted[j]
        pairs.append({'runs': [rows[i]['run'], rows[j]['run']],
            'publishedDifferenceN': actual, 'predictedDifferenceN': estimate,
            'sameStrictOrder': actual*estimate > 0})
    return {'spearmanForceRankCorrelation': correlation, 'pairs': pairs,
        'concordantPairs': sum(p['sameStrictOrder'] for p in pairs),
        'allPairsAgree': len(rows) == 5 and all(p['sameStrictOrder'] for p in pairs)}


def prepare(args):
    parent = Evidence(args.parent)
    metadata = args.metadata.resolve()
    available = json.loads((metadata/'available-runs.json').read_text())
    if available['revision'] != REVISION: raise ValueError('Dataset revision mismatch')
    selected = select_cases((metadata/'geo_parameters_all.csv').read_text(), available['runIds'])
    root = args.directory.resolve(); root.mkdir(parents=True, exist_ok=False)
    for name in ('records', 'meshes', 'metadata'): (root/name).mkdir()
    for name in ('geo_parameters_all.csv', 'available-runs.json'):
        shutil.copyfile(metadata/name, root/'metadata'/name)
    plan = {key: parent.plan[key] for key in
            ('sources', 'inputSha256', 'checkpointSha256', 'studySourceSha256', 'policy')}
    plan.update(schemaVersion='zephyr.published-ranking.v1', createdAt=utc(),
        parentDirectory=str(parent.root.resolve()), parentPlanSha256=parent.plan_hash,
        dataset='neashton/drivaerml', datasetRevision=REVISION, selected=selected,
        selector='Baseline run 1 and four nearest available runs by Euclidean distance over all 16 range-normalized parameters; ties by run ID. No force-based selection.',
        parameterRangeSource='https://arxiv.org/html/2408.11969v2#Sx7.T5',
        normalizationWidths=WIDTHS, maximumForwardEvaluations=5,
        scriptSha256=_file_sha256(Path(__file__)),
        metadataSha256={p.name: _file_sha256(p) for p in (root/'metadata').iterdir()},
        rankingCriterion='All ten strict pairwise drag-force orders agree. Also report Spearman correlation and every error; no threshold changes.',
        scope='Published-geometry ranking fallback. Does not validate the custom optimized shape or establish held-out model performance.')
    save(root/'plan.json', plan); (root/'plan.sha256').write_text(digest(plan)+'\n')
    print(json.dumps({'selected': [r['run'] for r in selected], 'planSha256': digest(plan)}))


def download(url, target, limit):
    temporary = target.with_suffix(target.suffix+'.part')
    total = 0
    with urllib.request.urlopen(url, timeout=90) as response, temporary.open('wb') as output:
        while chunk := response.read(1024*1024):
            total += len(chunk)
            if total > limit: raise ValueError('Download exceeds declared size bound')
            output.write(chunk)
    temporary.replace(target)


def fetch(e):
    if (e.root/'fetch.json').exists(): raise ValueError('Fetch receipt already exists')
    if shutil.disk_usage(e.root).free < 2*1024**3:
        raise ValueError('Require 2 GiB free for the five bounded mesh downloads')
    receipt = {'createdAt': utc(), 'planSha256': e.plan_hash, 'files': {}}
    for selected in e.plan['selected']:
        run = selected['run']; prefix = f'run_{run}'
        api = f'https://huggingface.co/api/datasets/neashton/drivaerml/tree/{REVISION}/{prefix}'
        with urllib.request.urlopen(api, timeout=30) as response: entries = json.load(response)
        save(e.root/'metadata'/f'tree-{run}.json', {'url': api, 'entries': entries})
        names = [f'drivaer_{run}.stl', f'geo_ref_{run}.csv', f'force_mom_{run}.csv']
        for name in names:
            entry = next(item for item in entries if item['path'] == prefix+'/'+name)
            limit = 200*1024*1024 if name.endswith('.stl') else 1024*1024
            if entry['size'] > limit: raise ValueError('Unexpected source file size')
            target = e.root/('meshes' if name.endswith('.stl') else 'metadata')/name
            url = f'https://huggingface.co/datasets/neashton/drivaerml/resolve/{REVISION}/{prefix}/{name}'
            if run == 1 and name.endswith('.stl') and not target.exists():
                from zephyr.local.cars import mesh_path
                if _file_sha256(mesh_path('drivaer-1')) != entry['lfs']['oid']:
                    raise ValueError('Local baseline differs from published baseline')
                shutil.copyfile(mesh_path('drivaer-1'), target)
            elif not target.exists(): download(url, target, limit)
            checksum = _file_sha256(target)
            if target.stat().st_size != entry['size']: raise ValueError('Source size mismatch')
            if 'lfs' in entry:
                if checksum != entry['lfs']['oid']: raise ValueError('Published LFS hash mismatch')
            else:
                content = target.read_bytes()
                if hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest() != entry['oid']:
                    raise ValueError('Published Git blob mismatch')
            relative = target.relative_to(e.root).as_posix()
            receipt['files'][relative] = {'sha256': checksum, 'url': url, 'bytes': entry['size']}
        print(json.dumps({'run': run, 'status': 'downloaded-and-hash-verified'}), flush=True)
    save(e.root/'fetch.json', receipt)
    (e.root/'fetch.sha256').write_text(digest(receipt)+'\n')


def run(e):
    import numpy as np
    import pyvista as pv
    from zephyr.local.conversion import mesh_hash
    parent = Evidence(e.plan['parentDirectory'])
    if parent.plan_hash != e.plan['parentPlanSha256']: raise ValueError('Parent identity changed')
    rows = parent.records()
    if any(sum(r['arm'] == arm and r['status'] == 'evaluated' for r in rows) != count
           for arm, count in (('lhs', 100), ('tpe', 100), ('random', 200), ('confirm', 9))):
        raise ValueError('Finish primary optimization, controls and repeats first')
    receipt = json.loads((e.root/'fetch.json').read_text())
    if receipt['planSha256'] != e.plan_hash or digest(receipt) != (e.root/'fetch.sha256').read_text().strip():
        raise ValueError('Download evidence changed')
    for name, data in receipt['files'].items():
        if _file_sha256(e.root/name) != data['sha256']: raise ValueError('Downloaded source changed')
    existing = {row['run']: row for row in e.records()}
    with Runtime() as runtime:
        verify_runtime(e, runtime)
        for selected in e.plan['selected']:
            number = selected['run']
            if number in existing: continue
            mesh = pv.read(e.root/'meshes'/f'drivaer_{number}.stl')
            mesh.points = mesh.points.astype('float64')
            if not np.isfinite(mesh.points).all() or not mesh.is_all_triangles or mesh.n_open_edges:
                raise ValueError('Published mesh is not a finite closed triangular surface')
            if np.any(mesh.points < runtime.box['min']) or np.any(mesh.points > runtime.box['max']):
                raise ValueError('Published mesh exceeds checkpoint bounds')
            started = time.perf_counter()
            force, fields, profile = runtime.evaluate(mesh, e.plan['policy']['conditions'])
            cd = float(next(csv.DictReader((e.root/'metadata'/f'force_mom_{number}.csv').open()))['Cd'])
            area = float(next(csv.DictReader((e.root/'metadata'/f'geo_ref_{number}.csv').open()))['aRef'])
            conditions = e.plan['policy']['conditions']
            q = .5*conditions['densityKgM3']*conditions['velocityMps']**2
            row = {'id': f'published-{number:03d}', 'arm': 'published-ranking', 'run': number,
                'status': 'evaluated', 'createdAt': utc(), 'meshHash': mesh_hash(mesh),
                'sourceStlSha256': receipt['files'][f'meshes/drivaer_{number}.stl']['sha256'],
                'forceN': force, 'dragN': force[0], 'publishedCd': cd, 'referenceAreaM2': area,
                'publishedForceN': cd*q*area, 'predictedCd': force[0]/(q*area),
                'conditions': conditions, 'profile': profile, 'seconds': time.perf_counter()-started,
                'provenance': runtime.provenance}
            e.append(row); print(json.dumps({'run': number, 'dragN': force[0], 'publishedForceN': row['publishedForceN']}), flush=True)
            del mesh, fields; gc.collect()
    rows = e.records()
    summary = {'createdAt': utc(), 'planSha256': e.plan_hash, 'rows': rows,
        'ranking': ranking(rows), 'accepted': False, 'engineeringValidated': False,
        'scope': e.plan['scope'], 'checkpointSplitMembership': 'not-established',
        'limitations': ['Five geometry-nearest published variants, not custom optimization candidates.',
            'Published coefficients converted at study density, velocity and each variant frontal area.',
            'Published CFD is a comparison, not experimental ground truth. Small rank differences may be within CFD uncertainty.']}
    save(e.root/'summary.json', summary)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['prepare', 'fetch', 'run'])
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--parent', type=Path); p.add_argument('--metadata', type=Path)
    p.add_argument('--live', action='store_true')
    args = p.parse_args()
    if args.command == 'prepare':
        if not args.parent or not args.metadata: p.error('Preparation needs parent and metadata directories')
        prepare(args); return
    if not args.live: p.error('Use --live for public downloads or local inference')
    e = Evidence(args.directory)
    if e.plan['scriptSha256'] != _file_sha256(Path(__file__)): raise ValueError('Frozen benchmark implementation changed')
    for name, checksum in e.plan['metadataSha256'].items():
        if _file_sha256(e.root/'metadata'/name) != checksum: raise ValueError('Selection metadata changed')
    (fetch if args.command == 'fetch' else run)(e)


if __name__ == '__main__': main()
