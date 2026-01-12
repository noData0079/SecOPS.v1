import React from 'react';

export default function LogsPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">System Logs</h2>

      <div className="bg-white p-4 rounded-lg border mb-4">
        <div className="flex gap-4">
           <input type="text" placeholder="Search logs..." className="border rounded px-3 py-2 flex-1" />
           <select className="border rounded px-3 py-2">
             <option>All Severities</option>
             <option>Info</option>
             <option>Warning</option>
             <option>Error</option>
           </select>
        </div>
      </div>

      <div className="space-y-2">
        <div className="bg-white p-4 rounded border text-sm font-mono">
           <span className="text-gray-500">[2023-10-27 10:00:01]</span> <span className="text-blue-600">INFO</span> Agent initialization complete.
        </div>
        <div className="bg-white p-4 rounded border text-sm font-mono">
           <span className="text-gray-500">[2023-10-27 10:00:05]</span> <span className="text-blue-600">INFO</span> Connected to database.
        </div>
        <div className="bg-white p-4 rounded border text-sm font-mono border-l-4 border-l-red-500">
           <span className="text-gray-500">[2023-10-27 10:05:00]</span> <span className="text-red-600">ERROR</span> Failed to connect to external API. Retry in 5s.
        </div>
      </div>
    </div>
  );
}
