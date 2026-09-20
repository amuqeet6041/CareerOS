import { formatSalary } from "@/utils/formatters";

// `job` shape follows the backend Job schema (see backend/app/schemas/job.py):
// { id, title, company, description, employment_type, work_mode, location,
//   salary_min, salary_max, currency, application_url, skills, ... }
export default function JobCard({ job }) {
  const salary = formatSalary(job.salary_min, job.salary_max, job.currency);

  return (
    <div className="rounded-lg border border-border bg-white p-5">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-navy">{job.title}</h3>
          <p className="text-sm text-navy/60">{job.company}</p>
        </div>
        {salary && salary !== "Not specified" ? (
          <span className="text-sm font-medium text-navy/70">{salary}</span>
        ) : null}
      </div>

      <div className="mt-3 flex flex-wrap gap-3 text-xs text-navy/60">
        {job.city ? <span>{job.city}</span> : job.location ? <span>{job.location}</span> : null}
        {job.country && job.city ? <span>&bull; {job.country}</span> : null}
        {job.work_mode ? (
          <span className="capitalize">&bull; {job.work_mode}</span>
        ) : null}
        {job.employment_type ? (
          <span className="capitalize">&bull; {job.employment_type.replace("-", " ")}</span>
        ) : null}
      </div>

      <div className="mt-4 flex gap-3">
        {job.application_url ? (
          <a
            href={job.application_url}
            target="_blank"
            rel="noreferrer"
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-light"
          >
            Apply
          </a>
        ) : null}
        <button className="rounded-md border border-border px-4 py-2 text-sm font-medium text-navy hover:bg-surface">
          Save
        </button>
      </div>
    </div>
  );
}