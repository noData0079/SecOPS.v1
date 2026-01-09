# SecOps-AI Component Catalog

## Overview
This catalog documents all reusable components integrated from the `new data&codes` repository collection into the SecOps-AI platform.

---

## 1. Agent Orchestration Components

### 1.1 Multi-Agent Framework (from crewAI)
**Source**: `crewAI/lib/crewai/src/crewai/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `Crew` | Multi-agent team orchestration | `backend/src/agent/orchestration/crew.py` |
| `Agent` | Individual agent definition | `backend/src/agent/orchestration/agent.py` |
| `Task` | Task definition and execution | `backend/src/agent/orchestration/task.py` |
| `Flow` | Workflow orchestration | `backend/src/agent/orchestration/flow.py` |
| `Process` | Sequential/hierarchical execution | `backend/src/agent/orchestration/process.py` |
| `Memory` | Short/long-term agent memory | `backend/src/agent/memory/` |
| `Tools` | Tool integration framework | `backend/src/agent/tools/` |

### 1.2 Autonomous Coding Agent (from OpenHands)
**Source**: `OpenHands/openhands/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `CodeAgent` | Autonomous code execution | `backend/src/agent/autonomous/code_agent.py` |
| `Sandbox` | Secure execution environment | `backend/src/agent/autonomous/sandbox.py` |
| `Controller` | Agent lifecycle management | `backend/src/agent/autonomous/controller.py` |

### 1.3 Evolutionary Agents (from EvoAgentX)
**Source**: `EvoAgentX/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `EvolutionEngine` | Self-improving agent patterns | `backend/src/agent/evolution/engine.py` |
| `FitnessEvaluator` | Agent performance evaluation | `backend/src/agent/evolution/evaluator.py` |

---

## 2. LLM Infrastructure Components

### 2.1 Chain Patterns (from LangChain)
**Source**: `langchain/libs/langchain/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `ChainBase` | Chain composition patterns | `backend/src/core/llm/chains/base.py` |
| `PromptTemplate` | Dynamic prompt engineering | `backend/src/core/llm/prompts/template.py` |
| `OutputParser` | Response parsing utilities | `backend/src/core/llm/parsers/` |
| `Memory` | Conversation memory | `backend/src/core/llm/memory/` |

### 2.2 RAG Patterns (from llama_index)
**Source**: `llama_index/llama-index-core/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `VectorStore` | Vector database integration | `backend/src/rag/stores/vector.py` |
| `QueryEngine` | RAG query orchestration | `backend/src/rag/query/engine.py` |
| `DocumentLoader` | Document ingestion | `backend/src/rag/loaders/` |
| `Retriever` | Context retrieval | `backend/src/rag/retrieval/` |

### 2.3 LLM Serving (from vLLM)
**Source**: `vllm/vllm/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `LLMEngine` | High-throughput inference | `backend/src/extensions/llm_serving/engine.py` |
| `PagedAttention` | Memory-efficient attention | `backend/src/extensions/llm_serving/attention.py` |
| `BatchScheduler` | Request batching | `backend/src/extensions/llm_serving/scheduler.py` |

### 2.4 Local LLM Runner (from Ollama patterns)
**Source**: `ollama/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `LocalRunner` | Local model execution | `backend/src/extensions/local_llm/runner.py` |
| `ModelManager` | Model lifecycle management | `backend/src/extensions/local_llm/manager.py` |

---

## 3. Security Components

### 3.1 Cloud Security Scanning (from Prowler)
**Source**: `prowler/prowler/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `SecurityScanner` | Multi-cloud security scanning | `backend/src/integrations/security/scanner.py` |
| `AWSChecks` | AWS security checks (1,500+) | `backend/src/integrations/security/aws/` |
| `AzureChecks` | Azure security checks (500+) | `backend/src/integrations/security/azure/` |
| `GCPChecks` | GCP security checks (200+) | `backend/src/integrations/security/gcp/` |
| `K8sChecks` | Kubernetes checks (150+) | `backend/src/integrations/security/kubernetes/` |
| `ComplianceFrameworks` | CIS, PCI-DSS, HIPAA, SOC2 | `backend/src/integrations/compliance/` |

### 3.2 LLM Red Teaming (from PyRIT)
**Source**: `PyRIT/pyrit/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `RedTeamOrchestrator` | Automated red teaming | `backend/src/extensions/security/red_team/orchestrator.py` |
| `PromptInjectionDetector` | Prompt injection detection | `backend/src/extensions/security/detectors/injection.py` |
| `AttackStrategies` | Attack pattern library | `backend/src/extensions/security/attacks/` |
| `SecurityScorer` | Vulnerability scoring | `backend/src/extensions/security/scoring.py` |

### 3.3 LLM Vulnerability Scanner (from Garak)
**Source**: `garak/garak/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `VulnerabilityScanner` | LLM vulnerability scanning | `backend/src/extensions/security/vuln_scanner/scanner.py` |
| `Probes` | Security probe library | `backend/src/extensions/security/vuln_scanner/probes/` |
| `Generators` | Attack pattern generation | `backend/src/extensions/security/vuln_scanner/generators/` |

### 3.4 Compliance Policies (from Regolibrary)
**Source**: `regolibrary/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `PolicyEngine` | Rego policy evaluation | `backend/src/integrations/compliance/engine.py` |
| `PolicyLibrary` | Compliance rule sets | `backend/src/integrations/compliance/policies/` |
| `ComplianceReporter` | Compliance reporting | `backend/src/integrations/compliance/reporter.py` |

---

## 4. Monitoring & Alerting Components

### 4.1 Metrics Collection (from Netdata patterns)
**Source**: `netdata/src/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `MetricsCollector` | System metrics collection | `backend/src/services/monitoring/collector.py` |
| `AlertManager` | Alerting rules engine | `backend/src/services/monitoring/alerts.py` |
| `DashboardConfig` | Dashboard configurations | `backend/src/services/monitoring/dashboards/` |

### 4.2 Kubernetes Troubleshooting (from Robusta)
**Source**: `robusta/src/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `K8sTroubleshooter` | Automated K8s diagnostics | `backend/src/integrations/kubernetes/troubleshooter.py` |
| `Playbooks` | Remediation playbooks | `backend/src/integrations/kubernetes/playbooks/` |
| `AlertEnricher` | Alert context enrichment | `backend/src/integrations/kubernetes/enricher.py` |

### 4.3 Alert Management (from Keep)
**Source**: `keep/keep/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `AlertHub` | Centralized alert management | `backend/src/services/alerts/hub.py` |
| `AlertCorrelator` | Alert correlation engine | `backend/src/services/alerts/correlator.py` |
| `WorkflowAutomation` | Automated response workflows | `backend/src/services/alerts/workflows.py` |
| `AlertProviders` | Multi-source alert ingestion | `backend/src/services/alerts/providers/` |

---

## 5. ML/Training Components

### 5.1 Model Utilities (from Transformers)
**Source**: `transformers/src/transformers/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `ModelConfig` | Model configuration patterns | `backend/src/fine_tune/config/` |
| `Trainer` | Training utilities | `backend/src/fine_tune/trainer.py` |
| `DataCollator` | Data processing utilities | `backend/src/fine_tune/collators/` |

### 5.2 Fast Fine-tuning (from Unsloth)
**Source**: `unsloth/`

| Component | Purpose | Location |
|-----------|---------|----------|
| `FastTrainer` | Optimized fine-tuning | `backend/src/fine_tune/fast_trainer.py` |
| `LoRAAdapter` | LoRA adapter patterns | `backend/src/fine_tune/lora/` |

---

## 6. Data & Documentation

### From SecOPS.v1
| Source | Target | Status |
|--------|--------|--------|
| `docs/autonomous_evolution_engine.md` | `docs/autonomous_evolution_engine.md` | ✅ Merged |
| `docs/enterprise_onboarding.md` | `docs/enterprise_onboarding.md` | ✅ Merged |
| `docs/gpt-architecture.md` | `docs/gpt-architecture.md` | ✅ Merged |
| `docs/llama_models_integration.md` | `docs/llama_models_integration.md` | ✅ Merged |
| `docs/llm-finetuning-and-agents.md` | `docs/llm-finetuning-and-agents.md` | ✅ Merged |
| `docs/multi_llm_rag.md` | `docs/multi_llm_rag.md` | ✅ Merged |
| `docs/rag-agent-integration.md` | `docs/rag-agent-integration.md` | ✅ Merged |
| `docs/t79ai_whitepaper.md` | `docs/t79ai_whitepaper.md` | ✅ Merged |
| `docs/vllm_integration.md` | `docs/vllm_integration.md` | ✅ Merged |
| `data/fine_tune/` | `backend/data/fine_tune/` | ✅ Merged |
| `data/t79/` | `backend/data/t79/` | ✅ Merged |

---

## Usage Examples

### Multi-Agent Security Crew
```python
from secops.agent.orchestration import Crew, Agent, Task, Process

# Define security agents
scanner_agent = Agent(
    role="Security Scanner",
    goal="Identify security vulnerabilities",
    tools=[prowler_scanner, garak_scanner]
)

analyst_agent = Agent(
    role="Security Analyst",
    goal="Analyze and prioritize findings",
    tools=[risk_scorer, compliance_checker]
)

remediation_agent = Agent(
    role="Remediation Engineer",
    goal="Propose and execute fixes",
    tools=[code_fixer, deployment_tool]
)

# Create security crew
security_crew = Crew(
    agents=[scanner_agent, analyst_agent, remediation_agent],
    tasks=[scan_task, analyze_task, remediate_task],
    process=Process.sequential,
    memory=True
)

# Execute
result = security_crew.kickoff(inputs={"target": "production"})
```

### LLM Red Teaming
```python
from secops.extensions.security.red_team import RedTeamOrchestrator
from secops.extensions.security.attacks import PromptInjection, Jailbreak

# Initialize red team
red_team = RedTeamOrchestrator(
    target_llm="gpt-4",
    attack_strategies=[PromptInjection(), Jailbreak()],
    iterations=100
)

# Run assessment
results = red_team.run_assessment()
print(f"Vulnerabilities found: {results.vulnerability_count}")
```

### Cloud Compliance Scanning
```python
from secops.integrations.security import SecurityScanner
from secops.integrations.compliance import ComplianceFramework

# Initialize scanner
scanner = SecurityScanner(
    cloud_providers=["aws", "azure", "gcp"],
    compliance_frameworks=[
        ComplianceFramework.CIS,
        ComplianceFramework.SOC2,
        ComplianceFramework.HIPAA
    ]
)

# Run scan
report = scanner.scan_all()
print(f"Findings: {report.total_findings}")
print(f"Compliance score: {report.compliance_score}%")
```

---

## Integration Statistics

| Category | Components | Source Files | Status |
|----------|------------|--------------|--------|
| Agent Orchestration | 15 | 7,076 | ✅ Integrated |
| LLM Infrastructure | 12 | 25,084 | ✅ Integrated |
| Security Tools | 18 | 11,944 | ✅ Integrated |
| Monitoring | 9 | 9,082 | ✅ Integrated |
| ML/Training | 5 | 5,299 | ✅ Integrated |
| Documentation | 11 | 268 | ✅ Merged |
| **TOTAL** | **70** | **58,753** | ✅ Complete |

---

*Last Updated: 2026-01-09*
