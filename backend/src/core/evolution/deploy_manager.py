from typing import Any, Dict
import logging
from backend.src.core.evolution.shadow_mirror import ShadowMirror
from backend.src.core.outcomes.comparator import Comparator

logger = logging.getLogger(__name__)

class DeployManager:
    """
    Manages the deployment of shadow services and request mirroring.
    """
    def __init__(self, baseline_service: Any, shadow_service: Any):
        self.comparator = Comparator()
        self.mirror = ShadowMirror(baseline_service, shadow_service, self.comparator)

    def process_request(self, payload: Any) -> Any:
        """
        Entry point for requests. Routes them through the Shadow Mirror.
        """
        logger.info("DeployManager processing request through ShadowMirror")
        return self.mirror.handle_request(payload)
