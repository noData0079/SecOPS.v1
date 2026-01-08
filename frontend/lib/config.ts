// frontend/lib/config.ts

/* ============================================================================
 *  Environment Helpers
 * ========================================================================== */

export const isBrowser = typeof window !== "undefined";
export const isDev = process.env.NODE_ENV === "development";
export const isProd = process.env.NODE_ENV === "production";

/* ============================================================================
 *  API & Backend URLs
 * ========================================================================== */

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.trim() ||
  "http://localhost:8000";

/* ============================================================================
 *  Application Metadata
 * ========================================================================== */

export const APP_NAME = "T79 AI";
export const APP_DESCRIPTION =
  "Automated security scanning, dependency auditing, CI hardening, and AI-assisted remediation.";
export const APP_VERSION =
  process.env.NEXT_PUBLIC_APP_VERSION || "0.1.0";

/* ============================================================================
 *  Feature Flags
 * ========================================================================== */

export const FEATURES = {
  ENABLE_RAG: true,
  ENABLE_GITHUB_INTEGRATION: true,
  ENABLE_K8S_INTEGRATION: false, // flip when ready
  ENABLE_CI_INTEGRATION: true,
  ENABLE_AI_FIX_SUGGESTIONS: true,
  ENABLE_NOTIFICATIONS: false,
  ENABLE_MULTI_ORGANIZATION: false,
} as const;

/* ============================================================================
 *  UI Defaults
 * ========================================================================== */

export const UI = {
  THEME: "light", // or "dark"
  SIDEBAR_WIDTH: 260,
  MAX_PAGE_WIDTH: 1440,
  DEFAULT_DATE_FORMAT: "DD MMM YYYY, HH:mm",
} as const;

/* ============================================================================
 *  RAG Defaults
 * ========================================================================== */

export const RAG_DEFAULTS = {
  TOP_K: 5,
  USE_LIVE_SEARCH: false,
  MODEL: "gpt-4o-mini", // override in llm_client
} as const;

/* ============================================================================
 *  Pagination / Fetch Settings
 * ========================================================================== */

export const FETCH_LIMITS = {
  ISSUES_PER_PAGE: 20,
  CHECK_RUNS_PER_PAGE: 10,
} as const;

/* ============================================================================
 *  Utility Config
 * ========================================================================== */

export const RETRY_POLICY = {
  retries: 2,
  retryDelayMs: 500,
} as const;

/**
 * Use this for debugging environment issues
 */
export const CONFIG_DEBUG_DUMP = {
  API_URL,
  APP_NAME,
  APP_VERSION,
  isDev,
  isProd,
  FEATURES,
};
