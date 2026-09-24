import Navbar from "@/components/shared/Navbar";
import Footer from "@/components/shared/Footer";
import { Info, MessageSquare } from "lucide-react";

export default function ContactPage() {
  return (
    <>
      <Navbar />
      <main className="relative overflow-hidden bg-canvas">
        <div className="pointer-events-none absolute left-1/2 top-0 h-[320px] w-[720px] -translate-x-1/2 rounded-full bg-primary/5 blur-3xl" />

        <div className="mx-auto max-w-3xl px-6 py-20">
          <div className="inline-flex items-center gap-2 rounded-full border border-accent/25 bg-accent/10 px-3 py-1.5 text-xs font-medium text-accent">
            <MessageSquare className="h-3.5 w-3.5" />
            Contact
          </div>

          <h1 className="mt-5 text-3xl font-bold tracking-tight text-navy sm:text-4xl">
            Contact Us
          </h1>

          <div className="mt-6 rounded-2xl border border-line bg-surface p-6 shadow-card sm:p-8">
            <div className="flex gap-3 rounded-xl border border-line bg-elevated p-4">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
              <p className="text-sm leading-6 text-muted">
                Placeholder contact page. Add a contact form or support email
                here.
              </p>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}