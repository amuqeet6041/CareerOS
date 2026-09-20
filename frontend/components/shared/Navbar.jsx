"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import {
Menu,
X,
ArrowRight,
Sparkles,
} from "lucide-react";

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

return ( <header className="fixed inset-x-0 top-0 z-50"> <div className="mx-auto max-w-7xl px-4 pt-4 sm:px-6 lg:px-8"> <nav className="relative rounded-2xl border border-white/[0.08] bg-[#07111F]/90 px-4 py-3 shadow-2xl shadow-black/10 backdrop-blur-xl sm:px-6">

{/* Subtle blue glow */}
      <div className="pointer-events-none absolute -inset-px rounded-2xl bg-gradient-to-r from-blue-500/10 via-transparent to-blue-400/10 opacity-70" />

      <div className="relative flex items-center justify-between">
        
        {/* Logo */}
        <Link
          href="/"
          className="group flex items-center gap-2.5"
          onClick={closeMobileMenu}
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#3B82F6] to-[#60A5FA] shadow-lg shadow-blue-500/20 transition-transform duration-300 group-hover:scale-105">
            <Sparkles className="h-4 w-4 text-white" strokeWidth={2.2} />
          </div>

          <div className="flex flex-col leading-none">
            <span className="text-[17px] font-semibold tracking-tight text-white">
              Career<span className="text-[#60A5FA]">OS</span>
            </span>
            <span className="mt-1 hidden text-[9px] font-medium uppercase tracking-[0.18em] text-slate-500 sm:block">
              Intelligent Career Platform
            </span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden items-center gap-8 md:flex">
          <Link
            href="/"
            className="text-sm font-medium text-slate-300 transition-colors duration-200 hover:text-white"
          >
            Home
          </Link>


          <a
            href="/#features"
            className="text-sm font-medium text-slate-300 transition-colors duration-200 hover:text-white"
          >
            Features
          </a>

          <a
            href="/#how-it-works"
            className="text-sm font-medium text-slate-300 transition-colors duration-200 hover:text-white"
          >
            How It Works
          </a>

        </div>

        {/* Desktop Actions */}
        <div className="hidden items-center gap-3 md:flex">
          {!isLoading && isAuthenticated ? (
            <>
              <span className="mr-1 max-w-[120px] truncate text-sm font-medium text-slate-400">
                {user?.name || "Dashboard"}
              </span>

              <Link
                href="/student-dashboard"
                className="group flex items-center gap-2 rounded-xl border border-blue-400/20 bg-blue-500/10 px-4 py-2.5 text-sm font-semibold text-blue-300 transition-all duration-200 hover:border-blue-400/40 hover:bg-blue-500/20 hover:text-blue-200"
              >
                Dashboard
                <ArrowRight
                  className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5"
                />
              </Link>

              <button
                type="button"
                onClick={handleSignOut}
                className="px-2 text-sm font-medium text-slate-400 transition-colors hover:text-white"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="px-3 py-2 text-sm font-medium text-slate-300 transition-colors hover:text-white"
              >
                Log in
              </Link>

              <Link
                href="/register"
                className="group flex items-center gap-2 rounded-xl bg-[#3B82F6] px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-500/20 transition-all duration-200 hover:bg-[#2563EB] hover:shadow-blue-500/30"
              >
                Get Started
                <ArrowRight
                  className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5"
                />
              </Link>
            </>
          )}
        </div>

        {/* Mobile Menu Button */}
        <button
          type="button"
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          aria-expanded={mobileOpen}
          onClick={() => setMobileOpen(!mobileOpen)}
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.04] text-slate-300 transition-colors hover:bg-white/[0.08] hover:text-white md:hidden"
        >
          {mobileOpen ? (
            <X className="h-5 w-5" />
          ) : (
            <Menu className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Mobile Navigation */}
      {mobileOpen && (
        <div className="relative mt-4 border-t border-white/[0.08] pt-4 md:hidden">
          <div className="flex flex-col gap-1">
            <Link
              href="/"
              onClick={closeMobileMenu}
              className="rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-colors hover:bg-white/[0.05] hover:text-white"
            >
              Home
            </Link>

            <Link
              href="/jobs"
              onClick={closeMobileMenu}
              className="rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-colors hover:bg-white/[0.05] hover:text-white"
            >
              Jobs
            </Link>

            <a
              href="/#features"
              onClick={closeMobileMenu}
              className="rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-colors hover:bg-white/[0.05] hover:text-white"
            >
              Features
            </a>

            <a
              href="/#how-it-works"
              onClick={closeMobileMenu}
              className="rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-colors hover:bg-white/[0.05] hover:text-white"
            >
              How It Works
            </a>

            <Link
              href="/about"
              onClick={closeMobileMenu}
              className="rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-colors hover:bg-white/[0.05] hover:text-white"
            >
              About
            </Link>

            <div className="my-2 h-px bg-white/[0.08]" />

            {!isLoading && isAuthenticated ? (
              <>
                <div className="px-4 py-2 text-sm text-slate-500">
                  Signed in as{" "}
                  <span className="font-medium text-slate-300">
                    {user?.name || "User"}
                  </span>
                </div>

                <Link
                  href="/student-dashboard"
                  onClick={closeMobileMenu}
                  className="flex items-center justify-center gap-2 rounded-xl bg-[#3B82F6] px-4 py-3 text-sm font-semibold text-white"
                >
                  Open Dashboard
                  <ArrowRight className="h-4 w-4" />
                </Link>

                <button
                  type="button"
                  onClick={handleSignOut}
                  className="rounded-xl px-4 py-3 text-left text-sm font-medium text-slate-400 transition-colors hover:bg-white/[0.05] hover:text-white"
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  onClick={closeMobileMenu}
                  className="rounded-xl px-4 py-3 text-sm font-medium text-slate-300 transition-colors hover:bg-white/[0.05] hover:text-white"
                >
                  Log in
                </Link>

                <Link
                  href="/register"
                  onClick={closeMobileMenu}
                  className="flex items-center justify-center gap-2 rounded-xl bg-[#3B82F6] px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-500/20"
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
