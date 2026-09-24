import DashboardSection from "@/components/dashboard/DashboardSection";
import { priorityStyles, priorityLabel } from "./priority";

export default function SkillGapsSection({ skillGaps }) {
  return (
    <DashboardSection
      title="Skill gaps"
      subtitle="Required skills missing from your verified profile, ranked by demand."
    >
      {skillGaps.length === 0 ? (
        <p className="text-sm text-navy/50">
          No skill gaps right now &mdash; your verified skills already cover what
          relevant jobs ask for.
        </p>
      ) : (
        <ul className="space-y-3">
          {skillGaps.map((gap) => (
            <li
              key={gap.skill}
              className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-line bg-surface p-3"
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-semibold text-navy">{gap.skill}</p>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${priorityStyles(gap.priority)}`}
                  >
                    {priorityLabel(gap.priority)}
                  </span>
                </div>
                {gap.why_it_matters ? (
                  <p className="mt-0.5 text-xs text-navy/50">{gap.why_it_matters}</p>
                ) : null}
              </div>
              <span className="text-xs font-medium text-navy/60">
                {gap.relevance_count}{" "}
                {gap.relevance_count === 1 ? "job" : "jobs"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </DashboardSection>
  );
}