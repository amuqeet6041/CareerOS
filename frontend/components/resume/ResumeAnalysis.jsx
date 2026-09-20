import SkillsList from "./SkillsList";
import EducationList from "./EducationList";
import ExperienceList from "./ExperienceList";
import CertificationsList from "./CertificationsList";

export default function ResumeAnalysis({ analysis }) {
  const statusLabel =
    analysis.analysis_status === "ai_analyzed"
      ? "AI-enhanced analysis"
      : analysis.analysis_status === "ai_failed"
        ? "Analysis fell back to a basic (non-AI) parse"
        : "Basic parse (AI analysis not enabled)";

  return (
    <div className="space-y-6">
      {analysis.total_experience_years != null && (
        <p className="text-sm text-navy/70">
          Total experience: <span className="font-semibold text-navy">{analysis.total_experience_years} years</span>
        </p>
      )}
      <p className="text-sm text-navy/50">{statusLabel}</p>
      <SkillsList skills={analysis.skills ?? []} />
      <EducationList education={analysis.education ?? []} />
      <ExperienceList experience={analysis.experience ?? []} />
      <CertificationsList certifications={analysis.certifications ?? []} />
    </div>
  );
}