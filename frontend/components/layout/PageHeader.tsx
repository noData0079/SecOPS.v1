// frontend/components/layout/PageHeader.tsx

import * as React from "react";

type PageHeaderProps = {
  title: string;
  description?: string;
  // Put buttons / filters / tags on the right side
  actions?: React.ReactNode;
  // Optional small label above title (e.g. "SecOps · Console")
  eyebrow?: string;
};

/**
 * PageHeader
 *
 * Standardized header for console pages.
 * Used to keep title + description + right side actions consistent.
 */
export function PageHeader({
  title,
  description,
  actions,
  eyebrow,
}: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && (
          <div className="mb-1 text-[11px] font-medium uppercase tracking-wide text-slate-500">
            {eyebrow}
          </div>
        )}
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          {title}
        </h1>
        {description && (
          <p className="mt-1 text-sm text-slate-600 max-w-xl">
            {description}
          </p>
        )}
      </div>

      {actions && (
        <div className="flex flex-wrap items-center gap-2">{actions}</div>
      )}
    </div>
  );
}
