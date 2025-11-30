"use client";

import React from "react";
import clsx from "clsx";

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;        // e.g. <Button>Create Issue</Button>
  className?: string;
  fullHeight?: boolean;            // center vertically
  variant?: "default" | "card";    // card background
}

const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  action,
  className,
  fullHeight = true,
  variant = "default",
}) => {
  return (
    <div
      className={clsx(
        "flex flex-col items-center text-center px-6",
        fullHeight && "justify-center py-20",
        variant === "card" &&
          "border border-neutral-200 bg-white shadow-sm rounded-xl py-14",
        className
      )}
    >
      {/* Icon */}
      {icon && (
        <div className="mb-4 text-neutral-400">
          <div className="[&>*]:h-10 [&>*]:w-10">{icon}</div>
        </div>
      )}

      {/* Title */}
      <h2 className="text-lg font-semibold text-neutral-900">{title}</h2>

      {/* Description */}
      {description && (
        <p className="text-sm text-neutral-600 mt-2 max-w-md">{description}</p>
      )}

      {/* Action */}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
};

export default EmptyState;
