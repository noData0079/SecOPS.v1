import React from 'react';

export default function PricingPage() {
  return (
    <div className="container py-12">
      <h1 className="text-3xl font-bold mb-8 text-center">Pricing Plans</h1>
      <div className="grid md:grid-cols-3 gap-8">
        <div className="p-6 border rounded-lg shadow-sm">
          <h3 className="text-xl font-bold mb-2">Developer</h3>
          <p className="text-3xl font-bold mb-4">$0 <span className="text-sm font-normal text-gray-500">/ mo</span></p>
          <ul className="space-y-2 mb-6">
            <li>Local deployment</li>
            <li>Single agent</li>
            <li>Community support</li>
          </ul>
          <button className="w-full py-2 bg-slate-900 text-white rounded">Sign Up</button>
        </div>
        <div className="p-6 border rounded-lg shadow-sm bg-slate-50 border-slate-200">
          <h3 className="text-xl font-bold mb-2">Pro</h3>
          <p className="text-3xl font-bold mb-4">$49 <span className="text-sm font-normal text-gray-500">/ mo</span></p>
          <ul className="space-y-2 mb-6">
            <li>Cloud hosting</li>
            <li>5 Active agents</li>
            <li>Priority support</li>
            <li>Audit logs</li>
          </ul>
          <button className="w-full py-2 bg-slate-900 text-white rounded">Get Pro</button>
        </div>
        <div className="p-6 border rounded-lg shadow-sm">
          <h3 className="text-xl font-bold mb-2">Enterprise</h3>
          <p className="text-3xl font-bold mb-4">Custom</p>
          <ul className="space-y-2 mb-6">
            <li>Air-gapped deployment</li>
            <li>Unlimited agents</li>
            <li>Dedicated success manager</li>
            <li>Custom SLAs</li>
          </ul>
          <button className="w-full py-2 bg-white border border-slate-300 rounded">Contact Sales</button>
        </div>
      </div>
    </div>
  );
}
