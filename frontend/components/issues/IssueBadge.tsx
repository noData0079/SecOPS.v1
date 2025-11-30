"use client";

import React from "react";
import clsx from "clsx";

export type IssueSeverity = "info" | "low" | "medium" | "high" | "critical";
export type IssueStatus = "open" | "acknowledged" | "resolved" | "ignored";

export type IssueBadgeKind = "severity" | "status" | "source" | "target";

export interface IssueBadgeProps {
  kind: IssueBadgeKind;
  value: string;           // raw value, we handle styling based on kind
  className?: string;
}

/* -------------------------------------------------------------------------- */
/*                                  Mappings                                  */
/* -------------------------------------------------------------------------- */

const severityClassMap: Record<IssueSeverity, string> = {
  info: "bg-blue-100 text-blue-700 border-blue-300",
  low: "bg-green-100 text-green-700 border-green-300",
  medium: "bg-yellow-100 text-yellow-800 border-yellow-400",
  high: "bg-orange-100 text-orange-800 border-orange-400",
  critical: "bg-red-100 text-red-800 border-red-400",
};

const statusClassMap: Record<IssueStatus, string> = {
  open: "bg-red-100 text-red-700 border-red-300",
  acknowledged: "bg-yellow-100 text-yellow-800 border-yellow-300",
  resolved: "bg-green-100 text-green-700 border-green-300",
  ignored: "bg-gray-100 text-gray-600 border-gray-300",
};

function getBadgeClasses(kind: IssueBadgeKind, value: string): string {
  if (kind === "severity") {
    const v = value.toLowerCase() as IssueSeverity;
    return severityClassMap[v] ?? "bg-gray-100 text-gray-700 border-gray-300";
  }

  if (kind === "status") {
    const v = value.toLowerCase() as IssueStatus;
    return statusClassMap[v] ?? "bg-gray-100 text-gray-700 border-gray-300";
  }

  // source / target – neutral pill style
  return "bg-neutral-100 text-neutral-600 border-neutral-300";
}

function formatLabel(kind: IssueBadgeKind, value: string): string {
  if (kind === "severity" || kind === "status") {
    return value.toUpperCase();
  }
  // source / target – Capitalize first letter
  return value.charAt(0).toUpperCase() + value.slice(1);
}

/* -------------------------------------------------------------------------- */
/*                                  Component                                 */
/* -------------------------------------------------------------------------- */

export const IssueBadge: React.FC<IssueBadgeProps> = ({
  kind,
  value,
  className,
}) => {
  const baseClasses =
    "inline-flex items-center px-2 py-0.5 rounded border text-xs font-medium";

  return (
    <span className={clsx(baseClasses, getBadgeClasses(kind, value), className)}>
      {formatLabel(kind, value)}
    </span>
  );
};

export default IssueBadge;
