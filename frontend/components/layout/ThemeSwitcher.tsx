"use client";

import { useEffect, useState } from "react";

/**
 * ThemeSwitcher
 *
 * Lightweight, dependency-free theme toggler supporting:
 * - Light mode
 * - Dark mode
 * - System preference
 *
 * Works with Tailwind's "dark" class strategy.
 */

export default function ThemeSwitcher() {
  const [theme, setTheme] = useState<"light" | "dark" | "system">("system");

  // Load theme from localStorage on hydration
  useEffect(() => {
    const stored = localStorage.getItem("theme");
    if (!stored) return;

    if (stored === "light" || stored === "dark" || stored === "system") {
      setTheme(stored);
      applyTheme(stored);
    }
  }, []);

  // Apply the theme to <html> element
  const applyTheme = (t: "light" | "dark" | "system") => {
    const root = window.document.documentElement;

    if (t === "light") {
      root.classList.remove("dark");
      return;
    }

    if (t === "dark") {
      root.classList.add("dark");
      return;
    }

    // system
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    if (prefersDark) root.classList.add("dark");
    else root.classList.remove("dark");
  };

  const handleChange = (t: "light" | "dark" | "system") => {
    setTheme(t);
    localStorage.setItem("theme", t);
    applyTheme(t);
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={() => handleChange("light")}
        className={`rounded-md px-2 py-1 text-xs border ${
          theme === "light"
            ? "bg-slate-900 text-white border-slate-900"
            : "bg-white text-slate-700 border-slate-200 hover:bg-slate-100"
        }`}
      >
        Light
      </button>

      <button
        onClick={() => handleChange("dark")}
        className={`rounded-md px-2 py-1 text-xs border ${
          theme === "dark"
            ? "bg-slate-900 text-white border-slate-900"
            : "bg-white text-slate-700 border-slate-200 hover:bg-slate-100"
        }`}
      >
        Dark
      </button>

      <button
        onClick={() => handleChange("system")}
        className={`rounded-md px-2 py-1 text-xs border ${
          theme === "system"
            ? "bg-slate-900 text-white border-slate-900"
            : "bg-white text-slate-700 border-slate-200 hover:bg-slate-100"
        }`}
      >
        System
      </button>
    </div>
  );
}
