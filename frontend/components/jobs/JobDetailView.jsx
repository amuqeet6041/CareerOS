"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { getJobById } from "@/services/jobService";
import { useJobMatch } from "@/hooks/useJobMatch";
import { useSavedJobs } from "@/hooks/useSavedJobs";
import { useApplications } from "@/hooks/useApplications";
import { useAuth } from "@/hooks/useAuth";
import {
  formatSalary,
  formatDate,
  humanizeLabel,
  formatExperienceRequirement,
} from "@/utils/formatters";

import ApplyNowButton from "./ApplyNowButton";
import SaveJobButton from "./SaveJobButton";
import MatchCard from "./MatchCard";
import { JobDetailSkeleton } from "./Skeletons";
import EmptyState from "@/components/shared/EmptyState";

export default function JobDetailView({ jobId }) {
  const [job, setJob] = useState(null);
  const [status, setStatus] = useState("loading");
  const [loadError, setLoadError] = useState(null);
  const cancelled = useRef(false);

  const { isAuthenticated, isLoading: authLoading } = useAuth();

  useEffect(() => {
    cancelled.current = false;
    setStatus("loading");
    setJob(null);
    setLoadError(null);

    getJobById(jobId)
      .then((data) => {
        if (cancelled.current) return;
        setJob(data);
        setStatus("success");
      })
      .catch((err) => {
        if (cancelled.current) return;
        setStatus("error");
        setLoadError(err?.message || "This job could not be loaded.");
      });

    return () => {
      cancelled.current = true;
    };
  }, [jobId]);

  const match = useJobMatch(jobId, {
    enabled: status === "success" && isAuthenticated && !authLoading,
  });

  const saved = useSavedJobs({
    enabled: status === "success" && isAuthenticated && !authLoading,
  });

  const applications = useApplications({
    enabled: status === "success" && isAuthenticated && !authLoading,
  });

  if (status === "loading") {
    return (
      <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6">
        <div className="h-4 w-24 animate-pulse rounded bg-elevated-strong" />
        <div className="mt-6">
          <JobDetailSkeleton />
        </div>
      </div>
    );
  }

  if (status === "error" || !job) {
    return (
      <div className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6">
        <EmptyState
          title="Job not found"
          description={loadError || "The job may have been removed or expired."}
          action={
            <Link
              href="/jobs"
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-accent-light"
            >
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Browse all jobs
            </Link>
          }
        />
      </div>
    );
  }

  const salary = formatSalary(job.salary_min, job.salary_max, job.currency);
  const hasSalary = Boolean(job.salary_min || job.salary_max);
  const location = [job.city, job.country].filter(Boolean).join(", ") || job.location;
  const workMode = humanizeLabel(job.work_mode);
  const employmentType = humanizeLabel(job.employment_type);
  const experience = formatExperienceRequirement(
    job.minimum_experience_years,
    job.maximum_experience_years
  );

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6">
      <Link
        href="/jobs"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-navy/60 transition-colors hover:text-navy"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        All jobs
      </Link>

      <div className="mt-6 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <article className="rounded-lg border border-line bg-surface p-6">
          <p className="text-xs font-medium uppercase tracking-wide text-navy/50">
            {job.company}
          </p>
          <div className="mt-1 flex flex-wrap items-start justify-between gap-4">
            <h1 className="text-2xl font-semibold text-navy">{job.title}</h1>
            {hasSalary ? (
              <div className="text-right">
                <p className="text-base font-semibold text-navy">{salary}</p>
                {job.currency ? (
                  <p className="text-xs text-navy/45">{job.currency}</p>
                ) : null}
              </div>
            ) : null}
          </div>

          <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-xs text-navy/60">
            {location ? <span>{location}</span> : null}
            {workMode ? <span>&bull; {workMode}</span> : null}
            {employmentType ? <span>&bull; {employmentType}</span> : null}
            {experience ? <span>&bull; {experience}</span> : null}
          </div>

          <div className="mt-6">
            <h2 className="text-sm font-semibold text-navy">Description</h2>
            <p className="mt-2 whitespace-pre-line text-sm leading-6 text-navy/75">
              {job.description || "No description available yet."}
            </p>
          </div>

          {job.skills?.length ? (
            <div className="mt-6">
              <h2 className="text-sm font-semibold text-navy">Required Skills</h2>
              <div className="mt-2 flex flex-wrap gap-2">
                {job.skills.map((skill) => (
                  <span
                    key={skill.skill_name}
                    className="rounded-full bg-elevated px-3 py-1 text-xs font-medium text-navy"
                  >
                    {skill.skill_name}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {job.qualifications?.length ? (
            <div className="mt-6">
              <h2 className="text-sm font-semibold text-navy">Qualifications</h2>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-navy/75">
                {job.qualifications.map((qualification) => (
                  <li key={qualification.qualification}>
                    {qualification.qualification}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <dl className="mt-6 grid grid-cols-2 gap-4 border-t border-line-subtle pt-5 sm:grid-cols-3">
            <MetaItem label="Source" value={humanizeLabel(job.source)} />
            {job.posted_at ? (
              <MetaItem label="Posted" value={formatDate(job.posted_at)} />
            ) : null}
            {job.expires_at ? (
              <MetaItem label="Expires" value={formatDate(job.expires_at)} />
            ) : null}
            {job.external_id != null ? (
              <MetaItem label="Reference" value={String(job.external_id)} />
            ) : null}
          </dl>
        </article>

        <div className="space-y-6 lg:sticky lg:top-8">
          <section className="rounded-lg border border-line bg-surface p-5">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-navy/50">
              Apply
            </h2>
            <p className="mt-2 text-sm text-navy/60">
              {isAuthenticated && !authLoading ? (
                <>
                  Applications open on the employer&apos;s website. Applying
                  records the job in{" "}
                  <Link
                    href="/student-dashboard/applications"
                    className="text-accent hover:underline"
                  >
                    My Applications
                  </Link>{" "}
                  so you can track it.
                </>
              ) : (
                <>Applications open on the employer&apos;s website.</>
              )}
            </p>
            <ApplyNowButton
              jobId={job.id}
              jobTitle={job.title}
              url={job.application_url}
              authenticated={isAuthenticated && !authLoading}
              applied={applications.appliedIds.has(job.id)}
              onTracked={applications.markApplied}
              showTrackedHint
              className="mt-3 w-full text-center"
            />
            <SaveJobButton
              jobId={job.id}
              jobTitle={job.title}
              saved={saved.savedIds.has(job.id)}
              authenticated={isAuthenticated && !authLoading}
              disabled={saved.loading}
              onToggle={saved.toggle}
              className="mt-3 w-full"
            />
          </section>

          <MatchCard
            status={match.status}
            data={match.data}
            onRetry={match.refetch}
          />
        </div>
      </div>
    </div>
  );
}

function MetaItem({ label, value }) {
  if (!value) return null;
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-navy/40">
        {label}
      </dt>
      <dd className="mt-0.5 text-sm text-navy/70">{value}</dd>
    </div>
  );
}