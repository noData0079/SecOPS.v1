from __future__ import annotations

import json
import os
from typing import Any, Dict

from .model import ProjectAModel

PROJECT_ROOT = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "model_config.json")


def load_model_config() -> Dict[str, Any]:
    """Load the Project A model configuration relative to this package."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


__all__ = ["ProjectAModel", "load_model_config"]
