"use client";

import React from "react";
import clsx from "clsx";

export type IssueStatus = "open" | "acknowledged" | "resolved" | "ignored";

export interface IssueStatusIndicatorProps {
  status: IssueStatus;
  showLabel?: boolean;     // if false = dot only (good for compact UI)
  size?: "sm" | "md";      // indicator size
  className?: string;
}

/* -------------------------------------------------------------------------- */
/*                                 Color Map                                   */
/* -------------------------------------------------------------------------- */

const statusColorMap: Record<IssueStatus, string> = {
  open: "bg-red-500",
  acknowledged: "bg-yellow-500",
  resolved: "bg-green-500",
  ignored: "bg-gray-400",
};

/* -------------------------------------------------------------------------- */
/*                               Size Settings                                */
/* -------------------------------------------------------------------------- */

const dotSizeMap = {
  sm: "h-2.5 w-2.5",
  md: "h-3 w-3",
};

/* -------------------------------------------------------------------------- */
/*                                  Component                                  */
/* -------------------------------------------------------------------------- */

const IssueStatusIndicator: React.FC<IssueStatusIndicatorProps> = ({
  status,
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
          statusColorMap[status],
          dotSizeMap[size]
        )}
      />

      {showLabel && (
        <span className="text-sm text-neutral-700 font-medium capitalize">
          {status}
        </span>
      )}
    </div>
  );
};

export default IssueStatusIndicator;
