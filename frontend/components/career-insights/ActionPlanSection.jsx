import DashboardSection from "@/components/dashboard/DashboardSection";

export default function ActionPlanSection({ actionPlan, resumeSuggestions }) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <DashboardSection
        title="Your action plan"
        subtitle="Evidence-based next steps from your current profile."
      >
        {actionPlan.length === 0 ? (
          <p className="text-sm text-navy/50">Build your profile to unlock a plan.</p>
        ) : (
          <ol className="space-y-2.5">
            {actionPlan.map((step, idx) => (
              <li key={idx} className="flex gap-3 text-sm text-navy/80">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent/10 text-xs font-bold text-accent">
                  {idx + 1}
                </span>
                <span className="pt-0.5">{step}</span>
              </li>
            ))}
          </ol>
        )}
      </DashboardSection>

      <DashboardSection
        title="Resume suggestions"
        subtitle="Ways to make your profile easier to assess."
      >
        {resumeSuggestions.length === 0 ? (
          <p className="text-sm text-navy/50">No suggestions right now.</p>
        ) : (
          <ul className="space-y-2">
            {resumeSuggestions.map((suggestion, idx) => (
              <li
                key={idx}
                className="flex gap-2 rounded-xl border border-border bg-surface p-3 text-sm text-navy/70"
              >
                <span className="text-green-600">&check;</span>
                {suggestion}
              </li>
            ))}
          </ul>
        )}
      </DashboardSection>
    </div>
  );
}