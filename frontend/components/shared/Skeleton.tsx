"use client";

import React from "react";
import clsx from "clsx";

export type SkeletonVariant = "rect" | "text" | "circle";

export interface SkeletonProps {
  variant?: SkeletonVariant;
  width?: number | string;
  height?: number | string;
  lines?: number;            // for text variant: number of lines
  className?: string;
}

/* -------------------------------------------------------------------------- */
/*                                  Helpers                                   */
/* -------------------------------------------------------------------------- */

function toSize(value?: number | string): string | undefined {
  if (value === undefined) return undefined;
  if (typeof value === "number") return `${value}px`;
  return value;
}

/* -------------------------------------------------------------------------- */
/*                                Main Component                              */
/* -------------------------------------------------------------------------- */

const Skeleton: React.FC<SkeletonProps> = ({
  variant = "rect",
  width,
  height,
  lines,
  className,
}) => {
  const style: React.CSSProperties = {
    width: toSize(width),
    height: toSize(height),
  };

  // Multi-line text skeleton
  if (variant === "text" && lines && lines > 1) {
    return (
      <div className={clsx("space-y-2", className)}>
        {Array.from({ length: lines }).map((_, idx) => (
          <div
            key={idx}
            className={clsx(
              "pulse rounded-md bg-neutral-200",
              idx === lines - 1 ? "w-2/3" : "w-full",
              "h-3"
            )}
          />
        ))}
      </div>
    );
  }

  // Single element skeleton
  return (
    <div
      className={clsx(
        "pulse bg-neutral-200",
        variant === "circle" ? "rounded-full" : "rounded-md",
        !height && variant === "text" && "h-3",
        className
      )}
      style={style}
    />
  );
};

export default Skeleton;
