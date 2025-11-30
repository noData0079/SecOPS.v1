"use client";

import React from "react";
import clsx from "clsx";

export type IssueSeverity = "info" | "low" | "medium" | "high" | "critical";

export interface IssueSeverityIndicatorProps {
  severity: IssueSeverity;
  showLabel?: boolean;      // if false → dot only
  size?: "sm" | "md";       // size of the dot
  className?: string;
}

/* -------------------------------------------------------------------------- */
/*                                 Color Map                                  */
/* -------------------------------------------------------------------------- */

const severityColorMap: Record<IssueSeverity, string> = {
  info: "bg-blue-500",
  low: "bg-green-500",
  medium: "bg-yellow-500",
  high: "bg-orange-500",
  critical: "bg-red-600",
};

/* -------------------------------------------------------------------------- */
/*                                Size Settings                               */
/* -------------------------------------------------------------------------- */

const dotSizeMap = {
  sm: "h-2.5 w-2.5",
  md: "h-3 w-3",
};

/* -------------------------------------------------------------------------- */
/*                                  Component                                  */
/* -------------------------------------------------------------------------- */

const IssueSeverityIndicator: React.FC<IssueSeverityIndicatorProps> = ({
  severity,
  showLabel = true,
  size = "md",
  className,
}) => {
  return (
    <div className={clsx("flex items-center gap-2", className)}>
      {/* Dot */}
      <span
        className={clsx(
          "rounded-full",
          severityColorMap[severity],
          dotSizeMap[size]
        )}
      />

      {showLabel && (
        <span className="text-sm text-neutral-700 font-medium capitalize">
          {severity}
        </span>
      )}
    </div>
  );
};

export default IssueSeverityIndicator;
