"use client";

import { useState } from "react";
import { ExclamationTriangleIcon, PowerIcon } from "@heroicons/react/24/outline";

export default function AdminPage() {
  const [authenticated, setAuthenticated] = useState(false);
  const [password, setPassword] = useState("");

  // Simulated Toggles
  const [toggles, setToggles] = useState({
    demoMode: true,
    llmProviders: true,
    rag: true,
    autonomousExec: false
  });

  const [killSwitchActive, setKillSwitchActive] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === "admin123") { // Mock password
      setAuthenticated(true);
    } else {
      alert("Invalid password");
    }
  };

  const toggle = (key: keyof typeof toggles) => {
    setToggles(prev => ({ ...prev, [key]: !prev[key] }));
  };

  if (!authenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <form onSubmit={handleLogin} className="w-full max-w-md space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-8 shadow-2xl">
          <h1 className="text-xl font-bold text-white text-center">TSM99 Admin Control Plane</h1>
          <input
            type="password"
            placeholder="Enter Admin Key"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded bg-slate-800 border border-slate-700 px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
          <button type="submit" className="w-full rounded bg-emerald-600 py-2 font-medium text-white hover:bg-emerald-500">
            Access Dashboard
          </button>
        </form>
      </div>
    )
  }

  return (
    <div className={`min-h-screen bg-slate-950 text-slate-200 p-8 ${killSwitchActive ? "border-4 border-red-600" : ""}`}>
      <header className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">System Admin & Controls</h1>
        <div className="flex items-center gap-4">
          <div className="text-xs text-slate-400">
            Target: <span className="font-mono text-emerald-400">prod-us-east-1</span>
          </div>
          <button onClick={() => setAuthenticated(false)} className="text-xs text-red-400 hover:text-red-300">
            Logout
          </button>
        </div>
      </header>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Metrics */}
        <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Live Metrics</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center bg-slate-800/50 p-3 rounded">
              <span className="text-sm text-slate-400">Active Demo Sessions</span>
              <span className="text-lg font-mono text-white">24</span>
            </div>
            <div className="flex justify-between items-center bg-slate-800/50 p-3 rounded">
              <span className="text-sm text-slate-400">Tokens Consumed (1h)</span>
              <span className="text-lg font-mono text-white">2.4M</span>
            </div>
            <div className="flex justify-between items-center bg-slate-800/50 p-3 rounded">
              <span className="text-sm text-slate-400">Est. API Cost</span>
              <span className="text-lg font-mono text-white">$42.10</span>
            </div>
          </div>
        </section>

        {/* Feature Toggles */}
        <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Feature Toggles</h2>
          <div className="space-y-4">
            {Object.entries(toggles).map(([key, active]) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-sm text-slate-300 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
                <button
                  onClick={() => toggle(key as any)}
                  className={`h-6 w-11 rounded-full transition-colors relative ${active ? 'bg-emerald-600' : 'bg-slate-700'}`}
                >
                  <span className={`absolute top-1 left-1 bg-white h-4 w-4 rounded-full transition-transform ${active ? 'translate-x-5' : ''}`} />
                </button>
              </div>
            ))}
          </div>
        </section>

        {/* Kill Switch */}
        <section className="rounded-xl border border-red-900/30 bg-red-950/10 p-6">
          <h2 className="text-lg font-semibold text-red-500 mb-4 flex items-center gap-2">
            <ExclamationTriangleIcon className="h-6 w-6" />
            Danger Zone
          </h2>
          <p className="text-xs text-red-400 mb-6">
            Disabling external connectivity will immediately stop all ongoing reasoning loops, demo sessions, and agent actions.
          </p>

          <button
            onClick={() => setKillSwitchActive(!killSwitchActive)}
            className={`w-full flex items-center justify-center gap-2 rounded-lg py-4 font-bold text-white transition-all shadow-lg ${killSwitchActive ? 'bg-slate-800 text-red-500 border border-red-500' : 'bg-red-600 hover:bg-red-500'}`}
          >
            <PowerIcon className="h-6 w-6" />
            {killSwitchActive ? "SYSTEM HALTED - CLICK TO RESTORE" : "KILL SWITCH (HALT ALL)"}
          </button>
        </section>
      </div>
    </div>
  );
}
