import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import pyvista as pv
from zephyr.research.policy import POLICY, noise_summary, decision, aerodynamic_power
from zephyr.research.morphs import PARAMETERS, SedanMorphs, domain_check
from zephyr.research.runtime import Evidence, digest, save
from zephyr.research.study import sample_parameters
from zephyr.research.advisor import validate_advice


class ResearchPolicyTests(unittest.TestCase):
    def test_noise_is_predeclared_and_never_zero(self):
        result = noise_summary([600.] * 5, [600.] * 10)
        self.assertGreater(result['operationalSigmaN'], 0)
        self.assertEqual(result['requiredReductionN'], 6.)
        changed = noise_summary([600.] * 5, [598., 602.] * 5)
        self.assertGreater(changed['requiredReductionN'], 6.)
        for values in ([600.] * 9, [float('nan')] * 10):
            with self.assertRaises(ValueError): noise_summary([600.] * 5, values)

    def test_strict_thresholds_controls_and_missing_domain_fail_closed(self):
        n = noise_summary([600.] * 5, [600.] * 10)
        args = (n, [580.] * 200, [590.] * 200, [580.] * 3)
        result = decision(*args, geometry_passed=True)
        self.assertTrue(result['numericalResearchPassed'])
        self.assertFalse(result['accepted'])
        self.assertFalse(result['engineeringValidated'])
        self.assertEqual(set(result['failedChecks']), {'trainingDistribution', 'independentComparison'})
        self.assertFalse(decision(n, [594.] * 200, [600.] * 200, [594.] * 3, geometry_passed=True)['checks']['moreThanOnePercent'])
        self.assertFalse(decision(n, [580.] * 199, [590.] * 200, [580.] * 3, geometry_passed=True)['checks']['equalBudget'])
        self.assertFalse(decision(n, [580.] * 200, [579.] * 200, [580.] * 3, geometry_passed=True)['checks']['beatsRandom'])
        self.assertFalse(decision(n, [580.] * 200, [590.] * 200, [580., 581., 580.], geometry_passed=True)['checks']['repeatable'])

    def test_power_shows_speed_scaling(self):
        value = aerodynamic_power(600., 580., 140.0004)
        self.assertAlmostEqual(value['savingW'], 20 * 38.889)
        slower = aerodynamic_power(600., 580., 70.0002)
        self.assertAlmostEqual(slower['savingW'], value['savingW'] / 8)
        with self.assertRaises(ValueError): aerodynamic_power(600., 580., float('nan'))

    def test_sampling_is_repeatable_and_control_is_independent(self):
        a, b = sample_parameters(12, 100, True), sample_parameters(13, 100)
        self.assertEqual(a, sample_parameters(12, 100, True))
        self.assertNotEqual(a, b)
        for name, definition in PARAMETERS.items():
            low, high = definition['rangeMm']
            strata = sorted(int((row[name] - low) / (high - low) * 100) for row in a)
            self.assertEqual(strata, list(range(100)))


class ResearchMorphTests(unittest.TestCase):
    def setUp(self):
        mesh = pv.Sphere(theta_resolution=32, phi_resolution=24).scale([4.7, 2., 1.5])
        self.morphs = SedanMorphs(mesh)

    def test_combined_morph_is_fixed_topology_and_preserves_cabin(self):
        params = {name: 10. for name in PARAMETERS}
        candidate = self.morphs.deform(params)
        self.assertTrue(np.array_equal(candidate.faces, self.morphs.mesh.faces))
        self.assertTrue(np.array_equal(candidate.points[self.morphs.protected], self.morphs.points[self.morphs.protected]))
        self.assertGreater(np.linalg.norm(candidate.points - self.morphs.points, axis=1).max(), .01)
        for params in ({'roof_camber': 1.}, {'rear_taper': 50.}, {'hood_camber': float('nan')}):
            with self.assertRaises(ValueError): self.morphs.deform(params)

    def test_noise_is_smooth_and_bounded(self):
        for _ in range(10):
            p = self.morphs.micro_parameters(np.random.default_rng(_))
            target = self.morphs.deform(p, allow_micro=True)
            self.assertLessEqual(np.linalg.norm(target.points - self.morphs.points, axis=1).max(), .00009 + 1e-12)

    def test_domain_screen_is_not_a_training_membership_claim(self):
        self.assertFalse(domain_check({'rear_taper': 20.})['trainingDistributionVerified'])
        self.assertEqual(domain_check({'rear_taper': 40.})['status'], 'refuse')

    def test_intersections_are_required_for_validity(self):
        c = self.morphs.deform({})
        checks = self.morphs.validate(c, POLICY, {'min': [-5, -5, -5], 'max': [5, 5, 5]})
        self.assertTrue(all(v['status'] == 'passed' for v in checks.values()), checks)
        c.points[0] = [float('nan')] * 3
        self.assertEqual(self.morphs.validate(c, POLICY, {'min': [-5]*3, 'max': [5]*3})['finite']['status'], 'failed')


class ResearchEvidenceTests(unittest.TestCase):
    def test_changed_plan_and_records_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'records').mkdir()
            plan = {'policy': copy.deepcopy(POLICY)}
            save(root / 'plan.json', plan); (root / 'plan.sha256').write_text(digest(plan))
            e = Evidence(root); e.append({'id': 'test', 'dragN': 600.})
            self.assertEqual(e.records()[0]['dragN'], 600.)
            with self.assertRaises(ValueError): e.append({'id': 'test'})
            file = root / 'records/test.json'; row = json.loads(file.read_text()); row['dragN'] = 1.; save(file, row)
            with self.assertRaises(ValueError): e.records()
            plan['policy']['minimumReductionFraction'] = 0.; save(root / 'plan.json', plan)
            with self.assertRaises(ValueError): Evidence(root)


class ResearchAdvisorTests(unittest.TestCase):
    def test_model_cannot_expand_user_limits_or_invent_grounding(self):
        brief = 'Reduce drag. Keep the cabin unchanged. Maximum movement 2 mm.'
        value = {'status': 'ready', 'reason': 'Explore bounded shapes', 'decisions': [
            {'parameter': k, 'action': 'explore', 'range': 'full', 'quote': brief, 'evidenceIds': []}
            for k in PARAMETERS]}
        result = validate_advice(value, brief, {'history': []})
        self.assertTrue(all(v == [-2., 2.] for v in result['searchSpace'].values()))
        self.assertEqual(result['maximumDisplacementMm'], 2.)
        for limit in ('Maximum displacement: 1 mm.', 'At most 1 millimetre.', 'No more than 1 mm.', 'Max movement = 1 mm.'):
            bounded = copy.deepcopy(value)
            for item in bounded['decisions']: item['quote'] = limit
            self.assertTrue(all(v == [-1., 1.] for v in validate_advice(bounded, limit, {'history': []})['searchSpace'].values()))
        for field, invalid in [('parameter', 'roof'), ('evidenceIds', ['invented-run']), ('quote', 'not in brief')]:
            corrupted = copy.deepcopy(value); corrupted['decisions'][0][field] = invalid
            with self.assertRaises(ValueError): validate_advice(corrupted, brief, {'history': []})
        value['status'] = 'refuse'
        with self.assertRaises(ValueError): validate_advice(value, brief, {'history': []})
        value['decisions'] = []
        self.assertEqual(validate_advice(value, brief, {'history': []})['searchSpace'], {})


class ResearchSearchTests(unittest.TestCase):
    def test_resume_preserves_proposals_and_equal_forward_budgets(self):
        from zephyr.research.study import search
        class FakeEvidence:
            def __init__(self, root):
                self.root = root; self.rows = []; self.plan_hash = 'test'
                self.plan = {'seed': 42, 'policy': {**POLICY, 'lhsCandidates': 2,
                    'adaptiveCandidates': 2, 'randomCandidates': 4, 'maximumProposalsPerArm': 20}}
            def records(self): return self.rows
        def evaluate(runtime, evidence, identifier, arm, parameters):
            row = {'id': identifier, 'arm': arm, 'parametersMm': parameters,
                   'status': 'evaluated', 'dragN': 600 + sum(v*v for v in parameters.values())}
            evidence.rows.append(row); return row
        with tempfile.TemporaryDirectory() as tmp, patch('zephyr.research.study.verified_noise'), patch('zephyr.research.study.evaluate_candidate', side_effect=evaluate):
            root = Path(tmp); (root/'one').mkdir(); (root/'two').mkdir()
            complete, resumed = FakeEvidence(root/'one'), FakeEvidence(root/'two')
            search(complete, None)
            search(resumed, None, evaluation_limit=3)
            self.assertEqual(len(resumed.rows), 3)
            search(resumed, None)
            self.assertEqual(complete.rows, resumed.rows)
            self.assertEqual(sum(r['arm']=='random' for r in complete.rows), 4)
            self.assertEqual(sum(r['arm'] in ('lhs','tpe') for r in complete.rows), 4)


if __name__ == '__main__':
    unittest.main()
