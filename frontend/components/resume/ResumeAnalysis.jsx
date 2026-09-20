import SkillsList from "./SkillsList";
import EducationList from "./EducationList";
import ExperienceList from "./ExperienceList";
import CertificationsList from "./CertificationsList";

export default function ResumeAnalysis({ analysis }) {
  return (
    <div className="space-y-6">
      <SkillsList skills={analysis.skills ?? []} />
      <EducationList education={analysis.education ?? []} />
      <ExperienceList experience={analysis.experience ?? []} />
      <CertificationsList certifications={analysis.certifications ?? []} />
    </div>
  );
}