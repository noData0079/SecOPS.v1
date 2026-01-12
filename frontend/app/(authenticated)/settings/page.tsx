import React from 'react';

export default function SettingsPage() {
  return (
    <div className="max-w-2xl">
      <h2 className="text-2xl font-bold mb-6">Settings</h2>

      <div className="bg-white p-6 rounded-lg border mb-6">
        <h3 className="text-lg font-bold mb-4">Profile</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input type="email" value="user@example.com" disabled className="mt-1 block w-full border-gray-300 rounded-md shadow-sm bg-gray-50" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Display Name</label>
            <input type="text" className="mt-1 block w-full border-gray-300 rounded-md shadow-sm" />
          </div>
        </div>
        <div className="mt-4 text-right">
           <button className="bg-slate-900 text-white px-4 py-2 rounded text-sm">Save Changes</button>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg border">
        <h3 className="text-lg font-bold mb-4">API Keys</h3>
        <div className="p-4 bg-gray-50 rounded border flex justify-between items-center">
           <code className="text-sm">sk_live_...4f9a</code>
           <button className="text-red-600 text-sm hover:underline">Revoke</button>
        </div>
        <div className="mt-4">
           <button className="border border-gray-300 px-4 py-2 rounded text-sm hover:bg-gray-50">Generate New Key</button>
        </div>
      </div>
    </div>
  );
}
