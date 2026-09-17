"""Validation for the exact DoMINO artifact bundle used by Zephyr."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ArtifactCheck:
    path: str
    purpose: str
    exists: bool
    nonempty: bool
    expected_sha256: str | None
    actual_sha256: str | None
    checksum_matches: bool | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = data.get("required")
    if not isinstance(required, list) or not required:
        raise ValueError("Artifact manifest must contain a non-empty 'required' list")
    return data


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_bundle(manifest_path: Path, assets_dir: Path) -> list[ArtifactCheck]:
    manifest = load_manifest(manifest_path)
    checks: list[ArtifactCheck] = []
    for item in manifest["required"]:
        relative = Path(item["path"])
        candidate = assets_dir / relative
        exists = candidate.is_file()
        nonempty = exists and candidate.stat().st_size > 0
        expected = item.get("sha256")
        actual = _file_sha256(candidate) if nonempty and expected else None
        matches = actual == expected if expected and actual else None
        checks.append(
            ArtifactCheck(
                path=relative.as_posix(),
                purpose=str(item["purpose"]),
                exists=exists,
                nonempty=nonempty,
                expected_sha256=expected,
                actual_sha256=actual,
                checksum_matches=matches,
            )
        )
    return checks


def bundle_ready(checks: list[ArtifactCheck]) -> bool:
    return bool(checks) and all(
        item.exists
        and item.nonempty
        and item.checksum_matches is not False
        for item in checks
    )

