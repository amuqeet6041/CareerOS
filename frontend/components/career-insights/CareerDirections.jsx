import DashboardSection from "@/components/dashboard/DashboardSection";

function SkillChips({ skills, missing }) {
  if (skills.length === 0) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {skills.map((skill) => (
        <span
          key={`${missing ? "missing" : "support"}-${skill}`}
          className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium ${
            missing
              ? "border border-warning/30 bg-warning/10 text-warning"
              : "border border-accent/15 bg-accent/10 text-accent"
          }`}
        >
          {skill}
        </span>
      ))}
    </div>
  );
}

export default function CareerDirections({ directions }) {
  return (
    <DashboardSection
      title="Potential career paths"
      subtitle="Current jobs grouped by role, matched against your profile."
    >
      {directions.length === 0 ? (
        <p className="text-sm text-navy/50">
          No role patterns found yet. Career directions appear once relevant jobs
          exist on the platform.
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {directions.map((direction) => (
            <div
              key={direction.title}
              className="rounded-xl border border-line bg-surface p-4"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-semibold text-navy">{direction.title}</p>
                {direction.average_match != null ? (
                  <span className="rounded-full border border-success/30 bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success">
                    {direction.average_match}% match
                  </span>
                ) : null}
              </div>
              <p className="mt-1 text-xs text-navy/50">
                {direction.matching_job_count}{" "}
                {direction.matching_job_count === 1 ? "job" : "jobs"} analyzed
              </p>
              {direction.explanation ? (
                <p className="mt-2 text-xs text-navy/70">{direction.explanation}</p>
              ) : null}
              <SkillChips skills={direction.supporting_skills} missing={false} />
              <SkillChips skills={direction.missing_skills} missing />
            </div>
          ))}
        </div>
      )}
    </DashboardSection>
  );
}