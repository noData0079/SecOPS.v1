from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class CodeIssue:
    """Lightweight representation of a code smell or TODO."""

    path: str
    line: int
    message: str


class CodeTargetClient:
    """
    Minimal codebase client that can surface quick signals from a repository.

    The client is intentionally lightweight: it walks the repository root and
    emits a handful of heuristics (TODO/FIXME counts, size metrics) that can be
    consumed by higher-level orchestrators.
    """

    def __init__(self, repo_path: Optional[str] = None) -> None:
        self.repo_path = repo_path or os.getcwd()

    def _safe_list_files(self) -> List[str]:
        """Return a flat list of files under repo_path, ignoring virtualenvs."""

        files: List[str] = []
        for root, _, filenames in os.walk(self.repo_path):
            if any(part.startswith(".") for part in root.split(os.sep)):
                # Skip dot-directories such as .git to keep things fast.
                continue
            for name in filenames:
                files.append(os.path.join(root, name))
        return files

    def summarize(self) -> Dict[str, object]:
        """
        Collect a handful of codebase signals.

        - Total file count and approximate size.
        - Naive TODO/FIXME counter for prioritization hints.
        """

        files = self._safe_list_files()
        todo_hits = 0
        for path in files:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if "TODO" in line or "FIXME" in line:
                            todo_hits += 1
            except (OSError, UnicodeDecodeError):
                continue

        total_bytes = 0
        for path in files:
            try:
                total_bytes += os.path.getsize(path)
            except OSError:
                continue

        return {
            "repo_path": self.repo_path,
            "file_count": len(files),
            "approx_size_bytes": total_bytes,
            "todo_mentions": todo_hits,
        }

    def collect_issues(self) -> List[CodeIssue]:
        """Gather simple inline issues to feed into RAG summaries."""

        issues: List[CodeIssue] = []
        for path in self._safe_list_files():
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        if "TODO" in line or "FIXME" in line:
                            issues.append(CodeIssue(path=path, line=idx, message=line.strip()))
            except (OSError, UnicodeDecodeError):
                continue
        return issues
