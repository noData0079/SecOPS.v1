"use client";

import React from "react";
import clsx from "clsx";

export interface TabItem {
  id: string;               // ex: "overview"
  label: string;            // ex: "Overview"
  disabled?: boolean;
  icon?: React.ReactNode;   // optional React icon
  count?: number;           // optional badge count
}

export interface TabsProps {
  tabs: TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  className?: string;
  size?: "sm" | "md";
}

/* -------------------------------------------------------------------------- */
/*                                    Tabs                                    */
/* -------------------------------------------------------------------------- */

const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeId,
  onChange,
  className,
  size = "md",
}) => {
  return (
    <div className={clsx("border-b border-neutral-200", className)}>
      <div className="flex gap-2 overflow-x-auto scrollbar-none">
        {tabs.map((tab) => {
          const isActive = tab.id === activeId;

          return (
            <button
              key={tab.id}
              type="button"
              disabled={tab.disabled}
              onClick={() => !tab.disabled && onChange(tab.id)}
              className={clsx(
                "relative inline-flex items-center gap-2 whitespace-nowrap rounded-md transition-colors",
                size === "sm" ? "px-2 py-1.5 text-sm" : "px-3 py-2 text-sm",
                isActive
                  ? "border-b-2 border-neutral-900 text-neutral-900"
                  : "border-b-2 border-transparent text-neutral-500 hover:text-neutral-800 hover:border-neutral-200",
                tab.disabled && "opacity-50 cursor-not-allowed"
              )}
            >
              {tab.icon && (
                <span
                  className={clsx(
                    "flex items-center",
                    isActive ? "text-blue-500" : "text-neutral-500"
                  )}
                >
                  {tab.icon}
                </span>
              )}

              <span>{tab.label}</span>

              {typeof tab.count === "number" && tab.count > 0 && (
                <span className="px-1.5 py-0.5 text-[11px] bg-neutral-200 rounded-full text-neutral-700 font-semibold">
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default Tabs;
