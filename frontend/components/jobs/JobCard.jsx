import Link from "next/link";
import MatchPill from "./MatchPill";
import ApplyButton from "./ApplyButton";
import {
  formatSalary,
  formatDate,
  humanizeLabel,
  formatExperienceRequirement,
} from "@/utils/formatters";

// `job` follows the backend Job schema (backend/app/schemas/job.py).
// `match` is the per-job entry produced by useJobMatches: either a real
// payload ({ status: "success", data: JobMatchResponse }) or a state marker
// (no-resume / error), or null when matches aren't rendered for this view.

export default function JobCard({ job, match = null, matchLoading = false }) {
  const salary = formatSalary(job.salary_min, job.salary_max, job.currency);
  const hasSalary = Boolean(job.salary_min || job.salary_max);
  const location = job.city || job.location;
  const workMode = humanizeLabel(job.work_mode);
  const employmentType = humanizeLabel(job.employment_type);
  const experience = formatExperienceRequirement(
    job.minimum_experience_years,
    job.maximum_experience_years
  );
  const posted = job.posted_at ? formatDate(job.posted_at) : "";

  return (
    <article className="flex flex-col rounded-lg border border-border bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="truncate text-xs font-medium uppercase tracking-wide text-navy/50">
            {job.company}
          </p>
          <h3 className="mt-1">
            <Link
              href={`/jobs/${job.id}`}
              className="text-base font-semibold text-navy hover:text-accent"
            >
              {job.title}
            </Link>
          </h3>
        </div>
        {hasSalary ? (
          <div className="shrink-0 text-right text-sm font-medium text-navy/70">
            {salary}
          </div>
        ) : null}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-navy/60">
        {location ? <span>{location}</span> : null}
        {workMode ? <span>&bull; {workMode}</span> : null}
        {employmentType ? <span>&bull; {employmentType}</span> : null}
        {experience ? <span>&bull; {experience}</span> : null}
        {posted ? <span className="text-navy/45">Posted {posted}</span> : null}
      </div>

      <MatchPill match={match} loading={matchLoading} />

      <div className="mt-4 flex items-center gap-3 border-t border-border/60 pt-4">
        <Link
          href={`/jobs/${job.id}`}
          className="rounded-md border border-border px-4 py-2 text-sm font-medium text-navy transition-colors hover:bg-surface"
        >
          View Job
        </Link>
        <ApplyButton url={job.application_url} />
      </div>
    </article>
  );
}