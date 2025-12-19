from __future__ import annotations

import base64
import os
import sys
from threading import Lock
from typing import Any, Dict, Optional, Union

PROJECT_A_PATH = os.path.join(os.path.dirname(__file__), "project_a")
if PROJECT_A_PATH not in sys.path:
    sys.path.insert(0, PROJECT_A_PATH)

from project_a.inference import ProjectAModel  # type: ignore  # noqa: E402

ProjectBPayload = Union[str, bytes, Dict[str, Any]]


class ProjectABridge:
    """Adapter that translates Project B payloads into Project A inputs."""

    _instance: Optional["ProjectABridge"] = None
    _lock: Lock = Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "ProjectABridge":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._model: Optional[ProjectAModel] = None
        return cls._instance

    def __init__(self) -> None:
        if self._model is None:
            self._model = ProjectAModel()

    def _normalize_payload(self, payload: ProjectBPayload) -> str:
        """Convert Project B payloads to the plain-text format Project A expects."""

        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")

        if isinstance(payload, str):
            try:
                decoded = base64.b64decode(payload, validate=True)
                return decoded.decode("utf-8")
            except Exception:
                return payload

        if isinstance(payload, dict):
            candidate = payload.get("data") or payload.get("text")
            if isinstance(candidate, bytes):
                candidate = candidate.decode("utf-8")
            if isinstance(candidate, str):
                return self._normalize_payload(candidate)
            raise ValueError("Unsupported dictionary payload structure for Project B input")

        raise TypeError(f"Unsupported payload type: {type(payload)!r}")

    def execute(self, project_b_payload: ProjectBPayload) -> Dict[str, Any]:
        """Run Project A inference and return a Project B-friendly response."""

        text_input = self._normalize_payload(project_b_payload)
        prediction = self._model.predict(text_input)
        return {
            "status": "success",
            "input": text_input,
            "data": prediction,
        }


__all__ = ["ProjectABridge", "ProjectBPayload"]
