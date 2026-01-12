import React from 'react';

export default function PlaybooksPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Incident Playbooks</h2>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg border hover:shadow-md transition-shadow cursor-pointer">
          <h3 className="text-lg font-bold mb-2">DDoS Mitigation</h3>
          <p className="text-sm text-gray-500 mb-4">Automatically scales WAF rules and rate limiting.</p>
          <div className="flex justify-between items-center">
             <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">Automated</span>
             <button className="text-sm text-blue-600 hover:underline">View Details</button>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border hover:shadow-md transition-shadow cursor-pointer">
          <h3 className="text-lg font-bold mb-2">Phishing Investigation</h3>
          <p className="text-sm text-gray-500 mb-4">Analyzes email headers and correlates with threat intel.</p>
          <div className="flex justify-between items-center">
             <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">Human-in-the-loop</span>
             <button className="text-sm text-blue-600 hover:underline">View Details</button>
          </div>
        </div>
      </div>
    </div>
  );
}
