export default function EmptyState({
  title = "Nothing here yet",
  description = "",
  icon = null,
  action = null,
  className = "",
}) {
  return (
    <div
      className={`rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm ${className}`}
    >
      {icon ? (
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-[#3B82F6]">
          {icon}
        </div>
      ) : (
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100">
          <div className="h-2 w-2 rounded-full bg-slate-400" />
        </div>
      )}

      <h3 className="text-base font-semibold text-[#07111F]">
        {title}
      </h3>

      {description ? (
        <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
          {description}
        </p>
      ) : null}

      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}