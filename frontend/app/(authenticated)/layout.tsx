import React from 'react';

export default function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col">
        <div className="h-16 flex items-center justify-center font-bold text-xl border-b border-slate-700">
          TSM99 Platform
        </div>
        <nav className="flex-1 px-2 py-4 space-y-2">
          <a href="/dashboard" className="block px-4 py-2 rounded hover:bg-slate-800">Dashboard</a>
          <a href="/projects" className="block px-4 py-2 rounded hover:bg-slate-800">Projects</a>
          <a href="/logs" className="block px-4 py-2 rounded hover:bg-slate-800">Logs</a>
          <a href="/playbooks" className="block px-4 py-2 rounded hover:bg-slate-800">Playbooks</a>
          <a href="/settings" className="block px-4 py-2 rounded hover:bg-slate-800">Settings</a>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-white border-b flex items-center justify-between px-6">
          <h1 className="text-lg font-semibold">Dashboard</h1>
          <div className="flex items-center space-x-4">
             {/* User profile placeholder */}
             <div className="w-8 h-8 bg-gray-300 rounded-full"></div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
