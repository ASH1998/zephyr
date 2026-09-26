import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from zephyr.research.replay import paused_selection
from zephyr.run_answers import run_facts


class PausedReplayTests(unittest.TestCase):
    def test_stopped_candidate_preserves_incomplete_claim_and_requires_checks(self):
        keys = ('topology finite protected bounds normals triangleArea edgeLength '
                'aspectGrowth watertight legalEnvelope checkpointBounds selfIntersection').split()
        row = {'id': 'tpe-0147', 'arm': 'tpe', 'status': 'evaluated',
               'recordSha256': 'a'*64, 'checks': {k: {'status': 'passed'} for k in keys}}
        with tempfile.TemporaryDirectory() as tmp, patch('zephyr.research.replay.verified_noise', return_value={}):
            e = SimpleNamespace(root=Path(tmp), plan_hash='b'*64, records=lambda: [row])
            with self.assertRaises(ValueError): paused_selection(e, row['id'])
            (e.root/'STOP').write_text('User stopped search')
            result = paused_selection(e, row['id'])
            self.assertFalse(result['accepted'])
            self.assertFalse(result['decision']['numericalResearchPassed'])
            self.assertEqual(result['phaseCounts']['random'], 0)
            self.assertNotIn('search-complete.json', [p.name for p in e.root.iterdir()])
            row['checks']['selfIntersection']['status'] = 'not-run'
            with self.assertRaises(ValueError): paused_selection(e, row['id'])
            with self.assertRaises(ValueError): paused_selection(e, 'not-found')

    def test_answers_do_not_claim_completed_controls_or_repeats(self):
        from test_run_answers import E
        e = copy.deepcopy(E)
        e['research'] = {'provisional': True, 'numericalResearchPassed': False,
                         'phaseCounts': {'lhs':100, 'tpe':90, 'random':0, 'confirm':0}}
        facts = run_facts(e)
        self.assertIn('0 random controls', facts['search']['text'])
        self.assertIn('stopped early', facts['confidence']['text'])
        self.assertIn('no further search is scheduled', facts['next']['text'])


if __name__ == '__main__': unittest.main()
