"""t79 core inference models and lightweight heuristics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "data" / "t79"

KEYWORD_CONFIG_PATH = DATA_ROOT / "keyword_config.json"
MODEL_CONFIG_PATH = DATA_ROOT / "model_config.json"
WEIGHTS_PATH = DATA_ROOT / "weights" / "dummy_weights.txt"
SIMPLE_CONFIG_PATH = DATA_ROOT / "simple" / "config.json"
SIMPLE_WEIGHTS_PATH = DATA_ROOT / "simple" / "weights.json"


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _load_checksum(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as weights_file:
        return sum(ord(char) for char in weights_file.read())


class SecurityInferenceModel:
    """Keyword-driven classifier used by the t79 stack."""

    def __init__(self, config_path: Path | None = None, weights_path: Path | None = None) -> None:
        self.config_path = config_path or KEYWORD_CONFIG_PATH
        self.weights_path = weights_path or WEIGHTS_PATH
        config = _load_json(self.config_path)
        self.labels: List[str] = config.get("labels", [])
        self.keywords: Dict[str, List[str]] = config.get("keywords", {})
        self.weights_checksum = _load_checksum(self.weights_path)

    def predict(self, text: str) -> Dict[str, Any]:
        normalized = text.lower()
        for label in ("critical", "suspicious"):
            for keyword in self.keywords.get(label, []):
                if keyword in normalized:
                    return {
                        "label": label,
                        "reason": f"matched keyword '{keyword}'",
                        "weights_checksum": self.weights_checksum,
                    }
        return {"label": "benign", "reason": "no keywords matched", "weights_checksum": self.weights_checksum}


class SimpleImageModel:
    """Tiny image scorer that reads its weights from the consolidated data folder."""

    def __init__(self) -> None:
        self.config = _load_json(SIMPLE_CONFIG_PATH)
        self.weights = _load_json(SIMPLE_WEIGHTS_PATH)

    def predict(self, image_array: np.ndarray) -> Dict[str, Any]:
        normalized = (image_array - image_array.min()) / max(image_array.ptp(), 1e-8)
        score = float(normalized.mean()) * self.weights.get("mean_multiplier", 1.0)
        label = "high-signal" if score > self.config.get("threshold", 0.5) else "low-signal"
        return {"label": label, "score": round(score, 4)}


class T79CoreModel:
    """Primary text inference model used throughout the unified t79 project."""

    def __init__(self, config: Dict[str, Any] | Path | None = None) -> None:
        self.config_path = MODEL_CONFIG_PATH if config is None or isinstance(config, dict) else config
        self.config = config if isinstance(config, dict) else _load_json(self.config_path)
        self.keyword_model = SecurityInferenceModel()

    def _build_prompt(self, text: str) -> str:
        template = self.config.get("prompt_template", "{text}")
        return template.replace("{text}", text)

    def predict(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        classification = self.keyword_model.predict(cleaned)
        confidence = min(1.0, self.config.get("confidence_base", 0.5) + len(cleaned.split()) * 0.01)
        return {
            "model": self.config.get("model_name", "t79"),
            "provider": self.config.get("provider", "local"),
            "version": self.config.get("version", "unknown"),
            "prompt": self._build_prompt(cleaned),
            "classification": classification,
            "tokens_processed": max(1, len(cleaned.split())),
            "confidence": round(confidence, 3),
        }


def predict(text: str) -> Dict[str, Any]:
    return T79CoreModel().predict(text)


__all__ = [
    "SecurityInferenceModel",
    "SimpleImageModel",
    "T79CoreModel",
    "predict",
]
