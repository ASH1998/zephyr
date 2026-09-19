"""Versioned, local-surrogate step policy. Never an engineering validation.

Thresholds below are explicit provisional numerical policy, not a measured
physical confidence interval or a transferable calibrated trust radius.
Probes are separate from the candidate used to test their prediction.
"""
import numpy as np
from zephyr.local.geometry import deform, validate_geometry
from zephyr.local.conversion import mesh_hash

POLICY_VERSION = 'local-handle-check-v1'
REQUIRED_CHECKS = frozenset(('topology', 'finite', 'protected', 'bounds', 'normals',
                            'triangleArea', 'watertight', 'symmetricHandle', 'transition', 'selfIntersection'))
POLICY = {'slopeRelativeTolerance': .20, 'centeringRelativeTolerance': .20, 'candidateRelativeTolerance': .25,
          'minimumSignalToNoise': 5., 'float32EpsilonMultiplier': 32.}


def calibrate_handle(mesh, baseline_drag, budget_m, evaluate):
    """Evaluate +/-h, +/-h/2 and a baseline repeat before choosing the step."""
    h = min(budget_m / 2, .001)
    samples = []
    radius_attempts = []
    # Fine source triangles can fail the normal/area gate even at 1 mm.
    # Shrink the probe radius geometrically before spending GPU work on it.
    for _ in range(7):
        safe = True
        for amplitude in (h, -h, h / 2, -h / 2):
            trial, protected, _ = deform(mesh, amplitude, budget_m)
            checks = validate_geometry(mesh, trial, protected, budget_m)
            failed = {k: v for k, v in checks.items() if v['status'] != 'passed'}
            if failed:
                safe = False
                radius_attempts.append({'radiusM': h, 'failedAmplitudeM': amplitude, 'checks': failed})
                break
        if safe:
            break
        h /= 2
    if not safe:
        return {'status': 'failed', 'reason': 'No geometry-safe probe radius found',
                'samples': samples, 'radiusAttempts': radius_attempts}
    repeated = float(evaluate(mesh.copy(deep=True), 'repeat')[0])
    for amplitude in (h, -h, h / 2, -h / 2):
        trial, protected, _ = deform(mesh, amplitude, budget_m)
        checks = validate_geometry(mesh, trial, protected, budget_m)
        if any(v['status'] != 'passed' for v in checks.values()):
            return {'status': 'failed', 'reason': 'A finite-difference probe failed geometry checks',
                    'samples': samples, 'checks': checks}
        name = ('probe-plus-' if amplitude > 0 else 'probe-minus-') + ('h' if abs(amplitude) == h else 'half')
        drag = float(evaluate(trial, name)[0])
        samples.append({'name': name, 'amplitudeM': amplitude, 'dragN': drag, 'meshHash': mesh_hash(trial)})
    result = assess_probes(baseline_drag, repeated, h, samples)
    result['radiusAttempts'] = radius_attempts
    return result


def assess_probes(baseline_drag, repeated, h, samples):
    values = [s['dragN'] for s in samples]
    if h <= 0 or len(values) != 4 or not np.isfinite([baseline_drag, repeated, h, *values]).all():
        raise ValueError('Finite-difference probes must be finite and complete')
    # Conservative numerical floor even when identical evaluations repeat exactly.
    noise = float(max(abs(repeated - baseline_drag),
                POLICY['float32EpsilonMultiplier'] * np.finfo(np.float32).eps * max(abs(baseline_drag), 1.)))
    coarse = (values[0] - values[1]) / (2 * h)
    fine = (values[2] - values[3]) / h
    signal = min(abs(values[0] - values[1]), abs(values[2] - values[3]))
    agreement = abs(coarse - fine) / max(abs(coarse), abs(fine), 1e-30)
    centering = abs((values[2] + values[3]) / 2 - baseline_drag)
    centered = centering <= POLICY['centeringRelativeTolerance'] * abs(values[2] - values[3]) / 2 + noise
    passed = baseline_drag > 0 and repeated > 0 and all(x > 0 for x in values) and (
        signal > POLICY['minimumSignalToNoise'] * noise and coarse * fine > 0
        and agreement <= POLICY['slopeRelativeTolerance'] and centered)
    return {'status': 'passed' if passed else 'failed', 'policyVersion': POLICY_VERSION,
            'scope': 'This mesh, conditions and rear handle only; not physical validation or a global trust radius',
            'policy': POLICY, 'baselineDragN': baseline_drag, 'repeatedBaselineDragN': repeated,
            'baselineRepeatDifferenceN': abs(repeated - baseline_drag), 'numericalFloorN': noise,
            'probeRadiusM': h, 'coarseSlopeNPerM': coarse, 'slopeNPerM': fine,
            'fineProbeMidpointOffsetN': centering, 'probeCenteringPassed': bool(centered),
            'slopeDisagreementPercent': agreement * 100, 'samples': samples,
            'reason': 'Two-scale directional slope resolved' if passed else 'Directional slope is unstable or unresolved above the numerical floor'}


def decide_step(baseline, actual, predicted_delta, calibration, checks, *, experimental=False):
    """Test held-out candidate reduction. No candidate is used to fit its predictor."""
    actual_delta = actual - baseline
    error = abs(actual_delta - predicted_delta)
    noise = calibration.get('numericalFloorN', float('inf'))
    resolved = abs(predicted_delta) > POLICY['minimumSignalToNoise'] * noise
    relative = error / abs(predicted_delta) * 100 if resolved else None
    agreement = resolved and relative <= 100 * POLICY['candidateRelativeTolerance']
    geometry_passed = REQUIRED_CHECKS.issubset(checks) and all(c['status'] == 'passed' for c in checks.values())
    numeric_passed = (np.isfinite([baseline, actual, predicted_delta]).all() and baseline > 0 and actual > 0
                      and calibration['status'] == 'passed' and agreement
                      and predicted_delta < -POLICY['minimumSignalToNoise'] * noise
                      and actual_delta < -POLICY['minimumSignalToNoise'] * noise)
    accept = numeric_passed and geometry_passed and not experimental
    if accept:
        reason = 'Accepted for further evaluation: local surrogate prediction and fresh reduction agree; geometry checks passed. Independent CFD is still required.'
    elif not geometry_passed:
        reason = 'Geometry validation failed or is incomplete; step refused.'
    elif experimental:
        reason = 'Experimental geometry outside the validated model domain; step refused regardless of the numerical improvement.'
    elif not numeric_passed:
        reason = 'Fresh reduction or local prediction agreement is insufficient; step refused.'
    return {'decision': 'accept' if accept else 'refuse', 'calibrated': bool(numeric_passed),
            'calibrationScope': 'local-surrogate-handle-only', 'policyVersion': POLICY_VERSION,
            'engineeringValidated': False, 'predictionErrorPercent': relative,
            'predictionErrorN': error, 'predictionErrorBaselinePercent': error / abs(baseline) * 100 if baseline else None,
            'actualDragDeltaN': actual_delta, 'predictedDragDeltaN': predicted_delta,
            'reductionRatio': actual_delta / predicted_delta if resolved and predicted_delta < 0 else None,
            'reason': reason}
