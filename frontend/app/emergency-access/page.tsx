"use client";

import { useState } from "react";
import { ExclamationCircleIcon, ShieldExclamationIcon } from "@heroicons/react/24/outline";

export default function EmergencyAccessPage() {
    const [step, setStep] = useState(1);
    const [token, setToken] = useState("");
    const [reason, setReason] = useState("");

    const handleActivate = (e: React.FormEvent) => {
        e.preventDefault();
        // In real scenario, this would validate the single-use token backend-side
        if (token && reason) {
            setStep(2); // Success state
        }
    };

    if (step === 2) {
        return (
            <div className="min-h-screen bg-red-950 text-white flex flex-col items-center justify-center p-6 text-center border-[20px] border-red-600 animate-pulse">
                <ShieldExclamationIcon className="h-24 w-24 text-red-500 mb-6" />
                <h1 className="text-4xl font-black mb-4 uppercase tracking-widest">Emergency Mode Active</h1>
                <p className="text-xl text-red-200 max-w-2xl mb-8">
                    You have been granted temporary, audited Break-Glass access. <br />
                    Session expires in <span className="font-mono font-bold">14:59</span>.
                </p>
                <div className="bg-black/50 p-6 rounded-lg text-left max-w-lg w-full mb-8 font-mono text-sm border border-red-500/30">
                    <div className="flex justify-between mb-2">
                        <span className="text-red-400">Identity:</span>
                        <span>EMERGENCY_ADMIN_01</span>
                    </div>
                    <div className="flex justify-between mb-2">
                        <span className="text-red-400">Reason:</span>
                        <span>{reason}</span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-red-400">Log ID:</span>
                        <span>0xCRITICAL_fa72...1b</span>
                    </div>
                </div>
                <button
                    onClick={() => window.location.href = '/admin'}
                    className="bg-red-600 hover:bg-red-500 text-white px-8 py-3 rounded font-bold text-lg shadow-lg shadow-red-900/50"
                >
                    Enter Control Plane
                </button>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 flex items-center justify-center p-6">
            <div className="w-full max-w-lg">
                <div className="text-center mb-8">
                    <div className="mx-auto h-16 w-16 bg-red-900/20 rounded-full flex items-center justify-center mb-4 border border-red-500/20">
                        <ExclamationCircleIcon className="h-8 w-8 text-red-500" />
                    </div>
                    <h1 className="text-3xl font-bold text-white uppercase tracking-wide">Break Glass Access</h1>
                    <p className="mt-2 text-slate-400 text-sm">
                        This procedure is for emergencies only. All actions will be logged as CRITICAL severity and cannot be deleted.
                    </p>
                </div>

                <form onSubmit={handleActivate} className="space-y-6 bg-slate-900 border border-slate-800 p-8 rounded-2xl shadow-2xl relative overflow-hidden">
                    {/* Warning Stripe */}
                    <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-600 via-orange-500 to-red-600" />

                    <div>
                        <label className="block text-xs font-bold text-red-400 mb-1 uppercase">Emergency Token</label>
                        <input
                            required
                            type="password"
                            placeholder="Enter offline single-use token"
                            value={token}
                            onChange={(e) => setToken(e.target.value)}
                            className="w-full rounded bg-slate-950 border border-slate-700 px-4 py-3 text-white focus:border-red-500 focus:outline-none font-mono"
                        />
                    </div>

                    <div>
                        <label className="block text-xs font-bold text-red-400 mb-1 uppercase">Mandatory Reason</label>
                        <textarea
                            required
                            rows={3}
                            placeholder="Detailed explanation required for audit log..."
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            className="w-full rounded bg-slate-950 border border-slate-700 px-4 py-3 text-white focus:border-red-500 focus:outline-none"
                        />
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-red-950/20 border border-red-900/30 rounded">
                        <input required type="checkbox" className="mt-1 bg-slate-900 border-slate-700 rounded text-red-600 focus:ring-red-500" />
                        <span className="text-xs text-slate-400 leading-relaxed">
                            I acknowledge that this session is monitored and that misuse of emergency privileges will result in immediate revocation and incident review.
                        </span>
                    </div>

                    <button type="submit" className="w-full rounded bg-red-600 py-3 font-bold text-white hover:bg-red-500 transition shadow-lg shadow-red-900/20 uppercase tracking-wider">
                        Activate Emergency Mode
                    </button>
                </form>
            </div>
        </div>
    );
}
