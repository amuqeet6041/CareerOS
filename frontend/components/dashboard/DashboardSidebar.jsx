"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/student-dashboard", label: "Overview" },
  { href: "/student-dashboard/profile", label: "Profile" },
  { href: "/student-dashboard/resume", label: "Resume" },
  { href: "/student-dashboard/jobs", label: "Job Matches" },
  { href: "/student-dashboard/saved-jobs", label: "Saved Jobs" },
  { href: "/student-dashboard/applications", label: "Applications" },
  { href: "/student-dashboard/career-insights", label: "Career Insights" },
];

function NavList({ pathname, onNavigate }) {
  return (
    <nav className="space-y-1 px-3 pb-4">
      {LINKS.map((link) => {
        const active = pathname === link.href;
        return (
          <Link
            key={link.href}
            href={link.href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={`block rounded-md px-3 py-2 text-sm font-medium ${
              active
                ? "bg-blue-50 text-[#3B82F6]"
                : "text-navy/70 hover:bg-surface hover:text-navy"
            }`}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}

export default function DashboardSidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Mobile navigation (sidebar is hidden below sm, so this supplies a menu) */}
      <div className="w-full border-b border-border bg-white sm:hidden">
        <button
          type="button"
          onClick={() => setMobileOpen((open) => !open)}
          aria-expanded={mobileOpen}
          className="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold text-navy"
        >
          <span>CareerOS &mdash; Menu</span>
          <span className="text-xs font-medium text-navy/60">
            {mobileOpen ? "Close" : "Open"}
          </span>
        </button>
        {mobileOpen && (
          <div className="border-t border-border pt-2">
            <NavList pathname={pathname} onNavigate={() => setMobileOpen(false)} />
          </div>
        )}
      </div>

      {/* Desktop sidebar */}
      <aside className="hidden w-60 shrink-0 border-r border-border bg-white sm:block">
        <div className="px-6 py-5 text-lg font-bold text-navy">CareerOS</div>
        <NavList pathname={pathname} />
      </aside>
    </>
  );
}