// frontend/lib/types.ts

/* ============================================================================
 *  Shared primitives / aliases
 * ========================================================================== */

export type ISODateString = string;

/* ============================================================================
 *  Auth
 * ========================================================================== */

export interface AuthLoginRequest {
  email: string;
  password: string;
}

export interface AuthUser {
  id: string;
  org_id: string;
  email: string;
  full_name?: string | null;
  is_superuser: boolean;
}

export interface AuthLoginResponse {
  access_token: string;
  token_type: "bearer";
  user: AuthUser;
}

/* ============================================================================
 *  Issues
 * ========================================================================== */

export type IssueSeverity = "info" | "low" | "medium" | "high" | "critical";
export type IssueStatus = "open" | "acknowledged" | "resolved" | "ignored";

export interface Issue {
  id: string;
  org_id: string;

  title: string;
  description?: string | null;

  severity: IssueSeverity;
  status: IssueStatus;

  source: string;          // github | k8s | ci | scanner | rag | manual
  code?: string | null;    // rule / check id

  target?: string | null;  // repo, cluster, service, env, etc.
  external_url?: string | null;

  metadata?: Record<string, any> | null;

  created_at: ISODateString;
  updated_at: ISODateString;
  resolved_at?: ISODateString | null;
}

/* ============================================================================
 *  RAG / AI query
 * ========================================================================== */

export interface RAGQueryRequest {
  query: string;
  top_k?: number;
  org_id?: string;
  project_id?: string;
  use_live_search?: boolean;
}

export interface RAGSource {
  id: string;
  title?: string;
  url?: string;
  snippet?: string;
  score?: number;
  metadata?: Record<string, any>;
}

export interface RAGTokenUsage {
  prompt: number;
  completion: number;
  total: number;
}

export interface RAGQueryMeta {
  model?: string;
  latency_ms?: number;
  token_usage?: RAGTokenUsage;
}

export interface RAGQueryResponse {
  answer: string;
  reasoning?: string;
  sources: RAGSource[];
  meta?: RAGQueryMeta;
}

/* ============================================================================
 *  Platform / health
 * ========================================================================== */

export type HealthStatus = "ok" | "degraded" | "error";

export interface PlatformHealthCheck {
  name: string;                // e.g. "database", "github", "rag"
  status: HealthStatus;        // ok | degraded | error
  details?: string;
}

export interface PlatformHealthResponse {
  status: HealthStatus;
  checks: PlatformHealthCheck[];
  timestamp: ISODateString;
  version?: string;
}

/* ============================================================================
 *  Generic API helpers (optional but handy)
 * ========================================================================== */

export interface ApiErrorShape {
  detail?: string | string[] | Record<string, any>;
}

/**
 * Shape for simple "success" style responses from mutation endpoints.
 */
export interface SimpleSuccessResponse {
  success: boolean;
  message?: string;
}
