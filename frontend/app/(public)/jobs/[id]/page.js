import Navbar from "@/components/shared/Navbar";
import Footer from "@/components/shared/Footer";
import JobDetailView from "@/components/jobs/JobDetailView";

// Public job detail route (/jobs/[id]). Renders the full job alongside the
// authenticated user's match panel; matches are surfaced for signed-in users.
export default function JobDetailPage({ params }) {
  const { id } = params;

  return (
    <>
      <Navbar />
      <main>
        <JobDetailView jobId={id} />
      </main>
      <Footer />
    </>
  );
}