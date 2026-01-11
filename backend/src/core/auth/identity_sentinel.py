"""
Identity Sentinel - Advanced Auth Protection

Detects "Impossible Travel" and anomalous usage patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LoginEvent:
    ip_address: str
    timestamp: datetime
    location: str  # e.g., "US", "DE" - mocked for now or derived from IP


class IdentitySentinel:
    """
    Monitors identity usage for anomalies.

    Features:
    - Impossible Travel Detection
    - Anomalous API usage
    - Autonomous token revocation
    """

    def __init__(self):
        # In-memory store for recent logins per user.
        # In production, this should be Redis or DB.
        self.user_logins: Dict[str, List[LoginEvent]] = {}

        # Threshold for impossible travel (km/h or just distinct countries in short time)
        # For this implementation, we'll use a simple "different location within X minutes" rule.
        self.impossible_travel_window_minutes = 60

    def analyze_activity(
        self,
        user_id: str,
        ip_address: str,
        location: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Analyze user activity for anomalies.

        Args:
            user_id: The user ID.
            ip_address: The source IP.
            location: The geographic location (mocked/provided).
            timestamp: Time of activity. Defaults to now.

        Returns:
            True if activity is SAFE, False if ANOMALOUS (and token revoked).
        """
        if timestamp is None:
            timestamp = datetime.now()

        current_event = LoginEvent(ip_address, timestamp, location)

        # Check history
        history = self.user_logins.get(user_id, [])

        # Sort history by timestamp
        history.sort(key=lambda x: x.timestamp)

        # Clean up old history (older than 24h)
        cutoff = timestamp - timedelta(hours=24)
        history = [e for e in history if e.timestamp > cutoff]

        # Check against last event
        if history:
            last_event = history[-1]
            if self._is_impossible_travel(last_event, current_event):
                logger.critical(
                    f"IMPOSSIBLE TRAVEL DETECTED for user {user_id}: "
                    f"{last_event.location} -> {current_event.location} "
                    f"in {(current_event.timestamp - last_event.timestamp).total_seconds()}s"
                )
                self.revoke_token(user_id, reason="Impossible Travel Detected")
                return False

        # Append new event
        history.append(current_event)
        self.user_logins[user_id] = history
        return True

    def _is_impossible_travel(self, event1: LoginEvent, event2: LoginEvent) -> bool:
        """
        Determine if travel between two events is impossible.
        Simple logic: Different location within the window.
        """
        if event1.location == event2.location:
            return False

        time_diff = abs((event2.timestamp - event1.timestamp).total_seconds()) / 60.0

        if time_diff < self.impossible_travel_window_minutes:
            return True

        return False

    def revoke_token(self, user_id: str, reason: str):
        """
        Revoke user tokens.
        In a real system, this would call Supabase/Auth API.
        """
        logger.warning(f"REVOKING TOKENS for user {user_id}. Reason: {reason}")
        # Placeholder for actual revocation logic
        # supabase.auth.admin.sign_out(user_id)


# Global instance
identity_sentinel = IdentitySentinel()
