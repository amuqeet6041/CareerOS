import Link from "next/link";
import { Sparkles, ArrowUpRight } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Main Footer */}
        <div className="grid gap-10 py-12 sm:grid-cols-2 lg:grid-cols-4 lg:py-16">
          {/* Brand */}
          <div className="lg:col-span-2">
            <Link href="/" className="group inline-flex items-center gap-2.5">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[#3B82F6] to-[#60A5FA] shadow-lg shadow-blue-500/20 transition-transform duration-300 group-hover:scale-105">
                <Sparkles
                  className="h-5 w-5 text-white"
                  strokeWidth={2.2}
                />
              </div>

              <span className="text-xl font-semibold tracking-tight text-[#07111F]">
                Career<span className="text-[#3B82F6]">OS</span>
              </span>
            </Link>

            <p className="mt-5 max-w-md text-sm leading-6 text-slate-500">
              An intelligent career platform that helps you understand your
              skills, discover relevant opportunities, and make better career
              decisions.
            </p>

            <Link
              href="/jobs"
              className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-[#2563EB] transition-colors hover:text-[#1D4ED8]"
            >
              Explore Jobs
              <ArrowUpRight className="h-4 w-4" />
            </Link>
          </div>

          {/* Product */}
          <div>
            <h3 className="text-sm font-semibold text-[#07111F]">
              Product
            </h3>

            <ul className="mt-4 space-y-3">
              <li>
                <Link
                  href="/jobs"
                  className="text-sm text-slate-500 transition-colors hover:text-[#07111F]"
                >
                  Find Jobs
                </Link>
              </li>

              <li>
                <Link
                  href="/#features"
                  className="text-sm text-slate-500 transition-colors hover:text-[#07111F]"
                >
                  Features
                </Link>
              </li>

              <li>
                <Link
                  href="/#how-it-works"
                  className="text-sm text-slate-500 transition-colors hover:text-[#07111F]"
                >
                  How It Works
                </Link>
              </li>

              <li>
                <Link
                  href="/register"
                  className="text-sm text-slate-500 transition-colors hover:text-[#07111F]"
                >
                  Get Started
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h3 className="text-sm font-semibold text-[#07111F]">
              Company
            </h3>

            <ul className="mt-4 space-y-3">
              <li>
                <Link
                  href="/about"
                  className="text-sm text-slate-500 transition-colors hover:text-[#07111F]"
                >
                  About CareerOS
                </Link>
              </li>

              <li>
                <Link
                  href="/contact"
                  className="text-sm text-slate-500 transition-colors hover:text-[#07111F]"
                >
                  Contact
                </Link>
              </li>

              <li>
                <Link
                  href="/login"
                  className="text-sm text-slate-500 transition-colors hover:text-[#07111F]"
                >
                  Log In
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="flex flex-col gap-3 border-t border-slate-100 py-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-slate-400">
            © {new Date().getFullYear()} CareerOS. All rights reserved.
          </p>

          <div className="flex items-center gap-5">
            <span className="text-xs text-slate-400">
              Intelligent career matching
            </span>

            <span className="h-1 w-1 rounded-full bg-slate-300" />

            <span className="text-xs font-medium text-slate-500">
              Built with AI
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}