# backend/src/fine_tune/trainer.py

"""Transformer-based and OpenAI fine-tuning utilities."""

from __future__ import annotations

import uuid
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================
# LOCAL TRANSFORMER FINE-TUNING
# ============================================

class LocalFineTuneEngine:
    """Run small causal language model fine-tunes using Hugging Face Transformers."""

    def __init__(
        self,
        *,
        base_model: str = "distilgpt2",
        output_root: str = "models/fine_tuned",
        max_length: int = 512,
    ) -> None:
        self.base_model = base_model
        self.output_root = Path(output_root)
        self.max_length = max_length
        self.output_root.mkdir(parents=True, exist_ok=True)

    def _load_tokenizer(self):
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        return tokenizer

    def _prepare_dataset(self, dataset_path: Path, tokenizer):
        from datasets import load_dataset
        raw = load_dataset("json", data_files=str(dataset_path))

        def tokenize(example: Dict[str, str]) -> Dict[str, Any]:
            text = f"{example['prompt']}\n\n{example['completion']}"
            tokenized = tokenizer(
                text,
                padding="max_length",
                truncation=True,
                max_length=self.max_length,
            )
            tokenized["labels"] = tokenized["input_ids"].copy()
            return tokenized

        return raw.map(tokenize)

    def start_job(
        self,
        dataset_path: str,
        *,
        learning_rate: float = 5e-5,
        epochs: int = 1,
        batch_size: int = 4,
        weight_decay: float = 0.01,
        warmup_steps: int = 10,
        seed: int = 42,
        report_to: Optional[str] = None,
    ) -> str:
        """Fine-tune a lightweight causal LM on the provided JSONL dataset."""
        from transformers import (
            AutoModelForCausalLM,
            DataCollatorForLanguageModeling,
            Trainer,
            TrainingArguments,
        )

        dataset_file = Path(dataset_path)
        run_id = f"ft-{uuid.uuid4().hex[:8]}"
        output_dir = self.output_root / run_id

        tokenizer = self._load_tokenizer()
        tokenized = self._prepare_dataset(dataset_file, tokenizer)

        model = AutoModelForCausalLM.from_pretrained(self.base_model)

        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False,
        )

        args = TrainingArguments(
            output_dir=str(output_dir),
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            num_train_epochs=epochs,
            learning_rate=learning_rate,
            weight_decay=weight_decay,
            warmup_steps=warmup_steps,
            seed=seed,
            logging_steps=5,
            save_steps=50,
            report_to=report_to if report_to else [],
            overwrite_output_dir=True,
        )

        trainer = Trainer(
            model=model,
            args=args,
            train_dataset=tokenized["train"],
            tokenizer=tokenizer,
            data_collator=data_collator,
        )
        trainer.train()

        model.save_pretrained(output_dir)
        tokenizer.save_pretrained(output_dir)

        return run_id


# ============================================
# OPENAI FINE-TUNING
# ============================================

class FineTuneStatus(str, Enum):
    """Fine-tuning job status."""
    PENDING = "pending"
    VALIDATING = "validating_files"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class FineTuneJob:
    """Fine-tuning job details."""
    job_id: str
    model: str
    training_file: str
    status: FineTuneStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    fine_tuned_model: Optional[str] = None
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "model": self.model,
            "training_file": self.training_file,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "fine_tuned_model": self.fine_tuned_model,
            "hyperparameters": self.hyperparameters,
            "error": self.error,
        }


class FineTuneEngine:
    """
    OpenAI fine-tuning engine with full job lifecycle management.
    
    Supports:
    - File upload for training data
    - Job creation with configurable hyperparameters
    - Job monitoring and status checking
    - Job cancellation
    - Listing available fine-tuned models
    """
    
    SUPPORTED_MODELS = [
        "gpt-4o-mini-2024-07-18",
        "gpt-4o-2024-08-06",
        "gpt-4-0613",
        "gpt-3.5-turbo-0125",
        "gpt-3.5-turbo-1106",
        "gpt-3.5-turbo-0613",
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize fine-tune engine."""
        import os
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None
        self._jobs: Dict[str, FineTuneJob] = {}
        logger.info("FineTuneEngine initialized")
    
    @property
    def client(self):
        """Get OpenAI client (lazy initialization)."""
        if self._client is None:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key)
        return self._client
    
    async def upload_training_file(self, file_path: str) -> str:
        """Upload a training file to OpenAI."""
        logger.info(f"Uploading training file: {file_path}")
        
        with open(file_path, "rb") as f:
            response = self.client.files.create(file=f, purpose="fine-tune")
        
        file_id = response.id
        logger.info(f"Training file uploaded: {file_id}")
        return file_id
    
    async def start_job(
        self,
        training_file: str,
        model: str = "gpt-4o-mini-2024-07-18",
        validation_file: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        suffix: Optional[str] = None,
    ) -> FineTuneJob:
        """Start a fine-tuning job."""
        if model not in self.SUPPORTED_MODELS:
            logger.warning(f"Model {model} may not support fine-tuning")
        
        logger.info(f"Starting fine-tune job with model {model}")
        
        job_params: Dict[str, Any] = {
            "training_file": training_file,
            "model": model,
        }
        
        if validation_file:
            job_params["validation_file"] = validation_file
        if suffix:
            job_params["suffix"] = suffix
        if hyperparameters:
            job_params["hyperparameters"] = hyperparameters
        
        response = self.client.fine_tuning.jobs.create(**job_params)
        
        job = FineTuneJob(
            job_id=response.id,
            model=model,
            training_file=training_file,
            status=FineTuneStatus(response.status),
            hyperparameters=hyperparameters or {},
        )
        
        self._jobs[job.job_id] = job
        logger.info(f"Fine-tune job started: {job.job_id}")
        
        return job
    
    async def get_job_status(self, job_id: str) -> FineTuneJob:
        """Get the current status of a fine-tuning job."""
        response = self.client.fine_tuning.jobs.retrieve(job_id)
        
        job = FineTuneJob(
            job_id=response.id,
            model=response.model,
            training_file=response.training_file,
            status=FineTuneStatus(response.status),
            created_at=datetime.fromtimestamp(response.created_at),
            finished_at=datetime.fromtimestamp(response.finished_at) if response.finished_at else None,
            fine_tuned_model=response.fine_tuned_model,
            hyperparameters=response.hyperparameters.model_dump() if response.hyperparameters else {},
            error=response.error.message if response.error else None,
        )
        
        self._jobs[job_id] = job
        return job
    
    async def wait_for_completion(
        self,
        job_id: str,
        poll_interval: int = 60,
        timeout: int = 3600,
    ) -> FineTuneJob:
        """Wait for a fine-tuning job to complete."""
        import asyncio
        
        start_time = time.time()
        
        while True:
            job = await self.get_job_status(job_id)
            
            if job.status in [FineTuneStatus.SUCCEEDED, FineTuneStatus.FAILED, FineTuneStatus.CANCELLED]:
                logger.info(f"Job {job_id} completed with status: {job.status}")
                return job
            
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Fine-tune job {job_id} did not complete within {timeout} seconds")
            
            await asyncio.sleep(poll_interval)
    
    async def cancel_job(self, job_id: str) -> FineTuneJob:
        """Cancel a fine-tuning job."""
        self.client.fine_tuning.jobs.cancel(job_id)
        job = await self.get_job_status(job_id)
        logger.info(f"Job {job_id} cancelled")
        return job
    
    async def list_jobs(self, limit: int = 20) -> List[FineTuneJob]:
        """List recent fine-tuning jobs."""
        response = self.client.fine_tuning.jobs.list(limit=limit)
        
        jobs = []
        for item in response.data:
            job = FineTuneJob(
                job_id=item.id,
                model=item.model,
                training_file=item.training_file,
                status=FineTuneStatus(item.status),
                created_at=datetime.fromtimestamp(item.created_at),
                finished_at=datetime.fromtimestamp(item.finished_at) if item.finished_at else None,
                fine_tuned_model=item.fine_tuned_model,
            )
            jobs.append(job)
        
        return jobs
