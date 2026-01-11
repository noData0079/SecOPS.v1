'use client';

import React, { useState } from 'react';

interface PolicyConfidence {
    policyId: string;
    ruleType: string;
    description: string;
    confidence: number;
    timesApplied: number;
    effectiveness: number;
    isBrittle: boolean;
    lastApplied: string;
}

export default function PolicyConfidenceDashboard() {
    const [policies] = useState<PolicyConfidence[]>([
        { policyId: 'risk_high_block', ruleType: 'risk_gate', description: 'Block high-risk actions in production', confidence: 0.92, timesApplied: 156, effectiveness: 0.94, isBrittle: false, lastApplied: '5m ago' },
        { policyId: 'action_limit_3', ruleType: 'action_limit', description: 'Max 3 actions per incident', confidence: 0.78, timesApplied: 89, effectiveness: 0.82, isBrittle: false, lastApplied: '15m ago' },
        { policyId: 'env_prod_escalate', ruleType: 'environment', description: 'Escalate deploy actions in prod', confidence: 0.65, timesApplied: 34, effectiveness: 0.71, isBrittle: true, lastApplied: '1h ago' },
        { policyId: 'tool_patch_review', ruleType: 'tool_gate', description: 'Apply patches require review', confidence: 0.88, timesApplied: 22, effectiveness: 0.91, isBrittle: false, lastApplied: '2h ago' },
        { policyId: 'time_freeze_block', ruleType: 'time_gate', description: 'Block changes during freeze', confidence: 0.45, timesApplied: 8, effectiveness: 0.50, isBrittle: true, lastApplied: '5d ago' },
    ]);

    const [showBrittleOnly, setShowBrittleOnly] = useState(false);

    const filteredPolicies = showBrittleOnly
        ? policies.filter(p => p.isBrittle)
        : policies;

    const getConfidenceColor = (conf: number) => {
        if (conf >= 0.8) return 'text-green-400';
        if (conf >= 0.6) return 'text-yellow-400';
        return 'text-red-400';
    };

    const brittleCount = policies.filter(p => p.isBrittle).length;

    return (
        <div className="bg-slate-900 rounded-xl border border-slate-700 p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                        <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                        Policy Confidence
                    </h2>
                    <p className="text-sm text-slate-400 mt-1">Governance rule effectiveness</p>
                </div>

                {brittleCount > 0 && (
                    <button
                        onClick={() => setShowBrittleOnly(!showBrittleOnly)}
                        className={`px-3 py-1 rounded-full text-sm flex items-center gap-1 ${showBrittleOnly
                                ? 'bg-red-500 text-white'
                                : 'bg-red-500/20 text-red-400'
                            }`}
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        {brittleCount} Brittle
                    </button>
                )}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4 text-center">
                    <p className="text-2xl font-bold text-white">{policies.length}</p>
                    <p className="text-xs text-slate-400">Active Policies</p>
                </div>
                <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4 text-center">
                    <p className="text-2xl font-bold text-green-400">
                        {(policies.reduce((a, b) => a + b.confidence, 0) / policies.length * 100).toFixed(0)}%
                    </p>
                    <p className="text-xs text-slate-400">Avg Confidence</p>
                </div>
                <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4 text-center">
                    <p className="text-2xl font-bold text-blue-400">
                        {policies.reduce((a, b) => a + b.timesApplied, 0)}
                    </p>
                    <p className="text-xs text-slate-400">Total Applications</p>
                </div>
            </div>

            {/* Policy List */}
            <div className="space-y-3">
                {filteredPolicies.map((policy) => (
                    <div
                        key={policy.policyId}
                        className={`bg-slate-800/50 rounded-lg border p-4 ${policy.isBrittle ? 'border-red-500/50' : 'border-slate-700'
                            }`}
                    >
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <div className="flex items-center gap-2">
                                    <span className="font-mono text-sm text-purple-400">{policy.policyId}</span>
                                    <span className="text-xs px-2 py-0.5 bg-slate-700 rounded text-slate-300">
                                        {policy.ruleType}
                                    </span>
                                    {policy.isBrittle && (
                                        <span className="text-xs px-2 py-0.5 bg-red-500/20 text-red-400 rounded">
                                            BRITTLE
                                        </span>
                                    )}
                                </div>
                                <p className="text-sm text-slate-300 mt-1">{policy.description}</p>
                            </div>

                            <div className="text-right">
                                <p className={`text-lg font-bold ${getConfidenceColor(policy.confidence)}`}>
                                    {(policy.confidence * 100).toFixed(0)}%
                                </p>
                                <p className="text-xs text-slate-400">confidence</p>
                            </div>
                        </div>

                        {/* Progress bar */}
                        <div className="mt-3">
                            <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                                <span>Effectiveness</span>
                                <span>{(policy.effectiveness * 100).toFixed(0)}%</span>
                            </div>
                            <div className="w-full bg-slate-700 rounded-full h-2">
                                <div
                                    className={`h-2 rounded-full ${policy.effectiveness >= 0.8 ? 'bg-green-500' :
                                            policy.effectiveness >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                                        }`}
                                    style={{ width: `${policy.effectiveness * 100}%` }}
                                />
                            </div>
                        </div>

                        {/* Meta */}
                        <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                            <span>Applied {policy.timesApplied} times</span>
                            <span>•</span>
                            <span>Last: {policy.lastApplied}</span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
