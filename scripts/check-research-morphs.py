"""Check the production morphs without changing them or observing forces."""
import argparse
import numpy as np
import pyvista as pv
from zephyr.local.cars import mesh_path
from zephyr.research.morphs import SedanMorphs
from zephyr.research.policy import POLICY
from zephyr.research.study import sample_parameters
from zephyr.research.runtime import save, source_hashes, utc


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True)
    p.add_argument('--samples', type=int, default=30)
    args = p.parse_args()
    if args.samples < 1: p.error('Use at least one sample')
    m = SedanMorphs(pv.read(mesh_path('drivaer-1')))
    box = {'min': [-1.5, -1.4, -.32], 'max': [5, 1.4, 1.4]}
    rows = []
    for index, params in enumerate(sample_parameters(31092026, args.samples, lhs=True)):
        c = m.deform(params)
        checks = m.validate(c, POLICY, box)
        rows.append({'index': index, 'parametersMm': params, 'checks': checks,
            'maximumMm': float(np.linalg.norm(c.points-m.points, axis=1).max()*1000),
            'passed': all(v['status'] == 'passed' for v in checks.values())})
    save(args.output, {'createdAt': utc(), 'sources': source_hashes(),
        'fragileProtection': m.fragile_regions, 'fixedVertices': int(m.protected.sum()),
        'scope': 'Geometry only; includes exact intersection checks on eligible meshes.', 'samples': rows})
    print(f'{sum(r["passed"] for r in rows)}/{len(rows)} legal proposals; other proposals refused before inference')


if __name__ == '__main__': main()
