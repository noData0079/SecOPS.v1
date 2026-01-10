"use client";

import { ArchitectureSection } from "@/components/landing/ArchitectureSection";

export default function PlatformPage() {
    return (
        <div className="min-h-screen bg-slate-950 text-white">
            <header className="py-20 text-center px-6">
                <h1 className="text-4xl font-bold tracking-tight md:text-6xl">Sovereign Architecture</h1>
                <p className="mt-6 text-xl text-slate-400 max-w-2xl mx-auto">
                    Built from the ground up to prevent the "Black Box" problem of autonomous AI.
                </p>
            </header>

            <ArchitectureSection />

            <section className="mx-auto max-w-4xl px-6 py-20 text-center">
                <h2 className="text-2xl font-bold mb-6">Why Sovereignty Matters</h2>
                <p className="text-slate-400 leading-relaxed">
                    As AI agents become autonomous, they must be accountable. TSM99 implements a dual-layer controls system:
                    <br /><br />
                    1. <strong>Deterministic Policy Layer:</strong> Hard constraints that AI cannot override.<br />
                    2. <strong>Probabilistic Reasoning Layer:</strong> LLM-driven intelligence for novel situations.
                    <br /><br />
                    This ensures that while the AI can "think" creatively, it can only "act" compliantly.
                </p>
            </section>
        </div>
    );
}
