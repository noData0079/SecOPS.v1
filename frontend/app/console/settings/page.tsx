"use client";

import { useEffect, useState, FormEvent } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

type IntegrationHealth = "connected" | "partial" | "disconnected" | "unknown";

type IntegrationsStatus = {
  github?: IntegrationHealth;
  k8s?: IntegrationHealth;
  ci?: IntegrationHealth;
  llm?: IntegrationHealth;
  billing?: IntegrationHealth;
};

export default function SettingsPage() {
  const [status, setStatus] = useState<IntegrationsStatus>({
    github: "unknown",
    k8s: "unknown",
    ci: "unknown",
    llm: "unknown",
    billing: "unknown",
  });
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [githubToken, setGithubToken] = useState("");
  const [githubOrg, setGithubOrg] = useState("");
  const [githubRepo, setGithubRepo] = useState("");

  const [k8sEndpoint, setK8sEndpoint] = useState("");
  const [k8sToken, setK8sToken] = useState("");

  const [ciProvider, setCiProvider] = useState("github_actions");
  const [llmProvider, setLlmProvider] = useState("openai");
  const [llmApiKey, setLlmApiKey] = useState("");

  const [billingEnabled, setBillingEnabled] = useState(false);
  const [baseMargin, setBaseMargin] = useState(20);
  const [highMargin, setHighMargin] = useState(35);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoadingStatus(true);
        setError(null);

        const res = await fetch(`${API_BASE_URL}/integrations/status`, {
          headers: { "Content-Type": "application/json" },
        });

        if (!res.ok) {
          // Backend might not have this endpoint yet – fail gracefully
          return;
        }

        const json: any = await res.json();

        if (cancelled) return;

        const s: IntegrationsStatus = {
          github: normalizeHealth(json.github),
          k8s: normalizeHealth(json.k8s),
          ci: normalizeHealth(json.ci),
          llm: normalizeHealth(json.llm),
          billing: normalizeHealth(json.billing),
        };

        setStatus(s);

        // Pre-fill some fields if backend returns settings
        if (json.github_settings) {
          setGithubOrg(json.github_settings.org ?? "");
          setGithubRepo(json.github_settings.repo ?? "");
        }
        if (json.llm_settings) {
          setLlmProvider(json.llm_settings.provider ?? "openai");
        }
        if (json.billing_settings) {
          setBillingEnabled(!!json.billing_settings.enabled);
          if (typeof json.billing_settings.base_margin === "number") {
            setBaseMargin(json.billing_settings.base_margin);
          }
          if (typeof json.billing_settings.high_margin === "number") {
            setHighMargin(json.billing_settings.high_margin);
          }
        }
      } catch {
        if (!cancelled) {
          // Just keep defaults; UI still works
        }
      } finally {
        if (!cancelled) setLoadingStatus(false);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleSaveGithub = async (e: FormEvent) => {
    e.preventDefault();
    await safePost(
      `${API_BASE_URL}/integrations/github`,
      {
        token: githubToken || undefined,
        org: githubOrg || undefined,
        repo: githubRepo || undefined,
      },
      "GitHub integration updated"
    );
  };

  const handleSaveK8s = async (e: FormEvent) => {
    e.preventDefault();
    await safePost(
      `${API_BASE_URL}/integrations/k8s`,
      {
        api_server: k8sEndpoint || undefined,
        bearer_token: k8sToken || undefined,
      },
      "Kubernetes integration updated"
    );
  };

  const handleSaveCi = async (e: FormEvent) => {
    e.preventDefault();
    await safePost(
      `${API_BASE_URL}/integrations/ci`,
      {
        provider: ciProvider,
      },
      "CI provider updated"
    );
  };

  const handleSaveLlm = async (e: FormEvent) => {
    e.preventDefault();
    await safePost(
      `${API_BASE_URL}/integrations/llm`,
      {
        provider: llmProvider,
        api_key: llmApiKey || undefined,
      },
      "LLM provider updated"
    );
  };

  const handleSaveBilling = async (e: FormEvent) => {
    e.preventDefault();
    await safePost(
      `${API_BASE_URL}/billing/settings`,
      {
        enabled: billingEnabled,
        base_margin_percent: baseMargin,
        high_margin_percent: highMargin,
      },
      "Billing settings updated"
    );
  };

  async function safePost(url: string, body: any, successMessage: string) {
    try {
      setSaving(true);
      setToast(null);
      setError(null);

      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        throw new Error(`Backend responded with ${res.status}`);
      }

      setToast(successMessage);
    } catch {
      setError(
        "Failed to save settings. Check backend API URL, auth, or implementation."
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-64px)] bg-gray-50">
      <div className="max-w-6xl mx-auto px-6 py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
              Settings
            </h1>
            <p className="mt-1 text-sm text-slate-600 max-w-xl">
              Configure integrations, LLM providers, and billing margins for
              your organization. These settings control how SecOpsAI connects
              to your stack and how usage is billed.
            </p>
          </div>

          <div className="text-xs text-slate-500">
            {loadingStatus ? (
              <span>Loading integration status…</span>
            ) : (
              <span>Status loaded</span>
            )}
          </div>
        </div>

        {/* Toast / error */}
        {toast && (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs text-emerald-800">
            {toast}
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-700">
            {error}
          </div>
        )}

        {/* Grid of settings cards */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* GitHub */}
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">
                  GitHub integration
                </h2>
                <p className="text-[11px] text-slate-600">
                  Used for repo scanning, security alerts, and CI workflows
                  (GitHub Actions).
                </p>
              </div>
              <HealthPill state={status.github ?? "unknown"} />
            </div>

            <form onSubmit={handleSaveGithub} className="space-y-2">
              <div>
                <label className="block text-[11px] font-medium text-slate-600 mb-1">
                  GitHub token
                </label>
                <input
                  type="password"
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                  placeholder="ghp_************************"
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
                <p className="mt-1 text-[10px] text-slate-500">
                  PAT with read permissions for repos and security alerts.
                </p>
              </div>

              <div className="grid gap-2 grid-cols-2">
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">
                    Organization / user
                  </label>
                  <input
                    type="text"
                    value={githubOrg}
                    onChange={(e) => setGithubOrg(e.target.value)}
                    placeholder="your-org"
                    className="w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">
                    Repository (optional)
                  </label>
                  <input
                    type="text"
                    value={githubRepo}
                    onChange={(e) => setGithubRepo(e.target.value)}
                    placeholder="your-repo"
                    className="w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center rounded-md bg-slate-900 px-3 py-1.5 text-[11px] font-medium text-white hover:bg-slate-800 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {saving ? "Saving…" : "Save GitHub settings"}
                </button>
              </div>
            </form>
          </section>

          {/* Kubernetes */}
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">
                  Kubernetes clusters
                </h2>
                <p className="text-[11px] text-slate-600">
                  Used for K8s misconfiguration checks, resource limits, and
                  ingress exposure.
                </p>
              </div>
              <HealthPill state={status.k8s ?? "unknown"} />
            </div>

            <form onSubmit={handleSaveK8s} className="space-y-2">
              <div>
                <label className="block text-[11px] font-medium text-slate-600 mb-1">
                  API server URL
                </label>
                <input
                  type="text"
                  value={k8sEndpoint}
                  onChange={(e) => setK8sEndpoint(e.target.value)}
                  placeholder="https://your-cluster:6443"
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-600 mb-1">
                  Bearer token
                </label>
                <input
                  type="password"
                  value={k8sToken}
                  onChange={(e) => setK8sToken(e.target.value)}
                  placeholder="eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldU..."
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
                <p className="mt-1 text-[10px] text-slate-500">
                  Use a minimally-scoped ServiceAccount token (read-only where
                  possible).
                </p>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center rounded-md bg-slate-900 px-3 py-1.5 text-[11px] font-medium text-white hover:bg-slate-800 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {saving ? "Saving…" : "Save K8s settings"}
                </button>
              </div>
            </form>
          </section>

          {/* CI provider */}
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">
                  CI provider
                </h2>
                <p className="text-[11px] text-slate-600">
                  Configure where SecOpsAI should look for build logs and
                  pipeline definitions.
                </p>
              </div>
              <HealthPill state={status.ci ?? "unknown"} />
            </div>

            <form onSubmit={handleSaveCi} className="space-y-2">
              <div>
                <label className="block text-[11px] font-medium text-slate-600 mb-1">
                  Provider
                </label>
                <select
                  value={ciProvider}
                  onChange={(e) => setCiProvider(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="github_actions">GitHub Actions</option>
                  <option value="gitlab_ci">GitLab CI</option>
                  <option value="jenkins">Jenkins</option>
                </select>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center rounded-md bg-slate-900 px-3 py-1.5 text-[11px] font-medium text-white hover:bg-slate-800 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {saving ? "Saving…" : "Save CI settings"}
                </button>
              </div>
            </form>
          </section>

          {/* LLM provider */}
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">
                  LLM provider
                </h2>
                <p className="text-[11px] text-slate-600">
                  Choose which model stack powers RAG synthesis, explanations,
                  and fix suggestions.
                </p>
              </div>
              <HealthPill state={status.llm ?? "unknown"} />
            </div>

            <form onSubmit={handleSaveLlm} className="space-y-2">
              <div>
                <label className="block text-[11px] font-medium text-slate-600 mb-1">
                  Provider
                </label>
                <select
                  value={llmProvider}
                  onChange={(e) => setLlmProvider(e.target.value)}
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                >
                  <option value="openai">OpenAI / Compatible</option>
                  <option value="deepseek">DeepSeek</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="gemini">Google Gemini</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-600 mb-1">
                  API key
                </label>
                <input
                  type="password"
                  value={llmApiKey}
                  onChange={(e) => setLlmApiKey(e.target.value)}
                  placeholder="sk-************************"
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
                <p className="mt-1 text-[10px] text-slate-500">
                  For DeepSeek or other OpenAI-compatible endpoints, configure
                  the base URL on the backend.
                </p>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center rounded-md bg-slate-900 px-3 py-1.5 text-[11px] font-medium text-white hover:bg-slate-800 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {saving ? "Saving…" : "Save LLM settings"}
                </button>
              </div>
            </form>
          </section>

          {/* Billing / pricing engine */}
          <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">
                  Billing & margins
                </h2>
                <p className="text-[11px] text-slate-600">
                  Configure how the platform converts compute costs into
                  customer pricing (e.g. FREEMIUM, PRO, ENTERPRISE).
                </p>
              </div>
              <HealthPill state={status.billing ?? "unknown"} />
            </div>

            <form onSubmit={handleSaveBilling} className="space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-700">
                <span>Enable billing engine</span>
                <label className="inline-flex items-center gap-1">
                  <input
                    type="checkbox"
                    checked={billingEnabled}
                    onChange={(e) => setBillingEnabled(e.target.checked)}
                    className="h-3 w-3"
                  />
                  <span className="text-[11px]">Enabled</span>
                </label>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">
                    Base margin (%)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={baseMargin}
                    onChange={(e) =>
                      setBaseMargin(Number(e.target.value) || 0)
                    }
                    className="w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                  <p className="mt-1 text-[10px] text-slate-500">
                    Typical for small usage (e.g. PRO tier).
                  </p>
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">
                    High usage margin (%)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={highMargin}
                    onChange={(e) =>
                      setHighMargin(Number(e.target.value) || 0)
                    }
                    className="w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  />
                  <p className="mt-1 text-[10px] text-slate-500">
                    For very large workloads or ENTERPRISE tier.
                  </p>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex items-center rounded-md bg-slate-900 px-3 py-1.5 text-[11px] font-medium text-white hover:bg-slate-800 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {saving ? "Saving…" : "Save billing settings"}
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>
    </div>
  );
}

function normalizeHealth(raw: any): IntegrationHealth {
  const v = String(raw ?? "").toLowerCase();
  if (v === "connected" || v === "ok" || v === "healthy") return "connected";
  if (v === "partial" || v === "degraded") return "partial";
  if (v === "disconnected" || v === "error" || v === "failed") {
    return "disconnected";
  }
  return "unknown";
}

function HealthPill({ state }: { state: IntegrationHealth }) {
  let label = "Unknown";
  let dot = "bg-slate-400";
  let cls = "bg-slate-50 text-slate-700 border-slate-200";

  if (state === "connected") {
    label = "Connected";
    dot = "bg-emerald-500";
    cls = "bg-emerald-50 text-emerald-700 border-emerald-200";
  } else if (state === "partial") {
    label = "Partial";
    dot = "bg-amber-500";
    cls = "bg-amber-50 text-amber-700 border-amber-200";
  } else if (state === "disconnected") {
    label = "Not connected";
    dot = "bg-red-500";
    cls = "bg-red-50 text-red-700 border-red-200";
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium ${cls}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      {label}
    </span>
  );
}
