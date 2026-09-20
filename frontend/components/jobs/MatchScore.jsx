import { formatMatchPercentage } from "@/utils/formatters";

// Match component scores are null when a job has no requirement or the resume
// lacks enough information. Unknowns are always labelled in text ("Not enough
// data"), never rendered as 0% or a bare bar/spinner color.

const COMPONENTS = [
  { label: "Skills", key: "skill_match_percentage", weightKey: "skill" },
  { label: "Qualifications", key: "qualification_match_percentage", weightKey: "qualification" },
  { label: "Experience", key: "experience_match_percentage", weightKey: "experience" },
];

function ScoreRow({ label, percentage }) {
  const pct = formatMatchPercentage(percentage);

  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-sm text-navy/70">{label}</span>
        {pct ? (
          <span className="text-sm font-semibold text-navy">{pct}</span>
        ) : (
          <span className="text-xs text-navy/40">Not enough data</span>
        )}
      </div>
      <div
        className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-border"
        role="img"
        aria-label={pct ? `${label}: ${pct}` : `${label}: not enough data`}
      >
        {pct ? (
          <div
            className="h-full rounded-full bg-accent"
            style={{ width: pct }}
          />
        ) : null}
      </div>
    </div>
  );
}

export default function MatchScore({ match }) {
  if (!match) return null;

  const overall = formatMatchPercentage(match.overall_match_percentage);
  const weights = match.component_weights || {};
  const weightLine = COMPONENTS.filter(({ weightKey }) => weights[weightKey] != null)
    .map(({ label, weightKey }) => `${label} ${weights[weightKey]}%`)
    .join(" · ");

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <div
          className="flex h-16 w-16 items-center justify-center rounded-2xl bg-surface text-xl font-bold text-navy"
          aria-label={overall ? `Overall match ${overall}` : "Overall match not available"}
        >
          {overall ?? "—"}
        </div>
        <div>
          <p className="text-sm font-medium text-navy/70">Overall Match</p>
          {overall ? (
            <p className="text-xs text-navy/50">How well this job fits your profile</p>
          ) : (
            <p className="text-xs text-navy/50">Not enough information to score</p>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {COMPONENTS.map(({ label, key }) => (
          <ScoreRow key={key} label={label} percentage={match[key]} />
        ))}
      </div>

      {weightLine ? (
        <p className="text-xs text-navy/40">
          Weighted as {weightLine}
        </p>
      ) : null}
    </div>
  );
}