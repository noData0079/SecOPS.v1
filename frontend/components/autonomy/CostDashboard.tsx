'use client';

import React, { useState } from 'react';

interface BudgetData {
    tenantId: string;
    dailyUsed: number;
    dailyLimit: number;
    monthlyUsed: number;
    monthlyLimit: number;
}

interface CostByTool {
    tool: string;
    cost: number;
    uses: number;
    roi: number;
}

export default function CostDashboard() {
    const [budget] = useState<BudgetData>({
        tenantId: 'default',
        dailyUsed: 45.23,
        dailyLimit: 100,
        monthlyUsed: 892.50,
        monthlyLimit: 2000,
    });

    const [costByTool] = useState<CostByTool[]>([
        { tool: 'restart_service', cost: 12.50, uses: 125, roi: 45.2 },
        { tool: 'get_logs', cost: 2.30, uses: 230, roi: 0 },
        { tool: 'scale_pod', cost: 18.75, uses: 75, roi: 32.1 },
        { tool: 'run_diagnostic', cost: 8.40, uses: 84, roi: 12.5 },
        { tool: 'rollback_deploy', cost: 3.28, uses: 8, roi: 156.0 },
    ]);

    const dailyPct = (budget.dailyUsed / budget.dailyLimit) * 100;
    const monthlyPct = (budget.monthlyUsed / budget.monthlyLimit) * 100;

    const getStatusColor = (pct: number) => {
        if (pct >= 90) return 'bg-red-500';
        if (pct >= 70) return 'bg-yellow-500';
        return 'bg-green-500';
    };

    return (
        <div className="bg-slate-900 rounded-xl border border-slate-700 p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                        <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Cost Dashboard
                    </h2>
                    <p className="text-sm text-slate-400 mt-1">Economic governance & ROI tracking</p>
                </div>

                {/* Emergency Cutoff */}
                <button className="px-4 py-2 bg-red-600/20 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-600/30 transition-colors">
                    Emergency Cutoff
                </button>
            </div>

            {/* Budget Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {/* Daily Budget */}
                <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-sm font-medium text-slate-300">Daily Budget</h3>
                        <span className="text-xs text-slate-400">
                            ${budget.dailyUsed.toFixed(2)} / ${budget.dailyLimit}
                        </span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-3">
                        <div
                            className={`h-3 rounded-full transition-all ${getStatusColor(dailyPct)}`}
                            style={{ width: `${Math.min(dailyPct, 100)}%` }}
                        />
                    </div>
                    <p className="text-xs text-slate-400 mt-2">
                        {dailyPct.toFixed(1)}% used • ${(budget.dailyLimit - budget.dailyUsed).toFixed(2)} remaining
                    </p>
                </div>

                {/* Monthly Budget */}
                <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-4">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-sm font-medium text-slate-300">Monthly Budget</h3>
                        <span className="text-xs text-slate-400">
                            ${budget.monthlyUsed.toFixed(2)} / ${budget.monthlyLimit}
                        </span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-3">
                        <div
                            className={`h-3 rounded-full transition-all ${getStatusColor(monthlyPct)}`}
                            style={{ width: `${Math.min(monthlyPct, 100)}%` }}
                        />
                    </div>
                    <p className="text-xs text-slate-400 mt-2">
                        {monthlyPct.toFixed(1)}% used • ${(budget.monthlyLimit - budget.monthlyUsed).toFixed(2)} remaining
                    </p>
                </div>
            </div>

            {/* Cost by Tool */}
            <div>
                <h3 className="text-sm font-medium text-slate-300 mb-4">Cost by Tool (Last 30 Days)</h3>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="text-left text-slate-400 border-b border-slate-700">
                                <th className="pb-3 font-medium">Tool</th>
                                <th className="pb-3 font-medium text-right">Uses</th>
                                <th className="pb-3 font-medium text-right">Cost</th>
                                <th className="pb-3 font-medium text-right">Avg Cost</th>
                                <th className="pb-3 font-medium text-right">ROI</th>
                            </tr>
                        </thead>
                        <tbody>
                            {costByTool.map((item) => (
                                <tr key={item.tool} className="border-b border-slate-800">
                                    <td className="py-3 font-mono text-purple-400">{item.tool}</td>
                                    <td className="py-3 text-right text-slate-300">{item.uses}</td>
                                    <td className="py-3 text-right text-slate-300">${item.cost.toFixed(2)}</td>
                                    <td className="py-3 text-right text-slate-400">
                                        ${(item.cost / item.uses).toFixed(4)}
                                    </td>
                                    <td className="py-3 text-right">
                                        <span className={`px-2 py-1 rounded text-xs ${item.roi >= 50
                                                ? 'bg-green-500/20 text-green-400'
                                                : item.roi >= 20
                                                    ? 'bg-yellow-500/20 text-yellow-400'
                                                    : 'bg-slate-500/20 text-slate-400'
                                            }`}>
                                            {item.roi > 0 ? `${item.roi.toFixed(1)}x` : 'N/A'}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-700">
                <div className="text-center">
                    <p className="text-2xl font-bold text-white">$45.23</p>
                    <p className="text-xs text-slate-400">Today&apos;s Spend</p>
                </div>
                <div className="text-center">
                    <p className="text-2xl font-bold text-green-400">32.4x</p>
                    <p className="text-xs text-slate-400">Overall ROI</p>
                </div>
                <div className="text-center">
                    <p className="text-2xl font-bold text-blue-400">522</p>
                    <p className="text-xs text-slate-400">Total Actions</p>
                </div>
                <div className="text-center">
                    <p className="text-2xl font-bold text-purple-400">$0.09</p>
                    <p className="text-xs text-slate-400">Avg Cost/Action</p>
                </div>
            </div>
        </div>
    );
}
