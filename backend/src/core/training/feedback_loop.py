"""
Feedback Loop - Collects and processes human feedback for model fine-tuning.

This module implements "Feedback Distillation":
1. Collects "Thumbs Up/Down" feedback from users via API.
2. Retrieves the corresponding incident context from EpisodicStore.
3. Formats high-quality (positive) feedback into training examples.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from src.core.memory.episodic_store import EpisodicStore

logger = logging.getLogger(__name__)

@dataclass
class FeedbackEntry:
    incident_id: str
    rating: int  # 1 for Thumbs Up, -1 for Thumbs Down
    comment: Optional[str] = None
    timestamp: str = ""

class FeedbackCollector:
    def __init__(self, feedback_dir: Optional[Path] = None):
        self.feedback_dir = feedback_dir or Path("backend/data/feedback")
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.feedback_dir / "feedback.jsonl"
        self.episodic_store = EpisodicStore()

    def collect_feedback(self, incident_id: str, rating: int, comment: Optional[str] = None) -> bool:
        """
        Log user feedback for a specific incident.
        """
        entry = FeedbackEntry(
            incident_id=incident_id,
            rating=rating,
            comment=comment,
            timestamp=datetime.now().isoformat()
        )

        try:
            with open(self.feedback_file, "a") as f:
                f.write(json.dumps(asdict(entry)) + "\n")
            logger.info(f"Recorded feedback for incident {incident_id}: rating={rating}")
            return True
        except Exception as e:
            logger.error(f"Failed to record feedback: {e}")
            return False

    def get_training_examples(self) -> List[Dict[str, Any]]:
        """
        Retrieve high-quality training examples based on positive feedback.

        Returns:
            List of Dicts with keys: "instruction", "output" (and optionally "input")
        """
        if not self.feedback_file.exists():
            return []

        training_data = []
        processed_incidents = set()

        # Read feedback file (reverse order to get latest feedback first?)
        # For now, just read all and filter for positive.
        try:
            with open(self.feedback_file, "r") as f:
                lines = f.readlines()
        except Exception as e:
            logger.error(f"Failed to read feedback file: {e}")
            return []

        for line in lines:
            try:
                data = json.loads(line)
                entry = FeedbackEntry(**data)

                # Only process positive feedback
                if entry.rating > 0 and entry.incident_id not in processed_incidents:
                    example = self._create_example_from_incident(entry.incident_id)
                    if example:
                        training_data.append(example)
                        processed_incidents.add(entry.incident_id)
            except Exception as e:
                logger.warning(f"Skipping malformed feedback line: {e}")
                continue

        logger.info(f"Retrieved {len(training_data)} training examples from human feedback.")
        return training_data

    def _create_example_from_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch incident from EpisodicStore and format as a training example.
        """
        incident = self.episodic_store.get_incident(incident_id)
        if not incident:
            logger.warning(f"Incident {incident_id} not found in EpisodicStore.")
            return None

        # We need to construct a training example.
        # Ideally: Instruction = Observation, Output = Action/Reasoning.
        # An incident might have multiple episodes. We should look for the *successful* ones.
        # Or if the feedback is for the whole incident, we might want the *final* successful action.

        examples = []
        for episode in incident.episodes:
            # We assume if the user gave a thumbs up, the actions taken were generally good,
            # especially if the episode led to a success.
            # However, usually thumbs up is for the *resolution*.

            if episode.action_taken and episode.outcome and episode.outcome.get("success"):
                # Construct the prompt as the model would see it
                # Note: This is a simplified reconstruction. Ideally we'd have the exact prompt stored.
                # But we have 'observation' and 'action'.

                instruction = f"""SYSTEM:
You are an autonomous infrastructure agent.
Your job: Choose the next action. Nothing else.

INPUT:
{episode.observation}

SOURCE: logs (inferred)

TOOLS AVAILABLE:
(All Tools)
"""
                # Reconstruct the output
                output_json = {
                    "reasoning": "Feedback-verified action.", # We might miss the original reasoning if not stored in episode
                    "confidence": 100,
                    "tool": episode.action_taken.get("tool"),
                    "args": episode.action_taken.get("args", {})
                }

                # If we have the original reasoning (stored in action or separate), use it.
                # EpisodeSnapshot has 'action_taken' which is the model response dict usually.
                if "reasoning" in episode.action_taken:
                    output_json["reasoning"] = episode.action_taken["reasoning"]

                examples.append({
                    "instruction": instruction,
                    "output": json.dumps(output_json, indent=2),
                    "source": "human_feedback"
                })

        # Return the last successful one, or all?
        # Let's return the last successful one as it's likely the solution.
        if examples:
            return examples[-1]

        return None

# Global instance
_feedback_collector = None

def get_feedback_collector():
    global _feedback_collector
    if _feedback_collector is None:
        _feedback_collector = FeedbackCollector()
    return _feedback_collector
