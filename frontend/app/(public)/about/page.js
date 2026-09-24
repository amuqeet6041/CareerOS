import Navbar from "@/components/shared/Navbar";
import Footer from "@/components/shared/Footer";
import { Info, Sparkles } from "lucide-react";

export default function AboutPage() {
  return (
    <>
      <Navbar />
      <main className="relative overflow-hidden bg-canvas">
        <div className="pointer-events-none absolute left-1/2 top-0 h-[320px] w-[720px] -translate-x-1/2 rounded-full bg-primary/5 blur-3xl" />

        <div className="mx-auto max-w-3xl px-6 py-20">
          <div className="inline-flex items-center gap-2 rounded-full border border-accent/25 bg-accent/10 px-3 py-1.5 text-xs font-medium text-accent">
            <Sparkles className="h-3.5 w-3.5" />
            About
          </div>

          <h1 className="mt-5 text-3xl font-bold tracking-tight text-navy sm:text-4xl">
            About CareerOS
          </h1>

          <div className="mt-6 rounded-2xl border border-line bg-surface p-6 shadow-card sm:p-8">
            <p className="text-base leading-7 text-ink-muted">
              CareerOS is an AI-powered career platform that helps job seekers
              understand their own profile and find opportunities that
              genuinely match their skills and qualifications.
            </p>

            <div className="mt-5 flex gap-3 rounded-xl border border-line bg-elevated p-4">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
              <p className="text-sm leading-6 text-muted">
                This page is a placeholder &mdash; replace it with real content
                about the team and mission.
              </p>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}