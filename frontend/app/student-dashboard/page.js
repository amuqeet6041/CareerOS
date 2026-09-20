import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import ProfileSummary from "@/components/dashboard/ProfileSummary";
import JobRecommendations from "@/components/dashboard/JobRecommendations";
import ApplicationStats from "@/components/dashboard/ApplicationStats";
import CareerOverview from "@/components/dashboard/CareerOverview";

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen bg-surface">
      <DashboardSidebar />
      <div className="flex-1">
        <DashboardHeader />
        <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
          <ProfileSummary />
          <div className="grid gap-6 lg:grid-cols-2">
            <JobRecommendations />
            <ApplicationStats />
          </div>
          <CareerOverview />
        </main>
      </div>
    </div>
  );
}
