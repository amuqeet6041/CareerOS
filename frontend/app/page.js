import Link from "next/link";
import Navbar from "@/components/shared/Navbar";
import Footer from "@/components/shared/Footer";
import {
  ArrowRight,
  ArrowUpRight,
  Brain,
  CheckCircle2,
  FileText,
  Filter,
  LayoutDashboard,
  Search,
  Sparkles,
  Target,
  TrendingUp,
  Upload,
  UserRound,
  Zap,
} from "lucide-react";

const FEATURES = [
  {
    icon: FileText,
    title: "AI Resume Analysis",
    description:
      "Upload your CV and let CareerOS extract your skills, education, experience, and qualifications automatically.",
  },
  {
    icon: Target,
    title: "Smart Job Matching",
    description:
      "CareerOS compares your profile with job requirements and shows clear Skill Match and Qualification Match scores.",
  },
  {
    icon: Search,
    title: "Live Job Discovery",
    description:
      "Discover relevant opportunities based on your skills, location, work preference, salary expectations, and profile.",
  },
  {
    icon: Filter,
    title: "Powerful Job Filters",
    description:
      "Quickly narrow opportunities by location, remote or hybrid work, job type, salary range, and other preferences.",
  },
  {
    icon: LayoutDashboard,
    title: "Career Dashboard",
    description:
      "Keep your career activity organized with saved jobs, applications, resume information, and personalized insights.",
  },
  {
    icon: TrendingUp,
    title: "Career Insights",
    description:
      "Understand your current profile, identify skill gaps, and discover areas that can improve your future opportunities.",
  },
];

const STEPS = [
  {
    number: "01",
    icon: Upload,
    title: "Upload Your Resume",
    description:
      "Upload your CV in PDF or DOCX format and let CareerOS process your information.",
  },
  {
    number: "02",
    icon: Brain,
    title: "AI Understands Your Profile",
    description:
      "Your skills, education, experience, and qualifications are extracted into a structured career profile.",
  },
  {
    number: "03",
    icon: Target,
    title: "Discover Your Matches",
    description:
      "CareerOS compares your profile with available opportunities and calculates relevant match scores.",
  },
  {
    number: "04",
    icon: CheckCircle2,
    title: "Apply & Track",
    description:
      "Explore job details, apply through the appropriate source, save opportunities, and track your progress.",
  },
];

const INDICATORS = [
  {
    icon: FileText,
    value: "PDF · DOCX",
    label: "Resume formats parsed",
  },
  {
    icon: Target,
    value: "0–100",
    label: "Transparent match scoring",
  },
  {
    icon: Search,
    value: "Live",
    label: "Opportunity discovery",
  },
  {
    icon: TrendingUp,
    value: "Actionable",
    label: "Skill-gap insights",
  },
];

function MatchPreview() {
  return (
    <div className="relative mx-auto w-full max-w-[520px]">
      {/* Glow */}
      <div className="absolute -inset-10 rounded-full bg-primary/10 blur-3xl" />

      {/* Main dashboard card */}
      <div className="relative animate-fade-in overflow-hidden rounded-3xl border border-line bg-surface/95 p-4 shadow-card-hover backdrop-blur-xl sm:p-5">
        {/* Window header */}
        <div className="flex items-center justify-between border-b border-line-subtle pb-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/15">
              <Sparkles className="h-4 w-4 text-accent-light" />
            </div>

            <div>
              <p className="text-xs font-semibold text-navy">CareerOS Match</p>
              <p className="text-[10px] text-muted">AI Career Analysis</p>
            </div>
          </div>

          <div className="flex gap-1.5">
            <span className="h-2 w-2 rounded-full bg-line" />
            <span className="h-2 w-2 rounded-full bg-line" />
            <span className="h-2 w-2 rounded-full bg-line" />
          </div>
        </div>

        {/* Profile */}
        <div className="mt-5 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-accent-light">
            <UserRound className="h-5 w-5 text-white" />
          </div>

          <div>
            <p className="text-sm font-semibold text-navy">Your Career Profile</p>
            <p className="text-xs text-muted">AI analyzed profile</p>
          </div>

          <div className="ml-auto rounded-full bg-success/10 px-2.5 py-1 text-[10px] font-semibold text-success">
            Analyzed
          </div>
        </div>

        {/* Match score */}
        <div className="mt-5 rounded-2xl border border-line bg-elevated p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-muted">Overall Job Match</p>

              <p className="mt-1 text-3xl font-bold tracking-tight text-navy">
                92%
              </p>
            </div>

            <div className="relative flex h-16 w-16 items-center justify-center rounded-full border-[5px] border-accent/20">
              <div className="absolute inset-[-5px] rounded-full border-[5px] border-transparent border-t-accent border-r-accent" />
              <span className="text-xs font-bold text-accent">92%</span>
            </div>
          </div>

          <div className="mt-4 h-2 overflow-hidden rounded-full bg-line/40">
            <div className="h-full w-[92%] rounded-full bg-gradient-to-r from-accent to-accent-light" />
          </div>
        </div>

        {/* Skills */}
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-line bg-elevated p-3">
            <p className="text-[10px] uppercase tracking-wider text-muted">
              Skill Match
            </p>
            <div className="mt-2 flex items-end justify-between">
              <span className="text-xl font-bold text-navy">95%</span>
              <span className="text-[10px] font-medium text-success">
                Strong
              </span>
            </div>
          </div>

          <div className="rounded-xl border border-line bg-elevated p-3">
            <p className="text-[10px] uppercase tracking-wider text-muted">
              Qualification
            </p>
            <div className="mt-2 flex items-end justify-between">
              <span className="text-xl font-bold text-navy">89%</span>
              <span className="text-[10px] font-medium text-accent">
                High
              </span>
            </div>
          </div>
        </div>

        {/* Skills tags */}
        <div className="mt-4">
          <p className="text-[10px] uppercase tracking-wider text-muted">
            Detected Skills
          </p>

          <div className="mt-2 flex flex-wrap gap-2">
            {["Python", "SQL", "Power BI", "Data Analysis"].map((skill) => (
              <span
                key={skill}
                className="rounded-lg border border-accent/15 bg-accent/10 px-2.5 py-1.5 text-[10px] font-medium text-accent"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Floating badge */}
      <div className="absolute -right-3 -top-4 hidden animate-fade-in-up rounded-2xl border border-line bg-surface px-4 py-3 shadow-card-hover [animation-delay:200ms] sm:block">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-success/10">
            <Zap className="h-3.5 w-3.5 text-success" />
          </div>

          <div>
            <p className="text-[10px] text-muted">Match Found</p>
            <p className="text-xs font-semibold text-navy">
              High compatibility
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function HomePage() {
  return (
    <main className="overflow-hidden bg-canvas">
      <Navbar />

      {/* =========================================================
          HERO
      ========================================================= */}
      <section className="relative min-h-[720px] overflow-hidden bg-canvas pt-32 sm:pt-36">
        {/* Background effects */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-[-300px] h-[600px] w-[900px] -translate-x-1/2 rounded-full bg-primary/10 blur-[120px]" />
          <div className="absolute right-[-200px] top-[200px] h-[400px] w-[400px] rounded-full bg-primary/8 blur-[100px]" />
          <div className="absolute bottom-[-200px] left-[-150px] h-[400px] w-[400px] rounded-full bg-info/5 blur-[100px]" />
        </div>

        {/* Grid */}
        <div className="pointer-events-none absolute inset-0 bg-grid opacity-[0.5] [mask-image:radial-gradient(ellipse_at_center,black_25%,transparent_75%)]" />

        <div className="relative mx-auto max-w-7xl px-4 pb-24 sm:px-6 lg:px-8 lg:pb-32">
          <div className="grid items-center gap-14 lg:grid-cols-[1.05fr_0.95fr] lg:gap-10">
            {/* Hero copy */}
            <div className="max-w-2xl">
              <div className="mb-6 inline-flex animate-fade-in-up items-center gap-2 rounded-full border border-gold/30 bg-gold/10 px-3.5 py-2 text-xs font-medium text-gold">
                <Sparkles className="h-3.5 w-3.5" />
                AI-powered career intelligence
              </div>

              <h1 className="animate-fade-in-up text-4xl font-bold leading-[1.08] tracking-[-0.035em] text-navy [animation-delay:60ms] sm:text-5xl lg:text-6xl">
                Your career.
                <br />
                <span className="text-gradient-blue">
                  Understood by AI.
                </span>
              </h1>

              <p className="mt-6 max-w-xl animate-fade-in-up text-base leading-7 text-ink-muted [animation-delay:120ms] sm:text-lg sm:leading-8">
                Upload your resume, discover relevant opportunities, and
                understand exactly how your skills and qualifications match
                real jobs.
              </p>

              <div className="mt-8 flex animate-fade-in-up flex-col gap-3 [animation-delay:180ms] sm:flex-row">
                <Link
                  href="/register"
                  className="group inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-6 py-3.5 text-sm font-semibold text-white shadow-glow-primary transition-all duration-200 hover:bg-accent-light"
                >
                  Get Started
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </Link>

                <Link
                  href="/jobs"
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-line bg-elevated px-6 py-3.5 text-sm font-semibold text-navy transition-all duration-200 hover:border-line hover:bg-elevated-strong"
                >
                  Explore Jobs
                  <ArrowUpRight className="h-4 w-4" />
                </Link>
              </div>

              {/* Trust points */}
              <div className="mt-9 flex animate-fade-in-up flex-wrap gap-x-6 gap-y-3 [animation-delay:240ms]">
                {[
                  "AI resume analysis",
                  "Clear match scores",
                  "Personalized discovery",
                ].map((item) => (
                  <div
                    key={item}
                    className="flex items-center gap-2 text-xs text-muted"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5 text-accent-light" />
                    {item}
                  </div>
                ))}
              </div>
            </div>

            {/* Hero visual */}
            <div className="lg:pl-4">
              <MatchPreview />
            </div>
          </div>
        </div>

        {/* Bottom fade */}
        <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-canvas to-transparent" />
      </section>

      {/* =========================================================
          INDICATORS
      ========================================================= */}
      <section className="relative bg-canvas pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-4 rounded-2xl border border-line bg-surface p-6 shadow-card sm:grid-cols-2 sm:p-8 lg:grid-cols-4">
            {INDICATORS.map((indicator, index) => {
              const Icon = indicator.icon;

              return (
                <div
                  key={indicator.label}
                  className="animate-fade-in-up flex items-center gap-3.5"
                  style={{ animationDelay: `${index * 60}ms` }}
                >
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent">
                    <Icon className="h-5 w-5" />
                  </div>

                  <div>
                    <p className="text-sm font-semibold text-navy">
                      {indicator.value}
                    </p>
                    <p className="mt-0.5 text-xs text-muted">
                      {indicator.label}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* =========================================================
          FEATURES
      ========================================================= */}
      <section
        id="features"
        className="relative overflow-hidden border-y border-line bg-elevated/60 py-20 sm:py-24"
      >
        <div className="pointer-events-none absolute left-[-150px] top-20 h-[360px] w-[360px] rounded-full bg-primary/5 blur-3xl" />

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl">
            <span className="text-xs font-bold uppercase tracking-[0.18em] text-gold">
              Platform
            </span>

            <h2 className="mt-3 text-3xl font-bold tracking-tight text-navy sm:text-4xl">
              Everything you need to navigate your career.
            </h2>

            <p className="mt-4 text-base leading-7 text-muted">
              From understanding your resume to discovering opportunities and
              tracking your applications, CareerOS brings the process together.
            </p>
          </div>

          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature, index) => {
              const Icon = feature.icon;

              return (
                <div
                  key={feature.title}
                  className="group relative animate-fade-in-up overflow-hidden rounded-2xl border border-line bg-surface p-6 shadow-card transition-all duration-300 hover:-translate-y-1 hover:border-accent/30 hover:shadow-card-hover"
                  style={{ animationDelay: `${index * 70}ms` }}
                >
                  <div className="pointer-events-none absolute -right-12 -top-12 h-32 w-32 rounded-full bg-primary/5 opacity-0 blur-2xl transition-opacity duration-300 group-hover:opacity-100" />

                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent/10 text-accent transition-colors duration-300 group-hover:bg-primary group-hover:text-white">
                    <Icon className="h-5 w-5" />
                  </div>

                  <h3 className="mt-5 text-base font-semibold text-navy">
                    {feature.title}
                  </h3>

                  <p className="mt-2 text-sm leading-6 text-muted">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* =========================================================
          HOW IT WORKS
      ========================================================= */}
      <section id="how-it-works" className="bg-canvas py-20 sm:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <span className="text-xs font-bold uppercase tracking-[0.18em] text-gold">
              Simple process
            </span>

            <h2 className="mt-3 text-3xl font-bold tracking-tight text-navy sm:text-4xl">
              From resume to opportunity.
            </h2>

            <p className="mt-4 text-base leading-7 text-muted">
              A simple workflow designed to turn your existing experience into
              actionable career opportunities.
            </p>
          </div>

          <div className="relative mt-14 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {/* Connector */}
            <div className="pointer-events-none absolute left-[12%] right-[12%] top-9 hidden h-px bg-gradient-to-r from-accent/10 via-accent/40 to-accent/10 lg:block" />

            {STEPS.map((step, index) => {
              const Icon = step.icon;

              return (
                <div
                  key={step.number}
                  className="relative animate-fade-in-up"
                  style={{ animationDelay: `${index * 90}ms` }}
                >
                  <div className="relative z-10 flex h-[72px] w-[72px] items-center justify-center rounded-2xl border border-accent/25 bg-surface text-accent shadow-card transition-transform duration-300 hover:-translate-y-1">
                    <Icon className="h-6 w-6" />

                    <span className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-[9px] font-bold text-white">
                      {step.number}
                    </span>
                  </div>

                  <h3 className="mt-5 text-base font-semibold text-navy">
                    {step.title}
                  </h3>

                  <p className="mt-2 text-sm leading-6 text-muted">
                    {step.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* =========================================================
          AI MATCHING SECTION
      ========================================================= */}
      <section className="relative overflow-hidden bg-elevated/60 py-20 sm:py-24">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-accent/30 to-transparent" />
        <div className="pointer-events-none absolute bottom-[-200px] right-[-120px] h-[400px] w-[400px] rounded-full bg-primary/8 blur-3xl" />

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-20">
            {/* Copy */}
            <div>
              <span className="text-xs font-bold uppercase tracking-[0.18em] text-gold">
                Transparent matching
              </span>

              <h2 className="mt-4 text-3xl font-bold tracking-tight text-navy sm:text-4xl">
                Know why a job matches you.
              </h2>

              <p className="mt-5 max-w-xl text-base leading-7 text-ink-muted">
                Instead of simply showing job listings, CareerOS gives you
                understandable indicators based on your profile.
              </p>

              <div className="mt-8 space-y-4">
                {[
                  {
                    title: "Skill Match",
                    description:
                      "Compare the skills identified in your profile with the skills requested by a job.",
                  },
                  {
                    title: "Qualification Match",
                    description:
                      "Compare education and qualification requirements with your profile.",
                  },
                  {
                    title: "Profile-based discovery",
                    description:
                      "Use your profile to find opportunities aligned with your preferences.",
                  },
                ].map((item) => (
                  <div key={item.title} className="flex gap-3">
                    <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-accent" />

                    <div>
                      <h3 className="text-sm font-semibold text-navy">
                        {item.title}
                      </h3>

                      <p className="mt-1 text-sm leading-6 text-muted">
                        {item.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Score cards */}
            <div className="rounded-3xl border border-line bg-surface p-5 shadow-card-hover sm:p-7">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-muted">
                    Recommended Opportunity
                  </p>

                  <h3 className="mt-1 text-lg font-semibold text-navy">
                    Data Analyst
                  </h3>
                </div>

                <span className="rounded-full bg-success/10 px-3 py-1.5 text-xs font-semibold text-success">
                  Strong Match
                </span>
              </div>

              <div className="mt-7 grid gap-4 sm:grid-cols-2">
                <div className="rounded-2xl border border-line bg-elevated p-5">
                  <p className="text-xs text-muted">Skill Match</p>

                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="text-4xl font-bold text-navy">94</span>
                    <span className="text-sm text-muted">%</span>
                  </div>

                  <div className="mt-4 h-1.5 rounded-full bg-line/50">
                    <div className="h-full w-[94%] rounded-full bg-accent" />
                  </div>
                </div>

                <div className="rounded-2xl border border-line bg-elevated p-5">
                  <p className="text-xs text-muted">Qualification Match</p>

                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="text-4xl font-bold text-navy">88</span>
                    <span className="text-sm text-muted">%</span>
                  </div>

                  <div className="mt-4 h-1.5 rounded-full bg-line/50">
                    <div className="h-full w-[88%] rounded-full bg-accent-light" />
                  </div>
                </div>
              </div>

              <div className="mt-4 rounded-2xl border border-line bg-elevated p-5">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-medium text-muted">
                    Matching Skills
                  </p>

                  <span className="text-xs text-success">
                    8 skills matched
                  </span>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {[
                    "Python",
                    "SQL",
                    "Power BI",
                    "Excel",
                    "Pandas",
                    "Data Analysis",
                    "Statistics",
                    "Visualization",
                  ].map((skill) => (
                    <span
                      key={skill}
                      className="rounded-lg bg-accent/10 px-2.5 py-1.5 text-[10px] font-medium text-accent"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =========================================================
          FINAL CTA
      ========================================================= */}
      <section className="relative overflow-hidden bg-canvas py-20 sm:py-28">
        <div className="pointer-events-none absolute left-1/2 top-1/2 h-[350px] w-[700px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/8 blur-[100px]" />

        <div className="relative mx-auto max-w-3xl px-4 text-center sm:px-6">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-accent/10 text-accent">
            <Sparkles className="h-6 w-6" />
          </div>

          <h2 className="mt-6 text-3xl font-bold tracking-tight text-navy sm:text-4xl">
            Ready to understand your next career move?
          </h2>

          <p className="mx-auto mt-4 max-w-xl text-base leading-7 text-muted">
            Create your CareerOS profile, upload your resume, and start
            discovering opportunities built around your skills.
          </p>

          <div className="mt-8">
            <Link
              href="/register"
              className="group inline-flex items-center gap-2 rounded-xl bg-primary px-7 py-3.5 text-sm font-semibold text-white shadow-glow-primary transition-all duration-200 hover:bg-accent-light"
            >
              Create Free Account
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}