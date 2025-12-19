import base64
import sys
from functools import lru_cache
from io import BytesIO
from typing import Any, Dict

from PIL import Image

PROJECT_A_PATH = "./project_a"
if PROJECT_A_PATH not in sys.path:
    sys.path.append(PROJECT_A_PATH)

from project_a import ProjectAModel, preprocess_image


class ProjectABridge:
    """
    Adapter that translates Project B inputs to Project A's inference interface.

    - Dynamically injects `./project_a` onto `sys.path`.
    - Converts Project B base64 image payloads into numpy arrays for Project A.
    - Uses a singleton Project A model instance to avoid repeated allocations.
    """

    def __init__(self) -> None:
        self.model = self._get_model_instance()

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_model_instance() -> ProjectAModel:
        return ProjectAModel()

    def run_inference(self, base64_payload: str) -> Dict[str, Any]:
        processed = preprocess_image(base64_payload)
        result = self.model.predict(processed)
        return {
            "status": "success",
            "data": result,
        }

    @staticmethod
    def encode_prediction_image(prediction_map: Dict[str, Any]) -> str:
        buffer = BytesIO()
        image = Image.new("RGB", (200, 50), color=(0, 0, 0))
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
