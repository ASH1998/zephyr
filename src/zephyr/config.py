"""Dependency-free runtime configuration for Zephyr's Token Factory model."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import sys

from zephyr.token_factory import DEFAULT_BASE_URL


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_ENV_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ConfigurationError(ValueError):
    """Raised when runtime model configuration is invalid or incomplete."""


@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    model: str
    api_key: str
    ai_project_id: str

    def sanitized(self) -> dict[str, str | bool]:
        """Return diagnostics that are safe to print and persist."""
        return {
            "base_url": self.base_url,
            "model": self.model,
            "api_key_present": bool(self.api_key),
            "ai_project_id_present": bool(self.ai_project_id),
        }


def load_env_file(
    path: str | Path = REPOSITORY_ROOT / ".env",
    *,
    environ: MutableMapping[str, str] | None = None,
    override: bool = False,
) -> bool:
    """Load simple KEY=VALUE entries without overriding shell values by default."""
    target = Path(path)
    if not target.is_file():
        return False
    destination = os.environ if environ is None else environ
    for line_number, raw_line in enumerate(target.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ConfigurationError(f"Invalid .env entry on line {line_number}")
        key, value = (part.strip() for part in line.split("=", 1))
        if not _ENV_KEY.fullmatch(key):
            raise ConfigurationError(f"Invalid environment key on line {line_number}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if override or key not in destination:
            destination[key] = value
    return True


def load_llm_config(
    environ: Mapping[str, str] | None = None,
    *,
    require_credentials: bool = False,
) -> LlmConfig:
    """Resolve the active model while keeping the API key out of diagnostics."""
    values = os.environ if environ is None else environ
    base_url = values.get("ZEPHYR_TOKEN_FACTORY_BASE_URL", DEFAULT_BASE_URL).strip()
    model = values.get("ZEPHYR_ACTIVE_MODEL", "").strip()
    primary_model = values.get("ZEPHYR_NEMOTRON_MODEL", "").strip()
    alternate_url = values.get("ZEPHYR_TOKEN_FACTORY_BASE_URL_V2", "").strip()
    if primary_model and model != primary_model and alternate_url:
        base_url = alternate_url
    api_key = values.get("NEBIUS_API_KEY", "").strip()
    project_id = values.get("NEBIUS_AI_PROJECT_ID", "").strip()
    if not base_url:
        raise ConfigurationError("ZEPHYR_TOKEN_FACTORY_BASE_URL is not configured")
    if require_credentials and not model:
        raise ConfigurationError("ZEPHYR_ACTIVE_MODEL is not configured")
    if require_credentials and not api_key:
        raise ConfigurationError("NEBIUS_API_KEY is not configured")
    return LlmConfig(base_url.rstrip("/"), model, api_key, project_id)


def main(argv: list[str] | None = None) -> int:
    """Print active configuration without ever exposing credentials."""
    del argv
    try:
        load_env_file()
        config = load_llm_config()
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(config.sanitized(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
