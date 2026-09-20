import DashboardSection from "@/components/dashboard/DashboardSection";
import { priorityStyles } from "./priority";

function StatusBanner({ ai }) {
  if (ai.status === "available") {
    return (
      <div className="rounded-xl border border-green-200 bg-green-50 p-4">
        <p className="text-sm text-green-800">
          <span className="font-semibold">AI analysis:</span>{" "}
          {ai.summary || "Personalized explanations from your career data."}
        </p>
      </div>
    );
  }
  if (ai.status === "failed") {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
        <p className="text-sm text-amber-800">
          AI insights temporarily unavailable. Your deterministic analysis above
          remains fully up to date.
        </p>
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <p className="text-sm text-navy/60">
        AI-powered explanations are not configured in this environment. The career
        analysis below is computed deterministically from your resume and the jobs
        on our platform.
      </p>
    </div>
  );
}

export default function AICareerInsights({ ai }) {
  return (
    <DashboardSection
      title="AI career insights"
      subtitle="Optional AI explanations grounded only in your verified data."
    >
      <StatusBanner ai={ai} />
      {ai.status === "available" ? (
        <div className="mt-4 space-y-6">
          {ai.career_directions?.length > 0 ? (
            <div>
              <h3 className="mb-2 text-sm font-semibold text-navy">Suggested paths</h3>
              <ul className="space-y-3">
                {ai.career_directions.map((direction) => (
                  <li
                    key={direction.title}
                    className="rounded-xl border border-border bg-surface p-3"
                  >
                    <p className="text-sm font-semibold text-navy">{direction.title}</p>
                    {direction.reason ? (
                      <p className="mt-1 text-xs text-navy/60">{direction.reason}</p>
                    ) : null}
                    {direction.next_steps?.length > 0 ? (
                      <ul className="mt-2 list-disc space-y-0.5 pl-4">
                        {direction.next_steps.map((step, idx) => (
                          <li key={`${direction.title}-${idx}`} className="text-xs text-navy/70">
                            {step}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {ai.skill_development?.length > 0 ? (
            <div>
              <h3 className="mb-2 text-sm font-semibold text-navy">Skills to develop</h3>
              <div className="flex flex-wrap gap-2">
                {ai.skill_development.map((item) => (
                  <div
                    key={item.skill}
                    className="rounded-full border border-border bg-surface py-1 pl-3 pr-1"
                  >
                    <span className="text-xs font-medium text-navy">{item.skill}</span>
                    <span
                      className={`ml-2 rounded-full px-2 py-0.5 text-[10px] font-semibold ${priorityStyles(item.priority)}`}
                    >
                      {item.priority}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {ai.resume_suggestions?.length > 0 ? (
            <div>
              <h3 className="mb-2 text-sm font-semibold text-navy">Resume suggestions</h3>
              <ul className="space-y-1.5">
                {ai.resume_suggestions.map((suggestion, idx) => (
                  <li key={`rs-${idx}`} className="flex gap-2 text-sm text-navy/70">
                    <span className="text-green-600">&check;</span>
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {ai.action_plan?.length > 0 ? (
            <div>
              <h3 className="mb-2 text-sm font-semibold text-navy">Suggested next steps</h3>
              <ul className="space-y-1.5">
                {ai.action_plan.map((step, idx) => (
                  <li key={`ap-${idx}`} className="flex gap-2 text-sm text-navy/70">
                    <span className="font-semibold text-accent">{idx + 1}.</span>
                    {step}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </DashboardSection>
  );
}