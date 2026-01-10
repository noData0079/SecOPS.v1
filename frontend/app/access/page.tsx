"use client";

import { useState } from "react";

export default function AccessPage() {
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitted(true);
        // Logic to email contact.founder@thesovereignmechanica.ai would go here (or via generic backend endpoint)
    };

    if (submitted) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-white p-6 text-center">
                <div className="h-16 w-16 rounded-full bg-emerald-500/20 flex items-center justify-center mb-6">
                    <svg className="h-8 w-8 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                </div>
                <h1 className="text-3xl font-bold mb-2">Request Received</h1>
                <p className="text-slate-400 max-w-md">
                    Thank you for your interest in The Sovereign Mechanica. Our team searches for high-impact partners. We will review your profile and reach out shortly.
                </p>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 flex items-center justify-center p-6">
            <div className="w-full max-w-lg">
                <div className="text-center mb-10">
                    <h1 className="text-3xl font-bold text-white">Request Enterprise Access</h1>
                    <p className="mt-2 text-slate-400">Join the waiting list for our Tier 1 Foundation pilot.</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6 bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-xl">
                    <div className="grid gap-6 md:grid-cols-2">
                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-1">First Name</label>
                            <input required className="w-full rounded bg-slate-800 border border-slate-700 px-3 py-2 text-white focus:border-emerald-500 focus:outline-none" />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-1">Last Name</label>
                            <input required className="w-full rounded bg-slate-800 border border-slate-700 px-3 py-2 text-white focus:border-emerald-500 focus:outline-none" />
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">Work Email</label>
                        <input required type="email" className="w-full rounded bg-slate-800 border border-slate-700 px-3 py-2 text-white focus:border-emerald-500 focus:outline-none" />
                    </div>

                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">Company</label>
                        <input required className="w-full rounded bg-slate-800 border border-slate-700 px-3 py-2 text-white focus:border-emerald-500 focus:outline-none" />
                    </div>

                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">Primary Use Case</label>
                        <select className="w-full rounded bg-slate-800 border border-slate-700 px-3 py-2 text-white focus:border-emerald-500 focus:outline-none">
                            <option>Automated Compliance</option>
                            <option>Autonomous SOC/Security</option>
                            <option>DevOps & Infrastructure</option>
                            <option>AI Agent Governance</option>
                        </select>
                    </div>

                    <button type="submit" className="w-full rounded bg-emerald-600 py-3 font-semibold text-white hover:bg-emerald-500 transition shadow-lg shadow-emerald-500/20">
                        Request Access
                    </button>
                </form>
            </div>
        </div>
    );
}
