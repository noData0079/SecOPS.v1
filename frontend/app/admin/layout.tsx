import React from 'react';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Admin Sidebar */}
      <aside className="w-64 bg-red-900 text-white flex flex-col">
        <div className="h-16 flex items-center justify-center font-bold text-xl border-b border-red-800">
          TSM99 Admin
        </div>
        <nav className="flex-1 px-2 py-4 space-y-2">
          <a href="/admin/overview" className="block px-4 py-2 rounded hover:bg-red-800">Overview</a>
          <a href="/admin/users" className="block px-4 py-2 rounded hover:bg-red-800">Users</a>
          <a href="/admin/projects" className="block px-4 py-2 rounded hover:bg-red-800">Projects</a>
          <a href="/admin/audit" className="block px-4 py-2 rounded hover:bg-red-800">Audit Logs</a>
          <a href="/admin/policies" className="block px-4 py-2 rounded hover:bg-red-800">Policies</a>
          <a href="/admin/billing" className="block px-4 py-2 rounded hover:bg-red-800">Billing</a>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-white border-b flex items-center justify-between px-6 border-l border-gray-200">
          <h1 className="text-lg font-semibold text-red-900">Admin Console</h1>
          <div className="flex items-center space-x-4">
             <span className="text-sm font-medium text-gray-500">Administrator</span>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
