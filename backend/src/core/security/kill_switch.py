from threading import Lock

class KillSwitchService:
    """
    Singleton service to manage the global safety kill switch.
    In a clustered environment, this state would be backed by Redis.
    For this MVP/Single-Instance deployment, in-memory is sufficient.
    """
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(KillSwitchService, cls).__new__(cls)
                    cls._instance._active = False
        return cls._instance

    def activate(self):
        """Immediately enable the kill switch, halting all non-admin traffic."""
        self._active = True

    def deactivate(self):
        """Disable the kill switch, restoring normal operations."""
        self._active = False

    def is_active(self) -> bool:
        """Check if the kill switch is currently active."""
        return self._active

# Global instance
kill_switch = KillSwitchService()
