import JobCard from "./JobCard";
import EmptyState from "@/components/shared/EmptyState";

export default function JobList({ jobs = [] }) {
  if (jobs.length === 0) {
    return (
      <EmptyState
        title="No jobs to show"
        description="Try adjusting your filters. Run `python -m app.cli seed-jobs` on the backend to load the demo jobs."
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
