from __future__ import annotations

import json
import os
from typing import Any, Dict, List

PROJECT_ROOT = os.path.dirname(__file__)
MODEL_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "model_config.json")
LABEL_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "config.json")
WEIGHTS_PATH = os.path.join(PROJECT_ROOT, "weights", "dummy_weights.txt")


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


class ProjectAModel:
    """Demo AI model that classifies text inputs.

    The model keeps path resolution relative to this module so moving the
    project under a different directory does not break config or weight loads.
    """

    def __init__(self) -> None:
        self.model_config = _load_json(MODEL_CONFIG_PATH)
        label_config = _load_json(LABEL_CONFIG_PATH)
        self.labels: List[str] = label_config.get("labels", [])
        self.keyword_map: Dict[str, List[str]] = label_config.get("keywords", {})
        self.weights_checksum = self._load_weights_checksum()

    def _load_weights_checksum(self) -> int:
        with open(WEIGHTS_PATH, "r", encoding="utf-8") as weights_file:
            return sum(ord(char) for char in weights_file.read())

    def _classify(self, normalized_text: str) -> str:
        for label in ("critical", "suspicious"):
            for keyword in self.keyword_map.get(label, []):
                if keyword in normalized_text:
                    return label
        return "benign"

    def predict(self, text: str) -> Dict[str, Any]:
        normalized = text.strip().lower()
        tokens = normalized.split()
        label = self._classify(normalized)
        prompt_template = self.model_config.get("prompt_template", "{text}")
        prompt = prompt_template.replace("{text}", text.strip())
        confidence = min(1.0, self.model_config.get("confidence_base", 0.5) + len(tokens) * 0.01)

        return {
            "model": self.model_config.get("model_name", "project_a"),
            "version": self.model_config.get("version", "unknown"),
            "weights_checksum": self.weights_checksum,
            "label": label,
            "token_count": len(tokens),
            "prompt": prompt,
            "confidence": round(confidence, 3),
        }


def predict(text: str) -> Dict[str, Any]:
    model = ProjectAModel()
    return model.predict(text)


__all__ = ["ProjectAModel", "predict"]
