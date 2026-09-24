import Link from "next/link";
import { formatDate } from "@/utils/formatters";

// Profile summary card fed by the real authenticated user (GET /api/auth/me)
// and the resume analysis (GET /api/resume/analysis). Counts come only from
// stored resume data; a loading resume shows dashes instead of guesses.

export default function ProfileSummary({ user, resume = null, resumeLoading = false }) {
  if (!user) {
    return (
      <div
        className="animate-pulse space-y-3 rounded-2xl border border-line bg-surface p-6 shadow-card"
        role="status"
        aria-label="Loading profile"
      >
        <div className="h-10 w-10 rounded-full bg-elevated-strong" />
        <div className="h-4 w-40 rounded bg-elevated-strong" />
        <div className="h-3 w-56 rounded bg-elevated/60" />
      </div>
    );
  }

  const initial = (user.name || "?").trim().charAt(0).toUpperCase();
  const counts = [
    { label: "Skills", value: resume?.skills?.length },
    { label: "Education", value: resume?.education?.length },
    { label: "Experience", value: resume?.experience?.length },
    { label: "Certifications", value: resume?.certifications?.length },
  ];

  return (
    <section className="rounded-2xl border border-line bg-surface p-6 shadow-card">
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-accent/10 text-xl font-semibold text-accent">
          {initial}
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-lg font-semibold text-navy">{user.name}</h2>
          <p className="truncate text-sm text-navy/60">{user.email}</p>
          {user.created_at ? (
            <p className="mt-1 text-xs text-navy/45">
              Joined {formatDate(user.created_at)}
            </p>
          ) : null}
        </div>
        <Link
          href="/student-dashboard/profile"
          className="rounded-md border border-line px-4 py-2 text-sm font-medium text-navy transition-colors hover:bg-elevated"
        >
          View Profile
        </Link>
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {counts.map(({ label, value }) => (
          <div
            key={label}
            className="rounded-xl border border-line bg-elevated p-3 text-center"
          >
            <dt className="text-xs text-navy/50">{label}</dt>
            <dd className="mt-1 text-xl font-semibold text-navy">
              {resumeLoading ? <span>&ndash;</span> : value ?? 0}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}