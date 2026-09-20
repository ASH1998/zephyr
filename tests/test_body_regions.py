import unittest
import numpy as np
import pyvista as pv
from zephyr.local.geometry import BODY_HANDLES, body_basis, deform, rear_basis
from zephyr.local.server import preset_plan
from zephyr.copilot import validate_interpretation
from test_copilot import REQUEST, VALUE


class BodyRegionsTests(unittest.TestCase):
    def test_input_contract_distinguishes_experimental_training_extrapolation(self):
        from zephyr.local.compatibility import check_surface_input
        box={'min':[-1,-1,-1], 'max':[1,1,1]}
        mesh=pv.Sphere(radius=.5)
        self.assertTrue(check_surface_input(mesh,box,experimental=False)['withinTrainingBounds'])
        tall=mesh.scale([1,1,5])
        with self.assertRaises(ValueError): check_surface_input(tall,box,experimental=False)
        self.assertEqual(check_surface_input(tall,box,experimental=True)['status'],'experimental-outside-training-bounds')
        with self.assertRaises(ValueError): check_surface_input(pv.Plane().triangulate(),box,experimental=True)

    def test_front_side_and_vertical_tools_preserve_explicit_envelopes(self):
        mesh = pv.Sphere(theta_resolution=70, phi_resolution=70).scale([4, 1.5, 1.5])
        p = mesh.points.astype(float)
        q = (p - p.min(axis=0)) / np.ptp(p, axis=0)
        fixed = (q[:, 2] <= .46) | ((q[:, 0] >= .25) & (q[:, 0] <= .80) & (q[:, 2] >= .60))
        for handle in BODY_HANDLES[:-1]:
            basis, protected, _ = body_basis(p, handle)
            self.assertTrue(np.all(protected[fixed]))
            for sign in (-1, 1):
                candidate, mask, _ = deform(mesh, sign*.004, .004, handle)
                self.assertTrue(np.array_equal(candidate.points[mask], mesh.points[mask]))
                self.assertTrue(np.array_equal(candidate.faces, mesh.faces))
                self.assertAlmostEqual(np.linalg.norm(candidate.points-p, axis=1).max(), .004)
            # Reflection must mirror the deformation rather than favor a side.
            mirrored = p.copy(); mirrored[:, 1] *= -1
            reflected, _, _ = body_basis(mirrored, handle)
            expected = basis.copy(); expected[:, 1] *= -1
            np.testing.assert_allclose(reflected, expected, atol=1e-12)
        for h in ('nose-width-v1', 'hood-height-v1'):
            b, _, _ = rear_basis(p, h)
            self.assertTrue(np.any(np.linalg.norm(b[q[:, 0] < .3], axis=1) > 0))
        self.assertTrue(np.any(body_basis(p, 'hood-height-v1')[0][:, 2] != 0))

    def test_preset_and_llm_share_allowlist_and_aircraft_rejection(self):
        for handle in BODY_HANDLES:
            plan = preset_plan({'geometryId': 'drivaer-1', 'budgetMm': 4, 'handle': handle})
            self.assertEqual(plan['intent']['graph']['handle'], handle)
            self.assertEqual(plan['intent']['provenance']['source'], 'user-selected-preset')
            self.assertEqual(validate_interpretation(VALUE | {'handle': handle}, REQUEST)['status'], 'ready')
        for data in ({'geometryId': 'x57', 'budgetMm': 4, 'handle': 'hood-height-v1'},
                     {'geometryId': 'drivaer-1', 'budgetMm': 4, 'handle': 'raw-vertices'},
                     {'geometryId': 'drivaer-1', 'budgetMm': 40, 'handle': 'hood-height-v1'}):
            with self.assertRaises(ValueError): preset_plan(data)
        with self.assertRaises(ValueError):
            validate_interpretation(VALUE | {'handle': 'compare-body-regions'}, REQUEST)
