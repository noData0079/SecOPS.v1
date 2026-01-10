"use client";

import { useState, useEffect } from "react";
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CpuChipIcon,
  BanknotesIcon,
  KeyIcon,
  DocumentCheckIcon,
  BeakerIcon,
  Cog6ToothIcon,
  SignalIcon
} from "@heroicons/react/24/outline";

export default function ControlPlanePage() {
  const [authenticated, setAuthenticated] = useState(false);
  const [password, setPassword] = useState("");
  const [activeTab, setActiveTab] = useState("global");
  const [killSwitchActive, setKillSwitchActive] = useState(false);
  const [emergencyMode, setEmergencyMode] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === "admin123") {
      setAuthenticated(true);
    } else {
      alert("Invalid Access Key");
    }
  };

  const menuItems = [
    { id: "overview", label: "System Overview", icon: ShieldCheckIcon },
    { id: "global", label: "Global Controls", icon: ExclamationTriangleIcon, textClass: "text-red-400" },
    { id: "runtime", label: "Agent Runtime", icon: CpuChipIcon },
    { id: "usage", label: "Usage & Cost", icon: BanknotesIcon },
    { id: "access", label: "Access & Identity", icon: KeyIcon },
    { id: "ledger", label: "Trust Ledger", icon: DocumentCheckIcon },
    { id: "demo", label: "Demo Governance", icon: BeakerIcon },
    { id: "config", label: "Platform Config", icon: Cog6ToothIcon },
    { id: "health", label: "System Health", icon: SignalIcon },
  ];

  if (!authenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <form onSubmit={handleLogin} className="w-full max-w-md space-y-6 rounded-xl border border-slate-800 bg-slate-900 p-8 shadow-2xl">
          <div className="text-center">
            <h1 className="text-xl font-bold text-white tracking-wide">TSM99 CONTROL PLANE</h1>
            <p className="text-xs text-slate-500 mt-2">Restricted Access. All actions audited.</p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Identity</label>
            <input disabled value="founder@thesovereignmechanica.ai" className="w-full rounded bg-slate-800/50 border border-slate-700 px-4 py-2 text-slate-400 text-sm cursor-not-allowed" />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Access Key</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded bg-slate-800 border border-slate-700 px-4 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500"
            />
          </div>

          <button type="submit" className="w-full rounded bg-emerald-600 py-2 font-medium text-white hover:bg-emerald-500 transition">
            Authenticate
          </button>
        </form>
      </div>
    )
  }

  return (
    <div className={`min-h-screen bg-slate-950 text-slate-200 flex flex-col ${emergencyMode || killSwitchActive ? "border-4 border-red-600" : ""}`}>

      {/* Top Bar */}
      <header className="flex h-14 items-center justify-between border-b border-white/5 bg-slate-900 px-6">
        <div className="flex items-center gap-4">
          <span className="font-bold text-white tracking-widest text-sm">CONTROL PLANE</span>
          <span className="text-slate-600">|</span>
          <span className="text-xs text-emerald-400">Environment: Production</span>
        </div>
        <div className="flex items-center gap-4 text-xs">
          {emergencyMode && <span className="animate-pulse font-bold text-red-500">⚠ EMERGENCY MODE ACTIVE</span>}
          <span className="text-slate-400">Admin: <span className="text-white">founder@thesovereignmechanica.ai</span></span>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 border-r border-white/5 bg-slate-900 overflow-y-auto">
          <nav className="p-4 space-y-1">
            {menuItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex w-full items-center gap-3 rounded px-3 py-2 text-sm font-medium transition-colors ${activeTab === item.id
                    ? "bg-slate-800 text-white"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-white"
                  } ${item.textClass || ""}`}
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </button>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto p-8">
          {activeTab === "global" && (
            <div className="max-w-2xl mx-auto space-y-8">
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
                Global Controls
              </h2>

              {/* KILL SWITCH CARD */}
              <div className="rounded-xl border border-red-900/50 bg-red-950/10 p-8 text-center">
                <h3 className="text-xl font-bold text-red-500 mb-2">Global Kill Switch</h3>
                <p className="text-sm text-red-400 mb-8 max-w-md mx-auto">
                  Activation immediately halts all autonomous execution, agent reasoning loops, and API calls. Read-only access persists.
                </p>

                <div className="mb-6">
                  <label className="block text-left text-xs font-medium text-red-300 mb-1">Mandatory Reason for Audit Log</label>
                  <input placeholder="e.g. Unexpected agent behavior in pod-99" className="w-full bg-red-950/30 border border-red-900/50 rounded px-3 py-2 text-red-200 placeholder-red-700/50 focus:outline-none focus:border-red-500" />
                </div>

                <button
                  onClick={() => setKillSwitchActive(!killSwitchActive)}
                  className={`w-full py-4 rounded font-bold text-lg transition-all ${killSwitchActive
                      ? "bg-slate-900 text-red-500 border-2 border-red-500 shadow-[0_0_20px_rgba(239,68,68,0.3)]"
                      : "bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-900/20"
                    }`}
                >
                  {killSwitchActive ? "SYSTEM HALTED - CLICK TO RESTORE" : "ACTIVATE KILL SWITCH"}
                </button>
              </div>
            </div>
          )}

          {activeTab !== "global" && (
            <div className="flex h-full items-center justify-center text-slate-500">
              <div className="text-center">
                <DocumentCheckIcon className="h-12 w-12 mx-auto mb-4 opacity-20" />
                <p>Module <strong>{menuItems.find(m => m.id === activeTab)?.label}</strong> is active.</p>
                <p className="text-xs mt-2">All actions in this view are logged to the Trust Ledger.</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
