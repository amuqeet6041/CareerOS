import Navbar from "@/components/shared/Navbar";
import Footer from "@/components/shared/Footer";

export default function ContactPage() {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="text-3xl font-semibold text-navy">Contact Us</h1>
        <p className="mt-4 text-navy/70">
          Placeholder contact page. Add a contact form or support email here.
        </p>
      </main>
      <Footer />
    </>
  );
}
