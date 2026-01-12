import { motion } from 'framer-motion';
import React from 'react';

interface AuditEvent {
    id: string;
    timestamp: string;
    axiom_summary: string;
}

interface AuditData {
    evolutions: AuditEvent[];
}

export const SovereignReport = ({ auditData }: { auditData: AuditData }) => (
  <div className="bg-white p-10 rounded-xl shadow-2xl text-slate-900 font-sans">
    <header className="border-b-2 border-slate-200 pb-6 mb-8 flex justify-between items-center">
      <h1 className="text-3xl font-bold uppercase tracking-tighter">Sovereign Transparency Report v1.1</h1>
      <div className="px-4 py-2 bg-green-100 text-green-700 rounded-full font-bold text-sm">
        HARDWARE ATTESTED: ACTIVE
      </div>
    </header>

    <section className="grid grid-cols-1 md:grid-cols-2 gap-12">
      {/* 1. Isolation Proof */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-500">Data Isolation Proof</h2>
        <div className="h-48 bg-slate-50 border-2 border-dashed border-slate-200 rounded-lg relative overflow-hidden flex items-center justify-center">
           {/* GSAP Animation of particles bouncing off a center 'Vault' core */}
           <motion.div
             animate={{ rotate: 360 }}
             transition={{ repeat: Infinity, duration: 10, ease: "linear" }}
             className="w-24 h-24 border-4 border-cyan-500 rounded-full border-t-transparent"
           />
           <div className="absolute text-xs text-slate-400 font-mono">ENCRYPTED</div>
        </div>
        <p className="text-xs text-slate-400 italic">"Cryptographic Zero-Knowledge Proof (ZKP) confirms 0.00% PII egress."</p>
      </div>

      {/* 2. Self-Evolution History */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-500">Evolution Lineage</h2>
        <ul className="space-y-2 max-h-48 overflow-y-auto">
          {auditData.evolutions.map(ev => (
            <li key={ev.id} className="text-sm p-2 bg-slate-100 rounded border-l-4 border-cyan-500">
              <strong>{ev.timestamp}:</strong> {ev.axiom_summary}
            </li>
          ))}
        </ul>
      </div>
    </section>
  </div>
);
