export default function DashboardHeader() {
  return (
    <header className="flex items-center justify-between border-b border-border bg-white px-6 py-4">
      <h1 className="text-sm font-medium text-navy/60">Dashboard</h1>
      <div className="flex items-center gap-3">
        <div className="h-8 w-8 rounded-full bg-accent/20" />
      </div>
    </header>
  );
}
