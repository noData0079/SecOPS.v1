import React from 'react';

export default function AboutPage() {
  return (
    <div className="container py-12">
      <h1 className="text-3xl font-bold mb-6">About TSM99</h1>
      <div className="max-w-3xl">
        <p className="text-lg mb-6">
          We are building the future of autonomous security operations.
        </p>

        <h2 className="text-2xl font-bold mt-8 mb-4">Mission</h2>
        <p className="mb-4">
          To empower security teams with autonomous agents that are safe, reliable, and accountable.
        </p>

        <h2 className="text-2xl font-bold mt-8 mb-4">Vision</h2>
        <p className="mb-4">
          A world where security operations are proactive, not reactive, and where human expertise is amplified by machine speed and scale.
        </p>
      </div>
    </div>
  );
}
