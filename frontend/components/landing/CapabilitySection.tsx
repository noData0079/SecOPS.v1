"use client";

import { useState } from "react";
import { FeatureCard } from "../ui/FeatureCard";
import { ServiceModal } from "../ui/ServiceModal";

export function CapabilitySection() {
    const [modalOpen, setModalOpen] = useState(false);
    const [activeCap, setActiveCap] = useState<{ title: string; content: React.ReactNode } | null>(null);

    const openModal = (title: string, content: React.ReactNode) => {
        setActiveCap({ title, content });
        setModalOpen(true);
    };

    return (
        <section className="bg-slate-950 py-20 border-b border-white/5">
            <div className="mx-auto max-w-7xl px-6">
                <div className="mb-12 text-center">
                    <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
                        Autonomous Capabilities
                    </h2>
                    <p className="mt-4 text-slate-400">
                        What the platform actually does.
                    </p>
                </div>

                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
                    <FeatureCard
                        title="Autonomous Security"
                        description="End-to-end detection, reasoning, and remediation."
                        onClick={() => openModal("Autonomous Security", (
                            <p>Full lifecycle security operations: Identify vulnerability -> Propose Fix -> Verify -> Commit.</p>
                        ))}
                    />
                    <FeatureCard
                        title="Autonomous DevOps"
                        description="Self-healing infrastructure and drift correction."
                        onClick={() => openModal("Autonomous DevOps", (
                            <p>Infrastructure as Code (IaC) drift detection and automatic reconciliation.</p>
                        ))}
                    />
                    <FeatureCard
                        title="AI Tools & Agents"
                        description="Manage, govern, and orchestrate third-party agents."
                        onClick={() => openModal("Autonomous AI Management", (
                            <p>Centralized governance plane for all your internal and external AI agents.</p>
                        ))}
                    />
                    <FeatureCard
                        title="Tech Ops"
                        description="Automate routine maintenance and operational tasks."
                        onClick={() => openModal("Automate Tech Ops", (
                            <p>Pattern-based scaling, log rotation, and database optimization tasks handled on autopilot.</p>
                        ))}
                    />
                </div>
            </div>

            <ServiceModal
                isOpen={modalOpen}
                closeModal={() => setModalOpen(false)}
                title={activeCap?.title || ""}
                content={activeCap?.content}
                ctaLabel="Contact Sales"
                ctaAction={() => window.location.href = "mailto:contact.founder@thesovereignmechanica.ai"}
            />
        </section>
    );
}
