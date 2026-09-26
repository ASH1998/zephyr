"""Separate sedan research CLI. Never changes the existing UI or aircraft."""
import argparse
import json
from pathlib import Path
from zephyr.local.locks import acquire_lock
from zephyr.research.runtime import Evidence, Runtime
from zephyr.research.study import prepare, verify_runtime, noise, search, confirm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'noise', 'search', 'confirm', 'status'])
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--live', action='store_true', help='Authorize local GPU evaluation')
    parser.add_argument('--seed', type=int, default=25092026)
    parser.add_argument('--max-seconds', type=float, default=14400)
    parser.add_argument('--evaluation-limit', type=int)
    args = parser.parse_args()
    if args.command == 'prepare':
        print(json.dumps(prepare(args.directory, args.seed), indent=2)); return
    evidence = Evidence(args.directory)
    if args.command == 'status':
        rows = evidence.records()
        print(json.dumps({'planSha256': evidence.plan_hash,
              'counts': {arm: sum(r['arm'] == arm and r['status'] == 'evaluated' for r in rows)
                         for arm in ('baseline', 'micro', 'lhs', 'tpe', 'random', 'confirm')},
              'refused': sum(r['status'] != 'evaluated' for r in rows)}, indent=2)); return
    if not args.live:
        parser.error('Use --live to authorize local GPU work')
    if args.max_seconds <= 0 or args.evaluation_limit is not None and args.evaluation_limit < 1:
        parser.error('Budgets must be positive')
    with acquire_lock(evidence.root / 'study.lock'), Runtime() as runtime:
        verify_runtime(evidence, runtime)
        if args.command == 'noise': noise(evidence, runtime)
        elif args.command == 'search': search(evidence, runtime, max_seconds=args.max_seconds, evaluation_limit=args.evaluation_limit)
        elif args.command == 'confirm': confirm(evidence, runtime)


if __name__ == '__main__':
    main()
