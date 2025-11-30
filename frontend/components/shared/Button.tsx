"use client";

import React from "react";
import clsx from "clsx";
import { Loader2 } from "lucide-react";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "outline"
  | "subtle"
  | "danger";

export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  className?: string;
}

/* -------------------------------------------------------------------------- */
/*                                 Variants                                    */
/* -------------------------------------------------------------------------- */

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-neutral-900 text-white hover:bg-neutral-800 border border-neutral-900",
  secondary:
    "bg-neutral-100 text-neutral-800 hover:bg-neutral-200 border border-neutral-300",
  outline:
    "bg-white text-neutral-800 border border-neutral-300 hover:bg-neutral-50",
  subtle:
    "bg-transparent text-neutral-700 hover:bg-neutral-100 border border-transparent",
  danger:
    "bg-red-600 text-white hover:bg-red-700 border border-red-700",
};

/* -------------------------------------------------------------------------- */
/*                                   Sizes                                     */
/* -------------------------------------------------------------------------- */

const sizeClasses: Record<ButtonSize, string> = {
  sm: "text-sm px-3 py-1.5 rounded-md",
  md: "text-sm px-4 py-2 rounded-lg",
  lg: "text-base px-5 py-3 rounded-xl",
};

/* -------------------------------------------------------------------------- */
/*                               Loader Spinner                                */
/* -------------------------------------------------------------------------- */

const Spinner = () => (
  <Loader2 className="animate-spin h-4 w-4 text-current" />
);

/* -------------------------------------------------------------------------- */
/*                                 Component                                   */
/* -------------------------------------------------------------------------- */

const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  fullWidth = false,
  leftIcon,
  rightIcon,
  className,
  ...props
}) => {
  const isDisabled = disabled || loading;

  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center font-medium transition-all select-none",
        variantClasses[variant],
        sizeClasses[size],
        {
          "w-full": fullWidth,
          "opacity-50 cursor-not-allowed": isDisabled,
        },
        className
      )}
      disabled={isDisabled}
      {...props}
    >
      {/* Left icon */}
      {leftIcon && !loading && (
        <span className="mr-2 flex items-center">{leftIcon}</span>
      )}

      {/* Loader */}
      {loading ? (
        <span className="flex items-center gap-2">
          <Spinner />
          {children && <span>{children}</span>}
        </span>
      ) : (
        children
      )}

      {/* Right icon */}
      {rightIcon && !loading && (
        <span className="ml-2 flex items-center">{rightIcon}</span>
      )}
    </button>
  );
};

export default Button;
