"""Supplemental, precommitted search that actually executes Nemotron's bounds.

This separate experiment never changes or substitutes for the primary 200/200
study. The model selects symbolic ranges; a deterministic optimizer picks values.
"""
from copy import deepcopy
import json
from pathlib import Path
import time
import numpy as np
from zephyr.artifacts import _file_sha256
from zephyr.research.advisor import validate_advice
from zephyr.research.runtime import Evidence, digest, save, utc, evaluate_candidate
from zephyr.research.study import verified_noise, verify_runtime, sample_parameters


def implementation_hashes():
    return {p.name: _file_sha256(p) for p in (Path(__file__), Path(__file__).with_name('advisor.py'))}


def prepare(parent, directory, brief, context, advice, qualification, budget=20):
    if not (parent.root / 'search-complete.json').exists():
        raise ValueError('Finish the primary search before preparing a follow-on')
    if not qualification.get('passed') or qualification.get('passedCount', 0) < 8 or len(qualification.get('cases', [])) != 10:
        raise ValueError('Require the recorded 8/10 advisor qualification')
    if not 10 <= budget <= 50:
        raise ValueError('Supplemental budget must be 10–50 evaluations per arm')
    checked = validate_advice(advice['response'], brief, context)
    if checked['status'] != 'ready' or checked['searchSpace'] != advice['searchSpace']:
        raise ValueError('Advisor refused or bounds were changed')
    if context['planSha256'] != parent.plan_hash:
        raise ValueError('Advisor context belongs to another study')
    citations = {i for d in advice['response']['decisions'] for i in d['evidenceIds']}
    if 'baseline-partial-sensitivity' not in citations or not citations.intersection(r['id'] for r in context['history']):
        raise ValueError('Follow-on decisions must cite both measured history and the partial sensitivity map')
    noise = verified_noise(parent)
    root = Path(directory); root.mkdir(parents=True, exist_ok=False)
    for name in ('records', 'meshes'): (root / name).mkdir()
    plan = deepcopy(parent.plan)
    plan['policy']['maximumDisplacementMm'] = min(plan['policy']['maximumDisplacementMm'], checked['maximumDisplacementMm'])
    plan.update(schemaVersion='zephyr.guided.v1', createdAt=utc(),
        parentPlanSha256=parent.plan_hash, parentDirectory=str(parent.root.resolve()),
        seed=parent.plan['seed'] + 1000, brief=brief, advice=advice,
        contextSha256=digest(context), qualificationSha256=digest(qualification),
        guidedSources=implementation_hashes(), parentNoise=noise, budgetPerArm=budget,
        maxForwardEvaluations=2*budget+4,
        sampling='Separate Nemotron-bounded TPE versus full-range uniform control; no primary-result replacement.',
        scope='Supplemental agent execution experiment. Does not establish training membership or physical validation.')
    save(root / 'plan.json', plan); (root / 'plan.sha256').write_text(digest(plan)+'\n')
    save(root / 'context.json', context); save(root / 'qualification.json', qualification)
    return plan


def run(evidence, runtime, max_seconds=7200, evaluation_limit=None):
    import optuna
    from optuna.distributions import FloatDistribution
    from optuna.trial import TrialState
    if optuna.__version__ != '4.5.0': raise ValueError('Use optuna==4.5.0')
    plan = evidence.plan
    verify_runtime(evidence, runtime)
    if plan['guidedSources'] != implementation_hashes(): raise ValueError('Guided implementation changed')
    context = json.loads((evidence.root/'context.json').read_text())
    qualification = json.loads((evidence.root/'qualification.json').read_text())
    if digest(context) != plan['contextSha256'] or digest(qualification) != plan['qualificationSha256']:
        raise ValueError('Guidance evidence changed')
    checked = validate_advice(plan['advice']['response'], plan['brief'], context)
    if checked['status'] != 'ready' or checked['searchSpace'] != plan['advice']['searchSpace']:
        raise ValueError('Guided bounds differ from validated model decisions')
    rows = {r['id']: r for r in evidence.records()}
    start, count = time.monotonic(), 0
    def evaluate(identifier, arm, params, fields=False):
        nonlocal count
        if identifier in rows:
            row = rows[identifier]
            if row['arm'] != arm or row['parametersMm'] != params or row['status'] == 'evaluation-failed':
                raise ValueError('Guided resume mismatch or failed inference')
            return row
        if ((evidence.root/'STOP').exists() or time.monotonic()-start >= max_seconds or
                evaluation_limit is not None and count >= evaluation_limit): return None
        row = evaluate_candidate(runtime, evidence, identifier, arm, params, save_fields=fields)
        count += row['status'] == 'evaluated'
        return row
    baseline = evaluate('guided-baseline', 'guided-baseline', {}, True)
    if baseline is None: return
    noise = plan['parentNoise']
    if baseline['status'] != 'evaluated' or abs(baseline['dragN']-noise['baselineMeanN']) > 2*noise['operationalSigmaN']:
        raise ValueError('Fresh baseline does not reproduce parent noise study')
    bounds = checked['searchSpace']
    distributions = {k: FloatDistribution(*v) for k, v in bounds.items() if v[0] < v[1]}
    fixed = {k: v[0] for k, v in bounds.items() if v[0] == v[1]}
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    optimizer = optuna.create_study(direction='minimize', sampler=optuna.samplers.TPESampler(seed=plan['seed'], n_startup_trials=10))
    legal, control = [], []
    for index in range(plan['policy']['maximumProposalsPerArm']):
        trial = optimizer.ask(distributions)
        row = evaluate('guided-%04d' % index, 'guided', {**fixed, **trial.params})
        if row is None: return
        if row['status'] == 'evaluated': optimizer.tell(trial, row['dragN']); legal.append(row)
        else: optimizer.tell(trial, state=TrialState.FAIL)
        if len(legal) == plan['budgetPerArm']: break
    if len(legal) != plan['budgetPerArm']: raise RuntimeError('Insufficient legal guided proposals')
    for index, params in enumerate(sample_parameters(plan['seed']+1, plan['policy']['maximumProposalsPerArm'])):
        row = evaluate('control-%04d' % index, 'guided-control', params)
        if row is None: return
        if row['status'] == 'evaluated': control.append(row)
        if len(control) == plan['budgetPerArm']: break
    if len(control) != plan['budgetPerArm']: raise RuntimeError('Insufficient legal control proposals')
    best = min(legal, key=lambda r: r['dragN']); confirmations = []
    for repeat in range(3):
        row = evaluate('guided-confirm-%d' % repeat, 'guided-confirm', best['parametersMm'], True)
        if row is None: return
        if row['status'] != 'evaluated': raise ValueError('Confirmation geometry failed')
        confirmations.append(row)
    conservative = max(r['dragN'] for r in confirmations)
    save(evidence.root/'summary.json', {'createdAt': utc(), 'planSha256': evidence.plan_hash,
        'status': 'complete', 'accepted': False, 'engineeringValidated': False,
        'counts': {'guided': len(legal), 'control': len(control), 'confirmations': len(confirmations)},
        'baselineN': baseline['dragN'], 'confirmedCandidateN': conservative,
        'reductionPercent': 100*(baseline['dragN']-conservative)/baseline['dragN'],
        'bestControlN': min(r['dragN'] for r in control),
        'beatsControlByPrimaryMargin': min(r['dragN'] for r in control)-conservative > noise['randomMarginN'],
        'repeatSpreadN': float(np.ptp([r['dragN'] for r in confirmations])),
        'parametersMm': best['parametersMm'], 'executedSearchSpace': bounds,
        'scope': plan['scope']})
