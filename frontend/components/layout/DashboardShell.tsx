// frontend/components/layout/DashboardShell.tsx

import * as React from "react";

type DashboardShellProps = {
  children: React.ReactNode;
};

/**
 * DashboardShell
 *
 * A simple, consistent wrapper for all console pages.
 * Gives you:
 * - proper background
 * - max-width
 * - horizontal padding
 * - vertical spacing
 */
export function DashboardShell({ children }: DashboardShellProps) {
  return (
    <div className="min-h-[calc(100vh-64px)] bg-gray-50">
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {children}
      </div>
    </div>
  );
}
