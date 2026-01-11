"""
Episodic Memory - Store complete incident snapshots.

This is NOT logs. This is structured, queryable memory of:
- Full incident state
- Actions taken
- Outcomes achieved
- Context at decision time
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class EpisodeSnapshot:
    """Complete snapshot of an incident episode."""
    episode_id: str
    incident_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # State at this point
    observation: str = ""
    system_state: Dict[str, Any] = field(default_factory=dict)
    
    # Decision made
    action_taken: Optional[Dict[str, Any]] = None
    policy_decision: str = ""  # ALLOW, BLOCK, ESCALATE
    confidence: float = 0.0
    
    # Outcome (if action was taken)
    outcome: Optional[Dict[str, Any]] = None
    
    # Context
    prior_episodes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EpisodeSnapshot":
        d["timestamp"] = datetime.fromisoformat(d["timestamp"])
        return cls(**d)


@dataclass
class IncidentMemory:
    """Complete memory of an incident."""
    incident_id: str
    started_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    
    episodes: List[EpisodeSnapshot] = field(default_factory=list)
    final_outcome: str = ""  # resolved, escalated, failed
    resolution_time_seconds: int = 0
    
    # Summary (computed)
    actions_taken: int = 0
    successful_actions: int = 0
    
    def add_episode(self, episode: EpisodeSnapshot):
        self.episodes.append(episode)
        self.actions_taken += 1 if episode.action_taken else 0
        if episode.outcome and episode.outcome.get("success"):
            self.successful_actions += 1
    
    def close(self, outcome: str):
        self.resolved_at = datetime.now()
        self.final_outcome = outcome
        if self.resolved_at and self.started_at:
            self.resolution_time_seconds = int(
                (self.resolved_at - self.started_at).total_seconds()
            )


class EpisodicStore:
    """
    Persistent episodic memory store.
    
    Stores complete incident histories for:
    - Pattern recognition
    - Learning from past
    - Audit trails
    - Replay analysis
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./data/episodic_memory")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache of recent incidents
        self.cache: Dict[str, IncidentMemory] = {}
        self.cache_limit = 100
    
    def start_incident(self, incident_id: str) -> IncidentMemory:
        """Start tracking a new incident."""
        memory = IncidentMemory(incident_id=incident_id)
        self.cache[incident_id] = memory
        logger.info(f"Started episodic memory for incident: {incident_id}")
        return memory
    
    def record_episode(
        self,
        incident_id: str,
        observation: str,
        system_state: Dict[str, Any],
        action: Optional[Dict[str, Any]] = None,
        policy_decision: str = "",
        confidence: float = 0.0,
        outcome: Optional[Dict[str, Any]] = None,
    ) -> EpisodeSnapshot:
        """Record an episode in the incident memory."""
        if incident_id not in self.cache:
            self.start_incident(incident_id)
        
        memory = self.cache[incident_id]
        
        episode = EpisodeSnapshot(
            episode_id=f"{incident_id}_{len(memory.episodes):03d}",
            incident_id=incident_id,
            observation=observation,
            system_state=system_state,
            action_taken=action,
            policy_decision=policy_decision,
            confidence=confidence,
            outcome=outcome,
            prior_episodes=[e.episode_id for e in memory.episodes[-3:]],
        )
        
        memory.add_episode(episode)
        
        return episode
    
    def close_incident(self, incident_id: str, outcome: str) -> Optional[IncidentMemory]:
        """Close an incident and persist to storage."""
        if incident_id not in self.cache:
            return None
        
        memory = self.cache[incident_id]
        memory.close(outcome)
        
        # Persist
        self._persist(memory)
        
        # Evict from cache if over limit
        if len(self.cache) > self.cache_limit:
            oldest = min(
                self.cache.values(),
                key=lambda m: m.started_at
            )
            del self.cache[oldest.incident_id]
        
        logger.info(
            f"Closed incident {incident_id}: {outcome}, "
            f"{memory.actions_taken} actions, {memory.resolution_time_seconds}s"
        )
        
        return memory
    
    def get_incident(self, incident_id: str) -> Optional[IncidentMemory]:
        """Get incident memory from cache or storage."""
        if incident_id in self.cache:
            return self.cache[incident_id]
        
        # Try loading from disk
        return self._load(incident_id)
    
    def find_similar(
        self,
        observation: str,
        limit: int = 5,
    ) -> List[IncidentMemory]:
        """Find similar past incidents based on observation."""
        # Simple keyword matching (use vector search in production)
        obs_words = set(observation.lower().split())
        
        scored: List[tuple] = []
        
        for filepath in self.storage_path.glob("*.json"):
            try:
                memory = self._load_file(filepath)
                if not memory or not memory.episodes:
                    continue
                
                # Score based on observation overlap
                memory_words: set = set()
                for ep in memory.episodes:
                    memory_words.update(ep.observation.lower().split())
                
                overlap = len(obs_words & memory_words)
                if overlap > 0:
                    scored.append((overlap, memory))
            except Exception as e:
                logger.warning(f"Failed to load {filepath}: {e}")
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:limit]]
    
    def get_success_patterns(self) -> Dict[str, Any]:
        """Analyze successful incident resolutions."""
        success_count = 0
        total_time = 0
        action_counts: Dict[str, int] = {}
        
        for filepath in self.storage_path.glob("*.json"):
            try:
                memory = self._load_file(filepath)
                if not memory:
                    continue
                
                if memory.final_outcome == "resolved":
                    success_count += 1
                    total_time += memory.resolution_time_seconds
                    
                    for ep in memory.episodes:
                        if ep.action_taken:
                            tool = ep.action_taken.get("tool", "unknown")
                            action_counts[tool] = action_counts.get(tool, 0) + 1
            except Exception:
                pass
        
        return {
            "success_count": success_count,
            "avg_resolution_time": total_time / max(1, success_count),
            "most_used_tools": sorted(
                action_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
        }
    
    def _persist(self, memory: IncidentMemory):
        """Persist incident memory to disk."""
        filename = f"{memory.incident_id}.json"
        filepath = self.storage_path / filename
        
        data = {
            "incident_id": memory.incident_id,
            "started_at": memory.started_at.isoformat(),
            "resolved_at": memory.resolved_at.isoformat() if memory.resolved_at else None,
            "final_outcome": memory.final_outcome,
            "resolution_time_seconds": memory.resolution_time_seconds,
            "actions_taken": memory.actions_taken,
            "successful_actions": memory.successful_actions,
            "episodes": [ep.to_dict() for ep in memory.episodes],
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def _load(self, incident_id: str) -> Optional[IncidentMemory]:
        """Load incident memory from disk."""
        filepath = self.storage_path / f"{incident_id}.json"
        return self._load_file(filepath)
    
    def _load_file(self, filepath: Path) -> Optional[IncidentMemory]:
        """Load incident memory from file."""
        if not filepath.exists():
            return None
        
        try:
            with open(filepath) as f:
                data = json.load(f)
            
            memory = IncidentMemory(
                incident_id=data["incident_id"],
                started_at=datetime.fromisoformat(data["started_at"]),
                resolved_at=datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None,
                final_outcome=data.get("final_outcome", ""),
                resolution_time_seconds=data.get("resolution_time_seconds", 0),
                actions_taken=data.get("actions_taken", 0),
                successful_actions=data.get("successful_actions", 0),
                episodes=[EpisodeSnapshot.from_dict(ep) for ep in data.get("episodes", [])],
            )
            return memory
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            return None


__all__ = [
    "EpisodicStore",
    "EpisodeSnapshot",
    "IncidentMemory",
]
