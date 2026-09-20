import Navbar from "@/components/shared/Navbar";
import Footer from "@/components/shared/Footer";
import JobList from "@/components/jobs/JobList";

// Public jobs browsing page (no auth required).
export default function PublicJobsPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-6 py-16">
        <h1 className="text-3xl font-semibold text-navy">Browse Jobs</h1>
        <p className="mt-2 text-navy/70">
          Sign in to see personalized match scores for each job.
        </p>
        <div className="mt-8">
          <JobList jobs={[]} />
        </div>
      </main>
      <Footer />
    </>
  );
}
