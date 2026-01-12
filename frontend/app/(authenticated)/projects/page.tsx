import React from 'react';

export default function ProjectsPage() {
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Projects</h2>
        <button className="bg-slate-900 text-white px-4 py-2 rounded hover:bg-slate-800">New Project</button>
      </div>

      <div className="grid gap-4">
        <div className="bg-white p-6 rounded-lg border shadow-sm flex justify-between items-center">
          <div>
            <h3 className="text-lg font-bold">Production Alpha</h3>
            <p className="text-sm text-gray-500">Last active: 2 hours ago</p>
          </div>
          <div className="flex space-x-2">
            <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">Healthy</span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border shadow-sm flex justify-between items-center">
          <div>
            <h3 className="text-lg font-bold">Staging Beta</h3>
            <p className="text-sm text-gray-500">Last active: 5 mins ago</p>
          </div>
          <div className="flex space-x-2">
             <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium">Running</span>
          </div>
        </div>
      </div>
    </div>
  );
}
