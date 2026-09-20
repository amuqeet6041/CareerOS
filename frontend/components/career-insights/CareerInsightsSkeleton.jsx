import DashboardSection, { SectionSkeleton } from "@/components/dashboard/DashboardSection";

export default function CareerInsightsSkeleton() {
  return (
    <div className="space-y-6" role="status" aria-label="Loading career insights">
      <DashboardSection title="Your verified profile">
        <SectionSkeleton />
      </DashboardSection>
      <DashboardSection title="Your strengths">
        <SectionSkeleton />
      </DashboardSection>
      <DashboardSection title="Skill gaps">
        <SectionSkeleton />
      </DashboardSection>
      <DashboardSection title="Potential career paths">
        <SectionSkeleton />
      </DashboardSection>
    </div>
  );
}