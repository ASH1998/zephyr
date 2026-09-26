"""Independently recheck recorded research/dent geometry and force integration."""
import argparse
import json
from pathlib import Path
import re
import numpy as np
import pyvista as pv
from omegaconf import OmegaConf
from zephyr.artifacts import _file_sha256
from zephyr.local.conversion import mesh_hash
from zephyr.research.morphs import SedanMorphs
from zephyr.research.policy import POLICY
from zephyr.research.runtime import ROOT, ASSETS, digest, save


def verify(run_id):
    if not re.fullmatch(r'local-[a-f0-9]{32}', run_id):
        raise ValueError('Expected a local run ID')
    folder = ROOT/'.local/runs'/run_id
    e = json.loads((folder/'evidence.json').read_text())
    payload = json.loads((folder/'result.json').read_text())
    assert e['runId'] == payload['runId'] == run_id
    assert e.get('research') or e.get('syntheticDent')
    assert e['trust']['decision'] == 'refuse' and e['trust']['engineeringValidated'] is False
    for key in ('forces', 'validation', 'trust', 'research', 'syntheticDent', 'provenance'):
        assert e.get(key) == payload.get(key), key
    a, b = [pv.read(folder/name) for name in ('baseline.vtk', 'evaluate.vtk')]
    for name in ('baseline.vtk', 'evaluate.vtk'):
        assert _file_sha256(folder/name) == e['artifacts'][name]['sha256']
    assert mesh_hash(a) == e['provenance']['meshHash']
    assert mesh_hash(b) == e['provenance']['candidateMeshHash']
    checker = SedanMorphs(a)
    config = OmegaConf.load(ASSETS/'config.yaml')
    checks = checker.validate(b, {**POLICY, 'maximumDisplacementMm': e['constraints']['maxDisplacementM']*1000},
                              OmegaConf.to_container(config.data.bounding_box_surface))
    assert all(v['status'] == 'passed' for v in checks.values()), checks
    assert abs(checks['bounds']['maximumM']-e['validation']['checks']['bounds']['maximumM']) < 1e-12
    forces = {}
    for key, mesh in (('baseline', a), ('candidate', b)):
        clean = pv.PolyData(mesh.points, mesh.faces)
        area = clean.compute_cell_sizes(length=False, area=True, volume=False).cell_data['Area']
        integrated = np.sum(area[:, None]*(-clean.cell_normals*mesh.cell_data['pred_surf_pressure'][:, None]
                                          -mesh.cell_data['pred_surf_wall_shear_stress']), axis=0)
        recorded = e['forces'][key+'DragN']
        error = abs(float(integrated[0])-recorded)
        tolerance = 32*np.finfo(np.float32).eps*max(abs(recorded), 1.)
        assert error < tolerance, (key, error, tolerance)
        assert float(mesh.field_data['aerodynamic_force'][0]) == recorded
        assert e['airflow'][key]['meshHash'] == mesh_hash(mesh)
        forces[key] = {'recordedN': recorded, 'reintegratedN': float(integrated[0]),
                       'differenceN': error, 'toleranceN': float(tolerance)}
    if e.get('syntheticDent'):
        scenario = json.loads((folder/'scenario.json').read_text())
        sha = scenario.pop('scenarioSha256')
        assert digest(scenario) == sha == e['syntheticDent']['scenarioSha256']
    return {'runId':run_id, 'status':'passed', 'geometry':checks, 'forceReintegration':forces,
            'evidenceSha256':_file_sha256(folder/'evidence.json'),
            'resultSha256':_file_sha256(folder/'result.json'),
            'verificationSourceSha256':_file_sha256(Path(__file__))}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_ids', nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    results = [verify(rid) for rid in args.run_ids]
    save(args.output, results)
    print(json.dumps([{'runId':r['runId'], 'status':r['status']} for r in results]))
