from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TableSummary:
    name: str
    columns: int
    notes: str


class DatabaseTargetClient:
    """
    Lightweight database target client.

    The client does not establish real network connections; instead it accepts
    declarative metadata about the target database to keep the orchestrator's
    contract simple and testable.
    """

    def __init__(self, connection_string: Optional[str] = None) -> None:
        self.connection_string = connection_string or ""

    def summarize(self, schema_metadata: Optional[dict] = None) -> Dict[str, object]:
        """
        Summarize a target database using provided metadata.

        If schema_metadata is provided, it should look like:
        {"tables": [{"name": "users", "columns": 5}, ...]}
        """

        tables_raw = schema_metadata.get("tables") if schema_metadata else []
        tables = [
            TableSummary(
                name=str(t.get("name", "unknown")),
                columns=int(t.get("columns", 0)),
                notes=t.get("notes", ""),
            )
            for t in tables_raw
        ]

        return {
            "connection": self.connection_string,
            "tables": [t.__dict__ for t in tables],
            "raw": json.dumps(schema_metadata or {}),
        }
