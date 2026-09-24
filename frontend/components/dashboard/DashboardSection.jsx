import Link from "next/link";

// Shared building blocks for dashboard sections: a titled card wrapper plus
// per-section loading and error states. Every section owns its own retry so a
// failed request can be recovered without taking down the rest of the page.

export function SectionError({ message = "Couldn't load this section.", onRetry = null }) {
  return (
    <div
      role="alert"
      className="rounded-xl border border-danger/25 bg-danger/5 p-6 text-center"
    >
      <p className="text-sm text-danger">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-md border border-danger/25 bg-surface px-4 py-2 text-sm font-medium text-danger transition-colors hover:bg-danger/10"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}

export function SectionSkeleton({ className = "" }) {
  return (
    <div
      className="space-y-3"
      role="status"
      aria-label="Loading section"
    >
      <div className={`skeleton h-4 w-1/3 rounded ${className}`} />
      <div className="skeleton h-20 w-full rounded-xl" />
      <div className="skeleton h-20 w-full rounded-xl" />
    </div>
  );
}

export default function DashboardSection({
  title,
  subtitle = "",
  actionHref = null,
  actionLabel = "",
  children,
}) {
  return (
    <section className="animate-fade-in-up rounded-2xl border border-line bg-surface p-6 shadow-card">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold text-navy">{title}</h2>
          {subtitle ? (
            <p className="mt-1 text-xs text-navy/50">{subtitle}</p>
          ) : null}
        </div>
        {actionHref && actionLabel ? (
          <Link
            href={actionHref}
            className="text-xs font-medium text-accent transition-colors hover:text-accent-light"
          >
            {actionLabel}
          </Link>
        ) : null}
      </div>
      {children}
    </section>
  );
}