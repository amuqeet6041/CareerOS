"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/components/shared/ThemeProvider";

export default function ThemeToggle({
  variant = "ghost",
  className = "",
}) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // SSR always renders the light state (identical to any stored theme), so
  // theme-dependent markup must not change during hydration. Gate on
  // `mounted` and reconcile a frame after mount to avoid React hydration
  // mismatches for dark-theme users.
  useEffect(() => {
    setMounted(true);
  }, []);

  const isDark = mounted && theme === "dark";

  const base =
    "relative inline-flex items-center justify-center rounded-xl text-sm font-medium transition-all duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-bright/60 active:scale-95";

  const variants = {
    ghost:
      "h-10 w-10 text-muted hover:bg-elevated hover:text-navy",
    solid:
      "h-10 w-10 border border-line bg-surface text-muted shadow-sm hover:border-line hover:bg-elevated hover:text-navy",
    soft:
      "h-10 w-10 text-navy/70 hover:bg-elevated hover:text-navy",
  };

  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label={isDark ? "Switch to light theme" : "Switch to dark theme"}
      title={isDark ? "Switch to light theme" : "Switch to dark theme"}
      className={`${base} ${variants[variant] ?? variants.ghost} ${className}`}
    >
      <span className="relative block h-5 w-5 overflow-hidden">
        <Sun
          className={`absolute inset-0 h-5 w-5 transition-all duration-300 ${
            isDark
              ? "translate-y-0 rotate-0 opacity-100"
              : "translate-y-6 rotate-90 opacity-0"
          }`}
          strokeWidth={2}
        />
        <Moon
          className={`absolute inset-0 h-5 w-5 transition-all duration-300 ${
            isDark
              ? "-translate-y-6 -rotate-90 opacity-0"
              : "translate-y-0 rotate-0 opacity-100"
          }`}
          strokeWidth={2}
        />
      </span>
      <span className="sr-only">
        {isDark ? "Dark theme active" : "Light theme active"}
      </span>
    </button>
  );
}