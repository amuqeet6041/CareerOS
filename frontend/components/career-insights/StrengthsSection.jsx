import DashboardSection from "@/components/dashboard/DashboardSection";

export default function StrengthsSection({ strengths }) {
  return (
    <DashboardSection
      title="Your strengths"
      subtitle="Verified skills that appear across the jobs relevant to you."
    >
      {strengths.length === 0 ? (
        <p className="text-sm text-navy/50">
          No matching skill demand detected yet. Add more verified skills or check
          back once more jobs are available.
        </p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {strengths.map((strength) => (
            <div
              key={strength.skill}
              className="flex items-center gap-2 rounded-full border border-accent/20 bg-accent/5 py-1 pl-3 pr-1"
            >
              <span className="text-sm font-medium text-navy">{strength.skill}</span>
              <span className="rounded-full bg-accent px-2 py-0.5 text-[11px] font-semibold text-white">
                {strength.relevance_count}{" "}
                {strength.relevance_count === 1 ? "job" : "jobs"}
              </span>
            </div>
          ))}
        </div>
      )}
    </DashboardSection>
  );
}