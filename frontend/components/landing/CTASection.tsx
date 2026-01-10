"use client";

import Link from "next/link";

export function CTASection() {
    return (
        <section className="bg-slate-950 py-24 border-t border-white/10">
            <div className="mx-auto max-w-4xl text-center px-6">
                <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                    Ready to govern your autonomy?
                </h2>
                <p className="mt-4 text-slate-400 text-lg">
                    Start with a controlled pilot. Scale to full sovereignty.
                </p>

                <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
                    <Link
                        href="/access"
                        className="rounded-full bg-white px-8 py-3.5 text-sm font-semibold text-slate-950 transition hover:bg-slate-200"
                    >
                        Request Enterprise Access
                    </Link>
                    <Link
                        href="/demo"
                        className="rounded-full border border-slate-700 bg-transparent px-8 py-3.5 text-sm font-semibold text-white transition hover:bg-slate-800"
                    >
                        Try Live Demo
                    </Link>
                </div>
                <p className="mt-8 text-xs text-slate-600">
                    Enterprise-grade security • SOC2 Ready • Self-hosted options available
                </p>
            </div>
        </section>
    );
}
