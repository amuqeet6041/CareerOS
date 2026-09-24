import Link from "next/link";
import EmptyState from "@/components/shared/EmptyState";

export default function CareerInsightsEmpty() {
  return (
    <EmptyState
      title="Upload a resume to unlock Career Insights"
      description="We analyze your verified skills against active jobs to surface strengths, skill gaps, and potential career paths."
      action={
        <Link
          href="/student-dashboard/resume"
          className="inline-block rounded-md bg-primary px-4 py-2 text-sm font-medium text-white shadow-glow-primary transition-colors hover:bg-accent-light"
        >
          Upload resume
        </Link>
      }
    />
  );
}