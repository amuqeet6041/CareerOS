import Link from "next/link";
import MatchScore from "./MatchScore";
import { EXPERIENCE_STATUS_LABELS, formatMatchPercentage } from "@/utils/formatters";

// Renders every state of /api/jobs/{id}/match without guessing:
// sign-in prompt, missing resume, transient error (retry), or the full score
// plus the deterministic explanation returned by the backend.

function ChipList({ title, items, tone }) {
  if (!items || items.length === 0) return null;

  const tones = {
    ok: "bg-success/10 text-success border border-success/20",
    warn: "bg-warning/10 text-warning border border-warning/30",
  };

  return (
    <div>
      <h4 className="text-xs font-semibold uppercase tracking-wide text-navy/50">
        {title}
      </h4>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {items.map((item) => (
          <span
            key={item}
            className={`rounded-full px-2.5 py-1 text-xs font-medium ${tones[tone] ?? tones.ok}`}
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

function ExperienceLine({ match }) {
  const status = match.experience_status;
  const label = EXPERIENCE_STATUS_LABELS[status];

  const bits = [];
  if (match.candidate_experience_years != null) {
    bits.push(`${match.candidate_experience_years} yrs experience`);
  }
  if (status && !["no_requirement", "unknown"].includes(status)) {
    if (match.minimum_required_years != null || match.maximum_required_years != null) {
      const range = [];
      if (match.minimum_required_years != null) range.push(`min ${Math.round(match.minimum_required_years)} yrs`);
      if (match.maximum_required_years != null) range.push(`max ${Math.round(match.maximum_required_years)} yrs`);
      if (range.length) bits.push(`required ${range.join(", ")}`);
    }
  }

  return (
    <div className="rounded-lg bg-elevated px-3 py-2.5">
      <p className="text-xs font-medium text-navy/70">
        {label || "Experience"}
      </p>
      {bits.length ? (
        <p className="mt-0.5 text-xs text-navy/50">{bits.join(" · ")}</p>
      ) : null}
    </div>
  );
}

export default function MatchCard({ status = "idle", data = null, onRetry, onSignIn, onUploadResume }) {
  if (status === "sign-in") {
    return (
      <Panel title="Your match">
        <p className="text-sm text-navy/60">
          Sign in to see your personalized match score for this job.
        </p>
        <Link
          href="/login"
          className="mt-4 inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-accent-light"
        >
          Sign in
        </Link>
      </Panel>
    );
  }

  if (status === "no-resume") {
    return (
      <Panel title="Your match">
        <p className="text-sm text-navy/60">
          Upload your resume to see how well this job fits your profile.
        </p>
        <Link
          href="/student-dashboard/resume"
          className="mt-4 inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-accent-light"
        >
          Upload resume
        </Link>
      </Panel>
    );
  }

  if (status === "loading" || status === "idle") {
    return (
      <Panel title="Your match">
        <div className="space-y-3">
          <div className="h-16 w-16 animate-pulse rounded-2xl bg-elevated-strong" />
          <div className="h-3 w-full max-w-[220px] animate-pulse rounded bg-elevated-strong" />
          <div className="h-3 w-3/4 animate-pulse rounded bg-elevated-strong" />
        </div>
      </Panel>
    );
  }

  if (status === "error") {
    return (
      <Panel title="Your match">
        <p className="text-sm text-navy/60">
          We couldn&apos;t calculate your match right now.
        </p>
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 inline-flex rounded-md border border-line px-4 py-2 text-sm font-medium text-navy hover:bg-elevated"
        >
          Try again
        </button>
      </Panel>
    );
  }

  if (status === "success" && data) {
    return (
      <Panel title="Your match">
        <MatchScore match={data} />

        {data.summary ? (
          <p className="text-sm leading-6 text-navy/70">{data.summary}</p>
        ) : null}

        <div className="space-y-4">
          <ExperienceLine match={data} />
          <ChipList title="Matched skills" items={data.matched_skills} tone="ok" />
          <ChipList title="Missing skills" items={data.missing_skills} tone="warn" />
          <ChipList title="Matched qualifications" items={data.matched_qualifications} tone="ok" />
          <ChipList title="Missing qualifications" items={data.missing_qualifications} tone="warn" />
        </div>
      </Panel>
    );
  }

  return null;
}

function Panel({ title, children }) {
  return (
    <section className="rounded-lg border border-line bg-surface p-5">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-navy/50">
        {title}
      </h2>
      <div className="mt-3">{children}</div>
    </section>
  );
}