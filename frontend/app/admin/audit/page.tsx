import React from 'react';

export default function AdminAuditPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-slate-800">Immutable Audit Ledger</h2>
      <div className="bg-white rounded-lg border shadow-sm p-4 mb-4">
        <p className="text-sm text-gray-600">
           This ledger is append-only and cryptographically verified.
        </p>
      </div>
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 font-mono text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Event ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actor</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Outcome</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            <tr>
              <td className="px-6 py-4">2023-10-27T10:00:00Z</td>
              <td className="px-6 py-4">evt_883a</td>
              <td className="px-6 py-4">system</td>
              <td className="px-6 py-4">POLICY_UPDATE</td>
              <td className="px-6 py-4 text-green-600">SUCCESS</td>
            </tr>
            <tr>
              <td className="px-6 py-4">2023-10-27T10:05:00Z</td>
              <td className="px-6 py-4">evt_883b</td>
              <td className="px-6 py-4">user_123</td>
              <td className="px-6 py-4">DELETE_DB</td>
              <td className="px-6 py-4 text-red-600">BLOCKED</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
