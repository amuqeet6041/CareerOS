import { Suspense } from "react";

import Navbar from "@/components/shared/Navbar";
import Footer from "@/components/shared/Footer";
import JobsExplorer from "@/components/jobs/JobsExplorer";
import JobHero from "@/components/jobs/JobHero";
import { JobCardSkeleton } from "@/components/jobs/Skeletons";

// Public jobs browsing page (no auth required). The explorer is client-side
// and reads the URL query string, so it must be wrapped in Suspense to keep
// the route statically pre-rendered.
export default function PublicJobsPage() {
  return (
    <>
      <Navbar />
      <main>
        <Suspense
          fallback={
            <>
              <JobHero>
                <div
                  aria-hidden="true"
                  className="flex w-full gap-2"
                >
                  <div className="h-12 flex-1 animate-pulse rounded-xl border border-line bg-elevated" />
                  <div className="h-12 w-28 animate-pulse rounded-xl bg-accent/60" />
                </div>
              </JobHero>
              <div className="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6">
                <p className="mb-5 text-sm text-navy/60">Loading jobs&hellip;</p>
                <div className="grid gap-4 md:grid-cols-2" aria-busy="true">
                  {Array.from({ length: 6 }, (_, index) => (
                    <JobCardSkeleton key={index} />
                  ))}
                </div>
              </div>
            </>
          }
        >
          <JobsExplorer variant="public" />
        </Suspense>
      </main>
      <Footer />
    </>
  );
}