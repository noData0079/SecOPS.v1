"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import * as React from "react";

type NavItemProps = {
  href: string;
  label: string;
  icon?: React.ReactNode;
  /**
   * Optional explicit active flag.
   * If not provided, we infer it from the current pathname.
   */
  isActiveOverride?: boolean;
  /**
   * Optional callback for click (e.g. close mobile menu).
   */
  onClick?: () => void;
};

/**
 * NavItem
 *
 * Generic navigation item that:
 * - Highlights when current route matches href
 * - Supports optional icon
 * - Works for sidebar or top nav
 */
export default function NavItem({
  href,
  label,
  icon,
  isActiveOverride,
  onClick,
}: NavItemProps) {
  const pathname = usePathname();

  const inferredActive =
    pathname === href || (href !== "/" && pathname?.startsWith(href + "/"));

  const active = isActiveOverride ?? inferredActive;

  return (
    <Link
      href={href}
      onClick={onClick}
      className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition ${
        active
          ? "bg-slate-900 text-white shadow-sm"
          : "text-slate-700 hover:bg-slate-100"
      }`}
    >
      {icon && <span className="h-4 w-4 flex items-center justify-center">{icon}</span>}
      <span>{label}</span>
    </Link>
  );
}
