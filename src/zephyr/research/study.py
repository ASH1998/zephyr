"""Reproducible forward-only study with equal legal-evaluation budgets."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import time
import numpy as np
from scipy.stats import qmc
from zephyr.artifacts import _file_sha256
from zephyr.local.cars import mesh_path
from zephyr.research.morphs import PARAMETERS
from zephyr.research.policy import POLICY, noise_summary
from zephyr.research.runtime import (ROOT, ASSETS, Evidence, Runtime, digest, save, utc,
                                     source_hashes, evaluate_candidate)


def sample_parameters(seed, count, lhs=False):
    names = list(PARAMETERS)
    unit = qmc.LatinHypercube(len(names), seed=seed).random(count) if lhs else np.random.default_rng(seed).random((count, len(names)))
    bounds = np.array([PARAMETERS[n]['rangeMm'] for n in names])
    values = bounds[:, 0] + unit * (bounds[:, 1] - bounds[:, 0])
    return [dict(zip(names, map(float, row))) for row in values]


def prepare(directory, seed=25092026):
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=False)
    for folder in ('records', 'meshes'):
        (root / folder).mkdir()
    plan = {'schemaVersion': 'zephyr.research.v1', 'createdAt': utc(), 'seed': seed,
            'geometryId': 'drivaer-1', 'policy': deepcopy(POLICY), 'parameters': deepcopy(PARAMETERS),
            'sources': source_hashes(), 'inputSha256': _file_sha256(mesh_path('drivaer-1')),
            'checkpointSha256': _file_sha256(ASSETS / 'DoMINO.0.501.mdlus'),
            'studySourceSha256': _file_sha256(Path(__file__)),
            'sampling': '100 legal Latin-hypercube warm starts plus 100 TPE; 200 independent uniform legal controls. Invalid geometry recorded, not evaluated. No backtracking or range changes.',
            'domainPolicy': 'Reject outside local ranges; flag all analogue morphs as training distribution unverified. This blocks final acceptance.',
            'maxForwardEvaluations': 424,
            'uiPolicy': 'Existing frontend, legacy API, aircraft, and viewer remain unchanged.'}
    save(root / 'plan.json', plan)
    (root / 'plan.sha256').write_text(digest(plan) + '\n')
    for name in plan['sources']:
        path = root / 'source' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, path)
    shutil.copyfile(Path(__file__), root / 'source/study.py')
    return plan


def verify_runtime(evidence, runtime):
    p, actual = evidence.plan, runtime.provenance
    if p['sources'] != actual['sources'] or p['inputSha256'] != actual['inputSha256'] or p['checkpointSha256'] != actual['checkpointSha256']:
        raise ValueError('Study source or asset identity changed; start a new study')
    if p['studySourceSha256'] != _file_sha256(Path(__file__)):
        raise ValueError('Study implementation changed; start a new study')
    path = evidence.root / 'runtime.json'
    if path.exists() and json.loads(path.read_text()) != actual:
        raise ValueError('Runtime identity changed; start a new study')
    if not path.exists():
        save(path, actual)


def noise(evidence, runtime):
    policy = evidence.plan['policy']
    rng = np.random.default_rng(evidence.plan['seed'])
    scheduled = [('baseline-%02d' % i, 'baseline', {}) for i in range(policy['baselineRepeats'])]
    scheduled += [('micro-%02d' % i, 'micro', runtime.morphs.micro_parameters(rng)) for i in range(policy['microPerturbations'])]
    # Mix repeats and tiny changes to expose within-session drift.
    rng.shuffle(scheduled)
    existing = {r['id']: r for r in evidence.records()}
    for identifier, arm, parameters in scheduled:
        if (evidence.root / 'STOP').exists():
            return
        if identifier in existing:
            if existing[identifier]['status'] != 'evaluated':
                raise ValueError('Noise study contains a failed sample; use a new study')
            continue
        row = evaluate_candidate(runtime, evidence, identifier, arm, parameters,
                                 micro=arm == 'micro', save_fields=identifier == 'baseline-00')
        if row['status'] != 'evaluated':
            raise ValueError('Invalid noise geometry; cannot establish the frozen noise study')
    rows = evidence.records()
    result = noise_summary([r['dragN'] for r in rows if r['arm'] == 'baseline'],
                           [r['dragN'] for r in rows if r['arm'] == 'micro'], policy)
    result['planSha256'] = evidence.plan_hash
    result['recordHashes'] = [r['recordSha256'] for r in rows if r['arm'] in ('baseline', 'micro')]
    save(evidence.root / 'noise.json', result)
    print(json.dumps(result), flush=True)


def verified_noise(evidence):
    rows = evidence.records()
    expected = noise_summary([r['dragN'] for r in rows if r['arm'] == 'baseline'],
                             [r['dragN'] for r in rows if r['arm'] == 'micro'], evidence.plan['policy'])
    actual = json.loads((evidence.root / 'noise.json').read_text())
    if any(actual.get(k) != v for k, v in expected.items()) or actual['planSha256'] != evidence.plan_hash:
        raise ValueError('Noise summary does not match source records')
    return actual


def search(evidence, runtime, *, max_seconds=14400, evaluation_limit=None):
    import optuna
    from optuna.distributions import FloatDistribution
    from optuna.trial import TrialState, create_trial
    if optuna.__version__ != '4.5.0':
        raise ValueError('Use optuna==4.5.0 for this frozen study')
    verified_noise(evidence)
    policy, seed = evidence.plan['policy'], evidence.plan['seed']
    existing = {r['id']: r for r in evidence.records()}
    distributions = {k: FloatDistribution(*v['rangeMm']) for k, v in PARAMETERS.items()}
    optimizer = optuna.create_study(direction='minimize', sampler=optuna.samplers.TPESampler(
        seed=seed + 2, n_startup_trials=0, multivariate=True, constant_liar=False))
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    started, new_evaluations = time.monotonic(), 0
    def stopped():
        return ((evidence.root / 'STOP').exists() or time.monotonic() - started >= max_seconds or
                evaluation_limit is not None and new_evaluations >= evaluation_limit)
    def evaluate(identifier, arm, parameters):
        nonlocal new_evaluations
        if identifier in existing:
            row = existing[identifier]
            if row['parametersMm'] != parameters or row['arm'] != arm:
                raise ValueError('Resumed proposal differs from frozen search history')
            if row['status'] == 'evaluation-failed':
                raise ValueError('A model evaluation failed; preserve study and diagnose before a new study')
            return row
        if stopped():
            return None
        row = evaluate_candidate(runtime, evidence, identifier, arm, parameters)
        new_evaluations += row['status'] == 'evaluated'
        return row
    # Frozen LHS blocks provide extra proposals when geometry rejects a point.
    lhs_count = 0
    for block in range(policy['maximumProposalsPerArm'] // policy['lhsCandidates']):
        for index, params in enumerate(sample_parameters(seed + 10 + block, policy['lhsCandidates'], lhs=True)):
            identifier = 'lhs-%04d' % (block * policy['lhsCandidates'] + index)
            row = evaluate(identifier, 'lhs', params)
            if row is None:
                return
            if row['status'] == 'evaluated':
                optimizer.add_trial(create_trial(params=params, distributions=distributions, value=row['dragN']))
                lhs_count += 1
            if lhs_count == policy['lhsCandidates']:
                break
        if lhs_count == policy['lhsCandidates']:
            break
    if lhs_count < policy['lhsCandidates']:
        raise RuntimeError('Insufficient legal LHS proposals under frozen limits')
    adaptive_count = 0
    for index in range(policy['maximumProposalsPerArm']):
        trial = optimizer.ask(distributions)
        row = evaluate('tpe-%04d' % index, 'tpe', trial.params)
        if row is None:
            return
        if row['status'] == 'evaluated':
            optimizer.tell(trial, row['dragN'])
            adaptive_count += 1
        else:
            optimizer.tell(trial, state=TrialState.FAIL)
        if adaptive_count == policy['adaptiveCandidates']:
            break
    if adaptive_count < policy['adaptiveCandidates']:
        raise RuntimeError('Insufficient legal adaptive proposals under frozen limits')
    random_count = 0
    for index, params in enumerate(sample_parameters(seed + 1, policy['maximumProposalsPerArm'])):
        row = evaluate('random-%04d' % index, 'random', params)
        if row is None:
            return
        random_count += row['status'] == 'evaluated'
        if random_count == policy['randomCandidates']:
            break
    if random_count < policy['randomCandidates']:
        raise RuntimeError('Insufficient legal random proposals under frozen limits')
    save(evidence.root / 'search-complete.json', {'planSha256': evidence.plan_hash,
         'counts': {'lhs': lhs_count, 'tpe': adaptive_count, 'random': random_count}, 'createdAt': utc()})


def confirm(evidence, runtime):
    rows, policy = evidence.records(), evidence.plan['policy']
    candidates = [r for r in rows if r['arm'] in ('lhs', 'tpe') and r['status'] == 'evaluated']
    controls = [r for r in rows if r['arm'] == 'random' and r['status'] == 'evaluated']
    if len(candidates) != policy['randomCandidates'] or len(controls) != len(candidates):
        raise ValueError('Complete equal search/control budgets before confirming finalists')
    top, seen = [], set()
    for row in sorted(candidates, key=lambda r: r['dragN']):
        if row['meshHash'] not in seen:
            seen.add(row['meshHash']); top.append(row)
        if len(top) == policy['topCandidates']:
            break
    existing = {r['id']: r for r in rows}
    for rank, original in enumerate(top):
        for repeat in range(policy['confirmationRepeats']):
            identifier = 'confirm-%d-%d' % (rank, repeat)
            if identifier in existing:
                continue
            if (evidence.root / 'STOP').exists():
                return
            evaluate_candidate(runtime, evidence, identifier, 'confirm', original['parametersMm'], save_fields=True)
    save(evidence.root / 'finalists.json', {'planSha256': evidence.plan_hash, 'candidateIds': [r['id'] for r in top]})
