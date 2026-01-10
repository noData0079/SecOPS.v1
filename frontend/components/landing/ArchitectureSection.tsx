"use client";

export function ArchitectureSection() {
    return (
        <section className="bg-slate-900 py-24">
            <div className="mx-auto max-w-7xl px-6">
                <div className="grid gap-12 lg:grid-cols-2 items-center">
                    <div>
                        <h2 className="text-3xl font-bold text-white mb-6">Built on Sovereign Architecture</h2>
                        <div className="space-y-8">
                            <div className="border-l-2 border-emerald-500/30 pl-6">
                                <h4 className="text-lg font-semibold text-emerald-400">Poly-LLM Reasoning</h4>
                                <p className="mt-2 text-slate-400 text-sm">
                                    Dynamic orchestration of GPT-4, Claude, and local specialized models for maximum accuracy and cost efficiency.
                                </p>
                            </div>
                            <div className="border-l-2 border-emerald-500/30 pl-6">
                                <h4 className="text-lg font-semibold text-emerald-400">Context Stitching</h4>
                                <p className="mt-2 text-slate-400 text-sm">
                                    Unified graph memory across GitHub, Kubernetes, and Cloud Logs to understand the "why" behind every signal.
                                </p>
                            </div>
                            <div className="border-l-2 border-emerald-500/30 pl-6">
                                <h4 className="text-lg font-semibold text-emerald-400">Continuous Verification</h4>
                                <p className="mt-2 text-slate-400 text-sm">
                                    Every action is validated against policy constraints and functional tests before commit.
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="relative rounded-2xl border border-white/10 bg-slate-950 p-8 shadow-2xl">
                        <div className="absolute top-0 right-0 p-4">
                            <span className="text-xs text-slate-600 font-mono">Architecture V1</span>
                        </div>
                        <pre className="text-xs font-mono text-emerald-500/80 leading-relaxed overflow-x-auto">
                            {`[Ingest] --> [Normalize] --> [Vector Store]
                                  |
                                  v
                            [Reasoning Engine]
                           /        |         \\
                  [Planner]    [Executor]    [Critic]
                      |             |            |
                  [Plan]  -->   [Action] --> [Verify]
                                    |
                                    v
                              [Trust Ledger]`}
                        </pre>
                    </div>
                </div>
            </div>
        </section>
    );
}
