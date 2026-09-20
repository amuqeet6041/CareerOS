import Navbar from "@/components/shared/Navbar";
import Footer from "@/components/shared/Footer";

export default function AboutPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="text-3xl font-semibold text-navy">About CareerOS</h1>
        <p className="mt-4 text-navy/70">
          CareerOS is an AI-powered career platform that helps job seekers understand
          their own profile and find opportunities that genuinely match their skills
          and qualifications. This page is a placeholder &mdash; replace it with real
          content about the team and mission.
        </p>
      </main>
      <Footer />
    </>
  );
}
