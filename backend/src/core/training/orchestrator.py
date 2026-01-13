import os
import logging
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Kaggle API might need env vars: KAGGLE_USERNAME, KAGGLE_KEY
try:
    from kaggle.api.kaggle_api_extended import KaggleApi
except (ImportError, OSError, Exception) as e:
    # Handle cases where Kaggle is not installed or configured, preventing import crash
    KaggleApi = None

from src.core.training.synthesizer import DeepSeekSynthesizer
from src.core.training.gatekeeper import DataCleaner
from src.core.training.feedback_loop import get_feedback_collector

logger = logging.getLogger(__name__)

class TrainingOrchestrator:
    """
    Recursive Training Orchestrator.

    Manages the distillation loop:
    Synthesize -> Clean -> Ship to Kaggle -> Train -> Retrieve
    """

    def __init__(self):
        self.api = None
        self._authenticated = False

        if KaggleApi:
            try:
                # Check if Kaggle config exists or env vars are set before authenticating to avoid SystemExit
                if os.getenv("KAGGLE_USERNAME") or os.path.exists(os.path.expanduser("~/.kaggle/kaggle.json")):
                    self.api = KaggleApi()
                    self.api.authenticate()
                    self._authenticated = True
                else:
                    logger.warning("Kaggle credentials not found. Remote training will be disabled.")
            except Exception as e:
                logger.error(f"Kaggle authentication failed: {e}")
        else:
            logger.warning("Kaggle API module not loaded. Remote training will be disabled.")

        self.synthesizer = DeepSeekSynthesizer()
        self.cleaner = DataCleaner()
        self.is_training = False
        self.current_status = "IDLE"
        self.gigo_stats = {"total": 0, "rejected": 0}

    async def start_training_run(self, count: int = 100):
        """
        The 'One-Click' Entry Point.
        """
        if self.is_training:
            logger.warning("Training already in progress.")
            return

        if not self._authenticated or not self.api:
             logger.error("Cannot start training: Kaggle not authenticated.")
             self.current_status = "ERROR: Kaggle Auth Failed"
             return

        self.is_training = True
        self.current_status = "SYNTHESIZING"
        logger.info("[TRAINING] Initiating Recursive IT Distillation...")

        try:
            # 1. Generate & Filter Data
            # Generate in batches to avoid huge prompts/timeouts
            batch_size = 10
            raw_data = []
            for _ in range(0, count, batch_size):
                batch = await self.synthesizer.generate_it_scenarios(count=batch_size)
                raw_data.extend(batch)

            # 1.5 Inject Human Feedback Data
            feedback_collector = get_feedback_collector()
            human_data = feedback_collector.get_training_examples()
            if human_data:
                logger.info(f"[TRAINING] Injecting {len(human_data)} human-verified examples.")
                # We prioritize human data by appending it to raw_data.
                # Note: We might want to skip cleaning for human data or ensure it passes too.
                # For now, we trust human feedback more, so we might bypass cleaner or allow it.
                # Let's treat it as raw_data so it goes through the same format checks,
                # but potentially we should mark it to bypass strict filtering if needed.
                raw_data.extend(human_data)

            self.current_status = "CLEANING"
            clean_data = await self.cleaner.filter_garbage(raw_data)

            # Update stats
            self.gigo_stats["total"] = len(raw_data)
            self.gigo_stats["rejected"] = len(raw_data) - len(clean_data)

            if not clean_data:
                logger.warning("No clean data generated. Aborting.")
                self.current_status = "FAILED: No Data"
                self.is_training = False
                return

            # 2. Update Kaggle Dataset
            self.current_status = "UPLOADING"
            dataset_slug = "tsm99-it-distillation-data"
            owner_slug = "tsm99" # Placeholder, user needs to set this

            # Use current directory for temporary file
            dataset_dir = "backend/data/training_upload"
            os.makedirs(dataset_dir, exist_ok=True)

            with open(f'{dataset_dir}/training_data.jsonl', 'w') as f:
                for item in clean_data:
                    f.write(json.dumps(item) + "\n")

            # Create metadata if not exists
            meta_file = f'{dataset_dir}/dataset-metadata.json'
            if not os.path.exists(meta_file):
                with open(meta_file, 'w') as f:
                    json.dump({
                        "title": "TSM99 IT Distillation Data",
                        "id": f"{owner_slug}/{dataset_slug}",
                        "licenses": [{"name": "CC0-1.0"}]
                    }, f)

            # Check if dataset exists, if not create, else version update
            try:
                self.api.dataset_create_version(
                    dataset_dir,
                    version_notes=f"Auto-generated update {datetime.now()}"
                )
            except Exception:
                # If it doesn't exist, try create (might need better handling of owner)
                try:
                    self.api.dataset_create_new(dataset_dir)
                except Exception as e:
                    logger.error(f"Failed to upload dataset: {e}")
                    # Continue anyway for now, assuming manual upload or existing data

            # 3. Trigger Kaggle GPU
            self.current_status = "TRAINING_REMOTE"
            self.trigger_kaggle_gpu()

            self.current_status = "COMPLETED_SUBMISSION"

        except Exception as e:
            logger.error(f"Training run failed: {e}")
            self.current_status = f"ERROR: {str(e)}"
        finally:
            self.is_training = False

    def trigger_kaggle_gpu(self):
        """Triggers the remote Kaggle Kernel for Llama 3.3 Fine-tuning."""
        if not self.api:
            logger.error("Kaggle API not initialized.")
            return

        # Pushes local kernel metadata to Kaggle to start execution
        kernel_dir = 'backend/src/core/training/kaggle_scripts'
        try:
            self.api.kernels_push(kernel_dir)
            logger.info("[KAGGLE] GPU Fine-tuning Session Started. Monitoring logs...")
        except Exception as e:
             logger.error(f"Failed to push kernel: {e}")

    def stop_training_run(self):
        """Emergency Stop."""
        logger.info("[TRAINING] Halt Signal Sent.")
        self.is_training = False
        self.current_status = "STOPPED"

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_training": self.is_training,
            "status": self.current_status,
            "gigo_stats": self.gigo_stats
        }

# Global instance
_orchestrator = None

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = TrainingOrchestrator()
    return _orchestrator
