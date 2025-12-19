"""Project A package exposing the demo AI model."""

from .inference import ProjectAModel, load_model_config, predict
from .model import SecurityInferenceModel

__all__ = ["ProjectAModel", "load_model_config", "predict", "SecurityInferenceModel"]
