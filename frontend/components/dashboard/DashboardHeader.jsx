"use client";

import { useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { ChevronDown, LogOut, Menu } from "lucide-react";
import ThemeToggle from "@/components/shared/ThemeToggle";
import { useAuth } from "@/hooks/useAuth";

const TITLES = {
  "/student-dashboard": "Overview",
  "/student-dashboard/profile": "Profile",
  "/student-dashboard/resume": "Resume",
  "/student-dashboard/jobs": "Job Matches",
  "/student-dashboard/saved-jobs": "Saved Jobs",
  "/student-dashboard/applications": "Applications",
  "/student-dashboard/career-insights": "Career Insights",
};

function initialsFor(name) {
  return (name || "U")
    .split(/\s+/)
    .map((part) => part[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export default function DashboardHeader({ onOpenMenu = null }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, signOut } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  const title = TITLES[pathname] ?? "Dashboard";

  const handleLogout = () => {
    signOut();
    setMenuOpen(false);
    router.push("/");
    router.refresh();
  };

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between gap-3 border-b border-line bg-canvas/85 px-4 py-3 backdrop-blur-md sm:px-6">
      <div className="flex min-w-0 items-center gap-2">
        <button
          type="button"
          id="dashboard-mobile-menu"
          onClick={onOpenMenu}
          aria-label="Open navigation menu"
          aria-haspopup="dialog"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-line bg-surface text-navy transition-colors hover:bg-elevated sm:hidden"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="min-w-0">
          <p className="truncate text-[10px] font-semibold uppercase tracking-[0.18em] text-muted">
            Student Dashboard
          </p>
          <h1 className="truncate text-lg font-bold tracking-tight text-navy">
            {title}
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <ThemeToggle variant="solid" />

        <div className="relative">
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            className="flex items-center gap-2 rounded-xl border border-line bg-surface py-1.5 pl-1.5 pr-3 shadow-sm transition-colors hover:bg-elevated"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/15 text-xs font-bold text-accent">
              {initialsFor(user?.name)}
            </span>
            <span className="hidden max-w-[120px] truncate text-sm font-medium text-navy sm:block">
              {user?.name || "Account"}
            </span>
            <ChevronDown className="h-3.5 w-3.5 text-muted" />
          </button>

          {menuOpen && (
            <>
              <button
                type="button"
                aria-hidden="true"
                tabIndex={-1}
                onClick={() => setMenuOpen(false)}
                className="fixed inset-0 z-10 cursor-default"
              />
              <div
                role="menu"
                className="absolute right-0 z-20 mt-2 w-56 animate-scale-in overflow-hidden rounded-xl border border-line bg-surface shadow-card-hover"
              >
                <div className="border-b border-line-subtle px-4 py-3">
                  <p className="truncate text-sm font-semibold text-navy">
                    {user?.name || "Account"}
                  </p>
                  <p className="mt-0.5 truncate text-xs text-muted">
                    {user?.email || "Signed in"}
                  </p>
                </div>
                <button
                  type="button"
                  role="menuitem"
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 px-4 py-2.5 text-sm font-medium text-danger transition-colors hover:bg-danger/5"
                >
                  <LogOut className="h-4 w-4" />
                  Log out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}