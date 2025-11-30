"use client";

import { useEffect, useState } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

type CheckStatus = "ok" | "warn" | "error" | "unknown";

type Check = {
  id: string;
  name: string;
  kind?: string;
  description?: string;
  enabled?: boolean;
  last_run_at?: string;
  last_status?: CheckStatus;
  last_issues_count?: number;
};

type ChecksResponseShape = {
  items?: any[];
};

export default function ChecksPage() {
  const [checks, setChecks] = useState<Check[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch(`${API_BASE_URL}/platform/checks`, {
          headers: { "Content-Type": "application/json" },
        });

        if (!res.ok) {
          throw new Error(`Backend responded with ${res.status}`);
        }

        const json: ChecksResponseShape | any = await res.json();
        let items: any[] = [];

        if (Array.isArray(json)) {
          items = json;
        } else if (Array.isArray(json?.items)) {
          items = json.items;
        }

        const normalized: Check[] = items.map((it, idx) => ({
          id: String(it.id ?? idx),
          name: String(
            it.name ?? it.display_name ?? "Unnamed check (no name provided)"
          ),
          kind: it.kind ?? it.type ?? undefined,
          description: it.description ?? it.summary ?? undefined,
          enabled: typeof it.enabled === "boolean" ? it.enabled : true,
          last_run_at: it.last_run_at ?? it.lastExecutedAt ?? undefined,
          last_status: normalizeStatus(it.last_status ?? it.status),
          last_issues_count:
            typeof it.last_issues_count === "number"
              ? it.last_issues_count
              : typeof it.issues_count === "number"
              ? it.issues_count
              : undefined,
        }));

        if (!cancelled) {
          setChecks(normalized);
        }
      } catch (e) {
        if (!cancelled) {
          setError("Failed to load checks. Check API URL or backend status.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleRunAll = async () => {
    try {
      setRunning(true);
      setToast(null);
      setError(null);

      const res = await fetch(`${API_BASE_URL}/platform/checks/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!res.ok) {
        throw new Error(`Backend responded with ${res.status}`);
      }

      setToast("Checks triggered successfully. Issues will appear in the console.");
    } catch {
      setError("Failed to trigger checks. Please try again.");
    } finally {
      setRunning(false);
    }
  };

  const handleRunSingle = async (checkId: string) => {
    try {
      setRunning(true);
      setToast(null);
      setError(null);

      const res = await fetch(
        `${API_BASE_URL}/platform/checks/${encodeURIComponent(checkId)}/run`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }
      );

      if (!res.ok) {
        throw new Error(`Backend responded with ${res.status}`);
      }

      setToast(`Check "${checkId}" triggered. Refresh later to see results.`);
    } catch {
      setError("Failed to run this check. Please try again.");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-64px)] bg-gray-50">
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
              Checks
            </h1>
            <p className="mt-1 text-sm text-slate-600 max-w-xl">
              View all automated security and reliability checks. You can run
              everything at once or trigger specific checks manually.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={handleRunAll}
              disabled={running || checks.length === 0}
              className="inline-flex items-center rounded-md bg-emerald-500 px-4 py-2 text-xs font-medium text-slate-950 shadow-sm hover:bg-emerald-400 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {running ? "Running checks…" : "Run all checks"}
            </button>
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

        {/* Loading */}
        {loading && (
          <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
            Loading checks…
          </div>
        )}

        {/* Checks list */}
        {!loading && (
          <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
            {checks.length === 0 ? (
              <div className="px-4 py-6 text-sm text-slate-500">
                No checks were returned by the backend. Once check modules are
                registered and exposed by the API, they will appear here.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {checks.map((check) => (
                  <CheckRow
                    key={check.id}
                    check={check}
                    onRun={() => handleRunSingle(check.id)}
                    running={running}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function CheckRow({
  check,
  onRun,
  running,
}: {
  check: Check;
  onRun: () => void;
  running: boolean;
}) {
  const badgeLabel =
    check.last_status === "ok"
      ? "Healthy"
      : check.last_status === "warn"
      ? "Warnings"
      : check.last_status === "error"
      ? "Failing"
      : "Unknown";

  const badgeClasses =
    check.last_status === "ok"
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : check.last_status === "warn"
      ? "bg-amber-50 text-amber-700 border-amber-200"
      : check.last_status === "error"
      ? "bg-red-50 text-red-700 border-red-200"
      : "bg-slate-50 text-slate-700 border-slate-200";

  return (
    <div className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-sm font-semibold text-slate-900">
            {check.name}
          </h2>
          {check.kind && (
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-600">
              {check.kind}
            </span>
          )}
          {check.enabled === false && (
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600">
              Disabled
            </span>
          )}
        </div>
        {check.description && (
          <p className="text-xs text-slate-600 max-w-xl">
            {check.description}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500">
          <span
            className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 ${badgeClasses}`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-current" />
            {badgeLabel}
          </span>
          {typeof check.last_issues_count === "number" && (
            <span>
              Last run created{" "}
              <span className="font-medium">{check.last_issues_count}</span>{" "}
              issue{check.last_issues_count === 1 ? "" : "s"}
            </span>
          )}
          {check.last_run_at && (
            <span>
              Last run:{" "}
              <span className="font-medium">
                {new Date(check.last_run_at).toLocaleString()}
              </span>
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 self-start sm:self-center">
        <button
          onClick={onRun}
          disabled={running || check.enabled === false}
          className="inline-flex items-center rounded-md border border-slate-300 bg-white px-3 py-1.5 text-[11px] font-medium text-slate-800 hover:bg-slate-50 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {running ? "Running…" : "Run check"}
        </button>
      </div>
    </div>
  );
}

function normalizeStatus(raw: any): CheckStatus {
  const v = String(raw ?? "").toLowerCase();
  if (["ok", "healthy"].includes(v)) return "ok";
  if (["warn", "warning", "degraded"].includes(v)) return "warn";
  if (["error", "fail", "failed"].includes(v)) return "error";
  return "unknown";
}
