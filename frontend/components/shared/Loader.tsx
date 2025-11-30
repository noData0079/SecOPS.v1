"use client";

import React from "react";
import clsx from "clsx";

export type LoaderSize = "xs" | "sm" | "md" | "lg";
export type LoaderVariant = "primary" | "neutral" | "white";

export interface LoaderProps {
  size?: LoaderSize;
  variant?: LoaderVariant;
  label?: string;
  center?: boolean; // center horizontally & vertically
  className?: string;
}

/* -------------------------------------------------------------------------- */
/*                                Size Classes                                */
/* -------------------------------------------------------------------------- */

const sizeClassMap: Record<LoaderSize, string> = {
  xs: "h-3 w-3",
  sm: "h-4 w-4",
  md: "h-6 w-6",
  lg: "h-10 w-10",
};

/* -------------------------------------------------------------------------- */
/*                              Color Variants                                 */
/* -------------------------------------------------------------------------- */

const variantClassMap: Record<LoaderVariant, string> = {
  primary: "border-neutral-900 border-t-transparent",
  neutral: "border-neutral-400 border-t-transparent",
  white: "border-white border-t-transparent",
};

/* -------------------------------------------------------------------------- */
/*                                 Component                                   */
/* -------------------------------------------------------------------------- */

const Loader: React.FC<LoaderProps> = ({
  size = "md",
  variant = "primary",
  label,
  center = false,
  className,
}) => {
  const spinner = (
    <div
      className={clsx(
        "animate-spin rounded-full border-2",
        sizeClassMap[size],
        variantClassMap[variant],
        className
      )}
    />
  );

  return (
    <div
      className={clsx("flex items-center gap-2", {
        "justify-center w-full h-full": center,
      })}
    >
      {spinner}
      {label && (
        <span className="text-sm text-neutral-600 font-medium">{label}</span>
      )}
    </div>
  );
};

export default Loader;
