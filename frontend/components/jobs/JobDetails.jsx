import { formatSalary } from "@/utils/formatters";

export default function JobDetails({ job }) {
  if (!job) return null;

  const salary = formatSalary(job.salary_min, job.salary_max, job.currency);

  return (
    <div className="rounded-lg border border-line bg-surface p-6">
      <h2 className="text-xl font-semibold text-navy">{job.title}</h2>
      <p className="text-navy/60">{job.company}</p>

      <div className="mt-2 flex flex-wrap gap-3 text-xs text-navy/60">
        {job.location ? <span>{job.location}</span> : null}
        {job.work_mode ? (
          <span className="capitalize">&bull; {job.work_mode}</span>
        ) : null}
        {job.employment_type ? (
          <span className="capitalize">&bull; {job.employment_type.replace("-", " ")}</span>
        ) : null}
        {salary && salary !== "Not specified" ? <span>&bull; {salary}</span> : null}
        {job.minimum_experience_years != null ? (
          <span>&bull; {job.minimum_experience_years}+ yrs</span>
        ) : null}
      </div>

      {job.application_url ? (
        <div className="mt-4">
          <a
            href={job.application_url}
            target="_blank"
            rel="noreferrer"
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-accent-light"
          >
            Apply
          </a>
        </div>
      ) : null}

      <div className="mt-4">
        <h3 className="text-sm font-semibold text-navy">Description</h3>
        <p className="mt-1 text-sm text-navy/70">
          {job.description || "No description available yet."}
        </p>
      </div>

      {job.skills?.length ? (
        <div className="mt-4">
          <h3 className="text-sm font-semibold text-navy">Required Skills</h3>
          <div className="mt-1 flex flex-wrap gap-2">
            {job.skills.map((skill) => (
              <span
                key={skill.skill_name}
                className="rounded-full bg-elevated px-3 py-1 text-xs text-navy"
              >
                {skill.skill_name}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {job.qualifications?.length ? (
        <div className="mt-4">
          <h3 className="text-sm font-semibold text-navy">Qualifications</h3>
          <ul className="mt-1 list-disc pl-5 text-sm text-navy/70">
            {job.qualifications.map((qualification) => (
              <li key={qualification.qualification}>{qualification.qualification}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}