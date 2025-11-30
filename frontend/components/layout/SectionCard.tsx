// frontend/components/layout/SectionCard.tsx

import * as React from "react";

type SectionCardProps = {
  title: string;
  description?: string;
  // Optional label in top-right (e.g. status, badge, etc.)
  meta?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
};

/**
 * SectionCard
 *
 * Generic card used for settings sections, panels, etc.
 * Keeps style uniform across GitHub/K8s/LLM/Billing blocks.
 */
export function SectionCard({
  title,
  description,
  meta,
  children,
  className = "",
}: SectionCardProps) {
  return (
    <section
      className={`rounded-xl border border-slate-200 bg-white p-4 shadow-sm space-y-3 ${className}`}
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
          {description && (
            <p className="text-[11px] text-slate-600">{description}</p>
          )}
        </div>
        {meta && <div className="shrink-0">{meta}</div>}
      </div>

      <div>{children}</div>
    </section>
  );
}
