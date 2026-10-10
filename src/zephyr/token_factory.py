"""Minimal, dependency-free client for Nebius Token Factory capability probes."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://api.tokenfactory.nebius.com/v1"


class TokenFactoryError(RuntimeError):
    """A sanitized Token Factory request or response failure."""


@dataclass(frozen=True)
class ModelInfo:
    id: str
    owned_by: str | None = None


def parse_model_list(payload: dict[str, Any]) -> list[ModelInfo]:
    data = payload.get("data")
    if not isinstance(data, list):
        raise TokenFactoryError("Model response did not contain a 'data' list")
    models: list[ModelInfo] = []
    for item in data:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise TokenFactoryError("Model response contained an invalid model entry")
        models.append(ModelInfo(id=item["id"], owned_by=item.get("owned_by")))
    return models


def parse_structured_message(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        choice = payload["choices"][0]
        if choice.get("finish_reason") == "length":
            raise TokenFactoryError("Structured response hit its token limit; no constraints were accepted")
        message = choice["message"]
        refusal = message.get("refusal")
        content = message["content"]
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise TokenFactoryError("Completion response did not contain a message") from exc
    if refusal:
        raise TokenFactoryError("Selected model refused the structured probe")
    if not isinstance(content, str):
        raise TokenFactoryError("Completion message did not contain text JSON")
    try:
        decoded = json.loads(content)
    except json.JSONDecodeError as exc:
        raise TokenFactoryError("Completion message was not valid JSON") from exc
    if not isinstance(decoded, dict):
        raise TokenFactoryError("Completion JSON was not an object")
    return decoded


class TokenFactoryClient:
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0):
        if not api_key:
            raise ValueError("api_key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = Request(f"{self._base_url}{path}", data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self._timeout) as response:
                decoded = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise TokenFactoryError(f"Token Factory returned HTTP {exc.code}") from exc
        except URLError as exc:
            raise TokenFactoryError("Token Factory could not be reached") from exc
        except json.JSONDecodeError as exc:
            raise TokenFactoryError("Token Factory returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise TokenFactoryError("Token Factory returned a non-object response")
        return decoded

    def list_models(self, ai_project_id: str | None = None) -> list[ModelInfo]:
        query = urlencode({"ai_project_id": ai_project_id}) if ai_project_id else ""
        suffix = f"?{query}" if query else ""
        return parse_model_list(self._request_json("GET", f"/models{suffix}"))

    def complete_json(self, model: str, system: str, user: str | list[dict[str, Any]], schema: dict[str, Any],
                      *, name: str, ai_project_id: str | None = None, max_tokens: int = 2048):
        """One bounded structured call. Return content and credential-free provenance."""
        import time
        query = urlencode({"ai_project_id": ai_project_id}) if ai_project_id else ""
        suffix = f"?{query}" if query else ""
        payload = {"model": model, "messages": [{"role": "system", "content": system},
                   {"role": "user", "content": user}], "temperature": 0, "max_tokens": max_tokens,
                   "response_format": {"type": "json_schema", "json_schema": {
                       "name": name, "strict": True, "schema": schema}}}
        started = time.perf_counter()
        response = self._request_json("POST", f"/chat/completions{suffix}", payload)
        value = parse_structured_message(response)
        return value, {"model": response.get("model", model), "requestedModel": model,
                       "seconds": round(time.perf_counter() - started, 3),
                       "usage": response.get("usage"), "schema": name}

    def probe_constraint_schema(self, model: str, ai_project_id: str | None = None) -> dict[str, Any]:
        schema = {
            "name": "zephyr_constraint_probe",
            "schema": {
                "type": "object",
                "properties": {
                    "objective": {"type": "string", "enum": ["reduce_drag"]},
                    "locked_regions": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["cabin"]},
                        "minItems": 1,
                        "maxItems": 1,
                    },
                    "max_displacement_mm": {"type": "number", "minimum": 0, "maximum": 4},
                },
                "required": ["objective", "locked_regions", "max_displacement_mm"],
                "additionalProperties": False,
            },
            "strict": True,
        }
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Compile the aerodynamic instruction into the supplied JSON schema. Do not add assumptions.",
                },
                {
                    "role": "user",
                    "content": "Reduce drag. Keep the cabin unchanged. Maximum displacement: 4 mm.",
                },
            ],
            "response_format": {"type": "json_schema", "json_schema": schema},
            "temperature": 0,
            # Reasoning models share this budget between reasoning and the final JSON.
            "max_tokens": 1024,
        }
        query = urlencode({"ai_project_id": ai_project_id}) if ai_project_id else ""
        suffix = f"?{query}" if query else ""
        return parse_structured_message(self._request_json("POST", f"/chat/completions{suffix}", payload))


def is_nvidia_candidate(model: ModelInfo) -> bool:
    normalized = f"{model.id} {model.owned_by or ''}".lower()
    return "nvidia" in normalized or "nemotron" in normalized


def validate_constraint_probe(value: dict[str, Any]) -> bool:
    return (
        set(value) == {"objective", "locked_regions", "max_displacement_mm"}
        and value["objective"] == "reduce_drag"
        and value["locked_regions"] == ["cabin"]
        and value["max_displacement_mm"] == 4
    )
