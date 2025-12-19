"""Simple AI model implementation for Project A.

The model loads lightweight configuration and weight metadata from the
local ``data`` directory and exposes a ``predict`` method that expects a
normalized numpy array.
"""

import json
import os
from typing import Any, Dict

import numpy as np


class SimpleImageModel:
    """Toy model that scores an array and returns a label.

    This is intentionally lightweight but demonstrates how the model
    could resolve on-disk resources after being moved under the
    ``project_a`` subfolder.
    """

    def __init__(self) -> None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        with open(os.path.join(data_dir, "config.json"), "r", encoding="utf-8") as config_file:
            self.config = json.load(config_file)
        with open(os.path.join(data_dir, "weights.json"), "r", encoding="utf-8") as weights_file:
            self.weights = json.load(weights_file)

    def predict(self, image_array: np.ndarray) -> Dict[str, Any]:
        """Generate a deterministic prediction for the provided array."""
        normalized = (image_array - image_array.min()) / max(image_array.ptp(), 1e-8)
        score = float(normalized.mean()) * self.weights["mean_multiplier"]
        if score > self.config["threshold"]:
            label = "high-signal"
        else:
            label = "low-signal"
        return {"label": label, "score": round(score, 4)}
