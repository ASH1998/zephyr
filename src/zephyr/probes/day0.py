"""Generate a sanitized Day-0 capability report."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any

from zephyr.artifacts import bundle_ready, validate_bundle
from zephyr.config import load_env_file
from zephyr.token_factory import (
    DEFAULT_BASE_URL,
    TokenFactoryClient,
    TokenFactoryError,
    is_nvidia_candidate,
    validate_constraint_probe,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-models", action="store_true", help="Call Token Factory GET /v1/models")
    parser.add_argument("--structured-model", help="Run the strict Zephyr schema probe against this live model ID")
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=Path(os.environ.get("ZEPHYR_DOMINO_ASSETS_DIR", REPOSITORY_ROOT / ".local" / "domino-assets")),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=REPOSITORY_ROOT / "config" / "domino-artifacts.json",
    )
    parser.add_argument("--output", type=Path, help="Write the sanitized JSON report to this path")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero unless every requested gate passes")
    return parser


def make_report(args: argparse.Namespace) -> dict[str, Any]:
    api_key = os.environ.get("NEBIUS_API_KEY", "")
    project_id = os.environ.get("NEBIUS_AI_PROJECT_ID", "")
    base_url = os.environ.get("ZEPHYR_TOKEN_FACTORY_BASE_URL", DEFAULT_BASE_URL)
    checks = validate_bundle(args.manifest, args.assets_dir)
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "probe_version": 1,
        "environment": {
            "nebius_api_key_present": bool(api_key),
            "nebius_ai_project_id_present": bool(project_id),
            "token_factory_base_url": base_url,
        },
        "domino_bundle": {
            "assets_dir": str(args.assets_dir.resolve()),
            "ready": bundle_ready(checks),
            "files": [item.to_dict() for item in checks],
        },
        "token_factory": {
            "requested": args.live_models,
            "reachable": None,
            "model_count": None,
            "nvidia_candidates": [],
            "selected_model_present": None,
            "structured_probe": None,
            "error": None,
        },
    }

    if args.structured_model and not args.live_models:
        report["token_factory"]["error"] = "--structured-model requires --live-models"
        return report
    if not args.live_models:
        return report
    if not api_key:
        report["token_factory"]["error"] = "NEBIUS_API_KEY is not configured"
        return report

    client = TokenFactoryClient(api_key=api_key, base_url=base_url)
    try:
        models = client.list_models(project_id or None)
        model_ids = {model.id for model in models}
        candidates = [model.id for model in models if is_nvidia_candidate(model)]
        report["token_factory"].update(
            {
                "reachable": True,
                "model_count": len(models),
                "nvidia_candidates": sorted(candidates),
                "selected_model_present": args.structured_model in model_ids if args.structured_model else None,
            }
        )
        if args.structured_model:
            if args.structured_model not in model_ids:
                report["token_factory"]["structured_probe"] = {
                    "passed": False,
                    "error": "Selected model ID is absent from the live catalog",
                }
            else:
                value = client.probe_constraint_schema(args.structured_model, project_id or None)
                report["token_factory"]["structured_probe"] = {
                    "passed": validate_constraint_probe(value),
                    "value": value,
                }
    except TokenFactoryError as exc:
        report["token_factory"]["reachable"] = False
        report["token_factory"]["error"] = str(exc)
    return report


def requested_gates_pass(report: dict[str, Any]) -> bool:
    if not report["domino_bundle"]["ready"]:
        return False
    token_factory = report["token_factory"]
    if token_factory["requested"] and token_factory["reachable"] is not True:
        return False
    structured = token_factory["structured_probe"]
    if structured is not None and structured.get("passed") is not True:
        return False
    return token_factory.get("error") is None


def main(argv: list[str] | None = None) -> int:
    load_env_file(REPOSITORY_ROOT / ".env")
    args = build_parser().parse_args(argv)
    report = make_report(args)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{rendered}\n", encoding="utf-8")
    return 1 if args.strict and not requested_gates_pass(report) else 0


if __name__ == "__main__":
    sys.exit(main())
