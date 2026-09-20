export default function ProfileSummary({ completion = 0 }) {
  return (
    <div className="rounded-lg border border-border bg-white p-6">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-navy">Profile Completion</h2>
        <span className="text-sm font-medium text-navy/70">{completion}%</span>
      </div>
      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-border">
        <div className="h-full rounded-full bg-accent" style={{ width: `${completion}%` }} />
      </div>
    </div>
  );
}
