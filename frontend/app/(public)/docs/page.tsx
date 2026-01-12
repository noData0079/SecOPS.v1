import React from 'react';

export default function DocsPage() {
  return (
    <div className="container py-12">
      <h1 className="text-3xl font-bold mb-6">Documentation</h1>
      <div className="grid md:grid-cols-4 gap-8">
        <div className="col-span-1 border-r pr-4">
           <ul className="space-y-2">
             <li className="font-bold">Getting Started</li>
             <li className="pl-4 text-gray-600">Installation</li>
             <li className="pl-4 text-gray-600">Configuration</li>
             <li className="font-bold mt-4">Core Concepts</li>
             <li className="pl-4 text-gray-600">Agents</li>
             <li className="pl-4 text-gray-600">Policies</li>
           </ul>
        </div>
        <div className="col-span-3">
          <h2 className="text-2xl font-bold mb-4">Platform Overview</h2>
          <p className="mb-4">
            TSM99 is an autonomous security intelligence platform designed to work alongside human operators.
            It leverages advanced LLMs to reason about security events and take action within safe bounds.
          </p>
          <h3 className="text-xl font-bold mb-2">Architecture</h3>
          <p className="mb-4">
            The system is built on a modular architecture separating the reasoning engine (Model) from the execution layer (Tools).
            This ensures that no AI action is taken without passing through a deterministic Policy Engine.
          </p>
        </div>
      </div>
    </div>
  );
}
