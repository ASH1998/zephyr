import copy
from types import SimpleNamespace
import unittest
import numpy as np
import pyvista as pv
from zephyr.research.dent import dent_mesh
from zephyr.run_answers import run_facts, summarize_run


class DentTests(unittest.TestCase):
    def test_prescribed_dent_is_local_inward_bounded_and_preserves_protected_points(self):
        m = pv.Plane(center=(0, .22, .74), direction=(0, 0, 1), i_size=2, j_size=2,
                     i_resolution=20, j_resolution=20).triangulate()
        points = m.points.astype(float)
        protected = np.zeros(len(points), dtype=bool)
        protected[len(points)//2] = True
        morphs = SimpleNamespace(mesh=m, points=points, protected=protected)
        candidate = dent_mesh(morphs)
        delta = candidate.points-points
        np.testing.assert_array_equal(candidate.faces, m.faces)
        np.testing.assert_array_equal(delta[:, :2], 0)
        np.testing.assert_array_equal(delta[protected], 0)
        self.assertLess(delta[:, 2].min(), -.005)
        self.assertGreaterEqual(delta[:, 2].min(), -.012-1e-12)
        self.assertLessEqual(delta[:, 2].max(), 0)
        self.assertGreater(np.count_nonzero(np.linalg.norm(delta, axis=1)==0), len(points)*.9)
        np.testing.assert_array_equal(candidate.points, dent_mesh(morphs).points)
        for value in (0, -1, 13, float('nan'), True):
            with self.assertRaises(ValueError): dent_mesh(morphs, depth_mm=value)

    def test_dent_answers_cannot_claim_crash_inspection_or_optimization(self):
        from test_run_answers import E
        e = copy.deepcopy(E)
        e['syntheticDent'] = {'preset': {'depthMm':12}}
        facts = run_facts(e)
        self.assertIn('not a simulation of a crash', facts['decision']['text'])
        self.assertIn('No optimization', facts['search']['text'])
        self.assertIn('not implemented', facts['next']['text'])
        self.assertNotIn('smaller trial', facts['budget']['text'])
        self.assertEqual(summarize_run(e)['headline'], 'Synthetic dent: aerodynamic comparison')


if __name__ == '__main__': unittest.main()
