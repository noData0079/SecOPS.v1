// frontend/app/console/issues/[id]/page.tsx

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

type Severity = "critical" | "high" | "medium" | "low";

type IssueDetail = {
  id: string;
  title: string;
  severity: Severity;
  source: string;
  status?: "open" | "resolved" | "ignored" | string;
  created_at?: string;
  updated_at?: string;

  // Optional fields your backend may expose
  description?: string;
  impact?: string;
  explanation?: string;
  recommended_fix?: string;
  remediation_steps?: string;
  code_snippet?: string;
  check_name?: string;
  check_type?: string;
};

async function fetchIssue(id: string): Promise<IssueDetail | null> {
  try {
    const res = await fetch(
      `${API_BASE_URL}/platform/issues/${encodeURIComponent(id)}`,
      {
        // we want fresh data when navigating
        cache: "no-store",
      }
    );

    if (!res.ok) {
      return null;
    }

    const json: any = await res.json();

    // Support either plain object or { issue: {...} }
    const raw = json.issue ?? json;

    const detail: IssueDetail = {
      id: String(raw.id ?? id),
      title: String(
        raw.title ?? "Unlabeled issue (title not provided by backend)"
      ),
      severity: normalizeSeverity(raw.severity),
      source: String(raw.source ?? raw.check_source ?? "Unknown"),
      status: normalizeStatus(raw.status),

      created_at: raw.created_at,
      updated_at: raw.updated_at,

      description: raw.description ?? raw.summary ?? undefined,
      impact: raw.impact ?? raw.risk ?? undefined,
      explanation: raw.explanation ?? raw.analysis ?? undefined,
      recommended_fix: raw.recommended_fix ?? raw.fix ?? undefined,
      remediation_steps: raw.remediation_steps ?? raw.steps ?? undefined,
      code_snippet: raw.code_snippet ?? raw.patch ?? undefined,
      check_name: raw.check_name ?? raw.rule_name ?? undefined,
      check_type: raw.check_type ?? raw.kind ?? undefined,
    };

    return detail;
  } catch {
    return null;
  }
}

export default async function IssueDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const issue = await fetchIssue(params.id);

  if (!issue) {
    return (
      <div className="min-h-[calc(100vh-64px)] bg-gray-50">
        <div className="max-w-4xl mx-auto px-6 py-10">
          <h1 className="text-xl font-semibold text-slate-900 mb-2">
            Issue not found
          </h1>
          <p className="text-sm text-slate-600 mb-4">
            We couldn&apos;t load details for this issue. It may have been
            deleted, or the backend is currently unavailable.
          </p>
          <a
            href="/console/issues"
            className="inline-flex items-center rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-50"
          >
            ← Back to issues
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-64px)] bg-gray-50">
      <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">
        {/* Breadcrumb */}
        <div className="text-[11px] text-slate-500 flex items-center gap-1">
          <a
            href="/console"
            className="hover:text-blue-600 hover:underline"
          >
            Console
          </a>
          <span>/</span>
          <a
            href="/console/issues"
            className="hover:text-blue-600 hover:underline"
          >
            Issues
          </a>
          <span>/</span>
          <span className="truncate max-w-[220px] sm:max-w-xs">
            {issue.title}
          </span>
        </div>

        {/* Header */}
        <header className="space-y-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <SeverityBadge severity={issue.severity} />
                <StatusBadge status={issue.status ?? "open"} />
                {issue.source && (
                  <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] text-slate-700">
                    Source: {issue.source}
                  </span>
                )}
              </div>
              <h1 className="text-xl font-semibold tracking-tight text-slate-900">
                {issue.title}
              </h1>
            </div>

            <div className="text-[11px] text-right text-slate-500 space-y-0.5">
              {issue.created_at && (
                <p>
                  Created:{" "}
                  <span className="font-medium">
                    {new Date(issue.created_at).toLocaleString()}
                  </span>
                </p>
              )}
              {issue.updated_at && (
                <p>
                  Updated:{" "}
                  <span className="font-medium">
                    {new Date(issue.updated_at).toLocaleString()}
                  </span>
                </p>
              )}
              {issue.check_name && (
                <p>
                  Check:{" "}
                  <span className="font-medium">{issue.check_name}</span>
                </p>
              )}
            </div>
          </div>
        </header>

        {/* Content grid */}
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
          {/* Left: explanation, impact, fix */}
          <div className="space-y-4">
            {/* Summary / Description */}
            <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="text-sm font-semibold text-slate-900 mb-1.5">
                Summary
              </h2>
              <p className="text-xs text-slate-700 whitespace-pre-line">
                {issue.description ??
                  "No explicit description provided by backend for this issue."}
              </p>
            </section>

            {/* Why it matters */}
            <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="text-sm font-semibold text-slate-900 mb-1.5">
                Why this matters
              </h2>
              <p className="text-xs text-slate-700 whitespace-pre-line">
                {issue.impact ??
                  issue.explanation ??
                  "The backend did not provide a detailed impact explanation. In a production environment, this section should describe risk level, potential exploit paths, and affected environments."}
              </p>
            </section>

            {/* Suggested fix */}
            <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-2">
              <h2 className="text-sm font-semibold text-slate-900 mb-1.5">
                Suggested fix
              </h2>
              <p className="text-xs text-slate-700 whitespace-pre-line">
                {issue.recommended_fix ??
                  "The backend has not returned a concrete remediation message. For live usage, this field should contain the primary recommended fix (e.g., patch version, config change, or policy update)."}
              </p>

              {issue.remediation_steps && (
                <div className="mt-2">
                  <h3 className="text-[11px] font-semibold text-slate-800 mb-1">
                    Step-by-step remediation
                  </h3>
                  <p className="text-xs text-slate-700 whitespace-pre-line">
                    {issue.remediation_steps}
                  </p>
                </div>
              )}
            </section>

            {/* Code snippet / config patch */}
            {issue.code_snippet && (
              <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="text-sm font-semibold text-slate-900 mb-1.5">
                  Example patch / configuration
                </h2>
                <pre className="mt-1 overflow-x-auto rounded-md bg-slate-950 px-3 py-2 text-[11px] leading-relaxed text-slate-100">
                  <code>{issue.code_snippet}</code>
                </pre>
              </section>
            )}
          </div>

          {/* Right: meta / next steps */}
          <aside className="space-y-4">
            <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="text-sm font-semibold text-slate-900 mb-2">
                Issue metadata
              </h2>
              <dl className="space-y-1 text-xs text-slate-700">
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500">ID</dt>
                  <dd className="font-mono text-[11px] text-slate-800">
                    {issue.id}
                  </dd>
                </div>
                {issue.check_type && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-slate-500">Check type</dt>
                    <dd className="font-medium">{issue.check_type}</dd>
                  </div>
                )}
                {issue.source && (
                  <div className="flex justify-between gap-4">
                    <dt className="text-slate-500">Source</dt>
                    <dd className="font-medium">{issue.source}</dd>
                  </div>
                )}
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500">Status</dt>
                  <dd className="font-medium capitalize">
                    {(issue.status ?? "open").toString()}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500">Severity</dt>
                  <dd className="font-medium capitalize">
                    {issue.severity}
                  </dd>
                </div>
              </dl>
            </section>

            <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="text-sm font-semibold text-slate-900 mb-1.5">
                Implementation checklist
              </h2>
              <ul className="list-disc list-inside space-y-1 text-xs text-slate-700">
                <li>
                  Apply the suggested fix in a feature branch or staging
                  environment.
                </li>
                <li>Run unit / integration tests relevant to this area.</li>
                <li>
                  Validate that there are no new warnings in CI or cluster
                  logs.
                </li>
                <li>Promote to production once validated.</li>
              </ul>
            </section>

            <a
              href="/console/issues"
              className="inline-flex w-full items-center justify-center rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-800 hover:bg-slate-50"
            >
              ← Back to all issues
            </a>
          </aside>
        </div>
      </div>
    </div>
  );
}

function normalizeSeverity(raw: any): Severity {
  const v = String(raw ?? "").toLowerCase();
  if (v === "critical") return "critical";
  if (v === "high") return "high";
  if (v === "low") return "low";
  return "medium";
}

function normalizeStatus(raw: any): "open" | "resolved" | "ignored" | string {
  const v = String(raw ?? "").toLowerCase();
  if (v === "resolved" || v === "closed") return "resolved";
  if (v === "ignored" || v === "suppressed") return "ignored";
  return "open";
}

function SeverityBadge({ severity }: { severity: Severity }) {
  const label =
    severity === "critical"
      ? "CRITICAL"
      : severity === "high"
      ? "HIGH"
      : severity === "medium"
      ? "MEDIUM"
      : "LOW";

  const classes =
    severity === "critical"
      ? "bg-red-50 text-red-700 border-red-200"
      : severity === "high"
      ? "bg-amber-50 text-amber-700 border-amber-200"
      : severity === "medium"
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : "bg-slate-50 text-slate-700 border-slate-200";

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${classes}`}
    >
      {label}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const normalized = (status ?? "").toLowerCase();
  let label = "Open";
  let classes = "bg-emerald-50 text-emerald-700 border-emerald-200";

  if (normalized === "resolved" || normalized === "closed") {
    label = "Resolved";
    classes = "bg-slate-50 text-slate-700 border-slate-200";
  } else if (normalized === "ignored" || normalized === "suppressed") {
    label = "Ignored";
    classes = "bg-amber-50 text-amber-700 border-amber-200";
  }

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-medium ${classes}`}
    >
      {label}
    </span>
  );
}
