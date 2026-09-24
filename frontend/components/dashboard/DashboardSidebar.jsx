"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bookmark,
  ChevronDown,
  FileText,
  LayoutDashboard,
  Send,
  Sparkles,
  Target,
  TrendingUp,
  UserRound,
  X,
} from "lucide-react";

const LINKS = [
  { href: "/student-dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/student-dashboard/profile", label: "Profile", icon: UserRound },
  { href: "/student-dashboard/resume", label: "Resume", icon: FileText },
  { href: "/student-dashboard/jobs", label: "Job Matches", icon: Target },
  { href: "/student-dashboard/saved-jobs", label: "Saved Jobs", icon: Bookmark },
  { href: "/student-dashboard/applications", label: "Applications", icon: Send },
  {
    href: "/student-dashboard/career-insights",
    label: "Career Insights",
    icon: TrendingUp,
  },
];

function Brand() {
  return (
    <Link href="/" className="flex items-center gap-2.5">
      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-accent-light shadow-glow-primary">
        <Sparkles className="h-4 w-4 text-white" strokeWidth={2.2} />
      </div>
      <div className="flex flex-col leading-none">
        <span className="text-[16px] font-semibold tracking-tight text-navy">
          Career<span className="text-accent">OS</span>
        </span>
        <span className="mt-1 text-[9px] font-medium uppercase tracking-[0.18em] text-muted">
          Student Platform
        </span>
      </div>
    </Link>
  );
}

function NavList({ pathname, onNavigate = null, stagger = false }) {
  return (
    <nav className="space-y-1 px-3" aria-label="Dashboard navigation">
      {LINKS.map((link, index) => {
        const active = pathname === link.href;
        const Icon = link.icon;

        return (
          <Link
            key={link.href}
            href={link.href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            style={
              stagger ? { animationDelay: `${90 + index * 45}ms` } : undefined
            }
            className={`group flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-colors duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-bright/60 ${
              stagger ? "animate-fade-in-up" : ""
            } ${
              active
                ? "bg-accent/10 text-accent"
                : "text-navy/70 hover:bg-elevated hover:text-navy"
            }`}
          >
            <Icon
              className={`h-4 w-4 shrink-0 transition-colors duration-200 ${
                active ? "text-accent" : "text-muted group-hover:text-navy"
              }`}
            />
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}

function FooterCard() {
  return (
    <div className="mx-5 mb-[max(0.75rem,env(safe-area-inset-bottom))] mt-2 rounded-xl border border-line bg-elevated p-4">
      <p className="text-xs font-semibold text-navy">AI-powered career platform</p>
      <p className="mt-1 text-xs leading-5 text-muted">
        Resume analysis, job matching, and insights in one place.
      </p>
    </div>
  );
}

export default function DashboardSidebar({ open = false, onClose = null }) {
  const pathname = usePathname();
  const panelRef = useRef(null);
  const closeButtonRef = useRef(null);

  // Escape closes the drawer; body scroll is locked while it is open.
  useEffect(() => {
    if (!open) return;
    const onKey = (event) => {
      if (event.key === "Escape") onClose?.();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  // Focus the close button when it opens; return focus to the hamburger on close.
  useEffect(() => {
    if (open) {
      // wait a frame so the panel is interactive
      const id = window.setTimeout(() => closeButtonRef.current?.focus(), 30);
      return () => window.clearTimeout(id);
    }
    const trigger = document.getElementById("dashboard-mobile-menu");
    if (document.activeElement === document.body && trigger) trigger.focus();
  }, [open]);

  const trapFocus = (event) => {
    if (event.key !== "Tab") return;
    const panel = panelRef.current;
    if (!panel) return;
    const focusables = panel.querySelectorAll(
      'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    if (focusables.length === 0) return;
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  return (
    <>
      {/* Desktop sidebar (fixed; content column is offset with sm:pl-64) */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-line bg-surface sm:flex">
        <div className="flex items-center justify-between px-5 py-5">
          <Brand />
          <span className="relative inline-flex items-center rounded-full border border-accent/25 bg-accent/10 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-[0.14em] text-accent">
            <ChevronDown className="mr-0.5 h-2.5 w-2.5 -rotate-90" />
            Student
          </span>
        </div>

        <div className="flex-1 overflow-y-auto pb-4">
          <NavList pathname={pathname} />
        </div>

        <FooterCard />
      </aside>

      {/* Mobile drawer + overlay (stays in the DOM so exit transitions play) */}
      <div
        aria-hidden="true"
        onClick={onClose}
        className={`fixed inset-0 z-40 bg-black/55 backdrop-blur-sm transition-opacity duration-200 sm:hidden ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      />
      <aside
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label="Dashboard navigation"
        aria-hidden={!open}
        onKeyDown={trapFocus}
        className={`fixed inset-y-0 left-0 z-50 flex w-[280px] max-w-[85vw] flex-col bg-surface shadow-2xl shadow-black/20 transition-transform duration-300 ease-out motion-reduce:transition-none sm:hidden ${
          open ? "translate-x-0" : "-translate-x-full"
        } pb-[env(safe-area-inset-bottom)]`}
      >
        <div className="flex shrink-0 items-center justify-between px-5 pb-4 pt-5">
          <Brand />
          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            aria-label="Close navigation menu"
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-line bg-elevated text-navy transition-colors hover:bg-elevated-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-bright/60"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto pt-2">
          <NavList pathname={pathname} onNavigate={onClose} stagger />
        </div>

        <FooterCard />
      </aside>
    </>
  );
}