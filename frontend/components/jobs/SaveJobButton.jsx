"use client";

import { useState } from "react";
import Link from "next/link";
import { Bookmark, Loader2 } from "lucide-react";

// Save / un-save a job. The button only updates its visual state after the
// backend confirms the mutation (via the parent's `onToggle`), so a failed
// request never shows success. Unauthenticated users get a sign-in link
// instead of a save request that is expected to fail.
export default function SaveJobButton({
  jobId,
  jobTitle = "",
  saved = false,
  authenticated = true,
  disabled = false,
  onToggle = null,
  className = "",
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const base =
    "inline-flex items-center justify-center gap-1.5 rounded-md border px-3 py-2 text-sm font-medium transition-colors";

  if (!authenticated) {
    return (
      <Link
        href="/login"
        aria-label={`Sign in to save ${jobTitle}`}
        className={`${base} border-border bg-white text-navy hover:bg-surface ${className}`}
      >
        <Bookmark className="h-4 w-4" aria-hidden="true" />
        Save
      </Link>
    );
  }

  async function handleClick() {
    if (!onToggle || busy) return;
    setBusy(true);
    setError(null);
    try {
      await onToggle(jobId, saved);
    } catch (err) {
      setError(
        err?.message || `Couldn't ${saved ? "unsave" : "save"} this job right now.`
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <span className={`inline-flex flex-col items-stretch ${className}`}>
      <button
        type="button"
        onClick={handleClick}
        disabled={busy || disabled}
        aria-pressed={saved}
        aria-label={
          saved ? `Remove ${jobTitle} from saved jobs` : `Save ${jobTitle}`
        }
        className={`${base} ${
          saved
            ? "border-accent/40 bg-accent/10 text-accent hover:bg-accent/20"
            : "border-border bg-white text-navy hover:bg-surface"
        } ${busy || disabled ? "cursor-not-allowed opacity-60" : ""}`}
      >
        {busy ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          <Bookmark
            className={`h-4 w-4 ${saved ? "fill-current" : ""}`}
            aria-hidden="true"
          />
        )}
        {saved ? "Saved" : "Save"}
      </button>
      {error ? (
        <span role="alert" className="mt-1 text-xs text-red-600">
          {error}
        </span>
      ) : null}
    </span>
  );
}