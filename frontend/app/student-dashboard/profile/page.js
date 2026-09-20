import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";

export default function ProfilePage() {
  return (
    <div className="flex min-h-screen bg-surface">
      <DashboardSidebar />
      <div className="flex-1">
        <DashboardHeader />
        <main className="mx-auto max-w-4xl px-6 py-8">
          <h1 className="text-2xl font-semibold text-navy">Your Profile</h1>
          <p className="mt-2 text-navy/70">
            Placeholder profile page. Populate with data from the resume/profile API.
          </p>
        </main>
      </div>
    </div>
  );
}
