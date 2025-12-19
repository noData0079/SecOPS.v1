import json
from pathlib import Path
from typing import List

import numpy as np
import tensorflow as tf

BASE_DIR = Path(__file__).resolve().parent
WEIGHTS_PATH = BASE_DIR / "artifacts" / "model.keras"
CONFIG_PATH = BASE_DIR / "config" / "model_config.json"


def load_labels() -> List[str]:
    if not CONFIG_PATH.exists():
        return ["label"]

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config.get("class_labels", ["label"])


def _build_fallback_model(input_shape: tuple) -> tf.keras.Model:
    model = tf.keras.Sequential(
        [
            tf.keras.layers.InputLayer(input_shape=input_shape),
            tf.keras.layers.Rescaling(1.0 / 255.0),
            tf.keras.layers.Conv2D(8, 3, activation="relu"),
            tf.keras.layers.GlobalAveragePooling2D(),
            tf.keras.layers.Dense(len(load_labels()), activation="softmax"),
        ]
    )
    return model


def load_model() -> tf.keras.Model:
    input_shape = (224, 224, 3)
    if WEIGHTS_PATH.exists():
        return tf.keras.models.load_model(WEIGHTS_PATH)

    return _build_fallback_model(input_shape)


class ProjectAModel:
    def __init__(self) -> None:
        self.model = load_model()
        self.labels = load_labels()

    def predict(self, processed_image: np.ndarray) -> dict:
        predictions = self.model.predict(processed_image)
        label_index = int(np.argmax(predictions, axis=1)[0])
        return {
            "label": self.labels[label_index] if label_index < len(self.labels) else str(label_index),
            "confidence": float(predictions[0][label_index]),
        }
