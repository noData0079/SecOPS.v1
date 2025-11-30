# backend/src/core/scheduler/jobs.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import List, Optional


@dataclass(frozen=True)
class ScheduledJob:
    """
    Declarative description of a scheduled check run.

    This is intentionally simple and framework-agnostic. A worker process
    (e.g. a cron-triggered script, APScheduler, or a cloud scheduler) can
    import this list and decide when to call CheckScheduler.enqueue_run.

    Fields:
    - id: stable identifier for the job
    - description: human-readable description
    - scope: logical scope to run (security, reliability, all, etc.)
    - checks: optional explicit list of check ids to run
    - run_at_utc: optional time-of-day in UTC when this job should run
    - interval_hours: optional fixed interval in hours between runs
    - enabled: if False, job should be ignored by workers
    """

    id: str
    description: str

    # Either scope OR explicit checks (or both)
    scope: Optional[str] = None
    checks: Optional[List[str]] = None

    # Scheduling hints (one or both may be used by a worker)
    run_at_utc: Optional[time] = None
    interval_hours: Optional[int] = None

    # Toggle job on/off without code changes in workers
    enabled: bool = True


# ---------------------------------------------------------------------------
# Default job definitions
# ---------------------------------------------------------------------------

DEFAULT_JOBS: List[ScheduledJob] = [
    ScheduledJob(
        id="nightly_security",
        description="Run all security-focused checks once per night.",
        scope="security",
        checks=None,  # let scheduler pick all security checks
        run_at_utc=time(hour=1, minute=0),  # 01:00 UTC
        interval_hours=None,
        enabled=True,
    ),
    ScheduledJob(
        id="twice_daily_reliability",
        description="Run reliability / k8s health checks twice a day.",
        scope="reliability",
        checks=["k8s_misconfig"],
        run_at_utc=None,
        interval_hours=12,
        enabled=True,
    ),
    ScheduledJob(
        id="daily_full_health",
        description="Run all checks once per day for a full health sweep.",
        scope="all",
        checks=None,
        run_at_utc=time(hour=3, minute=0),  # 03:00 UTC
        interval_hours=None,
        enabled=True,
    ),
]


# ---------------------------------------------------------------------------
# Helper functions for workers
# ---------------------------------------------------------------------------


def get_enabled_jobs() -> List[ScheduledJob]:
    """
    Return all jobs that are currently enabled.
    """
    return [job for job in DEFAULT_JOBS if job.enabled]


def get_job_by_id(job_id: str) -> Optional[ScheduledJob]:
    """
    Look up a single job by id.
    """
    for job in DEFAULT_JOBS:
        if job.id == job_id:
            return job
    return None
