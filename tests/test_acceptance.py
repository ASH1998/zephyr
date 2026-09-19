import unittest
from unittest.mock import patch
import numpy as np
import pyvista as pv
import torch
from zephyr.local.sensitivity import independent_batch_gradients, evaluate_surface
from zephyr.local.geometry import deform, propose
from zephyr.local.intersections import audit_intersections
from zephyr.local.trust import assess_probes, decide_step, calibrate_handle, REQUIRED_CHECKS


class GradientTests(unittest.TestCase):
    def test_each_batch_contributes_once_and_hook_is_removed(self):
        class Model(torch.nn.Module):
            def forward(self, inputs):
                return (inputs['geometry_coordinates'] * inputs['weight']).sum()
        model = Model()
        def upstream_loop():
            x = torch.ones((1, 2, 3), requires_grad=True)
            total = torch.zeros_like(x)
            for weight in (1., 2., 3.):
                model({'geometry_coordinates': x, 'weight': weight}).backward()
                total += x.grad
            return total
        torch.testing.assert_close(upstream_loop(), torch.full((1, 2, 3), 10.))
        with independent_batch_gradients(model):
            torch.testing.assert_close(upstream_loop(), torch.full((1, 2, 3), 6.))
        self.assertEqual(len(model._forward_pre_hooks), 0)

    def test_imported_normals_are_rebuilt_for_every_evaluation(self):
        class Fake:
            model = torch.nn.Identity()
            def __call__(self, mesh):
                self.assertion(mesh)
                return {}
        inference = Fake()
        mesh = pv.Sphere().compute_normals()
        self.assertIn('Normals', mesh.point_data)
        def check(mesh):
            self.assertNotIn('Normals', mesh.point_data)
            self.assertNotIn('Normals', mesh.cell_data)
            self.assertEqual(mesh.points.dtype, np.float64)
        inference.assertion = check
        evaluate_surface(inference, mesh)
        model = torch.nn.Identity()
        with self.assertRaises(RuntimeError):
            with independent_batch_gradients(model):
                raise RuntimeError('inference failed')
        self.assertEqual(len(model._forward_pre_hooks), 0)


class IntersectionTests(unittest.TestCase):
    def mesh(self, points):
        return pv.PolyData(np.array(points, float), [3, 0, 1, 2, 3, 3, 4, 5])
    def test_crossing_coplanar_disjoint_and_watertight(self):
        first = [[0,0,0],[2,0,0],[0,2,0]]
        for second in ([[.5,.5,-1],[.5,.5,1],[1,.5,0]], [[.2,.2,0],[.4,.2,0],[.2,.4,0]]):
            result = audit_intersections(self.mesh(first + second))
            self.assertEqual(result['status'], 'failed', result)
            self.assertEqual(result['intersectingFaces'], 2)
        self.assertEqual(audit_intersections(self.mesh(first + [[0,0,1],[2,0,1],[0,2,1]]))['status'], 'passed')
        self.assertEqual(audit_intersections(pv.Sphere())['status'], 'passed')
    def test_checker_version_mismatch_fails_closed(self):
        with patch('zephyr.local.intersections.version', return_value='other'):
            self.assertEqual(audit_intersections(pv.Sphere())['status'], 'not-run')


class TrustTests(unittest.TestCase):
    def probes(self, function=lambda x: 100 - 1000*x, repeat=100):
        h = .001
        samples = [{'amplitudeM': x, 'dragN': function(x)} for x in (h,-h,h/2,-h/2)]
        return assess_probes(100, repeat, h, samples)
    def decide(self, **changes):
        args = dict(baseline=100, actual=97.1, predicted_delta=-3., calibration=self.probes(),
                    checks={key: {'status': 'passed'} for key in REQUIRED_CHECKS})
        args.update(changes)
        return decide_step(**args)
    def test_acceptance_is_scoped_and_candidate_is_held_out(self):
        result = self.decide()
        self.assertEqual(result['decision'], 'accept')
        self.assertFalse(result['engineeringValidated'])
        self.assertAlmostEqual(result['reductionRatio'], 2.9/3)
        self.assertAlmostEqual(result['predictionErrorN'], .1)
        self.assertEqual(result['calibrationScope'], 'local-surrogate-handle-only')
    def test_refuse_worse_unresolved_unstable_bad_geometry_and_experimental(self):
        for change in (dict(actual=101), dict(actual=98), dict(predicted_delta=0),
                       dict(predicted_delta=.1), dict(actual=-1), dict(experimental=True),
                       dict(checks={'selfIntersection': {'status': 'not-run'}}),
                       dict(checks={'selfIntersection': {'status': 'failed'}}),
                       dict(checks={'selfIntersection': {'status': 'passed'}}),
                       dict(calibration=self.probes(repeat=101)),
                       dict(calibration=self.probes(lambda x: 99.8-1000*x)),
                       dict(calibration=self.probes(lambda x: 100-1000*x+1e9*x**3))):
            self.assertEqual(self.decide(**change)['decision'], 'refuse', change)
        tiny = self.decide(predicted_delta=-1e-9)
        self.assertIsNone(tiny['predictionErrorPercent'])
        self.assertIsNone(tiny['reductionRatio'])
        self.assertGreater(tiny['predictionErrorN'], 0)
    def test_repeatability_is_not_physical_uncertainty(self):
        result = self.probes()
        self.assertEqual(result['baselineRepeatDifferenceN'], 0)
        self.assertGreater(result['numericalFloorN'], 0)
        self.assertEqual(self.probes(lambda x: 100)['status'], 'failed')
    def test_full_pipeline_direction_overrides_partial_gradient(self):
        mesh = pv.Sphere()
        mesh.cell_data['geometry_sensitivity'] = np.ones((mesh.n_cells, 3))
        mesh.cell_data['smooth_sensitivity_cell'] = np.ones((mesh.n_cells, 3))
        # Positive dD/da chooses negative amplitude, regardless of displayed gradient.
        _, _, report = propose(mesh, .003, slope_n_per_m=1000)
        self.assertEqual(report['amplitudeM'], -.003)
        self.assertEqual(report['predictedDragDeltaN'], -3.)
        with self.assertRaises(ValueError): deform(mesh, .004, .003)
    def test_probe_positions_are_separate_from_candidate(self):
        mesh = pv.Sphere()
        basis_trial, _, _ = deform(mesh, .001, .003)
        direction = basis_trial.points - mesh.points
        calls = []
        def evaluate(trial, name):
            calls.append(name)
            amplitude = np.sum((trial.points-mesh.points)*direction) / np.sum(direction**2) * .001
            return np.array([100-1000*amplitude, 0., 0.])
        result = calibrate_handle(mesh, 100., .003, evaluate)
        self.assertEqual(result['status'], 'passed', result)
        self.assertEqual(len(calls), 5)
        self.assertEqual(max(abs(s['amplitudeM']) for s in result['samples']), .001)
        self.assertAlmostEqual(result['slopeNPerM'], -1000)

    def test_probe_radius_shrinks_before_any_unsafe_evaluation(self):
        mesh = pv.Sphere()
        direction = deform(mesh, .001, .003)[0].points-mesh.points
        def amplitude(trial):
            return np.sum((trial.points-mesh.points)*direction) / np.sum(direction**2) * .001
        def geometry(_base, trial, _mask, _budget):
            return {'normals': {'status': 'passed' if abs(amplitude(trial)) <= .0003 else 'failed'}}
        def evaluate(trial, _name):
            self.assertLessEqual(abs(amplitude(trial)), .0003)
            return np.array([100-1000*amplitude(trial), 0, 0])
        with patch('zephyr.local.trust.validate_geometry', side_effect=geometry):
            result = calibrate_handle(mesh, 100., .003, evaluate)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['probeRadiusM'], .00025)
        self.assertEqual(len(result['radiusAttempts']), 2)


if __name__ == '__main__':
    unittest.main()
