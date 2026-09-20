// Dark hero band used on the public jobs surface (matches the Navbar/landing
// palette). Safe to render in a server-side Suspense fallback.
export default function JobHero({ children }) {
  return (
    <section className="bg-[#07111F] pb-16 pt-28">
      <div className="mx-auto w-full max-w-6xl px-4 sm:px-6">
        <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          Browse Jobs
        </h1>
        <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">
          Find opportunities that fit your skills and experience.
        </p>
        {children ? <div className="mt-6 max-w-2xl">{children}</div> : null}
      </div>
    </section>
  );
}