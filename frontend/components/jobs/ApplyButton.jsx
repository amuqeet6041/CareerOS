// Apply Now navigates to the job's external application_url in a new tab.
// Navigation is never faked: without a URL the control is disabled and
// explains why. Saved-job persistence arrives in Phase 5 and is intentionally
// absent here.
export default function ApplyButton({ url, className = "" }) {
  const base =
    "inline-flex items-center justify-center gap-1.5 rounded-md px-4 py-2 text-sm font-medium transition-colors";

  if (!url) {
    return (
      <button
        type="button"
        disabled
        title="Application link unavailable"
        aria-disabled="true"
        className={`${base} cursor-not-allowed border border-border bg-surface text-navy/40 ${className}`}
      >
        Apply
      </button>
    );
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className={`${base} bg-accent text-white hover:bg-accent-light ${className}`}
    >
      Apply
      <span className="sr-only"> (opens in a new tab)</span>
    </a>
  );
}