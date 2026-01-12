import React from 'react';

export default function AdminProjectsPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-slate-800">Global Projects</h2>
      <div className="space-y-4">
        <div className="bg-white p-4 rounded-lg border shadow-sm flex justify-between items-center">
           <div>
             <h3 className="font-bold">Project Alpha</h3>
             <p className="text-sm text-gray-500">Owner: alice@example.com</p>
           </div>
           <div className="flex gap-2">
             <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded font-bold">High Risk</span>
           </div>
        </div>
        <div className="bg-white p-4 rounded-lg border shadow-sm flex justify-between items-center">
           <div>
             <h3 className="font-bold">Project Beta</h3>
             <p className="text-sm text-gray-500">Owner: charlie@example.com</p>
           </div>
           <div className="flex gap-2">
             <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded font-bold">Low Risk</span>
           </div>
        </div>
      </div>
    </div>
  );
}
