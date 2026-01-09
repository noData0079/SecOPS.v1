# backend/src/core/agentic/code_context_engine.py

"""
Code Context Engine - Layer 6

Grounds fixes in reality:
- Repo graph
- Dependency mapping  
- Ownership resolution
- Change impact analysis

Prevents hallucinated code.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class CodeFile:
    """Representation of a code file."""
    path: str
    language: str
    size_bytes: int
    last_modified: datetime
    owner: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "language": self.language,
            "size_bytes": self.size_bytes,
            "last_modified": self.last_modified.isoformat(),
            "owner": self.owner,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
        }


@dataclass
class ImpactAnalysis:
    """Analysis of change impact."""
    
    id: str
    target_file: str
    direct_impacts: List[str]  # Files directly affected
    transitive_impacts: List[str]  # Files indirectly affected
    blast_radius: int  # Total number of affected files
    risk_score: float  # 0.0 to 1.0
    owners_affected: List[str]
    test_coverage: float
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "target_file": self.target_file,
            "direct_impacts": self.direct_impacts,
            "transitive_impacts": self.transitive_impacts,
            "blast_radius": self.blast_radius,
            "risk_score": self.risk_score,
            "owners_affected": self.owners_affected,
            "test_coverage": self.test_coverage,
            "created_at": self.created_at.isoformat(),
        }


class CodeContextEngine:
    """
    Provides code context for grounding fixes.
    
    Key responsibilities:
    - Map repository structure
    - Track dependencies
    - Analyze change impact
    - Prevent hallucinations
    """
    
    def __init__(self):
        self._files: Dict[str, CodeFile] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._reverse_graph: Dict[str, Set[str]] = {}
        self._owners: Dict[str, str] = {}
        logger.info("CodeContextEngine initialized")
    
    async def index_repository(
        self,
        repo_path: str,
        include_patterns: Optional[List[str]] = None,
    ) -> int:
        """
        Index a repository's files and dependencies.
        
        Returns: Number of files indexed
        """
        include = include_patterns or ["*.py", "*.js", "*.ts", "*.go", "*.yaml", "*.yml"]
        count = 0
        
        repo = Path(repo_path)
        if not repo.exists():
            logger.warning(f"Repository not found: {repo_path}")
            return 0
        
        for pattern in include:
            for file_path in repo.rglob(pattern):
                if ".git" in str(file_path):
                    continue
                
                try:
                    stat = file_path.stat()
                    rel_path = str(file_path.relative_to(repo))
                    
                    code_file = CodeFile(
                        path=rel_path,
                        language=self._detect_language(file_path.suffix),
                        size_bytes=stat.st_size,
                        last_modified=datetime.fromtimestamp(stat.st_mtime),
                    )
                    
                    self._files[rel_path] = code_file
                    count += 1
                    
                except Exception as e:
                    logger.debug(f"Error indexing {file_path}: {e}")
        
        logger.info(f"Indexed {count} files from {repo_path}")
        return count
    
    def _detect_language(self, suffix: str) -> str:
        """Detect language from file suffix."""
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".md": "markdown",
            ".sh": "shell",
            ".dockerfile": "dockerfile",
        }
        return mapping.get(suffix.lower(), "unknown")
    
    async def add_dependency(
        self,
        source: str,
        target: str,
    ) -> None:
        """Add a dependency relationship."""
        if source not in self._dependency_graph:
            self._dependency_graph[source] = set()
        self._dependency_graph[source].add(target)
        
        if target not in self._reverse_graph:
            self._reverse_graph[target] = set()
        self._reverse_graph[target].add(source)
        
        # Update CodeFile objects
        if source in self._files:
            if target not in self._files[source].dependencies:
                self._files[source].dependencies.append(target)
        if target in self._files:
            if source not in self._files[target].dependents:
                self._files[target].dependents.append(source)
    
    async def get_dependencies(self, file_path: str) -> List[str]:
        """Get direct dependencies of a file."""
        return list(self._dependency_graph.get(file_path, set()))
    
    async def get_dependents(self, file_path: str) -> List[str]:
        """Get files that depend on this file."""
        return list(self._reverse_graph.get(file_path, set()))
    
    async def get_transitive_dependents(
        self,
        file_path: str,
        max_depth: int = 5,
    ) -> List[str]:
        """Get all transitive dependents (files affected by changes)."""
        visited = set()
        to_visit = [file_path]
        depth = 0
        
        while to_visit and depth < max_depth:
            current = to_visit.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            dependents = await self.get_dependents(current)
            to_visit.extend(dependents)
            depth += 1
        
        visited.discard(file_path)  # Don't include the source file
        return list(visited)
    
    async def analyze_impact(
        self,
        file_path: str,
    ) -> ImpactAnalysis:
        """
        Analyze the impact of changing a file.
        
        This grounds fixes in reality - prevents blind changes.
        """
        direct = await self.get_dependents(file_path)
        transitive = await self.get_transitive_dependents(file_path)
        
        # Remove direct from transitive
        transitive = [t for t in transitive if t not in direct]
        
        blast_radius = len(direct) + len(transitive)
        
        # Calculate risk score
        risk_score = min(1.0, blast_radius * 0.1)
        if blast_radius > 10:
            risk_score = min(1.0, risk_score + 0.3)
        
        # Find affected owners
        affected_owners = set()
        for f in [file_path] + direct + transitive:
            if f in self._owners:
                affected_owners.add(self._owners[f])
        
        return ImpactAnalysis(
            id=str(uuid4()),
            target_file=file_path,
            direct_impacts=direct,
            transitive_impacts=transitive,
            blast_radius=blast_radius,
            risk_score=risk_score,
            owners_affected=list(affected_owners),
            test_coverage=0.0,  # Would integrate with test coverage tools
            created_at=datetime.utcnow(),
        )
    
    async def set_owner(self, file_pattern: str, owner: str) -> None:
        """Set ownership for files matching pattern."""
        for path in self._files:
            if file_pattern in path:
                self._owners[path] = owner
                self._files[path].owner = owner
    
    async def get_context_for_fix(
        self,
        file_path: str,
        finding_id: str,
    ) -> Dict[str, Any]:
        """
        Get full context needed for generating a fix.
        
        Includes:
        - File content (if small enough)
        - Dependencies
        - Impact analysis
        - Related files
        """
        impact = await self.analyze_impact(file_path)
        
        context = {
            "file_path": file_path,
            "finding_id": finding_id,
            "file_info": self._files.get(file_path, {}).to_dict() if file_path in self._files else {},
            "impact": impact.to_dict(),
            "dependencies": await self.get_dependencies(file_path),
            "dependents": impact.direct_impacts,
        }
        
        return context
    
    def get_file_count(self) -> int:
        """Get number of indexed files."""
        return len(self._files)
