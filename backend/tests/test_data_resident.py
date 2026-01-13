"""
Test script for data-resident architecture components.
"""
import pytest
from core.sanitization import DataSanitizer, ReasoningBundleBuilder
from core.trust_ledger import TrustLedger, EntryType
from core.execution import LocalExecutionEngine, ApprovalGate, RiskBasedPolicy
from core.data_resident import DataResidentOrchestrator, Finding

def test_data_sanitization():
    print("\n1. Testing Data Sanitization...")
    sanitizer = DataSanitizer()

    # Test API key detection
    test_text = "API key: sk-12345678901234567890 and password: MyS3cretPass!"
    result = sanitizer.sanitize(test_text)

    # Assertions
    assert "sk-" not in result.sanitized_text
    assert "MyS3cretPass!" not in result.sanitized_text
    assert len(result.redactions) > 0

def test_reasoning_bundle_builder():
    print("\n2. Testing Reasoning Bundle Builder...")
    builder = ReasoningBundleBuilder()
    bundle = builder.build_from_finding(
        finding_id='F-001',
        finding_type='SQL_INJECTION',
        severity='HIGH',
        affected_file='db/query.ts',
        patterns=['string_interpolation'],
        policies=['PCI-6.5']
    )

    # Assertions
    assert bundle.finding_id == 'F-001'
    assert bundle.finding_type == 'SQL_INJECTION'
    assert bundle.affected_component is not None

def test_trust_ledger():
    print("\n3. Testing Trust Ledger...")
    ledger = TrustLedger(name='test')
    entry = ledger.log_finding(
        finding_id='F-001',
        finding_type='SQL_INJECTION',
        severity='HIGH',
        resource='db/query.ts'
    )

    # Assertions
    assert entry.entry_type.value is not None
    assert len(entry.hash) > 0
    assert ledger.verify_chain() is True

def test_execution_engine():
    print("\n4. Testing Execution Engine...")
    gate = ApprovalGate(
        require_human=False,
        policies=[RiskBasedPolicy(max_auto_approve_risk='low')]
    )
    engine = LocalExecutionEngine(approval_gate=gate)

    # Assertions
    assert engine.name == 'local_executor'
    assert engine.auto_verify is True

def test_data_resident_orchestrator():
    print("\n5. Testing Data-Resident Orchestrator...")
    orchestrator = DataResidentOrchestrator(name='test_orchestrator')

    finding = Finding(
        finding_type='SQL_INJECTION',
        severity='HIGH',
        resource='backend/db/query.ts',
        description='SQL injection vulnerability detected',
        patterns=['string_interpolation', 'unsanitized_input'],
        policies_violated=['PCI-6.5', 'OWASP-A3']
    )

    # Ingest finding
    finding_id = orchestrator.ingest_finding(finding)
    assert finding_id is not None

    # Request reasoning (sanitized)
    reasoning = orchestrator.request_reasoning(finding.id)
    assert reasoning is not None

    # Get telemetry (anonymized)
    telemetry = orchestrator.get_telemetry()
    assert 'tenant_id' in telemetry
    assert 'open_findings' in telemetry
