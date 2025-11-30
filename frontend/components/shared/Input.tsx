"use client";

import React from "react";
import clsx from "clsx";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
  className?: string;
}

/* -------------------------------------------------------------------------- */
/*                                   Component                                 */
/* -------------------------------------------------------------------------- */

const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  fullWidth = true,
  className,
  ...props
}) => {
  return (
    <div className={clsx("flex flex-col gap-1", fullWidth && "w-full")}>
      {/* Label */}
      {label && (
        <label className="text-sm font-medium text-neutral-800">
          {label}
        </label>
      )}

      {/* Input Wrapper */}
      <div
        className={clsx(
          "relative flex items-center rounded-lg border bg-white",
          error
            ? "border-red-500"
            : "border-neutral-300 hover:border-neutral-400",
          "transition-colors"
        )}
      >
        {/* Left Icon */}
        {leftIcon && (
          <span className="absolute left-3 text-neutral-500 flex items-center">
            {leftIcon}
          </span>
        )}

        {/* Input Field */}
        <input
          className={clsx(
            "w-full bg-transparent text-sm text-neutral-900 outline-none",
            "placeholder-neutral-400",
            leftIcon ? "pl-10" : "pl-3",
            rightIcon ? "pr-10" : "pr-3",
            "py-2.5",
            className
          )}
          {...props}
        />

        {/* Right Icon */}
        {rightIcon && (
          <span className="absolute right-3 text-neutral-500 flex items-center">
            {rightIcon}
          </span>
        )}
      </div>

      {/* Error */}
      {error && (
        <span className="text-xs text-red-600 font-medium">{error}</span>
      )}

      {/* Helper Text */}
      {!error && helperText && (
        <span className="text-xs text-neutral-500">{helperText}</span>
      )}
    </div>
  );
};

export default Input;
