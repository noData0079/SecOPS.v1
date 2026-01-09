# SecOps-AI Component Catalog

> **Integrated from 44 repositories with 154,710+ files**

---

## Quick Start

```python
# Multi-Agent Security Crew
from secops.agent.orchestration import Crew, Agent, Task, Process

# Create agents
scanner = Agent(role="Security Scanner", goal="Find vulnerabilities")
analyst = Agent(role="Security Analyst", goal="Analyze findings")

# Create crew
crew = Crew(
    agents=[scanner, analyst],
    tasks=[scan_task, analyze_task],
    process=Process.sequential
)

# Execute
result = crew.kickoff(inputs={"target": "production"})
```

```python
# Security Scanning
from secops.integrations.security import SecurityScanner, CloudProvider

scanner = SecurityScanner(
    providers=[CloudProvider.AWS, CloudProvider.AZURE],
    compliance_frameworks=["cis", "soc2", "hipaa"]
)
report = scanner.scan()
print(f"Findings: {report.total_findings}")
```

```python
# LLM Red Teaming
from secops.extensions.security.red_team import RedTeamOrchestrator

red_team = RedTeamOrchestrator(
    target_model="gpt-4",
    target_callable=my_llm_function
)
report = red_team.run_assessment()
print(f"Vulnerabilities: {report.vulnerability_count}")
```

---

## Integrated Components

### 1. Agent Orchestration (`backend/src/agent/orchestration/`)
| Component | Description | Source |
|-----------|-------------|--------|
| `Crew` | Multi-agent team orchestration | crewAI |
| `Agent` | Individual agent with role/goal | crewAI |
| `Task` | Executable task definition | crewAI |
| `Flow` | Workflow state management | crewAI |
| `Process` | Execution modes (sequential/hierarchical) | crewAI |

### 2. Security Scanning (`backend/src/integrations/security/`)
| Component | Description | Source |
|-----------|-------------|--------|
| `SecurityScanner` | Multi-cloud security scanner | Prowler |
| `Finding` | Security finding representation | Prowler |
| `ScanReport` | Comprehensive scan report | Prowler |
| 4,000+ Security Checks | AWS, Azure, GCP, K8s | Prowler |

### 3. LLM Security (`backend/src/extensions/security/red_team/`)
| Component | Description | Source |
|-----------|-------------|--------|
| `RedTeamOrchestrator` | Automated LLM red teaming | PyRIT |
| `AttackStrategy` | Attack strategy interface | PyRIT |
| `PromptInjectionStrategy` | Prompt injection testing | PyRIT |
| `JailbreakStrategy` | Jailbreak testing | PyRIT |

### 4. Alert Management (`backend/src/services/alerts/`)
| Component | Description | Source |
|-----------|-------------|--------|
| `AlertHub` | Central alert management | Keep |
| `AlertCorrelator` | Alert correlation engine | Keep |
| `AlertWorkflow` | Automated alert workflows | Keep |
| `AlertEnricher` | Alert context enrichment | Keep |

---

## Documentation
All documentation from SecOPS.v1 has been merged:
- `docs/autonomous_evolution_engine.md`
- `docs/enterprise_onboarding.md`
- `docs/gpt-architecture.md`
- `docs/llama_models_integration.md`
- `docs/llm-finetuning-and-agents.md`
- `docs/multi_llm_rag.md`
- `docs/rag-agent-integration.md`
- `docs/t79ai_whitepaper.md`
- `docs/vllm_integration.md`

---

## Source Repositories Integrated

| Repository | Files | Key Components |
|------------|-------|----------------|
| crewAI | 2,065 | Multi-agent orchestration |
| PyRIT | 1,194 | LLM red teaming |
| Prowler | 7,368 | Cloud security scanning |
| Keep | 2,243 | Alert management |
| langchain | 2,899 | LLM chains/prompts |
| llama_index | 10,580 | RAG patterns |
| OpenHands | 2,613 | Autonomous coding |
| vllm | 3,330 | LLM serving |
| SecOPS.v1 | 268 | Core patterns |
| **+ 35 more** | 122,150 | Additional utilities |

**Total: 154,710 files integrated**

---

*Generated: 2026-01-09*
