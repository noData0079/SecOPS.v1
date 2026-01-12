import React from 'react';

export default function AdminPoliciesPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-slate-800">Global Policies</h2>
      <div className="space-y-4">
        <div className="bg-white p-6 rounded-lg border shadow-sm">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-lg font-bold">Standard Operations</h3>
              <p className="text-sm text-gray-500">Applies to all non-admin users.</p>
            </div>
            <button className="text-sm text-blue-600 font-medium">Edit Rules</button>
          </div>
          <div className="bg-gray-50 p-4 rounded text-sm font-mono text-gray-700">
             ALLOW read_logs<br/>
             ALLOW restart_service WHERE env != 'production'<br/>
             BLOCK delete_database
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border shadow-sm">
           <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-lg font-bold">Emergency Override</h3>
              <p className="text-sm text-gray-500">Activated during declared incidents.</p>
            </div>
            <button className="text-sm text-blue-600 font-medium">Edit Rules</button>
          </div>
          <div className="bg-gray-50 p-4 rounded text-sm font-mono text-gray-700">
             ALLOW ALL WHERE approval_id IS NOT NULL
          </div>
        </div>
      </div>
    </div>
  );
}
