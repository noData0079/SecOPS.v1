"use client";

function FlowStep({ label, isLast = false }: { label: string; isLast?: boolean }) {
    return (
        <div className="flex items-center">
            <div className="flex flex-col items-center gap-2">
                <div className="flex h-12 w-12 items-center justify-center rounded-full border border-emerald-500/50 bg-emerald-500/10 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                    <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                </div>
                <span className="text-sm font-semibold text-slate-300">{label}</span>
            </div>
            {!isLast && (
                <div className="mx-4 h-[1px] w-12 bg-gradient-to-r from-emerald-500/50 to-transparent md:w-24" />
            )}
        </div>
    );
}

export function ClosedLoopSection() {
    return (
        <section className="bg-slate-950 py-24 border-b border-white/5">
            <div className="mx-auto max-w-7xl px-6 text-center">
                <div className="mb-16 flex flex-wrap justify-center gap-4 md:gap-0">
                    <FlowStep label="Detection" />
                    <FlowStep label="Reasoning" />
                    <FlowStep label="Action" />
                    <FlowStep label="Validation" isLast />
                </div>

                <h3 className="text-xl font-medium tracking-wide text-white">Closed-loop. Always on.</h3>

                <div className="mt-8 flex flex-wrap justify-center gap-3">
                    {["Model-driven", "Context-aware", "Workflow-native", "Agentic by design"].map((tag) => (
                        <span
                            key={tag}
                            className="rounded-full border border-slate-700 bg-slate-900 px-4 py-1.5 text-xs text-slate-400"
                        >
                            {tag}
                        </span>
                    ))}
                </div>
            </div>
        </section>
    );
}
