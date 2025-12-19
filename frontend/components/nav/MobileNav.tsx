"use client";

import { useState } from "react";
import NavItem from "./NavItem";

type MobileNavItem = {
  href: string;
  label: string;
  icon?: React.ReactNode;
};

type MobileNavProps = {
  items: MobileNavItem[];
};

/**
 * MobileNav
 *
 * Fully responsive collapsible navigation used on mobile.
 * Accepts an array of nav items and renders them using NavItem.
 */

export default function MobileNav({ items }: MobileNavProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Floating mobile toggle button */}
      <button
        onClick={() => setOpen(!open)}
        className="md:hidden fixed bottom-6 right-6 z-50 rounded-full bg-slate-900 text-white p-3 shadow-lg focus:outline-none"
      >
        <svg
          className="h-6 w-6"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          {open ? (
            <path d="M6 18L18 6M6 6l12 12" /> // X icon
          ) : (
            <path d="M4 6h16M4 12h16M4 18h16" /> // Menu icon
          )}
        </svg>
      </button>

      {/* Slide-in mobile nav panel */}
      <div
        className={`fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
        onClick={() => setOpen(false)}
      />

      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 transform bg-white border-r border-slate-200 shadow-xl transition-transform duration-300 md:hidden ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="p-6 flex flex-col h-full space-y-6">
          <div className="flex flex-col gap-1">
            <h2 className="text-lg font-semibold tracking-tight text-slate-900">
              T79 Menu
            </h2>
            <p className="text-xs text-slate-500">Navigation</p>
          </div>

          <nav className="space-y-1 flex-1">
            {items.map((item) => (
              <NavItem
                key={item.href}
                href={item.href}
                label={item.label}
                icon={item.icon}
                onClick={() => setOpen(false)}
              />
            ))}
          </nav>

          <div className="text-xs text-slate-500 border-t pt-4 mt-auto">
            T79AI v1.0.0  
            <br />
            <span className="text-slate-400">MVP Preview</span>
          </div>
        </div>
      </aside>
    </>
  );
}
