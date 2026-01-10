"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeftIcon, CloudArrowUpIcon, cpuIcon, LockClosedIcon } from "@heroicons/react/24/outline";

export default function DemoPage() {
    const [tokensUsed, setTokensUsed] = useState(1240);
    const TOKEN_LIMIT = 50000;
    const [file, setFile] = useState<File | null>(null);
    const [error, setError] = useState("");
    const [analysis, setAnalysis] = useState<string | null>(null);

    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (!selectedFile) return;

        // CLIENT-SIDE GUARD: 200KB
        if (selectedFile.size > 200 * 1024) {
            setError("Demo restriction: File size must be under 200KB.");
            return;
        }

        setFile(selectedFile);
        setError("");
        // Simulate immediate analysis for demo feel
        setTimeout(() => {
            setAnalysis("Scanning complete. Risk detected: HIGH.");
            setTokensUsed(prev => prev + 450);
        }, 1500);
    };

    const percentage = Math.min((tokensUsed / TOKEN_LIMIT) * 100, 100);

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 font-sans">
            {/* Disclaimer Banner */}
            <div className="bg-amber-900/20 border-b border-amber-500/20 px-4 py-2 text-center text-xs font-medium text-amber-500">
                ⚠️ DEMO MODE: Actions are simulated. Execution is disabled. Session resets in 60m.
            </div>

            {/* Demo Navbar */}
            <header className="flex items-center justify-between border-b border-white/5 bg-slate-900 px-6 py-4">
                <div className="flex items-center gap-4">
                    <Link href="/" className="text-slate-400 hover:text-white transition">
                        <ArrowLeftIcon className="h-5 w-5" />
                    </Link>
                    <span className="font-semibold text-white">TSM99 Demo Workspace</span>
                </div>

                {/* Token Meter */}
                <div className="flex items-center gap-3">
                    <div className="text-xs text-slate-400">Session Usage:</div>
                    <div className="h-2 w-32 rounded-full bg-slate-800 overflow-hidden">
                        <div
                            className="h-full bg-emerald-500 transition-all duration-500"
                            style={{ width: `${percentage}%` }}
                        />
                    </div>
                    <div className="text-xs font-mono text-emerald-400">{tokensUsed.toLocaleString()} / {TOKEN_LIMIT.toLocaleString()}</div>
                </div>
            </header>

            <main className="mx-auto max-w-5xl px-6 py-8 grid gap-8 lg:grid-cols-[1fr_300px]">

                {/* Left Column: Workspace */}
                <div className="space-y-6">

                    {/* 1. Ingest Panel */}
                    <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6">
                        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <CloudArrowUpIcon className="h-5 w-5 text-emerald-500" />
                            Signal Ingestion
                        </h2>
                        <div className="border-2 border-dashed border-slate-700 rounded-lg p-8 text-center hover:bg-slate-800/50 transition">
                            <input
                                type="file"
                                className="hidden"
                                id="fileUpload"
                                onChange={handleFileUpload}
                            />
                            <label htmlFor="fileUpload" className="cursor-pointer">
                                <div className="mx-auto h-12 w-12 text-slate-500 mb-2">
                                    <svg className="w-full h-full" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                    </svg>
                                </div>
                                <p className="text-sm text-slate-300 font-medium">Click to upload config or log file</p>
                                <p className="text-xs text-slate-500 mt-1">Max 200KB (Restricted for Demo)</p>
                            </label>
                        </div>
                        {error && <p className="mt-3 text-xs text-red-400">{error}</p>}
                        {file && (
                            <div className="mt-4 flex items-center justify-between bg-emerald-900/10 border border-emerald-500/20 rounded px-4 py-2 text-sm text-emerald-300">
                                <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
                                <span>Ready for reasoning</span>
                            </div>
                        )}
                    </section>

                    {/* 2. Reasoning View */}
                    <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 min-h-[300px]">
                        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            Reasoning Engine
                        </h2>
                        {analysis ? (
                            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-500">
                                <div className="p-4 rounded bg-slate-950 border-l-4 border-amber-500">
                                    <h3 className="text-amber-400 font-medium text-sm">Potential Misconfiguration Detected</h3>
                                    <p className="text-slate-400 text-xs mt-1">Analysis of uploaded file indicates a high-severity security gap in ingress controller configuration.</p>
                                </div>
                                <div className="text-xs font-mono text-slate-500">
                                    Thinking pass 1... OK<br />
                                    Correlating with CVE database... MATCH (CVE-2024-XXXX)<br />
                                    Checking policy constraints... VIOLATION<br />
                                </div>
                            </div>
                        ) : (
                            <div className="h-full flex items-center justify-center text-slate-600 text-sm">
                                Waiting for input signal...
                            </div>
                        )}
                    </section>

                    {/* 3. Proposed Fix (Read Only) */}
                    <section className="rounded-xl border border-slate-800 bg-slate-900/50 p-6 opacity-75">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-white">Proposed Remediation</h2>
                            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 border border-slate-700 px-2 py-0.5 rounded">Read-Only</span>
                        </div>
                        <div className="bg-black p-4 rounded font-mono text-xs text-slate-300 overflow-x-auto">
                            {`- apiVersion: networking.k8s.io/v1
- kind: Ingress
- metadata:
-   annotations:
-     kubernetes.io/ingress.class: nginx
+ apiVersion: networking.k8s.io/v1
+ kind: Ingress
+ metadata:
+   annotations:
+     kubernetes.io/ingress.class: nginx
+     nginx.ingress.kubernetes.io/auth-type: basic`}
                        </div>
                        <div className="mt-4 flex gap-4">
                            <button disabled className="flex-1 rounded bg-slate-800 py-2 text-sm font-medium text-slate-500 cursor-not-allowed flex items-center justify-center gap-2">
                                <LockClosedIcon className="h-4 w-4" />
                                Auto-Fix Disabled (Demo)
                            </button>
                        </div>
                    </section>

                </div>

                {/* Right Column: Trust Ledger Preview */}
                <aside className="space-y-6">
                    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
                        <h3 className="text-sm font-semibold text-white mb-3">Live Trust Ledger</h3>
                        <div className="space-y-3">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="flex gap-3 text-xs">
                                    <div className="mt-1 h-2 w-2 rounded-full bg-emerald-500" />
                                    <div>
                                        <div className="text-slate-300">Policy Check Passed</div>
                                        <div className="text-slate-600 font-mono text-[10px]">hash: 0x7f...3a</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="rounded-xl bg-gradient-to-br from-emerald-900/20 to-slate-900 border border-emerald-500/20 p-4">
                        <h3 className="text-sm font-semibold text-emerald-400 mb-2">Upgrade to Enterprise</h3>
                        <p className="text-xs text-slate-400 mb-4">Unlock full autonomous execution and unlimited reasoning.</p>
                        <button className="w-full rounded bg-emerald-600 py-2 text-xs font-semibold text-white hover:bg-emerald-500">
                            Request Access
                        </button>
                    </div>
                </aside>

            </main>
        </div>
    );
}
