"""Select an explicitly paused study candidate without relaxing research gates."""
from zephyr.research.runtime import digest, save, utc
from zephyr.research.study import verified_noise


def paused_selection(evidence, candidate_id):
    if not (evidence.root / 'STOP').is_file():
        raise ValueError('Stop the search before selecting a provisional demo')
    rows = evidence.records()
    candidates = [r for r in rows if r['id'] == candidate_id and
                  r['arm'] in ('lhs', 'tpe') and r['status'] == 'evaluated']
    if len(candidates) != 1:
        raise ValueError('Select one saved, evaluated optimization candidate')
    winner = candidates[0]
    required = ('topology', 'finite', 'protected', 'bounds', 'normals', 'triangleArea',
                'edgeLength', 'aspectGrowth', 'watertight', 'legalEnvelope',
                'checkpointBounds', 'selfIntersection')
    if any(winner['checks'].get(k, {}).get('status') != 'passed' for k in required):
        raise ValueError('Selected candidate has incomplete geometry checks')
    counts = {arm: sum(r['arm'] == arm and r['status'] == 'evaluated' for r in rows)
              for arm in ('lhs', 'tpe', 'random', 'confirm')}
    result = {'createdAt': utc(), 'planSha256': evidence.plan_hash,
              'status': 'paused-by-user', 'accepted': False, 'engineeringValidated': False,
              'winner': winner, 'noise': verified_noise(evidence), 'phaseCounts': counts,
              'sourceRecords': {r['id']: r['recordSha256'] for r in rows},
              'selectionReason': 'User selected the saved approximately 3.33% candidate for the demo and stopped further optimization.',
              'decision': {'numericalResearchPassed': False,
                           'failedChecks': ['searchStoppedEarly', 'matchedControlsIncomplete',
                                            'finalistRepeatsIncomplete', 'trainingDistributionUnverified',
                                            'independentCandidateComparisonNotRun']},
              'independentComparison': {'status': 'not-run', 'passed': False}}
    result['selectionSha256'] = digest(result)
    # A receipt is separate from the immutable experiment and its original policy.
    save(evidence.root / ('demo-selection-' + candidate_id + '.json'), result)
    return result
