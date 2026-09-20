import EmptyState from "@/components/shared/EmptyState";

export default function JobRecommendations({ jobs = [] }) {
  return (
    <div className="rounded-lg border border-border bg-white p-6">
      <h2 className="mb-4 font-semibold text-navy">Recommended Jobs</h2>
      {jobs.length === 0 ? (
        <EmptyState
          title="No recommendations yet"
          description="Upload a resume to get personalized job recommendations."
        />
      ) : (
        <ul className="space-y-2">
          {jobs.map((job) => (
            <li key={job.id} className="text-sm text-navy/80">
              {job.title} &mdash; {job.company}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
