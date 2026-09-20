// Whole-dashboard skeleton shown only while the auth session is being
// restored. Once signed in, each section renders its own per-section skeleton
// so completed sections never flash while slower ones load.

export default function DashboardSkeleton() {
  return (
    <div className="animate-pulse space-y-6" role="status" aria-label="Loading dashboard">
      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <div className="h-40 rounded-2xl bg-border/40" />
          <div className="h-32 rounded-2xl bg-border/40" />
        </div>
        <div className="h-40 rounded-2xl bg-border/40" />
      </div>
      <div className="h-80 rounded-2xl bg-border/40" />
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="h-56 rounded-2xl bg-border/40" />
        <div className="h-56 rounded-2xl bg-border/40" />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="h-40 rounded-2xl bg-border/40" />
        <div className="h-40 rounded-2xl bg-border/40" />
      </div>
    </div>
  );
}