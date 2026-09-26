"""Short sedan comparison path; unchanged geometry gates and fresh fields."""
PROFILE = 'sedan-demo-v1'


def calibration_for_run(request, mesh, baseline, budget, evaluate, handle, calibrate):
    if request.get('executionProfile') == PROFILE:
        return {'status': 'not-run', 'policyVersion': PROFILE, 'samples': [],
                'reason': 'Direction chosen from the original sensitivity field; repeat and directional probes omitted.'}
    return calibrate(mesh, baseline, budget, evaluate, handle)


def comparison_decision(baseline, candidate, checks):
    from zephyr.local.trust import REQUIRED_CHECKS
    geometry_ok = REQUIRED_CHECKS.issubset(checks) and all(c['status'] == 'passed' for c in checks.values())
    return {'decision': 'refuse', 'calibrated': False, 'engineeringValidated': False,
            'policyVersion': PROFILE, 'predictionErrorPercent': None,
            'actualDragDeltaN': candidate - baseline,
            'reason': ('Original and changed shapes evaluated. Local calibration was not run.' if geometry_ok
                       else 'Geometry validation failed or is incomplete; step refused.')}
