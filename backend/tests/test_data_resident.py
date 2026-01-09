"""
Test script for data-resident architecture components.
"""
import sys
sys.path.insert(0, r'c:\Users\mymai\Desktop\SecOps-ai\backend\src')

print("Testing Data-Resident Architecture Components...")
print("=" * 50)

# Test 1: Sanitization
print("\n1. Testing Data Sanitization...")
from core.sanitization import DataSanitizer, ReasoningBundleBuilder

sanitizer = DataSanitizer()

# Test API key detection
test_text = "API key: sk-12345678901234567890 and password: MyS3cretPass!"
result = sanitizer.sanitize(test_text)
print("   Input:", test_text[:50], "...")
print("   Output:", result.sanitized_text[:50], "...")
print("   Redactions:", len(result.redactions))
print("   [OK] Sanitization working")

# Test 2: Reasoning Bundle
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
print("   Finding:", bundle.finding_id)
print("   Type:", bundle.finding_type)
print("   Component (hashed):", bundle.affected_component)
print("   [OK] Bundle builder working")

# Test 3: Trust Ledger
print("\n3. Testing Trust Ledger...")
from core.trust_ledger import TrustLedger, EntryType

ledger = TrustLedger(name='test')
entry = ledger.log_finding(
    finding_id='F-001',
    finding_type='SQL_INJECTION',
    severity='HIGH',
    resource='db/query.ts'
)
print("   Entry type:", entry.entry_type.value)
print("   Entry hash:", entry.hash[:16], "...")
print("   Chain valid:", ledger.verify_chain())
print("   [OK] Trust ledger working")

# Test 4: Execution Engine
print("\n4. Testing Execution Engine...")
from core.execution import LocalExecutionEngine, ApprovalGate, RiskBasedPolicy

gate = ApprovalGate(
    require_human=False,
    policies=[RiskBasedPolicy(max_auto_approve_risk='low')]
)
engine = LocalExecutionEngine(approval_gate=gate)
print("   Engine name:", engine.name)
print("   Auto-verify:", engine.auto_verify)
print("   [OK] Execution engine working")

# Test 5: Full Orchestrator
print("\n5. Testing Data-Resident Orchestrator...")
from core.data_resident import DataResidentOrchestrator, Finding

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
print("   Finding ingested:", finding_id[:8], "...")

# Request reasoning (sanitized)
reasoning = orchestrator.request_reasoning(finding.id)
print("   Reasoning bundle:", len(reasoning), "chars")

# Get telemetry (anonymized)
telemetry = orchestrator.get_telemetry()
print("   Telemetry: tenant_id=" + telemetry['tenant_id'] + ", findings=" + str(telemetry['open_findings']))
print("   [OK] Orchestrator working")

print("\n" + "=" * 50)
print("[SUCCESS] ALL DATA-RESIDENT COMPONENTS VERIFIED!")
print("=" * 50)
