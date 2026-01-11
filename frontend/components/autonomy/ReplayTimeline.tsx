'use client';

import React, { useState } from 'react';

interface ReplayEntry {
    id: string;
    incidentId: string;
    timestamp: string;
    observation: string;
    action: string;
    outcome: 'success' | 'failure' | 'escalated';
    score: number;
    learningApplied: boolean;
}

export default function ReplayTimeline() {
    const [entries] = useState<ReplayEntry[]>([
        {
            id: '1',
            incidentId: 'INC-001',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            observation: 'Memory leak detected in payment-service',
            action: 'restart_service',
            outcome: 'success',
            score: 92,
            learningApplied: true,
        },
        {
            id: '2',
            incidentId: 'INC-002',
            timestamp: new Date(Date.now() - 7200000).toISOString(),
            observation: 'Database connection timeout',
            action: 'scale_pod',
            outcome: 'success',
            score: 78,
            learningApplied: true,
        },
        {
            id: '3',
            incidentId: 'INC-003',
            timestamp: new Date(Date.now() - 10800000).toISOString(),
            observation: 'Critical security vulnerability CVE-2024-XXXX',
            action: 'apply_patch',
            outcome: 'escalated',
            score: 0,
            learningApplied: false,
        },
        {
            id: '4',
            incidentId: 'INC-004',
            timestamp: new Date(Date.now() - 14400000).toISOString(),
            observation: 'Deployment rollback needed',
            action: 'rollback_deploy',
            outcome: 'failure',
            score: 35,
            learningApplied: true,
        },
    ]);

    const [filter, setFilter] = useState<'all' | 'success' | 'failure' | 'escalated'>('all');

    const filteredEntries = entries.filter(e => filter === 'all' || e.outcome === filter);

    const getOutcomeStyle = (outcome: string) => {
        switch (outcome) {
            case 'success': return 'bg-green-500/20 text-green-400 border-green-500/30';
            case 'failure': return 'bg-red-500/20 text-red-400 border-red-500/30';
            case 'escalated': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
            default: return 'bg-slate-500/20 text-slate-400';
        }
    };

    const stats = {
        total: entries.length,
        success: entries.filter(e => e.outcome === 'success').length,
        failure: entries.filter(e => e.outcome === 'failure').length,
        escalated: entries.filter(e => e.outcome === 'escalated').length,
        avgScore: Math.round(entries.reduce((a, b) => a + b.score, 0) / entries.length),
        learned: entries.filter(e => e.learningApplied).length,
    };

    return (
        <div className="bg-slate-900 rounded-xl border border-slate-700 p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                        <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Replay Timeline
                    </h2>
                    <p className="text-sm text-slate-400 mt-1">Learning from past actions</p>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                    <p className="text-sm text-slate-400">Total Actions</p>
                    <p className="text-2xl font-bold text-white">{stats.total}</p>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                    <p className="text-sm text-slate-400">Success Rate</p>
                    <p className="text-2xl font-bold text-green-400">
                        {((stats.success / stats.total) * 100).toFixed(0)}%
                    </p>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                    <p className="text-sm text-slate-400">Avg Score</p>
                    <p className="text-2xl font-bold text-blue-400">{stats.avgScore}</p>
                </div>
                <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
                    <p className="text-sm text-slate-400">Lessons Applied</p>
                    <p className="text-2xl font-bold text-purple-400">{stats.learned}</p>
                </div>
            </div>

            {/* Filters */}
            <div className="flex gap-2 mb-4">
                {(['all', 'success', 'failure', 'escalated'] as const).map(f => (
                    <button
                        key={f}
                        onClick={() => setFilter(f)}
                        className={`px-3 py-1 rounded-full text-sm transition-colors ${filter === f
                                ? 'bg-purple-500 text-white'
                                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                            }`}
                    >
                        {f.charAt(0).toUpperCase() + f.slice(1)}
                    </button>
                ))}
            </div>

            {/* Timeline */}
            <div className="space-y-3">
                {filteredEntries.map((entry) => (
                    <div
                        key={entry.id}
                        className="bg-slate-800/50 rounded-lg border border-slate-700 p-4 hover:border-slate-600 transition-colors"
                    >
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xs text-slate-500 font-mono">{entry.incidentId}</span>
                                    <span className="text-xs text-slate-500">
                                        {new Date(entry.timestamp).toLocaleString()}
                                    </span>
                                </div>
                                <p className="text-white">{entry.observation}</p>
                                <div className="flex items-center gap-3 mt-2">
                                    <span className="text-sm text-purple-400 font-mono">→ {entry.action}</span>
                                    {entry.learningApplied && (
                                        <span className="text-xs text-green-400 flex items-center gap-1">
                                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                            </svg>
                                            Learning Applied
                                        </span>
                                    )}
                                </div>
                            </div>
                            <div className="flex flex-col items-end gap-2">
                                <span className={`px-2 py-1 rounded-full text-xs border ${getOutcomeStyle(entry.outcome)}`}>
                                    {entry.outcome.toUpperCase()}
                                </span>
                                {entry.score > 0 && (
                                    <span className="text-sm text-slate-400">Score: {entry.score}</span>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
