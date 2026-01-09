# The Sovereign Mechanica (TSM99)

**TSM99**: The Autonomous Agentic AI Platform for Security Operations.

> **DOMAIN**: [thesovereignmechanica.ai](https://thesovereignmechanica.ai)

TSM99 is a production-ready, self-evolving security automation platform that consolidates 10 layers of intelligence into a single sovereign control system.

## 🌟 Key Features
- **TSM99 AI Core**: Self-evolving learning system (Foundation → Autonomous)
- **Sovereign Data**: Full data residency with local execution
- **Poly-LLM**: Orchestrates GPT-4, Claude, Gemini, and Local models
- **Trust Ledger**: Cryptographic audit of all actions

## Multi-LLM RAG inspirations

The RAG stack in this repository is designed to stay provider-agnostic and can borrow ideas from several leading open-source projects:

- **LangChain** ([langchain-ai/langchain](https://github.com/langchain-ai/langchain)) for modular chains, tool invocation, and prompt/LLM abstractions.
- **LlamaIndex** ([run-llama/llama_index](https://github.com/run-llama/llama_index)) for ingestion pipelines, retriever composition, and response synthesizers.
- **GraphRAG** ([microsoft/graphrag](https://github.com/microsoft/graphrag)) for graph-aware retrieval, semantic neighborhoods, and multi-hop reasoning.

The intent is not to fork these projects, but to use their patterns to keep the `backend/src/rag` components composable and easy to swap between providers. See `docs/multi_llm_rag.md` for a deeper mapping between upstream ideas and the current engine.

## How to plug frameworks into the backend RAG engine

1. **Locate the orchestration layer.** The public API for the engine lives in `backend/src/rag/AdvancedRAGSystem.py`, which wires together retrieval (`SearchOrchestrator`), synthesis (`RAGSynthesizer`), and citation processing.
2. **Add retrievers or vector stores.** Implement new retriever classes under `backend/src/integrations` and expose them through `SearchOrchestrator` to mimic LangChain or LlamaIndex retriever patterns.
3. **Customize synthesis prompts.** `backend/src/rag/RAGSynthesizer.py` is where LangChain-style chains or LlamaIndex response synthesizers can be slotted in.
4. **Experiment with graph retrieval.** If adding GraphRAG-like context stitching, create graph-aware retrieval helpers in `backend/src/rag` and pass them into the orchestrator.

This setup keeps the project ready to incorporate best practices from multiple frameworks without tightly coupling to any single library.
T79 AI is an end-to-end DevT79 co-pilot that pairs a FastAPI backend with a Next.js 14 frontend. It automates security scanning, dependency auditing, CI/CD hardening, and delivers AI-powered remediation guidance.

## Repository layout
- **backend/** – FastAPI service with RAG integrations, platform routing, and observability hooks.
- **frontend/** – Next.js 14 app with TailwindCSS-driven UI for the T79 console.
- **infra/** – Docker, Kubernetes, and CI/CD assets (including docker-compose for local orchestration).
- **docs/** – Architectural notes such as the transformer/MoE overview.

## Quickstart
### Prerequisites
- Python 3.10+
- Node.js 18+ and npm (or a compatible package manager)
- Docker (optional, for containerized runs)

### Backend (FastAPI)
1. Create a virtual environment and install dependencies:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run the API locally:
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend (Next.js)
1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start the dev server:
   ```bash
   npm run dev
   ```
   The app defaults to http://localhost:3000 and expects the backend at http://localhost:8000.

### Docker Compose
Bring up both services with the provided compose file:
```bash
docker compose -f infra/docker-compose.yaml up --build
```

## 🚀 Deployment

### Prerequisites
- Python 3.9+
- OpenAI/Anthropic/Google API keys (optional for local models)

### Setup & Run
1. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Configure environment:
   ```bash
   # Copy .env.example to .env and add your API keys
   cp .env.example .env
   ```
3. Start the API:
   ```bash
   cd backend/src
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```
4. Access Documentation:
   - **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 📡 API Endpoints
- `POST /api/v1/findings` - Report security findings
- `GET /api/v1/findings` - List findings (with filters)
- `POST /api/v1/findings/{id}/fix` - Trigger auto-fix (Playbook or LLM)
- `GET /api/v1/system/metrics` - View system intelligence stats

## 🧪 Testing
Run integration tests to verify deployment:
```bash
python backend/tests/test_integration.py
```
## Additional resources
- Frontend integration guidance: `frontend/lib/appsSdkUiIntegration.ts`
- Transformer and MoE background: `docs/gpt-architecture.md`
- RAG and agentic integration blueprint: `docs/rag-agent-integration.md`
- Fine-tuning, agent blueprint, and alignment playbook: `docs/llm-finetuning-and-agents.md`
- High-throughput serving and deployment patterns with vLLM: `docs/vllm_integration.md`
