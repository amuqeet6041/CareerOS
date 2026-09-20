import Link from "next/link";
import { ExternalLink } from "lucide-react";

import ApplicationStatus from "./ApplicationStatus";
import { formatDate, humanizeLabel } from "@/utils/formatters";

// One tracked application. The backend embeds the full job in the response
// (ApplicationOut.job), so each card renders without extra requests. Jobs
// that have since been removed render a muted fallback instead of erroring.
export default function ApplicationCard({ application }) {
  const job = application.job;

  if (!job) {
    return (
      <article className="rounded-lg border border-border bg-white p-5">
        <p className="text-sm text-navy/70">
          This job is no longer available.
        </p>
        <div className="mt-4 flex items-center justify-between gap-3 border-t border-border/60 pt-4">
          <span className="text-xs text-navy/45">
            Applied {formatDate(application.applied_at)}
          </span>
          <ApplicationStatus status={application.status} />
        </div>
      </article>
    );
  }

  const location =
    [job.city, job.country].filter(Boolean).join(", ") || job.location;
  const workMode = humanizeLabel(job.work_mode);
  const employmentType = humanizeLabel(job.employment_type);

  return (
    <article className="rounded-lg border border-border bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-xs font-medium uppercase tracking-wide text-navy/50">
            {job.company}
          </p>
          <h3 className="mt-1 text-base font-semibold text-navy">{job.title}</h3>
        </div>
        <ApplicationStatus status={application.status} />
      </div>

      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-navy/60">
        {location ? <span>{location}</span> : null}
        {workMode ? <span>&bull; {workMode}</span> : null}
        {employmentType ? <span>&bull; {employmentType}</span> : null}
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border/60 pt-4">
        <span className="text-xs text-navy/45">
          Applied {formatDate(application.applied_at)}
        </span>
        <div className="flex items-center gap-2">
          <Link
            href={`/jobs/${job.id}`}
            className="rounded-md border border-border px-3 py-1.5 text-sm font-medium text-navy transition-colors hover:bg-surface"
          >
            View Job
          </Link>
          {job.application_url ? (
            <a
              href={job.application_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-md bg-accent px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-accent-light"
            >
              Open application
              <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
            </a>
          ) : null}
        </div>
      </div>
    </article>
  );
}