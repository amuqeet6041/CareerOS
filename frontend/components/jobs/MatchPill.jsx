import { formatMatchPercentage } from "@/utils/formatters";

// Compact per-card match indicator for job lists. Each state carries a text
// label (never just a color), and unknowns never masquerade as 0% or 100%.

export default function MatchPill({ match = null, loading = false }) {
  if (loading) {
    return (
      <div className="mt-3 flex w-fit items-center rounded-full bg-surface px-2.5 py-1 text-xs font-medium text-navy/50">
        <span className="mr-2 inline-block h-2 w-2 animate-pulse rounded-full bg-border" />
        Scoring&hellip;
      </div>
    );
  }

  if (!match) return null;

  if (match.status === "success") {
    const overall = formatMatchPercentage(match.data?.overall_match_percentage);
    if (overall != null) {
      return (
        <div className="mt-3 flex w-fit items-center rounded-full bg-success/10 px-2.5 py-1 text-xs font-medium text-success">
          {overall} match
        </div>
      );
    }
    return (
      <div className="mt-3 flex w-fit items-center rounded-full bg-border/50 px-2.5 py-1 text-xs font-medium text-navy/50">
        Scores unavailable
      </div>
    );
  }

  if (match.status === "no-resume") {
    return (
      <div className="mt-3 flex w-fit items-center rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700">
        Resume needed
      </div>
    );
  }

  return null;
}