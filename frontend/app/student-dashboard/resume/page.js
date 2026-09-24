import DashboardShell from "@/components/dashboard/DashboardShell";
import ResumeManager from "@/components/resume/ResumeManager";

export default function ResumePage() {
  return (
    <DashboardShell maxWidth="4xl">
      <div>
        <h1 className="text-2xl font-bold text-navy">Resume</h1>
        <p className="mt-1 text-sm text-navy/50">
          Upload, parse, and analyze your resume.
        </p>
      </div>
      <ResumeManager />
    </DashboardShell>
  );
}