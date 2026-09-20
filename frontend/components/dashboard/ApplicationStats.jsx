const DEFAULT_STATS = [
  { label: "Applied", value: 0 },
  { label: "In Review", value: 0 },
  { label: "Interviews", value: 0 },
  { label: "Offers", value: 0 },
];

export default function ApplicationStats({ stats = DEFAULT_STATS }) {
  return (
    <div className="rounded-lg border border-border bg-white p-6">
      <h2 className="mb-4 font-semibold text-navy">Application Stats</h2>
      <div className="grid grid-cols-2 gap-4">
        {stats.map((s) => (
          <div key={s.label}>
            <p className="text-2xl font-semibold text-navy">{s.value}</p>
            <p className="text-xs text-navy/60">{s.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
