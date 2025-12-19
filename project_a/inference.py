"""Public inference entrypoint for Project A."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .model import ProjectAModel, predict

_PROJECT_ROOT = Path(__file__).resolve().parent
_CONFIG_PATH = _PROJECT_ROOT / "config" / "model_config.json"


def load_model_config() -> Dict[str, Any]:
    """Load the model configuration relative to this module."""

    with _CONFIG_PATH.open("r", encoding="utf-8") as fp:
        return json.load(fp)


__all__ = ["ProjectAModel", "load_model_config", "predict"]
