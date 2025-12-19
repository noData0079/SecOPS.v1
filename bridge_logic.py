"""Bridge layer between Project B (FastAPI app) and Project A (AI model).

The bridge dynamically exposes Project A's inference API while keeping
changes to both codebases minimal.
"""

from __future__ import annotations

import base64
import json
import os
import sys
from typing import Any, Dict, List

import numpy as np

PROJECT_A_PATH = os.path.join(os.path.dirname(__file__), "project_a")
if PROJECT_A_PATH not in sys.path:
    sys.path.insert(0, PROJECT_A_PATH)

from project_a import inference as project_a_inference


class AIBridge:
    """Singleton bridge that adapts Project B payloads for Project A."""

    _instance: "AIBridge | None" = None

    def __new__(cls) -> "AIBridge":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = project_a_inference
        return cls._instance

    def execute(self, encoded_payload: str) -> Dict[str, Any]:
        """Convert Project B payload to Project A format and run inference."""
        image_array = self._decode_payload(encoded_payload)
        prediction = self._model.predict(image_array)
        return {"status": "success", "prediction": prediction}

    def _decode_payload(self, encoded_payload: str) -> np.ndarray:
        """Decode base64-encoded JSON data into a numpy array.

        Project B sends a base64 string containing JSON with ``width``,
        ``height``, and ``data`` fields. ``data`` is expected to be a flat
        list of grayscale pixel intensities.
        """
        decoded_bytes = base64.b64decode(encoded_payload.encode("utf-8"))
        payload = json.loads(decoded_bytes.decode("utf-8"))
        width = int(payload.get("width", 0))
        height = int(payload.get("height", 0))
        data: List[float] = payload.get("data", [])
        if width * height != len(data):
            raise ValueError("Invalid payload dimensions")
        array = np.array(data, dtype=float).reshape((height, width))
        return array
