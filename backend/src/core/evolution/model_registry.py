"""
Model Registry - Manages model versions and their paths.
"""
import os
import json
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class ModelRegistry:
    def __init__(self, registry_file: str = "backend/data/model_registry.json"):
        self.registry_file = registry_file
        self.models: Dict[str, Any] = {}
        self._load_registry()

    def _load_registry(self):
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    self.models = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load registry: {e}")
                self.models = {}
        else:
            # Initialize with default
             self.models = {
                "v1.0.1-human-vetted": {
                    "path": "models/tsm99_prod_v1",
                    "status": "STABLE",
                    "description": "Initial baseline"
                }
            }
             self._save_registry()

    def _save_registry(self):
        os.makedirs(os.path.dirname(self.registry_file), exist_ok=True)
        try:
            with open(self.registry_file, 'w') as f:
                json.dump(self.models, f, indent=4)
        except Exception as e:
             logger.error(f"Failed to save registry: {e}")

    def get_stable_path(self, version: str) -> str:
        """Returns the path for a given stable version."""
        if version in self.models:
            return self.models[version]["path"]
        raise ValueError(f"Version {version} not found in registry.")

    def register_model(self, version: str, path: str, description: str = ""):
        """Registers a new model version."""
        self.models[version] = {
            "path": path,
            "status": "CANDIDATE",
            "description": description
        }
        self._save_registry()
        logger.info(f"Registered model {version} at {path}")

    def quarantine_failed_model(self, reason: str):
        """Marks the current candidate as failed/quarantined."""
        # Find the most recent candidate or just log it.
        # For simplicity, we just log it as a generic quarantine event in the registry metadata if we had one.
        logger.warning(f"Quarantining failed model due to: {reason}")
        # In a real system, we'd update the specific version's status

    def promote_to_stable(self, version: str):
        if version in self.models:
            self.models[version]["status"] = "STABLE"
            self._save_registry()
            logger.info(f"Promoted {version} to STABLE")

# Global instance
model_registry = ModelRegistry()
