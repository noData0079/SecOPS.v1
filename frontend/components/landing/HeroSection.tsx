"use client";

import Link from "next/link";

export function HeroSection() {
    return (
        <section className="relative overflow-hidden border-b border-white/10 bg-slate-950 pt-24 pb-16 md:pt-32 md:pb-24">
            {/* Background Gradient */}
            <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950" />
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-emerald-900/20 via-slate-950/0 to-transparent" />

            <div className="relative z-10 mx-auto max-w-7xl px-6 text-center">
                <h1 className="text-4xl font-bold tracking-tight text-white sm:text-6xl mb-6">
                    Policy-Governed <span className="text-emerald-500">Autonomy</span>
                </h1>
                <p className="mt-6 text-lg leading-8 text-slate-400 max-w-2xl mx-auto">
                    The first autonomous security platform you can actually trust.
                    Governed by human oversight. Enforced by policy. Auditable by design.
                </p>

                <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
                    <Link
                        href="/access"
                        className="rounded-full bg-slate-100 px-8 py-3.5 text-sm font-semibold text-slate-900 transition hover:bg-white hover:shadow-[0_0_20px_rgba(255,255,255,0.3)]"
                    >
                        Request Access
                    </Link>
                    <Link
                        href="/demo"
                        className="rounded-full border border-emerald-500/50 bg-emerald-500/10 px-8 py-3.5 text-sm font-semibold text-emerald-400 backdrop-blur-sm transition hover:bg-emerald-500/20 hover:border-emerald-500"
                    >
                        Try Live Demo
                    </Link>
                </div>
            </div>
        </section>
    );
}
