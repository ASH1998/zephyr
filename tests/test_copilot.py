import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from zephyr.config import LlmConfig
from zephyr.copilot import Copilot, HANDLE, canonical_request, validate_interpretation, evidence_facts

REQUEST={'geometryId':'drivaer-1','budgetMm':3.6,'brief':'Reduce drag. Keep the cabin unchanged.','mode':'iteration'}
VALUE={'status':'ready','objective':'reduce_drag','protectedRegions':['cabin'],'handle':HANDLE,'requestedMaxMm':None,'evidenceQuotes':['Reduce drag.'],'message':'Reduce drag with the fixed rear taper and cabin lock.'}
META={'model':'test-model','seconds':.01,'usage':{'total_tokens':10}}

class CopilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).parents[1]/'.local')
        self.client=Mock();self.client.complete_json.return_value=(copy.deepcopy(VALUE),META)
        self.copilot=Copilot(Path(self.tmp.name),LlmConfig('https://example.invalid','test-model','never-persist-this-key','project'),self.client)
    def tearDown(self):self.tmp.cleanup()
    def test_cached_server_owned_plan_and_exact_binding(self):
        plan=self.copilot.compile(REQUEST)
        self.assertEqual(self.copilot.compile(REQUEST)['intentId'],plan['intentId'])
        self.assertEqual(self.client.complete_json.call_count,1)
        self.assertEqual(self.copilot.authorize(plan['intentId'],REQUEST)['budgetMm'],3.6)
        for patch in [{'brief':'Move the cabin'},{'budgetMm':4},{'mode':'analysis'},{'geometryId':'other'}]:
            with self.assertRaises(ValueError):self.copilot.authorize(plan['intentId'],REQUEST|patch)
        with self.assertRaises(ValueError):self.copilot.authorize('intent-unknown',REQUEST)
        stored=next(Path(self.tmp.name).glob('*.json')).read_text()
        self.assertNotIn('never-persist-this-key',stored)
        self.assertNotIn('project',stored)
    def test_bounds_are_literal_and_cannot_be_relaxed(self):
        req=REQUEST|{'brief':REQUEST['brief']+' Maximum 2 mm.'}
        self.assertEqual(validate_interpretation(VALUE|{'requestedMaxMm':2},req)['effectiveBudgetMm'],2)
        self.assertEqual(validate_interpretation(VALUE|{'requestedMaxMm':3},req)['status'],'clarify')
        self.assertEqual(validate_interpretation(VALUE|{'requestedMaxMm':2},REQUEST)['status'],'clarify')
        for limit in [12,-1,0]:
            req=REQUEST|{'brief':REQUEST['brief']+f' Maximum {limit} mm.'}
            self.assertEqual(validate_interpretation(VALUE|{'requestedMaxMm':limit},req)['status'],'refuse')
        req=REQUEST|{'brief':REQUEST['brief']+' 2 mm or 3 mm.'}
        self.assertEqual(validate_interpretation(VALUE,req)['status'],'clarify')
        for budget in [True,0,12,float('nan')]:
            with self.assertRaises(ValueError):canonical_request(REQUEST|{'budgetMm':budget})
    def test_model_cannot_unlock_or_add_execution_fields(self):
        for patch in [{'protectedRegions':[]},{'handle':'raw-vertices'},{'vertices':[0,1,2]},{'trustThreshold':1},{'evidenceQuotes':['invented quotation']},{'requestedMaxMm':True}]:
            with self.assertRaises(ValueError):validate_interpretation(VALUE|patch,REQUEST)
        for status in ['clarify','refuse']:
            self.client.complete_json.return_value=(VALUE|{'status':status},META)
            c=Copilot(Path(self.tmp.name),self.copilot.config,self.client)
            plan=c.compile(REQUEST)
            with self.assertRaises(ValueError):c.authorize(plan['intentId'],REQUEST)
    def test_explanation_uses_measured_facts_and_keeps_refusal(self):
        e={'runId':'local-'+'a'*32,'forces':{'baselineDragN':621.7,'candidateDragN':621.8},'constraints':{'maxDisplacementM':.002},'validation':{'independentCfd':'not-run','checks':{'bounds':{'maximumM':.00025},'protected':{'status':'passed'}}},'trust':{'decision':'refuse','reason':'Uncalibrated','calibrated':False}}
        self.client.complete_json.return_value=({'factIds':['force']},META)
        result=self.copilot.explain(e)
        self.assertEqual([f['id'] for f in result['facts']],['decision','force','cfd'])
        self.assertIn('621.700 to 621.800',result['facts'][1]['text'])
        self.assertEqual(self.copilot.explain(e),result)
        self.assertEqual(self.client.complete_json.call_count,1)
        self.client.complete_json.return_value=({'factIds':['accept']},META)
        with self.assertRaises(ValueError):self.copilot.explain(e|{'runId':'local-'+'b'*32})
        self.assertIn('no candidate',evidence_facts(e|{'forces':{'candidateDragN':None}})['analysis']['text'])

if __name__=='__main__':unittest.main()
