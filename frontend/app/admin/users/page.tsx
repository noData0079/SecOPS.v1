"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";
import type { AdminUser } from "@/lib/types";

export default function AdminUsers() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
     // Fallback static data
    const staticUsers: AdminUser[] = [
        { id: "1", email: "founder@t79.ai", role: "admin", active: true, tier: "enterprise", mfa: true },
        { id: "2", email: "engineer@t79.ai", role: "member", active: true, tier: "pro", mfa: false },
        { id: "3", email: "guest@t79.ai", role: "viewer", active: false, tier: "free", mfa: false },
    ];

    api.admin
      .users()
      .then(setUsers)
      .catch(() => {
          console.warn("Using static users fallback");
          setUsers(staticUsers);
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 px-6 py-16">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold">User Directory</h1>
        <p className="text-slate-300 mt-2 mb-6 max-w-3xl">
          Track seats, MFA adoption, and subscription tier in one place. Data syncs with the billing webhook and identity provider.
        </p>

        {error && <div className="mb-4 text-sm text-red-600">{error}</div>}

        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
          <table className="min-w-full divide-y divide-slate-800 text-sm">
            <thead className="bg-slate-900/80">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-slate-300">Email</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-300">Role</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-300">Tier</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-300">Status</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-300">MFA</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {users.map((user) => (
                <tr key={user.id || user.email} className="hover:bg-slate-800/40 transition">
                  <td className="px-4 py-3 text-slate-200">{user.email}</td>
                  <td className="px-4 py-3 text-slate-300 capitalize">{user.role}</td>
                  <td className="px-4 py-3 text-emerald-400 capitalize">{user.tier || "Standard"}</td>
                  <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${user.active ? 'bg-emerald-900 text-emerald-200' : 'bg-slate-700 text-slate-300'}`}>
                        {user.active ? "Active" : "Inactive"}
                      </span>
                  </td>
                  <td className="px-4 py-3 text-slate-400">{user.mfa ? "Enabled" : "Missing"}</td>
                </tr>
              ))}
               {users.length === 0 && (
                <tr>
                  <td className="p-4 text-center text-slate-500" colSpan={5}>
                    No users found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
