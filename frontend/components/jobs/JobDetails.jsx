import { formatSalary } from "@/utils/formatters";

export default function JobDetails({ job }) {
  if (!job) return null;

  const salary = formatSalary(job.salary_min, job.salary_max, job.currency);

  return (
    <div className="rounded-lg border border-border bg-white p-6">
      <h2 className="text-xl font-semibold text-navy">{job.title}</h2>
      <p className="text-navy/60">{job.company}</p>

      <div className="mt-2 flex flex-wrap gap-3 text-xs text-navy/60">
        {job.location ? <span>{job.location}</span> : null}
        {job.work_mode ? <span>&bull; {job.work_mode}</span> : null}
        {job.job_type ? <span>&bull; {job.job_type}</span> : null}
        {salary && salary !== "Not specified" ? <span>&bull; {salary}</span> : null}
      </div>

      <div className="mt-4">
        <h3 className="text-sm font-semibold text-navy">Description</h3>
        <p className="mt-1 text-sm text-navy/70">
          {job.description || "No description available yet."}
        </p>
      </div>
    </div>
  );
}