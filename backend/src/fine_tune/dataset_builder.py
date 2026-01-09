# backend/src/fine_tune/dataset_builder.py

"""Dataset builder for OpenAI fine-tuning with JSONL output and validation."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

logger = logging.getLogger(__name__)


def _normalize_prompt(content: str) -> str:
    """Legacy prompt normalization for backward compatibility."""
    prefix = (
        "You are T79 AI, a security automation assistant. "
        "Summarize the issue, cite risky elements, and propose a precise mitigation."
    )
    return f"{prefix}\n\n<observation>\n{content.strip()}\n</observation>\n\n### Response:"


@dataclass
class ConversationMessage:
    """A single message in a conversation."""
    role: str  # "system", "user", or "assistant"
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class TrainingExample:
    """A single training example for fine-tuning."""
    messages: List[ConversationMessage]
    
    def to_dict(self) -> Dict[str, Any]:
        return {"messages": [m.to_dict() for m in self.messages]}
    
    def to_jsonl(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class DatasetStats:
    """Statistics about a dataset."""
    total_examples: int = 0
    total_tokens_estimate: int = 0
    avg_messages_per_example: float = 0.0
    validation_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_examples": self.total_examples,
            "total_tokens_estimate": self.total_tokens_estimate,
            "avg_messages_per_example": self.avg_messages_per_example,
            "validation_errors": self.validation_errors,
            "is_valid": len(self.validation_errors) == 0,
        }


class DatasetBuilder:
    """
    Build and validate datasets for OpenAI fine-tuning.
    
    Supports:
    - Building datasets from various input formats
    - JSONL output compatible with OpenAI fine-tuning
    - Dataset validation
    - Token estimation
    - Train/validation split
    """
    
    MIN_EXAMPLES = 10  # OpenAI minimum
    RECOMMENDED_EXAMPLES = 50  # Recommended for good results
    
    def __init__(self, system_prompt: Optional[str] = None):
        """Initialize dataset builder."""
        self.system_prompt = system_prompt
        self.examples: List[TrainingExample] = []
        logger.info("DatasetBuilder initialized")
    
    def add_example(
        self,
        user_message: str,
        assistant_response: str,
        system_prompt: Optional[str] = None,
    ) -> None:
        """Add a single training example."""
        messages = []
        
        sys_prompt = system_prompt or self.system_prompt
        if sys_prompt:
            messages.append(ConversationMessage(role="system", content=sys_prompt))
        
        messages.append(ConversationMessage(role="user", content=user_message))
        messages.append(ConversationMessage(role="assistant", content=assistant_response))
        
        self.examples.append(TrainingExample(messages=messages))
    
    def add_conversation(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> None:
        """Add a multi-turn conversation as a training example."""
        conversation = []
        
        sys_prompt = system_prompt or self.system_prompt
        if sys_prompt and (not messages or messages[0].get("role") != "system"):
            conversation.append(ConversationMessage(role="system", content=sys_prompt))
        
        for msg in messages:
            conversation.append(ConversationMessage(
                role=msg["role"],
                content=msg["content"]
            ))
        
        self.examples.append(TrainingExample(messages=conversation))
    
    def build_from_qa_pairs(
        self,
        qa_pairs: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> int:
        """Build dataset from question-answer pairs."""
        count = 0
        for pair in qa_pairs:
            self.add_example(
                user_message=pair["question"],
                assistant_response=pair["answer"],
                system_prompt=system_prompt,
            )
            count += 1
        
        logger.info(f"Added {count} examples from Q&A pairs")
        return count
    
    def build_from_files(
        self,
        files: Iterable[str],
        prompt_template: str = "Analyze the following content:\n\n{content}",
        response_generator: Optional[callable] = None,
    ) -> int:
        """Build dataset from files with a prompt template."""
        count = 0
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                user_message = prompt_template.format(content=content[:4000])
                
                if response_generator:
                    assistant_response = response_generator(content)
                else:
                    assistant_response = f"I've analyzed the content from {Path(file_path).name}."
                
                self.add_example(user_message, assistant_response)
                count += 1
                
            except Exception as e:
                logger.warning(f"Failed to process file {file_path}: {e}")
        
        logger.info(f"Added {count} examples from files")
        return count
    
    def validate(self) -> DatasetStats:
        """Validate the dataset."""
        stats = DatasetStats()
        stats.total_examples = len(self.examples)
        
        if stats.total_examples < self.MIN_EXAMPLES:
            stats.validation_errors.append(
                f"Dataset has {stats.total_examples} examples, minimum is {self.MIN_EXAMPLES}"
            )
        
        total_messages = 0
        for i, example in enumerate(self.examples):
            total_messages += len(example.messages)
            
            if len(example.messages) < 2:
                stats.validation_errors.append(f"Example {i} has fewer than 2 messages")
            
            roles = [m.role for m in example.messages]
            if "assistant" not in roles:
                stats.validation_errors.append(f"Example {i} missing assistant message")
            
            for msg in example.messages:
                stats.total_tokens_estimate += len(msg.content) // 4
        
        if stats.total_examples > 0:
            stats.avg_messages_per_example = total_messages / stats.total_examples
        
        return stats
    
    def to_jsonl(self, output_path: Optional[str] = None) -> str:
        """Convert dataset to JSONL format."""
        lines = [example.to_jsonl() for example in self.examples]
        jsonl_content = "\n".join(lines)
        
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(jsonl_content)
            logger.info(f"Dataset written to {output_path}")
        
        return jsonl_content
    
    def split(self, validation_ratio: float = 0.2) -> tuple['DatasetBuilder', 'DatasetBuilder']:
        """Split dataset into training and validation sets."""
        import random
        
        examples = self.examples.copy()
        random.shuffle(examples)
        
        split_idx = int(len(examples) * (1 - validation_ratio))
        
        train_builder = DatasetBuilder(system_prompt=self.system_prompt)
        train_builder.examples = examples[:split_idx]
        
        val_builder = DatasetBuilder(system_prompt=self.system_prompt)
        val_builder.examples = examples[split_idx:]
        
        return train_builder, val_builder
    
    def save(
        self,
        output_dir: str,
        train_file: str = "train.jsonl",
        validation_file: Optional[str] = "validation.jsonl",
        validation_ratio: float = 0.2,
    ) -> Dict[str, str]:
        """Save dataset to files with optional train/validation split."""
        os.makedirs(output_dir, exist_ok=True)
        result = {}
        
        if validation_file and validation_ratio > 0:
            train_builder, val_builder = self.split(validation_ratio)
            
            train_path = os.path.join(output_dir, train_file)
            train_builder.to_jsonl(train_path)
            result["train"] = train_path
            
            val_path = os.path.join(output_dir, validation_file)
            val_builder.to_jsonl(val_path)
            result["validation"] = val_path
        else:
            train_path = os.path.join(output_dir, train_file)
            self.to_jsonl(train_path)
            result["train"] = train_path
        
        return result


def build_dataset(files: Iterable[str], *, tags: Sequence[str] | None = None) -> List[dict]:
    """
    Legacy function for backward compatibility.
    
    Convert raw text files into a JSONL-ready list of prompt/completion pairs.
    """
    dataset: List[dict] = []
    for file_path in files:
        path = Path(file_path)
        try:
            with path.open("r", encoding="utf-8") as file:
                content = file.read()

            entry = {
                "prompt": _normalize_prompt(content),
                "completion": "Provide a concise remediation plan grounded in the observation.",
                "meta": {
                    "source": path.name,
                    "tags": list(tags) if tags else [],
                },
            }
            dataset.append(entry)
        except Exception as e:
            logger.warning(f"Failed to process {file_path}: {e}")

    return dataset
