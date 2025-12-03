const auditLogs = Array.from({ length: 12 }).map((_, idx) => ({
  id: `audit-${idx + 1}`,
  actor: idx % 2 === 0 ? "system" : "founder@secops.ai",
  action: idx % 2 === 0 ? "policy.update" : "scan.run",
  target: `service-${idx + 1}`,
  createdAt: new Date(Date.now() - idx * 5 * 60 * 1000).toISOString(),
}));

export default function AuditLogsPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 px-6 py-16">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold">Audit Logs</h1>
        <p className="text-slate-300 mt-2 mb-6 max-w-3xl">
          SOC2-friendly audit history showing every admin action, agent remediation, and policy update.
        </p>

        <div className="rounded-xl border border-slate-800 bg-slate-900 divide-y divide-slate-800">
          {auditLogs.map((entry) => (
            <div key={entry.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <p className="font-medium">{entry.action}</p>
                <p className="text-slate-400 text-sm">
                  {entry.actor} on {entry.target}
                </p>
              </div>
              <span className="text-xs text-slate-400">{new Date(entry.createdAt).toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
