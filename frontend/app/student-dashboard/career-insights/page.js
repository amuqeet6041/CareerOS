import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import CareerOverview from "@/components/dashboard/CareerOverview";

export default function CareerInsightsPage() {
  return (
    <div className="flex min-h-screen bg-surface">
      <DashboardSidebar />
      <div className="flex-1">
        <DashboardHeader />
        <main className="mx-auto max-w-6xl px-6 py-8">
          <h1 className="text-2xl font-semibold text-navy">Career Insights</h1>
          <div className="mt-6">
            <CareerOverview />
          </div>
        </main>
      </div>
    </div>
  );
}
