"use client";

import { useState } from "react";
import { FeatureCard } from "../ui/FeatureCard";
import { ServiceModal } from "../ui/ServiceModal";

export function OutcomeSection() {
    const [modalOpen, setModalOpen] = useState(false);
    const [activeFeature, setActiveFeature] = useState<{ title: string; content: React.ReactNode } | null>(null);

    const openModal = (title: string, content: React.ReactNode) => {
        setActiveFeature({ title, content });
        setModalOpen(true);
    };

    return (
        <section className="bg-slate-950 py-20 border-b border-white/5">
            <div className="mx-auto max-w-7xl px-6">
                <div className="mb-12 text-center">
                    <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                        Platform Outcomes
                    </h2>
                    <p className="mt-4 text-slate-400">
                        Ultimate results from a single, agentic control system.
                    </p>
                </div>

                <div className="grid gap-6 md:grid-cols-3">
                    <FeatureCard
                        title="Automate Compliance"
                        description="Continuous compliance evidence, policy-driven enforcement, and audit-ready trust ledgers."
                        onClick={() => openModal("Automate Compliance", (
                            <div className="space-y-4">
                                <p>TSM99 maps every action to compliance frameworks (SOC2, ISO 27001, HIPAA).</p>
                                <ul className="list-disc pl-5 space-y-2">
                                    <li><strong>Continuous Evidence:</strong> Auto-collect proofs for auditors.</li>
                                    <li><strong>Policy Enforcement:</strong> Prevent drift before it happens.</li>
                                    <li><strong>Trust Ledger:</strong> Cryptographic audit trail of every AI decision.</li>
                                </ul>
                            </div>
                        ))}
                    />

                    <FeatureCard
                        title="Manage Risk"
                        description="Signal correlation, noise suppression, and real-risk prioritization."
                        onClick={() => openModal("Manage Risk", (
                            <div className="space-y-4">
                                <p>Stop chasing false positives. TSM99 correlates signals across your stack.</p>
                                <ul className="list-disc pl-5 space-y-2">
                                    <li><strong>Signal Correlation:</strong> Connects K8s, GitHub, and Cloud logs.</li>
                                    <li><strong>Noise Suppression:</strong> Filters out 99% of non-critical alerts.</li>
                                    <li><strong>Prioritization:</strong> Focuses on what actually threatens your business.</li>
                                </ul>
                            </div>
                        ))}
                    />

                    <FeatureCard
                        title="Prove Trust Continuously"
                        description="Cryptographic audit trail, continuous validation, and verifiable execution."
                        onClick={() => openModal("Prove Trust Continuously", (
                            <div className="space-y-4">
                                <p>Autonomy requires verification. We prove every action.</p>
                                <ul className="list-disc pl-5 space-y-2">
                                    <li><strong>Cryptographic Anchors:</strong> Actions are hashed and immutable.</li>
                                    <li><strong>Continuous Validation:</strong> Every fix is tested immediately.</li>
                                    <li><strong>Verifiable Execution:</strong> Full traceability from intent to commit.</li>
                                </ul>
                            </div>
                        ))}
                    />
                </div>
            </div>

            <ServiceModal
                isOpen={modalOpen}
                closeModal={() => setModalOpen(false)}
                title={activeFeature?.title || ""}
                content={activeFeature?.content}
                ctaLabel="Contact Sales"
                ctaAction={() => window.location.href = "mailto:contact.founder@thesovereignmechanica.ai"}
            />
        </section>
    );
}
