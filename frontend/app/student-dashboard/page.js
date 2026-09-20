import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import StudentDashboard from "@/components/dashboard/StudentDashboard";

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen bg-surface">
      <DashboardSidebar />
      <div className="flex-1">
        <DashboardHeader />
        <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
          <StudentDashboard />
        </main>
      </div>
    </div>
  );
}