import JobCard from "./JobCard";
import EmptyState from "@/components/shared/EmptyState";

export default function JobList({ jobs = [] }) {
  if (jobs.length === 0) {
    return (
      <EmptyState
        title="No jobs to show"
        description="Once job sources are connected, matching jobs will appear here."
      />
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} />
      ))}
    </div>
  );
}
