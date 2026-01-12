from typing import Any, List
import contextlib
from .pii_filter import PIIFilter

class MockHardwareEnclave:
    """
    Mocks the Hardware Root of Trust and Secure Enclave.
    """
    def __init__(self):
        self.is_locked = True
        self.active_sessions = 0

    @contextlib.contextmanager
    def secure_session(self):
        self.active_sessions += 1
        # In a real scenario, this would initialize encrypted memory regions
        session = SecureSession(self)
        try:
            yield session
        finally:
            self.active_sessions -= 1
            session.shred_memory()

class SecureSession:
    def __init__(self, enclave):
        self.enclave = enclave
        self.memory_buffer = []
        self.is_active = True

    def shred_memory(self):
        """
        Simulates overwriting memory with zeros.
        """
        self.memory_buffer = []
        self.is_active = False

class SovereignGate:
    def __init__(self, hardware_enclave=None):
        self.enclave = hardware_enclave if hardware_enclave else MockHardwareEnclave()
        self.hard_rules = ["NO_LOG", "NO_TRAIN", "NO_EGRESS"]
        self.pii_filter = PIIFilter()

    def process_sensitive_query(self, client_data: str, ai_model: Any) -> Any:
        """
        Processes data inside a 'Black Box' where
        learning is physically disabled.
        """
        with self.enclave.secure_session() as session:
            # 1. Strip all PII (Personal Identifiable Information)
            clean_context = self.scrub_pii(client_data)

            # Store in secure session (simulated)
            session.memory_buffer.append(clean_context)

            # 2. Set AI to 'Ephemeral Mode' (Zero-Memory)
            # This forces the LLM to use 0-shot logic without logging
            # Check if ai_model has a generate method, otherwise mock it
            if hasattr(ai_model, 'generate'):
                response = ai_model.generate(clean_context, temperature=0, store_context=False)
            else:
                # Mock response if ai_model is just a mock object or function
                response = f"Processed: {clean_context[:20]}..."

            # 3. Shred the session memory immediately after response
            # (Handled by context manager's finally block, but called here to be explicit as per spec)
            session.shred_memory()

            return response

    def scrub_pii(self, data: str) -> str:
        # Automated masking of Names, IPs, and Secrets before the AI sees them
        return self.pii_filter.mask(data)
