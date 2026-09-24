"use client";

import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import { useState } from "react";

const MAX_WIDTH = {
  xl: "max-w-xl",
  "2xl": "max-w-2xl",
  "3xl": "max-w-3xl",
  "4xl": "max-w-4xl",
  "5xl": "max-w-5xl",
  "6xl": "max-w-6xl",
  "7xl": "max-w-7xl",
};

export default function DashboardShell({ children, maxWidth = "6xl" }) {
  const [navOpen, setNavOpen] = useState(false);

  return (
    <div className="min-h-screen bg-canvas">
      {/* Desktop aside is fixed on the left (sm+). The mobile drawer is
          rendered by DashboardSidebar via its own fixed overlay panel. */}
      <DashboardSidebar open={navOpen} onClose={() => setNavOpen(false)} />
      <div className="flex min-h-screen flex-col sm:pl-64">
        <DashboardHeader onOpenMenu={() => setNavOpen(true)} />
        <main
          className={`mx-auto w-full ${MAX_WIDTH[maxWidth] ?? MAX_WIDTH["6xl"]} space-y-6 px-4 py-8 sm:px-6`}
        >
          {children}
        </main>
      </div>
    </div>
  );
}