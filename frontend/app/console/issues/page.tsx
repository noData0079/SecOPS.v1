"use client";

import { useEffect, useMemo, useState } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

type Severity = "critical" | "high" | "medium" | "low";

type Issue = {
  id: string;
  title: string;
  severity: Severity;
  source: string;
  status?: "open" | "resolved" | "ignored" | string;
  created_at?: string;
  updated_at?: string;
};

type IssuesResponseShape = {
  items?: any[];
  total?: number;
};

const SEVERITY_OPTIONS: { label: string; value: Severity | "all" }[] = [
  { label: "All severities", value: "all" },
  { label: "Critical", value: "critical" },
  { label: "High", value: "high" },
  { label: "Medium", value: "medium" },
  { label: "Low", value: "low" },
];

const STATUS_OPTIONS: { label: string; value: string }[] = [
  { label: "All statuses", value: "all" },
  { label: "Open", value: "open" },
  { label: "Resolved", value: "resolved" },
  { label: "Ignored", value: "ignored" },
];

export default function IssuesListPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [query, setQuery] = useState("");
  const [severityFilter, setSeverityFilter] = useState<Severity | "all">("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sourceFilter, setSourceFilter] = useState<string>("all");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        const url = new URL(`${API_BASE_URL}/platform/issues`);
        // Filters are optional – backend can choose to ignore them
        if (severityFilter !== "all") {
          url.searchParams.set("severity", severityFilter);
        }
        if (statusFilter !== "all") {
          url.searchParams.set("status", statusFilter);
        }
        if (sourceFilter !== "all") {
          url.searchParams.set("source", sourceFilter);
        }
        if (query.trim()) {
          url.searchParams.set("q", query.trim());
        }

        const res = await fetch(url.toString(), {
          headers: { "Content-Type": "application/json" },
        });

        if (!res.ok) {
          throw new Error(`Backend responded with ${res.status}`);
        }

        const json: IssuesResponseShape | any = await res.json();

        let items: any[] = [];
        if (Array.isArray(json)) {
          items = json;
        } else if (Array.isArray(json?.items)) {
          items = json.items;
        }

        const normalized: Issue[] = items.map((it, i) => ({
          id: String(it.id ?? i),
          title: String(
            it.title ?? "Unlabeled issue (title not provided by backend)"
          ),
          severity: normalizeSeverity(it.severity),
          source: String(it.source ?? "Unknown"),
          status: normalizeStatus(it.status),
          created_at: it.created_at,
          updated_at: it.updated_at,
        }));

        if (!cancelled) {
          setIssues(normalized);
        }
      } catch (e) {
        if (!cancelled) {
          setError("Failed to load issues. Check API URL or backend status.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
    // we reload when filters/search change
  }, [query, severityFilter, statusFilter, sourceFilter]);

  const stats = useMemo(
    () => computeStats(issues),
    [issues]
  );

  const uniqueSources = useMemo(() => {
    const set = new Set<string>();
    for (const issue of issues) {
      if (issue.source) set.add(issue.source);
    }
    return Array.from(set);
  }, [issues]);

  return (
    <div className="min-h-[calc(100vh-64px)] bg-gray-50">
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
              Issues
            </h1>
            <p className="mt-1 text-sm text-slate-600 max-w-xl">
              All issues detected across repositories, CI pipelines, and clusters. 
              Filter by severity, status, or source to focus on what matters most.
            </p>
          </div>

          <div className="text-xs text-slate-500">
            <span className="font-medium">{issues.length}</span> issues loaded
          </div>
        </div>

        {/* Filters */}
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-3">
          <div className="grid gap-3 md:grid-cols-[2fr_1fr_1fr_1fr] items-end">
            <div>
              <label className="block text-[11px] font-medium text-slate-600 mb-1">
                Search
              </label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search by title, source, or description..."
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-600 mb-1">
                Severity
              </label>
              <select
                value={severityFilter}
                onChange={(e) =>
                  setSeverityFilter(e.target.value as Severity | "all")
                }
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              >
                {SEVERITY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-600 mb-1">
                Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              >
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-600 mb-1">
                Source
              </label>
              <select
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
                className="w-full rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              >
                <option value="all">All sources</option>
                {uniqueSources.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Summary stats */}
          <div className="flex flex-wrap gap-3 text-[11px] text-slate-600">
            <StatPill label="Critical" value={stats.critical} tone="critical" />
            <StatPill label="High" value={stats.high} tone="high" />
            <StatPill label="Medium" value={stats.medium} tone="medium" />
            <StatPill label="Low" value={stats.low} tone="low" />
            <StatPill
              label="Open"
              value={stats.open}
              tone="neutral"
            />
            <StatPill
              label="Resolved"
              value={stats.resolved}
              tone="neutral"
            />
          </div>
        </div>

        {/* Loading/Error */}
        {loading && (
          <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
            Loading issues…
          </div>
        )}

        {error && !loading && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Issues table */}
        {!loading && !error && (
          <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
            {issues.length === 0 ? (
              <div className="px-4 py-6 text-sm text-slate-500">
                No issues found for the selected filters. Once your integrations
                are configured and checks have run, issues will be listed here.
              </div>
            ) : (
              <IssuesTable issues={issues} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function IssuesTable({ issues }: { issues: Issue[] }) {
  return (
    <div className="overflow-x-auto text-xs">
      <table className="min-w-full divide-y divide-slate-100">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-slate-600">
              Severity
            </th>
            <th className="px-4 py-2 text-left font-medium text-slate-600">
              Title
            </th>
            <th className="px-4 py-2 text-left font-medium text-slate-600">
              Source
            </th>
            <th className="px-4 py-2 text-left font-medium text-slate-600">
              Status
            </th>
            <th className="px-4 py-2 text-left font-medium text-slate-600">
              Created
            </th>
            <th className="px-4 py-2 text-left font-medium text-slate-600" />
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {issues.map((issue) => (
            <tr key={issue.id} className="hover:bg-slate-50">
              <td className="px-4 py-2">
                <SeverityBadge severity={issue.severity} />
              </td>
              <td className="px-4 py-2 max-w-[280px]">
                <div className="truncate text-slate-900">{issue.title}</div>
              </td>
              <td className="px-4 py-2">
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-700">
                  {issue.source}
                </span>
              </td>
              <td className="px-4 py-2">
                <StatusBadge status={issue.status ?? "open"} />
              </td>
              <td className="px-4 py-2 text-[11px] text-slate-500">
                {issue.created_at
                  ? new Date(issue.created_at).toLocaleString()
                  : "—"}
              </td>
              <td className="px-4 py-2 text-right">
                <a
                  href={`/console/issues/${encodeURIComponent(issue.id)}`}
                  className="text-[11px] font-medium text-blue-600 hover:underline"
                >
                  View
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
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
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${classes}`}
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
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-medium ${classes}`}
    >
      {label}
    </span>
  );
}

type Stats = {
  critical: number;
  high: number;
  medium: number;
  low: number;
  open: number;
  resolved: number;
};

function computeStats(issues: Issue[]): Stats {
  return issues.reduce<Stats>(
    (acc, issue) => {
      acc[issue.severity] += 1;
      const s = (issue.status ?? "open").toLowerCase();
      if (s === "resolved" || s === "closed") acc.resolved += 1;
      else acc.open += 1;
      return acc;
    },
    {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      open: 0,
      resolved: 0,
    }
  );
}

type StatPillProps = {
  label: string;
  value: number;
  tone: "critical" | "high" | "medium" | "low" | "neutral";
};

function StatPill({ label, value, tone }: StatPillProps) {
  const toneClasses =
    tone === "critical"
      ? "bg-red-50 text-red-700 border-red-200"
      : tone === "high"
      ? "bg-amber-50 text-amber-700 border-amber-200"
      : tone === "medium"
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : tone === "low"
      ? "bg-slate-50 text-slate-700 border-slate-200"
      : "bg-slate-50 text-slate-600 border-slate-200";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 ${toneClasses}`}
    >
      <span className="text-[11px]">{label}</span>
      <span className="text-[11px] font-semibold">{value}</span>
    </span>
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
