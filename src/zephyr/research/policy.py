"""Predeclared research decisions, independent of the model and optimizer."""
import math
import numpy as np

POLICY = {
    'version': 'sedan-forward-study-v1',
    'baselineRepeats': 5, 'microPerturbations': 10, 'microMaximumMm': .09,
    'minimumReductionFraction': .01, 'sigmaMultiplier': 5.,
    'randomMarginFraction': .001, 'topCandidates': 3, 'confirmationRepeats': 3,
    'repeatToleranceSigma': 2., 'lhsCandidates': 100, 'adaptiveCandidates': 100,
    'randomCandidates': 200, 'maximumProposalsPerArm': 2000,
    'maximumDisplacementMm': 60., 'minimumNormalCosine': .95,
    'areaRatio': [.5, 2.], 'edgeRatio': [.5, 2.], 'maximumAspectGrowth': 2.,
    'independentRelativeDeltaTolerance': .5,
    'conditions': {'velocityMps': 38.889, 'densityKgM3': 1.205},
}


def finite_values(values, minimum):
    a = np.asarray(values, dtype=float)
    if a.ndim != 1 or len(a) < minimum or not np.isfinite(a).all():
        raise ValueError('Missing, insufficient or nonfinite force samples')
    return a


def noise_summary(baselines, perturbations, policy=POLICY):
    b = finite_values(baselines, policy['baselineRepeats'])
    p = finite_values(perturbations, policy['microPerturbations'])
    mean = float(b.mean())
    if mean <= 0:
        raise ValueError('Expected positive baseline drag')
    repeat_sd, perturb_sd = float(b.std(ddof=1)), float(p.std(ddof=1))
    guard = float(32 * np.finfo(np.float32).eps * max(abs(mean), 1.))
    sigma = max(repeat_sd, perturb_sd, guard)
    return {'baselineMeanN': mean, 'repeatSigmaN': repeat_sd,
            'perturbationSigmaN': perturb_sd, 'float32GuardN': guard,
            'operationalSigmaN': sigma,
            'requiredReductionN': max(policy['sigmaMultiplier'] * sigma,
                                      policy['minimumReductionFraction'] * mean),
            'randomMarginN': max(policy['sigmaMultiplier'] * sigma,
                                 policy['randomMarginFraction'] * mean),
            'scope': 'Perturbation spread includes shape response; not surrogate error or physical uncertainty.'}


def decision(noise, optimized, random, confirmations, *, geometry_passed,
             domain_verified=False, independent=None, policy=POLICY):
    """Fail closed on incomplete counts, confirmation, domain or independent evidence."""
    opt = finite_values(optimized, 1)
    rand = finite_values(random, 1)
    rep = finite_values(confirmations, 1)
    baseline, sigma = noise['baselineMeanN'], noise['operationalSigmaN']
    # Use worst fresh confirmation, not a lucky minimum from search.
    candidate = float(rep.max())
    reduction = baseline - candidate
    checks = {
        'equalBudget': len(opt) == len(rand) == policy['randomCandidates'],
        'confirmationCount': len(rep) >= policy['confirmationRepeats'],
        'repeatable': float(np.ptp(rep)) <= max(policy['repeatToleranceSigma'] * sigma, noise['float32GuardN']),
        'moreThanOnePercent': reduction > policy['minimumReductionFraction'] * baseline,
        'moreThanFiveSigma': reduction > policy['sigmaMultiplier'] * sigma,
        'beatsRandom': float(rand.min()) - candidate > noise['randomMarginN'],
        'geometry': bool(geometry_passed), 'trainingDistribution': bool(domain_verified),
        'independentComparison': bool(independent and independent.get('passed') is True),
    }
    numerical = all(value for key, value in checks.items()
                    if key not in ('trainingDistribution', 'independentComparison'))
    return {'policyVersion': policy['version'], 'checks': checks,
            'numericalResearchPassed': numerical, 'accepted': all(checks.values()),
            'engineeringValidated': False, 'candidateConservativeN': candidate,
            'reductionN': reduction, 'reductionPercent': 100 * reduction / baseline,
            'failedChecks': [key for key, value in checks.items() if not value],
            'scope': 'Research screening only; independent CFD is a comparison, not certification.'}


def aerodynamic_power(baseline_n, candidate_n, speed_kmh, evaluated_speed_mps=38.889):
    if not all(math.isfinite(v) for v in (baseline_n, candidate_n, speed_kmh, evaluated_speed_mps)):
        raise ValueError('Power inputs must be finite')
    if min(baseline_n, candidate_n, evaluated_speed_mps) <= 0 or speed_kmh < 0:
        raise ValueError('Invalid force or speed')
    speed = speed_kmh / 3.6
    scale = (speed / evaluated_speed_mps) ** 2
    return {'speedKmh': speed_kmh, 'speedMps': speed, 'evaluatedSpeedMps': evaluated_speed_mps,
            'baselineEvaluatedForceN': baseline_n, 'candidateEvaluatedForceN': candidate_n,
            'baselinePowerW': baseline_n * scale * speed,
            'candidatePowerW': candidate_n * scale * speed,
            'savingW': (baseline_n - candidate_n) * scale * speed,
            'assumption': 'Constant CdA and density; force scales with speed squared. Aero power only, not total vehicle energy.'}
