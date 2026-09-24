import Link from "next/link";
import EmptyState from "@/components/shared/EmptyState";
import DashboardSection, { SectionSkeleton } from "./DashboardSection";
import SkillsList from "@/components/resume/SkillsList";
import EducationList from "@/components/resume/EducationList";
import ExperienceList from "@/components/resume/ExperienceList";
import CertificationsList from "@/components/resume/CertificationsList";

// Factual career overview built entirely from the stored resume analysis:
// skills, education, experience, and certifications. It states only what is
// on record -- no advice, skill-gap analysis, or market projections (those
// belong to Phase 7).

export default function CareerOverview({ resume = null, loading = false }) {
  return (
    <DashboardSection
      title="Career overview"
      subtitle="What your resume tells us."
      actionHref="/student-dashboard/resume"
      actionLabel="View resume"
    >
      {loading && !resume ? (
        <SectionSkeleton />
      ) : !resume ? (
        <EmptyState
          title="No career data yet"
          description="Upload a resume to see extracted skills, education, experience, and certifications here."
          action={
            <Link
              href="/student-dashboard/resume"
              className="inline-block rounded-md bg-primary px-4 py-2 text-sm font-medium text-white shadow-glow-primary transition-colors hover:bg-accent-light"
            >
              Upload resume
            </Link>
          }
        />
      ) : (
        <div className="space-y-6">
          {resume.total_experience_years != null ? (
            <p className="text-sm text-navy/70">
              Total experience:{" "}
              <span className="font-semibold text-navy">
                {resume.total_experience_years} years
              </span>
            </p>
          ) : null}
          <SkillsList skills={resume.skills ?? []} />
          <EducationList education={resume.education ?? []} />
          <ExperienceList experience={resume.experience ?? []} />
          <CertificationsList certifications={resume.certifications ?? []} />
        </div>
      )}
    </DashboardSection>
  );
}