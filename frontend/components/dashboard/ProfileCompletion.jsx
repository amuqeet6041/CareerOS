import { Check } from "lucide-react";
import { computeProfileCompletion } from "@/lib/profileCompletion";

// Progress bar + legend for profile completion. The percentage is computed by
// the pure formula in lib/profileCompletion.js over real profile/resume data
// and never guessed. Legend lives in the same card so the number is explainable.

export default function ProfileCompletion({ user, resume = null }) {
  const completion = computeProfileCompletion({ user, resume });

  return (
    <section className="rounded-2xl border border-line bg-surface p-6 shadow-card">
      <div className="flex flex-wrap items-center gap-6">
        <div className="text-center">
          <p className="text-3xl font-semibold text-accent">{completion.percentage}%</p>
          <p className="mt-1 text-xs text-navy/50">profile complete</p>
        </div>
        <div className="min-w-0 flex-1">
          <div
            className="h-2.5 w-full overflow-hidden rounded-full bg-line/40"
            role="meter"
            aria-label="Profile completion"
            aria-valuemin={0}
            aria-valuemax={completion.total}
            aria-valuenow={completion.completed}
          >
            <div
              className="h-full rounded-full bg-gradient-to-r from-accent to-accent-light"
              style={{ width: `${completion.percentage}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-navy/60">
            {completion.completed} of {completion.total} sections carry real
            data.
          </p>
        </div>
      </div>

      <ul className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
        {completion.components.map(({ key, label, met }) => (
          <li
            key={key}
            title={met ? "Completed" : "Not yet"}
            className="flex min-w-0 items-center gap-2 text-xs"
          >
            <span
              className={`inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full ${
                met ? "bg-success text-white" : "bg-elevated-strong text-navy/40"
              }`}
            >
              {met ? (
                <Check className="h-3 w-3" aria-hidden="true" />
              ) : (
                <span className="h-1.5 w-1.5 rounded-full bg-current" />
              )}
            </span>
            <span className={met ? "truncate text-navy/80" : "truncate text-navy/40"}>
              {label}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}