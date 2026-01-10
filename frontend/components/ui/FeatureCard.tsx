"use client";

import React from "react";

type FeatureCardProps = {
    title: string;
    description?: string; // Optional description
    onClick?: () => void;
    className?: string;
    icon?: React.ReactNode;
};

export function FeatureCard({ title, description, onClick, className = "", icon }: FeatureCardProps) {
    return (
        <button
            onClick={onClick}
            className={`group relative flex flex-col items-start rounded-xl border border-slate-800 bg-slate-900/50 p-6 text-left transition-all hover:border-slate-600 hover:bg-slate-900 ${className}`}
        >
            {/* Optional Glow Effect on Hover */}
            <div className="absolute inset-0 -z-10 rounded-xl bg-gradient-to-br from-emerald-500/0 to-emerald-500/0 opacity-0 transition-opacity group-hover:from-emerald-500/5 group-hover:to-transparent group-hover:opacity-100" />

            {icon && <div className="mb-4 text-emerald-400">{icon}</div>}

            <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
            {description && (
                <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                    {description}
                </p>
            )}
        </button>
    );
}
