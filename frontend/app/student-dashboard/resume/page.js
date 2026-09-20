import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import ResumeManager from "@/components/resume/ResumeManager";

export default function ResumePage() {
  return (
    <div className="flex min-h-screen bg-surface">
      <DashboardSidebar />
      <div className="flex-1">
        <DashboardHeader />
        <main className="mx-auto max-w-4xl space-y-8 px-6 py-8">
          <h1 className="text-2xl font-semibold text-navy">Resume</h1>
          <ResumeManager />
        </main>
      </div>
    </div>
  );
}