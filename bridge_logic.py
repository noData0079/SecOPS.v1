"""Direct access to the unified t79 inference without path hacks."""

from __future__ import annotations

from typing import Any, Dict, Union

from project_a import T79Inference

T79Payload = Union[str, Dict[str, Any]]


def _normalize_payload(payload: T79Payload) -> str:
    if isinstance(payload, dict):
        candidate = payload.get("data") or payload.get("text") or payload.get("payload")
        if isinstance(candidate, bytes):
            return candidate.decode("utf-8")
        if isinstance(candidate, str):
            return candidate
        raise ValueError("Unsupported dictionary payload structure for t79 input")
    if isinstance(payload, bytes):
        return payload.decode("utf-8")
    if isinstance(payload, str):
        return payload
    raise TypeError(f"Unsupported payload type: {type(payload)!r}")


def run_inference(payload: T79Payload) -> Dict[str, Any]:
    normalized = _normalize_payload(payload)
    return T79Inference().predict(normalized)


__all__ = ["run_inference", "T79Payload"]
