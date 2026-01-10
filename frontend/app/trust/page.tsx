"use client";

export default function TrustLedgerPage() {
    return (
        <div className="min-h-screen bg-slate-950 text-slate-200">
            <header className="border-b border-white/5 bg-slate-900 px-6 py-8">
                <div className="mx-auto max-w-7xl">
                    <h1 className="text-3xl font-bold text-white">Trust Ledger</h1>
                    <p className="mt-2 text-slate-400">Cryptographically verifiable audit trail of all autonomous actions.</p>
                </div>
            </header>

            <main className="mx-auto max-w-7xl px-6 py-12">
                <div className="rounded-xl border border-slate-800 bg-slate-900 overflow-hidden">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-slate-950 text-slate-400">
                            <tr>
                                <th className="px-6 py-4 font-medium">Timestamp</th>
                                <th className="px-6 py-4 font-medium">Actor</th>
                                <th className="px-6 py-4 font-medium">Action</th>
                                <th className="px-6 py-4 font-medium">Status</th>
                                <th className="px-6 py-4 font-medium">Hash</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800 text-slate-300">
                            <tr className="hover:bg-slate-800/50 transition">
                                <td className="px-6 py-4 font-mono text-xs text-slate-500">2026-01-10 14:32:05</td>
                                <td className="px-6 py-4">
                                    <span className="inline-flex items-center gap-1.5 rounded bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/20">
                                        Agent-01 (Security)
                                    </span>
                                </td>
                                <td className="px-6 py-4">Auto-remediate Ingress misconfiguration</td>
                                <td className="px-6 py-4 text-emerald-400">Verified</td>
                                <td className="px-6 py-4 font-mono text-xs text-slate-600">0x8f2a...9b1c</td>
                            </tr>
                            <tr className="hover:bg-slate-800/50 transition">
                                <td className="px-6 py-4 font-mono text-xs text-slate-500">2026-01-10 14:30:12</td>
                                <td className="px-6 py-4">
                                    <span className="inline-flex items-center gap-1.5 rounded bg-blue-500/10 px-2 py-0.5 text-xs font-medium text-blue-400 border border-blue-500/20">
                                        Policy Engine
                                    </span>
                                </td>
                                <td className="px-6 py-4">Block Pull Request #422 (High Risk)</td>
                                <td className="px-6 py-4 text-emerald-400">Enforced</td>
                                <td className="px-6 py-4 font-mono text-xs text-slate-600">0x3c1d...e4f2</td>
                            </tr>
                            <tr className="hover:bg-slate-800/50 transition">
                                <td className="px-6 py-4 font-mono text-xs text-slate-500">2026-01-10 14:15:00</td>
                                <td className="px-6 py-4">
                                    <span className="inline-flex items-center gap-1.5 rounded bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-400 border border-amber-500/20">
                                        Agent-02 (DevOps)
                                    </span>
                                </td>
                                <td className="px-6 py-4">Scale up replica set (CPU {'>'} 80%)</td>
                                <td className="px-6 py-4 text-slate-400">Pending Approval</td>
                                <td className="px-6 py-4 font-mono text-xs text-slate-600">0xa1b2...c3d4</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </main>
        </div>
    );
}
