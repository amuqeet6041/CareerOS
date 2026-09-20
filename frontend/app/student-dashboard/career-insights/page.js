"use client";

import { useEffect } from "react";
import DashboardSidebar from "@/components/dashboard/DashboardSidebar";
import DashboardHeader from "@/components/dashboard/DashboardHeader";
import { SectionError } from "@/components/dashboard/DashboardSection";
import { useCareerInsights } from "@/hooks/useCareerInsights";
import CareerInsightsView from "@/components/career-insights/CareerInsightsView";
import CareerInsightsSkeleton from "@/components/career-insights/CareerInsightsSkeleton";
import CareerInsightsEmpty from "@/components/career-insights/CareerInsightsEmpty";

export default function CareerInsightsPage() {
  const { data, loading, error, noResume, load } = useCareerInsights();

  useEffect(() => {
    load();
  }, [load]);

  let content;
  if (loading && !data) {
    content = <CareerInsightsSkeleton />;
  } else if (noResume) {
    content = <CareerInsightsEmpty />;
  } else if (error) {
    content = <SectionError message={error} onRetry={load} />;
  } else if (data) {
    content = <CareerInsightsView data={data} />;
  } else {
    content = <CareerInsightsEmpty />;
  }

  return (
    <div className="flex min-h-screen bg-surface">
      <DashboardSidebar />
      <div className="flex-1">
        <DashboardHeader />
        <main className="mx-auto max-w-6xl px-6 py-8">
          <div className="mb-6">
            <h1 className="text-2xl font-semibold text-navy">Career Insights</h1>
            <p className="mt-1 text-sm text-navy/50">
              Understand your strengths, close skill gaps, and explore roles you
              already have a head start on.
            </p>
          </div>
          {content}
        </main>
      </div>
    </div>
  );
}