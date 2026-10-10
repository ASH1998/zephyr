import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock

from zephyr.local.demo import PROFILE, calibration_for_run, comparison_decision
from zephyr.local.server import Jobs, validate_request
from zephyr.local.trust import REQUIRED_CHECKS
from zephyr.run_answers import run_facts, summarize_run


class DemoTests(unittest.TestCase):
    def test_demo_omits_probes_but_full_mode_still_calls_calibration(self):
        evaluate, calibrate = Mock(), Mock(return_value={'status': 'passed'})
        result = calibration_for_run({'executionProfile': PROFILE}, None, 600, .002, evaluate, 'hood-height-v1', calibrate)
        self.assertEqual(result['status'], 'not-run')
        self.assertEqual(result['samples'], [])
        evaluate.assert_not_called(); calibrate.assert_not_called()
        self.assertEqual(calibration_for_run({}, None, 600, .002, evaluate, 'hood-height-v1', calibrate)['status'], 'passed')
        calibrate.assert_called_once_with(None, 600, .002, evaluate, 'hood-height-v1')

    def test_demo_retains_geometry_failures_and_cannot_claim_acceptance(self):
        checks = {k: {'status': 'passed'} for k in REQUIRED_CHECKS}
        trust = comparison_decision(600, 580, checks)
        self.assertFalse(trust['calibrated']); self.assertEqual(trust['decision'], 'refuse')
        self.assertFalse(trust['engineeringValidated'])
        checks['selfIntersection']['status'] = 'failed'
        self.assertIn('Geometry validation failed', comparison_decision(600, 580, checks)['reason'])
        checks.pop('selfIntersection')
        self.assertIn('incomplete', comparison_decision(600, 580, checks)['reason'])

    def test_only_server_selected_sedan_iterations_use_demo(self):
        request = {'geometryId': 'drivaer-1', 'mode': 'iteration', 'budgetMm': 2,
                   'brief': 'Reduce drag. Keep the cabin unchanged.'}
        with self.assertRaises(ValueError): validate_request(request | {'executionProfile': PROFILE})
        script = "import sys;from pathlib import Path;p=Path(sys.argv[1]);(p/'result.json').write_text('{}');(p/'evidence.json').write_text('{}')"
        with tempfile.TemporaryDirectory(dir=Path(__file__).parents[1]/'.local') as directory:
            jobs = Jobs(Path(directory), [sys.executable, '-c', script], fast_demo=True)
            try:
                for geometry, mode, expected in [('drivaer-1','iteration',PROFILE), ('drivaer-1','analysis',None), ('x57','analysis',None)]:
                    job = jobs.start(request | {'geometryId': geometry, 'mode': mode})
                    saved = json.loads((Path(directory)/job['runId']/'request.json').read_text())
                    self.assertEqual(saved.get('executionProfile'), expected)
                    deadline = time.monotonic() + 10
                    while jobs.active and time.monotonic() < deadline: time.sleep(.02)
                    self.assertIsNone(jobs.active)
            finally: jobs.close()

    def test_summary_describes_comparison_without_inventing_probe_checks(self):
        evidence = {'runId': 'local-'+'a'*32, 'executionProfile': PROFILE,
                    'forces': {'baselineDragN': 600, 'candidateDragN': 590},
                    'trust': comparison_decision(600, 590, {k:{'status':'passed'} for k in REQUIRED_CHECKS}),
                    'validation': {'geometry':'passed', 'independentCfd':'not-run', 'checks':{}},
                    'calibration': {'status':'not-run'}}
        facts = run_facts(evidence)
        self.assertIn('omitted', facts['search']['text'])
        self.assertIn('not run', facts['confidence']['text'])
        self.assertNotIn('accepted', facts['decision']['text'])
        self.assertEqual(summarize_run(evidence)['headline'], 'Lower predicted resistance')
