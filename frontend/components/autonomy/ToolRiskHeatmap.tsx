'use client';

import React, { useState } from 'react';

interface ToolRisk {
    tool: string;
    baseRisk: number;
    contextualRisk: number;
    successRate: number;
    lastUsed: string;
    isBlacklisted: boolean;
    cooldownSeconds: number;
}

export default function ToolRiskHeatmap() {
    const [tools] = useState<ToolRisk[]>([
        { tool: 'get_logs', baseRisk: 0.0, contextualRisk: 0.05, successRate: 0.99, lastUsed: '2m ago', isBlacklisted: false, cooldownSeconds: 0 },
        { tool: 'run_diagnostic', baseRisk: 0.1, contextualRisk: 0.15, successRate: 0.95, lastUsed: '5m ago', isBlacklisted: false, cooldownSeconds: 0 },
        { tool: 'restart_service', baseRisk: 0.3, contextualRisk: 0.45, successRate: 0.87, lastUsed: '12m ago', isBlacklisted: false, cooldownSeconds: 0 },
        { tool: 'scale_pod', baseRisk: 0.4, contextualRisk: 0.50, successRate: 0.82, lastUsed: '1h ago', isBlacklisted: false, cooldownSeconds: 0 },
        { tool: 'update_config', baseRisk: 0.5, contextualRisk: 0.65, successRate: 0.78, lastUsed: '3h ago', isBlacklisted: false, cooldownSeconds: 30 },
        { tool: 'apply_patch', baseRisk: 0.7, contextualRisk: 0.80, successRate: 0.65, lastUsed: '1d ago', isBlacklisted: false, cooldownSeconds: 0 },
        { tool: 'rollback_deploy', baseRisk: 0.8, contextualRisk: 0.90, successRate: 0.72, lastUsed: '2d ago', isBlacklisted: false, cooldownSeconds: 0 },
        { tool: 'escalate', baseRisk: 0.0, contextualRisk: 0.0, successRate: 1.0, lastUsed: '30m ago', isBlacklisted: false, cooldownSeconds: 0 },
    ]);

    const getRiskColor = (risk: number) => {
        if (risk >= 0.7) return 'bg-red-500';
        if (risk >= 0.5) return 'bg-orange-500';
        if (risk >= 0.3) return 'bg-yellow-500';
        if (risk >= 0.1) return 'bg-green-500';
        return 'bg-blue-500';
    };

    const getRiskLabel = (risk: number) => {
        if (risk >= 0.7) return 'HIGH';
        if (risk >= 0.5) return 'MEDIUM';
        if (risk >= 0.3) return 'LOW';
        return 'NONE';
    };

    return (
        <div className="bg-slate-900 rounded-xl border border-slate-700 p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                        <svg className="w-5 h-5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        Tool Risk Heatmap
                    </h2>
                    <p className="text-sm text-slate-400 mt-1">Dynamic risk assessment by context</p>
                </div>
            </div>

            {/* Heatmap Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                {tools.map((tool) => (
                    <div
                        key={tool.tool}
                        className={`relative rounded-lg border p-4 ${tool.isBlacklisted
                                ? 'border-red-500/50 bg-red-500/10'
                                : 'border-slate-700 bg-slate-800/50'
                            }`}
                    >
                        {/* Risk indicator */}
                        <div className={`absolute top-2 right-2 w-3 h-3 rounded-full ${getRiskColor(tool.contextualRisk)}`} />

                        {/* Tool name */}
                        <p className="font-mono text-sm text-white truncate">{tool.tool}</p>

                        {/* Risk bar */}
                        <div className="w-full bg-slate-700 rounded-full h-2 mt-2">
                            <div
                                className={`h-2 rounded-full ${getRiskColor(tool.contextualRisk)}`}
                                style={{ width: `${tool.contextualRisk * 100}%` }}
                            />
                        </div>

                        {/* Stats */}
                        <div className="flex items-center justify-between mt-2 text-xs text-slate-400">
                            <span>{tool.successRate * 100}% success</span>
                            <span className={getRiskColor(tool.contextualRisk).replace('bg-', 'text-')}>
                                {getRiskLabel(tool.contextualRisk)}
                            </span>
                        </div>

                        {/* Status badges */}
                        {(tool.isBlacklisted || tool.cooldownSeconds > 0) && (
                            <div className="mt-2">
                                {tool.isBlacklisted && (
                                    <span className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded">
                                        BLACKLISTED
                                    </span>
                                )}
                                {tool.cooldownSeconds > 0 && (
                                    <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">
                                        Cooldown: {tool.cooldownSeconds}s
                                    </span>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Legend */}
            <div className="flex items-center justify-center gap-6 pt-4 border-t border-slate-700">
                <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                    <span className="text-xs text-slate-400">None</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-green-500"></span>
                    <span className="text-xs text-slate-400">Low</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                    <span className="text-xs text-slate-400">Medium</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-orange-500"></span>
                    <span className="text-xs text-slate-400">Elevated</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-red-500"></span>
                    <span className="text-xs text-slate-400">High</span>
                </div>
            </div>
        </div>
    );
}
