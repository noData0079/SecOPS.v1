import React from 'react';

interface VaultStatusProps {
  trustScore?: number;
}

export const VaultStatus: React.FC<VaultStatusProps> = ({ trustScore = 100 }) => (
  <div className="p-4 border border-cyan-500/30 bg-black/50 backdrop-blur-md rounded-lg">
    <h3 className="text-xs uppercase text-cyan-400 mb-2">Hardware Enclave (TEE)</h3>
    <div className="flex items-center gap-4">
      <div className="relative h-12 w-12">
         {/* Animated spinning pulse rings */}
         <div className="absolute inset-0 border-2 border-cyan-500 rounded-full animate-ping" />
         <div className="absolute inset-2 border border-cyan-300 rounded-full animate-pulse" />
      </div>
      <div>
        <div className="text-xl font-mono text-white">LOCKED</div>
        <div className="text-[10px] text-gray-400 italic">Egress Block: {trustScore}% Active</div>
      </div>
    </div>
  </div>
);
