"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { createApplication } from "@/services/applicationService";

// Apply Now opens the job's external application_url in a new tab. For
// authenticated users it ALSO records an application (createApplication) so
// the job shows up under "My Applications" -- starting here, not faking the
// external submission. The navigation is never faked: without a URL the
// control is disabled and explains why.
//
// The external tab is opened synchronously in the click handler (so popup
// blockers don't swallow it) and tracking runs in the background. A 409
// (already applied) converges to the "Applied" state without creating a
// duplicate record.
export default function ApplyNowButton({
  jobId,
  jobTitle = "",
  url,
  authenticated = true,
  applied = false,
  onTracked = null,
  showTrackedHint = false,
  className = "",
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

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

  function open() {
    window.open(url, "_blank", "noopener,noreferrer");
  }

  function handleClick() {
    setError(null);
    if (authenticated && !applied) {
      setBusy(true);
      createApplication(jobId)
        .then(() => onTracked?.(jobId))
        .catch((err) => {
          if (err?.status === 409) {
            onTracked?.(jobId);
          } else {
            setError(
              err?.message ||
                "Your application couldn't be recorded, but you can still open the employer's application."
            );
          }
        })
        .finally(() => setBusy(false));
    }
    open();
  }

  return (
    <span className={`inline-flex flex-col items-stretch ${className}`}>
      <button
        type="button"
        onClick={handleClick}
        disabled={busy}
        aria-label={
          applied ? `Open application for ${jobTitle}` : `Apply to ${jobTitle}`
        }
        className={`${base} ${
          applied
            ? "border border-accent/30 bg-accent/10 text-accent hover:bg-accent/15"
            : "bg-accent text-white hover:bg-accent-light"
        }`}
      >
        {busy ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : null}
        {applied ? "Applied" : busy ? "Applying..." : "Apply"}
        {!busy && !applied ? (
          <span className="sr-only"> (opens in a new tab)</span>
        ) : null}
      </button>
      {showTrackedHint && applied ? (
        <span className="mt-1 text-center text-xs text-navy/50">
          Tracked in My Applications
        </span>
      ) : null}
      {error ? (
        <span role="alert" className="mt-1 text-center text-xs text-red-600">
          {error}
        </span>
      ) : null}
    </span>
  );
}