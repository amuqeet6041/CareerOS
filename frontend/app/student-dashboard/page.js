import DashboardShell from "@/components/dashboard/DashboardShell";
import StudentDashboard from "@/components/dashboard/StudentDashboard";

export default function DashboardPage() {
  return (
    <DashboardShell>
      <StudentDashboard />
    </DashboardShell>
  );
}