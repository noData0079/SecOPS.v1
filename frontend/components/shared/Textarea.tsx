"use client";

import React from "react";
import clsx from "clsx";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  rows?: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const Textarea: React.FC<TextareaProps> = ({
  label,
  error,
  rows = 4,
  size = "md",
  className,
  ...props
}) => {
  const sizeClasses = {
    sm: "text-sm px-2 py-2",
    md: "text-sm px-3 py-2.5",
    lg: "text-base px-4 py-3",
  };

  return (
    <div className={clsx("flex flex-col gap-1 w-full", className)}>
      {/* Label */}
      {label && (
        <label className="text-sm font-medium text-neutral-700">
          {label}
        </label>
      )}

      {/* Textarea */}
      <textarea
        rows={rows}
        className={clsx(
          "w-full rounded-md border outline-none transition-colors resize-none",
          "bg-white text-neutral-900 placeholder-neutral-400",
          sizeClasses[size],
          error
            ? "border-red-500 focus:border-red-500 focus:ring-red-200"
            : "border-neutral-300 focus:border-neutral-900 focus:ring-neutral-200",
          "focus:ring-2",
          props.disabled && "opacity-60 cursor-not-allowed"
        )}
        {...props}
      />

      {/* Error Message */}
      {error && (
        <span className="text-xs text-red-600 mt-0.5">{error}</span>
      )}
    </div>
  );
};

export default Textarea;
