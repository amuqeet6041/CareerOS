export default function EmptyState({
  title = "Nothing here yet",
  description = "",
  icon = null,
  action = null,
  className = "",
}) {
  return (
    <div
      className={`animate-fade-in-up rounded-2xl border border-line bg-surface p-8 text-center shadow-card ${className}`}
    >
      {icon ? (
        <div className="animate-pop-in mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/10 text-accent ring-1 ring-accent/10">
          {icon}
        </div>
      ) : (
        <div className="animate-pop-in mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-elevated ring-1 ring-line">
          <div className="h-2 w-2 rounded-full bg-muted" />
        </div>
      )}

      <h3 className="text-base font-semibold text-navy">{title}</h3>

      {description ? (
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">
          {description}
        </p>
      ) : null}

      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}