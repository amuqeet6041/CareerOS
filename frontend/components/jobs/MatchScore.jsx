export default function MatchScore({ label, percentage = 0 }) {
  const clamped = Math.max(0, Math.min(100, percentage));

  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-24 overflow-hidden rounded-full bg-border">
        <div
          className="h-full rounded-full bg-success"
          style={{ width: `${clamped}%` }}
        />
      </div>
      <span className="text-xs font-medium text-navy/70">
        {label}: {clamped}%
      </span>
    </div>
  );
}
