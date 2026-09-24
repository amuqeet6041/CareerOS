// Hero band used on the public jobs surface (theme-aware; matches the
// Navbar/landing palette). Safe to render in a server-side Suspense fallback.
export default function JobHero({ children }) {
  return (
    <section className="relative overflow-hidden bg-canvas pb-16 pt-28">
      <div className="pointer-events-none absolute left-1/2 top-[-180px] h-[360px] w-[720px] -translate-x-1/2 rounded-full bg-primary/10 blur-[100px]" />
      <div
        className="pointer-events-none absolute inset-0 bg-grid opacity-[0.35] [mask-image:radial-gradient(ellipse_at_top,black_15%,transparent_70%)]"
        aria-hidden="true"
      />
      <div className="relative mx-auto w-full max-w-6xl px-4 sm:px-6">
        <h1 className="text-3xl font-bold tracking-tight text-navy sm:text-4xl">
          Browse Jobs
        </h1>
        <p className="mt-3 max-w-xl text-sm leading-6 text-muted">
          Find opportunities that fit your skills and experience.
        </p>
        {children ? <div className="mt-6 max-w-2xl">{children}</div> : null}
      </div>
    </section>
  );
}