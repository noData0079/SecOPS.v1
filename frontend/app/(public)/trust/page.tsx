import React from 'react';

export default function TrustPage() {
  return (
    <div className="container py-12">
      <h1 className="text-3xl font-bold mb-6">Trust & Security</h1>
      <div className="prose max-w-3xl">
        <p className="lead text-xl mb-6">
          Our philosophy is simple: You should not have to trust an AI blindly. TSM99 is built on an "Audit-First" architecture.
        </p>

        <h2 className="text-2xl font-bold mt-8 mb-4">Data Handling</h2>
        <p className="mb-4">
          We process data locally or within your private cloud environment. No sensitive data is sent to public model APIs without your explicit configuration and consent.
        </p>

        <h2 className="text-2xl font-bold mt-8 mb-4">Compliance</h2>
        <p className="mb-4">
          Our immutable audit ledger provides a cryptographic trail of every decision and action taken by the system, designed to map directly to SOC2 and ISO 27001 requirements.
        </p>

        <h2 className="text-2xl font-bold mt-8 mb-4">Transparency</h2>
        <p className="mb-4">
          We publish regular transparency reports regarding model safety evaluations and incident response effectiveness.
        </p>
      </div>
    </div>
  );
}
