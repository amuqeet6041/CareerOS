// Shared skeleton placeholders for job surfaces (list + detail) while data
// loads. They mirror the real card shapes so layout doesn't jump on arrival.

export function JobCardSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-white p-5" aria-hidden="true">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="h-3 w-24 animate-pulse rounded bg-border" />
          <div className="h-4 w-48 animate-pulse rounded bg-border" />
        </div>
        <div className="h-4 w-24 animate-pulse rounded bg-border" />
      </div>
      <div className="mt-4 h-3 w-3/4 animate-pulse rounded bg-border" />
      <div className="mt-6 flex gap-3">
        <div className="h-9 w-24 animate-pulse rounded-md bg-border" />
        <div className="h-9 w-20 animate-pulse rounded-md bg-border" />
      </div>
    </div>
  );
}

export function JobDetailSkeleton() {
  return (
    <div aria-hidden="true">
      <div className="h-4 w-24 animate-pulse rounded bg-border" />
      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-4 rounded-lg border border-border bg-white p-6">
          <div className="h-3 w-28 animate-pulse rounded bg-border" />
          <div className="h-6 w-2/3 animate-pulse rounded bg-border" />
          <div className="h-3 w-1/2 animate-pulse rounded bg-border" />
          <div className="h-40 animate-pulse rounded bg-border" />
        </div>
        <div className="space-y-6">
          <div className="h-40 animate-pulse rounded-lg border border-border bg-white" />
          <div className="h-52 animate-pulse rounded-lg border border-border bg-white" />
        </div>
      </div>
    </div>
  );
}