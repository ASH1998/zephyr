import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer

from zephyr.research.runtime import digest, save
from zephyr.research.policy import POLICY, noise_summary
from zephyr.research.morphs import PARAMETERS
from zephyr.research.advisor import validate_advice
from zephyr.research.guided import prepare, run, implementation_hashes


class GuidedExecutionTests(unittest.TestCase):
    def test_invalid_advice_is_preserved_and_provider_secrets_are_not_logged(self):
        from types import SimpleNamespace
        from zephyr.research.advisor import AdviceValidationError
        source = Path(__file__).resolve().parents[1]/'scripts/guided-sedan-search.py'
        spec = importlib.util.spec_from_file_location('guided_cli', source)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        config = SimpleNamespace(model='Nemotron', api_key='never-persist-this')
        raw = {'status': 'ready', 'decisions': [{'quote': 'invented quotation'}]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(module, 'advise', side_effect=AdviceValidationError('Ungrounded quote', raw, {'model': 'Nemotron'})):
                with self.assertRaises(AdviceValidationError):
                    module.recorded_advice(None, config, 'Keep the cabin fixed', {'history': []}, root/'invalid')
            error = json.loads((root/'invalid/error.json').read_text())
            self.assertEqual(error['uneditedResponse'], raw)
            self.assertEqual(json.loads((root/'invalid/input.json').read_text())['brief'], 'Keep the cabin fixed')
            with patch.object(module, 'advise', side_effect=RuntimeError('never-persist-this')):
                with self.assertRaises(RuntimeError):
                    module.recorded_advice(None, config, 'Keep the cabin fixed', {}, root/'provider')
            self.assertEqual(json.loads((root/'provider/error.json').read_text()), {'errorType': 'RuntimeError'})
            self.assertNotIn('never-persist-this', ''.join(p.read_text() for p in root.rglob('*.json')))

    def test_brief_ceiling_binds_combined_geometry_policy(self):
        brief = 'Reduce drag. Maximum displacement: 2 mm.'
        context = {'planSha256': 'parent', 'history': [{'id': 'history-1'}],
                   'sensitivity': {'id': 'baseline-partial-sensitivity'}}
        response = {'status': 'ready', 'reason': 'Explore small changes', 'decisions': [
            {'parameter': k, 'action': 'explore', 'range': 'full', 'quote': brief,
             'evidenceIds': ['history-1', 'baseline-partial-sensitivity']} for k in PARAMETERS]}
        advice = validate_advice(response, brief, context)
        class Parent:
            plan_hash = 'parent'
            plan = {'seed': 42, 'policy': copy.deepcopy(POLICY)}
        with tempfile.TemporaryDirectory() as tmp, patch('zephyr.research.guided.verified_noise', return_value=noise_summary([600.]*5, [600.]*10)):
            parent = Parent(); parent.root = Path(tmp)/'parent'; parent.root.mkdir()
            (parent.root/'search-complete.json').write_text('{}')
            plan = prepare(parent, Path(tmp)/'next', brief, context, advice,
                           {'passed': True, 'passedCount': 10, 'cases': [{}]*10}, budget=10)
            self.assertEqual(plan['policy']['maximumDisplacementMm'], 2.)
            self.assertEqual(parent.plan['policy']['maximumDisplacementMm'], 60.)

    def test_model_fixed_parameters_reach_actual_evaluator_and_resume_is_identical(self):
        brief = 'Explore the hood. Maximum movement 2 mm.'
        context = {'history': []}
        response = {'status': 'ready', 'reason': 'Explore hood only', 'decisions': [
            {'parameter': k, 'action': 'explore' if k == 'hood_camber' else 'fix',
             'range': 'full', 'quote': brief, 'evidenceIds': []} for k in PARAMETERS]}
        advice = validate_advice(response, brief, context)
        class Evidence:
            def __init__(self, root):
                self.root = root; root.mkdir(); self.rows = []; self.plan_hash = 'test'
                self.plan = {'guidedSources': implementation_hashes(), 'contextSha256': digest(context),
                    'qualificationSha256': digest({}), 'brief': brief, 'advice': advice, 'seed': 42,
                    'parentNoise': noise_summary([600.]*5, [600.]*10), 'policy': POLICY,
                    'budgetPerArm': 10, 'scope': 'unit test'}
                save(root/'context.json', context); save(root/'qualification.json', {})
            def records(self): return self.rows
        def evaluate(runtime, e, identifier, arm, params, save_fields=False):
            if arm in ('guided', 'guided-confirm'):
                self.assertTrue(all(v == 0 for k, v in params.items() if k != 'hood_camber'))
                self.assertLessEqual(abs(params['hood_camber']), 2.)
            row = {'id': identifier, 'arm': arm, 'parametersMm': params,
                   'status': 'evaluated', 'dragN': 600 - sum(params.values())}
            e.rows.append(row); return row
        with tempfile.TemporaryDirectory() as tmp, patch('zephyr.research.guided.verify_runtime'), patch('zephyr.research.guided.evaluate_candidate', side_effect=evaluate):
            root = Path(tmp); complete, resumed = Evidence(root/'one'), Evidence(root/'two')
            run(complete, None)
            run(resumed, None, evaluation_limit=4)
            self.assertEqual(len(resumed.rows), 4)
            run(resumed, None)
            self.assertEqual(complete.rows, resumed.rows)
            self.assertEqual(len(complete.rows), 24)
            result = json.loads((complete.root/'summary.json').read_text())
            self.assertEqual(result['counts'], {'guided': 10, 'control': 10, 'confirmations': 3})
            self.assertFalse(result['accepted'])
            resumed.plan['advice'] = copy.deepcopy(advice)
            resumed.plan['advice']['searchSpace']['hood_camber'] = [-30, 30]
            with self.assertRaises(ValueError): run(resumed, None)


class DeploymentServerTests(unittest.TestCase):
    def test_recorded_routes_download_and_compute_refusal(self):
        source = Path(__file__).resolve().parents[1]/'scripts/serve-sedan-demo.py'
        spec = importlib.util.spec_from_file_location('recorded_server', source)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root/'web').mkdir(); (root/'web/index.html').write_text('<p>Original UI</p>')
            (root/'evidence').mkdir(); (root/'evidence/result.json').write_text('{"source":"recorded"}')
            (root/'evidence/candidate.zip').write_bytes(b'test-archive')
            (root/'private.txt').write_text('not served')
            routes = {'/api/runs/test/result': 'evidence/result.json', '/api/runs/test/candidate.zip':'evidence/candidate.zip'}
            server = ThreadingHTTPServer(('127.0.0.1', 0), module.handler(root, routes, 'test'))
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            base = 'http://127.0.0.1:'+str(server.server_port)
            try:
                with urlopen(base) as response:
                    self.assertTrue(response.url.endswith('/?replay=test'))
                    self.assertIn(b'Original UI', response.read())
                with urlopen(base+'/api/runs/test/result') as response:
                    self.assertEqual(json.load(response), {'source': 'recorded'})
                with urlopen(base+'/api/runs/test/candidate.zip') as response:
                    self.assertEqual(response.headers['Content-Type'], 'application/zip')
                    self.assertEqual(response.read(), b'test-archive')
                for path in ('/private.txt', '/evidence/', '/api/unknown', '/../private.txt'):
                    with self.assertRaises(HTTPError) as error: urlopen(base+path)
                    self.assertEqual(error.exception.code, 404)
                with self.assertRaises(HTTPError) as error: urlopen(Request(base+'/api/runs', b'{}'))
                self.assertEqual(error.exception.code, 409)
                self.assertIn('recorded evidence', json.load(error.exception)['error'])
            finally: server.shutdown(); thread.join(); server.server_close()


class ReportCompletionTests(unittest.TestCase):
    def test_missing_second_finalist_repeat_prevents_numerical_pass(self):
        from zephyr.research.report import make_report
        class Evidence:
            plan_hash = 'test-plan'
            plan = {'policy': POLICY}
            def records(self): return self.rows
        def record(identifier, arm, drag, mesh, params):
            return {'id': identifier, 'arm': arm, 'dragN': drag, 'meshHash': mesh,
                'parametersMm': params, 'status': 'evaluated', 'recordSha256': identifier,
                'checks': {'geometry': {'status': 'passed'}}, 'domain': {'trainingDistributionVerified': False}}
        with tempfile.TemporaryDirectory() as tmp:
            e = Evidence(); e.root = Path(tmp); e.rows = [record('baseline-00', 'baseline', 600., 'base', {})]
            opt = [record(('lhs' if i<100 else 'tpe')+f'-{i:04d}', 'lhs' if i<100 else 'tpe',
                          580.+i*.01, 'mesh-'+str(i), {'sample': i}) for i in range(200)]
            e.rows += opt + [record(f'random-{i:04d}', 'random', 590.+i*.01, 'control-'+str(i), {}) for i in range(200)]
            for rank, original in enumerate(opt[:3]):
                e.rows += [record(f'confirm-{rank}-{i}', 'confirm', original['dragN'], original['meshHash'], original['parametersMm']) for i in range(3)]
            with patch('zephyr.research.report.Evidence', return_value=e), patch('zephyr.research.report.verified_noise', return_value=noise_summary([600.]*5, [600.]*10)), patch('zephyr.research.report.artifact_path', return_value=e.root/'unused.vtk'), patch('zephyr.research.report.shape_plot'), patch('zephyr.research.report.plot_search'):
                full = make_report(e.root, e.root/'report')
                self.assertTrue(full['decision']['numericalResearchPassed'])
                self.assertFalse(full['accepted'])
                self.assertEqual(len(full['finalists']), 3)
                text = (e.root/'report/README.md').read_text(encoding='utf-8')
                self.assertIn('Air density (held constant)', text)
                self.assertIn('Baseline evaluated force', text)
                opt[-1]['arm'] = 'lhs'
                wrong_phase = make_report(e.root, e.root/'wrong-phase')
                self.assertFalse(wrong_phase['decision']['numericalResearchPassed'])
                self.assertIn('phaseBudgetsComplete', wrong_phase['decision']['failedChecks'])
                self.assertEqual(wrong_phase['phaseCounts'], {'lhs': 101, 'tpe': 99})
                opt[-1]['arm'] = 'tpe'
                e.rows = [r for r in e.rows if r['id'] != 'confirm-1-2']
                incomplete = make_report(e.root, e.root/'incomplete')
                self.assertFalse(incomplete['decision']['numericalResearchPassed'])
                self.assertIn('allFinalistsRepeated', incomplete['decision']['failedChecks'])


if __name__ == '__main__': unittest.main()
