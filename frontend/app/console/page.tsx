"use client";

import { useEffect, useState } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

type PlatformStatus = {
  status?: string;
  env?: string;
  services?: Record<string, string>;
};

type SeverityCounts = {
  critical: number;
  high: number;
  medium: number;
  low: number;
};

type IssueSummary = {
  id: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low";
  source: string;
  created_at?: string;
};

type ConsoleState = {
  status: PlatformStatus | null;
  severityCounts: SeverityCounts;
  recentIssues: IssueSummary[];
};

export default function ConsolePage() {
  const [data, setData] = useState<ConsoleState>({
    status: null,
    severityCounts: {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
    },
    recentIssues: [],
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        const [statusRes, issuesRes] = await Promise.allSettled([
          fetch(`${API_BASE_URL}/platform/status`, {
            headers: { "Content-Type": "application/json" },
          }),
          fetch(`${API_BASE_URL}/platform/issues/overview`, {
            headers: { "Content-Type": "application/json" },
          }),
        ]);

        let status: PlatformStatus | null = null;
        let severityCounts: SeverityCounts = {
          critical: 0,
          high: 0,
          medium: 0,
          low: 0,
        };
        let recentIssues: IssueSummary[] = [];

        if (
          statusRes.status === "fulfilled" &&
          statusRes.value.ok &&
          !cancelled
        ) {
          const json = await statusRes.value.json();
          status = json ?? null;
        }

        if (
          issuesRes.status === "fulfilled" &&
          issuesRes.value.ok &&
          !cancelled
        ) {
          const json = await issuesRes.value.json();

          // We keep this defensive: accept several shapes.
          // Expected shape (example):
          // {
          //   severity_counts: { critical: 1, high: 2, medium: 3, low: 4 },
          //   recent_issues: [...]
          // }
          const counts =
            (json?.severity_counts as Partial<SeverityCounts>) ?? {};
          severityCounts = {
            critical: counts.critical ?? 0,
            high: counts.high ?? 0,
            medium: counts.medium ?? 0,
            low: counts.low ?? 0,
          };

          const issues = Array.isArray(json?.recent_issues)
            ? json.recent_issues
            : [];

          recentIssues = issues.map((it: any, idx: number) => ({
            id: String(it.id ?? idx),
            title: String(
              it.title ?? "Unlabeled issue (title not provided by backend)"
            ),
            severity: normalizeSeverity(it.severity),
            source: String(it.source ?? "Unknown"),
            created_at: it.created_at,
          }));
        }

        if (!cancelled) {
          setData({ status, severityCounts, recentIssues });
        }
      } catch (e) {
        if (!cancelled) {
          setError("Failed to load console data. Please try again.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  const { status, severityCounts, recentIssues } = data;

  return (
    <div className="min-h-[calc(100vh-64px)] bg-gray-50">
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
              SecOps Console
            </h1>
            <p className="mt-1 text-sm text-slate-600">
              High-level view of your security posture, automated checks, and
              AI-generated recommendations.
            </p>
          </div>

          <div className="flex flex-wrap gap-2 text-xs text-slate-500">
            <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-emerald-700">
              API: {API_BASE_URL.replace(/^https?:\/\//, "")}
            </span>
            {status?.env && (
              <span className="rounded-full border border-slate-200 bg-white px-3 py-1">
                Env: <span className="font-medium">{status.env}</span>
              </span>
            )}
          </div>
        </div>

        {/* Loading / error */}
        {loading && (
          <div className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
            Loading latest platform status and issues…
          </div>
        )}

        {error && !loading && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Main grid */}
        {!loading && (
          <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,1.2fr)]">
            {/* Left: Issues + recent activity */}
            <div className="space-y-6">
              {/* Severity summary */}
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-slate-900">
                    Issue severity overview
                  </h2>
                  <span className="text-[11px] text-slate-500">
                    Generated by latest checks
                  </span>
                </div>
                <div className="grid gap-3 sm:grid-cols-4">
                  <SeverityCard
                    label="Critical"
                    value={severityCounts.critical}
                    tone="critical"
                  />
                  <SeverityCard
                    label="High"
                    value={severityCounts.high}
                    tone="high"
                  />
                  <SeverityCard
                    label="Medium"
                    value={severityCounts.medium}
                    tone="medium"
                  />
                  <SeverityCard
                    label="Low"
                    value={severityCounts.low}
                    tone="low"
                  />
                </div>
              </div>

              {/* Recent issues */}
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-slate-900">
                    Recent issues
                  </h2>
                  <a
                    href="/console/issues"
                    className="text-xs text-blue-600 hover:underline"
                  >
                    View all
                  </a>
                </div>

                {recentIssues.length === 0 ? (
                  <p className="text-xs text-slate-500">
                    No issues received from the backend yet. Once integrations
                    are configured and checks run, new issues will appear here.
                  </p>
                ) : (
                  <div className="divide-y divide-slate-100">
                    {recentIssues.slice(0, 6).map((issue) => (
                      <IssueRow key={issue.id} issue={issue} />
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Right: Platform status / checks summary */}
            <div className="space-y-6">
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-slate-900">
                    Platform status
                  </h2>
                  <StatusPill status={status?.status ?? "unknown"} />
                </div>

                <dl className="space-y-2 text-xs text-slate-600">
                  <div className="flex justify-between">
                    <dt>Environment</dt>
                    <dd className="font-medium">
                      {status?.env ?? "not provided"}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt>Backend health</dt>
                    <dd className="font-medium">
                      {status?.status ?? "unknown"}
                    </dd>
                  </div>
                </dl>

                {status?.services && (
                  <div className="mt-4 border-t border-slate-100 pt-3">
                    <p className="mb-2 text-[11px] font-medium text-slate-500">
                      Services
                    </p>
                    <ul className="space-y-1.5 text-[11px] text-slate-600">
                      {Object.entries(status.services).map(
                        ([service, state]) => (
                          <li
                            key={service}
                            className="flex items-center justify-between"
                          >
                            <span className="truncate">{service}</span>
                            <span className="ml-3 font-medium">{state}</span>
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}
              </div>

              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="mb-2 text-sm font-semibold text-slate-900">
                  Next steps
                </h2>
                <ol className="list-inside list-decimal space-y-1 text-xs text-slate-600">
                  <li>
                    Configure your backend URL in{" "}
                    <code className="rounded bg-slate-100 px-1 py-0.5">
                      NEXT_PUBLIC_API_URL
                    </code>
                    .
                  </li>
                  <li>
                    Go to{" "}
                    <a
                      href="/console/settings"
                      className="text-blue-600 hover:underline"
                    >
                      Settings
                    </a>{" "}
                    to connect GitHub, CI, and Kubernetes clusters.
                  </li>
                  <li>
                    Trigger checks manually or let the scheduler run and then
                    revisit this console.
                  </li>
                </ol>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function normalizeSeverity(raw: any): IssueSummary["severity"] {
  const v = String(raw ?? "").toLowerCase();
  if (v === "critical") return "critical";
  if (v === "high") return "high";
  if (v === "medium") return "medium";
  if (v === "low") return "low";
  return "medium";
}

type SeverityCardProps = {
  label: string;
  value: number;
  tone: "critical" | "high" | "medium" | "low";
};

function SeverityCard({ label, value, tone }: SeverityCardProps) {
  const toneClasses =
    tone === "critical"
      ? "bg-red-50 text-red-700 border-red-100"
      : tone === "high"
      ? "bg-amber-50 text-amber-700 border-amber-100"
      : tone === "medium"
      ? "bg-emerald-50 text-emerald-700 border-emerald-100"
      : "bg-slate-50 text-slate-700 border-slate-100";

  return (
    <div className={`rounded-lg border p-3 ${toneClasses}`}>
      <div className="text-[11px] font-medium uppercase tracking-wide">
        {label}
      </div>
      <div className="mt-1 text-lg font-semibold">{value}</div>
      <div className="mt-0.5 text-[11px] text-current/70">
        open {label.toLowerCase()} issues
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const normalized = String(status ?? "").toLowerCase();
  let label = "Unknown";
  let dotClass = "bg-slate-400";
  let textClass = "text-slate-700 bg-slate-100 border-slate-200";

  if (normalized === "ok" || normalized === "healthy") {
    label = "Healthy";
    dotClass = "bg-emerald-500";
    textClass = "text-emerald-700 bg-emerald-50 border-emerald-200";
  } else if (normalized === "degraded" || normalized === "warn") {
    label = "Degraded";
    dotClass = "bg-amber-500";
    textClass = "text-amber-700 bg-amber-50 border-amber-200";
  } else if (normalized === "down" || normalized === "error") {
    label = "Down";
    dotClass = "bg-red-500";
    textClass = "text-red-700 bg-red-50 border-red-200";
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium ${textClass}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dotClass}`} />
      {label}
    </span>
  );
}

function IssueRow({ issue }: { issue: IssueSummary }) {
  const severityLabel =
    issue.severity === "critical"
      ? "CRITICAL"
      : issue.severity === "high"
      ? "HIGH"
      : issue.severity === "medium"
      ? "MEDIUM"
      : "LOW";

  const severityTone =
    issue.severity === "critical"
      ? "bg-red-50 text-red-700 border-red-200"
      : issue.severity === "high"
      ? "bg-amber-50 text-amber-700 border-amber-200"
      : issue.severity === "medium"
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : "bg-slate-50 text-slate-700 border-slate-200";

  return (
    <a
      href={`/console/issues/${encodeURIComponent(issue.id)}`}
      className="flex items-start gap-3 px-2 py-2.5 hover:bg-slate-50 rounded-lg transition"
    >
      <span
        className={`mt-0.5 inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${severityTone}`}
      >
        {severityLabel}
      </span>
      <div className="flex-1">
        <p className="text-xs font-medium text-slate-900">{issue.title}</p>
        <p className="mt-0.5 text-[11px] text-slate-500">
          Source: {issue.source}
          {issue.created_at && (
            <> • {new Date(issue.created_at).toLocaleString()}</>
          )}
        </p>
      </div>
    </a>
  );
}
