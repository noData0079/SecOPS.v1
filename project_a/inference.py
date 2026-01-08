"""Unified inference entrypoint for the t79 library."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .model import T79CoreModel, SimpleImageModel

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "data" / "t79" / "model_config.json"


def load_model_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)


class T79Inference:
    """Lightweight proxy that exposes t79 predictions."""

    def __init__(self) -> None:
        self.model = T79CoreModel(load_model_config())

    def predict(self, text: str) -> Dict[str, Any]:
        return self.model.predict(text)


class T79ImageInference:
    """Inference helper for the tiny demo image model."""

    def __init__(self) -> None:
        self._model = SimpleImageModel()

    def predict(self, image_array) -> Dict[str, Any]:
        return self._model.predict(image_array)


def predict(text: str) -> Dict[str, Any]:
    return T79Inference().predict(text)


def predict_image(image_array) -> Dict[str, Any]:
    return T79ImageInference().predict(image_array)


__all__ = [
    "T79Inference",
    "T79ImageInference",
    "T79CoreModel",
    "load_model_config",
    "predict",
    "predict_image",
]
