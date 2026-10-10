"""Run the prepared independent pair in Linux/OpenFOAM; standard library only.

Usage: python3 run-sedan-cfd.py
       --live --directory /path/to/study/cfd
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    tmp = path.with_suffix('.tmp'); tmp.write_text(json.dumps(data, indent=2, allow_nan=False)); tmp.replace(path)


def replace_one(text, pattern, replacement):
    result, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1: raise ValueError('CFD template does not match expected structure: ' + pattern)
    return result


def setup(root, plan, name, levels):
    template = Path('/usr/share/doc/openfoam-examples/examples/incompressible/simpleFoam/motorBike')
    root.mkdir(exist_ok=False)
    for folder in ('system', 'constant', '0.orig'):
        shutil.copytree(template / folder, root / ('0' if folder == '0.orig' else folder))
    for path in root.rglob('*.gz'):
        path.with_suffix('').write_bytes(gzip.decompress(path.read_bytes()))
    shutil.copyfile(root.parents[1] / plan['files'][name]['file'], root / 'constant/triSurface/zephyr.stl')
    snappy = root / 'system/snappyHexMeshDict'; text = snappy.read_text()
    text = text.replace('motorBike.obj', 'zephyr.stl').replace('addLayers       true', 'addLayers       false')
    text = replace_one(text, r'features\s*\(.*?\);', 'features ();')
    text = text.replace('level (5 6)', f'level ({levels[0]} {levels[1]})')
    text = text.replace('levels ((1E15 4))', 'levels ((1E15 2))')
    text = text.replace('min  (-1.0 -0.7 0.0)', 'min (-2 -2 0)').replace('max  ( 8.0  0.7 2.5)', 'max (10 2 3)')
    text = text.replace('maxLocalCells 100000', 'maxLocalCells 4000000').replace('maxGlobalCells 2000000', 'maxGlobalCells 4000000')
    text = text.replace('explicitFeatureSnap true', 'explicitFeatureSnap false').replace('implicitFeatureSnap false', 'implicitFeatureSnap true')
    snappy.write_text(text)
    # Stricter than the tutorial's boundary-skew limit of 20: checkMesh uses 4.
    # Enforce quality during snapping instead of ignoring a failed final audit.
    quality = root / 'system/meshQualityDict'
    quality.write_text(quality.read_text()+'\nmaxBoundarySkewness 3.5;\nmaxInternalSkewness 3.5;\n')
    block = root / 'system/blockMeshDict'
    text = replace_one(block.read_text(), r'vertices\s*\(.*?\);',
        'vertices ((-15 -10 0) (35 -10 0) (35 10 0) (-15 10 0) (-15 -10 10) (35 -10 10) (35 10 10) (-15 10 10));')
    block.write_text(text.replace('(20 8 8)', '(50 20 10)'))
    initial = root / '0/include/initialConditions'; text = initial.read_text()
    text = text.replace('(20 0 0)', f"({plan['conditions']['velocityMps']} 0 0)").replace('0.24', '0.2269').replace('1.78', '1.37')
    initial.write_text(text)
    control = '''FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }
application simpleFoam; startFrom startTime; startTime 0; stopAt endTime;
endTime ITERATIONS; deltaT 1; writeControl timeStep; writeInterval ITERATIONS;
purgeWrite 1; writeFormat binary; writePrecision 10; writeCompression off;
timeFormat general; timePrecision 6; runTimeModifiable false;
functions { aerodynamicForces { type forces; libs ("libforces.so");
patches ("motorBike.*"); rho rhoInf; rhoInf DENSITY; CofR (0 0 0);
writeControl timeStep; writeInterval 1; log true; } }
'''.replace('ITERATIONS', str(plan['iterations'])).replace('DENSITY', str(plan['conditions']['densityKgM3']))
    (root / 'system/controlDict').write_text(control)
    viscosity = root / 'constant/transportProperties'
    if viscosity.exists():
        viscosity.write_text(re.sub(r'(nu\s+(?:\[[^\]]+\]\s*)?)[\d.eE+-]+\s*;', r'\g<1>1.507e-5;', viscosity.read_text()))
    return {str(p.relative_to(root)): sha(p) for folder in ('system', '0', 'constant')
            for p in (root / folder).rglob('*') if p.is_file() and p.suffix != '.gz'}


def run_case(root, plan):
    entry = {'status': 'running', 'commands': [], 'meshPassed': False, 'converged': False}
    for cmd in ('blockMesh', 'snappyHexMesh', 'checkMesh', 'simpleFoam'):
        started = time.monotonic()
        with (root / ('log.' + cmd)).open('w') as log:
            try:
                result = subprocess.run([cmd, *(['-overwrite'] if cmd == 'snappyHexMesh' else [])], cwd=root,
                    stdout=log, stderr=subprocess.STDOUT, timeout=plan['maximumCommandSeconds'])
                code = result.returncode
            except subprocess.TimeoutExpired: code = 124
        entry['commands'].append({'command': cmd, 'exitCode': code, 'seconds': time.monotonic() - started})
        save(root / 'receipt.json', entry)
        print(root.name, cmd, code, flush=True)
        if code:
            entry['status'] = 'failed'; break
        if cmd == 'checkMesh':
            entry['meshPassed'] = 'Mesh OK.' in (root / 'log.checkMesh').read_text()
            if not entry['meshPassed']:
                entry['status'] = 'mesh-quality-failed'; break
    else:
        files = sorted((root / 'postProcessing').glob('aerodynamicForces/*/force.dat'))
        if files:
            # OpenFOAM forces force.dat: time, TOTAL xyz, pressure xyz, viscous xyz.
            numbers = [re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', line)
                       for line in files[-1].read_text().splitlines() if line and not line.startswith('#')]
            drag = [float(row[1]) for row in numbers if len(row) >= 10]
            tail = drag[-plan['forceTailSamples']:]
            if tail:
                mean, spread = sum(tail)/len(tail), max(tail)-min(tail)
                entry.update(dragN=mean, tailRangeN=spread, sampleCount=len(drag),
                    converged=len(tail) == plan['forceTailSamples'] and mean > 0 and spread/mean < plan['forceTailRelativeRange'])
        entry['status'] = 'complete'
    save(root / 'receipt.json', entry)
    return entry


def reuse_baseline(case, definitions, plan, cache, level):
    """Reuse only exactly matching inputs with every cached output hash verified."""
    cached_plan = json.loads((cache/'plan.json').read_text())
    keys = ('planSha256', 'baselineMeshHash', 'conditions', 'groundTranslationM',
            'wheelGroundGapM', 'solver', 'levels', 'iterations', 'forceTailSamples',
            'forceTailRelativeRange', 'maximumCommandSeconds', 'maximumGlobalCells')
    if any(plan.get(k) != cached_plan.get(k) for k in keys):
        raise ValueError('Baseline cache uses a different CFD protocol')
    if plan['files']['baseline']['sha256'] != cached_plan['files']['baseline']['sha256']:
        raise ValueError('Baseline STL differs from the cache')
    source = cache/level/'baseline'
    if definitions != json.loads((source/'input-receipt.json').read_text()):
        raise ValueError('Baseline solver inputs differ from cache')
    manifest = json.loads((source/'case-files.json').read_text())
    if manifest['runnerSha256'] != sha(Path(__file__)):
        raise ValueError('CFD runner differs from cached execution')
    for name, expected in manifest['files'].items():
        path = (source/name).resolve()
        if not path.is_relative_to(source.resolve()) or not path.is_file() or sha(path) != expected:
            raise ValueError('Cached CFD artifact missing or changed')
    shutil.copytree(source, case, dirs_exist_ok=True)
    save(case/'reuse.json', {'source': str(source), 'manifestSha256': sha(source/'case-files.json'),
                            'scope': 'Exact-input reuse of an independently computed baseline'})
    return json.loads((case/'receipt.json').read_text())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--live', action='store_true'); p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--baseline-cache', type=Path)
    args = p.parse_args()
    if not args.live: p.error('Use --live to authorize local CFD computation')
    # Debian/Ubuntu packages install binaries in /usr/bin; their upstream bashrc
    # references an absent project bin directory. Set the data paths directly.
    os.environ.setdefault('WM_PROJECT_DIR', '/usr/share/openfoam')
    os.environ.setdefault('WM_PROJECT_VERSION', 'v1912')
    os.environ.setdefault('FOAM_ETC', '/usr/share/openfoam/etc')
    root = args.directory.resolve(); plan = json.loads((root / 'plan.json').read_text())
    if (root / 'results.json').exists(): p.error('Existing CFD results are never overwritten')
    for value in plan['files'].values():
        if sha(root / value['file']) != value['sha256']: raise ValueError('Input STL changed')
    summary = {'method': 'OpenFOAM', 'planSha256': plan['planSha256'],
        'stage': plan.get('stage', 'comparison'),
        'baselineMeshHash': plan['baselineMeshHash'], 'candidateMeshHash': plan['candidateMeshHash'],
        'conditions': plan['conditions'], 'limitations': plan['limitations'], 'levels': []}
    for level, resolution in plan['levels'].items():
        (root / level).mkdir(exist_ok=False)
        row = {'name': level, 'meshPassed': True, 'converged': True, 'artifacts': {}, 'cases': {}}
        names = ('baseline',) if plan.get('stage') == 'baseline-only' else ('baseline', 'candidate')
        for name in names:
            case = root / level / name
            definitions = setup(case, plan, name, resolution)
            save(case / 'input-receipt.json', definitions)
            result = (reuse_baseline(case, definitions, plan, args.baseline_cache.resolve(), level)
                      if name == 'baseline' and args.baseline_cache else run_case(case, plan))
            row['cases'][name] = result
            save(case/'case-files.json', {'runnerSha256': sha(Path(__file__)),
                'files': {str(p.relative_to(case)): sha(p) for p in case.rglob('*')
                          if p.is_file() and p.name != 'case-files.json'}})
            row[name + 'DragN'] = result.get('dragN')
            row['meshPassed'] &= result['meshPassed']; row['converged'] &= result['converged']
            for file in [case / 'receipt.json', case / 'input-receipt.json', case/'case-files.json', *case.glob('reuse.json'), *case.glob('log.*'),
                         *case.glob('postProcessing/aerodynamicForces/*/force.dat')]:
                row['artifacts'][str(file.relative_to(root.parent))] = sha(file)
        summary['levels'].append(row); save(root / 'results.json', summary)
    if plan.get('stage') != 'baseline-only': save(root.parent / 'independent.json', summary)


if __name__ == '__main__': main()
