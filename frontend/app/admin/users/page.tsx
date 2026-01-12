import React from 'react';

export default function AdminUsersPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-slate-800">User Management</h2>
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            <tr>
              <td className="px-6 py-4 whitespace-nowrap">alice@example.com</td>
              <td className="px-6 py-4 whitespace-nowrap">Admin</td>
              <td className="px-6 py-4 whitespace-nowrap"><span className="text-green-600">Active</span></td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-blue-600 cursor-pointer">Edit</td>
            </tr>
            <tr>
              <td className="px-6 py-4 whitespace-nowrap">bob@example.com</td>
              <td className="px-6 py-4 whitespace-nowrap">User</td>
              <td className="px-6 py-4 whitespace-nowrap"><span className="text-gray-600">Inactive</span></td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-blue-600 cursor-pointer">Edit</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
