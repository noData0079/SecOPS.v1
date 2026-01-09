# backend/src/utils/data_loader.py

"""Centralized data loading for local configurations."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Base data directory relative to backend root
_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


def _load_json(relative_path: str) -> Dict[str, Any]:
    """Load JSON file from data directory."""
    filepath = _DATA_DIR / relative_path
    if not filepath.exists():
        logger.warning(f"Data file not found: {filepath}")
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_jsonl(relative_path: str) -> List[Dict[str, Any]]:
    """Load JSONL file from data directory."""
    filepath = _DATA_DIR / relative_path
    if not filepath.exists():
        logger.warning(f"Data file not found: {filepath}")
        return []
    results = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def get_model_config() -> Dict[str, Any]:
    """Get T79 model configuration."""
    return _load_json("models/model_config.json")


def get_keyword_config() -> Dict[str, Any]:
    """Get security keyword classification config."""
    return _load_json("models/keyword_config.json")


def get_inference_config() -> Dict[str, Any]:
    """Get inference settings."""
    return _load_json("inference/config.json")


def get_fine_tuning_data() -> List[Dict[str, Any]]:
    """Get security hardening fine-tuning prompts."""
    return _load_jsonl("fine_tune/security_hardening.jsonl")


def classify_threat(text: str) -> str:
    """
    Classify threat level based on keyword matching.
    
    Returns: 'critical', 'suspicious', or 'benign'
    """
    config = get_keyword_config()
    keywords = config.get("keywords", {})
    
    text_lower = text.lower()
    
    # Check critical first
    for keyword in keywords.get("critical", []):
        if keyword.lower() in text_lower:
            return "critical"
    
    # Check suspicious
    for keyword in keywords.get("suspicious", []):
        if keyword.lower() in text_lower:
            return "suspicious"
    
    return "benign"


def get_data_directory() -> Path:
    """Get the base data directory path."""
    return _DATA_DIR
