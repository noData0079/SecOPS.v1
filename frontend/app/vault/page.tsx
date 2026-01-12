"use client";

import React, { useState, useEffect } from 'react';
import { VaultStatus } from '../../components/vault/VaultStatus';
import { SovereignReport } from '../../components/vault/SovereignReport';
import { ShutterTransition } from '../../components/vault/ShutterTransition';

export default function SovereignVaultPage() {
    const [isLoaded, setIsLoaded] = useState(false);

    // Mock data for the report
    const auditData = {
        evolutions: [
            { id: "1", timestamp: "2024-05-10 09:00:00", axiom_summary: "Generated Axiom: BLOCK_TOR_EXIT_NODES" },
            { id: "2", timestamp: "2024-05-10 10:15:00", axiom_summary: "Optimized Policy: REDUCE_LOG_RETENTION" },
            { id: "3", timestamp: "2024-05-10 11:30:00", axiom_summary: "Enforced Rule: NO_ROOT_LOGIN" },
        ]
    };

    useEffect(() => {
        // Simulate loading delay for transition
        setTimeout(() => setIsLoaded(true), 500);
    }, []);

    return (
        <div className="min-h-screen bg-[#050505] text-white overflow-hidden relative font-mono">
            <ShutterTransition isChanging={!isLoaded} />

            <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10 pointer-events-none"></div>

            <main className="relative z-10 container mx-auto px-4 py-8">
                <header className="flex justify-between items-center mb-12">
                    <div>
                        <h1 className="text-4xl font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-600">
                            SOVEREIGN VAULT
                        </h1>
                        <p className="text-cyan-500/60 text-sm mt-2">SECURE ENCLAVE // ZERO-KNOWLEDGE PROOF</p>
                    </div>
                    <VaultStatus trustScore={100} />
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left Column: Visualizer Placeholder */}
                    <div className="lg:col-span-1 space-y-8">
                        <div className="border border-cyan-900/50 bg-black/40 rounded-xl p-6 h-[400px] relative overflow-hidden group">
                            <div className="absolute inset-0 bg-gradient-to-b from-transparent to-cyan-900/10 pointer-events-none" />
                            <h3 className="text-cyan-400 text-sm uppercase mb-4 tracking-widest border-b border-cyan-900/50 pb-2">
                                Live Enclave State
                            </h3>
                            <div className="flex items-center justify-center h-full">
                                {/* 3D Cube Placeholder */}
                                <div className="w-32 h-32 border-2 border-cyan-500 animate-spin-slow relative">
                                    <div className="absolute inset-0 bg-cyan-500/10 blur-xl"></div>
                                    <div className="absolute top-1/2 left-1/2 w-16 h-16 bg-cyan-400/20 -translate-x-1/2 -translate-y-1/2"></div>
                                </div>
                            </div>
                            <div className="absolute bottom-4 left-6 text-xs text-cyan-600">
                                MEMORY_USAGE: 0.00KB (LEAK_PROOF)
                            </div>
                        </div>

                        <div className="p-4 border border-cyan-900/30 rounded-lg bg-black/60">
                            <h4 className="text-cyan-500 text-xs uppercase mb-2">Active Hard Rules</h4>
                            <ul className="space-y-1 text-xs text-gray-400 font-mono">
                                <li className="flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span> NO_LOG
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span> NO_TRAIN
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span> NO_EGRESS
                                </li>
                            </ul>
                        </div>
                    </div>

                    {/* Right Column: Transparency Report */}
                    <div className="lg:col-span-2">
                         <SovereignReport auditData={auditData} />

                         <div className="mt-8 grid grid-cols-2 gap-4">
                            <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-lg">
                                <div className="text-slate-400 text-xs uppercase mb-1">Privacy Score</div>
                                <div className="text-3xl font-bold text-white">100%</div>
                                <div className="text-emerald-500 text-xs mt-1">ALL PII MASKED</div>
                            </div>
                            <div className="bg-slate-900/50 border border-slate-800 p-4 rounded-lg">
                                <div className="text-slate-400 text-xs uppercase mb-1">Data Leaked</div>
                                <div className="text-3xl font-bold text-white">0 KB</div>
                                <div className="text-emerald-500 text-xs mt-1">TO TRAINING CORE</div>
                            </div>
                         </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
