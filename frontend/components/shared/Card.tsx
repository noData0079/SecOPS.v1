"use client";

import React from "react";
import clsx from "clsx";

export type CardVariant = "default" | "subtle" | "outlined" | "hover";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  padding?: "none" | "sm" | "md" | "lg";
  rounded?: "md" | "lg" | "xl";
  clickable?: boolean;
  shadow?: "none" | "sm" | "md";
  children: React.ReactNode;
  className?: string;
}

/* -------------------------------------------------------------------------- */
/*                               Variant classes                               */
/* -------------------------------------------------------------------------- */

const variantClasses: Record<CardVariant, string> = {
  default: "bg-white border border-neutral-200",
  subtle: "bg-neutral-50 border border-neutral-200",
  outlined: "bg-white border border-neutral-300",
  hover:
    "bg-white border border-neutral-200 hover:shadow-md transition-shadow cursor-pointer",
};

/* -------------------------------------------------------------------------- */
/*                               Padding classes                               */
/* -------------------------------------------------------------------------- */

const paddingClasses = {
  none: "p-0",
  sm: "p-3",
  md: "p-4",
  lg: "p-6",
};

/* -------------------------------------------------------------------------- */
/*                               Rounded classes                                */
/* -------------------------------------------------------------------------- */

const roundedClasses = {
  md: "rounded-md",
  lg: "rounded-lg",
  xl: "rounded-xl",
};

/* -------------------------------------------------------------------------- */
/*                                Shadow classes                                */
/* -------------------------------------------------------------------------- */

const shadowClasses = {
  none: "",
  sm: "shadow-sm",
  md: "shadow-md",
};

/* -------------------------------------------------------------------------- */
/*                                   Component                                 */
/* -------------------------------------------------------------------------- */

const Card: React.FC<CardProps> = ({
  variant = "default",
  padding = "md",
  rounded = "xl",
  clickable = false,
  shadow = "sm",
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={clsx(
        "w-full",
        variantClasses[variant],
        paddingClasses[padding],
        roundedClasses[rounded],
        shadowClasses[shadow],
        {
          "cursor-pointer hover:shadow-md transition-all": clickable,
        },
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
