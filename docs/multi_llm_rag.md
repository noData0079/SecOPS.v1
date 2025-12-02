# Multi-LLM RAG patterns

SecOPS.v1 keeps its Retrieval-Augmented Generation engine modular so that patterns from multiple open-source libraries can be reused without vendor lock-in. The repositories below are the main references when extending `backend/src/rag`.

| Project | What to borrow | Where to plug it in |
| --- | --- | --- |
| [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | Chains, tools, retriever abstractions, and prompt templates. | Wrap chain or tool calls inside `SearchOrchestrator` or `RAGSynthesizer` so they feed into `AdvancedRAGSystem.answer_query`. |
| [run-llama/llama_index](https://github.com/run-llama/llama_index) | Node-based ingestion, retriever composition, and response synthesizers. | Mirror the ingestion/output schema in new classes under `backend/src/integrations` and pass composed retrievers into the orchestrator. |
| [microsoft/graphrag](https://github.com/microsoft/graphrag) | Graph construction, semantic neighborhoods, and multi-hop reasoning. | Add graph-aware retrieval helpers in `backend/src/rag` and surface them via the orchestrator for graph-based context stitching. |

## Implementation tips

- Keep new retrievers side-effect free and injectable so they can be toggled per organization or query mode.
- Normalize outputs to `AdvancedRAGTypes.RetrievedContext` and `RAGAnswer` so the API schemas stay stable regardless of backend provider.
- Reuse the existing `LLMClient` abstraction before wiring in provider-specific SDKs.

This document should be updated as new frameworks or patterns are incorporated into the RAG pipeline.
