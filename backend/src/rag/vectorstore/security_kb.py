"""
Security Knowledge Vector Store

RAG-based security knowledge retrieval using local vector stores.
Provides context-aware security information for remediation.
"""

from __future__ import annotations

import uuid
import hashlib
import logging
import json
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KnowledgeType(str, Enum):
    """Types of security knowledge."""
    
    CVE = "cve"
    OWASP = "owasp"
    CIS = "cis"
    PLAYBOOK = "playbook"
    REMEDIATION = "remediation"
    BEST_PRACTICE = "best_practice"
    POLICY = "policy"


@dataclass
class SecurityDocument:
    """A security knowledge document."""
    
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    title: str = ""
    knowledge_type: KnowledgeType = KnowledgeType.REMEDIATION
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "title": self.title,
            "knowledge_type": self.knowledge_type.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class SearchResult:
    """Result from a vector search."""
    
    document: SecurityDocument
    score: float
    distance: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.document.doc_id,
            "title": self.document.title,
            "content": self.document.content[:500] + "..." if len(self.document.content) > 500 else self.document.content,
            "score": self.score,
            "knowledge_type": self.document.knowledge_type.value,
        }


class EmbeddingEngine:
    """
    Generate embeddings for text.
    
    Supports multiple backends:
    - sentence-transformers (local)
    - OpenAI embeddings
    - HuggingFace embeddings
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        use_openai: bool = False,
    ):
        self.model_name = model_name
        self.use_openai = use_openai
        self._model = None
        self._openai_client = None
    
    def _get_model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded embedding model: {self.model_name}")
            except ImportError:
                logger.warning("sentence-transformers not available, using fallback")
        return self._model
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts."""
        if self.use_openai:
            return self._embed_openai(texts)
        return self._embed_local(texts)
    
    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local model."""
        model = self._get_model()
        if model is None:
            # Fallback: simple hash-based "embedding"
            return [self._fallback_embed(t) for t in texts]
        
        embeddings = model.encode(texts)
        return embeddings.tolist()
    
    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI."""
        import os
        import openai
        
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        return [item.embedding for item in response.data]
    
    def _fallback_embed(self, text: str) -> List[float]:
        """Simple fallback embedding based on character hashing."""
        # Create a deterministic embedding from text
        hash_val = int(hashlib.sha256(text.encode()).hexdigest(), 16)
        embedding = []
        for i in range(384):  # Match MiniLM dimension
            embedding.append(((hash_val >> i) & 1) * 2 - 1 + (hash_val % 1000) / 1000)
        return embedding


class SecurityVectorStore(BaseModel):
    """
    Vector store for security knowledge.
    
    Stores and retrieves security documents using semantic similarity.
    Supports ChromaDB for persistence or in-memory for testing.
    
    Attributes:
        name: Store identifier
        persist_path: Path to persist the database
        embedding_model: Model for generating embeddings
        use_chroma: Use ChromaDB backend
    """
    
    model_config = {"arbitrary_types_allowed": True}
    
    name: str = Field(default="security_knowledge")
    persist_path: Optional[str] = Field(default=None)
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    use_chroma: bool = Field(default=True)
    
    _embedding_engine: EmbeddingEngine = None
    _collection = None
    _documents: Dict[str, SecurityDocument] = {}
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        self._embedding_engine = EmbeddingEngine(self.embedding_model)
        self._documents = {}
        self._collection = None
        
        if self.use_chroma:
            self._init_chroma()
        else:
            self._init_memory()
    
    def _init_chroma(self):
        """Initialize ChromaDB collection."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            if self.persist_path:
                client = chromadb.PersistentClient(path=self.persist_path)
            else:
                client = chromadb.Client()
            
            self._collection = client.get_or_create_collection(
                name=self.name,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"ChromaDB collection initialized: {self.name}")
        except ImportError:
            logger.warning("ChromaDB not available, using in-memory store")
            self._init_memory()
    
    def _init_memory(self):
        """Initialize in-memory store."""
        self._documents = {}
        self._embeddings: Dict[str, List[float]] = {}
        logger.info("Using in-memory vector store")
    
    def add_documents(self, documents: List[SecurityDocument]) -> int:
        """Add documents to the vector store."""
        if not documents:
            return 0
        
        # Generate embeddings
        texts = [doc.content for doc in documents]
        embeddings = self._embedding_engine.embed(texts)
        
        for doc, embedding in zip(documents, embeddings):
            doc.embedding = embedding
            self._documents[doc.doc_id] = doc
        
        if self._collection is not None:
            # Add to ChromaDB
            self._collection.add(
                ids=[doc.doc_id for doc in documents],
                embeddings=embeddings,
                documents=texts,
                metadatas=[{
                    "title": doc.title,
                    "knowledge_type": doc.knowledge_type.value,
                    **doc.metadata
                } for doc in documents]
            )
        
        logger.info(f"Added {len(documents)} documents to vector store")
        return len(documents)
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        knowledge_type: Optional[KnowledgeType] = None,
    ) -> List[SearchResult]:
        """Search for relevant documents."""
        query_embedding = self._embedding_engine.embed([query])[0]
        
        if self._collection is not None:
            # Search ChromaDB
            where_filter = None
            if knowledge_type:
                where_filter = {"knowledge_type": knowledge_type.value}
            
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
            )
            
            search_results = []
            for i, doc_id in enumerate(results["ids"][0]):
                if doc_id in self._documents:
                    doc = self._documents[doc_id]
                    distance = results["distances"][0][i] if results["distances"] else 0
                    score = 1 - distance  # Convert distance to similarity
                    search_results.append(SearchResult(
                        document=doc,
                        score=score,
                        distance=distance,
                    ))
            
            return search_results
        else:
            # In-memory search
            return self._memory_search(query_embedding, n_results, knowledge_type)
    
    def _memory_search(
        self,
        query_embedding: List[float],
        n_results: int,
        knowledge_type: Optional[KnowledgeType],
    ) -> List[SearchResult]:
        """Search in-memory store."""
        import math
        
        def cosine_similarity(a: List[float], b: List[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            return dot / (norm_a * norm_b + 1e-8)
        
        results = []
        for doc in self._documents.values():
            if knowledge_type and doc.knowledge_type != knowledge_type:
                continue
            
            if doc.embedding:
                score = cosine_similarity(query_embedding, doc.embedding)
                results.append(SearchResult(
                    document=doc,
                    score=score,
                    distance=1 - score,
                ))
        
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:n_results]
    
    def get_document(self, doc_id: str) -> Optional[SecurityDocument]:
        """Get a document by ID."""
        return self._documents.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        if doc_id in self._documents:
            del self._documents[doc_id]
            
            if self._collection is not None:
                self._collection.delete(ids=[doc_id])
            
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        type_counts = {}
        for doc in self._documents.values():
            t = doc.knowledge_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            "name": self.name,
            "total_documents": len(self._documents),
            "by_type": type_counts,
            "using_chroma": self._collection is not None,
        }


def create_security_knowledge_base() -> SecurityVectorStore:
    """Create a pre-populated security knowledge base."""
    store = SecurityVectorStore(name="security_kb")
    
    # Add built-in security knowledge
    documents = [
        SecurityDocument(
            title="SQL Injection Prevention",
            content="SQL injection attacks occur when user input is directly included in SQL queries without proper sanitization. Prevention methods include: (1) Use parameterized queries or prepared statements, (2) Use ORM frameworks that handle escaping, (3) Validate and sanitize all user input, (4) Use stored procedures, (5) Apply least privilege to database accounts.",
            knowledge_type=KnowledgeType.REMEDIATION,
            metadata={"cwe": "CWE-89", "owasp": "A03:2021"},
        ),
        SecurityDocument(
            title="Cross-Site Scripting (XSS) Prevention",
            content="XSS attacks inject malicious scripts into web pages. Prevention: (1) Encode output based on context (HTML, JavaScript, URL, CSS), (2) Use Content Security Policy (CSP) headers, (3) Use HttpOnly and Secure flags on cookies, (4) Validate input on server side, (5) Use modern frameworks with auto-escaping.",
            knowledge_type=KnowledgeType.REMEDIATION,
            metadata={"cwe": "CWE-79", "owasp": "A03:2021"},
        ),
        SecurityDocument(
            title="Hardcoded Credentials Remediation",
            content="Never store credentials in source code. Remediation: (1) Use environment variables, (2) Use secret management systems (Vault, AWS Secrets Manager, Azure Key Vault), (3) Rotate credentials regularly, (4) Use CI/CD secret injection, (5) Scan commits for secrets before push.",
            knowledge_type=KnowledgeType.REMEDIATION,
            metadata={"cwe": "CWE-798"},
        ),
        SecurityDocument(
            title="OWASP Top 10 2021",
            content="A01: Broken Access Control, A02: Cryptographic Failures, A03: Injection, A04: Insecure Design, A05: Security Misconfiguration, A06: Vulnerable Components, A07: Auth Failures, A08: Data Integrity Failures, A09: Security Logging Failures, A10: SSRF.",
            knowledge_type=KnowledgeType.OWASP,
            metadata={"year": "2021"},
        ),
        SecurityDocument(
            title="JWT Security Best Practices",
            content="Secure JWT implementation: (1) Use strong algorithms (RS256, ES256), avoid HS256 in multi-tenant systems, (2) Always verify signatures, (3) Validate all claims (exp, iat, iss, aud), (4) Use short expiration times, (5) Store tokens securely (HttpOnly cookies), (6) Implement token refresh mechanism.",
            knowledge_type=KnowledgeType.BEST_PRACTICE,
            metadata={"category": "authentication"},
        ),
        SecurityDocument(
            title="Kubernetes Security Checklist",
            content="K8s security: (1) Use RBAC, avoid cluster-admin, (2) Enable Pod Security Standards, (3) Use network policies, (4) Scan container images, (5) Use secrets encryption, (6) Enable audit logging, (7) Limit resource requests, (8) Use read-only root filesystem.",
            knowledge_type=KnowledgeType.CIS,
            metadata={"platform": "kubernetes"},
        ),
    ]
    
    store.add_documents(documents)
    
    return store
