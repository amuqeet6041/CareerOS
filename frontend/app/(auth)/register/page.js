import Link from "next/link";
import RegisterForm from "@/components/auth/RegisterForm";
import ThemeToggle from "@/components/shared/ThemeToggle";
import { Rocket, Sparkles } from "lucide-react";

export default function RegisterPage() {
  return (
    <main className="relative flex min-h-screen flex-col overflow-hidden bg-canvas px-6 py-10">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-[-280px] h-[560px] w-[880px] -translate-x-1/2 rounded-full bg-primary/10 blur-[120px]" />
        <div className="absolute bottom-[-220px] right-[-160px] h-[420px] w-[420px] rounded-full bg-primary/6 blur-[100px]" />
      </div>
      <div className="pointer-events-none absolute inset-0 bg-grid opacity-[0.35] [mask-image:radial-gradient(ellipse_at_top,black_20%,transparent_70%)]" />

      <div className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-accent-light shadow-glow-primary">
            <Sparkles className="h-4 w-4 text-white" strokeWidth={2.2} />
          </div>
          <span className="text-[17px] font-semibold tracking-tight text-navy">
            Career<span className="text-accent">OS</span>
          </span>
        </Link>
        <ThemeToggle />
      </div>

      <div className="relative z-10 mx-auto flex w-full max-w-md flex-1 flex-col justify-center py-10">
        <div className="animate-slide-up">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10 text-accent">
            <Rocket className="h-5 w-5" />
          </div>

          <h1 className="mt-5 text-center text-2xl font-bold tracking-tight text-navy">
            Create your account
          </h1>
          <p className="mt-2 text-center text-sm leading-6 text-muted">
            Upload a resume, get matched, and track your next career move.
          </p>

          <div className="mt-8 rounded-2xl border border-line bg-surface p-6 shadow-card sm:p-7">
            <RegisterForm />
          </div>

          <p className="mt-6 text-center text-sm text-muted">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-semibold text-accent transition-colors hover:text-accent-light"
            >
              Log in
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}