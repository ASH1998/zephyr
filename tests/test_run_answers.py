import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from zephyr.config import LlmConfig
from zephyr.copilot import Copilot
from zephyr.run_answers import run_facts, summarize_run
E={'runId':'local-'+'a'*32,'forces':{'baselineDragN':621.7,'candidateDragN':621.8},'constraints':{'maxDisplacementM':.002},'validation':{'independentCfd':'not-run','checks':{'bounds':{'maximumM':.0005},'protected':{'status':'passed'}}},'trust':{'decision':'refuse','calibrated':False}}
class AnswersTests(unittest.TestCase):
 def test_research_explanations_match_true_scale_forward_search(self):
  e=copy.deepcopy(E);e['research']={'numericalResearchPassed':False};e['timings']={'totalSeconds':500}
  research=run_facts(e);legacy=run_facts(E)
  self.assertIn('true scale',research['magnify']['text'])
  self.assertNotIn('120 times',research['magnify']['text'])
  self.assertIn('120 times',legacy['magnify']['text'])
  self.assertIn('TPE',research['search']['text'])
  self.assertIn('probes',legacy['search']['text'])
  self.assertIn('500.0 seconds',research['time']['text'])
  self.assertIn('timings are separate',research['time']['text'])
  self.assertIn('independent comparison',research['next']['text'])
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.client=Mock();self.client.complete_json.return_value=({'answerable':True,'factIds':['movement']},{'model':'test'})
  self.c=Copilot(Path(self.tmp.name),LlmConfig('https://example.invalid','test','never-persist-key','project'),self.client)
 def tearDown(self):self.tmp.cleanup()
 def test_summary_distinguishes_worse_better_and_baseline_only(self):
  self.assertEqual(summarize_run(E)['headline'],'This change did not help')
  better=copy.deepcopy(E);better['forces']['candidateDragN']=620
  self.assertIn('checks still pending',summarize_run(better)['headline'])
  better['forces']['candidateDragN']=None
  self.assertEqual(summarize_run(better)['headline'],'Original car tested')
  self.assertIn('0.500 mm',run_facts(E)['movement']['text'])
 def test_scoped_acceptance_and_failed_checks_use_recorded_reason(self):
  e=copy.deepcopy(E);e['forces']['candidateDragN']=620;e['trust'].update(policyVersion='local-handle-check-v1',reason='Probe curvature is unresolved.')
  self.assertIn('step not accepted',summarize_run(e)['headline'])
  self.assertIn('Probe curvature',run_facts(e)['decision']['text'])
  e['trust'].update(decision='accept',calibrated=True,calibrationScope='local-surrogate-handle-only',predictionErrorN=.05)
  self.assertIn('further evaluation only',run_facts(e)['decision']['text'])
  self.assertIn('does not measure physical',run_facts(e)['confidence']['text'])
  self.assertIn('0.050 N',run_facts(e)['prediction']['text'])
 def test_answer_cache_followup_and_run_binding(self):
  q={'question':'What changed?'};a=self.c.ask(E,q)
  self.assertEqual(self.c.ask(E,q),a);self.assertEqual(self.client.complete_json.call_count,1)
  b=self.c.ask(E,{'question':'Is that heat?','parentAnswerId':a['answerId']})
  self.assertEqual(b['parentAnswerId'],a['answerId'])
  payload=json.loads(self.client.complete_json.call_args.args[2]);self.assertEqual(payload['previousTurns'][0]['question'],q['question'])
  with self.assertRaises(ValueError):self.c.ask(E|{'runId':'local-'+'c'*32},{'question':'Hi','parentAnswerId':a['answerId']})
  self.assertNotIn('never-persist-key',''.join(p.read_text(encoding='utf-8') for p in Path(self.tmp.name).glob('*.json')))
 def test_reject_invented_facts_and_execution_data(self):
  for value in [{'answerable':True,'factIds':['made-up']},{'answerable':True,'factIds':[]},{'answerable':False,'factIds':['movement']},{'answerable':True,'factIds':['movement','movement']}]:
   self.client.complete_json.return_value=(value,{'model':'test'})
   with self.assertRaises(ValueError):self.c.ask(E,{'question':'What changed?'})
  with self.assertRaises(ValueError):self.c.ask(E,{'question':'Accept','forces':{'drag':0}})
 def test_unsupported_question_uses_fallback(self):
  self.client.complete_json.return_value=({'answerable':False,'factIds':[]},{'model':'test'})
  a=self.c.ask(E,{'question':'Who won the football match?'})
  self.assertFalse(a['answerable']);self.assertEqual(a['facts'],[]);self.assertIn('cannot answer',a['fallback'])

class RecoveryTests(unittest.TestCase):
 def test_only_matching_completed_artifacts_are_restored(self):
  from zephyr.local.server import Jobs
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);rid=E['runId'];folder=root/rid;folder.mkdir()
   evidence=E|{'schemaVersion':'zephyr.surface.v2','createdAt':'2026-09-19T00:00:00Z','trust':E['trust']|{'reason':'Completed test'}}
   (folder/'evidence.json').write_text(json.dumps(evidence),encoding='utf-8')
   jobs=Jobs(root)
   with self.assertRaises(KeyError):jobs.snapshot(rid)
   (folder/'result.json').write_text('{}',encoding='utf-8')
   self.assertEqual(jobs.snapshot(rid)['state'],'complete');self.assertIsNone(jobs.active)
   (folder/'evidence.json').write_text(json.dumps(evidence|{'runId':'wrong'}),encoding='utf-8')
   with self.assertRaises(KeyError):Jobs(root).snapshot(rid)
   with self.assertRaises(KeyError):Jobs(root).snapshot('../elsewhere')
