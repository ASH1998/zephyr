"""Smooth seven-parameter, fixed-topology sedan deformation in metres.

These are explicit spatial morphs, not a reconstruction of ANSA's unpublished
control boxes. Dataset range analogues are recorded without asserting membership.
"""
import numpy as np
from zephyr.local.geometry import smoothstep
from zephyr.local.intersections import audit_intersections

PARAMETERS = {
    'rear_taper': {'rangeMm': [-30., 30.], 'analogue': 'Rearend_tapering', 'publishedMm': [-90, 70]},
    'deck_height': {'rangeMm': [-30., 30.], 'analogue': 'Decklid_Height', 'publishedMm': [-50, 50]},
    'hood_camber': {'rangeMm': [-30., 30.], 'analogue': 'Hood_Angle', 'publishedMm': [-50, 50]},
    'nose_width': {'rangeMm': [-30., 30.], 'analogue': 'Front_Planview', 'publishedMm': [-75, 75]},
    'side_shoulders': {'rangeMm': [-20., 20.], 'analogue': 'Vehicle_Width', 'publishedMm': [-100, 100]},
    'front_overhang': {'rangeMm': [-30., 30.], 'analogue': 'Front_Overhang', 'publishedMm': [-150, 100]},
    'rear_overhang': {'rangeMm': [-30., 30.], 'analogue': 'Rear_Overhang', 'publishedMm': [-150, 100]},
}
SOURCE = 'https://arxiv.org/html/2408.11969v2#Sx7.T5'


class SedanMorphs:
    def __init__(self, mesh):
        self.mesh = mesh.copy(deep=True)
        self.points = np.asarray(mesh.points, dtype=np.float64).copy()
        lo, hi = self.points.min(0), self.points.max(0)
        q = (self.points - lo) / np.maximum(hi - lo, 1e-12)
        x, z = q[:, 0], q[:, 2]
        rise = lambda v, a, b: smoothstep((v - a) / (b - a))
        cabin = rise(x, .12, .25) * (1 - rise(x, .80, .94))
        envelope = rise(z, .40, .60) * (1 - cabin * rise(z, .42, .60))
        front, rear = 1 - rise(x, .08, .36), rise(x, .65, .96)
        side = rise(x, .04, .25) * (1 - rise(x, .78, .97))
        y = self.points[:, 1] / max(abs(lo[1]), abs(hi[1]))
        definitions = {
            'rear_taper': (1, -y * rear * envelope),
            'deck_height': (2, rear * envelope),
            'hood_camber': (2, front * envelope),
            'nose_width': (1, y * front * envelope),
            'side_shoulders': (1, y * side * envelope),
            'front_overhang': (0, -front * envelope),
            'rear_overhang': (0, rear * envelope),
        }
        self.bases = {}
        for name, (axis, weights) in definitions.items():
            scale = np.max(np.abs(weights))
            if scale <= 0:
                raise ValueError('Unsupported geometry: empty morph region')
            basis = np.zeros_like(self.points)
            basis[:, axis] = weights / scale
            self.bases[name] = basis
        self.protected = (z <= .40) | ((x >= .25) & (x <= .80) & (z >= .60))
        for b in self.bases.values():
            b[self.protected] = 0
        self.faces = mesh.faces.reshape(-1, 4)[:, 1:]
        self.reference = self.metrics(self.points)
        self.fragile_regions = self.protect_fragile_triangles()

    def protect_fragile_triangles(self):
        """Freeze ill-conditioned mesh patches before observing ANY forces.

        Axis endpoint tests identify fragile triangles; compact radial C2 factors
        smoothly suppress every handle there. Combined shapes still pass the full
        independent per-candidate geometry gate. No amplitude backtracking.
        """
        from zephyr.research.policy import POLICY
        na, aa, _, qa = self.reference
        failed = set()
        for name, limits in PARAMETERS.items():
            for mm in limits['rangeMm']:
                points = self.points + self.bases[name] * mm / 1000
                nb, ab, _, qb = self.metrics(points)
                cosine = np.sum(na * nb, axis=1) / np.maximum(aa * ab, 1e-30)
                area = ab / np.maximum(aa, 1e-30)
                bad = ((cosine <= POLICY['minimumNormalCosine']) |
                       (area <= POLICY['areaRatio'][0]) | (area >= POLICY['areaRatio'][1]) |
                       (qb > qa * POLICY['maximumAspectGrowth']))
                failed.update(self.faces[bad].reshape(-1).tolist())
        if not failed:
            return []
        seeds = self.points[sorted(failed)]
        reflected = seeds.copy(); reflected[:, 1] *= -1
        seeds = np.unique(np.concatenate([seeds, reflected]), axis=0)
        # Connected components of nearby seed points define a small set of
        # enclosing balls. Products, unlike nearest-distance minima, remain C2.
        near = np.linalg.norm(seeds[:, None] - seeds[None, :], axis=2) <= .15
        remaining, regions = set(range(len(seeds))), []
        weight = np.ones(len(self.points))
        while remaining:
            group, pending = set(), [min(remaining)]
            while pending:
                index = pending.pop()
                if index in group:
                    continue
                group.add(index)
                pending.extend(i for i in np.flatnonzero(near[index]) if i not in group)
            remaining -= group
            selected = seeds[sorted(group)]
            centre = selected.mean(0)
            radius = float(np.linalg.norm(selected - centre, axis=1).max()) + .10
            distance = np.linalg.norm(self.points - centre, axis=1)
            weight *= smoothstep((distance - radius) / .35)
            regions.append({'centreM': centre.tolist(), 'fixedRadiusM': radius, 'transitionM': .35})
        for basis in self.bases.values():
            basis *= weight[:, None]
        self.protected |= weight == 0
        return regions

    def metrics(self, points):
        triangles = points[self.faces]
        edges = np.stack([triangles[:, 1] - triangles[:, 0],
                          triangles[:, 2] - triangles[:, 1], triangles[:, 0] - triangles[:, 2]], 1)
        lengths = np.linalg.norm(edges, axis=2)
        normals = np.cross(edges[:, 0], -edges[:, 2])
        area = np.linalg.norm(normals, axis=1)
        aspect = lengths.max(1) ** 2 / np.maximum(area, 1e-30)
        return normals, area, lengths, aspect

    def deform(self, parameters, *, allow_micro=False):
        if set(parameters) - set(PARAMETERS):
            raise ValueError('Unknown morph; roof, greenhouse and ramp edits are unsupported')
        displacement = np.zeros_like(self.points)
        for name, value in parameters.items():
            if isinstance(value, bool) or not np.isfinite(value):
                raise ValueError('Morph parameters must be finite numbers')
            low, high = PARAMETERS[name]['rangeMm']
            if not low <= value <= high:
                raise ValueError('Morph outside frozen parameter range: ' + name)
            displacement += self.bases[name] * (value / 1000)
        if allow_micro:
            peak = np.linalg.norm(displacement, axis=1).max()
            if peak > .00009 + 1e-12:
                raise ValueError('Micro perturbation exceeds 0.09 mm')
        result = self.mesh.copy(deep=True)
        result.points = self.points + displacement
        result.clear_data()
        return result

    def micro_parameters(self, rng):
        values = dict(zip(PARAMETERS, rng.uniform(-1, 1, len(PARAMETERS))))
        delta = sum(self.bases[k] * v for k, v in values.items())
        scale = .09 * rng.uniform(.1, 1.) / np.linalg.norm(delta, axis=1).max()
        return {k: float(v * scale) for k, v in values.items()}

    def validate(self, candidate, policy, box, *, intersections=True):
        checks = {}
        def add(name, passed, **measurements):
            checks[name] = {'status': 'passed' if bool(passed) else 'failed', **measurements}
        same = candidate.n_points == self.mesh.n_points and np.array_equal(candidate.faces, self.mesh.faces)
        add('topology', same)
        if not same:
            return checks
        p = np.asarray(candidate.points)
        add('finite', np.isfinite(p).all())
        if not np.isfinite(p).all():
            return checks
        add('protected', np.array_equal(p[self.protected], self.points[self.protected]), vertices=int(self.protected.sum()))
        displacement = float(np.linalg.norm(p - self.points, axis=1).max())
        add('bounds', displacement <= policy['maximumDisplacementMm'] / 1000 + 1e-12, maximumM=displacement)
        # Project-specific legal envelope plus the pinned checkpoint input box.
        margin = policy['maximumDisplacementMm'] / 1000
        add('legalEnvelope', np.all(p >= self.points.min(0) - margin) and np.all(p <= self.points.max(0) + margin))
        add('checkpointBounds', np.all(p >= box['min']) and np.all(p <= box['max']))
        na, aa, ea, qa = self.reference
        nb, ab, eb, qb = self.metrics(p)
        cosine = np.sum(na * nb, axis=1) / np.maximum(aa * ab, 1e-30)
        area, edges, quality = ab / np.maximum(aa, 1e-30), eb / np.maximum(ea, 1e-30), qb / np.maximum(qa, 1e-30)
        add('normals', np.all(ab > 1e-14) and np.all(cosine > policy['minimumNormalCosine']), minimumCosine=float(cosine.min()))
        add('triangleArea', np.all((area > policy['areaRatio'][0]) & (area < policy['areaRatio'][1])), minimumRatio=float(area.min()), maximumRatio=float(area.max()))
        add('edgeLength', np.all((edges > policy['edgeRatio'][0]) & (edges < policy['edgeRatio'][1])), minimumRatio=float(edges.min()), maximumRatio=float(edges.max()))
        add('aspectGrowth', np.all(quality <= policy['maximumAspectGrowth']), maximum=float(quality.max()))
        add('watertight', candidate.n_open_edges == self.mesh.n_open_edges == 0)
        if intersections and all(v['status'] == 'passed' for v in checks.values()):
            checks['selfIntersection'] = audit_intersections(candidate)
        else:
            checks['selfIntersection'] = {'status': 'not-run'}
        return checks


def domain_check(parameters):
    outside = [k for k, v in parameters.items() if k not in PARAMETERS or
               not np.isfinite(v) or not PARAMETERS[k]['rangeMm'][0] <= v <= PARAMETERS[k]['rangeMm'][1]]
    return {'status': 'refuse' if outside else 'range-screened-unverified',
            'trainingDistributionVerified': False, 'outside': outside, 'source': SOURCE,
            'reason': 'Local C2 morphs are analogues, not the ANSA parameterization; the sample baseline parameter vector is not established.'}
