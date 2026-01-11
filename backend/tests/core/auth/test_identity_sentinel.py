import pytest
from datetime import datetime, timedelta
from src.core.auth.identity_sentinel import IdentitySentinel, LoginEvent

def test_identity_sentinel_normal_activity():
    sentinel = IdentitySentinel()
    user_id = "user123"

    # Login 1
    assert sentinel.analyze_activity(user_id, "192.168.1.1", "US") is True

    # Login 2: Same location, 5 mins later
    assert sentinel.analyze_activity(
        user_id,
        "192.168.1.1",
        "US",
        timestamp=datetime.now() + timedelta(minutes=5)
    ) is True

def test_identity_sentinel_impossible_travel():
    sentinel = IdentitySentinel()
    user_id = "user_traveler"

    now = datetime.now()

    # Login 1: US
    sentinel.analyze_activity(user_id, "1.1.1.1", "US", timestamp=now)

    # Login 2: DE (Germany) 10 mins later -> Impossible
    is_safe = sentinel.analyze_activity(
        user_id,
        "2.2.2.2",
        "DE",
        timestamp=now + timedelta(minutes=10)
    )

    assert is_safe is False

def test_identity_sentinel_possible_travel():
    sentinel = IdentitySentinel()
    user_id = "user_slow_traveler"

    now = datetime.now()

    # Login 1: US
    sentinel.analyze_activity(user_id, "1.1.1.1", "US", timestamp=now)

    # Login 2: DE (Germany) 5 hours later -> Possible (if we assume > 60 min is ok for test simplicity)
    # The sentinel uses `impossible_travel_window_minutes = 60`

    is_safe = sentinel.analyze_activity(
        user_id,
        "2.2.2.2",
        "DE",
        timestamp=now + timedelta(hours=5)
    )

    assert is_safe is True
