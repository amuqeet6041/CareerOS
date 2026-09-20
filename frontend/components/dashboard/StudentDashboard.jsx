"use client";

import { useEffect, useCallback, useState } from "react";
import Link from "next/link";

import { useAuth } from "@/hooks/useAuth";
import { useResume } from "@/hooks/useResume";
import { useApplications } from "@/hooks/useApplications";
import { useSavedJobs } from "@/hooks/useSavedJobs";
import { useJobRecommendations } from "@/hooks/useJobRecommendations";

import ProfileSummary from "./ProfileSummary";
import ProfileCompletion from "./ProfileCompletion";
import ResumeStatusCard from "./ResumeStatusCard";
import RecommendedJobs from "./RecommendedJobs";
import ApplicationStats from "./ApplicationStats";
import RecentApplications from "./RecentApplications";
import SavedJobsSummary from "./SavedJobsSummary";
import CareerOverview from "./CareerOverview";
import DashboardSkeleton from "./DashboardSkeleton";
import EmptyState from "@/components/shared/EmptyState";

// Orchestrates every dashboard section from existing APIs:
//   GET /api/auth/me          -> profile + completion
//   GET /api/resume/analysis  -> resume status + career overview
//   GET /api/jobs + /match    -> recommended jobs (bounded, via hook)
//   GET /api/applications     -> application stats + recent applications
//   GET /api/jobs/saved       -> saved jobs summary
// Each section renders its own loading / error / empty state.

export default function StudentDashboard() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();

  const resume = useResume();
  const applications = useApplications({ enabled: isAuthenticated });
  const saved = useSavedJobs({ enabled: isAuthenticated });

  useEffect(() => {
    if (isAuthenticated) resume.load();
  }, [isAuthenticated, resume.load]);

  const hasResume = Boolean(resume.analysis);
  const recommendations = useJobRecommendations({
    enabled: isAuthenticated && hasResume && !resume.loading,
  });

  const [retrying, setRetrying] = useState(false);
  const onRetryAnalysis = useCallback(async () => {
    setRetrying(true);
    try {
      await resume.retryAnalysis();
    } catch {
      // The failure is surfaced by useResume's error state.
    } finally {
      setRetrying(false);
    }
  }, [resume]);

  if (authLoading) return <DashboardSkeleton />;

  if (!isAuthenticated) {
    return (
      <EmptyState
        title="Sign in to view your dashboard"
        description="Your profile, resume, applications, and saved jobs appear here once you sign in."
        action={
          <Link
            href="/login"
            className="inline-block rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-light"
          >
            Sign in
          </Link>
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <ProfileSummary
            user={user}
            resume={resume.analysis}
            resumeLoading={resume.loading}
          />
          <ProfileCompletion user={user} resume={resume.analysis} />
        </div>
        <ResumeStatusCard
          resume={resume.analysis}
          loading={resume.loading}
          error={resume.error}
          retrying={retrying}
          onRetryAnalysis={onRetryAnalysis}
          onRetryLoad={resume.load}
        />
      </div>

      <RecommendedJobs
        recommendations={recommendations.recommendations}
        loading={recommendations.loading}
        error={recommendations.error}
        onRetry={recommendations.refetch}
        noResume={!hasResume && !resume.loading}
        savedIds={saved.savedIds}
        appliedIds={applications.appliedIds}
        onToggleSave={saved.toggle}
        onApplyTracked={applications.markApplied}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <ApplicationStats
          applications={applications.applications}
          loading={applications.loading}
          error={applications.error}
          onRetry={applications.refetch}
        />
        <RecentApplications
          applications={applications.applications}
          loading={applications.loading}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <SavedJobsSummary
          savedJobs={saved.savedJobs}
          loading={saved.loading}
          error={saved.error}
          onRetry={saved.refetch}
        />
        <CareerOverview resume={resume.analysis} loading={resume.loading} />
      </div>
    </div>
  );
}