"""Prepare and execute an evidence-grounded Nemotron follow-on study."""
import argparse
import json
import os
from pathlib import Path
from uuid import uuid4
from zephyr.artifacts import _file_sha256
from zephyr.config import load_env_file, load_llm_config
from zephyr.token_factory import TokenFactoryClient
from zephyr.local.locks import acquire_lock
from zephyr.research.runtime import Evidence, Runtime, save, utc
from zephyr.research.advisor import advise, history_context, AdviceValidationError, SYSTEM, SCHEMA
from zephyr.research.guided import prepare, run


def recorded_advice(client, config, brief, context, directory):
    """Keep every actual attempt, including refusals and invalid model responses."""
    root = Path(directory); root.mkdir(parents=True, exist_ok=False)
    save(root/'input.json', {'createdAt': utc(), 'brief': brief, 'context': context,
        'model': config.model, 'system': SYSTEM, 'schema': SCHEMA,
        'cliSha256': _file_sha256(Path(__file__))})
    try:
        answer = advise(client, config, brief, context)
    except AdviceValidationError as exc:
        save(root/'error.json', {'errorType': type(exc).__name__,
            'validationReason': str(exc), 'uneditedResponse': exc.response,
            'provenance': exc.provenance})
        raise
    except Exception as exc:
        # Provider exception messages may contain request details; keep only type.
        save(root/'error.json', {'errorType': type(exc).__name__})
        raise
    save(root/'advice.json', answer)
    return {**answer, 'attemptEvidence': {'directory': str(root.resolve()),
        'inputSha256': _file_sha256(root/'input.json'),
        'adviceSha256': _file_sha256(root/'advice.json')}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['prepare', 'run'])
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--parent', type=Path)
    p.add_argument('--qualification', type=Path)
    p.add_argument('--sensitivity-run', type=Path)
    p.add_argument('--brief', default='Reduce sedan drag. Use the search history and partial sensitivity evidence to choose which parameters to explore next. Cite at least one history ID and baseline-partial-sensitivity in the decisions evidenceIds, explaining how these observations informed the choices. Keep the cabin, greenhouse, wheels and underbody unchanged. Maximum movement 30 mm.')
    p.add_argument('--budget', type=int, default=20)
    p.add_argument('--max-seconds', type=float, default=7200)
    p.add_argument('--evaluation-limit', type=int)
    p.add_argument('--live', action='store_true')
    args = p.parse_args()
    if not args.live: p.error('Use --live to authorize Token Factory or local GPU execution')
    if args.max_seconds <= 0 or args.evaluation_limit is not None and args.evaluation_limit < 1:
        p.error('Budgets must be positive')
    if args.command == 'prepare':
        if not all((args.parent, args.qualification, args.sensitivity_run)):
            p.error('Preparation requires parent study, qualification results and sensitivity run')
        if args.directory.exists(): p.error('Use a new study directory')
        parent = Evidence(args.parent)
        if not (parent.root/'search-complete.json').exists(): p.error('Finish the primary search first')
        qualification = json.loads(args.qualification.read_text())
        if not qualification.get('passed'): p.error('Advisor qualification has not passed')
        context = history_context(parent, args.sensitivity_run)
        env = os.environ.copy(); load_env_file(environ=env)
        config = load_llm_config(env, require_credentials=True)
        attempt = args.directory.with_name(args.directory.name+'-advice-'+uuid4().hex)
        advice = recorded_advice(TokenFactoryClient(config.api_key, config.base_url, timeout=120),
                                 config, args.brief, context, attempt)
        prepare(parent, args.directory, args.brief, context, advice, qualification, args.budget)
        print(json.dumps({'status': advice['status'], 'searchSpace': advice['searchSpace']}))
    else:
        evidence = Evidence(args.directory)
        with acquire_lock(evidence.root/'study.lock'), Runtime() as runtime:
            run(evidence, runtime, args.max_seconds, args.evaluation_limit)


if __name__ == '__main__': main()
