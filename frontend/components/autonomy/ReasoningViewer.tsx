'use client';

import React, { useState, useEffect } from 'react';

interface ReasoningStep {
    timestamp: string;
    observation: string;
    modelDecision: {
        tool: string;
        args: Record<string, unknown>;
        confidence: number;
    };
    policyDecision: 'ALLOW' | 'BLOCK' | 'ESCALATE';
    policyReason: string;
    outcome?: {
        success: boolean;
        score: number;
    };
}

interface ReasoningViewerProps {
    incidentId: string;
    onClose?: () => void;
}

export default function AutonomyReasoningViewer({ incidentId, onClose }: ReasoningViewerProps) {
    const [steps, setSteps] = useState<ReasoningStep[]>([]);
    const [selectedStep, setSelectedStep] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Simulated data - replace with actual API call
        const mockSteps: ReasoningStep[] = [
            {
                timestamp: new Date().toISOString(),
                observation: 'High CPU usage detected on api-server-1 (95%)',
                modelDecision: {
                    tool: 'restart_service',
                    args: { service: 'api-server-1', graceful: true },
                    confidence: 0.87,
                },
                policyDecision: 'ALLOW',
                policyReason: 'Risk level LOW in staging environment',
                outcome: { success: true, score: 85 },
            },
            {
                timestamp: new Date(Date.now() + 30000).toISOString(),
                observation: 'CPU normalized to 45%',
                modelDecision: {
                    tool: 'get_logs',
                    args: { service: 'api-server-1', lines: 100 },
                    confidence: 0.92,
                },
                policyDecision: 'ALLOW',
                policyReason: 'Read-only operation, no risk',
                outcome: { success: true, score: 95 },
            },
        ];

        setTimeout(() => {
            setSteps(mockSteps);
            setLoading(false);
        }, 500);
    }, [incidentId]);

    const getPolicyColor = (decision: string) => {
        switch (decision) {
            case 'ALLOW': return 'bg-green-500/20 text-green-400 border-green-500/30';
            case 'BLOCK': return 'bg-red-500/20 text-red-400 border-red-500/30';
            case 'ESCALATE': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
            default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
        }
    };

    return (
        <div className="bg-slate-900 rounded-xl border border-slate-700 p-6 max-w-4xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                        <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                        Autonomy Reasoning
                    </h2>
                    <p className="text-sm text-slate-400 mt-1">Incident: {incidentId}</p>
                </div>
                {onClose && (
                    <button onClick={onClose} className="text-slate-400 hover:text-white">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                )}
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
                </div>
            ) : (
                <>
                    {/* Timeline */}
                    <div className="space-y-4">
                        {steps.map((step, index) => (
                            <div
                                key={index}
                                className={`relative pl-8 pb-4 border-l-2 ${index === steps.length - 1 ? 'border-transparent' : 'border-slate-700'
                                    }`}
                            >
                                {/* Timeline dot */}
                                <div className={`absolute left-[-9px] top-0 w-4 h-4 rounded-full border-2 ${step.outcome?.success
                                        ? 'bg-green-500 border-green-400'
                                        : 'bg-slate-700 border-slate-600'
                                    }`} />

                                {/* Step card */}
                                <div
                                    className={`bg-slate-800/50 rounded-lg border ${selectedStep === index ? 'border-purple-500' : 'border-slate-700'
                                        } p-4 cursor-pointer hover:border-purple-500/50 transition-colors`}
                                    onClick={() => setSelectedStep(selectedStep === index ? null : index)}
                                >
                                    {/* Observation */}
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <p className="text-sm text-slate-400">
                                                {new Date(step.timestamp).toLocaleTimeString()}
                                            </p>
                                            <p className="text-white mt-1">{step.observation}</p>
                                        </div>
                                        <span className={`px-2 py-1 rounded-full text-xs border ${getPolicyColor(step.policyDecision)}`}>
                                            {step.policyDecision}
                                        </span>
                                    </div>

                                    {/* Expanded details */}
                                    {selectedStep === index && (
                                        <div className="mt-4 space-y-4 border-t border-slate-700 pt-4">
                                            {/* Model Decision */}
                                            <div>
                                                <h4 className="text-sm font-medium text-slate-300 mb-2">Model Decision</h4>
                                                <div className="bg-slate-900 rounded p-3">
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-purple-400 font-mono">{step.modelDecision.tool}</span>
                                                        <span className="text-sm text-slate-400">
                                                            Confidence: {(step.modelDecision.confidence * 100).toFixed(0)}%
                                                        </span>
                                                    </div>
                                                    <pre className="text-xs text-slate-400 mt-2 overflow-x-auto">
                                                        {JSON.stringify(step.modelDecision.args, null, 2)}
                                                    </pre>
                                                </div>
                                            </div>

                                            {/* Policy Reason */}
                                            <div>
                                                <h4 className="text-sm font-medium text-slate-300 mb-2">Policy Reason</h4>
                                                <p className="text-sm text-slate-400 bg-slate-900 rounded p-3">
                                                    {step.policyReason}
                                                </p>
                                            </div>

                                            {/* Outcome */}
                                            {step.outcome && (
                                                <div>
                                                    <h4 className="text-sm font-medium text-slate-300 mb-2">Outcome</h4>
                                                    <div className="flex items-center gap-4 bg-slate-900 rounded p-3">
                                                        <span className={`px-2 py-1 rounded text-xs ${step.outcome.success
                                                                ? 'bg-green-500/20 text-green-400'
                                                                : 'bg-red-500/20 text-red-400'
                                                            }`}>
                                                            {step.outcome.success ? 'SUCCESS' : 'FAILED'}
                                                        </span>
                                                        <span className="text-sm text-slate-400">
                                                            Score: {step.outcome.score}/100
                                                        </span>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Legend */}
                    <div className="mt-6 pt-4 border-t border-slate-700 flex items-center gap-4 text-xs text-slate-400">
                        <span className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-green-500"></span>
                            ALLOW
                        </span>
                        <span className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-red-500"></span>
                            BLOCK
                        </span>
                        <span className="flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                            ESCALATE
                        </span>
                    </div>
                </>
            )}
        </div>
    );
}
