// Shared skeleton placeholders for job surfaces (list + detail) while data
// loads. They mirror the real card shapes so layout doesn't jump on arrival.

export function JobCardSkeleton() {
  return (
    <div className="rounded-lg border border-line bg-elevated p-5" aria-hidden="true">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="skeleton h-3 w-24 rounded" />
          <div className="skeleton h-4 w-48 rounded" />
        </div>
        <div className="skeleton h-4 w-24 rounded" />
      </div>
      <div className="skeleton mt-4 h-3 w-3/4 rounded" />
      <div className="mt-6 flex gap-3">
        <div className="skeleton h-9 w-24 rounded-md" />
        <div className="skeleton h-9 w-20 rounded-md" />
      </div>
    </div>
  );
}

export function JobDetailSkeleton() {
  return (
    <div aria-hidden="true">
      <div className="skeleton h-4 w-24 rounded" />
      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-4 rounded-lg border border-line bg-elevated p-6">
          <div className="skeleton h-3 w-28 rounded" />
          <div className="skeleton h-6 w-2/3 rounded" />
          <div className="skeleton h-3 w-1/2 rounded" />
          <div className="skeleton h-40 rounded" />
        </div>
        <div className="space-y-6">
          <div className="skeleton h-40 rounded-lg" />
          <div className="skeleton h-52 rounded-lg" />
        </div>
      </div>
    </div>
  );
}