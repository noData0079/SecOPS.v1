"use client";
import React, { useEffect, useState } from 'react';
import { api } from "@/lib/api-client";

interface AdminOverviewData {
  platform_health: string;
  active_users: number;
  system_load: number;
  active_agents: number;
}

export default function AdminOverviewPage() {
  const [data, setData] = useState<AdminOverviewData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/admin/overview")
      .then(setData)
      .catch((err) => console.error("Failed to fetch admin overview", err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;
  if (!data) return <div>Error loading data.</div>;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6 text-slate-800">Admin Overview</h2>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-l-4 border-l-green-500">
          <h3 className="text-sm font-medium text-gray-500 uppercase">System Health</h3>
          <p className="text-2xl font-bold mt-2 text-green-700">{data.platform_health}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-sm font-medium text-gray-500 uppercase">Active Users</h3>
          <p className="text-2xl font-bold mt-2">{data.active_users}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-sm font-medium text-gray-500 uppercase">System Load</h3>
          <p className="text-2xl font-bold mt-2">{data.system_load}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <h3 className="text-sm font-medium text-gray-500 uppercase">Active Agents</h3>
          <p className="text-2xl font-bold mt-2">{data.active_agents}</p>
        </div>
      </div>
    </div>
  );
}
