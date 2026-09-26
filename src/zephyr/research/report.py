"""Export standalone scientific plots and an auditable research conclusion."""
import json
import re
from pathlib import Path
import numpy as np
from zephyr.artifacts import _file_sha256
from zephyr.research.runtime import Evidence, save, utc
from zephyr.research.study import verified_noise
from zephyr.research.policy import decision, aerodynamic_power


def artifact_path(evidence, record):
    item = record['artifact']
    path = (evidence.root / item['path']).resolve()
    if not path.is_relative_to(evidence.root.resolve()) or _file_sha256(path) != item['sha256']:
        raise ValueError('Geometry artifact identity mismatch')
    return path


def independent_comparison(evidence, baseline, candidate):
    path = evidence.root / 'independent.json'
    if not path.exists():
        return {'passed': False, 'status': 'not-run'}
    data = json.loads(path.read_text())
    checks = {'plan': data.get('planSha256') == evidence.plan_hash,
              'baseline': data.get('baselineMeshHash') == baseline['meshHash'],
              'candidate': data.get('candidateMeshHash') == candidate['meshHash'],
              'conditions': data.get('conditions') == evidence.plan['policy']['conditions'],
              'solverIndependent': data.get('method') == 'OpenFOAM',
              'meshStudy': len(data.get('levels', [])) >= 2}
    differences = []
    for level in data.get('levels', []):
        values = [level.get('baselineDragN'), level.get('candidateDragN')]
        valid = all(isinstance(v, (int, float)) and np.isfinite(v) and v > 0 for v in values)
        checks[level.get('name', 'unknown') + ':valid'] = valid and level.get('meshPassed') is True and level.get('converged') is True
        if valid:
            differences.append((values[0] - values[1]) / values[0])
        receipts = level.get('artifacts', {})
        checks[level.get('name', 'unknown') + ':receipts'] = bool(receipts)
        for name, sha in receipts.items():
            artifact = (evidence.root / name).resolve()
            if not artifact.is_relative_to(evidence.root.resolve()) or not artifact.is_file() or _file_sha256(artifact) != sha:
                checks[level.get('name', 'unknown') + ':receipts'] = False
        # Recompute the reported force from the hash-verified solver output.
        # A JSON boolean or an unrelated log file cannot establish convergence.
        for case in ('baseline', 'candidate'):
            prefix = f"cfd/{level.get('name', 'unknown')}/{case}/"
            force_files = [name for name in receipts if name.startswith(prefix+'postProcessing/aerodynamicForces/') and name.endswith('/force.dat')]
            verified = False
            if len(force_files) == 1 and checks[level.get('name', 'unknown') + ':receipts']:
                lines = (evidence.root/force_files[0]).read_text().splitlines()
                numbers = [re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', line) for line in lines if line and not line.startswith('#')]
                forces = [float(row[1]) for row in numbers if len(row) >= 10]
                tail = forces[-100:]
                if len(tail) == 100 and np.isfinite(tail).all() and np.mean(tail) > 0:
                    mean = sum(tail)/len(tail)
                    reported = level.get(case+'DragN')
                    verified = (isinstance(reported, (int, float)) and abs(mean-reported) <= 1e-9 and
                                (max(tail)-min(tail))/mean < .002)
                mesh_log = prefix+'log.checkMesh'
                verified = verified and mesh_log in receipts and 'Mesh OK.' in (evidence.root/mesh_log).read_text()
            checks[level.get('name', 'unknown')+':'+case+'SourceForces'] = bool(verified)
    surrogate = (baseline['dragN'] - candidate['dragN']) / baseline['dragN']
    tolerance = evidence.plan['policy']['independentRelativeDeltaTolerance']
    checks['sameDirection'] = surrogate > 0 and len(differences) >= 2 and all(v > 0 for v in differences)
    checks['roughSize'] = len(differences) >= 2 and surrogate > 0 and all(abs(v - surrogate) <= tolerance * surrogate for v in differences)
    checks['meshConsistency'] = len(differences) >= 2 and abs(differences[-1] - differences[-2]) <= tolerance * max(abs(differences[-1]), 1e-12)
    source_verified = all(v for k, v in checks.items() if k not in ('sameDirection', 'roughSize', 'meshConsistency'))
    return {'passed': all(checks.values()), 'status': 'compared' if source_verified else 'inconclusive', 'checks': checks,
            'cfdReductionFractions': differences, 'surrogateReductionFraction': surrogate,
            'levels': data.get('levels', []), 'conditions': data.get('conditions'),
            'sourceSha256': _file_sha256(path), 'limitations': data.get('limitations', [])}


def make_report(directory, output, speed_kmh=120.):
    evidence = Evidence(directory)
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    rows, noise = evidence.records(), verified_noise(evidence)
    opt = sorted([r for r in rows if r['arm'] in ('lhs', 'tpe') and r['status'] == 'evaluated'], key=lambda r: (r['arm'] != 'lhs', r['id']))
    random = [r for r in rows if r['arm'] == 'random' and r['status'] == 'evaluated']
    baseline = next(r for r in rows if r['id'] == 'baseline-00')
    confirmed = [r for r in rows if r['id'].startswith('confirm-0-') and r['status'] == 'evaluated']
    result = {'createdAt': utc(), 'planSha256': evidence.plan_hash, 'noise': noise,
              'conditions': evidence.plan['policy']['conditions'],
              'counts': {'optimized': len(opt), 'random': len(random), 'winnerConfirmations': len(confirmed)},
              'phaseCounts': {arm: sum(r['arm'] == arm for r in opt) for arm in ('lhs', 'tpe')},
              'status': 'incomplete', 'accepted': False, 'engineeringValidated': False,
              'sourceRecords': {r['id']: r['recordSha256'] for r in rows},
              'rejectedProposals': sum(r['status'] != 'evaluated' for r in rows)}
    if opt:
        result['bestSearchCandidate'] = min(opt, key=lambda r: r['dragN'])
    if confirmed and random:
        best = max(confirmed, key=lambda r: r['dragN'])
        comparison = independent_comparison(evidence, baseline, best)
        result['independentComparison'] = comparison
        result['decision'] = decision(noise, [r['dragN'] for r in opt], [r['dragN'] for r in random],
            [r['dragN'] for r in confirmed], geometry_passed=all(c['status'] == 'passed' for r in confirmed for c in r['checks'].values()),
            domain_verified=all(r['domain']['trainingDistributionVerified'] for r in confirmed),
            independent=comparison, policy=evidence.plan['policy'])
        selected, seen = [], set()
        for record in sorted(opt, key=lambda r: r['dragN']):
            if record['meshHash'] not in seen:
                selected.append(record); seen.add(record['meshHash'])
            if len(selected) == evidence.plan['policy']['topCandidates']: break
        finalist_checks = []
        result['finalists'] = []
        for rank, original in enumerate(selected):
            repeats = [r for r in rows if r['id'].startswith(f'confirm-{rank}-') and r['status'] == 'evaluated']
            result['finalists'].append({'rank': rank+1, 'searchId': original['id'], 'meshHash': original['meshHash'],
                'searchDragN': original['dragN'], 'confirmationDragN': [r['dragN'] for r in repeats]})
            finalist_checks.append(len(repeats) == evidence.plan['policy']['confirmationRepeats'] and
                all(r['meshHash'] == original['meshHash'] and r['parametersMm'] == original['parametersMm'] and
                    abs(r['dragN']-original['dragN']) <= 2*noise['operationalSigmaN'] for r in repeats))
        verified_finalists = len(finalist_checks) == evidence.plan['policy']['topCandidates'] and all(finalist_checks)
        result['decision']['checks']['allFinalistsRepeated'] = verified_finalists
        result['decision']['checks']['phaseBudgetsComplete'] = (
            result['phaseCounts']['lhs'] == evidence.plan['policy']['lhsCandidates'] and
            result['phaseCounts']['tpe'] == evidence.plan['policy']['adaptiveCandidates'])
        for name in ('allFinalistsRepeated', 'phaseBudgetsComplete'):
            if not result['decision']['checks'][name]:
                result['decision']['failedChecks'].append(name)
                result['decision']['numericalResearchPassed'] = result['decision']['accepted'] = False
        result.update(status='evaluated', accepted=result['decision']['accepted'], winner=best,
                      power=aerodynamic_power(noise['baselineMeanN'], best['dragN'], speed_kmh))
        shape_plot(artifact_path(evidence, baseline), artifact_path(evidence, best), output / 'sedan-true-scale.png')
    plot_search(noise, opt, random, output / 'drag-study.png')
    save(output / 'summary.json', result)
    lines = ['# Sedan research result', '', 'Surrogate estimates; physical improvement is not established.', '',
             f"Plan: `{evidence.plan_hash}`", f"Status: **{result['status']}**. Accepted: **{result['accepted']}**.", '',
             f"Evaluations: optimized {len(opt)}, random {len(random)}, winner confirmations {len(confirmed)}.",
             f"Optimization phases: LHS {result['phaseCounts']['lhs']}, TPE {result['phaseCounts']['tpe']}.",
             f"Baseline: {noise['baselineMeanN']:.6f} N; operational sigma: {noise['operationalSigmaN']:.6f} N.",
             f"Required improvement: strictly >{noise['requiredReductionN']:.6f} N; random margin >{noise['randomMarginN']:.6f} N.", '',
             '![Search and random control](drag-study.png)', '']
    if 'decision' in result:
        d = result['decision']
        lines += [f"Confirmed reduction: **{d['reductionPercent']:.4f}%** ({d['reductionN']:.6f} N).",
                  f"Failed gates: {', '.join(d['failedChecks']) or 'none'}.", '',
                  'Parameters (mm): `' + json.dumps(result['winner']['parametersMm'], sort_keys=True) + '`.', '',
                  '![True-scale geometry](sedan-true-scale.png)', '',
                  f"At {speed_kmh:g} km/h, estimated aero power saving: {result['power']['savingW']:.1f} W.",
                  result['power']['assumption'], '',
                  'All inputs, source identities, checks and independent-comparison details are in `summary.json`.']
        p = result['power']
        lines += ['', '## Aero power inputs', '',
            '| Input | Value |', '|---|---:|',
            f"| Evaluated speed | {p['evaluatedSpeedMps']:.6f} m/s |",
            f"| Air density (held constant) | {result['conditions']['densityKgM3']:.6f} kg/m³ |",
            f"| Baseline evaluated force | {p['baselineEvaluatedForceN']:.6f} N |",
            f"| Candidate evaluated force | {p['candidateEvaluatedForceN']:.6f} N |",
            f"| Selected speed | {p['speedKmh']:.3f} km/h = {p['speedMps']:.6f} m/s |",
            f"| Baseline aero power at selected speed | {p['baselinePowerW']:.3f} W |",
            f"| Candidate aero power at selected speed | {p['candidatePowerW']:.3f} W |", '',
            'Calculation: P = F_evaluated × (v / v_evaluated)² × v. No powertrain, rolling resistance or battery-range model is implied.', '',
            '## Finalist repeats', '', '| Rank / search ID | Search drag (N) | Fresh drag repeats (N) |', '|---|---:|---|']
        for row in result['finalists']:
            repetitions = ', '.join(f'{v:.6f}' for v in row['confirmationDragN']) or 'Missing'
            lines.append(f"| {row['rank']} / {row['searchId']} | {row['searchDragN']:.6f} | {repetitions} |")
        independent = result['independentComparison']
        lines += ['', '## Independent comparison', '',
            f"Status: {independent['status']}. Agreement gate passed: {independent['passed']}."]
        if independent.get('levels'):
            lines += ['', '| Mesh | Baseline (N) | Candidate (N) | Mesh check | Force convergence |', '|---|---:|---:|---|---|']
            for row in independent['levels']:
                number = lambda key: f"{row[key]:.6f}" if isinstance(row.get(key), (int, float)) else 'Unavailable'
                lines.append(f"| {row['name']} | {number('baselineDragN')} | {number('candidateDragN')} | {row.get('meshPassed')} | {row.get('converged')} |")
            lines += ['', *independent.get('limitations', [])]
    (output / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return result


def plot_search(noise, optimized, random, path):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), gridspec_kw={'width_ratios': [2, 1]})
    for rows, label, color in ((optimized, 'LHS + TPE', '#146c94'), (random, 'Uniform random', '#c86827')):
        values = np.array([r['dragN'] for r in rows])
        if len(values):
            axes[0].plot(np.arange(1, len(values)+1), np.minimum.accumulate(values), label=label, color=color)
            axes[1].hist(values, bins=min(20, max(3, len(values)//5)), alpha=.55, label=label, color=color)
    b, band = noise['baselineMeanN'], 5 * noise['operationalSigmaN']
    axes[0].axhspan(b-band, b+band, color='gray', alpha=.2, label='Baseline ±5 operational sigma')
    axes[0].axhline(b-noise['requiredReductionN'], linestyle='--', color='black', label='Required reduction')
    axes[0].set(xlabel='Legal forward evaluations per arm', ylabel='Best predicted drag (N)', title='Equal-budget progress (partial until both reach 200)')
    axes[1].set(xlabel='Predicted drag (N)', ylabel='Candidates', title='All evaluated candidates')
    axes[0].legend(fontsize=8); fig.tight_layout(); fig.savefig(path, dpi=170); plt.close(fig)


def shape_plot(baseline_path, candidate_path, path):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    import pyvista as pv
    a, b = pv.read(baseline_path), pv.read(candidate_path)
    ids = np.linspace(0, a.n_points-1, min(30000, a.n_points), dtype=int)
    movement = np.linalg.norm(a.points-b.points, axis=1)*1000
    max_mm = float(movement.max())
    cmap = LinearSegmentedColormap.from_list('movement', ['#9aabb3', '#e8c273', '#ca5f14'])
    fig, axes = plt.subplots(2, 2, figsize=(12, 6), layout='constrained')
    colored = None
    for col, (mesh, label) in enumerate(((a, 'Original'), (b, 'Candidate'))):
        for row, (x, y, view) in enumerate(((0, 2, 'Side'), (0, 1, 'Top'))):
            ax = axes[row, col]
            if col:
                colored = ax.scatter(mesh.points[ids, x], mesh.points[ids, y], s=.15,
                    c=movement[ids], cmap=cmap, vmin=0, vmax=max(max_mm, 1e-9), rasterized=True)
            else:
                ax.scatter(mesh.points[ids, x], mesh.points[ids, y], s=.15, color='#9aabb3', rasterized=True)
            ax.set_aspect('equal'); ax.set_title(label + ' — ' + view)
            combined = np.concatenate([a.points, b.points])
            ax.set_xlim(combined[:, x].min()-.05, combined[:, x].max()+.05)
            ax.set_ylim(combined[:, y].min()-.05, combined[:, y].max()+.05)
            ax.set_xlabel('Metres'); ax.set_ylabel('Metres')
    fig.colorbar(colored, ax=axes.ravel().tolist(), shrink=.8, pad=.015, label='Actual movement (mm)')
    fig.suptitle(f'Actual geometry scale, no displacement magnification; max movement {max_mm:.2f} mm')
    fig.savefig(path, dpi=180); plt.close(fig)
