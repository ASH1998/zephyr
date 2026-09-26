"""Live, no-manual-edit qualification on ten previously recorded application briefs."""
import argparse
import json
import os
import shutil
from pathlib import Path
from zephyr.config import load_env_file, load_llm_config
from zephyr.token_factory import TokenFactoryClient, TokenFactoryError
from zephyr.artifacts import _file_sha256
from zephyr.research.runtime import Evidence, save, utc
from zephyr.research.advisor import advise, history_context, AdviceValidationError

CASES = [
    ('local-0311ec5eb7644523b573f674dff2c1cc', ['hood_camber']),
    ('local-039d31f920de4c4aab599292dab40513', ['side_shoulders']),
    ('local-2590a0b23cc744c7860f447124c2d498', ['hood_camber', 'side_shoulders', 'nose_width', 'deck_height', 'rear_taper']),
    ('local-26b4f0c324844c4d9fd17cc066df9c71', None),
    ('local-2c1f85ec64144a2cb28a49db74b98660', ['nose_width']),
    ('local-5dc4b61d4d8848bca486eb963108f2c1', ['rear_taper']),
    ('local-914d0053077f4030bbfb5eac70a3f138', ['rear_taper']),
    ('local-be532b54c3fc400ab4a3cdb77cd5b548', ['deck_height']),
    ('local-d7753b6dff4b4aa0992be7d45143ae9a', 'refuse'),
    ('local-f76a1757dc7d4143abbbd8f69e53d5f3', ['rear_taper']),
]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--sensitivity-run', type=Path, required=True)
    p.add_argument('--live', action='store_true')
    args = p.parse_args()
    if not args.live: p.error('Use --live to authorize the ten Token Factory calls')
    if args.output.exists(): p.error('Use a new output directory')
    evidence = Evidence(args.directory); context = history_context(evidence, args.sensitivity_run)
    if not context['history']: p.error('Search history is required')
    args.output.mkdir(parents=True)
    save(args.output / 'context.json', context)
    root = Path(__file__).resolve().parents[1]
    corpus = []
    for rid, expected in CASES:
        request = json.loads((root / '.local/runs' / rid / 'request.json').read_text())
        corpus.append({'runId': rid, 'brief': request['brief'], 'expectedOpen': expected})
    save(args.output / 'corpus.json', {'cases': corpus, 'passMinimum': 8,
        'scope': 'Existing application briefs, some produced by verification scripts; not held-out human rulebook validation.'})
    sources = ['scripts/test-sedan-advisor.py', 'src/zephyr/research/advisor.py', 'src/zephyr/token_factory.py']
    snapshots = args.output / 'source'; snapshots.mkdir()
    for name in sources: shutil.copyfile(root/name, snapshots/Path(name).name)
    save(args.output / 'source-manifest.json', {'sources': {name: _file_sha256(root/name) for name in sources},
        'contextSha256': _file_sha256(args.output/'context.json'), 'corpusSha256': _file_sha256(args.output/'corpus.json')})
    env = os.environ.copy(); load_env_file(environ=env); config = load_llm_config(env, require_credentials=True)
    client = TokenFactoryClient(config.api_key, config.base_url, timeout=120)
    report = {'createdAt': utc(), 'model': config.model, 'cases': [], 'passed': False}
    for case in corpus:
        row = {**case, 'passed': False}
        try:
            answer = advise(client, config, case['brief'], context)
            opened = sorted(k for k, (a, b) in answer['searchSpace'].items() if a < b)
            expected = case['expectedOpen']
            row['answer'] = answer
            row['passed'] = (answer['status'] == 'refuse' if expected == 'refuse' else
                answer['status'] == 'ready' and (bool(opened) if expected is None else opened == sorted(expected)))
        except AdviceValidationError as exc:
            row.update(errorType=type(exc).__name__, validationReason=str(exc),
                       uneditedResponse=exc.response, provenance=exc.provenance)
        except TokenFactoryError as exc:
            row.update(errorType=type(exc).__name__, sanitizedReason=str(exc))
        except Exception as exc:
            row['errorType'] = type(exc).__name__
        report['cases'].append(row)
        report['passedCount'] = sum(r['passed'] for r in report['cases'])
        report['passed'] = len(report['cases']) == 10 and report['passedCount'] >= 8
        save(args.output / 'results.json', report)
        print(case['runId'], row['passed'], flush=True)
    if not report['passed']: raise SystemExit('Advisor qualification failed; responses retained without edits')


if __name__ == '__main__': main()
