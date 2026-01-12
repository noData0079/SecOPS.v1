import pytest
from backend.src.core.vault.sovereign_gate import SovereignGate, MockHardwareEnclave
from backend.src.core.vault.pii_filter import PIIFilter
from backend.src.core.audit.zkp_generator import ZKPGenerator

class MockAIModel:
    def generate(self, context, temperature=0, store_context=False):
        assert temperature == 0
        assert store_context is False
        return f"AI Response to: {context}"

def test_pii_filter():
    pii_filter = PIIFilter()
    text = "Contact me at user@example.com or 192.168.1.1."
    masked = pii_filter.mask(text)
    assert "<EMAIL_REDACTED>" in masked
    assert "<IP_REDACTED>" in masked
    assert "user@example.com" not in masked
    assert "192.168.1.1" not in masked

def test_sovereign_gate_process():
    gate = SovereignGate()
    ai_model = MockAIModel()
    client_data = "My secret IP is 10.0.0.1"

    response = gate.process_sensitive_query(client_data, ai_model)

    assert "AI Response to:" in response
    assert "<IP_REDACTED>" in response
    assert "10.0.0.1" not in response

def test_zkp_generator():
    zkp = ZKPGenerator()
    proof = zkp.generate_proof("sensitive data", "block_ip")

    assert proof["status"] == "VERIFIED"
    assert proof["verifier_attestation"] == "HARDWARE_ENCLAVE_SIGNED"
    assert "proof_signature" in proof
    assert proof["action"] == "block_ip"
