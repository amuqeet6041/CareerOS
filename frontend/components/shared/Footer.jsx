import Link from "next/link";
import { ArrowUpRight, Sparkles } from "lucide-react";

export default function Footer() {
  return (
    <footer className="relative overflow-hidden border-t border-line bg-canvas">
      {/* Soft decorative glow */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-accent/40 to-transparent" />
      <div className="pointer-events-none absolute -top-40 left-1/2 h-80 w-[720px] -translate-x-1/2 rounded-full bg-primary/5 blur-3xl" />

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Main Footer */}
        <div className="grid gap-10 py-12 sm:grid-cols-2 lg:grid-cols-4 lg:py-16">
          {/* Brand */}
          <div className="lg:col-span-2">
            <Link href="/" className="group inline-flex items-center gap-2.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-accent-light shadow-glow-primary transition-transform duration-300 group-hover:scale-105">
                <Sparkles className="h-5 w-5 text-white" strokeWidth={2.2} />
              </div>

              <span className="text-xl font-semibold tracking-tight text-navy">
                Career<span className="text-accent">OS</span>
              </span>
            </Link>

            <p className="mt-5 max-w-md text-sm leading-6 text-muted">
              An intelligent career platform that helps you understand your
              skills, discover relevant opportunities, and make better career
              decisions.
            </p>

            <Link
              href="/jobs"
              className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-accent transition-colors hover:text-accent-light"
            >
              Explore Jobs
              <ArrowUpRight className="h-4 w-4" />
            </Link>
          </div>

          {/* Product */}
          <div>
            <h3 className="text-sm font-semibold text-navy">Product</h3>

            <ul className="mt-4 space-y-3">
              <li>
                <Link
                  href="/jobs"
                  className="text-sm text-muted transition-colors hover:text-navy"
                >
                  Find Jobs
                </Link>
              </li>

              <li>
                <Link
                  href="/#features"
                  className="text-sm text-muted transition-colors hover:text-navy"
                >
                  Features
                </Link>
              </li>

              <li>
                <Link
                  href="/#how-it-works"
                  className="text-sm text-muted transition-colors hover:text-navy"
                >
                  How It Works
                </Link>
              </li>

              <li>
                <Link
                  href="/register"
                  className="text-sm text-muted transition-colors hover:text-navy"
                >
                  Get Started
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="text-sm font-semibold text-navy">Company</h3>

            <ul className="mt-4 space-y-3">
              <li>
                <Link
                  href="/about"
                  className="text-sm text-muted transition-colors hover:text-navy"
                >
                  About CareerOS
                </Link>
              </li>

              <li>
                <Link
                  href="/contact"
                  className="text-sm text-muted transition-colors hover:text-navy"
                >
                  Contact
                </Link>
              </li>

              <li>
                <Link
                  href="/login"
                  className="text-sm text-muted transition-colors hover:text-navy"
                >
                  Log In
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="flex flex-col gap-3 border-t border-line-subtle py-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-muted">
            © {new Date().getFullYear()} CareerOS. All rights reserved.
          </p>

          <div className="flex items-center gap-5">
            <span className="text-xs text-muted">
              Intelligent career matching
            </span>

            <span className="h-1 w-1 rounded-full bg-line" />

            <span className="text-xs font-medium text-navy/70">
              Built with AI
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}