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

function MatchPreview() {
  return (
    <div className="relative mx-auto w-full max-w-[520px]">
      {/* Glow */}
      <div className="absolute -inset-10 rounded-full bg-blue-500/10 blur-3xl" />

      {/* Main dashboard card */}
      <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-[#0B1B30]/95 p-4 shadow-2xl shadow-black/30 backdrop-blur-xl sm:p-5">
        {/* Window header */}
        <div className="flex items-center justify-between border-b border-white/[0.08] pb-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/15">
              <Sparkles className="h-4 w-4 text-blue-400" />
            </div>

            <div>
              <p className="text-xs font-semibold text-white">
                CareerOS Match
              </p>
              <p className="text-[10px] text-slate-500">
                AI Career Analysis
              </p>
            </div>
          </div>

          <div className="flex gap-1.5">
            <span className="h-2 w-2 rounded-full bg-slate-600" />
            <span className="h-2 w-2 rounded-full bg-slate-600" />
            <span className="h-2 w-2 rounded-full bg-slate-600" />
          </div>
        </div>

        {/* Profile */}
        <div className="mt-5 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-400">
            <UserRound className="h-5 w-5 text-white" />
          </div>

          <div>
            <p className="text-sm font-semibold text-white">
              Your Career Profile
            </p>
            <p className="text-xs text-slate-500">
              AI analyzed profile
            </p>
          </div>

          <div className="ml-auto rounded-full bg-green-500/10 px-2.5 py-1 text-[10px] font-semibold text-green-400">
            Analyzed
          </div>
        </div>

        {/* Match score */}
        <div className="mt-5 rounded-2xl border border-white/[0.08] bg-white/[0.03] p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-400">
                Overall Job Match
              </p>

              <p className="mt-1 text-3xl font-bold tracking-tight text-white">
                92%
              </p>
            </div>

            <div className="relative flex h-16 w-16 items-center justify-center rounded-full border-[5px] border-blue-500/20">
              <div className="absolute inset-[-5px] rounded-full border-[5px] border-transparent border-t-blue-400 border-r-blue-400" />
              <span className="text-xs font-bold text-blue-300">92%</span>
            </div>
          </div>

          <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/[0.06]">
            <div className="h-full w-[92%] rounded-full bg-gradient-to-r from-blue-600 to-blue-400" />
          </div>
        </div>

        {/* Skills */}
        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-3">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">
              Skill Match
            </p>
            <div className="mt-2 flex items-end justify-between">
              <span className="text-xl font-bold text-white">95%</span>
              <span className="text-[10px] font-medium text-green-400">
                Strong
              </span>
            </div>
          </div>

          <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-3">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">
              Qualification
            </p>
            <div className="mt-2 flex items-end justify-between">
              <span className="text-xl font-bold text-white">89%</span>
              <span className="text-[10px] font-medium text-blue-400">
                High
              </span>
            </div>
          </div>
        </div>

        {/* Skills tags */}
        <div className="mt-4">
          <p className="text-[10px] uppercase tracking-wider text-slate-500">
            Detected Skills
          </p>

          <div className="mt-2 flex flex-wrap gap-2">
            {["Python", "SQL", "Power BI", "Data Analysis"].map((skill) => (
              <span
                key={skill}
                className="rounded-lg border border-blue-400/10 bg-blue-500/[0.08] px-2.5 py-1.5 text-[10px] font-medium text-blue-300"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Floating badge */}
      <div className="absolute -right-3 -top-4 hidden rounded-2xl border border-white/10 bg-[#10243D] px-4 py-3 shadow-xl sm:block">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-green-500/10">
            <Zap className="h-3.5 w-3.5 text-green-400" />
          </div>

          <div>
            <p className="text-[10px] text-slate-500">Match Found</p>
            <p className="text-xs font-semibold text-white">
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
    <main className="overflow-hidden bg-white">
      <Navbar />

      {/* =========================================================
          HERO
      ========================================================= */}
      <section className="relative min-h-[760px] overflow-hidden bg-[#07111F] pt-32 sm:pt-36">
        {/* Background effects */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-[-300px] h-[600px] w-[900px] -translate-x-1/2 rounded-full bg-blue-500/10 blur-[120px]" />

          <div className="absolute right-[-200px] top-[200px] h-[400px] w-[400px] rounded-full bg-blue-600/[0.06] blur-[100px]" />

          <div className="absolute bottom-[-200px] left-[-150px] h-[400px] w-[400px] rounded-full bg-sky-500/[0.05] blur-[100px]" />
        </div>

        {/* Grid */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.035]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)",
            backgroundSize: "50px 50px",
          }}
        />

        <div className="relative mx-auto max-w-7xl px-4 pb-24 sm:px-6 lg:px-8 lg:pb-32">
          <div className="grid items-center gap-14 lg:grid-cols-[1.05fr_0.95fr] lg:gap-10">
            {/* Hero copy */}
            <div className="max-w-2xl">
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-400/20 bg-blue-500/[0.08] px-3.5 py-2 text-xs font-medium text-blue-300">
                <Sparkles className="h-3.5 w-3.5" />
                AI-powered career intelligence
              </div>

              <h1 className="text-4xl font-bold leading-[1.08] tracking-[-0.035em] text-white sm:text-5xl lg:text-6xl">
                Your career.
                <br />
                <span className="bg-gradient-to-r from-blue-400 via-sky-400 to-blue-300 bg-clip-text text-transparent">
                  Understood by AI.
                </span>
              </h1>

              <p className="mt-6 max-w-xl text-base leading-7 text-slate-400 sm:text-lg sm:leading-8">
                Upload your resume, discover relevant opportunities, and
                understand exactly how your skills and qualifications match
                real jobs.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link
                  href="/register"
                  className="group inline-flex items-center justify-center gap-2 rounded-xl bg-[#3B82F6] px-6 py-3.5 text-sm font-semibold text-white shadow-xl shadow-blue-500/20 transition-all duration-200 hover:bg-[#2563EB] hover:shadow-blue-500/30"
                >
                  Get Started
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </Link>

                <Link
                  href="/jobs"
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-6 py-3.5 text-sm font-semibold text-slate-200 transition-all duration-200 hover:border-white/20 hover:bg-white/[0.08] hover:text-white"
                >
                  Explore Jobs
                  <ArrowUpRight className="h-4 w-4" />
                </Link>
              </div>

              {/* Trust points */}
              <div className="mt-9 flex flex-wrap gap-x-6 gap-y-3">
                {[
                  "AI resume analysis",
                  "Clear match scores",
                  "Personalized discovery",
                ].map((item) => (
                  <div
                    key={item}
                    className="flex items-center gap-2 text-xs text-slate-500"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5 text-blue-400" />
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
        <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white to-transparent" />
      </section>


  

      {/* =========================================================
          FEATURES
      ========================================================= */}
      <section id="features" className="bg-slate-50 py-20 sm:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl">
            <span className="text-xs font-bold uppercase tracking-[0.18em] text-[#3B82F6]">
              Platform
            </span>

            <h2 className="mt-3 text-3xl font-bold tracking-tight text-[#07111F] sm:text-4xl">
              Everything you need to navigate your career.
            </h2>

            <p className="mt-4 text-base leading-7 text-slate-500">
              From understanding your resume to discovering opportunities and
              tracking your applications, CareerOS brings the process together.
            </p>
          </div>

          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => {
              const Icon = feature.icon;

              return (
                <div
                  key={feature.title}
                  className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-blue-200 hover:shadow-xl hover:shadow-blue-500/[0.06]"
                >
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-[#3B82F6] transition-colors group-hover:bg-blue-500 group-hover:text-white">
                    <Icon className="h-5 w-5" />
                  </div>

                  <h3 className="mt-5 text-base font-semibold text-[#07111F]">
                    {feature.title}
                  </h3>

                  <p className="mt-2 text-sm leading-6 text-slate-500">
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
      <section id="how-it-works" className="bg-white py-20 sm:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <span className="text-xs font-bold uppercase tracking-[0.18em] text-[#3B82F6]">
              Simple process
            </span>

            <h2 className="mt-3 text-3xl font-bold tracking-tight text-[#07111F] sm:text-4xl">
              From resume to opportunity.
            </h2>

            <p className="mt-4 text-base leading-7 text-slate-500">
              A simple workflow designed to turn your existing experience into
              actionable career opportunities.
            </p>
          </div>

          <div className="relative mt-14 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {/* Connector */}
            <div className="pointer-events-none absolute left-[12%] right-[12%] top-9 hidden h-px bg-slate-200 lg:block" />

            {STEPS.map((step) => {
              const Icon = step.icon;

              return (
                <div key={step.number} className="relative">
                  <div className="relative z-10 flex h-[72px] w-[72px] items-center justify-center rounded-2xl border border-blue-100 bg-white text-[#3B82F6] shadow-sm">
                    <Icon className="h-6 w-6" />

                    <span className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-[#07111F] text-[9px] font-bold text-white">
                      {step.number}
                    </span>
                  </div>

                  <h3 className="mt-5 text-base font-semibold text-[#07111F]">
                    {step.title}
                  </h3>

                  <p className="mt-2 text-sm leading-6 text-slate-500">
                    {step.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* =========================================================
          MATCH SCORE SECTION
      ========================================================= */}
      <section className="bg-[#07111F] py-20 sm:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-20">
            {/* Copy */}
            <div>
              <span className="text-xs font-bold uppercase tracking-[0.18em] text-blue-400">
                Transparent matching
              </span>

              <h2 className="mt-4 text-3xl font-bold tracking-tight text-white sm:text-4xl">
                Know why a job matches you.
              </h2>

              <p className="mt-5 max-w-xl text-base leading-7 text-slate-400">
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
                    <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-blue-400" />

                    <div>
                      <h3 className="text-sm font-semibold text-white">
                        {item.title}
                      </h3>

                      <p className="mt-1 text-sm leading-6 text-slate-500">
                        {item.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Score cards */}
            <div className="rounded-3xl border border-white/10 bg-[#0B1B30] p-5 shadow-2xl sm:p-7">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-slate-500">
                    Recommended Opportunity
                  </p>

                  <h3 className="mt-1 text-lg font-semibold text-white">
                    Data Analyst
                  </h3>
                </div>

                <span className="rounded-full bg-green-500/10 px-3 py-1.5 text-xs font-semibold text-green-400">
                  Strong Match
                </span>
              </div>

              <div className="mt-7 grid gap-4 sm:grid-cols-2">
                <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5">
                  <p className="text-xs text-slate-500">Skill Match</p>

                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="text-4xl font-bold text-white">94</span>
                    <span className="text-sm text-slate-500">%</span>
                  </div>

                  <div className="mt-4 h-1.5 rounded-full bg-white/[0.06]">
                    <div className="h-full w-[94%] rounded-full bg-blue-500" />
                  </div>
                </div>

                <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5">
                  <p className="text-xs text-slate-500">
                    Qualification Match
                  </p>

                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="text-4xl font-bold text-white">88</span>
                    <span className="text-sm text-slate-500">%</span>
                  </div>

                  <div className="mt-4 h-1.5 rounded-full bg-white/[0.06]">
                    <div className="h-full w-[88%] rounded-full bg-sky-400" />
                  </div>
                </div>
              </div>

              <div className="mt-4 rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-medium text-slate-400">
                    Matching Skills
                  </p>

                  <span className="text-xs text-green-400">
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
                      className="rounded-lg bg-green-500/[0.08] px-2.5 py-1.5 text-[10px] font-medium text-green-300"
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
      <section className="relative overflow-hidden bg-white py-20 sm:py-28">
        <div className="pointer-events-none absolute left-1/2 top-1/2 h-[350px] w-[700px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-blue-500/[0.06] blur-[100px]" />

        <div className="relative mx-auto max-w-3xl px-4 text-center sm:px-6">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-[#3B82F6]">
            <Sparkles className="h-6 w-6" />
          </div>

          <h2 className="mt-6 text-3xl font-bold tracking-tight text-[#07111F] sm:text-4xl">
            Ready to understand your next career move?
          </h2>

          <p className="mx-auto mt-4 max-w-xl text-base leading-7 text-slate-500">
            Create your CareerOS profile, upload your resume, and start
            discovering opportunities built around your skills.
          </p>

          <div className="mt-8">
            <Link
              href="/register"
              className="group inline-flex items-center gap-2 rounded-xl bg-[#3B82F6] px-7 py-3.5 text-sm font-semibold text-white shadow-xl shadow-blue-500/20 transition-all duration-200 hover:bg-[#2563EB] hover:shadow-blue-500/30"
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