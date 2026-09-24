"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Menu, Sparkles, X } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import ThemeToggle from "@/components/shared/ThemeToggle";

export default function Navbar() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, signOut } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleSignOut = () => {
    signOut();
    setMobileOpen(false);
    router.push("/");
    router.refresh();
  };

  const closeMobileMenu = () => {
    setMobileOpen(false);
  };

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="mx-auto max-w-7xl px-4 pt-4 sm:px-6 lg:px-8">
        <nav className="relative rounded-2xl border border-line bg-surface/90 px-4 py-3 shadow-card backdrop-blur-xl sm:px-6">
          {/* Subtle accent glow */}
          <div className="pointer-events-none absolute -inset-px rounded-2xl bg-gradient-to-r from-primary/10 via-transparent to-accent/10 opacity-70" />

          <div className="relative flex items-center justify-between gap-3">
            {/* Logo */}
            <Link
              href="/"
              className="group flex items-center gap-2.5"
              onClick={closeMobileMenu}
            >
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-accent-light shadow-glow-primary transition-transform duration-300 group-hover:scale-105">
                <Sparkles className="h-4 w-4 text-white" strokeWidth={2.2} />
              </div>

              <div className="flex flex-col leading-none">
                <span className="text-[17px] font-semibold tracking-tight text-navy">
                  Career<span className="text-accent">OS</span>
                </span>
                <span className="mt-1 hidden text-[9px] font-medium uppercase tracking-[0.18em] text-muted sm:block">
                  Intelligent Career Platform
                </span>
              </div>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden items-center gap-7 md:flex">
              <Link
                href="/"
                className="text-sm font-medium text-navy/70 transition-colors duration-200 hover:text-navy"
              >
                Home
              </Link>

              <Link
                href="/jobs"
                className="text-sm font-medium text-navy/70 transition-colors duration-200 hover:text-navy"
              >
                Jobs
              </Link>

              <a
                href="/#features"
                className="text-sm font-medium text-navy/70 transition-colors duration-200 hover:text-navy"
              >
                Features
              </a>

              <a
                href="/#how-it-works"
                className="text-sm font-medium text-navy/70 transition-colors duration-200 hover:text-navy"
              >
                How It Works
              </a>
            </div>

            {/* Desktop Actions */}
            <div className="hidden items-center gap-3 md:flex">
              <ThemeToggle />

              {!isLoading && isAuthenticated ? (
                <>
                  <span className="mr-1 hidden max-w-[120px] truncate text-sm font-medium text-muted lg:block">
                    {user?.name || "Dashboard"}
                  </span>

                  <Link
                    href="/student-dashboard"
                    className="group flex items-center gap-2 rounded-xl border border-accent/30 bg-accent/10 px-4 py-2.5 text-sm font-semibold text-accent transition-all duration-200 hover:border-accent/50 hover:bg-accent/15"
                  >
                    Dashboard
                    <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
                  </Link>

                  <button
                    type="button"
                    onClick={handleSignOut}
                    className="px-2 py-2 text-sm font-medium text-muted transition-colors hover:text-navy"
                  >
                    Log out
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="px-3 py-2 text-sm font-medium text-navy/70 transition-colors hover:text-navy"
                  >
                    Log in
                  </Link>

                  <Link
                    href="/register"
                    className="group flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-white shadow-glow-primary transition-all duration-200 hover:bg-accent-light"
                  >
                    Get Started
                    <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
                  </Link>
                </>
              )}
            </div>

            {/* Mobile Menu Button */}
            <div className="flex items-center gap-2 md:hidden">
              <ThemeToggle />
              <button
                type="button"
                aria-label={mobileOpen ? "Close menu" : "Open menu"}
                aria-expanded={mobileOpen}
                onClick={() => setMobileOpen(!mobileOpen)}
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-line bg-elevated text-navy transition-colors hover:bg-elevated-strong"
              >
                {mobileOpen ? (
                  <X className="h-5 w-5" />
                ) : (
                  <Menu className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>

          {/* Mobile Navigation */}
          {mobileOpen && (
            <div className="relative mt-4 animate-fade-in border-t border-line pt-4 md:hidden">
              <div className="flex flex-col gap-1 pb-1">
                <Link
                  href="/"
                  onClick={closeMobileMenu}
                  className="rounded-xl px-4 py-3 text-sm font-medium text-navy/70 transition-colors hover:bg-elevated hover:text-navy"
                >
                  Home
                </Link>

                <Link
                  href="/jobs"
                  onClick={closeMobileMenu}
                  className="rounded-xl px-4 py-3 text-sm font-medium text-navy/70 transition-colors hover:bg-elevated hover:text-navy"
                >
                  Jobs
                </Link>

                <a
                  href="/#features"
                  onClick={closeMobileMenu}
                  className="rounded-xl px-4 py-3 text-sm font-medium text-navy/70 transition-colors hover:bg-elevated hover:text-navy"
                >
                  Features
                </a>

                <a
                  href="/#how-it-works"
                  onClick={closeMobileMenu}
                  className="rounded-xl px-4 py-3 text-sm font-medium text-navy/70 transition-colors hover:bg-elevated hover:text-navy"
                >
                  How It Works
                </a>

                <Link
                  href="/about"
                  onClick={closeMobileMenu}
                  className="rounded-xl px-4 py-3 text-sm font-medium text-navy/70 transition-colors hover:bg-elevated hover:text-navy"
                >
                  About
                </Link>

                <div className="my-2 h-px bg-line-subtle" />

                {!isLoading && isAuthenticated ? (
                  <>
                    <div className="px-4 py-2 text-sm text-muted">
                      Signed in as{" "}
                      <span className="font-medium text-navy">
                        {user?.name || "User"}
                      </span>
                    </div>

                    <Link
                      href="/student-dashboard"
                      onClick={closeMobileMenu}
                      className="flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-white shadow-glow-primary"
                    >
                      Open Dashboard
                      <ArrowRight className="h-4 w-4" />
                    </Link>

                    <button
                      type="button"
                      onClick={handleSignOut}
                      className="rounded-xl px-4 py-3 text-left text-sm font-medium text-muted transition-colors hover:bg-elevated hover:text-navy"
                    >
                      Log out
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      href="/login"
                      onClick={closeMobileMenu}
                      className="rounded-xl px-4 py-3 text-sm font-medium text-navy/70 transition-colors hover:bg-elevated hover:text-navy"
                    >
                      Log in
                    </Link>

                    <Link
                      href="/register"
                      onClick={closeMobileMenu}
                      className="flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-white shadow-glow-primary"
                    >
                      Get Started
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </>
                )}
              </div>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}