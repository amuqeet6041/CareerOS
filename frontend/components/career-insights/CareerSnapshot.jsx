import DashboardSection from "@/components/dashboard/DashboardSection";

export default function CareerSnapshot({ summary }) {
  const chips = [...(summary.skills ?? [])];
  const fields = [];

  if (summary.total_experience_years != null) {
    fields.push({
      label: "Experience",
      value: `${summary.total_experience_years} years`,
    });
  }
  if ((summary.education ?? []).length > 0) {
    fields.push({ label: "Education", value: `${summary.education.length} entries` });
  }
  if ((summary.certifications ?? []).length > 0) {
    fields.push({ label: "Certifications", value: `${summary.certifications.length}` });
  }
  if (summary.experience_entries > 0) {
    fields.push({ label: "Work entries", value: `${summary.experience_entries}` });
  }

  return (
    <DashboardSection
      title="Your verified profile"
      subtitle="Facts extracted from your uploaded resume."
    >
      {chips.length > 0 ? (
        <div className="mb-4 flex flex-wrap gap-2">
          {chips.map((skill, idx) => (
            <span
              key={`${skill}-${idx}`}
              className="rounded-full border border-accent/15 bg-accent/10 px-3 py-1 text-xs font-medium text-accent"
            >
              {skill}
            </span>
          ))}
        </div>
      ) : (
        <p className="mb-4 text-sm text-navy/50">No skills on file yet.</p>
      )}

      {fields.length > 0 ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {fields.map((field) => (
            <div
              key={field.label}
              className="rounded-xl border border-line bg-surface p-3"
            >
              <p className="text-xs text-navy/50">{field.label}</p>
              <p className="mt-1 text-sm font-semibold text-navy">{field.value}</p>
            </div>
          ))}
        </div>
      ) : null}
    </DashboardSection>
  );
}